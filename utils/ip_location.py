"""
IP 定位工具模块
通过 ip-api.com 获取用户当前的大致位置（经纬度、城市名）
"""
import json
import logging
import urllib.request

from core.constants import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def get_ip_location(timeout=5):
    """通过 IP 获取用户当前位置

    Args:
        timeout: 请求超时时间（秒），默认 5

    Returns:
        dict: {
            "lat": float,       # 纬度
            "lon": float,       # 经度
            "city": str,        # 城市名
            "region": str,      # 省份/地区名
            "country": str,     # 国家名
        }
        获取失败返回 None
    """
    req_no_proxy = urllib.request.Request(
        "http://ip-api.com/json/?lang=zh-CN&fields=status,lat,lon,city,regionName,country",
        headers={"User-Agent": "Umi-Float/0.1"},
    )
    req_https = urllib.request.Request(
        "https://ipapi.co/json/",
        headers={"User-Agent": "Umi-Float/0.1"},
    )

    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req_no_proxy, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") != "success":
            logger.warning("IP 定位失败: status=%s", data.get("status"))
            return None
        city = data.get("city", "")
        lat = data.get("lat")
        lon = data.get("lon")
        logger.info("IP 定位成功: %s (%.4f, %.4f)", city, lat, lon)
        return {
            "lat": lat,
            "lon": lon,
            "city": city,
            "region": data.get("regionName", ""),
            "country": data.get("country", ""),
        }
    except Exception as e:
        logger.warning("ip-api.com 直连失败 (%s)，尝试 ipapi.co...", e)

    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req_https, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if raw.startswith("<"):
                raise ValueError("HTML response")
            data = json.loads(raw)
        if data.get("latitude") is None:
            logger.warning("ipapi.co 失败: %s", data.get("error", "unknown"))
            return None
        city = data.get("city", "")
        lat = data.get("latitude")
        lon = data.get("longitude")
        logger.info("IP 定位成功(ipapi.co): %s (%.4f, %.4f)", city, lat, lon)
        return {
            "lat": lat,
            "lon": lon,
            "city": city,
            "region": data.get("region", ""),
            "country": data.get("country_name", ""),
        }
    except Exception as e:
        logger.warning("ipapi.co 直连失败 (%s)，回退到系统代理...", e)

    try:
        with urllib.request.urlopen(req_https, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if raw.startswith("<"):
                raise ValueError("HTML response")
            data = json.loads(raw)
        if data.get("latitude") is None:
            logger.warning("ipapi.co 代理失败: %s", data.get("error", "unknown"))
            return None
        city = data.get("city", "")
        lat = data.get("latitude")
        lon = data.get("longitude")
        logger.info("IP 定位成功(ipapi.co代理): %s (%.4f, %.4f)", city, lat, lon)
        return {
            "lat": lat,
            "lon": lon,
            "city": city,
            "region": data.get("region", ""),
            "country": data.get("country_name", ""),
        }
    except Exception as e:
        logger.warning("IP 定位最终失败: %s", e)
        return None


def is_default_location(location_id=None, config_dict=None):
    """判断是否为默认位置（北京）"""
    default_id = DEFAULT_CONFIG.get("weather_location", "101010100")
    return location_id == default_id