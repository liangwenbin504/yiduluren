#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期筛选测试脚本
验证日期筛选的准确性、完整性和速度
"""

import requests
import json
import time

API_BASE_URL = 'http://localhost:5000/api'

def test_date_filter(start_date, end_date, mountain='子', min_daliuren_score=70, max_results=10, parallel_type='thread', max_workers=8):
    """测试日期筛选功能"""
    print(f"\n测试日期范围: {start_date} 至 {end_date}")
    print(f"并行类型: {parallel_type}, 最大并行数: {max_workers}")
    print("=" * 60)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 调用日期范围分析API
        url = f"{API_BASE_URL}/doushou/full_range_analyze"
        data = {
            "mountain": mountain,
            "start_date": start_date,
            "end_date": end_date,
            "min_daliuren_score": min_daliuren_score,
            "max_results": max_results,
            "parallel_type": parallel_type,
            "max_workers": max_workers
        }
        
        response = requests.post(url, json=data, timeout=600)  # 10分钟超时
        response.raise_for_status()
        result = response.json()
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 打印测试结果
        print(f"执行时间: {execution_time:.2f}秒")
        print(f"总天数: {result.get('total_days', 0)}")
        print(f"总课数: {result.get('total_days', 0) * 12}")
        print(f"符合条件的课数: {result.get('total_candidates', 0)}")
        print(f"返回结果数: {len(result.get('results', []))}")
        
        # 打印性能信息
        performance = result.get('performance', {})
        if performance:
            print(f"API处理时间: {performance.get('elapsed_seconds', 0):.2f}秒")
            print(f"实际并行数: {performance.get('parallel_workers', 0)}")
            print(f"内存使用: {performance.get('memory_used_mb', 0):.2f}MB")
        
        # 打印筛选规则和权重
        if 'filter_rules' in result:
            print("\n筛选规则:")
            for rule, value in result['filter_rules'].items():
                print(f"  {rule}: {value}")
        
        if 'score_weights' in result:
            print("\n评分权重:")
            for weight, value in result['score_weights'].items():
                print(f"  {weight}: {value}")
        
        # 打印前5个结果
        results = result.get('results', [])
        if results:
            print("\n前5个结果:")
            for i, item in enumerate(results[:5]):
                date = item.get('date')
                shichen = item.get('shichen')
                total_score = item.get('total_score')
                doushou_score = item.get('doushou_score')
                daliuren_score = item.get('daliuren_score')
                yanqin_score = item.get('yanqin_score')
                daliuren_keti = item.get('daliuren_keti', '')
                
                print(f"{i+1}. {date} {shichen}时 - 综合{total_score:.1f}分")
                print(f"   斗首: {doushou_score:.1f}, 六壬: {daliuren_score:.1f}, 演禽: {yanqin_score:.1f}")
                if daliuren_keti:
                    print(f"   课体: {daliuren_keti}")
        
        return True, execution_time, result
        
    except requests.RequestException as e:
        print(f"测试失败: {e}")
        return False, 0, None

def main():
    """主测试函数"""
    print("开始测试日期筛选功能...")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        # 线程池测试
        {"start_date": "2026-05-01", "end_date": "2026-05-31", "mountain": "子", "parallel_type": "thread", "max_workers": 8},
        {"start_date": "2026-05-01", "end_date": "2026-07-31", "mountain": "子", "parallel_type": "thread", "max_workers": 8},
        {"start_date": "2026-05-01", "end_date": "2026-10-31", "mountain": "子", "parallel_type": "thread", "max_workers": 8},
        # 进程池测试
        {"start_date": "2026-05-01", "end_date": "2026-05-31", "mountain": "子", "parallel_type": "process", "max_workers": 8},
        {"start_date": "2026-05-01", "end_date": "2026-07-31", "mountain": "子", "parallel_type": "process", "max_workers": 8},
        {"start_date": "2026-05-01", "end_date": "2026-10-31", "mountain": "子", "parallel_type": "process", "max_workers": 8},
        # 不同坐山测试
        {"start_date": "2026-05-01", "end_date": "2026-05-31", "mountain": "午", "parallel_type": "process", "max_workers": 8},
        # 不同评分要求测试
        {"start_date": "2026-05-01", "end_date": "2026-05-31", "mountain": "子", "min_daliuren_score": 80, "parallel_type": "process", "max_workers": 8},
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}")
        print("-" * 60)
        
        success, execution_time, result = test_date_filter(
            test_case["start_date"],
            test_case["end_date"],
            test_case.get("mountain", "子"),
            test_case.get("min_daliuren_score", 70),
            10,  # max_results
            test_case.get("parallel_type", "thread"),
            test_case.get("max_workers", 8)
        )
        
        results.append({
            "test_case": i+1,
            "start_date": test_case["start_date"],
            "end_date": test_case["end_date"],
            "mountain": test_case.get("mountain", "子"),
            "min_daliuren_score": test_case.get("min_daliuren_score", 70),
            "parallel_type": test_case.get("parallel_type", "thread"),
            "max_workers": test_case.get("max_workers", 8),
            "success": success,
            "execution_time": execution_time,
            "result": result
        })
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    total_time = sum(r["execution_time"] for r in results)
    
    print(f"总测试数: {total_tests}")
    print(f"成功测试数: {successful_tests}")
    print(f"失败测试数: {total_tests - successful_tests}")
    print(f"平均执行时间: {total_time / total_tests:.2f}秒")
    
    # 分析性能
    print("\n性能分析:")
    for r in results:
        if r["success"]:
            days = r["result"].get("total_days", 0)
            if days > 0:
                time_per_day = r["execution_time"] / days
                print(f"测试用例 {r['test_case']}: {days}天, {r['parallel_type']}, {r['max_workers']}线程, 每天耗时: {time_per_day:.4f}秒")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()
