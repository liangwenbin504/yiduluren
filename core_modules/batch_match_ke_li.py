#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量重新匹配 64 课体与 8640 课例
使用完整的课体判断算法
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from complete_qi_ke_engine import CompleteQiKeEngine
from ke_ti_judge import KeTiJudgeCalculator
from accurate_ke_jing_matcher import AccurateKeJingMatcher


def batch_match_all_ke_li():
    """批量匹配所有课例"""
    print("=" * 80)
    print("批量重新匹配 64 课体与 8640 课例")
    print("=" * 80)
    
    # 加载课例数据
    with open('data/720_ke_li.json', 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
    
    print(f"\n已加载 {len(ke_li_data)} 个课例")
    
    # 初始化引擎
    engine = CompleteQiKeEngine()
    matcher = AccurateKeJingMatcher()
    ke_ti_judge = KeTiJudgeCalculator()
    
    # 统计
    total_matched = 0
    all_ke_ti_count = {}
    
    # 逐个处理课例
    processed = 0
    for ke_key, ke_data in ke_li_data.items():
        ri_gan_zhi = ke_data.get('ri_gan_zhi', '')
        yue = ke_data.get('yue', '')
        shi = ke_data.get('shi', '')
        yue_jiang = ke_data.get('yue_jiang', '')
        
        if not all([ri_gan_zhi, yue, shi, yue_jiang]):
            continue
        
        try:
            # 起课
            result = engine.qi_ke(ri_gan_zhi, yue_jiang, shi, lunar_month=1, nian_zhi=yue)
            
            # 使用课体判断
            sike = result['四课']
            sanchuan = result['三传']
            tiandi_pan = result['天地盘']['天地对应']
            ri_gan = ri_gan_zhi[0]
            ri_zhi = ri_gan_zhi[1]
            
            ke_ti_list = ke_ti_judge.judge_all_ke_ti(
                sike, sanchuan, tiandi_pan, ri_gan, ri_zhi,
                yue, shi, lunar_month=1, nian_zhi=yue
            )
            
            # 更新课例数据
            ke_data['matched_ke_jing'] = ke_ti_list
            ke_data['ke_ti_count'] = len(ke_ti_list)
            
            # 统计
            for ke_name in ke_ti_list:
                all_ke_ti_count[ke_name] = all_ke_ti_count.get(ke_name, 0) + 1
            
            total_matched += 1
            processed += 1
            
            if processed % 1000 == 0:
                print(f"已处理 {processed}/{len(ke_li_data)} 个课例...")
        
        except Exception as e:
            print(f"处理课例 {ke_key} 失败：{e}")
            continue
    
    # 保存更新后的数据
    output_file = 'data/720_ke_li_matched.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ke_li_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n已保存匹配结果到：{output_file}")
    print(f"成功匹配：{total_matched}/{len(ke_li_data)} 个课例")
    
    # 统计课体分布
    print(f"\n64 课体分布统计:")
    print("=" * 80)
    sorted_ke_ti = sorted(all_ke_ti_count.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_ke_ti:
        print(f"{name:15s}: {count:4d} 课")
    
    print(f"\n总计：{len(all_ke_ti_count)} 个课体被匹配")
    
    # 检查是否有未匹配的课体
    with open('data/64_ke_jing_accurate.json', 'r', encoding='utf-8') as f:
        ke_jing_data = json.load(f)
    
    all_ke_ti_names = {v['ke_name'] for v in ke_jing_data['courses'].values()}
    matched_ke_ti_names = set(all_ke_ti_count.keys())
    unmatched = all_ke_ti_names - matched_ke_ti_names
    
    if unmatched:
        print(f"\n未匹配的课体 ({len(unmatched)}个):")
        for name in sorted(unmatched):
            print(f"  X {name}")
    else:
        print(f"\n[OK] 恭喜！所有 64 个课体都已匹配到课例！")


if __name__ == '__main__':
    batch_match_all_ke_li()
