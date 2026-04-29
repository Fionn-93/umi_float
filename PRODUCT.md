# Umi-Float 产品介绍

## 一、产品概述与定位

**Umi-Float** 是一款面向 Deepin / UOS Linux 桌面环境的轻量级悬浮工具箱。它以"悬浮球 + 抽屉式面板"为核心交互模式，将系统常用功能与第三方扩展工具整合到一个常驻桌面的圆形入口中，让用户随时触达所需功能，无需在任务栏或开始菜单中翻找。

### 设计理念

- **极简主义** — 减少边框和装饰，通过背景色变化引导交互，视觉降噪
- **呼吸感** — 合理使用内边距和外边距，让界面疏朗不拥挤
- **动态反馈** — 所有交互项均有 hover 状态，展开/收起配备缓动动画
- **统一性** — 全局使用应用主题色，悬浮球、面板、设置中心保持视觉一致

### 核心价值

| 维度 | 说明 |
|------|------|
| 即时触达 | 悬浮球常驻桌面，一次点击或悬停即可展开功能面板 |
| 个性定制 | 10 种主题配色、可调尺寸与透明度、灵活的扩展管理 |
| 轻量运行 | Python + PyQt5 原生实现，无 Electron 依赖，内存占用极低 |
| 平台贴合 | 深度集成 Deepin DBus 服务，适配 UOS 系统特性 |

---

## 二、功能特性详解

### 2.1 悬浮球（Float Ball）

悬浮球是 Umi-Float 的主入口，常驻桌面最上层，提供三种信息显示模式：

#### 时钟模式

- 秒针进度环实时旋转，中心显示小时与分钟
- 秒针轨迹使用主题色，底盘轨道半透明
- 刷新频率 100ms

#### 性能模式

- 彩色内存占用进度环：<40% 绿色、40%–80% 黄色、>80% 红色
- 中心显示内存百分比，下方显示实时下行网速（如 `↓1.2M`）
- 刷新频率 1 秒

#### 天气模式

- 显示当前温度（大字号）和天气描述（小字号）
- 天气图标以半透明水印形式出现在背景
- 集成和风天气（QWeather）v7 API，30 分钟自动刷新

#### 可调参数

| 参数 | 范围 | 说明 |
|------|------|------|
| 悬浮球大小 | 32–128 px | 拖动滑块实时调整 |
| 透明度 | 0.1–1.0 | 控制悬浮球不透明度 |
| 显示模式 | 时钟 / 性能 / 天气 | 右键菜单或设置中心切换 |
| 边缘吸附 | 20 px 阈值 | 鼠标释放时自动吸附到最近屏幕边缘 |
| 位置记忆 | — | 自动保存位置到配置文件，下次启动恢复 |

### 2.2 环形面板（Pie Panel）

点击悬浮球后展开的快捷入口面板，以环形布局呈现已启用的扩展按钮。

#### 展开动画

- 按钮从中心点以 **OutBack** 缓动飞出到环状目标位置
- 每个按钮延迟 40ms 启动，形成波浪效果
- 缩放动画同步：从 0 → 1 伴随位移

#### 收起动画

- 按钮以 **InQuad** 缓动飞回中心并缩小至消失
- 反向延迟（30ms/按钮），最远按钮先消失

#### 可调参数

| 参数 | 范围 | 说明 |
|------|------|------|
| 展开方式 | 鼠标点击 / 鼠标悬停 | 点击展开（默认）或悬停自动展开 |
| 按钮大小 | 32–100 px | 面板中扩展图标的尺寸 |
| 按钮间距 | 0–30 px | 环形布局中按钮之间的间距 |

#### 柔和阴影

每个按钮和中心按钮均绘制 radialGradient 圆形阴影，2px 垂直偏移、10px 扩散半径，营造悬浮质感。

### 2.3 主题系统

提供 10 种预设主题，每种主题色自动派生出 9 色调色板，覆盖全部 UI 控件：

