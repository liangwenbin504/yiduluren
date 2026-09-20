# -*- coding: utf-8 -*-
"""
上证指数日线数据增量更新（供 regime_backtest.parse_index / tianji_harness 消费）

背景（2026-09-05 发现）：
  _memory/idx_*.txt 行情数据停在 2026-07-30，导致 tianji_harness 的周期结算全部卡死
  （周期 261 窗口 07-31~08-28 已走完 8 天仍显示"待验证"，因为取不到 period_end 收盘价）。
  数据每停更一天，天机统计就多空转一天 —— 故做成可复用的增量更新脚本。

用法：
  python engine/update_index_data.py            # 增量更新（默认，自动备份）
  python engine/update_index_data.py --check    # 只体检，不写盘
  python engine/update_index_data.py --full     # 全量重抓 2025 至今（忽略本地已有）

数据源：akshare 上证指数 sh000001 日线。
文件格式（与既有 idx_*.txt 保持一致，倒序：新→旧）：
  | date | open | last | high | low | volume | amount | exchange |
  其中 last = 收盘价（parse_index 取 cols[1]=open, cols[2]=last）
"""
import os
import re
import sys
import glob
import shutil
import datetime
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_DIR = os.path.join(ROOT, "_memory")
TARGET = os.path.join(MEM_DIR, "idx_2025_2026.txt")
# 数据源选型（2026-09-05 实测）：
#   ak.index_zh_a_hist（东财）在本机报错 RemoteDisconnected，连不通；
#   ak.stock_zh_index_daily（新浪）可用，但 1.18.60 起不再接受 start_date/end_date，
#   只返回全历史，故在本地按日期过滤。symbol 用 "sh000001"。
SYMBOL = "sh000001"
HEADER = "| date | open | last | high | low | volume | amount | exchange |"
SEP = "| --- | --- | --- | --- | --- | --- | --- | --- |"
FULL_START = "2025-01-01"

ROW_RE = re.compile(r"^\|\s*(20\d{2}-\d{2}-\d{2})\s*\|")


def _backup(path):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak.%s.txt" % (path[:-4] if path.endswith(".txt") else path, stamp)
    shutil.copy2(path, bak)
    return bak


def _read_local(path):
    """返回 {date: (open, last, high, low, volume, amount, exchange)}，跳过表头/空行。"""
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = ROW_RE.match(line)
            if not m:
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) < 3:
                continue
            try:
                op, last = float(cols[1]), float(cols[2])
            except ValueError:
                continue
            high = float(cols[3]) if len(cols) > 3 and cols[3] else op
            low = float(cols[4]) if len(cols) > 4 and cols[4] else op
            vol = cols[5] if len(cols) > 5 else "0"
            amt = cols[6] if len(cols) > 6 else "0"
            exc = cols[7] if len(cols) > 7 else "0"
            rows[cols[0]] = (op, last, high, low, vol, amt, exc)
    return rows


def _fetch(symbol=SYMBOL, start=FULL_START, end=None):
    """抓 akshare 上证指数日线，返回 {date: (open,last,high,low,vol,amt,exc)}。"""
    import akshare as ak

    end = end or datetime.date.today().isoformat()
    df = ak.stock_zh_index_daily(symbol=symbol)      # 新浪源，全历史，无日期参数
    if df is None or df.empty:
        raise RuntimeError("akshare 返回空数据（网络问题或接口变更）")
    df = df[(df.iloc[:, 0].astype(str).str[:10] >= start) &
            (df.iloc[:, 0].astype(str).str[:10] <= end)]
    # 兼容列名：date/open/high/low/close/volume/amount，或中文
    colmap = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc in ("date", "日期"):
            colmap["date"] = c
        elif lc in ("open", "开盘"):
            colmap["open"] = c
        elif lc in ("close", "last", "收盘", "收盘点位"):
            colmap["close"] = c
        elif lc in ("high", "最高"):
            colmap["high"] = c
        elif lc in ("low", "最低"):
            colmap["low"] = c
        elif lc in ("volume", "成交量"):
            colmap["volume"] = c
        elif lc in ("amount", "成交额"):
            colmap["amount"] = c
    out = {}
    for _, r in df.iterrows():
        d = str(r[colmap["date"]])[:10]
        if d < start:
            continue
        try:
            op = float(r[colmap["open"]])
            cl = float(r[colmap["close"]])
        except (ValueError, TypeError):
            continue
        hi = float(r[colmap["high"]]) if "high" in colmap else op
        lo = float(r[colmap["low"]]) if "low" in colmap else op
        vol = r[colmap["volume"]] if "volume" in colmap else 0
        amt = r[colmap["amount"]] if "amount" in colmap else 0
        out[d] = (op, cl, hi, lo, vol, amt, 0)
    return out


