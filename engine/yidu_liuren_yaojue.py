#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日要诀 — 完整规则引擎 (v2.0)
========================================
提取自张九仪《仪度六壬选日要诀》(李佳明注)

实现:
  A. 斗首五行规则（已实现→增强）
     1. 二十四山斗首五行（元辰/武财/廉子/贪官/破鬼）
     2. 六十日相替定局（五虎遁）
     3. 六相六替自动判断
     4. 四柱透元辰检查
     5. 三元三武一廉第一吉课检测
     6. 凶宜在外吉宜在内规则

  B. 拱类课格检测（新增）
     7.  拱干格 — 初末传拱天干
     8.  两贵引从格 — 两贵拱干
     9.  拱支格 — 初末传拱支
     10. 干支拱贵格 — 干/支夹拱贵人
     11. 干支拱日禄格 — 干/支夹拱禄神
     12. 三合拱贵格 — 三传三合拱贵人
     13. 三合拱禄格 — 三传三合拱禄神
     14. 三合拱马格 — 三传三合拱驿马

  C. 到山到向增强（新增）
     15. 贵人到山到向检测
     16. 禄到山到向检测
     17. 马到山到向检测
     18. 活马活禄检测（三传中发传）

  D. 高级课格（新增）
     19. 朝天格 — 贵人加干
     20. 归垣格 — 贵人归垣
     21. 罗纹格 — 干支互生
     22. 龙德课 — 太岁月将乘贵人发用

  E. 补元规则（新增）
     23. 以元补元
     24. 以武补元
     25. 以廉补元
     26. 以贪破补元（需到山到向发传）
