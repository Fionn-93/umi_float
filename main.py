#!/usr/bin/env python3
"""
Umi-Float 主入口
"""

import logging
import sys
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QActionGroup, QDialog
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

from core.config import get_config
from core.state import get_state
from core.constants import APP_NAME, APP_VERSION, DEFAULT_CONFIG
from utils.ip_location import get_ip_location
from utils.weather_info import lookup_city_by_coords
from widgets.location_selector import lookup_city_id_by_name

from ui.float_widget import FloatWidget
from ui.tray_icon import TrayIcon
from ui.pie_panel import PiePanel
from ui.plugin_panel import PluginPanel
from ui.settings_dialog import SettingsDialog
from ui.plugin_edit_dialog import PluginEditDialog
from plugins.plugin_manager import PluginManager


class Application:
    """应用主类"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        import os

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        self.app.setWindowIcon(QIcon(icon_path))

        self.config = get_config()
        self.state = get_state()
        self.plugin_manager = PluginManager()

        from utils.clipboard_watcher import ClipboardWatcher

        ClipboardWatcher.get()

        self._try_auto_locate()

        self._init_ui()

    def _try_auto_locate(self):
        cfg = self.config.get()
        default_id = DEFAULT_CONFIG.get("weather_location", "101010100")
        if cfg.get("weather_location", default_id) != default_id:
            logger.info(
                "跳过自动定位: weather_location 已设置为 %s",
                cfg.get("weather_location"),
            )
            return
        api_key = cfg.get("weather_api_key", "")
        if not api_key:
            logger.info("跳过自动定位: 未配置 API Key")
            return
        import threading

        def do_locate():
            logger.info("开始自动定位...")
            ip_info = get_ip_location()
            if ip_info is None:
                logger.warning("自动定位失败: 无法获取IP位置")
                return
            location_id = lookup_city_by_coords(
                api_key,
                ip_info["lat"],
                ip_info["lon"],
                cfg.get("weather_api_host") or None,
            )
            if location_id is None:
                logger.warning("自动定位: QWeather API 未找到，尝试本地匹配...")
                location_id = lookup_city_id_by_name(
                    ip_info.get("city", ""), ip_info.get("region", "")
                )
            if location_id is None:
                logger.warning(
                    "自动定位失败: 未找到 %s 对应的城市", ip_info.get("city")
                )
                return
            logger.info(
                "自动定位成功: location_id=%s, city=%s",
                location_id,
                ip_info.get("city"),
            )
            self.config.update(weather_location=location_id)

        thread = threading.Thread(target=do_locate, daemon=True)
        thread.start()

    def _init_ui(self):
        """初始化UI"""
        self.float_widget = FloatWidget()
        self.drawer_panel = PiePanel()
        self.plugin_panel = PluginPanel()
        self.tray_icon = TrayIcon()
        self.settings_dialog = None

        # 连接信号
        self.tray_icon.show_hide_requested.connect(self._toggle_float_widget)
        self.tray_icon.settings_requested.connect(self._show_settings)
        self.tray_icon.quit_requested.connect(self._quit)

        self.float_widget.clicked.connect(self._toggle_panel)
        self.float_widget.show_menu.connect(self._show_context_menu)
        self.float_widget.drag_started.connect(self.drawer_panel.hide_panel)
        self.float_widget.hover_expand.connect(self._on_hover_expand)

        self.drawer_panel.plugin_executed.connect(self._execute_plugin)
        self.drawer_panel.panel_closed.connect(self._on_panel_closed)
        self.drawer_panel.show_menu.connect(self._show_context_menu)
        self.drawer_panel.plugin_edit_requested.connect(self._on_plugin_edit)
        self.drawer_panel.plugin_disable_requested.connect(self._on_plugin_disable)

        self.plugin_panel.closed.connect(self._on_plugin_panel_closed)

        # 加载插件到面板
        self.plugin_manager.initialize()
        enabled_plugins, _ = self.plugin_manager.get_ordered_plugins()
        plugins_dict = {pid: config for pid, config in enabled_plugins}
        self.drawer_panel.set_plugins(plugins_dict)

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
            self.settings_dialog.page_changed.connect(self._on_page_changed)
            self.settings_dialog.finished.connect(self._on_settings_closed)
            self.settings_dialog.show()
            if not self.drawer_panel.isVisible():
                self.drawer_panel.enter_preview_mode(self.float_widget)
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def _on_settings_closed(self):
        """设置窗口关闭时退出预览模式"""
        if self.drawer_panel._preview_mode:
            self.drawer_panel.exit_preview_mode()
        if self.drawer_panel._hover_mode and self.drawer_panel.isVisible():
            self.drawer_panel._leave_timer.start()
        self.settings_dialog = None

    def _on_page_changed(self, page_index):
        """页面切换时处理预览模式"""
        if page_index == 2:
            if not self.drawer_panel._preview_mode:
                self.drawer_panel.enter_preview_mode(self.float_widget)

    def _apply_settings(self, target):
        """应用设置变更"""
        self.float_widget.apply_settings()
        self.drawer_panel._center_label.refresh_theme()
        for btn in self.drawer_panel._buttons:
            btn.refresh_theme()
        if target == "float_ball":
            if self.drawer_panel._preview_mode:
                self.drawer_panel.exit_preview_mode()
        elif target == "pie_panel":
            if self.drawer_panel._preview_mode:
                self.plugin_manager.reload_plugins()
                enabled_plugins, _ = self.plugin_manager.get_ordered_plugins()
                plugins_dict = {pid: config for pid, config in enabled_plugins}
                self.drawer_panel.set_plugins(plugins_dict)
                self.drawer_panel.refresh_preview_layout(self.float_widget)
            else:
                self.drawer_panel.enter_preview_mode(self.float_widget)

    def _quit(self):
        """退出应用"""
        print("正在退出...")
        self.tray_icon.hide()
        self.app.quit()

    def _restart(self):
        """重启应用"""
        import os
        import sys

        print("正在重启...")
        self.tray_icon.hide()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _toggle_panel(self):
        """切换抽屉面板显示"""
        cfg = self.config.get()
        if cfg.get("pie_expand_mode", "click") != "click":
            return
        if self.drawer_panel.isVisible():
            self.drawer_panel.hide_panel()
        else:
            self.float_widget.hide()
            self.drawer_panel.show_panel(self.float_widget)

    def _on_hover_expand(self):
        """悬浮展开面板"""
        cfg = self.config.get()
        if cfg.get("pie_expand_mode", "click") != "hover":
            return
        if self.drawer_panel.isVisible():
            return
        self.drawer_panel.set_hover_mode(True)
        self.float_widget.hide()
        self.drawer_panel.show_panel(self.float_widget)

    def _on_panel_closed(self):
        """面板关闭后恢复悬浮球"""
        if self.drawer_panel._pending_float_pos is not None:
            self.float_widget.move(self.drawer_panel._pending_float_pos)
            self.config.update(
                position={
                    "x": self.drawer_panel._pending_float_pos.x(),
                    "y": self.drawer_panel._pending_float_pos.y(),
                }
            )
            self.drawer_panel._pending_float_pos = None
        self.drawer_panel.set_hover_mode(False)
        self.float_widget.show()

    def _show_context_menu(self):
        """显示右键菜单"""
        menu = QMenu()
        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        display_submenu = QMenu("显示模式", menu)
        mode_group = QActionGroup(display_submenu)
        mode_group.setExclusive(True)
        current_mode = self.config.get()["display_mode"]
        for label, key in [
            ("时钟", "clock"),
            ("性能", "performance"),
            ("天气", "weather"),
        ]:
            action = QAction(label, display_submenu)
            action.setCheckable(True)
            action.setChecked(key == current_mode)
            action.setData(key)
            display_submenu.addAction(action)
            mode_group.addAction(action)
        display_submenu.triggered.connect(self._switch_display_mode)
        menu.addMenu(display_submenu)
        menu.addSeparator()
        restart_action = QAction("重启", self.app)
        restart_action.triggered.connect(self._restart)
        menu.addAction(restart_action)
        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        if self.float_widget.isVisible():
            menu.exec_(self.float_widget.mapToGlobal(self.float_widget.rect().center()))
        else:
            from PyQt5.QtGui import QCursor

            menu.exec_(QCursor.pos())

    def _switch_display_mode(self, action):
        mode = action.data()
        if mode and mode != self.config.get()["display_mode"]:
            self.config.update(display_mode=mode)
            self.float_widget.apply_settings()

    def _on_plugin_edit(self, plugin_id: str):
        """从面板右键编辑插件"""
        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()
        plugin_config = None
        for pid, config in enabled + disabled:
            if pid == plugin_id:
                plugin_config = config
                break
        if plugin_config is None:
            return
        dialog = PluginEditDialog(
            plugin_id=plugin_id,
            name=plugin_config.name,
            description=plugin_config.description,
            icon=plugin_config.icon,
            exec_cmd=plugin_config.exec,
            parent=None,
        )
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            pm.update_plugin_override(
                plugin_id,
                {
                    "name": data["name"],
                    "description": data["description"],
                    "icon": data["icon"],
                    "exec": data["exec"],
                },
            )
            self._refresh_panel_plugins()

    def _on_plugin_disable(self, plugin_id: str):
        """从面板右键禁用插件"""
        pm = PluginManager.get()
        pm.disable_plugin(plugin_id)
        self._refresh_panel_plugins()

    def _refresh_panel_plugins(self):
        """刷新面板插件列表"""
        self.plugin_manager.reload_plugins()
        enabled_plugins, _ = self.plugin_manager.get_ordered_plugins()
        plugins_dict = {pid: config for pid, config in enabled_plugins}
        self.drawer_panel.set_plugins(plugins_dict)
        self.drawer_panel.show_panel(self.float_widget, animate=False)

    def _execute_plugin(self, plugin_id: str):
        """执行插件"""
        ptype, pdata = self.plugin_manager.execute_plugin(plugin_id)
        if ptype == "widget":
            self._show_widget_panel(plugin_id)
        elif ptype == "command":
            self.drawer_panel.hide_panel()

    def _show_widget_panel(self, plugin_id: str):
        """显示 widget 插件面板"""
        widget_class = self.plugin_manager.get_widget_class(plugin_id)
        if widget_class is None:
            print(f"无法加载 widget 插件: {plugin_id}")
            return
        plugins = self.plugin_manager.get_plugins()
        config = plugins.get(plugin_id)
        if config is None:
            return
        data_dir = self.plugin_manager.get_plugin_data_dir(plugin_id)
        from utils.theme_colors import get_current_accent_color
        from PyQt5.QtWidgets import QApplication

        host_info = {
            "name": config.name,
            "accent_color": get_current_accent_color(),
            "data_dir": data_dir,
            "app": QApplication.instance(),
        }
        self.drawer_panel.hide_panel()
        self.plugin_panel.set_plugin(plugin_id, widget_class, host_info)
        self.plugin_panel.show_panel(self.float_widget)

    def _on_plugin_panel_closed(self):
        """插件面板关闭后恢复浮球"""
        self.float_widget.show()

    def run(self):
        """运行应用"""
        return self.app.exec_()


def main():
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
