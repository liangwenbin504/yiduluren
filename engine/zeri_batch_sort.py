# -*- coding: utf-8 -*-
"""批量择日排序梯次：把「择日类型类神吉应」纳入排序（2026-09-12 憨爷「按你的建议」拍板）。

【实证·根因】批量候选 `total_score` **99.5%（201/202）恒为 100**
  —— 权威骨架 `luma_base` 起手 ≥60（`daliuren_luma_guiren` 夹 60–100）＋加分项叠加后必饱和，
  两处 `min(100, ...)`（`yidu_liuren_yaojue.analyze_yidu_full` ＋ `stock_dashboard._ttl`）→ 分数信息被抹平。
  而生产 `/api/zeri/batch` 排序键
  （`_lmg_key → _weighted_score → _LX_PRI → bonus_score → liuren_score → total_score`）
  **完全不含类神吉应** → `zeri_type` 参数实质失效：
  按 rank 排序 TOP20 中 类神=凶 **11/20**（凶应夺魁）；类神=凶 组 rank 均值 63.36 **反高于** 类神=吉 63.08。

【根本解】把 `leishen_detail.end`（吉>平>凶）作为**排序梯次**，插在
  「禄马贵人条件（首键 `_lmg_key`／`_lmg_priority_key`）」之后、斗首六壬加权分（`_weighted_score`）**之前**。
  ⚠️ 位置经模拟验证：置第 2 位 → TOP20 = 吉 **20/20** ✓；置 `_weighted_score` **之后** → 无效（仍 11 凶）。
  理由自洽：禄马贵人＝首键（不改）→ 类神吉应＝**六壬主旨对本用事类型的落实** → 斗首/六壬加权分…

【回退】env `ZERI_TYPE_TIER=0` → 返回恒 0，逐位回退旧口径（零回归）。
【中性】未选 zeri_type（`leishen_detail` 为空）→ 梯次恒 1，等同旧口径。
"""
import os

ZERI_TYPE_TIER = os.environ.get('ZERI_TYPE_TIER', '1') == '1'
_END_TIER = {'吉': 2, '平': 1, '凶': 0}


def tier_from_detail(detail):
    """由 `leishen_detail` 字典取梯次（唯一真源，供生产与引擎侧共用）：吉 2 > 平 1 > 凶 0；未知 → 1（中性）。"""
    return _END_TIER.get(((detail or {}).get('end') or ''), 1)


def leishen_end_tier(cand):
    """类神吉应梯次（越大越好）：吉 2 > 平 1 > 凶 0；未知 / 未选类型 → 1（中性）。"""
    return tier_from_detail((cand or {}).get('leishen_detail'))


def type_tier_key(cand):
    """**降序**排序键分量（`sort` 里取负 → 越小越前）：返回 `-leishen_end_tier`；未启用恒 0。"""
    if not ZERI_TYPE_TIER:
        return 0
    return -leishen_end_tier(cand)


def type_tier_rank(cand):
    """**升序**（`reverse=True`）排序键分量：返回 `leishen_end_tier`（越大越前）；
    未启用 → **恒 1（中性）**，与其它候选同值 → 逐位回退旧口径零回归。"""
    if not ZERI_TYPE_TIER:
        return 1
    return leishen_end_tier(cand)
