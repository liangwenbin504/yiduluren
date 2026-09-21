# -*- coding: utf-8 -*-
"""
六壬「原子谓词」引擎 v1.0（2026-08-16 憨爷：用矩阵/向量化方法啃 500+ 变格判断）
================================================================
把六壬课式判断拆成不可再分的「原子谓词」，每条谓词 = (name, args)，接受 env 返回 bool。

设计目标：
  1. 504 条变格（从属格）的条件，全部可表示为若干原子谓词的 与/或（DNF）。
  2. 起一课 → 构造 env → 计算事实向量 → 规则矩阵一次扫完 → 命中变格 + 吉凶。
  3. 原子谓词可复用、可扩展；规则是声明式数据，非代码。

env 结构（由 kege_bianjie_engine.build_env 构造）：
  ri_gan/ri_zhi/ganzhi, sanchuan(3), gan_shang/zhi_shang,
  tian_jiang{天盘支:天将}, tiandi_pan{地盘支:天盘支},
  kongwang(2), keti, season, is_day,
  tai_sui, ben_ming_zhi,
  lu(日禄)/de(日德)/yima(驿马)/guiren(贵人),
  shensha{地支: 神煞名集合},  # 预计算：月厌/丧车/天目/死气/丁神等
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# ── 基础常量（与 bifa_detector 对齐）──
GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
GAN_JIGONG = {'甲':'寅','乙':'辰','丙':'巳','丁':'未','戊':'巳','己':'未','庚':'申','辛':'戌','壬':'亥','癸':'丑'}
WX_SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
WX_KE = {'木':'土','火':'金','土':'水','金':'木','水':'火'}
WX_MU = {'木':'未','火':'戌','金':'丑','水':'辰','土':'辰'}  # 三合五行墓（金丑水辰木未火戌土辰）
# 五行胎位（十二长生·土双位：水土同宫"午"为主 + 火土同宫"子"；木胎酉/火胎子/金胎卯/水胎午）
WX_TAI = {'木':'酉','火':'子','土':('午','子'),'金':'卯','水':'午'}
TAI_SHEN = {g: WX_TAI[GAN_WX[g]] for g in GAN_WX}
# 十天干胎位（十干阴阳十二长生·阴干逆排；占胎时五行胎位不在课传则退用此）
TAI_SHEN_10 = {'甲':'酉','乙':'申','丙':'子','丁':'亥','戊':'子','己':'亥','庚':'卯','辛':'寅','壬':'午','癸':'巳'}
# 十二长生位（土双位：水土同宫"申"为主 + 火土同宫"寅"；木长生亥、火长生寅、金长生巳、水长生申）
CHANG_SHENG = {'木':'亥','火':'寅','土':('申','寅'),'金':'巳','水':'申'}
# 绝位（长生+9，土双位：水土同宫"巳"为主 + 火土同宫"亥"）
JUE_WX = {'木':'申','火':'亥','土':('巳','亥'),'金':'寅','水':'巳'}
# 败气（十二长生沐浴位，土双位：水土同宫"酉"为主 + 火土同宫"卯"；通解上L1011）
BAI_WX = {'木':'子','火':'卯','土':('酉','卯'),'金':'午','水':'酉'}
YANG = set('子寅辰午申戌')
YIN = set('丑卯巳未酉亥')
DIZHI_ORDER = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
DIZHI_IDX = {z:i for i,z in enumerate(DIZHI_ORDER)}
LIU_HE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯','辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}
LIU_HAI = {'子':'未','未':'子','丑':'午','午':'丑','寅':'巳','巳':'寅','卯':'辰','辰':'卯','申':'亥','亥':'申','酉':'戌','戌':'酉'}
LIU_CHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
XING = {
    '寅':{'巳'},'巳':{'申'},'申':{'寅'},           # 无恩刑
    '丑':{'戌'},'戌':{'未'},'未':{'丑'},           # 恃势刑
    '子':{'卯'},'卯':{'子'},                        # 无礼刑
    '辰':{'辰'},'午':{'午'},'酉':{'酉'},'亥':{'亥'},  # 自刑
}
# 十干帝旺位（十二长生帝旺：甲卯乙寅丙午丁巳戊午己巳庚酉辛申壬子癸亥）
DI_WANG_ZHI = {'甲':'卯','乙':'寅','丙':'午','丁':'巳','戊':'午','己':'巳',
               '庚':'酉','辛':'申','壬':'子','癸':'亥'}
SANHE = [{'申','子','辰'},{'亥','卯','未'},{'寅','午','戌'},{'巳','酉','丑'}]
# 三合局各支→局五行（申子辰=水、亥卯未=木、寅午戌=火、巳酉丑=金）
_SANHE_WX = {'申':'水','子':'水','辰':'水','亥':'木','卯':'木','未':'木',
             '寅':'火','午':'火','戌':'火','巳':'金','酉':'金','丑':'金'}
# 三合局命名（生男生女用：东南木火=男、西北金水=女）
SANHE_JU = {'润下': {'申','子','辰'}, '曲直': {'亥','卯','未'},
            '炎上': {'寅','午','戌'}, '从革': {'巳','酉','丑'}}
JI_JIANG = {'贵人','青龙','太常','六合','太阴','天后'}
XIONG_JIANG = {'螣蛇','朱雀','勾陈','白虎','玄武','天空'}
# 天将→五行（生克以天将本家五行论，与 bifa_detector.TIANJIANG_WUXING 一致）
TIANJIANG_WX_MAP = {'贵人':'土','螣蛇':'火','朱雀':'火','六合':'木','勾陈':'土','青龙':'木',
                    '天空':'土','白虎':'金','太常':'土','玄武':'水','太阴':'金','天后':'水'}
# 旺相休囚死：按季节。囚 = 克当季旺者；死 = 当季旺所克者
WANG_WX = {'春':'木','夏':'火','秋':'金','冬':'水'}
QIU_WX = {'春':'金','夏':'水','秋':'火','冬':'土'}   # 克旺者（金克木…）
SI_WX  = {'春':'土','夏':'金','秋':'木','冬':'火'}   # 旺所克（木克土…）
# 阳位（贵人落地盘阳位则天乙顺行，与 gui_ren_engine 一致）
TIANYI_YANG = {'亥','子','丑','寅','卯','辰'}

# 旧太岁（病符）：去年太岁 = 当年太岁的前一位地支
DIZHI_TAI_SUI_PREV = {
    '子': '亥', '丑': '子', '寅': '丑', '卯': '寅', '辰': '卯', '巳': '辰',
    '午': '巳', '未': '午', '申': '未', '酉': '申', '戌': '酉', '亥': '戌',
}


def _wx(z: str) -> str:
    return GAN_WX.get(z, '') or ZHI_WX.get(z, '')


def _zhi_sheng(a: str, b: str) -> bool:
    """a 生 b（按五行）"""
    return WX_SHENG.get(_wx(a), '') == _wx(b)


def _zhi_ke(a: str, b: str) -> bool:
    """a 克 b（按五行）"""
    return WX_KE.get(_wx(a), '') == _wx(b)


# ══════════════════════════════════════════════════════════════
# 原子谓词分发：每个谓词 = (name, args) → bool
# args 支持「相对标记」，在求值时先解析成实际地支/天干：
#   干/支/干上/支上/初/中/末/干墓/支墓/干禄/日德/驿马/月厌/丧车/天目/关神 …
# ══════════════════════════════════════════════════════════════
def _kechuan_zhi(env):
    """四课三传上出现的支集合（三传 + 干上/支上 + 四课上神）"""
    zhis = set()
    for z in (env.get('sanchuan') or []):
        if z:
            zhis.add(z)
    if env.get('gan_shang'):
        zhis.add(env['gan_shang'])
    if env.get('zhi_shang'):
        zhis.add(env['zhi_shang'])
    for k in (env.get('si_ke') or []):
        if isinstance(k, (list, tuple)):
            for x in k[1:3]:  # [课名, 上神, 下神, 天将]
                if isinstance(x, str) and x in DIZHI_ORDER:
                    zhis.add(x)
        elif isinstance(k, str) and k in DIZHI_ORDER:
            zhis.add(k)
    return zhis


def _si_ke_san_chuan_all(env, target):
    """日干寄宫 + 日支 + 四课上神 + 三传 是否全落在 target（YANG/YIN）支集合。
    用于六阳课（纯阳）／六阴课（纯阴）判断。四课不完整（<4课）则不判，返回 False。"""
    si_ke = env.get('si_ke') or []
    if len(si_ke) < 4:
        return False
    zhis = set()
    jigong = GAN_JIGONG.get(env.get('ri_gan', ''), '')
    if jigong:
        zhis.add(jigong)
    rz = env.get('ri_zhi', '')
    if rz:
        zhis.add(rz)
    for k in si_ke:
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            if k[1] in DIZHI_ORDER:
                zhis.add(k[1])   # 四课上神
        elif isinstance(k, str) and k in DIZHI_ORDER:
            zhis.add(k)
    for z in (env.get('sanchuan') or []):
        if z:
            zhis.add(z)
    return bool(zhis) and all(z in target for z in zhis)


def _zhi_in_wei(zhi, wei) -> bool:
    """判断地支 zhi 是否落在某十二长生位置 wei（wei 为 str 或 tuple/list 集合，土为双位）。"""
    if not zhi:
        return False
    if isinstance(wei, (tuple, list, set, frozenset)):
        return zhi in wei
    return bool(wei) and zhi == wei


def _resolve_taishen(env):
    """胎神取用（憨爷规则 2026-08-16）：以四课三传出现为准，五行胎位优先（土双位）；
    五行胎位不在课传则退用十天干胎位；都不在则兜底五行胎位主值。"""
    rg = env.get('ri_gan', '')
    if not rg:
        return ''
    wx_tai = WX_TAI.get(_wx(rg), '')    # 五行胎位（土为双位 tuple）
    gan_tai = TAI_SHEN_10.get(rg, '')   # 十干胎位（阴干逆排）
    kc = _kechuan_zhi(env)
    # 五行胎位：课传出现任一候选则取该支（主值优先）
    if isinstance(wx_tai, (tuple, list)):
        for t in wx_tai:
            if t and t in kc:
                return t
    elif wx_tai and wx_tai in kc:
        return wx_tai
    if gan_tai and gan_tai in kc:
        return gan_tai
    # 兜底：五行胎位（主值）
    return wx_tai[0] if isinstance(wx_tai, (tuple, list)) and wx_tai else (wx_tai or '')


def _resolve(arg: str, env: dict) -> str:
    """把相对标记解析成实际地支/天干；字面地支原样返回。"""
    if not isinstance(arg, str):
        return arg
    if arg == '干': return env.get('ri_gan', '')
    if arg == '支': return env.get('ri_zhi', '')
    if arg == '干宫': return GAN_JIGONG.get(env.get('ri_gan', ''), '')
    if arg == '干上': return env.get('gan_shang', '')
    if arg == '支上': return env.get('zhi_shang', '')
    sc = env.get('sanchuan') or []
    if arg == '初': return sc[0] if len(sc) > 0 else ''
    if arg == '中': return sc[1] if len(sc) > 1 else ''
    if arg == '末': return sc[2] if len(sc) > 2 else ''
    if arg == '干墓': return WX_MU.get(_wx(env.get('ri_gan', '')), '')
    if arg == '支墓': return WX_MU.get(_wx(env.get('ri_zhi', '')), '')
    if arg == '干禄': return env.get('lu', '')
    if arg == '日德': return env.get('de', '')
    if arg == '驿马': return env.get('yima', '')
    if arg == '胎神': return _resolve_taishen(env)
    if arg == '支胎': return WX_TAI.get(_wx(env.get('ri_zhi', '')), '')
    if arg == '丁神': return env.get('ding_shen', '')
    if arg == '干长生': return CHANG_SHENG.get(_wx(env.get('ri_gan', '')), '')
    if arg == '支长生': return CHANG_SHENG.get(_wx(env.get('ri_zhi', '')), '')
    if arg == '干败': return BAI_WX.get(_wx(env.get('ri_gan', '')), '')
    if arg == '支败': return BAI_WX.get(_wx(env.get('ri_zhi', '')), '')
    if arg == '干绝': return JUE_WX.get(_wx(env.get('ri_gan', '')), '')
    if arg == '支绝': return JUE_WX.get(_wx(env.get('ri_zhi', '')), '')
    if arg == '病符':
        ts = env.get('tai_sui', '')
        if ts in DIZHI_ORDER:
            return DIZHI_ORDER[(DIZHI_ORDER.index(ts) - 1) % 12]  # 去年太岁 = 病符
        return ''
    return arg


def eval_atom(name: str, args: list, env: dict) -> bool:
    """原子谓词求值分发表"""
    fn = _ATOMS.get(name)
    if not fn:
        return False
    try:
        # 【P3 神煞类收敛 2026-09-02】神煞名参数不做 _resolve：
        # sc_has_sha 的 sha 位、x_shi_shensha 的 sha 位（第二位）为字面神煞名，
        # 若经 _resolve 会被劫持成具体地支（如 '丁神'→旬丁神支、'病符'→去年太岁），
        # 导致对照 build_env 预计算 shensha 名集合恒假 → 丁神系/病符系规则断链。
        if name == 'sc_has_sha':
            return fn(env, args[0] if args else '')
        if name == 'x_shi_shensha':
            x = _resolve(args[0], env) if args and len(args) > 0 else ''
            sha = args[1] if args and len(args) > 1 else ''
            return fn(env, x, sha)
        resolved = [_resolve(a, env) for a in (args or [])]
        return fn(env, *resolved)
    except Exception:
        return False


def _gan_sheng(env, x): return _zhi_sheng(env['ri_gan'], x)
def _x_sheng_gan(env, x): return _zhi_sheng(x, env['ri_gan'])
def _x_ke_gan(env, x): return _zhi_ke(x, env['ri_gan'])
def _gan_ke_x(env, x): return _zhi_ke(env['ri_gan'], x)
def _x_bi_gan(env, x): return _wx(x) == _wx(env['ri_gan'])
def _zhi_sheng_zhi(env, x, y): return _zhi_sheng(x, y)
def _zhi_ke_zhi(env, x, y): return _zhi_ke(x, y)

def _x_shi_gan_mu(env, x): return bool(x) and x == WX_MU.get(_wx(env['ri_gan']), '')
def _x_shi_zhi_mu(env, x): return bool(x) and x == WX_MU.get(_wx(env['ri_zhi']), '')
def _x_kong(env, x): return bool(x) and x in (env.get('kongwang') or ('', ''))

def _x_he_y(env, x, y): return LIU_HE.get(x, '') == y
def _x_hai_y(env, x, y): return LIU_HAI.get(x, '') == y
def _x_chong_y(env, x, y): return LIU_CHONG.get(x, '') == y
def _x_xing_y(env, x, y): return y in XING.get(x, set())

def _zhi_eq(env, x, y): return bool(x) and x == y

# ══════════════════════════════════════════════════════════════
# 批次2 刑害类收敛谓词（2026-09-02）：一字/二字/三字刑、四胜煞、助刑戕德、合中犯杀、得少失多
# 判据以《毕法赋》原文为唯一基准，见 extracted_data/毕法赋_古籍注解_下_正文.txt
# ══════════════════════════════════════════════════════════════
def _si_ke_shang_all(env, zhi_set):
    """一字刑（宾主不投刑在上·第75法）：「四课上神全逢辰午酉亥者是也」。
    a=[四支集合]，四课上神全 ∈ 集合方命中（缺课不算）。"""
    if not zhi_set:
        return False
    allowed = set(zhi_set)
    sike_shang = env.get('si_ke_shang', []) or []
    if not sike_shang:   # 【兜底】si_ke_shang 缺失时从 si_ke 原始结构提取
        sike_shang = _sike_shang_from_sike(env)
    if len(sike_shang) < 4:
        return False
    return all(z in allowed for z in sike_shang)


def _san_chuan_xing(env):
    """三字刑（宾主不投刑在上·第75法）：「三传寅巳申或丑戌未」。
    寅巳申为无恩刑、丑戌未为恃势刑；三传顺序不限（寅巳申/巳申寅/申寅巳、丑戌未/戌未丑/未丑戌俱是）。"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    s = set(sc)
    return s == {'寅', '巳', '申'} or s == {'丑', '戌', '未'}


def _zhu_xing_qiang_de(env):
    """助刑戕德格（宾主不投刑在上·第75法变格）：
    「六处有神作支之自刑，又作干鬼，又结连三传为鬼是也」。如庚午日午加庚发用。
    判据：支为自刑支（辰午酉亥）且六处(干上/支上/三传)有神=支，且支克干（作干鬼），且三传皆克干（结连为鬼）。"""
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    sc = env.get('sanchuan', [])
    if not gan or not zhi or len(sc) != 3:
        return False
    if zhi not in ('辰', '午', '酉', '亥'):          # 支须为自刑支
        return False
    if zhi not in ([gs, zs] + list(sc)):            # 六处有神作支之自刑（神=支）
        return False
    if not _zhi_ke(zhi, gan):                       # 又作干鬼（支克干）
        return False
    return all(_zhi_ke(z, gan) for z in sc)         # 结连三传为鬼（三传皆克干）


def _de_shao_shi_duo(env):
    """得少失多格（费有余而得不足·第57法）：
    「甲寅日干上卯，乃日之旺神，三传辰巳午…辰乃干上卯之六害，中末盗气」。
    判据：干上=日干帝旺（旺神）且初传=干上之六害且中末传为日干所生（子孙盗气泄我）。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    sc = env.get('sanchuan', [])
    if not gan or not gs or len(sc) != 3:
        return False
    if DI_WANG_ZHI.get(gan, '') != gs:              # 干上须为日干旺神（帝旺位）
        return False
    chu, zhong, mo = sc
    if LIU_HAI.get(chu, '') != gs:                  # 初传=干上之六害
        return False
    return _zhi_sheng(gan, zhong) and _zhi_sheng(gan, mo)   # 中末盗气（日干生之，我生者泄我）

# ══════════════════════════════════════════════════════════════
# 批次3 神煞类收敛谓词（2026-09-02）：罗网系（干前/支前一辰）+ 三传神煞扫描
# 判据以《毕法赋》原文为唯一基准（所谋多拙逢罗网·第55法）
# ══════════════════════════════════════════════════════════════
def _shi_gan_wang(env, loc):
    """值干之罗网（所谋多拙逢罗网·第55法）：「干上乘干前一辰」。
    例甲申日干上卯（甲寄寅，帝旺卯）；丙申日干上午；壬寅日干上子。loc=日干帝旺位方为网。"""
    return bool(loc) and loc == DI_WANG_ZHI.get(env.get('ri_gan', ''), '')


def _shi_zhi_qian(env, loc):
    """值支之罗网（所谋多拙逢罗网·第55法）：「支上乘支前一辰」。
    例甲申日支上酉（申后一位）、庚寅日支上酉。loc=日支顺行下一支（乘旺为网）。"""
    rz = env.get('ri_zhi', '')
    if not loc or rz not in DIZHI_ORDER:
        return False
    return loc == DIZHI_ORDER[(DIZHI_ORDER.index(rz) + 1) % 12]


def _sc_has_sha(env, sha):
    """三传任一支为某神煞（课传逢煞）。替代 sc_has(神煞名) 占位用法——
    sc_has 仅判地支∈三传，传神煞名恒假；此处按 build_env 预计算 shensha 查询。"""
    if not sha:
        return False
    return any(sha in (env.get('shensha', {}).get(z) or set())
               for z in (env.get('sanchuan') or []) if z)

def _de_shen_wei_gui(env):
    """德神为鬼：日德之神加临鬼方（德神所坐之盘克日干），德化鬼而不害，占功名利病无妨。
    通解上·德庆课「或乙日申德加酉为用，酉来克乙，申化鬼，乃德神为鬼之例」（德申坐地盘酉，酉克乙木）。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判德坐鬼方。"""
    gan = env.get('ri_gan', '')
    de = env.get('de', '')
    if not gan or not de:
        return False
    tdp = env.get('tiandi_pan', {}) or {}
    # 【B5d 2026-09-03】原文「申德加酉为用」→ 德须在课传六处，防全盘扫描命中偏高(恰20%边界)
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    if de not in spots:
        return False
    for dp, tp in tdp.items():
        if tp == de and _zhi_ke(dp, gan):
            return True
    return False


def _zhi_shang_dun_gui(env):
    """支上神遁旬中干鬼（支上神旬遁干五行克日干），明暗二鬼格之暗鬼。
    毕法赋·虎乘遁鬼殃非浅「干上神作日干明鬼，又支上神遁旬干作日干暗鬼」。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 仿 _gan_shang_dun_gui 按原文判暗鬼。"""
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    if not zs or not gan:
        return False
    g = _dun_gan(env, zs)
    return bool(g) and WX_KE.get(_wx(g), '') == _wx(gan)


def _gui_ren_zuo_mu(env):
    """贵人作墓：贵神（昼夜贵之一）作四墓（丑辰未戌）加临干上。
    毕法赋·鬼乘天乙乃神祗「贵人作墓格：六甲日丑为夜贵作墓神加干，六庚日丑为昼贵作墓神加干」。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判贵临干且为墓。"""
    gs = env.get('gan_shang', '')
    gan = env.get('ri_gan', '')
    if not gs or not gan:
        return False
    gui = GUIREN_MAP.get(gan, ())
    if not gui or gs not in gui:
        return False
    return gs in '丑辰未戌'


def _gui_ren_tuo_qi(env):
    """贵人脱气：贵神加临干上而为日干脱气（日干生贵神），必被贵人脱赚或神祗降殃以致脱耗。
    毕法赋·鬼乘天乙乃神祗「贵人脱气格：如六壬、六癸日以卯为夜贵作脱气」。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判贵临干且为脱气。"""
    gs = env.get('gan_shang', '')
    gan = env.get('ri_gan', '')
    if not gs or not gan:
        return False
    gui = GUIREN_MAP.get(gan, ())
    if not gui or gs not in gui:
        return False
    return _zhi_sheng(gan, gs)


def _bu_xing_zhong_xing(env):
    """不幸中幸、幸中不幸：白虎却作长生（白虎乘日干长生=不幸中幸），青龙却乘日鬼（青龙乘日鬼=幸中不幸）。
    毕法赋「如六戊日伏吟，昼占三重白虎作长生，乃不幸中幸；夜占三重青龙作日干之鬼，乃幸中不幸」。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判课传白虎乘长生/青龙乘日鬼。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    tj = env.get('tian_jiang', {})
    cs = CHANG_SHENG.get(_wx(gan), '')
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    for z in spots:
        jiang = tj.get(z, '')
        if jiang == '白虎':
            if cs and _zhi_in_wei(z, cs):      # 白虎作长生：不幸中幸
                return True
        elif jiang == '青龙':
            if _zhi_ke(z, gan):                # 青龙乘日鬼：幸中不幸
                return True
    return False


def _hu_zhi_yin_shen_zhi_hu(env):
    """虎之阴神制虎：白虎乘日鬼之位，其阴神（该位加临之下一神=tiandi_pan[x]）克鬼（制虎）。
    毕法赋·虎临干鬼凶速速「如甲子日申加戌昼将，上乘白虎作中传，申坐戌空，又赖虎之阴神上乘午火而制虎鬼。
    经云：虎之阴神还制虎，生者安宁病者愈」（tiandi_pan[申]=午，午火克申金）。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判阴神制虎。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    tj = env.get('tian_jiang', {})
    tdp = env.get('tiandi_pan', {}) or {}
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    for z in spots:
        if tj.get(z, '') == '白虎' and _zhi_ke(z, gan):
            yinshen = tdp.get(z, '')
            if yinshen and _zhi_ke(yinshen, z):  # 阴神克鬼（制虎鬼）
                return True
    return False


def _gui_zuo_gui_fang(env):
    """鬼坐鬼方无所畏：日鬼加临于克鬼之地盘（鬼坐于其鬼方=受制无威，故无所畏）。
    毕法赋·虎临干鬼凶速速「又如甲子日申加午昼将，上乘白虎作末传，其申不空，诚为可畏，
    尤赖申金坐于午火之上。经云：鬼坐鬼方无所畏」（午火克申金=午为申之鬼方）。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判鬼坐鬼方。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    tdp = env.get('tiandi_pan', {}) or {}
    tj = env.get('tian_jiang', {}) or {}
    # 【B5d 2026-09-03 v2】原文例「申加午...上乘白虎作末传」→ 须白虎乘鬼同位（限课传六处，
    # 防全盘 12 位扫描过宽 41.67%；实测无白虎要求时六处版仍 41.67%）
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    dp_by_tp = {tp: dp for dp, tp in tdp.items()}
    for z in spots:
        if tj.get(z, '') != '白虎' or not _zhi_ke(z, gan):
            continue
        if _zhi_ke(dp_by_tp.get(z, ''), z):
            return True
    return False


