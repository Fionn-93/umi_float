"""
取色器插件 - 主 Widget
"""

import json
import logging
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QGraphicsDropShadowEffect,
    QApplication,
    QLayout,
)
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRect,
    QSize,
    QTimer,
    pyqtSignal,
    QEvent,
)
from PyQt5.QtGui import (
    QColor,
    QPixmap,
    QPainter,
    QPen,
    QFont,
    QCursor,
    QImage,
)
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRect,
    QRectF,
    QSize,
    QTimer,
    pyqtSignal,
    QEvent,
)
from PyQt5.QtGui import (
    QColor,
    QPixmap,
    QPainter,
    QPainterPath,
    QPen,
    QFont,
    QCursor,
    QImage,
    QBrush,
    QPalette,
)

logger = logging.getLogger(__name__)

MAX_HISTORY = 50


class ColorHistory:
    """颜色历史持久化"""

    def __init__(self, data_dir: Path):
        self._path = data_dir / "color_history.json"
        self._items = self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("ColorHistory _save failed: %s", e)

    def add(self, hex_color: str):
        hex_color = hex_color.upper()
        self._items = [h for h in self._items if h["hex"] != hex_color]
        self._items.insert(0, {"hex": hex_color})
        if len(self._items) > MAX_HISTORY:
            self._items = self._items[:MAX_HISTORY]
        self._save()

    def clear(self):
        self._items = []
        self._save()

    @property
    def items(self):
        return list(self._items)


def rgb_to_hsl(r, g, b):
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r_f, g_f, b_f)
    min_c = min(r_f, g_f, b_f)
    l = (max_c + min_c) / 2.0
    if max_c == min_c:
        h, s = 0.0, 0.0
    else:
        d = max_c - min_c
        s = d / (1.0 - abs(2 * l - 1.0))
        if max_c == r_f:
            h = ((g_f - b_f) / d) % 6
        elif max_c == g_f:
            h = (b_f - r_f) / d + 2
        else:
            h = (r_f - g_f) / d + 4
        h /= 6.0
    return round(h * 360), round(s * 100), round(l * 100)


def rgb_to_cmyk(r, g, b):
    if r == 0 and g == 0 and b == 0:
        return 0, 0, 0, 100
    k = 1 - max(r, g, b) / 255.0
    c = (1 - r / 255.0 - k) / (1 - k) if k < 1 else 0
    m = (1 - g / 255.0 - k) / (1 - k) if k < 1 else 0
    y = (1 - b / 255.0 - k) / (1 - k) if k < 1 else 0
    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)


class _PickerOverlay(QWidget):
    """全屏拾取覆盖层"""

    finished = pyqtSignal(object)

    def __init__(self, screenshot: QPixmap, accent_color: str):
        super().__init__()
        self._screenshot = screenshot
        self._mouse_pos = QPoint()
        self._picked_color = None
        self._accent_color = accent_color
        ar, ag, ab = _rgb_from_hex(accent_color)
        self._ar, self._ag, self._ab = ar, ag, ab

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self._mouse_pos.isNull():
            self._draw_magnifier(painter, self._mouse_pos)

    def _draw_magnifier(self, painter: QPainter, pos: QPoint):
        mx, my = pos.x(), pos.y()

        img = self._screenshot.toImage()
        w, img_h = img.width(), img.height()

        sample_side = 17
        half_s = sample_side // 2
        scale = 9
        disp_side = sample_side * scale

        region_x = max(0, mx - half_s)
        region_y = max(0, my - half_s)
        region_w = min(sample_side, w - region_x)
        region_h = min(sample_side, img_h - region_y)

        lx = mx + 20
        ly = my + 20
        gap = 20

        if lx + disp_side > w:
            lx = mx - disp_side - gap
        if ly + disp_side > img_h:
            ly = my - disp_side - gap

        cx = lx + disp_side // 2
        cy = ly + disp_side // 2

        src_rect = QRectF(
            float(region_x), float(region_y), float(region_w), float(region_h)
        )
        dst_rect = QRectF(float(lx), float(ly), float(disp_side), float(disp_side))
        painter.drawImage(dst_rect, img, src_rect)

        painter.setPen(QPen(Qt.white, 4))
        painter.drawRoundedRect(lx, ly, disp_side, disp_side, 8, 8)
        painter.setPen(QPen(QColor(50, 50, 50), 2.5))
        painter.drawRoundedRect(lx, ly, disp_side, disp_side, 8, 8)

        cross_half = 12
        cross_gap = 3

        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(cx - cross_half, cy, cx - cross_gap, cy)
        painter.drawLine(cx + cross_gap, cy, cx + cross_half, cy)
        painter.drawLine(cx, cy - cross_half, cx, cy - cross_gap)
        painter.drawLine(cx, cy + cross_gap, cx, cy + cross_half)

        painter.setPen(QPen(Qt.white, 2.5))
        painter.drawLine(cx - cross_half, cy, cx - cross_gap, cy)
        painter.drawLine(cx + cross_gap, cy, cx + cross_half, cy)
        painter.drawLine(cx, cy - cross_half, cx, cy - cross_gap)
        painter.drawLine(cx, cy + cross_gap, cx, cy + cross_half)

    def showEvent(self, event):
        super().showEvent(event)
        global_pos = QCursor.pos()
        self._mouse_pos = self.mapFromGlobal(global_pos)
        self.activateWindow()
        self.setFocus()
        self.update()

    def mouseMoveEvent(self, event):
        self._mouse_pos = event.pos()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            mx, my = event.pos().x(), event.pos().y()
            img = self._screenshot.toImage()
            if 0 <= mx < img.width() and 0 <= my < img.height():
                self._picked_color = img.pixelColor(mx, my).name().upper()
            else:
                self._picked_color = None
            self.finished.emit(self._picked_color)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._picked_color = None
            self.finished.emit(None)
            self.close()

    def get_picked_color(self):
        return self._picked_color