| 主题键 | 显示名称 | 主色 | 色系分类 |
|--------|----------|------|----------|
| `lavender` | 薰衣草紫 | `#7B61FF` | 现代感 / 清新 |
| `coral` | 珊瑚红 | `#FF6B6B` | 现代感 / 清新 |
| `sunset` | 夕阳橙 | `#FF9F43` | 现代感 / 清新 |
| `rose` | 玫瑰粉 | `#FF85A2` | 现代感 / 清新 |
| `forest` | 森林绿 | `#4CAF50` | 现代感 / 清新 |
| `matcha` | 抹茶绿 | `#8BC34A` | 现代感 / 清新 |
| `azure` | 蔚蓝 | `#4FC3F7` | 现代感 / 清新 |
| `indigo` | 靛蓝 | `#5C6BC0` | 现代感 / 清新 |
| `pearl` | 珍珠白 | `#F5F5F7` | 沉稳 / 工具 |
| `ebony` | 乌木黑 | `#2C2C2E` | 沉稳 / 工具 |

**调色板派生规则**：

- 浮球文字色：根据主色明度自动选择白色或深色
- 浮球边框色：主色饱和度 +20%、明度 -15%
- 面板常态背景：10% 主色 + 90% 白色混合
- 面板悬停背景：85% 主色透明度
- 文字色：常态/悬停两档

切换主题后，悬浮球、面板、设置中心、所有弹窗同步实时刷新，无需重启。

### 2.4 设置中心（Settings Dialog）

860×620 无边框圆角窗口，可拖动，居中显示。

#### 页面结构

| 页面 | 内容 |
|------|------|
| **个性化** | 主题选择、浮球显示模式/大小、面板展开方式/图标大小/间距 |
| **天气** | API 地址与密钥、省/市/区三级联动地区选择、自动定位、连接测试 |
| **扩展** | 已启用/已禁用扩展列表、拖拽排序、新建/编辑/删除 |

#### 交互特性

- 侧边栏导航：选中项使用主题色背景 + 白色文字
- 页面切换：180ms `QPropertyAnimation` 淡入动画
- 修改即生效，无需点"确认"按钮
- 天气设置页进入时自动进入面板预览模式，退出时恢复

#### 组件规范

- 卡片（Card）：白色背景 `#ffffff`，圆角 16px，边框 `#e5e7eb`
- 设置行（SettingRow）：悬停背景 `rgba(0,0,0,0.03)`，左侧文字区固定 240px
- 下拉框：`QListView` 白底修复 UOS/chameleon 样式白底问题
- 确认对话框：替代 `QMessageBox`，统一风格

### 2.5 系统托盘（Tray Icon）

系统托盘驻留于任务栏通知区域，提供：

| 菜单项 | 功能 |
|--------|------|
| 显示/隐藏悬浮球 | 切换浮球可见性（不退出应用） |
| 偏好设置 | 打开设置中心 |
| 退出 | 关闭应用 |

图标来源：`assets/icon.png`，回退为系统主题图标 `applications-utilities`。

> **应用生命周期**：`QApplication.setQuitOnLastWindowClosed(False)` — 关闭悬浮球不会退出应用，仅通过托盘菜单退出。

### 2.6 系统信息采集

#### 内存监控

读取 `/proc/meminfo`，计算 `MemTotal - MemAvailable` 得到已用百分比与 GB 数值，每秒刷新。

#### 网络速度监控

读取 `/proc/net/dev`，两次采样差值计算实时上下行速率。自动排除 lo/docker/veth/virbr 等虚拟接口。格式化规则：

| 速率范围 | 格式 |
|----------|------|
| < 1 KB/s | `xxx B` |
| 1 KB/s – 1 MB/s | `x.xK` |
| ≥ 1 MB/s | `x.xM` |

#### 天气数据

通过和风天气（QWeather）v7 API 获取实时天气，内置 31 套 SVG 天气图标映射。首次运行自动通过 IP 定位配置默认城市。

#### IP 地理定位

三级回退策略：

1. `ip-api.com`（HTTP，无代理）
2. `ipapi.co`（HTTPS，无代理）
3. `ipapi.co`（HTTPS，系统代理）

定位结果自动匹配 QWeather 城市数据库写入配置。

#### 屏幕几何信息

