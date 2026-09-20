# -*- coding: utf-8 -*-
"""IP → 经纬度定位（在线 API 多级 fallback + 内存缓存）
用于实际排盘时按访问者 IP 定位经纬度，供真太阳时昼夜判断（天将）。
A/B 评估古例不用此模块（固定浙江坐标 30N/120E）。
"""
import time
import requests

_CACHE = {}          # ip -> (ts, lat, lon, province, city)
_CACHE_TTL = 3600    # 缓存 1 小时


def _fetch(ip, timeout=4):
    """尝试多个免费 API 返回 (lat, lon, province, city)，失败返回 None"""
    # 1. ipwho.is（latitude/longitude 字段，无需 key）
    try:
        url = f'http://ipwho.is/{ip}' if ip else 'http://ipwho.is/'
        d = requests.get(url, timeout=timeout).json()
        if d.get('success') and d.get('latitude') is not None:
            return d['latitude'], d['longitude'], d.get('region', ''), d.get('city', '')
    except Exception:
        pass
    # 2. ipinfo.io（loc 字段 "lat,lon"，无需 key）
    try:
        url = f'https://ipinfo.io/{ip}/json' if ip else 'https://ipinfo.io/json'
        d = requests.get(url, timeout=timeout).json()
        loc = d.get('loc', '')
        if loc and ',' in loc:
            lat, lon = loc.split(',')
            return float(lat), float(lon), d.get('region', ''), d.get('city', '')
    except Exception:
        pass
    return None


def ip_to_coords(ip=None, timeout=4):
    """IP → (lat, lon, province, city)。失败返回 (None, None, '', '')。
    带 1 小时内存缓存，避免每次排盘重复请求 API。
    """
    key = ip or 'local'
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _CACHE_TTL:
        return hit[1], hit[2], hit[3], hit[4]
    r = _fetch(ip, timeout)
    if r is None:
        return None, None, '', ''
    lat, lon, prov, city = r
    _CACHE[key] = (time.time(), lat, lon, prov, city)
    return lat, lon, prov, city


def get_client_ip(request):
    """从 Flask request 取客户端 IP（优先 X-Forwarded-For，代理场景）"""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or ''