def _gui_zi_jiu_sheng(env):
    """鬼自就生不来侵：日鬼加临于鬼之长生位（鬼自就生，不来为害）。
    毕法赋·虎临干鬼凶速速「又如戊寅日寅加亥夜将，上乘白虎作中传，诚为凶也，
    殊不知寅木坐于亥水之上，寅木受亥水作长生，不来为害。经云：鬼自就生不来侵」（亥=寅木长生）。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判鬼临长生。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    tdp = env.get('tiandi_pan', {}) or {}
    tj = env.get('tian_jiang', {}) or {}
    # 【B5d 2026-09-03 v2】原文例「寅加亥...上乘白虎作中传」→ 须白虎乘鬼同位临长生（限课传六处，
    # 防全盘扫描命中偏高恰 20% 边界；与鬼坐鬼方同源同文例）
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    dp_by_tp = {tp: dp for dp, tp in tdp.items()}
    for z in spots:
        if tj.get(z, '') != '白虎' or not _zhi_ke(z, gan):
            continue
        cs = CHANG_SHENG.get(_wx(z), '')
        if cs and _zhi_in_wei(dp_by_tp.get(z, ''), cs):
            return True
    return False


def _tian_gui_zuo_ri_gui(env):
    """天鬼作日鬼：课传六处有神乘天鬼（伏殃煞）且为日鬼，占病必是疫气。
    毕法赋·鬼临三四讼灾随「天鬼作日鬼格：在六处占病，必是疫气」。
    天鬼神煞（正月起酉逆行四仲：酉午卯子循环）由 build_env 预计算入 shensha。
    【B5d 2026-09-03】原规则共享 x_ke_gan(初) 占位判据 26.25% 过宽 → 按原文判天鬼临处且为日鬼。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    shensha = env.get('shensha', {})
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in (env.get('sanchuan') or []) if z}
    for z in spots:
        if '天鬼' in (shensha.get(z) or set()) and _zhi_ke(z, gan):
            return True
    return False


def _x_cheng(env, x, j):
    """X乘天将：仅限课传六处（四课三传+干上支上）及年命之神（2026-08-21 修复：
    原实现直查天盘，盘外之支乘将也命中——天将乘神只论课传/年命，变格33条规则同受益）"""
    if not x:
        return False
    if x not in _kechuan_zhi(env) and x != env.get('ben_ming_zhi', ''):
        return False
    return env.get('tian_jiang', {}).get(x, '') == j


def _x_cheng_ji(env, x):
    if not x:
        return False
    if x not in _kechuan_zhi(env) and x != env.get('ben_ming_zhi', ''):
        return False
    return env.get('tian_jiang', {}).get(x, '') in JI_JIANG


def _x_cheng_xiong(env, x):
    if not x:
        return False
    if x not in _kechuan_zhi(env) and x != env.get('ben_ming_zhi', ''):
        return False
    return env.get('tian_jiang', {}).get(x, '') in XIONG_JIANG
def _j_ke_x(env, x):
    # 2026-08-21 审计补丁：与 _x_cheng 同口径——天将克神仅限课传六处+年命
    if not x or (x not in _kechuan_zhi(env) and x != env.get('ben_ming_zhi', '')):
        return False
    j = env.get('tian_jiang', {}).get(x, '')
    jw = TIANJIANG_WX_MAP.get(j, '')
    return bool(jw) and WX_KE.get(jw, '') == _wx(x)

def _j_sheng_gan(env, x):
    """x 所乘天将（本家五行）生日干（2026-08-21 审计补丁：限课传六处+年命）"""
    if not x or (x not in _kechuan_zhi(env) and x != env.get('ben_ming_zhi', '')):
        return False
    j = env.get('tian_jiang', {}).get(x, '')
    jw = TIANJIANG_WX_MAP.get(j, '')
    return bool(jw) and WX_SHENG.get(jw, '') == _wx(env.get('ri_gan', ''))

def _j_ke_gan(env, x):
    """x 所乘天将（本家五行）克日干"""
    j = env.get('tian_jiang', {}).get(x, '')
    jw = TIANJIANG_WX_MAP.get(j, '')
    return bool(jw) and WX_KE.get(jw, '') == _wx(env.get('ri_gan', ''))

def _x_ke_j(env, x):
    """x（地支五行）克其所乘天将（本家五行）"""
    j = env.get('tian_jiang', {}).get(x, '')
    jw = TIANJIANG_WX_MAP.get(j, '')
    return bool(jw) and WX_KE.get(_wx(x), '') == jw

def _shi_keti(env, k): return k in env.get('keti', '')
def _sc_set(env, a, b, c): return set(env.get('sanchuan', [])) == {a, b, c}
def _sc_has(env, x): return x in env.get('sanchuan', [])
def _sc_quanyang(env): sc = env.get('sanchuan', []); return bool(sc) and all(z in YANG for z in sc)
def _sc_quanyin(env): sc = env.get('sanchuan', []); return bool(sc) and all(z in YIN for z in sc)
def _sc_sanhe(env): return any(set(env.get('sanchuan', [])) == s for s in SANHE)
def _sc_ju(env, ju):
    """三传成特定三合局（曲直/炎上/从革/润下）"""
    return set(env.get('sanchuan', [])) == SANHE_JU.get(ju, set())
def _keti_liuyang(env):
    """六阳课：日干寄宫 + 日支 + 四课上神 + 三传 全在阳支（纯阳）"""
    return _si_ke_san_chuan_all(env, YANG)
def _keti_liuyin(env):
    """六阴课：日干寄宫 + 日支 + 四课上神 + 三传 全在阴支（纯阴）"""
    return _si_ke_san_chuan_all(env, YIN)
def _sc_quanzhong(env):
    """三传皆四仲（子午卯酉）"""
    sc = env.get('sanchuan', [])
    return len(sc) == 3 and all(z in {'子','午','卯','酉'} for z in sc)
def _chu_shi(env, x): return env.get('sanchuan', ['', '', ''])[0] == x
def _mo_shi(env, x): return env.get('sanchuan', ['', '', ''])[2] == x

def _x_shi_shensha(env, x, sha):
    """x 是否为某神煞（预计算 shensha{地支:{神煞集合}}）"""
    return sha in (env.get('shensha', {}).get(x) or set())
def _x_shi_lu(env, x): return x == env.get('lu', '')
def _x_shi_de(env, x): return x == env.get('de', '')
def _x_shi_yima(env, x): return x == env.get('yima', '')


def _yima_bei_chong(env):
    """驿马被冲破（官爵淹留）：驿马发用（官爵课之马动）且课传六处见驿马对冲神。
    观月经·官爵课「忽然驿马破，官职有淹留。若申子辰日时，功曹发用，是驿马动也。
    若课中见传送是驿马破也，主帝王降罪之兆」（寅马见申=破）。
    【B5e 2026-09-04】官爵淹留格原判据"驿马空亡"（简化为占位，20% 过宽且语义错）
    → 按「马发用∧课见冲神」精确化（实测 6.39%）。"""
    yima = env.get('yima', '')
    if not yima:
        return False
    sc = env.get('sanchuan') or []
    if not sc or sc[0] != yima:          # 驿马发用（官爵课前提）
        return False
    chong = LIU_CHONG.get(yima, '')
    if not chong:
        return False
    spots = set()
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.add(z)
    spots |= {z for z in sc if z}
    return chong in spots

def _x_wang(env, x):
    # 旺：x 五行 == 当季旺五行（春木夏火秋金冬水）
    wang = {'春':'木','夏':'火','秋':'金','冬':'水'}.get(env.get('season', ''), '')
    return bool(wang) and _wx(x) == wang

def _benming_shi(env, x): return env.get('ben_ming_zhi', '') == x
def _x_ke_benming(env, x):
    bm = env.get('ben_ming_zhi', '')
    return bool(bm) and _zhi_ke(x, bm)

def _gan_shang_shi(env, x): return _zhi_in_wei(env.get('gan_shang', ''), x)
def _zhi_shang_shi(env, x): return _zhi_in_wei(env.get('zhi_shang', ''), x)
def _gan_shang_yang(env): return env.get('gan_shang', '') in YANG
def _gan_shang_yin(env): return env.get('gan_shang', '') in YIN
def _gan_yin_shen(env):
    """干上神的阴神 = 第二课上神（si_ke[1] 的『上神』）"""
    si_ke = env.get('si_ke') or []
    if len(si_ke) >= 2:
        k = si_ke[1]
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            return k[1] if k[1] in DIZHI_ORDER else ''
    return ''
def _gan_yin_shen_yang(env): return _gan_yin_shen(env) in YANG
def _gan_yin_shen_yin(env): return _gan_yin_shen(env) in YIN
def _gan_shi(env, x): return env.get('ri_gan', '') == x
def _zhi_shi(env, x): return env.get('ri_zhi', '') == x
def _is_day(env): return env.get('is_day', True)

def _sc_jinlianru(env):
    """三传进连茹（初→中→末 顺行连续）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3: return False
    i0 = DIZHI_IDX.get(sc[0]); i1 = DIZHI_IDX.get(sc[1]); i2 = DIZHI_IDX.get(sc[2])
    return i0 is not None and i1 == (i0+1) % 12 and i2 == (i0+2) % 12

def _sc_tuilianru(env):
    """三传退连茹（末→中→初 逆行连续，即初→中→末递减）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3: return False
    i0 = DIZHI_IDX.get(sc[0]); i1 = DIZHI_IDX.get(sc[1]); i2 = DIZHI_IDX.get(sc[2])
    return i0 is not None and i1 == (i0-1) % 12 and i2 == (i0-2) % 12

def _ganzhi_he(env):
    """干支六合（干寄宫与日支六合）"""
    gp = GAN_JIGONG.get(env.get('ri_gan', ''), '')
    return bool(gp) and LIU_HE.get(gp, '') == env.get('ri_zhi', '')

def _ganzhi_shang_he(env):
    """干支上神六合"""
    return LIU_HE.get(env.get('gan_shang', ''), '') == env.get('zhi_shang', '')

def _x_shi_guiren(env, x):
    """x 是贵人地支（昼贵或夜贵）"""
    gp = env.get('guiren', ()) or ()
    return x in gp

def _gan_yang(env): return env.get('ri_gan', '') in '甲丙戊庚壬'
def _gan_yin(env): return env.get('ri_gan', '') in '乙丁己辛癸'
def _x_wang_xiang(env, x):
    """x 旺或相（旺=当季五行，相=旺所生）"""
    if not x:
        return False
    w = WANG_WX.get(env.get('season', ''), '')
    if not w:
        return False
    wx = _wx(x)
    return wx == w or wx == WX_SHENG.get(w, '')


def _x_shuai(env, x):
    """x 衰（休囚死：非旺非相）"""
    if not x:
        return False
    w = WANG_WX.get(env.get('season', ''), '')
    if not w:
        return False
    return not _x_wang_xiang(env, x)

def _chu_meng(env):
    """初传为四孟（寅申巳亥）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and sc[0] in {'寅','申','巳','亥'}

def _chu_zhong(env):
    """初传为四仲（子午卯酉）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and sc[0] in {'子','午','卯','酉'}

def _chu_ji(env):
    """初传为四季（辰戌丑未）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and sc[0] in {'辰','戌','丑','未'}

def _tianjiang_ru_chuan(env, j):
    """某天将入三传"""
    tj = env.get('tian_jiang', {})
    return any(tj.get(z, '') == j for z in (env.get('sanchuan') or []))

def _season_shi(env, x): return env.get('season', '') == x

def _x_qiu_si(env, x):
    """x 囚或死（按当季：囚=克旺者，死=旺所克）"""
    if not x: return False
    q = QIU_WX.get(env.get('season', ''), '')
    s = SI_WX.get(env.get('season', ''), '')
    wx = _wx(x)
    return (bool(q) and wx == q) or (bool(s) and wx == s)

def _x_shi_siqi(env, x):
    """x 是当季死气（五行=当季死五行）"""
    if not x: return False
    s = SI_WX.get(env.get('season', ''), '')
    return bool(s) and _wx(x) == s

def _x_shi_bai(env, x):
    """x 是日干五行败气（十二长生沐浴位，通解上L1011；土双位）"""
    if not x: return False
    b = BAI_WX.get(_wx(env.get('ri_gan', '')), '')
    return _zhi_in_wei(x, b)

def _xiaochuan(env):
    """小产法：母本命上神冲或克胎神"""
    bm = env.get('ben_ming_zhi', '')
    tai = _resolve_taishen(env)
    if not bm or not tai:
        return False
    tp = env.get('tiandi_pan', {}) or {}
    shang = tp.get(bm, '')  # 本命上神 = 天盘加临本命地支
    if not shang:
        return False
    return LIU_CHONG.get(shang, '') == tai or WX_KE.get(_wx(shang), '') == _wx(tai)

def _jiang_lin_siqi(env, j):
    """天将 j 所乘之地支 = 月内死气（月死气克该天将）"""
    siqi = env.get('si_qi', '')
    if not siqi:
        return False
    tj = env.get('tian_jiang', {}) or {}
    return tj.get(siqi, '') == j

def _x_dun_gan(env, x, gan):
    """x 的旬遁天干 == gan（旬遁干：甲子旬甲配子顺排十干）"""
    if not x or not gan:
        return False
    rg = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    if not rg or not rz:
        return False
    try:
        g_idx = '甲乙丙丁戊己庚辛壬癸'.index(rg)
        z_idx = DIZHI_ORDER.index(rz)
        shou = (z_idx - g_idx) % 12  # 旬首支
        x_idx = DIZHI_ORDER.index(x)
        offset = (x_idx - shou) % 12   # 在地支环上的正向偏移
        dun = '甲乙丙丁戊己庚辛壬癸'[offset % 10]
        return dun == gan
    except (ValueError, IndexError):
        return False

def _ganzhi_tong_gong(env):
    """干支同宫（日干寄宫 == 日支），借钱还债格"""
    return GAN_JIGONG.get(env.get('ri_gan', ''), '') == env.get('ri_zhi', '')

def _taishen_zuo_changsheng(env):
    """胎神（天盘）加临胎神自身五行的长生位（地盘），胎神坐长生格（土双位）"""
    tai = _resolve_taishen(env)
    if not tai:
        return False
    cs = CHANG_SHENG.get(_wx(tai), '')  # 胎神五行的长生位（土为 tuple）
    tdp = env.get('tiandi_pan', {}) or {}
    if isinstance(cs, (tuple, list)):
        return any(tdp.get(c, '') == tai for c in cs)
    return bool(cs) and tdp.get(cs, '') == tai

def _taishen_lin_jue(env):
    """胎神（天盘）加临胎神自身五行的绝位（地盘），胎神临绝受克（土双位）"""
    tai = _resolve_taishen(env)
    if not tai:
        return False
    jue = JUE_WX.get(_wx(tai), '')  # 胎神五行的绝位（火绝亥、木绝申…；土双位）
    tdp = env.get('tiandi_pan', {}) or {}
    if isinstance(jue, (tuple, list)):
        return any(tdp.get(j, '') == tai for j in jue)
    return bool(jue) and tdp.get(jue, '') == tai

def _x_zhi_wang(env, x):
    """x 当令旺（复刻 bifa_detector._is_zhi_wang：x 非空，且 season 为空时视作旺，非空则按当季旺五行判）"""
    if not x:
        return False
    season = env.get('season', '')
    if season:
        wx = _wx(x)
        season_wx = WANG_WX.get(season, '')
        if wx and season_wx:
            return wx == season_wx
    return True

def _gan_shang_dun_gui(env):
    """干上神遁旬中干鬼（干上神旬遁干五行克日干），财遁鬼格"""
    gs = env.get('gan_shang', '')
    rg = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    if not gs or not rg or not rz:
        return False
    try:
        g_idx = '甲乙丙丁戊己庚辛壬癸'.index(rg)
        z_idx = DIZHI_ORDER.index(rz)
        shou = (z_idx - g_idx) % 12
        gs_idx = DIZHI_ORDER.index(gs)
        offset = (gs_idx - shou) % 12
        dun = '甲乙丙丁戊己庚辛壬癸'[offset % 10]
        return WX_KE.get(GAN_WX.get(dun, ''), '') == GAN_WX.get(rg, '')
    except (ValueError, IndexError):
        return False

def _tp_jia(env, x, y):
    """天盘 x 加临地盘 y（tiandi_pan[y]==x）"""
    return (env.get('tiandi_pan', {}) or {}).get(y, '') == x

def _tian_gang_jia(env):
    """天罡（辰）所加临的地盘支（天盘辰落于哪个地盘位）"""
    tp = env.get('tiandi_pan', {}) or {}
    for d, t in tp.items():
        if t == '辰':
            return d
    return ''

def _tian_gang_bi_gan(env):
    """天罡所加临地盘支与日干比（同五行）→ 生男（通解上L4050 天罡断男女法）"""
    d = _tian_gang_jia(env)
    return bool(d) and _wx(d) == _wx(env.get('ri_gan', ''))

def _tian_gang_bi_zhi(env):
    """天罡所加临地盘支与日支比（同五行）→ 生女"""
    d = _tian_gang_jia(env)
    return bool(d) and _wx(d) == _wx(env.get('ri_zhi', ''))

def _shen_jia_fu_ming(env):
    """天盘申加临丈夫行年（申加夫命，通解上L4043《连珠经》法）"""
    f = env.get('fu_xing_nian_zhi', '')
    return bool(f) and (env.get('tiandi_pan', {}) or {}).get(f, '') == '申'

def _qi_xing_nian_shang(env):
    """妻行年上神 = 天盘加临妻行年地支的神"""
    q = env.get('qi_xing_nian_zhi', '')
    if not q:
        return ''
    return (env.get('tiandi_pan', {}) or {}).get(q, '')

def _qi_xing_nian_shang_yang(env):
    """妻行年上神为阳 → 生男"""
    return _qi_xing_nian_shang(env) in YANG

def _qi_xing_nian_shang_yin(env):
    """妻行年上神为阴 → 生女"""
    return _qi_xing_nian_shang(env) in YIN

def _tianyi_zhi(env):
    """天乙（贵人天将）所乘天盘支"""
    tj = env.get('tian_jiang', {}) or {}
    for z, j in tj.items():
        if j == '贵人':
            return z
    return ''

def _tianyi_shun(env):
    """天乙顺行？贵人落地盘位阳（亥子丑寅卯辰）则顺、阴则逆（同 gui_ren_engine）。
    缺 tiandi_pan 时按昼顺夜逆兜底。无法判断返回 None。"""
    G = _tianyi_zhi(env)
    if not G:
        return None
    td = env.get('tiandi_pan', {}) or {}
    di_pos = ''
    for d, t in td.items():
        if t == G:
            di_pos = d
            break
    if di_pos:
        return di_pos in TIANYI_YANG
    return env.get('is_day', True)


def _richen_qian_hou(env):
    """日辰（日干寄宫+日支）相对天乙（贵人天盘支）的位置：
    '前'=两处都在天乙顺行侧5宫；'后'=两处都在逆行侧5宫；'中'=对冲/混杂；None=无法判断。
    注：前后各 5 宫，对冲宫 G±6 不计入前后。"""
    G = _tianyi_zhi(env)
    if not G:
        return None
    gi = DIZHI_IDX.get(G)
    if gi is None:
        return None
    is_shun = _tianyi_shun(env)
    if is_shun is None:
        return None
    qian, hou = set(), set()
    for k in range(1, 6):
        if is_shun:
            qian.add(DIZHI_ORDER[(gi + k) % 12])  # 顺行侧为前
            hou.add(DIZHI_ORDER[(gi - k) % 12])   # 逆行侧为后
        else:
            qian.add(DIZHI_ORDER[(gi - k) % 12])
            hou.add(DIZHI_ORDER[(gi + k) % 12])
    jigong = GAN_JIGONG.get(env.get('ri_gan', ''), '')
    ri_zhi = env.get('ri_zhi', '')
    zhis = [z for z in (jigong, ri_zhi) if z]
    if not zhis:
        return None
    if all(z in qian for z in zhis):
        return '前'
    if all(z in hou for z in zhis):
        return '后'
    return '中'


def _richen_zai_tianyi_qian(env):
    """日辰居天乙前"""
    return _richen_qian_hou(env) == '前'


def _richen_zai_tianyi_hou(env):
    """日辰居天乙后"""
    return _richen_qian_hou(env) == '后'

def _mo_xinghai_jiaohu(env):
    """末传刑害交互：末传与干支（寄宫/日支）或初传、中传有刑或害关系"""
    sc = env.get('sanchuan', []) or []
    if len(sc) < 3:
        return False
    mo = sc[2]
    others = [GAN_JIGONG.get(env.get('ri_gan', ''), ''), env.get('ri_zhi', '')]
    if len(sc) >= 1: others.append(sc[0])
    if len(sc) >= 2: others.append(sc[1])
    for y in others:
        if not y or y == mo:
            continue
        # 刑：mo 刑 y 或 y 刑 mo；害：六害（对称）
        if mo in XING and y in XING.get(mo, set()):
            return True
        if y in XING and mo in XING.get(y, set()):
            return True
        if LIU_HAI.get(mo, '') == y:
            return True
    return False


# ── 财/鬼谓词（2026-08-21 新增：支持毕法赋硬编码规则迁移） ──
def _x_shi_cai(env, x):
    """x 是日干之财爻（日干克 x）"""
    return bool(x) and _zhi_ke(env['ri_gan'], x) and _wx(x) != _wx(env['ri_gan'])


def _x_shi_gui(env, x):
    """x 是日干之官鬼（x 克日干）"""
    return bool(x) and _zhi_ke(x, env['ri_gan']) and _wx(x) != _wx(env['ri_gan'])


def _sc_quancai(env):
    """三传皆日干之财"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and all(_zhi_ke(env['ri_gan'], z) and _wx(z) != _wx(env['ri_gan']) for z in sc)


def _sc_quangui(env):
    """三传皆日干之官鬼"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and all(_zhi_ke(z, env['ri_gan']) and _wx(z) != _wx(env['ri_gan']) for z in sc)


def _sc_chu_cai_mo_gui(env):
    """初传财→末传鬼（传财化鬼）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    chu, _, mo = sc
    return (_zhi_ke(env['ri_gan'], chu) and _wx(chu) != _wx(env['ri_gan']) and
            _zhi_ke(mo, env['ri_gan']) and _wx(mo) != _wx(env['ri_gan']))


def _sc_chu_sheng_zhong_sheng_mo(env):
    """初生中、中生末（递生模式A）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    return _zhi_sheng(sc[0], sc[1]) and _zhi_sheng(sc[1], sc[2])


def _sc_chu_ke_zhong_ke_mo(env):
    """初克中、中克末（递克模式A）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    return _zhi_ke(sc[0], sc[1]) and _zhi_ke(sc[1], sc[2])


def _sc_mo_sheng_zhong_sheng_chu(env):
    """末生中、中生初（递生模式B：逆递生）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    return _zhi_sheng(sc[2], sc[1]) and _zhi_sheng(sc[1], sc[0])


def _sc_mo_ke_zhong_ke_chu(env):
    """末克中、中克初（递克模式B：逆递克）"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    return _zhi_ke(sc[2], sc[1]) and _zhi_ke(sc[1], sc[0])


def _x_sheng_chu(env, x):
    """x 生初传"""
    sc = env.get('sanchuan', [])
    return bool(x) and len(sc) == 3 and _zhi_sheng(x, sc[0])


def _x_sheng_mo(env, x):
    """x 生末传"""
    sc = env.get('sanchuan', [])
    return bool(x) and len(sc) == 3 and _zhi_sheng(x, sc[2])


def _x_ke_chu(env, x):
    """x 克初传"""
    sc = env.get('sanchuan', [])
    return bool(x) and len(sc) == 3 and _zhi_ke(x, sc[0])


def _x_ke_mo(env, x):
    """x 克末传"""
    sc = env.get('sanchuan', [])
    return bool(x) and len(sc) == 3 and _zhi_ke(x, sc[2])


def _mo_sheng_gan(env):
    """末传生日干"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(sc[2], env['ri_gan'])


def _chu_sheng_gan(env):
    """初传生日干"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(sc[0], env['ri_gan'])


def _mo_ke_gan(env):
    """末传克日干"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(sc[2], env['ri_gan']) and _wx(sc[2]) != _wx(env['ri_gan'])


def _chu_ke_gan(env):
    """初传克日干"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(sc[0], env['ri_gan']) and _wx(sc[0]) != _wx(env['ri_gan'])


# ── 三传内部生克关系（用于"末助初""递生/递克""苦去甘来"等变格判断）──
def _mo_sheng_chu(env):
    """末传生初传（末助初的基础）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(sc[2], sc[0])


def _mo_ke_chu(env):
    """末传克初传（苦去甘来的基础：末克初）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(sc[2], sc[0]) and _wx(sc[2]) != _wx(sc[0])


def _zhong_sheng_chu(env):
    """中传生初传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(sc[1], sc[0])


def _zhong_ke_chu(env):
    """中传克初传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(sc[1], sc[0]) and _wx(sc[1]) != _wx(sc[0])


def _zhong_sheng_mo(env):
    """中传生末传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(sc[1], sc[2])


def _zhong_ke_mo(env):
    """中传克末传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(sc[1], sc[2]) and _wx(sc[1]) != _wx(sc[2])


