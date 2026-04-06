#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬完整起课引擎测试 GUI（增强版）
功能：
1. 完整起课排盘
2. 课体选择与浏览
3. 查看每个课体的课例数量
4. 64 课经匹配
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
import json

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from complete_qi_ke_engine import CompleteQiKeEngine
from accurate_ke_jing_matcher import AccurateKeJingMatcher


class CompleteQiKeGUI:
    """完整起课引擎测试界面（增强版）"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬完整起课引擎测试系统 - 课体浏览版")
        self.root.geometry("1600x1000")
        
        # 初始化引擎
        self.engine = CompleteQiKeEngine()
        self.matcher = AccurateKeJingMatcher()
        
        # 加载课例数据
        self.load_ke_li_data()
        
        # 统计每个课体的课例数量
        self.ke_ti_statistics = self.count_ke_ti_statistics()
        
        # 状态栏变量
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        
        # 创建界面
        self.create_ui()
    
    def load_ke_li_data(self):
        """加载课例数据"""
        try:
            # 优先使用专业版匹配数据
            ke_li_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_matched_pro.json')
            if not os.path.exists(ke_li_file):
                ke_li_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_matched.json')
            if not os.path.exists(ke_li_file):
                ke_li_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li.json')
            
            if os.path.exists(ke_li_file):
                with open(ke_li_file, 'r', encoding='utf-8') as f:
                    self.ke_li_data = json.load(f)
                print(f"已加载 {len(self.ke_li_data)} 个课例")
            else:
                self.ke_li_data = {}
                print("课例数据文件不存在")
        except Exception as e:
            print(f"加载课例数据失败：{e}")
            self.ke_li_data = {}
    
    def count_ke_ti_statistics(self):
        """统计每个课体的课例数量"""
        statistics = {}
        for ke_data in self.ke_li_data.values():
            matched_ke_jing = ke_data.get('matched_ke_jing', [])
            for ke_name in matched_ke_jing:
                statistics[ke_name] = statistics.get(ke_name, 0) + 1
        return statistics
    
    def create_ui(self):
        """创建界面"""
        # 主分割窗口（左中右三栏）
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ===== 左侧：课体选择区 =====
        left_frame = ttk.LabelFrame(main_pane, text="课体选择与统计", padding=10)
        main_pane.add(left_frame, weight=1)
        
        # 课体搜索
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="搜索课体：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_ke_ti).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="清除", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        # 课体列表（带数量统计）
        list_frame = ttk.LabelFrame(left_frame, text="课体列表（点击查看详情）", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建 Treeview
        columns = ('课体名称', '课例数量')
        self.ke_ti_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=25)
        
        self.ke_ti_tree.heading('课体名称', text='课体名称')
        self.ke_ti_tree.heading('课例数量', text='课例数量')
        self.ke_ti_tree.column('课体名称', width=120, anchor='w')
        self.ke_ti_tree.column('课例数量', width=80, anchor='center')
        
        # 填充数据
        self.populate_ke_ti_list()
        
        self.ke_ti_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ke_ti_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ke_ti_tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定选择事件
        self.ke_ti_tree.bind('<<TreeviewSelect>>', self.on_ke_ti_selected)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(left_frame, text="匹配统计", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, font=('微软雅黑', 9))
        self.stats_text.pack(fill=tk.X)
        self.update_stats_display()
        
        # 匹配进度说明
        progress_frame = ttk.LabelFrame(left_frame, text="说明", padding=8)
        progress_frame.pack(fill=tk.X, pady=5)
        
        progress_text = tk.Text(progress_frame, height=5, wrap=tk.WORD, font=('微软雅黑', 8))
        progress_text.pack(fill=tk.X)
        progress_text.insert('1.0', "当前系统已匹配 45 个课体（70.3%），覆盖 8640 个课例（100%）。\n\n其余 19 个课体需要特殊条件判断和天将系统配合。")
        progress_text.config(state='disabled')
        
        # ===== 中间：起课输入区 =====
        middle_frame = ttk.LabelFrame(main_pane, text="起课参数输入", padding=10)
        main_pane.add(middle_frame, weight=1)
        
        self.create_qi_ke_inputs(middle_frame)
        
        # ===== 右侧：结果显示区 =====
        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=2)
        
        # 上部：课式排盘
        top_frame = ttk.LabelFrame(right_pane, text="课式排盘", padding=10)
        right_pane.add(top_frame, weight=2)
        
        self.result_text = scrolledtext.ScrolledText(top_frame, wrap=tk.WORD, width=70, height=18, 
                                                     font=('Consolas', 10))
        self.result_text.pack(fill='both', expand=True)
        
        # 下部：课经匹配
        bottom_frame = ttk.LabelFrame(right_pane, text="64 课经匹配结果", padding=10)
        right_pane.add(bottom_frame, weight=1)
        
        self.kejing_text = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, width=70, height=12,
                                                     font=('Consolas', 10))
        self.kejing_text.pack(fill='both', expand=True)
        
        # 状态栏
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_qi_ke_inputs(self, parent):
        """创建起课输入区"""
        # 1. 日干支
        ttk.Label(parent, text="1. 日干支：", font=('微软雅黑', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=8)
        
        self.ri_gan_var = tk.StringVar(value='甲子')
        ri_gan_combo = ttk.Combobox(parent, textvariable=self.ri_gan_var, width=18, state='readonly')
        ganzhi_list = [
            '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
            '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
            '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
            '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
            '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
            '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
        ]
        ri_gan_combo['values'] = ganzhi_list
        ri_gan_combo.current(0)
        ri_gan_combo.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 2. 月将
        ttk.Label(parent, text="2. 月将：", font=('微软雅黑', 10, 'bold')).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=8)
        
        self.yue_jiang_var = tk.StringVar(value='亥')
        yue_jiang_combo = ttk.Combobox(parent, textvariable=self.yue_jiang_var, width=18, state='readonly')
        yue_jiang_combo['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        yue_jiang_combo.current(11)
        yue_jiang_combo.grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 3. 占时
        ttk.Label(parent, text="3. 占时：", font=('微软雅黑', 10, 'bold')).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=8)
        
        self.shi_chen_var = tk.StringVar(value='午')
        shi_chen_combo = ttk.Combobox(parent, textvariable=self.shi_chen_var, width=18, state='readonly')
        shi_chen_combo['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        shi_chen_combo.current(6)
        shi_chen_combo.grid(row=5, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 4. 农历月
        ttk.Label(parent, text="4. 农历月份：", font=('微软雅黑', 9)).grid(
            row=6, column=0, columnspan=2, sticky='w', pady=8)
        
        self.lunar_month_var = tk.StringVar(value='1')
        lunar_month_spin = ttk.Spinbox(parent, textvariable=self.lunar_month_var, from_=1, to=12, width=10)
        lunar_month_spin.grid(row=7, column=0, columnspan=2, pady=5, padx=5)
        
        # 5. 年支
        ttk.Label(parent, text="5. 年支：", font=('微软雅黑', 9)).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=8)
        
        self.nian_zhi_var = tk.StringVar(value='子')
        nian_zhi_combo = ttk.Combobox(parent, textvariable=self.nian_zhi_var, width=18, state='readonly')
        nian_zhi_combo['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        nian_zhi_combo.current(0)
        nian_zhi_combo.grid(row=9, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="起课", command=self.qi_ke, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear, width=12).pack(side=tk.LEFT, padx=5)
        
        # 快捷测试
        test_frame = ttk.LabelFrame(parent, text="快捷测试", padding=5)
        test_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Button(test_frame, text="伏吟课", 
                  command=lambda: self.load_test_case('戊辰', '子', '子', 12)).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(test_frame, text="反吟课", 
                  command=lambda: self.load_test_case('丙寅', '戌', '辰', 9)).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(test_frame, text="普通课", 
                  command=lambda: self.load_test_case('甲子', '亥', '午', 1)).pack(side=tk.LEFT, padx=2, pady=2)
    
    def populate_ke_ti_list(self):
        """填充课体列表"""
        # 清空现有数据
        for item in self.ke_ti_tree.get_children():
            self.ke_ti_tree.delete(item)
        
        # 按课例数量排序
        sorted_ke_ti = sorted(self.ke_ti_statistics.items(), key=lambda x: x[1], reverse=True)
        
        # 插入数据
        for ke_name, count in sorted_ke_ti:
            self.ke_ti_tree.insert('', 'end', values=(ke_name, count))
        
        self.status_var.set(f"共显示 {len(sorted_ke_ti)} 个课体")
    
    def search_ke_ti(self):
        """搜索课体"""
        search_term = self.search_var.get().strip()
        if not search_term:
            return
        
        # 清空现有数据
        for item in self.ke_ti_tree.get_children():
            self.ke_ti_tree.delete(item)
        
        # 搜索匹配的课体
        matched = [(name, count) for name, count in self.ke_ti_statistics.items() 
                  if search_term.lower() in name.lower()]
        
        # 插入搜索结果
        for ke_name, count in matched:
            self.ke_ti_tree.insert('', 'end', values=(ke_name, count))
        
        self.status_var.set(f"搜索到 {len(matched)} 个课体")
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set('')
        self.populate_ke_ti_list()
        self.status_var.set("已清除搜索")
    
    def on_ke_ti_selected(self, event):
        """选择课体时显示详细信息"""
        selected_item = self.ke_ti_tree.selection()
        if not selected_item:
            return
        
        item = self.ke_ti_tree.item(selected_item[0])
        ke_name = item['values'][0]
        count = item['values'][1]
        
        # 显示该课体的课例列表
        self.display_ke_ti_examples(ke_name, count)
        
        self.status_var.set(f"已选择：{ke_name}（{count}个课例）")
    
    def display_ke_ti_examples(self, ke_name: str, count: int):
        """显示课体的课例"""
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 80)
        output.append(f"课体：【{ke_name}】")
        output.append(f"课例数量：{count} 个")
        output.append("=" * 80)
        
        # 查找包含该课体的所有课例
        examples = []
        for ke_key, ke_data in self.ke_li_data.items():
            matched_ke_jing = ke_data.get('matched_ke_jing', [])
            if ke_name in matched_ke_jing:
                examples.append(ke_data)
        
        # 显示前 20 个课例
        output.append(f"\n课例列表（显示前 {min(20, len(examples))} 个，共{len(examples)}个）：\n")
        
        for i, example in enumerate(examples[:20], 1):
            ri_gan_zhi = example.get('ri_gan_zhi', '')
            yue = example.get('yue', '')
            shi = example.get('shi', '')
            yue_jiang = example.get('yue_jiang', '')
            score = example.get('score', 0)
            
            output.append(f"{i}. {ri_gan_zhi}日 {yue}月 {shi}时 (月将：{yue_jiang}) - 评分：{score}")
        
        if len(examples) > 20:
            output.append(f"\n... 还有 {len(examples) - 20} 个课例，请使用搜索或筛选功能查看")
        
        output.append("\n" + "=" * 80)
        output.append("\n提示：双击课例或点击'起课'按钮可查看该课例的详细排盘")
        
        self.result_text.insert(tk.END, "\n".join(output))
        
        # 存储当前课体信息供起课使用
        self.current_ke_ti_examples = examples
    
    def update_stats_display(self):
        """更新统计信息显示"""
        self.stats_text.delete('1.0', tk.END)
        
        total_ke_ti = len(self.ke_ti_statistics)
        total_ke_li = len(self.ke_li_data)
        top_5 = sorted(self.ke_ti_statistics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats = f"""课体总数：{total_ke_ti} 个
