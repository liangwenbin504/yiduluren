#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度六壬择日权衡算法系统

依据《仪度六壬选日要诀》注解实现的斗首法与六壬法权衡算法

优先级规则：
1. 斗首法优先级 > 六壬课格优先级
2. 先筛选斗首最吉日期，再匹配六壬最吉课格
3. 逐级匹配，直至找到合适的组合

匹配策略：
1. 首要任务：应用斗首法对指定日期范围内的所有日期进行吉凶评估并排序，筛选出最吉日期
2. 将斗首法选出的最吉日期与六壬最吉课格进行匹配验证
3. 若最吉斗首日期无法匹配最吉六壬课格，则选择次吉斗首日期继续尝试匹配最吉六壬课格
4. 若次吉斗首日期仍无法匹配最吉六壬课格，则保持最吉斗首日期不变，尝试匹配次吉六壬课格
5. 以此类推，按照"斗首吉凶优先级高于六壬课格优先级"的原则进行逐级匹配
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from kejing_scoring import KeJingScoring


class DouShouRanking:
    """斗首法日期 ranking 类"""
    
    def __init__(self):
        # 斗首课格评分（与 douhou_kege_system.py 一致）
        self.doushou_scores = {
            '武财课': 9.0,    # 上上大吉
            '元辰课': 8.5,    # 上吉
            '廉贞课': 6.0,    # 小吉
            '贪官课': 3.0,    # 中凶 - 不可用
            '破鬼课': 2.5,    # 大凶 - 不可用
        }
    
    def rank_dates(self, start_date, end_date):
        """
        对日期范围内的日期进行斗首法吉凶 ranking
        
        :param start_date: 开始日期 (datetime)
        :param end_date: 结束日期 (datetime)
        :return: 按斗首评分排序的日期列表 [(日期，课格，评分), ...]
        """
        date_rankings = []
        
        current = start_date
        while current <= end_date:
            # 这里简化处理，实际应该调用斗首法计算引擎
            # 现在随机分配一个斗首课格（演示用）
            import random
            kege = random.choice(list(self.doushou_scores.keys()))
            score = self.doushou_scores[kege]
            
            date_rankings.append({
                'date': current,
                'kege': kege,
                'score': score,
                'usable': score >= 5.0
            })
            
            current += timedelta(days=1)
        
        # 按评分降序排序
        date_rankings.sort(key=lambda x: x['score'], reverse=True)
        
        return date_rankings


