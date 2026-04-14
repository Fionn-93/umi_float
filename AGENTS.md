# Developer Instructions

## Running the App

```bash
PYTHONPATH=/path/to/umi_float:$PYTHONPATH python3 main.py
```

All imports are relative to project root (e.g., `from core.config import get_config`). The app crashes without PYTHONPATH set.

## Platform

**Deepin Linux only.** Extensions shell out to Deepin apps (`deepin-calculator`, `dde-file-manager`, etc.) and the screenshot extension uses `qdbus com.deepin.Screenshot`. `utils/system_info.py` calls `org.deepin.dde.Display1` over DBus for screen info. System tray uses `QSystemTrayIcon` (may need `libayatana-appindicator3`).

## Dev Tools

- Python 3.12, PyQt5 5.15.11
- Formatter: `black` (line-length 88) | Typecheck: `mypy` | Lint: `pylint` | Test: `pytest` + `pytest-qt`
- Config in `pyproject.toml`. No CI, no pre-commit hooks, no task runner scripts.
- `./venv/` in repo root (gitignored).
- `tests/` exists but contains only `__init__.py` — no actual tests yet.

## Architecture

### Entrypoint

`main.py` → `Application` class creates `QApplication`, then `FloatWidget` (the ball), `PiePanel` (the popup menu), `TrayIcon`, and `PluginManager`. Signals wire them together.

### Singletons (critical pattern)

`ConfigManager`, `AppState`, and `PluginManager` all use the same hand-rolled singleton pattern where `__init__` early-returns if `_instance` is already set:

```python
def __init__(self):
    self._config = None  # MUST be first — accessed before _instance check returns
    if ConfigManager._instance is not None:
        return
    ConfigManager._instance = self
```

Any instance attribute must be initialized **before** the `_instance` check, otherwise second calls to the constructor get an object without those attributes (`AttributeError`).

### Plugin System

- Extensions are `manifest.json` files with `name`, `icon`, `exec`, `type`, `enabled` fields.
- `PluginLoader.load_all_plugins()` reads two directories in order:
  1. `~/.local/share/umi-float/extensions/` (user)
  2. `<repo>/extensions/` (project — overrides user plugins with same directory name)
- Execution: `subprocess.run(config.exec, shell=True, check=True)` — `shell=True` is required because some commands use `qdbus` with arguments.
- `plugin_changed` signal exists on `PluginLoader` but is never connected to a `QFileSystemWatcher`. Hot reload is not implemented.

### Import Side Effects

Importing `core.constants` creates directories at module load time:
- `~/.config/umi-float/`
- `~/.local/share/umi-float/extensions/`

### Application Lifecycle

`QApplication.setQuitOnLastWindowClosed(False)` — closing the float widget does not quit the app. Quit only via system tray menu.

### Dead Code

`ui/drawer_panel.py` (`DrawerPanel`) is unused. `main.py` imports `PiePanel` from `ui/pie_panel.py` and assigns it to `self.drawer_panel`. The old drawer panel is dead code.

## UI Gotchas

### Click vs Drag (FloatWidget)

`FloatWidget` distinguishes clicks from drags using a 10-pixel `manhattanLength` threshold. Movement < 10px emits `clicked`; >= 10px emits `drag_started`. Edge snapping (20px threshold) runs on every mouse release.

### Theme Colors (FloatButton)

Do not use stylesheets alone for background/text colors — they don't reliably stick on this widget. Use `QPalette`:

```python
new_palette = self.palette()
new_palette.setColor(QPalette.Window, theme_bg)
new_palette.setColor(QPalette.WindowText, theme_text)
self.setPalette(new_palette)
```

Use stylesheets only for border, border-radius, and font. Theme detection: `palette.color(QPalette.Window).lightness() <= 128` means dark.

`QGraphicsDropShadowEffect` clips to the rectangular window boundary — unusable for the circular float ball.

## Known Bug

`utils/system_info.py:is_dark_theme()` references `QPalette` but only imports `QGuiApplication` from `PyQt5.QtGui`. This method will raise `NameError` at runtime. Needs `from PyQt5.QtGui import QGuiApplication, QPalette`.

## Config

- `pydantic>=2.12.0` is in `requirements.txt` but is **not used anywhere**. Config validation is manual in `ConfigManager._validate_config()`. Do not introduce pydantic models.
- Config file: `~/.config/umi-float/config.json`. Written automatically on first run with defaults from `core/constants.py:DEFAULT_CONFIG`.
