#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证前端代码中四课的计算
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
print(f"验证前端代码中四课的计算")
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
    day_gan = sizhu_data['sizhu']['dayGan']
    day_zhi = sizhu_data['sizhu']['dayZhi']
    
    print(f"\n日干支: {day_gan}{day_zhi}")
    
    # 日干寄宫
    RIGAN_JIGONG = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
        '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    ri_gan_ji_gong = RIGAN_JIGONG[day_gan]
    print(f"日干寄宫: {ri_gan_ji_gong}")
    
    # 前端代码中四课的计算
    print(f"\n前端代码中四课的计算:")
    
    # 第一课：日干上神
    ke1_bottom = day_gan  # 显示日干，而不是日干寄宫
    ke1_top = tiandi_pan[ri_gan_ji_gong]
    print(f"  第一课: 上神={ke1_top}, 下神={ke1_bottom}")
    
    # 第二课：日干上神之上神
    ke2_bottom = ke1_top
    ke2_top = tiandi_pan[ke2_bottom]
    print(f"  第二课: 上神={ke2_top}, 下神={ke2_bottom}")
    
    # 第三课：日支上神
    ke3_bottom = day_zhi
    ke3_top = tiandi_pan[day_zhi]
    print(f"  第三课: 上神={ke3_top}, 下神={ke3_bottom}")
    
    # 第四课：日支上神之上神
    ke4_bottom = ke3_top
    ke4_top = tiandi_pan[ke4_bottom]
    print(f"  第四课: 上神={ke4_top}, 下神={ke4_bottom}")
    
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
    
    ke_results = []
    
    # 第一课
    shang = ke1_top
    xia = ke1_bottom
    shang_wuxing = WUXING[shang]
    xia_wuxing = WUXING[xia]
    
    if KE_MAP[shang_wuxing] == xia_wuxing:
        print(f"  第一课: {shang}({shang_wuxing}) 克 {xia}({xia_wuxing}) - 上克下")
        ke_results.append(('克', shang, xia))
    elif KE_MAP[xia_wuxing] == shang_wuxing:
        print(f"  第一课: {xia}({xia_wuxing}) 贼 {shang}({shang_wuxing}) - 下贼上")
        ke_results.append(('贼', shang, xia))
    else:
        print(f"  第一课: {shang}({shang_wuxing}) 与 {xia}({xia_wuxing}) 无克贼")
    
    # 第二课
    shang = ke2_top
    xia = ke2_bottom
    shang_wuxing = WUXING[shang]
    xia_wuxing = WUXING[xia]
    
    if KE_MAP[shang_wuxing] == xia_wuxing:
        print(f"  第二课: {shang}({shang_wuxing}) 克 {xia}({xia_wuxing}) - 上克下")
        ke_results.append(('克', shang, xia))
    elif KE_MAP[xia_wuxing] == shang_wuxing:
        print(f"  第二课: {xia}({xia_wuxing}) 贼 {shang}({shang_wuxing}) - 下贼上")
        ke_results.append(('贼', shang, xia))
    else:
        print(f"  第二课: {shang}({shang_wuxing}) 与 {xia}({xia_wuxing}) 无克贼")
    
    # 第三课
    shang = ke3_top
    xia = ke3_bottom
    shang_wuxing = WUXING[shang]
    xia_wuxing = WUXING[xia]
    
    if KE_MAP[shang_wuxing] == xia_wuxing:
        print(f"  第三课: {shang}({shang_wuxing}) 克 {xia}({xia_wuxing}) - 上克下")
        ke_results.append(('克', shang, xia))
    elif KE_MAP[xia_wuxing] == shang_wuxing:
        print(f"  第三课: {xia}({xia_wuxing}) 贼 {shang}({shang_wuxing}) - 下贼上")
        ke_results.append(('贼', shang, xia))
    else:
        print(f"  第三课: {shang}({shang_wuxing}) 与 {xia}({xia_wuxing}) 无克贼")
    
    # 第四课
    shang = ke4_top
    xia = ke4_bottom
    shang_wuxing = WUXING[shang]
    xia_wuxing = WUXING[xia]
    
    if KE_MAP[shang_wuxing] == xia_wuxing:
        print(f"  第四课: {shang}({shang_wuxing}) 克 {xia}({xia_wuxing}) - 上克下")
        ke_results.append(('克', shang, xia))
    elif KE_MAP[xia_wuxing] == shang_wuxing:
        print(f"  第四课: {xia}({xia_wuxing}) 贼 {shang}({shang_wuxing}) - 下贼上")
        ke_results.append(('贼', shang, xia))
    else:
        print(f"  第四课: {shang}({shang_wuxing}) 与 {xia}({xia_wuxing}) 无克贼")
    
    print(f"\n克贼结果: {ke_results}")
    
    # 根据宗门九课规则判断
    print(f"\n根据宗门九课规则判断:")
    if len(ke_results) == 1:
        ke_type, shang, xia = ke_results[0]
        chu_chuan = shang
        zhong_chuan = tiandi_pan[chu_chuan]
        mo_chuan = tiandi_pan[zhong_chuan]
        ke_ti = '元首课' if ke_type == '克' else '重审课'
        print(f"  起法: 贼克法")
        print(f"  课体: {ke_ti}")
        print(f"  三传: {chu_chuan} → {zhong_chuan} → {mo_chuan}")
    elif len(ke_results) > 1:
        print(f"  有多个克贼，需要比用")

print("\n" + "=" * 70)
