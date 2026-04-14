"""
插件基类 (简化版)
"""
from abc import ABC, abstractmethod
from typing import Optional


class PluginConfig:
    """插件配置"""
    
    def __init__(self, data: dict):
        self.data = data
    
    @property
    def name(self) -> str:
        return self.data.get('name', '')
    
    @property
    def icon(self) -> str:
        return self.data.get('icon', '')
    
    @property
    def exec(self) -> str:
        return self.data.get('exec', '')
    
    @property
    def type(self) -> str:
        return self.data.get('type', 'command')
    
    @property
    def enabled(self) -> bool:
        return self.data.get('enabled', True)


class Plugin(ABC):
    """插件基类"""
    
    def __init__(self, config: PluginConfig):
        self.config = config
    
    @abstractmethod
    def execute(self):
        """执行插件"""
        pass
    
    @property
    def name(self) -> str:
        """插件名称"""
        return self.config.name
    
    @property
    def icon(self) -> str:
        """插件图标"""
        return self.config.icon
    
    @property
    def is_enabled(self) -> bool:
        """是否启用"""
        return self.config.enabled
    
    def enable(self):
        """启用插件"""
        self.config.data['enabled'] = True
    
    def disable(self):
        """禁用插件"""
        self.config.data['enabled'] = False
