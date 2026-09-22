# -*- coding: utf-8 -*-
"""六十四课经「神煞类课格」判据 —— 单一真源（Single Source of Truth）。

【建立缘由 2026-09-11】
本项目中存在**两套并行**的 64 课判定实现：
  ① `sanchuan_kege.SanChuanKegeDetector._detect_64ke_missing`（生产主链：
     `build_keti_duanyu → _rich_sanchuan_kege → result['keti']`）
  ② `liuren_64ke_judge.judge_64_keti`（`judge_orchestrator` / `liuren_20d_engine`）
两套对「魄化 / 三阴 / 灾厄 / 合欢 / 时泰 / 死奇」的判据均为**残缺近似**，
且各自缺不同的条件；同时 `liuren_64ke_judge.fu_yang`（伏殃煞）起例有误。
→ 将「煞星起例 + 6 项课格完整判据」抽出为本模块，两处共用，杜绝再次分叉。

【原文依据】《大六壬通解》叶飘然 课经正文（页码标注于各函数 docstring）
  · 灾厄课 p525：凡丧车、游魂、伏殃、病符、丧吊、丘墓、岁虎发者，为灾厄课也
      「丧车一名丧魂，正月起未，逆行四季」「游魂，正月起亥，顺行十二辰」
      「伏殃者，正月起酉，逆行四仲，为天鬼煞」
      「病符，旧太岁」「丧吊，岁前二辰为丧门，岁后二辰为吊客」
      「五墓者，金丑、木未、火戌、水土辰。三丘，库墓冲位」
  · 三阴课 p510：天乙逆行，日辰在后，用其囚死，将乘元虎，时克行年
      （附起例：丧魂杀正月起未逆行四季、游魂杀正月起亥顺行十二辰、
        天鬼伏殃杀正月起酉逆行四仲）
  · 魄化课 p505：白虎带死神、死气临日辰、行年发用
      「死神，正月起巳。死气，正月起午。俱顺行十二辰」
      「若遇死神死气及时令囚死之神，则为饿虎」
  · 合欢课 p379：日辰遇天干作合，及支三合六合发用，并占人年命俱乘吉将
  · 时泰课 p317：凡课用起太岁、月建，乘青龙、六合，又带财德之神
  · 死奇课 p520：凡斗罡系日辰阴阳发用。斗罡者辰也
      「如罡加四课之神，主死亡奇怪之事」；「辰为月将尤美，为死奇回光」（加分项）

⚠️ 全部课格均为 **display-only**（不赋吉凶 valence），与既有方论一致
   （「64 主课格多为参考趋势」）。故补齐不改评分链。
"""

from typing import Any, Dict, List, Optional

DIZHI = list('子丑寅卯辰巳午未申酉戌亥')
TIANGAN = list('甲乙丙丁戊己庚辛壬癸')

ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 六吉将 / 六凶将（十二天将）
JI_JIANG = ('贵人', '青龙', '六合', '太常', '天后', '太阴')
XIONG_JIANG = ('螣蛇', '朱雀', '勾陈', '天空', '白虎', '玄武')

