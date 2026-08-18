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
        'has_xiong': tanguan > 0 or pogui > 0,
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


# ══════════════════════════════════════════════════════════════
# F. 综合评分
# ══════════════════════════════════════════════════════════════

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
                       nian_zhi: str = None) -> dict:
    """
    完整的仪度六壬择日分析

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
    
    # === F. 综合评分 ===
    total_score = liuxiang_score['score']
    matched_patterns = []
    
    # 斗首得分
    if sanyuan_check['is_first_jike']:
        total_score += 15
        matched_patterns.append(f'+15 {sanyuan_check["grade"]}')
    elif sanyuan_check['grade']:
        total_score += 8
        matched_patterns.append(f'+8 {sanyuan_check["grade"]}')
    
    if jixiong_check['is_ideal']:
        total_score += jixiong_check['score']
        matched_patterns.append(f'+{jixiong_check["score"]} 凶在外吉在内')
    
    # 拱格得分
    for gp in gong_patterns:
        if gp['matched']:
            total_score += 5
            matched_patterns.append(f'+5 {gp["name"]}')
    
    # 到山到向得分
    dsdx_count = sum([lu_dsdx['is_daoshan_daoxiang'], ma_dsdx['is_daoshan_daoxiang'], guiren_dsdx['is_daoshan_daoxiang']])
    total_score += dsdx_count * 5
    if dsdx_count > 0:
        matched_patterns.append(f'+{dsdx_count*5} {dsdx_count}项到山到向')
    
    # 活马活禄
    if huoma_huolu['count'] > 0:
        total_score += huoma_huolu['count'] * 5
        matched_patterns.append(f'+{huoma_huolu["count"]*5} 活禄马({huoma_huolu["count"]}项)')
    
    # 高级课格
    for pattern in [chaotian, guiyuan, luowen, longde]:
        if pattern.get('matched'):
            total_score += 5
            matched_patterns.append(f'+5 {pattern["name"]}')
    
    # 补元
    if buyuan['method']:
        total_score += 3
        matched_patterns.append(f'+3 {buyuan["method"]}')
    
    total_score = max(20, min(100, total_score))
    
    # 评级
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
        'matched_patterns': matched_patterns,
        'summary': f'[{grade}] {shan}山{xiang_shou}向 评分{total_score}分\n' +
                   yuan_check['recommendation'] + '\n' +
                   (sanyuan_check['grade'] + '\n' if sanyuan_check['grade'] else '') +
                   f'拱格: {len([p for p in gong_patterns if p["matched"]])}个, ' +
                   f'到山到向: {dsdx_count}项, ' +
                   f'活禄马: {huoma_huolu["count"]}项',
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
