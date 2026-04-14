"""
抽屉式面板
"""
from functools import partial

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class DrawerPanel(QFrame):
    """抽屉式面板"""
    
    plugin_executed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_window()
        self._setup_ui()
        
        self._plugins = {}
    
    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(300, 400)
        
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #4A90E2;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                color: #333;
            }
        """)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        title_label = QLabel("插件列表")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(5)
        
        self.plugins_layout = QVBoxLayout()
        self.plugins_layout.setSpacing(5)
        layout.addLayout(self.plugins_layout)
        
        layout.addStretch()
        
        settings_btn = QPushButton("设置")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #357ABD;
            }
        """)
        settings_btn.clicked.connect(lambda: print("设置功能待实现"))
        layout.addWidget(settings_btn)
        
        self.setLayout(layout)
    
    def set_plugins(self, plugins):
        """设置插件列表"""
        self._plugins = plugins
        self._refresh_plugins_ui()
    
    def _refresh_plugins_ui(self):
        """刷新插件列表UI"""
        for i in reversed(range(self.plugins_layout.count())):
            item = self.plugins_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        for plugin_id, plugin_config in self._plugins.items():
            btn = QPushButton(plugin_config.name)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.8);
                    border: 1px solid #ddd;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: rgba(74, 144, 226, 0.1);
                    border-color: #4A90E2;
                }
            """)
            btn.clicked.connect(partial(self.plugin_executed.emit, plugin_id))
            self.plugins_layout.addWidget(btn)
    
    def show_panel(self, parent_widget):
        """显示面板"""
        parent_pos = parent_widget.pos()
        parent_size = parent_widget.size()
        
        panel_x = parent_pos.x() + parent_size.width() + 5
        screen = parent_widget.screen()
        screen_rect = screen.availableGeometry()
        
        if panel_x + self.width() > screen_rect.right():
            panel_x = parent_pos.x() - self.width() - 5
        
        panel_y = parent_pos.y()
        if panel_y + self.height() > screen_rect.bottom():
            panel_y = screen_rect.bottom() - self.height()
        
        self.move(panel_x, panel_y)
        self.show()
    
    def hide_panel(self):
        """隐藏面板"""
        self.hide()
