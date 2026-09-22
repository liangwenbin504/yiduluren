# -*- coding: utf-8 -*-
"""
判断层编排器（轻量 harness）
============================
统一收口判断层 4 个引擎的调用：
  1. 64 课        judge_64_keti（engine.liuren_64ke_judge）
  2. 毕法赋        judge_bifa（engine.bifa_judge）
  3. 特殊课格      SpecialKegeDetector（engine.special_kege）
  4. 变格（从属格） detect_bianjie（engine.kege_bianjie_engine）

设计要点：
  - 统一 env（课式数据）+ 统一预处理（季节/农历月/行年/旬空，只算一次）
  - 适配层（env → 各引擎各自参数）
  - 调度层（循环 + try/except 隔离 + 聚合）
  - **纯收口重构**：判断逻辑与 stock_dashboard 原散落调用完全一致，A/B 应 1:1 无差异。

这是「轻量 harness」：判断引擎作为可替换的函数插件，编排器统一调度；
但不引入重插件框架（注册表/热加载/配置开关），避免过度设计。
"""
from typing import Dict, List, Tuple, Any


def _season_by_lunar_month(lm: int) -> str:
    """季节按农历月（月建=节气月）定，勿用月将硬映射（月将午≠午月）"""
    return {1: '春', 2: '春', 3: '春', 4: '夏', 5: '夏', 6: '夏',
            7: '秋', 8: '秋', 9: '秋', 10: '冬', 11: '冬', 12: '冬'}.get(lm, '')


def _derive_bifa_ext_keys(env: dict) -> dict:
    """补齐毕法赋谓词需要的派生 env 键（2026-09-21 新增）。

    🔴 **血泪根因**：`build_judge_env` 原本只产 30 个键，而 `kege_atoms` 的谓词
    还读了 16 个它不产的键 ⇒ 恒取默认空值 ⇒ **47 个谓词、15 个法静默失效**
    （实测零中法 4 个：第 2/56/61/72 法），判否又被 judge 的 `except` 吞掉，
    运行时零日志零报错。

    **真源一律复用 `engine.bifa_detector`** —— 那里已有一个**完整版** env 建造者
    （`detect()` 内 `_data_env`），谓词本就是按它写的。⛔ 不在此另立标准。

    ⚠️ 本批**不补**的两类（避免臆造定义）：
      · `de`（日德）—— bifa_detector 里也注释「如需可扩展」，实体未实现 ⇒ 保持 `''`。
      · `shensha`／`si_qi` —— 在任何 env 建造者里都**没有真源** ⇒ 保持缺失，
        相关 4 个谓词仍失效，待专项排期。
    """
    out = {}
    try:
        from engine.bifa_detector import (LU_SHEN, YIMA, GUIREN_MAP, get_ding_shen,
                                          get_xun_shou, get_xun_wei, get_fen_xun_kong,
                                          _extract_sike_shang, _get_sanchuan_trend)
    except Exception:
        return out
    gz = env.get('ganzhi', '')
    rg, rz = env.get('ri_gan', ''), env.get('ri_zhi', '')
    try:
        out['lu'] = LU_SHEN.get(rg, '')                      # 十干禄
        out['yima'] = YIMA.get(rz, '')                       # 驿马（按日支三合）
        gr = GUIREN_MAP.get(rg, ('', ''))                    # (昼贵, 夜贵)
        out['guiren'] = gr
        out['gui_ren'] = gr                                  # 兼容两种键名
        out['ben_ming'] = env.get('ben_ming_zhi', '')        # 兼容 ben_ming_zhi
        out['si_ke'] = env.get('sike') or []                 # 四课（第70法）
        out['si_ke_shang'] = _extract_sike_shang(env.get('sike'))
        out['yue_jiang'] = env.get('yuejiang', '')           # 兼容 yuejiang
        out['tai_sui'] = env.get('nian_zhi', '')
        out['ding_shen'] = get_ding_shen(gz) if gz else ''
        xs = get_xun_shou(gz) if gz else ''
        xw = get_xun_wei(gz) if gz else ''
        out['xun_shou_zhi'] = xs[1] if xs and len(xs) > 1 else ''
        out['xun_wei_zhi'] = xw[1] if xw and len(xw) > 1 else ''
        out['fen_xun_kong'] = get_fen_xun_kong(gz) if gz else None
        out['trend'] = _get_sanchuan_trend(env.get('sanchuan') or [])
        out['de'] = ''                                       # 日德未实现，保持空
    except Exception:
        return out
    return out


