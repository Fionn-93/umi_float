# Umi-Float 插件开发指南

## 一、概述

Umi-Float 的插件系统支持三种执行类型：

| 类型 | 说明 | 执行方式 |
|------|------|----------|
| `command` | Shell 命令 | 通过 `subprocess.Popen(..., shell=True)` 执行外部程序 |
| `python` | Python 模块 | 在主进程内通过 `importlib` 动态加载，调用 `run(context)` 函数 |
| `widget` | Qt Widget 窗口 | 在主进程内通过 `importlib` 动态加载，调用 `create_widget(host_info)` 函数，以独立窗口或嵌入面板方式展示 |

> **平台限定**：Umi-Float 仅运行于 Deepin/UOS Linux，部分插件依赖 Deepin 特有工具（如 `deepin-calculator`、`qdbus com.deepin.Screenshot`）。

---

## 二、目录结构

### 项目内置插件

```
umi_float/
└── extensions/
    └── <plugin_dir>/
        ├── manifest.json
        └── ...         # 类型相关文件（Python 包、图标等）
```

内置插件位于仓库根目录 `extensions/` 下，随项目发布，不可删除。

### 用户插件

```
~/.local/share/umi-float/extensions/
└── <plugin_id>/
    ├── manifest.json
    └── ...
```

用户插件位于用户数据目录，可自由增删。

> **覆盖规则**：若项目内置插件与用户插件的目录名相同，用户插件会覆盖内置插件（按目录名匹配，非 manifest 内的 name）。

### 插件数据目录

插件可通过 `host_info["data_dir"]` 访问自己的数据目录：

```python
data_dir = host_info["data_dir"]  # Path → ~/.local/share/umi-float/extensions/<plugin_id>/data/
data_dir.mkdir(parents=True, exist_ok=True)
```

---

## 三、manifest.json 规范

```json
{
  "name": "插件显示名称",
  "description": "功能描述（鼠标悬停提示）",
  "icon": "图标名称或路径",
  "exec": "执行命令 / Python 模块名 / widget 包名",
  "type": "command | python | widget",
  "version": "1.0.0",
  "entry": "create_widget",
  "window_mode": "embedded",
  "enabled": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 在面板上显示的名称 |
| `description` | string | 否 | 鼠标悬停时的提示文字 |
| `icon` | string | 是 | 图标名称，详见"图标系统"章节 |
| `exec` | string | 是 | command：shell 命令；python：不含后缀的 `.py` 文件名；widget：包目录名 |
| `type` | string | 否 | 默认为 `command` |
| `version` | string | 否 | 插件版本号，默认 `1.0.0` |
| `entry` | string | 否 | widget 类型入口函数名，默认 `create_widget` |
| `window_mode` | string | 否 | widget 专属：`embedded`（嵌入面板）或 `independent`（独立窗口），默认 `embedded` |
| `enabled` | boolean | 否 | 默认 true |

---

## 四、command 类型

直接通过 shell 执行外部程序，适合打开系统应用或调用工具命令。

```json
{
  "name": "计算器",
  "description": "打开 Deepin 计算器",
  "icon": "accessories-calculator",
  "exec": "deepin-calculator",
  "type": "command",
  "enabled": true
}
```

`exec` 可以是任何可执行的 shell 命令（含管道、重定向等）。例如截图工具使用 DBus 调用：

```json
{
  "name": "截图工具",
  "description": "调用系统截图工具",
  "icon": "camera-photo",
  "exec": "qdbus com.deepin.Screenshot /com/deepin/Screenshot com.deepin.Screenshot.StartScreenshot",
  "type": "command",
  "enabled": true
}
```

无需额外代码，填好 manifest 即可。

---

## 五、python 类型

python 类型插件在主进程内执行，可以访问 PyQt5 GUI 环境，适合需要弹出窗口或与主应用交互的场景。

### 入口函数

扩展目录下的 `.py` 文件**必须**导出以下签名：

```python
def run(context: dict) -> None:
    pass
