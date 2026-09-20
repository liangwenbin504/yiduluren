"""
十一分类实验 — 自动统计报告

功能：
  1. 按类别统计预测准确率（固定时辰 vs 日干偏财 vs 日支偏财 vs ...）
  2. 投票一致性 vs 准确率分析
  3. 按课体统计准确率
  4. 按预测趋势类型统计准确率
  5. 虚拟账户净值曲线
  6. 错误模式诊断

数据源：
  - _memory/stock_predictions.json    → 预测记录
  - _memory/virtual_portfolio_*.json   → 各账户净值
  - _memory/auto_trades_*.json         → 交易记录
"""
import json
import os
from datetime import datetime, date
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(BASE_DIR, "_memory")

CATEGORY_ORDER = ["fixed_time", "ri_gan_pian_cai", "ri_zhi_pian_cai", "ri_gan_shi_shen", "ri_zhi_shi_shen",
                  "ri_gan_zheng_yin", "ri_gan_pian_yin", "ri_zhi_zheng_yin", "ri_zhi_pian_yin", "random", "manual"]
CATEGORY_LABELS = {
    "fixed_time": "固定时辰课(09:00)",
    "ri_gan_pian_cai": "日干偏财时",
    "ri_zhi_pian_cai": "日支偏财时",
    "ri_gan_shi_shen": "日干食神时",
    "ri_zhi_shi_shen": "日支食神时",
    "ri_gan_zheng_yin": "日干正印时",
    "ri_gan_pian_yin": "日干偏印时",
    "ri_zhi_zheng_yin": "日支正印时",
    "ri_zhi_pian_yin": "日支偏印时",
    "random": "随机课(13:45)",
    "manual": "人工指定时",
}

TREND_DISPLAY = {
    "涨": "涨", "跌": "跌", "平": "平",
    "先涨后跌": "先涨后跌", "先跌后涨": "先跌后涨",
    "先涨后平": "先涨后平", "先跌后平": "先跌后平",
    "先平后涨": "先平后涨", "先平后跌": "先平后跌",
    "震荡偏涨": "震荡偏涨", "震荡偏跌": "震荡偏跌",
}


