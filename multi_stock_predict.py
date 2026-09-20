#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一课多断：个股/多标的六壬预测系统
=================================
核心原理：六壬一课可断万事。同一时辰起一课，对不同标的取不同"类神"分析。

类象映射体系：
  1. 行业五行 → 个股所属五行（金木水火土）
  2. 股票代码 → 地支类象（代码尾数对应地支）
  3. 上市板块 → 板块五行属性

分析逻辑：
  起一课 → 对每个标的取对应的六亲/地支/天将为"类神"
        → 看类神在课传中的旺衰、生克、空亡、刑冲
        → 判断该标的当日吉凶趋势

用法：
  python multi_stock_predict.py                  # 预测所有标的
  python multi_stock_predict.py --symbol 600519  # 预测单个标的
"""

import json, os, sys, time, requests
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE, "_memory")

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"

# ═══════════════════════════════════════════════════════════
# 1. 个股类象映射表
# ═══════════════════════════════════════════════════════════

STOCK_LEIXIANG = {
    # ── 大盘指数 ──
    "000001": {"name":"上证指数","shen":"辰(天罡)","tianjiang":"勾陈","liuqin":"父母",
        "basis":"「天罡」所主「争田」→大盘为市场根基","category":"index"},
    "399001": {"name":"深证成指","shen":"戌(河魁)","tianjiang":"天空","liuqin":"父母",
        "basis":"「河魁」所主「印绶」→深市重科创","category":"index"},
    "399006": {"name":"创业板指","shen":"午(胜光)","tianjiang":"朱雀","liuqin":"子孙",
        "basis":"「胜光」所主「信息」→创业板重科技","category":"index"},
    # ── 白酒 → 未(小吉/太常)：「酒食」是太常明确定义 ──
    "600519": {"name":"贵州茅台","shen":"未(小吉)","tianjiang":"太常","liuqin":"妻财",
        "basis":"「小吉」所主「酒食」→茅台=白酒，太常直接对应","category":"consumer"},
    "000858": {"name":"五粮液","shen":"未(小吉)","tianjiang":"太常","liuqin":"妻财",
        "basis":"同上「酒食」类象","category":"consumer"},
    # ── 银行 → 酉(从魁/太阴):「金银」；丑(大吉/贵人):「珍宝」──
    "600036": {"name":"招商银行","shen":"酉(从魁)","tianjiang":"太阴","liuqin":"妻财",
        "basis":"「从魁」类象「金银」→银行=金银财富","category":"bank"},
    "601398": {"name":"工商银行","shen":"丑(大吉)","tianjiang":"贵人","liuqin":"妻财",
        "basis":"「大吉」所主「珍宝」→全球最大银行","category":"bank"},
    # ── 汽车 → 卯(太冲/六合)：「船车、驿马」；寅(功曹/青龙):「舟车」──
    "002594": {"name":"比亚迪","shen":"卯(太冲)","tianjiang":"六合","liuqin":"官鬼",
        "basis":"「太冲」类象「船车」→新能源车龙头","category":"auto"},
    "000625": {"name":"长安汽车","shen":"寅(功曹)","tianjiang":"青龙","liuqin":"妻财",
        "basis":"「功曹」类象「舟车」→传统车企","category":"auto"},
    # ── 电池 → 巳(太乙/螣蛇)：「炉冶、火光」──
    "300750": {"name":"宁德时代","shen":"巳(太乙)","tianjiang":"螣蛇","liuqin":"子孙",
        "basis":"「太乙」类象「炉冶」→电池制造之炉火","category":"tech"},
    # ── 医药 → 申(传送/白虎)：「药物」是白虎明确类象 ──
    "600276": {"name":"恒瑞医药","shen":"申(传送)","tianjiang":"白虎","liuqin":"子孙",
        "basis":"「传送」类象「药物」→医药直接对应","category":"pharma"},
    # ── 地产 → 辰(天罡/勾陈)：「争田、田宅」──
    "000002": {"name":"万科A","shen":"辰(天罡)","tianjiang":"勾陈","liuqin":"父母",
        "basis":"「天罡」所主「田宅」→地产直接对应","category":"realestate"},
    # ── 互联网 → 午(胜光/朱雀)：「信息、文书」──
    "300059": {"name":"东方财富","shen":"午(胜光)","tianjiang":"朱雀","liuqin":"妻财",
        "basis":"「胜光」所主「信息」→互联网券商","category":"internet"},
    # ── 芯片 → 巳(太乙)：「炉冶」喻芯片制造 ──
    "688981": {"name":"中芯国际","shen":"巳(太乙)","tianjiang":"螣蛇","liuqin":"官鬼",
        "basis":"「太乙」类象「炉冶」→芯片=炉冶之火","category":"chip"},
    # ── 黄金 → 酉(从魁)：「金银」明确 ──
    "600547": {"name":"山东黄金","shen":"酉(从魁)","tianjiang":"太阴","liuqin":"妻财",
        "basis":"「从魁」类象「金银、首饰」→黄金股","category":"gold"},
    # ── 电力 → 亥(登明/玄武)：「江河」 ──
    "600900": {"name":"长江电力","shen":"亥(登明)","tianjiang":"玄武","liuqin":"妻财",
        "basis":"「登明」类象「江河」→水电=江河之水","category":"power"},
    # ── 通信 → 申(传送)：「信息」传递 ──
    "600050": {"name":"中国联通","shen":"申(传送)","tianjiang":"白虎","liuqin":"父母",
        "basis":"「传送」所主「信息」→通信=信息传递","category":"telecom"},
}


# ═══════════════════════════════════════════════════════════
# 1.5 自动类象映射（量化选股器 → 六壬可分析股票池）
# ═══════════════════════════════════════════════════════════

# 代码尾数 → 地支
_DIZHI_MAP = {
    '0': '子', '1': '丑', '2': '寅', '3': '卯', '4': '辰',
    '5': '巳', '6': '午', '7': '未', '8': '申', '9': '酉'
}

# 地支 → 十二神（标准映射，以月将加时旋转）
_SHISHEN_MAP = {
    '子': '登明', '丑': '大吉', '寅': '功曹', '卯': '太冲',
    '辰': '天罡', '巳': '太乙', '午': '胜光', '未': '小吉',
    '申': '传送', '酉': '从魁', '戌': '河魁', '亥': '神后'
}

# 股票代码尾数 → 地支 → 天将 的类象映射（股票类象分析用，非六壬排盘天将；
# 排盘天将须经 gui_ren_engine 贵人加临顺逆排布，此处为固定类象表）
_TIANJIANG_MAP = {
    '子': '贵人', '丑': '螣蛇', '寅': '朱雀', '卯': '六合',
    '辰': '勾陈', '巳': '青龙', '午': '天空', '未': '白虎',
    '申': '太常', '酉': '玄武', '戌': '太阴', '亥': '天后'
}

# 行业/名称关键词 → 五行
_INDUSTRY_WUXING = {
    '银行|证券|保险|多元金融|信托': '金',
    '芯片|半导体|科技|通信|互联网|软件|电子|计算机': '火',
    '地产|基建|建材|工程|水泥|装修': '土',
    '医药|医疗|食品|饮料|农业|白酒|消费|养殖': '木',
    '能源|有色|钢铁|煤炭|石油|黄金|矿业': '金',
    '电力|水力|环保|公用事业|水务': '水',
    '汽车|机械|化工|制造|电器|轻工': '木',
    '军工|国防|航天|航空': '金',
    '传媒|广告|文化|教育': '火',
    '物流|运输|交通|港口': '水',
}

# 日干五行 → 六亲映射表
# 生我者为父母，我生者为子孙，克我者为官鬼，我克者为妻财，同我者为兄弟
_GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
}
_SHENGWUXING = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
}
_KEWUXING = {
    '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
}
_WUXING_LIUQIN = {
    '父母': {'relation': '生我', 'element': None},  # 日干生此五行
    '子孙': {'relation': '我生', 'element': None},  # 日干所生
    '官鬼': {'relation': '克我', 'element': None},  # 克日干
    '妻财': {'relation': '我克', 'element': None},  # 日干所克
    '兄弟': {'relation': '同我', 'element': None},  # 同日干
}


def _infer_wuxing(name_or_industry, industry=None):
    """从股票名称/行业推断五行"""
    import re
    text = f"{name_or_industry} {industry or ''}"
    for pattern, wx in _INDUSTRY_WUXING.items():
        if re.search(pattern, text):
            return wx
    return '土'


def auto_map_leixiang(symbol, name, industry=None, day_gan=None):
    """自动映射股票类象（当不在硬编码字典中时使用）

    Args:
        symbol: 股票代码
        name: 股票名称
        industry: 行业（可选）
        day_gan: 日干（如'甲'），用于推算六亲

    Returns:
        dict: 类象映射信息
    """
    import re
    code = str(symbol).strip()
    last_digit = code[-1]
    dizhi = _DIZHI_MAP.get(last_digit, '子')
    shen_name = _SHISHEN_MAP.get(dizhi, '未知')
    tianjiang = _TIANJIANG_MAP.get(dizhi, '未知')

    # 推断五行
    wuxing = '土'
    text = f"{name} {industry or ''}"
    for pattern, wx in _INDUSTRY_WUXING.items():
        if re.search(pattern, text):
            wuxing = wx
            break

    # 推断六亲（基于日干五行与股票五行的关系）
    liuqin = '兄弟'  # 默认
    if day_gan:
        gan_wx = _GAN_WUXING.get(day_gan, '土')
        # 关系判断
        if _SHENGWUXING.get(gan_wx) == wuxing:
            liuqin = '子孙'  # 日干生股票五行 → 泄气
        elif _SHENGWUXING.get(wuxing) == gan_wx:
            liuqin = '父母'  # 股票五行生日干 → 得生
        elif _KEWUXING.get(gan_wx) == wuxing:
            liuqin = '妻财'  # 日干克股票五行 → 财
        elif _KEWUXING.get(wuxing) == gan_wx:
            liuqin = '官鬼'  # 股票五行克日干 → 官
        else:
            liuqin = '兄弟'  # 同五行

    return {
        'name': name,
        'shen': f'{dizhi}({shen_name})',
        'tianjiang': tianjiang,
        'liuqin': liuqin,
        'wuxing': wuxing,
        'dizhi': dizhi,
        'basis': f'自动映射：代码尾数{last_digit}→{dizhi}→{shen_name}/{tianjiang}，行业/名称五行→{wuxing}，日干{day_gan}→六亲{liuqin}',
        'auto_mapped': True,
        'category': 'auto',
    }


def get_leixiang_for_stock(symbol, name, industry=None, day_gan=None):
    """获取股票类象：先查硬编码，再自动映射"""
    if symbol in STOCK_LEIXIANG:
        info = dict(STOCK_LEIXIANG[symbol])
        info['auto_mapped'] = False
        return info
    return auto_map_leixiang(symbol, name, industry, day_gan)


def load_screener_pool(top_n=15):
    """从量化选股器结果加载股票池"""
    result_file = os.path.join(MEMORY, "stock_screener_result.json")
    if not os.path.exists(result_file):
        print(f"  ⚠️ 选股结果文件不存在: {result_file}")
        return []
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', [])
    return results[:top_n]


def get_market_timing(target_date=None):
    """① 六壬择时：读取当日大盘预测，判断今日是否适合开仓

    从 stock_predictions.json 中读取 fixed_time 类别的最新大盘预测，
    基于吉凶+趋势判断今日是看多/看空/观望。

    Returns:
        dict: {
            'signal': 'bull' | 'bear' | 'neutral',  # 看多/看空/中性
            'jixiong': '吉' | '凶' | '中平' | ...,    # 吉凶
            'trend': '涨' | '跌' | ...,               # 趋势
            'analysis': '...',                        # 分析
            'rizhu': '',                              # 日柱
            'shichen': '',                            # 占时
            'target_date': '',                        # 预测目标日
            'source': 'stock_predictions.json'
        }
    """
    import os as _os
    import json as _json
    pred_file = _os.path.join(MEMORY, "stock_predictions.json")
    if not _os.path.exists(pred_file):
        return {
            'signal': 'neutral',
            'jixiong': '',
            'trend': '',
            'analysis': '暂无大盘预测数据',
            'rizhu': '',
            'shichen': '',
            'target_date': target_date or '',
            'source': 'none'
        }

    try:
        with open(pred_file, 'r', encoding='utf-8') as f:
            predictions = _json.load(f)
    except Exception:
        return {
            'signal': 'neutral',
            'jixiong': '',
            'trend': '',
            'analysis': '读取预测文件失败',
            'rizhu': '',
            'shichen': '',
            'target_date': target_date or '',
            'source': 'error'
        }

    # 找 fixed_time 类别的最新预测
    from datetime import datetime as _dt
    today_str = target_date or _dt.now().strftime("%Y-%m-%d")
    latest = None
    for p in reversed(predictions):
        if p.get('category') == 'fixed_time' and p.get('target_date') == today_str:
            latest = p
            break

    if latest is None:
        # 找不到今天的，取最新的一条 fixed_time
        for p in reversed(predictions):
            if p.get('category') == 'fixed_time':
                latest = p
                break

    if latest is None:
        return {
            'signal': 'neutral',
            'jixiong': '',
            'trend': '',
            'analysis': '无 fixed_time 类别的大盘预测',
            'rizhu': '',
            'shichen': '',
            'target_date': today_str,
            'source': 'none'
        }

    jx = latest.get('jixiong', '')
    trend = latest.get('trend_prediction', '')

    # 判断信号
    signal = 'neutral'
    bullish_jx = ('吉', '大吉', '小吉')
    bearish_jx = ('凶', '大凶', '小凶')
    bullish_trend_keywords = ('涨', '上涨', '先涨', '先涨后跌')
    bearish_trend_keywords = ('跌', '下跌', '先跌', '先跌后涨')

    is_jx_bull = any(b in jx for b in bullish_jx)
    is_jx_bear = any(b in jx for b in bearish_jx)
    is_trend_bull = any(b in trend for b in bullish_trend_keywords)
    is_trend_bear = any(b in trend for b in bearish_trend_keywords)

    if is_jx_bull and is_trend_bull:
        signal = 'bull'
    elif is_jx_bear and is_trend_bear:
        signal = 'bear'
    elif is_jx_bull or is_trend_bull:
        signal = 'bull'
    elif is_jx_bear or is_trend_bear:
        signal = 'bear'
    else:
        signal = 'neutral'

    return {
        'signal': signal,
        'jixiong': jx,
        'trend': trend,
        'analysis': latest.get('analysis', ''),
        'rizhu': latest.get('rizhu', ''),
        'shichen': latest.get('shi_chen', ''),
        'target_date': latest.get('target_date', ''),
        'predict_time': latest.get('predict_time', ''),
        'source': 'stock_predictions.json'
    }


def calc_position_quant_only(screener_score=0):
    """⑤ 仓位管理（参考模式）：仅按量化评分给仓位建议，忽略六壬择时

    量化决策分直接映射到仓位，六壬不参与：
    - 评分≥80 → 重仓(80%)
    - 评分≥50 → 中仓(50%)
    - 评分≥20 → 轻仓(20%)
    - 评分<20 → 观望(0%)

    Args:
        screener_score: 量化评分

    Returns:
        dict: {'level': str, 'pct': float, 'reason': str}
    """
    score = float(screener_score or 0)
    if score >= 80:
        return {'level': '重仓', 'pct': 80, 'reason': '量化高分，重仓参与'}
    elif score >= 50:
        return {'level': '中仓', 'pct': 50, 'reason': '量化达标，中仓参与'}
    elif score >= 20:
        return {'level': '轻仓', 'pct': 20, 'reason': '量化偏弱，轻仓观察'}
    else:
        return {'level': '观望', 'pct': 0, 'reason': '量化不足，观望'}


def calc_position(liuren_confidence, market_signal, screener_score=0):
    """⑤ 仓位管理：基于六壬置信度 + 大盘择时信号 + 量化评分计算建议仓位

    仓位规则:
    - 大盘看空 → 空仓/极轻仓(≤10%)
    - 大盘中性 + 六壬置信度≥70% → 重仓(60-80%)
    - 大盘中性 + 六壬置信度50-70% → 轻仓(20-40%)
    - 大盘中性 + 六壬置信度<50% → 观望
    - 大盘看多 + 六壬置信度≥70% → 满仓(80-100%)
    - 大盘看多 + 六壬置信度50-70% → 中仓(40-60%)
    - 大盘看多 + 六壬置信度<50% → 轻仓(10-20%)

    注意：参考模式（LIUREN_REFERENCE_ONLY=True）下，本函数不被调用，
    由 calc_position_quant_only() 替代，六壬择时与置信度均不参与。

    Args:
        liuren_confidence: 六壬置信度 0-1
        market_signal: 'bull'/'bear'/'neutral'
        screener_score: 量化评分 (可选，微调用)

    Returns:
        dict: {'level': str, 'pct': float, 'reason': str}
    """
    conf = float(liuren_confidence or 0)

    if market_signal == 'bear':
        # 大盘看空，不管个股怎么样都要控制仓位
        if conf >= 0.7:
            return {'level': '极轻仓', 'pct': 10, 'reason': '大盘看空，即使个股看涨也仅极轻仓试探'}
        else:
            return {'level': '空仓观望', 'pct': 0, 'reason': '大盘看空，建议空仓观望'}

    if market_signal == 'bull':
        # 大盘看多，仓位可以重一些
        if conf >= 0.7:
            return {'level': '满仓', 'pct': 90, 'reason': '大盘看多+六壬高置信，建议满仓'}
        elif conf >= 0.5:
            return {'level': '中仓', 'pct': 50, 'reason': '大盘看多+六壬中等置信，建议中仓'}
        else:
            return {'level': '轻仓', 'pct': 15, 'reason': '大盘看多但六壬置信不足，轻仓参与'}
    else:
        # 中性震荡，精选个股
        if conf >= 0.7:
            return {'level': '重仓', 'pct': 70, 'reason': '震荡市+六壬高置信，重仓精选个股'}
        elif conf >= 0.5:
            return {'level': '轻仓', 'pct': 30, 'reason': '震荡市+六壬中等置信，轻仓参与'}
        else:
            return {'level': '观望', 'pct': 0, 'reason': '震荡市+六壬低置信，建议观望'}


def dual_phase_select(top_n=15, day_gan=None):
    """双阶段选股：量化海选 → 六壬标注（参考模式不淘汰）

    结合①六壬择时 + ⑤仓位管理：
    - 先判断今日大盘吉凶，决定整体仓位基调
    - 再对个股逐一计算建议仓位

    参考模式（LIUREN_REFERENCE_ONLY=True）：
    - 六壬不再淘汰任何个股，仅作标注/对照
    - 仓位由量化评分决定（calc_position_quant_only）

    Returns:
        list: 双重验证后的推荐列表（含量化评分+六壬预测+仓位建议）
    """
    # 参考模式开关
    try:
        from config import LIUREN_REFERENCE_ONLY
    except Exception:
        LIUREN_REFERENCE_ONLY = True

    # 阶段0：大盘择时（参考模式仅记录，不影响选股）
    timing = get_market_timing()
    market_signal = timing.get('signal', 'neutral')
    signal_map = {'bull': '📈看多', 'bear': '📉看空', 'neutral': '➡️中性'}
    if LIUREN_REFERENCE_ONLY:
        print(f"\n  📅 六壬择时·参考：{signal_map.get(market_signal, '?')}（吉凶:{timing.get('jixiong','?')} 趋势:{timing.get('trend','?')}）【仅参考·不影响选股】")
    else:
        print(f"\n  📅 六壬择时：{signal_map.get(market_signal, '?')}（吉凶:{timing.get('jixiong','?')} 趋势:{timing.get('trend','?')}）")

    # 阶段1：量化选股
    screener_pool = load_screener_pool(top_n)
    if not screener_pool:
        print("  ❌ 量化选股池为空")
        return []

    print(f"\n  📊 阶段1：量化选股 → {len(screener_pool)} 只候选")
    for s in screener_pool:
        print(f"    #{s.get('rank')} {s.get('name')}({s.get('code')}) 评分:{s.get('score')} {s.get('advice')}")

    # 阶段2：六壬精选（参考模式仅标注，不淘汰）
    symbols = [s['code'] for s in screener_pool]
    predictions = predict_multi_stocks(symbols=symbols, day_gan=day_gan)

    if not predictions:
        print("  ❌ 六壬预测失败（参考模式：不影响选股，按量化处理）")
        return screener_pool

    # 合并结果 + 仓位计算
    liuren_map = {p['symbol']: p for p in predictions}
    dual_results = []
    for s in screener_pool:
        p = liuren_map.get(s['code'], {})
        trend = p.get('trend', '')
        jixiong = p.get('jixiong', '')
        conf = float(p.get('confidence', 0))
        is_bullish_trend = ('涨' in trend or '先涨' in trend)
        is_favorable_jx = jixiong in ('吉', '中平')

        if LIUREN_REFERENCE_ONLY:
            # 参考模式：六壬不淘汰个股，全部保留；标注参考信息
            # 验证等级仅反映"量化达标与否"，六壬仅作对照展示
            verify_level = 'verified' if (s.get('score', 0) or 0) >= 50 else 'watch'
        else:
            # 原逻辑：六壬三级验证（通过/观察/淘汰），置信度门槛≥50%
            if is_bullish_trend and is_favorable_jx and conf >= 0.5:
                verify_level = 'verified'     # ✅ 通过：看涨+吉/中平+置信度≥50%
            elif is_bullish_trend and is_favorable_jx and conf >= 0.4:
                verify_level = 'watch'        # 👀 观察：看涨+吉/中平+置信度40-50%
            elif is_bullish_trend and conf >= 0.4:
                verify_level = 'watch'        # 👀 观察：看涨但吉凶不明+置信度≥40%
            else:
                verify_level = 'rejected'     # ❌ 淘汰

        # ⑤ 仓位管理
        if LIUREN_REFERENCE_ONLY:
            position = calc_position_quant_only(s.get('score', 0))
        else:
            position = calc_position(conf, market_signal, s.get('score', 0))

        dual_results.append({
            'code': s.get('code'),
            'name': s.get('name'),
            'screener_rank': s.get('rank'),
            'screener_score': s.get('score'),
            'screener_advice': s.get('advice'),
            'liuren_trend': trend,
            'liuren_jixiong': jixiong,
            'liuren_confidence': conf,
            'liuren_analysis': p.get('analysis', ''),
            'liuren_reference': LIUREN_REFERENCE_ONLY,
            'dual_verified': verify_level == 'verified',
            'verify_level': verify_level,
            'position_level': position['level'],
            'position_pct': position['pct'],
            'position_reason': position['reason'],
        })

    # 排序：参考模式按量化评分；原逻辑按验证等级+量化评分
    if LIUREN_REFERENCE_ONLY:
        dual_results.sort(key=lambda x: (x['screener_score'] or 0), reverse=True)
    else:
        level_order = {'verified': 2, 'watch': 1, 'rejected': 0}
        dual_results.sort(key=lambda x: (level_order.get(x['verify_level'], 0), x['screener_score']), reverse=True)

    verified = [r for r in dual_results if r['verify_level'] == 'verified']
    watching = [r for r in dual_results if r['verify_level'] == 'watch']
    if LIUREN_REFERENCE_ONLY:
        print(f"\n  🎯 阶段2：六壬标注（参考） → 量化达标 {len(verified)} / 观察 {len(watching)} / 共 {len(dual_results)}（六壬不参与淘汰）")
    else:
        print(f"\n  🎯 阶段2：六壬精选 → ✅通过 {len(verified)} / 👀观察 {len(watching)} / 共 {len(dual_results)}")
    for r in verified:
        print(f"    {'✅' if not LIUREN_REFERENCE_ONLY else '📊'} {r['name']}({r['code']}) 量化:{r['screener_score']} 六壬:{r['liuren_trend']}/{r['liuren_jixiong']} 置信:{r['liuren_confidence']:.0%} → {r['position_level']}({r['position_pct']}%)")
    for r in watching:
        print(f"    👀 {r['name']}({r['code']}) 量化:{r['screener_score']} 六壬:{r['liuren_trend']}/{r['liuren_jixiong']} 置信:{r['liuren_confidence']:.0%} → {r['position_level']}({r['position_pct']}%)")

    # 大盘择时信息也返回（放在第一个元素的market_timing字段）
    return dual_results, timing


# ═══════════════════════════════════════════════════════════
# 1.6 真随机占时（活时法：物理熵源模拟掷铜钱/抽签）
# ═══════════════════════════════════════════════════════════

DIZHI_LIST = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

def true_random_shichen(timeout=3):
    """活时法：从 random.org 大气噪声 API 获取真随机数，映射到12时辰

    原理: random.org 用大气无线电噪声生成真随机数,
    数学上不可预测,接近传统六壬"掷铜钱/抽签"求活时的本质。

    Args:
        timeout: HTTP请求超时秒数

    Returns:
        tuple: (时辰地支, 来源说明)
    """
    try:
        import requests as _req
        r = _req.get(
            "https://www.random.org/integers/",
            params={
                "num": 1,
                "min": 0,
                "max": 11,
                "col": 1,
                "base": 10,
                "format": "plain",
            },
            timeout=timeout,
        )
        if r.status_code == 200:
            idx = int(r.text.strip())
            if 0 <= idx <= 11:
                return DIZHI_LIST[idx], f"random.org大气噪声(熵源:idx={idx})"
    except Exception as e:
        pass
    return None, "random.org不可用"


def huoshi_paipan():
    """活时法排盘:真随机择时 + 完整排盘

    适用场景:用户主动"求天机",无自然正时(非求测时刻)。
    例如:页面点击"人工占一课"按钮 / 命令行 `python multi_stock_predict.py --mode huoshi`

    Returns:
        tuple: (排盘文本, 日柱, 占时, 来源说明)
    """
    now = get_beijing_now()
    rizhu = get_rizhu(now.date())
    yuejiang = get_yuejiang(now.date())

    # 1. 获取真随机占时
    shichen, source = true_random_shichen()
    if shichen is None:
        # 降级方案:用毫秒级时间戳作为局部熵源(比 random.choice 更不可预测)
        import time as _t
        microsec = int((_t.time() % 1) * 1_000_000)
        idx = microsec % 12
        shichen = DIZHI_LIST[idx]
        source = f"本地时间戳微秒(降级:idx={idx})"

    # 2. 排盘（V2 权威引擎，与古例/天机起课同源）
    try:
        paipan_text, rizhu, shichen = _paipan_v2(rizhu, yuejiang, shichen)
        paipan_text = f"""日柱: {rizhu}  月将: {yuejiang}  占时: {shichen}（活时法:{source}）
{paipan_text}"""
        return paipan_text, rizhu, shichen, source
    except Exception as e:
        return f"活时排盘异常: {e}", rizhu, shichen, source


# ═══════════════════════════════════════════════════════════
# 2. 一课多断分析Prompt
# ═══════════════════════════════════════════════════════════

def build_multi_stock_prompt(paipan_text, rizhu, shi_chen, stocks):
    """构建一课多断的分析Prompt"""

    stocks_desc = []
    for sym, info in stocks.items():
        basis = info.get('basis', '')
        stocks_desc.append(
            f"- {info['name']}({sym})：十二神={info['shen']}，"
            f"天将={info['tianjiang']}，类神取{info['liuqin']}爻"
            f"{' —「' + basis + '」' if basis else ''}"
        )

    prompt = f"""你是一位精通大六壬一课多断的专家。以下是同一时辰的排盘，请对多个股票标的分别分析。

