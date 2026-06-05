# Umi-Float 桌面悬浮工具箱

## 项目简介

Umi-Float 是一款面向 Deepin / UOS Linux 桌面环境的轻量级悬浮工具箱。它以"悬浮球 + 抽屉式面板"为核心交互模式，将系统常用功能与第三方扩展工具整合到一个常驻桌面的圆形入口中，让用户随时触达所需功能，无需在任务栏或开始菜单中翻找。

## 功能特性

### 悬浮球

- 圆形悬浮球常驻桌面最上层，支持自由拖动与边缘自动吸附
- 三种显示模式：
  - **时钟模式** — 秒针进度环 + 数字时钟，100ms 刷新
  - **性能模式** — 内存占用进度环（绿/黄/红三档）+ 实时下行网速
  - **天气模式** — 当前温度 + 天气描述 + 动态图标，30 分钟自动刷新
- 滚轮上下滚动循环切换显示模式
- 贴边胶囊模式：拖至屏幕边缘自动缩为窄条，悬停展开
- 可调参数：尺寸（32–128px）、透明度（0.1–1.0）
- 位置自动记忆，下次启动恢复

### 环形面板

- 点击或悬停展开（可选触发方式）
- 展开动画：OutBack 缓动 + 波浪延迟（40ms/按钮）+ 缩放动画
- 收起动画：InQuad 缓动 + 反向延迟
- 中心返回按钮，可拖动面板调整浮球位置
- 柔和圆形阴影，热区自动裁剪

### 主题系统

- 10 种预设主题，每种主色自动派生 9 色调色板：

| 主题 | 颜色 |
|------|------|
| 薰衣草紫 `#7B61FF` | 珊瑚红 `#FF6B6B` |
| 夕阳橙 `#FF9F43` | 玫瑰粉 `#FF85A2` |
| 森林绿 `#4CAF50` | 抹茶绿 `#8BC34A` |
| 蔚蓝 `#4FC3F7` | 靛蓝 `#5C6BC0` |
| 珍珠白 `#F5F5F7` | 乌木黑 `#2C2C2E` |

- 切换后悬浮球、面板、设置中心、所有弹窗实时刷新

### 设置中心

- 现代圆角卡片风格，无边框窗口，可拖动
- 三大页面：
  - **个性化** — 主题选择、浮球显示模式/大小、面板展开方式/图标大小/间距
  - **天气** — API 配置、省/市/区三级联动地区选择、自动 IP 定位、连接测试
  - **扩展** — 拖拽排序、启用/禁用、新建（自定义/从应用新增/导入插件包）、编辑、删除
- 修改即生效，无需确认按钮

### 内置扩展

| 扩展 | 类型 | 说明 |
|------|------|------|
| 深度计算器 | command | 打开 Deepin 计算器（玲珑应用） |
| 截图工具 | command | 调用 Deepin 截图 DBus 服务 |
| 控制中心 | command | 打开 Deepin 控制中心 |
| 文件管理器 | command | 打开 Deepin 文件管理器（新窗口） |
| 剪切板历史 | widget | 独立窗口，SQLite 存储，支持文本/图片/文件历史 |
| 取色器 | widget | 独立窗口，从屏幕任意位置拾取颜色 |
| 性能监视器 | widget | 独立窗口，实时显示 CPU/内存/网络详细信息 |

### 系统集成

- **系统托盘** — 右键菜单：显示/隐藏、偏好设置、退出
- **右键菜单** — 悬浮球右键：设置、显示模式切换、重启、退出
- **自动定位** — 首次启动自动 IP 定位配置天气城市
- **剪贴板监听** — 全局剪贴板历史记录（文本/图片/文件，最多 100 条）

## 技术栈

- **语言**：Python 3.12
- **GUI 框架**：PyQt5 (Qt 5.15)
- **配置管理**：JSON + 手动验证
- **插件系统**：动态加载 + subprocess + importlib
- **系统集成**：DBus（Deepin Display1、Deepin Screenshot）
- **数据源**：/proc/meminfo、/proc/net/dev、和风天气 v7 API

## 项目结构

