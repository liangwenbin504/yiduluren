#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事引擎（失物类神判法）常驻回测脚本

覆盖：
  1. 类神提取 leishen_from_text 单测（失物词 → 地支）
  2. 六畜/器物类神表自检
  3. judge_lost W1-W4 忠实古文案例回测（含 W3 相克方向修复的 7 案例）
  4. 边界（无类神/空亡/乘凶将）

用法：
    python engine/backtest_leishen_lost.py
    退出码：0=全绿，1=有失败
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'engine'))

from leishen_engine import (
    judge_lost, leishen_from_text, leishen_in_sanchuan,
    LIUCHU_LEISHEN, QIWU_LEISHEN,
)

PASS, FAIL = 0, 0


def run(name, ok, detail=''):
    """断言并计数"""
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}' + (f' | {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  ❌ {name}' + (f' | {detail}' if detail else ''))


# ══════════════════════════════════════════════
# 1. 类神提取单测
# ══════════════════════════════════════════════
def test_leishen_extract():
    print('\n【1】类神提取 leishen_from_text')
    cases = [
        ('失马', '午'), ('占失狗不见', '戌'), ('银两不见了', '酉'),
        ('午为类神', '午'), ('以酉为类神', '酉'), ('度牒以为类神', '朱雀'),
        ('丢失金环', '酉'), ('寻船', '卯'), ('失牛', '丑'), ('失鸡', '酉'),
        ('猪不见了', '亥'), ('普通文本无类神', ''),
    ]
    for text, exp in cases:
        got = leishen_from_text(text)
        run(f'提取 {text!r} → {got!r}', got == exp, f'预期 {exp!r}')


# ══════════════════════════════════════════════
# 2. 六畜/器物类神表自检
# ══════════════════════════════════════════════
def test_tables():
    print('\n【2】类神表自检')
    run('六畜表 马→午, 狗→戌', LIUCHU_LEISHEN['马'] == '午' and LIUCHU_LEISHEN['狗'] == '戌')
    run('六畜表 牛→丑, 羊→未, 鸡→酉, 猪→亥',
        LIUCHU_LEISHEN['牛'] == '丑' and LIUCHU_LEISHEN['羊'] == '未'
        and LIUCHU_LEISHEN['鸡'] == '酉' and LIUCHU_LEISHEN['猪'] == '亥')
    # 酉=麦鸡鹅金玉铜铁石块果食（原文 L1707-1718：申主金银/酉主金玉铜铁）
    run('器物表 酉含金/玉/铜', '金' in QIWU_LEISHEN['酉'] and '玉' in QIWU_LEISHEN['酉'] and '铜' in QIWU_LEISHEN['酉'])
    run('器物表 申含金银', '金' in QIWU_LEISHEN['申'] and '银' in QIWU_LEISHEN['申'])
    run('器物表 卯含舟车', '舟' in QIWU_LEISHEN['卯'] or '船' in QIWU_LEISHEN['卯'])
    run('器物表覆盖12支', set(QIWU_LEISHEN.keys()) == set('子丑寅卯辰巳午未申酉戌亥'))


# ══════════════════════════════════════════════
# 3. judge_lost W1-W4 忠实古文案例回测
# ══════════════════════════════════════════════
def test_judge_lost():
    print('\n【3】judge_lost 古文案例回测（W1-W4）')

    def _jl(leishen, sc, go, zo, kong, c_tj='', z_tj='', m_tj=''):
        return judge_lost(leishen, sc, go, zo, set(kong), c_tj, z_tj, m_tj)

    # W1: 类神入传 → 吉
    r = _jl('午', ['戌', '午', '寅'], '巳', '辰', [], '白虎', '青龙', '六合')
    run('§182 失马(午中传青龙) → 吉', r['end'] == '吉', r['narr'][:40])

    # W3: 类神被传中克类神五行之支（乘白虎）所克 → 凶
    # 【2026-09-06 修复验证】旧代码方向反，判吉；修复后 KE[WX(z)]==类神五行
    r = _jl('戌', ['申', '午', '寅'], '辰', '戌', [], '六合', '天后', '白虎')
    run('§186 失狗(寅虎末传克戌) → 凶', r['end'] == '凶', r['narr'][:40])
    r = _jl('戌', ['辰', '午', '寅'], '辰', '戌', [], '青龙', '天后', '白虎')
    run('C428 失狗(寅作虎克戌) → 凶', r['end'] == '凶', r['narr'][:40])
    # 水克火反向验证：类神午(火)被传中亥(水)乘虎克 → 凶
    r = _jl('午', ['亥', '寅', '戌'], '巳', '辰', [], '白虎', '青龙', '六合')
    run('新增 午(火)被亥(水)乘虎克 → 凶', r['end'] == '凶', r['narr'][:40])

    # W4: 类神乘白虎/玄武本身 → 凶
    r = _jl('午', ['午', '申', '寅'], '巳', '子', [], '白虎', '朱雀', '六合')
    run('§180 失马(午乘白虎) → 凶', r['end'] == '凶', r['narr'][:40])
    r = _jl('酉', ['子', '卯', '酉'], '巳', '午', [], '青龙', '六合', '白虎')
    run('§187 失鸡(酉乘虎末传) → 凶', r['end'] == '凶', r['narr'][:40])

    # W2: 类神加日辰不空 → 吉
    r = _jl('酉', ['辰', '午', '寅'], '酉', '子', [], '青龙', '天后', '白虎')
    run('§191 失婢(酉加日干) → 吉', r['end'] == '吉', r['narr'][:40])

    # 类神乘天后/太阴 → 藏匿可寻吉
    r = _jl('午', ['戌', '午', '寅'], '巳', '辰', [], '太阴', '青龙', '六合')
    run('新增 类神乘太阴 → 吉(藏匿)', r['end'] == '吉', r['narr'][:40])

    # W4: 类神不入课传 → 凶
    r = _jl('午', ['寅', '子', '戌'], '酉', '辰', [], '六合', '青龙', '白虎')
    run('[174] 失马(不入课传) → 凶', r['end'] == '凶', r['narr'][:40])

    # 类神加日辰而空亡 → 凶
    r = _jl('午', ['寅', '子', '戌'], '午', '辰', ['午', '未'], '青龙', '六合', '白虎')
    run('新增 类神加日干而空亡 → 凶', r['end'] == '凶', r['narr'][:40])


# ══════════════════════════════════════════════
# 4. 边界
# ══════════════════════════════════════════════
def test_edge():
    print('\n【4】边界')
    r = judge_lost('', ['寅', '子', '戌'], '酉', '辰', set())
    run('无类神 → None', r is None)
    r = judge_lost('午', ['寅', '子', '戌'], '酉', '辰', set())
    run('Return 含 end/narr/src 三键',
        all(k in r for k in ('end', 'narr', 'src')), str(list(r.keys())))
    # 三传不足 3（中末缺失）不应崩溃
    r = judge_lost('午', ['寅'], '酉', '辰', set(), '青龙')
    run('三传仅初传不崩溃', r is not None, r['end'])


def main():
    print('=' * 60)
    print('叙事引擎（失物类神判法）回测')
    print('=' * 60)
    test_leishen_extract()
    test_tables()
    test_judge_lost()
    test_edge()
    print('=' * 60)
    print(f'结果: 通过 {PASS} / 失败 {FAIL}')
    print('=' * 60)
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())