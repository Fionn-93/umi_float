"""
性能监视器插件 - 主 Widget
"""

import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QProgressBar,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QPoint,
    QSize,
    QEvent,
)
from PyQt5.QtGui import QColor

logger = logging.getLogger(__name__)

from monitor import SystemMonitor, format_bytes, format_rate


class SectionLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #6b7280; "
            "letter-spacing: 1px; padding: 12px 0 6px 4px;"
        )


class MetricRow(QWidget):
    def __init__(self, label: str, accent_color: str, ar: int, ag: int, ab: int):
        super().__init__()
        self._accent = accent_color
        self._ar = ar
        self._ag = ag
        self._ab = ab
        self.setFixedHeight(36)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)

        self._label = QLabel(label)
        self._label.setStyleSheet("font-size: 13px; color: #1f2937; min-width: 80px;")
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setFixedWidth(120)
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: #e5e7eb;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {accent_color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self._progress)

        self._value_label = QLabel()
        self._value_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        self._value_label.setMinimumWidth(100)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._value_label)

        self._unit_label = QLabel()
        self._unit_label.setStyleSheet(
            "font-size: 12px; color: #6b7280; min-width: 60px;"
        )
        layout.addWidget(self._unit_label)

        layout.addStretch()

    def set_value(self, value: float, maximum: float, value_text: str, unit: str = ""):
        pct = int(value / maximum * 100) if maximum > 0 else 0
        self._progress.setValue(pct)
        self._value_label.setText(value_text)
        self._unit_label.setText(unit)

    def set_progress_only(self, percentage: int):
        self._progress.setValue(percentage)

    def set_text(self, label_text: str, value_text: str):
        self._label.setText(label_text)
        self._value_label.setText(value_text)
        self._unit_label.setText("")


class SimpleRow(QWidget):
    def __init__(self, label: str, accent_color: str, ar: int, ag: int, ab: int):
        super().__init__()
        self._accent = accent_color
        self._ar = ar
        self._ag = ag
        self._ab = ab
        self.setFixedHeight(32)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)

        self._label = QLabel(label)
        self._label.setStyleSheet("font-size: 13px; color: #1f2937; min-width: 80px;")
        layout.addWidget(self._label)

        self._value_label = QLabel()
        self._value_label.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #1f2937;"
        )
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._value_label)

        self._unit_label = QLabel()
        self._unit_label.setStyleSheet(
            "font-size: 12px; color: #6b7280; min-width: 60px;"
        )
        layout.addWidget(self._unit_label)

        layout.addStretch()

    def set_value(self, value_text: str, unit: str = ""):
        self._value_label.setText(value_text)
        self._unit_label.setText(unit)