def build_judge_env(ri_gan, ri_zhi, nian_zhi, yue_zhi, yuejiang,
                    sike, sanchuan, keti, tian_jiang, tiandi_pan,
                    shichen, zhanlei='其他',
                    ben_ming_zhi='', ben_ming_age='', ben_ming_sex='男',
                    fu_xing_nian_zhi='', qi_xing_nian_zhi='',
                    y=0, m=0, d=0, sanchuan_tianjiang=None, nianming='') -> dict:
    """构造统一课式 env（含预处理：旬空/农历月日节气/季节/行年/昼夜/干支上神）。
    nianming: 夫妻年命（'夫年干支,妻年干支'，如 '甲寅,己亥'），供繁昌课判定（缺省空）。"""
    ganzhi = ri_gan + ri_zhi
    sc3l = list(sanchuan) if sanchuan else ['', '', '']
    gs = sike[0][1] if sike and len(sike) >= 1 else ''
    zs = sike[2][1] if sike and len(sike) >= 3 else ''

    # 旬空
    kw_a, kw_b = '', ''
    try:
        from engine.bifa_detector import get_xun_kong as _gxk
        kw_a, kw_b = _gxk(ganzhi)
    except Exception:
        pass

    # 农历月/日 + 节气（2026-08-21 修复：y=0 无效日期不得调 sxtwl.fromSolar(0,0,0)，
    # 否则产生错乱农历月（如 11 月→冬），导致 qike 手工起课（无日期）毕法季节错判）
    lm = ld = 0
    jieqi = ''
    if y > 0 and m > 0 and d > 0:
        try:
            import sxtwl as _sx
            _lunar = _sx.fromSolar(y, m, d)
            lm = _lunar.getLunarMonth()
            ld = _lunar.getLunarDay()
            if _lunar.hasJieQi():
                jieqi = _lunar.getJieQi()
        except Exception:
            pass

    season = _season_by_lunar_month(lm)
    is_day = shichen in ('卯', '辰', '巳', '午', '未', '申')

    # 行年（本命 + 虚岁 + 性别）
    xing_nian = ''
    if ben_ming_zhi:
        try:
            from engine.liuren_keti_bifa import _xing_nian_zhi as _xnz
            _age = int(str(ben_ming_age).strip()) if str(ben_ming_age).strip().isdigit() else 0
            xing_nian = _xnz(ben_ming_zhi, _age, ben_ming_sex) or ''
        except Exception:
            xing_nian = ''

    _env = {
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'ganzhi': ganzhi,
        'sike': sike, 'sanchuan': sc3l,
        'sanchuan_tianjiang': sanchuan_tianjiang or [],
        'chu': sc3l[0], 'zhong': sc3l[1], 'mo': sc3l[2],
        'gan_shang': gs, 'zhi_shang': zs,
        'tian_jiang': tian_jiang, 'tiandi_pan': tiandi_pan,
        'yuejiang': yuejiang, 'yue_zhi': yue_zhi, 'nian_zhi': nian_zhi,
        'kongwang': (kw_a, kw_b), 'keti': keti,
        'season': season, 'is_day': is_day,
        'lunar_month': lm, 'lunar_day': ld, 'jieqi': jieqi,
        'ben_ming_zhi': ben_ming_zhi, 'xing_nian': xing_nian,
        'fu_xing_nian_zhi': fu_xing_nian_zhi, 'qi_xing_nian_zhi': qi_xing_nian_zhi,
        'zhanlei': zhanlei, 'shichen': shichen,
        # 【BUG-FIX 2026-09-01】繁昌课需夫妻年命，原 env 无 nianming → 主链路繁昌永不触发
        'nianming': nianming,
    }
    # 【BUG-FIX 2026-09-21】补毕法赋谓词需要的派生键（原 30 键 ⇒ 47 谓词静默失效）
    _env.update(_derive_bifa_ext_keys(_env))
    return _env


