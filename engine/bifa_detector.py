#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋100法检测引擎 v1.0
========================

基于大六壬课式信息，检测适用的毕法赋法条。
输入：三传、日干、日支、四课信息、天将等
输出：匹配的法条列表及股市信号

创建日期: 2026-07-29
数据来源: data/bifa_100_knowledge_base.json + 古籍注解上/下卷
"""

import json
import os
from typing import List, Dict, Optional, Tuple, Set

# 加载知识库
_KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bifa_100_knowledge_base.json')
_bifa_kb = None

def _load_kb():
    global _bifa_kb
    if _bifa_kb is None:
        with open(_KB_PATH, 'r', encoding='utf-8') as f:
            _bifa_kb = json.load(f)
    return _bifa_kb


# ============ 五行基础 ============
WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
    '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
    '戌': '土', '亥': '水',
}

GAN_WUXING = {k: v for k, v in WUXING.items() if k in '甲乙丙丁戊己庚辛壬癸'}
ZHI_WUXING = {k: v for k, v in WUXING.items() if k in '子丑寅卯辰巳午未申酉戌亥'}

# 天干→禄神
LU_SHEN = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
           '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# 天干→寄宫（地盘本位：阳干寄临官，阴干寄冠带）
GAN_JIGONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
              '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}

# 天干→长生（五行长生口径；【BUG-FIX 2026-08-18 案例实证】案例原文"辛长生于巳"
# （金长生巳，非阴阳长生辛子）、"癸绝于巳"、"丁绝于亥"——全部五行长生/绝，
# 0 例十干阴阳长生。故弃十干阴阳表（原乙午丁酉己酉辛子癸卯），统一五行长生。
# 土双位见 WX_CHANG_SHENG；此处单值用于十干单值场景。
CHANG_SHENG = {'甲': '亥', '乙': '亥', '丙': '寅', '丁': '寅', '戊': '申',
               '己': '申', '庚': '巳', '辛': '巳', '壬': '申', '癸': '申'}

# 天干→墓（三合五行墓：木未/火戌/金丑/水辰/土辰）
# 2026-08-15 憨爷指正："庚辛申酉金墓在丑"，天干墓按五行三合墓，非十干阴阳长生墓（辛墓非辰乃丑）
# 【BUG-FIX 2026-08-18 案例实证】"辛墓于丑""庚辛墓于丑"→ 五行墓确认
MU = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
      '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}

# 天干→绝（五行绝；【BUG-FIX 2026-08-18 案例实证】"癸绝于巳""丁绝于亥"→ 五行绝）
JUE = {'甲': '申', '乙': '申', '丙': '亥', '丁': '亥', '戊': '巳',
       '己': '巳', '庚': '寅', '辛': '寅', '壬': '巳', '癸': '巳'}

# 天干→胎神（五行胎；土双位见 WX_TAI_SHUANG）
TAI_SHEN = {'甲': '酉', '乙': '酉', '丙': '子', '丁': '子', '戊': '午',
            '己': '午', '庚': '卯', '辛': '卯', '壬': '午', '癸': '午'}

# 天干→败气（沐浴；五行沐浴）
BAI = {'甲': '子', '乙': '子', '丙': '卯', '丁': '卯', '戊': '酉',
       '己': '酉', '庚': '午', '辛': '午', '壬': '酉', '癸': '酉'}

# 五行十二长生双位（憨爷拍板 2026-08-16）：土双位（水土同宫主值 + 火土同宫次值）
WX_CHANG_SHENG = {'木': ('亥',), '火': ('寅',), '土': ('申', '寅'), '金': ('巳',), '水': ('申',)}
# 五行胎位双位（憨爷拍板 2026-08-16）：土双位（土胎午/子）
WX_TAI_SHUANG = {'木': ('酉',), '火': ('子',), '土': ('午', '子'), '金': ('卯',), '水': ('午',)}
# 五行死位双位（十二长生死=长生+7；土双位：土死卯/酉）
WX_SI_SHUANG = {'木': ('午',), '火': ('酉',), '土': ('卯', '酉'), '金': ('子',), '水': ('卯',)}


def _gan_wx_changsheng(ri_gan: str):
    """日干的五行十二长生位（双位 tuple，土为 ('申','寅')）"""
    wx = GAN_WUXING.get(ri_gan, '')
    return WX_CHANG_SHENG.get(wx, ())


def _gan_wx_tai(ri_gan: str):
    """日干的五行胎位（双位 tuple，土为 ('午','子')）"""
    wx = GAN_WUXING.get(ri_gan, '')
    return WX_TAI_SHUANG.get(wx, ())


def _wx_si(wx: str):
    """五行的死位（双位 tuple，土为 ('卯','酉')）"""
    return WX_SI_SHUANG.get(wx, ())

# 地支→旺神（当令之地）
ZHI_WANG = {'子': '子', '丑': '丑', '寅': '寅', '卯': '卯', '辰': '辰',
            '巳': '巳', '午': '午', '未': '未', '申': '申', '酉': '酉',
            '戌': '戌', '亥': '亥'}

# 地支顺序
DIZHI_ORDER = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
DIZHI_INDEX = {z: i for i, z in enumerate(DIZHI_ORDER)}

# 六合
LIUHE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯',
         '辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}

# 六害
LIUHAI = {'子':'未','未':'子','丑':'午','午':'丑','寅':'巳','巳':'寅',
          '卯':'辰','辰':'卯','申':'亥','亥':'申','酉':'戌','戌':'酉'}

# 六冲
LIUCHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅',
            '卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}

# 三刑
SANXING = {
    '寅': '巳', '巳': '申', '申': '寅',  # 无恩刑
    '丑': '戌', '戌': '未', '未': '丑',  # 恃势刑
    '子': '卯', '卯': '子',              # 无礼刑
    '辰': '辰', '午': '午', '酉': '酉', '亥': '亥',  # 自刑
}

# 三合局
SANHE_JU = {
    '申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金',
}

# 三合局对应的犯杀表（自刑/六害/冲） — 第84法
SANHE_SHANG = {
    '火': {'刑': '午', '害': '丑', '冲': '子'},  # 寅午戌
    '木': {'刑': '子', '害': '辰', '冲': '酉'},  # 亥卯未
    '水': {'刑': '卯', '害': '未', '冲': '午'},  # 申子辰
    '金': {'刑': '酉', '害': '戌', '冲': '卯'},  # 巳酉丑
}

# 月将→季节（月将是太阳过宫，中气换将：雨水后亥将…大寒后子将；
# 【BUG-FIX 2026-08-18】原表误用"月建"表（寅卯辰=春…），月将≠月建，错位一组。
# 月将对应：亥戌酉=春、申未午=夏、巳辰卯=秋、寅丑子=冬）
YUEJIANG_SEASON = {
    '亥': '春', '戌': '春', '酉': '春',
    '申': '夏', '未': '夏', '午': '夏',
    '巳': '秋', '辰': '秋', '卯': '秋',
    '寅': '冬', '丑': '冬', '子': '冬',
}

# 季节→五行旺
SEASON_WANG = {'春': '木', '夏': '火', '秋': '金', '冬': '水'}

# 天将→五行
TIANJIANG_WUXING = {
    '贵人': '土', '螣蛇': '火', '朱雀': '火', '六合': '木', '勾陈': '土',
    '青龙': '木', '天空': '土', '白虎': '金', '太常': '土', '玄武': '水',
    '太阴': '金', '天后': '水',
}

# 天将→本家地支（天将正位/本宫，生克以本家五行为准）
# 2026-08-15 憨爷指正：天将本家是天将的固定本位地支（如白虎本家申金、青龙本家寅木、
# 天后本家子水、玄武本家亥水），与"天将临时所乘地盘"是两回事。判断"脱上逢脱"等
# 涉及天将生克时，必须用本家地支的五行，绝不能用天将名字。
# 出处：《六壬大全》十二天将正位（贵丑、蛇巳、雀午、合卯、勾辰、龙寅、空戌、虎申、常未、武亥、阴酉、后子）。
TIANJIANG_BENJIA = {
    '贵人': '丑', '螣蛇': '巳', '朱雀': '午', '六合': '卯', '勾陈': '辰',
    '青龙': '寅', '天空': '戌', '白虎': '申', '太常': '未', '玄武': '亥',
    '太阴': '酉', '天后': '子',
}

# 驿马: 申子辰→寅, 亥卯未→巳, 寅午戌→申, 巳酉丑→亥
YIMA = {
    '申': '寅', '子': '寅', '辰': '寅',
    '亥': '巳', '卯': '巳', '未': '巳',
    '寅': '申', '午': '申', '戌': '申',
    '巳': '亥', '酉': '亥', '丑': '亥',
}

# 日干→(昼贵, 夜贵) 天乙贵人
GUIREN_MAP = {
    '甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
    '乙': ('子', '申'), '己': ('子', '申'),
    '丙': ('亥', '酉'), '丁': ('亥', '酉'),
    '壬': ('卯', '巳'), '癸': ('卯', '巳'),
    '辛': ('午', '寅'),
}

# 五行→墓
WUXING_MU = {'木': '未', '火': '戌', '土': '辰', '金': '丑', '水': '辰'}


# ============ 旬空计算 ============
XUN_GROUPS = [
    ('甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉'),  # 戌亥空
    ('甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未'),  # 申酉空
    ('甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳'),  # 午未空
    ('甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯'),  # 辰巳空
    ('甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑'),  # 寅卯空
    ('甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'),  # 子丑空
]

XUN_KONG_MAP = {}
for group in XUN_GROUPS:
    empty_1 = DIZHI_ORDER[(DIZHI_INDEX[group[-1][1]] + 1) % 12]
    empty_2 = DIZHI_ORDER[(DIZHI_INDEX[group[-1][1]] + 2) % 12]
    for gz in group:
        XUN_KONG_MAP[gz] = (empty_1, empty_2)

# 旬首
XUN_SHOU = {}
for group in XUN_GROUPS:
    for gz in group:
        XUN_SHOU[gz] = group[0]

# 旬尾
XUN_WEI = {}
for group in XUN_GROUPS:
    for gz in group:
        XUN_WEI[gz] = group[-1]

# 旬丁: 各旬的丁神地支
XUN_DING = {
    '甲子': '卯',  # 丁卯
    '甲戌': '丑',  # 丁丑
    '甲申': '亥',  # 丁亥
    '甲午': '酉',  # 丁酉
    '甲辰': '未',  # 丁未
    '甲寅': '巳',  # 丁巳
}

# 旬干对照: 旬首 → {地支: 天干}
XUN_GAN_MAP = {}
for _grp in XUN_GROUPS:
    _xun_shou = _grp[0]
    _gan_map = {}
    for _gz in _grp:
        _gan_map[_gz[1]] = _gz[0]  # 地支 → 天干
    XUN_GAN_MAP[_xun_shou] = _gan_map


def _get_zhi_mu(zhi: str) -> str:
    """获取地支的墓（按五行墓）"""
    wx = ZHI_WUXING.get(zhi, '')
    return WUXING_MU.get(wx, '')

# 旬丁神: 每旬中遁干为丁的地支
DING_SHEN = {}
for group in XUN_GROUPS:
    for gz in group:
        if gz[0] == '丁':
            DING_SHEN[group[0]] = gz[1]
            break

# 旬遁干表: 每旬中每个地支对应的遁干
XUN_DUNGAN = {}
for group in XUN_GROUPS:
    dun_map = {}
    for gz in group:
        dun_map[gz[1]] = gz[0]
    XUN_DUNGAN[group[0]] = dun_map


def get_ding_shen(ganzhi: str) -> str:
    """获取干支所在旬的丁神地支"""
    xun_shou = XUN_SHOU.get(ganzhi, '')
    return DING_SHEN.get(xun_shou, '')


def get_dun_gan(ganzhi: str, zhi: str) -> str:
    """获取某地支在当前旬中的遁干"""
    xun_shou = XUN_SHOU.get(ganzhi, '')
    dun_map = XUN_DUNGAN.get(xun_shou, {})
    return dun_map.get(zhi, '')


def get_xun_kong(ganzhi: str) -> Tuple[str, str]:
    """获取干支的旬空地支"""
    return XUN_KONG_MAP.get(ganzhi, ('', ''))


def get_xun_shou(ganzhi: str) -> str:
    """获取干支所在旬的旬首"""
    return XUN_SHOU.get(ganzhi, '')


def get_xun_wei(ganzhi: str) -> str:
    """获取干支所在旬的旬尾"""
    return XUN_WEI.get(ganzhi, '')


def get_fen_xun_kong(ganzhi: str):
    """分旬空亡（进茹/踏脚空亡用）：返回 {本旬/前旬/后旬/外前旬/外后旬: set(地支)}。
    旬空=旬尾+1、+2（即旬首+10、+11）；后旬（下一旬）=旬首-2，前旬（上一旬）=旬首+2。"""
    xun_shou = get_xun_shou(ganzhi)
    if not xun_shou:
        return None
    shou_idx = DIZHI_INDEX.get(xun_shou[1], -1)
    if shou_idx < 0:
        return None
    def _pair(offset):
        return {DIZHI_ORDER[(shou_idx + offset) % 12], DIZHI_ORDER[(shou_idx + offset + 1) % 12]}
    return {
        '本旬': _pair(10),
        '前旬': _pair(0),
        '后旬': _pair(8),
        '外前旬': _pair(2),
        '外后旬': _pair(6),
    }


def get_xun_ding(ganzhi: str) -> str:
    """获取干支所在旬的丁神地支（旬丁）"""
    xun_shou = get_xun_shou(ganzhi)
    if xun_shou:
        return XUN_DING.get(xun_shou, '')
    return ''


# ============ 三传走势判断 ============
def _is_shun_lianru(dizhi_list: List[str]) -> bool:
    """判断是否为顺连茹（三传连续顺行）"""
    if len(dizhi_list) != 3:
        return False
    idx = [DIZHI_INDEX.get(z, -1) for z in dizhi_list]
    return (-1 not in idx) and (idx[1] == (idx[0] + 1) % 12) and (idx[2] == (idx[1] + 1) % 12)


def _is_ni_lianru(dizhi_list: List[str]) -> bool:
    """判断是否为逆连茹（三传连续逆行）"""
    if len(dizhi_list) != 3:
        return False
    idx = [DIZHI_INDEX.get(z, -1) for z in dizhi_list]
    return (-1 not in idx) and (idx[1] == (idx[0] - 1) % 12) and (idx[2] == (idx[1] - 1) % 12)


def _is_shun_jianchuan(dizhi_list: List[str]) -> bool:
    """判断是否为顺间传（三传隔一顺行）"""
    if len(dizhi_list) != 3:
        return False
    idx = [DIZHI_INDEX.get(z, -1) for z in dizhi_list]
    return (-1 not in idx) and (idx[1] == (idx[0] + 2) % 12) and (idx[2] == (idx[1] + 2) % 12)


def _is_ni_jianchuan(dizhi_list: List[str]) -> bool:
    """判断是否为逆间传（三传隔一逆行）"""
    if len(dizhi_list) != 3:
        return False
    idx = [DIZHI_INDEX.get(z, -1) for z in dizhi_list]
    return (-1 not in idx) and (idx[1] == (idx[0] - 2) % 12) and (idx[2] == (idx[1] - 2) % 12)


def _is_sanhe_ju(dizhi_list: List[str]) -> Optional[str]:
    """判断是否为三合局，返回五行"""
    if len(dizhi_list) != 3:
        return None
    # 检查所有可能的排列
    for k, v in SANHE_JU.items():
        chars = set(k)
        if set(dizhi_list) == chars:
            return v
    return None


def _get_sanchuan_trend(dizhi_list: List[str]) -> str:
    """获取三传走势类型"""
    if _is_shun_lianru(dizhi_list):
        return '进连茹'
    if _is_ni_lianru(dizhi_list):
        return '退连茹'
    if _is_shun_jianchuan(dizhi_list):
        return '顺间传'
    if _is_ni_jianchuan(dizhi_list):
        return '逆间传'
    s = _is_sanhe_ju(dizhi_list)
    if s:
        return f'{s}局三合'
    return '其他'


# ============ 日干关系判断 ============
def _gan_sheng_gan(gan1: str, gan2: str) -> bool:
    """判断 gan1 生 gan2"""
    wx1 = GAN_WUXING.get(gan1)
    wx2 = GAN_WUXING.get(gan2)
    return _wuxing_sheng(wx1, wx2)


def _gan_ke_gan(gan1: str, gan2: str) -> bool:
    """判断 gan1 克 gan2"""
    wx1 = GAN_WUXING.get(gan1)
    wx2 = GAN_WUXING.get(gan2)
    return _wuxing_ke(wx1, wx2)


def _wuxing_sheng(wx1: Optional[str], wx2: Optional[str]) -> bool:
    """五行相生: wx1 生 wx2"""
    if not wx1 or not wx2:
        return False
    return (wx1 == '木' and wx2 == '火') or (wx1 == '火' and wx2 == '土') or \
           (wx1 == '土' and wx2 == '金') or (wx1 == '金' and wx2 == '水') or \
           (wx1 == '水' and wx2 == '木')


def _wuxing_ke(wx1: Optional[str], wx2: Optional[str]) -> bool:
    """五行相克: wx1 克 wx2"""
    if not wx1 or not wx2:
        return False
    return (wx1 == '木' and wx2 == '土') or (wx1 == '土' and wx2 == '水') or \
           (wx1 == '水' and wx2 == '火') or (wx1 == '火' and wx2 == '金') or \
           (wx1 == '金' and wx2 == '木')


def _is_gan_wealth(gan: str, zhi: str) -> bool:
    """判断地支是否为日干的财"""
    if not gan or not zhi:
        return False
    wg = GAN_WUXING.get(gan)
    wz = ZHI_WUXING.get(zhi)
    if not wg or not wz:
        return False
    # 日干克者为财 (我克者为财)
    return _wuxing_ke(wg, wz)


def _is_gan_ghost(gan: str, zhi: str) -> bool:
    """判断地支是否为日干的鬼（官鬼）"""
    wg = GAN_WUXING.get(gan)
    wz = ZHI_WUXING.get(zhi)
    if not wg or not wz:
        return False
    # 克日干者为鬼
    return _wuxing_ke(wz, wg)


def _is_gan_parent(gan: str, zhi: str) -> bool:
    """判断地支是否为日干的父母（生我者）"""
    wg = GAN_WUXING.get(gan)
    wz = ZHI_WUXING.get(zhi)
    if not wg or not wz:
        return False
    return _wuxing_sheng(wz, wg)


def _is_gan_child(gan: str, zhi: str) -> bool:
    """判断地支是否为日干的子孙（我生者）"""
    wg = GAN_WUXING.get(gan)
    wz = ZHI_WUXING.get(zhi)
    if not wg or not wz:
        return False
    return _wuxing_sheng(wg, wz)


def _is_gan_sibling(gan: str, zhi: str) -> bool:
    """判断地支是否与日干同类（比肩）"""
    wg = GAN_WUXING.get(gan)
    wz = ZHI_WUXING.get(zhi)
    return wg == wz


def _zhi_sheng_zhi(z1: str, z2: str) -> bool:
    """判断 z1 生 z2（地支五行相生；z1/z2 也可为天干，第77法天干互生用）"""
    return _wuxing_sheng(ZHI_WUXING.get(z1) or GAN_WUXING.get(z1), ZHI_WUXING.get(z2) or GAN_WUXING.get(z2))


def _zhi_ke_zhi(z1: str, z2: str) -> bool:
    """判断 z1 克 z2（地支五行相克；z1/z2 也可为天干）"""
    return _wuxing_ke(ZHI_WUXING.get(z1) or GAN_WUXING.get(z1), ZHI_WUXING.get(z2) or GAN_WUXING.get(z2))


# ============ 季节相关 ============
def _get_yue_ling_season(yuejiang: str) -> str:
    """从月将获取月令季节"""
    yj = yuejiang.replace('将', '').strip() if yuejiang else ''
    return YUEJIANG_SEASON.get(yj, '')


def _get_season_yuefen(season: str) -> List[int]:
    """获取季节对应的月份"""
    return {'春': [1,2,3], '夏': [4,5,6], '秋': [7,8,9], '冬': [10,11,12]}.get(season, [])


# 月令生气: 正月在子顺行
def _get_sheng_qi(yuejiang: str) -> str:
    """获取月令生气方位"""
    yj = yuejiang.replace('将', '').strip() if yuejiang else ''
    idx = DIZHI_INDEX.get(yj, -1)
    if idx == -1:
        return ''
    # 月将对应的月令: 亥将→正月, 戌将→二月, ..., 子将→十二月
    # 月将顺序: 亥戌酉申未午巳辰卯寅丑子
    yj_order = ['亥','戌','酉','申','未','午','巳','辰','卯','寅','丑','子']
    yue_ling_idx = yj_order.index(yj) if yj in yj_order else -1
    if yue_ling_idx == -1:
        return ''
    # 生气: 正月子, 二月丑, ..., 十二月亥
    sheng_qi_idx = yue_ling_idx  # 正月→子(0), 二月→丑(1)
    return DIZHI_ORDER[sheng_qi_idx]


# 月令死气: 与生气相冲
def _get_si_qi(yuejiang: str) -> str:
    """获取月令死气方位"""
    sq = _get_sheng_qi(yuejiang)
    return LIUCHONG.get(sq, '')


# ============ 地支辅助 ============
YANG_ZHI = {'子', '寅', '辰', '午', '申', '戌'}
YIN_ZHI = {'丑', '卯', '巳', '未', '酉', '亥'}

def _is_yang_zhi(z: str) -> bool:
    """判断是否为阳支"""
    return z in YANG_ZHI

def _is_yin_zhi(z: str) -> bool:
    """判断是否为阴支"""
    return z in YIN_ZHI


def _extract_sike_shang(si_ke_info) -> List[str]:
    """从四课信息提取上神地支列表（兼容 4-元组[(课名,上神,下神,天将),...] 与 字符串列表）。"""
    shang = []
    if not si_ke_info:
        return shang
    for ke in si_ke_info:
        if isinstance(ke, (list, tuple)) and len(ke) >= 2:
            z = ke[1]
        elif isinstance(ke, str):
            z = ke
        else:
            z = ''
        if z and z in ZHI_WUXING:
            shang.append(z)
    return shang

def _get_next_zhi(z: str) -> str:
    """获取下一个地支（顺行一位）"""
    idx = DIZHI_INDEX.get(z, -1)
    return DIZHI_ORDER[(idx + 1) % 12] if idx >= 0 else ''

def _get_prev_zhi(z: str) -> str:
    """获取上一个地支（逆行一位）"""
    idx = DIZHI_INDEX.get(z, -1)
    return DIZHI_ORDER[(idx - 1) % 12] if idx >= 0 else ''

def _is_zhi_before(a: str, b: str) -> bool:
    """判断a是否在b的顺行方向（从b到a的距离<=6）"""
    if a not in DIZHI_INDEX or b not in DIZHI_INDEX:
        return False
    dist = (DIZHI_INDEX[a] - DIZHI_INDEX[b]) % 12
    return 1 <= dist <= 6

def _is_zhi_after(a: str, b: str) -> bool:
    """判断a是否在b的逆行方向（从b到a的逆行距离<=6）"""
    if a not in DIZHI_INDEX or b not in DIZHI_INDEX:
        return False
    dist = (DIZHI_INDEX[b] - DIZHI_INDEX[a]) % 12
    return 1 <= dist <= 6


def _is_zhi_wang(z: str, season: str = '') -> bool:
    """判断地支是否当令旺相（地支五行与季节旺五行一致）"""
    if not z or ZHI_WANG.get(z) != z:
        return False
    if season:
        wx = ZHI_WUXING.get(z)
        season_wx = SEASON_WANG.get(season)
        if wx and season_wx:
            return wx == season_wx
    return True


# ============ 核心检测�� ============
class BiFaDetector:
    """毕法赋100法检测引擎"""
    
    def __init__(self):
        self.kb = _load_kb()
        self.detected_rules = []
        
    def detect(self,
               sanchuan_dizhi: List[str],
               ri_gan: str = '',
               ri_zhi: str = '',
               ganzhi: str = '',
               yuejiang: str = '',
               season: str = '',
               gan_shang_shen: str = '',
               zhi_shang_shen: str = '',
               si_ke_info: Optional[List[str]] = None,
               tian_jiang: Optional[Dict] = None,
               tiandi_pan: Optional[Dict] = None,
               keti: str = '',
               tai_sui: str = '',
               ben_ming_zhi: str = '',
               shichen: str = '',
               ) -> Dict:
        """
        检测适用的毕法赋法条
        
        参数:
        - sanchuan_dizhi: 三传地支列表 (3个)
        - ri_gan: 日干 (如 '甲')
        - ri_zhi: 日支 (如 '子')
        - ganzhi: 完整干支 (如 '甲子')
        - yuejiang: 月将 (如 '午将')
        - season: 季节 (如 '春', 若未传入则从月将推断)
        - gan_shang_shen: 干上神 (如有)
        - zhi_shang_shen: 支上神 (如有)
        - si_ke_info: 四课信息 (如有)
        - tian_jiang: 天将信息 (如有)
        - tiandi_pan: 天地盘 (地盘支→天盘支映射，用于夹克检测)
        
        返回:
        {
            '匹配法条': [...],
            '法条详情': {...},
            '股市信号': {'综合倾向': '涨'/'跌'/'震荡'/'平', '信号强度': float, '操作建议': str},
            '检测统计': {...}
        }
        """
        self.detected_rules = []

        # 【BUG-FIX 2026-08-18】空/非法输入兜底：缺日干日支或三传不足 3 个地支时
        # 毕法无法判定，直接返回空结果（原空盘会误命中多条规则，如 build_keti_duanyu({}) 误判为凶）。
        _valid_sc = [z for z in (sanchuan_dizhi or []) if z in DIZHI_ORDER]
        if not ri_gan or not ri_zhi or len(_valid_sc) < 3:
            return {
                '匹配法条': [],
                '法条详情': {},
                '股市信号': {'综合倾向': '平', '信号强度': 0.0, '操作建议': '', '各信号权重': {}},
                '检测统计': {'检测法条数': 0, '涨法条数': 0, '跌法条数': 0, '震荡法条数': 0},
            }

        if not season:
            season = _get_yue_ling_season(yuejiang)
        
        # 昼夜（昼时：卯辰巳午未申；夜时：酉戌亥子丑寅）
        is_day = shichen in ('卯', '辰', '巳', '午', '未', '申') if shichen else True
        
        # 获取旬空
        kongwang = get_xun_kong(ganzhi) if ganzhi else ('', '')
        
        # 三传走势
        trend = _get_sanchuan_trend(sanchuan_dizhi)
        
        # 数据化简单法规则匹配（第16/82/12 法及后续简单法已迁 data/bifa_rules.json，2026-08-16 ①批次）
        try:
            _data_env = {
                'ri_gan': ri_gan, 'ri_zhi': ri_zhi,
                'gan_shang': gan_shang_shen, 'zhi_shang': zhi_shang_shen,
                'sanchuan': sanchuan_dizhi, 'kongwang': tuple(kongwang),
                'lu': LU_SHEN.get(ri_gan, ''),
                'yima': YIMA.get(ri_zhi, ''),
                'season': season,
                'tian_jiang': tian_jiang or {},
                'tiandi_pan': tiandi_pan or {},
                'tai_sui': tai_sui or '',
            }
            self._match_data_rules(_data_env)
        except Exception:
            pass
        
        # 1. 三传递生 (第31法)
        self._check_rule_31(sanchuan_dizhi, ri_gan)
        
        # 2. 三传互克 (第32法)
        self._check_rule_32(sanchuan_dizhi, ri_gan)
        
        # 3. 进茹空亡 (第17法)
        self._check_rule_17(trend, sanchuan_dizhi, kongwang, ganzhi)
        
        # 4. 踏脚空亡 (第18法)
        self._check_rule_18(trend, sanchuan_dizhi, kongwang, ganzhi)
        
        # 5. 传财太旺 (第14法)
        self._check_rule_14(sanchuan_dizhi, ri_gan)
        
        # 6. 传财化鬼 (第27法)
        # self._check_rule_27(sanchuan_dizhi, ri_gan, gan_shang_shen)  # 已迁 data/bifa_rules.json
        
        # 7. 传鬼化财 (第28法)
        self._check_rule_28(sanchuan_dizhi, ri_gan, gan_shang_shen)
        
        # 8. 眷属丰盈/屋宅宽广 (第29/30法)
        self._check_rule_29_30(sanchuan_dizhi, ri_gan, ri_zhi)
        
        # 9. 有始无终/难变易 (第33法)
        self._check_rule_33(sanchuan_dizhi, ri_gan)
        
        # 10. 传墓入墓 (第81法)
        self._check_rule_81(sanchuan_dizhi, ri_gan)
        
        # 11. 不行传者 (第82法) —— 已迁 data/bifa_rules.json
        # self._check_rule_82(sanchuan_dizhi, kongwang)
        
        # 12. 三六合 (第83/84法)
        self._check_rule_83_84(sanchuan_dizhi, ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        
        # 13. 胎财生气/死气 (第19/20法)
        self._check_rule_19_20(ri_gan, yuejiang)
        
        # 14. 金日逢丁/水日逢丁 (第25/26法)
        self._check_rule_25_26(ri_gan, ganzhi, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, ben_ming_zhi)
        
        # 15. 干支皆败 (第36法) —— 已迁 data/bifa_rules.json（沐浴位）
        # self._check_rule_36(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        
        # 16. 干支值绝 (第79法) —— 已迁 data/bifa_rules.json（十二长生绝位）
        # self._check_rule_79(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        
        # 17. 人宅受脱 (第35法) —— 已迁 data/bifa_rules.json（干生干上脱人、支生支上脱宅）
        # self._check_rule_35(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        
        # 18. 空上乘空 (第16法) —— 已迁 data/bifa_rules.json
        # self._check_rule_16(gan_shang_shen, kongwang)
        
        # 19. 互生俱生 (第77法)
        self._check_rule_77(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        
        # 20. 任信丁马/来去俱空 (第89/90法)
        self._check_rule_89_90(trend, sanchuan_dizhi, kongwang, ganzhi, gan_shang_shen, zhi_shang_shen)
        
        # 21. 干支乘墓 (第88法)
        # self._check_rule_88(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        
        # === Batch1: 第1-80法补充 ===
        # 22. 前后引从 (第1法)
        self._check_rule_1(sanchuan_dizhi, ri_gan, ri_zhi)
        # 23. 首尾相见 (第2法)
        self._check_rule_2(ri_gan, ri_zhi, ganzhi, gan_shang_shen, zhi_shang_shen)
        # 24. 六阳数足 (第5法)
        self._check_rule_5(sanchuan_dizhi, ri_gan, ri_zhi, si_ke_info)
        # 25. 六阴相继 (第6法)
        self._check_rule_6(sanchuan_dizhi, ri_gan, ri_zhi, si_ke_info)
        # 26. 旺禄临身 (第7法)
        # self._check_rule_7(ri_gan, gan_shang_shen)  # 已迁 data/bifa_rules.json
        # 27. 权摄不正 (第8法)
        # self._check_rule_8(ri_gan, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        # 28. 众鬼虽彰 (第11法)
        self._check_rule_11(sanchuan_dizhi, ri_gan, gan_shang_shen)
        # 29. 狐假虎威 (第12法) —— 已迁 data/bifa_rules.json
        # self._check_rule_12(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        # 30. 鬼贼当时 (第13法)
        self._check_rule_13(sanchuan_dizhi, ri_gan, season)
        # 31. 脱上逢脱 (第15法)
        self._check_rule_15(ri_gan, gan_shang_shen, tian_jiang)
        # 32. 交车相合 (第21法)
        # self._check_rule_21(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        # 33. 上下皆合 (第22法)
        # self._check_rule_22(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        # 34. 逢罗网 (第55法)
        self._check_rule_55(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)
        # 35. 空空如也 (第74法)
        self._check_rule_74(sanchuan_dizhi, kongwang, ganzhi)
        # 36. 宾主不投刑 (第75法)
        self._check_rule_75(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, sanchuan_dizhi)
        # 37. 彼此猜忌害 (第76法)
        self._check_rule_76(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, sanchuan_dizhi)
        # 38. 互旺皆旺 (第78法)
        # self._check_rule_78(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, season)  # 已迁 data/bifa_rules.json
        # 39. 人宅皆死 (第80法)
        self._check_rule_80(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, yuejiang)
        
        # === Batch2: 第51-73法 ===
        # 51. 魁度天门关隔定
        # self._check_rule_51(sanchuan_dizhi, ri_gan, tiandi_pan)  # 已迁 data/bifa_rules.json
        
        # 52. 罡塞鬼户任谋为
        # self._check_rule_52(sanchuan_dizhi, ri_gan, tiandi_pan)  # 已迁 data/bifa_rules.json
        
        # 53. 两蛇夹墓凶难免
        self._check_rule_53(ri_gan, gan_shang_shen, zhi_shang_shen, tian_jiang)
        
        # 57. 费有余而得不足
        self._check_rule_57(sanchuan_dizhi, ri_gan, kongwang)
        
        # 58. 用破身心无所归
        self._check_rule_58(sanchuan_dizhi, ri_gan, kongwang)
        
        # 59. 华盖覆日人昏晦
        # self._check_rule_59(ri_gan, gan_shang_shen)  # 已迁 data/bifa_rules.json
        
        # 60. 太阳射宅屋光辉
        self._check_rule_60(ri_zhi, zhi_shang_shen, yuejiang)
        
        # 63. 彼此全伤防两损
        # self._check_rule_63(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        
        # 64. 夫妇芜淫各有私
        # self._check_rule_64(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        
        # 65. 干墓并关人宅废
        self._check_rule_65(sanchuan_dizhi, ri_gan, ri_zhi, season, gan_shang_shen, zhi_shang_shen)
        
        # 66. 支坟财并旅程稽
        self._check_rule_66(sanchuan_dizhi, ri_gan, ri_zhi)
        
        # 73. 前后逼迫难进退
        # self._check_rule_73(sanchuan_dizhi, ri_gan)  # 已迁 data/bifa_rules.json

        # === Batch3: 虎龙病讼凶灾系列 ===
        # 54. 虎视逢虎力难施
        self._check_rule_54(ri_gan, tian_jiang, keti)
        # 56. 天网自裹己招非
        self._check_rule_56(ri_gan, gan_shang_shen, ben_ming_zhi)
        # 61. 干乘墓虎无占病
        self._check_rule_61(ri_gan, gan_shang_shen, tian_jiang, ben_ming_zhi, is_day)
        # 62. 支乘墓虎有伏尸
        self._check_rule_62(ri_gan, ri_zhi, zhi_shang_shen, tian_jiang)
        # 67. 受虎克神为病症
        self._check_rule_67(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)
        # 68. 制鬼之位乃良医
        self._check_rule_68(sanchuan_dizhi, ri_gan, gan_shang_shen)
        # 69. 虎乘遁鬼殃非浅
        self._check_rule_69(ri_gan, ganzhi, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)
        # 70. 鬼临三四讼灾随
        self._check_rule_70(ri_gan, si_ke_info)
        # 71. 病符克宅全家患
        # self._check_rule_71(ri_zhi, zhi_shang_shen, tai_sui)  # 已迁 data/bifa_rules.json
        # 72. 丧吊全逢挂缟衣
        self._check_rule_72(gan_shang_shen, zhi_shang_shen, tai_sui)
        # 91. 虎临干鬼凶速速
        self._check_rule_91(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)
        # 92. 龙加生气吉迟迟
        self._check_rule_92(ri_gan, yuejiang, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)

        # === Batch3: 第9-100法补充 ===
        # 9. 避难逃生须弃旧
        self._check_rule_9(sanchuan_dizhi, ri_gan, gan_shang_shen)
        # 10. 朽木难雕别作为
        self._check_rule_10(sanchuan_dizhi, ganzhi, kongwang, si_ke_info, tiandi_pan)
        # 23. 彼求我事支传干
        self._check_rule_23(sanchuan_dizhi, ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, si_ke_info)
        # 24. 我求彼事干传支
        # self._check_rule_24(sanchuan_dizhi, ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        # 34. 苦去甘来乐里悲
        self._check_rule_34(sanchuan_dizhi, ri_gan)
        # 37. 末助初兮三等论
        self._check_rule_37(sanchuan_dizhi, ri_gan)
        # 38. 闭口卦体两般推
        self._check_rule_38(sanchuan_dizhi, ganzhi, tian_jiang, tiandi_pan)
        # 93. 妄用三传灾福异
        self._check_rule_93(sanchuan_dizhi, ri_gan)
        # 94. 喜惧空亡乃妙机
        self._check_rule_94(sanchuan_dizhi, ri_gan, kongwang)
        # 95. 六爻现卦防其克
        self._check_rule_95(sanchuan_dizhi, ri_gan)
        # 96. 旬内空亡逐类推
        self._check_rule_96(sanchuan_dizhi, ri_gan, ganzhi, kongwang)
        # 97. 所筮不入仍凭类
        self._check_rule_97(sanchuan_dizhi, ri_gan)
        # 98. 非占现类勿言之 —— 已停用（2026-08-15 憨爷拍板：这句断课方法论提醒以后一律不用）
        # self._check_rule_98()
        # 99. 常问不应逢吉象
        self._check_rule_99(ri_gan, season)
        # 100. 已灾凶逃返无疑
        self._check_rule_100(sanchuan_dizhi, ri_gan)

        # === Batch4: 贵人天将系列 ===
        # 3. 帘幕贵人高甲第（昼占夜贵、夜占昼贵为帘幕）
        self._check_rule_3(ri_gan, gan_shang_shen, is_day)
        # 4. 催官使者赴官期（日鬼乘白虎加干）
        # self._check_rule_4(ri_gan, gan_shang_shen, tian_jiang)  # 已迁 data/bifa_rules.json
        # 39. 太阳照武宜擒贼（月将临玄武上）
        self._check_rule_39(yuejiang, tian_jiang)
        # 40. 后合占婚岂用媒
        # self._check_rule_40(gan_shang_shen, zhi_shang_shen, tian_jiang)  # 已迁 data/bifa_rules.json
        # 41. 富贵干支逢禄马
        # self._check_rule_41(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen)  # 已迁 data/bifa_rules.json
        # 42. 尊崇传内遇三奇
        self._check_rule_42(sanchuan_dizhi, ganzhi)
        # 43. 害贵讼直作曲断
        self._check_rule_43(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)
        # 44. 课传俱贵转无依
        self._check_rule_44(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, si_ke_info)
        # 45. 昼夜贵加求两贵
        self._check_rule_45(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, si_ke_info)
        # 46. 贵人差迭事参差
        self._check_rule_46(ri_gan, ri_zhi, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen)
        # 47. 贵虽在狱宜临干
        self._check_rule_47(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang, ri_zhi, tiandi_pan)
        # 48. 鬼乘天乙乃神祗
        # self._check_rule_48(ri_gan, gan_shang_shen, tian_jiang)  # 已迁 data/bifa_rules.json
        # 49. 两贵受克难干贵
        self._check_rule_49(ri_gan, ri_zhi, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen)
        # 50. 二贵皆空虚喜期
        self._check_rule_50(ri_gan, sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, kongwang)
        # 85. 初遭夹克不由己
        self._check_rule_85(sanchuan_dizhi, tian_jiang, tiandi_pan)
        # 86. 将逢内战所谋危
        self._check_rule_86(sanchuan_dizhi, gan_shang_shen, zhi_shang_shen, tian_jiang)
        # 87. 人宅坐墓甘招晦
        self._check_rule_87(ri_gan, ri_zhi, gan_shang_shen, zhi_shang_shen, tiandi_pan)
        
        # 【BUG-FIX 2026-08-18】删除原"独立收尾"5 条重复调用：
        # 第20/26/30/84/90 法逻辑已由组合方法 _check_rule_19_20 / _check_rule_25_26 /
        # _check_rule_29_30 / _check_rule_83_84 / _check_rule_89_90 完整覆盖；
        # 原独立版第30法判据(any 生支)与组合版(all 生支)矛盾，双调会行为不一致。

        # 构建结果
        return self._build_result()
    
    def _add_rule(self, rule_id: int, detail: str = '',
                  signal_override: str = '', conf_override: str = ''):
        """添加检测到的法条"""
        if rule_id not in [r['id'] for r in self.detected_rules]:
            rule_info = None
            for r in self.kb['rules']:
                if r['id'] == rule_id:
                    rule_info = r
                    break
            if rule_info:
                self.detected_rules.append({
                    'id': rule_id,
                    'name': rule_info['name'],
                    'rule': rule_info['core_rule'],
                    'detail': detail,
                    'stock_signal': signal_override or rule_info.get('stock_signal', '平'),
                    'confidence': conf_override or rule_info.get('confidence', 'low'),
                })
    
    def _match_data_rules(self, env: Dict):
        """匹配 data/bifa_rules.json（数据化的简单法），命中的 _add_rule。
        与变格引擎同源（kege_atoms 谓词 + DNF 规则表）；复杂法仍保留 _check_rule_N 代码。"""
        try:
            import os
            import json as _json
            from engine.kege_bianjie_engine import match_rule
            _p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'data', 'bifa_rules.json')
            _rules = _json.load(open(_p, encoding='utf-8')).get('rules', [])
            for r in _rules:
                if match_rule(r, env):
                    self._add_rule(r['id'], r.get('detail', ''))
        except Exception:
            pass

    def _build_result(self) -> Dict:
        """构建检测结果"""
        if not self.detected_rules:
            return {
                '匹配法条': [],
                '法条详情': {},
                '股市信号': {'综合倾向': '平', '信号强度': 0.0, '操作建议': '无毕法赋信号'},
                '检测统计': {'检测法条数': 0},
            }
        
        # 汇总股市信号
        signal_scores = {'涨': 0, '跌': 0, '震荡': 0}
        confidence_weights = {'high': 3, 'medium': 2, 'low': 1}
        total_weight = 0
        
        for rule in self.detected_rules:
            sig = rule.get('stock_signal', '平')
            conf = rule.get('confidence', 'low')
            w = confidence_weights.get(conf, 1)
            if sig in signal_scores:
                signal_scores[sig] += w
            total_weight += w
        
        # 判断综合倾向
        if total_weight > 0:
            max_sig = max(signal_scores, key=signal_scores.get)
            max_score = signal_scores[max_sig]
            if max_score > signal_scores.get('涨', 0) + signal_scores.get('跌', 0) - max_score:
                tendency = max_sig
            else:
                tendency = '震荡'
            strength = min(max_score / total_weight, 1.0)
        else:
            tendency = '平'
            strength = 0.0
        
        # 生成建议
        advice = self._generate_advice(tendency, strength)
        
        return {
            '匹配法条': [r['name'] for r in self.detected_rules],
            '法条详情': {
                r['name']: {
                    'id': r['id'],
                    '规则': r['rule'],
                    '详情': r['detail'],
                    '股市信号': r['stock_signal'],
                    '置信度': r['confidence'],
                }
                for r in self.detected_rules
            },
            '股市信号': {
                '综合倾向': tendency,
                '信号强度': round(strength, 2),
                '操作建议': advice,
                '各信号权重': signal_scores,
            },
            '检测统计': {
                '检测法条数': len(self.detected_rules),
                '涨法条数': sum(1 for r in self.detected_rules if r['stock_signal'] == '涨'),
                '跌法条数': sum(1 for r in self.detected_rules if r['stock_signal'] == '跌'),
                '震荡法条数': sum(1 for r in self.detected_rules if r['stock_signal'] == '震荡'),
            },
        }
    
    def _generate_advice(self, tendency: str, strength: float) -> str:
        """生成操作建议"""
        if tendency == '涨' and strength > 0.5:
            return '毕法赋多法条共振看涨，可考虑建仓'
        elif tendency == '跌' and strength > 0.5:
            return '毕法赋多法条共振看跌，建议回避或减仓'
        elif tendency == '震荡':
            return '毕法赋涨跌信号均衡，建议观望'
        else:
            return '毕法赋信号偏弱，参考价值有限'
    
    # ================== 各法条检测方法 ==================
    
    def _check_rule_31(self, sanchuan: List[str], ri_gan: str):
        """第31法: 三传递生人举荐
        初生中，中生末，末生日干；或末生中，中生初，初生日干
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        
        # 模式A: 初→中→末→干
        if _zhi_sheng_zhi(sanchuan[0], sanchuan[1]) and \
           _zhi_sheng_zhi(sanchuan[1], sanchuan[2]) and \
           _is_gan_parent(ri_gan, sanchuan[2]):
            self._add_rule(31, f'初{sanchuan[0]}生中{sanchuan[1]}生末{sanchuan[2]}生日干{ri_gan}')
            return
        
        # 模式B: 末→中→初→干
        if _zhi_sheng_zhi(sanchuan[2], sanchuan[1]) and \
           _zhi_sheng_zhi(sanchuan[1], sanchuan[0]) and \
           _is_gan_parent(ri_gan, sanchuan[0]):
            self._add_rule(31, f'末{sanchuan[2]}生中{sanchuan[1]}生初{sanchuan[0]}生日干{ri_gan}')
    
    def _check_rule_32(self, sanchuan: List[str], ri_gan: str):
        """第32法: 三传互克众人欺
        初克中，中克末，末克日干；或末克中，中克初，初克日干
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        
        # 模式A: 初克中克末克干
        if _zhi_ke_zhi(sanchuan[0], sanchuan[1]) and \
           _zhi_ke_zhi(sanchuan[1], sanchuan[2]) and \
           _is_gan_ghost(ri_gan, sanchuan[2]):
            self._add_rule(32, f'初{sanchuan[0]}克中{sanchuan[1]}克末{sanchuan[2]}克干{ri_gan}')
            return
        
        # 模式B: 末克中克初克干
        if _zhi_ke_zhi(sanchuan[2], sanchuan[1]) and \
           _zhi_ke_zhi(sanchuan[1], sanchuan[0]) and \
           _is_gan_ghost(ri_gan, sanchuan[0]):
            self._add_rule(32, f'末{sanchuan[2]}克中{sanchuan[1]}克初{sanchuan[0]}克干{ri_gan}')
    
    def _check_rule_17(self, trend: str, sanchuan: List[str], kongwang: Tuple[str, str], ganzhi: str = ''):
        """第17法: 进茹空亡宜退步
        进连茹三传皆落空亡（初传、中传本旬空，末传前旬空），宜退步（通解中L4707"壬子日三传寅卯辰皆空"）。
        """
        if trend != '进连茹' or len(sanchuan) != 3:
            return
        fxk = get_fen_xun_kong(ganzhi) if ganzhi else None
        if not fxk:
            return
        ben, qian = fxk['本旬'], fxk['前旬']
        if sanchuan[0] in ben and sanchuan[1] in ben and sanchuan[2] in qian:
            self._add_rule(17, f'进连茹{sanchuan}皆落空亡（初{sanchuan[0]}中{sanchuan[1]}本旬空、末{sanchuan[2]}前旬空），宜退步')

    def _check_rule_18(self, trend: str, sanchuan: List[str], kongwang: Tuple[str, str], ganzhi: str = ''):
        """第18法: 踏脚空亡进用宜
        退步传（退连茹或逆间传）三传皆落空亡（初传本旬空、中传后旬空、末传外后旬空），宜进（通解中L4746/4779"甲子日戌申午"）。
        """
        if trend not in ('退连茹', '逆间传') or len(sanchuan) != 3:
            return
        fxk = get_fen_xun_kong(ganzhi) if ganzhi else None
        if not fxk:
            return
        ben, hou, waihou = fxk['本旬'], fxk['后旬'], fxk['外后旬']
        if sanchuan[0] in ben and sanchuan[1] in hou and sanchuan[2] in waihou:
            self._add_rule(18, f'退步传{sanchuan}皆落空亡（初{sanchuan[0]}本旬空、中{sanchuan[1]}后旬空、末{sanchuan[2]}外后旬空），宜进')
    
    def _check_rule_14(self, sanchuan: List[str], ri_gan: str):
        """第14法: 传财太旺反财亏"""
        if len(sanchuan) != 3 or not ri_gan:
            return
        if all(_is_gan_wealth(ri_gan, z) for z in sanchuan):
            self._add_rule(14, f'三传{sanchuan}皆日干{ri_gan}之财，财太旺反亏')
    
    def _check_rule_27(self, sanchuan: List[str], ri_gan: str, gan_shang: str):
        """第27法: 传财化鬼财休觅
        初传为日干财爻，末传为官鬼，传财化鬼，取财致祸
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu = sanchuan[0]
        mo = sanchuan[2]
        if _is_gan_wealth(ri_gan, chu) and _is_gan_ghost(ri_gan, mo):
            # 初传为财，末传为鬼 → 传财化鬼
            self._add_rule(27, f'初传{chu}(财)化末传{mo}(鬼)，传财化鬼财休觅',
                           signal_override='跌', conf_override='high')
    
    def _check_rule_28(self, sanchuan: List[str], ri_gan: str, gan_shang: str):
        """第28法: 传鬼化财钱险危
        三传皆鬼，干上有制鬼之神，存财
        """
        if len(sanchuan) != 3 or not ri_gan or not gan_shang:
            return
        if all(_is_gan_ghost(ri_gan, z) for z in sanchuan):
            if _zhi_ke_zhi(gan_shang, sanchuan[0]) or _zhi_ke_zhi(gan_shang, sanchuan[1]):
                self._add_rule(28, f'三传鬼{sanchuan}，干上{gan_shang}制鬼存财，险中求财')
    
    def _check_rule_29_30(self, sanchuan: List[str], ri_gan: str, ri_zhi: str):
        """第29法: 眷属丰盈居狭宅 — 三传生干脱支
           第30法: 屋宅宽广致人衰 — 三传脱干生支
        """
        if len(sanchuan) != 3 or not ri_gan or not ri_zhi:
            return
        
        # 29: 三传皆生干且皆脱支
        if all(_is_gan_parent(ri_gan, z) for z in sanchuan) and all(_zhi_sheng_zhi(ri_zhi, z) for z in sanchuan):
            self._add_rule(29, f'三传{sanchuan}生日干{ri_gan}脱支辰{ri_zhi}，人口丰盈居宅窄')
            return
        
        # 30: 三传皆脱干且皆生支
        if all(_is_gan_child(ri_gan, z) for z in sanchuan) and all(_zhi_sheng_zhi(z, ri_zhi) for z in sanchuan):
            self._add_rule(30, f'三传{sanchuan}脱日干{ri_gan}生支辰{ri_zhi}，屋宅宽广致人衰')
    
    def _check_rule_33(self, sanchuan: List[str], ri_gan: str):
        """第33法: 有始无终难变易
        初传长生末传墓=有始无终；初传墓末传长生=先难后易
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        
        cs = _gan_wx_changsheng(ri_gan)   # 日干五行长生位（土双位 tuple）
        mu_zhi = MU.get(ri_gan, '')
        
        if cs and mu_zhi:
            if sanchuan[0] in cs and sanchuan[2] == mu_zhi:
                self._add_rule(33, f'初传{sanchuan[0]}长生，末传{mu_zhi}墓，有始无终')
            elif sanchuan[0] == mu_zhi and sanchuan[2] in cs:
                self._add_rule(33, f'初传{mu_zhi}墓，末传{sanchuan[2]}长生，先难后易（难变易）')
    
    def _check_rule_81(self, sanchuan: List[str], ri_gan: str):
        """第81法: 传墓入墓分憎爱
        初传为长生/财/禄/官（吉神）→ 传入墓位 = 凶（憎）
        初传为鬼/盗气（凶神）→ 传入墓位 = 吉（爱）
        【BUG-FIX 2026-08-18 案例实证】"据《毕法赋》传墓入墓分憎爱诀下
        生我者传墓入墓之议，亦不利也"——生我者(父母印星)传墓入墓不利。
        原"中传克初传且中传=墓"双条件过苛（墓支通常不克初传）→ 传墓入墓
        几乎不触发；改为直接判 中传或末传为日墓（传墓/入墓），初传为吉神
        （父母/财/官/禄/长生）则凶，鬼/盗气入墓为吉（爱，不报）。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        
        chu = sanchuan[0]
        zhong = sanchuan[1]
        mo = sanchuan[2]
        mu_zhi = MU.get(ri_gan, '')

        def _is_ji_shen(z):
            """吉神：生我者(父母印)/财(我克)/禄/长生。
            【BUG-FIX 2026-08-18】不含 克我者(鬼/官)：毕法"日鬼盗气却喜中末墓"——
            鬼入墓为吉（爱），非吉神。"""
            return (_is_gan_parent(ri_gan, z) or _is_gan_wealth(ri_gan, z)
                    or z == LU_SHEN.get(ri_gan)
                    or z in _gan_wx_changsheng(ri_gan))

        if not mu_zhi:
            return
        # 传墓（中传为日墓）或 入墓（末传为日墓）
        if zhong == mu_zhi or mo == mu_zhi:
            if _is_ji_shen(chu):
                self._add_rule(81, f'初传{chu}(吉神)传入墓{mu_zhi}，传墓入墓，不利')
            # 鬼/盗气入墓为吉（爱），不报凶
    
    def _check_rule_82(self, sanchuan: List[str], kongwang: Tuple[str, str]):
        """第82法: 不行传者考初时 — 中末空亡"""
        if len(sanchuan) != 3:
            return
        if kongwang and kongwang[0]:
            zhong_kong = sanchuan[1] in kongwang
            mo_kong = sanchuan[2] in kongwang
            if zhong_kong and mo_kong:
                self._add_rule(82, f'中传{sanchuan[1]}末传{sanchuan[2]}皆空，考初传{sanchuan[0]}')
    
    def _check_rule_83_84(self, sanchuan: List[str], ri_gan: str, ri_zhi: str,
                          gan_shang: str = '', zhi_shang: str = ''):
        """第83法: 万事喜忻三六合 / 第84法: 合中犯杀蜜中砒"""
        if len(sanchuan) != 3:
            return
        
        he_ju = _is_sanhe_ju(sanchuan)
        if not he_ju:
            return
        
        # 83法: 三六合
        self._add_rule(83, f'三传{sanchuan}成{he_ju}局三合')
        
        # 84法: 合中犯杀 — 三合局 + 干支上神见刑/害/冲
        if gan_shang or zhi_shang:
            sha_info = SANHE_SHANG.get(he_ju, {})
            xing = sha_info.get('刑', '')
            hai = sha_info.get('害', '')
            chong = sha_info.get('冲', '')
            
            violations = []
            for label, s in [('干上', gan_shang), ('支上', zhi_shang)]:
                if not s:
                    continue
                if s == xing:
                    violations.append(f'{label}{s}为自刑')
                # 【BUG-FIX 2026-08-18】原 `s == hai and LIUHAI.get(s) == xing`
                # 把"六害"与"刑"混为一谈：害位判断应为 s == hai（局中神之害位）。
                if s == hai:
                    violations.append(f'{label}{s}为六害')
                if s == chong:
                    violations.append(f'{label}{s}为冲')
            
            if violations:
                self._add_rule(84, f'三传{sanchuan}为{he_ju}局，{"、".join(violations)}，合中犯杀蜜中砒')
    
    def _check_rule_19_20(self, ri_gan: str, yuejiang: str):
        """第19法: 胎财生气妻怀孕 / 第20法: 胎财死气损胎推"""
        if not ri_gan or not yuejiang:
            return
        
        tai = _gan_wx_tai(ri_gan)   # 日干五行胎位（土双位 tuple）
        if not tai:
            return
        sheng_qi = _get_sheng_qi(yuejiang)
        si_qi = _get_si_qi(yuejiang)
        
        if sheng_qi and sheng_qi in tai:
            self._add_rule(19, f'日干{ri_gan}胎神{sheng_qi}为月令生气，胎财生气')
        elif si_qi and si_qi in tai:
            self._add_rule(20, f'日干{ri_gan}胎神{si_qi}为月令死气，胎财死气')
    
    def _check_rule_25_26(self, ri_gan: str, ganzhi: str, sanchuan: List[str] = None, gan_shang: str = '', zhi_shang: str = '', ben_ming_zhi: str = ''):
        """第25法: 金日逢丁凶祸动 / 第26法: 水日逢丁财动之
        庚辛日逢旬内丁神主凶动；壬癸日逢丁神主财动（六处：三传+干上+支上+本命，通解"三传年命日辰逢丁神"）。
        """
        if not ri_gan or not ganzhi:
            return
        ding_shen = get_ding_shen(ganzhi)
        if not ding_shen:
            return

        # 检查六处（三传、干上、支上、本命）是否有丁神
        positions = []
        if sanchuan:
            for i, z in enumerate(sanchuan):
                if z == ding_shen:
                    positions.append(['初传', '中传', '末传'][i])
        if gan_shang and gan_shang == ding_shen:
            positions.append('干上')
        if zhi_shang and zhi_shang == ding_shen:
            positions.append('支上')
        if ben_ming_zhi and ben_ming_zhi == ding_shen:
            positions.append('本命')

        if not positions:
            return

        pos_str = '、'.join(positions)

        # 第25法: 金日逢丁 (庚辛日)
        if ri_gan in ('庚', '辛'):
            self._add_rule(25, f'金日{ri_gan}逢丁神{ding_shen}在{pos_str}，凶祸动')
        # 第26法: 水日逢丁 (壬癸日)
        elif ri_gan in ('壬', '癸'):
            self._add_rule(26, f'水日{ri_gan}逢丁神{ding_shen}在{pos_str}，财动之')
    
    def _check_rule_36(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第36法: 干支皆败事倾颓"""
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_bai = BAI.get(ri_gan, '')
        zhi_bai = BAI.get(ri_zhi, '')
        if gan_bai and zhi_bai and gan_shang == gan_bai and zhi_shang == zhi_bai:
            self._add_rule(36, f'干上{gan_shang}为干败气，支上{zhi_shang}为支败气，干支皆败')
    
    def _check_rule_79(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第79法: 干支值绝凡谋决"""
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_jue = JUE.get(ri_gan, '')
        zhi_jue = JUE.get(ri_zhi, '')
        if gan_jue and zhi_jue and gan_shang == gan_jue and zhi_shang == zhi_jue:
            self._add_rule(79, f'干上{gan_shang}为干绝，支上{zhi_shang}为支绝，宜结绝凶事')
    
    def _check_rule_35(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第35法: 人宅受脱俱招盗"""
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_tuo = _is_gan_child(ri_gan, gan_shang)  # 干上脱干
        zhi_tuo = _is_gan_child(ri_zhi, zhi_shang)  # 支上脱支
        if gan_tuo and zhi_tuo:
            self._add_rule(35, f'干上{gan_shang}脱干，支上{zhi_shang}脱支，人宅受脱')
    
    def _check_rule_16(self, gan_shang: str, kongwang: Tuple[str, str]):
        """第16法: 空上乘空事莫追"""
        if not gan_shang or not kongwang or not kongwang[0]:
            return
        if gan_shang in kongwang:
            self._add_rule(16, f'干上{gan_shang}为旬空，空上乘空')
    
    def _check_rule_77(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第77法: 互生俱生凡事益"""
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        
        # 互生：干上生支，支上生干
        gan2zhi = _zhi_sheng_zhi(gan_shang, ri_zhi)
        zhi2gan = _zhi_sheng_zhi(zhi_shang, ri_gan)
        
        if gan2zhi and zhi2gan:
            self._add_rule(77, f'干上{gan_shang}生支{ri_zhi}，支上{zhi_shang}生干{ri_gan}，互生有益')
            return
        
        # 俱生：干上生干，支上生支
        gan_sheng_self = _zhi_sheng_zhi(gan_shang, ri_gan) if ri_gan and GAN_WUXING.get(ri_gan) else False
        zhi_sheng_self = _zhi_sheng_zhi(zhi_shang, ri_zhi) if ri_zhi and ZHI_WUXING.get(ri_zhi) else False
        if gan_sheng_self and zhi_sheng_self:
            self._add_rule(77, f'干上{gan_shang}生干，支上{zhi_shang}生支，俱生有益')
    
    def _check_rule_89_90(self, trend: str, sanchuan: List[str] = None, kongwang: Tuple[str, str] = ('', ''), ganzhi: str = '', gan_shang: str = '', zhi_shang: str = ''):
        """第89法: 任信丁马须言动 / 第90法: 来去俱空岂动宜
        伏吟+丁神→静中求动；返吟+三传皆空→虽动实不动。
        """
        if not trend or not sanchuan or len(sanchuan) != 3:
            return

        # 第89法: 伏吟+丁马 → 静中求动
        # 伏吟课: 三传地支相同
        is_fuyin = sanchuan[0] == sanchuan[1] == sanchuan[2]

        if is_fuyin and ganzhi:
            ding_shen = get_ding_shen(ganzhi)
            if ding_shen:
                has_ding = False
                ding_pos = ''
                for i, z in enumerate(sanchuan):
                    if z == ding_shen:
                        has_ding = True
                        ding_pos = ['初传', '中传', '末传'][i]
                        break
                if not has_ding and gan_shang and gan_shang == ding_shen:
                    has_ding = True
                    ding_pos = '干上'
                if not has_ding and zhi_shang and zhi_shang == ding_shen:
                    has_ding = True
                    ding_pos = '支上'
                if has_ding:
                    self._add_rule(89, f'伏吟课逢丁神{ding_shen}在{ding_pos}，静中求动，任信丁马须言动')

        # 第90法: 返吟+三传皆落空亡 → 虽有动意实不动
        # 返吟课: 初传与末传相冲
        is_fanyin = LIUCHONG.get(sanchuan[0], '') == sanchuan[2]

        if is_fanyin:
            fxk = get_fen_xun_kong(ganzhi) if ganzhi else None
            if fxk:
                ben, qian, hou, waihou = fxk['本旬'], fxk['前旬'], fxk['后旬'], fxk['外后旬']
                chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
                jinru = chu in ben and zhong in ben and mo in qian
                tuiru = chu in ben and zhong in hou and mo in waihou
                if jinru or tuiru:
                    self._add_rule(90, f'返吟课三传{sanchuan}皆落空亡（分旬），来去俱空岂动宜')
    
    def _check_rule_88(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第88法: 干支乘墓各昏迷"""
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_mu = MU.get(ri_gan, '')
        zhi_mu = WUXING_MU.get(ZHI_WUXING.get(ri_zhi, ''), '')  # 支墓用五行墓（地支→五行→墓），MU 是天干墓表
        if gan_mu and zhi_mu and gan_shang == gan_mu and zhi_shang == zhi_mu:
            self._add_rule(88, f'干上{gan_shang}为干墓，支上{zhi_shang}为支墓，干支乘墓')

    # === Batch2: 第51-73法 ===

    def _check_rule_51(self, sanchuan: List[str], ri_gan: str, tiandi_pan: Optional[Dict] = None):
        """第51法: 魁度天门关隔定
        戌（天魁）加亥（天门）为用者，百事阻隔。
        即：初传为戌，且天盘戌临地盘亥（戌加亥）。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        if sanchuan[0] != '戌':
            return
        if tiandi_pan and tiandi_pan.get('亥') == '戌':
            self._add_rule(51, f'初传戌（天魁）加亥（天门）为用，魁度天门，百事阻隔')

    def _check_rule_52(self, sanchuan: List[str], ri_gan: str, tiandi_pan: Optional[Dict] = None):
        """第52法: 罡塞鬼户任谋为
        辰（天罡）加寅（鬼户），百邪不侵。
        即：初传为辰，且天盘辰临地盘寅（辰加寅）。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        if sanchuan[0] != '辰':
            return
        if tiandi_pan and tiandi_pan.get('寅') == '辰':
            self._add_rule(52, f'初传辰（天罡）加寅（鬼户），罡塞鬼户任谋为')

    def _check_rule_53(self, ri_gan: str, gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第53法: 两蛇夹墓凶难免
        墓神临干支，兼天将乘螣蛇（蛇），名两蛇夹墓。
        """
        if not ri_gan or (not gan_shang and not zhi_shang):
            return
        gan_mu = MU.get(ri_gan, '')
        if not gan_mu:
            return
        # 墓神临干支
        mu_pos = ''
        if gan_shang == gan_mu:
            mu_pos = f'干上{gan_shang}'
        elif zhi_shang == gan_mu:
            mu_pos = f'支上{zhi_shang}'
        if not mu_pos:
            return
        # 天将乘螣蛇（蛇）
        if tian_jiang and '螣蛇' in tian_jiang.values():
            self._add_rule(53, f'{mu_pos}为日干墓神，天将乘螣蛇，两蛇夹墓凶难免')

    def _check_rule_57(self, sanchuan: List[str], ri_gan: str, kongwang: Tuple[str, str]):
        """第57法: 费有余而得不足
        生我者（父母爻）空亡，脱我者（子孙爻）实在。所得不偿所费。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        if not kongwang or not kongwang[0]:
            return

        has_parent_kong = False
        has_child_not_kong = False

        for z in sanchuan:
            if _is_gan_parent(ri_gan, z) and z in kongwang:
                has_parent_kong = True
            if _is_gan_child(ri_gan, z) and z not in kongwang:
                has_child_not_kong = True

        if has_parent_kong and has_child_not_kong:
            self._add_rule(57, f'生干之神旬空，脱干之神实在，费有余得不足')

    def _check_rule_58(self, sanchuan: List[str], ri_gan: str, kongwang: Tuple[str, str]):
        """第58法: 用破身心无所归
        初传财禄皆作空被克，全无实得。
        初传为日干之财且在旬空中，或被中传所克；或初传为禄神且空。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu, zhong = sanchuan[0], sanchuan[1]

        # 初传为财且空
        if _is_gan_wealth(ri_gan, chu) and kongwang and kongwang[0] and chu in kongwang:
            self._add_rule(58, f'初传{chu}为日干{ri_gan}之财在旬空，用破身心无所归')
            return
        # 初传为禄神且空
        lu = LU_SHEN.get(ri_gan, '')
        if lu and chu == lu and kongwang and kongwang[0] and chu in kongwang:
            self._add_rule(58, f'初传{chu}为日干禄神在旬空，用破身心无所归')
            return
        # 初传被中传克（无论财/禄）
        if _zhi_ke_zhi(zhong, chu) and (_is_gan_wealth(ri_gan, chu) or chu == LU_SHEN.get(ri_gan, '')):
            self._add_rule(58, f'初传{chu}(财/禄)被中传{zhong}克，用破身心无所归')

    def _check_rule_59(self, ri_gan: str, gan_shang: str):
        """第59法: 华盖覆日人昏晦
        支墓临干上。检查干上神是否为日干的墓神（MU）。
        """
        if not ri_gan or not gan_shang:
            return
        gan_mu = MU.get(ri_gan, '')
        if gan_mu and gan_shang == gan_mu:
            self._add_rule(59, f'干上{gan_shang}为日干{ri_gan}之墓，华盖覆日人昏晦')

    def _check_rule_60(self, ri_zhi: str, zhi_shang: str, yuejiang: str):
        """第60法: 太阳射宅屋光辉
        支墓作月将（太阳），反名太阳辉照家宅。
        """
        if not ri_zhi or not zhi_shang or not yuejiang:
            return
        zhi_mu = WUXING_MU.get(ZHI_WUXING.get(ri_zhi, ''), '')  # 支墓用五行墓（地支→五行→墓），MU 是天干墓表
        yj = yuejiang.replace('将', '').strip() if yuejiang else ''
        if zhi_mu and zhi_shang == zhi_mu and zhi_shang == yj:
            self._add_rule(60, f'支上{zhi_shang}为支墓亦为月将（太阳），太阳射宅屋光辉')

    def _check_rule_63(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第63法: 彼此全伤防两损
        干支各被上神克伐者。
        干被干上神克，支被支上神克。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_ke = _is_gan_ghost(ri_gan, gan_shang)
        zhi_ke = _zhi_ke_zhi(zhi_shang, ri_zhi)
        if gan_ke and zhi_ke:
            self._add_rule(63, f'干被干上{gan_shang}克，支被支上{zhi_shang}克，彼此全伤防两损')

    def _check_rule_64(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第64法: 夫妇芜淫各有私
        干被支上神克，支被干上神克。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_beizhi_ke = _is_gan_ghost(ri_gan, zhi_shang)
        zhi_beigan_ke = _zhi_ke_zhi(gan_shang, ri_zhi)
        if gan_beizhi_ke and zhi_beigan_ke:
            self._add_rule(64, f'干被支上{zhi_shang}克，支被干上{gan_shang}克，夫妇芜淫各有私')

    def _check_rule_65(self, sanchuan: List[str], ri_gan: str, ri_zhi: str,
                       season: str = '', gan_shang: str = '', zhi_shang: str = ''):
        """第65法: 干墓并关人宅废
        日干之墓作四季之关神（春丑夏辰秋未冬戌）发用，分干支发用：
        临干上主人口衰，临支上主宅废。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        guan_map = {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'}
        guan = guan_map.get(season, '')
        if not guan:
            return
        gan_mu = MU.get(ri_gan, '')
        if not gan_mu or gan_mu != guan:
            return  # 日干墓 = 四季关神
        chu = sanchuan[0]
        if chu != gan_mu:
            return  # 日干墓发用
        if gan_shang == chu:
            self._add_rule(65, f'日干{ri_gan}墓{gan_mu}作{season}关神发用临干上，主人口衰，干墓并关人宅废')
        elif zhi_shang == chu:
            self._add_rule(65, f'日干{ri_gan}墓{gan_mu}作{season}关神发用临支上，主宅废，干墓并关人宅废')

    def _check_rule_66(self, sanchuan: List[str], ri_gan: str, ri_zhi: str):
        """第66法: 支坟财并旅程稽
        地支之墓作日干之财者，商贩折本。
        检查三传中是否有地支=支墓=日干财。
        """
        if len(sanchuan) != 3 or not ri_gan or not ri_zhi:
            return
        zhi_mu = WUXING_MU.get(ZHI_WUXING.get(ri_zhi, ''), '')  # 支墓用五行墓（地支→五行→墓），MU 是天干墓表
        if not zhi_mu:
            return
        for z in sanchuan:
            if z == zhi_mu and _is_gan_wealth(ri_gan, z):
                self._add_rule(66, f'三传中{zhi_mu}为支墓且为日干{ri_gan}之财，支坟财并旅程稽')
                return

    def _check_rule_73(self, sanchuan: List[str], ri_gan: str):
        """第73法: 前后逼迫难进退
        初传为鬼（克干）且末传也为鬼（克干），前后受克。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu, mo = sanchuan[0], sanchuan[2]
        if _is_gan_ghost(ri_gan, chu) and _is_gan_ghost(ri_gan, mo):
            self._add_rule(73, f'初传{chu}克干{ri_gan}，末传{mo}克干{ri_gan}，前后逼迫难进退')

    # === Batch1: 第1-80法补充 ===

    def _check_rule_1(self, sanchuan: List[str], ri_gan: str, ri_zhi: str):
        """第1法: 前后引从升迁吉
        初传居干前为引，末传居干后为从；或初传居支前引，末传居支后从。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu, mo = sanchuan[0], sanchuan[2]
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        # 初传在干前（顺行方向），末传在干后（逆行方向）
        if _is_zhi_before(chu, gan_pos) and _is_zhi_after(mo, gan_pos):
            self._add_rule(1, f'初传{chu}居干{gan_pos}前为引，末传{mo}居干后为从，前后引从升迁吉')
            return
        # 初传在支前，末传在支后
        if ri_zhi and _is_zhi_before(chu, ri_zhi) and _is_zhi_after(mo, ri_zhi):
            self._add_rule(1, f'初传{chu}居支{ri_zhi}前为引，末传{mo}居支后为从，前后引从升迁吉')

    def _check_rule_2(self, ri_gan: str, ri_zhi: str, ganzhi: str, gan_shang: str, zhi_shang: str):
        """第2法: 首尾相见始终宜
        干上有旬尾，支上有旬首，名周而复始格。
        """
        if not ganzhi or not gan_shang or not zhi_shang:
            return
        xun_shou = get_xun_shou(ganzhi)
        xun_wei = get_xun_wei(ganzhi)
        if not xun_shou or not xun_wei:
            return
        shou_zhi = xun_shou[1] if len(xun_shou) > 1 else ''
        wei_zhi = xun_wei[1] if len(xun_wei) > 1 else ''
        if gan_shang == wei_zhi and zhi_shang == shou_zhi:
            self._add_rule(2, f'干上{gan_shang}为旬尾，支上{zhi_shang}为旬首，首尾相见始终宜')

    def _check_rule_5(self, sanchuan: List[str], ri_gan: str, ri_zhi: str, si_ke_info=None):
        """第5法: 六阳数足须公用
        支干四课三传皆居六阳之位（子寅辰午申戌）。
        """
        if len(sanchuan) != 3 or not ri_gan or not ri_zhi:
            return
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        sike_shang = _extract_sike_shang(si_ke_info)
        all_zhi = [z for z in list(sanchuan) + [gan_pos, ri_zhi] + sike_shang if z]
        if all_zhi and all(_is_yang_zhi(z) for z in all_zhi):
            self._add_rule(5, f'四课三传干支（{all_zhi}）全居阳位，六阳数足须公用')

    def _check_rule_6(self, sanchuan: List[str], ri_gan: str, ri_zhi: str, si_ke_info=None):
        """第6法: 六阴相继尽昏迷
        支干四课三传皆居六阴之位（丑卯巳未酉亥）。
        """
        if len(sanchuan) != 3 or not ri_gan or not ri_zhi:
            return
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        sike_shang = _extract_sike_shang(si_ke_info)
        all_zhi = [z for z in list(sanchuan) + [gan_pos, ri_zhi] + sike_shang if z]
        if all_zhi and all(_is_yin_zhi(z) for z in all_zhi):
            self._add_rule(6, f'四课三传干支（{all_zhi}）全居阴位，六阴相继尽昏迷')

    def _check_rule_7(self, ri_gan: str, gan_shang: str):
        """第7法: 旺禄临身徒妄作
        日之禄神又作日之旺神临于干上者。
        """
        if not ri_gan or not gan_shang:
            return
        lu = LU_SHEN.get(ri_gan, '')
        wang = ZHI_WANG.get(gan_shang, '')
        if lu and lu == gan_shang and wang == gan_shang:
            self._add_rule(7, f'干上{gan_shang}为日干{ri_gan}禄神兼旺神，旺禄临身徒妄作')

    def _check_rule_8(self, ri_gan: str, zhi_shang: str):
        """第8法: 权摄不正禄临支
        日干禄神加临支辰上者。
        """
        if not ri_gan or not zhi_shang:
            return
        lu = LU_SHEN.get(ri_gan, '')
        if lu and zhi_shang == lu:
            self._add_rule(8, f'日干{ri_gan}禄神{lu}临支上，权摄不正禄临支')

    def _check_rule_11(self, sanchuan: List[str], ri_gan: str, gan_shang: str):
        """第11法: 众鬼虽彰全不畏
        三传皆鬼，干上有救神制鬼。
        """
        if len(sanchuan) != 3 or not ri_gan or not gan_shang:
            return
        if all(_is_gan_ghost(ri_gan, z) for z in sanchuan):
            # 干上神能克三传中的鬼
            if any(_zhi_ke_zhi(gan_shang, z) for z in sanchuan):
                self._add_rule(11, f'三传{sanchuan}皆鬼，干上{gan_shang}制鬼，众鬼虽彰全不畏')

    def _check_rule_12(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第12法: 虽忧狐假虎威仪
        干畏克而赖支制之：干上神克干（鬼），支上神能克干上神。
        """
        if not ri_gan or not gan_shang or not zhi_shang:
            return
        if _is_gan_ghost(ri_gan, gan_shang) and _zhi_ke_zhi(zhi_shang, gan_shang):
            self._add_rule(12, f'干上{gan_shang}为鬼，支上{zhi_shang}制鬼，狐假虎威仪')

    def _check_rule_13(self, sanchuan: List[str], ri_gan: str, season: str):
        """第13法: 鬼贼当时无畏忌
        三传全逢日鬼（含三会/三合局为鬼），且鬼旺相（当季旺或相），鬼贪荣不克干，暂时无畏（通解中L4559"戊子日三传寅卯辰皆日鬼，春占木旺；三合为鬼亦如前说"）。
        """
        if len(sanchuan) != 3 or not ri_gan or not season:
            return
        season_wx = SEASON_WANG.get(season, '')
        if not season_wx:
            return
        gan_wx = GAN_WUXING.get(ri_gan, '')
        ghost_wx = {'土': '木', '水': '土', '火': '水', '金': '火', '木': '金'}.get(gan_wx, '')  # 克干五行
        if not ghost_wx:
            return
        # 三传皆鬼：单个地支五行皆克干，或三会局/三合局为鬼
        all_ghost = all(_is_gan_ghost(ri_gan, z) for z in sanchuan)
        if not all_ghost:
            s = frozenset(sanchuan)
            hui = {frozenset('寅卯辰'): '木', frozenset('巳午未'): '火', frozenset('申酉戌'): '金', frozenset('亥子丑'): '水'}
            he = {frozenset('申子辰'): '水', frozenset('寅午戌'): '火', frozenset('亥卯未'): '木', frozenset('巳酉丑'): '金'}
            if hui.get(s, '') == ghost_wx or he.get(s, '') == ghost_wx:
                all_ghost = True
        if not all_ghost:
            return
        xiang_wx = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(season_wx, '')  # 相 = 旺所生
        if ghost_wx == season_wx or ghost_wx == xiang_wx:
            self._add_rule(13, f'三传{sanchuan}皆日鬼且鬼逢旺相（{season}）贪荣不克干，鬼贼当时无畏忌')

    def _check_rule_15(self, ri_gan: str, gan_shang: str, tian_jiang: Optional[Dict] = None):
        """第15法: 脱上逢脱防虚诈
        两层脱缺一不可：
        ① 干生上神（上神为日干之脱气，子孙泄日干）；
        ② 上神又生「天将本家」（天将正位地支，如白虎本家申金、青龙本家寅木）。
        干→上神→天将本家 连环相生，层层脱耗，方为"脱上逢脱"。
        ⚠️ 2026-08-15 憨爷纠错：不能用天将名字做生克，必须用天将本家地支的五行。
        反例：辛酉日干上亥乘白虎——干辛金生亥水（①满足），但白虎本家申金生亥水，
        是"天将本家生上神"而非"上神生天将本家"，故不构成"脱上逢脱"，不应命中。
        """
        if not ri_gan or not gan_shang:
            return
        # ① 干生上神（上神为脱气）
        if not _is_gan_child(ri_gan, gan_shang):
            return
        detail = f'干{ri_gan}生上神{gan_shang}（脱气）'
        # ② 上神生天将本家（第二层脱）
        if tian_jiang:
            # tian_jiang 两种格式兼容：{天盘支: 天将名} 或 {'干上': 天将名}
            jiang = (tian_jiang.get(gan_shang, '') or tian_jiang.get('干上', '')
                     or tian_jiang.get('gan_shang', ''))
            benjia = TIANJIANG_BENJIA.get(jiang, '')
            if jiang and benjia and _zhi_sheng_zhi(gan_shang, benjia):
                bj_wx = ZHI_WUXING.get(benjia, '')
                detail += f'，上神{gan_shang}又生天将{jiang}本家{benjia}（{bj_wx}），脱上逢脱'
                self._add_rule(15, detail + '，脱上逢脱防虚诈')
        # 仅①满足、②不满足者，只算"干上脱气"，不构成"脱上逢脱"，不输出此句

    def _check_rule_21(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第21法: 交车相合交关利
        日干与支上神六合，地支与干上神六合。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        if LIUHE.get(gan_pos, '') == zhi_shang and LIUHE.get(ri_zhi, '') == gan_shang:
            self._add_rule(21, f'干{ri_gan}({gan_pos})合支上{zhi_shang}，支{ri_zhi}合干上{gan_shang}，交车相合交关利')

    def _check_rule_22(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第22法: 上下皆合两心齐
        干支上神六合，地支干支亦六合。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        if LIUHE.get(gan_shang, '') == zhi_shang and LIUHE.get(gan_pos, '') == ri_zhi:
            self._add_rule(22, f'干上{gan_shang}合支上{zhi_shang}，干{ri_gan}({gan_pos})合支{ri_zhi}，上下皆合两心齐')

    def _check_rule_55(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第55法: 所谋多拙逢罗网
        干上乘干前一辰（天罗），支上乘支前一辰（地网）。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        gan_pos = GAN_JIGONG.get(ri_gan, '')
        if not gan_pos:
            return
        gan_next = _get_next_zhi(gan_pos)
        zhi_next = _get_next_zhi(ri_zhi)
        if gan_shang == gan_next and zhi_shang == zhi_next:
            self._add_rule(55, f'干上{gan_shang}=干{gan_pos}前{gan_next}，支上{zhi_shang}=支{ri_zhi}前{zhi_next}，所谋多拙逢罗网')

    def _check_rule_74(self, sanchuan: List[str], kongwang: Tuple[str, str], ganzhi: str = ''):
        """第74法: 空空如也事休追
        三传皆落空亡（分旬：进茹前两传本旬空末传前旬空；退茹初传本旬空中传后旬空末传外后旬空）（通解中L7212）。
        """
        if len(sanchuan) != 3:
            return
        fxk = get_fen_xun_kong(ganzhi) if ganzhi else None
        if not fxk:
            return
        ben, qian, hou, waihou = fxk['本旬'], fxk['前旬'], fxk['后旬'], fxk['外后旬']
        chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
        jinru = chu in ben and zhong in ben and mo in qian
        tuiru = chu in ben and zhong in hou and mo in waihou
        if jinru or tuiru:
            self._add_rule(74, f'三传{sanchuan}皆落空亡（分旬），空空如也事休追')

    def _check_rule_75(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str, sanchuan: List[str] = None):
        """第75法: 宾主不投刑在上
        干支乘刑：干支上全逢自刑、互刑、无礼刑、或三传全刑。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        # 干支上自刑（辰午酉亥）
        if gan_shang in ('辰','午','酉','亥') and zhi_shang in ('辰','午','酉','亥'):
            self._add_rule(75, f'干支上{gan_shang}/{zhi_shang}皆自刑，宾主不投刑在上')
            return
        # 无礼刑（子卯互刑）
        if (gan_shang == '子' and zhi_shang == '卯') or (gan_shang == '卯' and zhi_shang == '子'):
            self._add_rule(75, f'干支上{gan_shang}/{zhi_shang}为无礼刑，宾主不投刑在上')
            return
        # 干上刑支上
        if SANXING.get(gan_shang, '') == zhi_shang:
            self._add_rule(75, f'干上{gan_shang}刑支上{zhi_shang}，宾主不投刑在上')
            return
        # 三传无恩刑（寅巳申）或恃势刑（丑戌未）
        if sanchuan and len(sanchuan) == 3:
            sx = set(sanchuan)
            if sx == {'寅', '巳', '申'}:
                self._add_rule(75, f'三传{sanchuan}为无恩刑（寅巳申），宾主不投刑在上')
                return
            if sx == {'丑', '戌', '未'}:
                self._add_rule(75, f'三传{sanchuan}为恃势刑（丑戌未），宾主不投刑在上')
            return

    def _check_rule_76(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str, sanchuan: List[str]):
        """第76法: 彼此猜忌害相随
        干支上下害，干支上神害，或三传有六害。
        """
        gan_pos = GAN_JIGONG.get(ri_gan, '') if ri_gan else ''
        # 干支相害
        if gan_pos and ri_zhi and LIUHAI.get(gan_pos, '') == ri_zhi:
            self._add_rule(76, f'干支{ri_gan}({gan_pos}){ri_zhi}相害，彼此猜忌害相随')
            return
        # 干支上神相害
        if gan_shang and zhi_shang and LIUHAI.get(gan_shang, '') == zhi_shang:
            self._add_rule(76, f'干上{gan_shang}害支上{zhi_shang}，彼此猜忌害相随')
            return
        # 三传含六害对
        if sanchuan and len(sanchuan) >= 2:
            for i in range(len(sanchuan)):
                for j in range(i+1, len(sanchuan)):
                    if LIUHAI.get(sanchuan[i], '') == sanchuan[j]:
                        self._add_rule(76, f'三传中{sanchuan[i]}害{sanchuan[j]}，彼此猜忌害相随')
                        return

    def _check_rule_78(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str, season: str = ''):
        """第78法: 互旺皆旺坐谋宜
        干支上互乘旺神，或干支上皆乘旺神。
        """
        if not gan_shang or not zhi_shang:
            return
        if _is_zhi_wang(gan_shang, season) and _is_zhi_wang(zhi_shang, season):
            self._add_rule(78, f'干上{gan_shang}为旺、支上{zhi_shang}为旺，互旺皆旺坐谋宜')

    def _check_rule_80(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str, yuejiang: str):
        """第80法: 人宅皆死各衰羸
        干支上互乘死气（干上=支死位、支上=干死位），或全乘月内死气（通解中L7492"戊申日干上子支上卯"）。
        """
        if not gan_shang or not zhi_shang:
            return
        gan_si = _wx_si(GAN_WUXING.get(ri_gan, ''))   # 干死位（土双位）
        zhi_si = _wx_si(ZHI_WUXING.get(ri_zhi, ''))   # 支死位（土双位）
        # 互乘死气：干上=支死位、支上=干死位
        hu_cheng = bool(zhi_si) and bool(gan_si) and gan_shang in zhi_si and zhi_shang in gan_si
        # 全乘月内死气
        si_qi = _get_si_qi(yuejiang) if yuejiang else ''
        quan_cheng = bool(si_qi) and gan_shang == si_qi and zhi_shang == si_qi
        if hu_cheng or quan_cheng:
            self._add_rule(80, f'干支上乘死气（互乘或全乘），人宅皆死各衰羸')

    # === Batch3: 虎龙病讼凶灾系列 ===

    def _check_rule_54(self, ri_gan: str, tian_jiang: Optional[Dict] = None, keti: str = ''):
        """第54法: 虎视逢虎力难施
        昴星课（虎视课）中天将又乘白虎，前后皆虎，力难施。
        ⚠️ 专指昴星课（虎视课），非昴星课不构成（2026-08-15 憨爷纠错：别责课不可误判）。
        """
        if not tian_jiang:
            return
        # 必须昴星课（虎视课）
        if '昴星' not in (keti or '') and '虎视' not in (keti or ''):
            return
        if '白虎' in tian_jiang.values():
            bai_hu_pos = [k for k, v in tian_jiang.items() if v == '白虎']
            self._add_rule(54, f'昴星课（虎视课）天将{bai_hu_pos}乘白虎，虎视逢虎力难施')

    def _check_rule_56(self, ri_gan: str, gan_shang: str, ben_ming_zhi: str = ''):
        """第56法: 天网自裹己招非
        墓神覆日，且占人本命又为墓神（本命地支=日干墓），名天网自裹。
        """
        if not ri_gan or not gan_shang:
            return
        gan_mu = MU.get(ri_gan, '')
        if not gan_mu or gan_shang != gan_mu:
            return
        if ben_ming_zhi and ben_ming_zhi == gan_mu:
            self._add_rule(56, f'干上{gan_shang}为日干{ri_gan}墓神覆日，本命{ben_ming_zhi}又为墓神，天网自裹己招非')

    def _check_rule_61(self, ri_gan: str, gan_shang: str, tian_jiang: Optional[Dict] = None, ben_ming_zhi: str = '', is_day: bool = True):
        """第61法: 干乘墓虎无占病
        六辛日丑加戌「昼将」乘白虎作墓神（辛墓丑，丑加戌=干上丑乘虎，昼占）；
        六乙日未乘白虎临本命/行年（乙墓未，未乘虎临本命，非加干）。余干无此例。
        """
        if not ri_gan or not tian_jiang:
            return
        gan_mu = MU.get(ri_gan, '')
        if not gan_mu:
            return
        if ri_gan == '辛':
            if is_day and gan_shang == gan_mu and tian_jiang.get(gan_shang, '') == '白虎':
                self._add_rule(61, f'六辛日昼占干上{gan_shang}(辛墓丑)乘白虎，干乘墓虎无占病')
        elif ri_gan == '乙':
            if tian_jiang.get(gan_mu, '') == '白虎' and ben_ming_zhi == gan_mu:
                self._add_rule(61, f'六乙日{gan_mu}(乙墓未)乘白虎临本命{ben_ming_zhi}，干乘墓虎无占病')

    def _check_rule_62(self, ri_gan: str, ri_zhi: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第62法: 支乘墓虎有伏尸
        干墓临支或支墓临支 + 白虎
        """
        if not ri_gan or not ri_zhi or not zhi_shang:
            return
        gan_mu = MU.get(ri_gan, '')
        zhi_mu = WUXING_MU.get(ZHI_WUXING.get(ri_zhi, ''), '')  # 支墓用五行墓（地支→五行→墓），MU 是天干墓表
        is_mu = (gan_mu and zhi_shang == gan_mu) or (zhi_mu and zhi_shang == zhi_mu)
        if not is_mu:
            return
        if tian_jiang and tian_jiang.get(zhi_shang, '') == '白虎':
            mu_type = '干墓' if (gan_mu and zhi_shang == gan_mu) else '支墓'
            ke_zhai = _zhi_ke_zhi(zhi_shang, ri_zhi)  # 克宅者为的（通解中L6631"未加酉不克支稍轻"）
            qing = '克宅为的' if ke_zhai else '不克宅稍轻'
            self._add_rule(62, f'支上{zhi_shang}为{mu_type}临支乘白虎（{qing}），支乘墓虎有伏尸')

    def _check_rule_67(self, ri_gan: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第67法: 受虎克神为病症
        古籍注解（毕法赋_古籍注解_下 第六七，脏腑口径=神之所克）：
        "金神乘白虎，必是肝经受病，可治肺而不可治肝。木神乘白虎，必是脾经受病…
        水→心、火→肺、土→肾。受虎克之国民流兵疫。"
        【2026-08-21 修复（用户指正"辰为子孙乘白虎不算受虎克神"）】：
        ① 范围：只查课传六处（三传+干上+支上），不再全盘扫描天将（原实现任何支乘白虎即触发，
           天盘无关支也报病）；
        ② 正格：神受虎克者方名"受虎克神为病症"——白虎属庚申金，金克木，木神乘虎为正受虎克；
           其余五行乘虎为变格"虎乘X神，X经受病"（古籍注解明列五神，不属正格但仍作脏腑提示）；
        ③ 六亲辅助：神为日干官鬼者病难速愈（古籍"白虎乘日鬼而作空亡，必已病而未瘥"），
           为子孙（制虎之神）者可疗（68法"制鬼之位乃良医"）。
        """
        if not tian_jiang:
            return
        organ_map = {'金': '肝', '木': '脾', '水': '心', '火': '肺', '土': '肾'}
        check_positions = list(sanchuan or [])
        for _p in (gan_shang, zhi_shang):
            if _p:
                check_positions.append(_p)
        for zhi in check_positions:
            if tian_jiang.get(zhi, '') != '白虎':
                continue
            wx = ZHI_WUXING.get(zhi, '')
            organ = organ_map.get(wx, '')
            if not organ:
                continue
            zheng = (wx == '木')  # 白虎庚申金，金克木→木神正受虎克
            lq = ''
            if ri_gan:
                if _is_gan_ghost(ri_gan, zhi):
                    lq = '；神为日干官鬼，病难速愈'
                elif _is_gan_child(ri_gan, zhi):
                    lq = '；神为日干子孙（制虎之神），病可疗'
            if zheng:
                self._add_rule(67, f'白虎乘{zhi}(木神，金克木正受虎克)，{organ}经受病，受虎克神为病症{lq}')
            else:
                self._add_rule(67, f'虎乘{zhi}({wx}神)，{organ}经受病（受虎克神为病症·变格）{lq}')
            return

    def _check_rule_68(self, sanchuan: List[str], ri_gan: str, gan_shang: str = ''):
        """第68法: 制鬼之位乃良医
        制鬼之神(食神/子孙爻)克鬼，即是良医。
        三传中有能克鬼的地支。
        """
        if not sanchuan or not ri_gan:
            return
        ghosts = []
        check_positions = list(sanchuan)
        if gan_shang:
            check_positions.append(gan_shang)
        for z in check_positions:
            if _is_gan_ghost(ri_gan, z):
                ghosts.append(z)
        if not ghosts:
            return
        for ghost in ghosts:
            for z in sanchuan:
                if z != ghost and _zhi_ke_zhi(z, ghost):
                    self._add_rule(68, f'三传中{z}克鬼{ghost}，制鬼之位乃良医')
                    return

    def _check_rule_69(self, ri_gan: str, ganzhi: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第69法: 虎乘遁鬼殃非浅
        白虎加临旬内之干为日鬼者。
        需要旬遁干计算。
        """
        if not ri_gan or not ganzhi or not tian_jiang:
            return
        xun_shou = XUN_SHOU.get(ganzhi, '')
        if not xun_shou:
            return
        dun_map = XUN_DUNGAN.get(xun_shou, {})
        if not dun_map:
            return
        for zhi, jiang in tian_jiang.items():
            if jiang != '白虎':
                continue
            dun_gan = dun_map.get(zhi, '')
            if not dun_gan:
                continue
            if _gan_ke_gan(dun_gan, ri_gan):
                self._add_rule(69, f'白虎乘{zhi}，遁干{dun_gan}为日干{ri_gan}之鬼，虎乘遁鬼殃非浅')
                return

    def _check_rule_70(self, ri_gan: str, si_ke_info: Optional[List[str]] = None):
        """第70法: 鬼临三四讼灾随
        日干之鬼临于第三四课全者。
        【BUG-FIX 2026-08-18】sike 元素为 tuple ('第一课',上神,下神,天将)，
        原 `zhi in ke3` 对 tuple 恒 False → 永不触发；改为从课位中提取地支判断。
        """
        if not ri_gan or not si_ke_info or len(si_ke_info) < 4:
            return
        ke3 = si_ke_info[2] if len(si_ke_info) > 2 else None
        ke4 = si_ke_info[3] if len(si_ke_info) > 3 else None

        def _ghost_in(ke) -> bool:
            if not ke:
                return False
            # 兼容 tuple/list ('第三课', 上神, 下神, 天将) 与 dict 格式
            if isinstance(ke, dict):
                zhis = [ke.get('上神', ''), ke.get('下神', '')]
            else:
                zhis = list(ke)[1:3] if len(ke) >= 3 else list(ke)
            return any(_is_gan_ghost(ri_gan, z) for z in zhis if z and z in DIZHI_ORDER)

        ghost_in_3 = _ghost_in(ke3)
        ghost_in_4 = _ghost_in(ke4)
        if ghost_in_3 and ghost_in_4:
            self._add_rule(70, f'日干{ri_gan}之鬼临第三课第四课，鬼临三四讼灾随')

    def _check_rule_71(self, ri_zhi: str, zhi_shang: str, tai_sui: str = ''):
        """第71法: 病符克宅全家患
        病符(去年太岁)临支又克支。
        """
        if not ri_zhi or not zhi_shang or not tai_sui:
            return
        idx = DIZHI_INDEX.get(tai_sui, -1)
        if idx < 0:
            return
        bing_fu = DIZHI_ORDER[(idx - 1) % 12]  # 去年太岁 = 病符
        if zhi_shang == bing_fu and _zhi_ke_zhi(zhi_shang, ri_zhi):
            self._add_rule(71, f'病符{bing_fu}(去年太岁)临支又克支{ri_zhi}，病符克宅全家患')

    def _check_rule_72(self, gan_shang: str, zhi_shang: str, tai_sui: str = ''):
        """第72法: 丧吊全逢挂缟衣
        岁前二辰丧门 + 岁后二辰吊客，干支上全逢。
        """
        if not gan_shang or not zhi_shang or not tai_sui:
            return
        idx = DIZHI_INDEX.get(tai_sui, -1)
        if idx < 0:
            return
        sang_men = DIZHI_ORDER[(idx + 2) % 12]  # 岁前二辰 = 丧门
        diao_ke = DIZHI_ORDER[(idx - 2) % 12]   # 岁后二辰 = 吊客
        if (gan_shang == sang_men and zhi_shang == diao_ke) or (gan_shang == diao_ke and zhi_shang == sang_men):
            self._add_rule(72, f'干上{gan_shang}支上{zhi_shang}全逢丧门{sang_men}吊客{diao_ke}，丧吊全逢挂缟衣')

    def _check_rule_91(self, ri_gan: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第91法: 虎临干鬼凶速速
        日干之鬼上乘白虎者，凶祸速中又速。
        """
        if not ri_gan or not tian_jiang:
            return
        for zhi, jiang in tian_jiang.items():
            if jiang != '白虎':
                continue
            if _is_gan_ghost(ri_gan, zhi):
                self._add_rule(91, f'{zhi}为日干{ri_gan}之鬼乘白虎，虎临干鬼凶速速')
                return

    def _check_rule_92(self, ri_gan: str, yuejiang: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第92法: 龙加生气吉迟迟
        青龙乘生干之神又作月内生气，徐徐发福。
        """
        if not ri_gan or not tian_jiang or not yuejiang:
            return
        sheng_qi = _get_sheng_qi(yuejiang)
        if not sheng_qi:
            return
        for zhi, jiang in tian_jiang.items():
            if jiang != '青龙':
                continue
            if _is_gan_parent(ri_gan, zhi) and zhi == sheng_qi:
                self._add_rule(92, f'{zhi}乘青龙，生干且为月令生气{sheng_qi}，龙加生气吉迟迟')
                return

    # === Batch3: 第9,10,23,24,34,37,38,93-100 ===

    def _check_rule_9(self, sanchuan: List[str], ri_gan: str, gan_shang: str):
        """第9法: 避难逃生须弃旧
        三传皆克干(鬼)或脱干(子孙)，但干上神生干——干上为救神，避难逃生。
        """
        if len(sanchuan) != 3 or not ri_gan or not gan_shang:
            return
        # 三传是否全对干不利（鬼或子孙/脱气）
        all_bad = all(
            _is_gan_ghost(ri_gan, z) or _is_gan_child(ri_gan, z)
            for z in sanchuan
        )
        if not all_bad:
            return
        # 干上神生干 — 有救神
        if _is_gan_parent(ri_gan, gan_shang):
            self._add_rule(9, f'三传{sanchuan}皆不利日干{ri_gan}，干上{gan_shang}生干为救神，避难逃生须弃旧')

    def _check_rule_10(self, sanchuan: List[str], ganzhi: str,
                       kongwang: Tuple[str, str], si_ke_info: Optional[List[str]] = None,
                       tiandi_pan: Optional[Dict] = None):
        """第10法: 朽木难雕别作为
        斫轮课（天盘卯加地盘申发用）中卯为空亡，名朽木不可雕（通解中L4362"庚戊日卯加申"）。
        """
        if len(sanchuan) != 3 or sanchuan[0] != '卯':
            return
        # 斫轮课：天盘卯加地盘申发用（无天地盘时兜底：四课含申）
        mao_jia_shen = False
        if tiandi_pan:
            mao_jia_shen = (tiandi_pan.get('申', '') == '卯')
        else:
            mao_jia_shen = bool(si_ke_info) and any('申' in str(ke) for ke in si_ke_info if ke)
        if not mao_jia_shen:
            return
        # 卯为空亡
        kw = kongwang if (kongwang and kongwang[0]) else \
            get_xun_kong(ganzhi) if ganzhi else ('', '')
        if kw and kw[0] and '卯' in kw:
            self._add_rule(10, f'初传卯加申（斫轮课），卯逢空亡，朽木难雕别作为')

    def _check_rule_23(self, sanchuan: List[str], ri_gan: str, ri_zhi: str,
                       gan_shang: str, zhi_shang: str,
                       si_ke_info: Optional[List[str]] = None):
        """第23法: 彼求我事支传干
        初传从支上起、末传归干上（通解中L4967"癸酉日初传从支上巳起，末传至干上酉止"）。
        """
        if len(sanchuan) != 3 or not gan_shang or not zhi_shang:
            return
        # 初传=支上神、末传=干上神
        if sanchuan[0] == zhi_shang and sanchuan[2] == gan_shang:
            self._add_rule(23, f'初传{sanchuan[0]}从支上起、末传{sanchuan[2]}归干上，彼求我事支传干')

    def _check_rule_24(self, sanchuan: List[str], ri_gan: str, ri_zhi: str,
                       gan_shang: str, zhi_shang: str):
        """第24法: 我求彼事干传支
        初传从干上起，末传归在支上者，凡事勉强，求人于己。
        """
        if len(sanchuan) != 3 or not gan_shang or not zhi_shang:
            return
        # 初传等于干上神，且支上神在传中
        if sanchuan[0] == gan_shang and zhi_shang in sanchuan:
            self._add_rule(24, f'初传{sanchuan[0]}从干上起，传涉支上{zhi_shang}，我求彼事干传支')

    # === 方法论/通识类规则 (93-100) ===

    def _check_rule_93(self, sanchuan: List[str], ri_gan: str = ''):
        """第93法: 妄用三传灾福异
        警示涉害择比等法不可妄用——起三传有错误则灾福无的验。
        仅在三传同时含多个自刑地支或涉害特征明显时才触发。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        # 严格条件：三传中至少2个自刑地支，且有克比涉害特征
        xing_count = sum(1 for z in sanchuan if SANXING.get(z) == z)
        has_kebi = any(
            _zhi_ke_zhi(sanchuan[0], z) for z in sanchuan[1:]
        ) or any(
            _zhi_ke_zhi(z, sanchuan[0]) for z in sanchuan[1:]
        )
        if xing_count >= 2 and has_kebi:
            self._add_rule(93, f'三传{sanchuan}含{xing_count}个自刑且涉克比，涉害择比宜慎用',
                          signal_override='震荡', conf_override='low')

    def _check_rule_94(self, sanchuan: List[str], ri_gan: str,
                       kongwang: Tuple[str, str]):
        """第94法: 喜惧空亡乃妙机
        天盘空亡吉凶七八分，地盘空亡吉凶十分。
        检查三传中空亡对吉凶的影响。
        """
        if len(sanchuan) != 3 or not kongwang or not kongwang[0]:
            return
        kong_in_chuan = [z for z in sanchuan if z in kongwang]
        if not kong_in_chuan:
            return
        # 分析空亡的影响
        effects = []
        for z in kong_in_chuan:
            loc = ['初传', '中传', '末传'][sanchuan.index(z)]
            if _is_gan_ghost(ri_gan, z):
                effects.append(f'{loc}{z}(鬼)空亡为吉')
            elif _is_gan_parent(ri_gan, z):
                effects.append(f'{loc}{z}(父母)空亡为凶')
            elif _is_gan_wealth(ri_gan, z):
                effects.append(f'{loc}{z}(财)空亡为凶')
            elif _is_gan_child(ri_gan, z):
                effects.append(f'{loc}{z}(子孙)空亡为吉')
        if effects:
            self._add_rule(94, f'三传空亡影响：{"，".join(effects)}。喜惧空亡乃妙机')

    def _check_rule_95(self, sanchuan: List[str], ri_gan: str):
        """第95法: 六爻现卦防其克
        三传中现某六亲爻，则忧其所克之类（通解：财爻现忧父母/父母现忧子息/子息现忧官事/官鬼现忧己身/同类现忧妻财）。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        cai = [z for z in sanchuan if _is_gan_wealth(ri_gan, z)]   # 财（干克）
        fu = [z for z in sanchuan if _is_gan_parent(ri_gan, z)]    # 父母（生干）
        zi = [z for z in sanchuan if _is_gan_child(ri_gan, z)]     # 子息（干生）
        gui = [z for z in sanchuan if _is_gan_ghost(ri_gan, z)]    # 官鬼（克干）
        tong = [z for z in sanchuan if ZHI_WUXING.get(z, '') == GAN_WUXING.get(ri_gan, '')]  # 同类（比肩）
        # 五等：某爻现，忧其所克之类
        if cai:
            self._add_rule(95, f'三传财爻{"、".join(cai)}现，忧父母。六爻现卦防其克')
        elif fu:
            self._add_rule(95, f'三传父母{"、".join(fu)}现，忧子息。六爻现卦防其克')
        elif zi:
            self._add_rule(95, f'三传子息{"、".join(zi)}现，忧官事。六爻现卦防其克')
        elif gui:
            self._add_rule(95, f'三传官鬼{"、".join(gui)}现，忧己身兄弟。六爻现卦防其克')
        elif tong:
            self._add_rule(95, f'三传同类{"、".join(tong)}现，忧妻财。六爻现卦防其克')

    def _check_rule_96(self, sanchuan: List[str], ri_gan: str, ganzhi: str,
                       kongwang: Tuple[str, str]):
        """第96法: 旬内空亡逐类推
        逐旬空亡各有类应：财空、鬼空、救空、比空、生空等。
        """
        if not ri_gan or not ganzhi or not kongwang or not kongwang[0]:
            return
        kw = kongwang
        if len(sanchuan) != 3:
            return
        type_effects = []
        for z in sanchuan:
            if z in kw:
                if _is_gan_wealth(ri_gan, z):
                    type_effects.append(f'{z}为财空（财储乏）')
                elif _is_gan_ghost(ri_gan, z):
                    type_effects.append(f'{z}为鬼空（忧散）')
                elif _is_gan_parent(ri_gan, z):
                    type_effects.append(f'{z}为生空（失惠）')
                elif _is_gan_sibling(ri_gan, z):
                    type_effects.append(f'{z}为比空（无助）')
        if type_effects:
            self._add_rule(96, f'旬空{kongwang}逐类推：{"，".join(type_effects)}')

    def _check_rule_97(self, sanchuan: List[str], ri_gan: str = ''):
        """第97法: 所筮不入仍凭类
        类神不在六处仍可类推——断课方法论。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        # 检查三传中是否缺少日干主要六亲
        gan_wx = GAN_WUXING.get(ri_gan, '')
        if not gan_wx:
            return
        has_parent = any(_is_gan_parent(ri_gan, z) for z in sanchuan)
        has_wealth = any(_is_gan_wealth(ri_gan, z) for z in sanchuan)
        has_ghost = any(_is_gan_ghost(ri_gan, z) for z in sanchuan)
        if not has_parent and not has_wealth and not has_ghost:
            self._add_rule(97, '三传中主要类神不显，宜凭类推理，所筮不入仍凭类')

    def _check_rule_98(self):
        """第98法: 非占现类勿言之
        不可妄言不相关之类神——断课方法论。
        ⚠️ 已停用（2026-08-15 憨爷拍板：这句以后一律不用，直接 return 不输出）。
        """
        return

    def _check_rule_99(self, ri_gan: str, season: str = ''):
        """第99法: 常问不应逢吉象
        吉泰课常人占致灾咎——吉课利贵人不利小人。
        """
        if not ri_gan:
            return
        # 当日干不当令时（衰），遇到多处吉象反而为忌
        if season:
            season_wx = SEASON_WANG.get(season, '')
            gan_wx = GAN_WUXING.get(ri_gan, '')
            if season_wx and gan_wx and season_wx == gan_wx:
                # 日干当令旺相，不需此法
                return
        # 日干不当令，检查是否已检测到多条吉象法条
        ji_rules = [r for r in self.detected_rules if r.get('stock_signal') == '涨']
        if len(ji_rules) >= 3:
            self._add_rule(99, f'日干{ri_gan}不当令，却逢多条吉象({",".join(r["name"] for r in ji_rules)})，常问不应逢吉象')

    def _check_rule_100(self, sanchuan: List[str], ri_gan: str = ''):
        """第100法: 已灾凶逃返无疑
        已见灾后占得凶卦可消除——以凶制凶。
        """
        if len(sanchuan) != 3:
            return
        xiong_rules = [r for r in self.detected_rules if r.get('stock_signal') == '跌']
        if len(xiong_rules) >= 4:
            self._add_rule(100, f'已检测{len(xiong_rules)}条凶象法条，若已见灾后占得，可消灾；若未见灾占得，当防病讼。已灾凶逃返无疑')

    def _check_rule_34(self, sanchuan: List[str], ri_gan: str):
        """第34法: 苦去甘来乐里悲
        苦去甘来：末传克初传（制鬼解害），且末传为日干长生位（转生）（通解中L5564"戊午日末申克初寅，申为戊土长生"）。
        乐里生忧：先各有长生之意，后递互盗气。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
        cs = _gan_wx_changsheng(ri_gan)   # 日干五行长生位（土双位 tuple）
        # 苦去甘来: 初传克干(鬼), 末传克初传(制鬼) 且 末传=日干长生位(转生)
        if _is_gan_ghost(ri_gan, chu) and _zhi_ke_zhi(mo, chu) and cs and mo in cs:
            self._add_rule(34, f'初传{chu}克干为害，末传{mo}克初解害又为日干长生，苦去甘来')
            return
        # 乐里生忧: 初生中生末(递相生), 末脱干(递互盗)
        if _zhi_sheng_zhi(chu, zhong) and _zhi_sheng_zhi(zhong, mo) and _is_gan_child(ri_gan, mo):
            self._add_rule(34, f'初{chu}生中{zhong}生末{mo}递相生，末传脱干，乐里生忧')

    def _check_rule_37(self, sanchuan: List[str], ri_gan: str):
        """第37法: 末助初兮三等论
        一末助初生日干；二末助初克日干；三末助初作日财。
        """
        if len(sanchuan) != 3 or not ri_gan:
            return
        chu, mo = sanchuan[0], sanchuan[2]
        # 末助初 = 末生初
        if not _zhi_sheng_zhi(mo, chu):
            return
        # 一: 初生干
        if _is_gan_parent(ri_gan, chu):
            self._add_rule(37, f'末传{mo}生初传{chu}生日干{ri_gan}，末助初生干，有人暗中推荐')
            return
        # 二: 初克干(鬼)
        if _is_gan_ghost(ri_gan, chu):
            self._add_rule(37, f'末传{mo}生初传{chu}克日干{ri_gan}，末助初克干，有教唆词讼之人')
            return
        # 三: 初为干财
        if _is_gan_wealth(ri_gan, chu):
            self._add_rule(37, f'末传{mo}生初传{chu}为日干{ri_gan}之财，末助初作财，暗有人以财相助')

    def _check_rule_38(self, sanchuan: List[str], ganzhi: str, tian_jiang: Optional[Dict] = None, tiandi_pan: Optional[Dict] = None):
        """第38法: 闭口卦体两般推
        ① 地盘旬首上神乘玄武（闭口卦根本）；② 旬尾加旬首发用更值初末六合（气塞于中）（通解中L5911）。
        """
        if len(sanchuan) != 3 or not ganzhi:
            return
        xun_shou = get_xun_shou(ganzhi)
        xun_wei = get_xun_wei(ganzhi)
        if not xun_shou or not xun_wei:
            return
        shou_zhi = xun_shou[1] if len(xun_shou) > 1 else ''
        wei_zhi = xun_wei[1] if len(xun_wei) > 1 else ''
        if not shou_zhi or not wei_zhi:
            return
        # ① 地盘旬首上神乘玄武
        if tiandi_pan and tian_jiang:
            shou_shang = tiandi_pan.get(shou_zhi, '')  # 天盘加临地盘旬首
            if shou_shang and tian_jiang.get(shou_shang, '') == '玄武':
                self._add_rule(38, f'地盘旬首{shou_zhi}上神{shou_shang}乘玄武，闭口卦')
                return
        # ② 旬尾加旬首发用 + 初末六合（气塞于中）
        wei_jia_shou = bool(tiandi_pan) and tiandi_pan.get(shou_zhi, '') == wei_zhi  # 天盘旬尾加地盘旬首
        chu_mo_he = LIUHE.get(sanchuan[0], '') == sanchuan[2]
        if sanchuan[0] == wei_zhi and wei_jia_shou and chu_mo_he:
            self._add_rule(38, f'旬尾{wei_zhi}加旬首{shou_zhi}发用且初末六合，闭口卦气塞于中')
            return
        # 【BUG-FIX 2026-08-18】删除原"兜底：旬尾发用即闭口卦"——无古籍依据
        # （闭口卦正解为地盘旬首上神乘玄武，或旬尾加旬首发用，二者均已在上方判定；
        # 仅"初传为旬尾"不成闭口卦，属编造判据）。

    # === Batch4: 贵人天将系列 ===

    def _check_rule_3(self, ri_gan: str, gan_shang: str, is_day: bool = True):
        """第3法: 帘幕贵人高甲第
        昼占得夜贵、夜占得昼贵为帘幕官，临日干上（或年命上）主科名高中（通解中L3974）。
        """
        if not ri_gan or not gan_shang:
            return
        gui = GUIREN_MAP.get(ri_gan)
        if not gui:
            return
        zhou_gui, ye_gui = gui
        lian_mu = ye_gui if is_day else zhou_gui  # 昼占夜贵、夜占昼贵
        if gan_shang == lian_mu:
            self._add_rule(3, f'{"昼" if is_day else "夜"}占帘幕贵人{lian_mu}临干上，主科名高中')

    def _check_rule_4(self, ri_gan: str, gan_shang: str, tian_jiang: Optional[Dict] = None):
        """第4法: 催官使者赴官期
        日鬼乘白虎加临日干：干上神为日鬼（官鬼爻），且所乘天将为白虎，名催官使者。
        """
        if not ri_gan or not gan_shang:
            return
        if not _is_gan_ghost(ri_gan, gan_shang):
            return
        jiang = (tian_jiang or {}).get(gan_shang, '') or (tian_jiang or {}).get('干上', '')
        if jiang == '白虎':
            self._add_rule(4, f'干上{gan_shang}为日鬼（官鬼）乘白虎，催官使者，必催速赴任')

    def _check_rule_39(self, yuejiang: str, tian_jiang: Optional[Dict] = None):
        """第39法: 太阳照武宜擒贼
        月将（太阳）临玄武上：月将天盘支所乘天将为玄武，占贼必败。
        """
        if not tian_jiang or not yuejiang:
            return
        yj = yuejiang.replace('将', '').strip()
        if tian_jiang.get(yj) == '玄武':
            self._add_rule(39, f'月将{yj}（太阳）照临玄武，太阳照武，宜擒贼')

    def _check_rule_40(self, gan_shang: str, zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第40法: 后合占婚岂用媒
        干上乘天后、支上乘六合，主私情婚事。
        """
        if not tian_jiang:
            return
        gan_jiang = tian_jiang.get(gan_shang, '') or tian_jiang.get('干上', '')
        zhi_jiang = tian_jiang.get(zhi_shang, '') or tian_jiang.get('支上', '')
        if gan_jiang == '天后' and zhi_jiang == '六合':
            self._add_rule(40, '干上乘天后、支上乘六合，后合占婚岂用媒')

    def _check_rule_41(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str):
        """第41法: 富贵干支逢禄马
        干上有支驿马，支上有干禄神，名真富贵卦。
        """
        if not ri_gan or not ri_zhi or not gan_shang or not zhi_shang:
            return
        yima = YIMA.get(ri_zhi, '')
        lushen = LU_SHEN.get(ri_gan, '')
        if yima and lushen and gan_shang == yima and zhi_shang == lushen:
            self._add_rule(41, f'干上{gan_shang}为支驿马，支上{zhi_shang}为干禄神，富贵干支逢禄马')

    def _check_rule_42(self, sanchuan: List[str], ganzhi: str):
        """第42法: 尊崇传内遇三奇
        三传全遇旬三奇（甲戊庚/乙丙丁）。
        """
        if len(sanchuan) != 3 or not ganzhi:
            return
        xun_shou = get_xun_shou(ganzhi)
        if not xun_shou:
            return
        gan_map = XUN_GAN_MAP.get(xun_shou)
        if not gan_map:
            return
        gans = [gan_map.get(z, '') for z in sanchuan]
        if '' in gans:
            return
        gan_set = set(gans)
        if gan_set == {'甲', '戊', '庚'}:
            self._add_rule(42, f'三传{sanchuan}旬干{gans}遇甲戊庚三奇，尊崇传内遇三奇')
        elif gan_set == {'乙', '丙', '丁'}:
            self._add_rule(42, f'三传{sanchuan}旬干{gans}遇乙丙丁三奇，尊崇传内遇三奇')

    def _check_rule_43(self, ri_gan: str, sanchuan: List[str], gan_shang: str,
                       zhi_shang: str, tian_jiang: Optional[Dict] = None):
        """第43法: 害贵讼直作曲断
        贵人与六害相逢，占讼理直而致曲断。
        """
        if not ri_gan or not tian_jiang:
            return
        all_zhi = [z for z in list(sanchuan) + [gan_shang, zhi_shang] if z]
        for gui_zhi, jiang in tian_jiang.items():
            if jiang == '贵人':
                for other_zhi in all_zhi:
                    if other_zhi != gui_zhi and LIUHAI.get(other_zhi, '') == gui_zhi:
                        self._add_rule(43, f'贵人乘{gui_zhi}，与{other_zhi}相害，害贵讼直作曲断')
                        return

    def _check_rule_44(self, ri_gan: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, si_ke_info=None):
        """第44法: 课传俱贵转无依
        四课三传皆是昼夜贵人，遍地贵人反无依。
        """
        if not ri_gan:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        zhou_gui, ye_gui = gui_ren
        sike_shang = _extract_sike_shang(si_ke_info)
        all_zhi = [z for z in list(sanchuan) + [gan_shang, zhi_shang] + sike_shang if z]
        all_zhi = list(dict.fromkeys(all_zhi))  # 去重
        if len(all_zhi) < 5:
            return
        if all(z in (zhou_gui, ye_gui) for z in all_zhi):
            self._add_rule(44, f'六处{all_zhi}皆为贵人（昼{zhou_gui}夜{ye_gui}），课传俱贵转无依')

    def _check_rule_45(self, ri_gan: str, sanchuan: List[str], gan_shang: str, zhi_shang: str, si_ke_info=None):
        """第45法: 昼夜贵加求两贵
        六处有旦暮天乙相加，告贵求事必涉两贵人。
        """
        if not ri_gan:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        zhou_gui, ye_gui = gui_ren
        sike_shang = _extract_sike_shang(si_ke_info)
        all_zhi = [z for z in list(sanchuan) + [gan_shang, zhi_shang] + sike_shang if z]
        has_zhou = zhou_gui in all_zhi
        has_ye = ye_gui in all_zhi
        if has_zhou and has_ye:
            self._add_rule(45, f'六处见昼贵{zhou_gui}与夜贵{ye_gui}，昼夜贵加求两贵')

    def _check_rule_46(self, ri_gan: str, ri_zhi: str, sanchuan: List[str], gan_shang: str, zhi_shang: str):
        """第46法: 贵人差迭事参差
        昼贵临于夜地，夜贵却临昼方，告贵求事多不归一。
        夜地=酉戌亥子丑寅, 昼方=卯辰巳午未申。
        检查干上(地盘=寄宫)和支上(地盘=日支)的贵人位置。
        """
        if not ri_gan:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        zhou_gui, ye_gui = gui_ren
        ye_di = {'酉', '戌', '亥', '子', '丑', '寅'}
        zhou_fang = {'卯', '辰', '巳', '午', '未', '申'}
        gan_di = GAN_JIGONG.get(ri_gan, '')
        zhou_on_ye = False
        ye_on_zhou = False
        # 干上: 天盘=gan_shang, 地盘=寄宫
        if gan_shang == zhou_gui and gan_di in ye_di:
            zhou_on_ye = True
        if gan_shang == ye_gui and gan_di in zhou_fang:
            ye_on_zhou = True
        # 支上: 天盘=zhi_shang, 地盘=ri_zhi
        if zhi_shang == zhou_gui and ri_zhi in ye_di:
            zhou_on_ye = True
        if zhi_shang == ye_gui and ri_zhi in zhou_fang:
            ye_on_zhou = True
        if zhou_on_ye and ye_on_zhou:
            self._add_rule(46, f'昼贵{zhou_gui}临夜地，夜贵{ye_gui}临昼方，贵人差迭事参差')

    def _check_rule_47(self, ri_gan: str, sanchuan: List[str], gan_shang: str,
                       zhi_shang: str, tian_jiang: Optional[Dict] = None,
                       ri_zhi: str = '', tiandi_pan: Optional[Dict] = None):
        """第47法: 贵虽在狱宜临干
        天乙贵人加临地盘辰戌上名入狱；乙辛日反名贵人临身（宜干投贵人）；辰戌日名贵人入宅非坐狱。
        """
        if not ri_gan or not tian_jiang or not tiandi_pan:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        # 贵人天盘支（天将"贵人"所乘的天盘支）
        gui_tianpan = [z for z, j in tian_jiang.items() if j == '贵人']
        if not gui_tianpan:
            return
        # 判断贵人天盘支是否加临地盘辰戌（坐狱）
        zai_yu = (tiandi_pan.get('辰', '') in gui_tianpan) or (tiandi_pan.get('戌', '') in gui_tianpan)
        if not zai_yu:
            return
        # 辰戌日 → 贵人入宅，非坐狱论
        if ri_zhi in ('辰', '戌'):
            return
        if ri_gan in ('乙', '辛'):
            self._add_rule(47, f'{ri_gan}日贵人坐地盘辰戌，名贵人临身，宜干投贵人周全成事')
        else:
            self._add_rule(47, f'天乙贵人坐地盘辰戌，天乙入狱，宜私谋阴祷')

    def _check_rule_48(self, ri_gan: str, gan_shang: str, tian_jiang: Optional[Dict] = None):
        """第48法: 鬼乘天乙乃神祗
        日鬼乘贵人临身，不可作鬼祟看，乃神祗为害。
        """
        if not ri_gan or not gan_shang or not tian_jiang:
            return
        gan_jiang = tian_jiang.get(gan_shang, '') or tian_jiang.get('干上', '')
        if gan_jiang == '贵人' and _is_gan_ghost(ri_gan, gan_shang):
            self._add_rule(48, f'干上{gan_shang}为日鬼乘贵人，鬼乘天乙乃神祗为害')

    def _check_rule_49(self, ri_gan: str, ri_zhi: str, sanchuan: List[str], gan_shang: str, zhi_shang: str):
        """第49法: 两贵受克难干贵
        昼夜贵人皆立受克之方，不可告贵用事。
        检查贵人地支所在位置的地盘是否克之。
        """
        if not ri_gan:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        zhou_gui, ye_gui = gui_ren
        # 构建位置→(天盘地支, 地盘地支)映射
        pos_info = {}
        if gan_shang:
            pos_info['干上'] = (gan_shang, GAN_JIGONG.get(ri_gan, ''))
        if zhi_shang:
            pos_info['支上'] = (zhi_shang, ri_zhi)  # 支上: 地盘=日支
        for i, key in enumerate(['初传', '中传', '末传']):
            if i < len(sanchuan) and sanchuan[i]:
                pos_info[key] = (sanchuan[i], '')  # 地盘未知
        zhou_ked = False
        ye_ked = False
        for pos, (tian_pan, di_pan) in pos_info.items():
            if not di_pan:
                continue
            if tian_pan == zhou_gui and _zhi_ke_zhi(di_pan, zhou_gui):
                zhou_ked = True
            if tian_pan == ye_gui and _zhi_ke_zhi(di_pan, ye_gui):
                ye_ked = True
        if zhou_ked and ye_ked:
            self._add_rule(49, f'昼贵{zhou_gui}与夜贵{ye_gui}皆立受克之方，两贵受克难干贵')

    def _check_rule_50(self, ri_gan: str, sanchuan: List[str], gan_shang: str,
                       zhi_shang: str, kongwang: Tuple[str, str]):
        """第50法: 二贵皆空虚喜期
        昼夜贵人皆空亡，干投贵人后被人搀越。
        """
        if not ri_gan or not kongwang or not kongwang[0]:
            return
        gui_ren = GUIREN_MAP.get(ri_gan)
        if not gui_ren:
            return
        zhou_gui, ye_gui = gui_ren
        # 贵人地支在旬空即为空亡
        zhou_kong = zhou_gui in kongwang
        ye_kong = ye_gui in kongwang
        if zhou_kong and ye_kong:
            self._add_rule(50, f'昼贵{zhou_gui}与夜贵{ye_gui}皆空亡{kongwang}，二贵皆空虚喜期')

    def _check_rule_85(self, sanchuan: List[str], tian_jiang: Optional[Dict] = None,
                       tiandi_pan: Optional[Dict] = None):
        """第85法: 初遭夹克不由己
        初传坐于克方又被天将所伤，名夹克，身不由己。
        检测：天将五行克初传 + 地盘五行克初传（双重夹克为真夹克）。
        """
        if len(sanchuan) != 3 or not tian_jiang:
            return
        chu = sanchuan[0]
        jiang = tian_jiang.get(chu, '') or tian_jiang.get('初传', '')
        if not jiang:
            return
        jiang_wx = TIANJIANG_WUXING.get(jiang, '')
        zhi_wx = ZHI_WUXING.get(chu, '')

        tian_jiang_ke = False
        dipan_ke = False
        dipan_zhi = ''

        # 1. 天将克初传
        if jiang_wx and zhi_wx and _wuxing_ke(jiang_wx, zhi_wx):
            tian_jiang_ke = True

        # 2. 地盘克初传（从天地盘中查找初传所在的地盘支）
        if tiandi_pan:
            for di_zhi, tian_zhi in tiandi_pan.items():
                if tian_zhi == chu:
                    dipan_zhi = di_zhi
                    di_wx = ZHI_WUXING.get(di_zhi, '')
                    if di_wx and zhi_wx and _wuxing_ke(di_wx, zhi_wx):
                        dipan_ke = True
                    break

        if tian_jiang_ke and dipan_ke:
            di_wx = ZHI_WUXING.get(dipan_zhi, '')
            self._add_rule(85,
                f'初传{chu}({zhi_wx})被天将{jiang}({jiang_wx})+地盘{dipan_zhi}({di_wx})双重夹克，不由己',
                signal_override='跌', conf_override='高')
        elif tian_jiang_ke:
            self._add_rule(85,
                f'初传{chu}({zhi_wx})被天将{jiang}({jiang_wx})克，初遭夹克不由己')

    def _check_rule_86(self, sanchuan: List[str], gan_shang: str, zhi_shang: str,
                       tian_jiang: Optional[Dict] = None):
        """第86法: 将逢内战所谋危
        天将五行克所乘地支五行，凡用事将成合被人搅扰。
        【BUG-FIX 2026-08-18】tian_jiang 键为地支（如 {'子':'贵人'}），原按
        '初传'/'中传' 等位置名取 → 永不匹配。现按位置→地支→天将取值。
        """
        if not tian_jiang:
            return
        pos_zhi = {}
        if len(sanchuan) >= 1:
            pos_zhi['初传'] = sanchuan[0]
        if len(sanchuan) >= 2:
            pos_zhi['中传'] = sanchuan[1]
        if len(sanchuan) >= 3:
            pos_zhi['末传'] = sanchuan[2]
        if gan_shang:
            pos_zhi['干上'] = gan_shang
        if zhi_shang:
            pos_zhi['支上'] = zhi_shang
        for pos, zhi in pos_zhi.items():
            if not zhi:
                continue
            # 兼容两种键格式：{地支: 天将}（tianjiang_map）或 {位置名: 天将}（tianjiang_detail）
            jiang = tian_jiang.get(zhi, '') or tian_jiang.get(pos, '')
            if not jiang:
                continue
            jiang_wx = TIANJIANG_WUXING.get(jiang, '')
            zhi_wx = ZHI_WUXING.get(zhi, '')
            if jiang_wx and zhi_wx and _wuxing_ke(jiang_wx, zhi_wx):
                self._add_rule(86, f'{pos}天将{jiang}({jiang_wx})克地支{zhi}({zhi_wx})，将逢内战所谋危')
                return

    def _check_rule_87(self, ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str, tiandi_pan: Optional[Dict] = None):
        """第87法: 人宅坐墓甘招晦
        天盘干（干寄宫）坐地盘干墓、天盘支（日支）坐地盘支墓（通解中L7753"壬寅日亥加辰、寅加未"）。
        """
        if not ri_gan or not ri_zhi or not tiandi_pan:
            return
        gan_ji = GAN_JIGONG.get(ri_gan, '')
        if not gan_ji:
            return
        gan_mu = _get_zhi_mu(gan_ji)   # 干寄宫（=干）之墓
        zhi_mu = _get_zhi_mu(ri_zhi)   # 支之墓
        if gan_mu and zhi_mu and tiandi_pan.get(gan_mu, '') == gan_ji and tiandi_pan.get(zhi_mu, '') == ri_zhi:
            self._add_rule(87, f'天盘干{gan_ji}坐地盘干墓{gan_mu}、天盘支{ri_zhi}坐地盘支墓{zhi_mu}，人宅坐墓甘招晦')

    # === 补全5条独立方法（逻辑原在组合方法中，现独立化） ===

    def _check_rule_20(self, ri_gan: str, yuejiang: str):
        """第20法: 胎财死气损胎推
        胎神作月内死气，妇孕不育。
        """
        if not ri_gan or not yuejiang:
            return
        tai = _gan_wx_tai(ri_gan)   # 日干五行胎位（土双位 tuple）
        if not tai:
            return
        si_qi = _get_si_qi(yuejiang)
        if si_qi and si_qi in tai:
            self._add_rule(20, f'日干{ri_gan}胎神{si_qi}为月令死气，胎财死气损胎推')

    def _check_rule_26(self, ri_gan: str, ganzhi: str, sanchuan: List[str] = None,
                        gan_shang: str = '', zhi_shang: str = '', ben_ming_zhi: str = ''):
        """第26法: 水日逢丁财动之
        壬癸日三传/年命/日辰六处逢旬内丁神，必主财动及远方寄财物。
        """
        if not ri_gan or ri_gan not in ('壬', '癸') or not ganzhi:
            return
        ding_shen = get_ding_shen(ganzhi)
        if not ding_shen:
            return
        positions = []
        if sanchuan:
            for i, z in enumerate(sanchuan):
                if z == ding_shen:
                    positions.append(['初传', '中传', '末传'][i])
        if gan_shang and gan_shang == ding_shen:
            positions.append('干上')
        if zhi_shang and zhi_shang == ding_shen:
            positions.append('支上')
        if ben_ming_zhi and ben_ming_zhi == ding_shen:
            positions.append('本命')
        if positions:
            self._add_rule(26, f'水日{ri_gan}逢丁神{ding_shen}在{"、".join(positions)}，财动之')

    def _check_rule_30(self, sanchuan: List[str], ri_gan: str, ri_zhi: str):
        """第30法: 屋宅宽广致人衰
        三传窃盗日干反生支辰，宅不容人居止，人口日衰。
        """
        if len(sanchuan) != 3 or not ri_gan or not ri_zhi:
            return
        if all(_is_gan_child(ri_gan, z) for z in sanchuan):
            if any(_zhi_sheng_zhi(z, ri_zhi) for z in sanchuan):
                self._add_rule(30, f'三传{sanchuan}脱日干{ri_gan}生支辰{ri_zhi}，屋宅宽广致人衰')

    def _check_rule_84(self, sanchuan: List[str], ri_gan: str = '', ri_zhi: str = '',
                        gan_shang: str = '', zhi_shang: str = ''):
        """第84法: 合中犯杀蜜中砒
        三传三合局，干支上神见刑/害/冲者，三合犯杀。
        """
        if len(sanchuan) != 3:
            return
        he_ju = _is_sanhe_ju(sanchuan)
        if not he_ju:
            return
        if not gan_shang and not zhi_shang:
            return
        sha_info = SANHE_SHANG.get(he_ju, {})
        xing = sha_info.get('刑', '')
        hai = sha_info.get('害', '')
        chong = sha_info.get('冲', '')
        violations = []
        for label, s in [('干上', gan_shang), ('支上', zhi_shang)]:
            if not s:
                continue
            if s == xing:
                violations.append(f'{label}{s}为自刑')
            if s == chong:
                violations.append(f'{label}{s}为冲')
            # 【BUG-FIX 2026-08-18】害位判断：s == hai（局中神之害位）；
            # 原 `LIUHAI.get(s) == hai` 误把"s 的六害对象"当害位，反向错判。
            if s == hai:
                violations.append(f'{label}{s}为六害')
        if violations:
            self._add_rule(84, f'三传{sanchuan}为{he_ju}局，{"、".join(violations)}，合中犯杀蜜中砒')

    def _check_rule_90(self, sanchuan: List[str], kongwang: Tuple[str, str], ganzhi: str = ''):
        """第90法: 来去俱空岂动宜
        返吟卦三传皆落空亡（分旬），虽有动意实不动。
        """
        if not sanchuan or len(sanchuan) != 3:
            return
        is_fanyin = LIUCHONG.get(sanchuan[0], '') == sanchuan[2]
        if not is_fanyin:
            return
        fxk = get_fen_xun_kong(ganzhi) if ganzhi else None
        if not fxk:
            return
        ben, qian, hou, waihou = fxk['本旬'], fxk['前旬'], fxk['后旬'], fxk['外后旬']
        chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
        jinru = chu in ben and zhong in ben and mo in qian
        tuiru = chu in ben and zhong in hou and mo in waihou
        if jinru or tuiru:
            self._add_rule(90, f'返吟课三传{sanchuan}皆落空亡（分旬），来去俱空岂动宜')


# ============ 便捷函数 ============
def detect_bifa(sanchuan_dizhi: List[str],
                ri_gan: str = '',
                ri_zhi: str = '',
                ganzhi: str = '',
                yuejiang: str = '',
                season: str = '',
                gan_shang_shen: str = '',
                zhi_shang_shen: str = '',
                **kwargs) -> Dict:
    """便捷检测函数"""
    detector = BiFaDetector()
    return detector.detect(
        sanchuan_dizhi=sanchuan_dizhi,
        ri_gan=ri_gan,
        ri_zhi=ri_zhi,
        ganzhi=ganzhi,
        yuejiang=yuejiang,
        season=season,
        gan_shang_shen=gan_shang_shen,
        zhi_shang_shen=zhi_shang_shen,
        **kwargs
    )


def get_bifa_summary(result: Dict) -> str:
    """获取毕法赋检测摘要"""
    rules = result.get('匹配法条', [])
    if not rules:
        return '未检测到毕法赋法条'
    return f'毕法赋: {"、".join(rules)}'
