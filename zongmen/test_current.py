#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试当前代码
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'engine'))

from sike_sanchuan_engine import SiKeSanChuanCalculator
import inspect

# 检查 qi_sike 函数签名
sig = inspect.signature(SiKeSanChuanCalculator.qi_sike)
print(f"qi_sike 签名：{sig}")
print(f"参数数量：{len(sig.parameters)}")

# 创建实例并测试
calc = SiKeSanChuanCalculator()

# 测试甲子日 子将子时
tiandi_pan = calc.get_tiandi_pan('子', '子')
print(f"\n天地盘：子 -> {tiandi_pan.get('子', 'N/A')}")

# 尝试调用 qi_sike
try:
    sike = calc.qi_sike('甲', '子', tiandi_pan)
    print(f"\n四课（4 参数）: 成功")
    for ke in sike:
        print(f"  {ke}")
except Exception as e:
    print(f"\n四课（4 参数）: 失败 - {e}")

# 尝试带 shi_chen 参数
try:
    sike = calc.qi_sike('甲', '子', tiandi_pan, '子')
    print(f"\n四课（5 参数）: 成功")
    for ke in sike:
        print(f"  {ke}")
except Exception as e:
    print(f"\n四课（5 参数）: 失败 - {e}")
