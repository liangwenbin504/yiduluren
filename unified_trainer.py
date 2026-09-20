#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一训练库加载器 — 整合全部自进化训练数据
==========================================
加载所有训练数据源，为预测引擎提供统一的修正查询接口。

数据源:
  1. stock_training_insights.json  — 分类权重 + 因子影响力
  2. human_corrections.json        — 12条人工纠正规则
  3. self_evolve_state.json        — 15条自进化规则
  4. pattern_accuracy_stats.json   — 天将/课体/三传历史准确率
  5. liuren_case_kb.json           — 675古案例匹配
  6. evolution_summary.json        — 5轮3903条进化训练总结
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"


def _tianjiang_name(x: str) -> str:
    """提取纯天将名：'辰(六合)' → '六合'；'六合' → '六合'。

    历史预测记录里三传天将存在两种写法（带地支前缀 / 纯名），
    评分前必须统一，否则位置校验会失效。
    """
    import re as _re
    m = _re.search(r'\((.+)\)', x or '')
    return m.group(1).strip() if m else (x or '').strip()


class UnifiedTrainer:
    """统一训练库，加载全部自进化数据，提供预测修正接口"""

    def __init__(self):
        self.insights = None         # 股票训练洞察
        self.corrections = None      # 人工纠正规则
        self.evolve_state = None     # 自进化状态
        self.pattern_stats = None    # 模式准确率统计
        self.case_kb = None          # 古案例知识库
        self.evolution_summary = None  # 进化训练总结
        self.loaded = False

    def load_all(self):
        """加载全部训练数据"""
        self.insights = self._load_json(MEMORY / "stock_training_insights.json")
        self.corrections = self._load_json(MEMORY / "human_corrections.json")
        self.evolve_state = self._load_json(MEMORY / "self_evolve_state.json")
        self.pattern_stats = self._load_json(MEMORY / "pattern_accuracy_stats.json")
        self.case_kb = self._load_json(MEMORY / "liuren_case_kb.json")
        self.evolution_summary = self._load_json(
            BASE / "processed_data" / "evolution_20260425_115647" / "evolution_summary.json"
        )
        self.loaded = True
        return self

    def _load_json(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ── 修正接口 ──

    def get_category_weight(self, category: str) -> float:
        """获取分类准确率权重 (0~1)，用于调整置信度"""
        if not self.insights:
            return 0.5
        weights = self.insights.get("category_weights", {})
        return weights.get(category, 0.5)

    def get_factor_impacts(self, sanchuan_list: List[str], tianjiang_list: List[str],
                           jixiong: str, trend: str) -> Tuple[int, List[str]]:
        """根据因子影响力计算修正分和理由"""
        score = 0
        reasons = []
        if not self.insights:
            return 0, reasons

        impacts = self.insights.get("factor_impact", {})

        # 三传五行
        wx_map = {
            '寅': '木', '卯': '木', '巳': '火', '午': '火',
            '申': '金', '酉': '金', '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土',
        }
        for z in sanchuan_list:
            wx = wx_map.get(z, '')
            if wx:
                key = f"sanchuan_{wx}"
                imp = impacts.get(key, 0)
                if abs(imp) > 0.05:
                    score += int(imp * 10)
                    reasons.append(f'三传含{wx}(影响力{imp:+.2f})')

        # 天将龙德
        if '青龙' in tianjiang_list:
            imp = impacts.get('tianjiang_has_longde', 0)
            if abs(imp) > 0.05:
                score += int(imp * 10)
                reasons.append(f'天将含青龙(影响力{imp:+.2f})')

        # 吉凶
        jx_key = f"jixiong_{jixiong}" if jixiong else ''
        imp = impacts.get(jx_key, 0)
        if abs(imp) > 0.05:
            score += int(imp * 10)
            reasons.append(f'吉凶{jixiong}(影响力{imp:+.2f})')

        # 趋势
        trend_key = f"trend_{trend}" if trend else ''
        imp = impacts.get(trend_key, 0)
        if abs(imp) > 0.05:
            score += int(imp * 10)
            reasons.append(f'趋势{trend}(影响力{imp:+.2f})')

        return score, reasons

    # ── 知识点特征影响（多维建模核心）──
    def get_knowledge_feature_impact(self, kf: Dict) -> Tuple[int, List[str]]:
        """
        消费 knowledge_features 的多维特征，产出修正分与理由。
        优先级：若 insights.factor_impact 中已学得该关系/维度的权重（key 形如
        rel_干上神_发用_比和 / yong_wangshuai_休 / bifa_交车相合 …），用学得权重；
        否则用领域默认 signed 值。这样训练系统「学到」的新维度会逐步覆盖默认值。
        """
        score = 0
        reasons = []
        if not kf or not isinstance(kf, dict):
            return 0, reasons
        impacts = self.insights.get("factor_impact", {}) if self.insights else {}

        # 1) 四组关系（含干上/支上/日干/支 与 发用、交车）
        for name, info in kf.get("relations", {}).items():
            rel_name = info.get("relation", "")
            signed = info.get("signed", 0.0)
            learned = impacts.get(f"rel_{name}_{rel_name}")
            if learned is not None and abs(learned) > 0.05:
                score += int(learned * 10)
                reasons.append(f"[{name}={rel_name}]学得影响{learned:+.2f}")
            elif signed:
                score += int(signed * 3)
                reasons.append(f"[{name}={rel_name}]{signed:+.1f}")

        # 2) 理气
        liqi = kf.get("liqi", {})
        wf = liqi.get("用神旺衰分", 0.0)
        wgrade = liqi.get("用神旺衰", "")
        wl = impacts.get(f"yong_wangshuai_{wgrade}") if wgrade else None
        if wl is not None and abs(wl) > 0.05:
            score += int(wl * 10)
            reasons.append(f"[用神旺衰{wgrade}]学得{wl:+.2f}")
        elif wf:
            score += int(wf * 3)
            reasons.append(f"[用神旺衰{wgrade}]{wf:+.1f}")
        kc = liqi.get("空亡数", 0)
        if kc:
            wk = impacts.get("kongwang") if impacts else None
            if wk is not None and abs(wk) > 0.05:
                score += int(wk * 10) * kc
                reasons.append(f"[空亡{kc}传·学得{wk:+.2f}]")
            else:
                score -= kc * 2
                reasons.append(f"[空亡{kc}传]-{kc * 2}")
        qf = liqi.get("气之流转", "")
        if "进气" in qf:
            score += 1
            reasons.append("[气之流转·进气]+1")
        elif "退气" in qf:
            score -= 1
            reasons.append("[气之流转·退气]-1")

        # 3) 类象
        lx = kf.get("leixiang", {})
        gang_net = lx.get("刚柔净额", 0)
        wg = impacts.get("gangrou") if impacts else None
        if gang_net != 0 and wg is not None and abs(wg) > 0.05:
            applied = int(wg * 10) * (1 if gang_net > 0 else -1)
            score += applied
            reasons.append(f"[{'柔神主导' if gang_net > 0 else '刚煞主导'}·学得{wg:+.2f}]{applied:+d}")
        elif gang_net > 0:
            score += gang_net
            reasons.append(f"[柔神主导]+{gang_net}")
        elif gang_net < 0:
            score += gang_net
            reasons.append(f"[刚煞主导]{gang_net}")
        ji = lx.get("吉神数", 0)
        xiong = lx.get("凶煞数", 0)
        if ji:
            score += min(ji, 3)
            reasons.append(f"[吉神{ji}]+{min(ji, 3)}")
        if xiong:
            score -= min(xiong, 3)
            reasons.append(f"[凶煞{xiong}]-{min(xiong, 3)}")

        # 4) 毕法赋（由关系/空亡推导）
        bf = kf.get("bifa", {})
        wb = impacts.get("bifa_jiaoche") if impacts else None
        jiaoche = bf.get("交车", [])
        if jiaoche and wb is not None and abs(wb) > 0.05:
            he = sum(1 for x in jiaoche if "合" in x)
            ke = sum(1 for x in jiaoche if ("克" in x or "刑" in x or "冲" in x))
            net = he - ke
            if net != 0:
                applied = int(wb * 10) * (1 if net > 0 else -1)
                score += applied
                reasons.append(f"[毕法·交车·学得{wb:+.2f}]{applied:+d}")
        else:
            for jc in jiaoche:
                if "合" in jc:
                    score += 2
                    reasons.append(f"[毕法·{jc}]+2")
                elif "克" in jc:
                    score -= 2
                    reasons.append(f"[毕法·{jc}]-2")
                elif "刑" in jc:
                    score -= 1
                    reasons.append(f"[毕法·{jc}]-1")
                elif "冲" in jc:
                    score -= 1
                    reasons.append(f"[毕法·{jc}]-1")
        if bf.get("用神空"):
            score -= 2
            reasons.append("[毕法·用神空]-2")

        # 5) 三传结构（进茹/退茹）
        sc = kf.get("sanchuan", {})
        cb = sc.get("传变", "")
        wc = impacts.get("chuanbian") if impacts else None
        if cb == "进茹(气进)":
            if wc is not None and abs(wc) > 0.05:
                score += int(wc * 10)
                reasons.append(f"[三传进茹·学得{wc:+.2f}]")
            else:
                score += 1
                reasons.append("[三传进茹]+1")
        elif cb == "退茹(气退)":
            if wc is not None and abs(wc) > 0.05:
                score -= int(wc * 10)
                reasons.append(f"[三传退茹·学得{wc:+.2f}]")
            else:
                score -= 1
                reasons.append("[三传退茹]-1")

        return score, reasons

    def apply_corrections_legacy(self, keti: str, sanchuan: List[str],
                                 tianjiang: List[str], rizhu: str) -> Tuple[int, List[str]]:
        """【已废弃·仅作回退与A/B对照】旧版关键词智能匹配实现。

        2026-09-10 实测缺陷（合成600课 + 历史真实课例 A/B，见 _ab_corrections.py）：
          · #2/#3/#4/#5/#8/#10 命中率 100%（600/600）—— 只要规则文本含关键词即计分，
            与课体/三传/日干支完全无关，实质是"常数偏移"伪装成规则命中
          · #6 与 #9 同象（六合）各计 +2 → 重复计分
          · #1 白虎不校验"乘财+日干旺"即给看涨分
          · #8 系前端三传渲染规则(applied_to=stock_dashboard.html)，被误当评分规则
          · #10 原文系"否定"滥用刑冲，实现却照扣 -1，方向与本意相反
        保留此函数仅供 `CORRECTIONS_STRICT=0` 回退与对照，新逻辑见 apply_corrections。
        """

        MAX_CORRECTION = 5  # 总纠正分上限
        score = 0
        reasons = []
        if not self.corrections:
            return 0, reasons

        rules = self.corrections.get("rules", [])
        for rule in rules:
            mistake = rule.get("mistake", "")
            correct = rule.get("correct_rule", "")
            rule_id = rule.get("id", "?")
            sc_str = ' '.join(sanchuan) if sanchuan else ''
            tj_str = ' '.join(tianjiang) if tianjiang else ''
            matched = False  # 本规则是否已匹配

            # 天将相关 — 任意天将出现在规则中且匹配三传天将
            tianjiang_names = ['贵人','青龙','六合','太常','天后','太阴','朱雀','螣蛇','勾陈','白虎','天空','玄武']
            for tj_name in tianjiang_names:
                if tj_name in mistake and tj_name in tj_str:
                    score += 2
                    reasons.append(f'[人工纠正#{rule_id}] 天将{tj_name}规则激活(+2)')
                    matched = True
                    break

            if matched:
                continue  # 天将已匹配，跳过后续检查防止重复加分

            # 铸印/破模课格
            if ('铸印' in mistake or '破模' in mistake) and ('铸印' in keti or '破模' in keti):
                score -= 3
                reasons.append(f'[人工纠正#{rule_id}] 铸印破模=大跌(-3)')
                continue

            # 末传+空亡+青龙=有惊无险
            if '末传' in mistake and '青龙' in mistake and len(tianjiang) >= 3:
                if tianjiang[2] == '青龙':
                    score += 3
                    reasons.append(f'[人工纠正#{rule_id}] 末传青龙=有惊无险(+3)')
                    continue

            # 神煞相关 (喜神/天德/月德/天喜/天赦)
            for sha in ['喜神','天德','月德','天喜','天赦','驿马','禄神','文昌','解神','福星']:
                if sha in mistake and sha in correct:
                    score += 1
                    reasons.append(f'[人工纠正#{rule_id}] 神煞{sha}规则(+1)')
                    matched = True
                    break

            if matched:
                continue

            # 太阳/月将/墓相关
            if '太阳' in mistake and '墓' in mistake:
                score += 1
                reasons.append(f'[人工纠正#{rule_id}] 太阳照墓规则(+1)')
                continue

            # 身强相关
            if '身强' in mistake:
                score += 1
                reasons.append(f'[人工纠正#{rule_id}] 身强判断规则(参考)')
                continue

            # 旬空/踏空
            if '旬空' in mistake or '踏空' in mistake:
                score -= 1
                reasons.append(f'[人工纠正#{rule_id}] 旬空踏空规则(-1)')
                continue

            # 刑冲相关
            if '刑' in mistake and '冲' in mistake:
                score -= 1
                reasons.append(f'[人工纠正#{rule_id}] 刑冲规则(-1)')
                continue

            # 末传+青龙+空=有惊无险
            if '末传' in mistake and '青龙' in mistake:
                if len(tianjiang) >= 3 and '青龙' in tianjiang[2]:
                    score += 2
                    reasons.append(f'[人工纠正#{rule_id}] 末传青龙(+2)')
                    continue

        # 总纠正分上限约束
        if score > MAX_CORRECTION:
            reasons.append(f'[纠正上限] 总分{score}超过上限+{MAX_CORRECTION}，截断为+{MAX_CORRECTION}')
            score = MAX_CORRECTION
        elif score < -MAX_CORRECTION:
            reasons.append(f'[纠正上限] 总分{score}低于下限-{MAX_CORRECTION}，截断为-{MAX_CORRECTION}')
            score = -MAX_CORRECTION

        return score, reasons

    # ─────────────────────────────────────────────────────────────────
    # 2026-09-10 严格化重写：只对「能从入参严格判定」的规则计分
    # 依据：_memory/human_corrections.json 各条 correct_rule 原文
    #       + OX Alpha(glm-5.3-flash) 独立复核裁决（_memory/ox_alpha_review_261.md）
    #       + A/B 全量对照（_ab_corrections.py，PY3.12 / PYTHONHASHSEED=0）
    # ─────────────────────────────────────────────────────────────────
    BIAS_CORRECTION = 1        # 系统性偏空补偿（详见注释）
    CORRECTION_MAX = 5         # 总纠正分上限（沿用旧制）

    def apply_corrections(self, keti: str, sanchuan: List[str],
                          tianjiang: List[str], rizhu: str) -> Tuple[int, List[str]]:
        """应用人工纠正规则（严格化版 v3）。

        改造原则（2026-09-10）：
          1. 只对能从入参 (keti, sanchuan, tianjiang, rizhu) 严格判定的规则计分；
             无法判定的规则一律**停用并留痕**，不再"文本含关键词即计分"。
          2. 旧实现里 #2/#3/#4/#5/#8/#10 的恒定触发（实测 100% 命中）合并为一条
             显式「系统性偏空校准」——依据 human_corrections.json summary：
             "系统核心偏见: 系统性偏空"，2026-07-21 复盘修正后 47/91 条由空转多。
             净值取 +1（A/B 三档中平均差最小 -0.31，最接近旧行为）。
          3. 同象规则去重：#6 与 #9 同为六合环拱，只由 #6 计一次且须在**末传**。

        回退：设置环境变量 CORRECTIONS_STRICT=0 可切回 apply_corrections_legacy。
        """
        import os as _os
        if _os.getenv('CORRECTIONS_STRICT', '1') == '0':
            return self.apply_corrections_legacy(keti, sanchuan, tianjiang, rizhu)

        score = 0
        reasons: List[str] = []
        if not self.corrections:
            return 0, reasons

        # ① 系统性偏空校准（旧实现中 #2+#3+#4-#5-#8-#10 的净值，显式化）
        if self.BIAS_CORRECTION:
            score += self.BIAS_CORRECTION
            reasons.append(
                f'[偏空校准] 系统性偏空补偿(+{self.BIAS_CORRECTION})  '
                f'依据:2026-07-21复盘summary「系统核心偏见=系统性偏空」')

        # ② 人工纠正#6：末传乘六合 + 生干 = 六合环拱（市场合力推涨）
        #    原文 correct_rule: "末传乘六合+生干=六合环拱→市场合力推涨"
        #    严格校验「末传」位置（旧实现只查三传天将串是否含"六合"，不作位置校验）
        if len(tianjiang) >= 3 and _tianjiang_name(tianjiang[2]) == '六合':
            score += 2
            reasons.append('[人工纠正#6] 末传乘六合=六合环拱(+2)  依据:correct_rule原文')

        # ③ 人工纠正#5：伏吟课带刑冲 = 静极而动（不动变必动，先跌后涨）
        #    原文 correct_rule: "伏吟带刑冲→不动变必动"
        #    严格校验课体为伏吟（旧实现不校验课体，任何课都扣 -1）
        if '伏吟' in (keti or ''):
            score -= 1
            reasons.append('[人工纠正#5] 伏吟带刑冲=不动变必动(先跌)(-1)  依据:correct_rule原文')

        # ── 停用并留痕（无法从现有入参严格判定；旧实现为恒定触发或方向相反）──
        #   #1  白虎/腾蛇：需"乘财 + 日干旺"方可判看涨，入参无财爻/旺衰 → 停用
        #   #2  神煞天喜：需真实神煞命中表，旧实现恒定 +1              → 停用
        #   #3  太阳照墓：需月将与四课，旧实现恒定 +1                   → 停用
        #   #4  身强：原文标注"参考"，且需日干旺衰，旧实现恒定 +1        → 停用
        #   #7  毕法赋全本：属知识库范畴，非评分项                       → 停用
        #   #8  旬空踏空：applied_to=stock_dashboard.html，系前端渲染规则 → 停用
        #   #9  六合环拱：与 #6 同象，已由 #6 覆盖，避免重复计分          → 停用
        #   #10 刑冲：原文系"否定"滥用刑冲，旧实现照扣 -1，方向与本意相反  → 停用
        #   #11 三传合鬼局通关：需合局与通关神判据，入参不足               → 停用
        #   #12 贵神昼夜：需日落时刻，入参不足                            → 停用

        # 总纠正分上限约束（沿用旧制）
        if score > self.CORRECTION_MAX:
            reasons.append(f'[纠正上限] 总分{score}超过上限+{self.CORRECTION_MAX}，截断为+{self.CORRECTION_MAX}')
            score = self.CORRECTION_MAX
        elif score < -self.CORRECTION_MAX:
            reasons.append(f'[纠正上限] 总分{score}低于下限-{self.CORRECTION_MAX}，截断为-{self.CORRECTION_MAX}')
            score = -self.CORRECTION_MAX

        return score, reasons

    def reload(self):
        """重新加载全部训练数据 — 审核后调用此方法刷新"""
        self.__init__()
        return self.load_all()

    def get_summary(self) -> Dict[str, Any]:
        """获取训练库总览，供前端展示"""
        return {
            "insights_accuracy": self.insights.get("overall_accuracy") if self.insights else 0,
            "insights_predictions": self.insights.get("total_predictions") if self.insights else 0,
            "corrections_count": self.corrections.get("total_corrections") if self.corrections else 0,
            "evolve_rounds": self.evolve_state.get("rounds") if self.evolve_state else 0,
            "evolve_rules": self.evolve_state.get("total_rules") if self.evolve_state else 0,
            "case_kb_total": self.case_kb.get("total") if self.case_kb else 0,
            "evolution_cycles": self.evolution_summary.get("总轮次") if self.evolution_summary else 0,
            "evolution_data_size": self.evolution_summary.get("最终训练池大小") if self.evolution_summary else 0,
            "evolution_score": self.evolution_summary.get("最终得分") if self.evolution_summary else 0,
        }


# 单例
_trainer: Optional[UnifiedTrainer] = None


def get_trainer() -> UnifiedTrainer:
    global _trainer
    if _trainer is None:
        _trainer = UnifiedTrainer().load_all()
    return _trainer


def reload_trainer() -> UnifiedTrainer:
    """审核保存后调用，强制刷新训练库，使新纠正立即生效"""
    global _trainer
    _trainer = UnifiedTrainer().load_all()
    return _trainer
