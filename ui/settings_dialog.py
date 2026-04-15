"""
设置对话框 - macOS 系统偏好设置风格
"""
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSlider, QPushButton, QWidget, QColorDialog,
    QFrame, QScrollArea, QSizePolicy, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont

from core.config import get_config
from utils.theme_colors import theme_from_hex


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._drag_pos = None
        self._is_dragging = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("设置")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(640, 440)
        self.resize(660, 460)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFixedWidth(150)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        self.nav_list.setStyleSheet("""
            #navList {
                background-color: #f6f6f6;
                border: none;
                border-right: 1px solid #e0e0e0;
                outline: none;
                font-size: 13px;
                padding: 8px 0px;
            }
            #navList::item {
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                margin: 2px 8px;
                color: #555;
            }
            #navList::item:selected {
                background-color: #ffffff;
                color: #1d1d1f;
                font-weight: 500;
            }
            #navList::item:hover:!selected {
                background-color: #ebebeb;
            }
        """)

        # 右侧内容区
        self.stack = QStackedWidget()
        self.stack.setObjectName("settingsStack")

        self.personalize_page = PersonalizePage(self)
        self.extensions_page = ExtensionsPage(self)

        nav_items = [
            "⚙  个性化",
            "🧩  扩展",
        ]
        for name in nav_items:
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(0, 36))
            self.nav_list.addItem(item)

        self.stack.addWidget(self.personalize_page)
        self.stack.addWidget(self.extensions_page)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.nav_list)
        body.addWidget(self.stack, 1)

        main_layout.addLayout(body)

    def _switch_page(self, row):
        self.stack.setCurrentIndex(row)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._is_dragging = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        super().mouseReleaseEvent(event)


class _GroupWidget(QWidget):
    """macOS 风格分组容器 - 白色圆角卡片"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("groupWidget")
        self.setStyleSheet("""
            #groupWidget {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #888; font-size: 11px; padding: 10px 16px 2px 16px; background: transparent;")
            self._layout.addWidget(title_label)

        self._row_container = QVBoxLayout()
        self._row_container.setContentsMargins(16, 8, 16, 8)
        self._row_container.setSpacing(0)
        self._layout.addLayout(self._row_container)

    def add_row(self, widget):
        if self._row_container.count() > 0:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setFixedHeight(1)
            sep.setStyleSheet("background-color: #f0f0f0; border: none;")
            self._row_container.addWidget(sep)
        self._row_container.addWidget(widget)


