"""
开机自启工具模块
"""

import os
from pathlib import Path


class Autostart:
    """开机自启管理器"""

    AUTOSTART_DIR = Path(os.path.expanduser("~/.config/autostart"))
    DESKTOP_FILE = AUTOSTART_DIR / "umi-float.desktop"

    @staticmethod
    def is_enabled() -> bool:
        """检查是否启用开机自启"""
        return Autostart.DESKTOP_FILE.exists()

    @staticmethod
    def enable(path: str) -> bool:
        """启用开机自启"""
        try:
            Autostart.AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)

            content = f"""[Desktop Entry]
Type=Application
Name=Umi-Float
Comment=Desktop Float Toolbox
Exec={path}
Icon=applications-utilities
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
            with open(Autostart.DESKTOP_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"启用开机自启失败: {e}")
            return False

    @staticmethod
    def disable() -> bool:
        """禁用开机自启"""
        try:
            if Autostart.DESKTOP_FILE.exists():
                Autostart.DESKTOP_FILE.unlink()
            return True
        except Exception as e:
            print(f"禁用开机自启失败: {e}")
            return False
