# -*- coding: utf-8 -*-
"""长征第1期 · 第二期综合向量分析：特征向量构建器
================================================================
为 218 案每案构建「综合特征向量」：
  ● 基础字段：case_id / 干支 / 三传 / 四课 / 占类 / 章节 / label / 本命 / 年
  ● 10 类引擎特征（feature_extractor 8类 + 神煞 + 演禽）
      - 课经(64课) / 毕法赋(100法) / 特殊课格 / 变格 / 应期 / 类象 / 天将 / 断案知识
      - 神煞(ShenShaCalculator)  ← 新增
      - 演禽(YanQinAnalyzer)     ← 新增（实验性，择日向）
  ● 标注四元组（断语判据）：leishen/liqi/leixiang/yingqi + engine_hits
  ● 扁平向量（供 CBR/训练消费）

设计原则：
  - feature_extractor 调用保持与 _annotate 脚本一致（nian_zhi=""），不改动已有 engine_hits 口径；
  - 神煞/演禽单独计算，用 longmarch 已同步的 year/month 字段补足太岁/月建/四柱。
  - 任何一类失败降级为空，不拖垮全量。
"""
import json, sys, os
sys.path.insert(0, '.')
from engine.feature_extractor import extract_features
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
from engine.gui_ren_engine import GuiRenCalculator
from engine.ganzhi_date import find_solar
from datetime import date

MONTH_ZHI = {1: '寅', 2: '卯', 3: '辰', 4: '巳', 5: '午', 6: '未',
             7: '申', 8: '酉', 9: '戌', 10: '亥', 11: '子', 12: '丑'}

# 神煞吉凶分类（shen_sha_calculator 返回 key，按《通解》吉凶归类）
JI_SHEN = {'日禄', '日德', '天乙贵人', '天乙贵人 2', '驿马', '日马', '日贵', '天德', '月德',
           '天喜', '天医', '天赦', '长生学堂', '贤贵', '进神', '日解', '日医', '五合', '支德',
           '华盖', '驾前太阳', '驾前太阴', '驾前龙德', '驾前天德',
           '马前将星', '马前攀鞍', '四季天喜', '四季天赦', '四季皇书', '四季天城',
           '六仪', '句奇', '响动', '四季天吏', '四季天车'}
XIONG_SHA = {'羊刃', '劫煞', '灾煞', '桃花', '天罗', '地网', '孤辰', '寡宿', '丧门', '吊客',
             '病符', '岁破', '月破', '月厌', '四废', '退神', '日刑', '日破', '日害', '直符',
             '游都', '鲁都', '六破', '三刑', '破碎', '雷电', '雨师',
             '驾前太岁', '驾前官符', '驾前死符', '驾前岁破', '驾前白虎', '驾前吊客', '驾前病符',
             '马前六厄', '马前劫杀', '马前灾杀', '马前天杀', '马前岁杀', '马前月杀', '马前地杀',
             '马前亡神', '四季转煞', '四季奸神', '四季四废', '四季丧车煞', '四季火鬼',
             '四季飞祸', '四季关神', '四季天盗', '闭口', '五亡神', '四季浴盆'}

ZHI = set('子丑寅卯辰巳午未申酉戌亥')


