"""
插件管理器
"""

from typing import Dict, List, Optional, Tuple
from plugins.plugin_loader import PluginLoader
from plugins.plugin_base import PluginConfig


class PluginManager:
    """插件管理器单例"""

    _instance: Optional["PluginManager"] = None

    def __init__(self):
        if PluginManager._instance is not None:
            return

        self.loader = None
        PluginManager._instance = self

    @classmethod
    def get(cls) -> "PluginManager":
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

    def get_ordered_plugins(
        self,
    ) -> Tuple[List[Tuple[str, PluginConfig]], List[Tuple[str, PluginConfig]]]:
        """获取有序的插件列表，返回 (已启用列表, 已禁用列表)"""
        if self.loader is None:
            self.initialize()
        return self.loader.get_ordered_plugins()

    def get_enabled_plugins(self) -> List[PluginConfig]:
        """获取已启用的插件"""
        enabled, _ = self.get_ordered_plugins()
        return [config for _, config in enabled]

    def execute_plugin(self, plugin_id: str):
        """执行插件"""
        if self.loader is None:
            self.initialize()
        self.loader.execute_plugin(plugin_id)

    def enable_plugin(self, plugin_id: str, index: int = -1):
        """启用插件"""
        if self.loader is None:
            self.initialize()
        self.loader.enable_plugin(plugin_id, index)

    def disable_plugin(self, plugin_id: str):
        """禁用插件"""
        if self.loader is None:
            self.initialize()
        self.loader.disable_plugin(plugin_id)

    def move_plugin(self, plugin_id: str, new_index: int, group: str):
        """移动插件位置"""
        if self.loader is None:
            self.initialize()
        self.loader.move_plugin(plugin_id, new_index, group)

    def update_plugin_override(self, plugin_id: str, fields: dict):
        """更新插件覆盖字段"""
        if self.loader is None:
            self.initialize()
        self.loader.update_plugin_override(plugin_id, fields)

    def create_plugin(
        self, name: str, description: str, icon: str, exec_cmd: str
    ) -> str:
        """创建新插件，返回 plugin_id"""
        if self.loader is None:
            self.initialize()
        return self.loader.create_plugin(name, description, icon, exec_cmd)

    def delete_plugin(self, plugin_id: str) -> bool:
        """删除插件"""
        if self.loader is None:
            self.initialize()
        return self.loader.delete_plugin(plugin_id)

    def is_project_plugin(self, plugin_id: str) -> bool:
        """判断是否为项目自带插件"""
        if self.loader is None:
            self.initialize()
        return self.loader.is_project_plugin(plugin_id)

    def save_custom_icon(self, source_path: str) -> str:
        """保存自定义图标，返回相对路径"""
        if self.loader is None:
            self.initialize()
        return self.loader.save_custom_icon(source_path)

    def reload_plugins(self):
        """重新加载所有插件"""
        if self.loader is None:
            self.initialize()
        else:
            self.loader.load_all_plugins()
