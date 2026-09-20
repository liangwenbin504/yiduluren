#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测日报生成器
==================
每日22:00自动生成，汇总当日所有预测与真实行情对比。

功能：
  1. 汇总所有11类 + 个股预测
  2. 对比真实行情（通过AKShare获取）
  3. 计算命中率、各维度准确率
  4. 生成HTML可视化报表

运行：
  python stock_report_generator.py              # 生成今日报表
  python stock_report_generator.py --date 2026-07-10  # 指定日期
  python stock_report_generator.py --watch      # 启动22:00定时生成
"""

import json, os, sys, time, requests
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict, Counter
from pathlib import Path

from config import (
    BASE, MEMORY, STOCK_REPORTS as REPORTS_DIR,
    STOCK_PREDICTIONS as PRED_FILE, get_beijing_now, classify_trend,
)
from pathlib import Path


def fetch_market_data(target_date=None):
    """获取当日真实行情"""
    if target_date is None:
        target_date = get_beijing_now().date()

    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000001")
        date_str = target_date.strftime("%Y-%m-%d")
        row = df[df['date'] == date_str]
        if not row.empty:
            r = row.iloc[0]
            return {
                "date": date_str,
                "open": float(r['open']),
                "close": float(r['close']),
                "high": float(r['high']),
                "low": float(r['low']),
                "volume": float(r['volume']),
                "change_pct": round((float(r['close']) - float(r['open'])) / float(r['open']) * 100, 2),
                "trend": classify_trend(float(r['open']), float(r['close']), float(r['high']), float(r['low'])),
            }
    except Exception as e:
        pass

    # 回退：从已有预测记录中取
    if PRED_FILE.exists():
        with open(PRED_FILE) as f:
            preds = json.load(f)
        if isinstance(preds, dict):
            preds = preds.get("predictions", preds.get("results", []))
        for p in preds:
            details = p.get("actual_details", {})
            if details and details.get("price"):
                return {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "open": details.get("open", 0),
                    "close": details.get("price", 0),
                    "high": details.get("high", 0),
                    "low": details.get("low", 0),
                    "change_pct": details.get("change_pct", 0),
                    "trend": p.get("actual_trend_calculated", "?"),
                }

    return None



def load_predictions(target_date=None):
    """加载预测数据"""
    if target_date is None:
        target_date = get_beijing_now().date()
    date_str = target_date.strftime("%Y-%m-%d") if isinstance(target_date, (date, datetime)) else target_date

    predictions = []
    if PRED_FILE.exists():
        with open(PRED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_preds = data if isinstance(data, list) else data.get("predictions", [])
        predictions = [p for p in all_preds if str(p.get("date", "")) == str(date_str)]

    # 也加载个股预测
    multi_files = sorted(MEMORY.glob("multi_stock_*.json"))
    for mf in multi_files:
        with open(mf, 'r', encoding='utf-8') as f:
            md = json.load(f)
        if str(md.get("date", "")) == str(date_str):
            for sp in md.get("predictions", []):
                predictions.append({
                    "date": date_str,
                    "category": f"个股_{sp.get('symbol','?')}",
                    "name": sp.get("name", "?"),
                    "trend_prediction": sp.get("trend", "?"),
                    "jixiong": sp.get("jixiong", "?"),
                    "confidence": sp.get("confidence", 0),
                    "source": "multi_stock",
                })

    return predictions


def generate_report(target_date=None):
    """生成日报"""
    if target_date is None:
        target_date = get_beijing_now().date()
    date_str = target_date.strftime("%Y-%m-%d") if isinstance(target_date, (date, datetime)) else str(target_date)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成 {date_str} 股票预测日报...")

    predictions = load_predictions(target_date)
    market = fetch_market_data(target_date)

    if not predictions:
        print(f"  ⚠️ {date_str} 无预测记录")
        return None

    # ── 统计 ──
    cat_stats = defaultdict(lambda: {"count": 0, "correct": 0})
    for p in predictions:
        cat = p.get("category", "其他")
        cat_stats[cat]["count"] += 1
        if p.get("trend_match"):
            cat_stats[cat]["correct"] += 1

    # ── 生成HTML ──
    html = build_html_report(date_str, predictions, market, cat_stats)

    # 保存（始终写入与路由一致的 项目根/stock_reports 目录，确保目录存在）
    report_dir = BASE / "stock_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"stock_report_{date_str}.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 同时保存JSON数据
    json_path = report_dir / f"stock_report_{date_str}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "generated_at": get_beijing_now().isoformat(),
            "market_data": market,
            "predictions": predictions,
            "stats": {k: dict(v) for k, v in cat_stats.items()},
        }, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 报表已生成: {report_path}")
    return str(report_path)


# 类别中英文映射（英文代码 → 中文显示名；未知类别保留原值）
CAT_NAMES = {
    'fixed_time': '固定时辰',
    'ri_gan_pian_cai': '日干偏财',
    'ri_zhi_pian_cai': '日支偏财',
    'ri_gan_shi_shen': '日干食神',
    'ri_zhi_shi_shen': '日支食神',
    'ri_gan_zheng_yin': '日干正印',
    'ri_gan_pian_yin': '日干偏印',
    'ri_zhi_zheng_yin': '日支正印',
    'ri_zhi_pian_yin': '日支偏印',
    'random': '随机课',
    'manual': '人工指定时',
    '_other': '其他',
}


def build_html_report(date_str, predictions, market, cat_stats):
    """构建HTML报表"""

    # 类别中文化（英文代码 → 中文，未知类别保留原值）
    def cn_cat(cat):
        return CAT_NAMES.get(cat, cat)

    # 计算总体统计
    total = len(predictions)
    matched = sum(1 for p in predictions if p.get("trend_match") is not None)
    correct = sum(1 for p in predictions if p.get("trend_match") is True)
    accuracy = correct / max(1, matched) * 100

    # 行情卡片
    market_card = ""
    if market:
        change = market.get("change_pct", 0)
        color = "#ef4444" if change > 0 else "#22c55e" if change < 0 else "#6b7280"
        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
        market_card = f"""
        <div class="market-card">
            <div class="market-title">上证指数</div>
            <div class="market-price">{market.get('close','?')}</div>
            <div class="market-change" style="color:{color}">{arrow}{abs(change):.2f}%</div>
            <div class="market-detail">开{market.get('open','?')} 高{market.get('high','?')} 低{market.get('low','?')}</div>
            <div class="market-trend">趋势: {market.get('trend','?')}</div>
        </div>"""

    # 预测表格
    rows = ""
    for i, p in enumerate(predictions):
        cat = p.get("category", "?")
        name = p.get("name") or cn_cat(cat)
        trend = p.get("trend_prediction", "?")
        jx = p.get("jixiong", "?")
        conf = p.get("confidence", 0)
        match = p.get("trend_match")
        source = p.get("source", "")

        if match is True:
            result_icon = "✅"
            result_class = "hit"
        elif match is False:
            result_icon = "❌"
            result_class = "miss"
        else:
            result_icon = "⏳"
            result_class = "pending"

        conf_bar = f'<div class="conf-bar"><div class="conf-fill" style="width:{conf*100}%"></div></div>'

        rows += f"""
        <tr class="{result_class}">
            <td>{i+1}</td>
            <td>{name[:12]}</td>
            <td><span class="tag">{cn_cat(cat)}</span></td>
            <td><strong>{trend}</strong></td>
            <td>{jx}</td>
            <td>{conf_bar}<span>{conf:.0%}</span></td>
            <td>{result_icon}</td>
            <td><small>{source}</small></td>
        </tr>"""

    # 类别统计
    cat_rows = ""
    for cat, stats in sorted(cat_stats.items()):
        acc = stats['correct'] / max(1, stats['count']) * 100
        cat_rows += f"<tr><td>{cn_cat(cat)}</td><td>{stats['count']}</td><td>{stats['correct']}</td><td>{acc:.0f}%</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>六壬股票预测日报 — {date_str}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Microsoft YaHei',sans-serif; background:#0f172a; color:#e2e8f0; padding:20px; }}
.container {{ max-width:1200px; margin:0 auto; }}
.header {{ text-align:center; padding:30px 0; border-bottom:2px solid #334155; margin-bottom:30px; }}
.header h1 {{ font-size:28px; color:#f8fafc; }}
.header .date {{ color:#94a3b8; margin-top:8px; }}
.market-card {{ background:linear-gradient(135deg,#1e293b,#0f172a); border:1px solid #334155;
    border-radius:16px; padding:24px; text-align:center; margin-bottom:30px; }}
.market-title {{ font-size:14px; color:#94a3b8; }}
.market-price {{ font-size:48px; font-weight:bold; color:#f8fafc; margin:10px 0; }}
.market-change {{ font-size:24px; font-weight:bold; }}
.market-detail {{ color:#64748b; margin-top:8px; }}
.market-trend {{ color:#94a3b8; margin-top:4px; }}
.stats-row {{ display:flex; gap:20px; margin-bottom:30px; flex-wrap:wrap; }}
.stat-card {{ flex:1; min-width:150px; background:#1e293b; border:1px solid #334155;
    border-radius:12px; padding:20px; text-align:center; }}
.stat-value {{ font-size:36px; font-weight:bold; }}
.stat-label {{ color:#94a3b8; margin-top:4px; font-size:14px; }}
.stat-value.green {{ color:#22c55e; }}
.stat-value.red {{ color:#ef4444; }}
.stat-value.blue {{ color:#3b82f6; }}
.section {{ background:#1e293b; border:1px solid #334155; border-radius:12px;
    padding:24px; margin-bottom:20px; }}
.section-title {{ font-size:18px; color:#f8fafc; margin-bottom:16px; border-bottom:1px solid #334155; padding-bottom:8px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; padding:10px 8px; color:#94a3b8; font-size:13px; border-bottom:2px solid #334155; }}
td {{ padding:10px 8px; border-bottom:1px solid #1e293b; font-size:14px; }}
tr:hover {{ background:rgba(59,130,246,0.05); }}
tr.hit {{ background:rgba(34,197,94,0.08); }}
tr.miss {{ background:rgba(239,68,68,0.08); }}
tr.pending {{ opacity:0.6; }}
.tag {{ background:#334155; padding:2px 8px; border-radius:4px; font-size:12px; }}
.conf-bar {{ width:60px; height:6px; background:#334155; border-radius:3px; display:inline-block; margin-right:6px; vertical-align:middle; }}
.conf-fill {{ height:100%; background:linear-gradient(90deg,#3b82f6,#22c55e); border-radius:3px; }}
.footer {{ text-align:center; padding:20px; color:#475569; font-size:12px; margin-top:30px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔮 六壬股票预测日报</h1>
        <div class="date">{date_str} | 生成时间 {get_beijing_now().strftime('%H:%M:%S')}</div>
    </div>

    {market_card}

    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-value blue">{total}</div>
            <div class="stat-label">总预测数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value green">{correct}</div>
            <div class="stat-label">命中</div>
        </div>
        <div class="stat-card">
            <div class="stat-value red">{matched-correct}</div>
            <div class="stat-label">失误</div>
        </div>
        <div class="stat-card">
            <div class="stat-value {'green' if accuracy>=50 else 'red'}">{accuracy:.0f}%</div>
            <div class="stat-label">准确率</div>
        </div>
        <div class="stat-card">
            <div class="stat-value blue">{len(predictions)-matched}</div>
            <div class="stat-label">待对照</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">📋 预测明细</div>
        <table>
            <thead>
                <tr><th>#</th><th>标的</th><th>类别</th><th>预测趋势</th><th>吉凶</th><th>置信度</th><th>结果</th><th>来源</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">📊 各类别统计</div>
        <table>
            <thead><tr><th>类别</th><th>预测数</th><th>命中</th><th>准确率</th></tr></thead>
            <tbody>{cat_rows}</tbody>
        </table>
    </div>

    <div class="footer">
        仪度六壬择日系统 · 股票预测日报 · 自动生成于每日22:00
    </div>
</div>
</body>
</html>"""

    return html


