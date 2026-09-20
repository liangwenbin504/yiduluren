#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融市场新闻采集与情绪分析器 v2.0
================================
多重数据源 + AI情绪提炼 → 量化市场信号

数据源:
  1. stock_hot_rank_em    — 东方财富热门板块（实时）
  2. stock_hot_keyword_em — 热门关键词
  3. stock_hot_search_baidu — 百度热搜
  4. stock_research_report_em — 券商研报
  5. stock_hot_up_em      — 涨幅居前个股
  6. index_news_sentiment_scope — 指数情绪

AI分析:
  - DeepSeek 提炼关键主题 + 多空判断
  - 输出量化信号 (-1.0 ~ +1.0)

用法:
  from market_news import MarketNewsAnalyzer
  mna = MarketNewsAnalyzer()
  signal = mna.get_signal()  # 综合市场情绪信号
  print(mna.report())        # 完整分析报告
"""

import json, os, sys, io, time
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
CACHE_FILE = MEMORY / "market_news_cache.json"

# 缓存有效期（分钟）
CACHE_TTL_MINUTES = 30


def _get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def _load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"updated": "", "data": {}}


def _save_cache(data):
    os.makedirs(MEMORY, exist_ok=True)
    tmp = str(CACHE_FILE) + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, str(CACHE_FILE))


class MarketNewsAnalyzer:
    """市场新闻采集与情绪分析器"""

    def __init__(self):
        self.cache = _load_cache()
        self.data = {}
        self._fresh = False

    def _is_cache_fresh(self) -> bool:
        updated = self.cache.get("updated", "")
        if not updated:
            return False
        try:
            t = datetime.fromisoformat(updated)
            return (_get_beijing_now() - t).total_seconds() < CACHE_TTL_MINUTES * 60
        except:
            return False

    # ═══════════════════════════════════════════
    # 数据采集
    # ═══════════════════════════════════════════

    def fetch_hot_rank(self) -> list:
        """获取东方财富热门板块排行"""
        try:
            import akshare as ak
            df = ak.stock_hot_rank_em()
            items = []
            for _, row in df.head(10).iterrows():
                rank = row.get('当前排名', '')
                name = row.get('股票名称', '')
                price = row.get('最新价', 0)
                chg = row.get('涨跌幅', 0)
                if rank and name:
                    items.append({
                        'rank': int(rank) if str(rank).isdigit() else 0,
                        'name': str(name),
                        'price': float(price) if price else 0,
                        'change_pct': float(chg) if chg else 0,
                    })
            return items
        except Exception as e:
            return [{"error": str(e)[:60]}]

    def fetch_hot_keywords(self) -> list:
        """获取热门关键词"""
        try:
            import akshare as ak
            df = ak.stock_hot_keyword_em()
            if df is not None and len(df) > 0:
                cols = df.columns.tolist()
                # 取前10
                keywords = []
                for _, row in df.head(10).iterrows():
                    kw = {}
                    for c in cols[:3]:
                        val = row.get(c, '')
                        if val and str(val) != 'nan':
                            kw[c] = str(val)
                    if kw:
                        keywords.append(kw)
                return keywords
        except:
            pass
        return []

    def fetch_hot_stocks(self) -> list:
        """获取涨幅居前个股"""
        try:
            import akshare as ak
            df = ak.stock_hot_up_em()
            items = []
            for _, row in df.head(8).iterrows():
                items.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('股票名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)),
                })
            return items
        except:
            return []

    def fetch_research_reports(self) -> list:
        """获取券商研报摘要"""
        try:
            import akshare as ak
            df = ak.stock_research_report_em()
            if df is not None and len(df) > 0:
                items = []
                for _, row in df.head(5).iterrows():
                    items.append({
                        'title': str(row.get('研究报告名称', ''))[:80],
                        'org': str(row.get('研究机构', '')),
                        'rating': str(row.get('评级', '')),
                    })
                return items
        except:
            return []

    def fetch_index_sentiment(self) -> dict:
        """获取指数新闻情绪"""
        try:
            import akshare as ak
            df = ak.index_news_sentiment_scope()
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                return {
                    'scope': float(latest.get('情感数值', 0)),
                    'date': str(latest.get('日期', '')),
                }
        except:
            pass
        return {}

    def collect_all(self, force: bool = False) -> dict:
        """采集全部数据源"""
        if not force and self._is_cache_fresh():
            self.data = self.cache.get("data", {})
            return self.data

        print("  📰 采集市场新闻数据...", flush=True)

        self.data = {
            "collected_at": _get_beijing_now().isoformat(),
            "hot_rank": self.fetch_hot_rank(),
            "hot_keywords": self.fetch_hot_keywords(),
            "hot_stocks": self.fetch_hot_stocks(),
            "research_reports": self.fetch_research_reports(),
            "index_sentiment": self.fetch_index_sentiment(),
        }

        self.cache = {"updated": _get_beijing_now().isoformat(), "data": self.data}
        _save_cache(self.cache)

        sources = sum(1 for k, v in self.data.items()
                      if isinstance(v, list) and len(v) > 0 and not (len(v) == 1 and 'error' in v[0]))
        print(f"  ✅ 采集完成: {sources} 个数据源有数据", flush=True)
        return self.data

    # ═══════════════════════════════════════════
    # AI情绪分析
    # ═══════════════════════════════════════════

    def analyze_sentiment(self, use_ai: bool = True) -> dict:
        """综合分析市场情绪，返回量化信号"""
        self.collect_all()

        # 统计信号
        signals = {}

        # 1. 热门板块涨跌比
        hot = self.data.get("hot_rank", [])
        if hot:
            up_count = sum(1 for h in hot if h.get('change_pct', 0) > 0)
            signals["hot_up_ratio"] = up_count / max(len(hot), 1)
        else:
            signals["hot_up_ratio"] = 0.5

        # 2. 涨幅股涨跌比
        stocks = self.data.get("hot_stocks", [])
        if stocks:
            avg_chg = sum(s.get('change_pct', 0) for s in stocks) / max(len(stocks), 1)
            signals["hot_stock_avg_chg"] = avg_chg
        else:
            signals["hot_stock_avg_chg"] = 0

        # 3. 指数情绪
        sent = self.data.get("index_sentiment", {})
        scope = sent.get("scope", 0)
        signals["index_sentiment_scope"] = scope

        # 4. AI综合分析
        ai_score = 0.5
        ai_summary = ""
        if use_ai:
            try:
                ai_score, ai_summary = self._ai_analyze()
            except:
                pass
        signals["ai_score"] = ai_score

        # 综合信号 (-1.0 ~ +1.0)
        composite = (
            (signals["hot_up_ratio"] - 0.5) * 0.3 +
            min(max(signals["hot_stock_avg_chg"] / 10, -0.5), 0.5) * 0.2 +
            (scope / 100) * 0.2 +
            (ai_score - 0.5) * 0.3
        )
        composite = max(-1.0, min(1.0, composite))

        return {
            "date": _get_beijing_now().strftime("%Y-%m-%d"),
            "signals": signals,
            "composite": round(composite, 4),
            "sentiment": "偏多" if composite > 0.15 else ("偏空" if composite < -0.15 else "中性"),
            "ai_summary": ai_summary,
            "data_sources": {
                "hot_rank": len(hot),
                "hot_keywords": len(self.data.get("hot_keywords", [])),
                "hot_stocks": len(stocks),
                "reports": len(self.data.get("research_reports", [])),
            }
        }

    def _ai_analyze(self) -> tuple:
        """使用DeepSeek AI分析新闻摘要"""
        hot = self.data.get("hot_rank", [])
        reports = self.data.get("research_reports", [])

        if not hot and not reports:
            return 0.5, ""

        # 构建AI分析提示
        hot_summary = "\n".join([
            f"  {h.get('rank','')}. {h.get('name','')} ({h.get('change_pct',0):+.1f}%)"
            for h in hot[:8] if h.get('name')
        ])

        report_summary = "\n".join([
            f"  {r.get('org','')}: {r.get('title','')[:50]} [{r.get('rating','')}]"
            for r in reports[:5]
        ])

        prompt = f"""根据今日A股热门板块和研报，判断市场情绪（偏多/偏空/中性）。

