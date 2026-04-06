#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
精确年月日时吉凶计算引擎

基于斗首法和六壬法的精确吉凶计算
计算到每年、每月、每日、每时的吉凶情况
"""

from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from ganzhi_calendar import get_sizhu_accurate


class PreciseAuspicousCalculator:
    """精确吉凶计算器"""
    
    def __init__(self):
        # 斗首课格评分
        self.doushou_scores = {
            '武财课': 9.0,    # 上上大吉
            '元辰课': 8.5,    # 上吉
            '廉贞课': 6.0,    # 小吉
            '贪官课': 3.0,    # 中凶
            '破鬼课': 2.5,    # 大凶
        }
        
        # 六壬课格基础分
        self.kejing_base_scores = {
            '龙德': 9.5, '天赦': 9.5, '三光': 9.3,
            '天德': 8.8, '月德': 8.8, '玉堂': 8.5,
            '生气': 7.8, '青龙': 7.8, '解神': 7.6,
            '伏吟': 5.5, '反吟': 5.3,
            '丧门': 2.5, '白虎': 2.3,
        }
    
    def calculate_year_fortune(self, year: int) -> dict:
        """
        计算流年吉凶
        
        :param year: 年份
        :return: 流年吉凶信息
        """
        # 年柱
        year_ganzhi = get_sizhu_accurate(year, 1, 1, 12)['年柱']
        
        # 年支太岁
        year_zhi = year_ganzhi[1]
        
        # 太岁吉凶判断（简化）
        if year_zhi in ['子', '午', '卯', '酉']:  # 四正
            year_score = 7.5  # 中吉
            year_desc = "四正之年，平稳发展"
        elif year_zhi in ['寅', '申', '巳', '亥']:  # 四生
            year_score = 8.0  # 上吉
            year_desc = "四生之地，生机勃勃"
        else:  # 四库
            year_score = 7.0  # 中平
            year_desc = "四库之年，宜守不宜攻"
        
        return {
            '年份': year,
            '年柱': year_ganzhi,
            '评分': year_score,
            '吉凶': self._get_jixiong_desc(year_score),
            '说明': year_desc
        }
    
    def calculate_month_fortune(self, year: int, month: int) -> dict:
        """
        计算流月吉凶
        
        :param year: 年份
        :param month: 月份（1-12）
        :return: 流月吉凶信息
        """
        sizhu = get_sizhu_accurate(year, month, 15, 12)
        month_ganzhi = sizhu['月柱']
        
        # 月令吉凶（简化）
        month_zhi = month_ganzhi[1]
        
        # 月建与年支关系
        year_ganzhi = get_sizhu_accurate(year, 1, 1, 12)['年柱']
        year_zhi = year_ganzhi[1]
        
        # 三合六合为吉，冲刑为凶
        san_he = {
            '子': '申辰', '丑': '巳酉', '寅': '午戌', '卯': '亥未',
            '辰': '子申', '巳': '酉丑', '午': '寅戌', '未': '亥卯',
            '申': '子辰', '酉': '巳丑', '戌': '午寅', '亥': '卯未'
        }
        
        if month_zhi in san_he.get(year_zhi, ''):
            month_score = 8.5  # 三合月，上吉
            month_desc = "三合月，吉利"
        elif month_zhi == year_zhi:
            month_score = 7.5  # 建月，中吉
            month_desc = "建月，平稳"
        elif self._is_chong(month_zhi, year_zhi):
            month_score = 4.0  # 冲月，小凶
            month_desc = "冲太岁月，需谨慎"
        else:
            month_score = 6.5  # 平月
            month_desc = "平月，无特殊"
        
        return {
            '年月': f"{year}年{month}月",
            '月柱': month_ganzhi,
            '评分': month_score,
            '吉凶': self._get_jixiong_desc(month_score),
            '说明': month_desc
        }
    
    def calculate_day_fortune(self, year: int, month: int, day: int, shan_name: str = None) -> dict:
        """
        计算流日吉凶（精确到日）
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param shan_name: 坐山名称（可选）
        :return: 流日吉凶信息
        """
        sizhu = get_sizhu_accurate(year, month, day, 12)
        day_ganzhi = sizhu['日柱']
        
        # 1. 日柱本身吉凶
        day_zhi = day_ganzhi[1]
        month_ganzhi = sizhu['月柱']
        month_zhi = month_ganzhi[1]
        
        # 2. 建除十二神（简化版）
        jianchu = self._calculate_jianchu(day_zhi, month_zhi)
        jianchu_score = self._get_jianchu_score(jianchu)
        
        # 3. 斗首课格（如果有坐山）
        doushou_score = 6.0  # 默认
        doushou_kege = "平课"
        if shan_name:
            doushou_info = self._calculate_doushou_day(day_ganzhi, shan_name)
            doushou_score = doushou_info['score']
            doushou_kege = doushou_info['kege']
        
        # 4. 综合评分（加权平均）
        day_score = (
            jianchu_score * 0.4 +  # 建除 40%
            doushou_score * 0.6    # 斗首 60%
        )
        
        return {
            '日期': f"{year}-{month:02d}-{day:02d}",
            '日柱': day_ganzhi,
            '建除': jianchu,
            '斗首课格': doushou_kege,
            '评分': round(day_score, 1),
            '吉凶': self._get_jixiong_desc(day_score),
            '说明': f"建除：{jianchu}，斗首：{doushou_kege}"
        }
    
    def calculate_hour_fortune(self, year: int, month: int, day: int, hour: int, shan_name: str = None) -> dict:
        """
        计算流时吉凶（精确到时）
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时（0-23）
        :param shan_name: 坐山（可选）
        :return: 流时吉凶信息
        """
        sizhu = get_sizhu_accurate(year, month, day, hour)
        hour_ganzhi = sizhu['时柱']
        
        # 时柱吉凶
        hour_zhi = hour_ganzhi[1]
        day_ganzhi = sizhu['日柱']
        day_zhi = day_ganzhi[1]
        
        # 时辰吉凶（简化）
        if hour_zhi in ['子', '午', '卯', '酉']:  # 四正时
            hour_score = 7.5
            hour_desc = "四正时，吉利"
        elif hour_zhi in ['寅', '申', '巳', '亥']:  # 四生时
            hour_score = 7.0
            hour_desc = "四生时，平稳"
        else:  # 四库时
            hour_score = 6.5
            hour_desc = "四库时，平"
        
        # 结合日支
        if self._is_chong(hour_zhi, day_zhi):
            hour_score -= 2.0  # 冲日支，减分
            hour_desc += "，但冲日支"
        
        return {
            '时辰': f"{hour:02d}:00-{(hour+2)%24:02d}:00",
            '时柱': hour_ganzhi,
            '评分': round(hour_score, 1),
            '吉凶': self._get_jixiong_desc(hour_score),
            '说明': hour_desc
        }
    
    def _calculate_jianchu(self, day_zhi: str, month_zhi: str) -> str:
        """计算建除十二神（简化）"""
        # 月建起建
        jianchu_list = ['建', '除', '满', '平', '定', '执',
                       '破', '危', '成', '收', '开', '闭']
        
        # 月支对应建日地支
        month_to_jian = {
            '寅': '寅', '卯': '卯', '辰': '辰', '巳': '巳',
            '午': '午', '未': '未', '申': '申', '酉': '酉',
            '戌': '戌', '亥': '亥', '子': '子', '丑': '丑'
        }
        
        jian_zhi = month_to_jian.get(month_zhi, '寅')
        zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        jian_index = zhi_list.index(jian_zhi)
        day_index = zhi_list.index(day_zhi)
        
        offset = (day_index - jian_index) % 12
        return jianchu_list[offset]
    
    def _get_jianchu_score(self, jianchu: str) -> float:
        """建除十二神评分"""
        scores = {
            '建': 7.5, '除': 8.0, '满': 7.0, '平': 7.0,
            '定': 8.0, '执': 7.5, '破': 4.0, '危': 6.0,
            '成': 8.5, '收': 7.5, '开': 9.0, '闭': 6.5
        }
        return scores.get(jianchu, 6.5)
    
    def _calculate_doushou_day(self, day_ganzhi: str, shan_name: str) -> dict:
        """计算日斗首课格（简化）"""
        # 根据日干与山家关系确定课格
        day_gan = day_ganzhi[0]
        
        # 二十四山元辰（简化）
        shan_yuanchen = {
            '壬山': '甲己', '子山': '甲己', '癸山': '戊癸',
            '丑山': '戊癸', '艮山': '丁壬', '寅山': '丁壬',
            '甲山': '丙辛', '卯山': '丙辛', '乙山': '乙庚',
            '辰山': '乙庚', '巽山': '甲己', '巳山': '甲己',
            '丙山': '戊癸', '午山': '戊癸', '丁山': '丁壬',
            '未山': '丁壬', '坤山': '丙辛', '申山': '丙辛',
            '庚山': '乙庚', '酉山': '乙庚', '辛山': '甲己',
            '戌山': '甲己', '乾山': '戊癸', '亥山': '戊癸',
        }
        
        yuanchen = shan_yuanchen.get(shan_name, '甲己')
        
        # 判断课格（简化）
        if day_gan in yuanchen:
            kege = '元辰课'
            score = 8.5
        elif day_gan in ['丙', '辛'] and shan_name in ['壬山', '子山']:
            kege = '武财课'
            score = 9.0
        elif day_gan in ['丁', '壬'] and shan_name in ['壬山', '子山']:
            kege = '贪官课'
            score = 3.0
        else:
            kege = '平课'
            score = 6.0
        
        return {'kege': kege, 'score': score}
    
    def _is_chong(self, zhi1: str, zhi2: str) -> bool:
        """判断是否相冲"""
        chong_pairs = [
            ('子', '午'), ('丑', '未'), ('寅', '申'),
            ('卯', '酉'), ('辰', '戌'), ('巳', '亥')
        ]
        return (zhi1, zhi2) in chong_pairs or (zhi2, zhi1) in chong_pairs
    
    def _get_jixiong_desc(self, score: float) -> str:
        """根据评分返回吉凶描述"""
        if score >= 9.0:
            return "上上大吉"
        elif score >= 8.0:
            return "上吉"
        elif score >= 7.0:
            return "中吉"
        elif score >= 6.0:
            return "小吉"
        elif score >= 5.0:
            return "吉凶参半"
        elif score >= 4.0:
            return "小凶"
        elif score >= 3.0:
            return "中凶"
        elif score >= 2.0:
            return "大凶"
        else:
            return "上凶"
    
    def get_best_date_in_range(self, start_date: datetime, end_date: datetime, 
                               shan_name: str = None, min_score: float = 7.0) -> list:
        """
        计算日期范围内的最吉日期
        
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param shan_name: 坐山
        :param min_score: 最低评分要求
        :return: 吉日列表（按评分排序）
        """
        auspicious_days = []
        
        current = start_date
        while current <= end_date:
            # 计算日的吉凶
            day_fortune = self.calculate_day_fortune(
                current.year, current.month, current.day, shan_name
            )
            
            # 计算年的吉凶
            year_fortune = self.calculate_year_fortune(current.year)
            
            # 计算月的吉凶
            month_fortune = self.calculate_month_fortune(current.year, current.month)
            
            # 综合评分（年 20% + 月 30% + 日 50%）
            total_score = (
                year_fortune['评分'] * 0.2 +
                month_fortune['评分'] * 0.3 +
                day_fortune['评分'] * 0.5
            )
            
            if total_score >= min_score:
                auspicious_days.append({
                    '日期': current.strftime('%Y-%m-%d'),
                    '年柱': year_fortune['年柱'],
                    '月柱': day_fortune.get('月柱', month_fortune['月柱']),
                    '日柱': day_fortune['日柱'],
                    '综合评分': round(total_score, 1),
                    '吉凶': self._get_jixiong_desc(total_score),
                    '说明': day_fortune['说明']
                })
            
            current += timedelta(days=1)
        
        # 按评分排序
        auspicious_days.sort(key=lambda x: x['综合评分'], reverse=True)
        
        return auspicious_days


def test_calculator():
    """测试吉凶计算器"""
    calc = PreciseAuspicousCalculator()
    
    print("=" * 80)
    print("精确年月日时吉凶计算测试")
    print("=" * 80)
    
    # 测试年
    print("\n【2026 年流年】")
    year = calc.calculate_year_fortune(2026)
    print(f"年柱：{year['年柱']}")
    print(f"评分：{year['评分']}分 - {year['吉凶']}")
    print(f"说明：{year['说明']}")
    
    # 测试月
    print("\n【2026 年 3 月流月】")
    month = calc.calculate_month_fortune(2026, 3)
    print(f"月柱：{month['月柱']}")
    print(f"评分：{month['评分']}分 - {month['吉凶']}")
    print(f"说明：{month['说明']}")
    
    # 测试日
    print("\n【2026 年 3 月 20 日流日（壬山）】")
    day = calc.calculate_day_fortune(2026, 3, 20, '壬山')
    print(f"日柱：{day['日柱']}")
    print(f"建除：{day['建除']}")
    print(f"斗首：{day['斗首课格']}")
    print(f"评分：{day['评分']}分 - {day['吉凶']}")
    print(f"说明：{day['说明']}")
    
    # 测试时
    print("\n【2026 年 3 月 20 日 23 时流时】")
    hour = calc.calculate_hour_fortune(2026, 3, 20, 23, '壬山')
    print(f"时辰：{hour['时辰']}")
    print(f"时柱：{hour['时柱']}")
    print(f"评分：{hour['评分']}分 - {hour['吉凶']}")
    print(f"说明：{hour['说明']}")
    
    # 测试吉日选择
    print("\n" + "=" * 80)
    print("【2026 年 3 月 15-25 日吉日选择（壬山）】")
    print("=" * 80)
    
    from datetime import datetime
    start = datetime(2026, 3, 15)
    end = datetime(2026, 3, 25)
    
    best_days = calc.get_best_date_in_range(start, end, '壬山', 7.0)
    
    for i, day in enumerate(best_days[:5], 1):  # 显示前 5 个吉日
        print(f"\n第{i}吉日：{day['日期']}")
        print(f"  四柱：{day['年柱']} {day['月柱']} {day['日柱']}")
        print(f"  评分：{day['综合评分']}分 - {day['吉凶']}")
        print(f"  说明：{day['说明']}")


if __name__ == '__main__':
    test_calculator()
