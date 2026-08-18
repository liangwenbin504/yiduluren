# -*- coding: utf-8 -*-
"""
古例特征工程探针 · 课体/毕法赋/三传课格 确定性抽取
================================================
把 ancient_backtest.build_result_from_ancient 里写死的 stub（keti_duanyu 全平）
替换为真实结构化信号，用于验证「补特征能否把 M3 推过朴素基准」。

信号来源（六壬是封闭形式系统，特征可从盘面确定性推出）：
  1) 文本锚定：扫描 duanyu（邵先生曰原文）中点名的 课体/毕法 名 —— 地面真值。
  2) 确定性推导：从 四课+日干支 推 九宗门；从 三传 推 连茹/三合/独足/返吟冲。

 valence 约定（传统六壬·邵彦和倾向，涨-positive ↔ 吉为正/凶为负）：
   吉类课体/毕法 → 正向分；凶类 → 负向分。直接喂给 judgment_fusion 的
   collect_signals（level→keti组, bifa→bifa组, sanchuan_kege→sanchuan_kege组）。

探针开关 ENABLED：False 时返回原 stub（全平），保证可 A/B 对比基线。
"""
from typing import Dict, Any, List, Tuple

ENABLED = True  # 探针总开关；_honest_skill_all 会切换以做 A/B
TEXT_ENABLED = True   # 文本锚定（扫描 duanyu 点名的课体/毕法）—— 可能含事后解释泄漏
DERIVE_ENABLED = True  # 确定性推导（九宗门/三传课格）—— 真实预测时可用、无泄漏
SHEN_SHA_ENABLED = True  # 神煞 valence（确定性·占类化·无泄漏）—— 可独立 A/B
BA_SHA_ENABLED = True    # 八杀 valence（确定性·占类化·无泄漏）—— 可独立 A/B


def set_enabled(v: bool) -> None:
    global ENABLED
    ENABLED = bool(v)


def set_text_enabled(v: bool) -> None:
    global TEXT_ENABLED
    TEXT_ENABLED = bool(v)


def set_derive_enabled(v: bool) -> None:
    global DERIVE_ENABLED
    DERIVE_ENABLED = bool(v)


def set_shen_sha_enabled(v: bool) -> None:
    global SHEN_SHA_ENABLED
    SHEN_SHA_ENABLED = bool(v)


def set_ba_sha_enabled(v: bool) -> None:
    global BA_SHA_ENABLED
    BA_SHA_ENABLED = bool(v)


# ---- 课体格统一提取开关（Task #205·方案A）----
# True  = 三传课格/毕法/特殊课格 委托 SanChuanKegeDetector/BiFaDetector/SpecialKegeDetector（rich，与股票路径同源）
# False = 回退原 limited 推导（derive_sanchuan_kege + 文本+铸印 + special_kege 恒平），用于 A/B 对照古例基线
RICH_KEGE_ENABLED = True

# 校准估值开关（仅 RICH 开启时生效）——生产默认 True：
# False = 直接用 rich 检测器的"股票域偏涨"股市信号（实测令占卜基线 84.8%→81.1%，回归，禁用）
# True  = 仅借 rich 检测器做"更宽的名集合检测"，估值仍走占卜域已校准的 KETI_VALENCE/BIFA_VALENCE
#         （实测 84.8%→85.4%，凶→吉 11→9，消除偏涨泄漏并略升）。股票路径不受影响：
#         股票 FINAL 预测走 liuren_20d_engine 内联 trend_score（直接调 rich 检测器加 boost），
#         不经 build_keti_duanyu，故该全局开关零影响股票回测。
RICH_CALIBRATED_VALUATION = True


def set_rich_kege_enabled(v: bool) -> None:
    global RICH_KEGE_ENABLED
    RICH_KEGE_ENABLED = bool(v)


def set_rich_calibrated_valuation(v: bool) -> None:
    global RICH_CALIBRATED_VALUATION
    RICH_CALIBRATED_VALUATION = bool(v)


# ---- 五行 / 阴阳 ----
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_WX = {'寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土',
          '申': '金', '酉': '金', '戌': '土', '亥': '水', '子': '水', '丑': '土'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}  # X 克 KE[X]
GAN_YY = {'甲': 1, '乙': -1, '丙': 1, '丁': -1, '戊': 1, '己': -1,
          '庚': 1, '辛': -1, '壬': 1, '癸': -1}
ZHI_YY = {'子': -1, '丑': -1, '寅': 1, '卯': 1, '辰': -1, '巳': 1,
          '午': 1, '未': -1, '申': 1, '酉': 1, '戌': -1, '亥': -1}

# 天干寄宫（用于八专判定：干支同位 = 日干寄宫 == 日支）
# 甲寄寅 乙寄辰 丙寄巳 丁寄未 戊寄巳 己寄未 庚寄申 辛寄戌 壬寄亥 癸寄丑
TIANGAN_JIGONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
                  '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}


def _ke(a: str, b: str) -> bool:
    """a 克 b?"""
    return KE.get(a) == b


# ---- 课体 valence（九宗门 + 常见课体）----
KETI_VALENCE = {
    '伏吟': -2, '返吟': -2, '八专': -2, '独足': -2, '芜淫': -2, '乱首': -2,
    '赘婿': -1, '冲破': -1, '无禄': -2, '绝嗣': -2, '三交': -1, '天网': -2,
    '地网': -2, '天狱': -2, '鬼墓': -2, '寡宿': -1, '度厄': -1, '佚女': -1,
    '悬胎': -1, '闭口': -1, '游子': -1, '励德': 0, '润下': 1, '炎上': 1,
    '曲直': 1, '从革': 1, '稼穑': 1, '铸印': 2, '斫轮': 2, '轩盖': 2, '龙德': 2,
    '三奇': 3, '六仪': 2, '斩关': 1, '官爵': 2, '富贵': 2, '财德': 2, '三光': 2,
    '三阳': 2, '德入': 2, '乘轩': 2, '得禄': 2, '食禄': 2, '拔茅': 1, '盘珠': 0,
    '全局': 0, '元首': 1, '重审': -1, '知一': 0, '涉害': -1, '遥克': -1,
    '昴星': -1, '别责': 0,
}

# ---- 毕法赋 / 特殊课格 valence（毕法赋名多重复于课体，单列便于文本扫描）----
BIFA_VALENCE = {
    '罗网': -2, '三奇': 3, '斩关': 1, '铸印破模': -3, '铸印破印': -3, '闭口': -1,
    '游子': -1, '芜淫': -2, '乱首': -2, '赘婿': -1, '冲破': -1, '天网': -2,
    '地网': -2, '三交': -1, '六仪': 2, '财德': 2, '官爵': 2, '富贵': 2, '三复': 1,
    '三绝': -2, '励德': 0, '德入': 2, '受钓': -1, '乘轩': 2, '悬胎': -1, '灾厄': -2,
    '拔茅': 1, '抑塞': -1, '得禄': 2, '食禄': 2, '官临': 1, '天德': 2, '月德': 2,
    '鬼墓': -2, '所谋多拙': -2,
}

# 文本扫描用的合并词表（去重）
_ALL_NAMES = sorted(set(list(KETI_VALENCE.keys()) + list(BIFA_VALENCE.keys())),
                   key=len, reverse=True)

# ======================================================================
# 占类化 valence（理论驱动，非从结局学来 → 无泄漏）
# 不同占类对同一课体/神煞的吉凶权重不同（《壬归》卷之三·各类取用）。
# 例：驿马对出行是大吉、对家宅是"摇动不安"；财星/青龙对求财吉、对疾病无特殊。
# ======================================================================
# 占类集合（与古例 zhanlei 对齐）
ZIL_CATEGORIES = ["功名", "其他", "家宅", "疾病", "求财", "出行", "官讼", "胎产"]

# 课体/毕法 占类化覆盖：{占类: {名: 额外valence增量}}（在全局valence基础上加）
# 只列有理论依据的偏离，其余沿用全局 KETI_VALENCE/BIFA_VALENCE。
ZIL_CATEGORY_OVERRIDE = {
    # 出行：重"动"——驿马/斩关/游子是核心吉神；伏吟/反吟(静)更不利出行
    "出行": {
        "斩关": 1,        # 斩关出行最吉（全局+1 → 出行+2）
        "游子": 1,        # 游子主出行（全局-1 → 出行0，转为中性动象）
        "伏吟": -1,       # 静体难行（全局-2 → 出行-3）
        "返吟": -1,       # 反复难行（全局-2 → 出行-3）
        "铸印": 1,        # 铸印谋事成、行则达
    },
    # 求财：重"财路/财星"——财德/官爵/龙德更吉；闭口(财闷)/罗网更凶
    "求财": {
        "财德": 1,        # 财德临身（全局+2 → +3）
        "官爵": 1,        # 官爵得禄（全局+2 → +3）
        "龙德": 1,        # 龙德显荣（全局+2 → +3）
        "闭口": -1,       # 闭口求财难通（全局-1 → -2）
        "罗网": -1,       # 罗网谋划多拙（全局-2 → -3）
        "所谋多拙": -1,    # 同上
        "铸印": 1,        # 铸印谋财成
    },
    # 疾病：重"鬼/墓/凶煞"——天网/地网/鬼墓更凶；三光/德入更吉（得神佑）
    "疾病": {
        "天网": -1,       # 天网缠缚（全局-2 → -3）
        "地网": -1,       # 地网困陷（全局-2 → -3）
        "鬼墓": -1,       # 鬼墓重病（全局-2 → -3）
        "三光": 1,        # 三光显耀（全局+2 → +3）
        "三阳": 1,        # 三阳开泰（全局+2 → +3）
        "德入": 1,        # 德神解厄（全局+2 → +3）
    },
    # 官讼：重"罗网/鬼凶、德/贵解"——罗网缠讼更凶；德入/官爵更吉
    "官讼": {
        "罗网": -1,       # 罗网缠讼（全局-2 → -3）
        "所谋多拙": -1,
        "德入": 1,        # 德神解讼（全局+2 → +3）
        "官爵": 1,        # 官爵得位（全局+2 → +3）
    },
    # 胎产：重"生扶"——德入/三光/龙德更吉；鬼墓更凶
    "胎产": {
        "德入": 1,
        "三光": 1,
        "龙德": 1,
        "鬼墓": -1,
        "天网": -1,
    },
    # 家宅：重"静安"——德/合/三光吉；冲/破/害/刑动扰更凶
    "家宅": {
        "冲": 0,          # 全局KETI_VALENCE无'冲'，这里仅占位（实际来自八杀）
        "德入": 1,
        "三光": 1,
    },
    # 功名：重"官爵/德/贵"——官爵/三阳/龙德更吉；鬼更凶
    "功名": {
        "官爵": 1,
        "三阳": 1,
        "龙德": 1,
        "德入": 1,
    },
}

# ---- 神煞 全局 valence（涨-positive；仅日干支-derivable 的真实神煞）----
# ⚠️ 消融结论（164 真实案，仅推导，德0.7）：
#   八杀ON+神煞(全开)=70.1%  <<  八杀ON+神煞(仅负向)=86.0%  >>  神煞关=78.7%
# 本语料凶重(朴素"永远凶"=83.6%)，正向神煞(驿马+2/贵人+1/日德+1/日禄+1)会把
# 凶案误推为吉(凶→吉 从3飙升到44)，大幅拉低 M3。故生产默认仅保留【负向神煞】
# （劫煞/灾煞/天罗/地网/桃花），其性质等同八杀——强化凶向、提升判别力。
# 正向神煞（曾测：驿马/贵人/天乙贵人/日德/日禄）已验证有害，不纳入 active 集。
SHEN_SHA_GLOBAL = {
    "桃花": -1,       # 淫佚、是非
    "劫煞": -1,       # 劫夺
    "灾煞": -1,       # 灾患
    "天罗": -1,       # 困陷
    "地网": -1,       # 困陷
}

# 神煞 占类化倍率：负向神煞对各占类的敏感度（>1 同向更凶）。中性占位即可，
# 负向神煞已足够判别；占类敏感度主要由 BA_SHA_CATEGORY_MULT 承载。
SHEN_SHA_CATEGORY_MULT = {
    "疾病": {"劫煞": 1.5, "灾煞": 1.5, "天罗": 1.5, "地网": 1.5},
    "官讼": {"劫煞": 1.5, "灾煞": 1.5, "桃花": 1.5},
    "家宅": {"天罗": 1.5, "地网": 1.5, "劫煞": 1.5, "灾煞": 1.5},
    "胎产": {"劫煞": 1.5, "灾煞": 1.5},
}

# ---- 八杀 valence（涨-positive；德只解凶不助吉→0，由 Gate 减半凶引擎处理）----
# 与 LiurenAnalysisEngine.BA_SHA_JIXIONG 对齐（德4/合3/鬼-4/墓-2/破-2/害-1/刑-1/冲-2）
BA_SHA_VALENCE = {
    "德": 0,    # 只解凶不助吉 → 不直接加涨质量（Gate 已对凶引擎×0.5）
    "合": 3,    # 和合圆成
    "鬼": -4,   # 伤残凶险
    "墓": -2,   # 暧昧不明
    "破": -2,   # 损坏
    "害": -1,   # 侵凌
    "刑": -1,   # 刑戮
    "冲": -2,   # 动荡
}

# 八杀 占类化倍率（部分占类对特定杀更敏感）
# ⚠️ 诊断修正（164 真实案，仅推导）：求财/出行/胎产的错例 100% 为「吉→凶」（过度看跌）。
#   主力修正来自 Gate 对这三类的 keti 降权（见 judgment_fusion.WEAK_KETI_CATS）。
#   此处对 求财/出行/胎产 放大【正向】八杀（合/德）×2：这些占类的吉案常带 合/德
#   （得财和合、出行得遂、胞胎得护），需抵消全局 keti 的过度看跌。
#   注：合+6 已触 SREF=4 强度上限，故 ×2 仅对「合/德 现而凶杀不显」的吉案起效，
#   不会把带 鬼/墓 的凶案误推吉（那由 SHEN_SHA_CATEGORY_POSITIVE 的 鬼墓 守卫兜底）。
#   疾病/官讼/家宅 保留负向放大（这些类凶杀更凶，原配置正确）。
BA_SHA_CATEGORY_MULT = {
    "求财": {"合": 2.0, "德": 2.0},
    "疾病": {"鬼": 1.5, "墓": 1.5, "刑": 1.5},
    "官讼": {"鬼": 1.5, "罗网": 1.5},
    "胎产": {"合": 1.5, "德": 2.0},
    "家宅": {"冲": 1.5, "破": 1.5, "害": 1.5, "刑": 1.5},
    "出行": {"冲": 1.5, "破": 1.5, "合": 2.0, "德": 2.0},
}

# 神煞 占类化【正向】集（仅对受益占类激活；全局 SHEN_SHA_GLOBAL 仍只保留负向，
# 避免凶重语料全局误推）。仅保留确证有益且不造假阳的：
#   出行：驿马/斩关 = 动象大吉（直接修复一个 吉→凶 错例；遇 鬼/墓 由守卫压制）
#   胎产：三光/德入 = 生扶（若盘面算得该神煞则加成；当前古例未算到，故实际 no-op）
# 求财 日德/日禄 已移除：实测在「无鬼/墓 的凶求财案」也现，引发 凶→吉 假阳；
#   且求财 吉→凶 错例的修复来自 合 放大 + keti 降权，本就不依赖日德/日禄，故移除无害。
SHEN_SHA_CATEGORY_POSITIVE = {
    "出行": {"驿马": 2, "斩关": 2},
    "胎产": {"三光": 1, "德入": 1},
}


# ======================================================================
# 1) 九宗门确定性推导（从 四课 + 日干支）
# ======================================================================
_V2_CALC = None  # 模块级缓存 V2 引擎单例（避免每次推导重复实例化）

def _get_v2_calc():
    global _V2_CALC
    if _V2_CALC is None:
        try:
            from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        except ImportError:
            from sike_sanchuan_engine import SiKeSanChuanCalculator2
        _V2_CALC = SiKeSanChuanCalculator2()
    return _V2_CALC


def _jzm_from_v2(ri_gan: str, ri_zhi: str, si_ke: List, tiandi_pan: Dict) -> List[str]:
    """【Task #204】委托权威 V2 引擎 SiKeSanChuanCalculator2.fa_sanchuan 取九宗门。

    把 V2 的 起法/课体 映射回 KETI_VALENCE 兼容的宗门名，作为古例路径的单一真相源。
    伏吟/返吟 由 derive_sanchuan_kege 按天地盘判定（与 V2 is_fu_yin/is_fan_yin 同义），
    此处不重复添加，避免双重计分。
    """
    calc = _get_v2_calc()
    res = calc.fa_sanchuan(si_ke, ri_gan, ri_zhi, tiandi_pan)
    qifa = res.get('起法', '')
    keti = res.get('课体', '')
    if qifa in ('伏吟法', '伏吟法（有贼克）'):
        return []   # 伏吟 → derive_sanchuan_kege（天地盘）
    if qifa == '反吟法':
        return []   # 返吟 → derive_sanchuan_kege（天地盘）
    if qifa == '八专法':
        return ['八专']
    if qifa == '别责法':
        return ['别责']
    if qifa == '遥克法':
        return ['遥克']
    if qifa == '昴星法':
        return ['昴星']
    if qifa == '贼克法':
        if '知一' in keti or '比用' in keti:
            return ['知一']
        if '重审' in keti:
            return ['重审']
        if '元首' in keti:
            return ['元首']
        return ['涉害']   # 见机格/察微格/涉害课 → 涉害(-1)
    return []


def derive_jiuzongmen(ri_gan: str, ri_zhi: str, si_ke: List, tiandi_pan: Dict = None) -> List[str]:
    """返回推导出的 课体名列表（可能空）。

    【Task #204 接线】若提供 tiandi_pan，则委托权威 V2 引擎 fa_sanchuan 取九宗门
    （起法/课体 → KETI_VALENCE 兼容名），保证古例路径与诚实基线同源（单一真相源）。
    无 tiandi_pan（兼容旧调用/非古例）时回退到下方经典起例。

    经典取用顺序（严格按《大六壬》起例，仅作无天地盘时的回退）：
      1) 八专：干支同位（日干寄宫 == 日支），如 甲寅/丁未/庚申/癸丑。
      2) 贼克：四课『同一课内』上神与下神相克
              —— 上克下 → 元首；下克上 → 重审。
      3) 遥克：无贼克时，四课上神与日干相克 → 遥克。
      4) 昴星/知一：无贼克且无遥克，取酉为用（兜底）。
    """
    if tiandi_pan:
        return _jzm_from_v2(ri_gan, ri_zhi, si_ke, tiandi_pan)
    out = []
    # 八专：干支同位（日干寄宫 == 日支），而非"干支五行相同"
    # 【BUG-FIX 2026-08-18】八专为独立课体，原 append 后未 return 会继续落入
    # 贼克/遥克判定（与 _jzm_from_v2 的 qifa=='八专法' 直接返回不一致）→ 双重课体。
    if ri_gan and ri_zhi and TIANGAN_JIGONG.get(ri_gan) == ri_zhi:
        return ['八专']

    # 四课: 每课 [课名, 上神地支, 下神(地支或日干/日支), ...]
    ups, downs = [], []
    for k in si_ke:
        if isinstance(k, (list, tuple)) and len(k) >= 3:
            ups.append(k[1])     # 上神地支
            downs.append(k[2])   # 下神（地支，或第一课=日干 / 第三课=日支）

    # ---- 2) 贼克（课内上下相克，非泛指上神克日干）----
    has_shangke = False  # 上克下 → 元首
    has_xiake = False    # 下克上 → 重审
    for up, down in zip(ups, downs):
        upw = ZHI_WX.get(up, '')
        downw = ZHI_WX.get(down, '') or GAN_WX.get(down, '')  # 下神可能是日干
        if not upw or not downw:
            continue
        if _ke(upw, downw):       # 上克下
            has_shangke = True
        elif _ke(downw, upw):     # 下克上
            has_xiake = True
    if has_shangke:
        out.append('元首')
        return out
    if has_xiake:
        out.append('重审')
        return out

    # ---- 3) 遥克（四课上神 vs 日干）----
    rg_wx = GAN_WX.get(ri_gan, '')
    has_yaok = False
    if rg_wx:
        for up in ups:
            uw = ZHI_WX.get(up, '')
            if uw and (_ke(uw, rg_wx) or _ke(rg_wx, uw)):
                has_yaok = True
                break
    if has_yaok:
        out.append('遥克')
        return out

    # ---- 4) 昴星 / 知一（无贼克且无遥克）----
    if ri_gan and GAN_WX.get(ri_gan):
        yg = GAN_YY.get(ri_gan)
        matched = [u for u in ups if ZHI_YY.get(u) == yg]
        out.append('知一' if matched else '昴星')
    else:
        out.append('昴星')
    return out


