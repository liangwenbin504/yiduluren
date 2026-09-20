"""
多账户虚拟交易系统

支持独立分类账户，各初始资金 100,000 元：
  - fixed_time        — 固定时辰课（对照组）
  - ri_gan_pian_cai   — 日干偏财时课
  - ri_zhi_pian_cai   — 日支偏财时课
  - ri_gan_shi_shen   — 日干食神时课
  - ri_zhi_shi_shen   — 日支食神时课
  - ri_gan_zheng_yin  — 日干正印时课
  - ri_gan_pian_yin   — 日干偏印时课
  - ri_zhi_zheng_yin  — 日支正印时课
  - ri_zhi_pian_yin   — 日支偏印时课
  - random            — 随机课（实验组B）
  - manual            — 人工指定时

每个账户独立交易、独立持仓、独立盈亏统计。
"""
import json
import os
from datetime import datetime
from pathlib import Path

INITIAL_CAPITAL = 1000000.0
MEMORY_DIR = Path(__file__).parent.parent / "_memory"

TRADE_FEE_RATE = 0.0003
SLIPPAGE_RATE = 0.0002
MAX_POSITION_RATIO = 0.95
STOP_LOSS_RATIO = -0.03
TAKE_PROFIT_RATIO = 0.05


def _portfolio_path(category: str) -> Path:
    return MEMORY_DIR / f"virtual_portfolio_{category}.json"


def _trades_path(category: str) -> Path:
    return MEMORY_DIR / f"auto_trades_{category}.json"


DEFAULT_PORTFOLIO = {
    "cash": INITIAL_CAPITAL,
    "shares": 0,
    "total_invested": 0.0,
    "last_price": 0.0,
    "position_value": 0.0,
    "total_value": INITIAL_CAPITAL,
    "high_water_mark": INITIAL_CAPITAL,
    "peak_value": INITIAL_CAPITAL,
    "initial_capital": INITIAL_CAPITAL,
}


