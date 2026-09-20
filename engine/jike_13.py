# -*- coding: utf-8 -*-
"""
十三吉课精细判定（依据《大六壬 64 课经》+《仪度六壬择日要诀》第144-148页"六壬课传美格并用法十三课"）。
2026-08-17 憨爷要求精细版：不得用"简化判断"，逐课按 definition 落码。
【2026-09-05 清单修正】以《要诀》十三课清单为准（富贵/荣华/龙德/官爵/时太/和美/合欢/回环/
  亨通/华盖乘轩/斩轮/铸印乘轩/德庆）；剔除 元首（九宗门课体非吉凶依据、清单外、17.5%过宽）与
  引从（清单外、近似判据）；合欢/回环与和美并列（三合类）由和美判据覆盖；时太=时泰、斩轮=斫轮。

十三吉课（11 课已实现 + 合欢/回环并入和美）：
  龙德、官爵、富贵、和美、亨通、华盖(轩盖)、斫轮、德庆、时泰、铸印、荣华

各课 definition（《要诀》为准，64课经补充）：
  龙德课：太岁月将乘贵人发用（《要诀》"太阳太岁同临卯山"）
  官爵课：岁、月、年、命 驿马发用，又天魁、太常人传
  富贵课：日课天干二贵发在三传并到山向（《要诀》第144页）
  和美课：四课得三合而发出三传，即课中三传，到山到向（《要诀》第145-146页）
  亨通课：三传顺生禄马贵人到山到向，逆生更有力（《要诀》第146页）
  华盖(轩盖)课：值胜光(午)为用，遇太冲(卯)、神后(子)
  斫轮课：卯加庚或加辛为用
  德庆课：干德支德天德月德四德聚集一神而发用在传（《要诀》第148页）
  时泰课：取年支月支发传即为山向禄马贵人到山到向（《要诀》时太课）
  铸印课：得戌加巳中传（巳戌卯）
  荣华课：本日禄马贵人三传全备（《要诀》第144页）
"""
from typing import Dict, List, Tuple

JIKE_13 = ['龙德', '官爵', '富贵', '和美', '亨通', '华盖', '斫轮', '德庆', '时泰', '铸印', '荣华']

# 日德（标准日德表：阳干取禄前、阴干取合）
_RI_DE = {'甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
          '己': '寅', '庚': '申', '辛': '巳', '壬': '亥', '癸': '寅'}
# 支德（日支→支德神）
_ZHI_DE = {'子': '巳', '丑': '午', '寅': '未', '卯': '申', '辰': '酉', '巳': '戌',
           '午': '亥', '未': '子', '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'}
# 天德贵人（按月支→支：干值取寄宫、卦值取方位，《协纪辨方书》口诀：
# 正丁二坤(申)三壬四辛五乾(亥)六甲七癸八艮(寅)九丙十乙十一巽(巳)十二庚）
_TIAN_DE = {'寅': '未', '卯': '申', '辰': '亥', '巳': '戌', '午': '亥', '未': '寅',
            '申': '丑', '酉': '寅', '戌': '巳', '亥': '辰', '子': '巳', '丑': '申'}
# 月德贵人（按月支三合局旺气阳干寄宫：寅午戌→丙(巳)、申子辰→壬(亥)、亥卯未→甲(寅)、巳酉丑→庚(申)）
_YUE_DE = {'寅': '巳', '午': '巳', '戌': '巳', '申': '亥', '子': '亥', '辰': '亥',
           '亥': '寅', '卯': '寅', '未': '寅', '巳': '申', '酉': '申', '丑': '申'}
# 十干阴阳贵（阳贵=昼贵，阴贵=夜贵）
# 【2026-09-11 二次订正】2026-09-09 的"与 GUIREN_MAP 对齐"修正本身对齐的是**错误的**
#   GUIREN_MAP（该表壬癸昼夜颠倒）→ 本次同步改正。权威判据：
#   《图解六壬大全》第1部 p.364「壬癸蛇兔藏（壬癸日昼贵巳，夜贵卯）」；
#   《通解·中卷》「壬子日初传巳加子为昼贵，末传卯加戌为夜贵」。
#   此处使用处（_gui_fg / _gui_set 等）均为 {阳,阴} 并集 → 功能无实害，仅正名与一致性。
_GUI_YANG = {'甲': '丑', '乙': '子', '丙': '亥', '丁': '亥', '戊': '丑',
             '己': '子', '庚': '丑', '辛': '午', '壬': '巳', '癸': '巳'}
