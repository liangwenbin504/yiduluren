# -*- coding: utf-8 -*-
"""
engine/sike_explain.py — 四课三传「分步解说」层（教学用 · 零侵入）

【干什么】
把权威起课引擎 SiKeSanChuanCalculator2 的内部中间态录下来，转成面向学习者的
六步解说：定月将 → 叠天地盘 → 起四课 → 判克贼 → 定取用 → 发三传。

【为什么不改引擎】
🔴 引擎是 M3 基线（89.9%）的载体，任何改动都有回归风险。
   本模块**一行都不改 sike_sanchuan_engine.py**，只在外层按 fa_sanchuan()
   的同一顺序重走一遍并记录中间量 —— 纯「旁路观测」。

【防漂移】
旁路观测最大的风险是「解说逻辑与引擎逻辑各写一套，日久漂移」。
   故 explain() 末尾强制自检：
     · 本层算出的 method 必须 == 引擎 _decide_method 的返回值
     · 本层三传必须 == calc.calculate() 的三传
   任一不符即在返回体的 _drift 字段中报警，绝不静默。

【口径铁律（沿用项目 MEMORY）】
· 「临 X」＝X 位上的天盘支（tiandi_pan 是 {地盘支: 天盘支}）
· 「乘」＝将所骑的天盘支；第 4 步判克一律「上神为地支、第一课下神为日干本气」
· 七级取用优先级见 _decide_method docstring（伏吟→贼克→八专→遥克→反吟→别责→昴星）
"""

from __future__ import annotations

from typing import Dict, List, Tuple

try:
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
except ImportError:                                    # 直接跑 engine/ 内脚本时
    from sike_sanchuan_engine import SiKeSanChuanCalculator2


_CALC_CACHE = None


def _calc() -> SiKeSanChuanCalculator2:
    """单例引擎（内部带天地盘/四课缓存，复用更快）。"""
    global _CALC_CACHE
    if _CALC_CACHE is None:
        _CALC_CACHE = SiKeSanChuanCalculator2()
    return _CALC_CACHE


# ── 原文出处（教学时挂在每一步末尾） ───────────────────────────────
_SRC = {
    'yuejiang': '月将＝太阳所躔之次，中气过宫；非月建。',
    'pan': '月将加于占时之宫，其余十二支顺布。《通解》上卷起例。',
    'sike': '第一课取日干寄宫之上神，第二课取第一课上神之上神；'
            '第三课取日支之上神，第四课取第三课上神之上神。',
    'ke': '四课上下相克：上克下曰「克」，下贼上曰「贼」。'
          '第一课下神为日干，判克用日干本气（218 古例实证 205/207）。',
    'quyong': '宗门九课取用次序：伏吟→贼克→八专→遥克→反吟→别责→昴星。'
              '《六壬大全》八专门：「无上下克不取遥克，径用八专法」。',
    'sanchuan': '初传发用既定，中传取初传所临宫之上神，末传取中传所临宫之上神。',
}


def _wx_of_zhi(c, zhi: str) -> str:
    return c.DIZHI_WU_XING.get(zhi, '')


def _wx_of_gan(c, gan: str) -> str:
    return c.TIAN_GAN_WU_XING.get(gan, '')


def _ke_relation(c, shang: str, xia: str) -> str:
    """五行关系人话表述（仅供展示，判定仍以引擎 is_ke 为准）。"""
    s, x = _wx_of_zhi(c, shang), None
    if xia in c.TIAN_GAN_WU_XING:
        x = _wx_of_gan(c, xia)
    else:
        x = _wx_of_zhi(c, xia)
    if not s or not x:
        return ''
    if c.WU_XING_KE.get(s) == x:
        return f'{s}克{x}'
    if c.WU_XING_KE.get(x) == s:
        return f'{x}克{s}'
    if s == x:
        return f'{s}同{x}'
    if c.WU_XING_SHENG.get(s) == x:
        return f'{s}生{x}'
    if c.WU_XING_SHENG.get(x) == s:
        return f'{x}生{s}'
    return f'{s}·{x}'


