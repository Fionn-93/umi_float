"""
环形面板 - 类似 gnome-pie
"""
import math
from functools import partial

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QByteArray
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient, QRegion, QPixmap
from PyQt5.QtSvg import QSvgRenderer


class PieButton(QLabel):
    """环形菜单按钮"""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon_name: str, name: str, size: int = 64, parent=None):
        super().__init__(parent)
        self.name = name
        self.icon_name = icon_name
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self._scale = 0.0
        
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QApplication, QStyle
        
        # 尝试从系统图标主题获取图标
        icon = QIcon.fromTheme(icon_name)
        if icon.isNull():
            # 如果没有图标，使用首字母
            self.setText(name[0].upper())
        else:
            # 考虑 HiDPI：乘以设备像素比获取高清 pixmap
            app = QApplication.instance()
            dpr = app.devicePixelRatio() if app else 1.0
            icon_size = int(size * 0.618)  # 黄金比例
            pixmap = icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
            pixmap.setDevicePixelRatio(dpr)
            self.setPixmap(pixmap)
        
        # 设置样式
        self._update_style(False)
    
    # 自定义主题色 - 清新配色方案
    THEME_BG_NORMAL = QColor(240, 248, 255, 240)  # 爱丽丝蓝，95%透明度
    THEME_BG_HOVERED = QColor(100, 149, 237, 220)  # 矢车菊蓝，悬停色
    THEME_TEXT_NORMAL = QColor(70, 130, 180)  # 钢青色
    THEME_TEXT_HOVERED = QColor(255, 255, 255)  # 白色
    
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
        self._update_style(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开"""
        self._update_style(False)
        super().leaveEvent(event)
    
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
    
    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        
        self._update_style(False)
        self._update_icon(False)
    
    # 自定义主题色 - 与 PieButton 保持一致
    THEME_BG_NORMAL = QColor(240, 248, 255, 240)  # 爱丽丝蓝
    THEME_BG_HOVERED = QColor(100, 149, 237, 220)  # 矢车菊蓝，悬停色
    
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
            }}
        """)
    
    def _update_icon(self, hovered: bool):
        """更新图标 - 使用固定白色图标"""
        # 始终使用白色图标
        icon_file = _get_assets_dir() / "arrow-go-back-line-white.svg"
        
        # 渲染 SVG
        renderer = QSvgRenderer(str(icon_file))
        icon_size = int(self.size * 0.618)  # 黄金比例
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        self.setPixmap(pixmap)
    
    def enterEvent(self, event):
        """鼠标进入"""
        self._update_style(True)
        self._update_icon(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开"""
        self._update_style(False)
        self._update_icon(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PiePanel(QWidget):
    """环形菜单面板"""
    
    plugin_executed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_window()
        self._setup_ui()
        
        self._plugins = {}
        self._buttons = []
        self._button_targets = []
        self._center_pos = QPoint(200, 200)
        self._pie_radius = 0  # 环形布局半径，用于计算 mask
        self._animation_group = []
        self._is_expanded = False
        self._is_collapsing = False  # 正在播放收起动画
    
    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 面板大小，根据需要调整
        self.setFixedSize(400, 400)
    
    def _setup_ui(self):
        """设置UI"""
        # 中心返回按钮
        self._center_label = CenterButton(size=80, parent=self)
        self._center_label.clicked.connect(self.hide_panel)
        self._center_label.hide()
    
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
        
        # 创建新按钮，作为 PiePanel 的子组件
        for plugin_id, plugin_config in self._plugins.items():
            icon_name = plugin_config.icon
            name = plugin_config.name
            
            btn = PieButton(icon_name, name, size=56, parent=self)
            btn.clicked.connect(partial(self._on_plugin_clicked, plugin_id))
            btn.hide()
            self._buttons.append(btn)
        
        print(f"PiePanel: Created {len(self._buttons)} plugin buttons")
    
    def _on_plugin_clicked(self, plugin_id: str):
        """插件点击"""
        self.plugin_executed.emit(plugin_id)
        self.hide_panel()
    
    def show_panel(self, parent_widget):
        """显示面板"""
        self.clearMask()  # 清除 mask，确保动画过程中按钮可正常显示
        
        parent_pos = parent_widget.pos()
        parent_size = parent_widget.size()
        parent_radius = parent_size.width() // 2
        
        screen = parent_widget.screen()
        screen_rect = screen.availableGeometry()
        
        # 计算中心位置（悬浮球中心，屏幕坐标）
        center_x = parent_pos.x() + parent_radius
        center_y = parent_pos.y() + parent_radius
        
        # 计算面板位置，使悬浮球在面板中心
        panel_radius = self.width() // 2
        panel_x = center_x - panel_radius
        panel_y = center_y - panel_radius
        
        # 边界检测
        if panel_x < screen_rect.left():
            panel_x = screen_rect.left()
        if panel_y < screen_rect.top():
            panel_y = screen_rect.top()
        if panel_x + self.width() > screen_rect.right():
            panel_x = screen_rect.right() - self.width()
        if panel_y + self.height() > screen_rect.bottom():
            panel_y = screen_rect.bottom() - self.height()
        
        self.move(panel_x, panel_y)
        
        # 计算中心点相对于面板的坐标
        relative_center_x = center_x - panel_x
        relative_center_y = center_y - panel_y
        self._center_pos = QPoint(int(relative_center_x), int(relative_center_y))
        
        # 移动中心标签
        center_label_radius = self._center_label.width() // 2
        self._center_label.move(
            int(relative_center_x - center_label_radius),
            int(relative_center_y - center_label_radius)
        )
        self._center_label.show()
        
        # 计算按钮目标位置（使用面板内相对坐标）
        self._calculate_button_targets(relative_center_x, relative_center_y)
        
        # 先把按钮放在中心位置（动画起点）
        button_radius = 56 // 2
        for btn in self._buttons:
            btn._set_scale(0.0)
            btn.move(
                int(relative_center_x - button_radius),
                int(relative_center_y - button_radius)
            )
            btn.show()
        
        # 显示面板
        self.show()
        
        # 启动展开动画
        self._expand_animations()
    
    def _calculate_button_targets(self, center_x: float, center_y: float):
        """计算按钮的目标位置（面板内相对坐标）"""
        num_buttons = len(self._buttons)
        self._button_targets = []
        if num_buttons == 0:
            return
        
        # 计算环形布局参数
        button_radius = 56 // 2  # 按钮半径
        center_label_radius = 40   # 中心标签半径
        spacing = 10               # 按钮间距
        
        # 计算外圆半径
        if num_buttons == 1:
            pie_radius = center_label_radius + button_radius + spacing
        elif num_buttons <= 6:
            angle_step = 360 / num_buttons
            angle_rad = math.radians(angle_step / 2)
            pie_radius = (center_label_radius + button_radius + spacing) / math.cos(angle_rad)
        else:
            circumference = (button_radius * 2 + spacing) * num_buttons
            pie_radius = circumference / (2 * math.pi)
            pie_radius = max(pie_radius, center_label_radius + button_radius + spacing)
        
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
                int(btn_center_x - button_radius),
                int(btn_center_y - button_radius)
            )
            self._button_targets.append(target)
    
    def _expand_animations(self):
        """展开动画：按钮从中心飞出到目标位置，同时从小变大"""
        self._is_expanded = True
        
        # 清除现有动画
        for anim in self._animation_group:
            anim.stop()
            anim.deleteLater()
        self._animation_group.clear()
        
        button_radius = 56 // 2
        center_start = QPoint(
            int(self._center_pos.x() - button_radius),
            int(self._center_pos.y() - button_radius)
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
    
    def _apply_mask(self):
        """设置圆形 mask，将热区限制为可见内容区域"""
        button_radius = 56 // 2
        # mask 半径 = 环形布局半径 + 按钮半径 + 少量 padding
        mask_radius = int(self._pie_radius + button_radius + 8)
        cx = self._center_pos.x()
        cy = self._center_pos.y()
        region = QRegion(
            cx - mask_radius, cy - mask_radius,
            mask_radius * 2, mask_radius * 2,
            QRegion.Ellipse
        )
        self.setMask(region)

    def _collapse_animations(self, callback):
        """收起动画：按钮飞回中心，同时缩小"""
        self._is_expanded = False
        
        # 清除现有动画
        for anim in self._animation_group:
            anim.stop()
            anim.deleteLater()
        self._animation_group.clear()
        
        button_radius = 56 // 2
        center_target = QPoint(
            int(self._center_pos.x() - button_radius),
            int(self._center_pos.y() - button_radius)
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
        if not self.isVisible() or self._is_collapsing:
            return
        
        if self._is_expanded:
            self._is_collapsing = True
            self._collapse_animations(self._hide_immediate)
        else:
            self._hide_immediate()
    
    def _hide_immediate(self):
        """立即隐藏"""
        self._is_expanded = False
        self._is_collapsing = False
        self.clearMask()
        self.hide()
    
    def hideEvent(self, event):
        """隐藏事件 - 拦截 Popup 自动关闭，先播放收起动画"""
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
        """不绘制背景，保持完全透明"""
        pass
