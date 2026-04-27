"""
插件列表项组件 - 支持拖拽
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QIcon, QDrag, QPixmap

from core.constants import ICONS_DIR, DATA_DIR


class PluginListItem(QFrame):
    """可拖拽的插件列表项"""

    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    drag_started = pyqtSignal()

    MIME_TYPE = "application/x-plugin-id"

    def __init__(
        self,
        plugin_id: str,
        name: str,
        icon_name: str,
        plugin_type: str = "command",
        parent=None,
    ):
        super().__init__(parent)
        self.plugin_id = plugin_id
        self._name = name
        self._icon_name = icon_name
        self._plugin_type = plugin_type
        self._drag_start_pos = None

        self.setFixedHeight(52)
        self.setObjectName("pluginListItem")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        drag_handle = QLabel("⋮⋮")
        drag_handle.setStyleSheet(
            "color: #aaa; font-size: 14px; background: transparent;"
        )
        drag_handle.setFixedWidth(20)
        layout.addWidget(drag_handle)

        icon_label = QLabel()
        icon = self._load_icon()
        from PyQt5.QtWidgets import QApplication

        app = QApplication.instance()
        dpr = app.devicePixelRatio() if app else 1.0
        pixmap = icon.pixmap(int(28 * dpr), int(28 * dpr))
        pixmap.setDevicePixelRatio(dpr)
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(28, 28)
        layout.addWidget(icon_label)

        name_label = QLabel(self._name)
        name_label.setStyleSheet(
            "color: #1d1d1f; font-size: 13px; background: transparent;"
        )
        layout.addWidget(name_label, 1)

        self._can_edit = self._plugin_type != "widget"
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(56, 30)
        if self._can_edit:
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.plugin_id))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    color: #374151;
                    font-size: 13px;
                    height: 30px;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    background: #f3f4f6;
                    border-color: #9ca3af;
                }
            """)
        else:
            edit_btn.setEnabled(False)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #f3f4f6;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    color: #9ca3af;
                    font-size: 13px;
                    height: 30px;
                    padding: 0 8px;
                }
            """)
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(56, 30)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.plugin_id))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                color: #b91c1c;
                font-size: 13px;
                height: 30px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #fee2e2;
                border-color: #f87171;
            }
        """)
        layout.addWidget(delete_btn)

        self.setStyleSheet("""
            #pluginListItem {
                background: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
            }
            #pluginListItem:hover {
                background: #fafafa;
                border-color: #d5d5d5;
            }
        """)

    def _load_icon(self) -> QIcon:
        if self._icon_name.startswith("icons/"):
            from plugins.plugin_manager import PluginManager

            icon = PluginManager.get().resolve_icon(self._icon_name, self.plugin_id)
            if icon:
                return icon

        icon = QIcon.fromTheme(self._icon_name)
        if not icon.isNull():
            return icon

        return QIcon.fromTheme("application-x-executable")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is None:
            return

        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self.MIME_TYPE, self.plugin_id.encode("utf-8"))
        drag.setMimeData(mime)

        pixmap = self.grab()
        transparent_pixmap = QPixmap(pixmap.size())
        transparent_pixmap.fill(Qt.transparent)
        from PyQt5.QtGui import QPainter

        painter = QPainter(transparent_pixmap)
        painter.setOpacity(0.4)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        drag.setPixmap(transparent_pixmap)
        drag.setHotSpot(self._drag_start_pos)

        self.drag_started.emit()
        drag.exec_(Qt.MoveAction)

        self._drag_start_pos = None

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)
