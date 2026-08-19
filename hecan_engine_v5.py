# -*- coding: utf-8 -*-
"""多条件合参引擎（2026-08-18）

方法论：叶飘然课例回测教训——正议结论均为"多条件合参"（如"幕贵+当旺+生日+占谋望"
四条件齐备才断必成），单抽条件必然过拟合误伤。

架构三层：
  L1 硬规则层（liuchen_engine 现有）：单/双条件规则，已过 632 全库验证——保持不动；
  L2 合参规则层（本引擎）：断语原文的"条件集合→结论"，**必须全条件命中才触发**，
     输出置信度与出处，接入叙事层（不参与评分，零回退风险）；
  L3 规则候选库（data/hecan_rules.json）：正议体提取的候选规则+验证状态，
     全中方向一致率达标（≥80% 且样本≥3）才升入 L2。

推广价值：任何古断语（邵公/陈公献/王牧夫/叶飘然/祝泌…）都可按
"断语→条件集合→结论"结构化入库，逐步把"象法活断"沉淀为"可验证合参"。
"""
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_rules(path: str = '') -> list:
    p = path or os.path.join(_ROOT, 'data', 'hecan_rules_v2.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('rules', []) if isinstance(d, dict) else d
    except Exception:
        return []


def check_signals(sig: dict, pan_signals: dict) -> bool:
    """单信号判定。pan_signals 由课程信号提取函数构造。"""
    s = str(sig.get('signal', ''))
    val = sig.get('value', True)
    neg = bool(sig.get('neg', False))
    got = pan_signals.get(s, False)
    hit = bool(got) == bool(val)
    return (not hit) if neg else hit


def hecan_judge(pan_signals: dict, rules: list = None) -> list:
    """合参判定：逐条规则算条件命中数，全中才触发。返回触发规则列表（含置信度）。"""
    rs = rules if rules is not None else load_rules()
    out = []
    for r in rs:
        conds = r.get('条件', [])
        if not conds:
            continue
        hit = sum(1 for c in conds if check_signals(c, pan_signals))
        if hit == len(conds):
            out.append({
                'id': r.get('id', ''), '结论': r.get('结论', ''),
                '置信度': round(r.get('置信度', 1.0) * hit / len(conds), 2),
                '出处': r.get('出处', ''), '叙事': r.get('叙事', ''),
            })
    return out


if __name__ == '__main__':
    rs = load_rules()
    print(f'合参规则库: {len(rs)} 条')
    # 自检：构造 §070 信号
    sig = {'干上_是贵人': True, '干上_空亡': True, '干上_生日干': True}
    out = hecan_judge(sig, rs)
    for o in out:
        print('触发:', o['id'], o['结论'], '|', o['叙事'][:40])

# ══════════════════════════════════════════════════════════════
# 课程信号构造器（合参规则的输入层，全部可计算）
# ══════════════════════════════════════════════════════════════
WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
      '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
GUI = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'},
       '戊': {'丑', '未'}, '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'},
       '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
GAN_MU = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
          '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}


def build_signals(ri_gan, ri_zhi, sanchuan, tianjiang_list, kong, sike, keti,
                  zhanlei, wangshuai_fn=None) -> dict:
    """构造合参信号字典。wangshuai_fn(zhi)->旺/相/休/囚/死（可传 wang_shuai 包装）。"""
    sig = {}
    gan_shang = ''
    zhi_shang = ''
    for i, k in enumerate(sike or []):
        us = str(k[1]) if isinstance(k, (list, tuple)) and len(k) >= 2 else str(k.get('上神', '')) if isinstance(k, dict) else ''
        if i == 0:
            gan_shang = us
        if i == 2:
            zhi_shang = us
    gan_tj = str(tianjiang_list[0]) if gan_shang in sanchuan and tianjiang_list else ''
    sc = list(sanchuan or [])
    tj = list(tianjiang_list or [])
    mo_tj = tj[2] if len(tj) > 2 else ''
    kw = set(kong or [])
    gwx = GAN_WX.get(ri_gan, '')
    gswx = WX.get(gan_shang, '')
    sig['干上_是贵人'] = gan_shang in GUI.get(ri_gan, set())
    sig['干上_空亡'] = gan_shang in kw
    sig['干上_生日干'] = bool(gswx and SHENG.get(gswx) == gwx)
    sig['干上_克日干'] = bool(gswx and KE.get(gswx) == gwx)
    sig['干上_官星'] = sig['干上_克日干']
    sig['干上_日墓'] = gan_shang == GAN_MU.get(ri_gan, '')
    sig['干上_乘白虎'] = (gan_shang == sc[0] if sc else False) and (tj[0] == '白虎' if tj else False)
    sig['干上_乘青龙'] = (gan_shang == sc[0] if sc else False) and (tj[0] == '青龙' if tj else False)
    if wangshuai_fn and gan_shang:
        sig['干上_旺相'] = wangshuai_fn(gan_shang) in ('旺', '相')
    else:
        sig['干上_旺相'] = False
    sig['末传_乘白虎'] = mo_tj == '白虎'
    sig['占类_疾病'] = zhanlei in ('疾病',)
    sig['占类_功名'] = zhanlei in ('功名', '前程')
    sig['占类_征战'] = zhanlei in ('征战',)
    sig['占类_谋望或求财'] = zhanlei in ('求财', '其他')
    sig['课体_伏吟'] = '伏吟' in str(keti or '')
    sig['课体_返吟'] = ('返吟' in str(keti or '')) or ('反吟' in str(keti or ''))
    sig['课体_八专'] = '八专' in str(keti or '')
    # 支上神
    sig['支上_生日干'] = bool(zhi_shang and SHENG.get(WX.get(zhi_shang, '')) == gwx)
    sig['支上_克日干'] = bool(zhi_shang and KE.get(WX.get(zhi_shang, '')) == gwx)
    # 干支相刑/相害（干支上神）
    _ZI_XING = {'辰', '午', '酉', '亥'}
    _LIU_HAI = {'子': '未', '未': '子', '丑': '午', '午': '丑', '寅': '巳', '巳': '寅',
                '卯': '辰', '辰': '卯', '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'}
    sig['干支上_自刑'] = bool(gan_shang in _ZI_XING and zhi_shang in _ZI_XING)
    sig['干支上_相害'] = bool(gan_shang and zhi_shang and _LIU_HAI.get(gan_shang) == zhi_shang)
    # 三合局
    _SANHE = [{'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'}]
    _sc_set = {z for z in sc if z}
    sig['三传_三合局'] = any(_sc_set == s for s in _SANHE)
    # 传位信号
    sig['初传_官鬼'] = bool(sc and KE.get(WX.get(sc[0], '')) == gwx)
    sig['中传_空亡'] = len(sc) > 1 and sc[1] in kw
    sig['末传_空亡'] = len(sc) > 2 and sc[2] in kw
    sig['末传_生日干'] = len(sc) > 2 and bool(SHENG.get(WX.get(sc[2], '')) == gwx)
    return sig


if __name__ == '__main__':
    rs = load_rules()
    print(f'合参规则库: {len(rs)} 条')
    # 自检 H003（§070 乙卯日）：干上子=乙贵空亡生乙木
    sig = build_signals('乙', '卯', ['未', '卯', '亥'], ['虎', '合', '后'], {'子'}, [], '', '功名')
    sig['干上_是贵人'] = True
    sig['干上_空亡'] = True
    sig['干上_生日干'] = True
    out = hecan_judge(sig, rs)
    for o in out:
        print('触发:', o['id'], o['结论'], '|', o['叙事'][:44])
