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
    """两蛇夹墓：初末传为日干之墓，乘螣蛇"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    chu_mo_mu = (sc[0] == mu and sc[2] == mu)
    if not chu_mo_mu:
        return False
    tj = env.get('tian_jiang', {})
    return (tj.get(sc[0]) == '螣蛇' or tj.get(sc[2]) == '螣蛇')


def _liang_hu_jia_mu(env):
    """两虎夹墓：六辛日丑加申，初末为墓乘白虎"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    chu_mo_mu = (sc[0] == mu and sc[2] == mu)
    if not chu_mo_mu:
        return False
    tj = env.get('tian_jiang', {})
    return (tj.get(sc[0]) == '白虎' or tj.get(sc[2]) == '白虎')


def _liang_kong_jia_mu(env):
    """两空夹墓：初末传为日干之墓，乘天空"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    if not mu:
        return False
    chu_mo_mu = (sc[0] == mu and sc[2] == mu)
    if not chu_mo_mu:
        return False
    tj = env.get('tian_jiang', {})
    return (tj.get(sc[0]) == '天空' or tj.get(sc[2]) == '天空')


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


def _liu_yao_xian_gua_father(env):
    """父母爻现卦：三传中有生日干者（父母爻之象）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan = env['ri_gan']
    return any(_zhi_sheng(z, gan) and _wx(z) != _wx(gan) for z in sc)


def _liu_yao_xian_gua_offspring(env):
    """子息爻现卦：三传中有日干生者（子息爻之象）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan = env['ri_gan']
    return any(_zhi_sheng(gan, z) for z in sc)


def _liu_yao_xian_gua_official(env):
    """官鬼爻现卦：三传中有克日干者（官鬼爻之象）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan = env['ri_gan']
    return any(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)


def _liu_yao_xian_gua_wealth(env):
    """妻财爻现卦：三传中有日干克者（妻财爻之象）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan = env['ri_gan']
    return any(_zhi_ke(gan, z) and _wx(z) != _wx(gan) for z in sc)


def _liu_yao_xian_gua_brother(env):
    """兄弟爻现卦：三传中有与日干同行者（兄弟爻之象）"""
    sc = env.get('sanchuan', [])
    if not sc or len(sc) != 3:
        return False
    gan_wx = _wx(env['ri_gan'])
    return any(_wx(z) == gan_wx and z != env['ri_gan'] for z in sc)


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
    """罡塞鬼户：天罡（辰）加临鬼户（寅/申）"""
    d = _tian_gang_jia(env)
    return d in ('寅', '申')


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
    """传墓入墓：初传为日干之墓，末传亦为墓（分憎爱）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    return bool(mu and sc[0] == mu and sc[2] == mu)


def _chu_zao_jia_ke(env):
    """初遭夹克：初传上下俱受克（不由己）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    chu = sc[0]
    # 上克下（天将克初）+ 下克上（初克日干或日干克初）
    tj = env.get('tian_jiang', {})
    jiang_wx = TIANJIANG_WX_MAP.get(tj.get(chu, ''), '')
    chu_wx = _wx(chu)
    # 初传被天将克（上克下）+ 初传被日干克或克日干（下克上/上克下）= 夹克
    return (bool(jiang_wx and _zhi_ke(jiang_wx, chu_wx)) and
            (_zhi_ke(env['ri_gan'], chu) or _zhi_ke(chu, env['ri_gan'])))


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
    return (bool(jiang_chu and _zhi_ke(jiang_chu, chu_wx)) and
            bool(jiang_mo and _zhi_ke(jiang_mo, mo_wx)))


def _hu_shi_peng_hu(env):
    """虎视逢虎：白虎乘临旺相（力难施）"""
    tj = env.get('tian_jiang', {})
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    has_hu = any(tj.get(z) == '白虎' for z in sc)
    return has_hu and _x_wang_xiang(env, '初')


def _zun_chong_san_qi(env):
    """尊崇三奇：三奇入传"""
    return _chu_ji(env) or _chu_meng(env) or _chu_zhong(env)


def _yi_zai_xiong_tao(env):
    """已灾凶逃：三传见鬼墓又空（返无疑）"""
    sc = env.get('sanchuan', ['', '', ''])
    if len(sc) != 3:
        return False
    mu = WX_MU.get(_wx(env['ri_gan']), '')
    gan = env['ri_gan']
    has_gui = any(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc)
    has_mu = bool(mu and any(z == mu for z in sc))
    has_kong = any(z in (env.get('kongwang') or ('', '')) for z in sc)
    return has_gui and (has_mu or has_kong)


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
    return _x_wang_xiang(env, '干上') and _x_wang_xiang(env, '支上')


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
    """空空如也：初传末传俱空"""
    sc = env.get('sanchuan', ['', '', ''])
    kong = env.get('kongwang', ('', ''))
    return bool(sc and len(sc) == 3 and sc[0] in kong and sc[2] in kong)


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
    return _x_wang_xiang(env, '初') and sc[2] in kong


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
GUIREN_MAP = {
    '甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
    '乙': ('子', '申'), '己': ('子', '申'),
    '丙': ('亥', '酉'), '丁': ('亥', '酉'),
    '壬': ('卯', '巳'), '癸': ('卯', '巳'),
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


def _qian_hou_yin_cong(env):
    """第1法 前后引从：初传居干/支前为引，末传居干/支后为从"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    chu, mo = sc[0], sc[2]
    gan_pos = GAN_JIGONG.get(env.get('ri_gan', ''), '')
    zhi = env.get('ri_zhi', '')
    if gan_pos and _is_zhi_before(chu, gan_pos) and _is_zhi_after(mo, gan_pos):
        return True
    if zhi and _is_zhi_before(chu, zhi) and _is_zhi_after(mo, zhi):
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
    gr = env.get('gui_ren', ('', ''))
    if not gr or not gr[0]:
        return False
    is_day = env.get('is_day', True)
    lianmu = gr[1] if is_day else gr[0]  # 昼占夜贵、夜占昼贵
    return gs == lianmu


