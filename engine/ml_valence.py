# -*- coding: utf-8 -*-
"""股票域 valence 权重 · 机器学习重标定（真正的 ML 路线）
================================================
把六壬解盘产出的各 valence/信号组（collect_signals 的 signed 贡献）作为特征，
用股票标签（独立市场标签）训练逻辑回归 / 直方图梯度提升，重新标定权重/符号。
- pred_offset=0 : 当日盘（D 盘 -> D 标签）
- pred_offset=1 : 次日盘（D-1 盘 -> D 标签，领式）
- label_mode='intraday' : y=1 if close>open
- label_mode='nextret'   : y=1 if close_D > close_{D-1}（次日收益）

诚实评估：expanding-window walk-forward（绝不打乱时序），朴素基线 55.3%，
留 2025-2026 作 holdout。复用 collect_signals（关 caishen，保留六亲/stock valence）。
"""
import os, sys, json, math
from collections import defaultdict
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import regime_backtest as rb
import engine.judgment_fusion as jf
from liuren_20d_engine import get_liuren_20d_signal

# 固定特征列（六壬 valence/信号组的聚合 signed 贡献）
FEATURE_COLS = ['keti', 'liuqin', 'wangshuai', 'kongwang', 'tianjiang',
                'stock_ba_sha', 'stock_shen_sha', 'stock_qiucai', 'bifa']


def build_feature_row(r):
    """把 collect_signals 的各组 signed 贡献聚合成定长特征向量。"""
    sigs = jf.collect_signals(r)
    agg = defaultdict(float)
    for name, mag, sign, conf in sigs:
        agg[name] += (float(mag) if sign else -float(mag))
    return [agg.get(c, 0.0) for c in FEATURE_COLS]


def build_dataset(pred_offset=0, label_mode='intraday'):
    series = rb.parse_index()
    charts = {d: get_liuren_20d_signal(d, "午") for d, _ in series}
    dates, X, y, valid = [], [], [], []
    for i, (date, (op, cl)) in enumerate(series):
        if pred_offset != 0:
            j = i - pred_offset
            if j < 0:
                valid.append(False); dates.append(date)
                X.append([0.0] * len(FEATURE_COLS)); y.append(0); continue
            r = charts[series[j][0]]
        else:
            r = charts[date]
        row = build_feature_row(r)
        if label_mode == 'intraday':
            yv = 1 if cl > op else 0
        else:  # nextret: D 收 vs D-1 收
            prev_cl = series[i - 1][1][1] if i > 0 else None   # [1][1] 才是 cl
            if prev_cl is None:
                valid.append(False); dates.append(date); X.append(row); y.append(0); continue
            yv = 1 if cl > prev_cl else 0
        X.append(row); y.append(yv); valid.append(True); dates.append(date)
    return dates, np.array(X, dtype=float), np.array(y, dtype=int), valid


def _wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _binom_p(k, n, p0):
    if n == 0: return 1.0
    se = math.sqrt(n * p0 * (1 - p0))
    if se == 0: return 1.0
    z = (k - n * p0) / se
    return math.erfc(abs(z) / math.sqrt(2))


def walkforward(X, y, valid, dates, model_kind='lr',
                test_years=range(2011, 2025), holdout_years=(2025, 2026)):
    from sklearn.preprocessing import StandardScaler
    if model_kind == 'lr':
        from sklearn.linear_model import LogisticRegression
        def make(): return LogisticRegression(C=1.0, max_iter=3000, random_state=0)
    else:
        from sklearn.ensemble import HistGradientBoostingClassifier
        def make(): return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                                         max_depth=3, random_state=0)
    from sklearn.metrics import roc_auc_score
    idx = [i for i in range(len(dates)) if valid[i]]
    yr = lambda d: int(d[:4])
    folds, yt_all, yp_all, yp_prob_all = [], [], [], []
    for ty in test_years:
        tr = [i for i in idx if yr(dates[i]) < ty]
        te = [i for i in idx if yr(dates[i]) == ty]
        if not te:
            continue
        Xtr, ytr = X[tr], y[tr]; Xte, yte = X[te], y[te]
        sc = StandardScaler().fit(Xtr)
        clf = make(); clf.fit(sc.transform(Xtr), ytr)
        p = clf.predict(sc.transform(Xte))
        proba = clf.predict_proba(sc.transform(Xte))[:, 1]
        acc = float((p == yte).mean())
        naive = float(yte.mean())
        brier = float(((proba - yte) ** 2).mean())
        try:
            auc = float(roc_auc_score(yte, proba))
        except ValueError:
            auc = float('nan')
        folds.append({"test_year": ty, "n": len(te), "acc": acc, "naive": naive,
                      "brier": brier, "auc": auc})
        yt_all.extend(yte.tolist()); yp_all.extend(p.tolist()); yp_prob_all.extend(proba.tolist())
    # 聚合 OOS
    n = len(yt_all); correct = sum(1 for a, b in zip(yt_all, yp_all) if a == b)
    acc = correct / n if n else 0.0
    proba = np.array(yp_prob_all); yt = np.array(yt_all)
    brier = float(((proba - yt) ** 2).mean()) if n else float('nan')
    try:
        auc = float(roc_auc_score(yt, proba))
    except ValueError:
        auc = float('nan')
    # 全量系数（2005-2024 训练，展示重标定后的 valence 权重）
    tr_full = [i for i in idx if yr(dates[i]) not in holdout_years]
    sc = StandardScaler().fit(X[tr_full])
    clf = make(); clf.fit(sc.transform(X[tr_full]), y[tr_full])
    if model_kind == 'lr':
        coefs = {c: float(w) for c, w in zip(FEATURE_COLS, clf.coef_[0])}
    else:
        coefs = {c: None for c in FEATURE_COLS}
    return {
        "model": model_kind, "n_oos": n, "acc": acc,
        "ci95": list(_wilson(correct, n)), "p_vs50": _binom_p(correct, n, 0.5),
        "p_vs_naive": _binom_p(correct, n, 0.5532), "brier": brier, "auc": auc,
        "folds": folds, "coefs": coefs,
    }


def run_all():
    out = {}
    specs = [
        ("ml_sameday_intraday", 0, "intraday"),
        ("ml_nextday_intraday", 1, "intraday"),
        ("ml_nextday_nextret", 1, "nextret"),
    ]
    for tag, po, lm in specs:
        print(f"== 构建数据集 {tag} (pred_offset={po}, label={lm}) ==")
        dates, X, y, valid = build_dataset(pred_offset=po, label_mode=lm)
        up = int(y[valid].sum()); tot = int(sum(valid))
        print(f"   有效 {tot} 日, 涨={up}({up/tot:.1%}) 跌={tot-up}")
        out[tag] = {
            "pred_offset": po, "label_mode": lm,
            "lr": walkforward(X, y, valid, dates, 'lr'),
            "hgb": walkforward(X, y, valid, dates, 'hgb'),
        }
    return out


if __name__ == "__main__":
    jf.DISABLE_CAISHEN = True
    os.environ.pop("DISABLE_LIUQIN", None)
    os.environ.pop("DISABLE_STOCK_VALENCE", None)
    res = run_all()
    print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
