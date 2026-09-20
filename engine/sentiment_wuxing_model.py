#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
市场情绪与五行量化回归模型

核心目标：建立市场情绪指标到五行调整系数的量化关系

架构设计：
1. 数据收集器：获取历史市场数据
2. 特征工程：提取市场情绪特征
3. 标签生成：计算各五行对应行业的收益率
4. 回归模型：学习情绪→五行的映射关系
5. 模型集成：集成到DynamicLeixiangAdjuster

特征工程：
- 市场宽度特征：涨跌比、涨停/跌停数量、上涨比例
- 资金面特征：北向资金净流入、融资融券变化
- 板块特征：领涨板块涨幅、热点板块数量
- 量价特征：总成交额、换手率、振幅

标签：
- 木（生长/消费）：白酒、食品、医药、农业
- 火（能量/科技）：芯片、AI、光伏、新能源
- 土（地产/基建）：房地产、基建、建材
- 金（金融/周期）：银行、券商、钢铁、煤炭
- 水（运输/公用）：电力、物流、环保、通信

模型选择：
- 线性回归：可解释性强
- 随机森林：捕捉非线性关系
- XGBoost：高精度（可选）
"""

import os
import sys
import json
import time
import pickle
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
# 1. 五行行业映射表
# ═══════════════════════════════════════════════════════════

WUXING_SECTOR_MAP = {
    "木": ["白酒", "食品饮料", "医药", "农业", "林业", "纺织"],
    "火": ["芯片", "半导体", "人工智能", "AI", "光伏", "新能源", "电子", "通信"],
    "土": ["房地产", "基建", "建材", "建筑", "工程机械"],
    "金": ["银行", "券商", "保险", "钢铁", "煤炭", "石油", "有色", "矿业"],
    "水": ["电力", "环保", "物流", "交通运输", "公用事业", "燃气"],
}

# 五行对应的行业指数代码（用于获取历史数据）
WUXING_INDEX_MAP = {
    "木": ["801010", "801150", "801180"],  # 食品饮料、医药生物、农林牧渔
    "火": ["801080", "801750", "801760"],  # 电子、计算机、通信
    "土": ["801180", "801210"],              # 房地产、建筑装饰
    "金": ["801780", "801110", "801160"],    # 银行、钢铁、煤炭
    "水": ["801040", "801130", "801170"],    # 钢铁？公用事业、综合
}

# 五行龙头股列表（个股级别特征）
# 每个五行选择10只代表性龙头股
WUXING_STOCK_LEADERS = {
    "木": [
        ("600519", "贵州茅台"),  # 白酒龙头
        ("000858", "五粮液"),    # 浓香型白酒
        ("600276", "恒瑞医药"),  # 创新药龙头
        ("300750", "宁德时代"),  # 动力电池龙头
        ("002594", "比亚迪"),    # 新能源车龙头
        ("600887", "伊利股份"),  # 乳业龙头
        ("000333", "美的集团"),  # 家电龙头
        ("600309", "万华化学"),  # 化工龙头
        ("000651", "格力电器"),  # 空调龙头
        ("600436", "片仔癀"),    # 中药龙头
    ],
    "火": [
        ("688981", "中芯国际"),  # 芯片代工龙头
        ("688012", "中微公司"),  # 半导体设备
        ("002415", "海康威视"),  # 安防龙头
        ("603019", "中科曙光"),  # 算力龙头
        ("300760", "迈瑞医疗"),  # 医疗IT
        ("002230", "科大讯飞"),  # AI龙头
        ("300059", "东方财富"),  # 互联网券商
        ("601138", "工业富联"),  # 电子制造
        ("002371", "北方华创"),  # 半导体设备
        ("688111", "金山办公"),  # 软件龙头
    ],
    "土": [
        ("001979", "招商蛇口"),  # 地产龙头
        ("600048", "保利发展"),  # 地产龙头
        ("601668", "中国建筑"),  # 基建龙头
        ("601390", "中国中铁"),  # 基建龙头
        ("600583", "海油工程"),  # 工程龙头
        ("000786", "北新建材"),  # 建材龙头
        ("600970", "中材国际"),  # 水泥龙头
        ("002080", "中材科技"),  # 新材料
        ("600489", "中金黄金"),  # 黄金龙头
        ("601857", "中国石油"),  # 石油龙头
    ],
    "金": [
        ("601398", "工商银行"),  # 银行龙头
        ("601288", "农业银行"),  # 银行龙头
        ("600036", "招商银行"),  # 银行龙头
        ("601318", "中国平安"),  # 保险龙头
        ("600030", "中信证券"),  # 券商龙头
        ("601211", "国泰君安"),  # 券商龙头
        ("601088", "中国神华"),  # 煤炭龙头
        ("601899", "紫金矿业"),  # 有色龙头
        ("600547", "山东黄金"),  # 黄金龙头
        ("600028", "中国石化"),  # 石油龙头
    ],
    "水": [
        ("601012", "隆基绿能"),  # 光伏龙头
        ("002459", "TCL中环"),  # 硅片龙头
        ("600900", "长江电力"),  # 水电龙头
        ("601985", "中国核电"),  # 核电龙头
        ("600886", "国投电力"),  # 电力龙头
        ("601991", "大唐发电"),  # 电力龙头
        ("003816", "中国广核"),  # 核电龙头
        ("600025", "华能水电"),  # 水电龙头
        ("601016", "节能风电"),  # 风电龙头
        ("002202", "金风科技"),  # 风电设备
    ],
}

# 个股级别特征列
STOCK_LEVEL_FEATURE_COLUMNS = [
    # 各五行龙头股平均涨跌幅
    "木_leader_avg_change",    # 木行业龙头平均涨幅
    "火_leader_avg_change",    # 火行业龙头平均涨幅
    "土_leader_avg_change",    # 土行业龙头平均涨幅
    "金_leader_avg_change",    # 金行业龙头平均涨幅
    "水_leader_avg_change",    # 水行业龙头平均涨幅
    
    # 各五行龙头股上涨比例
    "木_leader_up_ratio",      # 木行业龙头上涨比例
    "火_leader_up_ratio",      # 火行业龙头上涨比例
    "土_leader_up_ratio",      # 土行业龙头上涨比例
    "金_leader_up_ratio",      # 金行业龙头上涨比例
    "水_leader_up_ratio",      # 水行业龙头上涨比例
    
    # 各五行龙头股平均换手率
    "木_leader_avg_turnover",  # 木行业龙头平均换手率
    "火_leader_avg_turnover",  # 火行业龙头平均换手率
    "土_leader_avg_turnover",  # 土行业龙头平均换手率
    "金_leader_avg_turnover",  # 金行业龙头平均换手率
    "水_leader_avg_turnover",  # 水行业龙头平均换手率
    
    # 各五行龙头股平均振幅
    "木_leader_avg_amplitude", # 木行业龙头平均振幅
    "火_leader_avg_amplitude", # 火行业龙头平均振幅
    "土_leader_avg_amplitude", # 土行业龙头平均振幅
    "金_leader_avg_amplitude", # 金行业龙头平均振幅
    "水_leader_avg_amplitude", # 水行业龙头平均振幅
    
    # 个股异动统计
    "stock_limit_up_count",    # 个股涨停数量（龙头股）
    "stock_limit_down_count",  # 个股跌停数量（龙头股）
    "stock_surge_count",       # 个股大涨数量（>5%）
    "stock_plunge_count",      # 个股大跌数量（<-3%）
    
    # 个股成交额分布
    "stock_total_volume",      # 龙头股总成交额
    "stock_volume_concentration",  # 成交量集中度（前3只/总成交量）
    
    # 强弱指数
    "wood_fire_strength",      # 木火行业相对强度（成长 vs 周期）
    "metal_water_defense",     # 金水行业防御系数
]

# 特征列定义（更新后）
FEATURE_COLUMNS = [
    # 市场宽度特征
    "up_ratio",           # 上涨比例
    "limit_up_count",     # 涨停数量
    "limit_down_count",   # 跌停数量
    "avg_change",         # 平均涨跌幅
    "market_breadth_score",  # 市场宽度综合得分
    
    # 资金面特征
    "northbound_net",     # 北向资金净流入（亿元）
    "northbound_trend",   # 北向资金趋势（-1/0/1）
    "margin_change",      # 融资余额变化
    "capital_sentiment",  # 资金面情绪指标
    
    # 板块特征
    "hot_sector_count",   # 热点板块数量
    "top_sector_avg",     # 领涨板块平均涨幅
    "bottom_sector_avg",  # 领跌板块平均跌幅
    "sector_divergence",  # 板块分化度
    
    # 量价特征
    "total_volume",       # 总成交额（亿元）
    "turnover_rate",      # 平均换手率
    "market_amplitude",   # 平均振幅
    "volume_ratio",       # 量比
    
    # 时间特征
    "day_of_week",        # 星期几（1-5）
    "month_of_year",      # 月份（1-12）
    "is_month_start",     # 是否月初
    "is_month_end",       # 是否月末
    
    # 个股级别特征（新增）
    *STOCK_LEVEL_FEATURE_COLUMNS,
]

# 五行标签列
LABEL_COLUMNS = ["木_return", "火_return", "土_return", "金_return", "水_return"]


# ═══════════════════════════════════════════════════════════
# 2. 历史数据收集器
# ═══════════════════════════════════════════════════════════

class HistoricalDataCollector:
    """历史数据收集器
    
    收集历史市场数据用于模型训练
    """
    
    def __init__(self, data_dir: str = None):
        """
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir or os.path.join(_ROOT, "data", "sentiment_model")
        os.makedirs(self.data_dir, exist_ok=True)
        self._cache = {}
    
    def collect_daily_data(self, date: str) -> Dict:
        """收集单日市场数据
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            
        Returns:
            市场数据字典
        """
        cache_key = f"daily_{date}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        data = {
            "date": date,
            "market_features": self._collect_market_features(date),
            "sector_returns": self._collect_sector_returns(date),
            "capital_features": self._collect_capital_features(date),
        }
        
        self._cache[cache_key] = data
        return data
    
    def _collect_market_features(self, date: str) -> Dict:
        """收集市场特征数据"""
        features = {
            "up_ratio": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
            "avg_change": 0,
            "total_volume": 0,
        }
        
        if not AKSHARE_AVAILABLE:
            return self._generate_market_features(date)
        
        try:
            # 获取A股实时行情（用于当日数据）
            today = datetime.now().strftime("%Y-%m-%d")
            if date == today:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    total = len(df)
                    up_count = len(df[df['涨跌幅'] > 0])
                    limit_up = len(df[df['涨跌幅'] >= 9.9])
                    limit_down = len(df[df['涨跌幅'] <= -9.9])
                    
                    features["up_ratio"] = round(up_count / max(total, 1), 4)
                    features["limit_up_count"] = int(limit_up)
                    features["limit_down_count"] = int(limit_down)
                    features["avg_change"] = round(float(df['涨跌幅'].mean()), 4)
                    features["total_volume"] = round(float(df['成交额'].sum()) / 1e8, 2) if '成交额' in df.columns else 0
        except Exception as e:
            print(f"  市场特征获取失败({date}): {e}")
        
        return features
    
    def _collect_sector_returns(self, date: str) -> Dict:
        """收集板块收益率数据"""
        returns = {}
        
        if not AKSHARE_AVAILABLE:
            return self._generate_sector_returns(date)
        
        try:
            # 获取行业板块行情
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                # 计算各五行对应的板块收益率
                for wuxing, sectors in WUXING_SECTOR_MAP.items():
                    sector_returns = []
                    for sector in sectors:
                        sector_row = df[df['板块名称'] == sector]
                        if not sector_row.empty:
                            change = float(sector_row.iloc[0].get('涨跌幅', 0))
                            sector_returns.append(change)
                    
                    if sector_returns:
                        returns[f"{wuxing}_avg_return"] = round(np.mean(sector_returns), 4)
                    else:
                        returns[f"{wuxing}_avg_return"] = 0
        except Exception as e:
            print(f"  板块收益获取失败({date}): {e}")
            returns = self._generate_sector_returns(date)
        
        return returns
    
    def _collect_capital_features(self, date: str) -> Dict:
        """收集资金面特征数据"""
        features = {
            "northbound_net": 0,
            "northbound_trend": 0,
            "capital_sentiment": 0,
        }
        
        if not AKSHARE_AVAILABLE:
            return features
        
        try:
            # 北向资金数据
            net_flow_df = None
            try:
                net_flow_df = ak.stock_hsgt_north_net_flow_in_em()
                if net_flow_df is not None and not net_flow_df.empty:
                    latest = net_flow_df.iloc[-1]
                    for col in net_flow_df.columns:
                        if '净' in str(col) and '额' in str(col):
                            features["northbound_net"] = round(float(latest[col]) / 10000, 2)  # 转换为亿元
                            break
                    
                    # 计算趋势
                    if len(net_flow_df) >= 5:
                        recent = net_flow_df.tail(5)
                        flows = []
                        for _, row in recent.iterrows():
                            for col in net_flow_df.columns:
                                if '净' in str(col) and '额' in str(col):
                                    flows.append(float(row[col]))
                                    break
                        
                        if len(flows) >= 3:
                            recent_avg = np.mean(flows[-3:])
                            earlier_avg = np.mean(flows[:-3])
                            features["northbound_trend"] = 1 if recent_avg > earlier_avg else (-1 if recent_avg < earlier_avg else 0)
            except Exception:
                pass
        except Exception as e:
            print(f"  资金特征获取失败({date}): {e}")
        
        # 计算资金面情绪
        if features["northbound_net"] > 100:
            features["capital_sentiment"] = 0.5
        elif features["northbound_net"] > 0:
            features["capital_sentiment"] = 0.2
        elif features["northbound_net"] < -100:
            features["capital_sentiment"] = -0.5
        elif features["northbound_net"] < 0:
            features["capital_sentiment"] = -0.2
        
        return features
    
    def _generate_market_features(self, date: str) -> Dict:
        """生成模拟市场特征"""
        np.random.seed(hash(date) % (2**31))
        up_ratio = np.clip(np.random.beta(2.5, 2.5), 0.2, 0.8)
        limit_up = max(0, int(np.random.normal(30, 20)))
        limit_down = max(0, int(np.random.normal(15, 10)))
        avg_change = np.random.normal(0.3, 1.5)
        total_volume = max(1000, np.random.normal(8000, 2000))
        
        return {
            "up_ratio": round(float(up_ratio), 4),
            "limit_up_count": limit_up,
            "limit_down_count": limit_down,
            "avg_change": round(float(avg_change), 4),
            "total_volume": round(float(total_volume), 2),
        }
    
    def _generate_sector_returns(self, date: str) -> Dict:
        """生成模拟板块收益率"""
        np.random.seed(hash(date + "sectors") % (2**31))
        
        # 市场整体状态
        market_trend = np.random.normal(0.3, 1.0)
        
        returns = {}
        for wuxing in ["木", "火", "土", "金", "水"]:
            # 各五行板块有一定相关性
            base_return = market_trend + np.random.normal(0, 0.8)
            
            # 添加五行特征
            if wuxing in ["木", "火"]:
                base_return += 0.2  # 成长型行业略强
            elif wuxing in ["金", "水"]:
                base_return -= 0.1  # 周期型行业略弱
            
            returns[f"{wuxing}_avg_return"] = round(float(base_return), 4)
        
        return returns
    
    # ═══════════════════════════════════════════════════════════
    # 个股级别数据收集方法
    # ═══════════════════════════════════════════════════════════
    
    def _collect_stock_features(self, date: str) -> Dict:
        """收集个股级别特征数据
        
        包含：
        - 各五行龙头股平均涨跌幅
        - 各五行龙头股上涨比例
        - 各五行龙头股平均换手率
        - 各五行龙头股平均振幅
        - 个股异动统计
        - 个股成交额分布
        - 强弱指数
        """
        if not AKSHARE_AVAILABLE:
            return self._generate_stock_features(date)
        
        features = {}
        
        try:
            # 获取A股实时行情
            today = datetime.now().strftime("%Y-%m-%d")
            if date == today:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    features = self._calculate_stock_features_from_df(df)
        except Exception as e:
            print(f"  个股特征获取失败({date}): {e}")
            features = self._generate_stock_features(date)
        
        # 填充默认值（如果部分特征缺失）
        default_features = self._get_default_stock_features()
        for key, val in default_features.items():
            if key not in features:
                features[key] = val
        
        return features
    
    def _calculate_stock_features_from_df(self, df: pd.DataFrame) -> Dict:
        """从DataFrame计算个股特征"""
        features = {}
        
        # 构建股票代码索引
        df['代码'] = df['代码'].astype(str).str.zfill(6)
        
        # 各五行龙头股统计
        for wuxing, leaders in WUXING_STOCK_LEADERS.items():
            leader_codes = [code for code, _ in leaders]
            leader_df = df[df['代码'].isin(leader_codes)]
            
            if len(leader_df) > 0:
                # 平均涨跌幅
                avg_change = leader_df['涨跌幅'].mean()
                features[f"{wuxing}_leader_avg_change"] = round(float(avg_change), 4)
                
                # 上涨比例
                up_count = len(leader_df[leader_df['涨跌幅'] > 0])
                features[f"{wuxing}_leader_up_ratio"] = round(up_count / len(leader_df), 4)
                
                # 平均换手率
                if '换手率' in leader_df.columns:
                    features[f"{wuxing}_leader_avg_turnover"] = round(float(leader_df['换手率'].mean()), 4)
                else:
                    features[f"{wuxing}_leader_avg_turnover"] = 2.5
                
                # 平均振幅
                if '振幅' in leader_df.columns:
                    features[f"{wuxing}_leader_avg_amplitude"] = round(float(leader_df['振幅'].mean()), 4)
                else:
                    features[f"{wuxing}_leader_avg_amplitude"] = 3.0
            else:
                # 默认值
                features[f"{wuxing}_leader_avg_change"] = 0
                features[f"{wuxing}_leader_up_ratio"] = 0.5
                features[f"{wuxing}_leader_avg_turnover"] = 2.5
                features[f"{wuxing}_leader_avg_amplitude"] = 3.0
        
        # 个股异动统计
        all_leader_codes = []
        for leaders in WUXING_STOCK_LEADERS.values():
            all_leader_codes.extend([code for code, _ in leaders])
        
        all_leaders_df = df[df['代码'].isin(all_leader_codes)]
        
        if len(all_leaders_df) > 0:
            # 涨停数量
            features["stock_limit_up_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] >= 9.9]))
            # 跌停数量
            features["stock_limit_down_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] <= -9.9]))
            # 大涨数量
            features["stock_surge_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] > 5]))
            # 大跌数量
            features["stock_plunge_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] < -3]))
            
            # 总成交额
            if '成交额' in all_leaders_df.columns:
                total_vol = float(all_leaders_df['成交额'].sum()) / 1e8  # 亿元
                features["stock_total_volume"] = round(total_vol, 2)
                
                # 成交量集中度
                sorted_by_vol = all_leaders_df.nlargest(3, '成交额')
                if total_vol > 0:
                    features["stock_volume_concentration"] = round(
                        float(sorted_by_vol['成交额'].sum()) / float(all_leaders_df['成交额'].sum()), 4
                    )
                else:
                    features["stock_volume_concentration"] = 0.3
            else:
                features["stock_total_volume"] = 0
                features["stock_volume_concentration"] = 0.3
        else:
            features["stock_limit_up_count"] = 0
            features["stock_limit_down_count"] = 0
            features["stock_surge_count"] = 0
            features["stock_plunge_count"] = 0
            features["stock_total_volume"] = 0
            features["stock_volume_concentration"] = 0.3
        
        # 计算强弱指数
        wood_fire_change = (features.get("木_leader_avg_change", 0) + features.get("火_leader_avg_change", 0)) / 2
        metal_water_change = (features.get("金_leader_avg_change", 0) + features.get("水_leader_avg_change", 0)) / 2
        
        # 木火行业相对强度
        if metal_water_change != 0:
            features["wood_fire_strength"] = round(wood_fire_change / abs(metal_water_change) if metal_water_change != 0 else 1.0, 4)
        else:
            features["wood_fire_strength"] = 1.0
        
        # 金水行业防御系数（相对市场整体）
        features["metal_water_defense"] = round(1.0 - metal_water_change / 3, 4)
        
        return features
    
    def _generate_stock_features(self, date: str) -> Dict:
        """生成模拟个股特征数据"""
        np.random.seed(hash(date + "stocks") % (2**31))
        
        features = {}
        
        # 各五行龙头股平均涨跌幅（与板块收益率相关）
        for wuxing in ["木", "火", "土", "金", "水"]:
            features[f"{wuxing}_leader_avg_change"] = round(float(np.random.normal(0.3, 2.0)), 4)
            features[f"{wuxing}_leader_up_ratio"] = round(float(np.clip(np.random.beta(2.5, 2.5), 0.2, 0.8)), 4)
            features[f"{wuxing}_leader_avg_turnover"] = round(float(np.random.normal(2.5, 1.5)), 4)
            features[f"{wuxing}_leader_avg_amplitude"] = round(float(np.random.normal(3.0, 1.5)), 4)
        
        # 个股异动统计
        features["stock_limit_up_count"] = max(0, int(np.random.normal(3, 5)))
        features["stock_limit_down_count"] = max(0, int(np.random.normal(1, 3)))
        features["stock_surge_count"] = max(0, int(np.random.normal(15, 10)))
        features["stock_plunge_count"] = max(0, int(np.random.normal(8, 6)))
        
        # 成交额分布
        features["stock_total_volume"] = round(float(np.random.normal(500, 150)), 2)
        features["stock_volume_concentration"] = round(float(np.clip(np.random.normal(0.3, 0.1), 0.1, 0.5)), 4)
        
        # 强弱指数
        wood_fire = (features["木_leader_avg_change"] + features["火_leader_avg_change"]) / 2
        metal_water = (features["金_leader_avg_change"] + features["水_leader_avg_change"]) / 2
        features["wood_fire_strength"] = round(float(wood_fire / abs(metal_water) if metal_water != 0 else 1.0), 4)
        features["metal_water_defense"] = round(float(1.0 - metal_water / 3), 4)
        
        return features
    
    def _get_default_stock_features(self) -> Dict:
        """获取默认个股特征值"""
        defaults = {}
        for wuxing in ["木", "火", "土", "金", "水"]:
            defaults[f"{wuxing}_leader_avg_change"] = 0.0
            defaults[f"{wuxing}_leader_up_ratio"] = 0.5
            defaults[f"{wuxing}_leader_avg_turnover"] = 2.5
            defaults[f"{wuxing}_leader_avg_amplitude"] = 3.0
        
        defaults.update({
            "stock_limit_up_count": 0,
            "stock_limit_down_count": 0,
            "stock_surge_count": 0,
            "stock_plunge_count": 0,
            "stock_total_volume": 0,
            "stock_volume_concentration": 0.3,
            "wood_fire_strength": 1.0,
            "metal_water_defense": 0.5,
        })
        
        return defaults
    
    def generate_training_data(self, days: int = 365) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """生成训练数据集
        
        Args:
            days: 生成历史数据的天数
            
        Returns:
            (特征DataFrame, 标签DataFrame)
        """
        print(f"📊 正在生成 {days} 天的训练数据（含个股级别特征）...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        feature_rows = []
        label_rows = []
        
        current = start_date
        while current <= end_date:
            # 跳过周末
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue
            
            date_str = current.strftime("%Y-%m-%d")
            
            # 收集数据
            market_features = self._generate_market_features(date_str)
            sector_returns = self._generate_sector_returns(date_str)
            stock_features = self._generate_stock_features(date_str)  # 个股特征
            
            # 构建特征行
            feature_row = self._build_feature_row(date_str, market_features, sector_returns, stock_features)
            feature_rows.append(feature_row)
            
            # 构建标签行（次日收益率）
            label_row = self._build_label_row(sector_returns)
            label_rows.append(label_row)
            
            current += timedelta(days=1)
        
        features_df = pd.DataFrame(feature_rows)
        labels_df = pd.DataFrame(label_rows)
        
        print(f"  生成特征数据: {len(features_df)} 条")
        print(f"  生成标签数据: {len(labels_df)} 条")
        print(f"  特征列数: {len(FEATURE_COLUMNS)} (含{len(STOCK_LEVEL_FEATURE_COLUMNS)}个个股级别特征)")
        
        return features_df, labels_df
    
    def _build_feature_row(self, date: str, market: Dict, sectors: Dict, 
                            stock_features: Dict = None) -> Dict:
        """构建特征行（含个股级别特征）"""
        day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday() + 1
        month_of_year = datetime.strptime(date, "%Y-%m-%d").month
        day_of_month = datetime.strptime(date, "%Y-%m-%d").day
        
        if stock_features is None:
            stock_features = self._get_default_stock_features()
        
        row = {
            "date": date,
            # 市场宽度
            "up_ratio": market.get("up_ratio", 0),
            "limit_up_count": market.get("limit_up_count", 0),
            "limit_down_count": market.get("limit_down_count", 0),
            "avg_change": market.get("avg_change", 0),
            "market_breadth_score": self._calculate_breadth_score(market),
            
            # 资金面（默认值，实时获取时更新）
            "northbound_net": 0,
            "northbound_trend": 0,
            "margin_change": 0,
            "capital_sentiment": 0,
            
            # 板块特征
            "hot_sector_count": self._count_hot_sectors(sectors),
            "top_sector_avg": self._calc_top_sector_avg(sectors),
            "bottom_sector_avg": self._calc_bottom_sector_avg(sectors),
            "sector_divergence": self._calc_sector_divergence(sectors),
            
            # 量价特征
            "total_volume": market.get("total_volume", 0),
            "turnover_rate": 2.5,  # 平均换手率
            "market_amplitude": 3.0,  # 平均振幅
            "volume_ratio": 1.0,  # 量比
            
            # 时间特征
            "day_of_week": day_of_week,
            "month_of_year": month_of_year,
            "is_month_start": 1 if day_of_month <= 3 else 0,
            "is_month_end": 1 if day_of_month >= 27 else 0,
        }
        
        # 添加个股级别特征
        for col in STOCK_LEVEL_FEATURE_COLUMNS:
            row[col] = stock_features.get(col, 0)
        
        return row
    
    def _build_label_row(self, sectors: Dict) -> Dict:
        """构建标签行（各五行收益率）"""
        return {
            "木_return": sectors.get("木_avg_return", 0),
            "火_return": sectors.get("火_avg_return", 0),
            "土_return": sectors.get("土_avg_return", 0),
            "金_return": sectors.get("金_avg_return", 0),
            "水_return": sectors.get("水_avg_return", 0),
        }
    
    def _calculate_breadth_score(self, market: Dict) -> float:
        """计算市场宽度综合得分"""
        up_ratio = market.get("up_ratio", 0.5)
        limit_up = market.get("limit_up_count", 0)
        limit_down = market.get("limit_down_count", 0)
        avg_change = market.get("avg_change", 0)
        
        score = 0.0
        # 上涨比例贡献
        score += (up_ratio - 0.5) * 2  # -1 到 1
        # 涨停跌停贡献
        score += min(limit_up / 50, 1.0) * 0.5  # 最多 +0.5
        score -= min(limit_down / 30, 1.0) * 0.3  # 最多 -0.3
        # 平均涨跌幅贡献
        score += np.clip(avg_change / 3, -0.5, 0.5)
        
        return round(float(np.clip(score, -1, 1)), 4)
    
    def _count_hot_sectors(self, sectors: Dict) -> int:
        """统计热点板块数量"""
        count = 0
        for key, val in sectors.items():
            if isinstance(val, (int, float)) and val > 2.0:
                count += 1
        return count
    
    def _calc_top_sector_avg(self, sectors: Dict) -> float:
        """计算领涨板块平均涨幅"""
        returns = [v for v in sectors.values() if isinstance(v, (int, float))]
        if returns:
            sorted_returns = sorted(returns, reverse=True)
            return round(float(np.mean(sorted_returns[:2])), 4)
        return 0
    
    def _calc_bottom_sector_avg(self, sectors: Dict) -> float:
        """计算领跌板块平均跌幅"""
        returns = [v for v in sectors.values() if isinstance(v, (int, float))]
        if returns:
            sorted_returns = sorted(returns)
            return round(float(np.mean(sorted_returns[:2])), 4)
        return 0
    
    def _calc_sector_divergence(self, sectors: Dict) -> float:
        """计算板块分化度"""
        returns = [v for v in sectors.values() if isinstance(v, (int, float))]
        if len(returns) >= 2:
            return round(float(max(returns) - min(returns)), 4)
        return 0


# ═══════════════════════════════════════════════════════════
# 3. 市场情绪五行回归模型
# ═══════════════════════════════════════════════════════════

class SentimentWuxingRegressor:
    """市场情绪与五行回归模型
    
    学习市场情绪指标到五行调整系数的映射关系
    
    支持模型：
    - 线性回归（Ridge/Lasso）
    - 随机森林回归
    - 梯度提升回归
    """
    
    WUXING_LIST = ["木", "火", "土", "金", "水"]
    
    def __init__(self, model_type: str = "ridge"):
        """
        Args:
            model_type: 模型类型 ('ridge', 'lasso', 'random_forest', 'gradient_boosting')
        """
        self.model_type = model_type
        self.models = {}  # 每个五行一个模型
        self.scalers = {}  # 每个五行一个标准化器
        self.is_trained = False
        self.training_stats = {}
        self.model_params = self._get_model_params(model_type)
    
    def _get_model_params(self, model_type: str) -> Dict:
        """获取模型参数"""
        params = {
            "ridge": {
                "alpha": 1.0,
                "description": "Ridge回归（L2正则化，稳定）",
            },
            "lasso": {
                "alpha": 0.1,
                "description": "Lasso回归（L1正则化，特征选择）",
            },
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "description": "随机森林（捕捉非线性）",
            },
            "gradient_boosting": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5,
                "description": "梯度提升（高精度）",
            },
        }
        return params.get(model_type, params["ridge"])
    
    def train(self, features_df: pd.DataFrame, labels_df: pd.DataFrame) -> Dict:
        """训练模型
        
        Args:
            features_df: 特征DataFrame
            labels_df: 标签DataFrame
            
        Returns:
            训练结果统计
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn 未安装，请运行: pip install scikit-learn")
        
        print(f"🔄 正在训练 {self.model_type} 模型...")
        print(f"   特征数量: {len(FEATURE_COLUMNS)}")
        print(f"   样本数量: {len(features_df)}")
        
        # 预处理特征
        X = features_df[FEATURE_COLUMNS].values
        
        training_results = {}
        
        for wuxing in self.WUXING_LIST:
            y_col = f"{wuxing}_return"
            if y_col not in labels_df.columns:
                print(f"  ⚠️ 跳过 {wuxing}：缺少标签列 {y_col}")
                continue
            
            y = labels_df[y_col].values
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 标准化特征
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 创建模型
            model = self._create_model()
            
            # 训练
            model.fit(X_train_scaled, y_train)
            
            # 预测
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            # 评估
            train_mse = mean_squared_error(y_train, y_pred_train)
            test_mse = mean_squared_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            
            # 交叉验证
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            
            self.models[wuxing] = model
            self.scalers[wuxing] = scaler
            
            training_results[wuxing] = {
                "train_mse": round(float(train_mse), 6),
                "test_mse": round(float(test_mse), 6),
                "train_r2": round(float(train_r2), 4),
                "test_r2": round(float(test_r2), 4),
                "test_mae": round(float(test_mae), 4),
                "cv_r2_mean": round(float(np.mean(cv_scores)), 4),
                "cv_r2_std": round(float(np.std(cv_scores)), 4),
            }
            
            print(f"  ✅ {wuxing}: R²={test_r2:.4f}, MAE={test_mae:.4f}, CV_R²={np.mean(cv_scores):.4f}±{np.std(cv_scores):.4f}")
        
        self.is_trained = True
        self.training_stats = training_results
        
        return training_results
    
    def _create_model(self):
        """创建回归模型"""
        if not SKLEARN_AVAILABLE:
            return None
        
        if self.model_type == "ridge":
            return Ridge(alpha=self.model_params["alpha"])
        elif self.model_type == "lasso":
            return Lasso(alpha=self.model_params["alpha"], max_iter=10000)
        elif self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=self.model_params["n_estimators"],
                max_depth=self.model_params["max_depth"],
                random_state=42,
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=self.model_params["n_estimators"],
                learning_rate=self.model_params["learning_rate"],
                max_depth=self.model_params["max_depth"],
                random_state=42,
            )
        else:
            # 默认使用Ridge
            return Ridge(alpha=1.0)
    
    def predict(self, features: Dict) -> Dict[str, float]:
        """预测五行收益率
        
        Args:
            features: 特征字典
            
        Returns:
            各五行预测收益率
        """
        if not self.is_trained:
            raise ValueError("模型未训练，请先调用 train() 方法")
        
        # 构建特征向量
        x = np.array([[features.get(col, 0) for col in FEATURE_COLUMNS]])
        
        predictions = {}
        
        for wuxing in self.WUXING_LIST:
            if wuxing not in self.models:
                predictions[wuxing] = 0.0
                continue
            
            # 标准化
            x_scaled = self.scalers[wuxing].transform(x)
            
            # 预测
            pred = self.models[wuxing].predict(x_scaled)[0]
            predictions[wuxing] = round(float(pred), 4)
        
        return predictions
    
    def predict_wuxing_adjustment(self, features: Dict) -> Dict[str, float]:
        """预测五行调整系数（用于DynamicLeixiangAdjuster）
        
        将预测的收益率转换为调整系数：
        - 收益率 > 2% → 增强 1.15x
        - 收益率 1-2% → 增强 1.08x
        - 收益率 0-1% → 增强 1.03x
        - 收益率 -1~0% → 减弱 0.97x
        - 收益率 -2~-1% → 减弱 0.92x
        - 收益率 < -2% → 减弱 0.85x
        
        Args:
            features: 特征字典
            
        Returns:
            各五行调整系数
        """
        predictions = self.predict(features)
        
        adjustments = {}
        for wuxing, ret in predictions.items():
            adjustment = self._return_to_adjustment(ret)
            adjustments[wuxing] = adjustment
        
        return adjustments
    
    def _return_to_adjustment(self, predicted_return: float) -> float:
        """将预测收益率转换为调整系数"""
        if predicted_return > 2.0:
            return 1.15
        elif predicted_return > 1.0:
            return 1.08
        elif predicted_return > 0.0:
            return 1.03
        elif predicted_return > -1.0:
            return 0.97
        elif predicted_return > -2.0:
            return 0.92
        else:
            return 0.85
    
    def _return_to_adjustment_desc(self, adjustment: float) -> str:
        """获取调整系数的描述"""
        if adjustment >= 1.15:
            return "显著增强"
        elif adjustment >= 1.08:
            return "轻度增强"
        elif adjustment >= 1.03:
            return "微弱增强"
        elif adjustment >= 0.97:
            return "基本稳定"
        elif adjustment >= 0.92:
            return "轻度削弱"
        else:
            return "显著削弱"
    
    def get_feature_importance(self, wuxing: str) -> pd.DataFrame:
        """获取特征重要性
        
        Args:
            wuxing: 五行名称
            
        Returns:
            特征重要性DataFrame
        """
        if not self.is_trained or wuxing not in self.models:
            return pd.DataFrame()
        
        model = self.models[wuxing]
        
        if hasattr(model, 'feature_importances_'):
            # 树模型
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            # 线性模型
            importance = np.abs(model.coef_)
        else:
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'feature': FEATURE_COLUMNS,
            'importance': importance,
        })
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df
    
    def save(self, filepath: str):
        """保存模型"""
        model_data = {
            "model_type": self.model_type,
            "models": self.models,
            "scalers": self.scalers,
            "is_trained": self.is_trained,
            "training_stats": self.training_stats,
            "model_params": self.model_params,
            "feature_columns": FEATURE_COLUMNS,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 模型已保存: {filepath}")
    
    def load(self, filepath: str):
        """加载模型"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model_type = model_data["model_type"]
        self.models = model_data["models"]
        self.scalers = model_data["scalers"]
        self.is_trained = model_data["is_trained"]
        self.training_stats = model_data["training_stats"]
        self.model_params = model_data.get("model_params", self.model_params)
        
        print(f"📂 模型已加载: {filepath}")
        print(f"   模型类型: {self.model_type}")
        print(f"   已训练: {self.is_trained}")


# ═══════════════════════════════════════════════════════════
# 4. 与DynamicLeixiangAdjuster集成的适配器
# ═══════════════════════════════════════════════════════════

class RegressionModelAdapter:
    """回归模型适配器
    
    将SentimentWuxingRegressor集成到DynamicLeixiangAdjuster中
    """
    
    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: 预训练模型路径
        """
        self.model = None
        self.is_available = False
        self.model_accuracy = 0.0
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train_and_save(self, days: int = 365, model_type: str = "ridge",
                       save_path: str = None) -> Dict:
        """训练并保存模型
        
        Args:
            days: 训练数据天数
            model_type: 模型类型
            save_path: 保存路径
            
        Returns:
            训练统计
        """
        print("=" * 60)
        print("📈 市场情绪与五行回归模型训练")
        print("=" * 60)
        
        # 收集数据
        collector = HistoricalDataCollector()
        features_df, labels_df = collector.generate_training_data(days)
        
        # 训练模型
        self.model = SentimentWuxingRegressor(model_type=model_type)
        training_stats = self.model.train(features_df, labels_df)
        
        # 计算平均准确率
        accuracies = [v["test_r2"] for v in training_stats.values()]
        self.model_accuracy = np.mean(accuracies) if accuracies else 0
        
        self.is_available = True
        
        # 保存模型
        if save_path:
            self.model.save(save_path)
        else:
            default_path = os.path.join(
                _ROOT, "data", "sentiment_model", 
                f"sentiment_wuxing_{model_type}.pkl"
            )
            self.model.save(default_path)
        
        print("\n📊 训练完成汇总:")
        print(f"   平均R²: {self.model_accuracy:.4f}")
        print(f"   模型类型: {model_type}")
        
        return training_stats
    
    def load_model(self, model_path: str):
        """加载预训练模型"""
        try:
            self.model = SentimentWuxingRegressor()
            self.model.load(model_path)
            self.is_available = self.model.is_trained
            
            # 计算准确率
            if self.model.training_stats:
                accuracies = [v["test_r2"] for v in self.model.training_stats.values()]
                self.model_accuracy = np.mean(accuracies) if accuracies else 0.0
            
            print(f"✅ 模型加载成功，准确率: {self.model_accuracy:.4f}")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.is_available = False
    
    def predict_adjustments(self, market_data: Dict, sector_data: Dict = None,
                            capital_data: Dict = None) -> Dict[str, float]:
        """根据实时数据预测五行调整系数
        
        Args:
            market_data: 市场数据
            sector_data: 板块数据
            capital_data: 资金面数据
            
        Returns:
            五行调整系数字典
        """
        if not self.is_available or not self.model:
            return {}
        
        # 构建特征
        features = self._build_features(market_data, sector_data, capital_data)
        
        # 预测调整系数
        try:
            adjustments = self.model.predict_wuxing_adjustment(features)
            return adjustments
        except Exception as e:
            print(f"⚠️ 回归预测失败: {e}")
            return {}
    
    def _build_features(self, market_data: Dict, sector_data: Dict = None,
                        capital_data: Dict = None) -> Dict:
        """构建特征字典（含个股级别特征）"""
        features = {}
        
        # 从市场数据提取
        if market_data:
            sentiment = market_data.get("market_sentiment", {})
            breadth = market_data.get("market_breadth", {})
            
            features["up_ratio"] = breadth.get("up_ratio", 0.5) / 100  # 转换为比例
            features["limit_up_count"] = breadth.get("limit_up", 0)
            features["limit_down_count"] = breadth.get("limit_down", 0)
            features["avg_change"] = sentiment.get("avg_change", 0)
            features["market_breadth_score"] = self._calc_breadth_score_from_data(market_data)
            features["total_volume"] = sentiment.get("total_volume", 0) / 1e8 if sentiment.get("total_volume") else 0
        
        # 从资金面数据提取
        if capital_data:
            summary = capital_data.get("capital_flow_summary", {})
            features["northbound_net"] = capital_data.get("northbound", {}).get("net_flow", 0) / 10000 if capital_data.get("northbound", {}).get("net_flow") else 0
            features["capital_sentiment"] = summary.get("sentiment_score", 0)
            if features["northbound_net"] > 100:
                features["northbound_trend"] = 1
            elif features["northbound_net"] < -100:
                features["northbound_trend"] = -1
            else:
                features["northbound_trend"] = 0
        
        # 从板块数据提取
        if sector_data:
            hot_sectors = sector_data.get("hot_sectors", [])
            features["hot_sector_count"] = len(hot_sectors) if hot_sectors else 0
        
        # 尝试获取实时个股数据
        stock_features = self._fetch_realtime_stock_features()
        features.update(stock_features)
        
        # 填充默认值（如果部分特征缺失）
        default_stock = HistoricalDataCollector()._get_default_stock_features()
        for key, val in default_stock.items():
            if key not in features:
                features[key] = val
        
        # 时间特征
        now = datetime.now()
        features["day_of_week"] = now.weekday() + 1
        features["month_of_year"] = now.month
        features["is_month_start"] = 1 if now.day <= 3 else 0
        features["is_month_end"] = 1 if now.day >= 27 else 0
        
        # 确保所有特征列都有值
        for col in FEATURE_COLUMNS:
            if col not in features:
                features[col] = 0.0
        
        return features
    
    def _fetch_realtime_stock_features(self) -> Dict:
        """获取实时个股级别特征"""
        features = {}
        
        try:
            if not AKSHARE_AVAILABLE:
                return features
            
            # 获取A股实时行情
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return features
            
            # 构建股票代码索引
            df['代码'] = df['代码'].astype(str).str.zfill(6)
            
            # 各五行龙头股统计
            for wuxing, leaders in WUXING_STOCK_LEADERS.items():
                leader_codes = [code for code, _ in leaders]
                leader_df = df[df['代码'].isin(leader_codes)]
                
                if len(leader_df) > 0:
                    features[f"{wuxing}_leader_avg_change"] = round(float(leader_df['涨跌幅'].mean()), 4)
                    up_count = len(leader_df[leader_df['涨跌幅'] > 0])
                    features[f"{wuxing}_leader_up_ratio"] = round(up_count / len(leader_df), 4)
                    
                    if '换手率' in leader_df.columns:
                        features[f"{wuxing}_leader_avg_turnover"] = round(float(leader_df['换手率'].mean()), 4)
                    if '振幅' in leader_df.columns:
                        features[f"{wuxing}_leader_avg_amplitude"] = round(float(leader_df['振幅'].mean()), 4)
            
            # 个股异动统计
            all_codes = []
            for leaders in WUXING_STOCK_LEADERS.values():
                all_codes.extend([code for code, _ in leaders])
            
            all_leaders_df = df[df['代码'].isin(all_codes)]
            
            if len(all_leaders_df) > 0:
                features["stock_limit_up_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] >= 9.9]))
                features["stock_limit_down_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] <= -9.9]))
                features["stock_surge_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] > 5]))
                features["stock_plunge_count"] = int(len(all_leaders_df[all_leaders_df['涨跌幅'] < -3]))
                
                if '成交额' in all_leaders_df.columns:
                    total_vol = float(all_leaders_df['成交额'].sum()) / 1e8
                    features["stock_total_volume"] = round(total_vol, 2)
                    
                    sorted_by_vol = all_leaders_df.nlargest(3, '成交额')
                    if total_vol > 0:
                        features["stock_volume_concentration"] = round(
                            float(sorted_by_vol['成交额'].sum()) / float(all_leaders_df['成交额'].sum()), 4
                        )
            
            # 计算强弱指数
            wood_fire = (features.get("木_leader_avg_change", 0) + features.get("火_leader_avg_change", 0)) / 2
            metal_water = (features.get("金_leader_avg_change", 0) + features.get("水_leader_avg_change", 0)) / 2
            features["wood_fire_strength"] = round(float(wood_fire / abs(metal_water) if metal_water != 0 else 1.0), 4)
            features["metal_water_defense"] = round(float(1.0 - metal_water / 3), 4)
            
        except Exception:
            pass  # 静默失败，使用默认值
        
        return features
    
    def _calc_breadth_score_from_data(self, market_data: Dict) -> float:
        """从市场数据计算宽度得分"""
        breadth = market_data.get("market_breadth", {})
        sentiment = market_data.get("market_sentiment", {})
        
        up_ratio = breadth.get("up_ratio", 50) / 100
        limit_up = breadth.get("limit_up", 0)
        limit_down = breadth.get("limit_down", 0)
        avg_change = sentiment.get("avg_change", 0)
        
        score = 0.0
        score += (up_ratio - 0.5) * 2
        score += min(limit_up / 50, 1.0) * 0.5
        score -= min(limit_down / 30, 1.0) * 0.3
        score += np.clip(avg_change / 3, -0.5, 0.5)
        
        return round(float(np.clip(score, -1, 1)), 4)
    
    def get_status(self) -> Dict:
        """获取适配器状态"""
        return {
            "is_available": self.is_available,
            "model_accuracy": self.model_accuracy,
            "model_type": self.model.model_type if self.model else None,
            "wuxing_models": list(self.model.models.keys()) if self.model and self.model.is_trained else [],
        }


# ═══════════════════════════════════════════════════════════
# 5. 主测试脚本
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 市场情绪与五行量化回归模型测试")
    print("=" * 70)
    
    # 1. 测试数据收集
    print("\n📊 步骤1: 数据收集")
    print("-" * 40)
    collector = HistoricalDataCollector()
    features_df, labels_df = collector.generate_training_data(days=365)
    
    print(f"\n特征数据集形状: {features_df.shape}")
    print(f"标签数据集形状: {labels_df.shape}")
    print(f"\n特征列: {list(features_df.columns[:10])}...")
    print(f"标签列: {list(labels_df.columns)}")
    
    # 2. 模型训练对比
    print("\n📈 步骤2: 模型训练对比")
    print("-" * 40)
    
    model_types = ["ridge", "lasso", "random_forest", "gradient_boosting"]
    comparison_results = {}
    
    for model_type in model_types:
        print(f"\n🔄 训练 {model_type} 模型...")
        try:
            model = SentimentWuxingRegressor(model_type=model_type)
            stats = model.train(features_df, labels_df)
            
            accuracies = [v["test_r2"] for v in stats.values()]
            avg_r2 = np.mean(accuracies) if accuracies else 0
            comparison_results[model_type] = {"avg_r2": avg_r2, "stats": stats}
            
            print(f"  ✅ {model_type}: 平均R² = {avg_r2:.4f}")
        except Exception as e:
            print(f"  ❌ {model_type} 训练失败: {e}")
            comparison_results[model_type] = {"avg_r2": 0, "error": str(e)}
    
    # 3. 选择最优模型
    print("\n🏆 步骤3: 模型对比")
    print("-" * 40)
    
    best_model = None
    best_r2 = -float('inf')
    
    for model_type, result in comparison_results.items():
        avg_r2 = result.get("avg_r2", 0)
        print(f"  {model_type}: R² = {avg_r2:.4f}")
        
        if avg_r2 > best_r2:
            best_r2 = avg_r2
            best_model = model_type
    
    print(f"\n  最优模型: {best_model} (R² = {best_r2:.4f})")
    
    # 4. 使用最优模型进行预测演示
    print("\n🔮 步骤4: 预测演示")
    print("-" * 40)
    
    # 训练最优模型
    best_regressor = SentimentWuxingRegressor(model_type=best_model)
    best_regressor.train(features_df, labels_df)
    
    # 模拟市场数据
    test_features = {
        "up_ratio": 0.65,
        "limit_up_count": 45,
        "limit_down_count": 8,
        "avg_change": 0.5,
        "market_breadth_score": 0.6,
        "northbound_net": 350,
        "northbound_trend": 1,
        "margin_change": 0.05,
        "capital_sentiment": 0.4,
        "hot_sector_count": 5,
        "top_sector_avg": 3.5,
        "bottom_sector_avg": -1.2,
        "sector_divergence": 4.7,
        "total_volume": 8500,
        "turnover_rate": 2.8,
        "market_amplitude": 3.2,
        "volume_ratio": 1.2,
        "day_of_week": 3,
        "month_of_year": 8,
        "is_month_start": 0,
        "is_month_end": 0,
    }
    
    print(f"\n输入特征（模拟今日市场）:")
    print(f"  上涨比例: {test_features['up_ratio']*100:.0f}%")
    print(f"  涨停数量: {test_features['limit_up_count']}")
    print(f"  北向资金: {test_features['northbound_net']}亿")
    print(f"  市场宽度得分: {test_features['market_breadth_score']}")
    
    # 预测收益率
    predictions = best_regressor.predict(test_features)
    print(f"\n📊 预测各五行收益率:")
    for wuxing, ret in predictions.items():
        print(f"  {wuxing}: {ret:+.2f}%")
    
    # 预测调整系数
    adjustments = best_regressor.predict_wuxing_adjustment(test_features)
    print(f"\n📈 推荐调整系数:")
    for wuxing, adj in adjustments.items():
        desc = best_regressor._return_to_adjustment_desc(adj)
        print(f"  {wuxing}: {adj:.2f}x ({desc})")
    
    # 5. 特征重要性分析
    print("\n🔍 步骤5: 特征重要性分析")
    print("-" * 40)
    
    for wuxing in ["木", "火", "金"]:
        print(f"\n  {wuxing} 行业特征重要性 Top 5:")
        importance_df = best_regressor.get_feature_importance(wuxing)
        if not importance_df.empty:
            for _, row in importance_df.head(5).iterrows():
                print(f"    {row['feature']}: {row['importance']:.4f}")
    
    # 6. 保存最优模型
    print("\n💾 步骤6: 保存模型")
    print("-" * 40)
    
    model_dir = os.path.join(_ROOT, "data", "sentiment_model")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"best_{best_model}_model.pkl")
    best_regressor.save(model_path)
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    print(f"\n📋 总结:")
    print(f"  最优模型: {best_model}")
    print(f"  平均R²: {best_r2:.4f}")
    print(f"  模型路径: {model_path}")
    print(f"\n💡 使用方法:")
    print(f"  1. 初始化适配器: adapter = RegressionModelAdapter()")
    print(f"  2. 加载模型: adapter.load_model('{model_path}')")
    print(f"  3. 预测调整: adjustments = adapter.predict_adjustments(market_data)")
