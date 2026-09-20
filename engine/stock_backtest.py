# -*- coding: utf-8 -*-
"""
股例严格回测 · 支柱①②③④ 消融评估
====================================================================
数据集: data/stock_training_clean.json (21 条指数级案例, actual∈{涨,跌} 干净标签)
配置:   固定占时 = 午 (与项目 2026-07-30 参考文件一致, 合理市场占时)
方法:
  M1 原20d引擎 prediction.trend
  M2 融合层(门控+D-S, 支柱①②③, 不含CBR)
  M3 融合层 + CBR叙事证据组 (支柱①②③④, 当前部署)
  M4 CBR叙事单独 (holistic_judgment.trend)
指标: 方向准确率(仅决定性调用, 排除震荡弃权) + Brier(可用概率处)
对标: 多数类基线 + 数据内已有 LLM 基线(稀疏)
"""
from __future__ import annotations
import json, os, copy, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from liuren_20d_engine import get_liuren_20d_signal
from engine.judgment_fusion import fuse

SHICHEN = '午'
DATA = os.path.join('data', 'stock_training_clean.json')
OUT = os.path.join('engine', 'stock_backtest_report.json')

def norm_label(trend: str):
    """涨类→+1, 跌类→-1, 震荡/平/其他→0(弃权)."""
    if not trend:
        return 0
    t = trend.replace('看', '').strip()
    if t in ('涨',):
        return 1
    if t in ('跌',):
        return -1
    return 0  # 震荡/平

def brier(prob: dict, actual_label: int) -> float:
    """prob: {涨,平,跌} 概率; actual_label ∈ {+1,-1}."""
    p_up = prob.get('涨', prob.get('prob_up', 0)) or 0
    p_flat = prob.get('平', prob.get('prob_flat', 0)) or 0
    p_down = prob.get('跌', prob.get('prob_down', 0)) or 0
    o_up = 1.0 if actual_label == 1 else 0.0
    o_down = 1.0 if actual_label == -1 else 0.0
    o_flat = 0.0
    return (p_up - o_up) ** 2 + (p_flat - o_flat) ** 2 + (p_down - o_down) ** 2

