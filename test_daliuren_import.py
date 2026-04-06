#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试大六壬模块导入
"""

import sys
import os

# 添加路径
core_modules_path = os.path.join(os.path.dirname(__file__), 'core_modules', 'engine')
print(f"添加路径：{core_modules_path}")
sys.path.insert(0, core_modules_path)

print("\n尝试导入模块...")

try:
    print("1. 导入 sike_sanchuan_engine...")
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print("   ✅ 成功！")
    
    print("2. 导入 gui_ren_engine...")
    from gui_ren_engine import GuiRenCalculator
    print("   ✅ 成功！")
    
    print("3. 导入 dizhi_layout_generator...")
    from dizhi_layout_generator import arrange_tiandi_pan
    print("   ✅ 成功！")
    
    print("\n✅ 所有模块导入成功！")
    
    # 测试功能
    print("\n测试功能...")
    tiandi_pan = arrange_tiandi_pan('亥', '寅')
    print(f"天地盘：{len(tiandi_pan)} 个")
    
    calc = SiKeSanChuanCalculator()
    sike = calc.qi_sike('甲', '子', tiandi_pan)
    print(f"四课：{len(sike)} 个")
    
    print("\n✅ 功能测试成功！")
    
except Exception as e:
    import traceback
    print(f"\n❌ 导入失败：{e}")
    print(f"\n详细错误:\n{traceback.format_exc()}")