class PersonalizePage(QWidget):
    def __init__(self, parent_dialog):
        super().__init__()
        self.dialog = parent_dialog
        self.config = get_config()
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #f6f6f6; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #f6f6f6;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("个性化")
        title.setFont(QFont("", 16, QFont.Bold))
        title.setStyleSheet("color: #1d1d1f; background: transparent;")
        layout.addWidget(title)

        cfg = self.config.get()

        # 外观组
        group1 = _GroupWidget("外观")
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["时钟", "内存", "天气"])
        self.display_mode_combo.setCurrentText({"clock": "时钟", "memory": "内存", "weather": "天气"}.get(cfg.get('display_mode', 'clock'), "时钟"))
        self.display_mode_combo.currentIndexChanged.connect(self._on_display_mode_changed)
        self.display_mode_combo.setObjectName("displayModeCombo")
        self.display_mode_combo.setStyleSheet("""
            #displayModeCombo {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ffffff;
                color: #1d1d1f;
                font-size: 13px;
                min-width: 100px;
            }
            #displayModeComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        group1.add_row(_SettingRow("显示模式", self.display_mode_combo))
        self.color_btn = _ColorButton(cfg.get('theme_color', '#6495ED'))
        self.color_btn.color_changed.connect(self._on_theme_color_changed)
        group1.add_row(_SettingRow("主题色", self.color_btn))
        layout.addWidget(group1)

        # 悬浮球组
        group2 = _GroupWidget("悬浮球")
        self.size_slider = _LabeledSlider("大小", 32, 128, cfg.get('float_ball_size', 56), suffix=" px")
        self.size_slider.value_changed.connect(self._on_size_changed)
        group2.add_row(_SettingRow("悬浮球大小", self.size_slider))

        self.opacity_slider = _LabeledSlider("透明度", 10, 100, int(cfg.get('opacity', 0.9) * 100), suffix="%", scale=0.01)
        self.opacity_slider.value_changed.connect(self._on_opacity_changed)
        group2.add_row(_SettingRow("透明度", self.opacity_slider))
        layout.addWidget(group2)

        # 扩展面板组
        group3 = _GroupWidget("扩展面板")
        self.pie_btn_slider = _LabeledSlider("图标大小", 32, 100, cfg.get('pie_button_size', 56), suffix=" px")
        self.pie_btn_slider.value_changed.connect(self._on_pie_btn_size_changed)
        group3.add_row(_SettingRow("扩展图标大小", self.pie_btn_slider))

        self.spacing_slider = _LabeledSlider("间距", 0, 30, cfg.get('pie_spacing', 10), suffix=" px")
        self.spacing_slider.value_changed.connect(self._on_spacing_changed)
        group3.add_row(_SettingRow("面板间距", self.spacing_slider))
        layout.addWidget(group3)

        layout.addStretch()

        scroll.setWidget(content)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    def _on_theme_color_changed(self, hex_color):
        self.config.update(theme_color=hex_color)
        self.dialog.settings_changed.emit('float_ball')

    def _on_display_mode_changed(self, index):
        mode_map = {0: 'clock', 1: 'memory', 2: 'weather'}
        mode = mode_map.get(index, 'clock')
        self.config.update(display_mode=mode)
        self.dialog.settings_changed.emit('float_ball')

    def _on_size_changed(self, value):
        self.config.update(float_ball_size=value)
        self.dialog.settings_changed.emit('float_ball')

    def _on_opacity_changed(self, value):
        self.config.update(opacity=round(value * 0.01, 2))
        self.dialog.settings_changed.emit('float_ball')

    def _on_pie_btn_size_changed(self, value):
        self.config.update(pie_button_size=value)
        self.dialog.settings_changed.emit('pie_panel')

    def _on_spacing_changed(self, value):
        self.config.update(pie_spacing=value)
        self.dialog.settings_changed.emit('pie_panel')


class ExtensionsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("扩展管理")
        title.setFont(QFont("", 16, QFont.Bold))
        title.setStyleSheet("color: #1d1d1f; background: transparent;")
        layout.addWidget(title)

        group = _GroupWidget()
        placeholder = QLabel("扩展管理功能待实现")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 13px; padding: 40px 16px; background: transparent;")
        group._row_container.addWidget(placeholder)
        layout.addWidget(group)
        layout.addStretch()

        self.setStyleSheet("background-color: #f6f6f6;")


class _ColorButton(QWidget):
    color_changed = pyqtSignal(str)

    def __init__(self, hex_color: str, parent=None):
        super().__init__(parent)
        self._color = hex_color
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._swatch = QPushButton()
        self._swatch.setFixedSize(26, 26)
        self._swatch.setCursor(Qt.PointingHandCursor)
        self._swatch.clicked.connect(self._pick_color)
        self._update_swatch_style()

        self._hex_label = QLabel(hex_color)
        self._hex_label.setStyleSheet("color: #888; font-size: 12px; font-family: monospace; background: transparent;")

        layout.addWidget(self._swatch)
        layout.addWidget(self._hex_label)
        layout.addStretch()

    def _update_swatch_style(self):
        self._swatch.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #d0d0d0;
                border-radius: 6px;
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
            self._update_swatch_style()
            self._hex_label.setText(self._color)
            self.color_changed.emit(self._color)


class _LabeledSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, label, min_val, max_val, default, suffix="", scale=1.0, parent=None):
        super().__init__(parent)
        self._scale = scale
        self._suffix = suffix

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.blockSignals(True)
        self.slider.setValue(default)
        self.slider.blockSignals(False)
        self.slider.setObjectName("macSlider")
        self.slider.setStyleSheet("""
            #macSlider::groove:horizontal {
                height: 4px;
                background: #d0d0d0;
                border-radius: 2px;
            }
            #macSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 7px;
            }
            #macSlider::handle:horizontal:hover {
                border-color: #999;
            }
            #macSlider::sub-page:horizontal {
                background: #1976D2;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.slider, 1)

        if scale == 1.0:
            display_text = f"{default}{suffix}"
        else:
            display_text = f"{default * scale:.2f}{suffix}"
        self.value_label = QLabel(display_text)
        self.value_label.setFixedWidth(56)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("color: #1d1d1f; font-size: 12px; font-family: monospace; background: transparent;")
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val):
        if self._scale == 1.0:
            self.value_label.setText(f"{val}{self._suffix}")
        else:
            self.value_label.setText(f"{val * self._scale:.2f}{self._suffix}")
        self.value_changed.emit(val)


class _SettingRow(QWidget):
    """macOS 风格设置行：左侧标签 + 右侧控件"""

    def __init__(self, label_text, control_widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        label = QLabel(label_text)
        label.setFixedWidth(120)
        label.setStyleSheet("color: #1d1d1f; font-size: 13px; background: transparent;")
        layout.addWidget(label)
        layout.addWidget(control_widget, 1)