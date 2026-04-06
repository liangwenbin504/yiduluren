#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经完整查看器

功能：
1. 查看所有 64 课经的完整信息
2. 查询每个课经匹配的课例
3. 显示课经断语和评分
4. 支持搜索和过滤
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os


class ComprehensiveKeJingViewer:
    """综合课经查看器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬 64 课经完整查看器")
        self.root.geometry("1400x900")
        
        # 数据
        self.ke_jing_data = {}
        self.ke_li_data = {}
        
        # 加载数据
        self.load_data()
        
        # 创建界面
        self.create_ui()
        
        # 加载列表
        self.load_ke_jing_list()
    
    def load_data(self):
        """加载数据"""
        # 加载课经数据
        ke_jing_file = "data/64_ke_jing_accurate.json"
        if os.path.exists(ke_jing_file):
            with open(ke_jing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ke_jing_data = data.get('courses', {})
                print(f"已加载 {len(self.ke_jing_data)} 条课经")
        
        # 加载课例数据
        ke_li_file = "data/720_ke_li.json"
        if os.path.exists(ke_li_file):
            with open(ke_li_file, 'r', encoding='utf-8') as f:
                self.ke_li_data = json.load(f)
                print(f"已加载 {len(self.ke_li_data)} 个课例")
    
    def create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：课经列表和搜索
        left_frame = tk.Frame(main_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        # 标题
        tk.Label(left_frame, text="64 课经列表", font=('微软雅黑', 16, 'bold')).pack(pady=10)
        
        # 搜索框
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(search_frame, text="搜索:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, font=('微软雅黑', 11), width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(search_frame, text="搜索", command=self.search_ke_jing, 
                 font=('微软雅黑', 11), bg='blue', fg='white').pack(side=tk.LEFT)
        tk.Button(search_frame, text="重置", command=self.reset_search, 
                 font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=2)
        
        # 课经列表
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ke_jing_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                         font=('微软雅黑', 11), width=30)
        self.ke_jing_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.ke_jing_listbox.yview)
        
        self.ke_jing_listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # 统计信息
        stats_frame = tk.LabelFrame(left_frame, text="统计信息", font=('微软雅黑', 12, 'bold'))
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.stats_label = tk.Label(stats_frame, text="", font=('微软雅黑', 10), justify=tk.LEFT)
        self.stats_label.pack(padx=5, pady=5)
        
        # 右侧：课经详情
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 课名和类型
        title_frame = tk.Frame(right_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(title_frame, text="课名：", font=('微软雅黑', 12, 'bold')).pack(side=tk.LEFT)
        self.ke_name_label = tk.Label(title_frame, text="", font=('微软雅黑', 14, 'bold'), fg='blue')
        self.ke_name_label.pack(side=tk.LEFT, padx=10)
        
        self.ke_type_label = tk.Label(title_frame, text="", font=('微软雅黑', 12), fg='green')
        self.ke_type_label.pack(side=tk.RIGHT, padx=10)
        
        # 评分和等级
        score_frame = tk.Frame(right_frame)
        score_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(score_frame, text="评分：", font=('微软雅黑', 12)).pack(side=tk.LEFT)
        self.score_label = tk.Label(score_frame, text="", font=('微软雅黑', 12, 'bold'), fg='red')
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        tk.Label(score_frame, text="等级：", font=('微软雅黑', 12)).pack(side=tk.LEFT)
        self.level_label = tk.Label(score_frame, text="", font=('微软雅黑', 12, 'bold'), fg='orange')
        self.level_label.pack(side=tk.LEFT, padx=10)
        
        # 定义
        def_frame = tk.LabelFrame(right_frame, text="定义", font=('微软雅黑', 12, 'bold'))
        def_frame.pack(fill=tk.X, pady=5)
        
        self.definition_label = tk.Label(def_frame, text="", font=('微软雅黑', 11), 
                                        wraplength=800, justify=tk.LEFT)
        self.definition_label.pack(padx=10, pady=5)
        
        # 课经原文
        desc_frame = tk.LabelFrame(right_frame, text="课经原文", font=('微软雅黑', 12, 'bold'))
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.description_text = scrolledtext.ScrolledText(desc_frame, height=10, 
                                                         font=('微软雅黑', 11), wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 断语
        judgment_frame = tk.LabelFrame(right_frame, text="断语", font=('微软雅黑', 12, 'bold'))
        judgment_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.judgment_text = scrolledtext.ScrolledText(judgment_frame, height=8, 
                                                      font=('微软雅黑', 11), wrap=tk.WORD)
        self.judgment_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 匹配课例
        ke_li_frame = tk.LabelFrame(right_frame, text="匹配课例", font=('微软雅黑', 12, 'bold'))
        ke_li_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 课例列表
        ke_li_scroll = tk.Scrollbar(ke_li_frame)
        ke_li_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ke_li_listbox = tk.Listbox(ke_li_frame, yscrollcommand=ke_li_scroll.set, 
                                       font=('微软雅黑', 10), width=50)
        self.ke_li_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ke_li_scroll.config(command=self.ke_li_listbox.yview)
        
        # 按钮
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="刷新列表", command=self.load_ke_jing_list, 
                 font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="导出报告", command=self.export_report, 
                 font=('微软雅黑', 11), bg='green', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关闭", command=self.root.quit, 
                 font=('微软雅黑', 11), bg='gray', fg='white').pack(side=tk.RIGHT, padx=5)
    
    def load_ke_jing_list(self):
        """加载课经列表"""
        self.ke_jing_listbox.delete(0, tk.END)
        
        for ke_id in sorted(self.ke_jing_data.keys(), key=int):
            ke_data = self.ke_jing_data[ke_id]
            ke_name = ke_data.get('ke_name', '')
            ke_type = ke_data.get('ke_type', '')
            level = ke_data.get('level', '')
            self.ke_jing_listbox.insert(tk.END, f"{ke_name} ({ke_type}) - {level}")
        
        # 更新统计
        self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        total_ke_jing = len(self.ke_jing_data)
        total_ke_li = len(self.ke_li_data)
        
        # 计算每个课经的匹配数
        ke_jing_count = {}
        for ke_data in self.ke_li_data.values():
            for ke_name in ke_data.get('matched_ke_jing', []):
                ke_jing_count[ke_name] = ke_jing_count.get(ke_name, 0) + 1
        
        stats_text = f"课经总数：{total_ke_jing}\n"
        stats_text += f"课例总数：{total_ke_li}\n"
        stats_text += f"\n匹配最多的课经:\n"
        
        sorted_counts = sorted(ke_jing_count.items(), key=lambda x: x[1], reverse=True)
        for ke_name, count in sorted_counts[:5]:
            stats_text += f"  {ke_name}: {count} 课\n"
        
        self.stats_label.config(text=stats_text)
    
    def on_select(self, event):
        """选择课经"""
        selection = self.ke_jing_listbox.curselection()
        if selection:
            index = selection[0]
            ke_jing_str = self.ke_jing_listbox.get(index)
            ke_name = ke_jing_str.split(' ')[0]
            self.display_ke_jing(ke_name)
    
    def display_ke_jing(self, ke_name):
        """显示课经详情"""
        # 查找课经数据
        ke_data = None
        for ke_id, data in self.ke_jing_data.items():
            if data.get('ke_name') == ke_name:
                ke_data = data
                break
        
        if not ke_data:
            return
        
        # 显示基本信息
        self.ke_name_label.config(text=ke_data.get('ke_name', ''))
        self.ke_type_label.config(text=ke_data.get('ke_type', ''))
        self.score_label.config(text=f"{ke_data.get('score', 0)} 分")
        self.level_label.config(text=ke_data.get('level', ''))
        self.definition_label.config(text=ke_data.get('definition', ''))
        
        # 显示课经原文
        self.description_text.delete(1.0, tk.END)
        duanyu = ke_data.get('duanyu', [])
        if duanyu:
            for i, line in enumerate(duanyu, 1):
                self.description_text.insert(tk.END, f"{i}. {line}\n")
        
        # 显示断语
        self.judgment_text.delete(1.0, tk.END)
        summary = ke_data.get('summary', '')
        if summary:
            self.judgment_text.insert(tk.END, f"总断：{summary}\n\n")
        
        # 显示匹配课例
        self.ke_li_listbox.delete(0, tk.END)
        matched_count = 0
        for ke_key, ke_data_item in self.ke_li_data.items():
            if ke_name in ke_data_item.get('matched_ke_jing', []):
                if matched_count < 100:  # 只显示前 100 个
                    text = f"{ke_key} - {ke_data_item['ri_gan_zhi']}年{ke_data_item['yue']}月{ke_data_item['shi']}时"
                    self.ke_li_listbox.insert(tk.END, text)
                matched_count += 1
        
        # 在断语中显示总数
        self.judgment_text.insert(tk.END, f"\n\n匹配课例数：{matched_count} 个")
    
    def search_ke_jing(self):
        """搜索课经"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        
        self.ke_jing_listbox.delete(0, tk.END)
        count = 0
        
        for ke_id in sorted(self.ke_jing_data.keys(), key=int):
            ke_data = self.ke_jing_data[ke_id]
            ke_name = ke_data.get('ke_name', '')
            ke_type = ke_data.get('ke_type', '')
            level = ke_data.get('level', '')
            
            # 搜索课名、类型、断语
            if (keyword in ke_name or keyword in ke_type or 
                keyword in level or keyword in ke_data.get('summary', '')):
                self.ke_jing_listbox.insert(tk.END, f"{ke_name} ({ke_type}) - {level}")
                count += 1
        
        messagebox.showinfo("搜索结果", f"找到 {count} 条相关课经")
    
    def reset_search(self):
        """重置搜索"""
        self.search_entry.delete(0, tk.END)
        self.load_ke_jing_list()
    
    def export_report(self):
        """导出报告"""
        report_file = "docs/64 课经完整匹配报告.md"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 大六壬 64 课经完整匹配报告\n\n")
            f.write(f"生成时间：{os.path.basename(report_file)}\n\n")
            f.write(f"## 统计信息\n\n")
            f.write(f"- 课经总数：{len(self.ke_jing_data)}\n")
            f.write(f"- 课例总数：{len(self.ke_li_data)}\n\n")
            
            f.write("## 64 课经完整列表\n\n")
            
            for ke_id in sorted(self.ke_jing_data.keys(), key=int):
                ke_data = self.ke_jing_data[ke_id]
                ke_name = ke_data.get('ke_name', '')
                
                f.write(f"### {ke_name}\n\n")
                f.write(f"**类型**: {ke_data.get('ke_type', '')}\n\n")
                f.write(f"**评分**: {ke_data.get('score', 0)} 分 ({ke_data.get('level', '')})\n\n")
                f.write(f"**定义**: {ke_data.get('definition', '')}\n\n")
                
                f.write(f"**断语**:\n")
                for line in ke_data.get('duanyu', []):
                    f.write(f"- {line}\n")
                f.write("\n")
                
                f.write(f"**总断**: {ke_data.get('summary', '')}\n\n")
                
                # 统计匹配课例
                count = sum(1 for ke_data_item in self.ke_li_data.values() 
                          if ke_name in ke_data_item.get('matched_ke_jing', []))
                f.write(f"**匹配课例数**: {count} 个\n\n")
                f.write("---\n\n")
        
        messagebox.showinfo("导出成功", f"报告已导出到:\n{report_file}")


def main():
    root = tk.Tk()
    app = ComprehensiveKeJingViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
