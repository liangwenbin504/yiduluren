#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首择日第一斗首课格断语查看器

显示第一斗首课格的完整断语内容
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# 路径设置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
from douhou_kege_system import DiYiDouShouKeGe


class DouShouKeGeViewer:
    """斗首课格查看器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("斗首择日 - 第一斗首课格断语")
        self.root.geometry("1000x700")
        
        # 初始化课格系统
        self.analyzer = DiYiDouShouKeGe()
        
        # 创建界面
        self.create_ui()
        
        # 加载课格列表
        self.load_kege_list()
    
    def create_ui(self):
        """创建界面"""
        # 左侧：课格列表
        left_frame = tk.Frame(self.root, width=200, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(left_frame, text="第一斗首课格", 
                font=('微软雅黑', 14, 'bold'), bg='#f0f0f0').pack(pady=10)
        
        # 课格列表框
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.kege_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                       font=('微软雅黑', 11), selectbackground='#e0e0ff')
        self.kege_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.kege_listbox.yview)
        
        self.kege_listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # 右侧：断语详情
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 课格名称
        title_frame = tk.Frame(right_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(title_frame, text="课格：", font=('微软雅黑', 12, 'bold')).pack(side=tk.LEFT)
        self.kege_name_label = tk.Label(title_frame, text="", 
                                       font=('微软雅黑', 14, 'bold'), fg='blue')
        self.kege_name_label.pack(side=tk.LEFT, padx=10)
        
        # 课格说明
        desc_frame = tk.Frame(right_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(desc_frame, text="说明：", font=('微软雅黑', 11, 'bold')).pack(side=tk.LEFT)
        self.kege_desc_label = tk.Label(desc_frame, text="", 
                                       font=('微软雅黑', 11), wraplength=700, justify=tk.LEFT)
        self.kege_desc_label.pack(side=tk.LEFT, padx=10)
        
        # 断语标题
        tk.Label(right_frame, text="【断语】", 
                font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # 断语文本框
        self.duanyu_text = scrolledtext.ScrolledText(right_frame, height=20, 
                                                     font=('微软雅黑', 11), 
                                                     wrap=tk.WORD,
                                                     bg='#fafafa')
        self.duanyu_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 宜忌标题
        tk.Label(right_frame, text="【宜忌】", 
                font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # 宜忌文本框
        self.shiyong_text = scrolledtext.ScrolledText(right_frame, height=3, 
                                                      font=('微软雅黑', 11), 
                                                      wrap=tk.WORD,
                                                      bg='#fff8dc')
        self.shiyong_text.pack(fill=tk.X, pady=5)
        
        # 吉凶标题
        tk.Label(right_frame, text="【吉凶】", 
                font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # 吉凶文本框
        self.jixiong_text = scrolledtext.ScrolledText(right_frame, height=2, 
                                                      font=('微软雅黑', 11), 
                                                      wrap=tk.WORD,
                                                      bg='#f0fff0')
        self.jixiong_text.pack(fill=tk.X, pady=5)
        
        # 按钮
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="刷新", command=self.refresh, 
                 bg='#4CAF50', fg='white', font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="导出文本", command=self.export_text, 
                 bg='#2196F3', fg='white', font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关闭", command=self.root.quit, 
                 bg='#f44336', fg='white', font=('微软雅黑', 11)).pack(side=tk.RIGHT, padx=5)
    
    def load_kege_list(self):
        """加载课格列表"""
        self.kege_listbox.delete(0, tk.END)
        kege_names = self.analyzer.get_all_ke_ge_names()
        for name in kege_names:
            self.kege_listbox.insert(tk.END, name)
    
    def on_select(self, event):
        """选择课格"""
        selection = self.kege_listbox.curselection()
        if selection:
            index = selection[0]
            kege_name = self.kege_listbox.get(index)
            self.display_kege(kege_name)
    
    def display_kege(self, kege_name):
        """显示课格详情"""
        kege_data = self.analyzer.get_kege(kege_name)
        if kege_data:
            self.kege_name_label.config(text=kege_data['name'])
            self.kege_desc_label.config(text=kege_data['description'])
            
            # 显示断语
            self.duanyu_text.delete(1.0, tk.END)
            duanyu_list = kege_data.get('duanyu', [])
            for i, duanyu in enumerate(duanyu_list, 1):
                self.duanyu_text.insert(tk.END, f"{i}. {duanyu}\n")
            
            # 显示宜忌
            self.shiyong_text.delete(1.0, tk.END)
            self.shiyong_text.insert(tk.END, kege_data.get('shiyong', ''))
            
            # 显示吉凶
            self.jixiong_text.delete(1.0, tk.END)
            self.jixiong_text.insert(tk.END, kege_data.get('jixiong', ''))
    
    def refresh(self):
        """刷新"""
        self.load_kege_list()
        messagebox.showinfo("刷新", "课格列表已刷新")
    
    def export_text(self):
        """导出所有课格断语到文本文件"""
        output_path = "斗首择日第一斗首课格断语.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("斗首择日 - 第一斗首课格断语全集\n")
            f.write("=" * 70 + "\n\n")
            
            for kege_name in self.analyzer.get_all_ke_ge_names():
                report = self.analyzer.analyze_kege(kege_name)
                f.write(report + "\n\n")
        
        messagebox.showinfo("导出成功", f"已导出到：{output_path}")


def main():
    """主函数"""
    root = tk.Tk()
    app = DouShouKeGeViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
