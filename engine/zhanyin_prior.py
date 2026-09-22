# -*- coding: utf-8 -*-
"""占类条件先验谱（B 方案，2026-09-23；🔴 **零评分影响**，只给叙事层参考）

【是什么】
给定占类（章），输出「此占类下邵公常谈哪些事因」的排序谱。
数据源＝218 案疏正真值集（凶 172／吉 34），**严格口径：仅邵公断语**，
固化在 `data/zhanyin_prior.json`（由 `_冗余待删/_gen_zhanyin_prior.py` 生成）。

【⛔ 是什么 ≠ 判据】
  · lift ≈ 1 者 ⇒ **吉案也照样出现** ⇒ 属"背景舞台"，**不可用作凶兆**
    （教训见 2026-09-22 第二十一节：德亏 lift 0.40 反向、祖坟 0.99 零判别力）
  · 本层只说"此占类下常谈什么"，**不判吉凶、不进评分链、不给结论**
  · 分章样本小的（官讼 9、财产 8、出行 5）只作**弱参考**，已标 `样本` 字段

【为何不直接用总体谱】
  总谱最高是「六亲家人」lift 4.68，但那是跨占类平均；
  **分章才有指向性**：官讼章「官非对头」67%、疾病章「医药」35% 均居首 ⇒ 谱有信息量。
"""
import json
import os
from typing import Any, Dict, List

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JSON = os.path.join(_ROOT, 'data', 'zhanyin_prior.json')
_CACHE: Dict[str, Any] = {}

# lift 阈值：< 1.15 视为「背景舞台」（吉凶皆现），1.15~1.8 中等，>= 1.8 显著
LIFT_STAGE = 1.15
LIFT_STRONG = 1.8


def _load() -> Dict[str, Any]:
    if 'data' in _CACHE:
        return _CACHE['data']
    try:
        with open(_JSON, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        d = {}
    _CACHE['data'] = d
    return d


# 🔴 生产只有**粗占类** `zhanlei`（功名/家宅/疾病/…），而分章谱按 **细章**（前程仕进/宅墓/…）
#    建表。二者在 218 案里除「其他」外基本 1:1（字数校验：功名60=前程仕进60、家宅40=宅墓40、
#    疾病17=疾病17、官讼11=官讼11、胎产7=胎产子息7、婚姻3=婚姻3）⇒ 直接映射。
#    「其他」是混合章（终身/亡盗/六畜/行人/杂占/天时…）⇒ **不映射**，回落总体谱。
ZHANLEI_TO_SEC = {
    '功名': '前程仕进', '家宅': '宅墓', '疾病': '疾病', '官讼': '官讼',
    '胎产': '胎产子息', '求财': '财产', '出行': '出行访谒', '婚姻': '婚姻',
}


def _grade(lift, ratio):
    """给一条事因定性（⛔ 定性只用于展示措辞，不构成判断）"""
    if lift is None:                       # 吉案 0 命中
        return '仅见于凶案'
    if lift < 0.8:
        return '吉凶皆现（非凶兆）'
    if lift < LIFT_STAGE:
        return '弱'
    if lift < LIFT_STRONG:
        return '中等'
    return '显著'


def prior_for(sec: str = '', zhanlei: str = '') -> Dict[str, Any]:
    """按 章(zhanlei_code) 取谱；章缺失或样本<5 则回落到总体谱。

    返回 {占类, 章, 样本, 谱[], 语, 边界}
    """
    out: Dict[str, Any] = {'章': sec or '', '占类': zhanlei or '', '样本': 0,
                           '谱': [], '语': '', '来源': '', '边界': ''}
    try:
        d = _load()
        if not d:
            out['边界'] = '先验谱数据不可用'
            return out
        overall = d.get('总体') or {}
        by_sec = d.get('分章') or {}
        rows: List[Dict[str, Any]] = []
        src = ''
        sec_key = sec or ZHANLEI_TO_SEC.get(str(zhanlei or ''), '')
        if sec_key and sec_key in by_sec:
            sd = by_sec[sec_key]
            out['样本'] = sd.get('凶案数', 0)
            out['章'] = sec_key
            src = '分章谱（%s，凶案 n=%d）' % (sec_key, out['样本'])
            for r in sd.get('谱') or []:
                ov = overall.get(r['事因'], {})
                rows.append({'事因': r['事因'], '占比': r['占比'],
                             '案数': r.get('案数', 0),
                             'lift': ov.get('lift'), '定性': _grade(ov.get('lift'), r['占比'])})
        else:
            # 🔴 案数 ≠ 各类命中数之和（一案可命中多类）：总体样本只能取**案数**本身
            tn = (d.get('_总体样本') or {})
            out['样本'] = tn.get('凶案数', 0)
            src = '总体谱（分章样本不足 n<5，粗占类「%s」／章「%s」；凶案 n=%d）' % (
                zhanlei or '—', sec or '—', out['样本'])
            for k, v in sorted(overall.items(), key=lambda x: -x[1]['凶占比']):
                if v['凶占比'] <= 0:
                    continue
                rows.append({'事因': k, '占比': v['凶占比'], '案数': v.get('凶案数', 0),
                             'lift': v.get('lift'), '定性': _grade(v.get('lift'), v['凶占比'])})
        rows.sort(key=lambda r: -r['占比'])
        out['谱'] = rows
        out['来源'] = src
        if rows:
            top = [r for r in rows[:4]]
            out['语'] = '此占类下邵公常谈之事因：' + '、'.join(
                '%s %d%%（%s）' % (r['事因'], round(r['占比']), r['定性']) for r in top)
        out['边界'] = ('先验谱＝「此占类常谈什么」的统计参考；lift<1.15 属背景舞台，'
                       '⛔ 不可作凶兆；纯叙事层，不进评分链')
        return out
    except Exception as e:
        out['error'] = str(e)
        return out
