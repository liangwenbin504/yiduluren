#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器端性能测试脚本 - 顺序测试版本
按顺序测试不同日期范围，每个测试完成后保存结果
"""

import requests
import json
import time
import os
from datetime import datetime

def test_and_save(test_name, start_date, end_date, output_file):
    """测试并保存结果"""
    
    print(f"\n{'='*70}")
    print(f"📡 开始测试：{test_name}")
    print(f"   日期范围：{start_date} 至 {end_date}")
    print(f"{'='*70}")
    
    url = "http://localhost:5000/api/doushou/full_range_analyze"
    
    data = {
        "mountain": "壬",
        "start_date": start_date,
        "end_date": end_date,
        "min_daliuren_score": 70,
        "max_results": 5
    }
    
    start_time = time.time()
    
    try:
        # 使用更大的超时时间
        timeout = max(600, (datetime.strptime(end_date, '%Y-%m-%d') - 
                          datetime.strptime(start_date, '%Y-%m-%d')).days * 2)
        
        print(f"⏱️  超时设置：{timeout}秒")
        print(f"📡 发送请求...（这可能需要几分钟）")
        
        response = requests.post(url, json=data, timeout=timeout)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                perf = result.get('performance', {})
                
                result_data = {
                    'test_name': test_name,
                    'test_time': datetime.now().isoformat(),
                    'start_date': start_date,
                    'end_date': end_date,
                    'elapsed_seconds': round(elapsed_time, 2),
                    'total_days': result.get('total_days', 0),
                    'total_candidates': result.get('total_candidates', 0),
                    'results_count': len(result.get('results', [])),
                    'performance': perf,
                    'results': result.get('results', [])
                }
                
                # 保存到文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ 测试完成！")
                print(f"   耗时：{elapsed_time:.2f}秒")
                print(f"   遍历：{result.get('total_days')}天")
                print(f"   候选：{result.get('total_candidates')}个")
                print(f"   返回：{len(result.get('results', []))}个")
                
                if perf:
                    print(f"   平均每个时辰：{perf.get('avg_ms_per_shichen', 'N/A')}ms")
                
                print(f"\n💾 结果已保存到：{output_file}")
                
                return result_data
            else:
                print(f"❌ API 返回错误：{result.get('error', '未知错误')}")
                return None
        else:
            print(f"❌ HTTP 错误：{response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（>{timeout}秒）")
        return None
    except Exception as e:
        print(f"❌ 错误：{e}")
        return None

def main():
    """主测试流程"""
    
    print("="*70)
    print("仪度六壬择日系统 - 性能测试（顺序版）")
    print("="*70)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试计划
    test_plan = [
        ('7 天测试', '2026-11-01', '2026-11-07'),
        ('30 天测试', '2026-11-01', '2026-11-30'),
        ('3 个月测试', '2026-11-01', '2027-01-31'),
        ('1 年测试', '2026-11-01', '2027-10-31'),
        ('3 年测试', '2026-11-01', '2029-10-31'),
        ('10 年测试', '2026-11-01', '2036-10-31')
    ]
    
    all_results = []
    
    for i, (test_name, start_date, end_date) in enumerate(test_plan, 1):
        print(f"\n\n🎯 测试 {i}/{len(test_plan)}: {test_name}")
        
        output_file = f'test_result_{test_name.replace(" ", "_")}.json'
        
        result = test_and_save(test_name, start_date, end_date, output_file)
        
        if result:
            all_results.append(result)
        
        # 如果不是最后一个测试，等待 10 秒
        if i < len(test_plan):
            print(f"\n⏱️  等待 10 秒后进行下一个测试...")
            time.sleep(10)
    
    # 生成汇总报告
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    if all_results:
        for i, result in enumerate(all_results, 1):
            days = (datetime.strptime(result['end_date'], '%Y-%m-%d') - 
                    datetime.strptime(result['start_date'], '%Y-%m-%d')).days + 1
            print(f"{i}. {result['test_name']}: {result['elapsed_seconds']:.2f}秒 "
                  f"({days}天，{result['total_candidates']}候选)")
        
        # 保存汇总报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f'performance_summary_{timestamp}.txt'
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("仪度六壬择日系统 - 性能测试汇总报告\n")
            f.write("="*70 + "\n")
            f.write(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总测试数：{len(all_results)}\n")
            f.write("="*70 + "\n\n")
            
            for result in all_results:
                days = (datetime.strptime(result['end_date'], '%Y-%m-%d') - 
                        datetime.strptime(result['start_date'], '%Y-%m-%d')).days + 1
                f.write(f"{result['test_name']}:\n")
                f.write(f"  日期范围：{result['start_date']} 至 {result['end_date']} ({days}天)\n")
                f.write(f"  总耗时：{result['elapsed_seconds']:.2f}秒\n")
                f.write(f"  遍历天数：{result['total_days']}\n")
                f.write(f"  候选数量：{result['total_candidates']}\n")
                f.write(f"  返回结果：{result['results_count']}个\n")
                if result.get('performance'):
                    perf = result['performance']
                    f.write(f"  性能：{perf.get('elapsed_seconds', 'N/A')}秒 "
                           f"(平均{perf.get('avg_ms_per_shichen', 'N/A')}ms/时辰)\n")
                f.write("\n")
            
            f.write("="*70 + "\n")
            f.write("所有测试完成！\n")
            f.write("="*70 + "\n")
        
        print(f"\n📄 汇总报告已保存到：{summary_file}")
    else:
        print("\n❌ 没有成功的测试结果")
    
    print("\n" + "="*70)
    print("🎉 测试流程完成！")
    print("="*70)

if __name__ == '__main__':
    main()
