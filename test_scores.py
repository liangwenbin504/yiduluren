#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试评分计算模块"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'data'))

print('=' * 60)
print('测试模块导入...')
print('=' * 60)

# 测试斗首模块
try:
    from douhou_analyzer import DouhouKegeAnalyzer
    print('[OK] DouhouKegeAnalyzer 导入成功')
except Exception as e:
    print(f'[FAIL] DouhouKegeAnalyzer 导入失败: {e}')

# 测试天地盘模块
try:
    from dizhi_layout_generator import arrange_tiandi_pan
    print('[OK] arrange_tiandi_pan 导入成功')
except Exception as e:
    print(f'[FAIL] arrange_tiandi_pan 导入失败: {e}')

# 测试四课三传模块
try:
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print('[OK] SiKeSanChuanCalculator 导入成功')
except Exception as e:
    print(f'[FAIL] SiKeSanChuanCalculator 导入失败: {e}')

# 测试演禽模块
try:
    from yanqin_analyzer import YanQinAnalyzer
    print('[OK] YanQinAnalyzer 导入成功')
except Exception as e:
    print(f'[FAIL] YanQinAnalyzer 导入失败: {e}')

# 测试贵人模块
try:
    from gui_ren_engine import GuiRenCalculator
    print('[OK] GuiRenCalculator 导入成功')
except Exception as e:
    print(f'[FAIL] GuiRenCalculator 导入失败: {e}')

# 测试六亲模块
try:
    from liuqin_engine import LiuQinCalculator
    print('[OK] LiuQinCalculator 导入成功')
except Exception as e:
    print(f'[FAIL] LiuQinCalculator 导入失败: {e}')

print()
print('=' * 60)
print('测试评分计算...')
print('=' * 60)

# 测试斗首评分
print('\n1. 斗首评分测试:')
try:
    analyzer = DouhouKegeAnalyzer()
    sizhu = {'年柱': '丙午', '月柱': '甲午', '日柱': '甲寅', '时柱': '甲子'}
    result = analyzer.analyze_kege('壬', sizhu)
    score = result.get('综合评分', 0)
    print(f'   坐山: 壬, 四柱: 丙午 甲午 甲寅 甲子')
    print(f'   斗首评分: {score}')
    print(f'   课格格局: {result.get("课格格局", [])}')
except Exception as e:
    import traceback
    print(f'   斗首评分计算失败: {e}')
    traceback.print_exc()

# 测试大六壬评分
print('\n2. 大六壬评分测试:')
try:
    tiandi_pan = arrange_tiandi_pan('亥', '子')
    print(f'   天地盘: {tiandi_pan}')
    
    calc = SiKeSanChuanCalculator()
    sike = calc.qi_sike('甲', '寅', tiandi_pan)
    print(f'   四课: {sike}')
    
    sanchuan = calc.fa_sanchuan(sike, '甲', '寅', tiandi_pan)
    keti = sanchuan.get('课体', '')
    print(f'   三传: 初传={sanchuan.get("初传")}, 中传={sanchuan.get("中传")}, 末传={sanchuan.get("末传")}')
    print(f'   课体: {keti}')
    
    # 评分规则
    good_keti = ['元首课', '重审课', '知一课', '涉害课', '遥克课', '别责课', '八专课']
    bad_keti = ['反吟课', '伏吟课', '昴星课']
    
    if keti in good_keti:
        daliuren_score = 80
    elif keti in bad_keti:
        daliuren_score = 50
    else:
        daliuren_score = 70
    
    print(f'   大六壬评分: {daliuren_score}')
    
except Exception as e:
    import traceback
    print(f'   大六壬评分计算失败: {e}')
    traceback.print_exc()

# 测试演禽评分
print('\n3. 澹禽评分测试:')
try:
    yanqin = YanQinAnalyzer()
    day_zhi = '寅'
    
    yanqin_name = yanqin.get_ri_qin(day_zhi)
    yanqin_jixiong = yanqin._get_qin_jixiong(yanqin_name)
    
    print(f'   日干支: 甲寅')
    print(f'   澹禽: {yanqin_name}')
    print(f'   吉凶: {yanqin_jixiong}')
    
    if yanqin_jixiong == '吉':
        yanqin_score = 85
    elif yanqin_jixiong == '凶':
        yanqin_score = 50
    else:
        yanqin_score = 70
    
    print(f'   澹禽评分: {yanqin_score}')
    
except Exception as e:
    import traceback
    print(f'   澹禽评分计算失败: {e}')
    traceback.print_exc()

print()
print('=' * 60)
print('测试完成')
print('=' * 60)
