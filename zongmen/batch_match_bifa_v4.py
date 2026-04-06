#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋 v4.0 批量匹配程序
第四阶段：集成天将、课体格局，性能优化
"""

import json
import time
import pandas as pd
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from daliuren_base import enhance_ke_li_data
from bifa_rules_engine_v4 import BiFaRulesMatcherV4

def load_local_matched_results() -> Dict:
    """加载本地已匹配的课例结果"""
    try:
        # 使用 720 课例数据库（8640 课）
        with open('data/720_ke_li_jiu_zong_men.json', 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        # 数据结构：{metadata: {...}, ke_li: {...}}
        if 'ke_li' in all_data:
            ke_li_data = all_data['ke_li']
        else:
            # 过滤掉 metadata
            ke_li_data = {k: v for k, v in all_data.items() if k != 'metadata'}
        
        return ke_li_data
    except FileNotFoundError:
        print("未找到本地课例文件：data/720_ke_li_jiu_zong_men.json")
        return {}

def match_single_ke_li(args):
    """匹配单个课例（用于并行处理）"""
    key, ke_li, year = args
    matcher = BiFaRulesMatcherV4()
    
    # 增强课例数据（添加天将、课体格局等）
    ke_li_enhanced = enhance_ke_li_data(ke_li, year=year)
    
    # 匹配毕法赋规则
    bifa_result = matcher.match_all_rules(ke_li_enhanced)
    
    # 提取关键信息
    result = {
        'ri_gan_zhi': ke_li.get('ri_gan_zhi', ''),
        'shi': ke_li.get('shi', ''),
        'yue': ke_li.get('yue', ''),
        'chu_chuan': ke_li.get('chu_chuan', ''),
        'zhong_chuan': ke_li.get('zhong_chuan', ''),
        'mo_chuan': ke_li.get('mo_chuan', ''),
        'bifa_matched_count': bifa_result['matched_count'],
        'bifa_matched_rules': bifa_result['matched_rules'],
        'zong_men': ke_li_enhanced.get('zong_men', ''),
        'ke_ti_ge_ju': ke_li_enhanced.get('ke_ti_ge_ju', []),
        'te_shu_ge_ju': ke_li_enhanced.get('te_shu_ge_ju', []),
        'chu_tian_jiang': ke_li_enhanced.get('chu_tian_jiang', ''),
        'zhong_tian_jiang': ke_li_enhanced.get('zhong_tian_jiang', ''),
        'mo_tian_jiang': ke_li_enhanced.get('mo_tian_jiang', ''),
        'gui_ren_day': ke_li_enhanced.get('gui_ren_day', ''),
        'yue_jiang': ke_li_enhanced.get('yue_jiang', ''),
        'kong_wang': ke_li_enhanced.get('kong_wang', []),
        'ding_shen': ke_li_enhanced.get('ding_shen', ''),
        'sang_men': ke_li_enhanced.get('sang_men', ''),
        'diao_ke': ke_li_enhanced.get('diao_ke', ''),
        'bing_fu': ke_li_enhanced.get('bing_fu', ''),
        'chu_kong': ke_li_enhanced.get('chu_kong', False),
        'zhong_kong': ke_li_enhanced.get('zhong_kong', False),
        'mo_kong': ke_li_enhanced.get('mo_kong', False),
    }
    
    return key, result

def batch_match_bifa_v4():
    """批量匹配毕法赋 v4.0（支持并行处理）"""
    print("="*80)
    print("  毕法赋规则匹配系统 v4.0")
    print("  第四阶段：集成天将、课体格局，扩展至 50+ 条规则")
    print("="*80)
    print()
    
    # 加载本地课例
    print("正在加载本地课例...")
    local_matched = load_local_matched_results()
    
    if not local_matched:
        print("课例加载失败，退出程序")
        return
    
    total_ke_li = len(local_matched)
    print(f"已加载 {total_ke_li} 个课例")
    print()
    
    # 准备匹配数据
    year = 2024
    match_args = [(key, ke_li, year) for key, ke_li in local_matched.items()]
    
    # 使用并行处理优化性能
    print("正在并行匹配毕法赋规则...")
    start_time = time.time()
    
    bifa_results = {}
    processed = 0
    
    # 使用线程池并行处理（4 个线程）
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(match_single_ke_li, args): args[0] for args in match_args}
        
        for future in as_completed(futures):
            try:
                key, result = future.result()
                bifa_results[key] = result
                processed += 1
                
                if processed % 1000 == 0:
                    elapsed = time.time() - start_time
                    speed = processed / elapsed
                    print(f"  已处理 {processed}/{total_ke_li} 个课例 ({processed/total_ke_li*100:.1f}%), 速度：{speed:.1f} 课例/秒")
                
            except Exception as e:
                print(f"处理课例时出错：{e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    speed = total_ke_li / total_time
    
    print()
    print(f"匹配完成！")
    print(f"  总课例数：{total_ke_li}")
    print(f"  总耗时：{total_time:.2f} 秒")
    print(f"  处理速度：{speed:.1f} 课例/秒")
    print()
    
    # 统计匹配情况
    print("正在统计匹配结果...")
    total_matched = sum(1 for r in bifa_results.values() if r['bifa_matched_count'] > 0)
    avg_rules = sum(r['bifa_matched_count'] for r in bifa_results.values()) / total_ke_li
    
    print(f"  匹配课例数：{total_matched}/{total_ke_li} ({total_matched/total_ke_li*100:.1f}%)")
    print(f"  平均每课匹配规则数：{avg_rules:.2f} 条")
    print()
    
    # 保存 JSON 结果
    print("正在保存匹配结果...")
    try:
        with open('bifa_matched_results_v4.json', 'w', encoding='utf-8') as f:
            json.dump(bifa_results, f, ensure_ascii=False, indent=2)
        print("  JSON 结果已保存：bifa_matched_results_v4.json")
    except Exception as e:
        print(f"  保存 JSON 失败：{e}")
    
    # 转换为 Excel 格式
    print("正在生成 Excel 报表...")
    try:
        excel_data = []
        for key, result in bifa_results.items():
            row = {
                '课例编号': key,
                '日干支': result['ri_gan_zhi'],
                '时辰': result['shi'],
                '月份': result['yue'],
                '初传': result['chu_chuan'],
                '中传': result['zhong_chuan'],
                '末传': result['mo_chuan'],
                '宗门': result['zong_men'],
                '格局': ','.join(result['ke_ti_ge_ju']),
                '特殊格局': ','.join(result['te_shu_ge_ju']),
                '初传天将': result['chu_tian_jiang'],
                '中传天将': result['zhong_tian_jiang'],
                '末传天将': result['mo_tian_jiang'],
                '贵人': result['gui_ren_day'],
                '月将': result['yue_jiang'],
                '旬空': ','.join(result['kong_wang']),
                '丁神': result['ding_shen'],
                '丧门': result['sang_men'],
                '吊客': result['diao_ke'],
                '病符': result['bing_fu'],
                '初传空': '是' if result['chu_kong'] else '否',
                '中传空': '是' if result['zhong_kong'] else '否',
                '末传空': '是' if result['mo_kong'] else '否',
                '匹配规则数': result['bifa_matched_count'],
                '匹配规则': json.dumps(result['bifa_matched_rules'], ensure_ascii=False)
            }
            excel_data.append(row)
        
        df = pd.DataFrame(excel_data)
        df.to_excel('bifa_matched_results_v4.xlsx', index=False)
        print("  Excel 报表已保存：bifa_matched_results_v4.xlsx")
    except Exception as e:
        print(f"  生成 Excel 失败：{e}")
    
    print()
    print("="*80)
    print("  第四阶段批量匹配完成！")
    print("="*80)
    print()
    
    # 输出前 10 个课例的匹配详情
    print("前 10 个课例匹配详情：")
    print("-" * 80)
    for i, (key, result) in enumerate(list(bifa_results.items())[:10]):
        print(f"\n课例 {i+1}: {result['ri_gan_zhi']} ({key})")
        print(f"  三传：{result['chu_chuan']} {result['zhong_chuan']} {result['mo_chuan']}")
        print(f"  宗门：{result['zong_men']}")
        print(f"  格局：{', '.join(result['ke_ti_ge_ju']) if result['ke_ti_ge_ju'] else '无'}")
        print(f"  匹配规则数：{result['bifa_matched_count']}")
        if result['bifa_matched_rules']:
            print(f"  匹配规则:")
            for rule in result['bifa_matched_rules'][:3]:  # 只显示前 3 条
                print(f"    - {rule.get('rule_name', '')}: {rule.get('reasoning', '')}")

if __name__ == '__main__':
    batch_match_bifa_v4()
