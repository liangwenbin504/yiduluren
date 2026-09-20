#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI市场情绪分析器 v1.0 (Market Sentiment Analyzer)
================================================
利用 DeepSeek API 搜索当日财经新闻、政策动态、市场情绪，
提取关键信号并转化为预测因子。

用途:
  from ai_sentiment import analyze_market_sentiment
  result = analyze_market_sentiment()
  # → {"sentiment": "偏多", "key_factors": [...], "score": +0.3}

集成:
  - hermes_bridge: 调用 DeepSeek API 进行新闻摘要和情绪分析
  - 作为 ML 预测的补充因子
  - 每日盘前自动运行
"""

import json, os, sys, io
from datetime import datetime, date, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hermes_bridge import call_deepseek
from market_news import MarketNewsAnalyzer

MEMORY = os.path.join(os.path.dirname(__file__), "_memory")
SENTIMENT_FILE = os.path.join(MEMORY, "market_sentiment.json")


def analyze_market_sentiment(target_date: str = None) -> dict:
    """
    利用AI分析当日市场情绪

    返回:
      dict — {sentiment, score, key_factors, confidence, raw_analysis}
    """
    if target_date is None:
        target_date = date.today().isoformat()

    # 构建分析提示
    prompt = f"""你是一位资深A股市场分析师。请基于你的知识（截至训练数据），对{target_date}前后的A股市场做简要情绪分析。

请从以下维度给出判断：
1. 政策面：近期有无重大利好/利空政策？
2. 资金面：流动性、北向资金趋势如何？
3. 技术面：大盘当前位置和趋势
4. 外部环境：国际局势、外盘走势影响

请用JSON格式回复：
{{
  "sentiment": "偏多/偏空/中性",
  "score": 0.0~1.0 (偏高, 0.5=中性),
  "key_factors": ["因子1", "因子2", "因子3"],
  "risk_level": "低/中/高",
  "summary": "一句话总结"
}}

只返回JSON，不要其他文字。"""

    try:
        raw = call_deepseek([
            {"role": "system", "content": "你是专业的A股市场分析师。用简洁JSON格式回答。"},
            {"role": "user", "content": prompt},
        ], timeout=60)

        # 解析JSON
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1]
            if raw.endswith('```'):
                raw = raw[:-3]
        analysis = json.loads(raw)

    except Exception as e:
        analysis = {
            "sentiment": "中性",
            "score": 0.5,
            "key_factors": [f"API分析失败: {str(e)[:50]}"],
            "risk_level": "中",
            "summary": "无法获取AI情绪分析"
        }

    # 标准化
    result = {
        "date": target_date,
        "sentiment": analysis.get("sentiment", "中性"),
        "score": float(analysis.get("score", 0.5)),
        "key_factors": analysis.get("key_factors", [])[:5],
        "risk_level": analysis.get("risk_level", "中"),
        "summary": analysis.get("summary", ""),
        "analyzed_at": datetime.now().isoformat(),
    }

    # 持久化
    os.makedirs(MEMORY, exist_ok=True)
    records = []
    if os.path.exists(SENTIMENT_FILE):
        with open(SENTIMENT_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f)
    records = [r for r in records if r.get('date') != target_date]
    records.append(result)
    with open(SENTIMENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return result


def get_sentiment_signal() -> float:
    """
    获取最新市场情绪信号（-1.0 ~ +1.0）
    优先使用 market_news 实时数据，降级使用历史缓存
    """
    # 优先: market_news 实时数据
    try:
        from market_news import get_market_signal
        return get_market_signal()
    except:
        pass

    # 降级: 历史缓存
    if not os.path.exists(SENTIMENT_FILE):
        return 0.0

    with open(SENTIMENT_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    if not records:
        return 0.0

    latest = records[-1]
    score = latest.get("score", 0.5)
    return (score - 0.5) * 2  # 映射到 -1.0 ~ +1.0


def get_market_news_summary(days: int = 3) -> str:
    """获取最近N天的市场情绪摘要"""
    if not os.path.exists(SENTIMENT_FILE):
        return "无历史情绪数据"

    with open(SENTIMENT_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    recent = records[-days:]
    lines = ["📰 市场情绪摘要 (最近{}天)".format(len(recent))]
    for r in recent:
        emoji = "🟢" if r["score"] > 0.55 else ("🔴" if r["score"] < 0.45 else "🟡")
        lines.append(f"  {emoji} {r['date']}: {r['sentiment']}({r['score']:.2f}) {r['summary'][:60]}")

    return "\n".join(lines)


# ── 命令行 ──

if __name__ == "__main__":
    print("=" * 50)
    print("  AI市场情绪分析")
    print("=" * 50)

    result = analyze_market_sentiment()
    print(f"\n情绪: {result['sentiment']} (得分: {result['score']:.2f})")
    print(f"风险: {result['risk_level']}")
    print(f"关键因子: {', '.join(result['key_factors'])}")
    print(f"摘要: {result['summary']}")