def _rgb_from_hex(hex_color: str):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r, g, b


class FormatRow(QWidget):
    """颜色格式行：标签 + 值 + 复制按钮"""

    copy_requested = pyqtSignal(str)

    def __init__(
        self,
        label_text: str,
        value_text: str,
        accent_color: str,
        ar: int,
        ag: int,
        ab: int,
    ):
        super().__init__()
        self._value = value_text
        self._accent = accent_color
        self._ar, self._ag, self._ab = ar, ag, ab

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label_text)
        lbl.setFixedWidth(50)
        lbl.setStyleSheet("color: #6b7280; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl)

        val = QLabel(value_text)
        val.setStyleSheet("color: #1f2937; font-size: 13px;")
        layout.addWidget(val)

        layout.addStretch()

        btn = QPushButton("复制")
        btn.setObjectName("CopyFmtBtn")
        btn.setFixedSize(52, 26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"background: #ffffff; border: 1px solid #d1d5db; "
            f"border-radius: 6px; color: #374151; font-size: 11px;"
        )
        btn.enterEvent = lambda e: btn.setStyleSheet(
            f"background: rgba({self._ar}, {self._ag}, {self._ab}, 0.08); "
            f"border: 1px solid rgba({self._ar}, {self._ag}, {self._ab}, 0.4); "
            f"border-radius: 6px; color: {self._accent}; font-size: 11px;"
        )
        btn.leaveEvent = lambda e: btn.setStyleSheet(
            "background: #ffffff; border: 1px solid #d1d5db; "
            "border-radius: 6px; color: #374151; font-size: 11px;"
        )
        btn.clicked.connect(lambda: self.copy_requested.emit(self._value))
        layout.addWidget(btn)

    def set_value(self, text: str):
        self._value = text
        for i in range(self.layout().count()):
            w = self.layout().itemAt(i).widget()
            if isinstance(w, QLabel) and i == 1:
                w.setText(text)
                break


class ColorSwatchWidget(QWidget):
    """大方块颜色展示"""

    def __init__(self, color: QColor, accent_color: str):
        super().__init__()
        self._color = color
        self._accent = accent_color
        self.setFixedHeight(120)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"border-radius: 12px; background: {color.name()}; border: 1px solid #e5e7eb;"
        )


