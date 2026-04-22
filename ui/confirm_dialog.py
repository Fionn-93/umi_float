"""
确认对话框 - 统一样式的确认/警告对话框
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils.theme_colors import get_current_accent_color


class ConfirmDialog(QDialog):
    """确认对话框 - 统一样式"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._message = message
        self._accent_color = get_current_accent_color()

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(360)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("", 16, QFont.Bold))
        title_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        layout.addWidget(title_label)

        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(
            "color: #333333; font-size: 13px; background: transparent; line-height: 1.5;"
        )
        layout.addWidget(message_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #f5f5f5;
                border-color: #d0d0d0;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        accent = self._accent_color
        r = int(accent[1:3], 16)
        g = int(accent[3:5], 16)
        b = int(accent[5:7], 16)
        confirm_btn = QPushButton("确定")
        confirm_btn.setFixedSize(80, 32)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba({r}, {g}, {b}, 0.8);
            }}
        """)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

        self.setStyleSheet("background-color: #ffffff;")
