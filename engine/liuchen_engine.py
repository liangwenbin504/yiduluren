# -*- coding: utf-8 -*-
"""
事体走向引擎（六壬断事流程 · 2026-08-18 · 占类化增强版）
=============================================================
核心思想（用户方法论）：六壬判断除吉凶外，主要判断**事体的变化过程与走向**——
初始如何 → 中途如何 → 最终如何。吉凶只是走向的终点标签，走向本身才是主体。

v2 占类化增强（2026-08-18 用户指示"占类化走向规则一定要打扎实"）：
  每个占类（功名/疾病/官讼/求财/家宅/胎产/出行/婚姻/贼盗/行人）有专属走向规则，
  规则全部来自：
    A. 知识库 shishi_categories key_principles（duanan_knowledge_base.py，原文）
    B. 壬占汇选543案断语原文（案例ID可查，如 CASE-壬占汇选-0520）
  每条规则标注出处（L行号=知识库行号 / §=疏正案例 / CASE=壬占汇选案例），
  无古籍依据的判据一律不写（用户铁律：不能编造）。

输出：{'走向': '先难后易'/'先吉后凶'/..., '阶段': {初/中/末 各自态势},
       '叙事': '先...，中...，末...', '终局': '吉'/'凶'/'平'}
"""
import os
import sys
from typing import Dict, List, Any, Optional

try:
    from engine.liuchen_shensha import you_du, jie_sha, tian_ma, tian_she, xue_ji, tai_sui, sui_po
except Exception:
    you_du = jie_sha = tian_ma = tian_she = xue_ji = tai_sui = sui_po = lambda *a, **k: ''

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 地支五行/天干五行
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
# 日墓（五行三合墓）
GAN_MU = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
          '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}
# 五行长生
WX_CS = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}
# 五行绝
WX_JUE = {'木': '申', '火': '亥', '金': '寅', '水': '巳', '土': '巳'}
# 天将吉凶
_JI_JIANG = {'贵人', '青龙', '六合', '太常', '天后', '太阴'}
_XIONG_JIANG = {'白虎', '玄武', '螣蛇', '朱雀'}
# 日干禄神（甲禄寅、乙禄卯、丙戊禄巳、丁己禄午、庚禄申、辛禄酉、壬禄亥、癸禄子）
LU_SHEN = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
           '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# ── 占类六亲（L270 财爻 / L1315 官鬼 / L1647 官星）──
def _shi_shen(zhi: str, ri_gan: str) -> str:
    """地支对日干的六亲：官鬼/妻财/父母/子孙/兄弟"""
    if not zhi or not ri_gan:
        return ''
    zw = ZHI_WX.get(zhi, '')
    gw = GAN_WX.get(ri_gan, '')
    if not zw or not gw:
        return ''
    if KE.get(zw) == gw:
        return '官鬼'
    if KE.get(gw) == zw:
        return '妻财'
    if SHENG.get(zw) == gw:
        return '父母'
    if SHENG.get(gw) == zw:
        return '子孙'
    return '兄弟'


def _duan_shi(zhi: str, ri_gan: str, tj: str, kong: set) -> str:
    """单传态势：吉/凶/平（地支生克 + 天将 + 空亡）。"""
    if not zhi:
        return '平'
    s = 0.0
    gw = GAN_WX.get(ri_gan, '')
    zw = ZHI_WX.get(zhi, '')
    if gw and zw:
        if KE.get(zw) == gw:
            s -= 2  # 克日
        elif SHENG.get(gw) == zw:
            s -= 1  # 泄日
        elif SHENG.get(zw) == gw:
            s += 2  # 生日
    if tj in _JI_JIANG:
        s += 1.5
    elif tj in _XIONG_JIANG:
        s -= 1.5
    if zhi in kong:
        s -= 1.5
    if s >= 1:
        return '吉'
    if s <= -1:
        return '凶'
    return '平'


