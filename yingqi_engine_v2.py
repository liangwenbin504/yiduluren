# -*- coding: utf-8 -*-
"""应期增强引擎 v2（2026-08-20）——疏正43案回测归纳：古籍应期主流是"干支年/干支日"，
非仅"到月"。四法补强（全部标出处，叙事层不参与评分）：
  ① 旬空填实日（精确到日）——知识库 YQ_05"空亡填实/冲合"
  ② 三传合冲日（精确到日）——知识库 YQ_03"三传合住冲日方动；三传相冲合日方住"
  ③ 太岁冲合年（精确到年）——疏正25案干支年实例（"至辛亥年十月方得身动"）
  ④ 类神速迟定性——知识库 YQ_04"类神旺相应期月内/休囚月后/死绝年外"、YQ_05"临初传速/中传中/末传迟"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_ZHI = '子丑寅卯辰巳午未申酉戌亥'
_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
          '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
_LIUHE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
          '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
_SANHE = ({'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'})
WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
      '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}


def _xunkong(rg, rz):
    """日干支 → 旬空两支。"""
    g = '甲乙丙丁戊己庚辛壬癸'.index(rg)
    z = _ZHI.index(rz)
    shou = (z - g) % 12
    return {_ZHI[(shou + 10) % 12], _ZHI[(shou + 11) % 12]}


def fa_xunkong_tianshi(rg, rz, sanchuan):
    """① 旬空填实日：旬空两支，填实（值日）或冲空（冲动）之日应。"""
    if rg not in '甲乙丙丁戊己庚辛壬癸' or rz not in _ZHI:
        return ''
    kw = _xunkong(rg, rz)
    sc = set(z for z in sanchuan if z)
    lines = []
    for k in sorted(kw):
        if k in sc:
            lines.append(f'旬空{k}入传：填实值{k}之日、冲空值{_CHONG[k]}之日为应')
        else:
            lines.append(f'旬空{k}未现：填实值{k}之日应，冲动值{_CHONG[k]}之日应')
    if not lines:
        return ''
    return '旬空填实法：' + '；'.join(lines) + '（《壬归》"空亡填实/冲合"；疏正例"果于乙卯日"即填实之应）'


def fa_sanchuan_hechong(rg, rz, sanchuan):
    """② 三传合冲日：三传成三合局→冲日支之日方动；三传含冲日支→合日支之日方住。"""
    if rz not in _ZHI or len(sanchuan) < 3:
        return ''
    sc = [z for z in sanchuan if z]
    if len(sc) < 3:
        return ''
    sc_set = set(sc)
    chong_rz = _CHONG.get(rz, '')
    if any(sc_set == s for s in _SANHE):
        return f'三传合住（{"".join(sorted(sc_set))}局）：冲{rz}（值{chong_rz}）之日方动（《壬归》"三传合住，冲日方动"）'
    if chong_rz and chong_rz in sc_set:
        return f'三传见冲{rz}（{chong_rz}）：合{rz}（值{_LIUHE.get(rz, "")}）之日方住（《壬归》"三传相冲，合日方住"）'
    return ''


def fa_taisui_chonghe(tai_sui_zhi, ben_ming_zhi='', ben_ming_age=0):
    """③ 太岁/行年冲合年：当年（太岁）应；冲太岁之年应动；行年（本命+岁数）冲合之年应。"""
    if tai_sui_zhi not in _ZHI:
        return ''
    lines = [f'太岁{tai_sui_zhi}：当年应']
    ct = _CHONG.get(tai_sui_zhi)
    if ct:
        lines.append(f'冲太岁（值{ct}）之年应动')
    if ben_ming_zhi in _ZHI:
        try:
            _age = int(ben_ming_age)
        except Exception:
            _age = 0
        if _age and _age >= 1:
            bi = _ZHI.index(ben_ming_zhi)
            xn = _ZHI[(bi + _age - 1) % 12]  # 行年：男一岁起丙寅……近似取本命顺推
            lines.append(f'行年{xn}：值{xn}年应，冲{_CHONG.get(xn, "")}之年应动')
    return '太岁行年法：' + '；'.join(lines) + '（疏正例"至辛亥年十月方得身动"——冲合填实之年）'


def fa_leishen_suchi(sanchuan, wangshuai_fn=None, yuejiang=''):
    """④ 类神速迟定性：初传旺相→速（月内）；休囚→中（月后）；死绝→迟（年外）。
    初传为事发端，其旺衰定迟速（《壬归》"类神旺相则速，休囚则迟"）。"""
    if not sanchuan or not sanchuan[0]:
        return ''
    chu = sanchuan[0]
    ws = ''
    if wangshuai_fn and WX.get(chu):
        try:
            ws = wangshuai_fn(WX[chu], yuejiang) if wangshuai_fn.__code__.co_argcount >= 2 else wangshuai_fn(WX[chu])
        except Exception:
            try:
                ws = wangshuai_fn(chu)
            except Exception:
                ws = ''
    if ws in ('旺', '相'):
        speed = '初传' + chu + '旺相：事应速，月内或近期'
    elif ws in ('死',):
        speed = '初传' + chu + '死绝：事应迟，年外或无期'
    elif ws in ('休', '囚'):
        speed = '初传' + chu + '休囚：事应中，月后'
    else:
        return ''
    return speed + '（《六壬大全·旺相休囚死》"类神旺相应期在月内；休囚月后；死绝年外"）'


def yingqi_v2(ri_gan, ri_zhi, sanchuan, tiandi_pan=None, si_ke=None, shichen='',
              tai_sui_zhi='', zhanlei='其他', zishu='', ben_ming_zhi='', ben_ming_age=0,
              wangshuai_fn=None, yuejiang='') -> str:
    """应期增强总输出：原三法（支数/月建/太岁临身）由调用方 get_yingqi_unified 提供；
    本函数追加四法块（填实日/合冲日/太岁冲合年/类神速迟）。返回追加文本。"""
    blocks = []
    t1 = fa_xunkong_tianshi(ri_gan, ri_zhi, sanchuan)
    if t1:
        blocks.append(t1)
    t2 = fa_sanchuan_hechong(ri_gan, ri_zhi, sanchuan)
    if t2:
        blocks.append(t2)
    t3 = fa_taisui_chonghe(tai_sui_zhi, ben_ming_zhi, ben_ming_age)
    if t3:
        blocks.append(t3)
    t4 = fa_leishen_suchi(sanchuan, wangshuai_fn, yuejiang)
    if t4:
        blocks.append(t4)
    return '\n'.join(blocks)


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # 自检：丙寅日午将午时（FB-002 提车课，伏吟）
    sc = ['巳', '申', '寅']
    print('① 旬空填实:', fa_xunkong_tianshi('丙', '寅', sc))
    print('② 合冲日:', fa_sanchuan_hechong('丙', '寅', sc))
    print('③ 太岁行年:', fa_taisui_chonghe('午', '甲子', 42))
    from engine.liuchen_shensha import wang_shuai
    print('④ 类神速迟:', fa_leishen_suchi(sc, wang_shuai, '午'))
