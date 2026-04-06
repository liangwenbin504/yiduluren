#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课到山到向择日 GUI 界面
提供用户友好的龙德课择日功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from long_de_ke_selector import LongDeKeSelector
from daliuren_engine import DaLiuRenEngine
from ganzhi_calendar import get_sizhu_accurate


class LongDeKeGUI(ttk.Frame):
    """龙德课到山到向择日 GUI"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.selector = LongDeKeSelector()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="龙德课到山到向择日系统", 
                 font=('微软雅黑', 18, 'bold')).pack()
        ttk.Label(title_frame, text="太岁/月将乘贵人发用 + 禄马贵到山到向", 
                 font=('微软雅黑', 10)).pack()
        
        # 左侧参数区，右侧结果区
        content_frame = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧参数区
        left_frame = ttk.LabelFrame(content_frame, text="择日参数", padding=10)
        content_frame.add(left_frame, weight=1)
        
        self._setup_input_frame(left_frame)
        
        # 右侧结果区
        right_frame = ttk.LabelFrame(content_frame, text="择日结果", padding=10)
        content_frame.add(right_frame, weight=2)
        
        self._setup_result_frame(right_frame)
    
    def _setup_input_frame(self, parent):
        """设置输入参数区"""
        # 坐山选择
        shan_frame = ttk.LabelFrame(parent, text="坐山朝向", padding=10)
        shan_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(shan_frame, text="坐山:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.shan_var = tk.StringVar(value='壬')
        shan_combo = ttk.Combobox(shan_frame, textvariable=self.shan_var, 
                                 width=15, state='readonly')
        shan_combo['values'] = self._get_shan_list()
        shan_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(shan_frame, text="朝向:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.direction_var = tk.StringVar(value='丙')
        direction_combo = ttk.Combobox(shan_frame, textvariable=self.direction_var, 
                                      width=15, state='readonly')
        direction_combo['values'] = self._get_direction_list()
        direction_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # 日期范围
        date_frame = ttk.LabelFrame(parent, text="日期范围", padding=10)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar(value='2026-03-15')
        start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=15)
        start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=0, column=2, padx=5)
        
        ttk.Label(date_frame, text="结束日期:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar(value='2027-03-14')
        end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=15)
        end_date_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=1, column=2, padx=5)
        
        # 筛选条件
        filter_frame = ttk.LabelFrame(parent, text="筛选条件", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="最少到山到向:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.min_arrival_var = tk.IntVar(value=3)
        arrival_spin = ttk.Spinbox(filter_frame, from_=1, to=10, width=10, 
                                   textvariable=self.min_arrival_var)
        arrival_spin.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(filter_frame, text="个").grid(row=0, column=2, padx=5)
        
        ttk.Label(filter_frame, text="龙德课类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.long_de_type_var = tk.StringVar(value='全部')
        type_combo = ttk.Combobox(filter_frame, textvariable=self.long_de_type_var, 
                                 width=15, state='readonly')
        type_combo['values'] = ['全部', '太岁龙德课', '月将龙德课']
        type_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.select_btn = ttk.Button(button_frame, text="开始择日", command=self.start_selection, 
                                    width=15)
        self.select_btn.pack(pady=5)
        
        self.export_btn = ttk.Button(button_frame, text="导出结果", command=self.export_results, 
                                    width=15, state=tk.DISABLED)
        self.export_btn.pack(pady=5)
        
        self.clear_btn = ttk.Button(button_frame, text="清空结果", command=self.clear_results, 
                                   width=15)
        self.clear_btn.pack(pady=5)
        
        # 进度显示
        progress_frame = ttk.LabelFrame(parent, text="进度", padding=10)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="就绪", foreground='green')
        self.status_label.pack()
    
    def _setup_result_frame(self, parent):
        """设置结果区"""
        # 结果统计
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(stats_frame, text="符合数量:").pack(side=tk.LEFT, padx=5)
        self.count_label = ttk.Label(stats_frame, text="0", font=('微软雅黑', 12, 'bold'), 
                                    foreground='blue')
        self.count_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(stats_frame, text="个").pack(side=tk.LEFT, padx=5)
        
        # 结果列表
        list_frame = ttk.LabelFrame(parent, text="日期列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview
        columns = ('日期', '时辰', '到山到向', '龙德课类型', '推荐指数')
        self.result_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100, anchor='center')
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        
        # 详细信息
        detail_frame = ttk.LabelFrame(parent, text="详细信息", padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=12, wrap=tk.WORD, 
                                                    font=('微软雅黑', 10))
        self.detail_text.pack(fill=tk.BOTH, expand=True)
    
    def _get_shan_list(self):
        """获取坐山列表"""
        return ['壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳', 
                '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥']
    
    def _get_direction_list(self):
        """获取朝向列表"""
        return ['丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥', 
                '壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳']
    
    def start_selection(self):
        """开始择日"""
        try:
            # 获取参数
            mountain = self.shan_var.get()
            direction = self.direction_var.get()
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
            min_arrival = self.min_arrival_var.get()
            long_de_type = self.long_de_type_var.get()
            
            # 验证日期
            if start_date > end_date:
                messagebox.showerror("错误", "开始日期不能大于结束日期")
                return
            
            # 禁用按钮
            self.select_btn.config(state=tk.DISABLED)
            self.export_btn.config(state=tk.DISABLED)
            self.status_label.config(text="正在择日...", foreground='blue')
            
            # 清空结果
            self.clear_results()
            
            # 开始择日
            self.results = self.selector.select_long_de_dates(
                mountain, direction, start_date, end_date, min_arrival
            )
            
            # 筛选龙德课类型
            if long_de_type != '全部':
                self.results = [r for r in self.results if long_de_type in r['long_de_type']]
            
            # 更新界面
            self._update_result_list()
            
            # 启用按钮
            self.select_btn.config(state=tk.NORMAL)
            if self.results:
                self.export_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"择日完成，找到 {len(self.results)} 个符合条件的日期", 
                                   foreground='green')
            
        except Exception as e:
            messagebox.showerror("错误", f"择日失败：{str(e)}")
            self.select_btn.config(state=tk.NORMAL)
            self.status_label.config(text="择日失败", foreground='red')
    
    def _update_result_list(self):
        """更新结果列表"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.count_label.config(text=str(len(self.results)))
        
        for result in self.results[:100]:  # 最多显示 100 条
            values = (
                result['date'],
                result['shi'],
                f"{result['arrival_count']}个",
                result['long_de_type'].replace('课', ''),
                self._get_recommendation_emoji(result['arrival_count'])
            )
            self.result_tree.insert('', tk.END, values=values)
    
    def _get_recommendation_emoji(self, arrival_count: int) -> str:
        """获取推荐指数图标"""
        if arrival_count >= 6:
            return '⭐⭐⭐'
        elif arrival_count >= 5:
            return '⭐⭐'
        elif arrival_count >= 4:
            return '⭐'
        else:
            return '普通'
    
    def on_result_select(self, event):
        """选择结果时显示详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        index = self.result_tree.index(selection[0])
        if index >= len(self.results):
            return
        
        result = self.results[index]
        
        # 生成详细信息
        detail = self._generate_detail_text(result)
        
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, detail)
    
    def _generate_detail_text(self, result: Dict) -> str:
        """生成详细文本"""
        kege = self.selector.generate_kege_structure(result)
        
        text = "=" * 60 + "\n"
        text += "龙德课到山到向课格结构\n"
        text += "=" * 60 + "\n\n"
        
        # 基本信息
        text += "【基本信息】\n"
        text += f"日期：{kege['基本信息']['日期']} ({kege['基本信息']['星期']})\n"
        text += f"四柱：{kege['基本信息']['四柱']['年柱']}年 {kege['基本信息']['四柱']['月柱']}月 "
        text += f"{kege['基本信息']['四柱']['日柱']}日 {kege['基本信息']['四柱']['时柱']}时\n"
        text += f"坐山朝向：{kege['基本信息']['坐山朝向']}\n\n"
        
        # 六壬课式
        text += "【六壬课式】\n"
        text += f"月将：{kege['六壬课式']['月将']}\n"
        text += f"占时：{kege['六壬课式']['占时']}\n"
        text += f"三传：{kege['六壬课式']['三传'].get('初传', '')} → "
        text += f"{kege['六壬课式']['三传'].get('中传', '')} → "
        text += f"{kege['六壬课式']['三传'].get('末传', '')}\n"
        text += f"课体：{', '.join(kege['六壬课式']['课体'][:5])}\n\n"
        
        # 龙德课分析
        text += "【龙德课分析】\n"
        text += f"类型：{kege['龙德课分析']['龙德课类型']}\n\n"
        text += kege['龙德课分析']['判断依据'] + "\n"
        
        # 到山到向分析
        text += "\n【到山到向分析】\n"
        arrival = kege['到山到向分析']
        text += f"山家禄马贵：禄={arrival['山家信息'].get('禄', '')}, "
        text += f"马={arrival['山家信息'].get('马', '')}, "
        text += f"贵人={arrival['山家信息'].get('贵人', [])}\n"
        text += f"到山到向详情：{', '.join(arrival['到山到向详情'])}\n"
        text += f"总计：{len(arrival['到山到向详情'])}个\n\n"
        
        # 综合评价
        text += "【综合评价】\n"
        text += f"课格等级：{kege['综合评价']['课格等级']}\n"
        text += f"推荐指数：{kege['综合评价']['推荐指数']}\n"
        
        return text
    
    def clear_results(self):
        """清空结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.count_label.config(text="0")
        self.detail_text.delete(1.0, tk.END)
        self.results = []
    
    def export_results(self):
        """导出结果"""
        if not self.results:
            messagebox.showwarning("提示", "没有可导出的结果")
            return
        
        file_types = [
            ('JSON 文件', '*.json'),
            ('文本文件', '*.txt'),
            ('所有文件', '*.*')
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=file_types,
            title='导出择日结果'
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.selector.save_results(self.results, file_path)
                else:
                    # 导出为文本
                    mountain = self.shan_var.get()
                    direction = self.direction_var.get()
                    self.selector.generate_report(self.results, file_path, mountain, direction)
                
                messagebox.showinfo("成功", f"结果已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")


def test_long_de_gui():
    """测试 GUI"""
    root = tk.Tk()
    root.title("龙德课到山到向择日系统")
    root.geometry("1000x700")
    
    gui = LongDeKeGUI(root)
    gui.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()


if __name__ == '__main__':
    test_long_de_gui()
