#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
吉凶评价核心架构 - JixiongEvaluationCore

系统架构设计：
1. 吉凶属性定义层 - 定义吉凶等级和属性
2. 评分算法层 - 统一评分算法
3. 权重配置层 - 可配置权重系统
4. 断语映射层 - 断语与吉凶映射
5. 综合评价层 - 多维度综合评价

基于《仪度六壬选日要诀》等文献的吉凶评价体系
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class JixiongLevel(Enum):
    """吉凶等级枚举"""
    DA_JI = "大吉"      # 90-100分
    SHANG_JI = "上吉"   # 80-89分
    ZHONG_JI = "中吉"   # 70-79分
    XIAO_JI = "小吉"    # 60-69分
    PING = "平"         # 50-59分
    XIAO_XIONG = "小凶"  # 40-49分
    ZHONG_XIONG = "中凶" # 30-39分
    DA_XIONG = "大凶"    # 0-29分


@dataclass
class JixiongAttribute:
    """吉凶属性数据类"""
    level: JixiongLevel
    score_range: Tuple[int, int]
    description: str
    color: str  # 用于UI显示
    recommendation: str  # 建议
    applicable_scenarios: List[str] = field(default_factory=list)


@dataclass
class WeightConfig:
    """权重配置数据类"""
    name: str
    weight: float
    description: str = ""
    min_value: float = 0.0
    max_value: float = 100.0


@dataclass
class EvaluationResult:
    """评价结果数据类"""
    score: float
    level: JixiongLevel
    attribute: JixiongAttribute
    duanyu: str
    detailed_duanyu: Dict[str, str]
    factors: Dict[str, float]
    recommendations: List[str]
    literature_source: str = ""


class JixiongDefinitionLayer:
    """吉凶属性定义层"""
    
    JIXIONG_ATTRIBUTES = {
        JixiongLevel.DA_JI: JixiongAttribute(
            level=JixiongLevel.DA_JI,
            score_range=(90, 100),
            description="大吉大利，诸事皆宜",
            color="#FFD700",
            recommendation="宜速行事，机不可失",
            applicable_scenarios=["安葬", "开业", "上任", "嫁娶", "入宅"]
        ),
        JixiongLevel.SHANG_JI: JixiongAttribute(
            level=JixiongLevel.SHANG_JI,
            score_range=(80, 89),
            description="上吉之课，主贵人扶持",
            color="#FFA500",
            recommendation="宜积极进取，贵人相助",
            applicable_scenarios=["安葬", "开业", "上任", "祈福"]
        ),
        JixiongLevel.ZHONG_JI: JixiongAttribute(
            level=JixiongLevel.ZHONG_JI,
            score_range=(70, 79),
            description="中吉之课，平稳顺利",
            color="#90EE90",
            recommendation="宜稳步推进，循序渐进",
            applicable_scenarios=["祭祀", "祈福", "求嗣"]
        ),
        JixiongLevel.XIAO_JI: JixiongAttribute(
            level=JixiongLevel.XIAO_JI,
            score_range=(60, 69),
            description="小吉之课，略有助力",
            color="#98FB98",
            recommendation="宜谨慎行事，小有收获",
            applicable_scenarios=["日常事务", "小型活动"]
        ),
        JixiongLevel.PING: JixiongAttribute(
            level=JixiongLevel.PING,
            score_range=(50, 59),
            description="平运之课，无功无过",
            color="#D3D3D3",
            recommendation="宜守不宜进，静待时机",
            applicable_scenarios=["日常事务"]
        ),
        JixiongLevel.XIAO_XIONG: JixiongAttribute(
            level=JixiongLevel.XIAO_XIONG,
            score_range=(40, 49),
            description="小凶之课，略有阻碍",
            color="#FFB6C1",
            recommendation="宜谨慎行事，防小人是非",
            applicable_scenarios=["不宜大事"]
        ),
        JixiongLevel.ZHONG_XIONG: JixiongAttribute(
            level=JixiongLevel.ZHONG_XIONG,
            score_range=(30, 39),
            description="中凶之课，多有不利",
            color="#FF6347",
            recommendation="宜暂缓行事，避凶趋吉",
            applicable_scenarios=["不宜行事"]
        ),
        JixiongLevel.DA_XIONG: JixiongAttribute(
            level=JixiongLevel.DA_XIONG,
            score_range=(0, 29),
            description="大凶之课，诸事不宜",
            color="#FF0000",
            recommendation="宜避之，切勿行事",
            applicable_scenarios=["诸事不宜"]
        ),
    }
    
    @classmethod
    def get_attribute_by_score(cls, score: float) -> JixiongAttribute:
        """根据分数获取吉凶属性"""
        for level, attr in cls.JIXIONG_ATTRIBUTES.items():
            if attr.score_range[0] <= score <= attr.score_range[1]:
                return attr
        return cls.JIXIONG_ATTRIBUTES[JixiongLevel.PING]
    
    @classmethod
    def get_level_by_score(cls, score: float) -> JixiongLevel:
        """根据分数获取吉凶等级"""
        attr = cls.get_attribute_by_score(score)
        return attr.level