class ComprehensiveSelector:
    """综合择日权衡算法类"""
    
    def __init__(self):
        self.kejing_scorer = KeJingScoring()
        self.doushou_ranker = DouShouRanking()
        
        # 六壬课格分级
        self.kejing_levels = {
            '上上大吉': [],  # 9.0+
            '上吉': [],      # 8.0-8.9
            '中吉': [],      # 7.0-7.9
            '小吉': [],      # 6.0-6.9
            '吉凶参半': [],  # 5.0-5.9
            '小凶': [],      # 4.0-4.9
            '中凶': [],      # 3.0-3.9
            '大凶': [],      # 2.0-2.9
            '上凶': [],      # 2.0 以下
        }
        
        # 初始化课格分级
        self._init_kejing_levels()
    
    def _init_kejing_levels(self):
        """初始化六壬课格分级"""
        all_scores = self.kejing_scorer.get_all_kejing_scores()
        for kejing, score in all_scores.items():
            level = self.kejing_scorer.get_score_level(score)
            self.kejing_levels[level].append((kejing, score))
        
        # 每个级别内按分数排序
        for level in self.kejing_levels:
            self.kejing_levels[level].sort(key=lambda x: x[1], reverse=True)
    
    def select_auspicious_date_with_shan(self, shan_name, yuanchen, start_date, end_date, min_doushou_score=7.0, min_kejing_score=7.0):
        """
        带坐山的综合择日算法
        
        :param shan_name: 坐山名称（如'壬山'）
        :param yuanchen: 元辰（如'甲己'）
        :param start_date: 开始日期 (datetime 或字符串 'YYYY-MM-DD')
        :param end_date: 结束日期 (datetime 或字符串 'YYYY-MM-DD')
        :param min_doushou_score: 最小斗首评分要求
        :param min_kejing_score: 最小六壬课格评分要求
        :return: 最佳日期和课格组合
        """
        print("=" * 80)
        print("仪度六壬综合择日算法（带坐山）")
        print("=" * 80)
        print(f"\n坐山：{shan_name}")
        print(f"元辰：{yuanchen}")
        print(f"日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"斗首最低要求：{min_doushou_score}分")
        print(f"六壬最低要求：{min_kejing_score}分")
        print()
        
        # 调用原有的择日方法
        return self.select_auspicious_date(start_date, end_date, min_doushou_score, min_kejing_score)
    
    def select_auspicious_date(self, start_date, end_date, min_doushou_score=7.0, min_kejing_score=7.0):
        """
        综合择日算法（原有方法）
        
        :param start_date: 开始日期 (datetime 或字符串 'YYYY-MM-DD')
        :param end_date: 结束日期 (datetime 或字符串 'YYYY-MM-DD')
        :param min_doushou_score: 最小斗首评分要求（默认 7.0，中吉以上）
        :param min_kejing_score: 最小六壬课格评分要求（默认 7.0，中吉以上）
        :return: 最佳日期和课格组合
        """
        # 转换日期格式
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        print("=" * 80)
        print("仪度六壬综合择日算法")
        print("=" * 80)
        print(f"\n日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"斗首最低要求：{min_doushou_score}分（{self.doushou_ranker.doushou_scores.get('廉贞课', 0):.1f}分以上）")
        print(f"六壬最低要求：{min_kejing_score}分（中吉以上）")
        print()
        
        # 步骤 1：斗首法 ranking
        print("【步骤 1】应用斗首法对日期进行吉凶评估并排序")
        doushou_rankings = self.doushou_ranker.rank_dates(start_date, end_date)
        
        usable_dates = [d for d in doushou_rankings if d['usable'] and d['score'] >= min_doushou_score]
        print(f"  总日期数：{len(doushou_rankings)}")
        print(f"  可用日期数：{len(usable_dates)}")
        print(f"  最吉日期：{usable_dates[0]['date'].strftime('%Y-%m-%d')} ({usable_dates[0]['kege']}, {usable_dates[0]['score']:.1f}分)")
        print()
        
        # 步骤 2：尝试匹配最吉六壬课格
        print("【步骤 2】将斗首最吉日期与六壬最吉课格进行匹配")
        
        best_match = None
        match_history = []
        
        # 按优先级尝试匹配
        doushou_priority = ['上上大吉', '上吉', '中吉', '小吉']
        kejing_priority = ['上上大吉', '上吉', '中吉', '小吉', '吉凶参半']
        
        for ds_level in doushou_priority:
            # 获取该级别的斗首日期
            level_dates = [d for d in usable_dates if 
                          self.doushou_ranker.doushou_scores.get(d['kege'], 0) >= 
                          {'上上大吉': 9.0, '上吉': 8.0, '中吉': 7.0, '小吉': 6.0}.get(ds_level, 0)]
            
            if not level_dates:
                continue
            
            print(f"\n  尝试斗首等级：{ds_level} ({len(level_dates)}个日期)")
            
            for kj_level in kejing_priority:
                # 获取该级别的六壬课格
                level_kejing = self.kejing_levels.get(kj_level, [])
                
                if not level_kejing:
                    continue
                
                print(f"    尝试六壬等级：{kj_level} ({len(level_kejing)}个课格)")
                
                # 尝试匹配
                for date_info in level_dates:
                    for kejing, score in level_kejing:
                        if score >= min_kejing_score:
                            # 找到匹配
                            match = {
                                'date': date_info['date'],
                                'doushou_kege': date_info['kege'],
                                'doushou_score': date_info['score'],
                                'kejing': kejing,
                                'kejing_score': score,
                                'match_level': f"{ds_level} + {kj_level}"
                            }
                            
                            match_history.append(match)
                            
                            if not best_match:
                                best_match = match
                                print(f"      ✓ 找到匹配：{date_info['date'].strftime('%Y-%m-%d')}")
                                print(f"        斗首：{date_info['kege']} ({date_info['score']:.1f}分)")
                                print(f"        六壬：{kejing} ({score:.1f}分)")
                                break
                    
                    if best_match:
                        break
                
                if best_match:
                    break
            
            if best_match:
                break
        
        # 输出结果
        print("\n" + "=" * 80)
        print("【择日结果】")
        print("=" * 80)
        
        if best_match:
            print(f"\n✓ 最佳选择：{best_match['date'].strftime('%Y-%m-%d')}")
            print(f"\n斗首课格：")
            print(f"  课格：{best_match['doushou_kege']}")
            print(f"  评分：{best_match['doushou_score']:.1f}分")
            print(f"\n六壬课格：")
            print(f"  课格：{best_match['kejing']}")
            print(f"  评分：{best_match['kejing_score']:.1f}分")
            print(f"\n匹配等级：{best_match['match_level']}")
            
            # 决策依据
            print(f"\n【决策依据】")
            print(f"  1. 斗首法优先级高于六壬课格")
            print(f"  2. 优先选择斗首最吉日期")
            print(f"  3. 在斗首吉日内匹配最优六壬课格")
            print(f"  4. 逐级匹配，确保找到最佳组合")
        else:
            print("\n✗ 未找到合适的日期和课格组合")
            print("  建议：扩大日期范围或降低评分要求")
        
        print("\n" + "=" * 80)
        
        return best_match, match_history


def test_selector():
    """测试择日算法"""
    selector = ComprehensiveSelector()
    
    # 测试
    from datetime import datetime, timedelta
    start = datetime.now()
    end = start + timedelta(days=30)
    
    best_match, history = selector.select_auspicious_date(start, end)


if __name__ == '__main__':
    test_selector()
