#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证API返回的三传数据
"""

import requests
import json
from datetime import datetime

# 获取当前日期时间
now = datetime.now()
year = now.year
month = now.month
day = now.day
hour = now.hour

print("=" * 70)
print(f"验证API返回的三传数据")
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

# 使用API获取四柱
sizhu_url = f"http://localhost:5000/api/sizhu?year={year}&month={month}&day={day}&hour={hour}"
sizhu_response = requests.get(sizhu_url)
sizhu_data = sizhu_response.json()

if sizhu_data.get('success'):
    day_gan = sizhu_data['sizhu']['dayGan']
    day_zhi = sizhu_data['sizhu']['dayZhi']
    
    print(f"\n日干支: {day_gan}{day_zhi}")
    
    # 获取三传
    sanchuan_url = "http://localhost:5000/api/daliuren/san_chuan"
    sanchuan_data = {
        "ri_gan": day_gan,
        "ri_zhi": day_zhi,
        "yue_jiang": yue_jiang,
        "shi_chen": shi_chen
    }
    sanchuan_response = requests.post(sanchuan_url, json=sanchuan_data)
    sanchuan_result = sanchuan_response.json()
    
    print(f"\nAPI返回的完整数据:")
    print(json.dumps(sanchuan_result, ensure_ascii=False, indent=2))
    
    if sanchuan_result.get('success'):
        print(f"\n三传:")
        print(f"  初传: {sanchuan_result['sanchuan']['chuChuan']}")
        print(f"  中传: {sanchuan_result['sanchuan']['zhongChuan']}")
        print(f"  末传: {sanchuan_result['sanchuan']['moChuan']}")
        print(f"  课体: {sanchuan_result['sanchuan']['keTi']}")
        print(f"  起法: {sanchuan_result['sanchuan']['qiFa']}")

print("\n" + "=" * 70)
