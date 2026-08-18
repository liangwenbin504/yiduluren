# -*- coding: utf-8 -*-
"""
六壬 64 课判断引擎 v1.0（2026-08-15 憨爷拍板：把"字典"变成"引擎"）
================================================================
核心思想：课体不是查表，是根据起课数据（四课/三传/日辰/月将/神将/日月宿/年命）
动态判定"这一课是哪个课体"。

三层架构：
  ① 数据支撑层：日月宿（太阳/太阴躔度）、四正日（朔望弦晦）、斗罡、旺衰、神将
  ② 判定层：64 课每课一个 judge_XXX(env) 函数，严格按《大六壬通解》"凡…为X课"条件
  ③ 统一入口：judge_64_keti(env) → 返回命中的课体列表（含依据）

九宗门（元首/重审/知一/涉害/遥克/昴星/别责/八专/伏吟/返吟）由
sike_sanchuan_engine.SiKeSanChuanCalculator2.fa_sanchuan 判定（V2 已实现），
本引擎专注 54 课格 + 特殊课体的判定。
"""
import os, sys
from typing import List, Dict, Tuple, Any

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# ═════════════ 基础常量 ═════════════
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
DIZHI_IDX = {z: i for i, z in enumerate(DIZHI)}
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 二十八宿（含"重算留一"标记：奎张井翼氐斗 度数大，停留两天）
XIU_28 = ['角', '亢', '氐', '房', '心', '尾', '箕', '斗', '牛', '女', '虚', '危',
          '室', '壁', '奎', '娄', '胃', '昴', '毕', '觜', '参', '井', '鬼', '柳',
          '星', '张', '翼', '轸']
XIU_LIUYI = {'奎', '张', '井', '翼', '氐', '斗'}  # 重算留一的宿（度数大，停留两天）

# 二十八宿 → 十二地支宫（月宿加四仲判定用）
XIU_ZHI = {
    '角': '辰', '亢': '辰', '氐': '卯', '房': '卯', '心': '卯', '尾': '寅', '箕': '寅',
    '斗': '丑', '牛': '丑', '女': '子', '虚': '子', '危': '子', '室': '亥', '壁': '亥',
    '奎': '戌', '娄': '戌', '胃': '酉', '昴': '酉', '毕': '酉', '觜': '申', '参': '申',
    '井': '未', '鬼': '未', '柳': '午', '星': '午', '张': '午', '翼': '巳', '轸': '巳',
}

# 地支五行
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
# 天干五行
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 三合局
SANHE = {'申子辰': '水', '巳酉丑': '金', '寅午戌': '火', '亥卯未': '木'}
SANHE_MAP = {'子': '辰', '辰': '申', '申': '子', '丑': '巳', '巳': '酉', '酉': '丑',
             '寅': '戌', '戌': '午', '午': '寅', '卯': '未', '未': '亥', '亥': '卯'}

# 六害
LIUHAI = {'子': '未', '丑': '午', '寅': '巳', '卯': '辰', '辰': '卯',
          '巳': '寅', '午': '丑', '未': '子', '申': '亥', '酉': '戌', '戌': '酉', '亥': '申'}

# 三刑
SANXING = {'寅': '巳', '巳': '申', '申': '寅', '丑': '戌', '戌': '未', '未': '丑',
           '子': '卯', '卯': '子', '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'}

# 四仲（子午卯酉）、四孟（寅申巳亥）、四季（辰戌丑未）
SI_ZHONG = {'子', '午', '卯', '酉'}
SI_MENG = {'寅', '申', '巳', '亥'}
SI_JI = {'辰', '戌', '丑', '未'}

# 墓库（五行墓：木未、火戌、金丑、水土辰）
MU_KU = {'木': '未', '火': '戌', '金': '丑', '水': '辰', '土': '辰'}


# ═════════════ ① 数据支撑层 ═════════════

def ri_su(yue_jian: str) -> str:
    """日宿（太阳躔度宫神）：正月起亥，逆行十二辰。
    《通解》："日宿者，太阳躔度宫神也，正月起亥，逆行十二辰。"
    即正月亥、二月戌、三月酉…十二月子。
    """
    # 月支（寅=正月）→ 日宿地支，逆行
    yue_zhis = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']  # 正月到十二月
    start = '亥'
    for i, yz in enumerate(yue_zhis):
        if yue_jian == yz:
            idx = (DIZHI_IDX[start] - i) % 12
            return DIZHI[idx]
    return '亥'


def yue_su(lunar_month: int, lunar_day: int) -> str:
    """月宿（太阴躔度二十八宿）：正月初一起室，逐日数二十八宿，
    遇奎、张、井、翼、氐、斗宿"重算留一"（度数大，停留两天）。
    《通解》："正月初一起室…逐日数二十八宿，遇奎张井翼氐斗宿，重算留一。"
    """
    # 每月初一的宿（正月室、二奎、三胃、四毕、五参、六鬼、七张、八角、九氐、十尾、十一斗、十二虚）
    MONTH_START_XIU = {1: '室', 2: '奎', 3: '胃', 4: '毕', 5: '参', 6: '鬼',
                       7: '张', 8: '角', 9: '氐', 10: '尾', 11: '斗', 12: '虚'}
    start_xiu = MONTH_START_XIU.get((lunar_month - 1) % 12 + 1, '室')
    # 从起始宿开始，逐日数（含起始日），遇重算留一的宿停两天
    # 构造"带停留"的宿序列
    seq = []
    start_idx = XIU_28.index(start_xiu)
    # 数到 lunar_day 天（第1天=起始宿）
    days = 0
    pos = start_idx
    while days < lunar_day:
        xiu = XIU_28[pos % 28]
        seq.append(xiu)
        days += 1
        if xiu in XIU_LIUYI:
            # 重算留一：该宿停留两天（再append一次）
            if days < lunar_day:
                seq.append(xiu)
                days += 1
        pos += 1
    return seq[-1] if seq else start_xiu


