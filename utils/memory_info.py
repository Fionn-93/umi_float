"""
内存信息工具模块
读取 /proc/meminfo 获取内存使用率
"""


def get_memory_usage():
    """读取 /proc/meminfo，返回内存使用信息

    Returns:
        dict: {
            'percent': float,    # 使用百分比 0-100
            'total_gb': float,   # 总内存 GB
            'used_gb': float,    # 已用内存 GB
            'available_gb': float # 可用内存 GB
        }
        读取失败时返回 None
    """
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    value = int(parts[1])
                    meminfo[key] = value

        total = meminfo.get("MemTotal", 0)
        available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))

        if total == 0:
            return None

        used = total - available
        percent = (used / total) * 100
        kb_to_gb = 1024 * 1024

        return {
            "percent": round(percent, 1),
            "total_gb": round(total / kb_to_gb, 1),
            "used_gb": round(used / kb_to_gb, 1),
            "available_gb": round(available / kb_to_gb, 1),
        }
    except Exception:
        return None
