"""
应用选择器对话框 - 从系统已安装应用中选择创建快捷方式
"""
from typing import Optional, List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QGridLayout, QWidget
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QColor, QPen, QFontMetrics

from utils.desktop_entry import get_desktop_entries, filter_entries, AppEntry
from utils.system_info import SystemInfo


class AppItemWidget(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, entry: AppEntry, accent_color: str, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._selected = False
        self._hovered = False

        r = int(accent_color[1:3], 16)
        g = int(accent_color[3:5], 16)
        b = int(accent_color[5:7], 16)
        self._accent_rgb = (r, g, b)

        self.setFixedSize(90, 88)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("AppItemWidget")
        self.setToolTip(entry.name)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._icon_label = QLabel()
        self._icon_label.setObjectName("appIconLabel")
        self._icon_label.setFixedSize(48, 48)
        self._icon_label.setAlignment(Qt.AlignCenter)

        self._name_label = QLabel()
        self._name_label.setObjectName("appNameLabel")
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setWordWrap(False)
        self._name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        font = self.font()
        font.setPixelSize(12)
        self._name_label.setFont(font)
        self._name_label.setFixedWidth(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self._icon_label, alignment=Qt.AlignCenter)
        layout.addWidget(self._name_label, alignment=Qt.AlignCenter)

        self._set_elided_name(entry.name)
        self._update_icon()

    def _set_elided_name(self, name: str):
        fm = QFontMetrics(self._name_label.font())
        elided = fm.elidedText(name, Qt.ElideRight, 80)
        self._name_label.setText(elided)

    def _update_icon(self):
        icon_name = self.entry.icon
        dpr = 1.0
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            dpr = app.devicePixelRatio()

        icon_size = 48

        if not icon_name:
            icon = QIcon.fromTheme("application-x-executable")
        elif icon_name.startswith("/"):
            icon = QIcon(icon_name)
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")
        else:
            icon = QIcon.fromTheme(icon_name)
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")

        pix = icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
        if not pix.isNull():
            pix.setDevicePixelRatio(dpr)
            self._icon_label.setPixmap(pix)
        else:
            self._icon_label.clear()

    def isSelected(self) -> bool:
        return self._selected

    def setSelected(self, selected: bool):
        self._selected = selected
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        r, g, b = self._accent_rgb

        if self._selected:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(r, g, b, 46))
            painter.setPen(QPen(QColor(r, g, b, 180), 1.5))
            painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)
        elif self._hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(r, g, b, 18))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)


def get_app_picker_style(accent_color: str) -> str:
    r = int(accent_color[1:3], 16)
    g = int(accent_color[3:5], 16)
    b = int(accent_color[5:7], 16)
    return f"""
    QDialog {{
        background: #ffffff;
    }}
    QLabel {{
        background: transparent;
        color: #333333;
    }}
    QLineEdit {{
        border: none;
        border-radius: 12px;
        background: #f4f6f8;
        color: #1f2937;
        padding: 0 12px;
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 2px solid {accent_color};
        background: #ffffff;
    }}
    QLineEdit::placeholder {{
        color: #9ca3af;
    }}
    QPushButton {{
        background: #ffffff;
        color: #333333;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: #f5f5f5;
        border-color: {accent_color};
    }}
    #NoResultLabel {{
        color: #888888;
        font-size: 13px;
        background: transparent;
    }}
    #appIconLabel {{
        background: transparent;
    }}
    #appNameLabel {{
        color: #333333;
        font-size: 12px;
        background: transparent;
    }}
    """


class AppPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_entry: Optional[AppEntry] = None
        self._accent_color = SystemInfo.get_accent_color()
        self._all_entries: List[AppEntry] = []
        self._current_keyword = ""
        self._app_widgets: List = []

        self.setWindowTitle("选择应用")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(540, 480)
        self.resize(560, 520)
        self.setStyleSheet(get_app_picker_style(self._accent_color))

        self._init_ui()
        self._load_apps()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_label.setStyleSheet("color: #666666; font-size: 13px; background: transparent;")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入应用名称...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(8, 8, 8, 8)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll, 1)

        self._no_result_label = QLabel("未找到应用")
        self._no_result_label.setObjectName("NoResultLabel")
        self._no_result_label.setAlignment(Qt.AlignCenter)
        self._no_result_label.setVisible(False)
        layout.addWidget(self._no_result_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
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

    def _load_apps(self):
        self._all_entries = get_desktop_entries()
        self._populate_grid(self._all_entries)

    def _populate_grid(self, entries: List[AppEntry]):
        for i in reversed(range(self._grid_layout.count())):
            item = self._grid_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        cols = 5
        row = 0
        col = 0

        self._app_widgets = []

        for entry in entries:
            widget = AppItemWidget(entry, self._accent_color)
            widget.clicked.connect(self._on_item_clicked)
            self._grid_layout.addWidget(widget, row, col)
            self._app_widgets.append((entry, widget))

            col += 1
            if col >= cols:
                col = 0
                row += 1

        self._no_result_label.setVisible(len(entries) == 0)
        self._grid_widget.setVisible(len(entries) > 0)

    def _on_item_clicked(self, widget: AppItemWidget):
        self._selected_entry = widget.entry
        for entry, w in self._app_widgets:
            w.setSelected(w is widget)

    def _on_search_changed(self, text: str):
        self._current_keyword = text.strip()
        entries = filter_entries(self._all_entries, self._current_keyword)
        self._populate_grid(entries)
        self._selected_entry = None

    def _on_ok(self):
        if not self._selected_entry:
            return
        self.accept()

    def get_selected_entry(self) -> Optional[AppEntry]:
        return self._selected_entry