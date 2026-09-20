# -*- coding: utf-8 -*-
"""
跨牛熊·扩大回测 (regime backtest)
================================
用真实上证指数(sh000001) 日线 OHLC 作为标签源，对 liuren_20d_engine 做
多年份、跨牛熊的严格方向回测，定位"精准判断引擎"的有效边界。

方法:
  M1  原20d引擎         -> prediction.trend
  M2  融合①②③(无CBR)   -> fuse(去掉 holistic)
  M3  融合+CBR          -> fused_judgment (含综合叙事证据组)
  M4  CBR叙事单独       -> holistic_judgment.trend

标签: actual = 涨 if close > open else 跌  (与 stock_training_clean.json 口径一致)

牛熊分段: 按历史阶段(近似) 标注每个交易日所属周期, 并另算" trailing 120日收益带"。

指标: 覆盖率(非震荡比例) / 决断准确率(committed accuracy) / Brier / Wilson 95%CI /
       二项检验 p值(vs 0.5) / 系统性方向偏置(看跌占比)。
"""
import os, sys, json, glob, math, copy, time
from collections import defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

RAW_CACHE = os.path.join(HERE, "regime_backtest_raw.json")
REPORT = os.path.join(HERE, "regime_backtest_report.json")
MEM_DIR = os.path.join(ROOT, "_memory")

# 受控开关：仅在股票域诚实回测驱动置 True 时，run_engine 才额外记录
# 每日 stock valence 的"理论触发值"（用于覆盖率统计），不影响生产路径。
_CAPTURE_STOCK = False

# ----------------------------------------------------------------------------
# 1) 解析指数日线
# ----------------------------------------------------------------------------
def parse_index():
    rows = {}
    files = sorted(glob.glob(os.path.join(MEM_DIR, "idx_*.txt")))
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("| 20") and not line.startswith("| 19"):
                    continue
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) < 3:
                    continue
                date = cols[0]
                try:
                    op = float(cols[1])
                    cl = float(cols[2])  # 'last' = 收盘
                except ValueError:
                    continue
                rows[date] = (op, cl)
    series = sorted(rows.items())  # 升序
    return series

# ----------------------------------------------------------------------------
# 2) 牛熊周期标注 (近似历史阶段)
# ----------------------------------------------------------------------------
CYCLES = [
    ("2005-2007 大牛市",       "2005-01-01", "2007-10-16"),
    ("2007-2008 金融危机熊市",  "2007-10-17", "2008-11-04"),
    ("2008-2009 四万亿反弹",    "2008-11-05", "2009-08-04"),
    ("2009-2014 漫长震荡熊",    "2009-08-05", "2014-07-21"),
    ("2014-2015 杠杆牛",        "2014-07-22", "2015-06-12"),
    ("2015-2016 股灾",          "2015-06-13", "2016-01-28"),
    ("2016-2018 慢牛",          "2016-01-29", "2018-01-24"),
    ("2018-2019 贸易战熊市",    "2018-01-25", "2019-01-03"),
    ("2019-2021 结构牛",        "2019-01-04", "2021-02-10"),
    ("2021-2024 长期震荡熊",    "2021-02-11", "2024-09-23"),
    ("2024-2026 政策修复",      "2024-09-24", "2026-12-31"),
]

def cycle_of(date):
    for name, s, e in CYCLES:
        if s <= date <= e:
            return name
    return "未分类"

def trailing_regime(series, idx, win=120):
    """用 trailing win 日累计收益带 标注 牛/熊/震荡"""
    if idx < win:
        return "早期(样本不足)"
    c0 = series[idx - win][1][1]
    c1 = series[idx][1][1]
    if c0 <= 0:
        return "震荡"
    ret = (c1 - c0) / c0
    if ret > 0.10:
        return "牛( trailing +%)"
    if ret < -0.10:
        return "熊( trailing -%)"
    return "震荡"

