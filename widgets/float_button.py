"""
悬浮球按钮组件
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QColor, QFont

from core.config import get_config
from utils.theme_colors import theme_from_hex


class FloatButton(QLabel):
    """圆形悬浮球按钮"""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        self._apply_theme()
        
        # 设置时钟
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()
    
    def _apply_theme(self):
        """从配置应用主题色"""
        config = get_config()
        theme_color = config.get().get('theme_color', '#6495ED')
        colors = theme_from_hex(theme_color)
        self.THEME_BG = colors['float_bg']
        self.THEME_TEXT = colors['float_text']
        self.THEME_BORDER = colors['float_border']
        self._update_style()
    
    def _update_style(self):
        """使用自定义主题色更新样式"""
        font_size = self.size // 3
        radius = self.size // 2
        
        # 设置样式
        self.setStyleSheet(f"""
            background-color: rgba({self.THEME_BG.red()}, {self.THEME_BG.green()}, {self.THEME_BG.blue()}, {self.THEME_BG.alpha()});
            color: rgb({self.THEME_TEXT.red()}, {self.THEME_TEXT.green()}, {self.THEME_TEXT.blue()});
            border: 2px solid rgb({self.THEME_BORDER.red()}, {self.THEME_BORDER.green()}, {self.THEME_BORDER.blue()});
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: bold;
        """)
    
    def refresh_theme(self):
        """刷新主题色（配置变更后调用）"""
        self._apply_theme()
        self.update()
    
    def set_size(self, size: int):
        """更新悬浮球大小"""
        self.size = size
        self.setFixedSize(size, size)
        self._update_style()
        self.update()
    
    def update_time(self):
        """更新时间显示"""
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)