```

`context` 是 Umi-Float 传入的上下文字典：

| 键 | 类型 | 说明 |
|----|------|------|
| `app` | `QApplication` | 主应用实例，用于创建窗口、获取屏幕信息等 |

### 示例：取色器

```
extensions/color-picker/
├── manifest.json
└── color_picker.py
```

**manifest.json**：

```json
{
  "name": "取色器",
  "description": "从屏幕任意位置拾取颜色",
  "icon": "color-picker",
  "type": "python",
  "exec": "color_picker",
  "enabled": true
}
```

**color_picker.py**：

```python
"""取色器扩展 - 从屏幕拾取颜色并复制到剪贴板"""

import subprocess
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QFont


class ColorPickerWindow(QWidget):
    def __init__(self, screenshot: QPixmap):
        super().__init__()
        self.screenshot = screenshot
        self.mouse_pos = None
        self.current_color = QColor(0, 0, 0)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose)
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.mouse_pos:
            x, y = self.mouse_pos.x(), self.mouse_pos.y()
            color = self._get_pixel_color(x, y)
            self.current_color = color
            self._draw_magnifier(painter, self.mouse_pos, color)

    def _get_pixel_color(self, x, y) -> QColor:
        if 0 <= x < self.screenshot.width() and 0 <= y < self.screenshot.height():
            return self.screenshot.toImage().pixelColor(x, y)
        return QColor(0, 0, 0)

    def _draw_magnifier(self, painter, pos, color: QColor):
        mx, my = pos.x(), pos.y()
        size = 120
        half = size // 2
        mag_left = mx - half
        mag_top = my - half - size - 20
        painter.fillRect(int(mag_left), int(mag_top), size, size, Qt.white)
        hex_str = color.name().upper()
        rgb_str = f"rgb({color.red()}, {color.green()}, {color.blue()})"
        painter.setFont(QFont("monospace", 11))
        painter.setPen(Qt.black)
        painter.drawText(int(mag_left), int(mag_top + size + 20), hex_str)
        painter.drawText(int(mag_left), int(mag_top + size + 40), rgb_str)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hex_str = self.current_color.name().upper()
            QApplication.clipboard().setText(hex_str)
            self.close()
        elif event.button() == Qt.RightButton:
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


def run(context: dict) -> None:
    app = context.get("app")
    if app is None:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
    screen = QApplication.primaryScreen()
    screenshot = screen.grabWindow(0)
    window = ColorPickerWindow(screenshot)
    window.show()
```

### 注意事项

- **进程隔离**：扩展运行在主进程中，避免执行耗时操作阻塞 UI；若必须执行长时任务，使用 `QTimer.singleShot` 或 `threading.Thread`
- **命名冲突**：避免使用与 Umi-Float 内部模块相同的变量名（如 `app`、`config`）
- **异常处理**：扩展内未捕获的异常会打印到 stderr，不会导致主应用崩溃

---

## 六、widget 类型

widget 类型插件是功能最完善的插件形态，支持创建复杂的 Qt Widget 界面。以下以**剪切板历史**插件（`extensions/clipboard/`）为完整示例进行深入讲解。

### 6.1 目录结构

```
extensions/clipboard/
├── manifest.json
├── icons/
│   └── clipboard.svg
├── data/                    # 可选，运行时数据
│   └── clipboard_history.db
└── clipboard/               # Python 包（包名可自定义）
    ├── __init__.py
    └── widget.py            # 主 Widget 类
```

### 6.2 manifest.json

```json
{
  "name": "剪切板历史",
  "description": "记录复制和剪切的文本历史",
  "icon": "icons/clipboard.svg",
  "exec": "clipboard",
  "type": "widget",
  "version": "1.0.0",
  "entry": "create_widget",
  "window_mode": "independent",
  "enabled": true
}
```

关键字段说明：

| 字段 | 值 | 说明 |
|------|-----|------|
| `type` | `"widget"` | 标识为 widget 类型插件 |
| `exec` | `"clipboard"` | Python 包目录名（相对于插件根目录） |
| `entry` | `"create_widget"` | 入口函数名，默认 `create_widget` |
| `window_mode` | `"independent"` | `independent`：独立窗口；`embedded`：嵌入面板 |

### 6.3 __init__.py — 包入口

```python
"""剪切板历史插件 - 入口"""

