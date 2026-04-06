#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试 API 返回的三传天干
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
print(f"请求 URL: {url}")
print()

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        sanchuan = data.get('data', {}).get('sanchuan', {})
        
        print("三传数据:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天干：{sanchuan.get('三传天干', [])}")
        print(f"  三传干支：{sanchuan.get('三传干支', [])}")
        print()
        
        print("三传显示:")
        chuan_names = ['初传', '中传', '末传']
        ganzhi_list = sanchuan.get('三传干支', [])
        liuqin_list = sanchuan.get('三传六亲', [])
        tianjiang_list = sanchuan.get('三传天将', [])
        
        for i, ganzhi in enumerate(ganzhi_list):
            liuqin = liuqin_list[i] if i < len(liuqin_list) else ''
            tianjiang = tianjiang_list[i] if i < len(tianjiang_list) else ''
            
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
        stem_list = sanchuan.get('三传天干', [])
        if stem_list == ['壬', '癸', '甲']:
            print("✅ 正确！三传天干是：壬、癸、甲")
        elif stem_list == ['戊', '己', '庚']:
            print("❌ 错误！三传天干是：戊、己、庚（五鼠遁元法）")
        else:
            print(f"? 三传天干：{stem_list}")
    else:
        print("失败:", data.get('error', ''))
except Exception as e:
    print(f"错误：{e}")
    print("请确保 API 服务器已启动（运行 http_api_server.py）")
