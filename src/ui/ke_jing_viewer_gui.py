#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经查看器
用于查看和编辑课经数据
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# 路径设置
script_path = os.path.abspath(__file__)
engine_dir = os.path.dirname(script_path).replace('\\ui\\', '\\engine\\')
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from ke_jing_engine import LiuShiSiKeEngine


class KeJingViewerGUI:
    """课经查看器 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬 64 课经查看器")
        self.root.geometry("1200x800")
        
        # 初始化引擎
        self.engine = LiuShiSiKeEngine()
        
        # 创建界面
        self.create_ui()
        
        # 加载课经列表
        self.load_ke_jing_list()
    
    def create_ui(self):
        """创建界面"""
        # 左侧：课经列表
        left_frame = tk.Frame(self.root, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(left_frame, text="64 课经列表", font=('微软雅黑', 14, 'bold')).pack(pady=5)
        
        # 课经列表框
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ke_jing_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('微软雅黑', 11))
        self.ke_jing_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.ke_jing_listbox.yview)
        
        self.ke_jing_listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # 右侧：课经详情
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 课名
        title_frame = tk.Frame(right_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(title_frame, text="课名：", font=('微软雅黑', 12, 'bold')).pack(side=tk.LEFT)
        self.ke_name_label = tk.Label(title_frame, text="", font=('微软雅黑', 14, 'bold'), fg='blue')
        self.ke_name_label.pack(side=tk.LEFT, padx=10)
        
        # 课体
        type_frame = tk.Frame(right_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(type_frame, text="课体：", font=('微软雅黑', 12)).pack(side=tk.LEFT)
        self.ke_type_label = tk.Label(type_frame, text="", font=('微软雅黑', 12))
        self.ke_type_label.pack(side=tk.LEFT, padx=10)
        
        # 课经原文
        tk.Label(right_frame, text="课经原文:", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=5)
        self.description_text = scrolledtext.ScrolledText(right_frame, height=15, font=('微软雅黑', 11), wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 断语
        tk.Label(right_frame, text="断语:", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=5)
        self.judgment_text = scrolledtext.ScrolledText(right_frame, height=8, font=('微软雅黑', 11), wrap=tk.WORD)
        self.judgment_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 按钮
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="导入 PDF", command=self.import_pdf, bg='green', fg='white', font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="编辑课经", command=self.edit_ke_jing, bg='blue', fg='white', font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="保存修改", command=self.save_ke_jing, bg='orange', fg='white', font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关闭", command=self.root.quit, bg='gray', fg='white', font=('微软雅黑', 11)).pack(side=tk.RIGHT, padx=5)
    
    def load_ke_jing_list(self):
        """加载课经列表"""
        self.ke_jing_listbox.delete(0, tk.END)
        ke_jing_list = self.engine.get_all_ke_jing_list()
        for ke_name in ke_jing_list:
            self.ke_jing_listbox.insert(tk.END, ke_name)
    
    def on_select(self, event):
        """选择课经"""
        selection = self.ke_jing_listbox.curselection()
        if selection:
            index = selection[0]
            ke_name = self.ke_jing_listbox.get(index)
            self.display_ke_jing(ke_name)
    
    def display_ke_jing(self, ke_name):
        """显示课经详情"""
        ke_data = self.engine.get_ke_jing_detail(ke_name)
        if ke_data:
            self.ke_name_label.config(text=ke_data.get('ke_name', ''))
            self.ke_type_label.config(text=ke_data.get('ke_type', ''))
            
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(tk.END, ke_data.get('description', ''))
            
            self.judgment_text.delete(1.0, tk.END)
            self.judgment_text.insert(tk.END, ke_data.get('judgment', ''))
    
    def import_pdf(self):
        """导入 PDF"""
        messagebox.showinfo("提示", "PDF 导入功能开发中...\n将自动从《白话大六壬全书》提取 64 课经")
    
    def edit_ke_jing(self):
        """编辑课经"""
        messagebox.showinfo("提示", "编辑功能开发中...")
    
    def save_ke_jing(self):
        """保存课经"""
        ke_name = self.ke_name_label.cget("text")
        if ke_name:
            ke_data = self.engine.get_ke_jing_detail(ke_name)
            if ke_data:
                ke_data['description'] = self.description_text.get(1.0, tk.END).strip()
                ke_data['judgment'] = self.judgment_text.get(1.0, tk.END).strip()
                self.engine.save_data()
                messagebox.showinfo("成功", f"已保存课经：{ke_name}")


def main():
    root = tk.Tk()
    app = KeJingViewerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