class VirtualTrader:
    def __init__(self, category: str = "default"):
        valid_cats = ("fixed_time", "ri_gan_pian_cai", "ri_zhi_pian_cai", "ri_gan_shi_shen", "ri_zhi_shi_shen",
                      "ri_gan_zheng_yin", "ri_gan_pian_yin", "ri_zhi_zheng_yin", "ri_zhi_pian_yin", "random", "manual")
        if category not in valid_cats:
            raise ValueError(f"无效的分类: {category}")
        self.category = category
        self.portfolio_path = _portfolio_path(category)
        self.trades_path = _trades_path(category)
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.portfolio = self._load_portfolio()
        self._ensure_portfolio()
        self.trades = self._load_trades()

    def _load_portfolio(self):
        if self.portfolio_path.exists():
            try:
                data = json.loads(self.portfolio_path.read_text(encoding="utf-8"))
                for k, v in DEFAULT_PORTFOLIO.items():
                    data.setdefault(k, v)
                return data
            except Exception:
                pass
        return dict(DEFAULT_PORTFOLIO)

    def _ensure_portfolio(self):
        if not self.portfolio_path.exists():
            self._save_portfolio()

    def _save_portfolio(self):
        self.portfolio_path.write_text(
            json.dumps(self.portfolio, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _load_trades(self):
        if self.trades_path.exists():
            try:
                return json.loads(self.trades_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_trades(self):
        self.trades_path.write_text(
            json.dumps(self.trades, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def reset(self):
        self.portfolio = dict(DEFAULT_PORTFOLIO)
        self.trades = []
        self._save_portfolio()
        self._save_trades()

    @staticmethod
    def _get_position_ratio(vote_result: dict) -> float:
        """根据投票一致性计算仓位比例（支持加权投票的浮点数权重）"""
        if not vote_result or not isinstance(vote_result, dict):
            return 0.5
        total = sum(vote_result.values())
        if total < 1.5:
            return 0.5
        max_votes = max(vote_result.values())
        max_ratio = max_votes / total if total > 0 else 0
        if max_ratio >= 0.8:
            return 1.0
        elif max_ratio >= 0.5:
            return 0.5
        else:
            return 0.0

    @staticmethod
    def _describe_consistency(vote_result: dict) -> str:
        if not vote_result or not isinstance(vote_result, dict):
            return "无投票"
        total = sum(vote_result.values())
        if total < 1.5:
            return "无投票"
        max_votes = max(vote_result.values())
        max_ratio = max_votes / total if total > 0 else 0
        if max_ratio >= 0.8:
            return "高置信度"
        elif max_ratio >= 0.5:
            return "中置信度"
        else:
            return "低置信度"

    def get_signal(self, trend_prediction: str, combined_score: float,
                   position_ratio: float = 1.0) -> str:
        """
        根据趋势预测和综合评分生成交易信号。
        返回 BUY / SELL / HOLD。
        position_ratio=0.0 时不会发出 BUY 信号。
        """
        shares = self.portfolio["shares"]
        tp = trend_prediction.strip()

        if tp == "跌":
            if shares > 0:
                return "SELL"
            return "HOLD"

        if tp == "涨":
            if shares == 0:
                if position_ratio <= 0:
                    return "HOLD"
                return "BUY"
            return "HOLD"

        if "先跌后涨" in tp:
            if shares == 0 and combined_score >= 0:
                if position_ratio <= 0:
                    return "HOLD"
                return "BUY"
            return "HOLD"

        if "先涨后跌" in tp:
            if shares > 0:
                return "SELL"
            return "HOLD"

        if "偏跌" in tp or "震荡偏跌" in tp:
            if shares > 0:
                return "SELL"
            return "HOLD"

        if "偏涨" in tp or "震荡偏涨" in tp or "震荡偏多" in tp:
            if shares == 0 and combined_score >= 0:
                if position_ratio <= 0:
                    return "HOLD"
                return "BUY"
            return "HOLD"

        if "震荡" in tp:
            return "HOLD"

        if shares > 0:
            return "SELL"
        return "HOLD"

    def execute_trade(self, current_price: float, signal: str,
                      trend_prediction: str, rizhu: str, shi_chen: str,
                      kege_name: str = "", combined_score: float = 0.0,
                      position_ratio: float = 1.0):
        """
        执行交易（BUY/SELL/HOLD），更新持仓并记录。
        position_ratio 控制买入仓位比例（0.0~1.0）。
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price = current_price * (1 + SLIPPAGE_RATE) if signal == "BUY" else \
                current_price * (1 - SLIPPAGE_RATE)
        price = round(price, 2)

        old_total = self.portfolio["total_value"]
        old_shares = self.portfolio["shares"]

        trade = {
            "timestamp": timestamp,
            "category": self.category,
            "action": signal,
            "price": price,
            "shares_before": old_shares,
            "cash_before": round(self.portfolio["cash"], 2),
            "rizhu": rizhu,
            "shi_chen": shi_chen,
            "kege": kege_name,
            "trend": trend_prediction,
            "position_ratio": position_ratio,
        }

        if signal == "BUY":
            effective_ratio = MAX_POSITION_RATIO * position_ratio
            max_shares = int(self.portfolio["cash"] * effective_ratio / price / 100) * 100
            if max_shares < 100:
                trade["action"] = "BUY_FAILED"
                trade["reason"] = f"现金不足买1手(需{int(price*100):,}, 可用{int(self.portfolio['cash']*effective_ratio):,})"
            else:
                buy_shares = max_shares
                actual_cost = buy_shares * price
                actual_fee = actual_cost * TRADE_FEE_RATE
                self.portfolio["cash"] -= (actual_cost + actual_fee)
                self.portfolio["shares"] += buy_shares
                self.portfolio["total_invested"] += actual_cost
                trade["shares_changed"] = buy_shares
                trade["fee"] = round(actual_fee, 2)
                trade["total_cost"] = round(actual_cost + actual_fee, 2)

        elif signal == "SELL" and old_shares > 0:
            sell_shares = old_shares
            revenue = sell_shares * price
            fee = revenue * TRADE_FEE_RATE
            net_revenue = revenue - fee
            self.portfolio["cash"] += net_revenue
            self.portfolio["shares"] = 0
            trade["shares_changed"] = -sell_shares
            trade["fee"] = round(fee, 2)
            trade["net_revenue"] = round(net_revenue, 2)

        self.portfolio["last_price"] = price
        self.portfolio["position_value"] = self.portfolio["shares"] * price
        self.portfolio["total_value"] = round(
            self.portfolio["cash"] + self.portfolio["position_value"], 2
        )

        pnl = self.portfolio["total_value"] - old_total
        if self.portfolio["total_value"] > self.portfolio["peak_value"]:
            self.portfolio["peak_value"] = self.portfolio["total_value"]

        trade["cash_after"] = round(self.portfolio["cash"], 2)
        trade["shares_after"] = self.portfolio["shares"]
        trade["total_value"] = self.portfolio["total_value"]
        trade["pnl"] = round(pnl, 2)

        # 止损/止盈检查
        if signal != "BUY_FAILED":
            if pnl / old_total <= STOP_LOSS_RATIO if old_total > 0 else False:
                trade["stop_loss"] = True
            if pnl / old_total >= TAKE_PROFIT_RATIO if old_total > 0 else False:
                trade["take_profit"] = True

        self.trades.append(trade)
        self._save_portfolio()
        self._save_trades()
        return trade

    def _get_initial_capital(self) -> float:
        return self.portfolio.get("initial_capital", INITIAL_CAPITAL)

    def get_portfolio_summary(self) -> str:
        p = self.portfolio
        ic = self._get_initial_capital()
        total = p["total_value"]
        pnl = total - ic
        pnl_pct = (pnl / ic) * 100

        lines = [
            f"{'='*45}",
            f"  虚拟账户 [{self.category}]",
            f"{'='*45}",
            f"  初始资金: {ic:>10,.2f}",
            f"  当前现金: {p['cash']:>10,.2f}",
            f"  持仓市值: {p['position_value']:>10,.2f}",
            f"  总  资  产: {total:>10,.2f}",
            f"  累计盈亏: {pnl:>+10,.2f}  ({pnl_pct:>+.2f}%)",
            f"  交易次数: {len([t for t in self.trades if t['action'] in ('BUY','SELL')])}",
            f"{'='*45}",
        ]
        return "\n".join(lines)

    def get_trade_history(self, limit: int = 5) -> str:
        recent = [t for t in self.trades if t["action"] in ("BUY", "SELL")][-limit:]
        if not recent:
            return "  暂无交易记录"

        lines = [f"  {'时间':<16} {'操作':<5} {'价格':<8} {'股数':<6} {'金额变化':<10}",
                 "  " + "-" * 55]
        for t in recent:
            pnl_str = f"{t.get('pnl',0):>+8,.2f}" if t["action"] == "SELL" else ""
            shares = t.get("shares_changed", 0)
            lines.append(
                f"  {t['timestamp'][:16]:<16} {t['action']:<5} {t['price']:<8.2f} "
                f"{shares:<6} {pnl_str}"
            )
        return "\n".join(lines)


    def after_predict(self, prediction_entry: dict, ref_price: float):
        """盘前调用：根据预测结果自动交易（含置信度仓位控制）"""
        trend = prediction_entry.get("trend_prediction", "")
        combined_score = prediction_entry.get("combined_score", 0)
        vote_result = prediction_entry.get("vote_result", {})
        position_ratio = self._get_position_ratio(vote_result)
        consistency = self._describe_consistency(vote_result)
        rizhu = prediction_entry.get("rizhu", "")
        shi_chen = prediction_entry.get("shi_chen", "")
        kege = prediction_entry.get("keti", "")

        signal = self.get_signal(trend, combined_score, position_ratio)

        if position_ratio == 0.0 and signal == "HOLD":
            print(f"  [{self.category}] 虚拟交易: 无共识→不交易({consistency})", flush=True)
            return

        if signal in ("BUY", "SELL"):
            trade = self.execute_trade(
                current_price=ref_price,
                signal=signal,
                trend_prediction=trend,
                rizhu=rizhu,
                shi_chen=shi_chen,
                kege_name=kege,
                combined_score=combined_score,
                position_ratio=position_ratio,
            )
            actual_action = trade.get("action", signal)
            if actual_action == "BUY_FAILED":
                pct_label = {1.0: "满仓", 0.5: "半仓", 0.0: "零仓"}.get(position_ratio, f"{position_ratio:.0%}")
                print(f"  [{self.category}] 虚拟交易: 买入失败({pct_label}/{consistency}) — 资金不足", flush=True)
                return
            pct_label = {1.0: "满仓", 0.5: "半仓", 0.0: "零仓"}.get(position_ratio, f"{position_ratio:.0%}")
            action_cn = {"BUY": "买入", "SELL": "卖出"}[signal]
            pct_info = f"({pct_label}/{consistency})" if signal == "BUY" else ""
            print(f"  [{self.category}] 虚拟交易: {action_cn}{pct_info} @ {ref_price:.2f}", flush=True)
            print(f"  {self.get_portfolio_summary()}", flush=True)
        elif signal == "HOLD":
            pct_label = {1.0: "满仓", 0.5: "半仓", 0.0: "零仓"}.get(position_ratio, f"{position_ratio:.0%}")
            print(f"  [{self.category}] 虚拟交易: 持仓不动({pct_label}/{consistency})", flush=True)

    def after_review(self, actual_price: float, details: dict):
        """收盘后调用：按实际收盘价结算"""
        shares = self.portfolio["shares"]
        if shares > 0:
            revenue = shares * actual_price
            fee = revenue * TRADE_FEE_RATE
            net_revenue = revenue - fee
            self.portfolio["cash"] += net_revenue
            self.portfolio["shares"] = 0
            self.portfolio["last_price"] = actual_price
            self.portfolio["position_value"] = 0
            self.portfolio["total_value"] = round(self.portfolio["cash"], 2)
            self._save_portfolio()

            self.trades.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": self.category,
                "action": "AUTO_SELL",
                "price": actual_price,
                "reason": "收盘自动结算",
            })
            self._save_trades()
            print(f"  [{self.category}] 收盘结算: 卖出 {shares} 股 @ {actual_price:.2f}", flush=True)


def get_all_portfolios_summary() -> str:
    """获取所有分类账户的总览"""
    lines = []
    lines.append("=" * 50)
    lines.append("  多分类虚拟账户总览")
    lines.append("=" * 50)
    grand_total = 0.0
    grand_pnl = 0.0
    grand_initial = 0.0
    all_cats = ("fixed_time", "ri_gan_pian_cai", "ri_zhi_pian_cai", "ri_gan_shi_shen", "ri_zhi_shi_shen",
                "ri_gan_zheng_yin", "ri_gan_pian_yin", "ri_zhi_zheng_yin", "ri_zhi_pian_yin", "random", "manual")
    name_map = {"fixed_time": "固定时辰", "ri_gan_pian_cai": "日干偏财", "ri_zhi_pian_cai": "日支偏财",
                "ri_gan_shi_shen": "日干食神", "ri_zhi_shi_shen": "日支食神",
                "ri_gan_zheng_yin": "日干正印", "ri_gan_pian_yin": "日干偏印",
                "ri_zhi_zheng_yin": "日支正印", "ri_zhi_pian_yin": "日支偏印",
                "random": "随机", "manual": "人工指定时"}
    for cat in all_cats:
        trader = VirtualTrader(cat)
        p = trader.portfolio
        ic = p.get("initial_capital", INITIAL_CAPITAL)
        total = p["total_value"]
        pnl = total - ic
        pnl_pct = (pnl / ic) * 100
        trades = len([t for t in trader.trades if t["action"] in ("BUY","SELL")])
        lines.append(
            f"  {name:<8} | 初始 {ic:>8,.2f} → 总资产 {total:>10,.2f} | "
            f"盈亏 {pnl:>+8,.2f} ({pnl_pct:>+6.2f}%) | 交易 {trades} 次"
        )
        grand_total += total
        grand_pnl += pnl
        grand_initial += ic
    lines.append("-" * 50)
    lines.append(f"  总投入: {grand_initial:>10,.2f} | 总资产: {grand_total:>10,.2f} | 总盈亏: {grand_pnl:>+8,.2f}")
    lines.append("=" * 50)
    return "\n".join(lines)
