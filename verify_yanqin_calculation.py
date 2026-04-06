#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证演禽法计算逻辑的准确性
"""

from datetime import datetime
from core_modules.engine.yanqin_analyzer import YanQinAnalyzer

class LunarCalendar:
    """农历工具类"""
    
    # 天干
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    # 地支
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    @staticmethod
    def get_gz(year):
        """获取年干支"""
        # 1900年是庚子年
        base = 1900
        offset = year - base
        tg = (offset + 6) % 10  # 1900年是庚，对应索引6
        dz = (offset + 0) % 12  # 1900年是子，对应索引0
        return f"{LunarCalendar.TIANGAN[tg]}{LunarCalendar.DIZHI[dz]}"
    
    @staticmethod
    def get_month_gz(year, month):
        """获取月干支"""
        # 简化计算，实际需要考虑节气
        # 这里使用近似计算
        month_base = [0, 0, 3, 3, 6, 6, 9, 9, 12, 12, 15, 15]
        if month < 3:
            year -= 1
        tg = (year % 10 + month_base[month-1]) % 10
        dz = (year % 12 + month_base[month-1]) % 12
        return f"{LunarCalendar.TIANGAN[tg]}{LunarCalendar.DIZHI[dz]}"
    
    @staticmethod
    def get_day_gz(year, month, day):
        """获取日干支"""
        # 简化计算，实际需要使用儒积日法
        # 这里使用近似计算
        # 1900年1月1日是庚子日
        base_date = datetime(1900, 1, 1)
        target_date = datetime(year, month, day)
        delta = (target_date - base_date).days
        tg = (delta + 6) % 10  # 1900年1月1日是庚，对应索引6
        dz = (delta + 0) % 12  # 1900年1月1日是子，对应索引0
        return f"{LunarCalendar.TIANGAN[tg]}{LunarCalendar.DIZHI[dz]}"
    
    @staticmethod
    def get_hour_gz(hour):
        """获取时干支"""
        # 23-1点子时，1-3点丑时，以此类推
        shi_zhi_index = (hour + 1) // 2 % 12
        return LunarCalendar.DIZHI[shi_zhi_index]

def verify_yanqin_calculation():
    """验证演禽法计算逻辑"""
    print("=" * 70)
    print("演禽法计算逻辑验证")
    print("=" * 70)
    
    # 获取当前日期
    now = datetime.now()
    year, month, day, hour = now.year, now.month, now.day, now.hour
    
    print(f"当前日期：{year}年{month}月{day}日 {hour}时")
    
    # 计算四柱
    nian_gz = LunarCalendar.get_gz(year)
    yue_gz = LunarCalendar.get_month_gz(year, month)
    ri_gz = LunarCalendar.get_day_gz(year, month, day)
    shi_zhi = LunarCalendar.get_hour_gz(hour)
    
    # 构建时柱（简化，只取地支）
    shi_gz = f"{ri_gz[0]}{shi_zhi}"  # 时干由日干决定，这里简化处理
    
    sizhu = {
        '年柱': nian_gz,
        '月柱': yue_gz,
        '日柱': ri_gz,
        '时柱': shi_gz
    }
    
    print(f"四柱：{nian_gz}年 {yue_gz}月 {ri_gz}日 {shi_gz}时")
    
    # 提取地支
    year_zhi = nian_gz[-1]
    month_zhi = yue_gz[-1]
    day_zhi = ri_gz[-1]
    shi_zhi = shi_gz[-1]
    
    print(f"地支：年{year_zhi} 月{month_zhi} 日{day_zhi} 时{shi_zhi}")
    
    # 使用演禽法分析
    analyzer = YanQinAnalyzer()
    
    # 单独验证日禽计算
    print("\n【日禽计算验证】")
    print(f"日支：{day_zhi}")
    print(f"日禽起例表：{analyzer.RI_QIN_MAP}")
    ri_qin = analyzer.get_ri_qin(day_zhi)
    print(f"计算得出日禽：{ri_qin}")
    
    # 验证其他禽星计算
    print("\n【其他禽星计算验证】")
    nian_qin = analyzer.get_nian_qin(year_zhi)
    yue_qin = analyzer.get_yue_qin(month_zhi)
    shi_qin = analyzer.get_shi_qin(shi_zhi)
    
    print(f"年支：{year_zhi} → 年禽：{nian_qin}")
    print(f"月支：{month_zhi} → 月禽：{yue_qin}")
    print(f"时支：{shi_zhi} → 时禽：{shi_qin}")
    
    # 完整分析
    result = analyzer.analyze_yanqin(sizhu)
    
    print("\n【完整分析结果】")
    print("四禽：")
    for key, value in result['四禽'].items():
        qin_xing = result['四禽禽星'].get(f'{key}星', '')
        jixiong = result['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f"  {key}: {value} ({qin_xing}) - {jixiong}")
    
    # 分析演禽法与历法的差异
    print("\n【演禽法与历法差异分析】")
    print("1. 演禽法的日禽是基于日支计算的，而不是基于实际的天文位置")
    print("2. 演禽法的起例是固定的对应关系，属于传统数术体系")
    print("3. 历法中的星宿位置是基于实际天文观测的")
    print("4. 两者属于不同的系统，计算方法和目的不同")
    
    print("\n【结论】")
    print("演禽法是一种传统数术方法，其日禽计算基于日支与二十八宿的固定对应关系")
    print("这种计算方法与实际的天文历法星宿位置可能不一致")
    print("演禽法的价值在于其传统数术体系内的逻辑一致性，而非天文准确性")
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)

if __name__ == '__main__':
    verify_yanqin_calculation()
