#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试四柱文字竖排显示
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class TestVerticalTextApp:
    """测试竖排文字显示的应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("测试四柱文字竖排")
        self.root.geometry("600x300")
        
        # 创建四柱显示区域
        sizhu_frame = ttk.LabelFrame(root, text="四柱信息（年月日时）", padding=10)
        sizhu_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 四柱标签
        columns = ('年柱', '月柱', '日柱', '时柱')
        self.sizhu_labels = {}
        for i, col in enumerate(columns):
            frame = ttk.Frame(sizhu_frame)
            frame.grid(row=0, column=i, padx=20, pady=5)
            
            ttk.Label(frame, text=col, font=('微软雅黑', 10, 'bold')).pack()
            label = ttk.Label(frame, text="--", font=('微软雅黑', 14), foreground='red')
            label.pack()
            self.sizhu_labels[col] = label
        
        # 测试按钮
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="测试竖排显示", command=self.test_vertical_text).pack(padx=10)
        ttk.Button(btn_frame, text="测试横排显示", command=self.test_horizontal_text).pack(padx=10)
    
    def test_vertical_text(self):
        """测试竖排文字"""
        # 测试数据
        sizhu = {
            '年柱': '丙午',
            '月柱': '己亥',
            '日柱': '己亥',
            '时柱': '甲子'
        }
        
        # 竖排显示
        for col, ganzhi in sizhu.items():
            vertical_text = '\n'.join(ganzhi)
            self.sizhu_labels[col].config(text=vertical_text)
    
    def test_horizontal_text(self):
        """测试横排文字"""
        # 测试数据
        sizhu = {
            '年柱': '丙午',
            '月柱': '己亥',
            '日柱': '己亥',
            '时柱': '甲子'
        }
        
        # 横排显示
        for col, ganzhi in sizhu.items():
            self.sizhu_labels[col].config(text=ganzhi)


def main():
    """主函数"""
    root = tk.Tk()
    app = TestVerticalTextApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
