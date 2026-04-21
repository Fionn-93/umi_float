# Umi Float UI 设计规范

## 一、设计原则

### 1.1 核心理念
- **极简主义**：减少边框和装饰，通过背景色变化引导交互
- **呼吸感**：合理使用内边距和外边距，不要让文字和控件紧贴边框
- **动态反馈**：所有交互项必须有明显的 hover 状态
- **统一性**：全局使用系统强调色，保持视觉一致性

### 1.2 信息分层
- 页面背景使用纯白色，减少视觉干扰
- 分组标题使用浅灰色背景区分
- Hover 状态使用微妙的背景色变化

---

## 二、颜色系统

### 2.1 强调色
- **动态获取**：`SystemInfo.get_accent_color()`
- **默认值**：`#0078d4`
- **用途**：按钮、选中状态、聚焦边框、进度条等

### 2.2 文字颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 标题 | `#1d1d1f` | 页面标题 |
| 正文 | `#333333` | 主要文字内容 |
| 次要文字 | `#888888` | 标签、提示文字 |
| 分组标题 | `#8e8e93` | 分组标题文字 |
| 禁用文字 | `#aaaaaa` | 禁用状态文字 |

### 2.3 背景颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 页面背景 | `#ffffff` | 主要内容区域 |
| 侧边栏背景 | `#f7f7f7` | 导航区域 |
| Hover 背景 | `#fafafa` | 鼠标悬停状态 |
| 分组标题背景 | `#fafafa` | 预览区、分隔区域 |
| 输入框背景 | `#ffffff` | 文本输入框 |

### 2.4 边框颜色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 默认边框 | `#e0e0e0` | 输入框、按钮边框 |
| 分隔线 | `#f0f0f0` | 分组分隔 |
| Hover 边框 | `#d0d0d0` | 鼠标悬停状态 |
| 聚焦边框 | 强调色 | 输入框聚焦状态 |
| 侧边栏分隔线 | `#eeeeee` | 侧边栏与内容区分隔 |

---

## 三、字体规范

### 3.1 字体族
- **默认字体**：跟随系统默认
- **等宽字体**：`monospace`（数值显示）

### 3.2 字号规范

| 用途 | 字号 | 字重 |
|------|------|------|
| 页面标题 | 16px | Bold |
| 分组标题 | 12px | 600 |
| 正文 | 13px | Normal |
| 辅助文字 | 11-12px | Normal |
| 数值显示 | 12px | monospace |

---

## 四、间距规范

### 4.1 页面级间距
- 页面内边距：`16-20px`
- 分组间距：`0px`（使用分隔线替代）

### 4.2 组件级间距
- 分组内边距：`12-16px`
- 行间距：`8-12px`
- 控件间距：`6-10px`

### 4.3 设置行
- 最小高度：`48px`
- 内边距：`12px 16px`

---

## 五、圆角规范

| 组件 | 圆角值 |
|------|--------|
| 按钮 | `6px` |
| 输入框 | `6px` |
| 下拉框 | `6px` |
| 图标按钮 | `6px` |
| 侧边栏选中项 | `8px` |
| 预览区 | `6px` |

---

## 六、组件规范

### 6.1 按钮

#### 主要按钮（确定/新建）
```css
QPushButton {
    background: {accent_color};
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 13px;
}
QPushButton:hover {
    background: rgba({r}, {g}, {b}, 0.8);
}
```

#### 次要按钮（取消）
```css
QPushButton {
    background: #ffffff;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    font-size: 13px;
}
QPushButton:hover {
    background: #f5f5f5;
    border-color: #d0d0d0;
}
```

#### 尺寸规范
- 默认尺寸：`80 x 32px`
- 小尺寸：`60 x 32px`

#### 交互
- 所有按钮添加：`setCursor(Qt.PointingHandCursor)`

---

### 6.2 输入框

```css
QLineEdit {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px;
    font-size: 13px;
    color: #333333;
    background: #ffffff;
}
QLineEdit:focus {
    border-color: {accent_color};
}
```

---

### 6.3 下拉框

#### 按钮部分
```css
QComboBox {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 4px 10px;
    min-width: 120px;
    background: #ffffff;
    color: #333333;
    font-size: 13px;
}
QComboBox:hover {
    border-color: {accent_color};
}
```

#### 下拉列表
- 创建独立的 `QListView` 并设置样式
- 背景色：`#ffffff`
- 选中背景：`rgba({accent_color}, 0.13)`（22 为十六进制透明度约 13%）
- 选中文字：强调色
- 选项高度：`32px`

#### 关键代码
```python
view = QListView()
view.setStyleSheet("color: #333333; background-color: #ffffff;")
combo.setView(view)
```

---

### 6.4 滑块

```css
QSlider::groove:horizontal {
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -6px 0;
    background: #ffffff;
    border: 1px solid #dcdcdc;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    border-color: {accent_color};
}
QSlider::sub-page:horizontal {
    background: {accent_color};
    border-radius: 2px;
}
```

---

### 6.5 列表项（侧边栏）

```css
#navList::item {
    height: 40px;
    padding-left: 15px;
    border-radius: 8px;
    margin: 4px 10px;
    color: #666666;
}
#navList::item:selected {
    background-color: {accent_color};
    color: #ffffff;
    font-weight: 600;
}
#navList::item:hover:!selected {
    background-color: #ececec;
}
```

#### 禁用焦点框
```css
#navList::item:focus {
    outline: none;
}
```

---

### 6.6 确认对话框

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
每个对话框/页面定义 `get_xxx_style(accent_color)` 函数，返回完整样式表。

### 8.2 强调色获取
```python
from utils.system_info import SystemInfo

accent_color = SystemInfo.get_accent_color()
r = int(accent_color[1:3], 16)
g = int(accent_color[3:5], 16)
b = int(accent_color[5:7], 16)
```

### 8.3 颜色格式
- 固定颜色：`#ffffff`
- 带透明度：`rgba(r, g, b, 0.8)`
- **注意**：Qt5 QSS 不支持 8 位十六进制颜色（如 `#ffffffcc`）

---

## 九、参考实现

| 文件 | 说明 |
|------|------|
| `ui/settings_dialog.py` | 设置页面 |
| `ui/icon_picker_dialog.py` | 图标选择器 |
| `ui/plugin_edit_dialog.py` | 扩展编辑对话框 |
| `ui/confirm_dialog.py` | 确认对话框 |
