#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
《毕法赋》规则批量匹配程序 v2.0
第二阶段：扩展至 30+ 条规则，集成旬空、丁神系统
"""

import json
import pandas as pd
from datetime import datetime
from bifa_rules_engine_v2 import BiFaRulesMatcherV2
from daliuren_base import enhance_ke_li_data

def batch_match_bifa_v2():
    """批量匹配毕法赋规则 v2"""
    print("="*70)
    print("  《毕法赋》规则批量匹配程序 v2.0")
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
    matcher = BiFaRulesMatcherV2()
    
    # 批量匹配
    print("\n开始毕法赋规则匹配（第二阶段）...")
    start_time = datetime.now()
    
    matched_results = data_8640.get('matched_results', {})
    bifa_results = {}
    
    total_count = 0
    matched_count = 0
    error_count = 0
    
    for key, ke_li in matched_results.items():
        try:
            # 增强课例数据（添加旬空、丁神等）
            ke_li_enhanced = enhance_ke_li_data(ke_li)
            
            # 匹配毕法赋规则
            bifa_result = matcher.match_all_rules(ke_li_enhanced)
            
            # 保存结果
            bifa_results[key] = {
                'ri_gan_zhi': ke_li.get('ri_gan_zhi', ''),
                'yue': ke_li.get('yue', ''),
                'shi': ke_li.get('shi', ''),
                'primary_ke_jing': ke_li.get('primary_ke_jing', ''),
                'bifa_matched_count': bifa_result['matched_count'],
                'bifa_matched_rules': bifa_result['matched_rules'],
                # 新增：增强数据
                'xun': ke_li_enhanced.get('xun', ''),
                'kong_wang': ke_li_enhanced.get('kong_wang', []),
                'ding_shen': ke_li_enhanced.get('ding_shen', ''),
                'chu_kong': ke_li_enhanced.get('chu_kong', False),
                'zhong_kong': ke_li_enhanced.get('zhong_kong', False),
                'mo_kong': ke_li_enhanced.get('mo_kong', False),
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
    
    # 规则分布统计
    print("\n毕法赋规则匹配分布：")
    rule_stats = {}
    for key, result in bifa_results.items():
        for rule in result.get('bifa_matched_rules', []):
            rule_name = rule.get('rule_name', '')
            if rule_name:
                rule_stats[rule_name] = rule_stats.get(rule_name, 0) + 1
    
    sorted_rules = sorted(rule_stats.items(), key=lambda x: x[1], reverse=True)
    for rule_name, count in sorted_rules:
        percentage = count / total_count * 100
        print(f"  {rule_name}: {count} ({percentage:.1f}%)")
    
    # 保存 JSON 结果
    output_json = {
        'timestamp': datetime.now().isoformat(),
        'total': total_count,
        'matched': matched_count,
        'errors': error_count,
        'elapsed_seconds': elapsed,
        'match_method': 'bifa_rules_v2',
        'rule_statistics': rule_stats,
        'matched_results': bifa_results
    }
    
    json_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\bifa_matched_results_v2.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ JSON 结果已保存：{json_file}")
    
    # 生成 Excel 报告
    print("\n生成 Excel 报告...")
    excel_data = []
    
    for key, result in bifa_results.items():
        rule_names = [rule['rule_name'] for rule in result.get('bifa_matched_rules', [])]
        
        row = {
            '课例 ID': key,
            '日干支': result.get('ri_gan_zhi', ''),
            '月将': result.get('yue', ''),
            '时辰': result.get('shi', ''),
            '课经': result.get('primary_ke_jing', ''),
            '旬': result.get('xun', ''),
            '旬空': ','.join(result.get('kong_wang', [])),
            '丁神': result.get('ding_shen', ''),
            '毕法赋规则数': result.get('bifa_matched_count', 0),
            '毕法赋规则': ' | '.join(rule_names),
        }
        excel_data.append(row)
    
    df = pd.DataFrame(excel_data)
    excel_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\bifa_matched_results_v2.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
    
    print(f"✓ Excel 报告已保存：{excel_file}")
    
    # 总结
    print("\n" + "="*70)
    print("  ✅ 毕法赋批量匹配 v2.0 完成！")
    print("="*70)
    print(f"\n新增功能：")
    print("  ✓ 集成旬空计算")
    print("  ✓ 集成丁神计算")
    print("  ✓ 规则扩展至 18 条")
    print(f"  ✓ 输出包含旬空、丁神信息")
    print()

if __name__ == '__main__':
    batch_match_bifa_v2()
