# -*- coding: utf-8 -*-
"""女命行嫁月（《增补玉匣记》体系）—— ⛔ 已弃用（2026-09-11 憨爷拍板）

⛔ 弃用声明（2026-09-11，憨爷拍板「用六壬就不用《玉匣记》」）：
   本模块属《玉匣记》嫁娶专有体系，与本案「本门六壬择日」口径不合，**已从择日链路摘除**。
   · `_zeri_marriage_tabo.py` 不再 import 本模块；婚嫁避忌层已移除行嫁月判据。
   · 文件保留仅为留档（防误删、便于回退对照），**新代码勿再引用**。
   · 若憨爷日后改口要恢复，一句话即可重新接线（接口未变）。

原文歌诀（《增补玉匣记》「选择嫁娶吉日」·女命行嫁大利月）：
    正七迎鸡兔，二八虎合猴，
    三九蛇共猪，四十龙与狗，
    牛羊五十一，鼠马六十二。

释义：以**女命年支（属相）**定行嫁之「大利月」（农历月）——
    · 属鸡／兔（酉／卯）→ 正月、七月
    · 属虎／猴（寅／申）→ 二月、八月
    · 属蛇／猪（巳／亥）→ 三月、九月
    · 属龙／狗（辰／戌）→ 四月、十月
    · 属牛／羊（丑／未）→ 五月、十一月
    · 属鼠／马（子／午）→ 六月、十二月

小利月（合用次序：首选大利月，无奈方取小利月）：
    · 鼠马 → 正、七 ｜ 牛羊 → 四、十 ｜ 虎猴 → 三、九
    · 兔鸡 → 六、腊 ｜ 龙狗 → 五、十一 ｜ 蛇猪 → 二、八

另《玉匣记》有「阳前阴后一吉辰，正七首子及媒人，二八月妨翁与姑，
三九女之父母身，四十乃为夫主月，五共冬月妨自身」之妨月说，口径有争议，
**本模块不据以阻断**（避免臆造），仅出大利／小利两级。

⚠️ 月以**农历月（朔望月）**为准；闰月归其月数并置 is_leap 标记（闰月通常避用）。
对照：《钦定协纪辨方书》用事·婚姻、民间《嫁娶碎金赋》同此歌诀。
"""
from datetime import date

import sxtwl

# 女命年支 → 大利月（农历月序）
DA_LI = {
    '子': (6, 12), '午': (6, 12),
    '丑': (5, 11), '未': (5, 11),
    '寅': (2, 8), '申': (2, 8),
    '卯': (1, 7), '酉': (1, 7),
    '辰': (4, 10), '戌': (4, 10),
    '巳': (3, 9), '亥': (3, 9),
}
# 女命年支 → 小利月（农历月序）
XIAO_LI = {
    '子': (1, 7), '午': (1, 7),
    '丑': (4, 10), '未': (4, 10),
    '寅': (3, 9), '申': (3, 9),
    '卯': (6, 12), '酉': (6, 12),
    '辰': (5, 11), '戌': (5, 11),
    '巳': (2, 8), '亥': (2, 8),
}

_LABEL = {1: '正月', 2: '二月', 3: '三月', 4: '四月', 5: '五月', 6: '六月',
          7: '七月', 8: '八月', 9: '九月', 10: '十月', 11: '冬月', 12: '腊月'}


def lunar_of(d: date):
    """公历 date → (农历年, 农历月序, 农历日, 是否闰月)"""
    x = sxtwl.fromSolar(d.year, d.month, d.day)
    leap = bool(x.isLunarLeap()) if hasattr(x, 'isLunarLeap') else False
    return x.getLunarYear(), int(x.getLunarMonth()), int(x.getLunarDay()), leap


def month_status(nv_zhi: str, d: date) -> dict:
    """判某公历日在女命行嫁月体系中的等级。

    返回 dict:
      lunar_year/lunar_month/lunar_day/is_leap : 农历信息
      month_name   : '六月' 等
      status       : '大利月' | '小利月' | '常月'
      is_da_li     : 是否大利月（且非闰月）
      is_xiao_li   : 是否小利月（且非闰月）
      label        : 展示串，如 '六月(大利月)'
    """
    ly, lm, ld, leap = lunar_of(d)
    dz = DA_LI.get(nv_zhi, ())
    xz = XIAO_LI.get(nv_zhi, ())
    if lm in dz:
        st = '大利月'
    elif lm in xz:
        st = '小利月'
    else:
        st = '常月'
    is_da = (st == '大利月') and not leap
    is_xiao = (st == '小利月') and not leap
    mn = ('闰' if leap else '') + _LABEL.get(lm, f'{lm}月')
    tail = '' if leap else (f'({st})' if st != '常月' else '')
    return {
        'lunar_year': ly, 'lunar_month': lm, 'lunar_day': ld, 'is_leap': leap,
        'month_name': mn, 'status': st, 'is_da_li': is_da, 'is_xiao_li': is_xiao,
        'label': f'{mn}{tail}',
    }


def da_li_months(nv_zhi: str):
    """女命 → 大利月中文名列表"""
    return [_LABEL.get(m, f'{m}月') for m in DA_LI.get(nv_zhi, ())]


def xiao_li_months(nv_zhi: str):
    return [_LABEL.get(m, f'{m}月') for m in XIAO_LI.get(nv_zhi, ())]


def solar_ranges(nv_zhi: str, start: date, end: date, which: str = 'da'):
    """列出窗口内该女命的【大利月/小利月】公历区间。

    which: 'da' 大利月 | 'xiao' 小利月 | 'both' 合取
    """
    months = DA_LI.get(nv_zhi, ()) if which == 'da' else XIAO_LI.get(nv_zhi, ())
    if which == 'both':
        months = tuple(set(DA_LI.get(nv_zhi, ())) | set(XIAO_LI.get(nv_zhi, ())))
    out = []
    d = start
    cur = None
    while d <= end:
        ly, lm, ld, leap = lunar_of(d)
        hit = (lm in months) and not leap
        if hit:
            if cur and cur[3] == ly and cur[4] == lm:
                cur[2] = d
            else:
                if cur:
                    out.append(tuple(cur))
                cur = [d, d, d, ly, lm]
        else:
            if cur:
                out.append(tuple(cur))
                cur = None
        d = date.fromordinal(d.toordinal() + 1)
    if cur:
        out.append(tuple(cur))
    return [(a, b, ly, lm) for a, _, b, ly, lm in out]


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    NV = '午'
    print(f'女命 {NV}（马）→ 大利月 {da_li_months(NV)}；小利月 {xiao_li_months(NV)}')
    s, e = date(2026, 9, 11), date(2028, 2, 3)
    print(f'\n窗口 {s} ~ {e} 内 大利月区间：')
    for a, b, ly, lm in solar_ranges(NV, s, e, 'da'):
        print(f'  {a} ~ {b}   （农历 {ly} 年 {_LABEL.get(lm, lm)}，{(b-a).days+1} 天）')
    print(f'\n窗口内 小利月区间：')
    for a, b, ly, lm in solar_ranges(NV, s, e, 'xiao'):
        print(f'  {a} ~ {b}   （农历 {ly} 年 {_LABEL.get(lm, lm)}，{(b-a).days+1} 天）')
