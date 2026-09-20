"""
干支十神时辰引擎 — 五行关系模块

核心原则：日干/日支对应地支十二时辰。
时辰地支藏干本气与日干/日支的五行生克关系 = 十神。
不走五鼠遁天道，纯地支五行关系。

用法：
    from engine.ganzhi_shishen import get_shichen_for_category

    # 获取指定 category 在今日对应的正确时辰
    shi_chen = get_shichen_for_category('ri_gan_pian_cai', ri_gan='甲', ri_zhi='辰')
    # → '辰'（甲日偏财=戊土=辰时）
"""

# ── 地支藏干本气 (地支 → (天干, 阴阳)) ──
DI_ZHI_CANG_GAN = {
    '子': ('癸', '阴'),  # 癸水
    '丑': ('己', '阴'),  # 己土
    '寅': ('甲', '阳'),  # 甲木
    '卯': ('乙', '阴'),  # 乙木
    '辰': ('戊', '阳'),  # 戊土
    '巳': ('丙', '阳'),  # 丙火
    '午': ('丁', '阴'),  # 丁火
    '未': ('己', '阴'),  # 己土
    '申': ('庚', '阳'),  # 庚金
    '酉': ('辛', '阴'),  # 辛金
    '戌': ('戊', '阳'),  # 戊土
    '亥': ('壬', '阳'),  # 壬水
}

# ── 地支五行 ──
DI_ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}

# ── 十天干五行 ──
TIAN_GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}

# ── 十天干阴阳 ──
TIAN_GAN_YINYANG = {
    '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳',
    '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴',
}

# ── 十二地支 ──
ALL_DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# ── 五行生克 ──
WUXING_SK = {
    '木': {'生': '火', '克': '土', '被生': '水', '被克': '金'},
    '火': {'生': '土', '克': '金', '被生': '木', '被克': '水'},
    '土': {'生': '金', '克': '水', '被生': '火', '被克': '木'},
    '金': {'生': '水', '克': '木', '被生': '土', '被克': '火'},
    '水': {'生': '木', '克': '火', '被生': '金', '被克': '土'},
}


def _get_shishen(my_gan: str, my_yy: str, target_gan: str, target_yy: str) -> str:
    """
    给定「我」和「目标」的天干+阴阳，返回十神名称。
    
    参数:
        my_gan: 我的天干（如'甲'）
        my_yy: 我的阴阳（'阳'或'阴'）
        target_gan: 目标天干（如'戊'）
        target_yy: 目标阴阳（'阳'或'阴'）
    
    返回: 十神名（'正印','偏印','食神','伤官','正财','偏财','正官','七杀','比肩','劫财'）
    """
    my_wx = TIAN_GAN_WUXING[my_gan]
    target_wx = TIAN_GAN_WUXING[target_gan]
    same_yy = (my_yy == target_yy)  # 同阴阳

    if target_wx == my_wx:
        return '比肩' if same_yy else '劫财'
    
    sk = WUXING_SK[target_wx]
    
    # 目标生我 → 印星
    if sk['生'] == my_wx:
        return '偏印' if same_yy else '正印'
    
    # 我生目标 → 食伤
    if sk['被生'] == my_wx:
        return '食神' if same_yy else '伤官'
    
    # 目标克我 → 官杀
    if sk['克'] == my_wx:
        return '七杀' if same_yy else '正官'
    
    # 我克目标 → 财星
    if sk['被克'] == my_wx:
        return '偏财' if same_yy else '正财'
    
    return '未知'


def get_shishen_for_rigan(ri_gan: str, shi_zhi: str) -> str:
    """
    对于给定的日干和时辰地支，返回时辰对日干的十神名称。
    
    例如: ri_gan='甲', shi_zhi='辰' → 辰藏戊土，甲克戊(阳克阳) → '偏财'
    """
    if shi_zhi not in DI_ZHI_CANG_GAN:
        return '未知'
    target_gan, target_yy = DI_ZHI_CANG_GAN[shi_zhi]
    my_yy = TIAN_GAN_YINYANG.get(ri_gan, '阳')
    return _get_shishen(ri_gan, my_yy, target_gan, target_yy)


def get_shishen_for_rizhi(ri_zhi: str, shi_zhi: str) -> str:
    """
    对于给定的日支和时辰地支，返回时辰对日支的十神名称。
    
    例如: ri_zhi='辰'(戊土阳), shi_zhi='亥'(壬水阳) → 戊克壬(阳克阳) → '偏财'
    """
    if ri_zhi not in DI_ZHI_CANG_GAN or shi_zhi not in DI_ZHI_CANG_GAN:
        return '未知'
    my_gan, my_yy = DI_ZHI_CANG_GAN[ri_zhi]
    target_gan, target_yy = DI_ZHI_CANG_GAN[shi_zhi]
    return _get_shishen(my_gan, my_yy, target_gan, target_yy)


