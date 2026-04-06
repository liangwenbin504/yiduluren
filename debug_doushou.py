#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""详细分析斗首评分逻辑"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer
from sizhu_engine import get_sizhu
from datetime import datetime, timedelta

doushou = DouhouKegeAnalyzer()

print("=" * 70)
print("详细分析斗首评分逻辑 - 壬山")
print("=" * 70)

# 测试未来10天
today = datetime.now()
score_distribution = {}
low_score_examples = []

for day_offset in range(10):
    date = today + timedelta(days=day_offset)
    year, month, day = date.year, date.month, date.day
    
    for shichen in ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']:
        try:
            sizhu = get_sizhu(year, month, day, shichen)
            if not sizhu:
                continue
            
            result = doushou.analyze_kege('壬', sizhu)
            score = result.get('综合评分', 0)
            
            # 统计分数分布
            score_range = f"{(score//10)*10}-{(score//10)*10+9}"
            score_distribution[score_range] = score_distribution.get(score_range, 0) + 1
            
            # 收集低分案例
            if score < 50 and len(low_score_examples) < 3:
                low_score_examples.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'shichen': shichen,
                    'sizhu': sizhu,
                    'score': score,
                    'patterns': result.get('课格格局', []),
                    'star_counts': result.get('六相六替分析', {}).get('六相统计', {}),
                    '四柱分析': result.get('四柱分析', {})
                })
                
        except Exception as e:
            print(f"错误: {e}")

print("\n【分数分布】")
for range_name in sorted(score_distribution.keys()):
    count = score_distribution[range_name]
    bar = '█' * (count // 2)
    print(f"  {range_name}分: {count:3d} {bar}")

print(f"\n【低分案例分析】")
for i, example in enumerate(low_score_examples, 1):
    print(f"\n案例{i}: {example['date']} {example['shichen']}时 (评分: {example['score']})")
    print(f"  四柱: {example['sizhu'].get('年柱')} {example['sizhu'].get('月柱')} {example['sizhu'].get('日柱')} {example['sizhu'].get('时柱')}")
    print(f"  六相统计: {example['star_counts']}")
    print(f"  四柱分析:")
    for pillar, info in example['四柱分析'].items():
        print(f"    {pillar}: {info.get('干支')} 化气={info.get('化气五行')} 星曜={info.get('斗首星曜')}")
    print(f"  格局: {example['patterns']}")

# 验证壬山五行
print("\n" + "=" * 70)
print("验证壬山斗首五行")
print("=" * 70)
print(f"壬山斗首五行: {doushou.get_shan_jia_wuxing('壬')}")
print(f"天干化气表:")
for gan in ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']:
    huaqi = doushou.get_tiangan_huaqi(gan)
    liuqin = doushou.get_liuqin('土', huaqi)  # 壬山属土
    print(f"  {gan} -> 化{huaqi} -> {liuqin}")

print("\n" + "=" * 70)