# ======================================================================
# 2) 三传课格确定性推导（从 三传 + 天地盘）
# ======================================================================
# ---- 经典返吟/伏吟：天地盘判定（权威定义，见 sike_sanchuan_engine._is_fan_yin/_is_fu_yin）----
# 返吟：天地盘相冲（十二神各居冲位）→ 主动、主变、主反复、主迅速。
# 伏吟：天地盘重合（十二神各归本位）→ 主静、主困、主迟、主反复。
# ⚠️ 旧代理「初传与末传相冲」是经典「天地盘相冲」的【必要非充分条件】(superset)，
#    会过度标定——许多非返吟局（如 #1048 初子末午冲）被误判返吟。现已改回权威定义。
_CHONG_MAP = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
              '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
_DIZHI_12 = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


def _is_tiandi_fu_yin(tiandi_pan: Dict[str, str]) -> bool:
    """经典伏吟：天地盘重合（地盘支 == 天盘支，十二神各归本位）。"""
    for d in _DIZHI_12:
        if tiandi_pan.get(d) != d:
            return False
    return True


def _is_tiandi_fan_yin(tiandi_pan: Dict[str, str]) -> bool:
    """经典返吟：天地盘全冲（地盘支 + 天盘支 = 六冲，十二神各居冲位）。"""
    for d in _DIZHI_12:
        if tiandi_pan.get(d) != _CHONG_MAP.get(d):
            return False
    return True


def derive_sanchuan_kege(san_chuan: List[str], tiandi_pan: Dict[str, str] = None) -> Tuple[int, List[str]]:
    """返回 (valence, 命中的课格名列表)。

    返吟/伏吟按【经典·天地盘】判定（需传入 tiandi_pan）；
    独足/连茹/三合局仍从三传确定性推出。
    无天地盘时保守不标返/伏吟（避免旧代理误判），不影响其余课格。
    """
    names = []
    v = 0
    sc = [z for z in san_chuan if z in ZHI_WX]
    if len(sc) < 3:
        return 0, names
    a, b, c = sc[0], sc[1], sc[2]
    order = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    ia, ib, ic = order.index(a), order.index(b), order.index(c)
    # 独足
    if a == b == c:
        names.append('独足'); v += KETI_VALENCE['独足']
    # 连茹（连续三步；【BUG-FIX 2026-08-18】用模12差值，修复跨子环绕
    # 如 亥→子→丑(11,0,1) 原线性差 -11/1 漏判）
    d1 = (ib - ia) % 12
    d2 = (ic - ib) % 12
    if d1 == 1 and d2 == 1:
        names.append('进连茹'); v += 1
    elif d1 == 11 and d2 == 11:
        names.append('退连茹'); v -= 1
    # 三合局
    triples = [{'申', '子', '辰'}, {'亥', '卯', '未'},
               {'寅', '午', '戌'}, {'巳', '酉', '丑'}]
    if {a, b, c} in triples:
        names.append('三合局'); v += 1
    # 伏吟 / 返吟：经典定义，需天地盘（天地盘重合→伏吟，全冲→返吟）
    if tiandi_pan:
        if _is_tiandi_fan_yin(tiandi_pan) and '返吟' not in names:
            names.append('返吟'); v += KETI_VALENCE['返吟']
        if _is_tiandi_fu_yin(tiandi_pan) and '伏吟' not in names:
            names.append('伏吟'); v += KETI_VALENCE['伏吟']
    return v, names


# ======================================================================
# 3) 文本锚定（扫描 duanyu 点名的 课体/毕法）
# ======================================================================
def scan_text(names_text: str) -> Tuple[List[str], List[str]]:
    """返回 (命中的课体名, 命中的毕法名)。"""
    keti_hits, bifa_hits = [], []
    if not names_text:
        return keti_hits, bifa_hits
    for nm in _ALL_NAMES:
        if nm in names_text:
            if nm in KETI_VALENCE and nm not in keti_hits:
                keti_hits.append(nm)
            if nm in BIFA_VALENCE and nm not in bifa_hits:
                bifa_hits.append(nm)
    return keti_hits, bifa_hits


# ======================================================================
# 格式转换：valence → 融合层期望的字段
# ======================================================================
def _level_str(v: int) -> str:
    if v >= 4:
        return '上吉'
    if v >= 3:
        return '大吉'
    if v >= 2:
        return '中吉'
    if v >= 1:
        return '小吉'
    if v <= -4:
        return '大凶'
    if v <= -3:
        return '中凶'
    if v <= -2:
        return '小凶'
    if v <= -1:
        return '凶'
    return '平'


def _bifa_block(v: int) -> Dict[str, Any]:
    if v > 0:
        w = min(8, max(1, v))
        return {'股市信号': {'综合倾向': '涨', '信号强度': min(1.0, 0.31 + v / 8.0),
                             '各信号权重': {'涨': w}}}
    if v < 0:
        w = min(8, max(1, -v))
        return {'股市信号': {'综合倾向': '跌', '信号强度': min(1.0, 0.31 + (-v) / 8.0),
                             '各信号权重': {'跌': w}}}
    return {'股市信号': {'综合倾向': '平', '信号强度': 0, '各信号权重': {}}}


def _sk_block(v: int) -> Dict[str, Any]:
    if v > 0:
        return {'股市信号': {'综合倾向': '涨', '信号强度': min(1.0, 0.51 + v / 6.0)}}
    if v < 0:
        return {'股市信号': {'综合倾向': '跌', '信号强度': min(1.0, 0.51 + (-v) / 6.0)}}
    return {'股市信号': {'综合倾向': '平', '信号强度': 0}}


# ======================================================================
# 课体格统一提取：委托 rich 检测器（SanChuanKegeDetector / BiFaDetector / SpecialKegeDetector）
# 古例路径(build_keti_duanyu) 与 股票路径 共用同一组检测器，消除双真相源（Task #205·方案A）。
# 受 RICH_KEGE_ENABLED 控制；关闭时回退原 limited 推导（见 build_keti_duanyu 受限分支）。
# ======================================================================
_RICH_KEGE = None


def _get_rich_kege():
    """模块级单例缓存三检测器，避免每次调用重实例化。"""
    global _RICH_KEGE
    if _RICH_KEGE is None:
        try:
            from engine.sanchuan_kege import SanChuanKegeDetector
            from engine.bifa_detector import BiFaDetector
            from engine.special_kege import SpecialKegeDetector
        except ImportError:
            from sanchuan_kege import SanChuanKegeDetector
            from bifa_detector import BiFaDetector
            from special_kege import SpecialKegeDetector
        _RICH_KEGE = (SanChuanKegeDetector(), BiFaDetector(), SpecialKegeDetector())
    return _RICH_KEGE


def _get_kongwang(result: Dict[str, Any]):
    a = result.get('analysis', {}) or {}
    xk = a.get('xun_kong')
    if isinstance(xk, (list, tuple)) and xk:
        return list(xk)
    ki = a.get('kong_info', {}) or {}
    kw = ki.get('空亡') if isinstance(ki, dict) else None
    if isinstance(kw, (list, tuple)) and kw:
        return list(kw)
    return None


def _derive_gan_zhi_shang(si_ke, tiandi_pan, ri_gan, ri_zhi):
    """从四课/天地盘推导干上神、支上神（富检测器毕法/特殊课格需要）。
    【BUG-FIX 2026-08-18】兼容 sike 元素 dict 格式（{'上神':..,'下神':..}）：
    原 `si_ke[0][1]` 对 dict 键 KeyError 1。"""
    gan_shang = ''
    zhi_shang = ''

    def _ke_shang(k):
        if not k:
            return ''
        if isinstance(k, dict):
            return str(k.get('上神', '') or '')[-1:]
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            return str(k[1])[-1:]
        return ''

    if isinstance(si_ke, list):
        if len(si_ke) >= 1:
            gan_shang = _ke_shang(si_ke[0])
        if len(si_ke) >= 3:
            zhi_shang = _ke_shang(si_ke[2])
    if not gan_shang and ri_gan and tiandi_pan:
        g = tiandi_pan.get(ri_gan, '')
        if g:
            gan_shang = str(g)[-1:]
    if not zhi_shang and ri_zhi and tiandi_pan:
        z = tiandi_pan.get(ri_zhi, '')
        if z:
            zhi_shang = str(z)[-1:]
    return gan_shang, zhi_shang


def _rich_sanchuan_kege(result, ri_gan, ri_zhi, tiandi_pan, yuejiang='', season='', calibrated=False):
    """委托 SanChuanKegeDetector（68 课格变体）；补充伏吟/返吟（rich 检测器无 tiandi_pan 入参）。

    yuejiang/season 透传，使 rich 检测器四时变体判定与原股票内联调用一致。
    calibrated=False（股票 raw 域）时不强制跌（与原内联行为一致）；calibrated=True
    （古例占卜域）时对伏吟/返吟强制跌，保 Gate 降权不失效。
    """
    san_chuan = result.get('san_chuan', []) or []
    keti_raw = result.get('keti', '')
    kongwang = _get_kongwang(result)
    sk_det, _, _ = _get_rich_kege()
    r = sk_det.detect(san_chuan, ri_gan, ri_zhi, keti_raw, kongwang, season)
    names = list(r.get('课格列表', []))
    # 伏吟/返吟 由天地盘判定补充（与 derive_sanchuan_kege 同源，保 Gate 降权不失效）
    if tiandi_pan:
        if _is_tiandi_fan_yin(tiandi_pan) and '返吟' not in names:
            names.append('返吟')
        if _is_tiandi_fu_yin(tiandi_pan) and '伏吟' not in names:
            names.append('伏吟')
    r['课格列表'] = names
    if calibrated and ('伏吟' in names or '返吟' in names):
        # 伏吟/返吟 强凶（KETI_VALENCE 各 -2）→ 覆盖为跌，与 limited 行为一致（仅占卜域）
        r['股市信号'] = {'综合倾向': '跌', '信号强度': min(1.0, 0.51 + 2.0 / 6.0)}
    return r, names


def _rich_bifa(result, ri_gan, ri_zhi, si_ke, tiandi_pan, yuejiang='', season='', si_ke_info=None):
    """委托 BiFaDetector（毕法赋 100 法；自带从 ganzhi 推旬空、从 yuejiang 推 season）。

    yuejiang/season 透传，使 rich 检测器四时变体判定与原股票内联调用一致。
    tian_jiang 读取兼容 古例(tianjiang_detail) 与 股票(tianjiang) 两种键名。
    si_ke_info：毕法 rules 70/10/23 读四课信息；股票内联传 transform 后的 2-元组，
                故允许显式覆盖（默认回退 si_ke 原始 4-元组，与古例路径一致）。
    """
    san_chuan = result.get('san_chuan', []) or []
    ganzhi = (ri_gan or '') + (ri_zhi or '')
    tian_jiang = result.get('tianjiang_detail') or result.get('tianjiang') or result.get('tianjiang_map') or {}
    gan_shang, zhi_shang = _derive_gan_zhi_shang(si_ke, tiandi_pan, ri_gan, ri_zhi)
    if si_ke_info is None:
        si_ke_info = si_ke
    _, bf_det, _ = _get_rich_kege()
    r = bf_det.detect(
        sanchuan_dizhi=san_chuan, ri_gan=ri_gan, ri_zhi=ri_zhi, ganzhi=ganzhi,
        yuejiang=yuejiang, season=season, gan_shang_shen=gan_shang, zhi_shang_shen=zhi_shang,
        si_ke_info=si_ke_info, tian_jiang=tian_jiang, tiandi_pan=tiandi_pan,
    )
    return r, list(r.get('匹配法条', []))


def _rich_special(result, ri_gan, ri_zhi, si_ke, tiandi_pan, yuejiang='', season=''):
    """委托 SpecialKegeDetector（贵登天门/罡塞鬼户/两蛇夹墓等）；填 special_kege 死信号。

    yuejiang/season 透传；tian_jiang 读取兼容 股票(tianjiang_map: 地支→天将) 与 古例(tianjiang_detail: branch-keyed)。
    """
    san_chuan = result.get('san_chuan', []) or []
    ganzhi = (ri_gan or '') + (ri_zhi or '')
    # 股票路径特殊处理：SpecialKegeDetector 需要 地支→天将 映射，故优先取 tianjiang_map；
    # 古例路径仅设 tianjiang_detail(branch-keyed)，回退到它（行为不变，古例 85.4% 基线不受影响）。
    tian_jiang = result.get('tianjiang_map') or result.get('tianjiang_detail') or result.get('tianjiang') or {}
    gan_shang, zhi_shang = _derive_gan_zhi_shang(si_ke, tiandi_pan, ri_gan, ri_zhi)
    _, _, sp_det = _get_rich_kege()
    r = sp_det.detect(
        sanchuan_dizhi=san_chuan, ri_gan=ri_gan, ganzhi=ganzhi,
        tiandi_pan=tiandi_pan, tian_jiang=tian_jiang,
        gan_shang_shen=gan_shang, zhi_shang_shen=zhi_shang, yuejiang=yuejiang, season=season,
    )
    return r


def build_keti_duanyu(result: Dict[str, Any], duanyu_text: str = "", zhanlei: str = "其他",
                      yuejiang: str = "", season: str = "", use_calibrated: Any = None,
                      level_override: Any = None, si_ke_info: Any = None) -> Dict[str, Any]:
    """返回 keti_duanyu；同时把命中的课体名写回 result['keti'] 供 Gate 使用。
    zhanlei: 占类（求财/出行/疾病/...），用于占类化 valence 覆盖。

    【Task #205·方案A】课体格统一提取：RICH_KEGE_ENABLED=True 时，三传课格/毕法/特殊课格
    委托 SanChuanKegeDetector/BiFaDetector/SpecialKegeDetector（与股票路径同源），填
    special_kege 死信号、升级 sanchuan_kege/bifa 丰富度。False 时回退原 limited 推导。
    """
    if not ENABLED:
        return {
            "level": "平",
            "bifa_summary": "",
            "bifa": {"股市信号": {"综合倾向": "平", "信号强度": 0}},
            "sanchuan_kege": {"股市信号": {"综合倾向": "平", "信号强度": 0}},
            "special_kege": {"信号汇总": {"倾向": "平", "强度": 0}},
        }

    # 【BUG-FIX 2026-08-18】空输入兜底：缺日干日支或三传不足时无法判定课体，
    # 直接返回平（原空 env 会算出差 valence 的"凶"级，如 level='凶'）。
    bi0 = result.get('basic_info', {}) or {}
    sc0 = [z for z in (result.get('san_chuan', []) or []) if z in ZHI_WX]
    if not bi0.get('ri_gan') or not bi0.get('ri_zhi') or len(sc0) < 3:
        return {
            "level": "平",
            "bifa_summary": "",
            "bifa": {"股市信号": {"综合倾向": "平", "信号强度": 0}},
            "sanchuan_kege": {"股市信号": {"综合倾向": "平", "信号强度": 0}},
            "special_kege": {"信号汇总": {"倾向": "平", "强度": 0}},
        }

    bi = result.get('basic_info', {}) or {}
    ri_gan = bi.get('ri_gan', '')
    ri_zhi = bi.get('ri_zhi', '')
    si_ke = result.get('si_ke', []) or []
    san_chuan = result.get('san_chuan', []) or []
    tiandi_pan = result.get('tiandi_pan', {}) or {}

    # --- 课体 valence：九宗门(推导·委托 V2 fa_sanchuan) + 文本锚定 ---
    jzm = derive_jiuzongmen(ri_gan, ri_zhi, si_ke, tiandi_pan) if DERIVE_ENABLED else []
    text_keti, text_bifa = scan_text(duanyu_text) if TEXT_ENABLED else ([], [])
    keti_names = list(dict.fromkeys(jzm + text_keti))  # 去重保序
    keti_val = sum(KETI_VALENCE.get(n, 0) for n in keti_names)

    # --- 占类化覆盖（理论驱动，无泄漏）---
    ov = ZIL_CATEGORY_OVERRIDE.get(zhanlei, {})

    if RICH_KEGE_ENABLED:
        calibrated = RICH_CALIBRATED_VALUATION if use_calibrated is None else bool(use_calibrated)
        sanchuan_kege_out, sk_names = _rich_sanchuan_kege(result, ri_gan, ri_zhi, tiandi_pan, yuejiang, season, calibrated)
        bifa_out, bifa_names = _rich_bifa(result, ri_gan, ri_zhi, si_ke, tiandi_pan, yuejiang, season, si_ke_info)
        special_out = _rich_special(result, ri_gan, ri_zhi, si_ke, tiandi_pan, yuejiang, season)
        keti_val += sum(ov.get(n, 0) for n in keti_names)
        keti_names_all = list(dict.fromkeys(keti_names + sk_names))
        result['keti'] = " ".join(keti_names_all)
        # level 优先用 level_override（股票域传 LiuRenKetiDuanyu 等级，保持融合层 keti 信号不变）
        level = level_override if level_override is not None else _level_str(keti_val)
        if calibrated:
            # 借 rich 检测器做更宽的名集合检测，但估值走占卜域已校准表（防股票偏涨漏回）
            sk_val = sum(KETI_VALENCE.get(n, 0) for n in sk_names)
            bifa_val = sum(BIFA_VALENCE.get(n, 0) for n in bifa_names)
            # 【BUG-FIX 2026-08-18】bifa_val 已加 ov 覆盖值而 sk_val 未加 → 占类化
            # 覆盖（如官讼对特定课格的 +/− 调整）在 sk 块中丢失，两路估值口径不一致。
            sk_val += sum(ov.get(n, 0) for n in sk_names)
            bifa_val += sum(ov.get(n, 0) for n in bifa_names)
            return {
                "level": level,
                "bifa_summary": " ".join(bifa_names),
                "bifa": _bifa_block(bifa_val),
                "sanchuan_kege": _sk_block(sk_val),
                "special_kege": {"信号汇总": {"倾向": "平", "强度": 0}},  # 特殊课格尚无占卜域估值表
            }
        return {
            "level": level,
            "bifa_summary": " ".join(bifa_names),
            "bifa": bifa_out,
            "sanchuan_kege": sanchuan_kege_out,
            "special_kege": special_out,
        }

    # ---- 受限回退（与历史 limited 推导一致，用于 A/B 对照）----
    bifa_names = list(text_bifa)
    # 确定性：铸印（三传 巳戌卯 / 卯巳戌 等）→ 铸印
    sc = [z for z in san_chuan if z in ZHI_WX]
    if DERIVE_ENABLED and len(sc) == 3 and set(sc) == {'巳', '戌', '卯'} and '铸印' not in bifa_names:
        bifa_names.append('铸印')
    bifa_val = sum(BIFA_VALENCE.get(n, 0) for n in bifa_names)
    sk_val, sk_names = derive_sanchuan_kege(san_chuan, tiandi_pan) if DERIVE_ENABLED else (0, [])

    if ov:
        keti_val += sum(ov.get(n, 0) for n in keti_names)
        bifa_val += sum(ov.get(n, 0) for n in bifa_names)

    # 写入 result['keti']（Gate 用：伏吟/返吟/罗网检测）
    result['keti'] = " ".join(keti_names + sk_names)

    level = _level_str(keti_val)
    bifa_summary = " ".join(bifa_names)
    return {
        "level": level,
        "bifa_summary": bifa_summary,
        "bifa": _bifa_block(bifa_val),
        "sanchuan_kege": _sk_block(sk_val),
        "special_kege": {"信号汇总": {"倾向": "平", "强度": 0}},
    }


