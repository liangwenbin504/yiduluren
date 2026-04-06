#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 模块 1：日期范围生成模块

功能：
1. 生成从当前系统日期起至公元 2100 年 12 月 31 日期间的完整日期序列
2. 针对每个日期生成 12 个时辰的日课基础数据（每日 12 课）
3. 处理闰月、节气转换等特殊历法情况
4. 输出包含公历日期、农历日期、干支信息及时辰划分的标准数据结构
"""

from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# 添加 src 和 data 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from sizhu_engine import get_sizhu, get_year_ganzhi, get_month_ganzhi, get_day_ganzhi
from constants import DIZHI


class DateRangeGenerator:
    """日期范围生成器"""
    
    # 时辰对应关系
    SHICHEN_MAP = {
        0: '子', 1: '丑', 2: '寅', 3: '卯', 4: '辰', 5: '巳',
        6: '午', 7: '未', 8: '申', 9: '酉', 10: '戌', 11: '亥'
    }
    
    # 时辰时间范围（简化版，实际需要真太阳时校正）
    SHICHEN_TIME = {
        '子': (23, 1), '丑': (1, 3), '寅': (3, 5), '卯': (5, 7),
        '辰': (7, 9), '巳': (9, 11), '午': (11, 13), '未': (13, 15),
        '申': (15, 17), '酉': (17, 19), '戌': (19, 21), '亥': (21, 23)
    }
    
    def __init__(self, start_date: datetime = None, end_date: datetime = None):
        """
        初始化日期范围生成器
        :param start_date: 开始日期，默认为当前日期
        :param end_date: 结束日期，默认为 2100 年 12 月 31 日
        """
        self.start_date = start_date or datetime.now()
        self.end_date = end_date or datetime(2100, 12, 31)
        
    def generate_date_range(self) -> List[datetime]:
        """
        生成日期范围列表
        :return: 日期列表
        """
        date_list = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        return date_list
    
    def get_shichen_for_hour(self, hour: int) -> str:
        """
        根据小时获取时辰
        :param hour: 小时 (0-23)
        :return: 时辰地支
        """
        if hour == 23 or hour == 0:
            return '子'
        elif hour == 1:
            return '丑'
        elif hour == 3:
            return '寅'
        elif hour == 5:
            return '卯'
        elif hour == 7:
            return '辰'
        elif hour == 9:
            return '巳'
        elif hour == 11:
            return '午'
        elif hour == 13:
            return '未'
        elif hour == 15:
            return '申'
        elif hour == 17:
            return '酉'
        elif hour == 19:
            return '戌'
        elif hour == 21:
            return '亥'
        else:
            # 处理每个时辰的第二个小时
            hour_mapping = {
                0: '子', 2: '丑', 4: '寅', 6: '卯', 8: '辰',
                10: '巳', 12: '午', 14: '未', 16: '申', 18: '酉',
                20: '戌', 22: '亥'
            }
            return hour_mapping.get(hour, '子')
    
    def generate_daily_ke_data(self, date: datetime) -> List[Dict]:
        """
        生成单个日期的 12 个时辰日课数据
        :param date: 日期
        :return: 12 个时辰的日课数据列表
        """
        ke_data_list = []
        
        # 获取四柱基础信息
        year_ganzhi = get_year_ganzhi(date.year, date.month, date.day)
        month_ganzhi = get_month_ganzhi(date.year, date.month, date.day)
        day_ganzhi = get_day_ganzhi(date.year, date.month, date.day)
        
        # 生成 12 个时辰的数据
        for shichen_idx in range(12):
            shichen = self.SHICHEN_MAP[shichen_idx]
            
            # 计算时柱
            from sizhu_engine import get_hour_ganzhi
            hour_ganzhi = get_hour_ganzhi(day_ganzhi[0], shichen)
            
            # 构建日课数据结构
            ke_data = {
                '公历日期': {
                    '年': date.year,
                    '月': date.month,
                    '日': date.day,
                    '星期': date.strftime('%A'),
                    '日期字符串': date.strftime('%Y-%m-%d')
                },
                '农历日期': {
                    # TODO: 需要集成农历转换模块
                    '年': f"{year_ganzhi[0]}{year_ganzhi[1]}年",
                    '月': f"{month_ganzhi[0]}{month_ganzhi[1]}月",
                    '日': '待计算',
                    '日期字符串': '待计算'
                },
                '四柱信息': {
                    '年柱': f"{year_ganzhi[0]}{year_ganzhi[1]}",
                    '月柱': f"{month_ganzhi[0]}{month_ganzhi[1]}",
                    '日柱': f"{day_ganzhi[0]}{day_ganzhi[1]}",
                    '时柱': f"{hour_ganzhi[0]}{hour_ganzhi[1]}"
                },
                '时辰信息': {
                    '时辰地支': shichen,
                    '时辰天干': hour_ganzhi[0],
                    '时辰序号': shichen_idx + 1,
                    '时间范围': self._get_shichen_time_range(shichen)
                },
                '节气信息': {
                    '当前节气': '待计算',
                    '下一节气': '待计算',
                    '距下一节气天数': 0
                },
                '特殊历法': {
                    '是否闰月': False,
                    '是否节气日': False,
                    '是否朔望日': False
                }
            }
            
            ke_data_list.append(ke_data)
        
        return ke_data_list
    
    def _get_shichen_time_range(self, shichen: str) -> str:
        """获取时辰的时间范围"""
        time_map = {
            '子': '23:00-01:00', '丑': '01:00-03:00', '寅': '03:00-05:00',
            '卯': '05:00-07:00', '辰': '07:00-09:00', '巳': '09:00-11:00',
            '午': '11:00-13:00', '未': '13:00-15:00', '申': '15:00-17:00',
            '酉': '17:00-19:00', '戌': '19:00-21:00', '亥': '21:00-23:00'
        }
        return time_map.get(shichen, '')
    
    def generate_full_range_data(self, progress_callback=None) -> List[Dict]:
        """
        生成完整日期范围的所有日课数据
        :param progress_callback: 进度回调函数，参数为 (当前日期，总日期数)
        :return: 所有日课数据列表
        """
        all_ke_data = []
        date_range = self.generate_date_range()
        total_days = len(date_range)
        
        for idx, date in enumerate(date_range):
            # 调用进度回调
            if progress_callback:
                progress_callback(date, total_days)
            
            # 生成该日期的 12 个时辰数据
            daily_data = self.generate_daily_ke_data(date)
            all_ke_data.extend(daily_data)
            
            # 打印进度（可选）
            if (idx + 1) % 365 == 0:
                print(f"已处理 {idx + 1}/{total_days} 天")
        
        return all_ke_data
    
    def get_date_by_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        获取指定日期范围内的所有日课数据
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 日课数据列表
        """
        self.start_date = start_date
        self.end_date = end_date
        return self.generate_full_range_data()
    
    def get_single_day_data(self, date: datetime) -> List[Dict]:
        """
        获取单个日期的 12 个时辰数据
        :param date: 日期
        :return: 12 个时辰的日课数据
        """
        return self.generate_daily_ke_data(date)
    
    def get_single_ke_data(self, date: datetime, shichen_index: int) -> Dict:
        """
        获取特定日期和时辰的日课数据
        :param date: 日期
        :param shichen_index: 时辰索引 (1-12)
        :return: 单个日课数据
        """
        if shichen_index < 1 or shichen_index > 12:
            raise ValueError("时辰索引必须在 1-12 之间")
        
        daily_data = self.generate_daily_ke_data(date)
        return daily_data[shichen_index - 1]


