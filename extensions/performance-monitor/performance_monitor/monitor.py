"""
性能监视器 - 系统数据采集模块
纯函数实现，直接读取 Linux /proc 和 /sys 文件系统
"""

import os
import threading
from pathlib import Path
from typing import Optional, Dict


def _read_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return ""


class SystemMonitor:
    _instance: Optional["SystemMonitor"] = None

    def __init__(self):
        self._lock = threading.Lock()
        self._prev_net: Dict[str, tuple] = {}
        self._prev_disk: Dict[str, tuple] = {}
        self._prev_cpu_times: Optional[tuple] = None
        self._prev_cpu_idle: Optional[float] = None
        self._hwmon_temp_path: Optional[str] = None
        self._discover_hwmon()

    @classmethod
    def get(cls) -> "SystemMonitor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _discover_hwmon(self):
        hwmon_dir = Path("/sys/class/hwmon")
        if not hwmon_dir.exists():
            return
        for d in hwmon_dir.iterdir():
            name_file = d / "name"
            if name_file.exists():
                name = name_file.read_text().strip()
                if name in ("k10temp", "coretemp", "cpu_thermal", "x86_pkg_temp"):
                    temp_input = d / "temp1_input"
                    if temp_input.exists():
                        self._hwmon_temp_path = str(temp_input)
                        return

    def _get_cpu_usage(self) -> float:
        stat = _read_file("/proc/stat")
        lines = stat.split("\n")
        for line in lines:
            if line.startswith("cpu "):
                parts = line.split()
                user, nice, system, idle = (
                    int(parts[1]),
                    int(parts[2]),
                    int(parts[3]),
                    int(parts[4]),
                )
                iowait = int(parts[5]) if len(parts) > 5 else 0
                irq = int(parts[6]) if len(parts) > 6 else 0
                softirq = int(parts[7]) if len(parts) > 7 else 0
                total = user + nice + system + idle + iowait + irq + softirq
                idle_time = idle + iowait
                if self._prev_cpu_times is not None:
                    prev_total, prev_idle = self._prev_cpu_times
                    d_total = total - prev_total
                    d_idle = idle_time - prev_idle
                    if d_total > 0:
                        usage = (d_total - d_idle) / d_total * 100.0
                        self._prev_cpu_times = (total, idle_time)
                        self._prev_cpu_idle = idle_time
                        return usage
                self._prev_cpu_times = (total, idle_time)
                self._prev_cpu_idle = idle_time
                return 0.0
        return 0.0

    def _get_cpu_temp(self) -> float:
        if self._hwmon_temp_path:
            try:
                val = int(_read_file(self._hwmon_temp_path).strip())
                return val / 1000.0
            except Exception:
                pass
        hwmon_dir = Path("/sys/class/hwmon")
        if hwmon_dir.exists():
            for d in hwmon_dir.iterdir():
                temp_input = d / "temp1_input"
                if temp_input.exists():
                    try:
                        val = int(temp_input.read_text().strip())
                        if val > 0:
                            return val / 1000.0
                    except Exception:
                        pass
        return 0.0

    def _get_memory_info(self) -> tuple:
        meminfo = _read_file("/proc/meminfo")
        total = avail = swap_total = swap_free = 0
        for line in meminfo.split("\n"):
            if line.startswith("MemTotal:"):
                total = int(line.split()[1]) * 1024
            elif line.startswith("MemAvailable:"):
                avail = int(line.split()[1]) * 1024
            elif line.startswith("SwapTotal:"):
                swap_total = int(line.split()[1]) * 1024
            elif line.startswith("SwapFree:"):
                swap_free = int(line.split()[1]) * 1024
        used = total - avail
        swap_used = swap_total - swap_free
        return used, total, swap_used, swap_total

    def _get_network_rates(self) -> tuple:
        netdev = _read_file("/proc/net/dev")
        now = {}
        for line in netdev.split("\n"):
            if ":" not in line:
                continue
            iface, data = line.split(":", 1)
            iface = iface.strip()
            if iface in ("lo", "") or iface.startswith("veth"):
                continue
            parts = data.split()
            if len(parts) < 10:
                continue
            r_bytes = int(parts[0])
            t_bytes = int(parts[8])
            now[iface] = (r_bytes, t_bytes)
        rates = {}
        total_rx, total_tx = 0, 0
        with self._lock:
            for iface, (r_bytes, t_bytes) in now.items():
                total_rx += r_bytes
                total_tx += t_bytes
                if iface in self._prev_net:
                    prev_r, prev_t = self._prev_net[iface]
                    rates[iface] = (r_bytes - prev_r, t_bytes - prev_t)
                else:
                    rates[iface] = (0, 0)
            self._prev_net = now
        return rates, total_rx, total_tx

    def _get_disk_stats(self) -> tuple:
        diskstats = _read_file("/proc/diskstats")
        now = {}
        for line in diskstats.split("\n"):
            parts = line.split()
            if len(parts) < 14:
                continue
            major = int(parts[0])
            minor = int(parts[1])
            name = parts[2]
            if major == 7 or name.startswith("loop") or name.startswith("ram"):
                continue
            if not ((major == 8) or (major == 259)):
                continue
            r_completed = int(parts[5])
            w_completed = int(parts[9])
            r_sectors = int(parts[6])
            w_sectors = int(parts[10])
            now[name] = (r_completed, w_completed, r_sectors, w_sectors)
        total_read, total_write = 0, 0
        with self._lock:
            for name, (r_comp, w_comp, r_sec, w_sec) in now.items():
                if name in self._prev_disk:
                    prev_r, prev_w = self._prev_disk[name]
                    total_read += max(0, r_sec - prev_r)
                    total_write += max(0, w_sec - prev_w)
                else:
                    total_read += r_sec
                    total_write += w_sec
            self._prev_disk = {
                (n[0], n[1]): (r, w) for n, (r, w, rs, ws) in now.items()
            }
        return total_read * 512, total_write * 512

    def _get_disk_totals(self) -> tuple:
        diskstats = _read_file("/proc/diskstats")
        total_r, total_w = 0, 0
        for line in diskstats.split("\n"):
            parts = line.split()
            if len(parts) < 14:
                continue
            major = int(parts[0])
            name = parts[2]
            if major == 7 or name.startswith("loop") or name.startswith("ram"):
                continue
            if not ((major == 8) or (major == 259)):
                continue
            total_r += int(parts[6])
            total_w += int(parts[10])
        return total_r * 512, total_w * 512

    def get_all(self) -> dict:
        cpu_usage = self._get_cpu_usage()
        cpu_temp = self._get_cpu_temp()
        mem_used, mem_total, swap_used, swap_total = self._get_memory_info()
        net_rates, total_rx, total_tx = self._get_network_rates()
        disk_read_delta, disk_write_delta = self._get_disk_stats()
        disk_total_r, disk_total_w = self._get_disk_totals()
        total_net_r, total_net_w = 0, 0
        for iface, (r, t) in self._prev_net.items():
            pass
        return {
            "cpu_usage": cpu_usage,
            "cpu_temp": cpu_temp,
            "mem_used": mem_used,
            "mem_total": mem_total,
            "swap_used": swap_used,
            "swap_total": swap_total,
            "net_rates": net_rates,
            "total_rx": total_rx,
            "total_tx": total_tx,
            "disk_read_delta": disk_read_delta,
            "disk_write_delta": disk_write_delta,
            "disk_total_read": disk_total_r,
            "disk_total_write": disk_total_w,
        }


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 0:
        return "0 B"
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_rate(bytes_per_sec: float) -> str:
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    if bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
