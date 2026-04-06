#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动宗门九课起课法模块
"""
import subprocess
import sys
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
gui_script = os.path.join(current_dir, "src", "ui", "qike_verification_gui.py")

print("=" * 50)
print("正在启动大六壬起课方法验证系统...")
print("=" * 50)
print(f"脚本路径：{gui_script}")
print()

try:
    # 使用 subprocess 启动 GUI
    subprocess.Popen([sys.executable, gui_script], 
                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    print("✓ GUI 启动命令已发送！")
    print()
    print("如果窗口没有自动弹出，请检查：")
    print("1. Python 是否正确安装")
    print("2. tkinter 模块是否可用")
    print("3. 是否有错误提示窗口")
except Exception as e:
    print(f"✗ 启动失败：{e}")
    input("按回车键退出...")