# ----------------------------------------------------------------------------
# 3) 引擎调用 (resume-capable)
# ----------------------------------------------------------------------------
def normalize_trend(t):
    if t is None:
        return "ABSTAIN"
    if "涨" in t and "跌" not in t:
        return "UP"
    if "跌" in t:
        return "DOWN"
    return "ABSTAIN"

def run_engine(series, force=False, pred_offset=0):
    """pred_offset=0: 当天盘预测当天（默认）。
    pred_offset=1: 次日预测——用第 i-1 天的盘局预测第 i 天的涨跌（领式 lead-1）。
    首个交易日(i=0)无更早盘局，标记为 SKIP 并跳过。"""
    cache = {}
    if os.path.exists(RAW_CACHE) and not force:
        try:
            cache = json.load(open(RAW_CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    from liuren_20d_engine import get_liuren_20d_signal
    from engine.judgment_fusion import fuse
    done = set(cache.keys())
    total = len(series)
    out = dict(cache)
    t0 = time.time()
    # 次日预测：预先算好每日盘局，预测第 i 天用第 i-pred_offset 天的盘
    chart_cache = {}
    if pred_offset != 0:
        print(f"  预计算 {len(series)} 日盘局 (pred_offset={pred_offset}) ...")
        for d, _ in series:
            chart_cache[d] = get_liuren_20d_signal(d, "午")
    for i, (date, (op, cl)) in enumerate(series):
        if date in done:
            continue
        try:
            if pred_offset != 0:
                j = i - pred_offset
                if j < 0:
                    out[date] = {"open": op, "close": cl,
                                 "actual": ("UP" if cl > op else "DOWN"),
                                 "M1": "SKIP", "M2": "SKIP", "M3": "SKIP", "M4": "SKIP",
                                 "error": "no_prev_chart"}
                    continue
                r = chart_cache[series[j][0]]
            else:
                r = get_liuren_20d_signal(date, "午")
            pred = r.get("prediction") or {}
            fj = r.get("fused_judgment") or {}
            hj = r.get("holistic_judgment") or {}
            # M2: 去掉 holistic 后重算融合
            r2 = copy.deepcopy(r)
            r2.pop("holistic_judgment", None)
            fj2 = fuse(r2)
            actual = "UP" if cl > op else "DOWN"
            out[date] = {
                "open": op, "close": cl, "actual": actual,
                "M1": normalize_trend(pred.get("trend")),
                "M2": normalize_trend(fj2.get("trend")),
                "M3": normalize_trend(fj.get("trend")),
                "M4": normalize_trend(hj.get("trend")),
                "M3_prob_up": fj.get("prob_up"), "M3_prob_down": fj.get("prob_down"),
                "M3_prob_flat": fj.get("prob_flat"),
                "M2_prob_up": fj2.get("prob_up"), "M2_prob_down": fj2.get("prob_down"),
                "M2_prob_flat": fj2.get("prob_flat"),
                "M3_conf": fj.get("confidence"), "M3_conflict": fj.get("conflict"),
                "error": None,
            }
            if _CAPTURE_STOCK:
                try:
                    from engine.stock_liuren_features import extract_stock_valence
                    sv = extract_stock_valence(r)
                    out[date]["stock_fired"] = {
                        "ba_sha": sv.get("stock_ba_sha") or 0,
                        "shen_sha": sv.get("stock_shen_sha") or 0,
                        "qiucai": sv.get("stock_qiucai") or 0,
                    }
                except Exception:
                    out[date]["stock_fired"] = None
        except Exception as e:
            out[date] = {"open": op, "close": cl, "actual": ("UP" if cl > op else "DOWN"),
                         "M1": "ERR", "M2": "ERR", "M3": "ERR", "M4": "ERR", "error": str(e)[:120]}
        # 增量落盘, 防中断丢进度
        if (i + 1) % 200 == 0:
            json.dump(out, open(RAW_CACHE, "w", encoding="utf-8"))
            el = time.time() - t0
            print(f"  [{i+1}/{total}] {date} 已用 {el:.0f}s  ({(i+1)/el*60:.0f}/min)")
    json.dump(out, open(RAW_CACHE, "w", encoding="utf-8"))
    return out

# ----------------------------------------------------------------------------
# 4) 统计工具
# ----------------------------------------------------------------------------
def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))

