"""
系统信息工具模块
"""
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtDBus import QDBusConnection, QDBusInterface
from PyQt5.QtCore import QRect


class SystemInfo:
    """系统信息工具类"""
    
    @staticmethod
    def get_screen_geometry() -> QRect:
        """获取屏幕几何信息"""
        app = QGuiApplication.instance()
        if app is None:
            app = QGuiApplication([])
        
        screens = app.screens()
        if not screens:
            return QRect(0, 0, 1920, 1080)
        
        primary_screen = screens[0]
        return primary_screen.geometry()
    
    @staticmethod
    def get_screen_size() -> tuple:
        """获取屏幕尺寸"""
        geometry = SystemInfo.get_screen_geometry()
        return geometry.width(), geometry.height()
    
    @staticmethod
    def get_display_info() -> dict:
        """获取显示器信息"""
        bus = QDBusConnection.sessionBus()
        display = QDBusInterface(
            "org.deepin.dde.Display1",
            "/org/deepin/dde/Display1",
            "org.deepin.dde.Display1",
            bus
        )
        
        if display.isValid():
            try:
                width = display.call("ScreenWidth").arguments()[0]
                height = display.call("ScreenHeight").arguments()[0]
                return {
                    "width": width,
                    "height": height,
                    "valid": True
                }
            except Exception as e:
                print(f"获取显示器信息失败: {e}")
        
        geometry = SystemInfo.get_screen_geometry()
        return {
            "width": geometry.width(),
            "height": geometry.height(),
            "valid": False
        }
    
    @staticmethod
    def is_fullscreen() -> bool:
        """检测是否有全屏窗口"""
        return False
    
    @staticmethod
    def is_dark_theme() -> bool:
        """检测是否为暗色主题 - 已弃用，应用使用固定主题色"""
        # 返回 False 表示始终使用自定义亮色主题
        return False

    @staticmethod
    def get_accent_color() -> str:
        """
        获取 UOS 系统强调色
        Returns:
            强调色十六进制字符串，如 "#402FDB"
            失败返回默认值 "#0078d4"
        """
        try:
            bus = QDBusConnection.sessionBus()
            iface = QDBusInterface(
                "org.deepin.dde.Appearance1",
                "/org/deepin/dde/Appearance1",
                "org.freedesktop.DBus.Properties",
                bus
            )
            if iface.isValid():
                reply = iface.call("Get", "org.deepin.dde.Appearance1", "QtActiveColor")
                if reply.type() == 2 and reply.arguments():
                    return str(reply.arguments()[0])
        except Exception:
            pass
        return "#0078d4"
