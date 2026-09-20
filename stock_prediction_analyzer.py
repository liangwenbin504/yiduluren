#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测根因分析 + 训练反馈系统
================================
对每条预测进行深度根因分析：
  - 六壬推理是否有误？（课体/三传/天将/五行/六亲）
  - 时辰选择是否有误？
  - 实际行情中哪些信号被模型忽略/误判？

产出：
  1. 根因分析报告（每条预测逐一诊断）
  2. 训练增强数据（正确的→正例强化，错误的→负例教训）
  3. 策略优化建议（按课体/时辰/天将维度）
"""

import json, os, sys
from datetime import datetime
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
PRED_FILE = os.path.join(BASE, "_memory", "stock_predictions.json")

# ── 行情→趋势映射 ──
TREND_FROM_CHANGE = {
    "大涨": "涨", "涨": "涨", "小涨": "震荡偏涨",
    "大跌": "跌", "跌": "跌", "小跌": "震荡偏跌",
    "平": "平",
}

# ── 课体吉凶倾向表 ──
KETI_BIAS = {
    "重审课": {"倾向": "先抑后扬", "股市": "早盘震荡午后反弹"},
    "元首课": {"倾向": "趋势明确", "股市": "单边行情概率大"},
    "知一课": {"倾向": "比用竞争", "股市": "多空拉锯"},
    "涉害课": {"倾向": "多方博弈", "股市": "剧烈波动"},
    "遥克课": {"倾向": "外因主导", "股市": "受外部消息影响"},
    "昴星课": {"倾向": "暗昧不明", "股市": "方向不明"},
    "别责课": {"倾向": "另辟蹊径", "股市": "非主流走势"},
    "八专课": {"倾向": "专一", "股市": "趋势持续"},
    "伏吟课": {"倾向": "迟滞", "股市": "横盘震荡"},
    "反吟课": {"倾向": "反复", "股市": "剧烈反转"},
    "铸印课": {"倾向": "大吉", "股市": "强势上涨"},
    "斫轮课": {"倾向": "成器", "股市": "稳步上扬"},
    "润下课": {"倾向": "流动下行", "股市": "下跌或资金流出"},
    "炎上课": {"倾向": "向上", "股市": "上涨"},
}

# ── 三传天将吉凶 ──
TIANJIANG_JIXIONG = {
    "贵人": "吉", "青龙": "吉", "六合": "吉", "太常": "吉", "太阴": "吉", "天后": "吉",
    "螣蛇": "凶", "朱雀": "凶", "勾陈": "凶", "白虎": "凶", "玄武": "凶", "天空": "凶",
}


class StockPredictionAnalyzer:
    """股票预测根因分析器"""

    def __init__(self):
        with open(PRED_FILE, 'r', encoding='utf-8') as f:
            self.predictions = json.load(f)
        self.analyzed = []

    def _safe_rc(self, pred, key, default=""):
        rc = pred.get("reasoning_chain", {})
        if isinstance(rc, dict):
            return rc.get(key, default)
        return default

    def analyze_single(self, pred):
        """逐条深度分析"""
        date = pred.get("date", "?")
        trend_pred = pred.get("trend_prediction", "?")
        trend_actual = pred.get("actual_trend_calculated", "?")
        match = pred.get("trend_match")
        rizhu = pred.get("rizhu", "?")
        keti = pred.get("keti", "?")
        sanchuan_tj = pred.get("sanchuan_tianjiang", [])
        shi_chen = pred.get("shi_chen", "?")
        yue_jiang = pred.get("yue_jiang", "?")
        jixiong = pred.get("jixiong", "?")

        # ── 根因分析 ──
        rc = pred.get("reasoning_chain", {})
        analysis = {
            "date": date,
            "prediction": trend_pred,
            "actual": trend_actual,
            "match": match,
            "rizhu": rizhu,
            "keti": keti,
            "shi_chen": shi_chen,
            "root_causes": [],
            "lessons": [],
            "training_weight": 1.0,
        }

        # 1. 课时分析：时辰是否合适？
        gan = rizhu[0] if len(rizhu) >= 1 else ""
        if shi_chen:
            # 简单检查：已时(9-11)和午时(11-13)是交易活跃时段
            if shi_chen in ["巳", "午"]:
                analysis["root_causes"].append({
                    "type": "时辰分析",
                    "detail": f"占时{shi_chen}时在交易活跃时段，课象应更能反映盘中博弈",
                    "impact": "正面" if match else "中性",
                })
            elif shi_chen in ["未", "申"]:
                analysis["root_causes"].append({
                    "type": "时辰分析",
                    "detail": f"占时{shi_chen}时在午后，课象偏重尾盘走势",
                    "impact": "信息量不足" if not match else "精准",
                })

        # 2. 课体分析
        if keti and keti in KETI_BIAS:
            bias = KETI_BIAS[keti]
            # 检查预测是否与课体倾向一致
            pred_up = any(w in trend_pred for w in ["涨", "涨)"])
            pred_down = any(w in trend_pred for w in ["跌", "跌)"])
            keti_bull = any(w in str(bias) for w in ["涨", "上扬", "吉"])
            keti_bear = any(w in str(bias) for w in ["跌", "下行", "凶"])

            if match is False:
                if (keti_bull and pred_down) or (keti_bear and pred_up):
                    analysis["root_causes"].append({
                        "type": "课体误判",
                        "detail": f"{keti}倾向{bias['倾向']}，但预测为{trend_pred}，与课体本义矛盾",
                        "impact": "关键错误",
                    })
                    analysis["training_weight"] = 1.5  # 加重训练权重
            elif match is True:
                analysis["root_causes"].append({
                    "type": "课体正确",
                    "detail": f"{keti}倾向{bias['倾向']}，预测{trend_pred}与课体吻合",
                    "impact": "正面验证",
                })

        # 3. 三传天将吉凶分析
        jx_sequence = []
        for stj in sanchuan_tj[:3]:
            for jiang_name, jx in TIANJIANG_JIXIONG.items():
                if jiang_name in str(stj):
                    jx_sequence.append(jx)
                    break
            else:
                jx_sequence.append("?")

        if len(jx_sequence) == 3:
            pattern = "→".join(jx_sequence)
            # 吉→吉→吉 = 全吉
            # 凶→吉→吉 = 先凶后吉
            # 吉→凶→凶 = 先吉后凶
            ji_count = sum(1 for j in jx_sequence if j == "吉")
            xiong_count = sum(1 for j in jx_sequence if j == "凶")

            if trend_pred in ["涨"] and ji_count >= 2:
                analysis["root_causes"].append({
                    "type": "三传天将",
                    "detail": f"三传天将={pattern}，吉多凶少，预测涨合理",
                    "impact": "合理" if match else "信号失效",
                })
            elif trend_pred in ["跌"] and xiong_count >= 2:
                analysis["root_causes"].append({
                    "type": "三传天将",
                    "detail": f"三传天将={pattern}，凶多吉少，预测跌合理",
                    "impact": "合理" if match else "信号失效",
                })
            elif "先跌后涨" in trend_pred and jx_sequence[0] == "凶":
                analysis["root_causes"].append({
                    "type": "三传天将",
                    "detail": f"三传天将={pattern}，初传凶符合先跌判断",
                    "impact": "局部正确" if match else "细节偏差",
                })

        # 4. 教训提取
        if match is False:
            analysis["lessons"].append({
                "type": "失败教训",
                "detail": f"预测{trend_pred}，实际{trend_actual}。课体={keti}，时辰={shi_chen}",
                "fix": self._suggest_fix(pred),
            })
        elif match is True:
            analysis["lessons"].append({
                "type": "成功经验",
                "detail": f"预测{trend_pred}准确命中。课体={keti}提供了有效信号",
                "reinforce": f"课体{keti}的股市映射有效，可在同类课体中增加置信度",
            })

        self.analyzed.append(analysis)
        return analysis

    def _suggest_fix(self, pred):
        """根据失败案例建议修正"""
        suggestions = []
        keti = pred.get("keti", "")
        trend_pred = pred.get("trend_prediction", "")
        trend_actual = pred.get("actual_trend_calculated", "")

        # 如果是平盘但预测了方向，建议增加平盘判断
        if trend_actual in ["平", "震荡偏涨", "震荡偏跌"] and trend_pred in ["涨", "跌"]:
            suggestions.append("当日波动<0.3%时为平盘，避免强行判断方向")
        elif trend_actual in ["涨"] and "跌" in trend_pred:
            suggestions.append(f"课体{keti}在上涨日被误判，检查课体吉凶映射权重")
        elif trend_actual in ["跌"] and "涨" in trend_pred:
            suggestions.append(f"课体{keti}在下跌日被误判，检查空头信号是否被忽略")

        return suggestions[0] if suggestions else "需人工复核"

    def dimension_analysis(self):
        """按维度统计准确率"""
        dims = defaultdict(lambda: {"correct": 0, "wrong": 0, "total": 0})

        for pred in self.predictions:
            match = pred.get("trend_match")
            if match is None:
                continue

            # 课体维度
            keti = pred.get("keti", "未知")
            dims[f"课体_{keti}"]["total"] += 1
            if match:
                dims[f"课体_{keti}"]["correct"] += 1
            else:
                dims[f"课体_{keti}"]["wrong"] += 1

            # 时辰维度
            sc = pred.get("shi_chen", "?")
            dims[f"时辰_{sc}"]["total"] += 1
            if match:
                dims[f"时辰_{sc}"]["correct"] += 1
            else:
                dims[f"时辰_{sc}"]["wrong"] += 1

            # 三传首将维度
            stj = pred.get("sanchuan_tianjiang", [])
            if stj:
                first_jiang = stj[0] if stj else "?"
                dims[f"初传_{first_jiang}"]["total"] += 1
                if match:
                    dims[f"初传_{first_jiang}"]["correct"] += 1
                else:
                    dims[f"初传_{first_jiang}"]["wrong"] += 1

            # 日干维度
            rizhu = pred.get("rizhu", "?")
            gan = rizhu[0] if len(rizhu) >= 1 else "?"
            dims[f"日干_{gan}"]["total"] += 1
            if match:
                dims[f"日干_{gan}"]["correct"] += 1
            else:
                dims[f"日干_{gan}"]["wrong"] += 1

        # 只保留有数据的
        result = {}
        for k, v in dims.items():
            if v["total"] >= 1:
                v["accuracy"] = round(v["correct"] / v["total"], 3)
                result[k] = dict(v)

        return result

    def generate_training_insights(self):
        """生成训练增强数据"""
        insights = []

        for pred in self.predictions:
            match = pred.get("trend_match")
            if match is None:
                continue

            trend_pred = pred.get("trend_prediction", "?")
            trend_actual = pred.get("actual_trend_calculated", "?")
            keti = pred.get("keti", "")
            rizhu = pred.get("rizhu", "")
            rc = pred.get("reasoning_chain", {})

            # 正例：强化课体-趋势映射
            if match is True:
                insights.append({
                    "type": "positive_reinforcement",
                    "weight": 1.0,
                    "instruction": f"已知课体{keti}，日柱{rizhu}，正确预测趋势为{trend_pred}",
                    "input": f"课体={keti}，日柱={rizhu}，三传={'→'.join(pred.get('sanchuan',[]))}",
                    "output": f"趋势={trend_pred}，判断依据：{str(rc.get('课体',''))[:150]}",
                })

            # 负例：纠正错误映射
            if match is False:
                insights.append({
                    "type": "negative_correction",
                    "weight": 1.5,
                    "instruction": f"以下是错误预测案例，请学习正确判断",
                    "input": f"课体={keti}，日柱={rizhu}，三传={'→'.join(pred.get('sanchuan',[]))}",
                    "output": f"实际趋势={trend_actual}（非{trend_pred}）。关键差异：预测未充分考虑{self._get_diff_reason(pred)}",
                })

        return insights

    def _get_diff_reason(self, pred):
        """提取预测偏差原因"""
        trend_pred = pred.get("trend_prediction", "")
        trend_actual = pred.get("actual_trend_calculated", "")
        change = pred.get("actual_details", {}).get("change_pct", 0)

        reasons = []
        try:
            c = float(change)
        except:
            c = 0

        if abs(c) < 0.3:
            reasons.append(f"日振幅仅{c}%，属于平盘")
        if "跌" in trend_pred and c > 0:
            reasons.append("看跌信号被大盘上涨覆盖")
        if "涨" in trend_pred and c < 0:
            reasons.append("看涨信号被大盘下跌覆盖")
        if "先" in trend_pred and abs(c) < 1:
            reasons.append(f"预测复杂走势但实际为单边{c}%")

        return "；".join(reasons) if reasons else "市场整体走势"

    def save_report(self):
        """保存分析报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 逐条分析
        for pred in self.predictions:
            if pred.get("trend_match") is not None:
                self.analyze_single(pred)

        # 维度统计
        dims = self.dimension_analysis()

        # 训练数据
        training_insights = self.generate_training_insights()

        report = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_analyzed": len(self.analyzed),
                "correct": sum(1 for a in self.analyzed if a["match"] is True),
                "wrong": sum(1 for a in self.analyzed if a["match"] is False),
                "accuracy": round(
                    sum(1 for a in self.analyzed if a["match"] is True) / max(1, len(self.analyzed)), 3
                ),
            },
            "per_case_analysis": self.analyzed,
            "dimension_stats": dims,
            "training_insights": training_insights,
            "strategy_recommendations": self._generate_recommendations(dims),
        }

        # 保存
        path = os.path.join(BASE, f"stock_analysis_report_{timestamp}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 保存训练增强数据
        train_path = os.path.join(BASE, "_memory", "stock_training_insights.json")
        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump({"insights": training_insights, "updated_at": datetime.now().isoformat()},
                     f, ensure_ascii=False, indent=2)

        return report, path, train_path

    def _generate_recommendations(self, dims):
        """生成策略优化建议"""
        recs = []

        # 课体建议
        keti_dims = {k: v for k, v in dims.items() if k.startswith("课体_")}
        worst_keti = sorted(keti_dims.items(), key=lambda x: x[1]["accuracy"])
        if worst_keti:
            worst = worst_keti[0]
            if worst[1]["total"] >= 2 and worst[1]["accuracy"] < 0.5:
                recs.append({
                    "target": worst[0],
                    "action": f"降低{worst[0]}课体的看涨权重，增加平盘/震荡判断概率",
                    "evidence": f"{worst[1]['total']}次预测中仅{worst[1]['correct']}次正确",
                })

        # 时辰建议
        sc_dims = {k: v for k, v in dims.items() if k.startswith("时辰_")}
        best_sc = sorted(sc_dims.items(), key=lambda x: x[1]["accuracy"], reverse=True)
        if best_sc:
            best = best_sc[0]
            recs.append({
                "target": best[0],
                "action": f"增加{best[0]}时课预测权重，该时辰准确率最高",
                "evidence": f"准确率{best[1]['accuracy']:.0%} ({best[1]['correct']}/{best[1]['total']})",
            })

        # 低波动日建议
        recs.append({
            "target": "system_prompt",
            "action": "当日振幅<0.5%时，优先输出'平'或'震荡偏涨/偏跌'，避免强行判断方向",
            "evidence": "5/4和5/5振幅仅0.11%，预测方向全部错误",
        })

        return recs

    def print_report(self, report):
        """打印分析报告"""
        s = report["summary"]
        print("=" * 60)
        print("  📊 股票预测根因分析报告")
        print("=" * 60)
        print(f"  分析: {s['total_analyzed']} 条 | 准确: {s['correct']} | 失误: {s['wrong']} | {s['accuracy']:.0%}")
        print()

        # 逐条展示
        for a in self.analyzed:
            icon = "✅" if a["match"] else "❌"
            print(f"  {icon} {a['date']} | 预测={a['prediction']:<10} → 实际={a['actual']:<10}")
            for rc in a["root_causes"]:
                print(f"     [{rc['type']}] {rc['detail']}")
            for l in a["lessons"]:
                t = l.get("fix") or l.get("reinforce") or l["detail"]
                print(f"     📝 {l['type']}: {t[:100]}")
            print()

        # 策略建议
        print("=" * 60)
        print("  🎯 策略优化建议")
        print("=" * 60)
        for i, r in enumerate(report["strategy_recommendations"]):
            print(f"  {i+1}. [{r['target']}] {r['action']}")
            print(f"     证据: {r['evidence']}")

        print(f"\n  分析报告: stock_analysis_report_*.json")
        print(f"  训练数据: _memory/stock_training_insights.json")


if __name__ == "__main__":
    analyzer = StockPredictionAnalyzer()
    report, rp, tp = analyzer.save_report()
    analyzer.print_report(report)
