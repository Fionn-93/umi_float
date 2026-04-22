"""
设置对话框 - 现代圆角卡片风格
"""
import threading
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSlider, QPushButton, QWidget,
    QFrame, QScrollArea, QComboBox, QListView, QLineEdit,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation
from PyQt5.QtGui import QFont, QPalette, QColor

from core.config import get_config
from utils.theme_colors import get_all_themes, DEFAULT_THEME
from utils.system_info import SystemInfo
from utils.weather_info import fetch_weather, clear_weather_cache, lookup_city_by_coords
from utils.ip_location import get_ip_location
from plugins.plugin_manager import PluginManager
from widgets.plugin_list_widget import PluginListWidget, DropForwardScrollArea
from widgets.location_selector import LocationSelector, lookup_city_id_by_name
from ui.plugin_edit_dialog import PluginEditDialog
from ui.app_picker_dialog import AppPickerDialog
from ui.confirm_dialog import ConfirmDialog


class TitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        title = QLabel("设置中心")
        title.setObjectName("titleBarLabel")
        lay.addWidget(title)
        lay.addStretch()
        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(parent.close)
        lay.addWidget(close_btn)


class NavList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class SettingRow(QFrame):
    def __init__(self, title, widget, desc=""):
        super().__init__()
        self.setObjectName("row")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)

        left_container = QFrame()
        left_container.setFixedWidth(240)
        left_lay = QVBoxLayout(left_container)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("rowTitle")
        left_lay.addWidget(t)
        if desc:
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setObjectName("rowDesc")
            left_lay.addWidget(d)

        lay.addWidget(left_container, 0)
        lay.addSpacing(16)
        widget.setMinimumWidth(200)
        lay.addWidget(widget, 1)

    def enterEvent(self, event):
        self.setStyleSheet("#row{background:rgba(0,0,0,0.03);}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        super().leaveEvent(event)


class Card(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(16, 16, 16, 16)
        self.v.setSpacing(2)
        lab = QLabel(title.upper())
        lab.setObjectName("sectionTitle")
        self.v.addWidget(lab)

    def addRow(self, row):
        self.v.addWidget(row)


class LabeledSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, min_val, max_val, default, suffix="", scale=1.0, parent=None):
        super().__init__(parent)
        self._scale = scale
        self._suffix = suffix

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.setRange(min_val, max_val)
        self.slider.blockSignals(True)
        self.slider.setValue(default)
        self.slider.blockSignals(False)
        layout.addWidget(self.slider, 1)

        if scale == 1.0:
            display_text = f"{default}{suffix}"
        else:
            display_text = f"{default * scale:.2f}{suffix}"
        self.value_label = QLabel(display_text)
        self.value_label.setFixedWidth(48)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("color: #6b7280; font-size: 12px; background: transparent;")
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val):
        if self._scale == 1.0:
            self.value_label.setText(f"{val}{self._suffix}")
        else:
            self.value_label.setText(f"{val * self._scale:.2f}{self._suffix}")
        self.value_changed.emit(val)


