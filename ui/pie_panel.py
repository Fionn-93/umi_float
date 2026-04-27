"""
环形面板 - 类似 gnome-pie
"""

import math
from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel, QMenu
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    pyqtProperty,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QPoint,
    QByteArray,
)
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QFont,
    QPen,
    QRadialGradient,
    QRegion,
    QPixmap,
    QIcon,
)
from PyQt5.QtSvg import QSvgRenderer

from core.config import get_config
from core.constants import DATA_DIR
from utils.theme_colors import theme_from_key, DEFAULT_THEME


class PieButton(QLabel):
    """环形菜单按钮"""

    clicked = pyqtSignal()
    context_menu_requested = pyqtSignal(str)

    def __init__(
        self,
        plugin_id: str,
        icon_name: str,
        name: str,
        description: str = "",
        size: int = 64,
        parent=None,
    ):
        super().__init__(parent)
        self.plugin_id = plugin_id
        self.name = name
        self.icon_name = icon_name
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self._scale = 0.0
        self._hover_enabled = True

        tooltip = name
        if description:
            tooltip += f"\n{description}"
        self.setToolTip(tooltip)

        from PyQt5.QtWidgets import QApplication

        icon = None
        if icon_name.startswith("icons/"):
            from plugins.plugin_manager import PluginManager

            icon = PluginManager.get().resolve_icon(icon_name, plugin_id)

        if icon is None or icon.isNull():
            icon = QIcon.fromTheme(icon_name)

        if icon.isNull():
            self.setText(name[0].upper())
        else:
            app = QApplication.instance()
            dpr = app.devicePixelRatio() if app else 1.0
            icon_size = int(size * 0.618)
            pixmap = icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
            pixmap.setDevicePixelRatio(dpr)
            self.setPixmap(pixmap)

        self._apply_theme()

    def _apply_theme(self):
        """从配置应用主题色"""
        config = get_config()
        theme_key = config.get().get("theme", DEFAULT_THEME)
        colors = theme_from_key(theme_key)
        self.THEME_BG_NORMAL = colors["pie_bg_normal"]
        self.THEME_BG_HOVERED = colors["pie_bg_hovered"]
        self.THEME_TEXT_NORMAL = colors["pie_text_normal"]
        self.THEME_TEXT_HOVERED = colors["pie_text_hovered"]
        self._update_style(False)

    def refresh_theme(self):
        """刷新主题色"""
        self._apply_theme()

    def _update_style(self, hovered: bool):
        """更新样式 - 使用自定义主题色"""
        if hovered:
            bg = self.THEME_BG_HOVERED
            text = self.THEME_TEXT_HOVERED
        else:
            bg = self.THEME_BG_NORMAL
            text = self.THEME_TEXT_NORMAL

        self.setStyleSheet(f"""
            QLabel {{
                background: rgba({bg.red()}, {bg.green()}, {bg.blue()}, {bg.alpha()});
                color: rgb({text.red()}, {text.green()}, {text.blue()});
                border-radius: {self.size // 2}px;
                font-size: {self.size // 3}px;
                font-weight: bold;
            }}
        """)

    def _get_scale(self) -> float:
        """获取缩放"""
        return self._scale

    def _set_scale(self, scale: float):
        """设置缩放（用于动画）"""
        self._scale = scale
        self.update()

    scale = pyqtProperty(float, _get_scale, _set_scale)

    def paintEvent(self, event):
        """绘制事件，支持缩放"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 计算缩放后的位置和大小（仅在动画过程中缩放，完成后跳过）
        if 0 < self._scale < 1.0:
            center_x = self.width() / 2
            center_y = self.height() / 2

            # 绘制缩放效果
            painter.translate(center_x, center_y)
            painter.scale(self._scale, self._scale)
            painter.translate(-center_x, -center_y)

        super().paintEvent(event)

    def enterEvent(self, event):
        """鼠标进入"""
        if self._hover_enabled:
            self._update_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        if self._hover_enabled:
            self._update_style(False)
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        if not self._hover_enabled:
            return
        panel = self.parent()
        if panel and hasattr(panel, "_leave_timer"):
            panel._leave_timer.stop()
            panel._context_menu_active = True
        menu = QMenu(self)
        edit_action = menu.addAction("编辑扩展")
        disable_action = menu.addAction("禁用扩展")
        action = menu.exec_(event.globalPos())
        if panel and hasattr(panel, "_context_menu_active"):
            panel._context_menu_active = False
        if action == edit_action:
            self.context_menu_requested.emit(self.plugin_id)
        elif action == disable_action:
            self.context_menu_requested.emit(f"__disable__:{self.plugin_id}")

    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


def _get_assets_dir():
    """获取 assets 目录路径"""
    from pathlib import Path

    return Path(__file__).parent.parent / "assets"


class CenterButton(QLabel):
    """中心返回按钮"""

    clicked = pyqtSignal()
    drag_started = pyqtSignal()
    show_menu = pyqtSignal()

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self._hover_enabled = True
        self._press_pos = None
        self._drag_threshold = 10
        self._is_dragging = False

        self._apply_theme()
        self._update_icon(False)

    def _apply_theme(self):
        """从配置应用主题色"""
        config = get_config()
        theme_key = config.get().get("theme", DEFAULT_THEME)
        colors = theme_from_key(theme_key)
        self.THEME_BG_NORMAL = colors["center_bg_normal"]
        self.THEME_BG_HOVERED = colors["center_bg_hovered"]
        self._theme_icon_normal_color = colors["pie_text_normal"]
        self._theme_icon_hover_color = QColor(255, 255, 255)
        self._update_style(False)

    def refresh_theme(self):
        """刷新主题色"""
        self._apply_theme()
        self._update_icon(False)

    def _update_style(self, hovered: bool):
        """更新样式 - 使用自定义主题色"""
        if hovered:
            bg = self.THEME_BG_HOVERED
        else:
            bg = self.THEME_BG_NORMAL

        radius = self.size // 2
        self.setStyleSheet(f"""
            QLabel {{
                background: rgba({bg.red()}, {bg.green()}, {bg.blue()}, {bg.alpha()});
                border-radius: {radius}px;
                margin: 0px;
                padding: 0px;
            }}
        """)

    def _update_icon(self, hovered: bool):
        """更新图标 - hover时白色，正常时钢青色"""
        from PyQt5.QtWidgets import QApplication

        icon_file = _get_assets_dir() / "arrow-go-back-line-black.svg"

        app = QApplication.instance()
        dpr = app.devicePixelRatio() if app else 1.0

        icon_size = int(56 * 0.618)
        pixmap = QPixmap(int(icon_size * dpr), int(icon_size * dpr))
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)

        renderer = QSvgRenderer(str(icon_file))
        renderer.render(painter)

        # 动态着色：hover 白色，正常时主题色
        color = (
            self._theme_icon_hover_color if hovered else self._theme_icon_normal_color
        )
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        pixmap.setDevicePixelRatio(dpr)
        self.setPixmap(pixmap)

    def enterEvent(self, event):
        """鼠标进入"""
        if self._hover_enabled:
            self._update_style(True)
            self._update_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        if self._hover_enabled:
            self._update_style(False)
            self._update_icon(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and not self._is_dragging:
            distance = (event.globalPos() - self._press_pos).manhattanLength()
            if distance >= self._drag_threshold:
                self._is_dragging = True
                self.drag_started.emit()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._is_dragging and self._press_pos is not None:
                self.clicked.emit()
            self._press_pos = None
            self._is_dragging = False
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        panel = self.parent()
        if panel and hasattr(panel, "_leave_timer"):
            panel._leave_timer.stop()
            panel._context_menu_active = True
        self.show_menu.emit()
        if panel and hasattr(panel, "_context_menu_active"):
            panel._context_menu_active = False


class PiePanel(QWidget):
    """环形菜单面板"""

    plugin_executed = pyqtSignal(str)
    panel_closed = pyqtSignal()
    show_menu = pyqtSignal()
    plugin_edit_requested = pyqtSignal(str)
    plugin_disable_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._preview_mode = False
        self._hover_mode = False
        self._setup_window()
        self._setup_ui()

        self._plugins = {}
        self._buttons = []
        self._button_targets = []
        self._center_pos = QPoint(200, 200)
        self._pie_radius = 0
        self._animation_group = []
        self._is_expanded = False
        self._is_collapsing = False
        self._panel_dragging = False
        self._panel_drag_offset = QPoint()
        self._pending_float_pos = None
        self._context_menu_active = False
        self._shadow_timer = QTimer(self)
        self._shadow_timer.setInterval(16)
        self._shadow_timer.timeout.connect(self.update)

        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(300)
        self._leave_timer.timeout.connect(self._on_leave_timeout)

    def _setup_window(self):
        """设置窗口属性"""
        if self._hover_mode:
            self.setWindowFlags(
                Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            )
        else:
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)

    def _setup_ui(self):
        """设置UI"""
        # 中心返回按钮
        self._center_label = CenterButton(size=80, parent=self)
        self._center_label.clicked.connect(self.hide_panel)
        self._center_label.drag_started.connect(self._start_panel_drag)
        self._center_label.show_menu.connect(self.show_menu.emit)
        self._center_label.hide()

    def set_hover_mode(self, enabled: bool):
        self._hover_mode = enabled

    def enterEvent(self, event):
        self._leave_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._context_menu_active:
            super().leaveEvent(event)
            return
        if self._hover_mode and self._is_expanded and not self._preview_mode:
            self._leave_timer.start()
        super().leaveEvent(event)

    def _on_leave_timeout(self):
        from PyQt5.QtWidgets import QApplication

        global_pos = self.cursor().pos()
        widget = QApplication.widgetAt(global_pos)
        if widget and (widget is self or self.isAncestorOf(widget)):
            return
        if self._is_expanded and not self._is_collapsing:
            self.hide_panel()

    def _start_panel_drag(self):
        self._panel_dragging = True
        self._panel_drag_offset = self.mapFromGlobal(self.cursor().pos())

    def _do_panel_drag(self, global_pos):
        if not self._panel_dragging:
            return
        new_pos = global_pos - self._panel_drag_offset
        self.move(new_pos)

    def _end_panel_drag(self):
        if not self._panel_dragging:
            return
        self._panel_dragging = False
        panel_center_global = self.mapToGlobal(self._center_pos)
        from utils.system_info import SystemInfo

        screen_rect = SystemInfo.get_screen_geometry()
        float_size = get_config().get().get("float_ball_size", 56)
        float_x = panel_center_global.x() - float_size // 2
        float_y = panel_center_global.y() - float_size // 2
        float_x = max(
            screen_rect.left(), min(float_x, screen_rect.right() - float_size)
        )
        float_y = max(
            screen_rect.top(), min(float_y, screen_rect.bottom() - float_size)
        )
        self._pending_float_pos = QPoint(float_x, float_y)

    def set_plugins(self, plugins):
        """设置插件列表"""
        self._plugins = plugins
        self._refresh_plugins_ui()

    def _refresh_plugins_ui(self):
        """刷新插件UI"""
        # 清除现有按钮
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()

        config = get_config()
        cfg = config.get()
        button_size = cfg.get("pie_button_size", 56)

        # 创建新按钮，作为 PiePanel 的子组件
        for plugin_id, plugin_config in self._plugins.items():
            icon_name = plugin_config.icon
            name = plugin_config.name
            description = plugin_config.description

            btn = PieButton(
                plugin_id,
                icon_name,
                name,
                description=description,
                size=button_size,
                parent=self,
            )
            btn.clicked.connect(partial(self._on_plugin_clicked, plugin_id))
            btn.context_menu_requested.connect(self._on_plugin_context_menu)
            btn.hide()
            self._buttons.append(btn)

        print(f"PiePanel: Created {len(self._buttons)} plugin buttons")

    def _on_plugin_clicked(self, plugin_id: str):
        """插件点击"""
        if self._preview_mode:
            return
        self.plugin_executed.emit(plugin_id)
        self.hide_panel()

    def _on_plugin_context_menu(self, payload: str):
        """插件右键菜单回调"""
        if self._preview_mode:
            return
        if payload.startswith("__disable__:"):
            plugin_id = payload[len("__disable__:") :]
            self.plugin_disable_requested.emit(plugin_id)
            self.hide_panel()
        else:
            self.plugin_edit_requested.emit(payload)
            self.hide_panel()

    def enter_preview_mode(self, parent_widget):
        """进入预览模式：展开面板供设置预览，禁用交互"""
        if self._preview_mode:
            return
        self._preview_mode = True
        self._stop_all_animations()
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._refresh_plugins_ui()
        self._center_label.refresh_theme()
        for btn in self._buttons:
            btn.refresh_theme()
        self.show_panel(parent_widget, animate=True)
        for btn in self._buttons:
            btn._hover_enabled = False
        self._center_label._hover_enabled = False

    def exit_preview_mode(self):
        """退出预览模式：恢复 Popup 标志并隐藏面板"""
        if not self._preview_mode:
            return
        self._preview_mode = False
        self._shadow_timer.stop()
        self._stop_all_animations()
        self._is_expanded = False
        self._is_collapsing = False
        self.clearMask()
        self.hide()
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        for btn in self._buttons:
            btn._hover_enabled = True
        self._center_label._hover_enabled = True

    def refresh_preview_layout(self, parent_widget):
        """预览模式下刷新布局（无动画直接重排）"""
        if not self._preview_mode:
            return
        self._stop_all_animations()
        self._refresh_plugins_ui()
        self._center_label.refresh_theme()
        for btn in self._buttons:
            btn.refresh_theme()
        self.show_panel(parent_widget, animate=False)
        for btn in self._buttons:
            btn._hover_enabled = False
        self._center_label._hover_enabled = False

    def _stop_all_animations(self):
        """停止所有动画"""
        for anim in self._animation_group:
            anim.stop()
            anim.deleteLater()
        self._animation_group.clear()

    def show_panel(self, parent_widget, animate=True):
        """显示面板"""
        self.clearMask()
        self._leave_timer.stop()

        if self._hover_mode:
            self.setWindowFlags(
                Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            )
            self.setAttribute(Qt.WA_TranslucentBackground)

        parent_pos = parent_widget.pos()
        parent_size = parent_widget.size()
        parent_radius = parent_size.width() // 2

        screen = parent_widget.screen()
        screen_rect = screen.availableGeometry()

        center_x = parent_pos.x() + parent_radius
        center_y = parent_pos.y() + parent_radius

        panel_radius = self.width() // 2
        panel_x = center_x - panel_radius
        panel_y = center_y - panel_radius

        if panel_x < screen_rect.left():
            panel_x = screen_rect.left()
        if panel_y < screen_rect.top():
            panel_y = screen_rect.top()
        if panel_x + self.width() > screen_rect.right():
            panel_x = screen_rect.right() - self.width()
        if panel_y + self.height() > screen_rect.bottom():
            panel_y = screen_rect.bottom() - self.height()

        self.move(panel_x, panel_y)

        relative_center_x = center_x - panel_x
        relative_center_y = center_y - panel_y
        self._center_pos = QPoint(int(relative_center_x), int(relative_center_y))

        center_label_radius = self._center_label.width() // 2
        self._center_label.move(
            int(relative_center_x - center_label_radius),
            int(relative_center_y - center_label_radius),
        )
        self._center_label.show()

        self._calculate_button_targets(relative_center_x, relative_center_y)

        cfg = get_config().get()
        button_radius = cfg.get("pie_button_size", 56) // 2

        if animate:
            for btn in self._buttons:
                btn._set_scale(0.0)
                btn.move(
                    int(relative_center_x - button_radius),
                    int(relative_center_y - button_radius),
                )
                btn.show()
            self.show()
            self._expand_animations()
        else:
            for i, btn in enumerate(self._buttons):
                btn._set_scale(1.0)
                if i < len(self._button_targets):
                    btn.move(self._button_targets[i])
                btn.show()
            self._is_expanded = True
            self._center_label._hover_enabled = not self._preview_mode
            for btn in self._buttons:
                btn._hover_enabled = not self._preview_mode
            self.show()
            self._apply_mask()
            self.update()

    def _calculate_button_targets(self, center_x: float, center_y: float):
        """计算按钮的目标位置（面板内相对坐标）"""
        num_buttons = len(self._buttons)
        self._button_targets = []
        if num_buttons == 0:
            return

        # 计算环形布局参数
        cfg = get_config().get()
        button_radius = cfg.get("pie_button_size", 56) // 2  # 按钮半径
        center_label_radius = self._center_label.width() // 2  # 中心标签半径
        spacing = cfg.get("pie_spacing", 10)  # 按钮间距

        # 计算外圆半径
        if num_buttons == 1:
            pie_radius = center_label_radius + button_radius + spacing
        elif num_buttons == 2:
            # 特殊处理：两个按钮时直接计算，避免 cos(90°) = 0 的问题
            pie_radius = center_label_radius + button_radius + spacing
        elif num_buttons <= 6:
            angle_step = 360 / num_buttons
            angle_rad = math.radians(angle_step / 2)
            cos_val = math.cos(angle_rad)
            if cos_val > 0.1:
                pie_radius = (center_label_radius + button_radius + spacing) / cos_val
            else:
                pie_radius = center_label_radius + button_radius + spacing
        else:
            circumference = (button_radius * 2 + spacing) * num_buttons
            pie_radius = circumference / (2 * math.pi)
            pie_radius = max(pie_radius, center_label_radius + button_radius + spacing)

        # 安全检查：确保 pie_radius 是有限值
        if not math.isfinite(pie_radius) or pie_radius > 10000:
            pie_radius = center_label_radius + button_radius + spacing

        self._pie_radius = pie_radius

        # 计算每个按钮的目标位置
        for i, btn in enumerate(self._buttons):
            if num_buttons == 1:
                angle = 0
            else:
                angle = i * (360 / num_buttons) - 90
                if num_buttons == 2:
                    angle = i * 180 - 90

            angle_rad = math.radians(angle)

            btn_center_x = center_x + pie_radius * math.cos(angle_rad)
            btn_center_y = center_y + pie_radius * math.sin(angle_rad)

            target = QPoint(
                int(btn_center_x - button_radius), int(btn_center_y - button_radius)
            )
            self._button_targets.append(target)

    def _expand_animations(self):
        """展开动画：按钮从中心飞出到目标位置，同时从小变大"""
        self._is_expanded = True

        self._shadow_timer.start()

        # 动画期间禁用 hover，防止按钮飞出时误触发 hover
        for btn in self._buttons:
            btn._hover_enabled = False
        self._center_label._hover_enabled = False

        # 清除现有动画
        for anim in self._animation_group:
            anim.stop()
            anim.deleteLater()
        self._animation_group.clear()

        button_radius = get_config().get().get("pie_button_size", 56) // 2
        center_start = QPoint(
            int(self._center_pos.x() - button_radius),
            int(self._center_pos.y() - button_radius),
        )

        for i, btn in enumerate(self._buttons):
            target = self._button_targets[i]

            # 位移动画：从中心飞出到目标位置
            pos_anim = QPropertyAnimation(btn, b"pos")
            pos_anim.setDuration(300)
            pos_anim.setStartValue(center_start)
            pos_anim.setEndValue(target)
            pos_anim.setEasingCurve(QEasingCurve.OutBack)

            # 缩放动画：从 0 放大到 1
            scale_anim = QPropertyAnimation(btn, b"scale")
            scale_anim.setDuration(300)
            scale_anim.setStartValue(0.0)
            scale_anim.setEndValue(1.0)
            scale_anim.setEasingCurve(QEasingCurve.OutBack)

            # 错开延迟启动，产生波浪效果
            delay = i * 40
            QTimer.singleShot(delay, pos_anim.start)
            QTimer.singleShot(delay, scale_anim.start)

            self._animation_group.append(pos_anim)
            self._animation_group.append(scale_anim)

        # 动画完成后设置圆形 mask，使空白区域不接收鼠标事件
        total_delay = (len(self._buttons) - 1) * 40 + 300
        QTimer.singleShot(total_delay, self._apply_mask)
        QTimer.singleShot(total_delay, self._on_expand_finished)

    def _on_expand_finished(self):
        """展开动画结束后恢复 hover 并检测鼠标位置"""
        self._shadow_timer.stop()
        self.update()

        for btn in self._buttons:
            btn._hover_enabled = not self._preview_mode
        self._center_label._hover_enabled = not self._preview_mode

        # 检测鼠标下方的组件，应用正确的 hover 状态
        if self._preview_mode:
            return
        from PyQt5.QtWidgets import QApplication

        global_pos = self.cursor().pos()
        widget = QApplication.widgetAt(global_pos)
        if widget == self._center_label:
            self._center_label._update_style(True)
            self._center_label._update_icon(True)
        elif isinstance(widget, PieButton):
            widget._update_style(True)

    def _apply_mask(self):
        """设置圆形 mask，将热区限制为可见内容区域（含阴影空间）"""
        button_radius = get_config().get().get("pie_button_size", 56) // 2
        # mask 半径 = 环形布局半径 + 按钮半径 + 阴影模糊空间
        mask_radius = int(self._pie_radius + button_radius + 22)
        cx = self._center_pos.x()
        cy = self._center_pos.y()
        region = QRegion(
            cx - mask_radius,
            cy - mask_radius,
            mask_radius * 2,
            mask_radius * 2,
            QRegion.Ellipse,
        )
        self.setMask(region)

    def _collapse_animations(self, callback):
        """收起动画：按钮飞回中心，同时缩小"""
        self._is_expanded = False

        self._shadow_timer.start()

        # 清除现有动画
        for anim in self._animation_group:
            anim.stop()
            anim.deleteLater()
        self._animation_group.clear()

        button_radius = get_config().get().get("pie_button_size", 56) // 2
        center_target = QPoint(
            int(self._center_pos.x() - button_radius),
            int(self._center_pos.y() - button_radius),
        )

        for i, btn in enumerate(self._buttons):
            # 位移动画：飞回中心
            pos_anim = QPropertyAnimation(btn, b"pos")
            pos_anim.setDuration(200)
            pos_anim.setStartValue(btn.pos())
            pos_anim.setEndValue(center_target)
            pos_anim.setEasingCurve(QEasingCurve.InQuad)

            # 缩放动画：缩小到 0
            scale_anim = QPropertyAnimation(btn, b"scale")
            scale_anim.setDuration(200)
            scale_anim.setStartValue(btn._scale)
            scale_anim.setEndValue(0.0)
            scale_anim.setEasingCurve(QEasingCurve.InQuad)

            # 反向错开延迟
            delay = (len(self._buttons) - 1 - i) * 30
            QTimer.singleShot(delay, pos_anim.start)
            QTimer.singleShot(delay, scale_anim.start)

            self._animation_group.append(pos_anim)
            self._animation_group.append(scale_anim)

        # 动画结束后执行回调
        total_duration = 200 + (len(self._buttons) - 1) * 30
        QTimer.singleShot(total_duration, callback)

    def hide_panel(self):
        """隐藏面板"""
        if self._preview_mode:
            return
        if not self.isVisible() or self._is_collapsing:
            return

        if self._is_expanded:
            self._is_collapsing = True
            self._collapse_animations(self._hide_immediate)
        else:
            self._hide_immediate()

    def _hide_immediate(self):
        """立即隐藏"""
        self._shadow_timer.stop()
        self._leave_timer.stop()
        self._is_expanded = False
        self._is_collapsing = False
        self.clearMask()
        self.hide()
        self.panel_closed.emit()

    def mouseMoveEvent(self, event):
        if self._panel_dragging:
            self._do_panel_drag(event.globalPos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panel_dragging:
            self._end_panel_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        """隐藏事件 - 拦截 Popup 自动关闭，先播放收起动画"""
        if self._preview_mode:
            super().hideEvent(event)
            return
        if self._hover_mode:
            self._is_expanded = False
            self._is_collapsing = False
            super().hideEvent(event)
            return
        if self._is_expanded and not self._is_collapsing:
            event.ignore()
            self._is_collapsing = True
            # Qt Popup 会强制隐藏窗口，必须立即重新显示才能看到动画
            QTimer.singleShot(0, self.show)
            self._collapse_animations(self._hide_immediate)
            return

        self._is_expanded = False
        self._is_collapsing = False
        super().hideEvent(event)

    def paintEvent(self, event):
        """绘制阴影层 - macOS 风格柔和圆形阴影"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        shadow_color = QColor(0, 0, 0, 46)
        shadow_y_offset = 2
        shadow_spread = 10

        cfg = get_config().get()
        button_radius = cfg.get("pie_button_size", 56) // 2

        # 为每个按钮绘制阴影
        for btn in self._buttons:
            if not btn.isVisible():
                continue
            scale = btn._scale if hasattr(btn, "_scale") else 1.0
            if scale <= 0.01:
                continue

            r = button_radius * scale
            cx = btn.pos().x() + button_radius
            cy = btn.pos().y() + button_radius + shadow_y_offset

            gradient = QRadialGradient(cx, cy, r + shadow_spread)
            gradient.setColorAt(0, shadow_color)
            gradient.setColorAt(0.7, QColor(0, 0, 0, 20))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(
                int(cx - r - shadow_spread),
                int(cy - r - shadow_spread),
                int((r + shadow_spread) * 2),
                int((r + shadow_spread) * 2),
            )

        # 为中心返回按钮绘制阴影
        if self._center_label.isVisible():
            center_r = self._center_label.width() // 2
            if hasattr(self._center_label, "_scale"):
                pass  # center button doesn't scale
            cx = self._center_label.pos().x() + center_r
            cy = self._center_label.pos().y() + center_r + shadow_y_offset

            gradient = QRadialGradient(cx, cy, center_r + shadow_spread)
            gradient.setColorAt(0, shadow_color)
            gradient.setColorAt(0.7, QColor(0, 0, 0, 20))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(
                int(cx - center_r - shadow_spread),
                int(cy - center_r - shadow_spread),
                int((center_r + shadow_spread) * 2),
                int((center_r + shadow_spread) * 2),
            )

        painter.end()
