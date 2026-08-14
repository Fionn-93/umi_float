# Developer Instructions

## Running the App

```bash
PYTHONPATH=$(pwd):$PYTHONPATH python3 main.py
```

All imports are relative to project root (e.g., `from core.config import get_config`). The app crashes without `PYTHONPATH` set.

## Dev Commands

```bash
black --line-length 88 .
mypy .
pylint ui/ core/ utils/ plugins/ widgets/
pytest
```

No CI, no pre-commit hooks, no task runner scripts. `tests/` contains only `__init__.py` — no actual tests yet.

## Platform

**Deepin/UOS Linux only.** Extensions shell out to Deepin apps (`deepin-calculator`, `dde-file-manager`, etc.). Screenshot extension uses `qdbus com.deepin.Screenshot`. `utils/system_info.py` calls `org.deepin.dde.Display1` over DBus. System tray uses `QSystemTrayIcon` (may need `libayatana-appindicator3`).

## Architecture

### Entrypoint

`main.py` → `Application` creates `QApplication`, then `FloatWidget` (the ball), `PiePanel` (the popup menu), `PluginPanel` (widget plugin host), `TrayIcon`, and `PluginManager`. Signals wire them together.

### Singletons (critical pattern)

`ConfigManager`, `AppState`, and `PluginManager` all use the same hand-rolled singleton where `__init__` early-returns if `_instance` is already set:

```python
def __init__(self):
    self._config = None  # MUST be first — accessed before _instance check returns
    if ConfigManager._instance is not None:
        return
    ConfigManager._instance = self
```

Any instance attribute must be initialized **before** the `_instance` check, otherwise second constructor calls produce objects missing those attributes (`AttributeError`). `AppState` uses a `@classmethod get()` instead — same trap applies, `_instance` check must come after all attribute assignments.

### Plugin System

- Extensions are `manifest.json` files with `name`, `icon`, `exec`, `type`, `enabled` fields.
- Execution: `subprocess.Popen(..., shell=True, ...)` — `shell=True` is required because some commands use `qdbus` with arguments.
- `plugin_changed` signal exists on `PluginLoader` but is never connected to a `QFileSystemWatcher`. Hot reload is not implemented.
- Project plugins (`<repo>/extensions/`) override user plugins (`~/.local/share/umi-float/extensions/`) with the same directory name.
- Widget plugins receive `host_info` with `set_float_display(data)` / `clear_float_display()` to show custom progress ring + icon + text on the float ball, and `keep_float_visible` flag to keep the ball visible when the plugin window is open (used by the timer plugin).

### Import Side Effects

Importing `core.constants` creates directories at module load time:
- `~/.config/umi-float/`
- `~/.local/share/umi-float/extensions/`
- `~/.local/share/umi-float/icons/`

### Application Lifecycle

`QApplication.setQuitOnLastWindowClosed(False)` — closing the float widget does not quit the app. Quit only via system tray menu. `keep_float_visible` flag on `host_info` prevents the float ball from hiding when a plugin window is open (used by the timer plugin).

### Dead Code

`ui/drawer_panel.py` (`DrawerPanel`) is unused. `main.py` imports `PiePanel` from `ui/pie_panel.py` and assigns it to `self.drawer_panel`.

## UI Gotchas

### QWidget Background (most recent bug)

Plain `QWidget` subclasses **do not paint `background-color` from stylesheets** unless `WA_StyledBackground` is set. Always add:

```python
self.setAttribute(Qt.WA_StyledBackground, True)
```

Without this, the parent/chameleon style background bleeds through as dark or semi-transparent. `QScrollArea`, `QFrame`, `QDialog` don't need this — only `QWidget` direct subclasses.

### QComboBox on UOS (chameleon style)

Dropdown items render as white-on-white. Fix by creating a separate `QListView` with explicit stylesheet:

```python
view = QListView()
view.setStyleSheet("color: #333333; background-color: #ffffff;")
combo.setView(view)
```

Tab focus ring: add `QTabBar::tab:focus { outline: none; }` and `setFocusPolicy(Qt.NoFocus)`.

### QPushButton Focus Ring on UOS (chameleon style)

`QPushButton` 获得 Tab 焦点后会绘制一个主题色矩形边框。对插件面板中所有按钮（无论静态创建还是动态创建），最简一劳永逸的修复是在 widget 的全局样式表中加一行：

```python
self.setStyleSheet("""
    QPushButton:focus { outline: none; }
    ...
""")
```