class HistoryFlowLayout(QLayout):
    """流式布局：历史颜色色块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._row_height = 36
        self._spacing = 8

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def _do_layout(self, rect: QRect):
        y = rect.y()
        line_x = rect.x()
        row_max_y = y

        available_width = rect.width()

        for item in self._items:
            hint = item.sizeHint()
            w = hint.width()
            h = hint.height()

            if line_x + w > available_width + rect.x():
                line_x = rect.x()
                y = row_max_y + self._spacing

            item.setGeometry(QRect(line_x, y, w, h))
            line_x += w + self._spacing
            row_max_y = max(row_max_y, y + h)

        return y + row_max_y - rect.y()

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect)

    def sizeHint(self):
        if not self._items:
            return QSize(0, 0)
        total_w = sum(item.sizeHint().width() + self._spacing for item in self._items)
        rows = max(1, (total_w + self.count()) // max(self.count(), 1))
        return QSize(total_w, self._row_height * rows + self._spacing * (rows - 1))


class HistoryColorBtn(QPushButton):
    """历史记录中的小色块按钮"""

    def __init__(
        self, hex_color: str, accent_color: str, ar: int, ag: int, ab: int, parent=None
    ):
        super().__init__(parent)
        self._hex = hex_color.upper()
        self._accent = accent_color
        self._ar, self._ag, self._ab = ar, ag, ab

        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background: {self._hex}; border: 1px solid #e5e7eb; border-radius: 6px;"
        )

    def enterEvent(self, event):
        self.setStyleSheet(
            f"background: {self._hex}; "
            f"border: 1px solid rgba({self._ar}, {self._ag}, {self._ab}, 0.5); "
            f"border-radius: 6px;"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(
            f"background: {self._hex}; border: 1px solid #e5e7eb; border-radius: 6px;"
        )
        super().leaveEvent(event)


class ColorPickerWidget(QWidget):
    """取色器主窗口"""

    closed = pyqtSignal()

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._accent_color = host_info.get("accent_color", "#7B61FF")
        self._data_dir = host_info.get("data_dir")
        self._app = host_info.get("app")

        self._ar, self._ag, self._ab = _rgb_from_hex(self._accent_color)

        self._history = ColorHistory(self._data_dir) if self._data_dir else None
        self._current_hex = "#000000"
        self._overlay = None
        self._screenshot = None
        self._picker_active = False
        self._closed = False
        self._drag_pos = QPoint()

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(360, 580)

        self._build_ui()
        self._apply_theme_style()

        self._screenshot = None
        self._picker_active = True

    def show(self):
        if self._picker_active and self._overlay is None:
            self._show_picker_overlay()
            return
        super().show()

    def _rgb_from_hex(self, hex_color: str):
        return _rgb_from_hex(hex_color)

    def _build_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setObjectName("MainContainer")
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setAttribute(Qt.WA_StyledBackground, True)
        title_bar.setFixedHeight(54)
        title_lay = QHBoxLayout(title_bar)
        title_lay.setContentsMargins(20, 0, 10, 0)

        title_lbl = QLabel("取色器")
        title_lbl.setObjectName("WindowTitle")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")
        title_lbl.setCursor(Qt.SizeAllCursor)
        title_lbl.mousePressEvent = self._make_title_drag(True)
        title_lbl.mouseMoveEvent = self._make_title_drag(False)
        title_lbl.mouseReleaseEvent = self._make_title_drag(None)
        title_lay.addWidget(title_lbl)
        title_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "background: transparent; color: #86868b; border: none; border-radius: 6px; font-size: 16px;"
        )
        close_btn.clicked.connect(self._on_close_clicked)
        close_btn.enterEvent = lambda e: close_btn.setStyleSheet(
            f"background: rgba({self._ar}, {self._ag}, {self._ab}, 0.1); "
            "color: #1d1d1f; border: none; border-radius: 6px; font-size: 16px;"
        )
        close_btn.leaveEvent = lambda e: close_btn.setStyleSheet(
            "background: transparent; color: #86868b; border: none; border-radius: 6px; font-size: 16px;"
        )
        title_lay.addWidget(close_btn)
        container_lay.addWidget(title_bar)

        scroll = QScrollArea()
        scroll.setObjectName("ContentScroll")
        scroll.setStyleSheet("border: none; background: transparent;")
        scroll.setFrameShape(0)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setAttribute(Qt.WA_StyledBackground, True)
        scroll.viewport().setStyleSheet("background: #ffffff;")

        content = QWidget()
        content.setObjectName("ContentWidget")
        content.setAttribute(Qt.WA_StyledBackground, True)
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(16, 16, 16, 12)
        content_lay.setSpacing(16)

        self._swatch = ColorSwatchWidget(QColor(self._current_hex), self._accent_color)
        content_lay.addWidget(self._swatch)

        hex_val = self._current_hex
        rgb_c = QColor(hex_val)
        h, s, l = rgb_to_hsl(rgb_c.red(), rgb_c.green(), rgb_c.blue())
        c, m, y, k = rgb_to_cmyk(rgb_c.red(), rgb_c.green(), rgb_c.blue())

        fmt_section_lbl = QLabel("颜色值")
        fmt_section_lbl.setStyleSheet(
            "color: #6b7280; font-size: 11px; font-weight: bold;"
        )
        content_lay.addWidget(fmt_section_lbl)

        fmt_grid = QFrame()
        fmt_grid.setObjectName("FormatGrid")
        fmt_grid_lay = QVBoxLayout(fmt_grid)
        fmt_grid_lay.setContentsMargins(0, 0, 0, 0)
        fmt_grid_lay.setSpacing(6)

        self._hex_row = FormatRow(
            "HEX", hex_val, self._accent_color, self._ar, self._ag, self._ab
        )
        self._hex_row.copy_requested.connect(self._copy_text)
        fmt_grid_lay.addWidget(self._hex_row)

        rgb_str = f"{rgb_c.red()}, {rgb_c.green()}, {rgb_c.blue()}"
        self._rgb_row = FormatRow(
            "RGB", rgb_str, self._accent_color, self._ar, self._ag, self._ab
        )
        self._rgb_row.copy_requested.connect(self._copy_text)
        fmt_grid_lay.addWidget(self._rgb_row)

        hsl_str = f"{h}°, {s}%, {l}%"
        self._hsl_row = FormatRow(
            "HSL", hsl_str, self._accent_color, self._ar, self._ag, self._ab
        )
        self._hsl_row.copy_requested.connect(self._copy_text)
        fmt_grid_lay.addWidget(self._hsl_row)

        cmyk_str = f"{c}%, {m}%, {y}%, {k}%"
        self._cmyk_row = FormatRow(
            "CMYK", cmyk_str, self._accent_color, self._ar, self._ag, self._ab
        )
        self._cmyk_row.copy_requested.connect(self._copy_text)
        fmt_grid_lay.addWidget(self._cmyk_row)

        content_lay.addWidget(fmt_grid)

        hist_section_lbl = QLabel("历史记录")
        hist_section_lbl.setStyleSheet(
            "color: #6b7280; font-size: 11px; font-weight: bold;"
        )
        content_lay.addWidget(hist_section_lbl)

        hist_frame = QFrame()
        hist_frame.setObjectName("HistoryFrame")
        hist_frame.setAttribute(Qt.WA_StyledBackground, True)
        hist_frame.setStyleSheet(
            "background: #f9fafb; border: 1px solid #f3f4f6; border-radius: 8px;"
        )
        hist_lay = QVBoxLayout(hist_frame)
        hist_lay.setContentsMargins(8, 8, 8, 8)
        hist_lay.setSpacing(6)

        self._history_flow = HistoryFlowLayout()
        self._history_flow_widget = QWidget()
        self._history_flow_widget.setLayout(self._history_flow)
        self._history_flow_widget.setStyleSheet(
            "background: transparent; border: none;"
        )
        hist_lay.addWidget(self._history_flow_widget)

        self._clear_hist_btn = QPushButton("清空")
        self._clear_hist_btn.setObjectName("ClearHistBtn")
        self._clear_hist_btn.setFixedSize(40, 22)
        self._clear_hist_btn.setCursor(Qt.PointingHandCursor)
        self._clear_hist_btn.setStyleSheet(
            f"background: transparent; border: none; color: {self._accent_color}; "
            "font-size: 11px; font-weight: 500;"
        )
        self._clear_hist_btn.clicked.connect(self._clear_history)
        hist_lay.addWidget(self._clear_hist_btn, 0, Qt.AlignRight)

        content_lay.addWidget(hist_frame)

        content_lay.addStretch()

        scroll.setWidget(content)
        container_lay.addWidget(scroll)

        footer = QWidget()
        footer.setFixedHeight(48)
        footer.setAttribute(Qt.WA_StyledBackground, True)
        footer.setStyleSheet("border-top: 1px solid #f3f4f6;")
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(16, 0, 16, 0)

        self._repick_btn = QPushButton("重新取色")
        self._repick_btn.setObjectName("RepickBtn")
        self._repick_btn.setFixedHeight(32)
        self._repick_btn.setCursor(Qt.PointingHandCursor)
        self._repick_btn.setStyleSheet(
            f"background: {self._accent_color}; color: #ffffff; "
            "border: none; border-radius: 8px; font-size: 13px; font-weight: 500;"
        )
        self._repick_btn.enterEvent = lambda e: self._repick_btn.setStyleSheet(
            f"background: rgba({self._ar}, {self._ag}, {self._ab}, 0.85); color: #ffffff; "
            "border: none; border-radius: 8px; font-size: 13px; font-weight: 500;"
        )
        self._repick_btn.leaveEvent = lambda e: self._repick_btn.setStyleSheet(
            f"background: {self._accent_color}; color: #ffffff; "
            "border: none; border-radius: 8px; font-size: 13px; font-weight: 500;"
        )
        self._repick_btn.clicked.connect(self._start_picking)
        footer_lay.addWidget(self._repick_btn)
        container_lay.addWidget(footer)

        main_lay.addWidget(container)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)

        self._load_history()

    def _apply_theme_style(self):
        accent = self._accent_color
        ar, ag, ab = self._ar, self._ag, self._ab
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
            #ContentScroll {{
                border: none;
                background: #ffffff;
            }}
            #ContentWidget {{
                background: #ffffff;
            }}
            #HistoryFrame {{
                background: #f9fafb;
                border: 1px solid #f3f4f6;
                border-radius: 8px;
            }}
            #ClearHistBtn {{
                background: transparent;
                border: none;
                color: {accent};
                font-size: 11px;
                font-weight: 500;
            }}
            #RepickBtn {{
                background: {accent};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            """)

    def _make_title_drag(self, press):
        def handler(event):
            if press is True:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            elif press is False and event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self._drag_pos)
                event.accept()

        return handler

    def _load_history(self):
        while self._history_flow.count():
            item = self._history_flow.takeAt(0)
            if item:
                item.widget().deleteLater()

        if not self._history:
            return

        items = self._history.items
        if not items:
            return

        for entry in items:
            hex_c = entry["hex"]
            btn = HistoryColorBtn(
                hex_c, self._accent_color, self._ar, self._ag, self._ab
            )
            btn.clicked.connect(lambda _, h=hex_c: self._load_color(h))
            self._history_flow.addWidget(btn)

    def _load_color(self, hex_color: str):
        self._current_hex = hex_color.upper()
        c = QColor(self._current_hex)
        r, g, b = c.red(), c.green(), c.blue()
        h, s, l = rgb_to_hsl(r, g, b)
        c_cmyk, m_cmyk, y_cmyk, k_cmyk = rgb_to_cmyk(r, g, b)

        self._swatch.setStyleSheet(
            f"border-radius: 12px; background: {self._current_hex}; border: 1px solid #e5e7eb;"
        )

        self._hex_row.set_value(self._current_hex)
        self._rgb_row.set_value(f"{r}, {g}, {b}")
        self._hsl_row.set_value(f"{h}°, {s}%, {l}%")
        self._cmyk_row.set_value(f"{c_cmyk}%, {m_cmyk}%, {y_cmyk}%, {k_cmyk}%")

    def _copy_text(self, text: str):
        QApplication.clipboard().setText(text)
        try:
            subprocess.Popen(
                ["notify-send", "-a", "umi-float", f"已复制: {text}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _clear_history(self):
        if self._history:
            self._history.clear()
        self._load_history()

    def _show_picker_overlay(self):
        screen = QApplication.primaryScreen()
        logical_size = screen.geometry().size()
        pixmap = screen.grabWindow(0)
        if pixmap.size() != logical_size:
            self._screenshot = pixmap.scaled(
                logical_size.width(),
                logical_size.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation,
            )
        else:
            self._screenshot = pixmap
        self._picker_active = True
        self._overlay = _PickerOverlay(self._screenshot, self._accent_color)
        self._overlay.finished.connect(self._on_overlay_closed)
        self._overlay.show()

    def _start_picking(self):
        self._overlay = None
        self._picker_active = True
        self._show_picker_overlay()

    def _on_overlay_closed(self, picked_color):
        self._overlay = None
        self._picker_active = False
        if picked_color:
            self._current_hex = picked_color.upper()
            self._update_display(self._current_hex)
            if self._history:
                self._history.add(self._current_hex)
            self._load_history()
            self._show_widget()
        else:
            self._closed = True
            self.closed.emit()

    def _show_widget(self):
        self._position_near_anchor()
        super().show()
        self.raise_()
        self.activateWindow()

    def _position_near_anchor(self):
        pass

    def _update_display(self, hex_color: str):
        self._load_color(hex_color)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if (
                self.isVisible()
                and not self.isActiveWindow()
                and not self._picker_active
                and not self._closed
            ):
                self._closed = True
                self.closed.emit()
        super().changeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _on_close_clicked(self):
        self.closed.emit()
