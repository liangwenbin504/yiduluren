#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 模块 5：综合评分模块

功能：
1. 实现科学的加权评分算法
2. 将斗首课格评分、演禽真法评分及大六壬课格评分进行综合计算
3. 明确各评分项的初始权重系数（斗首 40%、演禽 30%、大六壬 30%）
4. 提供配置接口以便根据实际需求调整权重参数
5. 输出综合评分结果及各单项评分的详细占比分析
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WeightConfig:
    """权重配置数据类"""
    douhou_weight: float = 0.4  # 斗首权重
    yanqin_weight: float = 0.3  # 演禽权重
    daliuren_weight: float = 0.3  # 大六壬权重
    
    def __post_init__(self):
        """验证权重和是否为 1"""
        total = self.douhou_weight + self.yanqin_weight + self.daliuren_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"权重总和必须为 1，当前总和：{total}")
        
        # 确保所有权重非负
        if any(w < 0 for w in [self.douhou_weight, self.yanqin_weight, self.daliuren_weight]):
            raise ValueError("权重不能为负数")


@dataclass
class ScoreItem:
    """评分项数据类"""
    name: str  # 评分项名称
    score: float  # 分数 (0-100)
    weight: float  # 权重
    weighted_score: float  # 加权分数
    description: str = ""  # 描述