```
umi_float/
├── main.py                    # 应用入口
├── core/                      # 核心模块
│   ├── constants.py           # 常量定义与默认配置
│   ├── config.py              # 配置管理器（单例）
│   └── state.py               # 运行时状态（单例）
├── ui/                        # UI 模块
│   ├── float_widget.py        # 悬浮球窗口
│   ├── pie_panel.py           # 环形面板（动画、阴影、交互）
│   ├── settings_dialog.py     # 设置中心（三页面）
│   ├── tray_icon.py           # 系统托盘
│   ├── plugin_panel.py        # 插件 Widget 宿主面板
│   ├── icon_picker_dialog.py  # 图标选择器
│   ├── app_picker_dialog.py   # 应用选择器
│   ├── plugin_edit_dialog.py  # 扩展编辑对话框
│   └── confirm_dialog.py      # 确认对话框
├── widgets/                   # 基础组件
│   ├── float_button.py        # 悬浮球按钮（三种绘制模式）
│   ├── draggable_widget.py    # 可拖动窗口基类
│   ├── edge_snapper.py        # 边缘吸附
│   ├── location_selector.py   # 省/市/区三级联动选择器
│   ├── plugin_list_item.py    # 扩展列表项
│   ├── plugin_list_widget.py  # 扩展列表容器（拖拽排序）
│   └── toast.py               # Toast 通知
├── plugins/                   # 插件系统
│   ├── plugin_base.py         # PluginConfig 数据类
│   ├── plugin_loader.py       # 插件加载器（扫描、CRUD、执行）
│   └── plugin_manager.py      # 插件管理器（单例）
├── utils/                     # 工具模块
│   ├── system_info.py         # 屏幕几何（DBus + Qt 回退）
│   ├── theme_colors.py        # 主题色派生引擎
│   ├── memory_info.py         # 内存监控
│   ├── network_info.py        # 网络速度监控
│   ├── weather_info.py       # 和风天气 API 封装
│   ├── ip_location.py         # IP 地理定位
│   ├── clipboard_watcher.py  # 剪贴板历史监听
│   ├── desktop_entry.py      # .desktop 文件解析
│   └── autostart.py           # XDG 自启管理
├── components/                 # 复合组件
│   └── clock_widget.py        # 时钟弹窗组件
├── data/                       # 数据文件
│   └── qweather_china.json     # 中国省市区分级天气城市数据
├── assets/                     # 静态资源
│   ├── icon.png                # 应用图标
│   ├── arrow-go-back-line-black.svg
│   └── Weather/                 # 31 套天气 SVG 图标
├── extensions/                 # 内置扩展
│   ├── deepin-calculator/       # 深度计算器（玲珑应用）
│   ├── screenshot/              # 截图工具
│   ├── dde-control-center/      # 控制中心
│   ├── dde-file-manager/        # 文件管理器
│   ├── clipboard/               # 剪切板历史（widget）
│   ├── color-picker/            # 取色器（widget）
│   └── performance-monitor/     # 性能监视器（widget）
├── packaging/                  # 打包配置
│   ├── DEBIAN/control          # deb 包元数据
│   ├── DEBIAN/postinst         # 安装后脚本
│   └── usr/                    # 启动器、桌面入口、图标
├── scripts/
│   └── build-deb.sh            # 一键构建 deb 脚本
└── requirements.txt            # Python 依赖
```

## 快速开始

### 依赖安装

```bash
# 安装系统依赖
sudo apt install python3-venv python3-pip python3-pyqt5 python3-pyqt5.qtsvg python3-requests

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行项目

```bash
PYTHONPATH=$(pwd):$PYTHONPATH python3 main.py
```

### 构建 deb 包

```bash
bash scripts/build-deb.sh 1.0.2
```

生成 `umi-float_1.0.2_all.deb`，安装方式：

```bash
sudo dpkg -i umi-float_1.0.2_all.deb
```

## 扩展开发

### 扩展类型

| 类型 | 说明 | 执行方式 |
|------|------|----------|
| `command` | 启动外部命令 | `subprocess.Popen(shell=True)` |
| `widget` | 自定义 Qt Widget | 加载 `create_widget()` 工厂函数 |
| `python` | 进程内 Python 脚本 | 加载 `run()` 函数 |

### 扩展配置格式

在 `~/.local/share/umi-float/extensions/<plugin-id>/` 目录下创建 `manifest.json`：

```json
{
  "name": "扩展名称",
  "description": "扩展描述",
  "icon": "icon_name",
  "exec": "command_or_module",
  "type": "command",
  "enabled": true,
  "version": "1.0.0",
  "entry": "create_widget",
  "window_mode": "independent"
}
```

| 字段 | 说明 |
|------|------|
| `icon` | 系统图标名或 `icons/<filename>` 自定义图标 |
| `exec` | command 类型为命令；widget/python 类型为模块路径 |
| `entry` | widget 类型的入口函数名，默认 `create_widget` |
| `window_mode` | `embedded`（内嵌面板）或 `independent`（独立窗口） |

### Widget 插件示例

```python
def create_widget(host_info: dict):
    """host_info 包含: name, accent_color, data_dir, app"""
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel("Hello from plugin!")
    layout.addWidget(label)
    return widget