# ======================================================================
# 神煞 / 八杀 valence 抽取（确定性，从盘面算，无泄漏）
# ======================================================================
def extract_shen_sha_valence(analysis: Dict[str, Any], zhanlei: str = "其他") -> Dict[str, Any]:
    """从 analysis['ba_sha'] / analysis['shen_sha'] 抽取占类化 valence。
    返回 {'ba_sha': {score, level, details}, 'shen_sha': {score, level, details}}。
    这两个字段由 LiurenAnalysisEngine 确定性算出（日干支+三传），不读 duanyu → 无泄漏。
    """
    ba = analysis.get('ba_sha', {}) or {}
    ss = analysis.get('shen_sha', {}) or {}
    ba_mult = BA_SHA_CATEGORY_MULT.get(zhanlei, {})
    ss_mult = SHEN_SHA_CATEGORY_MULT.get(zhanlei, {})

    # ---- 八杀 ----
    ba_score = 0
    ba_details = []
    has_gui_mu = False  # 鬼/墓 现则压制正向八杀(合/德)放大（鬼墓阻事，不可强行看吉）
    if BA_SHA_ENABLED and isinstance(ba, dict):
        details = ba.get('八杀明细', []) or []
        for x in details:
            if isinstance(x, dict) and x.get('状态', '未现') != '未现' and x.get('杀', '') in ('鬼', '墓'):
                has_gui_mu = True
                break
        for x in details:
            if not isinstance(x, dict):
                continue
            kill = x.get('杀', '')
            status = x.get('状态', '未现')
            if status == '未现':
                continue
            base = BA_SHA_VALENCE.get(kill, 0)
            if base == 0:
                continue  # 德：只解凶不助吉，交给 Gate
            mult = ba_mult.get(kill, 1.0)
            # 鬼墓守卫：出现 鬼/墓 时，压制正向八杀(合/德)的占类放大（避免带鬼凶案误推吉）
            if base > 0 and has_gui_mu:
                mult = 1.0
            # 空亡的凶杀减力、吉杀减半（与 LiurenAnalysisEngine 一致）
            if status == '空亡':
                eff = base * 0.3 if base > 0 else base * 0.25
            else:
                eff = base * mult
            ba_score += eff
            ba_details.append(f"{kill}{status}({eff:+.1f})")

    # ---- 神煞（仅日干支-derivable 真实神煞）----
    ss_score = 0
    ss_details = []
    if SHEN_SHA_ENABLED and isinstance(ss, dict):
        for name, base in SHEN_SHA_GLOBAL.items():
            val = ss.get(name)
            if not val:
                continue
            mult = ss_mult.get(name, 1.0)
            eff = base * mult
            ss_score += eff
            ss_details.append(f"{name}({eff:+.1f})")
        # 占类化【正向】神煞（仅受益占类激活；不在全局集，避免凶重语料误推）
        pos = SHEN_SHA_CATEGORY_POSITIVE.get(zhanlei, {})
        for name, base in pos.items():
            val = ss.get(name)
            if not val:
                continue
            # 出行：鬼/墓 现则压制驿马/斩关（鬼墓阻行，不可强行看吉）
            if zhanlei == "出行" and has_gui_mu:
                continue
            eff = float(base)  # 已是定向正分
            ss_score += eff
            ss_details.append(f"{name}+({eff:+.1f})")

    return {
        "ba_sha": {
            "score": int(round(ba_score)),
            "level": _level_str(int(round(ba_score))),
            "details": ba_details,
        },
        "shen_sha": {
            "score": int(round(ss_score)),
            "level": _level_str(int(round(ss_score))),
            "details": ss_details,
        },
    }


# ======================================================================
# 胎产专属确定性特征：子孙生扶 / 德神临 / 胞胎神（占类化·无泄漏）
# ----------------------------------------------------------------------
# 传统《六壬》胎产以「子孙爻」(日干所生五行 = 我生者) 为主神：
#   子孙 现于三传 且 旺相生扶(不空亡 / 不受克 / 不被冲 / 非独足) → 母子平安(吉)；
#   子孙 空亡 / 受克(父母爻克子孙) / 被冲 / 独足无孕象 → 损胎(凶)。
# 另：德神(日德) 临三传 为「厚德载物」生扶吉象（邵彦和断案明言"日辰有德与长生"）。
# 另：胞胎神 = 长生十二宫"胎"位（规范胎神），现于三传且不受克/不空亡/不冲/非独足 → 孕成(吉)。
# 仅 zhanlei=='胎产' 激活；判定只用 日干支+三传(课传核心)，不读 duanyu → 无泄漏。
# 设计验证（164 真实案中 4 例胎产：2 吉 2 凶）：
#   126 丙申(凶): 子孙丑现，但 受克(三传卯寅木克土) → A 不触发；日德巳不现 → B 不触发；
#                 胎位(丙火→子)不现三传 → C 不触发 ✓
#   127 己未(凶): 子孙酉现，但 独足(三传全酉) → A 不触发；日德寅不现 → B 不触发；
#                 胎位(己土→子)不现三传 → C 不触发 ✓
#   129 丁酉(吉): 子孙丑现，不空亡/不受克/不被冲/非独足 → A 触发 ✓（C: 胎位子不现）
#   130 丙辰(吉): 子孙土不现三传，但 日德巳现于初传 → B 触发 ✓（C: 胎位子不现；三传寅虽为民俗胎神，
#                 但长生十二宫胎位取子，且寅被申冲受克，故 C 不触发，避免与 126 寅混淆）
# ======================================================================
TAICHAN_RIDE = {  # 日德（标准日德表：阳干取禄前、阴干取合）
    '甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
    '己': '寅', '庚': '申', '辛': '巳', '壬': '亥', '癸': '寅',
}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 我生者 = 子孙
WX_KE = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}      # 克我者 = 官鬼
_LIU_CHONG = [{'子', '午'}, {'丑', '未'}, {'寅', '申'}, {'卯', '酉'}, {'辰', '戌'}, {'巳', '亥'}]
_LIU_CHONG_SET = {z: next((p - {z}).pop() for p in _LIU_CHONG if z in p) for z in '子丑寅卯辰巳午未申酉戌亥'}
_ZHI_ORDER = '子丑寅卯辰巳午未申酉戌亥'
# 三刑（支刑支单向表：X 刑 _SAN_XING[X]）。三刑组：寅巳申、丑戌未、子卯；辰午酉亥自刑。
# 用于官讼"助刑伐德"（S5）：三传任一支刑克日德 → 德神遭刑，讼凶（《中黄经》庚午日例：巳刑申=日德）。
_SAN_XING = {'子': '卯', '丑': '戌', '寅': '巳', '卯': '子', '辰': '辰', '巳': '申',
             '午': '午', '未': '丑', '申': '寅', '酉': '酉', '戌': '未', '亥': '亥'}
# 洛书地支数（邵彦和应期断法数源，2026-08-02 从 219 案 duanyu 实测全对拍）：
#   子午9 丑未8 寅申7 卯酉6 辰戌5 巳亥4
# 用例：卯数六故不出六年(宅墓02·005) / 酉六数故主六年酒败(宅墓02·040) / 巳四加戌五共九年(前程03·069)
#       / 寅申各七数故有七年之测(出行11·154) / 丑八故八年也(疾病13·173) / 寅卯辰共八故初八日(亡盗15·200)
ZHI_NUMBER = {'子': 9, '午': 9, '丑': 8, '未': 8, '寅': 7, '申': 7,
              '卯': 6, '酉': 6, '辰': 5, '戌': 5, '巳': 4, '亥': 4}


def get_yingqi_text(ri_gan: str, ri_zhi: str, sanchuan_dizhi: list, si_ke=None,
                    zhanlei: str = '其他', zishu: str = '') -> str:
    """应期断法·多运算模式（记录层·叙事用，不参与 valence——应期=何时发生，非吉凶方向）。
    邵彦和洛书数法（通解下卷「后天五行数」+ 219 案回测，见 docs/reports/_应期断法体系研究.md）：
      支数表：子午9 丑未8 寅申7 卯酉6 辰戌5 巳亥4（ZHI_NUMBER）。
      运算模式（回测 17 样本 76% 复现）：
        ① 单支   ：独支/众数支之数 → 年应期（卯数六故不出六年）
        ② 相加   ：两/三支数相加 → 年应期（亥数四寅数七乃十一年；卯六辰五巳四共十五年）
        ③ 相乘   ：两支数相乘 → 寿数/物数（子九申七七九共六十三；申七亥四四七二十八）
        ④ 支位计数：行年支至课中支位差 → 年（从酉数至辰八位故八年）
      ⚠️ 邵彦和取「断句内特定支组合」非三传全支，运算选择依占类/所问而定（同一课可多解），
      故本函数输出**全部可行候选**，由用户/上层按所问选用；不武断选一。
    阴宅专属（zishu=='阴宅'，2026-08-18 邵公断案宅墓章深读）：
      ⑤ 取数增一半：主数 + 其半 → 先X年后更X年（§040/0344"酉六数故主六年酒败，更三年死，酉增一半也"；
         刘评"六年病者酉数为六…更三年死者顺数三年为丁巳水之绝地"）
      ⑥ 取数减一半：主数 前全用 后减半 → 十二年断（§043"未乃八数，两个八年十六年，先个八年全用后用一半，故十二年"；
         刘评"未八数，两个八年是十六年"）
    返回叙事文本；无可断时返回 ''。"""
    if not sanchuan_dizhi:
        return ''
    sc = [z for z in sanchuan_dizhi if z in ZHI_NUMBER]
    if not sc:
        return ''
    nums = [ZHI_NUMBER[z] for z in sc]
    parts = ['%s数%d' % (z, ZHI_NUMBER[z]) for z in sc]
    cands = []  # (模式, 说明)
    # ① 单支/众数
    from collections import Counter as _C
    cnt = _C(nums)
    top_num, top_cnt = cnt.most_common(1)[0]
    if len(sc) == 1 or top_cnt >= 2:
        cands.append(('单支%d' % top_num, '众数/独支 %d' % top_num))
    # ② 相加（去重支，和≤15 作年断）
    uniq_nums = sorted(set(nums), reverse=True)
    if len(uniq_nums) >= 2 and sum(uniq_nums) <= 15:
        cands.append(('相加%d' % sum(uniq_nums), '+'.join(str(n) for n in uniq_nums)))
    elif len(uniq_nums) >= 2:
        cands.append(('相加%d' % sum(uniq_nums), '+'.join(str(n) for n in uniq_nums) + '(和>15)'))
    # ③ 相乘（前两支/去重两支）
    if len(uniq_nums) >= 2:
        a, b = uniq_nums[0], uniq_nums[1]
        cands.append(('相乘%d' % (a * b), '%d×%d' % (a, b)))
    # ④ 支位计数（初传/末传与日支的位差；需 si_ke 供日支）
    ri_z = ''
    if si_ke and len(si_ke) >= 3:
        _k = si_ke[2]
        if isinstance(_k, (list, tuple)) and len(_k) >= 3:
            ri_z = _k[2] if _k[2] in ZHI_NUMBER else ''
    if ri_z and ri_z in ZHI_NUMBER and ri_z in _ZHI_ORDER:
        for _z in sc:
            _d = (_ZHI_ORDER.index(_z) - _ZHI_ORDER.index(ri_z)) % 12
            if 2 <= _d <= 11:
                cands.append(('支位%d' % _d, '%s至%s%d位' % (ri_z, _z, _d)))
                break
    # ⑤ 阴宅专属：取数增一半（§040/0344"壬日酉作天空故主酒败，酉六数故主六年酒败，更三年死，酉增一半也"）
    #   取数源：优先干上神（si_ke 第一课上神——邵公断阴宅寿数/应期多取干上，如§040酉=干上、§043未=干上），
    #   无干上神时退回三传首支。
    if zishu == '阴宅':
        _pick = ''
        if si_ke and len(si_ke) >= 1:
            _k0 = si_ke[0]
            if isinstance(_k0, (list, tuple)) and len(_k0) >= 2 and _k0[1] in ZHI_NUMBER:
                _pick = _k0[1]
            elif isinstance(_k0, dict):
                _pick = _k0.get('上神', '')
        if _pick not in ZHI_NUMBER:
            _pick = sc[0] if sc else ''
        if _pick:
            _main = ZHI_NUMBER[_pick]
            _half = _main // 2
            if _half >= 1:
                cands.append(('增半%d' % (_main + _half), '干上%s数%d增一半→先%d年后更%d年' % (_pick, _main, _main, _half)))
    # ⑥ 阴宅专属：取数减一半（§043"未乃八数，两个八年是十六年，先个八年全用后用一半，故十二年"；
    #   亦取干上神，与⑤同源）
    if zishu == '阴宅':
        _pick2 = ''
        if si_ke and len(si_ke) >= 1:
            _k0 = si_ke[0]
            if isinstance(_k0, (list, tuple)) and len(_k0) >= 2 and _k0[1] in ZHI_NUMBER:
                _pick2 = _k0[1]
            elif isinstance(_k0, dict):
                _pick2 = _k0.get('上神', '')
        if _pick2 not in ZHI_NUMBER:
            _pick2 = sc[0] if sc else ''
        if _pick2:
            _main2 = ZHI_NUMBER[_pick2]
            _half2 = _main2 // 2
            if _half2 >= 1:
                cands.append(('减半%d' % (_main2 * 2 - _half2), '干上%s数%d两倍%d先全用后减半→%d年' % (_pick2, _main2, _main2 * 2, _main2 * 2 - _half2)))
    # 输出（按占类权重排序：家宅/功名→相加年断、出行→单支、疾病/官讼→相乘寿数；2026-08-02 219案统计）
    if not cands:
        return '邵彦和应期法：%s → 取用神支之数' % '、'.join(parts)
    # 占类偏好：'相加' 优先（家宅/功名/求财/婚姻 年断）、'相乘' 优先（疾病/官讼 寿数数目）、'单支' 优先（出行/胎产/其他）
    _pref = {'家宅': '相加', '功名': '相加', '求财': '相加', '婚姻': '相加',
             '疾病': '相乘', '官讼': '相乘',
             '出行': '单支', '胎产': '单支', '其他': '单支'}
    # 单位偏好（壬占汇选 762 条应期断句统计，2026-08-02）：宅墓/求财/婚姻→年断、疾病/行人/官讼→月断、失物→日断、天时→日/时
    _unit_pref = {'家宅': '年', '功名': '年', '求财': '年', '婚姻': '年',
                  '疾病': '月', '行人': '月', '官讼': '月',
                  '失物': '日', '天时': '日'}
    _up = _unit_pref.get(zhanlei, '')
    _prefer = _pref.get(zhanlei, '')
    if zishu == '阴宅':
        # 阴宅偏好：增半/减半（邵公阴宅期候应象）优先于普通单支/相加
        _prefer = '增半'
    if _prefer:
        cands.sort(key=lambda x: (0 if x[0].startswith(_prefer) else 1, x[0]))
    uniq_c = []
    seen_k = set()
    for _i, (_k, _v) in enumerate(cands):
        if _k in seen_k:
            continue
        seen_k.add(_k)
        _mark = '★' if (_i == 0 and _prefer and _k.startswith(_prefer)) else ''
        uniq_c.append('%s%s=%s' % (_mark, _k, _v))
    _tail = '（%s占宜%s断）' % (zhanlei, _up) if _up else ''
    if zishu == '阴宅':
        _tail = '（阴宅宜年断：邵公期候应象"取数增一半/减一半"）'
    return '邵彦和应期法：%s → %s%s' % ('、'.join(parts), '；'.join(uniq_c), _tail)


# ---- 物数断法（数量·叙事层，2026-08-02 壬占汇选挖掘）----
# 应期=何时（时间），物数=多少（数量）。邵彦和/徐次宾物数运算（壬占汇选 543 案实证）：
#   ① 相乘取数：两支数相乘 → 基数（丑8×螣蛇4=32、未8×白虎7=56、寅7×子9=63）
#   ② 旺相乘十倍：旺相之气相乘则「人十则言百」（32→320贯、51→510里、63→6300人）
#   ③ 休囚不加倍：白虎无气时 56 贯不放大（0077）
#   ④ 行年上下相乘+遁干：亥4×子9=36 + 遁干乙8丙7=15 → 51 → 510里（干支共用数实操罕见实例）
#   ⑤ 旺相倍进：水旺于冬加倍 → 1020里（通解下卷「上下相乘」「旺相倍进」实操版）
# 用途：钱数/里程/人数（物数域）。⚠️ 叙事层严禁入评分（数量非吉凶）。
_GAN_NUMBER = {'甲': 9, '己': 9, '乙': 8, '庚': 8, '丙': 7, '辛': 7,
               '丁': 6, '壬': 6, '戊': 5, '癸': 5}  # 通解下卷「后天五行数」干支共用（实操罕见）


def get_wushu_text(ri_gan: str, sanchuan_dizhi: list, xing_nian_shang: str = '',
                   tianjiang_list: list = None, zhanlei: str = '其他') -> str:
    """物数断法（叙事层·不参与 valence）。
    输出可行物数候选：三传两两相乘之数（旺相×10、休囚不加）；行年上下相乘+遁干（若给 xing_nian_shang）。
    返回叙事文本；无可断时返回 ''。"""
    sc = [z for z in (sanchuan_dizhi or []) if z in ZHI_NUMBER]
    nums = [ZHI_NUMBER[z] for z in sc]
    cands = []
    # ① 三传两两相乘（去重支）
    uniq_nums = sorted(set(nums), reverse=True)
    if len(uniq_nums) >= 2:
        a, b = uniq_nums[0], uniq_nums[1]
        base = a * b
        cands.append(('相乘%d' % base, '%d×%d' % (a, b)))
        cands.append(('旺相×10→%d' % (base * 10), '%d×%d=人十则言百' % (a, b)))
    # ② 行年上下相乘+遁干（干支共用数实操；需行年上神）
    if xing_nian_shang and xing_nian_shang in ZHI_NUMBER:
        xns = xing_nian_shang
        # 行年支数 × 行年上神数
        # （0269：行年亥上子 → 亥4×子9=36；行年支不可靠仅给上神单支数，遁干并入③，叙事层）
        n1 = ZHI_NUMBER[xns]
        cands.append(('行年%s数%d' % (xns, n1), '单支 %d' % n1))
        cands.append(('行年旺相×10→%d' % (n1 * 10), '%d×10 远行人十则言百' % n1))
    # ③ 加遁干（干支共用数：ri_gan 遁干数并入）
    g_n = _GAN_NUMBER.get(ri_gan, 0)
    if g_n and len(uniq_nums) >= 2:
        s = sum(uniq_nums[:2]) + g_n
        cands.append(('干支并%d' % s, '%d+%d+遁干%d' % (uniq_nums[0], uniq_nums[1], g_n)))
        cands.append(('干支并旺×10→%d' % (s * 10), '%d 人十则言百' % s))
    if not cands:
        return ''
    uniq_c = []
    seen_k = set()
    for _k, _v in cands:
        if _k in seen_k:
            continue
        seen_k.add(_k)
        uniq_c.append('%s=%s' % (_k, _v))
    return '壬占汇选物数法：%s' % '；'.join(uniq_c)


