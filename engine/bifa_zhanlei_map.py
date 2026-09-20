# -*- coding: utf-8 -*-
"""
毕法赋占类过滤（2026-08-17 憨爷拍板：毕法赋做精细版）。

设计原则：
- **评估层零破坏**：本模块只做展示层过滤；古例 M3 评估的 bifa hits 不变。
- **标签来源**：data/bifa_100_knowledge_base.json 的 category（60 类）+ application（适用描述）。
- **统一占类**（与古例 zhanlei 对齐）：
    功名 / 其他 / 家宅 / 婚姻 / 胎产 / 求财 / 出行 / 疾病 / 官讼
- **通用规则**：zhanlei 为空（不限占类）——方法论/六亲/空亡/贵人/三传生克/阴阳格局等全局断语。
- **过滤规则**：rule 命中后，若其 zhanlei 非空且不含当前占类 → 展示层过滤掉（评估层保留）。
"""
from typing import Dict, List, Set

# ── category → 统一占类（专属；未列出的 category 视为通用=不限占类） ──
CATEGORY_ZHANLEI: Dict[str, Set[str]] = {
    # 功名
    '官职升迁': {'功名'},
    '官职差遣': {'功名'},
    '科举考试': {'功名'},
    # 婚姻
    '婚姻': {'婚姻'},
    # 家宅
    '家宅': {'家宅'},
    '家宅人口': {'家宅'},
    # 疾病 / 官讼（病讼=病+讼两用）
    '疾病': {'疾病'},
    '病证': {'疾病'},
    '病讼': {'疾病', '官讼'},
    '官讼': {'官讼'},
    # 求财
    '求财': {'求财'},
    '财动': {'求财'},
    '求财警示': {'求财'},
    # 出行
    '出行求财': {'出行', '求财'},
    # 胎产
    '胎孕': {'胎产'},
    # 其他（捕盗/防骗 等无专属占类的专项）
    '捕盗': {'其他'},
    '防骗': {'其他'},
    # 丧服：主孝服家宅之凶
    '丧服': {'家宅'},
}

# ── application 关键词 → 占类（category 通用时，按 application 补充限定） ──
# 精确词为主，避免误伤（'行'→'不行传者'、'官'→'官人'、'远'→'远动'、'失'→'得失' 等）
APP_KEYWORDS = [
    ('科举', '功名'), ('仕宦', '功名'), ('升迁', '功名'), ('官职', '功名'), ('甲第', '功名'),
    ('讼', '官讼'), ('狱', '官讼'),
    ('病', '疾病'), ('疾', '疾病'), ('医', '疾病'),
    ('财', '求财'), ('商贩', '求财'), ('贾', '求财'), ('投资', '求财'),
    ('出行', '出行'), ('远行', '出行'), ('访人', '出行'), ('商贩', '出行'),
    ('婚', '婚姻'), ('嫁', '婚姻'), ('娶', '婚姻'), ('夫妇', '婚姻'), ('芜淫', '婚姻'),
    ('胎', '胎产'), ('孕', '胎产'), ('产', '胎产'),
    ('宅', '家宅'), ('人宅', '家宅'), ('屋', '家宅'),
    ('捕', '其他'), ('盗', '其他'), ('贼', '其他'), ('失脱', '其他'), ('失物', '其他'),
]

ZHANLEI_ALL: Set[str] = {'功名', '其他', '家宅', '婚姻', '胎产', '求财', '出行', '疾病', '官讼'}


def get_bifa_zhanlei(rule: Dict) -> Set[str]:
    """单条规则 → 适用占类集合（空集合 = 通用不限占类）。"""
    cat = (rule.get('category') or '').strip()
    if cat in CATEGORY_ZHANLEI:
        return set(CATEGORY_ZHANLEI[cat])

    # category 通用 → 按 application 关键词补充限定（有明确占类词才限定，否则通用）
    app = str(rule.get('application') or '')
    hits: Set[str] = set()
    for kw, zl in APP_KEYWORDS:
        if kw in app:
            hits.add(zl)
    return hits


def filter_bifa_by_zhanlei(detected_rules: List[Dict], zhanlei: str) -> List[Dict]:
    """展示层过滤：保留「通用(空) 或 含当前占类」的命中。评估层不用本函数。"""
    if not detected_rules:
        return []
    zl = (zhanlei or '其他').strip()
    kept = []
    for r in detected_rules:
        rzl = get_bifa_zhanlei(r)
        if not rzl or zl in rzl:
            kept.append(r)
    return kept


def attach_zhanlei_info(rule: Dict) -> Dict:
    """为单条规则附加 'zhanlei' 说明（用于展示/审计，不改原字段）。"""
    out = dict(rule)
    out['zhanlei'] = sorted(get_bifa_zhanlei(rule))
    return out


if __name__ == '__main__':
    # 审计：输出全部 100 条的占类标签
    import json, os
    _p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'data', 'bifa_100_knowledge_base.json')
    kb = json.load(open(_p, encoding='utf-8'))
    n_limited = 0
    for r in kb['rules']:
        zl = get_bifa_zhanlei(r)
        if zl:
            n_limited += 1
        print(f"{r['id']:>3} {r.get('name','')[:20]:<22} -> {sorted(zl)}")
    print(f"\n限定 {n_limited}/100 条，通用 {100-n_limited}/100 条")
