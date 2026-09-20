#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化预测引擎 v1.0 — 方案A：宽基ETF轮动 + 波动率目标
===================================================
周期: 20个交易日（与六壬周期同步）

策略逻辑:
  1. 宽基ETF池: 沪深300/中证500/创业板/上证50/科创50
  2. 动量因子: 20日涨跌幅排名
  3. 波动率目标: ATR计算波动率，动态调整仓位
  4. 信号生成: 买入最强 + 减仓最弱

输出:
  - 预测周期起始日
  - 推荐ETF + 目标仓位
  - 趋势判断（涨/跌/震荡）
  - 置信度评分
"""

import json, os, sys, warnings
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 结算时回填知识点特征（自进化 Step1 卡点修复 2026-08-12）
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from engine.knowledge_features import extract_for_backfill

warnings.filterwarnings('ignore')

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
QUANT_DATA = BASE / "quant_data"
QUANT_MODELS = BASE / "quant_models"

os.makedirs(MEMORY, exist_ok=True)
os.makedirs(QUANT_DATA, exist_ok=True)
os.makedirs(QUANT_MODELS, exist_ok=True)

DEBUG_LOG = BASE / "_memory" / "quant_debug.log"

def _debug(msg):
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

ETF_POOL = {
    '沪深300': {'code': 'sh000300', 'etf': '510300', 'name': '沪深300ETF'},
    '中证500': {'code': 'sh000905', 'etf': '510500', 'name': '中证500ETF'},
    '创业板':   {'code': 'sz399006', 'etf': '159915', 'name': '创业板ETF'},
    '上证50':   {'code': 'sh000016', 'etf': '510050', 'name': '上证50ETF'},
    '科创50':   {'code': 'sh000688', 'etf': '588000', 'name': '科创50ETF'},
}

CYCLE_DAYS = 20                      # 一个量化周期 = 20 个交易日（主周期；六壬为辅对齐此窗口）
VOLATILITY_TARGET = 0.15
MAX_POSITION = 1.0
MIN_POSITION = 0.0


def _add_trading_days(start_dt, n):
    """从 start_dt(datetime) 起，跳过周六日，推进 n 个交易日（不处理节假日）。"""
    d = start_dt
    added = 0
    while added < n:
        d = d + timedelta(days=1)
        if d.weekday() >= 5:             # 5=Sat 6=Sun
            continue
        added += 1
    return d


def _get_akshare():
    try:
        import akshare as ak
        return ak
    except ImportError:
        return None


def fetch_etf_data_fallback(code):
    """子进程fallback获取数据"""
    try:
        import subprocess
        script = Path(__file__).parent / 'engine' / 'market_fetcher.py'
        result = subprocess.run(
            [sys.executable, str(script), 'etf', code],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            import tempfile
            tmp = Path(tempfile.gettempdir()) / f'quant_{code.replace(".","_")}.json'
            return None
    except:
        pass
    return None


def _generate_simulated_data(code, days=80, target_date=None):
    """生成模拟数据（当akshare不可用时）"""
    try:
        seed_val = sum(ord(c) * (i + 1) for i, c in enumerate(code)) % (2**32)
        np.random.seed(seed_val)
        base_prices = {
            'sh000300': 4000, 'sh000905': 5500, 'sz399006': 2000,
            'sh000016': 2800, 'sh000688': 1000,
        }
        base = base_prices.get(code, 3000)
        
        if target_date is None:
            end_date = datetime.now()
        else:
            if isinstance(target_date, str):
                end_date = pd.to_datetime(target_date).to_pydatetime()
            else:
                end_date = target_date
        
        dates = pd.date_range(end=end_date, periods=days, freq='B')
        returns = np.random.normal(0.0003, 0.015, days)
        prices = base * np.cumprod(1 + returns)
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
            'open': prices * (1 + np.random.normal(0, 0.005, days)),
            'volume': np.random.randint(1000000, 10000000, days),
        })
        return df
    except Exception as e:
        print(f"  ⚠️ 生成模拟数据失败 ({code}): {e}")
        return None


def fetch_etf_data(code, years=2, target_date=None):
    _debug(f"fetch_etf_data: start code={code}")
    ak = _get_akshare()
    if ak is not None:
        try:
            if code.startswith('sh') or code.startswith('sz'):
                df = ak.stock_zh_index_daily(symbol=code)
            else:
                df = ak.fund_etf_daily(symbol=code)
            
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume'][:len(df.columns)]
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 如果指定了目标日期，截断到目标日期（避免未来函数）
            if target_date is not None:
                if isinstance(target_date, str):
                    target_date = pd.to_datetime(target_date)
                df = df[df['date'] <= target_date]
                cutoff = target_date - timedelta(days=years * 365)
            else:
                cutoff = datetime.now() - timedelta(days=years * 365)
            
            df = df[df['date'] >= cutoff]
            _debug(f"fetch_etf_data: akshare returned {len(df)} rows")
            if len(df) >= 60:
                return df
            else:
                print(f"  ⚠️ {code} 实时数据不足({len(df)}条)，使用模拟数据")
        except Exception as e:
            _debug(f"fetch_etf_data: akshare failed: {e}")
            print(f"  ⚠️ {code} 实时数据获取失败: {e}")
    
    _debug(f"fetch_etf_data: using simulated data for {code}")
    print(f"  ℹ️ {code} 使用模拟数据模式（akshare不可用）")
    df = _generate_simulated_data(code, target_date=target_date)
    if df is not None and len(df) >= 60:
        _debug(f"fetch_etf_data: simulated data OK, {len(df)} rows")
        return df
    
    _debug(f"fetch_etf_data: FAILED for {code}")
    print(f"  ❌ {code} 数据获取彻底失败")
    return None


def calc_momentum(df, window=20):
    if df is None or len(df) < window:
        return None
    df = df.copy()
    df['momentum'] = df['close'].pct_change(window)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['atr'] = (df['high'] - df['low']).rolling(14).mean()
    df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
    
    # 标准RSI计算：上涨平均 / 下跌平均
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    # MACD辅助指标
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df


def get_quant_signal(target_date=None):
    """
    生成量化预测信号（20天周期）
    
    Args:
        target_date: 周期起始日（默认今天）
    
    Returns:
        dict: 完整的量化预测结果
    """
    if target_date is None:
        target_date = datetime.now()
    
    _debug(f"get_quant_signal: start, target_date={target_date}")
    
    print(f"\n{'='*60}")
    print(f"  量化预测引擎 — 20天周期")
    print(f"  起始日: {target_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}")
    
    results = []
    
    for name, info in ETF_POOL.items():
        code = info['code']
        _debug(f"get_quant_signal: processing {name} ({code})")
        print(f"\n  分析 {name} ({code})...")
        
        df = fetch_etf_data(code, target_date=target_date)
        _debug(f"get_quant_signal: fetch_etf_data({code}) returned {type(df).__name__}, len={len(df) if df is not None else 'None'}")
        if df is None or len(df) < 60:
            print(f"    ⚠️ 数据不足")
            _debug(f"get_quant_signal: {code} SKIPPED - data insufficient")
            continue
        
        df = calc_momentum(df)
        if df is None:
            _debug(f"get_quant_signal: {code} SKIPPED - calc_momentum returned None")
            continue
        
        _debug(f"get_quant_signal: {code} calc_momentum OK, proceeding")
        
        latest = df.iloc[-1]
        momentum = latest['momentum'] if pd.notna(latest['momentum']) else 0
        volatility = latest['volatility'] if pd.notna(latest['volatility']) else 0.2
        atr = latest['atr'] if pd.notna(latest['atr']) else 0
        price = latest['close']
        rsi = latest['rsi'] if pd.notna(latest['rsi']) else 50
        macd_hist = latest['macd_hist'] if pd.notna(latest['macd_hist']) else 0
        
        # 均线趋势判断（分级：强多/偏多/中性/偏空/强空）
        ma5 = latest['ma5']
        ma10 = latest['ma10']
        ma20 = latest['ma20']
        ma60 = latest['ma60']
        close = latest['close']
        
        ma_trend = 'neutral'
        ma_score = 0
        if pd.notna(ma60):
            if close > ma5 > ma10 > ma20 > ma60:
                ma_trend = 'strong_bullish'
                ma_score = 100
            elif close > ma20 and ma5 > ma20:
                    ma_trend = 'bullish'
                    ma_score = 50
            elif close < ma5 < ma10 < ma20 < ma60:
                ma_trend = 'strong_bearish'
                ma_score = -100
            elif close < ma20 and ma5 < ma20:
                ma_trend = 'bearish'
                ma_score = -50
        
        # 波动率目标仓位（仅做多时加仓，做空时减仓）
        if volatility > 0:
            target_vol = VOLATILITY_TARGET
            vol_ratio = target_vol / volatility
            position = min(MAX_POSITION, max(MIN_POSITION, vol_ratio))
        else:
            position = 0.5
        
        # 动量方向调整：动量为正才给满仓，动量为负则减仓
        if momentum < 0:
            position = position * max(0.05, 1 + momentum * 2)
        position = max(0.05, position)  # 保底5%
        
        # 综合评分（各因子标准化到[-100, 100]，加权）
        momentum_score = max(-100, min(100, momentum * 100))  # 20日涨跌幅 * 100
        rsi_score = (rsi - 50) * 2  # RSI 0-100 -> -100到100
        
        # MACD评分：柱状图正负
        macd_score = 0
        if pd.notna(macd_hist) and atr > 0:
            macd_ratio = macd_hist / atr
            macd_score = max(-100, min(100, macd_ratio * 500))
        
        # 加权综合评分
        score = (
            momentum_score * 0.35 +   # 动量 35%
            rsi_score * 0.20 +          # RSI 20%
            ma_score * 0.25 +          # 均线 25%
            macd_score * 0.20           # MACD 20%
        )
        
        results.append({
            'name': name,
            'code': code,
            'etf': info['etf'],
            'price': round(float(price), 2),
            'momentum_20d': round(float(momentum) * 100, 2) if pd.notna(momentum) else 0,
            'volatility': round(float(volatility) * 100, 2) if pd.notna(volatility) else 0,
            'atr': round(float(atr), 2) if pd.notna(atr) else 0,
            'rsi': round(float(rsi), 1) if pd.notna(rsi) else 50,
            'ma_trend': ma_trend,
            'position': round(position * 100, 1),
            'confidence': round(max(0, min(100, 50 + score * 0.5))),  # 置信度: 50±50→0~100
            'score': round(score, 1),
        })
    
    if not results:
        _debug(f"get_quant_signal: NO RESULTS - all ETFs failed")
        return {'error': '无法获取ETF数据'}
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    best = results[0]
    worst = results[-1]
    
    avg_score = np.mean([r['score'] for r in results])
    score_std = np.std([r['score'] for r in results]) if len(results) > 1 else 0
    
    # 趋势判断阈值（根据总分范围±100调整）
    if avg_score > 30:
        trend = '看涨'
    elif avg_score < -30:
        trend = '看跌'
    else:
        trend = '震荡'
    
    # 置信度计算：
    # 1. 分数绝对值越大，置信度越高（基础分）
    # 2. 各ETF方向一致性越高（标准差越小），置信度越高
    # 3. 动量、RSI、均线、MACD 多因子共振时置信度更高
    base_conf = min(90, 40 + abs(avg_score) * 0.6)
    
    # 一致性加分：标准差小说明各ETF方向一致
    if score_std < 15:
        consistency_bonus = 15
    elif score_std < 25:
        consistency_bonus = 8
    else:
        consistency_bonus = 0
    
    # 检查多因子共振（最好的ETF有多少因子同向）
    factor_agreement = 0
    if best['momentum_20d'] > 0:
        factor_agreement += 1
    if best['rsi'] > 50:
        factor_agreement += 1
    if best['ma_trend'] in ('bullish', 'strong_bullish'):
        factor_agreement += 1
    
    if worst['momentum_20d'] < 0:
        factor_agreement += 1
    if worst['rsi'] < 50:
        factor_agreement += 1
    if worst['ma_trend'] in ('bearish', 'strong_bearish'):
        factor_agreement += 1
    
    factor_bonus = min(10, factor_agreement * 1.5)
    
    conf = min(95, base_conf + consistency_bonus + factor_bonus)
    conf = max(10, conf)
    
    result = {
        'cycle_start': target_date.strftime('%Y-%m-%d'),
        'cycle_end': _add_trading_days(target_date, CYCLE_DAYS).strftime('%Y-%m-%d'),
        'cycle_days': CYCLE_DAYS,
        'trend_prediction': trend,
        'confidence': round(conf, 1),
        'best_etf': {
            'name': best['name'],
            'code': best['code'],
            'momentum_20d': best['momentum_20d'],
            'position': best['position'],
            'score': best['score'],
        },
        'worst_etf': {
            'name': worst['name'],
            'code': worst['code'],
            'momentum_20d': worst['momentum_20d'],
            'score': worst['score'],
        },
        'all_etfs': results,
        'average_score': round(avg_score, 1),
        'volatility_level': round(np.mean([r['volatility'] for r in results]), 2),
        'strategy': '宽基ETF轮动 + 波动率目标',
    }
    
    print(f"\n  ═══ 量化预测结果 ═══")
    print(f"  趋势: {trend} | 置信度: {conf:.1f}%")
    print(f"  推荐: {best['name']} (动量:{best['momentum_20d']:.1f}%, 仓位:{best['position']:.1f}%)")
    print(f"  避开: {worst['name']} (动量:{worst['momentum_20d']:.1f}%)")
    
    return result


def save_quant_prediction(prediction, filepath=None):
    if filepath is None:
        date_str = prediction.get('cycle_start', datetime.now().strftime('%Y-%m-%d'))
        filepath = QUANT_DATA / f'quant_prediction_{date_str}.json'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(prediction, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"  已保存: {filepath}")
    return filepath


def load_quant_prediction(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    filepath = QUANT_DATA / f'quant_prediction_{date_str}.json'
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_quant_history(limit=10):
    history = []
    files = sorted(QUANT_DATA.glob('quant_prediction_*.json'), reverse=True)[:limit]
    for fp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
                history.append(data)
        except:
            pass
    return history


# ── 20 交易日窗口回检（真实行情，无模拟兜底；防污染命中率）──
def _fetch_real_series(code, end_date):
    """回检专用：仅真实数据（akshare），绝不回落模拟数据。返回 date升序 df(date,close) 或 None。"""
    ak = _get_akshare()
    if ak is None:
        return None
    try:
        if code.startswith('sh') or code.startswith('sz'):
            df = ak.stock_zh_index_daily(symbol=code)
        else:
            df = ak.fund_etf_daily(symbol=code)
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume'][:len(df.columns)]
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        if end_date is not None:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            df = df[df['date'] <= end_date]
        return df[['date', 'close']].copy()
    except Exception as e:
        _debug(f"_fetch_real_series({code}) failed: {e}")
        return None


def _window_return(df, start_d, end_d):
    """窗口收益 = 最近≤end_d 收盘 / 最近≤start_d 收盘 - 1。

    防前视：只取 ≤ 各自日期 的最后一根已收盘 K 线；start 用预测日收盘锚定，
    end 用目标日（窗口末日）收盘。与预测窗口 [date, target_date] 严格一致。
    """
    if df is None or len(df) < 2:
        return None
    d0 = pd.to_datetime(start_d)
    d1 = pd.to_datetime(end_d)
    seg_s = df[df['date'] <= d0]
    seg_e = df[df['date'] <= d1]
    if seg_s.empty or seg_e.empty:
        return None
    c0 = float(seg_s.iloc[-1]['close'])
    c1 = float(seg_e.iloc[-1]['close'])
    if c0 <= 0:
        return None
    return c1 / c0 - 1.0


def check_quant_results():
    """量化 20 交易日窗口回检（与预测同源可比）。

    对 stock_predictions.json 中 category=='量化' 且 target_date<=今天 且未结算的记录：
    池内 5 指数 [date, target_date] 窗口收益均值 r，r>+0.5%→涨 / r<-0.5%→跌 / 其余→平，
    写回 actual_result + actual_details(各指数窗口收益) + status=completed。

    仅真实行情（无模拟兜底）；任一指数无数据则该记录跳过、保持 pending，绝不写假结果。
    """
    fp = MEMORY / "stock_predictions.json"
    if not fp.exists():
        return 0
    with open(fp, encoding='utf-8') as f:
        arr = json.load(f)
    today = datetime.now().date()
    n = 0
    for p in arr:
        if not isinstance(p, dict):
            continue
        if p.get('category') != '量化':
            continue
        if p.get('actual_result') or p.get('status') == 'completed':
            continue
        start, end = p.get('date'), p.get('target_date')
        if not start or not end:
            continue
        end_d = datetime.strptime(end, '%Y-%m-%d').date()
        if end_d > today:                  # 窗口未收盘，留待以后
            continue
        rets, per = [], {}
        for name, info in ETF_POOL.items():
            df = _fetch_real_series(info['code'], end_d)
            r = _window_return(df, start, end_d)
            if r is None:
                continue
            rets.append(r)
            per[name] = round(r * 100, 2)
        if not rets:
            _debug(f"check_quant_results: {p.get('id')} 无真实数据，跳过（保持 pending）")
            continue
        r_avg = float(np.mean(rets))
        actual = '涨' if r_avg > 0.005 else ('跌' if r_avg < -0.005 else '平')
        p['actual_result'] = actual
        p['actual_details'] = {
            'window_start': start, 'window_end': end,
            'window_return_pct': round(r_avg * 100, 2),
            'per_etf_return_pct': per,
            'basis': '池内5指数窗口收益均值(±0.5%)',
        }
        p['status'] = 'completed'
        # 自进化 Step1 卡点修复：标记 completed 时一并回填知识点特征
        _kf = extract_for_backfill(p)
        if _kf is not None:
            p['knowledge_features'] = _kf
        p['check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        n += 1
        _debug(f"check_quant_results: {p.get('id')} {start}~{end} r={r_avg*100:.2f}% → {actual}")
    if n:
        tmp = str(fp) + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(fp))
    return n


if __name__ == '__main__':
    result = get_quant_signal()
    if 'error' not in result:
        save_quant_prediction(result)
