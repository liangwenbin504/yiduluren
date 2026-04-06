#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试大六壬评价功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

print("=" * 80)
print("大六壬评价功能测试")
print("=" * 80)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API 地址：{BASE_URL}")
print("=" * 80)
print()

# 测试 1: 大六壬综合评分
print("【测试 1】大六壬综合评分 API")
print("-" * 80)
try:
    start = datetime.now()
    response = requests.get(f"{BASE_URL}/api/daliuren/score?shan=壬&ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=子", timeout=30)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"响应时间：{elapsed:.2f}秒")
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功：{data.get('success', False)}")
        if data.get('success'):
            print(f"评分：{data.get('total_score', 0)}")
            print(f"课体：{data.get('keti', '无')}")
            print(f"评估：{data.get('pinggu', '无')}")
            print(f"详情：{json.dumps(data.get('score_detail', {}), ensure_ascii=False, indent=2)[:500]}")
        else:
            print(f"❌ 错误：{data.get('error', '未知错误')}")
    else:
        print(f"❌ HTTP 错误：{response.text[:500]}")
except Exception as e:
    print(f"❌ 异常：{e}")
    import traceback
    traceback.print_exc()
print()

# 测试 2: 完整排盘
print("【测试 2】大六壬完整排盘 API")
print("-" * 80)
try:
    start = datetime.now()
    payload = {
        'ri_gan': '甲',
        'ri_zhi': '子',
        'yue_jiang': '亥',
        'shichen': '寅'
    }
    response = requests.post(f"{BASE_URL}/api/daliuren/san_chuan", json=payload, timeout=30)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"响应时间：{elapsed:.2f}秒")
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功：{data.get('success', False)}")
        if data.get('success'):
            sanchuan = data.get('sanchuan', {})
            print(f"课体：{sanchuan.get('keTi', '无')}")
            print(f"三传：{[sanchuan.get('chuChuan', ''), sanchuan.get('zhongChuan', ''), sanchuan.get('moChuan', '')]}")
        else:
            print(f"❌ 错误：{data.get('error', '未知错误')}")
    else:
        print(f"❌ HTTP 错误：{response.text[:500]}")
except Exception as e:
    print(f"❌ 异常：{e}")
    import traceback
    traceback.print_exc()
print()

# 测试 3: AI 评价
print("【测试 3】AI 综合评价 API")
print("-" * 80)
try:
    start = datetime.now()
    payload = {
        'ri_gan': '甲',
        'ri_zhi': '子',
        'yue_jiang': '亥',
        'shi_chen': '寅',
        'mountain': '壬'
    }
    response = requests.post(f"{BASE_URL}/api/ai/evaluate", json=payload, timeout=30)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"响应时间：{elapsed:.2f}秒")
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功：{data.get('success', False)}")
        if data.get('success'):
            evaluation = data.get('ai_evaluation', '无')
            print(f"评价：{evaluation[:200] if evaluation else '无'}")
        else:
            print(f"❌ 错误：{data.get('error', '未知错误')}")
    else:
        print(f"❌ HTTP 错误：{response.text[:500]}")
except Exception as e:
    print(f"❌ 异常：{e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 80)
print("测试完成！")
print("=" * 80)