【排盘数据】
{paipan_text}

日柱: {rizhu} | 占时: {shi_chen}时

【多标的类象映射】
{chr(10).join(stocks_desc)}

【一课多断原则（核心）】
同一个课（天地盘+四课+三传固定），对不同标的通过不同的"类神"来分析：
1. 先确定每个标的的类神（妻财/父母/官鬼/兄弟/子孙）
2. 看该类神在四课中的位置（加临何位、何将乘之）
3. 看该类神在三传中的出现（初/中/末传、旺衰、空亡）
4. 看该类神与日干的生克关系（类神生干吉、类神克干凶）
5. 看标的对应的地支在课传中的刑冲合害

【六亲股市映射】
- 妻财爻 → 资金/利润（旺相=涨，休囚=跌，空亡=虚涨虚跌）
- 父母爻 → 大盘/政策（旺相=利好，克财=政策打压）
- 官鬼爻 → 风险/主力（旺相=机构拉升，克干=风险释放）
- 兄弟爻 → 板块联动（旺相=跟涨，克财=轮动出逃）
- 子孙爻 → 成交量/散户（旺相=放量，空亡=缩量）

【输出格式】
纯JSON：
{{
  "predictions": [
    {{
      "symbol": "600519",
      "name": "贵州茅台",
      "trend": "涨/跌/平/先涨后跌/先跌后涨",
      "jixiong": "吉/凶/中平",
      "confidence": 0.0-1.0,
      "analysis": "基于类神分析..."
    }}
  ],
  "summary": "整体市场判断"
}}
"""
    return prompt


# ═══════════════════════════════════════════════════════════
# 3. 排盘逻辑（复用现有逻辑）
# ═══════════════════════════════════════════════════════════

def get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def get_rizhu(target_date):
    """计算日柱"""
    ref = date(1984, 1, 31)
    tian_gan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    di_zhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    days = (target_date - ref).days
    return tian_gan[days % 10] + di_zhi[days % 12]

def get_yuejiang(target_date):
    """计算月将（精确口径：中气换将，与 engine/yuejiang_engine 权威一致）

    2026-08-17 清理：原固定公历日期表（1/20 子、2/19 亥…）在节气时刻浮动年份
    会错 1 天，改为 YueJiangCalculator.get_yuejiang_by_date（sxtwl 精确中气）。
    """
    try:
        from engine.yuejiang_engine import YueJiangCalculator
        yj, _name = YueJiangCalculator().get_yuejiang_by_date(
            target_date.year, target_date.month, target_date.day)
        return yj
    except Exception:
        # 降级：固定日期近似表（仅当精确引擎不可用）
        rules = [(1,20,'子'),(2,19,'亥'),(3,21,'戌'),(4,20,'酉'),
                 (5,21,'申'),(6,21,'未'),(7,23,'午'),(8,23,'巳'),
                 (9,23,'辰'),(10,23,'卯'),(11,22,'寅'),(12,22,'丑')]
        m, d = target_date.month, target_date.day
        for mm, dd, yj in reversed(rules):
            if (m > mm) or (m == mm and d >= dd):
                return yj
        return rules[-1][2]

def _paipan_v2(rizhu, yuejiang, shichen):
    """权威 V2 排盘（SiKeSanChuanCalculator2，与古例/天机起课同源）

    2026-08-17 清理：替换旧 DaLiuRenEngine（其 fa_san_chuan 在反吟/涉害/遥克等
    场景与 V2 不一致，780 组合对比 62 处三传差异；四课全一致）。输出结构保持
    与旧引擎相同的文本格式，仅内容修正。
    返回: (paipan_text, rizhu, shichen)
    """
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    engine = SiKeSanChuanCalculator2()
    r = engine.calculate(rizhu[0], rizhu[1], yuejiang, shichen)
    sc = r['sanchuan']
    sanchuan_result = {
        '课体': sc.get('课体', ''),
        '三传': [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')],
        '起法': sc.get('起法', ''),
    }
    tianpan = r['tiandi_pan']
    sike = [{'name': n, 'top': s, 'bottom': x} for n, s, x, _ in r['sike']]
    paipan_text = f"""天地盘: {json.dumps(tianpan, ensure_ascii=False)}
