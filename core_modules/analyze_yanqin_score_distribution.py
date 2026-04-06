#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演禽直法课格分值分布分析
统计所有课格的演禽分值分布情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from yanqin_analyzer import YanQinAnalyzer
from sizhu_engine import get_sizhu, get_day_ganzhi


class YanQinScoreAnalyzer:
    """
    演禽直法分值分布分析器
    """
    
    def __init__(self):
        """
        初始化分析器
        """
        self.yanqin_analyzer = YanQinAnalyzer()
        
        # 统计信息
        self.stats = {
            '总课数': 0,
            '分数分布': {},
            '格局分布': {},
            '禽星分布': {},
            '吉凶统计': {
                '吉': 0,
                '凶': 0,
                '平': 0
            },
            '最高分': 0,
            '最低分': 100,
            '平均分': 0,
            '总分和': 0,
            '详细课格': []
        }
    
    def analyze_all_ke(self, start_date: datetime, end_date: datetime, show_progress: bool = True):
        """
        分析所有课格的演禽分值分布
        """
        print('='*100)
        print('演禽直法课格分值分布分析')
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
        
        # 初始化分数段
        for i in range(0, 101, 5):
            self.stats['分数分布'][f'{i}-{i+4}分'] = 0
        
        current_date = start_date
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日柱干支
            day_ganzhi = get_day_ganzhi(current_date.year, current_date.month, current_date.day)
            
            # 遍历 12 个时辰
            for shichen_idx, shichen in enumerate(shichen_list):
                # 获取四柱
                sizhu = get_sizhu(current_date.year, current_date.month, current_date.day, shichen)
                
                # 演禽分析
                yanqin_result = self.yanqin_analyzer.analyze_yanqin(sizhu)
                yanqin_score = yanqin_result.get('综合评分', 0)
                
                # 获取主要信息
                siqin = yanqin_result.get('四禽', {})
                nian_qin = siqin.get('年禽', '')
                yue_qin = siqin.get('月禽', '')
                ri_qin = siqin.get('日禽', '')
                shi_qin = siqin.get('时禽', '')
                
                # 吉凶（根据宿吉凶统计）
                susong_jixiong = yanqin_result.get('二十八宿属性', {})
                ji_count = sum(1 for v in susong_jixiong.values() if v == '吉')
                xiong_count = sum(1 for v in susong_jixiong.values() if v == '凶')
                if ji_count >= 3:
                    jixiong = '吉'
                elif xiong_count >= 3:
                    jixiong = '凶'
                else:
                    jixiong = '平'
                
                # 格局
                kege = yanqin_result.get('格局判定', [])
                
                # 统计分数段
                score_range = f'{(yanqin_score // 5) * 5}-{(yanqin_score // 5) * 5 + 4}分'
                self.stats['分数分布'][score_range] += 1
                
                # 统计格局
                if kege:
                    for pattern in kege:
                        pattern_name = pattern.get('格局名称', '未知')
                        if pattern_name not in self.stats['格局分布']:
                            self.stats['格局分布'][pattern_name] = 0
                        self.stats['格局分布'][pattern_name] += 1
                else:
                    if '无格局' not in self.stats['格局分布']:
                        self.stats['格局分布']['无格局'] = 0
                    self.stats['格局分布']['无格局'] += 1
                
                # 统计禽星
                for qin_name in [nian_qin, yue_qin, ri_qin, shi_qin]:
                    if qin_name:
                        if qin_name not in self.stats['禽星分布']:
                            self.stats['禽星分布'][qin_name] = 0
                        self.stats['禽星分布'][qin_name] += 1
                
                # 统计吉凶
                if jixiong in self.stats['吉凶统计']:
                    self.stats['吉凶统计'][jixiong] += 1
                
                # 统计最高分、最低分、总分
                if yanqin_score > self.stats['最高分']:
                    self.stats['最高分'] = yanqin_score
                if yanqin_score < self.stats['最低分']:
                    self.stats['最低分'] = yanqin_score
                self.stats['总分和'] += yanqin_score
                
                # 存储详细课格信息（80 分以上）
                if yanqin_score >= 80:
                    self.stats['详细课格'].append({
                        '日期': current_date.strftime('%Y-%m-%d'),
                        '时辰': shichen,
                        '四柱': f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}",
                        '演禽评分': yanqin_score,
                        '吉凶': jixiong,
                        '年禽': nian_qin,
                        '月禽': yue_qin,
                        '日禽': ri_qin,
                        '时禽': shi_qin,
                        '格局': [p.get('格局名称', '') for p in kege]
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
        print('📊 演禽直法课格分值分布统计')
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
        for jixiong, count in self.stats['吉凶统计'].items():
            percentage = count / total * 100 if total > 0 else 0
            print(f'  {jixiong}: {count}课 ({percentage:.1f}%)')
        
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
        
        # 4. 格局分布
        print('\n【演禽格局分布】')
        print(f'  {"格局名称":<25} {"课数":>8} {"百分比":>10}')
        print('  ' + '-'*45)
        
        sorted_patterns = sorted(self.stats['格局分布'].items(), 
                                key=lambda x: x[1], 
                                reverse=True)
        
        for pattern_name, count in sorted_patterns:
            percentage = count / self.stats['总课数'] * 100
            print(f'  {pattern_name:<25} {count:>8} {percentage:>9.1f}%')
        
        # 5. 高分课格
        print('\n【高分课格（80 分以上）】')
        high_score_count = len(self.stats['详细课格'])
        print(f'  80 分以上课数：{high_score_count}课')
        
        if high_score_count > 0:
            sorted_kege = sorted(self.stats['详细课格'], 
                                key=lambda x: x['演禽评分'], 
                                reverse=True)
            
            print(f'\n  前 20 个高分课格：')
            print(f'  {"排名":<6} {"日期":<12} {"时辰":<6} {"分数":>6} {"吉凶":<6} {"格局":<25}')
            print('  ' + '-'*70)
            
            for i, kege in enumerate(sorted_kege[:20], 1):
                patterns_str = ', '.join(kege['格局'][:1])
                print(f'  {i:<6} {kege["日期"]:<12} {kege["时辰"]:<6} {kege["演禽评分"]:>6} {kege["吉凶"]:<6} {patterns_str:<25}')
    
    def save_distribution(self, output_file: str):
        """
        保存分布统计到文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('演禽直法课格分值分布统计报告\n')
            f.write('='*100 + '\n\n')
            
            f.write(f'筛选范围：{self.stats["总课数"]}课\n\n')
            
            f.write('【总体统计】\n')
            f.write(f'  总课数：{self.stats["总课数"]}课\n')
            f.write(f'  最高分：{self.stats["最高分"]}分\n')
            f.write(f'  最低分：{self.stats["最低分"]}分\n')
            f.write(f'  平均分：{self.stats["平均分"]:.1f}分\n\n')
            
            f.write('【吉凶统计】\n')
            for jixiong, count in self.stats['吉凶统计'].items():
                percentage = count / self.stats['总课数'] * 100
                f.write(f'  {jixiong}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【分数段分布】\n')
            for score_range, count in sorted(self.stats['分数分布'].items(), 
                                            key=lambda x: int(x[0].split('-')[0]), 
                                            reverse=True):
                if count > 0:
                    percentage = count / self.stats['总课数'] * 100
                    f.write(f'  {score_range}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【演禽格局分布】\n')
            for pattern_name, count in sorted(self.stats['格局分布'].items(), 
                                             key=lambda x: x[1], 
                                             reverse=True):
                percentage = count / self.stats['总课数'] * 100
                f.write(f'  {pattern_name}: {count}课 ({percentage:.1f}%)\n')
            
            f.write('\n【高分课格（80 分以上）】\n')
            f.write(f'  总数：{len(self.stats["详细课格"])}课\n\n')
            
            sorted_kege = sorted(self.stats['详细课格'], key=lambda x: x['演禽评分'], reverse=True)
            for i, kege in enumerate(sorted_kege, 1):
                f.write(f'{i}. {kege["日期"]} {kege["时辰"]}时\n')
                f.write(f'   四柱：{kege["四柱"]}\n')
                f.write(f'   评分：{kege["演禽评分"]}分 ({kege["吉凶"]})\n')
                f.write(f'   年禽：{kege["年禽"]}, 月禽：{kege["月禽"]}, 日禽：{kege["日禽"]}, 时禽：{kege["时禽"]}\n')
                f.write(f'   格局：{", ".join(kege["格局"])}\n\n')
        
        print(f'\n结果已保存到：{output_file}')


def main():
    """
    主函数
    """
    print('='*100)
    print('演禽直法课格分值分布分析 - 演示')
    print('='*100)
    
    analyzer = YanQinScoreAnalyzer()
    
    start_date = datetime(2026, 3, 24)
    end_date = datetime(2029, 3, 24)
    
    analyzer.analyze_all_ke(start_date, end_date)
    analyzer.display_distribution()
    analyzer.save_distribution(os.path.join(os.path.dirname(__file__), 'yanqin_score_distribution.txt'))
    
    print('\n' + '='*100)
    print('分析完成')
    print('='*100)


if __name__ == '__main__':
    main()
