#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 API 服务器返回的数据
"""

import json
import urllib.request
import urllib.parse

# 测试 URL
base_url = "http://localhost:5000/api/qike"
params = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'yue_jiang': '子',
    'shi_chen': '子'
}

url = base_url + '?' + urllib.parse.urlencode(params)

print("测试 API 返回数据")
print("=" * 60)

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        result = data.get('data', {})
        sanchuan = result.get('sanchuan', {})
        
        print("sanchuan 的所有键:")
        for key in sanchuan.keys():
            print(f"  - {key}")
        
        print("\n三传字段:", '三传' in sanchuan)
        print("三传值:", sanchuan.get('三传', 'NOT FOUND'))
        
        print("\n完整 sanchuan 数据:")
        print(json.dumps(sanchuan, ensure_ascii=False, indent=2))
    else:
        print("起课失败:", data.get('error', ''))
        
except Exception as e:
    print(f"错误：{e}")
