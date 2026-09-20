# -*- coding: utf-8 -*-
"""股票域自有六壬特征工程库（涨/跌 valence）
================================================
参考古例域已验证的确定性特征工程（engine/liuren_keti_bifa 的 八杀/神煞 valence +
求财 valence），把"传统吉凶"映射为"股票涨/跌"，构建股票域自有的、干净的特征库。

设计纪律（与古例域一致，且与 caishen_enhance 决裂）：
  1. 确定性、无泄漏：所有特征从盘面对应的字段（ba_sha / shen_sha / ri_gan / ri_zhi /
     san_chuan / sanchuan_tianjiang / si_ke）确定性算出，绝不读事后断语。
  2. 不注入任何"看涨偏置"：本库只如实反映盘面传统吉凶结构。caishen_enhance 那种
     "朱雀+六合=最高看涨"的硬编码看涨注入已被证明有害（古例域造成吉乐观偏置、
     股票域系统性推涨）——本库不依赖它，评估时配合 DISABLE_CAISHEN=1 使用。
  3. 以 zhanlei="求财" 把股票当作财运域处理（股票本就是财），复用古例域为求财调校过的
     占类化倍率（合/德 ×2 等），语义自洽。
  4. 生产隔离：仅当股票路径置了 analysis['_is_stock'] 且未置 DISABLE_STOCK_VALENCE 才
     注入（judgment_fusion.collect_signals 控制）；古例路径不置 _is_stock → 零影响。

诚实定位：本库是"特征保真度"库，不是"预测器"。它能否让股票方向预测跑赢朴素基线
（永远猜涨 55.3%，由 base_down_rate=44.7% 推出），由 regime_backtest 用独立市场标签
（收盘>开盘）检验——数据说话，不假设它能赢。
"""
from typing import Dict, Any, List

# 复用古例域已验证的确定性抽取原语（这些函数只依赖盘面字段，股票路径已全部现成产出）
from engine.liuren_keti_bifa import (
    extract_shen_sha_valence,
    extract_qiucai_valence,
)

# 股票域特征总开关（消融用；与古例域 ENABLED 同范式）
STOCK_VALENCE_ENABLED = True


def set_stock_valence_enabled(v: bool) -> None:
    global STOCK_VALENCE_ENABLED
    STOCK_VALENCE_ENABLED = bool(v)


def extract_stock_valence(result: Dict[str, Any], zhanlei: str = "求财") -> Dict[str, Any]:
    """从单条股票预测 result 抽取股票域涨/跌 valence。

    返回：
      {
        'stock_ba_sha':   int,   # 八杀 valence（占类化·确定性）→ 涨-positive 分数
        'stock_shen_sha': int,   # 神煞 valence（负向-only·确定性）→ 涨-positive 分数
        'stock_qiucai':  int,   # 求财 valence（财爻/青龙/财虚）→ 涨-positive 分数
        'score':          int,   # 三分量合计（参考用）
        'level':          str,   # '涨' / '跌' / '平'
        'details':        list,  # 人类可读说明
        'fired':          str,   # 触发分量代号串
      }
    不激活（STOCK_VALENCE_ENABLED=False）时三分量均返回 0。
    """
    if not STOCK_VALENCE_ENABLED:
        return {"stock_ba_sha": 0, "stock_shen_sha": 0, "stock_qiucai": 0,
                "score": 0, "level": "平", "details": [], "fired": ""}

    a = result.get('analysis', {}) or {}
    bi = result.get('basic_info', {}) or {}
    ri_gan = bi.get('ri_gan', '')
    ri_zhi = bi.get('ri_zhi', '')
    san_chuan = result.get('san_chuan', []) or []
    sanchuan_tianjiang = result.get('sanchuan_tianjiang', []) or []
    si_ke = result.get('si_ke', []) or []

    # ---- 八杀 + 神煞 valence（以求财占类化倍率；神煞仅负向，防凶重语料误推吉）----
    ss = extract_shen_sha_valence(a, zhanlei=zhanlei)
    ba_score = ss.get('ba_sha', {}).get('score', 0) or 0
    sha_score = ss.get('shen_sha', {}).get('score', 0) or 0

    # ---- 求财 valence（财爻生扶/青龙乘财=涨；财虚=跌；X 路守卫防假阳）----
    qc = extract_qiucai_valence(ri_gan, ri_zhi, san_chuan, sanchuan_tianjiang, si_ke, zhanlei=zhanlei)
    qc_score = qc.get('score', 0) or 0

    total = ba_score + sha_score + qc_score
    fired = []
    if ba_score:
        fired.append(f"八杀({ba_score:+d})")
    if sha_score:
        fired.append(f"神煞({sha_score:+d})")
    if qc_score:
        fired.append(f"求财{qc.get('fired', '')}({qc_score:+d})")

    details: List[str] = []
    ba_d = ss.get('ba_sha', {}).get('details', []) or []
    if ba_d:
        details.append("八杀: " + "; ".join(ba_d))
    sha_d = ss.get('shen_sha', {}).get('details', []) or []
    if sha_d:
        details.append("神煞: " + "; ".join(sha_d))
    if qc.get('details'):
        details.extend(qc.get('details'))

    return {
        "stock_ba_sha": ba_score,
        "stock_shen_sha": sha_score,
        "stock_qiucai": qc_score,
        "score": total,
        "level": ("涨" if total > 0 else ("跌" if total < 0 else "平")),
        "details": details,
        "fired": " + ".join(fired),
    }
