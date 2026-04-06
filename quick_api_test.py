#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - API 性能问题分析工具

功能：
1. 快速测试 API 响应能力
2. 分析 API 服务器配置问题
3. 识别性能瓶颈
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_simple_api():
    """测试简单 API 的响应"""
    print("=" * 60)
    print("简单 API 响应测试")
    print("=" * 60)
    
    # 测试 1: 首页
    print("\n1. 测试首页 (/)...")
    try:
        start = time.time()
        r = requests.get(BASE_URL, timeout=10)
        elapsed = (time.time() - start) * 1000
        print(f"   状态码：{r.status_code}")
        print(f"   响应时间：{elapsed:.2f}ms")
        print(f"   响应内容：{r.text[:200]}")
    except Exception as e:
        print(f"   错误：{e}")
    
    # 测试 2: 简单 API - 山家五行
    print("\n2. 测试山家五行 API...")
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/doushou/shanjia_wuxing?mountain=壬", timeout=10)
        elapsed = (time.time() - start) * 1000
        print(f"   状态码：{r.status_code}")
        print(f"   响应时间：{elapsed:.2f}ms")
        if r.status_code == 200:
            print(f"   响应：{r.json()}")
        else:
            print(f"   错误：{r.text}")
    except Exception as e:
        print(f"   错误：{e}")
    
    # 测试 3: 简单 API - 天干化气
    print("\n3. 测试天干化气 API...")
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/doushou/tiangan_huaqi?tiangan=甲", timeout=10)
        elapsed = (time.time() - start) * 1000
        print(f"   状态码：{r.status_code}")
        print(f"   响应时间：{elapsed:.2f}ms")
        if r.status_code == 200:
            print(f"   响应：{r.json()}")
        else:
            print(f"   错误：{r.text}")
    except Exception as e:
        print(f"   错误：{e}")
    
    # 测试 4: 天地盘 API
    print("\n4. 测试天地盘 API...")
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅", timeout=10)
        elapsed = (time.time() - start) * 1000
        print(f"   状态码：{r.status_code}")
        print(f"   响应时间：{elapsed:.2f}ms")
        if r.status_code == 200:
            result = r.json()
            print(f"   课体：{result.get('success')}")
        else:
            print(f"   错误：{r.text}")
    except Exception as e:
        print(f"   错误：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    print("正在检查 API 服务器...")
    try:
        r = requests.get(BASE_URL, timeout=5)
        print(f"✅ API 服务器已就绪")
        test_simple_api()
    except:
        print(f"❌ API 服务器未响应")
        print("\n请先启动 API 服务器（非调试模式）:")
        print("  python -c \"from api_server import app; app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)\"")
        sys.exit(1)
