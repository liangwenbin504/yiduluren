#!/usr/bin/env python3
"""
前端和后端大六壬计算结果比较脚本
用于验证前端和后端大六壬计算的一致性
"""
import requests
import json
import time
import re

# API基础URL
API_BASE_URL = 'http://localhost:5000/api'

# 测试用例
TEST_CASES = [
    # 基本测试用例
    {"ri_gan": "甲", "ri_zhi": "子", "yue_jiang": "亥", "shi_chen": "寅"},
    {"ri_gan": "乙", "ri_zhi": "丑", "yue_jiang": "子", "shi_chen": "卯"},
    {"ri_gan": "丙", "ri_zhi": "寅", "yue_jiang": "丑", "shi_chen": "辰"},
]

# 前端计算逻辑（从主界面.html中提取）
def frontend_calculate_tianpan(yue_jiang, shi_chen):
    """前端计算天盘"""
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 月将映射（根据月份）
    YUEJIANG_MAP = {
        1: '丑', 2: '子', 3: '亥', 4: '戌', 5: '酉', 6: '申',
        7: '未', 8: '午', 9: '巳', 10: '辰', 11: '卯', 12: '寅'
    }
    
    # 计算天盘（月将加时）
    yueJiangIndex = DIZHI.index(yue_jiang)
    shiChenIndex2 = DIZHI.index(shi_chen)
    tianPanArray = []
    for i in range(12):
        # 地盘第i位的天盘 = 月将 + (i - 时辰位)
        tianPanArray.append(DIZHI[(yueJiangIndex + i - shiChenIndex2 + 12) % 12])
    
    # 转换为对象形式：键是地盘地支，值是天盘地支
    tianPan = {}
    for i in range(12):
        tianPan[DIZHI[i]] = tianPanArray[i]
    
    return tianPan

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

def compare_tianpan(backend_tianpan, frontend_tianpan):
    """比较前端和后端的天盘计算结果"""
    if backend_tianpan == frontend_tianpan:
        return True, "天盘计算结果一致"
    else:
        # 找出不一致的地方
        differences = []
        for dizhi in backend_tianpan:
            if backend_tianpan[dizhi] != frontend_tianpan.get(dizhi):
                differences.append(f"{dizhi}: 后端={backend_tianpan[dizhi]}, 前端={frontend_tianpan.get(dizhi)}")
        return False, f"天盘计算结果不一致: {'; '.join(differences)}"

def run_comparison():
    """运行前端和后端计算结果比较"""
    print("=" * 80)
    print("前端和后端大六壬计算结果比较")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n测试用例 {i+1}/{total_tests}:")
        print(f"参数: {test_case}")
        
        # 测试后端API
        backend_result = test_backend_api(test_case)
        
        if not backend_result.get('success'):
            print(f"❌ 后端API测试失败: {backend_result.get('error')}")
            failed_tests += 1
            continue
        
        # 获取后端天盘
        backend_tianpan = backend_result.get('data', {}).get('tiandi_pan', {})
        
        # 前端计算天盘
        frontend_tianpan = frontend_calculate_tianpan(test_case['yue_jiang'], test_case['shi_chen'])
        
        # 比较天盘
        is_consistent, message = compare_tianpan(backend_tianpan, frontend_tianpan)
        
        if is_consistent:
            print(f"✅ 天盘计算结果一致")
            passed_tests += 1
        else:
            print(f"❌ {message}")
            print(f"   后端天盘: {backend_tianpan}")
            print(f"   前端天盘: {frontend_tianpan}")
            failed_tests += 1
    
    print("\n" + "=" * 80)
    print("比较结果汇总:")
    print(f"总测试用例: {total_tests}")
    print(f"一致: {passed_tests}")
    print(f"不一致: {failed_tests}")
    print(f"一致率: {(passed_tests/total_tests*100):.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    run_comparison()
