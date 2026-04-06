#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试API响应 - 3年范围"""
import requests
import json

print("=" * 70)
print("测试API响应 - 3年范围")
print("=" * 70)

# 测试3年日期范围分析
payload = {
    "mountain": "壬山",
    "start_date": "2026-04-04",
    "end_date": "2029-04-04",
    "max_results": 20
}

try:
    response = requests.post(
        "http://localhost:5000/api/doushou/full_range_analyze",
        json=payload,
        timeout=120
    )
    print(f"日期范围分析: {response.status_code}")
    result = response.json()
    
    print(f"总天数: {result.get('total_days')}")
    print(f"候选数: {result.get('total_candidates')}")
    
    results = result.get('results', [])
    print(f"\n返回结果数: {len(results)}")
    
    if results:
        print("\n前10个结果:")
        for i, r in enumerate(results[:10], 1):
            print(f"  {i}. {r.get('date')} {r.get('shichen')}时")
            print(f"     斗首={r.get('doushou_score')}, 六壬={r.get('daliuren_score')}, 演禽={r.get('yanqin_score')}, 总分={r.get('total_score'):.1f}")
    else:
        print("无结果返回！")
        
except Exception as e:
    print(f"日期范围分析失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
