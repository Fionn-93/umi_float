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
from utils.weather_info import fetch_weather, get_cached_weather, get_icon_path


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

    def refresh_theme(self):
        self._apply_theme()
        self.update()

    def set_size(self, size: int):
        self.size = size
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.update()

    def set_mode(self, mode: str):
        if mode not in ('clock', 'performance', 'weather'):
            return
        self._mode = mode
        if mode == 'clock':
            self.timer.setInterval(100)
            self.setStyleSheet("background-color: transparent; border: none;")
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
            self._paint_clock_mode()
        elif self._mode == 'performance':
            self._paint_performance_mode()
        elif self._mode == 'weather':
            self._paint_weather_mode()

    def _paint_clock_mode(self):
        size = self.size
        radius = size // 2 - 1
        ring_width = max(3, int(size * 0.08))
        drawing_radius = radius - ring_width // 2
        ring_rect = QRect(
            1 + ring_width // 2,
            1 + ring_width // 2,
            drawing_radius * 2,
            drawing_radius * 2,
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opacity = int(get_config().get().get('opacity', 0.9) * 255)
        bg = QColor(self.THEME_BG)
        bg.setAlpha(opacity)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        track_color = QColor(self.THEME_TEXT)
        track_color.setAlpha(40)
        painter.setPen(QPen(track_color, ring_width, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(ring_rect, 0, 360 * 16)

        now = QTime.currentTime()
        seconds = now.second() + now.msec() / 1000.0
        span_angle = int(seconds / 60.0 * 360 * 16)

        progress_color = QColor(self.THEME_TEXT)
        progress_color.setAlpha(200)
        painter.setPen(QPen(progress_color, ring_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring_rect, 90 * 16, -span_angle)

        hh = now.toString("HH")
        mm = now.toString("mm")

        font_hh = QFont("", max(8, int(size * 0.25)), QFont.Bold)
        painter.setFont(font_hh)
        painter.setPen(QPen(self.THEME_TEXT))
        fm_hh = painter.fontMetrics()

        center_y = size // 2
        hh_height = fm_hh.height()
        hh_rect = QRect(0, center_y - hh_height + 4, size, hh_height)
        painter.drawText(hh_rect, Qt.AlignCenter, hh)

        font_mm = QFont("", max(6, int(size * 0.18)), QFont.Normal)
        painter.setFont(font_mm)
        color_mm = QColor(self.THEME_TEXT)
        color_mm.setAlpha(160)
        painter.setPen(QPen(color_mm))
        mm_rect = QRect(0, center_y - 2, size, hh_height)
        painter.drawText(mm_rect, Qt.AlignCenter, mm)

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

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

        span_angle = int(self._mem_percent / 100.0 * 360 * 16)

        if self._mem_percent < 40:
            perf_color = QColor(78, 205, 196)
        elif self._mem_percent < 80:
            perf_color = QColor(255, 200, 50)
        else:
            perf_color = QColor(255, 107, 107)

        painter.setPen(QPen(perf_color, ring_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring_rect, 90 * 16, -span_angle)

        num_text = str(int(self._mem_percent))
        sym_text = "%"
        net_text = f"↓{self._net_down_text}"

        font_num = QFont("", max(8, int(size * 0.28)), QFont.Bold)
        font_sym = QFont("", max(5, int(size * 0.13)), QFont.Bold)
        font_net = QFont("monospace", max(5, int(size * 0.11)), QFont.Normal)

        painter.setFont(font_num)
        fm_num = painter.fontMetrics()
        num_w = fm_num.horizontalAdvance(num_text)

        painter.setFont(font_sym)
        fm_sym = painter.fontMetrics()
        sym_w = fm_sym.horizontalAdvance(sym_text)

        painter.setFont(font_net)
        fm_net = painter.fontMetrics()
        net_w = fm_net.horizontalAdvance(net_text)

        total_h = fm_num.height() + fm_net.height() + 4
        start_y = (size - total_h) // 2 + 4

        row1_x = (size - (num_w + sym_w)) // 2

        painter.setFont(font_num)
        painter.setPen(QPen(self.THEME_TEXT))
        painter.drawText(row1_x, start_y + fm_num.ascent(), num_text)

        painter.setFont(font_sym)
        painter.setPen(QPen(self.THEME_TEXT))
        painter.drawText(row1_x + num_w + 1, start_y + fm_num.ascent() - (fm_num.ascent() // 7), sym_text)

        net_x = (size - net_w) // 2
        painter.setFont(font_net)
        sec_color = QColor(self.THEME_TEXT)
        sec_color.setAlpha(160)
        painter.setPen(QPen(sec_color))
        painter.drawText(net_x, start_y + fm_num.height() + 0 + fm_net.ascent(), net_text)

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def _paint_weather_mode(self):
        size = self.size
        radius = size // 2 - 1
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        opacity = int(get_config().get().get('opacity', 0.9) * 255)
        bg = QColor(self.THEME_BG)
        bg.setAlpha(opacity)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        data = self._weather_data

        if data is None:
            font = QFont("", max(8, int(size * 0.15)), QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(self.THEME_TEXT))
            painter.drawText(self.rect(), Qt.AlignCenter, "--°C")
        else:
            icon_code = data.get('icon_code', '100')
            icon_path = get_icon_path(icon_code)
            icon = QIcon(icon_path)
            temp = str(data.get('temp', '--'))
            desc = data.get('text', '')

            if not icon.isNull():
                from PyQt5.QtWidgets import QApplication
                app = QApplication.instance()
                dpr = app.devicePixelRatio() if app else 1.0
                icon_size = int(size * 0.50)

                src = icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
                src.setDevicePixelRatio(dpr)
                colored = QPixmap(src.size())
                colored.setDevicePixelRatio(dpr)
                colored.fill(Qt.transparent)
                p = QPainter(colored)
                p.drawPixmap(0, 0, src)
                p.setCompositionMode(QPainter.CompositionMode_SourceIn)
                p.fillRect(colored.rect(), self.THEME_TEXT)
                p.end()

                painter.save()
                painter.setOpacity(0.22)
                painter.drawPixmap((size - icon_size) // 2, (size - icon_size) // 2, icon_size, icon_size, colored)
                painter.restore()

            font_temp = QFont("", max(8, int(size * 0.28)), QFont.Bold)
            font_unit = QFont("", max(5, int(size * 0.13)), QFont.Bold)
            font_desc = QFont("", max(5, int(size * 0.11)), QFont.Normal)

            painter.setFont(font_temp)
            fm_temp = painter.fontMetrics()
            temp_w = fm_temp.horizontalAdvance(temp)

            painter.setFont(font_unit)
            fm_unit = painter.fontMetrics()
            unit_w = fm_unit.horizontalAdvance("°C")

            painter.setFont(font_desc)
            fm_desc = painter.fontMetrics()

            total_h = fm_temp.height() + fm_desc.height() + 4
            start_y = (size - total_h) // 2 + 4

            row1_x = (size - (temp_w + unit_w)) // 2

            painter.setFont(font_temp)
            painter.setPen(QPen(self.THEME_TEXT))
            painter.drawText(row1_x, start_y + fm_temp.ascent(), temp)

            painter.setFont(font_unit)
            painter.drawText(row1_x + temp_w + 1, start_y + fm_temp.ascent() - (fm_temp.ascent() // 7), "°C")

            desc_x = (size - fm_desc.horizontalAdvance(desc)) // 2
            painter.setFont(font_desc)
            color_desc = QColor(self.THEME_TEXT)
            color_desc.setAlpha(160)
            painter.setPen(QPen(color_desc))
            painter.drawText(desc_x, start_y + fm_temp.height() + 0 + fm_desc.ascent(), desc)

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)