#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试程序启动
"""

import tkinter as tk
from tkinter import ttk, messagebox

def test_startup():
    """测试基本启动"""
    print("正在启动测试程序...")
    
    root = tk.Tk()
    root.title("测试窗口")
    root.geometry("400x300")
    
    label = ttk.Label(root, text="程序启动成功！", font=('Arial', 16))
    label.pack(pady=50)
    
    btn = ttk.Button(root, text="关闭", command=root.destroy)
    btn.pack()
    
    print("测试窗口已打开")
    root.mainloop()
    print("测试程序已关闭")

if __name__ == '__main__':
    test_startup()
