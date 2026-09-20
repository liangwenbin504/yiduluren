# -*- coding: utf-8 -*-
"""
杀师日 / 犯雷日 判定（易郁《仪度六壬选日要诀》口诀，2026-08-17 憨爷 jpg 精确识读）。

图片口诀源（原书 1 页含三首歌 + 方忌标题）：
  1. 犯雷日歌（4 句）
     日：正月壬辰君莫犯，二月戊午不堪亲，子月(11)莫逢庚子日撞着雷霆大杀人
     时：正月巳日卯时妨，二月午日巳难当
  2. 杀师日时歌（12 个月，1-2 月与犯雷时歌共用"正月巳日卯时妨，二月午日巳难当"）
     正月巳日卯时妨，二月午日巳难当；三月未日丑时忌，四月申日辰不良；
     五酉子时师勿用，六戌未时杀师藏；七月癸日忌酉时，八月子日戌难医；
     九月丑日时妨午，十月寅日申须知；仲冬(11)卯日时妨亥，季冬(12)辰日寅杀师。
     注：七月"癸"按日干（其他月按日支），时辰为地支。
  3. 又杀师日歌（4 季，按节气月，日支+时支 二字并用才忌）
     春逢辰戌正堪忧，夏月卯酉不须求，秋遇牛羊师莫用，冬逢子午走无休。
  4. 二字并用方忌 = **以上三首歌的总则**（08-17 憨爷明确）：犯日、时/干、支 **两个字同时才凶**，
     只犯一个字不忌（如犯雷日"正月壬辰"=壬+辰两字；又杀师日"春辰戌"=日辰时戌两字）。
     本模块所有分支均已按二字并用实现（AND 判定）。

妨害对象：地师/风水师本人（开罗盘/点穴/下葬/立碑动罗经之事），与主家吉凶无关。
故只做"提醒/警示 + 可选禁用"，不进主家评分。
"""
from typing import Dict, List, Optional, Tuple

# ── 杀师日时歌：农历月 → (日支/干识别, 忌时支) ──
# 12 月全齐（08-17 憨爷补：1-2 月 = "正月巳日卯时妨，二月午日巳难当"，与犯雷日歌犯雷时共用这两句）
SHASHI_DAY_SH = {
    1:  ('zhi:巳', '卯'),    # 正月 巳日 卯时（憨爷补，与犯雷时共用）
    2:  ('zhi:午', '巳'),    # 二月 午日 巳时（憨爷补，与犯雷时共用）
    3:  ('zhi:未', '丑'),    # 三月 未日 丑时
    4:  ('zhi:申', '辰'),    # 四月 申日 辰时
    5:  ('zhi:酉', '子'),    # 五月 酉日 子时
    6:  ('zhi:戌', '未'),    # 六月 戌日 未时
    7:  ('gan:癸', '酉'),    # 七月 癸日 酉时（按日干，与其他月按日支不一致）
    8:  ('zhi:子', '戌'),    # 八月 子日 戌时
    9:  ('zhi:丑', '午'),    # 九月 丑日 午时
    10: ('zhi:寅', '申'),    # 十月 寅日 申时
    11: ('zhi:卯', '亥'),    # 仲冬 卯日 亥时
    12: ('zhi:辰', '寅'),    # 季冬 辰日 寅时
}
_MONTH_CN = {1:'正月',2:'二月',3:'三月',4:'四月',5:'五月',6:'六月',
             7:'七月',8:'八月',9:'九月',10:'十月',11:'仲冬',12:'季冬'}

# ── 又杀师日歌：节气月（按月建地支分四季）→ (忌日支, 忌时支) 二字并用 ──
# 憨爷 2026-08-17 纠正：「春遇辰戌正堪忧，只的日为辰时为戌就不行」→ 日支+时支 二字并用才忌，
# 单日=辰 或 单时=戌 都不忌。寅卯辰=春、巳午未=夏、申酉戌=秋、亥子丑=冬。
_SEASON_OF_ZHI = {'寅':'春','卯':'春','辰':'春','巳':'夏','午':'夏','未':'夏',
                 '申':'秋','酉':'秋','戌':'秋','亥':'冬','子':'冬','丑':'冬'}
_JI_SHASHI_DAY_SH = {
    '春': ('辰', '戌'),   # 日辰时戌（辰戌对冲）
    '夏': ('卯', '酉'),   # 日卯时酉（卯酉对冲）
    '秋': ('丑', '未'),   # 日丑时未（牛羊，丑未对冲）
    '冬': ('子', '午'),   # 日子时午（子午对冲）
}

# ── 犯雷日歌：日 + 时 ──
# 日：正月壬辰日、二月戊午日、子月(11)庚子日
FANLEI_DAY = {
    1:  '壬辰',  # 正月壬辰日
    2:  '戊午',  # 二月戊午日
    11: '庚子',  # 子月(十一月)庚子日
}
# 犯雷时：正月巳日卯时、二月午日巳时（与"杀师日时歌"已分离，2026-08-17 修正归属）
FANLEI_DAY_SH = {
    1:  ('zhi:巳', '卯'),  # 正月 巳日 卯时
    2:  ('zhi:午', '巳'),  # 二月 午日 巳时
}


def _lunar_month(date_str: str) -> Optional[int]:
    """公历 date_str(YYYY-MM-DD) → 农历月，失败 None。"""
    if not date_str or len(date_str) < 7:
        return None
    try:
        y, m, d = [int(x) for x in date_str.split('-')]
        import sxtwl
        day = sxtwl.fromSolar(y, m, d)
        return day.getLunarMonth()
    except Exception:
        return None


