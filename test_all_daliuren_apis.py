#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试所有大六壬相关 API
"""

import requests
import time

BASE_URL = "http://localhost:5000"

def test_api(name, endpoint, method='GET', data=None):
    """测试 API"""
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   结果：成功")
            else:
                print(f"   错误：{data.get('error', '未知')}")
        else:
            print(f"   HTTP 错误：{response.text[:100]}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {name}: 异常 - {e}")
        return False

print("=" * 80)
print("测试所有大六壬相关 API")
print("=" * 80)

# 测试其他 API 看服务器是否正常
print("\n【基础 API 测试】")
test_api("斗首山家五行", "/api/doushou/shanjia_wuxing?mountain=壬")

print("\n【大六壬 API 测试】")
# 测试不同的端点
test_api("排天地盘 (GET)", "/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅")
test_api("发三传 (GET)", "/api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=寅")

# 测试 POST 端点
test_api("起四课 (POST)", "/api/daliuren/si_ke", method='POST', 
         data={'ri_gan': '甲', 'ri_zhi': '子', 'yuejiang': '亥', 'shichen': '寅'})

test_api("完整排盘 (POST)", "/api/daliuren/san_chuan", method='POST',
         data={'ri_gan': '甲', 'ri_zhi': '子', 'yue_jiang': '亥', 'shichen': '寅'})

test_api("大六壬评分 (GET)", "/api/daliuren/score?shan=壬&ri_gan=甲&ri_zhi=子&yue_jiang=亥&shi_chen=子")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)
