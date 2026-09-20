"""
多温度投票 vs 多模型集成 — 策略对比引擎

功能：
1. 追踪两种策略的历史准确率
2. 自动推荐当前最优策略
3. 生成对比分析报告

策略定义：
  多温度投票 (multi_temp)：
    单个模型 + 3个不同temperature值 → 投票
    当前模型: deepseek-chat / temps: [0.05, 0.1, 0.2]

  多模型集成 (multi_model)：
    2个不同模型 + 固定temperature → 投票
    模型A: deepseek-chat / 模型B: gpt-4o-mini / temp: 0.1
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRATEGY_FILE = os.path.join(BASE, "_memory", "strategy_stats.json")

PRIMARY_MODEL = "deepseek-chat"
ALT_MODEL = "openai/gpt-4o-mini"

DEFAULT_STRATEGIES = {
    "multi_temp": {
        "label": "多温度投票",
        "description": "deepseek-chat + [0.05, 0.1, 0.2]",
        "total": 0,
        "correct": 0,
        "accuracy": 0,
    },
    "multi_model": {
        "label": "多模型集成",
        "description": "deepseek-chat + gpt-4o-mini",
        "total": 0,
        "correct": 0,
        "accuracy": 0,
    },
}


def _load_stats() -> dict:
    """加载策略统计"""
    if not os.path.exists(STRATEGY_FILE):
        return dict(DEFAULT_STRATEGIES)
    try:
        with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in DEFAULT_STRATEGIES:
            if k not in data:
                data[k] = dict(DEFAULT_STRATEGIES[k])
        return data
    except Exception:
        return dict(DEFAULT_STRATEGIES)


def _save_stats(stats: dict) -> None:
    """保存策略统计"""
    tmp = STRATEGY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STRATEGY_FILE)


def record_strategy_result(strategy: str, is_correct: bool) -> None:
    """
    记录一次策略执行结果

    参数：
        strategy: "multi_temp" 或 "multi_model"
        is_correct: 是否预测正确
    """
    stats = _load_stats()
    if strategy not in stats:
        stats[strategy] = dict(DEFAULT_STRATEGIES[strategy])

    stats[strategy]["total"] += 1
    if is_correct:
        stats[strategy]["correct"] += 1

    total = stats[strategy]["total"]
    correct = stats[strategy]["correct"]
    stats[strategy]["accuracy"] = round(correct / total, 3) if total > 0 else 0

    _save_stats(stats)


def batch_record_from_predictions(predictions: list[dict]) -> int:
    """
    从预测记录中批量提取策略结果

    prediction_entry 中含 method 字段：
      "two_stage_voting" -> multi_temp
      "multi_model" -> multi_model
    """
    completed = [p for p in predictions
                 if p.get("actual_result") and p.get("status") == "completed"]
    count = 0
    for p in completed:
        method = p.get("method", "")
        is_correct = p.get("actual_result") == p.get("trend_prediction")
        if method == "two_stage_voting":
            record_strategy_result("multi_temp", is_correct)
            count += 1
        elif method == "multi_model":
            record_strategy_result("multi_model", is_correct)
            count += 1
    return count


def compare_strategies() -> dict:
    """生成策略对比报告"""
    stats = _load_stats()
    mt = stats.get("multi_temp", {})
    mm = stats.get("multi_model", {})

    best = None
    if mt["total"] >= 3 and mm["total"] >= 3:
        if mt["accuracy"] > mm["accuracy"]:
            best = "multi_temp"
        elif mm["accuracy"] > mt["accuracy"]:
            best = "multi_model"
        else:
            best = "tie"
    elif mt["total"] >= 3:
        best = "multi_temp"
    elif mm["total"] >= 3:
        best = "multi_model"
    else:
        best = "insufficient_data"

    decision = ""
    if best == "multi_temp":
        decision = f"推荐使用多温度投票（准确率{mt['accuracy']:.0%} vs {mm['accuracy']:.0%}）"
    elif best == "multi_model":
        decision = f"推荐使用多模型集成（准确率{mm['accuracy']:.0%} vs {mt['accuracy']:.0%}）"
    elif best == "tie":
        decision = "两种策略准确率持平，任选均可"
    elif best == "insufficient_data":
        decision = "数据不足（至少各3条），暂无法推荐"

    return {
        "strategies": {
            "multi_temp": {
                "label": mt["label"],
                "desc": mt["description"],
                "total": mt["total"],
                "correct": mt["correct"],
                "accuracy": mt["accuracy"],
            },
            "multi_model": {
                "label": mm["label"],
                "desc": mm["description"],
                "total": mm["total"],
                "correct": mm["correct"],
                "accuracy": mm["accuracy"],
            },
        },
        "best": best,
        "decision": decision,
    }


def get_recommended_strategy() -> str:
    """
    获取推荐的策略

    返回：
        "multi_temp" 或 "multi_model"
    """
    comparison = compare_strategies()
    if comparison["best"] in ("multi_temp", "multi_model"):
        return comparison["best"]
    return "multi_temp"  # 默认


def get_strategy_report() -> str:
    """生成人类可读的策略对比报告"""
    comp = compare_strategies()
    lines = []
    lines.append("🧠 策略对比")
    lines.append("━" * 55)

    for sid, sinfo in comp["strategies"].items():
        acc_str = f"{sinfo['accuracy']*100:.1f}%" if sinfo["total"] > 0 else "暂无数据"
        lines.append(f"  {sinfo['label']:<14} {sinfo['total']}次/{sinfo['correct']}正确 {acc_str}")
        lines.append(f"  {'':>14} {sinfo['desc']}")

    if comp["decision"]:
        lines.append(f"  ──")
        lines.append(f"  → {comp['decision']}")

    return "\n".join(lines)
