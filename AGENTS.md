# Developer Instructions

## Runtime Requirements

**PYTHONPATH mandatory**: Must run with:
```bash
PYTHONPATH=/path/to/umi_float:$PYTHONPATH python3 main.py
```
Imports are relative to project root. App crashes without this.

## Platform Dependencies

**Deepin Linux only**: Uses Deepin DBus:
- `com.deepin.Screenshot` (screenshot plugin)
- `org.deepin.dde.Display1` (screen info)
- System tray requires `libayatana-appindicator3`

## Architecture Patterns

### ConfigManager Singleton (critical init order)
```python
self._config = None  # MUST be first
if ConfigManager._instance is not None:
    return
```
Otherwise causes `AttributeError: 'ConfigManager' object has no attribute '_config'`

### Plugin Loader Checks Two Directories
1. `~/.local/share/umi-float/extensions/` (user)
2. `repo_root/extensions/` (development)
Project extensions load second and override user plugins.

### Manual Config Validation
`pydantic>=2.12.0` in requirements but NOT used. Uses `ConfigManager._validate_config()`. Do not add pydantic.

## Runtime Side Effects

On import, `constants.py` creates:
- `~/.config/umi-float/`
- `~/.local/share/umi-float/extensions/`

## Application Lifecycle

`QApplication.setQuitOnLastWindowClosed(False)` - app stays alive via system tray. Closing float widget doesn't quit.

## Click vs Drag Detection (FloatWidget)

FloatWidget uses distance-based threshold (10 pixels) to distinguish:
- Mouse movement < 10px = click (emits `clicked` signal)
- Mouse movement >= 10px = drag

## Theme Adaptation (FloatButton)

**Do not use stylesheets for background/text colors** - they don't stick. Use palette method:

```python
new_palette = self.palette()
new_palette.setColor(QPalette.Window, theme_bg)
new_palette.setColor(QPalette.WindowText, theme_text)
new_palette.setColor(QPalette.Button, theme_bg)
new_palette.setColor(QPalette.ButtonText, theme_text)
self.setPalette(new_palette)
```

Combine with stylesheet for border/radius/font only. Theme detection uses `palette.color(QPalette.Window).lightness()`.

**No shadow effects**: `QGraphicsDropShadowEffect` gets clipped to window boundary (rectangle), unsuitable for circular widgets.

## Plugin Execution

`subprocess.run(cmd, shell=True, check=True)` - `shell=True` required for DBus commands.

## Current State

**Working**: Float widget, dragging, edge snapping (20px), drawer panel, system tray, plugins, config, theme adaptation.

**Missing**: Plugin hot reload (signal defined but not connected to QFileSystemWatcher).

## Dev Tools

`./venv/` in repo root (unusual). Dev tools in requirements-dev (black, mypy, pylint, pytest) but no scripts/CI.
