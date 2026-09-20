# -*- coding: utf-8 -*-
"""救神具象化引擎（jiuzhu）——纯叙事 / 展示层，**不进评分链**。

方法链（憨爷 2026-09-12 指令「救神要具象化」＋ 原文逐条印证）：

    ① 取救神（解神／子孙／日德／吉将／生气／天医）—— 须落【七处】且不空亡才「能用」
    ② 乘何将  → 定人事／对象   （鬼乘天乙乃神祇；天后→长辈；太常→祭祀神；白虎→伤鬼；天空→佛位）
    ③ 再看【阴神】（＝该支的天盘上神）→ 更精细定位处所
       （午为离明·明堂 → 家堂神；丑为明堂；子为明堂时；未主祭祀；寅申为寺观；巳为祭祀；
        卯为门户/前门；辰为山岗/天牢；酉为内门/私门；戌为堂/楼阁/城廓；亥为天门/堂庙之宫）
       ⇒ **十二支宫位类象已补齐**（2026-09-12，各行号见 GONG_XIANG 注释，均有原文）
    ④ 出化解之法（修设功德安慰宅神／阴祭私祷／敬重长辈／祭祀家神／求医服药…）

原文出处（**逐条**，行号已核）：

  * 解神取法 —— `通解_下.txt` **L13210** 注⑦：「**用神被月建冲破谓之解神，又名四时空亡。**」
      ∴ 解神 ＝ 月建之冲（月建＝寅 ⇒ 解神＝申，即憨爷所举「申为解神」）。
  * 救神减凶 —— `通解_上.txt` **L978**：「凡占讼、占病，忌鬼入传临日，**见子孙及救神减凶**。」
  * 子孙为药 —— `通解_上.txt` **L4145**：「**子为杀鬼之神，主有良医解救。**」「贵医，指贵人与天医、地医。」
  * 德贵制鬼 —— `通解_上.txt` **L1001**：「**凡贵德临身制鬼者反吉。**」
  * 吉将解神 —— `通解_上.txt` **L5351**：「或逢**龙、常、阴、后、六合吉将，生气、解神**、天德、月喜、德神、合神、吉神，得一在末传，可化凶为吉。」
  * 救神落空无效 —— `通解_上.txt` **L980**：「若落空，鬼反难捕捉。」；疏正 **L8059**：「奈寅落天中，更坐绝乡，既不得地生根，又怎么能起而救神。」
  * 家内人解救 —— `通解_上.txt` **L995**：「凡鬼临日干，得**支上神救者**，主一切事自外来，**要家内人解救**。」「**家鬼弄家神**，有救无祸，无救有祸。」
  * **鬼乘天乙乃神祇** —— `通解_中.txt` **L6157/6158**：「**鬼乘天乙乃神祇**……占病必是**神祇为害**，如临宅上者，必是**家堂神像不肃**而致病患，宜**修设功德安慰宅神**，庶得无咎。」
      （姊妹条：`通解_上.txt` **L7540 / L8122**：「六丁日贵作日鬼临日，占官利，占病**神祇所害**，临支**家神致病**，宜**修设安慰宅神**则吉。」）
  * 夜鬼主神祇 —— `通解_上.txt` **L976**：「凡**昼鬼主公讼是非，夜鬼主神祇妖祟**。」
  * 阴鬼神祇 —— `通解_中.txt` **L2328**：「**阳鬼公讼是非，阴鬼神祇星宿。**」
  * 天空评佛位 —— `通解_上.txt` **L3931**：「天乙乘鬼断神祇，**天空作官评佛位**。」
  * 阴祭私祷 —— `通解_上.txt` **L7529**：「又**贵人坐狱为受贿，宜阴祭私祷**。」
  * 白虎伤鬼祭乃宁 —— `通解_上.txt` **L1845**：「病者目头痛疽苦，**崇犯伤鬼祭乃宁**。」
  * 太常本祭祀神 —— `断案疏正_全文.txt` **L7993**：「盖用爻**太常本祭祀神**，巳火又是日德、生气……」
  * 太常须祭祷 —— `通解_下.txt` **L1501**：「然究竟夫鬼病无忧，**太常须祭祷**，脱多宜补剂自愈。」「其家**祭祷方安**。」
  * 天后（＝神后）类象 —— `通解_上.txt` **L2498**：「神后类象……为**后妃**、淫女、乳媪、媒妁、幼女、孩童、**老妇**、嫁妇、军妇、孀妇、娼妇、婢妾、**翁婆**、乐工、染匠、盗贼、驼子、**邪师、僧尼**、溺死，为奸邪、阴小、胎产、女经、淫洗、**私祷**……」
  * 午为离明·明堂 —— `通解_上.txt` **L6169 / L6203**：「惟**午加卯为明堂**，主万事昌隆。盖**午为离明**，卯为天驷，**房心明堂之宿**，遇凶亦吉也。」
  * 丑为明堂 —— `通解_上.txt` **L1725**：「**勾陈主战斗，丑为明堂**，封功决罪。」；`通解_中.txt` **L9113**：「**勾陈主明堂**，阴阳二将见财官、幕贵。」
  * 子为明堂（三奇）—— `通解_上.txt` **L7104 / L7123**：「又**丑为玉堂，子为明堂**」；`通解_下.txt` **L11232**：「子为明堂时。」
  * 未主祭祀 —— `通解_上.txt` **L2009 / L2011**：「小吉……**羊酒祠祷祭神祇**。」「天乙加未，玄武居亥，为三合，主**祠祷神祇**。」
  * 寅申为寺观 —— `通解_下.txt` **L4556**：「**寅申为寺观**，申乃空亡，是空中神祇来克我也。」
  * **阴神分层（内外明堂）** —— `通解_上.txt` **L3868**：「以勾陈阳神看**内明堂**，以勾陈**阴神**看**外明堂**。」
      ∴ **阳神定内、阴神定外** —— 这就是「再看阴神作更精细定位」的原文依据。
  * 生气 —— `通解_下.txt` **L13210** 注⑫：「生神者，**生气**也，正七月子午，二八月丑未，三九月寅申，四十月卯酉，五十一月辰戌，六十二月巳亥。」
      ∴ 生气 ＝ 月建前二辰（逆数；月建寅 ⇒ 生气子）。
  * 天医 —— 🔴 **口径以《断案疏正》为准**（2026-09-12 憨爷拍板「以月建前二辰为准！」）：
      `断案疏正_全文.txt` **L13249**《心镜》：「**日辰月建前居二，此是天医对地医**。」
      同书 **L13250-13251** 实例：「腊月以**卯**为月之天医」（丑月+2＝卯）／「卯日以**巳**为日之天医，冲取地医，故**亥**作地医」；
      同书 **L5272**：「但**天医居月建前二辰**。」
      ∴ 天医 ＝ 月建 + 2（顺数）；地医 ＝ 天医对冲（月建 + 8）。
      ⚠️ 弃《通解_下》L13210 注⑧「天医者，正月为戌…顺行十二辰＝月建后四辰」一说（两说为同一对宫组合的位置对调）。
  * 吉将表 —— `通解_上.txt` **L5351**：吉将＝「**龙、常、阴、后、六合**」；另加**贵人**（L1001「贵德临身制鬼者反吉」）。

⚠️ 本模块**只产出叙事与建议**；`jiuzhu` **不进评分链**（与 `tianjiang_gongwei` / `leixiang_chain` 同铁律）。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── 基础映射（复用引擎真源，避免自造）──
try:
    from engine.kege_shensha import ZHI_WX, GAN_WX, WX_KE, wang_xiang as _wang_xiang
except Exception:  # pragma: no cover
    ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
              '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
    GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
              '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    _wang_xiang = None

ZHI12 = '子丑寅卯辰巳午未申酉戌亥'
LIU_CHONG = {'子': '午', '丑': '未', '寅': '申', '卯': '酉', '辰': '戌',
             '巳': '亥', '午': '子', '未': '丑', '申': '寅', '酉': '卯',
             '戌': '辰', '亥': '巳'}

# ── 月建 → 生气（月建前二辰·逆数）／天医（月建前二辰·顺数）／地医（天医对冲）──
def sheng_qi(yue_jian: str) -> str:
    """生气＝月建前二辰（通解_下 L13210 注⑫：正七月子午…六十二月巳亥）。"""
    if yue_jian not in ZHI12:
        return ''
    return ZHI12[(ZHI12.index(yue_jian) - 2) % 12]


def tian_yi_med(yue_jian: str) -> str:
    """天医＝月建前二辰（月建+2）。

    🔴 口径以《断案疏正》为准（2026-09-12 憨爷拍板：「以月建前二辰为准！」）：
      * `断案疏正_全文.txt` L13249《心镜》：「**日辰月建前居二，此是天医对地医**。」
      * 同书 L13250-13251 实例：「腊月以**卯**为月之天医」（丑月+2＝卯）、
        「卯日以**巳**为日之天医，冲取地医，故**亥**作地医」（卯+2＝巳，巳冲＝亥）。
      * 同书 L5272：「但**天医居月建前二辰**。」
    ⚠️ 弃《通解_下》L13210 注⑧「正月为戌…顺行十二辰＝月建后四辰」一说。
    """
    if yue_jian not in ZHI12:
        return ''
    return ZHI12[(ZHI12.index(yue_jian) + 2) % 12]


def di_yi_med(yue_jian: str) -> str:
    """地医＝天医对冲（《心镜》「冲取地医」，疏正 L13251「冲取地医，故亥作地医」）。"""
    t = tian_yi_med(yue_jian)
    return LIU_CHONG.get(t, '')


# ── 乘将 → 人事／对象（第 ① 层具象化）──
JIANG_XIANG = {
    '贵人': ('神祇、尊长、贵官', '神祇为害 → 宜修设功德、安慰宅神；或求贵人转圜',
             '通解_中 L6157/L6158「鬼乘天乙乃神祇…宜修设功德安慰宅神」'),
    '太阴': ('阴神、阴私、暗昧之神', '敬祀鬼神（阴神主神祇星宿）',
             '通解_中 L2328「阴鬼神祇星宿」'),
    '天后': ('后妃、老妇、翁婆、母、僧尼、私祷', '敬重长辈（母／老妇／僧尼），或托媒妁老妇私祷',
             '通解_上 L2498「神后类象…老妇…翁婆…僧尼…私祷」'),
    '太常': ('祭祀神、酒食、父母、衣冠', '祭祷、祀先（太常本祭祀神）',
             '疏正 L7993「太常本祭祀神」；通解_下 L1501「太常须祭祷」'),
    '白虎': ('伤鬼、道路、疾病、凶丧', '祟犯伤鬼 → 祭乃宁',
             '通解_上 L1845「崇犯伤鬼祭乃宁」'),
    '天空': ('佛位、虚诈、奴仆', '评佛位／修斋设醮',
             '通解_上 L3931「天空作官评佛位」'),
    '勾陈': ('官讼、田土、明堂', '勾陈论明堂 —— 公门/祠堂之事',
             '通解_中 L9113「勾陈主明堂」'),
    '螣蛇': ('惊恐、怪异、邪祟、虚惊', '厌祷禳解、书符合药',
             '通解_上 L8367「合药书符、祈祷等事皆吉」'),
    '朱雀': ('文书、口舌、词讼', '祷祝、上文書',
             '通解_中 L2695「宜托人求贵暗祷」'),
    '青龙': ('财帛、喜事、吉庆', '—', ''),
    '六合': ('和合、媒妁、小儿、子孙', '托人说合 / 六合主子息',
             '通解_上 L5351（吉将）'),
    '玄武': ('盗贼、暗昧、水祟', '—', ''),
}

# 吉将（通解_上 L5351「龙、常、阴、后、六合吉将」＋ 贵人）
JI_JIANG = ('青龙', '太常', '太阴', '天后', '六合', '贵人')

# ── 阴神宫位类象（第 ② 层具象化，仅收有原文者）──
GONG_XIANG = {
    '午': ('离明 · 明堂（房心明堂之宿）', '祭祀家中神明／家堂神像之属',
           '通解_上 L6169/L6203「午为离明…房心明堂之宿」'),
    '丑': ('明堂（勾陈主明堂）', '公门、朝堂、封功决罪之事',
           '通解_上 L1725「丑为明堂，封功决罪」'),
    '子': ('明堂时（三奇之明堂）', '祷祝鬼神、妇人布帛裁制之属',
           '通解_上 L7104「子为明堂」；通解_下 L11232；金锁玉连环「子…祷祝鬼神」'),
    '未': ('祠祷祭神祇 · 五味酒食', '祭祀、祠祷、酒食宴饮之属',
           '通解_上 L2009/L2011「羊酒祠祷祭神祇」'),
    '寅': ('寺观', '寺观、僧道之所',
           '通解_下 L4556「寅申为寺观」'),
    '申': ('寺观（空中神祇）', '寺观、虚无空中之神祇',
           '通解_下 L4556「寅申为寺观，申乃空亡，是空中神祇来克我也」'),
    '巳': ('祭祀（日德生气）', '祭祀、禳谢之属',
           '疏正 L7993「巳火又是日德、生气」'),
    # ── 2026-09-12 依憨爷「继续挖原文补齐」新增 5 支（卯/辰/酉/戌/亥），各行号已实证 ──
    '卯': ('门户 · 前门（日出之门）', '门户、宅舍、出入之口 —— 家宅门庭、前门、出入之事',
           '疏正 L2356「卯为宅、为门户」；L10620「酉为内门，卯为前门」；'
           '通解_上 L1789「卯为门户，克伤故主暴客」；L1392「卯酉为…门户之象」'),
    '辰': ('山岗 · 天牢 · 监司（官府）', '岳庙山岗、牢狱官讼、田宅之事',
           '疏正 L5138「辰为山岗，寅为庙」；L6444「辰为监司，又为牢」；'
           '通解_中 L1548「辰为天牢」'),
    '酉': ('门户 · 内门 · 私门（归计门／太阴之门）', '门户口舌、女子私门、归计之事',
           '疏正 L10620「酉为内门」；L1513「酉为归计门」；L761「以酉为太阴之门」；'
           'L4069「末传酉为妇女，又是私门」'),
    '戌': ('堂 · 楼阁 · 城廓 · 寺观冈岭（地网／牢狱）', '堂上、楼阁高处、城廓、寺观冈岭、狱讼之事',
           '疏正 L1718「戌为堂」；L14747「戌为楼阁，故藏高处阁上」；L7169「戌为城廓」；'
           'L6067「戌乃寺观冈岭」；通解_中 L1548「戌为地网」；通解_上 L2582「戌为牢狱」'),
    '亥': ('天门 · 天庭 · 元穹宫（堂庙之宫）', '天门天庭、堂庙高位、厕溷之事',
           '疏正 L6110/L7291「（末）亥为天门」；L11487「亥为天庭」；'
           'L6185「亥为元穹宫，亦主八座」；L1516「亥为厕」；'
           '通解_上 L1392「已亥为堂庙之宫，因此为征召高位之所」；L1400「亥为天门，故曰登明」'),
}


def _zhi_wx(z: str) -> str:
    return ZHI_WX.get(z, '')


def _is_gui(zhi: str, ri_gan: str) -> bool:
    """该支是否为「日鬼」（支五行克日干五行）。"""
    zw, gw = _zhi_wx(zhi), GAN_WX.get(ri_gan, '')
    return bool(zw and gw and WX_KE.get(zw) == gw)


def _is_zi_sun(zhi: str, ri_gan: str) -> bool:
    """该支是否为「子孙」（日干生者）。"""
    zw, gw = _zhi_wx(zhi), GAN_WX.get(ri_gan, '')
    try:
        from engine.kege_shensha import WX_SHENG as _S
    except Exception:
        _S = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    return bool(zw and gw and _S.get(gw) == zw)


class JiuzhuEngine(object):
    """救神具象化：取救神 → 乘将定人事 → 阴神定处所 → 出化解之法。"""

    def build(self, result, ben_ming_zhi='', xing_nian_zhi=''):
        result = result or {}
        tjp = result.get('tiandi_pan') or {}
        tjm = result.get('tianjiang_map') or {}
        sz = result.get('sizhu') or {}
        ri_gz = str(sz.get('日') or '')
        ri_gan = ri_gz[:1]

        # 月建（＝月令，憨爷铁律：当令指月建）
        yue_jian = ''
        try:
            from engine.bifa_detector import get_yue_jian_from_yuejiang as _gyj
            yue_jian = str(_gyj(result.get('yuejiang') or '') or '')
        except Exception:
            yue_jian = ''

        # 旬空
        kong = set()
        try:
            from engine.bifa_detector import get_xun_kong as _gxk
            kong = set(x for x in (_gxk(ri_gz) or ('', '')) if x)
        except Exception:
            pass

        # 三传
        sc = result.get('sanchuan') or {}
        chuan = [str(sc.get(k) or '') for k in ('初传', '中传', '末传')]
        chuan = [c for c in chuan if c]

        # 四课上神（`sike` 元素 = (课名, 上神, 下神, 天将)，sk[1]＝上神）
        shang_shen = []
        for e in (result.get('sike') or []):
            try:
                up = e[1] if isinstance(e, (list, tuple)) and len(e) > 1 else (e.get('上神') if isinstance(e, dict) else '')
            except Exception:
                up = ''
            if up:
                shang_shen.append(str(up))

        # 七处（支）：四课上神 + 三传 + 本命上神 + 行年上神
        qi_chu = list(shang_shen) + chuan
        bm_up = str(tjp.get(str(ben_ming_zhi)) or '') if ben_ming_zhi else ''
        xn_up = str(tjp.get(str(xing_nian_zhi)) or '') if xing_nian_zhi else ''
        if bm_up:
            qi_chu.append(bm_up)
        if xn_up:
            qi_chu.append(xn_up)
        qi_chu_set = set(x for x in qi_chu if x)
        # 七处之「阴神」集合（＝七处各支的天盘上神）
        yin_of_qichu = set(str(tjp.get(z) or '') for z in qi_chu_set)
        yin_of_qichu.discard('')

        # ── ① 救神候选 ──
        cands = []

        def _cand(zhi, name, why, src):
            if zhi and zhi in ZHI12:
                cands.append({'zhi': zhi, 'name': name, 'why': why, 'src': src})

        if yue_jian:
            _cand(LIU_CHONG.get(yue_jian, ''), '解神',
                  '用神被月建冲破谓之解神（月建%s ⇒ 解神%s）' % (yue_jian, LIU_CHONG.get(yue_jian, '')),
                  '通解_下 L13210 注⑦「用神被月建冲破谓之解神，又名四时空亡」')
            _cand(sheng_qi(yue_jian), '生气', '生气（月建%s前二辰）' % yue_jian,
                  '通解_下 L13210 注⑫')
            _cand(tian_yi_med(yue_jian), '天医', '天医（月建%s前二辰）' % yue_jian,
                  '疏正 L13249《心镜》「日辰月建前居二，此是天医对地医」；L13250-13251 实例；L5272「天医居月建前二辰」')
            _cand(di_yi_med(yue_jian), '地医', '地医（天医对冲）',
                  '疏正 L13251「冲取地医，故亥作地医」')
        # 子孙爻（日干生者）——落七处者
        for z in (qi_chu_set | yin_of_qichu):
            if _is_zi_sun(z, ri_gan):
                _cand(z, '子孙', '日干%s生%s（子孙克鬼，主良医解救）' % (ri_gan, z),
                      '通解_上 L4145「子为杀鬼之神，主有良医解救」')
        # 日德
        try:
            from engine.shen_sha_calculator import ShenShaCalculator as _SSC
            _de = _SSC().get_ri_de(ri_gan)
            _cand(str(_de or ''), '日德', '日干%s之德神' % ri_gan,
                  '通解_上 L1001「贵德临身制鬼者反吉」')
        except Exception:
            pass
        # 吉将落七处
        for z in qi_chu_set:
            jj = str(tjm.get(z) or '')
            if jj in JI_JIANG:
                _cand(z, '吉将(%s)' % jj, '七处%s乘吉将%s' % (z, jj),
                      '通解_上 L5351「龙、常、阴、后、六合吉将…得一在末传，可化凶为吉」')

        # ── ② 定落点（七处 / 阴神）+ 空亡 + 旺衰 ──
        items, seen = [], set()
        for c in cands:
            z = c['zhi']
            if not z or z in seen:
                continue
            if z in qi_chu_set:
                via = '七处'
            elif z in yin_of_qichu:
                via = '阴神'
            else:
                continue
            seen.add(z)
            jiang = str(tjm.get(z) or '')
            jx, jsug, jsrc = JIANG_XIANG.get(jiang, ('', '', ''))
            yin = str(tjp.get(z) or '')
            yin_jiang = str(tjm.get(yin) or '')
            gx, gsug, gsrc = GONG_XIANG.get(yin, ('', '', ''))
            ws = ''
            if _wang_xiang is not None and yue_jian:
                try:
                    ws = str(_wang_xiang(z, yue_jian) or '')
                except Exception:
                    ws = ''
            is_kong = z in kong
            gui = _is_gui(z, ri_gan)

            # ── ③ 化解之法合成：乘将（对象·手段）＋ 阴神宫位（具体处所）＞ 神煞性质 ──
            #      🔴 依原文逐将分派，**勿以一类代全**（「鬼乘天乙乃神祇」特指贵人，非太常）。
            adv, adv_src = [], []
            if is_kong:
                adv.append('救神落空亡 —— 力薄难救，须另觅有气之救神')
                adv_src.append('通解_上 L980「若落空，鬼反难捕捉」')
            else:
                _J2A = {
                    '贵人': ('敬祀鬼神 · 修设功德、安慰宅神（鬼乘天乙乃神祇）', '通解_中 L6157/L6158'),
                    '太阴': ('敬祀鬼神（阴神主神祇星宿）', '通解_中 L2328「阴鬼神祇星宿」'),
                    '天空': ('修斋设醮 · 评佛位（天空作官评佛位）', '通解_上 L3931'),
                    '天后': ('敬重长辈（母/老妇/翁婆），或托僧尼私祷', '通解_上 L2498「神后类象」'),
                    '太常': ('祭祷、祀先（太常本祭祀神）', '疏正 L7993；通解_下 L1501「太常须祭祷」'),
                    '白虎': ('祭乃宁（祟犯伤鬼）', '通解_上 L1845「崇犯伤鬼祭乃宁」'),
                    '螣蛇': ('厌祷禳解、书符合药', '通解_上 L8367「合药书符、祈祷等事皆吉」'),
                    '朱雀': ('宜托人求贵暗祷', '通解_中 L2695「宜托人求贵暗祷」'),
                    '勾陈': ('公门／祠堂之事（勾陈主明堂）', '通解_中 L9113「勾陈主明堂」'),
                    '六合': ('托人说合（六合主子息）', '通解_上 L5351（吉将）'),
                }
                _a = _J2A.get(jiang)
                if _a:
                    adv.append(_a[0])
                    adv_src.append(_a[1])
                if c['name'] in ('子孙', '天医', '地医'):
                    adv.append('延医服药（子孙/天医为药，子为杀鬼之神）')
                    adv_src.append('通解_上 L4145「子为杀鬼之神，主有良医解救」')
                if gx:
                    adv.append('何处／何物：%s → %s' % (gx, gsug))
                    adv_src.append(gsrc)
                if jx and not _a:
                    adv.append('何人／何事：%s' % jx)
                    adv_src.append(jsrc)
                if not adv:
                    adv.append('以救神所在之支所主，随占类善用之')
                    adv_src.append('')
            chain = '%s（%s）' % (z, c['name'])
            if jiang:
                chain += ' → 乘%s（%s）' % (jiang, jx or '—')
            if yin:
                chain += ' → 阴神%s' % yin + ('（%s）' % gx if gx else '')
                if yin_jiang:
                    chain += '·乘%s' % yin_jiang
            items.append({
                'zhi': z, 'name': c['name'], 'why': c['why'], 'src': c['src'], 'via': via,
                'jiang': jiang, 'jiang_xiang': jx, 'jiang_src': jsrc,
                'yin_zhi': yin, 'yin_jiang': yin_jiang,
                'gong': gx, 'gong_xiang': gsug, 'gong_src': gsrc,
                'gui': gui, 'kong': is_kong, 'wangshuai': ws,
                'advice': adv, 'advice_src': adv_src, 'chain': chain,
            })

        # 排序：不空 & 落七处 & 乘凶将者优先（＝最切要的救神）
        items.sort(key=lambda it: (it['kong'], it['via'] != '七处', not it['gui']))
        items = items[:6]

        effective = any((not it['kong']) for it in items)
        note = ''
        if items:
            top = items[0]
            note = '救神：' + top['chain']
            if not effective:
                note += ' ⚠ 诸救神皆落空亡 —— 力薄，宜从速另图。'
        else:
            note = '课传七处未见成气之救神（解神/子孙/日德/吉将）—— 无解可言，以避为宜。'

        return {
            'items': items,
            'primary': items[0] if items else None,
            'effective': effective,
            'yue_jian': yue_jian,
            'jieshen': LIU_CHONG.get(yue_jian, '') if yue_jian else '',
            'kong': sorted(kong),
            'note': note,
            'rule': ('①取救神（解神＝月建之冲；子孙；日德；吉将；生气；天医），须落七处且不空亡才「能用」；'
                     '②看乘何将定人事（鬼乘天乙乃神祇／天后→长辈／太常·白虎→祭祀／天空→佛位）；'
                     '③再看【阴神】＝该支天盘上神，定更精细处所（十二支宫位类象已补齐，见 GONG_XIANG：'
                     '午为离明·明堂→家堂神；丑为明堂；子为明堂时；未主祭祀；寅申为寺观；巳为祭祀；'
                     '卯为门户；辰为山岗/天牢；酉为内门/私门；戌为堂/楼阁/城廓；亥为天门/堂庙之宫）；'
                     '④出化解之法。出处：通解_下 L13210（解神/生气/天医）、通解_上 L978·L995·L1001·L4145·L5351、'
                     '通解_上 L2498（神后类象）、通解_中 L6157/6158（鬼乘天乙乃神祇）、通解_上 L3868（阴神看外明堂）、'
                     '通解_上 L6169/6203（午为离明·明堂）。⛔ 本层纯叙事，不进评分链。'),
        }


def build_jiuzhu(result, ben_ming_zhi='', xing_nian_zhi=''):
    """便捷入口。"""
    return JiuzhuEngine().build(result, ben_ming_zhi=ben_ming_zhi, xing_nian_zhi=xing_nian_zhi)


if __name__ == '__main__':
    import json
    demo = {
        'sizhu': {'日': '甲申'},
        'yuejiang': '亥',                      # 寅月（建寅）→ 解神=申
        'tiandi_pan': {'申': '午', '午': '卯', '子': '酉', '辰': '丑', '寅': '子'},
        'tianjiang_map': {'申': '太阴', '午': '太常', '子': '贵人'},
        'sike': [('干上', '申', '甲', '太阴'), ('干阴', '午', '申', '太常'),
                 ('支上', '子', '申', '贵人'), ('支阴', '酉', '子', '')],
        'sanchuan': {'初传': '申', '中传': '午', '末传': '辰'},
    }
    out = build_jiuzhu(demo, ben_ming_zhi='亥', xing_nian_zhi='丑')
    print(json.dumps(out, ensure_ascii=False, indent=1))
