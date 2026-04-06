#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬禄马贵人到山到向 - 使用示例和验证脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_modules.engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen


def test_case_1():
    """测试案例 1：壬山甲子年丙寅月甲子日子时"""
    print("\n" + "=" * 100)
    print("测试案例 1：壬山甲子年丙寅月甲子日子时")
    print("=" * 100)
    
    calculator = DaLiuRenLuMaGuiRen()
    result = calculator.analyze_full(
        mountain='壬',
        shichen='子',
        nian_gan='甲',
        nian_zhi='子',
        yue_gan='丙',
        yue_zhi='寅',
        ri_gan='甲',
        ri_zhi='子'
    )
    calculator.print_analysis(result)
    
    return result


def test_case_2():
    """测试案例 2：丙山丙午年甲午月丙午日午时"""
    print("\n" + "=" * 100)
    print("测试案例 2：丙山丙午年甲午月丙午日午时")
    print("=" * 100)
    
    calculator = DaLiuRenLuMaGuiRen()
    result = calculator.analyze_full(
        mountain='丙',
        shichen='午',
        nian_gan='丙',
        nian_zhi='午',
        yue_gan='甲',
        yue_zhi='午',
        ri_gan='丙',
        ri_zhi='午'
    )
    calculator.print_analysis(result)
    
    return result


def test_case_3():
    """测试案例 3：甲山甲寅年丙寅月甲寅日寅时"""
    print("\n" + "=" * 100)
    print("测试案例 3：甲山甲寅年丙寅月甲寅日寅时")
    print("=" * 100)
    
    calculator = DaLiuRenLuMaGuiRen()
    result = calculator.analyze_full(
        mountain='甲',
        shichen='寅',
        nian_gan='甲',
        nian_zhi='寅',
        yue_gan='丙',
        yue_zhi='寅',
        ri_gan='甲',
        ri_zhi='寅'
    )
    calculator.print_analysis(result)
    
    return result


def test_single_pillar():
    """测试单柱检查功能"""
    print("\n" + "=" * 100)
    print("测试单柱检查功能")
    print("=" * 100)
    
    calculator = DaLiuRenLuMaGuiRen()
    
    # 先获取天地盘
    from src.utils.dizhi_layout_generator import arrange_tiandi_pan
    tiandi_pan = arrange_tiandi_pan('亥', '子')
    
    # 检查日柱
    pillar_result = calculator.check_single_pillar(
        tian_gan='甲',
        di_zhi='子',
        tiandi_pan=tiandi_pan,
        shichen='子',
        shan_jia='子',
        xiang_shou='午',
        pillar_name='日'
    )
    
    print(f"\n单柱检查结果：")
    print(f"  柱名: {pillar_result['pillar']}")
    print(f"  天干: {pillar_result['tian_gan']}")
    print(f"  地支: {pillar_result['di_zhi']}")
    print(f"  禄神: {pillar_result['lu_zhi']}")
    print(f"  驿马: {pillar_result['ma_zhi']}")
    print(f"  贵人: {pillar_result['guiren_zhi']}")
    print(f"  到山: {pillar_result['lu_to_shan'] or pillar_result['ma_to_shan'] or pillar_result['guiren_to_shan']}")
    print(f"  到向: {pillar_result['lu_to_xiang'] or pillar_result['ma_to_xiang'] or pillar_result['guiren_to_xiang']}")
    print(f"  合格: {'✅' if pillar_result['pillar_qualified'] else '❌'}")


def test_ben_shan():
    """测试本山本向检查功能"""
    print("\n" + "=" * 100)
    print("测试本山本向检查功能")
    print("=" * 100)
    
    calculator = DaLiuRenLuMaGuiRen()
    
    # 先获取天地盘
    from src.utils.dizhi_layout_generator import arrange_tiandi_pan
    tiandi_pan = arrange_tiandi_pan('亥', '子')
    
    # 检查本山本向
    ben_shan_result = calculator.check_ben_shan_ben_xiang(
        mountain='壬',
        shan_jia='子',
        xiang_shou='午',
        tiandi_pan=tiandi_pan,
        shichen='子',
        nian_gan='甲',
        nian_zhi='子',
        yue_gan='丙',
        yue_zhi='寅',
        ri_gan='甲',
        ri_zhi='子'
    )
    
    print(f"\n本山本向检查结果：")
    print(f"  有本山本向吉课: {'✅' if ben_shan_result['has_ben_shan_ji'] else '❌'}")
    if ben_shan_result['has_ben_shan_ji']:
        print(f"  详情:")
        for result in ben_shan_result['results']:
            print(f"    - {result['desc']}")


def main():
    """主测试函数"""
    print("\n" + "=" * 100)
    print("大六壬禄马贵人到山到向 - 测试验证脚本")
    print("=" * 100)
    
    # 运行所有测试
    results = []
    
    try:
        results.append(("案例1", test_case_1()))
        results.append(("案例2", test_case_2()))
        results.append(("案例3", test_case_3()))
        test_single_pillar()
        test_ben_shan()
        
        # 总结
        print("\n" + "=" * 100)
        print("测试总结")
        print("=" * 100)
        for name, result in results:
            print(f"\n{name}:")
            print(f"  坐山: {result['mountain']}")
            print(f"  评分: {result['score']}分")
            print(f"  评语: {result['status']}")
            print(f"  合格数: {result['qualified_count']}/3")
            print(f"  本山本向: {'✅' if result['ben_shan_result']['has_ben_shan_ji'] else '❌'}")
        
        print("\n" + "=" * 100)
        print("✅ 所有测试完成！")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
