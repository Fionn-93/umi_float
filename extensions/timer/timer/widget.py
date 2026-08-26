"""计时器插件 - 综合计时器（番茄钟/倒计时/正计时）"""

import json
import logging
import subprocess
import time
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QStackedWidget,
    QProgressBar,
    QApplication,
)
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRectF,
    QSize,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtSignal,
    QEvent,
)
from PyQt5.QtGui import QColor, QFont, QPainter, QIcon, QPixmap, QBrush, QLinearGradient
from PyQt5.QtSvg import QSvgRenderer

logger = logging.getLogger(__name__)

_ICONS_DIR = Path(__file__).parent.parent / "icons"
_ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"

TOMATO_ICON = str(_ICONS_DIR / "tomato.svg")
CUP_ICON = str(_ICONS_DIR / "cup-fill.svg")
HOURGLASS_ICON = str(_ICONS_DIR / "hourglass-2-fill.svg")
TIMER_ICON = str(_ICONS_DIR / "timer-fill.svg")

STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"

DEFAULT_WORK_MIN = 25
DEFAULT_BREAK_MIN = 5
DEFAULT_COUNTDOWN_MIN = 5


class StyledProgressBar(QProgressBar):
    def __init__(self, accent_color="#7B61FF", parent=None):
        super().__init__(parent)
        self._accent_color = accent_color
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_accent_color(self, color):
        self._accent_color = color

    def set_value_animated(self, value):
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = self.rect()
        h = r.height()
        bar_r = h / 2.0

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#e5e7eb"))
        painter.drawRoundedRect(r, bar_r, bar_r)

        pct = self.value() / max(self.maximum() - self.minimum(), 1)
        if pct > 0:
            c = r.width() * pct
            if c < bar_r * 2:
                progress_r = QRectF(r.x(), r.y(), c, h)
                painter.setBrush(QColor(self._accent_color))
                painter.drawRoundedRect(progress_r, bar_r, bar_r)
            else:
                clip = QRectF(r.x(), r.y(), c, h)
                painter.setClipRect(clip)
                grad = QLinearGradient(0, 0, c, 0)
                bg = QColor(self._accent_color)
                grad.setColorAt(0.0, bg)
                grad.setColorAt(1.0, bg.lighter(110))
                painter.setBrush(QBrush(grad))
                painter.drawRoundedRect(r, bar_r, bar_r)

        painter.end()


