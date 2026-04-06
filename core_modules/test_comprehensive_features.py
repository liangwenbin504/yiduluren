#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合功能测试脚本
测试三传显示和综合评价功能
"""

import sys
import os

# 添加所有需要的路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(project_root, 'src', 'engine'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from daliuren_engine import DaLiuRenEngine
from yiduluren_paipan import YiDuLiuRenPaiPan
from comprehensive_evaluation import ComprehensiveEvaluation
from ganzhi_calendar import get_sizhu_accurate


def test_san_chuan():
    """测试三传功能"""
    print("=" * 80)
    print("【测试三传功能】")
    print("=" * 80)
    
    # 测试日期：2026-03-20 23:00
    year, month, day, hour = 2026, 3, 20, 23
    sizhu = get_sizhu_accurate(year, month, day, hour)
    
    print(f"测试日期：{year}-{month:02d}-{day:02d} {hour:02d}:00")
    print(f"四柱：{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}")
    print()
    
    # 获取日干日支
    ri_gan = sizhu['日柱'][0]
    ri_zhi = sizhu['日柱'][1]
    shi_zhi = sizhu['时柱'][1]
    
    print(f"日干：{ri_gan}, 日支：{ri_zhi}, 时支：{shi_zhi}")
    print()
    
    # 排天盘
    paipan = YiDuLiuRenPaiPan()
    lunar_month = (month % 12) + 1
    yuejiang = paipan.get_yuejiang_by_month(lunar_month)
    tian_pan = paipan.arrange_tian_pan(yuejiang, shi_zhi)
    
    print(f"月将：{yuejiang}")
    print(f"天盘：{tian_pan}")
    print()
    
    # 排四课
    daliuren = DaLiuRenEngine()
    si_ke = daliuren.arrange_si_ke(ri_gan, ri_zhi, tian_pan)
    
    print("【四课】")
    for i, ke in enumerate(si_ke, 1):
        print(f"  第{i}课：{ke.get('top', '-')}（上） / {ke.get('bottom', '-')}（下）")
    print()
    
    # 发三传
    san_chuan_result = daliuren.fa_san_chuan(si_ke, ri_gan)
    
    print("【三传】")
    if san_chuan_result and san_chuan_result.get('三传'):
        san_chuan = san_chuan_result['三传']
        print(f"  初传：{san_chuan[0] if len(san_chuan) > 0 else '--'}")
        print(f"  中传：{san_chuan[1] if len(san_chuan) > 1 else '--'}")
        print(f"  末传：{san_chuan[2] if len(san_chuan) > 2 else '--'}")
        print(f"  课体：{san_chuan_result.get('课体', '--')}")
        print(f"  起法：{san_chuan_result.get('起法', '--')}")
    else:
        print("  三传未计算成功")
    print()
    
    return san_chuan_result


def test_comprehensive_evaluation():
    """测试综合评价功能"""
    print("=" * 80)
    print("【测试综合评价功能】")
    print("=" * 80)
    
    # 测试日期：2026-03-20 23:00
    year, month, day, hour = 2026, 3, 20, 23
    shan_name = "子山"
    kejing_name = "龙德"
    
    print(f"测试日期：{year}-{month:02d}-{day:02d} {hour:02d}:00")
    print(f"坐山：{shan_name}")
    print(f"课格：{kejing_name}")
    print()
    
    # 调用综合评价
    evaluator = ComprehensiveEvaluation()
    eval_result = evaluator.evaluate_date(year, month, day, hour, shan_name, kejing_name)
    
    print("【综合评价结果】")
    print(f"日期：{eval_result.get('日期', '--')}")
    print(f"四柱：{eval_result.get('四柱', {})}")
    print(f"综合评分：{eval_result.get('综合评分', 0)}分")
    print(f"吉凶等级：{eval_result.get('吉凶等级', '--')}")
    print()
    
    print("【综合评语】")
    print(eval_result.get('综合评语', ''))
    print()
    
    print("【宜忌】")
    yiji = eval_result.get('宜忌', {})
    print(f"宜：{','.join(yiji.get('宜', []))}")
    print(f"忌：{','.join(yiji.get('忌', []))}")
    print()
    
    return eval_result


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "仪度六壬综合功能测试" + " " * 33 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    # 测试三传
    san_chuan = test_san_chuan()
    
    # 测试综合评价
    eval_result = test_comprehensive_evaluation()
    
    print("=" * 80)
    print("【测试完成】")
    print("=" * 80)
    print()
    print("✓ 三传功能测试：", "成功" if san_chuan and san_chuan.get('三传') else "失败")
    print("✓ 综合评价功能测试：", "成功" if eval_result and eval_result.get('综合评分') else "失败")
    print()
    print("提示：GUI 界面已集成以上功能，可启动 comprehensive_gui.py 进行可视化测试")
    print()


if __name__ == '__main__':
    main()
