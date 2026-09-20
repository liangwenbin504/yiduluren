#!/usr/bin/env python3
"""
量化选股器 v1.0 — 多因子打分 + 六壬交叉验证
===========================================
四维筛选:
  A. 技术面 — 动量/量价/形态 (同花顺排名API)
  B. 资金面 — 主力净流入/北向 (东方财富)
  C. 估值面 — PE/PB分位 (AKShare)
  D. 六壬面 — 个股课盘吉凶 (一课多断)

输出: TOP 10 选股列表 + 综合评分 + 买卖建议

用法:
  python stock_screener.py            # 全市场扫描
  python stock_screener.py --top 20   # TOP 20
  python stock_screener.py --sector 白酒  # 板块选股
"""

import json, os, sys, io, time
import numpy as np; import pandas as pd
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE, '_memory')

# 全局配置：六壬是否仅作参考（不参与决策）
try:
    from config import LIUREN_REFERENCE_ONLY
except Exception:
    LIUREN_REFERENCE_ONLY = True  # 默认安全：参考模式


class QuantScreener:
    """多因子量化选股器"""

    def __init__(self):
        self.results = []
        self.scores = defaultdict(float)
        self.src_status = {}  # 各维度数据源可用性报告

    # ═══ A. 技术面 ═══

    def scan_momentum(self) -> dict:
        """扫描持续新高/连涨/强度排名"""
        scores = defaultdict(float)
        try:
            import akshare as ak
            # 连续上涨
            lxsz = ak.stock_rank_lxsz_ths()
            for _, row in lxsz.head(20).iterrows():
                code = str(row.get('股票代码', ''))
                days = row.get('连涨天数', 0)
                scores[code] += min(float(days) * 2, 20)

            # 持续新高
            cxd = ak.stock_rank_cxd_ths()
            for _, row in cxd.head(10).iterrows():
                code = str(row.get('股票代码', ''))
                scores[code] += 15

            # 向上突破
            xstp = ak.stock_rank_xstp_ths()
            for _, row in xstp.head(10).iterrows():
                code = str(row.get('股票代码', ''))
                scores[code] += 12

            # 创新高
            cxg = ak.stock_rank_cxg_ths()
            for _, row in cxg.head(10).iterrows():
                code = str(row.get('股票代码', ''))
                scores[code] += 18

            print(f"  技术面扫描完成: {len(scores)} 只候选")
            self.src_status['技术面'] = '✅ 同花顺排名(正常)'
        except Exception as e:
            print(f"  ⚠️ 技术面扫描异常: {e}")
            self.src_status['技术面'] = '⚠️ 跳过(同花顺不可用)'
        return scores

    # ═══ A2. 趋势质量 ═══

    def scan_trend_quality(self, stock_codes: list = None) -> dict:
        """
        趋势质量因子（聚宽v2版核心因子）
        - 均线多头排列
        - MA20斜率（向上/向下）
        - 偏离MA20的距离（避免追高，温和上涨最优）
        只对候选TOP50计算，减少API调用
        """
        scores = defaultdict(float)
        try:
            import akshare as ak
            
            if stock_codes is None or len(stock_codes) == 0:
                # 如果没给候选，先不计算（等初选后再精算）
                return scores
            
            print(f"  趋势质量计算中（{len(stock_codes)}只）...")
            
            for code in stock_codes[:50]:  # 最多算50只
                try:
                    # 获取60天日线（腾讯源替代东方财富 stock_zh_a_hist）
                    from tencent_market import tencent_hist
                    closes = np.array(tencent_hist(code, days=60), dtype=float)
                    if len(closes) < 40:
                        continue
                    
                    # 均线计算
                    ma5 = closes[-5:].mean()
                    ma10 = closes[-10:].mean()
                    ma20 = closes[-20:].mean()
                    current = closes[-1]
                    
                    score = 0.0
                    
                    # 1. 均线多头排列（权重最大）
                    if current > ma5 > ma10 > ma20:
                        score += 15
                    elif current > ma10 > ma20:
                        score += 10
                    elif current > ma20:
                        score += 5
                    else:
                        score -= 5  # 在MA20下方，减分
                    
                    # 2. MA20斜率（向上加分，向下减分）
                    if len(closes) >= 40:
                        ma20_now = closes[-20:].mean()
                        ma20_prev = closes[-40:-20].mean()
                        if ma20_prev > 0:
                            slope = (ma20_now / ma20_prev - 1) * 100
                            if slope > 2:
                                score += 8
                            elif slope > 0.5:
                                score += 4
                            elif slope < -2:
                                score -= 8
                            elif slope < -0.5:
                                score -= 4
                    
                    # 3. 偏离MA20的距离（温和上涨最优，涨太多减分）
                    if ma20 > 0:
                        deviation = (current / ma20 - 1) * 100
                        if 2 <= deviation <= 10:
                            score += 5  # 温和上涨，最佳区间
                        elif deviation > 20:
                            score -= 8  # 涨太多了，追高风险大
                        elif deviation > 15:
                            score -= 4
                    
                    scores[code] = max(score, -10)
                    
                except Exception:
                    continue
            
            print(f"  趋势质量计算完成: {len(scores)} 只")
            self.src_status['趋势质量'] = '✅ 腾讯日K线'
        except Exception as e:
            print(f"  ⚠️ 趋势质量计算异常: {e}")
            self.src_status['趋势质量'] = '⚠️ 跳过(腾讯K线不可用)'
        return scores

    # ═══ B. 资金面 ═══

    def scan_capital_flow(self) -> dict:
        """扫描资金流向"""
        scores = defaultdict(float)
        try:
            import akshare as ak
            flow = ak.stock_individual_fund_flow_rank()
            if flow is not None and len(flow) > 0:
                for _, row in flow.head(30).iterrows():
                    code = str(row.get('代码', ''))
                    if code:
                        net = float(row.get('主力净流入', 0)) / 1e8  # 亿
                        if net > 0:
                            scores[code] += min(net * 2, 25)
            print(f"  资金面扫描完成: {len(scores)} 只有主力流入")
            self.src_status['资金面'] = '✅ 东方财富资金流'
        except Exception as e:
            print(f"  ⚠️ 资金面扫描异常: {e}")
            self.src_status['资金面'] = '⚠️ 跳过(东方财富接口不可用)'
        return scores

    # ═══ C. 估值面 ═══

    def scan_valuation(self, stock_codes=None) -> dict:
        """
        估值筛选：低PB。
        - 给定候选代码时：用腾讯实时行情的 PB(市净率) 逐只评分（替代东方财富 stock_a_all_pb）。
        - 未给定代码时：尝试东方财富全市场PB（本环境通常被掐断，优雅降级）。
        """
        scores = defaultdict(float)
        # 候选模式：腾讯源逐只取 PB
        if stock_codes:
            from tencent_market import tencent_quote
            hit = 0
            for code in stock_codes:
                try:
                    q = tencent_quote(code)
                    if q and q.get('pb') and 0.5 < q['pb'] < 3:
                        scores[code] += (3 - q['pb']) * 5
                        hit += 1
                except Exception:
                    continue
            print(f"  估值面扫描完成(腾讯PB): {hit} 只低估值候选")
            self.src_status['估值面'] = '✅ 腾讯实时PB'
            return scores
        # 全市场模式（东财，本环境通常不可用）
        try:
            import akshare as ak
            import pandas as pd
            all_pb = ak.stock_a_all_pb()
            if all_pb is not None and len(all_pb) > 0:
                pb_col = [c for c in all_pb.columns if 'PB' in str(c) or '市净率' in str(c)]
                code_col = [c for c in all_pb.columns if '代码' in str(c) or 'code' in str(c).lower()]
                if pb_col and code_col:
                    all_pb['pb_val'] = pd.to_numeric(all_pb[pb_col[0]], errors='coerce')
                    low_pb = all_pb[all_pb['pb_val'] > 0].nsmallest(30, 'pb_val')
                    for _, row in low_pb.iterrows():
                        code = str(row[code_col[0]])
                        pb = float(row['pb_val'])
                        if 0.5 < pb < 3:
                            scores[code] += (3 - pb) * 5
            print(f"  估值面扫描完成: {len(scores)} 只低估值")
            self.src_status['估值面'] = '✅ 东方财富全市场PB'
        except Exception as e:
            print(f"  ⚠️ 估值面扫描异常(东财全市场PB不可用): {e}")
            self.src_status['估值面'] = '⚠️ 跳过(东方财富不可用，且无候选)'
        return scores

    # ═══ E. 宏观政策面 ═══

    def scan_macro_policy(self) -> dict:
        """宏观/政策面：市场情绪 + 指数位置 + 政策信号"""
        scores = defaultdict(float)
        macro_bias = 0  # 全局偏多/偏空信号
        try:
            # 1. AI市场情绪
            from ai_sentiment import get_sentiment_signal
            sentiment = get_sentiment_signal()
            macro_bias = sentiment * 5  # -5 ~ +5
            print(f"  宏观: AI情绪={sentiment:+.2f}  → 全局权重{macro_bias:+.0f}")

            # 2. 指数位置（腾讯指数日K线替代东方财富 stock_zh_index_daily）
            from tencent_market import tencent_index_daily
            idx_closes = tencent_index_daily('sh000001', days=400)
            if len(idx_closes) >= 60:
                arr = np.array(idx_closes, dtype=float)
                ma60 = arr[-60:].mean()
                if arr[-1] > ma60:
                    macro_bias += 3
                    print(f"  宏观: 指数在60日线上方 +3  | 总权重={macro_bias:+.0f}")
                else:
                    macro_bias -= 3
                    print(f"  宏观: 指数在60日线下方 -3  | 总权重={macro_bias:+.0f}")
            else:
                print(f"  宏观: 指数K线数据不足({len(idx_closes)}条)，跳过指数位置判断")

            # 3. 市场宽度（涨跌比）— 腾讯无全市场快照，优雅跳过（仅影响 ±2 权重）
            print(f"  宏观: 涨跌比维度不可用（腾讯无全市场快照），跳过 ±2 权重")
            self.src_status['宏观面'] = '✅ 腾讯指数 + ⚠️ 涨跌比跳过(腾讯无快照)'

        except Exception as e:
            print(f"  ⚠️ 宏观面扫描异常: {e}")
            self.src_status['宏观面'] = '⚠️ 跳过(指数/情绪异常)'

        # 全局偏多版块加分，偏空版块减分
        self.macro_bias = macro_bias
        return scores

    def apply_macro_bias(self, stock_scores: dict) -> dict:
        """将宏观偏多/偏空信号应用到所有个股"""
        if not hasattr(self, 'macro_bias') or self.macro_bias == 0:
            return stock_scores
        for code in list(stock_scores.keys()):
            # 同向加分，反向减半
            if stock_scores[code] > 0:
                stock_scores[code] += self.macro_bias
            else:
                stock_scores[code] += self.macro_bias * 0.5
        return stock_scores

    # ═══ F. 行业轮动面 ═══

    def scan_industry_rotation(self) -> dict:
        """行业轮动：热门板块+资金流向"""
        scores = defaultdict(float)
        hot_sectors = set()
        inflow_sectors = set()
        try:
            import akshare as ak
            # 热门板块排行
            hot = ak.stock_hot_rank_em()
            hot_sectors = set()
            for _, row in hot.head(5).iterrows():
                name = str(row.get('股票名称', ''))
                if name and name != 'nan':
                    hot_sectors.add(name)
            print(f"  行业: 热门板块TOP5 = {hot_sectors}")

            # 板块资金流
            flow = ak.stock_sector_fund_flow_rank()
            inflow_sectors = set()
            for _, row in flow.head(5).iterrows():
                name = str(row.get('名称', ''))
                if name:
                    inflow_sectors.add(name)
            print(f"  行业: 资金流入TOP5 = {inflow_sectors}")
            self.src_status['行业面'] = '✅ 东方财富板块'
        except Exception as e:
            print(f"  ⚠️ 行业轮动扫描异常: {e}")
            self.src_status['行业面'] = '⚠️ 跳过(东方财富不可用)'

        self.hot_sectors = hot_sectors
        self.inflow_sectors = inflow_sectors
        return scores

    def apply_industry_bias(self, stock_scores: dict) -> dict:
        """热门行业个股加权"""
        # 简化：用已知的行业映射
        sector_map = {
            '000001':'金融', '600036':'银行', '601398':'银行',
            '600519':'消费', '000858':'消费', '300750':'新能源',
            '002594':'汽车', '000625':'汽车',
            '600276':'医药', '688981':'科技', '300059':'金融科技',
            '000002':'地产', '600900':'电力', '600050':'通信',
            '600547':'黄金', '000333':'家电',
        }
        # 热门行业个股 +5
        for code, sector in sector_map.items():
            if sector in self.hot_sectors or sector in self.inflow_sectors:
                if code in stock_scores:
                    stock_scores[code] += 5
        return stock_scores

    # ═══ G. 筹码面 ═══

    def scan_chip_structure(self) -> dict:
        """筹码集中度：股东户数下降=主力吸筹"""
        scores = defaultdict(float)
        try:
            import akshare as ak
            df = ak.stock_hold_change_cninfo()
            if df is not None and len(df) > 0:
                for _, row in df.head(50).iterrows():
                    code = str(row.get('证券代码', '')).strip()
                    if code and len(code) == 6:
                        change = float(row.get('股东户数变动', 0))
                        if change < -5:  # 股东减少5%以上
                            scores[code] += 15  # 强吸筹
                        elif change < -2:
                            scores[code] += 8   # 中度吸筹
            print(f"  筹码面扫描完成: {len(scores)} 只筹码集中")
            self.src_status['筹码面'] = '✅ 股东户数(cninfo)'
        except Exception as e:
            print(f"  ⚠️ 筹码面扫描异常: {e}")
            self.src_status['筹码面'] = '⚠️ 跳过(股东户数接口不可用)'
        return scores

    # ═══ H. 财务面 ═══

    def scan_financial_health(self) -> dict:
        """财务健康：ROE + 营收增速"""
        scores = defaultdict(float)
        try:
            import akshare as ak
            df = ak.stock_yjbb_em(date=str(datetime.now().year) + '0331')
            if df is not None and len(df) > 0:
                for _, row in df.head(100).iterrows():
                    code = str(row.get('股票代码', ''))
                    roe = float(row.get('净资产收益率', 0)) if row.get('净资产收益率') else 0
                    rev_growth = float(row.get('营业收入同比增长', 0)) if row.get('营业收入同比增长') else 0
                    if roe > 15: scores[code] += 10
                    elif roe > 10: scores[code] += 5
                    if rev_growth > 20: scores[code] += 8
                    elif rev_growth > 10: scores[code] += 4
            print(f"  财务面扫描完成: {len(scores)} 只优质")
            self.src_status['财务面'] = '✅ 东方财富财报'
        except Exception as e:
            print(f"  ⚠️ 财务面扫描异常: {e}")
            self.src_status['财务面'] = '⚠️ 跳过(东方财富不可用)'
        return scores

    # ═══ I. 龙虎榜 ═══

    def scan_dragon_tiger(self) -> dict:
        """龙虎榜：机构/游资净买入"""
        scores = defaultdict(float)
        try:
            import akshare as ak
            df = ak.stock_lhb_detail_em()
            if df is not None and len(df) > 0:
                # 按股票汇总净买入
                net_buy = defaultdict(float)
                for _, row in df.iterrows():
                    code = str(row.get('代码', ''))
                    if code:
                        buy = float(row.get('买入金额', 0))
                        sell = float(row.get('卖出金额', 0))
                        net_buy[code] += (buy - sell)
                for code, net in net_buy.items():
                    net_wan = net / 10000  # 万元
                    if net_wan > 5000:      scores[code] += 20   # 大额净买
                    elif net_wan > 1000:    scores[code] += 12
                    elif net_wan > 0:       scores[code] += 6
            print(f"  龙虎榜扫描完成: {len(scores)} 只上榜净买")
            self.src_status['龙虎榜'] = '✅ 东方财富龙虎榜'
        except Exception as e:
            print(f"  ⚠️ 龙虎榜扫描异常: {e}")
            self.src_status['龙虎榜'] = '⚠️ 跳过(东方财富不可用)'
        return scores

    # ═══ J. ML精排 ═══

    def scan_ml_rerank(self, stock_scores: dict, top_n: int) -> dict:
        """ML对候选TOP50做终审精排"""
        try:
            candidates = sorted(stock_scores.items(), key=lambda x: -x[1])[:min(50, len(stock_scores))]
            if len(candidates) < 10:
                return stock_scores

            # 用ML预测方向辅助调整分数
            from ml_stock_predict import fetch_market_data, engineer_features
            df = fetch_market_data(years=1)
            if df is not None:
                features = engineer_features(df)
                latest = features.iloc[-1:] if len(features) > 0 else None
                if latest is not None:
                    # ML偏多/偏空信号
                    try:
                        from ml_stock_predict import predict_today as _ml_predict
                        ml_result = _ml_predict()
                        ml_trend = ml_result.get('trend_prediction', '')
                        ml_conf = ml_result.get('confidence', 0)
                        if '涨' in ml_trend:
                            # ML看多→多头股加分
                            for code, _ in candidates[:15]:
                                if code in stock_scores and stock_scores[code] > 0:
                                    stock_scores[code] += int(ml_conf * 10)
                        elif '跌' in ml_trend:
                            # ML看空→空头股减分
                            for code, _ in candidates[:15]:
                                if code in stock_scores and stock_scores[code] > 0:
                                    stock_scores[code] -= int(ml_conf * 8)
                        print(f"  ML精排完成: 趋势={ml_trend} 置信={ml_conf:.0%}")
                    except:
                        pass
            self.src_status['ML精排'] = '✅ 随机森林(固定种子)'
        except Exception as e:
            print(f"  ⚠️ ML精排异常: {e}")
            self.src_status['ML精排'] = '⚠️ 跳过(ML异常)'
        return stock_scores

    # ═══ D. 六壬面 ═══

    def scan_liuren(self) -> dict:
        """六壬课盘吉凶交叉验证"""
        scores = defaultdict(float)
        try:
            # 从 multi_stock 预测文件读取
            multi_files = sorted(
                [f for f in os.listdir(MEMORY) if f.startswith('multi_stock_')],
                reverse=True
            )
            if multi_files:
                with open(os.path.join(MEMORY, multi_files[0]), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                stock_data = data if isinstance(data, list) else data.get('predictions', [])
                for s in stock_data:
                    code = s.get('symbol', '')
                    trend = s.get('trend', '')
                    # 吉凶打分
                    if '涨' in trend:
                        scores[code] += 20
                    elif '先涨' in trend:
                        scores[code] += 15
                    elif '震荡偏涨' in trend:
                        scores[code] += 8
                    elif '跌' in trend:
                        scores[code] -= 20
                    elif '先跌' in trend:
                        scores[code] -= 10
                print(f"  六壬面扫描完成: {len(scores)} 只有预测")
            self.src_status['六壬面'] = '✅ 本地课盘预测'
        except Exception as e:
            print(f"  ⚠️ 六壬面扫描异常: {e}")
            self.src_status['六壬面'] = '⚠️ 跳过(本地预测缺失)'
        return scores

    # ═══ 综合 ═══

    def run(self, top_n=15):
        """执行全维度扫描（两阶段：初筛→精算）"""
        print("=" * 55)
        print("  🔍 量化选股器 v2.1 — 十一维多因子扫描")
        print("=" * 55)

        # ===== 第一阶段：快速初筛 =====
        all_scores = defaultdict(float)

        # 六壬面：始终运行（用于观察验证 / 积累数据），但默认不参与评分
        liuren_scores = self.scan_liuren()

        for name, scanner in [
            ('技术面', self.scan_momentum),
            ('资金面', self.scan_capital_flow),
            # ('六壬面', self.scan_liuren),  # 已解耦：参考模式不参与决策分
            ('宏观面', self.scan_macro_policy),
            ('行业面', self.scan_industry_rotation),
            ('筹码面', self.scan_chip_structure),
            ('财务面', self.scan_financial_health),
            ('龙虎榜', self.scan_dragon_tiger),
        ]:
            try:
                dim_scores = scanner()
                if name in ('宏观面', '行业面'):
                    continue
                for code, score in dim_scores.items():
                    all_scores[code] += score
            except Exception as e:
                print(f"  ❌ {name}: {e}")

        # 参考模式：六壬分不计入决策分，仅作展示/验证
        if not LIUREN_REFERENCE_ONLY:
            # 训练验证通过后，六壬参与评分
            for code, score in liuren_scores.items():
                all_scores[code] += score
        else:
            # 参考模式：单独保存六壬分，供前端标注
            self.liuren_scores = liuren_scores

        # 应用宏观 + 行业全局权重
        all_scores = self.apply_macro_bias(all_scores)
        all_scores = self.apply_industry_bias(all_scores)

        # ===== 第二阶段：趋势质量精算（TOP50候选）=====
        print("\n  --- 趋势质量精算阶段 ---")
        top_candidates = sorted(all_scores.items(), key=lambda x: -x[1])[:50]
        top_codes = [code for code, _ in top_candidates]
        trend_scores = self.scan_trend_quality(top_codes)
        for code, score in trend_scores.items():
            all_scores[code] += score

        # 估值面精算（TOP候选，腾讯PB替代东财全市场PB）
        val_scores = self.scan_valuation(top_codes)
        for code, score in val_scores.items():
            all_scores[code] += score

        # ML终审精排（对TOP50候选）
        all_scores = self.scan_ml_rerank(all_scores, top_n)

        # 按总分排序
        sorted_stocks = sorted(all_scores.items(), key=lambda x: -x[1])

        # 获取名称（腾讯实时行情替代东方财富 stock_zh_a_spot_em）
        name_map = {}
        from tencent_market import tencent_quote
        for code in [c for c, _ in sorted_stocks[:top_n]]:
            try:
                q = tencent_quote(code)
                if q and q.get('name'):
                    name_map[code] = q['name']
            except Exception:
                pass
        # 本地名称缓存
        try:
            with open(os.path.join(BASE, 'data', 'stock_names.json'), 'r', encoding='utf-8') as f:
                local = json.load(f)
            for code, name in local.items():
                if code not in name_map:
                    name_map[code] = name
        except:
            pass

        # 输出
        print(f"\n  {'─'*50}")
        print(f"  {'排名':<4} {'代码':<8} {'名称':<10} {'总评分':<8} {'建议':<10}")
        print(f"  {'─'*50}")

        self.results = []
        for rank, (code, score) in enumerate(sorted_stocks[:top_n], 1):
            name = name_map.get(code, '?')
            # 建议（仅基于量化决策分）
            if score >= 80:
                advice = '🟢 强烈买入'
            elif score >= 50:
                advice = '🟢 买入'
            elif score >= 20:
                advice = '🟡 关注'
            elif score >= 0:
                advice = '⚪ 观望'
            else:
                advice = '🔴 回避'

            # 六壬参考分（不参与决策，仅展示/验证）
            liuren_score = round(float(liuren_scores.get(code, 0)), 1)
            liuren_tag = f"  六壬:{liuren_score:+5.0f}[参考]" if LIUREN_REFERENCE_ONLY else f"  六壬:{liuren_score:+5.0f}"

            print(f"  {rank:<4} {code:<8} {name:<10} {score:>+6.0f}   {advice}{liuren_tag}")
            self.results.append({
                'rank': rank, 'code': code, 'name': name,
                'score': round(score, 1), 'advice': advice,
                'liuren_score': liuren_score,  # 参考（不参与决策）
                'liuren_reference': LIUREN_REFERENCE_ONLY,
            })

        print(f"\n  扫描完成: {len(sorted_stocks)} 只候选 → TOP {top_n}")

        # ═══ 数据源可用性报告（透明可审计）═══
        print(f"\n  {'─'*50}")
        print(f"  📊 选股维度数据源状态:")
        print(f"  {'─'*50}")
        for dim in ['技术面', '趋势质量', '资金面', '估值面', '六壬面',
                    '宏观面', '行业面', '筹码面', '财务面', '龙虎榜', 'ML精排']:
            st = self.src_status.get(dim, '—')
            print(f"  {dim:<8} {st}")
        active = sum(1 for v in self.src_status.values() if v.startswith('✅'))
        skip = sum(1 for v in self.src_status.values() if v.startswith('⚠️'))
        print(f"  {'─'*50}")
        print(f"  ✅ 生效维度 {active} 个 | ⚠️ 跳过维度 {skip} 个（跳过项不影响确定性，仅减少部分因子）")
        if LIUREN_REFERENCE_ONLY:
            print(f"  🔰 六壬参考模式：六壬面评分【不参与】决策分，仅作观察验证（详见 config.LIUREN_REFERENCE_ONLY）")

        return self.results

    def save(self):
        """保存选股结果"""
        out = {
            'scanned_at': datetime.now(timezone.utc).isoformat(),
            'results': self.results,
        }
        path = os.path.join(MEMORY, 'stock_screener_result.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  💾 已保存: {path}")

    def quick_picks(self):
        """快速获取推荐股列表"""
        self.run(top_n=10)
        self.save()
        return [r for r in self.results if r['score'] >= 10]


# ── 命令行 ──
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='量化选股器')
    parser.add_argument('--top', type=int, default=15, help='返回Top N')
    parser.add_argument('--sector', type=str, default='', help='板块筛选')
    args = parser.parse_args()

    screener = QuantScreener()
    screener.run(top_n=args.top)
    screener.save()