def binom_pvalue(k, n):
    """双侧二项检验 vs p0=0.5, 正态近似"""
    if n == 0:
        return 1.0
    se = math.sqrt(n * 0.25)
    if se == 0:
        return 1.0
    z = (k - n * 0.5) / se
    # 双尾 p
    p = math.erfc(abs(z) / math.sqrt(2))
    return p

def brier_from_probs(p_up, p_down, p_flat, actual):
    p_up = p_up or 0.0; p_down = p_down or 0.0; p_flat = p_flat or 0.0
    o_up = 1.0 if actual == "UP" else 0.0
    o_down = 1.0 if actual == "DOWN" else 0.0
    o_flat = 0.0
    return (p_up - o_up) ** 2 + (p_down - o_down) ** 2 + (p_flat - o_flat) ** 2

def method_metrics(rows, key, pkey=None):
    """rows: list of record dict. key=M1/M2/M3/M4. 若 pkey 给则算 Brier(用概率)."""
    n = len(rows)
    committed = 0
    correct = 0
    down_pred = 0
    brier_sum = 0.0
    brier_n = 0
    for r in rows:
        t = r.get(key)
        if t in ("UP", "DOWN"):
            committed += 1
            if t == r["actual"]:
                correct += 1
            if t == "DOWN":
                down_pred += 1
        if pkey:
            pu = r.get(pkey + "_prob_up"); pd = r.get(pkey + "_prob_down"); pf = r.get(pkey + "_prob_flat")
            if pu is not None and pd is not None:
                brier_sum += brier_from_probs(pu, pd, pf, r["actual"])
                brier_n += 1
    acc = correct / committed if committed else 0.0
    lo, hi = wilson_ci(correct, committed)
    pv = binom_pvalue(correct, committed)
    down_rate = down_pred / committed if committed else 0.0
    brier = brier_sum / brier_n if brier_n else None
    return {
        "n": n, "coverage": committed / n if n else 0.0,
        "committed": committed, "correct": correct,
        "accuracy": acc, "ci95": [lo, hi], "p_value": pv,
        "down_bias": down_rate,
        "brier": brier, "brier_n": brier_n,
    }

