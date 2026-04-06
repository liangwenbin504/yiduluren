#!/usr/bin/env python3
"""
系统集成测试脚本
用于验证整个系统的功能，确保大六壬模块的修改不会影响其他功能
"""
import requests
import json
import time

# API基础URL
API_BASE_URL = 'http://localhost:5000/api'

# 测试用例
TEST_CASES = [
    # 1. 大六壬API测试
    {
        "name": "大六壬起课API",
        "url": f"{API_BASE_URL}/qike",
        "method": "POST",
        "data": {
            "ri_gan": "甲",
            "ri_zhi": "子",
            "yue_jiang": "亥",
            "shi_chen": "寅"
        },
        "required_fields": ["tiandi_pan", "si_ke", "sanchuan"]
    },
    
    # 2. 斗首API测试
    {
        "name": "斗首分析API",
        "url": f"{API_BASE_URL}/doushou/analyze",
        "method": "POST",
        "data": {
            "mountain": "子山",
            "year_gan": "甲",
            "month_gan": "丙",
            "day_gan": "戊",
            "hour_gan": "庚"
        },
        "required_fields": ["score", "shanjia_wuxing"]
    },
    
    # 3. 演禽API测试
    {
        "name": "演禽四禽API",
        "url": f"{API_BASE_URL}/yanqin/four_qin",
        "method": "POST",
        "data": {
            "year_zhi": "子",
            "month_zhi": "子",
            "day_zhi": "子",
            "hour_zhi": "子"
        },
        "required_fields": ["四禽"]
    },
    
    # 4. 四柱API测试
    {
        "name": "四柱API",
        "url": f"{API_BASE_URL}/sizhu",
        "method": "GET",
        "params": {
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 0
        },
        "required_fields": ["sizhu"]
    },
    
    # 5. 日期范围API测试
    {
        "name": "日期范围生成API",
        "url": f"{API_BASE_URL}/date_range/generate",
        "method": "POST",
        "data": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-03"
        },
        "required_fields": ["dates", "count"]
    }
]

def test_api(test_case):
    """测试API接口"""
    url = test_case.get('url')
    method = test_case.get('method', 'GET')
    data = test_case.get('data')
    params = test_case.get('params')
    
    try:
        start_time = time.time()
        
        if method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, params=params, timeout=10)
        
        end_time = time.time()
        
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "data": result,
            "response_time": end_time - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def validate_result(result, required_fields):
    """验证API返回结果"""
    if not result.get('success'):
        return False, f"API调用失败: {result.get('error')}"
    
    data = result.get('data')
    if not data:
        return False, "API返回数据为空"
    
    # 验证必要字段
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"
    
    return True, "数据结构完整"

def run_integration_tests():
    """运行系统集成测试"""
    print("=" * 80)
    print("系统集成测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0
    total_response_time = 0
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n测试用例 {i+1}/{total_tests}: {test_case.get('name')}")
        print(f"URL: {test_case.get('url')}")
        
        # 测试API
        result = test_api(test_case)
        total_response_time += result.get('response_time', 0)
        
        is_valid, message = validate_result(result, test_case.get('required_fields', []))
        
        if is_valid:
            print(f"✅ 测试通过: {message}")
            print(f"   响应时间: {result.get('response_time', 0):.4f}秒")
            passed_tests += 1
        else:
            print(f"❌ 测试失败: {message}")
            if not result.get('success'):
                print(f"   错误信息: {result.get('error')}")
            failed_tests += 1
    
    print("\n" + "=" * 80)
    print("测试结果汇总:")
    print(f"总测试用例: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
    if total_tests > 0:
        print(f"平均响应时间: {(total_response_time/total_tests):.4f}秒")
    print("=" * 80)

if __name__ == "__main__":
    run_integration_tests()