def _gan_sheng_chu(env):
    """日干生初传（父母爻之象）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(env['ri_gan'], sc[0])


def _gan_sheng_zhong(env):
    """日干生中传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(env['ri_gan'], sc[1])


def _gan_sheng_mo(env):
    """日干生末传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(env['ri_gan'], sc[2])


def _gan_ke_chu(env):
    """日干克初传（初传为日干之财）"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(env['ri_gan'], sc[0]) and _wx(sc[0]) != _wx(env['ri_gan'])


def _zhi_sheng_chu(env):
    """日支生初传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_sheng(env['ri_zhi'], sc[0])


def _zhi_ke_chu(env):
    """日支克初传"""
    sc = env.get('sanchuan', [])
    return bool(sc) and len(sc) == 3 and _zhi_ke(env['ri_zhi'], sc[0]) and _wx(sc[0]) != _wx(env['ri_zhi'])


def _mo_zhu_chu_sheng_gan(env):
    """末助初生日：末传生初传，初传又生日干（傍有人助而亨旺）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    return _zhi_sheng(sc[2], sc[0]) and _zhi_sheng(sc[0], env['ri_gan'])


def _mo_zhu_chu_ke_gan(env):
    """末助初克干：末传生初传，初传又克日干（教唆词讼之人）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    return _zhi_sheng(sc[2], sc[0]) and _zhi_ke(sc[0], env['ri_gan']) and _wx(sc[0]) != _wx(env['ri_gan'])


def _mo_zhu_chu_zuo_cai(env):
    """末助初作财：末传生初传，初传为日干之财（暗有人以财相助）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    return _zhi_sheng(sc[2], sc[0]) and _zhi_ke(env['ri_gan'], sc[0]) and _wx(sc[0]) != _wx(env['ri_gan'])


def _en_duo_yuan_shen(env):
    """恩多怨深：干生初、初生中、中生末、末克干（恩中有怨）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    return (_zhi_sheng(env['ri_gan'], sc[0]) and
            _zhi_sheng(sc[0], sc[1]) and
            _zhi_sheng(sc[1], sc[2]) and
            _zhi_ke(sc[2], env['ri_gan']) and _wx(sc[2]) != _wx(env['ri_gan']))


def _ku_qu_gan_lai(env):
    """苦去甘来：末传克初传，初传又转生日干"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    return (_zhi_ke(sc[2], sc[0]) and _wx(sc[2]) != _wx(sc[0]) and
            _zhi_sheng(sc[0], env['ri_gan']))


def _liang_gui_jia_gan(env):
    """两贵拱干：干上、支上俱乘贵人（两贵引从）"""
    tj = env.get('tian_jiang', {})
    return bool(tj.get(env.get('gan_shang', '')) == '贵人' and
                tj.get(env.get('zhi_shang', '')) == '贵人')


def _liang_she_jia_mu(env):
    """两蛇夹墓（第53法 两蛇夹墓凶难免）：日干之墓临干或支，且墓神乘螣蛇。
    原文「丙戌日戌加巳及支辰来墓日干，兼昼夜天将皆乘蛇」；如占病积块在腹。
    【P4 收敛 2026-09-03】原判据「初末传同为墓乘蛇」结构上永不可能（初末同支且皆乘蛇）→
    按原文改判「墓临干/支乘螣蛇」（对齐 _liang_she_jia_mu_v2）。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or (not gs and not zs):
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    mu_zhi = gs if gs == mu else (zs if zs == mu else '')
    if not mu_zhi:
        return False
    return env.get('tian_jiang', {}).get(mu_zhi, '') == '螣蛇'


def _liang_hu_jia_mu(env):
    """两虎夹墓（第53法）：日干之墓临干或支，且墓神乘白虎。
    原文「六辛日丑加申两虎夹墓」（辛墓=丑，丑加申=干上乘白虎）。
    【P4 收敛 2026-09-03】原判据「初末同为墓乘白虎」结构不可能 → 按原文改判。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or (not gs and not zs):
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    mu_zhi = gs if gs == mu else (zs if zs == mu else '')
    if not mu_zhi:
        return False
    return env.get('tian_jiang', {}).get(mu_zhi, '') == '白虎'


def _liang_kong_jia_mu(env):
    """两空夹墓（第53法）：日干之墓临干或支，且墓神乘天空。
    原文「六甲日未加戌昼贵，两空夹墓」（甲墓=未，未加戌乘天空）。
    【P4 收敛 2026-09-03】原判据「初末同为墓乘天空」结构不可能 → 按原文改判。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or (not gs and not zs):
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    mu_zhi = gs if gs == mu else (zs if zs == mu else '')
    if not mu_zhi:
        return False
    return env.get('tian_jiang', {}).get(mu_zhi, '') == '天空'


def _liang_chang_jia_mu(env):
    """两常夹墓（第53法 两蛇夹墓·外变）：六己日，干墓辰加临干或支，且辰乘太常。
    毕法赋「外有六己日辰加未夜占，乃两常夹墓」（己土墓辰，辰乘太常=「两常」）。
    【B5a 2026-09-03】原规则误用 tian_gang_bi_gan（天罡断男女法）→ 按原文独立判据。"""
    if env.get('ri_gan', '') != '己':
        return False
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    mu_zhi = gs if gs == '辰' else (zs if zs == '辰' else '')
    if not mu_zhi:
        return False
    return env.get('tian_jiang', {}).get(mu_zhi, '') == '太常'


def _liang_hou_jia_mu(env):
    """两后夹墓：六壬日，干墓辰加临干或支，且辰乘天后。
    毕法赋「六壬日辰加亥乃两后夹墓」（壬水墓辰，辰乘天后=「两后」）。
    【B5a 2026-09-03】原规则误用 tian_gang_bi_gan → 按原文独立判据。"""
    if env.get('ri_gan', '') != '壬':
        return False
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    mu_zhi = gs if gs == '辰' else (zs if zs == '辰' else '')
    if not mu_zhi:
        return False
    return env.get('tian_jiang', {}).get(mu_zhi, '') == '天后'


def _zhi_shang_sheng_gan(env):
    """支上神生日干（避难逃生·支上受生）"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    return bool(zs and _zhi_sheng(zs, env['ri_gan']))


def _gan_shang_sheng_gan(env):
    """干上神生日干（避难逃生·干上受生）"""
    gs = env.get('gan_shang', '')
    return bool(gs and _zhi_sheng(gs, env['ri_gan']))


def _zhi_shang_ke_gan(env):
    """支上神克日干（前后逼迫·支上克干）"""
    zs = env.get('zhi_shang', '')
    return bool(zs and _zhi_ke(zs, env['ri_gan']) and _wx(zs) != _wx(env['ri_gan']))


def _gan_shang_ke_gan(env):
    """干上神克日干（舍益就损·不受福德 / 一喜一悲 用）"""
    gs = env.get('gan_shang', '')
    return bool(gs and _zhi_ke(gs, env['ri_gan']) and _wx(gs) != _wx(env['ri_gan']))


def _gan_zhi_shang_jie_ke_gan(env):
    """干上、支上俱克日干（前后逼迫·全伤坐克）"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    return (bool(gs and _zhi_ke(gs, env['ri_gan']) and _wx(gs) != _wx(env['ri_gan'])) and
            bool(zs and _zhi_ke(zs, env['ri_gan']) and _wx(zs) != _wx(env['ri_gan'])))


def _san_chuan_wu_yi_shou_sheng(env):
    """三传无益（三传俱不生干，须就干上或支上受生）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan = env['ri_gan']
    return not any(_zhi_sheng(z, gan) for z in sc)


def _sc_ju_wx(sc):
    """三传成三合局→局五行；不成局→''。毕法赋六爻现卦示例均为三合局（卯亥未木局/巳酉丑金局/寅午戌火局/申子辰水局）。"""
    if not sc or len(sc) != 3:
        return ''
    for s in SANHE:
        if set(sc) == s:
            return _SANHE_WX[next(z for z in s)]
    return ''


def _bi_nan_tao_sheng(env):
    """第9法「避难逃生须弃旧」专用谓词（2026-09-21 按原文格义重建）

    原文（在线_bifa_sina.html L398 起）：三传既无所益，不免弃三传而「就」别处受生。
      A  避难逃生格：三传皆无益（不生日干，且非实财／财而旬空），而**干上神**生日干
         ——甲子日干上子、三传戌申午「戌虽曰日财乃是旬空，申又是日鬼，午作脱气…
           不免只就干上子水而受生」。
      A2 同格变体：三传皆无益，而**日支（日干所坐地盘）**生日干
         ——甲子日辰加寅为初传，三传辰午申（辰虽曰日财，奈昼夜天将皆是六合，
           其财受上下夹克，终不可得）「不免日干就子支上而受生」。
      A3 避难逃生**得财**格：三传皆无益，弃三传而日干加日支**取财**
         ——壬午日三传辰酉寅「弃墓而投中传酉金之生（又是旬空），遂再投末传寅木
           （又是脱气），然后弃其三传，而壬干加午而取财也」。
      B  三传成局皆作脱气（局五行＝我生者），而支上／日支／干上有生可就
         ——庚子日子加申「三传水局皆作脱气…天盘申金坐于辰土之上就生」。
      ⛔ 原文**反例**必须不命中（否则判据过宽）：
         丁亥日三传午戌寅——原文明言「避难逃生而**终不能逃生者**」（寅实生丁，非皆无益）；
         乙酉日三传亥午丑——原文「**舍就皆不可**格」（亥实生乙，非皆无益）。
    【无益判据】z 生日干而旬空／为财而（旬空·落空地·受上下夹克）／不生日干（鬼·脱·比和）。
    """
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    ri_zhi = env.get('ri_zhi', '')
    if not gan or len(sc) != 3:
        return False
    kong = env.get('kongwang') or ('', '')
    tdp = env.get('tiandi_pan') or {}
    tj = env.get('tian_jiang') or {}
    di_of = {v: k for k, v in tdp.items() if v}      # 天盘支 → 所临地盘

    def sheng_gan(z):                       # z 生日干
        return bool(z) and _zhi_sheng(z, gan)

    def is_cai(z):                          # 日干克 z ⇒ 妻财
        return bool(z) and _zhi_ke(gan, z)

    def jia_ke(z):                          # 财受上下夹克：天将五行克 z 且所临地盘五行克 z
        if not z:
            return False
        di = di_of.get(z, '')
        up = TIANJIANG_WX_MAP.get(tj.get(z, ''), '')
        if not di or not up:
            return False
        zw = _wx(z)
        return WX_KE.get(up, '') == zw and WX_KE.get(_wx(di), '') == zw

    def wuyi(z):                            # 无益（不可就）
        if not z:
            return False
        if sheng_gan(z):
            return z in kong                              # 生我而旬空 ⇒ 不能就
        if is_cai(z):
            return (z in kong) or (di_of.get(z, '') in kong) or jia_ke(z)
        return True                                       # 鬼／脱气／比和 ⇒ 无益

    # A / A2 / A3
    if all(wuyi(z) for z in sc):
        if gs and sheng_gan(gs):
            return True
        if ri_zhi and sheng_gan(ri_zhi):
            return True
        if ri_zhi and is_cai(ri_zhi):       # A3：弃三传而日干加日支取财
            return True
    # B：三传成局作脱气，而别处有生可就
    ju = _sc_ju_wx(sc)
    if ju and WX_SHENG.get(_wx(gan), '') == ju:
        if (zs and sheng_gan(zs)) or (ri_zhi and sheng_gan(ri_zhi)) or (gs and sheng_gan(gs)):
            return True
    return False


def _zhuan_cai_hua_gui(env):
    """第27法「传财化鬼财休觅」专用谓词（2026-09-21 按原文五格重建）

    原文（在线_bifa_sina.html L915 起）五格，实测覆盖该法全部 10/10 课：
      A  主格·传财化鬼：三传作日之财（逐传皆财 **或** 三合成财局），其财生起**干上神**，
         而干上神克日干（为鬼）——辛亥日干上午、三传未卯亥「皆作木局为日之财…
         即生起干上之午火」；丁丑日干上亥、三传酉丑巳（金局为丁之财，金生亥水克丁）。
      A2 三传成局生日干、而干上见鬼——「丁酉日干上亥，三传亥卯未全生，但日上见鬼耳」。
      B  传财化鬼格：三传作财，反生起**支上神**而克日干——乙巳日三传未戌丑、支上申；
         丁亥日三传申酉戌、支上子。
      C  四己日：干上神为日之财，而三传成局来伤（克）日干——己卯日干上亥、三传曲直木局伤干。
      D  因财致祸格：三传中财爻反克干上之神——庚辰日干上丑、初传寅木为财而伤干上丑土。
      E  借钱还债格：干上神与支上神**皆为日之财**——辛酉日干上卯支上寅；壬子日干上巳支上午。
    """
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or len(sc) != 3 or not gs:
        return False

    def is_cai(z):                      # 日干克该支 ⇒ 妻财
        return bool(z) and _zhi_ke(gan, z)

    ju_wx = _sc_ju_wx(sc)               # 三合成局 → 局五行；不成局 → ''
    # 🔴 财的五行集合：① 三合成财局；② 三传中任一传为日之财。
    #    ⛔ 不能只取「逐传皆财/成财局」——原文丁亥日三传申酉戌（戌为土非财）
    #       明言「支上子…惟宜纳粟得官」，财只取申酉，故须逐传兜底。
    cai_wxs = set()
    if ju_wx and WX_KE.get(_wx(gan), '') == ju_wx:
        cai_wxs.add(ju_wx)
    for z in sc:
        if is_cai(z):
            cai_wxs.add(_wx(z))

    # A：财（或财局）生干上神，干上神克日干
    if _zhi_ke(gs, gan) and any(WX_SHENG.get(w, '') == _wx(gs) for w in cai_wxs):
        return True
    # A2：三传成局生日干，而干上见鬼
    if ju_wx and WX_SHENG.get(ju_wx, '') == _wx(gan) and _zhi_ke(gs, gan):
        return True
    # B：财（或财局）生支上神，支上神克日干
    if zs and _zhi_ke(zs, gan) and any(WX_SHENG.get(w, '') == _wx(zs) for w in cai_wxs):
        return True
    # C：干上神为财，三传成局克日干
    if is_cai(gs) and ju_wx and WX_KE.get(ju_wx, '') == _wx(gan):
        return True
    # D：三传中财爻克干上神
    if any(is_cai(z) and _zhi_ke(z, gs) for z in sc):
        return True
    # E：干上、支上皆日之财
    if zs and is_cai(gs) and is_cai(zs):
        return True
    return False


def _liu_yao_xian_gua_father(env):
    """父母爻现卦：三传成三合局，局五行生日干（毕法赋"三传皆作父母爻"。
    如戊寅日三传戌午寅火局，戊土受生。）"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gan_wx = _wx(env.get('ri_gan', ''))
    return bool(jw and gan_wx and WX_SHENG.get(jw, '') == gan_wx)


def _liu_yao_xian_gua_offspring(env):
    """子息爻现卦：三传成三合局，局五行日干所生（毕法赋"三传皆作子息爻"。
    如己巳日三传酉丑巳金局，己土生金。）"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gan_wx = _wx(env.get('ri_gan', ''))
    return bool(jw and gan_wx and WX_SHENG.get(gan_wx, '') == jw)


def _liu_yao_xian_gua_official(env):
    """官鬼爻现卦：三传成三合局，局五行克日干（毕法赋"三传皆鬼"。
    如乙丑日三传巳丑酉金局，金克乙木。）"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gan_wx = _wx(env.get('ri_gan', ''))
    return bool(jw and gan_wx and WX_KE.get(jw, '') == gan_wx)


def _liu_yao_xian_gua_wealth(env):
    """妻财爻现卦：三传成三合局，局五行被日干所克（毕法赋"三传俱作日之财"。
    如辛未日三传卯亥未木局，辛金克木。）"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gan_wx = _wx(env.get('ri_gan', ''))
    return bool(jw and gan_wx and WX_KE.get(gan_wx, '') == jw)


def _liu_yao_xian_gua_brother(env):
    """兄弟爻现卦：三传成三合局，局五行与日干同类（毕法赋"三传皆是日之同类"。
    如丙寅日三传戌午寅火局，丙火同类。）"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gan_wx = _wx(env.get('ri_gan', ''))
    return bool(jw and gan_wx and jw == gan_wx)


def _san_chuan_sheng_gan_shang(env):
    """六爻相生而成类：三传（三合局）生起干上之爻象（毕法赋"乃三传生起干上之爻象者"）。"""
    jw = _sc_ju_wx(env.get('sanchuan', []))
    gs_wx = _wx(env.get('gan_shang', ''))
    return bool(jw and gs_wx and WX_SHENG.get(jw, '') == gs_wx)


def _bingfu_wuyin(env):
    """夫妇芜淫：干上与支上互克（各有私情之象）"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gs or not zs:
        return False
    return (_zhi_ke(gs, env['ri_zhi']) and _zhi_ke(zs, env['ri_gan']))


def _ren_zhai_zuo_mu(env):
    """人宅坐墓：干上、支上俱为日干之墓（甘招晦）"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    return gs == mu and zs == mu


def _gan_zhi_cheng_mu(env):
    """干支乘墓：干上、支上俱为日干之墓（各昏迷）"""
    return _ren_zhai_zuo_mu(env)


def _zhi_cheng_mu_hu(env):
    """支乘墓虎：支上为日干之墓乘白虎（有伏尸）"""
    zs = env.get('zhi_shang', '')
    mu = WX_MU.get(_wx(env['ri_zhi']), '')  # 支墓
    if not mu:
        return False
    tj = env.get('tian_jiang', {})
    return zs == mu and tj.get(zs) == '白虎'


def _zhi_fen_cai_bing(env):
    """支坟财并：支上为日干之墓又是日干之财（旅程稽留）"""
    zs = env.get('zhi_shang', '')
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu or zs != mu:
        return False
    return _zhi_ke(env['ri_gan'], zs) and _wx(zs) != _wx(env['ri_gan'])


def _shu_zhai_kuan_guang(env):
    """屋宅宽广致人衰：支上为日干之墓（宅克人）"""
    zs = env.get('zhi_shang', '')
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    return zs == mu


def _shu_zhai_xia_zhai(env):
    """眷属丰盈居狭宅：干上为日干之财（人克宅）"""
    gs = env.get('gan_shang', '')
    if not gs:
        return False
    return _zhi_ke(env['ri_gan'], gs) and _wx(gs) != _wx(env['ri_gan'])


def _tai_yang_she_zhai(env):
    """太阳射宅：支上乘太阴或太阳临支（屋光辉）"""
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    return tj.get(zs) == '太阴' or tj.get(zs) == '太阳'


def _qi_xing_nian_shang_yang_tian_yang(env):
    """太阳临年命（旧别名，已存在 qi_xing_nian_shang_yang，此处略）"""
    return False


def _gang_se_gui_hu(env):
    """罡塞鬼户：天罡（辰）加临鬼户（寅）。
    通解「辰为天罡，寅为鬼户，凡辰加寅为罡塞鬼门，不论在传不在传，皆名罡塞鬼户」。
    【B5a 2026-09-03】原判据含 '申'，与原文「鬼户为寅」不符，过宽 → 严格只判寅。"""
    d = _tian_gang_jia(env)
    return d == '寅'


def _tian_wang_zi_guo(env):
    """天网自裹：干上为日干之墓（己招非）"""
    gs = env.get('gan_shang', '')
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    return gs == mu


def _gui_lin_san_si(env):
    """鬼临三四：三四课（即支上）有克日干者（讼灾随）"""
    zs = env.get('zhi_shang', '')
    return bool(zs and _zhi_ke(zs, env['ri_gan']) and _wx(zs) != _wx(env['ri_gan']))


def _bi_kou_gua(env):
    """闭口卦：初传为旬尾或干上为旬尾"""
    sc = env.get('sanchuan', ['', '', ''])
    kong = env.get('kongwang', ('', ''))
    return bool(sc and len(sc) == 3 and sc[0] in kong) or _x_kong(env, '初')


def _gan_zhi_jue(env):
    """干支值绝：干上、支上俱为日干之绝位"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    jwx = JUE_WX.get(_wx(env['ri_gan']))
    if isinstance(jwx, tuple):
        return gs in jwx and zs in jwx
    return bool(jwx and gs == jwx and zs == jwx)


def _gan_zhi_jie_bai(env):
    """干支皆败：干上、支上俱为日干之败气（沐浴位）"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    bwx = BAI_WX.get(_wx(env['ri_gan']))
    if isinstance(bwx, tuple):
        return gs in bwx and zs in bwx
    return bool(bwx and gs == bwx and zs == bwx)


def _tuo_shang_feng_tuo(env):
    """脱上逢脱：干上为日干生者（脱耗），又见三传脱干"""
    gs = env.get('gan_shang', '')
    sc = env.get('sanchuan', [])
    gan = env['ri_gan']
    if not (gs and _zhi_sheng(gan, gs)):
        return False
    return any(_zhi_sheng(gan, z) for z in sc) if sc and len(sc) == 3 else False


def _chuan_gui_hua_cai(env):
    """传鬼化财：三传初鬼末财（初传克干，末传为干之财）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    gan = env['ri_gan']
    return (_zhi_ke(sc[0], gan) and _wx(sc[0]) != _wx(gan) and
            _zhi_ke(gan, sc[2]) and _wx(sc[2]) != _wx(gan))


def _chuan_mu_ru_mu(env):
    """传墓入墓：初传（财/长生/禄）被中/末传墓入。
    毕法赋第八十一法：「生我者传墓入墓，如辛未日，三传巳戌卯，巳加子为初传，乃日之长生，
    岂宜中传戌来墓巳，末传又入戌乡」→ 判据=初传五行之墓 == 中传或末传。
    【BUG-FIX 2026-09-01】原实现"初末传同为日干之墓"在8640课内0命中（初末同支本就罕见，
    同为墓更不可能）→ 死规则；按原文改为"初传入墓"（初传五行墓于中末传）。"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    chu_wx = _wx(sc[0])
    if not chu_wx:
        return False
    mu = WX_MU.get(chu_wx, '')  # 初传五行之墓
    return bool(mu) and mu in sc[1:]


def _chu_zao_jia_ke(env):
    """初遭夹克：初传上下俱受克（不由己）—— 上=天将克初，下=地盘克初（毕法赋·初遭夹克不由己）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    chu = sc[0]
    tj = env.get('tian_jiang', {})
    tdp = env.get('tiandi_pan', {})
    jiang_wx = TIANJIANG_WX_MAP.get(tj.get(chu, ''), '')
    chu_wx = _wx(chu)
    if not jiang_wx or not chu_wx:
        return False
    # 【BUG-FIX 2026-09-01】jiang_wx 已是五行值，不能套 _zhi_ke（会对五行再 _wx → 恒空串且恒真/恒假）；
    # 原 v1"上克"因双重 _wx 恒真 + 下克还误容"初克日干"，导致 初遭夹克系 4 条规则 52.8% 误命中。
    # 现按毕法原义：上=天将五行克初传五行，下=地盘（初传下坐之支）五行克初传五行。
    if WX_KE.get(jiang_wx, '') != chu_wx:
        return False
    dipan = ''
    for dp, tp in (tdp or {}).items():
        if tp == chu:
            dipan = dp
            break
    return bool(dipan and WX_KE.get(_wx(dipan), '') == chu_wx)


def _bing_fu_ke_zhai(env):
    """病符克宅：病符（旧太岁）临支克宅"""
    zs = env.get('zhi_shang', '')
    tai_sui = env.get('tai_sui', '')
    prev_ts = DIZHI_TAI_SUI_PREV.get(tai_sui, '') if tai_sui else ''
    # 旧太岁（病符）临支上且支上神克宅（日支）
    return bool(prev_ts and zs == prev_ts and _zhi_ke(zs, env['ri_zhi']))


def _sang_diao_quan_feng(env):
    """丧吊全逢：丧门、吊客俱现（挂缟衣）"""
    shensha = env.get('shensha', {})
    has_sang = any('丧门' in v for v in shensha.values())
    has_diao = any('吊客' in v for v in shensha.values())
    return has_sang and has_diao


