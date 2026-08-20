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


def zeri_signals(keti: str, zetiri_type: str, sizhu: dict = None, shan_wx: str = '') -> dict:
    """择日合参信号：课体键 + 类型键（全部可计算）。"""
    sig = {}
    ks = str(keti or '')
    for k in _KETI_KEYS:
        sig['课体_' + k] = k in ks
    cls = zeri_type_class(zetiri_type)
    for k in ('出行', '动土', '安葬', '上任', '开业', '考试', '婚嫁', '立碑', '催龙补气', '其他'):
        sig['类型_' + k] = cls == k
    # 斗首四柱星曜信号（2026-08-20 注解2实战案例：四廉/破鬼把门/三武一元等，需 sizhu+山家五行）
    for k in ('斗首_四柱全廉', '斗首_年柱破鬼', '斗首_月柱武财', '斗首_日时柱元辰武财',
              '斗首_一破鬼两支生旺', '斗首_两破鬼一支生旺', '斗首_三武一元', '斗首_廉子一位无贪官',
              '斗首_双廉休囚元辰弱', '日支_冲山', '日支_冲月建'):
        sig[k] = False
    try:
        _sizhu = sizhu or {}
        _shan_wx = shan_wx or ''
        _STAR = {
            ('土', '土'): '元辰', ('土', '金'): '廉贞', ('土', '水'): '武财', ('土', '木'): '破鬼', ('土', '火'): '贪官',
            ('金', '金'): '元辰', ('金', '水'): '廉贞', ('金', '木'): '武财', ('金', '火'): '破鬼', ('金', '土'): '贪官',
            ('水', '水'): '元辰', ('水', '木'): '廉贞', ('水', '火'): '武财', ('水', '土'): '破鬼', ('水', '金'): '贪官',
            ('木', '木'): '元辰', ('木', '火'): '廉贞', ('木', '土'): '武财', ('木', '金'): '破鬼', ('木', '水'): '贪官',
            ('火', '火'): '元辰', ('火', '土'): '廉贞', ('火', '金'): '武财', ('火', '水'): '破鬼', ('火', '木'): '贪官'}
        _HUQI = {'甲': '土', '己': '土', '乙': '金', '庚': '金', '丙': '水', '辛': '水',
                 '丁': '木', '壬': '木', '戊': '火', '癸': '火'}
        _stars = []
        for _col, _alt in (('年', '年柱'), ('月', '月柱'), ('日', '日柱'), ('时', '时柱')):
            _gz = str(_sizhu.get(_col, _sizhu.get(_alt, '')))
            if len(_gz) >= 2:
                _stars.append(_STAR.get((_shan_wx, _HUQI.get(_gz[0], '')), ''))
        _stars = [s for s in _stars if s]
        sig['斗首_四柱全廉'] = len(_stars) == 4 and all(s == '廉贞' for s in _stars)
        sig['斗首_年柱破鬼'] = bool(_stars) and _stars[0] == '破鬼'
        sig['斗首_月柱武财'] = len(_stars) > 1 and _stars[1] == '武财'
        sig['斗首_日时柱元辰武财'] = len(_stars) > 2 and _stars[2] in ('元辰', '武财') and _stars[3] in ('元辰', '武财')
        n_po = _stars.count('破鬼')
        n_sheng = sum(1 for _g in _stars if _g in ('武财', '元辰'))
        sig['斗首_一破鬼两支生旺'] = n_po == 1 and n_sheng >= 2
        sig['斗首_两破鬼一支生旺'] = n_po >= 2 and n_sheng >= 1
        sig['斗首_三武一元'] = _stars.count('武财') >= 3 and _stars.count('元辰') >= 1
        sig['斗首_廉子一位无贪官'] = _stars.count('廉贞') == 1 and _stars.count('贪官') == 0
        sig['斗首_双廉休囚元辰弱'] = _stars.count('廉贞') >= 2 and _stars.count('元辰') <= 1
    except Exception:
        pass
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
