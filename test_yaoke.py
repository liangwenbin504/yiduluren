#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证当前排盘数据 - 检查是否应该使用遥克法
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from dizhi_layout_generator import arrange_tiandi_pan
from sike_sanchuan_engine import SiKeSanChuanCalculator

# 获取当前日期时间
now = datetime.now()
year = now.year
month = now.month
day = now.day
hour = now.hour

print("=" * 70)
print(f"验证当前排盘数据 - 检查是否应该使用遥克法")
print(f"日期时间: {year}年{month}月{day}日{hour}时")
print("=" * 70)

# 月将映射
yuejiang_map = {
    1: '丑', 2: '子', 3: '亥', 4: '戌', 5: '酉', 6: '申',
    7: '未', 8: '午', 9: '巳', 10: '辰', 11: '卯', 12: '寅'
}
yue_jiang = yuejiang_map[month]

# 时辰地支
dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
shichen_index = (hour + 1) // 2 % 12
shi_chen = dizhi[shichen_index]

print(f"月将: {yue_jiang}")
print(f"时辰: {shi_chen}")

# 天地盘
tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)
print(f"\n天地盘:")
for di, tian in tiandi_pan.items():
    print(f"  地盘{di} → 天盘{tian}")

# 使用API获取四柱
import requests
sizhu_url = f"http://localhost:5000/api/sizhu?year={year}&month={month}&day={day}&hour={hour}"
sizhu_response = requests.get(sizhu_url)
sizhu_data = sizhu_response.json()

if sizhu_data.get('success'):
    print(f"\n四柱信息:")
    print(f"  年柱: {sizhu_data['sizhu']['yearPillar']}")
    print(f"  月柱: {sizhu_data['sizhu']['monthPillar']}")
    print(f"  日柱: {sizhu_data['sizhu']['dayPillar']}")
    print(f"  时柱: {sizhu_data['sizhu']['hourPillar']}")
    
    day_gan = sizhu_data['sizhu']['dayGan']
    day_zhi = sizhu_data['sizhu']['dayZhi']
    
    print(f"\n日干支: {day_gan}{day_zhi}")
    
    # 四课
    calculator = SiKeSanChuanCalculator()
    sike = calculator.qi_sike(day_gan, day_zhi, tiandi_pan)
    
    print(f"\n四课:")
    for i, ke in enumerate(sike, 1):
        # ke 是元组：(课名, 上神, 下神, 其他)
        name = ke[0]
        shang = ke[1]
        xia = ke[2]
        print(f"  第{i}课: 上神={shang}, 下神={xia}")
    
    # 检查克贼
    print(f"\n检查克贼:")
    WUXING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
        '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
        '戌': '土', '亥': '水'
    }
    
    KE_MAP = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    for i, ke in enumerate(sike, 1):
        shang = ke[1]
        xia = ke[2]
        shang_wuxing = WUXING[shang]
        xia_wuxing = WUXING[xia]
        
        if KE_MAP[shang_wuxing] == xia_wuxing:
            print(f"  第{i}课: {shang}({shang_wuxing}) 克 {xia}({xia_wuxing}) - 上克下")
        elif KE_MAP[xia_wuxing] == shang_wuxing:
            print(f"  第{i}课: {xia}({xia_wuxing}) 贼 {shang}({shang_wuxing}) - 下贼上")
        else:
            print(f"  第{i}课: {shang}({shang_wuxing}) 与 {xia}({xia_wuxing}) 无克贼")
    
    # 检查遥克
    print(f"\n检查遥克:")
    ri_wuxing = WUXING[day_gan]
    print(f"日干: {day_gan}({ri_wuxing})")
    
    for i, ke in enumerate(sike, 1):
        shang = ke[1]
        shang_wuxing = WUXING[shang]
        
        if KE_MAP[shang_wuxing] == ri_wuxing:
            print(f"  第{i}课: {shang}({shang_wuxing}) 克 日干({ri_wuxing}) - 上克干")
        elif KE_MAP[ri_wuxing] == shang_wuxing:
            print(f"  第{i}课: 日干({ri_wuxing}) 克 {shang}({shang_wuxing}) - 干克上")
        else:
            print(f"  第{i}课: {shang}({shang_wuxing}) 与 日干({ri_wuxing}) 无遥克")
    
    # 三传
    sanchuan_result = calculator.fa_sanchuan(sike, day_gan, day_zhi, tiandi_pan)
    
    print(f"\n三传:")
    print(f"  初传: {sanchuan_result['初传']}")
    print(f"  中传: {sanchuan_result['中传']}")
    print(f"  末传: {sanchuan_result['末传']}")
    print(f"  课体: {sanchuan_result['课体']}")
    print(f"  起法: {sanchuan_result['起法']}")
    
    # 验证三传计算
    print(f"\n三传验证:")
    chu = sanchuan_result['初传']
    zhong = tiandi_pan.get(chu, '?')
    mo = tiandi_pan.get(zhong, '?')
    
    print(f"  初传: {chu}")
    print(f"  中传（初传作为地盘，其天盘）: {zhong}")
    print(f"  末传（中传作为地盘，其天盘）: {mo}")
    
    if sanchuan_result['中传'] == zhong and sanchuan_result['末传'] == mo:
        print("\n✅ 三传计算正确！")
    else:
        print(f"\n❌ 三传计算错误！")
        print(f"  期望中传: {zhong}, 实际: {sanchuan_result['中传']}")
        print(f"  期望末传: {mo}, 实际: {sanchuan_result['末传']}")

print("\n" + "=" * 70)