def _hou_po_bi_po(env):
    """前后逼迫：初传前克、末传后克（难进退）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    # 初传被前克（天将克初）+ 末传被后克（天将克末）= 前后逼迫
    tj = env.get('tian_jiang', {})
    jiang_chu = TIANJIANG_WX_MAP.get(tj.get(sc[0], ''), '')
    jiang_mo = TIANJIANG_WX_MAP.get(tj.get(sc[2], ''), '')
    chu_wx = _wx(sc[0])
    mo_wx = _wx(sc[2])
    # 【BUG-FIX 2026-09-01】jiang_* 已是五行值，若再套 _zhi_ke 会对五行取 _wx → 恒为空，
    # `WX_KE.get('','')==''` 恒真 → 前后逼迫/顾祖格 100% 命中。改为五行表直接比较。
    return (bool(jiang_chu and WX_KE.get(jiang_chu, '') == chu_wx) and
            bool(jiang_mo and WX_KE.get(jiang_mo, '') == mo_wx))


def _hu_shi_peng_hu(env):
    """虎视逢虎：白虎乘临旺相（力难施）"""
    tj = env.get('tian_jiang', {})
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    has_hu = any(tj.get(z) == '白虎' for z in sc)
    # 【BUG-FIX 2026-09-01】'初' 是相对标记，须先 _resolve 成实际地支再判旺相；
    # 原实现直传 '初' → _wx('初')='' 恒假 → 刚日昴星/多重虎 2 位点断链。
    return has_hu and _x_wang_xiang(env, _resolve('初', env))


def _bai_hu_lin_gan(env):
    """白虎临干（干上乘白虎）：占病主魂游千里（白虎临身之象）。
    【B5a 2026-09-03】原规则共享 tianjiang_ru_chuan(白虎) 过宽 → 收窄为白虎加临日干。"""
    gs = env.get('gan_shang', '')
    if not gs:
        return False
    return env.get('tian_jiang', {}).get(gs, '') == '白虎'


def _dun_gan(env, z):
    """地支 z 在日干所在旬中的遁干（旬首甲起顺行数至 z）"""
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    if not gan or not rz or not z:
        return ''
    GAN_S = '甲乙丙丁戊己庚辛壬癸'
    ZHI_S = '子丑寅卯辰巳午未申酉戌亥'
    try:
        g_i = GAN_S.index(gan)
        z_i = ZHI_S.index(rz)
    except ValueError:
        return ''
    xun_z = ZHI_S[(z_i - g_i) % 12]  # 甲旬首地支
    step = (ZHI_S.index(z) - ZHI_S.index(xun_z)) % 12
    return GAN_S[step % 10]


def _hu_cheng_dun_gui(env):
    """虎乘遁鬼（第69法 虎乘遁鬼殃非浅）：白虎所乘之神（六处），其遁干为日干之鬼。
    毕法赋「白虎加临旬内之干为日鬼者例，纵空亡亦不能为救」。
    【B5a 2026-09-03】原规则共享 tianjiang_ru_chuan(白虎) 过宽 → 按原文判遁鬼。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    tj = env.get('tian_jiang', {})
    spots = []
    for z in (env.get('gan_shang', ''), env.get('zhi_shang', '')):
        if z:
            spots.append(z)
    spots += list(env.get('sanchuan') or [])
    for z in spots:
        if not z or tj.get(z, '') != '白虎':
            continue
        g = _dun_gan(env, z)
        if g and WX_KE.get(_wx(g), '') == _wx(gan):
            return True
    return False


def _hu_shi_feng_hu(env):
    """虎视逢虎力难施（第54法）：柔日昴星课（虎视课）+ 白虎乘临干上或三传。
    毕法赋「虎视课者，乃柔日也。如柔日虎视卦中，天将又乘白虎者，凡占至惊至危」。
    【B5a 2026-09-03】原规则共享 tianjiang_ru_chuan(白虎) 过宽 → 加课体(柔日昴星)限定。"""
    if env.get('ri_gan', '') not in '乙丁己辛癸':
        return False
    if '昴星' not in env.get('keti', ''):
        return False
    tj = env.get('tian_jiang', {})
    spots = [env.get('gan_shang', '')] + list(env.get('sanchuan') or [])
    return any(z and tj.get(z, '') == '白虎' for z in spots)


def _zun_chong_san_qi(env):
    """尊崇三奇：三奇入传"""
    return _chu_ji(env) or _chu_meng(env) or _chu_zhong(env)


def _yi_zai_xiong_tao(env):
    """已灾凶逃：三传见鬼墓又空（返无疑）
    【B5b 2026-09-03】原判据「三传见鬼又墓/空」过宽 → 已灾逢凶可消格改用课体凶否卦判据
    （ke_xiong_qi_gua），本函数保留用于 64 课格佐证，不再被通用规则引用。"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    gan = env['ri_gan']
    has_gui = any(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)
    has_mu = bool(mu and any(z == mu for z in sc))
    has_kong = any(z in (env.get('kongwang') or ('', '')) for z in sc)
    return has_gui and (has_mu or has_kong)


_XIONG_QI_GUA = ('天网', '魄化', '天祸', '天寇', '二烦', '天狱')


def _ke_xiong_qi_gua(env):
    """已灾逢凶可消：课体为凶否之卦（第100法 已灾凶逃返无疑）。
    原文「凡值丧魂、魄化、天祸、天寇、伏殃、天狱、天网四张、天地二烦诸凶否卦，
    如已见病讼灾迍之后占得此，其灾可消除」。取 64 课引擎可判定的凶卦课体名。
    【B5b 修正】不含「灾厄」课体——灾厄课判据为"凶将（白虎/玄武/勾陈/螣蛇/朱雀/天空）
    发用"过于宽泛（8640课占 29.9%），与原文特指的凶否之卦（魄化/天网/天狱/二烦等）
    不同质，剔除后仅按原文名单匹配。"""
    kt = env.get('keti', '')
    return any(x in kt for x in _XIONG_QI_GUA)


def _gan_shang_jue(env):
    """干上为日干之绝位（结绝格：如六丙日干上亥，火绝于亥）。"""
    gs = env.get('gan_shang', '')
    if not gs:
        return False
    jwx = JUE_WX.get(_wx(env.get('ri_gan', '')))
    if not jwx:
        return False
    return gs in jwx if isinstance(jwx, tuple) else gs == jwx


def _le_li_sheng_you(env):
    """乐里生忧（第34法 苦去甘来乐里悲）：干上=干之长生、支上=支之长生，
    然干生支上（干被支上脱）、支生干上（支被干上脱），两边互盗。
    原文「庚寅日干上巳乃庚金之长生，支上亥乃寅木之长生，递互相参，
    庚金反被亥水脱，寅木又被巳火脱，两边脱盗，凡占皆然」。
    【B5b】原规则共享 tianjiang_ru_chuan(玄武) → 按原文精确落地。"""
    gan, rz = env.get('ri_gan', ''), env.get('ri_zhi', '')
    gs, zs = env.get('gan_shang', ''), env.get('zhi_shang', '')
    if not all((gan, rz, gs, zs)):
        return False

    def _cs(wx):
        v = CHANG_SHENG.get(wx, '')
        return v[0] if isinstance(v, tuple) else v

    if gs != _cs(_wx(gan)) or zs != _cs(_wx(rz)):
        return False
    return _zhi_sheng(gan, zs) and _zhi_sheng(rz, gs)


def _zhi_jia_gan_shang_sheng_gan(env):
    """自在格（第77法 互生俱生凡事益）：支加干上生日。
    原文「甲子、乙亥、丙寅、丁卯、戊午、己巳、庚辰、辛未、壬申、癸酉十日，
    并支加干上而生日也」→ 判据：干上神=日支，且日支生日干。
    【B5b】原用 zhi_shang_sheng_gan（任何支上神生干）过宽 → 精确为支加干上。"""
    gan, rz = env.get('ri_gan', ''), env.get('ri_zhi', '')
    gs = env.get('gan_shang', '')
    return bool(gs == rz and _zhi_sheng(rz, gan))


def _zhi_gan_shang_xiang_sheng(env):
    """支干相生（第31法 三传递生人举荐·变例）：支上生干上，干上生日干。
    原文「壬戌日干上申，支上未土生申金，金来生日」→ 支上→干上→干 顺生。
    【B5b】原用 zhi_shang_sheng_gan 过宽（只查一段生） → 要求两段连生。"""
    gan = env.get('ri_gan', '')
    gs, zs = env.get('gan_shang', ''), env.get('zhi_shang', '')
    return bool(gs and zs and _zhi_sheng(zs, gs) and _zhi_sheng(gs, gan))


def _lan_qu_qu_cai(env):
    """懒去取财：干上为日干之比肩（劫财），传内又见财爻。
    原文「懒去取财格：六甲日干上寅或卯，纵传内见财爻，如求财，必心多退悔，
    懒去取财，恐争夺也。余日逐类看所乘何神而言其事类」——六甲日干上寅卯
    即甲木比肩，比肩夺财故懒去取财。推广到余日：干上比劫 + 传中见财。
    【B5c】原规则共享 gan_ke_x(初)（26.53% 过宽）→ 按原文精确落地。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    sc = env.get('sanchuan', [])
    if not gan or not gs or len(sc) != 3:
        return False
    if _wx(gs) != _wx(gan):
        return False
    return any(_x_shi_cai(env, z) for z in sc)


def _san_chuan_cheng_tu(env):
    """土将助财·严格版：三传所乘天将皆为土神（贵人/勾陈/天空/太常）。
    原文「土将助财格：如六丙日酉加巳，三传皆财，夜将又皆土神，尽生起财神，
    大宜求财事」→ sc_quancai 由规则声明式 AND 保证，本谓词仅判三传皆乘土将。
    【B5c】⚠️ 全样本 8640 课验证：三传皆财时「皆乘土将」结构性恒假（0 命中，
    sc_quancai 180 课中天将土神个数分布 0:132/1:48/2:0/3:0），此严格版保留原义
    但不可达；规则改用 san_chuan_yi_tu 可达版。"""
    sc = env.get('sanchuan', ['', '', ''])
    tj = env.get('tian_jiang', {}) or {}
    if len(sc) != 3:
        return False
    return all(TIANJIANG_WX_MAP.get(tj.get(z, ''), '') == '土' for z in sc)


def _san_chuan_yi_tu(env):
    """土将助财·可达版：三传所乘天将中至少一传为土神（贵人/勾陈/天空/太常）。
    【B5c】严格版「皆乘土将」全样本验证恒假（土神数 2/3 分布均为 0 课）→ 按批次4
    死规则改写先例，降为「至少一传乘土将」，保「三传皆财」稀缺性判定 + 土将生财意象。
    注：三传皆财仅见于特殊课型（乙丑日三传皆土等，8640 课共 180 课），组合命中率实测 ~0.56%。"""
    sc = env.get('sanchuan', ['', '', ''])
    tj = env.get('tian_jiang', {}) or {}
    if len(sc) != 3:
        return False
    return any(TIANJIANG_WX_MAP.get(tj.get(z, ''), '') == '土' for z in sc)


def _zhong_gui_bu_wei(env):
    """众鬼虽彰全不畏：三传俱克干，但末传空亡"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    gan = env['ri_gan']
    all_gui = all(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)
    kong = env.get('kongwang', ('', ''))
    return all_gui and sc[2] in kong


def _san_chuan_hu_ke(env):
    """三传互克：初克中、中克末（众人欺）"""
    return _sc_chu_ke_zhong_ke_mo(env)


def _wu_wang_jie_wang(env):
    """互旺皆旺：干支俱旺相（坐谋宜）"""
    # 【BUG-FIX 2026-09-01】'干上'/'支上' 是相对标记，须先 _resolve 成实际地支；
    # 原实现把字面量'干上'直接交给 _x_wang_xiang → _wx('干上')='' 恒假 → 互旺/皆旺格永不触发。
    gs = _resolve('干上', env)
    zs = _resolve('支上', env)
    return _x_wang_xiang(env, gs) and _x_wang_xiang(env, zs)


def _zhi_xuan_mu_hu_you_fu_shi(env):
    """支乘墓虎有伏尸：支上为日支墓乘白虎"""
    return _zhi_cheng_mu_hu(env)


def _tai_sui_yong_zhen(env):
    """太岁用神：初传为太岁或月建发用"""
    sc = env.get('sanchuan', ['', '', ''])
    tai_sui = env.get('tai_sui', '')
    return bool(sc and tai_sui and sc[0] == tai_sui)


def _shou_wei_xiang_jian(env):
    """首尾相见：初传末传相同（始终宜）"""
    sc = env.get('sanchuan', ['', '', ''])
    return bool(sc and len(sc) == 3 and sc[0] == sc[2])


def _you_shi_wu_zhong(env):
    """有始无终：初传实，末传空亡"""
    sc = env.get('sanchuan', ['', '', ''])
    kong = env.get('kongwang', ('', ''))
    return bool(sc and len(sc) == 3 and sc[0] not in kong and sc[2] in kong)


def _kong_kong_ru_ye(env):
    """第74法 空空如也事休追：**三传皆空**（复合口径）

    【BUG-FIX 2026-09-11（两次定义纠正）】
    第一次：我误以为「三传皆空」= 三传都落**旬空那 2 支** → 数学不可能（枚举可满足数=0）→ 误判"无解"
    第二次（憨爷指出）：实为**多种"空"叠加**，据《毕法赋》注解 + 《六壬大全》第十八法「踏脚空亡」：
      「指三传皆空，或两传空，一传不空而**上乘天空**者亦然」
      「如丁丑日第十二局，三传申酉戌：初传申空亡，中传酉空亡**又坐空**，末传戌**坐空**」
      「踏脚空亡格：如甲子日，**戌加子为初传，乃本旬之空；申加戌为中传，乃后旬之空；
        午加申为末传，乃外后旬之空亡**」

    **判据（任一传满足下列任一"空"即算该传为空）**：
      ① **旬空**：本支 ∈ 本旬空亡
      ② **坐空**：该支所临**地盘** ∈ 本旬空亡
      ③ **乘天空**：该支上乘天将「天空」
      ④ **踏空**：本支 ∈ **后旬 / 外后旬**空亡（分旬空亡，见《大全》第十八法）
    三传**全部**为空 → 触发。
    """
    sc = env.get('sanchuan', []) or []
    if len(sc) != 3:
        return False
    kong = env.get('kongwang', ('', '')) or ('', '')
    tdp = env.get('tiandi_pan', {}) or {}
    tj = env.get('tian_jiang', {}) or {}
    fxk = env.get('fen_xun_kong') or {}

    # 反查：天盘支 → 其所临地盘支
    fan = {}
    for dp, tp in tdp.items():
        if tp:
            fan.setdefault(tp, dp)

    # 分旬空亡集合（后旬 / 外后旬 / 前旬）
    hou = set(fxk.get('后旬') or [])
    waihou = set(fxk.get('外后旬') or [])
    qian = set(fxk.get('前旬') or [])
    ben = set(fxk.get('本旬') or [])
    kong_set = set(x for x in kong if x)
    if ben:
        kong_set |= ben
    # 【2026-09-11 实测留档·待憨爷拍板】④踏空（分旬空亡）为憨爷指定判据（见本函数 docstring
    #   「第二次（憨爷指出）：实为多种'空'叠加…据《六壬大全》第十八法踏脚空亡」），
    #   故**不擅自加前置条件**。补回缺失的 fen_xun_kong env 键后实测（8640 课式）：
    #     仅 ①②③（原状，键缺失→④恒假）      =  474 / 8640 =  5.5%
    #     ①②③④ 全开（憨爷判据真正生效）      = 3114 / 8640 = 36.0%
    #     ①②③④ 且 ④ 限于进退连茹/间传课      = 1164 / 8640 = 13.5%
    #   36.0% 作为「格」的出现率偏高（4 种空 OR 后的理论期望 ≈ 27~36%，属"判据本身宽松"
    #   而非实现错误）。是否给 ④ 加「进退连茹课」前提（原文「谓三传皆空亡者是也，
    #   **于进退连茹课中多有**」仅系统计性说明、非限定条件，第18法另有「四课三传俱退连茹」
    #   之限），留待憨爷定夺。

    def _is_kong(z):
        if not z:
            return False
        if z in kong_set:                 # ① 困空（含本旬）
            return True
        dp = fan.get(z, '')
        if dp and dp in kong_set:         # ② 坐空
            return True
        if tj.get(z) in ('天空',):        # ③ 乘天空
            return True
        if z in hou or z in waihou or z in qian:   # ④ 踏空（分旬空亡，憨爷判据）
            return True
        return False

    return all(_is_kong(z) for z in sc)


def _si_ke_all_kong(env):
    """第74法 空空如也事休追 · 「四课全空格：四课无形事不出名」

    【BUG-FIX 2026-09-11】本条原被误编译为 `kong_kong_ru_ye`（三传皆空）——
    实测 8640 课式中「三传皆空格 / 四课全空格 / 鬼空尤妙亦宜制之」三条命中数**完全相同（均 474）**，
    即三条规则共用同一谓词 → 「四课全空」名不副实（只要三传皆空就报四课全空）。

    **权威判据**（《毕法赋》第74法「空空如也事休追」原注例，data/bifa_100_knowledge_base.json rules[73]）：
      「**乙巳日干上寅空亡，第二课又入空亡，支上卯作空亡第四课又空亡，四课皆空**。」
    → 判据 = **四课上神（干上/第二课/支上/第四课）全部落旬空**；缺课（不足四课）不算。
    """
    kong = set(x for x in (env.get('kongwang') or ('', '')) if x)
    if not kong:
        return False
    shang = env.get('si_ke_shang') or []
    if len(shang) < 4:
        shang = _sike_shang_from_sike(env)
    if len(shang) < 4:
        return False
    return all(z in kong for z in shang)


def _gui_kong_you_miao(env):
    """第74法附条「或鬼空尤妙…凡鬼空亦宜制之」· 鬼空格

    【BUG-FIX 2026-09-11】本条原被误编译为 `kong_kong_ru_ye`（三传皆空）——
    实测 8640 课式中三条命中数完全相同（均 474），「鬼空」并无独立判据。

    **权威判据**（《毕法赋》第74法「空空如也事休追」原文 +
    第96法「旬内空亡逐类推」：「财空军储乏，**鬼空敌人遁**」）：
      「…或**鬼空尤妙**…**凡鬼空亦宜制之**，不然尤有虚挠之凶，为我难见彼之象。」
    → 判据 = **官鬼（克日干之支）落旬空**。
      取处：三传 + 干上 + 支上 + 四课上神（六处口径；原文「纵戌亥在六处亦不可用」用六处）。

    吉凶仍记「平」：原文既称「尤妙」（鬼空则害我者无力）又戒「亦宜制之…尤有虚挠之凶」，
    吉凶两可，故不作吉/凶单向定级。
    """
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    kong = set(x for x in (env.get('kongwang') or ('', '')) if x)
    if not kong:
        return False
    liu = [z for z in (env.get('sanchuan') or []) if z]
    liu += [env.get('gan_shang', ''), env.get('zhi_shang', '')]
    liu += list(env.get('si_ke_shang') or _sike_shang_from_sike(env))
    for z in liu:
        if z and z in kong and _zhi_ke(z, gan):   # 支克干 ⇒ 官鬼；且落旬空
            return True
    return False


def _tuo_shang_you_tuo(env):
    """脱上逢脱：干上为日干生者（虚诈）"""
    return _tuo_shang_feng_tuo(env)


def _gui_hua_cai_qian_xian_wei(env):
    """传鬼化财钱险危：初传克干，末传为干之财"""
    return _chuan_gui_hua_cai(env)


def _mu_zhu_mu_fen_zeng_ai(env):
    """传墓入墓分憎爱：初末俱墓，乘将吉凶分憎爱"""
    return _chuan_mu_ru_mu(env)


def _zhi_guan_shi_zhe_fu(env):
    """催官使者：干上为日鬼乘白虎"""
    gs = env.get('gan_shang', '')
    tj = env.get('tian_jiang', {})
    gan = env['ri_gan']
    return bool(gs and _zhi_ke(gs, gan) and _wx(gs) != _wx(gan) and tj.get(gs) == '白虎')


def _shu_zhai_zhi_ji(env):
    """屋宅宽广致人衰（别名）"""
    return _shu_zhai_kuan_guang(env)


def _you_yu_er_de_bu_zu(env):
    """赹有余而得不足：初传旺相末传空"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    kong = env.get('kongwang', ('', ''))
    # 【BUG-FIX 2026-09-01】'初' 须先 _resolve（同 _hu_shi_peng_hu 修复，原直传恒假）
    return _x_wang_xiang(env, _resolve('初', env)) and sc[2] in kong


# 旧规则迁移用别名（避免破坏现有规则）
def _zhi_shang_ke_gan_alias(env): return _zhi_shang_ke_gan(env)
def _gan_shang_sheng_gan_alias(env): return _gan_shang_sheng_gan(env)


# ══════════════════════════════════════════════════════════════════
# ── 三期迁移谓词（2026-08-21）：64 条硬编码 _check_rule_* → 声明式 DNF ──
# ══════════════════════════════════════════════════════════════════

# 天将→本家地支（天将正位/本宫，生克以本家五行为准）
TIANJIANG_BENJIA = {
    '贵人': '丑', '螣蛇': '巳', '朱雀': '午', '六合': '卯', '勾陈': '辰',
    '青龙': '寅', '天空': '戌', '白虎': '申', '太常': '未', '玄武': '亥',
    '太阴': '酉', '天后': '子',
}
# 日干→(昼贵, 夜贵) 天乙贵人
# 【BUG-FIX 2026-09-11 壬癸昼夜颠倒】原 壬/癸 写作 ('卯','巳')，权威判据为昼巳/夜卯：
#   《图解六壬大全》第1部 p.364「壬癸蛇兔藏（壬癸日昼贵巳，夜贵卯）」+
#   《通解·中卷》「壬子日初传巳加子为昼贵，末传卯加戌为夜贵」（引从课·两贵引从天干格）
#   影响 _gui_ren_cha_die（第46法，按 zhou_gui/ye_gui 落宫判定）；第45法为集合语义不受影响。
GUIREN_MAP = {
    '甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
    '乙': ('子', '申'), '己': ('子', '申'),
    '丙': ('亥', '酉'), '丁': ('亥', '酉'),
    '壬': ('巳', '卯'), '癸': ('巳', '卯'),
    '辛': ('午', '寅'),
}
# 三合局→刑/害/冲（合中犯杀用）
SANHE_SHANG = {
    '火': {'刑': '午', '害': '丑', '冲': '子'},  # 寅午戌
    '木': {'刑': '子', '害': '辰', '冲': '酉'},  # 亥卯未
    '水': {'刑': '卯', '害': '未', '冲': '午'},  # 申子辰
    '金': {'刑': '酉', '害': '戌', '冲': '卯'},  # 巳酉丑
}
# 月将→季节（月将是太阳过宫，与月建错位一组）
YUEJIANG_SEASON = {
    '亥': '春', '戌': '春', '酉': '春',
    '申': '夏', '未': '夏', '午': '夏',
    '巳': '秋', '辰': '秋', '卯': '秋',
    '寅': '冬', '丑': '冬', '子': '冬',
}

# 月将→月生气地支（月生气从月建推：生气=月建后退2位；月建=（1-月将序号）%12，故生气=（11-月将序号）%12）
def _yue_sheng_qi_zhi(yuejiang: str) -> str:
    """由月将推算月生气地支。
    正月月将亥→生气子；二月月将戌→生气丑；…依此类推。
    """
    if not yuejiang or yuejiang not in DIZHI_IDX:
        return ''
    return DIZHI_ORDER[(11 - DIZHI_IDX[yuejiang]) % 12]

# 死气 = 生气冲位（生气+6）
def _yue_si_qi_zhi(yuejiang: str) -> str:
    """由月将推算月死气地支（死气=生气对冲位）。"""
    sq = _yue_sheng_qi_zhi(yuejiang)
    if not sq:
        return ''
    return DIZHI_ORDER[(DIZHI_IDX[sq] + 6) % 12]
# 旬遁干映射（旬首→{地支:天干}）
XUN_GROUPS = [
    ('甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉'),
    ('甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未'),
    ('甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳'),
    ('甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯'),
    ('甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑'),
    ('甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'),
]
XUN_GAN_MAP = {}
for _grp in XUN_GROUPS:
    _gm = {}
    for _gz in _grp:
        _gm[_gz[1]] = _gz[0]
    XUN_GAN_MAP[_grp[0]] = _gm
XUN_DING = {'甲子': '卯', '甲戌': '丑', '甲申': '亥', '甲午': '酉', '甲辰': '未', '甲寅': '巳'}


def _is_zhi_before(a: str, b: str) -> bool:
    """a 是否在 b 之前（顺行方向，a 在 b 前一格以上）"""
    if not a or not b:
        return False
    return (DIZHI_IDX[a] - DIZHI_IDX[b]) % 12 not in (0, 1) and (DIZHI_IDX[a] - DIZHI_IDX[b]) % 12 > 1


def _is_zhi_after(a: str, b: str) -> bool:
    """a 是否在 b 之后（逆行方向）"""
    if not a or not b:
        return False
    return (DIZHI_IDX[b] - DIZHI_IDX[a]) % 12 > 1


def _zhi_dist(a: str, b: str) -> int:
    """a 相对 b 的顺行距离（1~11，0 表示同位）"""
    if not a or not b:
        return -1
    return (DIZHI_IDX[a] - DIZHI_IDX[b]) % 12


