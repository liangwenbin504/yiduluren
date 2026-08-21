# -*- coding: utf-8 -*-
"""壬占汇选（Corpus_A）特征向量构建器
================================================================
从 engine/ancient_truth_labels.json 读取 Corpus_A 的 704 案壬占汇选案例，
筛选有完整起课数据的案例（ri_gan+ri_zhi+yue_jiang+shichen），
用 V2 引擎重算四课三传+天将，提取 10 类引擎特征 + 扁平向量，
输出到 data/rzhy_feature_vectors.json，供 CBR 检索合并使用。

设计原则：
  - 与 build_feature_vectors.py（218 案断案疏正）保持同一口径
  - V2 引擎重算三传，保证格式一致（地支-only, 3 元素）
  - 任何一类失败降级为空，不拖垮全量
  - Corpus_A 无 year/month，神煞/演禽降级处理
"""
import json, sys, os, re
sys.path.insert(0, '.')

from engine.feature_extractor import extract_features
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
from engine.gui_ren_engine import GuiRenCalculator
from engine.ganzhi_date import find_solar
from datetime import date
from engine.build_feature_vectors import build_flat_vector, build_shensha, build_yanqin, ZHI

# ── 路径 ──
BASE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(BASE, 'engine')
DATA = os.path.join(BASE, 'data')
SRC_FILE = os.path.join(ENGINE, 'ancient_truth_labels.json')
OUT_FILE = os.path.join(DATA, 'rzhy_feature_vectors.json')

DIZHI = set('子丑寅卯辰巳午未申酉戌亥')


def _normalize_yj(yj_raw):
    """月将格式归一化：'子将'→'子'"""
    if not yj_raw:
        return ''
    return yj_raw.rstrip('将')


def _normalize_shi(shi_raw):
    """时辰格式归一化：'申时'→'申'"""
    if not shi_raw:
        return ''
    return shi_raw.rstrip('时')


def _extract_dizhi_from_ganzhi(val):
    """从干支字符串提取地支：'壬申'→'申', '申'→'申'"""
    if not val or not isinstance(val, str):
        return ''
    if len(val) == 1 and val in DIZHI:
        return val
    if len(val) >= 2 and val[-1] in DIZHI:
        return val[-1]
    return ''


