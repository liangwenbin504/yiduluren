# -*- coding: utf-8 -*-
"""毕法赋 100 法回归测试

【用法】PYTHONHASHSEED=0 python engine/test_bifa_100.py
【数据】data/bifa_lowfreq_cases.json（低频法的真实正例，由 _probe_bifa_lowfreq.py 枚举 8640 课搜得）
【目的】把「低频法」从"从未被执行验证"状态纳入回归 —— 防"知一课式"静默失效
"""
import ast
import io
import json
import os
import sys

sys.path.insert(0, '.')
sys.path.insert(0, 'engine')

PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append((name, detail))
    print('  %s %s%s' % ('✅' if cond else '❌', name,
                         ('  [' + detail + ']') if detail and not cond else ''))


def detect_for(g, z, yj, shi, bmz=''):
    """跑一课，返回命中的毕法赋法号集合（bmz = 本命支）"""
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    from engine.bifa_detector import BiFaDetector
    calc = SiKeSanChuanCalculator2()
    gr = GuiRenCalculator()
    det = BiFaDetector()
    r = calc.calculate(g, z, yj, shi)
    s = r['sanchuan']
    tp = r['tiandi_pan']
    gj = gr.arrange_gui_ren_pan(g, {'天地对应': tp}, shi)
    tj = {t['地支']: t['天将'] for t in (gj.get('天将列表') or [])}
    sc = [s.get('初传'), s.get('中传'), s.get('末传')]
    det.detect(sanchuan_dizhi=sc, ri_gan=g, ri_zhi=z, ganzhi=g + z, yuejiang=yj,
               gan_shang_shen=r['sike'][0][1], zhi_shang_shen=r['sike'][2][1],
               si_ke_info=[(x[0], x[1], x[2]) for x in r['sike']],
               tian_jiang=tj, tiandi_pan=tp, keti=s.get('课体', ''), shichen=shi,
               ben_ming_zhi=bmz)
    return {int(h['id']) for h in (det.detected_rules or []) if h.get('id')}


def main():
    print('=' * 92)
    print('毕法赋 100 法回归测试')
    print('=' * 92)

    kb = json.load(io.open('data/bifa_100_knowledge_base.json', encoding='utf-8'))
    M = {r['id']: r for r in kb['rules']}

    # ── A. 低频法正例（来自枚举搜索结果）──
    p = 'data/bifa_lowfreq_cases.json'
    if not os.path.exists(p):
        print('⚠️ 缺少 %s（先运行 _probe_bifa_lowfreq.py）' % p)
        return 1
    low = json.load(io.open(p, encoding='utf-8'))

    print('\n【A. 低频法正例（%d 法）】' % len(low))
    for n_str, f in sorted(low.items(), key=lambda x: int(x[0])):
        n = int(n_str)
        name = (M.get(n) or {}).get('name', '')
        if not f:
            check('第%d法 %s（8640 课内未触发）' % (n, name), False,
                  '未找到正例 —— 需人工确认条件是否可实现')
            continue
        gz, yj, shi = f['ganzhi'], f['月将'], f['时辰']
        bmz = f.get('本命', '')
        ids = detect_for(gz[0], gz[1], yj, shi, bmz)
        check('第%d法 %s（%s日 月将%s %s时%s）'
              % (n, name, gz, yj, shi, (' 本命' + bmz) if bmz else ''),
              n in ids, '实得法号 %s' % sorted(ids)[:12])

    # ── B. 高频法抽查（用枚举搜得的正例，覆盖"常见课不崩"）──
    print('\n【B. 高频法正例抽查】')
    for n, gz, yj, shi, bmz in [(94, '甲子', '子', '丑', ''), (96, '乙丑', '丑', '丑', ''),
                                (1, '甲子', '子', '丑', '')]:
        name = (M.get(n) or {}).get('name', '')
        ids = detect_for(gz[0], gz[1], yj, shi, bmz)
        check('第%d法 %s（%s日 月将%s %s时）' % (n, name, gz, yj, shi), n in ids,
              '实得法号 %s' % sorted(ids)[:12])

    # ── C. 谓词重复定义守卫（2026-09-21 事故：_bi_nan_tao_sheng 新旧两版同名，
    #      后定义静默覆盖先定义 ⇒ 第9法整法 0 命中，且 judge 的 except 吞异常不报错）──
    print('\n【C. kege_atoms 同名谓词重复定义守卫】')
    _src = io.open(os.path.join('engine', 'kege_atoms.py'), encoding='utf-8').read()
    _names = [n.name for n in ast.parse(_src).body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    _dup = sorted({x for x in _names if _names.count(x) > 1})
    check('kege_atoms 无同名函数重复定义（%d 个函数）' % len(_names), not _dup,
          '重复：%s —— 后者静默覆盖前者' % _dup)

    print()
    print('=' * 92)
    print('结果：通过 %d ｜ 失败 %d' % (len(PASS), len(FAIL)))
    for n, d in FAIL:
        print('   ✗ %s  %s' % (n, d))
    print('=' * 92)
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
