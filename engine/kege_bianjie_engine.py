# -*- coding: utf-8 -*-
"""
六壬「变格（从属格）」规则匹配引擎 v1.0
================================================================
核心理念（2026-08-16 憨爷拍板方向）：
  504 条变格的文言条件 → 编译成「声明式规则」（DNF：原子谓词的与/或）→ 起课算事实向量 → 一次批量匹配。

规则表（data/kege_bianjie_rules.json）结构：
  {
    "rules": [
      {
        "变格": "乘轩落马", "课格": "轩盖", "吉凶": "大凶",
        "条件": [            # DNF：外层 OR（任一「项」满足即命中），内层 AND（谓词全真）
          [ {"p":"sc_set","a":["午","卯","子"]}, {"p":"x_kong","a":["卯"]} ],
          [ {"p":"sc_set","a":["午","卯","子"]}, {"p":"x_cheng_xiong","a":["卯"]} ]
        ]
      }, ...
    ]
  }
"""
import os, sys, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from engine.kege_atoms import eval_atom

_RULES_PATH = os.path.join(BASE, 'data', 'kege_bianjie_rules.json')


def _load_rules() -> list:
    try:
        kb = json.load(open(_RULES_PATH, encoding='utf-8'))
        return kb.get('rules', [])
    except Exception:
        return []


def match_rule(rule: dict, env: dict) -> bool:
    """单条规则匹配：DNF（OR of AND）"""
    for term in rule.get('条件', []):
        if all(eval_atom(p.get('p', ''), p.get('a', []), env) for p in term):
            return True
    return False


def match_all(rules: list, env: dict, zhanlei: str = '其他') -> list:
    """批量匹配所有规则，返回命中的变格列表（含吉凶/课格/占类）。
    占类过滤：规则「占类」=通用 或 =当前 zhanlei 才参与匹配（占类取用原则）。"""
    hits = []
    for r in rules:
        r_zl = r.get('占类', '通用')
        if r_zl != '通用' and r_zl != zhanlei:
            continue
        if match_rule(r, env):
            hits.append({
                'name': r.get('变格', ''),
                '课格': r.get('课格', ''),
                '等级': r.get('吉凶', ''),
                '占类': r_zl,
                '描述': r.get('说明', '') or r.get('条件说明', ''),
            })
    return hits


