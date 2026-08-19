# -*- coding: utf-8 -*-
"""占事断语生成器（P3 · 2026-08-18）

按具体占事（求财/婚姻/疾病/出行/官讼/功名/家宅/胎产/贼盗）生成六壬断语，
解决"一个断语通吃天下"的一刀切问题。三源合成：

1. 起课：权威 V2 引擎 SiKeSanChuanCalculator2（中气换将月将 + 九宗门完整）
2. 课体断语：liuren_keti_duanyu.LiuRenKetiDuanyu.get_keti_duanyu（课体话术）
3. 占类专属信号：liuren_keti_bifa 的 9 个 extract_*_valence（确定性·古籍出处）→ details 即人话断语
4. 毕法条文：BiFaDetector.detect → 命中条文 → data/bifa_100_knowledge_base.json 查 application/core_rule
"""
import json
import os
import re
import sys
from typing import Dict, List, Any

# 无论被 import 还是直接运行，都能找到 engine 包（脚本位于 engine/ 下）
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

GAN_SET = set('甲乙丙丁戊己庚辛壬癸')
ZHI_SET = set('子丑寅卯辰巳午未申酉戌亥')

# ── 前端 category 键 → 占类中文（与 9 抽取器口径一致）──
CATEGORY_MAP = {
    'general': '其他', 'stock': '求财', 'illness': '疾病', 'travel': '出行',
    'career': '功名', 'marriage': '婚姻', 'wealth': '求财', 'litigation': '官讼',
    'exam': '功名', 'lost': '贼盗', 'child': '胎产', 'house': '家宅',
    'business': '求财',
}

# ── 家宅子类识别（阳宅/阴宅/迁移，2026-08-18 三分）──
# 依据邵公断案：阴宅"占阴地总以辰为坟茔穴口"（§040）、迁移"迁店居住其户遂宁"（§014）。
# 注意：六壬术语"日墓/墓神/墓库"非坟地；断语中"遂成墓地""空坟"是阳宅凶应结果非占阴宅。
# 面向**占辞/问事描述**（question/shishi），非断语正文。
_ZHAIMU_YIN_PAT = re.compile(
    r'占坟|占阴宅|看地|寻地|寻穴|点穴|行龙|落脉|龙脉|入首|坐山|朝山|砂水|窀穸|'
    r'阴坟|坟地|墓地风水|阴宅风水|风水(?!不)|卜地|求地|坟山')
_ZHAIMU_QIAN_PAT = re.compile(r'迁居|移居|搬家|别迁|出外居|改造|修造|开店|移灶|他居|另居|移出|迁移|迁店|迁坟|移宅|改宅')
_ZHAIMU_YANG_PAT = re.compile(r'占宅|居宅|宅运|家宅|阳宅|宅基|买宅|新宅|宅上|入宅|破宅|修屋|造宅|求宅|宅内|宅前|宅后|屋|住|动土')


def classify_zhaimu_sub(text: str) -> str:
    """从占事描述/问事文本识别家宅子类：阴宅/迁移/阳宅（默认）。"""
    t = str(text or '')
    if _ZHAIMU_YIN_PAT.search(t):
        return '阴宅'
    if _ZHAIMU_QIAN_PAT.search(t):
        return '迁移'
    if _ZHAIMU_YANG_PAT.search(t):
        return '阳宅'
    return '阳宅'

# ── 占类中文 → 抽取器（惰性 import，避免模块级重依赖）──
_EXTRACTORS = None


def _get_extractors():
    global _EXTRACTORS
    if _EXTRACTORS is None:
        from engine.liuren_keti_bifa import (
            extract_taichan_valence, extract_guansong_valence, extract_qiucai_valence,
            extract_gongming_valence, extract_disease_valence, extract_jiazhai_valence,
            extract_chuxing_valence, extract_hunyin_valence, extract_zeidao_valence,
        )
        _EXTRACTORS = {
            '胎产': extract_taichan_valence, '官讼': extract_guansong_valence,
            '求财': extract_qiucai_valence, '功名': extract_gongming_valence,
            '疾病': extract_disease_valence, '家宅': extract_jiazhai_valence,
            '出行': extract_chuxing_valence, '婚姻': extract_hunyin_valence,
            '贼盗': extract_zeidao_valence,
        }
    return _EXTRACTORS


# ── 毕法 KB（100 条，含 application/core_rule）──
_BIFA_KB = None


