#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空亡三铁律审计模块 (engine/void_audit.py)
=========================================
【憨爷/用户拍板 2026-08-25】择日候选的空亡专项核查，三条铁律：

  ① 本命落旬空（可填补）：本命支落在日柱旬空 → 提示级（过旬/值年填实即可，安葬等长期之事不否决）
  ② 踏空（致命）：本命支本身不空，但本命所临的【地盘支】是旬空
       → 天盘本命支转动后落到的地盘位置为空亡，永远填不了（"踏空"），硬性否决
  ③ 乘天空（上下皆空，致命）：本命支乘天将"天空"（天空=空亡之将）
       → 本命逢旬空本可填补，但乘天空则上下皆空、必空，硬性否决

口径说明：
  - 旬空按【日柱】定旬（甲子/甲戌/甲申/甲午/甲辰/甲寅 六旬，每旬空 2 支 = 旬首 +10/+11）
  - 天地盘 _tdp 格式 {地盘支: 天盘支}
  - 天将映射 _tjm 格式 {地盘支: 天将}（GuiRenCalculator.arrange_gui_ren_pan 的 '天将映射'）
  - 本命临地盘 = 找 tdp 中"天盘支 == 本命支"对应的地盘支（本命上神所在的地盘）
  - 纯只读函数，不改任何状态；供 /api/zeri/batch 与 /api/zeri/analyze 共用

用法：
    from engine.void_audit import audit_void
    result = audit_void(ri_gan_zhi="甲午", tiandi_pan=tdp, tianjiang_map=tjm, ben_ming="辛亥")
    # result = {'xunkong': ['辰','巳'], 'ben_ming_void': False, 'tread_void': False,
    #           'ride_sky': False, 'level': '干净'|'提示'|'致命', 'reasons': [...], 'pass': True}