# ----------------------------------------------------------------------------
# 5) 主流程
# ----------------------------------------------------------------------------
def main(pred_offset=0):
    print("== 解析指数日线 ==")
    series = parse_index()
    print(f"  共 {len(series)} 个交易日, {series[0][0]} ~ {series[-1][0]}")
    print("== 运行引擎 (断点续跑) ==")
    raw = run_engine(series, pred_offset=pred_offset)
    recs = [raw[d] for d, _ in series]
    valid = [r for r in recs if r.get("error") is None and r.get("M1") != "ERR"]
    print(f"  有效记录 {len(valid)} / {len(recs)}")

    methods = [("M1", None), ("M2", "M2"), ("M3", "M3"), ("M4", None)]
    print("\n== 全样本指标 ==")
    overall = {}
    base_down = sum(1 for r in valid if r["actual"] == "DOWN") / len(valid)
    print(f"  实际跌占比(基准) = {base_down:.3f}")
    for mk, pk in methods:
        m = method_metrics(valid, mk, pk)
        overall[mk] = m
        print(f"  {mk}: 覆盖={m['coverage']:.2%} 决断准确率={m['accuracy']:.2%} "
              f"CI=[{m['ci95'][0]:.2%},{m['ci95'][1]:.2%}] p={m['p_value']:.3f} "
              f"看跌偏置={m['down_bias']:.2%} Brier={m['brier'] if m['brier'] else 'NA'}")

    # 分周期
    print("\n== 分牛熊周期 ==")
    by_cycle = defaultdict(list)
    for r, (d, _) in zip(valid, series):
        by_cycle[cycle_of(d)].append(r)
    cycle_report = OrderedDict()
    for name, _, _ in CYCLES + [("未分类", "", "")]:
        if name not in by_cycle:
            continue
        rows = by_cycle[name]
        if not rows:
            continue
        cycle_report[name] = {
            "n": len(rows),
            "actual_down_rate": sum(1 for r in rows if r["actual"] == "DOWN") / len(rows),
            "M3": method_metrics(rows, "M3", "M3"),
            "M1": method_metrics(rows, "M1"),
            "M4": method_metrics(rows, "M4"),
        }
        m3 = cycle_report[name]["M3"]
        print(f"  {name:22s} n={len(rows):4d} 实际跌={cycle_report[name]['actual_down_rate']:.2%} "
              f"M3决断准={m3['accuracy']:.2%}(p={m3['p_value']:.3f}) 覆盖={m3['coverage']:.2%} 看跌偏置={m3['down_bias']:.2%}")

    # 分年份
    print("\n== 分年份 ==")
    by_year = defaultdict(list)
    for r, (d, _) in zip(valid, series):
        by_year[d[:4]].append(r)
    year_report = OrderedDict()
    for y in sorted(by_year):
        rows = by_year[y]
        year_report[y] = {
            "n": len(rows),
            "actual_down_rate": sum(1 for r in rows if r["actual"] == "DOWN") / len(rows),
            "M3": method_metrics(rows, "M3", "M3"),
        }
        m3 = year_report[y]["M3"]
        print(f"  {y} n={len(rows):4d} 实际跌={year_report[y]['actual_down_rate']:.2%} "
              f"M3决断准={m3['accuracy']:.2%}(p={m3['p_value']:.3f}) 覆盖={m3['coverage']:.2%}")

    # trailing 收益带 分段
    print("\n== trailing 120日收益带 分段 ==")
    band_report = defaultdict(list)
    for i, (d, _) in enumerate(series):
        if d not in raw or raw[d].get("error"):
            continue
        band = trailing_regime(series, i, 120)
        band_report[band].append(raw[d])
    band_out = OrderedDict()
    for band in ["牛( trailing +%)", "震荡", "熊( trailing -%)", "早期(样本不足)"]:
        if band not in band_report:
            continue
        rows = band_report[band]
        band_out[band] = {
            "n": len(rows),
            "actual_down_rate": sum(1 for r in rows if r["actual"] == "DOWN") / len(rows),
            "M3": method_metrics(rows, "M3", "M3"),
        }
        m3 = band_out[band]["M3"]
        print(f"  {band:18s} n={len(rows):4d} 实际跌={band_out[band]['actual_down_rate']:.2%} "
              f"M3决断准={m3['accuracy']:.2%}(p={m3['p_value']:.3f}) 看跌偏置={m3['down_bias']:.2%}")

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "source": "上证指数 sh000001 日线 (腾讯自选股)",
        "label_rule": "actual = 涨 if close>open else 跌",
        "shichen": "午",
        "pred_design": ("次日预测(lead-1): 第D-1天盘局 -> 第D天涨跌" if pred_offset
                        else "当天盘->当天涨跌"),
        "pred_offset": pred_offset,
        "date_range": [series[0][0], series[-1][0]],
        "n_total": len(series), "n_valid": len(valid),
        "base_down_rate": base_down,
        "overall": overall,
        "by_cycle": cycle_report,
        "by_year": year_report,
        "by_trailing_band": band_out,
    }
    json.dump(report, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n报告已写: {REPORT}")
    # 结论提示
    m3 = overall["M3"]
    print(f"\n【摘要】M3(融合+CBR): 覆盖{m3['coverage']:.1%} 决断准{m3['accuracy']:.2%} "
          f"(vs 50% p={m3['p_value']:.3f}) 看跌偏置{m3['down_bias']:.1%} Brier={m3['brier']:.3f}")

if __name__ == "__main__":
    main()