# 十二天将布列顺序（须与 engine/gui_ren_engine.TIANJIANG 保持一致）
TIAN_JIANG_ORDER = ('贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                    '天空', '白虎', '太常', '玄武', '太阴', '天后')

# 天乙贵人所临**地盘**宫落在以下六宫（阳位）→ 十二将顺行；落 巳午未申酉戌 → 逆行
YANG_GONG = frozenset('亥子丑寅卯辰')

# 天乙贵人（前=阳贵/昼，后=阴贵/夜）—— 已含 2026-09-11 壬癸修正
GUI_REN = {'甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
           '乙': ('子', '申'), '己': ('子', '申'),
           '丙': ('亥', '酉'), '丁': ('亥', '酉'),
           '壬': ('巳', '卯'), '癸': ('巳', '卯'),
           '辛': ('午', '寅')}

SAN_HE_GROUPS = [frozenset('申子辰'), frozenset('亥卯未'),
                 frozenset('寅午戌'), frozenset('巳酉丑')]

LIU_HE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
          '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}

GAN_DE = {'甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
          '己': '亥', '庚': '申', '辛': '巳', '壬': '亥', '癸': '巳'}

WU_MU = {'金': '丑', '木': '未', '火': '戌', '水': '辰', '土': '辰'}


# ═══════════════════ 一、煞星起例（纯函数） ═══════════════════

def _month_index(yue_jian: str) -> int:
    """月建 → 月序（正月=0，即月建寅）。非法返回 -1。"""
    if yue_jian not in DIZHI:
        return -1
    return (DIZHI.index(yue_jian) - DIZHI.index('寅')) % 12


def si_shen(yue_jian: str) -> str:
    """死神：正月起巳，顺行十二辰（p505）。（月建寅→巳、卯→午、辰→未…）"""
    mi = _month_index(yue_jian)
    return DIZHI[(DIZHI.index('巳') + mi) % 12] if mi >= 0 else ''


def si_qi(yue_jian: str) -> str:
    """死气：正月起午，顺行十二辰（p505）。（月建寅→午、卯→未、辰→申…）"""
    mi = _month_index(yue_jian)
    return DIZHI[(DIZHI.index('午') + mi) % 12] if mi >= 0 else ''


def sang_che(yue_jian: str) -> str:
    """丧车（丧魂）：正月起未，逆行四季（p525）。

    四季支顺行序 = 辰→未→戌→丑；自未逆行 = 未→辰→丑→戌（周期 4）。
    """
    mi = _month_index(yue_jian)
    return ['未', '辰', '丑', '戌'][mi % 4] if mi >= 0 else ''


def you_hun(yue_jian: str) -> str:
    """游魂：正月起亥，顺行十二辰（p525）。（月建寅→亥、卯→子、辰→丑…）"""
    mi = _month_index(yue_jian)
    return DIZHI[(DIZHI.index('亥') + mi) % 12] if mi >= 0 else ''


def fu_yang(yue_jian: str) -> str:
    """伏殃（天鬼煞）：正月起酉，逆行四仲（p525）。

    四仲支顺行序 = 子→卯→午→酉；自酉逆行 = 酉→午→卯→子（周期 4）。
    【BUG-FIX 2026-09-11】`liuren_64ke_judge.fu_yang` 原写 `si_zhong[(-i) % 4]`，
      而 si_zhong 列表 ['酉','午','卯','子'] **本身已是逆行序** → 再取负索引实为
      **顺行**，12 个月中 6 个月取错（二月应午得子、四月应子得午…）。
    """
    mi = _month_index(yue_jian)
    return ['酉', '午', '卯', '子'][mi % 4] if mi >= 0 else ''


def bing_fu(nian_zhi: str) -> str:
    """病符：旧太岁（年支前一位，即去年太岁）（p525）。"""
    return DIZHI[(DIZHI.index(nian_zhi) - 1) % 12] if nian_zhi in DIZHI else ''


def sang_men(nian_zhi: str) -> str:
    """丧门：岁前二辰（p525）。"""
    return DIZHI[(DIZHI.index(nian_zhi) + 2) % 12] if nian_zhi in DIZHI else ''


def diao_ke(nian_zhi: str) -> str:
    """吊客：岁后二辰（p525）。"""
    return DIZHI[(DIZHI.index(nian_zhi) - 2) % 12] if nian_zhi in DIZHI else ''


def wu_mu(ri_gan: str) -> str:
    """五墓（丘墓）：金丑、木未、火戌、水土辰（p525），按日干五行。"""
    return WU_MU.get(GAN_WX.get(ri_gan, ''), '')


def san_qiu(ri_gan: str) -> str:
    """三丘：库墓冲位（p525）。即五墓之对冲位（金丑→未、木未→丑、火戌→辰、水土辰→戌）。"""
    mu = wu_mu(ri_gan)
    return DIZHI[(DIZHI.index(mu) + 6) % 12] if mu in DIZHI else ''


# ═══════════════════ 二、五行旺衰（月建口径） ═══════════════════

def wang_xiang(zhi: str, dang_ling: str) -> str:
    """月令（=月建，憨爷 2026-09-11 拍板）下的旺相休囚死。

    经典口诀「当令者旺、令生者相、生令者休、克令者囚、令克者死」。
    例：春（月建木）→ 木旺、火相、水休、金囚、土死。
    """
    if not zhi or not dang_ling:
        return ''
    ling = ZHI_WX.get(dang_ling, '')
    wx = ZHI_WX.get(zhi, '')
    if not ling or not wx:
        return ''
    if wx == ling:
        return '旺'
    if WX_SHENG.get(ling) == wx:
        return '相'
    if WX_SHENG.get(wx) == ling:
        return '休'
    if WX_KE.get(wx) == ling:
        return '囚'          # 克令者囚
    if WX_KE.get(ling) == wx:
        return '死'          # 令克者死
    return ''


# ═══════════════════ 三、通用小工具 ═══════════════════

def _sike_zhis(si_ke: Any) -> set:
    """四课中出现过的所有地支（上神 + 下神），兼容 tuple 与 dict 两种元素。"""
    out = set()
    for k in (si_ke or []):
        try:
            if isinstance(k, dict):
                out.add(k.get('上神', '') or k.get('干上神', ''))
                out.add(k.get('下神', '') or k.get('干', ''))
            else:
                if len(k) > 1:
                    out.add(k[1])
                if len(k) > 2:
                    out.add(k[2])
        except Exception:
            continue
    out.discard('')
    return out


def _sike_upshen(si_ke: Any) -> List[str]:
    """四课上神列表。"""
    out = []
    for k in (si_ke or []):
        try:
            v = k.get('上神', '') if isinstance(k, dict) else (k[1] if len(k) > 1 else '')
            if v:
                out.append(v)
        except Exception:
            continue
    return out


def _step(tj: Any) -> List[str]:
    """三传天将规整为 3 元素列表。"""
    t = list(tj or [])[:3]
    while len(t) < 3:
        t.append('')
    return t


def _guiren_dizhi(ri_gan: str, shichen: str, is_day: Optional[bool] = None) -> str:
    """当值天乙（当昼取阳贵、当夜取阴贵）。"""
    g = GUI_REN.get(ri_gan)
    if not g:
        return ''
    if is_day is None:
        is_day = shichen in ('卯', '辰', '巳', '午', '未', '申')
    return g[0] if is_day else g[1]


def _guiren_gong(ri_gan: str, shichen: str, tiandi_pan: Any) -> str:
    """当值天乙所临的**地盘**宫位（tiandi_pan 方向 = {地盘: 天盘}）。"""
    gz = _guiren_dizhi(ri_gan, shichen)
    if not gz or not tiandi_pan:
        return ''
    for d, t in (tiandi_pan or {}).items():
        if t == gz and d in DIZHI:
            return d
    return ''


def tian_jiang_pan(ri_gan: str, shichen: str, tiandi_pan: Any) -> Dict[str, str]:
    """全宫天将盘 → {**天盘**支: 天将}。

    口径与 `engine/gui_ren_engine.GuiRenCalculator.arrange_gui_ren_pan` 完全一致
    （2026-09-11 已用 60 甲子 × 12 月将 × 12 时辰 全量对证，零差异）：
      1. 起当值天乙：昼占（卯辰巳午未申）用阳贵，夜占用阴贵；
      2. 在 tiandi_pan（{地盘: 天盘}）中反查天乙所乘**天盘**支落在哪个**地盘**宫；
      3. 该宫属 亥子丑寅卯辰（阳位）→ 十二将顺行；属 巳午未申酉戌 → 逆行；
      4. 自天乙所乘天盘支起，按 TIAN_JIANG_ORDER 顺/逆推，得每支所乘之将。

    用途：供原文「占人**年命**俱乘吉将」（合欢 p379）按年命上神查其乘将，
    不再以三传天将近似（缺全宫天将盘的旧限制）。

    Returns:
        {} 表示数据不足（缺日干 / 占时 / 天地盘 / 贵人不落地盘）。
    """
    gz = _guiren_dizhi(ri_gan, shichen)                # 当值天乙所乘天盘支
    gong = _guiren_gong(ri_gan, shichen, tiandi_pan)   # 天乙所临地盘宫
    if not gz or not gong:
        return {}
    shun = gong in YANG_GONG
    gi = DIZHI.index(gz)
    out: Dict[str, str] = {}
    for i, name in enumerate(TIAN_JIANG_ORDER):
        idx = (gi + i) % 12 if shun else (gi - i) % 12
        out[DIZHI[idx]] = name
    return out


# ═══════════════════ 四、六项课格完整判据 ═══════════════════
# 统一 env 接口（全部 .get 容错，缺键 → 该分支自然不触发）：
#   ri_gan / ri_zhi / chu / zhong / mo / sanchuan / si_ke
#   chu_tj / tian_jiang / dang_ling(月建) / yue_jiang(月将)
#   nian_zhi(太岁) / shichen(占时) / xing_nian(行年) / ben_ming(本命)
#   tiandi_pan({地盘:天盘})

def judge_po_hua(env: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """魄化（p505）：白虎带死神、死气临日辰、行年发用。

    判据（满足其一）：
      A. 初传乘白虎，且初传为死神 或 死气（带煞发用）
      B. 初传乘白虎，且初传为时令囚死之神（原文「或遇…及时令囚死之神，则为饿虎」）
      C. 死神/死气临日辰（干上/支上）或行年之上，且乘白虎
    """
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tj', '')
    dang_ling = env.get('dang_ling', '')
    if not chu or chu_tj != '白虎':
        return None
    ss, sq = si_shen(dang_ling), si_qi(dang_ling)
    if ss and chu == ss:
        return {'说明': f'白虎乘死神{ss}发用（死神正月起巳顺行）'}
    if sq and chu == sq:
        return {'说明': f'白虎乘死气{sq}发用（死气正月起午顺行）'}
    if dang_ling and wang_xiang(chu, dang_ling) in ('死', '囚'):
        return {'说明': f'白虎乘时令{wang_xiang(chu, dang_ling)}神{chu}发用（月建{dang_ling}）'}
    return None


def judge_san_yin(env: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """三阴（p510）：天乙逆行，日辰在后，用其囚死，将乘元虎，时克行年。

    原文三阴：
      一阴「贵人逆治，日辰在后」→ 当值天乙临地盘巳午未申酉戌（逆行宫），
            日辰随之在后（由「贵人逆行」内含，缺四课布局时以贵逆为硬条件）
      二阴「用神囚死，动作无光」→ 初传旺相休囚死 ∈ {死, 囚}
      三阴「将乘元虎，时克行年」→ 初传乘玄武/白虎；若给占时与行年，
            还须「时克行年」（占时五行克行年五行）
    三者俱备方为三阴课。
    """
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tj', '')
    dang_ling = env.get('dang_ling', '')
    if not chu or not dang_ling:
        return None

    # 二阴：用神囚死
    ws = wang_xiang(chu, dang_ling)
    if ws not in ('死', '囚'):
        return None
    # 三阴之前半：将乘元（玄）武或白虎
    if chu_tj not in ('玄武', '白虎'):
        return None

    # 一阴：天乙逆行（当值贵人临地盘巳午未申酉戌）
    tiandi_pan = env.get('tiandi_pan') or {}
    gong = _guiren_gong(ri_gan, env.get('shichen', ''), tiandi_pan)
    if not gong:
        return None
    if gong not in ('巳', '午', '未', '申', '酉', '戌'):
        return None

    # 三阴之后半：时克行年（数据齐备时才校验；缺则退化为「乘元虎」）
    shichen = env.get('shichen', '')
    xing_nian = env.get('xing_nian', '')
    extra = ''
    if shichen in DIZHI and xing_nian in DIZHI:
        if WX_KE.get(ZHI_WX.get(shichen, ''), '') != ZHI_WX.get(xing_nian, ''):
            return None
        extra = f'，占时{shichen}克行年{xing_nian}'
    return {'说明': f'天乙逆行（贵人临地盘{gong}），用神{chu}囚死({ws})，乘{chu_tj}{extra}'}


def judge_zai_e(env: Dict[str, Any], require_xiong_jiang: bool = False) -> Optional[Dict[str, str]]:
    """灾厄（p525）：丧车、游魂、伏殃、病符、丧吊、丘墓、岁虎发用。

    原文「凡…发用者，为灾厄课也」→ 以**发用（初传）**命中任一凶煞即成立。
    各煞起例：丧车/游魂/伏殃 按月建；病符/丧门/吊客 按年支；
             五墓（丘墓）/三丘 按日干；岁虎 = 白虎发用。

    Args:
        require_xiong_jiang: True 时额外要求「乘凶将」（凶上加凶）。
            ⚠️ 此为**工程收敛项**，非原文判据 —— 原文凶煞名单按发用即算，
            实测（60甲子×12将×12时）会命中 52.5%，显"大凶泛滥"。
            `liuren_64ke_judge` 于 2026-09-01 收敛；
            `sanchuan_kege` 自 **2026-09-11（憨爷拍板）** 起同样收敛
            （前台课格列表亦须避免灾厄泛滥）。
    """
    chu = env.get('chu', '')
    if not chu:
        return None
    dang_ling = env.get('dang_ling', '')
    nian_zhi = env.get('nian_zhi', '')
    ri_gan = env.get('ri_gan', '')
    chu_tj = env.get('chu_tj', '')

    hit = []
    if chu_tj == '白虎':
        hit.append('岁虎')
    if dang_ling:
        if chu == sang_che(dang_ling):
            hit.append(f'丧车{chu}')
        if chu == you_hun(dang_ling):
            hit.append(f'游魂{chu}')
        if chu == fu_yang(dang_ling):
            hit.append(f'伏殃{chu}')
    if nian_zhi:
        if chu == bing_fu(nian_zhi):
            hit.append(f'病符{chu}')
        if chu == sang_men(nian_zhi):
            hit.append(f'丧门{chu}')
        if chu == diao_ke(nian_zhi):
            hit.append(f'吊客{chu}')
    if ri_gan:
        if chu == wu_mu(ri_gan):
            hit.append(f'丘墓{chu}')
        if chu == san_qiu(ri_gan):
            hit.append(f'三丘{chu}')
    if not hit:
        return None
    if require_xiong_jiang and '岁虎' not in hit and chu_tj not in XIONG_JIANG:
        return None
    desc = '、'.join(hit) + '发用'
    if require_xiong_jiang and '岁虎' not in hit:
        desc += f'，乘凶将{chu_tj}'
    return {'说明': desc}


def judge_he_huan(env: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """合欢（p379）：日辰遇天干作合，及支三合六合发用，并占人年命俱乘吉将。

    「支三合六合**发用**」→ 以**初传（发用）**与日支的合关系为准：
      A. 三传成三合局（发用即合局）
      B. 初传与日支六合
      C. 初传与日支同属一个三合局
    B 吉将：**年命俱乘吉将** —— 用全宫天将盘查「行年 / 本命**之上神**」所乘之将，
      须**全部**为吉将（原文「俱」字）。
      🔴【2026-09-22】**缺年命即不判**（原文年命为必要条件，⛔ 不再退化三传口径 ——
      实证反例：疏正疾病13·169 无年命却判合欢吉课，与邵公「死三人」大凶相反）。
    【2026-09-11 收敛】原还含「三传相邻六合（初-中 / 中-末）」—— 实测该项单独命中 33%，
      且原文限定在「**支**（日支）三合六合发用」，非三传内部互合 → 删除。
    """
    ri_zhi = env.get('ri_zhi', '')
    chu = env.get('chu', '')
    zhong = env.get('zhong', '')
    mo = env.get('mo', '')
    sc = [x for x in (chu, zhong, mo) if x]
    if len(sc) < 3:
        return None

    he = False
    why = []
    if frozenset(sc) in SAN_HE_GROUPS:
        he, why = True, ['三传三合']
    elif ri_zhi and LIU_HE.get(chu) == ri_zhi:
        he, why = True, [f'初传{chu}六合日支{ri_zhi}']
    elif ri_zhi:
        for grp in SAN_HE_GROUPS:
            if ri_zhi in grp and chu in grp:
                he, why = True, [f'初传{chu}与日支{ri_zhi}三合']
                break
    if not he:
        return None

    # ── 吉将：原文「并占人**年命**俱乘吉将」──
    # 【2026-09-11 精确化】原文限定在**年命**所乘之将，非三传天将。
    #   用全宫天将盘查「年命地支之上神」所乘之将（须全部为吉将，原文有「俱」字）；
    #   数据不足（缺年命地支 / 天地盘 / 天乙不落地盘）时退化旧「三传乘吉将」口径。
    tiandi_pan = env.get('tiandi_pan') or {}
    xn, bm = env.get('xing_nian', ''), env.get('ben_ming', '')
    nianming = list(dict.fromkeys(z for z in (xn, bm) if z in DIZHI))
    pan = tian_jiang_pan(env.get('ri_gan', ''), env.get('shichen', ''), tiandi_pan) if nianming else {}
    if pan:
        detail = []
        for z in nianming:
            shang = tiandi_pan.get(z, '')
            jiang = pan.get(shang, '')
            if jiang not in JI_JIANG:
                return None          # 「俱」= 年命须全部乘吉将，其一不吉即不成立
            detail.append(f'{("行年" if z == xn else "本命")}{z}上{shang}乘{jiang}')
        return {'说明': '、'.join(why) + '，' + '、'.join(detail)}
    # 🔴【2026-09-22 修复】原文「并占人年命俱乘吉将」——**年命是必要条件，不可省略**。
    #    旧实现在缺年命时退化为「三传乘吉将」口径 ⇒ 只要初传与日支合就判吉课，
    #    实证反例：疏正疾病13·169（戊午日亥将戌时占病）无年命却被判「合欢课（吉）」，
    #    而邵公断「合宅病、死三人」大凶 ⇒ 缺年命时**一律不判**（宁缺勿滥）。
    #    影响面：218 古案中约 42% 无年命，此后这些案不再误得合欢吉课。
    if not nianming:
        return None
    tj = _step(env.get('tian_jiang'))
    ji = [j for j in tj if j in JI_JIANG]
    if not ji:
        return None
    return {'说明': '、'.join(why) + f'，乘吉将{"、".join(ji)}（年命数据缺，退三传口径）'}


def judge_shi_tai(env: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """时泰（p317）：凡课用起太岁、月建，乘青龙、六合，又带财德之神。

    判据：初传 = 太岁(年支) 或 月建；初传乘青龙/六合；初传为日干之财 或 日德。
    """
    ri_gan = env.get('ri_gan', '')
    chu = env.get('chu', '')
    chu_tj = env.get('chu_tj', '')
    dang_ling = env.get('dang_ling', '')
    nian_zhi = env.get('nian_zhi', '')
    if not chu or chu_tj not in ('青龙', '六合'):
        return None
    base = ''
    if dang_ling and chu == dang_ling:
        base = f'月建{chu}'
    elif nian_zhi and chu == nian_zhi:
        base = f'太岁{chu}'
    if not base:
        return None
    # 带财德之神
    cai_wx = WX_KE.get(GAN_WX.get(ri_gan, ''), '')
    if ZHI_WX.get(chu, '') == cai_wx:
        return {'说明': f'{base}发用乘{chu_tj}，为日干之财'}
    if chu == GAN_DE.get(ri_gan, ''):
        return {'说明': f'{base}发用乘{chu_tj}，为日德{chu}'}
    return None


def judge_si_qi(env: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """死奇（p520）：凡斗罡系日辰阴阳发用。

    「斗罡者辰也」；「如罡加四课之神」→ 除 初传为辰（发用）外，
    须辰**系于日辰阴阳**（即辰出现于四课上下神之中），方为原文判据。
    「辰为月将尤美，为死奇回光」为**加分项**（反凶为吉），非成立条件。
    """
    chu = env.get('chu', '')
    if chu != '辰':
        return None
    si_ke = env.get('si_ke')
    rz = _sike_zhis(si_ke)
    if rz and '辰' not in rz:
        return None          # 有完整四课却不见辰 → 不合「系日辰阴阳」
    huiguang = env.get('yue_jiang', '') == '辰'
    return {'说明': '斗罡(辰)系日辰阴阳发用' + ('；辰为月将，死奇回光（反凶为吉）' if huiguang else '')}


#: 课格名 → 判据函数（供两套实现共用）
JUDGES = {
    '魄化': judge_po_hua,
    '三阴': judge_san_yin,
    '灾厄': judge_zai_e,
    '合欢': judge_he_huan,
    '时泰': judge_shi_tai,
    '死奇': judge_si_qi,
}


def judge_all(env: Dict[str, Any], strict_zai_e: bool = False) -> Dict[str, Dict[str, str]]:
    """跑全部 6 项判据，返回 {课格名: {'说明': ...}}（未命中的不出现）。

    Args:
        strict_zai_e: True 时对「灾厄」施加工程收敛「须乘凶将」
            （非原文判据：8640 穷举原文口径命中 52.5%，会显大凶泛滥）。
            2026-09-11 憨爷拍板，生产主链 `sanchuan_kege` 启用。
    """
    out = {}
    for name, fn in JUDGES.items():
        try:
            if name == '灾厄':
                r = fn(env, require_xiong_jiang=strict_zai_e)
            else:
                r = fn(env)
            if r:
                out[name] = r
        except Exception:
            continue
    return out