class LiuChenEngine:
    """事体走向引擎：三阶段（初=始/中=过程/末=结局）走向判定 + 占类化规则"""

    def _mk(self, walk, end, chu_shi, zhong_shi, mo_shi, chu, zhong, mo, narr, source=''):
        out = {
            '走向': walk,
            '终局': end,
            '阶段': {'初传': chu_shi, '中传': zhong_shi, '末传': mo_shi},
            '叙事': narr,
            '三传': f'{chu}·{zhong}·{mo}',
        }
        if source:
            out['出处'] = source
        return out

    # ══════════════════════════════════════════════════════════════
    # 占类化走向规则表（每条含古籍出处：L=知识库行号 / §=疏正案例 / CASE=壬占汇选）
    # 条件全部可计算：三传地支/天将/旬空/课体/四课。
    # ══════════════════════════════════════════════════════════════
    def _category_rules(self, category: str, ri_gan: str, ri_zhi: str,
                        chu: str, zhong: str, mo: str,
                        chu_tj: str, zhong_tj: str, mo_tj: str,
                        kong: set, keti: str, sike: List,
                        zishu: str = '', yuejiang: str = '', year: str = '',
                        sike_tj: Dict = None) -> Optional[Dict]:
        gw = GAN_WX.get(ri_gan, '')
        _tjmap = sike_tj or {}
        mu_zhi = GAN_MU.get(ri_gan, '')
        cs_zhi = WX_CS.get(gw, '')
        jue_zhi = WX_JUE.get(gw, '')
        chu_wx, zhong_wx, mo_wx = ZHI_WX.get(chu, ''), ZHI_WX.get(zhong, ''), ZHI_WX.get(mo, '')
        chu_shi = _duan_shi(chu, ri_gan, chu_tj, kong)
        zhong_shi = _duan_shi(zhong, ri_gan, zhong_tj, kong)
        mo_shi = _duan_shi(mo, ri_gan, mo_tj, kong)
        # 三传递生/递克
        di_sheng = bool(gw and chu_wx and zhong_wx and mo_wx and
                        SHENG.get(chu_wx) == zhong_wx and SHENG.get(zhong_wx) == mo_wx and
                        SHENG.get(mo_wx) == gw)
        di_ke = bool(gw and chu_wx and zhong_wx and mo_wx and
                     KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx and
                     KE.get(mo_wx) == gw)
        # 三传自墓传生 / 自生传墓（L544"三传自墓传生患易瘥，自生传墓者难瘳"）
        zi_mu_chuan_sheng = (chu == mu_zhi and mo == cs_zhi)
        zi_sheng_chuan_mu = (chu == cs_zhi and mo == mu_zhi)
        # 循环格：三传不离四课（L1077"循环格主病多反复"）
        xun_huan = False
        if sike and len(sike) >= 4:
            sike_zhi = set()
            for k in sike:
                if isinstance(k, (list, tuple)) and len(k) >= 2:
                    sike_zhi.add(str(k[1]))
                    if len(k) >= 3:
                        sike_zhi.add(str(k[2]))
                elif isinstance(k, dict):
                    sike_zhi.add(str(k.get('上神', '')))
                    sike_zhi.add(str(k.get('下神', '')))
            xun_huan = {chu, zhong, mo} <= sike_zhi
        # 官鬼/财爻在三传
        guan_gui_zhi = [z for z in (chu, zhong, mo) if _shi_shen(z, ri_gan) == '官鬼']
        cai_zhi = [z for z in (chu, zhong, mo) if _shi_shen(z, ri_gan) == '妻财']
        # 日干禄神（功名/求财等占类共用；甲禄寅、乙禄卯、丙戊禄巳、丁己禄午、庚禄申、辛禄酉、壬禄亥、癸禄子）
        lu_zhi = LU_SHEN.get(ri_gan, '')
        # 【神煞占类化 2026-08-18】游都/劫煞按日干日支恒可算；天马/天赦/血忌需月将（yuejiang）。
        # 口诀出处见 engine/liuchen_shensha.py（游都"丙辛只向功曹上"、劫煞"中传劫煞"、
        # 天马"中传天罡为天马"、天赦"春三月天赦在寅"、血忌"五月应在卯"）
        _ss_yd = you_du(ri_gan)          # 游都
        _ss_js = jie_sha(ri_zhi)         # 劫煞
        _ss_tm = tian_ma(yuejiang) if yuejiang else ''   # 天马
        _ss_ts = tian_she(yuejiang) if yuejiang else ''  # 天赦
        _ss_xj = xue_ji(yuejiang) if yuejiang else ''    # 血忌
        _ss_tsui = tai_sui(year) if year else ''          # 太岁
        _ss_spo = sui_po(year) if year else ''            # 岁破
        # 官星发用（L"求官用起官星"）
        guan_xing_fa_yong = _shi_shen(chu, ri_gan) == '官鬼'
        # 白虎乘鬼（L545"虎乘日鬼同入三传主大凶"）
        hu_gui = (chu_tj == '白虎' and _shi_shen(chu, ri_gan) == '官鬼') or \
                 (zhong_tj == '白虎' and _shi_shen(zhong, ri_gan) == '官鬼') or \
                 (mo_tj == '白虎' and _shi_shen(mo, ri_gan) == '官鬼')
        # 四课：干上神/支上神（sike 顺序：一二=干上，三四=支上）
        gan_shang = ''
        zhi_shang = ''
        if sike and len(sike) >= 4:
            def _sp(k):
                if isinstance(k, (list, tuple)) and len(k) >= 2:
                    return str(k[1])
                if isinstance(k, dict):
                    return str(k.get('上神', ''))
                return ''
            gan_shang = _sp(sike[0])
            zhi_shang = _sp(sike[2])
        # 干支上神天将（sike_tj 天将映射，供贵人乘贵/朱雀位置等规则）
        _gan_shang_tj = _tjmap.get(gan_shang, '')
        _zhi_shang_tj = _tjmap.get(zhi_shang, '')
        gan_ke_zhi_shang = bool(gan_shang and zhi_shang and
                                KE.get(ZHI_WX.get(gan_shang, '')) == ZHI_WX.get(zhi_shang, ''))
        zhi_ke_gan_shang = bool(gan_shang and zhi_shang and
                                KE.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(gan_shang, ''))
        # 天将：青龙/天后/玄武在传
        qing_long_zai_chuan = chu_tj == '青龙' or zhong_tj == '青龙' or mo_tj == '青龙'
        tian_hou_zai_chuan = chu_tj == '天后' or zhong_tj == '天后' or mo_tj == '天后'
        xuan_wu_zai_chuan = chu_tj == '玄武' or zhong_tj == '玄武' or mo_tj == '玄武'
        # 伏吟/返吟课体
        fu_yin = '伏吟' in keti
        # 【BUG-FIX 2026-08-18】课体名有"返吟"（V1）与"反吟"（V2引擎）两种写法，都匹配
        fan_yin = ('返吟' in keti) or ('反吟' in keti)

        # ── 通用占类守卫（所有占类共用，须优先于占类兜底规则）──
        # 末传=长生但空亡 → 见生不生，反成凶咎（L235"救神空亡为墓门开大凶"；
        #   案例0369"末又长生…奈何寅是空亡，所以不能引进，见生不生，反成凶咎"）
        if mo == cs_zhi and mo in kong:
            return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            f'末传{mo}为日干长生，然逢空亡，见生不生，救神空亡，反成凶咎',
                            'L235"救神空亡为墓门开大凶"; CASE-壬占汇选-0369')
        # 【指南深读 第五轮】末传空亡 且 中传=日干官鬼（初末逢空，独存中传，鬼临中途结局落空）
        #   → 文书得罪/事败于中途（ZN-章奏-五"初末逢空，独存中传，岁破为鬼……
        #   恐得罪于君相，于公不利"——癸卯日三传酉丑巳，末巳空、中传丑=癸之官鬼）
        if mo in kong and zhong_wx and KE.get(zhong_wx) == gw:
            return self._mk('中鬼末空', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            f'末传{mo}空亡而中传{zhong}为日干官鬼，初末逢空独存中鬼，事败于中途，恐得罪于人',
                            'ZN-章奏-五"初末逢空，独存中传，岁破为鬼…恐得罪于君相"')

        # ───────────────────────────
        # 【功名】（前程仕进·邵公断案60案深读增强 2026-08-18）
        # 刘评归纳："举凡仕宦之占，无非官、禄两样最为切要"（§058）；
        # "幕贵乃科名第一吉神"（§052）；"大凡占前程禄重于财"（§046）。
        # 层次：先课体课格（乱首/顾祖/四绝/登三天/铸印/六阴），
        #       次官禄切要（官星临身/禄临干/禄空/贵空），后幕贵学堂/脱耗。
        # ───────────────────────────
        if category == '功名':
            # 贵人（旦贵/暮贵）地支集
            GUI_REN_ZHI = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'},
                           '戊': {'丑', '未'}, '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'},
                           '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
            gui_zhi_set = GUI_REN_ZHI.get(ri_gan, set())
            # 羊刃（甲卯、丙午、戊午、庚酉、壬子）
            YANG_REN2 = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
            yang_ren = YANG_REN2.get(ri_gan, '')
            # 三传含官星数
            guan_cnt = sum(1 for z in (chu, zhong, mo) if _shi_shen(z, ri_gan) == '官鬼')
            # 干上神=官星（官星临身，§059"申官星临身龙神入庙"、§072"官星临日初传应之谓之催官符"）
            guan_lin_shen = bool(gan_shang and _shi_shen(gan_shang, ri_gan) == '官鬼')
            # 干上神=禄神（禄临干，§044"午乃丁禄临干日禄扶身"）
            lu_lin_gan = bool(lu_zhi and gan_shang == lu_zhi)
            # 禄神在三传且空亡（禄空，§055"禄空故不可为武"、§076"末又是禄乘空亡入墓"）
            lu_kong = bool(lu_zhi and any(z == lu_zhi and z in kong for z in (chu, zhong, mo)))
            # 干上神=贵人且空亡（贵空=虚贵，§060"贵人又乘空乃是虚贵"、§103"昼贵人空虚是贵而无位也"）
            gui_kong = bool(gan_shang in gui_zhi_set and gan_shang in kong)
            # 干支上神皆乘墓（§064"干支皆墓主前程迟滞"）
            gan_zhi_jie_mu = bool(gan_shang == mu_zhi and zhi_shang == GAN_MU.get(ri_gan, ''))
            # 干支上神自刑（§057"干支自刑主自满"）
            _ZI_XING2 = {'辰', '午', '酉', '亥'}
            zi_xing = bool((gan_shang in _ZI_XING2 and zhi_shang in _ZI_XING2) or
                           (gan_shang == ri_zhi and gan_shang in _ZI_XING2))
            # 三传皆子孙（脱气，§046"脱上逢脱必诗书荒废"、§093"一火生四土叠叠脱气"）
            zi_sun_all = all(_shi_shen(z, ri_gan) == '子孙' for z in (chu, zhong, mo))
            # 满局贵人（贵多不贵，§053"满局皆贵人贵多不贵慕十不得一"、§087"三传日辰遍地贵人"）
            # 【BUG-FIX 2026-08-18】§052 干上卯贵人（幕贵临干）+日贵巳末传=先晦后明吉，
            #   非贵多不贵——须贵人≥3处且≥2处空亡/受克（§053"身与初中皆空慕十不得一"）才判凶。
            gui_weizhi = [z for z in (gan_shang, zhi_shang, chu, zhong, mo)
                          if z and z in gui_zhi_set]
            gui_duo = len(gui_weizhi)
            gui_kong_cnt = sum(1 for z in gui_weizhi if z in kong)
            gui_duo_bad = gui_duo >= 3 and gui_kong_cnt >= 2
            # 四绝课：四正加四孟（干支上神构成四绝——§066"金绝寅、水绝巳、木绝申、火绝亥"）
            jue_zhi_set = {'寅': '申', '申': '寅', '巳': '亥', '亥': '巳'}  # 简化：干上/支上互为绝
            si_jue = bool(gan_shang and zhi_shang and
                          jue_zhi_set.get(gan_shang) == zhi_shang and
                          gan_shang in jue_zhi_set)
            # 铸印格：三传巳戌卯（§049"戌为模范亦落空地"、§050"朱雀投戌墓破模"）
            #   【指南深读 2026-08-18】{巳,丑,酉}为从革递生，非铸印——陈公献
            #   "传将递生格合周遍……必中无疑"（ZN-选举-六）仍主吉，不作损模凶断。
            zhu_yin = ({chu, zhong, mo} == {'巳', '戌', '卯'})
            # 顾祖课（初传=干上神 且 传退入支（§074"日上发传退入支上又是顾祖"））——
            #   判据：初传=干上神 且 末传贴近日支（d_mo <= 2 且 末传比初传更近支）
            #   【BUG-FIX 2026-08-18】§055 干上申=禄（弃武从文吉）、§058 干上寅=官星空
            #   （正任不可望但禄临支食禄吉），均非顾祖凶——守卫：干上神非禄神且非空亡官星。
            _zhi_seq2 = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                         '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
            _gu_zu_core = False
            if chu == gan_shang and ri_zhi in _zhi_seq2 and chu in _zhi_seq2 and mo in _zhi_seq2:
                _d_chu = abs(_zhi_seq2[chu] - _zhi_seq2[ri_zhi])
                _d_chu = min(_d_chu, 12 - _d_chu)
                _d_mo = abs(_zhi_seq2[mo] - _zhi_seq2[ri_zhi])
                _d_mo = min(_d_mo, 12 - _d_mo)
                _gu_zu_core = _d_mo <= 2 and _d_mo <= _d_chu
            # 守卫：干上神=禄神（禄临干吉，§055）或 干上神=空亡官星（正任不可望但食禄，§058）
            _lu_wei = (lu_zhi and gan_shang == lu_zhi)
            _gui_kong_gs = (gan_shang in kong and _shi_shen(gan_shang, ri_gan) == '官鬼')
            gu_zu = _gu_zu_core and not _lu_wei and not _gui_kong_gs

            # ⑥g 【指南深读 2026-08-18】三合局=日干官鬼 → 官局峥嵘，功名吉
            #   （ZN-仕宦-九"传将木局，官星峥嵘……功名显赫"、ZN-仕宦-三十二"传课结成官局……
            #   事业远大"；三合官局为官星成局，最利功名）
            _SANHE_G = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
            _SANHE_WX = ['水', '火', '金', '木']
            _gju_wx = ''
            for _gj, _gw2 in zip(_SANHE_G, _SANHE_WX):
                if {chu, zhong, mo} == _gj:
                    _gju_wx = _gw2
                    break
            if _gju_wx and KE.get(_gju_wx) == gw:
                # 【指南深读 2026-08-18】守卫②：无禄课（四课上神俱克下）不判官局吉——
                #   CASE-0318 无禄+官局仍断"无禄难食"（§076）
                _wulu_gj = bool(gan_shang and zhi_shang and ri_zhi and
                                KE.get(ZHI_WX.get(gan_shang, '')) == gw and
                                KE.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(ri_zhi, ''))
                if not _wulu_gj:
                    # 【指南深读 2026-08-18 第二轮】守卫①：官鬼局 + 初传=官鬼 → 需"干支乘墓或
                    #   日干死地"（合中犯煞）才凶——ZN-仕宦-七"干败支墓"（支上丑=辛墓）、
                    #   ZN-仕宦-三十"干支死伤"（干上卯=己死地）；否则官局仍吉
                    #   （ZN-选举-三"贵临贵位……两贵周旋推荐"昆弟皆中）
                    _GJ_SI = {'木': '午', '火': '酉', '金': '子', '水': '卯', '土': '卯'}
                    _gj_si_zhi = _GJ_SI.get(gw, '')
                    if _shi_shen(chu, ri_gan) == '官鬼' and (
                            gan_shang == mu_zhi or zhi_shang == mu_zhi or
                            gan_shang == _gj_si_zhi or zhi_shang == _gj_si_zhi):
                        return self._mk('官局受阻', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                        f'三传{chu}·{zhong}·{mo}官鬼局而初传{chu}又为官鬼，干支乘墓/死地，合中犯煞，推升虽必而结局不佳',
                                        'ZN-仕宦-七"合中犯煞，发用午火刑干害支"; ZN-仕宦-三十"干支死伤…结局不佳"')
                    return self._mk('官局峥嵘', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'三传{chu}·{zhong}·{mo}成{_gju_wx}局为日干官鬼局，官星成局，官局峥嵘，功名远大',
                                    'ZN-仕宦-九"传将木局，官星峥嵘"; ZN-选举-三"两贵周旋推荐"')
            # ⑥h 【指南深读 2026-08-18】三合财局 + 末传空亡 → 财局虚设，功名凶
            #   （ZN-仕宦-二十四"传将递生空亡……难以迁转"；传课纯财则印爻被克）
            if _gju_wx and KE.get(gw) == _gju_wx and mo in kong:
                return self._mk('财局空陷', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}财局而末传{mo}空亡，传课纯财印爻被克，虚设难迁',
                                'ZN-仕宦-二十四"传将递生空亡…难以迁转"')
            # ⑥f 【指南深读 第三轮】干上神=日干绝地 → 贵德临身/德丧禄绝分判
            #   （ZN-选举-七"贵德财马临身，且居太岁之位，必应今年甲榜"——干上巳=癸德亦=癸绝；
            #    ZN-仕宦-十一"干支乘死绝，德丧禄绝…必主去位"——干上申=甲绝=官鬼）
            _DE_ZHI = {'甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
                       '己': '亥', '庚': '申', '辛': '午', '壬': '巳', '癸': '巳'}
            if gan_shang == jue_zhi:
                if gan_shang == _DE_ZHI.get(ri_gan, ''):
                    return self._mk('贵德临身', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上神{gan_shang}为日德临身，贵德财马临身，必应今科甲榜',
                                    'ZN-选举-七"贵德财马临身，且居太岁之位，必应今年甲榜"')
                return self._mk('德丧禄绝', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}为日干绝地，干支乘死绝，德丧禄绝，朝官必主去位',
                                'ZN-仕宦-十一"干支乘死绝，德丧禄绝…必主去位"')
            # ⑥g2 【指南深读 第三轮】返吟 + 初传=日德（德入天门发用）→ 必中高魁
            #   （ZN-选举-五"戊日返吟是德入天门发用，丑未两贵相加…必中高魁"；
            #   守卫：干上=日绝先判（德丧禄绝凶优先，仕宦十一））
            if fan_yin and chu == _DE_ZHI.get(ri_gan, ''):
                return self._mk('德入天门', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'返吟课初传{chu}为日德入天门发用，德贵相加，必中高魁',
                                'ZN-选举-五"返吟是德入天门发用，丑未两贵相加…必中高魁"')
            # ⑥g3 【指南深读 第三轮】循环格 + 末传=日禄 → 德禄入末，功名吉
            #   （ZN-选举-一"末传德禄驿马，干支交车生合…必中高魁"）
            #   守卫：官星临身（§072 催官符先成后败）或禄临支（权摄食禄 §067）不判
            if xun_huan and lu_zhi and mo == lu_zhi and not guan_lin_shen and \
                    not (lu_zhi and zhi_shang == lu_zhi):
                return self._mk('德禄入末', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'循环格而末传{mo}为日禄，末传德禄驿马，干支交车生合，功名顺遂',
                                'ZN-选举-一"末传德禄驿马…必中高魁"')
            # ⑥g4 【指南深读 第三轮】干上=日墓 且 支上=日支绝地 → 干墓支绝，凶
            #   （ZN-仕宦-十九"干墓支绝…必解任去"——甲午日干上未=甲墓、支上亥=午之绝）
            _rz_wx = ZHI_WX.get(ri_zhi, '')
            _zhi_jue_d = WX_JUE.get(_rz_wx, '')
            if gan_shang == mu_zhi and _zhi_jue_d and zhi_shang == _zhi_jue_d:
                return self._mk('干墓支绝', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上{gan_shang}为日墓，支上{zhi_shang}为日支绝地，干墓支绝，功名非久远之象',
                                'ZN-仕宦-十九"干墓支绝…必解任去"')
            # ⑥g5 【指南深读 第三轮】支上神=官星：=贵人 → 官星临支吉（ZN-仕宦-二十九
            #   "亥贵作官星临支"）；非贵人 → 鬼临三四凶（ZN-仕宦-二十一"鬼临三四必主他非退位"）
            #   守卫（官星临支）：干支自刑（§062/081自满失宠）与赘婿（§065）不判吉
            if zhi_shang and _shi_shen(zhi_shang, ri_gan) == '官鬼':
                if zhi_shang in gui_zhi_set and not zi_xing and \
                        not (gan_shang == ri_zhi and ri_zhi and KE.get(gw) == ZHI_WX.get(ri_zhi, '')):
                    return self._mk('官星临支', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'支上神{zhi_shang}为官星又系贵人，官星临支，功名先推之征',
                                    'ZN-仕宦-二十九"亥贵作官星临支"')
                return self._mk('鬼临三四', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}为日干官鬼，鬼临三四课，必主他非退位',
                                'ZN-仕宦-二十一"鬼临三四，必主他非退位"')
            # ⑥g6 【指南深读 第四轮】干支上神皆=天罗（日干寄宫前一位）→ 罗网退职凶
            #   （ZN-仕宦-八"干支年命俱见罗网……仕宦忌罗网，以罗网为丁忧之象，主退职也"——
            #   己未日己寄未，天罗申，干支上皆申；八专自他处发用）
            _GAN_JI4 = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
                        '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}
            _TIANLUO_NEXT = {'寅': '卯', '辰': '巳', '巳': '午', '未': '申', '申': '酉',
                             '戌': '亥', '亥': '子', '卯': '辰', '午': '未', '酉': '戌',
                             '子': '丑', '丑': '寅'}
            _tianluo = _TIANLUO_NEXT.get(_GAN_JI4.get(ri_gan, ''), '')
            if _tianluo and gan_shang == _tianluo and zhi_shang == _tianluo:
                return self._mk('罗网退职', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支上神皆{_tianluo}为天罗，仕宦忌罗网，罗网为丁忧退职之象，恐不能也',
                                'ZN-仕宦-八"干支年命俱见罗网…仕宦忌罗网，以罗网为丁忧之象"')
            # ⑦ 干支自刑 → 自满失宠（§057"干支自刑主自满"；置于禄/贵之前——§057禄临干
            #   但自刑仍断"升转则未"，自刑优先）
            if zi_xing:
                return self._mk('自满失宠', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支自刑（干{gan_shang}支{zhi_shang}），主自满骄傲，因宠生祸失官',
                                '§前程仕进03·057"干支自刑主自满"')
            # ⑦a 赘婿课（支来就干为干所克，§065"支来就干为干所克…课名赘婿所以无正居"）→ 无正宅
            #   【BUG-FIX 2026-08-18】§065 干上申=支来就干受丙克=赘婿，无正宅，止于小职——
            #   置于三传递生之前，防"荐举升迁"误判吉
            if gan_shang == ri_zhi and ri_zhi and KE.get(gw) == ZHI_WX.get(ri_zhi, ''):
                return self._mk('赘婿无宅', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支{ri_zhi}来就干为干所克，课名赘婿，无正宅，多居寺观妻家，前程止于小职',
                                '§前程仕进03·065"支来就干为干所克…课名赘婿所以无正居也"')
            # ⑦c 顾祖课（初传=干上神且传退入支）→ 仕途受阻（§074"日上发传退入支上又是顾祖
            #   …仕途必定受阻"、§097"顾祖传空前程镜中花"）——课体级凶象，优先于官星吉
            #   【指南深读 第三轮 回滚】循环格守卫已撤——§087 顾祖传空（邵公凶）与
            #   ZN-仕宦-二十"格合周遍"（陈公献吉）同构冲突，以已深读疏正（邵公）体系为准
            if gu_zu:
                return self._mk('顾祖受阻', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}退入支上，顾祖课，仕途受阻，升转无望',
                                '§前程仕进03·074"日上发传退入支上又是顾祖"; §097"顾祖传空前程镜中花"')
            # ⑦d 返吟+初传官星 → 旧政迟任（§063"此课旧政上又见旧政…第六年方得赴任"；
            #   课体级凶象，优先于官星临身吉——§063 干上未=官星但返吟旧政迟任凶）
            if fan_yin and _shi_shen(chu, ri_gan) == '官鬼':
                return self._mk('旧政迟任', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'返吟课旧政上又见旧政，迁延迟任，第六年方得赴任',
                                '§前程仕进03·063"旧政上又见旧政…第六年方得赴任"')
            # ⑦e 无禄课（四课上神俱克下）→ 必不能食禄（§076"无禄课虽受通判必不能食禄"；
            #   判据：干上神克日干 且 支上神克日支）
            #   【BUG-FIX 2026-08-18】守卫：支上神=日禄（禄临支=权摄不正但食禄吉，§058"戊禄临支
            #   正任不可望却乃食禄"）时不判无禄
            if gan_shang and zhi_shang and ri_zhi and not (lu_zhi and zhi_shang == lu_zhi):
                _gan_shang_ke = KE.get(ZHI_WX.get(gan_shang, '')) == gw
                _zhi_shang_ke = KE.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(ri_zhi, '')
                if _gan_shang_ke and _zhi_shang_ke:
                    # 【指南深读 第五轮】守卫：支上=日贵人且乘贵人（月将贵人临年）→
                    #   无禄亦有中者（ZN-选举-四"课名虽为无禄，但亦有中者…月将贵人临年"——
                    #   己巳日支上子=己贵乘贵人）
                    if zhi_shang in gui_zhi_set and _zhi_shang_tj == '贵人':
                        return self._mk('无禄有中', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                        f'无禄课而支上{zhi_shang}为日贵人乘贵人，月将贵人临年，无禄亦有中者',
                                        'ZN-选举-四"课名虽为无禄，但亦有中者…月将贵人临年"')
                    return self._mk('无禄难食', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'四课上神俱克下，无禄课，虽受官职必不能食禄',
                                    '§前程仕进03·076"无禄课虽受通判必不能食禄"')
            # ① 官星临身+初传应之=催官符（§072"官星临日初传应之谓之催官符"）→ 得官
            #   【指南深读 第四轮】守卫：末传=长生（结局转生）→ 不判先成后败
            #   （ZN-选举-二"院试必取……驿马坐墓……静象也"——丙戌日末传寅=丙长生）
            if guan_lin_shen and _shi_shen(chu, ri_gan) == '官鬼':
                if (mo in kong or mo == mu_zhi or zhong in kong) and mo != cs_zhi:
                    return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'官星{gan_shang}临身初传应之，催官符赴任，然传中{"中传空丁忧" if zhong in kong else "末传" + mo + "空/墓"}，得官后不久即败',
                                    '§前程仕进03·072"官星临日初传应之谓之催官符"; §059"及第后死"')
                return self._mk('得官赴任', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{gan_shang}临身初传应之，催官符，主赴任得官',
                                '§前程仕进03·072"官星临日初传应之谓之催官符"')
            # ①b 官星临身（干上神=官星）→ 得官赴任；末传空/墓/凶将 或 中传空（父母丁忧）
            #   =先成后败（§072"及第后便丁父母服"、§059"及第后死"、§089"得十六月遭父丧"）
            #   【指南深读 第四轮】守卫：末传=长生 → 不判先成后败（结局转生，ZN-选举-二）
            if guan_lin_shen:
                _mo_bad = mo in kong or mo == mu_zhi or mo_shi == '凶'
                _zhong_bad = zhong in kong  # 中传空=父母空=丁忧（§072"中传父母空亡主丁忧"）
                if (_mo_bad or _zhong_bad) and mo != cs_zhi:
                    return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'官星{gan_shang}临身主得官，然{"中传空亡主丁忧" if _zhong_bad else "末传" + mo + ("空" if mo in kong else "墓" if mo == mu_zhi else "凶")}，得官后不久即败',
                                    '§前程仕进03·072"及第后便丁父母服"; §059"及第后死"')
                return self._mk('得官赴任', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{gan_shang}临身，主得官赴任',
                                '§前程仕进03·089"日上官星作贵"')
            # ②a 【指南深读 第五轮】官星发用 + 干支阴神（课2/课4上神）克官星 → 官受制凶
            #   （ZN-仕宦-二十三"忌日之阴阳制官，须防陈王田姓人为祟"——丁巳日初传亥=官鬼，
            #   干阴丑土克亥水，官受制而迁擢随罢）
            if guan_xing_fa_yong and sike and len(sike) >= 4 and chu_wx:
                _yin_ke_guan = False
                for _k in (sike[1], sike[3]):
                    _ys = str(_k[1]) if isinstance(_k, (list, tuple)) and len(_k) > 1 else str(_k.get('上神', ''))
                    if _ys and KE.get(ZHI_WX.get(_ys, '')) == chu_wx:
                        _yin_ke_guan = True
                        break
                if _yin_ke_guan:
                    return self._mk('阴阳制官', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'官星{chu}发用而干支阴神克官，官受制于人，迁擢随罢，须防人祟',
                                    'ZN-仕宦-二十三"忌日之阴阳制官，须防陈王田姓人为祟"')
            # ② 官星发用 + 得地 → 得官升迁（原有；加禄临干强化）
            #   【指南深读 2026-08-18】守卫：末传=日墓 → 不判升迁吉，落"功名难久"凶
            #   （ZN-仕宦-五"干支乘墓，禄马空陷……不能久任"）
            #   【指南深读 第四轮】守卫：初传=驿马且马临五行墓（日马坐墓库）→ 不判升迁吉
            #   （ZN-仕宦-十六"日马坐墓库，禄神临绝地，传将逆行……不能迁"——丁酉日初传亥=马，
            #   亥加辰水墓）
            _MA4 = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
                    '巳': '亥', '酉': '亥', '丑': '亥', '亥': '巳', '卯': '巳', '未': '巳'}
            _WX_MU4 = {'水': '辰', '木': '未', '火': '戌', '金': '丑'}
            _ma4 = _MA4.get(ri_zhi, '')
            _chu_xia = ''
            if sike:
                for _k in sike:
                    if isinstance(_k, (list, tuple)) and len(_k) > 2 and str(_k[1]) == chu:
                        _chu_xia = str(_k[2])
                        break
                    if isinstance(_k, dict) and str(_k.get('上神', '')) == chu:
                        _chu_xia = str(_k.get('下神', ''))
                        break
            _ma_mu = _WX_MU4.get(ZHI_WX.get(_ma4, ''), '')
            if guan_xing_fa_yong and chu_shi != '凶' and chu not in kong and mo != mu_zhi and \
                    not (_ma4 and chu == _ma4 and _ma_mu and _chu_xia == _ma_mu):
                return self._mk('得官升迁', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{chu}发用，官星得地，求官有望，升迁在望',
                                'L求官用起官星; CASE-壬占汇选-0117/0287')
            if guan_xing_fa_yong and _ma4 and chu == _ma4 and _ma_mu and _chu_xia == _ma_mu:
                return self._mk('日马坐墓', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{chu}发用而{chu}为驿马{_ma4}，马坐墓库（{_chu_xia}），禄马空陷，传将逆行，不能迁转',
                                'ZN-仕宦-十六"日马坐墓库，禄神临绝地，传将逆行…不能迁"')
            # ②b 禄临支（权摄不正禄临支）→ 正任不可望但食禄（§058"戊禄临支…正任不可望却乃食禄"；
            #   §069/097邵公"权摄不正禄临支"）
            if lu_zhi and zhi_shang == lu_zhi:
                return self._mk('权摄食禄', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'禄神{lu_zhi}临支，权摄不正禄临支，正任不可望，却乃食禄',
                                '§前程仕进03·058"权摄不正禄临支"; §069/097')
            # ③ 禄临干（随身禄）→ 得禄有官（§044"午乃丁禄临干日禄扶身"）
            if lu_lin_gan and not lu_kong:
                return self._mk('得禄有官', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'禄神{gan_shang}临干，随身禄扶身，得官食禄',
                                '§前程仕进03·044"午乃丁禄临干日禄扶身"')
            # ④ 禄空 → 虚禄难食（§055"将仕之禄乃虚禄…禄空不可为武"、§076"末又是禄乘空亡入墓"）
            #   【BUG-FIX 2026-08-18】§055 禄空但末传巳=官星长生学堂→弃武从文得科甲吉
            #   （"末巳作朱雀一为长生双为官星学堂故主科甲"）——守卫：末传=长生学堂且为官星→改文吉
            if lu_kong:
                _mo_xuetang = (mo == cs_zhi and _shi_shen(mo, ri_gan) in ('官鬼', '父母'))
                # 【指南深读 第二轮】守卫：三传两两递克（初克中、中克末）→ 不判弃武从文
                #   （ZN-仕宦-十四"三传递克是大凶之象"——巳申寅两两相克仍断大凶）
                _di_ke2 = bool(chu_wx and zhong_wx and mo_wx and
                               KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx)
                if _mo_xuetang and not _di_ke2:
                    return self._mk('弃武从文', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'禄神{lu_zhi}空亡不可为武，然末传{mo}为官星长生学堂，宜弃武从文，取科甲',
                                    '§前程仕进03·055"禄空故不可为武…末巳作朱雀一为长生双为官星学堂故主科甲"')
                return self._mk('虚禄难食', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'禄神{lu_zhi}空亡，虚禄也，得官不能食禄',
                                '§前程仕进03·055"将仕之禄乃虚禄"; §076"末又是禄乘空亡入墓"')
            # ⑤ 贵空 → 虚贵无位（§060"贵人又乘空乃是虚贵"、§103"昼贵人空虚是贵而无位也"）
            #   【BUG-FIX 2026-08-18】CASE-0162"禄马如此且乘天后恩泽青龙吉将相并安得不中"——
            #   贵人空但三传青龙/六合/天后吉将时仍可中，虚贵守卫：传中有青龙/六合/天后吉将不判凶
            if gui_kong:
                _ji_jiang_in_sc = any(t in ('青龙', '六合', '天后', '太常') for t in (chu_tj, zhong_tj, mo_tj))
                if _ji_jiang_in_sc:
                    return self._mk('贵空有救', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上贵人{gan_shang}空亡，然三传乘吉将（青龙/六合/天后），贵空有救，功名仍可图',
                                    'CASE-壬占汇选-0162"禄马如此且乘天后恩泽青龙吉将相并安得不中"')
                # 【指南深读 第二轮】贵空但初传生日干（印绶发用）→ 起官有期吉
                #   （ZN-仕宦-二十七"虎马丁神发用，作岁君生日，四墓覆生，已废复兴之象起官何疑"）
                #   【指南深读 第三轮】守卫：初传乘白虎（虎发用）→ 不判起官——ZN-仕宦-二十六
                #   （己未日酉将辰时初巳乘白虎）"月建虎马发用…贵临空害，居官难以久任"凶
                if chu_wx and SHENG.get(chu_wx) == gw and chu_tj != '白虎':
                    return self._mk('起官有期', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上贵人{gan_shang}空亡，然初传{chu}生日干，印绶发用作岁君生日，已废复兴，起官有期',
                                    'ZN-仕宦-二十七"虎马丁神发用，作岁君生日，四墓覆生，已废复兴之象起官何疑"')
                return self._mk('虚贵无位', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上贵人{gan_shang}空亡，贵而无位，求贵无门',
                                '§前程仕进03·060"贵人又乘空乃是虚贵"; §103"昼贵人空虚是贵而无位也"')
            # ⑥ 干支皆墓 → 前程迟滞（§064"干支皆墓主前程迟滞"）
            if gan_zhi_jie_mu:
                return self._mk('前程迟滞', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支上神皆乘墓（干{gan_shang}支{zhi_shang}），前程迟滞，凡事不通',
                                '§前程仕进03·064"干支皆墓主前程迟滞"')
            # ⑦ 干支自刑 → 自满失宠（§057"干支自刑主自满"）
            if zi_xing:
                return self._mk('自满失宠', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支自刑（干{gan_shang}支{zhi_shang}），主自满骄傲，因宠生祸失官',
                                '§前程仕进03·057"干支自刑主自满"')
            # ⑧ 满局贵人 → 贵多不贵（§053"满局皆贵人贵多不贵慕十不得一"）
            if gui_duo_bad:
                return self._mk('贵多不贵', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'课传满地贵人（{gui_duo}处，{gui_kong_cnt}处空亡），贵多不贵，慕十不得一，无贵可依',
                                '§前程仕进03·053"满局皆贵人贵多不贵慕十不得一"')
            # ⑨ 三传皆子孙（脱气）→ 诗书荒废（§046"脱上逢脱必诗书荒废"、§093"叠叠脱气"）
            if zi_sun_all:
                return self._mk('脱气荒废', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}皆子孙脱气，脱上逢脱，诗书荒废，功名难成',
                                '§前程仕进03·046"脱上逢脱必诗书荒废"; §093"一火生四土叠叠脱气"')
            # ⑩ 四绝课 → 偃蹇不通（§066"此课名四绝…前程非惟不远且又寿夭"）
            #   【指南深读 2026-08-18】守卫：末传=日禄不空（德禄入末）→ 不判四绝——
            #   ZN-选举-一"末传德禄驿马，干支交车生合……必中高魁"（四绝而末禄仍吉）
            if si_jue and not (lu_zhi and mo == lu_zhi and mo not in kong):
                return self._mk('四绝不通', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支上神{gan_shang}·{zhi_shang}四绝，偃蹇不通，前程非惟不远且又寿夭',
                                '§前程仕进03·066"此课名四绝且干支自刑"; §083"四绝偃蹇不通"')
            # ⑫ 铸印格+模空/破 → 虚名（§049"戌为模范亦落空地"、§050"朱雀投戌墓破模"、
            #   §078"初末夹定日墓引从不起"）
            #   模=戌（铸印格中戌为模）；戌空亡或受克（传中）→ 铸印损模虚名
            if zhu_yin:
                _mo_kong = '戌' in kong or (mo in kong)
                _mo_ke = any(KE.get(ZHI_WX.get(z, '')) == '土' for z in (chu, zhong, mo) if z != '戌')
                if _mo_kong or _mo_ke:
                    return self._mk('铸印损模', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'铸印格而模（戌）{"空亡" if _mo_kong else "受克"}，铸印损模，虚名无实',
                                    '§前程仕进03·049"戌为模范亦落空地"; §050"朱雀投戌墓破模"; §078"引从不起"')
            # ⑬ 羊刃在传/干支 → 升迁受阻（§051"干支皆天罗羊刃"、§054"午为阳刃撞干进锐退速"）
            #   【指南深读 第二轮 回滚】保持"羊刃单个临干支亦判凶"——§047/§051 邵公原断
            #   （"午为阳刃撞干…阻父丧"）；ZN-武举-一/仕宦-十三 羊刃误伤属邵公/陈公献体系
            #   冲突，以已深读的疏正（邵公）体系为准保留凶断。
            if yang_ren and (yang_ren in (chu, zhong, mo) or yang_ren in (gan_shang, zhi_shang)):
                return self._mk('羊刃阻迁', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'羊刃{yang_ren}临课传，升迁受阻，进锐退速',
                                '§前程仕进03·051"干支皆天罗羊刃"; §054"午为阳刃撞干进锐退速"')
            # ⑬c 【指南深读 第二轮】末传乘青龙（月将青龙）→ 片言入相，功名吉
            #   （ZN-仕宦-十"末传月将青龙片言入相"、ZN-仕宦-十三"喜末传月将青龙，是以将来可"）
            if mo_tj == '青龙':
                return self._mk('末龙入相', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}乘青龙（月将青龙），片言入相，功名有成',
                                'ZN-仕宦-十"末传月将青龙片言入相"; ZN-仕宦-十三"喜末传月将青龙"')
            # ⑬d 【指南深读 第三轮】末传=贵人且乘贵人 → 贵临末传，功名吉
            #   （ZN-仕宦-十八"贵德官星临年，月将青龙居丁…应未年高第"——末传亥=丁贵乘贵人）
            if mo in gui_zhi_set and mo_tj == '贵人':
                return self._mk('贵临末传', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日贵人又乘贵人，贵德临末，应期高第',
                                'ZN-仕宦-十八"贵德官星临年…应未年甲榜"')
            # ⑬b 幕贵临干（干上神=贵人且不空=科名第一吉神）→ 先晦后明登科
            #   （§052"太阴乘卯作幕贵加日干…先晦后明准拟登科"、§061"官星作幕贵今年必高中"；
            #   刘评"幕贵乃科名第一吉神"；守卫：传不空、非铸印破模——§050铸印破模凶不判吉）
            #   【指南深读 第二轮】守卫：干上神=日墓（幕贵即墓=干墓支绝）→ 不判吉
            #   （ZN-仕宦-十九"干墓支绝……必解任去"——干上未=甲之墓亦=幕贵）
            #   【指南深读 第三轮】守卫：八专课（自他处发用）→ 不判幕贵吉
            #   （ZN-仕宦-八"日比虎刃自他处发用……干支年命俱见罗网，恐不能也"）
            if gan_shang in gui_zhi_set and gan_shang not in kong and \
               not (chu in kong and zhong in kong) and gan_shang != mu_zhi and '八专' not in keti:
                if mo == cs_zhi or mo_shi == '吉':
                    return self._mk('先晦后明', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'幕贵{gan_shang}临干，科名第一吉神，先晦后明，准拟登科',
                                    '§前程仕进03·052"太阴乘卯作幕贵加日干先晦后明准拟登科"')
                return self._mk('幕贵临干', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'幕贵{gan_shang}临干，得贵助力，功名有望',
                                '§前程仕进03·052"幕贵乃科名第一吉神"')
            # ⑭ 官星落空亡 → 功名难成（原有）
            if chu in kong and _shi_shen(chu, ri_gan) == '官鬼':
                return self._mk('功名无成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{chu}空亡，功名落空，虽有机会亦难到手',
                                'CASE-壬占汇选-0112/0227/0291')
            if chu_tj == '朱雀' and _shi_shen(chu, ri_gan) == '官鬼' and chu in kong:
                return self._mk('场屋不利', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'朱雀乘官鬼{chu}又逢空亡，场屋不利，考试难中',
                                'CASE-壬占汇选-0177"帘幕克干朱雀遁丁神主场屋不利"')
            # 三传递生 → 有人提拔荐举（L98"三传递生皆主有人提拔荐举"；
            #   【BUG-FIX】闭口课递生"不能显荐"——案例0034"递生虽属举荐但是闭口不能显荐"）
            if di_sheng:
                if '闭口' in keti:
                    return self._mk('荐而难显', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'三传{chu}·{zhong}·{mo}递生有人举荐，然课逢闭口，不能显荐，功名难成',
                                    'CASE-壬占汇选-0034"递生虽属举荐但是闭口不能显荐"')
                return self._mk('荐举升迁', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}递生，有人荐举扶持，功名顺遂',
                                'L三传递生格; 案例0136"今年必高中"')
            # 三传递克 → 有人弹劾罢黜（L101"三传递克皆主有人弹劾必至罢黜"；
            #   【BUG-FIX】两两递克（初克中、中克末）亦大凶——陈公献0291
            #   "凡占仕，三传递克是大凶"（巳申寅两两相克，末传寅生日干仍断弹劾））
            if (di_ke or (chu_wx and zhong_wx and mo_wx and
                          KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx)):
                return self._mk('弹劾罢黜', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}递克，有人弹劾，位禄难保',
                                'L三传递克格; CASE-壬占汇选-0291"凡占仕三传递克是大凶"')
            # 三传俱空 → 功名无成（L387"三传俱空纵费尽心力到底无济"；
            #   案例0209"三传俱空，天将皆凶，大不美课，后果不中"）
            if chu in kong and zhong in kong and mo in kong:
                return self._mk('功名无成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}俱空亡，纵费尽心力到底无济，功名落空',
                                'L387"三传俱空纵费尽心力到底无济"; CASE-壬占汇选-0209')
            # 末传=日墓 → 居官不能久远（L114"干支各乘墓神主功名难于久远"）
            if mo == mu_zhi:
                return self._mk('功名难久', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，功名虽有亦难久远，终有败落',
                                'L干支各乘墓神主功名难于久远')
            # 自墓传生 → 自微至显（案例0458"自墓传生一则有寿二则自微至显"）
            #   【BUG-FIX】仅"初墓末生"触发；单末传长生不触发（案例0291末传长生仍弹劾，
            #   因初传空亡官星受制——见上"官星落空亡"分支）
            if chu == mu_zhi and mo == cs_zhi:
                return self._mk('先晦后明', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自墓({chu})传生({mo})，自微至显，功名终有发越',
                                'CASE-壬占汇选-0458"自墓传生自微至显"')

        # ───────────────────────────
        # 【疾病】
        # ───────────────────────────
        if category == '疾病':
            # 日干死地（§163"甲寅二木皆死于午"——木死午火死酉金死子水死卯土死卯）
            _SI_WX = {'木': '午', '火': '酉', '金': '子', '水': '卯', '土': '卯'}
            _si_zhi_d = _SI_WX.get(gw, '')
            # 白虎临干鬼（§164"白虎临干鬼乃旧太岁兼作病符"、§175"白虎乘午作鬼男病主三日内死"）
            _hu_lin_gan_gui = bool(gan_shang and _shi_shen(gan_shang, ri_gan) == '官鬼' and
                                   chu_tj == '白虎')
            # 四课上神皆脱日干（§166"此课大凶上下俱脱…其病恐是泄泻"）
            _shang_jie_tuo = bool(gan_shang and zhi_shang and
                                  SHENG.get(gw) == ZHI_WX.get(gan_shang, '') and
                                  SHENG.get(gw) == ZHI_WX.get(zhi_shang, ''))
            # 初传绝神+中末死地（§163"初传又是绝神…中末又是午…皆死于午"）
            _chu_jue_mo_si = bool(chu == jue_zhi and mo == _si_zhi_d)

            # ① 白虎临干鬼 → 病危速死（§175"白虎乘午作鬼男病主三日内死…虎乘干鬼凶速速"；
            #   §164"疾病之占首责白虎次及官鬼"）
            if _hu_lin_gan_gui:
                return self._mk('病危速死', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'白虎临干鬼{gan_shang}，虎乘干鬼凶速速，病危难救',
                                '§疾病13·175"白虎乘午作鬼男病主三日内死"; §164"首责白虎次及官鬼"')
            # ② 四课上神皆脱 → 上下俱脱大凶（§166"此课大凶上下俱脱…病恐是泄泻"）
            if _shang_jie_tuo:
                return self._mk('上下俱脱', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上{gan_shang}支上{zhi_shang}皆脱日干，上下俱脱，病由泄泻而起，凶',
                                '§疾病13·166"此课大凶上下俱脱其病恐是泄泻上得之"')
            # ③ 初传绝神+中末死地 → 病凶寿促（§163"初传又是绝神…中末又是午…皆死于午"）
            if _chu_jue_mo_si:
                return self._mk('病入死地', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}为日绝神，末传{mo}为日死地，病入死地，难治',
                                '§疾病13·163"初传又是绝神中末又是午皆死于午"')
            # ③b 【指南深读 2026-08-18】末传=日干官鬼克日（非空亡）→ 病危难救
            #   （ZN-疾病-七"末传巳火克日，故以日决之……必死"；L540"白虎克日病必凶"——
            #   末传官鬼克日与虎鬼同论；守卫：末传空亡则虎鬼空亡病自愈 L546；
            #   循环格主病多反复（L557），不判速死——CASE-0151）
            if mo_wx and KE.get(mo_wx) == gw and mo not in kong and not xun_huan:
                return self._mk('病危难救', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日干官鬼克日，鬼星临末定结局，病危难救',
                                'ZN-疾病-七"末传巳火克日，故以日决之"; L540"白虎克日病必凶"')
            # ④ 三传自墓传生 → 患易瘥（L544）
            if zi_mu_chuan_sheng:
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自墓({chu})传生({mo})，病虽重自墓传生，患易瘥，终可愈',
                                'L544"三传自墓传生患易瘥"')
            # ⑤ 三传自生传墓 → 难瘳（L544）
            if zi_sheng_chuan_mu:
                return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自生({chu})传墓({mo})，自生传墓，病难瘳，终凶',
                                'L544"自生传墓者难瘳"')
            # ⑥ 白虎乘日鬼同入三传 → 大凶（L545；案例0412"此课不利占病丁巳日必死"）
            if hu_gui:
                return self._mk('病危难救', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'白虎乘日鬼入传，病势凶险，恐难救治',
                                'L545"虎乘日鬼同入三传主大凶"; CASE-壬占汇选-0412')
            # ⑦ 虎鬼空亡 → 病自愈（L546）
            if any(z in kong and _shi_shen(z, ri_gan) == '官鬼' and tj == '白虎'
                   for z, tj in ((chu, chu_tj), (zhong, zhong_tj), (mo, mo_tj))):
                return self._mk('有惊无险', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'虎鬼{chu if chu in kong else zhong if zhong in kong else mo}空亡，病自愈，有惊无险',
                                'L546"虎鬼空亡病自愈"')
            # ⑧ 白虎克日 → 病必凶（L540）
            if mo_tj == '白虎' and KE.get(mo_wx) == gw:
                return self._mk('病势凶险', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}白虎克日干，病势凶险，须防不测',
                                'L540"白虎克日病必凶"')
            # ⑨ 循环格 → 病多反复（L557"循环格三传不离四课主病多反复"；
            #   【BUG-FIX 2026-08-18】邵公断案§166"循环格…病恐是泄泻…死在二十八日"、
            #   §168"循环不断…久而不治必成痨怯"——疾病循环格=病缠身凶，非平）
            if xun_huan:
                return self._mk('病多反复', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}不离四课，循环格，病多反复，迁延难愈',
                                'L557"循环格主病多反复"; §疾病13·166"死在二十八日"; §168"久而不治必成痨怯"')
            # ⑩ 传归死墓必死（L617"传归死墓必死"）
            if mo == mu_zhi and (chu_shi == '凶' or zhong_shi == '凶'):
                return self._mk('病终难救', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，传归死墓，病终难救',
                                'L617"传归死墓必死"')
            # ⑪ 长生空亡=虚生 → 病难愈（§162"日上长生是空亡…终身瘦弱二十八岁不能过"）
            if gan_shang == cs_zhi and gan_shang in kong:
                return self._mk('虚生难愈', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上长生{gan_shang}空亡，虚生无力，病缠绵难愈',
                                '§疾病13·162"日上长生是空亡…终身瘦弱"')
            # ⑫ 病符临支/支上（旧太岁）→ 全家病（§169"病符克宅全家患…疫气入宅主合宅病"；
            #   判据简化：支上神=日干死地或墓）
            if zhi_shang and (zhi_shang == _si_zhi_d or zhi_shang == mu_zhi):
                return self._mk('病符入宅', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}为日死/墓地，病符入宅，主合宅病',
                                '§疾病13·169"病符克宅全家患…疫气入宅主合宅病"')
            # ⑬ 三交课（四正相加）→ 病由情欲（§173"三交中有空亡六合者皆不正之合…其患有三"；
            #   判据：三传含≥2四正 或 干支上神自刑）
            _SI_ZHENG_JB = {'子', '午', '卯', '酉'}
            _sj_cnt = sum(1 for z in (chu, zhong, mo) if z in _SI_ZHENG_JB)
            if _sj_cnt >= 2:
                return self._mk('三交情病', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}三交课，四正相加，病由情欲不正之合',
                                '§疾病13·173"三交中有空亡六合者皆不正之合其患有三"')
            # ⑭ 昴星课纯阴无阳气 → 病危（§178"昴星课纯阴之象阴掩其阳是无阳气也…阴阳气绝"；
            #   判据：课体含"昴星" 或 三传皆阴且末传=日墓）
            if '昴星' in keti or (chu in ('子', '丑', '卯', '巳', '未', '酉', '亥') and
                                   zhong in ('子', '丑', '卯', '巳', '未', '酉', '亥') and
                                   mo in ('子', '丑', '卯', '巳', '未', '酉', '亥')):
                return self._mk('阴阳气绝', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'昴星纯阴之象，阴掩其阳，无阳气，阴阳气绝，病危',
                                '§疾病13·178"昴星课纯阴之象…阴阳气绝者促也"')

        # ───────────────────────────
        # 【官讼】
        # ───────────────────────────
        if category == '官讼':
            # 【邵公断案·官讼章深读 2026-08-18】核心：
            #   §202"贵人差迭事参差…不宜讼必主断理不明"——昼夜贵加为贵人差迭
            #   §203"一旬周遍格…惟讼要散不要关锁"——周遍格讼难散
            #   §204"顾祖课主原有讼根…天网课兜罗难脱"——讼有源头再发
            #   §207"独足课…必配本州"——独足课流配
            #   §211"乱首死奇…恐死不完尸"——乱首大凶
            # 贵人表（旦贵/暮贵）
            _GUI_REN_GS = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'},
                           '戊': {'丑', '未'}, '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'},
                           '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
            _gui_set_gs = _GUI_REN_GS.get(ri_gan, set())
            # 贵人差迭：干上神=贵人且官鬼、支上神=另一贵人（§202"昼贵在夜夜贵在昼"）
            _gui_zao_die = bool(gan_shang and zhi_shang and
                                gan_shang in _gui_set_gs and zhi_shang in _gui_set_gs and
                                _shi_shen(gan_shang, ri_gan) == '官鬼')
            # 独足课：三传同支（§207"三传酉酉酉…独足不行也必配"）
            _du_zu = (chu == zhong == mo)
            # 乱首课：支加干克干 或 干加支受支克（§211"日加辰作勾…自取乱首"——
            #   壬辰日干上加辰受克；§202/211均乱首）
            _luan_shou = bool(
                (gan_shang == ri_zhi and ri_zhi and KE.get(ZHI_WX.get(ri_zhi, '')) == gw) or
                (zhi_shang == ri_gan and ri_gan and KE.get(ZHI_WX.get(ri_zhi, '')) == gw)
            )
            # 六阴相继不利公讼（§202"六阴相继之体不利公讼"——三传皆阴）
            _YIN_GS = {'子', '丑', '卯', '巳', '未', '酉', '亥'}
            _liu_yin = (chu in _YIN_GS and zhong in _YIN_GS and mo in _YIN_GS)
            # 一旬周遍格/循环格（§203"一旬周遍格…惟讼要散不要关锁"——传不离课讼难散）
            # 干加支受克（§211"日加辰作勾"——干临支而受支克，乱首）
            _luan_shou2 = bool(zhi_shang == ri_gan and ri_zhi and
                               KE.get(ZHI_WX.get(ri_zhi, '')) == gw)

            # ① 递生但传含墓/死/白虎 → 讼凶（§211"三传递生…乱首死奇恐死不完尸"——
            #   壬辰日午丑申递生，然末申作虎入墓，乱首大凶，递生非吉）
            if di_sheng and (mo == mu_zhi or mo_tj == '白虎' or '乱首' in keti):
                return self._mk('乱首讼凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}递生，然乱首死奇/末传{mo}虎入墓，官讼大凶',
                                '§官讼16·211"乱首死奇…恐死不完尸"')
            # ①b 六阴相继不利公讼（§202"六阴相继之体不利公讼…必主断理不明"；
            #   【BUG-FIX 2026-08-18】§209 三传亥卯未六阴但成曲直木局（"三传曲直应先曲后直，
            #   末有龙故无事"）先凶后吉——三合局且局生日干时有救；§205木局为辛之财局
            #   （"传财太盛反化鬼"）仍凶
            _SANHE_GS = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
            _SANHE_WX_GS = {'水': {'申', '子', '辰'}, '火': {'寅', '午', '戌'},
                            '金': {'巳', '酉', '丑'}, '木': {'亥', '卯', '未'}}
            _ju_gs = ''
            for _jw, _jz in _SANHE_WX_GS.items():
                if {chu, zhong, mo} == _jz:
                    _ju_gs = _jw
                    break
            # 局生日干=有救（§209曲直木局生乙木）或 局=日干同类比劫局（§209乙日亥卯未木局
            #   "三传曲直应先曲后直，末有龙故无事"亦吉）；局克日干（财局§205）仍凶
            _ju_jiu = bool(_ju_gs and gw and (SHENG.get(_ju_gs) == gw or _ju_gs == gw))
            # 三传含对冲（巳亥反复等）→ 讼有反复非纯凶（CASE-0186"以巳亥反复皆四数也"）
            _CHONG_GS = {'子': '午', '午': '子', '卯': '酉', '酉': '卯',
                         '寅': '申', '申': '寅', '巳': '亥', '亥': '巳',
                         '丑': '未', '未': '丑', '辰': '戌', '戌': '辰'}
            _you_chong = bool(
                (chu and _CHONG_GS.get(chu) == zhong) or
                (chu and _CHONG_GS.get(chu) == mo) or
                (zhong and _CHONG_GS.get(zhong) == mo)
            )
            if _liu_yin and not _ju_jiu and not _you_chong:
                return self._mk('六阴讼晦', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}六阴相继，不利公讼，断理不明',
                                '§官讼16·202"六阴相继之体不利公讼"')
            # ①c 一旬周遍格/循环格（§203"一旬周遍格…惟讼要散不要关锁"——传不离课讼难散；
            #   【BUG-FIX 2026-08-18】§209 循环格+曲直局生身=先凶后吉，不判凶）
            if xun_huan and not _ju_jiu:
                return self._mk('周遍讼缠', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}不离四课，一旬周遍格，讼要散不要关锁，讼事缠绵',
                                '§官讼16·203"一旬周遍格…惟讼要散不要关锁"')
            # ①d 三合局（曲直/炎上等）→ 先曲后直，先凶后吉（§209"三传曲直应先曲后直，
            #   末有龙故无事"——乙未日亥卯未木局，邵公断"一出头便被枷锢后却无事"吉）
            if _ju_gs and _ju_jiu:
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}成{_ju_gs}局，先曲后直，虽先遭枷锢，终得无事',
                                '§官讼16·209"三传曲直应先曲后直，末有龙故无事"')
            # ① 贵人差迭 → 不宜讼，断理不明（§202"贵人差迭事参差…不宜讼必主断理不明"）
            if _gui_zao_die:
                return self._mk('贵人差迭', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上{gan_shang}支上{zhi_shang}贵人差迭，不宜讼，必主断理不明',
                                '§官讼16·202"贵人差迭事参差…不宜讼必主断理不明"')
            # ② 独足课 → 流配（§207"独足不行也…必配本州"）
            if _du_zu:
                return self._mk('独足流配', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}独足课，独足不行，官事主流配',
                                '§官讼16·207"独足不行也…必配本州"')
            # ③ 乱首课 → 大凶（§211"乱首死奇…恐死不完尸"）
            if _luan_shou:
                return self._mk('乱首大凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支{ri_zhi}加干克干，乱首死奇，官讼大凶，恐死不完尸',
                                '§官讼16·211"乱首死奇…其凶不可言恐死不完尸"')
            # ④ 末传生初传生日干 → 有人暗地用力扶持，官事不日消缴（L780）
            if mo_wx and chu_wx and SHENG.get(mo_wx) == chu_wx and SHENG.get(chu_wx) == gw:
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}生初传{chu}生日干，暗地有人用力扶持，官事不日消缴',
                                'L780"末传生初传而生日干者主有人暗地用力扶持官事不日消缴"')
            # ⑤ 初传白虎末传螣蛇 → 虎头蛇尾虽有祸乱渐消释（L790；案例0520"先凶后吉"）
            if chu_tj == '白虎' and mo_tj == '螣蛇':
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}白虎末传{mo}螣蛇，虎头蛇尾，虽有祸乱渐消释，官事先凶后吉',
                                'L790"若白虎作初传螣蛇作末传凡事虎头蛇尾虽有祸乱渐消释"; CASE-壬占汇选-0520')
            # ⑥ 初传官鬼旺相 → 讼必成；休囚 → 讼不成（L819"初传官鬼旺相讼必成休囚讼不成"）
            if _shi_shen(chu, ri_gan) == '官鬼':
                if chu not in kong and chu_shi != '凶':
                    return self._mk('讼事必成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'初传官鬼{chu}旺相，讼必成，我方不利',
                                    'L819"初传官鬼旺相讼必成"')
                return self._mk('讼可消散', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传官鬼{chu}休囚，讼不成，可消散',
                                'L819"官鬼休囚讼不成"')
            # ⑦ 干上神克支上神 → 先起者胜（L740；初传空亡或伏吟课例外——静局不讼）
            if gan_ke_zhi_shang and chu not in kong and not fu_yin:
                return self._mk('先起者胜', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}克支上神{zhi_shang}，先起者胜，理直气壮',
                                'L740"干上神刑克冲害支上神者先起者胜"')
            # ⑧ 支上神克干上神 → 后应者胜（L742）
            if zhi_ke_gan_shang and chu not in kong and not fu_yin:
                return self._mk('后应者胜', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}克干上神{gan_shang}，后应者胜，我方不利',
                                'L742"支上神刑克冲害干上神者后应者胜"')
            # ⑨ 末传=天喜/青龙乘解神 → 恩赦相救先凶后吉（案例0520/§212"末天喜乘龙作解神"）
            if mo_tj in ('青龙', '太常', '贵人') and mo_shi == '吉':
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}乘{mo_tj}，恩赦相救，先凶后吉，官事可解',
                                'CASE-壬占汇选-0520"末天喜乘龙作解神必有恩赦相救先凶而后吉"')
            # ⑩ 【指南深读 第二轮】干上神=日干长生（长生临身）→ 恩宥转凶为吉
            #   （ZN-占讼-二/六"长生临身，天赦加支……罪虽重亦转凶为吉"——乙未日干上亥=乙长生）
            if gan_shang == cs_zhi:
                return self._mk('恩宥转吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}为日干长生，长生临身，天赦加支，罪虽至重亦能转凶为吉',
                                'ZN-占讼-六"长生临身…遇赦转凶为吉"')
            # ⑪ 【神煞占类化 2026-08-18】天赦临干支 → 恩赦相救转凶为吉
            #   （ZN-占讼-二"支见天赦（春三月天赦在寅）……罪虽至重亦能转凶为吉"）
            #   守卫：螣蛇/白虎在传（蛇虎墓门，冢墓门开）→ 不判恩宥——ZN-占讼-十九
            #   "占讼最凶全无救解……蛇虎二墓加临卯酉，此为冢墓门开"
            if _ss_ts and (_ss_ts == gan_shang or _ss_ts == zhi_shang) and \
                    '螣蛇' not in (chu_tj, zhong_tj, mo_tj) and '白虎' not in (chu_tj, zhong_tj, mo_tj):
                return self._mk('天赦恩宥', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'天赦{_ss_ts}临干支，天赦加支，罪虽至重亦能转凶为吉',
                                'ZN-占讼-二"天赦居支…转凶为吉"')
            # ⑫ 【太岁占类化 2026-08-18】官讼：太岁临干生日干 → 太岁相救转吉；太岁克日干
            #   → 君上不喜（ZN-占讼-二"太岁贵人生日，罪虽至重亦能转凶为吉"；ZN-占讼-二十一
            #   "太岁克日，君上不喜，须得木姓人求解方可释荷"）——限官讼（朝廷事），
            #   仅当 year 提供时生效
            if _ss_tsui:
                _ts_wx_gs = ZHI_WX.get(_ss_tsui, '')
                if gan_shang == _ss_tsui and _ts_wx_gs and SHENG.get(_ts_wx_gs) == gw:
                    return self._mk('太岁相救', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'太岁{_ss_tsui}临干生日干，太岁贵人生日，罪虽至重亦能转凶为吉',
                                    'ZN-占讼-二"太岁贵人生日…转凶为吉"')
                if _ts_wx_gs and KE.get(_ts_wx_gs) == gw:
                    return self._mk('太岁克日', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'太岁{_ss_tsui}克日干，君上不喜，须得木姓人求解方可释荷',
                                    'ZN-占讼-二十一"太岁克日，君上不喜"')

        # ───────────────────────────
        # 【求财】
        # ───────────────────────────
        if category == '求财':
            # 【邵公断案·财产章深读 2026-08-18】核心：
            #   §134"求财视财爻乃通法常理"；§132"传财化鬼财休觅…传财太旺反财亏"；
            #   §133"独足无足不利陆行，若船行加倍得利"；§135"末传逢禄逢旺诸事遂意尽在末"；
            #   §136"干支上皆盗气…人宅受脱俱遭盗"；§137"日上见贵财支上见财库此大利"；
            #   §141"传鬼化财…必主喜兆"；§142"反复争夺之财甚薄"（返吟）；§148"皆阴岂宜进干"
            # ① 干上神=财爻 且 支上神=日墓（财库）→ 财归财库，得财大利（§137"日上见贵财，
            #   支上见财库，日上财神又归财库，此大利"）
            if gan_shang and zhi_shang and zhi_shang == mu_zhi and _shi_shen(gan_shang, ri_gan) == '妻财':
                return self._mk('财入库吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}为财，支上神{zhi_shang}为日墓财库，日上财神归财库，得财大利',
                                '§财产08·137"日上见贵财，支上见财库，日上财神又归财库，此大利"')
            # ② 传财化鬼 → 因财致祸（L274/L287"传财化鬼难求觅，因财致祸"；§132/137实证）
            if _shi_shen(chu, ri_gan) == '妻财' and KE.get(mo_wx) == gw:
                return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传财{chu}末传鬼{mo}，传财化鬼，因财致祸，得而复失',
                                'L274"传财化鬼难求觅"; §财产08·132"传财化鬼财休觅"')
            # ③ 三传皆鬼 + 干上神=财爻 → 传鬼化财，先难后易终吉（§141"三传虽鬼，只是少阻
            #   无妨…必主喜兆，非鬼兆也"；L"传鬼化财钱险危"——有财可化则险中取财）
            if mo_wx and chu_wx and zhong_wx and gw and \
                    KE.get(chu_wx) == gw and KE.get(zhong_wx) == gw and KE.get(mo_wx) == gw and \
                    gan_shang and _shi_shen(gan_shang, ri_gan) == '妻财':
                return self._mk('传鬼化财', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}皆鬼，然干上神{gan_shang}为财可化，先难后易，必主喜兆',
                                '§财产08·141"三传虽鬼，只是少阻无妨…必主喜兆，非鬼兆也"')
            # ④ 三传皆财（财局太旺）→ 传财太旺反财亏（§132"三传全财化为鬼…传财太旺反财亏"；
            #   L286"传财太旺反财亏"）
            _cai_cnt = sum(1 for z in (chu, zhong, mo) if _shi_shen(z, ri_gan) == '妻财')
            if _cai_cnt >= 2:
                return self._mk('财旺反亏', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}财爻太旺，传财太旺反财亏，财多伤身',
                                '§财产08·132"传财太旺反财亏"; L286')
            # ⑤ 独足课（三传同支）→ 利舟行不利陆行（§133"独足无足不利陆行，若船行加倍得利"）
            if chu == zhong == mo:
                return self._mk('独足利舟', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}独足课，独足无足不利陆行，若船行加倍得利',
                                '§财产08·133"独足无足不利陆行，若船行加倍得利"')
            # ⑥ 干支上皆盗气（干支互脱）→ 人宅受脱俱遭盗（§136"干支上皆盗气其家世店业十退五六"；
            #   L"人宅受脱俱遭盗"）
            if gan_shang and zhi_shang:
                _gan_tuo = SHENG.get(gw) == ZHI_WX.get(gan_shang, '')
                _zhi_tuo = SHENG.get(ZHI_WX.get(ri_zhi, '')) == ZHI_WX.get(zhi_shang, '')
                if _gan_tuo and _zhi_tuo:
                    return self._mk('人宅受脱', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上{gan_shang}支上{zhi_shang}皆盗气，人宅受脱俱遭盗，店业退败',
                                    '§财产08·136"干支上皆盗气其家世店业十退五六矣"')
            # ⑦ 返吟+财薄 → 反复争夺之财甚薄（§142"此乃反复争夺之财甚薄"；§139返吟讨息；
            #   返吟课体优先于传内细节——§142末传禄神亦不作吉断）
            if fan_yin:
                return self._mk('返吟薄财', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'返吟课反复争夺之财，财甚薄，得而复失',
                                '§财产08·142"此乃反复争夺之财甚薄"; §139"返吟始可将本求利"')
            # ⑧ 末传=禄神/旺相 → 末传逢禄逢旺诸事遂意尽在末（§135"末传逢禄逢旺诸事遂意尽在末"；
            #   优先于三传皆阴——§135三传皆阴而末禄，邵公仍断"尽在末也"）
            if lu_zhi and mo == lu_zhi:
                return self._mk('末禄遂意', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日禄，末传逢禄逢旺，诸事遂意，尽在末也',
                                '§财产08·135"末传逢禄逢旺诸事遂意尽在末"')
            # ⑨ 三传皆阴（阴课）→ 宜静不宜动，谋新不利（§148"三四课皆阴，岂宜进干"；
            #   刘评引《毕法》"六阴相继尽昏迷"）
            if chu in ('丑', '卯', '巳', '未', '酉', '亥') and \
                    zhong in ('丑', '卯', '巳', '未', '酉', '亥') and \
                    mo in ('丑', '卯', '巳', '未', '酉', '亥'):
                return self._mk('宜静谋旧', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}皆阴，宜静不宜动，谋新进干不利，自宜用旧',
                                '§交易谋为10·148"三传四课皆阴岂宜进干…自宜用旧，未利谋新"')
            # ⑩ 三传初中皆空独末为财爻 → 先难后得（L283）
            if chu in kong and zhong in kong and _shi_shen(mo, ri_gan) == '妻财':
                return self._mk('先难后易', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初中传空亡，末传{mo}为财爻，先涉艰难然后得财',
                                'L283"三传初中皆空独末为财爻先难后得"')
            # ⑪ 初传财末传生之 → 末来助始（L282）
            if _shi_shen(chu, ri_gan) == '妻财' and mo_wx and SHENG.get(mo_wx) == chu_wx:
                return self._mk('得财有望', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传财{chu}，末传{mo}生之，末来助始，有人暗将财相助',
                                'L282"初传财末传生之末来助始"')
            # ⑫ 财爻临日干 → 得财甚速；财在末传 → 得财迟滞（L270）
            if _shi_shen(mo, ri_gan) == '妻财' and mo_shi == '吉':
                return self._mk('终得财利', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为财爻得地，得财虽迟终有财利',
                                'L270"财在末传得财迟滞"')
            # ⑬ 财爻空亡（三传或支上）→ 不可强求（L275"财坐空亡不可强求"；
            #   §134"午财旬空故未得"——支上财空亦主先未得）
            _cai_kong = any(z in kong and _shi_shen(z, ri_gan) == '妻财' for z in (chu, zhong, mo))
            if not _cai_kong and zhi_shang and zhi_shang in kong and _shi_shen(zhi_shang, ri_gan) == '妻财':
                _cai_kong = True
            if _cai_kong:
                return self._mk('求财落空', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'财爻{chu if chu in kong and _shi_shen(chu, ri_gan) == "妻财" else zhi_shang if zhi_shang in kong else zhong}空亡，求财落空，不可强求',
                                'L275"财坐空亡不可强求"; §财产08·134"午财旬空故未得"')

        # ───────────────────────────
        # 【家宅】（邵公断案·宅墓章深读增强 2026-08-18）
        # 层次（刘科乐评疏归纳）：先课体课格（乱首/天狱/六阴/回环），
        #   次干支关系（谁加谁/谁墓谁/谁脱谁），后三传结构（递生克/脱泄/旺传死绝）。
        # 所有规则均有邵彦和断语原文 + 刘科乐评疏出处。
        # ───────────────────────────
        if category == '家宅':
            _YIN_ZHI = {'子', '丑', '卯', '巳', '未', '酉', '亥'}
            # 五行死地 / 羊刃 / 败地（邵公断宅常用）
            WX_SI = {'木': '午', '火': '酉', '金': '子', '水': '卯', '土': '卯'}
            WX_BAI = {'木': '子', '火': '卯', '金': '午', '水': '酉', '土': '酉'}
            YANG_REN = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
            si_zhi = WX_SI.get(gw, '')
            bai_zhi = WX_BAI.get(gw, '')
            yang_ren_zhi = YANG_REN.get(ri_gan, '')
            # 日干寄宫（自刑判定用：壬寄亥、乙寄辰、辛寄戌、丁寄未/巳、己寄未/巳…）
            GAN_JI_GONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
                           '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}
            ji_gong = GAN_JI_GONG.get(ri_gan, '')
            ZI_XING = {'辰', '午', '酉', '亥'}
            # 三合局：三传成局（申子辰水/寅午戌火/巳酉丑金/亥卯未木）
            SAN_HE = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
            sanchuan_set = {chu, zhong, mo}
            ju_wx = ''
            for jz, jwx in zip(SAN_HE, ['水', '火', '金', '木']):
                if sanchuan_set == jz:
                    ju_wx = jwx
                    break

            # ══════════════════════════════════════════════════════════
            # 【阴宅】（占坟地/风水，邵公"占阴地总以辰为坟茔穴口"§040刘评）
            # 阴宅专看：辰为坟茔穴口、初传主山穴、朱雀论朝案、龙砂水向。
            # ══════════════════════════════════════════════════════════
            if zishu == '阴宅':
                # ① 辰为坟茔穴口（§040刘评"占阴地总以辰为坟茔穴口"）；穴口空亡=虚穴
                #    → 先难后易（§041/CASE-0348"辰为坟地作空亡而发用故主有空穴…填实后必出贵人"）
                if chu == '辰' and chu in kong:
                    return self._mk('先难后易', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'初传辰为坟茔穴口而空亡，主有空穴虚坟，须填实之后方可安葬，先难后易，葬后发贵',
                                    '§宅墓02·041"辰为坟地作空亡而发用故主有空穴"; CASE-壬占汇选-0348"填实后必出贵人"')
                # ② 干为人、支为地（CASE-0465"夫占风水以支为地干为人"）；干上长生=吉地
                #    （CASE-0465"干乘长生六合…其平稳之地可知也"——邵公首判吉地，优先于凶将判）
                if gan_shang == cs_zhi:
                    return self._mk('风水吉地', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上神{gan_shang}为日干长生，干为人得生，风水不碍，平稳之地',
                                    'CASE-壬占汇选-0465"干乘长生六合…风水不碍"')
                # ③ 初传主山穴（§040"以初传为主山穴"）；白虎临传=两重白虎穴凶
                #    → 阴宅不吉（§040"艮山行龙坎山落穴不是正龙…有两重白虎…白蚁食尸"）
                if chu_tj == '白虎' or zhong_tj == '白虎':
                    return self._mk('阴宅不吉', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'白虎临穴（{chu if chu_tj=="白虎" else zhong}乘白虎），龙虎不真，两重白虎，阴宅不吉，主子孙耗败',
                                    '§宅墓02·040"有两重白虎第三重为案…主子孙贪淫好酒"')
                # ④ 朱雀论朝案（§041"卜地以朱雀为论朝案"）；朱雀乘贵人/生主山=文笔峰
                if chu_tj == '朱雀' or mo_tj == '朱雀':
                    return self._mk('朝案有情', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'朱雀论朝案，峰峦秀丽文星得用，有文笔双峰之奇，葬后出贵人',
                                    '§宅墓02·041"卜地以朱雀为论朝案…文笔双峰"')
                # ⑤ 支上神克干/墓 → 阴宅不利（CASE-0465"支见纯土风水不碍"反用：支上克干为碍）
                if zhi_shang and KE.get(ZHI_WX.get(zhi_shang, '')) == gw:
                    return self._mk('阴宅克人', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'支上神{zhi_shang}克日干，地不载人，阴宅不利，葬后损人',
                                    'CASE-壬占汇选-0465"以支为地干为人"（反用：支上克干为碍）')

            # ══════════════════════════════════════════════════════════
            # 【迁移】（占迁居/移宅/修造）
            # 迁移看丁马动象：凶课遇迁移可解（§014"迁店居住其户遂宁"）、
            # 人广宅狭宜分迁（§017"若移出各人自为活计"）、支空求新宅（§010）。
            # ══════════════════════════════════════════════════════════
            if zishu == '迁移':
                # ① 凶课（干支互脱/六阴/墓/空）→ 迁移可解，先凶后吉（§014"德丧神消人亡家破…迁店居住其户遂宁而祸亦解"；
                #    §035"急移可免"；§043"若不肯迁移必主十二年而死，次年即迁居"；§008"宅出怪住不得必别迁"）
                if (gan_shang == mu_zhi or (chu in kong and zhong in kong) or
                        (chu in _YIN_ZHI and zhong in _YIN_ZHI and mo in _YIN_ZHI) or
                        (chu in kong and mo in kong)):
                    return self._mk('宜迁避祸', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'课呈凶象（墓/空/六阴），旧宅不可安居，迁移可以避祸，宜速迁居，先凶后吉',
                                    '§宅墓02·014"迁店居住其户遂宁而祸亦解"; §宅墓02·035"急移可免"; §宅墓02·008"住不得必别迁"')
                # ② 人广宅狭（初传=支上神=宅上发用 或 三传脱支生日干）→ 宜分迁
                #    （§017"日往加辰是人广而宅狭也…宅居不得许多人…若移出各人自为活计"；
                #     §012"人盛宅狭人与宅替"）
                _zhi_wx = ZHI_WX.get(ri_zhi, '')
                _tuo_zhi_wx = SHENG.get(_zhi_wx, '') if _zhi_wx else ''
                _sheng_gan_wx = [w for w, v in SHENG.items() if v == gw]
                _ren_guang = (chu == zhi_shang) or (
                    _tuo_zhi_wx and mo_wx in (_tuo_zhi_wx,) and
                    any(w in {ZHI_WX.get(z) for z in (chu, zhong, mo)} for w in _sheng_gan_wx))
                if _ren_guang:
                    return self._mk('分迁为宜', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'人广宅狭（宅居不得许多人），宅上发用传日，宜移出分居，各人自为活计',
                                    '§宅墓02·017"日往加辰是人广而宅狭也…若移出各人自为活计"; §宅墓02·012"人盛宅狭"')
                # ③ 支上空亡 → 求新宅（§010"支上空亡是宅不可得而图也…求新宅看何方生旺即是"）
                if zhi_shang and zhi_shang in kong:
                    return self._mk('求新宅', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'支上神{zhi_shang}空亡，旧宅不可图，宜另求新宅，看何方生旺即是',
                                    '§宅墓02·010"支上空亡是宅不可得而图也…求新宅看何方生旺即是"')
                # ④ 课吉宅稳 → 不宜轻动（§031"只宜守分不宜运用，一运用便有艰辛"）
                if chu_shi == '吉' and mo_shi == '吉':
                    return self._mk('不宜轻动', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'课吉宅稳，只宜守分不宜运用，一运用便有艰辛',
                                    '§宅墓02·031"只宜守分不宜运用，一运用便有艰辛"')

            # 干支俱受生而互受脱 → 先兴旺而后衰败（CASE-0226；§004"庚生于巳寅生于亥，庚脱于亥寅脱于巳"）
            if gan_shang and zhi_shang:
                gan_cs = WX_CS.get(gw, '')
                zhi_cs = WX_CS.get(ZHI_WX.get(ri_zhi, ''), '')
                if gan_shang == gan_cs and zhi_shang == zhi_cs:
                    return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上神{gan_shang}为日干长生、支上神{zhi_shang}为日支长生，干支俱受生而互受脱，先兴旺而后衰败',
                                    'CASE-壬占汇选-0226; §宅墓02·004"干支俱受生而互受脱是先兴旺而后衰败"')
            # 支加干上为日墓 → 两蛇夹墓/真墓不可脱（§030"支来加日墓日，上又螣蛇夹住，主人如处云雾中进退不得"）
            if zhi_shang and ri_zhi and gan_shang == ri_zhi and ri_zhi == mu_zhi:
                return self._mk('宅墓交困', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支{ri_zhi}加干上为日墓，真墓不可脱，主人如处云雾中，进退不得',
                                '§宅墓02·030"支来加日墓日上又螣蛇夹住进退不得"')
            # 上门乱首：支来加干克干 → 不有大服必有大祸（§022"支来加干名上门乱首，不有大服必有大祸"；
            #   §043"支辰犯日乃下犯上"）
            if gan_shang == ri_zhi and ri_zhi and KE.get(ZHI_WX.get(ri_zhi, '')) == gw:
                return self._mk('上门乱首', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支{ri_zhi}加干上克日干，上门乱首，卑凌尊，下犯上，不有大服必有大祸',
                                '§宅墓02·022"支来加干名上门乱首不有大服必有大祸"')
            # 赘婿课：支来就干为干所制 → 家破屋拆（§005"此课支来就干为干所制名曰赘婿，六年中家破屋拆"）
            if gan_shang == ri_zhi and ri_zhi and KE.get(gw) == ZHI_WX.get(ri_zhi, ''):
                return self._mk('赘婿家破', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支{ri_zhi}来就干为干所制，名曰赘婿，身不由己，家破屋拆之象',
                                '§宅墓02·005"支来就干为干所制名曰赘婿，六年中家破屋拆"')
            # 干支各乘墓 → 身宅居墓无气（§009"此课占宅而身宅居墓无气"；§026"干支乘墓各昏迷"；
            #   L"干支乘墓各昏迷"）
            if gan_shang == mu_zhi and zhi_shang and ri_zhi:
                zhi_mu = GAN_MU.get(ri_gan, '')  # 支墓按日干同五行取
                if zhi_shang == zhi_mu:
                    return self._mk('身宅居墓', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'干上{gan_shang}支上{zhi_shang}各乘墓神，身宅居墓无气，宅运昏迷',
                                    '§宅墓02·009"身宅居墓无气"; L"干支乘墓各昏迷"')
            # 干上神=日墓 → 人受墓滞，利宅不利人（§019"日上墓作天后主迟滞时运未通"）
            if gan_shang == mu_zhi:
                return self._mk('利宅不利人', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}为日墓，主人受墓滞，时运未通，利宅不利人',
                                '§宅墓02·019"日上墓作天后主迟滞时运未通"')
            # 三传自旺方递归死绝 → 衰败（§011"丁巳二火自旺方递归死绝之地"；
            #   判据：中传=日绝、末传=日死）
            if zhong == jue_zhi and mo == si_zhi:
                return self._mk('旺极而衰', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自旺方递归死绝（中{zhong}为日绝、末{mo}为日死），家业由盛转衰',
                                '§宅墓02·011"丁巳二火自旺方递归死绝之地"')
            # 干支上神自刑 → 宅不居人/人自刑（§028"日上自刑乃人刑人，宅上自刑宅不居人也"；
            #   判据：干上神=日干寄宫（自刑）或 支上神=日支（自刑））
            if (gan_shang == ji_gong and gan_shang in ZI_XING) or \
               (zhi_shang == ri_zhi and zhi_shang in ZI_XING):
                return self._mk('干支自刑', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上{gan_shang}支上{zhi_shang}自刑，人刑人宅不居人，家道自耗',
                                '§宅墓02·028"日上自刑乃人刑人宅上自刑宅不居人也"')
            # 三传成子孙局（局五行=日干所生）或 ≥2 传为子孙爻 → 子息耗家财
            # （§008"三传日辰皆子孙爻，家计亦被子孙磨灭"；§031"中末传巳午为甲之子息
            #   秉旺气脱干，主因子息破费钱物而败"；§021"子作盗气，诸子耗盗财物"）
            zi_sun_cnt = sum(1 for z in (chu, zhong, mo) if _shi_shen(z, ri_gan) == '子孙')
            if (ju_wx and gw and SHENG.get(gw) == ju_wx) or zi_sun_cnt >= 2:
                return self._mk('子息耗家', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}为日干子孙（局/爻），子息脱耗家财，家计磨灭',
                                '§宅墓02·008"三传日辰皆子孙爻家计亦被子孙磨灭"; §宅墓02·031"主因子息破费钱物而败"')
            # 三传成财局（局五行=日干所克）→ 财多招盗/因财致祸（§016"三传皆财为家贼所偷"；
            #   §034"传财化鬼财休觅"）
            if ju_wx and gw and KE.get(gw) == ju_wx:
                return self._mk('财多招盗', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}成{ju_wx}局为日干财局，财气太盛为家贼所偷，因财致祸',
                                '§宅墓02·016"三传皆财为家贼所偷"; §宅墓02·034"传财化鬼财休觅"')
            # 末传=日墓 → 宅运衰败（L32"干支各乘墓绝必须传中及年命冲破乃吉"）
            if mo == mu_zhi:
                return self._mk('宅运衰败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，干支各乘墓绝，宅运衰败，须传中及年命冲破乃吉',
                                'L32"干支各乘墓绝必须传中及年命冲破乃吉"')
            # 三交课：三传含≥2个四正（子午卯酉）→ 宅中淫乱（§038"此课名为三交…主男女淫奔，
            #   宅中有淫乱不明事也"；发用午火临酉支上处死地）
            _SI_ZHENG = {'子', '午', '卯', '酉'}
            si_zheng_cnt = sum(1 for z in (chu, zhong, mo) if z in _SI_ZHENG)
            if si_zheng_cnt >= 2 and chu in _SI_ZHENG:
                return self._mk('宅中淫乱', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}三交课，四正相加，非死即败，主男女淫奔，宅中有淫乱不明事',
                                '§宅墓02·038"此课名为三交…主男女淫奔宅中有淫乱不明事也"')
            # 支上神=日干子孙（脱宅）→ 宅泄人散（§037"宅上子作天后，是前逼水…财退人散"）
            if zhi_shang and _shi_shen(zhi_shang, ri_gan) == '子孙':
                return self._mk('宅泄人散', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}为日干子孙脱宅，宅气外泄，财退人散',
                                '§宅墓02·037"宅上子作天后是前逼水，财退人散"')
            # 支上神=羊刃 → 家人争屋四散分飞（§042"宅上午上螣蛇带羊刃，主家人争屋四散分飞"）
            if zhi_shang and yang_ren_zhi and zhi_shang == yang_ren_zhi:
                return self._mk('争屋分飞', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}为日干羊刃，主家人争屋，四散分飞',
                                '§宅墓02·042"宅上午上螣蛇带羊刃主家人争屋四散分飞"')
            # 末传=日干败地 → 晚景衰败（§020"末传主晚景，传归于酉，作日之败神，因此晚年愈贪色"；
            #   置于羊刃/三交/宅泄之后——§042首断争屋分飞）
            if mo == bai_zhi:
                return self._mk('晚景败神', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日干败地，晚年运败，家计恐为所耗',
                                '§宅墓02·020"末传主晚景传归于酉作日之败神"')
            # 三传皆阴（六阴相继）→ 宅运衰败不振（§011"六阴相继更无阳神"；CASE-0476；
            #   守卫：中末空亡可解——§023"课得极阴主灾变最喜空亡可解"）
            if chu in _YIN_ZHI and zhong in _YIN_ZHI and mo in _YIN_ZHI:
                if zhong in kong and mo in kong:
                    return self._mk('阴极灾缓', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'三传{chu}·{zhong}·{mo}六阴相继，幸中末空亡可解，虽有灾危不至不测',
                                    '§宅墓02·023"课得极阴主灾变最喜空亡可解"')
                return self._mk('宅运不振', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}六阴相继更无阳神，家宅衰败不振',
                                '§宅墓02·011"六阴相继更无阳神从此衰败不振"')
            # 玄武乘日鬼入传 → 宅防失脱（L688"元武乘神克日干主破财失物"；
            #   守卫：仅玄武乘鬼触发——CASE-0206"三传无官鬼财在长生上不失财"）
            if any(tj == '玄武' and _shi_shen(z, ri_gan) == '官鬼'
                   for z, tj in ((chu, chu_tj), (zhong, zhong_tj), (mo, mo_tj))):
                return self._mk('宅防失脱', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'玄武乘日鬼入传，主退损人口常有失脱，宅防盗贼',
                                'L49"玄武加宅主退损人口常有失脱"; L688"元武乘神克日干主破财失物"')
            # 支上神空亡 → 先难后易（求宅基/坟地。邵公两案断法一致：
            #   §010"支上空亡是宅不可得而图也…中传巳火为干之长生，至丁巳年方才造此宅"（终得宅）；
            #   CASE-0348"辰为坟地作空亡而发用，故主有空穴…填实后必出贵人"（终发贵）。
            #   故支空非终凶，而是宅基暂未定，先难后易。）
            if zhi_shang and zhi_shang in kong:
                return self._mk('先难后易', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}空亡，宅基暂未可得，先涉艰难，待空亡填实/生旺之时终可得宅',
                                '§宅墓02·010"支上空亡是宅不可得而图也…至丁巳年方才造此宅"; CASE-壬占汇选-0348"填实后必出贵人"')
            # 支生干 → 宅生人安享福祉（L18；局部吉象，置于凶象之后）
            if zhi_shang and SHENG.get(ZHI_WX.get(zhi_shang, '')) == gw:
                return self._mk('宅运兴旺', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}生日干，宅生人，安享福祉，家宅兴旺',
                                'L"支生干=宅生人主安享福祉"')
            # 干生支 → 攻苦奔驰劳碌（L17；兜底：仅在无更明确走向时）
            if gan_shang and SHENG.get(gw) == ZHI_WX.get(zhi_shang or ri_zhi, ''):
                return self._mk('劳碌奔波', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干生支，人人生宅，攻苦奔驰劳碌终身',
                                'L"干生支=人人生宅主攻苦奔驰劳碌终身"')

        # ───────────────────────────
        # 【胎产】
        # ───────────────────────────
        if category == '胎产':
            # 【邵公断案·胎产子息章深读 2026-08-18】
            #   §125"干支见酉，皆阳刃破碎自刑…必不利于子母"（羊刃临干支）；
            #   §127"独足…毕竟男胎不成"（独足课子息难成）；
            #   §129"三传贵人太多，所以贵多不贵…年三十二上自有子"（课传贵多过房子难留）；
            #   §131"虎乘墓入内门，故母死"（末传日墓母死子存）
            YANG_REN3 = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
            _yr = YANG_REN3.get(ri_gan, '')
            GUI_REN3 = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'},
                        '戊': {'丑', '未'}, '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'},
                        '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
            _gui_set = GUI_REN3.get(ri_gan, set())
            # 干支上神皆=日干羊刃（破碎）→ 产育不利，子母俱伤（§125"干支见酉，皆阳刃破碎
            #   自刑，故先害身，却来害母"）
            if _yr and gan_shang == _yr and zhi_shang == _yr:
                return self._mk('刃破伤子', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支上神皆{_yr}为日干羊刃破碎自刑，必不利于子母，产育大凶',
                                '§胎产子息07·125"干支见酉，皆阳刃破碎自刑…必不利于子母"')
            # 【指南深读 第六轮】干上神乘白虎（日干上虎）→ 子母不保（ZN-孕产-四"日干上虎
            #   来遁鬼，支上子乘游魂……子母不保"——辛丑日干上酉乘白虎）
            if _gan_shang_tj == '白虎':
                return self._mk('虎临子母', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}乘白虎，日干上虎来遁鬼，子母不保',
                                'ZN-孕产-四"日干上虎来遁鬼…子母不保"')
            # 末传=日墓 → 母死子存（§131"虎乘墓入内门，故母死…日干得旺相之气，故儿存"）
            if mo == mu_zhi:
                return self._mk('母死子存', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，虎乘墓入内门，主母死；干上儿得旺气则子存',
                                '§胎产子息07·131"支是母兮干是儿…虎乘墓入内门，故母死…日干得旺相之气，故儿存"')
            # 三传独足（同支）→ 子息难成，男胎不成（§127"独足…毕竟男胎不成也"）
            if chu == zhong == mo:
                return self._mk('独足无子', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}独足课，子息难成，男胎不成',
                                '§胎产子息07·127"独足…毕竟男胎不成也"')
            # 课传贵人≥3处（贵多不贵）→ 子息占：过房子不合留，本命行年自有子（§129"三传
            #   贵人太多，所以贵多不贵…吾兄年三十二上，自有子"）
            _gui_cnt = (1 if gan_shang in _gui_set else 0) + (1 if zhi_shang in _gui_set else 0) + \
                       sum(1 for z in (chu, zhong, mo) if z in _gui_set)
            if _gui_cnt >= 3:
                return self._mk('贵多不贵', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'课传贵人{_gui_cnt}处，贵多不贵，过房子不合留，然本命行年自有子',
                                '§胎产子息07·129"三传贵人太多，所以贵多不贵…年三十二上自有子"')
            # 三传克日 → 难产；三传克支 → 伤母（L229）
            #   【指南深读 第三轮】守卫：中传=子孙（胎神乘旺气）→ 不判产难
            #   （ZN-孕产-二"月建重叠，作胎神乘旺气……母子清吉"——中传子=辛之子孙）
            if mo_wx and KE.get(mo_wx) == gw and _shi_shen(zhong, ri_gan) != '子孙':
                return self._mk('产难母伤', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传克日干，产难，须防伤母',
                                'L229"三传克日难产三传克支伤母"')
            # 【指南深读 第三轮】中传=日干官鬼（死气）→ 子息有损，凶
            #   （ZN-孕产-三"女子死者，作死气日鬼也"——中传酉=乙之官鬼）
            if zhong_wx and KE.get(zhong_wx) == gw:
                return self._mk('子息有损', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'中传{zhong}为日干官鬼死气，女子死者作死气日鬼，子息有损',
                                'ZN-孕产-三"女子死者，作死气日鬼也"')
            # 【指南深读 第三轮】干上神=卯（震=长男）→ 生男吉
            #   （ZN-孕产-五"干上卯属震，长男之象……生贵儿必矣"）
            if gan_shang == '卯':
                return self._mk('生男之祥', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神卯属震，长男之象，生贵儿必矣，生必顺利',
                                'ZN-孕产-五"干上卯属震，长男之象…生贵儿必矣"')
            # 支辰上神生日上神 → 顺而易生（L223）
            if gan_shang and zhi_shang and SHENG.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(gan_shang, ''):
                return self._mk('顺产易生', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}生日上神{gan_shang}，顺而易生，母子平安',
                                'L223"辰上神生日上神为顺而易生"')
            # 末传=长生 → 母无恙产易（案例0104"支辰又乘亥水长生故母无恙产亦易也"）
            if mo == cs_zhi:
                return self._mk('母安产顺', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日长生，母无恙，产亦易，母子俱安',
                                'CASE-壬占汇选-0104"支辰又乘亥水长生故母无恙产亦易也"')
            # 伏吟日辰相刑 → 子母俱死（案例0076"子母俱死伏吟课阴阳各伏"）
            #   【指南深读 第三轮】守卫：伏吟 + 中传=子孙（胎神乘旺）→ 母子清吉
            #   （ZN-孕产-二"月建重叠，作胎神乘旺气……母子清吉"）
            if fu_yin:
                if _shi_shen(zhong, ri_gan) == '子孙':
                    return self._mk('母子清吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'伏吟课而中传{zhong}为子孙胎神乘旺气，母子清吉，主双胎',
                                    'ZN-孕产-二"月建重叠，作胎神乘旺气…母子清吉"')
                return self._mk('产凶母危', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'伏吟课阴阳各伏，滞而不通，生不下，子母俱危',
                                'CASE-壬占汇选-0076"子母俱死盖伏吟课阴阳各伏"')
            # 初中空亡不见阳 → 产不顺（案例0523"虽曰向三阳奈初中空亡依旧不见阳"；
            #   【BUG-FIX 2026-08-18】末传凶将时不降为平——案例0150子病"末传朱雀带驿马主死后再来"）
            if (chu in kong or zhong in kong) and mo_shi != '凶':
                return self._mk('产期迁延', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初中传空亡，不见阳，产期迁延不顺',
                                'CASE-壬占汇选-0523"奈初中空亡依旧不见阳"')

        # ───────────────────────────
        # 【出行】
        # ───────────────────────────
        if category == '出行':
            # 【邵公断案·出行访谒/行人音信章深读 2026-08-18】
            #   §150"中传断桥，访之反不得"（三合局中传空亡）；§151"甲日火局十二分盗气…
            #   大有所费"（盗气局）；§154"日上驿马交驰…主动必远"（返吟驿马）；
            #   §158"中传又雀乘太岁…被蒿恼不意而动"（中传朱雀文书扰）；
            #   §161"昴星课…朱雀临门，主文字立至"（昴星文字即至）
            SAN_HE_JZ = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
            SAN_HE_WX = ['水', '火', '金', '木']
            _sanchuan_set = {chu, zhong, mo}
            _ju_wx = ''
            for _jz, _jwx in zip(SAN_HE_JZ, SAN_HE_WX):
                if _sanchuan_set == _jz:
                    _ju_wx = _jwx
                    break
            # 驿马（按日支三合：申子辰马寅、寅午戌马申、巳酉丑马亥、亥卯未马巳）
            _MA = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
                   '巳': '亥', '酉': '亥', '丑': '亥', '亥': '巳', '卯': '巳', '未': '巳'}
            _ma_zhi = _MA.get(ri_zhi, '')
            # 干支乘死绝最忌不宜远行（L434）
            if mo == jue_zhi or (mo in kong and mo_shi == '凶'):
                return self._mk('不宜远行', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}乘死绝，不宜远行，恐途中有阻',
                                'L434"干支乘死绝最忌不宜远行"')
            # 三合局中传空亡（断桥）→ 访之反不得（§150"中传断桥，访之反不得耳"；
            #   三合全局本主相见，中空则事中断）。末传旺相（临官/帝旺）→ 先凶后吉，
            #   终必达（§156"中传断桥…文书次第未备…目下未归。在三月子日至也"）
            if _ju_wx and zhong in kong:
                _wang_set = {'寅', '卯'} if gw == '木' else {'巳', '午'} if gw == '火' else \
                            {'申', '酉'} if gw == '金' else {'亥', '子'}
                if mo in _wang_set:
                    return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'三合局{chu}·{zhong}·{mo}中传{zhong}空亡为断桥，事受阻迟滞，然末传{mo}旺相，终必达，先凶后吉',
                                    '§行人音信11·156"中传断桥…文书次第未备…在三月子日至也"')
                return self._mk('访之不得', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三合局{chu}·{zhong}·{mo}中传{zhong}空亡为断桥，访之反不得，事不谐',
                                '§出行访谒11·150"中传断桥，访之反不得耳"')
            # 三合局为日之子孙（盗气局）→ 大有所费，所得微薄（§151"甲日火局，十二分盗气，
            #   支又来耗我，大有所费"）
            if _ju_wx and gw and SHENG.get(gw) == _ju_wx:
                return self._mk('破费无益', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三合{_ju_wx}局{chu}·{zhong}·{mo}为日干盗气，十二分盗气，支又来耗，大有所费，所得微薄',
                                '§出行访谒11·151"甲日火局，十二分盗气，支又来耗我，大有所费"')
            # 返吟+驿马入传（中传非日支）→ 主动必远，行必成（§154"日上驿马交驰…主动必远"；
            #   守卫：§149返吟中传归支=半路归家，不作远行之吉）
            if fan_yin and _ma_zhi and any(z == _ma_zhi for z in (chu, zhong, mo)) and zhong != ri_zhi:
                return self._mk('主动必远', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'返吟课驿马{_ma_zhi}交驰入传，主动必远，行必成，虽远必达',
                                '§出行访谒11·154"日上驿马交驰…主动必远"')
            # 【指南深读 第二轮】驿马临干 → 行人速来（ZN-行人-四"驿马临干……行人速来"）
            if _ma_zhi and gan_shang == _ma_zhi:
                return self._mk('行人速来', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'驿马{_ma_zhi}临干，行人自宅起程，速来将至',
                                'ZN-行人-四"驿马临干…行人速来"')
            # 螣蛇上课 → 途路有惊恐盗贼（L443）
            if chu_tj == '螣蛇' or mo_tj == '螣蛇':
                return self._mk('途中惊恐', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'螣蛇入传，途路有惊恐盗贼，出行不利',
                                'L443"螣蛇上课主途路有惊恐盗贼"')
            # 登三天课辰午申 → 途程艰难（L442）
            if {chu, zhong, mo} == {'辰', '午', '申'}:
                return self._mk('途程艰难', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                '登三天课，途程艰难，出行辛苦',
                                'L442"登三天课辰午申主呈途艰难"')
            # 初传=日干官鬼且临绝地 → 音信凶兆，文字来而事扰，先吉后凶（§158"申是岁马带鬼
            #   克日…涉三渊之格…被蒿恼不意而动…充替河州"）
            if chu == jue_zhi and _shi_shen(chu, ri_gan) == '官鬼':
                return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}为日干官鬼临绝地，音信文字必来，然鬼害来速，被蒿恼不意而动，先吉后凶',
                                '§行人音信12·158"申是岁马带鬼克日…被蒿恼不意而动"')
            # 昴星课 → 文字立至（§161"盖昴星课…朱雀临门，主文字立至"）
            if '昴星' in keti:
                return self._mk('文字立至', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'昴星课，类神乘道路神临门，文字立至，消息速达',
                                '§行人音信12·161"昴星课…朱雀临门，主文字立至"')
            # 日上得吉将/生日之神 → 往之吉（L416）
            if chu_shi == '吉' and mo_shi != '凶':
                return self._mk('出行顺利', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'日上得吉，出行顺利，往来无阻',
                                'L416"日干旺相或日上得吉将则往之吉"')

        # ───────────────────────────
        # 【婚姻】
        # ───────────────────────────
        if category == '婚姻':
            # 【邵公断案·婚姻章深读 2026-08-18】核心：
            #   §122"此课占婚何必有媒?私情久已通矣"（后合入传=婚必成，返吟玄武=淫奔先成后败）
            #   §123"上方出墓寻生其亲必成…但恐不久尊堂服动"（先成后败）
            #   §124"此课必成，恐成亲后…兼难得子"（天罗地网兜牢+退子=先成后败）
            # ① 后合入传（天后+六合俱现）→ 婚必成；若返吟/玄武淫神入传 → 私情淫奔之婚，
            #   女非贞良暗有退子，先成后败（§122"后合占婚岂用媒…私情久已通矣…暗有退子"）
            _hou_he = (chu_tj in ('天后', '六合') or zhong_tj in ('天后', '六合') or
                       mo_tj in ('天后', '六合'))
            if _hou_he and (chu_tj in ('天后', '六合') and (zhong_tj in ('天后', '六合') or
                                                            mo_tj in ('天后', '六合'))):
                if fan_yin or xuan_wu_zai_chuan:
                    return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'后合入传婚必成，然返吟玄武淫神乘之，私情淫奔，女非贞良，暗有退子，先成后败',
                                    '§婚姻06·122"此课占婚何必有媒?私情久已通矣…暗有退子"')
                return self._mk('私情已通', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'后合入传（天后六合并见），私情久已通，婚必成',
                                '§婚姻06·122"此课占婚何必有媒?私情久已通矣"')
            # ② 出墓寻生（干上神=日墓，传中见长生）→ 亲必成，然恐服动之灾，先成后败
            #   （§123"上方出墓寻生其亲必成…但恐不久尊堂服动"；L544"自墓传生"）
            if gan_shang and gan_shang == mu_zhi and \
                    any(z == cs_zhi for z in (chu, zhong, mo)):
                return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}为日墓，传中{cs_zhi}长生，出墓寻生其亲必成，然恐尊堂服动，先成后败',
                                '§婚姻06·123"上方出墓寻生其亲必成…但恐不久尊堂服动"')
            # ③ 三传生日 → 婚姻迪吉（L178"三传生日婚姻迪吉媒言亦实"）
            if mo_wx and SHENG.get(mo_wx) == gw:
                return self._mk('姻缘有成', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传生日干，婚姻迪吉，媒言亦实，婚事可成',
                                'L178"三传生日婚姻迪吉"')
            # ④ 日生三传 → 强成终久不偕（L179）
            if gw and mo_wx and SHENG.get(gw) == mo_wx:
                return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'日干生三传，事多乖违，强成终久不偕，婚姻难长久',
                                'L179"日生三传事多乖违强成终久不偕"')
            # ⑤ 初传天后与日辰相生 → 必成（案例0069"初传天后与日辰相生而气和必成之理也"）
            if chu_tj == '天后' and chu_shi != '凶':
                return self._mk('婚姻必成', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}乘天后与日辰相生，气和必成，婚姻可成',
                                'CASE-壬占汇选-0069"初传天后与日辰相生而气和必成之理也"')
            # ⑥ 朱雀发用克日 → 不成（L169"朱雀发用克日不成"）
            if chu_tj == '朱雀' and KE.get(chu_wx) == gw:
                return self._mk('婚姻不成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'朱雀发用克日干，婚姻不成，媒言难信',
                                'L169"朱雀发用克日不成"')
            # ⑦ 末传=日墓 → 婚难长久（L183"即成亦不长久"）
            if mo == mu_zhi:
                return self._mk('婚难长久', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，婚姻即成亦不长久',
                                'L"即成亦不长久"')
            # ⑧ 【指南深读 第二轮】支上神生日上神（支生干=两情相合）→ 婚吉
            #   （ZN-婚姻-一"干支上下相合，支上神又生干上神……夫妇偕老，有子之象"）
            if gan_shang and zhi_shang and SHENG.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(gan_shang, ''):
                return self._mk('两情相合', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}生干上神{gan_shang}，干支上下相合，女愿连姻，夫妇偕老',
                                'ZN-婚姻-一"干支上下相合，支上神又生干上神…夫妇偕老，有子之象"')

        # ───────────────────────────
        # 【征战】（大六壬指南兵斗/章奏体系 2026-08-18 第二轮）
        # ───────────────────────────
        if category == '征战':
            # ① 三合局=日干官鬼 → 官鬼局破城杀将（ZN-兵斗-五"贵人克干发用，合中犯煞……
            #   必然破城杀将"——辛巳日午寅戌火局=辛官鬼）
            _ZZ_SANHE = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
            _ZZ_WX = ['水', '火', '金', '木']
            _zz_ju = ''
            for _jz, _jwx in zip(_ZZ_SANHE, _ZZ_WX):
                if {chu, zhong, mo} == _jz:
                    _zz_ju = _jwx
                    break
            if _zz_ju and KE.get(_zz_ju) == gw:
                return self._mk('官局破城', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}官鬼局，贵人克干发用合中犯煞，必然破城杀将',
                                'ZN-兵斗-五"贵人克干发用，合中犯煞…必然破城杀将"')
            # ② 三传两两递克（初克中、中克末）→ 递克兵败（ZN-兵斗-十二"传将递克……
            #   两军敌战尽遭伤"——丙子日巳申寅两两相克）
            if chu_wx and zhong_wx and mo_wx and \
                    KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx:
                return self._mk('递克兵败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}递克，两军敌战尽遭伤，兵败之象',
                                'ZN-兵斗-十二"传将递克…两军敌战尽遭伤也"')
            # ③ 【指南深读 第四轮】末传克初传（非三合局）→ 以凶制凶，凶可解
            #   （ZN-兵斗-七"末传…蛇冲克初传，此为以凶制凶，不过虎头蛇尾，不日围解"——
            #   庚子日午酉子末子克初午；守卫：三合局不从革兵斗-二"合中刑干害支"仍凶）
            #   守卫：中末空亡（初实中末空）→ 不判吉——ZN-兵斗-九"中末俱空，岂能前进？
            #   凡初实中末空者……主事中途而止，强进必有祸也"
            if not _zz_ju and mo_wx and chu_wx and KE.get(mo_wx) == chu_wx and \
                    zhong not in kong and mo not in kong:
                return self._mk('以凶制凶', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}克初传{chu}，以凶制凶，不过虎头蛇尾，凶必无虞，不日围解',
                                'ZN-兵斗-七"末传…蛇冲克初传，此为以凶制凶…不日围解"')
            # ④ 【指南深读 第四轮】末传=日禄（健旺制劫）→ 守坚敌弱，吉
            #   （ZN-兵斗-四"末传健旺制劫，是守坚敌弱，故知必不能东下"——乙亥日末卯=乙禄）
            #   守卫：三合局=日干财局（传课纯财/合中刑干害支）→ 不判吉——ZN-兵斗-二
            #   "课传从革，合中刑干害支……死又何疑"（丙午日酉丑巳金局=丙财局，末巳=丙禄）
            if lu_zhi and mo == lu_zhi and not (_zz_ju and KE.get(gw) == _zz_ju):
                return self._mk('守坚敌弱', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日禄健旺制劫，守坚敌弱，必不能久持，围自解',
                                'ZN-兵斗-四"末传健旺制劫，是守坚敌弱"')
            # ⑤ 【神煞占类化 2026-08-18】劫煞入传 → 兵戈凶（ZN-出行-一"中传劫煞旬丁刑克支干"；
            #   ZN-兵斗-五"中传月建克末传，必然破城杀将"）
            if _ss_js and _ss_js in (chu, zhong, mo):
                return self._mk('劫煞兵戈', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'劫煞{_ss_js}入传，刑克支干，兵戈动扰，破城杀将之象',
                                'ZN-出行-一"中传劫煞旬丁刑克支干"; ZN-兵斗-五"中传月建克末传"')
            # ⑥ 【神煞占类化 2026-08-18】游都入传 → 贼兵据城（ZN-兵斗-五"游都居支前……
            #   贼符侵酉地……据城无疑"；守卫：游都离日辰远（不在传）不判——ZN-兵斗-四
            #   "游都居西南恋生，且离日辰远……守坚敌弱"）
            #   守卫：三合局生日干 → 不判凶——ZN-兵斗-十一"结水局生日……大吉之兆"
            #   （乙酉日申子辰水局生乙木，游都子在中传仍大吉）
            if _ss_yd and _ss_yd in (chu, zhong, mo) and not (_zz_ju and SHENG.get(_zz_ju) == gw):
                return self._mk('游都兵警', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'游都{_ss_yd}入传，贼兵据城，兵戈动扰之象',
                                'ZN-兵斗-五"游都居支前…据城无疑"')
            # ⑦ 【神煞占类化 2026-08-18】三合局=日干财局 且 初传临干（合中刑干害支）→ 凶
            #   （ZN-兵斗-二"课传从革，合中刑干害支……干乘死气，支乘干支之墓，死又何疑"——
            #   丙午日酉丑巳金局=丙财局，初传酉临干）
            if _zz_ju and KE.get(gw) == _zz_ju and gan_shang == chu:
                return self._mk('财局犯干', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}财局而初传{chu}临干，合中刑干害支，干乘死气，兵败之象',
                                'ZN-兵斗-二"课传从革，合中刑干害支…死又何疑"')

        # ───────────────────────────
        # 【贼盗】（失物/捕盗）
        # ───────────────────────────
        if category == '贼盗':
            # 【神煞占类化 2026-08-18】游都入传 → 贼盗之象（ZN-应候-二"游都贼符临干支，
            #   主有贼……自东北来劫邻人衣物银钱"）
            if _ss_yd and _ss_yd in (chu, zhong, mo):
                return self._mk('游都贼至', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'游都{_ss_yd}入传，贼盗将至，防劫夺失脱',
                                'ZN-应候-二"游都贼符临干支…主有贼"')
            # 元武乘鬼现传 → 盗难寻（L688"元武不克日辰而空亡脱气日鬼...必盗贼失脱之事"）
            if xuan_wu_zai_chuan and any(_shi_shen(z, ri_gan) == '官鬼' for z in (chu, zhong, mo)):
                return self._mk('失物难寻', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'玄武乘日鬼入传，盗贼难获，失物难寻',
                                'L688"元武乘神克日干主破财失物"')
            # 末传克初传 → 贼人堪捉（L702"末传盛初传贼人堪捉"）
            if mo_wx and chu_wx and KE.get(mo_wx) == chu_wx:
                return self._mk('失物可寻', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}克初传{chu}，贼人堪捉，失物可寻',
                                'L702"末传盛初传贼人堪捉"')
            # 【邵公断案·亡盗章 2026-08-18】独足课 → 失物不须寻，当日自归
            #   （§亡盗15·192"独足课，酉为婢，加未，不离身宅矣。兼独足体，一足焉能动焉？
            #   不须寻，当日归矣"）
            if chu == zhong == mo:
                return self._mk('独足自归', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}独足课，失物不离身宅，一足难行，不须寻当日归',
                                '§亡盗15·192"独足课…不须寻，当日归矣"')
            # 末传生日干 → 失物自归（L673"元武乘旺生干支者不寻自还"）
            #   【2026-08-18】置于循环格之前——§188 循环格而末酉生癸水，邵公断"可往擒之"（吉）
            if mo_wx and SHENG.get(mo_wx) == gw:
                return self._mk('失而复得', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}生日干，失物不寻自还，失而复得',
                                'L673"元武乘旺生干支者不寻自还"')
            # 循环格 → 贼人复来（L723"周遍格循环格主贼人复来"）
            if xun_huan:
                return self._mk('贼人复来', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'循环格，主贼人复来之意，失物难全保',
                                'L723"周遍格循环格主贼人复来"')

        # ───────────────────────────
        # 【行人】
        # ───────────────────────────
        if category == '行人':
            # 干克支 → 外人入内行人主归（L461）
            if gan_ke_zhi_shang:
                return self._mk('行人将归', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}克支上神{zhi_shang}，外人入内之象，行人主归',
                                'L461"干克支外人入内之象占行人主归"')
            # 支克干 → 由内向外行人未归（L462）
            if zhi_ke_gan_shang:
                return self._mk('行人未归', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}克干上神{gan_shang}，由内向外之象，行人未归',
                                'L462"支克干由内向外之象占行人未归"')
            # 三传先虚后实 → 行人来归；先实后虚 → 停留（L476-477）
            if (chu in kong or zhong in kong) and mo not in kong:
                return self._mk('行人来归', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传先虚后实，行人来归，先有波折终能归来',
                                'L476"三传先虚后实行人来归"')
            if chu not in kong and (zhong in kong or mo in kong):
                return self._mk('行人停留', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传先实后虚，行人停留，暂时难归',
                                'L477"先实后虚行人停留"')
            # 末传加日/末传生日 → 行人归（L482"末传加日者行人亦主归"）
            if mo_wx and SHENG.get(mo_wx) == gw:
                return self._mk('行人有信', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}生日干，行人主归，近日有信',
                                'L482"末传加日者行人亦主归"')

        return None

    def analyze(self, ri_gan: str, ri_zhi: str,
                sanchuan: List[str], tianjiang_list: List[str] = None,
                kongwang=('', ''), keti: str = '', sike: List = None,
                category: str = '', zishu: str = '', yuejiang: str = '',
                year: str = '', sike_tj: Dict = None) -> Dict[str, Any]:
        """
        主入口。返回事体走向分析。
        sanchuan: [初传, 中传, 末传]
        tianjiang_list: [初传天将, 中传天将, 末传天将]
        sike: 四课（用于循环格/干支上神判定）
        category: 占类（功名/疾病/官讼/求财/家宅/胎产/出行/婚姻/贼盗/行人/其他）
        zishu: 家宅子类（阳宅/阴宅/迁移；空=阳宅默认）。阴宅看辰穴/朝案，迁移看丁马/宜迁。
        yuejiang: 月将（'申将'或'申'），供神煞占类化规则（游都/劫煞/天马/天赦等）使用。
        year: 占课年（干支，如'己酉'），供太岁/岁破规则使用。
        sike_tj: 天将映射 {地支: 天将}（干支上神天将，供贵人乘贵/朱雀位置等规则）。
        """
        if not sanchuan or len(sanchuan) < 3:
            return {'走向': '未定', '阶段': {}, '叙事': '三传不全，无法判断事体走向', '终局': '平'}
        # 占类归一化（走失/六畜等归入贼盗——疏正亡盗吉案因占类未映射而误判平/凶，2026-08-18）
        if category in ('亡盗', '六畜走失', '走失'):
            category = '贼盗'
        tj = list(tianjiang_list or [])
        kong = set(kongwang or [])
        chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
        chu_tj = tj[0] if len(tj) > 0 else ''
        zhong_tj = tj[1] if len(tj) > 1 else ''
        mo_tj = tj[2] if len(tj) > 2 else ''

        # ── 阶段态势 ──
        chu_shi = _duan_shi(chu, ri_gan, chu_tj, kong)
        zhong_shi = _duan_shi(zhong, ri_gan, zhong_tj, kong)
        mo_shi = _duan_shi(mo, ri_gan, mo_tj, kong)
        mu_zhi = GAN_MU.get(ri_gan, '')
        cs_zhi = WX_CS.get(GAN_WX.get(ri_gan, ''), '')
        gw = GAN_WX.get(ri_gan, '')
        chu_wx, zhong_wx, mo_wx = ZHI_WX.get(chu, ''), ZHI_WX.get(zhong, ''), ZHI_WX.get(mo, '')

        # ── 占类化走向规则（v2：占类专属，优先于通用规则）──
        cat_out = self._category_rules(category, ri_gan, ri_zhi, chu, zhong, mo,
                                       chu_tj, zhong_tj, mo_tj, kong, keti, sike,
                                       zishu=zishu, yuejiang=yuejiang, year=year,
                                       sike_tj=sike_tj)
        if cat_out:
            return cat_out

        # ── 通用走向判定（语料实证规则，保持 v1 不动）──
        # ① 三传递生：初生中、中生末、末生日干 → 得人引荐扶持事成（L777/L722）
        if (gw and chu_wx and zhong_wx and mo_wx and
                SHENG.get(chu_wx) == zhong_wx and SHENG.get(zhong_wx) == mo_wx and
                SHENG.get(mo_wx) == gw):
            return self._mk('三传递生', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            '三传{0}递生（{1}生{2}、{2}生{3}、{3}生日干），得人引荐扶持，事成所谋遂意'.format(
                                f'{chu}·{zhong}·{mo}', chu_wx, zhong_wx, mo_wx))
        # ② 三传递克：初克中、中克末、末克日干 → 交易损伤事败（L723）
        if (gw and chu_wx and zhong_wx and mo_wx and
                KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx and
                KE.get(mo_wx) == gw):
            return self._mk('三传递克', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            '三传{0}递克（{1}克{2}、{2}克{3}、{3}克日干），层层伤害，事有损伤终归败'.format(
                                f'{chu}·{zhong}·{mo}', chu_wx, zhong_wx, mo_wx))
        # ③ 循环格：三传不离四课 → 反复（L1077"循环格主病多反复"，L1374"主贼人复来"）
        if sike and len(sike) >= 4:
            sike_zhi = set()
            for k in sike:
                if isinstance(k, (list, tuple)) and len(k) >= 2:
                    sike_zhi.add(str(k[1]))
                    if len(k) >= 3:
                        sike_zhi.add(str(k[2]))
                elif isinstance(k, dict):
                    sike_zhi.add(str(k.get('上神', '')))
                    sike_zhi.add(str(k.get('下神', '')))
            if {chu, zhong, mo} <= sike_zhi:
                return self._mk('反复', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}不离四课，循环格，事有反复，一波三折')
        # ④ 末传生日干 → 暗地有人扶持，事终成（知识库 L689/L780）
        if ZHI_WX.get(mo) and SHENG.get(ZHI_WX.get(mo, '')) == GAN_WX.get(ri_gan, ''):
            walk = '先难后易' if chu_shi == '凶' else '渐入佳境'
            narr = f'初传{chu}{chu_shi}，中传{zhong}{zhong_shi}，末传{mo}生日干，暗地有人扶持，事终有济'
            end = '吉'
        # ⑤ 末传=长生但空亡 → 见生不生，反成凶咎（L235"救神空亡为墓门开大凶"；
        #    案例0369"末又长生…奈何寅是空亡，所以不能引进，见生不生，反成凶咎"）
        if mo == cs_zhi and mo in kong:
            walk = '先吉后凶'
            narr = f'末传{mo}为日干长生，然逢空亡，见生不生，救神空亡，反成凶咎'
            end = '凶'
        # ⑥ 末传=长生 → 结局转生（自墓传生/否极泰来）
        elif mo == cs_zhi:
            walk = '先凶后吉' if (chu_shi == '凶' or zhong_shi == '凶') else '终得生助'
            narr = f'初{chu_shi}中{zhong_shi}，末传{mo}为日干长生，先难后易，否极泰来'
            end = '吉'
        # ⑦ 末传=日墓 → 有始无终/乐极生悲（L1470）
        elif mo == mu_zhi:
            walk = '先成后败' if (chu_shi == '吉' or zhong_shi == '吉') else '终归于晦'
            narr = f'初{chu_shi}中{zhong_shi}，末传{mo}为日墓，有始无终，乐极生悲之象'
            end = '凶'
        # ⑦ 初传中传空亡而末传不空 → 先涉艰难然后得遂（L783/L830）
        elif (chu in kong and zhong in kong) and mo not in kong:
            walk = '先难后易'
            narr = f'初传{chu}中传{zhong}空亡，末传{mo}不空，先涉艰难费尽心力然后得遂'
            end = '吉'
        # ⑧ 初凶末吉 → 先凶后吉
        elif chu_shi == '凶' and mo_shi == '吉':
            walk = '先凶后吉'
            narr = f'初传{chu}凶，末传{mo}吉，先凶后吉，终得吉'
            end = '吉'
        # ⑨ 初吉末凶 → 先吉后凶
        elif chu_shi == '吉' and mo_shi == '凶':
            walk = '先吉后凶'
            narr = f'初传{chu}吉，末传{mo}凶，先吉后凶，终归于凶'
            end = '凶'
        # ⑩ 三传皆吉 → 事必成
        elif chu_shi == '吉' and zhong_shi == '吉' and mo_shi == '吉':
            walk = '顺遂有成'
            narr = f'三传{chu}·{zhong}·{mo}皆吉，事必成，一帆风顺'
            end = '吉'
        # ⑪ 三传皆凶 → 事必败
        elif chu_shi == '凶' and zhong_shi == '凶' and mo_shi == '凶':
            walk = '艰阻终败'
            narr = f'三传{chu}·{zhong}·{mo}皆凶，事多艰阻，终归于败'
            end = '凶'
        # ⑫ 中末空亡 → 反复难定
        elif mo in kong and zhong in kong:
            walk = '反复难定'
            narr = f'中末传空亡，事有反复，一波三折，须耐心等待'
            end = '平'
        # ⑬ 默认：按末传态势定终局
        else:
            if mo_shi == '吉':
                walk = '终得吉' if chu_shi != '吉' else '始终向吉'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，末传{mo}吉，事终有济'
                end = '吉'
            elif mo_shi == '凶':
                walk = '终归于凶' if chu_shi != '凶' else '始终向凶'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，末传{mo}凶，事终不利'
                end = '凶'
            else:
                walk = '吉凶参半'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，吉凶参半，看类神走向'
                end = '平'

        return self._mk(walk, end, chu_shi, zhong_shi, mo_shi, chu, zhong, mo, narr)