优先通过 DBus 调用 `org.deepin.dde.Display1` 获取屏幕分辨率，失败时回退到 Qt `QScreen.geometry()`。

### 2.7 剪贴板历史

全局剪贴板监听器，记录所有复制/剪切操作：

- **存储**：SQLite 数据库（`~/.local/share/umi-float/clipboard_history.db`）
- **分类**：文本 / 图片 / 文件 自动识别
- **图片**：自动保存为 PNG 文件到 `clipboard_images/` 目录
- **去重**：与最近一条记录比较，相同内容不重复存储
- **容量**：最多保留 100 条记录，超出自动删除最旧条目
- **API**：`get_history(limit, content_type)` / `clear_history()` / `delete_item(row_id)`

### 2.8 自动定位

应用启动时，若天气城市为默认值（北京 `101010100`）且已配置 API Key，自动在后台线程中执行 IP 定位并设置最近城市。

---

## 三、界面交互说明

### 3.1 悬浮球交互

| 操作 | 行为 |
|------|------|
| 左键点击（位移 < 10px） | 展开/收起面板（click 模式） |
| 左键拖动（位移 ≥ 10px） | 移动浮球位置，释放后自动吸附屏幕边缘 |
| 鼠标进入 | 启动 200ms 定时器，到期后展开面板（hover 模式） |
| 鼠标离开 | 取消定时器 |
| 右键点击 | 显示上下文菜单：设置、显示模式切换、重启、退出 |

### 3.2 面板交互

| 操作 | 行为 |
|------|------|
| 点击扩展按钮 | 执行对应扩展（command 类型启动命令，widget 类型弹出面板） |
| 右键扩展按钮 | 弹出菜单：编辑扩展 / 禁用扩展 |
| 点击中心返回按钮 | 收起面板，恢复浮球 |
| 拖动中心按钮 | 移动面板整体位置，释放后更新浮球保存位置 |
| 鼠标离开面板（hover 模式） | 300ms 后自动收起面板 |

**位置约束**：面板始终定位在浮球中心，若超出屏幕边界则自动偏移至可见区域内。

### 3.3 设置中心交互

| 操作 | 行为 |
|------|------|
| 拖动标题栏 | 移动窗口 |
| 点击侧边栏项 | 切换页面（180ms 淡入） |
| 修改任意设置值 | 立即写入配置文件，实时更新 UI |
| 进入天气页面 | 面板自动进入预览模式（禁用交互按钮） |
| 关闭设置窗口 | 退出预览模式，恢复面板正常行为 |

---

## 四、扩展 / 插件系统

### 4.1 插件类型

| 类型 | 执行方式 | 说明 |
|------|----------|------|
| `command` | `subprocess.Popen(exec, shell=True)` | 启动外部命令或应用 |
| `widget` | 加载 Python 模块 `create_widget()` 函数 | 在独立/内嵌面板中显示自定义 Qt Widget |
| `python` | 加载 Python 脚本 `run()` 函数 | 进程内直接执行 |

> `shell=True` 是必需的，因为部分命令（如 `qdbus`）包含参数需要 Shell 解析。

### 4.2 内置扩展

| 扩展名 | 类型 | 执行命令 | 说明 |
|--------|------|----------|------|
| 计算器 | command | `deepin-calculator` | 打开 Deepin 计算器 |
| 截图工具 | command | `qdbus com.deepin.Screenshot /com/deepin/Screenshot com.deepin.Screenshot.StartScreenshot` | 调用 Deepin 截图 DBus 服务 |
| 剪切板历史 | widget | `clipboard`（entry: `create_widget`） | 独立窗口，SQLite 存储，支持文本/图片/文件历史 |
| 取色器 | widget | `color_picker`（entry: `create_widget`） | 独立窗口，从屏幕任意位置拾取颜色 |

### 4.3 扩展管理

- **拖拽排序**：在设置中心扩展页拖拽调整已启用扩展的顺序
- **启用/禁用**：开关切换，禁用的扩展不出现在面板中
- **新建扩展**：三种方式
  - **自定义新增** — 手动填写名称、描述、图标、执行命令
  - **从应用新增** — 扫描系统 `.desktop` 文件，浏览/搜索已安装应用
  - **导入插件包** — 上传 `.zip` 文件（仅 widget 类型）
