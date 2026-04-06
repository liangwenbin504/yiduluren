#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查当日星宿与历法是否一致
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

def check_today_star():
    """检查当日星宿"""
    print("=" * 70)
    print("当日星宿检查")
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
    
    # 使用演禽法分析
    analyzer = YanQinAnalyzer()
    result = analyzer.analyze_yanqin(sizhu)
    
    print("\n【演禽分析结果】")
    print("四禽：")
    for key, value in result['四禽'].items():
        qin_xing = result['四禽禽星'].get(f'{key}星', '')
        jixiong = result['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f"  {key}: {value} ({qin_xing}) - {jixiong}")
    
    print("\n【日禽分析】")
    ri_qin = result['四禽'].get('日禽', '')
    ri_qin_xing = result['四禽禽星'].get('日禽星', '')
    ri_qin_jixiong = result['二十八宿属性'].get('日宿吉凶', '')
    print(f"当日禽星：{ri_qin} ({ri_qin_xing})")
    print(f"吉凶：{ri_qin_jixiong}")
    
    # 与历法对比（这里使用简化的历法计算）
    print("\n【与历法对比】")
    print("注：此处使用简化的历法计算，实际应使用更精确的儒积日法")
    
    # 计算简化的历法星宿
    # 基于日期计算，假设每年365天，每宿约13.04天
    base_date = datetime(2023, 1, 1)  # 假设2023年1月1日是角宿
    target_date = datetime(year, month, day)
    delta_days = (target_date - base_date).days
    xiu_index = delta_days // 13 % 28
    calender_xiu = analyzer.ERSHIBA_XIU[xiu_index]
    
    print(f"历法计算星宿：{calender_xiu}")
    print(f"演禽法计算日禽：{ri_qin}")
    
    if ri_qin == calender_xiu:
        print("\n✅ 演禽法计算结果与历法一致")
    else:
        print("\n❌ 演禽法计算结果与历法不一致")
        print(f"   历法：{calender_xiu}")
        print(f"   演禽法：{ri_qin}")
    
    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)

if __name__ == '__main__':
    check_today_star()
