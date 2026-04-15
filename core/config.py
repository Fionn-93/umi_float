"""
配置管理模块 (简化版，不依赖 pydantic)
"""
import copy
import json
from pathlib import Path
from typing import Any, Dict

from core.constants import CONFIG_DIR, DEFAULT_CONFIG


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config_file = CONFIG_DIR / "config.json"
    
    def __init__(self):
        self._config = None
        
        if ConfigManager._instance is not None:
            return
        
        ConfigManager._instance = self
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = self._validate_config(data)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
        return self._config
    
    def _validate_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置"""
        config = copy.deepcopy(DEFAULT_CONFIG)
        
        if 'opacity' in data and isinstance(data['opacity'], (int, float)):
            config['opacity'] = max(0.1, min(1.0, float(data['opacity'])))
        
        if 'float_ball_size' in data and isinstance(data['float_ball_size'], int):
            config['float_ball_size'] = max(32, min(128, data['float_ball_size']))
        
        if 'theme_color' in data and isinstance(data['theme_color'], str):
            try:
                from PyQt5.QtGui import QColor
                c = QColor(data['theme_color'])
                if c.isValid():
                    config['theme_color'] = data['theme_color']
            except Exception:
                pass
        
        if 'pie_button_size' in data and isinstance(data['pie_button_size'], int):
            config['pie_button_size'] = max(32, min(100, data['pie_button_size']))
        
        if 'pie_spacing' in data and isinstance(data['pie_spacing'], int):
            config['pie_spacing'] = max(0, min(30, data['pie_spacing']))
        
        if 'auto_start' in data and isinstance(data['auto_start'], bool):
            config['auto_start'] = data['auto_start']
        
        if 'show_on_fullscreen' in data and isinstance(data['show_on_fullscreen'], bool):
            config['show_on_fullscreen'] = data['show_on_fullscreen']
        
        if 'weather_api_key' in data and isinstance(data['weather_api_key'], str):
            config['weather_api_key'] = data['weather_api_key']
        
        if 'weather_location' in data and isinstance(data['weather_location'], str):
            config['weather_location'] = data['weather_location']
        
        if 'position' in data and isinstance(data['position'], dict):
            pos = data['position']
            if isinstance(pos.get('x'), int) and isinstance(pos.get('y'), int):
                config['position'] = {'x': max(0, pos['x']), 'y': max(0, pos['y'])}
        
        return config
    
    def save(self) -> None:
        """保存配置"""
        if self._config is None:
            return
        
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def get(self) -> Dict[str, Any]:
        """获取配置"""
        if self._config is None:
            self.load()
        return self._config
    
    def update(self, **kwargs) -> None:
        """更新配置"""
        config = self.get()
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
        self._config = self._validate_config(config)
        self.save()
    
    def __getitem__(self, key):
        """获取配置项"""
        return self.get()[key]
    
    def __setitem__(self, key, value):
        """设置配置项"""
        self.update(**{key: value})


def get_config() -> ConfigManager:
    """获取配置管理器单例"""
    if ConfigManager._instance is None:
        ConfigManager()
    return ConfigManager._instance
