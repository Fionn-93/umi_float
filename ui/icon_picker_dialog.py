"""
图标选择器对话框
"""
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QGridLayout, QScrollArea, QFrame,
    QLineEdit, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

from core.constants import DATA_DIR
from utils.system_info import SystemInfo


PRESET_ICONS = [
    "applications-system", "applications-utilities", "preferences-system",
    "preferences-desktop", "system-settings", "system-software-install",
    "document-new", "document-open", "document-save", "document-print",
    "folder", "folder-open", "folder-new", "user-home", "computer",
    "drive-harddisk", "drive-optical", "drive-removable-media",
    "accessories-calculator", "accessories-text-editor", "utilities-terminal",
    "system-monitor", "system-search", "system-shutdown", "system-reboot",
    "audio-volume-high", "audio-volume-medium", "audio-volume-low", "audio-mute",
    "media-playback-start", "media-playback-pause", "media-playback-stop",
    "media-record", "media-eject", "media-optical", "media-floppy",
    "camera-photo", "camera-web", "video-display", "video-x-generic",
    "image-x-generic", "image", "folder-pictures", "folder-music",
    "folder-videos", "folder-documents", "folder-download",
    "network-wired", "network-wireless", "network-offline",
    "network-server", "network-workgroup", "network-transmit",
    "browser", "web-browser", "mail-unread", "mail-read",
    "internet-mail", "internet-news", "internet-web-browser",
    "weather-clear", "weather-clouds", "weather-rain", "weather-snow",
    "appointment", "appointment-new", "calendar", "office-calendar",
    "alarm", "clock", "stopwatch", "tasks",
    "battery", "battery-full", "battery-low", "battery-caution",
    "power", "power-profile-balanced", "power-profile-performance",
    "help-about", "help-contents", "help-faq",
    "dialog-information", "dialog-warning", "dialog-error", "dialog-question",
    "list-add", "list-remove", "view-refresh", "view-fullscreen",
    "window-close", "window-new", "window-duplicate",
    "user", "user-desktop", "user-trash", "user-trash-full",
    "emblem-important", "emblem-favorite", "emblem-system",
    "stock_lock", "stock_lock-open", "stock_save", "stock_open",
    "gnome-system-monitor", "gnome-terminal", "gnome-calculator",
    "nemo", "thunar", "pcmanfm", "nautilus",
    "deepin-calculator", "deepin-terminal", "deepin-editor",
    "dde-file-manager", "dde-calendar", "dde-dock",
]


def get_icon_picker_style(accent_color: str) -> str:
    """获取图标选择器样式表"""
    return f"""
/* Tab 扁平化 */
QTabWidget::pane {{
    border: none;
    background: #ffffff;
}}
QTabBar {{
    qproperty-drawBase: 0;
}}
QTabBar::tab {{
    background: transparent;
    color: #888888;
    padding: 8px 16px;
    font-size: 13px;
    border: none;
    outline: none;
}}
QTabBar::tab:selected {{
    color: {accent_color};
    font-weight: 600;
    border-bottom: 2px solid {accent_color};
    outline: none;
}}
QTabBar::tab:hover:!selected {{
    color: #333333;
}}
QTabBar::tab:focus {{
    outline: none;
    border: none;
}}

/* 搜索框 */
QLineEdit {{
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: #333333;
    background: #ffffff;
}}
QLineEdit:focus {{
    border-color: {accent_color};
}}

/* 图标按钮 */
#IconBtn {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
}}
#IconBtn:hover {{
    background: #f5f5f5;
    border-color: #e0e0e0;
}}
#IconBtn:checked {{
    background: {accent_color}22;
    border: 1px solid {accent_color};
}}
#IconBtn:focus {{
    outline: none;
}}

/* 预览容器 */
#PreviewContainer {{
    background: #fafafa;
    border-top: 1px solid #f0f0f0;
}}

/* 本地预览区 */
#LocalPreview {{
    background: #fafafa;
    border: 2px dashed #d0d0d0;
    border-radius: 8px;
}}
#LocalPreview:hover {{
    border-color: {accent_color};
}}
"""