def _qian_hou_yin_cong(env, args=None):
    """第1法 前后引从：初传居干/支前为引，末传居干/支后为从
    args: ['干']=仅测日干寄宫；['支']=仅测日支；空=（旧兼容）二者任一。
    【BUG-FIX 2026-09-02】原实现用 _is_zhi_before/_is_zhi_after（顺行差 2~11 格皆判为前/后，
    几乎恒真）→ 拱干/拱支 89.86% 命中。按原文改判据：
    初末传【加临之地盘】相对干支锚点：前=顺行 1~6 格（半环），后=顺行 7~11 格。
    原文示例：庚辰日（庚寄申）寅加酉(酉在申前1)为初传、子加未(未在申后1)为末传；
    壬子日（壬寄亥）巳加子(子前1)、卯加戌(戌后1) 两贵引从。"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    tdp = env.get('tiandi_pan', {})
    if not tdp:
        return False
    # 反查初/末传天盘所加临的地盘
    def di_pan(zhi):
        for d, tp in tdp.items():
            if tp == zhi:
                return d
        return ''
    chu_di = di_pan(sc[0])
    mo_di = di_pan(sc[2])
    if not chu_di or not mo_di:
        return False
    anchors = []
    # 【BUG-FIX 2026-09-02】eval_atom 对 '干'/'支' 先 _resolve 为日干/日支字符，
    # 故需同时兼容「字面 '干'/'支'」与「已解析的日干/日支」两种入参形态。
    ga = args and args[0]
    if ga == '干':
        anchors = [GAN_JIGONG.get(env.get('ri_gan', ''), '')]
    elif ga == '支':
        anchors = [env.get('ri_zhi', '')]
    elif ga == env.get('ri_gan', ''):
        anchors = [GAN_JIGONG.get(env.get('ri_gan', ''), '')]
    elif ga == env.get('ri_zhi', ''):
        anchors = [env.get('ri_zhi', '')]
    else:
        anchors = [GAN_JIGONG.get(env.get('ri_gan', ''), ''), env.get('ri_zhi', '')]
    for anchor in anchors:
        if not anchor:
            continue
        d_chu = _zhi_dist(chu_di, anchor)
        d_mo = _zhi_dist(mo_di, anchor)
        if 1 <= d_chu <= 6 and 7 <= d_mo <= 11:
            return True
    return False


def _shou_wei_xiang_jian_v2(env):
    """第2法 首尾相见：干上=旬尾地支，支上=旬首地支"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    shou = env.get('xun_shou_zhi', '')
    wei = env.get('xun_wei_zhi', '')
    return bool(gs and zs and shou and wei and gs == wei and zs == shou)


def _lian_mu_gui_ren(env):
    """第3法 帘幕贵人：昼占得夜贵/夜占得昼贵临干上"""
    gs = env.get('gan_shang', '')
    if not gs:
        return False
    gr = env.get('guiren', ('', ''))   # 【BUG-FIX 2026-09-02】键名统一：build_env 设 env['guiren']
    if not gr or not gr[0]:
        return False
    is_day = env.get('is_day', True)
    lianmu = gr[1] if is_day else gr[0]  # 昼占夜贵、夜占昼贵
    return gs == lianmu


def _zhuo_lun_xiu_mu(env):
    """第10法 朽木难雕：初传卯+卯加申(天地盘)+卯空亡"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3 or sc[0] != '卯':
        return False
    tdp = env.get('tiandi_pan', {})
    if not tdp.get('申') == '卯':
        return False
    kong = env.get('kongwang', ('', ''))
    return '卯' in kong


def _gui_zei_dang_shi(env):
    """第13法 鬼贼当时：三传皆鬼(含三合/三会局为鬼)且鬼旺相"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    season = env.get('season', '')
    if len(sc) != 3 or not gan or not season:
        return False
    gan_wx = _wx(gan)
    ghost_wx = WX_KE.get(gan_wx, '')
    if not ghost_wx:
        return False
    all_ghost = all(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)
    if not all_ghost:
        s = frozenset(sc)
        hui = {frozenset('寅卯辰'): '木', frozenset('巳午未'): '火', frozenset('申酉戌'): '金', frozenset('亥子丑'): '水'}
        he = {frozenset('申子辰'): '水', frozenset('寅午戌'): '火', frozenset('亥卯未'): '木', frozenset('巳酉丑'): '金'}
        if hui.get(s, '') == ghost_wx or he.get(s, '') == ghost_wx:
            all_ghost = True
    if not all_ghost:
        return False
    season_wx = WANG_WX.get(season, '')
    xiang_wx = WX_SHENG.get(season_wx, '')
    return ghost_wx == season_wx or ghost_wx == xiang_wx


def _tuo_shang_feng_tuo_v2(env):
    """第15法 脱上逢脱：干生上神+上神生天将本家"""
    gs = env.get('gan_shang', '')
    gan = env.get('ri_gan', '')
    if not gs or not gan or not _zhi_sheng(gan, gs):
        return False
    tj = env.get('tian_jiang', {})
    jiang = tj.get(gs, '')
    benjia = TIANJIANG_BENJIA.get(jiang, '')
    return bool(benjia and _zhi_sheng(gs, benjia))


def _jinru_kong_wang(env):
    """第17法 进茹空亡：进连茹+初/中本旬空、末前旬空"""
    if env.get('trend') != '进连茹':
        return False
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    fxk = env.get('fen_xun_kong')
    if not fxk:
        return False
    ben, qian = fxk.get('本旬', set()), fxk.get('前旬', set())
    return sc[0] in ben and sc[1] in ben and sc[2] in qian


def _tuiru_kong_wang(env):
    """第18法 踏脚空亡：退步传(退连茹/逆间传)+初本旬空、中后旬空、末外后旬空"""
    if env.get('trend') not in ('退连茹', '逆间传'):
        return False
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    fxk = env.get('fen_xun_kong')
    if not fxk:
        return False
    ben, hou, waihou = fxk.get('本旬', set()), fxk.get('后旬', set()), fxk.get('外后旬', set())
    return sc[0] in ben and sc[1] in hou and sc[2] in waihou


def _tai_cai_sheng_qi(env):
    """第19法 胎财生气：胎神=月将生气位+为日干之财（干生胎）"""
    gan = env.get('ri_gan', '')
    yj = env.get('yuejiang', '')
    if not gan or not yj:
        return False
    tai = WX_TAI.get(_wx(gan))
    if not tai:
        return False
    tai_set = set(tai) if isinstance(tai, tuple) else {tai}
    # 月生气位按月将精确推算：生气=DIZHI_ORDER[(11-月将序号)%12]
    sheng_qi = _yue_sheng_qi_zhi(yj)
    return sheng_qi in tai_set


def _tai_cai_si_qi(env):
    """第20法 胎财死气：胎神=月内死气

    【BUG-FIX 2026-09-11】原实现末段：
        `si_zhi = WX_KE.get(si_wx, '')` —— 得到的是**五行字符串**（如 '水'），
        而 `tai_set` 是**地支集合**（如 {'午','子'}）→ `si_zhi in tai_set` **恒 False**
        → 本节零触发（实测 120 个「日干×月将」组合命中 0）。
    正解：死气五行 → 取其**所属地支**，再与胎位比对。
      （死气 = 季所克之五行：春土、夏金、秋木、冬火）
    """
    gan = env.get('ri_gan', '')
    yj = env.get('yuejiang', '')
    if not gan or not yj:
        return False
    tai = WX_TAI.get(_wx(gan))
    if not tai:
        return False
    tai_set = set(tai) if isinstance(tai, tuple) else {tai}
    season = YUEJIANG_SEASON.get(yj, '')
    si_wx = SI_WX.get(season, '')
    if not si_wx:
        return False
    # 死气五行 → 该五行的地支集合（原实现误用 WX_KE「所克」得五行字符串，类型不匹配）
    si_zhi_set = {z for z in DIZHI_ORDER if ZHI_WX.get(z) == si_wx}
    return bool(si_zhi_set & tai_set)


def _zhi_chuan_gan(env):
    """第23法 彼求我事支传干：初传=支上、末传=干上"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if len(sc) != 3 or not gs or not zs:
        return False
    return sc[0] == zs and sc[2] == gs


def _jin_ri_feng_ding(env):
    """第25法 金日逢丁：庚辛日+六处逢丁神"""
    gan = env.get('ri_gan', '')
    if gan not in ('庚', '辛'):
        return False
    ding = env.get('ding_shen', '')
    if not ding:
        return False
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    bm = env.get('ben_ming', '')
    return ding in sc or ding == gs or ding == zs or ding == bm


def _shui_ri_feng_ding(env):
    """第26法 水日逢丁：壬癸日+六处逢丁神"""
    gan = env.get('ri_gan', '')
    if gan not in ('壬', '癸'):
        return False
    ding = env.get('ding_shen', '')
    if not ding:
        return False
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    bm = env.get('ben_ming', '')
    return ding in sc or ding == gs or ding == zs or ding == bm


def _chuan_gui_hua_cai_v2(env):
    """第28法「传鬼化财钱险危」判据（2026-09-21 按原文五格重建；旧判据要求
    「三传逐个克日干」+「干上克传」，于该法 8 课 **0 命中**）

    原文（在线_bifa_sina.html L989 起）五格：
      A  主格·全鬼变财：三传成三合局而其**局克日干**（作日之鬼），**传内有一神作财现**
         ——丙申日三传子申辰（申子辰水局为丙之鬼），中传申为日财「中间为财者」。
      B  取还魂债格·生**干上**财神：三传成局皆作脱气（局五行＝我生者），而局生起
         干上神，干上神为日之财——己丑日干上亥、三传酉丑巳（金局脱气生亥水作财）。
      B2 取还魂债格·生**支上**财神：三传成局皆作脱气，而局生起支上神，
         支上神为日之财——壬寅日支上午、三传未亥卯（木局脱气生午火作财）。
      C  传内财爻旬空，而传内另有他神生之（「**墓土将生空亡之财**」）
         ——丁丑日三传酉丑巳，酉为丁财而旬空，中传丑土生之。
      D  求财急取格（**财就人格**）：干上神为日之财，且**初传即干上神**
         ——乙巳日干上未初传未；辛卯日干上卯初传卯。
      E  空财格：干上神／初传为日之财而**落旬空**——丙子日酉加巳，申酉空。
      F  危中取财格：**日干克日支（支为财），而支上神克日干为鬼**
         ——甲辰日甲木克辰土为财，辰上乘申（申金克甲木为鬼）。
         ⛔ 排除支上鬼落旬空者：原文「甲戌日支上申空亡，似乎无畏」「辛卯日支上午
           作空亡，不可畏之」⇒ 空鬼不须畏，不算危中取财。
    """
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    ri_zhi = env.get('ri_zhi', '')
    if not gan or len(sc) != 3:
        return False
    kong = env.get('kongwang') or ('', '')

    def is_cai(z):                          # 日干克 z ⇒ 妻财
        return bool(z) and _zhi_ke(gan, z)

    ju = _sc_ju_wx(sc)
    # A：三传成局克日干（鬼局）而传内有财
    if ju and WX_KE.get(ju, '') == _wx(gan) and any(is_cai(z) for z in sc):
        return True
    # B / B2：三传成局作脱气，而局生起干上／支上财神
    if ju and WX_SHENG.get(_wx(gan), '') == ju:
        for t in (gs, zs):
            if t and is_cai(t) and WX_SHENG.get(ju, '') == _wx(t):
                return True
    # C：传内财爻旬空，而传内另有他神生之
    for z in sc:
        if is_cai(z) and z in kong and any(o != z and _zhi_sheng(o, z) for o in sc):
            return True
    # D / E：财就人格（干上为财且初传即干上）；财落旬空亦属空财格
    if gs and is_cai(gs) and sc[0] == gs:
        return True
    # F：危中取财——支为日财，支上神为鬼且不落旬空
    if ri_zhi and is_cai(ri_zhi) and zs and _zhi_ke(zs, gan) and zs not in kong:
        return True
    return False


def _juan_shu_feng_ying(env):
    """第29法 眷属丰盈居狭宅：**三传递生日干，反脱其支辰**

    【BUG-FIX 2026-09-11】原实现 `all(_zhi_sheng(z, gan) for z in sc)` —— 要求
    **三传各自生日干**，此条件在六壬中恒不成立（枚举 8640 课可满足数 = 0）→ 本节零触发。

    **正解（据《毕法赋》原文 + 课例）**：「谓**三传生其日干**，反脱其支辰是也。
    值此必人口丰盈而居宅狭窄也。**如甲申日干上午**」
      → 甲申日 干上午 时，三传 = **辰/申/子**：
        辰(土)→申(金)→子(水)→甲(木)  **逐位递生**（土生金、金生水、水生木）
        且 支申(金)生三传之子(水) → **反脱支辰**
      → **"三传生干"实为「三传递生日干」，非"三传各自生干"**
    """
    sc = env.get('sanchuan', []) or []
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if len(sc) != 3 or not gan or not zhi:
        return False
    # 三传递生日干：顺（初→中→末→干）或 逆（末→中→初→干）
    shun = (_zhi_sheng(sc[0], sc[1]) and _zhi_sheng(sc[1], sc[2])
            and _zhi_sheng(sc[2], gan))
    ni = (_zhi_sheng(sc[2], sc[1]) and _zhi_sheng(sc[1], sc[0])
          and _zhi_sheng(sc[0], gan))
    if not (shun or ni):
        return False
    # 反脱其支辰：支气被盗泄（三传中有日支所生之神）
    return any(_zhi_sheng(zhi, x) for x in sc)


def _wu_zhai_kuan_guang_v2(env):
    """第30法 屋宅宽广致人衰：**三传递盗日干，反生支辰**

    【BUG-FIX 2026-09-11】同第29法 —— 原实现要求"三传各自脱干"（恒不成立）。
    正解：**三传递盗日干**（干→初→中→末 逐位递生，即日干之气被三传递脱）+ 三传（终传）生支辰。
    原文课例：「**如甲辰日戌加寅**」。
    """
    sc = env.get('sanchuan', []) or []
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if len(sc) != 3 or not gan or not zhi:
        return False
    # 三传递盗日干：干→初→中→末（顺）或 干→末→中→初（逆）
    shun = (_zhi_sheng(gan, sc[0]) and _zhi_sheng(sc[0], sc[1])
            and _zhi_sheng(sc[1], sc[2]))
    ni = (_zhi_sheng(gan, sc[2]) and _zhi_sheng(sc[2], sc[1])
          and _zhi_sheng(sc[1], sc[0]))
    if not (shun or ni):
        return False
    # 反生支辰：三传生支（传气归支）
    return any(_zhi_sheng(x, zhi) for x in sc)


def _you_shi_wu_zhong_v2(env):
    """第33法 有始无终：初长生末墓 / 初墓末长生"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    cs = CHANG_SHENG.get(_wx(gan))
    mu = WX_MU.get(_wx(gan), '')
    if not cs or not mu:
        return False
    cs_set = set(cs) if isinstance(cs, tuple) else {cs}
    return (sc[0] in cs_set and sc[2] == mu) or (sc[0] == mu and sc[2] in cs_set)


def _bi_kou_gua_v2(env):
    """第38法 闭口卦两般推：①地盘旬首上神乘玄武 ②旬尾加旬首+初末六合"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    shou = env.get('xun_shou_zhi', '')
    wei = env.get('xun_wei_zhi', '')
    sc = env.get('sanchuan', [])
    # ① 地盘旬首上神乘玄武
    if shou and tdp:
        shou_shang = tdp.get(shou, '')
        if shou_shang and tj.get(shou_shang) == '玄武':
            return True
    # ② 旬尾加旬首发用+初末六合
    if sc and len(sc) == 3 and shou and wei:
        wei_jia_shou = tdp.get(shou, '') == wei
        chu_mo_he = LIU_HE.get(sc[0], '') == sc[2]
        if sc[0] == wei and wei_jia_shou and chu_mo_he:
            return True
    return False


def _bi_kou_gua_dipan(env):
    """【P4 旬首旬尾收敛 2026-09-03】第38法闭口卦之一：地盘旬首上神乘玄武。
    原文「闭口卦体两般推…地盘旬首上神乘元武者」（甲子旬中甲子日辰戌加子昼夜皆乘元武）。
    原规则364用 x_dun_gan(干上/支上) 参数缺失恒假断链 → 改判地盘旬首（xun_shou_zhi）上神乘玄武。"""
    tdp = env.get('tiandi_pan', {}) or {}
    tj = env.get('tian_jiang', {}) or {}
    shou = env.get('xun_shou_zhi', '')
    if not shou:
        return False
    shou_shang = tdp.get(shou, '')
    return bool(shou_shang and tj.get(shou_shang) == '玄武')


def _bi_kou_gua_xunwei(env):
    """【P4 旬首旬尾收敛 2026-09-03】第38法闭口卦之二：旬尾加旬首发用 → 气塞于中。
    原文「旬尾加旬首为发用者例，更值初末上下六合，则气塞于中」。
    「更值初末六合」为加强条件（锦上添花）非必要条件——实测真实起课 8640 课中
    初传=旬尾且加地盘旬首共 96 课，但初传六合神（申/子/寅）与末传（亥/未/巳/辰）
    结构性无交集，若强制 AND 初末六合则恒假断链。故核心判据=初传=旬尾且旬尾加于地盘旬首。"""
    tdp = env.get('tiandi_pan', {}) or {}
    shou = env.get('xun_shou_zhi', '')
    wei = env.get('xun_wei_zhi', '')
    sc = env.get('sanchuan', []) or []
    if len(sc) != 3 or not shou or not wei:
        return False
    wei_jia_shou = tdp.get(shou, '') == wei
    return bool(sc[0] == wei and wei_jia_shou)


def _sanhe_sheng_gan_shang(env):
    """【P4 传鬼为生收敛 2026-09-03】三传三合局之五行 生 干上神之五行。
    原文「传鬼为生格：三传皆作日鬼，反生起干上之神而育干」（庚午日干上辰，三传戌午寅火局火生辰土）。
    供 _liu_yao_xian_gua_official（三合局克日干）组合判据用。"""
    jw = _sc_ju_wx(env.get('sanchuan', []) or [])
    gs = env.get('gan_shang', '')
    return bool(jw and gs and WX_SHENG.get(jw, '') == _wx(gs))


def _xun_shou_lian_mu(env):
    """【P4 旬首旬尾收敛 2026-09-03】旬首作帘幕官临年命日干尤的（惟乙己辛日有之）。
    原文「帘幕贵人高甲第…旬首作帘幕官临年命日干尤的（惟乙己辛日有之）」。
    判据：日干为乙/己/辛 + 旬首临日干（干上=旬首）或临年命（年命上神=旬首）。"""
    if env.get('ri_gan', '') not in ('乙', '己', '辛'):
        return False
    shou = env.get('xun_shou_zhi', '')
    if not shou:
        return False
    if env.get('gan_shang', '') == shou:
        return True
    bm = env.get('ben_ming_zhi', '')
    if bm:
        tp = env.get('tiandi_pan', {}) or {}
        if tp.get(bm, '') == shou:
            return True
    return False


def _chen_xu_xun_shou(env):
    """【P4 旬首旬尾收敛 2026-09-03】辰戌作旬首临年命日干者必中魁元。
    原文「帘幕贵人高甲第…辰戌作旬首临年命日干者必中魁元」（辰戌为领袖之神）。
    判据：旬首=辰或戌 + 临日干（干上=旬首）或临年命（年命上神=旬首）。"""
    shou = env.get('xun_shou_zhi', '')
    if shou not in ('辰', '戌'):
        return False
    if env.get('gan_shang', '') == shou:
        return True
    bm = env.get('ben_ming_zhi', '')
    if bm:
        tp = env.get('tiandi_pan', {}) or {}
        if tp.get(bm, '') == shou:
            return True
    return False


def _tai_yang_zhao_wu(env):
    """第39法 太阳照武：月将乘玄武"""
    yj = env.get('yuejiang', '')
    tj = env.get('tian_jiang', {})
    return bool(yj and tj.get(yj) == '玄武')


def _zun_chong_san_qi_v2(env):
    """第42法 尊崇传内遇三奇：三传旬干=甲戊庚/乙丙丁"""
    sc = env.get('sanchuan', [])
    gz = env.get('ganzhi', '')
    if len(sc) != 3 or not gz or len(gz) < 2:
        return False
    # 【P3 神煞类收敛 2026-09-02】旬首查找修复：原代码 xs[0]==gz[0] 要求
    # 「旬首天干==日干」（旬首天干恒为甲），致三奇只可能在甲日命中 → 恒断链。
    # 正确旬首按「日支-日干 地支环距」定位旬首支 index（甲子0/甲寅2/甲辰4/甲午6/甲申8/甲戌10）。
    g_idx = '甲乙丙丁戊己庚辛壬癸'.index(gz[0])
    shou_idx = (DIZHI_IDX[gz[1]] - g_idx) % 12
    gan_map = None
    for xs, gm in XUN_GAN_MAP.items():
        if DIZHI_IDX[xs[1]] == shou_idx:
            gan_map = gm
            break
    if not gan_map:
        return False
    gans = [gan_map.get(z, '') for z in sc]
    if '' in gans:
        return False
    gan_set = set(gans)
    return gan_set == {'甲', '戊', '庚'} or gan_set == {'乙', '丙', '丁'}


def _hou_he_zhan_hun(env):
    """第40法 后合占婚：干上乘天后、支上乘六合"""
    tj = env.get('tian_jiang', {})
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    return bool(tj.get(gs) == '天后' and tj.get(zs) == '六合')


def _fu_gui_gan_zhi(env):
    """第41法 富贵干支：干上=支驿马，支上=干禄"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    yima = env.get('yima', '')
    lu = env.get('lu', '')
    return bool(gs and zs and yima and lu and gs == yima and zs == lu)


def _ke_chuan_ju_gui(env):
    """第44法 课传俱贵：四课三传皆是昼夜贵人所聚（遍地贵人，贵多者不贵）
    原文例课（丁酉日）：干上酉夜贵、酉上见亥昼贵、支课复归亥乡，三传酉亥丑，
    四课三传皆是昼夜贵人所聚；又"外有三传皆是贵人者亦可用"（辛巳日干上午等）。
    【BUG-FIX 2026-09-02】原判据要求四课上神+三传全部 ∈ {昼贵,夜贵} 两元素集，
    结构上永不可能命中 → 0 命中断链。按原文两条例证改判据：
      甲. 四课上神中贵人支 ≥3（例课：酉亥酉亥 = 4）；
      乙. 三传皆是贵人支（"外有三传皆是贵人者亦可用"）。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gr = env.get('guiren', ('', ''))   # 【BUG-FIX 2026-09-02】键名统一：build_env 设 env['guiren']
    if not gr or not gr[0]:
        return False
    gui_set = set(gr)
    sc = env.get('sanchuan', []) or []
    sike = env.get('si_ke_shang', []) or []
    if not sike:
        sike = _sike_shang_from_sike(env)   # 【BUG-FIX 2026-09-02】si_ke 兜底提取四课上神
    # 乙. 三传皆是贵人支
    if len(sc) == 3 and all(z in gui_set for z in sc):
        return True
    # 甲. 四课上神中贵人支 ≥3
    gui_cnt = sum(1 for z in sike if z in gui_set)
    return gui_cnt >= 3


def _tian_luo_di_wang(env):
    """第55法 所谋多拙逢罗网：干上=干前一辰(天罗)，支上=支前一辰(地网)"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    gan_pos = GAN_JIGONG.get(env.get('ri_gan', ''), '')
    zhi = env.get('ri_zhi', '')
    if not gan_pos or not zhi or not gs or not zs:
        return False
    tian_luo = DIZHI_ORDER[(DIZHI_IDX[gan_pos] + 1) % 12]
    di_wang = DIZHI_ORDER[(DIZHI_IDX[zhi] + 1) % 12]
    return gs == tian_luo and zs == di_wang


def _tian_wang_zi_guo_v2(env):
    """第56法 天网自裹：干上=墓 AND 本命=墓"""
    gs = env.get('gan_shang', '')
    gan = env.get('ri_gan', '')
    bm = env.get('ben_ming', '')
    mu = WX_MU.get(_wx(gan), '')
    return bool(gs and mu and gs == mu and bm == mu)