def _match_day_spec(rizhu: str, spec: str) -> bool:
    """spec 'zhi:巳' → 日支==巳；spec 'gan:癸' → 日干==癸。rizhu='癸酉'。"""
    if not rizhu or len(rizhu) < 2:
        return False
    if spec.startswith('zhi:'):
        return rizhu[1] == spec[4:]
    if spec.startswith('gan:'):
        return rizhu[0] == spec[4:]
    return False


def check_shashi(rizhu: str, nian_zhi: str = '', yue_zhi: str = '',
                 date_str: str = '', shichen: str = '') -> Dict:
    """杀师日/犯雷日判定（易郁《仪度六壬选日要诀》口诀）。
    rizhu: 日干支；nian_zhi: 年支（预留）；yue_zhi: 月建地支（节气月，用于又杀师日歌）；
    date_str: 公历 YYYY-MM-DD（sxtwl 算农历月）；shichen: 时辰地支。
    返回 {is_shashi, hits, level, note}。level: '犯雷日'/'杀师日'/'杀师时'。
    """
    hits: List[Tuple[str, str]] = []

    # === 杀师日时歌（按农历月+日+时，3-12 月；1-2 月 TODO） ===
    lm = _lunar_month(date_str) if date_str else None
    if lm and rizhu and shichen:
        day_spec, sh_spec = SHASHI_DAY_SH.get(lm, (None, None))
        if day_spec and sh_spec:
            if _match_day_spec(rizhu, day_spec) and shichen == sh_spec:
                hits.append(('杀师日时', f'{_MONTH_CN.get(lm, lm)}{day_spec[4:]}日{sh_spec}时（杀师日时歌）'))

    # === 又杀师日歌（按节气月，日支+时支 二字并用才忌） ===
    if yue_zhi and rizhu and len(rizhu) == 2 and shichen:
        season = _SEASON_OF_ZHI.get(yue_zhi, '')
        day_sh = _JI_SHASHI_DAY_SH.get(season)
        if day_sh and rizhu[1] == day_sh[0] and shichen == day_sh[1]:
            hits.append(('又杀师日', f'{season}季日{day_sh[0]}时{day_sh[1]}（又杀师日歌·二字并用）'))

    # === 犯雷日歌（按农历月+日柱完整） ===
    if lm and rizhu and len(rizhu) == 2:
        fl_rizhu = FANLEI_DAY.get(lm)
        if fl_rizhu and rizhu == fl_rizhu:
            hits.append(('犯雷日', f'{_MONTH_CN.get(lm, lm)}{fl_rizhu}日（犯雷日歌）'))
        # 犯雷时（正月巳日卯时、二月午日巳时）
        fl_day_spec, fl_sh = FANLEI_DAY_SH.get(lm, (None, None))
        if fl_day_spec and fl_sh and shichen == fl_sh:
            if _match_day_spec(rizhu, fl_day_spec):
                hits.append(('犯雷时', f'{_MONTH_CN.get(lm, lm)}{fl_day_spec[4:]}日{fl_sh}时（犯雷日歌）'))

    if not hits:
        return {'is_shashi': False, 'hits': [], 'level': '', 'note': ''}

    levels = [h[0] for h in hits]
    if '犯雷日' in levels or '犯雷时' in levels:
        level = '犯雷日'
    else:
        level = '杀师日'
    note = '此日/时妨害地理师/风水师本人（开罗盘、点穴、下葬、立碑动罗经之事），与主家吉凶无关；建议避开或由地师自行规避。'
    return {'is_shashi': True, 'hits': hits, 'level': level, 'note': note}


if __name__ == '__main__':
    # 自测 1：2026-02-22 丁卯日 午时（不应命中：非壬辰/非戊午/非巳卯时）
    print('2026-02-22 丁卯日 午时:', check_shashi('丁卯', '午', '寅', '2026-02-22', '午'))
    # 自测 2：犯雷日 - 2026 农历正月哪天是壬辰日？
    import sxtwl, sys
    sys.path.insert(0, '.')
    from engine.sizhu_engine import get_sizhu
    for d in range(1, 30):
        try:
            day = sxtwl.fromSolar(2026, 2, d)
            if day.getLunarMonth() == 1:
                sizhu = get_sizhu(2026, 2, d, '午')
                if sizhu['日柱'] == '壬辰':
                    print(f'2026-02-{d:02d} 正月壬辰日 犯雷日:', check_shashi('壬辰', '午', '寅', f'2026-02-{d:02d}', '午'))
        except Exception:
            pass
    # 自测 3：犯雷时 - 2026 农历正月哪天是巳日卯时？
    for d in range(1, 30):
        try:
            day = sxtwl.fromSolar(2026, 2, d)
            if day.getLunarMonth() == 1:
                sizhu = get_sizhu(2026, 2, d, '卯')
                if sizhu['日柱'][1] == '巳':
                    print(f'2026-02-{d:02d} 正月巳日卯时 犯雷时:', check_shashi(sizhu['日柱'], '午', '寅', f'2026-02-{d:02d}', '卯'))
        except Exception:
            pass
    # 自测 4：杀师日时歌 - 2026 农历三月未日丑时
    for d in range(1, 32):
        try:
            day = sxtwl.fromSolar(2026, 4, d)
            if day.getLunarMonth() == 3 and day.getLunarDay() >= 1:
                sizhu = get_sizhu(2026, 4, d, '丑')
                if sizhu['日柱'][1] == '未':
                    print(f'2026-04-{d:02d} 三月未日丑时 杀师日时:', check_shashi(sizhu['日柱'], '午', '辰', f'2026-04-{d:02d}', '丑'))
                    break
        except Exception:
            pass
    # 自测 5：又杀师日 - 春辰戌二字并用
    print('春辰戌（2026-03 某日辰日戌时）:', check_shashi('戊辰', '寅', '寅', '2026-03-15', '戌'))
