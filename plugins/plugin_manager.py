"""
插件管理器
"""
from typing import Dict, List, Optional
from plugins.plugin_loader import PluginLoader
from plugins.plugin_base import PluginConfig


class PluginManager:
    """插件管理器单例"""
    
    _instance: Optional['PluginManager'] = None
    
    def __init__(self):
        if PluginManager._instance is not None:
            return
        
        self.loader = None
        PluginManager._instance = self
    
    @classmethod
    def get(cls) -> 'PluginManager':
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self):
        """初始化插件加载器"""
        if self.loader is None:
            self.loader = PluginLoader()
            self.loader.load_all_plugins()
    
    def get_plugins(self) -> Dict[str, PluginConfig]:
        """获取所有插件"""
        if self.loader is None:
            self.initialize()
        return self.loader.get_plugins()
    
    def get_enabled_plugins(self) -> List[PluginConfig]:
        """获取已启用的插件"""
        return [p for p in self.get_plugins().values() if p.enabled]
    
    def execute_plugin(self, plugin_id: str):
        """执行插件"""
        if self.loader is None:
            self.initialize()
        self.loader.execute_plugin(plugin_id)
    
    def enable_plugin(self, plugin_id: str):
        """启用插件"""
        pass
    
    def disable_plugin(self, plugin_id: str):
        """禁用插件"""
        pass
