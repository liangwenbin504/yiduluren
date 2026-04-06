#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动主程序的包装器，捕获所有错误
"""

import sys
import traceback

try:
    print("正在导入主程序...")
    from 天地盘 import EnhancedDateSelectorGUI
    print("导入成功！")
    
    print("正在创建主窗口...")
    import tkinter as tk
    root = tk.Tk()
    app = EnhancedDateSelectorGUI(root)
    print("主窗口创建成功！")
    
    print("启动主循环...")
    root.mainloop()
    print("程序正常退出")
    
except Exception as e:
    print(f"\n❌ 错误：{e}")
    print("\n详细错误信息：")
    traceback.print_exc()
    input("\n按回车键退出...")
