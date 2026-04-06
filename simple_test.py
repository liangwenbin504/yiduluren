#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试 - 检查服务器是否正常运行
"""

import requests
import time

print("📡 测试服务器连接...")

url = "http://localhost:5000/api/doushou/full_range_analyze"

data = {
    "mountain": "壬",
    "start_date": "2026-11-01",
    "end_date": "2026-11-03",  # 只测试 3 天
    "min_daliuren_score": 70,
    "max_results": 3
}

try:
    print(f"发送请求到：{url}")
    start_time = time.time()
    
    response = requests.post(url, json=data, timeout=300)
    
    elapsed = time.time() - start_time
    
    print(f"\n响应状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功！耗时：{elapsed:.2f}秒")
        print(f"遍历：{result.get('total_days')}天")
        print(f"候选：{result.get('total_candidates')}个")
        
        if result.get('performance'):
            perf = result['performance']
            print(f"性能：{perf.get('elapsed_seconds')}秒 (平均{perf.get('avg_ms_per_shichen')}ms/时辰)")
    else:
        print(f"❌ HTTP 错误：{response.status_code}")
        
except Exception as e:
    print(f"❌ 错误：{e}")
    print("\n提示：请检查 API 服务器是否正在运行")
