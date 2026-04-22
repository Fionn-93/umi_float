"""
插件编辑对话框 - 新建/编辑扩展
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap

from ui.icon_picker_dialog import IconPickerDialog
from utils.theme_colors import get_current_accent_color


class PluginEditDialog(QDialog):
    """插件编辑对话框"""

    def __init__(
        self,
        plugin_id: str = None,
        name: str = "",
        description: str = "",
        icon: str = "",
        exec_cmd: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._plugin_id = plugin_id
        self._name = name
        self._description = description
        self._icon = icon
        self._exec = exec_cmd
        self._accent_color = get_current_accent_color()

        self.setWindowTitle("编辑扩展" if plugin_id else "新建扩展")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(400, 320)
        self.resize(420, 340)
        self.setStyleSheet("background-color: #ffffff;")

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self._name_input = self._add_field(layout, "名称", self._name)

        self._desc_input = QTextEdit()
        self._desc_input.setPlainText(self._description)
        self._desc_input.setFixedHeight(60)
        self._desc_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                color: #333333;
                background: #ffffff;
            }}
            QTextEdit:focus {{
                border-color: {self._accent_color};
            }}
        """)
        desc_layout = QHBoxLayout()
        desc_label = QLabel("描述")
        desc_label.setFixedWidth(60)
        desc_label.setStyleSheet(
            "color: #333333; font-size: 13px; background: transparent;"
        )
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self._desc_input)
        layout.addLayout(desc_layout)

        icon_layout = QHBoxLayout()
        icon_label = QLabel("图标")
        icon_label.setFixedWidth(60)
        icon_label.setStyleSheet(
            "color: #333333; font-size: 13px; background: transparent;"
        )
        icon_layout.addWidget(icon_label)

        self._icon_input = QLineEdit(self._icon)
        self._icon_input.setPlaceholderText("图标名称或路径")
        self._icon_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                color: #333333;
                background: #ffffff;
            }}
            QLineEdit:focus {{
                border-color: {self._accent_color};
            }}
        """)
        icon_layout.addWidget(self._icon_input)

        pick_btn = QPushButton("选择")
        pick_btn.setFixedSize(60, 32)
        pick_btn.setCursor(Qt.PointingHandCursor)
        pick_btn.clicked.connect(self._pick_icon)
        pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: #ffffff;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: #f5f5f5;
                border-color: {self._accent_color};
            }}
        """)
        icon_layout.addWidget(pick_btn)

        self._icon_preview = QLabel()
        self._icon_preview.setFixedSize(32, 32)
        self._icon_preview.setAlignment(Qt.AlignCenter)
        self._icon_preview.setStyleSheet(
            "background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px;"
        )
        icon_layout.addWidget(self._icon_preview)

        layout.addLayout(icon_layout)
        self._update_icon_preview()

        self._exec_input = self._add_field(layout, "命令", self._exec)

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

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 32)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.clicked.connect(self._on_ok)
        accent = self._accent_color
        r = int(accent[1:3], 16)
        g = int(accent[3:5], 16)
        b = int(accent[5:7], 16)
        ok_btn.setStyleSheet(f"""
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
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _add_field(self, layout: QVBoxLayout, label: str, value: str) -> QLineEdit:
        row_layout = QHBoxLayout()

        label_widget = QLabel(label)
        label_widget.setFixedWidth(60)
        label_widget.setStyleSheet(
            "color: #333333; font-size: 13px; background: transparent;"
        )
        row_layout.addWidget(label_widget)

        input_widget = QLineEdit(value)
        input_widget.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                color: #333333;
                background: #ffffff;
            }}
            QLineEdit:focus {{
                border-color: {self._accent_color};
            }}
        """)
        row_layout.addWidget(input_widget)

        layout.addLayout(row_layout)
        return input_widget

    def _pick_icon(self):
        dialog = IconPickerDialog(self._icon_input.text(), self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.get_selected_icon()
            if selected:
                self._icon_input.setText(selected)
                self._update_icon_preview()

    def _update_icon_preview(self):
        icon_name = self._icon_input.text()
        if not icon_name:
            self._icon_preview.clear()
            return

        from PyQt5.QtWidgets import QApplication

        app = QApplication.instance()
        dpr = app.devicePixelRatio() if app else 1.0

        if icon_name.startswith("icons/"):
            from core.constants import DATA_DIR

            icon_path = DATA_DIR / icon_name
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        int(28 * dpr),
                        int(28 * dpr),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    scaled.setDevicePixelRatio(dpr)
                    self._icon_preview.setPixmap(scaled)
                    return

        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            pixmap = icon.pixmap(int(28 * dpr), int(28 * dpr))
            pixmap.setDevicePixelRatio(dpr)
            self._icon_preview.setPixmap(pixmap)
        else:
            self._icon_preview.clear()

    def _on_ok(self):
        name = self._name_input.text().strip()
        if not name:
            self._name_input.setFocus()
            return

        exec_cmd = self._exec_input.text().strip()
        if not exec_cmd:
            self._exec_input.setFocus()
            return

        self._name = name
        self._description = self._desc_input.toPlainText().strip()
        self._icon = self._icon_input.text().strip()
        self._exec = exec_cmd

        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self._name,
            "description": self._description,
            "icon": self._icon,
            "exec": self._exec,
        }

    def get_plugin_id(self) -> Optional[str]:
        return self._plugin_id
