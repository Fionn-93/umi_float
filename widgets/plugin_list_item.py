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
    
    def __init__(self, plugin_id: str, name: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.plugin_id = plugin_id
        self._name = name
        self._icon_name = icon_name
        self._drag_start_pos = None
        
        self.setFixedHeight(48)
        self.setObjectName("pluginListItem")
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        drag_handle = QLabel("⋮⋮")
        drag_handle.setStyleSheet("color: #aaa; font-size: 14px; background: transparent;")
        drag_handle.setFixedWidth(20)
        layout.addWidget(drag_handle)
        
        icon_label = QLabel()
        icon = self._load_icon()
        icon_label.setPixmap(icon.pixmap(28, 28))
        icon_label.setFixedSize(28, 28)
        layout.addWidget(icon_label)
        
        name_label = QLabel(self._name)
        name_label.setStyleSheet("color: #1d1d1f; font-size: 13px; background: transparent;")
        layout.addWidget(name_label, 1)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(48, 28)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.plugin_id))
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #555;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e8e8e8;
                border-color: #ccc;
            }
        """)
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(48, 28)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.plugin_id))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #fff5f5;
                border: 1px solid #ffcdd2;
                border-radius: 4px;
                color: #c62828;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #ffebee;
                border-color: #ef9a9a;
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
            icon_path = DATA_DIR / self._icon_name
            if icon_path.exists():
                return QIcon(str(icon_path))
        
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
        mime.setData(self.MIME_TYPE, self.plugin_id.encode('utf-8'))
        drag.setMimeData(mime)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self._drag_start_pos)
        
        self.drag_started.emit()
        drag.exec_(Qt.MoveAction)
        
        self._drag_start_pos = None
    
    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)