课例总数：{total_ke_li} 个

出现频率最高的课体：
"""
        for i, (name, count) in enumerate(top_5, 1):
            stats += f"  {i}. {name}: {count}课\n"
        
        self.stats_text.insert('1.0', stats)
    
    def load_test_case(self, ri_gan_zhi, yue_jiang, shi_chen, lunar_month):
        """加载测试案例"""
        self.ri_gan_var.set(ri_gan_zhi)
        self.yue_jiang_var.set(yue_jiang)
        self.shi_chen_var.set(shi_chen)
        self.lunar_month_var.set(str(lunar_month))
        self.status_var.set(f"已加载测试案例：{ri_gan_zhi}日{yue_jiang}将{shi_chen}时")
    
    def qi_ke(self):
        """起课"""
        try:
            ri_gan_zhi = self.ri_gan_var.get()
            yue_jiang = self.yue_jiang_var.get()
            shi_chen = self.shi_chen_var.get()
            lunar_month = int(self.lunar_month_var.get())
            nian_zhi = self.nian_zhi_var.get()
            
            self.status_var.set(f"正在起课：{ri_gan_zhi}日{yue_jiang}将{shi_chen}时...")
            self.root.update()
            
            # 起课
            result = self.engine.qi_ke(ri_gan_zhi, yue_jiang, shi_chen, lunar_month, nian_zhi)
            
            # 显示课式
            self.display_result(result)
            
            # 匹配课经
            matched_kejing = self.matcher.match_by_complete_qi_ke(result)
            self.display_kejing(matched_kejing)
            
            self.status_var.set(f"起课完成，匹配到 {len(matched_kejing)} 个课经")
            
        except Exception as e:
            messagebox.showerror("错误", f"起课失败：{str(e)}")
            self.status_var.set("起课失败")
    
    def display_result(self, result: dict):
        """显示课式结果"""
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 80)
        output.append("大六壬完整课式")
        output.append("=" * 80)
        
        # 基本信息
        basic = result['基本信息']
        output.append(f"\n【基本信息】")
        output.append(f"  日干支：{basic['日干支']}")
        output.append(f"  月将：{basic['月将']}")
        output.append(f"  占时：{basic['占时']}")
        output.append(f"  农历月：{basic['农历月']}")
        output.append(f"  年支：{basic['年支']}")
        
        # 天地盘
        output.append(f"\n【天地盘】")
        output.append(f"  天盘：{' '.join(result['天地盘']['天盘'])}")
        output.append(f"  地盘：{' '.join(result['天地盘']['地盘'])}")
        
        # 四课
        output.append(f"\n【四课】")
        for i, ke in enumerate(result['四课'], 1):
            output.append(f"  第{i}课：{ke['top']} (上) / {ke['bottom']} (下)")
        
        # 三传
        output.append(f"\n【三传】")
        sanchuan = result['三传']
        output.append(f"  初传：{sanchuan.get('初传', '')}")
        output.append(f"  中传：{sanchuan.get('中传', '')}")
        output.append(f"  末传：{sanchuan.get('末传', '')}")
        output.append(f"  课体：{sanchuan.get('课体', '')}")
        output.append(f"  起法：{sanchuan.get('起法', '')}")
        
        # 天将
        output.append(f"\n【天将】")
        output.append(f"  贵人：{result['天将']['贵人']}")
        output.append(f"  顺逆：{result['天将']['顺逆']}")
        output.append(f"  昼夜：{result['天将']['昼夜']}")
        
        # 神煞
        output.append(f"\n【神煞】")
        shen_sha = result['神煞']
        for name, value in shen_sha.items():
            if value:
                output.append(f"  {name:8s}: {value}")
        
        # 课体判断
        output.append(f"\n【课体判断】")
        ke_ti = result['课体']
        if ke_ti:
            for kt in ke_ti:
                output.append(f"  ✓ {kt}")
        else:
            output.append(f"  (无特殊课体)")
        
        output.append("=" * 80)
        
        self.result_text.insert(tk.END, "\n".join(output))
    
    def display_kejing(self, matched_kejing: list):
        """显示课经匹配结果"""
        self.kejing_text.delete(1.0, tk.END)
        
        if not matched_kejing:
            self.kejing_text.insert(tk.END, "未匹配到课经")
            return
        
        output = []
        output.append(f"匹配到 {len(matched_kejing)} 个课经：")
        output.append("=" * 80)
        
        for i, ke in enumerate(matched_kejing, 1):
            ke_name = ke.get('ke_name', '未知')
            ke_type = ke.get('ke_type', '')
            definition = ke.get('definition', '')
            summary = ke.get('summary', '')
            score = ke.get('score', 0)
            level = ke.get('level', '')
            duanyu = ke.get('duanyu', [])
            
            output.append(f"\n【{i}】{ke_name} (编号：{ke.get('ke_id', '')})")
            output.append(f"  类型：{ke_type}")
            output.append(f"  定义：{definition}")
            output.append(f"  摘要：{summary}")
            output.append(f"  评分：{score} ({level})")
            
            if duanyu:
                output.append(f"  断语：")
                for d in duanyu[:3]:  # 只显示前 3 条断语
                    output.append(f"    - {d}")
            
            output.append("-" * 80)
        
        self.kejing_text.insert(tk.END, "\n".join(output))
    
    def clear(self):
        """清空"""
        self.ri_gan_var.set('甲子')
        self.yue_jiang_var.set('亥')
        self.shi_chen_var.set('午')
        self.lunar_month_var.set('1')
        self.nian_zhi_var.set('子')
        self.result_text.delete(1.0, tk.END)
        self.kejing_text.delete(1.0, tk.END)
        self.status_var.set("已清空")


def main():
    """主函数"""
    root = tk.Tk()
    app = CompleteQiKeGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
