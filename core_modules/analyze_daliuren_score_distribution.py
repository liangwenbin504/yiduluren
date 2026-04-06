#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬课格课体吉凶分值分布分析（简化版）
基于 64 课课经规则进行统计分析
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from typing import Dict
from daliuren_64ke_rules import KE_JING_64
from sizhu_engine import get_sizhu, get_day_ganzhi


class DaLiuRenScoreAnalyzer:
    """
    大六壬课格分值分布分析器（简化版）
    基于日干支直接推导课体
    """
    
    def __init__(self):
        """
        初始化分析器
        """
        # 统计信息
        self.stats = {
            '总课数': 0,
            '分数分布': {},
            '课体分布': {},
            '吉凶统计': {
                '大吉': 0,
                '中吉': 0,
                '小吉': 0,
                '平': 0,
                '小凶': 0,
                '中凶': 0,
                '大凶': 0
            },
            '最高分': 0,
            '最低分': 100,
            '平均分': 0,
            '总分和': 0,
            '详细课格': []
        }
        
        # 初始化分数段
        for i in range(0, 101, 5):
            self.stats['分数分布'][f'{i}-{i+4}分'] = 0
    
    def get_ke_ti_from_ganzhi(self, ri_gan: str, ri_zhi: str, shi_chen: str) -> Dict:
        """
        根据日干支和时辰简化推导课体
        这是一个简化模型，基于传统规则
        """
        # 简化规则：根据日干支和时辰关系判断课体
        # 实际应使用完整的起课方法
        
        # 伏吟课：月将=占时（简化为日支=时辰）
        if ri_zhi == shi_chen:
            return KE_JING_64.get('伏吟课', {})
        
        # 返吟课：日支冲时辰（简化）
        chong_map = {'子': '午', '丑': '未', '寅': '申', '卯': '酉', 
                     '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
                     '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'}
        if chong_map.get(ri_zhi) == shi_chen:
            return KE_JING_64.get('返吟课', {})
        
        # 其他课体随机分布（简化处理）
        # 实际应根据四课三传推导
        import random
        random.seed(hash(f"{ri_gan}{ri_zhi}{shi_chen}"))
        
        ke_ti_list = list(KE_JING_64.keys())
        selected_ke = random.choice(ke_ti_list)
        return KE_JING_64.get(selected_ke, {})
    
    def analyze_all_ke(self, start_date: datetime, end_date: datetime, show_progress: bool = True):
        """
        分析所有课格的大六壬分值分布
        """
        print('='*100)
        print('大六壬课格课体吉凶分值分布分析')
        print('='*100)
        print(f'筛选范围：{start_date.strftime("%Y 年%m 月%d 日")} 至 {end_date.strftime("%Y 年%m 月%d 日")}')
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
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日柱干支
            day_ganzhi = get_day_ganzhi(current_date.year, current_date.month, current_date.day)
            ri_gan = day_ganzhi[0]
            ri_zhi = day_ganzhi[1]
            
            # 遍历 12 个时辰
            for shichen in shichen_list:
                # 获取四柱
                sizhu = get_sizhu(current_date.year, current_date.month, current_date.day, shichen)
                
                # 推导课体
                ke_ti_result = self.get_ke_ti_from_ganzhi(ri_gan, ri_zhi, shichen)
                
                # 获取评分和吉凶
                ke_ti_name = ke_ti_result.get('code', 0)  # 课体名称
                base_score = ke_ti_result.get('base_score', 50)
                ji_xiong = ke_ti_result.get('jixiong', '平')
                
                # 映射吉凶等级
                ji_xiong_map = {
                    '大吉': '大吉', '中吉': '中吉', '小吉': '小吉',
                    '吉': '小吉', '平': '平',
                    '凶': '小凶', '大凶': '大凶'
                }
                ji_xiong_level = ji_xiong_map.get(ji_xiong, '平')
                
                # 统计分数段
                score_range = f'{(base_score // 5) * 5}-{(base_score // 5) * 5 + 4}分'
                if score_range in self.stats['分数分布']:
                    self.stats['分数分布'][score_range] += 1
                
                # 统计课体
                if ke_ti_name:
                    if ke_ti_name not in self.stats['课体分布']:
                        self.stats['课体分布'][ke_ti_name] = 0
                    self.stats['课体分布'][ke_ti_name] += 1
                
                # 统计吉凶
                if ji_xiong_level in self.stats['吉凶统计']:
                    self.stats['吉凶统计'][ji_xiong_level] += 1
                
                # 统计最高分、最低分、总分
                if base_score > self.stats['最高分']:
                    self.stats['最高分'] = base_score
                if base_score < self.stats['最低分']:
                    self.stats['最低分'] = base_score
                self.stats['总分和'] += base_score
                
                # 存储详细课格信息（80 分以上）
                if base_score >= 80:
                    self.stats['详细课格'].append({
                        '日期': current_date.strftime('%Y-%m-%d'),
                        '时辰': shichen,
                        '四柱': f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}",
                        '大六壬评分': base_score,
                        '吉凶等级': ji_xiong_level,
                        '课体': ke_ti_name
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
        print('📊 大六壬课格课体吉凶分值分布统计')
        print('='*100)
        
        # 1. 总体统计
        print('\n【总体统计】')
        print(f'  总课数：{self.stats["总课数"]}课')
        print(f'  最高分：{self.stats["最高分"]}分')
        print(f'  最低分：{self.stats["最低分"]}分')
        print(f'  平均分：{self.stats["平均分"]:.1f}分')
        
        # 2. 吉凶统计
        print('\n【吉凶统计】')
        total = sum(self.stats['吉凶统计'].values())
        for ji_xiong, count in self.stats['吉凶统计'].items():
            percentage = count / total * 100 if total > 0 else 0
            print(f'  {ji_xiong}: {count}课 ({percentage:.1f}%)')
        
        # 3. 分数段分布
        print('\n【分数段分布】')
        print(f'  {"分数段":<12} {"课数":>8} {"百分比":>10} {"直方图":<40}')
        print('  ' + '-'*70)
        
        sorted_ranges = sorted(self.stats['分数分布'].items(), 
                              key=lambda x: int(x[0].split('-')[0]), 
                              reverse=True)
        
        for score_range, count in sorted_ranges:
            if count > 0:
                percentage = count / self.stats['总课数'] * 100
                bar_length = int(percentage / 2)
                bar = '#' * bar_length
                print(f'  {score_range:<12} {count:>8} {percentage:>9.1f}% {bar:<40}')
        
        # 4. 课体分布
        print('\n【大六壬课体分布（前 15）】')
        print(f'  {"课体名称":<15} {"课数":>8} {"百分比":>10}')
        print('  ' + '-'*35)
        
        sorted_keti = sorted(self.stats['课体分布'].items(), 
                            key=lambda x: x[1], 
                            reverse=True)
        
        for keti_name, count in sorted_keti[:15]:
            percentage = count / self.stats['总课数'] * 100
            print(f'  {keti_name:<15} {count:>8} {percentage:>9.1f}%')
        
        # 5. 高分课格
        print('\n【高分课格（80 分以上）】')
        high_score_count = len(self.stats['详细课格'])
        print(f'  80 分以上课数：{high_score_count}课')
        
        if high_score_count > 0:
            sorted_kege = sorted(self.stats['详细课格'], 
                                key=lambda x: x['大六壬评分'], 
                                reverse=True)
            
            print(f'\n  前 20 个高分课格：')
            print(f'  {"排名":<6} {"日期":<12} {"时辰":<6} {"分数":>6} {"吉凶":<8} {"课体":<10}')
            print('  ' + '-'*60)
            
            for i, kege in enumerate(sorted_kege[:20], 1):
                print(f'  {i:<6} {kege["日期"]:<12} {kege["时辰"]:<6} {kege["大六壬评分"]:>6} {kege["吉凶等级"]:<8} {kege["课体"]:<10}')
    
    def save_distribution(self, output_file: str):
        """
        保存分布统计到文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('大六壬课格课体吉凶分值分布统计报告\n')
            f.write('='*100 + '\n\n')
            
            f.write(f'筛选范围：{self.stats["总课数"]}课\n\n')
            
            f.write('【总体统计】\n')
            f.write(f'  总课数：{self.stats["总课数"]}课\n')
            f.write(f'  最高分：{self.stats["最高分"]}分\n')
            f.write(f'  最低分：{self.stats["最低分"]}分\n')
            f.write(f'  平均分：{self.stats["平均分"]:.1f}分\n\n')
            
            f.write('【吉凶统计】\n')
            for ji_xiong, count in self.stats['吉凶统计'].items():
                percentage = count / self.stats['总课数'] * 100
                f.write(f'  {ji_xiong}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【分数段分布】\n')
            for score_range, count in sorted(self.stats['分数分布'].items(), 
                                            key=lambda x: int(x[0].split('-')[0]), 
                                            reverse=True):
                if count > 0:
                    percentage = count / self.stats['总课数'] * 100
                    f.write(f'  {score_range}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【大六壬课体分布（前 20）】\n')
            for keti_name, count in sorted(self.stats['课体分布'].items(), 
                                          key=lambda x: x[1], 
                                          reverse=True)[:20]:
                percentage = count / self.stats['总课数'] * 100
                f.write(f'  {keti_name}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【高分课格（80 分以上）】\n')
            f.write(f'  总数：{len(self.stats["详细课格"])}课\n\n')
            
            sorted_kege = sorted(self.stats['详细课格'], key=lambda x: x['大六壬评分'], reverse=True)
            for i, kege in enumerate(sorted_kege[:50], 1):
                f.write(f'{i}. {kege["日期"]} {kege["时辰"]}时\n')
                f.write(f'   四柱：{kege["四柱"]}\n')
                f.write(f'   评分：{kege["大六壬评分"]}分 ({kege["吉凶等级"]})\n')
                f.write(f'   课体：{kege["课体"]}\n\n')
        
        print(f'\n结果已保存到：{output_file}')


def main():
    """
    主函数
    """
    print('='*100)
    print('大六壬课格课体吉凶分值分布分析 - 演示')
    print('='*100)
    
    analyzer = DaLiuRenScoreAnalyzer()
    
    start_date = datetime(2026, 3, 24)
    end_date = datetime(2029, 3, 24)
    
    analyzer.analyze_all_ke(start_date, end_date)
    analyzer.display_distribution()
    analyzer.save_distribution(os.path.join(os.path.dirname(__file__), 'daliuren_score_distribution.txt'))
    
    print('\n' + '='*100)
    print('分析完成')
    print('='*100)


if __name__ == '__main__':
    main()
