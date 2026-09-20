# -*- coding: utf-8 -*-
"""第2层规则兜底回测：新物件命中 + 古籍不误伤 + 三层级顺序"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leishen_engine import leishen_from_text, leishen_rule_fallback
from leishen_engine import LOST_ITEM_LEISHEN_MODERN

PASS = FAIL = 0
def run(name, ok, detail=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}' + (f' | {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  ❌ {name}' + (f' | {detail}' if detail else ''))

print('【1】第2层规则兜底：新物件命中（静态表外的现代物件）')
fallback_cases = {
    '电饭煲丢了': '巳', '充电器不见了': '巳', '遥控器不知道放哪了': '巳',
    '银器丢了': '酉', '金链不见了': '酉', '铂金戒指丢了': '酉',
    '钻石耳钉掉了': '申',  # 钻石=申（规则首个命中，判类合理）
    '汽车不见了': '卯', '摩托车丢了': '卯', '车钥匙丢了': '丑',
    '证件包丢了': '戌', '零钱掉了': '辰', '袜子不见了': '丑',
    '衬衫丢了': '午', '毛毯不见了': '子', '铅笔掉了': '卯',
    '雨伞丢了': '亥', '水壶不见了': '子',
}
for text, exp in fallback_cases.items():
    got = leishen_from_text(text)
    run(f'兜底 {text!r} → {got!r}', got == exp, f'预期 {exp!r}')

print()
print('【2】三层级顺序：静态表优先于规则（同词 MODERN 表先命中）')
run('手机(静态表) → 巳', leishen_from_text('手机丢了') == '巳')
run('电脑(静态表) → 巳', leishen_from_text('电脑丢了') == '巳')
run('戒指(静态表) → 酉', leishen_from_text('戒指丢了') == '酉')

print()
print('【3】古籍语境不误伤（单字规则需失物语境）')
guwen_cases = {
    '占宅求安': '', '占病看吉凶': '', '占婚姻成否': '', '占前程如何': '',
    '邵公断宅': '', '占行人归期': '', '占考试中否': '',
}
for text, exp in guwen_cases.items():
    got = leishen_from_text(text)
    run(f'古籍占辞 {text!r} → {got!r}', got == exp, f'应空 {exp!r}')

print()
print('【4】失物语境才能触发单字规则')
run('丢了一支笔 → 寅', leishen_from_text('丢了一支笔') == '寅')
run('钱掉了 → 辰', leishen_from_text('钱掉了') == '辰')
run('一把伞不见了 → 亥', leishen_from_text('一把伞不见了') == '亥')

print()
print('=' * 60)
print(f'第2层规则兜底回测: 通过 {PASS} / 失败 {FAIL}')
print('=' * 60)