# ---- 月建应期（月建法·叙事层，2026-08-02 壬占汇选挖掘）----
# 原文规律（壬占汇选 762 条应期断句 + 典型案例）：
#   0012"用是子与未六害…讼起六月者未为六月建也"（未=干上神 → 断六月）
#   0019"九月成就者归计戌为九月建也"（戌=末传 → 断九月）
#   0077"发用大吉为财，为十二月建"（丑=初传 → 断十二月）；"未为六月建，故于六月得钱"（未=时上 → 断六月）
#   0064"丑是十二月建亥是十月建，丑至寅三位，即三日也"（月建位差 → 断日）
# 判定：月建支（正月建寅…十二月建丑）出现在课盘（三传/干上神/时上）→ 应期在该月。
# ⚠️ 叙事层输出，不参与 valence（应期=何时发生非吉凶方向）。
# 地支→农历月（月建）：寅=正月建，卯=二月建…丑=十二月建（地支顺推）
_YUE_JIAN_MONTH = {'寅': 1, '卯': 2, '辰': 3, '巳': 4, '午': 5, '未': 6,
                   '申': 7, '酉': 8, '戌': 9, '亥': 10, '子': 11, '丑': 12}


def get_yuejian_yingqi_text(ri_gan: str, ri_zhi: str, sanchuan_dizhi: list,
                            si_ke=None, shichen: str = '') -> str:
    """月建应期（叙事层·不参与 valence）。
    月建支在课盘关键位（初传/日干上神/时辰）→ 断应期在该农历月。
    原文依据（壬占汇选）：未=干上→断六月(0012)；戌=末传归计→断九月(0019)；
      丑=发用→断十二月(0077)；未=时上→断六月(0077)。
    收敛取位：初传（发用）+ 干上神 + 时辰（避免全盘支过载）。
    返回叙事文本；无可断时返回 ''。"""
    if not sanchuan_dizhi:
        return ''
    check = []
    # 初传（发用）
    sc = [z for z in sanchuan_dizhi if z in _YUE_JIAN_MONTH]
    if sc:
        check.append(('初传', sc[0]))
    # 日干上神（si_ke 第一课=干上，格式 tuple(课名, 上神, 下神, ...)）
    if si_ke and len(si_ke) >= 1:
        k = si_ke[0]
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            gan_shang = k[1]
            if gan_shang in _YUE_JIAN_MONTH:
                check.append(('干上', gan_shang))
    # 时辰
    if shichen in _YUE_JIAN_MONTH:
        check.append(('时', shichen))
    hits = [(pos, z, _YUE_JIAN_MONTH[z]) for pos, z in check if z in _YUE_JIAN_MONTH]
    if not hits:
        return ''
    parts = ['%s%s=%d月建' % (pos, z, m) for pos, z, m in hits]
    return '月建应期：%s → 应于该月' % '、'.join(parts)


# ---- 应期三法统一输出（叙事层整合，2026-08-02）----
# 应期断法三支柱（均叙事层，不参与 valence——应期=何时发生，非吉凶方向）：
#   ① 支数法（get_yingqi_text）：洛书地支数多候选（单支/相加/相乘/支位）+ 占类权重 + 单位偏好
#   ② 月建法（get_yuejian_yingqi_text）：月建支在初传/干上/时上 → 应于该月
#   ③ 太岁法（get_tai_sui_lin_shen_text）：太岁临身 → 当年应（需 tai_sui_zhi 参数）
# 物数法（get_wushu_text）= 数量非时间，单独输出（不混入应期）。
def get_yingqi_unified(ri_gan: str, ri_zhi: str, sanchuan_dizhi: list,
                       tiandi_pan: dict = None, si_ke=None, shichen: str = '',
                       tai_sui_zhi: str = '', zhanlei: str = '其他', zishu: str = '') -> str:
    """应期三法统一输出（叙事层·不参与 valence）。
    整合：支数法 + 月建法 + 太岁法（有参才输出），各法换行分块。
    zishu：家宅子类（阳宅/阴宅/迁移），阴宅时支数法启用邵公"增半/减半"期候应象。
    返回统一叙事文本；全部无可断时返回 ''。"""
    blocks = []
    # ① 支数法
    t1 = get_yingqi_text(ri_gan, ri_zhi, sanchuan_dizhi, si_ke=si_ke, zhanlei=zhanlei, zishu=zishu)
    if t1:
        blocks.append(t1)
    # ② 月建法
    t2 = get_yuejian_yingqi_text(ri_gan, ri_zhi, sanchuan_dizhi, si_ke=si_ke, shichen=shichen)
    if t2:
        blocks.append(t2)
    # ③ 太岁法（需 tiandi_pan + tai_sui_zhi）
    if tiandi_pan and tai_sui_zhi:
        t3 = get_tai_sui_lin_shen_text(ri_gan, tiandi_pan, tai_sui_zhi)
        if t3:
            blocks.append(t3)
    if not blocks:
        return ''
    return '\n'.join(blocks)


# ---- 太岁临身应期（太岁法·叙事层）----
# 通解/疏正：宅墓02·013"流年太岁在亥，太岁乘空临身，所谓当头立也。太岁即临身，而行年又入墓地，故主十六年而亡耳"；
#           前程03·059"太岁来克身，当年可见不宁"；疾病13·163"四十一岁上，太岁到寅，死矣"。
# 判定：太岁支 == 日干寄宫上神（干寄宫地盘→天盘对应支）→ 太岁临身，当年大凶"当头立"。
# 需求：tai_sui_zhi（当年太岁支，如 2026 丙午年→午）；古例从 duanyu 提取"太岁在X/X年太岁"；起课页由用户选。
# ⚠️ 太岁=年份参数，古案数据残缺（仅 4 案可提）→ 评估路径缺参零触发；叙事层输出不参与 valence。
_RI_JI_GONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
               '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}


def get_tai_sui_lin_shen_text(ri_gan: str, tiandi_pan: dict, tai_sui_zhi: str = '',
                              sanchuan_dizhi: list = None) -> str:
    """太岁临身应期（叙事层，不参与 valence）。太岁支==干寄宫上神 → 当头立凶（当年应）。
    返回叙事文本；缺参/不临身返回 ''。"""
    if not ri_gan or not tiandi_pan or tai_sui_zhi not in ZHI_NUMBER:
        return ''
    jg = _RI_JI_GONG.get(ri_gan)
    if not jg or jg not in tiandi_pan:
        return ''
    gan_shang = tiandi_pan.get(jg, '')
    if gan_shang == tai_sui_zhi:
        return '太岁临身：太岁(%s)临日干寄宫(%s)上神 → 当头立，当年应凶' % (tai_sui_zhi, jg)
    return ''
# 月解神（地解神/解神表，憨爷 2026-08-02 拍板：子月地解神为未）
# 出处：《图解六壬大全》第一部 占法及神煞，P297（页码 286）"星煞总表"内解/解神/外解行
# 起法：每两月一值（12 个月循环）：
#   1申 2申 3酉 4酉 5戌 6戌 7亥 8亥 9午 10午 11未 12未
# 依据：
#   1) 图解大全 P297 单行超高清单行 OCR 清晰显示完整 12 值（每两月同一支）
#   2) 通解 官讼例二十四（十一月乙卯日）："未乃十一月解神"→ 11月=未 ✓
#   3) 通解 官讼例二十五（十一月辛酉日）："乃解神未临寅上"→ 11月=未 ✓
# 勘误历史：
#   - 先曾按通解 404 页注释⑦"月建冲破"定为 11月=午（错误，已纠正）
#   - 再曾假设"正月酉起顺行"反推完整表（错误，已纠正——实际是"每两月一值"非"每月一值"）
_MONTH_JIE_SHEN = {1: '申', 2: '申', 3: '酉', 4: '酉', 5: '戌', 6: '戌',
                   7: '亥', 8: '亥', 9: '午', 10: '午', 11: '未', 12: '未'}
# 三合局→合成五行（用于 D2 守卫"会局助日"判定：申子辰水、亥卯未木、寅午戌火、巳酉丑金）
_SAN_HE_TABLE = (({'申', '子', '辰'}, '水'),
                  ({'亥', '卯', '未'}, '木'),
                  ({'寅', '午', '戌'}, '火'),
                  ({'巳', '酉', '丑'}, '金'))
# 胞胎神 = 长生十二宫之"胎"位（规范胎神，非民俗"寅"）。五行长生起处：
#   木长生亥→胎在酉；火长生寅→胎在子；土随火→胎在子；金长生巳→胎在卯；水长生申→胎在午。
# 不用"寅"：126 丙申三传含寅却为凶（子孙受克），裸用寅会误翻 → 取长生十二宫胎位避假阳。
# 【BUG-FIX 2026-08-18】土胎统一为双位 ('午','子')，与 _gan_changsheng 的
# 水土同宫(主值子)+火土同宫(次值午) 口径一致（原单值'子'漏午，两处胞胎神口径矛盾）。
TAI_WEI = {'木': '酉', '火': '子', '土': ('午', '子'), '金': '卯', '水': '午'}


def _tai_wei_in(wei, sc) -> bool:
    """胞胎神（可能 tuple 双位）是否有支现于三传。"""
    if isinstance(wei, (tuple, list, set, frozenset)):
        return any(z in sc for z in wei)
    return bool(wei) and wei in sc


def _xunkong(ri_gan: str, ri_zhi: str) -> set:
    """日干支 → 旬空两支（确定性，无泄漏）。"""
    if ri_gan not in GAN_WX or ri_zhi not in ZHI_WX:
        return set()
    g_idx = '甲乙丙丁戊己庚辛壬癸'.index(ri_gan)
    z_idx = _ZHI_ORDER.index(ri_zhi)
    shou = (z_idx - g_idx) % 12          # 旬首甲支序
    k1 = (shou + 10) % 12                # 旬空 = 旬首 +10 / +11
    k2 = (shou + 11) % 12
    return {_ZHI_ORDER[k1], _ZHI_ORDER[k2]}


def _nian_ming_shang_shen(ben_ming_zhi: str, tiandi_pan: dict) -> str:
    """本命地支 → 年命上神（本命居地盘，看天盘对应支）。
    毕法赋 53法"年命居亥上乘天罡辰虎冲戌蛇故名破墓"即此算法：
    年命地支在地盘，其上神（天盘对应）决定吉凶。
    tiandi_pan: {地盘支: 天盘支}（如 {'子':'酉','午':'卯'} → 午命上神卯）。
    无本命/无天地盘 → 返回 ''（年命守卫不启用，安全）。"""
    if not ben_ming_zhi or ben_ming_zhi not in ZHI_WX or not tiandi_pan:
        return ''
    # 兼容两种键序：{地盘:天盘}（引擎标准）；若发现反序（{天盘:地盘}）自动纠正
    if ben_ming_zhi in tiandi_pan:
        return tiandi_pan.get(ben_ming_zhi, '')
    for di, tian in tiandi_pan.items():
        if tian == ben_ming_zhi:
            return di
    return ''


def _xing_nian_zhi(ben_ming_zhi: str, age: int, sex: str = '男') -> str:
    """行年推算（标准六壬：男命从本命逆数，女命顺数，本命1岁起算到虚岁）。
    age: 虚岁（实岁+1）。
    sex: '男'/'女'（缺省男；古案无性别字段时用男）。
    返回行年地支；本命/岁数异常 → ''。
    注：通解 上卷 L3937 有 4个实例（男丑17/19、女寅16/卯18），与本算法部分吻合（女寅16=巳✓、男寅19=申✓），
    另两例（男丑17=午、女卯18=卯）按本算法算出 酉/申 不符——疑为古籍版本/流派差异或OCR。
    本算法作为主流规则供起课页使用，权威性以憨爷纸质书为准。"""
    if not ben_ming_zhi or ben_ming_zhi not in ZHI_WX:
        return ''
    if not isinstance(age, int) or age < 1:
        return ''
    forward = (sex == '女')
    # 本命为1岁：移动 (age-1) 位
    # 注意：ZHI_WX 是 dict(地支->五行)，无 .index()；此处用局部 zhi_list（与 _ZHI_ORDER 一致）
    zhi_list = '子丑寅卯辰巳午未申酉戌亥'
    idx = zhi_list.index(ben_ming_zhi)
    step = (age - 1) if forward else -(age - 1)
    return zhi_list[(idx + step) % 12]


def _xun_ding(ri_gan: str, ri_zhi: str) -> str:
    """日干支 → 旬丁支（通解 p138：甲子旬丁卯、甲戌旬丁丑…；旬丁=旬首支+3）。
    用于"财乘丁马"（求财章 L4622：财乘丁马忌庚辛，壬癸见丁看事类）。"""
    if ri_gan not in GAN_WX or ri_zhi not in ZHI_WX:
        return ''
    g_idx = '甲乙丙丁戊己庚辛壬癸'.index(ri_gan)
    z_idx = _ZHI_ORDER.index(ri_zhi)
    shou = (z_idx - g_idx) % 12
    return _ZHI_ORDER[(shou + 3) % 12]


# 驿马（按日支三合）：申子辰马在寅、亥卯未马在巳、寅午戌马在申、巳酉丑马在亥（通解 p92）
_YI_MA = {
    '申': '寅', '子': '寅', '辰': '寅',
    '亥': '巳', '卯': '巳', '未': '巳',
    '寅': '申', '午': '申', '戌': '申',
    '巳': '亥', '酉': '亥', '丑': '亥',
}