class Page(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        header = QLabel(title)
        header.setObjectName("pageTitle")
        title_row.addWidget(header)
        title_row.addStretch()

        self.title_actions = QHBoxLayout()
        self.title_actions.setSpacing(8)
        title_row.addLayout(self.title_actions)

        root.addLayout(title_row)
        self.body = QVBoxLayout()
        self.body.setSpacing(18)
        root.addLayout(self.body)
        root.addStretch()


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(str)
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._drag_pos = None
        self._is_dragging = False
        self._accent_color = SystemInfo.get_accent_color()
        self._animation = None
        self.setWindowTitle("设置")
        self.resize(860, 620)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._init_ui()
        self.applyStyle()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.bar = TitleBar(self)
        shell_layout.addWidget(self.bar)

        content = QHBoxLayout()
        content.setContentsMargins(12, 12, 12, 12)
        content.setSpacing(12)

        self.nav_list = NavList()
        nav_items = ["个性化", "天气", "扩展"]
        for name in nav_items:
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(0, 44))
            self.nav_list.addItem(item)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)

        self.stack = QStackedWidget()

        self.personalize_page = PersonalizePage(self)
        self.weather_page = WeatherPage(self)
        self.extensions_page = ExtensionsPage(self)

        self.stack.addWidget(self.personalize_page)
        self.stack.addWidget(self.weather_page)
        self.stack.addWidget(self.extensions_page)

        content.addWidget(self.nav_list)
        content.addWidget(self.stack, 1)
        shell_layout.addLayout(content)
        outer.addWidget(self.shell)

    def _switch_page(self, row):
        if row < 0 or row >= self.stack.count():
            return
        self.stack.setCurrentIndex(row)
        self.page_changed.emit(row)
        widget = self.stack.currentWidget()
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        self._animation = anim

    def applyStyle(self):
        accent = self._accent_color
        r = int(accent[1:3], 16)
        g = int(accent[3:5], 16)
        b = int(accent[5:7], 16)
        self.setStyleSheet(f"""
        #shell {{
            background: #f5f6f8;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
        }}
        #titleBarLabel {{
            font-size: 16px;
            font-weight: 700;
            color: #111;
        }}
        QPushButton#closeBtn {{
            color: #374151;
            font-size: 18px;
            font-weight: bold;
            background: transparent;
            border: none;
            border-radius: 8px;
            width: 30px;
            height: 30px;
        }}
        QPushButton#closeBtn:hover {{
            background-color: #e5e7eb;
            color: #111827;
        }}
        QPushButton#closeBtn:pressed {{
            background-color: #d1d5db;
        }}
        QListWidget {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 12px;
            font-size: 14px;
            outline: none;
        }}
        QListWidget::item {{
            height: 44px;
            border-radius: 12px;
            padding-left: 14px;
            color: #1f2937;
        }}
        QListWidget::item:selected {{
            background: {accent};
            color: white;
            font-weight: 600;
        }}
        QListWidget::item:hover:!selected {{
            background: rgba(0, 0, 0, 0.04);
        }}
        #card {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
        }}
        #pageTitle {{
            font-size: 22px;
            font-weight: 700;
            color: #1f2937;
            padding-bottom: 8px;
        }}
        #sectionTitle {{
            font-size: 11px;
            font-weight: 700;
            color: #6b7280;
            letter-spacing: 1px;
            padding: 2px 4px 10px 4px;
        }}
        #row {{
            border-radius: 14px;
        }}
        #row:hover {{
            background: rgba(0, 0, 0, 0.03);
        }}
        #rowTitle {{
            font-size: 14px;
            font-weight: 600;
            color: #1f2937;
        }}
        #rowDesc {{
            font-size: 12px;
            color: #6b7280;
        }}
        QLineEdit {{
            min-width: 240px;
            height: 38px;
            border: none;
            border-radius: 12px;
            background: #f4f6f8;
            color: #1f2937;
            padding: 0 12px;
        }}
        QLineEdit::placeholder {{
            color: #9ca3af;
        }}
        QComboBox {{
            height: 38px;
            border: none;
            border-radius: 12px;
            background: #f4f6f8;
            color: #1f2937;
            padding: 0 12px;
            selection-background-color: transparent;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            selection-background-color: rgba({r}, {g}, {b}, 0.13);
            outline: none;
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            color: #1f2937;
            height: 32px;
            padding-left: 10px;
            border-radius: 8px;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: rgba({r}, {g}, {b}, 0.13);
            color: {accent};
        }}
        QSlider::groove:horizontal {{
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {accent};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
            background: white;
            border: 2px solid {accent};
        }}
        QPushButton#actionBtn {{
            height: 38px;
            padding: 0 18px;
            border: none;
            border-radius: 12px;
            background-color: {accent};
            color: white;
            font-weight: 600;
        }}
        QPushButton#actionBtn:hover {{
            background-color: rgba({r}, {g}, {b}, 0.8);
        }}
        QPushButton#actionBtn:pressed {{
            background-color: rgba({r}, {g}, {b}, 0.6);
        }}
        QPushButton {{
            height: 38px;
            padding: 0 18px;
            border: none;
            border-radius: 12px;
            background: {accent};
            color: white;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: rgba({r}, {g}, {b}, 0.8);
        }}
        QPushButton:pressed {{
            background: rgba({r}, {g}, {b}, 0.6);
        }}
        QPushButton:disabled {{
            background: #cccccc;
            color: #ffffff;
        }}
        QScrollBar:vertical {{
            width: 10px;
            background: transparent;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.14);
            border-radius: 5px;
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        """)

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


