#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试空亡规则：甲申旬午未空，午应该不显示天干
"""

import json
import urllib.request
import urllib.parse

base_url = "http://localhost:5000/api/qike"

# 甲申日 酉将 申时
params = {'ri_gan': '甲', 'ri_zhi': '申', 'yue_jiang': '酉', 'shi_chen': '申'}
url = base_url + '?' + urllib.parse.urlencode(params)

print("测试甲申日 酉将 申时")
print("=" * 70)
print("日干支：甲申（甲申旬，午未空）")
print("三传：辰、巳、午")
print("预期结果：")
print("  - 辰不空：显示天干 壬 → 壬辰")
print("  - 巳不空：显示天干 癸 → 癸巳")
print("  - 午空亡：不显示天干 → 午（天干留空）")
print()

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        sanchuan = data.get('data', {}).get('sanchuan', {})
        
        print("实际返回结果:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天干：{sanchuan.get('三传天干', [])}")
        print(f"  三传干支：{sanchuan.get('三传干支', [])}")
        print()
        
        print("三传显示:")
        chuan_names = ['初传', '中传', '末传']
        ganzhi_list = sanchuan.get('三传干支', [])
        liuqin_list = sanchuan.get('三传六亲', [])
        tianjiang_list = sanchuan.get('三传天将', [])
        stem_list = sanchuan.get('三传天干', [])
        
        for i, ganzhi in enumerate(ganzhi_list):
            liuqin = liuqin_list[i] if i < len(liuqin_list) else ''
            tianjiang = tianjiang_list[i] if i < len(tianjiang_list) else ''
            stem = stem_list[i] if i < len(stem_list) else ''
            
            display = f"  {chuan_names[i]}: "
            if liuqin:
                display += f"[{liuqin}]"
            display += ganzhi
            if tianjiang:
                display += f" ({tianjiang})"
            print(display)
        
        print()
        print("=" * 70)
        print("验证:")
        
        # 验证空亡规则
        if stem_list == ['壬', '癸', '']:
            print("✅ 正确！午火空亡，天干留空")
            print("   三传天干：['壬', '癸', '']")
        elif stem_list == ['壬', '癸', '甲']:
            print("❌ 错误！午火空亡，应该不显示天干甲")
            print("   当前显示：['壬', '癸', '甲']")
        else:
            print(f"? 三传天干：{stem_list}")
        
        # 验证干支显示
        if ganzhi_list == ['壬辰', '癸巳', '午']:
            print("✅ 正确！午火只显示地支")
        elif ganzhi_list == ['壬辰', '癸巳', '甲午']:
            print("❌ 错误！午火应该只显示'午'，不应该显示'甲午'")
        else:
            print(f"? 三传干支：{ganzhi_list}")
            
    else:
        print("失败:", data.get('error', ''))
except Exception as e:
    print(f"错误：{e}")
