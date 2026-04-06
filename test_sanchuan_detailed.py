#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试六壬API - 详细版
"""

import requests
import json

def test_san_chuan_detailed():
    """测试三传API - 详细版"""
    url = "http://localhost:5000/api/daliuren/san_chuan"
    data = {
        "ri_gan": "乙",
        "ri_zhi": "未",
        "yue_jiang": "亥",
        "shi_chen": "寅"
    }
    
    print("=" * 60)
    print("测试三传API - 详细版")
    print("=" * 60)
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"成功: {result.get('success', False)}")
    print(f"\n完整返回数据:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

if __name__ == "__main__":
    try:
        test_san_chuan_detailed()
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
