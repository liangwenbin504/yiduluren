"""
农历转换工具（基于数据表）
"""

# 2020-2030 年农历数据（简化版）
# 格式：[春节的公历日期（月，日）]
# 春节是农历正月初一

LUNAR_NEW_YEAR = {
    2020: (1, 25),  # 2020 年春节 1 月 25 日
    2021: (2, 12),  # 2021 年春节 2 月 12 日
    2022: (2, 1),   # 2022 年春节 2 月 1 日
    2023: (1, 22),  # 2023 年春节 1 月 22 日
    2024: (2, 10),  # 2024 年春节 2 月 10 日
    2025: (1, 29),  # 2025 年春节 1 月 29 日
    2026: (2, 17),  # 2026 年春节 2 月 17 日
    2027: (2, 6),   # 2027 年春节 2 月 6 日
    2028: (1, 26),  # 2028 年春节 1 月 26 日
    2029: (2, 13),  # 2029 年春节 2 月 13 日
    2030: (2, 3),   # 2030 年春节 2 月 3 日
}

# 每月天数（农历大月 30 天，小月 29 天）
# 这里使用简化数据，实际需要查表
LUNAR_MONTH_DAYS = [
    30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29
]


def solar_to_lunar(year: int, month: int, day: int) -> str:
    """
    公历转农历（基于数据表）
    :param year: 公历年份
    :param month: 公历月份
    :param day: 公历日期
    :return: 农历日期字符串
    """
    if year not in LUNAR_NEW_YEAR:
        return f"农历{year}年（数据暂缺）"
    
    # 计算与春节的天数差
    spring_festival = LUNAR_NEW_YEAR[year]
    
    # 将日期转换为一年中的第几天
    def day_of_year(y, m, d):
        days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        # 闰年判断
        if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0):
            days_in_month[2] = 29
        
        return sum(days_in_month[:m]) + d
    
    # 今年春节是第几天
    spring_day = day_of_year(year, spring_festival[0], spring_festival[1])
    
    # 目标日期是第几天
    target_day = day_of_year(year, month, day)
    
    # 计算与春节相差的天数
    delta = target_day - spring_day
    
    # 如果在春节前，属于上一年腊月
    if delta < 0:
        # 属于上一年腊月（十二月）
        prev_year = year - 1
        if prev_year in LUNAR_NEW_YEAR:
            prev_spring = LUNAR_NEW_YEAR[prev_year]
            # 计算从正月初一到春节前一天的天数（即腊月天数）
            # 腊月天数 = 目标日期到年底的天数 + 年初到春节前一天的天数
            # 简化计算：直接返回腊月，日期需要查表（这里简化处理）
            # 实际应该用专业农历库
            lunar_day = -delta  # 距离春节的天数（负数转正）
            if lunar_day > 30:
                lunar_day = 30
            # 数字转中文（内部函数）
            def num_to_chinese_local(num):
                if num <= 10:
                    return ['零','一','二','三','四','五','六','七','八','九','十'][num]
                elif num <= 19:
                    return '十' + (['','一','二','三','四','五','六','七','八','九'][num-10] if num > 10 else '')
                elif num == 20:
                    return '二十'
                elif num <= 29:
                    return '二十' + ['','一','二','三','四','五','六','七','八','九'][num-20]
                elif num == 30:
                    return '三十'
                else:
                    return str(num)
            return f"农历{prev_year}年腊月{num_to_chinese_local(lunar_day)}日"
        else:
            return f"农历{year-1}年腊月（数据暂缺）"
    
    # 根据天数差计算农历月日
    lunar_month = 1
    lunar_day = 1 + delta
    
    # 遍历农历月
    for i, days in enumerate(LUNAR_MONTH_DAYS):
        if lunar_day <= days:
            break
        lunar_day -= days
        lunar_month += 1
        if lunar_month > 12:
            lunar_month = 12
            break
    
    # 数字转中文
    def num_to_chinese(num):
        if num <= 10:
            return ['零','一','二','三','四','五','六','七','八','九','十'][num]
        elif num <= 19:
            return '十' + (['','一','二','三','四','五','六','七','八','九'][num-10] if num > 10 else '')
        elif num == 20:
            return '二十'
        elif num <= 29:
            return '二十' + ['','一','二','三','四','五','六','七','八','九'][num-20]
        elif num == 30:
            return '三十'
        else:
            return str(num)
    
    return f"农历{year}年{num_to_chinese(lunar_month)}月{num_to_chinese(lunar_day)}日"


# 测试
if __name__ == '__main__':
    test_dates = [
        (2026, 1, 1),
        (2026, 2, 1),
        (2026, 2, 17),  # 春节
        (2026, 3, 1),
        (2026, 6, 15),
        (2026, 12, 31),
    ]
    
    print("=== 农历转换测试 ===")
    for year, month, day in test_dates:
        lunar = solar_to_lunar(year, month, day)
        print(f"{year}年{month}月{day}日 → {lunar}")
