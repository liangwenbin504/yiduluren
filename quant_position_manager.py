"""
量化持仓管理器 — 虚拟交易系统·量化子系统
==============================================
从量化选股结果自动建仓、跟踪持仓、到期平仓、绩效统计。
买卖决策由11维因子评分独立驱动，不参考六壬信号。

交易规则:
- 买入阈值: score >= 50 (买入 + 强烈买入)
- 总资金: 100万，等权重分配
- 持仓周期: 5个交易日，到期自动平仓
- 止盈: +15%，止损: -8%
- 买入/卖出价格: 当日收盘价(Tencent/akshare)
- 数据文件: _memory/quant_portfolio.json
"""
import json, os, sys, subprocess, uuid
from datetime import datetime, date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / '_memory'
PORTFOLIO_FILE = MEMORY / 'quant_portfolio.json'
SCREENER_FILE = MEMORY / 'stock_screener_result.json'

# ── 配置 ──
DEFAULT_CONFIG = {
    'total_capital': 1_000_000.0,
    'hold_days': 5,
    'stop_profit': 0.15,
    'stop_loss': -0.08,
    'buy_threshold': 50,
    # ── 交易费用模型 (A股) ──
    'commission_rate': 0.00025,   # 佣金费率: 万2.5 (买入+卖出各收)
    'min_commission': 5.0,        # 单笔最低佣金: ¥5
    'stamp_tax_rate': 0.0005,     # 印花税: 千0.5 (仅卖出收取)
    'transfer_rate': 0.00001,     # 过户费: 万0.1 (仅沪市 sh 开头, 买入+卖出各收)
}

_ak = None


def calc_fees(code, price, shares, is_buy, config=None):
    """
    计算 A股 单边交易费用。

    返回 (commission, stamp_tax, transfer_fee, total) 四元组(已四舍五入2位)。
    - 佣金: amount * commission_rate, 但不低于 min_commission (买/卖各收)
    - 印花税: 仅卖出 amount * stamp_tax_rate
    - 过户费: 仅沪市(sh开头) amount * transfer_rate (买/卖各收)
    """
    config = config or DEFAULT_CONFIG
    amount = price * shares
    commission = max(amount * config.get('commission_rate', 0.00025),
                     config.get('min_commission', 5.0))
    stamp_tax = 0.0 if is_buy else amount * config.get('stamp_tax_rate', 0.0005)
    transfer_fee = 0.0
    if str(code).lower().startswith('sh'):
        transfer_fee = amount * config.get('transfer_rate', 0.00001)
    total = commission + stamp_tax + transfer_fee
    return round(commission, 2), round(stamp_tax, 2), round(transfer_fee, 2), round(total, 2)


def _get_ak():
    global _ak
    if _ak is None:
        try:
            import akshare as ak
            _ak = ak
        except ImportError:
            _ak = False
    return _ak if _ak is not False else None


def _tencent_quote(code):
    try:
        from tencent_market import tencent_quote as _tq
        r = _tq(code)
        if not r:
            return None
        return {
            'code': str(code),
            'name': r.get('name', ''),
            'price': r.get('price', 0.0),
            'prev_close': r.get('pre_close', 0.0),
            'open': r.get('open', 0.0),
            'change': r.get('change', 0.0),
            'high': r.get('high', 0.0),
            'low': r.get('low', 0.0),
        }
    except Exception as e:
        print(f'  [量化·行情] 腾讯获取{code}失败: {e}')
        return None


