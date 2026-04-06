"""
准确的四柱计算引擎
严格按照节气计算年柱、月柱
"""

from datetime import datetime
import math

# 天干地支
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 60 甲子
LIUSHIJIAZI = []
for i in range(60):
    LIUSHIJIAZI.append((TIANGAN[i % 10], DIZHI[i % 12]))

# 节气数据（2025-2027 年）
# 格式：(节气名，公历日期)
JIEQI_DATA = {
    2025: {
        '小寒': (1, 5), '大寒': (1, 20),
        '立春': (2, 3), '雨水': (2, 18),
        '惊蛰': (3, 5), '春分': (3, 20),
        '清明': (4, 4), '谷雨': (4, 19),
        '立夏': (5, 5), '小满': (5, 20),
        '芒种': (6, 5), '夏至': (6, 21),
        '小暑': (7, 6), '大暑': (7, 22),
        '立秋': (8, 7), '处暑': (8, 22),
        '白露': (9, 7), '秋分': (9, 22),
        '寒露': (10, 7), '霜降': (10, 23),
        '立冬': (11, 7), '小雪': (11, 22),
        '大雪': (12, 6), '冬至': (12, 21),
    },
    2026: {
        '小寒': (1, 5), '大寒': (1, 20),
        '立春': (2, 4), '雨水': (2, 18),
        '惊蛰': (3, 5), '春分': (3, 20),
        '清明': (4, 4), '谷雨': (4, 19),
        '立夏': (5, 5), '小满': (5, 21),
        '芒种': (6, 5), '夏至': (6, 21),
        '小暑': (7, 7), '大暑': (7, 22),
        '立秋': (8, 7), '处暑': (8, 22),
        '白露': (9, 7), '秋分': (9, 22),
        '寒露': (10, 8), '霜降': (10, 23),
        '立冬': (11, 7), '小雪': (11, 22),
        '大雪': (12, 7), '冬至': (12, 22),
    },
    2027: {
        '小寒': (1, 5), '大寒': (1, 20),
        '立春': (2, 4), '雨水': (2, 18),
    }
}

# 月支对应（以节气为界）
# 寅月（立春 - 惊蛰前），卯月（惊蛰 - 清明前）...
YUEFEN_DIZHI = {
    1: '寅',  # 立春 - 惊蛰
    2: '卯',  # 惊蛰 - 清明
    3: '辰',  # 清明 - 立夏
    4: '巳',  # 立夏 - 芒种
    5: '午',  # 芒种 - 小暑
    6: '未',  # 小暑 - 立秋
    7: '申',  # 立秋 - 白露
    8: '酉',  # 白露 - 寒露
    9: '戌',  # 寒露 - 立冬
    10: '亥', # 立冬 - 大雪
    11: '子', # 大雪 - 小寒
    12: '丑', # 小寒 - 立春
}

# 节（每月的节，不是气）
JIE_NAMES = ['小寒', '立春', '惊蛰', '清明', '立夏', '芒种', 
             '小暑', '立秋', '白露', '寒露', '立冬', '大雪']


def get_jieqi_date(year: int, jie_name: str) -> datetime:
    """获取节气日期"""
    if year not in JIEQI_DATA or jie_name not in JIEQI_DATA[year]:
        # 简单推算
        base_year = 2026
        base_date = JIEQI_DATA[base_year].get(jie_name, (2, 4))
        return datetime(year, base_date[0], base_date[1])
    
    date_info = JIEQI_DATA[year].get(jie_name)
    return datetime(year, date_info[0], date_info[1])


def get_year_ganzhi(year: int, month: int, day: int) -> tuple:
    """
    获取年干支（以立春为界）
    2025 年是乙巳年，2026 年立春后才是丙午年
    注意：立春当日属于新年
    """
    # 1984 年是甲子年
    base_year = 1984
    
    # 检查是否在立春前
    li_chun = get_jieqi_date(year, '立春')
    target_date = datetime(year, month, day)
    
    if target_date < li_chun:
        # 立春前，属于上一年
        actual_year = year - 1
    else:
        # 立春及立春后，属于本年
        actual_year = year
    
    offset = (actual_year - base_year) % 60
    return LIUSHIJIAZI[offset]


