"""
选股持仓管理器 - 虚拟交易系统核心模块
==============================================
从量化选股结果自动建仓、跟踪持仓、到期平仓、绩效统计。
双轨并行：自动建仓 + 支持手动买入/平仓。

交易规则:
- 买入阈值: score >= 50 (买入 + 强烈买入)
- 总资金: 100万，等权重分配
- 持仓周期: 5个交易日，到期自动平仓
- 止盈: +15%，止损: -8%
- 买入价格: 当日收盘价(从akshare获取)
- 卖出价格: 平仓时当日收盘价
"""
import json, os, sys, subprocess, uuid
from datetime import datetime, date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / '_memory'
PORTFOLIO_FILE = MEMORY / 'screener_portfolio.json'
SCREENER_FILE = MEMORY / 'stock_screener_result.json'

# ── 配置 ──
DEFAULT_CONFIG = {
    'total_capital': 1_000_000.0,
    'hold_days': 5,
    'stop_profit': 0.15,
    'stop_loss': -0.08,
    'buy_threshold': 50,  # score >= 50 自动建仓
}

# akshare 缓存
_ak = None


def _get_ak():
    """延迟加载 akshare"""
    global _ak
    if _ak is None:
        try:
            import akshare as ak
            _ak = ak
        except ImportError:
            _ak = False
    return _ak if _ak is not False else None


def _tencent_quote(code):
    """
    腾讯单股实时行情（委托 tencent_market 共享模块，统一行情源）。
    返回 dict: {code, name, price, prev_close, open, change, high, low}
    """
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
        print(f'  [行情] 腾讯获取{code}失败: {e}')
        return None


def get_stock_price(code):
    """
    获取个股最新价格。
    返回 dict: {price, change_pct, name, open, high, low, pre_close} 或 None。
    """
    # 方案1：腾讯单股API（轻量，本环境稳定可用）
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

    # 方案2：akshare 新浪源（全量）
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
            print(f'  [行情] akshare新浪源获取{code}失败: {e}')

    # 方案3：akshare 东方财富（本环境常被限流/断连，作最后兜底）
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
            print(f'  [行情] akshare东方财富获取{code}失败: {e}')
    return None


def get_stock_close_price(code, target_date=None):
    """
    获取个股指定日期的收盘价。
    如果 target_date 为 None 或为今天，取腾讯实时价（盘后即当日收盘价）。
    历史日期优先用 akshare 日线，失败则降级腾讯实时价。
    """
    if target_date is None:
        target_date = date.today()

    # 今天或未来日期 → 直接用腾讯实时价（盘后即为收盘价，最稳）
    if target_date >= date.today():
        tq = _tencent_quote(code)
        if tq and tq.get('price', 0) > 0:
            return tq['price']

    # 历史日期 → 腾讯日K线（准确历史收盘，主源）
    try:
        from tencent_market import tencent_close_on
        hp = tencent_close_on(code, target_date)
        if hp and hp > 0:
            return hp
    except Exception as e:
        print(f'  [收盘价] 腾讯获取{code} {target_date}失败: {e}')

    # 兜底：akshare 东方财富日线（本环境常被掐断）
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
            print(f'  [收盘价] akshare获取{code} {target_date}失败: {e}')

    # 最后兜底：腾讯实时价（不精确，仅防崩溃）
    tq = _tencent_quote(code)
    if tq and tq.get('price', 0) > 0:
        return tq['price']
    return None


def load_portfolio():
    """加载持仓数据"""
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
    
    # 确保有默认配置
    if 'config' not in data:
        data['config'] = dict(DEFAULT_CONFIG)
    if 'positions' not in data:
        data['positions'] = []
    if 'closed_trades' not in data:
        data['closed_trades'] = []
    if 'cash' not in data:
        data['cash'] = data['config'].get('total_capital', 1_000_000.0)
    
    # 兼容旧版: 确保 config 有所有字段
    for k, v in DEFAULT_CONFIG.items():
        if k not in data['config']:
            data['config'][k] = v
    
    return data


