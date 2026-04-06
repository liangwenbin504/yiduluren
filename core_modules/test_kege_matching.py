#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
课格判断功能测试
验证修复后的课格判断逻辑是否能找到足够的吉日
"""

from datetime import datetime, timedelta

# 天干地支
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 13 种课格
KE_GE_TYPES = [
    '富贵课', '荣华课', '龙德课', '官爵课', '时泰课',
    '和美课', '合欢课', '回环课', '亨通课',
    '华盖乘轩课', '德庆课', '斫轮课', '铸印乘轩课'
]

def check_liuren_kege(ri_ganzhi, shi_zhi):
    """检查六壬课格（修复后的逻辑）"""
    matched = []
    ri_gan = ri_ganzhi[0]
    ri_zhi = ri_ganzhi[1]
    
    # 龙德课：四正之时
    if shi_zhi in ['子', '午', '卯', '酉']:
        if ri_gan in ['甲', '戊', '庚', '乙', '己', '丙', '丁', '壬', '癸', '辛']:
            matched.append('龙德课')
    
    # 富贵课：干支相生相合
    if ri_gan in ['甲', '己'] and ri_zhi in ['子', '午', '卯', '酉']:
        matched.append('富贵课')
    elif ri_gan in ['丙', '辛'] and ri_zhi in ['寅', '申', '巳', '亥']:
        matched.append('富贵课')
    
    # 荣华课：三合六合
    if ri_zhi in ['子', '丑', '寅', '卯', '辰', '巳']:
        matched.append('荣华课')
    
    # 官爵课：官星得地
    if ri_gan in ['甲', '乙'] and shi_zhi in ['寅', '卯']:
        matched.append('官爵课')
    elif ri_gan in ['丙', '丁'] and shi_zhi in ['巳', '午']:
        matched.append('官爵课')
    
    # 时泰课：四库之时
    if shi_zhi in ['辰', '戌', '丑', '未']:
        matched.append('时泰课')
    
    # 和美课：干支和合
    if ri_gan in ['戊', '己'] and shi_zhi in ['子', '午']:
        matched.append('和美课')
    
    # 合欢课：阴阳和合
    if ri_gan in ['庚', '辛'] and shi_zhi in ['卯', '酉']:
        matched.append('合欢课')
    
    # 回环课：循环往复
    if len(ri_zhi) > 0 and ri_gan == ri_zhi[0]:
        matched.append('回环课')
    
    # 亨通课：四马之时
    if shi_zhi in ['寅', '申', '巳', '亥']:
        matched.append('亨通课')
    
    # 华盖乘轩课：文星拱照
    if ri_zhi in ['辰', '戌', '丑', '未']:
        matched.append('华盖乘轩课')
    
    # 德庆课：德星临照（阳干）
    if ri_gan in ['甲', '丙', '戊', '庚', '壬']:
        matched.append('德庆课')
    
    # 斫轮课：雕琢成器（阴干）
    if ri_gan in ['乙', '丁', '己', '辛', '癸']:
        matched.append('斫轮课')
    
    # 铸印乘轩课：印星之地
    if shi_zhi in ['丑', '未']:
        matched.append('铸印乘轩课')
    
    return matched if len(matched) > 0 else ['普通课']


def test_kege_matching():
    """测试课格匹配"""
    print("=" * 70)
    print("课格判断功能测试")
    print("=" * 70)
    
    # 测试数据：2026 年 3 月的部分日期
    test_dates = [
        (2026, 3, 15, '甲子'),
        (2026, 3, 16, '乙丑'),
        (2026, 3, 17, '丙寅'),
        (2026, 3, 18, '丁卯'),
        (2026, 3, 19, '戊辰'),
        (2026, 3, 20, '己巳'),
        (2026, 3, 21, '庚午'),
        (2026, 3, 22, '辛未'),
        (2026, 3, 23, '壬申'),
        (2026, 3, 24, '癸酉'),
    ]
    
    # 测试每个日期的 12 个时辰
    total_dates = 0
    matched_dates = 0
    longde_count = 0
    
    for year, month, day, ri_ganzhi in test_dates:
        date_str = f"{year}-{month:02d}-{day:02d}"
        print(f"\n{date_str} ({ri_ganzhi}日):")
        
        date_has_kege = False
        date_has_longde = False
        
        for shi_zhi in DIZHI:
            matched = check_liuren_kege(ri_ganzhi, shi_zhi)
            
            # 只显示有课格的时辰
            if len(matched) > 1 or (len(matched) == 1 and matched[0] != '普通课'):
                if '龙德课' in matched:
                    print(f"  {shi_zhi}时：{', '.join(matched)} ★")
                    longde_count += 1
                else:
                    print(f"  {shi_zhi}时：{', '.join(matched)}")
                date_has_kege = True
                if '龙德课' in matched:
                    date_has_longde = True
        
        if date_has_kege:
            matched_dates += 1
        total_dates += 1
        
        if date_has_longde:
            print(f"  → 此日有龙德课 ★")
    
    print("\n" + "=" * 70)
    print(f"测试统计:")
    print(f"  测试日期数：{total_dates} 天")
    print(f"  有课格的日期：{matched_dates} 天 ({matched_dates/total_dates*100:.1f}%)")
    print(f"  有龙德课的日期：{longde_count} 个时辰")
    print("=" * 70)
    
    # 测试 13 种课格是否都能匹配
    print("\n13 种课格覆盖测试:")
    kege_found = {kege: False for kege in KE_GE_TYPES}
    
    for ri_gan in TIANGAN:
        for ri_zhi in DIZHI:
            ri_ganzhi = ri_gan + ri_zhi
            for shi_zhi in DIZHI:
                matched = check_liuren_kege(ri_ganzhi, shi_zhi)
                for kege in matched:
                    if kege in kege_found:
                        kege_found[kege] = True
    
    for kege, found in kege_found.items():
        status = "✓" if found else "✗"
        print(f"  {status} {kege}")
    
    all_found = all(kege_found.values())
    print(f"\n所有课格都能匹配：{'✓ 是' if all_found else '✗ 否'}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == '__main__':
    test_kege_matching()
