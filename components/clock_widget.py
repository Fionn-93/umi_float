"""
时钟组件
"""

from PyQt5.QtWidgets import QLabel, QCalendarWidget, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont


class ClockWidget(QLabel):
    """时钟组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        self._update_time()

    def _setup_ui(self):
        """设置UI"""
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 12, QFont.Bold))
        self._update_time()

    def _setup_timer(self):
        """设置定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

    def _update_time(self):
        """更新时间"""
        current_time = QDate.currentDate().toString("hh:mm:ss")
        self.setText(current_time)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self._show_calendar()
        super().mousePressEvent(event)

    def _show_calendar(self):
        """显示日历"""
        dialog = QDialog(self)
        dialog.setWindowTitle("日历")
        dialog.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        calendar = QCalendarWidget()

        today = QDate.currentDate()
        calendar.setSelectedDate(today)

        layout.addWidget(calendar)
        dialog.setLayout(layout)

        dialog.move(self.mapToGlobal(self.rect().bottomLeft()))
        dialog.exec_()
