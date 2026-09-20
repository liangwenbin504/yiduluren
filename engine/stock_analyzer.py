#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票行情获取与六壬股市分析模块

功能：
1. 获取A股实时行情（AKShare）
2. 获取个股历史行情
3. 六壬股市特殊类象知识
4. 行情数据格式化（供AI prompt使用）
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

import threading as _threading
_MARKET_DATA_LOCK = _threading.Lock()
_MARKET_DATA_CACHE = None
_MARKET_DATA_READY = False


def _preload_market_data():
    """后台预加载全市场数据（AKShare首次耗时较长）"""
    global _MARKET_DATA_CACHE, _MARKET_DATA_READY
    if not HAS_AKSHARE:
        _MARKET_DATA_READY = True
        return
    try:
        df = ak.stock_zh_a_spot_em()
        code_map = {}
        for _, row in df.iterrows():
            code_map[str(row["代码"])] = row
        with _MARKET_DATA_LOCK:
            _MARKET_DATA_CACHE = {"all_df": df, "code_map": code_map}
            _MARKET_DATA_READY = True
    except Exception:
        with _MARKET_DATA_LOCK:
            _MARKET_DATA_READY = True


_preload_thread = _threading.Thread(target=_preload_market_data, daemon=True)
_preload_thread.start()


STOCK_CLASS_KNOWLEDGE = """
【股市六壬特殊类象】
一、地支与股市类象
- 子：资金、散户、水下、低位、银行
- 丑：券商、基金、机构、银根
- 寅：开市、开盘、上涨、龙头
- 卯：突破、放量、门户、通道
- 辰：震荡、盘整、横盘、平台
- 巳：拉升、急涨、火速行情、投机
- 午：天量、大阳线、涨停、高潮
- 未：阴跌、回落、回调、套牢
- 申：下跌、破位、空头、出货
- 酉：收盘、缩量、整理、金叉
- 戌：跌停、崩盘、套牢盘、ST股
- 亥：潜伏、底仓、暗流、对倒

二、神将股市类象
- 贵人(丑)：国家队、白马股、绩优股
- 螣蛇(巳)：妖股、庄股、异常波动
- 朱雀(午)：消息面、利好利空、公告
- 六合(卯)：横盘、整理、多空平衡
- 勾陈(辰)：套牢、死叉、阻力位
- 青龙(寅)：上升趋势、牛市、主力
- 天空(戌)：虚假突破、主力骗线
- 白虎(申)：暴跌、恐慌盘、踩踏
- 太常(未)：慢牛、消费股、分红
- 玄武(亥)：内幕交易、潜伏盘、老鼠仓
- 太阴(酉)：阴跌、杀估值、缩量
- 天后(子)：流动性宽松、放水、利好

三、课体与股市
- 龙德课：大盘蓝筹走强，宜价值投资
- 富贵课：利好驱动上涨，宜顺势而为
- 三光课：多方发力上行，短期看涨
- 三阳课：多方主导，趋势向好
- 三奇课：突发利好，走势异常
- 六仪课：基本面优良，稳健上行
- 轩盖课：权重股搭台，题材股唱戏
- 铸印发课：底部放量启动，中线看好
- 龙战课：多空激战，剧烈波动
- 九丑课：利空突袭，恐慌下跌
- 天网课：套牢盘沉重，难以突破
- 死奇课：走势破位，止损离场
"""


