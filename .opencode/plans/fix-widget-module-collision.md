# Fix: Widget plugin `sys.modules` + `sys.path` collision (v2)

## Root Cause

Two layers of collision when multiple widget extensions use bare `from widget import ClassName`:

1. **`sys.modules` caching**: `widget` module cached under same key → second plugin finds wrong module
2. **`sys.path` ordering**: Each `__init__.py` does `sys.path.insert(0, plugin_dir)`, paths accumulate. The most recently loaded plugin's path sits at `sys.path[0]`. After popping `sys.modules['widget']`, the next `from widget import ...` resolves to whichever plugin's path is first in `sys.path`.

The previous fix (v1) only handled `sys.modules`, which made the first switch work but fail on the **second** switch:
- color-picker → clipboard → color-picker: last open fails because clipboard's path is at `sys.path[0]`

## Fix

**File**: `plugins/plugin_loader.py`, method `get_widget_class` (lines 377-388)

Replace the current wrapper with a robust version that snapshots `sys.modules`, manages `sys.path`, and cleans up after each call:

```python
            import sys as _sys

            _plugin_dir = str(init_file.parent)

            def _make_entry_wrapper(_func, _pdir):
                def _wrapper(host_info):
                    _before = set(_sys.modules.keys())
                    _sys.path.insert(0, _pdir)
                    try:
                        return _func(host_info)
                    finally:
                        _after = set(_sys.modules.keys())
                        for _key in _after - _before:
                            _sys.modules.pop(_key, None)
                        try:
                            _sys.path.remove(_pdir)
                        except ValueError:
                            pass
                return _wrapper

            return _make_entry_wrapper(entry_func, _plugin_dir)
```

The wrapper:
1. **Before call**: Snapshot `sys.modules` keys, insert correct plugin directory at `sys.path[0]`
2. **Call**: Execute `create_widget(host_info)` — bare `from widget import ...` resolves to the correct plugin's `widget.py`
3. **After call (finally)**: Remove all newly-added `sys.modules` entries (not just `widget`), remove the inserted `sys.path` entry

This ensures complete isolation: no stale modules, no `sys.path` pollution, works for any number of switches between widget plugins.

## Testing

1. Run app → open color-picker → close → open clipboard → close → open color-picker → ✓
2. Rapidly switch between multiple widget plugins → no `ImportError`
3. Verify each widget loads its own `widget.py` (check logs for correct path)

## Impact

- Centralized fix in one file, one method
- Handles any local module name collision (not just `widget`)
- No extension modifications needed
- No `sys.path` accumulation between calls