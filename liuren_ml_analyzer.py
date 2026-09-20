#!/usr/bin/env python3
"""六壬ML反馈分析器"""
import json, os, sys, io, gc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
PRED_FILE = MEMORY / "stock_predictions.json"

WUXING_DZ = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

def extract_liuren_features(prediction):
    feats = {}
    rizhu = prediction.get('rizhu', '')
    if rizhu and len(rizhu) >= 2:
        feats['rizhu_gan'] = rizhu[0]
        feats['rizhu_zhi'] = rizhu[1]
    feats['yuejiang'] = prediction.get('yue_jiang', '')
    feats['shichen'] = prediction.get('shi_chen', '')
    feats['category'] = prediction.get('category', '?')
    jx = str(prediction.get('jixiong', ''))
    feats['jixiong_ji'] = 1 if '吉' in jx else 0
    feats['jixiong_xiong'] = 1 if '凶' in jx else 0
    sanchuan = prediction.get('sanchuan', [])
    for i, sz in enumerate(sanchuan[:3]):
        feats[f'sc{i}'] = str(sz)
        feats[f'sc{i}_wx'] = WUXING_DZ.get(str(sz), '')
    feats['correct'] = 1 if prediction.get('trend_prediction') == prediction.get('actual_result') else 0
    return feats

def analyze_liuren_factors():
    if not PRED_FILE.exists(): return None
    with open(PRED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    preds = data if isinstance(data, list) else data.get('predictions', [])
    matched = [p for p in preds if p.get('status') == 'completed']
    if len(matched) < 3: return None

    features = [extract_liuren_features(p) for p in matched]
    df = pd.DataFrame(features)
    correct = df['correct']

    try:
        print(f"\n  六壬因子: {len(preds)}预测/{len(matched)}对照")
        print(f"  命中: {correct.sum()}/{len(correct)} = {correct.mean()*100:.0f}%")
    except: pass

    insights = {
        "at": datetime.now(timezone.utc).isoformat(),
        "total": len(preds), "matched": len(matched),
        "accuracy": round(correct.mean() * 100, 1),
    }

    with open(MEMORY / "liuren_factor_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)

    gc.collect()
    return insights

if __name__ == '__main__':
    analyze_liuren_factors()
