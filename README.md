# Umi-Float 桌面悬浮工具箱

## 项目简介

Umi-Float 是一个常驻桌面的轻量化入口，通过"悬浮球 + 抽屉式面板"的设计，整合系统常用功能与第三方扩展工具。

## 功能特性

### 核心功能
- **悬浮球**：圆形悬浮球，支持拖动、边缘吸附、透明度调节、主题色自定义
- **显示模式**：支持时钟、性能监控、天气三种显示模式
- **抽屉式面板**：点击展开的环形面板，支持插件快捷访问
- **系统托盘**：集成系统托盘，支持显示/隐藏、偏好设置、退出
- **设置界面**：现代圆角卡片风格偏好设置，无边框窗口，支持实时预览

### 扩展管理
- **拖拽排序**：支持拖拽调整扩展顺序
- **启用/禁用**：支持扩展的启用和禁用切换
- **新建扩展**：支持创建新的扩展，自动生成 UUID 目录
- **编辑扩展**：支持编辑扩展名称、描述、图标、执行命令
- **删除扩展**：支持删除扩展（带确认对话框）
- **图标选择器**：提供预设图标库，支持本地图片上传

### 内置扩展
- **计算器**：打开 Deepin 计算器
- **文件管理器**：打开文件管理器
- **设置**：打开系统设置
- **日历**：打开日历应用
- **截图**：调用 Deepin 截图工具

## 技术栈

- **语言**：Python 3.12
- **GUI框架**：PyQt5 (Qt 5.15)
- **配置管理**：JSON + 手动验证
- **插件系统**：动态加载 + subprocess
- **系统集成**：DBus

## 项目结构

```
umi_float/
├── main.py                    # 应用入口
├── core/                      # 核心模块
│   ├── constants.py           # 常量定义
│   ├── config.py              # 配置管理
│   └── state.py               # 应用状态
├── ui/                        # UI模块
│   ├── float_widget.py        # 悬浮球窗口
│   ├── pie_panel.py           # 环形面板
│   ├── settings_dialog.py     # 设置对话框
│   ├── tray_icon.py           # 系统托盘
│   ├── icon_picker_dialog.py  # 图标选择器
│   └── plugin_edit_dialog.py  # 扩展编辑对话框
├── widgets/                   # 基础组件
│   ├── float_button.py        # 悬浮球按钮（支持三种模式）
│   ├── draggable_widget.py    # 可拖动窗口
│   ├── edge_snapper.py        # 边缘吸附
│   ├── plugin_list_item.py    # 扩展列表项（支持拖拽）
│   └── plugin_list_widget.py  # 扩展列表容器
├── plugins/                   # 插件系统
│   ├── plugin_base.py         # 插件基类
│   ├── plugin_loader.py       # 插件加载器
│   └── plugin_manager.py      # 插件管理器
├── utils/                     # 工具模块
│   ├── system_info.py         # 屏幕几何信息
│   ├── theme_colors.py        # 主题色生成
│   ├── memory_info.py         # 内存信息
│   └── weather_info.py        # 天气信息
├── extensions/                # 内置扩展目录
│   ├── calculator/
│   ├── file_manager/
│   ├── settings/
│   ├── calendar/
│   └── screenshot/
└── requirements.txt           # 依赖列表
```

## 快速开始

### 依赖安装

```bash
# 安装系统依赖
sudo apt install python3-venv python3-pip

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行项目

```bash
PYTHONPATH=/path/to/umi_float:$PYTHONPATH python3 main.py
```

## 扩展开发

### 扩展配置格式

在 `~/.local/share/umi-float/extensions/your_plugin/` 目录下创建 `manifest.json`：

```json
{
  "name": "扩展名称",
  "description": "扩展描述",
  "icon": "icon_name",
  "exec": "command_to_execute",
  "type": "command",
  "enabled": true
}
```

### 图标说明

- **系统图标**：使用系统图标主题名称（如 `accessories-calculator`）
- **自定义图标**：上传本地图片，自动保存到 `~/.local/share/umi-float/icons/`

## 配置说明

配置文件位于：`~/.config/umi-float/config.json`

```json
{
  "opacity": 0.9,
  "float_ball_size": 56,
  "theme": "deepin",
  "display_mode": "clock",
  "pie_button_size": 56,
  "pie_spacing": 10,
  "pie_expand_mode": "click",
  "auto_start": false,
  "show_on_fullscreen": false,
  "weather_api_host": "je693837aw.re.qweatherapi.com",
  "weather_api_key": "",
  "weather_location": "101010100",
  "position": {"x": 100, "y": 100},
  "plugin_overrides": {}
}
```

### 配置项说明

| 配置项 | 说明 | 范围/类型 |
|--------|------|-----------|
| `opacity` | 悬浮球透明度 | 0.1-1.0 |
| `float_ball_size` | 悬浮球大小 | 32-128 |
| `theme` | 主题预设 | deepin/macos/github/... |
| `display_mode` | 显示模式 | clock/performance/weather |
| `pie_button_size` | 扩展图标大小 | 32-100 |
| `pie_spacing` | 面板间距 | 0-30 |
| `pie_expand_mode` | 展开方式 | click/hover |
| `auto_start` | 开机自启 | boolean |
| `weather_api_host` | 和风天气 API 地址 | string |
| `weather_api_key` | 和风天气 API Key | string |
| `weather_location` | 天气查询位置 | 城市ID |
| `plugin_overrides` | 扩展覆盖配置 | object |

## 开发计划

### MVP 版本 (v0.1.0) - 当前版本
- [x] 悬浮球 + 拖动 + 吸附
- [x] 系统托盘集成
- [x] 配置管理
- [x] 插件系统基础
- [x] 设置界面（macOS 风格）
- [x] 悬浮球显示模式（时钟/内存/天气）
- [x] 扩展管理（拖拽排序、启用/禁用、新建/编辑/删除）
- [x] 图标选择器

### v0.2.0 计划
- [ ] 全屏检测 + 避让
- [ ] 开机自启
- [ ] 更多内置扩展
- [ ] 扩展市场/在线下载

## 注意事项

1. **Deepin 环境优化**：项目在 Deepin 25 上测试，使用 Deepin 特有的 DBus 服务
2. **Python 版本**：推荐使用 Python 3.12+
3. **天气功能**：需要配置和风天气 API Key

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
