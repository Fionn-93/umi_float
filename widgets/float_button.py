"""
悬浮球按钮组件
支持三种显示模式：时钟、性能、天气
支持胶囊变形（贴边性能监视器）
"""

from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import (
    Qt, QTimer, QTime, QRect, QRectF, pyqtProperty,
    QPropertyAnimation,
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPen, QIcon, QPixmap, QPainterPath,
)
from PyQt5.QtSvg import QSvgRenderer

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

        self._capsule_mode = False
        self._scale = 1.0

        self._override_active = False
        self._override_text = ""
        self._override_progress = 0.0
        self._override_icon_path = None
        self._pomodoro_hidden = False
        self._hovered = False
        self._text_opacity = 1.0
        self._fade_anim = QPropertyAnimation(self, b"text_opacity")
        self._fade_anim.setDuration(1000)

        self._apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_content)
        self.timer.start(1000)

        self._refresh_content()

    def _apply_theme(self):
        config = get_config()
        theme_key = config.get().get("theme", DEFAULT_THEME)
        colors = theme_from_key(theme_key)
        self.THEME_BG = colors["float_bg"]
        self.THEME_TEXT = colors["float_text"]
        self.THEME_BORDER = colors["float_border"]

    def refresh_theme(self):
        self._apply_theme()
        self.update()

    def set_size(self, size: int):
        self.size = size
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.update()

    def set_mode(self, mode: str):
        if mode not in ("clock", "performance", "weather"):
            return
        self._mode = mode
        if mode == "clock":
            self.timer.setInterval(100)
            self.setStyleSheet("background-color: transparent; border: none;")
        elif mode == "performance":
            self.timer.setInterval(1000)
            self.setStyleSheet("background-color: transparent; border: none;")
        elif mode == "weather":
            self.timer.setInterval(30 * 60 * 1000)
            self.setStyleSheet("background-color: transparent; border: none;")
            self._fetch_weather()
        self._refresh_content()

    def set_override(self, text: str, progress: float, icon_path: str = None):
        self._override_text = text
        self._override_progress = max(0.0, min(1.0, progress))
        self._override_icon_path = icon_path
        was_pomodoro = self._pomodoro_hidden
        self._pomodoro_hidden = icon_path is not None and "tomato" in str(icon_path)
        self._override_active = True
        self._hovered = False

        if self._pomodoro_hidden and not was_pomodoro:
            self._text_opacity = 1.0
            self._fade_anim.stop()
            self._fade_anim.setStartValue(1.0)
            self._fade_anim.setEndValue(0.25)
            self._fade_anim.start()
        elif not self._pomodoro_hidden and was_pomodoro:
            self._text_opacity = 1.0
            self._fade_anim.stop()
        self.update()

    def clear_override(self):
        self._override_active = False
        self._override_text = ""
        self._override_progress = 0.0
        self._override_icon_path = None
        self._pomodoro_hidden = False
        self._hovered = False
        self._text_opacity = 1.0
        self._fade_anim.stop()
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        if self._pomodoro_hidden and self._override_active:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._text_opacity)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if self._pomodoro_hidden and self._override_active:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._text_opacity)
            self._fade_anim.setEndValue(0.25)
            self._fade_anim.start()
        super().leaveEvent(event)

    def _fetch_weather(self):
        config = get_config()
        cfg = config.get()
        api_key = cfg.get("weather_api_key", "")
        location = cfg.get("weather_location", "101010100")
        api_host = cfg.get("weather_api_host", "") or None
        self._weather_data = fetch_weather(api_key, location, api_host)

    def _refresh_content(self):
        mem = get_memory_usage()
        if mem:
            self._mem_percent = mem["percent"]
        net = NetworkMonitor.get().get_speed()
        if net:
            self._net_up_text = net["up_text"]
            self._net_down_text = net["down_text"]
        if self._mode == "weather":
            cached = get_cached_weather()
            if cached:
                self._weather_data = cached
            else:
                self._fetch_weather()
        self.update()

    # -- scale property for QPropertyAnimation --

    def _get_scale(self):
        return self._scale

    def _set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, _get_scale, _set_scale)

    def _get_text_opacity(self):
        return self._text_opacity

    def _set_text_opacity(self, value):
        self._text_opacity = value
        self.update()

    text_opacity = pyqtProperty(float, _get_text_opacity, _set_text_opacity)

    # -- painting --

    def paintEvent(self, event):
        if self._override_active and not self._capsule_mode:
            self._paint_override_mode()
        elif self._capsule_mode:
            self._paint_capsule_mode()
        else:
            if self._mode == "clock":
                self._paint_clock_mode()
            elif self._mode == "performance":
                self._paint_performance_mode()
            elif self._mode == "weather":
                self._paint_weather_mode()

    def _perf_color(self):
        if self._mem_percent < 40:
            return QColor(78, 205, 196)
        elif self._mem_percent < 80:
            return QColor(255, 200, 50)
        return QColor(255, 107, 107)

    def _paint_capsule_mode(self):
        w = self.width()
        h = self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        radius = w // 2
        margin = 0
        capsule_rect = QRectF(
            margin, margin, w - 2 * margin, h - 2 * margin,
        )

        track_color = QColor(self.THEME_BG)
        track_color.setAlpha(int(255 * 0.8))
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(capsule_rect, radius, radius)

        fill_h = int(h * self._mem_percent / 100.0)
        fill_rect = QRectF(
            margin, h - margin - fill_h,
            w - 2 * margin, fill_h,
        )

        painter.setBrush(self._perf_color())

        clip_path = QPainterPath()
        clip_path.addRoundedRect(capsule_rect, radius, radius)
        painter.setClipPath(clip_path)
        painter.drawRect(fill_rect)
        painter.setClipping(False)

        border_color = QColor(self.THEME_BORDER)
        border_color.setAlpha(100)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(capsule_rect, radius, radius)

        painter.end()

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
        self._apply_scale_transform(painter)

        opacity = int(get_config().get().get("opacity", 0.9) * 255)
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
            drawing_radius * 2,
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._apply_scale_transform(painter)

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
        net_text = f"\u2193{self._net_down_text}"

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
        painter.drawText(
            row1_x + num_w + 1,
            start_y + fm_num.ascent() - (fm_num.ascent() // 7),
            sym_text,
        )

        net_x = (size - net_w) // 2
        painter.setFont(font_net)
        sec_color = QColor(self.THEME_TEXT)
        sec_color.setAlpha(160)
        painter.setPen(QPen(sec_color))
        painter.drawText(
            net_x, start_y + fm_num.height() + 0 + fm_net.ascent(), net_text
        )

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
        self._apply_scale_transform(painter)

        opacity = int(get_config().get().get("opacity", 0.9) * 255)
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
            painter.drawText(self.rect(), Qt.AlignCenter, "--\u00b0C")
        else:
            icon_code = data.get("icon_code", "100")
            icon_path = get_icon_path(icon_code)
            icon = QIcon(icon_path)
            temp = str(data.get("temp", "--"))
            desc = data.get("text", "")

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
                painter.drawPixmap(
                    (size - icon_size) // 2,
                    (size - icon_size) // 2,
                    icon_size,
                    icon_size,
                    colored,
                )
                painter.restore()

            font_temp = QFont("", max(8, int(size * 0.28)), QFont.Bold)
            font_unit = QFont("", max(5, int(size * 0.13)), QFont.Bold)
            font_desc = QFont("", max(5, int(size * 0.11)), QFont.Normal)

            painter.setFont(font_temp)
            fm_temp = painter.fontMetrics()
            temp_w = fm_temp.horizontalAdvance(temp)

            painter.setFont(font_unit)
            fm_unit = painter.fontMetrics()
            unit_w = fm_unit.horizontalAdvance("\u00b0C")

            painter.setFont(font_desc)
            fm_desc = painter.fontMetrics()

            total_h = fm_temp.height() + fm_desc.height() + 4
            start_y = (size - total_h) // 2 + 4

            row1_x = (size - (temp_w + unit_w)) // 2

            painter.setFont(font_temp)
            painter.setPen(QPen(self.THEME_TEXT))
            painter.drawText(row1_x, start_y + fm_temp.ascent(), temp)

            painter.setFont(font_unit)
            painter.drawText(
                row1_x + temp_w + 1,
                start_y + fm_temp.ascent() - (fm_temp.ascent() // 7),
                "\u00b0C",
            )

            desc_x = (size - fm_desc.horizontalAdvance(desc)) // 2
            painter.setFont(font_desc)
            color_desc = QColor(self.THEME_TEXT)
            color_desc.setAlpha(160)
            painter.setPen(QPen(color_desc))
            painter.drawText(
                desc_x, start_y + fm_temp.height() + 0 + fm_desc.ascent(), desc
            )

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def _paint_override_mode(self):
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
        self._apply_scale_transform(painter)

        opacity = int(get_config().get().get("opacity", 0.9) * 255)
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

        span_angle = int(self._override_progress * 360 * 16)
        progress_color = QColor(self.THEME_TEXT)
        progress_color.setAlpha(200)
        painter.setPen(QPen(progress_color, ring_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring_rect, 90 * 16, -span_angle)

        if self._override_icon_path:
            dpr = QApplication.instance().devicePixelRatio() if QApplication.instance() else 1.0
            icon_size = int(size * 0.50)
            src = QPixmap(int(icon_size * dpr), int(icon_size * dpr))
            src.fill(Qt.transparent)
            svg_painter = QPainter(src)
            svg_painter.setRenderHint(QPainter.Antialiasing)
            renderer = QSvgRenderer(self._override_icon_path)
            renderer.render(svg_painter)
            svg_painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            svg_painter.fillRect(src.rect(), self.THEME_TEXT)
            svg_painter.end()
            src.setDevicePixelRatio(dpr)
            painter.save()
            painter.setOpacity(0.22)
            painter.drawPixmap(
                (size - icon_size) // 2, (size - icon_size) // 2,
                icon_size, icon_size, src,
            )
            painter.restore()

        painter.save()
        painter.setOpacity(self._text_opacity)
        self._draw_override_text(painter, size)
        painter.restore()

        border_pen = QPen(self.THEME_BORDER, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, radius * 2, radius * 2)

        painter.end()

    def _draw_override_text(self, painter, size):
        text = self._override_text

        parts = text.split(":")
        if len(parts) == 3:
            top_text = "%s:%s" % (parts[0], parts[1])
            bottom_text = parts[2]
        else:
            top_text = parts[0] if len(parts) > 0 else ""
            bottom_text = parts[1] if len(parts) > 1 else ""

        top_size = max(8, int(size * 0.25))
        bottom_size = max(6, int(size * 0.18))

        font_top = QFont("", top_size, QFont.Bold)
        painter.setFont(font_top)
        painter.setPen(QPen(self.THEME_TEXT))
        fm_top = painter.fontMetrics()

        center_y = size // 2
        top_height = fm_top.height()
        top_rect = QRect(0, center_y - top_height + 4, size, top_height)
        painter.drawText(top_rect, Qt.AlignCenter, top_text)

        font_bottom = QFont("", bottom_size, QFont.Normal)
        painter.setFont(font_bottom)
        color_bottom = QColor(self.THEME_TEXT)
        color_bottom.setAlpha(180)
        painter.setPen(QPen(color_bottom))
        bottom_rect = QRect(0, center_y - 2, size, top_height)
        painter.drawText(bottom_rect, Qt.AlignCenter, bottom_text)

    def _apply_scale_transform(self, painter):
        if self._scale != 1.0:
            s = self._scale
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            painter.translate(cx, cy)
            painter.scale(s, s)
            painter.translate(-cx, -cy)

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)
