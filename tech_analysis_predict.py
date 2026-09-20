#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日对照 + 周度对比系统
=======================
收盘后：自动保存 实际 vs 六壬 vs ML 三方对照
周五：  汇总整周日度对比表
"""

import json, os, sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

from config import (
    BASE, MEMORY, STOCK_REPORTS as COMPARE_DIR,
    ML_PREDICTIONS as TECH_PRED_FILE,
    get_beijing_now, classify_trend,
)


def daily_save_comparison(date_str=None):
    """每日收盘后保存三方对照（实际+六壬+ML）"""
    if date_str is None:
        date_str = get_beijing_now().strftime("%Y-%m-%d")

    COMPARE_FILE = MEMORY / "daily_compare.json"
    records = []
    if COMPARE_FILE.exists():
        with open(COMPARE_FILE, 'r') as f:
            records = json.load(f)
    if any(r.get('date') == date_str for r in records):
        return

    # 获取实际行情
    actual_trend = None
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000001")
        row = df[df['date'].astype(str) == date_str]
        if not row.empty:
            r = row.iloc[-1]
            actual_trend = classify_trend(float(r['open']), float(r['close']),
                                          float(r['high']), float(r['low']))
    except: pass
    if not actual_trend:
        pred_file = MEMORY / "stock_predictions.json"
        if pred_file.exists():
            with open(pred_file, 'r') as f:
                data = json.load(f)
            preds = data if isinstance(data, list) else data.get("predictions", [])
            for p in preds:
                if p.get('date') == date_str and p.get('actual_details'):
                    try:
                        ad = p['actual_details']
                        if isinstance(ad, dict):
                            c = float(ad.get('change_pct', 0))
                            actual_trend = '涨' if c > 0.5 else '跌' if c < -0.5 else '平'
                        elif isinstance(ad, str):
                            actual_trend = ad  # 直接使用字符串
                    except: pass
                    break
            # 如果还没找到，直接用actual_result
            if not actual_trend:
                for p in preds:
                    if p.get('date') == date_str and p.get('actual_result'):
                        actual_trend = p['actual_result']
                        break
    if not actual_trend: return

    # 六壬预测
    lr_trend = '?'
    pred_file = MEMORY / "stock_predictions.json"
    if pred_file.exists():
        with open(pred_file, 'r') as f:
            data = json.load(f)
        preds = data if isinstance(data, list) else data.get("predictions", [])
        lp = next((p for p in preds if p.get('date') == date_str
                   and p.get('category') == 'fixed_time'), None)
        if not lp: lp = next((p for p in preds if p.get('date') == date_str), None)
        if lp: lr_trend = lp.get('trend_prediction', '?')

    # ML预测
    ml_trend = '?'
    if TECH_PRED_FILE.exists():
        with open(TECH_PRED_FILE, 'r') as f:
            tech_preds = json.load(f)
        mp = next((p for p in tech_preds if p.get('date') == date_str), None)
        if mp: ml_trend = mp.get('trend_prediction', '?')

    def is_correct(pred, actual):
        if pred == '?' or not actual: return None
        if pred == actual: return True
        up, down = ['涨'], ['跌']
        if any(w in str(pred) for w in up) and any(w in str(actual) for w in up): return True
        if any(w in str(pred) for w in down) and any(w in str(actual) for w in down): return True
        return False

    record = {
        "date": date_str, "actual": actual_trend,
        "liuren_trend": lr_trend, "liuren_correct": is_correct(lr_trend, actual_trend),
        "ml_trend": ml_trend, "ml_correct": is_correct(ml_trend, actual_trend),
        "saved_at": get_beijing_now().isoformat(),
    }
    records.append(record)
    with open(COMPARE_FILE, 'w') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def generate_weekly_compare():
    """周度对比报告（汇总已入库的每日对照数据）"""
    print("=" * 64)
    print("  WEEKLY COMPARE: Liu Ren vs ML Ensemble")
    print("=" * 64)

    COMPARE_FILE = MEMORY / "daily_compare.json"
    if not COMPARE_FILE.exists():
        print("  No data yet, wait for daily close")
        return None

    with open(COMPARE_FILE, 'r') as f:
        records = json.load(f)

    today = get_beijing_now().date()
    monday = today - timedelta(days=today.weekday())
    week_dates = {(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)}
    week_recs = [r for r in records if r['date'] in week_dates]
    if not week_recs:
        print("  No data this week"); return None

    lr_h, lr_m, lr_t, ml_h, ml_m, ml_t = 0, 0, 0, 0, 0, 0

    print()
    print("  Week: {} ~ {}".format(min(week_dates), max(week_dates)))
    print("  Records: {}/5 days\n".format(len(week_recs)))
    print("  {:<12} {:<8} {:<12} {:<6} {:<12} {:<6} {:<6}".format(
        "Date","Actual","LiuRen","Hit?","ML","Hit?","Winner"))
    print("  " + "-" * 62)

    for r in sorted(week_recs, key=lambda x: x['date']):
        lo, mo = r.get('liuren_correct'), r.get('ml_correct')
        if lo is not None: lr_t += 1; lr_h += lo; lr_m += (not lo)
        if mo is not None: ml_t += 1; ml_h += mo; ml_m += (not mo)
        li = "Y" if lo else ("N" if lo is False else "?")
        mi = "Y" if mo else ("N" if mo is False else "?")
        if lo and not mo: w = "LiuRen"
        elif mo and not lo: w = "ML"
        elif lo and mo: w = "Both"
        elif lo is False and mo is False: w = "None"
        else: w = "-"
        print("  {:<12} {:<8} {:<12} {:<6} {:<12} {:<6} {:<6}".format(
            r['date'], r.get('actual','?'), r.get('liuren_trend','?'),
            li, r.get('ml_trend','?'), mi, w))

    lr_a = lr_h / max(1, lr_t) * 100
    ml_a = ml_h / max(1, ml_t) * 100
    print("\n  " + "=" * 62)
    print("  LiuRen: {}/{} = {:.0f}%".format(lr_h, lr_t, lr_a))
    print("  ML:     {}/{} = {:.0f}%".format(ml_h, ml_t, ml_a))
    if lr_a > ml_a:
        w_str = "🏆 LiuRen WINS! (+{:.0f}%)".format(lr_a - ml_a)
    elif ml_a > lr_a:
        w_str = "🏆 ML WINS! (+{:.0f}%)".format(ml_a - lr_a)
    else:
        w_str = "🤝 TIE"
    print("\n  {}".format(w_str))

    result = {
        "week": "{}~{}".format(min(week_dates), max(week_dates)),
        "liuren": {"hit": lr_h, "miss": lr_m, "accuracy": round(lr_a, 1)},
        "ml": {"hit": ml_h, "miss": ml_m, "accuracy": round(ml_a, 1)},
        "winner": "liuren" if lr_a > ml_a else ("ml" if ml_a > lr_a else "tie"),
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = COMPARE_DIR / "weekly_compare_{}.json".format(ts)
    with open(path, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\n  Report: {}".format(path))
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--compare", action="store_true", help="Weekly report")
    p.add_argument("--daily", type=str, help="Manual daily save YYYY-MM-DD")
    a = p.parse_args()
    if a.compare:
        generate_weekly_compare()
    elif a.daily:
        daily_save_comparison(a.daily)
        print("Done: {} saved".format(a.daily))
    else:
        print("Usage: python tech_analysis_predict.py --compare | --daily YYYY-MM-DD")


if __name__ == "__main__":
    main()