- **编辑扩展**：修改名称、描述、图标、执行命令
- **删除扩展**：确认对话框后移除（内置扩展仅禁用，不可删除）

#### 图标选择器

扩展编辑时可通过图标选择器选择图标，支持两种来源：

1. **预设图标库** — 100+ Freedesktop 标准图标 + Deepin 专属图标，自动过滤在浅色背景下不可见的图标
2. **本地上传** — 支持 PNG/JPG/SVG/ICO 格式，图片保存至 `~/.local/share/umi-float/icons/` 并以 `icons/` 前缀引用

### 4.4 扩展目录结构

```
~/.local/share/umi-float/extensions/
└── <plugin-id>/
    ├── manifest.json          # 扩展描述文件
    ├── icons/                 # 自定义图标（可选）
    │   └── my-icon.svg
    └── data/                  # 扩展数据目录（自动创建）
```

项目内置扩展位于 `<repo>/extensions/`，优先级高于同名用户扩展。

### 4.5 扩展配置格式

**manifest.json** 完整字段：

```json
{
  "name": "扩展名称",
  "description": "扩展描述",
  "icon": "accessories-calculator",
  "exec": "deepin-calculator",
  "type": "command",
  "enabled": true,
  "version": "1.0.0",
  "entry": "create_widget",
  "window_mode": "independent"
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | string | — | 扩展显示名称 |
| `description` | string | `""` | 扩展描述（tooltip） |
| `icon` | string | — | 系统图标名或 `icons/<filename>` 自定义图标 |
| `exec` | string | — | command 类型为命令，widget/python 类型为模块路径或脚本名 |
| `type` | string | `"command"` | `command` / `widget` / `python` |
| `enabled` | bool | `true` | 是否启用 |
| `version` | string | `"1.0.0"` | 扩展版本 |
| `entry` | string | `"create_widget"` | widget 类型的入口函数名 |
| `window_mode` | string | `"embedded"` | widget 类型的窗口模式：`embedded`（内嵌面板）或 `independent`（独立窗口） |

### 4.6 Widget 插件开发

Widget 类型插件需在扩展目录下提供 Python 模块，导出 `create_widget(host_info)` 工厂函数：

```python
def create_widget(host_info: dict):
    """
    host_info 包含:
      - name: str          # 扩展名
      - accent_color: str   # 当前主题色 (#RRGGBB)
      - data_dir: Path      # 扩展数据目录
      - app: QApplication   # Qt 应用实例
    """
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel("Hello from plugin!")
    layout.addWidget(label)
    return widget
