#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器端性能测试脚本
测试优化后的 API 性能
"""

import requests
import json
import time

def test_performance():
    """测试完整日期范围分析的性能"""
    
    print("=" * 60)
    print("仪度六壬择日系统 - 性能测试")
    print("=" * 60)
    
    # 测试参数
    test_cases = [
        {
            'name': '7 天范围测试',
            'start_date': '2026-11-01',
            'end_date': '2026-11-07',
            'expected': '20-30 秒'
        },
        {
            'name': '30 天范围测试',
            'start_date': '2026-11-01',
            'end_date': '2026-11-30',
            'expected': '1-2 分钟'
        }
    ]
    
    url = "http://localhost:5000/api/doushou/full_range_analyze"
    
    data = {
        "mountain": "壬",
        "start_date": "",
        "end_date": "",
        "min_daliuren_score": 70,
        "max_results": 5
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}/{len(test_cases)}】{test_case['name']}")
        print(f"日期范围：{test_case['start_date']} 至 {test_case['end_date']}")
        print(f"预期耗时：{test_case['expected']}")
        print("-" * 60)
        
        data['start_date'] = test_case['start_date']
        data['end_date'] = test_case['end_date']
        
        print("📡 正在发送请求...")
        start_time = time.time()
        
        try:
            response = requests.post(url, json=data, timeout=600)
            elapsed_time = time.time() - start_time
            
            print(f"\n✅ 响应状态码：{response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    print(f"⏱️  实际耗时：{elapsed_time:.2f} 秒")
                    print(f"📊 遍历天数：{result.get('total_days', 'N/A')}")
                    print(f"📊 候选数量：{result.get('total_candidates', 'N/A')}")
                    print(f"📊 返回结果：{len(result.get('results', []))} 个")
                    
                    # 检查性能数据
                    perf = result.get('performance', {})
                    if perf:
                        print(f"\n📈 性能统计:")
                        print(f"   - 总耗时：{perf.get('elapsed_seconds', 'N/A')} 秒")
                        print(f"   - 平均每个时辰：{perf.get('avg_ms_per_shichen', 'N/A')} ms")
                    
                    # 评估性能
                    print(f"\n🎯 性能评估:")
                    if elapsed_time < 60:
                        print(f"   ✨ 优秀！耗时 {elapsed_time:.2f}秒 (< 60 秒)")
                    elif elapsed_time < 120:
                        print(f"   👍 良好！耗时 {elapsed_time:.2f}秒 (60-120 秒)")
                    elif elapsed_time < 180:
                        print(f"   👌 一般！耗时 {elapsed_time:.2f}秒 (120-180 秒)")
                    else:
                        print(f"   ⚠️  需要优化！耗时 {elapsed_time:.2f}秒 (> 180 秒)")
                    
                    # 计算提升比例
                    if i == 2:  # 30 天测试
                        old_time = 420  # 7 分钟（优化前平均）
                        improvement = ((old_time - elapsed_time) / old_time) * 100
                        print(f"\n🚀 性能提升：约 {improvement:.1f}% (对比优化前的 {old_time/60:.1f} 分钟)")
                    
                else:
                    print(f"❌ API 返回错误：{result.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP 错误：{response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时（> 600 秒）")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到 API 服务器")
            print(f"   请确认 API 服务器正在运行：http://localhost:5000")
            return
        except Exception as e:
            print(f"❌ 错误：{e}")
        
        if i < len(test_cases):
            print(f"\n⏱️  等待 5 秒后进行下一个测试...")
            time.sleep(5)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    print("\n📝 测试报告:")
    print("请将以下信息发送给开发者:")
    print("-" * 60)
    print("1. 7 天范围测试耗时：______ 秒")
    print("2. 30 天范围测试耗时：______ 秒")
    print("3. 性能评估结果：______")
    print("4. 是否有错误：______")
    print("-" * 60)

if __name__ == '__main__':
    test_performance()
