#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬股市预测评分配置表（单一数据源）

所有课体/六亲/旺衰/空亡/铸印/天将/十二长生的评分规则集中于此。
引擎 liuren_20d_engine.py 从本文件读取评分，不再硬编码。

更新方式：
1. 人工审核修正后，更新本文件对应字段的 score 值
2. 训练库迭代时，根据验证结果调整评分权重
3. 引擎代码无需修改，自动读取新评分
"""

# ============================================================================
# 1. 课体等级评分（基于 liuren_64ke_v2.py 的吉凶等级）
# ============================================================================
KETI_LEVEL_SCORE = {
    '上吉': 5,
    '大吉': 4,
    '中吉': 3,
    '小吉': 2,
    '吉':  1,
    '平':  0,
    '凶':  -2,
    '小凶': -3,
    '中凶': -4,
    '大凶': -6,
}

# 64课经大凶课额外扣分
DAXIONG_EXTRA_DEDUCTION = -3


# ============================================================================
# 2. 六亲评分（三传六亲对涨跌的影响）
# ============================================================================
LIUQIN_SCORE = {
    '妻财': 2,    # 资金流入，利好
    '官鬼': 1,    # 主力动作，偏多
    '父母': 0,    # 政策面，中性
    '子孙': -1,   # 散户跟风，偏空
    '兄弟': -2,   # 资金分流，利空
}


# ============================================================================
# 3. 旺衰评分（三传地支旺衰对涨跌的影响）
# ============================================================================
WANGSHUAI_SCORE = {
    '旺':  1,
    '相':  1,
    '休':  0,
    '囚': -1,
    '死': -1,
}


# ============================================================================
# 4. 空亡评分
# ============================================================================
KONGWANG_SCORE = {
    '末传落空': -2,   # 末传空亡，结果落空
    '中传落空': -1,   # 中传空亡，过程受阻
    '初传落空': 0,    # 初传空亡，起步受影响但不致命
}


# ============================================================================
# 5. 铸印课格评分（从 liuren_64ke_knowledge.py 股市判断衍生）
# ============================================================================
ZHUYIN_SCORE = {
    '铸印破模': -5,   # 巳为铸模逢空亡，印破不成，主下跌
    '铸印破印': -5,   # 戌为印逢空亡，印破不成，主下跌
    '铸印破模_初空': -4,  # 巳为铸模逢空亡（初传），主下跌
    '正常铸印': 3,    # 铸造成型，主上涨
}


# ============================================================================
# 6. 天将评分（三传天将吉凶）
# ============================================================================
# 三传天将组合的特殊评分
TIANJIANG_COMBO_SCORE = {
    '后勾玄': {       # 天后+勾陈+玄武 三凶将齐聚
        'score': -4,
        'desc_key': '天将凶(后勾玄)',  # 对应 liuren_64ke_knowledge.py 股市判断的key
    },
}

# 天将凶将数量加权
TIANJIANG_XIONG_COUNT_SCORE = {
    3: -2,   # 三凶将齐聚，额外扣分
    2: -1,   # 两凶将并临
    1: 0,    # 单个凶将影响不大
    0: 0,
}


# ============================================================================
# 7. 十二长生评分（日干五行在三传中的长生位）
# ============================================================================
# 长生位本身的基础评分
CHANGSHENG_SCORE = {
    '长生':  2,    # 生我之力，根基稳固
    '帝旺':  1,    # 旺气充足
    '墓':   -1,    # 停滞入库
    '绝':   -2,    # 气绝断绝
}

# 长生位逢空亡的评分调整（空亡则正负反转或减轻）
CHANGSHENG_KONG_SCORE = {
    '长生空亡': -2,   # 生我之力无力，根基不稳
    '帝旺空亡': -1,   # 旺气不足
    '墓空亡':    1,   # 入库之力减轻
    '绝空亡':    1,   # 绝处逢生
}


# ============================================================================
# 8. 双线验证评分（课格天将线 × 十二长生线）
# ============================================================================
DOUBLE_LINE_SCORE = {
    '双线凶煞': -3,   # 课格天将线凶 + 十二长生线凶，两线共振必大跌
    '双线吉庆':  3,   # 课格天将线吉 + 十二长生线吉，两线共振必大涨
    '一吉一凶':  0,   # 两线方向相反，震荡为主
}


# ============================================================================
# 9. 趋势判定阈值
# ============================================================================
TREND_THRESHOLD = {
    '看涨': 3,     # score >= 3
    '看跌': -3,    # score <= -3
    # 中间为震荡
}


# ============================================================================
# 10. 置信度计算参数
# ============================================================================
CONFIDENCE_CONFIG = {
    # ---- 标定模式（2026-09-20 憨爷拍板改 tanh）----
    # 'linear'（旧）：50 + score*10  ⇒ score>=5 顶格 100、<=-5 压 0。
    #   240 课实测：conf=100 占 30.8%、conf=0 占 45.4%，两端合计 **76.2%**，
    #   score 实际跨度 -23~+27 却只映射出 11 个值 ⇒ 强度信息在两端全丢。
    # 'tanh'（现）：50 + 45*tanh(score/8) ⇒ 值域恒在 (5, 95)，**数学上永不饱和**，
    #   且严格单调 ⇒ 保留强弱排序。特殊课格下限(floor)逻辑不变。
    'mode': 'tanh',
    'base': 50,               # 中位（score=0 时的置信度）
    'half_range': 45,         # 振幅 ⇒ conf ∈ [5, 95]
    'tanh_scale': 8,          # 陡峭度：score=8 → conf≈84；score=3（看涨线）→ 66
    'score_multiplier': 10,   # 仅 mode='linear' 时生效（保留旧参数以便回滚对照）
    'min': 0,
    'max': 100,
    # 特殊课格的置信度下限
    'zhu_yin_po_mo_floor': 75,      # 铸印破模课置信度下限
    'zhu_yin_po_mo_3xiong_floor': 85,  # 铸印破模+三凶将
    'double_line_xiong_floor': 90,      # 双线凶煞置信度下限
}


# ============================================================================
# 11-18. 壬归12维度评分（对应 LiurenAnalysisEngine.analyze() 的12个分析维度）
# ============================================================================

# 11. 四课加临评分（壬归·卷之一·一：四课之间的关系）
SIKE_QI_SCORE = {
    '相生': 1,       # 四课相生，主顺势
    '相克': -1,       # 四课相克，主逆势
    '递生': 2,        # 递相生扶，大吉
    '交克': -2,        # 交相克贼，大凶
    '无关系': 0,
}

# 12. 用神五气评分（壬归·卷之一·二：用神旺衰）
YONGSHEN_WUQI_SCORE = {
    '旺': 2,           # 用神旺相，事可成
    '相': 1,           # 用神相生，事可谋
    '休': 0,           # 用神休囚，事迟滞
    '囚': -1,          # 用神囚死，事难成
    '死': -2,          # 用神死绝，事必败
}

# 13. 三传制救评分（壬归·卷之一·三：初传/中传/末传的制化关系）
SANCHUAN_ZHIJIU_SCORE = {
    '递生': 2,        # 初生中、中生末，递相生扶
    '递克': -2,        # 初克中、中克末，递相克贼
    '制救': 1,         # 有制有救，凶中化吉
    '无制无救': -1,     # 无制无救，凶上加凶
    '无关系': 0,
}

# 14. 贵神吉凶评分（壬归·卷之一·四：天将吉凶）
GUISHEN_JIXIONG_SCORE = {
    '贵人': 2,         # 国家队/权重股
    '青龙': 2,         # 资金流入
    '六合': 1,         # 板块共振
    '太常': 0,         # 常规走势
    '太阴': 1,         # 主力吸筹
    '天后': 0,         # 流动性宽松
    '朱雀': 0,         # 消息驱动
    '腾蛇': -1,        # 洗盘反复
    '勾陈': -1,        # 横盘拖延
    '天空': -2,        # 利好落空
    '白虎': -2,        # 暴跌恐慌
    '玄武': -2,        # 庄家出货
}

# 15. 八杀体系评分（壬归·卷之一·五：八种凶杀）
BA_SHA_SCORE = {
    '死奇': -3,        # 死奇杀，大凶
    '魄化': -3,        # 魄化杀，大凶
    '飞魂': -2,        # 飞魂杀
    '丧吊': -2,        # 丧吊杀
    '天祸': -2,        # 天祸杀
    '天寇': -2,        # 天寇杀
    '孤辰': -1,        # 孤辰杀
    '寡宿': -1,        # 寡宿杀
    '无': 0,
}

# 16. 十二气财星评分（壬归·卷之三：财星十二气）
CAI_SHI_ER_QI_SCORE = {
    '财旺': 2,         # 财星旺相，主涨
    '财相': 1,         # 财星相生
    '财休': 0,         # 财星休囚
    '财囚': -1,        # 财星囚死
    '财死': -2,        # 财星死绝
    '财空': -1,        # 财星空亡
}

# 17. 身强身弱评分（壬归·卷之三：日干强弱）
SHEN_QIANG_RUO_SCORE = {
    '身强': 1,         # 日干强旺，能任财官
    '身弱': -1,        # 日干衰弱，不能任财
    '中和': 0,         # 身命中和
}

# 18. 神煞评分
SHEN_SHA_SCORE = {
    '天乙贵人': 2,     # 最吉之神
    '禄': 1,           # 禄神
    '马': 1,           # 驿马
    '天德': 1,         # 天德贵人
    '月德': 1,         # 月德贵人
    '三奇': 2,         # 三奇贵人
    '华盖': 0,         # 华盖（中性）
    '桃花': 0,         # 桃花（中性）
    '羊刃': -1,        # 羊刃
    '劫煞': -1,        # 劫煞
    '亡神': -1,        # 亡神
    '空亡': -1,        # 空亡
    '无': 0,
}


# ============================================================================
# 12维度权重配置（用于加权合成总分）
# ============================================================================
DIMENSION_WEIGHTS = {
    'keti_level':     0.12,  # 1. 课体等级（基础）
    'liuqin':         0.10,  # 2. 六亲
    'wangshuai':      0.08,  # 3. 旺衰
    'kongwang':       0.08,  # 4. 空亡
    'zhuyin':         0.08,  # 5. 铸印课格
    'tianjiang':      0.10,  # 6. 天将
    'changsheng':     0.08,  # 7. 十二长生
    'sike_qi':        0.05,  # 8. 四课加临
    'yongshen':       0.08,  # 9. 用神五气
    'sanchuan_zhijiu':0.05,  # 10. 三传制救
    'guishen':        0.05,  # 11. 贵神吉凶
    'ba_sha':         0.05,  # 12. 八杀体系
    'cai_shi_er_qi':  0.05,  # 财星十二气（附加）
    'shen_qiang_ruo': 0.03,  # 身强身弱（附加）
}


# ============================================================================
# 便捷函数
# ============================================================================

def get_keti_level_score(level_name):
    """获取课体等级对应的评分"""
    return KETI_LEVEL_SCORE.get(level_name, 0)


def get_liuqin_score(liuqin_name):
    """获取六亲对应的评分"""
    return LIUQIN_SCORE.get(liuqin_name, 0)


def get_wangshuai_score(wangshuai_name):
    """获取旺衰对应的评分"""
    return WANGSHUAI_SCORE.get(wangshuai_name, 0)


def get_kongwang_score(position):
    """获取空亡评分（position: '初传'/'中传'/'末传'）"""
    key_map = {'初传': '初传落空', '中传': '中传落空', '末传': '末传落空'}
    return KONGWANG_SCORE.get(key_map.get(position, ''), 0)


def get_zhuyin_score(zhuyin_type):
    """获取铸印课格评分"""
    return ZHUYIN_SCORE.get(zhuyin_type, 0)


def get_tianjiang_combo_score(combo_name):
    """获取天将组合评分"""
    return TIANJIANG_COMBO_SCORE.get(combo_name, {}).get('score', 0)


def get_tianjiang_xiong_count_score(count):
    """获取天将凶将数量的额外扣分"""
    return TIANJIANG_XIONG_COUNT_SCORE.get(count, 0)


def get_changsheng_score(changsheng_name):
    """获取十二长生位评分"""
    return CHANGSHENG_SCORE.get(changsheng_name, 0)


def get_changsheng_kong_score(changsheng_name):
    """获取十二长生位逢空亡的评分调整"""
    key = f'{changsheng_name}空亡'
    return CHANGSHENG_KONG_SCORE.get(key, 0)


def get_double_line_score(line_type):
    """获取双线验证评分"""
    return DOUBLE_LINE_SCORE.get(line_type, 0)


def get_sike_qi_score(relationship):
    """获取四课加临评分"""
    return SIKE_QI_SCORE.get(relationship, 0)


def get_yongshen_wuqi_score(wangshuai):
    """获取用神五气评分"""
    return YONGSHEN_WUQI_SCORE.get(wangshuai, 0)


def get_sanchuan_zhijiu_score(relationship):
    """获取三传制救评分"""
    return SANCHUAN_ZHIJIU_SCORE.get(relationship, 0)


def get_guishen_score(guishen_name):
    """获取贵神（天将）吉凶评分"""
    return GUISHEN_JIXIONG_SCORE.get(guishen_name, 0)


def get_ba_sha_score(sha_name):
    """获取八杀评分"""
    return BA_SHA_SCORE.get(sha_name, 0)


def get_cai_shi_er_qi_score(cai_status):
    """获取财星十二气评分"""
    return CAI_SHI_ER_QI_SCORE.get(cai_status, 0)


def get_shen_qiang_ruo_score(status):
    """获取身强身弱评分"""
    return SHEN_QIANG_RUO_SCORE.get(status, 0)


def get_shen_sha_score(shen_sha_name):
    """获取神煞评分"""
    return SHEN_SHA_SCORE.get(shen_sha_name, 0)


def calculate_confidence(trend_score, special_flags=None):
    """
    计算置信度
    
    Args:
        trend_score: 趋势评分
        special_flags: dict，特殊课格标记，如：
            {'zhu_yin_po_mo': True, 'tianjiang_3xiong': True, 'double_line_xiong': True}
    
    Returns:
        float: 置信度（0-100）
    """
    import math
    _cfg = CONFIDENCE_CONFIG
    if _cfg.get('mode') == 'tanh':
        # 2026-09-20 憨爷拍板：线性标定两端饱和（76.2% 压在 0/100），改 tanh 压缩。
        # 严格单调 ⇒ 强弱排序保留；值域 (base-half_range, base+half_range) 永不触顶。
        conf = _cfg['base'] + _cfg['half_range'] * math.tanh(
            float(trend_score) / float(_cfg['tanh_scale']))
    else:
        conf = _cfg['base'] + trend_score * _cfg['score_multiplier']
    conf = max(_cfg['min'], min(_cfg['max'], conf))
    
    if special_flags:
        if special_flags.get('zhu_yin_po_mo') and special_flags.get('tianjiang_3xiong'):
            conf = max(conf, CONFIDENCE_CONFIG['zhu_yin_po_mo_3xiong_floor'])
        elif special_flags.get('zhu_yin_po_mo'):
            conf = max(conf, CONFIDENCE_CONFIG['zhu_yin_po_mo_floor'])
        
        if special_flags.get('double_line_xiong'):
            conf = max(conf, CONFIDENCE_CONFIG['double_line_xiong_floor'])
    
    return round(conf, 1)


def get_trend_prediction(trend_score):
    """
    根据评分判定趋势
    
    Returns:
        str: '看涨' / '看跌' / '震荡'
    """
    if trend_score >= TREND_THRESHOLD['看涨']:
        return '看涨'
    elif trend_score <= TREND_THRESHOLD['看跌']:
        return '看跌'
    else:
        return '震荡'