_GUI_YIN = {'甲': '未', '乙': '申', '丙': '酉', '丁': '酉', '戊': '未',
            '己': '申', '庚': '未', '辛': '寅', '壬': '卯', '癸': '卯'}
# 地支五行
_ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
           '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
# 天干五行
_GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
           '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
# 五行相生（我生）：生我者 = SHENG_WO
_WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
_WX_SHENG_WO = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生我
# 六合 / 三合
_LIU_HE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
           '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
_SAN_HE_GROUPS = (('申', '子', '辰'), ('寅', '午', '戌'), ('巳', '酉', '丑'), ('亥', '卯', '未'))


def _is_liu_he(a, b):
    return _LIU_HE.get(a) == b


def _is_san_he(a, b):
    return a != b and any(a in g and b in g for g in _SAN_HE_GROUPS)


def _ma_of(zhi: str) -> str:
    """三合局驿马（申子辰马寅、寅午戌马申、巳酉丑马亥、亥卯未马巳）。"""
    ma = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
          '巳': '亥', '酉': '亥', '丑': '亥', '亥': '巳', '卯': '巳', '未': '巳'}
    return ma.get(zhi, '')


def check_jike_13(keti: str = '', sike: list = None, sanchuan_dizhi: List[str] = None,
                  tianjiang_list: List[str] = None, ri_gan: str = '', ri_zhi: str = '',
                  nian_zhi: str = '', yue_zhi: str = '', lu_zhi: str = '', ma_zhi: str = '',
                  longde_matched: bool = False, ben_ming_zhi: str = '',
                  lmg_dsdx: list = None, shan_lmg: list = None) -> Dict:
    """十三吉课精细判定。返回 {hits, is_jike, details: [(课名, 依据)]}。
    sike: 四课 [[课名,上神,下神,天将],...]；sanchuan_dizhi: [初,中,末]；tianjiang_list: 三传天将。
    lmg_dsdx: 禄马贵人到山到向的支集合（《要诀》亨通/和美课原文"禄马贵人到山到向"；
              由调用方按天盘加临到山/向计算；缺省时退回"三传在传"近似）。
    shan_lmg: 山向禄马贵人支集合（时太课原文"山向禄马贵人"；山禄+山贵人；缺省时退回"发用即可"）。"""
    sc = [z for z in (sanchuan_dizhi or []) if z]
    tj = [t for t in (tianjiang_list or []) if t]
    hits: List[str] = []
    details: List[str] = []

    def _hit(name, why):
        hits.append(name)
        details.append(why)

    # 四课干上/支上
    gan_shang = zhi_shang = ''
    if sike and isinstance(sike, (list, tuple)):
        for sk in sike:
            if isinstance(sk, (list, tuple)) and len(sk) >= 2:
                if sk[0] == '第一课':
                    gan_shang = sk[1]
                elif sk[0] == '第三课':
                    zhi_shang = sk[1]
    if len(sc) < 3:
        return {'hits': [], 'is_jike': False, 'details': []}

    chu, zhong, mo = sc[0], sc[1], sc[2]

    # 1. 【2026-09-05 剔除元首】原判据"课体名含元首"（九宗门课体，非吉凶依据——get_keti_deduction
    #   注释原则："九宗门是起课方法，不是吉凶依据"；且《要诀》第144-148页"六壬课传美格并用法十三课"
    #   清单无元首课；实测 17.5% 课命中、98% 单中——最大冗余加分源）。元首课不再作十三吉课加分，
    #   其课体吉性由 get_keti_deduction 上吉课（不扣分）体现。

    # 2. 龙德课：太岁月将乘贵人发用
    if longde_matched:
        _hit('龙德', '太岁=月将乘贵人发用')

    # 3. 官爵课：岁/月/年/命驿马发用 + 天魁(戌)太常人传
    mas = [z for z in [_ma_of(nian_zhi), _ma_of(yue_zhi), _ma_of(ri_zhi), _ma_of(ben_ming_zhi)] if z]
    if mas and chu in mas and '戌' in sc and '太常' in tj:
        _hit('官爵', f'驿马{chu}发用，天魁戌在传，太常在传')

    # 4. 富贵课（【2026-09-05 原文核对改判据】《要诀》第144页："以日课的天干二贵发在三传并到山向"；
    #   例 乙卯日三传申戌子，申=阳贵、子=阴贵——天干二贵皆在三传）——非64课经"天乙乘旺相临日辰发用"通义：
    #   判据 = 日阳贵与日阴贵两尊皆在三传 ＋ 至少一贵到山到向（lmg_dsdx；None 时退回"二贵在三传即可"近似）
    _gui_fg = {g for g in (_GUI_YANG.get(ri_gan, ''), _GUI_YIN.get(ri_gan, '')) if g}
    if len(_gui_fg) >= 2 and all(g in sc for g in _gui_fg):
        if lmg_dsdx is None or any(g in lmg_dsdx for g in _gui_fg):
            _hit('富贵', f'天干二贵{"".join(sorted(_gui_fg))}皆在三传（《要诀》富贵课）')

    # 5. 和美课（【2026-09-05 原文核对改判据】以《要诀》第145-146页定义为准，非64课经"干支遇三合六合"通义）：
    #   原文："和美课（7 合欢课、8 回环课）：总取四课得三合而发出三传，即课中三传也，到山到向。"
    #   例1 丁日四课三传皆亥卯未（木局三合），亥=丁日贵，"得三合拱贵格"
    #   例2 乙日四课三传皆未卯亥，卯=乙日禄，"得三合拱禄格"
    #   → 判据：三传恰为完整三合局（亥卯未/申子辰/寅午戌/巳酉丑 全备）＋ 禄马贵到山到向（三传中所见；
    #     lmg_dsdx=None 表示调用方无到山向能力，退回"三传在传"近似）
    _lmg = set(lmg_dsdx) if lmg_dsdx is not None else {
        z for z in (lu_zhi, ma_zhi, _GUI_YANG.get(ri_gan, ''), _GUI_YIN.get(ri_gan, '')) if z}
    _hm = ''
    for _g5 in _SAN_HE_GROUPS:
        if set(sc) == set(_g5):
            _hm = ''.join(_g5)
            break
    if _hm and any(z in _lmg for z in sc):
        _hit('和美', f'三传{_hm}三合局且禄马贵{"到山向" if lmg_dsdx else "在传"}（《要诀》和美课）')

    # 6. 亨通课（【2026-09-05 原文核对改判据】以《仪度六壬择日要诀》第146页定义为准，非64课经通义）：
    #   原文："亨通课：取三传顺生禄马贵人到山到向也、逆生更有力。"
    #   例1 戊辰日三传亥寅巳顺生（亥水生寅木→寅木生巳火），巳=戊日禄（"顺生日干巳禄"）
    #   例2 丁亥日三传巳寅亥逆生（巳火生寅木→寅木生亥水），巳=日支之马，末传亥=艮之贵人
    #   → 判据：三传递相生（顺生：初生中且中生末；或逆生：末生中且中生初）
    #      ＋ 三传中见 日禄/日马/日贵（"禄马贵人"）
    _HT_CHU, _HT_ZHONG, _HT_MO = _ZHI_WX.get(chu, ''), _ZHI_WX.get(zhong, ''), _ZHI_WX.get(mo, '')
    _ht_shun = (_WX_SHENG.get(_HT_CHU) == _HT_ZHONG and _WX_SHENG.get(_HT_ZHONG) == _HT_MO)
    _ht_ni = (_WX_SHENG.get(_HT_MO) == _HT_ZHONG and _WX_SHENG.get(_HT_ZHONG) == _HT_CHU)
    if (_ht_shun or _ht_ni) and any(z in _lmg for z in sc):
        _dir = '顺生' if _ht_shun else '逆生'
        _hit('亨通', f'三传{_dir}（{"→".join(sc)}）且禄马贵{"到山向" if lmg_dsdx is not None else "在传"}（《要诀》亨通课）')

    # 7. 华盖(轩盖)课：胜光午为用，遇太冲卯神后子
    if set(sc) == {'午', '卯', '子'}:
        _hit('华盖', '三传午卯子（胜光为用遇太冲神后）')

    # 8. 斫轮课：卯加庚或加辛为用
    if chu == '卯' and ri_gan in ('庚', '辛'):
        _hit('斫轮', f'卯加{ri_gan}为用')

    # 9. 德庆课（【2026-09-05 原文核对重写判据】《要诀》第148页："取干德，支德，天德，月德四德聚集一神，
    #   而发用在传……四德全甚少，止有干德支德或止有天德月德亦好"）——非"任何德神发用乘吉将"通义：
    #   判据 = 干德与支德同支（干德支德聚一神）或 天德与月德同支（天月二德聚一神），且该支发用（初传）乘吉将
    de_ganzhi = {_RI_DE.get(ri_gan, ''), _ZHI_DE.get(ri_zhi, '')}
    de_tianyue = {d for d in (_TIAN_DE.get(yue_zhi, ''), _YUE_DE.get(yue_zhi, '')) if d} if yue_zhi else set()
    _de_one = set()
    if len(de_ganzhi) == 1 and next(iter(de_ganzhi)):
        _de_one.update(de_ganzhi)          # 干德==支德 聚一神
    if len(de_tianyue) == 1 and next(iter(de_tianyue)):
        _de_one.update(de_tianyue)         # 天德==月德 聚一神
    if chu in _de_one:
        _chu_tj = tj[0] if tj else ''
        if _chu_tj and _chu_tj in ('贵人', '六合', '青龙', '太常', '天后', '太阴'):
            _hit('德庆', f'德神{chu}聚一神发用乘{_chu_tj}（干德支德/天月二德同支）')
        elif not tj:
            _hit('德庆', f'德神{chu}聚一神发用（干德支德/天月二德同支）')

    # 10. 时太课（【2026-09-05 原文核对改判据】《要诀》第145页："取年支月支发传即为山向禄马贵人
    #   到山到向福力最大，其天将不必拘定青龙六合"）——非64课经"太岁月建发用乘青龙六合"通义：
    #   判据 = 年支或月支发用（初传）＋ 该支为山向禄马贵人（山禄/山贵集合，shan_lmg）；
    #   天将不必拘定（去掉青龙六合条件）；shan_lmg=None（调用方无山向信息）退回"发用即可"近似
    if chu in (nian_zhi, yue_zhi):
        if shan_lmg is None:
            _hit('时泰', f'太岁/月建{chu}发用（《要诀》时太课·山向禄马贵未知）')
        elif chu in shan_lmg:
            _hit('时泰', f'太岁/月建{chu}发用为山向禄马贵（《要诀》时太课）')

    # 11. 铸印课：得戌加巳中传（三传巳戌卯）
    if chu == '巳' and zhong == '戌' and mo == '卯':
        _hit('铸印', '巳戌卯（戌加巳中传铸印）')

    # 12. 荣华课（【2026-09-05 原文核对改判据】《要诀》第144页："荣华课：本日禄马贵人三传全备。"
    #   例 壬申日三传巳寅亥：巳=阳贵、寅=日马、亥=壬禄——禄/马/贵三者皆在三传）
    #   非64课经通义"禄马贵人临干支年命发传乘吉将"（宽松判据）
    _gui_set = {z for z in (_GUI_YANG.get(ri_gan, ''), _GUI_YIN.get(ri_gan, '')) if z}
    _rh_lu_ok = bool(lu_zhi) and lu_zhi in sc
    _rh_ma_ok = bool(ma_zhi) and ma_zhi in sc
    _rh_gui_ok = bool(_gui_set) and any(g in sc for g in _gui_set)
    if _rh_lu_ok and _rh_ma_ok and _rh_gui_ok:
        _gui_hit = next((g for g in _gui_set if g in sc), '')
        _hit('荣华', f'禄马贵三传全备（禄{lu_zhi}、马{ma_zhi}、贵{_gui_hit or ""}）')

    # 13. 【2026-09-05 剔除引从】原判据"干上为初、支上为末"近似（缺地盘前后精确判定），
    #   且《要诀》第144-148页"六壬课传美格并用法十三课"清单（富贵/荣华/龙德/官爵/时太/和美/
    #   合欢/回环/亨通/华盖乘轩/斩轮/铸印乘轩/德庆）不含引从——不再作十三吉课加分。

    return {'hits': hits, 'is_jike': bool(hits), 'details': details}


if __name__ == '__main__':
    # 自测：元首课 + 三传午卯子(华盖) + 龙德
    print(check_jike_13(keti='元首课',
                        sike=[['第一课', '午', '甲', '贵人'], ['第二课', '未', '午', '太常'],
                              ['第三课', '卯', '子', '青龙'], ['第四课', '辰', '卯', '六合']],
                        sanchuan_dizhi=['午', '卯', '子'], tianjiang_list=['青龙', '六合', '贵人'],
                        ri_gan='甲', ri_zhi='子', nian_zhi='寅', yue_zhi='辰',
                        lu_zhi='寅', ma_zhi='寅', longde_matched=True, ben_ming_zhi='寅'))
    # 自测：铸印课（巳戌卯）
    print(check_jike_13(keti='重审课', sanchuan_dizhi=['巳', '戌', '卯'], tianjiang_list=['太常', '六合', '青龙'],
                        ri_gan='辛', ri_zhi='丑'))
    # 自测：斫轮课（卯加庚）
    print(check_jike_13(keti='重审课', sanchuan_dizhi=['卯', '戌', '巳'], tianjiang_list=['太常', '六合', '青龙'],
                        ri_gan='庚', ri_zhi='子'))
