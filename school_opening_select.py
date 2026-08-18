#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开学择日——2026年8月16-28日，坐子向午"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.sizhu_engine import get_sizhu
from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
from engine.yidu_liuren_yaojue import analyze_yidu_full, LU, get_yima
from engine.gui_ren_engine import GuiRenCalculator
from data.斗首择日规则 import GUIREN
from datetime import date, timedelta

# 吉将/凶将
JI_JIANG = {'贵人','青龙','六合','太常','太阴','天后'}
XIONG_JIANG = {'白虎','玄武','螣蛇','天空','勾陈','朱雀'}

# 十二长生（日干→长生地支）
CHANGSHENG_POS = {
    '甲':'亥','乙':'午','丙':'寅','丁':'酉','戊':'寅',
    '己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯',
}

# 六十花甲子
JIAZI = []
for i in range(60):
    g = '甲乙丙丁戊己庚辛壬癸'[i%10]
    z = '子丑寅卯辰巳午未申酉戌亥'[i%12]
    JIAZI.append(g+z)

# 旬空
XUN_KONG = {
    0: ['戌','亥'], 10: ['申','酉'], 20: ['午','未'],
    30: ['辰','巳'], 40: ['寅','卯'], 50: ['子','丑'],
}

def get_xunkong(ri_zhu):
    idx = JIAZI.index(ri_zhu)
    xun_start = (idx // 10) * 10
    return XUN_KONG.get(xun_start, [])

# 旺相休囚
WX_MAP = {'寅卯':'木','巳午':'火','申酉':'金','亥子':'水','辰戌丑未':'土'}
WX_SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}

def get_wx(zhi):
    for k,v in WX_MAP.items():
        if zhi in k: return v
    return ''

def is_xiu_qiu(chuan_zhi, yue_zhi):
    wx_c = get_wx(chuan_zhi)
    wx_yue = get_wx(yue_zhi)
    wang = wx_yue
    xiang = WX_SHENG.get(wang,'')
    if wx_c == wang: return False  # 旺
    if wx_c == xiang: return False  # 相
    return True  # 休囚死

# 刑冲
CHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅',
         '卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
XING = {'寅':'巳','巳':'申','申':'寅','丑':'戌','戌':'未','未':'丑','子':'卯','卯':'子'}
HAI = {'子':'未','未':'子','丑':'午','午':'丑','寅':'巳','巳':'寅',
       '卯':'辰','辰':'卯','申':'亥','亥':'申','酉':'戌','戌':'酉'}
KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

def has_xingchong(chuan_zhi, ri_zhi, yue_zhi):
    issues = []
    if CHONG.get(chuan_zhi) == ri_zhi: issues.append('冲日支')
    if CHONG.get(chuan_zhi) == yue_zhi: issues.append('冲月建')
    if XING.get(chuan_zhi) == ri_zhi: issues.append('刑日支')
    if HAI.get(chuan_zhi) == ri_zhi: issues.append('害日支')
    wx_c, wx_r = get_wx(chuan_zhi), get_wx(ri_zhi)
    if KE.get(wx_r) == wx_c: issues.append('日支克')
    return issues


# ═══════════════════ 主程序 ═══════════════════

print('='*80)
print('  学校开学择日: 2026-08-16 ~ 2026-08-28')
print('  坐子向午 | 时辰: 辰巳午未')
print('  核心条件: 禄/马/贵人/长生 至少一发出三传')
print('  附加要求: 不落空、不踏空、不休囚、不刑冲克害')
print('='*80)

gui_calc = GuiRenCalculator()
lm = DaLiuRenLuMaGuiRen()
candidates = []

start = date(2026, 8, 16)
end = date(2026, 8, 28)
current = start

