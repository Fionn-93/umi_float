# 剪切板历史插件 — UI 样式规范

> 本规范基于 `DESIGN.md` 全局设计系统，针对剪切板历史插件的 UI 组件制定。
> 插件以**独立窗口模式**运行（`manifest.json: window_mode: "independent"`）。

---

## 一、窗口架构

- **独立窗口**：`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`
- **透明背景**：`setAttribute(Qt.WA_TranslucentBackground)` + 圆角容器
- **拖拽**：`mousePressEvent` / `mouseMoveEvent`
- **阴影**：`QGraphicsDropShadowEffect`（`blurRadius: 25`, `yOffset: 6`, `color: rgba(0,0,0,50)`）
- **尺寸**：`resize(380, 560)`

```
ClipboardWidget
└── QVBoxLayout (margins: 12,12,12,12)
    └── MainContainer (#ffffff, #e5e7eb border, 16px radius)
        ├── TitleBar (54px, 底部分割线 rgba(229,231,235,0.5))
        │   ├── WindowTitle (14px Bold, #1f2937)
        │   └── CloseBtn (32x32, hover: accent 10% bg)
        ├── ClipboardListWidget (透明背景, NoSelection)
        │   └── item → ClipboardItemWidget (90px 高卡片，可单击复制)
        └── Footer (35px, 状态标签)
```

---

## 二、颜色系统

### 2.1 强调色（动态）

通过 `host_info["accent_color"]` 获取，典型值 `#7B61FF`。

```python
def _rgb_from_hex(self, hex_color: str):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r, g, b
```

| Token | 用途 |
|-------|------|
| `rgba({ar},{ag},{ab},0.13)` | 类型标签背景 |
| `rgba({ar},{ag},{ab},0.1)` | 关闭按钮 hover 背景 |
| `rgba({ar},{ag},{ab},0.03)` | 卡片 hover 背景 |
| `rgba({ar},{ag},{ab},0.2)` | 卡片 hover 边框 |

### 2.2 固定颜色 Token

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

---

## 三、字体规范

| 元素 | 字号 | 字重 | 颜色 |
|------|------|------|------|
| WindowTitle | 14px | Bold (700) | `#1f2937` |
| 内容标签 | 13px | Normal | `#1f2937` |
| 类型标签 | 10px | Bold (700) | `{accent}`（中文"文本"/"图片"/"链接"） |
| 时间标签 | 11px | Normal | `#6b7280` |
| 操作按钮 | 11px | Normal | ActionBtn: `#374151` / DeleteBtn: `#b91c1c` |
| 状态标签 | 11px | Normal | `#6b7280` / `{accent}`（反馈时 bold） |

---

## 四、间距规范

| 组件 | 属性 | 值 |
|------|------|-----|
| 根布局 | contentsMargins | `12px 12px 12px 12px` |
| 主容器 | border-radius | `16px` |
| 主容器 | border | `1px solid #e5e7eb` |
| 标题栏 | FixedHeight | `54px` |
| 标题栏 | contentsMargins | `20px 0 10px 0` |
| 卡片 | FixedHeight | `90px` |
| 卡片 | 列表间距 | `98px - 90px = 8px` 上下间距（通过 setSizeHint 控制） |
| 卡片 | contentsMargins | `12px 10px 12px 10px` |
| 底部状态栏 | FixedHeight | `35px` |

---

## 五、圆角规范

| 组件 | 圆角值 |
|------|--------|
| 主容器 | `16px` |
| 卡片 | `10px` |
| 关闭按钮 | `6px` |
| 类型标签 | `4px` |
| 操作按钮（复制/删除） | `6px` |

---

## 六、组件规范

### 6.1 主容器（MainContainer）

```css
#MainContainer {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
}
```

### 6.2 标题栏（TitleBar）

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

### 6.3 关闭按钮（CloseBtn）

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

### 6.4 列表（ClipboardListWidget）

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

### 6.5 卡片条目（ClipboardItemWidget）

卡片整体可点击（单击触发复制），hover 显示操作按钮组。

#### 默认状态
```css
#ItemCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
```

#### Hover 状态
```css
#ItemCard {
    background: rgba({ar}, {ag}, {ab}, 0.03);
    border: 1px solid rgba({ar}, {ag}, {ab}, 0.2);
    border-radius: 10px;
}
```

**注意**：`enterEvent`/`leaveEvent` 动态设置的 stylesheet 会**替换**整个控件的样式，必须完整写 `background` + `border` + `border-radius`。

#### 内容文本截断规则
- 原始内容按 `\n` 分割为多行
- 超过 2 行：只保留前 2 行，第 2 行末尾加 ` ...`
- 不超过 2 行：合并为单行，超 100 字符截断加 ` ...`
- `QLabel` 设置 `wordWrap(True)` + `maximumHeight(48)` 限制显示高度

#### 复制按钮（ActionBtn）
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

#### 删除按钮（DeleteBtn）
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

### 6.6 状态栏

```css
#StatusLabel {
    color: #6b7280;
    font-size: 11px;
}
```

- 默认提示："悬停查看操作"
- 复制反馈："已复制到剪切板"（accent 色，bold）

---

## 七、关键样式约束

| 约束 | 说明 |
|------|------|
| **8位hex禁用** | Qt5 QSS 不支持 `{color}dd`，必须用 `rgba(r,g,b,a)` |
| **WA_TranslucentBackground** | 必须设置，配合 FramelessWindowHint 实现圆角 |
| **QGraphicsDropShadowEffect** | 圆角窗口下 CSS box-shadow 被裁剪，必须用 Qt 效果 |
| **hover 动态样式** | `enterEvent`/`leaveEvent` 内联 setStyleSheet 可行（动态状态无更好方案） |

---

## 八、参考

- 全局设计规范：`DESIGN.md`
- 强调色系统：`utils/theme_colors.py`
- 主设置样式：`ui/settings_dialog.py::applyStyle()`
- 关闭按钮规范：`DESIGN.md §6.1`
- 次要按钮规范：`DESIGN.md §6.1`（编辑/删除按钮样式）