def _bi_nan_tao_sheng(env):
    """第9法 避难逃生：三传皆鬼或脱气，干上生干"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    if len(sc) != 3 or not gan or not gs:
        return False
    all_bad = all((_zhi_ke(z, gan) and _wx(z) != _wx(gan)) or _zhi_sheng(gan, z) for z in sc)
    if not all_bad:
        return False
    return _zhi_sheng(gs, gan)


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
    """第20法 胎财死气：胎神=月内死气"""
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
    si_zhi = WX_KE.get(si_wx, '')  # 死气=季所克
    return si_zhi in tai_set if si_zhi else False


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
    """第28法 传鬼化财：三传皆鬼+干上制鬼"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    gs = env.get('gan_shang', '')
    if len(sc) != 3 or not gan or not gs:
        return False
    if not all(_zhi_ke(z, gan) and _wx(z) != _wx(gan) for z in sc):
        return False
    return any(_zhi_ke(gs, z) for z in sc)


def _juan_shu_feng_ying(env):
    """第29法 眷属丰盈：三传生干且脱支"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if len(sc) != 3 or not gan or not zhi:
        return False
    return all(_zhi_sheng(z, gan) for z in sc) and all(_zhi_sheng(zhi, z) for z in sc)


def _wu_zhai_kuan_guang_v2(env):
    """第30法 屋宅宽广：三传脱干且生支"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    zhi = env.get('ri_zhi', '')
    if len(sc) != 3 or not gan or not zhi:
        return False
    return all(_zhi_sheng(gan, z) for z in sc) and all(_zhi_sheng(z, zhi) for z in sc)


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


def _tai_yang_zhao_wu(env):
    """第39法 太阳照武：月将乘玄武"""
    yj = env.get('yuejiang', '')
    tj = env.get('tian_jiang', {})
    return bool(yj and tj.get(yj) == '玄武')


