"""
系统托盘图标
"""
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标"""
    
    show_hide_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_tray()
        self._setup_menu()
    
    def _setup_tray(self):
        """设置托盘"""
        self.setToolTip("Umi-Float 桌面工具箱")
        
        # 尝试加载系统图标
        icon = QIcon.fromTheme("applications-utilities")
        if icon.isNull():
            icon = QIcon.fromTheme("preferences-system")
        if icon.isNull():
            icon = QIcon.fromTheme("system-run")
        
        self.setIcon(icon)
        self.setVisible(True)
    
    def _setup_menu(self):
        """设置右键菜单"""
        menu = QMenu()
        
        show_hide_action = QAction("显示/隐藏悬浮球", self)
        show_hide_action.triggered.connect(self.show_hide_requested.emit)
        menu.addAction(show_hide_action)
        
        menu.addSeparator()
        
        settings_action = QAction("偏好设置", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