def get_month_ganzhi(year: int, month: int, day: int) -> tuple:
    """
    获取月干支（以节气为界）
    月建：正月寅，二月卯...十一月子，十二月丑
    以节为界：小寒 - 立春前为丑月，立春 - 惊蛰前为寅月...
    注意：节气当日属于新月
    """
    target_date = datetime(year, month, day)
    
    # 检查各个节气，确定月份
    # 顺序：小寒 (丑月始) -> 立春 (寅月始) -> 惊蛰 (卯月始) -> ... -> 大雪 (子月始)
    jieqi_order = [
        ('小寒', 12),   # 丑月开始
        ('立春', 1),    # 寅月开始
        ('惊蛰', 2),    # 卯月开始
        ('清明', 3),    # 辰月开始
        ('立夏', 4),    # 巳月开始
        ('芒种', 5),    # 午月开始
        ('小暑', 6),    # 未月开始
        ('立秋', 7),    # 申月开始
        ('白露', 8),    # 酉月开始
        ('寒露', 9),    # 戌月开始
        ('立冬', 10),   # 亥月开始
        ('大雪', 11),   # 子月开始
    ]
    
    # 默认丑月（小寒前）
    month_idx = 12
    
    # 找到最后一个满足条件的节气（>= 表示节气当日属于新月）
    for jie_name, month_num in jieqi_order:
        jie_date = get_jieqi_date(year, jie_name)
        if jie_date and target_date >= jie_date:
            month_idx = month_num
    
    # 年干（用于五虎遁）
    year_tiangan, _ = get_year_ganzhi(year, month, day)
    
    # 月支
    month_dizhi = YUEFEN_DIZHI[month_idx]
    
    # 五虎遁求月干
    # 甲己之年丙作首，乙庚之岁戊为头，丙辛之岁寻庚上，丁壬壬寅顺水流，戊癸之年甲寅头
    # 意思是：甲己年寅月起丙寅，乙庚年寅月起戊寅，丙辛年寅月起庚寅，丁壬年寅月起壬寅，戊癸年寅月起甲寅
    if year_tiangan in ['甲', '己']:
        start_tiangan = '丙'  # 寅月起丙
    elif year_tiangan in ['乙', '庚']:
        start_tiangan = '戊'  # 寅月起戊
    elif year_tiangan in ['丙', '辛']:
        start_tiangan = '庚'  # 寅月起庚
    elif year_tiangan in ['丁', '壬']:
        start_tiangan = '壬'  # 寅月起壬
    else:  # 戊、癸
        start_tiangan = '甲'  # 寅月起甲
    
    # 计算月干：从寅月 (1) 开始顺数
    # 寅月=1 对应 start_tiangan，卯月=2 对应 start_tiangan+1, ...
    start_idx = TIANGAN.index(start_tiangan)
    # 月干索引 = (起始天干索引 + 月份索引 - 1) % 10
    # 丑月 (12) 是寅月的前一个月，所以是 (start_idx - 1) % 10
    if month_idx == 12:  # 丑月，在寅月之前
        month_tiangan_idx = (start_idx - 1) % 10
    else:
        # 寅月 (1): start_idx + 0
        # 卯月 (2): start_idx + 1
        # ...
        month_tiangan_idx = (start_idx + month_idx - 1) % 10
    
    return TIANGAN[month_tiangan_idx], month_dizhi


def get_day_ganzhi(year: int, month: int, day: int) -> tuple:
    """
    高氏日柱公式
    基于 2000 年 1 月 1 日戊午日
    """
    base_date = datetime(2000, 1, 1)
    base_ganzhi_index = 54  # 戊午在 60 甲子中的序号
    
    target_date = datetime(year, month, day)
    delta_days = (target_date - base_date).days
    
    ganzhi_index = (base_ganzhi_index + delta_days) % 60
    
    return LIUSHIJIAZI[ganzhi_index]


def get_hour_ganzhi(day_tiangan: str, shichen: str) -> tuple:
    """
    获取时干支（五鼠遁）
    """
    if day_tiangan in ['甲', '己']:
        start_tiangan = '甲'
    elif day_tiangan in ['乙', '庚']:
        start_tiangan = '丙'
    elif day_tiangan in ['丙', '辛']:
        start_tiangan = '戊'
    elif day_tiangan in ['丁', '壬']:
        start_tiangan = '庚'
    else:  # 戊、癸
        start_tiangan = '壬'
    
    shichen_idx = DIZHI.index(shichen)
    hour_tiangan_idx = (TIANGAN.index(start_tiangan) + shichen_idx) % 10
    
    return TIANGAN[hour_tiangan_idx], shichen


def get_sizhu(year: int, month: int, day: int, shichen: str = '午') -> dict:
    """
    获取四柱（年月日时）
    """
    year_ganzhi = get_year_ganzhi(year, month, day)
    month_ganzhi = get_month_ganzhi(year, month, day)
    day_ganzhi = get_day_ganzhi(year, month, day)
    hour_ganzhi = get_hour_ganzhi(day_ganzhi[0], shichen)
    
    return {
        '年柱': f"{year_ganzhi[0]}{year_ganzhi[1]}",
        '月柱': f"{month_ganzhi[0]}{month_ganzhi[1]}",
        '日柱': f"{day_ganzhi[0]}{day_ganzhi[1]}",
        '时柱': f"{hour_ganzhi[0]}{hour_ganzhi[1]}",
    }


# 测试
if __name__ == '__main__':
    print("=== 四柱计算测试 ===")
    print("\n2026 年 2 月 1 日（立春前）:")
    sizhu = get_sizhu(2026, 2, 1, '午')
    print(f"  年柱：{sizhu['年柱']} (乙巳年，立春前属上一年)")
    print(f"  月柱：{sizhu['月柱']} (丁丑月，乙年丑月)")
    print(f"  日柱：{sizhu['日柱']}")
    print(f"  时柱：{sizhu['时柱']}")
    
    print("\n2026 年 2 月 5 日（立春后）:")
    sizhu = get_sizhu(2026, 2, 5, '午')
    print(f"  年柱：{sizhu['年柱']} (应该是丙午)")
    print(f"  月柱：{sizhu['月柱']} (应该是庚寅)")
    print(f"  日柱：{sizhu['日柱']}")
    print(f"  时柱：{sizhu['时柱']}")
