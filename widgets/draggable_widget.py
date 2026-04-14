"""
可拖动窗口组件
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint


class DraggableWidget(QWidget):
    """可拖动的窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_position = QPoint()
        self._drag_callback = None
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._dragging and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPos() - self._drag_position
            self.move(new_pos)
            event.accept()
            
            if self._drag_callback:
                self._drag_callback(new_pos)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def set_drag_callback(self, callback):
        """设置拖动回调函数"""
        self._drag_callback = callback
