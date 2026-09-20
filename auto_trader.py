"""
自动交易系统
根据大六壬预测的涨跌方向，全自动用虚拟资金买入/卖出
每天盘前自动执行，收盘后自动对照结果
"""
import sys, os, json, subprocess
from datetime import datetime, date

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

TRADE_LOG = os.path.join(BASE, "_memory", "auto_trades.json")
PREDICTIONS_FILE = os.path.join(BASE, "_memory", "stock_predictions.json")
PORTFOLIO_FILE = os.path.join(BASE, "_memory", "virtual_portfolio.json")


def get_session():
    now = datetime.now()
    h, m = now.hour, now.minute
    wd = now.weekday()
    if wd >= 5:
        return "weekend"
    if 9 <= h < 11 or (h == 11 and m <= 30):
        return "morning"
    if 13 <= h < 15:
        return "afternoon"
    if h < 9:
        return "pre_market"
    return "closed"


def load_trade_log():
    if os.path.exists(TRADE_LOG):
        with open(TRADE_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"trades": [], "daily_summary": []}


def save_trade_log(log):
    os.makedirs(os.path.dirname(TRADE_LOG), exist_ok=True)
    with open(TRADE_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def load_predictions():
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data[-1]
        if isinstance(data, dict):
            return data
    return None


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_index_price():
    import akshare as ak
    df = ak.stock_zh_index_spot_em()
    row = df[df["名称"] == "上证指数"].iloc[0]
    return {"price": float(row["最新价"]), "change_pct": float(row["涨跌幅"]),
            "open": float(row["今开"]), "high": float(row["最高"]), "low": float(row["最低"]),
            "pre_close": float(row["昨收"])}


def analyze_trend(prediction):
    """
    分析趋势并生成交易信号
    优先考虑吉凶判断，再结合趋势预测
    """
    trend = prediction.get("trend_prediction", "")
    jixiong = prediction.get("jixiong", "")
    
    # 优先考虑吉凶判断（权重更高）
    if jixiong:
        if "吉" in jixiong:
            # 吉：倾向买入
            if "跌" in trend and "涨" not in trend:
                # 吉但趋势是纯跌，谨慎持有
                return "hold"
            else:
                # 吉+任何包含涨的趋势，买入
                return "buy"
        elif "凶" in jixiong:
            # 凶：倾向卖出
            if "涨" in trend and "跌" not in trend:
                # 凶但趋势是纯涨，谨慎持有
                return "hold"
            else:
                # 凶+任何包含跌的趋势，卖出
                return "sell"
    
    # 如果没有吉凶，使用原有的趋势分析逻辑
    if not trend:
        return "hold"
    
    # 趋势分析
    if "先跌后涨" in trend:
        # 先跌后涨：整体偏多，买入
        return "buy"
    elif "先涨后跌" in trend:
        # 先涨后跌：整体偏空，卖出
        return "sell"
    elif "涨" in trend and "跌" not in trend:
        # 纯涨：买入
        return "buy"
    elif "跌" in trend and "涨" not in trend:
        # 纯跌：卖出
        return "sell"
    elif "涨" in trend and "跌" in trend:
        # 涨跌都有：看出现顺序
        if trend.index("涨") < trend.index("跌"):
            return "buy"
        else:
            return "sell"
    elif "震荡" in trend or "盘整" in trend:
        # 震荡/盘整：持有观望
        return "hold"
    
    return "hold"


def execute_trade(signal, category="general", jixiong="", trend_prediction=""):
    """
    执行交易 - 每个类别有独立的资金池
    :param signal: 交易信号 (buy/sell/hold)
    :param category: 预测类别 (如 fixed_time, ri_zhi_shi_shen 等)
    :param jixiong: 吉凶判断
    :param trend_prediction: 趋势预测
    """
    from virtual_portfolio import load_portfolio as lp, save_portfolio as sp, get_index_price as gip
    
    # 使用分类特定的投资组合文件
    category_file = os.path.join(BASE, "_memory", f"virtual_portfolio_{category}.json")
    
    price_data, error = gip()
    if error:
        print(f"  [自动交易] 无法获取价格: {error}")
        return None
    price = price_data["price"]
    
    # 加载分类特定的投资组合
    if os.path.exists(category_file):
        with open(category_file, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
    else:
        # 初始化新的独立资金池
        portfolio = {
            "initial_capital": 100000.0,
            "cash": 100000.0,
            "shares": 0,
            "avg_cost": 0,
            "transactions": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    trade = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "price": price, "signal": signal, "category": category}

    if signal == "buy":
        cash = portfolio["cash"]
        amount = round(cash * 0.3, 2)
        amount = min(amount, cash)
        if amount < 100:
            print(f"  [自动交易] [{category}] 现金不足({cash:.2f})，跳过买入")
            return None
        shares = amount / price
        total_cost_basis = portfolio["avg_cost"] * portfolio["shares"] + amount
        total_shares = portfolio["shares"] + shares
        portfolio["avg_cost"] = total_cost_basis / total_shares if total_shares > 0 else 0
        portfolio["shares"] = total_shares
        portfolio["cash"] -= amount
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        portfolio.setdefault("transactions", []).append({
            "type": "buy", "price": price, "amount": amount,
            "shares": shares, "time": now_str, "auto": True,
            "category": category, "jixiong": jixiong, "trend_prediction": trend_prediction
        })
        portfolio["updated_at"] = now_str
        with open(category_file, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        trade["action"] = "buy"
        trade["amount"] = amount
        trade["shares"] = shares
        print(f"  [自动交易] [{category}] 买入 {amount:.2f}元 @ {price:.2f}, 持仓 {total_shares:.4f}份额")
        return trade

    elif signal == "sell":
        # 只能卖出自己类别的持仓
        if portfolio["shares"] <= 0:
            print(f"  [自动交易] [{category}] 无持仓，跳过卖出")
            return None
        shares_value = portfolio["shares"] * price
        sell_shares_pct = 0.3
        sell_shares = portfolio["shares"] * sell_shares_pct
        sell_amount = sell_shares * price
        portfolio["shares"] -= sell_shares
        portfolio["cash"] += sell_amount
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        portfolio.setdefault("transactions", []).append({
            "type": "sell", "price": price, "amount": sell_amount,
            "shares": sell_shares, "time": now_str, "auto": True,
            "category": category, "jixiong": jixiong, "trend_prediction": trend_prediction
        })
        portfolio["updated_at"] = now_str
        with open(category_file, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        trade["action"] = "sell"
        trade["amount"] = sell_amount
        trade["shares"] = sell_shares
        print(f"  [自动交易] [{category}] 卖出 {sell_amount:.2f}元 @ {price:.2f}, 剩余 {portfolio['shares']:.4f}份额")
        return trade
    else:
        print(f"  [自动交易] [{category}] 信号=hold，不操作")
        trade["action"] = "hold"
        return trade


def record_trade(prediction, trade_result):
    log = load_trade_log()
    record = {
        "date": date.today().isoformat(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "prediction": prediction.get("trend_prediction", "") if prediction else "",
        "signal": analyze_trend(prediction) if prediction else "hold",
        "action": trade_result.get("action", "none") if trade_result else "none",
        "price": trade_result.get("price", 0) if trade_result else 0,
        "amount": trade_result.get("amount", 0) if trade_result else 0,
    }
    log["trades"].append(record)
    save_trade_log(log)
    return record


def review_result():
    prediction = load_predictions()
    if not prediction or prediction.get("status") != "completed":
        print("\n  [收盘对照] 无已完成预测，跳过")
        return
    actual = prediction.get("actual_result", "")
    if not actual:
        print("\n  [收盘对照] 预测记录中无实际结果，运行 auto_review.py 获取")
        return
    trend = prediction.get("trend_prediction", "")
    match = "✅ 准确" if actual in trend else "❌ 偏差"
    print(f"\n  [收盘对照] {match}")
    print(f"    预测: {trend}")
    print(f"    实际: {actual}")


def print_status(portfolio, price_data=None):
    if not portfolio:
        return
    shares = portfolio.get("shares", 0)
    cash = portfolio.get("cash", 0)

    if shares > 0 and not price_data:
        try:
            price_data = get_index_price()
        except:
            price_data = None

    if shares > 0 and price_data and "price" in price_data:
        current_price = price_data["price"]
        market_value = shares * current_price
        total_value = cash + market_value
        cost_basis = shares * portfolio.get("avg_cost", 0)
        pnl = market_value - cost_basis
        pnl_pct = ((current_price / portfolio.get("avg_cost", 1)) - 1) * 100
    else:
        total_value = cash
        pnl = 0
        pnl_pct = 0

    print(f"\n  [组合状态]")
    print(f"    总资产: {total_value:.2f} 元")
    if shares > 0:
        print(f"    持仓: {shares:.4f} 份额 @ {portfolio.get('avg_cost', 0):.2f} 均价")
    print(f"    现金: {cash:.2f} 元")
    pnl_str = f"+{pnl:.2f}" if pnl >= 0 else f"{pnl:.2f}"
    print(f"    浮动盈亏: {pnl_str} 元 ({pnl_pct:+.2f}%)")


def run():
    print("=" * 60)
    print("  大六壬 · 自动交易系统")
    print("  根据预测涨跌，全自动买卖上证指数")
    print("=" * 60)

    # 参考模式：六壬不参与决策，自动交易暂停（仅观察记录）
    try:
        from config import LIUREN_REFERENCE_ONLY
    except Exception:
        LIUREN_REFERENCE_ONLY = True
    if LIUREN_REFERENCE_ONLY:
        print("\n  🔰 六壬参考模式已开启：自动交易暂停（仅生成信号供观察验证）")
        print("     验证期结束、精准度达标后，将 config.LIUREN_REFERENCE_ONLY 设为 False 即可恢复")
        # 仅展示当前预测信号，不执行任何买卖
        prediction = load_predictions()
        today_str = date.today().isoformat()
        if prediction and prediction.get("date") == today_str:
            print(f"  🔮 今日六壬预测（参考）: {prediction.get('trend_prediction', '')} 吉凶:{prediction.get('jixiong','')}")
        else:
            print(f"  🔮 今日暂无六壬预测记录")
        return

    session = get_session()
    today_str = date.today().isoformat()
    portfolio = load_portfolio()
    prediction = load_predictions()

    if session == "weekend":
        print(f"\n  今天是周末，股市休市中")
        price_data = get_index_price() if session != "weekend" else None
        print_status(portfolio, price_data)
        review_result()
        return

    if session == "pre_market":
        print(f"\n  📊 盘前时段 - 准备执行预测与交易")
        if prediction and prediction.get("date") == today_str:
            print(f"  今日已有预测: {prediction.get('trend_prediction', '')}")
        else:
            print(f"\n  正在运行大六壬预测...")
            result = subprocess.run(
                [sys.executable, "stock_daily_predict.py"],
                cwd=BASE, capture_output=True, text=True, encoding="utf-8"
            )
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            prediction = load_predictions()

        if not prediction or prediction.get("date") != today_str:
            print("  [自动交易] 预测失败或无今日预测")
            return

        signal = analyze_trend(prediction)
        print(f"\n  🔮 预测: {prediction.get('trend_prediction', '')}")
        print(f"  📡 信号: {signal.upper()}")

        trade_result = execute_trade(signal)
        record_trade(prediction, trade_result)

    elif session in ("morning", "afternoon"):
        print(f"\n  📊 交易时段中 - 等待收盘")
        print(f"  今日预测: {prediction.get('trend_prediction', '未知') if prediction else '无'}")
        price_data = get_index_price()
        print_status(portfolio, price_data)

    elif session == "closed":
        print(f"\n  📊 盘后时段 - 收盘对照")
        review_result()
        price_data = get_index_price()
        print_status(portfolio, price_data)

    log = load_trade_log()
    today_trades = [t for t in log["trades"] if t.get("date") == today_str]
    if today_trades:
        print(f"\n  [今日操作] {len(today_trades)} 笔")
        for t in today_trades:
            action_icon = {"buy": "买入", "sell": "卖出", "hold": "持有"}.get(t.get("action", ""), t.get("action", ""))
            print(f"    {t['time']} {action_icon} ({t.get('signal', '')}) @ {t.get('price', 0):.2f}")

    total_trades = len(log["trades"])
    print(f"\n  [累计] 共 {total_trades} 笔自动交易")

    print(f"\n  {'='*60}")
    print(f"  提示: 每天盘前运行此脚本，即可全自动交易")
    print(f"  建议用Windows任务计划程序设置每天 9:20 自动运行")
    print(f"  {'='*60}")


if __name__ == "__main__":
    run()
