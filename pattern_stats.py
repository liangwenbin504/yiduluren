#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬特征统计分析器 v1.0
======================
P2-7: 拱格 vs 预测准确率统计
P2-9: 天将吉凶 vs 实际涨跌率统计

用法:
  from pattern_stats import PatternStatsAnalyzer
  psa = PatternStatsAnalyzer()
  psa.analyze_all()  # 分析所有历史预测的拱格/天将规律
  print(psa.report())
"""

import json, os
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(__file__).parent
PRED_FILE = BASE / "_memory" / "stock_predictions.json"
STATS_FILE = BASE / "_memory" / "pattern_accuracy_stats.json"

# 吉将/凶将
JI_JIANG = {'贵人', '青龙', '六合', '太常', '太阴', '天后'}
XIONG_JIANG = {'白虎', '玄武', '螣蛇', '天空', '勾陈', '朱雀'}

# 拱格名称（与 yidu_liuren_yaojue 一致）
GONG_NAMES = ['拱干格', '两贵引从格', '拱支格', '干支拱贵格', '干支拱日禄格',
              '三合拱贵格', '三合拱禄格', '三合拱马格']

# 高级课格
ADVANCED_NAMES = ['朝天格', '归垣格', '罗纹格', '龙德课']


def _load_json(path, default=None):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


class PatternStatsAnalyzer:
    """六壬模式统计分析器"""

    def __init__(self):
        self.predictions = _load_json(PRED_FILE, [])
        self.stats = _load_json(STATS_FILE, {
            "gong_stats": {},      # {拱格名: {total, correct}}
            "tianjiang_stats": {}, # {天将名: {total, correct, trend_dist}}
            "keti_stats": {},      # {课体: {total, correct}}
            "sanchuan_stats": {},  # {初传地支: {total, correct}}
            "combined_summary": [], # 汇总
        })

    def collect_from_predictions(self):
        """从所有已完成预测中收集数据"""
        completed = [p for p in self.predictions
                     if p.get("actual_result") and p.get("status") == "completed"]

        for p in completed:
            actual = p.get("actual_result", "")
            trend = p.get("trend_prediction", "")
            is_correct = trend == actual

            # 拱格统计
            gong_patterns = p.get("gong_patterns", [])
            for gp in gong_patterns:
                if isinstance(gp, dict):
                    name = gp.get("name", "")
                    matched = gp.get("matched", False)
                elif isinstance(gp, str):
                    name = gp
                    matched = True
                else:
                    continue
                if not matched:
                    continue
                if name not in self.stats["gong_stats"]:
                    self.stats["gong_stats"][name] = {"total": 0, "correct": 0,
                                                       "trends": {}}
                self.stats["gong_stats"][name]["total"] += 1
                if is_correct:
                    self.stats["gong_stats"][name]["correct"] += 1
                # 趋势分布
                td = self.stats["gong_stats"][name].setdefault("trends", {})
                td[actual] = td.get(actual, 0) + 1

            # 天将统计
            tianjiang_map = p.get("tianjiang_map", {})
            sanchuan_tj = p.get("sanchuan_tianjiang", [])
            for tj in sanchuan_tj:
                if not tj:
                    continue
                name = tj if isinstance(tj, str) else str(tj)
                if name not in self.stats["tianjiang_stats"]:
                    self.stats["tianjiang_stats"][name] = {"total": 0, "correct": 0,
                                                            "trends": {}, "type": ""}
                ss = self.stats["tianjiang_stats"][name]
                ss["total"] += 1
                if is_correct:
                    ss["correct"] += 1
                ss["trends"][actual] = ss["trends"].get(actual, 0) + 1
                if name in JI_JIANG:
                    ss["type"] = "吉将"
                elif name in XIONG_JIANG:
                    ss["type"] = "凶将"
                else:
                    ss["type"] = "其他"

            # 课体统计
            keti = p.get("keti", "")
            if keti:
                if keti not in self.stats["keti_stats"]:
                    self.stats["keti_stats"][keti] = {"total": 0, "correct": 0}
                self.stats["keti_stats"][keti]["total"] += 1
                if is_correct:
                    self.stats["keti_stats"][keti]["correct"] += 1

            # 三传地支统计
            sanchuan = p.get("sanchuan", [])
            for i, zhi in enumerate(sanchuan[:1]):  # 只统计初传
                if not zhi:
                    continue
                if zhi not in self.stats["sanchuan_stats"]:
                    self.stats["sanchuan_stats"][zhi] = {"total": 0, "correct": 0}
                self.stats["sanchuan_stats"][zhi]["total"] += 1
                if is_correct:
                    self.stats["sanchuan_stats"][zhi]["correct"] += 1

    def analyze_all(self) -> dict:
        """完整分析并保存"""
        self.collect_from_predictions()

        # 汇总
        summary = {
            "gong_top": self._top_patterns("gong_stats"),
            "tianjiang_top": self._top_patterns("tianjiang_stats"),
            "keti_top": self._top_patterns("keti_stats"),
            "sanchuan_top": self._top_patterns("sanchuan_stats"),
            "ji_vs_xiong": self._ji_xiong_summary(),
        }

        self.stats["combined_summary"] = summary

        # 保存
        import os
        tmp = str(STATS_FILE) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(STATS_FILE))

        return summary

    def _top_patterns(self, key: str, min_samples: int = 2) -> list:
        """获取top N模式"""
        d = self.stats.get(key, {})
        items = []
        for name, stat in d.items():
            total = stat.get("total", 0)
            correct = stat.get("correct", 0)
            if total >= min_samples:
                items.append({
                    "name": name,
                    "total": total,
                    "correct": correct,
                    "accuracy": round(correct / total, 3),
                })
        items.sort(key=lambda x: -x["accuracy"])
        return items[:8]

    def _ji_xiong_summary(self) -> dict:
        """吉将 vs 凶将 汇总"""
        d = self.stats.get("tianjiang_stats", {})
        ji_total = ji_correct = 0
        xiong_total = xiong_correct = 0
        for name, stat in d.items():
            if stat.get("type") == "吉将":
                ji_total += stat["total"]
                ji_correct += stat["correct"]
            elif stat.get("type") == "凶将":
                xiong_total += stat["total"]
                xiong_correct += stat["correct"]

        return {
            "吉将": {"total": ji_total, "correct": ji_correct,
                     "accuracy": round(ji_correct / max(ji_total, 1), 3)},
            "凶将": {"total": xiong_total, "correct": xiong_correct,
                     "accuracy": round(xiong_correct / max(xiong_total, 1), 3)},
        }

    def report(self) -> str:
        """生成中文统计报告"""
        if not self.stats.get("combined_summary"):
            self.analyze_all()

        s = self.stats["combined_summary"]
        lines = ["=" * 60]
        lines.append("  六壬模式预测力统计分析")
        lines.append("=" * 60)

        # 拱格
        lines.append("\n📐 拱格 vs 预测准确率:")
        for item in s.get("gong_top", [])[:5]:
            bar = "█" * int(item["accuracy"] * 20)
            lines.append(f"  {item['name']:<12} {item['accuracy']:.0%} {bar} ({item['correct']}/{item['total']})")
        if not s.get("gong_top"):
            lines.append("  (数据不足)")

        # 天将
        lines.append("\n👼 天将吉凶 vs 预测准确率:")
        jx = s.get("ji_vs_xiong", {})
        for k, v in jx.items():
            lines.append(f"  {k}: {v['accuracy']:.0%} ({v['correct']}/{v['total']})")

        for item in s.get("tianjiang_top", [])[:5]:
            lines.append(f"  {item['name']:<8} {item['accuracy']:.0%} ({item['correct']}/{item['total']})")

        # 课体
        lines.append("\n📚 课体 vs 预测准确率:")
        for item in s.get("keti_top", [])[:5]:
            lines.append(f"  {item['name']:<10} {item['accuracy']:.0%} ({item['correct']}/{item['total']})")

        # 初传
        lines.append("\n🔮 初传地支 vs 预测准确率:")
        for item in s.get("sanchuan_top", [])[:5]:
            lines.append(f"  {item['name']:<8} {item['accuracy']:.0%} ({item['correct']}/{item['total']})")

        return "\n".join(lines)


# ── 便捷函数 ──

def analyze_and_report() -> str:
    """一键分析并生成报告"""
    psa = PatternStatsAnalyzer()
    psa.analyze_all()
    return psa.report()


if __name__ == "__main__":
    print(analyze_and_report())