def _get_bifa_kb():
    global _BIFA_KB
    if _BIFA_KB is None:
        _here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(os.path.dirname(_here), 'data', 'bifa_100_knowledge_base.json')
        with open(p, encoding='utf-8') as f:
            _BIFA_KB = {r.get('name'): r for r in json.load(f).get('rules', [])}
    return _BIFA_KB


def paipan_v2(ri_gan: str, ri_zhi: str, yuejiang: str, shichen: str) -> Dict[str, Any]:
    """权威 V2 起课：天地盘/四课/三传/课体/天将。
    【BUG-FIX 2026-08-18】非法干支/月将/时辰输入时返回空排盘（原会 KeyError 崩溃）。"""
    if (ri_gan not in GAN_SET or ri_zhi not in ZHI_SET
            or yuejiang not in ZHI_SET or shichen not in ZHI_SET):
        return {'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'yuejiang': yuejiang, 'shichen': shichen,
                'tiandi_pan': {}, 'sike': [], 'sanchuan': [],
                'keti': '', 'qifa': '', 'tianjiang_map': {}, 'tianjiang_list': []}
    from engine.sike_sanchuan_engine_patched import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    calc = SiKeSanChuanCalculator2()
    tdp = calc.get_tiandi_pan(yuejiang, shichen)
    sike = calc.qi_sike(ri_gan, ri_zhi, tdp)
    sc = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tdp)
    sanchuan = [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')]
    tjm = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shichen).get('天将映射', {})
    return {
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'yuejiang': yuejiang, 'shichen': shichen,
        'tiandi_pan': tdp, 'sike': sike, 'sanchuan': sanchuan,
        'keti': sc.get('课体', ''), 'qifa': sc.get('起法', ''),
        'tianjiang_map': tjm,
        'tianjiang_list': [tjm.get(z, '') for z in sanchuan],
    }


# 抽取器三传参数名（个别不同：胎产=san_chuan、疾病=san_chuan_dizhi，其余=sanchuan_dizhi）
_SC_PARAM = {
    '胎产': 'san_chuan', '疾病': 'san_chuan_dizhi',
}


def _zhanshi_class_signal(pan: Dict[str, Any], zhanlei: str) -> Dict[str, Any]:
    """按占类调对应抽取器，取 details（人话断语）+ level"""
    exs = _get_extractors()
    ex = exs.get(zhanlei)
    if not ex:
        return {'score': 0, 'level': '平', 'details': [], 'fired': ''}
    kw = dict(ri_gan=pan['ri_gan'], ri_zhi=pan['ri_zhi'],
              tianjiang_list=pan['tianjiang_list'], zhanlei=zhanlei)
    sc_key = _SC_PARAM.get(zhanlei, 'sanchuan_dizhi')
    try:
        return ex(**{sc_key: pan['sanchuan']}, si_ke=pan['sike'], **kw)
    except TypeError:
        return ex(**{sc_key: pan['sanchuan']}, **kw)


def _bifa_duanyu(pan: Dict[str, Any]) -> List[Dict[str, str]]:
    """毕法检测 → 命中条文 → KB 查白话/占事应用"""
    from engine.bifa_detector import BiFaDetector
    from engine.liuren_keti_bifa import _derive_gan_zhi_shang
    gan_shang, zhi_shang = _derive_gan_zhi_shang(pan['sike'], pan['tiandi_pan'], pan['ri_gan'], pan['ri_zhi'])
    r = BiFaDetector().detect(
        sanchuan_dizhi=pan['sanchuan'], ri_gan=pan['ri_gan'], ri_zhi=pan['ri_zhi'],
        ganzhi=pan['ri_gan'] + pan['ri_zhi'], yuejiang=pan['yuejiang'], season='',
        gan_shang_shen=gan_shang, zhi_shang_shen=zhi_shang,
        si_ke_info=pan['sike'], tian_jiang=pan['tianjiang_map'], tiandi_pan=pan['tiandi_pan'],
    )
    kb = _get_bifa_kb()
    out = []
    for name in (r.get('匹配法条') or []):
        item = kb.get(name, {})
        out.append({
            '条文': name,
            '白话': item.get('core_rule', ''),
            '占事应用': item.get('application', ''),
            '古例': (item.get('example') or '')[:120],
        })
    return out