class StockAnalyzer:
    """股票行情分析与六壬股市预测辅助"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60

    def search_stock(self, keyword: str) -> List[Dict]:
        """搜索股票代码

        Args:
            keyword: 股票名称或代码

        Returns:
            股票信息列表
        """
        if not HAS_AKSHARE:
            return self._mock_search_stock(keyword)

        try:
            df = ak.stock_info_a_code_name()
            results = []
            keyword_upper = keyword.upper()
            for _, row in df.iterrows():
                code = str(row["code"])
                name = str(row["name"])
                if keyword_upper in code or keyword in name:
                    results.append({"code": code, "name": name})
            return results[:20]
        except Exception as e:
            print(f"搜索股票失败: {e}")
            return self._mock_search_stock(keyword)

    def _mock_search_stock(self, keyword: str) -> List[Dict]:
        """搜索失败时的mock数据"""
        mock = [
            {"code": "000001", "name": "平安银行"},
            {"code": "600036", "name": "招商银行"},
            {"code": "600519", "name": "贵州茅台"},
            {"code": "000858", "name": "五粮液"},
            {"code": "300750", "name": "宁德时代"},
            {"code": "601318", "name": "中国平安"},
            {"code": "000333", "name": "美的集团"},
            {"code": "600900", "name": "长江电力"},
            {"code": "002415", "name": "海康威视"},
            {"code": "601166", "name": "兴业银行"},
        ]
        keyword_upper = keyword.upper()
        return [s for s in mock if keyword_upper in s["code"] or keyword in s["name"]]

    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取个股实时行情（优先使用预加载缓存）

        Args:
            stock_code: 股票代码（如 "000001" 或 "sz.000001"）

        Returns:
            行情数据字典
        """
        cache_key = f"quote_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        if not HAS_AKSHARE:
            result = self._mock_realtime_quote(stock_code)
            self._set_cache(cache_key, result)
            return result

        try:
            # 检查预加载缓存是否就绪
            if _MARKET_DATA_READY and _MARKET_DATA_CACHE is not None:
                with _MARKET_DATA_LOCK:
                    code_map = _MARKET_DATA_CACHE["code_map"]
                row = code_map.get(stock_code)
                if row is not None:
                    result = {
                        "code": stock_code,
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌幅", 0)),
                        "change_amount": float(row.get("涨跌额", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "open": float(row.get("今开", 0)),
                        "prev_close": float(row.get("昨收", 0)),
                        "turnover_rate": float(row.get("换手率", 0)),
                        "market_cap": float(row.get("总市值", 0)),
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._set_cache(cache_key, result)
                    return result

            # 缓存未就绪 -> 返回模拟数据（避免调用全量API导致超时）
            return self._mock_realtime_quote(stock_code)
        except Exception as e:
            print(f"获取实时行情失败 {stock_code}: {e}")
            return self._mock_realtime_quote(stock_code)

    def _mock_realtime_quote(self, stock_code: str) -> Dict:
        """获取行情失败时的mock数据"""
        import random
        base_price = random.uniform(10, 100)
        change_pct = random.uniform(-5, 5)
        return {
            "code": stock_code,
            "name": "示例股票",
            "price": round(base_price, 2),
            "change": round(change_pct, 2),
            "change_amount": round(base_price * change_pct / 100, 2),
            "volume": round(random.uniform(1000, 100000), 0),
            "amount": round(random.uniform(100000, 10000000), 0),
            "high": round(base_price * (1 + abs(change_pct) / 200), 2),
            "low": round(base_price * (1 - abs(change_pct) / 200), 2),
            "open": round(base_price * (1 + random.uniform(-0.5, 0.5) / 100), 2),
            "prev_close": round(base_price, 2),
            "turnover_rate": round(random.uniform(0.1, 5), 2),
            "market_cap": round(random.uniform(10e9, 1000e9), 0),
            "timestamp": datetime.now().isoformat(),
        }

    def get_market_overview(self) -> Dict:
        """获取大盘概览

        Returns:
            包含上证、深证、创业板等指数行情
        """
        if not HAS_AKSHARE:
            return self._mock_market_overview()

        try:
            df = ak.stock_zh_index_spot_em()
            sh_row = df[df["名称"] == "上证指数"]
            if not sh_row.empty:
                price = float(sh_row.iloc[0].get("最新价", 0))
                return {
                    "shanghai": {"name": "上证指数", "price": price},
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception:
            try:
                sh_spot = self.get_realtime_quote("000001")
                if sh_spot and sh_spot.get("price"):
                    return {
                        "shanghai": {"name": "上证指数", "price": sh_spot["price"]},
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception:
                pass
            return self._mock_market_overview()

    def _mock_market_overview(self) -> Dict:
        return {
            "shanghai": {"name": "上证指数", "price": 3100},
            "shenzhen": {"name": "深证成指", "price": 9500},
            "timestamp": datetime.now().isoformat(),
        }

    def format_quote_for_prompt(self, quote: Dict) -> str:
        """将行情数据格式化为AI提示词片段"""
        if not quote:
            return ""

        lines = [
            "【当前行情数据】",
            f"股票：{quote.get('name', '')}（{quote.get('code', '')}）",
            f"最新价：{quote.get('price', 'N/A')}",
            f"涨跌幅：{quote.get('change', 'N/A')}%",
            f"最高价：{quote.get('high', 'N/A')}",
            f"最低价：{quote.get('low', 'N/A')}",
            f"开盘价：{quote.get('open', 'N/A')}",
            f"昨收价：{quote.get('prev_close', 'N/A')}",
            f"成交量：{self._format_volume(quote.get('volume', 0))}",
            f"成交额：{self._format_amount(quote.get('amount', 0))}",
            f"换手率：{quote.get('turnover_rate', 'N/A')}%",
        ]
        return "\n".join(lines)

    def _format_volume(self, v: float) -> str:
        """格式化成交量"""
        if v >= 1e8:
            return f"{v/1e8:.2f}亿"
        if v >= 1e4:
            return f"{v/1e4:.2f}万"
        return str(int(v))

    def _format_amount(self, v: float) -> str:
        """格式化成交额"""
        if v >= 1e8:
            return f"{v/1e8:.2f}亿"
        if v >= 1e4:
            return f"{v/1e4:.2f}万"
        return str(int(v))

    def _get_cache(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["time"] < self.cache_timeout:
                return entry["data"]
        return None

    def _set_cache(self, key: str, data: Dict):
        """设置缓存"""
        self.cache[key] = {"data": data, "time": time.time()}

    @staticmethod
    def get_stock_class_knowledge() -> str:
        """获取股市类象知识"""
        return STOCK_CLASS_KNOWLEDGE


def test_stock_analyzer():
    """测试股票分析器"""
    import random
    analyzer = StockAnalyzer()

    print("=" * 60)
    print("股票行情获取测试")
    print("=" * 60)

    test_codes = ["000001", "600519", "300750"]
    for code in test_codes:
        print(f"\n--- {code} ---")
        quote = analyzer.get_realtime_quote(code)
        if quote:
            print(analyzer.format_quote_for_prompt(quote))
        else:
            print(f"未获取到 {code} 的数据")
        time.sleep(1)

    print("\n" + "=" * 60)
    print("股市类象知识预览")
    print("=" * 60)
    knowledge = StockAnalyzer.get_stock_class_knowledge()
    print(knowledge[:300] + "...")


if __name__ == "__main__":
    test_stock_analyzer()