import sys
from pathlib import Path

plugin_dir = Path(__file__).parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))


def create_widget(host_info: dict):
    from widget import ClipboardWidget
    return ClipboardWidget(host_info)
```

> **职责**：`__init__.py` 将插件包目录加入 `sys.path`，使 `importlib` 能正确加载。然后从子模块导入并调用 `create_widget(host_info)`。

### 6.4 host_info 字典

widget 插件的主类构造函数接收一个 `host_info` 字典：

| 键 | 类型 | 说明 |
|----|------|------|
| `name` | string | 插件显示名称（来自 manifest） |
| `accent_color` | string | 当前应用主题色（十六进制，如 `"#7B61FF"`） |
| `data_dir` | Path | 插件数据目录 `~/.local/share/umi-float/extensions/<plugin_id>/data/` |
| `app` | QApplication | 主应用实例 |
| `widget_host` | QWidget | PluginPanel 宿主面板引用 |
| `set_float_display` | callable | `set_float_display(data: dict)` — 在浮球上显示自定义进度环 + 图标 + 文字。`data` 格式：`{ "progress": 0.0–1.0, "icon": QIcon, "text": str, "icon_color": str }` |
| `clear_float_display` | callable | `clear_float_display()` — 清除自定义浮球显示，恢复为当前显示模式 |
| `keep_float_visible` | bool | 若为 `True`，插件窗口打开时浮球保持可见（默认 `False`，用于计时器插件确保倒计时可见） |

```python
def __init__(self, host_info: dict):
    super().__init__()
    self._host_info = host_info
    self._accent_color = host_info.get("accent_color", "#7B61FF")
    data_dir = host_info.get("data_dir")  # Path 对象

    # 可选：更新浮球显示
    host_info.get("set_float_display")({
        "progress": 0.5,
        "icon": my_icon,
        "text": "05:30",
        "icon_color": "#FF6B6B",
    })

    # 可选：让浮球保持可见
    host_info.get("keep_float_visible", False)
```

### 6.5 独立窗口模式（window_mode: independent）

独立窗口模式适合需要完整窗口 chrome（标题栏、关闭按钮、阴影）的插件。

**窗口标志组合**：

```python
self.setWindowFlags(
    Qt.Window
    | Qt.FramelessWindowHint       # 无边框
    | Qt.WindowStaysOnTopHint      # 始终在最前
)
self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景（圆角必需）
```

**阴影效果**（替代 CSS box-shadow，Qt 图形效果不会被圆角裁剪）：

```python
from PyQt5.QtGui import QColor, QGraphicsDropShadowEffect

shadow = QGraphicsDropShadowEffect(self)
shadow.setBlurRadius(25)
shadow.setYOffset(6)
shadow.setColor(QColor(0, 0, 0, 50))
container.setGraphicsEffect(shadow)
```

**关闭信号**：widget 必须实现 `closed` pyqtSignal，供主应用监听并恢复悬浮球：

```python
class ClipboardWidget(QWidget):
    closed = pyqtSignal()

    def _on_close(self):
        self.closed.emit()
```

主应用侧的连接逻辑：

```python
# main.py
if config.window_mode == "independent":
    widget_instance = widget_class(host_info)
    widget_instance.closed.connect(self._on_independent_widget_closed)
    widget_instance.move(x, y)
    widget_instance.show()
```

**拖拽移动**（无标题栏窗口需要手动实现）：

```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

def mouseMoveEvent(self, event):
    if event.buttons() == Qt.LeftButton:
        self.move(event.globalPos() - self._drag_pos)
        event.accept()
