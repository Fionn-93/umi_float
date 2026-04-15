"""
主题色彩派生工具
从一个主色自动派生出完整的配色方案
"""
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


def derive_theme(primary: QColor) -> dict:
    """
    从主色派生完整配色方案

    Args:
        primary: 主色 QColor

    Returns:
        dict 包含:
            - float_bg: 悬浮球背景色 (主色, 95% alpha)
            - float_text: 悬浮球文字色 (明度自适应)
            - float_border: 悬浮球边框色 (饱和度+20%, 明度-15%)
            - pie_bg_normal: 面板按钮常态背景 (主色10%混白)
            - pie_bg_hovered: 面板按钮悬停背景 (主色, 85% alpha)
            - pie_text_normal: 面板按钮常态文字 (同边框色)
            - pie_text_hovered: 面板按钮悬停文字 (白色)
            - center_bg_normal: 中心按钮常态背景 (主色10%混白, 不透明)
            - center_bg_hovered: 中心按钮悬停背景 (主色, 不透明)
    """
    from PyQt5.QtGui import QPalette, QGuiApplication

    h = primary.hue()
    s = primary.saturation()
    v = primary.value()

    # 悬浮球背景: 主色 95% alpha
    float_bg = QColor(primary)
    float_bg.setAlpha(242)

    # 悬浮球文字: 根据明度选择白或深色
    if v > 128:
        float_text = QColor(255, 255, 255)
    else:
        float_text = QColor(30, 30, 30)

    # 悬浮球边框: 饱和度+20%, 明度-15%
    border_s = min(255, s + int(255 * 0.20))
    border_v = max(0, v - int(255 * 0.15))
    float_border = QColor.fromHsv(max(0, h), border_s, border_v)

    # 面板按钮背景: 主色10%混白
    pie_bg_normal = _blend(primary, QColor(255, 255, 255), 0.10)
    pie_bg_normal.setAlpha(240)

    # 面板按钮悬停: 主色 85% alpha
    pie_bg_hovered = QColor(primary)
    pie_bg_hovered.setAlpha(217)

    # 面板按钮文字: 同边框色
    pie_text_normal = QColor(float_border)

    # 面板按钮悬停文字: 白色
    pie_text_hovered = QColor(255, 255, 255)

    # 中心按钮常态背景: 主色10%混白 不透明
    center_bg_normal = _blend(primary, QColor(255, 255, 255), 0.10)

    # 中心按钮悬停背景: 主色 不透明
    center_bg_hovered = QColor(primary)
    center_bg_hovered.setAlpha(255)

    return {
        'float_bg': float_bg,
        'float_text': float_text,
        'float_border': float_border,
        'pie_bg_normal': pie_bg_normal,
        'pie_bg_hovered': pie_bg_hovered,
        'pie_text_normal': pie_text_normal,
        'pie_text_hovered': pie_text_hovered,
        'center_bg_normal': center_bg_normal,
        'center_bg_hovered': center_bg_hovered,
    }


def _blend(color: QColor, base: QColor, ratio: float) -> QColor:
    """将 color 按 ratio 混合到 base 上"""
    r = int(base.red() * (1 - ratio) + color.red() * ratio)
    g = int(base.green() * (1 - ratio) + color.green() * ratio)
    b = int(base.blue() * (1 - ratio) + color.blue() * ratio)
    return QColor(r, g, b)


def theme_from_hex(hex_color: str) -> dict:
    """从十六进制颜色字符串派生主题"""
    return derive_theme(QColor(hex_color))