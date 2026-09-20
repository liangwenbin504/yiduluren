"""
三级决策矩阵引擎 v2.0
=====================
量化(个股) + 六壬(宏观) → 综合决策建议
量化为主，六壬为辅：置信度≤50%时显示六壬预测按钮

参考模式（config.LIUREN_REFERENCE_ONLY=True）：
六壬预测【不参与】任何买卖决策，仅展示供观察验证。
Level 3（量化置信度<50%）改为"量化不足·空仓观望"，不再依赖六壬。
"""
from datetime import datetime
from pathlib import Path

try:
    from config import LIUREN_REFERENCE_ONLY
except Exception:
    LIUREN_REFERENCE_ONLY = True  # 默认安全：参考模式

def compute_decision_matrix(target_date=None):
    from liuren_20d_engine import get_liuren_20d_signal, load_liuren_prediction
    
    # 1. 六壬宏观
    try:
        if target_date:
            liuren = load_liuren_prediction(target_date.strftime('%Y-%m-%d'))
            if not liuren:
                liuren = get_liuren_20d_signal(target_date)
        else:
            liuren = get_liuren_20d_signal()
    except:
        liuren = {'prediction': {'trend': '震荡', 'score': 0, 'confidence': 50}, 'keti': ''}
    
    lr_trend = liuren['prediction']['trend']
    lr_conf = liuren['prediction']['confidence']
    lr_score = liuren['prediction']['score']
    is_bull = '涨' in lr_trend
    is_bear = '跌' in lr_trend
    
    # 2. 量化
    try:
        from quant_predictor import get_quant_signal
        quant = get_quant_signal(target_date)
        stocks = quant.get('analysis', {})
    except:
        quant = {'trend_prediction': '震荡', 'confidence': 50}
        stocks = {}
    
    q_trend = quant.get('trend_prediction', '震荡')
    q_conf = quant.get('confidence', 50)
    
    decisions = []
    stock_data = stocks if stocks else {'上证综指': {'trend': q_trend, 'confidence': q_conf, 'score': 0}}
    
    hi = mid = lo = 0
    for name, sd in stock_data.items():
        qt = sd.get('trend', q_trend)
        qc = sd.get('confidence', q_conf)
        qb = '涨' in qt if qt else False
        qd = '跌' in qt if qt else False
        
        if qc >= 70:
            level = 1; hi += 1
            conf_color = '#27ae60'; row_color = '#e8f5e9'
            main = qt; need_liuren = False
            if qb and is_bull: adv = ('🟢 强烈看涨·买入', 'HIGH_BUY')
            elif qb and is_bear: adv = ('⚡ 量化涨/六壬跌·减半', 'CAUTIOUS')
            elif qd and is_bear: adv = ('🔴 强烈看跌·卖出', 'HIGH_SELL')
            elif qd and is_bull: adv = ('⚡ 量化跌/六壬涨·观望', 'CAUTIOUS')
            else: adv = ('⏸ 不明·观望', 'HOLD')
            reason = f'量化高置信({qc}%)，直接采用'
        elif qc >= 50:
            level = 2; mid += 1
            conf_color = '#f39c12'; row_color = '#fff8e1'
            need_liuren = False
            if LIUREN_REFERENCE_ONLY:
                # 参考模式：六壬不参与，直接采用量化信号
                main = qt; reason = f'量化({qc}%)独立决策（六壬仅参考）'
                adv = ('📈 看涨·买入', 'BUY') if qb else ('📉 看跌·卖出', 'SELL') if qd else ('⏸ 不明·观望', 'HOLD')
            elif qb == is_bull:
                main = qt; reason = f'量化({qc}%)与六壬一致'
                adv = ('📈 看涨·加仓', 'BUY') if qb else ('📉 看跌·减仓', 'SELL')
            else:
                main = f'{qt}/{lr_trend}'; reason = f'量化({qc}%)与六壬矛盾'
                adv = ('⚠️ 分歧·减半', 'DIVERGE')
        else:
            level = 3; lo += 1
            conf_color = '#e74c3c'; row_color = '#fde8e8'
            if LIUREN_REFERENCE_ONLY:
                # 参考模式：六壬不参与决策，量化不足即空仓观望
                main = '震荡'; need_liuren = False
                reason = f'量化置信低({qc}%)，六壬仅参考·空仓观望'
                adv = ('⏸ 不明·观望', 'HOLD')
            else:
                # 原逻辑：量化不足时依赖六壬
                main = lr_trend; need_liuren = True
                reason = f'量化置信低({qc}%)，需六壬'
                if is_bull: adv = ('🔮 六壬涨·轻仓试探', 'LIGHT_BUY')
                elif is_bear: adv = ('🔮 六壬跌·空仓观望', 'EMPTY')
                else: adv = ('⏸ 不明·观望', 'HOLD')
        
        decisions.append({
            'stock': name, 'level': level,
            'conf_color': conf_color, 'row_color': row_color,
            'quant_trend': qt, 'quant_conf': qc,
            'liuren_trend': lr_trend, 'liuren_conf': lr_conf,
            'main_signal': main, 'reason': reason,
            'advice': adv[0], 'need_liuren': need_liuren,
        })
    
    return {
        'cycle_start': liuren.get('cycle_start', ''),
        'cycle_end': liuren.get('cycle_end', ''),
        'liuren_macro': {'trend': lr_trend, 'score': lr_score, 'confidence': lr_conf, 'keti': liuren.get('keti', '')},
        'quant_overview': {'trend': q_trend, 'confidence': q_conf},
        'stats': {'total': len(decisions), 'high': hi, 'mid': mid, 'need_liuren': lo},
        'decisions': decisions,
    }