# ── 适配层：统一 env → 各引擎参数 ──

def _judge_64keti(env: dict) -> Any:
    from engine.liuren_64ke_judge import judge_64_keti
    _tj3l = env.get('sanchuan_tianjiang') or []
    keti_env = {
        'ri_gan': env['ri_gan'], 'ri_zhi': env['ri_zhi'],
        'sike': env['sike'], 'sanchuan': env['sanchuan'],
        'chu': env['chu'], 'zhong': env['zhong'], 'mo': env['mo'],
        'yue_jiang': env['yuejiang'], 'yue_jian': env['yue_zhi'],
        'nian_zhi': env['nian_zhi'],
        'chu_tianjiang': _tj3l[0] if _tj3l else '',
        'tian_jiang': env['tian_jiang'],
        'tdp': env['tiandi_pan'],
        'kong_wang': [x for x in env['kongwang'] if x],
        'lunar_month': env['lunar_month'], 'lunar_day': env['lunar_day'],
        'jieqi': env['jieqi'],
        # 【BUG-FIX 2026-09-01】天网课需占时 shichen，原适配层未传 → 天网永不触发
        'shichen': env.get('shichen', ''),
        # 【BUG-FIX 2026-09-01】繁昌课需夫妻年命 nianming，原适配层未传 → 繁昌永不触发
        'nianming': env.get('nianming', ''),
    }
    return judge_64_keti(keti_env)


def _judge_bifa(env: dict) -> Any:
    from engine.bifa_judge import judge_bifa
    return judge_bifa(
        sanchuan_dizhi=env['sanchuan'],
        ri_gan=env['ri_gan'], ri_zhi=env['ri_zhi'],
        ganzhi=env['ganzhi'],
        yuejiang=env['yuejiang'],
        # 【BUG-FIX 2026-08-18】原传 season='' 让毕法内部用月将兜底算季节，
        # 而 YUEJIANG_SEASON 曾误用月建表→季节错位；env 已按农历月算好 season，
        # 直接透传，口径与其余引擎一致。
        season=env.get('season', ''),
        gan_shang_shen=env['gan_shang'],
        zhi_shang_shen=env['zhi_shang'],
        si_ke_info=env['sike'],
        tian_jiang=env['tian_jiang'],
        tiandi_pan=env['tiandi_pan'],
        keti=env['keti'],
        tai_sui=env['nian_zhi'],
        ben_ming_zhi=env['ben_ming_zhi'],
        shichen=env['shichen'],
    )


def _judge_special(env: dict) -> Any:
    from engine.special_kege import SpecialKegeDetector
    return SpecialKegeDetector().detect(
        sanchuan_dizhi=env['sanchuan'],
        ri_gan=env['ri_gan'],
        ganzhi=env['ganzhi'],
        tiandi_pan=env['tiandi_pan'],
        tian_jiang=env['tian_jiang'],
        gan_shang_shen=env['gan_shang'],
        zhi_shang_shen=env['zhi_shang'],
        yuejiang=env['yuejiang'],
        kongwang=env['kongwang'],
        season=env['season'],
        ben_ming_zhi=env['ben_ming_zhi'],
        xing_nian=env['xing_nian'],
    )


