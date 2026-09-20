#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票预测专用规则引擎

核心功能：
1. 基于课体、三传、天将、六亲的规则判断
2. 零成本快速预测（无需调用AI）
3. 可解释的决策过程

规则体系：
1. 课体定大局（主干）
2. 三传定时序（大枝）
3. 六亲+天将（中枝）
4. 神煞/旺衰（细枝）

输出：吉凶判断、趋势预测、置信度、推理链
"""

from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════
# 1. 课体判断规则（主干）
# ═══════════════════════════════════════════════════════════

KETI_STOCK_RULES = {
    # 吉课体 → 看涨
    "元首课": {"score": 0.9, "trend": "涨", "meaning": "趋势延续，市场多头主导"},
    "重审课": {"score": 0.8, "trend": "涨", "meaning": "贵人扶持，上涨延续"},
    "六合课": {"score": 0.85, "trend": "震荡偏涨", "meaning": "和合之象，多空平衡偏多"},
    "三合课": {"score": 0.82, "trend": "涨", "meaning": "三合成局，资金合力推涨"},
    "顺行课": {"score": 0.75, "trend": "震荡上行", "meaning": "顺势而为，上涨通道"},
    "比和课": {"score": 0.7, "trend": "震荡", "meaning": "多空平衡，方向不明"},
    
    # 凶课体 → 看跌
    "涉害课": {"score": 0.25, "trend": "跌", "meaning": "多空博弈激烈，利空主导"},
    "遥克课": {"score": 0.3, "trend": "先跌后涨", "meaning": "突发消息驱动，波动剧烈"},
    "反吟课": {"score": 0.2, "trend": "剧烈反转", "meaning": "趋势反转，方向突变"},
    "伏吟课": {"score": 0.5, "trend": "盘整/震荡", "meaning": "盘整迟滞，方向不明"},
    "弹射课": {"score": 0.35, "trend": "震荡偏跌", "meaning": "上弹下射，方向不定偏空"},
    "昴星课": {"score": 0.15, "trend": "暴跌", "meaning": "凶课之极，风险极大"},
    "闭口课": {"score": 0.4, "trend": "盘整", "meaning": "封闭不通，成交清淡"},
    
    # 中性课体
    "练蛇课": {"score": 0.55, "trend": "震荡", "meaning": "如蛇蜿蜒，方向不明"},
    "周遍课": {"score": 0.5, "trend": "震荡", "meaning": "周而复始，循环往复"},
}


# ═══════════════════════════════════════════════════════════
# 2. 天将动态规则（中枝）
# ═══════════════════════════════════════════════════════════

TIANJIANG_STOCK_RULES = {
    "青龙": {
        "乘财": {"score": 0.9, "trend": "主升浪", "condition": "日干旺"},
        "乘鬼": {"score": 0.3, "trend": "拉高出货", "condition": "身弱"},
        "乘生干": {"score": 0.75, "trend": "反弹", "condition": ""},
    },
    "白虎": {
        "乘财": {"score": 0.85, "trend": "暴发", "condition": "日干旺+德禄"},
        "乘财(身弱)": {"score": 0.2, "trend": "暴跌", "condition": "日干衰"},
        "乘鬼": {"score": 0.15, "trend": "恐慌", "condition": "日干弱"},
    },
    "朱雀": {
        "乘财": {"score": 0.8, "trend": "利好大涨", "condition": "旺"},
        "乘鬼": {"score": 0.25, "trend": "利空恐慌", "condition": ""},
        "乘生干": {"score": 0.7, "trend": "政策暖风", "condition": ""},
    },
    "腾蛇": {
        "乘财": {"score": 0.75, "trend": "洗盘后涨", "condition": ""},
        "乘鬼": {"score": 0.3, "trend": "假突破", "condition": ""},
        "乘空": {"score": 0.45, "trend": "虚惊一场", "condition": ""},
    },
    "玄武": {
        "乘财": {"score": 0.7, "trend": "暗盘流入", "condition": ""},
        "乘鬼": {"score": 0.3, "trend": "主力出货", "condition": ""},
        "乘生干": {"score": 0.65, "trend": "隐形利好", "condition": ""},
    },
    "勾陈": {
        "乘财": {"score": 0.72, "trend": "蓄势待涨", "condition": ""},
        "乘鬼": {"score": 0.4, "trend": "盘整阻力", "condition": ""},
        "乘生干": {"score": 0.6, "trend": "筑底", "condition": ""},
    },
    "贵人": {
        "乘财": {"score": 0.85, "trend": "主力托市", "condition": ""},
        "乘鬼": {"score": 0.45, "trend": "护盘无效", "condition": ""},
        "乘生干": {"score": 0.8, "trend": "国家队入场", "condition": ""},
    },
    "六合": {
        "乘财": {"score": 0.82, "trend": "和合上涨", "condition": ""},
        "乘鬼": {"score": 0.4, "trend": "分歧", "condition": ""},
        "乘生干": {"score": 0.75, "trend": "人气聚拢", "condition": ""},
    },
    "太阴/天后/太常": {
        "乘财": {"score": 0.7, "trend": "稳步上行", "condition": "日干旺"},
        "乘鬼": {"score": 0.35, "trend": "缓跌", "condition": ""},
    },
    "天空": {
        "乘财": {"score": 0.45, "trend": "利好落空", "condition": ""},
        "乘鬼": {"score": 0.4, "trend": "虚跌", "condition": ""},
    },
}


# ═══════════════════════════════════════════════════════════
# 3. 六亲力量规则
# ═══════════════════════════════════════════════════════════

LIUQIN_STOCK_RULES = {
    "妻财": {
        "interpretation": "资金面",
        "stock_meaning": "资金充足/流动性好",
        "strong_signal": "身强能担财 → 涨",
        "weak_signal": "身弱不胜财 → 涨势难继",
    },
    "官鬼": {
        "interpretation": "主力/庄力",
        "stock_meaning": "主力控盘/庄股",
        "strong_signal": "官鬼旺相 → 主力强势控盘",
        "weak_signal": "官鬼休囚 → 主力出货",
    },
    "父母": {
        "interpretation": "政策/消息",
        "stock_meaning": "政策面/基本面",
        "strong_signal": "父母旺相 → 政策利好",
        "weak_signal": "父母休囚 → 政策真空",
    },
    "子孙": {
        "interpretation": "市场情绪",
        "stock_meaning": "散户/游资",
        "strong_signal": "子孙旺相 → 人气旺盛",
        "weak_signal": "子孙休囚 → 情绪低迷",
    },
    "兄弟": {
        "interpretation": "竞争/阻力",
        "stock_meaning": "抛压/阻力位",
        "strong_signal": "兄弟旺相 → 抛压沉重",
        "weak_signal": "兄弟休囚 → 阻力较弱",
    },
}


# ═══════════════════════════════════════════════════════════
# 4. 三传时序规则
# ═══════════════════════════════════════════════════════════

SANCHUAN_STOCK_RULES = {
    "初传": {
        "stock_meaning": "开盘时段趋势",
        "good_signals": ["青龙", "六合", "贵人", "太常", "朱雀"],
        "bad_signals": ["白虎", "玄武", "勾陈", "腾蛇"],
    },
    "中传": {
        "stock_meaning": "盘中时段趋势",
        "good_signals": ["青龙", "六合", "贵人", "太阴"],
        "bad_signals": ["白虎", "玄武", "天空", "勾陈"],
    },
    "末传": {
        "stock_meaning": "尾盘时段趋势",
        "good_signals": ["青龙", "六合", "贵人", "天后", "太常"],
        "bad_signals": ["白虎", "玄武", "天空", "腾蛇"],
    },
}


class StockRuleEngine:
    """股票预测专用规则引擎"""
    
    def __init__(self, realtime_engine=None):
        """
        Args:
            realtime_engine: 实时行情引擎实例（可选）
        """
        self._rule_stats = {
            "total_evaluations": 0,
            "keti_evaluations": 0,
            "tianjiang_evaluations": 0,
            "sanchuan_evaluations": 0,
            "avg_confidence": 0.0,
            "realtime_adjustments": 0,
        }
        self._last_reasoning_chain = []
        self._realtime_engine = realtime_engine
        self._last_realtime_adjustment = None
    
    def set_realtime_engine(self, engine):
        """设置实时行情引擎"""
        self._realtime_engine = engine
    
    def evaluate(self, paipan_data: Dict, stock_wuxing: str = "") -> Dict:
        """综合评估股票预测
        
        Args:
            paipan_data: 排盘数据，包含：
                - keti: 课体名称
                - sanchuan: 三传信息
                - tianjiang: 天将信息
                - liuqin: 六亲信息
                - wuxing: 五行分析
                - day_gan: 日干
                - shen_wangshuai: 身强身弱
            stock_wuxing: 股票行业五行（用于动态调整）
                
        Returns:
            Dict: 评估结果
        """
        self._rule_stats["total_evaluations"] += 1
        
        reasoning_chain = []
        scores = []
        
        # 1. 课体评估（权重0.4）
        keti_score, keti_analysis = self._evaluate_keti(paipan_data)
        scores.append(("课体", keti_score, 0.4))
        reasoning_chain.append(keti_analysis)
        if keti_score > 0:
            self._rule_stats["keti_evaluations"] += 1
        
        # 2. 三传评估（权重0.25）
        sanchuan_score, sanchuan_analysis = self._evaluate_sanchuan(paipan_data)
        scores.append(("三传", sanchuan_score, 0.25))
        reasoning_chain.append(sanchuan_analysis)
        if sanchuan_score > 0:
            self._rule_stats["sanchuan_evaluations"] += 1
        
        # 3. 天将评估（权重0.2）
        tianjiang_score, tianjiang_analysis = self._evaluate_tianjiang(paipan_data)
        scores.append(("天将", tianjiang_score, 0.2))
        reasoning_chain.append(tianjiang_analysis)
        if tianjiang_score > 0:
            self._rule_stats["tianjiang_evaluations"] += 1
        
        # 4. 六亲评估（权重0.15）
        liuqin_score, liuqin_analysis = self._evaluate_liuqin(paipan_data)
        scores.append(("六亲", liuqin_score, 0.15))
        reasoning_chain.append(liuqin_analysis)
        
        # 计算加权总分
        total_score = sum(score * weight for _, score, weight in scores)
        confidence = min(total_score, 0.95)
        
        # 趋势判断
        trend = self._determine_trend(total_score, paipan_data)
        jixiong = self._determine_jixiong(total_score)
        
        # 风险提示
        risk_warnings = self._generate_risk_warnings(paipan_data, total_score)
        
        # 身强调整
        shen_strong = paipan_data.get("shen_wangshuai", "")
        if "身强" in shen_strong:
            total_score = min(total_score * 1.1, 0.95)  # 身强加10%
        elif "身弱" in shen_strong:
            total_score = total_score * 0.9  # 身弱减10%
        
        # 实时行情动态调整（如果有股票五行信息）
        realtime_adjustment = None
        if self._realtime_engine and stock_wuxing:
            try:
                adjustment_result = self._realtime_engine.adjust_prediction(
                    total_score, stock_wuxing
                )
                total_score = adjustment_result["adjusted_score"]
                realtime_adjustment = adjustment_result
                self._rule_stats["realtime_adjustments"] += 1
                reasoning_chain.append(
                    f"📊 实时行情调整: {adjustment_result['adjustment_description']} "
                    f"({adjustment_result['base_score']:.2f}→{total_score:.2f})"
                )
            except Exception:
                pass
        
        self._rule_stats["avg_confidence"] = (
            self._rule_stats["avg_confidence"] * 0.95 + confidence * 0.05
        )
        self._last_reasoning_chain = reasoning_chain
        
        result = {
            "score": round(total_score, 3),
            "confidence": round(confidence, 3),
            "trend": trend,
            "jixiong": jixiong,
            "reasoning_chain": reasoning_chain,
            "detailed_scores": [(name, round(score, 3), weight) for name, score, weight in scores],
            "risk_warnings": risk_warnings,
            "rule_based": True,
            "cost": 0.0,  # 规则引擎零成本
            "response_time_ms": 5,  # 响应时间~5ms
        }
        
        # 添加实时调整信息
        if realtime_adjustment:
            result["realtime_adjustment"] = realtime_adjustment
            result["stock_wuxing"] = stock_wuxing
        
        return result
    
    def _evaluate_keti(self, paipan_data: Dict) -> Tuple[float, str]:
        """评估课体"""
        keti = paipan_data.get("keti", "")
        rule = KETI_STOCK_RULES.get(keti, None)
        
        if rule:
            score = rule["score"]
            analysis = f"课体「{keti}」：{rule['meaning']}，趋势{rule['trend']}，评分{score}"
        else:
            score = 0.5
            analysis = f"课体「{keti}」：未收录，默认中性评分0.5"
        
        return score, analysis
    
    def _evaluate_sanchuan(self, paipan_data: Dict) -> Tuple[float, str]:
        """评估三传"""
        sanchuan = paipan_data.get("sanchuan", {})
        day_gan = paipan_data.get("day_gan", "")
        
        if not sanchuan:
            return 0.5, "三传：无数据，默认中性"
        
        total_score = 0
        details = []
        
        for pos in ["first", "second", "third"]:
            god = sanchuan.get(pos, "")
            rule = SANCHUAN_STOCK_RULES.get(["初传", "中传", "末传"][["first", "second", "third"].index(pos)], {})
            
            good_signals = rule.get("good_signals", [])
            bad_signals = rule.get("bad_signals", [])
            
            pos_score = 0.5
            if any(g in god for g in good_signals):
                pos_score = 0.75
                details.append(f"{pos}传{god}：吉将，加分")
            elif any(g in god for g in bad_signals):
                pos_score = 0.25
                details.append(f"{pos}传{god}：凶将，减分")
            else:
                details.append(f"{pos}传{god}：中性")
            
            total_score += pos_score
        
        avg_score = total_score / 3
        
        analysis = f"三传评估：{'; '.join(details)}，平均评分{avg_score:.2f}"
        return avg_score, analysis
    
    def _evaluate_tianjiang(self, paipan_data: Dict) -> Tuple[float, str]:
        """评估天将"""
        tianjiang = paipan_data.get("tianjiang", "")
        liuqin = paipan_data.get("liuqin", "")
        day_gan = paipan_data.get("day_gan", "")
        shen_strong = paipan_data.get("shen_wangshuai", "")
        
        if not tianjiang:
            return 0.5, "天将：无数据，默认中性"
        
        # 解析天将字符串，如 "白虎+申, 玄武+亥, 勾陈+辰"
        jiang_list = [j.strip() for j in tianjiang.split(",")]
        total_score = 0
        details = []
        
        for jiang_entry in jiang_list:
            parts = jiang_entry.split("+")
            jiang_name = parts[0] if len(parts) > 0 else ""
            shen = parts[1] if len(parts) > 1 else ""
            
            # 查找天将规则
            rule = TIANJIANG_STOCK_RULES.get(jiang_name, None)
            if rule:
                # 根据六亲关系选择规则
                liuqin_type = self._infer_liuqin_for_tianjiang(shen, liuqin, day_gan)
                sub_rule = rule.get(f"乘{liuqin_type}", rule.get("乘财", None))
                
                if sub_rule:
                    score = sub_rule["score"]
                    details.append(f"{jiang_name}乘{shen}：{sub_rule['trend']}，评分{score}")
                else:
                    score = 0.5
                    details.append(f"{jiang_name}乘{shen}：无规则，默认0.5")
            else:
                score = 0.5
                details.append(f"{jiang_name}：未收录，默认0.5")
            
            total_score += score
        
        avg_score = total_score / max(len(jiang_list), 1)
        
        # 身强调整
        if "身强" in shen_strong and avg_score > 0.6:
            avg_score = min(avg_score * 1.05, 0.95)
            details.append("身强加持，加分5%")
        elif "身弱" in shen_strong and avg_score > 0.6:
            avg_score = avg_score * 0.9
            details.append("身弱不胜财，减分10%")
        
        analysis = f"天将评估：{'; '.join(details)}，平均评分{avg_score:.2f}"
        return avg_score, analysis
    
    def _evaluate_liuqin(self, paipan_data: Dict) -> Tuple[float, str]:
        """评估六亲"""
        liuqin = paipan_data.get("liuqin", "")
        
        if not liuqin:
            return 0.5, "六亲：无数据，默认中性"
        
        # 解析六亲信息
        liuqin_analysis = []
        score = 0.5
        
        for lq_type, rule in LIUQIN_STOCK_RULES.items():
            if lq_type in liuqin:
                liuqin_analysis.append(f"{lq_type}：{rule['stock_meaning']}")
        
        # 财旺加分
        if "妻财旺" in liuqin or "妻财" in liuqin and "旺" in liuqin:
            score += 0.15
            liuqin_analysis.append("财旺加分")
        
        # 官鬼旺减分
        if "官鬼旺" in liuqin:
            score -= 0.1
            liuqin_analysis.append("官鬼旺，风险加分")
        
        score = max(0.1, min(score, 0.95))
        
        analysis = f"六亲评估：{'; '.join(liuqin_analysis) if liuqin_analysis else '无特殊信号'}，评分{score:.2f}"
        return score, analysis
    
    def _determine_trend(self, score: float, paipan_data: Dict) -> str:
        """根据评分确定趋势"""
        # 检查特殊情况
        keti = paipan_data.get("keti", "")
        
        # 伏吟课带刑冲 → 反转信号
        if "伏吟" in keti:
            wuxing = paipan_data.get("wuxing", "")
            if "刑" in wuxing or "冲" in wuxing:
                return "反转上涨(伏吟带刑冲)"
        
        # 评分映射趋势
        if score >= 0.8:
            return "大涨"
        elif score >= 0.65:
            return "上涨"
        elif score >= 0.55:
            return "震荡偏涨"
        elif score >= 0.45:
            return "震荡"
        elif score >= 0.35:
            return "震荡偏跌"
        elif score >= 0.2:
            return "下跌"
        else:
            return "大跌"
    
    def _determine_jixiong(self, score: float) -> str:
        """根据评分确定吉凶"""
        if score >= 0.6:
            return "吉"
        elif score >= 0.4:
            return "中平"
        else:
            return "凶"
    
    def _generate_risk_warnings(self, paipan_data: Dict, score: float) -> List[str]:
        """生成风险提示"""
        warnings = []
        
        keti = paipan_data.get("keti", "")
        tianjiang = paipan_data.get("tianjiang", "")
        shen_strong = paipan_data.get("shen_wangshuai", "")
        
        # 课体风险
        if keti in ["昴星课", "反吟课"]:
            warnings.append(f"⚠️ {keti}：高风险课体")
        elif keti in ["涉害课", "遥克课"]:
            warnings.append(f"⚠️ {keti}：波动较大")
        
        # 天将风险
        if "白虎" in tianjiang and "乘鬼" in tianjiang:
            warnings.append("⚠️ 白虎乘鬼：恐慌信号")
        if "天空" in tianjiang:
            warnings.append("⚠️ 天空：虚象，利好可能落空")
        
        # 身弱风险
        if "身弱" in shen_strong and score > 0.5:
            warnings.append("⚠️ 身弱不胜财：涨势难继")
        
        # 综合风险
        if score < 0.3:
            warnings.append("⚠️ 综合评分过低：建议减仓或观望")
        elif score < 0.5:
            warnings.append("⚠️ 综合评分偏低：控制仓位")
        
        return warnings
    
    def _infer_liuqin_for_tianjiang(self, shen: str, liuqin: str, day_gan: str) -> str:
        """推断天将所乘神的六亲关系"""
        # 简化处理：根据六亲字符串推断
        if "财" in liuqin:
            return "财"
        elif "鬼" in liuqin:
            return "鬼"
        elif "生" in liuqin or "父母" in liuqin:
            return "生干"
        else:
            return "财"  # 默认按财处理
    
    def get_stats(self) -> Dict:
        """获取规则引擎统计"""
        return {
            **self._rule_stats,
            "engine_type": "stock_rule_engine",
            "cost_per_call": 0.0,
            "last_reasoning_chain": self._last_reasoning_chain[-3:] if self._last_reasoning_chain else [],
        }
    
    def get_supported_ketis(self) -> List[str]:
        """获取支持的课体列表"""
        return list(KETI_STOCK_RULES.keys())
    
    def get_supported_tianjiangs(self) -> List[str]:
        """获取支持的天将列表"""
        return list(TIANJIANG_STOCK_RULES.keys())
