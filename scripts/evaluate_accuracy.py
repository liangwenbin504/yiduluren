"""
股票预测准确率评估脚本
评估训练集中各案例的预测准确率，生成统计报告
"""

import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_stock_cases():
    """加载股票训练案例"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cases_file = os.path.join(base_dir, "data", "stock_training_cases.json")
    if not os.path.exists(cases_file):
        print(f"股票案例文件不存在: {cases_file}")
        return []
    with open(cases_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_accuracy(cases: list) -> dict:
    """评估预测准确率"""
    total = len(cases)
    if total == 0:
        return {"error": "无案例可评估"}

    has_actual = [c for c in cases if c.get("actual_trend")]
    verified = [c for c in has_actual if c.get("is_correct", False)]
    unverified = [c for c in cases if not c.get("actual_trend")]
    auto_gen = [c for c in cases if c.get("auto_generated", False)]

    correct_count = len(verified)
    total_verified = len(has_actual)

    accuracy = (correct_count / total_verified * 100) if total_verified > 0 else 0

    trend_stats = Counter()
    trend_correct = Counter()
    for c in has_actual:
        pred = c.get("trend_prediction", "")
        trend_stats[pred] += 1
        if c.get("is_correct", False):
            trend_correct[pred] += 1

    trend_accuracy = {}
    for trend, count in trend_stats.items():
        trend_accuracy[trend] = {
            "total": count,
            "correct": trend_correct.get(trend, 0),
            "accuracy": round(trend_correct.get(trend, 0) / count * 100, 1)
        }

    source_stats = defaultdict(list)
    for c in has_actual:
        src = c.get("source", "未知")
        source_stats[src].append(c.get("is_correct", False))

    source_accuracy = {}
    for src, results in source_stats.items():
        source_accuracy[src] = {
            "total": len(results),
            "correct": sum(results),
            "accuracy": round(sum(results) / len(results) * 100, 1)
        }

    confidence_stats = defaultdict(list)
    for c in has_actual:
        conf = c.get("confidence", "low")
        confidence_stats[conf].append(c.get("is_correct", False))

    confidence_accuracy = {}
    for conf, results in confidence_stats.items():
        confidence_accuracy[conf] = {
            "total": len(results),
            "correct": sum(results),
            "accuracy": round(sum(results) / len(results) * 100, 1)
        }

    return {
        "评估时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "总案例数": total,
        "已验证案例数": total_verified,
        "未验证案例数": len(unverified),
        "自动采集案例数": len(auto_gen),
        "正确预测数": correct_count,
        "错误预测数": total_verified - correct_count,
        "整体准确率": round(accuracy, 1),
        "按方向准确率": trend_accuracy,
        "按来源准确率": source_accuracy,
        "按置信度准确率": confidence_accuracy
    }


def print_report(report: dict):
    """打印评估报告"""
    if "error" in report:
        print(f"⚠️ {report['error']}")
        return

    print(f"\n{'='*50}")
    print(f"📊 大六壬股票预测准确率评估报告")
    print(f"{'='*50}")
    print(f"评估时间：{report['评估时间']}")
    print(f"总案例数：{report['总案例数']}")
    print(f"已验证案例：{report['已验证案例数']}")
    print(f"未验证案例：{report['未验证案例数']}")
    print(f"自动采集案例：{report['自动采集案例数']}")
    print()
    print(f"🎯 整体准确率：{report['整体准确率']}%")
    print(f"  正确：{report['正确预测数']}  |  错误：{report['错误预测数']}")
    print()

    print(f"{'─'*50}")
    print(f"按方向准确率：")
    print(f"{'─'*50}")
    for trend, stats in sorted(report['按方向准确率'].items()):
        bar = "█" * int(stats['accuracy'] / 5) + "░" * (20 - int(stats['accuracy'] / 5))
        print(f"  {trend:<6} {stats['correct']:>2}/{stats['total']:<2} {bar} {stats['accuracy']}%")

    print()
    print(f"{'─'*50}")
    print(f"按来源准确率：")
    print(f"{'─'*50}")
    for src, stats in sorted(report['按来源准确率'].items()):
        bar = "█" * int(stats['accuracy'] / 5) + "░" * (20 - int(stats['accuracy'] / 5))
        print(f"  {src:<16} {stats['correct']:>2}/{stats['total']:<2} {bar} {stats['accuracy']}%")

    print()
    print(f"{'─'*50}")
    print(f"按置信度准确率：")
    print(f"{'─'*50}")
    for conf, stats in sorted(report['按置信度准确率'].items()):
        bar = "█" * int(stats['accuracy'] / 5) + "░" * (20 - int(stats['accuracy'] / 5))
        print(f"  {conf:<8} {stats['correct']:>2}/{stats['total']:<2} {bar} {stats['accuracy']}%")

    print(f"{'='*50}")
    print()

    total_verified = report['已验证案例数']
    accuracy = report['整体准确率']
    if total_verified >= 20:
        if accuracy >= 75:
            level = "🟢 良好"
        elif accuracy >= 60:
            level = "🟡 一般"
        else:
            level = "🔴 需改进"
        print(f"综合评级：{level}（基于{total_verified}个验证案例）")
    else:
        print(f"⏳ 验证案例不足20个，继续积累数据...")


def save_report(report: dict):
    """保存报告到文件"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_dir = os.path.join(base_dir, "data")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "accuracy_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告已保存到 {report_file}")


def update_case_verification(case_id: str, actual_trend: str):
    """手动更新案例验证结果"""
    cases = load_stock_cases()
    for case in cases:
        if case["id"] == case_id:
            case["actual_trend"] = actual_trend
            case["is_correct"] = case["trend_prediction"] == actual_trend
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cases_file = os.path.join(base_dir, "data", "stock_training_cases.json")
            with open(cases_file, 'w', encoding='utf-8') as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
            print(f"案例 {case_id} 已更新：预测={case['trend_prediction']}，实际={actual_trend}，正确={case['is_correct']}")
            return True
    print(f"未找到案例 {case_id}")
    return False


if __name__ == "__main__":
    cases = load_stock_cases()
    if not cases:
        print("⚠️ 未找到股票训练案例，请先运行 collect_stock_training_data.py")
        sys.exit(1)

    report = evaluate_accuracy(cases)
    print_report(report)
    save_report(report)
