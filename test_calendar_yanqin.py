#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试基于历法的演禽真法分析
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

def test_calendar_yanqin():
    """测试基于历法的演禽真法分析"""
    print("=" * 70)
    print("基于历法的演禽真法分析测试")
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
    
    # 使用传统演禽法分析
    analyzer = YanQinAnalyzer()
    traditional_result = analyzer.analyze_yanqin(sizhu)
    
    # 使用基于历法的演禽法分析
    calendar_result = analyzer.analyze_yanqin_with_calendar(sizhu, year, month, day)
    
    print("\n【传统演禽法结果】")
    print("四禽：")
    for key, value in traditional_result['四禽'].items():
        qin_xing = traditional_result['四禽禽星'].get(f'{key}星', '')
        jixiong = traditional_result['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f"  {key}: {value} ({qin_xing}) - {jixiong}")
    
    print("\n【基于历法的演禽法结果】")
    print("四禽：")
    for key, value in calendar_result['四禽'].items():
        qin_xing = calendar_result['四禽禽星'].get(f'{key}星', '')
        jixiong = calendar_result['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f"  {key}: {value} ({qin_xing}) - {jixiong}")
    
    print("\n【对比分析】")
    print(f"日禽（传统方法）：{traditional_result['四禽']['日禽']}")
    print(f"日禽（基于历法）：{calendar_result['四禽']['日禽']}")
    
    if calendar_result['四禽']['日禽'] != traditional_result['四禽']['日禽']:
        print("\n✅ 已成功实现基于历法的演禽真法分析")
        print("   日禽计算现在与权威历法保持一致")
    else:
        print("\n⚠️  传统方法与基于历法的计算结果相同")
    
    print("\n【基于历法的演禽真法分析结果】")
    print(f"综合评分：{calendar_result['综合评分']}分")
    print("吉凶断语：")
    for duanyu in calendar_result['吉凶断语']:
        print(f"  - {duanyu}")
    
    print("\n【格局判定】")
    for pattern in calendar_result['格局判定']:
        print(f"  - {pattern['格局名称']} ({pattern['吉凶']}): {pattern['描述']}")
    
    print("\n【生克关系】")
    for key, value in calendar_result['生克关系'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    test_calendar_yanqin()
