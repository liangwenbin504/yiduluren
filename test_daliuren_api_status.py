#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 API 专项测试
测试大六壬 API 的实际运行状态和性能
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_daliuren_api():
    """测试大六壬 API"""
    print("=" * 80)
    print("大六壬 API 专项测试")
    print("=" * 80)
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API 地址：{BASE_URL}")
    print("=" * 80)
    print()
    
    # 测试 1: 排天地盘
    print("【测试 1】排天地盘")
    print("-" * 80)
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅", timeout=30)
        elapsed = (time.time() - start) * 1000
        
        print(f"响应时间：{elapsed:.2f}ms")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功：{data.get('success', False)}")
            if data.get('success'):
                print(f"天地对应：{len(data.get('天地对应', {}))} 个")
            else:
                print(f"❌ 错误：{data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP 错误：{response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    print()
    
    # 测试 2: 起四课
    print("【测试 2】起四课")
    print("-" * 80)
    try:
        start = time.time()
        payload = {
            'ri_gan': '甲',
            'ri_zhi': '子',
            'yuejiang': '亥',
            'shichen': '寅'
        }
        response = requests.post(f"{BASE_URL}/api/daliuren/si_ke", json=payload, timeout=30)
        elapsed = (time.time() - start) * 1000
        
        print(f"响应时间：{elapsed:.2f}ms")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功：{data.get('success', False)}")
            if data.get('success'):
                print(f"四课数量：{len(data.get('四课', []))}")
                print(f"四课：{data.get('四课', [])}")
            else:
                print(f"❌ 错误：{data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP 错误：{response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    print()
    
    # 测试 3: 发三传（宗门九课）
    print("【测试 3】发三传（宗门九课）")
    print("-" * 80)
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=寅", timeout=30)
        elapsed = (time.time() - start) * 1000
        
        print(f"响应时间：{elapsed:.2f}ms")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功：{data.get('success', False)}")
            if data.get('success'):
                print(f"课体：{data.get('课体', '无')}")
                print(f"三传：{data.get('三传', [])}")
            else:
                print(f"❌ 错误：{data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP 错误：{response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    print()
    
    # 测试 4: 大六壬综合评分
    print("【测试 4】大六壬综合评分")
    print("-" * 80)
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/daliuren/score?shan=壬&ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=子", timeout=30)
        elapsed = (time.time() - start) * 1000
        
        print(f"响应时间：{elapsed:.2f}ms")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功：{data.get('success', False)}")
            if data.get('success'):
                print(f"评分：{data.get('score', 0)}")
                print(f"课体：{data.get('keti', '无')}")
                if 'detail' in data:
                    print(f"详情：{json.dumps(data['detail'], ensure_ascii=False, indent=2)[:500]}")
            else:
                print(f"❌ 错误：{data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP 错误：{response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    print()
    
    # 测试 5: 完整排盘
    print("【测试 5】完整排盘")
    print("-" * 80)
    try:
        start = time.time()
        payload = {
            'ri_gan': '甲',
            'ri_zhi': '子',
            'yue_jiang': '亥',
            'shichen': '寅'
        }
        response = requests.post(f"{BASE_URL}/api/daliuren/san_chuan", json=payload, timeout=30)
        elapsed = (time.time() - start) * 1000
        
        print(f"响应时间：{elapsed:.2f}ms")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功：{data.get('success', False)}")
            if data.get('success'):
                print(f"课体：{data.get('课体', '无')}")
                print(f"三传：{data.get('三传', [])}")
                print(f"天地盘：{len(data.get('天地盘', {}))} 个")
            else:
                print(f"❌ 错误：{data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP 错误：{response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    print()
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)

if __name__ == '__main__':
    test_daliuren_api()
