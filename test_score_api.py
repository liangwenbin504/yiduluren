#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

url = 'http://localhost:5000/api/daliuren/score'
params = {
    'shan': '壬',
    'ri_gan': '丙',
    'ri_zhi': '子',
    'yue_jiang': '亥',
    'shi_chen': '子'
}

try:
    r = requests.get(url, params=params, timeout=10)
    print('状态码:', r.status_code)
    result = r.json()
    print('成功:', result.get('success'))
    print('课体:', result.get('keti'))
    print('总分:', result.get('total_score'), '/', result.get('max_score'))
    print('评估:', result.get('pinggu'))
    print('评分详情:')
    for k, v in result.get('score_detail', {}).items():
        print('  ', k, ':', v)
except Exception as e:
    print('请求失败:', e)