def save_portfolio(data):
    """保存持仓数据"""
    MEMORY.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_screener_results():
    """加载最新选股结果"""
    if not SCREENER_FILE.exists():
        print('  [选股持仓] 暂无选股结果文件')
        return []
    
    with open(SCREENER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    if not results:
        print('  [选股持仓] 选股结果为空')
    return results


def build_positions(today_str=None):
    """
    自动建仓: 读取选股结果，对 score >= 50 的个股生成虚拟买单。
    
    规则:
    - 每只股票等权重分配资金
    - 使用当日收盘价作为买入价格
    - 同一批次(batch)的持仓到期日相同
    - 不会重复买入已有持仓的股票
    """
    if today_str is None:
        today_str = date.today().isoformat()
    
    portfolio = load_portfolio()
    config = portfolio['config']
    threshold = config['buy_threshold']
    total_capital = config['total_capital']
    
    screener = load_screener_results()
    if not screener:
        return {'success': False, 'message': '无选股结果', 'trades': []}
    
    # 筛选买入标的
    buy_list = [s for s in screener if s['score'] >= threshold]
    
    if not buy_list:
        print(f'  [自动建仓] 选股结果中无 score >= {threshold} 的标的，跳过')
        return {'success': True, 'message': f'无符合条件的标的(score >= {threshold})', 'trades': []}
    
    # 等权重分配
    per_stock_capital = total_capital / len(buy_list)
    
    # 获取已有持仓的股票代码
    existing_codes = {p['code'] for p in portfolio['positions'] if p.get('status') == 'holding'}
    
    trades = []
    batch_id = today_str
    
    for stock in buy_list:
        code = stock['code']
        name = stock['name']
        score = stock['score']
        advice = stock['advice']
        
        if code in existing_codes:
            print(f'  [自动建仓] {name}({code}) 已有持仓，跳过')
            continue
        
        # 获取价格
        price_data = get_stock_close_price(code)
        if price_data is None:
            print(f'  [自动建仓] {name}({code}) 无法获取价格，跳过')
            continue
        
        price = price_data
        shares = int(per_stock_capital / price / 100) * 100  # 整手
        if shares < 100:
            print(f'  [自动建仓] {name}({code}) 资金不足买1手，跳过 (单价{price}, 资金{per_stock_capital:.0f})')
            continue
        
        amount = shares * price
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
            'source': 'auto'
        }
        
        portfolio['positions'].append(pos)
        existing_codes.add(code)
        trades.append(pos)
        print(f'  [自动建仓] ✅ {name}({code}) {advice} 买入{shares}股 @ {price} 金额{amount:.0f}')
    
    portfolio.setdefault('stats', {})
    portfolio['stats']['last_build'] = today_str
    portfolio['stats']['total_builds'] = portfolio['stats'].get('total_builds', 0) + 1
    
    save_portfolio(portfolio)
    return {
        'success': True,
        'message': f'建仓完成: {len(trades)}/{len(buy_list)} 只',
        'trades': trades
    }


def manual_buy(code, name, shares, price=None, advice='手动买入', score=0):
    """
    手动买入某只股票。
    """
    portfolio = load_portfolio()
    
    if price is None:
        price_data = get_stock_price(code)
        if price_data is None:
            return {'success': False, 'message': f'无法获取{code}价格'}
        price = price_data['price']
        if not name:
            name = price_data.get('name', code)
    
    today_str = date.today().isoformat()
    
    # 检查是否已有持仓
    existing = [p for p in portfolio['positions'] if p['code'] == code and p.get('status') == 'holding']
    if existing:
        return {'success': False, 'message': f'{name}({code})已有持仓'}
    
    amount = shares * price
    pos = {
        'id': f'{today_str.replace("-","")}-{code}-manual-{uuid.uuid4().hex[:6]}',
        'batch': today_str,
        'code': code,
        'name': name,
        'buy_price': round(price, 2),
        'shares': shares,
        'amount': round(amount, 2),
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
        'source': 'manual'
    }
    
    portfolio['positions'].append(pos)
    save_portfolio(portfolio)
    print(f'  [手动买入] ✅ {name}({code}) {shares}股 @ {price} 金额{amount:.0f}')
    return {'success': True, 'message': f'买入{name}({code}) {shares}股', 'trade': pos}


