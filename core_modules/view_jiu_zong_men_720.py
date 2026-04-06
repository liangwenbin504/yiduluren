#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
九宗门起课法 - 720 课例关联查看器
用于查看使用九宗门起课法计算的 720 课例（8640 课）匹配结果
"""

import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class JiuZongMenViewer:
    """九宗门课例查看器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("九宗门起课法 - 720 课例关联查看器")
        self.root.geometry("1200x800")
        
        # 加载数据
        self.load_data()
        
        # 创建界面
        self.create_interface()
    
    def load_data(self):
        """加载课例数据"""
        data_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_jiu_zong_men.json')
        
        if not os.path.exists(data_file):
            messagebox.showerror("错误", f"找不到数据文件：{data_file}")
            self.data = {}
            self.metadata = {}
            return
        
        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        
        self.metadata = full_data.get('metadata', {})
        self.ke_li = full_data.get('ke_li', {})
        
        # 统计信息
        self.stats = {
            'total': self.metadata.get('total_ke_li', 0),
            'methods': self.metadata.get('methods_distribution', {}),
            'ke_jing': self.metadata.get('ke_jing_distribution', {})
        }
    
    def create_interface(self):
        """创建界面"""
        # 标题
        title_frame = tk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(title_frame, text="九宗门起课法 - 720 课例关联查看器", 
                font=('微软雅黑', 18, 'bold')).pack()
        
        # 统计信息
        stats_frame = tk.LabelFrame(self.root, text="统计信息", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_text = f"总课例数：{self.stats['total']} | "
        stats_text += f"九宗门起法：{len(self.stats['methods'])} 种 | "
        stats_text += f"匹配课经：{len(self.stats['ke_jing'])} 个"
        
        tk.Label(stats_frame, text=stats_text, font=('微软雅黑', 11)).pack()
        
        # 主内容区
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：搜索和列表
        left_frame = tk.Frame(main_pane, width=400)
        main_pane.add(left_frame)
        
        # 搜索区
        search_frame = tk.LabelFrame(left_frame, text="搜索课例", padx=10, pady=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="日干支:").grid(row=0, column=0, sticky='e', pady=5)
        self.search_gan_zhi = ttk.Combobox(search_frame, width=10)
        self.search_gan_zhi['values'] = self._get_unique_gan_zhi()
        self.search_gan_zhi.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(search_frame, text="月建:").grid(row=0, column=2, sticky='e', pady=5)
        self.search_yue = ttk.Combobox(search_frame, width=5)
        self.search_yue['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.search_yue.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(search_frame, text="时辰:").grid(row=0, column=4, sticky='e', pady=5)
        self.search_shi = ttk.Combobox(search_frame, width=5)
        self.search_shi['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.search_shi.grid(row=0, column=5, padx=5, pady=5)
        
        tk.Button(search_frame, text="搜索", command=self.search_ke_li).grid(row=0, column=6, padx=10)
        
        # 课例列表
        list_frame = tk.LabelFrame(left_frame, text="课例列表", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建 Treeview
        columns = ('课例', '月建', '时辰', '主课经', '起法')
        self.ke_li_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.ke_li_tree.heading(col, text=col)
            self.ke_li_tree.column(col, width=80)
        
        self.ke_li_tree.pack(fill=tk.BOTH, expand=True)
        self.ke_li_tree.bind('<<TreeviewSelect>>', self.on_ke_li_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ke_li_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ke_li_tree.configure(yscrollcommand=scrollbar.set)
        
        # 右侧：详细信息
        right_frame = tk.LabelFrame(main_pane, text="详细信息", padx=10, pady=10)
        main_pane.add(right_frame)
        
        self.detail_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=60, height=40)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始加载部分课例
        self.load_sample_ke_li()
    
    def _get_unique_gan_zhi(self):
        """获取所有独特的日干支"""
        gan_zhi_set = set()
        for key in self.ke_li.keys():
            parts = key.split('_')
            if len(parts) >= 1:
                gan_zhi_set.add(parts[0])
        return sorted(list(gan_zhi_set))
    
    def load_sample_ke_li(self):
        """加载部分课例样本"""
        self.ke_li_tree.delete(*self.ke_li_tree.get_children())
        
        count = 0
        for key, value in self.ke_li.items():
            if count >= 100:  # 只显示前 100 个
                break
            
            parts = key.split('_')
            if len(parts) >= 3:
                gan_zhi, yue, shi = parts[0], parts[1], parts[2]
                zhu_ke_jing = value.get('primary_ke_jing', '')
                qi_fa = value.get('jiu_zong_men_method', '')
                
                self.ke_li_tree.insert('', 'end', values=(gan_zhi, yue, shi, zhu_ke_jing, qi_fa))
                count += 1
    
    def search_ke_li(self):
        """搜索课例"""
        gan_zhi = self.search_gan_zhi.get()
        yue = self.search_yue.get()
        shi = self.search_shi.get()
        
        self.ke_li_tree.delete(*self.ke_li_tree.get_children())
        
        count = 0
        for key, value in self.ke_li.items():
            parts = key.split('_')
            if len(parts) >= 3:
                k_gan_zhi, k_yue, k_shi = parts[0], parts[1], parts[2]
                
                # 匹配条件
                if gan_zhi and k_gan_zhi != gan_zhi:
                    continue
                if yue and k_yue != yue:
                    continue
                if shi and k_shi != shi:
                    continue
                
                zhu_ke_jing = value.get('primary_ke_jing', '')
                qi_fa = value.get('jiu_zong_men_method', '')
                
                self.ke_li_tree.insert('', 'end', values=(k_gan_zhi, k_yue, k_shi, zhu_ke_jing, qi_fa))
                count += 1
        
        messagebox.showinfo("搜索结果", f"找到 {count} 个课例")
    
    def on_ke_li_select(self, event):
        """选择课例时显示详细信息"""
        selection = self.ke_li_tree.selection()
        if not selection:
            return
        
        item = self.ke_li_tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 3:
            gan_zhi, yue, shi = values[0], values[1], values[2]
            key = f"{gan_zhi}_{yue}_{shi}"
            
            if key in self.ke_li:
                self.show_detail(key, self.ke_li[key])
    
    def show_detail(self, key: str, value: dict):
        """显示课例详细信息"""
        self.detail_text.delete(1.0, tk.END)
        
        text = "=" * 60 + "\n"
        text += "课例详细信息\n"
        text += "=" * 60 + "\n\n"
        
        text += f"【基本信息】\n"
        text += f"课例键：{key}\n"
        text += f"日干支：{value.get('ri_gan_zhi', '')}\n"
        text += f"月建：{value.get('yue', '')}\n"
        text += f"时辰：{value.get('shi', '')}\n"
        text += f"月将：{value.get('yue_jiang', '')}\n\n"
        
        text += f"【九宗门起法】\n"
        text += f"{value.get('jiu_zong_men_method', '')}\n\n"
        
        text += f"【匹配课经】\n"
        matched = value.get('matched_ke_jing', [])
        if matched:
            for ke_jing in matched:
                text += f"  • {ke_jing}\n"
        else:
            text += "  无匹配课经\n"
        text += "\n"
        
        text += f"【主课经】\n"
        text += f"{value.get('primary_ke_jing', '')}\n\n"
        
        text += f"【课体列表】\n"
        ke_ti_list = value.get('ke_ti_list', [])
        if ke_ti_list:
            for ke_ti in ke_ti_list:
                text += f"  • {ke_ti}\n"
        else:
            text += "  无课体\n"
        text += "\n"
        
        # 显示四课（如果有）
        if 'sike' in value:
            text += f"【四课】\n"
            sike = value['sike']
            for i, (ke_name, shang, xia, tian_jiang) in enumerate(sike, 1):
                text += f"  {ke_name}：上{shang} 下{xia}"
                if tian_jiang:
                    text += f" ({tian_jiang})"
                text += "\n"
            text += "\n"
        
        # 显示三传（如果有）
        if 'sanchuan' in value:
            text += f"【三传】\n"
            sanchuan = value['sanchuan']
            if '三传' in sanchuan:
                san_chuan_list = sanchuan['三传']
                for i, chuan in enumerate(san_chuan_list):
                    chuan_name = ['初传', '中传', '末传'][i]
                    text += f"  {chuan_name}: {chuan}\n"
            text += "\n"
        
        text += "=" * 60
        
        self.detail_text.insert(tk.END, text)


def main():
    """主函数"""
    root = tk.Tk()
    app = JiuZongMenViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