class IconPickerDialog(QDialog):
    """图标选择器对话框"""

    def __init__(self, current_icon: str = "", parent=None):
        super().__init__(parent)
        self._selected_icon = current_icon
        self._selected_icon_path = None
        self._accent_color = SystemInfo.get_accent_color()

        self.setWindowTitle("选择图标")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(480, 400)
        self.resize(500, 450)
        self.setStyleSheet(get_icon_picker_style(self._accent_color))

        self._init_ui()

    def _is_icon_visible_on_light_bg(self, icon: QIcon) -> bool:
        """检测图标在浅色背景下是否可见"""
        pixmap = icon.pixmap(24, 24)
        if pixmap.isNull():
            return False

        image = pixmap.toImage()
        if image.isNull():
            return False

        total_brightness = 0
        pixel_count = 0

        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                alpha = pixel.alpha()
                if alpha < 128:
                    continue

                brightness = 0.299 * pixel.red() + 0.587 * pixel.green() + 0.114 * pixel.blue()
                total_brightness += brightness
                pixel_count += 1

        if pixel_count == 0:
            return False

        avg_brightness = total_brightness / pixel_count

        return avg_brightness < 200

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.tabBar().setFocusPolicy(Qt.NoFocus)
        tabs.addTab(self._create_preset_tab(), "预设图标")
        tabs.addTab(self._create_local_tab(), "本地文件")
        layout.addWidget(tabs)

        preview_container = QWidget()
        preview_container.setObjectName("PreviewContainer")
        current_layout = QHBoxLayout(preview_container)
        current_layout.setContentsMargins(16, 12, 16, 12)

        current_label = QLabel("当前:")
        current_label.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        current_layout.addWidget(current_label)

        self._icon_name_label = QLabel(self._selected_icon or "未选择")
        self._icon_name_label.setStyleSheet("color: #333333; font-size: 12px; background: transparent;")
        current_layout.addWidget(self._icon_name_label)
        current_layout.addStretch()

        self._preview_label = QLabel()
        self._preview_label.setFixedSize(48, 48)
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet("background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px;")
        current_layout.addWidget(self._preview_label)
        layout.addWidget(preview_container)

        self._update_preview()

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

    def _create_preset_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_label.setStyleSheet("color: #666666; font-size: 13px; background: transparent;")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入图标名称...")
        self._search_input.textChanged.connect(self._filter_icons)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        self._icon_grid = QGridLayout(grid_widget)
        self._icon_grid.setSpacing(8)
        self._icon_grid.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        self._populate_icons()

        return tab

    def _create_local_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        desc = QLabel("选择本地图片文件作为扩展图标")
        desc.setStyleSheet("color: #666666; font-size: 13px; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._local_preview = QLabel()
        self._local_preview.setObjectName("LocalPreview")
        self._local_preview.setFixedSize(96, 96)
        self._local_preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._local_preview, alignment=Qt.AlignCenter)

        self._local_path_label = QLabel("未选择文件")
        self._local_path_label.setStyleSheet("color: #888888; font-size: 11px; background: transparent;")
        self._local_path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._local_path_label)

        browse_btn = QPushButton("选择文件...")
        browse_btn.setFixedSize(120, 36)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_local_file)
        browse_btn.setStyleSheet(f"""
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
        layout.addWidget(browse_btn, alignment=Qt.AlignCenter)

        layout.addStretch()

        return tab

    def _populate_icons(self):
        row, col = 0, 0
        cols = 8

        self._icon_buttons = []

        for icon_name in PRESET_ICONS:
            icon = QIcon.fromTheme(icon_name)
            if icon.isNull():
                continue

            if not self._is_icon_visible_on_light_bg(icon):
                continue

            btn = QPushButton()
            btn.setObjectName("IconBtn")
            btn.setFixedSize(40, 40)
            btn.setIcon(icon)
            btn.setIconSize(QSize(24, 24))
            btn.setToolTip(icon_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=icon_name: self._select_preset_icon(name))

            self._icon_grid.addWidget(btn, row, col)
            self._icon_buttons.append((icon_name, btn))

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _filter_icons(self, text: str):
        text = text.lower()
        for icon_name, btn in self._icon_buttons:
            visible = text in icon_name.lower()
            btn.setVisible(visible)

    def _select_preset_icon(self, icon_name: str):
        self._selected_icon = icon_name
        self._selected_icon_path = None

        for name, btn in self._icon_buttons:
            btn.setChecked(name == icon_name)

        self._update_preview()

    def _browse_local_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图标文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.svg *.ico);;所有文件 (*)"
        )

        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._local_preview.setPixmap(scaled)
                self._local_path_label.setText(file_path)

                self._selected_icon = ""
                self._selected_icon_path = file_path
                self._update_preview()

    def _update_preview(self):
        if self._selected_icon:
            icon = QIcon.fromTheme(self._selected_icon)
            if not icon.isNull():
                self._preview_label.setPixmap(icon.pixmap(40, 40))
                self._icon_name_label.setText(self._selected_icon)
                return

        if self._selected_icon_path:
            pixmap = QPixmap(self._selected_icon_path)
            if not pixmap.isNull():
                self._preview_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._icon_name_label.setText("自定义图标")
                return

        self._preview_label.clear()
        self._icon_name_label.setText("未选择")

    def _on_ok(self):
        if self._selected_icon_path:
            from plugins.plugin_manager import PluginManager
            pm = PluginManager.get()
            saved_path = pm.save_custom_icon(self._selected_icon_path)
            if saved_path:
                self._selected_icon = saved_path
        self.accept()

    def get_selected_icon(self) -> str:
        return self._selected_icon
