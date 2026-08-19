# -*- coding: utf-8 -*-
"""择日合参桥（2026-08-19）：把 hecan_engine_v8 多条件合参迁移到择日模块。
定位：择日候选的「古籍合参警示/佐证层」——不参与择日评分（评分口径为斗首/仪度/
禄马贵/演禽分层体系，合参只做提示）。
用法：任何择日调用方（stock_dashboard._build_zeri_candidate 等）：
    from zeri_hecan_bridge import zeri_hecan_eval
    hecan = zeri_hecan_eval(ri_gan, ri_zhi, sike, sanchuan, tianjiang_map, keti, yuejiang, zetiri_type)
接入点（主服务文件解锁后贴入 stock_dashboard.py `_build_zeri_candidate` ②b 之后）：
    try:
        from zeri_hecan_bridge import zeri_hecan_eval
        _hecan = zeri_hecan_eval(ri_gan, ri_zhi, _sike4, _sc3, _tjm, _keti, _yj, zetiri_type)
    except Exception:
        _hecan = {'hits': [], 'narr': '', '警告': []}
    并在 return dict 加 'hecan': _hecan。
"""
import io
import sys

from hecan_engine_v8 import hecan_judge, build_signals
from engine.liuchen_shensha import wang_shuai
from engine.bifa_detector import get_xun_kong

_WXH = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}


def zeri_zhanlei(zetiri_type: str) -> str:
    """择日类型 → 合参占类键（开业/交易→求财、上任→功名；安葬/动土/出行无对应键归'其他'）。"""
    t = str(zetiri_type or '')
    if any(k in t for k in ('任', '官', '职', '仕', '升迁', '赴任')):
        return '功名'
    if any(k in t for k in ('开', '财', '交易', '生意', '求财')):
        return '求财'
    return '其他'


def zeri_hecan_eval(ri_gan: str, ri_zhi: str, sike, sanchuan, tianjiang_map: dict,
                    keti: str, yuejiang: str, zetiri_type: str = '') -> dict:
    """择日单课合参评估。sanchuan 可为 dict({'初传'..}) 或 list；返回
    {'hits': [{id,结论,叙事,出处}...], 'narr': 拼接判语, '警告': 凶规则判语列表, '佐证': 吉规则判语列表}。"""
    try:
        sc = ([sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
              if isinstance(sanchuan, dict) else list(sanchuan or []))
        tjm = tianjiang_map or {}
        tj = [tjm.get(z, '') for z in sc]
        kw = set(get_xun_kong(str(ri_gan) + str(ri_zhi)))
        zl = zeri_zhanlei(zetiri_type)
        sig = build_signals(ri_gan, ri_zhi, sc, tj, kw, sike, str(keti or ''), zl,
                            lambda z: wang_shuai(_WXH.get(z, ''), yuejiang),
                            yuejiang=yuejiang, tianjiang_map=tjm)
        hc = hecan_judge(sig)
        hits = [{'id': o['id'], '结论': o['结论'], '叙事': o['叙事'], '出处': o['出处']} for o in hc[:2]]
        narr = '；'.join("合参[%s]：%s（%s）" % (o['id'], o['叙事'], o['出处']) for o in hc[:2])
        return {
            'hits': hits,
            'narr': narr,
            '警告': ["合参[%s]：%s" % (o['id'], o['叙事']) for o in hc[:2] if o['结论'] == '凶'],
            '佐证': ["合参[%s]：%s" % (o['id'], o['叙事']) for o in hc[:2] if o['结论'] == '吉'],
        }
    except Exception:
        return {'hits': [], 'narr': '', '警告': [], '佐证': []}


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # 自检：择日样例（戊申日酉将巳时，开业）——叶池首案同课式
    from engine.sike_sanchuan_engine_patched import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    calc = SiKeSanChuanCalculator2()
    tdp = calc.get_tiandi_pan('酉', '巳')
    sike = calc.qi_sike('戊', '申', tdp)
    scd = calc.fa_sanchuan(sike, '戊', '申', tdp)
    tjm = GuiRenCalculator().arrange_gui_ren_pan('戊', {'天地对应': tdp}, '巳').get('天将映射', {})
    sc3 = {'初传': scd.get('初传', ''), '中传': scd.get('中传', ''), '末传': scd.get('末传', '')}
    r = zeri_hecan_eval('戊', '申', sike, sc3, tjm, scd.get('课体', ''), '酉', '开业')
    print('课体:', scd.get('课体', ''), '三传:', sc3)
    print('占类映射:', zeri_zhanlei('开业'))
    print('合参:', r['narr'] or '（无规则触发）')
    # 再验功名映射触发 N004 的可能
    print('上任映射:', zeri_zhanlei('上任赴任'))