def _fmt_num(v):
    """整数型字段去掉 .0，浮点保留原样（与既有文件风格一致）。"""
    if isinstance(v, float) and abs(v - int(v)) < 1e-9:
        return str(int(v))
    return str(v)


def _write(path, rows):
    lines = [HEADER, SEP]
    for d in sorted(rows.keys(), reverse=True):     # 倒序：新 → 旧
        op, last, hi, lo, vol, amt, exc = rows[d]
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            d, _fmt_num(op), _fmt_num(last), _fmt_num(hi), _fmt_num(lo),
            _fmt_num(vol), _fmt_num(amt), _fmt_num(exc)))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def health_check(verbose=True):
    """体检：数据末日 vs 今天，返回 dict。"""
    local = _read_local(TARGET)
    last = max(local.keys()) if local else None
    today = datetime.date.today()
    gap_days = None
    if last:
        ld = datetime.datetime.strptime(last, "%Y-%m-%d").date()
        gap_days = (today - ld).days
    info = {
        "file": TARGET,
        "rows": len(local),
        "last_date": last,
        "today": today.isoformat(),
        "gap_days": gap_days,
    }
    if verbose:
        print("== 行情数据体检 ==")
        print("  文件      : %s" % os.path.basename(TARGET))
        print("  本地条数  : %d" % info["rows"])
        print("  数据末日  : %s" % last)
        print("  今天      : %s" % today.isoformat())
        if gap_days is not None:
            print("  滞后      : %d 天%s" % (gap_days, "  ⚠ 超过 7 天，周期结算会卡死" if gap_days > 7 else "  (正常)"))
    return info


def main():
    ap = argparse.ArgumentParser(description="上证指数日线增量更新")
    ap.add_argument("--check", action="store_true", help="只体检不写盘")
    ap.add_argument("--full", action="store_true", help="全量重抓 2025 至今")
    ap.add_argument("--symbol", default=SYMBOL)
    args = ap.parse_args()

    if args.check:
        health_check()
        return

    before = health_check(verbose=False)
    print("更新前：末日 %s，共 %d 条" % (before["last_date"], before["rows"]))

    local = {} if args.full else _read_local(TARGET)
    fetched = _fetch(symbol=args.symbol,
                     start=FULL_START if args.full else (before["last_date"] or FULL_START))
    print("akshare 抓到：%d 条（区间 %s ~ %s）" % (
        len(fetched), min(fetched) if fetched else "-", max(fetched) if fetched else "-"))

    merged = dict(local)
    added = [d for d in fetched if d not in merged]
    updated = []
    if args.full:
        # 全量模式：以远端为准，刷新历史（数据源口径差异会写进历史行，慎用）
        for d in fetched:
            if d in merged and merged[d][1] != fetched[d][1]:
                updated.append(d)
            merged[d] = fetched[d]
    else:
        # 增量模式（默认）：只补本地缺失的日期，绝不动已有历史行
        for d in added:
            merged[d] = fetched[d]

    # 交叉校验：本地已有日期 vs 远端收盘价，防数据源口径不一致污染历史
    overlap = [d for d in fetched if d in local]
    if overlap:
        diffs = [(d, local[d][1], fetched[d][1]) for d in overlap
                 if abs(local[d][1] - fetched[d][1]) > 0.01]
        print("交叉校验：重叠 %d 日，收盘价不一致 %d 日" % (len(overlap), len(diffs)))
        if diffs:
            worst = max(diffs, key=lambda x: abs(x[1] - x[2]))
            print("  ⚠ 最大差异：%s 本地 %.2f vs 远端 %.2f（差 %.2f）" % (
                worst[0], worst[1], worst[2], worst[2] - worst[1]))
            print("  默认增量模式不会覆盖本地历史行；如需以远端为准请加 --full")

    if not added and not updated:
        print("无需更新：本地已是最新。")
        return

    if os.path.exists(TARGET):
        bak = _backup(TARGET)
        print("已备份 → %s" % os.path.basename(bak))

    _write(TARGET, merged)
    print("已写入 %s：新增 %d 条，修正 %d 条，共 %d 条" % (
        os.path.basename(TARGET), len(added), len(updated), len(merged)))
    if added:
        print("  新增区间：%s ~ %s" % (min(added), max(added)))
    print()
    health_check()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
