"""
悬浮球按钮组件
"""
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QPalette, QBrush, QColor, QFont


class FloatButton(QLabel):
    """圆形悬浮球按钮"""
    
    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        # 初始化样式
        self._update_theme()
        
        # 设置时钟
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()
    
    def _update_theme(self):
        """根据系统主题更新样式"""
        app = QApplication.instance()
        if app is None:
            return
        
        palette = app.palette()
        bg_color = palette.color(QPalette.Window)
        is_dark = bg_color.lightness() <= 128
        
        font_size = self.size // 3
        radius = self.size // 2
        
        if is_dark:
            theme_bg = QColor(28, 28, 28, 242)  # #1C1C1C with 95% opacity
            theme_text = QColor(135, 206, 250)  # #87CEFA
        else:
            theme_bg = QColor(255, 255, 255, 242)  # #FFFFFF with 95% opacity
            theme_text = QColor(74, 144, 226)  # #4A90E2
        
        # 设置调色板
        new_palette = self.palette()
        new_palette.setColor(QPalette.Window, theme_bg)
        new_palette.setColor(QPalette.WindowText, theme_text)
        new_palette.setColor(QPalette.Button, theme_bg)
        new_palette.setColor(QPalette.ButtonText, theme_text)
        new_palette.setColor(QPalette.Base, theme_bg)
        new_palette.setColor(QPalette.Text, theme_text)
        self.setPalette(new_palette)
        
        # 设置样式
        self.setStyleSheet(f"""
            background-color: {theme_bg.name()};
            color: {theme_text.name()};
            border: 2px solid #4A90E2;
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: bold;
        """)
    
    def update_time(self):
        """更新时间显示"""
        current_time = QTime.currentTime().toString("HH:mm")
        self.setText(current_time)