"""

# ── 旬空表：旬首（甲X）→ 空亡两支 ──
_XUNKONG = {
    ('甲', '子'): ('戌', '亥'),
    ('甲', '戌'): ('申', '酉'),
    ('甲', '申'): ('午', '未'),
    ('甲', '午'): ('辰', '巳'),
    ('甲', '辰'): ('寅', '卯'),
    ('甲', '寅'): ('子', '丑'),
}
_GAN = '甲乙丙丁戊己庚辛壬癸'
_ZHI = '子丑寅卯辰巳午未申酉戌亥'


def _get_xunkong(ri_gan_zhi):
    """由日柱（如"甲午"）推旬首，返回旬空两支列表。"""
    if not ri_gan_zhi or len(ri_gan_zhi) < 2:
        return []
    rg, rz = ri_gan_zhi[0], ri_gan_zhi[1]
    if rg not in _GAN or rz not in _ZHI:
        return []
    gi, zi = _GAN.index(rg), _ZHI.index(rz)
    # 倒推回旬首（天干为甲）
    back = 0
    while _GAN[(gi - back) % 10] != '甲' and back < 12:
        back += 1
    if back >= 12:
        return []
    head_zhi = _ZHI[(zi - back) % 12]
    x1 = _ZHI[(_ZHI.index(head_zhi) + 10) % 12]
    x2 = _ZHI[(_ZHI.index(head_zhi) + 11) % 12]
    return [x1, x2]


def _ben_ming_zhi(ben_ming):
    """从本命（60甲子 或 单地支）提取本命支。"""
    if not ben_ming:
        return ''
    bm = str(ben_ming).strip()
    if len(bm) >= 2 and bm[-1] in _ZHI:
        return bm[-1]
    if bm in _ZHI:
        return bm
    return ''


def _tread_position(tiandi_pan, ben_ming_zhi):
    """
    本命所临的地盘支：找天地盘中"天盘支 == 本命支"对应的地盘支。
    tdp = {地盘: 天盘}；本命支作为天盘（转动后）落在某地盘上。
    """
    if not tiandi_pan or not ben_ming_zhi:
        return ''
    for di, tian in tiandi_pan.items():
        if tian == ben_ming_zhi:
            return di
    return ''


def audit_void(ri_gan_zhi='', tiandi_pan=None, tianjiang_map=None, ben_ming=''):
    """
    空亡三铁律审计。

    参数：
        ri_gan_zhi: 日柱干支，如 "甲午"（用于定旬空）
        tiandi_pan: {地盘支: 天盘支}
        tianjiang_map: {地盘支: 天将}（天将映射）
        ben_ming: 本命，60甲子（如"辛亥"）或单地支（如"亥"）

    返回 dict：
        xunkong: 旬空两支列表
        ben_ming_zhi: 本命支
        ben_ming_void: 本命是否落旬空（①可填补）
        tread_zhi: 本命所临地盘支
        tread_void: 是否踏空（②致命）
        ride_general: 本命所乘天将
        ride_sky: 是否乘天空（③致命）
        level: '致命' / '提示' / '干净'
        reasons: 命中的铁律说明列表
        pass: True=可用（无致命），False=致命否决
    """
    xk = _get_xunkong(ri_gan_zhi)
    bmz = _ben_ming_zhi(ben_ming)
    tread_zhi = _tread_position(tiandi_pan, bmz)
    ride_gen = ''
    if tianjiang_map and bmz:
        ride_gen = tianjiang_map.get(bmz, '') or ''

    ben_ming_void = bool(bmz and bmz in xk)
    tread_void = bool(tread_zhi and tread_zhi in xk)
    ride_sky = bool(ride_gen == '天空')

    reasons = []
    if ben_ming_void:
        reasons.append(f'本命{bmz}落旬空({",".join(xk)})——过旬/值年{bmz}可填实，非致命')
    if tread_void:
        reasons.append(f'本命{bmz}临地盘{tread_zhi}(旬空)——踏空，永远填不了，致命')
    if ride_sky:
        reasons.append(f'本命{bmz}乘天空——上下皆空，真空，致命')

    if tread_void or ride_sky:
        level = '致命'
    elif ben_ming_void:
        level = '提示'
    else:
        level = '干净'

    return {
        'xunkong': xk,
        'ben_ming_zhi': bmz,
        'ben_ming_void': ben_ming_void,
        'tread_zhi': tread_zhi,
        'tread_void': tread_void,
        'ride_general': ride_gen,
        'ride_sky': ride_sky,
        'level': level,
        'reasons': reasons,
        'pass': level != '致命',
    }


# ── 自测（python engine/void_audit.py）──
if __name__ == '__main__':
    # 已知案例（来自 10 年扫描验证）
    cases = [
        # (日柱, 天地盘, 天将映射, 本命, 期望 level)
        ('甲午', {'丑': '子', '亥': '戌', '午': '巳', '卯': '寅', '子': '亥', '寅': '丑',
                  '巳': '辰', '戌': '酉', '未': '午', '申': '未', '辰': '卯', '酉': '申'},
         {'丑': '天空', '亥': '太常', '午': '螣蛇', '卯': '勾陈', '子': '白虎', '寅': '青龙',
          '巳': '朱雀', '戌': '玄武', '未': '贵人', '申': '天后', '辰': '六合', '酉': '太阴'},
         '辛亥', '干净'),   # 2030-02-28 子：空辰巳，亥不空，临子不空，乘太常
        ('庚午', {'丑': '丑', '亥': '亥', '午': '午', '卯': '卯', '子': '子', '寅': '寅',
                  '巳': '巳', '戌': '戌', '未': '未', '申': '申', '辰': '辰', '酉': '酉'},
         {'丑': '贵人', '亥': '太阴', '午': '青龙', '卯': '朱雀', '子': '天后', '寅': '螣蛇',
          '巳': '勾陈', '戌': '玄武', '未': '天空', '申': '白虎', '辰': '六合', '酉': '太常'},
         '辛亥', '致命'),   # 2032-09-21 巳：伏吟盘，甲子旬空戌亥，本命亥落空+临亥=踏空
        ('甲寅', {'丑': '子', '亥': '戌', '午': '巳', '卯': '寅', '子': '亥', '寅': '丑',
                  '巳': '辰', '戌': '酉', '未': '午', '申': '未', '辰': '卯', '酉': '申'},
         {'丑': '天空', '亥': '太常', '午': '螣蛇', '卯': '勾陈', '子': '白虎', '寅': '青龙',
          '巳': '朱雀', '戌': '玄武', '未': '贵人', '申': '天后', '辰': '六合', '酉': '太阴'},
         '辛亥', '致命'),   # 2034-04-28 戌：甲寅旬空子丑，亥临地盘子=踏空
        ('癸卯', {'丑': '巳', '亥': '卯', '午': '戌', '卯': '未', '子': '辰', '寅': '午',
                  '巳': '酉', '戌': '寅', '未': '亥', '申': '子', '辰': '申', '酉': '丑'},
         {'丑': '太常', '亥': '天空', '午': '螣蛇', '卯': '太阴', '子': '白虎', '寅': '玄武',
          '巳': '贵人', '戌': '青龙', '未': '朱雀', '申': '六合', '辰': '天后', '酉': '勾陈'},
         '辛亥', '致命'),   # 2029-05-13 巳：真实盘，本命亥乘天空=真空
    ]
    print("== void_audit 自测 ==")
    for c in cases:
        r = audit_void(c[0], c[1], c[2], c[3])
        ok = '✅' if r['level'] == c[4] else '❌'
        print(f"{ok} 日柱={c[0]} 本命={c[3]} 期望={c[4]} 实得={r['level']} | "
              f"空=[{','.join(r['xunkong'])}] 落空={r['ben_ming_void']} "
              f"临{r['tread_zhi']}踏空={r['tread_void']} 乘{r['ride_general']} "
              f"| {'; '.join(r['reasons']) or '干净'}")
