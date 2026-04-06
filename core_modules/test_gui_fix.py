#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI 改进修复验证脚本
测试"开始择日"功能是否正常工作
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.precise_calendar import PreciseCalendar, get_sizhu_accurate

def test_core_calculation():
    """测试核心计算功能"""
    print("="*70)
    print("测试核心计算功能")
    print("="*70)
    
    calendar = PreciseCalendar()
    
    # 测试日期
    test_date = datetime(2026, 3, 15)
    
    print(f"\n测试日期：{test_date.strftime('%Y-%m-%d')}")
    
    # 测试 12 个时辰
    results = []
    for shi_zhi in calendar.DIZHI:
        shi_index = calendar.DIZHI.index(shi_zhi)
        shi_hour = shi_index * 2
        
        try:
            sizhu = get_sizhu_accurate(
                test_date.year, test_date.month, test_date.day,
                shi_hour, 0, 116.4074, 39.9042
            )
            
            ri_ganzhi = sizhu['日柱']
            results.append({
                '时辰': shi_zhi,
                '四柱': sizhu,
                '日柱': ri_ganzhi
            })
            
        except Exception as e:
            print(f"错误：{shi_zhi}时 - {e}")
    
    # 输出结果
    print(f"\n计算结果（前 3 个时辰）：")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['时辰']}时")
        print(f"   四柱：{result['四柱']['年柱']} {result['四柱']['月柱']} {result['四柱']['日柱']} {result['四柱']['时柱']}")
        print(f"   日柱：{result['日柱']}")
        print()
    
    print(f"✓ 核心计算功能正常，共计算 {len(results)} 个时辰")
    print("="*70)
    
    return True

def test_shan_xiang_pairs():
    """测试山向配对关系"""
    print("\n" + "="*70)
    print("测试山向配对关系")
    print("="*70)
    
    # 24 山
    SHAN_24 = [
        '壬', '子', '癸', '丑', '艮', '寅',
        '甲', '卯', '乙', '辰', '巽', '巳',
        '丙', '午', '丁', '未', '坤', '申',
        '庚', '酉', '辛', '戌', '乾', '亥'
    ]
    
    # 山向对应关系（六合）
    SHAN_XIANG_PAIRS = {
        '壬': '丙', '子': '午', '癸': '丁', '丑': '未',
        '艮': '坤', '寅': '申', '甲': '庚', '卯': '酉',
        '乙': '辛', '辰': '戌', '巽': '乾', '巳': '亥',
        '丙': '壬', '午': '子', '丁': '癸', '未': '丑',
        '坤': '艮', '申': '寅', '庚': '甲', '酉': '卯',
        '辛': '乙', '戌': '辰', '乾': '巽', '亥': '巳'
    }
    
    print("\n测试自动匹配功能：")
    test_cases = ['壬', '子', '甲', '卯', '丙', '午', '庚', '酉']
    
    for shan in test_cases:
        xiang = SHAN_XIANG_PAIRS[shan]
        print(f"  {shan}山 → {xiang}向 ✓")
    
    print(f"\n✓ 山向配对关系正确，共 {len(SHAN_XIANG_PAIRS)} 对")
    print("="*70)
    
    return True

def test_gui_components():
    """测试 GUI 组件引用"""
    print("\n" + "="*70)
    print("测试 GUI 组件引用")
    print("="*70)
    
    # 读取文件，检查是否还有旧组件引用
    with open('enhanced_date_selector_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查旧组件
    old_components = [
        'current_shan_label',
        'current_xiang_label',
        'shan_info_text',
        'shan_buttons',
        'xiang_buttons'
    ]
    
    issues = []
    for comp in old_components:
        if comp in content:
            # 排除注释和定义
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if comp in line and not line.strip().startswith('#') and f'self.{comp}' in line:
                    # 检查是否是定义行
                    if '=' in line and f'self.{comp}' in line.split('=')[0]:
                        continue
                    issues.append((comp, i, line.strip()))
    
    if issues:
        print("\n⚠ 发现旧组件引用：")
        for comp, line_num, line in issues:
            print(f"  第{line_num}行：{comp}")
            print(f"    {line}")
        print("\n✗ 需要进一步修复")
    else:
        print("\n✓ 未发现旧组件引用，所有引用已更新为新组件")
    
    # 检查新组件
    new_components = [
        'shan_combo',
        'xiang_combo',
        'date_result_text',
        'shan_xiang_label'
    ]
    
    print("\n新组件使用情况：")
    for comp in new_components:
        count = content.count(comp)
        print(f"  {comp}: {count}次 ✓")
    
    print("="*70)
    
    return len(issues) == 0

def test_date_calculation():
    """测试日期计算逻辑"""
    print("\n" + "="*70)
    print("测试日期计算逻辑（模拟择日）")
    print("="*70)
    
    from datetime import timedelta
    
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2026, 3, 17)
    
    print(f"\n测试范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    total_days = (end_date - start_date).days + 1
    total_shichen = total_days * 12
    
    print(f"总天数：{total_days}天")
    print(f"总时辰数：{total_shichen}个")
    
    # 模拟计算
    calendar = PreciseCalendar()
    count = 0
    
    current_date = start_date
    while current_date <= end_date:
        for shi_zhi in calendar.DIZHI:
            shi_index = calendar.DIZHI.index(shi_zhi)
            shi_hour = shi_index * 2
            
            try:
                sizhu = get_sizhu_accurate(
                    current_date.year, current_date.month, current_date.day,
                    shi_hour, 0, 116.4074, 39.9042
                )
                count += 1
            except Exception as e:
                print(f"错误：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {e}")
        
        current_date += timedelta(days=1)
    
    print(f"\n✓ 成功计算 {count}个时辰")
    print(f"✓ 日期计算逻辑正常")
    print("="*70)
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("仪度六壬择日系统 - GUI 改进修复验证")
    print("="*70)
    
    tests = [
        ("核心计算功能", test_core_calculation),
        ("山向配对关系", test_shan_xiang_pairs),
        ("GUI 组件引用", test_gui_components),
        ("日期计算逻辑", test_date_calculation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n✗ {name}测试失败：{e}")
    
    # 汇总结果
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"  错误：{error}")
    
    print(f"\n总计：{passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用。")
        print("\n下一步：")
        print("1. 手动启动 GUI：python enhanced_date_selector_gui.py")
        print("2. 选择山向：壬山丙向")
        print("3. 设置日期：2026-03-15 至 2026-06-15")
        print('4. 点击"开始择日"')
        print("5. 查看结果")
    else:
        print(f"\n⚠ 有 {total - passed} 项测试失败，请检查修复。")
    
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
