"""
常量定义模块
"""
import os
from pathlib import Path

# 应用信息
APP_NAME = "Umi-Float"
APP_VERSION = "0.1.0"
APP_ID = "com.umi.float"

# 配置目录
CONFIG_DIR = Path(os.path.expanduser("~/.config/umi-float"))
DATA_DIR = Path(os.path.expanduser("~/.local/share/umi-float"))
EXTENSIONS_DIR = DATA_DIR / "extensions"
ICONS_DIR = DATA_DIR / "icons"

# 确保目录存在
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# 默认配置值
DEFAULT_CONFIG = {
    "opacity": 0.9,
    "float_ball_size": 56,
    "theme": "deepin",
    "display_mode": "clock",
    "pie_button_size": 56,
    "pie_spacing": 10,
    "auto_start": False,
    "show_on_fullscreen": False,
    "weather_api_key": "",
    "weather_location": "101010100",
    "position": {"x": 100, "y": 100},
    "plugin_overrides": {},
}

# 插件配置文件名
PLUGIN_MANIFEST = "manifest.json"

# 扩展目录常量
PROJECT_EXTENSIONS_DIR = Path(__file__).parent.parent / "extensions"
