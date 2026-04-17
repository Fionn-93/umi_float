"""
插件编辑对话框 - 新建/编辑扩展
"""
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

from ui.icon_picker_dialog import IconPickerDialog


class PluginEditDialog(QDialog):
    """插件编辑对话框"""
    
    def __init__(self, plugin_id: str = None, name: str = "", description: str = "",
                 icon: str = "", exec_cmd: str = "", parent=None):
        super().__init__(parent)
        self._plugin_id = plugin_id
        self._name = name
        self._description = description
        self._icon = icon
        self._exec = exec_cmd
        
        self.setWindowTitle("编辑扩展" if plugin_id else "新建扩展")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(400, 320)
        self.resize(420, 340)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        self._name_input = self._add_field(layout, "名称", self._name)
        
        self._desc_input = QTextEdit()
        self._desc_input.setPlainText(self._description)
        self._desc_input.setFixedHeight(60)
        self._desc_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                color: #1d1d1f;
                background: #ffffff;
            }
            QTextEdit:focus {
                border-color: #1976D2;
            }
        """)
        desc_layout = QHBoxLayout()
        desc_label = QLabel("描述")
        desc_label.setFixedWidth(60)
        desc_label.setStyleSheet("color: #1d1d1f; font-size: 13px;")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self._desc_input)
        layout.addLayout(desc_layout)
        
        icon_layout = QHBoxLayout()
        icon_label = QLabel("图标")
        icon_label.setFixedWidth(60)
        icon_label.setStyleSheet("color: #1d1d1f; font-size: 13px;")
        icon_layout.addWidget(icon_label)
        
        self._icon_input = QLineEdit(self._icon)
        self._icon_input.setPlaceholderText("图标名称或路径")
        self._icon_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                color: #1d1d1f;
                background: #ffffff;
            }
            QLineEdit:focus {
                border-color: #1976D2;
            }
        """)
        icon_layout.addWidget(self._icon_input)
        
        pick_btn = QPushButton("选择")
        pick_btn.setFixedSize(60, 32)
        pick_btn.clicked.connect(self._pick_icon)
        pick_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #555;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
        """)
        icon_layout.addWidget(pick_btn)
        
        self._icon_preview = QLabel()
        self._icon_preview.setFixedSize(32, 32)
        self._icon_preview.setAlignment(Qt.AlignCenter)
        self._icon_preview.setStyleSheet("background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;")
        icon_layout.addWidget(self._icon_preview)
        
        layout.addLayout(icon_layout)
        self._update_icon_preview()
        
        self._exec_input = self._add_field(layout, "命令", self._exec)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 32)
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1565C0;
            }
        """)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
    
    def _add_field(self, layout: QVBoxLayout, label: str, value: str) -> QLineEdit:
        row_layout = QHBoxLayout()
        
        label_widget = QLabel(label)
        label_widget.setFixedWidth(60)
        label_widget.setStyleSheet("color: #1d1d1f; font-size: 13px;")
        row_layout.addWidget(label_widget)
        
        input_widget = QLineEdit(value)
        input_widget.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                color: #1d1d1f;
                background: #ffffff;
            }
            QLineEdit:focus {
                border-color: #1976D2;
            }
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
        
        if icon_name.startswith("icons/"):
            from core.constants import DATA_DIR
            from pathlib import Path
            icon_path = DATA_DIR / icon_name
            if icon_path.exists():
                from PyQt5.QtGui import QPixmap
                pixmap = QPixmap(str(icon_path))
                if not pixmap.isNull():
                    self._icon_preview.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    return
        
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            self._icon_preview.setPixmap(icon.pixmap(28, 28))
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