def _make_combo(items, current_index=0):
    combo = QComboBox()
    combo.addItems(items)
    combo.setCurrentIndex(current_index)
    combo.setMinimumWidth(180)
    view = QListView()
    view.setStyleSheet("border: none; background: white;")
    combo.setView(view)
    return combo


class PersonalizePage(Page):
    def __init__(self, parent_dialog):
        super().__init__("个性化")
        self.dialog = parent_dialog
        self.config = get_config()
        self._build_ui()

    def _build_ui(self):
        cfg = self.config.get()

        c1 = Card("Appearance")
        themes = get_all_themes()
        theme_names = [name for _, name in themes]
        self.theme_combo = _make_combo(theme_names)
        current_theme = cfg.get("theme", DEFAULT_THEME)
        for i, (key, _) in enumerate(themes):
            if key == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        c1.addRow(SettingRow("主题", self.theme_combo, "选择悬浮球配色方案"))
        self.body.addWidget(c1)

        c2 = Card("Float Ball")
        self.display_mode_combo = _make_combo(
            ["时钟", "性能", "天气"],
            {"clock": 0, "performance": 1, "weather": 2}.get(cfg.get("display_mode", "clock"), 0),
        )
        self.display_mode_combo.currentIndexChanged.connect(self._on_display_mode_changed)
        c2.addRow(SettingRow("显示模式", self.display_mode_combo, "悬浮球显示的内容类型"))

        self.size_slider = LabeledSlider(32, 128, cfg.get("float_ball_size", 56), suffix=" px")
        self.size_slider.value_changed.connect(self._on_size_changed)
        c2.addRow(SettingRow("大小", self.size_slider, "调整悬浮球尺寸"))
        self.body.addWidget(c2)

        c3 = Card("Pie Panel")
        self.expand_mode_combo = _make_combo(
            ["鼠标点击", "鼠标悬浮"],
            0 if cfg.get("pie_expand_mode", "click") == "click" else 1,
        )
        self.expand_mode_combo.currentIndexChanged.connect(self._on_expand_mode_changed)
        c3.addRow(SettingRow("展开方式", self.expand_mode_combo, "选择展开面板的触发方式"))

        self.pie_btn_slider = LabeledSlider(32, 100, cfg.get("pie_button_size", 56), suffix=" px")
        self.pie_btn_slider.value_changed.connect(self._on_pie_btn_size_changed)
        c3.addRow(SettingRow("图标大小", self.pie_btn_slider, "面板中按钮图标的大小"))

        self.spacing_slider = LabeledSlider(0, 30, cfg.get("pie_spacing", 10), suffix=" px")
        self.spacing_slider.value_changed.connect(self._on_spacing_changed)
        c3.addRow(SettingRow("间距", self.spacing_slider, "面板按钮之间的间距"))
        self.body.addWidget(c3)

    def _on_theme_changed(self, index):
        themes = get_all_themes()
        if 0 <= index < len(themes):
            self.config.update(theme=themes[index][0])
            self.dialog.settings_changed.emit("float_ball")

    def _on_display_mode_changed(self, index):
        mode_map = {0: "clock", 1: "performance", 2: "weather"}
        self.config.update(display_mode=mode_map.get(index, "clock"))
        self.dialog.settings_changed.emit("float_ball")

    def _on_size_changed(self, value):
        self.config.update(float_ball_size=value)
        self.dialog.settings_changed.emit("float_ball")

    def _on_pie_btn_size_changed(self, value):
        self.config.update(pie_button_size=value)
        self.dialog.settings_changed.emit("pie_panel")

    def _on_spacing_changed(self, value):
        self.config.update(pie_spacing=value)
        self.dialog.settings_changed.emit("pie_panel")

    def _on_expand_mode_changed(self, index):
        self.config.update(pie_expand_mode="click" if index == 0 else "hover")
        self.dialog.settings_changed.emit("pie_panel")