四课: {json.dumps(sike, ensure_ascii=False)}
三传: {json.dumps(sanchuan_result, ensure_ascii=False)}"""
    return paipan_text, rizhu, shichen

def get_shichen(hour):
    """时辰计算"""
    sc_map = {23:'子',0:'子',1:'丑',3:'寅',5:'卯',7:'辰',9:'巳',
              11:'午',13:'未',15:'申',17:'酉',19:'戌',21:'亥'}
    for h in range(23, -1, -2):
        if hour >= h:
            return sc_map.get(h, '子')
    return '子'

def quick_paipan():
    """独立排盘（不依赖stock_daily_predict）

    占时采用真太阳时校正后的当前时辰（与 stock_daily_predict.py 一致）。
    任何想要"正时"占课的调用都应走此函数。
    """
    now = get_beijing_now()
    rizhu = get_rizhu(now.date())
    yuejiang = get_yuejiang(now.date())

    # ── 真太阳时校正（与 stock_daily_predict.py 对齐）──
    try:
        from engine.solar_time import get_true_solar_time
        from stock_daily_predict import USER_PROVINCE, USER_COUNTY
        solar = get_true_solar_time(USER_PROVINCE, USER_COUNTY, now)
        shichen = solar["shi_chen"]
        shi_chen_source = "真太阳时校正"
    except Exception as e:
        # 降级：真太阳时计算失败时退回北京时间
        shichen = get_shichen(now.hour)
        shi_chen_source = f"北京时间(降级:{e})"

    try:
        paipan_text, rizhu, shichen = _paipan_v2(rizhu, yuejiang, shichen)
        paipan_text = f"""日柱: {rizhu}  月将: {yuejiang}  占时: {shichen}（{shi_chen_source}）
{paipan_text}"""
        return paipan_text, rizhu, shichen
    except Exception as e:
        return f"排盘异常: {e}\n日柱={rizhu} 月将={yuejiang} 占时={shichen}", rizhu, shichen


# ═══════════════════════════════════════════════════════════
# 4. 主预测流程
# ═══════════════════════════════════════════════════════════

def predict_multi_stocks(symbols=None, day_gan=None, stock_info_map=None):
    """一课多断：预测多个标的

    Args:
        symbols: 股票代码列表，None则使用硬编码字典
        day_gan: 日干（如'甲'），用于自动映射六亲
        stock_info_map: 股票信息映射 {code: {name, industry, ...}}，用于自动映射

    Returns:
        list: 预测结果列表
    """
    if symbols is None:
        symbols = list(STOCK_LEIXIANG.keys())

    # 构建股票信息字典（硬编码 + 自动映射）
    stocks = {}
    auto_count = 0
    for s in symbols:
        info = get_leixiang_for_stock(
            symbol=s,
            name=(stock_info_map or {}).get(s, {}).get('name', s),
            industry=(stock_info_map or {}).get(s, {}).get('industry'),
            day_gan=day_gan
        )
        stocks[s] = info
        if info.get('auto_mapped'):
            auto_count += 1

    if not stocks:
        print("❌ 无有效标的")
        return []

    print("=" * 60)
    print("  一课多断：个股类象分析系统")
    print("=" * 60)
    print(f"  标的数量: {len(stocks)} (硬编码:{len(stocks)-auto_count} 自动映射:{auto_count})")
    for sym, info in stocks.items():
        tag = "🤖" if info.get('auto_mapped') else "📖"
        print(f"    {tag} {sym} {info['name']} — {info.get('wuxing','?')}行/{info['liuqin']}爻/{info['tianjiang']}")

    # 起一课
    print("\n  起课中...")
    paipan_text, rizhu, shichen = quick_paipan()
    print(f"  日柱={rizhu} 占时={shichen}")

    # 确定日干用于六亲推断
    if day_gan is None:
        day_gan = rizhu[0]
    print(f"  日干={day_gan} 用于六亲推断")

    # 构建Prompt
    prompt = build_multi_stock_prompt(paipan_text, rizhu, shichen, stocks)

    # 调用API
    print(f"\n  调用DeepSeek API分析 {len(stocks)} 个标的...")
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "你是精通大六壬一课多断的专家。输出纯JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 3000,
                "temperature": 0.3,
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
            },
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"  ❌ API错误: {resp.status_code} {resp.text[:200]}")
            return []

        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ❌ API异常: {e}")
        return []

    # 解析结果
    try:
        j0 = content.find("{")
        j1 = content.rfind("}") + 1
        result = json.loads(content[j0:j1])
    except:
        print(f"  ❌ JSON解析失败，原始输出:\n{content[:500]}")
        return []

    # 显示结果
    predictions = result.get("predictions", [])
    print(f"\n{'=' * 60}")
    print(f"  📊 一课多断预测结果")
    print(f"{'=' * 60}")
    print(f"  {rizhu}日 {shichen}时课")
    print()
    for p in predictions:
        sym = p.get("symbol", "?")
        name = p.get("name", "?")
        trend = p.get("trend", "?")
        jx = p.get("jixiong", "?")
        conf = p.get("confidence", 0)
        analysis = p.get("analysis", "")[:100]

        bar = "█" * int(conf * 20)
        print(f"  {name}({sym})")
        print(f"    趋势: {trend} | 吉凶: {jx} | 置信度: {conf:.0%} {bar}")
        print(f"    分析: {analysis}")
        print()

    if result.get("summary"):
        print(f"  整体判断: {result['summary']}")

    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(MEMORY, f"multi_stock_{timestamp}.json")
    os.makedirs(MEMORY, exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": get_beijing_now().strftime("%Y-%m-%d"),
            "rizhu": rizhu,
            "shichen": shichen,
            "day_gan": day_gan,
            "predictions": predictions,
            "paipan": paipan_text[:500],
            "auto_mapped_count": auto_count,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n  已保存: {save_path}")
    return predictions


def add_custom_stock(symbol, name, shen, liuqin, tianjiang):
    """添加自定义标的"""
    STOCK_LEIXIANG[symbol] = {
        "name": name,
        "market": market,
        "shen": shen,
        "dizhi": symbol[-1],  # 用代码尾数
        "liuqin": liuqin,
        "tianjiang": tianjiang,
        "category": "custom",
    }
    print(f"✅ 已添加: {symbol} {name} (十二神={shen}, 类神={liuqin})")


# ═══════════════════════════════════════════════════════════

def predict_multi_stocks_from_list(codes, names=None, shichen=None, rizhu=None, day_gan=None):
    """从股票列表进行一课多断预测（供审核管理器调用）

    Args:
        codes: 股票代码列表
        names: 股票名称列表（可选）
        shichen: 指定占时（时辰），如"午时"
        rizhu: 指定日柱，如"辛卯"
        day_gan: 指定日干（默认从rizhu取）

    Returns:
        dict: {predictions, rizhu, shichen, keti, sanchuan, sike}
    """
    if not codes:
        return {"predictions": [], "rizhu": rizhu or "", "shichen": shichen or ""}

    names = names or []
    stock_info_map = {}
    for i, code in enumerate(codes):
        name = names[i] if i < len(names) else code
        stock_info_map[code] = {"name": name}

    # 起课（自定义课式：审核指定日柱/时辰 → 今日精确月将 + V2 权威引擎排盘；未指定 → quick_paipan 当前课）
    if shichen and rizhu:
        from engine.yuejiang_engine import YueJiangCalculator
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        from engine.gui_ren_engine import GuiRenCalculator

        try:
            yuejiang_calc = YueJiangCalculator()
            from datetime import date as ddate
            today = ddate.today()
            yj, yj_name = yuejiang_calc.get_yuejiang_by_date(today.year, today.month, today.day)

            ri_gan = rizhu[0] if rizhu else "甲"
            ri_zhi = rizhu[1] if len(rizhu) > 1 else "子"

            # V2 权威排盘（与 /api/zeri/analyze 同引擎；月将=今日精确月将，时辰=审核指定）
            engine = SiKeSanChuanCalculator2()
            tdp = engine.get_tiandi_pan(yj, shichen)
            sike = engine.qi_sike(ri_gan, ri_zhi, tdp)
            raw = engine.fa_sanchuan(sike, ri_gan, ri_zhi, tdp)
            sc3 = [raw.get('初传', ''), raw.get('中传', ''), raw.get('末传', '')]

            # 天将（贵人加临顺逆，完整排布）
            tj_map = {}
            try:
                gc = GuiRenCalculator()
                tj_result = gc.arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shichen)
                tj_map = tj_result.get('天将映射', {}) or {}
            except Exception:
                tj_map = {}
            SHORT = {'贵人': '贵', '螣蛇': '蛇', '朱雀': '雀', '六合': '合', '勾陈': '勾', '青龙': '龙',
                     '天空': '空', '白虎': '虎', '太常': '常', '玄武': '玄', '太阴': '阴', '天后': '后'}
            tj3 = [SHORT.get(tj_map.get(s, ''), tj_map.get(s, '') or '?') for s in sc3]

            sike_str = " ".join(f"{k[1]} {k[2]}" for k in sike[:4] if len(k) >= 3)
            sanchuan_str = "".join(sc3)
            tianjiang_str = "".join(tj3)
            keti_str = raw.get('课体', '')

            paipan_text = f"""
