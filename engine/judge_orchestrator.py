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

    ⚠️ 本批**不补**的一类（避免臆造定义）：
      · `de`（日德）—— bifa_detector 里注释「如需可扩展」，实体未实现 ⇒ 保持 `''`。
        （⏳ 2026-09-28 复核：**起例其实在案** —— 起例表 L3000「日德 寅 申 巳 亥 巳 寅 申 巳 亥 巳」
         当为甲乙丙丁戊己庚辛壬癸 → 寅申巳亥巳寅申巳亥巳。
         🔴 **2026-09-30 勘误**：此处原写「与 `kege_shensha.GAN_DE` 同名常量**已存在且一致**」
         —— **该判断有误**（漏看「己」干：彼处作「亥」、原文应「寅」）。已修 `kege_shensha.GAN_DE`
         等 3 处实现（见 `docs/reports/_表级双真源普查报告.md`），现 5 处实现全部与原文一致。
         但**规则中仍零引用** ⇒ 暂不接线，待有消费方时启用。）
      · ~~`shensha`／`si_qi` 无真源~~ —— **2026-09-28 已证伪并接线**（真源＝`kege_shensha` 全部
        起例纯函数；`shensha{地支:{煞名}}` 反向表 ＋ `si_qi` 单值），相关 4 谓词已复活。
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
        # 🆕 2026-09-28 憨爷「按你的建议操作」：**接线 `shensha` / `si_qi` 两个键**
        #   🔴🔴🔴 **2026-09-28 三度复核·重大更正（务必先读）**：
        #     **本函数产出的 `shensha`／`si_qi`／`de` 等键，在当前生产链路中「无任何消费方」。**
        #     实证：`kege_atoms.eval_atom` 的**唯一生产调用方**是
        #       `kege_bianjie_engine.match_all`（L43 逐条 eval、L271 由 `detect_bianjie` 调度）；
        #     而 `detect_bianjie` **内部自建 env**（`build_env`，L268）⇒ 用的是它**自己**的 shensha，
        #     **根本不读** `build_judge_env` → `_derive_bifa_ext_keys` 产出的这一份。
        #     另：`_judge_bifa` 走 `judge_bifa(**逐参数)`（L243 起），毕法赋引擎亦不读 `shensha`。
        #     ⇒ 本段接线目前是**惰性的**（无副作用，亦无收益）——**不是 bug，但也不是「已生效」**。
        #   ✅ **真正服务变格规则的那一份 shensha，早已在 `kege_bianjie_engine.build_env` 内实现**
        #     （生气/死气/血支/血忌/飞廉/破碎/羊刃/天医/天鬼/丧门/吊客/丁神…经实测 **规则所需
        #      13 个煞名 13/13 全覆盖**，与 `kege_shensha` 起例**逐煞一致**，见
        #      `_冗余待删/_probe_shensha_crossline_0928.py`：72 课×12 煞 = 864 项 **0 不一致**）。
        #   📌 **去留裁定**：本段**保留**（口径已校正、与变格层等价），作为「若将来把
        #     `build_judge_env` 的 env 作为**唯一真源**下传（如让 `detect_bianjie` 接受外部 env）
        #     时的现成基础」；⛔ 但**不得**再宣称「4 个谓词已复活」——那是**误判**（谓词读的是
        #     变格层自建 env，本段接不接线都不影响其取值）。
        #   🔴 **教训（第 8 坑）**：查「假接线」不能只查「出口有没有赋值」，还须**反向追消费方**
        #     ——「谁读这个键」；赋了而无人读 ⇔ 另一种假接线。
        #   ── 以下为原始接线说明（口径已校正，保留备查）──
        #   🔴 血泪根因（旧注释所记「没有真源」**已过期**）：`kege_atoms` 的 4 个读点
        #      （`_sc_has_sha` L345／`_de_shen_wei_gui` L520／`_x_shi_shensha` L608／
        #       `_sang_diao_quan_feng` L1724）读 `env['shensha']`。
        #   ✅ 真源本就都在 —— `kege_shensha` 的起例纯函数 ＋ `bifa_detector.get_ding_shen`。
        #      ⛔ 不在本函数另立标准，一律转发调用。
        #   ⚠️ **只接线有真源的煞**。2026-09-28 二次复核：原注「其余 7 煞无起例」**已证伪**
        #      —— 回《通解》上「神煞起例表」L2937–L3040 复扫，**7 煞起例全部在案**
        #      （血支 L2943／血忌 L2945／羊刃 L3022／破碎 L926／孤辰·寡宿 L4019／天医 L2868）。
        #      ⇒ 现已全部接入（⛔ 教训：凡见「起例未取证」**必先回原文表复扫**，结论会过期）。
        #   🔴🔴 **口径铁律：神煞起例一律按月建（`env['yue_zhi']`），⛔ 绝不用月将（`yuejiang`）**。
        #      月建＝节气月地支（正月建寅，L2821 表头），月将＝太阳所躔（雨水后亥），**两者不同**。
        #      本函数初版误传 `yuejiang`（口径错位，全盘偏 1~2 位）⇒ 已改 `yue_zhi`；
        #      仅当 `yue_zhi` 缺失（`/api/qike` 手工起课无日期）才退用 `yuejiang` 兜底。
        #   🔴 「生气」≠「死神」：生气正月起**子**（L2827），死神正月起**巳**（L2941）——
        #      初版竟把 `si_shen`(死神) 当成生气接进去（**实证 bug**，51 条规则受影响），已改回 `sheng_qi`。
        _yj = env.get('yue_zhi', '') or env.get('yuejiang', '') or ''   # 月建优先，兜底月将
        _nz = env.get('nian_zhi', '') or ''
        try:
            from engine.kege_shensha import (si_qi as _k_si_qi, sang_men as _k_sang_men,
                                             diao_ke as _k_diao_ke, fu_yang as _k_fu_yang,
                                             tian_mu as _k_tian_mu, yue_yan as _k_yue_yan,
                                             fei_lian as _k_fei_lian, tian_guai as _k_tian_guai,
                                             you_hun as _k_you_hun, sheng_qi as _k_sheng_qi,
                                             bing_fu as _k_bing_fu, sang_che as _k_sang_che,
                                             yuan_shen as _k_yuan_shen,
                                             # 2026-09-28 补 7 煞（起例已回原文表取证）
                                             xue_zhi as _k_xue_zhi, xue_ji as _k_xue_ji,
                                             yang_ren as _k_yang_ren, po_sui as _k_po_sui,
                                             gu_chen as _k_gu_chen, gua_su as _k_gua_su,
                                             tian_yi as _k_tian_yi,
                                             # 2026-10-21 补「三丘」：原为孤儿函数（起例有据、无人调用）
                                             #   《壬學瑣記》辛未日占病「未是三邱」实证 ⇒ 辛日三丘＝未，
                                             #   与 `san_qiu('辛')` 一致。⛔ 谓词层零使用 ⇒ 不影响评分。
                                             #   ⓘ 字形统一用引擎口径「三丘」（憨爷 2026-10-21 定）。
                                             san_qiu as _k_san_qiu)
            _ss = {}
            # 值＝该煞所落之**地支**；反向建表 {地支: {煞名, ...}}
            _pairs = []
            if _yj:
                _pairs += [('天目', _k_tian_mu(_yj)), ('月厌', _k_yue_yan(_yj)),
                           ('飞廉', _k_fei_lian(_yj)), ('天怪', _k_tian_guai(_yj)),
                           ('飞魂', _k_you_hun(_yj)), ('死气', _k_si_qi(_yj)),
                           ('生气', _k_sheng_qi(_yj)), ('天鬼', _k_fu_yang(_yj)),  # 伏殃＝天鬼
                           ('丧车', _k_sang_che(_yj)), ('愿神', _k_yuan_shen(_yj)),
                           ('血支', _k_xue_zhi(_yj)), ('血忌', _k_xue_ji(_yj)),
                           ('天医', _k_tian_yi(_yj)), ('孤辰', _k_gu_chen(_yj)),
                           ('寡宿', _k_gua_su(_yj))]
            if _nz:
                _pairs += [('丧门', _k_sang_men(_nz)), ('吊客', _k_diao_ke(_nz)),
                           ('病符', _k_bing_fu(_nz))]
            # 破碎：原文 L926「子午卯酉在巳，寅申巳亥在酉，辰戌丑未在丑，**可论年、月、日**」
            #   ⇒ 三处皆可起例，但同一煞名落点不同会互相污染（年/月支推的破碎点被误当
            #     日支破碎点）⇒ **本引擎统一取「日支」单一口径**，与 `kege_bianjie_engine.build_env`
            #     （`ssc.get_zhi_sha(ri_zhi)` 亦只取日支）**保持全系统一致**，避免同煞两值。
            #   ⚠️ 若将来确需年/月口径（如择日按年支论破碎），另立键，⛔ 勿混入本煞名。
            if rz:
                _pairs.append(('破碎', _k_po_sui(rz)))
            # 羊刃按日干（L3022）
            if rg:
                _pairs.append(('羊刃', _k_yang_ren(rg)))
                # 三丘按日干＝五墓之对冲位（kege_shensha.san_qiu，起例有据 p525）
                #   《壬學瑣記》辛未日占病「未是三邱」⇔ san_qiu('辛')='未' 实证一致
                _pairs.append(('三丘', _k_san_qiu(rg)))
            _ds = get_ding_shen(gz) if gz else ''
            if _ds:
                _pairs.append(('丁神', _ds))
            for _sha_nm, _sha_z in _pairs:
                if _sha_z:
                    _ss.setdefault(_sha_z, set()).add(_sha_nm)
            out['shensha'] = _ss
            out['si_qi'] = _k_si_qi(_yj) if _yj else ''
        except Exception:
            out['shensha'] = {}
            out['si_qi'] = ''
    except Exception:
        return out
    return out


