# -*- coding: utf-8 -*-
"""
月亮躔度（太阴入二十八宿）精确计算模块
========================================
《仪度六壬择日要诀》"日月合塑 / 日月对望"工程第一步：
以公历日期 → 农历（sxtwl）→ 代入《大六壬通解》月宿算法 → 太阴躔二十八宿 + 地支宫。

依据原文（《通解》二烦课）：
  "月宿者，太阴星躔度宫神也。正月初一起室，二奎，三胃，四毕，五参，六鬼，
   七张，八角，九氐，十尾，十一斗，十二虚。每月初一移一宿，逐日数二十八宿，
   遇奎、张、井、翼、氐、斗宿，重算留一，数尽月宿住处为太阴所在宫神。"
  "更详《七政历》细度为准" —— 本模块同时提供按日平推实现（留一双日宿）。

兼容性：
  - 复用 liuren_64ke_judge.XIU_28 / XIU_LIUYI / XIU_ZHI（二十八宿 → 十二支宫）
  - build_env 的 lunar_month 为负时表示闰月（sxtwl 约定），按 |month| 取同月起始宿
"""
import sys
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else None
if BASE and BASE not in sys.path:
    sys.path.insert(0, BASE)

try:
    from engine.liuren_64ke_judge import XIU_28, XIU_LIUYI, XIU_ZHI
except Exception:  # 独立调用时的兜底（防循环 import）
    XIU_28 = ['角', '亢', '氐', '房', '心', '尾', '箕', '斗', '牛', '女', '虚', '危',
              '室', '壁', '奎', '娄', '胃', '昴', '毕', '觜', '参', '井', '鬼', '柳',
              '星', '张', '翼', '轸']
    XIU_LIUYI = {'奎', '张', '井', '翼', '氐', '斗'}
    XIU_ZHI = {
        '角': '辰', '亢': '辰', '氐': '卯', '房': '卯', '心': '卯', '尾': '寅', '箕': '寅',
        '斗': '丑', '牛': '丑', '女': '子', '虚': '子', '危': '子', '室': '亥', '壁': '亥',
        '奎': '戌', '娄': '戌', '胃': '酉', '昴': '酉', '毕': '酉', '觜': '申', '参': '申',
        '井': '未', '鬼': '未', '柳': '午', '星': '午', '张': '午', '翼': '巳', '轸': '巳',
    }

# 每月初一的起始宿（正月室起）——《通解》原文
MONTH_START_XIU = {1: '室', 2: '奎', 3: '胃', 4: '毕', 5: '参', 6: '鬼',
                   7: '张', 8: '角', 9: '氐', 10: '尾', 11: '斗', 12: '虚'}


def _lunar_from_solar(year: int, month: int, day: int):
    """公历 → (农历月, 农历日, 是否闰月, 节气名)。
    本机 sxtwl 的闰月用 isLunarLeap() 布尔标记（getLunarMonth 恒为正），
    旧代码注释所提"负数代表闰月"的 sxtwl 版本与此不同——统一按 isLunarLeap 处理。"""
    try:
        import sxtwl as _sx
        if not (year > 0 and 1 <= month <= 12 and 1 <= day <= 31):
            return 0, 0, False, ''
        _lunar = _sx.fromSolar(year, month, day)
        lm = _lunar.getLunarMonth()
        ld = _lunar.getLunarDay()
        leap = bool(_lunar.isLunarLeap())
        jieqi = ''
        if _lunar.hasJieQi():
            jieqi = _lunar.getJieQi()
        return lm, ld, leap, jieqi
    except Exception:
        return 0, 0, False, ''


def yue_su_accurate(year: int, month: int, day: int, lunar_month: int = None, lunar_day: int = None,
                    lunar_leap: bool = False) -> str:
    """
    太阴躔二十八宿（精确版，公历日期入口）。

    优先使用传入的 lunar_month/lunar_day（已由调用方算好的农历）；未传则由
    sxtwl 从公历反解。闰月（lunar_leap=True 或 lunar_month<0 兼容旧约定）按
    同月序号取起始宿（《通解》未明言闰月超宿，古法闰月沿用本月起宿惯例）。

    返回: 二十八宿名（如 '室'）
    """
    if lunar_month is None or lunar_day is None:
        lunar_month, lunar_day, leap, _ = _lunar_from_solar(year, month, day)
        lunar_leap = lunar_leap or leap
    if not lunar_month or not lunar_day:
        return ''
    lm = abs(int(lunar_month))  # 兼容负值旧约定
    ld = int(lunar_day)
    if lunar_leap and lm > 1:
        # 闰月沿上月惯例逐次平移一格（闰X月 = X月的月序宿位；古法有争议，
        # 择日以"闰月取本月"为准——《要诀》合朔/对望关键是日月宫位，不做二义）
        pass
    start_xiu = MONTH_START_XIU.get(lm, '室')

    start_idx = XIU_28.index(start_xiu)
    seq = []
    pos = start_idx
    days = 0
    while days < ld:
        xiu = XIU_28[pos % 28]
        seq.append(xiu)
        days += 1
        if xiu in XIU_LIUYI:
            # 重算留一：该宿停留两天（再 append 一次）
            if days < ld:
                seq.append(xiu)
                days += 1
        pos += 1
    return seq[-1] if seq else start_xiu


def yue_su_zhi(year: int, month: int, day: int, lunar_month: int = None, lunar_day: int = None) -> str:
    """太阴躔度所临十二地支宫（XIU_ZHI 映射），用于与太阳/坐山/向首对位。"""
    xiu = yue_su_accurate(year, month, day, lunar_month, lunar_day)
    return XIU_ZHI.get(xiu, '') if xiu else ''


def moon_liangdu(year: int, month: int, day: int, lunar_month: int = None, lunar_day: int = None) -> dict:
    """
    月亮躔度完整信息（供日月合塑/日月对望判定复用）。

    返回:
      {
        'lunar_month': 农历月, 'lunar_day': 农历日, 'is_leap': 是否闰月,
        'xiu': 二十八宿名, 'zhi': 地支宫,
      }
    """
    leap = False
    if lunar_month is None or lunar_day is None:
        lunar_month, lunar_day, leap, _ = _lunar_from_solar(year, month, day)
    xiu = yue_su_accurate(year, month, day, lunar_month, lunar_day, leap)
    return {
        'lunar_month': lunar_month,
        'lunar_day': lunar_day,
        'is_leap': leap,
        'xiu': xiu,
        'zhi': XIU_ZHI.get(xiu, '') if xiu else '',
    }


def moon_table_month_norm():
    """月度归一对照（用于回归验证/文档）：每月初一的起始宿。"""
    return dict(MONTH_START_XIU)


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== 每月初一太阴宿（《通解》基准） ===')
    for m in range(1, 13):
        # 用 2026 年各月近似（仅验证起宿对照；日取当月第 1 个朔日近似）
        print(f'  农历{m}月初一 → {MONTH_START_XIU[m]}（应为原文基准）')
    print()
    print('=== 2026-09（农历七月廿四）实测 ===')
    info = moon_liangdu(2026, 9, 5)
    print('  2026-09-05 →', info)
    print('  与 liuren_64ke_judge.yue_su 对照：',
          '(import 后对比)')
    try:
        from engine.liuren_64ke_judge import yue_su
        print('  旧版 yue_su(7,24):', yue_su(7, 24), '| 新版:', info['xiu'])
    except Exception as e:
        print('  对照失败:', e)