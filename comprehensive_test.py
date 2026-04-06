#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - 全面测试脚本
测试所有核心功能和 API 接口
"""

import sys
import os
import requests
import json
from datetime import datetime

# 配置
API_BASE_URL = 'http://localhost:5000'
FRONTEND_URL = 'http://localhost:8000'

print("=" * 80)
print("仪度六壬择日系统 - 全面测试")
print("=" * 80)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 测试结果统计
test_results = {
    'passed': 0,
    'failed': 0,
    'total': 0
}

def test_api(name, url, method='GET', data=None, expected_status=200):
    """测试 API 接口"""
    test_results['total'] += 1
    print(f"\n[{test_results['total']}] 测试：{name}")
    print(f"URL: {url}")
    print(f"方法：{method}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ 通过 (状态码：{response.status_code})")
            test_results['passed'] += 1
            return True, response
        else:
            print(f"❌ 失败 (状态码：{response.status_code}, 期望：{expected_status})")
            test_results['failed'] += 1
            return False, response
    except Exception as e:
        print(f"❌ 异常：{str(e)}")
        test_results['failed'] += 1
        return False, None

# 1. 测试服务器连通性
print("\n" + "=" * 80)
print("【1】服务器连通性测试")
print("=" * 80)

test_api("API 服务器根路径", f"{API_BASE_URL}/")
test_api("前端服务器", f"{FRONTEND_URL}/", expected_status=200)

# 2. 测试四柱计算 API
print("\n" + "=" * 80)
print("【2】四柱计算 API 测试")
print("=" * 80)

test_api(
    "四柱计算 - 正常日期",
    f"{API_BASE_URL}/api/sizhu",
    data={
        'year': 2026,
        'month': 3,
        'day': 29,
        'hour': 18
    },
    method='POST'
)

test_api(
    "四柱计算 - 边界日期",
    f"{API_BASE_URL}/api/sizhu",
    data={
        'year': 2027,
        'month': 1,
        'day': 1,
        'hour': 0
    },
    method='POST'
)

# 3. 测试斗首 API
print("\n" + "=" * 80)
print("【3】斗首择日 API 测试")
print("=" * 80)

test_api(
    "斗首山家五行",
    f"{API_BASE_URL}/api/doushou/shanjia_wuxing?mountain=壬"
)

test_api(
    "斗首天干化气",
    f"{API_BASE_URL}/api/doushou/tiangan_huaqi?tiangan=甲"
)

test_api(
    "斗首五星",
    f"{API_BASE_URL}/api/doushou/five_stars?mountain=壬&tiangan=甲"
)

test_api(
    "斗首分析",
    f"{API_BASE_URL}/api/doushou/analyze",
    method='POST',
    data={
        'mountain': '壬',
        'date': '2026-03-29',
        'hour': '酉'
    }
)

# 4. 测试日期范围分析 API
print("\n" + "=" * 80)
print("【4】日期范围分析 API 测试")
print("=" * 80)

test_api(
    "完整日期范围分析",
    f"{API_BASE_URL}/api/doushou/full_range_analyze",
    method='POST',
    data={
        'mountain': '壬',
        'start_date': '2026-03-20',
        'end_date': '2026-04-20',
        'min_daliuren_score': 70,
        'max_results': 5
    },
    expected_status=200
)

# 5. 测试导出文档 API
print("\n" + "=" * 80)
print("【5】导出文档 API 测试")
print("=" * 80)

success, response = test_api(
    "导出 docx 文档",
    f"{API_BASE_URL}/api/export/docx",
    method='POST',
    data={
        'title_type': '安葬吉日',
        'mountain': '壬',
        'dates': [
            {'date': '2026-03-23', 'hour': '子', 'score': '95'},
            {'date': '2026-03-24', 'hour': '丑', 'score': '92'}
        ],
        'keti_list': ['元首课', '龙德课'],
        'evaluation': '此课格龙德贵人照临，大吉大利。'
    }
)

if success and response:
    result = response.json()
    if result.get('success'):
        print(f"✅ 文件生成成功：{result.get('filename')}")
        
        # 测试下载
        download_url = result.get('download_url')
        if download_url:
            test_api(
                "下载导出文件",
                f"{API_BASE_URL}{download_url}"
            )
    else:
        print(f"❌ 导出失败：{result.get('error')}")

# 6. 性能测试
print("\n" + "=" * 80)
print("【6】性能测试")
print("=" * 80)

import time

start = time.time()
test_api(
    "日期范围分析响应时间",
    f"{API_BASE_URL}/api/doushou/full_range_analyze",
    method='POST',
    data={
        'mountain': '壬',
        'start_date': '2026-03-20',
        'end_date': '2026-04-20',
        'min_daliuren_score': 70,
        'max_results': 3
    }
)
elapsed = time.time() - start
print(f"响应时间：{elapsed:.2f}秒")

if elapsed < 3:
    print("✅ 性能良好 (< 3 秒)")
elif elapsed < 10:
    print("⚠️  性能一般 (< 10 秒)")
else:
    print("❌ 性能较差 (> 10 秒)")

# 7. 错误处理测试
print("\n" + "=" * 80)
print("【7】错误处理测试")
print("=" * 80)

test_api(
    "错误处理 - 无效参数",
    f"{API_BASE_URL}/api/sizhu",
    method='POST',
    data={},
    expected_status=200  # 应该返回错误信息，但状态码仍是 200
)

test_api(
    "错误处理 - 不存在的路径",
    f"{API_BASE_URL}/api/nonexistent",
    expected_status=404
)

# 输出测试报告
print("\n" + "=" * 80)
print("【测试报告】")
print("=" * 80)
print(f"总测试数：{test_results['total']}")
print(f"✅ 通过：{test_results['passed']}")
print(f"❌ 失败：{test_results['failed']}")
print(f"通过率：{test_results['passed']/test_results['total']*100:.1f}%")
print("=" * 80)

if test_results['failed'] == 0:
    print("🎉 所有测试通过！系统运行正常！")
else:
    print(f"⚠️  有 {test_results['failed']} 个测试失败，请检查系统！")

print("=" * 80)
