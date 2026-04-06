#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试涉害法的三传
"""

import json
import urllib.request
import urllib.parse

base_url = "http://localhost:5000/api/qike"
params = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'yue_jiang': '戌',
    'shi_chen': '子'
}

url = base_url + '?' + urllib.parse.urlencode(params)

print("测试涉害法课例")
print("=" * 60)
print(f"请求：甲子日 戌将子时\n")

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        result = data.get('data', {})
        sanchuan = result.get('sanchuan', {})
        
        print("起法:", sanchuan.get('起法', ''))
        print("课体:", sanchuan.get('课体', ''))
        print("三传:", sanchuan.get('三传', 'NOT FOUND'))
        print("三传天将:", sanchuan.get('三传天将', 'NOT FOUND'))
        print("初传:", sanchuan.get('初传', ''))
        print("中传:", sanchuan.get('中传', ''))
        print("末传:", sanchuan.get('末传', ''))
        
        print("\n完整 sanchuan 数据:")
        print(json.dumps(sanchuan, ensure_ascii=False, indent=2))
    else:
        print("起课失败:", data.get('error', ''))
        
except Exception as e:
    print(f"错误：{e}")
