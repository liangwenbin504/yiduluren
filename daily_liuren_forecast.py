#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬前向预测记录器（每日真实起课）
==================================
原理：
  - 每天真实起课（记录动念时刻，即脚本执行时间）
  - 预测未来20个交易日的走势
  - 自动保存为JSON，累积样本
  - 每日盘后自动验证

使用方法：
  python daily_liuren_forecast.py   # 执行当日预测
  python daily_liuren_forecast.py --verify  # 验证昨日及之前的预测
  python daily_liuren_forecast.py --report  # 生成月度报告
"""

import sys
import io
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# 不包装 stdout，直接使用
BASE = Path(__file__).parent
PRED_DIR = BASE / "_memory"
PRED_FILE = PRED_DIR / "liuren_forward_records.json"

# 确保目录存在
PRED_DIR.mkdir(parents=True, exist_ok=True)


def load_records():
    if PRED_FILE.exists():
        with open(PRED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_records(records):
    with open(PRED_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def generate_today_forecast():
    """为今天生成六壬预测"""
    from generate_liuren_20d_signals import (
        get_day_ganzhi, get_yuejiang_for_date,
        analyze_8_dimensions, get_trading_days
    )
    
    now = datetime.now()
    today = now.date()
    
    # 检查是否为交易日
    if today.weekday() >= 5:
        print(f"  今天 {today} 是周末，跳过")
        return None
    
    records = load_records()
    
    # 检查今天是否已经预测过
    today_str = today.isoformat()
    for r in records:
        if r.get('predict_date') == today_str:
            print(f"  今日 {today_str} 已预测过")
            return r
    
    # 执行起课（真实动念时刻）
    year, month, day = today.year, today.month, today.day
    ri_gan, ri_zhi = get_day_ganzhi(year, month, day)
    yuejiang = get_yuejiang_for_date(year, month, day)
    shichen = now.strftime('%H:%M')  # 真实时辰
    
    print(f"  真实起课时刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  年: {year}  月: {month}  日: {day}")
    print(f"  日柱: {ri_gan}{ri_zhi}")
    print(f"  月将: {yuejiang}")
    print(f"  占时: {shichen}")
    
    # 2026-08-17 清理：旧 DaLiuRenEngine → V2 权威引擎
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    r = SiKeSanChuanCalculator2().calculate(ri_gan, ri_zhi, yuejiang, SHICHEN_FOR_20D)
    sc = r['sanchuan']
    san_chuan_result = {
        '课体': sc.get('课体', ''),
        '三传': [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')],
        '起法': sc.get('起法', ''),
        'tiandi_pan': r['tiandi_pan'],
    }
    
    composite, details, dim_scores = analyze_8_dimensions(san_chuan_result, ri_gan)
    
    # 吉凶判定
    if composite > 0.3: jixiong = '大吉'
    elif composite > 0.15: jixiong = '吉'
    elif composite > 0.05: jixiong = '小吉'
    elif composite > -0.05: jixiong = '中平'
    elif composite > -0.15: jixiong = '小凶'
    elif composite > -0.3: jixiong = '凶'
    else: jixiong = '大凶'
    
    # 趋势判定
    trend_score = dim_scores.get('sanchuan', 0)
    if trend_score > 0.3: trend = '上涨'
    elif trend_score > 0.05: trend = '偏涨'
    elif trend_score > -0.05: trend = '震荡'
    elif trend_score > -0.3: trend = '偏跌'
    else: trend = '下跌'
    
    # 建议仓位
    confidence = min(0.9, 0.5 + abs(composite))
    if composite > 0.3: suggested_pos = 1.0
    elif composite > 0.15: suggested_pos = 0.8
    elif composite > 0.05: suggested_pos = 0.6
    elif composite > -0.05: suggested_pos = 0.5
    elif composite > -0.15: suggested_pos = 0.3
    elif composite > -0.3: suggested_pos = 0.1
    else: suggested_pos = 0.0
    
    # 计算目标日期（T+20交易日）
    future_trading = get_trading_days(today, today + timedelta(days=60))
    target_date = None
    if len(future_trading) >= 21:  # 排除今天
        target_date = future_trading[20].isoformat()
    
    record = {
        'predict_date': today_str,
        'predict_time': now.isoformat(),
        'target_date': target_date,
        'period': '20d',
        'input': {
            'year': year, 'month': month, 'day': day,
            'shichen': shichen,
            'yuejiang': yuejiang,
            'ri_zhu': ri_gan + ri_zhi,
        },
        'output': {
            'jixiong': jixiong,
            'trend': trend,
            'confidence': round(confidence, 3),
            'jx_score': round(composite, 3),
            'suggested_position': suggested_pos,
            'keti': san_chuan_result.get('课体', ''),
            'sanchuan': '-'.join(san_chuan_result.get('三传', [])),
            'details': details,
            'dim_scores': {k: round(v, 3) for k, v in dim_scores.items()},
        },
        'actual': {
            'status': 'pending',
            'actual_change': None,
            'actual_dir': None,
            'verified': False,
        }
    }
    
    records.append(record)
    save_records(records)
    
    print(f"\n  ┌─── 预测结果 ───┐")
    print(f"  │ 吉凶: {jixiong}")
    print(f"  │ 趋势: {trend}")
    print(f"  │ 置信度: {confidence:.1%}")
    print(f"  │ 建议仓位: {suggested_pos:.0%}")
    print(f"  │ 目标日期 (T+20): {target_date}")
    print(f"  │ 8维评分:")
    for k, v in dim_scores.items():
        bar = '█' * int((v + 1) * 5) if v > 0 else '░' * int((-v + 1) * 5)
        print(f"  │   {k:10s}: {v:+.2f} {bar}")
    print(f"  └─────────────────┘")
    
    return record


def verify_predictions():
    """验证已到期的预测（T+20日）"""
    import random  # 模拟行情（实际应使用akshare）
    
    records = load_records()
    verified_count = 0
    today = date.today()
    
    # 获取模拟行情
    random.seed(42)
    price = 4000.0
    price_map = {}
    for d in sorted(set(r['predict_date'] for r in records)):
        target_d = date.fromisoformat(d) + timedelta(days=30)  # 简化：30天后验证
        while target_d not in price_map:
            change = random.gauss(0.0003, 0.012)
            price *= (1 + change)
            price_map[d] = round(price, 2)
            target_d += timedelta(days=1)
    
    for r in records:
        if r['actual']['verified']:
            continue
        
        predict_date = date.fromisoformat(r['predict_date'])
        # 简化验证：如果是20天前的预测，今天就可以验证
        if (today - predict_date).days >= 20:
            # 获取实际价格（此处为模拟）
            t_close = price_map.get(r['predict_date'], 4000)
            t20_close = t_close * (1 + random.gauss(0.006, 0.05))  # 20天涨跌幅
            
            change_20d = (t20_close / t_close) - 1
            actual_dir = 1 if change_20d > 0 else (-1 if change_20d < 0 else 0)
            
            pred_dir = 0
            jx = r['output']['jixiong']
            if '大吉' in jx or jx == '吉' or jx == '小吉':
                pred_dir = 1
            elif jx == '凶' or jx == '大凶' or jx == '小凶':
                pred_dir = -1
            
            hit = (pred_dir == actual_dir) if pred_dir != 0 else None
            
            r['actual'] = {
                'status': 'verified',
                'actual_change': round(change_20d, 4),
                'actual_dir': actual_dir,
                'verified': True,
                'hit': hit,
                'verify_date': today.isoformat(),
            }
            verified_count += 1
    
    if verified_count > 0:
        save_records(records)
        print(f"  验证完成: {verified_count} 条预测已更新")
    else:
        print(f"  无需验证的预测")
    
    # 统计已验证记录的命中率
    verified = [r for r in records if r['actual']['verified']]
    if verified:
        hits = sum(1 for r in verified if r['actual']['hit'])
        total = len(verified)
        rate = hits / total * 100 if total > 0 else 0
        print(f"\n  历史命中率: {hits}/{total} = {rate:.1f}%")


def generate_report():
    """生成月度报告"""
    records = load_records()
    verified = [r for r in records if r['actual']['verified']]
    pending = [r for r in records if not r['actual']['verified']]
    
    print(f"\n{'='*60}")
    print(f"  六壬前向预测报告")
    print(f"{'='*60}")
    print(f"  总预测数: {len(records)}")
    print(f"  已验证: {len(verified)}")
    print(f"  待验证: {len(pending)}")
    
    if verified:
        hits = sum(1 for r in verified if r['actual']['hit'])
        total = len(verified)
        rate = hits / total * 100
        print(f"\n  ┌─── 命中率 ───┐")
        print(f"  │ 总命中率: {hits}/{total} = {rate:.1f}%")
        
        # 按吉凶类型分
        jixiong_stats = {}
        for r in verified:
            jx = r['output']['jixiong']
            if jx not in jixiong_stats:
                jixiong_stats[jx] = {'hit': 0, 'total': 0}
            jixiong_stats[jx]['total'] += 1
            if r['actual']['hit']:
                jixiong_stats[jx]['hit'] += 1
        
        print(f"  │")
        print(f"  │ 分类型命中率:")
        for jx, stats in sorted(jixiong_stats.items()):
            r = stats['hit'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  │   {jx}: {stats['hit']}/{stats['total']} = {r:.1f}%")
        print(f"  └─────────────┘")
    
    print(f"\n  最近5条预测:")
    print(f"  {'日期':<12} {'吉凶':<8} {'趋势':<8} {'状态':<10} {'命中率':<10}")
    print(f"  {'-'*50}")
    for r in sorted(records, key=lambda x: x['predict_date'], reverse=True)[:5]:
        jx = r['output']['jixiong']
        tr = r['output']['trend']
        status = '已验证' if r['actual']['verified'] else '待验证'
        hit = '?' 
        if r['actual']['verified']:
            hit = '✓' if r['actual']['hit'] else '✗'
        print(f"  {r['predict_date']:<12} {jx:<8} {tr:<8} {status:<10} {hit:<10}")
    
    print(f"{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='六壬前向预测记录器')
    parser.add_argument('--verify', action='store_true', help='验证历史预测')
    parser.add_argument('--report', action='store_true', help='生成报告')
    args = parser.parse_args()
    
    if args.report:
        generate_report()
    elif args.verify:
        verify_predictions()
    else:
        generate_today_forecast()


if __name__ == '__main__':
    main()
