#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级机器学习技术分析预测系统 v3.0
===================================
特征工程:
  - 量价特征: 涨跌幅/振幅/量比/换手率
  - 均线特征: MA5/10/20/60/120 偏离度 + 排列状态
  - 动量特征: RSI/MACD/KDJ/CCI/威廉/WR/MOM/ROC
  - 波动特征: ATR/布林带宽/历史波动率
  - 资金流: OBV/MFI/CMF/北向资金
  - 形态特征: K线形态识别(锤子线/吞没/三兵等15种)
  - 时间特征: 星期/月份/月初月末效应
  - 衍生特征: 特征交叉/滞后/滚动统计

模型:
  - XGBoost + LightGBM 集成
  - 滚动窗口训练(500天训练→预测次日→滑动)
  - 概率校准 + 置信度输出

数据源:
  - AKShare: 上证指数日线(3年+历史)
  - AKShare: 北向资金
  - AKShare: 融资融券

用法:
  python ml_stock_predict.py                # 训练+预测
  python ml_stock_predict.py --train-only   # 仅训练
  python ml_stock_predict.py --predict-only # 仅预测
  python ml_stock_predict.py --backtest     # 完整回测评估
"""

import json, os, sys, warnings, joblib
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings('ignore')

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
MODEL_DIR = BASE / "ml_models"
DATA_DIR = BASE / "ml_data"

os.makedirs(MEMORY, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# 1. 数据获取
# ═══════════════════════════════════════════════════════════

def get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def fetch_market_data(years=3):
    """获取上证指数历史日线数据 + 附加数据源"""
    print("  获取上证日线数据...")
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000001")
        df.columns = ['date','open','close','high','low','volume']
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # 只保留最近N年
        cutoff = (get_beijing_now() - timedelta(days=years*365)).date()
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= pd.Timestamp(cutoff)]
        print(f"    获取到 {len(df)} 条日线数据 ({df['date'].min().date()} ~ {df['date'].max().date()})")
        return df
    except Exception as e:
        print(f"    ⚠️ 日线获取失败: {e}")
        return None


def add_north_flow(df):
    """添加北向资金数据（多重API备选）"""
    import akshare as ak
    nf = None

    # 备选1: 沪股通历史资金流向
    try:
        nf_raw = ak.stock_hsgt_hist_em(symbol="沪股通")
        if nf_raw is not None and len(nf_raw) > 0:
            nf = pd.DataFrame()
            nf['date'] = pd.to_datetime(nf_raw['日期'])
            nf['net_flow'] = pd.to_numeric(nf_raw.get('当日成交净买额', 0), errors='coerce').fillna(0)
            # 如果全是NaN，尝试计算
            if nf['net_flow'].sum() == 0:
                buy = pd.to_numeric(nf_raw.get('买入成交额', 0), errors='coerce').fillna(0)
                sell = pd.to_numeric(nf_raw.get('卖出成交额', 0), errors='coerce').fillna(0)
                if buy.sum() > 0:
                    nf['net_flow'] = buy - sell
    except Exception:
        pass

    # 备选2: 北向资金板块排行（提取汇总）
    if nf is None or nf['net_flow'].sum() == 0:
        try:
            board = ak.stock_hsgt_board_rank_em(symbol="沪股通")
            if board is not None and len(board) > 0:
                # 用板块成交额变化作为替代信号
                nf = pd.DataFrame()
                nf['date'] = pd.to_datetime(board.get('日期', pd.Timestamp.now()))
                nf['net_flow'] = pd.to_numeric(board.get('成交额', 0), errors='coerce').fillna(0)
        except Exception:
            pass

    # 备选3: 沪深港通资金流向（新浪）
    if nf is None or nf['net_flow'].sum() == 0:
        try:
            nf_raw2 = ak.stock_hsgt_fund_flow_summary_em()
            if nf_raw2 is not None and len(nf_raw2) > 0:
                nf = pd.DataFrame()
                nf['date'] = pd.to_datetime(nf_raw2.get('日期', pd.Timestamp.now()))
                nf['net_flow'] = pd.to_numeric(nf_raw2.get('北向资金', 0), errors='coerce').fillna(0)
        except Exception:
            pass

    # 合并或降级
    if nf is not None and len(nf) > 0 and nf['net_flow'].sum() != 0:
        nf['date'] = pd.to_datetime(nf['date'])
        df = df.merge(nf, on='date', how='left')
        df['net_flow'] = df['net_flow'].fillna(0)
        valid = (df['net_flow'] != 0).sum()
        print(f"    北向资金已合并 (有效{valid}天)")
    else:
        df['net_flow'] = 0
        # 尝试从ai_sentiment获取资金情绪
        try:
            from ai_sentiment import get_sentiment_signal
            signal = get_sentiment_signal()
            df['net_flow'] = signal * 100  # 映射为近似值
            print(f"    ⚠️ 北向资金API全部失败，使用AI情绪替代 (信号={signal:.2f})")
        except Exception:
            print(f"    ⚠️ 北向资金获取失败，使用默认值0")

    return df


# ═══════════════════════════════════════════════════════════
# 2. 特征工程 — 50+特征
# ═══════════════════════════════════════════════════════════

def engineer_features(df):
    """构建全部技术特征"""
    o, h, l, c, v = df['open'], df['high'], df['low'], df['close'], df['volume']

    features = pd.DataFrame(index=df.index)

    # ── A. 基础量价(8个) ──
    features['returns'] = c.pct_change()
    features['log_returns'] = np.log(c / c.shift(1))
    features['amplitude'] = (h - l) / c.shift(1)
    features['price_position'] = (c - l) / (h - l + 1e-8)
    features['volume_ratio'] = v / v.rolling(20).mean()
    features['volume_change'] = v.pct_change()
    features['gap'] = (o - c.shift(1)) / c.shift(1)
    features['hl_ratio'] = h / l

    # ── B. 均线系统(12个) ──
    for n in [5, 10, 20, 30, 60, 120]:
        ma = c.rolling(n).mean()
        features[f'ma{n}_deviation'] = (c - ma) / ma  # 偏离度
        if n <= 60:
            features[f'ma{n}_slope'] = ma.diff(n) / ma.shift(n)  # 斜率

    # 均线排列
    ma5, ma10, ma20, ma60 = [c.rolling(n).mean() for n in [5, 10, 20, 60]]
    features['ma_bullish'] = ((ma5 > ma10) & (ma10 > ma20) & (ma20 > ma60)).astype(int)
    features['ma_bearish'] = ((ma5 < ma10) & (ma10 < ma20) & (ma20 < ma60)).astype(int)
    features['ma_cross_5_20'] = ((ma5 > ma20) & (ma5.shift(1) <= ma20.shift(1))).astype(int)

    # ── C. 动量指标(18个) ──
    # RSI
    for n in [6, 14, 24]:
        delta = c.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(span=n).mean()
        avg_loss = loss.ewm(span=n).mean()
        rs = avg_gain / (avg_loss + 1e-8)
        features[f'rsi_{n}'] = 100 - (100 / (1 + rs))

    # MACD
    ema12, ema26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
    macd_dif = ema12 - ema26
    macd_dea = macd_dif.ewm(span=9).mean()
    features['macd_dif'] = macd_dif
    features['macd_dea'] = macd_dea
    features['macd_hist'] = 2 * (macd_dif - macd_dea)
    features['macd_cross'] = ((macd_dif > macd_dea) & (macd_dif.shift(1) <= macd_dea.shift(1))).astype(int)

    # KDJ
    low_n, high_n = l.rolling(9).min(), h.rolling(9).max()
    rsv = (c - low_n) / (high_n - low_n + 1e-8) * 100
    features['kdj_k'] = rsv.ewm(com=2).mean()
    features['kdj_d'] = features['kdj_k'].ewm(com=2).mean()
    features['kdj_j'] = 3 * features['kdj_k'] - 2 * features['kdj_d']

    # CCI
    tp = (h + l + c) / 3
    ma_tp = tp.rolling(20).mean()
    md_tp = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean())
    features['cci'] = (tp - ma_tp) / (0.015 * md_tp + 1e-8)

    # WR 威廉指标
    features['wr_14'] = (h.rolling(14).max() - c) / (h.rolling(14).max() - l.rolling(14).min() + 1e-8) * -100

    # MOM 动量
    features['mom_10'] = c - c.shift(10)
    features['roc_10'] = (c - c.shift(10)) / c.shift(10) * 100

    # ── D. 波动特征(8个) ──
    features['atr_14'] = (h - l).rolling(14).mean() / c  # 归一化ATR
    bb_std = c.rolling(20).std()
    bb_ma = c.rolling(20).mean()
    features['boll_width'] = (bb_ma + 2*bb_std - (bb_ma - 2*bb_std)) / bb_ma
    features['boll_position'] = (c - (bb_ma - 2*bb_std)) / (4*bb_std + 1e-8)
    for n in [5, 10, 20]:
        features[f'volatility_{n}'] = features['returns'].rolling(n).std()
    features['high_low_range'] = (h.rolling(20).max() - l.rolling(20).min()) / c

    # ── E. 资金流特征(6个) ──
    # OBV
    obv = (v * ((c > c.shift(1)).astype(int) * 2 - 1)).cumsum()
    features['obv_change'] = obv.pct_change(5)
    features['obv_ma_div'] = (obv - obv.rolling(20).mean()) / obv.rolling(20).std()

    # MFI
    money_flow = tp * v
    pos_flow = money_flow.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_flow = money_flow.where(tp < tp.shift(1), 0).rolling(14).sum()
    features['mfi'] = 100 - (100 / (1 + pos_flow / (neg_flow + 1e-8)))

    # CMF
    clv = ((c - l) - (h - c)) / (h - l + 1e-8)
    features['cmf'] = (clv * v).rolling(20).sum() / v.rolling(20).sum()

    # 北向资金
    if 'net_flow' in df.columns:
        features['north_flow_5d'] = df['net_flow'].rolling(5).mean()
        features['north_flow_20d'] = df['net_flow'].rolling(20).mean()

    # ── F. K线形态(15个) ──
    body = abs(c - o)
    upper_shadow = h - np.maximum(c, o)
    lower_shadow = np.minimum(c, o) - l
    avg_body = body.rolling(20).mean()

    features['doji'] = (body / (h - l + 1e-8) < 0.1).astype(int)
    features['hammer'] = ((lower_shadow > 2*body) & (upper_shadow < 0.3*body) & (body > 0)).astype(int)
    features['shooting_star'] = ((upper_shadow > 2*body) & (lower_shadow < 0.3*body) & (body > 0)).astype(int)
    features['marubozu_bull'] = ((body > 3*avg_body) & (c > o) & (upper_shadow < 0.1*body) & (lower_shadow < 0.1*body)).astype(int)
    features['marubozu_bear'] = ((body > 3*avg_body) & (c < o) & (upper_shadow < 0.1*body) & (lower_shadow < 0.1*body)).astype(int)
    features['engulfing_bull'] = ((c > o) & (c.shift(1) < o.shift(1)) & (o < c.shift(1)) & (c > o.shift(1))).astype(int)
    features['engulfing_bear'] = ((c < o) & (c.shift(1) > o.shift(1)) & (o > c.shift(1)) & (c < o.shift(1))).astype(int)
    features['three_white'] = ((c > o) & (c.shift(1) > o.shift(1)) & (c.shift(2) > o.shift(2))).astype(int)
    features['three_black'] = ((c < o) & (c.shift(1) < o.shift(1)) & (c.shift(2) < o.shift(2))).astype(int)

    # ── G. 时间特征(5个) ──
    features['day_of_week'] = df['date'].dt.dayofweek
    features['month'] = df['date'].dt.month
    features['month_start'] = (df['date'].dt.day <= 3).astype(int)
    features['month_end'] = (df['date'].dt.day >= 28).astype(int)
    features['is_monday'] = (df['date'].dt.dayofweek == 0).astype(int)
    features['is_friday'] = (df['date'].dt.dayofweek == 4).astype(int)

    # ── H. 特征交叉(6个) ──
    features['rsi_vol'] = features['rsi_14'] * features['volume_ratio']
    features['ma_trend'] = features['ma20_deviation'] - features['ma60_deviation']
    features['tech_score'] = (
        features['ma_bullish'] * 2 + features['ma_bearish'] * -2 +
        (features['rsi_14'] - 50) / 25 +
        features['macd_hist'] / c * 1000
    )
    features['volume_price'] = features['returns'] * features['volume_ratio']

    # ── I. 滞后 + 滚动特征(8个) ──
    for lag in [1, 2, 3, 5]:
        features[f'ret_lag_{lag}'] = features['returns'].shift(lag)
    features['ret_ma_5'] = features['returns'].rolling(5).mean()
    features['ret_std_5'] = features['returns'].rolling(5).std()
    features['ret_max_5'] = features['returns'].rolling(5).max()
    features['ret_min_5'] = features['returns'].rolling(5).min()

    # ── J. AI情绪特征（新增） ──
    try:
        from ai_sentiment import get_sentiment_signal, get_market_news_summary
        sentiment = get_sentiment_signal()  # -1.0 ~ +1.0
        features['ai_sentiment'] = sentiment
        # 滞后信号（前N天的情绪）
        if os.path.exists(os.path.join(MEMORY, 'market_sentiment.json')):
            import json
            with open(os.path.join(MEMORY, 'market_sentiment.json'), 'r', encoding='utf-8') as f:
                hist = json.load(f)
            if isinstance(hist, list) and len(hist) >= 3:
                # 将历史情绪信号映射到日期
                sent_map = {}
                for h in hist:
                    sent_map[h.get('date','')] = (h.get('score',0.5)-0.5)*2
                features['ai_sentiment_1d'] = features.index.to_series().apply(
                    lambda i: sent_map.get(str(i.date())[:10], sentiment))
                print(f"    AI情绪特征已添加 (当前信号={sentiment:+.2f})")
    except Exception:
        features['ai_sentiment'] = 0.0
        features['ai_sentiment_1d'] = 0.0

    # ── 标签: 次日涨跌(1=涨, 0=跌) ──
    features['target'] = (features['returns'].shift(-1) > 0).astype(int)
    # 三分类标签: 2=涨>0.5%, 1=平, 0=跌<-0.5%
    next_ret = features['returns'].shift(-1)
    features['target_3class'] = np.where(next_ret > 0.005, 2, np.where(next_ret < -0.005, 0, 1))

    # 删除NaN行
    features = features.iloc[120:]  # 去掉均线计算期的NaN
    features = features.dropna()

    return features


# ═══════════════════════════════════════════════════════════
# 3. 模型训练 + 回测
# ═══════════════════════════════════════════════════════════

def train_evaluate(features, train_days=500):
    """滚动窗口训练+回测评估"""
    from sklearn.metrics import accuracy_score, classification_report

    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

    feature_cols = [c for c in features.columns if not c.startswith('target')]
    n = len(features)
    results = []
    max_results = min(n - train_days, 200)  # 限制最多200条，防内存泄漏

    print(f"\n  滚动窗口回测 (训练{train_days}天→预测1天, 共{n - train_days}轮, 记录{max_results}轮)")

    for i in range(train_days, min(n - 1, train_days + max_results)):
        if (i - train_days) % 100 == 0:
            print(f"    进度: {i-train_days}/{max_results}")

        train = features.iloc[i - train_days:i]
        test = features.iloc[i:i + 2]

        X_train = train[feature_cols].values
        y_train = train['target'].values
        X_test = test[feature_cols].values[:1]
        y_test = test['target'].values[:1]

        # 训练 (HistGradientBoosting + RandomForest 集成)
        import gc
        m_hgb = HistGradientBoostingClassifier(max_iter=100, max_depth=6, learning_rate=0.05,
                                                early_stopping=False, random_state=42)
        m_hgb.fit(X_train, y_train)
        proba = m_hgb.predict_proba(X_test)[0][1]

        m_rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
        m_rf.fit(X_train, y_train)
        proba += m_rf.predict_proba(X_test)[0][1]

        proba /= 2
        pred = 1 if proba > 0.5 else 0

        # 释放模型内存
        del m_hgb, m_rf
        if i % 10 == 0:
            gc.collect()

        results.append({
            'date': features.index[i],
            'actual': y_test[0],
            'pred': pred,
            'proba': proba,
            'correct': int(pred == y_test[0]),
        })

    # 统计
    correct = sum(r['correct'] for r in results)
    total = len(results)
    acc = correct / total * 100 if total > 0 else 0

    print(f"\n  回测完成: {correct}/{total} = {acc:.1f}%")

    # 按年份统计
    yearly = defaultdict(lambda: {'correct': 0, 'total': 0})
    for r in results:
        yr = str(r['date'])[:4]
        yearly[yr]['correct'] += r['correct']
        yearly[yr]['total'] += 1
    print(f"  各年准确率:")
    for yr in sorted(yearly):
        y = yearly[yr]
        print(f"    {yr}: {y['correct']}/{y['total']} = {y['correct']/y['total']*100:.1f}%")

    return results, acc


def train_final_model(features, train_days=500):
    """用最近数据训练最终模型用于今日预测"""
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

    feature_cols = [c for c in features.columns if not c.startswith('target')]

    # 最近500天训练
    train = features.iloc[-train_days:]

    X = train[feature_cols].values
    y = train['target'].values

    # 训练集成模型
    m_hgb = HistGradientBoostingClassifier(max_iter=150, max_depth=6, learning_rate=0.05,
                                            early_stopping=False, random_state=42)
    m_hgb.fit(X, y)

    m_rf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
    m_rf.fit(X, y)

    models = {'hgb': m_hgb, 'rf': m_rf}

    # 保存模型
    for name, model in models.items():
        with open(MODEL_DIR / f'{name}_model.joblib', 'wb') as f:
            joblib.dump(model, f)

    # 保存特征列
    with open(MODEL_DIR / 'feature_cols.json', 'w') as f:
        json.dump(feature_cols, f)

    print(f"  模型已保存: {list(models.keys())}")
    return models, feature_cols


def predict_today():
    """预测今日走势"""
    # 获取数据
    df = fetch_market_data(years=3)
    if df is None:
        return None
    df = add_north_flow(df)

    # 特征工程
    features = engineer_features(df)
    feature_cols = [c for c in features.columns if not c.startswith('target')]

    # 加载模型
    models = {}
    for name in ['hgb', 'rf']:
        path = MODEL_DIR / f'{name}_model.joblib'
        if path.exists():
            with open(path, 'rb') as f:
                models[name] = joblib.load(f)

    if not models:
        print("  ❌ 未找到模型，请先运行: python ml_stock_predict.py")
        return None

    # 预测
    latest = features.iloc[-1:][feature_cols].values
    proba = 0
    for name, model in models.items():
        proba += model.predict_proba(latest)[0][1]
    proba /= len(models)

    # 置信度贝叶斯校准
    calibrated_conf = proba
    try:
        from feedback_loop import get_feedback_loop
        fb = get_feedback_loop()
        bs = fb._bucket_accuracy("high_zeri")
        if bs.get("total", 0) >= 5:
            calibrated_conf = proba * 0.7 + bs["accuracy"] * 0.3
    except: pass

    if calibrated_conf > 0.65:
        trend, jx, conf = "涨", "吉", calibrated_conf
    elif calibrated_conf > 0.55:
        trend, jx, conf = "震荡偏涨", "中平", calibrated_conf
    elif calibrated_conf > 0.45:
        trend, jx, conf = "平", "中平", 0.5
    elif calibrated_conf > 0.35:
        trend, jx, conf = "震荡偏跌", "中平", 1 - calibrated_conf
    else:
        trend, jx, conf = "跌", "凶", 1 - calibrated_conf

    result = {
        "date": get_beijing_now().strftime("%Y-%m-%d"),
        "system": "ML集成(HGB+RF,76特征)",
        "trend_prediction": trend, "jixiong": jx,
        "confidence": round(conf, 3),
        "probability_up": round(proba, 3),
        "calibrated": round(calibrated_conf, 3),
        "predicted_at": get_beijing_now().isoformat(),
    }

    # 附加AI情绪信号
    try:
        from ai_sentiment import get_sentiment_signal
        result["ai_sentiment"] = round(get_sentiment_signal(), 3)
        result["ai_flag"] = "偏多" if result["ai_sentiment"] > 0.15 else ("偏空" if result["ai_sentiment"] < -0.15 else "中性")
    except:
        pass

    # 保存（UTF-8）
    pred_file = MEMORY / "ml_predictions.json"
    predictions = []
    if pred_file.exists():
        with open(pred_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
    predictions = [p for p in predictions if p['date'] != result['date']]
    predictions.append(result)
    with open(pred_file, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)

    return result


# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ML股票预测系统 v3.0")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--predict-only", action="store_true")
    parser.add_argument("--backtest", action="store_true")
    args = parser.parse_args()

    print("=" * 55)
    print("  🤖 ML集成学习股票预测系统 v3.0")
    print("=" * 55)

    # 获取数据
    df = fetch_market_data(years=3)
    if df is None or len(df) < 300:
        print("❌ 数据不足")
        return
    df = add_north_flow(df)

    # 特征工程
    print("\n  特征工程...")
    features = engineer_features(df)
    n_features = len([c for c in features.columns if not c.startswith('target')])
    print(f"  生成 {n_features} 个特征, {len(features)} 行数据")

    if args.backtest or (not args.train_only and not args.predict_only):
        # 回测评估
        results, acc = train_evaluate(features)
        # 训练最终模型
        train_final_model(features)

    if args.train_only:
        train_final_model(features)
        return

    if args.backtest:
        return

    # 预测
    result = predict_today()
    if result:
        print(f"\n{'='*55}")
        print(f"  📈 今日预测")
        print(f"  {'='*55}")
        print(f"  上涨概率: {result['probability_up']:.1%}")
        print(f"  预测趋势: {result['trend_prediction']}")
        print(f"  吉凶: {result['jixiong']}")
        print(f"  置信度: {result['confidence']:.0%}")


if __name__ == "__main__":
    main()