def get_stock_price(code):
    tq = _tencent_quote(code)
    if tq and tq.get('price', 0) > 0:
        return {
            'price': tq['price'],
            'change_pct': tq.get('change', 0.0),
            'name': tq.get('name', code),
            'open': tq.get('open', 0.0),
            'high': tq.get('high', 0.0),
            'low': tq.get('low', 0.0),
            'pre_close': tq.get('prev_close', 0.0),
        }

    ak = _get_ak()
    if ak:
        try:
            df = ak.stock_zh_a_spot()
            row = df[df['代码'] == str(code).zfill(6)]
            if not row.empty:
                r = row.iloc[0]
                return {
                    'price': float(r['最新价']),
                    'change_pct': float(r['涨跌幅']),
                    'name': str(r['名称']),
                    'open': float(r['今开']),
                    'high': float(r['最高']),
                    'low': float(r['最低']),
                    'pre_close': float(r['昨收']),
                }
        except Exception as e:
            print(f'  [量化·行情] akshare新浪源获取{code}失败: {e}')

    if ak:
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == str(code).zfill(6)]
            if not row.empty:
                r = row.iloc[0]
                return {
                    'price': float(r['最新价']),
                    'change_pct': float(r['涨跌幅']),
                    'name': str(r['名称']),
                    'open': float(r['今开']),
                    'high': float(r['最高']),
                    'low': float(r['最低']),
                    'pre_close': float(r['昨收']),
                }
        except Exception as e:
            print(f'  [量化·行情] akshare东方财富获取{code}失败: {e}')
    return None


def get_stock_close_price(code, target_date=None):
    if target_date is None:
        target_date = date.today()

    if target_date >= date.today():
        tq = _tencent_quote(code)
        if tq and tq.get('price', 0) > 0:
            return tq['price']

    try:
        from tencent_market import tencent_close_on
        hp = tencent_close_on(code, target_date)
        if hp and hp > 0:
            return hp
    except Exception as e:
        print(f'  [量化·收盘价] 腾讯获取{code} {target_date}失败: {e}')

    ak = _get_ak()
    if ak:
        try:
            end_date = target_date.strftime('%Y%m%d')
            start_date = (target_date - timedelta(days=30)).strftime('%Y%m%d')
            df = ak.stock_zh_a_hist(symbol=code, period='daily',
                                     start_date=start_date, end_date=end_date,
                                     adjust='qfq')
            if df is not None and not df.empty:
                row = df.iloc[-1]
                return float(row['收盘'])
        except Exception as e:
            print(f'  [量化·收盘价] akshare获取{code} {target_date}失败: {e}')

    tq = _tencent_quote(code)
    if tq and tq.get('price', 0) > 0:
        return tq['price']
    return None


def load_portfolio():
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}

    if 'config' not in data:
        data['config'] = dict(DEFAULT_CONFIG)
    if 'positions' not in data:
        data['positions'] = []
    if 'closed_trades' not in data:
        data['closed_trades'] = []
    if 'cash' not in data:
        data['cash'] = data['config'].get('total_capital', 1_000_000.0)

    for k, v in DEFAULT_CONFIG.items():
        if k not in data['config']:
            data['config'][k] = v

    return data