```

### 6.6 嵌入面板模式（window_mode: embedded）

嵌入面板模式下，widget 被放入 `PluginPanel`（一个容器窗口），跟随悬浮球位置自动定位。widget 本身不需要实现标题栏、关闭按钮和拖拽逻辑。

```python
# 嵌入模式 widget 不需要：
# - Qt.FramelessWindowHint
# - Qt.WA_TranslucentBackground
# - 手动拖拽实现
# - 标题栏和关闭按钮
```

> `PluginPanel` 提供统一的标题栏（含关闭按钮）和容器，widget 只需关注自身业务 UI。

### 6.7 动态强调色获取

应用主题色通过 `host_info["accent_color"]` 传入。若需要在运行时重新获取（例如刷新样式）：

```python
from utils.theme_colors import get_current_accent_color

accent = get_current_accent_color()  # "#7B61FF"

def _rgb_from_hex(self, hex_color: str):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r, g, b
```

---

## 七、UI 样式规范

widget 类型插件应遵循以下 UI 规范。以下规范基于全局设计系统（`DESIGN.md`），针对 widget 插件场景整理。

### 7.1 窗口架构

#### 独立窗口（window_mode: independent）

```
ClipboardWidget
└── QVBoxLayout (margins: 12,12,12,12)
    └── MainContainer (#ffffff, #e5e7eb border, 16px radius)
        ├── TitleBar (54px, 底部分割线 rgba(229,231,235,0.5))
        │   ├── WindowTitle (14px Bold, #1f2937)
        │   └── CloseBtn (32x32, hover: accent 10% bg)
        ├── ClipboardListWidget (透明背景, NoSelection)
        │   └── item → ClipboardItemWidget (卡片，可单击复制)
        └── Footer (35px, 状态标签)
```

**窗口标志**：`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`

**透明背景**：`setAttribute(Qt.WA_TranslucentBackground)` + 圆角容器

**阴影**：`QGraphicsDropShadowEffect`（`blurRadius: 25`, `yOffset: 6`, `color: rgba(0,0,0,50)`）

**尺寸**：`resize(380, 560)`（参考值，按需调整）

### 7.2 颜色系统

#### 动态强调色（来自 host_info）

| Token | 用途 |
|-------|------|
| `rgba({ar},{ag},{ab},0.13)` | 类型标签背景 |
| `rgba({ar},{ag},{ab},0.1)` | 关闭按钮 hover 背景 |
| `rgba({ar},{ag},{ab},0.03)` | 卡片 hover 背景 |
| `rgba({ar},{ag},{ab},0.2)` | 卡片 hover 边框 |

#### 固定颜色 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `#ffffff` | 容器背景 | MainContainer |
| `#e5e7eb` | 边框色 | 容器边框、ActionBtn 边框 |
| `#1f2937` | 主文字 | WindowTitle、内容标签 |
| `#6b7280` | 次要文字 | 时间标签、状态标签默认 |
| `#86868b` | 关闭按钮默认色 | CloseBtn |
| `#1d1d1f` | 关闭按钮 hover 文字 | CloseBtn hover |
| `#d1d5db` | 按钮边框 | ActionBtn 默认边框 |
| `#9ca3af` | 按钮边框 hover | ActionBtn hover 边框 |
| `#f3f4f6` | 按钮背景 hover | ActionBtn hover |
| `#fecaca` | 删除按钮边框 | DeleteBtn 默认边框 |
| `#f87171` | 删除按钮边框 hover | DeleteBtn hover 边框 |
| `#fee2e2` | 删除按钮背景 hover | DeleteBtn hover |
| `#b91c1c` | 删除按钮文字 | DeleteBtn |
| `#374151` | 操作按钮文字 | ActionBtn |
| `rgba(229,231,235,0.5)` | 标题栏分割线 | TitleBar border-bottom |

### 7.3 字体规范

| 元素 | 字号 | 字重 | 颜色 |
|------|------|------|------|
| WindowTitle | 14px | Bold (700) | `#1f2937` |
| 内容标签 | 13px | Normal | `#1f2937` |
| 类型标签 | 10px | Bold (700) | `{accent}` |
| 时间标签 | 11px | Normal | `#6b7280` |
| 操作按钮 | 11px | Normal | ActionBtn: `#374151` / DeleteBtn: `#b91c1c` |
| 状态标签 | 11px | Normal | `#6b7280` / `{accent}`（反馈时 bold） |

### 7.4 间距规范

| 组件 | 属性 | 值 |
|------|------|-----|
| 根布局 | contentsMargins | `12px 12px 12px 12px` |
| 主容器 | border-radius | `16px` |
| 主容器 | border | `1px solid #e5e7eb` |
| 标题栏 | FixedHeight | `54px` |
| 标题栏 | contentsMargins | `20px 0 10px 0` |
| 卡片 | FixedHeight | `90px` |
| 卡片 | contentsMargins | `12px 10px 12px 10px` |
| 底部状态栏 | FixedHeight | `35px` |

### 7.5 圆角规范

| 组件 | 圆角值 |
|------|--------|
| 主容器 | `16px` |
| 卡片 | `10px` |
| 关闭按钮 | `6px` |
| 类型标签 | `4px` |
| 操作按钮 | `6px` |

### 7.6 组件 QSS 模板

#### 主容器（MainContainer）

```css
#MainContainer {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
}
```

#### 标题栏（TitleBar）

```css
#TitleBar {
    border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}
#WindowTitle {
    font-size: 14px;
    font-weight: bold;
    color: #1f2937;
}
```

#### 关闭按钮（CloseBtn）

```css
#CloseBtn {
    background: transparent;
    color: #86868b;
    border: none;
    border-radius: 6px;
    font-size: 16px;
}
#CloseBtn:hover {
    background: rgba({ar}, {ag}, {ab}, 0.1);
    color: #1d1d1f;
}
```

#### 列表（ClipboardListWidget）

```css
#ClipboardListWidget {
    border: none;
    background: transparent;
}
#ClipboardListWidget::item {
    background: transparent;
    padding: 4px 8px;
}
```

- `NoSelection` 模式，无选中高亮
- `ScrollPerPixel` 滚动

#### 卡片条目（ClipboardItemWidget）

**默认状态**：

```css
#ItemCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
```

**Hover 状态**：

```css
#ItemCard {
    background: rgba({ar}, {ag}, {ab}, 0.03);
    border: 1px solid rgba({ar}, {ag}, {ab}, 0.2);
    border-radius: 10px;
}
```

> **注意**：`enterEvent`/`leaveEvent` 动态设置的 stylesheet 会**替换**整个控件的样式，必须完整写 `background` + `border` + `border-radius`。

**复制按钮（ActionBtn）**：

```css
#ActionBtn {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    color: #374151;
    font-size: 11px;
}
#ActionBtn:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}
```

**删除按钮（DeleteBtn）**：

```css
#DeleteBtn {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    color: #b91c1c;
    font-size: 11px;
}
#DeleteBtn:hover {
    background: #fee2e2;
    border-color: #f87171;
}
```

### 7.7 Qt5 样式约束

| 约束 | 说明 |
|------|------|
| **8位hex禁用** | Qt5 QSS 不支持 `{color}dd`，必须用 `rgba(r,g,b,a)` |
| **WA_TranslucentBackground** | 必须设置，配合 FramelessWindowHint 实现圆角 |
| **QGraphicsDropShadowEffect** | 圆角窗口下 CSS box-shadow 被裁剪，必须用 Qt 效果 |
| **WA_StyledBackground** | `QWidget` 子类必须添加此属性才能渲染 `background-color` stylesheet |
| **hover 动态样式** | `enterEvent`/`leaveEvent` 内联 `setStyleSheet` 可行（动态状态无更好方案） |

---

## 八、图标系统

图标支持两种来源：

### 系统图标

使用 Freedesktop 图标主题名称：

```json
{
  "icon": "accessories-calculator"
}
```

可通过 `QIcon.fromTheme(name)` 渲染。

| 场景 | 图标名 |
|------|--------|
| 计算器 | `accessories-calculator` |
| 文件管理器 | `system-file-manager` |
| 设置 | `preferences-system` |
| 日历 | `x-office-calendar` |
| 截图 | `camera-photo` |
| 颜色选择 | `color-picker` |

### 自定义图标

上传本地图片后，路径以 `icons/` 开头，指向 `~/.local/share/umi-float/icons/` 下的文件：

```json
{
  "icon": "icons/abc123.png"
}
```

---

## 九、打包与分发

如需将 widget 插件分享给其他用户，将插件目录打包为 zip 文件。接收方只需将解压后的目录放入 `~/.local/share/umi-float/extensions/` 即可。

widget 类型插件包结构：

```
my-plugin.zip
└── my_plugin/
    ├── manifest.json
    ├── icons/
    │   └── icon.svg
    ├── data/
    └── my_plugin/
        ├── __init__.py
        └── widget.py
```

> 注意：zip 包内的顶层目录名即为 `plugin_id`。

---

## 十、调试提示

1. **运行时无反应**：`subprocess.Popen` 静默失败时查看终端 stderr 输出
2. **widget 类型加载失败**：检查 `manifest.json` 的 `exec`、`entry` 字段是否正确匹配文件结构
3. **manifest 字段缺失**：缺少必填字段会导致插件无法加载，查看启动日志
4. **图标不显示**：检查图标名是否可被 `QIcon.fromTheme()` 识别，或路径是否正确
5. **PYTHONPATH**：运行应用时确保 `PYTHONPATH` 包含项目根目录：
   ```bash
   PYTHONPATH=$(pwd):$PYTHONPATH python3 main.py
   ```
6. **独立窗口不显示**：检查是否正确发射 `closed` 信号；主应用依赖此信号恢复悬浮球
7. **样式不生效**：`QWidget` 子类确认已设置 `WA_StyledBackground` 属性

---

## 十一、API 参考

插件可从以下路径导入所需模块：

| 模块 | 说明 |
|------|------|
| `PyQt5.QtWidgets` | 所有 Qt 控件 |
| `PyQt5.QtCore` | Qt 核心类型（Qt 常量、QTimer、pyqtSignal 等） |
| `PyQt5.QtGui` | QColor、QPainter、QIcon、QPixmap 等 |
| `core.config` → `get_config()` | 获取 `ConfigManager` 单例，可读取/修改配置 |
| `core.constants` | 常量定义（`DATA_DIR`、`CONFIG_DIR`、`EXTENSIONS_DIR` 等） |
| `utils.theme_colors` | `get_current_accent_color()`、`theme_from_key()` 等 |
| `utils.system_info` | `SystemInfo.get_screen_geometry()` 等 |

> 注意：不要直接 import 主应用其他模块（如 `main`），避免循环依赖和未定义行为。

---

## 十二、完整示例：剪切板历史插件

以下为剪切板历史插件的完整文件结构与核心代码。

### 文件结构

```
extensions/clipboard/
├── manifest.json
├── icons/
│   └── clipboard.svg
└── clipboard/
    ├── __init__.py
    └── widget.py
```

### manifest.json

```json
{
  "name": "剪切板历史",
  "description": "记录复制和剪切的文本历史",
  "icon": "icons/clipboard.svg",
  "exec": "clipboard",
  "type": "widget",
  "version": "1.0.0",
  "entry": "create_widget",
  "window_mode": "independent",
  "enabled": true
}
```

### clipboard/__init__.py

```python
"""剪切板历史插件 - 入口"""

import sys
from pathlib import Path

plugin_dir = Path(__file__).parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))


def create_widget(host_info: dict):
    from widget import ClipboardWidget
    return ClipboardWidget(host_info)
```

### clipboard/widget.py（核心部分）

```python
"""剪切板历史插件 - 卡片式交互增强版"""

import logging
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QHBoxLayout, QGraphicsDropShadowEffect,
    QApplication, QFrame, QAbstractItemView,
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QPoint, QSize, QDateTime,
    QMimeData, QUrl, QRectF, QEvent,
)
from PyQt5.QtGui import QColor, QPixmap, QPainter, QPainterPath

from utils.clipboard_watcher import ClipboardWatcher
from core.constants import DATA_DIR

logger = logging.getLogger(__name__)


class ClipboardItemWidget(QFrame):
    """自定义卡片条目组件"""

    copy_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(int)
    clicked = pyqtSignal(str, str)

    TYPE_NAMES = {"text": "文本", "image": "图片", "file": "文件", "url": "链接"}

    def __init__(self, row_id, content, content_type, timestamp, accent_color, ar, ag, ab):
        super().__init__()
        self.row_id = row_id
        self.content = content
        self.content_type = content_type
        self._accent = accent_color
        self._ar = ar
        self._ag = ag
        self._ab = ab
        self._timestamp = timestamp

        self.setObjectName("ItemCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header: 类型标签 + 时间 + 操作按钮
        header_layout = QHBoxLayout()

        label_text = self.TYPE_NAMES.get(content_type, "文本")
        type_label = QLabel(label_text)
        type_label.setStyleSheet(
            f"background: rgba({ar}, {ag}, {ab}, 0.13); "
            f"color: {accent_color}; "
            f"font-size: 10px; "
            f"font-weight: bold; "
            f"padding: 2px 6px; "
            f"border-radius: 4px;"
        )

        time_str = self._format_time(timestamp)
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        header_layout.addWidget(type_label)
        header_layout.addWidget(time_label)
        header_layout.addStretch()

        # 操作按钮组
        self.action_group = QWidget()
        self.action_group.setFixedWidth(70)
        action_lay = QHBoxLayout(self.action_group)
        action_lay.setContentsMargins(0, 0, 0, 0)
        action_lay.setSpacing(8)

        self.btn_copy = QPushButton("复制")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setFixedSize(28, 28)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        action_lay.addWidget(self.btn_copy)

        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("DeleteBtn")
        self.btn_delete.setFixedSize(28, 28)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        action_lay.addWidget(self.btn_delete)

        header_layout.addWidget(self.action_group)
        layout.addLayout(header_layout)

        # 内容区
        if content_type == "image":
            self._build_image_content(layout)
        elif content_type == "file":
            self._build_file_content(layout)
        else:
            self._build_text_content(layout)

        self.btn_copy.clicked.connect(
            lambda: self.copy_requested.emit(self.content, self.content_type)
        )
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.row_id))

    def _build_text_content(self, layout):
        self.setFixedHeight(90)
        display_text = self._prepare_display_text(self.content)
        self.content_label = QLabel(display_text)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #1f2937; font-size: 13px;")
        self.content_label.setMaximumHeight(48)
        layout.addWidget(self.content_label)

    def _build_image_content(self, layout):
        self.setFixedHeight(140)
        img_path = DATA_DIR / "clipboard_images" / self.content
        pixmap = QPixmap(str(img_path)) if img_path.exists() else QPixmap()
        # ... 图片渲染逻辑（圆角裁剪等）
        layout.addWidget(thumb_label)

    def _build_file_content(self, layout):
        self.setFixedHeight(90)
        files = self.content.strip().split("\n")
        file_name = Path(files[0]).name if files else "未知文件"
        display_name = f"{file_name} 等 {len(files)} 个文件" if len(files) > 1 else file_name
        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #1f2937; font-size: 13px; font-weight: 500;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)

    def _prepare_display_text(self, content: str) -> str:
        lines = content.strip().split("\n")
        if len(lines) > 2:
            return lines[0] + "\n" + lines[1] + " ..."
        text = " ".join(lines)
        return text[:100] + " ..." if len(text) > 100 else text

    def _format_time(self, timestamp):
        dt = QDateTime.fromSecsSinceEpoch(int(timestamp))
        return dt.toString("HH:mm:ss")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.content, self.content_type)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.btn_copy.setStyleSheet(
            "background: #ffffff; border: 1px solid #d1d5db; "
            "border-radius: 6px; color: #374151; font-size: 11px;"
        )
        self.btn_delete.setStyleSheet(
            "background: #fef2f2; border: 1px solid #fecaca; "
            "border-radius: 6px; color: #b91c1c; font-size: 11px;"
        )
        self.setStyleSheet(
            f"#ItemCard {{ background: rgba({self._ar}, {self._ag}, {self._ab}, 0.03); "
            f"border: 1px solid rgba({self._ar}, {self._ag}, {self._ab}, 0.2); "
            f"border-radius: 10px; }}"
        )

    def leaveEvent(self, event):
        self.btn_copy.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        self.btn_delete.setStyleSheet(
            "background: transparent; border: none; color: transparent; font-size: 11px;"
        )
        self.setStyleSheet(
            "#ItemCard { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; }"
        )


class ClipboardWidget(QWidget):
    """剪切板历史主窗口"""

    closed = pyqtSignal()

    def __init__(self, host_info: dict):
        super().__init__()
        self._host_info = host_info
        self._watcher = ClipboardWatcher.get()
        self._accent_color = host_info.get("accent_color", "#7B61FF")
        self._last_history_hash = None
        self._drag_pos = QPoint()
        self._current_filter = "all"

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 560)

        self._build_ui()
        self._apply_theme_style()
        self._load_history()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self._refresh_if_needed)
        self._refresh_timer.start()

    def _rgb_from_hex(self, hex_color: str):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return r, g, b

    def _apply_theme_style(self):
        accent = self._accent_color
        ar, ag, ab = self._rgb_from_hex(accent)
        self.setStyleSheet(f"""
            #MainContainer {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; }}
            #TitleBar {{ border-bottom: 1px solid rgba(229, 231, 235, 0.5); }}
            #WindowTitle {{ font-size: 14px; font-weight: bold; color: #1f2937; }}
            #CloseBtn {{ background: transparent; color: #86868b; border: none; border-radius: 6px; font-size: 16px; }}
            #CloseBtn:hover {{ background: rgba({ar}, {ag}, {ab}, 0.1); color: #1d1d1f; }}
            #ItemCard {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; }}
            #StatusLabel {{ color: #6b7280; font-size: 11px; }}
        """)

    def _build_ui(self):
        # 完整 UI 构建（标题栏 + 过滤栏 + 列表 + 状态栏）
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        # ... 详见 extensions/clipboard/clipboard/widget.py

    def _load_history(self):
        rows = self._watcher.get_history(limit=40, content_type=self._current_filter)
        current_hash = hash(tuple((r[0], r[1]) for r in rows))
        if current_hash == self._last_history_hash:
            return
        self._last_history_hash = current_hash
        self._list_widget.clear()
        ar, ag, ab = self._rgb_from_hex(self._accent_color)
        for row_id, content, content_type, timestamp in rows:
            item = QListWidgetItem(self._list_widget)
            item.setSizeHint(QSize(0, 98))
            card = ClipboardItemWidget(row_id, content, content_type, timestamp,
                                       self._accent_color, ar, ag, ab)
            card.copy_requested.connect(self._handle_copy)
            card.delete_requested.connect(self._handle_delete)
            card.clicked.connect(lambda c, t: self._handle_copy(c, t))
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, card)

    def _handle_copy(self, content, content_type):
        clipboard = QApplication.clipboard()
        if content_type == "image":
            img_path = DATA_DIR / "clipboard_images" / content
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                clipboard.setPixmap(pixmap)
        elif content_type == "file":
            mime = QMimeData()
            urls = [QUrl.fromLocalFile(p) for p in content.strip().split("\n")]
            mime.setUrls(urls)
            clipboard.setMimeData(mime)
        else:
            clipboard.setText(content)
        try:
            subprocess.Popen(["notify-send", "-a", "umi-float", "已复制到剪切板"])
        except Exception:
            pass
        self.closed.emit()

    def _handle_delete(self, row_id):
        self._watcher.delete_item(row_id)
        self._load_history()

    def _refresh_if_needed(self):
        if self.isVisible():
            self._load_history()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        super().closeEvent(event)
```

> 完整代码见 `extensions/clipboard/clipboard/widget.py`。