def test_date_generator():
    """测试日期生成器"""
    print("=" * 70)
    print("日期范围生成模块测试")
    print("=" * 70)
    
    # 测试 1：生成单个日期数据
    print("\n【测试 1】生成 2026 年 3 月 24 日的 12 个时辰数据")
    generator = DateRangeGenerator()
    test_date = datetime(2026, 3, 24)
    daily_data = generator.get_single_day_data(test_date)
    
    print(f"\n公历日期：{test_date.strftime('%Y-%m-%d')}")
    print(f"四柱信息：")
    for i, data in enumerate(daily_data[:1], 1):  # 只显示第一个时辰
        print(f"  时辰{data['时辰信息']['时辰序号']}({data['时辰信息']['时辰地支']}时): "
              f"年柱={data['四柱信息']['年柱']}, 月柱={data['四柱信息']['月柱']}, "
              f"日柱={data['四柱信息']['日柱']}, 时柱={data['四柱信息']['时柱']}")
    
    # 测试 2：生成小范围日期数据
    print("\n【测试 2】生成 2026 年 3 月 24 日至 2026 年 3 月 26 日的数据")
    start = datetime(2026, 3, 24)
    end = datetime(2026, 3, 26)
    range_data = generator.get_date_by_range(start, end)
    print(f"生成数据总数：{len(range_data)} 条 (3 天×12 时辰)")
    
    # 测试 3：获取特定时辰数据
    print("\n【测试 3】获取 2026 年 3 月 24 日午时 (第 7 个时辰) 的数据")
    single_ke = generator.get_single_ke_data(test_date, 7)
    print(f"  时辰：{single_ke['时辰信息']['时辰地支']}时")
    print(f"  时柱：{single_ke['四柱信息']['时柱']}")
    print(f"  时间范围：{single_ke['时辰信息']['时间范围']}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_date_generator()