```

`manifest.json` 中的 `exec` 字段指向模块目录（如 `clipboard`），`entry` 指定入口函数名（默认 `create_widget`）。

**窗口模式**：

- `embedded` — 在应用内嵌面板中显示，面板关闭时浮球恢复
- `independent` — 创建独立浮动窗口，定位在浮球旁，关闭后恢复浮球

### 4.7 插件覆盖机制

用户可在不修改 manifest.json 的情况下覆盖扩展的某些字段。覆盖配置存储在全局配置的 `plugin_overrides` 字段中：

```json
{
  "plugin_overrides": {
    "calculator": {
      "icon": "my-custom-icon",
      "exec": "gnome-calculator"
    }
  }
}
```

---

## 五、技术架构概要

### 架构图

```
┌─────────────────────────────────────────────────┐
│                   main.py                       │
│               Application 入口                   │
├─────────────────────────────────────────────────┤
│  FloatWidget  │  PiePanel  │  PluginPanel  │ TrayIcon │
│  (悬浮球)      │  (环形面板) │  (插件面板)    │ (系统托盘) │
├─────────────────────────────────────────────────┤
│              SettingsDialog (设置中心)            │
│  PersonalizePage │ WeatherPage │ ExtensionsPage  │
├─────────────────────────────────────────────────┤
│              PluginManager (单例)                │
│           PluginLoader │ PluginConfig            │
├─────────────────────────────────────────────────┤
│   core/                  utils/                  │
│   ConfigManager  │  SystemInfo / ThemeColors    │
│   AppState       │  MemoryInfo / NetworkMonitor │
│   Constants      │  WeatherInfo / IPLocation    │
│                  │  ClipboardWatcher / AutoStart │
├─────────────────────────────────────────────────┤
│              extensions/                         │
│   calculator │ screenshot │ clipboard │ color-picker │
└─────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `core/constants.py` | 应用信息、目录路径、默认配置 |
| `core/config.py` | 配置管理器单例，JSON 读写与验证 |
| `core/state.py` | 运行时状态单例（浮球可见性、面板可见性、全屏状态） |
| `ui/float_widget.py` | 悬浮球窗口（透明圆形、模式切换、拖动/点击/悬停检测） |
| `ui/pie_panel.py` | 环形面板（PieButton、CenterButton、展开/收起动画、阴影绘制） |
| `ui/plugin_panel.py` | 插件 Widget 宿主面板 |
| `ui/settings_dialog.py` | 设置中心（三页面、个性化/天气/扩展管理） |
| `ui/tray_icon.py` | 系统托盘图标与菜单 |
| `ui/icon_picker_dialog.py` | 图标选择器（系统图标网格 + 本地文件上传） |
| `ui/app_picker_dialog.py` | 应用选择器（扫描 .desktop 文件，网格布局，搜索过滤） |
| `ui/plugin_edit_dialog.py` | 扩展编辑对话框 |
| `ui/confirm_dialog.py` | 确认对话框（替代 QMessageBox） |
| `widgets/float_button.py` | 悬浮球按钮绘制（时钟/性能/天气三种模式的自定义 QPainter） |
| `widgets/draggable_widget.py` | 可拖动窗口基类 |
| `widgets/edge_snapper.py` | 屏幕边缘吸附计算 |
| `widgets/location_selector.py` | 省/市/区三级联动天气地区选择器 |
| `widgets/plugin_list_widget.py` | 扩展列表容器（支持拖拽排序） |
| `widgets/plugin_list_item.py` | 扩展列表项（开/关、编辑、删除） |
| `widgets/toast.py` | Toast 通知组件 |
| `plugins/plugin_manager.py` | 插件管理器单例（CRUD、排序、执行、导入） |
| `plugins/plugin_loader.py` | 插件加载器（扫描目录、加载 manifest、执行命令/Widget） |
| `plugins/plugin_base.py` | PluginConfig 数据类、Plugin 抽象基类 |
| `utils/theme_colors.py` | 主题色派生引擎（9 色调色板自动生成） |
| `utils/system_info.py` | 屏幕几何（DBus + Qt 回退） |
| `utils/memory_info.py` | 内存使用率（/proc/meminfo） |
| `utils/network_info.py` | 网络速度监控（/proc/net/dev） |
| `utils/weather_info.py` | 和风天气 API 封装、图标映射、缓存 |
| `utils/ip_location.py` | IP 地理定位（三级回退） |
| `utils/clipboard_watcher.py` | 全局剪贴板监听与 SQLite 存储 |
| `utils/autostart.py` | XDG 自启管理 |
| `utils/desktop_entry.py` | .desktop 文件解析与应用列表扫描 |

### 核心设计模式

**单例模式**：`ConfigManager`、`AppState`、`PluginManager`、`ClipboardWatcher`、`NetworkMonitor` 均采用手写单例。关键约束：`__init__` 中所有实例属性必须在 `_instance` 检查之前初始化，否则第二次构造调用会返回不完整的对象。

**信号槽驱动**：UI 更新通过 PyQt5 信号槽串联，如：

- `FloatWidget.clicked` → `Application._toggle_panel`
- `PiePanel.plugin_executed` → `Application._execute_plugin`
- `SettingsDialog.settings_changed` → `Application._apply_settings`

**配置即生效**：设置修改通过 `config.update(**kwargs)` 写入 JSON 后立即触发 UI 刷新，无需手动保存。

### 数据文件

