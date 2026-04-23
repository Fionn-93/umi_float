# Umi-Float 扩展开发手册

## 一、概述

Umi-Float 的扩展系统支持两种执行类型：

| 类型 | 说明 | 执行方式 |
|------|------|----------|
| `command` | Shell 命令 | 通过 `subprocess.Popen(..., shell=True)` 执行外部程序 |
| `python` | Python 模块 | 在主进程内通过 `importlib` 动态加载并调用函数，适合有 UI 或需返回值的功能 |

## 二、目录结构

### 项目内置扩展

```
umi_float/
└── extensions/
    └── <extension_dir>/
        └── manifest.json
        └── xxx.py          # 仅 python 类型需要
```

内置扩展位于仓库根目录的 `extensions/` 下，随项目发布，**不可删除**。

### 用户扩展

```
~/.local/share/umi-float/extensions/
└── <extension_id>/
    └── manifest.json
    └── xxx.py              # 仅 python 类型需要
```

用户扩展位于用户数据目录，可自由增删。

> **注意**：若项目内置扩展与用户扩展的目录名相同，用户扩展会覆盖内置扩展（按目录名匹配，不是 manifest 内的 name）。

## 三、manifest.json 规范

```json
{
  "name": "扩展显示名称",
  "description": "扩展功能描述",
  "icon": "图标名称",
  "exec": "执行命令或 Python 模块名",
  "type": "command | python",
  "enabled": true
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 在面板上显示的名称 |
| `description` | string | 否 | 鼠标悬停时的提示文字 |
| `icon` | string | 是 | 图标名称，详见"图标系统"章节 |
| `exec` | string | 是 | command 类型：shell 命令；python 类型：不含后缀的 `.py` 文件名 |
| `type` | string | 否 | 默认为 `command`；`python` 表示进程内模块 |
| `enabled` | boolean | 否 | 默认为 true |

## 四、类型: `command`

直接通过 shell 执行外部程序，适合打开系统应用或调用工具命令。

**示例：计算器**

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

## 五、类型: `python`

python 类型扩展在主进程内执行，可以访问 PyQt5 的 GUI 环境，适合需要弹出窗口、读取返回值、或与主应用交互的场景。

### 入口函数

扩展目录下的 `.py` 文件**必须**导出以下签名：

```python
def run(context: dict) -> None:
    pass
```

`context` 是 Umi-Float 传入的上下文字典，当前版本包含：

| 键 | 类型 | 说明 |
|----|------|------|
| `app` | `QApplication` | 主应用实例，用于创建窗口、获取屏幕信息等 |

后续版本可能在此字典中增加更多字段，扩展应使用 `context.get("app")` 安全获取。

### 加载机制

插件加载器使用 `importlib.util` 动态加载模块：

1. 根据 `exec` 字段（不含 `.py`）定位扩展目录下的 `.py` 文件
2. 使用 `spec_from_file_location` 创建模块 spec
3. 调用 `module.run(context)` 执行

示例调用链：

```
execute_plugin("color-picker")
  → config.exec = "color_picker"
  → 加载 extensions/color-picker/color_picker.py
  → 调用 run({"app": QApplication.instance()})
```

### 限制与注意事项

- **进程隔离**：扩展运行在主进程中，避免执行耗时操作阻塞 UI；若必须执行长时任务，使用 `QTimer.singleShot` 或 `threading.Thread` 将任务抛到后台
- **命名冲突**：避免使用与 Umi-Float 内部模块相同的变量名（如 `app`、`config`）
- **异常处理**：扩展内未捕获的异常会打印到 stderr，不会导致主应用崩溃
- **资源释放**：若扩展创建了顶层窗口，确保在 `run()` 返回前完成销毁或正确设置生命周期

## 六、图标系统

图标支持两种来源：

### 系统图标

使用 Freedesktop 图标主题名称：

```json
{
  "icon": "accessories-calculator"
}
```

可通过 `QIcon.fromTheme(name)` 渲染。常用图标名参考：

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

可通过 `QIcon(str(DATA_DIR / icon_name))` 加载。

## 七、扩展生命周期

### 加载

应用启动时，`PluginLoader` 会扫描项目内置目录和用户目录，将所有含 `manifest.json` 的子目录注册为扩展。注册时仅读取配置，不执行代码。

### 覆盖配置

扩展的 manifest 是基础配置，用户可在 `~/.config/umi-float/config.json` 的 `plugin_overrides` 字段中覆盖某些显示属性（如显示名、图标、执行命令）：

```json
{
  "plugin_overrides": {
    "<extension_dir>": {
      "name": "自定义名称",
      "icon": "different-icon"
    }
  }
}
```

### 排序

启用的扩展按 `enabled_plugins` 列表顺序排列；禁用的扩展按 `disabled_plugins` 列表顺序排列。两个列表的相对顺序均可通过设置界面拖拽调整。

## 八、示例：command 类型

### manifest

```json
{
  "name": "终端",
  "description": "打开 Deepin 终端",
  "icon": "utilities-terminal",
  "exec": "deepin-terminal",
  "type": "command",
  "enabled": true
}
```

无需额外代码，填好 manifest 即可。

## 九、示例：python 类型 — 取色器

本节以"取色器"扩展为例，展示完整的 python 类型扩展实现。

### 目录结构

```
extensions/color-picker/
├── manifest.json
└── color_picker.py
```

### manifest.json

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

### color_picker.py

```python
"""
取色器扩展 - 从屏幕拾取颜色并复制到剪贴板
"""

