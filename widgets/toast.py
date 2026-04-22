"""
Toast 提示组件 - 页面内浮动提示条
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class ToastWidget(QLabel):
    _toast_instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(36)
        self.hide()
        font = QFont()
        font.setPointSize(13)
        font.setWeight(QFont.Medium)
        self.setFont(font)

    def _reposition(self):
        parent = self.parent()
        if parent is None:
            return
        self.adjustSize()
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 20
        self.move(x, y)

    def show_toast(self, message, success=True):
        bg = "#4CAF50" if success else "#FF6B6B"
        self.setText(message)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: white;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        self._reposition()
        self.raise_()
        self.show()
        self._hide_timer = QTimer.singleShot(3000, self.hide)

    @staticmethod
    def get_instance(parent):
        if ToastWidget._toast_instance is None:
            ToastWidget._toast_instance = ToastWidget(parent)
            ToastWidget._toast_instance.hide()
        return ToastWidget._toast_instance