#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈回路引擎 v1.0 (Feedback Loop Engine)
========================================
桥接择日系统与预测系统，实现闭环反馈。

功能:
  P1-4: 择日质量 → 预测置信度关联
  P1-5: 训练数据闭环收集（自动采集 + 去重）
  P1-6: ML反馈双向读取（预测时读取权重，对照后更新权重）

用法:
  from feedback_loop import FeedbackLoop
  fb = FeedbackLoop()
  # 预测前: fb.get_zeri_confidence(date) → 根据择日质量调整置信度
  # 预测后: fb.record_result(prediction) → 记录结果+更新权重+采集训练案例
"""

import json, os, sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
DATA = BASE / "data"

# ── 文件路径 ──
PRED_FILE = MEMORY / "stock_predictions.json"
COMPARE_FILE = MEMORY / "daily_compare.json"
ZERI_STATS_FILE = MEMORY / "zeri_accuracy_stats.json"
TRAINING_FILE = DATA / "stock_training_cases.json"


def _load_json(path, default=None):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def _save_json(path, data):
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, str(path))


class FeedbackLoop:
    """反馈回路管理器"""

    def __init__(self):
        self.stats = _load_json(ZERI_STATS_FILE, {
            "high_zeri": {"total": 0, "correct": 0},
            "mid_zeri": {"total": 0, "correct": 0},
            "low_zeri": {"total": 0, "correct": 0},
            "records": [],
        })

    # ═══════════════════════════════════════════
    # P1-4: 择日质量 → 预测置信度
    # ═══════════════════════════════════════════

    def get_zeri_confidence(self, zeri_score: float) -> dict:
        """
        根据择日质量和历史统计，返回置信度调整建议

        返回: {"adjustment": float, "reason": str, "historical_acc": float}
        """
        # 历史准确率
        high = self.stats.get("high_zeri", {})
        mid = self.stats.get("mid_zeri", {})
        low = self.stats.get("low_zeri", {})

        high_acc = high.get("correct", 0) / max(high.get("total", 1), 1)
        mid_acc = mid.get("correct", 0) / max(mid.get("total", 1), 1)
        low_acc = low.get("correct", 0) / max(low.get("total", 1), 1)

        # 当前择日分对应的历史准确率
        if zeri_score >= 75:
            bucket = "high_zeri"
            hist_acc = high_acc
        elif zeri_score >= 60:
            bucket = "mid_zeri"
            hist_acc = mid_acc
        else:
            bucket = "low_zeri"
            hist_acc = low_acc

        # 置信度调整
        if hist_acc > 0.6 and high.get("total", 0) >= 5:
            adjustment = +0.10
            reason = f"高择日分日历史准确率{hist_acc:.0%}，上调置信度"
        elif hist_acc < 0.4 and high.get("total", 0) >= 5:
            adjustment = -0.10
            reason = f"低择日分日历史准确率{hist_acc:.0%}，下调置信度"
        else:
            adjustment = 0
            reason = "历史数据不足或准确率中性"

        return {
            "adjustment": adjustment,
            "reason": reason,
            "historical_acc": round(hist_acc, 3),
            "bucket": bucket,
            "bucket_samples": self.stats.get(bucket, {}).get("total", 0),
        }

    # ═══════════════════════════════════════════
    # P1-5: 训练数据闭环收集
    # ═══════════════════════════════════════════

    def collect_training_case(self, prediction: dict) -> bool:
        """
        从一条已完成的预测中自动收集训练案例

        prediction需包含: date, rizhu, sanchuan, trend_prediction, actual_result
        """
        actual = prediction.get("actual_result")
        if not actual:
            return False

        trend = prediction.get("trend_prediction", "")
        is_correct = trend == actual
        pred_id = prediction.get("id", "")

        # 去重检查
        existing = _load_json(TRAINING_FILE, [])
        for case in existing:
            if pred_id and pred_id in case.get("source", ""):
                return False

        # 构建训练案例
        case = {
            "id": f"CASE-STOCK-{len(existing)+1:03d}",
            "date": prediction.get("date", ""),
            "rizhu": prediction.get("rizhu", ""),
            "sanchuan": prediction.get("sanchuan", []),
            "keti": prediction.get("keti", ""),
            "trend_prediction": trend,
            "actual_result": actual,
            "is_correct": is_correct,
            "zeri_score": prediction.get("zeri_score", 0),
            "source": f"auto_collect {pred_id}",
            "collected_at": datetime.now().isoformat(),
        }

        existing.append(case)
        _save_json(TRAINING_FILE, existing)
        return True

    def batch_collect_from_predictions(self) -> dict:
        """从stock_predictions.json批量收集所有已完成预测"""
        preds = _load_json(PRED_FILE, [])
        completed = [p for p in preds if p.get("actual_result") and p.get("status") == "completed"]

        collected = 0
        for p in completed:
            if self.collect_training_case(p):
                collected += 1

        return {"total_available": len(completed), "collected": collected}

    # ═══════════════════════════════════════════
    # P1-6: ML反馈双向读取
    # ═══════════════════════════════════════════

    def record_result(self, prediction: dict) -> dict:
        """
        记录预测结果并触发完整反馈回路:
        1. 更新温度权重
        2. 更新择日-准确率统计
        3. 收集训练案例
        4. 更新历史对照

        返回: 反馈摘要
        """
        actual = prediction.get("actual_result", "")
        trend = prediction.get("trend_prediction", "")
        zeri_score = prediction.get("zeri_score", 0)
        is_correct = trend == actual

        # 1. 更新温度权重
        try:
            from engine.online_learner import record_prediction_entry, update_weights
            record_prediction_entry(prediction)
            update_weights()
        except Exception as e:
            print(f"  [权重更新异常] {e}")

        # 2. 更新择日-准确率统计
        if zeri_score >= 75:
            bucket = "high_zeri"
        elif zeri_score >= 60:
            bucket = "mid_zeri"
        else:
            bucket = "low_zeri"

        if bucket not in self.stats:
            self.stats[bucket] = {"total": 0, "correct": 0}
        self.stats[bucket]["total"] += 1
        if is_correct:
            self.stats[bucket]["correct"] += 1

        # 记录详细信息
        self.stats.setdefault("records", []).append({
            "date": prediction.get("date", ""),
            "zeri_score": zeri_score,
            "bucket": bucket,
            "trend": trend,
            "actual": actual,
            "correct": is_correct,
        })
        if len(self.stats["records"]) > 200:
            self.stats["records"] = self.stats["records"][-200:]

        _save_json(ZERI_STATS_FILE, self.stats)

        # 3. 收集训练案例
        collected = self.collect_training_case(prediction)

        # 4. 更新历史对照
        self._update_daily_compare(prediction)

        # 生成报告
        conf_info = self.get_zeri_confidence(zeri_score)

        return {
            "is_correct": is_correct,
            "zeri_bucket": bucket,
            "zeri_confidence_adj": conf_info["adjustment"],
            "training_collected": collected,
            "bucket_stats": {
                "high": self._bucket_accuracy("high_zeri"),
                "mid": self._bucket_accuracy("mid_zeri"),
                "low": self._bucket_accuracy("low_zeri"),
            },
        }

    def _bucket_accuracy(self, bucket: str) -> dict:
        b = self.stats.get(bucket, {"total": 0, "correct": 0})
        total = b.get("total", 0)
        return {
            "total": total,
            "correct": b.get("correct", 0),
            "accuracy": round(b.get("correct", 0) / max(total, 1), 3),
        }

    def _update_daily_compare(self, prediction: dict):
        """更新每日对照文件"""
        d = prediction.get("date", "")
        entry = {
            "date": d,
            "trend_prediction": prediction.get("trend_prediction", ""),
            "actual": prediction.get("actual_result", ""),
            "zeri_score": prediction.get("zeri_score", 0),
            "correct": prediction.get("trend_prediction") == prediction.get("actual_result"),
        }

        compare = _load_json(COMPARE_FILE, [])
        if not isinstance(compare, list):
            compare = []
        # 替换同日记录
        compare = [c for c in compare if c.get("date") != d]
        compare.append(entry)
        _save_json(COMPARE_FILE, compare)

    def get_stats_report(self) -> str:
        """生成择日-准确率统计报告"""
        lines = ["📊 择日分 vs 预测准确率"]
        lines.append(f"  高择日分(≥75): {self._bucket_accuracy('high_zeri')}")
        lines.append(f"  中择日分(60-74): {self._bucket_accuracy('mid_zeri')}")
        lines.append(f"  低择日分(<60): {self._bucket_accuracy('low_zeri')}")

        records = self.stats.get("records", [])
        if len(records) >= 10:
            recent = records[-30:]
            correct = sum(1 for r in recent if r.get("correct"))
            lines.append(f"  近30次准确率: {correct}/{len(recent)} ({correct/len(recent):.0%})")

        return "\n".join(lines)


# ── 全局单例 ──
_feedback_loop = None


def get_feedback_loop() -> FeedbackLoop:
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = FeedbackLoop()
    return _feedback_loop
