#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))

print('测试大六壬模块...')

try:
    from dizhi_layout_generator import arrange_tiandi_pan
    print('[OK] arrange_tiandi_pan 导入成功')
except Exception as e:
    print(f'[FAIL] arrange_tiandi_pan: {e}')

try:
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print('[OK] SiKeSanChuanCalculator 导入成功')
except Exception as e:
    print(f'[FAIL] SiKeSanChuanCalculator: {e}')

print()
print('测试计算...')

try:
    tiandi_pan = arrange_tiandi_pan('亥', '子')
    print(f'天地盘: {tiandi_pan}')
    
    calc = SiKeSanChuanCalculator()
    sike = calc.qi_sike('甲', '寅', tiandi_pan)
    print(f'四课: {sike}')
    
    sanchuan = calc.fa_sanchuan(sike, '甲', '寅', tiandi_pan)
    keti = sanchuan.get('课体', '')
    print(f'课体: {keti}')
    
    good_keti = ['元首课', '重审课', '知一课', '涉害课', '遥克课', '别责课', '八专课']
    bad_keti = ['反吟课', '伏吟课', '昴星课']
    
    if keti in good_keti:
        score = 80
    elif keti in bad_keti:
        score = 50
    else:
        score = 70
    
    print(f'大六壬评分: {score}')
    
except Exception as e:
    import traceback
    print(f'计算失败: {e}')
    traceback.print_exc()
