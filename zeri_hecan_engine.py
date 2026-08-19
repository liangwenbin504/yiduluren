# -*- coding: utf-8 -*-
"""择日合参引擎（2026-08-19）：择日专属条件合参规则——三层架构迁移到择日域。
L1 = 择日评分体系（斗首/仪度/禄马贵/演禽，不动）；L2 = 本引擎（全条件命中才触发，
警示/佐证层不参与评分）；L3 = data/zeri_hecan_rules.json 候选库（门槛：真实反馈
全中≥3 且一致率≥80% 才升 L2——当前反馈池仅 3 条，全部挂"候选-样本不足"）。
规则来源（每条标出处）：《仪度六壬择日要诀》场景吉凶课表（liuren_keti_duanyu）、
64 课格断语（daliuren_64ke_rules）、择日案例反馈（data/zeri_case_feedback.json）。"""
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))

_TYPE_MAP = {'提车': '出行', '搬家': '动土', '入宅': '动土', '开工': '动土', '上任': '上任',
             '赴任': '上任', '升迁': '上任', '开业': '开业', '开张': '开业', '交易': '开业',
             '安葬': '安葬', '下葬': '安葬', '立碑': '立碑', '出行': '出行', '远行': '出行',
             '考试': '考试', '婚嫁': '婚嫁', '结婚': '婚嫁', '动土': '动土', '催龙补气': '催龙补气'}

_KETI_KEYS = ('伏吟', '返吟', '八专', '官爵', '亨通', '元首', '龙德', '华盖乘轩', '富贵',
              '荣华', '遥克', '时泰', '合欢', '和美', '德庆')


def zeri_type_class(zetiri_type: str) -> str:
    """择日类型 → 要诀场景类（提车归出行、开张归开业等）。"""
    t = str(zetiri_type or '')
    for k, v in _TYPE_MAP.items():
        if k in t:
            return v
    return '其他'


def zeri_signals(keti: str, zetiri_type: str) -> dict:
    """择日合参信号：课体键 + 类型键（全部可计算）。"""
    sig = {}
    ks = str(keti or '')
    for k in _KETI_KEYS:
        sig['课体_' + k] = k in ks
    cls = zeri_type_class(zetiri_type)
    for k in ('出行', '动土', '安葬', '上任', '开业', '考试', '婚嫁', '立碑', '催龙补气', '其他'):
        sig['类型_' + k] = cls == k
    return sig


def load_zeri_rules(path: str = '') -> list:
    p = path or os.path.join(_ROOT, 'data', 'zeri_hecan_rules.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('rules', []) if isinstance(d, dict) else d
    except Exception:
        return []


def zeri_hecan_judge(sig: dict, rules: list = None) -> list:
    """择日合参判定：全条件命中才触发。返回触发规则（含结论/叙事/出处）。"""
    rs = rules if rules is not None else load_zeri_rules()
    out = []
    for r in rs:
        conds = r.get('条件', [])
        if not conds:
            continue
        hit = 0
        for c in conds:
            s = str(c.get('signal', ''))
            got = bool(sig.get(s, False))
            want = bool(c.get('value', True))
            ok = got == want
            if c.get('neg'):
                ok = not ok
            if ok:
                hit += 1
        if hit == len(conds):
            out.append({'id': r.get('id', ''), '结论': r.get('结论', ''),
                        '叙事': r.get('叙事', ''), '出处': r.get('出处', ''),
                        '置信度': r.get('置信度', 0)})
    return out


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    rs = load_zeri_rules()
    print('择日合参规则库:', len(rs), '条')
    sig = zeri_signals('伏吟课', '提车')
    print('提车+伏吟课 信号:', sig['课体_伏吟'], sig['类型_出行'])
    for o in zeri_hecan_judge(sig):
        print('触发:', o['id'], o['结论'], '|', o['叙事'][:44])