import subprocess
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QFont


class ColorPickerWindow(QWidget):
    """取色器主窗口，覆盖全屏，实时显示鼠标位置颜色"""

    def __init__(self, screenshot: QPixmap):
        super().__init__()
        self.screenshot = screenshot
        self.mouse_pos = None
        self.current_color = QColor(0, 0, 0)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose)

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

        self.magnifier_size = 120
        self.magnifier_zoom = 4

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.mouse_pos:
            x, y = self.mouse_pos.x(), self.mouse_pos.y()
            color = self._get_pixel_color(x, y)
            self.current_color = color

            self._draw_magnifier(painter, self.mouse_pos, color)

    def _get_pixel_color(self, x: int, y: int) -> QColor:
        if 0 <= x < self.screenshot.width() and 0 <= y < self.screenshot.height():
            return self.screenshot.toImage().pixelColor(x, y)
        return QColor(0, 0, 0)

    def _draw_magnifier(self, painter: QPainter, pos, color: QColor):
        mx, my = pos.x(), pos.y()

        half = self.magnifier_size // 2
        mag_left = mx - half
        mag_top = my - half - self.magnifier_size - 20

        bg = painter.background()
        painter.setBackground(Qt.white)
        painter.fillRect(int(mag_left), int(mag_top), self.magnifier_size, self.magnifier_size, Qt.white)

        src_x = max(0, mx - self.magnifier_size // (2 * self.magnifier_zoom))
        src_y = max(0, my - self.magnifier_size // (2 * self.magnifier_zoom))
        src_rect = self.screenshot.copy(int(src_x), int(src_y),
                                       self.magnifier_size // self.magnifier_zoom,
                                       self.magnifier_size // self.magnifier_zoom)
        scaled = src_rect.scaled(self.magnifier_size, self.magnifier_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        painter.drawImage(int(mag_left), int(mag_top), scaled.toImage())

        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(1)
        painter.setPen(pen)
        cx = mag_left + self.magnifier_size / 2
        cy = mag_top + self.magnifier_size / 2
        painter.drawLine(int(cx - 8), int(cy), int(cx + 8), int(cy))
        painter.drawLine(int(cx), int(cy - 8), int(cx), int(cy + 8))
        painter.drawRect(int(mag_left), int(mag_top), self.magnifier_size - 1, self.magnifier_size - 1)

        hex_str = color.name().upper()
        rgb_str = f"rgb({color.red()}, {color.green()}, {color.blue()})"

        label_y = mag_top + self.magnifier_size + 8
        painter.setFont(QFont("monospace", 11))
        painter.setPen(Qt.black)
        painter.drawText(int(mag_left), int(label_y), hex_str)
        painter.drawText(int(mag_left), int(label_y + 18), rgb_str)

        color_patch = QPixmap(24, 24)
        color_patch.fill(color)
        painter.drawPixmap(int(mag_left + self.magnifier_size + 8), int(mag_top + self.magnifier_size - 24), color_patch)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hex_str = self.current_color.name().upper()
            QApplication.clipboard().setText(hex_str)
            try:
                subprocess.Popen(
                    ["notify-send", "取色器", f"已复制 {hex_str} 到剪贴板"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
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
</script>
```

## 十、项目 API 参考

扩展可从以下路径导入所需模块：

| 模块 | 说明 |
|------|------|
| `PyQt5.QtWidgets` | 所有 Qt 控件 |
| `PyQt5.QtCore` | Qt 核心类型（Qt 常量、QTimer 等） |
| `PyQt5.QtGui` | QColor、QPainter、QIcon 等 |
| `core.config` → `get_config()` | 获取 `ConfigManager` 单例，可读取/修改配置 |
| `core.constants` | 常量定义（DATA_DIR、CONFIG_DIR 等） |
| `utils.system_info` | `SystemInfo.get_screen_geometry()` 等工具方法 |

> 注意：不要直接 import 主应用其他模块（如 `main`），避免循环依赖和未定义行为。

## 十一、调试提示

1. **运行时无反应**：`subprocess.Popen` 静默失败时查看终端 stderr 输出
2. **python 类型加载失败**：`print()` 语句在 `run()` 入口处打印确认是否被调用；异常堆栈会被捕获并打印
3. **manifest 字段缺失**：缺少必填字段会导致扩展无法加载，查看启动日志
4. **图标不显示**：检查图标名是否可被 `QIcon.fromTheme()` 识别，或路径是否正确
5. **PYTHONPATH**：运行应用时确保 `PYTHONPATH` 包含项目根目录，否则 import 可能失败

## 十二、扩展打包与分发（可选）

如需将扩展分享给其他用户，可以将扩展目录打包为 zip 文件。接收方只需将解压后的目录放入 `~/.local/share/umi-float/extensions/` 即可，无需重启应用（系统托盘菜单可刷新扩展列表）。