```

### 图标说明

- **系统图标**：使用 Freedesktop 图标主题名称（如 `accessories-calculator`）
- **自定义图标**：上传本地图片，自动保存到 `~/.local/share/umi-float/icons/`

## 配置说明

配置文件：`~/.config/umi-float/config.json`（首次运行自动创建）

| 配置项 | 说明 | 范围 / 类型 | 默认值 |
|--------|------|-------------|--------|
| `opacity` | 悬浮球透明度 | 0.1–1.0 | `1.0` |
| `float_ball_size` | 悬浮球尺寸 | 32–128 px | `83` |
| `theme` | 主题预设键 | lavender / coral / sunset / rose / forest / matcha / azure / indigo / pearl / ebony | `"lavender"` |
| `display_mode` | 悬浮球显示模式 | clock / performance / weather | `"performance"` |
| `pie_button_size` | 面板按钮大小 | 32–100 px | `63` |
| `pie_spacing` | 面板按钮间距 | 0–30 px | `9` |
| `pie_expand_mode` | 面板展开方式 | click / hover | `"click"` |
| `auto_start` | 开机自启 | boolean | `false` |
| `show_on_fullscreen` | 全屏时显示悬浮球 | boolean | `false` |
| `weather_api_host` | 和风天气 API 地址 | string | `"je693837aw.re.qweatherapi.com"` |
| `weather_api_key` | 和风天气 API Key | string | `""` |
| `weather_location` | 天气城市 ID | string | `"101010100"` |
| `position` | 悬浮球位置 | `{ "x": int, "y": int }` | `{ "x": 100, "y": 100 }` |
| `plugin_overrides` | 扩展覆盖配置 | object | `{}` |

## 开发计划

### v1.0.2 - 当前版本

- [x] 悬浮球 + 拖动 + 边缘吸附 + 贴边胶囊模式
- [x] 滚轮循环切换显示模式
- [x] 三种显示模式（时钟 / 性能 / 天气）
- [x] 10 种主题预设 + 自动调色板派生
- [x] 环形面板 + 展开/收起动画
- [x] 系统托盘集成
- [x] 配置管理（JSON + 手动验证）
- [x] 设置中心（个性化 / 天气 / 扩展管理）
- [x] 扩展管理（拖拽排序、启用/禁用、新建/编辑/删除）
- [x] 图标选择器（系统图标 + 本地上传）
- [x] 应用选择器（扫描系统 .desktop 文件）
- [x] 内置扩展（深度计算器、截图、控制中心、文件管理器、剪切板历史、取色器、性能监视器）
- [x] Widget 插件系统 + 独立窗口模式
- [x] 导入插件包（.zip）
- [x] 和风天气 + 自动 IP 定位
- [x] 内存 / 网络速度实时监控
- [x] 剪贴板历史监听（SQLite）

### v1.1.0 计划

- [ ] 全屏检测 + 避让
- [ ] 开机自启（XDG Autostart）
- [ ] 更多内置扩展
- [ ] 扩展市场 / 在线下载

## 注意事项

1. **Deepin/UOS 优化**：项目在 Deepin 25 上测试，使用 Deepin 特有的 DBus 服务（Screenshot、Display1）及玲珑应用（如深度计算器）
2. **Python 版本**：推荐使用 Python 3.12+
3. **天气功能**：需要配置和风天气 API Key
4. **系统依赖**：`python3-pyqt5`、`python3-pyqt5.qtsvg`、`python3-requests`
5. **系统托盘**：可能需要 `libayatana-appindicator3`

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。