#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线强化学习器 v2.0
==================
新特性:
  - 动态温度: 不限于0.05/0.1/0.2，自动追踪新出现的温度值
  - EMA衰减: 旧数据指数衰减（半衰期可配置），避免历史数据过度影响
  - 持久化统计: 每次更新自动保存，支持跨会话累计
  - 权重不确定性: 样本少时权重自动降低

工作流程:
  预测时: stage2_results → 加权投票
  对照后: record_result(temperature, trend, actual) → 更新准确率
  定期: update_weights() → 重新计算权重 + EMA衰减
"""

import json, os, math
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_FILE = os.path.join(BASE, "_memory", "temperature_weights.json")

# ── 配置 ──
DEFAULT_TEMPS = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
HALF_LIFE_DAYS = 30          # EMA半衰期（天）
MIN_SAMPLES = 3              # 最少样本数才参与权重计算
WINDOW_DAYS = 90             # 滑动窗口（天），太旧的数据自动清理


def _temp_key(temperature: float) -> str:
    return f"t{temperature}"


def _now_epoch_day() -> int:
    """到今天为止的天数（epoch day）"""
    return int(datetime.now(timezone.utc).timestamp() / 86400)


def load_weights() -> dict:
    """加载温度权重，自动初始化默认温度"""
    if not os.path.exists(WEIGHTS_FILE):
        return _default_weights()

    try:
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_weights()

    # 确保默认温度都存在
    for temp in DEFAULT_TEMPS:
        key = _temp_key(temp)
        if key not in data:
            data[key] = {"total": 0, "correct": 0, "weight": 1.0}

    return data


def _default_weights() -> dict:
    return {
        _temp_key(t): {"total": 0, "correct": 0, "weight": 1.0,
                        "last_seen_day": 0, "history": []}
        for t in DEFAULT_TEMPS
    }


def save_weights(weights: dict) -> None:
    """原子写入权重文件"""
    tmp = WEIGHTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(weights, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, WEIGHTS_FILE)


def record_result(temperature: float, trend: str, actual: str) -> None:
    """
    记录一次预测结果（P1-3增强版）
    - 支持任意温度值（动态追踪）
    - 记录时间戳用于EMA衰减
    - 保存历史记录用于滑动窗口
    """
    weights = load_weights()
    key = _temp_key(temperature)

    if key not in weights:
        weights[key] = {"total": 0, "correct": 0, "weight": 1.0,
                         "last_seen_day": 0, "history": []}

    today = _now_epoch_day()
    weights[key]["total"] += 1
    if trend == actual:
        weights[key]["correct"] += 1
    weights[key]["last_seen_day"] = today

    # 保存历史记录（最近100条）
    history = weights[key].get("history", [])
    history.append({"day": today, "trend": trend, "actual": actual, "correct": trend == actual})
    if len(history) > 100:
        history = history[-100:]
    weights[key]["history"] = history

    save_weights(weights)


def record_prediction_entry(prediction_entry: dict) -> None:
    """从一条完整的预测记录中提取温度结果并记录"""
    actual = prediction_entry.get("actual_result")
    if not actual:
        return

    detail = prediction_entry.get("vote_detail") or prediction_entry.get("stage2_detail")
    if not detail:
        return

    for temp_key, trend in detail.items():
        if temp_key.startswith("t") and trend:
            try:
                temp = float(temp_key[1:])
                record_result(temp, trend, actual)
            except (ValueError, TypeError):
                continue


def update_weights(decay: float = 0.9, use_ema: bool = True) -> dict:
    """
    重新计算所有温度权重（P1-3增强版）

    权重公式:
      accuracy = correct / total
      raw_weight = accuracy / max_accuracy  (归一化)
      if use_ema: weight = decay * old_weight + (1-decay) * raw_weight
      else:       weight = raw_weight

    样本不足时返回默认权重1.0
    """
    weights = load_weights()
    today = _now_epoch_day()

    # 清理过期数据（超过WINDOW_DAYS天）
    for key in list(weights.keys()):
        history = weights[key].get("history", [])
        if history:
            cutoff = today - WINDOW_DAYS
            recent = [h for h in history if h.get("day", 0) >= cutoff]
            if len(recent) < len(history):
                weights[key]["history"] = recent
                weights[key]["total"] = len(recent)
                weights[key]["correct"] = sum(1 for h in recent if h.get("correct"))

    # 计算各温度的准确率
    accuracies = {}
    for key, v in weights.items():
        total = v.get("total", 0)
        correct = v.get("correct", 0)
        if total >= MIN_SAMPLES:
            accuracies[key] = correct / total
        else:
            accuracies[key] = None

    valid = {k: a for k, a in accuracies.items() if a is not None}
    if not valid:
        return weights

    max_acc = max(valid.values()) if valid else 1.0

    for key in weights:
        acc = accuracies.get(key)
        if acc is not None and max_acc > 0:
            raw_weight = max(0.05, acc / max_acc)
        else:
            raw_weight = 1.0

        old_weight = weights[key].get("weight", 1.0)
        if use_ema:
            weights[key]["weight"] = round(decay * old_weight + (1 - decay) * raw_weight, 4)
        else:
            weights[key]["weight"] = round(raw_weight, 4)

        weights[key]["accuracy"] = round(acc, 4) if acc is not None else 0
        weights[key]["samples"] = weights[key].get("total", 0)

    # 更新时间戳
    weights["_last_update_day"] = today
    weights["_total_samples"] = sum(v.get("total", 0) for v in weights.values()
                                     if isinstance(v, dict))

    save_weights(weights)
    return weights


def get_weighted_vote(stage2_results: list) -> dict:
    """
    根据温度权重计算加权投票结果（支持任意温度）

    参数: stage2_results = [(temperature, trend), ...]
    返回: {"涨": 1.5, "跌": 0.8, "winner": "涨", "confidence": 0.65}
    """
    weights = load_weights()
    weighted = {}
    total_weight = 0

    for temp, trend in stage2_results:
        key = _temp_key(temp)
        w = weights.get(key, {}).get("weight", 1.0)
        samples = weights.get(key, {}).get("samples", 0)
        # 样本不足时降低置信度
        if samples < MIN_SAMPLES:
            w *= 0.5
        weighted[trend] = weighted.get(trend, 0) + w
        total_weight += w

    if not weighted:
        return {"winner": "", "confidence": 0, "votes": {}}

    sorted_votes = sorted(weighted.items(), key=lambda x: -x[1])
    winner = sorted_votes[0][0]
    confidence = sorted_votes[0][1] / total_weight if total_weight > 0 else 0

    return {
        "winner": winner,
        "confidence": round(confidence, 3),
        "votes": {k: round(v, 3) for k, v in weighted.items()},
        "total_samples": weights.get("_total_samples", 0),
    }


def get_all_temps() -> list:
    """获取所有已知的温度值（动态）"""
    weights = load_weights()
    temps = []
    for key in weights:
        if key.startswith("t") and key[1:].replace('.', '').isdigit():
            try:
                temps.append(float(key[1:]))
            except ValueError:
                pass
    return sorted(temps)


def get_weight_report() -> str:
    """生成详细权重报告"""
    weights = load_weights()
    all_temps = get_all_temps()
    lines = ["🌡️ 温度权重状态 (v2.0)"]
    lines.append(f"   总样本: {weights.get('_total_samples', 0)}")
    lines.append(f"   活跃温度: {len(all_temps)} 个")

    for temp in sorted(all_temps):
        key = _temp_key(temp)
        v = weights.get(key, {})
        total = v.get("total", 0)
        correct = v.get("correct", 0)
        weight = v.get("weight", 1.0)
        acc = correct / total if total > 0 else 0
        bar = "█" * int(weight * 10)
        lines.append(f"   {key:<8} w={weight:.3f} {bar} acc={acc:.0%} ({correct}/{total})")

    return "\n".join(lines)


# ── 向后兼容 ──

def adjust_vote_result(stage2_results: list) -> dict:
    """向后兼容接口"""
    result = get_weighted_vote(stage2_results)
    return result.get("votes", {})


def get_weighted_winner(stage2_results: list) -> tuple:
    """向后兼容接口"""
    result = get_weighted_vote(stage2_results)
    is_unanimous = result.get("confidence", 0) > 0.8
    return result["winner"], result["votes"], is_unanimous
