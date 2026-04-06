#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间计算系统模块
实现时地支的精确计算和月将的正确添加

功能：
1. 时地支与月将的关联算法
2. 时辰与地支的精确匹配逻辑
3. 月将添加规则的验证机制
"""

import math
from datetime import datetime, date, time

class TimeCalculation:
    """时间计算类"""
    
    # 地支
    DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 时辰与地支对应关系
    SHI_CHEN_MAP = {
        '子时': ('子', 23, 1),
        '丑时': ('丑', 1, 3),
        '寅时': ('寅', 3, 5),
        '卯时': ('卯', 5, 7),
        '辰时': ('辰', 7, 9),
        '巳时': ('巳', 9, 11),
        '午时': ('午', 11, 13),
        '未时': ('未', 13, 15),
        '申时': ('申', 15, 17),
        '酉时': ('酉', 17, 19),
        '戌时': ('戌', 19, 21),
        '亥时': ('亥', 21, 23)
    }
    
    # 月将与月份对应关系（基于节气）
    YUE_JIANG_MAP = {
        '丑': '大寒后',  # 丑将（大吉）
        '子': '雨水后',  # 子将（神后）
        '亥': '春分后',  # 亥将（登明）
        '戌': '谷雨後',  # 戌将（河魁）
        '酉': '小满后',  # 酉将（从魁）
        '申': '夏至后',  # 申将（传送）
        '未': '大暑后',  # 未将（小吉）
        '午': '处暑后',  # 午将（胜光）
        '巳': '秋分后',  # 巳将（太乙）
        '辰': '霜降后',  # 辰将（天罡）
        '卯': '小雪后',  # 卯将（太冲）
        '寅': '冬至后'   # 寅将（功曹）
    }
    
    @classmethod
    def get_hour_zhi(cls, hour, minute=0, second=0):
        """
        根据时间获取时地支
        
        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）
            second: 秒钟（0-59）
            
        Returns:
            str: 时地支
        """
        # 计算总分钟数（精确到秒）
        total_minutes = hour * 60 + minute + second / 60
        
        # 子时特殊处理（23:00-01:00）
        if (hour >= 23) or (hour < 1):
            return '子'
        elif hour >= 1 and hour < 3:
            return '丑'
        elif hour >= 3 and hour < 5:
            return '寅'
        elif hour >= 5 and hour < 7:
            return '卯'
        elif hour >= 7 and hour < 9:
            return '辰'
        elif hour >= 9 and hour < 11:
            return '巳'
        elif hour >= 11 and hour < 13:
            return '午'
        elif hour >= 13 and hour < 15:
            return '未'
        elif hour >= 15 and hour < 17:
            return '申'
        elif hour >= 17 and hour < 19:
            return '酉'
        elif hour >= 19 and hour < 21:
            return '戌'
        else:  # hour >= 21 and hour < 23
            return '亥'
    
    @classmethod
    def calculate_true_solar_time(cls, hour, minute, longitude=120.0, date_obj=None):
        """
        计算真太阳时
        
        Args:
            hour: 北京时间小时
            minute: 北京时间分钟
            longitude: 经度（默认120.0，北京时间）
            date_obj: 日期对象
            
        Returns:
            tuple: (真太阳时小时, 真太阳时分钟)
        """
        if date_obj is None:
            date_obj = datetime.now().date()
        
        # 计算经度时差（每度4分钟）
        longitude_diff = (longitude - 120.0) * 4
        
        # 计算均时差（简化版）
        equation_of_time = cls._calculate_equation_of_time(date_obj)
        
        # 总时差（分钟）
        total_offset = longitude_diff + equation_of_time
        
        # 计算真太阳时
        total_minutes = hour * 60 + minute + total_offset
        
        # 调整到0-1440分钟范围内
        total_minutes = total_minutes % 1440
        if total_minutes < 0:
            total_minutes += 1440
        
        true_hour = int(total_minutes // 60)
        true_minute = int(total_minutes % 60)
        
        return true_hour, true_minute
    
    @classmethod
    def _calculate_equation_of_time(cls, date_obj):
        """
        计算均时差（简化版）
        
        Args:
            date_obj: 日期对象
            
        Returns:
            float: 均时差（分钟）
        """
        # 简化版均时差计算
        # 实际应用中应使用更精确的天文算法
        month = date_obj.month
        day = date_obj.day
        
        # 基于月份的简化均时差表（分钟）
        equation_table = {
            1: -10, 2: -14, 3: -12, 4: -4, 5: 3, 6: 7, 
            7: 6, 8: 0, 9: -6, 10: -12, 11: -15, 12: -11
        }
        
        return equation_table.get(month, 0)
    
    @classmethod
    def get_true_hour_zhi(cls, hour, minute, longitude=120.0, date_obj=None):
        """
        根据真太阳时获取时地支
        
        Args:
            hour: 北京时间小时
            minute: 北京时间分钟
            longitude: 经度
            date_obj: 日期对象
            
        Returns:
            str: 时地支
        """
        true_hour, true_minute = cls.calculate_true_solar_time(hour, minute, longitude, date_obj)
        return cls.get_hour_zhi(true_hour, true_minute)
    
    @classmethod
    def get_tian_pan(cls, yue_jiang, shi_zhi):
        """
        计算天盘（月将加时）
        
        Args:
            yue_jiang: 月将
            shi_zhi: 时地支
            
        Returns:
            dict: 天盘地支映射
        """
        if yue_jiang not in cls.DI_ZHI:
            raise ValueError(f"无效的月将: {yue_jiang}")
        if shi_zhi not in cls.DI_ZHI:
            raise ValueError(f"无效的时地支: {shi_zhi}")
        
        # 计算天盘：月将加时，从时支位置开始顺排
        tian_pan = {}
        
        # 找到时支的位置
        shi_pos = cls.DI_ZHI.index(shi_zhi)
        
        # 从时支位置开始，将月将放入，然后顺排其他地支
        for i, di_zhi in enumerate(cls.DI_ZHI):
            # 计算天盘地支的位置：从月将开始，按顺序排列
            # 公式：(月将索引 + (当前位置 - 时支位置)) % 12
            tian_zhi_idx = (cls.DI_ZHI.index(yue_jiang) + (i - shi_pos)) % 12
            tian_pan[di_zhi] = cls.DI_ZHI[tian_zhi_idx]
        
        return tian_pan
    
    @classmethod
    def validate_yue_jiang_addition(cls, yue_jiang, shi_zhi, tian_pan):
        """
        验证月将添加规则
        
        Args:
            yue_jiang: 月将
            shi_zhi: 时地支
            tian_pan: 天盘
            
        Returns:
            bool: 验证结果
        """
        try:
            # 验证输入参数
            if yue_jiang not in cls.DI_ZHI:
                return False
            if shi_zhi not in cls.DI_ZHI:
                return False
            if not isinstance(tian_pan, dict):
                return False
            
            # 计算期望的天盘
            expected_tian_pan = cls.get_tian_pan(yue_jiang, shi_zhi)
            
            # 验证天盘是否完整
            if len(tian_pan) != len(cls.DI_ZHI):
                return False
            
            # 验证所有地支都存在
            for di_zhi in cls.DI_ZHI:
                if di_zhi not in tian_pan:
                    return False
            
            # 验证天盘是否正确
            for di_zhi, expected_tian_zhi in expected_tian_pan.items():
                if tian_pan[di_zhi] != expected_tian_zhi:
                    return False
            
            # 额外验证：时支位置的天盘地支应该是月将
            if tian_pan[shi_zhi] != yue_jiang:
                return False
            
            return True
        except:
            return False
    
    @classmethod
    def get_shi_chen_info(cls, hour, minute=0):
        """
        获取时辰信息
        
        Args:
            hour: 小时
            minute: 分钟
            
        Returns:
            dict: 时辰信息
        """
        zhi = cls.get_hour_zhi(hour, minute)
        
        # 找到对应的时辰名称
        shi_chen_name = None
        for name, (z, start, end) in cls.SHI_CHEN_MAP.items():
            if z == zhi:
                shi_chen_name = name
                break
        
        return {
            'shi_chen': shi_chen_name,
            'zhi': zhi,
            'start_hour': cls.SHI_CHEN_MAP[shi_chen_name][1],
            'end_hour': cls.SHI_CHEN_MAP[shi_chen_name][2]
        }
    
    @classmethod
    def calculate_time_components(cls, datetime_str):
        """
        计算时间组件
        
        Args:
            datetime_str: 日期时间字符串（格式：YYYY-MM-DD HH:MM:SS）
            
        Returns:
            dict: 时间组件
        """
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        # 计算平太阳时时地支
        ping_zhi = cls.get_hour_zhi(dt.hour, dt.minute, dt.second)
        
        # 计算真太阳时时地支（默认北京经度）
        true_hour, true_minute = cls.calculate_true_solar_time(dt.hour, dt.minute)
        zhen_zhi = cls.get_hour_zhi(true_hour, true_minute)
        
        return {
            'datetime': dt,
            'ping_shi_zhi': ping_zhi,
            'zhen_shi_zhi': zhen_zhi,
            'true_solar_time': f"{true_hour:02d}:{true_minute:02d}"
        }
    
    @classmethod
    def get_complete_time_info(cls, datetime_str, yue_jiang=None, longitude=120.0):
        """
        获取完整的时间信息，包括时地支与月将的关联
        
        Args:
            datetime_str: 日期时间字符串
            yue_jiang: 月将（可选）
            longitude: 经度
            
        Returns:
            dict: 完整时间信息
        """
        components = cls.calculate_time_components(datetime_str)
        dt = components['datetime']
        
        # 获取时辰信息
        shi_chen_info = cls.get_shi_chen_info(dt.hour, dt.minute)
        
        # 计算天盘（如果提供了月将）
        tian_pan = None
        validation_result = None
        if yue_jiang:
            tian_pan = cls.get_tian_pan(yue_jiang, components['zhen_shi_zhi'])
            validation_result = cls.validate_yue_jiang_addition(yue_jiang, components['zhen_shi_zhi'], tian_pan)
        
        return {
            **components,
            **shi_chen_info,
            'yue_jiang': yue_jiang,
            'tian_pan': tian_pan,
            'validation_result': validation_result,
            'longitude': longitude
        }
    
    @classmethod
    def validate_time_calculation(cls, datetime_str, yue_jiang):
        """
        验证时间计算的完整性
        
        Args:
            datetime_str: 日期时间字符串
            yue_jiang: 月将
            
        Returns:
            dict: 验证结果
        """
        try:
            # 获取完整时间信息
            time_info = cls.get_complete_time_info(datetime_str, yue_jiang)
            
            # 验证月将添加规则
            if time_info['validation_result']:
                return {
                    'valid': True,
                    'message': '时间计算验证通过',
                    'data': time_info
                }
            else:
                return {
                    'valid': False,
                    'message': '月将添加规则验证失败',
                    'data': time_info
                }
        except Exception as e:
            return {
                'valid': False,
                'message': f'验证过程出错: {str(e)}',
                'data': None
            }

if __name__ == '__main__':
    # 测试代码
    print("=== 时间计算系统测试 ===")
    
    # 测试时地支计算
    print("\n1. 时地支计算测试:")
    test_times = [(23, 30), (0, 30), (1, 30), (12, 0), (20, 0), (5, 30), (15, 45)]
    for hour, minute in test_times:
        zhi = TimeCalculation.get_hour_zhi(hour, minute)
        info = TimeCalculation.get_shi_chen_info(hour, minute)
        print(f"{hour:02d}:{minute:02d} → {info['shi_chen']} ({zhi})")
    
    # 测试真太阳时计算
    print("\n2. 真太阳时计算测试:")
    test_cases = [(10, 0, 116.4), (10, 0, 104.1), (10, 0, 87.6)]  # 北京、成都、乌鲁木齐
    test_date = date(2026, 3, 31)
    for hour, minute, longitude in test_cases:
        true_hour, true_minute = TimeCalculation.calculate_true_solar_time(hour, minute, longitude, test_date)
        zhen_zhi = TimeCalculation.get_hour_zhi(true_hour, true_minute)
        print(f"北京时间 {hour:02d}:{minute:02d} (经度 {longitude}°) → 真太阳时 {true_hour:02d}:{true_minute:02d} → {zhen_zhi}")
    
    # 测试天盘计算
    print("\n3. 天盘计算测试:")
    test_cases = [
        ('亥', '子'),  # 月将亥，时支子
        ('亥', '丑'),  # 月将亥，时支丑
        ('子', '子'),  # 月将子，时支子
        ('丑', '卯'),  # 月将丑，时支卯
        ('寅', '辰'),  # 月将寅，时支辰
        ('卯', '巳'),  # 月将卯，时支巳
    ]
    for yue_jiang, shi_zhi in test_cases:
        tian_pan = TimeCalculation.get_tian_pan(yue_jiang, shi_zhi)
        print(f"月将: {yue_jiang}, 时支: {shi_zhi}")
        print("天盘:", tian_pan)
        
        # 验证天盘
        valid = TimeCalculation.validate_yue_jiang_addition(yue_jiang, shi_zhi, tian_pan)
        print(f"验证结果: {'✅ 正确' if valid else '❌ 错误'}")
        
        # 验证时支位置的天盘地支是否为月将
        if tian_pan.get(shi_zhi) == yue_jiang:
            print(f"时支位置验证: ✅ 正确（{shi_zhi}位置为{yue_jiang}）")
        else:
            print(f"时支位置验证: ❌ 错误（{shi_zhi}位置应为{yue_jiang}，实际为{tian_pan.get(shi_zhi)}")
        print()
    
    # 测试完整时间组件计算
    print("\n4. 完整时间组件测试:")
    test_datetime = "2026-03-31 10:00:00"
    components = TimeCalculation.calculate_time_components(test_datetime)
    print(f"日期时间: {test_datetime}")
    print(f"平太阳时时地支: {components['ping_shi_zhi']}")
    print(f"真太阳时时地支: {components['zhen_shi_zhi']}")
    print(f"真太阳时: {components['true_solar_time']}")
    
    # 测试完整时间信息
    print("\n5. 完整时间信息测试:")
    test_cases = [
        ("2026-03-31 10:00:00", "亥"),
        ("2026-03-31 12:00:00", "子"),
        ("2026-03-31 14:00:00", "丑")
    ]
    for datetime_str, yue_jiang in test_cases:
        time_info = TimeCalculation.get_complete_time_info(datetime_str, yue_jiang)
        print(f"日期时间: {datetime_str}")
        print(f"月将: {yue_jiang}")
        print(f"时辰: {time_info['shi_chen']}")
        print(f"时地支: {time_info['zhi']}")
        print(f"真太阳时: {time_info['true_solar_time']}")
        print(f"真太阳时时地支: {time_info['zhen_shi_zhi']}")
        print(f"天盘验证: {'✅ 正确' if time_info['validation_result'] else '❌ 错误'}")
        print()
    
    # 测试时间计算验证
    print("\n6. 时间计算验证测试:")
    test_cases = [
        ("2026-03-31 10:00:00", "亥"),
        ("2026-03-31 12:00:00", "子"),
        ("2026-03-31 14:00:00", "丑")
    ]
    for datetime_str, yue_jiang in test_cases:
        validation = TimeCalculation.validate_time_calculation(datetime_str, yue_jiang)
        print(f"日期时间: {datetime_str}")
        print(f"月将: {yue_jiang}")
        print(f"验证结果: {'✅ 通过' if validation['valid'] else '❌ 失败'}")
        print(f"验证消息: {validation['message']}")
        print()
    
    print("\n=== 测试完成 ===")
