#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
《毕法赋》规则批量匹配程序
对 8640 课例进行完整毕法赋规则匹配，生成 JSON 和 Excel 报告
"""

import json
import pandas as pd
from datetime import datetime
from bifa_rules_engine import BiFaRulesMatcher

def batch_match_bifa_rules():
    """批量匹配毕法赋规则"""
    print("="*70)
    print("  《毕法赋》规则批量匹配程序")
    print("="*70)
    print()
    
    # 加载 8640 课例数据
    print("加载 8640 课例数据...")
    try:
        with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\local_rules_matched_results.json', 'r', encoding='utf-8') as f:
            data_8640 = json.load(f)
        print(f"✓ 成功加载 {data_8640['matched']} 个课例")
    except Exception as e:
        print(f"✗ 加载失败：{e}")
        return
    
    # 创建匹配器
    matcher = BiFaRulesMatcher()
    
    # 批量匹配
    print("\n开始毕法赋规则匹配...")
    start_time = datetime.now()
    
    matched_results = data_8640.get('matched_results', {})
    bifa_results = {}
    
    total_count = 0
    matched_count = 0
    error_count = 0
    
    for key, ke_li in matched_results.items():
        try:
            # 匹配毕法赋规则
            bifa_result = matcher.match_all_rules(ke_li)
            
            # 保存结果
            bifa_results[key] = {
                'ri_gan_zhi': ke_li.get('ri_gan_zhi', ''),
                'yue': ke_li.get('yue', ''),
                'shi': ke_li.get('shi', ''),
                'primary_ke_jing': ke_li.get('primary_ke_jing', ''),
                'bifa_matched_count': bifa_result['matched_count'],
                'bifa_matched_rules': bifa_result['matched_rules']
            }
            
            total_count += 1
            if bifa_result['matched_count'] > 0:
                matched_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"匹配错误 {key}: {e}")
        
        # 进度显示
        if total_count % 1000 == 0:
            print(f"  已处理 {total_count}/{len(matched_results)} 课例...")
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    # 统计信息
    print("\n" + "="*70)
    print("  匹配完成统计")
    print("="*70)
    print(f"总算例数：{total_count}")
    print(f"匹配到规则：{matched_count} ({matched_count/total_count*100:.1f}%)")
    print(f"未匹配：{total_count - matched_count}")
    print(f"错误数：{error_count}")
    print(f"处理时间：{elapsed:.2f}秒")
    print(f"处理速度：{total_count/elapsed:.0f} 课/秒")
    
    # 课经分布统计
    print("\n毕法赋规则匹配分布：")
    rule_stats = {}
    for key, result in bifa_results.items():
        for rule in result.get('bifa_matched_rules', []):
            rule_name = rule.get('rule_name', '')
            if rule_name:
                rule_stats[rule_name] = rule_stats.get(rule_name, 0) + 1
    
    # 按匹配次数排序
    sorted_rules = sorted(rule_stats.items(), key=lambda x: x[1], reverse=True)
    for rule_name, count in sorted_rules[:20]:  # 显示前 20 条
        percentage = count / total_count * 100
        print(f"  {rule_name}: {count} ({percentage:.1f}%)")
    
    # 保存 JSON 结果
    output_json = {
        'timestamp': datetime.now().isoformat(),
        'total': total_count,
        'matched': matched_count,
        'errors': error_count,
        'elapsed_seconds': elapsed,
        'match_method': 'bifa_rules',
        'rule_statistics': rule_stats,
        'matched_results': bifa_results
    }
    
    json_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\bifa_matched_results.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ JSON 结果已保存：{json_file}")
    
    # 生成 Excel 报告
    print("\n生成 Excel 报告...")
    excel_data = []
    
    for key, result in bifa_results.items():
        # 提取规则名称列表
        rule_names = [rule['rule_name'] for rule in result.get('bifa_matched_rules', [])]
        
        row = {
            '课例 ID': key,
            '日干支': result.get('ri_gan_zhi', ''),
            '月将': result.get('yue', ''),
            '时辰': result.get('shi', ''),
            '课经': result.get('primary_ke_jing', ''),
            '毕法赋规则数': result.get('bifa_matched_count', 0),
            '毕法赋规则': ' | '.join(rule_names),
        }
        excel_data.append(row)
    
    # 创建 DataFrame
    df = pd.DataFrame(excel_data)
    
    # 保存 Excel
    excel_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\bifa_matched_results.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
    
    print(f"✓ Excel 报告已保存：{excel_file}")
    
    # 生成统计摘要
    print("\n" + "="*70)
    print("  毕法赋规则匹配摘要")
    print("="*70)
    
    # 按课经分组统计
    ke_jing_stats = {}
    for key, result in bifa_results.items():
        ke_jing = result.get('primary_ke_jing', '')
        if ke_jing not in ke_jing_stats:
            ke_jing_stats[ke_jing] = {'total': 0, 'with_bifa': 0}
        
        ke_jing_stats[ke_jing]['total'] += 1
        if result.get('bifa_matched_count', 0) > 0:
            ke_jing_stats[ke_jing]['with_bifa'] += 1
    
    print("\n按课经分布统计：")
    for ke_jing, stats in sorted(ke_jing_stats.items()):
        percentage = stats['with_bifa'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {ke_jing}: {stats['with_bifa']}/{stats['total']} ({percentage:.1f}%)")
    
    print("\n" + "="*70)
    print("  ✅ 毕法赋批量匹配完成！")
    print("="*70)

if __name__ == '__main__':
    batch_match_bifa_rules()
