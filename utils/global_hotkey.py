"""
全局快捷键管理模块（X11 XGrabKey 后端）

通过 X11 XGrabKey 在 root window 上注册全局快捷键抓取，配合
QAbstractNativeEventFilter 拦截 xcb KeyPress 事件实现系统级全局快捷键，
不依赖窗口焦点，也不依赖 dde-session-daemon / XEventMonitor 服务。

之前使用 org.deepin.dde.XEventMonitor1 的 D-Bus 信号方案在部分系统上
不再发送 KeyPress 信号，导致快捷键失效，因此改为底层 X11 方案。
"""

import ctypes
import ctypes.util
import logging

from PyQt5.QtCore import QObject, pyqtSignal, QAbstractNativeEventFilter
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# libX11 加载
# ---------------------------------------------------------------------------

_libX11_path = ctypes.util.find_library("X11")
_libX11 = ctypes.cdll.LoadLibrary(_libX11_path) if _libX11_path else None

# X11 常量
_GRAB_MODE_ASYNC = 1

_SHIFT_MASK = 1 << 0
_LOCK_MASK = 1 << 1
_CONTROL_MASK = 1 << 2
_MOD1_MASK = 1 << 3  # Alt
_MOD4_MASK = 1 << 6  # Super/Win

# XCB 事件类型
_XCB_KEY_PRESS = 2

if _libX11 is not None:
    _libX11.XOpenDisplay.restype = ctypes.c_void_p
    _libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    _libX11.XDefaultRootWindow.restype = ctypes.c_ulong
    _libX11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    _libX11.XStringToKeysym.restype = ctypes.c_ulong
    _libX11.XStringToKeysym.argtypes = [ctypes.c_char_p]
    _libX11.XKeysymToKeycode.restype = ctypes.c_int
    _libX11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    _libX11.XGrabKey.restype = ctypes.c_int
    _libX11.XGrabKey.argtypes = [
        ctypes.c_void_p,  # Display*
        ctypes.c_int,  # keycode
        ctypes.c_uint,  # modifiers
        ctypes.c_ulong,  # grab_window
        ctypes.c_int,  # owner_events
        ctypes.c_int,  # pointer_mode
        ctypes.c_int,  # keyboard_mode
    ]
    _libX11.XUngrabKey.restype = None
    _libX11.XUngrabKey.argtypes = [
        ctypes.c_void_p,  # Display*
        ctypes.c_int,  # keycode
        ctypes.c_uint,  # modifiers
        ctypes.c_ulong,  # grab_window
    ]
    _libX11.XFlush.restype = ctypes.c_int
    _libX11.XFlush.argtypes = [ctypes.c_void_p]
    _libX11.XCloseDisplay.restype = ctypes.c_int
    _libX11.XCloseDisplay.argtypes = [ctypes.c_void_p]


