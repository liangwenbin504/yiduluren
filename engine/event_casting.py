#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件驱动起课引擎 v1.1（独立体系，与天机起课完全分离）
================================================================
背景（2026-08-15 憨爷拍板）：量化预测"拿不定"时（如大股突然异动），
才起课辅助预测"继续向上还是突然下跌"。非固定时辰、非机械类别。

铁律：
- 触发条件 = 动态 σ（反教条主义）：事件强度 = 单日|涨跌| ÷ 滚动20日标准差
    ≥1.5σ 弱记录（仅记录） / ≥2.0σ 主触发（自动起课） / ≥2.5σ 强标注（黑天鹅）
- 独立台账 event_casts.json（与 tianji_casts.json 分离——本质不同：
  天机=主观心动随时，事件=客观条件触发。混用统计口径脏，走回头路）。
- 检测 = 心跳自动（v1.1 憨爷拍板）：交易日盘中每 5 分钟自动拉实时行情，
  达 2σ 即自动起课，**时辰 = 事件触发时刻的真实时辰**（比人工补录精准）。
  守卫：仅交易日 + 实时数据存在 + 真 2σ 事件 + 一事一课；绝不自动落盘
  到 liuren_20d_data（周期文件），只写独立台账。AUTO_CAST 开关可控。
- 评估窗口：主 5 交易日 + 20 日辅助对齐。分方向各自对比条件基线，
  绝不用 55.3% 朴素基线。
- 条件基线（动态 2σ 事件口径，本地数据重算，见 _compute_baselines）：
  向上事件后5日上涨概率 / 向下事件后5日上涨概率（含20日）。