class RateRow(QWidget):
    def __init__(
        self,
        label: str,
        accent_color: str,
        ar: int,
        ag: int,
        ab: int,
        show_bar: bool = True,
    ):
        super().__init__()
        self._accent = accent_color
        self._ar = ar
        self._ag = ag
        self._ab = ab
        self._show_bar = show_bar
        self.setFixedHeight(36)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)

        self._label = QLabel(label)
        self._label.setStyleSheet("font-size: 13px; color: #1f2937; min-width: 80px;")
        layout.addWidget(self._label)

        if show_bar:
            self._bar = QProgressBar()
            self._bar.setFixedWidth(100)
            self._bar.setFixedHeight(6)
            self._bar.setTextVisible(False)
            self._bar.setStyleSheet(f"""
                QProgressBar {{
                    background: #e5e7eb;
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {accent_color};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(self._bar)

        self._value_label = QLabel()
        self._value_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_label.setMinimumWidth(80)
        layout.addWidget(self._value_label)

        layout.addStretch()

    def set_rate(self, bytes_per_sec: float, max_bytes_per_sec: float):
        self._value_label.setText(format_rate(bytes_per_sec))
        if self._show_bar and max_bytes_per_sec > 0:
            pct = int(bytes_per_sec / max_bytes_per_sec * 100)
            self._bar.setValue(min(pct, 100))

    def set_static(self, value_text: str):
        self._value_label.setText(value_text)
        if self._show_bar:
            self._bar.setValue(0)


class PerformanceMonitorWidget(QWidget):
    closed = pyqtSignal()

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._accent_color = host_info.get("accent_color", "#7B61FF")
        self._ar, self._ag, self._ab = self._rgb_from_hex(self._accent_color)
        self._drag_pos = QPoint()
        self._just_shown = False
        self._prev_net_rx = 0
        self._prev_net_tx = 0
        self._prev_disk_r = 0
        self._prev_disk_w = 0
        self._net_baseline_done = False

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 560)

        self._monitor = SystemMonitor.get()

        self._build_ui()
        self._apply_theme_style()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self._refresh_data)
        self._refresh_timer.start()

        self._initial_read_done = False

    def _rgb_from_hex(self, hex_color: str):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return r, g, b

    def _apply_theme_style(self):
        accent = self._accent_color
        ar, ag, ab = self._ar, self._ag, self._ab
        self.setStyleSheet(f"""
            #MainContainer {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
            }}
            #TitleBar {{
                border-bottom: 1px solid rgba(229, 231, 235, 0.5);
            }}
            #WindowTitle {{
                font-size: 14px;
                font-weight: bold;
                color: #1f2937;
            }}
            #CloseBtn {{
                background: transparent;
                color: #86868b;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }}
            #CloseBtn:hover {{
                background: rgba({ar}, {ag}, {ab}, 0.1);
                color: #1d1d1f;
            }}
            #ContentScroll {{
                border: none;
                background: transparent;
            }}
            #ContentWidget {{
                background: transparent;
            }}
        """)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setObjectName("MainContainer")
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setAttribute(Qt.WA_StyledBackground, True)
        title_bar.setFixedHeight(54)
        title_lay = QHBoxLayout(title_bar)
        title_lay.setContentsMargins(20, 0, 10, 0)

        title_lbl = QLabel("性能监视器")
        title_lbl.setObjectName("WindowTitle")
        title_lbl.setCursor(Qt.SizeAllCursor)
        title_lbl.mousePressEvent = self._make_drag(True)
        title_lbl.mouseMoveEvent = self._make_drag(False)
        title_lbl.mouseReleaseEvent = self._make_drag(None)
        title_lay.addWidget(title_lbl)
        title_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        close_btn.enterEvent = lambda e: close_btn.setStyleSheet(
            f"background: rgba({self._ar}, {self._ag}, {self._ab}, 0.1); color: #1d1d1f; border: none; border-radius: 6px; font-size: 16px;"
        )
        close_btn.leaveEvent = lambda e: close_btn.setStyleSheet(
            "background: transparent; color: #86868b; border: none; border-radius: 6px; font-size: 16px;"
        )
        title_lay.addWidget(close_btn)
        container_lay.addWidget(title_bar)

        scroll = QScrollArea()
        scroll.setObjectName("ContentScroll")
        scroll.setStyleSheet("border: none; background: transparent;")
        scroll.setFrameShape(0)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setAttribute(Qt.WA_StyledBackground, True)
        scroll.viewport().setStyleSheet("background: #ffffff;")

        content = QWidget()
        content.setObjectName("ContentWidget")
        content.setAttribute(Qt.WA_StyledBackground, True)
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(16, 8, 16, 16)
        content_lay.setSpacing(0)

        self._cpu_usage_row = MetricRow(
            "CPU 占用", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._cpu_usage_row)

        self._cpu_temp_row = SimpleRow(
            "CPU 温度", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._cpu_temp_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #f3f4f6; max-height: 1px;")
        content_lay.addWidget(sep1)

        self._mem_used_row = MetricRow(
            "内存", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._mem_used_row)

        self._swap_used_row = MetricRow(
            "交换空间", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._swap_used_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #f3f4f6; max-height: 1px;")
        content_lay.addWidget(sep2)

        self._net_down_row = RateRow(
            "↓ 下行", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._net_down_row)

        self._net_up_row = RateRow(
            "↑ 上行", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._net_up_row)

        self._net_total_down_row = SimpleRow(
            "↓ 累计下行", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._net_total_down_row)

        self._net_total_up_row = SimpleRow(
            "↑ 累计上行", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._net_total_up_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("background: #f3f4f6; max-height: 1px;")
        content_lay.addWidget(sep3)

        self._disk_read_row = RateRow(
            "磁盘读取", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._disk_read_row)

        self._disk_write_row = RateRow(
            "磁盘写入", self._accent_color, self._ar, self._ag, self._ab
        )
        content_lay.addWidget(self._disk_write_row)

        content_lay.addStretch()

        scroll.setWidget(content)
        container_lay.addWidget(scroll)

        self.main_layout.addWidget(container)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)

    def _make_drag(self, press):
        def handler(event):
            if press is True:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            elif press is False and event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self._drag_pos)
                event.accept()

        return handler

    def _refresh_data(self):
        try:
            data = self._monitor.get_all()

            cpu_usage = data["cpu_usage"]
            self._cpu_usage_row.set_value(cpu_usage, 100, f"{cpu_usage:.1f}", "%")

            cpu_temp = data["cpu_temp"]
            if cpu_temp > 0:
                self._cpu_temp_row.set_value(f"{cpu_temp:.1f}", "°C")
            else:
                self._cpu_temp_row.set_value("N/A", "")

            mem_used = data["mem_used"]
            mem_total = data["mem_total"]
            if mem_total > 0:
                self._mem_used_row.set_value(
                    mem_used,
                    mem_total,
                    f"{format_bytes(mem_used)} / {format_bytes(mem_total)}",
                    "",
                )
            else:
                self._mem_used_row.set_value(0, 1, "N/A", "")

            swap_used = data["swap_used"]
            swap_total = data["swap_total"]
            if swap_total > 0:
                self._swap_used_row.set_value(
                    swap_used,
                    swap_total,
                    f"{format_bytes(swap_used)} / {format_bytes(swap_total)}",
                    "",
                )
            else:
                self._swap_used_row.set_value(0, 1, "N/A", "")

            net_rates = data["net_rates"]
            total_rx = data["total_rx"]
            total_tx = data["total_tx"]

            total_down_rate = sum(r for _, (r, _) in net_rates.items())
            total_up_rate = sum(t for _, (_, t) in net_rates.items())

            if self._net_baseline_done:
                self._net_down_row.set_rate(total_down_rate, 100 * 1024 * 1024)
                self._net_up_row.set_rate(total_up_rate, 50 * 1024 * 1024)
            else:
                self._net_down_row.set_static("—")
                self._net_up_row.set_static("—")
                self._net_baseline_done = True

            self._net_total_down_row.set_value(format_bytes(total_rx), "")
            self._net_total_up_row.set_value(format_bytes(total_tx), "")

            disk_read = data["disk_read_delta"]
            disk_write = data["disk_write_delta"]

            if self._initial_read_done:
                self._disk_read_row.set_rate(disk_read, 200 * 1024 * 1024)
                self._disk_write_row.set_rate(disk_write, 200 * 1024 * 1024)
            else:
                self._disk_read_row.set_static("—")
                self._disk_write_row.set_static("—")
                self._initial_read_done = True

        except Exception as e:
            logger.warning("Performance monitor refresh failed: %s", e)

    def _on_close(self):
        self.closed.emit()

    def showEvent(self, event):
        super().showEvent(event)
        self._just_shown = True
        QTimer.singleShot(100, self.activateWindow)
        QTimer.singleShot(300, self._clear_just_shown)

    def _clear_just_shown(self):
        self._just_shown = False

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if self.isVisible() and not self.isActiveWindow() and not self._just_shown:
                self.closed.emit()
        super().changeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        super().closeEvent(event)