class WeightConfigLayer:
    """权重配置层"""
    
    DEFAULT_WEIGHTS = {
        '课体课格': WeightConfig(name='课体课格', weight=0.30, description="六壬课体课格评分"),
        '禄马贵人': WeightConfig(name='禄马贵人', weight=0.25, description="禄马贵人到山到向评分"),
        '斗首课格': WeightConfig(name='斗首课格', weight=0.20, description="斗首课格评分"),
        '演禽真法': WeightConfig(name='演禽真法', weight=0.15, description="演禽真法评分"),
        '山向配合': WeightConfig(name='山向配合', weight=0.10, description="山向与日课配合评分"),
    }
    
    def __init__(self, custom_weights: Dict[str, float] = None):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        if custom_weights:
            self.update_weights(custom_weights)
    
    def update_weights(self, new_weights: Dict[str, float]):
        """更新权重配置"""
        for key, value in new_weights.items():
            if key in self.weights:
                self.weights[key].weight = value
        self._validate_weights()
    
    def _validate_weights(self):
        """验证权重总和"""
        total = sum(w.weight for w in self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"权重总和必须为1，当前总和：{total}")
    
    def get_weight(self, name: str) -> float:
        """获取指定权重"""
        return self.weights.get(name, WeightConfig(name="", weight=0)).weight
    
    def get_all_weights(self) -> Dict[str, float]:
        """获取所有权重"""
        return {k: v.weight for k, v in self.weights.items()}


