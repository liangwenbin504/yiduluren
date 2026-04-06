#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
三模块审核测试脚本
逐一验证斗首、演禽、大六壬评分计算
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))

print('=' * 70)
print('三模块审核测试')
print('=' * 70)

# 测试数据
test_cases = [
    {'name': '测试1-甲寅日', 'sizhu': {'年柱': '丙午', '月柱': '甲午', '日柱': '甲寅', '时柱': '甲子'}, 'shan': '壬'},
    {'name': '测试2-丙子日', 'sizhu': {'年柱': '乙巳', '月柱': '丁丑', '日柱': '丙子', '时柱': '戊子'}, 'shan': '壬'},
    {'name': '测试3-庚申日', 'sizhu': {'年柱': '乙巳', '月柱': '戊寅', '日柱': '庚申', '时柱': '丙子'}, 'shan': '壬'},
]

# ============================================================
# 一、斗首择日模块审核
# ============================================================
print('\n' + '=' * 70)
print('一、斗首择日模块审核')
print('=' * 70)

try:
    from douhou_analyzer import DouhouKegeAnalyzer
    doushou_analyzer = DouhouKegeAnalyzer()
    print('[OK] 斗首模块导入成功')
except Exception as e:
    print(f'[FAIL] 斗首模块导入失败: {e}')
    doushou_analyzer = None

if doushou_analyzer:
    for tc in test_cases:
        print(f"\n{tc['name']}: 坐山={tc['shan']}, 四柱={tc['sizhu']}")
        result = doushou_analyzer.analyze_kege(tc['shan'], tc['sizhu'])
        
        score = result.get('综合评分', 0)
        patterns = result.get('课格格局', [])
        sizhu_analysis = result.get('四柱分析', {})
        
        print(f"  斗首评分: {score}")
        print(f"  课格格局: {[p['格局名称'] for p in patterns]}")
        
        for pillar, info in sizhu_analysis.items():
            print(f"    {pillar}: {info.get('干支')} -> 化气={info.get('化气五行')}, 星曜={info.get('斗首星曜')}")
        
        # 判断是否达标
        if score >= 70:
            print(f"  [PASS] 斗首评分达标 (>=70)")
        else:
            print(f"  [FAIL] 斗首评分不达标 (<70)")

# ============================================================
# 二、演禽模块审核
# ============================================================
print('\n' + '=' * 70)
print('二、演禽模块审核')
print('=' * 70)

try:
    from yanqin_analyzer import YanQinAnalyzer
    yanqin_analyzer = YanQinAnalyzer()
    print('[OK] 演禽模块导入成功')
except Exception as e:
    print(f'[FAIL] 演禽模块导入失败: {e}')
    yanqin_analyzer = None

if yanqin_analyzer:
    for tc in test_cases:
        print(f"\n{tc['name']}:")
        
        day_zhi = tc['sizhu']['日柱'][1] if len(tc['sizhu']['日柱']) > 1 else '子'
        
        try:
            yanqin_name = yanqin_analyzer.get_ri_qin(day_zhi)
            yanqin_jixiong = yanqin_analyzer.XIU_JIXIONG.get(yanqin_name, '平')
            
            # 评分规则
            if yanqin_jixiong == '吉':
                yanqin_score = 85
            elif yanqin_jixiong == '凶':
                yanqin_score = 50
            else:
                yanqin_score = 70
            
            print(f"  日支: {day_zhi}")
            print(f"  日禽: {yanqin_name}")
            print(f"  吉凶: {yanqin_jixiong}")
            print(f"  演禽评分: {yanqin_score}")
            
            if yanqin_score >= 70:
                print(f"  [PASS] 演禽评分达标 (>=70)")
            else:
                print(f"  [FAIL] 演禽评分不达标 (<70)")
                
        except Exception as e:
            import traceback
            print(f"  [ERROR] 演禽计算失败: {e}")
            traceback.print_exc()

# ============================================================
# 三、大六壬模块审核
# ============================================================
print('\n' + '=' * 70)
print('三、大六壬模块审核')
print('=' * 70)

try:
    from dizhi_layout_generator import arrange_tiandi_pan
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print('[OK] 大六壬模块导入成功')
except Exception as e:
    print(f'[FAIL] 大六壬模块导入失败: {e}')
    arrange_tiandi_pan = None
    SiKeSanChuanCalculator = None

if arrange_tiandi_pan and SiKeSanChuanCalculator:
    calc = SiKeSanChuanCalculator()
    
    for tc in test_cases:
        print(f"\n{tc['name']}:")
        
        ri_gan = tc['sizhu']['日柱'][0] if tc['sizhu']['日柱'] else '甲'
        ri_zhi = tc['sizhu']['日柱'][1] if len(tc['sizhu']['日柱']) > 1 else '子'
        
        # 测试多个时辰
        for shichen in ['子', '卯', '午', '酉']:
            try:
                tiandi_pan = arrange_tiandi_pan('亥', shichen)
                sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
                sanchuan = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
                
                keti = sanchuan.get('课体', '')
                
                # 评分规则
                good_keti = ['元首课', '重审课', '知一课', '涉害课', '遥克课', '别责课', '八专课']
                bad_keti = ['反吟课', '伏吟课', '昴星课']
                
                if keti in good_keti:
                    daliuren_score = 80
                elif keti in bad_keti:
                    daliuren_score = 50
                else:
                    daliuren_score = 70
                
                print(f"  时辰={shichen}: 课体={keti}, 评分={daliuren_score}")
                
            except Exception as e:
                print(f"  时辰={shichen}: [ERROR] {e}")

# ============================================================
# 四、综合评分测试
# ============================================================
print('\n' + '=' * 70)
print('四、综合评分测试')
print('=' * 70)

print("\n寻找三种评分同时>=70的日课...")
print("提示：如果评分标准过高，可能需要降低阈值或扩大日期范围")

print('\n' + '=' * 70)
print('审核完成')
print('=' * 70)