def _judge_is_day(shichen: str, y=0, m=0, d=0) -> bool:
    """昼夜判定：**有日期则按太阳出入（真太阳时）**，无日期才退化固定时辰分界。

    🔴 憨爷 2026-10-22 指正：「以前我就是让你以**太阳出入**定昼夜的啊」
      ⇒ 真源 `engine/gui_ren_daynight.py` 早已写好（赤纬＋均时差＋经度差，安龙 25.1N/105.5E），
        但主链路一直用固定「卯-申为昼」⇒ 本函数即**接线点**。
    ⚠ 无 y/m/d（或非法日期）时退化为固定分界，保持旧行为，⛔ 不抛错。
    ⓘ 用**时辰起点**（酉=17:00）判定，与 `gui_ren_daynight.SHI_CHEN_HOUR` 一致；
       ∴ 夏季酉时多为昼、冬季酉时跨昼夜 —— 正是本项目要区分的那一段。
    """
    sc = str(shichen or '')
    if sc:
        try:
            _y, _m, _d = int(y or 0), int(m or 0), int(d or 0)
            if _y > 0 and 1 <= _m <= 12 and 1 <= _d <= 31:
                from datetime import date as _date
                from engine.gui_ren_daynight import is_daytime as _idt
                return bool(_idt(sc, 0, 25.1, 105.5, _date(_y, _m, _d)))
        except Exception:
            pass
    return sc in ('卯', '辰', '巳', '午', '未', '申')


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
    # 🔴 2026-10-22 憨爷指正：「以前我就是让你以**太阳出入**定昼夜的啊」
    #   `engine/gui_ren_daynight.py` 早已实现（真太阳时＋赤纬＋均时差，安龙 25.1N/105.5E），
    #   但主链路一直用固定「卯-申为昼」⇒ **模块写了没接线**。此处即接线点。
    #   ⚠ 无 y/m/d 时退化为固定分界（保持旧行为，⛔ 不报错）。
    is_day = _judge_is_day(shichen, y, m, d)

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
        # 🔴 2026-10-22：透传昼夜（按**太阳出入**判定，见 `_judge_is_day`）
        is_day=env.get('is_day'),
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


