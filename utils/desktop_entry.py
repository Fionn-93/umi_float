"""
桌面入口解析器 - 扫描系统中的 .desktop 文件
"""
import locale
import os
import configparser
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AppEntry:
    name: str
    icon: str
    comment: str
    exec: str
    categories: str


DESKTOP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
]


def _get_locale_suffix() -> str:
    try:
        loc = locale.getlocale()[0]
        if loc and "." in loc:
            loc = loc.split(".")[0]
        if loc:
            return f"[{loc}]"
    except Exception:
        pass
    env_lang = os.environ.get("LANG", "")
    if env_lang and "." in env_lang:
        loc = env_lang.split(".")[0]
        if loc:
            return f"[{loc}]"
    return ""


def _clean_exec(exec_str: str) -> str:
    exec_str = exec_str.strip()
    for suffix in ["%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%c", "%k", "%v", "%m"]:
        exec_str = exec_str.replace(suffix, "")
    exec_str = exec_str.strip()
    return exec_str


def _is_valid_desktop_entry(cp: configparser.ConfigParser) -> bool:
    try:
        if not cp.has_section("Desktop Entry"):
            return False
        entry_type = cp.get("Desktop Entry", "Type", fallback="")
        if entry_type != "Application":
            return False
        if cp.has_option("Desktop Entry", "NoDisplay") and cp.getboolean("Desktop Entry", "NoDisplay"):
            return False
        if cp.has_option("Desktop Entry", "Hidden") and cp.getboolean("Desktop Entry", "Hidden"):
            return False
        if not cp.has_option("Desktop Entry", "Exec"):
            return False
        return True
    except Exception:
        return False


def _parse_desktop_file(file_path: str) -> Optional[AppEntry]:
    try:
        cp = configparser.ConfigParser(comment_prefixes="#", strict=False, interpolation=None)
        cp.read(file_path, encoding="utf-8")

        if not _is_valid_desktop_entry(cp):
            return None

        ls = _get_locale_suffix()
        name = cp.get("Desktop Entry", f"Name{ls}", fallback="") or cp.get("Desktop Entry", "Name", fallback="")
        if not name:
            name = cp.get("Desktop Entry", f"GenericName{ls}", fallback="") or cp.get("Desktop Entry", "GenericName", fallback="")
        if not name:
            return None

        icon = cp.get("Desktop Entry", "Icon", fallback="")
        comment = cp.get("Desktop Entry", f"Comment{ls}", fallback="") or cp.get("Desktop Entry", "Comment", fallback="")
        exec_cmd = _clean_exec(cp.get("Desktop Entry", "Exec", fallback=""))
        categories = cp.get("Desktop Entry", "Categories", fallback="")

        return AppEntry(
            name=name,
            icon=icon,
            comment=comment,
            exec=exec_cmd,
            categories=categories,
        )
    except Exception:
        return None


def get_desktop_entries() -> List[AppEntry]:
    entries = []
    seen_names = set()

    for desktop_dir in DESKTOP_DIRS:
        if not os.path.isdir(desktop_dir):
            continue
        for filename in sorted(os.listdir(desktop_dir)):
            if not filename.endswith(".desktop"):
                continue
            file_path = os.path.join(desktop_dir, filename)
            entry = _parse_desktop_file(file_path)
            if entry and entry.name and entry.name not in seen_names and entry.exec:
                seen_names.add(entry.name)
                entries.append(entry)

    entries.sort(key=lambda e: e.name.lower())
    return entries


def filter_entries(entries: List[AppEntry], keyword: str) -> List[AppEntry]:
    if not keyword:
        return entries
    kw = keyword.lower()
    result = []
    for e in entries:
        if kw in e.name.lower() or (e.comment and kw in e.comment.lower()):
            result.append(e)
    return result