这比逐个按钮 `setFocusPolicy(Qt.NoFocus)` 更可靠，因为它覆盖动态创建的按钮（如 `QListWidget` 中嵌入的卡片按钮）。

### Qt5 Color Format

`{color}dd` (8-digit hex) is **not** supported in Qt5 QSS. Use `rgba(r, g, b, 0.8)` for transparency.

### Click vs Drag (FloatWidget)

10-pixel `manhattanLength` threshold. `< 10px` → `clicked`; `≥ 10px` → `drag_started`. Edge snapping runs on every mouse release (20px threshold).

### FloatButton Theme Colors

Do not use stylesheets alone for background/text colors — they don't reliably stick. Use `QPalette`:

```python
new_palette = self.palette()
new_palette.setColor(QPalette.Window, theme_bg)
new_palette.setColor(QPalette.WindowText, theme_text)
self.setPalette(new_palette)
```

Use stylesheets only for border, border-radius, and font. `QGraphicsDropShadowEffect` clips to the rectangular window boundary — unusable for the circular float ball.

### HiDPI Icons

Must multiply pixel sizes by `devicePixelRatio()` and call `setDevicePixelRatio(dpr)` on pixmaps for sharp rendering on high-DPI displays.

### Icon Paths in PieButton

Icons starting with `icons/` are custom icons saved to `DATA_DIR`. System icons use `QIcon.fromTheme()`.

### Plugin List Drag & Drop (most recent bug)

`_calculate_drop_index` returns the index in the **UI layout** (visible list). `_handle_reorder` must compute `old_index` from the **same layout**, not from the config list (`enabled_plugins`). If config-only plugins (loaded but not visible) exist, the config index differs from the UI index, causing incorrect adjustment/early-return.

**Fix**: `_handle_reorder` reads widget order from `_get_section_content().layout()`, applies the reorder in UI coordinates, then maps the result back to config order by preserving UI order for config items.

### Timer Float Display Bridge

When a timer/plugin runs, the float ball can show a custom display (progress ring + icon + MM:SS text) via `set_float_display()` / `clear_float_display()` passed in `host_info`. The `keep_float_visible` flag prevents the float ball from hiding when the plugin window opens. The pomodoro fade animation (`text_opacity` pyqtProperty, 1.0→0.25 on idle, 800ms pulse) is handled by `float_button.py:_paint_override_mode()`.

### Global Hotkey (X11 XGrabKey)

System: `utils/global_hotkey.py` → `GlobalHotkeyManager` uses `XGrabKey` on the root window + `QAbstractNativeEventFilter` intercepting `xcb_generic_event_t` KeyPress events. `XkbSetIgnoreLockMods` ensures CapsLock/NumLock/ScrollLock don't interfere. Config key: `toggle_shortcut` (default `"Alt+F"`). Keyboard navigation in PiePanel (Up/Down/Tab cycle, Enter activate, Esc close) is wired separately.

### host_info Plugin Context

Widget plugins receive a `host_info` dict with:
- `name`, `accent_color`, `data_dir`, `app`, `widget_host` (PluginPanel reference)
- `set_float_display(data)` / `clear_float_display()` — show/custom progress ring on the float ball
- `keep_float_visible: bool` — if True, float ball stays visible when the plugin window is open

## Design Reference

All UI styling decisions follow `DESIGN.md` at project root. Key points:

- Accent color: `get_current_accent_color()` (reads app theme from ConfigManager → `theme_from_key`). All UI uses the same app theme; system accent color is no longer used.
- Each dialog/page defines a `get_xxx_style(accent_color)` function for its stylesheet.
- `Card` > `#sectionTitle` (group title) has `padding: 2px 4px 10px 4px`, uppercase + letter-spacing — set containing layout spacing to `2`, not `12`.
- Page title (`#pageTitle`): 22px Bold, color `#1f2937`.
- Setting rows (`SettingRow`): hover background `rgba(0,0,0,0.03)`, left container fixed width `240px`.

## Config

- `pydantic>=2.12.0` is in `requirements.txt` but **not used anywhere**. Config validation is manual in `ConfigManager._validate_config()`. Do not introduce pydantic models.
- Config key `theme_color` is deprecated — migrated to `theme` (preset key). `display_mode: "memory"` is auto-migrated to `"performance"`.
- Config file: `~/.config/umi-float/config.json`. Written automatically on first run with defaults from `core/constants.py:DEFAULT_CONFIG`.