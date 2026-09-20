#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史六壬信号生成器
==================
功能：
  1. 从已有预测记录中提取每日六壬信号
  2. 导出为CSV格式，供聚宽/米筐等量化平台回测读取
  3. 信号格式：date, jixiong, trend, confidence, suggested_position

用法：
  python liuren_signal_generator.py                # 从已有记录提取
  python liuren_signal_generator.py --export csv   # 导出CSV
  python liuren_signal_generator.py --backfill     # 回填历史（需API可用）
"""

import json, os, sys, csv, io
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
PRED_FILE = MEMORY / "stock_predictions.json"
OUTPUT_CSV = MEMORY / "liuren_daily_signals.csv"


def load_predictions():
    """加载所有预测记录"""
    if not PRED_FILE.exists():
        print(f"  预测文件不存在: {PRED_FILE}")
        return []
    try:
        with open(PRED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get('predictions', [])
    except Exception as e:
        print(f"  加载失败: {e}")
        return []


def calc_jixiong_score(jixiong: str) -> float:
    """将吉凶文字转换为数值分数 (-1 ~ +1)"""
    jx = (jixiong or "").strip()
    if not jx:
        return 0.0
    score = 0.0
    if '大凶' in jx: score -= 1.0
    elif '凶' in jx: score -= 0.7
    elif '小凶' in jx: score -= 0.4
    elif '先凶' in jx: score -= 0.3
    if '大吉' in jx: score += 1.0
    elif '吉' in jx: score += 0.7
    elif '小吉' in jx: score += 0.4
    elif '先吉' in jx: score += 0.3
    if '中平' in jx or jx == '平':
        score = 0.0
    if '藏' in jx:
        score *= 0.5
    if '后吉' in jx or '转吉' in jx:
        score = max(score, 0.3)
    if '后凶' in jx or '转凶' in jx:
        score = min(score, -0.3)
    return max(min(score, 1.0), -1.0)


def calc_trend_bias(trend: str) -> float:
    """将趋势预测转换为多空倾向 (-1 ~ +1)"""
    t = (trend or "").strip()
    if not t:
        return 0.0
    score = 0.0
    if t.startswith('涨'): score += 0.8
    elif '先涨' in t: score += 0.4
    elif '偏涨' in t: score += 0.5
    elif '后涨' in t: score += 0.3
    if t.startswith('跌'): score -= 0.8
    elif '先跌' in t: score -= 0.4
    elif '偏跌' in t: score -= 0.5
    elif '后跌' in t: score -= 0.3
    if t == '平' or '震荡' in t and '偏' not in t:
        score = 0.0
    return max(min(score, 1.0), -1.0)


def calc_suggested_position(jixiong_score: float, trend_bias: float, confidence: float) -> float:
    """
    计算建议仓位 (0.0 ~ 1.0)
    综合吉凶分数 + 趋势倾向 + 置信度
    """
    if confidence <= 0:
        confidence = 0.5
    
    # 综合信号
    signal = jixiong_score * 0.6 + trend_bias * 0.4
    
    # 置信度加权
    weighted_signal = signal * confidence
    
    # 映射到仓位
    if weighted_signal > 0.4:
        return 1.0      # 满仓
    elif weighted_signal > 0.2:
        return 0.8      # 八成仓
    elif weighted_signal > 0.05:
        return 0.6      # 六成仓
    elif weighted_signal > -0.05:
        return 0.5      # 半仓（中性）
    elif weighted_signal > -0.2:
        return 0.3      # 三成仓
    elif weighted_signal > -0.4:
        return 0.1      # 一成仓
    else:
        return 0.0      # 空仓


def extract_daily_signals(predictions: list) -> list:
    """
    从预测记录中提取每日信号
    同一天有多条预测时取均值
    """
    daily_data = defaultdict(list)
    
    for p in predictions:
        target_date = p.get('target_date') or p.get('date') or ''
        if not target_date:
            continue
        
        jixiong = p.get('jixiong', '')
        trend = p.get('trend_prediction', '')
        confidence = p.get('confidence', 0) or 0
        
        if not jixiong and not trend:
            continue
        
        jx_score = calc_jixiong_score(jixiong)
        trend_score = calc_trend_bias(trend)
        
        daily_data[target_date].append({
            'jixiong': jixiong,
            'trend': trend,
            'confidence': float(confidence),
            'jx_score': jx_score,
            'trend_score': trend_score,
        })
    
    # 按日期汇总
    signals = []
    for d in sorted(daily_data.keys()):
        items = daily_data[d]
        avg_jx = sum(i['jx_score'] for i in items) / len(items)
        avg_trend = sum(i['trend_score'] for i in items) / len(items)
        avg_conf = sum(i['confidence'] for i in items) / len(items)
        
        # 取置信度最高的那条的文字描述
        best = max(items, key=lambda x: x['confidence'])
        
        pos = calc_suggested_position(avg_jx, avg_trend, avg_conf)
        
        # 用文字描述
        if pos >= 0.9:
            pos_label = "满仓"
        elif pos >= 0.7:
            pos_label = "八成仓"
        elif pos >= 0.5:
            pos_label = "半仓"
        elif pos >= 0.3:
            pos_label = "三成仓"
        elif pos >= 0.1:
            pos_label = "一成仓"
        else:
            pos_label = "空仓"
        
        signals.append({
            'date': d,
            'jixiong': best['jixiong'],
            'trend': best['trend'],
            'confidence': round(avg_conf, 3),
            'jx_score': round(avg_jx, 3),
            'trend_score': round(avg_trend, 3),
            'suggested_position': round(pos, 2),
            'position_label': pos_label,
            'num_predictions': len(items),
        })
    
    return signals


def export_csv(signals: list):
    """导出为CSV"""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'date', 'jixiong', 'trend', 'confidence',
            'jx_score', 'trend_score', 
            'suggested_position', 'position_label', 'num_predictions'
        ])
        writer.writeheader()
        writer.writerows(signals)
    print(f"\n  已导出: {OUTPUT_CSV}")
    print(f"  共 {len(signals)} 条日度信号")


def print_summary(signals: list):
    """打印统计摘要"""
    if not signals:
        print("  无信号数据")
        return
    
    bullish = sum(1 for s in signals if s['suggested_position'] > 0.6)
    bearish = sum(1 for s in signals if s['suggested_position'] < 0.4)
    neutral = len(signals) - bullish - bearish
    
    avg_pos = sum(s['suggested_position'] for s in signals) / len(signals)
    
    print(f"\n{'='*55}")
    print(f"  六壬每日信号 — 统计摘要")
    print(f"{'='*55}")
    print(f"  覆盖日期: {signals[0]['date']} ~ {signals[-1]['date']}")
    print(f"  总交易日: {len(signals)} 天")
    print(f"  平均仓位: {avg_pos:.1%}")
    print(f"  看多天数（仓位>60%）: {bullish} 天 ({bullish/len(signals):.1%})")
    print(f"  中性天数: {neutral} 天 ({neutral/len(signals):.1%})")
    print(f"  看空天数（仓位<40%）: {bearish} 天 ({bearish/len(signals):.1%})")
    print(f"{'='*55}")
    
    print(f"\n  最近10条信号:")
    print(f"  {'日期':<12} {'吉凶':<8} {'趋势':<10} {'置信度':<8} {'建议仓位':<10}")
    print(f"  {'-'*55}")
    for s in signals[-10:]:
        print(f"  {s['date']:<12} {s['jixiong']:<8} {s['trend']:<10} "
              f"{s['confidence']:>6.0%}   {s['position_label']:<8}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='六壬历史信号生成器')
    parser.add_argument('--export', choices=['csv', 'json'], default='csv',
                        help='导出格式 (默认csv)')
    parser.add_argument('--backfill', action='store_true',
                        help='回填历史预测（暂未实现）')
    args = parser.parse_args()
    
    print("=" * 55)
    print("  六壬历史信号生成器 v1.0")
    print("=" * 55)
    
    predictions = load_predictions()
    print(f"\n  加载预测记录: {len(predictions)} 条")
    
    signals = extract_daily_signals(predictions)
    print(f"  提取日度信号: {len(signals)} 天")
    
    if signals:
        print_summary(signals)
        export_csv(signals)
        
        print(f"\n  💡 使用说明：")
        print(f"     1. 将 {OUTPUT_CSV.name} 上传到聚宽研究环境")
        print(f"     2. 在策略中读取：signals = pd.read_csv('liuren_daily_signals.csv')")
        print(f"     3. 用 suggested_position 字段控制仓位")
        print(f"     4. 对比：纯量化 vs 六壬+量化，看超额收益")
    else:
        print("\n  ⚠️ 暂无可用信号数据")
        print("     请先运行 stock_daily_predict.py 生成预测记录")


if __name__ == '__main__':
    main()
