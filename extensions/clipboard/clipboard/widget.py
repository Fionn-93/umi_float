"""
剪切板历史插件 - 主界面
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMenu,
    QAction,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor

from utils.clipboard_watcher import ClipboardWatcher


class ClipboardWidget(QWidget):
    """剪切板历史主 widget"""

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._watcher = ClipboardWatcher.get()
        self._build_ui()
        self._load_history()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.timeout.connect(self._refresh_if_needed)
        self._refresh_timer.start()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget(self)
        header.setObjectName("ClipboardHeader")
        header.setStyleSheet("""
            #ClipboardHeader {
                background: #fafafa;
                border-bottom: 1px solid #e5e5e5;
                padding: 8px 12px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel("剪切板历史", self)
        self._title_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1d1d1f;"
        )
        header_layout.addWidget(self._title_label)

        self._clear_btn = QPushButton("清空", self)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #e5e5e5;
                border-radius: 4px;
                color: #666;
                font-size: 12px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background: #fee2e2;
                border-color: #fecaca;
                color: #b91c1c;
            }
        """)
        self._clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(self._clear_btn)

        layout.addWidget(header)

        self._list_widget = QListWidget(self)
        self._list_widget.setObjectName("ClipboardList")
        self._list_widget.setStyleSheet("""
            #ClipboardList {
                border: none;
                background: #ffffff;
            }
            #ClipboardList::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            #ClipboardList::item:hover {
                background: #f5f5f5;
            }
            #ClipboardList::item:selected {
                background: #e8e0ff;
            }
        """)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list_widget)

        self._placeholder = QLabel("暂无记录", self)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #aaa; font-size: 13px; padding: 40px;")
        self._placeholder.setVisible(False)
        layout.addWidget(self._placeholder)

        self.setStyleSheet("""
            ClipboardWidget {
                background: #ffffff;
            }
        """)

    def _load_history(self):
        rows = self._watcher.get_history(limit=100)

        self._list_widget.clear()
        for row_id, content, content_type, created_at in rows:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, row_id)
            item.setData(Qt.UserRole + 1, content)
            item.setData(Qt.UserRole + 2, content_type)

            display_text = content[:100] + "..." if len(content) > 100 else content
            display_text = display_text.replace("\n", " ")
            item.setText(display_text)
            self._list_widget.addItem(item)

        self._placeholder.setVisible(self._list_widget.count() == 0)

    def _refresh_if_needed(self):
        pass

    def _on_item_clicked(self, item: QListWidgetItem):
        content = item.data(Qt.UserRole + 1)
        if content:
            from PyQt5.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(content)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self._copy_selected)
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(copy_action)
        menu.addAction(delete_action)
        menu.exec_(QCursor.pos())

    def _copy_selected(self):
        current_item = self._list_widget.currentItem()
        if current_item:
            self._on_item_clicked(current_item)

    def _delete_selected(self):
        current_item = self._list_widget.currentItem()
        if not current_item:
            return
        row_id = current_item.data(Qt.UserRole)
        self._watcher.delete_item(row_id)
        self._load_history()

    def _clear_history(self):
        self._watcher.clear_history()
        self._load_history()

    def closeEvent(self, event):
        self._refresh_timer.stop()