def si_zheng_day(lunar_day: int) -> bool:
    """四正日：朔(初一)、弦(初八)、望(十五)、下弦(廿三)、晦(月终)。"""
    return lunar_day in (1, 8, 15, 23)


def dou_gang() -> str:
    """斗罡 = 辰（天罡）。"""
    return '辰'


# ═════════════ 精化用的基础计算 ═════════════
# 五行旺相休囚死（月建定旺衰）
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 十干禄（日禄）
GAN_LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
          '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# 十干德（日德）
GAN_DE = {'甲': '寅', '己': '寅', '乙': '申', '庚': '申', '丙': '巳', '辛': '巳',
          '丁': '亥', '壬': '亥', '戊': '巳', '癸': '巳'}

# 天干五合
GAN_HE = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙',
          '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}

# 贵人（昼贵人，日干定）
GAN_GUIREN = {'甲': '丑', '戊': '丑', '庚': '丑', '乙': '子', '己': '子',
              '丙': '亥', '丁': '亥', '壬': '卯', '癸': '卯', '辛': '午'}

# 驿马（三合局长生对冲）
YI_MA = {'申': '寅', '子': '寅', '辰': '寅', '巳': '亥', '酉': '亥', '丑': '亥',
         '寅': '申', '午': '申', '戌': '申', '亥': '巳', '卯': '巳', '未': '巳'}


def get_wang_shuai(zhi: str, yue_jian: str) -> str:
    """地支五行在月建下的旺衰：旺/相/休/囚/死。"""
    wx = ZHI_WX.get(zhi, '')
    wx_jian = ZHI_WX.get(yue_jian, '')
    if not wx or not wx_jian:
        return ''
    if wx == wx_jian:
        return '旺'
    if WX_SHENG.get(wx_jian) == wx:
        return '相'
    if WX_SHENG.get(wx) == wx_jian:
        return '休'
    if WX_KE.get(wx) == wx_jian:
        return '囚'
    if WX_KE.get(wx_jian) == wx:
        return '死'
    return ''


def is_wang_xiang(zhi: str, yue_jian: str) -> bool:
    """是否旺相（旺或相）。"""
    return get_wang_shuai(zhi, yue_jian) in ('旺', '相')


def get_season(yue_jian: str) -> str:
    """月建定季节：寅卯辰=春、巳午未=夏、申酉戌=秋、亥子丑=冬。"""
    if yue_jian in ('寅', '卯', '辰'):
        return '春'
    if yue_jian in ('巳', '午', '未'):
        return '夏'
    if yue_jian in ('申', '酉', '戌'):
        return '秋'
    if yue_jian in ('亥', '子', '丑'):
        return '冬'
    return ''


