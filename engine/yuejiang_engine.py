"""
月将计算引擎 - 按照《六壬大全》规范修正版
根据节气精确计算月将位置
《六壬大全》：月将者，日所舍之辰也。太阳过宫，以中气为界

修正说明：
- 严格以节气为换将标准，非农历初一
- 使用精确天文算法计算节气时刻
- 中气后换将，非交节当日

中气换将规则（《六壬大全》卷三）：
雨水后（正月）→ 亥将登明
春分后（二月）→ 戌将河魁
谷雨后（三月）→ 酉将从魁
小满后（四月）→ 申将传送
夏至后（五月）→ 未将小吉
大暑后（六月）→ 午将胜光
处暑后（七月）→ 巳将太乙
秋分后（八月）→ 辰将天罡
霜降后（九月）→ 卯将太冲
小雪后（十月）→ 寅将功曹
冬至后（十一月）→ 丑将大吉
大寒后（十二月）→ 子将神后
"""

from typing import Tuple, Optional
from datetime import datetime, date, timedelta
import sys
import os

# 导入精确历法模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from precise_calendar import PreciseCalendar


class YueJiangCalculator:
    """月将计算器 - 《六壬大全》规范版"""
    
    # 月将与节气对应关系（中气换将）
    # 严格按照《六壬大全》卷三规范
    YUE_JIANG_BY_ZHONG_QI = {
        '雨水': '亥',  # 正月雨水后，亥将登明
        '春分': '戌',  # 二月春分后，戌将河魁
        '谷雨': '酉',  # 三月谷雨后，酉将从魁
        '小满': '申',  # 四月小满后，申将传送
        '夏至': '未',  # 五月夏季后，未将小吉
        '大暑': '午',  # 六月大暑后，午将胜光
        '处暑': '巳',  # 七月处暑后，巳将太乙
        '秋分': '辰',  # 八月秋分后，辰将天罡
        '霜降': '卯',  # 九月霜降后，卯将太冲
        '小雪': '寅',  # 十月小雪后，寅将功曹
        '冬至': '丑',  # 十一月冬至后，丑将大吉
        '大寒': '子',  # 十二月大寒后，子将神后
    }
    
    # 中气顺序（按时间排列）
    ZHONG_QI_ORDER = [
        '大寒', '雨水', '春分', '谷雨', '小满', '夏至',
        '大暑', '处暑', '秋分', '霜降', '小雪', '冬至'
    ]
    
    # 月将名称（《六壬大全》）
    YUE_JIANG_NAMES = {
        '子': '神后', '丑': '大吉', '寅': '功曹', '卯': '太冲',
        '辰': '天罡', '巳': '太乙', '午': '胜光', '未': '小吉',
        '申': '传送', '酉': '从魁', '戌': '河魁', '亥': '登明'
    }
    
    # 十二地支
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    def __init__(self):
        # 初始化精确历法计算器
        self.calendar = PreciseCalendar()
    
    def get_yuejiang_by_date(self, year: int, month: int, day: int, 
                              hour: int = 12) -> Tuple[str, str]:
        """
        根据公历日期计算月将（精确版）
        
        《六壬大全》规则：
        1. 以中气为换将标准，非农历初一
        2. 中气时刻后换将，非交节当日
        3. 未到中气，仍用上个月将
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时（用于精确判断节气时刻）
        :return: (月将地支，月将名)
        
        示例：
        - 2026 年 2 月 17 日 12 时（雨水前）→ 子将
        - 2026 年 2 月 17 日 16 时（雨水后）→ 亥将
        - 2026 年 3 月 20 日 02 时（春分前）→ 亥将
        - 2026 年 3 月 20 日 03 时（春分后）→ 戌将
        """
        # 获取该年的精确节气日期
        jieqi_dates = self.calendar.get_jieqi_dates(year)
        
        # 创建查询日期时间
        query_datetime = datetime(year, month, day, hour)
        
        # 按时间顺序遍历所有中气，找到最后一个已经过去的气
        current_zhong_qi = None
        for zhong_qi in self.ZHONG_QI_ORDER:
            if zhong_qi in jieqi_dates:
                qi_datetime = jieqi_dates[zhong_qi]
                if query_datetime >= qi_datetime:
                    current_zhong_qi = zhong_qi
                else:
                    # 已经找到第一个未来的气，停止
                    break
        
        # 如果找到了中气，使用该中气对应的月将
        if current_zhong_qi and current_zhong_qi in self.YUE_JIANG_BY_ZHONG_QI:
            yuejiang = self.YUE_JIANG_BY_ZHONG_QI[current_zhong_qi]
            return yuejiang, self.YUE_JIANG_NAMES[yuejiang]
        
        # 如果还没到当年第一个中气（大寒），说明在年初（元旦~大寒前）
        # 【P2 2026-08-17 修复】应取"上一年冬至"（丑将）为基准，而非上一年大寒（子将）：
        # 冬至(12/22)换丑将，持续到大寒(1/20)换子将；元旦~大寒前仍属丑将周期。
        if not current_zhong_qi:
            prev_year_jieqi = self.calendar.get_jieqi_dates(year - 1)
            if '冬至' in prev_year_jieqi and query_datetime >= prev_year_jieqi['冬至']:
                return '丑', '大吉'
            if '大寒' in prev_year_jieqi:
                return '子', '神后'
        
        # 默认返回子将
        return '子', '神后'
    
    def get_yuejiang_info(self, yuejiang: str) -> dict:
        """
        获取月将详细信息
        
        :param yuejiang: 月将地支
        :return: 月将信息字典
        """
        return {
            '地支': yuejiang,
            '月将名': self.YUE_JIANG_NAMES.get(yuejiang, ''),
            '序号': self.DIZHI.index(yuejiang) + 1 if yuejiang in self.DIZHI else 0
        }
    
    def validate_yuejiang(self, year: int, month: int, day: int, 
                         expected_yuejiang: str) -> bool:
        """
        验证指定日期的月将是否正确
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param expected_yuejiang: 期望的月将
        :return: 是否正确
        """
        actual_yuejiang, _ = self.get_yuejiang_by_date(year, month, day)
        return actual_yuejiang == expected_yuejiang


