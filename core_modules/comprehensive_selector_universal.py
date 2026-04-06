#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用全面筛选系统
适用于任何时间范围的日课筛选（三年、五年、十年等）
严格采用逐一筛选法，确保不遗漏任何一课
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from douhou_analyzer import DouhouKegeAnalyzer
from liuxiang_liuti_correct import LiuXiangLiuTiCorrect
from sizhu_engine import get_sizhu, get_day_ganzhi


class ComprehensiveSelector:
    """
    通用全面筛选器
    严格逐一筛选，确保不遗漏任何一课
    """
    
    def __init__(self, shan: str = '壬'):
        """
        初始化筛选器
        :param shan: 坐山（如'壬'）
        """
        self.shan = shan
        self.douhou_analyzer = DouhouKegeAnalyzer()
        self.liuxiang_system = LiuXiangLiuTiCorrect()
        
        # 统计信息
        self.stats = {
            '总天数': 0,
            '总课数': 0,
            '已分析课数': 0,
            '元辰得位课数': 0,
            '上上大吉课数': 0,
            '吉课数': 0,
            '平课数': 0,
            '凶课数': 0
        }
    
    def analyze_single_ke(self, sizhu: dict):
        """
        分析单个课格
        严格逐一筛选，不遗漏任何细节
        """
        # 1. 斗首课格分析
        douhou_result = self.douhou_analyzer.analyze_kege(self.shan, sizhu)
        douhou_score = douhou_result['综合评分']
        
        # 2. 六相六替分析
        liuxiang_result = self.liuxiang_system.analyze_sizhu(sizhu, '土')
        liuxiang_score = liuxiang_result.get('平均分', 0)
        
        # 3. 检查元辰是否得位
        yuanchen_positions = []
        for pillar_name, ganzhi in sizhu.items():
            tiangan = ganzhi[0]
            huaqi = self.liuxiang_system.get_huaqi(tiangan)
            if huaqi == '土':  # 元辰
                yuanchen_positions.append(pillar_name)
        
        yuanchen_dewei = len(yuanchen_positions) >= 1
        
        # 4. 元辰不得位则减分
        if not yuanchen_dewei:
            adjusted_douhou_score = max(0, douhou_score - 30)
        else:
            adjusted_douhou_score = douhou_score
        
        # 5. 综合评分：斗首 70% + 六相六替 30%
        total_score = adjusted_douhou_score * 0.7 + liuxiang_score * 0.3
        
        # 6. 统计
        self.stats['已分析课数'] += 1
        if yuanchen_dewei:
            self.stats['元辰得位课数'] += 1
        
        zonghe_pingjia = liuxiang_result.get('综合评价', '')
        if zonghe_pingjia == '上上大吉':
            self.stats['上上大吉课数'] += 1
        elif zonghe_pingjia == '吉':
            self.stats['吉课数'] += 1
        elif zonghe_pingjia == '平':
            self.stats['平课数'] += 1
        else:
            self.stats['凶课数'] += 1
        
        return {
            'sizhu': sizhu,
            '斗首评分': douhou_score,
            '调整后斗首评分': adjusted_douhou_score,
            '六相六替评分': liuxiang_score,
            '总分': total_score,
            '元辰位置': yuanchen_positions,
            '元辰得位': yuanchen_dewei,
            '斗首格局': douhou_result.get('课格格局', []),
            '六相统计': liuxiang_result.get('六相统计', 0),
            '六替统计': liuxiang_result.get('六替统计', 0),
            '吉课数': liuxiang_result.get('吉课数', 0),
            '凶课数': liuxiang_result.get('凶课数', 0),
            '综合评价': zonghe_pingjia
        }
    
    def select_top_ke(self, start_date: datetime, end_date: datetime, 
                     top_n: int = 5, min_score: float = 0,
                     show_progress: bool = True):
        """
        全面筛选指定时间范围内的最佳课格
        严格逐一筛选，确保不遗漏任何一课
        
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param top_n: 返回前 N 个最佳课格
        :param min_score: 最低分数要求
        :param show_progress: 是否显示进度
        :return: 最佳课格列表
        """
        print('='*100)
        print('通用全面筛选系统')
        print('='*100)
        print(f'筛选范围：{start_date.strftime("%Y 年%m 月%d 日")} 至 {end_date.strftime("%Y 年%m 月%d 日")}')
        print(f'坐山：{self.shan}山')
        print(f'目标：选出前 {top_n} 个最佳课格')
        print('='*100)
        
        # 计算总课数
        total_days = (end_date - start_date).days + 1
        total_ke = total_days * 12  # 每天 12 时辰
        
        self.stats['总天数'] = total_days
        self.stats['总课数'] = total_ke
        
        print(f'\n总天数：{total_days}天')
        print(f'总课数：{total_ke}课（每天 12 时辰）')
        print(f'\n开始逐一分析...\n')
        
        # 时辰地支
        shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        all_results = []
        current_date = start_date
        day_count = 0
        
        # 严格逐一筛选
        while current_date <= end_date:
            day_count += 1
            
            # 获取日柱干支
            day_ganzhi = get_day_ganzhi(current_date.year, current_date.month, current_date.day)
            
            # 逐一分析 12 个时辰
            for shichen_idx, shichen in enumerate(shichen_list):
                # 获取四柱（精确计算）
                sizhu = get_sizhu(current_date.year, current_date.month, current_date.day, shichen)
                
                # 分析课格
                result = self.analyze_single_ke(sizhu)
                result['公历日期'] = current_date
                result['时辰'] = shichen
                result['日柱'] = f"{day_ganzhi[0]}{day_ganzhi[1]}"
                
                # 筛选符合条件的课格
                if result['总分'] >= min_score:
                    all_results.append(result)
            
            # 进度显示
            if show_progress and day_count % 100 == 0:
                progress = day_count / total_days * 100
                print(f"已分析 {day_count}/{total_days} 天 ({progress:.1f}%) - {self.stats['已分析课数']}课")
            
            current_date += timedelta(days=1)
        
        print(f'\n分析完成！共分析 {len(all_results)} 个课格')
        
        # 按总分排序
        print('\n正在排序...')
        all_results.sort(key=lambda x: x['总分'], reverse=True)
        
        # 返回前 N 个
        top_results = all_results[:top_n]
        
        return top_results
    
    def display_results(self, results: list):
        """
        显示筛选结果
        """
        print('\n' + '='*100)
        print(f'🏆 最佳 {len(results)} 个吉课（按综合评分排序）')
        print('='*100)
        
        for i, result in enumerate(results, 1):
            print(f'\n【第{i}名】{result["公历日期"].strftime("%Y 年%m 月%d 日")} {result["时辰"]}时')
            print('-'*100)
            print(f'四柱：{result["sizhu"]["年柱"]} {result["sizhu"]["月柱"]} {result["sizhu"]["日柱"]} {result["sizhu"]["时柱"]}')
            print(f'\n【斗首课格】')
            print(f'  元辰位置：{result["元辰位置"]}')
            print(f'  元辰得位：{"✅ 是" if result["元辰得位"] else "❌ 否"}')
            print(f'  斗首评分：{result["斗首评分"]}分 → 调整后：{result["调整后斗首评分"]}分')
            
            if result['斗首格局']:
                print(f'  格局：')
                for pattern in result['斗首格局'][:3]:
                    print(f'    - {pattern["格局名称"]} ({pattern["吉凶"]}): {pattern["描述"]}')
            
            print(f'\n【六相六替】')
            print(f'  六相数：{result["六相统计"]}个')
            print(f'  六替数：{result["六替统计"]}个')
            print(f'  吉课数：{result["吉课数"]}个')
            print(f'  凶课数：{result["凶课数"]}个')
            print(f'  评分：{result["六相六替评分"]:.1f}分')
            print(f'  综合评价：{result["综合评价"]}')
            
            print(f'\n【综合评分】')
            print(f'  总分：{result["总分"]:.1f}分')
            print(f'  计算：斗首 ({result["调整后斗首评分"]}×70%) + 六相六替 ({result["六相六替评分"]:.1f}×30%)')
        
        # 显示统计信息
        print('\n' + '='*100)
        print('📊 筛选统计')
        print('='*100)
        print(f'总天数：{self.stats["总天数"]}天')
        print(f'总课数：{self.stats["总课数"]}课')
        print(f'元辰得位：{self.stats["元辰得位课数"]}课')
        print(f'上上大吉：{self.stats["上上大吉课数"]}课')
        print(f'吉课：{self.stats["吉课数"]}课')
        print(f'平课：{self.stats["平课数"]}课')
        print(f'凶课：{self.stats["凶课数"]}课')
        print('='*100)
        print('筛选完成')
        print('='*100)
    
    def save_results(self, results: list, output_file: str):
        """
        保存结果到文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'{self.shan}山最佳{len(results)}课\n')
            f.write(f'筛选范围：{self.stats["总天数"]}天，{self.stats["总课数"]}课\n')
            f.write('='*100 + '\n\n')
            
            for i, result in enumerate(results, 1):
                f.write(f'【第{i}名】{result["公历日期"].strftime("%Y 年%m 月%d 日")} {result["时辰"]}时\n')
                f.write(f'四柱：{result["sizhu"]["年柱"]} {result["sizhu"]["月柱"]} {result["sizhu"]["日柱"]} {result["sizhu"]["时柱"]}\n')
                f.write(f'总分：{result["总分"]:.1f}分\n')
                f.write(f'元辰得位：{"是" if result["元辰得位"] else "否"}\n')
                f.write(f'斗首格局：{", ".join([p["格局名称"] for p in result["斗首格局"]])}\n')
                f.write(f'六相统计：{result["六相统计"]}个，六替统计：{result["六替统计"]}个\n')
                f.write(f'吉课数：{result["吉课数"]}个，凶课数：{result["凶课数"]}个\n')
                f.write('\n')
        
        print(f'\n结果已保存到：{output_file}')


def main():
    """
    主函数：演示不同时间范围的筛选
    """
    print('='*100)
    print('通用全面筛选系统 - 演示')
    print('='*100)
    
    # 创建筛选器
    selector = ComprehensiveSelector(shan='壬')
    
    # 示例 1：三年范围（2026.3.24 - 2029.3.24）
    print('\n【示例 1】三年范围筛选')
    start_date = datetime(2026, 3, 24)
    end_date = datetime(2029, 3, 24)
    
    top_5 = selector.select_top_ke(start_date, end_date, top_n=5)
    selector.display_results(top_5)
    selector.save_results(top_5, os.path.join(os.path.dirname(__file__), 'top5_3years.txt'))
    
    # 示例 2：五年范围（可根据需要调整）
    # print('\n【示例 2】五年范围筛选')
    # start_date = datetime(2026, 3, 24)
    # end_date = datetime(2031, 3, 24)
    # top_5 = selector.select_top_ke(start_date, end_date, top_n=5)
    # selector.display_results(top_5)
    
    # 示例 3：十年范围（可根据需要调整）
    # print('\n【示例 3】十年范围筛选')
    # start_date = datetime(2026, 3, 24)
    # end_date = datetime(2036, 3, 24)
    # top_5 = selector.select_top_ke(start_date, end_date, top_n=5)
    # selector.display_results(top_5)
    
    print('\n' + '='*100)
    print('演示完成')
    print('='*100)
    print('\n说明：')
    print('1. 本系统适用于任何时间范围的筛选（三年、五年、十年等）')
    print('2. 严格采用逐一筛选法，确保不遗漏任何一课')
    print('3. 可根据需要调整 start_date 和 end_date 参数')
    print('4. 可根据需要调整 top_n 参数（返回前 N 个最佳课格）')
    print('='*100)


if __name__ == '__main__':
    main()
