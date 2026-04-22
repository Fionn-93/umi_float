"""
插件列表容器 - 管理拖拽分组
"""

from typing import List, Tuple
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDragMoveEvent, QDropEvent

from plugins.plugin_base import PluginConfig
from widgets.plugin_list_item import PluginListItem


class DropForwardScrollArea(QScrollArea):
    """支持将拖拽事件转发给内部 widget 的 ScrollArea"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event):
        widget = self.widget()
        if widget and widget.acceptDrops():
            widget.dragEnterEvent(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        widget = self.widget()
        if widget and widget.acceptDrops():
            pos = self.viewport().mapTo(widget, event.pos())
            from PyQt5.QtCore import QMimeData, Qt
            from PyQt5.QtGui import QDragMoveEvent

            new_event = QDragMoveEvent(
                pos,
                event.possibleActions(),
                event.mimeData(),
                event.mouseButtons(),
                event.keyboardModifiers(),
            )
            widget.dragMoveEvent(new_event)
            event.setAccepted(new_event.isAccepted())

    def dropEvent(self, event):
        widget = self.widget()
        if widget and widget.acceptDrops():
            pos = self.viewport().mapTo(widget, event.pos())
            from PyQt5.QtCore import QMimeData, Qt
            from PyQt5.QtGui import QDropEvent

            new_event = QDropEvent(
                pos,
                event.possibleActions(),
                event.mimeData(),
                event.mouseButtons(),
                event.keyboardModifiers(),
            )
            widget.dropEvent(new_event)
            event.setAccepted(new_event.isAccepted())
        else:
            event.ignore()


class PluginListWidget(QWidget):
    """插件列表容器"""

    order_changed = pyqtSignal()
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Tuple[str, PluginListItem]] = []
        self._current_drag_item = None
        self._highlighted_section = None

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background-color: #f6f6f6;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 16)
        self._main_layout.setSpacing(16)

        self._enabled_section = self._create_section("已启用")
        self._main_layout.addWidget(self._enabled_section)

        self._disabled_section = self._create_section("已禁用")
        self._main_layout.addWidget(self._disabled_section)
        self._main_layout.addStretch()

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setAcceptDrops(True)

        self._drop_indicator = QFrame(self)
        self._drop_indicator.setFixedHeight(3)
        self._drop_indicator.setStyleSheet("""
            QFrame {
                background: #1976D2;
                border-radius: 1px;
            }
        """)
        self._drop_indicator.hide()

    def _create_section(self, title: str) -> QFrame:
        section = QFrame()
        section.setObjectName(f"section_{title}")
        section.setStyleSheet("""
            #section_{title} {{
                background: transparent;
            }}
        """.format(title=title))

        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        header = QLabel(f"{title} (0)")
        header.setFont(QFont("", 13, QFont.Bold))
        header.setStyleSheet("color: #555; background: transparent;")
        layout.addWidget(header)

        content = QFrame()
        content.setObjectName("sectionContent")
        content.setStyleSheet("""
            #sectionContent {
                background: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                min-height: 60px;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(6)

        placeholder = QLabel("拖拽扩展到此处")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(
            "color: #aaa; font-size: 12px; background: transparent; padding: 16px;"
        )
        placeholder.setObjectName("placeholder")
        content_layout.addWidget(placeholder)

        content.setProperty("header_label", header)

        layout.addWidget(content)

        return section

    def _get_section_content(self, section: QFrame) -> QVBoxLayout:
        if section is None:
            return None
        for child in section.children():
            if child.objectName() == "sectionContent":
                return child.layout()
        return None

    def _get_section_header(self, section: QFrame) -> QLabel:
        for child in section.children():
            if isinstance(child, QVBoxLayout):
                for i in range(child.count()):
                    item = child.itemAt(i)
                    if item and isinstance(item.widget(), QLabel):
                        return item.widget()
        return None

    def set_plugins(
        self,
        enabled: List[Tuple[str, PluginConfig]],
        disabled: List[Tuple[str, PluginConfig]],
    ):
        """设置插件列表"""
        self._clear_section(self._enabled_section)
        self._clear_section(self._disabled_section)
        self._items.clear()

        for plugin_id, config in enabled:
            item = PluginListItem(plugin_id, config.name, config.icon)
            item.edit_requested.connect(self.edit_requested.emit)
            item.delete_requested.connect(self.delete_requested.emit)
            item.drag_started.connect(self._on_drag_started)
            self._add_item_to_section(self._enabled_section, item)
            self._items.append((plugin_id, item))

        for plugin_id, config in disabled:
            item = PluginListItem(plugin_id, config.name, config.icon)
            item.edit_requested.connect(self.edit_requested.emit)
            item.delete_requested.connect(self.delete_requested.emit)
            item.drag_started.connect(self._on_drag_started)
            self._add_item_to_section(self._disabled_section, item)
            self._items.append((plugin_id, item))

        self._update_placeholder(self._enabled_section, len(enabled) == 0)
        self._update_placeholder(self._disabled_section, len(disabled) == 0)

        self._update_section_count(self._enabled_section, len(enabled))
        self._update_section_count(self._disabled_section, len(disabled))

    def _clear_section(self, section: QFrame):
        content_layout = self._get_section_content(section)
        if content_layout is None:
            return

        items_to_remove = []
        for i in range(content_layout.count()):
            item = content_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PluginListItem):
                items_to_remove.append(item.widget())

        for widget in items_to_remove:
            widget.deleteLater()

    def _add_item_to_section(self, section: QFrame, item: PluginListItem):
        content_layout = self._get_section_content(section)
        if content_layout is None:
            return
        content_layout.addWidget(item)

    def _update_section_count(self, section: QFrame, count: int):
        header = self._get_section_header(section)
        if header:
            text = header.text().rsplit(" ", 1)[0]
            header.setText(f"{text} ({count})")

    def _update_placeholder(self, section: QFrame, show: bool):
        """更新占位标签：列表为空时添加，不为空时删除"""
        content_layout = self._get_section_content(section)
        if content_layout is None:
            return

        placeholder = None
        for i in range(content_layout.count()):
            item = content_layout.itemAt(i)
            if item and item.widget() and item.widget().objectName() == "placeholder":
                placeholder = item.widget()
                break

        if show:
            if placeholder is None:
                placeholder = QLabel("拖拽扩展到此处")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet(
                    "color: #aaa; font-size: 12px; background: transparent; padding: 16px;"
                )
                placeholder.setObjectName("placeholder")
                content_layout.addWidget(placeholder)
        else:
            if placeholder is not None:
                content_layout.removeWidget(placeholder)
                placeholder.deleteLater()

    def _on_drag_started(self):
        sender = self.sender()
        if isinstance(sender, PluginListItem):
            self._current_drag_item = sender

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(PluginListItem.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(PluginListItem.MIME_TYPE):
            self._hide_drop_indicator()
            event.ignore()
            return

        drop_pos = event.pos()

        target_section, target_group = self._detect_target_section(drop_pos)

        if target_section is None:
            self._hide_drop_indicator()
            event.ignore()
            return

        plugin_id = bytes(event.mimeData().data(PluginListItem.MIME_TYPE)).decode(
            "utf-8"
        )
        source_is_enabled = any(
            child.plugin_id == plugin_id
            for child in self._enabled_section.findChildren(PluginListItem)
        )
        target_is_enabled = target_group == "enabled"

        if source_is_enabled != target_is_enabled:
            self._highlight_section(target_section)
            self._drop_indicator.hide()
        else:
            self._clear_section_highlight()
            target_layout = self._get_section_content(target_section)
            insert_y = self._calculate_insert_position(
                drop_pos, target_layout, target_section
            )
            if insert_y is not None:
                self._show_drop_indicator_at(insert_y, target_section)

        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._hide_drop_indicator()

    def dropEvent(self, event):
        self._hide_drop_indicator()

        if not event.mimeData().hasFormat(PluginListItem.MIME_TYPE):
            event.ignore()
            return

        plugin_id = bytes(event.mimeData().data(PluginListItem.MIME_TYPE)).decode(
            "utf-8"
        )
        drop_pos = event.pos()

        target_section = None
        target_group = None

        enabled_content = self._get_section_content(self._enabled_section)
        disabled_content = self._get_section_content(self._disabled_section)

        if enabled_content and enabled_content.parent():
            content_widget = enabled_content.parent()
            content_rect = content_widget.rect()
            content_top_left = content_widget.mapTo(self, content_rect.topLeft())
            local_rect = content_rect.translated(content_top_left)
            if local_rect.contains(drop_pos):
                target_section = self._enabled_section
                target_group = "enabled"

        if target_section is None and disabled_content and disabled_content.parent():
            content_widget = disabled_content.parent()
            content_rect = content_widget.rect()
            content_top_left = content_widget.mapTo(self, content_rect.topLeft())
            local_rect = content_rect.translated(content_top_left)
            if local_rect.contains(drop_pos):
                target_section = self._disabled_section
                target_group = "disabled"

        if target_section is None:
            event.ignore()
            return

        target_layout = (
            enabled_content if target_group == "enabled" else disabled_content
        )

        source_is_enabled = False
        for child in self._enabled_section.findChildren(PluginListItem):
            if child.plugin_id == plugin_id:
                source_is_enabled = True
                break

        target_is_enabled = target_group == "enabled"

        if source_is_enabled != target_is_enabled:
            self._handle_cross_group_move(plugin_id, target_group)
        else:
            new_index = self._calculate_drop_index(drop_pos, target_layout)
            self._handle_reorder(plugin_id, new_index, target_group)

        event.acceptProposedAction()
        self.order_changed.emit()

    def _calculate_drop_index(self, pos, layout) -> int:
        if layout is None or layout.count() == 0:
            return 0

        actual_index = 0
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.objectName() == "placeholder":
                    continue

                widget_rect = widget.rect()
                widget_top_left = widget.mapTo(self, widget_rect.topLeft())
                local_rect = widget_rect.translated(widget_top_left)
                center_y = local_rect.top() + local_rect.height() // 2
                if pos.y() < center_y:
                    return actual_index
                actual_index += 1

        return actual_index

    def _handle_cross_group_move(self, plugin_id: str, target_group: str):
        from plugins.plugin_manager import PluginManager

        pm = PluginManager.get()

        if target_group == "enabled":
            pm.enable_plugin(plugin_id)
        else:
            pm.disable_plugin(plugin_id)

    def _handle_reorder(self, plugin_id: str, new_index: int, group: str):
        from plugins.plugin_manager import PluginManager

        pm = PluginManager.get()

        cfg = pm.loader._config.get()
        if group == "enabled":
            plugins_list = list(cfg.get("enabled_plugins", []))
        else:
            plugins_list = list(cfg.get("disabled_plugins", []))

        old_index = plugins_list.index(plugin_id) if plugin_id in plugins_list else -1

        if old_index == -1:
            return

        if new_index > old_index:
            new_index -= 1

        if new_index == old_index:
            return

        pm.move_plugin(plugin_id, new_index, group)

    def refresh(self):
        """刷新列表"""
        from plugins.plugin_manager import PluginManager

        pm = PluginManager.get()
        enabled, disabled = pm.get_ordered_plugins()
        self.set_plugins(enabled, disabled)

    def _detect_target_section(self, pos):
        """检测拖拽位置对应的目标分组"""
        enabled_content = self._get_section_content(self._enabled_section)
        disabled_content = self._get_section_content(self._disabled_section)

        if enabled_content and enabled_content.parent():
            content_widget = enabled_content.parent()
            content_rect = content_widget.rect()
            content_top_left = content_widget.mapTo(self, content_rect.topLeft())
            local_rect = content_rect.translated(content_top_left)
            if local_rect.contains(pos):
                return self._enabled_section, "enabled"

        if disabled_content and disabled_content.parent():
            content_widget = disabled_content.parent()
            content_rect = content_widget.rect()
            content_top_left = content_widget.mapTo(self, content_rect.topLeft())
            local_rect = content_rect.translated(content_top_left)
            if local_rect.contains(pos):
                return self._disabled_section, "disabled"

        return None, None

    def _calculate_insert_position(self, pos, layout, section):
        """计算插入指示器的 Y 坐标位置"""
        if layout is None:
            return None

        content_widget = None
        for child in section.children():
            if child.objectName() == "sectionContent":
                content_widget = child
                break

        if content_widget is None:
            return None

        content_top_left = content_widget.mapTo(self, content_widget.rect().topLeft())
        content_inner_rect = content_widget.rect()
        content_inner_top = content_top_left.y() + 8

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.objectName() == "placeholder":
                    continue
                widget_rect = widget.rect()
                widget_top_left = widget.mapTo(self, widget_rect.topLeft())
                local_rect = widget_rect.translated(widget_top_left)
                center_y = local_rect.top() + local_rect.height() // 2
                if pos.y() < center_y:
                    return local_rect.top() - 4

        last_bottom = content_inner_top
        for i in range(layout.count() - 1, -1, -1):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.objectName() == "placeholder":
                    continue
                widget_rect = widget.rect()
                widget_top_left = widget.mapTo(self, widget_rect.topLeft())
                local_rect = widget_rect.translated(widget_top_left)
                last_bottom = local_rect.bottom() + 4
                break

        return last_bottom

    def _show_drop_indicator_at(self, y_pos, section):
        """在指定位置显示拖拽指示器"""
        content_widget = None
        for child in section.children():
            if child.objectName() == "sectionContent":
                content_widget = child
                break

        if content_widget is None:
            return

        content_top_left = content_widget.mapTo(self, content_widget.rect().topLeft())
        content_rect = content_widget.rect()

        self._drop_indicator.setFixedWidth(content_rect.width() - 40)
        self._drop_indicator.move(content_top_left.x() + 20, int(y_pos))
        self._drop_indicator.show()

    def _highlight_section(self, section):
        """高亮目标分组"""
        if self._highlighted_section and self._highlighted_section != section:
            self._clear_section_highlight()

        content_widget = None
        for child in section.children():
            if child.objectName() == "sectionContent":
                content_widget = child
                break

        if content_widget:
            content_widget.setStyleSheet("""
                #sectionContent {
                    background: #ffffff;
                    border: 2px solid #1976D2;
                    border-radius: 8px;
                    min-height: 60px;
                }
            """)
            self._highlighted_section = section

    def _clear_section_highlight(self):
        """清除分组高亮"""
        if self._highlighted_section:
            content_widget = None
            for child in self._highlighted_section.children():
                if child.objectName() == "sectionContent":
                    content_widget = child
                    break

            if content_widget:
                content_widget.setStyleSheet("""
                    #sectionContent {
                        background: #ffffff;
                        border: 1px solid #e5e5e5;
                        border-radius: 8px;
                        min-height: 60px;
                    }
                """)
            self._highlighted_section = None

    def _hide_drop_indicator(self):
        """隐藏拖拽指示器"""
        self._drop_indicator.hide()
        self._clear_section_highlight()
        self._current_drag_item = None