class WeatherPage(Page):
    test_finished = pyqtSignal(bool, str)
    locate_finished = pyqtSignal(bool, str)

    def __init__(self, parent_dialog):
        super().__init__("天气")
        self.dialog = parent_dialog
        self.config = get_config()
        self.test_finished.connect(self._on_test_finished)
        self.locate_finished.connect(self._on_locate_finished)
        self._build_ui()

    def _build_ui(self):
        from widgets.toast import ToastWidget
        cfg = self.config.get()

        self.toast = ToastWidget.get_instance(self)

        c1 = Card("Weather Service")
        self.api_host_input = QLineEdit()
        self.api_host_input.setPlaceholderText("输入和风天气 API 地址")
        self.api_host_input.setText(cfg.get("weather_api_host", ""))
        self.api_host_input.editingFinished.connect(self._on_api_host_changed)
        c1.addRow(SettingRow("API 地址", self.api_host_input, "和风天气服务的 API 端点地址"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入和风天气 API Key")
        self.api_key_input.setText(cfg.get("weather_api_key", ""))
        self.api_key_input.editingFinished.connect(self._on_api_key_changed)
        c1.addRow(SettingRow("API Key", self.api_key_input, "和风天气服务的访问密钥"))
        self.body.addWidget(c1)

        c2 = Card("Location")
        self.location_selector = LocationSelector(
            current_id=cfg.get("weather_location", "101010100")
        )
        self.location_selector.location_changed.connect(self._on_location_changed)

        location_row = QWidget()
        location_row_layout = QHBoxLayout(location_row)
        location_row_layout.setContentsMargins(0, 0, 0, 0)
        location_row_layout.setSpacing(8)
        location_row_layout.addWidget(self.location_selector)

        self.locate_btn = QPushButton("自动定位")
        self.locate_btn.setObjectName("locateBtn")
        self.locate_btn.setCursor(Qt.PointingHandCursor)
        self.locate_btn.clicked.connect(self._on_locate_clicked)
        location_row_layout.addWidget(self.locate_btn)
        location_row_layout.addStretch(1)

        c2.addRow(SettingRow("地区", location_row, "选择天气数据对应的地理位置"))

        self.test_btn = QPushButton("测试连接")
        self.test_btn.setObjectName("actionBtn")
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.clicked.connect(self._on_test_clicked)
        c2.addRow(SettingRow("连接状态", self.test_btn, "验证 API 配置是否正确"))
        self.body.addWidget(c2)

    def _on_api_host_changed(self):
        self.config.update(weather_api_host=self.api_host_input.text())
        clear_weather_cache()
        self.dialog.settings_changed.emit("float_ball")

    def _on_api_key_changed(self):
        self.config.update(weather_api_key=self.api_key_input.text())
        clear_weather_cache()
        self.dialog.settings_changed.emit("float_ball")

    def _on_location_changed(self, location_id):
        self.config.update(weather_location=location_id)
        clear_weather_cache()
        self.dialog.settings_changed.emit("float_ball")

    def _on_test_clicked(self):
        api_host = self.api_host_input.text().strip()
        api_key = self.api_key_input.text().strip()
        location = self.location_selector.current_location_id()
        if not api_host or not api_key or not location:
            self.toast.show_toast("请填写完整配置", success=False)
            return
        self.test_btn.setEnabled(False)

        def do_test():
            result = fetch_weather(api_key, location, api_host)
            if result is not None:
                msg = f"连接成功：{result.get('text', '')}, {result.get('temp', '--')}°C"
                self.test_finished.emit(True, msg)
            else:
                self.test_finished.emit(False, "连接失败，请检查配置")

        thread = threading.Thread(target=do_test, daemon=True)
        thread.start()

    def _on_test_finished(self, success, message):
        self.test_btn.setEnabled(True)
        if success:
            self.toast.show_toast(message, success=True)
        else:
            self.toast.show_toast(message, success=False)
        self.config.update(
            weather_api_host=self.api_host_input.text(),
            weather_api_key=self.api_key_input.text(),
            weather_location=self.location_selector.current_location_id(),
        )
        clear_weather_cache()
        self.dialog.settings_changed.emit("float_ball")

    def _on_locate_clicked(self):
        import logging
        logger = logging.getLogger(__name__)
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.toast.show_toast("请先填写 API Key", success=False)
            return
        self.locate_btn.setEnabled(False)

        def do_locate():
            logger.info("开始自动定位...")
            ip_info = get_ip_location()
            if ip_info is None:
                logger.warning("自动定位失败: 无法获取IP位置")
                self.locate_finished.emit(False, "无法获取IP位置")
                return
            location_id = lookup_city_by_coords(
                api_key,
                ip_info["lat"],
                ip_info["lon"],
                self.api_host_input.text().strip() or None,
            )
            if location_id is None:
                logger.warning("自动定位: QWeather API 未找到，尝试本地匹配...")
                location_id = lookup_city_id_by_name(
                    ip_info.get("city", ""), ip_info.get("region", "")
                )
            if location_id is None:
                logger.warning("自动定位失败: 未找到 %s 对应的城市", ip_info.get("city"))
                self.locate_finished.emit(False, f"未找到 {ip_info['city']} 对应的城市")
                return
            logger.info("自动定位成功: location_id=%s", location_id)
            self.locate_finished.emit(True, location_id)

        thread = threading.Thread(target=do_locate, daemon=True)
        thread.start()

    def _on_locate_finished(self, success, result):
        self.locate_btn.setEnabled(True)
        if success:
            location_id = result
            self.location_selector.set_location_by_id(location_id)
            self.config.update(weather_location=location_id)
            clear_weather_cache()
            self.dialog.settings_changed.emit("float_ball")
            self.toast.show_toast("定位成功", success=True)
        else:
            self.toast.show_toast(result, success=False)


class ExtensionsPage(Page):
    def __init__(self, parent):
        super().__init__("扩展")
        self.dialog = parent
        self._build_ui()

    def _build_ui(self):
        c = Card("Extensions")

        new_btn = QPushButton("+ 新建扩展")
        new_btn.setObjectName("actionBtn")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setMinimumWidth(100)
        new_btn.clicked.connect(self._on_new_plugin)
        self.title_actions.addWidget(new_btn)

        shortcut_btn = QPushButton("+ 新建快捷方式")
        shortcut_btn.setObjectName("actionBtn")
        shortcut_btn.setCursor(Qt.PointingHandCursor)
        shortcut_btn.setMinimumWidth(120)
        shortcut_btn.clicked.connect(self._on_new_shortcut)
        self.title_actions.addWidget(shortcut_btn)

        scroll = DropForwardScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.plugin_list = PluginListWidget()
        self.plugin_list.order_changed.connect(self._on_order_changed)
        self.plugin_list.edit_requested.connect(self._on_edit_plugin)
        self.plugin_list.delete_requested.connect(self._on_delete_plugin)

        scroll.setWidget(self.plugin_list)
        c.v.addWidget(scroll)
        self.body.addWidget(c)
        self._refresh_list()

    def _refresh_list(self):
        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()
        self.plugin_list.set_plugins(enabled, disabled)

    def _on_order_changed(self):
        self._refresh_list()
        self.dialog.settings_changed.emit("pie_panel")

    def _on_new_plugin(self):
        dialog = PluginEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            pm = PluginManager.get()
            pm.create_plugin(
                name=data["name"],
                description=data["description"],
                icon=data["icon"],
                exec_cmd=data["exec"],
            )
            self._refresh_list()
            self.dialog.settings_changed.emit("pie_panel")

    def _on_new_shortcut(self):
        dialog = AppPickerDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            entry = dialog.get_selected_entry()
            if entry:
                pm = PluginManager.get()
                pm.create_plugin(
                    name=entry.name,
                    description=entry.comment,
                    icon=entry.icon,
                    exec_cmd=entry.exec,
                )
                self._refresh_list()
                self.dialog.settings_changed.emit("pie_panel")

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
            parent=self,
        )
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            pm.update_plugin_override(plugin_id, {
                "name": data["name"],
                "description": data["description"],
                "icon": data["icon"],
                "exec": data["exec"],
            })
            self._refresh_list()
            self.dialog.settings_changed.emit("pie_panel")

    def _on_delete_plugin(self, plugin_id: str):
        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()
        plugin_config = None
        for pid, config in enabled + disabled:
            if pid == plugin_id:
                plugin_config = config
                break
        if plugin_config is None:
            return
        dialog = ConfirmDialog(
            "确认删除",
            f'确定要删除扩展 "{plugin_config.name}" 吗？\n此操作不可撤销。',
            self,
        )
        if dialog.exec_() == QDialog.Accepted:
            pm.delete_plugin(plugin_id)
            self._refresh_list()
            self.dialog.settings_changed.emit("pie_panel")