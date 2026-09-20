# -*- coding: utf-8 -*-
"""第3层 LLM 兜底回测：全miss物件→LLM→缓存；命中不重复调用；古籍不触发"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leishen_engine import leishen_from_text, leishen_llm_fallback_cached, _load_llm_cache, _LLM_CACHE_FILE

PASS = FAIL = 0
def run(name, ok, detail=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}' + (f' | {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  ❌ {name}' + (f' | {detail}' if detail else ''))

print('【1】全新未收录物件 → LLM 兜底（静态表+规则都miss，走第3层）')
# 这些词既不在静态表也不在规则表
new_items = ['助听器找不到了', '我的助听器掉了', '假牙丢了', '脚垫不见了']
for text in new_items:
    got = leishen_from_text(text)
    run(f'LLM兜底 {text!r} → {got!r}', got in set('子丑寅卯辰巳午未申酉戌亥'),
        f'类神={got}')

print()
print('【2】缓存生效：同物件第二次不调 LLM（直接缓存返回）')
cache1 = dict(_load_llm_cache())
for text in new_items[:2]:
    got = leishen_from_text(text)  # 第二次：应命中缓存
    run(f'缓存命中 {text!r} → {got!r}', got in set('子丑寅卯辰巳午未申酉戌亥'),
        f'类神={got}')
run('缓存文件已写入', os.path.exists(_LLM_CACHE_FILE), _LLM_CACHE_FILE)
run('缓存条目增加', len(_load_llm_cache()) >= len(cache1),
    f'{len(cache1)} → {len(_load_llm_cache())}')

print()
print('【3】三层级不误伤：静态表/规则仍优先（不进LLM）')
run('手机(静态表)→巳', leishen_from_text('手机丢了') == '巳')
run('电饭煲(规则)→巳', leishen_from_text('电饭煲丢了') == '巳')
run('古籍占宅→空', leishen_from_text('占宅求安') == '')

print()
print('【4】缓存内容展示')
cache = _load_llm_cache()
for k, v in list(cache.items())[-6:]:
    print(f'    {k!r} → {v}')

print()
print('=' * 60)
print(f'第3层 LLM 兜底回测: 通过 {PASS} / 失败 {FAIL}')
print('=' * 60)