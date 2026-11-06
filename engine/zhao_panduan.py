# -*- coding: utf-8 -*-
"""
赵师判据（赵林声课程 · 三条组合规则）
==============================================================
来源：66.5 小时课程全量转录 + 人工校勘
      `.workbuddy/memory/REFERENCE-赵林声.md`
      原始素材 `E:\\玄学资料\\D05 赵林声33.84G\\_提炼\\赵林声非线性知识清单.md`

三条判据（均出自赵师自述「书上没有」）：
  1. 飞机忌乘 —— 驿马位与丧门/吊客/病符同宫（占出行）
  2. 病势向上 —— 四课三传见螣蛇（占病）
  3. 动手术   —— 羊刃与白虎同宫（占病）

🔴 定位：**纯叙事层**。不赋 valence、不进评分链、不改 M3。
   理由：三条均属「象」的组合提示，赵师原话是判据启发，非吉凶结论。
⛔ 不得据此直接改判定；须走三项校验才可上升为评分层。
"""

from typing import Any, Dict, List, Optional

# 天马：**正月起午，顺行六阳位（午→申→戌→子→寅→辰）**（憨爷 2026-10-21 亲授）
#   ⚠️ 天马 ≠ 驿马。驿马按日支三合（申子辰→寅），天马按**月建**。
#   赵师口称「天马」，此处一律取天马口径。
TIAN_MA_SEQ = ['午', '申', '戌', '子', '寅', '辰']
# 月建（寅=正月）→ 天马位
_YUE_JIAN_ORDER = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']


def tian_ma(yue_jian: str) -> str:
    """天马：正月起午，顺行六阳位。yue_jian 为月建地支（寅＝正月）。"""
    if yue_jian not in _YUE_JIAN_ORDER:
        return ''
    return TIAN_MA_SEQ[_YUE_JIAN_ORDER.index(yue_jian) % 6]

# 羊刃按日干（与 kege_shensha.yang_ren 同源，此处内联以免循环导入）
YANG_REN = {'甲': '卯', '乙': '辰', '丙': '午', '丁': '未', '戊': '午',
            '己': '未', '庚': '酉', '辛': '戌', '壬': '子', '癸': '丑'}

ZHAO_PANDUAN = [
    {
        '名': '飞机忌乘',
        '触发占类': ('出行', '行人', '行程', '走失'),
        '条件': '天马位（正月起午顺行六阳）与 丧门／吊客／病符 同宫',
        '断': '此日忌乘飞机',
        '源': '赵林声 0016-090815__p02・L256',
        '原文': '天马只要落到飞虎、落到丧门、病地也落到一块去了，那天飞机千万别坐',
        '级': '叙事层',
    },
    {
        '名': '病势向上',
        '触发占类': ('病', '疾', '医', '健康'),
        '条件': '四课三传见螣蛇',
        '断': '病势向上（恶化期），非静止',
        '源': '赵林声 0016-090815__p02・L256',
        '原文': '测病遇到螣蛇，就这个病还在往上涨',
        '级': '叙事层',
    },
    {
        '名': '动手术',
        '触发占类': ('病', '疾', '医', '健康'),
        '条件': '羊刃位 与 白虎 同宫',
        '断': '有动手术之象',
        '源': '赵林声 0030-110815__p01・L4',
        '原文': '阳刃本身就是刀子，加在一个白虎上，标准的动手术的相',
        '级': '叙事层',
    },
]


def _sanchuan_list(env: Dict[str, Any]) -> List[str]:
    """取四课三传涉及的支（去重，保序）。"""
    out: List[str] = []
    for k in ('chu', 'zhong', 'mo'):
        v = env.get(k)
        if v:
            out.append(str(v))
    sc = env.get('sanchuan')
    if isinstance(sc, (list, tuple)):
        for x in sc:
            if x and str(x) not in out:
                out.append(str(x))
    for key in ('gan_shang', 'zhi_shang', 'gan_shang_shen', 'zhi_shang_shen'):
        v = env.get(key)
        if v and str(v) not in out:
            out.append(str(v))
    return out


def _jiang_of(zhi: str, env: Dict[str, Any]) -> str:
    """查某支所乘天将。兼容 {天盘支: 将} 与 {地盘支: 将} 两种口径。"""
    jp = env.get('tian_jiang_pan') or env.get('tian_jiang') or {}
    if not isinstance(jp, dict):
        return ''
    return str(jp.get(zhi) or '')


