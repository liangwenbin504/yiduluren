#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
三传课格识别引擎 v2.0
======================

基于陈公献《大六壬指南》六层课格体系、《六壬大全》64课经、
《毕法赋》100法，从三传结构全面识别课格。

核心功能：
1. 三合局/全局课识别（润下/曲直/炎上/从革）+ 顺逆三合细化
2. 稼穑课识别（三传辰戌丑未全土局，含四时变体）
3. 连茹课识别（顺连茹12种 + 逆连茹12种细化命名）
4. 间传课识别（顺三间12种 + 逆三间12种细化命名）
5. 特殊课格：铸印/斫轮/高盖乘轩/玄胎/盘珠
6. 三传递生/递克关系分析
7. 课格股市映射（吉凶→涨跌倾向，含强度权重）
8. 课格复合判断（多个课格共存时的叠加规则）

数据来源：
- 陈公献《大六壬指南》心印赋+指掌赋（最核心来源）
- 《六壬大全》64课经+毕法赋100法
- 壬占汇选704古案例NLP提取验证
- data/sanchuan_kege_knowledge_base.json 统一知识库

版本历史：
- v1.0 (2026-07-29): 初版，16种课格
- v2.0 (2026-07-29): 大幅升级，整合三源经典文献，覆盖68种课格变体
"""

from typing import Dict, List, Tuple, Optional, Set

# ============================================================================
# 地支基础数据
# ============================================================================

DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

DIZHI_YIN_YANG = {
    '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴',
    '辰': '阳', '巳': '阴', '午': '阳', '未': '阴',
    '申': '阳', '酉': '阴', '戌': '阳', '亥': '阴'
}

DIZHI_WU_XING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 五行生克
WU_XING_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WU_XING_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 天干五行
TIANGAN_WU_XING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

# 地支四孟四仲四季
DIZHI_MENG = {'寅', '申', '巳', '亥'}  # 四孟（驿马位）
DIZHI_ZHONG = {'子', '午', '卯', '酉'}  # 四仲（桃花/沐浴位）
DIZHI_JI = {'辰', '戌', '丑', '未'}  # 四季（墓库位）

# 三合局定义
SAN_HE_GROUPS = {
    frozenset(['申', '子', '辰']): {
        'name': '水局', 'kege': '润下', 'kege_full': '润下课',
        'direction': '北方', 'zhongshen': '子',
        'stock_industry': '水利、航运、白酒、金融、物流'
    },
    frozenset(['亥', '卯', '未']): {
        'name': '木局', 'kege': '曲直', 'kege_full': '曲直课',
        'direction': '东方', 'zhongshen': '卯',
        'stock_industry': '医药、教育、新能源、环保'
    },
    frozenset(['寅', '午', '戌']): {
        'name': '火局', 'kege': '炎上', 'kege_full': '炎上课',
        'direction': '南方', 'zhongshen': '午',
        'stock_industry': '能源、科技、军工、传媒'
    },
    frozenset(['巳', '酉', '丑']): {
        'name': '金局', 'kege': '从革', 'kege_full': '从革课',
        'direction': '西方', 'zhongshen': '酉',
        'stock_industry': '金融、制造、军工、贵金属'
    },
}

# ============================================================================
# 64 课经缺失课格辅助数据（《大六壬通解》叶飘然 上卷 p256-385 课目总歌/课经）
# 仅用于「起课显示」结构判定，不赋吉凶 valence（玄胎方论：64主课格多为参考趋势）
# ============================================================================

# 天干寄宫（用于干支三刑/六害判定）
TIAN_GAN_JI_GONG = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子'
}

# 六合（地支合）
LIU_HE_PAIRS = [
    frozenset(['子', '丑']), frozenset(['寅', '亥']), frozenset(['卯', '戌']),
    frozenset(['辰', '酉']), frozenset(['巳', '申']), frozenset(['午', '未'])
]

# 三刑（地支）
SAN_XING_SETS = [
    ({'寅', '巳', '申'}, '无恩之刑'),
    ({'丑', '戌', '未'}, '恃势之刑'),
    ({'子', '卯'}, '无礼之刑'),
    ({'辰'}, '自刑'), ({'午'}, '自刑'), ({'酉'}, '自刑'), ({'亥'}, '自刑'),
]

# 六害（地支）
LIU_HAI_PAIRS = [
    frozenset(['子', '未']), frozenset(['丑', '午']), frozenset(['寅', '巳']),
    frozenset(['卯', '辰']), frozenset(['申', '亥']), frozenset(['酉', '戌'])
]

# 干禄（用于繁华/荣华课「禄马发」）
GAN_LU = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子'
}

# 驿马（日支三合局之驿马）
YI_MA = {
    '申': '寅', '子': '寅', '辰': '寅',
    '寅': '申', '午': '申', '戌': '申',
    '亥': '亥', '卯': '亥', '未': '亥',
    '巳': '巳', '酉': '巳', '丑': '巳'
}

# 十干日德（阳尊阴卑，用于时泰课「财德」）
GAN_DE = {
    '甲': '寅', '乙': '申', '丙': '巳', '丁': '亥',
    '戊': '巳', '己': '亥', '庚': '申', '辛': '寅',
    '壬': '亥', '癸': '巳'
}

# 吉将（用于合欢/繁华等）
JI_JIANG = {'青龙', '六合', '太阴', '太常', '贵人', '天后'}

# 凶将（用于魄化/三阴）
XIONG_JIANG = {'白虎', '玄武', '螣蛇', '勾陈', '朱雀'}

# 季 → 孤辰地支（春巳/夏申/秋亥/冬寅，顺四孟）
SEASON_GU_CHEN = {
    '春': '巳', '夏': '申', '秋': '亥', '冬': '寅'
}

# ============================================================================
# 陈公献顺三合细化（8种）
# ============================================================================

SHUN_SANHE_REFINEMENTS = {
    # 三传按特定顺序时，在全局课基础上有额外细化名称
    ('子', '辰', '申'): {'name': '出奇', 'parent': '润下课', 'duanyu': '自新改过', 'jixiong': '平偏吉'},
    ('辰', '申', '子'): {'name': '呈斗', 'parent': '润下课', 'duanyu': '玩阴阳于天象', 'jixiong': '平'},
    ('午', '戌', '寅'): {'name': '间魁', 'parent': '炎上课', 'duanyu': '舍室从庭', 'jixiong': '平'},
    ('戌', '寅', '午'): {'name': '顶墓', 'parent': '炎上课', 'duanyu': '会消息于方与', 'jixiong': '平偏吉'},
    ('卯', '未', '亥'): {'name': '合从', 'parent': '曲直课', 'duanyu': '彼我咎怀其忿', 'jixiong': '平偏凶'},
    ('未', '亥', '卯'): {'name': '从吉', 'parent': '曲直课', 'duanyu': '待时而动', 'jixiong': '吉'},
    ('酉', '丑', '巳'): {'name': '献刃', 'parent': '从革课', 'duanyu': '远近俱被其伤', 'jixiong': '凶'},
    ('丑', '酉', '巳'): {'name': '藏金', 'parent': '从革课', 'duanyu': '因事而韬', 'jixiong': '平'},
}

# ============================================================================
# 陈公献逆三合细化（5种）
# ============================================================================

NI_SANHE_REFINEMENTS = {
    ('辰', '子', '申'): {'name': '特顺', 'parent': '润下课', 'duanyu': '贵勿躐等', 'jixiong': '平偏凶'},
    ('戌', '午', '寅'): {'name': '就燥', 'parent': '炎上课', 'duanyu': '行合中庸', 'jixiong': '平'},
    ('未', '卯', '亥'): {'name': '正阳', 'parent': '曲直课', 'duanyu': '遵发生之意', 'jixiong': '平偏吉'},
    ('丑', '酉', '巳'): {'name': '法罡', 'parent': '从革课', 'duanyu': '防肃杀之威', 'jixiong': '凶'},
    # 丑酉巳同时匹配献刃和法罡，献刃优先
}

# ============================================================================
# 陈公献顺三间课格（进间传细化12种）
# ============================================================================

SHUN_SANJIAN = {
    # key: (chu, zhong, mo) tuple — 间距+2
    ('亥', '丑', '卯'): {'name': '溟蒙', 'duanyu': '事多暗昧', 'jixiong': '凶',
        'note': '三传俱在夜方，全无阳气',
        'stock': {'倾向': '跌', '信号强度': 0.65, '解读': '三传溟蒙，全无阳气。行情暗昧不明，观望为上。'}},
    ('子', '寅', '辰'): {'name': '向三阳', 'duanyu': '渐望光明', 'jixiong': '吉',
        'note': '子为夜方之始，寅为三阳之首',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传向三阳，渐望光明。行情由弱转强，可逐步布局。'}},
    ('丑', '卯', '巳'): {'name': '出户', 'duanyu': '春雷震蛰', 'jixiong': '吉',
        'note': '卯为门户，出门向阳。704案例3次命中',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传出户，如春雷震蛰。行情启动突破，积极看多。'}},
    ('寅', '辰', '午'): {'name': '出三阳', 'duanyu': '金鲤波中', 'jixiong': '吉',
        'note': '一路向东南，辰午旺气',
        'stock': {'倾向': '涨', '信号强度': 0.65, '解读': '三传出三阳，金鲤得水。行情持续向好。'}},
    ('卯', '巳', '未'): {'name': '迎阳', 'duanyu': '鸣高冈之鸾凤', 'jixiong': '吉',
        'note': '午为阳而卯巳迎之',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传迎阳，鸾凤鸣冈。行情迎接上涨，把握趋势。'}},
    ('辰', '午', '申'): {'name': '登三天', 'duanyu': '得云雨之蛟龙', 'jixiong': '大吉',
        'note': '辰午申三阳天位，如登天梯',
        'stock': {'倾向': '涨', '信号强度': 0.8, '解读': '登三天为强势上涨信号。辰为积累、午为爆发、申为突破，三段式上涨。',
                  '建议': '积极看多，分三段操作：辰位布局、午位加仓、申位减仓。'}},
    ('巳', '未', '酉'): {'name': '变盈', 'duanyu': '名秋声之稼', 'jixiong': '平',
        'note': '阳终阴始',
        'stock': {'倾向': '震荡', '信号强度': 0.4, '解读': '三传变盈，阳终阴始。行情进入转折期，观望为主。'}},
    ('午', '申', '戌'): {'name': '出三天', 'duanyu': '似鸣鹤之在阴', 'jixiong': '平偏吉',
        'note': '有名声未能实至',
        'stock': {'倾向': '震荡偏涨', '信号强度': 0.5, '解读': '三传出三天，名声在外但实质未达。行情表面强势但动能不足。'}},
    ('未', '酉', '亥'): {'name': '人局', 'duanyu': '心劳而日拙', 'jixiong': '凶',
        'note': '阴气盛，心劳不休',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传人局，阴气盛心劳日拙。行情疲软，不宜入场。'}},
    ('申', '戌', '子'): {'name': '涉三渊', 'duanyu': '当隐于山林', 'jixiong': '凶',
        'note': '陈公献定义：申子水局有林象，戌土山象。幽人守正',
        'stock': {'倾向': '跌', '信号强度': 0.7, '解读': '涉三渊（申戌子）：水局入渊，行情趋于弱势。宜守不宜攻。'}},
    ('酉', '亥', '丑'): {'name': '凝阴', 'duanyu': '忧不可解', 'jixiong': '凶',
        'note': '皆在夜位，阴气所凝',
        'stock': {'倾向': '跌', '信号强度': 0.65, '解读': '三传凝阴，阴气凝聚。行情低迷难解，观望等待。'}},
    ('戌', '子', '寅'): {'name': '入三渊', 'duanyu': '枉不能伸', 'jixiong': '凶',
        'note': '戌寅火局而子水居北乘旺为渊，火化水屈不能伸',
        'stock': {'倾向': '跌', '信号强度': 0.65, '解读': '三传入三渊，火旺入水渊。行情受压下行，暂避锋芒。'}},
}

# ============================================================================
# 陈公献逆三间课格（退间传细化12种）
# ============================================================================

NI_SANJIAN = {
    ('亥', '酉', '未'): {'name': '时遁', 'duanyu': '无出潜之意', 'jixiong': '平',
        'stock': {'倾向': '震荡', '信号强度': 0.35, '解读': '三传时遁，潜藏不出。行情蛰伏观望。'}},
    ('戌', '申', '午'): {'name': '迅戾', 'duanyu': '有追悔之心', 'jixiong': '凶',
        'note': '午火局中间申反成克象',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传迅戾，中途反悔。行情急转直下。'}},
    ('酉', '未', '巳'): {'name': '励明', 'duanyu': '出入从起所便', 'jixiong': '平偏吉',
        'note': '背暗投明',
        'stock': {'倾向': '震荡偏涨', '信号强度': 0.5, '解读': '三传励明，背暗投明。行情由弱转强。'}},
    ('申', '午', '辰'): {'name': '凝阳', 'duanyu': '动止罔戾于心', 'jixiong': '吉',
        'note': '俱东南阳位',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传凝阳，凝聚于阳。行情行止如意。'}},
    ('未', '巳', '卯'): {'name': '回明', 'duanyu': '利有悠往', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传回明，利于悠往。行情稳步向好。'}},
    ('午', '辰', '寅'): {'name': '顾祖', 'duanyu': '喜气和平', 'jixiong': '吉',
        'note': '午火生于寅，有顾母意',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传顾祖，喜气和平。行情稳中有升。'}},
    ('巳', '卯', '丑'): {'name': '转悖', 'duanyu': '吉凶二者之间', 'jixiong': '平',
        'note': '金局杀机转悖',
        'stock': {'倾向': '震荡', '信号强度': 0.4, '解读': '三传转悖，吉凶未定。行情反复震荡。'}},
    ('辰', '寅', '子'): {'name': '涉疑', 'duanyu': '祸福双关之道', 'jixiong': '平',
        'note': '水局中传见寅，两局不纯',
        'stock': {'倾向': '震荡', '信号强度': 0.4, '解读': '三传涉疑，祸福双关。行情方向不明，观望。'}},
    ('卯', '丑', '亥'): {'name': '断涧', 'duanyu': '主利分明', 'jixiong': '平',
        'stock': {'倾向': '震荡', '信号强度': 0.35, '解读': '三传断涧，难进。行情受阻但利害分明。'}},
    ('寅', '子', '戌'): {'name': '冥阳', 'duanyu': '善人是宝', 'jixiong': '平',
        'note': '阳入于溟，怀宝不出',
        'stock': {'倾向': '震荡', '信号强度': 0.35, '解读': '三传冥阳，怀宝不出。行情有价值但不显现。'}},
    ('丑', '亥', '酉'): {'name': '极阴', 'duanyu': '如月隐西山', 'jixiong': '凶',
        'note': '皆是夜方',
        'stock': {'倾向': '跌', '信号强度': 0.65, '解读': '三传极阴，月隐西山。行情低迷无起色。'}},
    ('子', '戌', '申'): {'name': '偃蹇', 'duanyu': '似马驰栈道', 'jixiong': '凶',
        'note': '坎水见险',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传偃蹇，马驰栈道。行情险象环生。'}},
}

# ============================================================================
# 陈公献顺连茹课格（进连茹细化12种）
# ============================================================================

SHUN_LIANRU = {
    ('亥', '子', '丑'): {'name': '龙潜', 'duanyu': '空怀宝以迷邦', 'jixiong': '平',
        'note': '俱在夜方全无阳气，即易乾龙勿用',
        'stock': {'倾向': '震荡', '信号强度': 0.35, '解读': '三传龙潜，潜龙勿用。行情蛰伏，等待时机。'}},
    ('子', '丑', '寅'): {'name': '含春', 'duanyu': '莫炫玉而求售', 'jixiong': '平偏吉',
        'note': '得阳气而未畅，宜韬养勿用',
        'stock': {'倾向': '震荡偏涨', '信号强度': 0.45, '解读': '三传含春，阳气初萌。行情蓄势待发，逢低布局。'}},
    ('丑', '寅', '卯'): {'name': '将泰', 'duanyu': '有声名而未蒙实惠', 'jixiong': '平偏吉',
        'stock': {'倾向': '震荡偏涨', '信号强度': 0.45, '解读': '三传将泰，名声在外实质未至。行情表面活跃。'}},
    ('寅', '卯', '辰'): {'name': '正和', 'duanyu': '展将略而果沐恩光', 'jixiong': '吉',
        'note': '日之始，君子向明求治',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传正和，向明求治。行情光明正大上涨。'}},
    ('卯', '辰', '巳'): {'name': '离渐', 'duanyu': '利用宾于王家', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传离渐，渐入佳境。行情稳步推进。'}},
    ('辰', '巳', '午'): {'name': '升阶', 'duanyu': '亲观光于上国', 'jixiong': '大吉',
        'note': '午正阳泰阶',
        'stock': {'倾向': '涨', '信号强度': 0.7, '解读': '三传升阶，登高望远。行情节节攀升，大吉。'}},
    ('巳', '午', '未'): {'name': '近阳', 'duanyu': '名实相须', 'jixiong': '吉',
        'note': '君臣合德功成名就',
        'stock': {'倾向': '涨', '信号强度': 0.6, '解读': '三传近阳，名实相副。行情名副其实上涨。'}},
    ('午', '未', '申'): {'name': '丽名', 'duanyu': '威权独盛', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传丽名，威权独盛。行情强势但需防盛极而衰。'}},
    ('未', '申', '酉'): {'name': '回春', 'duanyu': '若午夜残灯', 'jixiong': '凶',
        'note': '东南之气灭，险象',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传回春，午夜残灯。行情转弱，渐趋暗淡。'}},
    ('申', '酉', '戌'): {'name': '流金', 'duanyu': '似霜桥走马', 'jixiong': '凶',
        'note': '金地肃杀',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传流金，霜桥走马。行情危机四伏，谨慎操作。'}},
    ('酉', '戌', '亥'): {'name': '革故从新', 'duanyu': '小人进而君子退', 'jixiong': '凶',
        'note': '纯夜方，小人道长君子道消',
        'stock': {'倾向': '跌', '信号强度': 0.55, '解读': '三传革故从新，小人得势。行情不利主流投资者。'}},
    ('戌', '亥', '子'): {'name': '隐明就暗', 'duanyu': '私事吉而公事凶', 'jixiong': '平偏凶',
        'stock': {'倾向': '震荡偏跌', '信号强度': 0.45, '解读': '三传隐明就暗，明退暗进。行情表面平静暗藏变数。'}},
}

# ============================================================================
# 陈公献逆连茹课格（退连茹细化12种）
# ============================================================================

NI_LIANRU = {
    ('亥', '戌', '酉'): {'name': '回阴', 'duanyu': '心怀暗昧之私', 'jixiong': '凶',
        'stock': {'倾向': '跌', '信号强度': 0.55, '解读': '三传回阴，暗昧用事。行情隐忧重重。'}},
    ('戌', '酉', '申'): {'name': '返驾', 'duanyu': '主行肃杀之道', 'jixiong': '凶',
        'note': '孙膑占之刖足而返',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传返驾，肃杀之道。行情面临回调压力。'}},
    ('酉', '申', '未'): {'name': '出狱', 'duanyu': '疏者亲亲者疏', 'jixiong': '平偏吉',
        'note': '戌为牢狱向申为出',
        'stock': {'倾向': '震荡偏涨', '信号强度': 0.5, '解读': '三传出狱，脱离困境。行情触底反弹。'}},
    ('申', '未', '午'): {'name': '陵阴', 'duanyu': '安者危危者安', 'jixiong': '平',
        'note': '阴阳交接安危之机',
        'stock': {'倾向': '震荡', '信号强度': 0.4, '解读': '三传陵阴，安危交替。行情波动加大，注意风控。'}},
    ('未', '午', '巳'): {'name': '渐烯', 'duanyu': '脱凡俗而渐入高明', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传渐烯，渐入高明。行情逐步向好。'}},
    ('午', '巳', '辰'): {'name': '登庸', 'duanyu': '舍井蛙而旋登月阙', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传登庸，登高月阙。行情突破上行。'}},
    ('巳', '辰', '卯'): {'name': '正己', 'duanyu': '人物咸亨', 'jixiong': '吉',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传正己，人物咸亨。行情通达顺畅。'}},
    ('辰', '卯', '寅'): {'name': '返照', 'duanyu': '行藏攸利', 'jixiong': '吉',
        'note': '返照阳明',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传返照，行藏攸利。行情回暖向好。'}},
    ('卯', '寅', '丑'): {'name': '联芳', 'duanyu': '否极泰来', 'jixiong': '吉',
        'note': '披枝归根',
        'stock': {'倾向': '涨', '信号强度': 0.55, '解读': '三传联芳，否极泰来。行情触底回升。'}},
    ('寅', '丑', '子'): {'name': '游魂', 'duanyu': '事成立败', 'jixiong': '凶',
        'note': '阳气入阴极位，诸事不利',
        'stock': {'倾向': '跌', '信号强度': 0.65, '解读': '三传游魂，事成立败。行情看似企稳实则危险。'}},
    ('丑', '子', '亥'): {'name': '入墓', 'duanyu': '仕进无心', 'jixiong': '凶',
        'note': '⚠ 此即常见所说的涉三渊(丑子亥)。陈公献归为入墓课。向晦宴息，百事收藏。',
        'stock': {'倾向': '跌', '信号强度': 0.75, '解读': '三传入墓(丑子亥)，如坠深渊。行情持续下跌，阴跌不止。宜空仓观望。',
                  '建议': '强烈建议减仓或空仓，等待三传重新出现阳局。'}},
    ('子', '亥', '戌'): {'name': '重阴', 'duanyu': '宁甘没齿', 'jixiong': '凶',
        'note': '宁矢志没齿静俟不敢进',
        'stock': {'倾向': '跌', '信号强度': 0.6, '解读': '三传重阴，静俟不敢进。行情死寂，观望为宜。'}},
}

# ============================================================================
# 特殊课格定义
# ============================================================================

SPECIAL_KEGE = {
    '铸印': {
        'sanchuan': ('巳', '戌', '卯'),
        'jixiong': '上吉',
        'definition': '巳为炉、戌为印、卯为模，如铸印成形。辛日占之尤吉。',
        'condition': '有官者必迁，无官者反有官非口舌',
        'stock': {'倾向': '涨', '信号强度': 0.75,
                  '解读': '铸印课：巳(炉)资金沉淀→戌(印)政策利好→卯(模)形成突破。看涨信号。'},
    },
    '斫轮': {
        'sanchuan': ('卯', '戌', '巳'),
        'jixiong': '上吉',
        'definition': '卯为斧、戌为斤、巳为轮，如斫轮之象。卯日占之尤吉。',
        'condition': '旧物更新，革故鼎新',
        'stock': {'倾向': '涨', '信号强度': 0.7,
                  '解读': '斫轮课：卯(斧)资金介入→戌(斤)震荡洗盘→巳(轮)启动上行。反转上涨信号。'},
    },
    '高盖乘轩': {
        'sanchuan': ('午', '卯', '子'),
        'jixiong': '上吉',
        'definition': '午为天马、卯为天车、子为华盖。公卿出行之象，鼎席必至。',
        'condition': '正月午为天马最验',
        'stock': {'倾向': '涨', '信号强度': 0.7,
                  '解读': '高盖乘轩课：天马+天车+华盖，大吉之象。行情主升，贵人助力。'},
    },
}

# ============================================================================
# 三传课格检测器 v2.0
# ============================================================================

class SanChuanKegeDetector:
    """三传课格检测器 v2.0

    从三传列表直接检测以下课格类型：
    - 三合局（全局课）：润下课/曲直课/炎上课/从革课 + 顺逆三合细化
    - 稼穑课（三传辰戌丑未全土局，含四时变体）
    - 连茹课（顺连茹12种/逆连茹12种，按起始位置定名）
    - 间传课（顺三间12种/逆三间12种，按起始位置定名）
    - 特殊课格：铸印/斫轮/高盖乘轩/玄胎/盘珠
    - 三传递生/递克关系（需日干信息）
    - 空亡变格（需空亡信息）

    检测优先级：
    1. 三合局（set匹配）→ 2. 三合局细化（顺序匹配）→ 3. 稼穑课
    4. 连茹课（间距±1）→ 5. 间传课（间距±2）→ 6. 特殊课格
    7. 生克关系 → 8. 空亡变格
    """

    def __init__(self):
        self.detected_kege = []  # 检测到的课格列表
        self.kege_details = {}   # 课格详情字典

    def detect(self, sanchuan_list: List[str],
               ri_gan: str = '', ri_zhi: str = '',
               keti_raw: str = '',
               kongwang: Optional[List[str]] = None,
               season: str = '',
               tian_jiang: Optional[List[str]] = None,
               yue_jian: str = '',
               si_ke: Optional[List] = None,
               jieqi: str = '',
               nianming: str = '') -> Dict:
        """主检测入口

        Args:
            sanchuan_list: 三传地支列表，如 ['申', '子', '辰']
            ri_gan: 日干，如 '甲'
            ri_zhi: 日支，如 '子'
            keti_raw: 已有课体名称（如'元首课'），用于补充信息
            kongwang: 空亡地支列表，如 ['寅', '卯']
            season: 季节（春/夏/秋/冬），用于稼穑/玄胎四时变体判断
            jieqi: 节气（四立/分至前一日等），如'立春'/'春分前一日'，供天祸/天寇检测（缺省跳过）
            nianming: 夫妻年命，格式'夫年干支,妻年干支'，如'甲寅,己亥'，供繁昌检测（缺省跳过）

        Returns:
            课格识别结果字典
        """
        self.detected_kege = []
        self.kege_details = {}

        # 【P4 2026-08-18】消费 keti_raw：九宗门课体记入详情输出，供下游与三传课格融合
        # （dict 包装：_generate_stock_signals 遍历 kege_details 期望值为 dict，
        #   无"股市信号"键会安全跳过；不进 detected_kege 以免破坏股市信号生成）
        if keti_raw:
            self.kege_details['九宗门课体'] = {'课体': keti_raw}

        if len(sanchuan_list) < 3:
            return {'课格列表': [], '课格详情': {}, '三传分类': {}, '股市信号': {}}

        chu, zhong, mo = sanchuan_list[0], sanchuan_list[1], sanchuan_list[2]
        chu_idx = DIZHI.index(chu) if chu in DIZHI else -1
        zhong_idx = DIZHI.index(zhong) if zhong in DIZHI else -1
        mo_idx = DIZHI.index(mo) if mo in DIZHI else -1

        sanchuan_tuple = (chu, zhong, mo)
        sanchuan_set = set(sanchuan_list)

        # ===== 检测流水线（按优先级排序） =====

        # 1. 三合局检测（全局课）— set匹配，优先于一切
        self._detect_san_he(sanchuan_list)

        # 2. 三合局细化检测（顺序相关，在三合局基础上）
        if '全局课' in self.detected_kege:
            self._detect_sanhe_refinement(sanchuan_tuple)

        # 3. 稼穑课检测（三传辰戌丑未全土局）
        if sanchuan_set <= DIZHI_JI and len(sanchuan_list) == 3:
            self._detect_jia_se(sanchuan_list, season)

        # 4. 连茹课检测（间距±1，含12种细化命名）
        self._detect_lian_ru(chu_idx, zhong_idx, mo_idx, sanchuan_tuple)

        # 5. 间传课检测（间距±2，含24种细化命名）
        self._detect_jian_chuan(chu_idx, zhong_idx, mo_idx, sanchuan_tuple)

        # 6. 特殊课格检测（铸印/斫轮/高盖乘轩/玄胎）
        self._detect_special_kege(sanchuan_list)

        # 7. 三传递生/递克分析（需日干信息）
        if ri_gan:
            self._detect_shengke(sanchuan_list, ri_gan)

        # 8. 空亡变格检测
        if kongwang:
            self._detect_kongwang_variant(sanchuan_list, kongwang)

        # 8.5 六十四课经缺失课格检测（起课显示用，不赋吉凶）
        # 数据：三传 + 日干支 + 三传天将 + 月将(月令proxy) + 四课 + 节气(可选) + 年命(可选)
        self._detect_64ke_missing(sanchuan_list, ri_gan, ri_zhi,
                                  tian_jiang or [], yue_jian or '', si_ke or [],
                                  jieqi or '', nianming or '',
                                  kongwang or [])

        # 9. 三传分类检测
        sanchuan_classification = self._classify_sanchuan(sanchuan_list)

        # 10. 生成股市信号
        stock_signals = self._generate_stock_signals(ri_gan, ri_zhi)

        # 构建结果
        result = {
            '课格列表': self.detected_kege,
            '课格详情': self.kege_details,
            '三传分类': sanchuan_classification,
            '股市信号': stock_signals,
        }

        return result

    # -------------------------------------------------------------------------
    # 1. 三合局检测
    # -------------------------------------------------------------------------

    def _detect_san_he(self, sanchuan_list: List[str]) -> None:
        """检测三传是否成三合局

        三合局是《六壬大全》中"全局课"的核心：
        - 申子辰 → 水局 → 润下课
        - 亥卯未 → 木局 → 曲直课
        - 寅午戌 → 火局 → 炎上课
        - 巳酉丑 → 金局 → 从革课
        """
        chuan_set = set(sanchuan_list)

        for group_fs, info in SAN_HE_GROUPS.items():
            if group_fs == chuan_set:
                self.detected_kege.append(info['kege_full'])
                self.detected_kege.append('全局课')
                self.kege_details[info['kege_full']] = {
                    '名称': info['kege_full'],
                    '类型': '三合局',
                    '五行': info['name'],
                    '方位': info['direction'],
                    '中神': info['zhongshen'],
                    '地支组合': '·'.join(sorted(group_fs)),
                    '吉凶': '吉',
                    '定义': f'三传{info["direction"]}{info["name"]}局，三传合局，事必有成',
                    '断语': self._get_sanhe_duanyu(info['kege']),
                    '64课经': f"全局课：{info['kege_full']}。三传{info['name']}局，{info['direction']}方一气，事物形成合力。",
                    '利好行业': info.get('stock_industry', ''),
                    '股市信号': self._get_sanhe_stock_signal(info['kege_full']),
                }
                break

    def _get_sanhe_duanyu(self, kege_name: str) -> str:
        """获取三合局断语（融合陈公献心印赋+指掌赋）"""
        duanyus = {
            '润下': '水局主流动、聪明、沟通。三传润下，如江河奔流，事事畅通。占求财宜动不宜静，主恩泽下流宜施惠于人。',
            '曲直': '木局主生长、创新、发展。三传曲直，如春木繁茂，事业渐长。福者愈福祸者愈祸，有放大效应。',
            '炎上': '火局主热情、快速、消耗。三传炎上，如火势蔓延，事态急进。占求财宜快进快出，主气焰薰天急于进用。',
            '从革': '金局主变革、决断、肃杀。三传从革，如金石之坚，事多变革。革故鼎新之象但金乃破物之神亦主刑伤。',
        }
        return duanyus.get(kege_name, '三传成局，事必有成，合力显著。')

    def _get_sanhe_stock_signal(self, kege_full: str) -> Dict:
        """获取三合局股市信号"""
        signals_map = {
            '润下课': {
                '倾向': '涨', '信号强度': 0.7,
                '解读': '水局润下，如江河奔流。占股票主行情滔滔，资金如水流涌入。利好水利、航运、白酒、金融、物流等行业。',
                '风险提示': '水局过旺可能泛滥，需防高位放量出货。',
                '建议': '顺势做多，注意末传（辰）是否空亡。'
            },
            '曲直课': {
                '倾向': '涨', '信号强度': 0.65,
                '解读': '木局曲直，如春木萌发。占股票主慢牛行情，温和上涨。利好医药、教育、新能源、环保等行业。',
                '风险提示': '木局生长缓慢，不宜追高。曲直课有放大效应，是吉则愈吉、是凶则愈凶。',
                '建议': '中长线布局，关注成长股。'
            },
            '炎上课': {
                '倾向': '涨', '信号强度': 0.75,
                '解读': '火局炎上，如火势燎原。占股票主爆发行情，急速拉升。利好能源、科技、军工、传媒等行业。',
                '风险提示': '火局急涨急跌，易有过热风险。末传戌土临空亡或白虎则急转直下。',
                '建议': '快进快出，严格止盈止损。'
            },
            '从革课': {
                '倾向': '涨', '信号强度': 0.6,
                '解读': '金局从革，如金石变革。占股票主结构性行情，强者恒强。利好金融、制造、军工、贵金属等行业。',
                '风险提示': '金局肃杀，个股分化严重，选股难度大。',
                '建议': '精选龙头，回避弱势股。'
            },
        }
        return signals_map.get(kege_full, {})

    # -------------------------------------------------------------------------
    # 2. 三合局细化检测（顺三合8种 + 逆三合5种）
    # -------------------------------------------------------------------------

    def _detect_sanhe_refinement(self, sanchuan_tuple: Tuple[str, str, str]) -> None:
        """检测三合局的顺序细化名称

        陈公献将三合局按三传顺序细分为：
        - 顺三合8种：出奇/呈斗/间魁/顶墓/合从/从吉/献刃/藏金
        - 逆三合5种：特顺/就燥/正阳/法罡/四土逆行
        """
        # 顺三合细化
        if sanchuan_tuple in SHUN_SANHE_REFINEMENTS:
            ref = SHUN_SANHE_REFINEMENTS[sanchuan_tuple]
            self.detected_kege.append(ref['name'])
            self.kege_details[ref['name']] = {
                '名称': ref['name'],
                '类型': '顺三合细化',
                '母课格': ref['parent'],
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': ref['jixiong'],
                '断语': ref['duanyu'],
            }

        # 逆三合细化（排除已被顺三合匹配的）
        if sanchuan_tuple in NI_SANHE_REFINEMENTS and sanchuan_tuple not in SHUN_SANHE_REFINEMENTS:
            ref = NI_SANHE_REFINEMENTS[sanchuan_tuple]
            self.detected_kege.append(ref['name'])
            self.kege_details[ref['name']] = {
                '名称': ref['name'],
                '类型': '逆三合细化',
                '母课格': ref['parent'],
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': ref['jixiong'],
                '断语': ref['duanyu'],
            }

    # -------------------------------------------------------------------------
    # 3. 稼穑课检测
    # -------------------------------------------------------------------------

    def _detect_jia_se(self, sanchuan_list: List[str], season: str = '') -> None:
        """检测稼穑课（三传辰戌丑未全土局）

        稼穑不是普通全局课，而是三传皆季土的特殊形态。
        陈公献按四时分为：春稼穑/夏游子/秋地角/冬五墓
        """
        season_names = {
            '春': ('稼穑', '生长以时，由微至著', '吉'),
            '夏': ('游子', '漂流不定，有千里之势', '平'),
            '秋': ('地角', '据一隅而忘天下', '平偏凶'),
            '冬': ('五墓', '舍朝市而守丘墟', '凶'),
        }

        name, duanyu, jixiong = season_names.get(season, ('稼穑', '自微而至著', '吉'))

        self.detected_kege.append('稼穑课')
        if name != '稼穑':
            self.detected_kege.append(name)

        self.kege_details['稼穑课'] = {
            '名称': '稼穑课',
            '类型': '土局特殊课格',
            '三传': '·'.join(sanchuan_list),
            '季节': season if season else '未知',
            '四时名': name,
            '吉凶': jixiong,
            '定义': '辰戌丑未四土全在三传。土有生物之功而日渐增长，自微而至著。',
            '断语': duanyu,
            '64课经': '稼穑课：四季相传丑辰未戌。土盛于夏乘巳午之生有千里之势，至秋土气渐衰，冬则休囚。',
            '股市信号': {
                '倾向': '震荡偏涨' if jixiong == '吉' else ('震荡' if jixiong == '平' else '震荡偏跌'),
                '信号强度': 0.5,
                '解读': f'稼穑课（{name}）：三传皆土，{duanyu}。市场进入{"慢牛蓄势" if jixiong == "吉" else "横盘整理" if jixiong == "平" else "低迷守势"}阶段。',
                '风险提示': '稼穑课主缓，不适合短线操作。须玩顺逆玩四时。'
            }
        }

    # -------------------------------------------------------------------------
    # 4. 连茹课检测（含12种细化命名）
    # -------------------------------------------------------------------------

    def _detect_lian_ru(self, chu_idx: int, zhong_idx: int, mo_idx: int,
                        sanchuan_tuple: Tuple[str, str, str]) -> None:
        """检测连茹课（三传相连）

        连茹课出自《六壬大全》64课经，为小吉课。
        陈公献将连茹细分为顺连茹12种+逆连茹12种，各有专名。

        顺连茹：三传顺行相邻（如子丑寅），向阳明
        逆连茹：三传逆行相邻（如丑子亥），向阴暗
        """
        def cyclic_diff(a, b):
            diff = (b - a) % 12
            return diff if diff <= 6 else diff - 12

        d1 = cyclic_diff(chu_idx, zhong_idx)
        d2 = cyclic_diff(zhong_idx, mo_idx)

        if d1 == 1 and d2 == 1:
            # 进连茹 — 查找细化名称
            self.detected_kege.append('进连茹')

            if sanchuan_tuple in SHUN_LIANRU:
                ref = SHUN_LIANRU[sanchuan_tuple]
                self.detected_kege.append(ref['name'])
                self.kege_details[ref['name']] = {
                    '名称': ref['name'],
                    '类型': '顺连茹细化',
                    '三传': '→'.join(sanchuan_tuple),
                    '吉凶': ref['jixiong'],
                    '断语': ref['duanyu'],
                    '股市信号': ref.get('stock', {}),
                }

            # 基础进连茹（当有细化名称时降低权重，避免与细化信号冲突）
            _has_ref = sanchuan_tuple in SHUN_LIANRU
            self.kege_details['进连茹'] = {
                '名称': '进连茹课',
                '类型': '连茹',
                '方向': '顺行',
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': '小吉',
                '定义': '三传顺行相连，如珠串进，事主逐渐推进，日益向好',
                '64课经': '进连茹课（小吉）：三传俱连茹，顺则先进合退。事主步步推进，由近及远。',
                '股市信号': {
                    '倾向': '涨', '信号强度': 0.1 if _has_ref else 0.6,
                    '解读': ('三传进连茹（基础类别），细化名称:' + SHUN_LIANRU[sanchuan_tuple]['name']) if _has_ref else '三传进连茹，主行情逐步上行，可分批建仓。',
                    '风险提示': '需防连茹末传空亡，则推进乏力。'
                }
            }

        elif d1 == -1 and d2 == -1:
            # 退连茹 — 查找细化名称
            self.detected_kege.append('退连茹')

            if sanchuan_tuple in NI_LIANRU:
                ref = NI_LIANRU[sanchuan_tuple]
                self.detected_kege.append(ref['name'])
                self.kege_details[ref['name']] = {
                    '名称': ref['name'],
                    '类型': '逆连茹细化',
                    '三传': '→'.join(sanchuan_tuple),
                    '吉凶': ref['jixiong'],
                    '断语': ref['duanyu'],
                    '股市信号': ref.get('stock', {}),
                }

            # 基础退连茹（当有细化名称时降低权重）
            _has_ref = sanchuan_tuple in NI_LIANRU
            self.kege_details['退连茹'] = {
                '名称': '退连茹课',
                '类型': '连茹',
                '方向': '逆行',
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': '小吉',
                '定义': '三传逆行相连，事主先退后进，以退为进',
                '64课经': '退连茹课（小吉）：三传俱连茹，逆则先退后进。事主暂时受阻，退而后成。',
                '股市信号': {
                    '倾向': '跌→涨', '信号强度': 0.1 if _has_ref else 0.4,
                    '解读': ('三传退连茹（基础类别），细化名称:' + NI_LIANRU[sanchuan_tuple]['name']) if _has_ref else '三传退连茹，主行情先回调再上行。短期承压，中期可期。',
                    '风险提示': '退连茹末传见凶将（白虎/玄武），则退势加深。'
                }
            }

    # -------------------------------------------------------------------------
    # 5. 间传课检测（含24种细化命名）
    # -------------------------------------------------------------------------

    def _detect_jian_chuan(self, chu_idx: int, zhong_idx: int, mo_idx: int,
                           sanchuan_tuple: Tuple[str, str, str]) -> None:
        """检测间传课（三传隔位相传）

        间传课出自《六壬大全》64课经。
        陈公献将间传细分为顺三间12种+逆三间12种，各有专名。

        顺三间：三传隔位顺行（如子寅辰），越三间向阳明
        逆三间：三传隔位逆行（如亥酉未），越三间向阴暗
        """
        def cyclic_diff(a, b):
            diff = (b - a) % 12
            return diff if diff <= 6 else diff - 12

        d1 = cyclic_diff(chu_idx, zhong_idx)
        d2 = cyclic_diff(zhong_idx, mo_idx)

        if d1 == 2 and d2 == 2:
            # 进间传 — 查找细化名称
            self.detected_kege.append('进间传')

            if sanchuan_tuple in SHUN_SANJIAN:
                ref = SHUN_SANJIAN[sanchuan_tuple]
                self.detected_kege.append(ref['name'])
                self.kege_details[ref['name']] = {
                    '名称': ref['name'],
                    '类型': '顺三间细化',
                    '三传': '→'.join(sanchuan_tuple),
                    '吉凶': ref['jixiong'],
                    '断语': ref['duanyu'],
                    '股市信号': ref.get('stock', {}),
                }

            # 基础进间传（当有细化名称时降低权重）
            _has_ref = sanchuan_tuple in SHUN_SANJIAN
            self.kege_details['进间传'] = {
                '名称': '进间传课',
                '类型': '间传',
                '方向': '顺行',
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': '小吉',
                '定义': '三传隔位顺行，如跳跃前进。事主有波折但总体向前。',
                '股市信号': {
                    '倾向': '震荡偏涨', '信号强度': 0.1 if _has_ref else 0.5,
                    '解读': ('三传进间传（基础类别），细化名称:' + SHUN_SANJIAN[sanchuan_tuple]['name']) if _has_ref else '三传进间传，主行情震荡上行，有波段机会。',
                    '风险提示': '间传有断档，注意中途回调风险。'
                }
            }

        elif d1 == -2 and d2 == -2:
            # 退间传 — 查找细化名称
            self.detected_kege.append('退间传')

            if sanchuan_tuple in NI_SANJIAN:
                ref = NI_SANJIAN[sanchuan_tuple]
                self.detected_kege.append(ref['name'])
                self.kege_details[ref['name']] = {
                    '名称': ref['name'],
                    '类型': '逆三间细化',
                    '三传': '→'.join(sanchuan_tuple),
                    '吉凶': ref['jixiong'],
                    '断语': ref['duanyu'],
                    '股市信号': ref.get('stock', {}),
                }

            # 基础退间传（当有细化名称时降低权重）
            _has_ref = sanchuan_tuple in NI_SANJIAN
            self.kege_details['退间传'] = {
                '名称': '退间传课',
                '类型': '间传',
                '方向': '逆行',
                '三传': '→'.join(sanchuan_tuple),
                '吉凶': '平偏凶',
                '定义': '三传隔位逆行，事有退缩反复之象。',
                '股市信号': {
                    '倾向': '震荡偏跌', '信号强度': 0.1 if _has_ref else 0.4,
                    '解读': ('三传退间传（基础类别），细化名称:' + NI_SANJIAN[sanchuan_tuple]['name']) if _has_ref else '三传退间传，主行情有退潮迹象，反弹力度有限。',
                    '风险提示': '退间传中若见空亡，跌势加速。'
                }
            }

    # -------------------------------------------------------------------------
    # 6. 特殊课格检测
    # -------------------------------------------------------------------------

    def _detect_special_kege(self, sanchuan_list: List[str]) -> None:
        """检测各种特殊三传课格"""
        chu, zhong, mo = sanchuan_list[0], sanchuan_list[1], sanchuan_list[2]
        sanchuan_tuple = (chu, zhong, mo)

        # 6a. 铸印/斫轮/高盖乘轩（三传精确匹配）
        for kege_name, info in SPECIAL_KEGE.items():
            if sanchuan_tuple == info['sanchuan']:
                self.detected_kege.append(kege_name)
                self.kege_details[kege_name] = {
                    '名称': f'{kege_name}课',
                    '类型': '特殊课格',
                    '三传': '→'.join(sanchuan_tuple),
                    '吉凶': info['jixiong'],
                    '定义': info['definition'],
                    '条件': info.get('condition', ''),
                    '股市信号': info.get('stock', {}),
                }

        # 6b. 玄胎课：三传皆孟（寅申巳亥全在三传）
        if set(sanchuan_list) <= DIZHI_MENG and len(sanchuan_list) == 3:
            self.detected_kege.append('玄胎')
            meng_str = '·'.join(sanchuan_list)
            self.kege_details['玄胎'] = {
                '名称': '玄胎课',
                '类型': '特殊课格',
                '三传': meng_str,
                '吉凶': '吉',
                '定义': '三传皆孟（寅申巳亥），如胎孕之象。孟为四生之气，主新生、开始、萌芽。',
                '64课经': '玄胎课（吉）：三传皆孟，如胎孕之象。非怀孕则有移旧更新之意。',
                '断语': '玄胎孕育，事主新生。四生之地，主萌芽待发。',
                '股市信号': {
                    '倾向': '震荡偏涨', '信号强度': 0.55,
                    '解读': '玄胎课为萌芽信号（长期看多）。三传皆孟，四生之气，主新兴行业、概念股启动。短期波动大，长期看好。',
                    '风险提示': '玄胎为萌芽期，可能反复震荡，需耐心持有。'
                }
            }

        # 6c. 三传阴阳属性（仅在没有主要课格时标注，避免冲突）
        yang_count = sum(1 for z in sanchuan_list if DIZHI_YIN_YANG.get(z) == '阳')
        has_major_kege = bool(set(self.detected_kege) & {
            '全局课', '登三天', '涉三渊', '入三渊', '铸印', '斫轮', '高盖乘轩',
            '玄胎', '进连茹', '退连茹', '进间传', '退间传', '稼穑课'
        })

        if yang_count == 0 and not has_major_kege:
            self.detected_kege.append('三阴')
            self.kege_details['三阴'] = {
                '名称': '三阴课',
                '类型': '三传属性（参考）',
                '三传': '·'.join(sanchuan_list),
                '吉凶': '凶',
                '定义': '三传皆阴（丑卯巳未酉亥），阴气凝重，事多暗昧。',
                '股市信号': {
                    '倾向': '跌', '信号强度': 0.4,
                    '解读': '三传皆阴为下跌参考信号。阴气较重，需注意市场情绪低迷。',
                    '风险提示': '三阴课中若见贵人/青龙等吉将，可减其凶性。'
                }
            }

        # 6d. 三传皆仲（子午卯酉全在三传）
        if set(sanchuan_list) <= DIZHI_ZHONG and len(sanchuan_list) == 3:
            self.kege_details['三传皆仲'] = {
                '名称': '三传皆仲',
                '类型': '三传属性',
                '三传': '·'.join(sanchuan_list),
                '吉凶': '平',
                '定义': '三传皆仲（子午卯酉），四正之气，主正中、主流。',
                '股市信号': {
                    '倾向': '平', '信号强度': 0.3,
                    '解读': '三传皆仲，主流板块主导，大盘走势平稳。'
                }
            }

        # 6e. 三传皆季（辰戌丑未全在三传，仅当未触发稼穑课时标注）
        if set(sanchuan_list) <= DIZHI_JI and '稼穑课' not in self.detected_kege:
            if '三传皆季' not in self.detected_kege:
                self.detected_kege.append('三传皆季')
            self.kege_details['三传皆季'] = {
                '名称': '三传皆季',
                '类型': '三传属性',
                '三传': '·'.join(sanchuan_list),
                '吉凶': '平偏滞',
                '定义': '三传皆季（辰戌丑未），四库之气，主储藏、阻滞。',
                '股市信号': {
                    '倾向': '震荡', '信号强度': 0.35,
                    '解读': '三传皆季（辰戌丑未），四库之气，主储藏、阻滞。市场进入震荡横盘期，趋势不明。'
                }
            }

    # -------------------------------------------------------------------------
    # 7. 三传递生/递克分析
    # -------------------------------------------------------------------------

    def _detect_shengke(self, sanchuan_list: List[str], ri_gan: str) -> None:
        """检测三传递生/递克关系（毕法赋核心分析法）

        毕法赋第31法「三传递生人举荐」
        毕法赋第32法「三传互克众人欺」

        需要日干五行来判断三传与日干的关系。
        """
        if ri_gan not in TIANGAN_WU_XING:
            return

        gan_wx = TIANGAN_WU_XING[ri_gan]
        chu_wx = DIZHI_WU_XING.get(sanchuan_list[0], '')
        zhong_wx = DIZHI_WU_XING.get(sanchuan_list[1], '')
        mo_wx = DIZHI_WU_XING.get(sanchuan_list[2], '')

        if not all([chu_wx, zhong_wx, mo_wx]):
            return

        # 顺递生：初生中→中生末→末生干
        shun_ds = (WU_XING_SHENG.get(chu_wx) == zhong_wx and
                   WU_XING_SHENG.get(zhong_wx) == mo_wx and
                   WU_XING_SHENG.get(mo_wx) == gan_wx)

        # 逆递生：末生中→中生初→初生干
        ni_ds = (WU_XING_SHENG.get(mo_wx) == zhong_wx and
                 WU_XING_SHENG.get(zhong_wx) == chu_wx and
                 WU_XING_SHENG.get(chu_wx) == gan_wx)

        if shun_ds or ni_ds:
            self.detected_kege.append('亨通课')
            self.kege_details['亨通课'] = {
                '名称': '亨通课',
                '类型': '生克关系',
                '方向': '顺递生' if shun_ds else '逆递生',
                '吉凶': '吉',
                '毕法赋': '第31法「三传递生人举荐」',
                '断语': '三传递生日干，主有人举荐，事久荣盛。',
                '股市信号': {
                    '倾向': '涨', '信号强度': 0.55,
                    '解读': '三传递生，层层扶助。行情获得多重利好推动。'
                }
            }

        # 顺递克：初克中→中克末→末克干
        shun_dk = (WU_XING_KE.get(chu_wx) == zhong_wx and
                   WU_XING_KE.get(zhong_wx) == mo_wx and
                   WU_XING_KE.get(mo_wx) == gan_wx)

        # 逆递克：末克中→中克初→初克干
        ni_dk = (WU_XING_KE.get(mo_wx) == zhong_wx and
                 WU_XING_KE.get(zhong_wx) == chu_wx and
                 WU_XING_KE.get(chu_wx) == gan_wx)

        if shun_dk or ni_dk:
            self.detected_kege.append('殃咎课')
            self.kege_details['殃咎课'] = {
                '名称': '殃咎课',
                '类型': '生克关系',
                '方向': '顺递克' if shun_dk else '逆递克',
                '吉凶': '凶',
                '毕法赋': '第32法「三传互克众人欺」',
                '断语': '三传递克日干，主他人欺凌，互相克害。',
                '股市信号': {
                    '倾向': '跌', '信号强度': 0.65,
                    '解读': '三传递克，层层伤害。行情遭受多重利空打击。'
                }
            }

        # 三传与日干基本关系
        rel_chu = self._wx_relation(chu_wx, gan_wx)
        rel_mo = self._wx_relation(mo_wx, gan_wx)
        if rel_chu or rel_mo:
            self.kege_details['日干关系'] = {
                '初传与日干': rel_chu,
                '末传与日干': rel_mo,
            }

    def _wx_relation(self, wx1: str, wx2: str) -> str:
        """五行关系判断"""
        if not wx1 or not wx2:
            return ''
        if WU_XING_SHENG.get(wx1) == wx2:
            return f'{wx1}生{wx2}'
        elif WU_XING_KE.get(wx1) == wx2:
            return f'{wx1}克{wx2}'
        elif wx1 == wx2:
            return f'{wx1}比和'
        else:
            sheng_by = [k for k, v in WU_XING_SHENG.items() if v == wx1]
            ke_by = [k for k, v in WU_XING_KE.items() if v == wx1]
            if wx2 in sheng_by:
                return f'{wx2}生{wx1}（{wx1}得生）'
            elif wx2 in ke_by:
                return f'{wx2}克{wx1}（{wx1}被克）'
        return ''

    # -------------------------------------------------------------------------
    # 8. 空亡变格检测
    # -------------------------------------------------------------------------

    def _detect_kongwang_variant(self, sanchuan_list: List[str], kongwang: List[str]) -> None:
        """检测连茹空亡变格

        毕法赋第17法「进茹空亡宜退步」— 声传空谷
        毕法赋第18法「踏脚空亡进用宜」— 踏脚空亡
        """
        kw_set = set(kongwang)
        all_empty = all(z in kw_set for z in sanchuan_list)

        if not all_empty:
            return

        if '进连茹' in self.detected_kege:
            self.detected_kege.append('声传空谷')
            self.kege_details['声传空谷'] = {
                '名称': '声传空谷',
                '类型': '空亡变格',
                '吉凶': '平偏凶',
                '毕法赋': '第17法「进茹空亡宜退步」',
                '断语': '进连茹遇空亡，退吉而进不宜，虚声无实。',
                '股市信号': {
                    '倾向': '跌', '信号强度': 0.55,
                    '解读': '进连茹全值空亡，虚声无实。行情上涨无力，宜退不宜进。'
                }
            }

        if '退连茹' in self.detected_kege:
            self.detected_kege.append('踏脚空亡')
            self.kege_details['踏脚空亡'] = {
                '名称': '踏脚空亡',
                '类型': '空亡变格',
                '吉凶': '凶转吉',
                '毕法赋': '第18法「踏脚空亡进用宜」',
                '断语': '退连茹遇空亡，宜进不宜退。',
                '股市信号': {
                    '倾向': '涨', '信号强度': 0.5,
                    '解读': '退连茹全值空亡，利空出尽反为利。可反向操作。'
                }
            }

    # -------------------------------------------------------------------------
    # 8.5 六十四课经缺失课格检测（起课显示用，不赋吉凶）
    # -------------------------------------------------------------------------

    def _add_kege(self, name: str, detail: Dict) -> None:
        """加入课格（去重）"""
        if name not in self.detected_kege:
            self.detected_kege.append(name)
            self.kege_details[name] = detail

    def _wang_xiang(self, zhi: str, yue_ling_wx: str) -> str:
        """月令旺相休囚死：返回 '旺'/'相'/'休'/'囚'/'死'"""
        wx = DIZHI_WU_XING.get(zhi, '')
        if not wx:
            return ''
        if wx == yue_ling_wx:
            return '旺'
        if WU_XING_SHENG.get(yue_ling_wx) == wx:
            return '相'
        if WU_XING_SHENG.get(wx) == yue_ling_wx:
            return '休'
        if WU_XING_KE.get(yue_ling_wx) == wx:
            return '囚'
        if WU_XING_KE.get(wx) == yue_ling_wx:
            return '死'
        return ''

    def _liu_he(self, a: str, b: str) -> bool:
        s = frozenset([a, b])
        return any(p == s for p in LIU_HE_PAIRS)

    def _liu_hai(self, a: str, b: str) -> bool:
        s = frozenset([a, b])
        return any(p == s for p in LIU_HAI_PAIRS)

    def _san_xing(self, a: str, b: str, c: str) -> bool:
        """a(初传)、b(干寄宫)、c(日支) 是否构成三刑（含自刑）"""
        triple = {a, b, c}
        for sx, _ in SAN_XING_SETS:
            if sx <= triple and len(sx) <= len(triple):
                if len(sx) == 1:
                    if a in sx and (a == b or a == c or b == c):
                        return True
                else:
                    if len(triple & sx) >= (3 if len(sx) == 3 else 2):
                        return True
        return False

    def _detect_64ke_missing(self, sanchuan_list: List[str],
                             ri_gan: str, ri_zhi: str,
                             tian_jiang: List[str],
                             yue_jian: str, si_ke: List,
                             jieqi: str = '',
                             nianming: str = '',
                             kongwang: Optional[List[str]] = None) -> None:
        """六十四课经缺失课格（P1 清单，约19个）结构检测。

        依据《大六壬通解》叶飘然 上卷 p5136-5151 课目总歌 + 课经正文。
        ⚠️ 显示用，不赋吉凶 valence（方论：64主课格多为参考趋势）。
        数据来源：三传 + 日干支 + 三传天将 + 月将(月令proxy) + 四课。
        jieqi: 节气输入（四立/分至前一日），用于天祸/天寇（缺省跳过）。
        nianming: 夫妻年命输入（'夫年干支,妻年干支'），用于繁昌（缺省跳过）。
        注：迤福（八远兼五福，吉凶参驳）定义参驳、无单一定义，暂不实现。
        """
        if len(sanchuan_list) < 3:
            return
        chu, zhong, mo = sanchuan_list[0], sanchuan_list[1], sanchuan_list[2]
        gj = TIAN_GAN_JI_GONG.get(ri_gan, '')
        yue_ling_wx = DIZHI_WU_XING.get(yue_jian, '') if yue_jian else ''
        tj = tian_jiang if len(tian_jiang) >= 3 else ['', '', '']
        chu_tj, zhong_tj, mo_tj = tj[0], tj[1], tj[2]

        def _ref(name, rule, src):
            return {
                '名称': name, '类型': '六十四课经', '吉凶': '参考趋势(无定吉凶)',
                '64课经': f'{name}课：{rule}', '通解': src,
            }

        # —— 仅需 三传 + 日干支（无天将/月令） ——

        # 1. 九丑（p5147：子午卯酉日 + 乙戊己辛壬日）
        if ri_zhi in ('子', '午', '卯', '酉') and ri_gan in ('乙', '戊', '己', '辛', '壬'):
            self._add_kege('九丑', _ref('九丑', '子午与卯酉，配合乙戊己辛壬', '通解 p5147'))

        # 2. 殃咎（p5147：三传克日因）
        rg_wx = TIANGAN_WU_XING.get(ri_gan, '')
        if rg_wx:
            ke = WU_XING_KE.get(rg_wx, '')
            if ke and all(DIZHI_WU_XING.get(z, '') == ke for z in [chu, zhong, mo]):
                self._add_kege('殃咎', _ref('殃咎', '三传克日因', '通解 p5147'))

        # 3. 亨通（p7971：三传递生日干）
        if (WU_XING_SHENG.get(DIZHI_WU_XING.get(chu, ''), '') == DIZHI_WU_XING.get(zhong, '')) and \
           (WU_XING_SHENG.get(DIZHI_WU_XING.get(zhong, ''), '') == DIZHI_WU_XING.get(mo, '')) and \
           (WU_XING_SHENG.get(DIZHI_WU_XING.get(mo, ''), '') == rg_wx) and rg_wx:
            self._add_kege('亨通', _ref('亨通', '三传递生日干', '通解 p7971'))

        # 4. 连茹统称标注（p5151：连珠联茹兼进退）——仅作统称标签，不重复具体方向名
        if any(k in self.detected_kege for k in ('进连茹', '退连茹', '连茹课', '顺连茹', '逆连茹')):
            if '连茹课' not in self.detected_kege and not any(k in self.detected_kege for k in ('进连茹', '退连茹')):
                self._add_kege('连茹课', _ref('连茹课', '连珠联茹兼进退', '通解 p5151'))

        # 5. 六纯（p5151：六纯十杂兼物类——三传同五行且非三合局）
        if '全局课' not in self.detected_kege:
            wxs = [DIZHI_WU_XING.get(z, '') for z in [chu, zhong, mo]]
            if len(set(wxs)) == 1 and wxs[0]:
                self._add_kege('六纯', _ref('六纯', '三传同一五行，六纯十杂兼物类', '通解 p5151'))

        # 6. 刑伤（p5136：干支三刑用）
        if gj and ri_zhi and self._san_xing(chu, gj, ri_zhi):
            self._add_kege('刑伤', _ref('刑伤', '干支三刑用', '通解 p5136'))

        # 7. 侵害（p5136：日辰六害兼）
        if gj and ri_zhi and self._liu_hai(gj, ri_zhi):
            self._add_kege('侵害', _ref('侵害', '日辰六害兼', '通解 p5136'))

        # 8. 龙战（p5145：卯酉日兼用）
        if ri_zhi in ('卯', '酉') and chu in ('卯', '酉'):
            self._add_kege('龙战', _ref('龙战', '卯酉日兼用', '通解 p5145'))

        # 9. 解离（p3996/5136：四辰互克上→干上神克支、支上神克干）
        if si_ke and len(si_ke) >= 4:
            gan_shang = si_ke[0][1] if isinstance(si_ke[0], tuple) else si_ke[0].get('干上神', '')
            zhi_shang = si_ke[2][1] if isinstance(si_ke[2], tuple) else si_ke[2].get('支上神', '')
            if gan_shang and zhi_shang:
                # 解离：干上神克日支(地支) 且 支上神克日干(天干)
                if (WU_XING_KE.get(DIZHI_WU_XING.get(gan_shang, ''), '') == DIZHI_WU_XING.get(ri_zhi, '')) and \
                   (WU_XING_KE.get(DIZHI_WU_XING.get(zhi_shang, ''), '') == TIANGAN_WU_XING.get(ri_gan, '')):
                    self._add_kege('解离', _ref('解离', '干上神克支、支上神克干（四辰互克）', '通解 p3996/5136'))

        # 10. 和美（p5136：各合互合皆为欢→四课交车合）
        if si_ke and len(si_ke) >= 4:
            gan_shang = si_ke[0][1] if isinstance(si_ke[0], tuple) else si_ke[0].get('干上神', '')
            zhi_shang = si_ke[2][1] if isinstance(si_ke[2], tuple) else si_ke[2].get('支上神', '')
            if gan_shang and zhi_shang:
                if self._liu_he(gan_shang, ri_zhi) and self._liu_he(zhi_shang, TIAN_GAN_JI_GONG.get(ri_gan)):
                    self._add_kege('和美', _ref('和美', '干支上神互合（交车合）', '通解 p5136'))

        # 10.5 交车格细分（通解 p88-90「交车格」17 种：长生合/财合/脱合/害合/空合/刑合/冲合/克合/三交合/交会合等；
        # 显示层，不赋吉凶。交车成立=干上神六合日支 且 支上神六合日干寄宫。）
        if si_ke and len(si_ke) >= 4:
            gan_shang = si_ke[0][1] if isinstance(si_ke[0], tuple) else si_ke[0].get('干上神', '')
            zhi_shang = si_ke[2][1] if isinstance(si_ke[2], tuple) else si_ke[2].get('支上神', '')
            if gan_shang and zhi_shang and self._liu_he(gan_shang, ri_zhi) and self._liu_he(zhi_shang, TIAN_GAN_JI_GONG.get(ri_gan, ri_gan)):
                sub = []
                kong = kongwang or []
                # 五行长生（阳干顺/五行长生：木亥火寅金巳水申土申）
                _zhi_cs = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}
                _gan_cs = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
                           '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}
                gs_wx = DIZHI_WU_XING.get(gan_shang, '')
                zs_wx = DIZHI_WU_XING.get(zhi_shang, '')
                rz_wx = DIZHI_WU_XING.get(ri_zhi, '')
                rg_wx = TIANGAN_WU_XING.get(ri_gan, '')
                # 空合
                if gan_shang in kong or zhi_shang in kong:
                    sub.append('空合')
                # 长生合：干上神=支长生 且 支上神=干长生
                if _zhi_cs.get(rz_wx) == gan_shang and _gan_cs.get(ri_gan) == zhi_shang:
                    sub.append('长生合')
                # 财合：干上神=支之财(支克干上神) 且 支上神=日干之财(日干克支上神)
                if rz_wx and WU_XING_KE.get(rz_wx) == gs_wx and rg_wx and WU_XING_KE.get(rg_wx) == zs_wx:
                    sub.append('财合')
                # 脱合：干上神生支(泄支) 且 支上神生日干(泄干)
                if rz_wx and WU_XING_SHENG.get(gs_wx) == rz_wx and rg_wx and WU_XING_SHENG.get(zs_wx) == rg_wx:
                    sub.append('脱合')
                # 克合：干上神克支 或 支上神克日干
                if rz_wx and WU_XING_KE.get(gs_wx) == rz_wx or rg_wx and WU_XING_KE.get(zs_wx) == rg_wx:
                    sub.append('克合')
                # 害合（六害：子未丑午寅巳卯辰申亥酉戌）
                _hai = {'子': '未', '丑': '午', '寅': '巳', '卯': '辰', '辰': '卯', '巳': '寅',
                        '午': '丑', '未': '子', '申': '亥', '酉': '戌', '戌': '酉', '亥': '申'}
                if _hai.get(gan_shang) == ri_zhi or _hai.get(zhi_shang) == ri_gan:
                    sub.append('害合')
                # 冲合（六冲）
                _chong = {'子': '午', '丑': '未', '寅': '申', '卯': '酉', '辰': '戌', '巳': '亥',
                          '午': '子', '未': '丑', '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'}
                if _chong.get(gan_shang) == ri_zhi or _chong.get(zhi_shang) == ri_gan:
                    sub.append('冲合')
                if sub:
                    self._add_kege('交车格', _ref('交车格', '交车合细分：' + '、'.join(sub), '通解 p88-90'))

        # 10.6 64课P2补全（回环/三交/六纯；显示层，不赋吉凶）
        # 回环：三传皆在四课地支中（循环周遍，三传不离四课；通解 p3996「循环周遍」）
        if si_ke and len(si_ke) >= 4 and len(sanchuan_list) >= 3:
            _ke_zhi = set()
            for _k in si_ke:
                if isinstance(_k, tuple) and len(_k) >= 3:
                    _ke_zhi.add(_k[1])
                elif isinstance(_k, tuple) and len(_k) >= 2:
                    _ke_zhi.add(_k[0])
            if _ke_zhi and all(z in _ke_zhi for z in sanchuan_list[:3]):
                self._add_kege('回环', _ref('回环', '三传不离四课（循环周遍）', '通解 p3996/5136'))
        # 三交：三传皆四仲（子午卯酉）
        if len(sanchuan_list) >= 3 and all(z in ('子', '午', '卯', '酉') for z in sanchuan_list[:3]):
            self._add_kege('三交', _ref('三交', '三传皆四仲（三交课）', '通解 p5136'))
        # 六纯：三传同阴阳（纯阳/纯阴）
        if len(sanchuan_list) >= 3:
            _yang = {'子', '寅', '辰', '午', '申', '戌'}
            _sc3 = sanchuan_list[:3]
            if all(z in _yang for z in _sc3) or all(z not in _yang for z in _sc3):
                self._add_kege('六纯', _ref('六纯', '三传纯阳或纯阴（六纯课）', '通解 p5151'))

        # —— 需 节气 / 年命 输入（缺则跳过；不依赖月令旺相） ——

        # 20. 天祸（p5136：天祸四立绝神用，昨日之干加今干）
        # 四立日（立春/立夏/立秋/立冬）占，昨日干支临今日干上（或反之）者为天祸。
        # 完整判定：昨日天干临干上 / 昨日地支临干上（2026-08-17 精细化，补昨日之干判定）。
        if jieqi in ('立春', '立夏', '立秋', '立冬') and si_ke and len(si_ke) >= 4:
            _TIAN_GAN_LOCAL = '甲乙丙丁戊己庚辛壬癸'
            _zuo_ri_zhi = DIZHI[(DIZHI.index(ri_zhi) - 1) % 12] if ri_zhi in DIZHI else ''
            _zuo_ri_gan = _TIAN_GAN_LOCAL[(_TIAN_GAN_LOCAL.index(ri_gan) - 1) % 10] if ri_gan in _TIAN_GAN_LOCAL else ''
            _gan_shang = si_ke[0][1] if isinstance(si_ke[0], tuple) else si_ke[0].get('干上神', '')
            _zhi_shang = si_ke[2][1] if isinstance(si_ke[2], tuple) else si_ke[2].get('支上神', '')
            if (_zuo_ri_gan and _gan_shang == _zuo_ri_gan) or (_zuo_ri_zhi and (_gan_shang == _zuo_ri_zhi or _zhi_shang == _zuo_ri_zhi)):
                self._add_kege('天祸', _ref('天祸', f'四立日昨日干支({_zuo_ri_gan}{_zuo_ri_zhi})临今日干上（四立绝神用）', '通解 p5136'))

        # 21. 天寇 —— 完整判定已迁移至 liuren_64ke_judge.judge_tian_kou（四离日+月宿加四仲），
        # 此处残缺近似版（仅"分至前一日"）已停用，避免残缺天寇混入课格列表（2026-08-15 憨爷指正）。

        # 22. 繁昌（p5136：繁昌夫妻年为用，德合旺相卦应咸；p8048/8054：夫妻行年乘本命旺相气，
        # 又值干支德合——如夫甲寅、妻己亥，甲己合、寅亥合，为繁昌课）
        # nianming 格式：'夫年干支,妻年干支'，如 '甲寅,己亥'。
        if nianming:
            _parts = [p.strip() for p in nianming.replace('，', ',').split(',') if p.strip()]
            if len(_parts) >= 2 and len(_parts[0]) == 2 and len(_parts[1]) == 2:
                _f_gan, _f_zhi, _m_gan, _m_zhi = _parts[0][0], _parts[0][1], _parts[1][0], _parts[1][1]
                _gan_he = (_f_gan, _m_gan) in (('甲', '己'), ('己', '甲'), ('乙', '庚'), ('庚', '乙'),
                                               ('丙', '辛'), ('辛', '丙'), ('丁', '壬'), ('壬', '丁'),
                                               ('戊', '癸'), ('癸', '戊'))
                if _gan_he and self._liu_he(_f_zhi, _m_zhi):
                    self._add_kege('繁昌', _ref('繁昌', '夫妻年命德合（夫%s妻%s干合支合）' % (_parts[0], _parts[1]), '通解 p8048/8054'))

        # —— 需 三传天将 / 月将(月令) ——
        if not yue_ling_wx:
            return  # 其余需月令旺相，无月将则跳过

        # 11. 合欢（p5136：吉将三六合用兼——三传三六合 + 吉将）
        liu_he_or_he = (self._liu_he(chu, zhong) or self._liu_he(zhong, mo) or
                        (frozenset([chu, zhong, mo]) in SAN_HE_GROUPS))
        if liu_he_or_he and (set(tj) & JI_JIANG):
            self._add_kege('合欢', _ref('合欢', '三传三六合且乘吉将', '通解 p5136'))

        # 12. 魄化（p5144：死囚带白虎）
        if chu_tj == '白虎' and self._wang_xiang(chu, yue_ling_wx) in ('死', '囚'):
            self._add_kege('魄化', _ref('魄化', '死囚带白虎', '通解 p5144'))

        # 13. 繁华/荣华（p3762/5136：贵旺禄马发）
        if (set(tj) & {'贵人'}) and GAN_LU.get(ri_gan) in (chu, zhong, mo) and \
                YI_MA.get(ri_zhi) in (chu, zhong, mo):
            self._add_kege('繁华', _ref('繁华', '贵人乘旺、禄马发于三传', '通解 p3762/5136'))

        # 14. 三阴（p5145：贵逆日辰后 + 死囚玄虎）
        if chu_tj == '白虎' and self._wang_xiang(chu, yue_ling_wx) in ('死', '囚') and \
                ('玄武' in tj):
            self._add_kege('三阴', _ref('三阴', '死囚带玄虎（贵逆）', '通解 p5145'))

        # 15. 孤辰（p4017/5136：季→孤辰；三传见孤辰）
        season = self._season_from_yuejian(yue_jian)
        gc = SEASON_GU_CHEN.get(season, '')
        if gc and gc in (chu, zhong, mo):
            self._add_kege('孤辰', _ref('孤辰', '季前孤辰入传', '通解 p4017/5136'))

        # 16. 死奇（p5146：月躔天罡(辰)用）
        if yue_jian == '辰' and chu == '辰':
            self._add_kege('死奇', _ref('死奇', '月建在辰(天罡)且天罡发用', '通解 p5146'))

        # 17. 二烦 —— 完整判定已迁移至 liuren_64ke_judge.judge_er_fan（四仲月将+四正日+日月宿加四仲+斗罡系丑未），
        # 此处残缺近似版（仅"月将加四仲"1/4条件）已停用，避免残缺二烦混入课格列表（2026-08-15 憨爷指正）。

        # 18. 灾厄（p5146：游魂用——月将后一辰为游魂）
        you_hun = DIZHI[(DIZHI.index(yue_jian) - 1) % 12] if yue_jian in DIZHI else ''
        if chu == you_hun:
            self._add_kege('灾厄', _ref('灾厄', '游魂发用（月将后一辰）', '通解 p5146'))

        # 19. 时泰（p7314：月建(月将proxy)发用 + 青龙/六合 + 财德）
        ke_wx = WU_XING_KE.get(rg_wx, '')  # 我克之五行
        cai_zhi = [z for z in DIZHI if DIZHI_WU_XING.get(z) == ke_wx]  # 财支
        ri_de = GAN_DE.get(ri_gan, '')
        if chu == yue_jian and chu_tj in ('青龙', '六合') and \
                (chu in cai_zhi or chu == ri_de):
            self._add_kege('时泰', _ref('时泰', '月建发用乘青龙六合带财德', '通解 p7314'))

    def _season_from_yuejian(self, yue_jian: str) -> str:
        """月将(月令proxy)→ 季"""
        if yue_jian in ('寅', '卯', '辰'):
            return '春'
        if yue_jian in ('巳', '午', '未'):
            return '夏'
        if yue_jian in ('申', '酉', '戌'):
            return '秋'
        if yue_jian in ('亥', '子', '丑'):
            return '冬'
        return ''

    # -------------------------------------------------------------------------
    # 9. 三传分类
    # -------------------------------------------------------------------------

    def _classify_sanchuan(self, sanchuan_list: List[str]) -> Dict:
        """三传综合分类"""
        chu, zhong, mo = sanchuan_list[0], sanchuan_list[1], sanchuan_list[2]

        classification = {
            '三传': f'{chu}·{zhong}·{mo}',
            '阴阳分布': {
                '初传': DIZHI_YIN_YANG.get(chu, '?'),
                '中传': DIZHI_YIN_YANG.get(zhong, '?'),
                '末传': DIZHI_YIN_YANG.get(mo, '?'),
            },
            '五行分布': {
                '初传': DIZHI_WU_XING.get(chu, '?'),
                '中传': DIZHI_WU_XING.get(zhong, '?'),
                '末传': DIZHI_WU_XING.get(mo, '?'),
            },
            '四孟四仲四季': {
                '初传': self._get_meng_zhong_ji(chu),
                '中传': self._get_meng_zhong_ji(zhong),
                '末传': self._get_meng_zhong_ji(mo),
            },
            '整体五行': self._get_overall_wuxing(sanchuan_list),
        }

        # 三传走势
        chu_idx = DIZHI.index(chu)
        zhong_idx = DIZHI.index(zhong)
        mo_idx = DIZHI.index(mo)

        d1 = (zhong_idx - chu_idx) % 12
        d2 = (mo_idx - zhong_idx) % 12

        if d1 == 1 and d2 == 1:
            classification['三传走势'] = '连茹进传'
        elif d1 == 11 and d2 == 11:
            classification['三传走势'] = '连茹退传'
        elif d1 == 2 and d2 == 2:
            classification['三传走势'] = '间传进传'
        elif d1 == 10 and d2 == 10:
            classification['三传走势'] = '间传退传'
        elif d1 == 0 and d2 == 0:
            classification['三传走势'] = '伏吟停滞'
        else:
            classification['三传走势'] = '杂传'

        return classification

    def _get_meng_zhong_ji(self, zhi: str) -> str:
        if zhi in DIZHI_MENG: return '孟'
        if zhi in DIZHI_ZHONG: return '仲'
        if zhi in DIZHI_JI: return '季'
        return '?'

    def _get_overall_wuxing(self, sanchuan_list: List[str]) -> Dict:
        wuxing_list = [DIZHI_WU_XING.get(z, '?') for z in sanchuan_list]
        wuxing_set = set(wuxing_list)
        result = {
            '五行分布': wuxing_list,
            '五行种类': list(wuxing_set),
        }
        if len(wuxing_set) == 1:
            result['特征'] = f'三传同一五行({wuxing_list[0]})，一气纯清'
        elif len(wuxing_set) == 2:
            result['特征'] = f'三传两种五行，{wuxing_set}相杂'
        else:
            result['特征'] = f'三传三种五行，{wuxing_set}并见'
        return result

    # -------------------------------------------------------------------------
    # 10. 股市信号生成
    # -------------------------------------------------------------------------

    def _generate_stock_signals(self, ri_gan: str = '', ri_zhi: str = '') -> Dict:
        """综合所有检测到的课格，生成总体的股市涨跌信号"""
        signals = {
            '综合倾向': '平',
            '信号强度': 0.0,
            '课格信号': [],
            '操作建议': '',
        }

        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0

        for kege_name, detail in self.kege_details.items():
            stock_signal = detail.get('股市信号', {})
            if not stock_signal:
                continue

            tendency = stock_signal.get('倾向', '平')
            strength = stock_signal.get('信号强度', 0.0)
            interpretation = stock_signal.get('解读', '')
            risk = stock_signal.get('风险提示', '')
            advice = stock_signal.get('建议', '')

            signals['课格信号'].append({
                '课格': kege_name,
                '倾向': tendency,
                '强度': strength,
                '解读': interpretation,
                '风险': risk,
            })

            total_weight += strength

            if tendency in ('涨', '震荡偏涨'):
                bullish_score += strength
            elif tendency in ('跌', '震荡偏跌'):
                bearish_score += strength
            elif '跌' in tendency and '涨' in tendency:
                bullish_score += strength * 0.4
                bearish_score += strength * 0.6

        if total_weight > 0:
            net = (bullish_score - bearish_score) / total_weight
            signals['信号强度'] = abs(net)

            if net > 0.4:
                signals['综合倾向'] = '涨'
                signals['操作建议'] = '三传课格偏多，可积极看涨。注意末传是否有空亡或凶将。'
            elif net > 0.15:
                signals['综合倾向'] = '震荡偏涨'
                signals['操作建议'] = '三传课格略偏多，可谨慎看涨，控制仓位。'
            elif net > -0.15:
                signals['综合倾向'] = '震荡'
                signals['操作建议'] = '三传课格多空均衡，宜观望等待方向明确。'
            elif net > -0.4:
                signals['综合倾向'] = '震荡偏跌'
                signals['操作建议'] = '三传课格略偏空，宜减仓或观望。'
            else:
                signals['综合倾向'] = '跌'
                signals['操作建议'] = '三传课格偏空，宜空仓或做空。关注是否有反转信号。'
        else:
            signals['综合倾向'] = '平'
            signals['操作建议'] = '三传课格信号不明确，需结合其他维度综合判断。'

        # 三合局特殊效应
        if '全局课' in self.detected_kege:
            signals['三合局效应'] = '三传成局，事物被"合住"。涨则延续（趋势延续），跌则被锁（难以突破）。需等冲日（与日干相冲之日）才能破局。'

        return signals

    def get_sanhe_stock_signal(self, kege_name: str) -> Dict:
        """获取三合局股市信号（外部接口兼容）"""
        return self._get_sanhe_stock_signal(kege_name)


# ============================================================================
# 便捷工具函数
# ============================================================================

def detect_sanchuan_kege(sanchuan_list: List[str],
                         ri_gan: str = '', ri_zhi: str = '',
                         keti_raw: str = '',
                         kongwang: Optional[List[str]] = None,
                         season: str = '') -> Dict:
    """快速检测三传课格

    Args:
        sanchuan_list: 三传列表，如 ['申', '子', '辰']
        ri_gan: 日干
        ri_zhi: 日支
        keti_raw: 已有课体名称
        kongwang: 空亡地支列表
        season: 季节（春/夏/秋/冬）

    Returns:
        检测结果字典
    """
    detector = SanChuanKegeDetector()
    return detector.detect(sanchuan_list, ri_gan, ri_zhi, keti_raw, kongwang, season)


def get_sanchuan_kege_summary(result: Dict) -> str:
    """获取三传课格摘要文本（用于前端展示）"""
    if not result or not result.get('课格列表'):
        return '无特殊三传课格'

    kege_list = result['课格列表']
    summary_parts = []

    # 课格列表
    summary_parts.append(f"三传课格: {'、'.join(kege_list)}")

    # 三传走势
    classification = result.get('三传分类', {})
    if classification.get('三传走势'):
        summary_parts.append(f"走势: {classification['三传走势']}")

    # 股市信号
    signals = result.get('股市信号', {})
    if signals.get('综合倾向') and signals['综合倾向'] != '平':
        summary_parts.append(f"涨跌信号: {signals['综合倾向']} (强度{signals.get('信号强度', 0):.2f})")

    return ' | '.join(summary_parts)


# ============================================================================
# 测试
# ============================================================================

if __name__ == '__main__':
    test_cases = [
        # 三合局
        {'sanchuan': ['申', '子', '辰'], 'desc': '申子辰→水局润下课（全局课）'},
        {'sanchuan': ['寅', '午', '戌'], 'desc': '寅午戌→火局炎上课（全局课）'},
        {'sanchuan': ['亥', '卯', '未'], 'desc': '亥卯未→木局曲直课（全局课）'},
        {'sanchuan': ['巳', '酉', '丑'], 'desc': '巳酉丑→金局从革课（全局课）'},
        # 三合局细化
        {'sanchuan': ['子', '辰', '申'], 'desc': '子辰申→润下课+出奇'},
        {'sanchuan': ['辰', '申', '子'], 'desc': '辰申子→润下课+呈斗'},
        {'sanchuan': ['午', '戌', '寅'], 'desc': '午戌寅→炎上课+间魁'},
        {'sanchuan': ['酉', '丑', '巳'], 'desc': '酉丑巳→从革课+献刃'},
        # 顺三间（间传）
        {'sanchuan': ['辰', '午', '申'], 'desc': '辰午申→登三天'},
        {'sanchuan': ['丑', '卯', '巳'], 'desc': '丑卯巳→出户'},
        {'sanchuan': ['子', '寅', '辰'], 'desc': '子寅辰→向三阳'},
        {'sanchuan': ['申', '戌', '子'], 'desc': '申戌子→涉三渊（陈公献定义）'},
        {'sanchuan': ['亥', '丑', '卯'], 'desc': '亥丑卯→溟蒙'},
        {'sanchuan': ['卯', '巳', '未'], 'desc': '卯巳未→迎阳'},
        # 逆三间
        {'sanchuan': ['午', '辰', '寅'], 'desc': '午辰寅→顾祖'},
        {'sanchuan': ['寅', '子', '戌'], 'desc': '寅子戌→冥阳'},
        # 顺连茹
        {'sanchuan': ['辰', '巳', '午'], 'desc': '辰巳午→升阶'},
        {'sanchuan': ['子', '丑', '寅'], 'desc': '子丑寅→含春'},
        {'sanchuan': ['寅', '卯', '辰'], 'desc': '寅卯辰→正和'},
        {'sanchuan': ['巳', '午', '未'], 'desc': '巳午未→近阳'},
        # 逆连茹
        {'sanchuan': ['丑', '子', '亥'], 'desc': '丑子亥→入墓（常见涉三渊）'},
        {'sanchuan': ['亥', '戌', '酉'], 'desc': '亥戌酉→回阴'},
        {'sanchuan': ['卯', '寅', '丑'], 'desc': '卯寅丑→联芳'},
        # 特殊课格
        {'sanchuan': ['巳', '戌', '卯'], 'desc': '巳戌卯→铸印课'},
        {'sanchuan': ['卯', '戌', '巳'], 'desc': '卯戌巳→斫轮课'},
        {'sanchuan': ['午', '卯', '子'], 'desc': '午卯子→高盖乘轩'},
        {'sanchuan': ['寅', '申', '巳'], 'desc': '寅申巳→玄胎课（三传皆孟）'},
        {'sanchuan': ['辰', '戌', '丑'], 'desc': '辰戌丑→三传皆季（参考）'},
    ]

    detector = SanChuanKegeDetector()

    print("=" * 80)
    print("三传课格检测引擎 v2.0 — 测试")
    print("=" * 80)

    passed = 0
    failed = 0

    for case in test_cases:
        result = detector.detect(case['sanchuan'])
        kege_str = '、'.join(result['课格列表'])
        signals = result['股市信号']

        print(f"\n【{case['desc']}】")
        print(f"  三传: {'·'.join(case['sanchuan'])}")
        print(f"  课格: {kege_str}")

        if signals.get('综合倾向'):
            print(f"  信号: {signals['综合倾向']} (强度: {signals.get('信号强度', 0):.2f})")

        # 简单验证
        if result['课格列表']:
            passed += 1
        else:
            failed += 1
            print(f"  ⚠️ 未检测到任何课格！")

    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 个测试用例")
    print(f"{'=' * 80}")
