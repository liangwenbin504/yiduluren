#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试API端点
"""

import sys
import os
import requests
import json

url = 'http://localhost:5000/api/doushou/full_range_analyze'

data = {
    'mountain': '壬',
    'start_date': '2026-04-01',
    'end_date': '2026-04-03',
    'min_daliuren_score': 70,
    'max_results': 5
}

print("=" * 80)
print("测试 API 端点")
print("=" * 80)
print(f"URL: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
print()

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('success'):
            print("\n✅ API 调用成功！")
            print(f"   共找到 {result.get('total_candidates', 0)} 个候选日课")
        else:
            print(f"\n❌ API 返回错误: {result.get('error')}")
    else:
        print(f"响应内容: {response.text}")
        print("\n❌ API 调用失败！")
        
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ 连接错误: {e}")
    print("   请确保 API 服务器已启动！")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