def _fei_you_er_de_bu_zu_v2(env):
    """第57法 费有余得不足：父母爻空+子孙爻实在"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    kong = env.get('kongwang', ('', ''))
    if len(sc) != 3 or not gan or not kong[0]:
        return False
    has_parent_kong = any(_zhi_sheng(z, gan) and _wx(z) != _wx(gan) and z in kong for z in sc)
    has_child_not_kong = any(_zhi_sheng(gan, z) and z not in kong for z in sc)
    return has_parent_kong and has_child_not_kong


def _yong_po_shen_xin(env):
    """第58法「用破身心无所归」（2026-09-21 按原文七课重建）

    原文总纲（在线_bifa_sina.html L1844 起）：「**财禄俱作空被克，总无实得之意**」。
    判据＝用神（初传／干上）为日之**财或禄**，而该用神「**作空或被克**」，
    且三传余位**不能为依靠**。

      ⛔【BUG-FIX 2026-09-21】旧版两处硬伤（该法 7 课 0 命中）：
        · `lu = env.get('lu', '')` —— **`judge_orchestrator.build_judge_env` 不产 'lu' 键**
          （只有 `bifa_detector` / `kege_bianjie_engine` 才设）⇒ is_lu 恒 False，
          禄格永不命中；判否又被 judge 的 except 静默吞掉。⇒ 改用**本地十干禄表**。
        · 只看初传不看干上；分支A 要求「初传落空」、分支B 要求「中传克初传」
          ⇒ 课1~5（初传财受**坐克／上克**）与课6~7（关键在**干上**）全部落空。

    七课实测（用神破 + 余位无所归）：
      课1 戊申 三传子寅辰：初子为财「坐戌土之上受克」＋中寅为鬼且空（寅卯空）。
      课2 丙申 三传申亥寅：初申为财「申加巳」坐克（巳火克金）＋中亥为鬼。
      课3 丁卯 三传酉亥丑：初酉为财「昼乘朱雀」上克（火克金）＋中亥为鬼且空。
      课4 癸未 三传巳戌卯：初巳为财「巳加子」坐克（子水克火）＋中戌为鬼、末卯脱气。
      课5 己酉 三传亥卯未：初亥为财「亥加己」坐克（未土克水）＋中卯为鬼且空。
      课6 壬寅返吟 干上巳：干上巳为财而**落空**（辰巳空）＋初末寅为脱气。
      课7 壬寅伏吟 干上亥：干上亥为**日禄**（壬禄亥）乘天空土将克水＋中寅脱气、末巳财空。
    """
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    if not gan or len(sc) != 3:
        return False
    kong = env.get('kongwang') or ('', '')
    tj = env.get('tian_jiang') or {}
    tdp = env.get('tiandi_pan') or {}
    di_of = {v: k for k, v in tdp.items() if v}      # 天盘支 → 所临地盘
    # 十干禄（⛔ 不得用 env['lu']：judge_orchestrator.build_judge_env 不产该键）
    LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
          '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

    def is_cai(z):
        return bool(z) and _zhi_ke(gan, z) and _wx(z) != _wx(gan)

    def is_lu(z):
        return bool(z) and LU.get(gan, '') == z

    def bei_ke(z):
        """用神「作空或被克」：落旬空／坐克（所临地盘克之）／上克（天将五行克之）"""
        if not z:
            return False
        if z in kong:
            return True
        di = di_of.get(z, '')
        if di and WX_KE.get(_wx(di), '') == _wx(z):
            return True
        up = TIANJIANG_WX_MAP.get(tj.get(z, ''), '')
        return bool(up) and WX_KE.get(up, '') == _wx(z)

    def wu_suo_gui(z):
        """余位不能为依靠：为日鬼（含鬼而空）／脱气／落空"""
        if not z:
            return False
        if _zhi_ke(z, gan) and _wx(z) != _wx(gan):
            return True
        if _zhi_sheng(gan, z):
            return True
        return z in kong

    for u in (sc[0], gs):                            # 用神：先初传，后干上
        if u and (is_cai(u) or is_lu(u)) and bei_ke(u):
            if any(wu_suo_gui(z) for z in sc if z != u):
                return True
    return False


def _tai_yang_she_zhai_v2(env):
    """第60法 太阳射宅：支墓=月将(支上=支墓=月将)"""
    zs = env.get('zhi_shang', '')
    zhi = env.get('ri_zhi', '')
    yj = env.get('yuejiang', '')
    if not zs or not zhi or not yj:
        return False
    zhi_mu = WX_MU.get(_wx(zhi), '')
    return bool(zhi_mu and zs == zhi_mu and zs == yj)


def _zhi_cheng_mu_hu_v2(env):
    """第62法 支乘墓虎：干墓临支或支墓临支 + 白虎"""
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    tj = env.get('tian_jiang', {})
    if not zs or not gan:
        return False
    gan_mu = WX_MU.get(_wx(gan), '')
    zhi_mu = WX_MU.get(_wx(zhi), '')
    is_mu = (zs == gan_mu) or (zs == zhi_mu)
    return bool(is_mu and tj.get(zs) == '白虎')


def _gan_mu_bing_guan(env):
    """第65法 干墓并关：日干墓=季关神+发用+临干/支"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    season = env.get('season', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if len(sc) != 3 or not gan or not season:
        return False
    guan_map = {'春': '丑', '夏': '辰', '秋': '未', '冬': '戌'}
    guan = guan_map.get(season, '')
    gan_mu = WX_MU.get(_wx(gan), '')
    if not gan_mu or gan_mu != guan:
        return False
    return sc[0] == gan_mu and (gs == gan_mu or zs == gan_mu)


def _zhi_fen_cai_bing_v2(env):
    """第66法 支坟财并：三传有支墓=日干财"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if len(sc) != 3 or not gan or not zhi:
        return False
    zhi_mu = WX_MU.get(_wx(zhi), '')
    if not zhi_mu:
        return False
    return any(z == zhi_mu and _zhi_ke(gan, z) and _wx(z) != _wx(gan) for z in sc)


def _shou_hu_ke_shen(env):
    """第67法 受虎克神：课传六处乘白虎，白虎五行克之

    【BUG-FIX 2026-09-11】原实现末行 `_zhi_ke('金', z)` —— 把**地支** z 直接喂给
    期望**五行**的 `_zhi_ke`（实测 `_zhi_ke('金','木')=True` 而 `_zhi_ke('金','寅')=False`）
    → 条件恒 False，本节零触发（112320 课式穷举内 0 次）。
    另有无效语句 `for z in six: if ... : pass`（空循环，仅注释）。
    正解：先把地支转五行 `_wx(z)` 再比较。
    """
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {}) or {}
    six = [z for z in (list(sc) + [gs, zs]) if z]
    if not six:
        return False
    hu_wx = TIANJIANG_WX_MAP.get('白虎', '')   # 白虎五行 = 金
    if not hu_wx:
        return False
    # 白虎五行（金）克该支五行
    # ⚠️ 不可用 `_zhi_ke(hu_wx, _wx(z))` —— `_wx` 对五行输入返回 ''，
    #    会得 `WX_KE['']==''` 即 `'' == ''` 的**假阳性**！必须直接用五行表比较。
    return any(tj.get(z) == '白虎' and WX_KE.get(hu_wx, '') == _wx(z) for z in six)


def _zhi_gui_liang_yi(env):
    """第68法 制鬼之位乃良医：三传中有克鬼之神(食神/子孙爻)
    【2026-09-09 OX 复核 + 用户质疑修复】原实现把 WX_KE（我克：木→土）当"鬼五行"，
    而鬼 = 克我者（乙木→金），制鬼 = 克鬼者（火克金）。原写法导致 乙日鬼被错算成"土"、
    制鬼错算成"水"，三传亥(水)被误判为制鬼之神（262期"亥制鬼"谬误真相）。
    正确：ghost = 克gan五行者；制者 = 克ghost者。
    注意本文件 WX_KE 语义恒为"我克"（a克b ⇔ WX_KE[a]==b），故：
      ghost_wx = 反向查 (克我) ；制鬼_wx = 再反向查 (克鬼)。"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    gan_wx = _wx(gan)
    # 鬼 = 克我者：找 x 使 WX_KE[x]（x克某）== gan_wx
    ghost_wx = next((x for x, y in WX_KE.items() if y == gan_wx), '')
    if not ghost_wx:
        return False
    # 制鬼之神五行 = 克鬼者：找 x 使 WX_KE[x] == ghost_wx
    ke_gui_wx = next((x for x, y in WX_KE.items() if y == ghost_wx), '')
    # 须满足：三传有制鬼之神 **且三传确实有鬼**（无鬼则"制鬼"无的放矢，不触发）
    has_ghost = any(_wx(z) == ghost_wx for z in sc)
    if not has_ghost:
        return False
    return any(_wx(z) == ke_gui_wx for z in sc)


def _sang_diao_quan_feng_v2(env):
    """第72法 丧吊全逢：丧门+吊客临干支"""
    tai_sui = env.get('tai_sui', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not tai_sui or not gs or not zs:
        return False
    sang = DIZHI_ORDER[(DIZHI_IDX[tai_sui] + 2) % 12]  # 岁前二辰
    diao = DIZHI_ORDER[(DIZHI_IDX[tai_sui] - 2) % 12]  # 岁后二辰
    return (gs == sang and zs == diao) or (gs == diao and zs == sang)


def _hu_sheng_ju_sheng(env):
    """第77法 互生俱生：互生(干上生支+支上生干) 或 俱生(干上生干+支上生支)"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if not gs or not zs or not gan or not zhi:
        return False
    if _zhi_sheng(gs, zhi) and _zhi_sheng(zs, gan):
        return True
    if _zhi_sheng(gs, gan) and _zhi_sheng(zs, zhi):
        return True
    return False


def _ren_zhai_jie_si(env):
    """第80法 人宅皆死：干上=支死位+支上=干死位"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if not gs or not zs or not gan or not zhi:
        return False
    # 死位 = 当季所克五行之地支（如春木旺→死土→辰戌丑未）
    season_wx = WANG_WX.get(env.get('season', ''), '')
    if not season_wx:
        return False
    si_wx = WX_KE.get(season_wx, '')  # 旺所克=死
    if not si_wx:
        return False
    # 死位地支全集（该五行所有地支，而非仅取首个）
    si_zhi_set = {z for z, w in ZHI_WX.items() if w == si_wx}
    return gs in si_zhi_set and zs in si_zhi_set


def _dead_zhi(wx):
    """五行之十二长生死位（长生顺行第7位：长生→沐浴→冠带→临官→帝旺→衰→病→死；土双位→死位双位）。
    例：戊土(水土同宫申+7=卯)、庚金(巳+7=子)、寅木(亥+7=午)、丙丁火(寅+7=酉)，与毕法赋实例全符。"""
    cs = CHANG_SHENG.get(wx, '')
    if not cs:
        return ''
    def _shift(z):
        return DIZHI_ORDER[(DIZHI_IDX[z] + 7) % 12]
    if isinstance(cs, tuple):
        return tuple(_shift(z) for z in cs)
    return _shift(cs)


def _hu_cheng_si_qi(env):
    """干支互乘死气格（毕法赋·人宅皆死各衰羸·"干支上互乘死气格"）：
    干上=支之十二长生死位 且 支上=干之十二长生死位（交叉互乘）。
    如戊申日干上子(申金死位)、支上卯(戊土死位)；庚寅日干上午(寅木死位)、支上子(庚金死位)。"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if not gs or not zs or not gan or not zhi:
        return False
    zhi_die = _dead_zhi(ZHI_WX.get(zhi, ''))
    gan_die = _dead_zhi(GAN_WX.get(gan, ''))
    if not zhi_die or not gan_die:
        return False
    return _zhi_in_wei(gs, zhi_die) and _zhi_in_wei(zs, gan_die)


def _quan_cheng_si_qi(env):
    """干支全乘死气格（毕法赋·人宅皆死各衰羸·"支干全乘死气格"）：
    干上=干之十二长生死位 且 支上=支之十二长生死位（干支各自本气乘死气）。
    例：庚寅/庚申/辛丑日干上子(金死于子)；乙丑/甲申/甲寅干上午(木死于午)；
    己未/壬申/壬寅干上卯(己土·壬水死于卯)；丙寅/丙申/丁丑干上酉(火死于酉)。"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if not gs or not zs or not gan or not zhi:
        return False
    gan_die = _dead_zhi(GAN_WX.get(gan, ''))
    zhi_die = _dead_zhi(ZHI_WX.get(zhi, ''))
    if not gan_die or not zhi_die:
        return False
    return _zhi_in_wei(gs, gan_die) and _zhi_in_wei(zs, zhi_die)


def _san_liu_he(env):
    """第83法 万事喜忻三六合：三传成三合局"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    return any(set(sc) == s for s in SANHE)


def _he_zhong_fan_sha(env):
    """第84法 合中犯杀：三合局+干支上神见刑/害/冲"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if len(sc) != 3:
        return False
    s = frozenset(sc)
    ju_wx = ''
    for jn, js in SANHE_JU.items():
        if s == js:
            ju_wx = {'润下': '水', '曲直': '木', '炎上': '火', '从革': '金'}.get(jn, '')
            break
    if not ju_wx:
        return False
    sha = SANHE_SHANG.get(ju_wx, {})
    for label, up in [('干上', gs), ('支上', zs)]:
        if not up:
            continue
        if up == sha.get('刑') or up == sha.get('害') or up == sha.get('冲'):
            return True
    return False


def _chu_zao_jia_ke_v2(env):
    """第85法 初遭夹克：天将五行克初传 + 地盘五行克初传

    【BUG-FIX 2026-09-11】原实现两处 `_zhi_ke` 把**地支**当**五行**传：
      `_zhi_ke(jiang_wx, chu)` 与 `_zhi_ke(dipan, chu)` —— 实测 `_zhi_ke('金','寅')=False`
      → 首个判断 `if not False: return False` **恒真** → 本节零触发。
    正解：地支先经 `_wx()` 转五行。
    """
    sc = env.get('sanchuan', []) or []
    tj = env.get('tian_jiang', {}) or {}
    tdp = env.get('tiandi_pan', {}) or {}
    if len(sc) != 3:
        return False
    chu = sc[0]
    chu_wx = _wx(chu)
    if not chu_wx:
        return False
    jiang = tj.get(chu, '')
    jiang_wx = TIANJIANG_WX_MAP.get(jiang, '')
    if not jiang_wx:
        return False
    # ① 天将五行克初传（⚠️ 不可用 _zhi_ke(五行,五行) —— _wx 对五行返回 ''，
    #    会得 '' == '' 假阳性；必须直接查五行表）
    if WX_KE.get(jiang_wx, '') != chu_wx:
        return False
    # ② 地盘五行克初传（初传所坐地盘）：tiandi_pan 是 {地盘: 天盘}，反查
    dipan = ''
    for dp, tp in tdp.items():
        if tp == chu:
            dipan = dp
            break
    if not dipan:
        return False
    return WX_KE.get(_wx(dipan), '') == chu_wx


def _jiang_feng_nei_zhan(env):
    """第86法 将逢内战：天将五行克所乘地支五行

    【BUG-FIX 2026-09-11】原实现 `_zhi_ke(jwx, z)`（五行×**地支**）恒 False，
    且 `_wx(jwx)` 对五行输入返回 ''（`_wx` 是"地支→五行"）→ 首条件恒真、次条件恒假
    → 本节零触发。正解：`_zhi_ke(jwx, _wx(z))`。
    （"五行不同"是"克"的必要条件，无需单列。）
    """
    sc = env.get('sanchuan', []) or []
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {}) or {}
    six = [z for z in (list(sc) + [gs, zs]) if z]
    for z in six:
        jiang = tj.get(z, '')
        if not jiang:
            continue
        jwx = TIANJIANG_WX_MAP.get(jiang, '')
        z_wx = _wx(z)
        # ⚠️ 同上：不可经 _zhi_ke 传五行（假阳性）
        if jwx and z_wx and WX_KE.get(jwx, '') == z_wx:
            return True
    return False


def _ren_zhai_zuo_mu_v2(env):
    """第87法 人宅坐墓：天盘干(寄宫)坐地盘干墓、天盘支坐地盘支墓"""
    tdp = env.get('tiandi_pan', {})
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if not gan or not zhi or not tdp:
        return False
    gan_pos = GAN_JIGONG.get(gan, '')
    gan_mu = WX_MU.get(_wx(gan), '')
    zhi_mu = WX_MU.get(_wx(zhi), '')
    if not gan_mu or not zhi_mu:
        return False
    # 天盘干寄宫坐地盘干墓：tiandi_pan[gan_mu] == gan_pos
    # 天盘支坐地盘支墓：tiandi_pan[zhi_mu] == zhi
    return tdp.get(gan_mu, '') == gan_pos and tdp.get(zhi_mu, '') == zhi


def _ren_xin_ding_ma(env):
    """第89法 任信丁马：伏吟课 + 丁神在六处

    【BUG-FIX 2026-09-11】原判据 `sc[0]==sc[1]==sc[2]`（要求"三传完全相同"）
    把伏吟课认错了 —— **伏吟课的三传通常并不相同**（如 丑/戌/未、酉/戌/未）。
    实测：730 个伏吟课（60 干支 × 12「月将=时辰」）中，三传齐同者为 **0 个**
    → 本节在 112320 课式的穷举中**零触发**（死规则）。
    其中"逢丁神"者达 **180 个**，本应触发。

    正解（据《大六壬》伏吟课定义 + 毕法赋原文"伏吟卦…传中及干支上有丁神或驿马"）：
      伏吟课 ⟺ 月将 == 时辰（天地盘重合）；
    "六处"指三传 + 干上 + 支上。
    """
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    # 伏吟课判定：优先用课体名（引擎 calculate 产出，含子格名），否则用「月将==时辰」
    keti = str(env.get('keti', '') or '')
    is_fuyin = ('伏吟' in keti) or ('不虞' in keti) or ('自任' in keti)
    if not is_fuyin:
        yj = env.get('yuejiang', '') or env.get('yue_jiang', '')
        shi = env.get('shichen', '')
        is_fuyin = bool(yj and shi and yj == shi)
    if not is_fuyin:
        return False
    ding = env.get('ding_shen', '')
    if not ding:
        return False
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    return ding in sc or ding == gs or ding == zs


def _zhi_is_kong(env, z):
    """公共工具：判断某支是否为「空」

    「空」有四种形态（据《毕法赋》注解 + 《六壬大全》第十八法「踏脚空亡」）：
      ① **旬空**：本支 ∈ 本旬空亡
      ② **坐空**：该支所临**地盘** ∈ 本旬空亡
      ③ **乘天空**：该支上乘天将「天空」
      ④ **踏空**：本支 ∈ **前旬 / 后旬 / 外后旬**空亡（分旬空亡）
    """
    if not z:
        return False
    kong = env.get('kongwang', ('', '')) or ('', '')
    kong_set = set(x for x in kong if x)
    fxk = env.get('fen_xun_kong') or {}
    if fxk.get('本旬'):
        kong_set |= set(fxk['本旬'])
    if z in kong_set:                                    # ① 旬空
        return True
    tdp = env.get('tiandi_pan', {}) or {}
    for dp, tp in tdp.items():                           # ② 坐空
        if tp == z and dp in kong_set:
            return True
    tj = env.get('tian_jiang', {}) or {}
    if tj.get(z) == '天空':                               # ③ 乘天空
        return True
    if (z in set(fxk.get('前旬') or []) or z in set(fxk.get('后旬') or [])
            or z in set(fxk.get('外后旬') or [])):        # ④ 踏空
        return True
    return False


def _lai_qu_ju_kong(env):
    """第90法 来去俱空岂动宜（2026-09-21 按原文**三子类**重建）

    原文（在线_bifa_sina.html L2738 起）：「夫**来去**者，返吟卦也，缘**初传与末传**、
    初中末往来交互也…内有**三传皆空亡**者，虽有动意，**实不动**也」。

    ⛔ 旧版只认「初末**相冲** + 三传**皆**复合空」⇒ 7 课 **0 命中**：
       · 返吟三传是「卯酉卯／戌辰戌／巳亥巳」式，初末**同支**（往来），**并非相冲**；
       · 「三传皆空」过严——课1 中传酉不空、课2 中传辰不空、课3 初末巳不空。

    三子类（实测覆盖 7/7）：
      A 来去俱空（返吟／似返吟）：**初传 == 末传**（往来交互）且三传中**有旬空**
        ——己酉日卯酉卯「用鬼皆空」、乙丑日戌辰戌「传财俱空」、
          戊辰日巳亥巳「生气落空」、癸未日申寅申（原文明言「**似**返吟卦」「始末皆空」）。
      B 斩关·移远就近：**干上、支上皆乘魁罡（辰/戌）**而**中末传有空**
        「必主动，缘中末空亡，**反不能动**」
        ——庚寅日干上辰支上戌（三传戌午寅，午空）、庚寅日干上戌支上辰（三传辰午申，午空）。
      C 柔日昴星·干上墓覆：**干上神即日干之墓** 且 课体为**昴星**
        「虽干支上全乘魁罡，缘干上墓覆，又是柔日昴星，伏匿万状，终不能动」
        ——己丑日干上辰（己土墓在辰）、支上戌、课体昴星。
    """
    sc = env.get('sanchuan', []) or []
    gan = env.get('ri_gan', '')
    if len(sc) != 3:
        return False
    kong = env.get('kongwang') or ('', '')
    gs, zs = env.get('gan_shang', ''), env.get('zhi_shang', '')
    keti = env.get('keti', '') or ''
    # A：初末同支（来去往来）＋ 三传中有旬空
    if sc[0] == sc[2] and any(z in kong for z in sc):
        return True
    # B：干支上皆魁罡 ＋ 中末有空（斩关反不能动）
    if gs in ('辰', '戌') and zs in ('辰', '戌') and any(z in kong for z in sc[1:]):
        return True
    # C：干上墓覆 ＋ 干支上皆魁罡（柔日昴星，伏匿不动）
    #    ⛔ **不得用 `'昴星' in env['keti']`**：judge_all 在跑完 `_judge_64keti` 后会
    #       **回填 env['keti'] 为 64 课格判出的课体名**（judge_orchestrator BUG-FIX
    #       2026-09-01），覆盖入参原值 ⇒ 谓词读到的是改写后的课体，昴星判定失效。
    #       故改用原文实指的三个可判特征，与 keti 解耦。
    mu = WX_MU.get(_wx(gan), '') if gan else ''
    if (mu and gs == mu and gs in ('辰', '戌') and zs in ('辰', '戌')
            and gan in '乙丁己辛癸'):
        return True
    return False


def _hu_lin_gan_gui(env):
    """第91法 虎临干鬼：课传六处有日鬼乘白虎"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    gan = env.get('ri_gan', '')
    six = [z for z in (sc + [gs, zs]) if z]
    return any(tj.get(z) == '白虎' and _zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in six) if six and gan else False


def _long_jia_sheng_qi(env):
    """第92法 龙加生气：课传六处有青龙乘生干之神 且 该神为月生气位"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    gan = env.get('ri_gan', '')
    yj = env.get('yuejiang', '')
    six = [z for z in (sc + [gs, zs]) if z]
    if not six or not gan or not yj:
        return False
    sheng_qi = _yue_sheng_qi_zhi(yj)
    if not sheng_qi:
        return False
    for z in six:
        if tj.get(z) == '青龙' and _zhi_sheng(z, gan) and z == sheng_qi:
            return True
    return False


def _wang_yong_san_chuan(env):
    """第93法 妄用三传：三传≥2自刑+涉克比"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    xing_count = sum(1 for z in sc if z in XING.get(z, set()))
    has_kebi = any(_zhi_ke(sc[0], z) for z in sc[1:]) or any(_zhi_ke(z, sc[0]) for z in sc[1:])
    return xing_count >= 2 and has_kebi


def _xi_ju_kong_wang(env):
    """第94法 喜惧空亡：三传有空亡，影响吉凶"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    kong = env.get('kongwang', ('', ''))
    if len(sc) != 3 or not gan or not kong[0]:
        return False
    return any(z in kong for z in sc)


def _xun_nei_kong_wang(env):
    """第96法 旬内空亡逐类推：三传空亡有类应"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    kong = env.get('kongwang', ('', ''))
    if len(sc) != 3 or not gan or not kong[0]:
        return False
    for z in sc:
        if z in kong:
            if (_zhi_ke(gan, z) and _wx(z) != _wx(gan)) or \
               (_zhi_ke(z, gan) and _wx(z) != _wx(gan)) or \
               _zhi_sheng(z, gan) or _zhi_sheng(gan, z):
                return True
    return False


def _suo_shi_bu_ru(env):
    """第97法 所筮不入：三传缺主要六亲(父母/财/鬼)"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    has_parent = any(_zhi_sheng(z, gan) and _wx(z) != _wx(gan) for z in sc)
    has_wealth = any(_zhi_ke(gan, z) and _wx(z) != _wx(gan) for z in sc)
    has_ghost = any(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)
    return not has_parent and not has_wealth and not has_ghost


def _chang_wen_bu_ying(env):
    """第99法 常问不应：吉泰课（三传皆生干）常人占反致灾咎"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    return all(_zhi_sheng(z, gan) for z in sc)


def _yi_zai_xiong_tao_v2(env):
    """第100法 已灾凶逃：三传皆鬼（以凶制凶）"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    return all(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)




# ══════════════════════════════════════════════════════════════════
# ── 四期迁移谓词（2026-08-21）：剩余 13 条硬编码 _check_rule_* → 声明式 DNF ──
# ══════════════════════════════════════════════════════════════════

