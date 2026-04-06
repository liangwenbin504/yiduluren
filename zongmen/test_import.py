#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试导入是否成功
"""

import sys
import os

# 添加路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, 'src'))
sys.path.insert(0, os.path.join(script_dir, 'src', 'engine'))

print("Python 路径:")
for path in sys.path:
    print(f"  - {path}")
print()

try:
    print("正在导入 sike_sanchuan_engine...")
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print("[OK] sike_sanchuan_engine 导入成功!")
    
    print("\n正在导入 utils.dizhi_layout_generator...")
    from utils.dizhi_layout_generator import arrange_tiandi_pan
    print("[OK] utils.dizhi_layout_generator 导入成功!")
    
    print("\n正在创建计算器实例...")
    calc = SiKeSanChuanCalculator()
    print("[OK] 计算器创建成功!")
    
    print("\n正在测试天地盘计算...")
    tiandi_pan = calc.get_tiandi_pan('子', '子')
    print(f"[OK] 天地盘计算成功！")
    print(f"   月将：子，时辰：子")
    print(f"   天盘子位：{tiandi_pan.get('子', 'N/A')}")
    
    print("\n正在测试四课计算...")
    sike = calc.qi_sike('甲', '子', tiandi_pan)
    print(f"[OK] 四课计算成功!")
    for ke in sike:
        print(f"   {ke[0]}: 上{ke[1]} 下{ke[2]}")
    
    print("\n正在测试三传计算...")
    sanchuan = calc.fa_sanchuan(sike, '甲', '子', tiandi_pan)
    print(f"[OK] 三传计算成功!")
    print(f"   起法：{sanchuan.get('起法', 'N/A')}")
    print(f"   课体：{sanchuan.get('课体', 'N/A')}")
    print(f"   三传：{sanchuan.get('三传', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("[OK] 所有测试通过！模块工作正常！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[FAIL] 测试失败!")
    print(f"错误：{e}")
    import traceback
    traceback.print_exc()