def build_shensha(ri_gan, ri_zhi, lunar_month, nian_zhi, sanchuan, sike):
    """神煞特征：位置 + 命中（神煞地支是否临课传）。"""
    from engine.shen_sha_calculator import ShenShaCalculator
    sc = ShenShaCalculator()
    ri_gan_zhi = ri_gan + ri_zhi
    try:
        all_sha = sc.calculate_all_shen_sha(ri_gan, ri_zhi, lunar_month or 1, nian_zhi or '子', ri_gan_zhi)
    except Exception:
        all_sha = {}
    # 课传地支集合（三传 + 四课上神/下神）
    pan = set(sanchuan)
    for k in (sike or []):
        if isinstance(k, dict):
            pan.add(k.get('上神', '')); pan.add(k.get('下神', ''))
        elif isinstance(k, (list, tuple)) and len(k) >= 2:
            pan.add(k[1])
    hits = {}
    for name, zhi in all_sha.items():
        if zhi and zhi in ZHI and zhi in pan:
            hits[name] = zhi
    ji_hit = [k for k in hits if k in JI_SHEN]
    xiong_hit = [k for k in hits if k in XIONG_SHA]
    return {
        '位置': {k: v for k, v in all_sha.items() if v},
        '命中': hits,
        '命中数': len(hits),
        '吉神命中': ji_hit,
        '凶煞命中': xiong_hit,
        '吉神数': len(ji_hit),
        '凶煞数': len(xiong_hit),
    }


def build_yanqin(year_zhi, lunar_month, ri_zhi, hour_zhi):
    """演禽特征（实验性，择日向）。缺年/月则退化起「日禽+时禽」（日支+时支即可）。"""
    from engine.yanqin_analyzer import YanQinAnalyzer
    if not (ri_zhi and hour_zhi):
        return {}
    month_zhi = MONTH_ZHI.get(lunar_month, '') if lunar_month else ''
    try:
        ya = YanQinAnalyzer()
        if year_zhi and month_zhi:
            # 完整：四禽 + 泊宫 + 格局 + 评分
            r = ya.analyze_four_qin(year_zhi, month_zhi, ri_zhi, hour_zhi)
            return {
                '四禽': r.get('四禽', {}),
                '泊宫': r.get('泊宫', {}),
                '格局判定': r.get('格局判定', []),
                '综合评分': r.get('综合评分', ''),
                '吉凶断语': r.get('吉凶断语', []),
            }
        # 退化：仅日禽 + 时禽（原书无年月，起不了四禽）
        ri_qin = ya.get_ri_qin(ri_zhi)
        shi_qin = ya.get_shi_qin(hour_zhi, ri_qin)
        return {
            '四禽': {
                '日禽': {'宿': ri_qin, '禽星': ya.XIU_TO_QIN.get(ri_qin, ''), '吉凶': ya.XIU_JIXIONG.get(ri_qin, '平')},
                '时禽': {'宿': shi_qin, '禽星': ya.XIU_TO_QIN.get(shi_qin, ''), '吉凶': ya.XIU_JIXIONG.get(shi_qin, '平')},
            },
            '退化': True,
        }
    except Exception:
        return {}


def build_flat_vector(ri_gan, ri_zhi, sanchuan, sike, features, shensha, zhanlei):
    """扁平特征向量（供 CBR/训练消费）。"""
    from engine.knowledge_features import relation, WX
    vec = {}
    vec['ri_gan'] = ri_gan
    vec['ri_zhi'] = ri_zhi
    vec['zhanlei'] = zhanlei
    chu = sanchuan[0] if sanchuan else ''
    vec['fayong'] = chu
    vec['fayong_wuxing'] = WX.get(chu, '')
    # 发用对日干/日支关系
    if chu and ri_gan:
        vec['fayong_ri_gan'] = relation(chu, ri_gan)['relation']
    if chu and ri_zhi:
        vec['fayong_ri_zhi'] = relation(chu, ri_zhi)['relation']
    # 三传结构
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
    # 课格/毕法/变格 命中数
    vec['keti_count'] = len(features.get('keti', []))
    vec['bifa_count'] = len((features.get('bifa', {}) or {}).get('断法', []))
    vec['special_count'] = len((features.get('special', {}) or {}).get('匹配课格', []))
    vec['bianjie_count'] = len((features.get('bianjie', {}) or {}).get('匹配变格', []))
    # 神煞
    vec['ji_sha_count'] = shensha.get('吉神数', 0)
    vec['xiong_sha_count'] = shensha.get('凶煞数', 0)
    vec['shensha_hit_count'] = shensha.get('命中数', 0)
    return vec


