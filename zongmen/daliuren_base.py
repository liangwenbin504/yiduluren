#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬基础计算模块
提供天将、旬空、丁神、月将等基础计算功能
"""

from typing import Dict, List, Tuple, Optional

# ==================== 基础常量 ====================

# 十天干
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 十二地支
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十二天将
TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙', 
              '天空', '白虎', '太常', '玄武', '太阴', '天后']

# 六十甲子
JIA_ZI_60 = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

# 六丁神（旬内丁神）
LIU_DING = {
    '甲子': '丁卯', '甲戌': '丁丑', '甲申': '丁亥',
    '甲午': '丁酉', '甲辰': '丁未', '甲寅': '丁巳'
}

# 旬空映射
XUN_KONG = {
    '甲子': ['戌', '亥'],
    '甲戌': ['申', '酉'],
    '甲申': ['午', '未'],
    '甲午': ['辰', '巳'],
    '甲辰': ['寅', '卯'],
    '甲寅': ['子', '丑']
}

# 月将（太阳过宫）
YUE_JIANG = {
    '子': '丑',  # 正月建寅，月将在丑
    '丑': '子',  # 二月建卯，月将在子
    '寅': '亥',  # 三月建辰，月将在亥
    '卯': '戌',  # 四月建巳，月将在戌
    '辰': '酉',  # 五月建午，月将在酉
    '巳': '申',  # 六月建未，月将在申
    '午': '未',  # 七月建申，月将在未
    '未': '午',  # 八月建酉，月将在午
    '申': '巳',  # 九月建戌，月将在巳
    '酉': '辰',  # 十月建亥，月将在辰
    '戌': '卯',  # 十一月建子，月将在卯
    '亥': '寅'   # 十二月建丑，月将在寅
}

# 贵人地支（昼夜贵人）
GUI_REN_ZHI = {
    '甲': {'day': '丑', 'night': '未'},
    '乙': {'day': '子', 'night': '申'},
    '丙': {'day': '亥', 'night': '酉'},
    '丁': {'day': '酉', 'night': '亥'},
    '戊': {'day': '丑', 'night': '未'},
    '己': {'day': '子', 'night': '申'},
    '庚': {'day': '未', 'night': '丑'},
    '辛': {'day': '午', 'night': '寅'},
    '壬': {'day': '卯', 'night': '巳'},
    '癸': {'day': '巳', 'night': '卯'}
}

# 天将顺序（贵人顺逆排布）
TIAN_JIANG_ORDER = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙', 
                    '天空', '白虎', '太常', '玄武', '太阴', '天后']

# 天将五行属性
TIAN_JIANG_WU_XING = {
    '贵人': '土', '螣蛇': '火', '朱雀': '火', '六合': '木',
    '勾陈': '土', '青龙': '木', '天空': '土', '白虎': '金',
    '太常': '土', '玄武': '水', '太阴': '金', '天后': '水'
}

# 天将吉凶
TIAN_JIANG_JI_XIONG = {
    '贵人': '吉', '螣蛇': '凶', '朱雀': '凶', '六合': '吉',
    '勾陈': '凶', '青龙': '吉', '天空': '凶', '白虎': '凶',
    '太常': '吉', '玄武': '凶', '太阴': '吉', '天后': '吉'
}

# 神煞映射（简化版）
SHEN_SHA_MAP = {
    '丧门': {'year_offset': 2},  # 岁前二辰
    '吊客': {'year_offset': -2},  # 岁后二辰
    '病符': {'year_offset': -1},  # 旧太岁
    '岁破': {'year_offset': 6},  # 岁冲
}

# 月内神煞
YUE_SHEN_SHA = {
    '生气': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  # 正月起子顺行
    '死气': [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5],  # 正月起午顺行
    '月厌': [8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10, 9],  # 正月起戌逆行
    '天喜': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1],  # 正月起丑顺行
}

# 地支阴阳
ZHI_YIN_YANG = {
    '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴',
    '辰': '阳', '巳': '阴', '午': '阳', '未': '阴',
    '申': '阳', '酉': '阴', '戌': '阳', '亥': '阴'
}

# 天干阴阳
GAN_YIN_YANG = {
    '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴',
    '戊': '阳', '己': '阴', '庚': '阳', '辛': '阴',
    '壬': '阳', '癸': '阴'
}

# 地支五行
ZHI_WU_XING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 天干五行
GAN_WU_XING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

# ==================== 基础计算函数 ====================

def get_xun(ri_gan_zhi: str) -> str:
    """
    根据日干支获取所属旬
    """
    if ri_gan_zhi not in JIA_ZI_60:
        return ''
    
    idx = JIA_ZI_60.index(ri_gan_zhi)
    xun_idx = (idx // 10) * 10
    return JIA_ZI_60[xun_idx]

def get_kong_wang(ri_gan_zhi: str) -> List[str]:
    """
    获取旬空地支
    """
    xun = get_xun(ri_gan_zhi)
    return XUN_KONG.get(xun, [])

def get_ding_shen(ri_gan_zhi: str) -> str:
    """
    获取旬内丁神
    """
    xun = get_xun(ri_gan_zhi)
    return LIU_DING.get(xun, '')

def get_yue_jiang(yue: str) -> str:
    """
    根据月建获取月将
    """
    return YUE_JIANG.get(yue, '')

def get_yin_yang(element: str, is_gan: bool = True) -> str:
    """
    获取阴阳属性
    """
    if is_gan:
        return GAN_YIN_YANG.get(element, '阳')
    else:
        return ZHI_YIN_YANG.get(element, '阳')

def get_wu_xing(element: str, is_gan: bool = True) -> str:
    """
    获取五行属性
    """
    if is_gan:
        return GAN_WU_XING.get(element, '土')
    else:
        return ZHI_WU_XING.get(element, '土')

def get_sheng_ke(element1: str, element2: str, is_gan1: bool = True, is_gan2: bool = True) -> str:
    """
    判断五行生克关系
    """
    wx1 = get_wu_xing(element1, is_gan1)
    wx2 = get_wu_xing(element2, is_gan2)
    
    sheng_cycle = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    ke_cycle = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    if wx1 == wx2:
        return '比和'
    elif sheng_cycle.get(wx1) == wx2:
        return '生'
    elif sheng_cycle.get(wx2) == wx1:
        return '被生'
    elif ke_cycle.get(wx1) == wx2:
        return '克'
    elif ke_cycle.get(wx2) == wx1:
        return '被克'
    else:
        return '未知'

def get_lu_shen(ri_gan: str) -> str:
    """
    获取禄神（日干之禄）
    甲禄在寅，乙禄在卯，丙戊禄在巳，丁己禄在午，
    庚禄在申，辛禄在酉，壬禄在亥，癸禄在子
    """
    lu_map = {
        '甲': '寅', '乙': '卯',
        '丙': '巳', '丁': '午', '戊': '巳', '己': '午',
        '庚': '申', '辛': '酉',
        '壬': '亥', '癸': '子'
    }
    return lu_map.get(ri_gan, '')

def get_gui_shen(ri_gan: str) -> List[str]:
    """
    获取鬼煞（克日干者）
    """
    gui_map = {
        '甲': ['庚', '辛', '申', '酉'],
        '乙': ['庚', '辛', '申', '酉'],
        '丙': ['壬', '癸', '亥', '子'],
        '丁': ['壬', '癸', '亥', '子'],
        '戊': ['甲', '乙', '寅', '卯'],
        '己': ['甲', '乙', '寅', '卯'],
        '庚': ['丙', '丁', '巳', '午'],
        '辛': ['丙', '丁', '巳', '午'],
        '壬': ['戊', '己', '辰', '戌', '丑', '未'],
        '癸': ['戊', '己', '辰', '戌', '丑', '未']
    }
    return gui_map.get(ri_gan, [])

def get_cai_shen(ri_gan: str) -> List[str]:
    """
    获取财煞（日干克者）
    """
    cai_map = {
        '甲': ['戊', '己', '辰', '戌', '丑', '未'],
        '乙': ['戊', '己', '辰', '戌', '丑', '未'],
        '丙': ['庚', '辛', '申', '酉'],
        '丁': ['庚', '辛', '申', '酉'],
        '戊': ['壬', '癸', '亥', '子'],
        '己': ['壬', '癸', '亥', '子'],
        '庚': ['甲', '乙', '寅', '卯'],
        '辛': ['甲', '乙', '寅', '卯'],
        '壬': ['丙', '丁', '巳', '午'],
        '癸': ['丙', '丁', '巳', '午']
    }
    return cai_map.get(ri_gan, [])

def get_zhang_sheng(ri_gan: str) -> List[str]:
    """
    获取长生
    甲木长生在亥，乙木长生在午，丙火长生在寅，丁火长生在酉，
    戊土长生在寅，己土长生在酉，庚金长生在巳，辛金长生在子，
    壬水长生在申，癸水长生在卯
    """
    zs_map = {
        '甲': ['亥'], '乙': ['午'],
        '丙': ['寅'], '丁': ['酉'],
        '戊': ['寅'], '己': ['酉'],
        '庚': ['巳'], '辛': ['子'],
        '壬': ['申'], '癸': ['卯']
    }
    return zs_map.get(ri_gan, [])

def get_di_pan_zhi(ri_gan_zhi: str, tian_pan_zhi: str) -> str:
    """
    根据地盘支找天盘支（简化版，实际需要月将加时）
    这里提供基础映射关系
    """
    # 简化处理：伏吟
    return tian_pan_zhi

def get_tian_jiang_order(ri_gan_zhi: str, is_day: bool = True) -> List[str]:
    """
    获取天将排列顺序
    贵人顺逆排布
    """
    # 简化版：返回标准顺序
    if is_day:
        return TIAN_JIANG.copy()
    else:
        return TIAN_JIANG[::-1]

def get_gui_ren(ri_gan: str, is_day: bool = True) -> str:
    """
    获取贵人（昼夜贵人）
    """
    gui_info = GUI_REN_ZHI.get(ri_gan, {})
    if is_day:
        return gui_info.get('day', '丑')
    else:
        return gui_info.get('night', '未')

def get_tian_jiang_at_zhi(ri_gan: str, zhi: str, is_day: bool = True) -> str:
    """
    根据日干和地支获取天将
    简化版：贵人加临地盘支，顺逆排布
    """
    gui_ren = get_gui_ren(ri_gan, is_day)
    
    # 地支配数
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    gui_idx = zhi_map.get(gui_ren, 0)
    target_idx = zhi_map.get(zhi, 0)
    
    # 计算天将索引（简化：顺行）
    offset = (target_idx - gui_idx) % 12
    tian_jiang_idx = offset % 12
    
    return TIAN_JIANG_ORDER[tian_jiang_idx]

def get_tian_jiang_full_pailie(ri_gan: str, shi: str, is_day: bool = True) -> Dict[str, str]:
    """
    完整天将排盘：贵人加临地盘，顺逆排布十二天将
    ri_gan: 日干
    shi: 时辰（用于判断昼夜）
    is_day: 是否白天（True=白天，False=夜晚）
    
    返回：{地盘支：天将}
    """
    gui_ren = get_gui_ren(ri_gan, is_day)
    
    # 地支配数
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    gui_idx = zhi_map.get(gui_ren, 0)
    
    # 判断贵人顺逆：贵人在地盘亥子丑寅卯辰为顺行，在巳午未申酉戌为逆行
    shun_xing_positions = ['亥', '子', '丑', '寅', '卯', '辰']
    ni_xing_positions = ['巳', '午', '未', '申', '酉', '戌']
    
    if gui_ren in shun_xing_positions:
        shun_xing = True
    elif gui_ren in ni_xing_positions:
        shun_xing = False
    else:
        # 默认顺行
        shun_xing = True
    
    # 排布天将
    tian_jiang_result = {}
    for i, di_zhi in enumerate(DI_ZHI):
        if shun_xing:
            tian_jiang_idx = (i - gui_idx) % 12
        else:
            tian_jiang_idx = (gui_idx - i) % 12
        
        tian_jiang_result[di_zhi] = TIAN_JIANG_ORDER[tian_jiang_idx]
    
    return tian_jiang_result

def get_tian_jiang_sheng_ke(tian_jiang: str, zhi: str) -> str:
    """
    判断天将与地支的生克关系
    """
    tj_wx = TIAN_JIANG_WU_XING.get(tian_jiang, '土')
    zhi_wx = ZHI_WU_XING.get(zhi, '土')
    
    return get_sheng_ke(tj_wx, zhi_wx, is_gan1=False, is_gan2=False)

def get_tian_jiang_ke_ri(tian_jiang: str, ri_gan: str) -> str:
    """
    判断天将是否克日干
    返回：'克日'、'生日'、'比和'、'被克'、'被生'
    """
    tj_wx = TIAN_JIANG_WU_XING.get(tian_jiang, '土')
    ri_wx = GAN_WU_XING.get(ri_gan, '土')
    
    return get_sheng_ke(tj_wx, ri_wx, is_gan1=False, is_gan2=True)

def get_ke_ti_ge_ju(chu_chuan: str, zhong_chuan: str, mo_chuan: str, 
                    ri_gan: str, ri_zhi: str) -> Dict:
    """
    判断课体格局（九宗门分类）
    
    九宗门：
    1. 元首课：上克下
    2. 重审课：下克上
    3. 知一课：二上克下或二下克上
    4. 涉害课：涉害深浅
    5. 昴星课：无克贼
    6. 别责课：四课有两课相同
    7. 八专课：干支同位
    8. 伏吟课：天地盘相同
    9. 反吟课：天地盘对冲
    
    返回格局信息
    """
    result = {
        'ge_ju': [],
        'zong_men': '',
        'te_shu_ge_ju': []
    }
    
    # 伏吟：三传皆相同
    if chu_chuan == zhong_chuan == mo_chuan:
        result['ge_ju'].append('伏吟课')
        result['zong_men'] = '伏吟'
    
    # 反吟：初传与末传对冲
    zhi_chong = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    if zhi_chong.get(chu_chuan) == mo_chuan:
        result['ge_ju'].append('反吟课')
        result['zong_men'] = '反吟'
    
    # 八专：干支同位（简化判断）
    if ri_gan == ri_zhi:
        result['ge_ju'].append('八专课')
        result['zong_men'] = '八专'
    
    # 连茹：三传连续
    zhi_xu = {z: i for i, z in enumerate(DI_ZHI)}
    chu_idx = zhi_xu.get(chu_chuan, 0)
    zhong_idx = zhi_xu.get(zhong_chuan, 0)
    mo_idx = zhi_xu.get(mo_chuan, 0)
    
    # 顺连茹
    if (zhong_idx - chu_idx) % 12 == 1 and (mo_idx - zhong_idx) % 12 == 1:
        result['ge_ju'].append('顺连茹')
        result['te_shu_ge_ju'].append('连茹')
    
    # 逆连茹
    if (chu_idx - zhong_idx) % 12 == 1 and (zhong_idx - mo_idx) % 12 == 1:
        result['ge_ju'].append('逆连茹')
        result['te_shu_ge_ju'].append('连茹')
    
    # 三合局
    san_he = {
        '申子辰': '水局', '亥卯未': '木局',
        '寅午戌': '火局', '巳酉丑': '金局'
    }
    chuan_set = {chu_chuan, zhong_chuan, mo_chuan}
    for he_str, ju_name in san_he.items():
        if set(he_str).issubset(chuan_set):
            result['ge_ju'].append(f'三合{ju_name}')
            result['te_shu_ge_ju'].append('三合局')
            break
    
    # 三会局
    san_hui = {
        '亥子丑': '水局', '寅卯辰': '木局',
        '巳午未': '火局', '申酉戌': '金局'
    }
    for hui_str, ju_name in san_hui.items():
        if set(hui_str).issubset(chuan_set):
            result['ge_ju'].append(f'三会{ju_name}')
            result['te_shu_ge_ju'].append('三会局')
            break
    
    # 进退连珠
    if (zhong_idx - chu_idx) % 12 == 1 and (mo_idx - zhong_idx) % 12 == 1:
        result['ge_ju'].append('进茹')
    elif (chu_idx - zhong_idx) % 12 == 1 and (zhong_idx - mo_idx) % 12 == 1:
        result['ge_ju'].append('退茹')
    
    # 如果以上都不是，默认为昴星课
    if not result['zong_men']:
        result['zong_men'] = '昴星'
    
    return result

def get_yue_jiang_by_month(yue: str) -> str:
    """
    根据月建获取月将
    """
    return YUE_JIANG.get(yue, '')

def get_tian_pan_zhi(yue_jiang: str, shi: str) -> Dict[str, str]:
    """
    计算天盘地支（月将加时）
    月将加在地盘时支上，顺行十二辰
    """
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    
    yue_jiang_idx = zhi_map.get(yue_jiang, 0)
    shi_idx = zhi_map.get(shi, 0)
    
    # 月将加在时支上
    start_offset = shi_idx
    
    # 天盘：月将从时支开始顺排
    tian_pan = {}
    for i, di_zhi in enumerate(DI_ZHI):
        tian_idx = (yue_jiang_idx + i) % 12
        tian_pan[di_zhi] = DI_ZHI[tian_idx]
    
    return tian_pan

def get_nian_zhi(year: int) -> str:
    """
    根据年份获取年支（太岁）
    """
    # 简化：以 2024 年为甲辰年计算
    base_year = 2024
    base_zhi_idx = 4  # 辰
    
    offset = (year - base_year) % 12
    zhi_idx = (base_zhi_idx + offset) % 12
    
    return DI_ZHI[zhi_idx]

def get_sang_men(year: int) -> str:
    """
    获取丧门（岁前二辰）
    """
    nian_zhi = get_nian_zhi(year)
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    nian_idx = zhi_map.get(nian_zhi, 0)
    
    # 岁前二辰
    sang_men_idx = (nian_idx + 2) % 12
    return DI_ZHI[sang_men_idx]

def get_diao_ke(year: int) -> str:
    """
    获取吊客（岁后二辰）
    """
    nian_zhi = get_nian_zhi(year)
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    nian_idx = zhi_map.get(nian_zhi, 0)
    
    # 岁后二辰
    diao_ke_idx = (nian_idx - 2) % 12
    return DI_ZHI[diao_ke_idx]

def get_bing_fu(year: int) -> str:
    """
    获取病符（旧太岁）
    """
    nian_zhi = get_nian_zhi(year)
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    nian_idx = zhi_map.get(nian_zhi, 0)
    
    # 旧太岁（后退一位）
    bing_fu_idx = (nian_idx - 1) % 12
    return DI_ZHI[bing_fu_idx]

def get_yue_shen_sha(yue: str, sha_name: str) -> str:
    """
    获取月内神煞
    yue: 月建（子丑寅卯...）
    sha_name: 神煞名（生气、死气、月厌、天喜）
    """
    yue_map = {z: i for i, z in enumerate(DI_ZHI)}
    yue_idx = yue_map.get(yue, 0)
    
    sha_list = YUE_SHEN_SHA.get(sha_name, [])
    if not sha_list or yue_idx >= len(sha_list):
        return ''
    
    sha_idx = sha_list[yue_idx]
    return DI_ZHI[sha_idx]

def get_shen_sha_extended(ri_gan_zhi: str, zhi: str, year: int = 2024, yue: str = '') -> List[str]:
    """
    获取扩展神煞
    """
    shen_sha = get_shen_sha(ri_gan_zhi, zhi)
    
    # 年神煞
    nian_zhi = get_nian_zhi(year)
    zhi_map = {z: i for i, z in enumerate(DI_ZHI)}
    zhi_idx = zhi_map.get(zhi, 0)
    nian_idx = zhi_map.get(nian_zhi, 0)
    
    # 丧门
    if zhi_idx == (nian_idx + 2) % 12:
        shen_sha.append('丧门')
    
    # 吊客
    if zhi_idx == (nian_idx - 2) % 12:
        shen_sha.append('吊客')
    
    # 病符
    if zhi_idx == (nian_idx - 1) % 12:
        shen_sha.append('病符')
    
    # 岁破
    if zhi_idx == (nian_idx + 6) % 12:
        shen_sha.append('岁破')
    
    # 月神煞
    if yue:
        yue_idx = zhi_map.get(yue, 0)
        
        # 生气
        if zhi_idx == yue_idx + 1:  # 简化
            shen_sha.append('生气')
        
        # 死气
        if zhi_idx == (yue_idx + 7) % 12:
            shen_sha.append('死气')
    
    return shen_sha

def get_shen_sha(ri_gan_zhi: str, zhi: str) -> List[str]:
    """
    获取神煞（简化版）
    """
    shen_sha = []
    
    # 判断是否旬空
    kong_wang = get_kong_wang(ri_gan_zhi)
    if zhi in kong_wang:
        shen_sha.append('旬空')
    
    # 判断是否丁神
    ding = get_ding_shen(ri_gan_zhi)
    if zhi == ding:
        shen_sha.append('丁神')
    
    return shen_sha

# ==================== 课例数据增强函数 ====================

def enhance_ke_li_data(ke_li: Dict, year: int = 2024) -> Dict:
    """
    增强课例数据，添加旬空、丁神、神煞、天将、课体格局等信息
    """
    enhanced = ke_li.copy()
    
    ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
    if not ri_gan_zhi:
        return enhanced
    
    # 提取日干日支
    ri_gan = ri_gan_zhi[0] if len(ri_gan_zhi) >= 1 else ''
    ri_zhi = ri_gan_zhi[1] if len(ri_gan_zhi) >= 2 else ''
    
    # 获取时辰（用于天将排布）
    shi = ke_li.get('shi', '')
    yue = ke_li.get('yue', '')
    
    # 添加旬信息
    enhanced['xun'] = get_xun(ri_gan_zhi)
    
    # 添加旬空
    enhanced['kong_wang'] = get_kong_wang(ri_gan_zhi)
    
    # 添加丁神
    enhanced['ding_shen'] = get_ding_shen(ri_gan_zhi)
    
    # 添加禄神
    enhanced['lu_shen'] = get_lu_shen(ri_gan)
    
    # 添加鬼煞
    enhanced['gui_shen'] = get_gui_shen(ri_gan)
    
    # 添加财煞
    enhanced['cai_shen'] = get_cai_shen(ri_gan)
    
    # 添加长生
    enhanced['zhang_sheng'] = get_zhang_sheng(ri_gan)
    
    # 添加贵人（昼夜）
    # 简化：白天用昼贵人
    enhanced['gui_ren_day'] = get_gui_ren(ri_gan, is_day=True)
    enhanced['gui_ren_night'] = get_gui_ren(ri_gan, is_day=False)
    
    # 添加完整天将排盘
    enhanced['tian_jiang_pailie'] = get_tian_jiang_full_pailie(ri_gan, shi, is_day=True)
    
    # 添加三传天将
    chu_chuan = ke_li.get('chu_chuan', '')
    zhong_chuan = ke_li.get('zhong_chuan', '')
    mo_chuan = ke_li.get('mo_chuan', '')
    
    tian_jiang_pailie = enhanced['tian_jiang_pailie']
    enhanced['chu_tian_jiang'] = tian_jiang_pailie.get(chu_chuan, '')
    enhanced['zhong_tian_jiang'] = tian_jiang_pailie.get(zhong_chuan, '')
    enhanced['mo_tian_jiang'] = tian_jiang_pailie.get(mo_chuan, '')
    
    # 添加天将生克
    enhanced['chu_tian_jiang_ke'] = get_tian_jiang_ke_ri(enhanced['chu_tian_jiang'], ri_gan)
    enhanced['zhong_tian_jiang_ke'] = get_tian_jiang_ke_ri(enhanced['zhong_tian_jiang'], ri_gan)
    enhanced['mo_tian_jiang_ke'] = get_tian_jiang_ke_ri(enhanced['mo_tian_jiang'], ri_gan)
    
    # 添加课体格局
    ge_ju_info = get_ke_ti_ge_ju(chu_chuan, zhong_chuan, mo_chuan, ri_gan, ri_zhi)
    enhanced['ke_ti_ge_ju'] = ge_ju_info['ge_ju']
    enhanced['zong_men'] = ge_ju_info['zong_men']
    enhanced['te_shu_ge_ju'] = ge_ju_info['te_shu_ge_ju']
    
    # 添加月将
    if yue:
        enhanced['yue_jiang'] = get_yue_jiang_by_month(yue)
    
    # 添加天盘（简化）
    if enhanced.get('yue_jiang') and shi:
        enhanced['tian_pan'] = get_tian_pan_zhi(enhanced['yue_jiang'], shi)
    
    # 添加神煞（三传）
    enhanced['chu_chuan_shen_sha'] = get_shen_sha_extended(ri_gan_zhi, chu_chuan, year, yue)
    enhanced['zhong_chuan_shen_sha'] = get_shen_sha_extended(ri_gan_zhi, zhong_chuan, year, yue)
    enhanced['mo_chuan_shen_sha'] = get_shen_sha_extended(ri_gan_zhi, mo_chuan, year, yue)
    
    # 判断三传是否空亡
    kong_wang = enhanced['kong_wang']
    enhanced['chu_kong'] = chu_chuan in kong_wang
    enhanced['zhong_kong'] = zhong_chuan in kong_wang
    enhanced['mo_kong'] = mo_chuan in kong_wang
    
    # 判断三传是否丁神
    ding = enhanced['ding_shen']
    enhanced['chu_ding'] = chu_chuan == ding
    enhanced['zhong_ding'] = zhong_chuan == ding
    enhanced['mo_ding'] = mo_chuan == ding
    
    # 添加年神煞
    enhanced['sang_men'] = get_sang_men(year)
    enhanced['diao_ke'] = get_diao_ke(year)
    enhanced['bing_fu'] = get_bing_fu(year)
    
    # 判断三传是否有丧门吊客
    enhanced['chu_sang_men'] = chu_chuan == enhanced['sang_men']
    enhanced['chu_diao_ke'] = chu_chuan == enhanced['diao_ke']
    
    # 添加月神煞
    if yue:
        enhanced['yue_sheng_qi'] = get_yue_shen_sha(yue, '生气')
        enhanced['yue_si_qi'] = get_yue_shen_sha(yue, '死气')
    
    return enhanced

# ==================== 测试函数 ====================

def test_basic_functions():
    """测试基础功能"""
    print("="*70)
    print("  大六壬基础计算功能测试")
    print("="*70)
    print()
    
    test_cases = ['甲子', '乙丑', '丙寅', '庚申', '辛酉', '壬戌', '癸亥']
    
    for ri_gan_zhi in test_cases:
        print(f"\n日干支：{ri_gan_zhi}")
        print(f"  旬：{get_xun(ri_gan_zhi)}")
        print(f"  旬空：{get_kong_wang(ri_gan_zhi)}")
        print(f"  丁神：{get_ding_shen(ri_gan_zhi)}")
        
        ri_gan = ri_gan_zhi[0]
        print(f"  禄神：{get_lu_shen(ri_gan)}")
        print(f"  鬼煞：{get_gui_shen(ri_gan)}")
        print(f"  财煞：{get_cai_shen(ri_gan)}")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    test_basic_functions()