def _judge_bianjie(env: dict) -> Any:
    from engine.kege_bianjie_engine import detect_bianjie
    return detect_bianjie(
        ri_gan=env['ri_gan'], ri_zhi=env['ri_zhi'], sanchuan=env['sanchuan'],
        gan_shang=env['gan_shang'], zhi_shang=env['zhi_shang'],
        tian_jiang=env['tian_jiang'], tiandi_pan=env['tiandi_pan'],
        kongwang=env['kongwang'], keti=env['keti'],
        yuejiang=env['yuejiang'], season=env['season'], is_day=env['is_day'],
        tai_sui=env['nian_zhi'], ben_ming_zhi=env['ben_ming_zhi'],
        lunar_month=env['lunar_month'],
        zhanlei=env['zhanlei'],
        si_ke=env['sike'],
        fu_xing_nian_zhi=env['fu_xing_nian_zhi'],
        qi_xing_nian_zhi=env['qi_xing_nian_zhi'],
    )


def _judge_shensha_xiang(env: dict) -> dict:
    """神煞象意层（2026-09-22 新增；🔴 **零评分影响**，只出象不进分）

    背景：疾病13·169（戊午日亥将戌时）实证——天鬼／死神／死气／病符的值引擎**全部算对**，
    却一个都没进判定输出 ⇒ 只剩「凶」字，没有「疫气入宅／死气死神入宅」的象。
    原文依据：《通解》p505 死神（正月起巳顺行）／死气（正月起午顺行）、
    p525 伏殃即天鬼（正月起酉逆行四仲）／病符（旧太岁）／丧门（岁前二辰）／吊客（岁后二辰）。
    产出：各煞在课传**六处**（三传＋干上＋支上）的落点，供叙事层取象。
    """
    empty = {'落点': [], '说明': [], '煞值': {}}
    try:
        from engine.kege_shensha import (fu_yang, si_shen, si_qi, bing_fu,
                                         sang_men, diao_ke)
    except Exception as e:
        empty['error'] = str(e)
        return empty
    yz = env.get('yue_zhi', '') or ''
    nz = env.get('nian_zhi', '') or ''
    if not yz and not nz:
        return empty
    sc = list(env.get('sanchuan') or [])
    positions = [('初传', sc[0] if len(sc) > 0 else ''),
                 ('中传', sc[1] if len(sc) > 1 else ''),
                 ('末传', sc[2] if len(sc) > 2 else ''),
                 ('干上', env.get('gan_shang', '')),
                 ('支上', env.get('zhi_shang', ''))]
    sha = {}
    if yz:
        sha['天鬼'] = fu_yang(yz)     # 伏殃＝天鬼煞
        sha['死神'] = si_shen(yz)
        sha['死气'] = si_qi(yz)
    if nz:
        sha['病符'] = bing_fu(nz)     # 旧太岁
        sha['丧门'] = sang_men(nz)
        sha['吊客'] = diao_ke(nz)
    luo, biao = [], {}
    for name, zhi in sha.items():
        if not zhi:
            continue
        biao[name] = zhi
        hit = [p for p, v in positions if v and v == zhi]
        if hit:
            luo.append({'煞': name, '支': zhi, '位置': hit})
    out = {'落点': luo,
           '说明': ['%s%s在%s' % (x['煞'], x['支'], '、'.join(x['位置'])) for x in luo],
           '煞值': biao}
    return out


# ── 调度层：判断引擎注册表（轻量插件）──
_JUDGERS = [
    ('keti_judged', _judge_64keti),
    ('bifa_judged', _judge_bifa),
    ('special_kege', _judge_special),
    ('bianjie_kege', _judge_bianjie),
    # 🆕 2026-09-22：神煞象意层（天鬼/死神/死气/病符/丧吊落点）🔴 零评分影响
    ('shensha_xiang', _judge_shensha_xiang),
]
# ⛔ 若需临时摘除该层：把上行注释掉即可（下游无硬依赖）

