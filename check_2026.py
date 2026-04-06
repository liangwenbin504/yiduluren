#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查2026年丙午年的吉课"""
import requests
import json

print("=" * 70)
print("检查2026年（丙午年）的吉课")
print("=" * 70)

# 测试2026年全年的日期范围
payload = {
    "mountain": "壬山",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "max_results": 50
}

try:
    response = requests.post(
        "http://localhost:5000/api/doushou/full_range_analyze",
        json=payload,
        timeout=120
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    print(f"总天数: {result.get('total_days')}")
    print(f"候选数: {result.get('total_candidates')}")
    
    results = result.get('results', [])
    print(f"\n返回结果数: {len(results)}")
    
    if results:
        print("\n前20个结果（按评分排序）:")
        for i, r in enumerate(results[:20], 1):
            print(f"  {i}. {r.get('date')} {r.get('shichen')}时")
            print(f"     斗首={r.get('doushou_score')}, 六壬={r.get('daliuren_score')}, 演禽={r.get('yanqin_score')}, 总分={r.get('total_score'):.1f}")
            print(f"     四柱: {r.get('sizhu', {}).get('年柱')} {r.get('sizhu', {}).get('月柱')} {r.get('sizhu', {}).get('日柱')} {r.get('sizhu', {}).get('时柱')}")
    else:
        print("无结果返回！")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
