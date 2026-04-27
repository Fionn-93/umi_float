"""
剪贴板监听器 - 全局单例，独立于任何 UI 组件
"""

import sqlite3
import time
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from core.constants import DATA_DIR


class ClipboardWatcher:
    """全局剪贴板监听器，单例模式"""

    _instance = None

    def __init__(self):
        self._last_text = ""
        self._db_path = DATA_DIR / "clipboard_history.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._history_limit = 100
        self._init_db()
        self._start_listening()

    @classmethod
    def get(cls) -> "ClipboardWatcher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_db(self):
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                created_at REAL NOT NULL
            )
            """)
        conn.commit()
        conn.close()

    def _start_listening(self):
        clipboard = QApplication.clipboard()
        clipboard.dataChanged.connect(self._on_clipboard_changed)
        try:
            self._last_text = clipboard.text() or ""
        except Exception:
            self._last_text = ""

    def _on_clipboard_changed(self):
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text() or ""
            if text and text != self._last_text:
                self._last_text = text
                self._add_to_history(text, "text")
        except Exception:
            pass

    def _add_to_history(self, content: str, content_type: str = "text"):
        if not content or not content.strip():
            return
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()

        c.execute(
            "SELECT content FROM clipboard_history ORDER BY created_at DESC LIMIT 1"
        )
        last_row = c.fetchone()
        if last_row and last_row[0] == content:
            conn.close()
            return

        c.execute(
            "INSERT INTO clipboard_history (content, content_type, created_at) VALUES (?, ?, ?)",
            (content, content_type, time.time()),
        )

        c.execute("SELECT COUNT(*) FROM clipboard_history")
        count = c.fetchone()[0]
        if count > self._history_limit:
            c.execute(
                "DELETE FROM clipboard_history WHERE id IN ("
                "SELECT id FROM clipboard_history ORDER BY created_at ASC LIMIT ?)",
                (count - self._history_limit,),
            )

        conn.commit()
        conn.close()

    def get_history(self, limit: int = 100):
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute(
            "SELECT id, content, content_type, created_at FROM clipboard_history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def clear_history(self):
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("DELETE FROM clipboard_history")
        conn.commit()
        conn.close()

    def delete_item(self, row_id: int):
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("DELETE FROM clipboard_history WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()
