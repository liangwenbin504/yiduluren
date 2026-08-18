# -*- coding: utf-8 -*-
"""全古籍库统一回测工具（2026-08-18）
三库合计 479 案：疏正集 218 + 壬占汇选 183 + 大六壬指南 78
用法：python _memory/_ab_all.py  → 输出各库吉凶符合率
任何引擎修改后都应跑本工具确认无回归。"""
import json, sys, io, os
sys.path.insert(0, r'E:\仪度六壬择日\yiduluren')
os.chdir(r'E:\仪度六壬择日\yiduluren')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.zhanshi_duanyu import generate

def is_ji(lv):
    return lv and '吉' in str(lv) and '凶' not in str(lv)
def is_xiong(lv):
    return lv and '凶' in str(lv)

def run_case(rg, rz, yj, shi, zl, label, tag):
    try:
        lv = generate(rg, rz, yj, shi, zhanshi=zl).get('level', '平')
    except Exception:
        lv = 'ERR'
    return {'tag': tag, 'label': label, 'lv': lv}

def main():
    all_rows = []
    # 1. 疏正集 218
    c1 = json.load(open(r'E:\仪度六壬择日\yiduluren\engine\shuzheng_real_cases.json', encoding='utf-8'))
    for c in c1:
        gz = c.get('day_ganzhi', '')
        if len(gz) < 2:
            continue
        all_rows.append(run_case(gz[0], gz[1],
                                 str(c.get('yue_jiang', '') or '').replace('将', ''),
                                 str(c.get('shichen', '') or ''),
                                 c.get('zhanlei', '其他'), c.get('label', ''), '疏正'))
    # 2. 壬占汇选 183
    c2 = json.load(open(r'E:\仪度六壬择日\yiduluren\extracted_data\_guji_fetch\壬占汇选_案例_labeled.json', encoding='utf-8'))
    for c in c2:
        gz = str(c.get('ganzhi', ''))
        if len(gz) < 2:
            continue
        q = str(c.get('question', ''))
        zl = '其他'
        for k, v in [('行', '出行'), ('功名', '功名'), ('官', '官讼'), ('病', '疾病'),
                     ('财', '求财'), ('宅', '家宅'), ('产', '胎产'), ('婚', '婚姻'), ('贼', '贼盗')]:
            if k in q:
                zl = v
                break
        all_rows.append(run_case(gz[0], gz[1],
                                 str(c.get('yuejiang', '') or '').replace('将', ''),
                                 str(c.get('shichen', '') or ''),
                                 zl, c.get('label', ''), '壬占汇选'))
    # 3. 大六壬指南 78
    c3 = json.load(open(r'E:\仪度六壬择日\yiduluren\engine\ancient_truth_labels_zhinan_v3.json', encoding='utf-8'))['cases']
    for c in c3:
        all_rows.append(run_case(str(c.get('ri_gan', '')), str(c.get('ri_zhi', '')),
                                 str(c.get('yue_jiang', '') or '').replace('将', ''),
                                 str(c.get('shichen', '') or ''),
                                 c.get('category', '其他'), c.get('label', ''), '大六壬指南'))

    print(f'全量案例: {len(all_rows)} 案')
    for tag in ('疏正', '壬占汇选', '大六壬指南'):
        sub = [r for r in all_rows if r['tag'] == tag]
        xo = sum(1 for r in sub if is_xiong(r['lv']) and r['label'] == '凶')
        jo = sum(1 for r in sub if is_ji(r['lv']) and r['label'] == '吉')
        po = sum(1 for r in sub if r['label'] == '平' and r['lv'] == '平')
        tx = sum(1 for r in sub if r['label'] == '凶')
        tj = sum(1 for r in sub if r['label'] == '吉')
        tp = sum(1 for r in sub if r['label'] == '平')
        err = sum(1 for r in sub if r['lv'] == 'ERR')
        acc = (xo + jo + po) / max(1, len(sub) - err)
        print(f'  {tag}: {len(sub)}案(凶{tx}吉{tj}平{tp}) ERR={err} 判凶{xo}/{tx} 判吉{jo}/{tj} 平{po}/{tp} 符合率={acc:.3f}')
    xo = sum(1 for r in all_rows if is_xiong(r['lv']) and r['label'] == '凶')
    jo = sum(1 for r in all_rows if is_ji(r['lv']) and r['label'] == '吉')
    po = sum(1 for r in all_rows if r['label'] == '平' and r['lv'] == '平')
    err = sum(1 for r in all_rows if r['lv'] == 'ERR')
    acc = (xo + jo + po) / max(1, len(all_rows) - err)
    print(f'总体: {len(all_rows)}案 ERR={err} 判凶{xo} 判吉{jo} 平{po} 总符合率={acc:.3f}')
    return acc

if __name__ == '__main__':
    main()
