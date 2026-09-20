#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬古案例知识库
=================
加载675个壬占汇选案例，为股票预测提供历史模式匹配。
"""

import json, os, sys, io
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).parent
CASE_FILE = BASE / "extracted_data" / "壬占汇选_训练数据_v2.json"
MEMORY = BASE / "_memory"
KB_FILE = MEMORY / "liuren_case_kb.json"

# ── 加载 ──
def load_cases():
    if not CASE_FILE.exists():
        print("  ⚠️ 案例文件不存在")
        return []
    with open(CASE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_knowledge_base(cases):
    """构建可搜索的知识库索引"""
    kb = {
        "total": len(cases),
        "by_ganzhi": defaultdict(list),
        "by_sanchuan": defaultdict(list),
        "by_yuejiang": defaultdict(list),
        "by_keti": defaultdict(list),
        "by_source": defaultdict(list),
        "stats": {},
    }

    for case in cases:
        gz = case.get('ganzhi', '')
        if gz:
            kb['by_ganzhi'][gz].append(case.get('question', '?'))

        sc = case.get('sanchuan', [])
        if sc:
            key = ' '.join(sc[:3])
            kb['by_sanchuan'][key].append(case)

        yj = case.get('yuejiang', '')
        if yj:
            kb['by_yuejiang'][yj].append(case)

        kt = case.get('keti', '')
        if kt:
            kb['by_keti'][kt].append(case)

        src = case.get('source', '未知')
        kb['by_source'][src].append(case)

    # 统计
    kb['stats'] = {
        'total_cases': len(cases),
        'with_sanchuan': sum(1 for c in cases if c.get('sanchuan')),
        'unique_ganzhi': len(kb['by_ganzhi']),
        'unique_sanchuan_combos': len(kb['by_sanchuan']),
        'unique_yuejiang': len(kb['by_yuejiang']),
        'unique_keti': len(kb['by_keti']),
        'source_distribution': {k: len(v) for k, v in kb['by_source'].items()},
    }

    # 转换为可序列化的dict
    kb['by_ganzhi'] = dict(kb['by_ganzhi'])
    kb['by_yuejiang'] = dict(kb['by_yuejiang'])
    kb['by_keti'] = {k: len(v) for k, v in kb['by_keti'].items()}

    # sanchuan只保留前100个最常见的
    sc_sorted = sorted(kb['by_sanchuan'].items(), key=lambda x: len(x[1]), reverse=True)
    kb['by_sanchuan'] = {k: len(v) for k, v in sc_sorted[:200]}

    return kb


def match_sanchuan(sanchuan, kb, top_k=5):
    """查找与给定三传最相似的历史案例"""
    sc_str = ' '.join(sanchuan[:3]) if isinstance(sanchuan, list) else str(sanchuan)
    matches = []

    # 精确匹配
    for sc_key in kb.get('by_sanchuan', {}):
        # 计算重叠度
        sc_parts = sc_key.split()
        query_parts = sc_str.split()
        overlap = len(set(sc_parts) & set(query_parts))
        if overlap > 0:
            matches.append((sc_key, overlap))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:top_k]


def match_ganzhi(ganzhi, kb):
    """查找同干支日的历史案例"""
    return kb.get('by_ganzhi', {}).get(ganzhi, [])


def generate_prediction_insight(prediction_data, kb):
    """基于古案例库生成预测洞察"""
    insights = []
    ganzhi = prediction_data.get('rizhu', '')[:2]
    sanchuan = prediction_data.get('sanchuan', [])

    # 1. 同干支日案例数
    gz_cases = match_ganzhi(ganzhi, kb)
    if gz_cases:
        insights.append(f"同干支日{ganzhi}共有{len(gz_cases)}个古案例可供参考")

    # 2. 相似三传
    sc_matches = match_sanchuan(sanchuan, kb)
    if sc_matches:
        top = sc_matches[0]
        insights.append(f"三传最相似组合'{top[0]}'在古籍中出现{top[1]}次")

    return insights


def main():
    print("=" * 55)
    print("  六壬古案例知识库")
    print("=" * 55)

    cases = load_cases()
    if not cases:
        return

    kb = build_knowledge_base(cases)

    # 保存知识库
    os.makedirs(MEMORY, exist_ok=True)
    with open(KB_FILE, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    print(f"\n  📊 知识库统计:")
    print(f"  总案例: {kb['stats']['total_cases']}")
    print(f"  有三传: {kb['stats']['with_sanchuan']}")
    print(f"  干支日: {kb['stats']['unique_ganzhi']}/60")
    print(f"  三传组合: {kb['stats']['unique_sanchuan_combos']} 种")

    print(f"\n  出处权威性:")
    for src, count in sorted(kb['stats']['source_distribution'].items(), 
                              key=lambda x: x[1], reverse=True):
        bar = '█' * (count // 10)
        print(f"    {src:<12} {count:>4} {bar}")

    print(f"\n  ✅ 知识库已保存: {KB_FILE}")
    return kb


if __name__ == '__main__':
    main()
