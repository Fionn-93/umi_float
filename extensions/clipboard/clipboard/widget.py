"""
剪切板历史插件 - 卡片式交互增强版
"""

import logging
from pathlib import Path
import subprocess

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QApplication,
    QFrame,
    QAbstractItemView,
)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QPoint,
    QSize,
    QDateTime,
    QMimeData,
    QUrl,
    QRectF,
    QByteArray,
    QEvent,
)
from PyQt5.QtGui import QColor, QPixmap, QPainter, QPainterPath

from utils.clipboard_watcher import ClipboardWatcher
from core.constants import DATA_DIR

logger = logging.getLogger(__name__)


class ClipboardItemWidget(QFrame):
    """自定义卡片条目组件"""

    copy_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(int)
    clicked = pyqtSignal(str, str)

    TYPE_NAMES = {"text": "文本", "image": "图片", "file": "文件", "url": "链接"}

    def __init__(
        self, row_id, content, content_type, timestamp, accent_color, ar, ag, ab
    ):
        super().__init__()
        self.row_id = row_id
        self.content = content
        self.content_type = content_type
        self._accent = accent_color
        self._ar = ar
        self._ag = ag
        self._ab = ab
        self._timestamp = timestamp

        self.setObjectName("ItemCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()

        label_text = self.TYPE_NAMES.get(content_type, "文本")
        type_label = QLabel(label_text)
        type_label.setStyleSheet(
            f"background: rgba({ar}, {ag}, {ab}, 0.13); "
            f"color: {accent_color}; "
            f"font-size: 10px; "
            f"font-weight: bold; "
            f"padding: 2px 6px; "
            f"border-radius: 4px;"
        )

        time_str = self._format_time(timestamp)
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        header_layout.addWidget(type_label)
        header_layout.addWidget(time_label)
        header_layout.addStretch()

        self.action_group = QWidget()
        self.action_group.setFixedWidth(70)
        action_lay = QHBoxLayout(self.action_group)
        action_lay.setContentsMargins(0, 0, 0, 0)
        action_lay.setSpacing(8)

        self.btn_copy = QPushButton("复制")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setFixedSize(28, 28)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        action_lay.addWidget(self.btn_copy)

        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("DeleteBtn")
        self.btn_delete.setFixedSize(28, 28)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        action_lay.addWidget(self.btn_delete)

        header_layout.addWidget(self.action_group)

        layout.addLayout(header_layout)

        if content_type == "image":
            self._build_image_content(layout)
        elif content_type == "file":
            self._build_file_content(layout)
        else:
            self._build_text_content(layout)

        self.btn_copy.clicked.connect(
            lambda: self.copy_requested.emit(self.content, self.content_type)
        )
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.row_id))

    def _build_text_content(self, layout):
        self.setFixedHeight(90)
        display_text = self._prepare_display_text(self.content)
        self.content_label = QLabel(display_text)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #1f2937; font-size: 13px;")
        self.content_label.setMaximumHeight(48)
        layout.addWidget(self.content_label)

    def _build_image_content(self, layout):
        self.setFixedHeight(140)
        img_path = DATA_DIR / "clipboard_images" / self.content
        pixmap = QPixmap(str(img_path)) if img_path.exists() else QPixmap()

        thumb_label = QLabel()
        thumb_label.setFixedSize(240, 90)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet("background: transparent;")

        if not pixmap.isNull():
            scaled = pixmap.scaled(
                240, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            img_w = scaled.width()
            img_h = scaled.height()
            x = max(0, (240 - img_w) // 2)
            y = max(0, (90 - img_h) // 2)
            cropped = scaled.copy(x, y, min(img_w, 240), min(img_h, 90))
            rounded = self._apply_rounded_corners(cropped, 8)
            thumb_label.setPixmap(rounded)
        else:
            thumb_label.setText("图片已失效")
            thumb_label.setStyleSheet(
                "background: #f3f4f6; border-radius: 8px; "
                "color: #9ca3af; font-size: 12px;"
            )

        layout.addWidget(thumb_label)

        if not pixmap.isNull():
            info_label = QLabel(f"{pixmap.width()} × {pixmap.height()}")
            info_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            layout.addWidget(info_label)

    def _apply_rounded_corners(self, pixmap: QPixmap, radius: int) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rounded.rect()), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return rounded

    def _build_file_content(self, layout):
        self.setFixedHeight(90)
        files = self.content.strip().split("\n")
        file_name = Path(files[0]).name if files else "未知文件"

        if len(files) > 1:
            display_name = f"{file_name} 等 {len(files)} 个文件"
        else:
            display_name = file_name

        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #1f2937; font-size: 13px; font-weight: 500;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)

        path_label = QLabel(self.content.strip().split("\n")[0])
        path_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path_label)

    def _prepare_display_text(self, content: str) -> str:
        lines = content.strip().split("\n")
        if len(lines) > 2:
            return lines[0] + "\n" + lines[1] + " ..."
        text = " ".join(lines)
        if len(text) > 100:
            return text[:100] + " ..."
        return text

    def _format_time(self, timestamp):
        dt = QDateTime.fromSecsSinceEpoch(int(timestamp))
        return dt.toString("HH:mm:ss")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.content, self.content_type)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.btn_copy.setStyleSheet(
            "background: #ffffff; border: 1px solid #d1d5db; "
            "border-radius: 6px; color: #374151; font-size: 11px;"
        )
        self.btn_delete.setStyleSheet(
            "background: #fef2f2; border: 1px solid #fecaca; "
            "border-radius: 6px; color: #b91c1c; font-size: 11px;"
        )
        self.setStyleSheet(
            f"#ItemCard {{ background: rgba({self._ar}, {self._ag}, {self._ab}, 0.03); "
            f"border: 1px solid rgba({self._ar}, {self._ag}, {self._ab}, 0.2); "
            f"border-radius: 10px; }}"
        )

    def leaveEvent(self, event):
        self.btn_copy.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        self.btn_delete.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        self.setStyleSheet(
            "#ItemCard { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; }"
        )


