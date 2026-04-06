#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

# 根据用户选中的div，这一课的参数是：
# 月将：申，时辰：子
# 日干支需要从四课推断：第一课下神是己，说明日干是己
# 第三课下神是未，说明日支是未

url = 'http://localhost:5000/api/daliuren/score'
params = {
    'shan': '壬',  # 坐山
    'ri_gan': '己',  # 日干（从第一课推断）
    'ri_zhi': '未',  # 日支（从第三课推断）
    'yue_jiang': '申',  # 月将
    'shi_chen': '子'   # 时辰
}

print('=' * 70)
print('大六壬评分详细报告')
print('=' * 70)
print(f'坐山: {params["shan"]}')
print(f'日干支: {params["ri_gan"]}{params["ri_zhi"]}')
print(f'月将: {params["yue_jiang"]}')
print(f'时辰: {params["shi_chen"]}')
print()

try:
    r = requests.get(url, params=params, timeout=10)
    result = r.json()
    
    print('课体:', result.get('keti'))
    print('总分:', result.get('total_score'), '/', result.get('max_score'))
    print('评估:', result.get('pinggu'))
    print()
    
    print('评分详情:')
    print('-' * 50)
    for k, v in result.get('score_detail', {}).items():
        print(f'{k}:')
        for key, val in v.items():
            print(f'  {key}: {val}')
        print()
    
    print('三传:', result.get('sanchuan'))
    
except Exception as e:
    print('请求失败:', e)