class _XCBKeyPressEvent(ctypes.Structure):
    _fields_ = [
        ("response_type", ctypes.c_uint8),
        ("detail", ctypes.c_uint8),  # keycode
        ("sequence", ctypes.c_uint16),
        ("time", ctypes.c_uint32),
        ("root", ctypes.c_uint32),
        ("event", ctypes.c_uint32),
        ("child", ctypes.c_uint32),
        ("root_x", ctypes.c_int16),
        ("root_y", ctypes.c_int16),
        ("event_x", ctypes.c_int16),
        ("event_y", ctypes.c_int16),
        ("state", ctypes.c_uint16),  # 修饰键状态
        ("same_screen", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
    ]


# ---------------------------------------------------------------------------
# 快捷键解析辅助
# ---------------------------------------------------------------------------

_MODIFIER_NAMES = {
    "alt",
    "ctrl",
    "control",
    "shift",
    "super",
    "win",
    "meta",
    "mod1",
    "mod4",
}

# 配置串中修饰键别名 -> 规范 token
_MOD_ALIASES = {
    "control": "ctrl",
    "win": "super",
    "meta": "super",
    "mod4": "super",
    "mod1": "alt",
}

# 规范 token -> X11 modifier mask
_MOD_MASKS = {
    "alt": _MOD1_MASK,
    "ctrl": _CONTROL_MASK,
    "shift": _SHIFT_MASK,
    "super": _MOD4_MASK,
}

# 应忽略的锁定类修饰键组合
# 注意：只包含 CapsLock（LockMask），不包含 NumLock/Mod2Mask 等，
# 因为对同一 keycode 注册多个 XGrabKey 会导致 X11 服务器不发送事件。
_INSENSITIVE_MODS = [0, _LOCK_MASK]


def normalize_shortcut(shortcut: str) -> str:
    """将快捷键串归一化为小写 token。

    'Alt+F'、'alt_f'、'<Alt>f' 均归一化为 'alt+f'。
    """
    s = (
        shortcut.strip()
        .replace("<", " ")
        .replace(">", " ")
        .replace("+", " ")
        .replace("_", " ")
        .replace("-", " ")
        .lower()
    )
    parts = [p for p in s.split() if p]
    mods = sorted(_MOD_ALIASES.get(p, p) for p in parts if p in _MODIFIER_NAMES)
    keys = [p for p in parts if p not in _MODIFIER_NAMES]
    return "+".join(mods + keys)


class _X11EventFilter(QAbstractNativeEventFilter):
    """拦截 X11 xcb KeyPress 事件的 Qt 原生事件过滤器。"""

    def __init__(self, manager: "GlobalHotkeyManager"):
        super().__init__()
        self._manager = manager

    def nativeEventFilter(self, eventType, message):  # pylint: disable=invalid-name
        if eventType != b"xcb_generic_event_t":
            return False, 0
        handled = self._manager.handle_x11_event(message)
        return handled, 0


class GlobalHotkeyManager(QObject):
    """全局快捷键管理器（X11 XGrabKey 后端）"""

    toggle_shortcut_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._display = None
        self._root_window = None
        self._shortcuts = {}  # name -> normalized token
        self._registered = {}  # name -> (keycode, mods)
        self._event_filter = None
        self._filter_installed = False

    # -- 对外接口 ---------------------------------------------------------

    def update(self, shortcuts: dict) -> None:
        """根据配置注册/重注册全局快捷键。

        shortcuts: {"toggle": "Alt+F", "pin": "Ctrl+D"}
        """
        normalized = {}
        for name, value in shortcuts.items():
            token = normalize_shortcut(value or "")
            if token:
                normalized[name] = token
        self.unregister_all()
        self._shortcuts = normalized
        if not normalized:
            logger.info("无快捷键配置，跳过全局快捷键注册")
            return
        self._register()

    def unregister_all(self) -> None:
        """注销全部全局快捷键"""
        for keycode, mods in self._registered.values():
            self._ungrab(keycode, mods)
        self._registered.clear()
        self._shortcuts.clear()
        self._remove_event_filter()
        if self._display is not None:
            _libX11.XFlush(self._display)
            _libX11.XCloseDisplay(self._display)
            self._display = None
            self._root_window = None
        logger.info("全局快捷键已注销")

    # -- 内部实现 ---------------------------------------------------------

    def _ensure_display(self) -> bool:
        if self._display is not None:
            return True
        if _libX11 is None:
            logger.warning("libX11 不可用，全局快捷键不可用")
            return False
        self._display = _libX11.XOpenDisplay(None)
        if not self._display:
            self._display = None
            logger.warning("无法打开 X11 显示，全局快捷键不可用")
            return False
        self._root_window = _libX11.XDefaultRootWindow(self._display)
        return True

    def _parse_shortcut(self, token: str):
        parts = token.split("+")
        mods = 0
        key_name = None
        for part in parts:
            mask = _MOD_MASKS.get(part)
            if mask is not None:
                mods |= mask
            else:
                key_name = part
        if not key_name:
            logger.warning("无法解析快捷键: %s", token)
            return None, 0
        keysym = _libX11.XStringToKeysym(key_name.encode("utf-8"))
        if keysym == 0:
            logger.warning("无法获取键符: %s", key_name)
            return None, 0
        keycode = _libX11.XKeysymToKeycode(self._display, keysym)
        if keycode == 0:
            logger.warning("无法获取键码: %s", key_name)
            return None, 0
        return keycode, mods

    def _register(self) -> None:
        if not self._ensure_display():
            return
        self._install_event_filter()
        for name, token in self._shortcuts.items():
            keycode, mods = self._parse_shortcut(token)
            if keycode is None:
                logger.warning("跳过快捷键 %s", token)
                continue
            ok = self._grab(keycode, mods)
            if ok:
                self._registered[name] = (keycode, mods)
                logger.info(
                    "注册全局快捷键: %s (keycode=%d, mods=0x%x)", token, keycode, mods
                )
            else:
                logger.warning("XGrabKey 失败，快捷键 %s 可能已被占用", token)
        if not self._registered:
            self._remove_event_filter()
            return
        _libX11.XFlush(self._display)

    def _grab(self, keycode: int, mods: int) -> bool:
        """抓取指定 keycode + 修饰键组合，覆盖 CapsLock/NumLock 等状态。"""
        success = False
        for extra in _INSENSITIVE_MODS:
            result = _libX11.XGrabKey(
                self._display,
                keycode,
                mods | extra,
                self._root_window,
                0,  # owner_events = False
                _GRAB_MODE_ASYNC,
                _GRAB_MODE_ASYNC,
            )
            if result != 0:
                success = True
        return success

    def _ungrab(self, keycode: int, mods: int) -> None:
        for extra in _INSENSITIVE_MODS:
            _libX11.XUngrabKey(self._display, keycode, mods | extra, self._root_window)

    def _install_event_filter(self) -> None:
        if self._filter_installed:
            return
        app = QApplication.instance()
        if app is None:
            logger.warning("未找到 QApplication，无法安装事件过滤器")
            return
        self._event_filter = _X11EventFilter(self)
        app.installNativeEventFilter(self._event_filter)
        self._filter_installed = True

    def _remove_event_filter(self) -> None:
        if not self._filter_installed:
            return
        app = QApplication.instance()
        if app is not None and self._event_filter is not None:
            app.removeNativeEventFilter(self._event_filter)
        self._event_filter = None
        self._filter_installed = False

    def handle_x11_event(self, message) -> bool:
        if not self._registered or self._display is None:
            return False
        addr = int(message)
        event = ctypes.cast(addr, ctypes.POINTER(_XCBKeyPressEvent)).contents
        if (event.response_type & 0x7F) != _XCB_KEY_PRESS:
            return False
        keycode = event.detail
        state = event.state
        for name, (expected_keycode, expected_mods) in self._registered.items():
            if keycode == expected_keycode and (state & expected_mods) == expected_mods:
                if name == "toggle":
                    self.toggle_shortcut_triggered.emit()
                return True
        return False