| 路径 | 说明 |
|------|------|
| `~/.config/umi-float/config.json` | 用户配置文件 |
| `~/.local/share/umi-float/extensions/` | 用户扩展目录 |
| `~/.local/share/umi-float/icons/` | 自定义图标目录 |
| `~/.local/share/umi-float/clipboard_history.db` | 剪贴板历史数据库 |
| `data/qweather_china.json` | 中国省市区分级地区数据（用于天气城市选择） |
| `assets/Weather/` | 31 套天气 SVG 图标（sun、cloudy、rainy 等各含 fill/line 两变体） |

---

## 六、安装与配置

### 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Deepin 25 / UOS Linux |
| Python | 3.12+ |
| Qt 运行时 | PyQt5 5.15.11 |
| 系统库 | `libayatana-appindicator3`（系统托盘支持，可选） |

### 安装依赖

```bash
# 安装系统依赖
sudo apt install python3-venv python3-pip

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行

```bash
PYTHONPATH=$(pwd):$PYTHONPATH python3 main.py
```

> **注意**：所有 import 均基于项目根目录，必须设置 `PYTHONPATH`，否则应用无法启动。

### 配置文件

配置文件路径：`~/.config/umi-float/config.json`

首次运行自动创建，内容为默认配置：

```json
{
  "opacity": 1.0,
  "float_ball_size": 83,
  "theme": "lavender",
  "display_mode": "performance",
  "pie_button_size": 63,
  "pie_spacing": 9,
  "pie_expand_mode": "click",
  "auto_start": false,
  "show_on_fullscreen": false,
  "weather_api_host": "je693837aw.re.qweatherapi.com",
  "weather_api_key": "<your-api-key>",
  "weather_location": "101010100",
  "position": { "x": 100, "y": 100 },
  "plugin_overrides": {}
}
```

### 配置项说明

| 配置项 | 说明 | 范围 / 类型 | 默认值 |
|--------|------|-------------|--------|
| `opacity` | 悬浮球透明度 | 0.1–1.0 | `1.0` |
| `float_ball_size` | 悬浮球尺寸 | 32–128 px | `83` |
| `theme` | 主题预设键 | `lavender` / `coral` / `sunset` / `rose` / `forest` / `matcha` / `azure` / `indigo` / `pearl` / `ebony` | `"lavender"` |
| `display_mode` | 悬浮球显示模式 | `clock` / `performance` / `weather` | `"performance"` |
| `pie_button_size` | 面板按钮大小 | 32–100 px | `63` |
| `pie_spacing` | 面板按钮间距 | 0–30 px | `9` |
| `pie_expand_mode` | 面板展开方式 | `click` / `hover` | `"click"` |
| `auto_start` | 开机自启 | boolean | `false` |
| `show_on_fullscreen` | 全屏时显示悬浮球 | boolean | `false` |
| `weather_api_host` | 和风天气 API 地址 | string | `"je693837aw.re.qweatherapi.com"` |
| `weather_api_key` | 和风天气 API Key | string | `""` |
| `weather_location` | 天气城市 ID | string（QWeather Location ID） | `"101010100"` |
| `position` | 悬浮球位置 | `{ "x": int, "y": int }` | `{ "x": 100, "y": 100 }` |
| `plugin_overrides` | 扩展覆盖配置 | object | `{}` |

**弃用配置项**：

- `theme_color` → 已迁移为 `theme`（主题预设键）
- `display_mode: "memory"` → 已自动迁移为 `"performance"`

### 天气功能配置

1. 在设置中心 → 天气页面填写和风天气 API 地址和 Key
2. 通过省/市/区三级选择器选择城市，或点击"自动定位"按钮
3. 点击"测试连接"验证配置是否正确
4. 切换显示模式为"天气"即可在悬浮球上查看天气

### 自启动配置

通过 XDG Autostart 实现，桌面文件路径：`~/.config/autostart/umi-float.desktop`

可在设置中启用（当前版本需手动配置）或通过 `utils/autostart.py` 管理：

```python
from utils.autostart import Autostart

Autostart.enable("/path/to/main.py")   # 启用自启
Autostart.disable()                       # 禁用自启
Autostart.is_enabled()                    # 查询状态
```