def _ku_qu_gan_lai_le_li_bei(env):
    """第34法 苦去甘来乐里悲：①末克初且末为日干长生(苦去甘来)；②初三递生末脱干(乐里生忧)"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    chu, zhong, mo = sc[0], sc[1], sc[2]
    cs = CHANG_SHENG.get(_wx(gan), '')
    cs_set = cs if isinstance(cs, (tuple, list)) else ((cs,) if cs else ())
    # 苦去甘来：初传克干(鬼), 末传克初传 且 末传为日干长生位
    if _zhi_ke(chu, gan) and _zhi_ke(mo, chu) and mo in cs_set:
        return True
    # 乐里生忧：初生中, 中生末, 末传脱干(干生末=子孙)
    if _zhi_sheng(chu, zhong) and _zhi_sheng(zhong, mo) and _zhi_sheng(gan, mo):
        return True
    return False


def _hai_gui_song_zhi_zuo_qu(env):
    """第43法 害贵讼直作曲断：贵人乘某支，与课传六处某支相害"""
    tj = env.get('tian_jiang', {})
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not tj:
        return False
    all_zhi = [z for z in list(sc) + [gs, zs] if z]
    for gui_zhi, jiang in tj.items():
        if jiang != '贵人':
            continue
        for other in all_zhi:
            if other != gui_zhi and LIU_HAI.get(other, '') == gui_zhi:
                return True
    return False


def _sike_shang_from_sike(env):
    """【2026-09-02】从 si_ke（四课原始结构）兜底提取四课上神列表"""
    sike = env.get('si_ke') or []
    out = []
    for k in sike:
        if isinstance(k, (list, tuple)) and len(k) > 1:
            if k[1] in DIZHI_ORDER:
                out.append(k[1])
        elif isinstance(k, str) and k in DIZHI_ORDER:
            out.append(k)
    return out


def _zhou_ye_gui_jia(env):
    """第45法 昼夜贵加求两贵：六处(三传+干上+支上+四课上神)见昼贵且见夜贵"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    zhou_gui, ye_gui = gui
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    sike_shang = env.get('si_ke_shang', []) or []
    if not sike_shang:
        sike_shang = _sike_shang_from_sike(env)   # 【BUG-FIX 2026-09-02】si_ke 兜底
    all_zhi = [z for z in list(sc) + [gs, zs] + list(sike_shang) if z]
    return zhou_gui in all_zhi and ye_gui in all_zhi


def _gui_ren_cha_die(env):
    """第46法 贵人差迭事参差：昼贵临夜地、夜贵临昼方。
    【BUG-FIX 2026-09-02】判据改为天地盘落点：甲子日丑昼贵坐酉(夜地)、未夜贵坐卯(昼方)。
    原实现只查干上/支上两处 → 覆盖面过窄且无法命中原文示例。"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    zhou_gui, ye_gui = gui
    ye_di = {'酉', '戌', '亥', '子', '丑', '寅'}
    zhou_fang = {'卯', '辰', '巳', '午', '未', '申'}
    tdp = env.get('tiandi_pan', {})
    if not tdp:
        return False
    zhou_pos = [d for d, tp in tdp.items() if tp == zhou_gui]
    ye_pos = [d for d, tp in tdp.items() if tp == ye_gui]
    zhou_on_ye = any(d in ye_di for d in zhou_pos)
    ye_on_zhou = any(d in zhou_fang for d in ye_pos)
    if not (zhou_on_ye and ye_on_zhou):
        return False
    # 【B5e 2026-09-04】原文例「丑为昼贵坐在酉上，未为夜贵却坐在卯上」——酉卯相冲，
    # 两贵落点互为对冲才成"差迭/参差"错位象；原仅昼贵临夜地∧夜贵临昼方命中 31.67%
    # 过宽（几何本底 ~25%）→ 加落点对冲后实测 15.00%。
    return any(d0 and d1 and LIU_CHONG.get(d0, '') == d1 for d0 in zhou_pos for d1 in ye_pos)


def _gui_zai_yu_yi_lin_gan(env):
    """第47法 贵虽在狱宜临干：贵人天盘支加临地盘辰戌(入狱)；辰戌日非坐狱；乙辛日为临身"""
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    tj = env.get('tian_jiang', {})
    tdp = env.get('tiandi_pan', {})
    if not gan or not tj or not tdp:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    gui_tianpan = [z for z, j in tj.items() if j == '贵人']
    if not gui_tianpan:
        return False
    zai_yu = (tdp.get('辰', '') in gui_tianpan) or (tdp.get('戌', '') in gui_tianpan)
    if not zai_yu:
        return False
    # 辰戌日 → 贵人入宅，非坐狱
    if rz in ('辰', '戌'):
        return False
    return True  # 乙辛日临身 or 余干入狱


def _liang_gui_shou_ke(env):
    """第49法 两贵受克难干贵：昼夜贵人立于受克之方。
    【BUG-FIX 2026-09-02】判据改为天地盘落点（原文：六乙六己申加午子加戌，六丙六丁亥加未酉加巳，
    六辛午加子寅加申，六壬六癸巳加亥卯加酉；惟甲戊庚无此例）；
    原文所列乃昼/夜贵任一受克之并列示例（如六乙六己日 或申加午或子加戌 即受克格），
    且"不论在传不在传"→ 直接按二贵天盘落点受克判定，不依赖所乘天将（贵人将全天盘仅一位）。"""
    gan = env.get('ri_gan', '')
    if not gan or gan in '甲戊庚':
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui or not gui[0]:
        return False
    zhou_gui, ye_gui = gui
    tdp = env.get('tiandi_pan', {})
    if not tdp:
        return False
    zhou_pos = [d for d, tp in tdp.items() if tp == zhou_gui]
    ye_pos = [d for d, tp in tdp.items() if tp == ye_gui]
    zhou_ked = any(_zhi_ke(d, zhou_gui) for d in zhou_pos)
    ye_ked = any(_zhi_ke(d, ye_gui) for d in ye_pos)
    # 【B5e 2026-09-04】原文"凡昼夜贵人皆立受克之方者"——「皆」=两贵同时受克（AND）。
    # 原文例"申加午、子加戌"在同一盘中同时成立（天盘顺排：申加午则子在戌）；
    # 原 OR 实现把命中率 24% 翻倍于原文本义 → 改 AND 后实测 5.83%。
    return zhou_ked and ye_ked


def _er_gui_jie_kong(env):
    """第50法 二贵皆空虚喜期：**昼夜贵人皆值空亡**

    【BUG-FIX 2026-09-11】原实现只判「两贵**本支** ∈ 旬空」——
    而旬空仅 2 支、昼夜贵（如丁日亥/酉）往往只重合其一 → **恒不成立**（112320 课式零触发）。

    **正解（据《毕法赋》原文）**：「此谓**旦暮贵人皆值空亡**者……如**丁丑日干上酉**」
      「**皆值空亡**」须含两义：
        ① **本支空亡**：贵人地支本身 ∈ 本旬空亡
        ② **坐空**：贵人**所临地盘** ∈ 本旬空亡

    实测原文课例（丁丑日 月将子 戌时，干上酉；空亡申酉；丁日昼贵亥/夜贵酉）：
      · 昼贵 **亥**：本支不空，**所临地盘 = 酉（空亡）→ 坐空** ✓
      · 夜贵 **酉**：**本支 ∈ 空亡** ✓
      → 两贵皆值空亡成立（原文课例得证）
    """
    gan = env.get('ri_gan', '')
    gui = GUIREN_MAP.get(gan)
    if not gan or not gui:
        return False
    kw = set(x for x in (env.get('kongwang') or ()) if x)
    if not kw:
        return False
    tdp = env.get('tiandi_pan', {}) or {}
    fan = {}
    for dp, tp in tdp.items():
        if tp:
            fan.setdefault(tp, dp)

    def _zhi_kong(z):
        if not z:
            return False
        if z in kw:                      # ① 本支空亡
            return True
        dp = fan.get(z, '')
        return bool(dp) and dp in kw     # ② 坐空

    return all(_zhi_kong(g) for g in gui)


def _liang_she_jia_mu_v2(env):
    """第53法 两蛇夹墓凶难免：日干墓临干或支，且墓神乘螣蛇"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    if not gan or (not gs and not zs):
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    mu_zhi = gs if gs == mu else (zs if zs == mu else '')
    if not mu_zhi:
        return False
    return tj.get(mu_zhi, '') == '螣蛇'


def _hu_shi_peng_hu_v2(env):
    """第54法 虎视逢虎力难施：昴星课(虎视课)且三传有支乘白虎"""
    keti = env.get('keti', '') or ''
    if '昴星' not in keti and '虎视' not in keti:
        return False
    tj = env.get('tian_jiang', {})
    sc = env.get('sanchuan', [])
    return any(tj.get(z) == '白虎' for z in sc if z)


def _gan_cheng_mu_hu(env):
    """第61法 干乘墓虎无占病：辛日昼占干上墓乘白虎；乙日墓乘白虎临本命"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    tj = env.get('tian_jiang', {})
    is_day = env.get('is_day', True)
    ben_ming = env.get('ben_ming', '')
    if not gan or not tj:
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    if gan == '辛':
        return bool(is_day and gs == mu and tj.get(gs) == '白虎')
    if gan == '乙':
        return bool(tj.get(mu) == '白虎' and ben_ming == mu)
    return False


def _gui_lin_san_si_v2(env):
    """第70法 鬼临三四讼灾随：第三课和第四课都有日干之鬼"""
    gan = env.get('ri_gan', '')
    si_ke = env.get('si_ke', [])
    if not gan or len(si_ke) < 4:
        return False

    def _ghost_in(ke):
        if not ke:
            return False
        if isinstance(ke, dict):
            zhis = [ke.get('上神', ''), ke.get('下神', '')]
        elif isinstance(ke, (list, tuple)):
            zhis = list(ke)[1:3] if len(ke) >= 3 else list(ke)
        else:
            zhis = []
        return any(_zhi_ke(z, gan) for z in zhis if z and z in DIZHI_ORDER)

    return _ghost_in(si_ke[2]) and _ghost_in(si_ke[3])


# ══════════════════════════════════════════════════════════════
# P1 贵人系收敛谓词（2026-09-02 批次1，判据以毕法赋古籍原文为唯一基准）
# 文末注明支撑规则；原文依据见 docs/变格规则库收敛方案
# ══════════════════════════════════════════════════════════════

def _tian_yi_zuo_chen_xu(env):
    """天乙贵人加临地盘辰戌（供 贵人临身/天乙入狱/贵人受贿）
    原文（第47法）：天乙贵人加临地盘辰戌上者，虽名入狱……"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    if not tdp or not tj:
        return False
    for d in ('辰', '戌'):
        tp = tdp.get(d, '')
        if tp and tj.get(tp, '') == '贵人':
            return True
    return False


def _gui_ren_lin_shen(env):
    """贵人临身：天乙加临辰戌，且乙辛二日（反宜干投贵人周全成事）
    原文（第47法）：如是乙辛二日占，却名贵人临身"""
    if env.get('ri_gan', '') not in '乙辛':
        return False
    return _tian_yi_zuo_chen_xu(env)


def _gui_ren_ru_yu(env):
    """天乙入狱：昼夜贵坐地盘辰戌，非乙辛日；辰戌日占为贵人入宅非坐狱
    原文（第47法）：其余八干，昼夜贵人坐地盘辰戌之上，始名天乙入狱"""
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    if not gan or gan in '乙辛':
        return False
    if rz in ('辰', '戌'):
        return False  # 辰戌日占乃为贵人入宅，非坐狱论也
    return _tian_yi_zuo_chen_xu(env)


def _gui_ren_sai_gui_hu(env):
    """贵塞鬼户：三传皆日鬼 + 贵人加临寅（鬼门）
    原文（第52法变格）：壬戌壬辰日巳加寅，三传辰未戌皆鬼；如用昼贵乃名贵人临寅鬼门"""
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', [])
    if not gan or len(sc) != 3:
        return False
    if not all(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc):
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    tdp = env.get('tiandi_pan', {})
    return tdp.get('寅', '') in gui    # 昼/夜贵支加临寅位


def _gui_ren_xing_shun(env):
    """贵人顺治格：一日内全无逆贵人
    原文（第46法变格）：唯有巳为月将，甲戊庚日有之，内有空亡贵人乃无用"""
    yj = (env.get('yuejiang', '') or '').replace('将', '').strip()
    return yj == '巳' and env.get('ri_gan', '') in '甲戊庚'


def _gui_ren_xing_ni(env):
    """贵人逆治格：一日内全无顺贵人
    原文（第46法变格）：惟亥为月将，甲戊庚日有之，内忌空亡"""
    yj = (env.get('yuejiang', '') or '').replace('将', '').strip()
    return yj == '亥' and env.get('ri_gan', '') in '甲戊庚'


def _gui_fu_gan_zhi(env):
    """贵覆干支格：干支上皆乘昼夜贵人（一目昼一夜，甲乙两贵分临干支）
    原文（第45法变格）：如甲申日干上丑、支上未，庚寅日干上未、支上丑…"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or not gs or not zs:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    return gs != zs and {gs, zs} == set(gui)


def _gui_deng_tian_men(env):
    """神藏煞没格：甲戊庚日，丑未为昼夜贵加地盘亥（贵登天门，百煞拱护）
    原文（第52法变格）：如甲戊庚三日以丑未临亥者尤的…丑未为昼夜贵加地盘亥，乃名贵登天门"""
    if env.get('ri_gan', '') not in '甲戊庚':
        return False
    tdp = env.get('tiandi_pan', {})
    return tdp.get('亥', '') in ('丑', '未')


def _gui_shang_gui(env):
    """昼夜贵相加格：贵临贵位（昼贵加临夜贵支位或反之）
    原文（第45法）：六处有旦暮天乙相加者…如六丁日亥加酉昼，丁巳丁亥丁丑日酉加亥夜…
    盖贵临贵位，乃官人见官人也"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    zhou_gui, ye_gui = gui
    tdp = env.get('tiandi_pan', {})
    if not tdp:
        return False
    zpos = [d for d, tp in tdp.items() if tp == zhou_gui]
    ypos = [d for d, tp in tdp.items() if tp == ye_gui]
    # 昼贵加在夜贵支位（地盘=夜贵支），或夜贵加在昼贵支位
    return (ye_gui in zpos) or (zhou_gui in ypos)


def _gui_cheng_tian_yi(env):
    """鬼乘天乙：日鬼临干或支，且乘贵人
    原文（第48法）：如六辛日午加干，如用昼占，虽是日鬼临身，缘为贵人…
    又六丙日昼将亥加巳或亥加支，六丁日昼将亥加未，六乙日申加乙或申加支"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    for x in (gs, zs):
        if x and x in gui and _zhi_ke(x, gan) and _wx(x) != _wx(gan):
            return True
    return False


def _bai_hu_lin_chou(env):
    """白虎乘临丑格：白虎临丑（丑乃天乙本家，不宜见白虎）
    原文（第49法变格）：白虎或乘临丑格，乃贵人怒恶之貌…缘丑乃天乙之本家，不宜见白虎也"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    tp = tdp.get('丑', '')
    return bool(tp and tj.get(tp, '') == '白虎')


def _zhu_que_ke_gui(env):
    """贵人忌惮格：贵人临身 + 朱雀乘神克贵人
    原文（第49法变格）：如甲日丑加寅，乃昼贵临身…缘朱雀乘卯而克天乙之丑土故也；
    又六己日申为夜贵临身，朱雀乘午而克贵。
    【BUG-FIX 2026-09-02】原实现只要盘上朱雀乘神克任一贵即命中（37.5%过宽）；
    按原文补"贵人临干支（临身）"前提。"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    # 先定贵人是否临身（临干或临支）
    lin_shen = None
    for x in (gs, zs):
        if x in gui:
            lin_shen = x
            break
    if not lin_shen:
        return False
    tj = env.get('tian_jiang', {})
    return any(j == '朱雀' and _zhi_ke(z, lin_shen) for z, j in tj.items())


def _zhu_que_lin_wu(env):
    """真朱雀格：朱雀临午，惟可求文书于朝廷
    原文（第49法变格）：真朱雀格，缘朱雀临午，惟可求文书于朝廷或达于至尊之前最宜"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    tp = tdp.get('午', '')
    return bool(tp and tj.get(tp, '') == '朱雀')


def _shen_jia_wu_bai_hu_tou_zhuque(env):
    """申加午白虎投朱雀：盘上申加午，申乘白虎
    原文（第43法）：凡申加午为白虎投朱雀…皆主讼"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    return tdp.get('午', '') == '申' and tj.get('申', '') == '白虎'


def _wu_jia_chen_zhuque_tou_gouchen(env):
    """午加辰朱雀投勾陈：盘上午加辰，午乘朱雀
    原文（第43法）：午加辰为朱雀投勾陈，皆主讼"""
    tdp = env.get('tiandi_pan', {})
    tj = env.get('tian_jiang', {})
    return tdp.get('辰', '') == '午' and tj.get('午', '') == '朱雀'


def _hai_gui(env):
    """害贵格：初传与贵人相害（贵人与六害同处）
    原文（第43法）：甲申日未加申为夜贵…初传子与未又为害；五甲日未加寅用夜贵亦如其说"""
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', [])
    if not gan or not sc or not sc[0]:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    chu = sc[0]
    return any(chu and gui_zhi and LIU_HAI.get(chu, '') == gui_zhi for gui_zhi in gui)


def _hai_gui_used(env):
    """害贵格（仅所用之贵）：初传与「当用之贵」相害（昼占害昼贵、夜占害夜贵）。
    毕法赋·害贵讼直作屈断43「如甲申日未加申为夜贵…初传子与未又为害」——初传所害正是
    该夜占所用之贵未；原 hai_gui 同时查昼夜二贵命中 20.83% 过宽 → 按"害所干之贵"收敛。
    【B5e 2026-09-04】实测仅按用贵判定 10.42%。"""
    gan = env.get('ri_gan', '')
    sc = env.get('sanchuan', [])
    if not gan or not sc or not sc[0]:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    chu = sc[0]
    gz = gui[0] if env.get('is_day', True) else gui[1]
    return bool(chu and gz and LIU_HAI.get(chu, '') == gz)


def _qu_zhi_zuo_gui(env):
    """曲直作鬼枷锢：六己日曲直课（亥卯未木局）作鬼，卯加亥先曲后直，卯加未先直后曲
    原文（第43法变格）：曲直作鬼枷锢，如六己日逢曲直课也，卯加亥先曲后直，卯加未先直后曲"""
    if env.get('ri_gan', '') != '己':
        return False
    sc = env.get('sanchuan', [])
    if len(sc) != 3 or set(sc) != {'亥', '卯', '未'}:
        return False
    tdp = env.get('tiandi_pan', {})
    return tdp.get('亥', '') == '卯' or tdp.get('未', '') == '卯'


def _liang_gui_jia_mu(env):
    """两贵夹墓：日干墓神乘贵人将（且按原文加临）
    原文（第53法变格外）：六甲日未加丑夜贵，两贵夹墓；六庚日丑加丑，两贵夹墓"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    mu = WX_MU.get(_wx(gan), '')
    if not mu:
        return False
    tj = env.get('tian_jiang', {})
    if tj.get(mu, '') != '贵人':
        return False
    # 原文例：六甲日未加丑 / 六庚日丑加丑
    tdp = env.get('tiandi_pan', {})
    if gan == '甲':
        return tdp.get('丑', '') == '未'
    if gan == '庚':
        return tdp.get('丑', '') == '丑'
    return True  # 其余干支以"日墓乘贵"表达


def _duo_mu_sha(env):
    """咄目煞：夜占用贵人（贵人咄目专视，反坐罪也，大不利告贵）
    原文（第44法变格）：如用夜贵，乃名咄目煞，如贵人咄目专视，反坐罪也"""
    if env.get('is_day', True):
        return False
    gs = env.get('gan_shang', '')
    tj = env.get('tian_jiang', {})
    return bool(gs and tj.get(gs, '') == '贵人')


def _ye_gui_nei_zhan(env):
    """夜贵内战格：六癸日卯临申为用
    原文（毕法赋下篇）：夜贵内战格，六癸日卯临申为用"""
    if env.get('ri_gan', '') != '癸':
        return False
    sc = env.get('sanchuan', [])
    if not sc or sc[0] != '卯':
        return False
    tdp = env.get('tiandi_pan', {})
    return tdp.get('申', '') == '卯'


def _dou_gui_xiang_jia(env):
    """斗鬼相加格：丑加未或未加丑（斗鬼相加中魁元）
    原文（功名类）：丑加未或未加丑，斗鬼相加中魁元"""
    tdp = env.get('tiandi_pan', {})
    return tdp.get('未', '') == '丑' or tdp.get('丑', '') == '未'


def _de_ru_tian_men(env):
    """德入天门格：日德加亥为用（初传=日德，且德支加临地盘亥）
    原文（功名类）：德入天门格，日德加亥为用"""
    de = env.get('de', '')
    sc = env.get('sanchuan', [])
    if not de or not sc or sc[0] != de:
        return False
    tdp = env.get('tiandi_pan', {})
    return tdp.get('亥', '') == de


def _ya_kui_xing(env):
    """亚魁星：天盘酉临日干（寄宫）或日支（占试必高中）
    原文（功名类）：亚魁星，天盘酉临年命日干，占试必高中（年命依赖项人工复核）"""
    tdp = env.get('tiandi_pan', {})
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    gan_di = GAN_JIGONG.get(gan, '')
    if gan_di and tdp.get(gan_di, '') == '酉':
        return True
    return bool(rz and tdp.get(rz, '') == '酉')


def _en_zhu_jv_jian(env):
    """恩主举荐：传年日辰有父母爻（生干者），或长生作贵人
    简化判据：干上或三传中支乘贵人且生日干（父母爻）"""
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    sc = env.get('sanchuan', [])
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0]:
        return False
    cands = [z for z in ([gs] + list(sc)) if z]
    return any(z in gui and _zhi_sheng(z, gan) for z in cands)


def _gui_lin_gan(env):
    """贵人临干：干上神乘贵人（拱贵格基础）"""
    gs = env.get('gan_shang', '')
    tj = env.get('tian_jiang', {})
    return bool(gs and tj.get(gs, '') == '贵人')


