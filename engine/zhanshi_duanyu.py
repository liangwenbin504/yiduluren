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
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
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
             zhanshi: str = '其他', category: str = '') -> Dict[str, Any]:
    """按占事生成完整断语。zhanshi 为中文占类；category 为前端英文键（二选一，category 优先映射）。"""
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

    # ── 综合评级：占类信号 + 三传时序 加权合成（权重由 218 案实例反推，2026-08-18）──
    # 实例网格搜索最优：占类=0.6、时序=0.4、课体=0.0 → 符合率 0.650（134/206）。
    # 课体 valence 单独符合率仅 0.228（64课吉凶表偏凶且与断案吉凶相关性弱），
    # 剔除出评分（仅作展示），避免劣质信号拉低精度。
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
    # 权重 0.6/0.4（实例反推最优；课体 0.0 剔除）
    total = zl_score * 0.6 + seq_score * 0.4
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
        'seq_desc': seq_desc,
        'seq_score': seq.get('score', 0),
        'keti_duanyu': keti_text,
        'zhanshi_duanyu': zl_details,
        'bifa_duanyu': bifa_duanyu,
        'bifa_detail': bifa[:3],
        'summary': '；'.join(filter(None, [keti_text] + zl_details + bifa_duanyu[:2] + ([seq_desc] if seq_desc else []))) or '课体平稳，需结合具体占事详参。',
    }


if __name__ == '__main__':
    for zl, cat in [('求财', 'wealth'), ('婚姻', 'marriage'), ('疾病', 'illness'), ('出行', 'travel'), ('官讼', 'litigation')]:
        r = generate('甲', '子', '亥', '寅', zhanshi=zl)
        print('[' + zl + '] 课体=' + r['paipan']['keti'] + ' 等级=' + r['level'])
        print('   占类断语: ' + str(r['zhanshi_duanyu']))
        print('   毕法: ' + str([b['条文'] for b in r['bifa_detail']]))
