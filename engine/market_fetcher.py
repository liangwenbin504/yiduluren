#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行情数据获取子进程脚本
在独立进程中运行，避免 mini-racer DLL 崩溃影响主 Dashboard 进程。
用法:
  python market_fetcher.py market          → 返回最新行情
  python market_fetcher.py history [days]  → 返回历史K线（默认120天）
"""
import sys, json

def fetch_market():
    import akshare as ak
    df = ak.stock_zh_index_daily(symbol="sh000001")
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    price = round(float(latest['close']), 2)
    prev_close = round(float(prev['close']), 2)
    change = round(price - prev_close, 2)
    change_pct = round(change / prev_close * 100, 2)
    high = round(float(latest['high']), 2)
    low = round(float(latest['low']), 2)
    # akshare新版本date在列中（RangeIndex），兼容旧版DatetimeIndex
    date_val = latest.get('date', latest.name)
    if hasattr(date_val, 'strftime'):
        date_str = date_val.strftime('%Y-%m-%d')
    elif hasattr(date_val, 'isoformat'):
        date_str = date_val.isoformat()
    else:
        date_str = str(date_val)[:10]
    return {
        'price': price,
        'prev_close': prev_close,
        'change': change,
        'change_pct': change_pct,
        'high': high,
        'low': low,
        'date': date_str,
        'name': '上证指数',
        'code': '000001',
    }

def fetch_history(days=120):
    import akshare as ak
    df = ak.stock_zh_index_daily(symbol="sh000001")
    df = df.tail(max(days, 10))
    history = []
    for _, row in df.iterrows():
        date_val = row.get('date', row.name)
        if hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d')
        elif hasattr(date_val, 'isoformat'):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val)[:10]
        history.append({
            'date': date_str,
            'close': round(float(row['close']), 2),
            'high': round(float(row['high']), 2),
            'low': round(float(row['low']), 2),
        })
    return history

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        if cmd == 'market':
            result = fetch_market()
        elif cmd == 'history':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 120
            result = fetch_history(days)
        else:
            result = {'error': f'未知命令: {cmd}'}
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)
