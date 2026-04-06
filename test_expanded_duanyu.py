#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试扩充后的断语库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu

def test_expanded_library():
    """测试扩充断语库"""
    
    print("=" * 80)
    print("扩充断语库测试")
    print("=" * 80)
    
    duanyu = LiuRenKetiDuanyu()
    
    # 测试1: 加载扩充断语库
    print("\n【测试1】加载扩充断语库")
    expanded_lib = duanyu.load_expanded_library()
    print(f"断语库版本：{expanded_lib.get('metadata', {}).get('version', '未知')}")
    print(f"文献来源：{', '.join(expanded_lib.get('metadata', {}).get('sources', []))}")
    
    # 测试2: 获取禄马贵人断语
    print("\n【测试2】禄马贵人断语")
    luma_types = ['禄神到山', '驿马到山', '贵人到山', '禄神到向', '驿马到向', '贵人到向']
    for luma_type in luma_types:
        luma_duanyu = duanyu.get_expanded_luma_duanyu(luma_type)
        if luma_duanyu:
            print(f"\n{luma_type}：")
            for sub_key, sub_value in list(luma_duanyu.items())[:2]:
                if isinstance(sub_value, dict):
                    print(f"  · {sub_key}：{sub_value.get('断语', '无')[:50]}...")
    
    # 测试3: 获取龙德课断语
    print("\n【测试3】龙德课断语")
    longde_types = ['月将龙德课', '太岁龙德课', '真龙德课']
    for longde_type in longde_types:
        longde_duanyu = duanyu.get_expanded_longde_duanyu(longde_type)
        print(f"\n{longde_type}：")
        print(f"  断语：{longde_duanyu.get('断语', '无')[:60]}...")
        print(f"  等级：{longde_duanyu.get('等级', '未知')}")
    
    # 测试4: 获取山向断语
    print("\n【测试4】山向断语")
    shan_list = ['壬山', '子山', '癸山', '艮山', '寅山']
    for shan in shan_list:
        shan_duanyu = duanyu.get_shan_xiang_duanyu(shan)
        print(f"\n{shan}：")
        print(f"  五行：{shan_duanyu.get('五行', '未知')}")
        print(f"  元辰：{shan_duanyu.get('元辰', '未知')}")
        print(f"  禄神：{shan_duanyu.get('禄神', '未知')}")
        print(f"  驿马：{shan_duanyu.get('驿马', '未知')}")
        print(f"  贵人：{', '.join(shan_duanyu.get('贵人', []))}")
    
    # 测试5: 获取斗首课格断语
    print("\n【测试5】斗首课格断语")
    kege_list = ['元辰课', '武财课', '贪狼课', '廉贞课', '破军课']
    for kege in kege_list:
        kege_duanyu = duanyu.get_doushou_duanyu(kege)
        print(f"\n{kege}：")
        print(f"  断语：{kege_duanyu.get('断语', '无')[:60]}...")
        print(f"  宜：{', '.join(kege_duanyu.get('宜', []))}")
        print(f"  忌：{', '.join(kege_duanyu.get('忌', []))}")
    
    # 测试6: 生成禄马贵人报告
    print("\n【测试6】禄马贵人报告")
    luma_info = {
        '禄神到山': {'年禄到山': True, '日禄到山': True},
        '驿马到山': {'日马到山': True},
        '贵人到山': {'年贵到山': True, '日贵到山': True}
    }
    report = duanyu.generate_luma_duanyu_report(luma_info)
    print(report[:500])
    
    # 测试7: 生成山向综合报告
    print("\n【测试7】山向综合报告")
    report = duanyu.generate_shan_xiang_report('壬山', luma_info)
    print(report[:800])
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    test_expanded_library()