def _liang_gui_yin_cong(env):
    """两贵引从：初末传为昼夜二贵，且初末传【加临之地盘】分别引/从日干（寄宫）或日支
    原文（第1法·两贵引从天干格）：如壬子日初传巳加子为昼贵，末传卯加戌为夜贵…
    壬子日（壬寄亥）：初传巳加子（子顺行亥前1格）为引，末传卯加戌（戌顺行亥前11格即后1格）为从。
    【BUG-FIX 2026-09-02】原实现用天盘初末传本身与寄宫比前后（顺行差 2~11 格皆判为前/后，判据过阔），
    按原文统一为『加临地盘』判据，与 _qian_hou_yin_cong 同口径：前=顺行 1~6 格，后=顺行 7~11 格。"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    chu, mo = sc[0], sc[2]
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0] or not gui[1]:
        return False
    if {chu, mo} != set(gui):
        return False
    tdp = env.get('tiandi_pan', {})
    if not tdp or not isinstance(tdp, dict):
        return False

    # 反查初/末传天盘所加临的地盘（tdp: {地盘: 天盘}）
    def di_pan(zhi):
        for d, tp in tdp.items():
            if tp == zhi:
                return d
        return ''
    chu_di, mo_di = di_pan(chu), di_pan(mo)
    if not chu_di or not mo_di:
        return False
    anchors = set()
    gj = GAN_JIGONG.get(gan, '')
    zhi = env.get('ri_zhi', '')
    if gj:
        anchors.add(gj)
    if zhi:
        anchors.add(zhi)
    for anchor in anchors:
        d_chu = _zhi_dist(chu_di, anchor)
        d_mo = _zhi_dist(mo_di, anchor)
        if 1 <= d_chu <= 6 and 7 <= d_mo <= 11:
            return True
    return False


def _gui_gong_nian_ming(env):
    """两贵拱年命：两贵（干支上昼夜配对 或 初末传为二贵）夹住年命支
    原文（第1法·昼夜贵人临干支上拱其年命在内者）：如丁酉日酉加丁，亥加酉，占人年命在申；
    二贵拱年命格：如癸未日初传巳加子，未传卯加戌，占人行年本命在亥"""
    bmz = env.get('ben_ming_zhi', '')
    if not bmz:
        return False
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan, ('', ''))
    if not gui[0] or not gui[1]:
        return False
    pair = None
    gs, zs = env.get('gan_shang', ''), env.get('zhi_shang', '')
    if gs and zs and gs in gui and zs in gui and gs != zs:
        pair = (gs, zs)
    else:
        sc = env.get('sanchuan', [])
        if len(sc) == 3 and {sc[0], sc[2]} == set(gui):
            pair = (sc[0], sc[2])
    if not pair:
        return False
    a, b = pair
    return (_is_zhi_before(a, bmz) and _is_zhi_after(b, bmz)) or \
           (_is_zhi_before(b, bmz) and _is_zhi_after(a, bmz))


def _nian_ming_po_wang(env):
    """年命破网（天罗地网无咎）：干支上神为天罗(辰)/地网(戌)，年命上神冲破之；或网逢空亡亦为破罗破网。
    原文（天罗地网）：「如占人年命上神冲破支干之网，始无咎也，或遇空亡亦名破罗破网」。
    【P4 收敛 2026-09-03】原规则条件 x_chong_y(初,干) 将地支冲结果与天干比较，类型不匹配恒假 →
    改为本谓词：干支上为网(辰戌) 且 (网空亡 或 年命上神冲网)。"""
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if gs not in ('辰', '戌') and zs not in ('辰', '戌'):
        return False
    net = gs if gs in ('辰', '戌') else zs
    kong = env.get('kongwang') or ('', '')
    if net in kong:
        return True
    bmz = env.get('ben_ming_zhi', '')
    tdp = env.get('tiandi_pan', {}) or {}
    if not bmz or not tdp:
        return False
    nian_shang = tdp.get(bmz, '')
    if not nian_shang:
        return False
    return LIU_CHONG.get(nian_shang, '') == net or LIU_CHONG.get(net, '') == nian_shang


_ATOMS = {
    # 五行生克
    'gan_sheng': _gan_sheng, 'x_sheng_gan': _x_sheng_gan,
    'x_ke_gan': _x_ke_gan, 'gan_ke_x': _gan_ke_x, 'x_bi_gan': _x_bi_gan,
    'zhi_sheng': _zhi_sheng_zhi, 'zhi_ke': _zhi_ke_zhi,
    # 墓/空亡
    'x_shi_gan_mu': _x_shi_gan_mu, 'x_shi_zhi_mu': _x_shi_zhi_mu, 'x_kong': _x_kong,
    # 合害冲刑
    'x_he_y': _x_he_y, 'x_hai_y': _x_hai_y, 'x_chong_y': _x_chong_y, 'x_xing_y': _x_xing_y,
    'gui_gong_nian_ming': _gui_gong_nian_ming, 'nian_ming_po_wang': _nian_ming_po_wang,
    # 天将
    'x_cheng': _x_cheng, 'x_cheng_ji': _x_cheng_ji, 'x_cheng_xiong': _x_cheng_xiong, 'j_ke_x': _j_ke_x,
    'j_sheng_gan': _j_sheng_gan, 'j_ke_gan': _j_ke_gan, 'x_ke_j': _x_ke_j,
    # 课体/三传
    'shi_keti': _shi_keti, 'sc_set': _sc_set, 'sc_has': _sc_has,
    'sc_quanyang': _sc_quanyang, 'sc_quanyin': _sc_quanyin, 'sc_sanhe': _sc_sanhe, 'sc_quanzhong': _sc_quanzhong,
    'sc_ju': _sc_ju, 'keti_liuyang': _keti_liuyang, 'keti_liuyin': _keti_liuyin,
    'chu_shi': _chu_shi, 'mo_shi': _mo_shi,
    # 神煞
    'x_shi_shensha': _x_shi_shensha, 'x_shi_lu': _x_shi_lu, 'x_shi_de': _x_shi_de, 'x_shi_yima': _x_shi_yima,
    'yima_bei_chong': _yima_bei_chong,          # 驿马被冲破/官爵淹留（B5e 2026-09-04）
    # 旺相
    'x_wang': _x_wang, 'x_wang_xiang': _x_wang_xiang, 'x_shuai': _x_shuai,
    # 年命
    'benming_shi': _benming_shi, 'x_ke_benming': _x_ke_benming,
    # 上神
    'gan_shang_shi': _gan_shang_shi, 'zhi_shang_shi': _zhi_shang_shi,
    'gan_shang_yang': _gan_shang_yang, 'gan_shang_yin': _gan_shang_yin,
    'gan_yin_shen_yang': _gan_yin_shen_yang, 'gan_yin_shen_yin': _gan_yin_shen_yin,
    'gan_shi': _gan_shi, 'zhi_shi': _zhi_shi,
    # 连茹/合/贵人/阴阳
    'sc_jinlianru': _sc_jinlianru, 'sc_tuilianru': _sc_tuilianru,
    'ganzhi_he': _ganzhi_he, 'ganzhi_shang_he': _ganzhi_shang_he,
    'x_shi_guiren': _x_shi_guiren, 'gan_yang': _gan_yang, 'gan_yin': _gan_yin,
    'x_wang_xiang': _x_wang_xiang,
    # 初传孟仲季/天将入传
    'chu_meng': _chu_meng, 'chu_zhong': _chu_zhong, 'chu_ji': _chu_ji,
    'tianjiang_ru_chuan': _tianjiang_ru_chuan, 'season_shi': _season_shi,
    # 昼夜
    'is_day': _is_day,
    # 囚死/天乙前后/末传刑害（三光失明·埋影/三阳开泰/微服蹉跎等）
    'x_qiu_si': _x_qiu_si, 'tianyi_shun': _tianyi_shun,
    'richen_zai_tianyi_qian': _richen_zai_tianyi_qian, 'richen_zai_tianyi_hou': _richen_zai_tianyi_hou,
    'mo_xinghai_jiaohu': _mo_xinghai_jiaohu,
    'tp_jia': _tp_jia, 'x_shi_siqi': _x_shi_siqi, 'xiaochuan': _xiaochuan,
    # 第27法专用：传财化鬼财休觅（原文五格，2026-09-21）
    'zhuan_cai_hua_gui': _zhuan_cai_hua_gui,
    # 第9法专用：避难逃生须弃旧（原文格义，2026-09-21）
    'bi_nan_tao_sheng': _bi_nan_tao_sheng,
    'x_shi_bai': _x_shi_bai,
    'tian_gang_bi_gan': _tian_gang_bi_gan, 'tian_gang_bi_zhi': _tian_gang_bi_zhi,
    'shen_jia_fu_ming': _shen_jia_fu_ming, 'qi_xing_nian_shang_yang': _qi_xing_nian_shang_yang, 'qi_xing_nian_shang_yin': _qi_xing_nian_shang_yin,
    'jiang_lin_siqi': _jiang_lin_siqi, 'x_dun_gan': _x_dun_gan,
    'gan_shang_dun_gui': _gan_shang_dun_gui, 'ganzhi_tong_gong': _ganzhi_tong_gong,
    'taishen_zuo_changsheng': _taishen_zuo_changsheng, 'taishen_lin_jue': _taishen_lin_jue,
    'x_zhi_wang': _x_zhi_wang,
    # ── 财/鬼谓词（2026-08-21 新增：支持毕法赋规则迁移） ──
    'x_shi_cai': _x_shi_cai, 'x_shi_gui': _x_shi_gui,
    'sc_quancai': _sc_quancai, 'sc_quangui': _sc_quangui,
    'sc_chu_cai_mo_gui': _sc_chu_cai_mo_gui,
    'sc_chu_sheng_zhong_sheng_mo': _sc_chu_sheng_zhong_sheng_mo,
    'sc_chu_ke_zhong_ke_mo': _sc_chu_ke_zhong_ke_mo,
    'sc_mo_sheng_zhong_sheng_chu': _sc_mo_sheng_zhong_sheng_chu,
    'sc_mo_ke_zhong_ke_chu': _sc_mo_ke_zhong_ke_chu,
    'x_sheng_chu': _x_sheng_chu, 'x_sheng_mo': _x_sheng_mo,
    'x_ke_chu': _x_ke_chu, 'x_ke_mo': _x_ke_mo,
    'mo_sheng_gan': _mo_sheng_gan, 'chu_sheng_gan': _chu_sheng_gan,
    'mo_ke_gan': _mo_ke_gan, 'chu_ke_gan': _chu_ke_gan,
    # ── 三传内部生克（2026-08-21 新增：兜底规则精细化）──
    'mo_sheng_chu': _mo_sheng_chu, 'mo_ke_chu': _mo_ke_chu,
    'zhong_sheng_chu': _zhong_sheng_chu, 'zhong_ke_chu': _zhong_ke_chu,
    'zhong_sheng_mo': _zhong_sheng_mo, 'zhong_ke_mo': _zhong_ke_mo,
    'gan_sheng_chu': _gan_sheng_chu, 'gan_sheng_zhong': _gan_sheng_zhong, 'gan_sheng_mo': _gan_sheng_mo,
    'gan_ke_chu': _gan_ke_chu,
    'zhi_sheng_chu': _zhi_sheng_chu, 'zhi_ke_chu': _zhi_ke_chu,
    # ── 复合变格谓词（毕法赋主法对应）──
    'mo_zhu_chu_sheng_gan': _mo_zhu_chu_sheng_gan,
    'mo_zhu_chu_ke_gan': _mo_zhu_chu_ke_gan,
    'mo_zhu_chu_zuo_cai': _mo_zhu_chu_zuo_cai,
    'en_duo_yuan_shen': _en_duo_yuan_shen,
    'ku_qu_gan_lai': _ku_qu_gan_lai,
    'liang_gui_jia_gan': _liang_gui_jia_gan,
    'liang_she_jia_mu': _liang_she_jia_mu,
    'liang_hu_jia_mu': _liang_hu_jia_mu,
    'liang_kong_jia_mu': _liang_kong_jia_mu,
    'liang_chang_jia_mu': _liang_chang_jia_mu, 'liang_hou_jia_mu': _liang_hou_jia_mu,
    'zhi_shang_sheng_gan': _zhi_shang_sheng_gan,
    'gan_shang_sheng_gan': _gan_shang_sheng_gan,
    'gan_shang_ke_gan': _gan_shang_ke_gan,
    'zhi_shang_ke_gan': _zhi_shang_ke_gan,
    'gan_zhi_shang_jie_ke_gan': _gan_zhi_shang_jie_ke_gan,
    'san_chuan_wu_yi_shou_sheng': _san_chuan_wu_yi_shou_sheng,
    'liu_yao_xian_gua_father': _liu_yao_xian_gua_father,
    'liu_yao_xian_gua_offspring': _liu_yao_xian_gua_offspring,
    'liu_yao_xian_gua_official': _liu_yao_xian_gua_official,
    'liu_yao_xian_gua_wealth': _liu_yao_xian_gua_wealth,
    'liu_yao_xian_gua_brother': _liu_yao_xian_gua_brother,
    'san_chuan_sheng_gan_shang': _san_chuan_sheng_gan_shang,
    'bingfu_wuyin': _bingfu_wuyin,
    'ren_zhai_zuo_mu': _ren_zhai_zuo_mu,
    'gan_zhi_cheng_mu': _gan_zhi_cheng_mu,
    'zhi_cheng_mu_hu': _zhi_cheng_mu_hu,
    'zhi_fen_cai_bing': _zhi_fen_cai_bing,
    'shu_zhai_kuan_guang': _shu_zhai_kuan_guang,
    'shu_zhai_xia_zhai': _shu_zhai_xia_zhai,
    'tai_yang_she_zhai': _tai_yang_she_zhai,
    'tian_wang_zi_guo': _tian_wang_zi_guo, 'gang_se_gui_hu': _gang_se_gui_hu,
    'bai_hu_lin_gan': _bai_hu_lin_gan, 'hu_cheng_dun_gui': _hu_cheng_dun_gui,
    'hu_shi_feng_hu': _hu_shi_feng_hu,
    'gui_lin_san_si': _gui_lin_san_si,
    'bi_kou_gua': _bi_kou_gua,
    # ── P4 旬首旬尾收敛（2026-09-03 新增）──
    'bi_kou_gua_dipan': _bi_kou_gua_dipan,
    'bi_kou_gua_xunwei': _bi_kou_gua_xunwei,
    'sanhe_sheng_gan_shang': _sanhe_sheng_gan_shang,
    'xun_shou_lian_mu': _xun_shou_lian_mu,
    'chen_xu_xun_shou': _chen_xu_xun_shou,
    'gan_zhi_jue': _gan_zhi_jue,
    'gan_zhi_jie_bai': _gan_zhi_jie_bai,
    'tuo_shang_feng_tuo': _tuo_shang_feng_tuo,
    'chuan_gui_hua_cai': _chuan_gui_hua_cai,
    'chuan_mu_ru_mu': _chuan_mu_ru_mu,
    'chu_zao_jia_ke': _chu_zao_jia_ke,
    'bing_fu_ke_zhai': _bing_fu_ke_zhai,
    'sang_diao_quan_feng': _sang_diao_quan_feng,
    'hou_po_bi_po': _hou_po_bi_po,
    'hu_shi_peng_hu': _hu_shi_peng_hu,
    'zun_chong_san_qi': _zun_chong_san_qi,
    'yi_zai_xiong_tao': _yi_zai_xiong_tao,
    'zhong_gui_bu_wei': _zhong_gui_bu_wei,
    # ── B5b 宽松度收敛（2026-09-03 新增）──
    'ke_xiong_qi_gua': _ke_xiong_qi_gua,
    'gan_shang_jue': _gan_shang_jue,
    'le_li_sheng_you': _le_li_sheng_you,
    'zhi_jia_gan_shang_sheng_gan': _zhi_jia_gan_shang_sheng_gan,
    'zhi_gan_shang_xiang_sheng': _zhi_gan_shang_xiang_sheng,
    # ── B5c 求财族群收敛（2026-09-03 新增）──
    'lan_qu_qu_cai': _lan_qu_qu_cai,
    'san_chuan_cheng_tu': _san_chuan_cheng_tu,
    'san_chuan_yi_tu': _san_chuan_yi_tu,
    'san_chuan_hu_ke': _san_chuan_hu_ke,
    'wu_wang_jie_wang': _wu_wang_jie_wang,
    'zhi_xuan_mu_hu_you_fu_shi': _zhi_xuan_mu_hu_you_fu_shi,
    'tai_sui_yong_zhen': _tai_sui_yong_zhen,
    'shou_wei_xiang_jian': _shou_wei_xiang_jian,
    'you_shi_wu_zhong': _you_shi_wu_zhong,
    'kong_kong_ru_ye': _kong_kong_ru_ye,
    # 【BUG-FIX 2026-09-11】第74法「四课全空格」专用谓词（原误编译为 kong_kong_ru_ye）
    'si_ke_all_kong': _si_ke_all_kong,
    # 【BUG-FIX 2026-09-11】第74法「鬼空尤妙亦宜制之」专用谓词（原误编译为 kong_kong_ru_ye）
    'gui_kong_you_miao': _gui_kong_you_miao,
    'tuo_shang_you_tuo': _tuo_shang_you_tuo,
    'gui_hua_cai_qian_xian_wei': _gui_hua_cai_qian_xian_wei,
    'mu_zhu_mu_fen_zeng_ai': _mu_zhu_mu_fen_zeng_ai,
    'zhi_guan_shi_zhe_fu': _zhi_guan_shi_zhe_fu,
    'shu_zhai_zhi_ji': _shu_zhai_zhi_ji,
    'you_yu_er_de_bu_zu': _you_yu_er_de_bu_zu,
    # ── 三期迁移谓词（2026-08-21）：64 条硬编码 _check_rule_* → 声明式 ──
    'qian_hou_yin_cong': _qian_hou_yin_cong,
    'shou_wei_xiang_jian_v2': _shou_wei_xiang_jian_v2,
    'lian_mu_gui_ren': _lian_mu_gui_ren,
    'bi_nan_tao_sheng': _bi_nan_tao_sheng,
    'zhuo_lun_xiu_mu': _zhuo_lun_xiu_mu,
    'gui_zei_dang_shi': _gui_zei_dang_shi,
    'tuo_shang_feng_tuo_v2': _tuo_shang_feng_tuo_v2,
    'jinru_kong_wang': _jinru_kong_wang,
    'tuiru_kong_wang': _tuiru_kong_wang,
    'tai_cai_sheng_qi': _tai_cai_sheng_qi,
    'tai_cai_si_qi': _tai_cai_si_qi,
    'zhi_chuan_gan': _zhi_chuan_gan,
    'jin_ri_feng_ding': _jin_ri_feng_ding,
    'shui_ri_feng_ding': _shui_ri_feng_ding,
    'chuan_gui_hua_cai_v2': _chuan_gui_hua_cai_v2,
    'juan_shu_feng_ying': _juan_shu_feng_ying,
    'wu_zhai_kuan_guang_v2': _wu_zhai_kuan_guang_v2,
    'you_shi_wu_zhong_v2': _you_shi_wu_zhong_v2,
    'bi_kou_gua_v2': _bi_kou_gua_v2,
    'tai_yang_zhao_wu': _tai_yang_zhao_wu,
    'zun_chong_san_qi_v2': _zun_chong_san_qi_v2,
    'hou_he_zhan_hun': _hou_he_zhan_hun,
    'fu_gui_gan_zhi': _fu_gui_gan_zhi,
    'ke_chuan_ju_gui': _ke_chuan_ju_gui,
    'tian_luo_di_wang': _tian_luo_di_wang,
    'tian_wang_zi_guo_v2': _tian_wang_zi_guo_v2,
    'fei_you_er_de_bu_zu_v2': _fei_you_er_de_bu_zu_v2,
    'yong_po_shen_xin': _yong_po_shen_xin,
    'tai_yang_she_zhai_v2': _tai_yang_she_zhai_v2,
    'zhi_cheng_mu_hu_v2': _zhi_cheng_mu_hu_v2,
    'gan_mu_bing_guan': _gan_mu_bing_guan,
    'zhi_fen_cai_bing_v2': _zhi_fen_cai_bing_v2,
    'shou_hu_ke_shen': _shou_hu_ke_shen,
    'zhi_gui_liang_yi': _zhi_gui_liang_yi,
    'sang_diao_quan_feng_v2': _sang_diao_quan_feng_v2,
    'hu_sheng_ju_sheng': _hu_sheng_ju_sheng,
    'ren_zhai_jie_si': _ren_zhai_jie_si,
    'hu_cheng_si_qi': _hu_cheng_si_qi,
    'quan_cheng_si_qi': _quan_cheng_si_qi,
    'san_liu_he': _san_liu_he,
    'he_zhong_fan_sha': _he_zhong_fan_sha,
    'chu_zao_jia_ke_v2': _chu_zao_jia_ke_v2,
    'jiang_feng_nei_zhan': _jiang_feng_nei_zhan,
    'ren_zhai_zuo_mu_v2': _ren_zhai_zuo_mu_v2,
    'ren_xin_ding_ma': _ren_xin_ding_ma,
    'lai_qu_ju_kong': _lai_qu_ju_kong,
    'hu_lin_gan_gui': _hu_lin_gan_gui,
    'long_jia_sheng_qi': _long_jia_sheng_qi,
    'wang_yong_san_chuan': _wang_yong_san_chuan,
    'xi_ju_kong_wang': _xi_ju_kong_wang,
    'xun_nei_kong_wang': _xun_nei_kong_wang,
    'suo_shi_bu_ru': _suo_shi_bu_ru,
    'chang_wen_bu_ying': _chang_wen_bu_ying,

    # ── 四期迁移谓词（2026-08-21）：剩余 13 条硬编码 → 声明式 ──
    'ku_qu_gan_lai_le_li_bei': _ku_qu_gan_lai_le_li_bei,
    'hai_gui_song_zhi_zuo_qu': _hai_gui_song_zhi_zuo_qu,
    'zhou_ye_gui_jia': _zhou_ye_gui_jia,
    'gui_ren_cha_die': _gui_ren_cha_die,
    'gui_zai_yu_yi_lin_gan': _gui_zai_yu_yi_lin_gan,
    'liang_gui_shou_ke': _liang_gui_shou_ke,
    'er_gui_jie_kong': _er_gui_jie_kong,
    'liang_she_jia_mu_v2': _liang_she_jia_mu_v2,
    'hu_shi_peng_hu_v2': _hu_shi_peng_hu_v2,
    'gan_cheng_mu_hu': _gan_cheng_mu_hu,
    'hu_cheng_dun_gui': _hu_cheng_dun_gui,
    'gui_lin_san_si_v2': _gui_lin_san_si_v2,
    'yi_zai_xiong_tao_v2': _yi_zai_xiong_tao_v2,

    # ── P1 贵人系收敛谓词（2026-09-02 批次1）──
    'gui_ren_shou_ke': _liang_gui_shou_ke,          # 两贵受克（第49法，天地盘判据）
    'gui_ren_sai_gui_hu': _gui_ren_sai_gui_hu,      # 贵塞鬼户（第52法变格）
    'gui_ren_xing_shun': _gui_ren_xing_shun,        # 顺治格（第46法变格）
    'gui_ren_xing_ni': _gui_ren_xing_ni,            # 逆治格（第46法变格）
    'gui_fu_gan_zhi': _gui_fu_gan_zhi,              # 贵覆干支格（第45法变格，昼夜配对）
    'gui_deng_tian_men': _gui_deng_tian_men,        # 神藏煞没/贵登天门（第52法变格）
    'gui_shang_gui': _gui_shang_gui,                # 昼夜贵相加（第45法）
    'gui_cheng_tian_yi': _gui_cheng_tian_yi,        # 鬼乘天乙（第48法）
    'gui_ren_lin_shen': _gui_ren_lin_shen,          # 贵人临身（第47法，乙辛日）
    'gui_ren_ru_yu': _gui_ren_ru_yu,                # 天乙入狱（第47法，余八干）
    'bai_hu_lin_chou': _bai_hu_lin_chou,            # 白虎临丑（第49法变格）
    'zhu_que_ke_gui': _zhu_que_ke_gui,              # 贵人忌惮（第49法变格）
    'zhu_que_lin_wu': _zhu_que_lin_wu,              # 真朱雀（第49法变格）
    'shen_jia_wu_bai_hu_tou_zhuque': _shen_jia_wu_bai_hu_tou_zhuque,  # 申加午白虎投朱雀（第43法）
    'wu_jia_chen_zhuque_tou_gouchen': _wu_jia_chen_zhuque_tou_gouchen,  # 午加辰朱雀投勾陈（第43法）
    'hai_gui': _hai_gui,                            # 害贵格（第43法）
    'hai_gui_used': _hai_gui_used,                  # 害贵格·仅所用之贵（B5e 2026-09-04）
    'qu_zhi_zuo_gui': _qu_zhi_zuo_gui,              # 曲直作鬼枷锢（第43法变格）
    'liang_gui_jia_mu': _liang_gui_jia_mu,          # 两贵夹墓（第53法变格外）
    'duo_mu_sha': _duo_mu_sha,                      # 咄目煞（第44法变格）
    'ye_gui_nei_zhan': _ye_gui_nei_zhan,            # 夜贵内战（下篇变格）
    'dou_gui_xiang_jia': _dou_gui_xiang_jia,        # 斗鬼相加（功名类）
    'de_ru_tian_men': _de_ru_tian_men,              # 德入天门（功名类）
    'ya_kui_xing': _ya_kui_xing,                    # 亚魁星（功名类，年命依赖已简化）
    'en_zhu_jv_jian': _en_zhu_jv_jian,              # 恩主举荐（功名类）
    'gui_lin_gan': _gui_lin_gan,                    # 贵临干（拱贵基础）
    'liang_gui_yin_cong': _liang_gui_yin_cong,      # 两贵引从（第1法，初末传二贵夹干/支）
    'gui_gong_nian_ming': _gui_gong_nian_ming,      # 两贵拱年命（第1法，两贵夹年命支）

    # ── P2 刑害类收敛谓词（2026-09-02 批次2）──
    'zhi_eq': _zhi_eq,                              # 通用相等（四胜煞用）
    'si_ke_shang_all': _si_ke_shang_all,            # 一字刑：四课上神全∈集合（辰午酉亥）
    'san_chuan_xing': _san_chuan_xing,              # 三字刑：三传寅巳申/丑戌未
    'zhu_xing_qiang_de': _zhu_xing_qiang_de,        # 助刑戕德（宾主不投刑·第75法变格）
    'de_shao_shi_duo': _de_shao_shi_duo,            # 得少失多（费有余而得不足·第57法）
    # ── P3 神煞类收敛谓词（2026-09-02 批次3）──
    'shi_gan_wang': _shi_gan_wang,                  # 值干之罗网：loc=日干帝旺（干前一辰）
    'shi_zhi_qian': _shi_zhi_qian,                  # 值支之罗网：loc=日支顺行下一支（支前一辰）
    'sc_has_sha': _sc_has_sha,                      # 三传任一支为某神煞（替代 sc_has(神煞名) 占位）

    # ── B5d 鬼类族群收敛谓词（2026-09-03 批次5d）──
    'de_shen_wei_gui': _de_shen_wei_gui,            # 德神为鬼：德坐鬼方（德庆课）
    'zhi_shang_dun_gui': _zhi_shang_dun_gui,        # 支上神遁旬干为日鬼（明暗二鬼之暗鬼）
    'gui_ren_zuo_mu': _gui_ren_zuo_mu,              # 贵人作墓：贵神作四墓加干
    'gui_ren_tuo_qi': _gui_ren_tuo_qi,              # 贵人脱气：贵神为日干脱气
    'bu_xing_zhong_xing': _bu_xing_zhong_xing,      # 不幸中幸/幸中不幸：白虎作长生/青龙乘日鬼
    'hu_zhi_yin_shen_zhi_hu': _hu_zhi_yin_shen_zhi_hu,  # 虎之阴神制虎：虎鬼得制
    'gui_zuo_gui_fang': _gui_zuo_gui_fang,          # 鬼坐鬼方无所畏：鬼坐于己之克地
    'gui_zi_jiu_sheng': _gui_zi_jiu_sheng,          # 鬼自就生不来侵：鬼临其长生位
    'tian_gui_zuo_ri_gui': _tian_gui_zuo_ri_gui,    # 天鬼作日鬼：天鬼临处且为日鬼
}