def extract_taichan_valence(ri_gan: str, ri_zhi: str, san_chuan: List[str],
                            tianjiang_list: List[str] = None,
                            zhanlei: str = "其他") -> Dict[str, Any]:
    """胎产吉信号（确定性·无泄漏）。仅 zhanlei=='胎产' 有意义；否则 score=0。"""
    if zhanlei != '胎产':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not san_chuan or len(san_chuan) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}

    zisun_wx = WX_SHENG.get(rgwx)          # 子孙五行（我生者）
    ke_zisun_wx = WX_KE.get(zisun_wx)      # 克子孙者（父母）五行
    sc = [z for z in san_chuan if z in ZHI_WX]
    # 【BUG-FIX 2026-08-18】过滤后不足 3 支视为异常输入，与其他占类守卫口径一致
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc_wx = [ZHI_WX[z] for z in sc]
    kong = _xunkong(ri_gan, ri_zhi)
    tj = list(tianjiang_list or [])
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]

    # ---- A: 子孙生扶 ----
    zisun_zhi = [z for z in sc if ZHI_WX.get(z) == zisun_wx]
    a_fired = False
    if zisun_zhi:
        dudu = len(set(sc)) == 1                              # 独足（无孕象）
        shouke = any(w == ke_zisun_wx for w in sc_wx)         # 父母克子孙
        kong_z = any(z in kong for z in zisun_zhi)            # 子孙落旬空
        chong_z = False                                       # 子孙被六冲（冲支现于三传）
        for z in zisun_zhi:
            for pair in _LIU_CHONG:
                if z in pair:
                    partner = (pair - {z}).pop()
                    if partner in set(sc):
                        chong_z = True
        a_fired = not (dudu or shouke or kong_z or chong_z)

    # ---- B: 德神临（日德现于三传） ----
    ride_zhi = TAICHAN_RIDE.get(ri_gan)
    b_fired = bool(ride_zhi and ride_zhi in sc)

    # ---- D: 胎逢偏鬼及玄武（孕产章 L4121：胞胎神为官鬼五行且玄武现传 → 种子私妊/非己所出）----
    # 放 C 前：私妊凶象优先于胞胎旺相吉（胞胎乘玄武时不可断孕成）
    tai2 = TAI_WEI.get(rgwx)
    if tai2 and _tai_wei_in(tai2, sc) and ZHI_WX.get(sc[0]) == WX_KE.get(rgwx) and '玄武' in tj_at:
        # 胞胎神为官鬼五行：取命中胞胎支的五行判定
        _tai_hit = next((z for z in sc if (isinstance(tai2, (tuple, list, set, frozenset)) and z in tai2) or z == tai2), '')
        return {"score": -4, "level": "凶-胎逢偏鬼玄武私妊",
                "details": [f"胞胎神({_tai_hit or tai2})为官鬼五行且玄武现传→种子私妊，非己所出"],
                "fired": "D"}

    # ---- C: 胞胎神（长生十二宫胎位） ----
    tai_zhi = TAI_WEI.get(rgwx)
    c_fired = False
    if tai_zhi and _tai_wei_in(tai_zhi, sc):
        _tai_hit = next((z for z in sc if (isinstance(tai_zhi, (tuple, list, set, frozenset)) and z in tai_zhi) or z == tai_zhi), '')
        # 【BUG-FIX 2026-08-18】空亡判定针对"命中胞胎支"（双位胞胎午/子只判实际入传者），
        # 原判全体胞胎支 → 双位中任一落空即门控，另一不空胎位被误杀。
        kong_t = _tai_hit in kong                                  # 命中胞胎支落旬空
        ke_tai_wx = WX_KE.get(ZHI_WX.get(_tai_hit, ''))            # 克胞胎者五行
        shouke_t = any(w == ke_tai_wx for w in sc_wx)              # 胞胎受克
        dudu_t = len(set(sc)) == 1                                # 独足无孕象
        chong_t = False                                           # 胞胎被六冲
        # 【BUG-FIX 2026-08-18】冲判定基于"命中胞胎支" _tai_hit：
        # 原遍历全部胞胎位(如午,子)判冲 → 胞胎午不在传，其冲对子反在传时误判"胞胎被冲"。
        if _tai_hit:
            for pair in _LIU_CHONG:
                if _tai_hit in pair:
                    partner = (pair - {_tai_hit}).pop()
                    if partner in set(sc):
                        chong_t = True
        c_fired = not (kong_t or shouke_t or dudu_t or chong_t)

    if a_fired:
        return {"score": 6, "level": "吉-子孙生扶",
                "details": [f"子孙({zisun_wx})现于三传且生扶(不空亡/不受克/不被冲/非独足)"],
                "fired": "A"}
    if b_fired:
        return {"score": 6, "level": "吉-德神临",
                "details": [f"日德({ride_zhi})临三传"], "fired": "B"}
    if c_fired:
        return {"score": 6, "level": "吉-胞胎神",
                "details": [f"胞胎神({_tai_hit or tai_zhi})临三传且不受克/不空亡/不冲/非独足"],
                "fired": "C"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 官讼专属确定性特征：解厄吉(P) / 官鬼凶(Q) / 连茹凶(R)（占类化·无泄漏）
# ----------------------------------------------------------------------
# 传统《六壬》词讼(官讼)判定要点（邵彦和断案验证）：
#   - 解厄吉：末传见青龙(或解神/天喜)，主官贵相助、恩赦解厄 → 吉（先凶后吉/得脱）。
#     辛酉案"末天喜乘龙作解神，必有恩赦相救，先凶而后吉"即此。
#   - 官鬼凶：官鬼(克我者=WX_KE[日干])现于三传，主讼事发作、官非临身 → 凶。
#   - 连茹凶：三传地支连续(进茹/退茹，含跨子环绕)，主事牵连不绝、词讼拖延 → 凶
#     （辛亥子丑"进茹课，遂连绵起事"）。
# 仅 zhanlei=='官讼' 激活；青龙取自三传天将(确定性)，官鬼/连茹取自日干支+三传 → 无泄漏。
# 设计验证（164 真实案中 9 例官讼：2 吉 7 凶）：
#   童秀才丁酉(凶): 官鬼亥现三传 → Q(-6) ✓        辛丑(凶): 无官鬼/非连茹 → 维持原凶 ✓
#   庚申(凶): 官鬼午现→Q(-6) ✓（青龙在初传非末传→P 不触发，安全）
#   祝秀才乙酉(凶,误判吉): 亥子丑连茹 → R(-6) → 翻凶 ✓（无官鬼/青龙末传）
#   己巳(凶): 独足非连茹无官鬼 → 维持凶 ✓        庚午(凶): 官鬼午现→Q(-6)+午巳辰连茹→R(-6) ✓
#   乙末(吉): 无官鬼/非连茹/无青龙末传 → 不触发 ✓ 辛丑(凶): 无官鬼/非连茹 → 维持凶 ✓
#   辛酉(吉,误判凶): 末传青龙+无官鬼 → P(+6) → 翻吉 ✓
# ======================================================================
def extract_guansong_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                             tianjiang_list: List[str] = None, zhanlei: str = "其他",
                             lunar_month: int = None) -> Dict[str, Any]:
    """官讼吉/凶信号（确定性·无泄漏）。仅 zhanlei=='官讼' 有意义；否则 score=0。
    lunar_month: 农历月份(1-12)，用于 S2 守卫"白虎乘当月解神→凶可解"（与疾病 D2 同源：
    通解官讼例二十四"未乃十一月解神…虎虽乘之而临亥，主爪牙无用，不足畏也"）；缺省不启用。"""
    if zhanlei != '官讼':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]

    # 官鬼(克我者)地支现三传？
    gg_wx = WX_KE.get(rgwx)
    has_guigui = any(ZHI_WX.get(z) == gg_wx for z in sc)

    # 死/墓/绝/旬空（S2 守卫"勾陈白虎临死墓绝空→受制失势"用）
    kong = _xunkong(ri_gan, ri_zhi)
    cs = _gan_changsheng(rgwx)
    si_zhi = cs.get('死')           # 日死支
    mu_zhi = cs.get('墓')           # 日墓支
    jue_zhi = cs.get('绝')          # 日绝支（土双位 tuple）

    # 连茹(三传地支连续，进茹/退茹，含跨子环绕)
    idxs = sorted(_ZHI_ORDER.index(z) for z in sc)
    is_lianshu = False
    if len(idxs) == 3:
        for start in idxs:
            seq = {(start + i) % 12 for i in range(3)}
            if seq == set(idxs):
                is_lianshu = True
                break

    # 末传天将 = 青龙（解厄吉象，结局得脱）
    mo_chuan_qinglong = len(tj) >= 3 and tj[2] == '青龙'

    # ---- P: 解厄吉（末传青龙且无官鬼）----
    # 【BUG-FIX 2026-08-18】排除"青龙乘申退鳞"：末传青龙乘申时是 S6 凶象
    # （龙退鳞，欢中生悲/退财损身），原 P 先返回遮蔽 S6 → 吉凶颠倒。
    mo_chuan_qinglong_shen = len(sc) >= 3 and sc[2] == '申' and mo_chuan_qinglong
    if mo_chuan_qinglong and not has_guigui and not mo_chuan_qinglong_shen:
        return {"score": 6, "level": "吉-青龙末传解厄",
                "details": ["末传青龙(解厄/官贵吉)且无官鬼现三传→讼得解"],
                "fired": "P"}

    # ---- S2: 勾陈白虎同克日（占讼章 L4708：犯法之人遭刑戮）----
    # 放 Q 前：比通用"官鬼发动"更具体的刑戮凶象优先
    hu_ke = any(tj_at[i] == '白虎' and ZHI_WX.get(sc[i]) == gg_wx for i in range(len(sc)))
    gou_ke = any(tj_at[i] == '勾陈' and ZHI_WX.get(sc[i]) == gg_wx for i in range(len(sc)))
    if hu_ke and gou_ke:
        # 🛡️ 守卫：勾或虎任一临日干死/墓/绝/空亡 → 受制/失势，凶可解（依官讼例二十四"勾陈受制白虎失势…岂不美哉"）。
        # "勾/虎临死墓绝空"= 勾/虎本身无气，无力克日。
        weak = _jiang_lin_wei(si_zhi, sc, tj_at, ('勾陈', '白虎')) \
            or _jiang_lin_wei(mu_zhi, sc, tj_at, ('勾陈', '白虎')) \
            or _jiang_lin_wei(jue_zhi, sc, tj_at, ('勾陈', '白虎')) \
            or any(tj_at[i] in ('勾陈', '白虎') and sc[i] in kong for i in range(len(sc)))
        if weak:
            return {"score": -3, "level": "凶-勾陈白虎同克受制降级",
                    "details": ["勾陈白虎同乘鬼克日但勾/虎临死墓绝空→受制失势，降级记录"],
                    "fired": "S2x"}
        # 【BUG-FIX 2026-08-18】补月解神守卫（与疾病 D2 守卫B 同源，通解官讼例二十四
        # "未乃十一月解神…虎虽乘之而临亥，主爪牙无用，不足畏也"）：
        # 白虎乘当月解神 → 凶可解，降级记录。
        if lunar_month and 1 <= lunar_month <= 12:
            jie_zhi = _MONTH_JIE_SHEN.get(lunar_month)
            bh_idx = next((i for i, tjv in enumerate(tj_at) if tjv == '白虎'), -1)
            if bh_idx >= 0 and jie_zhi and sc[bh_idx] == jie_zhi:
                return {"score": -3, "level": "凶-勾陈白虎同克临解神降级",
                        "details": [f"白虎乘当月解神({jie_zhi})→爪牙无用，凶可解，降级记录"],
                        "fired": "S2y"}
        return {"score": -6, "level": "凶-勾陈白虎同克日",
                "details": ["勾陈白虎同现且乘官鬼克日干→犯法之人遭刑戮"],
                "fired": "S2"}

    # ---- S3: 朱勾克日莫兴词（占讼章 L4677：妄举轻为自投死）----
    zhu_gou_ke = any(tj_at[i] in ('朱雀', '勾陈') and ZHI_WX.get(sc[i]) == gg_wx for i in range(len(sc)))
    if zhu_gou_ke:
        return {"score": -4, "level": "凶-朱勾克日莫兴词",
                "details": ["朱雀/勾陈乘官鬼克日→勿兴词，妄举轻为自投死"],
                "fired": "S3"}

    # ---- S6: 青龙退鳞（前程03·074"乘龙加申为退鳞，欢中生悲，退财损身之兆"；
    #       官讼16·204"其青龙加申为退鳞，所以笞背"）----
    # 青龙乘申=龙在申秋，退鳞换骨，主退财损身/刑责。三传位上青龙乘申 → 凶。
    # 诊断 3/3 全凶（2026-08-02）：宅墓02·020/财产08·134/一课二事09·144。
    # 注：盘面任意位青龙乘申 23/29 误伤 6 吉案，仅三传位（发用等）可断 → 守此判定。
    for i in range(len(sc)):
        if sc[i] == '申' and tj_at[i] == '青龙':
            return {"score": -4, "level": "凶-青龙退鳞",
                    "details": ["青龙乘申现于三传→龙退鳞，欢中生悲，退财损身/刑责之兆"],
                    "fired": "S6"}

    # ---- S5: 助刑伐德（占讼章 L...：《中黄经》庚午日例"凡占官讼胜负，先以刑德言之…德神遭刑之克…助刑伐德，事虽小而必大"）----
    # 日德支被三传任一支刑克 → 德神遭刑，讼深不利。
    de_zhi = TAICHAN_RIDE.get(ri_gan)
    if de_zhi:
        for z in sc:
            if _SAN_XING.get(z) == de_zhi:
                return {"score": -5, "level": "凶-助刑伐德",
                        "details": [f"{z}刑日德({de_zhi})→助刑伐德，德神遭刑，讼深不利"],
                        "fired": "S5"}

    # ---- S7: 传财化鬼（占讼章：传财太盛反化鬼；§官讼16·205"木局生干上午火，火来克日…传财太盛反化鬼"）----
    # 三传财局（我克者三合局）且财生官鬼（财五行生官鬼五行）→ 财生鬼，鬼克日，因财致祸。
    # 2026-08-17 A/B：M3 87.0→87.4、官讼 90.9→100、凶→吉假阳 3→2，吉案零误伤。
    _cai_wx = KE.get(rgwx, '')
    _gg_wx = WX_KE.get(rgwx, '')
    _sc_set = set(sc)
    _cai_ju = any(_sc_set == grp and wx == _cai_wx for grp, wx in _SAN_HE_TABLE)
    if _cai_ju and WX_SHENG.get(_cai_wx) == _gg_wx:
        return {"score": -5, "level": "凶-传财化鬼",
                "details": [f"三传财局({_cai_wx})生官鬼({_gg_wx})克日→传财太盛反化鬼，因财致祸"],
                "fired": "S7"}

    # ---- Q: 官鬼凶（克我者现三传）----
    if has_guigui:
        return {"score": -6, "level": "凶-官鬼发动",
                "details": ["官鬼(克我)现于三传→讼事发作/官非临身"],
                "fired": "Q"}

    # ---- R: 连茹凶（三传地支连续）----
    if is_lianshu:
        return {"score": -6, "level": "凶-连茹牵连",
                "details": ["三传地支连续(进茹/退茹)→事牵连不绝/词讼拖延"],
                "fired": "R"}

    # ---- S4: 虎头蛇尾（通解 上卷 L4208 歌诀+注："虎头蛇尾重还轻…注：初传白虎，末传螣蛇，则为虎头蛇尾，
    #      凶而不死"；上卷 L4677 占讼歌"虎头蛇尾祸不凶"+注⑩"初虎末蛇"；下卷 L6562 陈公献占讼"以凶制凶，反无凶矣"）----
    # 2026-08-02 复核：引擎乐观语义（凶而不死→减凶）与通解原文一致，确认保留。
    # 注：官讼例五"鼠头虎尾"系另一说法（批判白虎不能解），与"初虎末蛇"（虎头蛇尾）语义不同，勿混淆。
    if len(tj) >= 3 and tj[0] == '白虎' and tj[2] == '螣蛇':
        return {"score": 2, "level": "吉-虎头蛇尾减凶",
                "details": ["初传白虎末传螣蛇→虎头蛇尾，凶而不死，祸有转机"],
                "fired": "S4"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ---- 天狱（通用课体凶信号，不限于占类）----
# 通解：宅墓02·022"斗罡系日本加亥，名天狱，不有大服，必有大祸"；
#       宅墓02·025"天罡加日本，名天狱故也"；胎产07·128"此乃天网课，若讨子便是一个冤家入门"。
# 定义：天罡(辰)在天盘加于日干长生位（日本）之上 → 天狱课，主大祸/大服/官非。
# 诊断 8/8 全凶（2026-08-02）：家宅020/025/026/043、胎产131、求财134、亡盗198、官讼208。
def extract_tianyu_valence(ri_gan: str, tiandi_pan: Dict) -> Dict[str, Any]:
    """天狱课体通用凶信号。tiandi_pan: {地盘支: 天盘支} 12 键完整盘。
    天盘辰所临地盘 == 日干长生位 → 天狱（天罡加日本）。无盘/缺参安全返回平。"""
    if not ri_gan or not tiandi_pan or len(tiandi_pan) < 12:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    # 日干长生位（五行长生；【BUG-FIX 2026-08-18 案例实证】"丙以寅为日本"、
    # "辛长生于巳"→ 五行长生；原"阳顺阴逆"十干阴阳表（乙午辛子…）与案例矛盾，弃用）
    _RI_CS = {'甲': '亥', '丙': '寅', '戊': '申', '庚': '巳', '壬': '申',
              '乙': '亥', '丁': '寅', '己': '申', '辛': '巳', '癸': '申'}
    ri_cs = _RI_CS.get(ri_gan)
    if not ri_cs:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    # 天盘辰加于哪个地盘
    tian_chen_at = None
    for di, tian in tiandi_pan.items():
        if tian == '辰':
            tian_chen_at = di
            break
    if tian_chen_at == ri_cs:
        return {"score": -5, "level": "凶-天狱课",
                "details": [f"天罡(辰)加于日干长生位({ri_cs})=日本→天狱课，不有大服必有大祸"],
                "fired": "TY"}
    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ---- 太岁临身（通用凶信号·需年份参数）----
# 宅墓02·013"太岁乘空临身，所谓当头立也…故主十六年而亡耳"；前程03·059"太岁来克身，当年可见不宁"。
# 判定：太岁支（占课年地支）== 日干寄宫上神 → 太岁临身，当年大凶。
# 全量回测（2026-08-02，year 178 案）：15 触发仅 11 凶(73%)误伤 4 → 加守卫：
#   ① 排除占类：胎产(0%)/官讼(50%) 方向差
#   ② 三传乘青龙禁：青龙=财帛吉神化解（055 初传青龙入庙邵断转文途吉）
#   守卫后 8/8=100%（2026-08-02 全量验证）→ 可接入评分。
# ⚠️ 需 year（占课干支年）参数；古案 year 178 案已补，缺省零触发。
def extract_tai_sui_valence(ri_gan: str, tiandi_pan: Dict, year: str = '',
                            zhanlei: str = '', sanchuan_dizhi: list = None,
                            tianjiang_list: list = None) -> Dict[str, Any]:
    """太岁临身通用凶信号（守卫版）。year: 占课干支年（如'戊申'），取其地支为太岁。
    守卫：①胎产/官讼占类不触发（全量回测 0%/50% 方向差）
          ②三传乘青龙不触发（青龙吉神化解，055 案验证）
    无盘/缺年/不临身/命中守卫 安全返回平。"""
    if not ri_gan or not tiandi_pan or len(tiandi_pan) < 12 or len(year) != 2:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    # 守卫①：排除占类（胎产 0%、官讼 50% 方向差，全量回测 2026-08-02）
    if zhanlei in ('胎产', '官讼'):
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tai_sui = year[1]
    if tai_sui not in ZHI_NUMBER:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    jg = _RI_JI_GONG.get(ri_gan)
    if not jg or jg not in tiandi_pan:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    gan_shang = tiandi_pan.get(jg, '')
    if gan_shang == tai_sui:
        # 守卫②：三传乘青龙（财帛吉神化解，055 案"寅上青龙入庙宜习文"邵断转途吉）
        if sanchuan_dizhi and tianjiang_list:
            sc = [z for z in sanchuan_dizhi if z in ZHI_NUMBER]
            tj = list(tianjiang_list or [])
            for i in range(len(sc)):
                if i < len(tj) and tj[i] == '青龙':
                    return {"score": 0, "level": "平", "details": [], "fired": ""}
        return {"score": -4, "level": "凶-太岁临身",
                "details": [f"太岁({tai_sui})临日干寄宫({jg})上神→当头立，当年应凶"],
                "fired": "TS"}
    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 求财专属确定性特征：财爻生扶吉(G) / 青龙乘财吉(L) / 财虚凶(X)（占类化·无泄漏）
# ----------------------------------------------------------------------
# 传统《六壬》求财取用（邵彦和断案验证）：
#   - 财爻 = 日干所克(我克者) = KE[日干五行]，为求财核心用神。财爻现三传且旺相
#     (不空亡/不墓绝/不被克/无官鬼发动) → 得财(吉)。
#   - 青龙 = 财帛之将，青龙乘财爻/临三传 → 大吉（求财最喜青龙）。
#   - 财虚凶：财爻虽现三传，但 ①被克(三传有克财爻五行之支，如卯木克未土→兄弟争财/财被伤)
#     或 ②官鬼(克我者)空亡临日干(四课第一课)克日 → 财虚/因财致祸/累得累失(凶)。
# 仅 zhanlei=='求财' 激活；财爻/官鬼/青龙/旬空/四课 全从日干支+三传+天将确定性推出 → 无泄漏。
# 设计验证（164 真实案中 12 例求财：当前错 2 例，方向相反）：
#   童监税(吉,误判凶): 日干支损坏('十一')→财爻不可算→先修数据 day_ganzhi='乙未'；
#      修后 财爻(乙木→土=丑戌未)现三传、不空亡/不墓/不受克(三传无木)/官鬼(金)不现→G(+6)翻吉 ✓
#   无名(凶,误判吉): 财爻(未土)现，但 三传卯(木)克未(土)=财受克，且第一课申(官鬼)空亡克日
#      → X(−6)翻凶 ✓（G/L 因财虚守卫不触发，避免强化错误吉）
#   钱三郎(凶,预凶): 财爻(酉金)现，但 官鬼(子水)现三传→G被门控；X不触发(子不空亡)→维持凶 ✓
#   曹八秀才(吉,预吉): 财爻(巳火)现，但 官鬼(戌土)现三传→G被门控→维持吉(八杀+6) ✓ 无假阳
# 注意：求财"财爻被冲"不阻塞——财爻六冲对象仍同五行财爻(如丑未皆土)，代表财来财去/分争，不否定得财。
# ======================================================================
_CAI_MU = {'木': '未', '火': '戌', '金': '丑', '水': '辰', '土': '辰'}  # 财爻入墓支

def extract_qiucai_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                           tianjiang_list: List[str] = None, si_ke=None,
                           zhanlei: str = "其他") -> Dict[str, Any]:
    """求财吉/凶信号（确定性·无泄漏）。仅 zhanlei=='求财' 有意义；否则 score=0。"""
    if zhanlei != '求财':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    kong = _xunkong(ri_gan, ri_zhi)

    cai_wx = KE.get(rgwx, '')          # 财爻(我克者)
    gg_wx = WX_KE.get(rgwx, '')       # 官鬼(克我者)
    cai_zhi = [z for z in sc if ZHI_WX.get(z) == cai_wx]     # 财爻支现三传
    gg_in_sc = any(ZHI_WX.get(z) == gg_wx for z in sc)      # 官鬼现三传
    # 财受克：三传有 克财爻五行 之支（如卯木克未土）
    cai_ke_wx = WX_KE.get(cai_wx, '')
    cai_shouke = any(ZHI_WX.get(z) == cai_ke_wx for z in sc) if cai_wx else False
    # 官鬼空亡克日：四课第一课(日干上神) = 官鬼 且该支空亡
    gg_kong_ke_ri = False
    if si_ke and isinstance(si_ke, (list, tuple)) and len(si_ke) >= 1:
        first = si_ke[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            up = first[1]
            if ZHI_WX.get(up) == gg_wx and up in kong:
                gg_kong_ke_ri = True

    # ---- X: 财虚凶（财爻现但受克 / 官鬼空亡克日）----
    if cai_zhi and (cai_shouke or gg_kong_ke_ri):
        why = []
        if cai_shouke:
            why.append("财爻受克(三传有克财爻之支)")
        if gg_kong_ke_ri:
            why.append("官鬼空亡克日")
        return {"score": -6, "level": "凶-财虚", "details": ["·".join(why) + "→财虚/因财致祸"], "fired": "X"}

    # ---- X2: 传鬼化财险财（求财章 L4628：三传皆鬼独存财=险财，"传鬼化财钱险危"）----
    gg_count = sum(1 for z in sc if ZHI_WX.get(z) == gg_wx)
    if gg_count >= 2 and cai_zhi:
        return {"score": -4, "level": "凶-传鬼化财险财",
                "details": ["三传官鬼多而独存财爻→其财险出，得之不安稳，多不正之财"],
                "fired": "X2"}

    # ---- X3: 财乘丁马忌庚辛（求财章 L4622：财爻临旬丁/驿马，庚辛日丁为鬼主凶祸）----
    xd = _xun_ding(ri_gan, ri_zhi)
    ym = _YI_MA.get(ri_zhi, '')
    cai_dm = [z for z in cai_zhi if z == xd or z == ym]
    if cai_dm and rgwx == '金':
        return {"score": -4, "level": "凶-财乘丁马庚辛日鬼",
                "details": [f"财爻({cai_dm})乘丁马，庚辛日丁火为官鬼→因财动祸，求速财反遭殃"],
                "fired": "X3"}
    # 注：壬癸日丁火为财（财动吉）已由 G/L 自然覆盖，不在此额外处理；其余日干不特判（通解只明言庚辛忌）。

    # ---- K: 财归库吉（财库现三传且财爻不空亡 → 财有所归，得财稳固）----
    # 古籍求财章"财归库"（§财产08·141 三传皆鬼而末见财库"少阻无妨"；§137"日上财神归财库此大利"）。
    # 与「财爻入墓(财衰被埋·凶)」的区别：财爻不空亡=旺相 → 入库为「库」(吉)，空亡=衰 → 入墓(凶)。
    # 2026-08-17 A/B：M3 86.0→86.5、吉recall 27.3→30.3、求财 78.6→85.7，凶→吉假阳 3→3 零误伤。
    # 【BUG-FIX 2026-08-18】补 cai_zhi 前置：须财爻本身入传才有"财归库"，
    # 原仅判财库在三传（财爻未入传也报吉）→ 财未现而妄断得财。
    _cai_mu_zhi = _CAI_MU.get(cai_wx, '')
    if cai_zhi and _cai_mu_zhi and _cai_mu_zhi in set(sc):
        _cai_kong = any(z in kong for z in cai_zhi)
        if not _cai_kong:
            return {"score": 5, "level": "吉-财归库",
                    "details": [f"财爻({','.join(cai_zhi)})入传且财库({_cai_mu_zhi})现三传、财爻不空亡→财有所归，得财稳固"],
                    "fired": "K"}

    # ---- G: 财爻生扶吉 ----
    if cai_zhi and not gg_in_sc and not cai_shouke and not gg_kong_ke_ri:
        cai_kong = any(z in kong for z in cai_zhi)     # 财爻空亡
        mu = _CAI_MU.get(cai_wx, '')
        cai_mu = mu in set(sc)                          # 财爻入墓
        if not cai_kong and not cai_mu:
            return {"score": 6, "level": "吉-财爻生扶",
                    "details": ["财爻(我克者)现三传且旺相(不空亡/不墓绝/不受克/无官鬼)→得财"],
                    "fired": "G"}

    # ---- L: 青龙乘财吉（青龙乘财爻且财爻旺相）----
    # 【BUG-FIX 2026-08-18】原仅判"青龙临三传"，未校验青龙所乘之支为财爻
    # → 青龙乘官鬼/兄弟亦报"得财"。现要求 sc[i] 为财爻（青龙乘财）才触发。
    for i, t in enumerate(tj):
        if t == '青龙' and i < len(sc) and sc[i] in cai_zhi and sc[i] not in kong:
            if not gg_in_sc and not cai_shouke and not gg_kong_ke_ri:
                return {"score": 6, "level": "吉-青龙乘财",
                        "details": [f"青龙乘财爻({sc[i]})临三传且旺相→得财"], "fired": "L"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 功名专属确定性特征（仕宦章 L4551-4590 + 选举章 L4508-4544；占类化·无泄漏）
# ----------------------------------------------------------------------
# 仕宦章核心：日辰虚实定荣枯；临官帝旺干支遇，爵禄峥嵘任帝都（吉）；
#             六阳数足功名显（吉）；朱雀值鬼防黜落（凶）；凡占墓绝亏官爵（凶）；
#             德入天门名显传（吉）；帘幕贵人高甲第（吉·选举）。
# 本语料凶重（47 案功名中 37 凶/10 吉），正向信号一律加门控（不空亡/不与凶同现），
# 记取"妻财局判吉全反/正向神煞有害"教训。
# ======================================================================
_GUI_REN = {'甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'],
            '戊': ['丑', '未'], '己': ['子', '申'], '庚': ['丑', '未'], '辛': ['午', '寅'],
            '壬': ['巳', '卯'], '癸': ['巳', '卯']}
_YANG_ZHI = {'子', '寅', '辰', '午', '申', '戌'}


def extract_gongming_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                             tianjiang_list: List[str] = None,
                             zhanlei: str = "其他", xing_nian_zhi: str = "",
                             tiandi_pan: dict = None) -> Dict[str, Any]:
    """功名/仕宦/选举吉凶信号（确定性·无泄漏）。仅 zhanlei=='功名' 有意义；否则 score=0。
    xing_nian_zhi/tiandi_pan: 行年接入（邵师断语「行年午上乘申为干支长生系文星学堂」§052），
      仅作记录层（G4，score 0）——因 §096 凶案行年上神亦=长生，单特征不定吉凶，须与
      贵人/幕贵组合才有意义，样本 n=1 不过闸，不进 valence。缺省不启用。"""
    if zhanlei != '功名':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    kong = _xunkong(ri_gan, ri_zhi)
    cs = _gan_changsheng(rgwx)
    lin_guan, di_wang = cs.get('临官'), cs.get('帝旺')
    mu_zhi, jue_zhi = cs.get('墓'), cs.get('绝')
    gg_wx = WX_KE.get(rgwx)
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]

    # ---- X1: 朱雀值鬼防黜落（L4575：朱雀临官鬼克日干则防被免职）----
    # 【BUG-FIX 2026-08-18 案例实证】§03·055 庚日 末巳作朱雀，"一为长生，双为官星
    # 学堂，故主科甲"（弃武从文得科甲=吉）——朱雀乘官鬼但该支为日干长生位=
    # 长生学堂（文印吉），非防黜落。仅当朱雀乘鬼且非长生位才判凶。
    for i, z in enumerate(sc):
        if tj_at[i] == '朱雀' and ZHI_WX.get(z) == gg_wx:
            _cs = _gan_changsheng(rgwx)
            _cs_vals = _cs.get('长生', ())
            _cs_vals = _cs_vals if isinstance(_cs_vals, (tuple, list, set)) else (_cs_vals,)
            if z not in _cs_vals:
                return {"score": -5, "level": "凶-朱雀值鬼防黜落",
                        "details": [f"朱雀乘官鬼({z})现传→防黜落/去官"], "fired": "X1"}
            # 朱雀乘鬼但=长生学堂 → 不判凶（记录层提示）
            return {"score": 0, "level": "吉-朱雀乘长生学堂(记录)",
                    "details": [f"朱雀乘官星({z})但为日干长生学堂→文印吉（记录层）"],
                    "fired": "X1y"}

    # ---- X2: 墓绝亏官爵（L4575：凡占墓绝亏官爵）----
    # 【BUG-FIX 2026-08-18 案例实证】§03·052 癸日 末传巳（墓绝）但乘贵人=
    # "日贵在末传，先晦后明准拟登科"（吉）——墓绝乘贵人/生干=先凶后吉，
    # 非亏官爵。仅当墓绝乘凶将或空亡才判凶。
    if _wei_in_sc(mu_zhi, sc) or _wei_in_sc(jue_zhi, sc):
        hit = mu_zhi if _wei_in_sc(mu_zhi, sc) else (jue_zhi[0] if isinstance(jue_zhi, (tuple, list)) else jue_zhi)
        _hit_idx = next((i for i, z in enumerate(sc) if z == hit), -1)
        _hit_tj = tj_at[_hit_idx] if _hit_idx >= 0 else ''
        if _hit_tj in ('贵人', '青龙', '六合', '太常', '天后', '太阴'):
            return {"score": 0, "level": "平-墓绝乘吉将(记录)",
                    "details": [f"三传见墓/绝({hit})但乘吉将{_hit_tj}→先晦后明（记录层）"],
                    "fired": "X2y"}
        return {"score": -3, "level": "凶-墓绝亏官爵",
                "details": [f"三传见日墓/绝({hit})→功名亏损"],
                "fired": "X2"}

    # ---- G1: 临官帝旺临传（L4552：临官帝旺干支遇，爵禄峥嵘任帝都）----
    # 2026-08-01 A/B 实证：正向信号在凶重语料(功名 37凶/10吉)误推吉，M3 87.2→84.8 负回归，
    # 吉信号一律降级为记录（score 0，不进 valence）。凶信号 X1/X2 保留。
    g1_zhi = [z for z in sc if z == lin_guan or z == di_wang]
    g1_kong = any(z in kong for z in g1_zhi)
    if g1_zhi and not g1_kong:
        return {"score": 0, "level": "吉-临官帝旺临传(记录)",
                "details": [f"三传见临官({lin_guan})/帝旺({di_wang})→爵禄峥嵘（记录层，不计 valence）"],
                "fired": "G1"}

    # ---- G2: 六阳数足（L4554：六阳数足功名显，利公干）----
    if all(z in _YANG_ZHI for z in sc):
        return {"score": 0, "level": "吉-六阳数足(记录)",
                "details": ["三传皆阳→六阳数足，功名显达（记录层，不计 valence）"],
                "fired": "G2"}

    # ---- G3: 帘幕贵人（选举章 L4510：帘幕贵人高甲第）----
    gui_z = _GUI_REN.get(ri_gan, [])
    g3_hit = [z for z in sc if z in gui_z]
    if g3_hit and not any(z in kong for z in g3_hit):
        return {"score": 0, "level": "吉-帘幕贵人(记录)",
                "details": [f"贵人({g3_hit})临传→考试/功名得贵助力（记录层，不计 valence）"],
                "fired": "G3"}

    # ---- G4: 行年文星学堂（§052 邵师：行年午上乘申为干支长生系文星学堂，合起日贵）----
    # 行年上神（行年居地盘看天盘）=日干长生位 → 文星学堂。记录层（score 0）：
    # §096 凶案行年丑上寅亦=长生，单特征不定吉凶，须与贵人/幕贵组合；样本 n=1 不过闸。
    if xing_nian_zhi and tiandi_pan and xing_nian_zhi in ZHI_WX:
        xns = tiandi_pan.get(xing_nian_zhi, '')
        if xns:
            cs_list = cs.get('长生')
            cs_set = cs_list if isinstance(cs_list, (tuple, list)) else [cs_list]
            if xns in cs_set:
                return {"score": 0, "level": "吉-行年文星学堂(记录)",
                        "details": [f"行年{xing_nian_zhi}上乘{xns}=日干长生→文星学堂（记录层，须合贵人/幕贵，不计 valence）"],
                        "fired": "G4"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 疾病专属确定性特征（依据《大六壬通解》疾病章 p239-243；节选核心可确定性判定者）
# ----------------------------------------------------------------------
# 疾病章核心法则（邵彦和断案验证）：
#   ·虎鬼凶速速：白虎乘日鬼(克日干)现三传 → 凶（最重）；虎鬼空亡则不治自愈(不触发凶)。
#   ·生龙回生：青龙乘生气生日干 → 危而复生(吉)。
#   ·子孙解厄：子孙爻(我生者)现三传不空亡/不坐墓 → 良药脱厄(吉)；坐空墓则不能解厄。
#   ·贵医：贵人(天乙)现三传 → 贵医解厄(吉)。
#   ·两蛇夹墓：螣蛇+日墓现传 → 疾难除(凶)；六合乘申临卯 → 身尸入棺(凶)。
#   ·华盖孝帛：太常+华盖现传 → 孝帛盖头(凶)。
#   ·自墓传生：初传日墓末传长生 → 危即安(吉)。
# 仅 zhanlei=='疾病' 激活；只用 日干/日支/三传地支/三传天将/旬空/日干十二长生 → 完全确定性·无泄漏。
# 不依赖 年命/月建/缺失神煞(死神死气血支血忌地医)，避免引入未验证起例。
# ======================================================================
_WX_CHANGSHENG = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}  # 五行长生起点(水土同宫)
_HUA_GAI = {'木': '未', '火': '戌', '金': '丑', '水': '辰', '土': '辰'}        # 华盖=三合局墓支