def _judge_path(c, info: Dict) -> List[Dict]:
    """按 _decide_method 的**同一优先级顺序**逐条复核，记录「触发 / 未触发 + 理由」。

    ⚠️ 这是解说层自己走一遍，仅用于展示判定路径；
       最终 method 以引擎 _decide_method 返回值为准，并在 explain() 中比对。
    """
    path: List[Dict] = []

    def mark(name: str, hit: bool, reason: str) -> bool:
        path.append({'rule': name, 'hit': hit, 'reason': reason})
        return hit

    # 1 伏吟
    if mark('伏吟法', info['is_fu_yin'],
            '月将加占时，天地盘十二宫全同' if info['is_fu_yin']
            else '天地盘错位，非伏吟'):
        return path

    # 2 贼克
    kr = info['ke_results']
    if kr:
        desc = '、'.join(f"第{n}课{k}（{s}上{x}下）" for n, k, s, x in kr)
        mark('贼克法', True, f'四课有克贼：{desc}')
        return path
    mark('贼克法', False, '四课上下神无一相克')

    # 2.5 八专（无克径用，不参与遥克）
    if mark('八专法', info['is_ba_zhuan'],
            '干支同位（八专日），无克贼 ⇒ 径用八专，不再取遥克' if info['is_ba_zhuan']
            else '干支不同位，非八专日'):
        return path

    # 3 遥克
    yk = info['yao_ke_results']
    if yk:
        desc = '、'.join(f"第{n}课{k}（{s}）" for n, k, s, x in yk)
        mark('遥克法', True, f'无克贼，四课上神与日干相克：{desc}')
        return path
    mark('遥克法', False, '四课上神与日干亦不相克')

    # 4 反吟
    if mark('反吟法', info['is_fan_yin'],
            '天地盘十二宫全冲（反吟），且无克贼无遥克' if info['is_fan_yin']
            else '天地盘非全冲，非反吟'):
        return path

    # 5 别责
    if mark('别责法', info['is_bie_ze'],
            '四课不全（有重复课），且无克贼无遥克' if info['is_bie_ze']
            else '四课齐备，非别责'):
        return path

    # 6 八专（兜底，实际不会到）
    if mark('八专法（兜底）', False, '上方已判过，此处不触发'):
        return path

    mark('昴星法', True, '无克贼、无遥克、非伏吟反吟别责 ⇒ 昴星取用')
    return path


def _zeike_path(c, info: Dict) -> List[Dict]:
    """贼克法「宗门内细分」——四层展开，教学上最关键的一段。

    引擎口径（sike_sanchuan_engine._execute_zei_ke）：
      1. 贼（下贼上）优先于克（上克下）
      2. 候选计数定课体：单个贼→重审课、单个克→元首课、两个以上→知一课
      3. 比用：阳日取阳支上神，阴日取阴支上神
      4. 比用后仍多候选 → 涉害法（课体改由涉害定：见机／察微／缀瑕）
    """
    kr = info['ke_results']
    zei = [(n, s, x) for n, k, s, x in kr if k == '贼']
    ke = [(n, s, x) for n, k, s, x in kr if k == '克']
    yang = info['yang_ri']
    out: List[Dict] = []

    def mark(rule: str, hit: bool, reason: str) -> None:
        out.append({'rule': rule, 'hit': hit, 'reason': reason})

    def fmt(lst):
        return '、'.join(f'第{n}课{s}上{x}下' for n, s, x in lst)

    if zei:
        mark('① 贼优先于克', True, f'有贼 {len(zei)} 处（{fmt(zei)}），有贼则不取克')
        cand, hint = zei, '重审课' if len(zei) == 1 else '知一课'
    else:
        mark('① 贼优先于克', False, '四课无贼，径取上克下')
        cand, hint = ke, '元首课' if len(ke) == 1 else '知一课'

    mark('② 候选计数定课体', True,
         f'候选 {len(cand)} 个 ⇒ {hint}'
         + ('（单贼）' if len(zei) == 1 else '（单克）' if not zei and len(ke) == 1
            else '（两个以上，须比用，故名「知一」）'))

    if len(cand) > 1:
        by = [t for t in cand
              if (yang and c.is_yang_zhi(t[1])) or ((not yang) and not c.is_yang_zhi(t[1]))]
        mark('③ 比用', bool(by),
             f'{"阳" if yang else "阴"}日取{"阳" if yang else "阴"}支上神，'
             f'命中 {len(by)}/{len(cand)} 个候选'
             + ('' if by else '（无一相合，仍以全部候选入涉害）'))
        use = by or cand
    else:
        use = cand

    if len(use) == 1:
        mark('④ 定初传', True, f'候选唯一「{use[0][1]}」⇒ 初传')
    else:
        mark('④ 涉害法', True,
             f'比用后仍余 {len(use)} 个候选，转涉害取深者；课体改由涉害定（见机／察微／缀瑕）')
    return out


