#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单 API 性能测试
快速测试优化后的 API 性能
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_endpoint(name, endpoint, method='GET', data=None):
    """测试单个端点"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start = time.time()
        if method == 'GET':
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        elapsed = (time.time() - start) * 1000
        
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {name}: {elapsed:.2f}ms (状态码：{response.status_code})")
        
        return elapsed
    except Exception as e:
        print(f"❌ {name}: 错误 - {e}")
        return None

print("=" * 60)
print("简单 API 性能测试")
print("=" * 60)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API 地址：{BASE_URL}")
print("=" * 60)
print()

# 测试斗首 API
print("【斗首择日 API】")
test_endpoint("获取山家五行", "/api/doushou/shanjia_wuxing?mountain=壬")
test_endpoint("获取天干化气", "/api/doushou/tiangan_huaqi?tiangan=甲")
test_endpoint("计算斗首五星", "/api/doushou/five_stars?mountain=壬&tiangan=甲")
print()

# 测试六壬 API
print("【大六壬排盘 API】")
test_endpoint("排天地盘", "/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅")
test_endpoint("大六壬综合评分", "/api/daliuren/score?shan=壬&ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=子")
print()

# 测试上传 API
print("【文件上传 API】")
test_endpoint("上传状态检查", "/api/upload/status/test-123")
print()

# 测试发布 API
print("【发布功能 API】")
publish_data = {
    'mountain': '壬',
    'four_pillars': {'year': '丙午', 'month': '辛卯', 'day': '己亥', 'hour': '甲子'},
    'dates': [{'date': '2026-11-15', 'score': 85}]
}
test_endpoint("发布日课", "/api/publish", method='POST', data=publish_data)
print()

print("=" * 60)
print("测试完成！")
print("=" * 60)
