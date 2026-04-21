"""
设置对话框 - 参考 FeelUOwn 风格
"""
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSlider, QPushButton, QWidget,
    QFrame, QScrollArea, QComboBox, QMessageBox, QListView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont

from core.config import get_config
from utils.theme_colors import get_all_themes, DEFAULT_THEME
from plugins.plugin_manager import PluginManager
from widgets.plugin_list_widget import PluginListWidget, DropForwardScrollArea
from ui.plugin_edit_dialog import PluginEditDialog


class MidHeader(QLabel):
    """分组标题 - 参考 FeelUOwn"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        font = self.font()
        font.setPixelSize(16)
        font.setWeight(QFont.Bold)
        self.setFont(font)
        self.setStyleSheet("color: #1d1d1f; padding: 16px 0 8px 0; background: transparent;")


class _SettingRow(QWidget):
    """设置行：左侧标签 + 右侧控件"""

    def __init__(self, label_text, control_widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        label = QLabel(label_text)
        label.setStyleSheet("color: #1d1d1f; font-size: 13px; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(control_widget)


class _LabeledSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, min_val, max_val, default, suffix="", scale=1.0, parent=None):
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


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(str)
    page_changed = pyqtSignal(int)

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
        self.page_changed.emit(row)

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
        scroll.setStyleSheet("QScrollArea { background-color: #ffffff; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        cfg = self.config.get()

        layout.addWidget(MidHeader("外观"))

        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["时钟", "性能", "天气"])
        self.display_mode_combo.setCurrentText(
            {"clock": "时钟", "performance": "性能", "weather": "天气"}.get(
                cfg.get('display_mode', 'clock'), "时钟"
            )
        )
        self.display_mode_combo.currentIndexChanged.connect(self._on_display_mode_changed)
        display_view = QListView()
        display_view.setStyleSheet("color: #1d1d1f; background-color: #ffffff;")
        self.display_mode_combo.setView(display_view)
        self.display_mode_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ffffff;
                color: #1d1d1f;
                font-size: 13px;
                min-width: 100px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                selection-background-color: #e3f2fd;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                color: #1d1d1f;
                background-color: #ffffff;
                height: 28px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e3f2fd;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(_SettingRow("显示模式", self.display_mode_combo))

        self.theme_combo = QComboBox()
        themes = get_all_themes()
        theme_names = [name for _, name in themes]
        self.theme_combo.addItems(theme_names)
        current_theme = cfg.get('theme', DEFAULT_THEME)
        for i, (key, name) in enumerate(themes):
            if key == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_view = QListView()
        theme_view.setStyleSheet("color: #1d1d1f; background-color: #ffffff;")
        self.theme_combo.setView(theme_view)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ffffff;
                color: #1d1d1f;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                selection-background-color: #e3f2fd;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                color: #1d1d1f;
                background-color: #ffffff;
                height: 28px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e3f2fd;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(_SettingRow("主题", self.theme_combo))

        layout.addWidget(MidHeader("悬浮球"))

        self.size_slider = _LabeledSlider(32, 128, cfg.get('float_ball_size', 56), suffix=" px")
        self.size_slider.value_changed.connect(self._on_size_changed)
        layout.addWidget(_SettingRow("大小", self.size_slider))

        self.opacity_slider = _LabeledSlider(10, 100, int(cfg.get('opacity', 0.9) * 100), suffix="%", scale=0.01)
        self.opacity_slider.value_changed.connect(self._on_opacity_changed)
        layout.addWidget(_SettingRow("透明度", self.opacity_slider))

        layout.addWidget(MidHeader("扩展面板"))

        self.pie_btn_slider = _LabeledSlider(32, 100, cfg.get('pie_button_size', 56), suffix=" px")
        self.pie_btn_slider.value_changed.connect(self._on_pie_btn_size_changed)
        layout.addWidget(_SettingRow("图标大小", self.pie_btn_slider))

        self.spacing_slider = _LabeledSlider(0, 30, cfg.get('pie_spacing', 10), suffix=" px")
        self.spacing_slider.value_changed.connect(self._on_spacing_changed)
        layout.addWidget(_SettingRow("间距", self.spacing_slider))

        layout.addStretch()

        scroll.setWidget(content)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    def _on_theme_changed(self, index):
        themes = get_all_themes()
        if 0 <= index < len(themes):
            theme_key = themes[index][0]
            self.config.update(theme=theme_key)
            self.dialog.settings_changed.emit('float_ball')

    def _on_display_mode_changed(self, index):
        mode_map = {0: 'clock', 1: 'performance', 2: 'weather'}
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
        self.dialog = parent
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background-color: #ffffff;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 12)
        header_layout.setSpacing(12)

        title = QLabel("扩展管理")
        title.setFont(QFont("", 16, QFont.Bold))
        title.setStyleSheet("color: #1d1d1f; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        new_btn = QPushButton("+ 新建")
        new_btn.setFixedSize(80, 32)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_plugin)
        new_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #1565C0;
            }
        """)
        header_layout.addWidget(new_btn)

        layout.addWidget(header)

        scroll = DropForwardScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #ffffff; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.plugin_list = PluginListWidget()
        self.plugin_list.order_changed.connect(self._on_order_changed)
        self.plugin_list.edit_requested.connect(self._on_edit_plugin)
        self.plugin_list.delete_requested.connect(self._on_delete_plugin)

        scroll.setWidget(self.plugin_list)
        layout.addWidget(scroll)

        self.setStyleSheet("background-color: #ffffff;")

        self._refresh_list()

    def _refresh_list(self):
        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()
        self.plugin_list.set_plugins(enabled, disabled)

    def _on_order_changed(self):
        self._refresh_list()
        self.dialog.settings_changed.emit('pie_panel')

    def _on_new_plugin(self):
        dialog = PluginEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            pm = PluginManager.get()
            pm.create_plugin(
                name=data['name'],
                description=data['description'],
                icon=data['icon'],
                exec_cmd=data['exec']
            )
            self._refresh_list()
            self.dialog.settings_changed.emit('pie_panel')

    def _on_edit_plugin(self, plugin_id: str):
        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()

        plugin_config = None
        for pid, config in enabled + disabled:
            if pid == plugin_id:
                plugin_config = config
                break

        if plugin_config is None:
            return

        dialog = PluginEditDialog(
            plugin_id=plugin_id,
            name=plugin_config.name,
            description=plugin_config.description,
            icon=plugin_config.icon,
            exec_cmd=plugin_config.exec,
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            pm.update_plugin_override(plugin_id, {
                'name': data['name'],
                'description': data['description'],
                'icon': data['icon'],
                'exec': data['exec'],
            })
            self._refresh_list()
            self.dialog.settings_changed.emit('pie_panel')

    def _on_delete_plugin(self, plugin_id: str):
        pm = PluginManager.get()

        plugin_config = None
        enabled, disabled = pm.get_ordered_plugins()
        for pid, config in enabled + disabled:
            if pid == plugin_id:
                plugin_config = config
                break

        if plugin_config is None:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除扩展 \"{plugin_config.name}\" 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            pm.delete_plugin(plugin_id)
            self._refresh_list()
            self.dialog.settings_changed.emit('pie_panel')