def _zhi_yue_jian_wangshuai(zhi: str, yuejiang: str) -> str:
    """地支在月令下的旺衰（旺相休囚死；月令=月将对应季节的五行）。
    简化：用月将地支五行定当令，同令=旺、生令=相、克令=囚、令生=休、令克=死。"""
    WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
    SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    zwx = WX.get(zhi, '')
    mwx = WX.get(yuejiang, '')
    if not zwx or not mwx:
        return ''
    if zwx == mwx:
        return '旺'
    if SHENG.get(mwx) == zwx:
        return '相'
    if KE.get(zwx) == mwx:
        return '休'
    if SHENG.get(zwx) == mwx:
        return '囚'
    return '死'


# 天将吉凶（邵公断案通行口径：青龙六合太常天后太阴贵人=吉，白虎玄武螣蛇朱雀=凶，勾陈天空=中性）
_JI_JIANG = {'贵人', '青龙', '六合', '太常', '天后', '太阴'}
_XIONG_JIANG = {'白虎', '玄武', '螣蛇', '朱雀'}


def _zhi_shang_zhi(sike: List) -> str:
    """取支上神地支（第三课上神，dict/list 兼容）。"""
    if not sike or len(sike) < 3:
        return ''
    k3 = sike[2]
    if isinstance(k3, dict):
        return str(k3.get('上神', '') or '')
    if isinstance(k3, (list, tuple)) and len(k3) >= 2:
        return str(k3[1])
    return ''


def _zhi_shang_signal(ri_gan: str, ri_zhi: str, sike: List, yuejiang: str,
                      zhanshi: str = '其他') -> Dict[str, Any]:
    """支上神（宅/事体·根基）吉凶信号（案例实证，2026-08-18）：
    支=事体/宅/内/静，三传=过程/外/动。支上神受损（泄克冲刑墓日干+凶将）
    即使三传吉，无解神最终还是凶。
    案例证据：
      "支上动出午鬼克身，的是占病"（§疾病13·174）→ 支上克日=凶
      "支上又脱干…人宅受脱俱遭盗"（§宅墓02·004）→ 支上泄日=凶
      "宅上子作螣蛇，主子外横"（§宅墓02·016）→ 支上凶将=凶
      "宅上午上螣蛇带羊刃，主家人争屋"（§宅墓02·042）→ 支上凶将=凶
      "宅上贵人六害，末财禄又入盗气"（§前程03·082）→ 支上害=凶
      "日鬼传归宅上，宅上却又生鬼"（§流年05·120）→ 支上生鬼=凶
      "受支上午火、青龙秉月建之旺来生合于我"（§前程03·047）→ 支上生日=吉
      "支宅上去作朱雀，乃戊禄临支"（§前程03·058）→ 支上禄=吉
    """
    if not ri_gan or not ri_zhi or not sike or len(sike) < 3:
        return {'score': 0, 'dir': '平', 'desc': ''}
    # 支上神 = 第三课上神（sike 元素 dict/list 兼容）
    k3 = sike[2]
    if isinstance(k3, dict):
        zhi_shang = str(k3.get('上神', '') or '')
    elif isinstance(k3, (list, tuple)) and len(k3) >= 2:
        zhi_shang = str(k3[1])
    else:
        zhi_shang = ''
    if not zhi_shang or zhi_shang not in ZHI_SET:
        return {'score': 0, 'dir': '平', 'desc': ''}
    # 支上神天将（tianjiang_map 由外部传入? 这里从 sike 第4元素取）
    zhi_shang_tj = ''
    if isinstance(k3, dict):
        zhi_shang_tj = str(k3.get('天将', '') or '')
    elif isinstance(k3, (list, tuple)) and len(k3) >= 4:
        zhi_shang_tj = str(k3[3])
    WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
    GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
              '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    _z_wx = WX.get(zhi_shang, '')
    _g_wx = GAN_WX.get(ri_gan, '')
    score = 0.0
    desc = ''
    if _z_wx and _g_wx:
        if KE.get(_z_wx) == _g_wx:
            score -= 3.0
            desc = f'支上{zhi_shang}克日干{ri_gan}，事体受损'
        elif SHENG.get(_g_wx) == _z_wx:
            score -= 2.0
            desc = f'支上{zhi_shang}泄日干{ri_gan}，人宅受脱'
        elif SHENG.get(_z_wx) == _g_wx:
            score += 2.0
            desc = f'支上{zhi_shang}生日干{ri_gan}，事体生身'
    # 凶将/吉将
    if zhi_shang_tj in _XIONG_JIANG:
        score -= 2.0
        desc += f'，乘凶将{zhi_shang_tj}'
    elif zhi_shang_tj in _JI_JIANG:
        score += 1.5
        desc += f'，乘吉将{zhi_shang_tj}'
    # 支上=日墓
    _MU = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
           '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}
    if _MU.get(ri_gan) == zhi_shang:
        score -= 2.0
        desc += f'，支上为日墓'
    return {'score': round(score, 2), 'dir': '吉' if score > 0 else ('凶' if score < 0 else '平'), 'desc': desc}