class PomodoroPage(QWidget):
    def __init__(self, parent_widget):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._parent = parent_widget
        self._state = STATE_IDLE
        self._phase = "work"
        self._work_min = DEFAULT_WORK_MIN
        self._break_min = DEFAULT_BREAK_MIN
        self._remaining_sec = 0
        self._total_sec = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(800)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(14)

        settings_row = QHBoxLayout()
        settings_row.setSpacing(16)

        work_layout = QVBoxLayout()
        work_layout.setSpacing(4)
        work_label = QLabel("工作时间")
        work_label.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold;")
        self._work_spin = QSpinBox()
        self._work_spin.setRange(1, 120)
        self._work_spin.setValue(DEFAULT_WORK_MIN)
        self._work_spin.setFixedHeight(32)
        self._work_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._work_spin.setStyleSheet(
            "QSpinBox { border: 1px solid #e5e7eb; border-radius: 6px; "
            "padding: 2px 8px; font-size: 13px; color: #1f2937; background: #ffffff; "
            "text-align: center; }"
            "QSpinBox::up-button, QSpinBox::down-button { width: 0px; }"
            "QSpinBox::up-arrow, QSpinBox::down-arrow { width: 0px; }"
        )
        self._work_spin.valueChanged.connect(self._on_settings_changed)
        work_layout.addWidget(work_label)

        work_spin_row = QHBoxLayout()
        work_spin_row.setSpacing(4)
        work_spin_row.addWidget(self._work_spin)
        work_unit = QLabel("分钟")
        work_unit.setStyleSheet("color: #6b7280; font-size: 13px;")
        work_spin_row.addWidget(work_unit)
        work_layout.addLayout(work_spin_row)

        work_pills = QHBoxLayout()
        work_pills.setSpacing(6)
        for v in [15, 25, 45]:
            pill = self._create_pill(str(v), v, self._work_spin)
            work_pills.addWidget(pill)
        work_pills.addStretch()
        work_layout.addLayout(work_pills)

        break_layout = QVBoxLayout()
        break_layout.setSpacing(4)
        break_label = QLabel("休息时间")
        break_label.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold;")
        self._break_spin = QSpinBox()
        self._break_spin.setRange(1, 60)
        self._break_spin.setValue(DEFAULT_BREAK_MIN)
        self._break_spin.setFixedHeight(32)
        self._break_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._break_spin.setStyleSheet(
            "QSpinBox { border: 1px solid #e5e7eb; border-radius: 6px; "
            "padding: 2px 8px; font-size: 13px; color: #1f2937; background: #ffffff; "
            "text-align: center; }"
            "QSpinBox::up-button, QSpinBox::down-button { width: 0px; }"
            "QSpinBox::up-arrow, QSpinBox::down-arrow { width: 0px; }"
        )
        self._break_spin.valueChanged.connect(self._on_settings_changed)
        break_layout.addWidget(break_label)

        break_spin_row = QHBoxLayout()
        break_spin_row.setSpacing(4)
        break_spin_row.addWidget(self._break_spin)
        break_unit = QLabel("分钟")
        break_unit.setStyleSheet("color: #6b7280; font-size: 13px;")
        break_spin_row.addWidget(break_unit)
        break_layout.addLayout(break_spin_row)

        break_pills = QHBoxLayout()
        break_pills.setSpacing(6)
        for v in [5, 10, 15]:
            pill = self._create_pill(str(v), v, self._break_spin)
            break_pills.addWidget(pill)
        break_pills.addStretch()
        break_layout.addLayout(break_pills)

        settings_row.addLayout(work_layout)
        settings_row.addLayout(break_layout)

        self._config_widget = QWidget()
        config_layout = QVBoxLayout(self._config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(14)
        config_layout.addLayout(settings_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        sep.setFixedHeight(1)
        config_layout.addWidget(sep)

        layout.addWidget(self._config_widget)

        status_row = QHBoxLayout()
        status_row.setAlignment(Qt.AlignCenter)
        status_row.setSpacing(6)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )
        self._dot_color = "#9ca3af"
        self._dot_rgb = (156, 163, 175)

        self._status_label = QLabel("准备开始")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            "color: #1f2937; font-size: 14px; font-weight: bold;"
        )
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_label)
        layout.addLayout(status_row)

        font_time = QFont()
        font_time.setPointSize(48)
        font_time.setBold(True)
        self._time_label = QLabel("25:00")
        self._time_label.setFont(font_time)
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("color: #1f2937;")
        layout.addWidget(self._time_label)

        self._progress_bar = StyledProgressBar(accent_color=self._parent.accent_color)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        layout.addWidget(self._progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._action_btn = QPushButton()
        self._action_btn.setFixedHeight(38)
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.setObjectName("ActionBtn")
        ar, ag, ab = self._parent.accent_rgb
        self._action_btn.setStyleSheet(
            "QPushButton#ActionBtn { background: "
            + self._parent.accent_color
            + "; color: #ffffff; "
            "border: none; border-radius: 12px; font-size: 14px; font-weight: bold; "
            "padding: 0 18px; }"
            "QPushButton#ActionBtn:hover { background: rgba(%d,%d,%d,0.85); }"
            % (ar, ag, ab)
        )
        self._action_btn.clicked.connect(self._on_action)
        self._update_action_btn_text("开始")

        self._stop_btn = QPushButton()
        self._stop_btn.setFixedHeight(38)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setObjectName("StopBtn")
        self._stop_btn.setStyleSheet(
            "QPushButton#StopBtn { background: transparent; color: #6b7280; "
            "border: 1px solid #e5e7eb; border-radius: 12px; font-size: 14px; }"
            "QPushButton#StopBtn:hover { background: rgba(0,0,0,0.04); "
            "border-color: #d1d5db; color: #1f2937; }"
        )
        self._stop_btn.clicked.connect(self.stop)
        self._update_stop_btn_text()

        btn_row.addWidget(self._action_btn)
        btn_row.addWidget(self._stop_btn)
        layout.addLayout(btn_row)

    def _create_pill(self, label, value, spinbox):
        btn = QPushButton(label)
        btn.setFixedHeight(26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background: #f3f4f6; border: none; border-radius: 13px; "
            "padding: 0 12px; font-size: 11px; color: #6b7280; font-weight: 600; }"
            "QPushButton:hover { background: #e5e7eb; color: #1f2937; }"
        )
        btn.clicked.connect(lambda checked, v=value: spinbox.setValue(v))
        return btn

    def _update_action_btn_text(self, text):
        self._action_btn.setText(text)
        if text == "开始":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        elif text == "暂停":
            icon = self._parent._load_svg_icon("pause-fill", QColor("#ffffff"))
        elif text == "继续":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        else:
            icon = QIcon()
        self._action_btn.setIcon(icon)
        self._action_btn.setIconSize(QSize(16, 16))

    def _update_stop_btn_text(self):
        self._stop_btn.setText("停止")
        icon = self._parent._load_svg_icon("stop-line", QColor("#6b7280"))
        self._stop_btn.setIcon(icon)
        self._stop_btn.setIconSize(QSize(16, 16))

    def _on_settings_changed(self):
        if self._state == STATE_IDLE:
            self._work_min = self._work_spin.value()
            self._break_min = self._break_spin.value()
            self._parent._save_settings()
            self._reset_display()

    def _update_config_visible(self):
        self._config_widget.setVisible(self._state == STATE_IDLE)

    def _on_action(self):
        if self._state == STATE_IDLE:
            self._parent._stop_any_active(self)
            self._work_min = self._work_spin.value()
            self._break_min = self._break_spin.value()
            self._parent._save_settings()
            self._start_work()
        elif self._state == STATE_RUNNING:
            self._pause()
        elif self._state == STATE_PAUSED:
            self._resume()

    def _start_work(self):
        self._state = STATE_RUNNING
        self._phase = "work"
        self._total_sec = self._work_min * 60
        self._remaining_sec = self._total_sec
        self._update_config_visible()
        self._update_action_btn_text("暂停")
        self._work_spin.setEnabled(False)
        self._break_spin.setEnabled(False)
        self._timer.start()
        self._progress_bar.show()
        self._pulse_timer.start()
        self._update_display()

    def _start_break(self):
        self._state = STATE_RUNNING
        self._phase = "break"
        self._total_sec = self._break_min * 60
        self._remaining_sec = self._total_sec
        self._update_config_visible()
        self._update_action_btn_text("暂停")
        self._timer.start()
        self._progress_bar.show()
        self._pulse_timer.start()
        self._update_display()

    def _pause(self):
        self._state = STATE_PAUSED
        self._timer.stop()
        self._pulse_timer.stop()
        self._update_action_btn_text("继续")
        self._update_display()

    def _resume(self):
        if self._remaining_sec <= 0:
            self.stop()
            return
        self._state = STATE_RUNNING
        self._update_action_btn_text("暂停")
        self._timer.start()
        self._pulse_timer.start()
        self._update_display()

    def stop(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._pulse_phase = False
        self._state = STATE_IDLE
        self._phase = "work"
        self._remaining_sec = 0
        self._total_sec = 0
        self._update_config_visible()
        self._update_action_btn_text("开始")
        self._work_spin.setEnabled(True)
        self._break_spin.setEnabled(True)
        self._reset_display()
        if self._parent._is_active_timer(self):
            self._parent._clear_float_display()

    def _tick(self):
        self._remaining_sec -= 1
        if self._remaining_sec <= 0:
            self._remaining_sec = 0
            self._on_period_end()
        self._update_display()

    def _on_period_end(self):
        self._timer.stop()
        self._pulse_timer.stop()
        if self._phase == "work":
            self._parent._notify("工作完成", "休息 %d 分钟" % self._break_min)
            self._start_break()
        else:
            self._parent._notify(
                "休息结束", "开始下一个番茄 (%d 分钟)" % self._work_min
            )
            self._start_work()

    def _pulse_tick(self):
        self._pulse_phase = not self._pulse_phase
        if self._pulse_phase:
            self._status_dot.setStyleSheet(
                "background: %s; border-radius: 4px; border: none;" % self._dot_color
            )
        else:
            r, g, b = self._dot_rgb
            self._status_dot.setStyleSheet(
                "background: rgba(%d,%d,%d,0.3); border-radius: 4px; border: none;"
                % (r, g, b)
            )

    def _update_display(self):
        if self._state == STATE_IDLE:
            return
        minutes = self._remaining_sec // 60
        seconds = self._remaining_sec % 60
        time_str = "%02d:%02d" % (minutes, seconds)
        self._time_label.setText(time_str)

        if self._phase == "work":
            status = "工作中"
            icon_path = TOMATO_ICON
            progress = (
                self._remaining_sec / self._total_sec if self._total_sec > 0 else 0
            )
            dot_color = self._parent.accent_color
        else:
            status = "休息中"
            icon_path = CUP_ICON
            progress = (
                self._remaining_sec / self._total_sec if self._total_sec > 0 else 0
            )
            dot_color = "#4CAF50"

        if self._state == STATE_PAUSED:
            status = "已暂停"
            dot_color = "#f59e0b"

        self._status_label.setText(status)
        self._dot_color = dot_color
        c = dot_color
        self._dot_rgb = (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        self._status_dot.setStyleSheet(
            "background: %s; border-radius: 4px; border: none;" % dot_color
        )
        self._progress_bar.set_value_animated(int(progress * 100))
        if self._parent._is_active_timer(self):
            self._parent._update_float_display(time_str, progress, icon_path)

    def _reset_display(self):
        minutes = self._work_spin.value()
        self._time_label.setText("%02d:00" % minutes)
        self._status_label.setText("准备开始")
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )
        self._progress_bar.hide()
        self._progress_bar.set_value_animated(0)

    def load_settings(self, data):
        self._work_min = data.get("work_min", DEFAULT_WORK_MIN)
        self._break_min = data.get("break_min", DEFAULT_BREAK_MIN)
        self._work_spin.blockSignals(True)
        self._work_spin.setValue(self._work_min)
        self._work_spin.blockSignals(False)
        self._break_spin.blockSignals(True)
        self._break_spin.setValue(self._break_min)
        self._break_spin.blockSignals(False)
        self._reset_display()

    def to_settings(self):
        return {"work_min": self._work_min, "break_min": self._break_min}


class CountdownPage(QWidget):
    def __init__(self, parent_widget):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._parent = parent_widget
        self._state = STATE_IDLE
        self._total_min = DEFAULT_COUNTDOWN_MIN
        self._remaining_sec = 0
        self._total_sec = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(800)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(14)

        dur_layout = QVBoxLayout()
        dur_layout.setSpacing(4)
        dur_label = QLabel("倒计时时长")
        dur_label.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold;")
        self._dur_spin = QSpinBox()
        self._dur_spin.setRange(1, 180)
        self._dur_spin.setValue(DEFAULT_COUNTDOWN_MIN)
        self._dur_spin.setFixedHeight(32)
        self._dur_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._dur_spin.setStyleSheet(
            "QSpinBox { border: 1px solid #e5e7eb; border-radius: 6px; "
            "padding: 2px 8px; font-size: 13px; color: #1f2937; background: #ffffff; "
            "text-align: center; }"
            "QSpinBox::up-button, QSpinBox::down-button { width: 0px; }"
            "QSpinBox::up-arrow, QSpinBox::down-arrow { width: 0px; }"
        )
        self._dur_spin.valueChanged.connect(self._on_settings_changed)
        dur_layout.addWidget(dur_label)

        dur_spin_row = QHBoxLayout()
        dur_spin_row.setSpacing(4)
        dur_spin_row.addWidget(self._dur_spin)
        dur_unit = QLabel("分钟")
        dur_unit.setStyleSheet("color: #6b7280; font-size: 13px;")
        dur_spin_row.addWidget(dur_unit)
        dur_layout.addLayout(dur_spin_row)

        dur_pills = QHBoxLayout()
        dur_pills.setSpacing(6)
        for v in [5, 10, 30]:
            pill = self._create_pill(str(v), v, self._dur_spin)
            dur_pills.addWidget(pill)
        dur_pills.addStretch()
        dur_layout.addLayout(dur_pills)

        self._config_widget = QWidget()
        config_layout = QVBoxLayout(self._config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(14)
        config_layout.addLayout(dur_layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        sep.setFixedHeight(1)
        config_layout.addWidget(sep)

        layout.addWidget(self._config_widget)

        status_row = QHBoxLayout()
        status_row.setAlignment(Qt.AlignCenter)
        status_row.setSpacing(6)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )
        self._dot_color = "#9ca3af"
        self._dot_rgb = (156, 163, 175)

        self._status_label = QLabel("准备开始")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            "color: #1f2937; font-size: 14px; font-weight: bold;"
        )
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_label)
        layout.addLayout(status_row)

        font_time = QFont()
        font_time.setPointSize(48)
        font_time.setBold(True)
        self._time_label = QLabel("05:00")
        self._time_label.setFont(font_time)
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("color: #1f2937;")
        layout.addWidget(self._time_label)

        self._progress_bar = StyledProgressBar(accent_color=self._parent.accent_color)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        layout.addWidget(self._progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._action_btn = QPushButton()
        self._action_btn.setFixedHeight(38)
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.setObjectName("ActionBtn")
        ar, ag, ab = self._parent.accent_rgb
        self._action_btn.setStyleSheet(
            "QPushButton#ActionBtn { background: "
            + self._parent.accent_color
            + "; color: #ffffff; "
            "border: none; border-radius: 12px; font-size: 14px; font-weight: bold; "
            "padding: 0 18px; }"
            "QPushButton#ActionBtn:hover { background: rgba(%d,%d,%d,0.85); }"
            % (ar, ag, ab)
        )
        self._action_btn.clicked.connect(self._on_action)
        self._update_action_btn_text("开始")

        self._reset_btn = QPushButton()
        self._reset_btn.setFixedHeight(38)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setObjectName("StopBtn")
        self._reset_btn.setStyleSheet(
            "QPushButton#StopBtn { background: transparent; color: #6b7280; "
            "border: 1px solid #e5e7eb; border-radius: 12px; font-size: 14px; }"
            "QPushButton#StopBtn:hover { background: rgba(0,0,0,0.04); "
            "border-color: #d1d5db; color: #1f2937; }"
        )
        self._reset_btn.clicked.connect(self._reset)
        self._update_reset_btn_text()

        btn_row.addWidget(self._action_btn)
        btn_row.addWidget(self._reset_btn)
        layout.addLayout(btn_row)

    def _create_pill(self, label, value, spinbox):
        btn = QPushButton(label)
        btn.setFixedHeight(26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background: #f3f4f6; border: none; border-radius: 13px; "
            "padding: 0 12px; font-size: 11px; color: #6b7280; font-weight: 600; }"
            "QPushButton:hover { background: #e5e7eb; color: #1f2937; }"
        )
        btn.clicked.connect(lambda checked, v=value: spinbox.setValue(v))
        return btn

    def _update_action_btn_text(self, text):
        self._action_btn.setText(text)
        if text == "开始":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        elif text == "暂停":
            icon = self._parent._load_svg_icon("pause-fill", QColor("#ffffff"))
        elif text == "继续":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        else:
            icon = QIcon()
        self._action_btn.setIcon(icon)
        self._action_btn.setIconSize(QSize(16, 16))

    def _update_reset_btn_text(self):
        self._reset_btn.setText("停止")
        icon = self._parent._load_svg_icon("stop-line", QColor("#6b7280"))
        self._reset_btn.setIcon(icon)
        self._reset_btn.setIconSize(QSize(16, 16))

    def _on_settings_changed(self):
        if self._state == STATE_IDLE:
            self._total_min = self._dur_spin.value()
            self._parent._save_settings()
            self._reset_display()

    def _update_config_visible(self):
        self._config_widget.setVisible(self._state == STATE_IDLE)

    def _on_action(self):
        if self._state == STATE_IDLE:
            self._parent._stop_any_active(self)
            self._total_min = self._dur_spin.value()
            self._start()
        elif self._state == STATE_RUNNING:
            self._pause()
        elif self._state == STATE_PAUSED:
            self._resume()

    def _start(self):
        self._state = STATE_RUNNING
        self._total_sec = self._total_min * 60
        self._remaining_sec = self._total_sec
        self._update_config_visible()
        self._update_action_btn_text("暂停")
        self._dur_spin.setEnabled(False)
        self._timer.start()
        self._progress_bar.show()
        self._pulse_timer.start()
        self._update_display()

    def _pause(self):
        self._state = STATE_PAUSED
        self._timer.stop()
        self._pulse_timer.stop()
        self._update_action_btn_text("继续")
        self._update_display()

    def _resume(self):
        if self._remaining_sec <= 0:
            self._reset()
            return
        self._state = STATE_RUNNING
        self._update_action_btn_text("暂停")
        self._timer.start()
        self._pulse_timer.start()
        self._update_display()

    def _reset(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._pulse_phase = False
        self._state = STATE_IDLE
        self._remaining_sec = 0
        self._total_sec = 0
        self._update_config_visible()
        self._update_action_btn_text("开始")
        self._dur_spin.setEnabled(True)
        self._reset_display()
        if self._parent._is_active_timer(self):
            self._parent._clear_float_display()

    def stop(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._state = STATE_IDLE
        self._remaining_sec = 0
        self._total_sec = 0
        self._update_config_visible()
        self._update_action_btn_text("开始")
        self._dur_spin.setEnabled(True)
        self._reset_display()
        self._parent._clear_float_display()

    def _tick(self):
        self._remaining_sec -= 1
        if self._remaining_sec <= 0:
            self._remaining_sec = 0
            self._on_complete()
        self._update_display()

    def _on_complete(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._state = STATE_IDLE
        self._update_action_btn_text("开始")
        self._dur_spin.setEnabled(True)
        self._update_config_visible()
        self._parent._notify("倒计时结束", "设定的 %d 分钟已到" % self._total_min)
        self._reset_display()
        if self._parent._is_active_timer(self):
            self._parent._clear_float_display()

    def _pulse_tick(self):
        self._pulse_phase = not self._pulse_phase
        if self._pulse_phase:
            self._status_dot.setStyleSheet(
                "background: %s; border-radius: 4px; border: none;" % self._dot_color
            )
        else:
            r, g, b = self._dot_rgb
            self._status_dot.setStyleSheet(
                "background: rgba(%d,%d,%d,0.3); border-radius: 4px; border: none;"
                % (r, g, b)
            )

    def _update_display(self):
        minutes = self._remaining_sec // 60
        seconds = self._remaining_sec % 60
        time_str = "%02d:%02d" % (minutes, seconds)
        self._time_label.setText(time_str)
        progress = self._remaining_sec / self._total_sec if self._total_sec > 0 else 0

        if self._state == STATE_RUNNING:
            status = "倒计时中"
            dot_color = self._parent.accent_color
        else:
            status = "已暂停"
            dot_color = "#f59e0b"

        self._status_label.setText(status)
        self._dot_color = dot_color
        c = dot_color
        self._dot_rgb = (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        self._status_dot.setStyleSheet(
            "background: %s; border-radius: 4px; border: none;" % dot_color
        )
        self._progress_bar.set_value_animated(int(progress * 100))
        if self._parent._is_active_timer(self):
            self._parent._update_float_display(time_str, progress, HOURGLASS_ICON)

    def _reset_display(self):
        self._time_label.setText("%02d:00" % self._dur_spin.value())
        self._status_label.setText("准备开始")
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )
        self._progress_bar.hide()
        self._progress_bar.set_value_animated(0)

    def load_settings(self, data):
        self._total_min = data.get("countdown_min", DEFAULT_COUNTDOWN_MIN)
        self._dur_spin.blockSignals(True)
        self._dur_spin.setValue(self._total_min)
        self._dur_spin.blockSignals(False)
        self._reset_display()

    def to_settings(self):
        return {"countdown_min": self._total_min}


class StopwatchPage(QWidget):
    def __init__(self, parent_widget):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._parent = parent_widget
        self._state = STATE_IDLE
        self._elapsed_sec = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(800)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(14)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        status_row = QHBoxLayout()
        status_row.setAlignment(Qt.AlignCenter)
        status_row.setSpacing(6)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )
        self._dot_color = "#9ca3af"
        self._dot_rgb = (156, 163, 175)

        self._status_label = QLabel("准备开始")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            "color: #1f2937; font-size: 14px; font-weight: bold;"
        )
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_label)
        layout.addLayout(status_row)

        font_time = QFont()
        font_time.setPointSize(48)
        font_time.setBold(True)
        self._time_label = QLabel("00:00")
        self._time_label.setFont(font_time)
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("color: #1f2937;")
        layout.addWidget(self._time_label)

        self._progress_bar = StyledProgressBar(accent_color=self._parent.accent_color)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._action_btn = QPushButton()
        self._action_btn.setFixedHeight(38)
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.setObjectName("ActionBtn")
        ar, ag, ab = self._parent.accent_rgb
        self._action_btn.setStyleSheet(
            "QPushButton#ActionBtn { background: "
            + self._parent.accent_color
            + "; color: #ffffff; "
            "border: none; border-radius: 12px; font-size: 14px; font-weight: bold; "
            "padding: 0 18px; }"
            "QPushButton#ActionBtn:hover { background: rgba(%d,%d,%d,0.85); }"
            % (ar, ag, ab)
        )
        self._action_btn.clicked.connect(self._on_action)
        self._update_action_btn_text("开始")

        self._reset_btn = QPushButton()
        self._reset_btn.setFixedHeight(38)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setObjectName("StopBtn")
        self._reset_btn.setStyleSheet(
            "QPushButton#StopBtn { background: transparent; color: #6b7280; "
            "border: 1px solid #e5e7eb; border-radius: 12px; font-size: 14px; }"
            "QPushButton#StopBtn:hover { background: rgba(0,0,0,0.04); "
            "border-color: #d1d5db; color: #1f2937; }"
        )
        self._reset_btn.clicked.connect(self._reset)
        self._update_reset_btn_text()

        btn_row.addWidget(self._action_btn)
        btn_row.addWidget(self._reset_btn)
        layout.addLayout(btn_row)

    def _update_action_btn_text(self, text):
        self._action_btn.setText(text)
        if text == "开始":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        elif text == "暂停":
            icon = self._parent._load_svg_icon("pause-fill", QColor("#ffffff"))
        elif text == "继续":
            icon = self._parent._load_svg_icon("play-fill", QColor("#ffffff"))
        else:
            icon = QIcon()
        self._action_btn.setIcon(icon)
        self._action_btn.setIconSize(QSize(16, 16))

    def _update_reset_btn_text(self):
        self._reset_btn.setText("停止")
        icon = self._parent._load_svg_icon("stop-line", QColor("#6b7280"))
        self._reset_btn.setIcon(icon)
        self._reset_btn.setIconSize(QSize(16, 16))

    def _on_action(self):
        if self._state == STATE_IDLE:
            self._parent._stop_any_active(self)
            self._start()
        elif self._state == STATE_RUNNING:
            self._pause()
        elif self._state == STATE_PAUSED:
            self._resume()

    def _start(self):
        self._state = STATE_RUNNING
        self._update_action_btn_text("暂停")
        self._timer.start()
        self._pulse_timer.start()
        self._update_display()

    def _pause(self):
        self._state = STATE_PAUSED
        self._timer.stop()
        self._pulse_timer.stop()
        self._update_action_btn_text("继续")
        self._update_display()

    def _resume(self):
        self._state = STATE_RUNNING
        self._update_action_btn_text("暂停")
        self._timer.start()
        self._pulse_timer.start()
        self._update_display()

    def _reset(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._pulse_phase = False
        self._state = STATE_IDLE
        self._elapsed_sec = 0
        self._update_action_btn_text("开始")
        self._reset_display()
        if self._parent._is_active_timer(self):
            self._parent._clear_float_display()

    def stop(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._state = STATE_IDLE
        self._elapsed_sec = 0
        self._update_action_btn_text("开始")
        self._reset_display()
        self._parent._clear_float_display()

    def _tick(self):
        self._elapsed_sec += 1
        self._update_display()

    def _pulse_tick(self):
        self._pulse_phase = not self._pulse_phase
        if self._pulse_phase:
            self._status_dot.setStyleSheet(
                "background: %s; border-radius: 4px; border: none;" % self._dot_color
            )
        else:
            r, g, b = self._dot_rgb
            self._status_dot.setStyleSheet(
                "background: rgba(%d,%d,%d,0.3); border-radius: 4px; border: none;"
                % (r, g, b)
            )

    def _update_display(self):
        minutes = self._elapsed_sec // 60
        seconds = self._elapsed_sec % 60
        time_str = "%02d:%02d" % (minutes, seconds)
        hours = self._elapsed_sec // 3600
        if hours > 0:
            time_str = "%d:%s" % (hours, time_str)
        self._time_label.setText(time_str)

        if self._state == STATE_RUNNING:
            status = "计时中"
            dot_color = self._parent.accent_color
        else:
            status = "已暂停"
            dot_color = "#f59e0b"

        self._status_label.setText(status)
        self._dot_color = dot_color
        c = dot_color
        self._dot_rgb = (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        self._status_dot.setStyleSheet(
            "background: %s; border-radius: 4px; border: none;" % dot_color
        )

        if self._parent._is_active_timer(self):
            progress = min(1.0, self._elapsed_sec / 3600.0)
            self._parent._update_float_display(time_str, progress, TIMER_ICON)

    def _reset_display(self):
        self._time_label.setText("00:00")
        self._status_label.setText("准备开始")
        self._status_dot.setStyleSheet(
            "background: #9ca3af; border-radius: 4px; border: none;"
        )


class TimerWidget(QWidget):
    closed = pyqtSignal()
    pin_toggled = pyqtSignal(bool)

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._accent_color = host_info.get("accent_color", "#7B61FF")
        self._data_dir: Path = host_info.get("data_dir")
        if self._data_dir:
            self._data_dir.mkdir(parents=True, exist_ok=True)

        self._set_float_display = host_info.get("set_float_display")
        self._clear_float_display_handler = host_info.get("clear_float_display")
        self._active_timer_page = None
        self._drag_pos = QPoint()
        self._pinned = False
        self._shown_at = 0.0

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 400)

        self._build_ui()
        self._load_settings()

    @property
    def accent_color(self):
        return self._accent_color

    @property
    def accent_rgb(self):
        c = self._accent_color
        return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        container = QFrame()
        container.setObjectName("MainContainer")
        container.setStyleSheet(
            "#MainContainer { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; }"
            "QPushButton:focus { outline: none; }"
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(25)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)

        title_bar = self._build_title_bar()
        container_layout.addWidget(title_bar)

        self._pomodoro_page = PomodoroPage(self)
        self._countdown_page = CountdownPage(self)
        self._stopwatch_page = StopwatchPage(self)

        self._filter_bar = QWidget()
        self._filter_bar.setObjectName("FilterBar")
        self._filter_bar.setFixedHeight(44)
        self._filter_bar.setAttribute(Qt.WA_StyledBackground, True)
        filter_lay = QHBoxLayout(self._filter_bar)
        filter_lay.setContentsMargins(20, 8, 16, 8)
        filter_lay.setSpacing(8)

        self._tab_btns = []
        self._tab_labels = ["番茄钟", "倒计时", "正计时"]
        for i, label in enumerate(self._tab_labels):
            btn = QPushButton(label)
            btn.setObjectName("FilterTabBtn")
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setProperty("active", i == 0)
            btn.clicked.connect(lambda checked, idx=i: self._on_tab_clicked(idx))
            filter_lay.addWidget(btn)
            self._tab_btns.append(btn)
        filter_lay.addStretch()

        ar, ag, ab = self.accent_rgb
        self._filter_bar.setStyleSheet(
            f"#FilterTabBtn {{"
            f"    background: #f4f6f8;"
            f"    color: #6b7280;"
            f"    border: none;"
            f"    border-radius: 14px;"
            f"    font-size: 12px;"
            f"    font-weight: 500;"
            f"    padding: 0 16px;"
            f"}}"
            f"#FilterTabBtn:hover {{"
            f"    background: #ebedf0;"
            f"    color: #374151;"
            f"}}"
            f'#FilterTabBtn[active="true"] {{'
            f"    background: {self._accent_color};"
            f"    color: #ffffff;"
            f"}}"
            f'#FilterTabBtn[active="true"]:hover {{'
            f"    background: rgba({ar}, {ag}, {ab}, 0.85);"
            f"}}"
        )

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pomodoro_page)
        self._stack.addWidget(self._countdown_page)
        self._stack.addWidget(self._stopwatch_page)

        container_layout.addWidget(self._filter_bar)
        container_layout.addWidget(self._stack)
        root.addWidget(container)

    def _build_title_bar(self):
        bar = QFrame()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(54)
        bar.setStyleSheet(
            "#TitleBar { border-bottom: 1px solid rgba(229,231,235,0.5); }"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("计时器")
        title.setObjectName("WindowTitle")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")
        layout.addWidget(title)
        layout.addStretch()

        self._pin_btn = QPushButton()
        self._pin_btn.setObjectName("PinBtn")
        self._pin_btn.setFixedSize(32, 32)
        self._pin_btn.setCursor(Qt.PointingHandCursor)
        self._pin_btn.setStyleSheet("background: transparent; border: none;")
        self._pin_btn.setIcon(self._load_pin_icon(False))
        self._pin_btn.enterEvent = lambda e: self._update_pin_hover(True)
        self._pin_btn.leaveEvent = lambda e: self._update_pin_hover(False)
        self._pin_btn.clicked.connect(self._on_pin_clicked)
        layout.addWidget(self._pin_btn)

        close_btn = QPushButton()
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton#CloseBtn { background: transparent; border: none; "
            "border-radius: 6px; }"
            "QPushButton#CloseBtn:hover { background: rgba(%d,%d,%d,0.1); }"
            % self.accent_rgb
        )
        close_icon = self._load_svg_icon("close-line", QColor("#86868b"))
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(QSize(18, 18))
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        return bar

    def _load_svg_icon(self, name: str, color: QColor) -> QIcon:
        svg_path = _ASSETS_DIR / f"{name}.svg"
        app = QApplication.instance()
        dpr = app.devicePixelRatio() if app else 1.0
        icon_size = int(16 * dpr)
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        QSvgRenderer(str(svg_path)).render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        pixmap.setDevicePixelRatio(dpr)
        return QIcon(pixmap)

    def _on_tab_clicked(self, index):
        for i, btn in enumerate(self._tab_btns):
            active = i == index
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._stack.setCurrentIndex(index)

    def showEvent(self, event):
        super().showEvent(event)
        self._shown_at = time.monotonic()
        QTimer.singleShot(100, self.activateWindow)

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if self.isVisible() and not self._pinned:
                elapsed = time.monotonic() - self._shown_at
                if not self.isActiveWindow() and elapsed > 0.5:
                    self.hide()
        super().changeEvent(event)

    def _load_pin_icon(self, filled: bool, color=None) -> QIcon:
        name = "pushpin-fill" if filled else "pushpin-line"
        if color is None:
            color = QColor(self._accent_color) if filled else QColor("#86868b")
        elif isinstance(color, str):
            color = QColor(color)
        return self._load_svg_icon(name, color)

    def _update_pin_hover(self, hovered: bool):
        if self._pinned:
            return
        color = "#1d1d1f" if hovered else "#86868b"
        self._pin_btn.setIcon(self._load_pin_icon(False, color))

    def _on_pin_clicked(self):
        self._pinned = not self._pinned
        self._pin_btn.setIcon(self._load_pin_icon(self._pinned))
        self.pin_toggled.emit(self._pinned)

    def _stop_any_active(self, source):
        if (
            self._active_timer_page is not None
            and self._active_timer_page is not source
        ):
            self._active_timer_page.stop()
            self._clear_float_display()
        self._active_timer_page = source

    def _is_active_timer(self, page):
        return self._active_timer_page is page

    def _update_float_display(self, text: str, progress: float, icon_path: str):
        if self._set_float_display:
            self._set_float_display(text, progress, icon_path)

    def _clear_float_display(self):
        self._active_timer_page = None
        if self._clear_float_display_handler:
            self._clear_float_display_handler()

    def _notify(self, title, message):
        try:
            subprocess.Popen(["notify-send", "-a", "umi-float", title, message])
        except Exception:
            pass

    def _load_settings(self):
        if not self._data_dir:
            return
        settings_file = self._data_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._pomodoro_page.load_settings(data)
                self._countdown_page.load_settings(data)
            except Exception as e:
                logger.warning("加载计时器设置失败: %s", e)

    def _save_settings(self):
        if not self._data_dir:
            return
        settings_file = self._data_dir / "settings.json"
        try:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            data.update(self._pomodoro_page.to_settings())
            data.update(self._countdown_page.to_settings())
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("保存计时器设置失败: %s", e)

    def _on_close(self):
        self.hide()

    def closeEvent(self, event):
        self._on_close()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
