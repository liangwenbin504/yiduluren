# -*- coding: utf-8 -*-
"""干支年/农历月日 → 公历日期换算
锚点：邵彦和殁于 1133 癸丑（评疏载），60 甲子反推公历年。
"""
import sxtwl
from datetime import date, timedelta

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]
_ANCHOR = JIAZI.index('癸丑')  # 1133 年


def year_gz_to_solar(year_gz):
    """干支年 → 公历年（以邵彦和年代 1133=癸丑 为锚点）"""
    if year_gz not in JIAZI:
        return None
    return 1133 + (JIAZI.index(year_gz) - _ANCHOR)


def day_gz_of(d):
    """公历 date → 日干支字符串"""
    x = sxtwl.fromSolar(d.year, d.month, d.day)
    gz = x.getDayGZ()
    return GAN[gz.tg] + ZHI[gz.dz]


def find_solar(year_gz, lunar_month, day_gz):
    """干支年 + 农历月 + 日干支 → 公历 date（找不到返回 None）"""
    sy = year_gz_to_solar(year_gz)
    if sy is None:
        return None
    d = date(sy, 1, 1)
    end = date(sy + 1, 1, 1)
    while d < end:
        x = sxtwl.fromSolar(d.year, d.month, d.day)
        if x.getLunarYear() == sy and x.getLunarMonth() == lunar_month:
            gz = x.getDayGZ()
            if GAN[gz.tg] + ZHI[gz.dz] == day_gz:
                return d
        d += timedelta(days=1)
    return None


def find_solar_by_lunar_day(year_gz, lunar_month, lunar_day):
    """干支年 + 农历月 + 农历日（初八）→ 公历 date"""
    sy = year_gz_to_solar(year_gz)
    if sy is None:
        return None
    d = date(sy, 1, 1)
    end = date(sy + 1, 1, 1)
    while d < end:
        x = sxtwl.fromSolar(d.year, d.month, d.day)
        if x.getLunarYear() == sy and x.getLunarMonth() == lunar_month and x.getLunarDay() == lunar_day:
            return d
        d += timedelta(days=1)
    return None
