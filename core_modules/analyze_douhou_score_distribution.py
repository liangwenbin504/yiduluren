#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首课格分值分布分析
统计所有课格的斗首分值分布情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from douhou_analyzer import DouhouKegeAnalyzer
from liuxiang_liuti_correct import LiuXiangLiuTiCorrect
from sizhu_engine import get_sizhu, get_day_ganzhi
import json


class DouhouScoreAnalyzer:
    """
    斗首课格分值分布分析器
    """
    
    def __init__(self, shan: str = '壬'):
        """
        初始化分析器
        :param shan: 坐山
        """
        self.shan = shan
        self.douhou_analyzer = DouhouKegeAnalyzer()
        self.liuxiang_system = LiuXiangLiuTiCorrect()
        
        # 统计信息
        self.stats = {
            '总课数': 0,
            '分数分布': {},  # 每个分数段的课数
            '格局分布': {},  # 每种格局的课数
            '元辰得位统计': {
                '得位': 0,
                '不得位': 0
            },
            '最高分': 0,
            '最低分': 100,
            '平均分': 0,
            '总分和': 0,
            '详细课格': []  # 存储所有课格信息
        }
    
    def analyze_all_ke(self, start_date: datetime, end_date: datetime, show_progress: bool = True):
        """
        分析所有课格的分值分布
        """
        print('='*100)
        print('斗首课格分值分布分析')
        print('='*100)
        print(f'筛选范围：{start_date.strftime("%Y 年%m 月%d 日")} 至 {end_date.strftime("%Y 年%m 月%d 日")}')
        print(f'坐山：{self.shan}山')
        print('='*100)
        
        # 计算总课数
        total_days = (end_date - start_date).days + 1
        total_ke = total_days * 12
        
        print(f'\n总天数：{total_days}天')
        print(f'总课数：{total_ke}课\n')
        print('开始分析...\n')
        
        # 时辰地支
        shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        current_date = start_date
        day_count = 0
        
        # 初始化分数段
        for i in range(0, 101, 5):
            self.stats['分数分布'][f'{i}-{i+4}分'] = 0
        
        # 逐一分析
        while current_date <= end_date:
            day_count += 1
            
            # 获取日柱干支
            day_ganzhi = get_day_ganzhi(current_date.year, current_date.month, current_date.day)
            
            # 遍历 12 个时辰
            for shichen_idx, shichen in enumerate(shichen_list):
                # 获取四柱
                sizhu = get_sizhu(current_date.year, current_date.month, current_date.day, shichen)
                
                # 斗首分析
                douhou_result = self.douhou_analyzer.analyze_kege(self.shan, sizhu)
                douhou_score = douhou_result['综合评分']
                
                # 检查元辰得位
                yuanchen_positions = []
                for pillar_name, ganzhi in sizhu.items():
                    tiangan = ganzhi[0]
                    huaqi = self.liuxiang_system.get_huaqi(tiangan)
                    if huaqi == '土':
                        yuanchen_positions.append(pillar_name)
                
                yuanchen_dewei = len(yuanchen_positions) >= 1
                
                # 统计分数段
                score_range = f'{(douhou_score // 5) * 5}-{(douhou_score // 5) * 5 + 4}分'
                self.stats['分数分布'][score_range] += 1
                
                # 统计格局
                patterns = douhou_result.get('课格格局', [])
                if patterns:
                    for pattern in patterns:
                        pattern_name = pattern['格局名称']
                        if pattern_name not in self.stats['格局分布']:
                            self.stats['格局分布'][pattern_name] = 0
                        self.stats['格局分布'][pattern_name] += 1
                else:
                    if '无格局' not in self.stats['格局分布']:
                        self.stats['格局分布']['无格局'] = 0
                    self.stats['格局分布']['无格局'] += 1
                
                # 统计元辰得位
                if yuanchen_dewei:
                    self.stats['元辰得位统计']['得位'] += 1
                else:
                    self.stats['元辰得位统计']['不得位'] += 1
                
                # 统计最高分、最低分、总分
                if douhou_score > self.stats['最高分']:
                    self.stats['最高分'] = douhou_score
                if douhou_score < self.stats['最低分']:
                    self.stats['最低分'] = douhou_score
                self.stats['总分和'] += douhou_score
                
                # 存储详细课格信息（只存储 80 分以上的）
                if douhou_score >= 80:
                    self.stats['详细课格'].append({
                        '日期': current_date.strftime('%Y-%m-%d'),
                        '时辰': shichen,
                        '四柱': f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}",
                        '斗首评分': douhou_score,
                        '元辰得位': yuanchen_dewei,
                        '元辰位置': yuanchen_positions,
                        '格局': [p['格局名称'] for p in patterns]
                    })
                
                self.stats['总课数'] += 1
            
            # 进度显示
            if show_progress and day_count % 100 == 0:
                progress = day_count / total_days * 100
                print(f"已分析 {day_count}/{total_days} 天 ({progress:.1f}%)")
            
            current_date += timedelta(days=1)
        
        # 计算平均分
        self.stats['平均分'] = self.stats['总分和'] / self.stats['总课数'] if self.stats['总课数'] > 0 else 0
        
        print(f'\n分析完成！共分析 {self.stats["总课数"]} 个课格')
    
    def display_distribution(self):
        """
        显示分值分布
        """
        print('\n' + '='*100)
        print('📊 斗首课格分值分布统计')
        print('='*100)
        
        # 1. 总体统计
        print('\n【总体统计】')
        print(f'  总课数：{self.stats["总课数"]}课')
        print(f'  最高分：{self.stats["最高分"]}分')
        print(f'  最低分：{self.stats["最低分"]}分')
        print(f'  平均分：{self.stats["平均分"]:.1f}分')
        
        # 2. 元辰得位统计
        print('\n【元辰得位统计】')
        dewei = self.stats['元辰得位统计']['得位']
        buwei = self.stats['元辰得位统计']['不得位']
        total = dewei + buwei
        print(f'  元辰得位：{dewei}课 ({dewei/total*100:.1f}%)')
        print(f'  元辰不得位：{buwei}课 ({buwei/total*100:.1f}%)')
        
        # 3. 分数段分布
        print('\n【分数段分布】')
        print(f'  {"分数段":<12} {"课数":>8} {"百分比":>10} {"直方图":<40}')
        print('  ' + '-'*70)
        
        # 按分数段排序显示
        sorted_ranges = sorted(self.stats['分数分布'].items(), 
                              key=lambda x: int(x[0].split('-')[0]), 
                              reverse=True)
        
        for score_range, count in sorted_ranges:
            if count > 0:  # 只显示有课数的分数段
                percentage = count / self.stats['总课数'] * 100
                # 绘制简易直方图
                bar_length = int(percentage / 2)  # 每 2% 一个#
                bar = '#' * bar_length
                print(f'  {score_range:<12} {count:>8} {percentage:>9.1f}% {bar:<40}')
        
        # 4. 格局分布
        print('\n【斗首格局分布】')
        print(f'  {"格局名称":<20} {"课数":>8} {"百分比":>10}')
        print('  ' + '-'*40)
        
        # 按课数排序
        sorted_patterns = sorted(self.stats['格局分布'].items(), 
                                key=lambda x: x[1], 
                                reverse=True)
        
        for pattern_name, count in sorted_patterns:
            percentage = count / self.stats['总课数'] * 100
            print(f'  {pattern_name:<20} {count:>8} {percentage:>9.1f}%')
        
        # 5. 高分课格（80 分以上）
        print('\n【高分课格（80 分以上）】')
        high_score_count = len(self.stats['详细课格'])
        print(f'  80 分以上课数：{high_score_count}课')
        
        if high_score_count > 0:
            # 按分数排序
            sorted_kege = sorted(self.stats['详细课格'], 
                                key=lambda x: x['斗首评分'], 
                                reverse=True)
            
            # 显示前 20 个
            print(f'\n  前 20 个高分课格：')
            print(f'  {"排名":<6} {"日期":<12} {"时辰":<6} {"四柱":<25} {"分数":>6} {"格局":<20}')
            print('  ' + '-'*90)
            
            for i, kege in enumerate(sorted_kege[:20], 1):
                patterns_str = ', '.join(kege['格局'][:2])  # 只显示前两个格局
                print(f'  {i:<6} {kege["日期"]:<12} {kege["时辰"]:<6} {kege["四柱"]:<25} {kege["斗首评分"]:>6} {patterns_str:<20}')
    
    def save_distribution(self, output_file: str):
        """
        保存分布统计到文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('斗首课格分值分布统计报告\n')
            f.write('='*100 + '\n\n')
            
            f.write(f'筛选范围：{self.stats["总课数"]}课\n')
            f.write(f'坐山：{self.shan}山\n\n')
            
            f.write('【总体统计】\n')
            f.write(f'  总课数：{self.stats["总课数"]}课\n')
            f.write(f'  最高分：{self.stats["最高分"]}分\n')
            f.write(f'  最低分：{self.stats["最低分"]}分\n')
            f.write(f'  平均分：{self.stats["平均分"]:.1f}分\n\n')
            
            f.write('【元辰得位统计】\n')
            f.write(f'  元辰得位：{self.stats["元辰得位统计"]["得位"]}课\n')
            f.write(f'  元辰不得位：{self.stats["元辰得位统计"]["不得位"]}课\n\n')
            
            f.write('【分数段分布】\n')
            for score_range, count in sorted(self.stats['分数分布'].items(), 
                                            key=lambda x: int(x[0].split('-')[0]), 
                                            reverse=True):
                if count > 0:
                    percentage = count / self.stats['总课数'] * 100
                    f.write(f'  {score_range}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【斗首格局分布】\n')
            for pattern_name, count in sorted(self.stats['格局分布'].items(), 
                                             key=lambda x: x[1], 
                                             reverse=True):
                percentage = count / self.stats['总课数'] * 100
                f.write(f'  {pattern_name}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【高分课格（80 分以上）】\n')
            f.write(f'  总数：{len(self.stats["详细课格"])}课\n\n')
            
            # 保存所有高分课格
            sorted_kege = sorted(self.stats['详细课格'], key=lambda x: x['斗首评分'], reverse=True)
            for i, kege in enumerate(sorted_kege, 1):
                f.write(f'{i}. {kege["日期"]} {kege["时辰"]}时\n')
                f.write(f'   四柱：{kege["四柱"]}\n')
                f.write(f'   分数：{kege["斗首评分"]}分\n')
                f.write(f'   元辰得位：{"是" if kege["元辰得位"] else "否"}\n')
                f.write(f'   格局：{", ".join(kege["格局"])}\n\n')
        
        print(f'\n结果已保存到：{output_file}')


def main():
    """
    主函数
    """
    print('='*100)
    print('斗首课格分值分布分析 - 演示')
    print('='*100)
    
    # 创建分析器
    analyzer = DouhouScoreAnalyzer(shan='壬')
    
    # 分析三年范围
    start_date = datetime(2026, 3, 24)
    end_date = datetime(2029, 3, 24)
    
    analyzer.analyze_all_ke(start_date, end_date)
    analyzer.display_distribution()
    analyzer.save_distribution(os.path.join(os.path.dirname(__file__), 'douhou_score_distribution.txt'))
    
    print('\n' + '='*100)
    print('分析完成')
    print('='*100)


if __name__ == '__main__':
    main()