while current <= end:
    for shichen in ['辰','巳','午','未']:
        y,m,d = current.year, current.month, current.day
        sizhu = get_sizhu(y,m,d,shichen)
        ng,nz = sizhu['年柱'][0], sizhu['年柱'][1]
        yg,yz = sizhu['月柱'][0], sizhu['月柱'][1]
        rg,rz = sizhu['日柱'][0], sizhu['日柱'][1]
        sg,sz = sizhu['时柱'][0], sizhu['时柱'][1]
        ri_zhu = rg + rz

        # 日干长生/禄/马/贵人
        cs = CHANGSHENG_POS.get(rg,'')
        lu = LU.get(rg,'')
        ma = get_yima(rz)
        guiren = list(GUIREN.get(rg,[]))

        # 旬空
        xunkong = get_xunkong(ri_zhu)

        # 天地盘 + 三传（2026-08-17 清理：月将精确中气 + V2 权威引擎）
        yj = lm.get_yuejiang_by_date(y, m, d)
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        r = SiKeSanChuanCalculator2().calculate(rg, rz, yj, shichen)
        sc_v2 = r['sanchuan']
        cl = [sc_v2.get('初传', ''), sc_v2.get('中传', ''), sc_v2.get('末传', '')]
        cl = [c for c in cl if c]
        if not cl: continue
        sc_out = {'初传': cl[0], '中传': cl[1] if len(cl)>1 else '', '末传': cl[2] if len(cl)>2 else ''}
        tp = {'天地对应': r['tiandi_pan']}  # 兼容 gui_ren_engine/analyze_yidu_full 的旧结构

        # 核心条件: 禄马贵长生至少一在三传
        chuan_set = set(cl)
        cs_in = cs in chuan_set
        lu_in = lu in chuan_set
        ma_in = ma in chuan_set
        gui_in = any(g in chuan_set for g in guiren[:2])

        if not (cs_in or lu_in or ma_in or gui_in):
            continue

        # 检查不落空
        chuan_kong = [c for c in cl if c in xunkong]

        # 检查不休囚
        chuan_xiuqiu = [c for c in cl if is_xiu_qiu(c, yz)]

        # 检查不刑冲
        chuan_xc = []
        for c in cl:
            iss = has_xingchong(c, rz, yz)
            if iss:
                chuan_xc.append((c, iss))

        # 天将
        try:
            gp = gui_calc.arrange_gui_ren_pan(rg, tp, shichen)
            tj_map = gp.get('天将映射', {})
        except:
            tj_map = {}

        # 吉将
        chuan_jj = []
        for c in cl:
            tj = tj_map.get(c, '')
            if tj in JI_JIANG:
                chuan_jj.append(f'{c}({tj})')

        # 综合择日评分
        tp_simple = tp.get('天地对应', {})
        analysis = analyze_yidu_full(
            shan='子', year_pillar=ng+nz, month_pillar=yg+yz,
            day_pillar=rg+rz, hour_pillar=sg+sz,
            ri_gan=rg, ri_zhi=rz, sanchuan=sc_out, tiandi_pan=tp_simple,
            yue_jiang=yj, nian_zhi=nz,
        )

        # 扣分
        penalty = len(chuan_kong)*15 + len(chuan_xiuqiu)*10 + len(chuan_xc)*8
        score = max(10, min(100, analysis['total_score'] - penalty))

        hit_items = []
        if cs_in: hit_items.append('长生')
        if lu_in: hit_items.append('禄')
        if ma_in: hit_items.append('马')
        if gui_in: hit_items.append('贵人')

        candidates.append({
            'date': current.strftime('%Y-%m-%d'),
            'shichen': shichen,
            'sizhu': f'{ng}{nz} {yg}{yz} {rg}{rz} {sg}{sz}',
            'ri_gan': rg, 'ri_zhi': rz,
            'changsheng': cs, 'lu': lu, 'ma': ma, 'guiren': guiren,
            'sanchuan': sc_out,
            'hit': hit_items,
            'chuan_kong': chuan_kong,
            'chuan_xiuqiu': chuan_xiuqiu,
            'chuan_xc': chuan_xc,
            'chuan_jj': chuan_jj,
            'xunkong': xunkong,
            'score': score,
            'grade': analysis['grade'],
            'doushou': analysis['doushou']['classes'],
            'yuanchen': analysis['doushou']['yuanchen_check']['has_yuanchen'],
            'gong': len([p for p in analysis['gong_patterns'] if p.get('matched')]),
            'huoma': analysis['huoma_huolu']['count'],
            'dsdx': analysis['daoshan_daoxiang']['total_count'],
            'analysis': analysis,
        })

    current += timedelta(days=1)

# 排序
candidates.sort(key=lambda x: x['score'], reverse=True)

print(f'\n找到 {len(candidates)} 个合格候选\n')

for i, c in enumerate(candidates[:12]):
    p = []
    if c['chuan_kong']: p.append(f'空亡:{c["chuan_kong"]}')
    if c['chuan_xiuqiu']: p.append(f'休囚:{c["chuan_xiuqiu"]}')
    if c['chuan_xc']: p.append(f'刑冲:{c["chuan_xc"]}')

    star = '⭐' if c['score'] >= 80 else ('✅' if c['score'] >= 65 else '')
    print(f'{star} #{i+1}  {c["date"]} {c["shichen"]}时 | {c["sizhu"]} | 总分:{c["score"]:.0f} [{c["grade"]}]')
    print(f'    三传: {c["sanchuan"]["初传"]}→{c["sanchuan"]["中传"]}→{c["sanchuan"]["末传"]}')
    print(f'    命中: {"、".join(c["hit"])}')
    print(f'    吉将: {", ".join(c["chuan_jj"]) if c["chuan_jj"] else "无"}')
    print(f'    旬空: {" ".join(c["xunkong"])}')
    if p: print(f'    ⚠️ {"; ".join(p)}')
    print(f'    斗首: {c["doushou"]} | 拱{c["gong"]}活{c["huoma"]}到{c["dsdx"]}')
    print()

if not candidates:
    print('❌ 无合格候选！以下为范围内所有日柱：')
    cur = start
    while cur <= end:
        for sc_name in ['辰','巳','午','未']:
            sz = get_sizhu(cur.year, cur.month, cur.day, sc_name)
            rg2,rz2 = sz['日柱'][0], sz['日柱'][1]
            cs2 = CHANGSHENG_POS.get(rg2,'')
            print(f'{cur} {sc_name}时  日柱{rg2}{rz2}  长生{cs2}')
        cur += timedelta(days=1)
