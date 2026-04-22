"""
插件加载器 - 支持顺序管理、CRUD 操作
"""

import json
import shutil
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

from core.constants import (
    EXTENSIONS_DIR,
    PLUGIN_MANIFEST,
    PROJECT_EXTENSIONS_DIR,
    ICONS_DIR,
)
from core.config import get_config
from plugins.plugin_base import PluginConfig


class PluginLoader(QObject):
    """插件加载器"""

    plugins_loaded = pyqtSignal()
    plugin_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, PluginConfig] = {}
        self._plugin_paths: Dict[str, Path] = {}
        self._config = get_config()

    def load_all_plugins(self):
        """加载所有插件"""
        self._plugins.clear()
        self._plugin_paths.clear()

        self._load_plugins_from_dir(EXTENSIONS_DIR)
        self._load_plugins_from_dir(PROJECT_EXTENSIONS_DIR)

        self._migrate_plugin_order()

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
                        self._plugin_paths[plugin_id] = plugin_dir
                    except Exception as e:
                        print(f"加载插件失败 {plugin_dir}: {e}")

    def _load_manifest(self, manifest_file: Path) -> PluginConfig:
        """加载插件配置"""
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PluginConfig(data)

    def _migrate_plugin_order(self):
        """首次运行时迁移插件顺序"""
        cfg = self._config.get()
        has_enabled = "enabled_plugins" in cfg
        has_disabled = "disabled_plugins" in cfg

        if has_enabled and has_disabled:
            enabled = cfg.get("enabled_plugins", [])
            disabled = cfg.get("disabled_plugins", [])
            if enabled or disabled:
                return

        if not self._plugins:
            return

        enabled_list = []
        disabled_list = []

        for plugin_id, config in self._plugins.items():
            if config.enabled:
                enabled_list.append(plugin_id)
            else:
                disabled_list.append(plugin_id)

        self._config.update(
            enabled_plugins=enabled_list, disabled_plugins=disabled_list
        )

    def get_plugins(self) -> Dict[str, PluginConfig]:
        """获取所有插件"""
        return self._plugins

    def get_plugin_path(self, plugin_id: str) -> Optional[Path]:
        """获取插件目录路径"""
        return self._plugin_paths.get(plugin_id)

    def is_project_plugin(self, plugin_id: str) -> bool:
        """判断是否为项目自带插件"""
        path = self._plugin_paths.get(plugin_id)
        if path is None:
            return False
        try:
            path.resolve().relative_to(PROJECT_EXTENSIONS_DIR.resolve())
            return True
        except ValueError:
            return False

    def get_ordered_plugins(
        self,
    ) -> Tuple[List[Tuple[str, PluginConfig]], List[Tuple[str, PluginConfig]]]:
        """获取有序的插件列表，返回 (已启用列表, 已禁用列表)"""
        cfg = self._config.get()
        enabled_order = cfg.get("enabled_plugins", [])
        disabled_order = cfg.get("disabled_plugins", [])

        enabled_list = []
        for plugin_id in enabled_order:
            if plugin_id in self._plugins:
                config = self._get_effective_config(plugin_id)
                enabled_list.append((plugin_id, config))

        disabled_list = []
        for plugin_id in disabled_order:
            if plugin_id in self._plugins:
                config = self._get_effective_config(plugin_id)
                disabled_list.append((plugin_id, config))

        for plugin_id, config in self._plugins.items():
            if plugin_id not in enabled_order and plugin_id not in disabled_order:
                effective_config = self._get_effective_config(plugin_id)
                disabled_list.append((plugin_id, effective_config))

        return enabled_list, disabled_list

    def _get_effective_config(self, plugin_id: str) -> PluginConfig:
        """获取插件的有效配置（应用覆盖）"""
        base_config = self._plugins.get(plugin_id)
        if base_config is None:
            return None

        cfg = self._config.get()
        overrides = cfg.get("plugin_overrides", {}).get(plugin_id, {})

        effective_data = dict(base_config.data)
        effective_data.update(overrides)

        return PluginConfig(effective_data)

    def enable_plugin(self, plugin_id: str, index: int = -1):
        """启用插件"""
        if plugin_id not in self._plugins:
            return

        cfg = self._config.get()
        enabled = list(cfg.get("enabled_plugins", []))
        disabled = list(cfg.get("disabled_plugins", []))

        if plugin_id in enabled:
            return

        if plugin_id in disabled:
            disabled.remove(plugin_id)

        if index < 0 or index >= len(enabled):
            enabled.append(plugin_id)
        else:
            enabled.insert(index, plugin_id)

        self._config.update(enabled_plugins=enabled, disabled_plugins=disabled)
        self.plugin_changed.emit(plugin_id)

    def disable_plugin(self, plugin_id: str):
        """禁用插件"""
        if plugin_id not in self._plugins:
            return

        cfg = self._config.get()
        enabled = list(cfg.get("enabled_plugins", []))
        disabled = list(cfg.get("disabled_plugins", []))

        if plugin_id not in enabled:
            return

        enabled.remove(plugin_id)
        disabled.append(plugin_id)

        self._config.update(enabled_plugins=enabled, disabled_plugins=disabled)
        self.plugin_changed.emit(plugin_id)

    def move_plugin(self, plugin_id: str, new_index: int, group: str):
        """移动插件位置"""
        cfg = self._config.get()

        if group == "enabled":
            enabled = list(cfg.get("enabled_plugins", []))
            if plugin_id not in enabled:
                return
            enabled.remove(plugin_id)
            new_index = max(0, min(new_index, len(enabled)))
            enabled.insert(new_index, plugin_id)
            self._config.update(enabled_plugins=enabled)
        elif group == "disabled":
            disabled = list(cfg.get("disabled_plugins", []))
            if plugin_id not in disabled:
                return
            disabled.remove(plugin_id)
            new_index = max(0, min(new_index, len(disabled)))
            disabled.insert(new_index, plugin_id)
            self._config.update(disabled_plugins=disabled)

        self.plugin_changed.emit(plugin_id)

    def update_plugin_override(self, plugin_id: str, fields: dict):
        """更新插件覆盖字段"""
        if plugin_id not in self._plugins:
            return

        cfg = self._config.get()
        overrides = dict(cfg.get("plugin_overrides", {}))

        if plugin_id not in overrides:
            overrides[plugin_id] = {}

        overrides[plugin_id].update(fields)

        self._config.update(plugin_overrides=overrides)
        self.plugin_changed.emit(plugin_id)

    def create_plugin(
        self, name: str, description: str, icon: str, exec_cmd: str
    ) -> str:
        """创建新插件，返回 plugin_id"""
        plugin_id = str(uuid.uuid4())
        plugin_dir = EXTENSIONS_DIR / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "name": name,
            "description": description,
            "icon": icon,
            "exec": exec_cmd,
            "type": "command",
            "enabled": True,
        }

        manifest_file = plugin_dir / PLUGIN_MANIFEST
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)

        config = PluginConfig(manifest_data)
        self._plugins[plugin_id] = config
        self._plugin_paths[plugin_id] = plugin_dir

        cfg = self._config.get()
        enabled = list(cfg.get("enabled_plugins", []))
        enabled.append(plugin_id)
        self._config.update(enabled_plugins=enabled)

        self.plugin_changed.emit(plugin_id)
        return plugin_id

    def delete_plugin(self, plugin_id: str) -> bool:
        """删除插件"""
        if plugin_id not in self._plugins:
            return False

        plugin_path = self._plugin_paths.get(plugin_id)
        if plugin_path and plugin_path.exists():
            try:
                shutil.rmtree(plugin_path)
            except Exception as e:
                print(f"删除插件目录失败: {e}")
                return False

        del self._plugins[plugin_id]
        del self._plugin_paths[plugin_id]

        cfg = self._config.get()
        enabled = list(cfg.get("enabled_plugins", []))
        disabled = list(cfg.get("disabled_plugins", []))
        overrides = dict(cfg.get("plugin_overrides", {}))

        if plugin_id in enabled:
            enabled.remove(plugin_id)
        if plugin_id in disabled:
            disabled.remove(plugin_id)
        if plugin_id in overrides:
            del overrides[plugin_id]

        self._config.update(
            enabled_plugins=enabled,
            disabled_plugins=disabled,
            plugin_overrides=overrides,
        )

        self.plugin_changed.emit(plugin_id)
        return True

    def execute_plugin(self, plugin_id: str):
        """执行插件（非阻塞）"""
        if plugin_id not in self._plugins:
            print(f"插件不存在: {plugin_id}")
            return

        config = self._get_effective_config(plugin_id)
        try:
            subprocess.Popen(
                config.exec,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"执行插件: {config.name}")
        except Exception as e:
            print(f"执行插件失败: {e}")

    def save_custom_icon(self, source_path: str) -> str:
        """保存自定义图标，返回相对路径"""
        source = Path(source_path)
        if not source.exists():
            return ""

        icon_id = str(uuid.uuid4())
        ext = source.suffix or ".png"
        dest = ICONS_DIR / f"{icon_id}{ext}"

        shutil.copy2(source, dest)

        return f"icons/{icon_id}{ext}"