def main():
    # 1. 加载 Corpus_A 案例
    with open(SRC_FILE, 'r', encoding='utf-8') as f:
        d = json.load(f)
    all_cases = [c for c in d['cases'] if c.get('source') == 'Corpus_A']
    print(f"Corpus_A total: {len(all_cases)}")

    # 2. 筛选有完整起课数据的案例
    valid = []
    for c in all_cases:
        rg = c.get('ri_gan', '')
        rz = c.get('ri_zhi', '')
        yj = _normalize_yj(c.get('yue_jiang', ''))
        shi = _normalize_shi(c.get('shichen', ''))
        if rg and rz and yj and shi and yj in DIZHI and shi in DIZHI:
            valid.append(c)
    print(f"Valid (complete起课 data): {len(valid)}")

    # 3. V2 引擎初始化
    eng = SiKeSanChuanCalculator2()
    gc = GuiRenCalculator()

    out = []
    n_ok = 0
    n_fail = 0
    errors = []

    for i, c in enumerate(valid):
        cid = c.get('id', f'RZHY-{i}')
        rg = c.get('ri_gan', '')
        rz = c.get('ri_zhi', '')
        yj = _normalize_yj(c.get('yue_jiang', ''))
        shi = _normalize_shi(c.get('shichen', ''))
        gz = rg + rz
        zhanlei = c.get('category', c.get('zhanlei', '其他'))
        label = c.get('label', '')
        interpretation = c.get('interpretation', '')

        try:
            # V2 引擎：天地盘 + 四课 + 三传 + 天将
            tdp = eng.get_tiandi_pan(yj, shi)
            sike_tuples = eng.qi_sike(rg, rz, tdp)
            sike = [[t[0], t[1], t[2]] for t in sike_tuples]
            sc_dict = eng.fa_sanchuan(sike_tuples, rg, rz, tdp)
            sc = [sc_dict.get('初传', ''), sc_dict.get('中传', ''), sc_dict.get('末传', '')]
            # 过滤空值
            sc = [x for x in sc if x]

            if len(sc) < 3:
                # V2 引擎未能推出完整三传，尝试用存储的三传
                stored_sc = c.get('sanchuan', [])
                sc = [_extract_dizhi_from_ganzhi(x) for x in stored_sc] if stored_sc else []
                sc = [x for x in sc if x]
                if len(sc) < 3:
                    n_fail += 1
                    errors.append(f"{cid}: sanchuan insufficient (len={len(sc)})")
                    continue

            tj = gc.arrange_gui_ren_pan(rg, {'天地对应': tdp}, shi)
            tjm = tj['天将映射']

            # 无 year/month，用默认值
            sd = date(2026, 1, 1)

            # 8 类引擎特征
            f = extract_features(rg, rz, '', '', yj, shi, sc, sike,
                                 tjm, tdp, zhanlei, sec='',
                                 y=sd.year, m=sd.month, d=sd.day,
                                 sanchuan_tianjiang=[tjm.get(x, '') for x in sc])

            # 神煞（无年月，降级）
            shensha = build_shensha(rg, rz, 1, '', sc, sike)

            # 演禽（降级）
            yanqin = build_yanqin('', 0, rz, shi)

            # 扁平向量
            vec = build_flat_vector(rg, rz, sc, sike, f, shensha, zhanlei)

            rec = {
                'case_id': cid,
                'source': 'Corpus_A',
                'name': c.get('name', ''),
                'question': c.get('question', ''),
                'zhanlei': zhanlei,
                'label': label,
                'day_ganzhi': gz,
                'yue_jiang': yj,
                'shichen': shi,
                'sanchuan': sc,
                'sike': sike,
                'duanyu': interpretation,
                'features': {
                    'keti': [k['课体'] for k in f.get('keti', [])],
                    'bifa': [(dd['法句'], dd.get('分类', '')) for dd in f.get('bifa', {}).get('断法', [])],
                    'special': f.get('special', {}).get('匹配课格', []),
                    'bianjie': f.get('bianjie', {}).get('匹配变格', []),
                    'yingqi': f.get('yingqi', ''),
                    'shensha': shensha,
                    'leixiang': f.get('leixiang', []),
                    'tianjiang': {k: v for k, v in (tjm or {}).items()},
                    'duanan': f.get('duanan', {}),
                    'yanqin': yanqin,
                },
                'annotation': {
                    'leishen': c.get('leishen', []),
                    'liqi': c.get('liqi', []),
                    'yingqi': [c.get('yingqi', '')] if c.get('yingqi') else [],
                },
                'vector': vec,
            }
            out.append(rec)
            n_ok += 1

        except Exception as e:
            n_fail += 1
            errors.append(f"{cid}: {type(e).__name__}: {str(e)[:80]}")

        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(valid)}, ok={n_ok}, fail={n_fail}")

    # 4. 输出
    result = {
        'meta': {
            'source': 'ancient_truth_labels.json Corpus_A (壬占汇选)',
            'total': n_ok,
            'failed': n_fail,
            'schema': '基础字段 + 10类引擎特征 + 标注四元组 + 扁平向量 (与 longmarch_feature_vectors.json 同口径)',
            'engine': 'SiKeSanChuanCalculator2 (V2 引擎重算三传)',
        },
        'cases': out,
    }
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    sz = os.path.getsize(OUT_FILE)
    print(f"\nDone: {n_ok} cases → {OUT_FILE}")
    print(f"Failed: {n_fail}")
    print(f"File size: {sz/1024:.1f} KB")
    if errors:
        print(f"Errors (first 5):")
        for e in errors[:5]:
            print(f"  {e}")


if __name__ == '__main__':
    main()
