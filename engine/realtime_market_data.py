#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时行情数据对接与动态类象调整模块

核心功能：
1. 实时行情采集：大盘/板块/个股数据获取
2. 市场情绪分析：涨跌家数/涨停跌停/成交量
3. 板块轮动追踪：资金流向/热点板块识别
4. 动态类象调整：根据实时行情调整五行/类象映射
5. 与股票规则引擎集成

数据源：AKShare（东方财富/新浪财经）
"""

import os
import sys
import time
import json
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# 抑制AKShare的警告
warnings.filterwarnings('ignore')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("⚠️ akshare 未安装，请运行: pip install akshare")


class MarketDataFetcher:
    """行情数据采集器"""
    
    def __init__(self, cache_ttl: int = 60):
        """
        Args:
            cache_ttl: 缓存有效期（秒）
        """
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.last_update = None
        self._init_stats()
    
    def _init_stats(self):
        """初始化统计"""
        self.stats = {
            "total_fetches": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "cache_hits": 0,
            "last_fetch_time": None,
        }
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        now = time.time()
        if key in self.cache:
            cached_time, data = self.cache[key]
            if now - cached_time < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """设置缓存"""
        self.cache[key] = (time.time(), data)
    
    def fetch_market_overview(self) -> Dict:
        """获取大盘概览"""
        cache_key = "market_overview"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_market_overview()
            
            # 获取A股实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return self._get_mock_market_overview()
            
            # 计算市场指标
            total_stocks = len(df)
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])
            limit_up = len(df[df['涨跌幅'] >= 9.9])
            limit_down = len(df[df['涨跌幅'] <= -9.9])
            
            # 计算成交量
            total_volume = df['成交额'].sum() if '成交额' in df.columns else 0
            total_turnover = df['成交量'].sum() if '成交量' in df.columns else 0
            
            # 计算平均涨跌幅
            avg_change = df['涨跌幅'].mean() if '涨跌幅' in df.columns else 0
            median_change = df['涨跌幅'].median() if '涨跌幅' in df.columns else 0
            
            result = {
                "fetch_time": datetime.now().isoformat(),
                "data_source": "东方财富(akshare)",
                "market_breadth": {
                    "total_stocks": total_stocks,
                    "up_count": int(up_count),
                    "down_count": int(down_count),
                    "flat_count": int(flat_count),
                    "limit_up": int(limit_up),
                    "limit_down": int(limit_down),
                    "up_ratio": round(up_count / max(total_stocks, 1) * 100, 2),
                    "limit_up_ratio": round(limit_up / max(total_stocks, 1) * 100, 2),
                },
                "market_sentiment": {
                    "avg_change": round(float(avg_change), 3),
                    "median_change": round(float(median_change), 3),
                    "total_volume": float(total_volume),
                    "market_status": self._determine_market_status(
                        up_count, down_count, limit_up, limit_down, avg_change
                    ),
                },
                "top_gainers": self._get_top_n(df, '涨跌幅', 10, ascending=False),
                "top_losers": self._get_top_n(df, '涨跌幅', 10, ascending=True),
                "most_active": self._get_top_n(df, '成交额', 10, ascending=False) if '成交额' in df.columns else [],
            }
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            self.stats["last_fetch_time"] = result["fetch_time"]
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 大盘数据获取失败: {e}")
            return self._get_mock_market_overview()
    
    def fetch_sector_data(self) -> Dict:
        """获取板块数据"""
        cache_key = "sector_data"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_sector_data()
            
            # 获取板块行情
            sector_df = ak.stock_board_industry_name_em()
            
            if sector_df is None or sector_df.empty:
                return self._get_mock_sector_data()
            
            # 计算板块涨跌
            if '涨跌幅' in sector_df.columns:
                sector_df = sector_df.sort_values('涨跌幅', ascending=False)
            
            # 获取前10领涨和领跌板块
            top_sectors = []
            bottom_sectors = []
            
            for _, row in sector_df.head(10).iterrows():
                top_sectors.append({
                    "name": row.get('板块名称', row.get('名称', '')),
                    "change": float(row.get('涨跌幅', 0)),
                    "up_count": int(row.get('上涨家数', 0)),
                    "down_count": int(row.get('下跌家数', 0)),
                })
            
            for _, row in sector_df.tail(10).iterrows():
                bottom_sectors.append({
                    "name": row.get('板块名称', row.get('名称', '')),
                    "change": float(row.get('涨跌幅', 0)),
                    "up_count": int(row.get('上涨家数', 0)),
                    "down_count": int(row.get('下跌家数', 0)),
                })
            
            result = {
                "fetch_time": datetime.now().isoformat(),
                "data_source": "东方财富(akshare)",
                "top_sectors": top_sectors,
                "bottom_sectors": bottom_sectors,
                "sector_count": len(sector_df),
                "hot_sectors": self._identify_hot_sectors(top_sectors),
                "rotation_signal": self._analyze_rotation(top_sectors, bottom_sectors),
            }
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 板块数据获取失败: {e}")
            return self._get_mock_sector_data()
    
    def fetch_stock_detail(self, stock_code: str) -> Dict:
        """获取个股详细数据"""
        cache_key = f"stock_{stock_code}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_stock_detail(stock_code)
            
            # 获取个股实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return self._get_mock_stock_detail(stock_code)
            
            # 查找指定股票
            stock_row = df[df['代码'] == stock_code]
            
            if stock_row.empty:
                return self._get_mock_stock_detail(stock_code)
            
            row = stock_row.iloc[0]
            
            result = {
                "fetch_time": datetime.now().isoformat(),
                "code": stock_code,
                "name": str(row.get('名称', '')),
                "price": float(row.get('最新价', 0)),
                "change": float(row.get('涨跌幅', 0)),
                "volume": float(row.get('成交额', 0)) if '成交额' in row.index else 0,
                "turnover_rate": float(row.get('换手率', 0)) if '换手率' in row.index else 0,
                "amplitude": float(row.get('振幅', 0)) if '振幅' in row.index else 0,
            }
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 个股数据获取失败({stock_code}): {e}")
            return self._get_mock_stock_detail(stock_code)
    
    def _get_top_n(self, df: pd.DataFrame, column: str, n: int, 
                   ascending: bool = False) -> List[Dict]:
        """获取前N名"""
        try:
            if column not in df.columns:
                return []
            top = df.nlargest(n, column) if not ascending else df.nsmallest(n, column)
            result = []
            for _, row in top.iterrows():
                item = {}
                for col in ['代码', '名称', '最新价', '涨跌幅', '成交额']:
                    if col in row.index:
                        item[col] = row[col]
                result.append(item)
            return result
        except Exception:
            return []
    
    def _determine_market_status(self, up: int, down: int, 
                                  limit_up: int, limit_down: int,
                                  avg_change: float) -> str:
        """判断市场状态"""
        total = up + down
        if total == 0:
            return "中性"
        
        up_ratio = up / total
        limit_ratio = (limit_up - limit_down) / max(total, 1)
        
        if up_ratio > 0.7 and limit_ratio > 0.05:
            return "强势上涨"
        elif up_ratio > 0.6:
            return "震荡偏多"
        elif up_ratio < 0.3 and limit_ratio < -0.05:
            return "强势下跌"
        elif up_ratio < 0.4:
            return "震荡偏空"
        elif abs(avg_change) < 0.3:
            return "横盘震荡"
        else:
            return "中性"
    
    def _identify_hot_sectors(self, top_sectors: List[Dict]) -> List[str]:
        """识别热点板块"""
        hot = []
        for sector in top_sectors[:5]:
            change = sector.get('change', 0)
            if change > 2.0:
                hot.append(sector['name'])
        return hot
    
    def _analyze_rotation(self, top: List[Dict], 
                           bottom: List[Dict]) -> Dict:
        """分析板块轮动"""
        if not top or not bottom:
            return {"rotation_signal": "无", "detail": ""}
        
        top_avg = np.mean([s['change'] for s in top[:3]])
        bottom_avg = np.mean([s['change'] for s in bottom[:3]])
        
        if top_avg > 3 and bottom_avg < -1:
            signal = "强势轮动"
            detail = f"领涨板块平均涨幅{top_avg:.1f}%，领跌板块平均跌幅{bottom_avg:.1f}%"
        elif top_avg > 1 and bottom_avg > 0:
            signal = "普涨格局"
            detail = f"所有板块均上涨，领涨{top_avg:.1f}%"
        elif top_avg < 0 and bottom_avg < -1:
            signal = "普跌格局"
            detail = f"大部分板块下跌，领跌{bottom_avg:.1f}%"
        else:
            signal = "分化格局"
            detail = f"板块分化，领涨{top_avg:.1f}%，领跌{bottom_avg:.1f}%"
        
        return {"rotation_signal": signal, "detail": detail}
    
    def _get_mock_market_overview(self) -> Dict:
        """获取模拟大盘数据（用于API不可用时）"""
        return {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "模拟数据(离线模式)",
            "market_breadth": {
                "total_stocks": 5000,
                "up_count": 3000,
                "down_count": 1800,
                "flat_count": 200,
                "limit_up": 85,
                "limit_down": 12,
                "up_ratio": 60.0,
                "limit_up_ratio": 1.7,
            },
            "market_sentiment": {
                "avg_change": 0.35,
                "median_change": 0.12,
                "total_volume": 850000000000,
                "market_status": "震荡偏多",
            },
            "top_gainers": [],
            "top_losers": [],
            "most_active": [],
            "mock_data": True,
        }
    
    def _get_mock_sector_data(self) -> Dict:
        """获取模拟板块数据"""
        return {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "模拟数据(离线模式)",
            "top_sectors": [
                {"name": "白酒", "change": 3.5, "up_count": 15, "down_count": 2},
                {"name": "芯片", "change": 2.8, "up_count": 20, "down_count": 5},
                {"name": "新能源", "change": 2.2, "up_count": 25, "down_count": 8},
            ],
            "bottom_sectors": [
                {"name": "煤炭", "change": -1.5, "up_count": 5, "down_count": 20},
                {"name": "钢铁", "change": -1.2, "up_count": 8, "down_count": 18},
            ],
            "sector_count": 80,
            "hot_sectors": ["白酒", "芯片"],
            "rotation_signal": {"rotation_signal": "震荡偏多", "detail": ""},
            "mock_data": True,
        }
    
    def _get_mock_stock_detail(self, code: str) -> Dict:
        """获取模拟个股数据"""
        return {
            "fetch_time": datetime.now().isoformat(),
            "code": code,
            "name": "示例股票",
            "price": 10.0,
            "change": 1.5,
            "volume": 500000000,
            "turnover_rate": 2.5,
            "amplitude": 3.2,
            "mock_data": True,
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "akshare_available": AKSHARE_AVAILABLE,
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
    
    def fetch_northbound_data(self) -> Dict:
        """获取北向资金数据（沪深港通）
        
        包含：
        - 北向资金净流入
        - 沪股通/深股通分别净流入
        - 累计净流入
        - 资金流向趋势
        """
        cache_key = "northbound_data"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_northbound_data()
            
            # 尝试获取北向资金净流入数据
            net_flow_df = None
            try:
                net_flow_df = ak.stock_hsgt_north_net_flow_in_em()
            except Exception:
                pass
            
            # 尝试获取北向资金持股数据
            holding_df = None
            try:
                holding_df = ak.stock_hsgt_north_holding_em()
            except Exception:
                pass
            
            result = self._process_northbound_data(net_flow_df, holding_df)
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 北向资金数据获取失败: {e}")
            return self._get_mock_northbound_data()
    
    def fetch_margin_trading_data(self) -> Dict:
        """获取融资融券数据
        
        包含：
        - 融资余额
        - 融券余额
        - 融资买入额
        - 融券卖出量
        - 融资融券余额趋势
        """
        cache_key = "margin_trading_data"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_margin_trading_data()
            
            # 尝试获取上交所融资融券数据
            sse_df = None
            try:
                sse_df = ak.stock_margin_detail_sse()
            except Exception:
                pass
            
            # 尝试获取深交所融资融券数据
            szse_df = None
            try:
                szse_df = ak.stock_margin_detail_szse()
            except Exception:
                pass
            
            result = self._process_margin_trading_data(sse_df, szse_df)
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 融资融券数据获取失败: {e}")
            return self._get_mock_margin_trading_data()
    
    def fetch_capital_flow_data(self) -> Dict:
        """获取资金流向汇总（北向资金+融资融券）"""
        cache_key = "capital_flow_data"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self.stats["total_fetches"] += 1
        
        try:
            # 获取北向资金
            northbound = self.fetch_northbound_data()
            
            # 获取融资融券
            margin = self.fetch_margin_trading_data()
            
            # 汇总资金流向数据
            result = {
                "fetch_time": datetime.now().isoformat(),
                "data_source": "东方财富(akshare)",
                "northbound": northbound,
                "margin_trading": margin,
                "capital_flow_summary": self._summarize_capital_flow(northbound, margin),
            }
            
            self._set_cache(cache_key, result)
            self.stats["successful_fetches"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_fetches"] += 1
            print(f"⚠️ 资金流向数据获取失败: {e}")
            return self._get_mock_capital_flow_data()
    
    def _process_northbound_data(self, net_flow_df, holding_df) -> Dict:
        """处理北向资金数据"""
        result = {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "东方财富(akshare)",
            "has_data": False,
        }
        
        # 处理净流入数据
        if net_flow_df is not None and not net_flow_df.empty:
            try:
                # 获取最新日期的数据
                latest = net_flow_df.iloc[-1] if len(net_flow_df) > 0 else None
                
                if latest is not None:
                    result["has_data"] = True
                    
                    # 解析字段（不同版本akshare字段名可能不同）
                    net_flow = 0
                    sh_flow = 0
                    sz_flow = 0
                    
                    for col in net_flow_df.columns:
                        col_lower = col.lower() if isinstance(col, str) else str(col)
                        if '净' in str(col) and '额' in str(col):
                            net_flow = float(latest[col]) if pd.notna(latest[col]) else 0
                        elif '沪' in str(col) and ('净' in str(col) or '额' in str(col)):
                            sh_flow = float(latest[col]) if pd.notna(latest[col]) else 0
                        elif '深' in str(col) and ('净' in str(col) or '额' in str(col)):
                            sz_flow = float(latest[col]) if pd.notna(latest[col]) else 0
                    
                    result["net_flow"] = net_flow  # 万元
                    result["sh_net_flow"] = sh_flow  # 沪股通
                    result["sz_net_flow"] = sz_flow  # 深股通
                    
                    # 计算最近5日趋势
                    if len(net_flow_df) >= 5:
                        recent_5 = net_flow_df.tail(5)
                        flows = []
                        for _, row in recent_5.iterrows():
                            flow_val = 0
                            for col in net_flow_df.columns:
                                if '净' in str(col) and '额' in str(col):
                                    flow_val = float(row[col]) if pd.notna(row[col]) else 0
                                    break
                            flows.append(flow_val)
                        
                        result["recent_5_day_flow"] = flows
                        result["flow_trend"] = self._calculate_flow_trend(flows)
                        
            except Exception as e:
                print(f"  北向数据解析异常: {e}")
        
        # 处理持股数据
        if holding_df is not None and not holding_df.empty:
            try:
                total_holding = 0
                if len(holding_df) > 0:
                    for col in holding_df.columns:
                        if '持' in str(col) and '股' in str(col):
                            total_holding = float(holding_df[col].sum())
                            break
                    result["total_holding"] = total_holding  # 万股
                    result["holding_count"] = len(holding_df)
                    result["has_data"] = True
            except Exception:
                pass
        
        # 如无数据，使用模拟数据
        if not result.get("has_data", False):
            result = self._get_mock_northbound_data()
        
        return result
    
    def _process_margin_trading_data(self, sse_df, szse_df) -> Dict:
        """处理融资融券数据"""
        result = {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "东方财富(akshare)",
            "has_data": False,
            "total_margin_balance": 0,  # 融资融券总余额
            "financing_balance": 0,  # 融资余额
            "short_balance": 0,  # 融券余额
            "financing_buy": 0,  # 融资买入额
            "short_sell": 0,  # 融券卖出量
        }
        
        try:
            all_dfs = []
            if sse_df is not None and not sse_df.empty:
                all_dfs.append(("SSE", sse_df))
            if szse_df is not None and not szse_df.empty:
                all_dfs.append(("SZSE", szse_df))
            
            if all_dfs:
                result["has_data"] = True
                
                for market_name, df in all_dfs:
                    if len(df) > 0:
                        latest = df.iloc[-1]
                        
                        for col in df.columns:
                            col_str = str(col)
                            # 融资余额
                            if '融资' in col_str and '余额' in col_str:
                                val = float(latest[col]) if pd.notna(latest[col]) else 0
                                result["financing_balance"] += val
                            # 融券余额
                            elif '融券' in col_str and '余额' in col_str:
                                val = float(latest[col]) if pd.notna(latest[col]) else 0
                                result["short_balance"] += val
                            # 融资买入
                            elif '融资' in col_str and ('买入' in col_str or '额' in col_str):
                                val = float(latest[col]) if pd.notna(latest[col]) else 0
                                result["financing_buy"] += val
                            # 融券卖出
                            elif '融券' in col_str and ('卖出' in col_str or '量' in col_str):
                                val = float(latest[col]) if pd.notna(latest[col]) else 0
                                result["short_sell"] += val
                
                result["total_margin_balance"] = result["financing_balance"] + result["short_balance"]
                
                # 计算融资融券趋势
                if len(all_dfs) > 0:
                    result["margin_trend"] = self._calculate_margin_trend(all_dfs)
                    
        except Exception as e:
            print(f"  融资融券数据解析异常: {e}")
        
        # 如无数据，使用模拟数据
        if not result.get("has_data", False):
            result = self._get_mock_margin_trading_data()
        
        return result
    
    def _calculate_flow_trend(self, flows: List[float]) -> str:
        """计算资金流向趋势"""
        if len(flows) < 3:
            return "数据不足"
        
        # 计算最近3日平均值
        recent_avg = np.mean(flows[-3:])
        # 计算之前的平均值
        earlier_avg = np.mean(flows[:-3]) if len(flows) > 3 else flows[0]
        
        if recent_avg > 0 and recent_avg > earlier_avg * 1.2:
            return "加速流入"
        elif recent_avg > 0 and recent_avg >= earlier_avg:
            return "持续流入"
        elif recent_avg < 0 and recent_avg < earlier_avg * 1.2:
            return "加速流出"
        elif recent_avg < 0 and recent_avg <= earlier_avg:
            return "持续流出"
        elif abs(recent_avg) < abs(earlier_avg) * 0.5:
            return "流入减缓" if recent_avg > 0 else "流出减缓"
        else:
            return "波动"
    
    def _calculate_margin_trend(self, all_dfs) -> str:
        """计算融资融券趋势"""
        try:
            # 获取最近5日数据计算趋势
            for market_name, df in all_dfs:
                if len(df) >= 5:
                    # 找融资余额列
                    balance_col = None
                    for col in df.columns:
                        if '融资' in str(col) and '余额' in str(col):
                            balance_col = col
                            break
                    
                    if balance_col:
                        recent_5 = df[balance_col].tail(5).dropna()
                        if len(recent_5) >= 3:
                            recent_avg = recent_5.iloc[-3:].mean()
                            earlier_avg = recent_5.iloc[:-3].mean() if len(recent_5) > 3 else recent_5.iloc[0]
                            
                            if recent_avg > earlier_avg * 1.05:
                                return "融资余额上升"
                            elif recent_avg < earlier_avg * 0.95:
                                return "融资余额下降"
                            else:
                                return "融资余额稳定"
        except Exception:
            pass
        
        return "数据不足"
    
    def _summarize_capital_flow(self, northbound: Dict, margin: Dict) -> Dict:
        """汇总资金流向分析"""
        net_flow = northbound.get("net_flow", 0)
        flow_trend = northbound.get("flow_trend", "未知")
        margin_balance = margin.get("total_margin_balance", 0)
        margin_trend = margin.get("margin_trend", "未知")
        
        # 判断资金面整体状态
        capital_status = "中性"
        reasons = []
        
        # 北向资金分析
        if net_flow > 50:  # 净流入超过50亿
            capital_status = "资金流入"
            reasons.append(f"北向资金大幅净流入({net_flow:.0f}万元)")
        elif net_flow > 0:
            reasons.append(f"北向资金小幅净流入({net_flow:.0f}万元)")
        elif net_flow < -50:
            capital_status = "资金流出"
            reasons.append(f"北向资金大幅净流出({abs(net_flow):.0f}万元)")
        elif net_flow < 0:
            reasons.append(f"北向资金小幅净流出({abs(net_flow):.0f}万元)")
        
        # 融资融券分析
        if margin_trend == "融资余额上升":
            reasons.append("融资买入增加，看多情绪增强")
            if capital_status == "中性":
                capital_status = "资金流入"
        elif margin_trend == "融资余额下降":
            reasons.append("融资偿还增加，看空情绪增强")
            if capital_status == "中性":
                capital_status = "资金流出"
        
        # 计算资金面情绪指标 (-1到1)
        sentiment_score = 0.0
        
        # 北向资金贡献
        if net_flow > 100:
            sentiment_score += 0.4
        elif net_flow > 50:
            sentiment_score += 0.3
        elif net_flow > 0:
            sentiment_score += 0.1
        elif net_flow < -100:
            sentiment_score -= 0.4
        elif net_flow < -50:
            sentiment_score -= 0.3
        elif net_flow < 0:
            sentiment_score -= 0.1
        
        # 融资融券贡献
        if margin_trend == "融资余额上升":
            sentiment_score += 0.2
        elif margin_trend == "融资余额下降":
            sentiment_score -= 0.2
        
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        return {
            "capital_status": capital_status,
            "sentiment_score": round(sentiment_score, 2),
            "flow_trend": flow_trend,
            "margin_trend": margin_trend,
            "reasons": reasons,
        }
    
    def _get_mock_northbound_data(self) -> Dict:
        """获取模拟北向资金数据"""
        return {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "模拟数据(离线模式)",
            "has_data": False,
            "net_flow": 350000,  # 35亿净流入
            "sh_net_flow": 200000,  # 沪股通20亿
            "sz_net_flow": 150000,  # 深股通15亿
            "total_holding": 1250000,  # 北向资金总持股1250万股
            "holding_count": 520,  # 持股520只股票
            "recent_5_day_flow": [280000, 320000, 290000, 350000, 380000],
            "flow_trend": "持续流入",
            "mock_data": True,
        }
    
    def _get_mock_margin_trading_data(self) -> Dict:
        """获取模拟融资融券数据"""
        return {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "模拟数据(离线模式)",
            "has_data": False,
            "total_margin_balance": 1850000000000,  # 融资融券总余额1.85万亿
            "financing_balance": 1720000000000,  # 融资余额1.72万亿
            "short_balance": 130000000000,  # 融券余额1300亿
            "financing_buy": 85000000000,  # 融资买入850亿
            "short_sell": 12000000000,  # 融券卖出120亿
            "margin_trend": "融资余额上升",
            "mock_data": True,
        }
    
    def _get_mock_capital_flow_data(self) -> Dict:
        """获取模拟资金流向汇总"""
        northbound = self._get_mock_northbound_data()
        margin = self._get_mock_margin_trading_data()
        summary = self._summarize_capital_flow(northbound, margin)
        
        return {
            "fetch_time": datetime.now().isoformat(),
            "data_source": "模拟数据(离线模式)",
            "northbound": northbound,
            "margin_trading": margin,
            "capital_flow_summary": summary,
            "mock_data": True,
        }


class DynamicLeixiangAdjuster:
    """动态类象调整器
    
    根据实时行情数据动态调整股票类象映射：
    1. 市场情绪影响：牛市增强木/火，熊市增强金/水
    2. 板块轮动影响：热门行业临时增强对应五行
    3. 个股异动影响：放量突破调整类象强度
    4. 时间周期影响：季节性调整
    5. 资金面影响：北向资金和融资融券调整五行权重
    """
    
    # 市场状态对应的五行增强
    MARKET_WUXING_BOOST = {
        "强势上涨": {"木": 1.2, "火": 1.3, "金": 0.9},
        "震荡偏多": {"木": 1.1, "火": 1.15, "土": 1.05},
        "横盘震荡": {"土": 1.1, "金": 1.05},
        "震荡偏空": {"金": 1.15, "水": 1.1, "木": 0.9},
        "强势下跌": {"金": 1.3, "水": 1.25, "木": 0.8, "火": 0.85},
        "中性": {},
    }
    
    # 热点板块对应的五行增强
    SECTOR_WUXING_BOOST = {
        # 热门板块 → 增强对应行业的五行权重
        "白酒": {"木": 1.2},
        "食品饮料": {"木": 1.15},
        "医药": {"木": 1.15},
        "芯片": {"火": 1.25},
        "半导体": {"火": 1.25},
        "人工智能": {"火": 1.3},
        "AI": {"火": 1.3},
        "新能源": {"水": 1.2},
        "光伏": {"水": 1.2},
        "储能": {"水": 1.2},
        "锂电池": {"木": 1.2},
        "汽车": {"木": 1.15},
        "军工": {"金": 1.2},
        "银行": {"金": 1.15},
        "券商": {"金": 1.2},
        "房地产": {"土": 1.2},
        "基建": {"土": 1.15},
        "煤炭": {"金": 1.1},
        "石油": {"金": 1.15},
        "有色": {"金": 1.15},
        "钢铁": {"金": 1.1},
        "电力": {"水": 1.15},
        "环保": {"水": 1.1},
    }
    
    # 资金面状态对应的五行增强
    # 北向资金大幅流入/融资余额上升 → 增强木/火（财富/活力）
    # 北向资金大幅流出/融资余额下降 → 增强金/水（防御/流动性）
    CAPITAL_WUXING_BOOST = {
        # 资金流入状态
        "资金大幅流入": {"木": 1.12, "火": 1.15},
        "资金持续流入": {"木": 1.08, "火": 1.10},
        "资金加速流入": {"木": 1.15, "火": 1.18},
        # 资金流出状态
        "资金大幅流出": {"金": 1.15, "水": 1.12},
        "资金持续流出": {"金": 1.12, "水": 1.08},
        "资金加速流出": {"金": 1.18, "水": 1.15},
        # 融资融券状态
        "融资余额上升": {"木": 1.06, "火": 1.08},
        "融资余额下降": {"金": 1.08, "水": 1.06},
        # 中性状态
        "资金中性": {},
        "未知": {},
    }
    
    # 资金面情绪指标阈值
    CAPITAL_SENTIMENT_THRESHOLDS = {
        # 情绪评分区间 → 调整描述
        "strong_inflow": 0.5,   # 情绪评分 > 0.5 → 强势流入
        "mild_inflow": 0.15,    # 情绪评分 > 0.15 → 温和流入
        "neutral_upper": 0.15,  # -0.15 ~ 0.15 → 中性
        "mild_outflow": -0.15,  # 情绪评分 < -0.15 → 温和流出
        "strong_outflow": -0.5,  # 情绪评分 < -0.5 → 强势流出
    }
    
    def __init__(self):
        self.current_adjustments = {}
        self.market_data = None
        self.sector_data = None
        self.capital_flow_data = None
        self.last_update = None
        self.regression_adapter = None  # 回归模型适配器
        self.use_regression = False  # 是否使用回归模型优化
        self._init_regression_adapter()
    
    def _init_regression_adapter(self):
        """初始化回归模型适配器"""
        try:
            from engine.sentiment_wuxing_model import RegressionModelAdapter
            
            model_path = os.path.join(_ROOT, "data", "sentiment_model", "best_lasso_model.pkl")
            if os.path.exists(model_path):
                self.regression_adapter = RegressionModelAdapter()
                self.regression_adapter.load_model(model_path)
                self.use_regression = self.regression_adapter.is_available
                if self.use_regression:
                    print(f"✅ 回归模型已加载 (准确率: {self.regression_adapter.model_accuracy:.4f})")
                else:
                    print("⚠️ 回归模型加载失败，使用规则引擎模式")
            else:
                print("⚠️ 回归模型文件不存在，使用规则引擎模式")
        except ImportError:
            print("⚠️ 回归模型模块不可用，使用规则引擎模式")
        except Exception as e:
            print(f"⚠️ 回归模型初始化失败: {e}")
            self.use_regression = False
    
    def update_market_data(self, market_data: Dict):
        """更新市场数据"""
        self.market_data = market_data
        self.last_update = datetime.now().isoformat()
        self._recalculate_adjustments()
    
    def update_sector_data(self, sector_data: Dict):
        """更新板块数据"""
        self.sector_data = sector_data
        self._recalculate_adjustments()
    
    def update_capital_flow_data(self, capital_flow_data: Dict):
        """更新资金流向数据
        
        Args:
            capital_flow_data: 资金流向数据字典，包含：
                - northbound: 北向资金数据
                - margin_trading: 融资融券数据
                - capital_flow_summary: 资金流向汇总分析
        """
        self.capital_flow_data = capital_flow_data
        self.last_update = datetime.now().isoformat()
        self._recalculate_adjustments()
    
    def _recalculate_adjustments(self):
        """重新计算调整系数
        
        调整优先级：
        1. 规则引擎调整（市场情绪 > 板块轮动 > 资金面）
        2. 回归模型优化（如果可用，与规则引擎结果融合）
        最终调整范围控制在 ±20% 以内
        """
        adjustments = {}
        
        # 1. 市场情绪调整
        if self.market_data:
            sentiment = self.market_data.get("market_sentiment", {})
            market_status = sentiment.get("market_status", "中性")
            market_breadth = self.market_data.get("market_breadth", {})
            
            # 获取市场状态对应的五行增强
            wuxing_boost = self.MARKET_WUXING_BOOST.get(market_status, {})
            
            for wx, multiplier in wuxing_boost.items():
                adjustments[wx] = adjustments.get(wx, 1.0) * multiplier
            
            # 涨停数量额外增强
            limit_up = market_breadth.get("limit_up", 0)
            if limit_up > 50:
                # 涨停超过50只，增强木火（财富/活力）
                adjustments["木"] = adjustments.get("木", 1.0) * 1.05
                adjustments["火"] = adjustments.get("火", 1.0) * 1.05
            elif limit_up < 10:
                # 涨停少于10只，增强金水（防御/流动性）
                adjustments["金"] = adjustments.get("金", 1.0) * 1.03
                adjustments["水"] = adjustments.get("水", 1.0) * 1.03
        
        # 2. 板块轮动调整
        if self.sector_data:
            hot_sectors = self.sector_data.get("hot_sectors", [])
            top_sectors = self.sector_data.get("top_sectors", [])
            
            # 热点板块增强
            for sector_name in hot_sectors:
                boost = self.SECTOR_WUXING_BOOST.get(sector_name, {})
                for wx, multiplier in boost.items():
                    # 临时增强，倍数更高
                    adjusted_multiplier = multiplier * 1.1  # 热点板块额外+10%
                    adjustments[wx] = adjustments.get(wx, 1.0) * adjusted_multiplier
            
            # 领涨板块增强
            if top_sectors:
                for sector in top_sectors[:3]:
                    name = sector.get("name", "")
                    change = sector.get("change", 0)
                    if change > 3:
                        boost = self.SECTOR_WUXING_BOOST.get(name, {})
                        for wx, multiplier in boost.items():
                            adjustments[wx] = adjustments.get(wx, 1.0) * multiplier
        
        # 3. 资金面调整（北向资金 + 融资融券）
        if self.capital_flow_data:
            capital_adjustments = self._calculate_capital_adjustments()
            for wx, multiplier in capital_adjustments.items():
                if wx in adjustments:
                    adjustments[wx] = adjustments[wx] * multiplier
                else:
                    adjustments[wx] = multiplier
        
        # 4. 回归模型优化（如果可用）
        if self.use_regression and self.regression_adapter:
            try:
                regression_adjustments = self.regression_adapter.predict_adjustments(
                    self.market_data, self.sector_data, self.capital_flow_data
                )
                
                # 融合规则引擎和回归模型结果
                # 规则引擎权重 0.6，回归模型权重 0.4
                rule_weight = 0.6
                ml_weight = 0.4
                
                for wx in ["木", "火", "土", "金", "水"]:
                    rule_adj = adjustments.get(wx, 1.0)
                    ml_adj = regression_adjustments.get(wx, 1.0)
                    
                    # 加权融合
                    fused_adj = rule_adj * rule_weight + ml_adj * ml_weight
                    adjustments[wx] = fused_adj
            except Exception:
                # 回归模型失败时回退到规则引擎
                pass
        
        # 5. 限制调整范围在 ±20% 以内
        adjustments = self._clamp_adjustments(adjustments)
        
        self.current_adjustments = adjustments
    
    def _calculate_capital_adjustments(self) -> Dict:
        """计算资金面对五行的调整系数
        
        基于北向资金流向和融资融券趋势，转换为五行调整系数：
        - 北向资金大幅流入 → 增强木/火（财富/活力）
        - 北向资金大幅流出 → 增强金/水（防御/流动性）
        - 融资余额上升 → 增强木/火（看多情绪）
        - 融资余额下降 → 增强金/水（看空情绪）
        """
        adjustments = {}
        
        # 获取资金流向汇总
        summary = self.capital_flow_data.get("capital_flow_summary", {})
        northbound = self.capital_flow_data.get("northbound", {})
        margin = self.capital_flow_data.get("margin_trading", {})
        
        # 获取资金面情绪指标
        sentiment_score = summary.get("sentiment_score", 0)
        capital_status = summary.get("capital_status", "中性")
        flow_trend = summary.get("flow_trend", "未知")
        margin_trend = summary.get("margin_trend", "未知")
        
        # 基于情绪评分计算资金状态
        threshold = self.CAPITAL_SENTIMENT_THRESHOLDS
        
        if sentiment_score > threshold["strong_inflow"]:
            # 强势流入
            capital_boost_key = "资金大幅流入"
        elif sentiment_score > threshold["mild_inflow"]:
            # 温和流入
            if flow_trend == "加速流入":
                capital_boost_key = "资金加速流入"
            elif flow_trend == "持续流入":
                capital_boost_key = "资金持续流入"
            else:
                capital_boost_key = "资金持续流入"
        elif sentiment_score < threshold["strong_outflow"]:
            # 强势流出
            capital_boost_key = "资金大幅流出"
        elif sentiment_score < threshold["mild_outflow"]:
            # 温和流出
            if flow_trend == "加速流出":
                capital_boost_key = "资金加速流出"
            elif flow_trend == "持续流出":
                capital_boost_key = "资金持续流出"
            else:
                capital_boost_key = "资金持续流出"
        else:
            # 中性
            capital_boost_key = "资金中性"
        
        # 应用资金状态的五行增强
        capital_boost = self.CAPITAL_WUXING_BOOST.get(capital_boost_key, {})
        for wx, multiplier in capital_boost.items():
            adjustments[wx] = adjustments.get(wx, 1.0) * multiplier
        
        # 融资融券趋势调整
        if margin_trend in self.CAPITAL_WUXING_BOOST:
            margin_boost = self.CAPITAL_WUXING_BOOST[margin_trend]
            for wx, multiplier in margin_boost.items():
                adjustments[wx] = adjustments.get(wx, 1.0) * multiplier * 0.5  # 融资融券权重减半
        
        return adjustments
    
    def _clamp_adjustments(self, adjustments: Dict) -> Dict:
        """限制调整系数在 ±20% 以内
        
        Args:
            adjustments: 原始调整系数
            
        Returns:
            限制后的调整系数
        """
        clamped = {}
        for wx, multiplier in adjustments.items():
            # 限制在 0.8 ~ 1.2 之间
            clamped[wx] = max(0.8, min(1.2, multiplier))
        return clamped
    
    def set_regression_enabled(self, enabled: bool):
        """启用/禁用回归模型
        
        Args:
            enabled: 是否启用
        """
        if enabled and self.regression_adapter and self.regression_adapter.is_available:
            self.use_regression = True
            self._recalculate_adjustments()
            print("✅ 回归模型已启用")
        elif not enabled:
            self.use_regression = False
            self._recalculate_adjustments()
            print("⚠️ 回归模型已禁用，使用规则引擎")
        else:
            print("⚠️ 回归模型不可用，无法启用")
    
    def retrain_regression_model(self, days: int = 365, model_type: str = "lasso") -> bool:
        """重新训练回归模型
        
        Args:
            days: 训练数据天数
            model_type: 模型类型
            
        Returns:
            是否成功
        """
        try:
            from engine.sentiment_wuxing_model import RegressionModelAdapter
            
            print(f"🔄 正在重新训练回归模型 ({model_type}, {days}天)...")
            self.regression_adapter = RegressionModelAdapter()
            save_path = os.path.join(_ROOT, "data", "sentiment_model", "best_lasso_model.pkl")
            training_stats = self.regression_adapter.train_and_save(
                days=days, model_type=model_type, save_path=save_path
            )
            
            self.use_regression = self.regression_adapter.is_available
            if self.use_regression:
                self._recalculate_adjustments()
                print(f"✅ 回归模型重训练完成，准确率: {self.regression_adapter.model_accuracy:.4f}")
            return True
        except Exception as e:
            print(f"❌ 回归模型重训练失败: {e}")
            return False
    
    def load_regression_model(self, model_path: str) -> bool:
        """加载指定的回归模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            是否成功
        """
        try:
            from engine.sentiment_wuxing_model import RegressionModelAdapter
            
            self.regression_adapter = RegressionModelAdapter()
            self.regression_adapter.load_model(model_path)
            self.use_regression = self.regression_adapter.is_available
            
            if self.use_regression:
                self._recalculate_adjustments()
                print(f"✅ 回归模型加载成功: {model_path}")
            else:
                print(f"⚠️ 回归模型加载失败: {model_path}")
            return self.use_regression
        except Exception as e:
            print(f"❌ 回归模型加载异常: {e}")
            return False
    
    def get_wuxing_adjustment(self, base_wuxing: str) -> float:
        """获取指定五行的调整系数"""
        if not self.current_adjustments:
            return 1.0
        return self.current_adjustments.get(base_wuxing, 1.0)
    
    def adjust_score(self, base_score: float, stock_wuxing: str) -> float:
        """根据行情调整预测分数
        
        Args:
            base_score: 基础预测分数 (0-1)
            stock_wuxing: 股票行业五行
        
        Returns:
            调整后的分数
        """
        adjustment = self.get_wuxing_adjustment(stock_wuxing)
        
        # 限制调整范围在 ±20%
        adjustment = max(0.8, min(1.2, adjustment))
        
        # 应用调整
        adjusted_score = base_score * adjustment
        
        # 确保在有效范围内
        return max(0.05, min(0.98, adjusted_score))
    
    def get_dynamic_leixiang(self, stock_code: str, 
                              base_leixiang: Dict) -> Dict:
        """获取动态类象（结合实时行情调整）
        
        Args:
            stock_code: 股票代码
            base_leixiang: 基础类象信息
        
        Returns:
            调整后的类象信息
        """
        result = base_leixiang.copy()
        
        # 获取行业五行
        industry_wuxing = base_leixiang.get('industry_wuxing', '土')
        
        # 应用动态调整
        adjustment = self.get_wuxing_adjustment(industry_wuxing)
        result['dynamic_adjustment'] = adjustment
        result['adjusted_wuxing'] = industry_wuxing
        result['dynamic_factor'] = self._describe_adjustment(adjustment)
        
        # 如果有个股实时数据
        stock_detail = None
        # 这里可以接入个股实时数据
        
        return result
    
    def _describe_adjustment(self, adjustment: float) -> str:
        """描述调整情况"""
        if adjustment > 1.15:
            return f"🔥 显著增强(x{adjustment:.2f})"
        elif adjustment > 1.05:
            return f"📈 轻度增强(x{adjustment:.2f})"
        elif adjustment < 0.9:
            return f"📉 显著削弱(x{adjustment:.2f})"
        elif adjustment < 0.95:
            return f"⬇️ 轻度削弱(x{adjustment:.2f})"
        else:
            return f"➡️ 基本稳定(x{adjustment:.2f})"
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        status = {
            "last_update": self.last_update,
            "current_adjustments": self.current_adjustments,
            "market_available": self.market_data is not None,
            "sector_available": self.sector_data is not None,
            "capital_flow_available": self.capital_flow_data is not None,
            "regression_model": {
                "enabled": self.use_regression,
                "available": self.regression_adapter is not None and self.regression_adapter.is_available if self.regression_adapter else False,
                "accuracy": self.regression_adapter.model_accuracy if self.regression_adapter and self.regression_adapter.is_available else 0,
            }
        }
        
        # 添加资金面状态信息
        if self.capital_flow_data:
            summary = self.capital_flow_data.get("capital_flow_summary", {})
            status["capital_flow_status"] = {
                "capital_status": summary.get("capital_status", "未知"),
                "sentiment_score": summary.get("sentiment_score", 0),
                "flow_trend": summary.get("flow_trend", "未知"),
                "margin_trend": summary.get("margin_trend", "未知"),
            }
        
        return status


class RealtimeLeixiangEngine:
    """实时类象引擎（对外统一接口）"""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.adjuster = DynamicLeixiangAdjuster()
        self._initialized = False
        self._capital_flow_enabled = True  # 是否启用资金面分析
    
    def initialize(self, include_capital_flow: bool = True) -> Dict:
        """初始化引擎（获取初始行情数据）
        
        Args:
            include_capital_flow: 是否包含资金面数据（北向资金+融资融券）
        """
        print("🔄 正在初始化实时类象引擎...")
        
        # 获取市场数据
        market_data = self.fetcher.fetch_market_overview()
        self.adjuster.update_market_data(market_data)
        
        # 获取板块数据
        sector_data = self.fetcher.fetch_sector_data()
        self.adjuster.update_sector_data(sector_data)
        
        # 获取资金流向数据
        self._capital_flow_enabled = include_capital_flow
        if include_capital_flow:
            print("   正在获取资金流向数据...")
            capital_flow_data = self.fetcher.fetch_capital_flow_data()
            self.adjuster.update_capital_flow_data(capital_flow_data)
            self._last_capital_flow = capital_flow_data
        
        self._initialized = True
        
        status = self.adjuster.get_status()
        print(f"✅ 实时类象引擎初始化完成")
        print(f"   市场状态: {market_data.get('market_sentiment', {}).get('market_status', '未知')}")
        print(f"   热点板块: {sector_data.get('hot_sectors', [])}")
        if include_capital_flow:
            capital_status = status.get("capital_flow_status", {})
            print(f"   资金状态: {capital_status.get('capital_status', '未知')}")
            print(f"   资金情绪: {capital_status.get('sentiment_score', 0)}")
        print(f"   调整系数: {status['current_adjustments']}")
        
        return status
    
    def refresh(self, include_capital_flow: bool = True) -> Dict:
        """刷新行情数据
        
        Args:
            include_capital_flow: 是否包含资金面数据
        """
        print("🔄 正在刷新行情数据...")
        
        market_data = self.fetcher.fetch_market_overview()
        self.adjuster.update_market_data(market_data)
        
        sector_data = self.fetcher.fetch_sector_data()
        self.adjuster.update_sector_data(sector_data)
        
        # 刷新资金流向数据
        if include_capital_flow:
            capital_flow_data = self.fetcher.fetch_capital_flow_data()
            self.adjuster.update_capital_flow_data(capital_flow_data)
            self._last_capital_flow = capital_flow_data
        
        status = self.adjuster.get_status()
        print(f"✅ 刷新完成")
        print(f"   市场状态: {market_data.get('market_sentiment', {}).get('market_status', '未知')}")
        if include_capital_flow and self._last_capital_flow:
            summary = self._last_capital_flow.get("capital_flow_summary", {})
            print(f"   资金状态: {summary.get('capital_status', '未知')}")
        
        return status
    
    def get_capital_flow_analysis(self) -> Dict:
        """获取资金流向分析结果
        
        Returns:
            资金流向分析字典，包含：
            - northbound: 北向资金数据
            - margin_trading: 融资融券数据
            - summary: 资金流向汇总
        """
        if hasattr(self, '_last_capital_flow') and self._last_capital_flow:
            return self._last_capital_flow
        return {
            "status": "未获取",
            "message": "请先初始化引擎或调用refresh(include_capital_flow=True)",
        }
    
    def adjust_prediction(self, base_score: float, 
                          stock_wuxing: str) -> Dict:
        """调整预测分数"""
        adjusted_score = self.adjuster.adjust_score(base_score, stock_wuxing)
        adjustment = self.adjuster.get_wuxing_adjustment(stock_wuxing)
        
        return {
            "base_score": base_score,
            "adjusted_score": round(adjusted_score, 3),
            "adjustment_factor": round(adjustment, 2),
            "wuxing": stock_wuxing,
            "adjustment_description": self.adjuster._describe_adjustment(adjustment),
        }
    
    def get_engine_status(self) -> Dict:
        """获取引擎状态"""
        return {
            "initialized": self._initialized,
            "capital_flow_enabled": self._capital_flow_enabled,
            "fetcher_stats": self.fetcher.get_stats(),
            "adjuster_status": self.adjuster.get_status(),
        }


def create_realtime_engine() -> RealtimeLeixiangEngine:
    """创建实时类象引擎实例"""
    return RealtimeLeixiangEngine()


if __name__ == "__main__":
    # 测试模块
    print("=" * 60)
    print("🚀 实时行情对接与动态类象调整测试（含资金面分析）")
    print("=" * 60)
    
    # 测试1: 初始化并获取资金面数据
    print("\n" + "=" * 40)
    print("📊 测试1: 完整初始化（含资金面数据）")
    print("=" * 40)
    engine = create_realtime_engine()
    status = engine.initialize(include_capital_flow=True)
    print(f"\n📊 引擎状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    # 测试2: 资金流向分析
    print("\n" + "=" * 40)
    print("💰 测试2: 资金流向分析")
    print("=" * 40)
    capital_analysis = engine.get_capital_flow_analysis()
    print(f"\n资金流向分析结果:")
    if "northbound" in capital_analysis:
        nb = capital_analysis["northbound"]
        print(f"  北向资金净流入: {nb.get('net_flow', 0):.0f} 万元")
        print(f"  沪股通净流入: {nb.get('sh_net_flow', 0):.0f} 万元")
        print(f"  深股通净流入: {nb.get('sz_net_flow', 0):.0f} 万元")
        print(f"  资金流向趋势: {nb.get('flow_trend', '未知')}")
        
        margin = capital_analysis.get("margin_trading", {})
        print(f"  融资余额: {margin.get('financing_balance', 0):.0f} 元")
        print(f"  融资融券趋势: {margin.get('margin_trend', '未知')}")
        
        summary = capital_analysis.get("capital_flow_summary", {})
        print(f"  资金面状态: {summary.get('capital_status', '未知')}")
        print(f"  资金情绪评分: {summary.get('sentiment_score', 0)}")
        print(f"  分析原因: {summary.get('reasons', [])}")
    
    # 测试3: 分数调整（含资金面影响）
    print("\n" + "=" * 40)
    print("📈 测试3: 分数调整（含资金面影响）")
    print("=" * 40)
    test_cases = [
        (0.7, "木"),
        (0.8, "火"),
        (0.6, "金"),
        (0.5, "水"),
        (0.65, "土"),
    ]
    
    print("\n分数调整结果:")
    print(f"  {'五行':<6} {'基础分':<8} {'调整后':<8} {'调整因子':<10} {'描述'}")
    print(f"  {'-'*50}")
    for base_score, wuxing in test_cases:
        result = engine.adjust_prediction(base_score, wuxing)
        print(f"  {wuxing:<6} {base_score:<8.2f} {result['adjusted_score']:<8.3f} {result['adjustment_factor']:<10.2f} {result['adjustment_description']}")
    
    # 测试4: 资金面对比测试
    print("\n" + "=" * 40)
    print("🔍 测试4: 资金面对比（开启 vs 关闭）")
    print("=" * 40)
    
    # 使用模拟的资金流入数据
    print("\n场景1: 资金大幅流入（北向资金+500亿，融资余额上升）")
    inflow_data = {
        "northbound": {
            "net_flow": 5000000,  # 500亿
            "flow_trend": "持续流入",
        },
        "margin_trading": {
            "margin_trend": "融资余额上升",
        },
        "capital_flow_summary": {
            "capital_status": "资金流入",
            "sentiment_score": 0.6,
            "flow_trend": "持续流入",
            "margin_trend": "融资余额上升",
        }
    }
    engine.adjuster.update_capital_flow_data(inflow_data)
    
    print("\n  分数调整结果（资金大幅流入场景）:")
    for base_score, wuxing in test_cases:
        result = engine.adjust_prediction(base_score, wuxing)
        print(f"    {wuxing}: {base_score:.2f} → {result['adjusted_score']:.3f} ({result['adjustment_description']})")
    
    # 使用模拟的资金流出数据
    print("\n场景2: 资金大幅流出（北向资金-500亿，融资余额下降）")
    outflow_data = {
        "northbound": {
            "net_flow": -5000000,  # -500亿
            "flow_trend": "持续流出",
        },
        "margin_trading": {
            "margin_trend": "融资余额下降",
        },
        "capital_flow_summary": {
            "capital_status": "资金流出",
            "sentiment_score": -0.6,
            "flow_trend": "持续流出",
            "margin_trend": "融资余额下降",
        }
    }
    engine.adjuster.update_capital_flow_data(outflow_data)
    
    print("\n  分数调整结果（资金大幅流出场景）:")
    for base_score, wuxing in test_cases:
        result = engine.adjust_prediction(base_score, wuxing)
        print(f"    {wuxing}: {base_score:.2f} → {result['adjusted_score']:.3f} ({result['adjustment_description']})")
    
    # 恢复正常初始化数据
    engine.refresh(include_capital_flow=True)
    
    # 测试5: 引擎状态
    print("\n" + "=" * 40)
    print("📋 测试5: 引擎状态汇总")
    print("=" * 40)
    engine_status = engine.get_engine_status()
    print(f"\n  引擎已初始化: {engine_status['initialized']}")
    print(f"  资金面分析启用: {engine_status['capital_flow_enabled']}")
    print(f"  总获取次数: {engine_status['fetcher_stats']['total_fetches']}")
    print(f"  成功获取次数: {engine_status['fetcher_stats']['successful_fetches']}")
    print(f"  缓存命中率: {engine_status['fetcher_stats']['cache_hits']}")
    
    adjuster_status = engine_status['adjuster_status']
    if 'capital_flow_status' in adjuster_status:
        cs = adjuster_status['capital_flow_status']
        print(f"\n  资金面状态:")
        print(f"    资金状态: {cs.get('capital_status', '未知')}")
        print(f"    情绪评分: {cs.get('sentiment_score', 0)}")
        print(f"    北向趋势: {cs.get('flow_trend', '未知')}")
        print(f"    融资趋势: {cs.get('margin_trend', '未知')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