class ComprehensiveScorer:
    """综合评分器"""
    
    def __init__(self, weight_config: Optional[WeightConfig] = None):
        """
        初始化综合评分器
        :param weight_config: 权重配置，默认使用标准配置
        """
        self.weight_config = weight_config or WeightConfig()
        self.logs = []
    
    def log(self, message: str):
        """记录日志"""
        self.logs.append(message)
    
    def set_weights(self, douhou: float, yanqin: float, daliuren: float):
        """
        设置权重
        :param douhou: 斗首权重
        :param yanqin: 演禽权重
        :param daliuren: 大六壬权重
        """
        self.weight_config = WeightConfig(douhou, yanqin, daliuren)
        self.log(f"权重已更新：斗首={douhou}, 演禽={yanqin}, 大六壬={daliuren}")
    
    def get_weights(self) -> Dict[str, float]:
        """获取当前权重配置"""
        return {
            '斗首': self.weight_config.douhou_weight,
            '演禽': self.weight_config.yanqin_weight,
            '大六壬': self.weight_config.daliuren_weight
        }
    
    def calculate_comprehensive_score(
        self,
        douhou_score: float,
        yanqin_score: float,
        daliuren_score: float
    ) -> Dict:
        """
        计算综合评分
        :param douhou_score: 斗首评分 (0-100)
        :param yanqin_score: 演禽评分 (0-100)
        :param daliuren_score: 大六壬评分 (0-100)
        :return: 综合评分结果字典
        """
        self.logs = []
        self.log("开始计算综合评分")
        
        # 验证分数范围
        for score_name, score in [
            ('斗首', douhou_score),
            ('演禽', yanqin_score),
            ('大六壬', daliuren_score)
        ]:
            if not (0 <= score <= 100):
                raise ValueError(f"{score_name}评分必须在 0-100 之间，当前：{score}")
        
        # 计算加权分数
        douhou_weighted = douhou_score * self.weight_config.douhou_weight
        yanqin_weighted = yanqin_score * self.weight_config.yanqin_weight
        daliuren_weighted = daliuren_score * self.weight_config.daliuren_weight
        
        # 综合评分
        comprehensive_score = douhou_weighted + yanqin_weighted + daliuren_weighted
        
        # 构建评分项
        score_items = [
            ScoreItem(
                name='斗首课格',
                score=douhou_score,
                weight=self.weight_config.douhou_weight,
                weighted_score=douhou_weighted,
                description=self._get_score_description(douhou_score)
            ),
            ScoreItem(
                name='演禽真法',
                score=yanqin_score,
                weight=self.weight_config.yanqin_weight,
                weighted_score=yanqin_weighted,
                description=self._get_score_description(yanqin_score)
            ),
            ScoreItem(
                name='大六壬课体',
                score=daliuren_score,
                weight=self.weight_config.daliuren_weight,
                weighted_score=daliuren_weighted,
                description=self._get_score_description(daliuren_score)
            )
        ]
        
        # 计算占比
        total_weighted = sum(item.weighted_score for item in score_items)
        if total_weighted > 0:
            for item in score_items:
                item.percentage = (item.weighted_score / total_weighted * 100) if total_weighted > 0 else 0
        else:
            for item in score_items:
                item.percentage = 0
        
        # 构建结果
        result = {
            '综合评分': round(comprehensive_score, 2),
            '综合吉凶': self._get_comprehensive_jixiong(comprehensive_score),
            '各单项评分': {
                '斗首课格': {
                    '原始分数': douhou_score,
                    '权重': self.weight_config.douhou_weight,
                    '加权分数': round(douhou_weighted, 2),
                    '占比': round(score_items[0].percentage, 2),
                    '吉凶': self._get_score_description(douhou_score)
                },
                '演禽真法': {
                    '原始分数': yanqin_score,
                    '权重': self.weight_config.yanqin_weight,
                    '加权分数': round(yanqin_weighted, 2),
                    '占比': round(score_items[1].percentage, 2),
                    '吉凶': self._get_score_description(yanqin_score)
                },
                '大六壬课体': {
                    '原始分数': daliuren_score,
                    '权重': self.weight_config.daliuren_weight,
                    '加权分数': round(daliuren_weighted, 2),
                    '占比': round(score_items[2].percentage, 2),
                    '吉凶': self._get_score_description(daliuren_score)
                }
            },
            '权重配置': self.get_weights(),
            '评分详情': [
                {
                    '名称': item.name,
                    '分数': item.score,
                    '权重': item.weight,
                    '加权分': round(item.weighted_score, 2),
                    '占比': f"{item.percentage:.2f}%",
                    '吉凶': item.description
                }
                for item in score_items
            ],
            '日志': []
        }
        
        # 记录计算过程
        self.log(f"斗首评分：{douhou_score} × {self.weight_config.douhou_weight} = {douhou_weighted:.2f}")
        self.log(f"演禽评分：{yanqin_score} × {self.weight_config.yanqin_weight} = {yanqin_weighted:.2f}")
        self.log(f"大六壬评分：{daliuren_score} × {self.weight_config.daliuren_weight} = {daliuren_weighted:.2f}")
        self.log(f"综合评分：{comprehensive_score:.2f}")
        
        result['日志'] = self.logs.copy()
        
        return result
    
    def _get_score_description(self, score: float) -> str:
        """根据分数返回吉凶描述"""
        if score >= 90:
            return "上上大吉"
        elif score >= 80:
            return "上吉"
        elif score >= 70:
            return "中吉"
        elif score >= 60:
            return "小吉"
        elif score >= 50:
            return "吉凶参半"
        elif score >= 40:
            return "小凶"
        elif score >= 30:
            return "中凶"
        elif score >= 20:
            return "大凶"
        else:
            return "上凶"
    
    def _get_comprehensive_jixiong(self, score: float) -> Dict:
        """获取综合吉凶详细信息"""
        jixiong_map = {
            '上上大吉': {
                'level': 1,
                'description': '百事亨通，万事如意',
                'suggestion': '大吉之日，百事可为，宜嫁娶、入宅、开市、动土等'
            },
            '上吉': {
                'level': 2,
                'description': '诸事顺利，谋事可成',
                'suggestion': '吉之日，大利行事，多数事情都适宜'
            },
            '中吉': {
                'level': 3,
                'description': '总体吉利，小有波折',
                'suggestion': '可用之日，行事谨慎则吉'
            },
            '小吉': {
                'level': 4,
                'description': '小利，宜守不宜攻',
                'suggestion': '斟酌用之，小事可为，大事需谨慎'
            },
            '吉凶参半': {
                'level': 5,
                'description': '吉凶混杂，需谨慎行事',
                'suggestion': '可不用，如必须用事，需择吉时并做化解'
            },
            '小凶': {
                'level': 6,
                'description': '小有不利，易生波折',
                'suggestion': '不宜用，如必须用事，需慎重考虑'
            },
            '中凶': {
                'level': 7,
                'description': '多有不利，诸事难成',
                'suggestion': '忌用，避免重要行事'
            },
            '大凶': {
                'level': 8,
                'description': '大凶之象，灾祸难免',
                'suggestion': '不可用，百事忌'
            },
            '上凶': {
                'level': 9,
                'description': '极凶，大灾大难',
                'suggestion': '大忌，绝对不可用事'
            }
        }
        
        # 根据分数确定吉凶等级
        if score >= 90:
            level = '上上大吉'
        elif score >= 80:
            level = '上吉'
        elif score >= 70:
            level = '中吉'
        elif score >= 60:
            level = '小吉'
        elif score >= 50:
            level = '吉凶参半'
        elif score >= 40:
            level = '小凶'
        elif score >= 30:
            level = '中凶'
        elif score >= 20:
            level = '大凶'
        else:
            level = '上凶'
        
        result = jixiong_map.get(level, jixiong_map['吉凶参半'])
        result['level_name'] = level
        
        return result
    
    def compare_scores(
        self,
        score_list: List[Dict],
        sort_by: str = 'comprehensive'
    ) -> Dict:
        """
        比较多个日课的综合评分
        :param score_list: 评分结果列表（每个元素为 calculate_comprehensive_score 的返回值）
        :param sort_by: 排序依据 ('comprehensive' 综合，'douhou' 斗首，'yanqin' 演禽，'daliuren' 大六壬)
        :return: 比较结果
        """
        if not score_list:
            return {'error': '评分列表为空'}
        
        # 排序
        if sort_by == 'comprehensive':
            sorted_scores = sorted(
                score_list,
                key=lambda x: x.get('综合评分', 0),
                reverse=True
            )
        elif sort_by == 'douhou':
            sorted_scores = sorted(
                score_list,
                key=lambda x: x.get('各单项评分', {}).get('斗首课格', {}).get('原始分数', 0),
                reverse=True
            )
        elif sort_by == 'yanqin':
            sorted_scores = sorted(
                score_list,
                key=lambda x: x.get('各单项评分', {}).get('演禽真法', {}).get('原始分数', 0),
                reverse=True
            )
        elif sort_by == 'daliuren':
            sorted_scores = sorted(
                score_list,
                key=lambda x: x.get('各单项评分', {}).get('大六壬课体', {}).get('原始分数', 0),
                reverse=True
            )
        else:
            sorted_scores = score_list
        
        # 构建比较结果
        comparison = {
            '总课数': len(score_list),
            '排序方式': sort_by,
            '最佳日课': sorted_scores[0] if sorted_scores else None,
            '最差日课': sorted_scores[-1] if sorted_scores else None,
            '平均分': sum(s.get('综合评分', 0) for s in score_list) / len(score_list) if score_list else 0,
            '最高分': max(s.get('综合评分', 0) for s in score_list) if score_list else 0,
            '最低分': min(s.get('综合评分', 0) for s in score_list) if score_list else 0,
            '排序结果': [
                {
                    '排名': i + 1,
                    '综合评分': s.get('综合评分', 0),
                    '综合吉凶': s.get('综合吉凶', {}).get('level_name', ''),
                    '斗首分数': s.get('各单项评分', {}).get('斗首课格', {}).get('原始分数', 0),
                    '演禽分数': s.get('各单项评分', {}).get('演禽真法', {}).get('原始分数', 0),
                    '大六壬分数': s.get('各单项评分', {}).get('大六壬课体', {}).get('原始分数', 0),
                }
                for i, s in enumerate(sorted_scores)
            ]
        }
        
        return comparison
    
    def generate_report(self, comprehensive_result: Dict) -> str:
        """
        生成综合评分报告
        :param comprehensive_result: calculate_comprehensive_score 的返回值
        :return: 格式化报告文本
        """
        report = []
        report.append("=" * 70)
        report.append("日课综合评分报告")
        report.append("=" * 70)
        
        report.append(f"\n【综合评分】{comprehensive_result['综合评分']}分")
        report.append(f"【综合吉凶】{comprehensive_result['综合吉凶'].get('level_name', '')}")
        report.append(f"【吉凶描述】{comprehensive_result['综合吉凶'].get('description', '')}")
        
        report.append("\n【各单项评分】")
        for item in comprehensive_result['评分详情']:
            report.append(f"\n  {item['名称']}:")
            report.append(f"    原始分数：{item['分数']} ({item['吉凶']})")
            report.append(f"    权重：{item['权重'] * 100}%")
            report.append(f"    加权分数：{item['加权分']}")
            report.append(f"    占比：{item['占比']}")
        
        report.append("\n【建议】")
        report.append(f"  {comprehensive_result['综合吉凶'].get('suggestion', '')}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


def test_comprehensive_scorer():
    """测试综合评分器"""
    print("=" * 70)
    print("综合评分模块测试")
    print("=" * 70)
    
    scorer = ComprehensiveScorer()
    
    # 测试 1：标准权重
    print("\n【测试 1】标准权重配置 (斗首 40%、演禽 30%、大六壬 30%)")
    print(f"当前权重：{scorer.get_weights()}")
    
    douhou = 85  # 斗首评分
    yanqin = 75  # 演禽评分
    daliuren = 80  # 大六壬评分
    
    result = scorer.calculate_comprehensive_score(douhou, yanqin, daliuren)
    
    print(f"\n输入评分:")
    print(f"  斗首：{douhou}分")
    print(f"  演禽：{yanqin}分")
    print(f"  大六壬：{daliuren}分")
    
    print(f"\n综合评分：{result['综合评分']}分")
    print(f"综合吉凶：{result['综合吉凶']['level_name']}")
    print(f"吉凶描述：{result['综合吉凶']['description']}")
    
    print("\n各单项详情:")
    for item in result['评分详情']:
        print(f"  {item['名称']}: {item['分数']}分 × {item['权重']} = {item['加权分']}分 (占比{item['占比']})")
    
    # 测试 2：自定义权重
    print("\n【测试 2】自定义权重配置 (斗首 50%、演禽 25%、大六壬 25%)")
    scorer.set_weights(0.5, 0.25, 0.25)
    result2 = scorer.calculate_comprehensive_score(douhou, yanqin, daliuren)
    print(f"综合评分：{result2['综合评分']}分")
    
    # 测试 3：生成报告
    print("\n【测试 3】生成综合评分报告")
    report = scorer.generate_report(result)
    print(report)
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_comprehensive_scorer()
