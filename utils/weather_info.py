"""
天气信息工具模块
调用和风天气 API 获取当前天气
"""
import logging
import time
import json
import gzip
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_CACHE = {
    'data': None,
    'timestamp': 0,
    'ttl': 30 * 60,
}

WEATHER_ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "Weather"

QWEATHER_ICON_MAP = {
    "100": "sun-fill",
    "101": "moon-clear-fill",
    "102": "sun-cloudy-fill",
    "103": "moon-cloudy-fill",
    "104": "cloudy-fill",
    "150": "sun-fill",
    "151": "moon-clear-fill",
    "300": "rainy-fill",
    "301": "heavy-showers-fill",
    "302": "thunderstorms-fill",
    "303": "thunderstorms-fill",
    "304": "thunderstorms-fill",
    "305": "drizzle-fill",
    "306": "rainy-fill",
    "307": "heavy-showers-fill",
    "308": "thunderstorms-fill",
    "309": "drizzle-fill",
    "310": "thunderstorms-fill",
    "311": "heavy-showers-fill",
    "312": "heavy-showers-fill",
    "313": "hail-fill",
    "314": "hail-fill",
    "315": "hail-fill",
    "399": "rainy-fill",
    "400": "snowy-fill",
    "401": "snowy-fill",
    "402": "snowflake-fill",
    "403": "snowflake-fill",
    "404": "drizzle-fill",
    "405": "drizzle-fill",
    "406": "drizzle-fill",
    "407": "snowy-fill",
    "408": "snowy-fill",
    "409": "snowflake-fill",
    "499": "snowy-fill",
    "500": "mist-fill",
    "501": "mist-fill",
    "502": "foggy-fill",
    "503": "foggy-fill",
    "504": "foggy-fill",
    "507": "haze-fill",
    "508": "haze-fill",
    "509": "foggy-fill",
    "510": "foggy-fill",
    "511": "foggy-fill",
    "512": "foggy-fill",
    "513": "foggy-fill",
    "514": "foggy-fill",
    "515": "foggy-fill",
    "900": "sun-fill",
    "901": "sun-fill",
    "999": "sun-fill",
}


def get_icon_path(icon_code):
    """将和风天气 icon code 映射为本地 SVG 图标路径"""
    name = QWEATHER_ICON_MAP.get(str(icon_code), "sun-fill")
    return str(WEATHER_ICONS_DIR / f"{name}.svg")


def clear_weather_cache():
    """清除天气缓存"""
    global _CACHE
    _CACHE['data'] = None
    _CACHE['timestamp'] = 0


def fetch_weather(api_key, location, api_host=None):
    """获取当前天气

    Args:
        api_key: 和风天气 API Key
        location: 城市 ID（如 101010100）
        api_host: API 地址，为 None 时使用默认值

    Returns:
        dict: {
            'icon': str,       # 系统图标名
            'icon_code': str,  # 和风天气 icon code
            'text': str,       # 天气描述（如"晴"）
            'temp': str,       # 温度（如"25"）
            'temp_unit': str,  # 温度单位 "°C"
        }
        失败时返回 None
    """
    if not api_key:
        return None

    if not api_host:
        api_host = "je693837aw.re.qweatherapi.com"

    now = time.time()
    if _CACHE['data'] is not None and (now - _CACHE['timestamp']) < _CACHE['ttl']:
        return _CACHE['data']

    try:
        url = (
            f"https://{api_host}/v7/weather/now"
            f"?key={api_key}&location={location}"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "Umi-Float/0.1",
            "Accept-Encoding": "gzip",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            data = json.loads(gzip.decompress(raw).decode('utf-8'))

        if data.get('code') != '200':
            return None

        now_data = data.get('now', {})
        icon_code = now_data.get('icon', '100')
        text = now_data.get('text', '')
        temp = now_data.get('temp', '--')

        result = {
            'icon': get_icon_path(icon_code),
            'icon_code': icon_code,
            'text': text,
            'temp': temp,
            'temp_unit': '°C',
        }

        _CACHE['data'] = result
        _CACHE['timestamp'] = now
        return result

    except Exception:
        return None


def get_cached_weather():
    """获取缓存的天气数据（不发起网络请求）"""
    return _CACHE['data']


def lookup_city_by_coords(api_key, lat, lon, api_host=None):
    """通过经纬度查找 QWeather 城市 Location ID

    Args:
        api_key: 和风天气 API Key
        lat: 纬度
        lon: 经度
        api_host: API 地址，为 None 时使用默认值

    Returns:
        str: QWeather Location ID（如 "101020100"）
        失败时返回 None
    """
    if not api_key:
        return None

    if not api_host:
        api_host = "je693837aw.re.qweatherapi.com"

    try:
        url = (
            f"https://{api_host}/v7/city/lookup"
            f"?location={lon},{lat}&key={api_key}"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "Umi-Float/0.1",
            "Accept-Encoding": "gzip",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                raw = gzip.decompress(raw)
            except Exception:
                pass
            data = json.loads(raw.decode('utf-8'))

        if data.get('code') != '200':
            logger.warning("城市查找 API 错误: code=%s", data.get('code'))
            return None

        location_list = data.get('location', [])
        if location_list:
            location_id = str(location_list[0].get('id'))
            logger.info("城市查找成功: id=%s", location_id)
            return location_id
        logger.warning("城市查找失败: 未找到 (%.4f, %.4f) 对应的城市", lat, lon)
        return None

    except Exception as e:
        logger.warning("城市查找失败: %s", e)
        return None