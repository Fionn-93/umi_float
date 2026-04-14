"""
应用状态管理模块
"""
from typing import Optional


class AppState:
    """应用状态单例"""
    
    _instance: Optional['AppState'] = None
    
    def __init__(self):
        if AppState._instance is not None:
            return
        
        self._is_fullscreen = False
        self._float_ball_visible = True
        self._panel_visible = False
        AppState._instance = self
    
    @classmethod
    def get(cls) -> 'AppState':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def is_fullscreen(self) -> bool:
        """是否全屏"""
        return self._is_fullscreen
    
    @is_fullscreen.setter
    def is_fullscreen(self, value: bool) -> None:
        """设置全屏状态"""
        self._is_fullscreen = value
    
    @property
    def float_ball_visible(self) -> bool:
        """悬浮球是否可见"""
        return self._float_ball_visible
    
    @float_ball_visible.setter
    def float_ball_visible(self, value: bool) -> None:
        """设置悬浮球可见性"""
        self._float_ball_visible = value
    
    @property
    def panel_visible(self) -> bool:
        """面板是否可见"""
        return self._panel_visible
    
    @panel_visible.setter
    def panel_visible(self, value: bool) -> None:
        """设置面板可见性"""
        self._panel_visible = value


def get_state() -> AppState:
    """获取应用状态单例"""
    return AppState.get()
