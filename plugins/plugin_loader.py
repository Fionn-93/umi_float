"""
插件加载器
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal

from core.constants import EXTENSIONS_DIR, PLUGIN_MANIFEST, PROJECT_EXTENSIONS_DIR
from plugins.plugin_base import Plugin, PluginConfig


class PluginLoader(QObject):
    """插件加载器"""
    
    plugins_loaded = pyqtSignal()
    plugin_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, PluginConfig] = {}
    
    def load_all_plugins(self):
        """加载所有插件"""
        self._plugins.clear()
        
        self._load_plugins_from_dir(EXTENSIONS_DIR)
        self._load_plugins_from_dir(PROJECT_EXTENSIONS_DIR)
    
    def _load_plugins_from_dir(self, dir_path: Path):
        """从目录加载插件"""
        if not dir_path.exists():
            return
        
        for plugin_dir in dir_path.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / PLUGIN_MANIFEST
                if manifest_file.exists():
                    try:
                        config = self._load_manifest(manifest_file)
                        plugin_id = str(plugin_dir.name)
                        self._plugins[plugin_id] = config
                        print(f"加载插件: {config.name}")
                    except Exception as e:
                        print(f"加载插件失败 {plugin_dir}: {e}")
    
    def _load_manifest(self, manifest_file: Path) -> PluginConfig:
        """加载插件配置"""
        with open(manifest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return PluginConfig(data)
    
    def get_plugins(self) -> Dict[str, PluginConfig]:
        """获取所有插件"""
        return self._plugins
    
    def execute_plugin(self, plugin_id: str):
        """执行插件"""
        if plugin_id not in self._plugins:
            print(f"插件不存在: {plugin_id}")
            return
        
        config = self._plugins[plugin_id]
        try:
            subprocess.run(config.exec, shell=True, check=True)
            print(f"执行插件: {config.name}")
        except subprocess.CalledProcessError as e:
            print(f"执行插件失败: {e}")