# ── 神煞象义表（🔴 每条**必附原文出处**；⛔ 未取证的煞一律不出象义，宁缺勿造）──
#    2026-09-27 憨爷「神煞接入叙事层」时新增；键＝煞名，值＝(象, 出处)
_SHA_XIANG_YI = {
    '愿神': ('神佛香愿事・有愿未还',
             '《断案疏正》评疏 L12854「或谓二月愿神在亥」＋ L12853「所乘太阴神为神佛香愿事，'
             '临空作传，未曾还愿之故」；《心镜・疾病门・占何鬼祟》L13425「得青龙，贵人鬼，'
             '及司命、愿神」'),
    # ── 惊怪科「八妖」（《通解》上 L3126：天目・月厌・飞廉・天鬼・天怪・飞魂・直符・月宿）──
    '飞魂': ('夜多凶梦・鬼祟相侵・恍惚不宁',
             '《通解》中 L1811-1812《订讹》「飞魂：令人魂有飞扬千里之象…占主夜多凶梦，'
             '鬼祟相侵，恍惚不宁」；起例 L1791「顺行正月起登明」；'
             '用法 L1794《袖中金》「若于日辰行年上见者，壅滞魂魄之往来…健者忧衰，病者忧死」'),
    '月厌': ('家中怪异・鬼来哭声・血光',
             '《通解》上 L3126 八妖「如占宅有一煞入占，便主家有怪异」；'
             'L4905「月厌天罡六甲辰，若加卯上鬼来寻。屋头屋尾哭声频」；'
             'L3790「月忌、血支、月厌等临日支主家里有血光灾害」；起例 L2957（正月起戌逆行）'),
    '天目': ('鬼祟为祸（克干上者便是祟）',
             '《通解》上 L4877「每日两个天目鬼，四时居重辰上二。重克干上便是祟」；'
             'L5003「天目鬼来相步行…看其等处作灾」；起例 L4814「天目春辰、夏未、秋戍、冬丑」；'
             '八妖 L3126'),
    # 🆕 2026-09-27 第三步：八妖补齐（飞廉／天怪／直符）—— 起例真源见 `kege_shensha` 各 docstring
    '飞廉': ('怪异（八妖）｜迅速之神（行人立至）—— 两义项并存',
             '《通解》上 L3126 八妖「如占宅有一煞入占，便主家有怪异」；'
             '起例 L2959（八月＝亥；双证 下 L5051「按：六月飞廉在卯，不在辰」与表内六月卯吻合）｜'
             '另一义项：上 L3647「飞廉也为迅速之神」、L4438「飞廉加干发用，主行人立至」'),
    '天怪': ('家中怪异（八妖）',
             '《通解》上 L3126 八妖；起例 L2963「正月起丑逆行」⇒ 八月＝午。'
             '⚠ 上 L1402「登明…亦名天怪」为**亥神别名**，同名异指，勿混'),
    '直符': ('占病凶・出行不归（八妖·怪异）｜逃亡向之吉',
             '《通解》上 L3126 八妖；L3026「直符…即飞符，占病凶，出行不归，逃亡向之吉」；'
             '起例按**日干**（甲巳…癸戌，不用亥子），上 L3026 ＋ 下 L11623 双证；'
             '另一义项：上 L4701「天目直符逃者佳」'),
    # 🆕 2026-09-27 第四步①：八妖**收官** —— 月宿（太阴躔度）⇒ 覆盖 8/8
    '月宿': ('太阴躔宿所临之宫（八妖）｜占宅有怪异',
             '《通解》上 L3126 八妖「如占宅有一煞入占，便主家有怪异」；'
             '起例 中 L1246「月宿者，太阴星躔度宫神也。正月初一起室…遇奎张井翼氐斗宿，重算留一」'
             '（「起月宿法」另见 中 L1311）；宿→辰映射 中 L1319-1320「月宿所属十二辰」；'
             '⚠ 原文自注「更详《七政历》细度为准」⇒ 本层所呈为**平推近似值**，非实际躔度'),
    # 🆕 2026-09-27 第四步②：**天将类**神煞 —— ⛔ 非起例所得，其「值」＝该处所乘之支
    #   🔴 憨爷点出：**占惊怪／疾病时**须留意 —— 青龙＝纸钱煞、太常＝孝服煞。
    #   ⚠️ 二者**本为吉将**（十二将之中吉），⛔ 不得据常态判凶；且本层零评分，只供叙事取象。
    '青龙': ('纸钱煞（占病・占怪・宅占时方以此论）｜⚠ 常态为吉将，不作凶论',
             '《通解》中 L1229「**青龙为纸钱煞，加末传**」（同案 案验 L1233「寅应青龙」）；'
             '上 L5945「问：青龙为纸钱煞，占病固凶」；'
             '中 L3184「青龙为长者…又为**孝服纸钱煞**，下季定有孝服」；'
             '下 L1773「宅乘青龙太常谓之孝服纸钱杀也」'),
    '太常': ('孝服煞（占病・占怪・宅占）｜加干＝外孝服・加支＝内孝服・加末传＝归计门｜⚠ 常态为吉将',
             '《通解》中 L1229「**太常乘死气为孝服煞，加日干**」；中 L3348「太常为孝服煞」；'
             '上 L1113「太常孝服神，带丧吊，主亲服」；'
             '上 L4147「鬼作死气乘太常**加干，主有外孝服**……乘常**加支，主有内孝服**」；'
             '下 L4667「丧吊全入三传而**末为归计门作太常为孝服**也」；'
             '下 L1773「宅乘青龙太常谓之孝服纸钱杀也」；旁证 下 L3164「破碎作太常，乘鬼入宅，又主孝服」'),
    # 🆕 2026-09-28 憨爷「按你的建议操作」：**收魂煞**（占病专论·同属天将类机制）
    #   ⛔ 与八妖不同科：八妖是「起例所得之煞」，此煞是「**墓神**为玄武即是」的**组合判据**。
    #   🔴 唯一带**日干限定**的煞 —— 原文自注「**惟六戊一千有之**」。
    '收魂煞': ('占病大凶（魂魄入墓被锁，医药难施）｜限**六戊日**',
               '《通解》上 L3122「收魂煞：凡**墓神为玄武**即是。占病主凶」；'
               '注文 上 L4159「所谓**玄乘日墓名收魂煞**。惟**六戊**一千有之，'
               '如**戊申日昴星，三传戌酉午**，昼夜占，**武乘日墓发用**是也」。'
               '🔴 戊墓取「**戌**」之实证：原文案例初传＝戌，与「武乘日墓**发用**」吻合 ⇒ '
               '戊墓＝戌（火土同宫），⛔ 非 `WX_MU["土"]="辰"` 的水土同宫口径（该口径用于夹墓类）。'
               '旁证：`duanan_knowledge_base` L1128/L1217「最怕收魂煞日之墓神乘元武」；'
               '上 L4158 断句「**引鬼为生忌收魂**」（毕法赋句）'),
}


