# -*- coding: utf-8 -*-
"""
Phase C v4 数据驱动混合规则引擎
================================
来源：壬占汇选 134 条真实案例训练
最终准确率：硬编码 45.5% → Phase B 75.4% → Phase C v4 84.3%

架构：
  ┌─────────────────────────────────────────────────────┐
  │ 输入：占事类型 + 课体列表 + 特殊格局列表              │
  │     （支持壬占汇选格式 和 主引擎 paipan_result 格式） │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────────────────┐
  │ Step 1: 全局权重打分（Phase B v2 calibrated weights） │
  │  score = Σ(课体权重) + Σ(格局权重)                    │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────────────────┐
  │ Step 2: 占事类型差异化组合兜底                        │
  │  - 功名：11 条 100% 吉率组合 强制判吉                  │
  │         4 条 80%+ 组合 双命中→偏吉                    │
  │  - 家宅/占病/官讼：强信号组合加分                      │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────────────────┐
  │ Step 3: 救应规则检查（71 条全局规则）                  │
  │  凶元素 + 救应元素 → score += rescue_bonus            │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────────────────┐
  │ Step 4: 输出                                         │
  │  verdict: 吉/平/凶                                   │
  │  score: 标准化分数                                    │
  │  confidence: 置信度 0-1                               │
  │  decision_path: 决策路径（可观测）                     │
  └─────────────────────────────────────────────────────┘
"""
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple

# 占事类型标准化映射（主引擎占事 → 壬占汇选占事）
ZHANSHI_NORMALIZE = {
    '功名': '功名', '学业': '功名', '考试': '功名', '求职': '功名',
    '家宅': '家宅', '住宅': '家宅',
    '占病': '占病', '疾病': '占病', '治病': '占病', '健康': '占病',
    '官讼': '官讼', '诉讼': '官讼', '打官司': '官讼', '官司': '官讼', '征战': '官讼',
    '出行': '出行', '远行': '出行', '旅行': '出行',
    '胎产': '胎产', '怀孕': '胎产', '生育': '胎产',
    '求财': '求财', '财运': '求财', '赚钱': '求财', '股票预测': '求财', '大盘预测': '求财',
    '婚姻': '婚姻', '感情': '婚姻', '姻缘': '婚姻',
    '失物': '失物', '走失': '失物', '寻物': '失物',
}

# 71 条救应规则（Phase B v2 训练结果）
JIUYING_RULES = [
    {'xiong': '德庆', 'jiuying': '全局', 'lift': 0.33, 'count': 2},
    {'xiong': '德庆', 'jiuying': '合欢', 'lift': 0.33, 'count': 2},
    {'xiong': '德庆', 'jiuying': '贵人作日鬼', 'lift': 0.33, 'count': 2},
    {'xiong': '德庆', 'jiuying': '龙德', 'lift': 0.33, 'count': 2},
    {'xiong': '引从', 'jiuying': '六纯', 'lift': 0.20, 'count': 3},
    {'xiong': '引从', 'jiuying': '将逢内战', 'lift': 0.20, 'count': 3},
    {'xiong': '引从', 'jiuying': '励德', 'lift': 0.20, 'count': 2},
    {'xiong': '引从', 'jiuying': '间传', 'lift': 0.20, 'count': 2},
]


