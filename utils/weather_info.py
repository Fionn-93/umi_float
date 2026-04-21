"""
天气信息工具模块
调用和风天气 API 获取当前天气
"""
import time
import json
import gzip
import urllib.request
import urllib.error


_CACHE = {
    'data': None,
    'timestamp': 0,
    'ttl': 30 * 60,  # 30 分钟缓存
}

QWEATHER_ICON_MAP = {
    "100": "weather-clear",
    "101": "weather-clear-night",
    "102": "weather-few-clouds",
    "103": "weather-few-clouds-night",
    "104": "weather-overcast",
    "150": "weather-clear",
    "151": "weather-clear-night",
    "300": "weather-showers",
    "301": "weather-showers",
    "302": "weather-storm",
    "303": "weather-storm",
    "304": "weather-storm",
    "305": "weather-showers",
    "306": "weather-showers",
    "307": "weather-showers",
    "308": "weather-storm",
    "309": "weather-showers",
    "310": "weather-storm",
    "311": "weather-showers",
    "312": "weather-showers",
    "313": "weather-freezing-rain",
    "314": "weather-freezing-rain",
    "315": "weather-freezing-rain",
    "399": "weather-showers",
    "400": "weather-snow",
    "401": "weather-snow",
    "402": "weather-snow",
    "403": "weather-snow",
    "404": "weather-snow-rain",
    "405": "weather-snow-rain",
    "406": "weather-snow-rain",
    "407": "weather-snow",
    "408": "weather-snow",
    "409": "weather-snow",
    "499": "weather-snow",
    "500": "weather-fog",
    "501": "weather-fog",
    "502": "weather-fog",
    "503": "weather-fog",
    "504": "weather-fog",
    "507": "weather-fog",
    "508": "weather-fog",
    "509": "weather-fog",
    "510": "weather-fog",
    "511": "weather-fog",
    "512": "weather-fog",
    "513": "weather-fog",
    "514": "weather-fog",
    "515": "weather-fog",
    "900": "weather-clear",
    "901": "weather-clear",
    "999": "weather-clear",
}


def get_icon_name(icon_code):
    """将和风天气 icon code 映射为系统图标名"""
    return QWEATHER_ICON_MAP.get(str(icon_code), "weather-clear")


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
            'icon': get_icon_name(icon_code),
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