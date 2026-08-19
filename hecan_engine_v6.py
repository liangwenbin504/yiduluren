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
                  zhanlei, wangshuai_fn=None, yuejiang='') -> dict:
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
    yj_placeholder = yuejiang
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
    # ═══ v6 扩展信号（月破/旬首尾/丁神/驿马/进茹退茹/初传天将）═══
    # 月破 = 月将六合之冲
    from engine.liuchen_shensha import yue_jian as _yjj
    _CH = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
    _jian = _yjj(yj_placeholder)
    _po = _CH.get(_jian, '')
    sig['干上_月破'] = bool(_po and gan_shang == _po)
    sig['支上_月破'] = bool(_po and zhi_shang == _po)
    sig['初传_月破'] = bool(_po and sc and sc[0] == _po)
    # 旬首/旬尾（日干支所在旬）
    _XS = {'甲子': ('甲子','癸亥'), '甲戌': ('甲戌','癸酉'), '甲申': ('甲申','癸未'),
           '甲午': ('甲午','癸巳'), '甲辰': ('甲辰','癸卯'), '甲寅': ('甲寅','癸丑')}
    gz = ri_gan + ri_zhi
    _shou = ''
    _wei = ''
    for shou, (s, w) in _XS.items():
        _seq = '甲子乙丑丙寅丁卯戊辰己巳庚午辛未壬申癸酉甲戌乙亥丙子丁丑戊寅己卯庚辰辛巳壬午癸未甲申乙酉丙戌丁亥戊子己丑庚寅辛卯壬辰癸巳甲午乙未丙申丁酉戊戌己亥庚子辛丑壬寅癸卯甲辰乙巳丙午丁未戊申己酉庚戌辛亥壬子癸丑甲寅乙卯丙辰丁巳戊午己未庚申辛酉壬戌癸亥'
        if gz in _seq[_seq.index(shou):_seq.index(shou) + 10]:
            _shou, _wei = s, w
            break
    sig['干上_旬首'] = bool(_shou and gan_shang == _shou[-1])
    sig['支上_旬首'] = bool(_shou and zhi_shang == _shou[-1])
    sig['初传_旬尾'] = bool(_wei and sc and sc[0] == _wei[-1])
    sig['干上_旬尾'] = bool(_wei and gan_shang == _wei[-1])
    # 旬丁（旬中丁神所遁之支："辛日逢丁""水日逢丁"）
    _DING = {'甲子': '卯', '甲戌': '丑', '甲申': '亥', '甲午': '酉', '甲辰': '未', '甲寅': '巳'}
    _ding = ''
    for shou, w in _DING.items():
        _seq2 = '甲子乙丑丙寅丁卯戊辰己巳庚午辛未壬申癸酉甲戌乙亥丙子丁丑戊寅己卯庚辰辛巳壬午癸未甲申乙酉丙戌丁亥戊子己丑庚寅辛卯壬辰癸巳甲午乙未丙申丁酉戊戌己亥庚子辛丑壬寅癸卯甲辰乙巳丙午丁未戊申己酉庚戌辛亥壬子癸丑甲寅乙卯丙辰丁巳戊午己未庚申辛酉壬戌癸亥'
        if gz in _seq2[_seq2.index(shou):_seq2.index(shou) + 10]:
            _ding = w
            break
    sig['丁神_在传'] = bool(_ding and _ding in sc)
    sig['丁神_临干'] = bool(_ding and gan_shang == _ding)
    sig['丁神_临支'] = bool(_ding and zhi_shang == _ding)
    # 驿马（按日支三合）
    _MA = {'申':'寅','子':'寅','辰':'寅','寅':'申','午':'申','戌':'申','巳':'亥','酉':'亥','丑':'亥','亥':'巳','卯':'巳','未':'巳'}
    _ma = _MA.get(ri_zhi, '')
    sig['干上_驿马'] = bool(_ma and gan_shang == _ma)
    sig['初传_驿马'] = bool(_ma and sc and sc[0] == _ma)
    # 进茹/退茹（三传依次进退一位，循环序）
    _SQ = {'子':0,'丑':1,'寅':2,'卯':3,'辰':4,'巳':5,'午':6,'未':7,'申':8,'酉':9,'戌':10,'亥':11}
    _jinru = _tuiru = False
    if len(sc) >= 3 and all(sc):
        d1 = (_SQ[sc[1]] - _SQ[sc[0]]) % 12
        d2 = (_SQ[sc[2]] - _SQ[sc[1]]) % 12
        _jinru = (d1 == 1 and d2 == 1)
        _tuiru = (d1 == 11 and d2 == 11)
    sig['三传_进茹'] = _jinru
    sig['三传_退茹'] = _tuiru
    # 初传乘各天将（12 将）
    _ctj = tj[0] if tj else ''
    for _jn in ('贵人','青龙','六合','太常','天后','太阴','白虎','玄武','螣蛇','朱雀','勾陈','天空'):
        sig['初传_乘' + _jn] = _ctj == _jn
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
