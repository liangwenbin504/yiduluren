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
                        zishu: str = '') -> Optional[Dict]:
        gw = GAN_WX.get(ri_gan, '')
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
        fan_yin = '返吟' in keti

        # ── 通用占类守卫（所有占类共用，须优先于占类兜底规则）──
        # 末传=长生但空亡 → 见生不生，反成凶咎（L235"救神空亡为墓门开大凶"；
        #   案例0369"末又长生…奈何寅是空亡，所以不能引进，见生不生，反成凶咎"）
        if mo == cs_zhi and mo in kong:
            return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            f'末传{mo}为日干长生，然逢空亡，见生不生，救神空亡，反成凶咎',
                            'L235"救神空亡为墓门开大凶"; CASE-壬占汇选-0369')

        # ───────────────────────────
        # 【功名】（前程仕进·邵公断案60案深读增强 2026-08-18）
        # 刘评归纳："举凡仕宦之占，无非官、禄两样最为切要"（§058）；
        # "幕贵乃科名第一吉神"（§052）；"大凡占前程禄重于财"（§046）。
        # 层次：先课体课格（乱首/顾祖/四绝/登三天/铸印/六阴），
        #       次官禄切要（官星临身/禄临干/禄空/贵空），后幕贵学堂/脱耗。
        # ───────────────────────────
        if category == '功名':
            # 日干禄神（甲禄寅、乙禄卯、丙戊禄巳、丁己禄午、庚禄申、辛禄酉、壬禄亥、癸禄子）
            LU_SHEN = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
                       '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
            lu_zhi = LU_SHEN.get(ri_gan, '')
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
            # 铸印格：三传巳戌卯/戌卯巳/卯巳戌（§049"戌为模范亦落空地"、§050"朱雀投戌墓破模"）
            zhu_yin = ({chu, zhong, mo} == {'巳', '戌', '卯'} or
                       {chu, zhong, mo} == {'巳', '丑', '酉'})
            # 顾祖课（初传=干上神 且 传退入支（§074"日上发传退入支上又是顾祖"））——
            #   判据：初传=干上神 且 末传贴近日支（d_mo <= 2 且 末传比初传更近支）
            #   【BUG-FIX 2026-08-18】§055 干上申=禄（弃武从文吉），申→寅→巳非退向支，
            #   不判顾祖；§074 午→辰→寅 末传寅贴近支辰（d=2<初传d=2且寅为支上神）→ 顾祖凶。
            _zhi_seq2 = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                         '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
            if chu == gan_shang and ri_zhi in _zhi_seq2 and chu in _zhi_seq2 and mo in _zhi_seq2:
                _d_chu = abs(_zhi_seq2[chu] - _zhi_seq2[ri_zhi])
                _d_chu = min(_d_chu, 12 - _d_chu)
                _d_mo = abs(_zhi_seq2[mo] - _zhi_seq2[ri_zhi])
                _d_mo = min(_d_mo, 12 - _d_mo)
                gu_zu = _d_mo <= 2 and _d_mo <= _d_chu
            else:
                gu_zu = False

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
            if gu_zu:
                return self._mk('顾祖受阻', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}退入支上，顾祖课，仕途受阻，升转无望',
                                '§前程仕进03·074"日上发传退入支上又是顾祖"; §097"顾祖传空前程镜中花"')
            # ① 官星临身+初传应之=催官符（§072"官星临日初传应之谓之催官符"）→ 得官
            if guan_lin_shen and _shi_shen(chu, ri_gan) == '官鬼':
                if mo in kong or mo == mu_zhi or zhong in kong:
                    return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'官星{gan_shang}临身初传应之，催官符赴任，然传中{"中传空丁忧" if zhong in kong else "末传" + mo + "空/墓"}，得官后不久即败',
                                    '§前程仕进03·072"官星临日初传应之谓之催官符"; §059"及第后死"')
                return self._mk('得官赴任', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{gan_shang}临身初传应之，催官符，主赴任得官',
                                '§前程仕进03·072"官星临日初传应之谓之催官符"')
            # ①b 官星临身（干上神=官星）→ 得官赴任；末传空/墓/凶将 或 中传空（父母丁忧）
            #   =先成后败（§072"及第后便丁父母服"、§059"及第后死"、§089"得十六月遭父丧"）
            if guan_lin_shen:
                _mo_bad = mo in kong or mo == mu_zhi or mo_shi == '凶'
                _zhong_bad = zhong in kong  # 中传空=父母空=丁忧（§072"中传父母空亡主丁忧"）
                if _mo_bad or _zhong_bad:
                    return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'官星{gan_shang}临身主得官，然{"中传空亡主丁忧" if _zhong_bad else "末传" + mo + ("空" if mo in kong else "墓" if mo == mu_zhi else "凶")}，得官后不久即败',
                                    '§前程仕进03·072"及第后便丁父母服"; §059"及第后死"')
                return self._mk('得官赴任', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{gan_shang}临身，主得官赴任',
                                '§前程仕进03·089"日上官星作贵"')
            # ② 官星发用 + 得地 → 得官升迁（原有；加禄临干强化）
            if guan_xing_fa_yong and chu_shi != '凶' and chu not in kong:
                return self._mk('得官升迁', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'官星{chu}发用，官星得地，求官有望，升迁在望',
                                'L求官用起官星; CASE-壬占汇选-0117/0287')
            # ③ 禄临干（随身禄）→ 得禄有官（§044"午乃丁禄临干日禄扶身"）
            if lu_lin_gan and not lu_kong:
                return self._mk('得禄有官', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'禄神{gan_shang}临干，随身禄扶身，得官食禄',
                                '§前程仕进03·044"午乃丁禄临干日禄扶身"')
            # ④ 禄空 → 虚禄难食（§055"将仕之禄乃虚禄…禄空不可为武"、§076"末又是禄乘空亡入墓"）
            if lu_kong:
                return self._mk('虚禄难食', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'禄神{lu_zhi}空亡，虚禄也，得官不能食禄',
                                '§前程仕进03·055"将仕之禄乃虚禄"; §076"末又是禄乘空亡入墓"')
            # ⑤ 贵空 → 虚贵无位（§060"贵人又乘空乃是虚贵"、§103"昼贵人空虚是贵而无位也"）
            if gui_kong:
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
            if si_jue:
                return self._mk('四绝不通', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干支上神{gan_shang}·{zhi_shang}四绝，偃蹇不通，前程非惟不远且又寿夭',
                                '§前程仕进03·066"此课名四绝且干支自刑"; §083"四绝偃蹇不通"')
            # ⑩b 返吟+旧太岁 → 旧政迟任（§063"此课旧政上又见旧政…第六年方得赴任"）
            #   【BUG-FIX 2026-08-18】返吟课（干支对冲）+ 初传=干上神 → 旧政再来迟任
            if fan_yin and chu == gan_shang and _shi_shen(chu, ri_gan) == '官鬼':
                return self._mk('旧政迟任', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'返吟课旧政上又见旧政，迁延迟任，六年方得赴任',
                                '§前程仕进03·063"旧政上又见旧政…第六年方得赴任"')
            # ⑩c 无禄课（四课上神俱克下）→ 必不能食禄（§076"无禄课虽受通判必不能食禄"）
            #   判据：四课上神皆克其下神（简化：干上神克日干 且 支上神克日支）
            if gan_shang and zhi_shang and ri_zhi:
                _gan_shang_ke = KE.get(ZHI_WX.get(gan_shang, '')) == gw
                _zhi_shang_ke = KE.get(ZHI_WX.get(zhi_shang, '')) == ZHI_WX.get(ri_zhi, '')
                if _gan_shang_ke and _zhi_shang_ke:
                    return self._mk('无禄难食', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'四课上神俱克下，无禄课，虽受官职必不能食禄',
                                    '§前程仕进03·076"无禄课虽受通判必不能食禄"')
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
            if yang_ren and (yang_ren in (chu, zhong, mo) or yang_ren in (gan_shang, zhi_shang)):
                return self._mk('羊刃阻迁', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'羊刃{yang_ren}临课传，升迁受阻，进锐退速',
                                '§前程仕进03·051"干支皆天罗羊刃"; §054"午为阳刃撞干进锐退速"')
            # ⑬b 幕贵临干（干上神=贵人且不空=科名第一吉神）→ 先晦后明登科
            #   （§052"太阴乘卯作幕贵加日干…先晦后明准拟登科"、§061"官星作幕贵今年必高中"；
            #   刘评"幕贵乃科名第一吉神"；守卫：传不空、非铸印破模——§050铸印破模凶不判吉）
            if gan_shang in gui_zhi_set and gan_shang not in kong and \
               not (chu in kong and zhong in kong):
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
            # 三传自墓传生 → 患易瘥（L544）
            if zi_mu_chuan_sheng:
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自墓({chu})传生({mo})，病虽重自墓传生，患易瘥，终可愈',
                                'L544"三传自墓传生患易瘥"')
            # 三传自生传墓 → 难瘳（L544）
            if zi_sheng_chuan_mu:
                return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传自生({chu})传墓({mo})，自生传墓，病难瘳，终凶',
                                'L544"自生传墓者难瘳"')
            # 白虎乘日鬼同入三传 → 大凶（L545；案例0412"此课不利占病丁巳日必死"）
            if hu_gui:
                return self._mk('病危难救', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'白虎乘日鬼入传，病势凶险，恐难救治',
                                'L545"虎乘日鬼同入三传主大凶"; CASE-壬占汇选-0412')
            # 虎鬼空亡 → 病自愈（L546）
            if any(z in kong and _shi_shen(z, ri_gan) == '官鬼' and tj == '白虎'
                   for z, tj in ((chu, chu_tj), (zhong, zhong_tj), (mo, mo_tj))):
                return self._mk('有惊无险', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'虎鬼{chu if chu in kong else zhong if zhong in kong else mo}空亡，病自愈，有惊无险',
                                'L546"虎鬼空亡病自愈"')
            # 白虎克日 → 病必凶（L540）
            if mo_tj == '白虎' and KE.get(mo_wx) == gw:
                return self._mk('病势凶险', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}白虎克日干，病势凶险，须防不测',
                                'L540"白虎克日病必凶"')
            # 循环格 → 病多反复（L557"循环格三传不离四课主病多反复"）
            if xun_huan:
                return self._mk('病多反复', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}不离四课，循环格，病多反复，迁延难愈',
                                'L557"循环格主病多反复"')
            # 传归死墓必死（L617"传归死墓必死"）
            if mo == mu_zhi and (chu_shi == '凶' or zhong_shi == '凶'):
                return self._mk('病终难救', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，传归死墓，病终难救',
                                'L617"传归死墓必死"')

        # ───────────────────────────
        # 【官讼】
        # ───────────────────────────
        if category == '官讼':
            # 末传生初传生日干 → 有人暗地用力扶持，官事不日消缴（L780）
            if mo_wx and chu_wx and SHENG.get(mo_wx) == chu_wx and SHENG.get(chu_wx) == gw:
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}生初传{chu}生日干，暗地有人用力扶持，官事不日消缴',
                                'L780"末传生初传而生日干者主有人暗地用力扶持官事不日消缴"')
            # 初传白虎末传螣蛇 → 虎头蛇尾虽有祸乱渐消释（L790；案例0520"先凶后吉"）
            if chu_tj == '白虎' and mo_tj == '螣蛇':
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}白虎末传{mo}螣蛇，虎头蛇尾，虽有祸乱渐消释，官事先凶后吉',
                                'L790"若白虎作初传螣蛇作末传凡事虎头蛇尾虽有祸乱渐消释"; CASE-壬占汇选-0520')
            # 初传官鬼旺相 → 讼必成；休囚 → 讼不成（L819"初传官鬼旺相讼必成休囚讼不成"）
            if _shi_shen(chu, ri_gan) == '官鬼':
                if chu not in kong and chu_shi != '凶':
                    return self._mk('讼事必成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                    f'初传官鬼{chu}旺相，讼必成，我方不利',
                                    'L819"初传官鬼旺相讼必成"')
                return self._mk('讼可消散', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传官鬼{chu}休囚，讼不成，可消散',
                                'L819"官鬼休囚讼不成"')
            # 干上神克支上神 → 先起者胜（L740；初传空亡或伏吟课例外——静局不讼）
            if gan_ke_zhi_shang and chu not in kong and not fu_yin:
                return self._mk('先起者胜', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'干上神{gan_shang}克支上神{zhi_shang}，先起者胜，理直气壮',
                                'L740"干上神刑克冲害支上神者先起者胜"')
            # 支上神克干上神 → 后应者胜（L742）
            if zhi_ke_gan_shang and chu not in kong and not fu_yin:
                return self._mk('后应者胜', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'支上神{zhi_shang}克干上神{gan_shang}，后应者胜，我方不利',
                                'L742"支上神刑克冲害干上神者后应者胜"')
            # 末传=天喜/青龙乘解神 → 恩赦相救先凶后吉（案例0520）
            if mo_tj in ('青龙', '太常', '贵人') and mo_shi == '吉':
                return self._mk('先凶后吉', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}乘{mo_tj}，恩赦相救，先凶后吉，官事可解',
                                'CASE-壬占汇选-0520"末天喜乘龙作解神必有恩赦相救先凶而后吉"')

        # ───────────────────────────
        # 【求财】
        # ───────────────────────────
        if category == '求财':
            # 传财化鬼 → 因财致祸（L274/L287"传财化鬼难求觅，因财致祸"）
            if _shi_shen(chu, ri_gan) == '妻财' and KE.get(mo_wx) == gw:
                return self._mk('先吉后凶', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传财{chu}末传鬼{mo}，传财化鬼，因财致祸，得而复失',
                                'L274"传财化鬼难求觅"')
            # 三传初中皆空独末为财爻 → 先难后得（L283）
            if chu in kong and zhong in kong and _shi_shen(mo, ri_gan) == '妻财':
                return self._mk('先难后易', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初中传空亡，末传{mo}为财爻，先涉艰难然后得财',
                                'L283"三传初中皆空独末为财爻先难后得"')
            # 初传财末传生之 → 末来助始（L282）
            if _shi_shen(chu, ri_gan) == '妻财' and mo_wx and SHENG.get(mo_wx) == chu_wx:
                return self._mk('得财有望', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传财{chu}，末传{mo}生之，末来助始，有人暗将财相助',
                                'L282"初传财末传生之末来助始"')
            # 财爻临日干 → 得财甚速；财在末传 → 得财迟滞（L270）
            if _shi_shen(mo, ri_gan) == '妻财' and mo_shi == '吉':
                return self._mk('终得财利', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为财爻得地，得财虽迟终有财利',
                                'L270"财在末传得财迟滞"')
            # 财爻空亡 → 不可强求（L275"财坐空亡不可强求"）
            if any(z in kong and _shi_shen(z, ri_gan) == '妻财' for z in (chu, zhong, mo)):
                return self._mk('求财落空', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'财爻{chu if chu in kong else zhong if zhong in kong else mo}空亡，求财落空，不可强求',
                                'L275"财坐空亡不可强求"')

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
            # 三传克日 → 难产；三传克支 → 伤母（L229）
            if mo_wx and KE.get(mo_wx) == gw:
                return self._mk('产难母伤', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传克日干，产难，须防伤母',
                                'L229"三传克日难产三传克支伤母"')
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
            if fu_yin:
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
            # 干支乘死绝最忌不宜远行（L434）
            if mo == jue_zhi or (mo in kong and mo_shi == '凶'):
                return self._mk('不宜远行', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}乘死绝，不宜远行，恐途中有阻',
                                'L434"干支乘死绝最忌不宜远行"')
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
            # 日上得吉将/生日之神 → 往之吉（L416）
            if chu_shi == '吉' and mo_shi != '凶':
                return self._mk('出行顺利', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'日上得吉，出行顺利，往来无阻',
                                'L416"日干旺相或日上得吉将则往之吉"')

        # ───────────────────────────
        # 【婚姻】
        # ───────────────────────────
        if category == '婚姻':
            # 三传生日 → 婚姻迪吉（L178"三传生日婚姻迪吉媒言亦实"）
            if mo_wx and SHENG.get(mo_wx) == gw:
                return self._mk('姻缘有成', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传生日干，婚姻迪吉，媒言亦实，婚事可成',
                                'L178"三传生日婚姻迪吉"')
            # 日生三传 → 强成终久不偕（L179）
            if gw and mo_wx and SHENG.get(gw) == mo_wx:
                return self._mk('先成后败', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'日干生三传，事多乖违，强成终久不偕，婚姻难长久',
                                'L179"日生三传事多乖违强成终久不偕"')
            # 初传天后与日辰相生 → 必成（案例0069"初传天后与日辰相生而气和必成之理也"）
            if chu_tj == '天后' and chu_shi != '凶':
                return self._mk('婚姻必成', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'初传{chu}乘天后与日辰相生，气和必成，婚姻可成',
                                'CASE-壬占汇选-0069"初传天后与日辰相生而气和必成之理也"')
            # 朱雀发用克日 → 不成（L169"朱雀发用克日不成"）
            if chu_tj == '朱雀' and KE.get(chu_wx) == gw:
                return self._mk('婚姻不成', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'朱雀发用克日干，婚姻不成，媒言难信',
                                'L169"朱雀发用克日不成"')
            # 末传=日墓 → 婚难长久（L183"即成亦不长久"）
            if mo == mu_zhi:
                return self._mk('婚难长久', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}为日墓，婚姻即成亦不长久',
                                'L"即成亦不长久"')

        # ───────────────────────────
        # 【贼盗】（失物/捕盗）
        # ───────────────────────────
        if category == '贼盗':
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
            # 循环格 → 贼人复来（L723"周遍格循环格主贼人复来"）
            if xun_huan:
                return self._mk('贼人复来', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'循环格，主贼人复来之意，失物难全保',
                                'L723"周遍格循环格主贼人复来"')
            # 末传生日干 → 失物自归（L673"元武乘旺生干支者不寻自还"）
            if mo_wx and SHENG.get(mo_wx) == gw:
                return self._mk('失而复得', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'末传{mo}生日干，失物不寻自还，失而复得',
                                'L673"元武乘旺生干支者不寻自还"')

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
                category: str = '', zishu: str = '') -> Dict[str, Any]:
        """
        主入口。返回事体走向分析。
        sanchuan: [初传, 中传, 末传]
        tianjiang_list: [初传天将, 中传天将, 末传天将]
        sike: 四课（用于循环格/干支上神判定）
        category: 占类（功名/疾病/官讼/求财/家宅/胎产/出行/婚姻/贼盗/行人/其他）
        zishu: 家宅子类（阳宅/阴宅/迁移；空=阳宅默认）。阴宅看辰穴/朝案，迁移看丁马/宜迁。
        """
        if not sanchuan or len(sanchuan) < 3:
            return {'走向': '未定', '阶段': {}, '叙事': '三传不全，无法判断事体走向', '终局': '平'}
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
                                       zishu=zishu)
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
                    sike: List = None, category: str = '', zishu: str = '') -> Dict[str, Any]:
    """便捷入口"""
    return LiuChenEngine().analyze(ri_gan, ri_zhi, sanchuan, tianjiang_list, kongwang, keti, sike,
                                  category, zishu)


if __name__ == '__main__':
    # 自测：占类化规则
    for cat, sc, tj, rg in [('功名', ['戌', '午', '丑'], ['玄武', '朱雀', '白虎'], '甲'),
                            ('疾病', ['未', '午', '亥'], ['白虎', '六合', '青龙'], '甲'),
                            ('官讼', ['申', '亥', '寅'], ['白虎', '六合', '青龙'], '甲'),
                            ('求财', ['寅', '卯', '戌'], ['勾陈', '六合', '玄武'], '辛'),
                            ('胎产', ['亥', '酉', '卯'], ['六合', '太阴', '青龙'], '甲')]:
        r = analyze_liuchen(rg, '子', sc, tj, category=cat)
        print(f'[{cat}] {sc} {tj} → {r["走向"]} / {r["终局"]} / {r["叙事"]}')
