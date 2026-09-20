# -*- coding: utf-8 -*-
"""择日总分「重标定」刻度（2026-09-12 憨爷拍板「C·根治」）—— 单一真源。

【问题·实证】旧口径 `total_score = max(20, min(100, luma_base + bonus))`：
    原始分 R = luma_base + bonus 实测 **min 67 / 中位 130 / p90 150 / 最大 183**，
    **95.8% 的候选 R ≥ 100** → 全被 `min(100, …)` 削成同一个 100（旧值只有 8~16 个不同取值），
    连带 grade 也退化（**98.3% 恒为「上上吉」**）→ 分数与档位双双失去分辨力。

【根治】把 R **保序线性展开**到 [20, 100]：
        S = 20 + 80 * (R - R_LO) / (R_HI - R_LO)          （clamp [20, 100]）
    · 语义：**R ≥ R_HI ⇒ 100 分 = 满分级**（R_HI 取 180：跨 卯/子/午 三山 × 2026–2028 三年
      实测上限 183，向上取整）。
    · **保序** ⇒ R 越大分越高，排序语义不变（仅数值刻度变化）。
    · 档位随新刻度重划（90/80/70/60/40 不变），使「上上吉」回归稀缺、档位恢复区分度。

【回退】env `ZERI_SCORE_RESCALE=0` → 逐位回到旧口径（`min(100, …)`）。
【锚点】env `ZERI_SCORE_R_LO`（默认 20）／`ZERI_SCORE_R_HI`（默认 180）可调。

【生产链】引擎侧 `analyze_yidu_full` 出口重标定；生产 `stock_dashboard._ttl` 因需再叠加
    「命主加成 adj」后合成，故改用本模块对 **raw_total + adj** 一次性重标定，
    避免「先重标定、再 min(100, +adj)」造成的二次糊顶（adj 最大 18）。
"""
import os

ZERI_SCORE_RESCALE = os.environ.get('ZERI_SCORE_RESCALE', '1') == '1'
SCORE_R_LO = float(os.environ.get('ZERI_SCORE_R_LO', '20'))
SCORE_R_HI = float(os.environ.get('ZERI_SCORE_R_HI', '180'))

# 档位阈值（旧/新刻度共用；旧口径下 95.8% 落在 ≥90 → 「上上吉」退化）
GRADE_BANDS = ((90, '上上吉'), (80, '上吉'), (70, '中吉'), (60, '吉'), (40, '平'))


def rescale(raw):
    """把未削平原始分 R 保序展开到 [20, 100]。未启用时返回旧口径 `min(100, …)` 值。"""
    r = float(raw or 0)
    if not ZERI_SCORE_RESCALE:
        return max(20.0, min(100.0, r))
    span = SCORE_R_HI - SCORE_R_LO
    if span <= 0:
        return max(20.0, min(100.0, r))
    return round(max(20.0, min(100.0, 20.0 + 80.0 * (r - SCORE_R_LO) / span)), 1)


def grade_of(score):
    """按总分取档位（与 `analyze_yidu_full` 旧分档阈值完全一致）。"""
    s = float(score or 0)
    for thr, name in GRADE_BANDS:
        if s >= thr:
            return name
    return '凶'