class ClipboardWidget(QWidget):
    """剪切板历史主窗口"""

    closed = pyqtSignal()

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._watcher = ClipboardWatcher.get()
        self._accent_color = host_info.get("accent_color", "#7B61FF")
        self._last_history_hash = None
        self._drag_pos = QPoint()
        self._current_filter = "all"
        self._just_shown = False

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 560)

        self._build_ui()
        self._apply_theme_style()
        self._load_history()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self._refresh_if_needed)
        self._refresh_timer.start()

    def _rgb_from_hex(self, hex_color: str):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return r, g, b

    def _apply_theme_style(self):
        accent = self._accent_color
        ar, ag, ab = self._rgb_from_hex(accent)

        self.setStyleSheet(f"""
            #MainContainer {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
            }}
            #TitleBar {{
                border-bottom: 1px solid rgba(229, 231, 235, 0.5);
            }}
            #WindowTitle {{
                font-size: 14px;
                font-weight: bold;
                color: #1f2937;
            }}
            #CloseBtn {{
                background: transparent;
                color: #86868b;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }}
            #CloseBtn:hover {{
                background: rgba({ar}, {ag}, {ab}, 0.1);
                color: #1d1d1f;
            }}
            #FilterTabBtn {{
                background: #f4f6f8;
                color: #6b7280;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }}
            #FilterTabBtn:hover {{
                background: #ebedf0;
                color: #374151;
            }}
            #FilterTabBtn[active="true"] {{
                background: {accent};
                color: #ffffff;
            }}
            #FilterTabBtn[active="true"]:hover {{
                background: rgba({ar}, {ag}, {ab}, 0.85);
            }}
            #ClearBtn {{
                background: transparent;
                border: none;
                color: {accent};
                font-size: 12px;
                font-weight: 500;
                border-radius: 6px;
                padding: 4px 8px;
            }}
            #ClearBtn:hover {{
                background: rgba({ar}, {ag}, {ab}, 0.1);
                color: #1d1d1f;
            }}
            #FilterBar {{
                border-bottom: 1px solid rgba(229, 231, 235, 0.5);
            }}
            #ClipboardListWidget {{
                border: none;
                background: transparent;
            }}
            #ClipboardListWidget::item {{
                background: transparent;
                padding: 3px 6px;
            }}
            #ItemCard {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }}
            #StatusLabel {{
                color: #6b7280;
                font-size: 11px;
            }}
        """)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        self._container = QFrame()
        self._container.setObjectName("MainContainer")
        container_lay = QVBoxLayout(self._container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        self._title_bar = QWidget()
        self._title_bar.setObjectName("TitleBar")
        self._title_bar.setFixedHeight(54)
        title_lay = QHBoxLayout(self._title_bar)
        title_lay.setContentsMargins(20, 0, 10, 0)

        self._title_label = QLabel("剪切板历史")
        self._title_label.setObjectName("WindowTitle")
        title_lay.addWidget(self._title_label)
        title_lay.addStretch()

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("CloseBtn")
        self._close_btn.setFixedSize(32, 32)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self.closed.emit)
        title_lay.addWidget(self._close_btn)

        container_lay.addWidget(self._title_bar)

        self._filter_bar = QWidget()
        self._filter_bar.setObjectName("FilterBar")
        self._filter_bar.setFixedHeight(36)
        self._filter_bar.setAttribute(Qt.WA_StyledBackground, True)
        filter_lay = QHBoxLayout(self._filter_bar)
        filter_lay.setContentsMargins(20, 0, 16, 0)

        self._filter_btns = []
        self._filter_group = QWidget()
        filter_btn_lay = QHBoxLayout(self._filter_group)
        filter_btn_lay.setContentsMargins(0, 0, 0, 0)
        filter_btn_lay.setSpacing(4)

        for label, key in [("全部", "all"), ("文本", "text"), ("图片", "image"), ("文件", "file")]:
            btn = QPushButton(label)
            btn.setObjectName("FilterTabBtn")
            btn.setFixedSize(56, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setProperty("active", key == "all")
            btn.clicked.connect(lambda checked, k=key: self._on_tab_clicked(k))
            filter_btn_lay.addWidget(btn)
            self._filter_btns.append((btn, key))

        filter_lay.addWidget(self._filter_group)
        filter_lay.addStretch()

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setObjectName("ClearBtn")
        self._clear_btn.setFixedSize(40, 28)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        filter_lay.addWidget(self._clear_btn)

        container_lay.addWidget(self._filter_bar)

        self._list_widget = QListWidget()
        self._list_widget.setObjectName("ClipboardListWidget")
        self._list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self._list_widget.setFocusPolicy(Qt.NoFocus)
        container_lay.addWidget(self._list_widget)

        self._footer = QFrame()
        self._footer.setFixedHeight(35)
        footer_lay = QHBoxLayout(self._footer)
        self._status_label = QLabel("悬停查看操作")
        self._status_label.setObjectName("StatusLabel")
        self._status_label.setStyleSheet("margin-left: 15px;")
        footer_lay.addWidget(self._status_label)
        container_lay.addWidget(self._footer)

        self.main_layout.addWidget(self._container)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 50))
        self._container.setGraphicsEffect(shadow)

    def _load_history(self):
        rows = self._watcher.get_history(limit=40, content_type=self._current_filter)
        current_hash = hash(tuple((r[0], r[1]) for r in rows))
        if current_hash == self._last_history_hash:
            return

        self._last_history_hash = current_hash
        self._list_widget.clear()

        ar, ag, ab = self._rgb_from_hex(self._accent_color)

        for row_id, content, content_type, timestamp in rows:
            item = QListWidgetItem(self._list_widget)

            if content_type == "image":
                item.setSizeHint(QSize(0, 148))
            else:
                item.setSizeHint(QSize(0, 98))

            card = ClipboardItemWidget(
                row_id,
                content,
                content_type,
                timestamp,
                self._accent_color,
                ar,
                ag,
                ab,
            )
            card.copy_requested.connect(self._handle_copy)
            card.delete_requested.connect(self._handle_delete)
            card.clicked.connect(lambda c, t: self._handle_copy(c, t))

            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, card)

    def _handle_copy(self, content, content_type):
        clipboard = QApplication.clipboard()
        if content_type == "image":
            img_path = DATA_DIR / "clipboard_images" / content
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                clipboard.setPixmap(pixmap)
            else:
                return
        elif content_type == "file":
            mime = QMimeData()
            urls = [QUrl.fromLocalFile(p) for p in content.strip().split("\n")]
            mime.setUrls(urls)
            gnome_data = "copy\n" + "\n".join(u.toString() for u in urls)
            mime.setData(
                "x-special/gnome-copied-files", QByteArray(gnome_data.encode())
            )
            clipboard.setMimeData(mime)
        else:
            clipboard.setText(content)

        try:
            subprocess.Popen(["notify-send", "-a", "umi-float", "已复制到剪切板"])
        except Exception:
            pass
        logger.info("_handle_copy: 复制完成，发出 closed 信号")
        self.closed.emit()

    def _handle_delete(self, row_id):
        self._watcher.delete_item(row_id)
        self._load_history()

    def _on_clear_clicked(self):
        logger.info("_on_clear_clicked: 清空剪切板历史")
        self._watcher.clear_history()
        self._load_history()

    def _on_tab_clicked(self, key):
        self._current_filter = key
        for btn, k in self._filter_btns:
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._last_history_hash = None
        self._load_history()

    def _refresh_if_needed(self):
        if self.isVisible():
            self._load_history()

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            visible = self.isVisible()
            active = self.isActiveWindow()
            will_close = visible and not active
            logger.debug(
                "changeEvent: ActivationChange visible=%s active=%s just_shown=%s → closed.emit=%s",
                visible, active, self._just_shown, will_close,
            )
            if will_close and not self._just_shown:
                self.closed.emit()
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._just_shown = True
        QTimer.singleShot(100, self.activateWindow)
        QTimer.singleShot(300, self._clear_just_shown)

    def _clear_just_shown(self):
        self._just_shown = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        super().closeEvent(event)
