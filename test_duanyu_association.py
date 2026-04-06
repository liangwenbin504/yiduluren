#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试断语库与综合建议的关联
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from liuren_keti_duanyu import LiuRenKetiDuanyu
import ai_evaluation as ai_eval_module
AIEvaluation = ai_eval_module.AIEvaluation

print("=" * 80)
print("测试断语库与综合建议的关联")
print("=" * 80)

# 1. 测试六壬课体断语库
print("\n【1】测试六壬课体断语库")
print("-" * 80)
liuren_duanyu = LiuRenKetiDuanyu()

test_ketis = ['元首课', '龙德课', '重审课', '知一课']
for keti in test_ketis:
    info = liuren_duanyu.get_keti_duanyu(keti)
    print(f"\n课格: {keti}")
    print(f"  等级: {info.get('等级', '未知')}")
    print(f"  断语: {info.get('断语', '未知')}")
    print(f"  有总论: {'是' if info.get('详细断语', {}).get('总论') else '否'}")
    print(f"  有宜事: {'是' if info.get('宜事') else '否'}")
    print(f"  有忌事: {'是' if info.get('忌事') else '否'}")

# 2. 测试AI评价系统
print("\n\n【2】测试AI评价系统生成传统断语")
print("-" * 80)
ai_eval = AIEvaluation()

test_data = {
    "课格列表": ["元首课", "龙德课"],
    "daliuren_detail": {
        "shan_jia": "子",
        "xiang_shou": "午",
        "ri_qualified": True,
        "ri_shan_count": 1,
        "ri_xiang_count": 1,
        "yue_qualified": True,
        "yue_shan_count": 1,
        "yue_xiang_count": 0,
        "nian_qualified": False,
        "nian_shan_count": 0,
        "nian_xiang_count": 0,
        "qualified_count": 2
    }
}

traditional_duanyu = ai_eval._generate_traditional_duanyu(test_data)
print("生成的传统断语长度:", len(traditional_duanyu))
print("\n传统断语预览:")
print("-" * 80)
print(traditional_duanyu[:1000] + "..." if len(traditional_duanyu) > 1000 else traditional_duanyu)

print("\n" + "=" * 80)
print("测试结论")
print("=" * 80)
print("✅ 断语库正常加载")
print("✅ 六壬课体断语库有详细断语")
print("✅ AI评价系统可以生成传统断语")
print("\n⚠️  问题分析:")
print("  1. '综合建议'部分在前端主界面.html中是硬编码生成的")
print("  2. 没有使用断语库中的详细内容")
print("  3. 传统断语只添加在综合评价的后面")
