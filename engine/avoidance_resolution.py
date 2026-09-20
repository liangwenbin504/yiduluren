#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
避忌化解判定模块 (engine/avoidance_resolution.py)
=================================================
【憨爷/用户拍板 2026-08-25】安葬等择日文书"不用避忌"的判定依据。

核心前提：
  * 好课 = 坐山、向山都不被制（被制的课评分已过滤）
  * 故好课里坐山/向山冲力恒在 → 被"冲"的属相必受伤，除非化解

攻击力量排序（用户确认）：冲 > 刑 > 克（无情克凶/有情克吉） > 害

判定模型：
  ① 冲 → 【必避】除非 B（合神在课且有力）或 C（被冲者得生）
  ② 刑/害/破（非冲）→ 攻击者是否入课（四课+三传+年月日时四柱）：
       - 不入课 → 伤害不了 → 不避
       - 入课但被课中神制 → 力量弱 → 不避
       - 入课且不被制 → 力量在 → 避
  ③ 克 → 有情克（阳克阴/阴克阳）=吉不管；无情克（阳克阳/阴克阴）=凶按②

得生（被冲者得生）细化——生金之土按墓库分（用户确认）：
  * 丑（金库墓神）：墓而不生，不作救神
  * 辰（水库）、未（木库）、戌（火库）：当旺才作救神
      当旺 = ①月令土月(辰戌丑未)/火月(巳午生土)，或
             ②四课三传中该库土的下神(地盘)为火/土局长生(寅)临官(巳)帝旺(午)
      不当旺：戌=申入鬼墓凶；未=财库伤父母/饮食病；辰=水库不作救
  * 生我者按五行：生金者土（辰戌丑未）、生木者水、生火者木、生土者火、生水者金
     （非库土生我者直接按五行相生判救）

力量等级（用户确认）：
  日上神（干上神）：能解，主当下，治标
  支上神          ：能解，主长久，治本
  干阴神/支阴神   ：力弱 / 应期久
  三传            ：参与生助或克制

用法：
    from engine.avoidance_resolution import judge_avoidance
    result = judge_avoidance(
        shan='寅', xiang='申',
        sizhu_zhi=['戌','寅','午','子'],     # 年月日时四柱地支
        tiandi_pan={...},                    # {地盘: 天盘}
        gan_shang_shen='丑', zhi_shang_shen='巳',
        gan_yin_shen='子', zhi_yin_shen='辰',
        sanchuan=['子','亥','戌'],
    )
