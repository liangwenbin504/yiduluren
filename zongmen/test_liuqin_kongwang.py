#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试六亲和空亡功能
"""

import json
import urllib.request
import urllib.parse

base_url = "http://localhost:5000/api/qike"

# 测试 1：甲子日 戌将子时（涉害课）- 初传空亡
print("测试 1：甲子日 戌将子时（涉害课）")
print("=" * 60)
print("日干支：甲子（甲子旬，戌亥空）\n")
params = {'ri_gan': '甲', 'ri_zhi': '子', 'yue_jiang': '戌', 'shi_chen': '子'}
url = base_url + '?' + urllib.parse.urlencode(params)

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        sanchuan = data.get('data', {}).get('sanchuan', {})
        
        print("三传数据:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天干：{sanchuan.get('三传天干', [])}")
        print(f"  三传干支：{sanchuan.get('三传干支', [])}")
        print(f"  三传六亲：{sanchuan.get('三传六亲', [])}")
        print(f"  三传天将：{sanchuan.get('三传天将', [])}")
        print(f"  三传空亡：{sanchuan.get('三传空亡', [])}")
        
        print("\n三传显示：")
        chuan_names = ['初传', '中传', '末传']
        ganzhi_list = sanchuan.get('三传干支', [])
        liuqin_list = sanchuan.get('三传六亲', [])
        tianjiang_list = sanchuan.get('三传天将', [])
        kongwang_list = sanchuan.get('三传空亡', [])
        for i, ganzhi in enumerate(ganzhi_list):
            liuqin = liuqin_list[i] if i < len(liuqin_list) else ''
            tianjiang = tianjiang_list[i] if i < len(tianjiang_list) else ''
            kongwang = kongwang_list[i] if i < len(kongwang_list) else ''
            
            display = f"  {chuan_names[i]}: "
            if liuqin:
                display += f"[{liuqin}]"
            display += ganzhi
            if tianjiang:
                display += f" ({tianjiang})"
            if kongwang:
                display += f" [{kongwang}]"
            print(display)
    else:
        print("失败:", data.get('error', ''))
except Exception as e:
    print(f"错误：{e}")

print()
print()

# 测试 2：甲子日 子将子时（伏吟课）- 无空亡
print("测试 2：甲子日 子将子时（伏吟课）")
print("=" * 60)
print("日干支：甲子（甲子旬，戌亥空）\n")
params = {'ri_gan': '甲', 'ri_zhi': '子', 'yue_jiang': '子', 'shi_chen': '子'}
url = base_url + '?' + urllib.parse.urlencode(params)

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        sanchuan = data.get('data', {}).get('sanchuan', {})
        
        print("三传数据:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天干：{sanchuan.get('三传天干', [])}")
        print(f"  三传干支：{sanchuan.get('三传干支', [])}")
        print(f"  三传六亲：{sanchuan.get('三传六亲', [])}")
        print(f"  三传天将：{sanchuan.get('三传天将', [])}")
        print(f"  三传空亡：{sanchuan.get('三传空亡', [])}")
        
        print("\n三传显示：")
        chuan_names = ['初传', '中传', '末传']
        ganzhi_list = sanchuan.get('三传干支', [])
        liuqin_list = sanchuan.get('三传六亲', [])
        tianjiang_list = sanchuan.get('三传天将', [])
        kongwang_list = sanchuan.get('三传空亡', [])
        for i, ganzhi in enumerate(ganzhi_list):
            liuqin = liuqin_list[i] if i < len(liuqin_list) else ''
            tianjiang = tianjiang_list[i] if i < len(tianjiang_list) else ''
            kongwang = kongwang_list[i] if i < len(kongwang_list) else ''
            
            display = f"  {chuan_names[i]}: "
            if liuqin:
                display += f"[{liuqin}]"
            display += ganzhi
            if tianjiang:
                display += f" ({tianjiang})"
            if kongwang:
                display += f" [{kongwang}]"
            print(display)
    else:
        print("失败:", data.get('error', ''))
except Exception as e:
    print(f"错误：{e}")
