"""
设置对话框
"""
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSlider, QPushButton, QWidget, QColorDialog,
    QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from core.config import get_config
from utils.theme_colors import theme_from_hex


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 420)
        self.resize(640, 440)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(120)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)

        self.stack = QStackedWidget()

        self.personalize_page = PersonalizePage(self)
        self.extensions_page = ExtensionsPage(self)

        nav_items = [
            ("个性化", self.personalize_page),
            ("扩展", self.extensions_page),
        ]
        for name, page in nav_items:
            item = QListWidgetItem(name)
            self.nav_list.addItem(item)
            self.stack.addWidget(page)

        layout.addWidget(self.nav_list)
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        layout.addWidget(self.stack, 1)

        self.setStyleSheet(self._dialog_style())

    def _switch_page(self, row):
        self.stack.setCurrentIndex(row)

    def _dialog_style(self):
        return """
            QDialog {
                background-color: #f5f5f5;
            }
            QListWidget {
                background-color: #e8e8e8;
                border: none;
                outline: none;
                font-size: 13px;
                padding: 8px 0px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border: none;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #ffffff;
                color: #1976D2;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #dcdcdc;
            }
        """


class PersonalizePage(QWidget):
    def __init__(self, parent_dialog):
        super().__init__()
        self.dialog = parent_dialog
        self.config = get_config()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("个性化")
        title.setFont(QFont("", 15, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        config = self.config.get()

        # 主题色
        self.color_btn = _ColorButton(config.get('theme_color', '#6495ED'))
        self.color_btn.color_changed.connect(self._on_theme_color_changed)
        row = _make_row("主题色", self.color_btn)
        layout.addWidget(row)

        # 悬浮球大小
        self.size_slider = _LabeledSlider(
            "悬浮球大小", 32, 128,
            config.get('float_ball_size', 56),
            suffix=" px",
        )
        self.size_slider.value_changed.connect(self._on_size_changed)
        layout.addWidget(self.size_slider)

        # 透明度
        self.opacity_slider = _LabeledSlider(
            "透明度", 10, 100,
            int(config.get('opacity', 0.9) * 100),
            suffix="%",
            scale=0.01,
        )
        self.opacity_slider.value_changed.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

        # 面板按钮大小
        self.pie_btn_slider = _LabeledSlider(
            "面板按钮大小", 32, 128,
            config.get('pie_button_size', 56),
            suffix=" px",
        )
        self.pie_btn_slider.value_changed.connect(self._on_pie_btn_size_changed)
        layout.addWidget(self.pie_btn_slider)

        # 面板间距
        self.spacing_slider = _LabeledSlider(
            "面板间距", 0, 30,
            config.get('pie_spacing', 10),
            suffix=" px",
        )
        self.spacing_slider.value_changed.connect(self._on_spacing_changed)
        layout.addWidget(self.spacing_slider)

        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)

    def _on_theme_color_changed(self, hex_color):
        self.config.update(theme_color=hex_color)
        self.dialog.settings_changed.emit()

    def _on_size_changed(self, value):
        self.config.update(float_ball_size=value)
        self.dialog.settings_changed.emit()

    def _on_opacity_changed(self, value):
        self.config.update(opacity=round(value * 0.01, 2))
        self.dialog.settings_changed.emit()

    def _on_pie_btn_size_changed(self, value):
        self.config.update(pie_button_size=value)
        self.dialog.settings_changed.emit()

    def _on_spacing_changed(self, value):
        self.config.update(pie_spacing=value)
        self.dialog.settings_changed.emit()


class ExtensionsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("扩展管理")
        title.setFont(QFont("", 15, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        placeholder = QLabel("扩展管理功能待实现")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
        layout.addWidget(placeholder, 1)

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)


class _ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, hex_color: str, parent=None):
        super().__init__(parent)
        self._color = hex_color
        self.setFixedSize(48, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick_color)
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #ccc;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #999;
            }}
        """)

    def _pick_color(self):
        current = QColor(self._color)
        color = QColorDialog.getColor(current, self, "选择主题色")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)


class _LabeledSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, label, min_val, max_val, default, suffix="", scale=1.0, parent=None):
        super().__init__(parent)
        self._scale = scale
        self._suffix = suffix
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(label)
        name_label.setFixedWidth(120)
        name_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(name_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.blockSignals(True)
        self.slider.setValue(default)
        self.slider.blockSignals(False)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #ddd;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -5px 0;
                background: #1976D2;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #1976D2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.slider, 1)

        if scale == 1.0:
            display_text = f"{default}{suffix}"
        else:
            display_text = f"{default * scale:.2f}{suffix}"
        self.value_label = QLabel(display_text)
        self.value_label.setFixedWidth(64)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val):
        if self._scale == 1.0:
            self.value_label.setText(f"{val}{self._suffix}")
        else:
            self.value_label.setText(f"{val * self._scale:.2f}{self._suffix}")
        self.value_changed.emit(val)


def _make_row(label_text, widget):
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    name_label = QLabel(label_text)
    name_label.setFixedWidth(120)
    name_label.setStyleSheet("font-size: 13px; color: #333;")
    layout.addWidget(name_label)
    layout.addWidget(widget)
    layout.addStretch()
    return row