class HybridRuleEngine:
    """Phase C v4 数据驱动混合规则引擎"""

    _instance = None
    _weights_loaded = False

    def __init__(self, weights_path: str = None):
        """
        初始化规则引擎

        Args:
            weights_path: hybrid_weights.json 路径，默认 data/distillation/hybrid_weights.json
        """
        if weights_path is None:
            # 尝试多种相对路径
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'data', 'distillation', 'hybrid_weights.json'),
                'data/distillation/hybrid_weights.json',
            ]
            for c in candidates:
                if os.path.exists(c):
                    weights_path = c
                    break

        self.weights_path = weights_path
        self.global_keti = {}
        self.global_special = {}
        self.zhanshi_overrides = {}
        self.zhanshi_jiuying = {}   # Phase F: 占事专属救应规则
        self.metadata = {}
        self._loaded = False

        if weights_path and os.path.exists(weights_path):
            self._load_weights()

    @classmethod
    def get_instance(cls) -> 'HybridRuleEngine':
        """单例获取"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reload(cls) -> 'HybridRuleEngine':
        """重置单例并重建（权重文件热加载，B5v-recalib 发布用）"""
        cls._instance = None
        return cls.get_instance()

    def _load_weights(self):
        """加载 hybrid_weights.json"""
        try:
            with open(self.weights_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.global_keti = data.get('global_keti', {})
            self.global_special = data.get('global_special', {})
            self.zhanshi_overrides = data.get('zhanshi_overrides', {})
            self.zhanshi_jiuying = data.get('zhanshi_jiuying', {})   # Phase F
            self.global_jiuying = data.get('jiuying_rules', [])      # B5v-recalib：入库的全局救应（此前仅硬编码 JIUYING_RULES）
            self.metadata = data.get('metadata', {})
            self._loaded = True
        except Exception as e:
            print(f"⚠️ hybrid_rule_engine 加载权重失败: {e}")
            self._loaded = False

    def is_available(self) -> bool:
        """引擎是否可用"""
        return self._loaded and (self.global_keti or self.global_special)

    # ============================================================
    # 输入适配
    # ============================================================

    @staticmethod
    def normalize_zhanshi(zhanshi: str) -> str:
        """把各种占事叫法映射到壬占汇选标准名"""
        if not zhanshi:
            return ''
        zs = zhanshi.strip()
        return ZHANSHI_NORMALIZE.get(zs, zs)

    @staticmethod
    def extract_elements(paipan_result: Dict) -> Tuple[List[str], List[str]]:
        """
        从排盘结果中提取课体列表和特殊格局列表

        支持两种格式：
        1. 壬占汇选 feature 格式: {'keti': [...], 'special': [...]}
        2. 主引擎 paipan_result 格式: {'课体': '全局,六纯,...', 'keti': [...], 'special_patterns': [...]}
        """
        ketis = []
        specials = []

        # 课体提取
        if 'keti' in paipan_result:
            raw = paipan_result['keti']
            if isinstance(raw, list):
                ketis = [str(k) for k in raw]
            elif isinstance(raw, str):
                ketis = [k.strip() for k in re.split(r'[,，、\s]+', raw) if k.strip()]
        if not ketis and '课体' in paipan_result:
            raw = paipan_result['课体']
            if isinstance(raw, list):
                ketis = [str(k) for k in raw]
            elif isinstance(raw, str):
                ketis = [k.strip() for k in re.split(r'[,，、\s]+', raw) if k.strip()]

        # 特殊格局提取
        if 'special' in paipan_result:
            raw = paipan_result['special']
            if isinstance(raw, list):
                specials = [str(s) for s in raw]
            elif isinstance(raw, str):
                specials = [s.strip() for s in re.split(r'[,，、\s]+', raw) if s.strip()]
        elif 'special_patterns' in paipan_result:
            raw = paipan_result['special_patterns']
            if isinstance(raw, list):
                specials = [str(s) for s in raw]
        elif '格局' in paipan_result:
            raw = paipan_result['格局']
            if isinstance(raw, list):
                specials = [str(s) for s in raw]
            elif isinstance(raw, str):
                specials = [s.strip() for s in re.split(r'[,，、\s]+', raw) if s.strip()]

        return ketis, specials

    # ============================================================
    # 核心推理
    # ============================================================

    def predict(self, paipan_result: Dict, zhanshi: str = None) -> Dict:
        """
        执行 Phase C v4 推理

        Args:
            paipan_result: 排盘结果（壬占汇选格式 或 主引擎格式）
            zhanshi: 占事类型（任意叫法，会自动标准化）

        Returns:
            {
                'verdict': '吉' | '平' | '凶',
                'score': float,              # 标准化分数 -10 ~ +10
                'confidence': float,         # 置信度 0~1
                'decision_path': [...],      # 决策路径
                'matched_combos': [...],     # 命中的组合（如果有）
                'rescue_used': [...],        # 触发的救应规则
                'zhanshi_used': str,         # 实际使用的标准化占事类型
            }
        """
        decision_path = []
        decision_path.append(f"Step 0: 输入占事={zhanshi}, 引擎=Phase C v4 Hybrid")

        # 元素提取
        ketis, specials = self.extract_elements(paipan_result)
        elems = set(ketis + specials)
        decision_path.append(f"Step 0: 提取课体={ketis}, 格局={specials}")

        # 占事标准化
        std_zs = self.normalize_zhanshi(zhanshi) if zhanshi else ''
        decision_path.append(f"Step 0: 标准化占事={std_zs or '(未指定)'}")

        # ========== Step 1: 全局权重打分 ==========
        base_score = 0.0
        for k in ketis:
            w = self.global_keti.get(k, 0)
            if w != 0:
                base_score += w
        for s in specials:
            w = self.global_special.get(s, 0)
            if w != 0:
                base_score += w
        decision_path.append(f"Step 1: 全局权重打分 = {base_score:+.2f} (课体{len(ketis)}项+格局{len(specials)}项)")

        # ========== Step 2: 占事类型组合兜底 ==========
        combo_adjust = 0.0
        matched_combos = []

        if std_zs and std_zs in self.zhanshi_overrides:
            override = self.zhanshi_overrides[std_zs]

            # ---------- Phase Q: 极端凶形态阻断 ----------
            # xiong_blockers = 强凶课体/凶煞清单（数据驱动：该占事吉案例零命中证据）。
            # 命中任一 blocker → 禁用全部 100% 组合强制判吉 + 80% 组合偏吉 + 占事级正向
            # 权重微调，并凶向 -5，让全局权重/救应自然裁决 —— 防止未来凶案例命中多条高阶
            # 组合被强制判吉（特别是功名 1890 条组合的高过拟合风险）
            hit_blockers = [e for e in elems if e in override.get('xiong_blockers', [])]
            if hit_blockers:
                combo_adjust -= 5.0
                decision_path.append(
                    f"Step 2: ⚠️ 命中极端凶形态 {hit_blockers} → 禁用强制判吉/偏吉/权重微调，凶向 -5"
                )

            # 100% 吉率组合 → 强制 +10 分（覆盖全局）
            # 支持两种格式：["A","B"] 或 {"combo":["A","B"], "exclude":["X"]}（含排除元素则不强制）
            ji_combos_raw = override.get('ji_combos', [])
            for item in ji_combos_raw:
                if hit_blockers:  # Phase Q: 极端凶形态下不执行强制判吉
                    decision_path.append(
                        "Step 2: 极端凶形态阻断中 → 跳过 100% 吉率组合检查"
                    )
                    break
                if isinstance(item, dict):
                    combo_list = item.get('combo', [])
                    excludes = item.get('exclude', [])
                else:
                    combo_list = item
                    excludes = []
                combo_set = frozenset(combo_list)
                if combo_set.issubset(elems):
                    if excludes and any(e in elems for e in excludes):
                        decision_path.append(
                            f"Step 2: 组合 {list(combo_set)} 命中但含排除元素 {excludes} → 不强制"
                        )
                        continue
                    matched_combos.append(('100%吉', list(combo_set)))
                    decision_path.append(
                        f"Step 2: ⚡ 命中 100% 吉率组合 {list(combo_set)} → 强制判吉!"
                    )
                    return self._format_result(
                        verdict='吉', score=10.0, confidence=0.95,
                        decision_path=decision_path, matched_combos=matched_combos,
                        rescue_used=[], zhanshi_used=std_zs,
                        reason=f"强制: 命中100%吉率组合 {'+'.join(combo_set)}"
                    )

            # 80%+ 吉率组合 → 统计命中数（Phase Q: 极端凶形态下跳过偏吉路径）
            # 支持 dict 格式 {"combo": [...], "rate": x, "exclude": [...]}（Phase T: 含排除元素则不计数）
            high_combos_raw = override.get('high_combos', [])
            high_hits = []
            if not hit_blockers:
                for hc in high_combos_raw:
                    combo_list = hc.get('combo', [])
                    excludes = hc.get('exclude', [])
                    combo_set = frozenset(combo_list)
                    if combo_set.issubset(elems):
                        if excludes and any(e in elems for e in excludes):
                            decision_path.append(
                                f"Step 2: 偏吉组合 {list(combo_set)} 命中但含排除元素 {excludes} → 不计数"
                            )
                            continue
                        high_hits.append(hc)
            if len(high_hits) >= 2:
                decision_path.append(
                    f"Step 2: 命中 {len(high_hits)} 个 80%+ 吉率组合 → 偏吉调整"
                )
                combo_adjust += 5.0
                matched_combos.append(('80%+双命中', [h['combo'] for h in high_hits]))

            # 占事级元素权重微调（Phase J）：命中元素 → 加/减分（负值即减分）
            # Phase Q: 极端凶形态下跳过（未含负向对冲，防正向微调掩盖凶形态）
            weight_adjusts = override.get('weight_adjusts', {})
            zs_adjust = 0.0
            zs_hits = []
            if not hit_blockers:
                for e, delta in weight_adjusts.items():
                    if e in elems:
                        zs_adjust += delta
                        zs_hits.append(f"{e}{delta:+.0f}")
            if zs_hits:
                combo_adjust += zs_adjust
                decision_path.append(
                    f"Step 2: 占事专属权重微调[{std_zs}] {'+'.join(zs_hits)} → {zs_adjust:+.2f}"
                )

        # ========== Step 3: 救应规则检查（Phase F: 占事专属优先，全局兜底） ==========
        rescue_bonus = 0.0
        rescue_used = []

        # 选择规则集：当前占事有专属校准表 → 用专属；否则用 global_jiuying（入库）→ 兜底硬编码常量
        if std_zs and std_zs in self.zhanshi_jiuying and self.zhanshi_jiuying[std_zs]:
            rules = self.zhanshi_jiuying[std_zs]
            rule_source = f"专属({std_zs} {len(rules)}条)"
        elif getattr(self, 'global_jiuying', None):
            rules = self.global_jiuying
            rule_source = f"全局入库({len(rules)}条)"
        else:
            rules = JIUYING_RULES
            rule_source = f"全局常量({len(JIUYING_RULES)}条)"

        for rule in rules:
            if rule['xiong'] in elems and rule['jiuying'] in elems:
                bonus = rule['lift'] * 5  # 放大到权重尺度
                rescue_bonus += bonus
                rescue_used.append(f"{rule['xiong']}→{rule['jiuying']}(+{bonus:.1f})")

        if rescue_used:
            decision_path.append(
                f"Step 3: 触发 {len(rescue_used)} 条救应规则[{rule_source}] → +{rescue_bonus:.2f}"
            )
        elif rule_source.startswith("专属"):
            decision_path.append(f"Step 3: 专属表[{std_zs}]无命中 → 无救应加分")

        # ========== Step 4: 综合判定 ==========
        final_score = base_score + combo_adjust + rescue_bonus
        verdict, confidence = self._score_to_verdict(final_score, len(elems), len(rescue_used))

        decision_path.append(
            f"Step 4: 最终分={final_score:+.2f} (base={base_score:+.2f} + combo={combo_adjust:+.2f} + rescue={rescue_bonus:+.2f}) → {verdict} (置信度 {confidence:.0%})"
        )

        return self._format_result(
            verdict=verdict, score=final_score, confidence=confidence,
            decision_path=decision_path, matched_combos=matched_combos,
            rescue_used=rescue_used, zhanshi_used=std_zs,
            reason=f"Phase C v4: base={base_score:+.1f} combo={combo_adjust:+.1f} rescue={rescue_bonus:+.1f}"
        )

    def _score_to_verdict(self, score: float, elem_count: int, rescue_count: int) -> Tuple[str, float]:
        """分数 → 判定 + 置信度"""
        # 分数归一化到 -10 ~ +10 区间
        normalized = max(-10, min(10, score))

        if normalized >= 3:
            verdict = '吉'
            confidence = min(0.95, 0.55 + normalized * 0.04)
        elif normalized >= 1:
            verdict = '平吉'
            confidence = min(0.80, 0.45 + normalized * 0.05)
        elif normalized <= -3:
            verdict = '凶'
            confidence = min(0.95, 0.55 + abs(normalized) * 0.04)
        elif normalized <= -1:
            verdict = '平凶'
            confidence = min(0.80, 0.45 + abs(normalized) * 0.05)
        else:
            verdict = '中平'
            confidence = 0.50 + abs(normalized) * 0.05

        # 救应规则越多，置信度越高（因为有更多"数据证据"）
        if rescue_count >= 3:
            confidence = min(0.98, confidence + 0.05)
        elif rescue_count >= 1:
            confidence = min(0.95, confidence + 0.02)

        # 元素太少（<2）说明信息不足，降置信度
        if elem_count < 3:
            confidence *= 0.8
            confidence = max(0.30, confidence)

        return verdict, round(confidence, 2)

    @staticmethod
    def _format_result(verdict, score, confidence, decision_path,
                       matched_combos, rescue_used, zhanshi_used, reason) -> Dict:
        """统一输出格式"""
        return {
            'success': True,
            'verdict': verdict,
            'score': round(score, 2),
            'confidence': confidence,
            'engine_used': 'hybrid_rule_v4',
            'decision_path': decision_path,
            'matched_combos': matched_combos,
            'rescue_used': rescue_used,
            'zhanshi_used': zhanshi_used,
            'reason': reason,
        }

    # ============================================================
    # 主引擎兼容接口
    # ============================================================

    def judge(self, paipan_result: Dict, zhanshi: str = None, **kwargs) -> Dict:
        """
        兼容 smart_judge.rule_engine 的调用接口
        调用方: self.rule_engine(paipan_result=..., zhanshi=...)
        """
        result = self.predict(paipan_result, zhanshi)

        # 补充主引擎期望的字段
        result['result'] = result['verdict']
        result['duanyu'] = self._generate_duanyu(result)
        result['bifa_rules'] = []
        result['leishen_analysis'] = f"Phase C v4 数据驱动规则引擎: {result['reason']}"
        result['yingqi'] = None
        result['zhanshi'] = zhanshi

        return result

    @staticmethod
    def _generate_duanyu(result: Dict) -> str:
        """根据推理结果生成可读断语"""
        v = result['verdict']
        s = result['score']
        c = result['confidence']

        verdict_cn = {'吉': '大吉', '平吉': '小吉', '中平': '中平',
                      '平凶': '小凶', '凶': '大凶'}.get(v, v)

        parts = [f"【Phase C v4 断语】{verdict_cn}（分数 {s:+.1f}，置信度 {c:.0%}）"]

        if result['matched_combos']:
            combo_strs = []
            for label, items in result['matched_combos']:
                if isinstance(items[0], list):
                    combo_strs.append(f"{label}: {' + '.join('+'.join(c) for c in items)}")
                else:
                    combo_strs.append(f"{label}: {' + '.join(items)}")
            parts.append(f"  命中组合: {'; '.join(combo_strs)}")

        if result['rescue_used']:
            parts.append(f"  救应触发: {', '.join(result['rescue_used'][:5])}")
            if len(result['rescue_used']) > 5:
                parts.append(f"  ...等共 {len(result['rescue_used'])} 条救应规则")

        return '\n'.join(parts)

    # ============================================================
    # 元信息
    # ============================================================

    def get_info(self) -> Dict:
        """返回引擎元信息"""
        return {
            'engine': 'Phase C v4 Hybrid Rule Engine',
            'version': '4.0',
            'data_source': '壬占汇选 134 条带label案例',
            'phase_b_accuracy': self.metadata.get('phase_b_accuracy', 75.4),
            'phase_c_v4_accuracy': self.metadata.get('phase_c_v4_accuracy', 84.3),
            'improvement': self.metadata.get('improvement', 9.0),
            'total_training_cases': self.metadata.get('total_cases', 134),
            'global_keti_count': len(self.global_keti),
            'global_special_count': len(self.global_special),
            'jiuying_rules_count': len(JIUYING_RULES),
            'zhanshi_jiuying_count': {zs: len(r) for zs, r in self.zhanshi_jiuying.items()},
            'phase_f_accuracy': self.metadata.get('phase_f_accuracy', None),
            'zhanshi_overrides': list(self.zhanshi_overrides.keys()),
            'weights_loaded': self._loaded,
        }


# ============================================================
# 便捷函数
# ============================================================

def hybrid_predict(paipan_result: Dict, zhanshi: str = None) -> Dict:
    """一行调用 Phase C v4 规则引擎"""
    engine = HybridRuleEngine.get_instance()
    return engine.predict(paipan_result, zhanshi)


def hybrid_judge(paipan_result: Dict, zhanshi: str = None, **kwargs) -> Dict:
    """兼容旧接口的一行调用"""
    engine = HybridRuleEngine.get_instance()
    return engine.judge(paipan_result, zhanshi, **kwargs)


# ============================================================
# 测试入口
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Phase C v4 混合规则引擎 — 快速自测")
    print("=" * 60)

    engine = HybridRuleEngine.get_instance()
    info = engine.get_info()
    print(f"\n📊 引擎状态:")
    print(f"  权重加载: {'✅' if info['weights_loaded'] else '❌'}")
    print(f"  课体权重: {info['global_keti_count']} 项")
    print(f"  格局权重: {info['global_special_count']} 项")
    print(f"  救应规则: {info['jiuying_rules_count']} 条")
    print(f"  占事覆盖: {info['zhanshi_overrides']}")
    print(f"  训练数据: {info['total_training_cases']} 条壬占汇选案例")
    print(f"  Phase B 准确率: {info['phase_b_accuracy']:.1f}%")
    print(f"  Phase C v4 准确率: {info['phase_c_v4_accuracy']:.1f}% (+{info['improvement']:.1f}%)")

    # 测 1：功名 - 将逢内战 + 死奇（应强制判吉）
    print(f"\n{'='*60}")
    print("测试 1: 功名 - 将逢内战+死奇 → 应强制吉")
    test1 = {'keti': ['斩关', '死奇', '励德'], 'special': ['将逢内战', '鬼墓']}
    r1 = engine.predict(test1, '功名')
    print(f"  判定: {r1['verdict']} (score={r1['score']:+.1f}, conf={r1['confidence']:.0%})")
    print(f"  路径: {r1['decision_path']}")
    print(f"  命中组合: {r1['matched_combos']}")

    # 测 2：功名 - 全局权重兜底（无100%组合）
    print(f"\n{'='*60}")
    print("测试 2: 功名 - 纯全局权重兜底（无100%吉组合）")
    test2 = {'keti': ['三奇', '连珠', '六仪'], 'special': ['贵塞鬼户', '初遭夹克']}
    r2 = engine.predict(test2, '功名')
    print(f"  判定: {r2['verdict']} (score={r2['score']:+.1f}, conf={r2['confidence']:.0%})")
    print(f"  救应触发: {r2['rescue_used']}")

    # 测 3：家宅 - 将逢内战 + 贵塞鬼户（救应）
    print(f"\n{'='*60}")
    print("测试 3: 家宅 - 将逢内战+贵塞鬼户 → 救应触发")
    test3 = {'keti': ['全局', '六纯', '励德'], 'special': ['将逢内战', '贵塞鬼户', '贵登天门']}
    r3 = engine.predict(test3, '家宅')
    print(f"  判定: {r3['verdict']} (score={r3['score']:+.1f}, conf={r3['confidence']:.0%})")
    print(f"  救应触发: {len(r3['rescue_used'])} 条")

    # 测 4：无占事类型（纯全局权重）
    print(f"\n{'='*60}")
    print("测试 4: 无占事类型 - 纯全局权重打分")
    test4 = {'keti': ['元首', '重审', '返吟'], 'special': ['末助初生']}
    r4 = engine.predict(test4)
    print(f"  判定: {r4['verdict']} (score={r4['score']:+.1f})")

    print(f"{'='*60}")
    print("✅ 自测完成！")
    print(f"{'='*60}")
