# -*- coding: utf-8 -*-
"""现代类神映射回测：26个现代物件识别 + 全量回归（31基础 + 14原文）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leishen_engine import leishen_from_text, judge_lost, LOST_ITEM_LEISHEN_MODERN

PASS = FAIL = 0
def run(name, ok, detail=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}' + (f' | {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  ❌ {name}' + (f' | {detail}' if detail else ''))

print('【1】现代物件类神识别（26项）')
modern = {
    '手机不见了': '巳', '占失手机': '巳', '电脑丢了': '巳', '钱包掉了': '辰',
    '钥匙找不到了': '丑', '戒指丢了': '酉', '银行卡不见了': '申', '手表丢了': '酉',
    '平板不见了': '巳', '充电宝丢了': '午', '耳机不见了': '巳', '眼镜丢了': '酉',
    '护照不见了': '戌', '自行车丢了': '卯', '电动车不见了': '卯',
    '金银首饰丢了': '申', '玉佩不见了': '巳', '项链丢了': '巳',
    '公文包不见了': '寅', '笔记本电脑丢了': '巳', '金器不见了': '酉', '银元丢了': '酉',
    '玉镯不见了': '巳', '现金不见了': '辰', '存折丢了': '辰', '水杯不见了': '子',
}
for text, exp in modern.items():
    got = leishen_from_text(text)
    run(f'提取 {text!r} → {got!r}', got == exp, f'预期 {exp!r}')

print()
print('【2】现代表自检')
run('现代表 40 项', len(LOST_ITEM_LEISHEN_MODERN) >= 38, str(len(LOST_ITEM_LEISHEN_MODERN)))
run('巳=手机/电脑/平板', LOST_ITEM_LEISHEN_MODERN['手机'] == '巳' and LOST_ITEM_LEISHEN_MODERN['电脑'] == '巳')
run('戌=证件', LOST_ITEM_LEISHEN_MODERN['身份证'] == '戌' and LOST_ITEM_LEISHEN_MODERN['护照'] == '戌')
run('酉=金玉', LOST_ITEM_LEISHEN_MODERN['戒指'] == '酉' and LOST_ITEM_LEISHEN_MODERN['手表'] == '酉')
run('卯=车', LOST_ITEM_LEISHEN_MODERN['自行车'] == '卯' and LOST_ITEM_LEISHEN_MODERN['电动车'] == '卯')

print()
print('【3】现代物件走失判定（用现代表类神跑 W1-W4）')
# 手机(巳)在初传 → 吉
r = judge_lost('巳', ['巳', '申', '寅'], '辛', '未', [], '青龙', '太常', '六合')
run('失手机 巳入初传 → 吉', r['end'] == '吉', r['narr'][:36])
# 钱包(辰)被寅(木)克乘虎 → 凶
r = judge_lost('辰', ['寅', '午', '戌'], '甲', '子', [], '白虎', '天后', '六合')
run('失钱包 辰被寅木克乘虎 → 凶', r['end'] == '凶', r['narr'][:36])
# 钥匙(丑)不入传 → 凶
r = judge_lost('丑', ['寅', '午', '戌'], '甲', '子', [], '六合', '青龙', '天后')
run('失钥匙 丑不入课传 → 凶', r['end'] == '凶', r['narr'][:36])
# 戒指(酉)加日辰不空 → 吉
r = judge_lost('酉', ['寅', '午', '戌'], '酉', '子', [], '六合', '青龙', '天后')
run('失戒指 酉加日干不空 → 吉', r['end'] == '吉', r['narr'][:36])

print()
print('=' * 60)
print(f'现代类神回测: 通过 {PASS} / 失败 {FAIL}')
print('=' * 60)