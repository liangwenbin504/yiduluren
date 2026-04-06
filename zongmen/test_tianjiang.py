#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试天将功能
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

print("测试天将功能")
print("=" * 60)
print(f"请求：甲子日 子将子时\n")

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        result = data.get('data', {})
        
        # 显示四课（包含天将）
        print("【四课】")
        for ke in result.get('sike', []):
            ke_name, shang, xia, tian_jiang = ke
            tian_jiang_str = f" ({tian_jiang})" if tian_jiang else ""
            print(f"  {ke_name}: 上{shang} 下{xia}{tian_jiang_str}")
        
        print()
        
        # 显示三传（包含天将）
        print("【三传】")
        sanchuan = result.get('sanchuan', {})
        san_chuan_list = sanchuan.get('三传', [])
        san_chuan_tian_jiang = sanchuan.get('三传天将', [])
        
        chuan_names = ['初传', '中传', '末传']
        for i, chuan in enumerate(san_chuan_list):
            tian_jiang = san_chuan_tian_jiang[i] if i < len(san_chuan_tian_jiang) else ''
            tian_jiang_str = f" ({tian_jiang})" if tian_jiang else ""
            print(f"  {chuan_names[i]}: {chuan}{tian_jiang_str}")
        
        print()
        print("起法:", sanchuan.get('起法', ''))
        print("课体:", sanchuan.get('课体', ''))
        
    else:
        print("起课失败:", data.get('error', ''))
        
except Exception as e:
    print(f"错误：{e}")
    import traceback
    traceback.print_exc()
