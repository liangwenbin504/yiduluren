#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试六壬API
"""

import requests
import json

def test_tiandi_pan():
    """测试天地盘API"""
    url = "http://localhost:5000/api/daliuren/tiandi_pan"
    params = {"yuejiang": "亥", "shichen": "寅"}
    
    print("=" * 60)
    print("测试天地盘API")
    print("=" * 60)
    
    response = requests.get(url, params=params)
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"成功: {data.get('success', False)}")
    print(f"\n地盘 ({len(data.get('di_pan', []))} 个元素):")
    print(f"  {data.get('di_pan', [])}")
    print(f"\n天盘 ({len(data.get('tian_pan', []))} 个元素):")
    print(f"  {data.get('tian_pan', [])}")
    print(f"\n天地对应 ({len(data.get('tiandi_duiying', {}))} 个映射):")
    for di, tian in data.get('tiandi_duiying', {}).items():
        print(f"  {di} -> {tian}")
    
    return data

def test_si_ke():
    """测试四课API"""
    url = "http://localhost:5000/api/daliuren/si_ke"
    data = {
        "ri_gan": "乙",
        "ri_zhi": "未",
        "yuejiang": "亥",
        "shichen": "寅"
    }
    
    print("\n" + "=" * 60)
    print("测试四课API")
    print("=" * 60)
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"成功: {result.get('success', False)}")
    print(f"\n天盘 ({len(result.get('tian_pan', []))} 个元素):")
    print(f"  {result.get('tian_pan', [])}")
    print(f"\n四课:")
    for ke in result.get('si_ke', []):
        print(f"  {ke.get('name')}: 上神={ke.get('top')}, 下神={ke.get('bottom')}")
    
    return result

def test_san_chuan():
    """测试三传API"""
    url = "http://localhost:5000/api/daliuren/san_chuan"
    data = {
        "ri_gan": "乙",
        "ri_zhi": "未",
        "yue_jiang": "亥",
        "shi_chen": "寅"
    }
    
    print("\n" + "=" * 60)
    print("测试三传API")
    print("=" * 60)
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"成功: {result.get('success', False)}")
    print(f"\n三传:")
    print(f"  初传: {result.get('san_chuan', {}).get('chu', 'N/A')}")
    print(f"  中传: {result.get('san_chuan', {}).get('zhong', 'N/A')}")
    print(f"  末传: {result.get('san_chuan', {}).get('mo', 'N/A')}")
    
    return result

if __name__ == "__main__":
    try:
        test_tiandi_pan()
        test_si_ke()
        test_san_chuan()
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
