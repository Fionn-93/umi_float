"""
插件加载器 - 支持顺序管理、CRUD 操作
"""

import json
import logging
import shutil
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

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

    def resolve_icon(self, icon_name: str, plugin_id: str = None) -> Optional[QIcon]:
        """解析图标名称，返回 QIcon 或 None（fallback 到调用方处理）"""
        from PyQt5.QtGui import QIcon

        if not icon_name.startswith("icons/"):
            return None
        if plugin_id and plugin_id in self._plugin_paths:
            plugin_icon = self._plugin_paths[plugin_id] / icon_name
            if plugin_icon.exists():
                return QIcon(str(plugin_icon))
        global_icon = ICONS_DIR / icon_name
        if global_icon.exists():
            return QIcon(str(global_icon))
        return None

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
        self,
        name: str,
        description: str,
        icon: str,
        exec_cmd: str,
        plugin_type: str = "command",
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
            "type": plugin_type,
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

    def install_plugin(self, zip_path: str) -> Tuple[bool, str, str]:
        """安装 widget 插件包，返回 (成功, 消息, plugin_id)"""
        import zipfile

        zip_file = Path(zip_path)
        if not zip_file.exists():
            return False, "文件不存在", ""

        try:
            with zipfile.ZipFile(zip_file, "r") as z:
                if "manifest.json" not in z.namelist():
                    return False, "不是有效的插件包：缺少 manifest.json", ""
                manifest_data = json.loads(z.read("manifest.json").decode("utf-8"))
            plugin_type = manifest_data.get("type", "command")
            if plugin_type != "widget":
                return False, "只有 widget 类型插件支持导入安装", ""
            plugin_id = str(uuid.uuid4())
            plugin_dir = EXTENSIONS_DIR / plugin_id
            plugin_dir.mkdir(parents=True, exist_ok=True)
            data_dir = plugin_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_file, "r") as z:
                z.extractall(plugin_dir)
            config = PluginConfig(manifest_data)
            self._plugins[plugin_id] = config
            self._plugin_paths[plugin_id] = plugin_dir
            cfg = self._config.get()
            enabled = list(cfg.get("enabled_plugins", []))
            enabled.append(plugin_id)
            self._config.update(enabled_plugins=enabled)
            self.plugin_changed.emit(plugin_id)
            return True, "安装成功", plugin_id
        except Exception as e:
            return False, f"安装失败: {e}", ""

    def get_plugin_data_dir(self, plugin_id: str) -> Optional[Path]:
        """获取插件数据目录"""
        plugin_path = self._plugin_paths.get(plugin_id)
        if plugin_path is None:
            return None
        data_dir = plugin_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def get_widget_class(self, plugin_id: str):
        """获取 widget 插件的 Widget 类"""
        plugin_path = self._plugin_paths.get(plugin_id)
        if plugin_path is None:
            logger.warning("get_widget_class: plugin_path 不存在, plugin_id=%s", plugin_id)
            return None
        config = self._get_effective_config(plugin_id)
        if config is None:
            logger.warning("get_widget_class: effective_config 为 None, plugin_id=%s", plugin_id)
            return None
        if config.type != "widget":
            logger.warning("get_widget_class: 类型不是 widget, plugin_id=%s, type=%s", plugin_id, config.type)
            return None
        exec_name = config.exec
        init_file = plugin_path / exec_name
        if not init_file.exists():
            logger.warning("get_widget_class: init_file 不存在, plugin_id=%s, path=%s", plugin_id, init_file)
            return None
        if init_file.is_dir():
            init_file = init_file / "__init__.py"
            if not init_file.exists():
                logger.warning("get_widget_class: __init__.py 不存在, plugin_id=%s, path=%s", plugin_id, init_file)
                return None
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                f"w_{plugin_id}", str(init_file)
            )
            if spec is None or spec.loader is None:
                logger.warning("get_widget_class: spec 或 loader 为 None, plugin_id=%s", plugin_id)
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            entry_func = getattr(module, config.entry, None)
            if entry_func is None:
                logger.warning("get_widget_class: entry func 不存在, plugin_id=%s, entry=%s", plugin_id, config.entry)
                return None
            logger.info("get_widget_class: 成功加载 widget, plugin_id=%s", plugin_id)
            return entry_func
        except Exception as e:
            logger.error("get_widget_class: 加载异常, plugin_id=%s, error=%s", plugin_id, e)
            return None

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
        """执行插件（非阻塞），返回 (类型, command_exec 或 widget_class)"""
        if plugin_id not in self._plugins:
            print(f"插件不存在: {plugin_id}")
            return ("none", None)

        config = self._get_effective_config(plugin_id)
        if config.type == "widget":
            return ("widget", plugin_id)
        try:
            if config.type == "python":
                self._execute_python_plugin(plugin_id, config)
            else:
                subprocess.Popen(
                    config.exec,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"执行插件: {config.name}")
            return ("command", config.exec)
        except Exception as e:
            print(f"执行插件失败: {e}")
            return ("none", None)

    def _execute_python_plugin(self, plugin_id: str, config):
        """执行 Python 类型插件（进程内）"""
        plugin_path = self._plugin_paths.get(plugin_id)
        if plugin_path is None:
            print(f"插件路径不存在: {plugin_id}")
            return

        script_file = plugin_path / f"{config.exec}.py"
        if not script_file.exists():
            print(f"插件脚本不存在: {script_file}")
            return

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                f"ext_{plugin_id}", str(script_file)
            )
            if spec is None or spec.loader is None:
                print(f"无法加载插件模块: {script_file}")
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "run"):
                print(f"插件缺少 run() 函数: {script_file}")
                return
            from PyQt5.QtWidgets import QApplication

            app = QApplication.instance()
            module.run({"app": app})
            print(f"执行 Python 插件: {config.name}")
        except Exception as e:
            print(f"执行 Python 插件失败: {e}")

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