热门板块:
{hot_summary}

券商研报:
{report_summary}

请返回JSON:
{{"sentiment": "偏多/偏空/中性", "score": 0.0~1.0, "reason": "一句话理由"}}"""

        try:
            from hermes_bridge import call_deepseek
            raw = call_deepseek([
                {"role": "system", "content": "你是A股市场分析师，只返回JSON。"},
                {"role": "user", "content": prompt},
            ], timeout=45)

            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(raw)
            return float(result.get("score", 0.5)), result.get("reason", "")
        except:
            return 0.5, ""

    # ═══════════════════════════════════════════
    # 输出
    # ═══════════════════════════════════════════

    def get_signal(self) -> float:
        """快速获取综合情绪信号 (-1.0 ~ +1.0)"""
        result = self.analyze_sentiment(use_ai=True)
        return result["composite"]

    def report(self) -> str:
        """生成完整报告"""
        result = self.analyze_sentiment(use_ai=True)
        sig = result["composite"]
        emoji = "🟢" if sig > 0.15 else ("🔴" if sig < -0.15 else "🟡")

        lines = ["=" * 60]
        lines.append(f"  📰 市场新闻情绪分析 — {result['date']}")
        lines.append("=" * 60)
        lines.append(f"\n  {emoji} 综合信号: {sig:+.3f} ({result['sentiment']})")

        ds = result["data_sources"]
        lines.append(f"\n  数据源: 热门板块{ds['hot_rank']}个 | 关键词{ds['hot_keywords']}个 | "
                     f"涨幅股{ds['hot_stocks']}个 | 研报{ds['reports']}篇")

        if result.get("ai_summary"):
            lines.append(f"\n  🤖 AI分析: {result['ai_summary']}")

        hot = self.data.get("hot_rank", [])[:5]
        if hot:
            lines.append(f"\n  🔥 热门板块TOP5:")
            for h in hot:
                color = "🔴" if h.get('change_pct', 0) < 0 else "🟢"
                lines.append(f"    {color} {h.get('name','')} ({h.get('change_pct',0):+.1f}%)")

        return "\n".join(lines)


# ── 便捷函数 ──

def get_market_signal() -> float:
    """快速获取市场情绪信号"""
    return MarketNewsAnalyzer().get_signal()


def get_market_report() -> str:
    """获取市场情绪报告"""
    return MarketNewsAnalyzer().report()


# ── 命令行 ──

if __name__ == "__main__":
    mna = MarketNewsAnalyzer()
    mna.collect_all(force=True)
    print(mna.report())
