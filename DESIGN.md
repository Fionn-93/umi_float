# Umi Float UI 设计规范

## 一、设计原则

### 1.1 核心理念
- **极简主义**：减少边框和装饰，通过背景色变化引导交互
- **呼吸感**：合理使用内边距和外边距，不要让文字和控件紧贴边框
- **动态反馈**：所有交互项必须有明显的 hover 状态
- **统一性**：全局使用系统强调色，保持视觉一致性
- **对齐基准**：设置行左侧文字区固定宽度，右侧控件从同一条垂直线开始

### 1.2 信息分层
- 页面背景使用浅灰色 `#f5f6f8`，减少视觉干扰
- 卡片背景使用纯白色 `#ffffff` + 浅灰边框 `#e5e7eb`
- Hover 状态使用微妙的背景色变化

---

## 二、颜色系统

### 2.1 强调色（系统动态）
- **动态获取**：`SystemInfo.get_accent_color()`
- **默认值**：`#0078d4`
- **用途**：按钮、选中状态、聚焦边框、进度条等 UI 控件
- **来源**：UOS 系统设置 → 个性化 → 强调色

### 2.2 预设主题色（应用内）

用于悬浮球、Pie 面板的配色派生。

| 主题键 | 显示名称 | 颜色值 | 分类 |
|--------|----------|--------|------|
| `deepin` | Deepin (默认) | `#2CA7E8` | 经典/原生 |
| `macos` | macOS Blue | `#007AFF` | 经典/原生 |
| `github` | GitHub Green | `#2EA44F` | 经典/原生 |
| `lavender` | 薰衣草紫 | `#7B61FF` | 现代感/清新 |
| `coral` | 珊瑚红 | `#FF6B6B` | 现代感/清新 |
| `forest` | 森林绿 | `#4CAF50` | 现代感/清新 |
| `sunset` | 夕阳橙 | `#FF9F43` | 现代感/清新 |
| `rose` | 玫瑰粉 | `#FF85A2` | 现代感/清新 |
| `steam` | Steam Dark | `#1B2838` | 沉稳/工具 |
| `spotify` | Spotify Green | `#1DB954` | 沉稳/工具 |
| `nvidia` | NVIDIA Green | `#76B900` | 沉稳/工具 |

**使用方式**：
```python
from utils.theme_colors import PRESET_THEMES, DEFAULT_THEME, theme_from_key

colors = theme_from_key('deepin')
```

### 2.3 文字颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 页面标题 | `#1f2937` | 页面标题（22px Bold） |
| 正文 | `#1f2937` | 主要文字内容 |
| 次要文字 | `#6b7280` | 标签、提示文字、描述 |
| 分组标题 | `#6b7280` | 卡片分组标题（大写+letter-spacing） |
| 禁用文字 | `#9ca3af` | placeholder 等 |
| 标题栏文字 | `#111` | 设置中心标题 |
| 关闭按钮 | `#374151` | 标题栏关闭按钮默认色 |

### 2.4 背景颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 窗口外壳 | `#f5f6f8` | 设置对话框外层 shell |
| 卡片背景 | `#ffffff` | Card 组件背景 |
| 导航列表 | `#ffffff` | 侧边栏导航背景 |
| 输入框/下拉框 | `#f4f6f8` | QLineEdit、QComboBox 背景 |
| Hover 背景 | `rgba(0,0,0,0.03)` | 设置行悬停 |

### 2.5 边框颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 卡片边框 | `#e5e7eb` | Card、NavList、QComboBox 下拉菜单边框 |
| 外壳边框 | `#e5e7eb` | Shell 边框 |
| 行悬停边框 | `#d1d5db` | 关闭按钮 pressed 状态 |
| 插件项边框 | `#e5e5e5` | 插件列表项默认边框 |

---

## 三、字体规范

### 3.1 字体族
- **默认字体**：跟随系统默认
- **等宽字体**：`monospace`（数值显示）

### 3.2 字号规范

| 用途 | 字号 | 字重 |
|------|------|------|
| 页面标题 | 22px | Bold (700) |
| 分组标题 | 11px | Bold (700) |
| 正文/设置项标题 | 14px | SemiBold (600) |
| 辅助文字/描述 | 12px | Normal |
| 导航项 | 14px | Normal |
| 数值显示 | 12px | Normal |

---

## 四、间距规范