def save_portfolio(data):
    MEMORY.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_screener_results():
    if not SCREENER_FILE.exists():
        print('  [量化持仓] 暂无选股结果文件')
        return []

    with open(SCREENER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data.get('results', [])
    if not results:
        print('  [量化持仓] 选股结果为空')
    return results


def add_trading_days(start_date, n):
    d = start_date
    count = 0
    while count < n:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            count += 1
    return d


def build_positions(today_str=None):
    """
    量化自动建仓: 读取选股结果，对 score >= 50 的个股全部买入。
    纯量化因子驱动，不参考六壬信号。
    """
    if today_str is None:
        today_str = date.today().isoformat()

    portfolio = load_portfolio()
    config = portfolio['config']
    threshold = config['buy_threshold']

    screener = load_screener_results()
    if not screener:
        return {'success': False, 'message': '无选股结果', 'trades': []}

    buy_list = [s for s in screener if s['score'] >= threshold]

    if not buy_list:
        print(f'  [量化建仓] 选股结果中无 score >= {threshold} 的标的，跳过')
        return {'success': True, 'message': f'无符合条件的标的(score >= {threshold})', 'trades': []}

    total_capital = config['total_capital']
    per_stock_capital = total_capital / len(buy_list)

    existing_codes = {p['code'] for p in portfolio['positions'] if p.get('status') == 'holding'}

    trades = []
    batch_id = today_str

    for stock in buy_list:
        code = stock['code']
        name = stock['name']
        score = stock['score']
        advice = stock['advice']

        if code in existing_codes:
            print(f'  [量化建仓] {name}({code}) 已有持仓，跳过')
            continue

        price_data = get_stock_close_price(code)
        if price_data is None:
            print(f'  [量化建仓] {name}({code}) 无法获取价格，跳过')
            continue

        price = price_data
        shares = int(per_stock_capital / price / 100) * 100
        if shares < 100:
            print(f'  [量化建仓] {name}({code}) 资金不足买1手，跳过 (单价{price})')
            continue

        amount = shares * price
        _, _, _, buy_fee = calc_fees(code, price, shares, True, config)
        buy_time = f'{today_str} 15:00:00'
        hold_until = add_trading_days(date.fromisoformat(today_str), config['hold_days']).isoformat()

        pos = {
            'id': f'{today_str.replace("-","")}-{code}',
            'batch': batch_id,
            'code': code,
            'name': name,
            'buy_price': round(price, 2),
            'shares': shares,
            'amount': round(amount, 2),
            'buy_fee': buy_fee,
            'buy_time': buy_time,
            'advice': advice,
            'score': score,
            'status': 'holding',
            'hold_until': hold_until,
            'current_price': round(price, 2),
            'pnl': 0.0,
            'pnl_pct': 0.0,
            'close_price': None,
            'close_time': None,
            'close_reason': None,
            'daily_pnl_log': [],
            'source': 'quant',
            'subsystem': '量化',
        }

        portfolio['positions'].append(pos)
        existing_codes.add(code)
        trades.append(pos)
        print(f'  [量化建仓] ✅ {name}({code}) {advice}(分{score}) 买入{shares}股 @ {price} 金额{amount:.0f}')

    portfolio.setdefault('stats', {})
    portfolio['stats']['last_build'] = today_str
    portfolio['stats']['total_builds'] = portfolio['stats'].get('total_builds', 0) + 1

    save_portfolio(portfolio)
    return {
        'success': True,
        'message': f'量化建仓完成: {len(trades)}/{len(buy_list)} 只',
        'trades': trades
    }


def manual_buy(code, name, shares, price=None, advice='手动买入', score=0):
    portfolio = load_portfolio()

    if price is None:
        price_data = get_stock_price(code)
        if price_data is None:
            return {'success': False, 'message': f'无法获取{code}价格'}
        price = price_data['price']
        if not name:
            name = price_data.get('name', code)

    today_str = date.today().isoformat()
    config = portfolio['config']

    existing = [p for p in portfolio['positions'] if p['code'] == code and p.get('status') == 'holding']
    if existing:
        return {'success': False, 'message': f'{name}({code})已有持仓'}

    amount = shares * price
    _, _, _, buy_fee = calc_fees(code, price, shares, True, config)
    pos = {
        'id': f'{today_str.replace("-","")}-{code}-manual-{uuid.uuid4().hex[:6]}',
        'batch': today_str,
        'code': code,
        'name': name,
        'buy_price': round(price, 2),
        'shares': shares,
        'amount': round(amount, 2),
        'buy_fee': buy_fee,
        'buy_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'advice': advice,
        'score': score,
        'status': 'holding',
        'hold_until': add_trading_days(date.fromisoformat(today_str), portfolio['config']['hold_days']).isoformat(),
        'current_price': round(price, 2),
        'pnl': 0.0,
        'pnl_pct': 0.0,
        'close_price': None,
        'close_time': None,
        'close_reason': None,
        'daily_pnl_log': [],
        'source': 'manual',
        'subsystem': '量化',
    }

    portfolio['positions'].append(pos)
    save_portfolio(portfolio)
    print(f'  [量化·手动买入] ✅ {name}({code}) {shares}股 @ {price} 金额{amount:.0f}')
    return {'success': True, 'message': f'买入{name}({code}) {shares}股', 'trade': pos}


def manual_sell(position_id, price=None):
    portfolio = load_portfolio()

    pos = None
    for p in portfolio['positions']:
        if p['id'] == position_id and p.get('status') == 'holding':
            pos = p
            break

    if pos is None:
        return {'success': False, 'message': f'未找到持仓 {position_id}'}

    if price is None:
        price_data = get_stock_price(pos['code'])
        if price_data is None:
            return {'success': False, 'message': f'无法获取{pos["code"]}价格'}
        price = price_data['price']

    close_price = round(price, 2)
    gross_pnl = (close_price - pos['buy_price']) * pos['shares']
    buy_fee = pos.get('buy_fee', 0.0)
    _, _, _, sell_fee = calc_fees(pos['code'], close_price, pos['shares'], False, portfolio['config'])
    net_pnl = gross_pnl - buy_fee - sell_fee
    invested = pos['buy_price'] * pos['shares'] + buy_fee
    pnl = round(net_pnl, 2)
    pnl_pct = round(net_pnl / invested * 100, 2) if invested > 0 else 0

    pos['status'] = 'closed'
    pos['close_price'] = close_price
    pos['close_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pos['close_reason'] = '手动平仓'
    pos['sell_fee'] = sell_fee
    pos['total_fee'] = round(buy_fee + sell_fee, 2)
    pos['pnl'] = pnl
    pos['pnl_pct'] = pnl_pct

    portfolio['closed_trades'].append(pos)
    portfolio['positions'] = [p for p in portfolio['positions'] if p['id'] != position_id]

    save_portfolio(portfolio)
    print(f'  [量化·手动平仓] {pos["name"]}({pos["code"]}) @ {close_price} 盈亏{pnl:.0f}({pnl_pct:+.2f}%)')
    return {'success': True, 'message': f'平仓{pos["name"]} 盈亏{pnl:.0f}', 'trade': pos}


def close_positions(today_str=None):
    if today_str is None:
        today_str = date.today().isoformat()

    portfolio = load_portfolio()
    config = portfolio['config']
    holding = [p for p in portfolio['positions'] if p.get('status') == 'holding']

    if not holding:
        return {'success': True, 'message': '无持仓', 'closed': []}

    closed = []
    for pos in holding:
        code = pos['code']
        price_data = get_stock_close_price(code, date.fromisoformat(today_str))

        if price_data is None:
            print(f'  [量化平仓] {pos["name"]}({code}) 无法获取价格，跳过')
            continue

        current_price = price_data
        gross = (current_price - pos['buy_price']) * pos['shares']
        buy_fee = pos.get('buy_fee', 0.0)
        _, _, _, sell_fee = calc_fees(code, current_price, pos['shares'], False, config)
        net = gross - buy_fee - sell_fee
        invested = pos['buy_price'] * pos['shares'] + buy_fee
        pnl_pct = net / invested if invested > 0 else 0

        pos['current_price'] = round(current_price, 2)
        pos['pnl'] = round(net, 2)
        pos['pnl_pct'] = round(pnl_pct * 100, 2)

        reason = None
        if pnl_pct >= config['stop_profit']:
            reason = f'止盈 (+{pnl_pct*100:.1f}%)'
        elif pnl_pct <= config['stop_loss']:
            reason = f'止损 ({pnl_pct*100:.1f}%)'
        elif today_str >= pos.get('hold_until', '9999-12-31'):
            reason = '到期'

        if reason:
            pos['status'] = 'closed'
            pos['close_price'] = round(current_price, 2)
            pos['close_time'] = f'{today_str} 15:00:00'
            pos['close_reason'] = reason
            pos['sell_fee'] = sell_fee
            pos['total_fee'] = round(buy_fee + sell_fee, 2)
            pos['pnl'] = round(net, 2)
            pos['pnl_pct'] = round(pnl_pct * 100, 2)

            portfolio['closed_trades'].append(pos)
            closed.append(pos)
            print(f'  [量化平仓] {pos["name"]}({code}) {reason} @ {current_price} 盈亏{pos["pnl"]:.0f}({pos["pnl_pct"]:+.2f}%)')

    portfolio['positions'] = [p for p in portfolio['positions'] if p.get('status') == 'holding']
    save_portfolio(portfolio)

    return {
        'success': True,
        'message': f'量化平仓完成: {len(closed)} 笔',
        'closed': closed
    }


def update_daily_pnl(today_str=None):
    if today_str is None:
        today_str = date.today().isoformat()

    portfolio = load_portfolio()
    holding = [p for p in portfolio['positions'] if p.get('status') == 'holding']

    updated = 0
    for pos in holding:
        price_data = get_stock_close_price(pos['code'], date.fromisoformat(today_str))
        if price_data is None:
            continue

        current_price = price_data
        pnl_pct = (current_price - pos['buy_price']) / pos['buy_price']

        pos['current_price'] = round(current_price, 2)
        pos['pnl_pct'] = round(pnl_pct * 100, 2)
        pos['pnl'] = round((current_price - pos['buy_price']) * pos['shares'], 2)

        pos.setdefault('daily_pnl_log', []).append({
            'date': today_str,
            'price': round(current_price, 2),
            'pnl': pos['pnl'],
            'pnl_pct': pos['pnl_pct']
        })
        updated += 1

    if updated:
        save_portfolio(portfolio)
        print(f'  [量化·日盈亏] {updated} 只持仓已更新')

    return {'success': True, 'updated': updated}


def get_positions():
    portfolio = load_portfolio()
    holding = [p for p in portfolio['positions'] if p.get('status') == 'holding']
    closed = portfolio.get('closed_trades', [])
    config = portfolio.get('config', DEFAULT_CONFIG)

    total_cost = sum(p.get('amount', 0) for p in holding)
    total_invested = sum(p.get('amount', 0) + p.get('buy_fee', 0) for p in holding)
    total_pnl = sum(p.get('pnl', 0) for p in holding)
    total_market_value = sum(
        (p.get('current_price', p.get('buy_price', 0)) * p.get('shares', 0))
        for p in holding
    )
    # 累计交易费用 = 在持买入费 + 已平买卖费
    total_fees = round(
        sum(p.get('buy_fee', 0) for p in holding)
        + sum((t.get('buy_fee', 0) + t.get('sell_fee', 0)) for t in closed),
        2,
    )

    return {
        'subsystem': '量化',
        'config': config,
        'positions': holding,
        'closed_trades': closed[-50:],
        'summary': {
            'holding_count': len(holding),
            'closed_count': len(closed),
            'total_cost': round(total_cost, 2),
            'total_invested': round(total_invested, 2),
            'total_market_value': round(total_market_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl / total_invested * 100, 2) if total_invested > 0 else 0,
            'total_fees': total_fees,
        }
    }


def get_performance():
    portfolio = load_portfolio()
    closed = portfolio.get('closed_trades', [])
    config = portfolio.get('config', DEFAULT_CONFIG)

    if not closed:
        return {
            'subsystem': '量化',
            'total_trades': 0,
            'message': '尚无平仓记录，需累积数据'
        }

    total = len(closed)
    wins = [t for t in closed if t.get('pnl', 0) > 0]
    losses = [t for t in closed if t.get('pnl', 0) < 0]
    draws = [t for t in closed if t.get('pnl', 0) == 0]

    win_rate = len(wins) / total * 100 if total > 0 else 0

    avg_return = sum(t.get('pnl_pct', 0) for t in closed) / total if total > 0 else 0
    avg_win = sum(t.get('pnl_pct', 0) for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.get('pnl_pct', 0) for t in losses) / len(losses) if losses else 0

    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')

    by_advice = {}
    for t in closed:
        advice = t.get('advice', '未知')
        if advice not in by_advice:
            by_advice[advice] = {'trades': 0, 'wins': 0, 'total_pnl_pct': 0, 'total_pnl': 0}
        by_advice[advice]['trades'] += 1
        pnl = t.get('pnl', 0)
        pnl_pct = t.get('pnl_pct', 0)
        if pnl > 0:
            by_advice[advice]['wins'] += 1
        by_advice[advice]['total_pnl_pct'] += pnl_pct
        by_advice[advice]['total_pnl'] += pnl

    for k, v in by_advice.items():
        v['win_rate'] = round(v['wins'] / v['trades'] * 100, 1) if v['trades'] > 0 else 0
        v['avg_return'] = round(v['total_pnl_pct'] / v['trades'], 2) if v['trades'] > 0 else 0
        v['avg_pnl'] = round(v['total_pnl'] / v['trades'], 2) if v['trades'] > 0 else 0

    by_source = {}
    for t in closed:
        src = t.get('source', 'quant')
        if src not in by_source:
            by_source[src] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        by_source[src]['trades'] += 1
        if t.get('pnl', 0) > 0:
            by_source[src]['wins'] += 1
        by_source[src]['total_pnl'] += t.get('pnl', 0)

    for k, v in by_source.items():
        v['win_rate'] = round(v['wins'] / v['trades'] * 100, 1) if v['trades'] > 0 else 0

    monthly_pnl = {}
    for t in closed:
        close_time = t.get('close_time', '')
        if close_time:
            month = close_time[:7]
            if month not in monthly_pnl:
                monthly_pnl[month] = 0
            monthly_pnl[month] += t.get('pnl', 0)

    total_pnl = sum(t.get('pnl', 0) for t in closed)
    total_pnl_pct = sum(t.get('pnl_pct', 0) for t in closed)
    # 累计交易费用 与 毛盈亏(未扣费) 对照
    total_fees = round(sum((t.get('buy_fee', 0) + t.get('sell_fee', 0)) for t in closed), 2)
    total_gross_pnl = round(sum(t.get('pnl', 0) + t.get('buy_fee', 0) + t.get('sell_fee', 0) for t in closed), 2)

    cumulative = 0
    max_cumulative = 0
    max_drawdown = 0
    for t in sorted(closed, key=lambda x: x.get('close_time', '')):
        cumulative += t.get('pnl', 0)
        max_cumulative = max(max_cumulative, cumulative)
        max_drawdown = min(max_drawdown, cumulative - max_cumulative)

    hold_days_dist = {}
    for t in closed:
        close_reason = t.get('close_reason', '未知')
        if close_reason not in hold_days_dist:
            hold_days_dist[close_reason] = 0
        hold_days_dist[close_reason] += 1

    return {
        'subsystem': '量化',
        'total_trades': total,
        'win_count': len(wins),
        'loss_count': len(losses),
        'draw_count': len(draws),
        'win_rate': round(win_rate, 1),
        'avg_return_pct': round(avg_return, 2),
        'avg_win_pct': round(avg_win, 2),
        'avg_loss_pct': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else None,
        'total_pnl': round(total_pnl, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'total_gross_pnl': total_gross_pnl,
        'total_fees': total_fees,
        'max_drawdown': round(max_drawdown, 2),
        'by_advice': by_advice,
        'by_source': by_source,
        'monthly_pnl': monthly_pnl,
        'close_reasons': hold_days_dist,
        'config': config,
    }


def daily_run(today_str=None):
    if today_str is None:
        today_str = date.today().isoformat()

    if date.fromisoformat(today_str).weekday() >= 5:
        print(f'  ⏭ [量化] 周末休市({today_str})，跳过')
        return {'build': {'message': '周末跳过'}, 'close': {'message': '周末跳过'}}

    print(f'\n{"="*50}')
    print(f'  [量化持仓管理] {today_str}')
    print(f'{"="*50}')

    print('\n  ▶ 检查持仓平仓...')
    close_result = close_positions(today_str)

    print('\n  ▶ 更新当日盈亏...')
    update_daily_pnl(today_str)

    print('\n  ▶ 自动建仓...')
    build_result = build_positions(today_str)

    print(f'\n  ✅ [量化] 完成: 建仓{build_result.get("message","")} | {close_result.get("message","")}')

    return {
        'subsystem': '量化',
        'build': build_result,
        'close': close_result,
    }


# ── 命令行 ──
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='量化持仓管理器')
    parser.add_argument('--build', action='store_true', help='仅建仓')
    parser.add_argument('--close', action='store_true', help='仅平仓')
    parser.add_argument('--update', action='store_true', help='仅更新盈亏')
    parser.add_argument('--daily', action='store_true', help='每日完整流程')
    parser.add_argument('--stats', action='store_true', help='绩效统计')
    parser.add_argument('--list', action='store_true', help='列出持仓')
    args = parser.parse_args()

    if args.daily:
        daily_run()
    elif args.build:
        build_positions()
    elif args.close:
        close_positions()
    elif args.update:
        update_daily_pnl()
    elif args.stats:
        perf = get_performance()
        print(json.dumps(perf, ensure_ascii=False, indent=2))
    elif args.list:
        positions = get_positions()
        print(json.dumps(positions, ensure_ascii=False, indent=2))
    else:
        daily_run()