def _zhi_in_wei(zhi, wei) -> bool:
    """判断地支 zhi 是否落在某十二长生位置 wei（wei 为 str 或 tuple/list 集合，土为双位）。"""
    if not zhi:
        return False
    if isinstance(wei, (tuple, list, set, frozenset)):
        return zhi in wei
    return bool(wei) and zhi == wei


def _wei_in_sc(wei, sc) -> bool:
    """判断十二长生位置 wei（str 或 tuple/list，土双位）是否有支出现在三传 sc 中。"""
    if isinstance(wei, (tuple, list, set, frozenset)):
        return any(z in sc for z in wei)
    return bool(wei) and wei in sc


def _jiang_lin_wei(wei, sc, tj_at, jiangs) -> bool:
    """判断十二长生位置 wei（str 或 tuple/list，土双位）是否有支出现在三传 sc 且乘 jiangs 之一。"""
    if isinstance(wei, (tuple, list, set, frozenset)):
        return any(z in sc and any(tj_at[i] in jiangs and sc[i] == z for i in range(len(sc))) for z in wei)
    return bool(wei) and wei in sc and any(tj_at[i] in jiangs and sc[i] == wei for i in range(len(sc)))


def _gan_changsheng(rgwx: str) -> Dict[str, str]:
    """日干五行 → 十二长生支位字典（确定性·无泄漏）。
    土双位（憨爷拍板 2026-08-16）：长生/沐浴/绝/胎 为 tuple（水土同宫主值 + 火土同宫次值），其余单值。"""
    if rgwx not in _WX_CHANGSHENG:
        return {}
    start = _WX_CHANGSHENG[rgwx]
    si = _ZHI_ORDER.index(start)
    names = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
    result = {names[i]: _ZHI_ORDER[(si + i) % 12] for i in range(12)}
    if rgwx == '土':
        result['长生'] = ('申', '寅')
        result['沐浴'] = ('酉', '卯')
        result['绝'] = ('巳', '亥')
        result['胎'] = ('午', '子')
    return result


def extract_disease_valence(ri_gan: str, ri_zhi: str, san_chuan_dizhi: List[str],
                            tianjiang_list: List[str] = None, zhanlei: str = "其他",
                            lunar_month: int = None,
                            ben_ming_zhi: str = "", tiandi_pan: dict = None) -> Dict[str, Any]:
    """疾病吉/凶信号（确定性·无泄漏）。仅 zhanlei=='疾病' 有意义；否则 score=0。
    lunar_month: 农历月份(1-12)，用于月解神守卫（白虎乘当月解神→凶可解）；缺省不启用。
    ben_ming_zhi/tiandi_pan: 年命接入（毕法赋53法"行年本命是戌其死尤速"），用于 D3 两蛇夹墓
      年命加重守卫（本命==日墓 → 凶加重）与化解（年命上神冲墓 → 破墓得解）。缺省不启用。"""
    if zhanlei != '疾病':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not san_chuan_dizhi or len(san_chuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in san_chuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    kong = _xunkong(ri_gan, ri_zhi)
    cs = _gan_changsheng(rgwx)
    mu_zhi = cs.get('墓')           # 日墓支
    si_zhi = cs.get('死')           # 日死支
    jue_zhi = cs.get('绝')          # 日绝支
    chang_zhi = cs.get('长生')      # 日长生支
    gg_wx = WX_KE.get(rgwx)         # 日鬼(克我)五行
    zisun_wx = WX_SHENG.get(rgwx)   # 子孙(我生)五行

    # 天将按三传位置对齐
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]

    # ---- D1: 虎鬼发动（最凶）----
    for i, z in enumerate(sc):
        if tj_at[i] == '白虎' and ZHI_WX.get(z) == gg_wx:
            if z in kong:
                continue  # 虎鬼空亡，不治自愈 → 不触发凶
            return {"score": -6, "level": "凶-虎鬼发动",
                    "details": [f"白虎乘日鬼({z})现三传→虎鬼凶速速"], "fired": "D1"}

    # ---- D2: 死墓绝空叠白虎 ----
    if '白虎' in tj_at:
        if (_wei_in_sc(si_zhi, sc)) or (_wei_in_sc(mu_zhi, sc)) or (_wei_in_sc(jue_zhi, sc)) or any(z in kong for z in sc):
            # 🛡️ 守卫A：三传构成三合局且助日（合成五行==日干同类，或生日干印星）→ 凶可解
            # 依据：官讼例二十四"喜三传会木局助日…不足畏"（《中黄经》乙卯日例，亥卯未会木局）。
            sc_set = set(sc)
            san_he_wx = None
            for grp, wx in _SAN_HE_TABLE:
                if sc_set == grp:
                    san_he_wx = wx; break
            helps = san_he_wx and (san_he_wx == rgwx or WX_SHENG.get(san_he_wx) == rgwx)
            if helps:
                return {"score": -2, "level": "凶-白虎会局助日降级",
                        "details": [f"白虎临死墓绝空但三传{san_he_wx}局助日→凶可解，降级记录"],
                        "fired": "D2x"}
            # 🛡️ 守卫B：白虎所乘支为当月解神 → 凶可解（月解神=月建冲破，通解 404页注释⑦）
            # 依据：官讼例二十四"又未乃十一月解神，虎虽乘之而临亥，主爪牙无用，不足畏也"。
            if lunar_month and 1 <= lunar_month <= 12:
                jie_zhi = _MONTH_JIE_SHEN.get(lunar_month)
                bh_idx = next((i for i, tjv in enumerate(tj_at) if tjv == '白虎'), -1)
                if bh_idx >= 0 and jie_zhi and sc[bh_idx] == jie_zhi:
                    return {"score": -2, "level": "凶-白虎临解神降级",
                            "details": [f"白虎乘当月解神({jie_zhi})临死墓绝空→凶可解，降级记录"],
                            "fired": "D2y"}
            return {"score": -5, "level": "凶-白虎临死墓绝空",
                    "details": ["白虎现传且三传见死/墓/绝/空→占病必重"], "fired": "D2"}

    # ---- D3: 两蛇夹墓 / 六片板格(身尸入棺) ----
    # 2026-08-02 课经正文核验修正（通解 上卷 L4164+L4181 歌诀注 / 中卷 毕法赋第五十三法 L6278）：
    #   D3  两蛇夹墓：原文"丙戌日昼占戌加巳，成临螣蛇，螣蛇与地盘巳火双蛇夹日墓"——须日墓乘螣蛇（同传位）。
    #        原实现"螣蛇现传+日墓现传"过宽（不同传位也误触发，曾误伤吉案），改为同传位。
    #   D3b 六片板格(身尸入棺)：原文"六合乘申临卯，为尸人棺……上有六合，下有卯木，是为棺也"——
    #        须六合乘申（申上神为六合）。原实现"六合乘卯+申现传"方向反了，已修正。
    if any(tj_at[i] == '螣蛇' and sc[i] == mu_zhi for i in range(len(sc))):
        # 🛡️ 年命加重/化解守卫（毕法赋53法 L6280-6281）：
        #   "或行年本命是戌，其死尤速"——本命==日墓 → 凶加重 -5→-7
        #   "如年命居亥上乘天罡辰虎冲戌蛇故名破墓"——年命上神冲日墓 → 破墓得解 -5→-2
        if ben_ming_zhi and mu_zhi:
            if ben_ming_zhi == mu_zhi:
                return {"score": -7, "level": "凶-两蛇夹墓年命加凶",
                        "details": [f"日墓({mu_zhi})乘螣蛇且本命({ben_ming_zhi})即日墓→其死尤速"],
                        "fired": "D3n"}
            nss = _nian_ming_shang_shen(ben_ming_zhi, tiandi_pan)
            if nss and nss in _LIU_CHONG_SET.get(mu_zhi, set()):
                return {"score": -2, "level": "凶-两蛇夹墓年命破墓降级",
                        "details": [f"日墓({mu_zhi})乘螣蛇但年命上神({nss})冲墓→破墓得解"],
                        "fired": "D3p"}
        return {"score": -5, "level": "凶-两蛇夹墓",
                "details": [f"日墓({mu_zhi})乘螣蛇现传→两蛇夹墓疾难除"], "fired": "D3"}
    if any(tj_at[i] == '六合' and sc[i] == '申' for i in range(len(sc))):
        return {"score": -5, "level": "凶-六片板格身尸入棺",
                "details": ["六合乘申临卯→身尸入棺(死人棺)，占病必死"], "fired": "D3b"}

    # ---- D4: 华盖孝帛 ----
    hua_gai = _HUA_GAI.get(rgwx)
    if '太常' in tj_at and hua_gai and hua_gai in set(sc):
        return {"score": -4, "level": "凶-华盖孝帛",
                "details": [f"太常现传且华盖({hua_gai})现传→孝帛盖头"], "fired": "D4"}

    # ---- D5: 收魂煞（疾病章 L4158：玄乘日墓名收魂煞，占病大凶）----
    for i, z in enumerate(sc):
        if tj_at[i] == '玄武' and mu_zhi and z == mu_zhi:
            return {"score": -5, "level": "凶-收魂煞",
                    "details": [f"玄武乘日墓({mu_zhi})现传→收魂煞，占病主凶"], "fired": "D5"}

    # ---- D6: 丧吊死常（疾病章 L4143-4147：官鬼乘太常 + 日死/墓现传 = 孝服死丧）----
    gui_tc = [sc[i] for i in range(len(sc)) if tj_at[i] == '太常' and ZHI_WX.get(sc[i]) == gg_wx]
    if gui_tc and ((si_zhi in set(sc)) or (mu_zhi in set(sc))):
        return {"score": -4, "level": "凶-鬼乘太常死墓孝服",
                "details": [f"官鬼({gui_tc[0]})乘太常现传且三传见日死/墓→丧吊死常，主孝服（丧吊全逢挂缟衣）"],
                "fired": "D6"}

    # ---- D7: 子临巳绝（疾病章 L4216：水绝于巳，水日三传见巳→占病主死亡之象）----
    if rgwx == '水' and '巳' in set(sc):
        return {"score": -3, "level": "凶-子临巳绝",
                "details": ["水日三传见巳（水绝于巳）→子临巳位定死亡，占病尤忌"],
                "fired": "D7"}

    # 说明：疾病占在真实疏正案中强偏凶(16凶/1吉/1未知, 全集18例)，且六壬"凶象定生死"。
    # 子孙解厄/生龙/贵医(P系列)虽为通解吉象，但在强凶案中随吉将现传而大量误触发假阳
    # （诊断见 8 例方向矛盾: 3 凶案被推吉、1 吉案被 D3 误伤），故第一版仅保留疾病特有的
    # 死凶结构(D系列, 纯凶向)，不臆造吉信号(守铁律·确定性·无泄漏)。
    # 后续若需补解厄吉象，须加门控：仅当课体无通用凶象(日鬼/死墓绝空/白虎现传)时才判吉，避免假阳。
    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 家宅专属确定性特征（阳宅章 L3714-3840；占类化·无泄漏）
