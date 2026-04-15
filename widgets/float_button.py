"""
悬浮球按钮组件
支持三种显示模式：时钟、内存水位、天气
"""
import math
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QTime, QRect
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QIcon, QPixmap
)

from core.config import get_config
from utils.theme_colors import theme_from_hex
from utils.memory_info import get_memory_usage
from utils.weather_info import fetch_weather, get_cached_weather


class FloatButton(QLabel):
    """圆形悬浮球按钮"""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)

        self._mode = "clock"
        self._mem_percent = 0.0
        self._wave_offset = 0.0
        self._weather_data = None
        self._wave_timer = None

        self._apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_content)
        self.timer.start(1000)

        self._refresh_content()

    def _apply_theme(self):
        config = get_config()
        theme_color = config.get().get('theme_color', '#6495ED')
        colors = theme_from_hex(theme_color)
        self.THEME_BG = colors['float_bg']
        self.THEME_TEXT = colors['float_text']
        self.THEME_BORDER = colors['float_border']

    def _update_style(self):
        radius = self.size // 2
        font_size = max(8, int(self.size * 0.27))
        self.setStyleSheet(f"""
            background-color: rgba({self.THEME_BG.red()}, {self.THEME_BG.green()}, {self.THEME_BG.blue()}, {self.THEME_BG.alpha()});
            color: rgb({self.THEME_TEXT.red()}, {self.THEME_TEXT.green()}, {self.THEME_TEXT.blue()});
            border: 2px solid rgb({self.THEME_BORDER.red()}, {self.THEME_BORDER.green()}, {self.THEME_BORDER.blue()});
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: bold;
        """)

    def refresh_theme(self):
        self._apply_theme()
        self.update()

    def set_size(self, size: int):
        self.size = size
        self.setFixedSize(size, size)
        self._update_style()
        self.update()

    def set_mode(self, mode: str):
        if mode not in ('clock', 'memory', 'weather'):
            return
        self._mode = mode
        if mode == 'clock':
            self.timer.setInterval(1000)
            self._stop_wave_timer()
            self._update_style()
        elif mode == 'memory':
            self.timer.setInterval(2000)
            self._start_wave_timer()
            self.setStyleSheet("background-color: transparent; border: none;")
        elif mode == 'weather':
            self.timer.setInterval(30 * 60 * 1000)
            self._stop_wave_timer()
            self.setStyleSheet("background-color: transparent; border: none;")
            self._fetch_weather()
        self._refresh_content()

    def _start_wave_timer(self):
        if self._wave_timer is None:
            self._wave_timer = QTimer(self)
            self._wave_timer.timeout.connect(self._animate_wave)
            self._wave_timer.start(50)

    def _stop_wave_timer(self):
        if self._wave_timer is not None:
            self._wave_timer.stop()
            self._wave_timer.deleteLater()
            self._wave_timer = None

    def _animate_wave(self):
        self._wave_offset += 3.0
        if self._wave_offset > 360:
            self._wave_offset -= 360
        self.update()

    def _fetch_weather(self):
        config = get_config()
        cfg = config.get()
        api_key = cfg.get('weather_api_key', '')
        location = cfg.get('weather_location', '101010100')
        self._weather_data = fetch_weather(api_key, location)

    def _refresh_content(self):
        if self._mode == 'memory':
            mem = get_memory_usage()
            if mem:
                self._mem_percent = mem['percent']
        elif self._mode == 'weather':
            cached = get_cached_weather()
            if cached:
                self._weather_data = cached
            else:
                self._fetch_weather()
        self.update()

    # ── 绘制 ──

    def paintEvent(self, event):
        if self._mode == 'clock':
            self._paint_via_stylesheet()
            super().paintEvent(event)
            current_time = QTime.currentTime().toString("HH:mm")
            font_size = max(8, int(self.size * 0.27))
            font = QFont("", font_size, QFont.Bold)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setFont(font)
            painter.setPen(QPen(self.THEME_TEXT))
            painter.drawText(self.rect(), Qt.AlignCenter, current_time)
            painter.end()
        elif self._mode == 'memory':
            self._paint_memory_mode()
        elif self._mode == 'weather':
            self._paint_weather_mode()

    def _paint_via_stylesheet(self):
        opacity = int(get_config().get().get('opacity', 0.9) * 255)
        radius = self.size // 2
        font_size = max(8, int(self.size * 0.27))
        self.setStyleSheet(f"""
            background-color: rgba({self.THEME_BG.red()}, {self.THEME_BG.green()}, {self.THEME_BG.blue()}, {opacity});
            color: rgb({self.THEME_TEXT.red()}, {self.THEME_TEXT.green()}, {self.THEME_TEXT.blue()});
            border: 2px solid rgb({self.THEME_BORDER.red()}, {self.THEME_BORDER.green()}, {self.THEME_BORDER.blue()});
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: bold;
        """)

    def _paint_memory_mode(self):
        radius = self.size // 2 - 1
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        base = QColor(self.THEME_BG)
        base.setAlpha(255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        clip = QPainterPath()
        clip.addEllipse(1, 1, radius * 2, radius * 2)
        painter.setClipPath(clip)

        fill_ratio = min(max(self._mem_percent / 100.0, 0.0), 1.0)
        fill_y = self.size - int(self.size * fill_ratio)

        wave_color = QColor(self.THEME_TEXT)
        wave_color.setAlpha(180)

        fill_path = QPainterPath()
        fill_path.moveTo(0, self.size)
        fill_path.lineTo(0, fill_y)

        wave_amp = 3.0
        wave_freq = 0.08
        for x in range(self.size + 1):
            y = fill_y + wave_amp * math.sin(
                wave_freq * x * 2 * math.pi / self.size
                + math.radians(self._wave_offset)
            )
            fill_path.lineTo(x, y)

        fill_path.lineTo(self.size, self.size)
        fill_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(wave_color)
        painter.drawPath(fill_path)

        font_size = max(8, int(self.size * 0.27))
        font = QFont("", font_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self.THEME_TEXT))
        painter.setClipRect(self.rect())
        painter.drawText(self.rect(), Qt.AlignCenter, f"{int(self._mem_percent)}%")

        pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.setClipPath(QPainterPath())
        clip2 = QPainterPath()
        clip2.addEllipse(1, 1, radius * 2, radius * 2)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def _paint_weather_mode(self):
        opacity = int(get_config().get().get('opacity', 0.9) * 255)
        radius = self.size // 2 - 1
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        bg = QColor(self.THEME_BG)
        bg.setAlpha(opacity)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        data = self._weather_data

        if data is None:
            font_size = max(8, self.size // 4)
            font = QFont("", font_size, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(self.THEME_TEXT))
            painter.drawText(self.rect(), Qt.AlignCenter, "--°")
        else:
            icon_name = data.get('icon', 'weather-clear')
            icon = QIcon.fromTheme(icon_name)
            temp = data.get('temp', '--')

            icon_size = max(16, self.size // 2)
            if icon.isNull():
                text_icon = data.get('text', '')
                font_size = max(10, self.size // 4)
                font = QFont("", font_size, QFont.Bold)
                painter.setFont(font)
                painter.setPen(QPen(self.THEME_TEXT))
                text_rect = QRect(0, 0, self.size, self.size * 2 // 3)
                painter.drawText(text_rect, Qt.AlignCenter, text_icon)
            else:
                from PyQt5.QtWidgets import QApplication
                app = QApplication.instance()
                dpr = app.devicePixelRatio() if app else 1.0
                pixmap = icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
                pixmap.setDevicePixelRatio(dpr)
                ix = (self.size - icon_size) // 2
                iy = max(2, self.size // 2 - icon_size // 2 - 4)
                painter.drawPixmap(ix, iy, icon_size, icon_size, pixmap)

            temp_font_size = max(9, self.size // 5)
            temp_font = QFont("", temp_font_size, QFont.Bold)
            painter.setFont(temp_font)
            painter.setPen(QPen(self.THEME_TEXT))
            temp_text = f"{temp}°"
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(temp_text)
            th = fm.height()
            tx = (self.size - tw) // 2
            ty = self.size - max(4, self.size // 8)
            painter.drawText(tx, ty, temp_text)

        pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)