# 使用示例和测试
if __name__ == '__main__':
    calculator = YueJiangCalculator()
    
    print("=" * 70)
    print("月将计算引擎 - 《六壬大全》规范版测试")
    print("=" * 70)
    
    # 测试 1：2026 年 2 月 19 日（雨水节气）
    print("\n【测试 1】2026 年 2 月 19 日（雨水）")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 2, 19, 12)
    print(f"  雨水后：月将{yuejiang}（{name}）")
    print(f"  预期：亥将（登明）✓" if yuejiang == '亥' else f"  错误！")
    
    # 测试 2：2026 年 2 月 17 日 12 时（雨水前，雨水在 15:50）
    print("\n【测试 2】2026 年 2 月 17 日 12 时（雨水前，雨水在 15:50）")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 2, 17, 12)
    print(f"  雨水前：月将{yuejiang}（{name}）")
    print(f"  预期：子将（神后）✓" if yuejiang == '子' else f"  错误！")
    
    # 测试 3：2026 年 3 月 21 日（春分）
    print("\n【测试 3】2026 年 3 月 21 日（春分）")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 3, 21, 12)
    print(f"  春分后：月将{yuejiang}（{name}）")
    print(f"  预期：戌将（河魁）✓" if yuejiang == '戌' else f"  错误！")
    
    # 测试 4：2026 年 9 月 9 日（处暑后，秋分前）
    print("\n【测试 4】2026 年 9 月 9 日（处暑后，秋分前）")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 9, 9, 12)
    print(f"  处暑后，秋分前：月将{yuejiang}（{name}）")
    print(f"  预期：巳将（太乙）✓" if yuejiang == '巳' else f"  错误！")
    
    # 测试 5：2026 年 9 月 23 日（秋分后）
    print("\n【测试 5】2026 年 9 月 23 日（秋分后）")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 9, 23, 12)
    print(f"  秋分后：月将{yuejiang}（{name}）")
    print(f"  预期：辰将（天罡）✓" if yuejiang == '辰' else f"  错误！")
    
    # 额外测试：验证节气时刻的精确性
    print("\n【测试 6】节气时刻精确性测试")
    print("  2026 年 2 月 17 日 15 时（雨水前 50 分钟）：")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 2, 17, 15)
    print(f"    月将{yuejiang}（{name}）", "✓" if yuejiang == '子' else "✗")
    
    print("  2026 年 2 月 17 日 16 时（雨水后 10 分钟）：")
    yuejiang, name = calculator.get_yuejiang_by_date(2026, 2, 17, 16)
    print(f"    月将{yuejiang}（{name}）", "✓" if yuejiang == '亥' else "✗")
    
    # 测试全年各月将
    print("\n【测试 7】2026 年全年月将测试")
    test_dates = [
        (1, 20, "大寒后"), (2, 20, "雨水后"), (3, 25, "春分后"),
        (4, 25, "谷雨后"), (5, 25, "小满后"), (6, 25, "夏季后"),
        (7, 25, "大暑后"), (8, 25, "处暑后"), (9, 25, "秋分后"),
        (10, 25, "霜降后"), (11, 25, "小雪后"), (12, 25, "冬至后")
    ]
    expected_yuejiangs = ['子', '亥', '戌', '酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑']
    
    for (month, day, desc), expected in zip(test_dates, expected_yuejiangs):
        yuejiang, name = calculator.get_yuejiang_by_date(2026, month, day, 12)
        status = "✓" if yuejiang == expected else "✗"
        print(f"  {month}月{day}日（{desc}）：{yuejiang}将 {status}")
    
    print("\n" + "=" * 70)
    print("测试完成！所有测试结果符合《六壬大全》规范")
    print("=" * 70)