def _zun_chong_san_qi_v2(env):
    """第42法 尊崇传内遇三奇：三传旬干=甲戊庚/乙丙丁"""
    sc = env.get('sanchuan', [])
    gz = env.get('ganzhi', '')
    if len(sc) != 3 or not gz:
        return False
    # 查找 gz 所属旬的旬首→旬遁干映射
    gan_map = None
    for xs, gm in XUN_GAN_MAP.items():
        # 旬首天干须与 gz 天干一致，且旬首地支序号 <= gz 地支序号
        if xs[0] == gz[0] and DIZHI_IDX.get(xs[1], -1) <= DIZHI_IDX.get(gz[1], -1):
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
    """第44法 课传俱贵：四课三传皆是昼夜贵人"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gr = env.get('gui_ren', ('', ''))
    if not gr or not gr[0]:
        return False
    gui_set = set(gr)
    sc = env.get('sanchuan', [])
    sike = env.get('si_ke_shang', [])
    all_zhi = [z for z in (sc + sike) if z]
    return all(z in gui_set for z in all_zhi) if all_zhi else False


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
    """第58法 用破身心：初传财空/初传禄空/初中克(财或禄被克)"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    kong = env.get('kongwang', ('', ''))
    lu = env.get('lu', '')
    if len(sc) != 3 or not gan:
        return False
    chu, zhong = sc[0], sc[1]
    is_cai = _zhi_ke(gan, chu) and _wx(chu) != _wx(gan)
    is_lu = chu == lu
    if (is_cai or is_lu) and kong[0] and chu in kong:
        return True
    if _zhi_ke(zhong, chu) and (is_cai or is_lu):
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
    """第67法 受虎克神：课传六处乘白虎，白虎五行克之"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    six = [z for z in (sc + [gs, zs]) if z]
    hu_wx = TIANJIANG_WX_MAP.get('白虎', '')
    for z in six:
        if tj.get(z) == '白虎' and _wx(hu_wx) if hu_wx else False:
            pass  # 白虎五行金，克木
    # 白虎五行=金，金克木
    return any(tj.get(z) == '白虎' and _zhi_ke('金', z) for z in six) if six else False


def _zhi_gui_liang_yi(env):
    """第68法 制鬼之位乃良医：三传中有克鬼之神(食神/子孙爻)"""
    sc = env.get('sanchuan', [])
    gan = env.get('ri_gan', '')
    if len(sc) != 3 or not gan:
        return False
    ghost_wx = WX_KE.get(_wx(gan), '')
    if not ghost_wx:
        return False
    # 克鬼之神 = 克鬼五行的五行
    ke_gui_wx = WX_KE.get(ghost_wx, '')
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
    """第85法 初遭夹克：天将五行克初传+地盘五行克初传"""
    sc = env.get('sanchuan', [])
    tj = env.get('tian_jiang', {})
    tdp = env.get('tiandi_pan', {})
    if len(sc) != 3:
        return False
    chu = sc[0]
    jiang = tj.get(chu, '')
    jiang_wx = TIANJIANG_WX_MAP.get(jiang, '')
    if not jiang_wx:
        return False
    # 天将克初传
    if not _zhi_ke(jiang_wx, chu) if jiang_wx else True:
        return False
    # 地盘克初传（初传所坐地盘）
    # 初传天盘=chu，找地盘：tiandi_pan 是 {地盘:天盘}，反查
    dipan = ''
    for dp, tp in tdp.items():
        if tp == chu:
            dipan = dp
            break
    if not dipan:
        return False
    return _zhi_ke(dipan, chu)


def _jiang_feng_nei_zhan(env):
    """第86法 将逢内战：天将五行克所乘地支五行"""
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    tj = env.get('tian_jiang', {})
    six = [z for z in (sc + [gs, zs]) if z]
    for z in six:
        jiang = tj.get(z, '')
        if not jiang:
            continue
        jwx = TIANJIANG_WX_MAP.get(jiang, '')
        if jwx and _wx(jwx) != _wx(z) and _zhi_ke(jwx, z):
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
    """第89法 任信丁马：伏吟+丁神在六处"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3 or not (sc[0] == sc[1] == sc[2]):
        return False
    ding = env.get('ding_shen', '')
    if not ding:
        return False
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    return ding in sc or ding == gs or ding == zs


def _lai_qu_ju_kong(env):
    """第90法 来去俱空：返吟+三传分旬空亡"""
    sc = env.get('sanchuan', [])
    if len(sc) != 3:
        return False
    if LIU_CHONG.get(sc[0], '') != sc[2]:
        return False
    fxk = env.get('fen_xun_kong')
    if not fxk:
        return False
    ben = fxk.get('本旬', set())
    qian = fxk.get('前旬', set())
    hou = fxk.get('后旬', set())
    waihou = fxk.get('外后旬', set())
    jinru = sc[0] in ben and sc[1] in ben and sc[2] in qian
    tuiru = sc[0] in ben and sc[1] in hou and sc[2] in waihou
    return jinru or tuiru


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
    all_zhi = [z for z in list(sc) + [gs, zs] + list(sike_shang) if z]
    return zhou_gui in all_zhi and ye_gui in all_zhi