def main():
    lm = json.load(open('data/longmarch_annotations.json', encoding='utf-8'))
    eng = SiKeSanChuanCalculator2()
    gc = GuiRenCalculator()

    out = []
    n = 0
    for c in lm['cases']:
        cid = c['case_id']
        gz = c.get('day_ganzhi', '')
        yj = c.get('yue_jiang', '')
        shi = c.get('shichen', '')
        if not (len(gz) == 2 and yj and shi):
            continue
        ri_gan, ri_zhi = gz[0], gz[1]
        sanchuan = c.get('sanchuan') or []
        sike_raw = c.get('sike') or []
        # 引擎基础（天地盘 + 四课 + 天将）；P1：统一到权威 V2 引擎
        tdp = eng.get_tiandi_pan(yj, shi)
        sike_tuples = eng.qi_sike(ri_gan, ri_zhi, tdp)
        sike = [[t[0], t[1], t[2]] for t in sike_tuples]
        tj = gc.arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shi)
        sd = find_solar(c.get('year'), c.get('month'), gz) if c.get('year') and c.get('month') else None
        sd = sd or date(2026, 1, 1)

        # 8 类引擎特征（与 engine_hits 口径一致）
        f = extract_features(ri_gan, ri_zhi, '', '', yj, shi, sanchuan, sike,
                             tj['天将映射'], tp, c.get('zhanlei', '其他'), sec=c.get('sec', ''),
                             y=sd.year, m=sd.month, d=sd.day,
                             sanchuan_tianjiang=[tj['天将映射'].get(x, '') for x in sanchuan])

        # 神煞（用 year 年支 + month 月建）
        nian_zhi = (c.get('year') or '')[-1:] if c.get('year') else ''
        nian_zhi = nian_zhi if nian_zhi in ZHI else ''
        lunar_month = c.get('month') or 0
        shensha = build_shensha(ri_gan, ri_zhi, lunar_month, nian_zhi, sanchuan, sike)

        # 演禽（实验性）
        yanqin = build_yanqin(nian_zhi, lunar_month, ri_zhi, shi)

        # 扁平向量
        vec = build_flat_vector(ri_gan, ri_zhi, sanchuan, sike, f, shensha, c.get('zhanlei', ''))

        rec = {
            'case_id': cid,
            'sec': c.get('sec', ''),
            'sec_name': c.get('sec_name', ''),
            'zhanlei': c.get('zhanlei', ''),
            'label': c.get('label', ''),
            'day_ganzhi': gz,
            'yue_jiang': yj,
            'shichen': shi,
            'sanchuan': sanchuan,
            'sike': sike_raw,
            'ben_ming': c.get('ben_ming', ''),
            'year': c.get('year', ''),
            'month': lunar_month,
            'duanyu': c.get('duanyu', ''),
            'features': {
                'keti': [k['课体'] for k in f.get('keti', [])],
                'bifa': [(d['法句'], d.get('分类', '')) for d in f.get('bifa', {}).get('断法', [])],
                'special': f.get('special', {}).get('匹配课格', []),
                'bianjie': f.get('bianjie', {}).get('匹配变格', []),
                'yingqi': f.get('yingqi', ''),
                'shensha': shensha,
                'leixiang': f.get('leixiang', []),
                'tianjiang': {k: v for k, v in (tj['天将映射'] or {}).items()},
                'duanan': f.get('duanan', {}),
                'yanqin': yanqin,
            },
            'annotation': c.get('annotation') or {},
            'vector': vec,
        }
        out.append(rec)
        n += 1

    json.dump({'meta': {'source': 'longmarch_annotations.json', 'total': n,
                        'schema': '基础字段 + 10类引擎特征 + 标注四元组 + 扁平向量'},
               'cases': out},
              open('data/longmarch_feature_vectors.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'已构建 {n} 案特征向量 → data/longmarch_feature_vectors.json')


if __name__ == '__main__':
    main()