def report_watchdog():
    """22:00定时生成守护"""
    print("=" * 50)
    print("  股票日报守护进程")
    print(f"  启动: {get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  每日22:00自动生成报表")
    print("=" * 50)

    last_date = None
    while True:
        now = get_beijing_now()
        today = now.strftime("%Y-%m-%d")
        hour = now.hour
        minute = now.minute

        # 每天22:00-22:05之间生成
        if hour == 22 and 0 <= minute < 5:
            if today != last_date:
                print(f"\n[{now.strftime('%H:%M:%S')}] ⏰ 到22:00，生成今日报表...")
                generate_report(now.date())
                last_date = today

        time.sleep(30)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="股票预测日报生成器")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--watch", action="store_true", help="启动22:00定时生成守护")
    parser.add_argument("--list", action="store_true", help="列出所有历史报表")
    args = parser.parse_args()

    if args.watch:
        report_watchdog()
        return

    if args.list:
        reports = sorted(REPORTS_DIR.glob("stock_report_*.html"), reverse=True)
        if reports:
            print(f"历史报表 ({len(reports)} 份):")
            for r in reports[:20]:
                size = r.stat().st_size / 1024
                print(f"  {r.name} ({size:.0f}KB)")
            print(f"\n  报表目录: {REPORTS_DIR}")
        else:
            print("暂无报表")
        return

    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    report_path = generate_report(target_date)
    if report_path:
        print(f"\n  查看报表: {report_path}")


if __name__ == "__main__":
    main()
