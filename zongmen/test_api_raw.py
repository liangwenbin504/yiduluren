#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试 API 返回的原始数据
"""

import json
import urllib.request
import urllib.parse

base_url = "http://localhost:5000/api/qike"
params = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'yue_jiang': '子',
    'shi_chen': '子'
}

url = base_url + '?' + urllib.parse.urlencode(params)

print("测试 API 原始数据")
print("=" * 60)

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        result = data.get('data', {})
        sike = result.get('sike', [])
        sanchuan = result.get('sanchuan', {})
        
        print("四课数据:")
        for ke in sike:
            print(f"  {ke}")
        
        print("\n三传数据:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天将：{sanchuan.get('三传天将', 'NOT FOUND')}")
        print(f"  所有键：{list(sanchuan.keys())}")
        
    else:
        print("失败:", data.get('error', ''))
        
except Exception as e:
    print(f"错误：{e}")