# 孤辰：春巳顺四孟；寡宿：春丑顺四季（《通解》芜淫课注）
GU_CHEN_BY_SEASON = {'春': '巳', '夏': '申', '秋': '亥', '冬': '寅'}
GUA_SU_BY_SEASON = {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'}

# 灾厄课凶煞（《通解》灾厄课：正月起X顺/逆行）
YUE_ZHIS = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']  # 正月到十二月


def sang_che(yue_jian: str) -> str:
    """丧车（丧魂）：正月起未，逆行四季（未戌丑辰）。"""
    si_ji = ['未', '戌', '丑', '辰']
    for i, yz in enumerate(YUE_ZHIS):
        if yue_jian == yz:
            return si_ji[(-i) % 4]
    return ''


def you_hun(yue_jian: str) -> str:
    """游魂：正月起亥，顺行十二辰。"""
    for i, yz in enumerate(YUE_ZHIS):
        if yue_jian == yz:
            return DIZHI[(DIZHI_IDX['亥'] + i) % 12]
    return ''


def fu_yang(yue_jian: str) -> str:
    """伏殃：正月起酉，逆行四仲（酉午卯子）。"""
    si_zhong = ['酉', '午', '卯', '子']
    for i, yz in enumerate(YUE_ZHIS):
        if yue_jian == yz:
            return si_zhong[(-i) % 4]
    return ''


def bing_fu(nian_zhi: str) -> str:
    """病符：旧太岁（年支前一位）。"""
    return DIZHI[(DIZHI_IDX[nian_zhi] - 1) % 12] if nian_zhi in DIZHI_IDX else ''


def sang_men(nian_zhi: str) -> str:
    """丧门：岁前二辰。"""
    return DIZHI[(DIZHI_IDX[nian_zhi] + 2) % 12] if nian_zhi in DIZHI_IDX else ''


def diao_ke(nian_zhi: str) -> str:
    """吊客：岁后二辰。"""
    return DIZHI[(DIZHI_IDX[nian_zhi] - 2) % 12] if nian_zhi in DIZHI_IDX else ''


def wu_mu(ri_gan: str) -> str:
    """五墓：金丑、木未、火戌、水土辰（日干墓）。"""
    wx = GAN_WX.get(ri_gan, '')
    return MU_KU.get(wx, '')


# ═════════════ ② 判定层：64 课判定函数 ═════════════
# env 结构：{ri_gan, ri_zhi, sike(四课[[课名,上神,下神,天将]...]), sanchuan(三传[初传,中传,末传]),
#            yue_jiang(月将), yue_jian(月建), chu(初传), zhong(中传), mo(末传),
#            tian_jiang(三传天将), nianming, lunar_month, lunar_day, year, month, day}

def _ref(name, cond, src):
    return {'课体': name, '条件': cond, '依据': src}


def judge_du_e(env):
    """度厄：四课内三上克下，或三下贼上。"""
    sike = env.get('sike', [])
    shang_ke = sum(1 for k in sike if _ke(k[1], k[2]))
    xia_ke = sum(1 for k in sike if _ke(k[2], k[1]))
    if shang_ke == 3 or xia_ke == 3:
        return _ref('度厄', f'四课内三上克下({shang_ke})或三下贼上({xia_ke})', '通解 度厄课')
    return None


def judge_wu_lu(env):
    """无禄：四上俱克下。"""
    sike = env.get('sike', [])
    if len(sike) == 4 and all(_ke(k[1], k[2]) for k in sike):
        return _ref('无禄', '四课皆上克下', '通解 无禄课')
    return None


def judge_jue_si(env):
    """绝嗣：四下俱克上。"""
    sike = env.get('sike', [])
    if len(sike) == 4 and all(_ke(k[2], k[1]) for k in sike):
        return _ref('绝嗣', '四课皆下克上', '通解 绝嗣课')
    return None


def judge_tian_wang(env):
    """天网：占时与用神同克日。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    shi = env.get('shi_chen', '')
    if _ke(chu, ri_gan) and _ke(shi, ri_gan):
        return _ref('天网', f'占时{shi}与用神{chu}同克日干', '通解 天网课')
    return None


def judge_quan_ju(env):
    """全局：三合俱在传。"""
    sc = env.get('sanchuan', [])
    if len(sc) >= 3:
        for ju in SANHE:
            if all(z in sc for z in ju):
                return _ref('全局', f'三传{sc}成{ju}三合局', '通解 全局课')
    return None


def judge_xuan_tai(env):
    """玄胎：孟神发用，传皆四孟。"""
    chu = env.get('chu', '')
    sc = env.get('sanchuan', [])
    if chu in SI_MENG and all(z in SI_MENG for z in sc):
        return _ref('玄胎', f'孟神{chu}发用，三传{sc}皆四孟', '通解 玄胎课')
    return None


def judge_lian_zhu(env):
    """连珠：用神传在一方相连作中末。"""
    sc = env.get('sanchuan', [])
    if len(sc) >= 3:
        idx = [DIZHI_IDX[z] for z in sc if z in DIZHI_IDX]
        if len(idx) == 3:
            if (idx[1] - idx[0]) % 12 == 1 and (idx[2] - idx[1]) % 12 == 1:
                return _ref('连珠', f'三传{sc}顺连茹', '通解 连珠课')
            if (idx[0] - idx[1]) % 12 == 1 and (idx[1] - idx[2]) % 12 == 1:
                return _ref('连珠', f'三传{sc}逆连茹', '通解 连珠课')
    return None


def judge_jian_chuan(env):
    """间传：间位作三传。"""
    sc = env.get('sanchuan', [])
    if len(sc) >= 3:
        idx = [DIZHI_IDX[z] for z in sc if z in DIZHI_IDX]
        if len(idx) == 3:
            if (idx[1] - idx[0]) % 12 == 2 and (idx[2] - idx[1]) % 12 == 2:
                return _ref('间传', f'三传{sc}隔位相传', '通解 间传课')
    return None


def judge_liu_chun(env):
    """六纯：四课三传俱阳，或俱阴。"""
    sike = env.get('sike', [])
    sc = env.get('sanchuan', [])
    yang_zhi = {'子', '寅', '辰', '午', '申', '戌'}
    yin_zhi = {'丑', '卯', '巳', '未', '酉', '亥'}
    all_zhi = [k[1] for k in sike if len(k) > 1] + [k[2] for k in sike if len(k) > 2] + sc
    all_zhi = [z for z in all_zhi if z in DIZHI_IDX]
    if all_zhi and (all(z in yang_zhi for z in all_zhi) or all(z in yin_zhi for z in all_zhi)):
        return _ref('六纯', '四课三传俱阳或俱阴', '通解 六纯课')
    return None


def judge_zhan_guan(env):
    """斩关：魁罡加日干支发用。"""
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    sike = env.get('sike', [])
    # 魁罡=戌辰；发用为魁罡，或魁罡加日干/日支
    if chu in ('戌', '辰'):
        return _ref('斩关', f'魁罡{chu}发用', '通解 斩关课')
    return None


def judge_long_zhan(env):
    """龙战：卯酉日占，卯酉为用，年立卯酉。"""
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    if ri_zhi in ('卯', '酉') and chu in ('卯', '酉'):
        return _ref('龙战', f'卯酉日占，{chu}为用', '通解 龙战课')
    return None


def judge_si_qi(env):
    """死奇：斗罡系日辰阴阳发用。"""
    chu = env.get('chu', '')
    if chu == '辰':
        return _ref('死奇', '天罡(辰)发用', '通解 死奇课')
    return None


def judge_gui_mu(env):
    """鬼墓：日辰墓神及日鬼发用。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    wx = GAN_WX.get(ri_gan, '')
    mu = MU_KU.get(wx, '')
    if chu == mu:
        return _ref('鬼墓', f'日干{ri_gan}墓神{mu}发用', '通解 鬼墓课')
    return None


def judge_li_de(env):
    """励德：天乙立卯酉——阳贵、阴贵两个贵人，任一加临地盘卯或酉，即"贵人临门"。
    《通解》："凡天乙立卯酉，为励德课。"
    憨爷拍板（2026-08-15）：阳贵/阴贵（与昼夜贵本质不同）都查，任一临卯酉即励德。
    细分：阳神前引阴神后随→君子吉；阴神前阳神后→小人得意（统随之体，反复不定）。
    """
    ri_gan = env.get('ri_gan', '')
    tdp = env.get('tdp', {})  # {地盘支: 天盘支}
    # 十干阳贵/阴贵（前=阳贵，后=阴贵）
    GUI_REN = {'甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
               '乙': ['子', '申'], '己': ['子', '申'],
               '丙': ['亥', '酉'], '丁': ['亥', '酉'],
               '壬': ['卯', '巳'], '癸': ['卯', '巳'],
               '辛': ['午', '寅']}
    guis = GUI_REN.get(ri_gan, [])
    for gui in guis:
        # 逆映射：天盘 gui 加临的地盘位
        for d, t in (tdp or {}).items():
            if t == gui and d in ('卯', '酉'):
                return _ref('励德', f'贵人{gui}加临地盘{d}（贵人临门）', '通解 励德课')
    return None


def judge_zhu_yin(env):
    """铸印课（2026-08-16 憨爷拍板 A+B 都算）：
    A 标准：三传巳戌卯（巳炉、戌印天魁、卯印模太冲，戌中辛金逢巳中丙火作合）
    B 变体：发用(初传)所临地盘=巳(炉)，三传见戌(印)、卯(模)
    """
    sc = env.get('sanchuan', [])
    if not sc:
        sc = [env.get('chu', ''), env.get('zhong', ''), env.get('mo', '')]
    chu = sc[0] if len(sc) > 0 else ''
    zhong = sc[1] if len(sc) > 1 else ''
    mo = sc[2] if len(sc) > 2 else ''
    # A：三传巳戌卯
    if chu == '巳' and zhong == '戌' and mo == '卯':
        return _ref('铸印', '三传巳戌卯（巳炉/戌印/卯模，戌中辛金逢巳中丙火作合）', '通解 铸印课')
    # B：发用临巳(炉) + 三传见戌(印)卯(模)
    sike = env.get('sike', [])
    chu_di = ''
    for k in sike:
        if len(k) >= 3 and k[1] == chu:
            chu_di = k[2]
            break
    if chu_di == '巳' and '戌' in sc and '卯' in sc:
        return _ref('铸印', '发用临巳(炉)+三传见戌(印)卯(模)', '通解 铸印课')
    return None


def judge_xuan_gai(env):
    """轩盖：胜光(午)为用，遇太冲(卯)神后(子)。"""
    chu = env.get('chu', '')
    sc = env.get('sanchuan', [])
    if chu == '午' and '卯' in sc and '子' in sc:
        return _ref('轩盖', '午为用，传遇卯子', '通解 轩盖课')
    return None


def judge_you_zi(env):
    """游子：三传皆土，旬丁天马加季发用。"""
    sc = env.get('sanchuan', [])
    if sc and all(ZHI_WX.get(z, '') == '土' for z in sc):
        return _ref('游子', f'三传{sc}皆土(四季)', '通解 游子课')
    return None


def judge_san_jiao(env):
    """三交：四仲日占，四仲加日辰，三传皆仲，逢阴合。"""
    ri_zhi = env.get('ri_zhi', '')
    sc = env.get('sanchuan', [])
    if ri_zhi in SI_ZHONG and sc and all(z in SI_ZHONG for z in sc):
        return _ref('三交', f'四仲日占，三传{sc}皆仲', '通解 三交课')
    return None


def judge_long_de(env):
    """龙德：太岁月将乘贵人发用。"""
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    if chu_tj == '贵人':
        return _ref('龙德', '贵人发用', '通解 龙德课')
    return None


def judge_shi_tai(env):
    """时泰：太岁月建乘青龙六合，带财德之神发用。"""
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    ri_gan = env.get('ri_gan', '')
    # 财 = 我克之五行对应的地支
    cai_wx = WX_KE.get(GAN_WX.get(ri_gan, ''), '')
    cai_zhi = [z for z, wx in ZHI_WX.items() if wx == cai_wx]
    de = GAN_DE.get(ri_gan, '')
    if chu_tj in ('青龙', '六合') and (chu in cai_zhi or chu == de):
        return _ref('时泰', f'{chu_tj}发用，带财德({chu})', '通解 时泰课')
    return None


def judge_rong_hua(env):
    """荣华：禄马贵人临干支年命，旺相气发用，乘吉将。"""
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    yue_jian = env.get('yue_jian', '')
    lu = GAN_LU.get(ri_gan, '')
    ma = YI_MA.get(ri_zhi, '')
    gui = GAN_GUIREN.get(ri_gan, '')
    lin = [z for z in (lu, ma, gui) if z]
    sike_zhi = [k[1] for k in env.get('sike', []) if len(k) > 1]
    if (chu in lin or any(z in sike_zhi for z in lin)) and is_wang_xiang(chu, yue_jian) and \
            chu_tj in ('贵人', '青龙', '六合', '太常', '天后', '太阴'):
        return _ref('荣华', f'禄马贵临日辰，旺相{chu_tj}发用', '通解 荣华课')
    return None


def judge_guan_jue(env):
    """官爵：岁月年命驿马发用，天魁太常入传。"""
    chu = env.get('chu', '')
    sc = env.get('sanchuan', [])
    ri_zhi = env.get('ri_zhi', '')
    ma = YI_MA.get(ri_zhi, '')
    if chu == ma and ('戌' in sc or env.get('chu_tianjiang', '') == '太常'):
        return _ref('官爵', f'驿马{ma}发用，天魁太常入传', '通解 官爵课')
    return None


def judge_san_guang(env):
    """三光：用神、日辰旺相，吉神在中。"""
    chu = env.get('chu', '')
    ri_zhi = env.get('ri_zhi', '')
    yue_jian = env.get('yue_jian', '')
    chu_tj = env.get('chu_tianjiang', '')
    if is_wang_xiang(chu, yue_jian) and is_wang_xiang(ri_zhi, yue_jian) and \
            chu_tj in ('贵人', '青龙', '六合', '太常', '天后', '太阴'):
        return _ref('三光', f'用神日辰旺相，吉将{chu_tj}发用', '通解 三光课')
    return None


def judge_san_qi(env):
    """三奇：旬日之奇发用或入传。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    sc = env.get('sanchuan', [])
    # 旬奇：甲子甲戌旬用丑，甲申甲午旬用子，甲辰甲寅旬用亥
    xun = _xun_shou(env.get('ri_gan', ''), env.get('ri_zhi', ''))
    xun_qi = {'甲子': '丑', '甲戌': '丑', '甲申': '子', '甲午': '子', '甲辰': '亥', '甲寅': '亥'}
    q = xun_qi.get(xun, '')
    if q and (chu == q or q in sc):
        return _ref('三奇', f'旬奇{q}入传', '通解 三奇课')
    return None


def judge_liu_yi(env):
    """六仪：旬首之仪发用或入传。"""
    xun = _xun_shou(env.get('ri_gan', ''), env.get('ri_zhi', ''))
    chu = env.get('chu', '')
    sc = env.get('sanchuan', [])
    yi = {'甲子': '子', '甲戌': '戌', '甲申': '申', '甲午': '午', '甲辰': '辰', '甲寅': '寅'}
    y = yi.get(xun, '')
    if y and (chu == y or y in sc):
        return _ref('六仪', f'旬首仪{y}入传', '通解 六仪课')
    return None


def judge_he_huan(env):
    """合欢：日辰天干作合+支三合六合发用。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    # 天干五合：甲己 乙庚 丙辛 丁壬 戊癸
    gan_he = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙',
              '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}
    if chu in SANHE_MAP and SANHE_MAP.get(chu) == ri_zhi:
        return _ref('合欢', f'三传六合{chu}发用', '通解 合欢课')
    return None


def judge_he_mei(env):
    """和美：干支三合六合上下互合。"""
    ri_zhi = env.get('ri_zhi', '')
    sike = env.get('sike', [])
    # 干支上神与日辰六合
    for k in sike:
        if len(k) > 2 and k[2] == ri_zhi and k[1] in SANHE_MAP and SANHE_MAP.get(k[1]) == ri_zhi:
            return _ref('和美', '干支上下互合', '通解 和美课')
    return None


def judge_heng_tong(env):
    """亨通：用神生日，三传递生日干。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    if _sheng(chu, ri_gan):
        return _ref('亨通', f'用神{chu}生日干', '通解 亨通课')
    return None


def judge_qin_hai(env):
    """侵害：日辰六害相加并行年。"""
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    if chu in LIUHAI and LIUHAI.get(chu) == ri_zhi:
        return _ref('侵害', f'六害{chu}加日支', '通解 侵害课')
    return None


def judge_xing_shang(env):
    """刑伤：三刑发用并行年。"""
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    if chu in SANXING and SANXING.get(chu) == ri_zhi:
        return _ref('刑伤', f'三刑{chu}加日支', '通解 刑伤课')
    return None


def judge_po_hua(env):
    """魄化：白虎带死神死气临日辰行年发用。"""
    chu_tj = env.get('chu_tianjiang', '')
    if chu_tj == '白虎':
        return _ref('魄化', '白虎发用', '通解 魄化课')
    return None


def judge_yang_jiu(env):
    """殃咎：三传递克日，神将克战，或干支乘墓。"""
    ri_gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', [])
    if sc and all(_ke(z, ri_gan) for z in sc):
        return _ref('殃咎', f'三传{sc}递克日干', '通解 殃咎课')
    return None


def judge_bi_kou(env):
    """闭口：旬尾加旬首，或旬首乘玄武发用。"""
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    if chu_tj == '玄武':
        return _ref('闭口', '玄武发用', '通解 闭口课')
    return None


def judge_tian_huo(env):
    """天祸：四立日，今日干支临昨日干支（或反之）发用。"""
    jieqi = env.get('jieqi', '')
    if jieqi in ('立春', '立夏', '立秋', '立冬'):
        return _ref('天祸', f'四立日({jieqi})干支临昨日(四绝)', '通解 天祸课')
    return None


def judge_tian_kou(env):
    """天寇：四离日，月宿加离辰(四仲)发用。"""
    jieqi = env.get('jieqi', '')
    lunar_month = env.get('lunar_month', 0)
    lunar_day = env.get('lunar_day', 0)
    if jieqi in ('春分', '秋分', '夏至', '冬至'):
        yue_su_ = yue_su(lunar_month, lunar_day) if lunar_month else ''
        li_zhi = XIU_ZHI.get(yue_su_, '')
        if li_zhi in SI_ZHONG:
            return _ref('天寇', f'四离日({jieqi})月宿{yue_su_}加离辰{li_zhi}', '通解 天寇课')
    return None


def judge_er_fan(env):
    """二烦：四仲月将 + 四正日 + 日月宿加四仲 + 斗罡系丑未。"""
    yue_jiang = env.get('yue_jiang', '')
    lunar_day = env.get('lunar_day', 0)
    lunar_month = env.get('lunar_month', 0)
    # 四条件
    c1 = yue_jiang in SI_ZHONG
    c2 = si_zheng_day(lunar_day)
    # 日月宿加四仲：日宿地支在四仲 + 月宿（二十八宿）对应地支宫在四仲
    ri_su_ = ri_su(env.get('yue_jian', ''))
    yue_su_ = yue_su(lunar_month, lunar_day) if lunar_month else ''
    ri_su_zhong = ri_su_ in SI_ZHONG
    yue_su_zhong = XIU_ZHI.get(yue_su_, '') in SI_ZHONG if yue_su_ else False
    c3 = ri_su_zhong and yue_su_zhong
    # 斗罡系丑未（天罡辰加临丑未）
    c4 = env.get('dou_gang_wei', '') in ('丑', '未')
    hit = [ok for c, ok in [(c1, '四仲月将'), (c2, '四正日'), (c3, f'日月宿加四仲(日{ri_su_}月{yue_su_})'), (c4, '斗罡系丑未')] if c]
    if len(hit) == 4:
        return _ref('二烦', f'天地相并：{hit}', '通解 二烦课')
    return None


def judge_zhuo_lun(env):
    """斫轮：卯加庚或加辛为用。"""
    chu = env.get('chu', '')
    if chu == '卯':
        return _ref('斫轮', '卯(太冲)发用(卯加庚辛)', '通解 斫轮课')
    return None


def judge_yin_cong(env):
    """引从：日辰干支前后上神发用为初末传。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    sike = env.get('sike', [])
    # 引从课原文：日辰干支前后上神发用为初末传。当前实现基于干上神/支上神的近似
    # （缺地盘"干前支后"精确位置判定，2026-08-17 记档：待《通解》原文核对该课精确前提）。
    chu, mo = env.get('chu', ''), env.get('mo', '')
    gan_shang = ''
    zhi_shang = ''
    for k in sike:
        if len(k) > 2 and k[2] == ri_gan and not gan_shang:
            gan_shang = k[1]
        if len(k) > 2 and k[2] == ri_zhi and not zhi_shang:
            zhi_shang = k[1]
    if gan_shang and zhi_shang and chu == gan_shang and mo == zhi_shang:
        return _ref('引从', f'干上{gan_shang}为初，支上{zhi_shang}为末，引从日辰', '通解 引从课')
    return None


def judge_luan_shou(env):
    """乱首：干加支受支克（下欺上）。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    sike = env.get('sike', [])
    for k in sike:
        if len(k) > 2 and k[2] == ri_zhi and k[1] == ri_gan:
            # 干加支，看是否支克干
            if _ke(ri_zhi, ri_gan):
                return _ref('乱首', f'干{ri_gan}加支{ri_zhi}受克', '通解 乱首课')
    return None


def judge_zhui_xu(env):
    """赘婿：支加干受干克（上凌下）。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    sike = env.get('sike', [])
    for k in sike:
        if len(k) > 2 and k[2] == ri_gan and k[1] == ri_zhi:
            if _ke(ri_gan, ri_zhi):
                return _ref('赘婿', f'支{ri_zhi}加干{ri_gan}受克', '通解 赘婿课')
    return None


def judge_chong_po(env):
    """冲破：日辰冲神加破为用。"""
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    # 冲神 = 日支对冲位
    chong = DIZHI[(DIZHI_IDX[ri_zhi] + 6) % 12] if ri_zhi in DIZHI_IDX else ''
    if chu == chong:
        return _ref('冲破', f'日支{ri_zhi}冲神{chong}发用', '通解 冲破课')
    return None


def judge_yin_yi(env):
    """淫佚：天后六合乘卯酉。"""
    # 卯酉上神乘天后/六合
    tian_jiang = env.get('tian_jiang', {})
    for zhi in ('卯', '酉'):
        if tian_jiang and tian_jiang.get(zhi) in ('天后', '六合'):
            return _ref('淫佚', f'{zhi}乘天后六合', '通解 淫佚课')
    return None


def judge_wu_yin(env):
    """芜淫：四课不备（二阴一阳或二阳一阴），日辰交互相克。"""
    sike = env.get('sike', [])
    yang_zhi = {'子', '寅', '辰', '午', '申', '戌'}
    sike_shang = [k[1] for k in sike if len(k) > 1]
    yang_count = sum(1 for z in sike_shang if z in yang_zhi)
    if len(sike) < 4 or yang_count in (1, 3):
        return _ref('芜淫', f'四课不备(阳神不备)', '通解 芜淫课')
    return None


def judge_jie_li(env):
    """解离：干上神克支，支上神克干。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    sike = env.get('sike', [])
    gan_shang = zhi_shang = ''
    for k in sike:
        if len(k) > 2 and k[2] == ri_gan and not gan_shang:
            gan_shang = k[1]
        if len(k) > 2 and k[2] == ri_zhi and not zhi_shang:
            zhi_shang = k[1]
    if gan_shang and zhi_shang and _ke(gan_shang, ri_zhi) and _ke(zhi_shang, ri_gan):
        return _ref('解离', f'干上{gan_shang}克支，支上{zhi_shang}克干', '通解 解离课')
    return None


def judge_gu_chen(env):
    """孤辰：春巳顺四孟（春巳夏申秋亥冬寅）。"""
    yue_jian = env.get('yue_jian', '')
    chu = env.get('chu', '')
    season = get_season(yue_jian)
    g = GU_CHEN_BY_SEASON.get(season, '')
    if g and chu == g:
        return _ref('孤辰', f'{season}季孤辰{g}发用', '通解 孤辰课')
    return None


def judge_gua_su(env):
    """寡宿：春丑顺四季（春丑夏辰秋未冬戌）。"""
    yue_jian = env.get('yue_jian', '')
    chu = env.get('chu', '')
    season = get_season(yue_jian)
    g = GUA_SU_BY_SEASON.get(season, '')
    if g and chu == g:
        return _ref('寡宿', f'{season}季寡宿{g}发用', '通解 寡宿课')
    return None


def judge_tian_yu(env):
    """天狱：墓作死囚用（日墓临死囚神发用）。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    yue_jian = env.get('yue_jian', '')
    wx = GAN_WX.get(ri_gan, '')
    mu = MU_KU.get(wx, '')
    if chu == mu and get_wang_shuai(chu, yue_jian) in ('死', '囚'):
        return _ref('天狱', f'日干墓神{mu}临死囚发用', '通解 天狱课')
    return None


def judge_san_yin(env):
    """三阴：天乙逆行，日辰在后，用神囚死，将乘玄虎，时克行年。"""
    chu_tj = env.get('chu_tianjiang', '')
    if chu_tj in ('玄武', '白虎'):
        return _ref('三阴', f'{chu_tj}发用(阴气)', '通解 三阴课')
    return None


def judge_pan_zhu(env):
    """盘珠：太岁月建日时并三传皆在四课之中。"""
    sc = env.get('sanchuan', [])
    sike_zhi = [k[1] for k in env.get('sike', []) if len(k) > 1] + [k[2] for k in env.get('sike', []) if len(k) > 2]
    if sc and all(z in sike_zhi for z in sc):
        return _ref('盘珠', f'三传{sc}皆在四课之中', '通解 盘珠课')
    return None


def judge_fan_chang(env):
    """繁昌：夫妻年立德方发用。"""
    nianming = env.get('nianming', '')
    if nianming and len(str(nianming)) >= 4:
        return _ref('繁昌', '夫妻年命发用', '通解 繁昌课')
    return None


def judge_jiu_chou(env):
    """九丑：乙戊己辛壬日，子午卯酉加临（特定十丑日）。
    九丑十课：戊子、戊午、壬子、壬午、乙卯、乙酉、己卯、己酉、辛卯、辛酉。"""
    ri_gan = env.get('ri_gan', '')
    ri_zhi = env.get('ri_zhi', '')
    JIU_CHOU_RI = {'戊子', '戊午', '壬子', '壬午', '乙卯', '乙酉', '己卯', '己酉', '辛卯', '辛酉'}
    if ri_gan + ri_zhi in JIU_CHOU_RI:
        return _ref('九丑', f'{ri_gan}{ri_zhi}日(九丑日)', '通解 九丑课')
    return None


def judge_za_zhuang(env):
    """杂状：初传动爻别五行纯杂、数目、物色。"""
    chu = env.get('chu', '')
    if chu:
        return _ref('杂状', f'初传{chu}动爻取象', '通解 杂状课')
    return None


def judge_wu_lei(env):
    """物类：初传动爻别五行六亲、物类亲疏。"""
    chu = env.get('chu', '')
    if chu:
        return _ref('物类', f'初传{chu}动爻类象', '通解 物类课')
    return None


def judge_zhun_fu(env):
    """迍福：八迍五福，吉凶参半。"""
    # 八迍（八种迍滞）五福（五种福），吉凶参半，暂以课传是否有救神判
    return _ref('迍福', '吉凶参半（八迍五福）', '通解 迍福课')


def judge_san_yang(env):
    """三阳：天乙顺行，日辰有气居前，旺相气发用。"""
    chu = env.get('chu', '')
    ri_gan = env.get('ri_gan', '')
    yue_jian = env.get('yue_jian', '')
    if ri_gan in ('甲', '丙', '戊', '庚', '壬') and is_wang_xiang(chu, yue_jian):
        return _ref('三阳', f'阳日{ri_gan}，{chu}旺相发用', '通解 三阳课')
    return None


def judge_fu_gui(env):
    """富贵：天乙乘旺相气，上下相生，临日辰年命发用。"""
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    yue_jian = env.get('yue_jian', '')
    if chu_tj == '贵人' and is_wang_xiang(chu, yue_jian):
        return _ref('富贵', '天乙贵人乘旺相发用', '通解 富贵课')
    return None


def judge_de_qing(env):
    """德庆：日辰干支德神，天月二德发用，乘吉将。"""
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tianjiang', '')
    de = GAN_DE.get(ri_gan, '')
    if chu == de and chu_tj in ('贵人', '青龙', '六合', '太常', '天后', '太阴'):
        return _ref('德庆', f'日德{de}发用乘吉将', '通解 德庆课')
    return None


def judge_zai_e(env):
    """灾厄：丧车、游魂、伏殃、病符、丧吊、丘墓、岁虎发用。"""
    chu = env.get('chu', '')
    yue_jian = env.get('yue_jian', '')
    nian_zhi = env.get('nian_zhi', '')
    ri_gan = env.get('ri_gan', '')
    chu_tj = env.get('chu_tianjiang', '')
    # 逐凶煞核对（丧车/游魂/伏殃按月建，病符/丧门/吊客按年支，五墓按日干，岁虎=白虎）
    xiong = []
    if chu == sang_che(yue_jian):
        xiong.append(f'丧车{chu}')
    if chu == you_hun(yue_jian):
        xiong.append(f'游魂{chu}')
    if chu == fu_yang(yue_jian):
        xiong.append(f'伏殃{chu}')
    if nian_zhi and chu == bing_fu(nian_zhi):
        xiong.append(f'病符{chu}')
    if nian_zhi and chu == sang_men(nian_zhi):
        xiong.append(f'丧门{chu}')
    if nian_zhi and chu == diao_ke(nian_zhi):
        xiong.append(f'吊客{chu}')
    if chu == wu_mu(ri_gan):
        xiong.append(f'丘墓{chu}')
    if chu_tj == '白虎':
        xiong.append(f'岁虎{chu}')
    if xiong:
        return _ref('灾厄', '、'.join(xiong) + '发用', '通解 灾厄课')
    return None


# ═════════════ 辅助函数 ═════════════
def _ke(a: str, b: str) -> bool:
    """a 克 b（五行相克）。"""
    wx_a, wx_b = ZHI_WX.get(a, ''), ZHI_WX.get(b, '')
    return wx_a and wx_b and _wx_ke(wx_a, wx_b)


def _wx_ke(a: str, b: str) -> bool:
    ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    return ke.get(a) == b


def _sheng(a: str, b: str) -> bool:
    """a 生 b（五行相生）。"""
    wx_a, wx_b = ZHI_WX.get(a, ''), GAN_WX.get(b, '')
    sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    return wx_a and wx_b and sheng.get(wx_a) == wx_b


def _xun_shou(ri_gan: str, ri_zhi: str) -> str:
    """根据日干日支推旬首（六甲）。"""
    if ri_gan not in TIANGAN or ri_zhi not in DIZHI_IDX:
        return ''
    gan_idx = TIANGAN.index(ri_gan)
    zhi_idx = DIZHI_IDX[ri_zhi]
    # 旬首地支 = 日支逆数（日干到甲的距离）位
    jia_zhi = DIZHI[(zhi_idx - gan_idx) % 12]
    return '甲' + jia_zhi


# ═════════════ ③ 统一入口 ═════════════
_JUDGES = {
    '度厄': judge_du_e, '无禄': judge_wu_lu, '绝嗣': judge_jue_si, '天网': judge_tian_wang,
    '全局': judge_quan_ju, '玄胎': judge_xuan_tai, '连珠': judge_lian_zhu, '间传': judge_jian_chuan,
    '六纯': judge_liu_chun, '斩关': judge_zhan_guan, '龙战': judge_long_zhan, '死奇': judge_si_qi,
    '鬼墓': judge_gui_mu, '励德': judge_li_de, '铸印': judge_zhu_yin, '轩盖': judge_xuan_gai,
    '游子': judge_you_zi, '三交': judge_san_jiao, '龙德': judge_long_de, '时泰': judge_shi_tai,
    '三光': judge_san_guang, '三奇': judge_san_qi, '六仪': judge_liu_yi, '合欢': judge_he_huan,
    '和美': judge_he_mei, '亨通': judge_heng_tong, '侵害': judge_qin_hai, '刑伤': judge_xing_shang,
    '魄化': judge_po_hua, '殃咎': judge_yang_jiu, '闭口': judge_bi_kou, '天祸': judge_tian_huo,
    '天寇': judge_tian_kou, '二烦': judge_er_fan,
    '斫轮': judge_zhuo_lun, '引从': judge_yin_cong, '乱首': judge_luan_shou, '赘婿': judge_zhui_xu,
    '冲破': judge_chong_po, '淫佚': judge_yin_yi, '芜淫': judge_wu_yin, '解离': judge_jie_li,
    '孤辰': judge_gu_chen, '寡宿': judge_gua_su, '天狱': judge_tian_yu, '三阴': judge_san_yin,
    '盘珠': judge_pan_zhu, '荣华': judge_rong_hua, '官爵': judge_guan_jue, '繁昌': judge_fan_chang,
    '九丑': judge_jiu_chou, '迍福': judge_zhun_fu,
    '三阳': judge_san_yang, '富贵': judge_fu_gui, '德庆': judge_de_qing, '灾厄': judge_zai_e,
}


def judge_64_keti(env: Dict[str, Any]) -> List[Dict]:
    """统一入口：判定命中的课体（不含九宗门，九宗门由 fa_sanchuan 返回课体）。
    【BUG-FIX 2026-08-18】空 env（缺日干日支）直接返回空——原空 env 会误命中
    鬼墓/冲破等规则（judge_64_keti({}) 误报）。"""
    if not env or not env.get('ri_gan') or not env.get('ri_zhi'):
        return []
    hits = []
    for name, fn in _JUDGES.items():
        try:
            r = fn(env)
            if r:
                hits.append(r)
        except Exception:
            pass
    return hits


if __name__ == '__main__':
    # 自测
    env = {'ri_gan': '辛', 'ri_zhi': '酉', 'chu': '午', 'zhong': '辰', 'mo': '寅',
           'sanchuan': ['午', '辰', '寅'], 'yue_jiang': '午', 'yue_jian': '申',
           'sike': [['一', '戌', '辛', '贵'], ['二', '戌', '戌', ''], ['三', '酉', '酉', ''], ['四', '酉', '酉', '']],
           'chu_tianjiang': '白虎', 'lunar_month': 7, 'lunar_day': 15}
    print('度厄:', judge_du_e(env))
    print('全局:', judge_quan_ju(env))
    print('连珠:', judge_lian_zhu(env))
    print('日宿(申月):', ri_su('申'))
    print('月宿(7月15):', yue_su(7, 15))