def manual_sell(position_id, price=None):
    """
    手动平仓某只持仓。
    """
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
    pnl = round((close_price - pos['buy_price']) * pos['shares'], 2)
    pnl_pct = round((close_price - pos['buy_price']) / pos['buy_price'] * 100, 2)
    
    pos['status'] = 'closed'
    pos['close_price'] = close_price
    pos['close_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pos['close_reason'] = '手动平仓'
    pos['pnl'] = pnl
    pos['pnl_pct'] = pnl_pct
    
    # 移到已平仓列表
    portfolio['closed_trades'].append(pos)
    portfolio['positions'] = [p for p in portfolio['positions'] if p['id'] != position_id]
    
    save_portfolio(portfolio)
    print(f'  [手动平仓] {pos["name"]}({pos["code"]}) @ {close_price} 盈亏{pnl:.0f}({pnl_pct:+.2f}%)')
    return {'success': True, 'message': f'平仓{pos["name"]} 盈亏{pnl:.0f}', 'trade': pos}


def close_positions(today_str=None):
    """
    自动平仓: 检查所有持仓，到期/止盈/止损则自动平仓。
    """
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
            print(f'  [自动平仓] {pos["name"]}({code}) 无法获取价格，跳过')
            continue
        
        current_price = price_data
        pnl_pct = (current_price - pos['buy_price']) / pos['buy_price']
        
        # 更新当前价格和盈亏
        pos['current_price'] = round(current_price, 2)
        pos['pnl_pct'] = round(pnl_pct * 100, 2)
        pos['pnl'] = round((current_price - pos['buy_price']) * pos['shares'], 2)
        
        # 判断是否需要平仓
        reason = None
        
        # 止盈
        if pnl_pct >= config['stop_profit']:
            reason = f'止盈 (+{pnl_pct*100:.1f}%)'
        # 止损
        elif pnl_pct <= config['stop_loss']:
            reason = f'止损 ({pnl_pct*100:.1f}%)'
        # 到期
        elif today_str >= pos.get('hold_until', '9999-12-31'):
            reason = '到期'
        
        if reason:
            pos['status'] = 'closed'
            pos['close_price'] = round(current_price, 2)
            pos['close_time'] = f'{today_str} 15:00:00'
            pos['close_reason'] = reason
            pos['pnl'] = round((current_price - pos['buy_price']) * pos['shares'], 2)
            pos['pnl_pct'] = round(pnl_pct * 100, 2)
            
            portfolio['closed_trades'].append(pos)
            closed.append(pos)
            print(f'  [自动平仓] {pos["name"]}({code}) {reason} @ {current_price} 盈亏{pos["pnl"]:.0f}({pos["pnl_pct"]:+.2f}%)')
    
    # 移除已平仓的
    portfolio['positions'] = [p for p in portfolio['positions'] if p.get('status') == 'holding']
    save_portfolio(portfolio)
    
    return {
        'success': True,
        'message': f'平仓完成: {len(closed)} 笔',
        'closed': closed
    }


def update_daily_pnl(today_str=None):
    """
    更新当日持仓盈亏（不触发平仓，仅更新浮动盈亏）。
    """
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
        
        # 记录每日盈亏
        pos.setdefault('daily_pnl_log', []).append({
            'date': today_str,
            'price': round(current_price, 2),
            'pnl': pos['pnl'],
            'pnl_pct': pos['pnl_pct']
        })
        updated += 1
    
    if updated:
        save_portfolio(portfolio)
        print(f'  [日盈亏更新] {updated} 只持仓已更新')
    
    return {'success': True, 'updated': updated}


def get_positions():
    """获取当前持仓列表"""
    portfolio = load_portfolio()
    holding = [p for p in portfolio['positions'] if p.get('status') == 'holding']
    closed = portfolio.get('closed_trades', [])
    config = portfolio.get('config', DEFAULT_CONFIG)
    
    # 汇总统计
    total_cost = sum(p.get('amount', 0) for p in holding)
    total_pnl = sum(p.get('pnl', 0) for p in holding)
    total_market_value = sum(
        (p.get('current_price', p.get('buy_price', 0)) * p.get('shares', 0))
        for p in holding
    )
    
    return {
        'config': config,
        'positions': holding,
        'closed_trades': closed[-50:],  # 最近50笔平仓
        'summary': {
            'holding_count': len(holding),
            'closed_count': len(closed),
            'total_cost': round(total_cost, 2),
            'total_market_value': round(total_market_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0,
        }
    }


def get_performance():
    """
    绩效统计: 胜率、平均收益、最大回撤、月度收益等。
    用于三个月复盘分析。
    """
    portfolio = load_portfolio()
    closed = portfolio.get('closed_trades', [])
    config = portfolio.get('config', DEFAULT_CONFIG)
    
    if not closed:
        return {
            'total_trades': 0,
            'message': '尚无平仓记录，需累积数据'
        }
    
    # 基础统计
    total = len(closed)
    wins = [t for t in closed if t.get('pnl', 0) > 0]
    losses = [t for t in closed if t.get('pnl', 0) < 0]
    draws = [t for t in closed if t.get('pnl', 0) == 0]
    
    win_rate = len(wins) / total * 100 if total > 0 else 0
    
    avg_return = sum(t.get('pnl_pct', 0) for t in closed) / total if total > 0 else 0
    avg_win = sum(t.get('pnl_pct', 0) for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.get('pnl_pct', 0) for t in losses) / len(losses) if losses else 0
    
    # 盈亏比
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    # 按建议分档
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
    
    # 按来源分档
    by_source = {}
    for t in closed:
        src = t.get('source', 'auto')
        if src not in by_source:
            by_source[src] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        by_source[src]['trades'] += 1
        if t.get('pnl', 0) > 0:
            by_source[src]['wins'] += 1
        by_source[src]['total_pnl'] += t.get('pnl', 0)
    
    for k, v in by_source.items():
        v['win_rate'] = round(v['wins'] / v['trades'] * 100, 1) if v['trades'] > 0 else 0
    
    # 月度收益（按平仓时间）
    monthly_pnl = {}
    for t in closed:
        close_time = t.get('close_time', '')
        if close_time:
            month = close_time[:7]  # YYYY-MM
            if month not in monthly_pnl:
                monthly_pnl[month] = 0
            monthly_pnl[month] += t.get('pnl', 0)
    
    # 总盈亏
    total_pnl = sum(t.get('pnl', 0) for t in closed)
    total_pnl_pct = sum(t.get('pnl_pct', 0) for t in closed)
    
    # 最大回撤（按平仓顺序累计盈亏）
    cumulative = 0
    max_cumulative = 0
    max_drawdown = 0
    for t in sorted(closed, key=lambda x: x.get('close_time', '')):
        cumulative += t.get('pnl', 0)
        max_cumulative = max(max_cumulative, cumulative)
        max_drawdown = min(max_drawdown, cumulative - max_cumulative)
    
    # 持仓周期分布
    hold_days_dist = {}
    for t in closed:
        close_reason = t.get('close_reason', '未知')
        if close_reason not in hold_days_dist:
            hold_days_dist[close_reason] = 0
        hold_days_dist[close_reason] += 1
    
    return {
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
        'max_drawdown': round(max_drawdown, 2),
        'by_advice': by_advice,
        'by_source': by_source,
        'monthly_pnl': monthly_pnl,
        'close_reasons': hold_days_dist,
        'config': config,
    }


def add_trading_days(start_date, n):
    """
    从 start_date 的次日算起，往后数满 n 个交易日（跳过周六、周日）。
    用于计算持仓到期日，保证周期恒定 = n 个交易日，不随买入星期几漂移。
    """
    d = start_date
    count = 0
    while count < n:
        d = d + timedelta(days=1)
        if d.weekday() < 5:  # 0=周一 ... 4=周五
            count += 1
    return d


def daily_run(today_str=None):
    """
    每日运行入口: 建仓 → 平仓 → 更新盈亏。
    供 auto_scheduler.py 在盘后调用。
    """
    if today_str is None:
        today_str = date.today().isoformat()
    
    # 周末休市：无新行情、无新选股，跳过建仓/平仓/盈亏更新，
    # 避免用周五冻结价平仓、避免重复建仓。
    if date.fromisoformat(today_str).weekday() >= 5:
        print(f'  ⏭ 周末休市({today_str})，跳过持仓管理')
        return {'build': {'message': '周末跳过'}, 'close': {'message': '周末跳过'}}
    
    print(f'\n{"="*50}')
    print(f'  [选股持仓管理] {today_str}')
    print(f'{"="*50}')
    
    # 1. 先检查是否需要平仓
    print('\n  ▶ 检查持仓平仓...')
    close_result = close_positions(today_str)
    
    # 2. 更新当日浮动盈亏
    print('\n  ▶ 更新当日盈亏...')
    update_daily_pnl(today_str)
    
    # 3. 自动建仓
    print('\n  ▶ 自动建仓...')
    build_result = build_positions(today_str)
    
    print(f'\n  ✅ 完成: 建仓{build_result.get("message","")} | {close_result.get("message","")}')
    
    return {
        'build': build_result,
        'close': close_result,
    }


# ── 命令行 ──
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='选股持仓管理器')
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
