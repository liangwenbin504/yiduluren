# -*- coding: utf-8 -*-
"""叙事引擎端到端汇总演示：四类物件 × 真实起课全链路

覆盖：
  A. 古籍原文案例（六畜/古器物 → 原文表类神）
  B. 现代静态表物件（OX Alpha 生成）
  C. 现代规则兜底物件（物性关键词）
  D. 现代 LLM 兜底物件（三层级漏网 + 审核）
链路：paipan_v2 起课 → 四课/三传/课体 → 类神定位 → judge_lost_modern(W1-W4) → 方位断语
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leishen_engine import judge_lost_modern, leishen_from_text
from zhanshi_duanyu_patched11 import paipan_v2

print('=' * 76)
print('  叙事引擎 · 端到端汇总演示（四类物件 × 真实起课全链路）')
print('=' * 76)

# ── 课例：标题/占辞/日干支/月将/时辰/三传(覆盖起课)/天将(初三末) ──
# A类古籍用原文真实排盘（三传取自《断案疏正》原文），B/C/D类现代用自定义起课
CASES = [
    # A. 古籍原文（三传=原文排盘，天将=原文乘将）
    ('A1 古籍 · 失马(§180王寺丞)', '占失马，午为马乘虎加亥为用', '乙', '巳', '亥', '卯',
     ['午', '丑', '子'], '白虎', '朱雀', ''),
    ('A2 古籍 · 失羊(§185)', '占失羊，未为羊加卯作青龙为用', '甲', '申', '辰', '午',
     ['未', '申', '酉'], '青龙', '天空', '太常'),
    # B. 现代静态表（自定义起课）
    ('B1 现代 · 失手机', '手机不见了', '辛', '巳', '亥', '申',
     None, '青龙', '太常', '六合'),
    ('B2 现代 · 失戒指', '婚戒戒指丢了', '丁', '卯', '戌', '巳',
     None, '六合', '青龙', '天后'),
    # C. 现代规则兜底
    ('C1 现代 · 失电饭煲', '电饭煲丢了', '丙', '辰', '子', '申',
     None, '青龙', '太常', '六合'),
    ('C2 现代 · 失雨伞', '雨伞忘了拿', '壬', '寅', '午', '戌',
     None, '六合', '青龙', '天后'),
    # D. 现代 LLM 兜底
    ('D1 现代 · 失助听器', '助听器找不到了', '庚', '午', '申', '卯',
     None, '青龙', '太常', '六合'),
    ('D2 现代 · 失假牙', '假牙丢了', '癸', '酉', '巳', '午',
     None, '六合', '青龙', '天后'),
]

# 类神来源标注
from leishen_engine import LOST_ITEM_LEISHEN_MODERN, MODERN_RULE_FALLBACK, LOST_ITEM_LEISHEN, LIUCHU_LEISHEN


def source_tag(text):
    t = str(text)
    for item in LOST_ITEM_LEISHEN_MODERN:
        if item in t:
            return '静态表'
    for kw, _z, _d in MODERN_RULE_FALLBACK:
        if kw in t:
            return '规则兜底'
    for item in LOST_ITEM_LEISHEN:
        if item in t:
            return '原文表'
    if any(f'{a}' in t for a in LIUCHU_LEISHEN):
        return '六畜表'
    return '？（LLM兜底）'


for title, item, rg, rz, yj, sc_zhi, fixed_sc, c1, c2, c3 in CASES:
    print()
    print('─' * 76)
    print(f'■ {title}')
    print(f'  占辞：{item}')

    pp = paipan_v2(rg, rz, yj, sc_zhi)
    if fixed_sc:
        sanchuan = list(fixed_sc)  # 古籍原文排盘（三传忠实原文）
        sc_note = f'{"→".join(sanchuan)}（原文排盘）'
    else:
        sanchuan = pp.get('sanchuan', [])
        sc_note = '→'.join(sanchuan) or '(起课失败)'
    print(f'  起课：{rg}{rz}日 {yj}将 {sc_zhi}时')
    print(f'        三传：{sc_note} | 课体：{pp.get("keti","")}（演示参考）')

    ls = leishen_from_text(item)
    tag = source_tag(item)
    print(f'  类神：{item} → {ls or "(未识别)"}  [{tag}]')

    r = judge_lost_modern(item, sanchuan, rg, rz, [], c1, c2, c3, pp.get('sike', []))
    if r:
        mark = {'吉': '✅吉', '凶': '❌凶', '平': '⚪平'}.get(r['end'], r['end'])
        print(f'  判定：【{mark}】')
        print(f'    断语：{r["narr"]}')
        src = r['src']
        if 'MODERN' in src:
            print(f'    溯源：{src.split("MODERN")[0].strip()} | [MODERN 现代补充]')
        else:
            print(f'    溯源：{src}')
    else:
        print('  判定：无法判定（无类神）')

print()
print('=' * 76)
print('链路：paipan_v2 起课 → 四课/三传/课体 → 类神定位(三层级) → judge_lost_modern W1-W4 → 方位断语')
print('=' * 76)