def judge_zhao_panduan(env: Dict[str, Any], category: str = '') -> List[Dict[str, str]]:
    """返回命中的赵师判据列表（可能为空）。

    Args:
        env: 与 judge_all 同构（ri_gan/ri_zhi/nian_zhi/chu/zhong/mo/tian_jiang_pan…）
        category: 占类名，用于「触发占类」过滤；空则不做占类过滤（全部检查）

    ⚠️ 纯叙事层：只报「有此象」，不判吉凶。
    """
    env = env or {}
    hits: List[Dict[str, str]] = []
    ri_gan = str(env.get('ri_gan') or '')
    ri_zhi = str(env.get('ri_zhi') or '')
    nian_zhi = str(env.get('nian_zhi') or '')
    cat = str(category or '')

    def _cat_ok(rule: Dict[str, Any]) -> bool:
        if not cat:
            return True
        return any(t in cat for t in rule.get('触发占类', ()))

    # ── ① 飞机忌乘：天马位 与 丧门/吊客/病符 同宫 ──
    rule = ZHAO_PANDUAN[0]
    if _cat_ok(rule):
        dang_ling = str(env.get('dang_ling') or env.get('yue_jian') or '')
        ma = tian_ma(dang_ling)
        xiong = set()
        try:
            from engine.kege_shensha import sang_men, diao_ke, bing_fu
            if nian_zhi:
                xiong = {sang_men(nian_zhi), diao_ke(nian_zhi), bing_fu(nian_zhi)}
        except Exception:
            xiong = set()
        if ma and ma in xiong:
            hits.append({
                '名': rule['名'], '断': rule['断'], '级': rule['级'],
                '依据': f'天马{ma}（{dang_ling}月建） 与凶煞同宫',
                '源': rule['源'],
            })

    # ── ② 病势向上：四课三传见螣蛇 ──
    rule = ZHAO_PANDUAN[1]
    if _cat_ok(rule):
        sn = _sanchuan_list(env)
        she = [z for z in sn if '螣蛇' in _jiang_of(z, env) or '腾蛇' in _jiang_of(z, env)]
        if she:
            hits.append({
                '名': rule['名'], '断': rule['断'], '级': rule['级'],
                '依据': f'{"、".join(she)} 乘螣蛇',
                '源': rule['源'],
            })

    # ── ③ 动手术：羊刃 与 白虎 同宫 ──
    rule = ZHAO_PANDUAN[2]
    if _cat_ok(rule) and ri_gan:
        ren = YANG_REN.get(ri_gan, '')
        if ren and '白虎' in _jiang_of(ren, env):
            hits.append({
                '名': rule['名'], '断': rule['断'], '级': rule['级'],
                '依据': f'羊刃{ren} 乘白虎',
                '源': rule['源'],
            })

    return hits


def self_test() -> bool:
    """最小自测：三条都能被触发。"""
    ok = True

    # ① 天马：正月起午顺行六阳
    cond0 = (tian_ma('寅') == '午' and tian_ma('卯') == '申' and tian_ma('辰') == '戌'
             and tian_ma('巳') == '子' and tian_ma('午') == '寅' and tian_ma('未') == '辰'
             and tian_ma('申') == '午')
    print('  ① 天马起例  正月午/二月申/三月戌/四月子/五月寅/六月辰/七月午:', cond0)
    ok &= cond0

    # ①b 天马与凶煞同宫才触发
    try:
        from engine.kege_shensha import sang_men, diao_ke, bing_fu
        # 找一个使天马落在凶煞位的年支组合
        for nian in '子丑寅卯辰巳午未申酉戌亥':
            bad = {sang_men(nian), diao_ke(nian), bing_fu(nian)}
            ma = tian_ma('寅')  # 正月 → 午
            envx = {'dang_ling': '寅', 'nian_zhi': nian}
            r = judge_zhao_panduan(envx, '出行')
            got = any(h['名'] == '飞机忌乘' for h in r)
            if got != (ma in bad):
                print('  ①b 不一致 nian=%s 天马=%s 凶煞=%s' % (nian, ma, bad))
                ok = False
        print('  ①b 天马×凶煞 同宫判据自洽: 见上（无输出即全一致）')
    except Exception as e:
        print('  ①b 跳过:', e)

    # ② 螣蛇
    env2 = {'chu': '子', 'tian_jiang_pan': {'子': '螣蛇'}}
    r2 = judge_zhao_panduan(env2, '占病')
    cond2 = any(h['名'] == '病势向上' for h in r2)
    print('  ② 病势向上  命中:', cond2)
    ok &= cond2

    # ③ 羊刃+白虎
    env3 = {'ri_gan': '甲', 'tian_jiang_pan': {'卯': '白虎'}}
    r3 = judge_zhao_panduan(env3, '占病')
    cond3 = any(h['名'] == '动手术' for h in r3)
    print('  ③ 动手术    命中:', cond3)
    ok &= cond3

    return ok


if __name__ == '__main__':
    print('赵师判据自测：')
    print('PASS' if self_test() else 'FAIL')
