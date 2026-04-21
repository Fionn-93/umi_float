"""
悬浮球主窗口
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QTimer
from core.config import get_config
from core.state import get_state
from widgets.float_button import FloatButton
from widgets.draggable_widget import DraggableWidget
from widgets.edge_snapper import EdgeSnapper
from utils.system_info import SystemInfo


class FloatWidget(DraggableWidget):
    """悬浮球窗口"""
    
    clicked = pyqtSignal()
    show_menu = pyqtSignal()
    drag_started = pyqtSignal()
    hover_expand = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = get_config()
        self.state = get_state()
        self.screen_rect = SystemInfo.get_screen_geometry()
        self.snapper = EdgeSnapper(snap_threshold=20)
        
        # 用于区分点击和拖动
        self._press_pos = None
        self._drag_threshold = 10
        self._drag_notified = False
        
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(200)
        self._hover_timer.timeout.connect(self.hover_expand.emit)
        
        self._setup_window()
        self._setup_ui()
        
        self.set_drag_callback(self._on_drag)
        self._load_position()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        opacity = self.config.get()['opacity']
        self.setWindowOpacity(opacity)
        
        size = self.config.get()['float_ball_size']
        self.setFixedSize(size, size)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        cfg = self.config.get()
        size = cfg['float_ball_size']
        self.ball = FloatButton(size=size)
        self.ball.set_mode(cfg['display_mode'])
        layout.addWidget(self.ball)
        
        self.setLayout(layout)
    
    def _load_position(self):
        """加载位置"""
        position = self.config.get()['position']
        self.move(position['x'], position['y'])
    
    def apply_settings(self):
        """应用配置变更（设置修改后调用）"""
        cfg = self.config.get()
        size = cfg['float_ball_size']
        opacity = cfg['opacity']
        
        old_size = self.width()
        center = self.pos()
        center_x = center.x() + old_size // 2
        center_y = center.y() + old_size // 2
        
        self.resize(size, size)
        self.setFixedSize(size, size)
        self.setWindowOpacity(opacity)
        
        self.move(center_x - size // 2, center_y - size // 2)
        
        self.ball.set_size(size)
        self.ball.refresh_theme()
        self.ball.set_mode(cfg['display_mode'])
        self.updateGeometry()
        self.repaint()
    
    def _on_drag(self, new_pos):
        """拖动回调"""
        pass
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._drag_notified = False
            self._hover_timer.stop()
            super().mousePressEvent(event)
        elif event.button() == Qt.RightButton:
            self.show_menu.emit()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        super().mouseMoveEvent(event)
        
        # 检测是否超过拖动阈值，发出 drag_started 信号（仅一次）
        if not self._drag_notified and self._press_pos is not None:
            distance = (event.globalPos() - self._press_pos).manhattanLength()
            if distance >= self._drag_threshold:
                self._drag_notified = True
                self._hover_timer.stop()
                self.drag_started.emit()
    
    def snap_to_edge(self):
        """吸附到边缘"""
        pos = self.pos()
        size = (self.width(), self.height())
        snapped_pos = self.snapper.calculate_snap_position(pos, size, self.screen_rect)
        self.move(snapped_pos)
        
        position = {'x': snapped_pos.x(), 'y': snapped_pos.y()}
        self.config.update(position=position)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        
        if event.button() == Qt.LeftButton:
            self.snap_to_edge()
            
            # 检查是否是点击（位移小于阈值）
            if self._press_pos is not None:
                release_pos = event.globalPos()
                distance = (release_pos - self._press_pos).manhattanLength()
                
                # 如果位移小于阈值，认为是点击
                if distance < self._drag_threshold:
                    self.clicked.emit()
                
                self._press_pos = None

    def enterEvent(self, event):
        cfg = self.config.get()
        if cfg.get('pie_expand_mode', 'click') == 'hover':
            self._hover_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_timer.stop()
        super().leaveEvent(event)