def analyze_liuchen(ri_gan: str, ri_zhi: str, sanchuan: List[str],
                    tianjiang_list: List[str] = None, kongwang=('', ''), keti: str = '',
                    sike: List = None, category: str = '', zishu: str = '',
                    yuejiang: str = '', year: str = '', sike_tj: Dict = None) -> Dict[str, Any]:
    """便捷入口"""
    return LiuChenEngine().analyze(ri_gan, ri_zhi, sanchuan, tianjiang_list, kongwang, keti, sike,
                                  category, zishu, yuejiang, year, sike_tj)


if __name__ == '__main__':
    # 自测：占类化规则
    for cat, sc, tj, rg in [('功名', ['戌', '午', '丑'], ['玄武', '朱雀', '白虎'], '甲'),
                            ('疾病', ['未', '午', '亥'], ['白虎', '六合', '青龙'], '甲'),
                            ('官讼', ['申', '亥', '寅'], ['白虎', '六合', '青龙'], '甲'),
                            ('求财', ['寅', '卯', '戌'], ['勾陈', '六合', '玄武'], '辛'),
                            ('胎产', ['亥', '酉', '卯'], ['六合', '太阴', '青龙'], '甲')]:
        r = analyze_liuchen(rg, '子', sc, tj, category=cat)
        print(f'[{cat}] {sc} {tj} → {r["走向"]} / {r["终局"]} / {r["叙事"]}')
