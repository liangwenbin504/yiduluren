#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("测试窗口")
root.geometry("400x300")

label = tk.Label(root, text="如果你看到这个窗口，说明 tkinter 正常工作！", font=('微软雅黑', 14))
label.pack(pady=50)

button = tk.Button(root, text="关闭", command=root.quit)
button.pack()

root.mainloop()
