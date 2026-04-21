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

**Deepin/UOS Linux only.** Extensions shell out to Deepin apps (`deepin-calculator`, `dde-file-manager`, etc.). Screenshot extension uses `qdbus com.deepin.Screenshot`. `utils/system_info.py` calls `org.deepin.dde.Display1` and `org.deepin.dde.Appearance1` over DBus. System tray uses `QSystemTrayIcon` (may need `libayatana-appindicator3`).

## Architecture

### Entrypoint

`main.py` → `Application` creates `QApplication`, then `FloatWidget` (the ball), `PiePanel` (the popup menu), `TrayIcon`, and `PluginManager`. Signals wire them together.

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

### Import Side Effects

Importing `core.constants` creates directories at module load time:
- `~/.config/umi-float/`
- `~/.local/share/umi-float/extensions/`
- `~/.local/share/umi-float/icons/`

### Application Lifecycle

`QApplication.setQuitOnLastWindowClosed(False)` — closing the float widget does not quit the app. Quit only via system tray menu.

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

## Design Reference

All UI styling decisions follow `DESIGN.md` at project root. Key points:

- Accent color: `SystemInfo.get_accent_color()` (DBus → `org.deepin.dde.Appearance1`, property `QtActiveColor`). Must use `iface.call("Get", ...)` — direct `iface.property()` returns `None`.
- Each dialog/page defines a `get_xxx_style(accent_color)` function for its stylesheet.
- `MidHeader` (group title) has built-in `padding: 20px 0 8px 4px` — set containing layout spacing to `0`, not `12`.
- Page title: 16px Bold, color `#1d1d1f`.
- Setting rows: `_SettingRow` with `setMinimumHeight(48)`, hover background `#fafafa`.

## Config

- `pydantic>=2.12.0` is in `requirements.txt` but **not used anywhere**. Config validation is manual in `ConfigManager._validate_config()`. Do not introduce pydantic models.
- Config key `theme_color` is deprecated — migrated to `theme` (preset key). `display_mode: "memory"` is auto-migrated to `"performance"`.
- Config file: `~/.config/umi-float/config.json`. Written automatically on first run with defaults from `core/constants.py:DEFAULT_CONFIG`.