class DuanyuMappingLayer:
    """断语映射层"""
    
    def __init__(self):
        self.expanded_lib = self._load_expanded_library()
    
    def _load_expanded_library(self) -> Dict:
        """加载扩充断语库"""
        lib_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'expanded_duanyu_library.json'
        )
        if os.path.exists(lib_path):
            with open(lib_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def map_keti_to_jixiong(self, keti_name: str) -> Tuple[JixiongLevel, str]:
        """将课体映射到吉凶等级"""
        keti_scores = {
            '龙德课': (JixiongLevel.DA_JI, "最吉，贵人临身"),
            '富贵课': (JixiongLevel.DA_JI, "富贵双全"),
            '官爵课': (JixiongLevel.DA_JI, "官运亨通"),
            '荣华课': (JixiongLevel.SHANG_JI, "荣华富贵"),
            '和美课': (JixiongLevel.SHANG_JI, "家庭和睦"),
            '元首课': (JixiongLevel.XIAO_JI, "事起男子"),
            '重审课': (JixiongLevel.XIAO_JI, "再三审核"),
            '无禄课': (JixiongLevel.XIAO_XIONG, "禄位不保"),
            '天网课': (JixiongLevel.ZHONG_XIONG, "天罗地网"),
            '勾陈课': (JixiongLevel.DA_XIONG, "勾连陈旧"),
        }
        return keti_scores.get(keti_name, (JixiongLevel.PING, "需具体分析"))
    
    def map_luma_to_jixiong(self, luma_type: str, is_arrived: bool) -> Tuple[JixiongLevel, str]:
        """将禄马贵人映射到吉凶等级"""
        if not is_arrived:
            return (JixiongLevel.PING, "未到山向")
        
        luma_scores = {
            '禄神到山': (JixiongLevel.SHANG_JI, "财源广进"),
            '禄神到向': (JixiongLevel.SHANG_JI, "贵人临门"),
            '驿马到山': (JixiongLevel.ZHONG_JI, "迁动有喜"),
            '驿马到向': (JixiongLevel.ZHONG_JI, "出行顺利"),
            '贵人到山': (JixiongLevel.DA_JI, "贵人扶持"),
            '贵人到向': (JixiongLevel.DA_JI, "贵人临门"),
        }
        return luma_scores.get(luma_type, (JixiongLevel.PING, "需具体分析"))
    
    def get_duanyu_by_jixiong(self, level: JixiongLevel, scenario: str = "总论") -> str:
        """根据吉凶等级获取断语"""
        duanyu_map = {
            JixiongLevel.DA_JI: {
                "总论": "大吉之课，诸事皆宜，贵人扶持，逢凶化吉。",
                "安葬": "安葬大吉，主子孙显达，富贵双全，当年必有喜事。",
                "开业": "开业大吉，主事业兴隆，财源广进，生意兴隆。",
            },
            JixiongLevel.SHANG_JI: {
                "总论": "上吉之课，贵人扶持，事业顺遂，逢凶化吉。",
                "安葬": "安葬上吉，主子孙显达，贵人扶持，事业顺遂。",
                "开业": "开业上吉，主事业兴隆，贵人扶持，生意兴隆。",
            },
            JixiongLevel.ZHONG_JI: {
                "总论": "中吉之课，平稳顺利，小有收获。",
                "安葬": "安葬中吉，主子孙平安，事业顺利。",
                "开业": "开业中吉，主事业平稳，生意顺利。",
            },
            JixiongLevel.XIAO_JI: {
                "总论": "小吉之课，略有助力，谨慎行事。",
                "安葬": "安葬小吉，主子孙平安，小有收获。",
                "开业": "开业小吉，主事业平稳，小有收获。",
            },
            JixiongLevel.PING: {
                "总论": "平运之课，无功无过，静待时机。",
                "安葬": "安葬平运，主子孙平安，无功无过。",
                "开业": "开业平运，主事业平稳，无功无过。",
            },
            JixiongLevel.XIAO_XIONG: {
                "总论": "小凶之课，略有阻碍，谨慎行事。",
                "安葬": "安葬小凶，主子孙有阻，谨慎行事。",
                "开业": "开业小凶，主事业有阻，谨慎行事。",
            },
            JixiongLevel.ZHONG_XIONG: {
                "总论": "中凶之课，多有不利，暂缓行事。",
                "安葬": "安葬中凶，主子孙不利，暂缓行事。",
                "开业": "开业中凶，主事业不利，暂缓行事。",
            },
            JixiongLevel.DA_XIONG: {
                "总论": "大凶之课，诸事不宜，避之为上。",
                "安葬": "安葬大凶，主子孙有灾，切勿行事。",
                "开业": "开业大凶，主事业有灾，切勿行事。",
            },
        }
        return duanyu_map.get(level, {}).get(scenario, "需具体分析")


class ScoringAlgorithmLayer:
    """评分算法层"""
    
    def __init__(self, weight_config: WeightConfigLayer = None):
        self.weight_config = weight_config or WeightConfigLayer()
        self.duanyu_mapper = DuanyuMappingLayer()
    
    def calculate_keti_score(self, keti_name: str) -> float:
        """计算课体评分（0-100）"""
        level, _ = self.duanyu_mapper.map_keti_to_jixiong(keti_name)
        attr = JixiongDefinitionLayer.JIXIONG_ATTRIBUTES[level]
        return (attr.score_range[0] + attr.score_range[1]) / 2
    
    def calculate_luma_score(self, luma_info: Dict) -> float:
        """计算禄马贵人评分（0-100）"""
        if not luma_info:
            return 50.0
        
        score = 0.0
        count = 0
        
        for luma_type, details in luma_info.items():
            if isinstance(details, dict):
                for sub_type, is_arrived in details.items():
                    if is_arrived:
                        level, _ = self.duanyu_mapper.map_luma_to_jixiong(luma_type, True)
                        attr = JixiongDefinitionLayer.JIXIONG_ATTRIBUTES[level]
                        score += (attr.score_range[0] + attr.score_range[1]) / 2
                        count += 1
        
        return score / count if count > 0 else 50.0
    
    def calculate_comprehensive_score(self, factors: Dict[str, float]) -> float:
        """计算综合评分"""
        total_score = 0.0
        total_weight = 0.0
        
        for factor_name, factor_score in factors.items():
            weight = self.weight_config.get_weight(factor_name)
            total_score += factor_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 50.0


class JixiongEvaluationCore:
    """吉凶评价核心类"""
    
    def __init__(self, custom_weights: Dict[str, float] = None):
        self.definition_layer = JixiongDefinitionLayer()
        self.weight_layer = WeightConfigLayer(custom_weights)
        self.duanyu_layer = DuanyuMappingLayer()
        self.scoring_layer = ScoringAlgorithmLayer(self.weight_layer)
    
    def evaluate(self, 
                 keti_name: str = None,
                 luma_info: Dict = None,
                 doushou_score: float = None,
                 yanqin_score: float = None,
                 shan_xiang_score: float = None) -> EvaluationResult:
        """
        综合评价
        
        :param keti_name: 课体名称
        :param luma_info: 禄马贵人信息
        :param doushou_score: 斗首评分
        :param yanqin_score: 演禽评分
        :param shan_xiang_score: 山向评分
        :return: 评价结果
        """
        factors = {}
        
        if keti_name:
            factors['课体课格'] = self.scoring_layer.calculate_keti_score(keti_name)
        
        if luma_info:
            factors['禄马贵人'] = self.scoring_layer.calculate_luma_score(luma_info)
        
        if doushou_score is not None:
            factors['斗首课格'] = doushou_score
        
        if yanqin_score is not None:
            factors['演禽真法'] = yanqin_score
        
        if shan_xiang_score is not None:
            factors['山向配合'] = shan_xiang_score
        
        comprehensive_score = self.scoring_layer.calculate_comprehensive_score(factors)
        level = self.definition_layer.get_level_by_score(comprehensive_score)
        attribute = self.definition_layer.get_attribute_by_score(comprehensive_score)
        duanyu = self.duanyu_layer.get_duanyu_by_jixiong(level)
        
        detailed_duanyu = {
            "总论": duanyu,
            "建议": attribute.recommendation,
            "适用场景": "、".join(attribute.applicable_scenarios)
        }
        
        recommendations = self._generate_recommendations(comprehensive_score, factors)
        
        return EvaluationResult(
            score=comprehensive_score,
            level=level,
            attribute=attribute,
            duanyu=duanyu,
            detailed_duanyu=detailed_duanyu,
            factors=factors,
            recommendations=recommendations,
            literature_source="《仪度六壬选日要诀》"
        )
    
    def _generate_recommendations(self, score: float, factors: Dict[str, float]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if score >= 80:
            recommendations.append("宜速行事，机不可失")
            recommendations.append("贵人扶持，诸事顺遂")
        elif score >= 60:
            recommendations.append("宜稳步推进，循序渐进")
            recommendations.append("谨慎行事，小有收获")
        elif score >= 40:
            recommendations.append("宜暂缓行事，避凶趋吉")
            recommendations.append("防小人是非，谨慎为上")
        else:
            recommendations.append("宜避之，切勿行事")
            recommendations.append("诸事不宜，静待时机")
        
        for factor, factor_score in factors.items():
            if factor_score < 50:
                recommendations.append(f"{factor}评分较低，需特别注意")
        
        return recommendations
    
    def get_evaluation_report(self, result: EvaluationResult) -> str:
        """生成评价报告"""
        report = []
        report.append("=" * 60)
        report.append("【吉凶评价报告】")
        report.append("=" * 60)
        report.append(f"\n综合评分：{result.score:.1f} 分")
        report.append(f"\n吉凶等级：{result.level.value}")
        report.append(f"\n吉凶描述：{result.attribute.description}")
        report.append(f"\n\n【断语】")
        report.append(f"\n{result.duanyu}")
        report.append(f"\n\n【详细断语】")
        for key, value in result.detailed_duanyu.items():
            report.append(f"\n  · {key}：{value}")
        report.append(f"\n\n【评分因素】")
        for factor, score in result.factors.items():
            weight = self.weight_layer.get_weight(factor)
            report.append(f"\n  · {factor}：{score:.1f} 分（权重：{weight*100:.0f}%）")
        report.append(f"\n\n【建议】")
        for i, rec in enumerate(result.recommendations, 1):
            report.append(f"\n  {i}. {rec}")
        report.append(f"\n\n【文献依据】")
        report.append(f"\n  {result.literature_source}")
        report.append("\n" + "=" * 60)
        
        return "".join(report)


if __name__ == '__main__':
    core = JixiongEvaluationCore()
    
    result = core.evaluate(
        keti_name="龙德课",
        luma_info={
            '禄神到山': {'日禄到山': True},
            '贵人到山': {'日贵到山': True}
        },
        doushou_score=85.0,
        yanqin_score=75.0,
        shan_xiang_score=80.0
    )
    
    print(core.get_evaluation_report(result))
