#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
择日结果显示问题 - 深度调试脚本
用于找出结果不显示的根本原因
"""

import sys
import os
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.precise_calendar import PreciseCalendar, get_sizhu_accurate
from engine.long_de_ke_selector import LongDeKeSelector

# 13 种课格
KE_GE_TYPES = [
    '富贵课', '荣华课', '龙德课', '官爵课', '时泰课',
    '和美课', '合欢课', '回环课', '亨通课',
    '华盖乘轩课', '德庆课', '斫轮课', '铸印乘轩课'
]

def check_liuren_kege(ri_ganzhi, shi_zhi):
    """检查六壬课格（与 GUI 中相同的逻辑）"""
    matched = []
    ri_gan = ri_ganzhi[0]
    ri_zhi = ri_ganzhi[1]
    
    # 龙德课：四正之时
    if shi_zhi in ['子', '午', '卯', '酉']:
        if ri_gan in ['甲', '戊', '庚', '乙', '己', '丙', '丁', '壬', '癸', '辛']:
            matched.append('龙德课')
    
    # 富贵课
    if ri_gan in ['甲', '己'] and ri_zhi in ['子', '午', '卯', '酉']:
        matched.append('富贵课')
    elif ri_gan in ['丙', '辛'] and ri_zhi in ['寅', '申', '巳', '亥']:
        matched.append('富贵课')
    
    # 荣华课
    if ri_zhi in ['子', '丑', '寅', '卯', '辰', '巳']:
        matched.append('荣华课')
    
    # 官爵课
    if ri_gan in ['甲', '乙'] and shi_zhi in ['寅', '卯']:
        matched.append('官爵课')
    elif ri_gan in ['丙', '丁'] and shi_zhi in ['巳', '午']:
        matched.append('官爵课')
    
    # 时泰课
    if shi_zhi in ['辰', '戌', '丑', '未']:
        matched.append('时泰课')
    
    # 和美课
    if ri_gan in ['戊', '己'] and shi_zhi in ['子', '午']:
        matched.append('和美课')
    
    # 合欢课
    if ri_gan in ['庚', '辛'] and shi_zhi in ['卯', '酉']:
        matched.append('合欢课')
    
    # 回环课
    if (ri_gan in ['甲', '乙'] and ri_zhi in ['寅', '卯']) or \
       (ri_gan in ['丙', '丁'] and ri_zhi in ['巳', '午']) or \
       (ri_gan in ['戊', '己'] and ri_zhi in ['辰', '戌', '丑', '未']) or \
       (ri_gan in ['庚', '辛'] and ri_zhi in ['申', '酉']) or \
       (ri_gan in ['壬', '癸'] and ri_zhi in ['亥', '子']):
        matched.append('回环课')
    
    # 亨通课
    if shi_zhi in ['寅', '申', '巳', '亥']:
        matched.append('亨通课')
    
    # 华盖乘轩课
    if ri_zhi in ['辰', '戌', '丑', '未']:
        matched.append('华盖乘轩课')
    
    # 德庆课
    if ri_gan in ['甲', '丙', '戊', '庚', '壬']:
        matched.append('德庆课')
    
    # 斫轮课
    if ri_gan in ['乙', '丁', '己', '辛', '癸']:
        matched.append('斫轮课')
    
    # 铸印乘轩课
    if shi_zhi in ['丑', '未']:
        matched.append('铸印乘轩课')
    
    return matched if len(matched) > 0 else ['普通课']


def test_date_calculation():
    """测试单日期计算"""
    print("=" * 70)
    print("择日计算深度调试")
    print("=" * 70)
    
    # 测试参数
    test_date = datetime(2026, 3, 15)  # 第一天
    shan = '壬'
    xiang = '丙'
    selected_kege_types = {'龙德课'}
    min_score = 7.0
    
    print(f"\n测试参数:")
    print(f"  日期：{test_date.strftime('%Y-%m-%d')}")
    print(f"  山向：{shan}山{xiang}向")
    print(f"  已选课格：{selected_kege_types}")
    print(f"  最低评分：{min_score}")
    print()
    
    # 初始化
    calendar = PreciseCalendar()
    long_de_selector = LongDeKeSelector()
    
    results = []
    
    # 计算 12 个时辰
    print("开始计算 12 个时辰...")
    for shi_zhi in calendar.DIZHI:
        shi_index = calendar.DIZHI.index(shi_zhi)
        shi_hour = shi_index * 2
        
        try:
            # 计算四柱
            sizhu = get_sizhu_accurate(
                test_date.year, test_date.month, test_date.day,
                shi_hour, 0, 116.4074, 39.9042
            )
            
            ri_ganzhi = sizhu['日柱']
            ri_gan = ri_ganzhi[0]
            
            # 计算斗首课格
            if ri_gan in ['甲', '己']:
                kege_name = '元辰课'
                kege_score = 8.5
            elif ri_gan in ['丙', '辛']:
                kege_name = '武财课'
                kege_score = 9.0
            elif ri_gan in ['戊', '癸']:
                kege_name = '贪官课'
                kege_score = 7.5
            elif ri_gan in ['乙', '庚']:
                kege_name = '廉贞课'
                kege_score = 6.0
            else:
                kege_name = '破鬼课'
                kege_score = 5.0
            
            # 检查评分
            if kege_score < min_score:
                continue
            
            # 检查六壬课格
            matched_kege = check_liuren_kege(ri_ganzhi, shi_zhi)
            
            if len(matched_kege) == 0:
                continue
            
            # 检查是否在选择的课格中
            if len(selected_kege_types) > 0:
                if not any(k in selected_kege_types for k in matched_kege):
                    continue
            
            # 检查龙德课
            is_longde = False
            longde_type = ''
            if '龙德课' in matched_kege:
                try:
                    is_longde, longde_type = long_de_selector.is_longde_ke(
                        ri_ganzhi,
                        sizhu.get('月柱', ['',''])[1] if sizhu.get('月柱') else '',
                        sizhu.get('年柱', ['',''])[1] if sizhu.get('年柱') else '',
                        []
                    )
                except Exception as e:
                    print(f"  {shi_zhi}时：龙德课检查失败 - {e}")
                    is_longde = False
                    longde_type = ''
            
            # 计算吉神
            jishen = []
            if ri_ganzhi[0] in ['甲', '戊', '庚']:
                jishen.append('天乙贵人')
            if shi_zhi in ['子', '午', '卯', '酉']:
                jishen.append('桃花')
            
            # 综合评分
            total_score = kege_score + len(matched_kege) * 0.5
            if is_longde:
                total_score += 2.0
            
            # 添加到结果
            results.append({
                '日期': test_date.strftime('%Y-%m-%d'),
                '时辰': shi_zhi,
                '四柱': f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}",
                '斗首课格': kege_name,
                '评分': round(total_score, 1),
                '课格类型': ', '.join(matched_kege[:3]),
                '吉神': ', '.join(jishen[:5]),
                '龙德课': is_longde,
                '龙德类型': longde_type
            })
            
            print(f"  ✓ {shi_zhi}时：{kege_name}, 课格：{', '.join(matched_kege[:3])}, 评分：{total_score:.1f}, 龙德：{is_longde}")
            
        except Exception as e:
            print(f"  ✗ {shi_zhi}时：错误 - {e}")
            continue
    
    print(f"\n结果统计:")
    print(f"  总结果数：{len(results)}")
    if len(results) > 0:
        print(f"  最高评分：{max(r['评分'] for r in results)}")
        print(f"  最低评分：{min(r['评分'] for r in results)}")
        print(f"\n前 3 个结果:")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r['日期']} {r['时辰']}时 - 评分：{r['评分']}")
    else:
        print(f"  ❌ 未找到符合条件的日期")
        print(f"\n可能的原因:")
        print(f"  1. 斗首评分 < {min_score}")
        print(f"  2. 没有匹配到选择的课格：{selected_kege_types}")
        print(f"  3. 龙德课检查失败")
    
    print("\n" + "=" * 70)
    
    return len(results) > 0


if __name__ == '__main__':
    success = test_date_calculation()
    if success:
        print("\n✅ 测试通过：能找到结果")
        print("\n问题可能出在 GUI 的结果更新部分")
    else:
        print("\n❌ 测试失败：找不到结果")
        print("\n问题出在计算逻辑或筛选条件")
    
    input("\n按回车键退出...")
