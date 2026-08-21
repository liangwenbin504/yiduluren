# -*- coding: utf-8 -*-
"""长征第1期 · CBR 案例检索（基于古例特征向量）
================================================================
给定一课（四课三传 + 占类），按「综合特征向量」检索最相似的古例，
返回其断语（duanyu）、吉凶（label）、标注四元组，供「依样断课」参考。

数据源（合并加载）：
  - data/longmarch_feature_vectors.json  ← 218 案断案疏正（Corpus_B）
  - data/rzhy_feature_vectors.json       ← 529 案壬占汇选（Corpus_A，V2 引擎重算三传）

相似度（0-100 加权合成）：
  占类匹配        25  （同类占事才有可比性）
  课格 Jaccard    30  （64课课体结构是核心）
  毕法赋 Jaccard  15  （断法一致）
  传变匹配        10  （进茹/退茹/乱传）
  发用五行+关系   10  （发用五行 5 + 发用对日干关系 5）
  神煞吉凶接近   10  （吉神数+凶煞数距离）

查询入口：
  retrieve(query, top_k)            给定特征字典，检索 Top-K
  retrieve_by_ke(ganzhi, yuejiang, shichen, zhanlei, top_k)  起课→提特征→检索
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
VEC_FILE = os.path.join(DATA, 'longmarch_feature_vectors.json')
RZHY_VEC_FILE = os.path.join(DATA, 'rzhy_feature_vectors.json')


def _jaccard(a, b):
    a, b = set(a or []), set(b or [])
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity(q_vec, q_feat, c_vec, c_feat) -> float:
    """计算查询课与候选古例的相似度（0-100）。"""
    score = 0.0
    # 1. 占类匹配
    if q_vec.get('zhanlei') and q_vec.get('zhanlei') == c_vec.get('zhanlei'):
        score += 25.0
    # 2. 课格+变格 Jaccard（2026-08-21 修复：原无变格维度——变格是从属格，与课格同属格局语义，
    #    联合计算；索引端 features.bianjie 一直有数据但从未参与打分）
    qk = [k for k in (q_feat.get('keti') or [])] + [k for k in (q_feat.get('bianjie') or [])]
    ck = [k for k in (c_feat.get('keti') or [])] + [k for k in (c_feat.get('bianjie') or [])]
    score += 30.0 * _jaccard(qk, ck)
    # 3. 毕法赋 Jaccard
    qb = [b[0] for b in (q_feat.get('bifa') or [])]
    cb = [b[0] for b in (c_feat.get('bifa') or [])]
    score += 15.0 * _jaccard(qb, cb)
    # 4. 传变匹配
    if q_vec.get('chuan_bian') and q_vec.get('chuan_bian') == c_vec.get('chuan_bian'):
        score += 10.0
    # 5. 发用五行 + 发用对日干关系
    if q_vec.get('fayong_wuxing') and q_vec.get('fayong_wuxing') == c_vec.get('fayong_wuxing'):
        score += 5.0
    if q_vec.get('fayong_ri_gan') and q_vec.get('fayong_ri_gan') == c_vec.get('fayong_ri_gan'):
        score += 5.0
    # 6. 神煞吉凶接近（2026-08-21 修复：查询端未提供神煞计数时跳过该维度——
    #    原实现查询端恒 0，d=|0-cj|+|0-cx| 对神煞多的案例系统性扣分，负贡献）
    qj, qx = q_vec.get('ji_sha_count', 0) or 0, q_vec.get('xiong_sha_count', 0) or 0
    if qj or qx:
        cj, cx = c_vec.get('ji_sha_count', 0) or 0, c_vec.get('xiong_sha_count', 0) or 0
        d = abs(qj - cj) + abs(qx - cx)
        score += 10.0 * (1.0 - d / (d + 4.0))
    return round(score, 1)


def _load_cases():
    """合并加载断案疏正（218 案）+ 壬占汇选（529 案）特征向量。"""
    cases = []
    # 1. 断案疏正（Corpus_B）
    if os.path.exists(VEC_FILE):
        d = json.load(open(VEC_FILE, encoding='utf-8'))
        cases.extend(d.get('cases', []))
    # 2. 壬占汇选（Corpus_A）
    if os.path.exists(RZHY_VEC_FILE):
        d = json.load(open(RZHY_VEC_FILE, encoding='utf-8'))
        cases.extend(d.get('cases', []))
    return cases


def retrieve(query_vec, query_feat, cases=None, top_k=5):
    """给定查询特征（vector + features），返回 Top-K 相似古例。"""
    cases = cases if cases is not None else _load_cases()
    scored = []
    for c in cases:
        s = similarity(query_vec, query_feat, c['vector'], c['features'])
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    out = []
    for s, c in scored[:top_k]:
        ann = c.get('annotation') or {}
        out.append({
            'case_id': c['case_id'],
            'source': c.get('source', 'Corpus_B'),
            'similarity': s,
            'zhanlei': c.get('zhanlei', ''),
            'label': c.get('label', ''),
            'day_ganzhi': c.get('day_ganzhi', ''),
            'sanchuan': c.get('sanchuan', []),
            'keti': c['features'].get('keti', []),
            'chuan_bian': c['vector'].get('chuan_bian', ''),
            'duanyu': c.get('duanyu', '')[:400],
            'leishen': ann.get('leishen', []),
            'liqi': ann.get('liqi', []),
            'yingqi': ann.get('yingqi', []),
        })
    return out


def build_query_features(ri_gan, ri_zhi, yuejiang, shichen, sanchuan, sike, tian_jiang, tiandi_pan, zhanlei):
    """复用 build_feature_vectors 的 8 类特征 + 扁平向量（神煞/演禽省略，检索不依赖）。"""
    from engine.feature_extractor import extract_features
    from engine.ganzhi_date import find_solar
    from datetime import date
    f = extract_features(ri_gan, ri_zhi, '', '', yuejiang, shichen, sanchuan, sike,
                         tian_jiang, tiandi_pan, zhanlei, sec='',
                         y=2026, m=1, d=1,
                         sanchuan_tianjiang=[tian_jiang.get(x, '') for x in sanchuan])
    from engine.knowledge_features import relation, WX
    vec = {}
    vec['zhanlei'] = zhanlei
    vec['ri_gan'] = ri_gan
    vec['ri_zhi'] = ri_zhi
    chu = sanchuan[0] if sanchuan else ''
    vec['fayong'] = chu
    vec['fayong_wuxing'] = WX.get(chu, '')
    if chu and ri_gan:
        vec['fayong_ri_gan'] = relation(chu, ri_gan)['relation']
    if chu and ri_zhi:
        vec['fayong_ri_zhi'] = relation(chu, ri_zhi)['relation']
    if len(sanchuan) >= 3:
        order = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
        try:
            idx = [order.index(x) for x in sanchuan[:3]]
            if idx[0]+1 == idx[1] and idx[1]+1 == idx[2]:
                vec['chuan_bian'] = '进茹'
            elif idx[0]-1 == idx[1] and idx[1]-1 == idx[2]:
                vec['chuan_bian'] = '退茹'
            else:
                vec['chuan_bian'] = '乱传'
        except Exception:
            vec['chuan_bian'] = ''
        vec['chu_ke_zhong'] = relation(sanchuan[0], sanchuan[1])['relation']
        vec['zhong_ke_mo'] = relation(sanchuan[1], sanchuan[2])['relation']
    # 神煞计数用 0（检索不依赖神煞，但保留字段一致）
    vec['ji_sha_count'] = 0
    vec['xiong_sha_count'] = 0
    vec['shensha_hit_count'] = 0
    feat = {
        'keti': [k['课体'] for k in f.get('keti', [])],
        'bifa': [(d['法句'], d.get('分类', '')) for d in f.get('bifa', {}).get('断法', [])],
        'special': f.get('special', {}).get('匹配课格', []),
        'bianjie': f.get('bianjie', {}).get('匹配变格', []),
    }
    return vec, feat


def retrieve_by_ke(day_ganzhi, yuejiang, shichen, zhanlei='', top_k=5, cases=None):
    """起一课 → 提特征 → 检索 Top-K 相似古例。
    P1（2026-08-17）：起课统一到权威 V2 引擎 SiKeSanChuanCalculator2
    （原 DaLiuRenEngine.fa_san_chuan 在反吟/涉害/遥克/伏吟等场景三传有误）。"""
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    eng = SiKeSanChuanCalculator2()
    gc = GuiRenCalculator()
    ri_gan, ri_zhi = day_ganzhi[0], day_ganzhi[1]
    tdp = eng.get_tiandi_pan(yuejiang, shichen)
    sike_tuples = eng.qi_sike(ri_gan, ri_zhi, tdp)
    sike = [[t[0], t[1], t[2]] for t in sike_tuples]
    sc_dict = eng.fa_sanchuan(sike_tuples, ri_gan, ri_zhi, tdp)
    sc = [sc_dict.get('初传', ''), sc_dict.get('中传', ''), sc_dict.get('末传', '')]
    tj = gc.arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shichen)
    tjm = tj['天将映射']
    vec, feat = build_query_features(ri_gan, ri_zhi, yuejiang, shichen, sc, sike, tjm, tdp, zhanlei)
    return {
        'query': {'day_ganzhi': day_ganzhi, 'yuejiang': yuejiang, 'shichen': shichen,
                  'zhanlei': zhanlei, 'sanchuan': sc, 'keti': feat['keti'],
                  'chuan_bian': vec.get('chuan_bian', '')},
        'matches': retrieve(vec, feat, cases=cases, top_k=top_k),
    }


if __name__ == '__main__':
    # 自检：加载量 + 检索一课
    cases = _load_cases()
    print(f'CBR index: {len(cases)} cases')
    # 来源统计
    src_count = {}
    for c in cases:
        s = c.get('source', 'Corpus_B')
        src_count[s] = src_count.get(s, 0) + 1
    print(f'  Sources: {src_count}')

    r = retrieve_by_ke('己卯', '子', '申', zhanlei='其他', top_k=5)
    print(f'\nQuery: {r["query"]}')
    print('Top相似古例:')
    for m in r['matches']:
        src_tag = '[疏正]' if m['source'] == 'Corpus_B' else '[汇选]'
        print(f"  {m['similarity']:>5}分  {src_tag} {m['case_id']}  [{m['zhanlei']}/{m['label']}] "
              f"三传{''.join(m['sanchuan'])} 课格{m['keti'][:3]}")