数据结构（_memory/event_casts.json）:
{
  "events": [ {event_id, date, symbol, name, change_pct, direction, sigma,
               level, rolling_sd, close, cast_id|null, created_at, auto} ],
  "casts":  [ {cast_id, event_id, date, shichen, prediction{...}, auto,
               created_at, window_5d{settled,actual_dir,hit}, window_20d{...}} ]
}
"""
import os, json, glob, statistics, sys
from datetime import datetime, date as _date

SHICHEN_MAP = {0:'子',1:'丑',2:'寅',3:'卯',4:'辰',5:'巳',6:'午',7:'未',8:'申',9:'酉',10:'戌',11:'亥'}
AUTO_CAST_ENABLED = True   # 事件起课自动触发开关（憨爷 2026-08-15：自动起课时辰更精准）

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_DIR = os.path.join(BASE, '_memory')
STORE_PATH = os.path.join(MEM_DIR, 'event_casts.json')

ROLL_WINDOW = 20          # 滚动标准差窗口（交易日，对齐 20 交易日周期）
LEVELS = [
    (1.5, 'weak',   '弱记录'),
    (2.0, 'main',   '主触发'),
    (2.5, 'strong', '强标注'),
]
# 宽基指数池（后续可扩展关注个股，各用自身滚动σ）
INDEX_POOL = [
    {'symbol': 'sh000001', 'name': '上证指数'},
    {'symbol': 'sh000300', 'name': '沪深300'},
]


# ── 数据加载（复用 _memory/idx_*.txt 行情缓存）──
def load_series(symbol='sh000001'):
    """返回 [(date_str, close), ...] 升序。优先用同名缓存文件。"""
    rows = {}
    files = sorted(glob.glob(os.path.join(MEM_DIR, 'idx_*.txt')) +
                   glob.glob(os.path.join(MEM_DIR, 'sh000001_2021_2024.txt')))
    # idx_*.txt 是上证指数；其他指数暂无缓存 → 回落上证
    for fp in files:
        with open(fp, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not (line.startswith('| 20') or line.startswith('| 19')):
                    continue
                cols = [c.strip() for c in line.strip('|').split('|')]
                if len(cols) < 3:
                    continue
                try:
                    rows[cols[0]] = float(cols[2])   # 'last' = 收盘
                except ValueError:
                    continue
    return sorted(rows.items())


def _store():
    if os.path.exists(STORE_PATH):
        try:
            return json.loads(open(STORE_PATH, encoding='utf-8').read())
        except Exception:
            pass
    return {'events': [], 'casts': []}


def _save(st):
    os.makedirs(MEM_DIR, exist_ok=True)
    tmp = STORE_PATH + '.tmp'
    open(tmp, 'w', encoding='utf-8').write(json.dumps(st, ensure_ascii=False, indent=2))
    os.replace(tmp, STORE_PATH)


# ── 触发检测 ──
def detect_events(date_str=None):
    """检测指定交易日（默认最近一个）的事件触发。返回事件列表（含已入库的）。
    事件强度 = |当日涨跌| / 滚动20日σ；分级 weak/main/strong。
    同日多标的可多事件（当前指数池只有上证可用缓存，其余回落）。
    """
    series = load_series()
    dates = [d for d, _ in series]
    closes = [c for _, c in series]
    if date_str is None:
        date_str = dates[-1]
    if date_str not in dates:
        return {'success': False, 'error': f'无 {date_str} 的行情数据（最近交易日 {dates[-1]}）'}
    i = dates.index(date_str)
    if i == 0:
        return {'success': False, 'error': '首日无涨跌幅'}
    chg = (closes[i] / closes[i-1] - 1) * 100
    win = closes[max(0, i-ROLL_WINDOW):i]  # 不含当日（用事件前 20 日估计"常态"）
    if len(win) < 10:
        return {'success': False, 'error': '滚动窗口样本不足'}
    rets = [(win[k]/win[k-1]-1)*100 for k in range(1, len(win))]
    sd = statistics.stdev(rets)
    sigma = abs(chg) / sd if sd > 0 else 0.0
    level = None
    for th, key, label in LEVELS:
        if sigma >= th:
            level = key
    if level is None:
        return {'success': True, 'data': [], 'note': f'{date_str} 无异动（{chg:+.2f}%，{sigma:.2f}σ）'}

    st = _store()
    ev = {
        'event_id': f'EV-{date_str}-{date_str.replace("-","")[2:]}{i%100:02d}',
        'date': date_str,
        'symbol': 'sh000001',
        'name': '上证指数',
        'change_pct': round(chg, 2),
        'direction': 'up' if chg >= 0 else 'down',
        'sigma': round(sigma, 2),
        'level': level,
        'rolling_sd': round(sd, 3),
        'close': round(closes[i], 2),
        'cast_id': None,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    # 去重：同日同标的已有事件则更新
    hit = None
    for k, e in enumerate(st['events']):
        if e.get('date') == date_str and e.get('symbol') == ev['symbol']:
            hit = k
            break
    if hit is not None:
        st['events'][hit] = ev
    else:
        st['events'].append(ev)
    _save(st)
    return {'success': True, 'data': [ev], 'note': f'{date_str} 触发 {ev["level"]}（{chg:+.2f}%，{sigma:.2f}σ）'}


# ── 心跳检测 + 自动起课（v1.1 憨爷拍板：时辰取事件触发时刻，精准）──
def _shichen_of(dt):
    return SHICHEN_MAP[(dt.hour + 1) // 2 % 12]


def fetch_realtime_change(symbol='sh000001'):
    """拉取实时涨跌幅（akshare 快照）。失败返回 None（心跳静默跳过，不阻塞）。"""
    try:
        import akshare as ak
        if symbol == 'sh000001':
            df = ak.stock_zh_index_spot_em(symbol="上证系列指数")
            row = df[df['代码'] == '000001']
            if row.empty:
                return None
            return float(row.iloc[0]['涨跌幅'])
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
        row = df[df['代码'] == symbol[2:]]
        if row.empty:
            return None
        return float(row.iloc[0]['涨跌幅'])
    except Exception:
        return None


def heartbeat_check(force_cast=False):
    """心跳检测（交易日盘中/收盘由后台线程调用，也可手动触发）：
    1) 拉实时涨跌幅（失败=非交易日/休市 → 跳过）
    2) 强度 = |实时涨跌| / 滚动20日σ（用缓存日线）
    3) ≥2σ → 记录事件；AUTO_CAST_ENABLED → 自动起课（时辰=触发时刻真实时辰）
    守卫：仅交易日实时数据存在 + 真 2σ + 一事一课；绝不写 liuren_20d_data。
    返回 {success, event|null, cast|null, note}
    """
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    chg = fetch_realtime_change()
    if chg is None:
        return {'success': True, 'event': None, 'cast': None,
                'note': f'{today} {now.strftime("%H:%M")} 无实时行情（非交易日或休市），心跳跳过'}
    series = load_series()
    closes = [c for _, c in series]
    if len(closes) < ROLL_WINDOW + 2:
        return {'success': False, 'error': '行情缓存不足'}
    win = closes[-ROLL_WINDOW:]
    rets = [(win[k]/win[k-1]-1)*100 for k in range(1, len(win))]
    sd = statistics.stdev(rets) if len(rets) > 1 else 1.0
    sigma = abs(chg) / sd if sd > 0 else 0.0

    # 未达 1.5σ：不算事件
    if sigma < 1.5:
        return {'success': True, 'event': None, 'cast': None,
                'note': f'{today} {now.strftime("%H:%M")} 实时 {chg:+.2f}%（{sigma:.2f}σ）未达事件阈值'}

    # 达事件阈值：先记录事件（自动，level 分级）
    level = 'main' if sigma >= 2.0 else 'weak'
    for th, key, label in LEVELS:
        if sigma >= th:
            level = key
    st = _store()
    ev = {
        'event_id': f'EV-{today}-{now.strftime("%H%M")}',
        'date': today,
        'symbol': 'sh000001',
        'name': '上证指数',
        'change_pct': round(chg, 2),
        'direction': 'up' if chg >= 0 else 'down',
        'sigma': round(sigma, 2),
        'level': level,
        'rolling_sd': round(sd, 3),
        'close': closes[-1] if closes else 0,
        'cast_id': None,
        'auto': True,
        'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
    }
    hit = None
    for k, e in enumerate(st['events']):
        if e.get('date') == today and e.get('symbol') == ev['symbol']:
            hit = k
            break
    if hit is not None:
        st['events'][hit] = ev
    else:
        st['events'].append(ev)
    _save(st)
    out = {'success': True, 'event': ev, 'cast': None,
           'note': f'{today} {now.strftime("%H:%M")} 触发 {level}（{chg:+.2f}%，{sigma:.2f}σ）'}

    # 自动起课（≥2σ 主触发 且 开关开 且 未起课）
    if AUTO_CAST_ENABLED and sigma >= 2.0:
        shichen = _shichen_of(now)
        r = record_cast(today, shichen, ev['event_id'], auto=True)
        if r.get('success'):
            out['cast'] = r['cast']
            out['note'] += f' → 已自动起课（{shichen}时）'
        else:
            out['note'] += f' → 自动起课跳过: {r.get("error")}'
    return out


# ── 起课录入（人工/自动，绝不瞎起课）──
def record_cast(date_str, shichen, event_id=None, auto=False):
    """事件起课录入：校验事件存在且强度>=1.5σ，铸真实一课并关联到事件。
    返回 {success, cast, message}。周期未到窗口的禁止项：不做任何自动落盘预测。
    """
    st = _store()
    # 定位事件
    ev = None
    if event_id:
        for e in st['events']:
            if e.get('event_id') == event_id:
                ev = e
                break
        if ev is None:
            return {'success': False, 'error': f'事件 {event_id} 不存在'}
    else:
        # 未指定事件：尝试按日期找；找不到则要求先检测
        cands = [e for e in st['events'] if e.get('date') == date_str]
        if not cands:
            return {'success': False, 'error': f'{date_str} 无已记录事件，请先调用检测'}
        ev = max(cands, key=lambda e: e.get('sigma', 0))
    if ev.get('sigma', 0) < 1.5:
        return {'success': False, 'error': f'事件强度 {ev["sigma"]}σ < 1.5σ，不构成起课条件'}
    if ev.get('cast_id'):
        return {'success': False, 'error': f'该事件已起课（{ev["cast_id"]}），一事一课'}

    # 铸真实一课（复用 liuren_20d_engine 起课路径，人工指定时辰）
    sys.path.insert(0, BASE)
    from liuren_20d_engine import get_liuren_20d_signal
    full = get_liuren_20d_signal(date_str, shichen, None)
    pred = (full or {}).get('prediction', {}) or {}
    bi = (full or {}).get('basic_info', {}) or {}
    cast = {
        'cast_id': f'EC-{date_str.replace("-","")}-{len(st["casts"])+1:02d}',
        'event_id': ev['event_id'],
        'date': date_str,
        'shichen': shichen,
        'auto': auto,
        'yuejiang': bi.get('yuejiang', ''),
        'prediction': {
            'trend': pred.get('trend', '--'),
            'confidence': pred.get('confidence', 0),
            'keti': (full or {}).get('keti', ''),
            'san_chuan': (full or {}).get('san_chuan', []),
            'reasons': pred.get('reasons', []),
        },
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'window_5d': {'settled': False},
        'window_20d': {'settled': False},
    }
    st['casts'].append(cast)
    ev['cast_id'] = cast['cast_id']
    ev['auto'] = auto
    _save(st)
    mode = '自动' if auto else '人工'
    return {'success': True, 'cast': cast, 'event': ev,
            'message': f'事件起课已记录 {cast["cast_id"]}（{mode}，{date_str} {shichen}时，{pred.get("trend","--")}）'}


# ── 评估：分方向条件基线对比 ──
def _compute_baselines():
    """动态 2σ 事件口径的条件基线（本地数据重算，诚实口径）。
    返回 {up: {5d: pct, 20d: pct}, down: {...}, n_up, n_down, range}
    """
    series = load_series()
    dates = [d for d, _ in series]
    closes = [c for _, c in series]
    N = len(series)
    # 滚动σ
    roll_sd = [None] * N
    for i in range(ROLL_WINDOW, N):
        win = closes[i-ROLL_WINDOW:i]
        rets = [(win[k]/win[k-1]-1)*100 for k in range(1, len(win))]
        roll_sd[i] = statistics.stdev(rets)
    up_ev, dn_ev = [], []
    for i in range(1, N):
        if roll_sd[i] is None:
            continue
        chg = (closes[i]/closes[i-1]-1)*100
        if abs(chg) >= 2.0 * roll_sd[i]:
            (up_ev if chg >= 0 else dn_ev).append(i)
    out = {'up': {}, 'down': {}, 'n_up': len(up_ev), 'n_down': len(dn_ev)}
    for tag, evs in (('up', up_ev), ('down', dn_ev)):
        for W in (5, 20):
            ups = tot = 0
            for i in evs:
                j = i + W
                if j >= N:
                    continue
                tot += 1
                if closes[j] > closes[i]:
                    ups += 1
            out[tag][f'{W}d'] = round(ups/tot*100, 1) if tot else None
    return out


def evaluate():
    """结算已到窗口的起课，分方向对比条件基线。只读，不落盘。"""
    st = _store()
    series = load_series()
    dates = [d for d, _ in series]
    closes = [c for _, c in series]
    idx = {d: i for i, d in enumerate(dates)}
    bl = _compute_baselines()
    results = []
    for c in st['casts']:
        ev = next((e for e in st['events'] if e.get('event_id') == c.get('event_id')), {})
        direction = ev.get('direction')
        for W in (5, 20):
            key = f'window_{W}d'
            if c.get(key, {}).get('settled'):
                continue
            di = idx.get(c.get('date'))
            if di is None or di + W >= len(dates):
                continue
            actual = 'up' if closes[di+W] > closes[di] else 'down'
            pred_trend = (c.get('prediction') or {}).get('trend', '')
            pred_dir = 'up' if pred_trend in ('看涨', '涨') else ('down' if pred_trend in ('看跌', '跌') else 'flat')
            hit = (pred_dir == actual) if pred_dir != 'flat' else None
            baseline = None
            if direction and bl.get(direction):
                baseline = bl[direction].get(f'{W}d')
            results.append({
                'cast_id': c['cast_id'], 'date': c['date'], 'event_dir': direction,
                'pred_trend': pred_trend, 'window': W, 'actual': actual, 'hit': hit,
                'baseline_pct': baseline,
            })
    return {'success': True, 'baselines': bl, 'settled': results}


# ── 查询 ──
def list_events(limit=50):
    st = _store()
    evs = sorted(st['events'], key=lambda e: e.get('date', ''), reverse=True)[:limit]
    return evs


def list_casts(limit=50):
    st = _store()
    cs = sorted(st['casts'], key=lambda c: c.get('created_at', ''), reverse=True)[:limit]
    return cs


def cmd_detect(date_str=None):
    r = detect_events(date_str)
    out = []
    for e in r.get('data', []):
        out.append(f"[{e['date']}] {e['name']} {e['change_pct']:+.2f}% "
                   f"({e['sigma']:.2f}σ/{e['level']}) 关联合约: {e['cast_id'] or '未起课'}")
    return '\n'.join(out) or r.get('note', '无事件')


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='事件驱动起课引擎')
    ap.add_argument('cmd', choices=['detect', 'casts', 'events', 'evaluate'],
                    help='detect[date] / casts / events / evaluate')
    ap.add_argument('date', nargs='?', default=None)
    a = ap.parse_args()
    if a.cmd == 'detect':
        print(cmd_detect(a.date))
    elif a.cmd == 'events':
        for e in list_events():
            print(f"{e['date']} {e['name']} {e['change_pct']:+.2f}% {e['sigma']:.2f}σ/{e['level']} 起课={e.get('cast_id') or '-'}")
    elif a.cmd == 'casts':
        for c in list_casts():
            print(f"{c['cast_id']} {c['date']} {c['shichen']}时 {(c.get('prediction') or {}).get('trend')}")
    elif a.cmd == 'evaluate':
        import json
        print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
