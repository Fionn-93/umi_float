"""
Widget 插件独立面板
"""

from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QColor

from core.config import get_config
from utils.theme_colors import theme_from_key, DEFAULT_THEME


class PluginPanel(QWidget):
    """Widget 插件独立面板"""

    closed = pyqtSignal()
    request_show_float = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugin_id = None
        self._plugin_widget = None
        self._host_info = {}
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(320, 400)
        self.resize(360, 480)

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)

        self._header = _PanelHeader(self)
        self._header.close_requested.connect(self.hide_panel)
        self._layout.addWidget(self._header)

        self._content = QWidget(self)
        self._content.setObjectName("PluginPanelContent")
        self._content.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self._layout.addWidget(self._content)

    def set_plugin(self, plugin_id: str, widget_class, host_info: dict):
        self._plugin_id = plugin_id
        self._host_info = host_info
        self._header.set_title(host_info.get("name", ""))
        if self._plugin_widget:
            self._plugin_widget.deleteLater()
            self._plugin_widget = None
        if widget_class:
            try:
                self._plugin_widget = widget_class(host_info)
                if self._plugin_widget:
                    self._content.layout().addWidget(self._plugin_widget)
            except Exception as e:
                print(f"创建插件 widget 失败: {e}")

    def show_panel(self, anchor_widget):
        if not anchor_widget:
            return
        anchor_pos = anchor_widget.mapToGlobal(QPoint(0, 0))
        anchor_size = anchor_widget.size()
        screen = anchor_widget.screen()
        screen_rect = screen.availableGeometry()

        x = anchor_pos.x() + anchor_size.width() + 16
        y = anchor_pos.y()
        if x + self.width() > screen_rect.right():
            x = anchor_pos.x() - self.width() - 16
        if y + self.height() > screen_rect.bottom():
            y = screen_rect.bottom() - self.height()
        if x < screen_rect.left():
            x = screen_rect.left()
        if y < screen_rect.top():
            y = screen_rect.top()

        self.move(x, y)
        self.show()
        self.raise_()

    def hide_panel(self):
        if self._plugin_widget:
            self._plugin_widget.deleteLater()
            self._plugin_widget = None
        while self._content.layout().count():
            item = self._content.layout().takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._plugin_id = None
        self.hide()
        self.closed.emit()

    def closeEvent(self, event):
        self.hide_panel()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pass
        super().mousePressEvent(event)


class _PanelHeader(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = ""
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._title_label = QLabel(self)
        self._title_label.setObjectName("PanelTitle")
        self._close_btn = QPushButton("×", self)
        self._close_btn.setObjectName("PanelCloseBtn")
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self._title_label, 1)
        layout.addWidget(self._close_btn, 0)

    def _apply_style(self):
        config = get_config()
        theme_key = config.get().get("theme", DEFAULT_THEME)
        colors = theme_from_key(theme_key)
        accent = colors["float_border"]
        self.setStyleSheet(f"""
            #PanelTitle {{
                color: #1d1d1f;
                font-size: 14px;
                font-weight: bold;
            }}
            #PanelCloseBtn {{
                background: transparent;
                color: #86868b;
                border: none;
                border-radius: 14px;
                font-size: 20px;
                font-weight: 300;
            }}
            #PanelCloseBtn:hover {{
                background: rgba({accent.red()}, {accent.green()}, {accent.blue()}, 40);
                color: #1d1d1f;
            }}
        """)

    def set_title(self, title: str):
        self._title = title
        self._title_label.setText(title)
