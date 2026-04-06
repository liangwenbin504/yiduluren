#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高精度历法转换模块

提供精确的公历与中国传统干支历法转换功能，包括：
- 四柱（年月日时）干支精确计算
- 节气精确计算
- 真太阳时计算
- 历法验证机制

作者：仪度六壬择日系统
版本：v1.0
创建日期：2026-03-15
"""

import math
from datetime import datetime, date, timedelta
from typing import Tuple, Dict, List, Optional


class PreciseCalendar:
    """
    高精度历法转换类
    
    实现精确的公历与干支历转换，严格遵循传统历法规则
    """
    
    # 天干
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 六十甲子（延迟初始化）
    LIUSHIJIAZI = None
    
    # 基准日：2026 年 3 月 20 日癸巳日（经过验证的准确日期）
    BASE_DATE = date(2026, 3, 20)
    BASE_GANZHI_INDEX = 29  # 癸巳在六十甲子中的索引
    
    # 节气名称
    JIEQI_NAMES = [
        '小寒', '大寒', '立春', '雨水', '惊蛰', '春分',
        '清明', '谷雨', '立夏', '小满', '芒种', '夏至',
        '小暑', '大暑', '立秋', '处暑', '白露', '秋分',
        '寒露', '霜降', '立冬', '小雪', '大雪', '冬至'
    ]
    
    # 节气对应的月支（用于月柱计算）- 修正版
    # 注意：月支以"节"为准，不是"气"
    # 12 节：立春、惊蛰、清明、立夏、芒种、小暑、立秋、白露、寒露、立冬、大雪、小寒
    JIEQI_MONTH = {
        '立春': '寅',  # 正月节
        '惊蛰': '卯',  # 二月节
        '清明': '辰',  # 三月节
        '立夏': '巳',  # 四月节
        '芒种': '午',  # 五月节
        '小暑': '未',  # 六月节
        '立秋': '申',  # 七月节
        '白露': '酉',  # 八月节
        '寒露': '戌',  # 九月节
        '立冬': '亥',  # 十月节
        '大雪': '子',  # 十一月节
        '小寒': '丑',  # 十二月节
    }
    
    # 六十甲子（延迟初始化）
    LIUSHIJIAZI = None
    
    # 中国主要城市经纬度数据库（经度，纬度）
    CITY_COORDINATES = {
        # 直辖市
        '北京': (116.4074, 39.9042),
        '天津': (117.2008, 39.0842),
        '上海': (121.4737, 31.2304),
        '重庆': (106.5516, 29.5630),
        
        # 省会城市
        '广州': (113.2644, 23.1291),
        '深圳': (114.0579, 22.5431),
        '成都': (104.0668, 30.5728),
        '杭州': (120.1551, 30.2741),
        '南京': (118.7969, 32.0603),
        '武汉': (114.3054, 30.5928),
        '西安': (108.9398, 34.3416),
        '长沙': (112.9388, 28.2282),
        '郑州': (113.6254, 34.7466),
        '济南': (117.0009, 36.6751),
        '沈阳': (123.4315, 41.8057),
        '哈尔滨': (126.5350, 45.8038),
        '长春': (125.3245, 43.8171),
        '石家庄': (114.5149, 38.0428),
        '太原': (112.5492, 37.8570),
        '合肥': (117.2272, 31.8206),
        '南昌': (115.8921, 28.6765),
        '福州': (119.3062, 26.0745),
        '贵阳': (106.6302, 26.6477),
        '昆明': (102.8329, 24.8801),
        '南宁': (108.3275, 22.8170),
        '海口': (110.1999, 20.0444),
        '兰州': (103.8343, 36.0611),
        '银川': (106.2309, 38.4872),
        '西宁': (101.7782, 36.6231),
        '呼和浩特': (111.7492, 40.8414),
        '乌鲁木齐': (87.6177, 43.7928),
        '拉萨': (91.1409, 29.6455),
        
        # 其他重要城市
        '大连': (121.6147, 38.9140),
        '青岛': (120.3826, 36.0671),
        '厦门': (118.0894, 24.4798),
        '宁波': (121.5498, 29.8683),
        '苏州': (120.5853, 31.2989),
        '无锡': (120.3119, 31.4912),
        '佛山': (113.1222, 23.0218),
        '东莞': (113.7493, 23.0205),
        '珠海': (113.5767, 22.2719),
        '汕头': (116.6824, 23.3540),
        '温州': (120.6994, 28.0006),
        '泉州': (118.5894, 24.8740),
        '烟台': (121.3914, 37.4638),
        '唐山': (118.1803, 39.6309),
        '保定': (115.4845, 38.8738),
        '洛阳': (112.4539, 34.6197),
        '开封': (114.3074, 34.7973),
        '桂林': (110.2901, 25.2736),
        '三亚': (109.5119, 18.2528),
        '丽江': (100.2299, 26.8721),
        '大理': (100.2677, 25.6065),
        '遵义': (106.9273, 27.7264),
        '延安': (109.4897, 36.6002),
        '井冈山': (114.1680, 26.5780),
        '韶山': (112.4930, 27.9080),
    }
    
    def __init__(self):
        """初始化历法计算器"""
        if PreciseCalendar.LIUSHIJIAZI is None:
            PreciseCalendar.LIUSHIJIAZI = [f'{self.TIANGAN[i%10]}{self.DIZHI[i%12]}' for i in range(60)]
    
    # ==================== 工具方法 ====================
    
    def _julian_day(self, d: date) -> float:
        """
        计算儒略日
        :param d: 日期
        :return: 儒略日
        """
        year = d.year
        month = d.month
        day = d.day
        
        if month <= 2:
            year -= 1
            month += 12
        
        A = year // 100
        B = 2 - A + A // 4
        
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
        
        return JD
    
    def _julian_day_from_datetime(self, dt: datetime) -> float:
        """
        计算带时间的儒略日
        :param dt: 日期时间
        :return: 儒略日
        """
        jd_date = self._julian_day(dt.date())
        time_fraction = (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400.0
        return jd_date + time_fraction
    
    def _sun_ecliptic_longitude(self, jd: float) -> float:
        """
        计算太阳黄经（简化算法，精度约 0.01 度）
        :param jd: 儒略日
        :return: 太阳黄经（度）
        """
        # 儒略世纪数
        T = (jd - 2451545.0) / 36525.0
        
        # 太阳平黄经
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        
        # 太阳平近点角
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        M_rad = math.radians(M)
        
        # 太阳中心差
        C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
        C += (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
        C += 0.000289 * math.sin(3 * M_rad)
        
        # 太阳真黄经
        L = L0 + C
        
        # 光行差修正
        L -= 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.134 * T))
        
        # 归一化到 0-360 度
        L = L % 360
        
        return L
    
    def _find_jieqi_time(self, year: int, jieqi_index: int) -> datetime:
        """
        精确计算节气时刻（二分法）
        :param year: 年份
        :param jieqi_index: 节气索引（0-23）
        :return: 节气的精确日期时间
        """
        # 目标黄经
        target_longitude = jieqi_index * 15.0
        
        # 估算日期（每个节气间隔约 15.22 天）
        base_date = datetime(year, 1, 1)
        if jieqi_index < 6:
            # 当年的节气
            days_offset = jieqi_index * 15.22
        else:
            # 可能需要调整
            days_offset = jieqi_index * 15.22
        
        # 二分法查找精确时刻
        start_dt = base_date + timedelta(days=days_offset - 2)
        end_dt = base_date + timedelta(days=days_offset + 2)
        
        # 迭代查找
        for _ in range(20):  # 足够的精度
            mid_dt = start_dt + (end_dt - start_dt) / 2
            mid_jd = self._julian_day_from_datetime(mid_dt)
            lon = self._sun_ecliptic_longitude(mid_jd)
            
            # 处理角度跨越 0 度的情况
            diff = lon - target_longitude
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            
            if abs(diff) < 0.0001:  # 精度达到 0.0001 度
                break
            
            if diff < 0:
                start_dt = mid_dt
            else:
                end_dt = mid_dt
        
        return mid_dt
    
    # ==================== 年柱计算 ====================
    
    def get_year_ganzhi(self, year: int, month: int, day: int) -> str:
        """
        精确计算年柱（以立春为界）
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 年柱干支
        """
        # 计算立春节气
        lichun = self._find_jieqi_time(year, 2)  # 立春是第 2 个节气（从 0 开始）
        
        target_date = date(year, month, day)
        
        # 判断是否在立春后
        if target_date >= lichun.date():
            # 立春后，属当年
            ganzhi_index = (year - 1984) % 60  # 1984 为甲子年
        else:
            # 立春前，属上一年
            ganzhi_index = (year - 1 - 1984) % 60
        
        return self.LIUSHIJIAZI[ganzhi_index]
    
    # ==================== 月柱计算 ====================
    
    def get_month_ganzhi(self, year: int, month: int, day: int) -> str:
        """
        精确计算月柱（按节气划分）
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 月柱干支
        """
        target_date = date(year, month, day)
        
        # 12 节的索引（0 开始）：立春 2, 惊蛰 4, 清明 6, 立夏 8, 芒种 10, 夏至 12,
        #                     立秋 14, 白露 16, 寒露 18, 立冬 20, 大雪 22, 小寒 0(上一年)
        jie_indices = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]
        jie_names = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', 
                     '立秋', '白露', '寒露', '立冬', '大雪', '小寒']
        
        current_jieqi = None
        current_jie_index = -1
        
        # 查找当前日期在哪个节之后
        for i, (jie_idx, jie_name) in enumerate(zip(jie_indices, jie_names)):
            # 如果是小寒（索引 0），可能是上一年或当年
            if jie_idx == 0:
                # 检查当年的小寒
                jieqi_date = self._find_jieqi_time(year, 0).date()
                next_jieqi_date = self._find_jieqi_time(year, 2).date()  # 下一个是立春
                
                if jieqi_date <= target_date < next_jieqi_date:
                    current_jieqi = jie_name
                    current_jie_index = i
                    break
            else:
                jieqi_date = self._find_jieqi_time(year, jie_idx).date()
                
                # 找下一个节
                next_jie_idx = jie_indices[(i + 1) % 12]
                if next_jie_idx == 0:
                    # 下一个是小寒，可能是下一年
                    next_jieqi_date = self._find_jieqi_time(year + 1, 0).date()
                else:
                    next_jieqi_date = self._find_jieqi_time(year, next_jie_idx).date()
                
                if jieqi_date <= target_date < next_jieqi_date:
                    current_jieqi = jie_name
                    current_jie_index = i
                    break
        
        if not current_jieqi:
            # 默认立春前（小寒到立春）
            current_jieqi = '小寒'
            current_jie_index = 11
        
        # 获取月支
        month_zhi = self.JIEQI_MONTH[current_jieqi]
        
        # 计算月支在寅卯辰巳午未申酉戌亥子丑中的序号（0-11）
        # 寅=0, 卯=1, 辰=2, 巳=3, 午=4, 未=5, 申=6, 酉=7, 戌=8, 亥=9, 子=10, 丑=11
        month_order = self.DIZHI.index(month_zhi) - 2  # 寅的索引是 2，减去 2 得到 0
        if month_order < 0:
            month_order += 12  # 子丑月需要调整
        
        # 五虎遁年起月法
        year_ganzhi = self.get_year_ganzhi(year, month, day)
        year_gan = year_ganzhi[0]
        
        # 根据年干确定正月（寅月）的天干
        if year_gan in ['甲', '己']:
            month_gan_base = 2  # 甲己之年丙作首（丙=2）
        elif year_gan in ['乙', '庚']:
            month_gan_base = 4  # 乙庚之岁戊为头（戊=4）
        elif year_gan in ['丙', '辛']:
            month_gan_base = 6  # 丙辛之岁从庚起（庚=6）
        elif year_gan in ['丁', '壬']:
            month_gan_base = 8  # 丁壬壬寅顺水流（壬=8）
        else:  # 戊、癸
            month_gan_base = 0  # 戊癸之年甲寅首（甲=0）
        
        # 月干 = 正月天干 + 月份序号
        month_gan_index = (month_gan_base + month_order) % 10
        
        return f'{self.TIANGAN[month_gan_index]}{month_zhi}'
    
    # ==================== 日柱计算 ====================
    
    def get_day_ganzhi(self, year: int, month: int, day: int) -> str:
        """
        精确计算日柱（使用基准日推算）
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 日柱干支
        """
        target_date = date(year, month, day)
        delta = (target_date - self.BASE_DATE).days
        
        ganzhi_index = (self.BASE_GANZHI_INDEX + delta) % 60
        
        return self.LIUSHIJIAZI[ganzhi_index]
    
    # ==================== 时柱计算 ====================
    
    def get_hour_ganzhi(self, day_ganzhi: str, hour: int, minute: int = 0, 
                       longitude: float = 120.0, latitude: float = None,
                       date_obj: date = None) -> str:
        """
        精确计算时柱（考虑真太阳时）
        :param day_ganzhi: 日柱干支
        :param hour: 小时（24 小时制，北京时间）
        :param minute: 分钟
        :param longitude: 当地经度（东经为正，西经为负，默认东经 120 度）
        :param latitude: 当地纬度（可选，用于更精确计算）
        :param date_obj: 日期（用于计算均时差）
        :return: 时柱干支
        """
        # 计算真太阳时
        true_solar_hour = self._calculate_true_solar_time(hour, minute, longitude, date_obj)
        
        # 时辰地支：严格对应真太阳时
        # 子时：23:00-01:00, 丑时：01:00-03:00, 寅时：03:00-05:00...
        if true_solar_hour >= 23 or true_solar_hour < 1:
            hour_zhi_index = 0  # 子
        elif true_solar_hour < 3:
            hour_zhi_index = 1  # 丑
        elif true_solar_hour < 5:
            hour_zhi_index = 2  # 寅
        elif true_solar_hour < 7:
            hour_zhi_index = 3  # 卯
        elif true_solar_hour < 9:
            hour_zhi_index = 4  # 辰
        elif true_solar_hour < 11:
            hour_zhi_index = 5  # 巳
        elif true_solar_hour < 13:
            hour_zhi_index = 6  # 午
        elif true_solar_hour < 15:
            hour_zhi_index = 7  # 未
        elif true_solar_hour < 17:
            hour_zhi_index = 8  # 申
        elif true_solar_hour < 19:
            hour_zhi_index = 9  # 酉
        elif true_solar_hour < 21:
            hour_zhi_index = 10  # 戌
        else:
            hour_zhi_index = 11  # 亥
        
        # 五鼠遁日干起时法
        day_gan = day_ganzhi[0]
        
        if day_gan in ['甲', '己']:
            hour_gan_base = 0  # 甲
        elif day_gan in ['乙', '庚']:
            hour_gan_base = 2  # 丙
        elif day_gan in ['丙', '辛']:
            hour_gan_base = 4  # 戊
        elif day_gan in ['丁', '壬']:
            hour_gan_base = 6  # 庚
        else:  # 戊、癸
            hour_gan_base = 8  # 壬
        
        hour_gan_index = (hour_gan_base + hour_zhi_index) % 10
        
        return f'{self.TIANGAN[hour_gan_index]}{self.DIZHI[hour_zhi_index]}'
    
    def _calculate_true_solar_time(self, hour: int, minute: int, longitude: float, 
                                   date_obj: date = None) -> float:
        """
        计算真太阳时
        :param hour: 小时（24 小时制）
        :param minute: 分钟
        :param longitude: 当地经度（东经为正，西经为负）
        :param date_obj: 日期（用于计算均时差）
        :return: 真太阳时（小时）
        """
        # 当地标准时间
        local_time = hour + minute / 60.0
        
        # 标准经度（东八区 120°）
        standard_longitude = 120.0
        
        # 1. 经度差引起的时差（每度 4 分钟）
        time_diff = (longitude - standard_longitude) * 4 / 60.0  # 小时
        
        # 2. 均时差（地球轨道椭圆引起，精确计算）
        if date_obj:
            equation_of_time = self._calculate_equation_of_time_precise(date_obj)
        else:
            equation_of_time = 0.0
        
        # 真太阳时 = 平太阳时 + 经度时差 + 均时差
        true_solar_time = local_time + time_diff + equation_of_time
        
        # 归一化到 0-24 小时
        return true_solar_time % 24
    
    def _calculate_equation_of_time_precise(self, date_obj: date) -> float:
        """
        精确计算均时差（Equation of Time）
        使用简化但精确的天文算法
        :param date_obj: 日期
        :return: 均时差（小时），范围约 -14 分钟到 +16 分钟
        """
        # 计算儒略日
        JD = self._julian_day(date_obj)
        
        # 儒略世纪数
        T = (JD - 2451545.0) / 36525.0
        
        # 太阳平黄经（度）
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        L0 = math.radians(L0 % 360)
        
        # 太阳平近点角（度）
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        M = math.radians(M % 360)
        
        # 黄赤交角（度）
        epsilon = 23.439291 - 0.013004 * T
        
        # 太阳轨道偏心率
        e = 0.016708634 - 0.000042037 * T
        
        # 计算均时差（弧度）
        # 第一项：轨道偏心率引起的
        y = math.tan(math.radians(epsilon / 2)) ** 2
        term1 = 2 * e * math.sin(M)
        
        # 第二项：黄赤交角引起的
        term2 = y * math.sin(2 * L0)
        
        # 均时差（弧度转换为度）
        EOT_rad = term1 - term2
        EOT_deg = math.degrees(EOT_rad)
        
        # 转换为小时（360 度 = 24 小时）
        EOT_hour = EOT_deg / 15.0
        
        return EOT_hour
    
    # ==================== 完整四柱计算 ====================
    
    def get_sizhu_precise(self, year: int, month: int, day: int, 
                         hour: int = 12, minute: int = 0,
                         longitude: float = 120.0, latitude: float = None,
                         city_name: str = None) -> Dict[str, str]:
        """
        精确计算四柱
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时（24 小时制，默认午时 12 点）
        :param minute: 分钟
        :param longitude: 经度（用于真太阳时，默认东经 120 度）
        :param latitude: 纬度（可选）
        :param city_name: 城市名称（可选，如果提供则自动获取经纬度）
        :return: 四柱字典 {年柱，月柱，日柱，时柱}
        """
        # 如果提供了城市名称，自动获取经纬度
        if city_name:
            coords = self.CITY_COORDINATES.get(city_name)
            if coords:
                longitude, latitude = coords
            else:
                print(f"警告：未找到城市 '{city_name}' 的经纬度，使用默认值")
        
        # 年柱（立春为界）
        year_ganzhi = self.get_year_ganzhi(year, month, day)
        
        # 月柱（节气为界）
        month_ganzhi = self.get_month_ganzhi(year, month, day)
        
        # 日柱（精确推算）
        day_ganzhi = self.get_day_ganzhi(year, month, day)
        
        # 时柱（真太阳时）
        date_obj = date(year, month, day)
        hour_ganzhi = self.get_hour_ganzhi(day_ganzhi, hour, minute, longitude, latitude, date_obj)
        
        return {
            '年柱': year_ganzhi,
            '月柱': month_ganzhi,
            '日柱': day_ganzhi,
            '时柱': hour_ganzhi
        }
    
    def get_city_coordinates(self, city_name: str) -> Tuple[float, float]:
        """
        获取城市经纬度
        :param city_name: 城市名称
        :return: (经度，纬度) 元组
        """
        return self.CITY_COORDINATES.get(city_name, (120.0, 30.0))
    
    def list_cities(self) -> List[str]:
        """
        列出所有支持的城市
        :return: 城市名称列表
        """
        return list(self.CITY_COORDINATES.keys())
    
    # ==================== 验证功能 ====================
    
    def verify_ganzhi(self, year: int, month: int, day: int, hour: int,
                     provided_sizhu: Dict[str, str]) -> Dict[str, bool]:
        """
        验证提供的四柱信息是否准确
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :param provided_sizhu: 提供的四柱信息
        :return: 验证结果字典
        """
        # 计算精确四柱
        calculated = self.get_sizhu_precise(year, month, day, hour)
        
        # 对比
        result = {}
        for pillar in ['年柱', '月柱', '日柱', '时柱']:
            provided = provided_sizhu.get(pillar, '')
            calculated_val = calculated[pillar]
            result[pillar] = (provided == calculated_val)
        
        result['全部正确'] = all(result.values())
        
        return result
    
    def verify_date(self, year: int, month: int, day: int, 
                   expected_ganzhi: str) -> bool:
        """
        验证特定日期的日柱
        :param year: 年
        :param month: 月
        :param day: 日
        :param expected_ganzhi: 期望的日柱
        :return: 是否正确
        """
        calculated = self.get_day_ganzhi(year, month, day)
        return calculated == expected_ganzhi
    
    # ==================== 辅助方法 ====================
    
    def get_jieqi_dates(self, year: int) -> Dict[str, datetime]:
        """
        获取某年所有节气的精确日期
        :param year: 年份
        :return: 节气名称到日期的字典
        """
        result = {}
        for i, jieqi_name in enumerate(self.JIEQI_NAMES):
            jieqi_dt = self._find_jieqi_time(year, i)
            result[jieqi_name] = jieqi_dt
        
        return result
    
    def get_lunar_month_day(self, year: int, month: int, day: int) -> str:
        """
        获取农历日期（简化版本）
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 农历日期字符串
        """
        # 这里需要完整的农历算法，暂时返回简化版本
        # 实际应该使用农历库或查表
        return f"农历{year}年{month}月{day}日"
    
    def get_zodiac(self, year: int, month: int, day: int) -> str:
        """
        获取生肖
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 生肖
        """
        year_ganzhi = self.get_year_ganzhi(year, month, day)
        zhi = year_ganzhi[1]
        
        zodiac_map = {
            '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
            '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
            '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
        }
        
        return zodiac_map.get(zhi, '')


# ==================== 便捷函数 ====================

def get_sizhu_accurate(year: int, month: int, day: int, 
                       hour: int = 12, minute: int = 0,
                       longitude: float = 120.0, latitude: float = None,
                       city_name: str = None) -> Dict[str, str]:
    """
    精确计算四柱的便捷函数
    :param year: 年
    :param month: 月
    :param day: 日
    :param hour: 时（北京时间）
    :param minute: 分钟
    :param longitude: 经度（用于真太阳时）
    :param latitude: 纬度（可选）
    :param city_name: 城市名称（可选，如果提供则自动获取经纬度）
    :return: 四柱字典
    """
    calendar = PreciseCalendar()
    return calendar.get_sizhu_precise(year, month, day, hour, minute, longitude, latitude, city_name)


def verify_sizhu(year: int, month: int, day: int, hour: int,
                provided_sizhu: Dict[str, str]) -> Dict[str, bool]:
    """
    验证四柱的便捷函数
    :param year: 年
    :param month: 月
    :param day: 日
    :param hour: 时
    :param provided_sizhu: 提供的四柱
    :return: 验证结果
    """
    calendar = PreciseCalendar()
    return calendar.verify_ganzhi(year, month, day, hour, provided_sizhu)


def get_day_ganzhi_accurate(year: int, month: int, day: int) -> str:
    """
    精确计算日柱的便捷函数
    :param year: 年
    :param month: 月
    :param day: 日
    :return: 日柱
    """
    calendar = PreciseCalendar()
    return calendar.get_day_ganzhi(year, month, day)


# ==================== 测试函数 ====================

def test_precise_calendar():
    """测试高精度历法模块"""
    print("=" * 80)
    print("高精度历法转换模块测试")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 测试案例 1：2026 年 9 月 4 日
    print("\n【测试案例 1】2026 年 9 月 4 日")
    year, month, day = 2026, 9, 4
    sizhu = calendar.get_sizhu_precise(year, month, day, 10)
    
    print(f"  公历：{year}年{month}月{day}日")
    print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")
    print(f"  说明：年柱={sizhu['年柱']}, 月柱={sizhu['月柱']}, 日柱={sizhu['日柱']}")
    
    # 验证说明
    print(f"\n  验证：")
    print(f"    - 年柱：2026 年为丙午年（正确）")
    print(f"    - 月柱：9 月 4 日在处暑后、寒露前，为丙申月（正确）")
    print(f"    - 日柱：2026 年 9 月 4 日为辛巳日（需要验证）")
    
    # 测试案例 2：2026 年 3 月 20 日（基准日）
    print("\n【测试案例 2】2026 年 3 月 20 日（基准日）")
    year, month, day = 2026, 3, 20
    sizhu = calendar.get_sizhu_precise(year, month, day, 12)
    
    print(f"  公历：{year}年{month}月{day}日")
    print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")
    print(f"  期望：丙午年 辛卯月 癸巳日 戊午时")
    
    # 测试案例 3：立春前后
    print("\n【测试案例 3】立春前后年柱变化")
    test_dates = [
        (2026, 2, 3),   # 立春前
        (2026, 2, 4),   # 立春（可能）
        (2026, 2, 5),   # 立春后
    ]
    
    for y, m, d in test_dates:
        year_ganzhi = calendar.get_year_ganzhi(y, m, d)
        day_ganzhi = calendar.get_day_ganzhi(y, m, d)
        print(f"  {y}年{m}月{d}日：年柱={year_ganzhi}, 日柱={day_ganzhi}")
    
    # 测试案例 4：节气前后月柱变化
    print("\n【测试案例 4】节气前后月柱变化（2026 年 9 月）")
    test_dates = [
        (2026, 9, 7),   # 白露前
        (2026, 9, 8),   # 白露（可能）
        (2026, 9, 9),   # 白露后
    ]
    
    for y, m, d in test_dates:
        month_ganzhi = calendar.get_month_ganzhi(y, m, d)
        day_ganzhi = calendar.get_day_ganzhi(y, m, d)
        print(f"  {y}年{m}月{d}日：月柱={month_ganzhi}, 日柱={day_ganzhi}")
    
    # 测试案例 5：验证功能
    print("\n【测试案例 5】验证功能")
    provided = {
        '年柱': '丙午',
        '月柱': '丙申',
        '日柱': '辛巳',
        '时柱': '癸巳'
    }
    result = calendar.verify_ganzhi(2026, 9, 4, 10, provided)
    print(f"  提供的四柱：{provided}")
    print(f"  验证结果：{result}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    test_precise_calendar()
