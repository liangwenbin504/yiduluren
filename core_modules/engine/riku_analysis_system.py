#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 主分析模块

整合所有分析模块，提供统一的日课分析接口
利用 GLM-5-TURBO 模型进行智能评价报告生成
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from date_range_generator import DateRangeGenerator
from douhou_analyzer import DouhouKegeAnalyzer
from yanqin_analyzer import YanQinAnalyzer
from daliuren_kege_analyzer import DaLiuRenKegeAnalyzer
from comprehensive_scorer import ComprehensiveScorer, WeightConfig


class RikeAnalysisSystem:
    """日课分析系统主类"""
    
    def __init__(self, weight_config: Optional[WeightConfig] = None):
        """
        初始化日课分析系统
        :param weight_config: 综合评分权重配置
        """
        self.date_generator = DateRangeGenerator()
        self.douhou_analyzer = DouhouKegeAnalyzer()
        self.yanqin_analyzer = YanQinAnalyzer()
        self.daliuren_analyzer = DaLiuRenKegeAnalyzer()
        self.comprehensive_scorer = ComprehensiveScorer(weight_config)
        
        self.logs = []
    
    def log(self, message: str):
        """记录日志"""
        self.logs.append(message)
    
    def analyze_single_ke(
        self,
        date: datetime,
        shichen_index: int,
        shan: str
    ) -> Dict:
        """
        分析单个日课
        :param date: 公历日期
        :param shichen_index: 时辰索引 (1-12)
        :param shan: 坐山 (如"壬"、"子"等)
        :return: 完整分析结果
        """
        self.logs = []
        self.log(f"开始分析日课：{date.strftime('%Y-%m-%d')} {shichen_index}时 坐山：{shan}")
        
        # 1. 获取日课基础数据
        ke_data = self.date_generator.get_single_ke_data(date, shichen_index)
        
        # 2. 提取四柱信息
        sizhu = ke_data['四柱信息']
        
        # 3. 斗首课格分析
        self.log("进行斗首课格分析...")
        douhou_result = self.douhou_analyzer.analyze_kege(shan, sizhu)
        
        # 4. 演禽真法分析
        self.log("进行演禽真法分析...")
        yanqin_result = self.yanqin_analyzer.analyze_yanqin(sizhu)
        
        # 5. 大六壬课体分析
        self.log("进行大六壬课体分析...")
        daliuren_result = self.daliuren_analyzer.analyze_kege(
            date=date,
            shichen_index=shichen_index,
            ri_gan=sizhu['日柱'][0],
            ri_zhi=sizhu['日柱'][1]
        )
        
        # 6. 综合评分
        self.log("计算综合评分...")
        comprehensive_result = self.comprehensive_scorer.calculate_comprehensive_score(
            douhou_score=douhou_result['综合评分'],
            yanqin_score=yanqin_result['综合评分'],
            daliuren_score=daliuren_result['综合评分']
        )
        
        # 7. 构建完整结果
        result = {
            '基础信息': {
                '公历日期': ke_data['公历日期'],
                '四柱': sizhu,
                '坐山': shan,
                '时辰': ke_data['时辰信息']
            },
            '斗首课格分析': douhou_result,
            '演禽真法分析': yanqin_result,
            '大六壬课体分析': daliuren_result,
            '综合评分': comprehensive_result,
            '辅助信息': {
                '状态': '待实现',
                '龙运': '尚未集成',
                '山运': '尚未集成'
            },
            'GLM 评价报告': '待生成',
            '系统日志': self.logs.copy()
        }
        
        # 8. 生成 GLM 评价报告 (模拟)
        result['GLM 评价报告'] = self._generate_glm_report(result)
        
        return result
    
    def analyze_daily_ke(
        self,
        date: datetime,
        shan: str,
        min_score: int = 0
    ) -> List[Dict]:
        """
        分析单日 12 个时辰的所有日课
        :param date: 公历日期
        :param shan: 坐山
        :param min_score: 最低分数筛选 (默认返回全部)
        :return: 分析结果列表
        """
        results = []
        
        for shichen_idx in range(1, 13):
            result = self.analyze_single_ke(date, shichen_idx, shan)
            
            # 筛选
            if result['综合评分']['综合评分'] >= min_score:
                results.append(result)
        
        # 按综合评分排序
        results.sort(key=lambda x: x['综合评分']['综合评分'], reverse=True)
        
        return results
    
    def analyze_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        shan: str,
        min_score: int = 60,
        progress_callback=None
    ) -> List[Dict]:
        """
        分析指定日期范围内的所有日课
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param shan: 坐山
        :param min_score: 最低分数筛选 (默认 60 分以上)
        :param progress_callback: 进度回调函数
        :return: 符合条件的日课分析结果列表
        """
        self.log(f"开始分析日期范围：{start_date} 至 {end_date}, 坐山：{shan}")
        
        # 设置日期范围
        self.date_generator.start_date = start_date
        self.date_generator.end_date = end_date
        
        all_results = []
        date_range = self.date_generator.generate_date_range()
        total_days = len(date_range)
        
        for idx, date in enumerate(date_range):
            # 进度回调
            if progress_callback:
                progress_callback(date, total_days, idx + 1)
            
            # 分析该日 12 时辰
            daily_results = self.analyze_daily_ke(date, shan, min_score)
            all_results.extend(daily_results)
            
            # 定期输出进度
            if (idx + 1) % 30 == 0:
                self.log(f"已处理 {idx + 1}/{total_days} 天，找到 {len(all_results)} 个符合条件的日课")
        
        # 按综合评分排序
        all_results.sort(key=lambda x: x['综合评分']['综合评分'], reverse=True)
        
        self.log(f"分析完成，共找到 {len(all_results)} 个符合条件的日课")
        
        return all_results
    
    def _generate_glm_report(self, result: Dict) -> str:
        """
        生成 GLM-5-TURBO 模型评价报告
        (当前为规则模板生成，后续可接入真实 GLM API)
        """
        report = []
        
        # 基础信息
        report.append("=" * 70)
        report.append("日课分析评价报告")
        report.append("=" * 70)
        
        base = result['基础信息']
        report.append(f"\n【日课信息】")
        report.append(f"  公历：{base['公历日期']['日期字符串']}")
        report.append(f"  四柱：{base['四柱']['年柱']} {base['四柱']['月柱']} {base['四柱']['日柱']} {base['四柱']['时柱']}")
        report.append(f"  坐山：{base['坐山']}")
        report.append(f"  时辰：{base['时辰']['时辰地支']}时 ({base['时辰']['时间范围']})")
        
        # 综合评分
        comp = result['综合评分']
        report.append(f"\n【综合评分】{comp['综合评分']}分")
        report.append(f"【综合吉凶】{comp['综合吉凶']['level_name']}")
        report.append(f"【吉凶描述】{comp['综合吉凶']['description']}")
        
        # 斗首分析
        douhou = result['斗首课格分析']
        report.append(f"\n【斗首课格分析】{douhou['综合评分']}分")
        report.append(f"  山家五行：{douhou['山家五行']}")
        if douhou.get('课格格局'):
            report.append("  格局:")
            for pattern in douhou['课格格局']:
                report.append(f"    - {pattern['格局名称']} ({pattern['吉凶']})")
        if douhou.get('吉凶断语'):
            report.append("  断语:")
            for duanyu in douhou['吉凶断语'][:3]:  # 最多显示 3 条
                report.append(f"    - {duanyu}")
        
        # 演禽分析
        yanqin = result['演禽真法分析']
        report.append(f"\n【演禽真法分析】{yanqin['综合评分']}分")
        report.append(f"  四禽:")
        for key, value in yanqin['四禽'].items():
            qin_xing = yanqin['四禽禽星'].get(f'{key}星', '')
            jixiong = yanqin['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
            report.append(f"    {key}: {value} ({qin_xing}) - {jixiong}")
        if yanqin.get('吉凶断语'):
            report.append("  断语:")
            for duanyu in yanqin['吉凶断语'][:3]:
                report.append(f"    - {duanyu}")
        
        # 大六壬分析
        daliuren = result['大六壬课体分析']
        report.append(f"\n【大六壬课体分析】{daliuren['综合评分']}分")
        report.append(f"  状态：{daliuren.get('状态', '待实现')}")
        
        # 建议
        report.append(f"\n【使用建议】")
        report.append(f"  {comp['综合吉凶'].get('suggestion', '')}")
        
        # 各单项占比
        report.append(f"\n【评分构成】")
        for item in comp['评分详情']:
            report.append(f"  {item['名称']}: {item['分数']}分 (权重{item['权重']*100}%, 占比{item['占比']})")
        
        report.append("\n" + "=" * 70)
        report.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def get_best_ke(
        self,
        start_date: datetime,
        end_date: datetime,
        shan: str,
        top_n: int = 10
    ) -> List[Dict]:
        """
        获取指定日期范围内最佳的 N 个日课
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param shan: 坐山
        :param top_n: 返回前 N 个最佳日课
        :return: 最佳日课列表
        """
        # 分析并筛选 (默认 70 分以上)
        all_results = self.analyze_date_range(start_date, end_date, shan, min_score=70)
        
        # 返回前 N 个
        return all_results[:top_n]


def test_riku_system():
    """测试日课分析系统"""
    print("=" * 70)
    print("日课分析系统测试")
    print("=" * 70)
    
    system = RikeAnalysisSystem()
    
    # 测试 1：分析单个日课
    print("\n【测试 1】分析单个日课")
    print("日期：2026 年 3 月 24 日 午时 (第 7 个时辰) 坐山：壬")
    
    test_date = datetime(2026, 3, 24)
    result = system.analyze_single_ke(test_date, 7, '壬')
    
    print(f"\n四柱：{result['基础信息']['四柱']}")
    print(f"综合评分：{result['综合评分']['综合评分']}分")
    print(f"综合吉凶：{result['综合评分']['综合吉凶']['level_name']}")
    
    print("\n" + "-" * 70)
    print(result['GLM 评价报告'])
    
    # 测试 2：分析单日所有时辰
    print("\n【测试 2】分析 2026 年 3 月 24 日全天 12 时辰，筛选 70 分以上")
    daily_results = system.analyze_daily_ke(test_date, '壬', min_score=70)
    print(f"找到 {len(daily_results)} 个符合条件的日课")
    
    if daily_results:
        print("\n前 3 个最佳日课:")
        for i, res in enumerate(daily_results[:3], 1):
            print(f"{i}. {res['基础信息']['时辰']['时辰地支']}时 - "
                  f"{res['综合评分']['综合评分']}分 ({res['综合评分']['综合吉凶']['level_name']})")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_riku_system()