def _sanchuan_time_sequence(sanchuan: List[str], tianjiang_list: List[str],
                            yuejiang: str, kongwang, zhanshi: str = '其他') -> Dict[str, Any]:
    """三传时序吉凶合成（案例实证规则，2026-08-18）：
    - 每传信号 = 天将吉凶(±2) + 旺衰(±1) + 空亡(-1)
    - 【BUG-FIX 2026-08-18 案例实证】天将吉凶按占类调整：
      朱雀=功名/考试/仕宦占的文印官星(吉，"朱雀为文印之神"§03·050)，
      其他占=口舌(凶，"朱雀口舌之神"§宅墓02·035)；
      勾陈=官讼/仕宦占的陈滞狱讼(凶，"官星乘勾陈主狱讼"§03·061)，
      其他占中性。
    - 权重：初传0.2 / 中传0.3 / 末传1.5（实例反推，末传定结局）
    - 末传空亡再扣1.5（案例"先凶后吉，奈何寅是空亡，反成凶咎"）
    - 先凶后吉(初<0且末>0)→吉；先吉后凶(初>0且末<0)→凶
    返回：每传分 + 合成分 + 走向描述。无三传数据安全返回平。"""
    if not sanchuan or len(sanchuan) < 3:
        return {'score': 0, 'dir': '平', 'per_chuan': [], 'desc': ''}
    tj = list(tianjiang_list or [])
    kw = set(kongwang or [])
    # 占类化的天将吉凶
    _wen_shu_zhanlei = ('功名', '考试', '仕宦', '前程')
    _guansong_zhanlei = ('官讼', '仕宦', '前程')
    per = []
    for i, z in enumerate(sanchuan):
        if not z:
            per.append(0.0)
            continue
        s = 0.0
        t = tj[i] if i < len(tj) else ''
        if t in _JI_JIANG:
            s += 2.0
        elif t == '朱雀':
            s += 1.0 if zhanshi in _wen_shu_zhanlei else -2.0
        elif t == '勾陈':
            s += -1.0 if zhanshi in _guansong_zhanlei else 0.0
        elif t in _XIONG_JIANG:
            s -= 2.0
        ws = _zhi_yue_jian_wangshuai(z, yuejiang)
        if ws in ('旺', '相'):
            s += 1.0
        elif ws in ('囚', '死'):
            s -= 1.0
        if z in kw:
            s -= 1.0
        per.append(s)
    # 权重（末传定结局；【BUG-FIX 2026-08-18 实例反推】218案网格搜索最优
    # 每传权重 (0.2, 0.3, 1.5)——末传权重最高、初传最低，印证案例
    # "末后却吉""末传天喜乘龙先凶后吉"，符合率 0.650→0.670）
    score = per[0] * 0.2 + per[1] * 0.3 + per[2] * 1.5
    # 末传空亡重罚（案例：先凶后吉但末传空亡→反成凶咎）
    if sanchuan[2] in kw:
        score -= 1.5
    # 走向判定
    desc = ''
    if per[0] < 0 and per[2] > 0:
        desc = '初凶末吉，先难后易，终得吉'
    elif per[0] > 0 and per[2] < 0:
        desc = '初吉末凶，先易后难，终归于凶'
    elif per[0] == 0 and per[2] == 0 and abs(score) < 0.5:
        desc = '始终平平，无大吉凶'
    elif score > 0.5:
        desc = '三传向吉，事有终成'
    elif score < -0.5:
        desc = '三传向凶，事有终败'
    else:
        desc = '吉凶参半，看类神走向'
    return {'score': round(score, 2), 'dir': '吉' if score > 0.5 else ('凶' if score < -0.5 else '平'),
            'per_chuan': [round(x, 2) for x in per], 'desc': desc}