def explain(ri_gan: str, ri_zhi: str, yue_jiang: str, shi_chen: str) -> Dict:
    """完整六步解说。

    参数：日干 / 日支 / 月将 / 占时（均为单字地支或天干）
    返回：{input, steps[6], pan, sike, sanchuan, method, keti, _drift}
    """
    c = _calc()
    ji_gong = c.TIAN_GAN_JI_GONG.get(ri_gan, '')
    steps: List[Dict] = []

    # ── 第 1 步：定月将与占时 ──────────────────────────────
    steps.append({
        'id': 1,
        'title': '定月将与占时',
        'lines': [
            f'日柱：{ri_gan}{ri_zhi}',
            f'月将：{yue_jiang}（太阳所躔之次，按中气过宫）',
            f'占时：{shi_chen}时',
        ],
        'src': _SRC['yuejiang'],
    })

    # ── 第 2 步：叠天地盘 ─────────────────────────────────
    tdp = c.get_tiandi_pan(yue_jiang, shi_chen)
    if not tdp:
        return {'error': f'非法月将或占时：{yue_jiang}/{shi_chen}', '_drift': []}

    shi_i = c.DIZHI_INDEX[shi_chen]
    jiang_i = c.DIZHI_INDEX[yue_jiang]
    steps.append({
        'id': 2,
        'title': '叠天地盘',
        'lines': [
            f'月将「{yue_jiang}」加于占时「{shi_chen}」之宫 —— 即地盘{shi_chen}位上得天盘{yue_jiang}',
            '其余十一宫按月将顺布（天盘随地盘顺行）',
            f'公式：地盘第 i 位之上神 = 月将({jiang_i}) + (i − 占时({shi_i})) mod 12',
        ],
        'pan': tdp,
        'src': _SRC['pan'],
    })

    # ── 第 3 步：起四课 ───────────────────────────────────
    sike = c.qi_sike(ri_gan, ri_zhi, tdp)
    gan_shang = tdp.get(ji_gong, '')
    zhi_shang = tdp.get(ri_zhi, '')
    steps.append({
        'id': 3,
        'title': '起四课',
        'lines': [
            f'{ri_gan}寄宫在「{ji_gong}」，该宫上神「{gan_shang}」⇒ 第一课 {gan_shang}/{ri_gan}（干阳）',
            f'第一课上神「{gan_shang}」之上神「{tdp.get(gan_shang, "")}」⇒ 第二课（干阴）',
            f'日支「{ri_zhi}」之上神「{zhi_shang}」⇒ 第三课（支阳）',
            f'第三课上神「{zhi_shang}」之上神「{tdp.get(zhi_shang, "")}」⇒ 第四课（支阴）',
        ],
        'sike': [{'ke': n, 'shang': s, 'xia': x} for n, s, x, _ in sike],
        'src': _SRC['sike'],
    })

    # ── 第 4 步：判克贼 ───────────────────────────────────
    info = c._collect_info(sike, ri_gan, ri_zhi, tdp)
    ke_rows = []
    for i, (name, shang, xia, _) in enumerate(sike):
        rel = _ke_relation(c, shang, xia)
        verdict = c.is_ke(shang, xia, ri_gan)
        ke_rows.append({
            'ke': name,
            'shang': shang, 'xia': xia,
            'rel': rel,
            'verdict': verdict or '无克',
            'note': '第一课下神为日干，以本气论' if i == 0 else '',
        })
    n_ke = sum(1 for r in ke_rows if r['verdict'] == '克')
    n_zei = sum(1 for r in ke_rows if r['verdict'] == '贼')
    steps.append({
        'id': 4,
        'title': '判克贼',
        'lines': [
            f'逐课比对上下神五行：克 {n_ke} 处、贼 {n_zei} 处',
            '口诀：上克下为「克」，下贼上为「贼」；两者俱有则取「比用」',
        ],
        'rows': ke_rows,
        'src': _SRC['ke'],
    })

    # ── 第 5 步：定取用 ───────────────────────────────────
    method = c._decide_method(info)
    path = _judge_path(c, info)
    detail = _zeike_path(c, info) if method == '贼克法' else []
    steps.append({
        'id': 5,
        'title': '定取用',
        'lines': [f'依宗门九课次序逐条判定 ⇒ 命中「{method}」'],
        'path': path,
        'detail': detail,
        'method': method,
        'src': _SRC['quyong'],
    })

    # ── 第 6 步：发三传 ───────────────────────────────────
    result = c._execute_method(method, info, tdp)
    result = c._enrich_ke_ge(result, ri_gan, ri_zhi, tdp, sike, shi_chen)
    if info['is_fan_yin'] and method != '反吟法':
        cur = result.get('课体', '')
        if '反吟' not in cur:
            result['课体'] = f'反吟{cur}' if cur else '反吟课'

    chu, zhong, mo = (result.get('初传', ''), result.get('中传', ''), result.get('末传', ''))
    steps.append({
        'id': 6,
        'title': '发三传',
        'lines': [
            f'初传「{chu}」⇒ 其临宫之上神「{tdp.get(chu, "")}」为中传',
            f'中传「{zhong}」⇒ 其临宫之上神「{tdp.get(zhong, "")}」为末传',
            f'起法：{result.get("起法", method)}｜课体：{result.get("课体", "")}',
        ],
        'sanchuan': {'初传': chu, '中传': zhong, '末传': mo},
        'qifa': result.get('起法', method),
        'keti': result.get('课体', ''),
        'src': _SRC['sanchuan'],
    })

    # ── 防漂移自检 ────────────────────────────────────────
    drift: List[str] = []
    try:
        ref = c.calculate(ri_gan, ri_zhi, yue_jiang, shi_chen)
        ref_sc = ref.get('sanchuan', {})
        if [ref_sc.get('初传'), ref_sc.get('中传'), ref_sc.get('末传')] != [chu, zhong, mo]:
            drift.append(f'三传与 calculate() 不一致：{ref_sc} vs {(chu, zhong, mo)}')
        if path and path[-1]['rule'].replace('（兜底）', '') not in method:
            drift.append(f'判定路径末条「{path[-1]["rule"]}」与 method「{method}」不符')
        # 贼克法细分：解说层推的课体提示须与引擎实际课体一致（反吟前缀除外）
        if method == '贼克法' and detail:
            hint = ''
            for d in detail:
                if d['rule'].startswith('②'):
                    hint = d['reason'].split('⇒')[1].split('（')[0].strip()
            actual = result.get('课体', '')
            if hint and hint not in actual and '涉害' not in d['rule']:
                drift.append(f'贼克法课体提示「{hint}」与引擎「{actual}」不符')
    except Exception as e:                              # noqa: BLE001
        drift.append(f'自检异常：{e}')

    return {
        'input': {'ri_gan': ri_gan, 'ri_zhi': ri_zhi,
                  'yue_jiang': yue_jiang, 'shi_chen': shi_chen,
                  'ji_gong': ji_gong},
        'steps': steps,
        'pan': tdp,
        'sike': [{'ke': n, 'shang': s, 'xia': x} for n, s, x, _ in sike],
        'sanchuan': {'初传': chu, '中传': zhong, '末传': mo},
        'method': method,
        'qifa': result.get('起法', method),
        'keti': result.get('课体', ''),
        '_drift': drift,
    }


if __name__ == '__main__':
    import json
    import sys
    a = sys.argv[1:] or ['己', '卯', '寅', '酉']
    print(json.dumps(explain(*a), ensure_ascii=False, indent=1))