def _judge_shensha_xiang(env: dict) -> dict:
    """神煞象意层（2026-09-22 新增；🔴 **零评分影响**，只出象不进分）

    背景：疾病13·169（戊午日亥将戌时）实证——天鬼／死神／死气／病符的值引擎**全部算对**，
    却一个都没进判定输出 ⇒ 只剩「凶」字，没有「疫气入宅／死气死神入宅」的象。
    原文依据：《通解》p505 死神（正月起巳顺行）／死气（正月起午顺行）、
    p525 伏殃即天鬼（正月起酉逆行四仲）／病符（旧太岁）／丧门（岁前二辰）／吊客（岁后二辰）。

    🆕 2026-09-27 憨爷「神煞接入叙事层」＋「惊怪之事应重神煞」：
      · 补入 **愿神**（＝与地医同宫，正月起戌顺行十二辰）。四重互证见
        `engine/kege_shensha.yuan_shen` docstring（《断案疏正》L12854／《神煞赋》／
        五书合编「正戌顺12：地医、愿神、天书」／《六壬大全》卷一逐月神煞二月亥位见「天书」）。
      · 新增 `象义` 键（🔴 **只增不改**，旧消费方无感）：仅对**已取证**的煞给象 ＋ 出处。
      ⛔ 天鬼／丧门／吊客／死气／死神／病符 已在层内（本次不动其口径）。

    🆕 2026-09-27 第三步（八妖 **4/8 → 7/8**）：补入 **飞廉・天怪・直符**。
      起因：复看 2026-09-26 实占课（癸卯日辰将午时）——按八妖全谱，七处惊怪由 1 条增至 3 条
      （+ 飞廉在**中传・干上**、+ 天怪在**先锋门**）。
      🔴 原记「飞廉/天怪/直符 起例未取证」经复核实为**误记**：三条起例**都在**《通解》上
        「神煞起例表」内（飞廉 L2959 ／ 天怪 L2963 ／ 直符 L3026 ＋ 下 L11623），详见 `kege_shensha` docstring。
      🔴 义项按铁律「穷举、OR 并存」：飞廉 兼「迅速之神」；直符 兼「逃亡向之吉」；天怪 另有
        L1402「登明亦名天怪」之**同名异指**（亥神别名），⛔ 不得据此判「象义未定」。
      ⛔ 月宿**仍不接**（起例＝太阴躔度／二十八宿，中 L1246／L1310-1319，成本高，另案拍板）。

    🆕 2026-09-27 第四步（憨爷「接入月宿…还有占测惊怪、疾病时，注意天将青龙为纸钱煞、
      太常为孝服」）—— 两件事一并落地：
      ① **八妖收官 7/8 → 8/8**：补入 **月宿**（太阴躔度）。
         🔴 **不另写算法**：直接复用引擎既有单一真源 `liuren_64ke_judge.yue_su`
           （天寇课／二烦课同用此源；`kege_shensha.yue_su` 为薄封装转发），
           宿→辰映射复用 `XIU_ZHI`（中 L1319-1320）。
         🔴 起例三处分歧已在 `kege_shensha.yue_su` docstring 定向（十月「尾 v.s. 心」→ 从 **尾**；
           L1309 举例脱「娄」字 → 按完整二十八宿推）；⛔ 不得据分歧判「起例未取证」。
         ⚠️ 本煞**依赖 env 的 `lunar_month`/`lunar_day`** —— 回测/分析链路若未传农历，
           该煞静默缺席（⛔ 不猜、不退化，免得以错日期反推错宫）。
      ② **天将类神煞**（⛔ 与上表机制不同）：青龙＝**纸钱煞**、太常＝**孝服煞**。
         · 值＝**该处所乘之支**（非起例所得）⇒ 不并入 `sha` 表，直接以「落点」条目追加
           （`煞`/`支`/`位置` 三键不变，另加可选键 `别称` ⇒ 旧消费方无感）。
         · 🔴 取用条件**严守原文明文**（⛔ 不无条件张榜，免生噪音）：
             青龙 → 乘**末传**（中 L1229「加末传」）或 乘**支上**（下 L1773「宅乘青龙」）；
             太常 → 乘**干上**（中 L1229／上 L4147「加干」＝**外孝服**）
                    或 乘**支上**（下 L1773／上 L4147「加支」＝**内孝服**）
                    或 乘**末传**（下 L4667「末为归计门作太常为孝服」）。
         · ⚠️ 青龙・太常**本为吉将** ⇒ `_SHA_XIANG_YI` 明注「占病／占怪／宅占方以此论」，
           且本层零评分，不进任何判吉凶链路。

    产出：各煞在课传**十处**的落点 ＋ 已取证煞的象义，供叙事层取象。

    🔴 2026-09-27 憨爷拍板「**补七处**」——取用点位对齐**古法八门**（《通解》上 L3365：
      「正时为先锋门，天上直时将为直事门，日为外事门，辰为内事门，初传发端门，
        中传移易门，末传归计门，以人的本命行年变体门」）
      ＝ **赵林声七处**（《课例北大》L56「行、命、行命上神，日上神，支上神，三传、先锋门」）。
      故本层取：三传 ＋ 干上 ＋ 支上 ＋ 本命 ＋ 行年 ＋ **本命上神** ＋ **行年上神** ＋ **先锋门**（正时）。
      ⛔ 「煞 ＝ 地盘支本身」这类无原文依据的口径**依旧不取**——「临 X」＝取 X 位置上的**天盘支**
        （「临日支」＝支上神，**非**「煞＝日支」；详见 SKILL `liuren-rule-onboarding` Q 类）。
      ⚠️ 本层**零评分**，扩位只增叙事可见度，不进任何评分/判吉凶链路。
    """
    empty = {'落点': [], '说明': [], '煞值': {}, '象义': []}
    try:
        from engine.kege_shensha import (fu_yang, si_shen, si_qi, bing_fu,
                                         sang_men, diao_ke, yuan_shen,
                                         you_hun, yue_yan, tian_mu,
                                         fei_lian, tian_guai, zhi_fu,
                                         yue_su_zhi, tian_jiang_pan,
                                         # 2026-10-21 接「三丘」（原为孤儿函数，起例有据无人调用）
                                         san_qiu)
    except Exception as e:
        empty['error'] = str(e)
        return empty
    yz = env.get('yue_zhi', '') or ''
    nz = env.get('nian_zhi', '') or ''
    rg = env.get('ri_gan', '') or ''      # 🆕 直符按**日干**起例（八妖，上 L3026）
    rz = env.get('ri_zhi', '') or ''      # 🆕 2026-10-22 跌扑煞按**日支**取驿马
    # 🆕 2026-09-27 第四步①：月宿 按**农历月日**起例（八妖，中 L1246）
    try:
        lm = int(env.get('lunar_month') or 0)
        ld = int(env.get('lunar_day') or 0)
    except Exception:
        lm = ld = 0
    if not yz and not nz and not rg and not (lm and ld):
        return empty
    sc = list(env.get('sanchuan') or [])
    # 🔴 天地盘两种形态都要吃（本层零评分，宁退化不可报错）：
    #    ① 平铺 {地盘支: 天盘支}          ← 回测/分析主链路（ancient_backtest L714/723/739 反证：变量本身即平铺）
    #    ② {地盘, 天盘, 月将, 占时, 天地对应:{地盘:天盘}}  ← daliuren_engine.arrange_tiandi_pan 的**结构体**形态
    tdp_raw = env.get('tiandi_pan') or {}
    if isinstance(tdp_raw, dict) and isinstance(tdp_raw.get('天地对应'), dict):
        tdp = tdp_raw['天地对应']
    elif isinstance(tdp_raw, dict):
        tdp = tdp_raw
    else:
        tdp = {}
    _bm = str(env.get('ben_ming_zhi') or '').strip()
    _xn = str(env.get('xing_nian') or '').strip()
    _zm = str(env.get('shichen') or '').strip()

    # 🔴 上神取值走**唯一真源** `leixiang_chain.yin_shen`（定义：阴神(X) = tiandi_pan[X]）。
    #    ⛔ 不复用同模块的 `qi_chu_map`：它读 `env['ben_ming']`，而 build_judge_env 产出的 env
    #       键名是 `ben_ming_zhi`（只有 stock_dashboard 自造 env 才带 `ben_ming`）
    #       ⇒ 直接复用会让「本命」锚点恒空（两套 env 约定不一致，此处显式规避）。
    try:
        from engine.leixiang_chain import yin_shen as _yin_shen
    except Exception:
        def _yin_shen(z, _tp):
            return str(_tp.get(z, '') or '') if (z and isinstance(_tp, dict)) else ''

    # 🔴 2026-09-27 憨爷「补七处」：取用点位 ＝ **古法八门**（《通解》上 L3365）
    #   ＝ **赵林声「七处」**（《北大课例》课例-10；与 `leixiang_chain.QI_CHU_NAMES` 同源同义）。
    #   本层刻意用**更细的位置名**（信息量更大，且既有 5 名一字不动 ⇒ 只增不改），映射关系：
    #     初/中/末传 → 七处「三传」｜干上 → 「日上神」｜支上 → 「支上神」
    #     本命 → 「本命」｜行年 → 「行年」｜本命上神＋行年上神 → 「行命上神」｜先锋门 → 「先锋门」
    #   🔴 「先锋门」取**占课正时本身**（如占课取午时 ⇒ 先锋门＝午）—— 憨爷 2026-09-27 拍板。
    #     依据：《通解》上 L3365「**正时为先锋门**」；赵林声《北大课例》L160「**先锋辰为鬼**」（取辰本身）。
    #     ⛔ **不取正时之上神**：月将加时 ⇒ 天地盘[正时] ≡ **月将**，
    #        取上神只会与月将重复、反而丢掉「正时」这条独立信息（闸口有恒等式断言固化）。
    positions = [('初传', sc[0] if len(sc) > 0 else ''),
                 ('中传', sc[1] if len(sc) > 1 else ''),
                 ('末传', sc[2] if len(sc) > 2 else ''),
                 ('干上', env.get('gan_shang', '')),
                 ('支上', env.get('zhi_shang', '')),
                 ('本命', _bm),
                 ('行年', _xn),
                 ('本命上神', _yin_shen(_bm, tdp)),
                 ('行年上神', _yin_shen(_xn, tdp)),
                 ('先锋门', _zm)]
    sha = {}
    if yz:
        sha['天鬼'] = fu_yang(yz)     # 伏殃＝天鬼煞
        sha['死神'] = si_shen(yz)
        sha['死气'] = si_qi(yz)
        sha['愿神'] = yuan_shen(yz)   # 🆕 与地医同宫（正月起戌顺行12）・主「神佛香愿・有愿未还」
        # 🆕 2026-09-27 第二步：惊怪科「八妖」（《通解》上 L3126）
        #    天鬼（上）＋ 以下三煞。
        sha['飞魂'] = you_hun(yz)     # 八妖・《订讹》L1811「夜多凶梦，鬼祟相侵，恍惚不宁」
        sha['月厌'] = yue_yan(yz)     # 八妖・L4905「鬼来寻…屋头屋尾哭声频」
        sha['天目'] = tian_mu(yz)     # 八妖・季煞 L4814；L4877「重克干上便是祟」
        # 🆕 2026-09-27 第三步（憨爷「按照你的建议操作」＝选项甲）：补齐八妖另三煞
        #    🔴 起例真源全在《通解》上「神煞起例表」内 —— 原记「起例未取证」**不成立**：
        #      飞廉 → L2959（双证 下 L5051「六月飞廉在卯」）；天怪 → L2963；直符 → L3026 ＋ 下 L11623（双证）。
        #    🔴 义项**并存**（⛔ 不二选一）：飞廉 兼「迅速之神」（L3647/L4438）；
        #      直符 兼「逃亡向之吉」（L3026/L4701）。
        #    ⛔ **只 OR 追加**，不动既有 7 煞任何口径；✅ 月宿 已接（2026-09-27 收官，
        #    薄封装转发 liuren_64ke_judge.yue_su，中 L1246/L1311/L1315/L1319-1320）⇒ 八妖 8/8。
        sha['飞廉'] = fei_lian(yz)
        sha['天怪'] = tian_guai(yz)
    # 🆕 2026-09-27 第四步①：八妖**收官** —— 月宿（太阴躔度）
    #   🔴 真源＝中 L1246「正月初一起室…遇奎张井翼氐斗宿，重算留一」；实现**复用**
    #      `liuren_64ke_judge.yue_su`（天寇/二烦同源，⛔ 不另立算法）；宿→辰 中 L1319-1320。
    #   ⚠️ 需农历月日；未传则本煞静默缺席（⛔ 不猜、不退化）。
    if lm and ld:
        sha['月宿'] = yue_su_zhi(lm, ld)
    if nz:
        sha['病符'] = bing_fu(nz)     # 旧太岁
        sha['丧门'] = sang_men(nz)
        sha['吊客'] = diao_ke(nz)
    if rg:
        sha['直符'] = zhi_fu(rg)      # 八妖・按日干（癸日→戌）；一名「飞符」，L3026／下 L11623 双证
        # 🆕 2026-10-21 接「三丘」：起例＝五墓之对冲位（`kege_shensha.san_qiu`，p525）。
        #   实证：《壬學瑣記》辛未日午将酉时占戌命人病「**未是三邱**」⇔ `san_qiu('辛')='未'` 一致。
        #   ⛔ 谓词层（bifa_detector）零使用 ⇒ 只进「煞值/落点」，**不影响评分**。
        #   ⓘ 字形统一用引擎口径「三丘」（憨爷 2026-10-21 定：统一用引擎的）。
        #   ⚠ 待办：本函数与 `build_judge_env` 各自算煞（多真源），后续应统一读 `env['shensha']`。
        sha['三丘'] = san_qiu(rg)
    luo, biao = [], {}
    for name, zhi in sha.items():
        if not zhi:
            continue
        biao[name] = zhi
        hit = [p for p, v in positions if v and v == zhi]
        if hit:
            luo.append({'煞': name, '支': zhi, '位置': hit})

    # 🆕 2026-09-27 第四步②：**天将类神煞**（青龙＝纸钱煞・太常＝孝服煞）
    #   ⛔ 与 `sha` 机制不同：其「值」是**该处所乘之支**（非起例所得）⇒ 不入 `sha`、不入 `煞值`，
    #      直接以「落点」条目追加 —— 三键 `煞/支/位置` 不变，另加**可选键 `别称`**（旧消费方无感）。
    #   取用条件**严守原文明文**（⛔ 不无条件张榜，免生噪音）：
    #     青龙＝纸钱煞：乘**末传**（中 L1229「青龙为纸钱煞，加末传」）
    #                   或乘**支上**（下 L1773「宅乘青龙太常谓之孝服纸钱杀也」）
    #     太常＝孝服煞：乘**干上**（中 L1229「加日干」／上 L4147「加干，主有**外**孝服」）
    #                   或乘**支上**（下 L1773／上 L4147「加支，主有**内**孝服」）
    #                   或乘**末传**（下 L4667「丧吊全入三传而**末为归计门作太常为孝服**也」）
    #   ⚠️ 天将盘走**单一真源** `kege_shensha.tian_jiang_pan`（8640 对证零差异），
    #      ⛔ 不猜 `env['tian_jiang']` 的形态（各链路给的是 dict/列表不一）。
    _TAI_CHANG_POS = {'干上': '孝服煞·外孝服', '支上': '孝服煞·内孝服',
                      '末传': '孝服煞·归计门'}
    extra_luo = []
    try:
        # 🔴 2026-10-22：昼夜按**太阳出入**（env['is_day'] 已由 `_judge_is_day` 算好）
        jp = tian_jiang_pan(rg, _zm, tdp, is_day=env.get('is_day')) or {}
    except Exception:
        jp = {}
    if jp:
        for _pn, _pv in positions:
            if not _pv or _pn not in ('末传', '干上', '支上'):
                continue
            _jiang = jp.get(_pv, '')
            if _jiang == '青龙' and _pn in ('末传', '支上'):
                extra_luo.append({'煞': '青龙', '支': _pv, '位置': [_pn], '别称': '纸钱煞'})
            elif _jiang == '太常' and _pn in _TAI_CHANG_POS:
                extra_luo.append({'煞': '太常', '支': _pv, '位置': [_pn],
                                  '别称': _TAI_CHANG_POS[_pn]})
    # 🆕 2026-09-28 憨爷「按你的建议操作」：**收魂煞**（占病大凶）
    #   判据（严守原文明文，上 L3122 ＋ L4159）：**六戊日** ＋ **日墓（＝戌）乘玄武**，
    #   且该墓神落在「干上／支上／三传」任一位置（原文案例落在**发用**）。
    #   ⚠️ 与八妖/天将类均不同：这是「**墓神**为玄武」的**组合判据**（墓＋将），
    #      ⛔ 不属起例所得，故同样只作「落点」追加、不入 `sha`／`煞值`。
    #   🔴 戊墓取「戌」而非 `WX_MU['土']='辰'`：原文案例「戊申日…三传戌酉午，武乘日墓发用」
    #      初传即戌 ⇒ 火土同宫。⛔ 不得直接套 `WX_MU`（那是水土同宫的夹墓口径）。
    #   🔴 日干限定「惟六戊一千有之」是**原文自注的成立条件**，⛔ 不得放宽到其他日干。
    if rg == '戊':
        _wu_mu = '戌'
        if jp.get(_wu_mu, '') == '玄武':
            _mu_pos = [p for p, v in positions if v and v == _wu_mu]
            if _mu_pos:
                extra_luo.append({'煞': '收魂煞', '支': _wu_mu, '位置': _mu_pos,
                                  '别称': '玄武乘日墓'})
    # 🆕 2026-10-22（《壬學瑣記》p074）**跌扑煞**：馹馬（驿马）加**辰戌**。
    #   原文逐字（读原图核过，⚠ 是「**馹**馬」不是「驺馬」；馹＝驿递之马＝驿马）：
    #     「跌撲殺，諸書未見，惟《管子神書》**馹馬加辰戌為跌撲殺**。又星命家**以馹馬併闌干
    #      主傾跌之災**，謂之闌干；**趕馬闌干即歲破**也」
    #   ⇒ 判据＝**驿马临地盘辰或戌**（天盘驿马加于地盘辰/戌）。
    #   ⚠ 影响面：R39（马姓占流年）**原文无日柱** ⇒ **无法回测** ⇒ 按铁律**只入本层
    #     （零评分影响）**，⛔ 不进评分链。
    #   ⚠ 与 `sha` 机制不同：其「落点」在**地盘**（辰/戌），非课传十处 ⇒ 走 `extra_luo`。
    if rz and isinstance(tdp, dict) and tdp:
        try:
            from engine.bifa_detector import YIMA as _YIMA
            _ym = _YIMA.get(rz, '')
            for _g in ('辰', '戌'):
                if _ym and tdp.get(_g) == _ym:
                    extra_luo.append({'煞': '跌扑', '支': _ym, '位置': ['地盘' + _g],
                                      '别称': '馹馬加辰戌'})
                    break
        except Exception:
            pass
    luo += extra_luo

    out = {'落点': luo,
           '说明': [(('%s（%s）乘%s' % (x['煞'], x['别称'], '、'.join(x['位置'])))
                     if x.get('别称')
                     else ('%s%s在%s' % (x['煞'], x['支'], '、'.join(x['位置'])))) for x in luo],
           '煞值': biao,
           # 🔴 象义**只对已取证煞**输出；命中才出，与「落点」同口径
           '象义': [{'煞': x['煞'], '象': _SHA_XIANG_YI[x['煞']][0],
                     '出处': _SHA_XIANG_YI[x['煞']][1]}
                    for x in luo if x['煞'] in _SHA_XIANG_YI]}
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
    'shensha_xiang': {'落点': [], '说明': [], '煞值': {}, '象义': []},
    'guishen_xiang': {'象域': False, '强度': 0, '候选': [], '类象语': '',
                      '祷所': '', '依据': []},
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
    # ── 寺观僧道·鬼祟取象层（**置于禳解之后**：只有 rangjie 判「宜禳」时才追加「宜祷于X方」）──
    # 🆕 2026-09-22 建层；🔴 2026-09-22 晚 218 案回测后**改定位**（第十八节）：
    #    邵公用此象 99.3% 是**类象取用**（断人33%／断地63%／断物事4%），「祷祈禳解」仅 0.7%（1/137）
    #    ⇒ 主输出改为**陈述式类象**「课传见寺观之象…」；「宜祷」降级为**宜禳时才追加**。
    #    依据：下L9631 未主祭祀神鬼／下L1182 未临宅＝鬼神／下L9598 子主祷祝鬼神
    #    ／下L4556 寅申为寺观／下L10788 龙居辰主寺观、申与僧同音／下L9643 戌主塑画／上L865 方位
    try:
        from engine.guishen_xiang_engine import suggest as _gsx
        result['guishen_xiang'] = _gsx(env, result)
    except Exception as e:
        result['guishen_xiang'] = {'象域': False, '强度': 0, '候选': [],
                                   '类象语': '', '祷所': '', '依据': [],
                                   'error': str(e)}
    # ── 六亲×神煞 冲突守卫（零评分层，2026-10-19）──
    #    🆕 🔴 零评分影响。只检「凶亲配吉神」结构并提示，⛔ 不改 score/grade/veto。
    #    起因：真实案例 INC-20240426-001（2024 占烤烟）——三传 庚申→甲寅→丁巳，
    #      初传申＝兄弟(劫财)兼禄神、末传巳＝官鬼(官讼)兼长生，断者取吉舍凶，
    #      断「收成不错」，实大亏二三十万＋官讼。他舍掉的每个字都成了现实。
    #    定则：一字多义时，六亲优先于神煞（MEMORY·术语）。
    #    依据：六亲真源 LiuQinCalculator／神煞真源 shensha_xiang.落点／禄·长生按日干查表。
    try:
        from engine.liuqin_shensha_guard import detect as _lsg
        result['liuqin_shensha_guard'] = _lsg(
            str(env.get('ri_gan') or ''),
            [str(x) for x in (env.get('sanchuan') or [])],
            env.get('sanchuan_tianjiang') or env.get('tian_jiang') or {},
            result.get('shensha_xiang') or {},
            str(env.get('zhanlei') or ''))
    except Exception as e:
        result['liuqin_shensha_guard'] = {
            '守卫': False, '冲突数': 0, '冲突': [], '说明': [], '依据': [],
            '评分影响': '无', 'error': str(e)}
    # ── 六亲象域展示层（A′，2026-09-23）──
    #    🆕 🔴 零评分影响。**只陈述**课传各位的六亲与状态，⛔ **不预测"凶应落在谁"**
    #    （A 原版经 218 案验证无信号：预测 27.4% < 随机 40.3%，特征扫描组合互相矛盾）。
    #    六亲真源＝LiuQinCalculator（生产同源）。依据：下L13114 六亲定义／上L3240／中L1544
    #    ／中L4763·L8046 生我者空亡／中L8037。
    try:
        from engine.liuqin_xiang_engine import suggest as _lqx
        result['liuqin_xiang'] = _lqx(env, result)
    except Exception as e:
        result['liuqin_xiang'] = {'象域': False, '位': [], '类象语': '',
                                  '原文直引': [], '依据': [], 'error': str(e)}
    # ── 占类条件先验谱（B，2026-09-23）──
    #    🆕 🔴 零评分影响。只说"此占类下邵公常谈哪些事因"，⛔ 不判吉凶。
    #    数据＝data/zhanyin_prior.json（218 案严格口径统计）。
    try:
        from engine.zhanyin_prior import prior_for as _prior
        result['zhanyin_prior'] = _prior(
            str(env.get('zhanlei_code') or env.get('sec_code') or ''),
            str(env.get('zhanlei') or ''))
    except Exception as e:
        result['zhanyin_prior'] = {'章': '', '占类': '', '样本': 0, '谱': [],
                                   '语': '', '来源': '', '边界': '', 'error': str(e)}
    return result
