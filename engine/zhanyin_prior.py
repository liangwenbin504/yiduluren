# -*- coding: utf-8 -*-
"""占类条件先验谱（B 方案，2026-09-23；🔴 **零评分影响**，只给叙事层参考）

【是什么】
给定占类（章），输出「此占类下邵公常谈哪些事因」的排序谱。
数据源＝218 案疏正真值集（凶 172／吉 34／平 1），**严格口径：仅邵公断语**，
固化在 `data/zhanyin_prior.json`（由 `_冗余待删/_gen_zhanyin_prior.py` 生成）。

【v2 攒案口径（2026-09-23）】
  🔴 **建谱池＝有断语即入池（n=218），不做 label 过滤**——
     B 层的语义是「此占类下邵公常谈什么」＝频率谱，频率**不需要吉凶标签**；
     label 只用于算 lift 护栏。⛔ 未改动任何案的真值 label（不惊动 M3 口径）。
     收益：分章 7 → **12 章**（补回亡盗 14／六畜走失 9／胎产子息 7／出行访谒 7／
     行人音信 6／杂占 6），各章样本普涨（前程 55→60、宅墓 38→40、财产 8→12、官讼 9→11）。
  🔴 **lift 护栏一条不丢**：每行仍带 `lift＝凶占比÷吉占比`，`lift<1.15` 判「吉凶皆现（非凶兆）」。
     ⛔ 扩池**不等于**放宽判据——谱只说"常谈什么"，从不说"这是凶兆"。
  🔴 **三级回落**：细章 `zhanlei_code` → 粗占类 `zhanlei`（生产实际传的是粗占类）→ 总体谱。

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
_JSON_LIDAI = os.path.join(_ROOT, 'data', 'zhanyin_prior_lidai.json')
_CACHE: Dict[str, Any] = {}

def _load_lidai() -> Dict[str, Any]:
    """「历代层」谱（明清，n=129）——🔴 与邵公层**分层并存，不得混算**"""
    if 'lidai' in _CACHE:
        return _CACHE['lidai']
    try:
        with open(_JSON_LIDAI, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        d = {}
    _CACHE['lidai'] = d
    return d


# lift 阈值：< 1.15 视为「背景舞台」（吉凶皆现），1.15~1.8 中等，>= 1.8 显著
LIFT_STAGE = 1.15
LIFT_STRONG = 1.8
# 跨层对比：两层占比之比 < SAME_RATIO ⇒ 判「跨代一致」
SAME_RATIO = 1.6


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
        by_zl = d.get('分章粗') or {}
        rows: List[Dict[str, Any]] = []
        zl_key = str(zhanlei or '')
        sec_key = sec or ZHANLEI_TO_SEC.get(zl_key, '')
        # 🔴 三级回落：细章 → 粗占类（生产实际传的就是粗占类）→ 总体谱
        sd = None
        if sec_key and sec_key in by_sec:
            sd = by_sec[sec_key]
            out['章'] = sec_key
            src = '分章谱（%s，n=%d，凶%d／吉%d）' % (
                sec_key, sd.get('案数', 0), sd.get('凶案数', 0), sd.get('吉案数', 0))
        elif zl_key and zl_key in by_zl:
            sd = by_zl[zl_key]
            out['章'] = zl_key
            src = '粗占类谱（%s，n=%d，凶%d／吉%d）' % (
                zl_key, sd.get('案数', 0), sd.get('凶案数', 0), sd.get('吉案数', 0))
        if sd is not None:
            out['样本'] = sd.get('案数', 0)
            for r in sd.get('谱') or []:
                # 🔴 「是不是凶兆」只能由**总体谱的 lift** 定（吉案 34，样本够）。
                #    ⛔ 不能用章内 lift：分章吉案常只有 1~5 例（前程仕进仅 5 吉），
                #       某条在 5 例里 0 命中就被标成「仅见于凶案」⇒ 纯属小样本噪声。
                lf = (overall.get(r['事因']) or {}).get('lift')
                rows.append({'事因': r['事因'], '占比': r['占比'], '案数': r.get('案数', 0),
                             'lift': lf, '定性': _grade(lf, r['占比'])})
        else:
            # 🔴 案数 ≠ 各类命中数之和（一案可命中多类）：样本只能取**案数**本身
            tn = (d.get('_总体样本') or {})
            out['样本'] = tn.get('案数', 0)
            src = '总体谱（分章样本不足 n<5；粗占类「%s」／章「%s」；n=%d）' % (
                zl_key or '—', sec or '—', out['样本'])
            for k, v in sorted(overall.items(), key=lambda x: -x[1]['占比']):
                rows.append({'事因': k, '占比': v['占比'], '案数': v.get('案数', 0),
                             'lift': v.get('lift'), '定性': _grade(v.get('lift'), v['占比'])})
        rows.sort(key=lambda r: -r['占比'])
        out['谱'] = rows
        out['来源'] = src
        if rows:
            top = [r for r in rows[:4]]
            out['语'] = '此占类下邵公常谈之事因：' + '、'.join(
                '%s %d%%（%s）' % (r['事因'], round(r['占比']), r['定性']) for r in top)
        # ── 历代层（明清 n=129）：与邵公层**分层并存**，带跨层标记 ──
        out['历代'] = _prior_lidai(sec_key or ZHANLEI_TO_SEC.get(zl_key, '') or out['章'],
                                   overall)
        out['边界'] = ('先验谱＝「此占类常谈什么」的统计参考；lift<1.15 属背景舞台，'
                       '⛔ 不可作凶兆；纯叙事层，不进评分链。'
                       '「历代层」为明清壬家语料（与邵公层分层，不得混算）')
        return out
    except Exception as e:
        out['error'] = str(e)
        return out


def _prior_lidai(sec: str, overall_shao: Dict[str, Any]) -> Dict[str, Any]:
    """历代（明清）层谱：细章 → 总体；每条附「邵公占比」与跨层标记。

    🔴 语义＝「**历代**壬家常谈什么」，⛔ 不是「邵公常谈什么」。
    ⛔ 历代案无吉凶真值 ⇒ **没有 lift**，⛔ 不得判凶兆。
    """
    out: Dict[str, Any] = {'章': sec or '', '样本': 0, '谱': [], '来源': '', '语': ''}
    try:
        d = _load_lidai()
        if not d:
            return out
        by_sec = d.get('分章') or {}
        if sec and sec in by_sec:
            sd = by_sec[sec]
            out['样本'] = sd.get('案数', 0)
            out['章'] = sec
            out['来源'] = '历代分章谱（%s，n=%d）' % (sec, out['样本'])
            raw = sd.get('谱') or []
        else:
            raw = d.get('总体') or []
            out['样本'] = (d.get('_口径') or {}).get('案数', 0)
            out['来源'] = '历代总体谱（章「%s」样本不足，n=%d）' % (sec or '—', out['样本'])
        rows: List[Dict[str, Any]] = []
        for r in raw:
            sg = float((overall_shao.get(r['事因']) or {}).get('占比', 0.0) or 0.0)
            ld = float(r.get('占比', 0.0) or 0.0)
            if sg <= 0 and ld <= 0:
                tag = ''
            elif sg <= 0:
                tag = '历代特色'
            elif ld <= 0:
                tag = '邵公特色'
            elif max(sg, ld) / max(0.1, min(sg, ld)) < SAME_RATIO:
                tag = '跨代一致'
            elif sg > ld:
                tag = '邵公特色'
            else:
                tag = '历代特色'
            rows.append({'事因': r['事因'], '占比': ld, '案数': r.get('案数', 0),
                         '邵公占比': round(sg, 1), '标记': tag})
        rows.sort(key=lambda r: -r['占比'])
        out['谱'] = rows
        if rows:
            out['语'] = '历代（明清）此占类常谈：' + '、'.join(
                '%s %d%%' % (r['事因'], round(r['占比'])) for r in rows[:4])
        return out
    except Exception as e:
        out['error'] = str(e)
        return out
