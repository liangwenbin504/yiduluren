"""
本地API服务 — 供股市行情仪表盘调用
处理买入/卖出请求，返回JSON结果

启动方式 (自动): stock_dashboard.py 会自动启动本服务
启动方式 (手动): python stock_api_server.py
"""
import json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

HOST = "127.0.0.1"
PORT = 18765


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/buy":
            self._handle_trade("buy")
        elif path == "/sell":
            self._handle_trade("sell")
        elif path == "/status":
            self._handle_status()
        else:
            self._send_json({"error": "未知路径"}, 404)

    def do_POST(self):
        self.do_GET()

    def _handle_trade(self, action):
        try:
            from virtual_portfolio import get_index_price, load_portfolio, save_portfolio

            price_data, error = get_index_price()
            if error:
                self._send_json({"success": False, "error": error})
                return

            price = price_data["price"]
            portfolio = load_portfolio()
            if not portfolio:
                self._send_json({"success": False, "error": "投资组合未初始化"})
                return

            if action == "buy":
                cash = portfolio["cash"]
                amount = round(cash * 0.1, 2)
                amount = min(amount, cash)
                if amount <= 0:
                    self._send_json({"success": False, "error": "现金不足"})
                    return

                shares = amount / price
                total_cost_basis = portfolio["avg_cost"] * portfolio["shares"] + amount
                total_shares = portfolio["shares"] + shares
                portfolio["avg_cost"] = total_cost_basis / total_shares if total_shares > 0 else 0
                portfolio["shares"] = total_shares
                portfolio["cash"] -= amount

                from datetime import datetime
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                portfolio.setdefault("transactions", []).append({
                    "type": "buy", "price": price, "amount": amount,
                    "shares": shares, "time": now_str
                })
                portfolio["updated_at"] = now_str
                save_portfolio(portfolio)

                self._send_json({
                    "success": True, "action": "买入",
                    "price": price, "amount": amount,
                    "shares": portfolio["shares"], "cash": portfolio["cash"],
                    "message": f"买入成功! 金额: {amount:.2f}元, 持有份额: {portfolio['shares']:.4f}"
                })
            else:
                shares_value = portfolio["shares"] * price
                if portfolio["shares"] <= 0:
                    self._send_json({"success": False, "error": "没有持仓可卖出"})
                    return

                sell_amount = round(shares_value * 0.1, 2)
                sell_shares = sell_amount / price
                sell_shares = min(sell_shares, portfolio["shares"])
                sell_amount = sell_shares * price
                portfolio["shares"] -= sell_shares
                portfolio["cash"] += sell_amount

                from datetime import datetime
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                portfolio.setdefault("transactions", []).append({
                    "type": "sell", "price": price, "amount": sell_amount,
                    "shares": sell_shares, "time": now_str
                })
                portfolio["updated_at"] = now_str
                save_portfolio(portfolio)

                self._send_json({
                    "success": True, "action": "卖出",
                    "price": price, "amount": sell_amount,
                    "shares": portfolio["shares"], "cash": portfolio["cash"],
                    "message": f"卖出成功! 金额: {sell_amount:.2f}元, 持有份额: {portfolio['shares']:.4f}"
                })
        except Exception as e:
            self._send_json({"success": False, "error": str(e)})

    def _handle_status(self):
        try:
            from virtual_portfolio import load_portfolio, get_index_price
            portfolio = load_portfolio()
            price_data, error = get_index_price()
            result = {
                "initial_capital": portfolio["initial_capital"],
                "cash": portfolio["cash"],
                "shares": portfolio["shares"],
                "total_value": portfolio["cash"] + portfolio["shares"] * (price_data["price"] if price_data else 0),
                "current_price": price_data["price"] if price_data else 0,
            }
            if portfolio["shares"] > 0:
                cost = portfolio["shares"] * portfolio["avg_cost"]
                market = portfolio["shares"] * (price_data["price"] if price_data else 0)
                result["pnl"] = market - cost
                result["pnl_pct"] = ((price_data["price"] / portfolio["avg_cost"]) - 1) * 100 if portfolio["avg_cost"] > 0 else 0
            else:
                result["pnl"] = 0
                result["pnl_pct"] = 0
            self._send_json({"success": True, "portfolio": result})
        except Exception as e:
            self._send_json({"success": False, "error": str(e)})

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_json({})

    def log_message(self, format, *args):
        print(f"[API] {args[0]} {args[1]} -> {args[2]}", flush=True)


def start_server():
    server = HTTPServer((HOST, PORT), APIHandler)
    print(f"  本地API服务运行中: http://{HOST}:{PORT}", flush=True)
    print(f"  GET /buy   -> 买入股票 (默认10000元)", flush=True)
    print(f"  GET /sell  -> 卖出股票 (默认10000元)", flush=True)
    print(f"  GET /status -> 查询持仓状态", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务已停止", flush=True)
        server.server_close()


if __name__ == "__main__":
    print("=" * 50)
    print("  大六壬股市行情 - 本地API服务")
    print("=" * 50)
    start_server()
