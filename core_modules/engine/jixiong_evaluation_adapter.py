#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
吉凶评价模块适配器 - JixiongEvaluationAdapter

整合新的吉凶评价核心架构与现有模块：
1. ComprehensiveScorer - 综合评分模块
2. LiuRenKeTiScorer - 六壬课体评分
3. ComprehensiveEvaluation - 综合评价系统
4. API接口适配

确保各模块与吉凶评价体系的交互逻辑、数据流转及接口兼容性
"""

from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from jixiong_evaluation_core import (
    JixiongEvaluationCore,
    JixiongLevel,
    JixiongAttribute,
    EvaluationResult,
    WeightConfigLayer
)


class JixiongEvaluationAdapter:
    """吉凶评价模块适配器"""
    
    def __init__(self, custom_weights: Dict[str, float] = None):
        self.core = JixiongEvaluationCore(custom_weights)
    
    def adapt_from_comprehensive_scorer(self, scorer_result: Dict) -> EvaluationResult:
        """
        适配综合评分模块结果
        
        :param scorer_result: ComprehensiveScorer 的输出结果
        :return: 标准化的评价结果
        """
        comprehensive_score = scorer_result.get('综合评分', 50)
        
        factors = {}
        single_scores = scorer_result.get('各单项评分', {})
        
        if '斗首课格' in single_scores:
            factors['斗首课格'] = single_scores['斗首课格'].get('原始分数', 50)
        if '演禽真法' in single_scores:
            factors['演禽真法'] = single_scores['演禽真法'].get('原始分数', 50)
        if '大六壬课体' in single_scores:
            factors['课体课格'] = single_scores['大六壬课体'].get('原始分数', 50)
        
        return self.core.evaluate(
            doushou_score=factors.get('斗首课格'),
            yanqin_score=factors.get('演禽真法'),
            shan_xiang_score=factors.get('山向配合')
        )
    
    def adapt_from_liuren_scorer(self, keti_name: str, score: float) -> EvaluationResult:
        """
        适配六壬课体评分结果
        
        :param keti_name: 课体名称
        :param score: 课体评分（0-10分制）
        :return: 标准化的评价结果
        """
        normalized_score = score * 10  # 转换为0-100分制
        
        return self.core.evaluate(keti_name=keti_name)
    
    def adapt_from_api_request(self, request_data: Dict) -> EvaluationResult:
        """
        适配API请求数据
        
        :param request_data: API请求数据
        :return: 标准化的评价结果
        """
        keti_name = request_data.get('keti') or request_data.get('课体')
        
        luma_info = {}
        if request_data.get('luma_info') or request_data.get('禄马贵人'):
            luma_info = request_data.get('luma_info') or request_data.get('禄马贵人')
        
        doushou_score = request_data.get('doushou_score') or request_data.get('斗首评分')
        yanqin_score = request_data.get('yanqin_score') or request_data.get('演禽评分')
        shan_xiang_score = request_data.get('shan_xiang_score') or request_data.get('山向评分')
        
        return self.core.evaluate(
            keti_name=keti_name,
            luma_info=luma_info,
            doushou_score=doushou_score,
            yanqin_score=yanqin_score,
            shan_xiang_score=shan_xiang_score
        )
    
    def to_api_response(self, result: EvaluationResult) -> Dict:
        """
        转换为API响应格式
        
        :param result: 评价结果
        :return: API响应字典
        """
        return {
            'success': True,
            'score': round(result.score, 2),
            'level': result.level.value,
            'description': result.attribute.description,
            'color': result.attribute.color,
            'duanyu': result.duanyu,
            'detailed_duanyu': result.detailed_duanyu,
            'factors': {k: round(v, 2) for k, v in result.factors.items()},
            'weights': self.core.weight_layer.get_all_weights(),
            'recommendations': result.recommendations,
            'literature_source': result.literature_source,
            'applicable_scenarios': result.attribute.applicable_scenarios
        }
    
    def to_legacy_format(self, result: EvaluationResult) -> Dict:
        """
        转换为旧版格式（兼容现有系统）
        
        :param result: 评价结果
        :return: 旧版格式字典
        """
        return {
            '综合评分': result.score,
            '综合吉凶': result.level.value,
            '吉凶描述': result.attribute.description,
            '断语': result.duanyu,
            '详细断语': result.detailed_duanyu,
            '评分因素': result.factors,
            '建议': result.recommendations,
            '文献依据': result.literature_source
        }


class WeightConfigManager:
    """权重配置管理器"""
    
    PRESETS = {
        'default': {
            '课体课格': 0.30,
            '禄马贵人': 0.25,
            '斗首课格': 0.20,
            '演禽真法': 0.15,
            '山向配合': 0.10,
        },
        'emphasis_keti': {
            '课体课格': 0.40,
            '禄马贵人': 0.25,
            '斗首课格': 0.15,
            '演禽真法': 0.10,
            '山向配合': 0.10,
        },
        'emphasis_luma': {
            '课体课格': 0.25,
            '禄马贵人': 0.35,
            '斗首课格': 0.20,
            '演禽真法': 0.10,
            '山向配合': 0.10,
        },
        'emphasis_doushou': {
            '课体课格': 0.25,
            '禄马贵人': 0.20,
            '斗首课格': 0.35,
            '演禽真法': 0.10,
            '山向配合': 0.10,
        },
        'balanced': {
            '课体课格': 0.20,
            '禄马贵人': 0.20,
            '斗首课格': 0.20,
            '演禽真法': 0.20,
            '山向配合': 0.20,
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, float]:
        """获取预设权重配置"""
        return cls.PRESETS.get(preset_name, cls.PRESETS['default']).copy()
    
    @classmethod
    def list_presets(cls) -> List[str]:
        """列出所有预设配置"""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def validate_custom_weights(cls, weights: Dict[str, float]) -> bool:
        """验证自定义权重"""
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            return False
        if any(w < 0 for w in weights.values()):
            return False
        return True


class ScoreThresholdManager:
    """评分阈值管理器"""
    
    THRESHOLDS = {
        'excellent': 85,     # 优秀阈值
        'good': 70,          # 良好阈值
        'pass': 60,          # 合格阈值
        'warning': 50,       # 警告阈值
        'danger': 40,        # 危险阈值
    }
    
    @classmethod
    def get_threshold_status(cls, score: float) -> str:
        """获取阈值状态"""
        if score >= cls.THRESHOLDS['excellent']:
            return 'excellent'
        elif score >= cls.THRESHOLDS['good']:
            return 'good'
        elif score >= cls.THRESHOLDS['pass']:
            return 'pass'
        elif score >= cls.THRESHOLDS['warning']:
            return 'warning'
        elif score >= cls.THRESHOLDS['danger']:
            return 'danger'
        else:
            return 'critical'
    
    @classmethod
    def get_threshold_description(cls, status: str) -> str:
        """获取阈值状态描述"""
        descriptions = {
            'excellent': '优秀：大吉之课，诸事皆宜',
            'good': '良好：上吉之课，贵人扶持',
            'pass': '合格：中吉之课，平稳顺利',
            'warning': '警告：平运之课，谨慎行事',
            'danger': '危险：凶课，暂缓行事',
            'critical': '严重：大凶之课，诸事不宜'
        }
        return descriptions.get(status, '未知状态')
    
    @classmethod
    def set_threshold(cls, name: str, value: float):
        """设置阈值"""
        if name in cls.THRESHOLDS and 0 <= value <= 100:
            cls.THRESHOLDS[name] = value


class JixiongEvaluationService:
    """吉凶评价服务（统一入口）"""
    
    def __init__(self, preset: str = 'default'):
        self.weights = WeightConfigManager.get_preset(preset)
        self.adapter = JixiongEvaluationAdapter(self.weights)
    
    def evaluate_date_course(self, course_data: Dict) -> Dict:
        """
        评价日课
        
        :param course_data: 日课数据
        :return: 评价结果
        """
        result = self.adapter.adapt_from_api_request(course_data)
        return self.adapter.to_api_response(result)
    
    def evaluate_keti(self, keti_name: str) -> Dict:
        """
        评价课体
        
        :param keti_name: 课体名称
        :return: 评价结果
        """
        result = self.core.evaluate(keti_name=keti_name)
        return self.adapter.to_api_response(result)
    
    def evaluate_luma(self, luma_info: Dict) -> Dict:
        """
        评价禄马贵人
        
        :param luma_info: 禄马贵人信息
        :return: 评价结果
        """
        result = self.core.evaluate(luma_info=luma_info)
        return self.adapter.to_api_response(result)
    
    def get_weight_config(self) -> Dict:
        """获取当前权重配置"""
        return self.weights
    
    def set_weight_config(self, preset: str = None, custom: Dict = None):
        """
        设置权重配置
        
        :param preset: 预设名称
        :param custom: 自定义权重
        """
        if preset:
            self.weights = WeightConfigManager.get_preset(preset)
        elif custom and WeightConfigManager.validate_custom_weights(custom):
            self.weights = custom
        
        self.adapter = JixiongEvaluationAdapter(self.weights)


if __name__ == '__main__':
    print("=" * 60)
    print("吉凶评价模块适配器测试")
    print("=" * 60)
    
    service = JixiongEvaluationService(preset='default')
    
    print("\n【测试1】预设权重配置列表")
    print(f"可用预设：{WeightConfigManager.list_presets()}")
    
    print("\n【测试2】当前权重配置")
    print(f"权重：{service.get_weight_config()}")
    
    print("\n【测试3】评价日课")
    course_data = {
        'keti': '龙德课',
        'luma_info': {
            '禄神到山': {'日禄到山': True},
            '贵人到山': {'日贵到山': True}
        },
        'doushou_score': 85,
        'yanqin_score': 75
    }
    result = service.evaluate_date_course(course_data)
    print(f"评分：{result['score']}")
    print(f"等级：{result['level']}")
    print(f"描述：{result['description']}")
    print(f"断语：{result['duanyu']}")
    
    print("\n【测试4】阈值状态")
    status = ScoreThresholdManager.get_threshold_status(result['score'])
    print(f"状态：{status}")
    print(f"描述：{ScoreThresholdManager.get_threshold_description(status)}")
    
    print("\n【测试5】切换权重预设")
    service.set_weight_config(preset='emphasis_keti')
    print(f"新权重：{service.get_weight_config()}")
    
    result2 = service.evaluate_date_course(course_data)
    print(f"新评分：{result2['score']}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
