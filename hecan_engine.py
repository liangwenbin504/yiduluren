# -*- coding: utf-8 -*-
"""多条件合参引擎（2026-08-18）

方法论：叶飘然课例回测教训——正议结论均为"多条件合参"（如"幕贵+当旺+生日+占谋望"
四条件齐备才断必成），单抽条件必然过拟合误伤。

架构三层：
  L1 硬规则层（liuchen_engine 现有）：单/双条件规则，已过 632 全库验证——保持不动；
  L2 合参规则层（本引擎）：断语原文的"条件集合→结论"，**必须全条件命中才触发**，
     输出置信度与出处，接入叙事层（不参与评分，零回退风险）；
  L3 规则候选库（data/hecan_rules.json）：正议体提取的候选规则+验证状态，
     全中方向一致率达标（≥80% 且样本≥3）才升入 L2。

推广价值：任何古断语（邵公/陈公献/王牧夫/叶飘然/祝泌…）都可按
"断语→条件集合→结论"结构化入库，逐步把"象法活断"沉淀为"可验证合参"。
"""
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_rules(path: str = '') -> list:
    p = path or os.path.join(_ROOT, 'data', 'hecan_rules.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('rules', []) if isinstance(d, dict) else d
    except Exception:
        return []


def check_signals(sig: dict, pan_signals: dict) -> bool:
    """单信号判定。pan_signals 由课程信号提取函数构造。"""
    s = str(sig.get('signal', ''))
    val = sig.get('value', True)
    neg = bool(sig.get('neg', False))
    got = pan_signals.get(s, False)
    hit = bool(got) == bool(val)
    return (not hit) if neg else hit


def hecan_judge(pan_signals: dict, rules: list = None) -> list:
    """合参判定：逐条规则算条件命中数，全中才触发。返回触发规则列表（含置信度）。"""
    rs = rules if rules is not None else load_rules()
    out = []
    for r in rs:
        conds = r.get('条件', [])
        if not conds:
            continue
        hit = sum(1 for c in conds if check_signals(c, pan_signals))
        if hit == len(conds):
            out.append({
                'id': r.get('id', ''), '结论': r.get('结论', ''),
                '置信度': round(r.get('置信度', 1.0) * hit / len(conds), 2),
                '出处': r.get('出处', ''), '叙事': r.get('叙事', ''),
            })
    return out


if __name__ == '__main__':
    rs = load_rules()
    print(f'合参规则库: {len(rs)} 条')
    # 自检：构造 §070 信号
    sig = {'干上_是贵人': True, '干上_空亡': True, '干上_生日干': True}
    out = hecan_judge(sig, rs)
    for o in out:
        print('触发:', o['id'], o['结论'], '|', o['叙事'][:40])
