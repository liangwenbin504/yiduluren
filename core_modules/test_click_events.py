#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试双击和右键功能
"""

import tkinter as tk
from tkinter import ttk, messagebox

def test_click_events():
    """测试点击事件"""
    root = tk.Tk()
    root.title("点击事件测试")
    root.geometry("600x400")
    
    # 创建 Treeview
    tree_frame = ttk.Frame(root, padding="10")
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    tree = ttk.Treeview(tree_frame, columns=('日期', '四柱'), show='tree')
    tree.pack(fill=tk.BOTH, expand=True)
    
    # 添加测试数据
    tree.insert('', 'end', iid='item1', text='1', values=('2026-03-23', '丙午 辛卯 丙申 戊子'))
    tree.insert('', 'end', iid='item2', text='2', values=('2026-03-24', '丙午 辛卯 丙申 己丑'))
    tree.insert('', 'end', iid='item3', text='3', values=('2026-03-25', '丙午 辛卯 丙申 庚寅'))
    
    # 绑定双击事件
    def on_double_click(event):
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            date = item['values'][0]
            print(f"双击：{date}")
            messagebox.showinfo("双击测试", f"双击了：{date}")
    
    tree.bind('<Double-1>', on_double_click)
    
    # 绑定选择事件
    def on_select(event):
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            date = item['values'][0]
            print(f"选中：{date}")
    
    tree.bind('<<TreeviewSelect>>', on_select)
    
    # 创建右键菜单
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="查看排盘", command=lambda: messagebox.showinfo("菜单", "查看排盘"))
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind('<Button-3>', show_context_menu)
    
    # 提示标签
    tip_label = ttk.Label(root, text="💡 双击日期或右键点击", foreground='blue')
    tip_label.pack(pady=5)
    
    print("测试程序已启动")
    print("请尝试：")
    print("1. 双击列表中的日期")
    print("2. 右键点击日期")
    print("3. 单击选中日期")
    
    root.mainloop()

if __name__ == '__main__':
    test_click_events()
