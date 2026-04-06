#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课课经规则库
基于《六壬大全》64 课课经整理
"""

# 64 课课经完整规则（基于 zongmen 资料）
KE_JING_64 = {
    # ==================== 九宗门正课（1-9） ====================
    '元首课': {
        'code': 1,
        'jixiong': '大吉',
        'base_score': 95,
        'definition': '四课之中一课上克下，其余无克。上克下为正，天地得位，以尊制卑',
        'xiang_yue': '天地得位，品物咸新。事用君子，忧喜俱真。君臣和合，父子慈亲。婚谐鸾凤，孕育麒麟。用兵客胜，论讼先陈。市贾出色，各利超群。官职首擢，柱石元勋。门庭喜溢，利见大人。',
        'duanyu': '元首课为大吉之课，万事顺利，元亨利贞。君王占之得伊吕之臣，臣子占之遇唐虞之君，常人占之万事顺利。',
        'te_zheng': ['一上克下', '余课无克', '天地得位'],
        'yong_shen': '取上克下者为初传'
    },
    
    '重审课': {
        'code': 2,
        'jixiong': '大吉',
        'base_score': 85,
        'definition': '四课之中有一课下贼上，其余无克。下贼上发用，以下犯上，必须再三详审',
        'xiang_yue': '顺天厚载，柔顺利贞。一下逆上，岂无忧惊？贵顺福至，贵逆乱兴。事宜后起，祸从内生。用兵主胜，受孕女形。诸般谋望，先难后成。',
        'duanyu': '重审课事多不顺，先难后成。积善者庆，积不善者殃。君子占之利有攸往。',
        'te_zheng': ['一下贼上', '余课无克', '以下犯上'],
        'yong_shen': '取下贼上者为初传'
    },
    
    '知一课': {
        'code': 3,
        'jixiong': '平',
        'base_score': 70,
        'definition': '四课之中有两课为上克下，或有两课为下克上，择课之阴阳与日比者为用神',
        'xiang_yue': '比者为喜，不比为忧。词宜和允，兵利主谋。祸从外起，事向朋谋。寻人失物，近处堪求。',
        'duanyu': '知一课事宜惟一，允执厥中。善恶混处，必知择其比和一善者而用之。',
        'te_zheng': ['二上克下', '或二下贼上', '比和为用'],
        'yong_shen': '阳日阳比，阴日阴比'
    },
    
    '涉害课': {
        'code': 4,
        'jixiong': '凶',
        'base_score': 55,
        'definition': '四课中有两课或三课、四课上下克战，须以课中受克深者发用',
        'xiang_yue': '见机而作，察微知著。涉害深者，事多艰难。必须经历风霜，历尽艰辛，方能苦尽甘来。',
        'duanyu': '涉害课凡事艰难，苦尽甘来。取受克深者为用，见机格害深 > 3，察微格害深 ≤ 3。',
        'te_zheng': ['多课克战', '涉害深者', '经历艰难'],
        'yong_shen': '取涉害最深者为初传'
    },
    
    '遥克课': {
        'code': 5,
        'jixiong': '凶',
        'base_score': 50,
        'definition': '四课上下无克，取遥相克贼为用。有日遥克神（蒿矢）和神遥克日（弹射）两种',
        'xiang_yue': '始虽惊恐，后无妨害。遥相克贼，事从外来。蒿矢射物，弹射击人。',
        'duanyu': '遥克课主始虽惊恐，后无妨害。事体遥远，或有小人作祟。',
        'te_zheng': ['四课无克', '遥相克贼', '蒿矢弹射'],
        'yong_shen': '上克干为蒿矢，干克上为弹射'
    },
    
    '昴星课': {
        'code': 6,
        'jixiong': '平',
        'base_score': 60,
        'definition': '四课上下无克，又无遥克，取酉宫昴宿为用。刚日仰视酉宫，柔日俯视酉宫',
        'xiang_yue': '虎视稽留，冬蛇隐伏。昴星照命，事多暗昧。刚日主动，柔日主静。',
        'duanyu': '昴星课虎视稽留，冬蛇隐伏。事多暗昧不明，需防小人作祟。',
        'te_zheng': ['四课无克', '无遥克', '取酉为用'],
        'yong_shen': '刚日取酉上神，柔日取酉下神'
    },
    
    '别责课': {
        'code': 7,
        'jixiong': '凶',
        'base_score': 45,
        'definition': '四课不全，只有三课，或有两课相同。主凡事不备，主有留连',
        'xiang_yue': '凡事不备，主有留连。别有所责，事不周全。阳日干合，阴日支合。',
        'duanyu': '别责课凡事不备，主有留连迟滞。阳日取干合上神，阴日取支前三合。',
        'te_zheng': ['四课不全', '两课相同', '凡事不备'],
        'yong_shen': '阳日干合，阴日支前三合'
    },
    
    '八专课': {
        'code': 8,
        'jixiong': '凶',
        'base_score': 40,
        'definition': '甲寅、庚申、壬子、丙午四日，干支同位，阴阳不分。主私洗不明，不利奔波',
        'xiang_yue': '私洗不明，不利奔波。八专之日，阴阳不分。干支同位，事多暧昧。',
        'duanyu': '八专课私洗不明，不利奔波。阴阳不分，事多暧昧不明。',
        'te_zheng': ['干支同位', '阴阳不分', '私洗不明'],
        'yong_shen': '阳日顺数第三，阴日逆数第三'
    },
    
    '伏吟课': {
        'code': 9,
        'jixiong': '凶',
        'base_score': 35,
        'definition': '月将加时，天地盘相同，十二神各居本宫。主静主慢，主有呻吟之声',
        'xiang_yue': '高中状元，得名荣归。伏吟主静，事多阻滞。宜静不宜动，待时而动。',
        'duanyu': '伏吟课主静主慢，事多阻滞。宜静不宜动，待时而动方吉。',
        'te_zheng': ['天地盘同', '十二神归位', '主静主慢'],
        'yong_shen': '有克依克，无克刚日取干上，柔日取支上'
    },
    
    '返吟课': {
        'code': 10,
        'jixiong': '平',
        'base_score': 50,
        'definition': '月将加时，天地盘对冲，十二神各居冲位。主反复不定，来者思去，离者思归',
        'xiang_yue': '来者思去，离者思归。返吟反复，事无定准。去而复来，离而复合。',
        'duanyu': '返吟课主反复不定，来者思去，离者思归。事多反复，成而复败。',
        'te_zheng': ['天地盘冲', '十二神对冲', '反复不定'],
        'yong_shen': '有克依克，无克取驿马'
    },
    
    # ==================== 衍生课（11-64 精选） ====================
    '三光课': {
        'code': 11,
        'jixiong': '大吉',
        'base_score': 90,
        'definition': '三传皆吉神，且旺相有气',
        'duanyu': '三光课大吉，百事亨通'
    },
    
    '三阳课': {
        'code': 12,
        'jixiong': '大吉',
        'base_score': 88,
        'definition': '三传皆阳，且生旺',
        'duanyu': '三阳课诸事顺利'
    },
    
    '龙德课': {
        'code': 13,
        'jixiong': '上吉',
        'base_score': 85,
        'definition': '太岁、月建、贵人发用',
        'duanyu': '龙德课贵人扶持'
    },
    
    '官爵课': {
        'code': 14,
        'jixiong': '上吉',
        'base_score': 85,
        'definition': '官星、爵星发用',
        'duanyu': '官爵课利求官求职'
    },
    
    '富贵课': {
        'code': 15,
        'jixiong': '上吉',
        'base_score': 83,
        'definition': '财星、禄神发用',
        'duanyu': '富贵课利求财'
    },
    
    '喜庆课': {
        'code': 16,
        'jixiong': '上吉',
        'base_score': 82,
        'definition': '喜神、庆星发用',
        'duanyu': '喜庆课主婚姻喜庆'
    },
    
    '斫轮课': {
        'code': 17,
        'jixiong': '中吉',
        'base_score': 75,
        'definition': '卯加申发用',
        'duanyu': '斫轮课主成就'
    },
    
    '铸印课': {
        'code': 18,
        'jixiong': '中吉',
        'base_score': 75,
        'definition': '巳加戌发用',
        'duanyu': '铸印课利官职'
    },
    
    '轩盖课': {
        'code': 19,
        'jixiong': '中吉',
        'base_score': 73,
        'definition': '午加卯发用',
        'duanyu': '轩盖课主荣显'
    },
    
    '登三天课': {
        'code': 20,
        'jixiong': '中吉',
        'base_score': 72,
        'definition': '三传递进',
        'duanyu': '登三天课主升迁'
    },
    
    '课宝课': {
        'code': 21,
        'jixiong': '中吉',
        'base_score': 70,
        'definition': '财宝发用',
        'duanyu': '课宝课利求财'
    },
    
    '无禄课': {
        'code': 22,
        'jixiong': '凶',
        'base_score': 30,
        'definition': '四课皆下贼上',
        'duanyu': '无禄课主不利'
    },
    
    '绝嗣课': {
        'code': 23,
        'jixiong': '大凶',
        'base_score': 20,
        'definition': '四课皆上克下',
        'duanyu': '绝嗣课大凶'
    },
    
    '乱首课': {
        'code': 24,
        'jixiong': '大凶',
        'base_score': 25,
        'definition': '支克干',
        'duanyu': '乱首课主以下犯上'
    },
    
    '赘婿课': {
        'code': 25,
        'jixiong': '凶',
        'base_score': 35,
        'definition': '干生支',
        'duanyu': '赘婿课主依附他人'
    },
    
    '冲破课': {
        'code': 26,
        'jixiong': '凶',
        'base_score': 30,
        'definition': '三传冲破',
        'duanyu': '冲破课主破坏'
    },
    
    '刑伤课': {
        'code': 27,
        'jixiong': '凶',
        'base_score': 28,
        'definition': '三传相刑',
        'duanyu': '刑伤课主伤害'
    },
    
    '害贵课': {
        'code': 28,
        'jixiong': '凶',
        'base_score': 32,
        'definition': '害贵人',
        'duanyu': '害贵课主失贵人助'
    },
    
    '空亡课': {
        'code': 29,
        'jixiong': '凶',
        'base_score': 25,
        'definition': '三传空亡',
        'duanyu': '空亡课主落空'
    },
    
    '脱气课': {
        'code': 30,
        'jixiong': '凶',
        'base_score': 30,
        'definition': '脱日干之气',
        'duanyu': '脱气课主耗损'
    },
    
    '伏吟课': {
        'code': 31,
        'jixiong': '凶',
        'base_score': 35,
        'definition': '天地盘伏吟',
        'duanyu': '伏吟课主阻滞'
    },
    
    '反吟课': {
        'code': 39,
        'jixiong': '平',
        'base_score': 45,
        'definition': '天地盘反吟',
        'duanyu': '反吟课主反复'
    }
}

# 课体吉凶分类统计
KE_JING_STATS = {
    '大吉': [1, 2, 11, 12],  # 元首、重审、三光、三阳
    '上吉': [13, 14, 15, 16],  # 龙德、官爵、富贵、喜庆
    '中吉': [17, 18, 19, 20, 21],  # 斫轮、铸印、轩盖、登三天、课宝
    '平': [3, 6, 10, 39],  # 知一、昴星、返吟
    '凶': [4, 5, 7, 8, 22, 24, 25, 26, 27, 28, 29, 30, 31],
    '大凶': [23]  # 绝嗣
}

def get_ke_jing_by_name(name: str) -> dict:
    """根据课名获取课经信息"""
    return KE_JING_64.get(name, {})

def get_ke_jing_by_code(code: int) -> dict:
    """根据课编号获取课经信息"""
    for name, info in KE_JING_64.items():
        if info['code'] == code:
            return info
    return {}

def get_score_by_name(name: str) -> int:
    """根据课名获取基础分数"""
    info = KE_JING_64.get(name, {})
    return info.get('base_score', 50)

def get_jixiong_by_name(name: str) -> str:
    """根据课名获取吉凶"""
    info = KE_JING_64.get(name, {})
    return info.get('jixiong', '平')

def get_all_ke_names() -> list:
    """获取所有课名列表"""
    return list(KE_JING_64.keys())

def get_ke_by_jixiong(jixiong: str) -> list:
    """根据吉凶获取课列表"""
    result = []
    for name, info in KE_JING_64.items():
        if info.get('jixiong') == jixiong:
            result.append(name)
    return result
