#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动定位模块
通过 GPS、WiFi 或 IP 定位获取当前位置，自动计算真太阳时
"""

import sys
import os
import json
from typing import Tuple, Optional, Dict
from datetime import date

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate


class LocationAutoDetector:
    """
    位置自动检测器
    支持多种定位方式：GPS、WiFi、IP 定位
    """
    
    def __init__(self):
        self.calendar = PreciseCalendar()
        self.location_cache = None
    
    def detect_location(self, method: str = 'auto') -> Optional[Dict]:
        """
        检测当前位置
        :param method: 定位方式 ('auto', 'gps', 'wifi', 'ip', 'manual')
        :return: 位置信息字典 {latitude, longitude, city, accuracy}
        """
        if method == 'auto':
            # 自动选择最佳定位方式
            location = self._detect_gps()
            if not location:
                location = self._detect_wifi()
            if not location:
                location = self._detect_ip()
            return location
        elif method == 'gps':
            return self._detect_gps()
        elif method == 'wifi':
            return self._detect_wifi()
        elif method == 'ip':
            return self._detect_ip()
        else:
            return None
    
    def _detect_gps(self) -> Optional[Dict]:
        """
        通过 GPS 定位（如果有 GPS 硬件）
        Windows 系统可以通过 Windows.Devices.Geolocation API
        但 Python 需要通过 ctypes 或其他库访问
        """
        try:
            # 方法 1：尝试使用 Python 的 geolocation 库
            try:
                import geocoder
                g = geocoder.ip('me')
                if g and g.latlng:
                    lat, lng = g.latlng
                    return {
                        'latitude': lat,
                        'longitude': lng,
                        'city': None,
                        'accuracy': 'gps',
                        'source': 'GPS/IP'
                    }
            except ImportError:
                pass
            
            # 方法 2：使用 Windows API（仅 Windows）
            if sys.platform == 'win32':
                return self._detect_windows_location()
            
        except Exception as e:
            print(f"GPS 定位失败：{e}")
        
        return None
    
    def _detect_windows_location(self) -> Optional[Dict]:
        """
        使用 Windows 位置 API
        需要 Windows 10 及以上版本，且已开启定位服务
        """
        try:
            import ctypes
            from ctypes import wintypes
            
            # 这是一个简化版本，实际需要使用 Windows.Devices.Geolocation WinRT API
            # 由于复杂性，我们使用备选方案
            pass
            
        except Exception:
            pass
        
        return None
    
    def _detect_wifi(self) -> Optional[Dict]:
        """
        通过 WiFi 定位（需要访问 Google 或第三方定位服务）
        """
        try:
            # 使用 Google 定位服务（需要 API key）
            # 这里使用免费的 IP 定位作为替代
            return self._detect_ip()
            
        except Exception as e:
            print(f"WiFi 定位失败：{e}")
        
        return None
    
    def _detect_ip(self) -> Optional[Dict]:
        """
        通过 IP 地址定位
        使用免费的 IP 定位服务
        """
        try:
            import urllib.request
            import ssl
            
            # 使用多个 IP 定位服务作为备份
            
            # 服务 1: ipapi.co
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen('https://ipapi.co/json/', context=context, timeout=5)
                data = json.loads(response.read().decode('utf-8'))
                
                if 'latitude' in data and 'longitude' in data:
                    return {
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'city': data.get('city'),
                        'region': data.get('region'),
                        'country': data.get('country_name'),
                        'accuracy': 'ip',
                        'source': 'IP 定位'
                    }
            except Exception:
                pass
            
            # 服务 2: ip-api.com
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen('http://ip-api.com/json/', context=context, timeout=5)
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('status') == 'success':
                    return {
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'accuracy': 'ip',
                        'source': 'IP 定位'
                    }
            except Exception:
                pass
            
            # 服务 3: 备用方案
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen('https://ipinfo.io/json/', context=context, timeout=5)
                data = json.loads(response.read().decode('utf-8'))
                
                if 'loc' in data:
                    loc = data['loc'].split(',')
                    return {
                        'latitude': float(loc[0]),
                        'longitude': float(loc[1]),
                        'city': data.get('city'),
                        'region': data.get('region'),
                        'country': None,
                        'accuracy': 'ip',
                        'source': 'IP 定位'
                    }
            except Exception:
                pass
            
        except Exception as e:
            print(f"IP 定位失败：{e}")
        
        return None
    
    def get_city_by_coordinates(self, lat: float, lng: float) -> Optional[str]:
        """
        根据经纬度获取最近的城市名称
        :param lat: 纬度
        :param lng: 经度
        :return: 城市名称
        """
        min_distance = float('inf')
        nearest_city = None
        
        for city, coords in self.calendar.CITY_COORDINATES.items():
            city_lng, city_lat = coords
            # 计算简单的欧氏距离
            distance = ((lat - city_lat) ** 2 + (lng - city_lng) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_city = city
        
        # 如果距离太远，返回 None
        if min_distance > 5:  # 5 度约 550 公里
            return None
        
        return nearest_city
    
    def get_current_sizhu(self, hour: int, minute: int = 0) -> Optional[Dict]:
        """
        获取当前位置当前的四柱
        :param hour: 小时（24 小时制）
        :param minute: 分钟
        :return: 四柱字典
        """
        from datetime import datetime
        
        # 获取当前位置
        location = self.detect_location()
        
        if not location:
            print("无法获取当前位置，使用默认位置（北京）")
            city_name = '北京'
            longitude, latitude = self.calendar.get_city_coordinates('北京')
        else:
            latitude = location['latitude']
            longitude = location['longitude']
            city_name = location.get('city') or self.get_city_by_coordinates(latitude, longitude)
        
        # 获取当前日期
        now = datetime.now()
        
        # 计算四柱
        if city_name and city_name in self.calendar.CITY_COORDINATES:
            sizhu = get_sizhu_accurate(
                now.year, now.month, now.day,
                hour, minute,
                city_name=city_name
            )
        else:
            sizhu = get_sizhu_accurate(
                now.year, now.month, now.day,
                hour, minute,
                longitude=longitude,
                latitude=latitude
            )
        
        # 添加位置信息
        sizhu['位置'] = {
            '城市': city_name,
            '经度': longitude,
            '纬度': latitude,
            '定位方式': location['accuracy'] if location else '默认'
        }
        
        return sizhu


def test_auto_location():
    """测试自动定位功能"""
    print("=" * 80)
    print("自动定位功能测试")
    print("=" * 80)
    
    detector = LocationAutoDetector()
    
    # 测试定位
    print("\n正在检测您的位置...")
    location = detector.detect_location()
    
    if location:
        print(f"\n✅ 定位成功！")
        print(f"  纬度：{location['latitude']:.4f}")
        print(f"  经度：{location['longitude']:.4f}")
        if location.get('city'):
            print(f"  城市：{location['city']}")
        if location.get('region'):
            print(f"  省份/州：{location['region']}")
        if location.get('country'):
            print(f"  国家：{location['country']}")
        print(f"  定位方式：{location['source']}")
        
        # 计算真太阳时
        from datetime import datetime
        now = datetime.now()
        
        calendar = PreciseCalendar()
        true_solar = calendar._calculate_true_solar_time(
            now.hour, now.minute, location['longitude'], now.date()
        )
        
        time_diff = (true_solar - (now.hour + now.minute/60)) * 60
        
        print(f"\n🕐 时间信息：")
        print(f"  当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  真太阳时：{true_solar:.2f}小时 ({int(true_solar)}:{int((true_solar % 1) * 60):02d})")
        print(f"  时差：{time_diff:.1f}分钟")
        
        # 计算四柱
        sizhu = detector.get_current_sizhu(now.hour, now.minute)
        
        print(f"\n📅 四柱信息：")
        print(f"  {sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")
        print(f"  位置：{sizhu['位置']['城市'] or '未知'} (东经{location['longitude']:.2f}°)")
        
    else:
        print("\n❌ 定位失败，请检查网络连接或手动设置位置")
        
        # 提供手动设置选项
        print("\n请选择您所在的城市：")
        calendar = PreciseCalendar()
        cities = list(calendar.CITY_COORDINATES.keys())
        
        for i, city in enumerate(cities[:20], 1):
            print(f"  {i}. {city}")
        
        print("  ... 更多城市请在代码中查看")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_auto_location()
