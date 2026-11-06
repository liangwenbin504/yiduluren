# -*- coding: utf-8 -*-
"""
毕法赋判断引擎 v1.0（纯六壬断法版，2026-08-15 憨爷：判断课体为毕法赋哪一句）
================================================================
输入：课式（三传/日干日支/月将/四课/天将/天地盘）
输出：命中的毕法赋法句 + 断法依据（core_rule/应用/示例），纯六壬断法，不混股市信号。

数据源：
  - data/bifa_100_knowledge_base.json（毕法赋100法，宋·凌福之，六壬大全·毕法赋四库全书本）
  - engine/bifa_detector.py（100法检测规则，复用其检测逻辑）
  - 通解《六壬毕法赋》歌诀 + 上下卷注解（校对用，data/_tongjie_ocr/通解_中.txt 3795行起）
"""
import os, sys, json
from typing import List, Dict, Any

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

_KB_PATH = os.path.join(BASE, 'data', 'bifa_100_knowledge_base.json')
_KB = None


def _load_kb():
    global _KB
    if _KB is None:
        try:
            _KB = json.load(open(_KB_PATH, encoding='utf-8'))
        except Exception:
            _KB = {'rules': []}
    return _KB


def _rule_by_name(name: str) -> Dict:
    kb = _load_kb()
    for r in kb.get('rules', []):
        if r.get('name') == name:
            return r
    return {}


def judge_bifa(sanchuan_dizhi: List[str], ri_gan: str = '', ri_zhi: str = '',
               ganzhi: str = '', yuejiang: str = '', season: str = '',
               gan_shang_shen: str = '', zhi_shang_shen: str = '',
               si_ke_info: List = None, tian_jiang: Dict = None,
               tiandi_pan: Dict = None, keti: str = '', tai_sui: str = '',
               ben_ming_zhi: str = '', shichen: str = '',
               is_day=None) -> Dict:
    """判断课体对应毕法赋 100 法的哪一句（纯六壬断法）。

    返回 {
        '匹配法句': [法句名...],
        '断法': [{法句, 断法依据(core_rule), 应用, 示例, 分类}...],
    }
    """
    try:
        from engine.bifa_detector import BiFaDetector
    except Exception:
        from bifa_detector import BiFaDetector

    det = BiFaDetector()
    raw = det.detect(
        sanchuan_dizhi=sanchuan_dizhi, ri_gan=ri_gan, ri_zhi=ri_zhi,
        ganzhi=ganzhi, yuejiang=yuejiang, season=season,
        gan_shang_shen=gan_shang_shen, zhi_shang_shen=zhi_shang_shen,
        si_ke_info=si_ke_info, tian_jiang=tian_jiang, tiandi_pan=tiandi_pan,
        keti=keti, tai_sui=tai_sui, ben_ming_zhi=ben_ming_zhi, shichen=shichen,
        is_day=is_day,   # 🔴 2026-10-22：昼夜按**太阳出入**（见 judge_orchestrator._judge_is_day）
    )

    matched = raw.get('匹配法条', []) or []
    duanfa = []
    for name in matched:
        kb = _rule_by_name(name)
        # 检测规则（detect 的 法条详情.规则）优先，知识库 core_rule 兜底
        detail = raw.get('法条详情', {}).get(name, {})
        rule = detail.get('规则', '') or kb.get('core_rule', '')
        duanfa.append({
            '法句': name,
            '断法依据': rule,
            '应用': kb.get('application', ''),
            '示例': kb.get('example', ''),
            '分类': kb.get('category', ''),
        })
    return {'匹配法句': matched, '断法': duanfa}


def cmd_bifa(sanchuan: str, ri_gan: str = '', ri_zhi: str = ''):
    """命令行：判断三传对应毕法赋哪一句"""
    sc = list(sanchuan)
    r = judge_bifa(sc, ri_gan, ri_zhi, ganzhi=ri_gan + ri_zhi if ri_gan and ri_zhi else '')
    print(f"三传 {sanchuan}（{ri_gan}{ri_zhi}日）命中的毕法赋法句：")
    if not r['匹配法句']:
        print('  无')
    for d in r['断法']:
        faju = d['法句']
        fenlei = d['分类']
        yiju = d['断法依据']
        print(f"  【{faju}】（{fenlei}）")
        print(f"    断法依据：{yiju}")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='毕法赋判断引擎')
    ap.add_argument('sanchuan', help='三传地支，如 申亥寅')
    ap.add_argument('--gan', default='', help='日干')
    ap.add_argument('--zhi', default='', help='日支')
    a = ap.parse_args()
    cmd_bifa(a.sanchuan, a.gan, a.zhi)