def find_shichen_for_rigan(ri_gan: str, target_shishen: str) -> list:
    """
    找到所有使「时辰→日干十神」等于 target_shishen 的时辰地支。
    
    返回: 时辰地支列表（按地支顺序）
    """
    results = []
    for dz in ALL_DI_ZHI:
        ss = get_shishen_for_rigan(ri_gan, dz)
        if ss == target_shishen:
            results.append(dz)
    return results


def find_shichen_for_rizhi(ri_zhi: str, target_shishen: str) -> list:
    """
    找到所有使「时辰→日支十神」等于 target_shishen 的时辰地支。
    
    返回: 时辰地支列表（按地支顺序）
    """
    results = []
    for dz in ALL_DI_ZHI:
        ss = get_shishen_for_rizhi(ri_zhi, dz)
        if ss == target_shishen:
            results.append(dz)
    return results


# ── category → (主体, 十神) 映射 ──
CATEGORY_MAP = {
    'ri_gan_pian_cai':   ('ri_gan', '偏财'),
    'ri_zhi_pian_cai':   ('ri_zhi', '偏财'),
    'ri_gan_shi_shen':   ('ri_gan', '食神'),
    'ri_zhi_shi_shen':   ('ri_zhi', '食神'),
    'ri_gan_zheng_yin':  ('ri_gan', '正印'),
    'ri_gan_pian_yin':   ('ri_gan', '偏印'),
    'ri_zhi_zheng_yin':  ('ri_zhi', '正印'),
    'ri_zhi_pian_yin':   ('ri_zhi', '偏印'),
}


def get_shichen_for_category(category: str, ri_gan: str = '', ri_zhi: str = '',
                              default_shi_chen: str = '巳') -> str:
    """
    根据预测类别，返回正确的时辰地支。
    
    参数:
        category: 预测类别（如 'ri_gan_pian_cai'）
        ri_gan: 日干
        ri_zhi: 日支
        default_shi_chen: 未匹配时的后备时辰（固定时辰/随机课/未知类别使用）
    
    返回: 时辰地支字符串
    """
    if category in ('fixed_time', 'random', 'manual'):
        return default_shi_chen
    
    if category not in CATEGORY_MAP:
        return default_shi_chen
    
    subject, shishen = CATEGORY_MAP[category]
    
    if not ri_gan or not ri_zhi:
        return default_shi_chen
    
    if subject == 'ri_gan':
        candidates = find_shichen_for_rigan(ri_gan, shishen)
    else:
        candidates = find_shichen_for_rizhi(ri_zhi, shishen)
    
    if candidates:
        # 如果只有一个候选，直接用；如果有多个，按时辰顺序取第一个
        # 优先取上午交易时段(9-15点之间)的时辰：巳(9-11)、午(11-13)、未(13-15)
        for preferred in ['巳', '午', '未', '辰', '申']:
            if preferred in candidates:
                return preferred
        return candidates[0]
    
    return default_shi_chen


def print_shichen_table(ri_gan: str, ri_zhi: str):
    """打印一张完整的十神时辰对照表（调试用）"""
    print(f"\n{'='*70}")
    print(f"  日干{ri_gan} / 日支{ri_zhi} — 十二时辰十神对照表")
    print(f"{'='*70}")
    print(f"{'时辰':<6} {'藏干':<6} {'对日干十神':<10} {'对日支十神':<10}")
    print(f"{'-'*40}")
    for dz in ALL_DI_ZHI:
        cg, yy = DI_ZHI_CANG_GAN[dz]
        ss_gan = get_shishen_for_rigan(ri_gan, dz)
        ss_zhi = get_shishen_for_rizhi(ri_zhi, dz)
        print(f"  {dz:<4} {cg}({yy})   {ss_gan:<10} {ss_zhi:<10}")
    print(f"{'='*70}")


# ── 快速自测 ──
if __name__ == '__main__':
    # 测试 2026-07-29 甲辰日
    print_shichen_table('甲', '辰')
    
    print("\n# 类别→时辰映射:")
    for cat, (sub, ss) in CATEGORY_MAP.items():
        sc = get_shichen_for_category(cat, ri_gan='甲', ri_zhi='辰')
        print(f"  {cat}({ss}) → {sc}时")
    
    # fixed_time 和 random 使用当前时辰
    print(f"  fixed_time → {get_shichen_for_category('fixed_time', '甲', '辰', '巳')}时")
    print(f"  random → {get_shichen_for_category('random', '甲', '辰', '巳')}时")
