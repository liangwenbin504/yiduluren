# -*- coding: utf-8 -*-
"""LLM 兜底增强回测：物性审核 + 方位联动 + 缓存结构 + 三层级回归"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import leishen_engine as LE
from leishen_engine import (_audit_llm_zhi, leishen_from_text, leishen_llm_fallback_cached,
                            get_llm_direction, _ZHI_DEFAULT_DIRECTION)

PASS = FAIL = 0
def run(name, ok, detail=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}' + (f' | {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  ❌ {name}' + (f' | {detail}' if detail else ''))

print('【1】物性五行审核（单元）')
# 金类物件：酉/申(金) 通过；辰/戌(土) 拦截
run('金饰→酉 通过', _audit_llm_zhi('金链丢了', '酉'))
run('金链→戌(土) 拦截', not _audit_llm_zhi('金链丢了', '戌'))
run('银器→申 通过', _audit_llm_zhi('银器丢了', '申'))
run('手机→巳(火) 通过', _audit_llm_zhi('手机掉了', '巳'))
run('手机→酉(金) 拦截', not _audit_llm_zhi('手机掉了', '酉'))
run('雨伞→亥(水) 通过', _audit_llm_zhi('雨伞丢了', '亥'))
run('无物性线索→信任', _audit_llm_zhi('稀奇古怪的东西丢了', '卯'))

print()
print('【2】LLM 兜底+审核+方位联动（全新未收录物件）')
new_items = ['助听器找不到了', '假牙丢了', '脚垫不见了', '香炉不见了']
for text in new_items:
    zhi = leishen_from_text(text)
    ok_zhi = zhi in LE._ZHI_SET
    direction = get_llm_direction(text)
    run(f'LLM兜底 {text!r} → 类神{zhi!r} + 方位{direction!r}',
        ok_zhi and bool(direction),
        f'类神={zhi} 方位={direction}')

print()
print('【3】缓存结构升级为 {zhi, direction}')
cache = LE._load_llm_cache()
struct_ok = all(isinstance(v, dict) and v.get('zhi') for v in cache.values())
run('缓存全部为结构化条目', struct_ok, str(list(cache.items())[-3:]))

print()
print('【4】三层级回归（静态/规则仍优先，不进LLM）')
run('手机(静态表)→巳', leishen_from_text('手机丢了') == '巳')
run('电饭煲(规则)→巳', leishen_from_text('电饭煲丢了') == '巳')
run('古籍占宅→空', leishen_from_text('占宅求安') == '')

print()
print('【5】方位断语端到端（judge_lost_modern → LLM 方位）')
from leishen_engine import judge_lost_modern
r = judge_lost_modern('助听器找不到了', ['巳', '申', '寅'], '辛', '巳', [], '青龙', '太常', '六合')
print(f'  失助听器: [{r["end"]}] {r["narr"]}  (src含LLM兜底: {"LLM兜底" in r["src"]})')
run('端到端方位已联动', '可寻方位/场所' in r['narr'] and 'LLM兜底' in r['src'], r['narr'][-50:])

print()
print('=' * 60)
print(f'LLM兜底增强回测: 通过 {PASS} / 失败 {FAIL}')
print('=' * 60)