### 4.1 窗口级间距
- 窗口尺寸：`860 x 620`
- 外壳外边距：`14px`
- 内容区内边距：`12px`
- 导航宽度：`200px`

### 4.2 页面级间距
- 页面内边距：`28px 24px`
- 卡片间距：`18px`

### 4.3 组件级间距
- 卡片内边距：`16px`
- 设置行内边距：`18px 14px`
- 设置行间距：`2px`（Card 内部）
- 左侧文字区固定宽度：`240px`
- 右侧控件最小宽度：`200px`

### 4.4 设置行
- 左侧容器固定宽度：`240px`
- 右侧控件 stretch：`1`
- 左侧 stretch：`0`（按需分配）

---

## 五、圆角规范

| 组件 | 圆角值 |
|------|--------|
| 窗口外壳 (shell) | `18px` |
| 卡片 (card) | `16px` |
| 导航列表 (navList) | `16px` |
| 设置行 (row) | `14px` |
| 输入框/下拉框 | `12px` |
| 按钮 | `12px` |
| 下拉菜单项 | `8px` |
| 关闭按钮 | `8px` |

---

## 六、组件规范

### 6.1 按钮

#### 主要按钮（新建/测试连接）
使用 `QPushButton#actionBtn` ID 选择器：
```css
QPushButton#actionBtn {
    height: 38px;
    padding: 0 18px;
    border: none;
    border-radius: 12px;
    background-color: {accent_color};
    color: white;
    font-weight: 600;
}
QPushButton#actionBtn:hover {
    background-color: rgba({r}, {g}, {b}, 0.8);
}
QPushButton#actionBtn:pressed {
    background-color: rgba({r}, {g}, {b}, 0.6);
}
```

#### 次要按钮（编辑/删除）
```css
/* 编辑按钮 */
QPushButton {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    color: #374151;
    font-size: 13px;
    height: 30px;
    padding: 0 8px;
}
QPushButton:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}

/* 删除按钮 */
QPushButton {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    color: #b91c1c;
    font-size: 13px;
    height: 30px;
    padding: 0 8px;
}
QPushButton:hover {
    background: #fee2e2;
    border-color: #f87171;
}
```

#### 关闭按钮
```css
QPushButton#closeBtn {
    color: #374151;
    font-size: 18px;
    font-weight: bold;
    background: transparent;
    border: none;
    border-radius: 8px;
    width: 30px;
    height: 30px;
}
QPushButton#closeBtn:hover {
    background-color: #e5e7eb;
    color: #111827;
}
QPushButton#closeBtn:pressed {
    background-color: #d1d5db;
}
```

#### 尺寸规范
- 主要按钮：自适应宽度，min-width 100px，高度 38px
- 次要按钮：`56 x 30px`
- 关闭按钮：`30 x 30px`

#### 交互
- 所有按钮添加：`setCursor(Qt.PointingHandCursor)`

---

### 6.2 输入框

```css
QLineEdit {
    min-width: 240px;
    height: 38px;
    border: none;
    border-radius: 12px;
    background: #f4f6f8;
    color: #1f2937;
    padding: 0 12px;
}
QLineEdit::placeholder {
    color: #9ca3af;
}
```

---

### 6.3 下拉框

#### 按钮部分
```css
QComboBox {
    height: 38px;
    border: none;
    border-radius: 12px;
    background: #f4f6f8;
    color: #1f2937;
    padding: 0 12px;
    selection-background-color: transparent;
}
QComboBox::drop-down {
    border: none;
}
```

#### 下拉列表
```css
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    selection-background-color: rgba({accent_color}, 0.13);
    outline: none;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    color: #1f2937;
    height: 32px;
    padding-left: 10px;
    border-radius: 8px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: rgba({accent_color}, 0.13);
    color: {accent_color};
}
```

#### 关键代码
```python
view = QListView()
view.setStyleSheet("border: none; background: white;")
combo.setView(view)
```

---

### 6.4 滑块

```css
QSlider::groove:horizontal {
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: {accent_color};
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    background: white;
    border: 2px solid {accent_color};
}
```

**布局行为**：
- Slider 使用 `QSizePolicy.Expanding` 占满右侧空间
- 数值标签固定宽度 `48px`

---

### 6.5 列表项（侧边栏）