def main():
    cases = json.load(open(DATA, encoding='utf-8'))
    rows = []
    agg = {
        'M1_pred': {'n': 0, 'hit': 0, 'call': 0},
        'M2_fused_no_cbr': {'n': 0, 'hit': 0, 'call': 0, 'brier': 0.0, 'brier_n': 0},
        'M3_integrated': {'n': 0, 'hit': 0, 'call': 0, 'brier': 0.0, 'brier_n': 0},
        'M4_holistic': {'n': 0, 'hit': 0, 'call': 0},
    }
    fails = 0
    for c in cases:
        dt = c.get('date')
        actual = c.get('actual')
        if actual not in ('涨', '跌'):
            continue
        actual_label = 1 if actual == '涨' else -1
        try:
            r = get_liuren_20d_signal(dt, SHICHEN)
        except Exception as e:
            fails += 1
            rows.append({'date': dt, 'actual': actual, 'error': str(e)[:60]})
            continue
        pred_trend = (r.get('prediction') or {}).get('trend', '')
        hj = r.get('holistic_judgment') or {}
        h_trend = hj.get('trend', '') if isinstance(hj, dict) and 'error' not in hj else ''
        fj_int = r.get('fused_judgment') or {}  # M3 (含CBR)
        # M2: 去掉 holistic 后重算融合
        r2 = copy.deepcopy(r)
        r2.pop('holistic_judgment', None)
        try:
            fj_no = fuse(r2)
        except Exception:
            fj_no = {}

        labs = {
            'M1_pred': norm_label(pred_trend),
            'M2_fused_no_cbr': norm_label(fj_no.get('trend', '')),
            'M3_integrated': norm_label(fj_int.get('trend', '')),
            'M4_holistic': norm_label(h_trend),
        }
        row = {'date': dt, 'actual': actual, 'actual_label': actual_label,
               'M1_pred': pred_trend, 'M2_fused_no_cbr': fj_no.get('trend', ''),
               'M3_integrated': fj_int.get('trend', ''), 'M4_holistic': h_trend}
        # 累加
        for m, lab in labs.items():
            a = agg[m]
            a['n'] += 1
            if lab != 0:
                a['call'] += 1
                if lab == actual_label:
                    a['hit'] += 1
        # Brier (仅决定性)
        if labs['M2_fused_no_cbr'] != 0:
            agg['M2_fused_no_cbr']['brier'] += brier(fj_no, actual_label)
            agg['M2_fused_no_cbr']['brier_n'] += 1
        if labs['M3_integrated'] != 0:
            agg['M3_integrated']['brier'] += brier(fj_int, actual_label)
            agg['M3_integrated']['brier_n'] += 1
        # 概率快照
        if labs['M3_integrated'] != 0:
            row['M3_p'] = {k: round(fj_int.get(k, 0), 3) for k in ('prob_up', 'prob_flat', 'prob_down')}
        rows.append(row)

    # 汇总
    summary = {'shichen': SHICHEN, 'total_cases': len(cases), 'runnable': len(rows) - fails, 'fails': fails}
    for m, a in agg.items():
        call = a['call']; hit = a['hit']
        summary[m] = {
            'n': a['n'], 'calls': call, 'hits': hit,
            'acc_call': round(hit / call, 3) if call else None,
            'acc_all': round(hit / a['n'], 3) if a['n'] else None,
            'brier': round(a['brier'] / a['brier_n'], 3) if a.get('brier_n') else None,
        }
    # 多数类基线
    n_up = sum(1 for c in cases if c.get('actual') == '涨')
    n_dn = sum(1 for c in cases if c.get('actual') == '跌')
    majority = '跌' if n_dn >= n_up else '涨'
    summary['majority_baseline'] = {'label': majority, 'acc': round(max(n_up, n_dn) / (n_up + n_dn), 3)}

    # CBR 贡献: M2(无CBR) → M3(有CBR) 改变了多少调用? 多少由错/弃权变对?
    flip_to_right = flip_to_wrong = same_right = same_wrong = abstain_to_call = 0
    for row in rows:
        if 'error' in row:
            continue
        l2 = norm_label(row['M2_fused_no_cbr']); l3 = norm_label(row['M3_integrated'])
        al = row['actual_label']
        if l2 == 0 and l3 != 0:
            abstain_to_call += 1
        if l2 != 0 and l3 != 0:
            if l2 == al and l3 == al: same_right += 1
            elif l2 != al and l3 == al: flip_to_right += 1
            elif l2 == al and l3 != al: flip_to_wrong += 1
            else: same_wrong += 1
    summary['cbr_effect'] = {'abstain_to_call': abstain_to_call, 'wrong_to_right': flip_to_right,
                             'right_to_wrong': flip_to_wrong, 'both_right': same_right, 'both_wrong': same_wrong}

    # holistic 单独一致率(建议的 综合叙事 可靠度乘子依据)
    h_agree = sum(1 for row in rows if 'error' not in row and norm_label(row['M4_holistic']) != 0
                  and norm_label(row['M4_holistic']) == row['actual_label'])
    h_call = sum(1 for row in rows if 'error' not in row and norm_label(row['M4_holistic']) != 0)
    summary['holistic_agreement'] = {'calls': h_call, 'agree': h_agree,
                                     'rate': round(h_agree / h_call, 3) if h_call else None,
                                     'suggested_mult': round(max(0.3, min(1.8, (h_agree + 1) / (h_call + 2) / 0.5)), 3) if h_call else None}

    report = {'summary': summary, 'per_case': rows}
    json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    # 控制台
    print(f"股例回测 ({SHICHEN} 时) · 可运行 {summary['runnable']}/{summary['total_cases']} 例, 失败 {fails}")
    print(f"{'方法':18s} {'调用':>4s} {'命中':>4s} {'准确率(调用)':>12s} {'Brier':>7s}")
    for m in ['M1_pred', 'M2_fused_no_cbr', 'M3_integrated', 'M4_holistic']:
        s = summary[m]
        b = s.get('brier'); b = f"{b:.3f}" if b is not None else "  -  "
        acc = s.get('acc_call'); acc = f"{acc*100:.1f}%" if acc is not None else "  -  "
        print(f"{m:18s} {s['calls']:>4d} {s['hits']:>4d} {acc:>12s} {b:>7s}")
    mb = summary['majority_baseline']
    print(f"多数类基线({mb['label']}): {mb['acc']*100:.1f}%")
    print(f"\nCBR 贡献(M2→M3): 弃权→决断 {abstain_to_call} | 错→对 {flip_to_right} | 对→错 {flip_to_wrong} | 双对 {same_right} | 双错 {same_wrong}")
    ha = summary['holistic_agreement']
    print(f"CBR单独一致率: {ha['agree']}/{ha['calls']} = {ha['rate']} → 建议 综合叙事 乘子 ≈ {ha['suggested_mult']}")
    print(f"\n报告已写: {OUT}")

if __name__ == '__main__':
    main()