def generate(ri_gan: str, ri_zhi: str, yuejiang: str, shichen: str,
             zhanshi: str = '其他', category: str = '', zishu: str = '',
             year: str = '', leishen: str = '', leishen_liuchu: bool = False) -> Dict[str, Any]:
    """按占事生成完整断语。zhanshi 为中文占类；category 为前端英文键（二选一，category 优先映射）；
    zishu 为家宅子类（阳宅/阴宅/迁移），仅 zhanshi==家宅 时生效；year 为占课年（干支），供太岁规则。"""
    if category:
        zhanshi = CATEGORY_MAP.get(category, zhanshi)
    pan = paipan_v2(ri_gan, ri_zhi, yuejiang, shichen)

    # 课体断语
    keti_text = ''
    keti_level = ''
    try:
        from engine.liuren_keti_duanyu import LiuRenKetiDuanyu
        kd = LiuRenKetiDuanyu().get_keti_duanyu(pan['keti'])
        keti_text = kd.get('断语', '') or kd.get('详细断语', {}).get('总论', '')
        keti_level = kd.get('等级', '')
    except Exception:
        pass

    # 占类专属断语
    zl_signal = _zhanshi_class_signal(pan, zhanshi)
    zl_details = list(zl_signal.get('details', []))

    # 毕法断语
    bifa = _bifa_duanyu(pan)
    bifa_duanyu = [f'{b["条文"]}：{b["白话"]}' for b in bifa if b.get('白话')]

    # ── 三传时序合成（案例实证：末传定结局，先凶后吉=吉、先吉后凶=凶）──
    # 数据源：pan['sanchuan'] + pan['tianjiang_list'] + yuejiang + 旬空
    kw = ()
    try:
        from engine.bifa_detector import get_xun_kong
        kw = get_xun_kong(ri_gan + ri_zhi) if ri_gan and ri_zhi else ('', '')
    except Exception:
        kw = ('', '')
    seq = _sanchuan_time_sequence(pan['sanchuan'], pan['tianjiang_list'], yuejiang, kw, zhanshi)
    seq_desc = seq.get('desc', '')

    # ── 事体走向引擎（六壬断事流程：初始→过程→结局，2026-08-18）──
    # 结合知识库规则（duanan_knowledge_base L783/L830/L1470/L689 等）判断
    # 事体变化过程与走向，非仅吉凶。输出叙事供断语使用。
    try:
        from engine.liuchen_engine import LiuChenEngine
        liuchen_out = LiuChenEngine().analyze(
            ri_gan, ri_zhi, pan['sanchuan'], pan['tianjiang_list'], kw, pan['keti'], pan['sike'],
            category=zhanshi, zishu=zishu, yuejiang=yuejiang, year=year,
            sike_tj=pan.get('tianjiang_map') or {},
            leishen=leishen, leishen_liuchu=leishen_liuchu)
    except Exception:
        liuchen_out = {'走向': '未定', '终局': '平', '叙事': '', '阶段': {}, '三传': ''}

    # ── 多条件合参（L2 层，叙事输出不参与评分；hecan_engine 全条件命中才触发）──
    hecan_narr = ''
    try:
        from hecan_engine_v7 import hecan_judge, build_signals
        from engine.liuchen_shensha import wang_shuai as _ws_hc
        _WXH = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
                '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
        _sig = build_signals(ri_gan, ri_zhi, pan['sanchuan'], pan['tianjiang_list'],
                             kw, pan['sike'], pan['keti'], zhanshi,
                             lambda z: _ws_hc(_WXH.get(z, ''), yuejiang))
        _hc = hecan_judge(_sig)
        if _hc:
            hecan_narr = '；'.join(f"合参[{o['id']}]：{o['叙事']}（{o['出处']}）" for o in _hc[:2])
    except Exception:
        hecan_narr = ''

    # ── 射覆判物（叙事层，不参与评分；袁天罡《射覆无移口鉴》+苗公鬼撮脚）──
    shefu_narr = ''
    if zhanshi == '射覆':
        try:
            from shefu_engine_v3 import shefu
            from engine.liuchen_shensha import wang_shuai as _ws
            from shefu_engine_v3 import shefu_yongshen, WX as _SF_WX
            _ys2 = shefu_yongshen(ri_gan, pan['sike'], pan['sanchuan'])['用神']
            _ws2 = _ws(_SF_WX.get(_ys2, ''), yuejiang)
            _sf = shefu(ri_gan, ri_zhi, pan['sanchuan'], pan['tianjiang_list'],
                        kw, pan['sike'], keti=pan['keti'], wangshuai=_ws2)
            shefu_narr = _sf.get('叙事', '')
        except Exception:
            shefu_narr = ''

    # ── 应期（邵彦和洛书数法 + 阴宅期候应象，叙事层不参与评分）──
    # 支数法/月建法/太岁法三支柱；阴宅(zishu)启用邵公"取数增一半/减一半"期候应象
    # （§040"酉六数故主六年酒败，更三年死，酉增一半也"；§043"未八数先个八年全用后用一半故十二年"）。
    yingqi_desc = ''
    try:
        from engine.liuren_keti_bifa import get_yingqi_unified
        yingqi_desc = get_yingqi_unified(
            ri_gan, ri_zhi, pan['sanchuan'], tiandi_pan=pan.get('tiandi_pan'),
            si_ke=pan['sike'], shichen=pan['shichen'],
            tai_sui_zhi=pan.get('tai_sui_zhi', ''), zhanlei=zhanshi, zishu=zishu)
    except Exception:
        yingqi_desc = ''

    # ── 支上神（宅/事体·根基）信号（案例实证：支上泄克冲刑墓日干+凶将→凶）──
    # 支=事体/内/静，三传=过程/外/动。支上受损即使三传吉，无解神最终凶。
    zs = _zhi_shang_signal(ri_gan, ri_zhi, pan['sike'], yuejiang, zhanshi)
    zs_desc = zs.get('desc', '')
    # 【BUG-FIX 2026-08-18 案例实证】解神守卫：支上凶 + 三传有解神 → 可解不判凶。
    # 案例："末天喜乘龙作解神，必有恩赦相救，先凶而后吉"（§官讼16·212）、
    # "传终地医能制午火，制鬼之位乃良医"（§疾病13·167）、
    # "年命制鬼则吉，无制则凶"（§财产08·137）、"月将之吉可解"（§杂占17·218）。
    _has_jieshen = False
    if zs.get('score', 0) < 0:
        # ① 末传乘解神/天喜/青龙/月将（恩赦/吉将化解）
        _mo_tj = pan['tianjiang_list'][2] if len(pan['tianjiang_list']) > 2 else ''
        _mo_zhi = pan['sanchuan'][2] if len(pan['sanchuan']) > 2 else ''
        if _mo_tj in ('青龙', '六合', '太常', '贵人', '天后', '太阴'):
            _has_jieshen = True
        # ② 三传有制鬼之支（克支上凶神五行；"制鬼之位乃良医"）
        if not _has_jieshen:
            _zs_wx = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
                      '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}.get(_zhi_shang_zhi(pan['sike']), '')
            # 【BUG-FIX 2026-08-18】制鬼=克支上凶神者（"传终地医能制午火"——水克火）：
            #   原表为"支上克谁"（我克者）方向反了；改为"谁克支上"（克我者）
            _ke_wx = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
            _zhi_ke_wx = _ke_wx.get(_zs_wx, '')
            if _zhi_ke_wx and any(
                    {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
                     '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}.get(z, '') == _zhi_ke_wx
                    for z in pan['sanchuan']):
                _has_jieshen = True
        if _has_jieshen:
            zs_score_eff = 0.0
            zs_desc = (zs_desc + '，但三传有解神（制鬼/吉将）可解').strip()
        else:
            zs_score_eff = max(-3.0, min(3.0, zs.get('score', 0) / 2.0))
    else:
        zs_score_eff = max(-3.0, min(3.0, zs.get('score', 0) / 2.0))

    # ── 综合评级：占类 + 三传时序 + 支上神 加权合成（权重实例反推，2026-08-18）──
    # 基础权重：占类=0.6、时序=0.4（218案反推）；支上神信号为事体根基，
    # 权重经实例搜索确认（初版 0.5，见 _weight_search 记录；课体 valence 剔除=0.0）
    _lv_score = {'上吉': 3, '大吉': 2.5, '吉': 2, '小吉': 1, '中吉': 1.5,
                 '平': 0, '中平': -0.5, '凶': -2, '小凶': -1, '中凶': -2.5, '大凶': -3}
    zl_score = 0
    zl_level = zl_signal.get('level', '')
    if zl_level:
        zl_score = _lv_score.get(str(zl_level).split('-')[0].strip(), 0)
        if str(zl_level).startswith('吉-'):
            zl_score = 2
        elif str(zl_level).startswith('凶-'):
            zl_score = -2
    # 时序分是绝对分（范围约 -6~+6），归一化到 -3~+3
    seq_score = max(-3.0, min(3.0, seq.get('score', 0) / 2.0))
    # 【2026-08-18 打通深读引擎】analyze_liuchen 终局（占类化深读规则：功名/家宅/官讼/疾病/
    # 婚姻/求财/出行/胎产）接入评分——深读成果从"叙事"传导到"吉凶分"。
    # 权重 218 案实例反推（_memory/_link_search4.py）：liu 权重 0.5 时主集符合率
    # 0.419→0.636、验证集(壬占汇选+指南261案) 0.387→0.456，四分量保留正权重不偏废。
    # 【2026-08-18 第四轮】liu ±2.5→±3：±3×0.5=±1.5 稳过阈值 ±1.2，防 zl/seq 抵消——
    # 仕宦-八/选举-二/仕宦-二十五 analyze 已判凶/吉但合成落平/小凶（指南合成边缘案修复）
    _liu_score = {'吉': 3, '凶': -3, '平': 0}.get(liuchen_out.get('终局', '平'), 0)
    # 权重（218 案实例反推，2026-08-18 v2）：占类0.2 / 时序0.2 / 支上0.1 / 深读终局0.5。
    # 支上=事体根基：支上泄克冲刑墓日干+凶将且无解神 → 凶（"支上动出午鬼克身"§疾病13·174）；
    # 有解神（末传吉将/制鬼）→ 可解不判凶（"末天喜乘龙作解神先凶后吉"§官讼16·212）。
    # 深读终局=占类化走向规则结论（邵公断案逐字深读提炼），为最强吉凶信号（实例反推主导权重）。
    total = zl_score * 0.2 + seq_score * 0.2 + zs_score_eff * 0.1 + _liu_score * 0.5
    if total >= 1.2:
        level = '吉'
    elif total >= 0.4:
        level = '小吉'
    elif total <= -1.2:
        level = '凶'
    elif total <= -0.4:
        level = '小凶'
    else:
        level = '平'

    return {
        'zhanshi': zhanshi,
        'paipan': {
            'ri_gan': pan['ri_gan'], 'ri_zhi': pan['ri_zhi'],
            'yuejiang': pan['yuejiang'], 'shichen': pan['shichen'],
            'sanchuan': pan['sanchuan'], 'keti': pan['keti'], 'qifa': pan['qifa'],
            'tianjiang': pan['tianjiang_list'],
        },
        'level': level,
        'liuchen': liuchen_out,
        'yingqi': yingqi_desc,
        'seq_desc': seq_desc,
        'seq_score': seq.get('score', 0),
        'zhi_shang_desc': zs_desc,
        'zhi_shang_score': zs.get('score', 0),
        'keti_duanyu': keti_text,
        'zhanshi_duanyu': zl_details,
        'bifa_duanyu': bifa_duanyu,
        'bifa_detail': bifa[:3],
        'shefu_duanyu': shefu_narr,
        'hecan_duanyu': hecan_narr,
        'summary': '；'.join(filter(None, [keti_text] + zl_details + bifa_duanyu[:2] + ([seq_desc] if seq_desc else []) + ([zs_desc] if zs_desc else []) + ([shefu_narr] if shefu_narr else []) + ([liuchen_out.get('叙事', '')] if liuchen_out.get('叙事') else []))) or '课体平稳，需结合具体占事详参。',
    }


if __name__ == '__main__':
    for zl, cat in [('求财', 'wealth'), ('婚姻', 'marriage'), ('疾病', 'illness'), ('出行', 'travel'), ('官讼', 'litigation')]:
        r = generate('甲', '子', '亥', '寅', zhanshi=zl)
        print('[' + zl + '] 课体=' + r['paipan']['keti'] + ' 等级=' + r['level'])
        print('   占类断语: ' + str(r['zhanshi_duanyu']))
        print('   毕法: ' + str([b['条文'] for b in r['bifa_detail']]))