日柱: {rizhu}
占时: {shichen}
月将: {yj_name}
四课: {sike_str}
三传: {sanchuan_str}
天将: {tianjiang_str}
课体: {keti_str}
""".strip()

        except Exception as e:
            print(f"  ⚠️ 自定义排盘失败: {e}，使用快速排盘")
            paipan_text, rizhu, shichen = quick_paipan()
            sike_str = ""
            sanchuan_str = ""
            keti_str = ""
    else:
        paipan_text, rizhu, shichen = quick_paipan()
        sike_str = ""
        sanchuan_str = ""
        keti_str = ""

    if day_gan is None and rizhu:
        day_gan = rizhu[0]

    # 构建股票信息
    stocks = {}
    for s in codes:
        info = get_leixiang_for_stock(
            symbol=s,
            name=stock_info_map.get(s, {}).get('name', s),
            industry=stock_info_map.get(s, {}).get('industry'),
            day_gan=day_gan
        )
        stocks[s] = info

    if not stocks:
        return {"predictions": [], "rizhu": rizhu, "shichen": shichen}

    # 构建Prompt
    prompt = build_multi_stock_prompt(paipan_text, rizhu, shichen, stocks)

    # 调用API
    predictions = []
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "你是精通大六壬一课多断的专家。输出纯JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 3000,
                "temperature": 0.3,
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
            },
            timeout=120,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            j0 = content.find("{")
            j1 = content.rfind("}") + 1
            result = json.loads(content[j0:j1])
            predictions = result.get("predictions", [])

            for p in predictions:
                code = p.get("symbol", p.get("code", ""))
                p["code"] = code
                if not p.get("name") and code in stock_info_map:
                    p["name"] = stock_info_map[code].get("name", code)

    except Exception as e:
        print(f"  ❌ API异常: {e}")

    return {
        "predictions": predictions,
        "rizhu": rizhu,
        "shichen": shichen,
        "sike": sike_str,
        "sanchuan": sanchuan_str,
        "keti": keti_str,
        "paipan_text": paipan_text,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="一课多断个股预测")
    parser.add_argument("--symbol", type=str, nargs="+", help="指定股票代码")
    parser.add_argument("--add", nargs=5, metavar=("CODE","NAME","SHEN","LIUQIN","TIANJIANG"),
                       help="添加自定义标的")
    parser.add_argument("--list", action="store_true", help="列出所有已配置标的")
    args = parser.parse_args()

    if args.list:
        print("=" * 50)
        print("  已配置标的")
        print("=" * 50)
        for sym, info in STOCK_LEIXIANG.items():
            print(f"  {sym:<8} {info['name']:<10} {info.get('shen','?'):<10} {info['liuqin']}爻 {info['tianjiang']}")
        return

    if args.add:
        add_custom_stock(*args.add)
        return

    predict_multi_stocks(args.symbol)


if __name__ == "__main__":
    main()
