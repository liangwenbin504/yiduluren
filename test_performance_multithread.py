#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器端性能测试脚本 - 多线程版本
测试优化后的 API 性能
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime

def test_date_range(test_name, start_date, end_date, mountain="壬", min_score=70, max_results=5):
    """测试单个日期范围"""
    
    url = "http://localhost:5000/api/doushou/full_range_analyze"
    
    data = {
        "mountain": mountain,
        "start_date": start_date,
        "end_date": end_date,
        "min_daliuren_score": min_score,
        "max_results": max_results
    }
    
    print(f"\n📡 开始测试：{test_name}")
    print(f"   日期范围：{start_date} 至 {end_date}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=data, timeout=600)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                perf = result.get('performance', {})
                
                result_data = {
                    'test_name': test_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'elapsed_seconds': round(elapsed_time, 2),
                    'total_days': result.get('total_days', 0),
                    'total_candidates': result.get('total_candidates', 0),
                    'results_count': len(result.get('results', [])),
                    'performance': perf,
                    'results': result.get('results', [])
                }
                
                print(f"✅ 完成！耗时：{elapsed_time:.2f}秒")
                print(f"   遍历：{result.get('total_days')}天，候选：{result.get('total_candidates')}个，返回：{len(result.get('results', []))}个")
                
                if perf:
                    print(f"   平均每个时辰：{perf.get('avg_ms_per_shichen', 'N/A')}ms")
                
                return result_data
            else:
                print(f"❌ API 返回错误：{result.get('error', '未知错误')}")
                return None
        else:
            print(f"❌ HTTP 错误：{response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（> 600 秒）")
        return None
    except Exception as e:
        print(f"❌ 错误：{e}")
        return None

def run_multithread_tests():
    """多线程并行测试"""
    
    print("=" * 70)
    print("仪度六壬择日系统 - 多线程性能测试")
    print("=" * 70)
    print(f" 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 测试用例配置
    test_cases = [
        {
            'name': '7 天测试',
            'start': '2026-11-01',
            'end': '2026-11-07'
        },
        {
            'name': '30 天测试',
            'start': '2026-11-01',
            'end': '2026-11-30'
        },
        {
            'name': '3 个月测试',
            'start': '2026-11-01',
            'end': '2027-01-31'
        },
        {
            'name': '1 年测试',
            'start': '2026-11-01',
            'end': '2027-10-31'
        },
        {
            'name': '3 年测试',
            'start': '2026-11-01',
            'end': '2029-10-31'
        },
        {
            'name': '10 年测试',
            'start': '2026-11-01',
            'end': '2036-10-31'
        }
    ]
    
    all_results = []
    
    # 使用线程池并行执行
    print(f"\n🚀 启动 {len(test_cases)} 个线程并行测试...")
    print("-" * 70)
    
    with ThreadPoolExecutor(max_workers=len(test_cases)) as executor:
        # 提交所有测试任务
        future_to_test = {
            executor.submit(
                test_date_range,
                tc['name'],
                tc['start'],
                tc['end']
            ): tc for tc in test_cases
        }
        
        # 收集结果
        for future in as_completed(future_to_test):
            test_case = future_to_test[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"❌ {test_case['name']} 测试异常：{e}")
    
    # 保存结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    # 按耗时排序
    all_results.sort(key=lambda x: x['elapsed_seconds'])
    
    for i, result in enumerate(all_results, 1):
        days = (datetime.strptime(result['end_date'], '%Y-%m-%d') - 
                datetime.strptime(result['start_date'], '%Y-%m-%d')).days + 1
        print(f"{i}. {result['test_name']}: {result['elapsed_seconds']:.2f}秒 "
              f"({days}天，{result['total_candidates']}候选)")
    
    # 保存到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'performance_test_results_{timestamp}.json'
    
    report_data = {
        'test_time': datetime.now().isoformat(),
        'test_mode': 'multithread',
        'total_tests': len(all_results),
        'results': all_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试结果已保存到：{output_file}")
    
    # 生成文本报告
    report_file = f'performance_test_report_{timestamp}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("仪度六壬择日系统 - 性能测试报告\n")
        f.write("=" * 70 + "\n")
        f.write(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试模式：多线程并行\n")
        f.write(f"总测试数：{len(all_results)}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("详细结果:\n")
        f.write("-" * 70 + "\n")
        for result in all_results:
            days = (datetime.strptime(result['end_date'], '%Y-%m-%d') - 
                    datetime.strptime(result['start_date'], '%Y-%m-%d')).days + 1
            f.write(f"\n{result['test_name']}:\n")
            f.write(f"  日期范围：{result['start_date']} 至 {result['end_date']} ({days}天)\n")
            f.write(f"  总耗时：{result['elapsed_seconds']:.2f}秒\n")
            f.write(f"  遍历天数：{result['total_days']}\n")
            f.write(f"  候选数量：{result['total_candidates']}\n")
            f.write(f"  返回结果：{result['results_count']}个\n")
            
            if result.get('performance'):
                perf = result['performance']
                f.write(f"  性能统计:\n")
                f.write(f"    - 总耗时：{perf.get('elapsed_seconds', 'N/A')}秒\n")
                f.write(f"    - 平均每个时辰：{perf.get('avg_ms_per_shichen', 'N/A')}ms\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("测试完成！\n")
        f.write("=" * 70 + "\n")
    
    print(f"📄 文本报告已保存到：{report_file}")
    
    return all_results

if __name__ == '__main__':
    results = run_multithread_tests()
    
    print("\n" + "=" * 70)
    print("🎉 所有测试完成！")
    print("=" * 70)