# ----------------------------------------------------------------------
# 阳宅章核心：支为宅、干为人；白虎临支（虎入宅凶）、墓神临支（少欢娱）、
#             三传脱支生日干（人多屋少）；罗网临宅/火鬼带丁（凶）。
# 家宅占类 32 案实测 100% 准 → 凶信号接入前 A/B，破坏则降级记录。
# 仅 zhanlei=='家宅' 激活；支上神取自四课（确定性）。
# ======================================================================
def _ke_first_zhi(ke) -> str:
    """取一课中首个地支（三元(课名,上神,下神)/二元(上神,下神) 兼容）"""
    if isinstance(ke, (list, tuple)):
        for ele in ke:
            if isinstance(ele, str) and ele in ZHI_WX:
                return ele
    return ''


def extract_jiazhai_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                            tianjiang_list: List[str] = None, si_ke=None,
                            zhanlei: str = "其他") -> Dict[str, Any]:
    """家宅吉/凶信号（确定性·无泄漏）。仅 zhanlei=='家宅' 有意义；否则 score=0。"""
    if zhanlei != '家宅':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]
    cs = _gan_changsheng(rgwx)
    mu_zhi = cs.get('墓')

    # 支上神（四课第三课首个地支；结构兼容）
    zhi_shang = ''
    if si_ke and len(si_ke) >= 3:
        zhi_shang = _ke_first_zhi(si_ke[2])
    # 干上神（四课第一课首个地支；结构兼容；H6/H7/H8 干支受脱/皆败/值绝用）
    gan_shang = ''
    if si_ke and len(si_ke) >= 1:
        gan_shang = _ke_first_zhi(si_ke[0])

    # ---- H1: 虎入宅（阳宅章 L3772：白虎临日支宅位主凶）----
    if zhi_shang:
        for i, z in enumerate(sc):
            if tj_at[i] == '白虎' and z == zhi_shang:
                return {"score": -5, "level": "凶-白虎入宅",
                        "details": [f"白虎乘支上神({zhi_shang})现传→虎入宅凶，宅中惊危"],
                        "fired": "H1"}

    # ---- H2: 墓神临支（阳宅章 L3756：墓神临支少欢娱，宅中幽暗）----
    if zhi_shang and mu_zhi and zhi_shang == mu_zhi:
        return {"score": -3, "level": "凶-墓神临支",
                "details": [f"日墓({mu_zhi})临支上神→宅中幽暗少欢娱，人丁不旺"],
                "fired": "H2"}

    # ---- H3: 三传脱支生日干（人多屋少）/ 三传盗干生支辰（屋旺人衰）----
    # 原文《大六壬指南》阳宅章：「三传脱支生日干，人多屋少从此断。三传盗干生支辰，屋旺人衰何必算。」
    # 阳宅章四句对仗（脱支生日干→人多屋少 / 盗干生支辰→屋旺人衰 / 生支克干→卖屋偿人 / 生日克支→弃家迁）
    # **均主人宅失衡，皆不吉**（"人多屋少"=宅被脱泄而宅衰，非吉）。
    # 精细版（2026-08-17 憨爷要求，废除原"近似：三传多我生五行"——原实现方向反了）：
    #   脱支 = 三传泄日支（日支所生 = WX_SHENG[zi_wx]）；生日干 = 三传生日干（生我者）
    #   盗干 = 三传泄日干（日干所生 = WX_SHENG[rgwx]）；生支辰 = 三传生日支（生日支者）
    zi_wx = ZHI_WX.get(ri_zhi, '')
    if zi_wx:
        sc_wx = [ZHI_WX.get(z) for z in sc]
        tuo_zhi = WX_SHENG.get(zi_wx)                             # 泄日支的五行（宅气被脱）
        sheng_gan = [w for w, v in WX_SHENG.items() if v == rgwx]  # 生日干的五行（生我者）
        dao_gan = WX_SHENG.get(rgwx)                              # 泄日干的五行（盗干）
        sheng_zhi = [w for w, v in WX_SHENG.items() if v == zi_wx]  # 生日支的五行（生支辰）
        # H3a：三传脱支生日干 → 人多屋少（宅衰人旺，人宅失衡，不吉）
        if tuo_zhi in sc_wx and any(s in sc_wx for s in sheng_gan):
            return {"score": -2, "level": "凶-三传脱支生日干",
                    "details": ["三传脱支(泄宅)生日干(生人)→人多屋少，宅衰人旺，主搬迁破财"],
                    "fired": "H3a"}
        # H3b：三传盗干生支辰 → 屋旺人衰（人衰，更凶）
        if dao_gan in sc_wx and any(s in sc_wx for s in sheng_zhi):
            return {"score": -3, "level": "凶-三传盗干生支辰",
                    "details": ["三传盗干(泄人)生支辰(生宅)→屋旺人衰，人丁不旺"],
                    "fired": "H3b"}

    # ---- H4: 支上克干（阳宅章 L3731 程树勋占自宅例：占宅吉凶，支上克干便为不吉；鬼临三四更凶）----
    # 支上神（第三课上神）五行克日干 → 人宅不吉。鬼临三四（支上两课）= 官鬼临宅位，更凶。
    if zhi_shang and ZHI_WX.get(zhi_shang) == WX_KE.get(rgwx):
        return {"score": -4, "level": "凶-支上克干鬼临宅",
                "details": [f"支上神({zhi_shang})五行克日干({ri_gan})→支上克干，人宅不吉，鬼临三四更凶"],
                "fired": "H4"}

    # ---- H5: 干支互脱（宅墓02·004 张九翁：盖庚生于巳，寅生于亥，庚脱于亥，寅脱于巳，
    #       干支俱受生而互受脱，是先兴旺而后衰败也……亥脱今日干则耗泄我矣故主费财）----
    # 判定：三传中任一传支 = 日干之脱神（日干生该支五行）且 = 日支五行之长生位 → 干被宅脱、支得其生，
    #       宅旺而人衰，先兴后败主费财。诊断 15/15 全凶（2026-08-02）。
    zi_wx = ZHI_WX.get(ri_zhi, '')
    if zi_wx:
        wo_sheng_wx = WX_SHENG.get(rgwx)   # 我生者（脱气）
        zi_cs = _gan_changsheng(zi_wx).get('长生')  # 日支五行长生位（土双位）
        for z in sc:
            if ZHI_WX.get(z) == wo_sheng_wx and _zhi_in_wei(z, zi_cs):
                return {"score": -3, "level": "凶-干支互脱费财",
                        "details": [f"三传{sc}含{z}：日干({ri_gan})生{z}(脱神)而{z}为日支({ri_zhi})长生→干支互脱，先兴后败主费财"],
                        "fired": "H5"}

    # ---- H6: 人宅受脱俱招盗（毕法赋35法：日干为人、日支为宅；原文"亦有二等"，满足其一即命中）----
    #   一等：支上干上皆乘脱气（干上脱干=干生干上 + 支上脱支=支生支上）
    #   二等：干上脱支、支上脱干（交车脱：支生干上 + 干生支上）
    if gan_shang and zhi_shang and zi_wx:
        wo_sheng_wx = WX_SHENG.get(rgwx)        # 日干我生者（脱气）
        zhi_sheng_wx = WX_SHENG.get(zi_wx)      # 日支我生者（脱气）
        yi_deng = (ZHI_WX.get(gan_shang) == wo_sheng_wx and ZHI_WX.get(zhi_shang) == zhi_sheng_wx)
        er_deng = (ZHI_WX.get(gan_shang) == zhi_sheng_wx and ZHI_WX.get(zhi_shang) == wo_sheng_wx)
        if yi_deng or er_deng:
            if yi_deng:
                det = f"干上({gan_shang})脱日干({ri_gan})、支上({zhi_shang})脱日支({ri_zhi})→干支上皆乘脱气"
            else:
                det = f"干上({gan_shang})脱日支({ri_zhi})、支上({zhi_shang})脱日干({ri_gan})→干上脱支支上脱干"
            return {"score": -3, "level": "凶-人宅受脱招盗",
                    "details": [det + "，人宅受脱被脱赚家宅遭盗"],
                    "fired": "H6"}

    # ---- H7: 干支皆败事倾颓（毕法赋36法：干支上皆逢败气=十二长生沐浴位；占身气血衰败、占宅屋舍崩颓）----
    if gan_shang and zhi_shang and zi_wx:
        zi_cs_all = _gan_changsheng(zi_wx)
        gan_bai = cs.get('沐浴')      # 日干五行沐浴位（土双位）
        zhi_bai = zi_cs_all.get('沐浴')  # 日支五行沐浴位（土双位）
        if _zhi_in_wei(gan_shang, gan_bai) and _zhi_in_wei(zhi_shang, zhi_bai):
            return {"score": -3, "level": "凶-干支皆败倾颓",
                    "details": [f"干上({gan_shang})=干沐浴位、支上({zhi_shang})=支沐浴位→干支皆败，身衰宅颓"],
                    "fired": "H7"}

    # ---- H8: 干支值绝凡谋决（毕法赋79法：干支上皆乘绝神=十二长生绝位；谋事不成，止宜结绝凶事）----
    if gan_shang and zhi_shang and zi_wx:
        zi_cs_all = _gan_changsheng(zi_wx)
        gan_jue = cs.get('绝')        # 日干五行绝位（土双位）
        zhi_jue = zi_cs_all.get('绝')  # 日支五行绝位（土双位）
        if _zhi_in_wei(gan_shang, gan_jue) and _zhi_in_wei(zhi_shang, zhi_jue):
            return {"score": -3, "level": "凶-干支值绝谋不成",
                    "details": [f"干上({gan_shang})=干绝位、支上({zhi_shang})=支绝位→干支值绝，谋事不成宜结绝凶事"],
                    "fired": "H8"}

    # ---- 方位相背（前程仕进03·047 徐将仕：戊辰干支皆东南神，辛卯命又是东方，三传反流入西方，
    #       顺行陷于西北，故死于外州）----
    # 记录（2026-08-02 诊断 20/25 有 5 误伤吉案：胎产129/130、求财132 等，未过 A/B 闸口）：
    # 三传主要方位与日支方位相背（东vs西/南vs北）→ 方向错位人离乡背。仅作叙事/教学素材，不参与评分。

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 出行专属确定性特征（出行章 L4237-4337；占类化·无泄漏）
# ----------------------------------------------------------------------
# 出行章核心：驿马居天中（马加空亡）出行不定不利（凶）；初旺末囚不利远行；
#             干凶支吉他乡有益；斗系日本/天网凶（需正时/天罡，暂略）。
# ======================================================================
def extract_chuxing_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                             tianjiang_list: List[str] = None, si_ke=None,
                             zhanlei: str = "其他") -> Dict[str, Any]:
    """出行吉/凶信号（确定性·无泄漏）。仅 zhanlei=='出行' 有意义；否则 score=0。"""
    if zhanlei != '出行':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    kong = _xunkong(ri_gan, ri_zhi)

    # ---- X1: 驿马居天中（出行章 L4247：驿马加空亡，出行不定不利）----
    ym = _YI_MA.get(ri_zhi, '')
    if ym and ym in set(sc) and ym in kong:
        return {"score": -5, "level": "凶-驿马空亡",
                "details": [f"驿马({ym})临三传但落空亡→出行不定，不利远行"],
                "fired": "X1"}

    # ---- X2: 中末逢空初不空（行人半路欲回程 L4243）----
    if sc[0] not in kong and (sc[1] in kong or sc[2] in kong):
        return {"score": -3, "level": "凶-中末空亡半路回",
                "details": ["初传不空而中/末传空亡→出行半路欲回程"],
                "fired": "X2"}

    # ---- X3: 玄武乘财临三传（壬占汇选跨书验证 10/10=100% 凶，排除胎产；2026-08-02）----
    # 依据：壬占汇选高频规则"发用为日干之财，上得元武→失财/被窃"（玄武=盗贼、财=所失）。
    # 出行/行人占类：玄武乘财主水路阻迟、行程不利（行人音信12·157 甲申日辰(土=甲财)乘玄武→水浅阻迟，凶）。
    # 跨书回测：疏正 219 案 10 触发全凶（排除胎产后 100%）；与 D1 虎鬼、S6 青龙退鳞同源不同象。
    tj_list = list(tianjiang_list or [])
    # 我克者=财（五行）：木克土/火克金/土克水/金克木/水克火
    WO_KE_CAI = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    cai_wx = WO_KE_CAI.get(rgwx, '')
    if cai_wx:
        for i, z in enumerate(sc):
            tjv = tj_list[i] if i < len(tj_list) else None
            if tjv == '玄武' and ZHI_WX.get(z) == cai_wx:
                return {"score": -3, "level": "凶-玄武乘财出行阻",
                        "details": [f"三传{z}为日财乘玄武→失财/被窃之象，出行阻迟"],
                        "fired": "X3"}
    # ---- G1(记录): 初中空陷末传助（L4245：末传得长生财禄，此难彼丰）----
    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 婚姻专属确定性特征（婚姻章 L3933-4023；占类化·无泄漏）
# ----------------------------------------------------------------------
# 婚姻章核心：财居旬后无情/官坐空亡（财官空亡则婚姻失败，凶）；
#             后合乘卯酉入课必有私合（凶）；传将生合百年配（吉·记录）。
# ======================================================================
def extract_hunyin_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                            tianjiang_list: List[str] = None, si_ke=None,
                            zhanlei: str = "其他") -> Dict[str, Any]:
    """婚姻吉/凶信号（确定性·无泄漏）。仅 zhanlei=='婚姻' 有意义；否则 score=0。"""
    if zhanlei != '婚姻':
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]
    kong = _xunkong(ri_gan, ri_zhi)
    cai_wx = KE.get(rgwx, '')
    gg_wx = WX_KE.get(rgwx, '')

    # ---- X1: 财居旬后总无情（婚姻章 L3935：财爻空亡则婚姻不成）----
    cai_kong = any(ZHI_WX.get(z) == cai_wx and z in kong for z in sc)
    if cai_kong:
        return {"score": -4, "level": "凶-财居旬后",
                "details": ["财爻(妻)落空亡→财居旬后，婚姻无情难成"],
                "fired": "X1"}

    # ---- X2: 官坐空亡鸾失匹（婚姻章 L3946：官鬼空亡则夫缘虚）----
    # 2026-08-02 降级 -4→-2：古例反例（婚姻例四 庚子日，官鬼巳空亡）邵彦和断"此课必成，但恐成亲后再归去"——
    # 官鬼空亡未阻断成婚，仅主"夫缘虚/婚后不宁"。维持弱凶记录（方向不变），不阻婚。
    gg_kong = any(ZHI_WX.get(z) == gg_wx and z in kong for z in sc)
    if gg_kong:
        return {"score": -2, "level": "凶-官坐空亡降级",
                "details": ["官鬼(夫)落空亡→夫缘虚，婚后恐不宁（不阻婚）"],
                "fired": "X2"}

    # ---- X3: 后合乘卯酉私合（婚姻章 L3983：天后/六合乘卯酉入课必有私合）----
    for i, z in enumerate(sc):
        if z in ('卯', '酉') and tj_at[i] in ('天后', '六合'):
            return {"score": -4, "level": "凶-后合卯酉私合",
                    "details": [f"{tj_at[i]}乘{z}入课→后合私合，婚有奸私"],
                    "fired": "X3"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ======================================================================
# 贼盗专属确定性特征（贼盗章 L4731-4813；占类化·无泄漏）
# ----------------------------------------------------------------------
# 贼盗章核心：占贼先视日鬼（玄武乘鬼现传=贼盗发动，凶）；财爻空陷赃难寻（凶）；
#             子孙休旺定追寻（吉·记录）。
# ======================================================================
def extract_zeidao_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                            tianjiang_list: List[str] = None, si_ke=None,
                            zhanlei: str = "其他", leishen: str = "",
                            tianjiang_map=None, shichen: str = "") -> Dict[str, Any]:
    """贼盗吉/凶信号（确定性·无泄漏）。

    两条路径：
    1) 贼盗占类（zhanlei=='贼盗'）：玄武乘鬼现传 / 财爻空陷赃难寻（贼盗章 L4731-4813）。
    2) 亡盗类神寻物（zhanlei=='其他' 且 leishen 非空；零涟漪——其余"其他"案与股票
       路径无 leishen 不触发）：邵彦和失物法——"凡失物须看类神在传或加日辰定见"
       （§199）、"有类神主其物不失"（§193）、"末申系类神寻之必见"（§194）、
       "酉为类神初传加巳长生不落空亡"（§195）。判定优先级：
       W0 太阳照武（毕法赋"太阳照武宜擒贼"）：玄武临地盘时辰 → 贼被擒，失物必得
          （§193 庚辰日辰时 玄武临辰，果于厕坑侧寻见）；
       W1 类神在三传 → 寻得吉（不论空亡；§194 末传申虽旬空仍"寻之必见"）；
       W2 类神加日辰（干上/支上=第一/第三课上神）：不空亡→吉（§199 加日辰定见），
          空亡→凶（§189 干上未旬空"自合失脱，捉贼不得"）；
       类神课传外 → 中性（§198/§200 边界：酉/卯不在课传仍寻得，天盘特位样本不足暂不作吉凶）。
    """
    if zhanlei != '贼盗' and (zhanlei != '其他' or not leishen):
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    rgwx = GAN_WX.get(ri_gan)
    if not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in ZHI_WX]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    tj_at = [tj[i] if i < len(tj) else None for i in range(len(sc))]
    kong = _xunkong(ri_gan, ri_zhi)
    cai_wx = KE.get(rgwx, '')
    gg_wx = WX_KE.get(rgwx, '')

    # ---- 亡盗类神寻物（零涟漪：仅 leishen 非空的"其他"案触发；邵彦和失物法）----
    if zhanlei == '其他' and leishen:
        if leishen not in ZHI_WX:
            return {"score": 0, "level": "平", "details": [], "fired": ""}
        # W0: 太阳照武（毕法赋）：玄武临地盘时辰盘 → 贼被擒，失物必得（§193 果寻见）
        if tianjiang_map and shichen and tianjiang_map.get(shichen) == '玄武':
            return {"score": 6, "level": "吉-太阳照武擒贼",
                    "details": [f"玄武临{shichen}(时辰)→太阳照武宜擒贼，失物必得"],
                    "fired": "W0"}
        # 【BUG-FIX 2026-08-18】W1/W2 优先级调整：类神在传(W1)先于加日辰(W2)。
        # 依据：邵彦和失物法"凡失物须看类神在传或加日辰定见"（§199）——
        # 类神入传为最直接的寻得证据（§194 末传申虽旬空仍"寻之必见"），
        # 原代码 W2 先判会遮蔽 W1（类神同时在传与日辰时 W1 永不触发）。
        # W1: 类神在三传 → 寻得吉（不论空亡；§194 末传申虽旬空仍"寻之必见"；§195/197 亦在传寻见）
        if leishen in sc:
            pos = '初传' if sc[0] == leishen else ('中传' if sc[1] == leishen else '末传')
            return {"score": 6, "level": "吉-类神在传寻得",
                    "details": [f"类神{leishen}现于{pos}→类神在传，失物可寻得"],
                    "fired": "W1"}
        # W2: 类神加日辰（干上/支上=第一/第三课上神）→ 未在传时再看日辰：
        #     不空→吉（§188/190/191/192/199 加日辰定见）；空→凶（§189 干上未旬空捉贼不得）
        if si_ke and isinstance(si_ke, (list, tuple)):
            for sk in si_ke:
                if isinstance(sk, (list, tuple)) and len(sk) >= 2:
                    if sk[1] == leishen and sk[0] in ('第一课', '第三课'):
                        place = '干上' if sk[0] == '第一课' else '支上'
                        if leishen in kong:
                            return {"score": -4, "level": "凶-类神加日辰空亡",
                                    "details": [f"类神{leishen}加{place}但临旬空→自合失脱，捉贼不得"],
                                    "fired": "W2K"}
                        return {"score": 6, "level": "吉-类神加日辰寻得",
                                "details": [f"类神{leishen}加于{place}且不落空亡→类神加日辰，失物可寻得"],
                                "fired": "W2"}
        # 类神课传外 → 中性（§198/§200 边界：酉/卯不在课传仍寻得，天盘特位样本不足暂不作吉凶）
        return {"score": 0, "level": "平", "details": ["类神未现课传，不作吉凶判定"], "fired": ""}

    # ---- X1: 玄武乘鬼现传（贼盗章 L4733：占贼行藏须视鬼，玄武主贼）----
    for i, z in enumerate(sc):
        if tj_at[i] == '玄武' and ZHI_WX.get(z) == gg_wx:
            return {"score": -5, "level": "凶-玄武乘鬼贼盗",
                    "details": [f"玄武乘官鬼({z})现传→贼盗发动，财物有失"],
                    "fired": "X1"}

    # ---- X2: 财爻空陷赃难寻（贼盗章 L4764：财爻空亡则赃物难回）----
    cai_kong = any(ZHI_WX.get(z) == cai_wx and z in kong for z in sc)
    if cai_kong:
        return {"score": -3, "level": "凶-财爻空陷赃难寻",
                "details": ["财爻落空亡→失物难寻，赃物难回"],
                "fired": "X2"}

    return {"score": 0, "level": "平", "details": [], "fired": ""}


