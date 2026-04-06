#!/usr/bin/env python3
"""
主界面大六壬功能测试脚本
用于验证主界面是否能够正确显示大六壬相关数据
"""
import requests
import json
import time

# API基础URL
API_BASE_URL = 'http://localhost:5000/api'

# 测试用例
TEST_CASES = [
    # 基本测试用例
    {
        "mountain": "子山",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "min_daliuren_score": 80,
        "max_results": 10
    },
    {
        "mountain": "丑山",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "min_daliuren_score": 70,
        "max_results": 5
    }
]

def test_full_range_analyze(test_case):
    """测试完整日期范围分析API"""
    url = f"{API_BASE_URL}/doushou/full_range_analyze"
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_case, timeout=30)
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

def validate_full_range_result(result):
    """验证完整日期范围分析结果"""
    if not result.get('success'):
        return False, f"API调用失败: {result.get('error')}"
    
    data = result.get('data')
    if not data:
        return False, "API返回数据为空"
    
    # 验证必要字段
    required_fields = ['results']
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"
    
    # 验证日期列表
    if not isinstance(data.get('results'), list):
        return False, "日期列表格式错误"
    
    # 验证每个日期项的字段
    for date_item in data.get('results', []):
        required_date_fields = ['date', 'shichen', 'doushou_score', 'daliuren_score']
        for field in required_date_fields:
            if field not in date_item:
                return False, f"日期项缺少必要字段: {field}"
    
    return True, "数据结构完整"

def run_main_interface_tests():
    """运行主界面功能测试"""
    print("=" * 80)
    print("主界面大六壬功能测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0
    total_response_time = 0
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n测试用例 {i+1}/{total_tests}:")
        print(f"参数: {test_case}")
        
        # 测试完整日期范围分析API
        result = test_full_range_analyze(test_case)
        total_response_time += result.get('response_time', 0)
        
        is_valid, message = validate_full_range_result(result)
        
        if is_valid:
            print(f"✅ 测试通过: {message}")
            print(f"   响应时间: {result.get('response_time', 0):.4f}秒")
            
            # 打印关键结果
            data = result.get('data')
            if data:
                print(f"   找到日期数: {data.get('total_candidates')}")
                print(f"   日期列表: {len(data.get('results', []))}项")
                if data.get('results'):
                    print(f"   第一个日期: {data.get('results')[0].get('date')} {data.get('results')[0].get('shichen')}")
                    print(f"   大六壬评分: {data.get('results')[0].get('daliuren_score')}")
                    print(f"   综合评分: {data.get('results')[0].get('total_score')}")
            
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
    run_main_interface_tests()
