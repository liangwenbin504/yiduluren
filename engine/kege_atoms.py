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
SANHE = [{'申','子','辰'},{'亥','卯','未'},{'寅','午','戌'},{'巳','酉','丑'}]
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
    j = env.get('tian_jiang', {}).get(x, '')
    jw = TIANJIANG_WX_MAP.get(j, '')
    return bool(jw) and WX_KE.get(jw, '') == _wx(x)

def _j_sheng_gan(env, x):
    """x 所乘天将（本家五行）生日干"""
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


_ATOMS = {
    # 五行生克
    'gan_sheng': _gan_sheng, 'x_sheng_gan': _x_sheng_gan,
    'x_ke_gan': _x_ke_gan, 'gan_ke_x': _gan_ke_x, 'x_bi_gan': _x_bi_gan,
    'zhi_sheng': _zhi_sheng_zhi, 'zhi_ke': _zhi_ke_zhi,
    # 墓/空亡
    'x_shi_gan_mu': _x_shi_gan_mu, 'x_shi_zhi_mu': _x_shi_zhi_mu, 'x_kong': _x_kong,
    # 合害冲刑
    'x_he_y': _x_he_y, 'x_hai_y': _x_hai_y, 'x_chong_y': _x_chong_y, 'x_xing_y': _x_xing_y,
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
    'x_shi_bai': _x_shi_bai,
    'tian_gang_bi_gan': _tian_gang_bi_gan, 'tian_gang_bi_zhi': _tian_gang_bi_zhi,
    'shen_jia_fu_ming': _shen_jia_fu_ming, 'qi_xing_nian_shang_yang': _qi_xing_nian_shang_yang, 'qi_xing_nian_shang_yin': _qi_xing_nian_shang_yin,
    'jiang_lin_siqi': _jiang_lin_siqi, 'x_dun_gan': _x_dun_gan,
    'gan_shang_dun_gui': _gan_shang_dun_gui, 'ganzhi_tong_gong': _ganzhi_tong_gong,
    'taishen_zuo_changsheng': _taishen_zuo_changsheng, 'taishen_lin_jue': _taishen_lin_jue,
    'x_zhi_wang': _x_zhi_wang,
}
