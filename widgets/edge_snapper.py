"""
边缘吸附组件
"""
from PyQt5.QtCore import QPoint, QRect


class EdgeSnapper:
    """边缘吸附工具"""
    
    def __init__(self, snap_threshold: int = 20):
        self.snap_threshold = snap_threshold
    
    def calculate_snap_position(self, widget_pos: QPoint, widget_size: tuple, screen_rect: QRect) -> QPoint:
        """
        计算吸附位置
        
        Args:
            widget_pos: 窗口当前位置
            widget_size: 窗口尺寸 (width, height)
            screen_rect: 屏幕几何
            
        Returns:
            吸附后的位置
        """
        x, y = widget_pos.x(), widget_pos.y()
        width, height = widget_size

        left = screen_rect.left()
        right = screen_rect.right()
        top = screen_rect.top()
        bottom = screen_rect.bottom()
        
        # 检查左边缘
        if abs(x - left) <= self.snap_threshold:
            x = left
        # 检查右边缘
        elif abs(x + width - right) <= self.snap_threshold:
            x = right - width
        
        # 检查上边缘
        if abs(y - top) <= self.snap_threshold:
            y = top
        # 检查下边缘
        elif abs(y + height - bottom) <= self.snap_threshold:
            y = bottom - height
        
        return QPoint(x, y)