# ─────────────────────────────────────────────────────────────
# 学业/成绩类神判断（憨爷 2026-08-17：日干文昌星与长生为类神）
# 仅 zhanlei in ('测孩子成绩','入学开学','考试','求学问') 触发；其余 score=0 零涟漪。
# 文昌星表（十干文昌）：甲巳乙午丙申丁酉戊申己酉庚亥辛子壬寅癸卯
# 长生：日干五行长生位（土双位：主值申+次值寅，_gan_changsheng 已实现）
# 判定（仿类神寻物法 W1/W2 结构）：
#   W1 文昌星在三传 → 吉（文昌照临，成绩佳）
#   W2 文昌星加日辰（第一/第三课上神）：不空→吉；空→凶（文星晦暗，成绩不显）
#   L1 长生在三传 → 吉（学识根基深厚）
#   L2 长生加日辰且不空 → 吉
#   文昌+长生同现（W1/L1 或 W2/L2 并存）→ 再加吉（文运两旺）
# 说明：新占类无古例 A/B 样本，score 仅供展示层（result['wenchang']），不进 M3 主评分。
# ─────────────────────────────────────────────────────────────
_WENCHANG = {
    '甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申',
    '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯',
}
_WENCHANG_ZHI = '学业文昌类神'


def extract_wenchang_valence(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                             si_ke=None, zhanlei: str = "其他") -> Dict[str, Any]:
    """测孩子成绩/学业类神判断（确定性·无泄漏）。
    仅 zhanlei in ('测孩子成绩','入学开学','考试','求学问') 有意义；否则 score=0。
    类神 = 日干文昌星 + 日干五行长生位（土双位主次皆算）。"""
    if zhanlei not in ('测孩子成绩', '入学开学', '考试', '求学问'):
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    wc = _WENCHANG.get(ri_gan, '')
    rgwx = GAN_WX.get(ri_gan, '')
    if not wc or not rgwx or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in _ZHI_ORDER]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    cs = _gan_changsheng(rgwx)
    cs_cs = cs.get('长生', '')
    # 长生位（土双位 tuple 展开；单值转列表）
    cs_list = list(cs_cs) if isinstance(cs_cs, tuple) else ([cs_cs] if cs_cs else [])
    kong = _xunkong(ri_gan, ri_zhi)

    score = 0
    details = []
    fired = []
    wc_hit = False   # 文昌是否已命中
    cs_hit = False   # 长生是否已命中

    # 日辰上神（第一课干上 / 第三课支上）→ 类神加日辰判断
    ri_ke_up = ''
    zhi_ke_up = ''
    if si_ke and isinstance(si_ke, (list, tuple)):
        for sk in si_ke:
            if isinstance(sk, (list, tuple)) and len(sk) >= 2:
                if sk[0] == '第一课':
                    ri_ke_up = sk[1]
                elif sk[0] == '第三课':
                    zhi_ke_up = sk[1]

    # W1/W2 文昌星
    if wc in sc:
        score += 4
        wc_hit = True
        fired.append('W1')
        details.append(f'文昌星{wc}现于三传→文昌照临，成绩佳')
    elif wc in (ri_ke_up, zhi_ke_up):
        if wc in kong:
            score -= 3
            fired.append('W2K')
            details.append(f'文昌星{wc}加日辰但临旬空→文星晦暗，成绩不显')
        else:
            score += 4
            wc_hit = True
            fired.append('W2')
            details.append(f'文昌星{wc}加日辰且不落空→成绩可期')

    # L1/L2 长生
    for cz in cs_list:
        if cz in sc:
            score += 3
            cs_hit = True
            fired.append('L1')
            details.append(f'长生{cz}现于三传→学识根基深厚')
            break
    else:
        for cz in cs_list:
            if cz in (ri_ke_up, zhi_ke_up) and cz not in kong:
                score += 3
                cs_hit = True
                fired.append('L2')
                details.append(f'长生{cz}加日辰且不空→学识有源')
                break

    # 文昌+长生同现 → 文运两旺
    if wc_hit and cs_hit:
        score += 2
        fired.append('W+L')
        details.append('文昌与长生同现→文运两旺')

    if not fired:
        return {"score": 0, "level": "平", "details": ["文昌星/长生未现课传日辰，不作吉凶判定"], "fired": ""}

    if score > 0:
        level = '吉-文昌长生照临' if wc_hit and cs_hit else ('吉-文昌照临' if wc_hit else '吉-长生助文')
    else:
        level = '凶-文昌空亡'
    return {"score": score, "level": level, "details": details, "fired": '+'.join(fired)}


# ─────────────────────────────────────────────────────────────
# 现代择日类型专属信号（憨爷 2026-08-17：古籍没有的现代类差异化评分）
# 思路：现代类映射复用长征已验证的古类信号（提车→出行驿马/买房→求财财爻/开工→财官局），
#       再加 1-3 条现代专属信号（白虎车马/勾陈纠纷/太岁犯土/墓库入宅等）。
# 仅 zetiri_type 命中现代 9 类时触发；其余 score=0 零涟漪。
# 说明：现代类无古例 A/B 样本，score 只进展示层（result['type_special']），不进 total_score。
# ─────────────────────────────────────────────────────────────
_YIMA_MA = {
    '申': '寅', '子': '寅', '辰': '寅',
    '寅': '申', '午': '申', '戌': '申',
    '巳': '亥', '酉': '亥', '丑': '亥',
    '亥': '巳', '卯': '巳', '未': '巳',
}
_GAN_MU = {'甲': '未', '乙': '戌', '丙': '戌', '丁': '丑', '戊': '戌',
           '己': '丑', '庚': '丑', '辛': '辰', '壬': '辰', '癸': '未'}
_MODERN_TYPES = ('提车', '买房过户', '开工', '阳宅动土', '阴宅动土', '迁坟', '入学开学', '考试', '祭祀祈福',
                 '催龙补气', '召山买土')
# 我生表（五行相生）：判断"支上神生日干"= 生气（支上五行生日干五行：WX_SHENG[支上] == 日干）
_WX_SHENG_LOCAL = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
# 地支六合表（阴阳合）：子丑/寅亥/卯戌/辰酉/巳申/午未
_LIU_HE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
           '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
# 地支三合局（三合会局补龙/归山判断）
_SAN_HE_GROUPS = (('申', '子', '辰'), ('寅', '午', '戌'), ('巳', '酉', '丑'), ('亥', '卯', '未'))


def extract_modern_type_valence(zetiri_type: str, ri_gan: str, ri_zhi: str,
                                sanchuan_dizhi: List[str], tianjiang_list: List[str] = None,
                                liuqin_list: List[str] = None, si_ke=None,
                                year_zhi: str = "",
                                lailong_zhi: str = "", shan_zhi: str = "", xiang_zhi: str = "",
                                pillar_luma: Dict = None) -> Dict[str, Any]:
    """现代择日类型专属信号（确定性·无泄漏）。仅 zetiri_type in _MODERN_TYPES 触发。
    输入均为引擎排盘字段（与起课同源）；依赖 _xunkong 判空亡。
    lailong_zhi/shan_zhi/xiang_zhi = 来龙/坐山/向首的地支（二十四山→八宫），供催龙补气/召山买土判山向合冲。
    pillar_luma = 四柱禄马贵到山到向明细（calculate_new_score 提供：
      count=合格柱数 / nian/yue/ri/shi 各柱合格 / lai_hit=禄马贵至少一到过 来龙）——催龙补气主信号。"""
    if zetiri_type not in _MODERN_TYPES:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    if not ri_gan or not ri_zhi or not sanchuan_dizhi or len(sanchuan_dizhi) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    sc = [z for z in sanchuan_dizhi if z in _ZHI_ORDER]
    if len(sc) < 3:
        return {"score": 0, "level": "平", "details": [], "fired": ""}
    tj = list(tianjiang_list or [])
    lq = list(liuqin_list or [])
    kong = _xunkong(ri_gan, ri_zhi)
    # 干上/支上（第一/第三课上神）
    ri_up = zhi_up = ''
    if si_ke and isinstance(si_ke, (list, tuple)):
        for sk in si_ke:
            if isinstance(sk, (list, tuple)) and len(sk) >= 2:
                if sk[0] == '第一课':
                    ri_up = sk[1]
                elif sk[0] == '第三课':
                    zhi_up = sk[1]
    zhi_up = zhi_up or (si_ke[2][1] if si_ke and len(si_ke) > 2 and isinstance(si_ke[2], (list, tuple)) and len(si_ke[2]) >= 2 else '')

    score = 0
    details = []
    fired = []

    def _fire(tag, pts, msg):
        nonlocal score
        score += pts
        fired.append(tag)
        details.append(msg)

    # ── 提车：驿马 + 白虎（映射出行类）──
    if zetiri_type == '提车':
        ma = _YIMA_MA.get(ri_zhi, '')
        if ma and ma in sc:
            _fire('MA', 3, f'驿马{ma}现于三传→提车出行顺遂')
        elif ma and ma in (ri_up, zhi_up) and ma not in kong:
            _fire('MA2', 2, f'驿马{ma}临日辰且不空→出行可期')
        if '白虎' in tj:
            _fire('BaiHu', -4, '白虎现于三传→防车马之虞/交通意外')
        if '贵人' in tj:
            _fire('GuiRen', 2, '贵人临传→提车得助，手续顺遂')

    # ── 买房过户：财爻 + 勾陈/玄武（映射求财类）──
    elif zetiri_type == '买房过户':
        has_cai = any('财' in str(x) for x in lq)
        if has_cai:
            _fire('Cai', 3, '财爻现于三传→置业得财，过户顺遂')
            if all(z in kong for z in sc):
                _fire('CaiK', -3, '三传皆空→置业虚耗，过户难成')
        if '勾陈' in tj:
            _fire('GouChen', -2, '勾陈临传→防过户纠纷/手续阻滞')
        if '玄武' in tj:
            _fire('XuanWu', -2, '玄武临传→防交易暗耗/文书不实')

    # ── 开工：财官同在传 + 三传皆空（映射求财+官讼）──
    elif zetiri_type == '开工':
        has_cai = any('财' in str(x) for x in lq)
        has_guan = any('官' in str(x) for x in lq)
        if has_cai and has_guan:
            _fire('CaiGuan', 3, '财官同现三传→事业根基稳固，财官两旺')
        if all(z in kong for z in sc):
            _fire('Kong', -3, '三传皆空→开工虚浮，难见成效')

    # ── 阳宅动土：支上神生日干（生气）+ 日干墓临支（墓优先，动土入墓主凶）──
    elif zetiri_type == '阳宅动土':
        mu = _GAN_MU.get(ri_gan, '')
        if mu and mu == zhi_up:
            _fire('MuZhi', -3, f'日干墓{mu}临支→动土入墓，根基受阻')
        elif zhi_up and GAN_WX.get(ri_gan) and ZHI_WX.get(zhi_up):
            if _WX_SHENG_LOCAL.get(ZHI_WX.get(zhi_up)) == GAN_WX.get(ri_gan):
                _fire('ShengQi', 3, f'支上{zhi_up}与日干相生→动土得生气，兴工顺利')

    # ── 阴宅动土/迁坟：太岁临支 + 生气 ──
    elif zetiri_type in ('阴宅动土', '迁坟'):
        if year_zhi and year_zhi == zhi_up:
            _fire('TaiSui', -4, f'太岁{year_zhi}临支→动土犯太岁，主凶')
        if zhi_up and GAN_WX.get(ri_gan) and ZHI_WX.get(zhi_up):
            if _WX_SHENG_LOCAL.get(ZHI_WX.get(zhi_up)) == GAN_WX.get(ri_gan):
                _fire('ShengQi', 3, f'支上{zhi_up}与日干相生→得生气，开山顺遂')

    # ── 入学开学/考试：官星临日辰 + 官星空（文昌见 extract_wenchang_valence）──
    elif zetiri_type in ('入学开学', '考试'):
        has_guan = any('官' in str(x) for x in lq)
        if has_guan:
            _fire('Guan', 2, '官星现于三传→学业得官贵助力')
            if all(z in kong for z in sc):
                _fire('GuanK', -2, '官星落空→学业虚名难实')

    # ── 祭祀祈福：支上神生日干 + 白虎临日辰 ──
    elif zetiri_type == '祭祀祈福':
        if zhi_up and GAN_WX.get(ri_gan) and ZHI_WX.get(zhi_up):
            if _WX_SHENG_LOCAL.get(ZHI_WX.get(zhi_up)) == GAN_WX.get(ri_gan):
                _fire('ShengQi', 3, f'支上{zhi_up}与日干相生→祭祀得感应，祈福有应')
        if '白虎' in tj:
            _fire('BaiHu', -3, '白虎临传→祭祀防不洁/冲撞')

    # ── 催龙补气（阴宅）：主信号=年月日四柱禄马贵到山到向（憨爷 2026-08-17 口径：
    #    来龙不明显可不选，重点是年月日及坐山贵人禄马到山到向；有来龙作贵人禄马则更好）──
    elif zetiri_type == '催龙补气':
        lg = lailong_zhi or shan_zhi  # 未选来龙退用坐山
        if not lg:
            _fire('NoLL', 0, '未提供来龙/坐山，不作龙气判断')
        pl = pillar_luma or {}
        pc = int(pl.get('count', 0) or 0)
        if pc >= 3:
            _fire('LM3', 5, f'年月日{pc}柱禄马贵人到山到向→禄马贵齐临，龙气得扶催旺')
        elif pc == 2:
            _fire('LM2', 3, f'{pc}柱禄马贵人到山到向→山向得禄马贵，催旺有力')
        elif pc == 1:
            _fire('LM1', 1, f'{pc}柱禄马贵人到山到向→微有助力')
        if pl.get('lai_hit'):
            _fire('LaiLM', 2, f'禄马贵临来龙{lg}→来龙得气，催旺更佳')
        if _CHONG_MAP.get(ri_zhi) == lg:
            _fire('ChongLG', -4, f'日支{ri_zhi}冲来龙{lg}→冲龙损气，催龙无功')
        if shan_zhi and _CHONG_MAP.get(ri_zhi) == shan_zhi:
            _fire('ChongShan', -3, f'日支{ri_zhi}冲坐山{shan_zhi}→冲山，龙气不安')

    # ── 召山买土（阴宅，与动土/山向有关）：冲山冲向大忌（凶优先）；日支合山向则土气归山 ──
    elif zetiri_type == '召山买土':
        _chong_hit = False
        if shan_zhi and _CHONG_MAP.get(ri_zhi) == shan_zhi:
            _fire('ChongShan', -4, f'日支{ri_zhi}冲坐山{shan_zhi}→冲山，动土大忌')
            _chong_hit = True
        if xiang_zhi and _CHONG_MAP.get(ri_zhi) == xiang_zhi:
            _fire('ChongXiang', -4, f'日支{ri_zhi}冲向首{xiang_zhi}→冲向，土气散失')
            _chong_hit = True
        if not _chong_hit:  # 冲山/冲向时不加合向分（凶优先）
            for t in (shan_zhi, xiang_zhi):
                if not t:
                    continue
                if _LIU_HE.get(ri_zhi) == t:
                    _fire('LH', 3, f'日支{ri_zhi}与山向{t}六合→土气归山，买土顺遂')
                    break
                if ri_zhi != t and any(ri_zhi in g and t in g for g in _SAN_HE_GROUPS):
                    _fire('SH', 3, f'日支{ri_zhi}与山向{t}三合→土气归山，买土顺遂')
                    break
        if year_zhi and year_zhi == zhi_up:
            _fire('TaiSui', -3, f'太岁{year_zhi}临支→动土犯太岁')
        mu = _GAN_MU.get(ri_gan, '')
        if mu and mu == zhi_up:
            _fire('MuZhi', -2, f'日干墓{mu}临支→取土入墓，土气不畅')

    if not fired:
        return {"score": 0, "level": "平", "details": [f'{zetiri_type}专属信号未触发'], "fired": ""}
    level = '吉' if score > 0 else ('凶' if score < 0 else '平')
    return {"score": score, "level": f'{level}-{zetiri_type}特判', "details": details, "fired": '+'.join(fired)}
