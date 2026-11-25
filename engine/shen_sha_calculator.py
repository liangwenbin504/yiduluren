#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬完整神煞计算模块（增强版）
包含：日辰神煞、月建神煞、年支神煞、季节神煞、旬煞等
实现完整的月煞、日煞系统
"""

from typing import Dict, List, Optional, Tuple


class ShenShaCalculator:
    """神煞计算器（增强版）"""
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 天干顺序
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 天干五行
    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
    }
    
    # 地支六合
    LIU_HE = {
        '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
        '辰': '酉', '巳': '申', '午': '未', '未': '午',
        '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
    }
    
    # 地支六冲
    LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    
    # 地支三合
    SAN_HE = {
        '申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金'
    }
    
    # 驿马 (按日支三合)
    YI_MA = {
        '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥'
    }
    
    # 桃花 (按日支三合)
    TAO_HUA = {
        '申子辰': '酉', '亥卯未': '子', '寅午戌': '卯', '巳酉丑': '午'
    }
    
    # 劫煞 (按日支三合)
    JIE_SHA = {
        '申子辰': '巳', '亥卯未': '申', '寅午戌': '亥', '巳酉丑': '寅'
    }
    
    # 灾煞 (按日支三合)
    ZAI_SHA = {
        '申子辰': '午', '亥卯未': '酉', '寅午戌': '子', '巳酉丑': '卯'
    }
    
    # 月煞（按月建）- 完整 12 个月
    # 天医 = 月建前二辰（正月辰顺行十二辰），依据《大六壬断案》评疏指正
    # 地医 = 天医对冲（正月戌顺行十二辰）
    YUE_SHA = {
        1: {'月建': '寅', '月破': '申', '月厌': '戌', '天德': '丁', '月德': '丁', '天喜': '戌', '天医': '辰', '死神': '巳', '死气': '午'},
        2: {'月建': '卯', '月破': '酉', '月厌': '酉', '天德': '坤', '月德': '申', '天喜': '亥', '天医': '巳', '死神': '午', '死气': '未'},
        3: {'月建': '辰', '月破': '戌', '月厌': '申', '天德': '壬', '月德': '壬', '天喜': '子', '天医': '午', '死神': '未', '死气': '申'},
        4: {'月建': '巳', '月破': '亥', '月厌': '未', '天德': '辛', '月德': '辛', '天喜': '丑', '天医': '未', '死神': '申', '死气': '酉'},
        5: {'月建': '午', '月破': '子', '月厌': '午', '天德': '乾', '月德': '亥', '天喜': '寅', '天医': '申', '死神': '酉', '死气': '戌'},
        6: {'月建': '未', '月破': '丑', '月厌': '巳', '天德': '甲', '月德': '甲', '天喜': '卯', '天医': '酉', '死神': '戌', '死气': '亥'},
        7: {'月建': '申', '月破': '寅', '月厌': '辰', '天德': '癸', '月德': '癸', '天喜': '辰', '天医': '戌', '死神': '亥', '死气': '子'},
        8: {'月建': '酉', '月破': '卯', '月厌': '卯', '天德': '艮', '月德': '寅', '天喜': '巳', '天医': '亥', '死神': '子', '死气': '丑'},
        9: {'月建': '戌', '月破': '辰', '月厌': '寅', '天德': '丙', '月德': '丙', '天喜': '午', '天医': '子', '死神': '丑', '死气': '寅'},
        10: {'月建': '亥', '月破': '巳', '月厌': '丑', '天德': '乙', '月德': '乙', '天喜': '未', '天医': '丑', '死神': '寅', '死气': '卯'},
        11: {'月建': '子', '月破': '午', '月厌': '子', '天德': '巽', '月德': '巳', '天喜': '申', '天医': '寅', '死神': '卯', '死气': '辰'},
        12: {'月建': '丑', '月破': '未', '月厌': '亥', '天德': '庚', '月德': '庚', '天喜': '酉', '天医': '卯', '死神': '辰', '死气': '巳'}
    }
    
    # 日煞（按日支）- 完整 12 地支
    # 2026-08-01 修正：'日支德_旧' 值错乱，改为通解 p138 支德表（子巳丑午寅未卯申辰酉巳戌午亥未子申丑酉寅戌卯亥辰）；
    # '日破' 原误取六冲值，改为通解 p138 六破表（子酉丑辰寅亥卯午辰丑巳申午卯未戌申巳酉子戌未亥寅）。
    RI_SHA = {
        '子': {'日禄': '亥', '日支德_旧': '巳', '日马': '寅', '日贵': '卯', '日破': '酉', '日害': '未'},
        '丑': {'日禄': '子', '日支德_旧': '午', '日马': '亥', '日贵': '子', '日破': '辰', '日害': '午'},
        '寅': {'日禄': '寅', '日支德_旧': '未', '日马': '申', '日贵': '丑', '日破': '亥', '日害': '巳'},
        '卯': {'日禄': '卯', '日支德_旧': '申', '日马': '巳', '日贵': '子', '日破': '午', '日害': '辰'},
        '辰': {'日禄': '巳', '日支德_旧': '酉', '日马': '寅', '日贵': '亥', '日破': '丑', '日害': '卯'},
        '巳': {'日禄': '午', '日支德_旧': '戌', '日马': '亥', '日贵': '酉', '日破': '申', '日害': '寅'},
        '午': {'日禄': '巳', '日支德_旧': '亥', '日马': '申', '日贵': '亥', '日破': '卯', '日害': '丑'},
        '未': {'日禄': '午', '日支德_旧': '子', '日马': '巳', '日贵': '子', '日破': '戌', '日害': '子'},
        '申': {'日禄': '申', '日支德_旧': '丑', '日马': '寅', '日贵': '丑', '日破': '巳', '日害': '亥'},
        '酉': {'日禄': '酉', '日支德_旧': '寅', '日马': '亥', '日贵': '午', '日破': '子', '日害': '戌'},
        '戌': {'日禄': '亥', '日支德_旧': '卯', '日马': '申', '日贵': '卯', '日破': '未', '日害': '酉'},
        '亥': {'日禄': '子', '日支德_旧': '辰', '日马': '巳', '日贵': '卯', '日破': '寅', '日害': '申'}
    }
    
    # 十干禄（按日干）
    SHI_GAN_LU = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
        '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    # 十干贵人（按日干）
    SHI_GAN_GUI_REN = {
        '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
        '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
        '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
        '癸': ['巳', '卯']
    }
    
    # 十干羊刃（按日干；通解 上卷 p138「日干神煞」阳刃表：甲卯乙辰丙午丁未戊午己未庚酉辛戌壬子癸丑）
    # 2026-08-01 憨爷拍板：由原阴刃（乙寅丁巳己巳辛申癸亥）对齐通解阳刃（子平标准）。
    SHI_GAN_YANG_REN = {
        '甲': '卯', '乙': '辰', '丙': '午', '丁': '未', '戊': '午',
        '己': '未', '庚': '酉', '辛': '戌', '壬': '子', '癸': '丑'
    }
    
    # 孤辰寡宿 (按年支三合局)
    GU_GUA = {
        '亥子丑': {'孤': '寅', '寡': '戌'},
        '寅卯辰': {'孤': '巳', '寡': '丑'},
        '巳午未': {'孤': '申', '寡': '辰'},
        '申酉戌': {'孤': '亥', '寡': '未'}
    }
    
    # 丧门吊客 (按年支)
    SANG_DIAO = {
        '子': {'丧门': '寅', '吊客': '戌'},
        '丑': {'丧门': '卯', '吊客': '亥'},
        '寅': {'丧门': '辰', '吊客': '子'},
        '卯': {'丧门': '巳', '吊客': '丑'},
        '辰': {'丧门': '午', '吊客': '寅'},
        '巳': {'丧门': '未', '吊客': '卯'},
        '午': {'丧门': '申', '吊客': '辰'},
        '未': {'丧门': '酉', '吊客': '巳'},
        '申': {'丧门': '戌', '吊客': '午'},
        '酉': {'丧门': '亥', '吊客': '未'},
        '戌': {'丧门': '子', '吊客': '申'},
        '亥': {'丧门': '丑', '吊客': '酉'}
    }
    
    # 病符 (年支前一位，子年前一位亥，丑年前一位子...)
    BING_FU = {
        '子': '亥', '丑': '子', '寅': '丑', '卯': '寅',
        '辰': '卯', '巳': '辰', '午': '巳', '未': '午',
        '申': '未', '酉': '申', '戌': '酉', '亥': '戌'
    }
    
    # 旬煞（通解 上卷 p138「六十甲子旬神煞」权威表；2026-08-01 落码）
    # 六旬 = 甲子/甲戌/甲申/甲午/甲辰/甲寅；旬内十干支同属一旬。
    # 六仪 = 旬首支；响动 = 旬中庚（六甲旬中庚即是）；句丁 = 旬中丁；
    # 闭口 = 旬尾癸（癸酉/癸未/癸巳/癸卯/癸丑/癸亥）；五亡神 = 旬中辛（六辛即是）。
    XUN_SHA = {
        '甲子': {'句奇': '丑', '六仪': '子', '响动': '午', '句丁': '卯',
                 '闭口': '酉', '五亡神': '未', '空亡': ['戌', '亥']},
        '甲戌': {'句奇': '丑', '六仪': '戌', '响动': '辰', '句丁': '丑',
                 '闭口': '未', '五亡神': '巳', '空亡': ['申', '酉']},
        '甲申': {'句奇': '子', '六仪': '申', '响动': '寅', '句丁': '亥',
                 '闭口': '巳', '五亡神': '卯', '空亡': ['午', '未']},
        '甲午': {'句奇': '子', '六仪': '午', '响动': '子', '句丁': '酉',
                 '闭口': '卯', '五亡神': '丑', '空亡': ['辰', '巳']},
        '甲辰': {'句奇': '亥', '六仪': '辰', '响动': '戌', '句丁': '未',
                 '闭口': '丑', '五亡神': '亥', '空亡': ['寅', '卯']},
        '甲寅': {'句奇': '亥', '六仪': '寅', '响动': '申', '句丁': '巳',
                 '闭口': '亥', '五亡神': '酉', '空亡': ['子', '丑']},
    }
    
    # 日干神煞（通解 上卷 p138「日干神煞」权威表；2026-08-01 落码）
    # 引擎已有：日禄(SHI_GAN_LU)/日德(get_ri_de)/羊刃(SHI_GAN_YANG_REN)。
    # 注：p138 表 OCR 将"亥"误识为"玄"（同页日支神煞表多处"玄"=亥位可互证），
    # 日解/日医/日刑 已按"亥"录入；"西"为"酉"误识。纸质书核对见审查报告。
    GAN_SHA = {
        '五合':     {'甲': '未', '乙': '申', '丙': '戌', '丁': '亥', '戊': '丑',
                     '己': '寅', '庚': '辰', '辛': '巳', '壬': '未', '癸': '巳'},
        '长生学堂': {'甲': '亥', '乙': '亥', '丙': '寅', '丁': '寅', '戊': '申',
                     '己': '申', '庚': '巳', '辛': '巳', '壬': '申', '癸': '申'},
        '贤贵':     {'甲': '丑', '乙': '申', '丙': '寅', '丁': '寅', '戊': '午',
                     '己': '丑', '庚': '申', '辛': '寅', '壬': '寅', '癸': '午'},
        '兼务':     {'甲': '戌', '乙': '酉', '丙': '申', '丁': '未', '戊': '午',
                     '己': '巳', '庚': '辰', '辛': '卯', '壬': '寅', '癸': '亥'},
        '进神':     {'甲': '子', '乙': '午', '丙': '子', '丁': '午', '戊': '子',
                     '己': '卯', '庚': '卯', '辛': '卯', '壬': '卯', '癸': '酉'},
        '退神':     {'甲': '丑', '乙': '未', '丙': '丑', '丁': '未', '戊': '丑',
                     '己': '辰', '庚': '辰', '辛': '辰', '壬': '辰', '癸': '戌'},
        '日解':     {'甲': '亥', '乙': '申', '丙': '未', '丁': '丑', '戊': '酉',
                     '己': '亥', '庚': '申', '辛': '未', '壬': '丑', '癸': '酉'},
        '日医':     {'甲': '卯', '乙': '亥', '丙': '丑', '丁': '未', '戊': '巳',
                     '己': '卯', '庚': '亥', '辛': '丑', '壬': '未', '癸': '巳'},
        '日刑':     {'甲': '巳', '乙': '辰', '丙': '申', '丁': '丑', '戊': '申',
                     '己': '丑', '庚': '寅', '辛': '未', '壬': '亥', '癸': '戌'},
        '直符':     {'甲': '巳', '乙': '辰', '丙': '卯', '丁': '寅', '戊': '丑',
                     '己': '午', '庚': '未', '辛': '申', '壬': '酉', '癸': '戌'},
        '游都':     {'甲': '丑', '乙': '子', '丙': '寅', '丁': '巳', '戊': '申',
                     '己': '丑', '庚': '子', '辛': '寅', '壬': '巳', '癸': '申'},
        '鲁都':     {'甲': '未', '乙': '午', '丙': '申', '丁': '亥', '戊': '寅',
                     '己': '未', '庚': '午', '辛': '申', '壬': '亥', '癸': '寅'},
    }
    
    # 日支神煞（通解 上卷 p138「日支神煞」权威表；2026-08-01 落码）
    # 注：p138 表 OCR 将"亥"误识为"玄"（同页多处玄=亥位互证）、"西"="酉"；
    # 支德/三刑/六破 已按亥/酉校正录入。六合/六冲/六害/日马/桃花/驿马/劫煞/灾煞 引擎已有。
    # 支德：子巳丑午寅未卯申辰酉巳戌午亥未子申丑酉寅戌卯亥辰（=日支顺行巳起）
    # 六破：子酉丑辰寅亥卯午辰丑巳申午卯未戌申巳酉子戌未亥寅
    ZHI_SHA = {
        '支仪': {'子': '午', '丑': '巳', '寅': '辰', '卯': '卯', '辰': '寅', '巳': '丑',
                 '午': '未', '未': '申', '申': '酉', '酉': '戌', '戌': '亥', '亥': '子'},
        '支德': {'子': '巳', '丑': '午', '寅': '未', '卯': '申', '辰': '酉', '巳': '戌',
                 '午': '亥', '未': '子', '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'},
        '六破': {'子': '酉', '丑': '辰', '寅': '亥', '卯': '午', '辰': '丑', '巳': '申',
                 '午': '卯', '未': '戌', '申': '巳', '酉': '子', '戌': '未', '亥': '寅'},
        '三刑': {'子': '卯', '丑': '戌', '寅': '巳', '卯': '子', '辰': '辰', '巳': '申',
                 '午': '午', '未': '丑', '申': '寅', '酉': '酉', '戌': '未', '亥': '亥'},
        '华盖': {'子': '辰', '丑': '丑', '寅': '戌', '卯': '未', '辰': '辰', '巳': '丑',
                 '午': '戌', '未': '未', '申': '辰', '酉': '丑', '戌': '戌', '亥': '未'},
        '破碎': {'子': '巳', '丑': '丑', '寅': '酉', '卯': '巳', '辰': '丑', '巳': '酉',
                 '午': '巳', '未': '丑', '申': '酉', '酉': '巳', '戌': '丑', '亥': '酉'},
        '雷电': {'子': '辰', '丑': '辰', '寅': '未', '卯': '未', '辰': '戌', '巳': '戌',
                 '午': '丑', '未': '丑', '申': '寅', '酉': '寅', '戌': '卯', '亥': '卯'},
        '雨师': {'子': '申', '丑': '酉', '寅': '戌', '卯': '亥', '辰': '子', '巳': '丑',
                 '午': '寅', '未': '卯', '申': '辰', '酉': '巳', '戌': '午', '亥': '未'},
        '晴朗': {'子': '午', '丑': '未', '寅': '申', '卯': '酉', '辰': '戌', '巳': '亥',
                 '午': '子', '未': '丑', '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'},
        '将军': {'子': '子', '丑': '酉', '寅': '午', '卯': '卯', '辰': '子', '巳': '酉',
                 '午': '午', '未': '卯', '申': '子', '酉': '酉', '戌': '午', '亥': '卯'},
    }
    
    # 驾前十二神煞（通解 上卷 p139-140「驾前神煞」，太岁前十二位，按岁支顺行）
    # 歌诀：太岁剑锋伏尸寄(建)、太阳天空仍可畏(除)、丧门内外孝服至(满)、
    #       太阴贯索勾绞具(平)、官符杖责难回避(定)、死符月德同行位(执)、
    #       岁破月空拦杆是(破)、龙德暴败天厄至(危)、白虎飞廉同此处(成)、
    #       天德福星卷舌系(收)、吊客天狗吠(开)、病符顺行位(闭)。
    # 与引擎既有 丧门/吊客/病符/岁破 同源（值一致验证通过）。
    JIA_QIAN_NAMES = ['太岁', '太阳', '丧门', '太阴', '官符', '死符',
                      '岁破', '龙德', '白虎', '天德', '吊客', '病符']
    
    # 日支三合局（通解 p138 日支神煞「三合」行语义：日支为子，四课三传遇申、辰即三合水局。
    # 此非单值神煞，为课传判断用：每日支唯一归属一三合局，另两支即课传命中目标。
    # 注：OCR 该行 13 值错位不可用（13值 vs 12列，删首删尾均不成规律），
    # 依憨爷解释 + 通解 L869 地支三合（申子辰/寅午戌/巳酉丑/亥卯未）以标准三合局为准。
    # 2026-08-01 憨爷拍板语义。）
    SAN_HE_JU = {
        '子': ('申子辰', '申', '辰'), '丑': ('巳酉丑', '巳', '酉'), '寅': ('寅午戌', '午', '戌'),
        '卯': ('亥卯未', '亥', '未'), '辰': ('申子辰', '申', '子'), '巳': ('巳酉丑', '酉', '丑'),
        '午': ('寅午戌', '寅', '戌'), '未': ('亥卯未', '亥', '卯'), '申': ('申子辰', '子', '辰'),
        '酉': ('巳酉丑', '丑', '巳'), '戌': ('寅午戌', '寅', '午'), '亥': ('亥卯未', '卯', '未'),
    }
    
    # 马前十二神煞（通解 上卷 p140「马前神煞」：按日支三合局，驿马起顺行十二位）
    # 次序：驿马、六厄、华盖、劫杀、灾杀、天杀、岁杀、月杀、地杀、亡神、将星、攀鞍
    # 四局驿马：申子辰马寅、亥卯未马巳、寅午戌马申、巳酉丑马亥。
    # 与已有 驿马(get_yi_ma)/华盖(ZHI_SHA)/劫煞(get_jie_sha)/灾煞(get_zai_sha) 同源一致。
    MA_QIAN_NAMES = ['驿马', '六厄', '华盖', '劫杀', '灾杀', '天杀', '岁杀', '月杀',
                     '地杀', '亡神', '将星', '攀鞍']
    # 日支 → 驿马（与 YI_MA 三合表一致，用于马前顺行起位）
    MA_QIAN_START = {
        '申': '寅', '子': '寅', '辰': '寅',
        '亥': '巳', '卯': '巳', '未': '巳',
        '寅': '申', '午': '申', '戌': '申',
        '巳': '亥', '酉': '亥', '丑': '亥',
    }
    
    # 四季神煞（通解 上卷 p134-135「四季神煞」；2026-08-01 补 OCR 表头+数值后落码）
    # 每项四值=春/夏/秋/冬对应地支（或四支=四季）。
    # 与各章互证：天喜=春戌夏丑秋辰冬未(婚姻章)、游神/戏神(行人章)、孤辰春巳顺四孟、
    # 寡宿春丑顺四季、四废=春酉夏子秋卯冬午、浴盆/天目=春辰夏未秋戌冬丑(疾病章)。
    # 注：三丘/五墓（四季长生之墓/四季之墓）数值 OCR 未出，疑=未戌丑辰（四季墓支），待纸质核对。
    # 飞祸（刑四孟）值申酉巳卯疑 OCR 有误，待核对。
    JI_JIE_SHA = {
        '天转': {'春': '卯', '夏': '午', '秋': '酉', '冬': '子'},
        '地转': {'春': '卯', '夏': '午', '秋': '酉', '冬': '子'},
        '天车': {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'},
        '天城': {'春': '申', '夏': '申', '秋': '申', '冬': '申'},
        '天吏': {'春': '寅', '夏': '寅', '秋': '寅', '冬': '寅'},
        '皇书': {'春': '寅', '夏': '巳', '秋': '申', '冬': '亥'},
        '天喜': {'春': '戌', '夏': '丑', '秋': '辰', '冬': '未'},
        '天赦': {'春': '寅', '夏': '午', '秋': '申', '冬': '子'},   # 干支戊寅/甲午/戊申/甲子，取支
        '天盗': {'春': '酉', '夏': '午', '秋': '卯', '冬': '子'},
        '钥神': {'春': '巳', '夏': '申', '秋': '亥', '冬': '寅'},
        '转煞': {'春': '卯', '夏': '午', '秋': '酉', '冬': '子'},
        '奸神': {'春': '寅', '夏': '亥', '秋': '申', '冬': '巳'},
        '游神': {'春': '丑', '夏': '子', '秋': '亥', '冬': '戌'},
        '戏神': {'春': '巳', '夏': '子', '秋': '酉', '冬': '辰'},
        '孤辰': {'春': '巳', '夏': '申', '秋': '亥', '冬': '寅'},
        '寡宿': {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'},
        '四废': {'春': '酉', '夏': '子', '秋': '卯', '冬': '午'},
        '丧车煞': {'春': '辰', '夏': '未', '秋': '戌', '冬': '丑'},
        '浴盆': {'春': '辰', '夏': '未', '秋': '戌', '冬': '丑'},
        '天目': {'春': '辰', '夏': '未', '秋': '戌', '冬': '丑'},
        '天耳': {'春': '戌', '夏': '丑', '秋': '辰', '冬': '未'},
        '飞祸': {'春': '申', '夏': '酉', '秋': '巳', '冬': '卯'},   # 疑 OCR 有误，待核
        '火鬼': {'春': '午', '夏': '酉', '秋': '子', '冬': '卯'},
        '关神': {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'},
    }
    SEASON_OF_MONTH = {1: '春', 2: '春', 3: '春', 4: '夏', 5: '夏', 6: '夏',
                       7: '秋', 8: '秋', 9: '秋', 10: '冬', 11: '冬', 12: '冬'}
    
    def __init__(self):
        pass
    
    def get_yi_ma(self, ri_zhi: str) -> str:
        """获取驿马"""
        for san_he, ma in self.YI_MA.items():
            if ri_zhi in san_he:
                return ma
        return ''
    
    def get_tao_hua(self, ri_zhi: str) -> str:
        """获取桃花"""
        for san_he, tao in self.TAO_HUA.items():
            if ri_zhi in san_he:
                return tao
        return ''
    
    def get_jie_sha(self, ri_zhi: str) -> str:
        """获取劫煞"""
        for san_he, jie in self.JIE_SHA.items():
            if ri_zhi in san_he:
                return jie
        return ''
    
    def get_zai_sha(self, ri_zhi: str) -> str:
        """获取灾煞"""
        for san_he, zai in self.ZAI_SHA.items():
            if ri_zhi in san_he:
                return zai
        return ''
    
    def get_ri_lu(self, ri_gan: str) -> str:
        """获取日禄"""
        return self.SHI_GAN_LU.get(ri_gan, '')
    
    def get_ri_de(self, ri_gan: str) -> str:
        """获取日德"""
        # 标准十干日德表（甲寅乙申丙巳丁亥戊巳己寅庚申辛巳壬亥癸巳；戊癸同巳，2026-08-16 日德 FixA 已核）
        de_map = {
            '甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
            '己': '寅', '庚': '申', '辛': '巳', '壬': '亥', '癸': '巳'
        }
        return de_map.get(ri_gan, '')
    
    def get_gui_ren(self, ri_gan: str) -> List[str]:
        """获取天乙贵人"""
        return self.SHI_GAN_GUI_REN.get(ri_gan, [])
    
    def get_yang_ren(self, ri_gan: str) -> str:
        """获取羊刃"""
        return self.SHI_GAN_YANG_REN.get(ri_gan, '')
    
    def get_yue_jian(self, lunar_month: int) -> str:
        """获取月建"""
        return self.YUE_SHA.get(lunar_month, {}).get('月建', '')
    
    def get_yue_po(self, lunar_month: int) -> str:
        """获取月破（月建冲）"""
        yue_jian = self.get_yue_jian(lunar_month)
        return self.LIU_CHONG.get(yue_jian, '')
    
    def get_yue_yan(self, lunar_month: int) -> str:
        """获取月厌"""
        return self.YUE_SHA.get(lunar_month, {}).get('月厌', '')
    
    def get_tian_de(self, lunar_month: int) -> str:
        """获取天德"""
        return self.YUE_SHA.get(lunar_month, {}).get('天德', '')
    
    def get_yue_de(self, lunar_month: int) -> str:
        """获取月德"""
        return self.YUE_SHA.get(lunar_month, {}).get('月德', '')
    
    def get_tian_xi(self, lunar_month: int) -> str:
        """获取天喜（口诀「春戌夏丑秋辰冬未」）

        【BUG-FIX 2026-09-11】原实现查 `YUE_SHA[lunar_month]['天喜']`，而该表的天喜值是
        **逐月递进**（正月戌、二月亥、三月子、四月丑…），与《大六壬大全》口诀不符 ——
        本文件 L275 注释自己就写着"天喜=春戌夏丑秋辰冬未(婚姻章)"，**表与注释矛盾**。
        实测：get_tian_xi(2) 返回亥（应戌）、(5)→寅（应丑）、(8)→巳（应辰）、(11)→申（应未），
        整体后移一位。
        现改为查四季表 `JI_JIE_SHA['天喜']`（数据本就正确：春戌/夏丑/秋辰/冬未）。
        依据：《图解六壬大全》第1部 p.284-570 神煞章 OCR（`_memory/ocr_part1_140_588.txt`）。
        """
        season = self.SEASON_OF_MONTH.get(lunar_month, '')
        return self.JI_JIE_SHA.get('天喜', {}).get(season, '')
    
    def get_tian_yi(self, lunar_month: int) -> str:
        """获取天医"""
        return self.YUE_SHA.get(lunar_month, {}).get('天医', '')
    
    def get_ri_sha(self, ri_zhi: str) -> Dict[str, str]:
        """获取日煞（完整）"""
        return self.RI_SHA.get(ri_zhi, {})
    
    def get_yue_sha(self, lunar_month: int) -> Dict[str, str]:
        """获取月煞（完整）"""
        return self.YUE_SHA.get(lunar_month, {})
    
    def get_gu_gua(self, nian_zhi: str) -> Dict[str, str]:
        """获取孤辰寡宿"""
        for san_he, gu_gua in self.GU_GUA.items():
            if nian_zhi in san_he:
                return gu_gua
        return {'孤': '', '寡': ''}
    
    def get_sang_diao(self, nian_zhi: str) -> Dict[str, str]:
        """获取丧门吊客"""
        return self.SANG_DIAO.get(nian_zhi, {'丧门': '', '吊客': ''})
    
    def get_bing_fu(self, nian_zhi: str) -> str:
        """获取病符（年支前一位）"""
        return self.BING_FU.get(nian_zhi, '')
    
    def get_sui_po(self, nian_zhi: str) -> str:
        """获取岁破（年支对冲）"""
        liu_chong = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
            '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
        }
        return liu_chong.get(nian_zhi, '')
    
    def get_tian_she(self, month_zhi: str) -> str:
        """获取天赦（按季节：春戊寅、夏甲午、秋戊申、冬甲子）"""
        TIAN_SHE = {
            '寅': '戊寅', '卯': '戊寅', '辰': '戊寅',
            '巳': '甲午', '午': '甲午', '未': '甲午',
            '申': '戊申', '酉': '戊申', '戌': '戊申',
            '亥': '甲子', '子': '甲子', '丑': '甲子'
        }
        return TIAN_SHE.get(month_zhi, '')
    
    def get_si_fei(self, month_zhi: str) -> str:
        """获取四废（按季节：春庚申辛酉、夏壬子癸亥、秋甲寅乙卯、冬丙午丁巳）"""
        SI_FEI = {
            '寅': '庚申辛酉', '卯': '庚申辛酉', '辰': '庚申辛酉',
            '巳': '壬子癸亥', '午': '壬子癸亥', '未': '壬子癸亥',
            '申': '甲寅乙卯', '酉': '甲寅乙卯', '戌': '甲寅乙卯',
            '亥': '丙午丁巳', '子': '丙午丁巳', '丑': '丙午丁巳'
        }
        return SI_FEI.get(month_zhi, '')
    
    def get_tian_luo_di_wang(self, ri_zhi: str) -> Dict[str, str]:
        """获取天罗地网（戌亥日天罗在辰，辰巳日地网在戌）"""
        result = {}
        if ri_zhi in ('戌', '亥'):
            result['天罗'] = '辰'
        if ri_zhi in ('辰', '巳'):
            result['地网'] = '戌'
        return result
    
    def get_xun_name(self, ri_gan_zhi: str) -> str:
        """由完整日干支精确定旬，返回旬首干支名（甲子/甲戌/甲申/甲午/甲辰/甲寅）。
        60甲子序 n 满足 n%10==干序 且 n%12==支序；旬首 = 序 (n//10)*10。
        """
        if not ri_gan_zhi or len(ri_gan_zhi) != 2:
            return ''
        gan, zhi = ri_gan_zhi[0], ri_gan_zhi[1]
        if gan not in self.TIANGAN or zhi not in self.DIZHI:
            return ''
        gan_i, zhi_i = self.TIANGAN.index(gan), self.DIZHI.index(zhi)
        n = None
        for k in range(60):
            if k % 10 == gan_i and k % 12 == zhi_i:
                n = k
                break
        if n is None:
            return ''
        xun_head_n = (n // 10) * 10
        return self.TIANGAN[xun_head_n % 10] + self.DIZHI[xun_head_n % 12]
    
    def get_xun_kong(self, ri_gan_zhi: str) -> List[str]:
        """
        获取旬空（通解 上卷 p138）
        甲子旬戌亥空，甲戌旬申酉空，甲申旬午未空
        甲午旬辰巳空，甲辰旬寅卯空，甲寅旬子丑空
        由完整日干支精确定旬（旧实现仅按日支序号粗判，丙子日等会误归甲子旬）。
        """
        xun = self.get_xun_name(ri_gan_zhi) if ri_gan_zhi else ''
        if not xun:
            return []
        return list(self.XUN_SHA.get(xun, {}).get('空亡', []))
    
    def get_xun_info(self, ri_gan_zhi: str) -> Dict[str, object]:
        """获取旬内全部神煞（旬首/句奇/六仪/响动/句丁/闭口/五亡神/空亡）"""
        if not ri_gan_zhi:
            return {}
        xun = self.get_xun_name(ri_gan_zhi)
        if not xun:
            return {}
        info = dict(self.XUN_SHA.get(xun, {}))
        info['旬首'] = xun
        return info
    
    def get_gan_sha(self, ri_gan: str) -> Dict[str, str]:
        """获取日干神煞（五合/长生学堂/贤贵/兼务/进神/退神/日解/日医/日刑/直符/游都/鲁都）"""
        result = {}
        if not ri_gan or ri_gan not in self.TIANGAN:
            return result
        for name, table in self.GAN_SHA.items():
            v = table.get(ri_gan, '')
            if v:
                result[name] = v
        return result
    
    def get_zhi_sha(self, ri_zhi: str) -> Dict[str, str]:
        """获取日支神煞（支仪/支德/六破/三刑/华盖/破碎/雷电/雨师/晴朗/将军）"""
        result = {}
        if not ri_zhi or ri_zhi not in self.DIZHI:
            return result
        for name, table in self.ZHI_SHA.items():
            v = table.get(ri_zhi, '')
            if v:
                result[name] = v
        return result
    
    def get_jia_qian(self, nian_zhi: str) -> Dict[str, str]:
        """获取驾前十二神煞（通解 上卷 p139-140，按岁支顺行十二位）"""
        result = {}
        if not nian_zhi or nian_zhi not in self.DIZHI:
            return result
        start = self.DIZHI.index(nian_zhi)
        for i, name in enumerate(self.JIA_QIAN_NAMES):
            result[name] = self.DIZHI[(start + i) % 12]
        return result
    
    def get_san_he_ju(self, ri_zhi: str) -> Tuple[str, List[str]]:
        """获取日支三合局（通解 p138「三合」行语义：日支+课传另两支=局成）。
        返回 (三合局名, 另两支列表)；例：get_san_he_ju('子') → ('申子辰', ['申', '辰'])。"""
        if not ri_zhi or ri_zhi not in self.DIZHI:
            return '', []
        ju = self.SAN_HE_JU.get(ri_zhi)
        if not ju:
            return '', []
        return ju[0], [ju[1], ju[2]]
    
    def get_ma_qian(self, ri_zhi: str) -> Dict[str, str]:
        """获取马前十二神煞（通解 上卷 p140；按日支三合局驿马起顺行十二位）"""
        result = {}
        if not ri_zhi or ri_zhi not in self.DIZHI:
            return result
        start_zhi = self.MA_QIAN_START.get(ri_zhi, '')
        if not start_zhi:
            return result
        start = self.DIZHI.index(start_zhi)
        for i, name in enumerate(self.MA_QIAN_NAMES):
            result[name] = self.DIZHI[(start + i) % 12]
        return result
    
    def get_jijie_sha(self, season: str = '') -> Dict[str, str]:
        """获取四季神煞（通解 上卷 p134-135；season='春/夏/秋/冬'，空则按公历月推）"""
        result = {}
        if not season:
            return result
        for name, table in self.JI_JIE_SHA.items():
            v = table.get(season, '')
            if v:
                result[name] = v
        return result
    
    def calculate_all_shen_sha(self, ri_gan: str, ri_zhi: str, 
                               lunar_month: int = 1, 
                               nian_zhi: str = '子',
                               ri_gan_zhi: str = '') -> Dict[str, str]:
        """
        计算所有神煞（完整版）
        
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param lunar_month: 农历月份
        :param nian_zhi: 年支
        :param ri_gan_zhi: 日干支（用于旬空）
        :return: 神煞字典
        """
        shen_sha = {}
        
        # ===== 日干神煞 =====
        shen_sha['日禄'] = self.get_ri_lu(ri_gan)
        shen_sha['日德'] = self.get_ri_de(ri_gan)
        shen_sha['羊刃'] = self.get_yang_ren(ri_gan)
        
        # 天乙贵人
        gui_ren_list = self.get_gui_ren(ri_gan)
        if gui_ren_list:
            shen_sha['天乙贵人'] = gui_ren_list[0]
            if len(gui_ren_list) > 1:
                shen_sha['天乙贵人 2'] = gui_ren_list[1]
        
        # ===== 日支神煞 =====
        shen_sha['驿马'] = self.get_yi_ma(ri_zhi)
        shen_sha['桃花'] = self.get_tao_hua(ri_zhi)
        shen_sha['劫煞'] = self.get_jie_sha(ri_zhi)
        shen_sha['灾煞'] = self.get_zai_sha(ri_zhi)
        
        # 天罗地网
        tian_luo = self.get_tian_luo_di_wang(ri_zhi)
        if tian_luo.get('天罗'):
            shen_sha['天罗'] = tian_luo['天罗']
        if tian_luo.get('地网'):
            shen_sha['地网'] = tian_luo['地网']
        
        # 日煞详情
        ri_sha_detail = self.get_ri_sha(ri_zhi)
        if ri_sha_detail:
            for key, value in ri_sha_detail.items():
                if value and key not in shen_sha:
                    shen_sha[key] = value
        
        # ===== 月建神煞 =====
        shen_sha['月建'] = self.get_yue_jian(lunar_month)
        shen_sha['月破'] = self.get_yue_po(lunar_month)
        shen_sha['月厌'] = self.get_yue_yan(lunar_month)
        shen_sha['天德'] = self.get_tian_de(lunar_month)
        shen_sha['月德'] = self.get_yue_de(lunar_month)
        shen_sha['天喜'] = self.get_tian_xi(lunar_month)
        shen_sha['天医'] = self.get_tian_yi(lunar_month)
        
        # 月煞详情
        yue_sha_detail = self.get_yue_sha(lunar_month)
        for key, value in yue_sha_detail.items():
            if value and key not in shen_sha:
                shen_sha[f'月{key}'] = value
        
        # 天赦、四废（按季节）
        MONTH_ZHI_MAP = {1:'寅',2:'卯',3:'辰',4:'巳',5:'午',6:'未',
                         7:'申',8:'酉',9:'戌',10:'亥',11:'子',12:'丑'}
        month_zhi = MONTH_ZHI_MAP.get(lunar_month, '')
        if month_zhi:
            tian_she = self.get_tian_she(month_zhi)
            if tian_she:
                shen_sha['天赦'] = tian_she
            si_fei = self.get_si_fei(month_zhi)
            if si_fei:
                shen_sha['四废'] = si_fei
        
        # ===== 年支神煞 =====
        gu_gua = self.get_gu_gua(nian_zhi)
        shen_sha['孤辰'] = gu_gua.get('孤', '')
        shen_sha['寡宿'] = gu_gua.get('寡', '')
        
        sang_diao = self.get_sang_diao(nian_zhi)
        shen_sha['丧门'] = sang_diao.get('丧门', '')
        shen_sha['吊客'] = sang_diao.get('吊客', '')
        shen_sha['病符'] = self.get_bing_fu(nian_zhi)
        shen_sha['岁破'] = self.get_sui_po(nian_zhi)
        
        # ===== 日干神煞（通解 上卷 p138；五合/长生学堂/贤贵/兼务/进神/退神/日解/日医/日刑/直符/游都/鲁都）=====
        gan_sha = self.get_gan_sha(ri_gan)
        for k, v in gan_sha.items():
            if v and k not in shen_sha:
                shen_sha[k] = v
        
        # ===== 日支神煞（通解 上卷 p138；支仪/支德/六破/三刑/华盖/破碎/雷电/雨师/晴朗/将军）=====
        # ⚠️ 中性神煞吉凶待核清单（08-17 记档，未落码——须《通解》原文逐条印证后进
        # build_feature_vectors 的 JI_SHEN/XIONG_SHA 集合，且动特征须古例 A/B 过 M3 闸口）：
        #   晴朗(天气类·中性) / 将军(疑凶·兵戎争斗) / 支仪(疑吉·六仪之属) /
        #   响动(疑中性·声名变动) / 句丁(疑中性·文书) / 句奇(疑吉) / 六仪(疑吉·旬首威仪) /
        #   雷电(疑凶·惊变) / 雨师(疑中性·天气)
        zhi_sha = self.get_zhi_sha(ri_zhi)
        for k, v in zhi_sha.items():
            if v and k not in shen_sha:
                shen_sha[k] = v
        
        # ===== 驾前十二神煞（通解 上卷 p139-140，按岁支顺行）=====
        if nian_zhi:
            jia_qian = self.get_jia_qian(nian_zhi)
            for k, v in jia_qian.items():
                if v:
                    shen_sha[f'驾前{k}'] = v
        
        # ===== 马前十二神煞（通解 上卷 p140；驿马/华盖/劫煞/灾煞已有，补 六厄/天杀/岁杀/月杀/地杀/亡神/将星/攀鞍）=====
        ma_qian = self.get_ma_qian(ri_zhi)
        for k, v in ma_qian.items():
            if k in ('驿马', '华盖', '劫煞', '灾煞'):
                continue  # 已有同源 key，不重复写入
            if v:
                shen_sha[f'马前{k}'] = v
        
        # ===== 四季神煞（通解 上卷 p134-135；按农历月推季节；展示/叙事用）=====
        season = self.SEASON_OF_MONTH.get(lunar_month or 1, '')
        if season:
            jijie = self.get_jijie_sha(season)
            for k, v in jijie.items():
                if v:
                    shen_sha[f'四季{k}'] = v
        
        # ===== 旬煞（通解 上卷 p138 六十甲子旬神煞：旬空/句奇/六仪/响动/句丁/闭口/五亡神）=====
        if ri_gan_zhi:
            xun_info = self.get_xun_info(ri_gan_zhi)
            if xun_info:
                kong = xun_info.get('空亡', [])
                shen_sha['旬空'] = ','.join(kong) if kong else ''
                for k in ('旬首', '句奇', '六仪', '响动', '句丁', '闭口', '五亡神'):
                    v = xun_info.get(k, '')
                    if v:
                        shen_sha[k] = v
            else:
                shen_sha['旬空'] = ','.join(self.get_xun_kong(ri_gan_zhi))
        
        return shen_sha


def main():
    """测试神煞计算"""
    calculator = ShenShaCalculator()
    
    print("=" * 80)
    print("神煞计算测试")
    print("=" * 80)
    
    # 测试甲子日
    ri_gan = '甲'
    ri_zhi = '子'
    ri_gan_zhi = '甲子'
    lunar_month = 1
    nian_zhi = '子'
    
    print(f"\n测试：{ri_gan_zhi}日 农历{lunar_month}月 年支{nian_zhi}")
    
    shen_sha = calculator.calculate_all_shen_sha(
        ri_gan, ri_zhi, lunar_month, nian_zhi, ri_gan_zhi
    )
    
    print("\n神煞列表:")
    for name, value in sorted(shen_sha.items()):
        if value:
            print(f"  {name:12s}: {value}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
