# -*- coding: utf-8 -*-
"""择日合参引擎（2026-08-19）：择日专属条件合参规则——三层架构迁移到择日域。
L1 = 择日评分体系（斗首/仪度/禄马贵/演禽，不动）；L2 = 本引擎（全条件命中才触发，
警示/佐证层不参与评分）；L3 = data/zeri_hecan_rules.json 候选库（门槛：真实反馈
全中≥3 且一致率≥80% 才升 L2——当前反馈池仅 3 条，全部挂"候选-样本不足"）。
规则来源（每条标出处）：《仪度六壬择日要诀》场景吉凶课表（liuren_keti_duanyu）、
64 课格断语（daliuren_64ke_rules）、择日案例反馈（data/zeri_case_feedback.json）。"""
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))

_TYPE_MAP = {'提车': '出行', '搬家': '动土', '入宅': '动土', '开工': '动土', '上任': '上任',
             '赴任': '上任', '升迁': '上任', '开业': '开业', '开张': '开业', '交易': '开业',
             '安葬': '安葬', '下葬': '安葬', '立碑': '立碑', '出行': '出行', '远行': '出行',
             '考试': '考试', '婚嫁': '婚嫁', '结婚': '婚嫁', '动土': '动土', '催龙补气': '催龙补气'}

_KETI_KEYS = ('伏吟', '返吟', '八专', '官爵', '亨通', '元首', '龙德', '华盖乘轩', '富贵',
              '荣华', '遥克', '时泰', '合欢', '和美', '德庆')


def zeri_type_class(zetiri_type: str) -> str:
    """择日类型 → 要诀场景类（提车归出行、开张归开业等）。"""
    t = str(zetiri_type or '')
    for k, v in _TYPE_MAP.items():
        if k in t:
            return v
    return '其他'


# ── 通用查表（2026-08-20 第二批注解2实战案例：禄马贵/旬空/三传美格/贪官制化）──
_LU10 = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午',
         '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
_MA12 = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
         '巳': '亥', '酉': '亥', '丑': '亥', '亥': '巳', '卯': '巳', '未': '巳'}
_GUI10 = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'},
          '戊': {'丑', '未'}, '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'},
          '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
_CH12 = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
         '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
_HE12 = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
         '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
_SANHE = {'寅': ('午', '戌'), '午': ('戌', '寅'), '戌': ('寅', '午'),
          '申': ('子', '辰'), '子': ('辰', '申'), '辰': ('申', '子'),
          '巳': ('酉', '丑'), '酉': ('丑', '巳'), '丑': ('巳', '酉'),
          '亥': ('卯', '未'), '卯': ('未', '亥'), '未': ('亥', '卯')}
