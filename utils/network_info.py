"""
网络流量监控模块
读取 /proc/net/dev 计算实时上下行速率
"""

import time

EXCLUDED_INTERFACES = {"lo", "docker0"}
EXCLUDED_PREFIXES = ("veth", "virbr", "br-", "docker")


def _is_real_interface(name):
    if name in EXCLUDED_INTERFACES:
        return False
    for prefix in EXCLUDED_PREFIXES:
        if name.startswith(prefix):
            return False
    return True


def _read_net_dev():
    stats = {}
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()
            for line in lines[2:]:
                parts = line.strip().split(":")
                if len(parts) != 2:
                    continue
                iface = parts[0].strip()
                if not _is_real_interface(iface):
                    continue
                fields = parts[1].split()
                if len(fields) >= 10:
                    rx_bytes = int(fields[0])
                    tx_bytes = int(fields[8])
                    stats[iface] = {"rx": rx_bytes, "tx": tx_bytes}
    except Exception:
        pass
    return stats


def _format_speed(bytes_per_sec):
    if bytes_per_sec < 0:
        return "0B"
    if bytes_per_sec < 1024:
        return f"{int(bytes_per_sec)}B"
    if bytes_per_sec < 1048576:
        return f"{bytes_per_sec / 1024:.1f}K"
    return f"{bytes_per_sec / 1048576:.1f}M"


class NetworkMonitor:
    _instance = None

    def __init__(self):
        if NetworkMonitor._instance is not None:
            return
        NetworkMonitor._instance = self
        self._prev_stats = _read_net_dev()
        self._prev_time = time.time()

    @staticmethod
    def get():
        if NetworkMonitor._instance is None:
            NetworkMonitor._instance = NetworkMonitor()
        return NetworkMonitor._instance

    def get_speed(self):
        now = time.time()
        cur_stats = _read_net_dev()
        elapsed = now - self._prev_time

        if elapsed <= 0:
            elapsed = 1.0

        total_rx = 0
        total_tx = 0

        for iface, cur in cur_stats.items():
            if iface in self._prev_stats:
                prev = self._prev_stats[iface]
                total_rx += max(0, cur["rx"] - prev["rx"])
                total_tx += max(0, cur["tx"] - prev["tx"])

        self._prev_stats = cur_stats
        self._prev_time = now

        rx_speed = total_rx / elapsed
        tx_speed = total_tx / elapsed

        return {
            "up": tx_speed,
            "down": rx_speed,
            "up_text": _format_speed(tx_speed),
            "down_text": _format_speed(rx_speed),
        }