```css
QListWidget {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 12px;
    font-size: 14px;
    outline: none;
}
QListWidget::item {
    height: 44px;
    border-radius: 12px;
    padding-left: 14px;
    color: #1f2937;
}
QListWidget::item:selected {
    background: {accent_color};
    color: white;
    font-weight: 600;
}
QListWidget::item:hover:!selected {
    background: rgba(0, 0, 0, 0.04);
}
```

---

### 6.6 卡片 (Card)

```css
#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
}
#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
    letter-spacing: 1px;
    padding: 2px 4px 10px 4px;
}
```

---

### 6.7 设置行 (SettingRow)

```css
#row {
    border-radius: 14px;
}
#row:hover {
    background: rgba(0, 0, 0, 0.03);
}
#rowTitle {
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
}
#rowDesc {
    font-size: 12px;
    color: #6b7280;
}
```

**布局**：
- 左侧容器固定宽度 `240px`
- 右侧控件 stretch=1，占满剩余空间

---

### 6.8 确认对话框

使用自定义 `ConfirmDialog` 替代 `QMessageBox`：

**结构**：
- 标题：16px Bold
- 内容：13px
- 按钮区域：右对齐，间距 8px

**按钮样式**：
- 确认按钮：主要按钮样式（强调色背景）
- 取消按钮：次要按钮样式（白色背景）

---

## 七、交互规范

### 7.1 鼠标指针
- 所有可点击元素添加：`setCursor(Qt.PointingHandCursor)`
- 包括：按钮、列表项、可点击的设置行

### 7.2 焦点状态
- 禁用默认焦点虚线框：`outline: none;`
- 使用边框颜色变化表示焦点状态

### 7.3 Hover 状态
- 所有交互元素必须有 hover 状态
- 使用背景色变化或边框颜色变化

### 7.4 选中状态
- 侧边栏选中：强调色背景 + 白色文字
- 图标选中：强调色边框 + 淡强调色背景
- Tab 选中：强调色下划线

---

## 八、全局样式管理

### 8.1 样式函数
样式统一在 `SettingsDialog.applyStyle()` 中集中管理，通过 `setStyleSheet` 一次性设置到对话框根节点，由 Qt 自动向下传播。

### 8.2 样式表传播陷阱
⚠️ **重要**：当子组件调用 `self.setStyleSheet(...)` 时，会切断从父组件继承样式表的能力。因此：
- `Page` 类**不**应调用 `setStyleSheet`，仅保留 `setAttribute(Qt.WA_StyledBackground, True)`
- 所有样式定义集中在 `SettingsDialog.applyStyle()`
- 需要特殊样式的组件使用 `setObjectName("xxx")` + CSS ID 选择器

### 8.3 强调色获取
```python
from utils.system_info import SystemInfo

accent_color = SystemInfo.get_accent_color()
r = int(accent_color[1:3], 16)
g = int(accent_color[3:5], 16)
b = int(accent_color[5:7], 16)
```

### 8.4 颜色格式
- 固定颜色：`#ffffff`
- 带透明度：`rgba(r, g, b, 0.8)`
- **注意**：Qt5 QSS 不支持 8 位十六进制颜色（如 `#ffffffcc`）

---

## 九、窗口规范

### 9.1 设置对话框
- **窗口标志**：`Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint`
- **透明背景**：`Qt.WA_TranslucentBackground`
- **尺寸**：`860 x 620`
- **外壳**：`#shell` 圆角 18px，背景 `#f5f6f8`，边框 `#e5e7eb`
- **标题栏**：自定义 `TitleBar`，高度 54px，仅保留关闭按钮
- **页面切换**：180ms 淡入动画（`QPropertyAnimation` + `QGraphicsOpacityEffect`）

### 9.2 拖拽
- 整个对话框支持鼠标拖拽移动
- 拖拽逻辑在 `SettingsDialog.mousePressEvent/MoveEvent/ReleaseEvent`

---

## 十、参考实现

| 文件 | 说明 |
|------|------|
| `ui/settings_dialog.py` | 设置页面（主文件，包含所有新组件） |
| `ui/icon_picker_dialog.py` | 图标选择器 |
| `ui/plugin_edit_dialog.py` | 扩展编辑对话框 |
| `ui/confirm_dialog.py` | 确认对话框 |
| `widgets/location_selector.py` | 地区级联选择器 |
| `widgets/plugin_list_item.py` | 插件列表项 |
| `widgets/plugin_list_widget.py` | 插件列表容器 |