"""

from typing import Dict, List, Tuple, Optional, Set
from datetime import date

# ── A. 斗首五行基础数据 ──

# 二十四山 → 斗首五行（憨爷 2026-08-13 拍板：癸丑火、乙辰金、辛戌土；与斗首歌诀一致）
SHAN_DOUSHO: Dict[str, str] = {
    '壬':'土','子':'土',   # 壬子土
    '癸':'火','丑':'火',   # 癸丑火（原误标土，已修正）
    '艮':'木','寅':'木',   # 艮寅木
    '甲':'水','卯':'水',   # 甲卯水
    '乙':'金','辰':'金',   # 乙辰金
    '巽':'土','巳':'土',   # 巽巳土
    '丙':'火','午':'火',   # 丙午火
    '丁':'木','未':'木',   # 丁未木
    '坤':'水','申':'水',   # 坤申水
    '庚':'金','酉':'金',   # 庚酉金
    '辛':'土','戌':'土',   # 辛戌土
    '乾':'火','亥':'火',   # 乾亥火
}

# 斗首五行 → 化气（天干合）
DOUSHO_WX_TO_HUAQI: Dict[str, str] = {
    '土': '甲己', '金': '乙庚', '水': '丙辛', '木': '丁壬', '火': '戊癸',
}

# 化气合 → 五行
HUAQI_TO_WX: Dict[str, str] = {
    '甲己': '土', '乙庚': '金', '丙辛': '水', '丁壬': '木', '戊癸': '火',
}

# 五虎遁（正月建寅）
WUHU_DUN: Dict[str, str] = {
    '甲己': '丙寅', '乙庚': '戊寅', '丙辛': '庚寅',
    '丁壬': '壬寅', '戊癸': '甲寅',
}

# 十干 → 五虎遁键
GAN_TO_HU_KEY: Dict[str, str] = {}
for k in WUHU_DUN:
    for c in k:
        GAN_TO_HU_KEY[c] = k

# 六十甲子
GAN_LIST: List[str] = list('甲乙丙丁戊己庚辛壬癸')
ZHI_LIST: List[str] = list('子丑寅卯辰巳午未申酉戌亥')
JIAZI_60: List[str] = [GAN_LIST[i%10] + ZHI_LIST[i%12] for i in range(60)]

# 十天干禄神
LU: Dict[str, str] = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
    '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子',
}

# 十二地支驿马
YIMA: Dict[str, str] = {
    '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥',
}

def get_yima(ri_zhi: str) -> str:
    """根据日支获取驿马"""
    for key, val in YIMA.items():
        if ri_zhi in key:
            return val
    return ''

# 十干寄宫
JIGONG: Dict[str, str] = {
    '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
    '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑',
}

# 三合局
SANHE: Dict[str, List[str]] = {
    '申子辰': ['申','子','辰'], '亥卯未': ['亥','卯','未'],
    '寅午戌': ['寅','午','戌'], '巳酉丑': ['巳','酉','丑'],
}

# 地支→三合局
ZHI_TO_SANHE: Dict[str, str] = {}
for k, v in SANHE.items():
    for z in v:
        ZHI_TO_SANHE[z] = k

# 十二长生宫序
SHENGONG_ORDER: List[str] = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养']

# 六相 / 六替
SIX_XIANG: Set[str] = {'长生','冠带','临官','帝旺','胎','养'}
SIX_TI: Set[str] = {'沐浴','衰','病','死','墓','绝'}

# 二十四山 → 山家映射 + 向首（二十四山对宫，憨爷 2026-08-14 拍板口径）
# 单一数据源：引用 engine/daliuren_luma_guiren.py 的 DaLiuRenLuMaGuiRen 类属性（2026-08-17 理顺统一，
# 原本地两份 dict 与 luma 重复，改一处忘另一处会错位；现只读引用，内容逐项比对 24 山 0 差异）
from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen as _LRM

SHAN_JIA_MAP: Dict[str, str] = _LRM.SHAN_JIA_MAP
XIANG_SHOU: Dict[str, str] = _LRM.XIANG_SHOU_MAP

# ── A1. 六十日相替定局（用五虎遁） ──

def get_60day_shengong(ri_gan: str) -> Dict[str, str]:
    """
    六十日相替定局：以五虎遁正月(寅)为长生
    甲己日起丙寅长生 → 丁卯沐浴 → ... 顺排12宫
    """
    hu_key = GAN_TO_HU_KEY.get(ri_gan, '甲己')
    yinyue = WUHU_DUN.get(hu_key, '丙寅')
    start_idx = JIAZI_60.index(yinyue)
    result = {}
    for i in range(12):
        gz = JIAZI_60[(start_idx + i) % 60]
        zhi = gz[1]
        result[zhi] = SHENGONG_ORDER[i]
    return result


def check_liuxiang_liuti(ganzhi: str, ri_gan: str) -> dict:
    """检查某干支在六十日相替定局中是六相还是六替"""
    zhi = ganzhi[1] if len(ganzhi) > 1 else ''
    sg = get_60day_shengong(ri_gan)
    state = sg.get(zhi, '')
    return {
        'zhi': zhi, 'state': state,
        'is_xiang': state in SIX_XIANG,
        'is_ti': state in SIX_TI,
        'type': '六相' if state in SIX_XIANG else ('六替' if state in SIX_TI else '?'),
    }


# ── A2. 二十四山完整斗首映射表 ──
# 取自《仪度六壬选日要诀》原文十二山斗首五行表
# 每山有特定的天干→类别配对（非简单化气推导！）

# 每山的天干→类别映射（5天干对应5类别）
# ⚠️ 废弃（2026-08-13 憨爷裁决）：此固定配对表与《仪度六壬选日要诀》权威口径矛盾
# （元辰=同我者，化气推导）。艮/寅/甲/卯四山存在抄录错位（如艮山丙≠元辰）。
# 保留仅供历史对照，实际判定请用 _build_doushou_shan_map 化气推导。
_SHAN_GAN_CATEGORY: Dict[str, Dict[str, str]] = {
    # 壬子土: 丙武, 戊贪, 庚廉, 壬破, 甲元
    '壬': {'丙':'武财','戊':'贪官','庚':'廉子','壬':'破鬼','甲':'元辰'},
    '子': {'丙':'武财','戊':'贪官','庚':'廉子','壬':'破鬼','甲':'元辰'},
    # 癸丑土: 丁贪, 己廉, 辛破, 癸元, 乙武
    '癸': {'丁':'贪官','己':'廉子','辛':'破鬼','癸':'元辰','乙':'武财'},
    '丑': {'丁':'贪官','己':'廉子','辛':'破鬼','癸':'元辰','乙':'武财'},
    # 艮寅木: 戊武, 庚贪, 壬廉, 甲破, 丙元
    '艮': {'戊':'武财','庚':'贪官','壬':'廉子','甲':'破鬼','丙':'元辰'},
    '寅': {'戊':'武财','庚':'贪官','壬':'廉子','甲':'破鬼','丙':'元辰'},
    # 甲卯水: 己贪, 辛廉, 癸破, 乙元, 丁武
    '甲': {'己':'贪官','辛':'廉子','癸':'破鬼','乙':'元辰','丁':'武财'},
    '卯': {'己':'贪官','辛':'廉子','癸':'破鬼','乙':'元辰','丁':'武财'},
    # 乙辰金: 庚元, 壬武, 甲贪, 丙廉, 戊破
    '乙': {'庚':'元辰','壬':'武财','甲':'贪官','丙':'廉子','戊':'破鬼'},
    '辰': {'庚':'元辰','壬':'武财','甲':'贪官','丙':'廉子','戊':'破鬼'},
    # 巽巳土: 辛武, 癸贪, 乙廉, 丁破, 己元
    '巽': {'辛':'武财','癸':'贪官','乙':'廉子','丁':'破鬼','己':'元辰'},
    '巳': {'辛':'武财','癸':'贪官','乙':'廉子','丁':'破鬼','己':'元辰'},
    # 丙午火: 壬贪, 甲廉, 丙破, 戊元, 庚武
    '丙': {'壬':'贪官','甲':'廉子','丙':'破鬼','戊':'元辰','庚':'武财'},
    '午': {'壬':'贪官','甲':'廉子','丙':'破鬼','戊':'元辰','庚':'武财'},
    # 丁未木: 癸廉, 乙破, 丁元, 己武, 辛贪
    '丁': {'癸':'廉子','乙':'破鬼','丁':'元辰','己':'武财','辛':'贪官'},
    '未': {'癸':'廉子','乙':'破鬼','丁':'元辰','己':'武财','辛':'贪官'},
    # 坤申水: 甲破, 丙元, 戊武, 庚贪, 壬廉
    '坤': {'甲':'破鬼','丙':'元辰','戊':'武财','庚':'贪官','壬':'廉子'},
    '申': {'甲':'破鬼','丙':'元辰','戊':'武财','庚':'贪官','壬':'廉子'},
    # 庚酉金: 乙元, 丁武, 己贪, 辛廉, 癸破
    '庚': {'乙':'元辰','丁':'武财','己':'贪官','辛':'廉子','癸':'破鬼'},
    '酉': {'乙':'元辰','丁':'武财','己':'贪官','辛':'廉子','癸':'破鬼'},
    # 辛戌土: 丙武, 戊贪, 庚廉, 壬破, 甲元
    '辛': {'丙':'武财','戊':'贪官','庚':'廉子','壬':'破鬼','甲':'元辰'},
    '戌': {'丙':'武财','戊':'贪官','庚':'廉子','壬':'破鬼','甲':'元辰'},
    # 乾亥火: 丁贪, 己廉, 辛破, 癸元, 乙武
    '乾': {'丁':'贪官','己':'廉子','辛':'破鬼','癸':'元辰','乙':'武财'},
    '亥': {'丁':'贪官','己':'廉子','辛':'破鬼','癸':'元辰','乙':'武财'},
}

# ── A3. 五星权威定义（《仪度六壬选日要诀》体系，山家为「我」）──
# 憨爷 2026-08-13 裁决：元辰=同我者（艮寅木元辰、甲卯水元辰），非固定天干配对！
# 元辰=同我 / 武财=我克 / 廉贞(廉子)=我生 / 贪官=生我 / 破鬼=克我
# 依据：六相六替之法步骤3 + LIUQIN_MAP + 知识库ZR_01_02/09_01/09_02实例
WX_SHENG: Dict[str, str] = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE: Dict[str, str] = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
_DOUSHOU_REL_MAP: Dict[str, str] = {
    '同我': '元辰', '我克': '武财', '我生': '廉贞', '生我': '贪官', '克我': '破鬼',
}

# 缓存：每山→完整60甲子映射
_shan_full_map_cache: Dict[str, Dict[str, str]] = {}


def _build_doushou_shan_map(shan: str) -> Dict[str, str]:
    """
    构建某山完整的60甲子斗首类别映射
    权威口径：天干化气五行与山家比较（同我=元辰/我克=武财/我生=廉贞/生我=贪官/克我=破鬼）
    （原 _SHAN_GAN_CATEGORY 固定配对表在艮/寅/甲/卯四山有抄录错误，已废弃改用推导）
    结果缓存以提高性能
    """
    if shan in _shan_full_map_cache:
        return _shan_full_map_cache[shan]

    shan_wx = SHAN_DOUSHO.get(shan, '土')

    result = {}
    for gan in GAN_LIST:
        hu_key = GAN_TO_HU_KEY.get(gan, '')
        hq_wx = HUAQI_TO_WX.get(hu_key, '')
        if not hq_wx:
            continue
        if hq_wx == shan_wx:
            rel = '同我'
        elif WX_SHENG.get(shan_wx) == hq_wx:
            rel = '我生'
        elif WX_SHENG.get(hq_wx) == shan_wx:
            rel = '生我'
        elif WX_KE.get(shan_wx) == hq_wx:
            rel = '我克'
        elif WX_KE.get(hq_wx) == shan_wx:
            rel = '克我'
        else:
            rel = ''
        cls = _DOUSHOU_REL_MAP.get(rel, '未知')
        for zhi in ZHI_LIST:
            gz = gan + zhi
            if gz in JIAZI_60:
                result[gz] = cls

    _shan_full_map_cache[shan] = result
    return result


def get_doushou_class(shan: str, ganzhi: str) -> str:
    """获取某干支在某山的斗首类别（化气推导口径）"""
    mapping = _build_doushou_shan_map(shan)
    return mapping.get(ganzhi, '未知')


def get_yuanchen_gans(shan: str) -> List[str]:
    """获取某山的元辰天干列表（元辰=同我者：化气五行与山家相同的天干）"""
    shan_wx = SHAN_DOUSHO.get(shan, '土')
    return list(DOUSHO_WX_TO_HUAQI.get(shan_wx, ''))


# ── A3. 四柱透元辰检查 ──

def check_sizhu_tou_yuanchen(year_pillar: str, month_pillar: str,
                              day_pillar: str, hour_pillar: str,
                              shan: str) -> dict:
    """
    检查四柱是否透元辰
    秘诀: "四柱必透一元辰。若不及透，必地支多元辰六相之支，此妙谛也"
    """
    pillars = {'年': year_pillar, '月': month_pillar, '日': day_pillar, '时': hour_pillar}
    
    # 使用24山映射获取每山的元辰天干
    yuan_chen_gans = get_yuanchen_gans(shan)
    
    result = {
        'has_yuanchen': False, 'yuanchen_pillars': [],
        'xiang_count': 0, 'ti_count': 0, 'recommendation': '',
        'pillar_details': {},
    }
    
    for label, pillar in pillars.items():
        gan = pillar[0]
        lt = check_liuxiang_liuti(pillar, day_pillar[0])
        result['pillar_details'][label] = {
            'pillar': pillar, 'is_yuanchen': gan in yuan_chen_gans,
            'liuxiang_liuti': lt
        }
        if gan in yuan_chen_gans:
            result['has_yuanchen'] = True
            result['yuanchen_pillars'].append(label)
        if lt['is_xiang']:
            result['xiang_count'] += 1
        elif lt['is_ti']:
            result['ti_count'] += 1
    
    if not result['has_yuanchen']:
        if result['xiang_count'] >= 2:
            result['recommendation'] = '⚠️ 无透元辰，但地支多六相，可勉强用'
        else:
            result['recommendation'] = '❌ 无透元辰且少六相，不宜用'
    else:
        result['recommendation'] = f'✅ 元辰透在{"/".join(result["yuanchen_pillars"])}柱'
    
    return result


# ── A4. 凶宜在外吉宜在内 ──

def check_jixiong_position(doushou_classes: Dict[str, str]) -> dict:
    """
    检查凶宜在外吉宜在内规则
    秘诀: "凶宜在外(年月), 吉宜在内(日时)"
    doushou_classes: {'年': '元辰'/'武财'...}
    """
    good = {'元辰','武财','廉子','廉贞'}  # 廉子=廉贞（同星异名，归一化）
    bad = {'贪官','破鬼'}
    
    result = {'is_ideal': False, 'warnings': [], 'score': 0}
    
    nian_yue_bad = doushou_classes.get('年','') in bad or doushou_classes.get('月','') in bad
    ri_shi_good = doushou_classes.get('日','') in good and doushou_classes.get('时','') in good
    ri_shi_bad = doushou_classes.get('日','') in bad or doushou_classes.get('时','') in bad
    
    if ri_shi_good:
        result['score'] += 10
        result['warnings'].append('✅ 吉在日时(内)')
    if nian_yue_bad:
        result['score'] += 5
        result['warnings'].append('✅ 凶在年月(外)')
    if ri_shi_bad:
        result['score'] -= 15
        result['warnings'].append('⚠️ 凶在日时(内) → 不利')
    if ri_shi_good and nian_yue_bad:
        result['is_ideal'] = True
        result['score'] += 5
        result['warnings'].append('✅ 凶在外吉在内 → 上吉格局')
    
    return result


# ── A5. 三元三武一廉检测 ──

def check_sanyuan_sanwu_yilian(year_class: str, month_class: str,
                                 day_class: str, hour_class: str) -> dict:
    """
    检测三元三武一廉第一吉课
    原文: "四柱合三元三武一廉之课，第一吉者也"
    """
    classes = {'年': year_class, '月': month_class, '日': day_class, '时': hour_class}
    yuanchen = sum(1 for c in classes.values() if c == '元辰')
    wucai = sum(1 for c in classes.values() if c == '武财')
    lianzi = sum(1 for c in classes.values() if c in ('廉子', '廉贞'))
    tanguan = sum(1 for c in classes.values() if c == '贪官')
    pogui = sum(1 for c in classes.values() if c == '破鬼')
    
    is_first_jike = False
    grade = ''
    
    # 第一吉课：三元一廉 or 三武一廉
    if (yuanchen == 3 and lianzi == 1) or (wucai == 3 and lianzi == 1):
        is_first_jike = True
        grade = '第一吉课'
    elif yuanchen == 4:
        grade = '四元大吉'
    elif wucai == 4:
        # 【2026-09-06】四武财与四元辰同为最高档（用户拍板"四元辰/四武财最吉"），
        #   原落到 wucai>=3 的"三武格局"，与四元大吉不对等。
        grade = '四武大吉'
    elif pogui == 1 and classes['年'] == '破鬼':
        # 【2026-09-06 破鬼把门（用户拍板）】破鬼独居年干=把门守户，反凶为吉，A档次优。
        #   注意：其余任何柱见破鬼仍按凶处理（见 return 的 has_xiong）。
        grade = '破鬼把门'
    elif yuanchen == 3 and wucai == 1:
        grade = '三元一武大吉'
    elif yuanchen >= 3:
        grade = '三元格局'
    elif wucai >= 3:
        grade = '三武格局'
    
    return {
        'is_first_jike': is_first_jike,
        'grade': grade,
        'yuanchen': yuanchen, 'wucai': wucai, 'lianzi': lianzi,
        'tanguan': tanguan, 'pogui': pogui,
        'has_xiong': tanguan > 0 or (pogui > 1 or (pogui == 1 and classes['年'] != '破鬼')),
    }


# ══════════════════════════════════════════════════════════════
# B. 拱类课格检测（新增核心功能）
# ══════════════════════════════════════════════════════════════

def _circular_between(target_idx: int, a_idx: int, b_idx: int) -> bool:
    """
    检查 target 是否在圆环上位于 a 和 b 之间的短弧内
    12地支环: 子=0, 丑=1, ..., 亥=11
    【BUG-FIX 2026-08-18】原实现仅判单方向，调用处 `A or B` 双向并集
    在圆环上恒真（target 必落在 a→b 或 b→a 之一）→ 拱格虚增+20分。
    现取短弧（跨度 ≤6），target 须落在 a、b 所夹的劣弧内才算拱。
    """
    if a_idx == b_idx or a_idx == target_idx or b_idx == target_idx:
        return False

    n = 12
    forward_dist = (b_idx - a_idx) % n
    if forward_dist > n // 2:
        # 长弧方向不构成"拱"，交换视角走短弧判定
        return _circular_between(target_idx, b_idx, a_idx)

    # 顺时针从a到b的短弧
    target_forward = (target_idx - a_idx) % n
    return 0 < target_forward < forward_dist


def check_gong_gan(sanchuan: dict, ri_gan: str) -> dict:
    """
    拱干格: 初末传拱天干
    条件: 初传居日干之前，末传居日干之后（或反之）
    主官职升擢，诸事最吉
    """
    if not sanchuan:
        return {'matched': False, 'name': '拱干格', 'level': '上吉'}
    
    chu = sanchuan.get('初传', '')
    mo = sanchuan.get('末传', '')
    if not chu or not mo:
        return {'matched': False, 'name': '拱干格', 'level': '上吉'}
    
    jigong = JIGONG.get(ri_gan, '')
    if not jigong:
        return {'matched': False, 'name': '拱干格', 'level': '上吉'}
    
    chu_idx = ZHI_LIST.index(chu) if chu in ZHI_LIST else -1
    mo_idx = ZHI_LIST.index(mo) if mo in ZHI_LIST else -1
    gan_idx = ZHI_LIST.index(jigong) if jigong in ZHI_LIST else -1
    
    if chu_idx < 0 or mo_idx < 0 or gan_idx < 0:
        return {'matched': False, 'name': '拱干格', 'level': '上吉'}
    
    matched = _circular_between(gan_idx, chu_idx, mo_idx) or _circular_between(gan_idx, mo_idx, chu_idx)
    
    return {
        'matched': matched,
        'name': '拱干格',
        'level': '上吉',
        'desc': f'初传{chu}、末传{mo}拱天干{ri_gan}（寄宫{jigong}）' if matched else '',
        'score': 88 if matched else 0,
    }


def check_lianggui_yincong(sanchuan: dict, ri_gan: str, guiren_zhi: List[str]) -> dict:
    """
    两贵引从格: 两贵拱干
    条件: 昼贵与夜贵分别在日干前后夹拱
    主上人提携
    """
    if not guiren_zhi or len(guiren_zhi) < 2:
        return {'matched': False, 'name': '两贵引从格', 'level': '上吉'}
    
    jigong = JIGONG.get(ri_gan, '')
    if not jigong:
        return {'matched': False, 'name': '两贵引从格', 'level': '上吉'}
    
    gan_idx = ZHI_LIST.index(jigong)
    
    # 使用有效的两个贵人
    valid_guiren = [g for g in guiren_zhi[:2] if g in ZHI_LIST]
    if len(valid_guiren) < 2:
        return {'matched': False, 'name': '两贵引从格', 'level': '上吉'}
    
    g1_idx = ZHI_LIST.index(valid_guiren[0])
    g2_idx = ZHI_LIST.index(valid_guiren[1])
    
    matched = _circular_between(gan_idx, g1_idx, g2_idx)
    
    return {
        'matched': matched,
        'name': '两贵引从格',
        'level': '上吉',
        'desc': f'两贵{valid_guiren[0]}、{valid_guiren[1]}拱天干{ri_gan}' if matched else '',
        'score': 90 if matched else 0,
    }


def check_gong_zhi(sanchuan: dict, ri_zhi: str) -> dict:
    """
    拱支格: 初末传拱地支
    条件: 初传居日支前，末传居日支后
    主家宅吉庆
    """
    if not sanchuan or ri_zhi not in ZHI_LIST:
        return {'matched': False, 'name': '拱支格', 'level': '吉'}
    
    chu = sanchuan.get('初传', '')
    mo = sanchuan.get('末传', '')
    if not chu or not mo or chu not in ZHI_LIST or mo not in ZHI_LIST:
        return {'matched': False, 'name': '拱支格', 'level': '吉'}
    
    chu_idx = ZHI_LIST.index(chu)
    mo_idx = ZHI_LIST.index(mo)
    zhi_idx = ZHI_LIST.index(ri_zhi)
    
    matched = _circular_between(zhi_idx, chu_idx, mo_idx) or _circular_between(zhi_idx, mo_idx, chu_idx)
    
    return {
        'matched': matched,
        'name': '拱支格',
        'level': '吉',
        'desc': f'初传{chu}、末传{mo}拱日支{ri_zhi}' if matched else '',
        'score': 80 if matched else 0,
    }


def check_ganzhi_gong_gui(ri_gan: str, ri_zhi: str, guiren_zhi: List[str]) -> dict:
    """
    干支拱贵格: 日干日支夹拱贵人
    条件: 贵人位于日干寄宫和日支之间
    宜告贵处事
    """
    jigong = JIGONG.get(ri_gan, '')
    if not jigong or ri_zhi not in ZHI_LIST:
        return {'matched': False, 'name': '干支拱贵格', 'level': '吉'}
    
    valid_guiren = [g for g in guiren_zhi[:2] if g in ZHI_LIST]
    if not valid_guiren:
        return {'matched': False, 'name': '干支拱贵格', 'level': '吉'}
    
    gan_idx = ZHI_LIST.index(jigong)
    zhi_idx = ZHI_LIST.index(ri_zhi)
    
    for g in valid_guiren:
        g_idx = ZHI_LIST.index(g)
        if _circular_between(g_idx, gan_idx, zhi_idx) or _circular_between(g_idx, zhi_idx, gan_idx):
            return {
                'matched': True,
                'name': '干支拱贵格',
                'level': '吉',
                'desc': f'日干{ri_gan}（{jigong}）、日支{ri_zhi}拱贵人{g}',
                'score': 82,
            }
    
    return {'matched': False, 'name': '干支拱贵格', 'level': '吉'}


def check_ganzhi_gong_lu(ri_gan: str, ri_zhi: str, lu_zhi: str) -> dict:
    """
    干支拱日禄格: 日干日支夹拱禄神
    条件: 禄位于日干和日支之间
    宜占食禄事
    """
    jigong = JIGONG.get(ri_gan, '')
    if not jigong or ri_zhi not in ZHI_LIST or lu_zhi not in ZHI_LIST:
        return {'matched': False, 'name': '干支拱日禄格', 'level': '吉'}
    
    gan_idx = ZHI_LIST.index(jigong)
    zhi_idx = ZHI_LIST.index(ri_zhi)
    lu_idx = ZHI_LIST.index(lu_zhi)
    
    matched = _circular_between(lu_idx, gan_idx, zhi_idx) or _circular_between(lu_idx, zhi_idx, gan_idx)
    
    return {
        'matched': matched,
        'name': '干支拱日禄格',
        'level': '吉',
        'desc': f'日干{ri_gan}（{jigong}）、日支{ri_zhi}拱禄神{lu_zhi}' if matched else '',
        'score': 80 if matched else 0,
    }


def check_sanhe_gong(sanchuan: dict, target_zhi: str, target_name: str) -> dict:
    """
    三合拱检测: 三传中任两个组成三合，第三个地支匹配目标
    """
    if not sanchuan:
        return {'matched': False, 'name': f'三合拱{target_name}格', 'level': '吉'}
    
    chuan_list = [
        sanchuan.get('初传', ''),
        sanchuan.get('中传', ''),
        sanchuan.get('末传', ''),
    ]
    chuan_zhi = [c for c in chuan_list if c and c in ZHI_LIST]
    
    if len(chuan_zhi) < 2:
        return {'matched': False, 'name': f'三合拱{target_name}格', 'level': '吉'}
    
    from itertools import combinations
    for a, b in combinations(chuan_zhi, 2):
        sa = ZHI_TO_SANHE.get(a, '')
        sb = ZHI_TO_SANHE.get(b, '')
        if sa and sa == sb:
            # 同一三合局，第三个地支应该匹配target
            san_he_set = set(SANHE.get(sa, []))
            missing = san_he_set - {a, b}
            for m in missing:
                if m == target_zhi:
                    return {
                        'matched': True,
                        'name': f'三合拱{target_name}格',
                        'level': '上吉',
                        'desc': f'三传中{a}{b}拱{target_name}{target_zhi}',
                        'score': 85,
                    }
    
    return {'matched': False, 'name': f'三合拱{target_name}格', 'level': '吉'}


def check_all_gong_patterns(sanchuan: dict, ri_gan: str, ri_zhi: str,
                             guiren_zhi: List[str], lu_zhi: str, ma_zhi: str) -> List[dict]:
    """
    检测所有拱类课格
    返回匹配到的所有课格列表
    """
    results = []
    
    # 7. 拱干格
    gong_gan = check_gong_gan(sanchuan, ri_gan)
    if gong_gan['matched']:
        results.append(gong_gan)
    
    # 8. 两贵引从格
    liang_gui = check_lianggui_yincong(sanchuan, ri_gan, guiren_zhi)
    if liang_gui['matched']:
        results.append(liang_gui)
    
    # 9. 拱支格
    gong_zhi = check_gong_zhi(sanchuan, ri_zhi)
    if gong_zhi['matched']:
        results.append(gong_zhi)
    
    # 10. 干支拱贵格
    gz_gui = check_ganzhi_gong_gui(ri_gan, ri_zhi, guiren_zhi)
    if gz_gui['matched']:
        results.append(gz_gui)
    
    # 11. 干支拱日禄格
    gz_lu = check_ganzhi_gong_lu(ri_gan, ri_zhi, lu_zhi)
    if gz_lu['matched']:
        results.append(gz_lu)
    
    # 12. 三合拱贵格
    if guiren_zhi:
        for gzhi in guiren_zhi[:2]:
            sanhe_gui = check_sanhe_gong(sanchuan, gzhi, '贵人')
            if sanhe_gui['matched']:
                results.append(sanhe_gui)
                break
    
    # 13. 三合拱禄格
    if lu_zhi:
        sanhe_lu = check_sanhe_gong(sanchuan, lu_zhi, '禄')
        if sanhe_lu['matched']:
            results.append(sanhe_lu)
    
    # 14. 三合拱马格
    if ma_zhi:
        sanhe_ma = check_sanhe_gong(sanchuan, ma_zhi, '马')
        if sanhe_ma['matched']:
            results.append(sanhe_ma)
    
    return results


# ══════════════════════════════════════════════════════════════
# C. 到山到向检测（增强）
# ══════════════════════════════════════════════════════════════

def check_lu_daoshan_daoxiang(lu_zhi: str, shan_target: str, xiang_target: str) -> dict:
    """禄到山到向检测"""
    return {
        'lu_zhi': lu_zhi,
        'to_shan': lu_zhi == shan_target,
        'to_xiang': lu_zhi == xiang_target,
        'is_daoshan_daoxiang': lu_zhi == shan_target or lu_zhi == xiang_target,
    }


def check_ma_daoshan_daoxiang(ma_zhi: str, shan_target: str, xiang_target: str) -> dict:
    """马到山到向检测"""
    return {
        'ma_zhi': ma_zhi,
        'to_shan': ma_zhi == shan_target,
        'to_xiang': ma_zhi == xiang_target,
        'is_daoshan_daoxiang': ma_zhi == shan_target or ma_zhi == xiang_target,
    }


def check_guiren_daoshan_daoxiang(guiren_zhi: List[str], shan_target: str, xiang_target: str) -> dict:
    """贵人到山到向检测"""
    to_shan = []
    to_xiang = []
    for gz in guiren_zhi[:2]:
        if gz == shan_target:
            to_shan.append(gz)
        if gz == xiang_target:
            to_xiang.append(gz)
    
    return {
        'guiren_zhi': guiren_zhi,
        'to_shan': to_shan,
        'to_xiang': to_xiang,
        'is_daoshan_daoxiang': len(to_shan) > 0 or len(to_xiang) > 0,
    }


def check_huoma_huolu(sanchuan: dict, lu_zhi: str, ma_zhi: str, guiren_zhi: List[str]) -> dict:
    """
    活马活禄检测: 禄马贵人在三传中发传
    秘诀: "真禄和活马才天机灵动，吉气迎入"
    """
    if not sanchuan:
        return {'huo_lu': False, 'huo_ma': False, 'huo_guiren': [], 'count': 0}
    
    chuan_list = [
        sanchuan.get('初传', ''),
        sanchuan.get('中传', ''),
        sanchuan.get('末传', ''),
    ]
    
    huo_lu = lu_zhi in chuan_list if lu_zhi else False
    huo_ma = ma_zhi in chuan_list if ma_zhi else False
    huo_guiren = [gz for gz in guiren_zhi[:2] if gz in chuan_list]
    
    count = sum([huo_lu, huo_ma, len(huo_guiren) > 0])
    
    return {
        'huo_lu': huo_lu,
        'huo_ma': huo_ma,
        'huo_guiren': huo_guiren,
        'count': count,
        'description': (
            f'三传中发传: {"禄" if huo_lu else ""}'
            f'{"马" if huo_ma else ""}'
            f'{"/".join(["贵"+g for g in huo_guiren]) if huo_guiren else ""}'
            f'(计{count}项)' if count > 0 else '无'
        ),
    }


# ══════════════════════════════════════════════════════════════
# D. 高级课格检测
# ══════════════════════════════════════════════════════════════

def check_chaotian_ge(tiandi_pan: dict, ri_gan: str, guiren_zhi: List[str]) -> dict:
    """
    朝天格: 贵人加日干之上
    条件: 贵人临日干寄宫的天盘位置
    """
    jigong = JIGONG.get(ri_gan, '')
    if not jigong or not tiandi_pan:
        return {'matched': False, 'name': '朝天格', 'level': '上吉'}
    
    tian_shen = tiandi_pan.get(jigong, '')
    if not tian_shen:
        return {'matched': False, 'name': '朝天格', 'level': '上吉'}
    
    matched = tian_shen in guiren_zhi[:2] if guiren_zhi else False
    
    return {
        'matched': matched,
        'name': '朝天格',
        'level': '上吉',
        'desc': f'贵人{tian_shen}加日干{ri_gan}（{jigong}）上' if matched else '',
        'score': 90 if matched else 0,
    }


def check_guiyuan_ge(tiandi_pan: dict, ri_zhi: str, guiren_zhi: List[str]) -> dict:
    """
    归垣格: 贵人归垣
    条件: 贵人临日支之上
    """
    if not tiandi_pan or ri_zhi not in ZHI_LIST:
        return {'matched': False, 'name': '归垣格', 'level': '吉'}
    
    tian_shen = tiandi_pan.get(ri_zhi, '')
    if not tian_shen:
        return {'matched': False, 'name': '归垣格', 'level': '吉'}
    
    matched = tian_shen in guiren_zhi[:2] if guiren_zhi else False
    
    return {
        'matched': matched,
        'name': '归垣格',
        'level': '吉',
        'desc': f'贵人{tian_shen}归垣日支{ri_zhi}' if matched else '',
        'score': 82 if matched else 0,
    }


def check_luowen_ge(ri_gan: str, ri_zhi: str, sike: list, tiandi_pan: dict) -> dict:
    """
    罗纹格: 干支互生
    条件: 干上神生支，支上神生干
    【BUG-FIX 2026-08-18】原 `if not sike or len(sike) < 4` 依赖四课，
    但 analyze_yidu_full 调用处传空 sike=[] → 永不触发。
    罗纹格判定只需天地盘（干支上神），解除 sike 依赖。
    """
    if not tiandi_pan:
        return {'matched': False, 'name': '罗纹格', 'level': '中吉'}
    
    jigong = JIGONG.get(ri_gan, '')
    if not jigong:
        return {'matched': False, 'name': '罗纹格', 'level': '中吉'}
    
    gan_shang = tiandi_pan.get(jigong, '')  # 干上神
    zhi_shang = tiandi_pan.get(ri_zhi, '')  # 支上神
    
    if not gan_shang or not zhi_shang:
        return {'matched': False, 'name': '罗纹格', 'level': '中吉'}
    
    # 罗纹格判定：干支上神五行互生（干上神生支、支上神生干，主客相生）
    WX_MAP = {
        '寅卯': '木', '巳午': '火', '申酉': '金',
        '亥子': '水', '辰戌丑未': '土',
    }
    
    def get_wx(zhi):
        for k, v in WX_MAP.items():
            if zhi in k:
                return v
        return ''
    
    gan_s_wx = get_wx(gan_shang)
    zhi_s_wx = get_wx(zhi_shang)
    
    # 生克关系: 木生火, 火生土, 土生金, 金生水, 水生木
    SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    
    gan_sheng_zhi = SHENG.get(gan_s_wx, '') == zhi_s_wx
    zhi_sheng_gan = SHENG.get(zhi_s_wx, '') == gan_s_wx
    
    matched = gan_sheng_zhi and zhi_sheng_gan
    
    return {
        'matched': matched,
        'name': '罗纹格',
        'level': '中吉',
        'desc': f'干上{gan_shang}生支、支上{zhi_shang}生干，主客相生' if matched else '',
        'score': 78 if matched else 0,
    }


def check_longde_ke(sanchuan: dict, tiandi_pan: dict, yue_jiang: str,
                     tianjiang_map: dict, nian_zhi: str) -> dict:
    """
    龙德课: 太岁=月将乘贵人发用
    条件: 太岁 = 月将，且乘贵人发用
    """
    if not sanchuan or not tiandi_pan:
        return {'matched': False, 'name': '龙德课', 'level': '上吉'}
    
    chu = sanchuan.get('初传', '')
    if not chu:
        return {'matched': False, 'name': '龙德课', 'level': '上吉'}
    
    # 太岁=月将
    taisui_equals_yuejiang = (nian_zhi == yue_jiang) if nian_zhi and yue_jiang else False
    
    # 太岁乘贵人发用
    taisui_is_chu = (chu == nian_zhi) if nian_zhi else False
    
    # 初传是否为贵人
    chu_tianjiang = tianjiang_map.get(chu, '') if isinstance(tianjiang_map, dict) else ''
    chu_is_guiren = (chu_tianjiang == '贵人')
    
    matched = taisui_equals_yuejiang and taisui_is_chu and chu_is_guiren
    
    return {
        'matched': matched,
        'name': '龙德课',
        'level': '上吉',
        'desc': f'太岁{nian_zhi}=月将{nian_zhi}乘贵人发用' if matched else '',
        'score': 95 if matched else 0,
    }


# ══════════════════════════════════════════════════════════════
# E. 斗首补元规则
# ══════════════════════════════════════════════════════════════

def check_buyuan_methods(pillars: Dict[str, str], shan: str, ri_gan: str) -> dict:
    """
    斗首补元规则检测
    原文: 以元补元→以武补元→以廉补元→以贪破补元
    
    pillars: {'年': '甲子', '月': '丙寅', '日': '戊辰', '时': '庚午'}
    """
    # 先检查元辰是否衰弱
    yuanchen_pillars = []
    yuan_chen_gans = get_yuanchen_gans(shan)
    
    for label, p in pillars.items():
        gan = p[0]
        lt = check_liuxiang_liuti(p, ri_gan)
        if gan in yuan_chen_gans:
            yuanchen_pillars.append({
                'pillar': label, 'ganshi': p,
                'state': lt['state'], 'is_xiang': lt['is_xiang']
            })
    
    # 检测是否需要补救
    needs_buyuan = True
    if yuanchen_pillars:
        all_xiang = all(p['is_xiang'] for p in yuanchen_pillars)
        if all_xiang:
            needs_buyuan = False
    
    if not needs_buyuan:
        return {'needs_buyuan': False, 'method': '', 'description': '元辰旺相，无需补救'}
    
    # 检测补救级别
    classes = {}
    for label, p in pillars.items():
        classes[label] = get_doushou_class(shan, p)
    
    buyuan_method = ''
    buyuan_pillars = []
    
    # 1. 以元补元（最优）
    for label, cls in classes.items():
        if cls == '元辰':
            p = pillars[label]
            lt = check_liuxiang_liuti(p, ri_gan)
            if lt['is_xiang']:
                buyuan_method = '以元补元'
                buyuan_pillars.append(label)
    
    # 2. 以武补元
    if not buyuan_pillars:
        for label, cls in classes.items():
            if cls == '武财':
                p = pillars[label]
                lt = check_liuxiang_liuti(p, ri_gan)
                if lt['is_xiang']:
                    buyuan_method = '以武补元'
                    buyuan_pillars.append(label)
    
    # 3. 以廉补元
    if not buyuan_pillars:
        for label, cls in classes.items():
            if cls == '廉子':
                p = pillars[label]
                lt = check_liuxiang_liuti(p, ri_gan)
                if lt['is_xiang']:
                    buyuan_method = '以廉补元'
                    buyuan_pillars.append(label)
    
    # 4. 以贪破补元（最次，需到山到向发传）
    if not buyuan_pillars:
        for label, cls in classes.items():
            if cls in ('贪官', '破鬼'):
                p = pillars[label]
                lt = check_liuxiang_liuti(p, ri_gan)
                if lt['is_ti']:
                    buyuan_method = '以贪破补元（需到山到向发传）'
                    buyuan_pillars.append(label)
    
    return {
        'needs_buyuan': needs_buyuan,
        'method': buyuan_method,
        'pillars': buyuan_pillars,
        'description': f'{buyuan_method}: {",".join(buyuan_pillars)}柱' if buyuan_method else '无有效补救',
        'yuanchen_status': yuanchen_pillars,
    }


# ═════════ 三煞方判定（《要诀》ZR_15_02 择日禁忌；2026-09-05 接入） ═════════
# 原文："三煞者，劫煞、灾煞、岁煞也。申子辰年煞在南方巳午未，亥卯未年煞在西方申酉戌，
#        寅午戌年煞在北方亥子丑，巳酉丑年煞在东方寅卯辰。日课不可犯。"
# 年支三合局 → 对冲方位的地支三合为三煞方；日课四柱地支任一落入即犯三煞。
SAN_SHA_MAP = {
    '申': ['巳','午','未'], '子': ['巳','午','未'], '辰': ['巳','午','未'],
    '亥': ['申','酉','戌'], '卯': ['申','酉','戌'], '未': ['申','酉','戌'],
    '寅': ['亥','子','丑'], '午': ['亥','子','丑'], '戌': ['亥','子','丑'],
    '巳': ['寅','卯','辰'], '酉': ['寅','卯','辰'], '丑': ['寅','卯','辰'],
}

def check_san_sha(nian_zhi: str, yue_zhi: str = '', pillars: Dict[str, str] = None) -> dict:
    """
    三煞方判定（《要诀》"日课不可犯"）
    - 年支三合局的对冲方位三地支 = 三煞方（SAN_SHA_MAP）
    - 月支可作次判（三煞随年为主，随月为辅——年煞最重）
    - pillars: {'年':'甲子','月':'丙寅','日':'戊辰','时':'庚午'}，取其地支判定落入
    返回 { hit, shan_sha_zhi, hit_pillars, level }
    """
    zhis = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    if nian_zhi not in SAN_SHA_MAP:
        return {'hit': False, 'shan_sha_zhi': [], 'hit_pillars': [], 'level': ''}
    san_sha = SAN_SHA_MAP[nian_zhi]
    # 月支三煞（次判，年为主月为辅）
    yue_sha = SAN_SHA_MAP.get(yue_zhi, []) if yue_zhi else []
    hit_pillars = []
    if pillars:
        for label in ['年', '月', '日', '时']:
            p = pillars.get(label, '')
            if len(p) >= 2 and p[1] in san_sha:
                hit_pillars.append(label)
    level = ''
    if hit_pillars:
        # 日时为内（最忌），年月为外
        inner = [x for x in hit_pillars if x in ('日', '时')]
        level = '犯三煞(日时·内，最忌)' if inner else '犯三煞(年月·外)'
    return {
        'hit': bool(hit_pillars),
        'shan_sha_zhi': san_sha,
        'yue_sha_zhi': yue_sha,
        'hit_pillars': hit_pillars,
        'level': level,
    }


# ══════════════════════════════════════════════════════════════
# F. 综合评分
# ══════════════════════════════════════════════════════════════

# ── 演禽窃要（《要诀》秘传；2026-09-05 接入）──
# 原文锚点（《仪度六壬选日要诀》李佳明注）：
#   ① 第73-75页：「甲山坐尾火宿，丑中斗木加来木下生火，竞含演禽真法」
#       甲山→寅宫→尾火宿（坐山宿）；丑宫→斗木宿；木（斗木）生火（尾火）→ 合演禽真法
#   ② 第75-76页：「演禽尾火毕月互相比旺」（庚山→申宫→毕月宿；三传寅→尾火宿；尾火毕月
#       均为七元将头高禽，比旺而吉）
# 判据（用户拍板 2026-09-05：到山+10 / 生+8 / 高禽+3；泊宫得地+8 / 失地-8；
#   比和仅展示不加分——无原文正面吉验例）：
#   · 坐山宿：二十四山 → 地支宫 → 宫首宿（甲→尾火、庚→毕月，与罗盘二十八宿分金等价）
#   · 日课宿：四柱地支 → 宫首宿（丑→斗木、寅→尾火、申→毕月）
#   · 相生：初传宿五行 生 坐山宿五行 → +8（例1「木下生火」；日→火、月→水归一同 yanqin_analyzer）
#   · 到山：坐山宿入初传/中传 → +10/个（例2 中传申=庚山毕月）
#   · 高禽：三传高禽宿≥2 且含坐山宿 → +3/个（例2 尾火毕月比旺）
#   · 比和：中传宿与坐山宿同五行 → 仅展示不加分（无原文正面吉验例）
#   · 泊宫：日禽锁泊得地+8/失地-8（需公历日期，经sxtwl 日禽；无日期安全跳过）

# 地支宫 → 宫首宿（辰角亢→角、巳翼轸→翼、午星张→星、未柳鬼→柳、
#   申毕觜参→毕、酉胃昴→胃、戌奎娄→奎、亥室壁→室、子虚危→虚、丑斗牛→斗、寅尾箕→尾、卯房心→房）
_YQ_ZHI_XIU = {'子': '虚', '丑': '斗', '寅': '尾', '卯': '房', '辰': '角', '巳': '翼',
               '午': '星', '未': '柳', '申': '毕', '酉': '胃', '戌': '奎', '亥': '室'}
# 二十四山 → 地支宫（双山归宫：壬子→子、癸丑→丑、艮寅→寅、甲卯→卯、乙辰→辰、
#   巽巳→巳、丙午→午、丁未→未、坤申→申、庚酉→酉、辛戌→戌、乾亥→亥）
_YQ_SHAN_TO_ZHI = {'壬': '子', '子': '子', '癸': '丑', '丑': '丑',
                   '艮': '寅', '寅': '寅', '甲': '寅', '卯': '卯',
                   '乙': '辰', '辰': '辰', '巽': '巳', '巳': '巳',
                   '丙': '午', '午': '午', '丁': '未', '未': '未',
                   '坤': '申', '申': '申', '庚': '申', '酉': '酉',
                   '辛': '戌', '戌': '戌', '乾': '亥', '亥': '亥'}
# 七元将头（七高禽）：能降伏诸禽，遇之比旺（原文「尾火毕月互相比旺」）
_YQ_GAO_QIN = ('尾', '毕', '井', '奎', '箕', '角', '亢')
_YQ_ZHISHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}


def _yq_xiu_wuxing(xiu: str, _wx_map: dict) -> str:
    """宿五行取用（日→火、月→水归一，与 yanqin_analyzer._xiu_wuxing 一致）。"""
    wx = _wx_map.get(xiu, '')
    if wx == '日':
        return '火'
    if wx == '月':
        return '水'
    return wx if wx in ('木', '火', '土', '金', '水') else ''


def check_yanqin_qieyao(shan: str, pillars: Dict[str, str],
                        shichen: str = '',
                        year: int = None, month: int = None, day: int = None,
                        sanchuan_dizhi: list = None) -> dict:
    """演禽窃要判定（《要诀》秘传 + 《禽星易见》泊宫）。

    判据载体 = 三传地支（原文例均以三传宿加临坐山，防空判过宽）：
      ① 例1（73-75页）：甲山尾火，三传丑亥酉「丑中斗木加来木下生火」——初传丑=斗木，生坐山尾火
      ② 例2（75-76页）：庚山毕月，三传寅申寅「演禽尾火毕月互相比旺」——中传申=毕月=坐山宿（演禽到山），
         初末寅=尾火（七元将头高禽比旺）
    ——所以相生/比和只认 初传+中传；坐山宿入三传=「演禽到山」；高禽≥2 才比旺。

    返回 {shan_xiu, shan_wx, hits, ds_count, sheng_count, bihe_count,
          gaoqin_count, po_gong, bonus}。bonus = 到山×10 + 相生×8 + 高禽×3 + 泊宫±8
    （比和仅展示不加分——无原文正面吉验例，2026-09-05 用户拍板）。
    """
    # 二十八宿五行表（从 yanqin_analyzer 取，避免双份数据）
    try:
        from engine.yanqin_analyzer import YanQinAnalyzer as _YQA
        _wx_map = dict(_YQA.XIU_WUXING)
    except Exception:
        _wx_map = {}
    if not _wx_map:
        _wx_map = {  # 降级内置表（与 yanqin_analyzer.XIU_WUXING 一致）
            '角': '木', '亢': '金', '氐': '土', '房': '日', '心': '月',
            '尾': '火', '箕': '水', '斗': '木', '牛': '金', '女': '土', '虚': '日', '危': '月',
            '室': '火', '壁': '水', '奎': '木', '娄': '金', '胃': '土', '昴': '日', '毕': '月',
            '觜': '火', '参': '水', '井': '木', '鬼': '金', '柳': '土', '星': '日', '张': '月',
            '翼': '火', '轸': '水',
        }

    # ① 坐山宿：二十四山 → 宫 → 宫首宿
    shan_zhi = _YQ_SHAN_TO_ZHI.get(shan, '')
    shan_xiu = _YQ_ZHI_XIU.get(shan_zhi, '')
    shan_wx = _yq_xiu_wuxing(shan_xiu, _wx_map)

    hits = []          # 命中明细 {position, zhi, xiu, wx, relation}
    ds_count = sheng_count = bihe_count = gaoqin_count = 0

    # ② 三传承载判据；无三传则仅返回坐山宿信息（不加分，防空判过宽）
    sc = [z for z in (sanchuan_dizhi or []) if z]
    if shan_wx and len(sc) >= 2:
        # 坐山宿入初传/中传 = 演禽到山（例2：中传申=庚山毕月；收敛只认前两传防过宽）
        for i, z in enumerate(sc[:2]):
            if _YQ_ZHI_XIU.get(z) == shan_xiu:
                ds_count += 1
                hits.append({'position': '初传' if i == 0 else ('中传' if i == 1 else '末传'),
                             'zhi': z, 'xiu': shan_xiu, 'relation': '到山'})
        # 相生/比和：相生只认初传（例1「丑中斗木加来」丑在初传，见原文三传丑亥酉），
        #   比和只认中传（例2「尾火毕月互相比旺」毕月=庚山宿在中传）——收敛命中率防过宽
        for i, z in enumerate(sc[:2]):
            xiu = _YQ_ZHI_XIU.get(z, '')
            wx = _yq_xiu_wuxing(xiu, _wx_map)
            rel = ''
            if xiu != shan_xiu and wx:
                if i == 0 and _YQ_ZHISHENG.get(wx) == shan_wx:
                    sheng_count += 1
                    rel = '相生'
                elif i == 1 and wx == shan_wx:
                    # 比和：无原文正面吉验例（例2「比旺」实指高禽），只展示不加分（2026-09-05 用户拍板）
                    bihe_count += 1
                    rel = '比和'
            if rel:
                hits.append({'position': '初传' if i == 0 else '中传',
                             'zhi': z, 'xiu': xiu, 'wx': wx, 'relation': rel})
        # 高禽比旺：三传高禽宿≥2 且含坐山宿（原文例2：庚山毕月=高禽在传，与初末尾火「互相比旺」；
        #   坐山宿非高禽（如尾/毕/角/奎外）则不判——收敛命中率防过宽）
        _gx = {z for z in sc if _YQ_ZHI_XIU.get(z) in _YQ_GAO_QIN}
        if shan_xiu in _YQ_GAO_QIN and len(_gx) >= 2:
            gaoqin_count = len(_gx)
            hits.append({'position': '三传', 'zhi': '、'.join(sc),
                         'relation': f'{shan_xiu}宿比旺({len(_gx)}高禽)'})

    po_gong = {}
    if year and month and day:
        try:
            from engine.yanqin_analyzer import YanQinAnalyzer as _YQA2
            _yq_res = _YQA2().analyze_yanqin_with_calendar(
                {'年柱': pillars.get('年', ''), '月柱': pillars.get('月', ''),
                 '日柱': pillars.get('日', ''), '时柱': pillars.get('时', '')},
                year, month, day)
            po_gong = _yq_res.get('泊宫', {}).get('日禽', {}) or {}
        except Exception:
            po_gong = {}

    bonus = ds_count * 10 + sheng_count * 8 + gaoqin_count * 3
    if po_gong.get('吉凶') == '吉':
        bonus += 8
    elif po_gong.get('吉凶') == '凶':
        bonus -= 8

    return {
        'shan_xiu': shan_xiu, 'shan_wx': shan_wx,
        'hits': hits, 'ds_count': ds_count, 'sheng_count': sheng_count,
        'bihe_count': bihe_count, 'gaoqin_count': gaoqin_count,
        'po_gong': po_gong, 'bonus': bonus,
    }


def score_doushou_liuxiang(year_pillar: str, month_pillar: str,
                            day_pillar: str, hour_pillar: str,
                            shan: str) -> dict:
    """综合斗首+六相六替评分（保持向后兼容）"""
    score = 60
    details = []
    
    yuan_check = check_sizhu_tou_yuanchen(year_pillar, month_pillar, day_pillar, hour_pillar, shan)
    if yuan_check['has_yuanchen']:
        score += 15
        details.append('+15 有透元辰')
    else:
        score -= 10
        details.append('-10 无透元辰')
    
    if yuan_check['xiang_count'] >= 3:
        score += 10
        details.append(f'+10 六相多({yuan_check["xiang_count"]}个)')
    elif yuan_check['xiang_count'] <= 1:
        score -= 10
        details.append(f'-10 六相少({yuan_check["xiang_count"]}个)')
    
    if yuan_check['ti_count'] >= 3:
        score -= 10
        details.append(f'-10 六替多({yuan_check["ti_count"]}个)')
    
    score = max(20, min(100, score))
    
    return {
        'score': score,
        'details': details,
        'yuanchen_check': yuan_check,
        'recommendation': yuan_check['recommendation'],
    }


def analyze_yidu_full(shan: str,
                       year_pillar: str, month_pillar: str,
                       day_pillar: str, hour_pillar: str,
                       ri_gan: str, ri_zhi: str,
                       sanchuan: dict = None,
                       tiandi_pan: dict = None,
                       tianjiang_map: dict = None,
                       yue_jiang: str = None,
                       nian_zhi: str = None,
                       shichen: str = None,
                       ke_ti: str = None,
                       year: int = None, month: int = None, day: int = None,
                       ben_ming: str = None, ben_ming_gan: str = None,
                       zeri_type: str = '', kong: list = None) -> dict:
    """
    完整的仪度六壬择日分析（2026-08-31 统一评分口径）

    评分口径（用户拍板）：
        权威骨架 = calculate_new_score 禄马贵人到山到向分（四柱到山到向 + 三传禄马贵
                  + 课体扣分 + 秘诀调整 + 太阳太岁）
        加分项   = 斗首六想增量 + 三元三武 + 凶在外吉在内 + 拱格 + 活禄马 + 高级课格 + 补元
        一票否决 = 斗首凶在日时(内)（贪官/破鬼临日时）→ 一定不能用（grade=不宜）

    参数:
        shan: 坐山（如'壬'）
        year_pillar, month_pillar, day_pillar, hour_pillar: 四柱干支
        ri_gan: 日干
        ri_zhi: 日支
        sanchuan: 三传 {初传, 中传, 末传}
        tiandi_pan: 天地盘 {地盘: 天盘}
        tianjiang_map: 天将映射 {地盘: 天将}
        yue_jiang: 月将
        nian_zhi: 年支
        shichen: 时辰（缺省用 时支 推导）
        ke_ti: 课体名称（供禄马贵人骨架课体扣分；缺省不扣课体分）
        ben_ming: 祭主（福主）本命地支（如'子'；2026-09-05 接入本命贵人/作禄作马加分）
        ben_ming_gan: 祭主（福主）本命天干（如'甲'；判定命禄用，可缺省）

    返回: 完整分析报告
    """
    # 边界保护：四柱空值/短柱用默认值（【BUG-FIX 2026-08-18】原只保护时柱，
    # 年/月/日柱为空时 check_sizhu_tou_yuanchen 内 pillar[0] 会 IndexError）
    if not year_pillar or len(year_pillar) < 2:
        year_pillar = '甲子'
    if not month_pillar or len(month_pillar) < 2:
        month_pillar = '甲子'
    if not day_pillar or len(day_pillar) < 2:
        day_pillar = '甲子'
    if not hour_pillar or len(hour_pillar) < 2:
        hour_pillar = '甲子'

    # === A. 斗首六相六替 ===
    yuan_check = check_sizhu_tou_yuanchen(year_pillar, month_pillar, day_pillar, hour_pillar, shan)
    liuxiang_score = score_doushou_liuxiang(year_pillar, month_pillar, day_pillar, hour_pillar, shan)
    
    # 斗首类别
    doushou_classes = {
        '年': get_doushou_class(shan, year_pillar),
        '月': get_doushou_class(shan, month_pillar),
        '日': get_doushou_class(shan, day_pillar),
        '时': get_doushou_class(shan, hour_pillar),
    }
    
    # 三元三武一廉
    sanyuan_check = check_sanyuan_sanwu_yilian(
        doushou_classes['年'], doushou_classes['月'],
        doushou_classes['日'], doushou_classes['时'],
    )
    
    # 凶吉内外
    jixiong_check = check_jixiong_position(doushou_classes)
    
    # === B. 拱类课格 ===
    lu_zhi = LU.get(ri_gan, '')
    ma_zhi = get_yima(ri_zhi)
    
    # 获取贵人
    guiren_zhi = []
    try:
        from data.斗首择日规则 import GUIREN
        if ri_gan in GUIREN:
            guiren_zhi = list(GUIREN[ri_gan])  # [昼贵, 夜贵]
    except Exception:
        # 【BUG-FIX 2026-08-18】data 模块不可用时降级为空贵人，不阻断整链分析
        guiren_zhi = []
    
    gong_patterns = []
    if sanchuan:
        gong_patterns = check_all_gong_patterns(sanchuan, ri_gan, ri_zhi, guiren_zhi, lu_zhi, ma_zhi)
    
    # === C. 到山到向 ===
    shan_jia = SHAN_JIA_MAP.get(shan, '')
    xiang_shou = XIANG_SHOU.get(shan, shan_jia)
    
    # 【2026-09-07 用户拍板：严格直达】daoshan_daoxiang 改"天盘加临后直达"口径（原静态日柱禄马贵
    #   直接比山向 → 与 luma_detail(calculate_new_score 加临口径) 矛盾，前端显示"0 vs 满分"）。
    #   现统一：禄马贵加临后正好落山家/向首才算到（不含三合次吉）。
    try:
        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen as _LUM
        _spj = _LUM().check_single_pillar(ri_gan, ri_zhi, tiandi_pan or {}, shichen or '午',
                                          shan_jia, xiang_shou, '日')
        _lu_z = _spj.get('lu_zhi', '') or ''
        _ma_z = _spj.get('ma_zhi', '') or ''
        _gr_z = _spj.get('guiren_zhi', '') or ''
        lu_dsdx = {'lu_zhi': _lu_z, 'is_daoshan_daoxiang': bool(_spj.get('lu_to_shan') or _spj.get('lu_to_xiang')),
                   'to_shan': [_lu_z] if _spj.get('lu_to_shan') else [], 'to_xiang': [_lu_z] if _spj.get('lu_to_xiang') else []}
        ma_dsdx = {'ma_zhi': _ma_z, 'is_daoshan_daoxiang': bool(_spj.get('ma_to_shan') or _spj.get('ma_to_xiang')),
                   'to_shan': [_ma_z] if _spj.get('ma_to_shan') else [], 'to_xiang': [_ma_z] if _spj.get('ma_to_xiang') else []}
        guiren_dsdx = {'guiren_zhi': [_gr_z] if _gr_z else [],
                       'is_daoshan_daoxiang': bool(_spj.get('guiren_to_shan') or _spj.get('guiren_to_xiang')),
                       'to_shan': [_gr_z] if _spj.get('guiren_to_shan') else [],
                       'to_xiang': [_gr_z] if _spj.get('guiren_to_xiang') else []}
    except Exception:
        # 降级：退回静态口径（不阻断）
        lu_dsdx = check_lu_daoshan_daoxiang(lu_zhi, shan_jia, xiang_shou)
        ma_dsdx = check_ma_daoshan_daoxiang(ma_zhi, shan_jia, xiang_shou)
        guiren_dsdx = check_guiren_daoshan_daoxiang(guiren_zhi, shan_jia, xiang_shou)
    
    # 活马活禄
    huoma_huolu = check_huoma_huolu(sanchuan, lu_zhi, ma_zhi, guiren_zhi) if sanchuan else {
        'huo_lu': False, 'huo_ma': False, 'huo_guiren': [], 'count': 0, 'description': '无三传数据'
    }
    
    # === D. 高级课格 ===
    chaotian = check_chaotian_ge(tiandi_pan, ri_gan, guiren_zhi) if tiandi_pan else {'matched': False}
    guiyuan = check_guiyuan_ge(tiandi_pan, ri_zhi, guiren_zhi) if tiandi_pan else {'matched': False}
    luowen = check_luowen_ge(ri_gan, ri_zhi, [], tiandi_pan) if tiandi_pan else {'matched': False}
    longde = check_longde_ke(sanchuan, tiandi_pan, yue_jiang, tianjiang_map, nian_zhi) if sanchuan else {'matched': False}
    
    # === E. 补元 ===
    buyuan = check_buyuan_methods(
        {'年': year_pillar, '月': month_pillar, '日': day_pillar, '时': hour_pillar},
        shan, ri_gan
    )

    # === E2. 三煞方判定（《要诀》ZR_15_02"日课不可犯"；2026-09-05 接入，择日禁忌）===
    #    年支三合对冲方位；四柱地支任一落入 = 犯三煞。日时(内)最忌。
    san_sha = check_san_sha(
        nian_zhi,
        month_pillar[1] if month_pillar and len(month_pillar) >= 2 else '',
        {'年': year_pillar, '月': month_pillar, '日': day_pillar, '时': hour_pillar},
    )
    
    # === F. 综合评分（2026-08-31 统一口径：禄马贵人到山到向为权威骨架 + 加分项 + 斗首凶在内一票否决）===
    matched_patterns = []
    # 时辰缺省用 时支 推导（六壬时辰 = 时柱地支）
    if not shichen and len(hour_pillar) >= 2:
        shichen = hour_pillar[1]
    if not shichen:
        shichen = '子'

    # 0) 斗首凶在日时(内) → 一票否决（用户拍板：一定不能用）
    #    check_jixiong_position 仅「凶在日时(内)」会产生负分（-15/-10），score<0 即命中
    jx_score = jixiong_check['score']
    vetoed = jx_score < 0
    veto_reason = '斗首凶在日时(内)（贪官/破鬼临日时），一定不能用' if vetoed else ''

    # 1) 禄马贵人到山到向权威骨架（calculate_new_score：四柱到山到向 + 三传禄马贵 + 课体扣分
    #    + 秘诀调整 + 太阳太岁；到山到向已含其中，不再另行加分避免重复）
    luma_base = 60.0
    luma_detail = {}
    try:
        # 【2026-09-05 单课日期传参】若调用方传了公历日期 → 用节气精确月将(get_yuejiang_by_date)
        #   覆盖外部 yue_jiang，使单课与批量同口径；未传日期则保持外部 yue_jiang（行为不变）。
        _lrm_yj = yue_jiang
        _cns_date = {}
        if year and month and day:
            _lrm_yj = _LRM().get_yuejiang_by_date(year, month, day)
            _cns_date = {'year': year, 'month': month, 'day': day}
        _ns = _LRM().calculate_new_score(
            shan, shichen,
            year_pillar[0], year_pillar[1], month_pillar[0], month_pillar[1],
            day_pillar[0], day_pillar[1], hour_pillar[0], hour_pillar[1],
            sanchuan=sanchuan,
            ke_ti_list=[ke_ti] if ke_ti else None,
            yuejiang=_lrm_yj,
            **_cns_date,
        )
        luma_base = float(_ns.get('final_score', 60) or 60)
        luma_detail = _ns
    except Exception:
        luma_base = 60.0

    # 1b) 课体修正明细透出（十三吉课加分/凶课减分：已在 luma_base 骨架内生效，此处仅展示不重复加分；
    #     2026-09-05 细化透出，供加分项明细可查）
    _kadj = luma_detail.get('keti_adjust') if isinstance(luma_detail, dict) else None
    if isinstance(_kadj, dict) and _kadj.get('ke_score'):
        _ks = int(_kadj['ke_score'])
        _knote = _kadj.get('note', '课体修正')
        matched_patterns.append(f'{_ks:+d} {_knote}')

    # 2) 加分项（斗首吉格 / 拱格 / 活禄马 / 高级课格 / 补元）
    bonus = 0.0
    # 斗首六想强弱增量（60 为基准压缩到 ±10 量级）
    doushou_delta = (liuxiang_score['score'] - 60) // 4
    if doushou_delta:
        bonus += doushou_delta
        matched_patterns.append(f'{doushou_delta:+d} 斗首六想')
    # 三元三武一廉（第一吉课）
    if sanyuan_check['is_first_jike']:
        bonus += 15
        matched_patterns.append(f'+15 {sanyuan_check["grade"]}')
    elif sanyuan_check['grade']:
        bonus += 8
        matched_patterns.append(f'+8 {sanyuan_check["grade"]}')
    # 凶在外吉在内（正向加分；凶在日时(内)已一票否决，不再罚分）
    if jx_score > 0:
        bonus += jx_score
        matched_patterns.append(f'+{jx_score} 凶在外吉在内')
    # 拱格得分
    # 【2026-09-05 同源去重】课体修正命中"禄马贵在三传"类十三吉课（亨通/和美/荣华——
    #   判据本身含"禄马贵到山向/三传全备"）时，"三传中之禄马贵"已有课体修正 +10~20 计分；
    #   活禄马与拱格的禄马贵类（拱贵/拱禄/拱马/干支拱日禄）不再重复加分，仅展示。
    _lmg_jike = any(k in str(luma_detail.get('keti_adjust', {}).get('jike_details', []))
                    if isinstance(luma_detail, dict) else ''
                    for k in ('亨通', '和美', '三传全备', '天干二贵', '发用为山向禄马贵'))
    for gp in gong_patterns:
        if not gp['matched']:
            continue
        if _lmg_jike and any(k in gp['name'] for k in ('拱贵', '拱禄', '拱马', '日禄')):
            matched_patterns.append(f'拱格 {gp["name"]}（禄马贵已计入课体修正，仅示）')
            continue
        bonus += 5
        matched_patterns.append(f'+5 {gp["name"]}')
    # 到山到向计数（仅用于明细展示，不参与加分——已在禄马贵人骨架内）
    dsdx_count = sum([lu_dsdx['is_daoshan_daoxiang'], ma_dsdx['is_daoshan_daoxiang'], guiren_dsdx['is_daoshan_daoxiang']])
    # 活马活禄
    if huoma_huolu['count'] > 0:
        if _lmg_jike:
            matched_patterns.append(f'活禄马({huoma_huolu["count"]}项·禄马贵已计入课体修正，仅示)')
        else:
            bonus += huoma_huolu['count'] * 5
            matched_patterns.append(f'+{huoma_huolu["count"]*5} 活禄马({huoma_huolu["count"]}项)')
    # 高级课格
    for pattern in [chaotian, guiyuan, luowen, longde]:
        if pattern.get('matched'):
            if pattern.get('name') == '龙德课' and '龙德' in str(
                    (sanchuan or {}).get('课体') if isinstance(sanchuan, dict) else ''):
                # 龙德课已由 luma_base 骨架课体修正（十三吉课 +10/+20）计分，此处不再重复加（2026-09-05 去重）
                matched_patterns.append('命中 龙德课（已在十三吉课课体修正计分）')
                continue
            bonus += 5
            matched_patterns.append(f'+5 {pattern["name"]}')
    # 补元
    if buyuan['method']:
        bonus += 3
        matched_patterns.append(f'+3 {buyuan["method"]}')
    # 斗首四柱结构格局加分（天地同流/一气/三朋/五常/秀气/三合/方局/官旺/三奇；2026-09-05 接入）
    #   分值表与 DouhouKegeAnalyzer._calculate_score 一致（天地同流+15、一气+8、三朋+5、五常+6、
    #   秀气+5、三合局/方局+4、官旺+3、三奇+4）；复用其判格局函数避免双份判据
    sizhu_patterns = []
    try:
        from engine.douhou_analyzer import DouhouKegeAnalyzer as _DHA
        _dh = _DHA()
        _dh._judge_sizhu_structure_patterns(
            sizhu_patterns,
            {'年柱': year_pillar, '月柱': month_pillar, '日柱': day_pillar, '时柱': hour_pillar},
        )
    except Exception:
        sizhu_patterns = []
    _SZ_STRUCT_SCORES = [
        ('天地同流', 15),
        ('天元一气', 8),
        ('地支一气', 8),
        ('三朋', 5),
        ('曲直', 6), ('炎上', 6), ('从革', 6), ('润下', 6), ('稼穑', 6),
        ('秀气', 5),
        # 三合局：格局名为「申子辰水局」等（douhou_analyzer 原用'三合'关键字不命中，此处按实名校准）
        ('水局', 4), ('木局', 4), ('火局', 4), ('金局', 4),
        ('方局', 4),
        ('官旺', 3),
        ('三奇', 4),
    ]
    for _pt in sizhu_patterns:
        if _pt.get('吉凶') not in ('吉', '大吉'):
            continue
        _pn = _pt.get('格局名称', '')
        _sv = 0
        for _kw, _v in _SZ_STRUCT_SCORES:
            if _kw in _pn:
                _sv = _v
                break
        if _sv:
            bonus += _sv
            matched_patterns.append(f'+{_sv} {_pn}')
    # 祭主（福主）本命应福加分（2026-09-05 接入；用户拍板：本命贵人+8/柱，作禄/作马+5/项）
    #   · 本命贵人：本命支落在某柱天干之天乙贵人地支集合 → 该柱为命主贵人到位（发贵应主）
    #   · 本命作禄：命干之禄支出现在四柱地支 → 坐命禄（发财应主）；本命作马：命支之驿马支在四柱 → 坐命马
    if ben_ming:
        try:
            _bmg = _LRM().check_ben_ming_guiren(
                ben_ming, year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0])
            if _bmg.get('count'):
                _bm_a = _bmg['count'] * 8
                bonus += _bm_a
                matched_patterns.append(f'+{_bm_a} 本命贵人({_bmg["count"]}柱)')
            _bml = _LRM().check_ben_ming_ma_lu(
                ben_ming, ben_ming_gan,
                year_pillar[1], month_pillar[1], day_pillar[1], hour_pillar[1])
            _bm_lm = _bml.get('lu_count', 0) + _bml.get('ma_count', 0)
            if _bm_lm:
                _bm_b = _bm_lm * 5
                bonus += _bm_b
                matched_patterns.append(
                    f'+{_bm_b} 本命作禄作马({_bml.get("lu_count", 0)}禄/{_bml.get("ma_count", 0)}马)')
        except Exception:
            pass
    # 演禽窃要加分（《要诀》秘传；2026-09-05 接入，用户拍板：到山+10/生+8/比和+5/高禽+3，结合泊宫）
    #   判据载体=三传（原文「丑中斗木加来木下生火」「演禽尾火毕月互相比旺」皆指三传宿加临坐山）
    yanqin_detail = {}
    try:
        _yq_sc = []
        if sanchuan and isinstance(sanchuan, dict):
            _yq_sc = [sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
        yanqin_detail = check_yanqin_qieyao(
            shan,
            {'年': year_pillar, '月': month_pillar, '日': day_pillar, '时': hour_pillar},
            shichen=shichen or (hour_pillar[1] if len(hour_pillar) >= 2 else ''),
            year=year, month=month, day=day,
            sanchuan_dizhi=_yq_sc,
        )
        if yanqin_detail['ds_count']:
            _yd2 = yanqin_detail['ds_count'] * 10
            bonus += _yd2
            matched_patterns.append(f'+{_yd2} 演禽到山({yanqin_detail["shan_xiu"]}宿入三传)')
        if yanqin_detail['sheng_count']:
            _ys = yanqin_detail['sheng_count'] * 8
            bonus += _ys
            matched_patterns.append(f'+{_ys} 演禽相生({_ys//8}传生{yanqin_detail["shan_xiu"]}宿)')
        if yanqin_detail['bihe_count']:
            _yb = yanqin_detail['bihe_count'] * 5
            bonus += _yb
            matched_patterns.append(f'+{_yb} 演禽比和({_yb//5}传同{yanqin_detail["shan_xiu"]}宿)')
        if yanqin_detail['gaoqin_count']:
            _yg = yanqin_detail['gaoqin_count'] * 3
            bonus += _yg
            matched_patterns.append(f'+{_yg} 演禽高禽比旺({_yg//3}宿)')
        _ypg = yanqin_detail.get('po_gong', {}) or {}
        if _ypg.get('吉凶') == '吉':
            bonus += 8
            matched_patterns.append('+8 日禽得地(泊{})'.format(_ypg.get('宫', '') + '宫'))
        elif _ypg.get('吉凶') == '凶':
            bonus -= 8
            matched_patterns.append('-8 日禽失地(泊{})'.format(_ypg.get('宫', '') + '宫'))
    except Exception:
        yanqin_detail = {}
    # 三煞方禁忌（《要诀》"日课不可犯"；日时内最忌从重，年月外从轻）
    #   2026-09-05 接入：犯三煞作负分禁忌，不推翻斗首一票否决，只降综合分/降评级
    san_sha_penalty = 0
    if san_sha['hit']:
        inner = any(x in san_sha['hit_pillars'] for x in ('日', '时'))
        san_sha_penalty = -15 if inner else -8
        bonus += san_sha_penalty
        matched_patterns.append(f'{san_sha_penalty} {san_sha["level"]}')

    # 3.5) 择日类型类神吉应（2026-09-06 方案A-L3 接线：事件类神入课吉应 → 加分/减分）
    #   接入点：add_year 权威骨架 + 加分项之后、综合分合成之前——与三煞禁忌同级作微调项。
    #   吉应 +4（类神入传/临长生/加日辰实）、凶应 -6（类神受克/乘虎玄/加日辰空）、平 ±0（不入传只减应验）。
    leishen_detail = {}
    if zeri_type and sanchuan:
        try:
            from engine.leishen_engine import judge_zeri_leishen, get_xunkong
            _sc_ls = [sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
            # 三传可能带干支全名（古例口径"甲子"）→ 取地支末字
            _sc_ls = [str(z)[-1] if str(z) else '' for z in _sc_ls]
            _kong_ls = list(kong) if kong else get_xunkong(day_pillar[0], day_pillar[1])
            # 干上/支上神（六壬寄宫：甲寅乙辰丙戊巳丁己未庚申辛戌壬亥癸丑）
            _JIG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
                    '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}
            _gs_ls = (tiandi_pan or {}).get(_JIG.get(day_pillar[0], ''), '')
            _zs_ls = (tiandi_pan or {}).get(day_pillar[1], '')
            _ls = judge_zeri_leishen(
                zeri_type, _sc_ls,
                gan_shang=_gs_ls, zhi_shang=_zs_ls, kong=_kong_ls,
                chu_tj=(tianjiang_map or {}).get(_sc_ls[0], '') if _sc_ls[0] else '',
                zhong_tj=(tianjiang_map or {}).get(_sc_ls[1], '') if _sc_ls[1] else '',
                mo_tj=(tianjiang_map or {}).get(_sc_ls[2], '') if _sc_ls[2] else '',
                ri_gan=day_pillar[0], ri_zhi=day_pillar[1], tai_sui=nian_zhi or '',
                # 2026-09-06 随山向重排：丧葬/祭祀主类神=山家支+向首支（安葬立碑看山向）
                shan=shan)
            if _ls and _ls.get('end'):
                _leq = {'吉': 4, '凶': -6, '平': 0}.get(_ls['end'], 0)
                if _leq:
                    bonus += _leq
                    matched_patterns.append(
                        f'{_leq:+d} {zeri_type}类神吉应[{_ls.get("leishen", "")}]({_ls.get("narr", "")[:16]})')
                leishen_detail = _ls
        except Exception:
            leishen_detail = {}

    # 3) 综合分 = 禄马贵人权威骨架 + 加分项
    total_score = round(luma_base + bonus, 1)
    # 【2026-09-06 铁律硬闸·禄马贵人发三传】六壬未达标(<2)的课，加分项再高也不得满分/上上吉：
    #   综合分封顶 89（配合 daliuren_luma_guiren 六壬分降档，双闸防"base灌满+bonus顶回100"）
    try:
        _fc_ls = (luma_detail or {}).get('sanchuan_luma_count', 0)
        if _fc_ls < 2 and total_score > 89:
            total_score = 89
    except Exception:
        pass
    # 斗首贡献加分（六想增量 + 三元三武 + 凶在外吉在内）——供前端"斗首/到向/六壬"拆解
    doushou_bonus = doushou_delta + (15 if sanyuan_check['is_first_jike'] else 8 if sanyuan_check['grade'] else 0) + (jx_score if jx_score > 0 else 0)

    # 【2026-09-07 前端SUMMARY补齐·互禄互贵】与批量优化器顶格判定同源（check_hulu_hugui）。
    #   生成如 "\n互禄互贵: 命中(互禄4项+互贵3项)" 的展示片段；未命中返回 ''，不影响旧输出。
    _hulu_hugui_summary = ''
    try:
        _hh = _LRM().check_hulu_hugui(
            year_pillar[0] if len(year_pillar) >= 2 else '甲',
            month_pillar[0] if len(month_pillar) >= 2 else '甲',
            day_pillar[0] if len(day_pillar) >= 2 else '甲',
            ben_ming_gan or '', shan,
            month_pillar[1] if len(month_pillar) >= 2 else '子')
        if _hh.get('is_mutual_lu_gui'):
            _hulu_n = int(_hh.get('hulu_count', 0) or 0)
            _hugui_n = int(_hh.get('hugui_count', 0) or 0)
            _hulu_hugui_summary = f'\n互禄互贵: 命中(互禄{_hulu_n}项+互贵{_hugui_n}项)'
    except Exception:
        _hulu_hugui_summary = ''

    # 4) 评级
    if vetoed:
        # 斗首凶在日时(内)：一票否决，压到 39 以下（平/凶域）+ 标记不宜
        total_score = min(total_score, 39)
        grade = '不宜'
    else:
        total_score = max(20, min(100, total_score))
        if total_score >= 90:
            grade = '上上吉'
        elif total_score >= 80:
            grade = '上吉'
        elif total_score >= 70:
            grade = '中吉'
        elif total_score >= 60:
            grade = '吉'
        elif total_score >= 40:
            grade = '平'
        else:
            grade = '凶'
    
    return {
        'shan': shan,
        'shan_jia': shan_jia,
        'xiang_shou': xiang_shou,
        'total_score': total_score,
        'grade': grade,
        # 详细结果
        'doushou': {
            'classes': doushou_classes,
            'yuanchen_check': yuan_check,
            'sanyuan_check': sanyuan_check,
            'jixiong_check': jixiong_check,
            'liuxiang_score': liuxiang_score,
        },
        'gong_patterns': gong_patterns,
        'daoshan_daoxiang': {
            'lu': lu_dsdx,
            'ma': ma_dsdx,
            'guiren': guiren_dsdx,
            'total_count': dsdx_count,
        },
        'huoma_huolu': huoma_huolu,
        'advanced_patterns': {
            '朝天格': chaotian,
            '归垣格': guiyuan,
            '罗纹格': luowen,
            '龙德课': longde,
        },
        'buyuan': buyuan,
        'san_sha': san_sha,              # 三煞方判定（《要诀》ZR_15_02 禁忌；2026-09-05）
        'san_sha_penalty': san_sha_penalty,  # 三煞扣分（日时内-15/年月外-8）
        'sizhu_patterns': sizhu_patterns,  # 斗首四柱结构格局（天地同流/一气等；2026-09-05 接入）
        'yanqin_detail': yanqin_detail,  # 演禽窃要（山宿/生克/高禽/泊宫；2026-09-05 接入）
        'matched_patterns': matched_patterns,
        # 统一口径拆解（2026-08-31）：禄马贵人骨架 + 加分项 + 一票否决标记
        'luma_base': round(luma_base, 1),
        'luma_detail': luma_detail,
        'bonus': round(bonus, 1),
        # 择日类型类神吉应（2026-09-06 方案A-L3：{end,narr,leishen,zhi_list,tianjiang_table}）
        'leishen_detail': leishen_detail,
        # 斗首贡献加分（六想增量 + 三元三武 + 凶在外吉在内）——供前端"斗首/到向/六壬"拆解
        'doushou_bonus': round(doushou_bonus, 1),
        'vetoed': vetoed,
        'veto_reason': veto_reason,
        # 【2026-09-07 前端SUMMARY补齐】互禄互贵命中：与批量优化器顶格判定同源
        #   （DaLiuRenLuMaGuiRen.check_hulu_hugui：年干丙禄巳→月干贵人…交叉互禄互贵），
        #   使前端 summary 能解释"互禄互贵通道"顶格课的依据（原来只显示 到山到向/拱格=0）。
        '_hulu_hugui_summary': _hulu_hugui_summary,
        'summary': f'[{grade}] {shan}山{xiang_shou}向 评分{total_score}分\n' +
                   yuan_check['recommendation'] + '\n' +
                   (sanyuan_check['grade'] + '\n' if sanyuan_check['grade'] else '') +
                   f'拱格: {len([p for p in gong_patterns if p["matched"]])}个, ' +
                   f'到山到向: {dsdx_count}项, ' +
                   f'活禄马: {huoma_huolu["count"]}项' +
                   (_hulu_hugui_summary or ''),
    }


# ══════════════════════════════════════════════════════════════
# 向后兼容导出
# ══════════════════════════════════════════════════════════════

def build_60day_table():
    """构建六十日相替定局表（向后兼容）"""
    table = {}
    for gan_key, yin_month in WUHU_DUN.items():
        start_idx = JIAZI_60.index(yin_month)
        for i in range(60):
            actual_idx = (start_idx + i) % 60
            actual_gz = JIAZI_60[actual_idx]
            sg_idx = i % 12
            state = SHENGONG_ORDER[sg_idx]
            table[(gan_key, i)] = {
                'ganzhi': actual_gz, 'state': state,
                'is_xiang': state in SIX_XIANG,
            }
    return table


def get_wuxing_shengong(wx: str) -> dict:
    """正五行十二长生宫"""
    CHANGSHENG = {'木':'亥','火':'寅','金':'巳','水':'申','土':'申'}
    cs = CHANGSHENG.get(wx, '申')
    cs_idx = ZHI_LIST.index(cs)
    result = {}
    for i, state in enumerate(SHENGONG_ORDER):
        zhi = ZHI_LIST[(cs_idx + i) % 12]
        result[zhi] = state
    return result