_ZHI_WX = {'寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金',
           '亥': '水', '子': '水', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
_WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
# 十二长生生旺位（阳长生态：长生/临官/帝旺——注解2实例"生寅旺午""旺卯养戌胎酉"口径）
_WX_SHENGWEI = {'木': ('亥', '寅', '卯'), '火': ('寅', '巳', '午'), '土': ('寅', '巳', '午'),
                '金': ('巳', '申', '酉'), '水': ('申', '亥', '子')}
# 十二长生全表（2026-08-21 接入：注解2"破鬼火死酉病申败卯墓戌…无一个扶助"全位判定；土随火）
_WX_CS12 = {
    '木': {'长生': '亥', '沐浴': '子', '冠带': '丑', '临官': '寅', '帝旺': '卯',
           '衰': '辰', '病': '巳', '死': '午', '墓': '未', '绝': '申', '胎': '酉', '养': '戌'},
    '火': {'长生': '寅', '沐浴': '卯', '冠带': '辰', '临官': '巳', '帝旺': '午',
           '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑'},
    '土': {'长生': '寅', '沐浴': '卯', '冠带': '辰', '临官': '巳', '帝旺': '午',
           '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑'},
    '金': {'长生': '巳', '沐浴': '午', '冠带': '未', '临官': '申', '帝旺': '酉',
           '衰': '戌', '病': '亥', '死': '子', '墓': '丑', '绝': '寅', '胎': '卯', '养': '辰'},
    '水': {'长生': '申', '沐浴': '酉', '冠带': '戌', '临官': '亥', '帝旺': '子',
           '衰': '丑', '病': '寅', '死': '卯', '墓': '辰', '绝': '巳', '胎': '午', '养': '未'},
}
_WX_WEI_NAMES = ('长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养')
# 休囚位集合（注解2"死酉病申败卯墓戌"：败即沐浴）
_XIUQIU = {'沐浴', '衰', '病', '死', '墓', '绝'}
# 六相支=长生冠带临官帝旺胎养；六替支=沐浴衰病死墓绝（注解1第三章六相六替诀）
_XIANG_WEI = ('长生', '冠带', '临官', '帝旺', '胎', '养')
# 文昌速查（注解1第四章五："甲丙文昌在巳猴，乙丁在午酉戊申。已酉庚亥辛子位，壬寅癸卯食禄荣"）
_WENCHANG = {'甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申',
             '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'}
# 红鸾（逆行起例：子卯丑寅…；天喜=红鸾对宫——注解1第四章六"祈子传家，生气元廉抱天喜"）
_HONGLUAN = {'子': '卯', '丑': '寅', '寅': '丑', '卯': '子', '辰': '亥', '巳': '戌',
             '午': '酉', '未': '申', '申': '未', '酉': '午', '戌': '巳', '亥': '辰'}


def _wx_position(wx: str, zhi: str) -> str:
    """五行+地支 → 十二长生位名（未命中返回空串）。"""
    if not wx or not zhi:
        return ''
    for name in _WX_WEI_NAMES:
        if _WX_CS12.get(wx, {}).get(name) == zhi:
            return name
    return ''
_GZ60 = ['甲乙丙丁戊己庚辛壬癸'[i % 10] + '子丑寅卯辰巳午未申酉戌亥'[i % 12] for i in range(60)]


def _xun_kong_of(gan: str, zhi: str):
    """日柱干支 → 所在旬空亡二支（按 60 干支序号定位，勿用字符下标）。"""
    gz = str(gan) + str(zhi)
    try:
        idx = _GZ60.index(gz)
    except ValueError:
        return set()
    base = (idx // 10) * 10
    return {_GZ60[(base + 10) % 60][1], _GZ60[(base + 11) % 60][1]}


def _shan_xiang_gui(shan: str, xiang: str = ''):
    """山向贵支集合：干山取干贵、支山以山支为贵位（"丑山作甲戊庚命贵人"），卦山无干不取。"""
    out = set()
    if str(shan or '') in _GUI10:
        out |= _GUI10[str(shan)]
    elif str(shan or '') in _CH12:
        out.add(str(shan))
    if str(xiang or '') in _GUI10:
        out |= _GUI10[str(xiang)]
    elif str(xiang or '') in _CH12:
        out.add(str(xiang))
    return out


def _shan_lu(shan: str):
    """山家禄支：干山取干禄（"癸山禄居子"），支山/卦山无禄。"""
    return _LU10.get(str(shan or ''), '')


def zeri_signals(keti: str, zetiri_type: str, sizhu: dict = None, shan_wx: str = '',
                 shan: str = '', xiang: str = '', sanchuan=None,
                 ri_gan: str = '', ri_zhi: str = '', ming: str = '',
                 yuejiang: str = '') -> dict:
    """择日合参信号：课体键 + 类型键 + 斗首四柱星曜 + 禄马贵/旬空/三传美格。
    2026-08-20 第二批：注解2 五~四章实战案例（两破鬼两支生旺损妻/星陷马空/贪官制化/
    拱禄拱贵/山贵同日禄/龙德课/真朱雀/十三美格），全部可计算、全部出自书例。"""
    sig = {}
    ks = str(keti or '')
    for k in _KETI_KEYS:
        sig['课体_' + k] = k in ks
    cls = zeri_type_class(zetiri_type)
    for k in ('出行', '动土', '安葬', '上任', '开业', '考试', '婚嫁', '立碑', '催龙补气', '其他'):
        sig['类型_' + k] = cls == k
    for k in ('斗首_四柱全廉', '斗首_年柱破鬼', '斗首_月柱武财', '斗首_日时柱元辰武财',
              '斗首_一破鬼两支生旺', '斗首_两破鬼一支生旺', '斗首_三武一元', '斗首_廉子一位无贪官',
              '斗首_双廉休囚元辰弱',
              '斗首_两破鬼两支生旺', '斗首_破鬼休囚', '斗首_年柱贪官', '斗首_贪官重见',
              '斗首_四柱全贪官', '斗首_贪官生元辰', '斗首_年贪月廉', '斗首_年贪月元',
              '斗首_两印夹一元', '斗首_日时柱贪破', '斗首_廉贪并坐', '斗首_武财旺',
              '斗首_元辰旺', '斗首_日时柱元辰',
              '日支_冲山', '日支_冲向', '日支_冲月建',
              '禄马_犯旬空', '禄马_均不落旬空', '日柱_坐禄马',
              '主命禄马_犯旬空', '主命禄马_不空坐日柱',
              '山贵_同日禄', '山禄贵_同太岁', '山禄贵_发传', '三传贵_落旬空',
              '拱日禄', '三传_禄马贵全备', '三传_连续相生', '三传_二贵',
              '三传_午卯子', '三传_斩轮', '三传_铸印乘轩', '四柱_六合在课', '真朱雀_乘传',
              '三传_三合局', '三传_三合拱贵', '三传_三合拱禄',
              '龙德_太岁为日贵', '龙德_太阳缠太岁', '龙德_发传',
              '官爵_四马归一', '官爵_马为山向贵', '官爵_马发传',
              '时泰_太岁月建发传', '德庆_四德发传',
              '斗首_破鬼坐死绝', '斗首_双廉休囚', '斗首_廉子入墓',
              '斗首_元辰弱', '斗首_年贪官休囚',
              '斗首_廉子坐禄贵生旺', '斗首_廉子年月生旺', '斗首_廉子坐休囚',
              '斗首_日时柱贪官',
              '斗首_四柱全元辰', '斗首_三元一武', '斗首_三元一廉', '斗首_二元二武',
              '斗首_两元夹一廉', '斗首_岁日夹战', '斗首_破鬼月',
              '斗首_贪破居六相', '斗首_凶宜在外', '斗首_元辰居墓绝',
              '斗首_元武贴命禄马', '斗首_元武加命',
              '文昌_入课', '天喜_入课', '拱日贵', '建贵', '禄马贵三秀'):
        sig[k] = False
    try:
        _sizhu = sizhu or {}
        _shan_wx = shan_wx or ''
        _STAR = {
            ('土', '土'): '元辰', ('土', '金'): '廉贞', ('土', '水'): '武财', ('土', '木'): '破鬼', ('土', '火'): '贪官',
            ('金', '金'): '元辰', ('金', '水'): '廉贞', ('金', '木'): '武财', ('金', '火'): '破鬼', ('金', '土'): '贪官',
            ('水', '水'): '元辰', ('水', '木'): '廉贞', ('水', '火'): '武财', ('水', '土'): '破鬼', ('水', '金'): '贪官',
            ('木', '木'): '元辰', ('木', '火'): '廉贞', ('木', '土'): '武财', ('木', '金'): '破鬼', ('木', '水'): '贪官',
            ('火', '火'): '元辰', ('火', '土'): '廉贞', ('火', '金'): '武财', ('火', '水'): '破鬼', ('火', '木'): '贪官'}
        _HUQI = {'甲': '土', '己': '土', '乙': '金', '庚': '金', '丙': '水', '辛': '水',
                 '丁': '木', '壬': '木', '戊': '火', '癸': '火'}
        _gz_list = []
        for _col, _alt in (('年', '年柱'), ('月', '月柱'), ('日', '日柱'), ('时', '时柱')):
            _gz = str(_sizhu.get(_col, _sizhu.get(_alt, '')))
            if len(_gz) >= 2:
                _gz_list.append(_gz)
            else:
                _gz_list.append('')
        _stars = [_STAR.get((_shan_wx, _HUQI.get(g[0], '')), '') for g in _gz_list if g]
        _zhis = [g[1] for g in _gz_list if g]
        sig['斗首_四柱全廉'] = len(_stars) == 4 and all(s == '廉贞' for s in _stars)
        sig['斗首_年柱破鬼'] = bool(_stars) and _stars[0] == '破鬼'
        sig['斗首_月柱武财'] = len(_stars) > 1 and _stars[1] == '武财'
        sig['斗首_日时柱元辰武财'] = len(_stars) > 2 and _stars[2] in ('元辰', '武财') and _stars[3] in ('元辰', '武财')
        n_po = _stars.count('破鬼')
        # 破鬼生旺支数：四柱地支落在破鬼化气生旺位（长生/临官/帝旺）的个数——注解2
        # "两破鬼生寅旺午"（火长生寅帝旺午）、"破鬼火死酉病申败卯墓戌…无一个扶助"口径
        _po_wx = ''
        for _g, _s in zip(_gz_list, _stars):
            if _s == '破鬼' and _g:
                _po_wx = _HUQI.get(_g[0], '')
                break
        _po_sw = _WX_SHENGWEI.get(_po_wx, ())
        n_po_sheng = sum(1 for z in _zhis if z in _po_sw)
        sig['斗首_一破鬼两支生旺'] = n_po == 1 and n_po_sheng >= 2
        sig['斗首_两破鬼一支生旺'] = n_po >= 2 and n_po_sheng >= 1
        sig['斗首_两破鬼两支生旺'] = n_po >= 2 and n_po_sheng >= 2
        sig['斗首_破鬼休囚'] = n_po >= 1 and n_po_sheng == 0
        sig['斗首_三武一元'] = _stars.count('武财') >= 3 and _stars.count('元辰') >= 1
        sig['斗首_廉子一位无贪官'] = _stars.count('廉贞') == 1 and _stars.count('贪官') == 0
        sig['斗首_双廉休囚元辰弱'] = _stars.count('廉贞') >= 2 and _stars.count('元辰') <= 1
        # 第八章太岁遇贪官系列
        n_tan = _stars.count('贪官')
        sig['斗首_年柱贪官'] = bool(_stars) and _stars[0] == '贪官'
        sig['斗首_贪官重见'] = n_tan >= 2
        sig['斗首_四柱全贪官'] = len(_stars) == 4 and n_tan == 4
        _tan_wx = ''
        for _g, _s in zip(_gz_list, _stars):
            if _s == '贪官' and _g:
                _tan_wx = _HUQI.get(_g[0], '')
                break
        sig['斗首_贪官生元辰'] = bool(_tan_wx) and _WX_SHENG.get(_tan_wx, '') == _shan_wx
        sig['斗首_年贪月廉'] = len(_stars) > 1 and _stars[0] == '贪官' and _stars[1] == '廉贞'
        sig['斗首_年贪月元'] = len(_stars) > 1 and _stars[0] == '贪官' and _stars[1] == '元辰'
        sig['斗首_两印夹一元'] = (len(_stars) > 3 and _stars[1] == '武财' and _stars[2] == '元辰'
                                  and _stars[3] == '武财')
        sig['斗首_日时柱贪破'] = len(_stars) > 2 and (_stars[2] in ('贪官', '破鬼') or _stars[3] in ('贪官', '破鬼'))
        sig['斗首_廉贪并坐'] = _stars.count('廉贞') >= 2 and n_tan >= 2
        sig['斗首_武财旺'] = any(_s == '武财' and z in _WX_SHENGWEI.get(_HUQI.get(g[0], ''), ())
                                 for g, _s, z in zip(_gz_list, _stars, _zhis))
        sig['斗首_元辰旺'] = any(_s == '元辰' and z in _WX_SHENGWEI.get(_HUQI.get(g[0], ''), ())
                                 for g, _s, z in zip(_gz_list, _stars, _zhis))
        sig['斗首_日时柱元辰'] = len(_stars) > 3 and _stars[2] == '元辰' and _stars[3] == '元辰'
        # ── 2026-08-21 十二长生全表接入：破鬼/廉子/贪官 休囚死绝·入墓 精确判定 ──
        # 破鬼坐死绝：四柱地支按破鬼化气全落休囚位（书例"癸火破鬼死酉病申败卯墓戌"）
        if _po_wx:
            _po_pos = [_wx_position(_po_wx, z) for z in _zhis]
            sig['斗首_破鬼坐死绝'] = n_po >= 1 and bool(_po_pos) and all(p in _XIUQIU for p in _po_pos)
        # 廉子休囚/入墓：按廉贞柱地支（书"廉子宜…不入墓""双廉坐休囚"）
        _lian_wx = ''
        for _g, _s in zip(_gz_list, _stars):
            if _s == '廉贞' and _g:
                _lian_wx = _HUQI.get(_g[0], '')
                break
        n_lian = _stars.count('廉贞')
        _lian_zhis = [g[1] for g, _s in zip(_gz_list, _stars) if _s == '廉贞' and g]
        _rg = str(ri_gan or '')  # 日干（廉子诀断需禄贵；日支段后文会重赋）
        if _lian_wx and _lian_zhis:
            _lian_pos = [_wx_position(_lian_wx, z) for z in _lian_zhis]
            sig['斗首_双廉休囚'] = n_lian >= 2 and all(p in _XIUQIU for p in _lian_pos)
            sig['斗首_廉子入墓'] = any(p == '墓' for p in _lian_pos)
            # 廉子诀四断补全（书"廉子宜一位坐禄贵生旺支不入墓…定生贵子"）：
            # 坐禄贵生旺 = 廉贞柱支落廉化气生旺位（长生/临官/帝旺）或日干禄贵支
            _lian_sheng_wei = {_WX_CS12.get(_lian_wx, {}).get(n, '') for n in ('长生', '临官', '帝旺')}
            _lu_gui = set()
            if _rg:
                _lu_gui.add(_LU10.get(_rg, ''))
                _lu_gui |= _GUI10.get(_rg, set())
            sig['斗首_廉子坐禄贵生旺'] = bool(set(_lian_zhis) & (_lian_sheng_wei | _lu_gui))
            sig['斗首_廉子坐休囚'] = all(p in _XIUQIU for p in _lian_pos)
            # 廉子居年月且年月支生旺（"若在年月坐生旺，而日时遇贪官以枭之主过房"）
            _lian_ym = [g[1] for i, (g, _s) in enumerate(zip(_gz_list, _stars))
                        if _s == '廉贞' and g and i < 2]
            sig['斗首_廉子年月生旺'] = bool(_lian_ym) and all(z in _lian_sheng_wei for z in _lian_ym)
        # 日时柱贪官（书"日时又遇贪官"——与日时柱贪破（含破鬼）区分）
        sig['斗首_日时柱贪官'] = len(_stars) > 2 and (_stars[2] == '贪官' or _stars[3] == '贪官')
        # ── 2026-08-21 注解1第三批：第四章元辰诀六用 + 第三章六相六替诀 ──
        _n_yuan = _stars.count('元辰')
        _n_wu = _stars.count('武财')
        _n_lian = _stars.count('廉贞')
        sig['斗首_四柱全元辰'] = len(_stars) == 4 and _n_yuan == 4
        sig['斗首_三元一武'] = _n_yuan == 3 and _n_wu == 1
        sig['斗首_三元一廉'] = _n_yuan == 3 and _n_lian == 1
        sig['斗首_二元二武'] = _n_yuan == 2 and _n_wu == 2
        _s0 = _stars[0] if _stars else ''
        _s1 = _stars[1] if len(_stars) > 1 else ''
        _s2 = _stars[2] if len(_stars) > 2 else ''
        _s3 = _stars[3] if len(_stars) > 3 else ''
        sig['斗首_两元夹一廉'] = _s0 == '元辰' and _s1 == '廉贞' and _s2 == '元辰'
        sig['斗首_岁日夹战'] = _s0 == '元辰' and _s1 == '贪官' and _s2 == '元辰'
        sig['斗首_破鬼月'] = _s1 == '破鬼'
        # 贪破居六相支（"贪狼和破鬼居在六相的地支上便能生灾祸了"）
        _tp_zhis = [g[1] for g, _s in zip(_gz_list, _stars) if _s in ('贪官', '破鬼') and g]
        _tp_wx = ''
        for _g, _s in zip(_gz_list, _stars):
            if _s in ('贪官', '破鬼') and _g:
                _tp_wx = _HUQI.get(_g[0], '')
                break
        sig['斗首_贪破居六相'] = bool(_tp_zhis) and bool(_tp_wx) and any(
            _wx_position(_tp_wx, z) in _XIANG_WEI for z in _tp_zhis)
        # 凶宜在外：贪破只在年月、日时必元武（"唯求二凶在年月，日时断要元武"）
        sig['斗首_凶宜在外'] = (len(_stars) == 4 and (_s0 in ('贪官', '破鬼') or _s1 in ('贪官', '破鬼'))
                                and _s2 in ('元辰', '武财') and _s3 in ('元辰', '武财'))
        # 元辰居墓绝（"元廉居墓绝，人才不得兴"）
        _y_zhis = [g[1] for g, _s in zip(_gz_list, _stars) if _s == '元辰' and g]
        _y_wx = ''
        for _g, _s in zip(_gz_list, _stars):
            if _s == '元辰' and _g:
                _y_wx = _HUQI.get(_g[0], '')
                break
        sig['斗首_元辰居墓绝'] = bool(_y_zhis) and bool(_y_wx) and any(
            _wx_position(_y_wx, z) in ('墓', '绝') for z in _y_zhis)
        # 财马贴元辰/元武逢岁驾：本山元武加本命禄马支/本命支（第四章三/四）
        _mgd = str(ming or '')
        if len(_mgd) >= 2 and _mgd[1] in _MA12:
            _yw_zhis = [g[1] for g, _s in zip(_gz_list, _stars) if _s in ('元辰', '武财') and g]
            _m_lu = _LU10.get(_mgd[0], '')
            _m_ma = _MA12.get(_mgd[1], '')
            sig['斗首_元武贴命禄马'] = bool(_yw_zhis) and (bool(_m_lu) and _m_lu in _yw_zhis
                                                          or bool(_m_ma) and _m_ma in _yw_zhis)
            sig['斗首_元武加命'] = bool(_yw_zhis) and _mgd[1] in _yw_zhis
        # 贵人会文昌：命干文昌优先、日干兜底（"甲午命以巳为文昌…造屋会元及第"）
        _wc_g = (_mgd[0] if len(_mgd) >= 2 and _mgd[0] in _WENCHANG else '') or _rg
        if _wc_g in _WENCHANG and _zhis:
            sig['文昌_入课'] = _WENCHANG[_wc_g] in _zhis
        # 生气元廉抱天喜：主命天喜支（红鸾对宫）入四柱
        if len(_mgd) >= 2 and _mgd[1] in _HONGLUAN:
            _tx = _CH12.get(_HONGLUAN[_mgd[1]], '')
            sig['天喜_入课'] = bool(_tx) and _tx in _zhis
        # 拱贵建贵（"癸未癸亥名拱卯贵。癸卯癸巳名建贵"——日干/命干贵支）
        _gui_all2 = set(_GUI10.get(_rg, set()))
        if len(_mgd) >= 2 and _mgd[0] in _GUI10:
            _gui_all2 |= _GUI10[_mgd[0]]
        if _gui_all2 and _zhis:
            sig['建贵'] = bool(set(_zhis) & _gui_all2)
            sig['拱日贵'] = any(g in _SANHE and g not in _zhis and all(x in _zhis for x in _SANHE[g])
                                for g in _gui_all2)
        # 禄马贵三秀（"取卯年为壬命建贵，取亥月壬命建禄，取申日为午命建马。三秀俱全"）
        if len(_mgd) >= 2 and _mgd[0] in _LU10 and _mgd[1] in _MA12:
            _m3_lu = _LU10.get(_mgd[0], '')
            _m3_ma = _MA12.get(_mgd[1], '')
            _m3_gui = _GUI10.get(_mgd[0], set())
            sig['禄马贵三秀'] = bool(_m3_lu) and _m3_lu in _zhis and bool(_m3_ma) and _m3_ma in _zhis                                 and bool(_m3_gui & set(_zhis))
        # 元辰衰弱（柱数近似：≤1柱——待样本复核的"元辰又衰弱"口径）
        sig['斗首_元辰弱'] = _stars.count('元辰') <= 1
        # 年柱贪官坐休囚支（书"贪官止一位在年休囚"）
        if _stars and _stars[0] == '贪官' and _gz_list and _gz_list[0]:
            _tan_pos = _wx_position(_HUQI.get(_gz_list[0][0], ''), _gz_list[0][1])
            sig['斗首_年贪官休囚'] = _tan_pos in _XIUQIU
        # 日支冲山/向/月建（要诀禁忌：日支与山家相冲=冲山）
        _rg = str(ri_gan or '')
        _rz = str(ri_zhi or '')
        if not _rz and _gz_list and len(_gz_list) > 2:
            _rz = _gz_list[2][1] if _gz_list[2] else ''
        _xiang = xiang or _CH12.get(str(shan or ''), '')
        _yue_zhi = (_gz_list[1][1] if len(_gz_list) > 1 and _gz_list[1] else '')
        if _rz:
            sig['日支_冲山'] = bool(shan) and _rz == _CH12.get(str(shan), '')
            sig['日支_冲向'] = bool(_xiang) and _rz == _CH12.get(str(_xiang), '')
            sig['日支_冲月建'] = bool(_yue_zhi) and _rz == _CH12.get(_yue_zhi, '')
            # 旬空（以日柱定旬——"四柱皆是甲辰旬中，空亡寅卯"）
            _day_gz = (_gz_list[2] if len(_gz_list) > 2 else '') or ''
            if not _rg and _day_gz:
                _rg = _day_gz[0]
            if not _rz and _day_gz:
                _rz = _day_gz[1]
            _kw = _xun_kong_of(_rg, _rz)
            _lu = _LU10.get(_rg, '')
            _ma = _MA12.get(_rz, '')
            sig['禄马_犯旬空'] = bool(_kw) and ((_lu in _kw) or (_ma in _kw))
            sig['禄马_均不落旬空'] = bool(_kw) and bool(_lu) and bool(_ma) and (_lu not in _kw) and (_ma not in _kw)
            sig['日柱_坐禄马'] = bool(_rz) and (_rz == _lu or _rz == _ma)
            # 主命禄马（注解2六/七：甲子命禄马寅落甲辰旬空→考退前程；甲申命庚寅日不空坐日柱→官至太守）
            _mg = str(ming or '')
            if len(_mg) >= 2 and _mg[0] in _LU10 and _mg[1] in _MA12 and _kw:
                _mlu = _LU10.get(_mg[0], '')
                _mma = _MA12.get(_mg[1], '')
                sig['主命禄马_犯旬空'] = (_mlu in _kw) or (_mma in _kw)
                sig['主命禄马_不空坐日柱'] = (_mlu not in _kw) and (_mma not in _kw) and _rz in (_mlu, _mma)
            # 四柱含日支六合（注解2"卯戌六合不能化解卯酉相冲"）
            sig['四柱_六合在课'] = bool(_rz) and bool(_HE12.get(_rz, '')) and _HE12.get(_rz, '') in _zhis
        # 山向贵禄与三传
        _sc = ([sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
               if isinstance(sanchuan, dict) else list(sanchuan or []))
        _sc = [str(z) for z in _sc if z]
        _gui_sx = _shan_xiang_gui(shan, _xiang)
        _lu_ri = _LU10.get(_rg, '')
        if _gui_sx and _lu_ri:
            sig['山贵_同日禄'] = _lu_ri in _gui_sx
        _nian_zhi = (_gz_list[0][1] if _gz_list and _gz_list[0] else '')
        _sl = _shan_lu(shan)
        if _nian_zhi:
            sig['山禄贵_同太岁'] = _nian_zhi in (_gui_sx | ({_sl} if _sl else set()))
        if _sc and _gui_sx:
            sig['山禄贵_发传'] = bool(set(_sc) & (_gui_sx | ({_sl} if _sl else set())))
        if _sc and _rz:
            _kw2 = _xun_kong_of(_rg, _rz)
            _gui_all = (_GUI10.get(_rg, set()) | _gui_sx)
            sig['三传贵_落旬空'] = bool(_kw2) and any(z in _kw2 and z in _gui_all for z in _sc)
        if _lu_ri and _zhis and _lu_ri in _SANHE:
            _gong = _SANHE[_lu_ri]
            sig['拱日禄'] = _lu_ri not in _zhis and all(x in _zhis for x in _gong)
        if _sc and _lu_ri:
            _ma_ri = _MA12.get(_rz, '')
            _gui_ri = _GUI10.get(_rg, set())
            sig['三传_禄马贵全备'] = _lu_ri in _sc and bool(_ma_ri) and _ma_ri in _sc and bool(set(_sc) & _gui_ri)
            if len(_sc) == 3:
                wx = [_ZHI_WX.get(z, '') for z in _sc]
                ok = all(wx)
                sig['三传_连续相生'] = ok and ((_WX_SHENG.get(wx[0], '') == wx[1] and _WX_SHENG.get(wx[1], '') == wx[2])
                                               or (_WX_SHENG.get(wx[2], '') == wx[1] and _WX_SHENG.get(wx[1], '') == wx[0]))
                sig['三传_二贵'] = ok and _gui_ri and _gui_ri <= set(_sc)
                sig['三传_午卯子'] = set(_sc) == {'午', '卯', '子'}
                # 斩轮课（卯戌巳，卯为车轮）/铸印乘轩课（巳戌卯，巳中丙火合戌中辛金铸印）——
                # 十三美格之11/12，按三传顺序区分
                sig['三传_斩轮'] = _sc == ['卯', '戌', '巳']
                sig['三传_铸印乘轩'] = _sc == ['巳', '戌', '卯']
                # 真朱雀：日干贵支含申者（乙己）自申贵逆数朱雀到午（注解2第十章四）
                sig['真朱雀_乘传'] = bool(_gui_ri & {'申'}) and '午' in _sc
        # ── 2026-08-21 十三美格剩余八课：龙德/官爵/时泰/和美合欢回环/德庆 ──
        _scs = set(_sc)
        _he_sanj = _scs in ({'亥', '卯', '未'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'申', '子', '辰'})
        sig['三传_三合局'] = len(_sc) == 3 and _he_sanj
        sig['三传_三合拱贵'] = sig['三传_三合局'] and bool(_scs & _gui_sx)
        sig['三传_三合拱禄'] = sig['三传_三合局'] and bool(_lu_ri) and _lu_ri in _sc
        # 龙德课：太岁之支为本日贵人 + 月将太阳缠临太岁支 + 发三传
        _yj = str(yuejiang or '')
        if _yj and _rg and _nian_zhi:
            sig['龙德_太岁为日贵'] = _nian_zhi in _GUI10.get(_rg, set())
            sig['龙德_太阳缠太岁'] = _yj == _nian_zhi
            sig['龙德_发传'] = _yj in _sc
        # 官爵课：太岁/月建/日元/生命四者共为一马 + 该马发用（书例丁亥癸卯乙未+乙亥命均马巳）
        _mgb = str(ming or '')
        _mz4 = [_nian_zhi, _yue_zhi, _rz, (_mgb[1] if len(_mgb) >= 2 else '')]
        _ma4 = [_MA12.get(z, '') for z in _mz4]
        sig['官爵_四马归一'] = bool(_ma4[0]) and all(m == _ma4[0] for m in _ma4)
        sig['官爵_马为山向贵'] = bool(_ma4[0]) and _ma4[0] in (_gui_sx | ({_sl} if _sl else set()))
        sig['官爵_马发传'] = bool(_ma4[0]) and _ma4[0] in _sc
        # 时泰课：太岁、月建之支皆发传
        sig['时泰_太岁月建发传'] = bool(_nian_zhi) and bool(_yue_zhi) and _nian_zhi in _sc and _yue_zhi in _sc
        # 德庆课：止有二日——九月丙子（德神巳发传）、三月壬午（德神亥发传）
        sig['德庆_四德发传'] = ((_rg == '丙' and _rz == '子' and _yue_zhi == '戌' and '巳' in _sc)
                                or (_rg == '壬' and _rz == '午' and _yue_zhi == '辰' and '亥' in _sc))
    except Exception:
        pass
    return sig


def load_zeri_rules(path: str = '') -> list:
    p = path or os.path.join(_ROOT, 'data', 'zeri_hecan_rules.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('rules', []) if isinstance(d, dict) else d
    except Exception:
        return []


# ── 规则短标签（2026-08-21 批量格局统计/前端徽标用；未收录回退 id）──
_RULE_LABELS = {
    'ZR-001': '伏吟·出行', 'ZR-002': '伏吟·动土', 'ZR-003': '伏吟·安葬', 'ZR-004': '伏吟·上任',
    'ZR-005': '返吟·出行', 'ZR-006': '八专·安葬', 'ZR-101': '官爵课', 'ZR-102': '亨通课',
    'ZR-103': '元首课', 'ZR-104': '龙德课', 'ZR-201': '亥子丑水局',
    'ZY-001': '四柱全廉', 'ZY-002': '破鬼把门', 'ZY-003': '破鬼克妻', 'ZY-004': '三武一元',
    'ZY-005': '双廉损丁', 'ZY-006': '两破鬼两支生旺', 'ZY-007': '两破鬼一支生旺',
    'ZY-008': '破鬼休囚武财旺', 'ZY-009': '廉子生贵子', 'ZY-010': '四贪全吉',
    'ZY-011': '太岁遇贪官', 'ZY-012': '武财制贪官', 'ZY-013': '贪官制化', 'ZY-014': '贪官重见',
    'ZY-015': '年贪月廉', 'ZY-016': '年贪月元', 'ZY-017': '两印夹一元', 'ZY-018': '廉贪并坐',
    'ZY-019': '日时柱贪破', 'ZY-020': '武财元辰旺', 'ZY-021': '禄马犯旬空', 'ZY-022': '主命禄马空亡',
    'ZY-023': '主命禄马坐日柱', 'ZY-024': '禄马不空', 'ZY-025': '山贵同日禄', 'ZY-026': '山禄贵同太岁',
    'ZY-027': '山禄贵发传', 'ZY-028': '三传贵落空', 'ZY-029': '拱日禄', 'ZY-030': '荣华课',
    'ZY-031': '亨通课', 'ZY-032': '富贵课', 'ZY-033': '华盖乘轩', 'ZY-034': '斩轮课',
    'ZY-035': '真朱雀', 'ZY-036': '日支冲山', 'ZY-037': '六合不解冲', 'ZY-038': '龙德课',
    'ZY-039': '官爵课', 'ZY-040': '时泰课', 'ZY-041': '和美课', 'ZY-042': '合欢课',
    'ZY-043': '回环课', 'ZY-044': '德庆课', 'ZY-045': '铸印乘轩', 'ZY-046': '廉子过房',
    'ZY-047': '廉子出外死',
}


def zeri_rule_label(rid) -> str:
    """规则短标签（批量统计与前端徽标用）。"""
    return _RULE_LABELS.get(str(rid or ''), str(rid or ''))


def zeri_hecan_judge(sig: dict, rules: list = None) -> list:
    """择日合参判定：全条件命中才触发。返回触发规则（含结论/叙事/出处）。"""
    rs = rules if rules is not None else load_zeri_rules()
    out = []
    for r in rs:
        conds = r.get('条件', [])
        if not conds:
            continue
        hit = 0
        for c in conds:
            s = str(c.get('signal', ''))
            got = bool(sig.get(s, False))
            want = bool(c.get('value', True))
            ok = got == want
            if c.get('neg'):
                ok = not ok
            if ok:
                hit += 1
        if hit == len(conds):
            out.append({'id': r.get('id', ''), '结论': r.get('结论', ''),
                        '叙事': r.get('叙事', ''), '出处': r.get('出处', ''),
                        '置信度': r.get('置信度', 0)})
    return out


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    rs = load_zeri_rules()
    print('择日合参规则库:', len(rs), '条')
    sig = zeri_signals('伏吟课', '提车')
    print('提车+伏吟课 信号:', sig['课体_伏吟'], sig['类型_出行'])
    for o in zeri_hecan_judge(sig):
        print('触发:', o['id'], o['结论'], '|', o['叙事'][:44])