def load_json(filename: str):
    path = os.path.join(MEMORY_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════
#  核心统计
# ═══════════════════════════════════════════════════════════════

# 【2026-08-02 修复】方向词汇归一化：量化/天机预测存"看涨/看跌/震荡/看平"，
# 回检存"涨/跌/平"——不归一化则"涨"≠"看涨"永远算错。仅映射语义相同的词，
# 复合趋势（先涨后跌等）保持精确相等，不改变旧口径。
_DIR_NORM = {
    "看涨": "涨", "涨": "涨",
    "看跌": "跌", "跌": "跌",
    "看平": "平", "平": "平", "震荡": "平",
}

def _norm_dir(t: str):
    if not t:
        return t
    return _DIR_NORM.get(t, t)


def _is_correct(pred: dict) -> bool:
    """判断一条预测是否正确（方向归一化：看涨↔涨/看跌↔跌/看平↔平/震荡↔平）"""
    if pred.get("status") != "completed":
        return None
    actual = pred.get("actual_result")
    trend = pred.get("trend_prediction")
    if not actual or not trend:
        return None
    return _norm_dir(actual) == _norm_dir(trend)


def stat_by_category(predictions: list[dict]) -> dict:
    """按类别统计准确率"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        cat = p.get("category", "unknown")
        result = _is_correct(p)
        if result is None:
            continue
        groups[cat]["total"] += 1
        if result:
            groups[cat]["correct"] += 1

    stats = {}
    for cat in CATEGORY_ORDER:
        g = groups.get(cat, {"total": 0, "correct": 0})
        stats[cat] = {
            "label": CATEGORY_LABELS.get(cat, cat),
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        }
    # 汇总
    all_t = sum(s["total"] for s in stats.values())
    all_c = sum(s["correct"] for s in stats.values())
    stats["total"] = {
        "label": "合计",
        "total": all_t,
        "correct": all_c,
        "accuracy": round(all_c / all_t, 3) if all_t > 0 else 0,
    }
    return stats


def stat_by_vote_consistency(predictions: list[dict]) -> dict:
    """按投票一致性统计准确率"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        result = _is_correct(p)
        if result is None:
            continue
        vote = p.get("vote_result")
        if not vote or not isinstance(vote, dict):
            continue
        total_votes = sum(vote.values())
        max_votes = max(vote.values()) if vote else 0
        if total_votes < 1.5:
            continue
        max_ratio = max_votes / total_votes if total_votes > 0 else 0
        if max_ratio >= 0.8:
            key = "高置信度"
        elif max_ratio >= 0.5:
            key = "中置信度"
        else:
            key = "低置信度"
        groups[key]["total"] += 1
        if result:
            groups[key]["correct"] += 1

    stats = {}
    for label in ["高置信度", "中置信度", "低置信度"]:
        g = groups.get(label, {"total": 0, "correct": 0})
        stats[label] = {
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        }
    return stats


def stat_by_keti(predictions: list[dict]) -> dict:
    """按课体统计准确率"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        result = _is_correct(p)
        if result is None:
            continue
        keti = p.get("keti", "未知")
        groups[keti]["total"] += 1
        if result:
            groups[keti]["correct"] += 1

    stats = []
    for keti, g in sorted(groups.items(), key=lambda x: -x[1]["total"]):
        stats.append({
            "keti": keti,
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        })
    return stats


def stat_by_trend_type(predictions: list[dict]) -> dict:
    """按预测趋势类型统计准确率"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        result = _is_correct(p)
        if result is None:
            continue
        trend = p.get("trend_prediction", "未知")
        groups[trend]["total"] += 1
        if result:
            groups[trend]["correct"] += 1

    stats = []
    for trend, g in sorted(groups.items(), key=lambda x: -x[1]["total"]):
        stats.append({
            "trend": trend,
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        })
    return stats


def stat_by_month(predictions: list[dict]) -> dict:
    """按月统计准确率走势"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        result = _is_correct(p)
        if result is None:
            continue
        month_key = p.get("date", "")[:7]
        groups[month_key]["total"] += 1
        if result:
            groups[month_key]["correct"] += 1

    stats = []
    for month_key in sorted(groups.keys()):
        g = groups[month_key]
        stats.append({
            "month": month_key,
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        })
    return stats


def stat_by_rizhu(predictions: list[dict]) -> dict:
    """按日柱统计准确率"""
    groups = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in predictions:
        result = _is_correct(p)
        if result is None:
            continue
        rz = p.get("rizhu", "未知")
        groups[rz]["total"] += 1
        if result:
            groups[rz]["correct"] += 1

    stats = []
    for rz, g in sorted(groups.items(), key=lambda x: -x[1]["total"]):
        stats.append({
            "rizhu": rz,
            "total": g["total"],
            "correct": g["correct"],
            "accuracy": round(g["correct"] / g["total"], 3) if g["total"] > 0 else 0,
        })
    return stats


def stat_error_patterns(predictions: list[dict]) -> dict:
    """错误模式诊断 — 基础版（兼容旧调用）"""
    return _build_error_patterns(predictions)


# ═══════════════════════════════════════════════════════════════
#  建议③：增强版错误模式自动诊断
# ═══════════════════════════════════════════════════════════════

def _build_error_patterns(predictions: list[dict]) -> dict:
    """构建基础错误模式"""
    errors = [p for p in predictions if _is_correct(p) is False]
    if not errors:
        return {"total_errors": 0, "patterns": []}

    keti_counter = Counter(p.get("keti", "未知") for p in errors)
    trend_counter = Counter(p.get("trend_prediction", "未知") for p in errors)
    cat_counter = Counter(p.get("category", "unknown") for p in errors)

    return {
        "total_errors": len(errors),
        "keti_breakdown": [{"keti": k, "count": v, "pct": round(v/len(errors)*100, 1)}
                          for k, v in keti_counter.most_common()],
        "trend_breakdown": [{"trend": k, "count": v, "pct": round(v/len(errors)*100, 1)}
                           for k, v in trend_counter.most_common()],
        "category_breakdown": [{"category": k, "count": v, "pct": round(v/len(errors)*100, 1)}
                              for k, v in cat_counter.most_common()],
    }


def stat_confusion_matrix(predictions: list[dict]) -> dict:
    """构建混淆矩阵 — actual_result vs trend_prediction"""
    reviewed = [p for p in predictions if _is_correct(p) is not None]
    if not reviewed:
        return {"matrix": {}, "total": 0, "correct": 0}

    all_trends = sorted(set(
        list(p.get("trend_prediction", "") for p in reviewed) +
        list(p.get("actual_result", "") for p in reviewed)
    ))

    matrix = {ref: {pred: 0 for pred in all_trends} for ref in all_trends}
    correct = 0
    total = len(reviewed)

    for p in reviewed:
        ref = p.get("actual_result", "")
        pred = p.get("trend_prediction", "")
        if ref in matrix and pred in matrix[ref]:
            matrix[ref][pred] += 1
            if _norm_dir(ref) == _norm_dir(pred):   # 【2026-08-02 修复】方向归一化后判定命中
                correct += 1

    # 按类别分别构建
    cat_matrix = {}
    for cat in CATEGORY_ORDER:
        cat_preds = [p for p in reviewed if p.get("category") == cat]
        if not cat_preds:
            continue
        cm = {ref: {pred: 0 for pred in all_trends} for ref in all_trends}
        for p in cat_preds:
            ref = p.get("actual_result", "")
            pred = p.get("trend_prediction", "")
            if ref in cm and pred in cm[ref]:
                cm[ref][pred] += 1
        cat_matrix[cat] = cm

    # 按投票一致性分别构建
    vote_matrix = {}
    for vkey, vlabel in [("高置信度", "full"), ("中置信度", "majority"), ("低置信度", "weak")]:
        vpreds = []
        for p in reviewed:
            vote = p.get("vote_result")
            if not vote or not isinstance(vote, dict):
                continue
            total_votes = sum(vote.values())
            max_votes = max(vote.values()) if vote else 0
            if total_votes < 1.5:
                continue
            max_ratio = max_votes / total_votes
            if vkey == "高置信度" and max_ratio >= 0.8:
                vpreds.append(p)
            elif vkey == "中置信度" and 0.5 <= max_ratio < 0.8:
                vpreds.append(p)
            elif vkey == "低置信度" and max_ratio < 0.5:
                vpreds.append(p)
        if vpreds:
            cm = {ref: {pred: 0 for pred in all_trends} for ref in all_trends}
            for p in vpreds:
                ref = p.get("actual_result", "")
                pred = p.get("trend_prediction", "")
                if ref in cm and pred in cm[ref]:
                    cm[ref][pred] += 1
            vote_matrix[vlabel] = cm

    return {
        "matrix": matrix,
        "all_labels": all_trends,
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 3) if total > 0 else 0,
        "by_category": cat_matrix,
        "by_vote_consistency": vote_matrix,
    }


def stat_bias_analysis(predictions: list[dict]) -> dict:
    """系统性偏差检测

    检测以下偏差模式：
    1. 方向偏差 — 系统是否偏向某一方向（涨/跌）
    2. 复合趋势滥用 — 过度使用"先涨后跌"等复合趋势
    3. 保守偏差 — 回避极端判断，倾向中间结果
    4. 类别偏差 — 某类预测系统性偏乐观/悲观
    """
    reviewed = [p for p in predictions if _is_correct(p) is not None]
    if len(reviewed) < 3:
        return {"biases": [], "note": "数据不足（<3条），无法进行有意义的偏差分析"}

    findings = []

    # ── 1. 方向偏差 ──
    direction_map = {
        "涨": "涨", "跌": "跌",
        "看涨": "涨", "看跌": "跌", "看平": "平", "震荡": "平",
        "先涨后跌": "涨→跌", "先跌后涨": "跌→涨",
        "先涨后平": "涨→平", "先跌后平": "跌→平",
        "先平后涨": "涨", "先平后跌": "跌",
        "震荡偏涨": "涨", "震荡偏跌": "跌",
        "平": "平",
    }

    actual_up = sum(1 for p in reviewed if direction_map.get(p.get("actual_result", "")) == "涨")
    actual_down = sum(1 for p in reviewed if direction_map.get(p.get("actual_result", "")) == "跌")
    pred_up = sum(1 for p in reviewed if direction_map.get(p.get("trend_prediction", "")) == "涨")
    pred_down = sum(1 for p in reviewed if direction_map.get(p.get("trend_prediction", "")) == "跌")

    total_directional = actual_up + actual_down
    if total_directional >= 5:
        actual_ratio = actual_up / total_directional
        pred_ratio = pred_up / (pred_up + pred_down) if (pred_up + pred_down) > 0 else 0.5
        bias = pred_ratio - actual_ratio
        if abs(bias) > 0.15:
            direction = "乐观" if bias > 0 else "悲观"
            findings.append({
                "type": "direction_bias",
                "severity": "high" if abs(bias) > 0.3 else "medium",
                "name": f"方向偏差（{direction}）",
                "detail": (
                    f"实际上涨占比{actual_ratio:.0%}，预测上涨占比{pred_ratio:.0%}，"
                    f"偏差{bias:+.0%}。系统倾向于预测{'上涨' if bias > 0 else '下跌'}。"
                ),
                "metric": round(bias, 3),
                "suggestion": (
                    "检查Prompt中是否过度强调某一方向的信号权重，"
                    "建议平衡涨跌判断标准" if direction == "乐观"
                    else "检查Prompt中是否过度强调风险信号，建议适当降低风险权重"
                ),
            })

    # ── 2. 复合趋势滥用 ──
    compound_trends = {"先涨后跌", "先跌后涨", "先涨后平", "先跌后平", "先平后涨", "先平后跌"}
    simple_trends = {"涨", "跌", "平"}

    actual_compound = sum(1 for p in reviewed if p.get("actual_result", "") in compound_trends)
    pred_compound = sum(1 for p in reviewed if p.get("trend_prediction", "") in compound_trends)
    wrong_compound = sum(
        1 for p in reviewed
        if p.get("actual_result", "") in simple_trends
        and p.get("trend_prediction", "") in compound_trends
        and _is_correct(p) is False
    )

    if len(reviewed) >= 5 and pred_compound > 0:
        actual_cr = actual_compound / len(reviewed)
        pred_cr = pred_compound / len(reviewed)
        if pred_cr > actual_cr + 0.15:
            findings.append({
                "type": "compound_overuse",
                "severity": "high" if (pred_cr - actual_cr) > 0.3 else "medium",
                "name": "复合趋势滥用",
                "detail": (
                    f"实际复合趋势占比{actual_cr:.0%}，预测复合趋势占比{pred_cr:.0%}，"
                    f"其中有{wrong_compound}次把简单趋势误判为复合趋势。"
                ),
                "metric": round(pred_cr - actual_cr, 3),
                "suggestion": (
                    "在Prompt中增加指令：'只有当三传走势明确显示先A后B的结构时才使用复合趋势'。"
                    "简单上涨就是涨，简单下跌就是跌。"
                ),
            })

    # ── 3. 保守偏差（回避极端判断） ──
    # 分析是否系统性地回避"涨"/"跌"，而倾向"平"/"震荡"等中间结果
    actual_extreme = sum(1 for p in reviewed if p.get("actual_result", "") in ("涨", "跌"))
    pred_extreme = sum(1 for p in reviewed if p.get("trend_prediction", "") in ("涨", "跌"))

    if len(reviewed) >= 5:
        actual_er = actual_extreme / len(reviewed)
        pred_er = pred_extreme / len(reviewed)
        if pred_er < actual_er - 0.15:
            findings.append({
                "type": "conservative_bias",
                "severity": "medium",
                "name": "保守偏差（回避极端判断）",
                "detail": (
                    f"实际极端趋势（涨/跌）占比{actual_er:.0%}，"
                    f"预测极端趋势占比{pred_er:.0%}，"
                    f"系统倾向于输出平/震荡/复合趋势等中性判断。"
                ),
                "metric": round(actual_er - pred_er, 3),
                "suggestion": (
                    "增加指令：'当课象信号明确时，大胆判断涨或跌，"
                    "不要因为怕错而回避方向性判断'。"
                ),
            })

    # ── 4. 类别偏差 ──
    cat_correctness = {}
    for cat in CATEGORY_ORDER:
        cat_preds = [p for p in reviewed if p.get("category") == cat]
        if len(cat_preds) < 2:
            continue
        correct = sum(1 for p in cat_preds if _is_correct(p) is True)
        cat_correctness[cat] = {
            "total": len(cat_preds),
            "correct": correct,
            "accuracy": correct / len(cat_preds),
        }

    if len(cat_correctness) >= 2:
        accs = [(cat, info["accuracy"]) for cat, info in cat_correctness.items()]
        accs.sort(key=lambda x: x[1])
        best_cat, best_acc = accs[-1]
        worst_cat, worst_acc = accs[0]
        if best_acc - worst_acc > 0.25 and best_acc > 0.5:
            findings.append({
                "type": "category_bias",
                "severity": "high" if (best_acc - worst_acc) > 0.4 else "medium",
                "name": f"类别准确率偏差（{worst_cat}偏低）",
                "detail": (
                    f"最高类别{best_cat}准确率{best_acc:.0%}，"
                    f"最低类别{worst_cat}准确率{worst_acc:.0%}，"
                    f"差距{best_acc-worst_acc:.0%}。"
                ),
                "metric": round(best_acc - worst_acc, 3),
                "suggestion": (
                    f"检查{worst_cat}类别的排盘/判断逻辑是否有系统性问题，"
                    f"参考{best_cat}类别的判断模式进行调整。"
                ),
            })

    # ── 5. 投票一致性偏差 ──
    vote_stats = stat_by_vote_consistency(predictions)
    if vote_stats:
        full = vote_stats.get("高置信度", {})
        weak = vote_stats.get("低置信度", {})
        if full["total"] >= 2 and weak["total"] >= 2:
            diff = full["accuracy"] - weak["accuracy"]
            if diff > 0.3:
                findings.append({
                    "type": "vote_consistency_bias",
                    "severity": "medium",
                    "name": "投票一致性偏差",
                    "detail": (
                        f"高置信度准确率{full['accuracy']:.0%}，"
                        f"低置信度准确率{weak['accuracy']:.0%}，"
                        f"差距{diff:.0%}。说明低置信度时判断可靠性显著下降。"
                    ),
                    "metric": round(diff, 3),
                    "suggestion": (
                        "建议对低置信度的预测结果进行标记，"
                        "在交易时降低仓位或不交易。"
                    ),
                })

    return {
        "total_reviewed": len(reviewed),
        "biases": findings,
        "summary": ", ".join(f["name"] for f in findings) if findings else "未检测到系统性偏差",
    }


def stat_error_feature_correlation(predictions: list[dict]) -> dict:
    """错误特征关联分析 — 分析错误与各特征维度的相关性"""
    reviewed = [p for p in predictions if _is_correct(p) is not None]
    if len(reviewed) < 3:
        return {"note": "数据不足"}

    # ── 课体 vs 准确率 ──
    keti_stats = stat_by_keti(predictions)
    keti_analysis = []
    for s in keti_stats:
        if s["total"] >= 2:
            keti_analysis.append(s)

    # ── 日柱 vs 准确率 ──
    rizhu_stats = stat_by_rizhu(predictions)
    rizhu_analysis = []
    for s in rizhu_stats:
        if s["total"] >= 2:
            rizhu_analysis.append(s)

    # ── 投票一致性 vs 准确率 ──
    vote_stats = stat_by_vote_consistency(predictions)

    # ── 旬空关联 ──
    # 读取预测数据中的reasoning_chain，看是否提到了旬空
    xunkong_errors = 0
    xunkong_total = 0
    no_xunkong_errors = 0
    no_xunkong_total = 0
    for p in reviewed:
        rc = p.get("reasoning_chain", {})
        if isinstance(rc, dict):
            has_xunkong = any("旬空" in str(v) for v in rc.values())
        else:
            has_xunkong = "旬空" in str(rc)
        is_err = _is_correct(p) is False
        if has_xunkong:
            xunkong_total += 1
            if is_err:
                xunkong_errors += 1
        else:
            no_xunkong_total += 1
            if is_err:
                no_xunkong_errors += 1

    xunkong_analysis = {}
    if xunkong_total >= 2:
        xunkong_analysis["has_xunkong"] = {
            "total": xunkong_total,
            "errors": xunkong_errors,
            "accuracy": round(1 - xunkong_errors / xunkong_total, 3),
        }
    if no_xunkong_total >= 2:
        xunkong_analysis["no_xunkong"] = {
            "total": no_xunkong_total,
            "errors": no_xunkong_errors,
            "accuracy": round(1 - no_xunkong_errors / no_xunkong_total, 3),
        }

    # ── 三传关联（初传地支五行 vs 准确率） ──
    wuxing_map = {"寅": "木", "卯": "木", "巳": "火", "午": "火",
                   "辰": "土", "戌": "土", "丑": "土", "未": "土",
                   "申": "金", "酉": "金", "亥": "水", "子": "水"}
    chu_chuan_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in reviewed:
        sanchuan = p.get("sanchuan", [])
        if sanchuan and len(sanchuan) > 0:
            chuchuan = sanchuan[0]
            wx = wuxing_map.get(chuchuan, "未知")
            chu_chuan_stats[wx]["total"] += 1
            if _is_correct(p) is True:
                chu_chuan_stats[wx]["correct"] += 1

    chuchuan_analysis = []
    for wx, st in sorted(chu_chuan_stats.items(), key=lambda x: -x[1]["total"]):
        if st["total"] >= 2:
            chuchuan_analysis.append({
                "wuxing": wx,
                "total": st["total"],
                "correct": st["correct"],
                "accuracy": round(st["correct"] / st["total"], 3),
            })

    # ── 发用类型关联 ──
    fayong_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for p in reviewed:
        fayong = p.get("fayong", "未知")
        fayong_stats[fayong]["total"] += 1
        if _is_correct(p) is True:
            fayong_stats[fayong]["correct"] += 1

    fayong_analysis = []
    for fy, st in sorted(fayong_stats.items(), key=lambda x: -x[1]["total"]):
        if st["total"] >= 2:
            fayong_analysis.append({
                "fayong": fy,
                "total": st["total"],
                "correct": st["correct"],
                "accuracy": round(st["correct"] / st["total"], 3),
            })

    return {
        "keti": keti_analysis,
        "rizhu": rizhu_analysis,
        "vote_consistency": vote_stats,
        "xunkong": xunkong_analysis,
        "chuchuan_wuxing": chuchuan_analysis,
        "fayong": fayong_analysis,
    }


def stat_error_streaks(predictions: list[dict]) -> dict:
    """连续错误/正确分析"""
    reviewed = [p for p in predictions if _is_correct(p) is not None]
    if not reviewed:
        return {"note": "无数据"}

    # 按日期排序
    sorted_preds = sorted(reviewed, key=lambda p: p.get("date", ""))
    results = [_is_correct(p) for p in sorted_preds]

    # 最长连续正确/错误
    max_correct = 0
    max_error = 0
    current_correct = 0
    current_error = 0
    current_streak = 0

    for r in results:
        if r is True:
            current_correct += 1
            current_error = 0
            max_correct = max(max_correct, current_correct)
        else:
            current_error += 1
            current_correct = 0
            max_error = max(max_error, current_error)

    # 当前连续状态
    if results:
        current_streak_val = 0
        current_streak_type = None
        for r in reversed(results):
            if current_streak_type is None:
                current_streak_type = "correct" if r else "error"
                current_streak_val = 1
            elif r is True and current_streak_type == "correct":
                current_streak_val += 1
            elif r is False and current_streak_type == "error":
                current_streak_val += 1
            else:
                break
        current_streak = {
            "type": current_streak_type,
            "length": current_streak_val,
        }
    else:
        current_streak = {"type": "none", "length": 0}

    # 近期趋势（最近N条准确率）
    window_sizes = [5, 10, 20]
    trends = {}
    for w in window_sizes:
        if len(results) >= w:
            recent = results[-w:]
            trends[f"last_{w}"] = {
                "count": w,
                "correct": sum(recent),
                "accuracy": round(sum(recent) / w, 3),
            }

    # 按类别分别统计连续错误
    cat_streaks = {}
    for cat in CATEGORY_ORDER:
        cat_preds = [p for p in sorted_preds if p.get("category") == cat]
        cat_results = [_is_correct(p) for p in cat_preds]
        if len(cat_results) >= 2:
            max_cat_err = 0
            cur_cat_err = 0
            for r in cat_results:
                if r is False:
                    cur_cat_err += 1
                    max_cat_err = max(max_cat_err, cur_cat_err)
                else:
                    cur_cat_err = 0
            cat_streaks[cat] = {
                "total": len(cat_results),
                "max_consecutive_errors": max_cat_err,
            }

    return {
        "total_sequences": len(results),
        "max_correct_streak": max_correct,
        "max_error_streak": max_error,
        "current_streak": current_streak,
        "recent_trends": trends,
        "by_category": cat_streaks,
    }


def stat_error_summary(predictions: list[dict]) -> dict:
    """综合错误诊断 — 聚合所有分析维度"""
    return {
        "basic": _build_error_patterns(predictions),
        "confusion_matrix": stat_confusion_matrix(predictions),
        "bias_analysis": stat_bias_analysis(predictions),
        "feature_correlation": stat_error_feature_correlation(predictions),
        "streaks": stat_error_streaks(predictions),
    }


def generate_insights(predictions: list[dict] = None) -> list[dict]:
    """基于错误模式生成可执行的改进建议"""
    if predictions is None:
        data = load_json("stock_predictions.json")
        predictions = data if isinstance(data, list) else (data.get("predictions", []) if data else [])

    reviewed = [p for p in predictions if _is_correct(p) is not None]
    if len(reviewed) < 3:
        return [{"priority": "info", "category": "general", "message": "数据不足（<3条），暂无法生成有意义的洞察"}]

    insights = []

    # ── 1. 总体表现 ──
    correct = sum(1 for p in reviewed if _is_correct(p) is True)
    total = len(reviewed)
    acc = correct / total
    if acc < 0.4:
        insights.append({
            "priority": "critical",
            "category": "overall",
            "message": f"总准确率仅{acc:.0%}（{correct}/{total}），低于随机水平，建议暂停交易并全面检查Prompt。",
        })
    elif acc < 0.6:
        insights.append({
            "priority": "warning",
            "category": "overall",
            "message": f"总准确率{acc:.0%}（{correct}/{total}），处于中等水平，有提升空间。",
        })
    else:
        insights.append({
            "priority": "good",
            "category": "overall",
            "message": f"总准确率{acc:.0%}（{correct}/{total}），表现良好。",
        })

    # ── 2. 类别对比 ──
    cat_stat = stat_by_category(predictions)
    cat_accs = [(cat, s["accuracy"]) for cat, s in cat_stat.items() if cat in CATEGORY_ORDER and s["total"] >= 2]
    if len(cat_accs) >= 2:
        cat_accs.sort(key=lambda x: x[1])
        worst_cat, worst_acc = cat_accs[0]
        best_cat, best_acc = cat_accs[-1]
        if worst_acc < 0.4 and best_acc > 0.5:
            insights.append({
                "priority": "high",
                "category": "category",
                "message": (
                    f"{CATEGORY_LABELS.get(worst_cat, worst_cat)}准确率仅{worst_acc:.0%}，"
                    f"远低于{best_cat}的{best_acc:.0%}。建议检查该类别排盘逻辑。"
                ),
            })

    # ── 3. 投票一致性 ──
    vote_stat = stat_by_vote_consistency(predictions)
    full = vote_stat.get("高置信度", {})
    weak = vote_stat.get("低置信度", {})
    if full["total"] >= 2:
        if full["accuracy"] >= 0.7:
            insights.append({
                "priority": "good",
                "category": "vote",
                "message": f"高置信度时准确率{full['accuracy']:.0%}（{full['correct']}/{full['total']}），高置信度可靠。",
            })
        elif full["accuracy"] < 0.5:
            insights.append({
                "priority": "high",
                "category": "vote",
                "message": f"高置信度时准确率仅{full['accuracy']:.0%}（{full['correct']}/{full['total']}），说明三个AI存在系统性共识错误，需检查Prompt基础设定。",
            })
    if weak["total"] >= 2 and weak["accuracy"] < 0.4:
        insights.append({
            "priority": "warning",
            "category": "vote",
            "message": f"低置信度时准确率{weak['accuracy']:.0%}，建议对此类预测降低交易仓位或放弃交易。",
        })

    # ── 4. 连续错误 ──
    streaks = stat_error_streaks(predictions)
    if streaks.get("max_error_streak", 0) >= 3:
        insights.append({
            "priority": "warning",
            "category": "streak",
            "message": f"出现最长{streaks['max_error_streak']}次连续错误，建议出现连续2次错误后暂停该类别预测。",
        })
    if streaks.get("current_streak", {}).get("type") == "error" and streaks["current_streak"]["length"] >= 2:
        insights.append({
            "priority": "warning",
            "category": "streak",
            "message": f"当前处于{streaks['current_streak']['length']}次连续错误中，建议启动应急检查。",
        })

    # ── 5. 特征关联 ──
    feature_corr = stat_error_feature_correlation(predictions)
    for k in feature_corr.get("keti", []):
        if k["total"] >= 3 and k["accuracy"] < 0.4:
            insights.append({
                "priority": "high" if k["accuracy"] < 0.25 else "medium",
                "category": "keti",
                "message": f"课体'{k['keti']}'准确率仅{k['accuracy']:.0%}（{k['correct']}/{k['total']}），建议检查该课体的判断逻辑。",
            })
    for f in feature_corr.get("fayong", []):
        if f["total"] >= 3 and f["accuracy"] < 0.4:
            insights.append({
                "priority": "medium",
                "category": "fayong",
                "message": f"发用'{f['fayong']}'准确率仅{f['accuracy']:.0%}（{f['correct']}/{f['total']}），建议核对发用判断规则。",
            })
    for wx in feature_corr.get("chuchuan_wuxing", []):
        if wx["total"] >= 3 and wx["accuracy"] < 0.4:
            insights.append({
                "priority": "medium",
                "category": "chuchuan_wuxing",
                "message": f"初传{wx['wuxing']}五行时准确率仅{wx['accuracy']:.0%}（{wx['correct']}/{wx['total']}），建议检查该五行判断逻辑。",
            })
    xk = feature_corr.get("xunkong", {})
    if "has_xunkong" in xk and "no_xunkong" in xk:
        xk_acc = xk["has_xunkong"]["accuracy"]
        no_xk_acc = xk["no_xunkong"]["accuracy"]
        if xk_acc < no_xk_acc - 0.2 and xk["has_xunkong"]["total"] >= 2:
            insights.append({
                "priority": "medium",
                "category": "xunkong",
                "message": (
                    f"涉及旬空时准确率{xk_acc:.0%}，低于无旬空时的{no_xk_acc:.0%}，"
                    f"差异{(no_xk_acc - xk_acc):.0%}。建议检查旬空引擎的判断逻辑。"
                ),
            })

    # ── 6. 偏差分析 ──
    bias = stat_bias_analysis(predictions)
    for b in bias.get("biases", []):
        insights.append({
            "priority": b["severity"],
            "category": "bias",
            "message": f"{b['name']}：{b['detail']}",
        })

    return insights


# ═══════════════════════════════════════════════════════════════
#  账户统计
# ═══════════════════════════════════════════════════════════════

def stat_portfolios() -> list[dict]:
    """读取三个虚拟账户的净值"""
    stats = []
    for cat in CATEGORY_ORDER:
        fname = f"virtual_portfolio_{cat}.json"
        data = load_json(fname)
        if data is None:
            stats.append({"category": cat, "label": CATEGORY_LABELS.get(cat, cat),
                          "status": "未初始化", "total_value": 0, "profit_pct": 0})
            continue
        init = data.get("initial_capital", 100000)
        total = data.get("total_value", data.get("cash", 0))
        profit_pct = round((total - init) / init * 100, 2)
        stats.append({
            "category": cat,
            "label": CATEGORY_LABELS.get(cat, cat),
            "status": "运行中",
            "initial_capital": init,
            "cash": data.get("cash", 0),
            "shares": data.get("shares", 0),
            "position_value": data.get("position_value", 0),
            "total_value": total,
            "high_water_mark": data.get("high_water_mark", init),
            "profit": round(total - init, 2),
            "profit_pct": profit_pct,
        })
    return stats


def stat_trade_counts() -> dict:
    """统计各账户交易次数"""
    result = {}
    for cat in CATEGORY_ORDER:
        fname = f"auto_trades_{cat}.json"
        data = load_json(fname)
        if data is None or "trades" not in data:
            result[cat] = {"buy": 0, "sell": 0, "total": 0}
            continue
        buys = sum(1 for t in data["trades"] if isinstance(t, dict) and t.get("type") == "buy")
        sells = sum(1 for t in data["trades"] if isinstance(t, dict) and t.get("type") == "sell")
        result[cat] = {"buy": buys, "sell": sells, "total": buys + sells}
    return result


# ═══════════════════════════════════════════════════════════════
#  报告生成
# ═══════════════════════════════════════════════════════════════

def _bar(pct: float, width: int = 20) -> str:
    """生成进度条"""
    if pct <= 0:
        return "░" * width
    filled = max(1, int(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def _pct_str(accuracy: float) -> str:
    """格式化百分比字符串"""
    return f"{accuracy * 100:>5.1f}%"


def _vline() -> str:
    return "  │"


def generate_full_report(predictions: list[dict] = None) -> str:
    """生成完整的统计报告文本"""
    if predictions is None:
        data = load_json("stock_predictions.json")
        predictions = data if isinstance(data, list) else (data.get("predictions", []) if data else [])

    if not predictions:
        return "⚠ 暂无预测数据"

    all_count = len(predictions)
    completed = [p for p in predictions if p.get("status") == "completed"]
    pending = [p for p in predictions if p.get("status") != "completed"]
    reviewed = [p for p in predictions if p.get("actual_result") is not None]
    start_date = min((p.get("date", "") for p in predictions if p.get("date")), default="?")
    end_date = max((p.get("date", "") for p in predictions if p.get("date")), default="?")

    lines = []
    lines.append("")
    lines.append("╔════════════════════════════════════════════════════════════╗")
    lines.append("║       十一分类实验自动统计报告                          ║")
    lines.append(f"║       {start_date} → {end_date}                           ║")
    lines.append("╚════════════════════════════════════════════════════════════╝")
    lines.append("")

    # ── 概览 ──
    lines.append("📊 数据概览")
    lines.append("━" * 55)
    lines.append(f"  总预测数:      {all_count}")
    lines.append(f"  已完成对照:    {len(reviewed)}")
    lines.append(f"  待对照:        {len(pending)}")
    reviewed_correct = sum(1 for p in reviewed if _is_correct(p) is True)
    reviewed_wrong = sum(1 for p in reviewed if _is_correct(p) is False)
    if reviewed:
        lines.append(f"  正确:          {reviewed_correct}")
        lines.append(f"  错误:          {reviewed_wrong}")
        acc = reviewed_correct / len(reviewed)
        lines.append(f"  总准确率:      {_pct_str(acc)}  {_bar(acc * 100)}")
    lines.append("")

    # ── 按类别统计 ──
    cat_stat = stat_by_category(predictions)
    lines.append("📈 按类别统计准确率")
    lines.append("━" * 55)
    lines.append(f"  {'类别':<20} {'次数':>6} {'正确':>6} {'准确率':>8}")
    lines.append(f"  {'─'*20} {'─'*6} {'─'*6} {'─'*8}")
    for cat in CATEGORY_ORDER:
        s = cat_stat.get(cat, {})
        if s["total"] > 0:
            lines.append(f"  {s['label']:<20} {s['total']:>6} {s['correct']:>6} {_pct_str(s['accuracy']):>8}")
    t = cat_stat.get("total", {})
    if t["total"] > 0:
        lines.append(f"  {'─'*20} {'─'*6} {'─'*6} {'─'*8}")
        lines.append(f"  {t['label']:<20} {t['total']:>6} {t['correct']:>6} {_pct_str(t['accuracy']):>8}")
    lines.append("")

    # ── 投票一致性 vs 准确率 ──
    vote_stat = stat_by_vote_consistency(predictions)
    if any(s["total"] > 0 for s in vote_stat.values()):
        lines.append("🔥 投票一致性 vs 准确率")
        lines.append("━" * 55)
        for label, s in vote_stat.items():
            if s["total"] > 0:
                bar = _bar(s["accuracy"] * 100)
                lines.append(f"  {label:<14} {s['total']:>4}次  正确{s['correct']:>3}次  {_pct_str(s['accuracy'])}  {bar}")
        lines.append("")

    # ── 按课体统计 ──
    keti_stat = stat_by_keti(predictions)
    if keti_stat:
        lines.append("📖 按课体统计准确率")
        lines.append("━" * 55)
        lines.append(f"  {'课体':<12} {'次数':>6} {'正确':>6} {'准确率':>8}")
        lines.append(f"  {'─'*12} {'─'*6} {'─'*6} {'─'*8}")
        for s in keti_stat[:10]:
            lines.append(f"  {s['keti']:<12} {s['total']:>6} {s['correct']:>6} {_pct_str(s['accuracy']):>8}")
        lines.append("")

    # ── 按趋势类型统计 ──
    trend_stat = stat_by_trend_type(predictions)
    if trend_stat:
        lines.append("🎯 按预测趋势类型统计准确率")
        lines.append("━" * 55)
        lines.append(f"  {'趋势':<12} {'次数':>6} {'正确':>6} {'准确率':>8}")
        lines.append(f"  {'─'*12} {'─'*6} {'─'*6} {'─'*8}")
        for s in trend_stat:
            lines.append(f"  {s['trend']:<12} {s['total']:>6} {s['correct']:>6} {_pct_str(s['accuracy']):>8}")
        lines.append("")

    # ── 按月走势 ──
    month_stat = stat_by_month(predictions)
    if len(month_stat) > 1:
        lines.append("📅 准确率月度走势")
        lines.append("━" * 55)
        for s in month_stat:
            bar = _bar(s["accuracy"] * 100)
            lines.append(f"  {s['month']}  {s['correct']:>3}/{s['total']:<3}  {_pct_str(s['accuracy'])}  {bar}")
        lines.append("")

    # ── 增强版错误模式诊断 ──
    err_summary = stat_error_summary(predictions)
    err = err_summary["basic"]
    if err["total_errors"] > 0:
        lines.append("🔍 错误模式诊断")
        lines.append("━" * 55)
        lines.append(f"  总错误数: {err['total_errors']}")

        lines.append(f"  ├ 错误时课体分布:")
        for item in err.get("keti_breakdown", [])[:5]:
            lines.append(f"  │   {item['keti']:<10} {item['count']:>3}次 ({item['pct']}%)")
        lines.append(f"  ├ 错误时趋势分布:")
        for item in err.get("trend_breakdown", [])[:5]:
            lines.append(f"  │   {item['trend']:<10} {item['count']:>3}次 ({item['pct']}%)")
        lines.append(f"  └ 错误时类别分布:")
        for item in err.get("category_breakdown", []):
            lines.append(f"      {item['category']:<12} {item['count']:>3}次 ({item['pct']}%)")
        lines.append("")

    # ── 混淆矩阵 ──
    cm = err_summary.get("confusion_matrix", {})
    if cm.get("total", 0) >= 3:
        lines.append("📊 混淆矩阵 (actual → prediction)")
        lines.append("━" * 55)
        labels = cm.get("all_labels", [])
        matrix = cm.get("matrix", {})
        for ref in labels:
            if ref in matrix and any(matrix[ref].values()):
                row_parts = [f"{ref:<8}"]
                for pred in labels:
                    v = matrix[ref].get(pred, 0)
                    if ref == pred and v > 0:
                        row_parts.append(f"\033[92m{v:>3}\033[0m")
                    elif v > 0:
                        row_parts.append(f"\033[91m{v:>3}\033[0m")
                    else:
                        row_parts.append(f"{v:>3}")
                lines.append("  " + " ".join(row_parts))
        # 按类别混淆矩阵
        for cat in CATEGORY_ORDER:
            cat_m = cm.get("by_category", {}).get(cat, {})
            if cat_m and any(any(v.values()) for v in cat_m.values()):
                lines.append(f"  ── {CATEGORY_LABELS.get(cat, cat)} ──")
                for ref in labels:
                    if ref in cat_m and any(cat_m[ref].values()):
                        row_parts = [f"{ref:<8}"]
                        for pred in labels:
                            v = cat_m[ref].get(pred, 0)
                            if ref == pred and v > 0:
                                row_parts.append(f"\033[92m{v:>3}\033[0m")
                            elif v > 0:
                                row_parts.append(f"\033[91m{v:>3}\033[0m")
                            else:
                                row_parts.append(f"{v:>3}")
                        lines.append("  " + " ".join(row_parts))
        lines.append("")

    # ── 系统性偏差检测 ──
    bias = err_summary.get("bias_analysis", {})
    if bias.get("biases"):
        lines.append("⚠️ 系统性偏差检测")
        lines.append("━" * 55)
        for b in bias["biases"]:
            severity_tag = "🔴" if b["severity"] == "high" else ("🟡" if b["severity"] == "medium" else "🟢")
            lines.append(f"  {severity_tag} {b['name']}")
            lines.append(f"     {b['detail']}")
            lines.append(f"     建议: {b.get('suggestion', '')}")
        lines.append("")

    # ── 连续错误分析 ──
    streaks = err_summary.get("streaks", {})
    if streaks.get("total_sequences", 0) >= 3:
        lines.append("📈 连续状态分析")
        lines.append("━" * 55)
        lines.append(f"  最长连续正确: {streaks['max_correct_streak']}次")
        lines.append(f"  最长连续错误: {streaks['max_error_streak']}次")
        cur = streaks.get("current_streak", {})
        if cur.get("length", 0) > 0:
            lines.append(f"  当前状态: {'✅ 连续正确' if cur['type']=='correct' else '❌ 连续错误'} {cur['length']}次")
        for w_name, w_data in streaks.get("recent_trends", {}).items():
            lines.append(f"  近期{w_name.replace('last_','')}条: {w_data['correct']}/{w_data['count']} ({w_data['accuracy']*100:.0f}%)")
        lines.append("")

    # ── 特征关联分析 ──
    fc = err_summary.get("feature_correlation", {})
    if fc.get("keti"):
        has_low = any(k["accuracy"] < 0.5 for k in fc["keti"] if k["total"] >= 3)
        if has_low:
            lines.append("📉 低准确率特征警示")
            lines.append("━" * 55)
            for k in fc["keti"]:
                if k["accuracy"] < 0.4 and k["total"] >= 3:
                    lines.append(f"  ├ 课体'{k['keti']}': {k['accuracy']*100:.0f}% ({k['correct']}/{k['total']})")
            for f in fc.get("fayong", []):
                if f["accuracy"] < 0.4 and f["total"] >= 3:
                    lines.append(f"  ├ 发用'{f['fayong']}': {f['accuracy']*100:.0f}% ({f['correct']}/{f['total']})")
            for wx in fc.get("chuchuan_wuxing", []):
                if wx["accuracy"] < 0.4 and wx["total"] >= 3:
                    lines.append(f"  └ 初传{wx['wuxing']}五行: {wx['accuracy']*100:.0f}% ({wx['correct']}/{wx['total']})")
            lines.append("")

    # ── 可执行洞察 ──
    insights = generate_insights(predictions)
    if insights:
        critical = [i for i in insights if i["priority"] == "critical"]
        high = [i for i in insights if i["priority"] == "high"]
        warning = [i for i in insights if i["priority"] == "warning"]
        good = [i for i in insights if i["priority"] == "good"]
        if critical or high or warning:
            lines.append("💡 改进建议")
            lines.append("━" * 55)
            for ins in critical + high + warning:
                tag = "🔴" if ins["priority"] == "critical" else ("🟡" if ins["priority"] == "high" else "⚪")
                lines.append(f"  {tag} [{ins['category']}] {ins['message']}")
            if good:
                lines.append(f"  ──")
                for ins in good[:2]:
                    lines.append(f"  ✅ [{ins['category']}] {ins['message']}")
            lines.append("")

    # ── 账户净值 ──
    portfolio_stats = stat_portfolios()
    lines.append("💰 虚拟账户净值")
    lines.append("━" * 55)
    for s in portfolio_stats:
        if s["status"] == "未初始化":
            lines.append(f"  {s['label']:<18} 未初始化")
            continue
        sign = "+" if s["profit_pct"] >= 0 else ""
        pct_display = f"{sign}{s['profit_pct']}%"
        lines.append(f"  {s['label']:<18} ¥{s['total_value']:<10,.2f}  {pct_display:>8}")
    lines.append("")

    # ── 交易统计 ──
    trade_counts = stat_trade_counts()
    lines.append("🔄 交易统计")
    lines.append("━" * 55)
    for cat in CATEGORY_ORDER:
        tc = trade_counts.get(cat, {})
        lines.append(f"  {CATEGORY_LABELS.get(cat, cat):<18} 买入{tc.get('buy', 0):>3}次 / 卖出{tc.get('sell', 0):>3}次 / 共{tc.get('total', 0)}笔")

    lines.append("")
    lines.append("=" * 55)
    lines.append(f"  报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 55)
    return "\n".join(lines)


def generate_short_report(predictions: list[dict] = None) -> str:
    """生成精简版报告（适合每日自动输出）"""
    if predictions is None:
        data = load_json("stock_predictions.json")
        predictions = data if isinstance(data, list) else (data.get("predictions", []) if data else [])

    reviewed = [p for p in predictions if p.get("actual_result") is not None]
    if not reviewed:
        return "📊 十一分类实验: 暂无已对照数据"

    correct = sum(1 for p in reviewed if _is_correct(p) is True)
    total = len(reviewed)
    acc = correct / total * 100

    cat_stat = stat_by_category(predictions)
    portfolio_stats = stat_portfolios()
    vote_stat = stat_by_vote_consistency(predictions)

    lines = []
    lines.append(f"📊 十一分类实验速报 (共{total}次对照, 准确率{acc:.1f}%)")
    for cat in CATEGORY_ORDER:
        s = cat_stat.get(cat, {})
        if s["total"] > 0:
            lines.append(f"  {s['label']:<18} {s['correct']}/{s['total']} ({s['accuracy']*100:.1f}%)")
    # 全票一致
    if vote_stat:
        full = vote_stat.get("高置信度", {})
        if full["total"] > 0:
            lines.append(f"  高置信度: {full['correct']}/{full['total']} ({full['accuracy']*100:.1f}%)")
    # 账户
    for s in portfolio_stats:
        if s["status"] != "未初始化":
            sign = "+" if s["profit_pct"] >= 0 else ""
            lines.append(f"  {s['label']:<18} ¥{s['total_value']:,.2f} ({sign}{s['profit_pct']}%)")
    # 洞察摘要（只取最重要的）
    insights = generate_insights(predictions)
    critical = [i for i in insights if i["priority"] == "critical"]
    high = [i for i in insights if i["priority"] == "high"]
    if critical:
        lines.append(f"  🔴 {'; '.join(i['message'][:80] for i in critical)}")
    elif high:
        lines.append(f"  🟡 {'; '.join(i['message'][:80] for i in high[:2])}")
    # 策略对比
    try:
        from engine.model_strategy import get_strategy_report
        sr_lines = get_strategy_report().split("\n")
        for sl in sr_lines:
            lines.append(f"  {sl}")
    except Exception:
        pass
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

def save_report():
    """生成报告并保存到文件"""
    report = generate_full_report()
    path = os.path.join(MEMORY_DIR, "accuracy_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    short = generate_short_report()
    print(report)
    print()
    print("=" * 55)
    print(f"  完整报告已保存: {path}")
    print("=" * 55)
    return report, short


if __name__ == "__main__":
    save_report()
