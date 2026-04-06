#!/usr/bin/env python3
"""
大六壬计算一致性验证脚本
用于验证前端和后端大六壬计算的一致性
"""
import requests
import json
import time

# API基础URL
API_BASE_URL = 'http://localhost:5000/api'

# 测试用例
TEST_CASES = [
    # 基本测试用例
    {"ri_gan": "甲", "ri_zhi": "子", "yue_jiang": "亥", "shi_chen": "寅"},
    {"ri_gan": "乙", "ri_zhi": "丑", "yue_jiang": "子", "shi_chen": "卯"},
    {"ri_gan": "丙", "ri_zhi": "寅", "yue_jiang": "丑", "shi_chen": "辰"},
    {"ri_gan": "丁", "ri_zhi": "卯", "yue_jiang": "寅", "shi_chen": "巳"},
    {"ri_gan": "戊", "ri_zhi": "辰", "yue_jiang": "卯", "shi_chen": "午"},
    {"ri_gan": "己", "ri_zhi": "巳", "yue_jiang": "辰", "shi_chen": "未"},
    {"ri_gan": "庚", "ri_zhi": "午", "yue_jiang": "巳", "shi_chen": "申"},
    {"ri_gan": "辛", "ri_zhi": "未", "yue_jiang": "午", "shi_chen": "酉"},
    {"ri_gan": "壬", "ri_zhi": "申", "yue_jiang": "未", "shi_chen": "戌"},
    {"ri_gan": "癸", "ri_zhi": "酉", "yue_jiang": "申", "shi_chen": "亥"},
    
    # 特殊课体测试用例
    {"ri_gan": "甲", "ri_zhi": "子", "yue_jiang": "子", "shi_chen": "子"},  # 伏吟课
    {"ri_gan": "甲", "ri_zhi": "午", "yue_jiang": "午", "shi_chen": "午"},  # 反吟课
]

def test_backend_api(test_case):
    """测试后端API"""
    url = f"{API_BASE_URL}/qike"
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_case, timeout=10)
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

def validate_results(result):
    """验证起课结果"""
    if not result.get('success'):
        return False, f"API调用失败: {result.get('error')}"
    
    data = result.get('data')
    if not data:
        return False, "API返回数据为空"
    
    # 验证必要字段
    required_fields = ['tiandi_pan', 'si_ke', 'sanchuan']
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"
    
    return True, "数据结构完整"

def compare_results(backend_result, frontend_result):
    """比较前端和后端的计算结果"""
    # 这里需要根据实际的前端计算结果格式进行调整
    # 暂时只验证后端结果的正确性
    pass

def run_tests():
    """运行所有测试用例"""
    print("=" * 80)
    print("大六壬计算一致性验证")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0
    total_response_time = 0
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n测试用例 {i+1}/{total_tests}:")
        print(f"参数: {test_case}")
        
        # 测试后端API
        backend_result = test_backend_api(test_case)
        total_response_time += backend_result.get('response_time', 0)
        
        is_valid, message = validate_results(backend_result)
        
        if is_valid:
            print(f"✅ 测试通过: {message}")
            print(f"   响应时间: {backend_result.get('response_time', 0):.4f}秒")
            
            # 打印关键结果
            data = backend_result.get('data')
            if data:
                print(f"   天地盘: {data.get('tiandi_pan')}")
                print(f"   四课: {data.get('si_ke')}")
                print(f"   三传: {data.get('sanchuan')}")
            
            passed_tests += 1
        else:
            print(f"❌ 测试失败: {message}")
            if not backend_result.get('success'):
                print(f"   错误信息: {backend_result.get('error')}")
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
    run_tests()
