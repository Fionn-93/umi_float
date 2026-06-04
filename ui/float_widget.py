"""
悬浮球主窗口
支持贴边自动切换为胶囊性能监视器
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import (
    Qt, QRect, pyqtSignal, QTimer, QPoint,
    QPropertyAnimation, QParallelAnimationGroup, QEasingCurve,
)
from PyQt5.QtGui import QCursor
from core.config import get_config
from core.state import get_state
from widgets.float_button import FloatButton
from widgets.draggable_widget import DraggableWidget
from widgets.edge_snapper import EdgeSnapper
from utils.system_info import SystemInfo

CAPSULE_WIDTH = 8
EXPAND_DURATION = 250
COLLAPSE_FADE_DURATION = 200
CAPSULE_FADE_IN_DURATION = 100
HOVER_ZONE_WIDTH = 24
HOVER_ZONE_V_EXTRA = 50
EDGE_HOVER_CHECK_MS = 50
EXPAND_SCALE_FROM = 0.5
COLLAPSE_SCALE_TO = 0.5


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

        self._press_pos = None
        self._drag_threshold = 10
        self._drag_notified = False

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(200)
        self._hover_timer.timeout.connect(self.hover_expand.emit)

        self._state = "normal"
        self._saved_display_mode = None
        self._edge_side = None
        self._animating = False
        self._anim_group = None

        self._edge_hover_timer = QTimer(self)
        self._edge_hover_timer.setInterval(EDGE_HOVER_CHECK_MS)
        self._edge_hover_timer.timeout.connect(self._check_edge_hover)

        self._setup_window()
        self._setup_ui()

        self.set_drag_callback(self._on_drag)
        self._load_position()

        QTimer.singleShot(0, self._check_startup_edge)

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        opacity = self.config.get()["opacity"]
        self.setWindowOpacity(opacity)

        size = self.config.get()["float_ball_size"]
        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        cfg = self.config.get()
        size = cfg["float_ball_size"]
        self.ball = FloatButton(size=size)
        self.ball.set_mode(cfg["display_mode"])
        layout.addWidget(self.ball)

        self.setLayout(layout)

    def _load_position(self):
        """加载位置"""
        position = self.config.get()["position"]
        self.move(position["x"], position["y"])

    def _check_startup_edge(self):
        edge = self.snapper.get_snapped_edge(
            self.pos(), (self.width(), self.height()), self.screen_rect,
        )
        if edge in ("left", "right"):
            self._enter_capsule_mode(edge, animated=False)

    def _get_capsule_size(self):
        ball_size = self.config.get()["float_ball_size"]
        return CAPSULE_WIDTH, ball_size

    def _snap_capsule_pos(self, cw, ch):
        center_y = self.pos().y() + self.height() // 2
        if self._edge_side == "left":
            tx = self.screen_rect.left()
        else:
            tx = self.screen_rect.right() - cw
        ty = center_y - ch // 2
        ty = max(self.screen_rect.top(), min(ty, self.screen_rect.bottom() - ch))
        return tx, ty

    def _snap_circle_pos(self, ball_size):
        center_y = self.pos().y() + self.height() // 2
        if self._edge_side == "left":
            tx = self.screen_rect.left()
        else:
            tx = self.screen_rect.right() - ball_size
        ty = center_y - ball_size // 2
        ty = max(self.screen_rect.top(), min(ty, self.screen_rect.bottom() - ball_size))
        return tx, ty

    # -- state transitions --

    def _enter_capsule_mode(self, edge, animated=True):
        if self._animating:
            return
        if self._state == "capsule":
            return

        self._saved_display_mode = self.config.get()["display_mode"]
        self._state = "capsule"
        self._edge_side = edge

        ball_size = self.config.get()["float_ball_size"]
        cw, ch = self._get_capsule_size()

        if animated:
            self._animate_to_capsule(cw, ch)
        else:
            self._snap_capsule(cw, ch)

    def _expand_from_capsule(self):
        if self._state != "capsule" or self._animating:
            return

        self._state = "hover_expanded"
        self._edge_hover_timer.stop()

        ball_size = self.config.get()["float_ball_size"]
        tx, ty = self._snap_circle_pos(ball_size)

        self._animate_expand(tx, ty, ball_size)

    def _collapse_to_capsule(self):
        if self._state != "hover_expanded" or self._animating:
            return

        self._state = "capsule"
        self.ball.timer.setInterval(1000)

        cw, ch = self._get_capsule_size()

        self._animate_collapse(cw, ch)

    def _enter_normal_mode(self):
        if self._state == "normal" or self._animating:
            return

        self._state = "normal"
        self._edge_side = None
        self._saved_display_mode = None
        self._edge_hover_timer.stop()

        ball_size = self.config.get()["float_ball_size"]
        self.ball._capsule_mode = False
        self.ball.setFixedSize(ball_size, ball_size)
        self.ball.set_size(ball_size)
        self.ball.set_mode(self.config.get()["display_mode"])
        self.ball._scale = 1.0
        self.setMinimumSize(ball_size, ball_size)
        self.setMaximumSize(ball_size, ball_size)

    # -- snap helpers (instant, no animation) --

    def _snap_capsule(self, cw, ch):
        tx, ty = self._snap_capsule_pos(cw, ch)
        self.ball._capsule_mode = True
        self.ball.setFixedSize(cw, ch)
        self.ball._scale = 1.0
        self.setMinimumSize(cw, ch)
        self.setMaximumSize(cw, ch)
        self.setGeometry(tx, ty, cw, ch)
        self.setWindowOpacity(self.config.get()["opacity"])
        self._save_position()
        self._edge_hover_timer.start()

    def _snap_circle(self, tx, ty, ball_size):
        self.ball._capsule_mode = False
        self.ball.setFixedSize(ball_size, ball_size)
        self.ball.set_size(ball_size)
        self.ball.set_mode(self._saved_display_mode)
        self.setMinimumSize(ball_size, ball_size)
        self.setMaximumSize(ball_size, ball_size)
        self.setGeometry(tx, ty, ball_size, ball_size)

    # -- animations --

    def _animate_expand(self, tx, ty, ball_size):
        self._animating = True
        self._dragging = False

        self._snap_circle(tx, ty, ball_size)
        self.ball._scale = EXPAND_SCALE_FROM
        self.setWindowOpacity(0.0)
        self.show()

        if self._anim_group is not None:
            self._anim_group.stop()
            self._anim_group.deleteLater()
            self._anim_group = None

        self._anim_group = QParallelAnimationGroup(self)

        target_opacity = self.config.get()["opacity"]

        scale_anim = QPropertyAnimation(self.ball, b"scale")
        scale_anim.setStartValue(EXPAND_SCALE_FROM)
        scale_anim.setEndValue(1.0)
        scale_anim.setDuration(EXPAND_DURATION)
        scale_anim.setEasingCurve(QEasingCurve.OutBack)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(target_opacity)
        opacity_anim.setDuration(EXPAND_DURATION)
        opacity_anim.setEasingCurve(QEasingCurve.OutQuad)

        self._anim_group.addAnimation(scale_anim)
        self._anim_group.addAnimation(opacity_anim)
        self._anim_group.finished.connect(self._on_expand_finished)
        self._anim_group.start()

    def _on_expand_finished(self):
        self._animating = False
        self.setWindowOpacity(self.config.get()["opacity"])
        self.ball._scale = 1.0

    def _animate_collapse(self, cw, ch):
        self._animating = True
        self._dragging = False

        if self._anim_group is not None:
            self._anim_group.stop()
            self._anim_group.deleteLater()
            self._anim_group = None

        self._anim_group = QParallelAnimationGroup(self)

        current_opacity = self.windowOpacity()

        scale_anim = QPropertyAnimation(self.ball, b"scale")
        scale_anim.setStartValue(1.0)
        scale_anim.setEndValue(COLLAPSE_SCALE_TO)
        scale_anim.setDuration(COLLAPSE_FADE_DURATION)
        scale_anim.setEasingCurve(QEasingCurve.InBack)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setStartValue(current_opacity)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setDuration(COLLAPSE_FADE_DURATION)
        opacity_anim.setEasingCurve(QEasingCurve.InQuad)

        self._anim_group.addAnimation(scale_anim)
        self._anim_group.addAnimation(opacity_anim)
        self._anim_group.finished.connect(
            lambda: self._on_collapse_fade_finished(cw, ch)
        )
        self._anim_group.start()

    def _on_collapse_fade_finished(self, cw, ch):
        tx, ty = self._snap_capsule_pos(cw, ch)

        self.ball._capsule_mode = True
        self.ball.setFixedSize(cw, ch)
        self.ball._scale = 1.0
        self.setMinimumSize(cw, ch)
        self.setMaximumSize(cw, ch)
        self.setGeometry(tx, ty, cw, ch)

        target_opacity = self.config.get()["opacity"]

        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(target_opacity)
        self._fade_in_anim.setDuration(CAPSULE_FADE_IN_DURATION)
        self._fade_in_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_in_anim.finished.connect(self._on_collapse_done)
        self._fade_in_anim.start()

    def _on_collapse_done(self):
        self._animating = False
        self.setWindowOpacity(self.config.get()["opacity"])
        self._save_position()
        self._edge_hover_timer.start()

    def _animate_to_capsule(self, cw, ch):
        self._animating = True
        self._dragging = False

        if self._anim_group is not None:
            self._anim_group.stop()
            self._anim_group.deleteLater()
            self._anim_group = None

        self._anim_group = QParallelAnimationGroup(self)

        current_opacity = self.windowOpacity()

        scale_anim = QPropertyAnimation(self.ball, b"scale")
        scale_anim.setStartValue(1.0)
        scale_anim.setEndValue(COLLAPSE_SCALE_TO)
        scale_anim.setDuration(COLLAPSE_FADE_DURATION)
        scale_anim.setEasingCurve(QEasingCurve.InBack)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setStartValue(current_opacity)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setDuration(COLLAPSE_FADE_DURATION)
        opacity_anim.setEasingCurve(QEasingCurve.InQuad)

        self._anim_group.addAnimation(scale_anim)
        self._anim_group.addAnimation(opacity_anim)
        self._anim_group.finished.connect(
            lambda: self._on_to_capsule_fade_finished(cw, ch)
        )
        self._anim_group.start()

    def _on_to_capsule_fade_finished(self, cw, ch):
        tx, ty = self._snap_capsule_pos(cw, ch)

        self.ball._capsule_mode = True
        self.ball.setFixedSize(cw, ch)
        self.ball._scale = 1.0
        self.setMinimumSize(cw, ch)
        self.setMaximumSize(cw, ch)
        self.setGeometry(tx, ty, cw, ch)

        target_opacity = self.config.get()["opacity"]

        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(target_opacity)
        self._fade_in_anim.setDuration(CAPSULE_FADE_IN_DURATION)
        self._fade_in_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_in_anim.finished.connect(self._on_to_capsule_done)
        self._fade_in_anim.start()

    def _on_to_capsule_done(self):
        self._animating = False
        self.setWindowOpacity(self.config.get()["opacity"])
        self._save_position()
        self._edge_hover_timer.start()

    # -- edge hover detection --

    def _check_edge_hover(self):
        if self._state != "capsule" or self._animating:
            return

        cursor_pos = QCursor.pos()
        capsule_geo = self.geometry()

        zone = QRect(
            capsule_geo.x() - HOVER_ZONE_WIDTH,
            capsule_geo.y() - HOVER_ZONE_V_EXTRA,
            capsule_geo.width() + 2 * HOVER_ZONE_WIDTH,
            capsule_geo.height() + 2 * HOVER_ZONE_V_EXTRA,
        )

        if zone.contains(cursor_pos):
            self._edge_hover_timer.stop()
            QTimer.singleShot(150, self._expand_from_capsule)

    # -- config --

    def _save_position(self):
        position = {"x": self.pos().x(), "y": self.pos().y()}
        self.config.update(position=position)

    def apply_settings(self):
        """应用配置变更（设置修改后调用）"""
        cfg = self.config.get()
        size = cfg["float_ball_size"]
        opacity = cfg["opacity"]

        if self._state == "normal":
            old_size = self.width()
            center = self.pos()
            center_x = center.x() + old_size // 2
            center_y = center.y() + old_size // 2

            self.setMinimumSize(size, size)
            self.setMaximumSize(size, size)
            self.setWindowOpacity(opacity)

            self.move(center_x - size // 2, center_y - size // 2)

            self.ball.set_size(size)
            self.ball.refresh_theme()
            self.ball.set_mode(cfg["display_mode"])
        elif self._state == "capsule":
            cw, ch = self._get_capsule_size()
            tx, ty = self._snap_capsule_pos(cw, ch)
            self.ball.setFixedSize(cw, ch)
            self.ball.refresh_theme()
            self._snap_capsule(cw, ch)
            self.setWindowOpacity(opacity)
        elif self._state == "hover_expanded":
            self.setWindowOpacity(opacity)
            self.ball.set_size(size)
            self.ball.refresh_theme()
            self.ball.set_mode(self._saved_display_mode)

        self.updateGeometry()
        self.repaint()

    def _on_drag(self, new_pos):
        """拖动回调"""
        pass

    # -- mouse events --

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            if self._state == "capsule":
                event.accept()
                return
            self._press_pos = event.globalPos()
            self._drag_notified = False
            self._hover_timer.stop()
            self._edge_hover_timer.stop()
            super().mousePressEvent(event)
        elif event.button() == Qt.RightButton:
            if self._state == "capsule":
                event.accept()
                return
            self.show_menu.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        super().mouseMoveEvent(event)

        if not self._drag_notified and self._press_pos is not None:
            distance = (event.globalPos() - self._press_pos).manhattanLength()
            if distance >= self._drag_threshold:
                self._drag_notified = True
                self._hover_timer.stop()
                self._edge_hover_timer.stop()
                self.drag_started.emit()

    def snap_to_edge(self):
        """吸附到边缘"""
        pos = self.pos()
        size = (self.width(), self.height())
        snapped_pos = self.snapper.calculate_snap_position(pos, size, self.screen_rect)
        self.move(snapped_pos)

        position = {"x": snapped_pos.x(), "y": snapped_pos.y()}
        self.config.update(position=position)

        edge = self.snapper.get_snapped_edge(snapped_pos, size, self.screen_rect)

        if self._animating:
            return

        if edge in ("left", "right"):
            if self._state == "normal":
                self._enter_capsule_mode(edge)
            elif self._state == "hover_expanded":
                self._enter_capsule_mode(edge)
        else:
            if self._state == "hover_expanded":
                self._enter_normal_mode()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)

        if event.button() == Qt.LeftButton:
            if self._state in ("capsule",):
                self._press_pos = None
                return

            self.snap_to_edge()

            if self._state == "hover_expanded":
                if self._press_pos is not None:
                    release_pos = event.globalPos()
                    distance = (release_pos - self._press_pos).manhattanLength()
                    if distance < self._drag_threshold:
                        self._collapse_to_capsule()
                self._press_pos = None
                return

            if self._press_pos is not None:
                release_pos = event.globalPos()
                distance = (release_pos - self._press_pos).manhattanLength()

                if distance < self._drag_threshold:
                    self.clicked.emit()

                self._press_pos = None

    def enterEvent(self, event):
        if self._state == "capsule":
            event.accept()
            return
        cfg = self.config.get()
        if cfg.get("pie_expand_mode", "click") == "hover":
            self._hover_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_timer.stop()
        if self._state == "hover_expanded" and not self._dragging:
            self._collapse_to_capsule()
            return
        super().leaveEvent(event)
