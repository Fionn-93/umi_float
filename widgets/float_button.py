"""
悬浮球按钮组件
支持三种显示模式：时钟、性能、天气
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QTime, QRect
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPen, QIcon, QPixmap
)

from core.config import get_config
from utils.theme_colors import theme_from_key, DEFAULT_THEME
from utils.memory_info import get_memory_usage
from utils.network_info import NetworkMonitor
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
        self._net_up_text = "0B"
        self._net_down_text = "0B"
        self._weather_data = None

        self._apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_content)
        self.timer.start(1000)

        self._refresh_content()

    def _apply_theme(self):
        config = get_config()
        theme_key = config.get().get('theme', DEFAULT_THEME)
        colors = theme_from_key(theme_key)
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
        if mode not in ('clock', 'performance', 'weather'):
            return
        self._mode = mode
        if mode == 'clock':
            self.timer.setInterval(1000)
            self._update_style()
        elif mode == 'performance':
            self.timer.setInterval(1000)
            self.setStyleSheet("background-color: transparent; border: none;")
        elif mode == 'weather':
            self.timer.setInterval(30 * 60 * 1000)
            self.setStyleSheet("background-color: transparent; border: none;")
            self._fetch_weather()
        self._refresh_content()

    def _fetch_weather(self):
        config = get_config()
        cfg = config.get()
        api_key = cfg.get('weather_api_key', '')
        location = cfg.get('weather_location', '101010100')
        api_host = cfg.get('weather_api_host', '') or None
        self._weather_data = fetch_weather(api_key, location, api_host)

    def _refresh_content(self):
        if self._mode == 'performance':
            mem = get_memory_usage()
            if mem:
                self._mem_percent = mem['percent']
            net = NetworkMonitor.get().get_speed()
            if net:
                self._net_up_text = net['up_text']
                self._net_down_text = net['down_text']
        elif self._mode == 'weather':
            cached = get_cached_weather()
            if cached:
                self._weather_data = cached
            else:
                self._fetch_weather()
        self.update()

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
        elif self._mode == 'performance':
            self._paint_performance_mode()
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

    def _paint_performance_mode(self):
        size = self.size
        radius = size // 2 - 1
        ring_width = max(3, int(size * 0.08))
        drawing_radius = radius - ring_width // 2
        ring_rect = QRect(
            1 + ring_width // 2,
            1 + ring_width // 2,
            drawing_radius * 2,
            drawing_radius * 2
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg = QColor(self.THEME_BG)
        bg.setAlpha(255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        track_color = QColor(self.THEME_TEXT)
        track_color.setAlpha(40)
        track_pen = QPen(track_color, ring_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(ring_rect, 0, 360 * 16)

        progress_color = QColor(self.THEME_TEXT)
        progress_color.setAlpha(220)
        progress_pen = QPen(progress_color, ring_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(progress_pen)
        span_angle = int(self._mem_percent / 100.0 * 360 * 16)
        painter.drawArc(ring_rect, 90 * 16, -span_angle)

        percent_font_size = max(8, int(size * 0.24))
        percent_font = QFont("", percent_font_size, QFont.Bold)
        painter.setFont(percent_font)
        painter.setPen(QPen(self.THEME_TEXT))
        percent_text = f"{int(self._mem_percent)}%"
        fm = painter.fontMetrics()
        ph = fm.height()
        py = size // 2 - ph // 2 + fm.ascent()
        px = (size - fm.horizontalAdvance(percent_text)) // 2
        painter.drawText(px, py, percent_text)

        net_font_size = max(5, int(size * 0.11))
        net_font = QFont("", net_font_size)
        painter.setFont(net_font)
        net_text = f"↓{self._net_down_text}"
        fm2 = painter.fontMetrics()
        nx = (size - fm2.horizontalAdvance(net_text)) // 2
        ny = py + fm2.ascent() + 6
        painter.drawText(nx, ny, net_text)

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
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