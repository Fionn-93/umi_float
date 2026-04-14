# Umi-Float 桌面悬浮工具箱

## 项目简介

Umi-Float 是一个常驻桌面的轻量化入口，通过"悬浮球 + 抽屉式面板"的设计，整合系统常用功能与第三方扩展工具。

## 功能特性

### 核心功能
- **悬浮球**：圆形悬浮球，支持拖动、边缘吸附、透明度调节
- **抽屉式面板**：鼠标悬停或点击展开的抽屉式面板
- **系统托盘**：集成系统托盘，支持显示/隐藏、偏好设置、退出
- **插件系统**：支持热加载的插件扩展机制

### 内置组件
- **数字时钟**：精确到秒的时钟，点击可弹出日历
- **天气预报**：支持和风天气 API

### 扩展机制
- **动态加载**：通过 QFileSystemWatcher 监听插件目录，无需重启应用
- **JSON 配置**：简单的 JSON 格式插件配置文件
- **示例插件**：包含截图工具示例（调用 Deepin 系统截图）

## 技术栈

- **语言**：Python 3.12
- **GUI框架**：PyQt5 (Qt 5.15)
- **配置管理**：JSON + 手动验证
- **插件系统**：QFileSystemWatcher + subprocess
- **系统集成**：DBus

## 项目结构

```
umi_float/
├── main.py                 # 应用入口
├── core/                   # 核心模块
│   ├── constants.py        # 常量定义
│   ├── config.py           # 配置管理
│   └── state.py            # 应用状态
├── ui/                     # UI模块
│   ├── float_widget.py     # 悬浮球窗口
│   ├── tray_icon.py        # 系统托盘
│   └── components/         # UI组件
│       └── clock_widget.py # 时钟组件
├── plugins/                # 插件系统
│   ├── plugin_base.py      # 插件基类
│   ├── plugin_loader.py    # 插件加载器
│   └── plugin_manager.py   # 插件管理器
├── widgets/                # 基础组件
│   ├── float_button.py     # 悬浮球按钮
│   ├── draggable_widget.py # 可拖动窗口
│   └── edge_snapper.py     # 边缘吸附
├── utils/                  # 工具模块
│   ├── system_info.py      # 系统信息
│   └── autostart.py        # 开机自启
├── extensions/             # 插件目录
│   └── screenshot/         # 截图插件示例
│       └── manifest.json
└── requirements.txt        # 依赖列表
```

## 快速开始

### 依赖安装

```bash
# 安装系统依赖
sudo apt install python3-venv python3-pip

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行项目

```bash
# 方法1：直接运行
python3 main.py

# 方法2：使用 PYTHONPATH
PYTHONPATH=/path/to/umi_float:$PYTHONPATH python3 main.py
```

## 插件开发

### 插件配置格式

在 `extensions/your_plugin/` 目录下创建 `manifest.json`：

```json
{
  "name": "插件名称",
  "description": "插件描述",
  "icon": "icon_name",
  "exec": "command_to_execute",
  "type": "command",
  "enabled": true
}
```

### 插件类型

- **command**：点击时执行命令
- **content**：持续显示内容的插件（待实现）

### 示例插件

查看 `extensions/screenshot/manifest.json` 获取完整示例。

## 配置说明

配置文件位于：`~/.config/umi-float/config.json`

```json
{
  "opacity": 0.9,
  "float_ball_size": 56,
  "auto_start": false,
  "show_on_fullscreen": false,
  "weather_api_key": "",
  "weather_location": "101010100",
  "position": {"x": 100, "y": 100}
}
```

### 配置项说明

- `opacity`: 悬浮球透明度 (0.1-1.0)
- `float_ball_size`: 悬浮球大小 (32-128)
- `auto_start`: 是否开机自启
- `show_on_fullscreen`: 全屏时是否显示
- `weather_api_key`: 和风天气 API Key
- `weather_location`: 天气查询位置（城市ID）
- `position`: 悬浮球位置

## 已知问题

1. **系统托盘图标**：当前缺少托盘图标，需要添加图标文件
2. **全屏检测**：全屏检测功能待完善
3. **热加载**：插件热加载功能待测试

## 开发计划

### MVP 版本 (v0.1.0) - 当前版本
- [x] 悬浮球 + 拖动 + 吸附
- [x] 系统托盘集成
- [x] 配置管理
- [x] 插件系统基础
- [x] 示例插件

### v0.2.0 计划
- [ ] 待办事项组件
- [ ] 天气组件
- [ ] 抽屉式面板
- [ ] 偏好设置界面

### v0.3.0 计划
- [ ] 全屏检测 + 避让
- [ ] 开机自启
- [ ] 插件热加载完善
- [ ] 更多内置组件

## 注意事项

1. **Deepin 环境优化**：项目在 Deepin 25 上测试，使用 Deepin 特有的 DBus 服务
2. **Python 版本**：推荐使用 Python 3.12+
3. **依赖问题**：由于系统限制，直接使用系统 Python 安装依赖可能受限

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