def build_env(ri_gan='', ri_zhi='', sanchuan=None, gan_shang='', zhi_shang='',
              tian_jiang=None, tiandi_pan=None, kongwang=('', ''), keti='',
              yuejiang='', season='', is_day=True, tai_sui='', ben_ming_zhi='',
              lunar_month=0, si_ke=None, fu_xing_nian_zhi='', qi_xing_nian_zhi='') -> dict:
    """构造课式环境 env（含预计算神煞：禄/德/驿马/月厌/四季神煞）。"""
    sc = sanchuan or []
    # 【BUG-FIX 2026-09-02】si_ke_shang：从 si_ke 提取四课上神列表（供 昼夜贵加求两贵/课传俱贵 谓词；
    # 原 build_env 未设该键 → _ke_chuan_ju_gui/_zhou_ye_gui_jia 取到空列表 → 判据不完整）
    sike_shang = []
    for _k in (si_ke or []):
        if isinstance(_k, (list, tuple)) and len(_k) > 1 and _k[1] in ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'):
            sike_shang.append(_k[1])
        elif isinstance(_k, str) and len(_k) >= 2 and _k[0] in ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'):
            sike_shang.append(_k[0])
    env = {
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'ganzhi': ri_gan + ri_zhi,
        'sanchuan': sc,
        'gan_shang': gan_shang, 'zhi_shang': zhi_shang,
        'si_ke': si_ke or [],
        'si_ke_shang': sike_shang,
        'tian_jiang': tian_jiang or {}, 'tiandi_pan': tiandi_pan or {},
        'kongwang': tuple(kongwang), 'keti': keti,
        'yuejiang': yuejiang, 'season': season, 'is_day': is_day,
        'tai_sui': tai_sui, 'ben_ming_zhi': ben_ming_zhi,
        'fu_xing_nian_zhi': fu_xing_nian_zhi, 'qi_xing_nian_zhi': qi_xing_nian_zhi,
    }

    # ── 预计算神煞（shensha: {地支: 神煞名集合}）──
    shensha = {}
    try:
        from engine.shen_sha_calculator import ShenShaCalculator
        ssc = ShenShaCalculator()
        lu = ssc.get_ri_lu(ri_gan) if ri_gan else ''
        de = ssc.get_ri_de(ri_gan) if ri_gan else ''
        yima = ssc.get_yi_ma(ri_zhi) if ri_zhi else ''
        env['lu'] = lu; env['de'] = de; env['yima'] = yima
        # 日禄/日德/驿马 作为神煞落到对应地支
        if lu: shensha.setdefault(lu, set()).add('日禄')
        if de: shensha.setdefault(de, set()).add('日德')
        if yima: shensha.setdefault(yima, set()).add('驿马')
        # 月厌
        if lunar_month:
            yueyan = ssc.get_yue_yan(lunar_month)
            if yueyan: shensha.setdefault(yueyan, set()).add('月厌')
        # 月内生气（正月起子顺行，即月建逆二辰；通解上L4793「七月生气在午」）
        if lunar_month:
            from engine.kege_atoms import DIZHI_ORDER as _DZ
            sheng_qi = _DZ[(lunar_month - 1) % 12] if 1 <= lunar_month <= 12 else ''
            if sheng_qi:
                env['sheng_qi'] = sheng_qi
                shensha.setdefault(sheng_qi, set()).add('生气')
        # 月内死气（正月起午顺行，通解下L4886「七月死气在子」）
        if lunar_month:
            from engine.kege_atoms import DIZHI_ORDER as _DZ2
            si_qi = _DZ2[(lunar_month + 5) % 12] if 1 <= lunar_month <= 12 else ''
            if si_qi:
                env['si_qi'] = si_qi
                shensha.setdefault(si_qi, set()).add('死气')
        # 血支（按月：正月丑顺行十二辰，通解上L2943「血支 丑寅卯辰巳午未申酉戌亥子」）
        if lunar_month:
            from engine.kege_atoms import DIZHI_ORDER as _DZ4
            xue_zhi = _DZ4[lunar_month % 12] if 1 <= lunar_month <= 12 else ''
            if xue_zhi:
                env['xue_zhi'] = xue_zhi
                shensha.setdefault(xue_zhi, set()).add('血支')
        # 血忌（按月：正月丑、二月未…硬编码，通解上L2945「血忌 丑未寅申卯酉辰戌巳亥午子」）
        if lunar_month:
            _XUE_JI = ['丑','未','寅','申','卯','酉','辰','戌','巳','亥','午','子']
            xue_ji = _XUE_JI[lunar_month - 1] if 1 <= lunar_month <= 12 else ''
            if xue_ji:
                env['xue_ji'] = xue_ji
                shensha.setdefault(xue_ji, set()).add('血忌')
        # 飞廉（按月：正月戌、二月巳…硬编码，通解上L2957「飞廉 戌巳午未寅卯辰亥子丑申酉」）
        if lunar_month:
            _FEI_LIAN = ['戌','巳','午','未','寅','卯','辰','亥','子','丑','申','酉']
            fei_lian = _FEI_LIAN[lunar_month - 1] if 1 <= lunar_month <= 12 else ''
            if fei_lian:
                env['fei_lian'] = fei_lian
                shensha.setdefault(fei_lian, set()).add('飞廉')
        # 旬丁神（甲子旬丁卯、甲戌旬丁丑…；旬丁=旬首支+3，通解p138）
        if ri_gan and ri_zhi:
            try:
                from engine.kege_atoms import DIZHI_ORDER as _DZ3
                _g_idx = '甲乙丙丁戊己庚辛壬癸'.index(ri_gan)
                _z_idx = _DZ3.index(ri_zhi)
                _shou = (_z_idx - _g_idx) % 12
                _ding = _DZ3[(_shou + 3) % 12]
                env['ding_shen'] = _ding
                shensha.setdefault(_ding, set()).add('丁神')
                # 【P4 旬首旬尾收敛 2026-09-03】旬首支/旬尾支（首尾相见·一旬周遍 / 闭口卦两般推 判据）。
                # 旬首按「日支-日干 地支环距」定位（甲子0/甲寅2/甲辰4/甲午6/甲申8/甲戌10），旬尾=旬首+9；
                # 原 build_env 未设 xun_shou_zhi/xun_wei_zhi → shou_wei_xiang_jian_v2/bi_kou_gua_v2 恒假断链。
                env['xun_shou_zhi'] = _DZ3[_shou]
                env['xun_wei_zhi'] = _DZ3[(_shou + 9) % 12]
            except Exception:
                pass
        # 【BUG-FIX 2026-09-11】分旬空亡（本旬/前旬/后旬/外前旬/外后旬）：
        #   kege_atoms._kong_kong_ru_ye 第④判据「踏空」与 _jinru_kong_wang/_tuiru_kong_wang
        #   均读 env['fen_xun_kong']，但原 build_env 从未产出该键 → 取 {} → **恒假断链**
        #   （实测「三传皆空格/四课全空格/鬼空尤妙亦宜制之」三规则命中断链至 ①②③ 三种空）。
        #   来源与口径与毕法赋引擎完全一致（bifa_detector.get_fen_xun_kong 单源复用，不另造表）。
        #   原文依据：《六壬大全》第十八法「踏脚空亡」——「甲子日戌加子为初传乃本旬之空，
        #   申加戌为中传乃后旬之空，午加申为末传乃外后旬之空亡」。
        if ri_gan and ri_zhi:
            try:
                from engine.bifa_detector import get_fen_xun_kong as _gfk
                _fxk = _gfk(ri_gan + ri_zhi)
                if _fxk:
                    env['fen_xun_kong'] = _fxk
            except Exception:
                pass
        # 【BUG-FIX 2026-09-11】三传走势（进连茹/退连茹/顺间传/逆间传/三合/其他）：
        #   kege_atoms._jinru_kong_wang / _tuiru_kong_wang 读 env['trend']（原缺 → 恒假）；
        #   _kong_kong_ru_ye 第④判据「踏空」亦按原文限定于进退连茹/间传课（同键）。
        #   来源与口径单源复用毕法赋引擎 _get_sanchuan_trend，不另造表。
        if sc and len(sc) == 3 and all(sc):
            try:
                from engine.bifa_detector import _get_sanchuan_trend as _gst
                env['trend'] = _gst(list(sc))
            except Exception:
                pass
        # 四季神煞（丧车/天目/关神/孤辰/寡宿/四废 等，按季节）
        jjs = getattr(ssc, 'JI_JIE_SHA', {})
        if season and jjs:
            for sha_name, by_season in jjs.items():
                z = by_season.get(season, '')
                if z:
                    shensha.setdefault(z, set()).add(sha_name)
        # 破碎（按日支：子午卯酉在巳、寅申巳亥在酉、辰戌丑未在丑，通解上L926/3056）
        try:
            _zsha = ssc.get_zhi_sha(ri_zhi) if ri_zhi else {}
            _posui = _zsha.get('破碎', '')
            if _posui:
                env['posui'] = _posui
                shensha.setdefault(_posui, set()).add('破碎')
        except Exception:
            pass
        # 羊刃（按日干，通解上p138 阳刃表；对齐子平标准）
        try:
            _yangren = ssc.get_yang_ren(ri_gan) if ri_gan else ''
            if _yangren:
                env['yang_ren'] = _yangren
                shensha.setdefault(_yangren, set()).add('羊刃')
        except Exception:
            pass
        # 天医（按月，YUE_SHA 表：正月辰顺行，通解上L73「天医=月建前二辰」）
        try:
            _tianyi = ssc.get_yue_sha(lunar_month).get('天医', '') if lunar_month else ''
            if _tianyi:
                env['tian_yi'] = _tianyi
                shensha.setdefault(_tianyi, set()).add('天医')
        except Exception:
            pass
        # 【B5d 2026-09-03】天鬼（伏殃煞，正月起酉逆行四仲：酉午卯子循环，毕法赋·鬼临三四讼灾随）。
        # 原 build_env 未算入 shensha → 天鬼作日鬼格 x_shi_shensha(位,天鬼) 恒假 0 命中断链。
        if lunar_month:
            _TIAN_GUI = ['酉', '午', '卯', '子']
            try:
                tian_gui = _TIAN_GUI[(lunar_month - 1) % 4]
                if tian_gui:
                    env['tian_gui'] = tian_gui
                    shensha.setdefault(tian_gui, set()).add('天鬼')
            except Exception:
                pass
        # 【BUG-FIX 2026-09-01】丧门/吊客（按年支，供「丧吊全逢格」挂缟衣 判据；
        # 原 build_env 未算入 shensha → _sang_diao_quan_feng 恒假 → 丧吊全逢系列 3 位点断链）
        if tai_sui:
            try:
                _sd = ssc.get_sang_diao(tai_sui) or {}
                _sm = _sd.get('丧门', '')
                _dk = _sd.get('吊客', '')
                if _sm:
                    shensha.setdefault(_sm, set()).add('丧门')
                if _dk:
                    shensha.setdefault(_dk, set()).add('吊客')
            except Exception:
                pass
        # 【BUG-FIX 2026-09-01】贵人地支（阳贵/阴贵）：供 x_shi_guiren 谓词
        # （两贵受克/贵塞鬼户/神藏煞没/昼夜贵相加 等 52 谓词位点、20+ 规则）；
        # 原 build_env 未设 env['guiren'] → x_shi_guiren 恒假 → 贵人相关规则全部断链。
        try:
            from engine.gui_ren_engine import GuiRenCalculator
            _grc = GuiRenCalculator()
            env['guiren'] = (
                _grc.get_gui_ren_by_ri_gan(ri_gan, is_night=False) if ri_gan else '',
                _grc.get_gui_ren_by_ri_gan(ri_gan, is_night=True) if ri_gan else '',
            )
        except Exception:
            env['guiren'] = ()
    except Exception:
        pass
    env['shensha'] = shensha
    return env


def detect_bianjie(ri_gan='', ri_zhi='', sanchuan=None, gan_shang='', zhi_shang='',
                   tian_jiang=None, tiandi_pan=None, kongwang=('', ''), keti='',
                   yuejiang='', season='', is_day=True, tai_sui='', ben_ming_zhi='',
                   lunar_month=0, zhanlei='其他', si_ke=None,
                   fu_xing_nian_zhi='', qi_xing_nian_zhi='') -> dict:
    """主入口：检测一课命中的所有变格（从属格），按占类过滤。"""
    env = build_env(ri_gan, ri_zhi, sanchuan, gan_shang, zhi_shang, tian_jiang,
                    tiandi_pan, kongwang, keti, yuejiang, season, is_day, tai_sui,
                    ben_ming_zhi, lunar_month, si_ke, fu_xing_nian_zhi, qi_xing_nian_zhi)
    hits = match_all(_load_rules(), env, zhanlei)
    return {
        '匹配变格': [h['name'] for h in hits],
        '变格详情': {h['name']: {'等级': h['等级'], '课格': h['课格'], '占类': h['占类'], '描述': h['描述']} for h in hits},
        '命中数': len(hits),
    }
