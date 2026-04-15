#!/usr/bin/env python3
"""
Umi-Float 主入口
"""
import sys
from PyQt5.QtWidgets import QApplication, QMenu, QAction
from PyQt5.QtCore import QTimer

from core.config import get_config
from core.state import get_state
from core.constants import APP_NAME, APP_VERSION

from ui.float_widget import FloatWidget
from ui.tray_icon import TrayIcon
from ui.pie_panel import PiePanel
from ui.settings_dialog import SettingsDialog
from plugins.plugin_manager import PluginManager


class Application:
    """应用主类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.config = get_config()
        self.state = get_state()
        self.plugin_manager = PluginManager()
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.float_widget = FloatWidget()
        self.drawer_panel = PiePanel()
        self.tray_icon = TrayIcon()
        self.settings_dialog = None
        
        # 连接信号
        self.tray_icon.show_hide_requested.connect(self._toggle_float_widget)
        self.tray_icon.settings_requested.connect(self._show_settings)
        self.tray_icon.quit_requested.connect(self._quit)
        
        self.float_widget.clicked.connect(self._toggle_panel)
        self.float_widget.show_menu.connect(self._show_context_menu)
        self.float_widget.drag_started.connect(self.drawer_panel.hide_panel)
        
        self.drawer_panel.plugin_executed.connect(self._execute_plugin)
        
        # 加载插件到面板
        self.plugin_manager.initialize()
        plugins = self.plugin_manager.get_plugins()
        self.drawer_panel.set_plugins(plugins)
        
        self.float_widget.show()
        
        print(f"{APP_NAME} v{APP_VERSION} 启动成功")
        print(f"配置目录: {self.config._config_file.parent}")
        print(f"已加载插件: {len(self.plugin_manager.get_plugins())}")
    
    def _toggle_float_widget(self):
        """切换悬浮球显示"""
        if self.state.float_ball_visible:
            self.float_widget.hide()
            self.state.float_ball_visible = False
        else:
            self.float_widget.show()
            self.state.float_ball_visible = True
    
    def _show_settings(self):
        """显示设置"""
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog()
            self.settings_dialog.settings_changed.connect(self._apply_settings)
            self.settings_dialog.show()
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
    
    def _apply_settings(self):
        """应用设置变更"""
        self.float_widget.apply_settings()
        self.drawer_panel._center_label.refresh_theme()
        for btn in self.drawer_panel._buttons:
            btn.refresh_theme()
        self.drawer_panel._refresh_plugins_ui()
    
    def _quit(self):
        """退出应用"""
        print("正在退出...")
        self.tray_icon.hide()
        self.app.quit()
    
    def _toggle_panel(self):
        """切换抽屉面板显示"""
        if self.drawer_panel.isVisible():
            self.drawer_panel.hide_panel()
        else:
            self.drawer_panel.show_panel(self.float_widget)
    
    def _show_context_menu(self):
        """显示右键菜单"""
        menu = QMenu()
        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        menu.exec_(self.float_widget.mapToGlobal(self.float_widget.rect().center()))
    
    def _execute_plugin(self, plugin_id: str):
        """执行插件"""
        self.plugin_manager.execute_plugin(plugin_id)
        self.drawer_panel.hide_panel()
    
    def run(self):
        """运行应用"""
        return self.app.exec_()


def main():
    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
