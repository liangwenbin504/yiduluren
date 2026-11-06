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

# 节气数据（2025-2029 年）
# 格式：(节气名，公历日期)
# 🔴 2026-10-31 修复（憨爷「先修节气引擎」）：原表 2025 年 13 处、2026 年 14 处、2027 年 2 处
#    节气日期比天文历**早 1 天**（如 2026 立冬原写 11/07，实为 11/08 01:51）。表内年份
#    直接查表、不经 sxtwl 校正，导致交节当天（及交界日）月柱/年柱/月将判错。
#    现全部按 sxtwl 天文历「交节北京时间日期」重写，并补 2028/2029 两年。
#    ✅ 自检：`python _gen_jieqi_table.py` 可重新按 sxtwl 生成同表；`_audit_jieqi_table.py` 逐条核对。
JIEQI_DATA = {
    2025: {
        '小寒': (1, 5), '大寒': (1, 20), '立春': (2, 4), '雨水': (2, 19),
        '惊蛰': (3, 6), '春分': (3, 21), '清明': (4, 5), '谷雨': (4, 20),
        '立夏': (5, 5), '小满': (5, 21), '芒种': (6, 6), '夏至': (6, 21),
        '小暑': (7, 7), '大暑': (7, 23), '立秋': (8, 7), '处暑': (8, 23),
        '白露': (9, 8), '秋分': (9, 23), '寒露': (10, 8), '霜降': (10, 23),
        '立冬': (11, 7), '小雪': (11, 22), '大雪': (12, 7), '冬至': (12, 22),
    },
    2026: {
        '小寒': (1, 6), '大寒': (1, 20), '立春': (2, 4), '雨水': (2, 19),
        '惊蛰': (3, 6), '春分': (3, 21), '清明': (4, 5), '谷雨': (4, 20),
        '立夏': (5, 6), '小满': (5, 21), '芒种': (6, 6), '夏至': (6, 22),
        '小暑': (7, 7), '大暑': (7, 23), '立秋': (8, 8), '处暑': (8, 23),
        '白露': (9, 8), '秋分': (9, 23), '寒露': (10, 8), '霜降': (10, 24),
        '立冬': (11, 8), '小雪': (11, 22), '大雪': (12, 7), '冬至': (12, 22),
    },
    2027: {
        '小寒': (1, 6), '大寒': (1, 20), '立春': (2, 4), '雨水': (2, 19),
        '惊蛰': (3, 6), '春分': (3, 21), '清明': (4, 5), '谷雨': (4, 20),
        '立夏': (5, 6), '小满': (5, 21), '芒种': (6, 6), '夏至': (6, 22),
        '小暑': (7, 7), '大暑': (7, 23), '立秋': (8, 8), '处暑': (8, 24),
        '白露': (9, 8), '秋分': (9, 23), '寒露': (10, 9), '霜降': (10, 24),
        '立冬': (11, 8), '小雪': (11, 23), '大雪': (12, 8), '冬至': (12, 22),
    },
    2028: {
        '小寒': (1, 6), '大寒': (1, 21), '立春': (2, 4), '雨水': (2, 19),
        '惊蛰': (3, 5), '春分': (3, 20), '清明': (4, 4), '谷雨': (4, 20),
        '立夏': (5, 5), '小满': (5, 21), '芒种': (6, 5), '夏至': (6, 21),
        '小暑': (7, 7), '大暑': (7, 22), '立秋': (8, 7), '处暑': (8, 23),
        '白露': (9, 7), '秋分': (9, 23), '寒露': (10, 8), '霜降': (10, 23),
        '立冬': (11, 7), '小雪': (11, 22), '大雪': (12, 7), '冬至': (12, 22),
    },
    2029: {
        '小寒': (1, 5), '大寒': (1, 20), '立春': (2, 4), '雨水': (2, 19),
        '惊蛰': (3, 5), '春分': (3, 21), '清明': (4, 5), '谷雨': (4, 20),
        '立夏': (5, 5), '小满': (5, 21), '芒种': (6, 6), '夏至': (6, 21),
        '小暑': (7, 7), '大暑': (7, 23), '立秋': (8, 7), '处暑': (8, 23),
        '白露': (9, 8), '秋分': (9, 23), '寒露': (10, 8), '霜降': (10, 23),
        '立冬': (11, 7), '小雪': (11, 22), '大雪': (12, 7), '冬至': (12, 22),
    },
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

# ── 交节时刻切分（2026-09-06 修复）──────────────────────────────
# 旧逻辑按"公历日 0 点"切年/月柱：交节当日 12 时辰全标新月/新年（错）。
#   现改为按"时辰中点 ≥ 交节时刻"切分：交节时刻所在的时辰段及之后=新节，之前=旧节。
#   误差边界：交节恰在时辰后段时，该时辰整体按新节计（工程妥协，注释说明）。
SHICHEN_HOUR_MID = {'子': 0.0, '丑': 2.0, '寅': 4.0, '卯': 6.0, '辰': 8.0, '巳': 10.0,
                    '午': 12.0, '未': 14.0, '申': 16.0, '酉': 18.0, '戌': 20.0, '亥': 22.0}

# sxtwl 节气序（0-23）：冬至0 小寒1 大寒2 立春3 雨水4 惊蛰5 春分6 清明7 谷雨8
#   立夏9 小满10 芒种11 夏至12 小暑13 大暑14 立秋15 处暑16 白露17 秋分18 寒露19 霜降20 立冬21 小雪22 大雪23
_SXTWL_JIE_INDEX = {'冬至': 0, '小寒': 1, '大寒': 2, '立春': 3, '雨水': 4, '惊蛰': 5,
                    '春分': 6, '清明': 7, '谷雨': 8, '立夏': 9, '小满': 10, '芒种': 11,
                    '夏至': 12, '小暑': 13, '大暑': 14, '立秋': 15, '处暑': 16, '白露': 17,
                    '秋分': 18, '寒露': 19, '霜降': 20, '立冬': 21, '小雪': 22, '大雪': 23}

_jieqi_hour_cache: dict = {}   # (year, name) -> 交节北京时间（当日小时 float，0-24）


def _jieqi_bj_hour(year: int, jie_name: str) -> float:
    """交节北京时间（当日小时 float）。优先 sxtwl 精确儒略日换算；失败退回 12.0（午时近似）。"""
    key = (year, jie_name)
    if key in _jieqi_hour_cache:
        return _jieqi_hour_cache[key]
    h = 12.0
    try:
        import sxtwl
        from datetime import timedelta
        idx = _SXTWL_JIE_INDEX.get(jie_name)
        if idx is None:
            raise ValueError(jie_name)
        dm = get_jieqi_date(year, jie_name)
        # 扫表日 ±1 天，找该节气当天取交节儒略日（防表日与天文日±1偏移）
        for dd in (-1, 0, 1):
            try:
                t0 = datetime(year, dm.month, dm.day + dd)
            except ValueError:
                continue
            day_obj = sxtwl.fromSolar(t0.year, t0.month, t0.day)
            if day_obj.hasJieQi() and day_obj.getJieQi() == idx:
                jd = day_obj.getJieQiJD()
                utc = datetime(2000, 1, 1, 12) + timedelta(days=jd - 2451545.0)
                bj = utc + timedelta(hours=8)
                h = bj.hour + bj.minute / 60.0
                break
    except Exception:
        pass
    _jieqi_hour_cache[key] = h
    return h


def get_jieqi_date(year: int, jie_name: str) -> datetime:
    """获取节气日期
    表内年份（2025-2027）直接查 JIEQI_DATA；表外年份改用 sxtwl 精确求交节日
    （2026-09-09 修复：交节日逐年漂移±1天，旧逻辑回退到2026年固定日期，
     导致 2030 白露(实际09-08 05:52)等被当成09-07，交节当天时辰月柱/年柱错判）。
    """
    if year in JIEQI_DATA and jie_name in JIEQI_DATA[year]:
        date_info = JIEQI_DATA[year].get(jie_name)
        if date_info:
            return datetime(year, date_info[0], date_info[1])
    # ── 表外年份：sxtwl 精确求交节日（基准月/日用于缩小扫描窗口）──
    base_date = JIEQI_DATA[2026].get(jie_name, (2, 4))
    idx = _SXTWL_JIE_INDEX.get(jie_name)
    if idx is not None:
        try:
            import sxtwl
            from datetime import timedelta
            bm = base_date[0]   # 节气所在公历月固定（节序由黄经定义）
            bd = base_date[1]
            # 扫描 基准日±6 天，命中该节气即返回（漂移最大±2天，留余量）。
            # ⚠ sxtwl.hasJieQi() 按 UTC 日期标记节气（与北京时差8h，跨日时会偏一天），
            #   故必须用 getJieQiJD() 换算回北京时日期（2026-09-09 修复：2030白露
            #   UTC 标 09-07 但北京时交节 09-08 05:52，若取 UTC 日会提前一天错判）。
            for dd in range(bd - 6, bd + 7):
                try:
                    d0 = datetime(year, bm, dd)
                except ValueError:
                    continue
                day_obj = sxtwl.fromSolar(d0.year, d0.month, d0.day)
                if day_obj.hasJieQi() and day_obj.getJieQi() == idx:
                    jd = day_obj.getJieQiJD()
                    utc = datetime(2000, 1, 1, 12) + timedelta(days=jd - 2451545.0)
                    bj = utc + timedelta(hours=8)
                    return datetime(bj.year, bj.month, bj.day)
        except Exception:
            pass
    return datetime(year, base_date[0], base_date[1])


def get_year_ganzhi(year: int, month: int, day: int, shichen: str = '午') -> tuple:
    """
    获取年干支（以立春为界）
    2025 年是乙巳年，2026 年立春后才是丙午年
    【2026-09-06 交节时刻修复】旧"立春当日属于新年"按公历日 0 点错判（交节当日前半仍属旧年）；
    改为：立春当日由"时辰中点 ≥ 交节时刻"判定（交节前=旧年，交节后=新年）。
    """
    # 1984 年是甲子年
    base_year = 1984
    
    # 检查是否在立春前
    li_chun = get_jieqi_date(year, '立春')
    target_date = datetime(year, month, day)
    
    if (month, day) == (li_chun.month, li_chun.day):
        # 【2026-09-06】立春当日：按交节时刻切分
        actual_year = year if SHICHEN_HOUR_MID.get(shichen, 12.0) >= _jieqi_bj_hour(year, '立春') else year - 1
    elif target_date < li_chun:
        # 立春前，属于上一年
        actual_year = year - 1
    else:
        # 立春后，属于本年
        actual_year = year
    
    offset = (actual_year - base_year) % 60
    return LIUSHIJIAZI[offset]


def get_month_ganzhi(year: int, month: int, day: int, shichen: str = '午') -> tuple:
    """
    获取月干支（以节气为界）
    月建：正月寅，二月卯...十一月子，十二月丑
    以节为界：小寒 - 立春前为丑月，立春 - 惊蛰前为寅月...
    【2026-09-06 交节时刻修复】旧"节气当日属于新月"按公历日 0 点错判（交节当日前半仍属旧月）；
    改为：交节当日由"时辰中点 ≥ 交节时刻"判定。
    """
    target_date = datetime(year, month, day)
    target_hour = SHICHEN_HOUR_MID.get(shichen, 12.0)

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

    # 【BUG-FIX 2026-09-13】跨年回溯（憨爷拍板：月建以四柱月柱为准，按「节」）。
    # 旧逻辑只在**本年** 12 个节里回溯：每年 1/1 ~ 本年小寒前（约 5 天）无任何节命中，
    # 于是回落默认丑月 → 月支整整错一位（应子月）。实测 2028-01-01~01-05 全被误判为丑月。
    # 修法：以**上一年大雪**为子月起算点，target 晚于它则先置子月，再由本年节气依次覆盖。
    # 例：2028-01-03 → 上一年大雪 2027-12-07 → 先置子月；本年小寒 2028-01-06 未到 → 保持子月 ✓
    _dx_prev = get_jieqi_date(year - 1, '大雪')
    if _dx_prev and target_date > _dx_prev:
        month_idx = 11   # 子月（大雪 ~ 小寒）

    # 找到最后一个满足条件的节气（== 表示节当日且时辰已过交节才属新月）
    for jie_name, month_num in jieqi_order:
        jie_date = get_jieqi_date(year, jie_name)
        if not jie_date:
            continue
        if target_date > jie_date:
            month_idx = month_num
        elif target_date == jie_date:
            # 【2026-09-06 交节时刻切分】交节当日：时辰中点 >= 交节时刻 → 新月
            if target_hour >= _jieqi_bj_hour(year, jie_name):
                month_idx = month_num
    
    # 年干（用于五虎遁）
    year_tiangan, _ = get_year_ganzhi(year, month, day, shichen)
    
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
    【2026-09-06 交节时刻切分】年/月柱按 shichen 交节时刻判定（交节当日不同时辰年/月柱可变）
    """
    year_ganzhi = get_year_ganzhi(year, month, day, shichen)
    month_ganzhi = get_month_ganzhi(year, month, day, shichen)
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