# 各引擎出错时的兜底返回
_FALLBACK = {
    'keti_judged': [],
    'bifa_judged': {'匹配法句': [], '断法': []},
    'special_kege': {'匹配课格': [], '课格详情': {}},
    'bianjie_kege': {'匹配变格': [], '变格详情': {}},
    'shensha_xiang': {'落点': [], '说明': [], '煞值': {}},
    'guishen_xiang': {'象域': False, '强度': 0, '候选': [], '建议语': '', '依据': []},
    'rangjie': {'宜禳': False, '提示': [], '禳法': [], '有救': False,
                '有救理由': [], '依据': []},
}


def judge_all(env: dict) -> dict:
    """统一编排判断层 4 个引擎，返回聚合结果；单引擎异常不影响其他。"""
    result = {}
    for key, fn in _JUDGERS:
        try:
            res = fn(env)
            result[key] = res
            # 【BUG-FIX 2026-09-01】64课格判定出的课体，回填 env['keti']，
            # 否则后续引擎（变格 shi_keti 等依赖 keti 的规则）读到的仍是入参原始值 →
            # 大量「×本课」类变格规则在真实 judge_all 链路静默永不触发。
            if key == 'keti_judged' and isinstance(res, list):
                names = [h.get('课体') for h in res if isinstance(h, dict) and h.get('课体')]
                if names:
                    env['keti'] = '、'.join(names)
        except Exception as e:
            fb = dict(_FALLBACK[key]) if isinstance(_FALLBACK[key], dict) else _FALLBACK[key]
            if isinstance(fb, dict):
                fb['error'] = str(e)
            result[key] = fb
    # ── 主格裁定层（依赖上述各层结果，故置于最后）──
    # 🆕 2026-09-22：课格并列时按原文明文裁定主格（🔴 零评分影响，只出裁定）
    #    依据：中L3460「以用为主」／中L3462「吉将乘囚休气不为吉」／上L2568「克日为凶虽吉将亦为凶」
    #    ／上L2637「空亡减半」／下L3544「吉不为吉」／上L6960 三光失明。
    try:
        from engine.keti_arbitration import arbitrate
        result['zhuge'] = arbitrate(env, result)
    except Exception as e:
        result['zhuge'] = {'主格': '', '主格性质': '平', '吉格': [], '凶格': [],
                           '降等': [], '理由': [], '数目': {}, '倾向': '平',
                           'error': str(e)}
    # ── 鬼神／祠庙取象层（依赖 shensha_xiang，故置于其后）──
    # 🆕 2026-09-22：🔴 零评分影响；只给「象域＋方位＋神格＋远近」，⛔ 不落专名
    #    依据：下L9631 未主祭祀神鬼／下L1182 未临宅＝鬼神／下L9598 子主祷祝鬼神
    #    ／下L4556 寅申为寺观／下L10788 龙居辰主寺观、申与僧同音／下L9643 戌主塑画／上L865 方位
    try:
        from engine.guishen_xiang_engine import suggest as _gsx
        result['guishen_xiang'] = _gsx(env, result)
    except Exception as e:
        result['guishen_xiang'] = {'象域': False, '强度': 0, '候选': [],
                                   '建议语': '', '依据': [], 'error': str(e)}
    # ── 禳解／趋避提示层（依赖 shensha_xiang / keti_judged，故置于主格裁定之后）──
    # 🆕 2026-09-22：🔴 零评分影响，只出提示不进分；输出一律带原文出处
    #    依据：中L2201 伏殃「惟宜禳祷以除之」／中L1841 三阴「宜禳之」＋有救判据
    #    ／中L2305 墓门开「迁葬／合寿木以禳之」／中L2450 励德「谢土神」／中L9371 刘日新移厕远井
    try:
        from engine.rangjie_engine import suggest as _rangjie
        result['rangjie'] = _rangjie(env, result)
    except Exception as e:
        result['rangjie'] = {'宜禳': False, '提示': [], '禳法': [], '有救': False,
                             '有救理由': [], '依据': [], 'error': str(e)}
    return result
