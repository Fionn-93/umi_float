"""取色器插件 - 入口"""

import sys
from pathlib import Path

plugin_dir = Path(__file__).parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))


def create_widget(host_info: dict):
    from widget import ColorPickerWidget

    return ColorPickerWidget(host_info)
