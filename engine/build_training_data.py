# -*- coding: utf-8 -*-
"""长征第1期 · 训练数据打包
================================================================
把 218 案特征向量 + label + 四元组标注，打包成标准训练集：
  ● meta：label/占类分布 + 特征 schema
  ● samples：每案 = 基础字段 + 数值特征 + 类别特征 + 原始特征名单 + 标注四元组
数值特征供下游训练器直接消费；类别特征供 one-hot；原始名单供检索/分析。
"""
import json, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEC = json.load(open(os.path.join(BASE, 'data', 'longmarch_feature_vectors.json'), encoding='utf-8'))
cases = VEC['cases']

samples = []
for c in cases:
    v = c['vector']
    f = c['features']
    shensha = f.get('shensha', {})
    ann = c.get('annotation') or {}
    samples.append({
        'case_id': c['case_id'],
        'label': c.get('label', ''),
        'zhanlei': c.get('zhanlei', ''),
        'sec_name': c.get('sec_name', ''),
        'day_ganzhi': c.get('day_ganzhi', ''),
        'sanchuan': c.get('sanchuan', []),
        # 数值特征（可训练）
        'numeric': {
            'keti_count': v.get('keti_count', 0),
            'bifa_count': v.get('bifa_count', 0),
            'special_count': v.get('special_count', 0),
            'bianjie_count': v.get('bianjie_count', 0),
            'ji_sha_count': v.get('ji_sha_count', 0),
            'xiong_sha_count': v.get('xiong_sha_count', 0),
            'shensha_hit_count': v.get('shensha_hit_count', 0),
        },
        # 类别特征（供 one-hot）
        'categorical': {
            'fayong': v.get('fayong', ''),
            'fayong_wuxing': v.get('fayong_wuxing', ''),
            'fayong_ri_gan': v.get('fayong_ri_gan', ''),
            'fayong_ri_zhi': v.get('fayong_ri_zhi', ''),
            'chuan_bian': v.get('chuan_bian', ''),
            'chu_ke_zhong': v.get('chu_ke_zhong', ''),
            'zhong_ke_mo': v.get('zhong_ke_mo', ''),
        },
        # 原始特征名单（课格/毕法/特殊/变格/神煞吉凶，供检索/one-hot）
        'raw': {
            'keti': f.get('keti', []),
            'bifa': [b[0] for b in f.get('bifa', [])],
            'special': f.get('special', []),
            'bianjie': f.get('bianjie', []),
            'ji_shen': shensha.get('吉神命中', []),
            'xiong_sha': shensha.get('凶煞命中', []),
        },
        # 标注四元组（断语判据）
        'annotation': {
            'leishen': ann.get('leishen', []),
            'liqi': ann.get('liqi', []),
            'leixiang': ann.get('leixiang', []),
            'yingqi': ann.get('yingqi', []),
        },
    })

label_dist = dict(Counter(c.get('label', '') for c in cases))
zhanlei_dist = dict(Counter(c.get('zhanlei', '') for c in cases))

out = {
    'meta': {
        'source': 'longmarch_feature_vectors.json',
        'total': len(samples),
        'label_dist': label_dist,
        'zhanlei_dist': zhanlei_dist,
        'numeric_schema': ['keti_count', 'bifa_count', 'special_count', 'bianjie_count',
                           'ji_sha_count', 'xiong_sha_count', 'shensha_hit_count'],
        'categorical_schema': ['fayong', 'fayong_wuxing', 'fayong_ri_gan', 'fayong_ri_zhi',
                               'chuan_bian', 'chu_ke_zhong', 'zhong_ke_mo'],
        'note': 'label 二分类主体=吉(33)+凶(173)=206；未知(11)+平(1)=12 待定。古例凶多吉少是原书特性，训练需注意类别不平衡。',
    },
    'samples': samples,
}

json.dump(out, open(os.path.join(BASE, 'data', 'longmarch_training_data.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'训练数据已打包 {len(samples)} 案 → data/longmarch_training_data.json')
print(f'label 分布: {label_dist}')
print(f'数值特征 {len(out["meta"]["numeric_schema"])} 维 + 类别特征 {len(out["meta"]["categorical_schema"])} 维')
