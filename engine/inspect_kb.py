#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查看教师模型完整输出格式"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.distillation_engine import DistillationEngine

# 用已有的蒸馏结果，看看知识库存储了什么
engine = DistillationEngine()
kb = engine.knowledge_store

print("=== 知识库内容 ===")
print(f"规则: {len(kb.get('rules', []))}")
for r in kb.get('rules', [])[:10]:
    print(f"  - {r}")

print(f"\n占事模板: {len(kb.get('zhanshi_templates', {}))}")
for k, v in kb.get('zhanshi_templates', {}).items():
    print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")

print(f"\n推理链: {len(kb.get('reasoning_chains', []))}")
for chain in kb.get('reasoning_chains', [])[:2]:
    print(f"  ID: {chain.get('case_id')}")
    reasoning = chain.get('reasoning', '')
    print(f"  长度: {len(reasoning)} 字符")
    # Show just the final answer part
    if "[最终回答]" in reasoning:
        final = reasoning.split("[最终回答]")[1].strip()
        print(f"  最终回答: {final[:500]}")
    else:
        print(f"  开头: {reasoning[:300]}")
    print()