"""

LIU_HE = {
    '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
    '辰': '酉', '巳': '申', '午': '未', '未': '午',
    '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
}
LIU_CHONG = {
    '子': '午', '丑': '未', '寅': '申', '卯': '酉',
    '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
    '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
}
SAN_HE_GROUPS = [
    ('申', '子', '辰'), ('亥', '卯', '未'),
    ('寅', '午', '戌'), ('巳', '酉', '丑')
]
XING_MAP = {
    # 双向互刑
    '子': '卯', '卯': '子',
    # 单向循环刑（木局：寅→巳→申→寅，不能反向）
    '寅': '巳', '巳': '申', '申': '寅',
    # 单向循环刑（土局：丑→戌→未→丑，不能反向）
    '丑': '戌', '戌': '未', '未': '丑',
    # 自刑（辰午酉亥需课中出现两个才能自刑，单独一个不能自刑）
    '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'
}

# 自刑地支集合
SELF_XING_ZHIS = {'辰', '午', '酉', '亥'}
LIU_HAI = {
    '子': '未', '未': '子', '丑': '午', '午': '丑',
    '寅': '巳', '巳': '寅', '卯': '辰', '辰': '卯',
    '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'
}
XIANG_PO = {
    '子': '酉', '酉': '子', '寅': '亥', '亥': '寅',
    '卯': '午', '午': '卯', '辰': '丑', '丑': '辰',
    '巳': '申', '申': '巳', '未': '戌', '戌': '未'
}
ZHI_WX = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}
# 地支对应属相（鼠牛虎兔龙蛇马羊猴鸡狗猪）
ZHI_SHENGXIAO = {
    '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔', '辰': '龙', '巳': '蛇',
    '午': '马', '未': '羊', '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
}
SHENG_ME = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE_MAP = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
YANG_ZHI = {'子', '寅', '辰', '午', '申', '戌'}
# 火/土局长生临官帝旺（土随火局：寅午戌）
HUO_TU_WANG = {'寅', '巳', '午'}
TU_YUE = {'辰', '戌', '丑', '未'}
HUO_YUE = {'巳', '午'}

# ── 五行十二长生临地（用户确认：被冲之支临自身旺地则不怕冲）──
# 十二长生序：长生 沐浴 冠带 临官 帝旺 衰 病 死 墓 绝 胎 养
# 旺地 = 长生/冠带/临官/帝旺/胎/养；败地 = 沐浴（子为寅木沐浴败地，不好）
# 五行起点（土双位：主申次寅，与 engine/bifa_detector.py 一致）
_WX_CS_START = {'木': '亥', '火': '寅', '土': '申', '金': '巳', '水': '申'}
_ZHI_ORDER = '亥子丑寅卯辰巳午未申酉戌'
# 每五行：地支 → 十二长生位名（从长生起点顺行）
def _build_cs_table():
    tbl = {}
    for wx, start in _WX_CS_START.items():
        start_i = _ZHI_ORDER.index(start)
        names = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        # 阳干顺行 12 位（土按申起顺行：申酉戌亥子丑寅卯辰巳午未）
        for k in range(12):
            z = _ZHI_ORDER[(start_i + k) % 12]
            tbl.setdefault(z, {})[wx] = names[k]
        # 土双位次值：火土同宫（土次长生寅 → 从寅顺行）
        if wx == '土':
            start_i2 = _ZHI_ORDER.index('寅')
            for k in range(12):
                z = _ZHI_ORDER[(start_i2 + k) % 12]
                tbl.setdefault(z, {}).setdefault(wx, names[k])
    return tbl
_CS_TBL = _build_cs_table()

# 十二长生旺地集合（临此位=得根不怕冲）
_CS_WANG = {'长生', '冠带', '临官', '帝旺', '胎', '养'}


def _zhi_wx(zhi):
    return ZHI_WX.get(zhi, '')


def _cs_pos(zhi, wx):
    """地支在指定五行的十二长生位名（如 子→木:沐浴）。"""
    return (_CS_TBL.get(zhi) or {}).get(wx, '')


def _attack_types(zhi, pool=None, core_pool=None, self_xing_extra_count=0):
    """
    返回 {攻击支: [类型...]}：冲/刑/害/破 该地支的所有支及其类型。
    
    Args:
        zhi: 目标地支
        pool: 课中所有支的集合（用于判断普通刑冲等）
        core_pool: 仅四课三传的地支集合（用于判断自刑条件）
        self_xing_extra_count: 自刑额外计数（安葬类特殊规则）
            安葬日下矿时，如果坐山是辰午酉亥之一，坐山本身算作1个，
            加上课中的1个，即使课中只有1个也满足自刑条件。
    
    自刑条件：辰、午、酉、亥需课中(四课三传)出现两个才能自刑，
    单独一个不能自刑。安葬类特殊规则可通过 self_xing_extra_count 增加计数。
    """
    out = {}
    c = LIU_CHONG.get(zhi)
    if c: out.setdefault(c, []).append('冲')
    x = XING_MAP.get(zhi)
    if x:
        if x == zhi:
            # 自刑（辰午酉亥）：需要四课三传中出现两个（不含年月日时四柱）
            _check_pool = core_pool or pool
            _count = _count_in_pool(zhi, _check_pool)
            if _count + self_xing_extra_count >= 2:
                out.setdefault(x, []).append('刑')
            # 否则跳过自刑（单独一个不能自刑）
        else:
            # 普通刑（双向互刑或单向循环刑）
            out.setdefault(x, []).append('刑')
    h = LIU_HAI.get(zhi)
    if h: out.setdefault(h, []).append('害')
    p = XIANG_PO.get(zhi)
    if p: out.setdefault(p, []).append('破')
    return out


def _count_in_pool(zhi, pool):
    """
    计算地支在课池中出现的次数。
    
    Args:
        zhi: 目标地支
        pool: 课池（可以是 set 或 list）
    
    Returns:
        int: 出现次数
    """
    if isinstance(pool, set):
        # set 无法统计重复次数，需要用 _course_pool_with_count
        return 1 if zhi in pool else 0
    elif isinstance(pool, dict):
        return pool.get(zhi, 0)
    elif isinstance(pool, (list, tuple)):
        return pool.count(zhi)
    return 0


def _course_pool_with_count(positions):
    """
    课中所有支及出现次数：四课上神 + 三传 + 年月日时四柱地支。
    
    Returns:
        dict: {地支: 出现次数}
    """
    count = {}
    for v in (positions.get('gan_shang'), positions.get('zhi_shang'),
              positions.get('gan_yin'), positions.get('zhi_yin')):
        if v and v in ZHI_WX:
            count[v] = count.get(v, 0) + 1
    for v in (positions.get('sanchuan') or []):
        if v and v in ZHI_WX:
            count[v] = count.get(v, 0) + 1
    for v in (positions.get('sizhu_zhi') or []):
        if v and v in ZHI_WX:
            count[v] = count.get(v, 0) + 1
    return count


def _course_core_pool_with_count(positions):
    """
    仅统计四课三传的地支及次数（不含年月日时四柱）。
    用于自刑条件判定：辰午酉亥需课中（四课三传）出现两个才能自刑，
    单独的一个不能自刑。
    
    Returns:
        dict: {地支: 出现次数}
    """
    count = {}
    for v in (positions.get('gan_shang'), positions.get('zhi_shang'),
              positions.get('gan_yin'), positions.get('zhi_yin')):
        if v and v in ZHI_WX:
            count[v] = count.get(v, 0) + 1
    for v in (positions.get('sanchuan') or []):
        if v and v in ZHI_WX:
            count[v] = count.get(v, 0) + 1
    return count


def _allies(zhi):
    res = set()
    h = LIU_HE.get(zhi)
    if h: res.add(h)
    for g in SAN_HE_GROUPS:
        if zhi in g:
            res.update(g)
            break
    return res


def _course_pool(positions):
    """课中所有支：四课上神 + 三传 + 年月日时四柱地支。"""
    pool = set()
    for v in (positions.get('gan_shang'), positions.get('zhi_shang'),
              positions.get('gan_yin'), positions.get('zhi_yin')):
        if v and v in ZHI_WX:
            pool.add(v)
    for v in (positions.get('sanchuan') or []):
        if v and v in ZHI_WX:
            pool.add(v)
    for v in (positions.get('sizhu_zhi') or []):
        if v and v in ZHI_WX:
            pool.add(v)
    return pool


def _is_controlled(zhi, positions):
    """某支是否被课中神制：被刑冲害破，或五行被克。"""
    pool_set = _course_pool(positions)
    pool_count = _course_pool_with_count(positions)
    core_pool_count = _course_core_pool_with_count(positions)
    if not pool_set:
        return False
    # 使用带计数的 pool 来判断（core_pool_count 用于自刑条件判断）
    attack_map = _attack_types(zhi, pool_count, core_pool_count)
    if any(p in attack_map for p in pool_set):
        return True
    wx = ZHI_WX.get(zhi, '')
    if wx:
        killer_wx = KE_MAP.get(wx)
        if killer_wx and any(ZHI_WX.get(p) == killer_wx for p in pool_set):
            return True
    return False


def _ku_tu_wang(zhi, positions):
    """
    库土（辰戌丑未）当旺判定（用户确认）：
      ① 月令：月支为土月(辰戌丑未)或火月(巳午，火生土)
      ② 课中下神：该库土在天地盘中的地盘位置(下神)为 寅/巳/午（火土局长生临官帝旺）
    """
    if zhi not in TU_YUE:
        return False
    sizhu = positions.get('sizhu_zhi') or []
    # ① 月令（四柱第二位=月支）
    if len(sizhu) >= 2 and sizhu[1] in TU_YUE | HUO_YUE:
        return True
    # ② 下神：tiandi_pan {地盘: 天盘}，该库土作为天盘 → 其地盘位置
    tdp = positions.get('tiandi_pan') or {}
    for di, tian in tdp.items():
        if tian == zhi and di in HUO_TU_WANG:
            return True
    return False


def _sheng_me_present(zhi, positions):
    """
    被冲属相是否得生（含库土墓库细分，用户确认）：
      生我五行者（如生金者土）出现在课中：
        - 非库土（如生木者水=亥子，生火者木=寅卯...）直接按相生判救
        - 库土（辰戌丑未）：
            丑（金墓）→ 墓而不生，不作救
            辰/未/戌 → 当旺才作救；不当旺：
                戌 → 申入鬼墓凶（注凶不救）
                未 → 财库伤父母/饮食病（注凶不救）
                辰 → 水库不作救
    返回 (是否得生, 说明)
    """
    wx = ZHI_WX.get(zhi, '')
    if not wx:
        return False, ''
    sheng_wx = SHENG_ME.get(wx)
    if not sheng_wx:
        return False, ''
    # 课中找生我五行的支
    sheng_zhi = [v for v in _course_pool(positions) if ZHI_WX.get(v) == sheng_wx]
    if not sheng_zhi:
        return False, ''
    for sz in sorted(sheng_zhi):
        if sz in TU_YUE:
            # 库土细分
            if sz == '丑':
                continue  # 金墓，墓而不生
            if _ku_tu_wang(sz, positions):
                return True, f'库土{sz}当旺生{wx}'
            # 不当旺
            if sz == '戌':
                return False, f'戌为火库不当旺，{zhi}入鬼墓凶'
            if sz == '未':
                return False, f'未为木库不当旺，财库伤父母/饮食病'
            # 辰不当旺
            continue
        else:
            return True, f'{sz}生{wx}'
    return False, ''


def judge_avoidance(shan='', xiang='', ri_zhi='',
                    sizhu_zhi=None, tiandi_pan=None,
                    gan_shang_shen='', zhi_shang_shen='',
                    gan_yin_shen='', zhi_yin_shen='',
                    sanchuan=None, shan_only=False):
    """
    避忌判定主函数。
    
    Args:
        shan_only: 是否只检查坐山（安葬文书专用，默认False）
            安葬类特殊规则：如果坐山是辰午酉亥之一，坐山本身算作1个，
            加上课中的1个，即使课中只有1个也满足自刑条件。
    
    Returns:
        dict: {
            'attacked': [{zhi, by, types, zodiac_zhi, zodiac_by}, ...],
            'resolved': bool,
            'reasons': [str, ...],
            'need_avoid': bool,
            'avoid_list': [{zhi, zodiac, types_str}, ...],  # 需要避忌的详细列表
        }
    """
    sanchuan = [s for s in (sanchuan or []) if s]
    positions = {
        'gan_shang': gan_shang_shen, 'zhi_shang': zhi_shang_shen,
        'gan_yin': gan_yin_shen, 'zhi_yin': zhi_yin_shen,
        'sanchuan': sanchuan,
        'sizhu_zhi': sizhu_zhi or [],
        'tiandi_pan': tiandi_pan or {},
    }
    
    # 根据 shan_only 决定检查范围
    if shan_only:
        bases = [shan] if shan and shan in ZHI_WX else []
    else:
        bases = [s for s in (shan, xiang) if s and s in ZHI_WX]
        if not bases and ri_zhi and ri_zhi in ZHI_WX:
            bases = [ri_zhi]
    
    # 安葬类特殊规则：如果坐山是辰午酉亥之一，坐山本身算作1个，
    # 加上课中的1个，即使课中只有1个也满足自刑条件
    # 这是安葬日下矿时的特殊避忌规则
    self_xing_extra_count = 0
    if shan_only and shan and shan in SELF_XING_ZHIS:
        self_xing_extra_count = 1  # 坐山本身算作1个
    
    # 获取带计数的课池（用于自刑判断：辰午酉亥需出现两个才自刑）
    pool_with_count = _course_pool_with_count(positions)
    core_pool_with_count = _course_core_pool_with_count(positions)
    
    attacked = []
    for b in bases:
        for t, types in _attack_types(b, pool_with_count, core_pool_with_count, 
                                        self_xing_extra_count).items():
            attacked.append({
                'zhi': t, 
                'by': b, 
                'types': types,
                'zodiac_zhi': ZHI_SHENGXIAO.get(t, ''),
                'zodiac_by': ZHI_SHENGXIAO.get(b, ''),
            })

    reasons = []
    avoid_list = []  # 需要避忌的详细列表
    resolved = True
    for item in attacked:
        target = item['zhi']
        by = item['by']
        types = item['types']
        pool = _course_pool(positions)
        
        # 生成类型描述
        types_str = '/'.join(types)
        zodiac_target = item['zodiac_zhi']
        zodiac_by = item['zodiac_by']

        if '冲' in types:
            # B. 合神救合
            b_ok = False
            for ally in _allies(target):
                if ally in pool and not _is_controlled(ally, positions):
                    b_ok = True
                    reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：合神{ally}在课且有力，合住化解')
                    break
            if b_ok:
                continue
            # C. 得生（库土细分）
            c_ok, c_note = _sheng_me_present(target, positions)
            if c_ok:
                reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：{c_note}，不怕冲')
                continue
            if c_note:
                reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：{c_note}，需避')
                resolved = False
                avoid_list.append({
                    'zhi': target,
                    'zodiac': zodiac_target,
                    'types_str': types_str,
                    'reason': c_note,
                })
                continue
            # D. 临自身十二长生旺地
            tdp = positions.get('tiandi_pan') or {}
            xia_shen = ''
            for di, tian in tdp.items():
                if tian == target:
                    xia_shen = di
                    break
            if xia_shen:
                wx = _zhi_wx(target)
                cs = _cs_pos(xia_shen, wx)
                if cs in _CS_WANG:
                    reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：临{xia_shen}({cs})自身旺地，得根不怕冲')
                    continue
                if cs == '沐浴':
                    reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：临{xia_shen}(沐浴败地)，不好')
                    resolved = False
                    avoid_list.append({
                        'zhi': target,
                        'zodiac': zodiac_target,
                        'types_str': types_str,
                        'reason': f'临{xia_shen}(沐浴败地)',
                    })
                    continue
                reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：临{xia_shen}({cs})非旺地')
                resolved = False
                avoid_list.append({
                    'zhi': target,
                    'zodiac': zodiac_target,
                    'types_str': types_str,
                    'reason': f'临{xia_shen}({cs})非旺地',
                })
                continue
            resolved = False
            reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})冲：无合救不得生，必避')
            avoid_list.append({
                'zhi': target,
                'zodiac': zodiac_target,
                'types_str': types_str,
                'reason': '无合救不得生',
            })
            continue

        # 非冲：刑/害/破
        # 安葬类特殊规则：自刑（辰午酉亥）直接避忌，不需要检查是否被制
        if self_xing_extra_count > 0 and target == by and target in SELF_XING_ZHIS and '刑' in types:
            resolved = False
            reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by})自刑：安葬日下矿，坐山{by}算作1个，加课中{target}=2个，需避')
            avoid_list.append({
                'zhi': target,
                'zodiac': zodiac_target,
                'types_str': types_str,
                'reason': '安葬日下矿自刑（坐山+课中=2个）',
            })
            continue
        
        if by in pool:
            if _is_controlled(by, positions):
                reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by}){types_str}：{by}入课但被制，力量弱，不避')
                continue
            resolved = False
            reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by}){types_str}：{by}入课且有力，需避')
            avoid_list.append({
                'zhi': target,
                'zodiac': zodiac_target,
                'types_str': types_str,
                'reason': f'{by}入课且有力',
            })
            continue
        else:
            reasons.append(f'{target}({zodiac_target}) 被{by}({zodiac_by}){types_str}：{by}不入课，伤害不了，不避')
            continue

    return {
        'attacked': attacked,
        'resolved': resolved,
        'reasons': reasons,
        'need_avoid': not resolved,
        'avoid_list': avoid_list,  # 需要避忌的详细列表
    }


if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("== avoidance_resolution 自测 ==")
    # 2030-02-28 子：寅山申向，四柱 庚戌戊寅甲午甲子（月支寅=木月），
    # 天地盘（月将亥加子）：丑→子 亥→戌 午→巳 卯→寅 子→亥 寅→丑 巳→辰 戌→酉 未→午 申→未 辰→卯 酉→申
    # 四课上神：丑(天空)/子/巳(朱雀)/辰；三传 子/亥/戌
    tdp = {'丑': '子', '亥': '戌', '午': '巳', '卯': '寅', '子': '亥', '寅': '丑',
           '巳': '辰', '戌': '酉', '未': '午', '申': '未', '辰': '卯', '酉': '申'}
    r = judge_avoidance(shan='寅', xiang='申',
                        sizhu_zhi=['戌', '寅', '午', '子'],
                        tiandi_pan=tdp,
                        gan_shang_shen='丑', zhi_shang_shen='巳',
                        gan_yin_shen='子', zhi_yin_shen='辰',
                        sanchuan=['子', '亥', '戌'])
    print("案例1(寅山申向 2030-02-28子): resolved=", r['resolved'], "| need_avoid=", r['need_avoid'])
    for x in r['reasons']:
        print("   -", x)
    print()
    print("案例2(同课寅/申之临地明细):")
    for z in ['寅', '申']:
        xia = ''
        for di, tian in tdp.items():
            if tian == z:
                xia = di
                break
        wx = ZHI_WX[z]
        cs = _cs_pos(xia, wx) if xia else '?'
        print(f"   {z}({wx}) 临{xia} = {cs}")
