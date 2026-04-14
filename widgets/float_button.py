"""
悬浮球按钮组件
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QColor, QFont


class FloatButton(QLabel):
    """圆形悬浮球按钮"""
    
    # 自定义主题色 - 清新蓝色系
    THEME_BG = QColor(100, 149, 237, 242)  # 矢车菊蓝，95%透明度
    THEME_TEXT = QColor(255, 255, 255)  # 白色文字
    THEME_BORDER = QColor(70, 130, 180)  # 钢青色边框
    
    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        # 初始化样式
        self._update_style()
        
        # 设置时钟
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()
    
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
    
    def update_time(self):
        """更新时间显示"""
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)