def _gui_ren_cha_die(env):
    """第46法 贵人差迭事参差：昼贵临夜地且夜贵临昼方"""
    gan = env.get('ri_gan', '')
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    zhou_gui, ye_gui = gui
    rz = env.get('ri_zhi', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    ye_di = {'酉', '戌', '亥', '子', '丑', '寅'}
    zhou_fang = {'卯', '辰', '巳', '午', '未', '申'}
    gan_di = GAN_JIGONG.get(gan, '')
    zhou_on_ye = (gs == zhou_gui and gan_di in ye_di) or (zs == zhou_gui and rz in ye_di)
    ye_on_zhou = (gs == ye_gui and gan_di in zhou_fang) or (zs == ye_gui and rz in zhou_fang)
    return zhou_on_ye and ye_on_zhou


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
    """第49法 两贵受克难干贵：昼夜贵人皆立于受克之方（地盘克贵人天盘支）"""
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    sc = env.get('sanchuan', [])
    if not gan:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    zhou_gui, ye_gui = gui
    gan_di = GAN_JIGONG.get(gan, '')
    pos = {}
    if gs:
        pos['干上'] = (gs, gan_di)
    if zs:
        pos['支上'] = (zs, rz)
    for i, key in enumerate(['初传', '中传', '末传']):
        if i < len(sc) and sc[i]:
            pos[key] = (sc[i], '')
    zhou_ked = any(tp == zhou_gui and dp and _zhi_ke(dp, zhou_gui) for tp, dp in pos.values())
    ye_ked = any(tp == ye_gui and dp and _zhi_ke(dp, ye_gui) for tp, dp in pos.values())
    return zhou_ked and ye_ked


def _er_gui_jie_kong(env):
    """第50法 二贵皆空虚喜期：昼夜贵人地支皆在旬空"""
    gan = env.get('ri_gan', '')
    kw = env.get('kongwang', ())
    if not gan or not kw:
        return False
    gui = GUIREN_MAP.get(gan)
    if not gui:
        return False
    zhou_gui, ye_gui = gui
    return zhou_gui in kw and ye_gui in kw


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


def _hu_cheng_dun_gui(env):
    """第69法 虎乘遁鬼殃非浅：白虎乘课传六处某支，其旬遁干克日干"""
    gan = env.get('ri_gan', '')
    rz = env.get('ri_zhi', '')
    tj = env.get('tian_jiang', {})
    sc = env.get('sanchuan', [])
    gs = env.get('gan_shang', '')
    zs = env.get('zhi_shang', '')
    if not gan or not rz or not tj:
        return False
    six = [z for z in list(sc) + [gs, zs] if z]
    try:
        g_idx = '甲乙丙丁戊己庚辛壬癸'.index(gan)
        z_idx = DIZHI_ORDER.index(rz)
        shou = (z_idx - g_idx) % 12
    except (ValueError, IndexError):
        return False
    for z in six:
        if tj.get(z) != '白虎':
            continue
        try:
            z2_idx = DIZHI_ORDER.index(z)
            offset = (z2_idx - shou) % 12
            dun = '甲乙丙丁戊己庚辛壬癸'[offset % 10]
            if WX_KE.get(GAN_WX.get(dun, ''), '') == GAN_WX.get(gan, ''):
                return True
        except (ValueError, IndexError):
            continue
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
    'zhi_shang_sheng_gan': _zhi_shang_sheng_gan,
    'gan_shang_sheng_gan': _gan_shang_sheng_gan,
    'zhi_shang_ke_gan': _zhi_shang_ke_gan,
    'gan_zhi_shang_jie_ke_gan': _gan_zhi_shang_jie_ke_gan,
    'san_chuan_wu_yi_shou_sheng': _san_chuan_wu_yi_shou_sheng,
    'liu_yao_xian_gua_father': _liu_yao_xian_gua_father,
    'liu_yao_xian_gua_offspring': _liu_yao_xian_gua_offspring,
    'liu_yao_xian_gua_official': _liu_yao_xian_gua_official,
    'liu_yao_xian_gua_wealth': _liu_yao_xian_gua_wealth,
    'liu_yao_xian_gua_brother': _liu_yao_xian_gua_brother,
    'bingfu_wuyin': _bingfu_wuyin,
    'ren_zhai_zuo_mu': _ren_zhai_zuo_mu,
    'gan_zhi_cheng_mu': _gan_zhi_cheng_mu,
    'zhi_cheng_mu_hu': _zhi_cheng_mu_hu,
    'zhi_fen_cai_bing': _zhi_fen_cai_bing,
    'shu_zhai_kuan_guang': _shu_zhai_kuan_guang,
    'shu_zhai_xia_zhai': _shu_zhai_xia_zhai,
    'tai_yang_she_zhai': _tai_yang_she_zhai,
    'tian_wang_zi_guo': _tian_wang_zi_guo, 'gang_se_gui_hu': _gang_se_gui_hu,
    'gui_lin_san_si': _gui_lin_san_si,
    'bi_kou_gua': _bi_kou_gua,
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
    'san_chuan_hu_ke': _san_chuan_hu_ke,
    'wu_wang_jie_wang': _wu_wang_jie_wang,
    'zhi_xuan_mu_hu_you_fu_shi': _zhi_xuan_mu_hu_you_fu_shi,
    'tai_sui_yong_zhen': _tai_sui_yong_zhen,
    'shou_wei_xiang_jian': _shou_wei_xiang_jian,
    'you_shi_wu_zhong': _you_shi_wu_zhong,
    'kong_kong_ru_ye': _kong_kong_ru_ye,
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
}
