"""
虚拟股票投资组合 — 100,000元模拟炒股系统
实时跟踪上证指数，自动计算盈亏

用法:
  python virtual_portfolio.py                 # 显示当前持仓盈亏
  python virtual_portfolio.py init            # 初始化/重置100,000元
  python virtual_portfolio.py buy [数量]      # 加仓（默认1份=10,000元）
  python virtual_portfolio.py sell [数量]     # 减仓
  python virtual_portfolio.py history         # 查看交易历史
"""
import json, os, sys, math, re
from datetime import datetime, timezone, timedelta
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE, "_memory", "virtual_portfolio.json")

HAS_AKSHARE = False
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    pass


def get_index_price():
    """获取上证指数最新价格"""
    if not HAS_AKSHARE:
        return None, "akshare未安装"
    try:
        df = ak.stock_zh_index_spot_em()
        sh = df[df["名称"] == "上证指数"]
        if not sh.empty:
            row = sh.iloc[0]
            return {
                "price": float(row["最新价"]),
                "change_pct": float(row["涨跌幅"]),
                "change_amount": float(row["涨跌额"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["今开"]),
                "prev_close": float(row["昨收"]),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }, None
        return None, "未找到上证指数"
    except Exception as e:
        return None, f"获取失败: {e}"


def init_portfolio():
    """初始化100,000元投资组合"""
    portfolio = {
        "initial_capital": 100000.0,
        "cash": 100000.0,
        "shares": 0.0,
        "avg_cost": 0.0,
        "transactions": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_portfolio(portfolio)

    data, err = get_index_price()
    if data:
        print(f"  上证指数当前价: {data['price']}")
        print(f"  100,000元可买 {int(100000 / data['price'] * 100)} 份指数基金（按每份0.01点）")

    print(f"\n✅ 虚拟投资组合已初始化: 100,000 元")
    return portfolio


def load_portfolio():
    """加载投资组合"""
    if not os.path.exists(PORTFOLIO_FILE):
        return None
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(portfolio):
    """保存投资组合"""
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    tmp = PORTFOLIO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, PORTFOLIO_FILE)


def buy(amount=None):
    """买入（加仓）
    amount: 买入金额，默认总现金的10%（约10,000元）
    """
    portfolio = load_portfolio()
    if not portfolio:
        print("❌ 投资组合未初始化，请先运行: python virtual_portfolio.py init")
        return

    data, err = get_index_price()
    if err:
        print(f"❌ 无法获取价格: {err}")
        return

    price = data["price"]
    cash = portfolio["cash"]

    if amount is None:
        amount = round(cash * 0.1, 2)
    amount = min(amount, cash)

    if amount <= 0:
        print("⚠️ 现金不足，无法买入")
        return

    shares = amount / price
    total_cost = amount
    total_shares = portfolio["shares"] + shares
    total_cost_basis = portfolio["avg_cost"] * portfolio["shares"] + total_cost
    new_avg_cost = total_cost_basis / total_shares if total_shares > 0 else 0

    portfolio["cash"] -= total_cost
    portfolio["shares"] = total_shares
    portfolio["avg_cost"] = new_avg_cost
    portfolio["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    portfolio.setdefault("transactions", []).append({
        "type": "buy",
        "price": price,
        "amount": total_cost,
        "shares": shares,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    save_portfolio(portfolio)
    print(f"✅ 买入成功!")
    print(f"  买入价: {price}")
    print(f"  买入金额: {total_cost:.2f} 元")
    print(f"  持有份额: {total_shares:.4f}")
    print(f"  剩余现金: {portfolio['cash']:.2f} 元")


def sell(amount=None):
    """卖出（减仓）
    amount: 卖出金额，默认持仓市值的10%
    """
    portfolio = load_portfolio()
    if not portfolio:
        print("❌ 投资组合未初始化")
        return

    data, err = get_index_price()
    if err:
        print(f"❌ 无法获取价格: {err}")
        return

    price = data["price"]
    holdings = portfolio["shares"] * price

    if holdings <= 0:
        print("⚠️ 没有持仓可卖")
        return

    if amount is None:
        amount = round(holdings * 0.1, 2)
    sell_shares = amount / price
    sell_shares = min(sell_shares, portfolio["shares"])
    sell_amount = sell_shares * price

    portfolio["shares"] -= sell_shares
    portfolio["cash"] += sell_amount
    portfolio["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    portfolio.setdefault("transactions", []).append({
        "type": "sell",
        "price": price,
        "amount": sell_amount,
        "shares": sell_shares,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    save_portfolio(portfolio)
    print(f"✅ 卖出成功!")
    print(f"  卖出价: {price}")
    print(f"  卖出金额: {sell_amount:.2f} 元")
    print(f"  卖出份额: {sell_shares:.4f}")
    print(f"  剩余份额: {portfolio['shares']:.4f}")


def show_status():
    """显示当前持仓和盈亏"""
    portfolio = load_portfolio()
    if not portfolio:
        print("❌ 投资组合未初始化")
        print("运行: python virtual_portfolio.py init")
        return

    data, err = get_index_price()
    if err:
        data = {"price": 0, "change_pct": 0, "time": "获取失败"}

    current_price = data["price"]
    shares = portfolio["shares"]
    avg_cost = portfolio["avg_cost"]
    cash = portfolio["cash"]
    initial = portfolio["initial_capital"]

    market_value = shares * current_price
    total_value = cash + market_value
    stock_pnl = market_value - shares * avg_cost if shares > 0 else 0
    stock_pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 and shares > 0 else 0
    total_pnl = total_value - initial
    total_pnl_pct = (total_pnl / initial * 100)

    print("=" * 60)
    print("   虚拟投资组合 — 持仓报告")
    print(f"   {data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}")
    print("=" * 60)
    print(f"\n📊 【市场数据】")
    print(f"  上证指数: {current_price:,.2f}")
    if data.get("change_pct") is not None:
        arrow = "▲" if data["change_pct"] >= 0 else "▼"
        print(f"  今日涨跌: {arrow} {abs(data['change_pct']):.2f}%")

    print(f"\n💰 【投资组合】")
    pnl_sign = "+" if total_pnl >= 0 else ""
    print(f"  初始资金: {initial:,.2f} 元")
    print(f"  总资产:   {total_value:,.2f} 元")
    print(f"  总盈亏:   {pnl_sign}{total_pnl:,.2f} 元 ({pnl_sign}{total_pnl_pct:+.2f}%)")
    print(f"  持仓市值: {market_value:,.2f} 元")
    print(f"  可用现金: {cash:,.2f} 元")

    if shares > 0:
        spnl_sign = "+" if stock_pnl >= 0 else ""
        print(f"\n📈 【持仓明细】")
        print(f"  持有份额: {shares:.4f}")
        print(f"  均价:     {avg_cost:.2f}")
        print(f"  现价:     {current_price:,.2f}")
        print(f"  持仓盈亏: {spnl_sign}{stock_pnl:,.2f} 元 ({spnl_sign}{stock_pnl_pct:+.2f}%)")

    txns = portfolio.get("transactions", [])
    if txns:
        print(f"\n📋 【交易记录】（最近5笔）")
        for t in txns[-5:]:
            arrow = "🟢" if t["type"] == "buy" else "🔴"
            print(f"  {arrow} {t['time'][:16]}  {t['type'].upper()}  {t['price']:>8.2f}  {t['amount']:>8.2f}元")

    change = data.get("change_pct", 0)
    print(f"\n{'=' * 60}")
    if total_pnl > 0:
        print(f"  🎉 累计盈利: +{total_pnl:,.2f} 元 🎉")
    elif total_pnl < 0:
        print(f"  😅 累计亏损: {total_pnl:,.2f} 元")
    else:
        print(f"  😐 持平")
    print("=" * 60)


def show_history():
    """显示完整交易历史"""
    portfolio = load_portfolio()
    if not portfolio:
        print("❌ 投资组合未初始化")
        return

    txns = portfolio.get("transactions", [])
    if not txns:
        print("暂无交易记录")
        return

    print("\n" + "=" * 70)
    print("   完整交易历史")
    print("=" * 70)
    print(f"  {'时间':<20} {'类型':<6} {'价格':<10} {'金额':<12} {'份额':<12}")
    print("  " + "-" * 60)

    for t in txns:
        print(f"  {t['time'][:16]:<20} {t['type'].upper():<6} {t['price']:<10.2f} {t['amount']:<12.2f} {t['shares']:<12.4f}")

    print("=" * 70)
    print(f"  共 {len(txns)} 笔交易")
    total_buy = sum(t["amount"] for t in txns if t["type"] == "buy")
    total_sell = sum(t["amount"] for t in txns if t["type"] == "sell")
    print(f"  总买入: {total_buy:,.2f} 元")
    print(f"  总卖出: {total_sell:,.2f} 元")


def get_portfolio_data():
    """获取投资组合数据（供外部模块调用）"""
    portfolio = load_portfolio()
    if not portfolio:
        return None

    data, err = get_index_price()
    if err:
        return {"error": err}

    current_price = data["price"]
    shares = portfolio["shares"]
    avg_cost = portfolio["avg_cost"]
    cash = portfolio["cash"]
    initial = portfolio["initial_capital"]

    market_value = shares * current_price
    total_value = cash + market_value
    stock_pnl = market_value - shares * avg_cost if shares > 0 else 0
    stock_pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 and shares > 0 else 0
    total_pnl = total_value - initial
    total_pnl_pct = (total_pnl / initial * 100)

    return {
        "initial_capital": initial,
        "cash": cash,
        "shares": shares,
        "avg_cost": avg_cost,
        "current_price": current_price,
        "market_value": market_value,
        "total_value": total_value,
        "stock_pnl": stock_pnl,
        "stock_pnl_pct": stock_pnl_pct,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "change_pct": data.get("change_pct", 0),
        "price_time": data.get("time", ""),
        "transactions": portfolio.get("transactions", []),
    }


def main():
    args = sys.argv[1:]

    if not args:
        show_status()
        return

    cmd = args[0].lower()

    if cmd == "init":
        init_portfolio()
    elif cmd == "buy":
        amount = float(args[1]) if len(args) > 1 else None
        buy(amount)
    elif cmd == "sell":
        amount = float(args[1]) if len(args) > 1 else None
        sell(amount)
    elif cmd == "history":
        show_history()
    elif cmd == "status":
        show_status()
    else:
        print(f"未知命令: {cmd}")
        print("用法: python virtual_portfolio.py [init|buy|sell|history|status]")


if __name__ == "__main__":
    main()
