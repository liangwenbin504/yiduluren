"""
仪度六壬择日软件 - 主程序
图形用户界面（GUI）- 智能择日版本
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.douhou_engine import DouShouCalculator
from engine.daliuren_engine import DaLiuRenEngine
from engine.smart_selector import SmartDateSelector
from engine.comprehensive_selector import ComprehensiveSelector
from ui.tianpan_widget import TianPanWithTianJiangWidget


class YiDuLiuRenApp:
    """仪度六壬择日软件主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("仪度六壬择日软件 v2.0 - 智能择日版")
        self.root.geometry("1200x800")
        
        # 初始化计算器
        self.douhou_calc = DouShouCalculator()
        self.daliuren_engine = DaLiuRenEngine()
        self.smart_selector = SmartDateSelector()
        self.comprehensive_selector = ComprehensiveSelector()
        
        # 存储选中的日期
        self.selected_date = None
        self.best_dates = []
        self.comprehensive_dates = []
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建主界面
        self.create_main_interface()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出结果", command=self.export_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_main_interface(self):
        """创建主界面"""
        # 创建 Notebook（选项卡）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 只创建综合择日选项卡
        self.create_comprehensive_tab()
    
    def create_comprehensive_tab(self):
        """创建综合择日选项卡（斗首 + 大六壬）"""
        comp_frame = ttk.Frame(self.notebook)
        self.notebook.add(comp_frame, text="综合择日")
        
        # 左侧输入区
        left_frame = ttk.LabelFrame(comp_frame, text="输入参数", padding=10)
        left_frame.pack(side='left', fill='both', padx=5, pady=5)
        
        # 1. 选择山向
        ttk.Label(left_frame, text="1. 选择山向：", font=('微软雅黑', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=10)
        
        self.comp_mountain = ttk.Combobox(left_frame, width=20, state='readonly')
        self.comp_mountain['values'] = [
            '壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳',
            '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥'
        ]
        self.comp_mountain.current(0)
        self.comp_mountain.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 2. 选择日期范围（年月日）
        ttk.Label(left_frame, text="2. 选择日期范围（年月日）：", font=('微软雅黑', 10, 'bold')).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(15, 5))
        
        from datetime import datetime
        current_year = datetime.now().year
        
        # 起始日期（年月日）
        start_frame = ttk.Frame(left_frame)
        start_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')
        
        ttk.Label(start_frame, text="从").pack(side='left')
        self.comp_start_year = ttk.Spinbox(start_frame, from_=current_year, to=2100, width=7, state='readonly')
        self.comp_start_year.set(current_year)
        self.comp_start_year.pack(side='left', padx=2)
        ttk.Label(start_frame, text="年").pack(side='left')
        
        self.comp_start_month = ttk.Spinbox(start_frame, from_=1, to=12, width=5, state='readonly')
        self.comp_start_month.set(1)
        self.comp_start_month.pack(side='left', padx=2)
        ttk.Label(start_frame, text="月").pack(side='left')
        
        self.comp_start_day = ttk.Spinbox(start_frame, from_=1, to=31, width=5, state='readonly')
        self.comp_start_day.set(1)
        self.comp_start_day.pack(side='left', padx=2)
        ttk.Label(start_frame, text="日").pack(side='left')
        
        # 结束日期（年月日）
        end_frame = ttk.Frame(left_frame)
        end_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')
        
        ttk.Label(end_frame, text="到").pack(side='left')
        self.comp_end_year = ttk.Spinbox(end_frame, from_=current_year, to=2100, width=7, state='readonly')
        self.comp_end_year.set(current_year + 5)  # 默认 5 年
        self.comp_end_year.pack(side='left', padx=2)
        ttk.Label(end_frame, text="年").pack(side='left')
        
        self.comp_end_month = ttk.Spinbox(end_frame, from_=1, to=12, width=5, state='readonly')
        self.comp_end_month.set(12)
        self.comp_end_month.pack(side='left', padx=2)
        ttk.Label(end_frame, text="月").pack(side='left')
        
        self.comp_end_day = ttk.Spinbox(end_frame, from_=1, to=31, width=5, state='readonly')
        self.comp_end_day.set(31)
        self.comp_end_day.pack(side='left', padx=2)
        ttk.Label(end_frame, text="日").pack(side='left')
        
        ttk.Label(end_frame, text="（全年逐日计算，默认 5 年）", font=('微软雅黑', 9)).pack(side='left', padx=5)
        
        # 3. 选择日期个数
        ttk.Label(left_frame, text="3. 最优日期个数：", font=('微软雅黑', 10, 'bold')).grid(
            row=5, column=0, columnspan=2, sticky='w', pady=(15, 5))
        
        self.comp_date_count = ttk.Spinbox(left_frame, from_=1, to=20, width=10, state='readonly')
        self.comp_date_count.set(5)
        self.comp_date_count.grid(row=6, column=0, columnspan=2, pady=5)
        
        # 计算按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="开始综合择日", command=self.select_comprehensive_dates).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_comprehensive).pack(side='left', padx=5)
        
        # 日期选择区
        date_select_frame = ttk.LabelFrame(left_frame, text="选择日期", padding=10)
        date_select_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Label(date_select_frame, text="4. 选择日期后自动显示分析结果").pack(pady=5)
        
        self.comp_date_var = tk.StringVar()
        self.comp_date_combo = ttk.Combobox(date_select_frame, textvariable=self.comp_date_var, 
                                           width=25, state='readonly')
        self.comp_date_combo.pack(pady=5)
        self.comp_date_combo.bind('<<ComboboxSelected>>', self.on_comprehensive_date_selected)
        
        # 右侧结果显示区 - 使用 PanedWindow 分隔图形和文字
        right_pane = ttk.PanedWindow(comp_frame, orient=tk.VERTICAL)
        right_pane.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # 上部：图形化显示区（天地盘）
        visual_frame = ttk.LabelFrame(right_pane, text="天地盘排布", padding=10)
        right_pane.add(visual_frame, weight=2)
        
        # 创建天盘图形组件（正方形地支 + 外层天将）
        self.comp_tianpan_widget = TianPanWithTianJiangWidget(visual_frame, width=700, height=550)
        self.comp_tianpan_widget.pack(fill='both', expand=True)
        
        # 下部：文字结果显示区
        text_frame = ttk.LabelFrame(right_pane, text="详细分析", padding=10)
        right_pane.add(text_frame, weight=1)
        
        self.comp_result = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=70, height=20)
        self.comp_result.pack(fill='both', expand=True)
    
    def select_comprehensive_dates(self):
        """选择综合最佳日期（年月日范围，精确到每一天）"""
        try:
            mountain = self.comp_mountain.get()
            
            # 获取起始日期（年月日）
            start_year = int(self.comp_start_year.get())
            start_month = int(self.comp_start_month.get())
            start_day = int(self.comp_start_day.get())
            
            # 获取结束日期（年月日）
            end_year = int(self.comp_end_year.get())
            end_month = int(self.comp_end_month.get())
            end_day = int(self.comp_end_day.get())
            
            date_count = int(self.comp_date_count.get())
            
            # 验证日期
            from datetime import datetime
            start_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            
            if start_date > end_date:
                messagebox.showerror("错误", "起始日期不能大于结束日期！")
                return
            
            # 计算天数差
            delta_days = (end_date - start_date).days
            year_range = end_year - start_year
            
            if year_range > 60 or delta_days > 21915:
                messagebox.showerror("错误", "日期范围不能超过 60 年（一个甲子循环）！")
                return
            
            if delta_days > 3650:  # 超过 10 年
                confirm = messagebox.askyesno("提示", 
                    f"日期范围为{delta_days}天（约{delta_days//365}年），计算时间会很长（预计{delta_days//100}秒以上）。\n\n"
                    f"建议：\n"
                    f"- 快速计算：使用 5 年范围（约 30-60 秒）\n"
                    f"- 全面比较：使用 10-20 年范围（约 1-3 分钟）\n"
                    f"- 甲子循环：使用 60 年范围（约 5-10 分钟）\n\n"
                    f"确定要继续吗？")
                if not confirm:
                    self.status_var.set("已取消计算")
                    return
            
            self.status_var.set(f"正在综合择日计算（{start_year}年{start_month}月{start_day}日 至 {end_year}年{end_month}月{end_day}日，共{delta_days+1}天，全年逐日计算）...")
            self.root.update()
            
            # 计算综合最佳日期（精确到每一天）
            self.comprehensive_dates = self.comprehensive_selector.select_comprehensive_dates(
                mountain, start_year, start_month, start_day,
                end_year, end_month, end_day,
                date_count
            )
            
            # 填充到下拉框
            date_strings = []
            for i, date in enumerate(self.comprehensive_dates, 1):
                date_str = (f"{date['公历日期']} "
                           f"(综合:{date['综合评分']:.1f}-{date['综合吉凶']}, "
                           f"斗首:{date['斗首评分']}, 六壬:{date['大六壬评分']})")
                date_strings.append(date_str)
            
            self.comp_date_combo['values'] = date_strings
            if date_strings:
                self.comp_date_combo.current(0)
                # 自动选择第一个日期
                self.on_comprehensive_date_selected(None)
            
            self.status_var.set(f"综合择日完成，找到 {len(self.comprehensive_dates)} 个吉日")
            
        except Exception as e:
            messagebox.showerror("错误", f"综合择日失败：{str(e)}")
            self.status_var.set("综合择日失败")
    
    def on_comprehensive_date_selected(self, event):
        """选择综合日期后显示详细分析（包含图形化天地盘）"""
        try:
            index = self.comp_date_combo.current()
            if index < 0 or index >= len(self.comprehensive_dates):
                return
            
            date_info = self.comprehensive_dates[index]
            
            # 绘制天地盘图形
            self._draw_comprehensive_tiandi_pan(date_info)
            
            # 显示详细分析
            self.comp_result.delete(1.0, tk.END)
            output = self.comprehensive_selector.get_date_detail(date_info)
            self.comp_result.insert(tk.END, output)
            
            self.status_var.set("已显示详细分析（含图形化天地盘）")
            
        except Exception as e:
            messagebox.showerror("错误", f"显示分析失败：{str(e)}")
    
    def _draw_comprehensive_tiandi_pan(self, date_info: dict):
        """在综合择日界面绘制天地盘图形"""
        try:
            # 从大六壬分析结果中获取排盘数据
            daliuren_result = date_info.get('大六壬分析', {}).get('排盘结果', {})
            
            if daliuren_result and '天地盘' in daliuren_result and '天将' in daliuren_result:
                # 绘制天地盘
                self.comp_tianpan_widget.draw(
                    daliuren_result['天地盘'],
                    daliuren_result['天将']
                )
            else:
                # 清空画布
                self.comp_tianpan_widget.delete("all")
                # 显示提示
                self.comp_tianpan_widget.create_text(
                    375, 260,
                    text="暂无排盘数据",
                    font=('微软雅黑', 16),
                    fill='#999999'
                )
        except Exception as e:
            # 绘图失败时清空画布
            self.comp_tianpan_widget.delete("all")
    
    def clear_comprehensive(self):
        """清空综合择日输入"""
        from datetime import datetime
        current_year = datetime.now().year
        
        self.comp_mountain.current(0)
        # 重置为当前年月日
        self.comp_start_year.set(current_year)
        self.comp_start_month.set(1)
        self.comp_start_day.set(1)
        # 结束日期为当前年 12 月 31 日
        self.comp_end_year.set(current_year)
        self.comp_end_month.set(12)
        self.comp_end_day.set(31)
        
        self.comp_date_count.set(5)
        self.comp_date_combo['values'] = []
        self.comp_result.delete(1.0, tk.END)
        self.comprehensive_dates = []
        
        # 清空天地盘图形
        if hasattr(self, 'comp_tianpan_widget'):
            self.comp_tianpan_widget.delete("all")
        
        self.status_var.set("已清空")
    
    def create_smart_douhou_tab(self):
        """创建智能斗首择日选项卡"""
        douhou_frame = ttk.Frame(self.notebook)
        self.notebook.add(douhou_frame, text="智能斗首择日")
        
        # 左侧输入区
        left_frame = ttk.LabelFrame(douhou_frame, text="输入参数", padding=10)
        left_frame.pack(side='left', fill='both', padx=5, pady=5)
        
        # 1. 选择山向
        ttk.Label(left_frame, text="1. 选择山向：", font=('微软雅黑', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=10)
        
        self.douhou_mountain = ttk.Combobox(left_frame, width=20, state='readonly')
        self.douhou_mountain['values'] = [
            '壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳',
            '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥'
        ]
        self.douhou_mountain.current(0)
        self.douhou_mountain.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # 2. 选择年份范围
        ttk.Label(left_frame, text="2. 选择年份范围：", font=('微软雅黑', 10, 'bold')).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(15, 5))
        
        year_frame = ttk.Frame(left_frame)
        year_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')
        
        ttk.Label(year_frame, text="从").pack(side='left')
        self.start_year = ttk.Spinbox(year_frame, from_=2020, to=2050, width=8, state='readonly')
        self.start_year.set(2026)
        self.start_year.pack(side='left', padx=5)
        
        ttk.Label(year_frame, text="到").pack(side='left')
        self.end_year = ttk.Spinbox(year_frame, from_=2020, to=2050, width=8, state='readonly')
        self.end_year.set(2030)
        self.end_year.pack(side='left', padx=5)
        
        # 3. 选择日期个数
        ttk.Label(left_frame, text="3. 最优日期个数：", font=('微软雅黑', 10, 'bold')).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=(15, 5))
        
        self.date_count = ttk.Spinbox(left_frame, from_=1, to=20, width=10, state='readonly')
        self.date_count.set(5)
        self.date_count.grid(row=5, column=0, columnspan=2, pady=5)
        
        # 计算按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="开始择日", command=self.select_best_dates).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_douhou).pack(side='left', padx=5)
        
        # 日期选择区
        date_select_frame = ttk.LabelFrame(left_frame, text="选择日期", padding=10)
        date_select_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Label(date_select_frame, text="4. 选择日期后自动显示分析结果").pack(pady=5)
        
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(date_select_frame, textvariable=self.date_var, 
                                       width=25, state='readonly')
        self.date_combo.pack(pady=5)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_selected)
        
        # 右侧结果显示区
        right_frame = ttk.LabelFrame(douhou_frame, text="分析结果", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        self.douhou_result = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=70, height=40)
        self.douhou_result.pack(fill='both', expand=True)
    
    def create_daliuren_tab(self):
        """创建大六壬排盘选项卡"""
        daliuren_frame = ttk.Frame(self.notebook)
        self.notebook.add(daliuren_frame, text="大六壬排盘")
        
        # 左侧输入区
        left_frame = ttk.LabelFrame(daliuren_frame, text="输入参数", padding=10)
        left_frame.pack(side='left', fill='both', padx=5, pady=5)
        
        # 农历月份
        ttk.Label(left_frame, text="农历月份：").grid(row=0, column=0, sticky='w', pady=5)
        self.daliuren_month = ttk.Combobox(left_frame, width=15, state='readonly')
        self.daliuren_month['values'] = [f"{i}月" for i in range(1, 13)]
        self.daliuren_month.current(0)
        self.daliuren_month.grid(row=0, column=1, pady=5, padx=5)
        
        # 占时（时辰）
        ttk.Label(left_frame, text="占时：").grid(row=1, column=0, sticky='w', pady=5)
        self.daliuren_shichen = ttk.Combobox(left_frame, width=15, state='readonly')
        self.daliuren_shichen['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.daliuren_shichen.current(2)
        self.daliuren_shichen.grid(row=1, column=1, pady=5, padx=5)
        
        # 日干
        ttk.Label(left_frame, text="日干：").grid(row=2, column=0, sticky='w', pady=5)
        self.daliuren_ri_gan = ttk.Combobox(left_frame, width=15, state='readonly')
        self.daliuren_ri_gan['values'] = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        self.daliuren_ri_gan.current(0)
        self.daliuren_ri_gan.grid(row=2, column=1, pady=5, padx=5)
        
        # 日支
        ttk.Label(left_frame, text="日支：").grid(row=3, column=0, sticky='w', pady=5)
        self.daliuren_ri_zhi = ttk.Combobox(left_frame, width=15, state='readonly')
        self.daliuren_ri_zhi['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.daliuren_ri_zhi.current(0)
        self.daliuren_ri_zhi.grid(row=3, column=1, pady=5, padx=5)
        
        # 计算按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="开始排盘", command=self.calculate_daliuren).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_daliuren).pack(side='left', padx=5)
        
        # 右侧结果显示区 - 使用 PanedWindow 分隔
        right_pane = ttk.PanedWindow(daliuren_frame, orient=tk.VERTICAL)
        right_pane.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # 上部：图形化显示区（天地盘、四课）
        visual_frame = ttk.LabelFrame(right_pane, text="排盘图示", padding=10)
        right_pane.add(visual_frame, weight=2)
        
        # 创建专业的天盘排布组件
        self.tianpan_widget = TianPanWithTianJiangWidget(visual_frame, width=600, height=550)
        self.tianpan_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 下部：文字结果显示区
        text_frame = ttk.LabelFrame(right_pane, text="详细结果", padding=10)
        right_pane.add(text_frame, weight=1)
        
        self.daliuren_result = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=60, height=15)
        self.daliuren_result.pack(fill='both', expand=True)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def select_best_dates(self):
        """选择最优日期"""
        try:
            mountain = self.douhou_mountain.get()
            start_year = int(self.start_year.get())
            end_year = int(self.end_year.get())
            date_count = int(self.date_count.get())
            
            if start_year > end_year:
                messagebox.showerror("错误", "起始年份不能大于结束年份！")
                return
            
            self.status_var.set("正在择日计算...")
            self.root.update()
            
            # 计算最优日期
            self.best_dates = self.smart_selector.select_best_dates(
                mountain, start_year, end_year, date_count
            )
            
            # 填充到下拉框
            date_strings = []
            for i, date in enumerate(self.best_dates, 1):
                date_str = f"{date['公历日期']} (评分:{date['综合评分']} - {date['吉凶等级']})"
                date_strings.append(date_str)
            
            self.date_combo['values'] = date_strings
            if date_strings:
                self.date_combo.current(0)
                # 自动选择第一个日期
                self.on_date_selected(None)
            
            self.status_var.set(f"择日完成，找到 {len(self.best_dates)} 个吉日期")
            
        except Exception as e:
            messagebox.showerror("错误", f"择日失败：{str(e)}")
            self.status_var.set("择日失败")
    
    def on_date_selected(self, event):
        """选择日期后显示详细分析"""
        try:
            index = self.date_combo.current()
            if index < 0 or index >= len(self.best_dates):
                return
            
            date_info = self.best_dates[index]
            
            # 显示详细分析
            self.douhou_result.delete(1.0, tk.END)
            output = self.format_detailed_analysis(date_info)
            self.douhou_result.insert(tk.END, output)
            
            self.selected_date = date_info
            self.status_var.set("已显示详细分析")
            
        except Exception as e:
            messagebox.showerror("错误", f"显示分析失败：{str(e)}")
    
    def format_detailed_analysis(self, date_info: dict) -> str:
        """格式化详细分析结果"""
        output = []
        output.append("=" * 70)
        output.append("仪度六壬斗首择日 - 详细分析结果")
        output.append("=" * 70)
        
        # 基本信息
        output.append(f"\n【基本信息】")
        output.append(f"公历日期：{date_info['公历日期']}")
        output.append(f"农历日期：{date_info['农历日期']}")
        output.append(f"吉凶等级：{date_info['吉凶等级']}")
        output.append(f"综合评分：{date_info['综合评分']} / 100")
        
        # 四柱
        output.append(f"\n【四柱八字】")
        for pillar_name, pillar_value in date_info['四柱'].items():
            output.append(f"  {pillar_name}: {pillar_value}")
        
        # 斗首分析
        output.append(f"\n【斗首五行分析】")
        douhou = date_info['斗首分析']
        output.append(f"  山家五行：{douhou['山家五行']}")
        output.append(f"\n  五星配置：")
        for star_name, wuxing in douhou['五星配置']['五星配置'].items():
            output.append(f"    {star_name}: {wuxing}")
        
        # 化气分析
        output.append(f"\n  四柱化气：")
        for name, info in douhou['化气分析'].items():
            output.append(f"    {name}柱：{info['天干']}化{info['化气']} - {info['与山家关系']}")
        
        # 禄马贵到山到向分析
        output.append(f"\n【禄马贵到山到向分析】")
        lu_ma_gui = date_info['禄马贵分析']
        
        output.append(f"\n  山家禄马贵：")
        if '禄' in lu_ma_gui['山家禄马贵']:
            output.append(f"    禄神：{lu_ma_gui['山家禄马贵']['禄']}")
        if '马' in lu_ma_gui['山家禄马贵']:
            output.append(f"    驿马：{lu_ma_gui['山家禄马贵']['马']}")
        if '贵' in lu_ma_gui['山家禄马贵']:
            output.append(f"    贵人：{lu_ma_gui['山家禄马贵']['贵']}")
        
        output.append(f"\n  年柱禄马贵：")
        if lu_ma_gui.get('年柱禄马贵'):
            for key, value in lu_ma_gui['年柱禄马贵'].items():
                output.append(f"    {key}: {value}")
        else:
            output.append("    无")
        
        output.append(f"\n  月柱禄马贵：")
        if lu_ma_gui.get('月柱禄马贵'):
            for key, value in lu_ma_gui['月柱禄马贵'].items():
                output.append(f"    {key}: {value}")
        else:
            output.append("    无")
        
        output.append(f"\n  日柱禄马贵：")
        if lu_ma_gui.get('日柱禄马贵'):
            for key, value in lu_ma_gui['日柱禄马贵'].items():
                output.append(f"    {key}: {value}")
        else:
            output.append("    无")
        
        # 总结
        output.append(f"\n【禄马贵总结】")
        for item in lu_ma_gui['总结']:
            output.append(f"  • {item}")
        
        # 吉凶判断
        output.append(f"\n【吉凶判断】")
        for judgment in douhou['吉凶判断']:
            output.append(f"  • {judgment}")
        
        # 特别提示
        output.append(f"\n【特别提示】")
        if date_info['综合评分'] >= 80:
            output.append("  ✅ 此日为上佳吉日，禄马贵齐全，宜用！")
        elif date_info['综合评分'] >= 70:
            output.append("  ✓ 此日为吉日，可用！")
        elif date_info['综合评分'] >= 60:
            output.append("  ○ 此日为小吉日，斟酌使用！")
        else:
            output.append("  △ 此日平平，建议另择吉日！")
        
        output.append("\n" + "=" * 70)
        
        return "\n".join(output)
    
    def format_douhou_result(self, result: dict) -> str:
        """格式化斗首结果（旧版，保留备用）"""
        output = []
        output.append("=" * 50)
        output.append("斗首择日分析结果")
        output.append("=" * 50)
        output.append(f"\n山向：{result['山向']}")
        output.append(f"山家五行：{result['山家五行']}")
        output.append(f"\n四柱天干：")
        for name, tiangan in result['四柱天干'].items():
            output.append(f"  {name}柱：{tiangan}")
        
        output.append(f"\n五星配置：")
        for star_name, wuxing in result['五星配置']['五星配置'].items():
            output.append(f"  {star_name}: {wuxing}")
        
        output.append(f"\n化气分析：")
        for name, info in result['化气分析'].items():
            output.append(f"  {name}柱：{info['天干']}化{info['化气']} - {info['与山家关系']}")
        
        output.append(f"\n吉凶判断：")
        for judgment in result['吉凶判断']:
            output.append(f"  • {judgment}")
        
        output.append("\n" + "=" * 50)
        return "\n".join(output)
    
    def calculate_daliuren(self):
        """计算大六壬排盘"""
        try:
            lunar_month = int(self.daliuren_month.get().replace('月', ''))
            shichen = self.daliuren_shichen.get()
            ri_gan = self.daliuren_ri_gan.get()
            ri_zhi = self.daliuren_ri_zhi.get()
            
            # 排盘
            result = self.daliuren_engine.full_pai_pan(lunar_month, shichen, ri_gan, ri_zhi)
            
            # 显示结果
            self.daliuren_result.delete(1.0, tk.END)
            output = self.format_daliuren_result(result)
            self.daliuren_result.insert(tk.END, output)
            
            # 绘制图形化界面
            self.draw_daliuren_chart(result)
            
            self.status_var.set("大六壬排盘完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"排盘失败：{str(e)}")
            self.status_var.set("排盘失败")
    
    def draw_daliuren_chart(self, result: dict):
        """绘制大六壬排盘图（使用专业组件）"""
        # 使用新的图形化组件绘制天地盘 + 天将
        self.tianpan_widget.draw(result['天地盘'], result['天将'])
    
    def draw_si_ke(self, si_ke: list, ri_zhu: str, x_start: int, y_start: int, cell_size: int):
        """绘制四课（美化版）"""
        canvas = self.daliuren_canvas
        
        # 颜色配置
        header_bg = '#FFD700'  # 标题背景（金色）
        top_bg = '#FFB6C1'  # 上神背景（浅红色）
        bottom_bg = '#87CEEB'  # 下神背景（天蓝色）
        text_color = '#2C3E50'  # 文字颜色
        border_color = '#8B4513'  # 边框颜色（棕色）
        
        # 标题
        canvas.create_text(x_start + 150, y_start - 20, 
                         text="四课", 
                         font=('微软雅黑', 16, 'bold'), 
                         fill='#8B0000')
        
        # 四课布局：从右到左排列
        ke_positions = [3, 2, 1, 0]  # 从右到左的列位置
        offset_x = 80  # 向右偏移
        
        for i, ke in enumerate(si_ke):
            col = ke_positions[i]
            x = x_start + col * cell_size + offset_x
            
            # 课名标签（顶部）
            ke_name = f"第{['一','二','三','四'][i]}课"
            canvas.create_rectangle(x, y_start - 25, x + cell_size, y_start - 5,
                                   fill=header_bg, outline=border_color, width=1)
            canvas.create_text(x + cell_size/2, y_start - 15, text=ke_name, 
                             font=('微软雅黑', 9, 'bold'), fill=text_color)
            
            # 上神
            canvas.create_rectangle(x, y_start, x + cell_size, y_start + cell_size, 
                                   fill=top_bg, outline=border_color, width=2)
            canvas.create_text(x + cell_size/2, y_start + cell_size/2, text=ke['top'], 
                             font=('微软雅黑', 14, 'bold'), fill=text_color)
            
            # 下神
            canvas.create_rectangle(x, y_start + cell_size, x + cell_size, y_start + 2*cell_size, 
                                   fill=bottom_bg, outline=border_color, width=2)
            canvas.create_text(x + cell_size/2, y_start + cell_size*1.5, text=ke['bottom'], 
                             font=('微软雅黑', 14, 'bold'), fill=text_color)
        
        # 标注"四课"竖排标题
        canvas.create_text(x_start + 10, y_start + cell_size, text="四课", 
                         font=('微软雅黑', 14, 'bold'), fill='#8B0000', angle=90)
    
    def draw_san_chuan(self, san_chuan: dict, x_start: int, y_start: int, cell_size: int):
        """绘制三传（美化版）"""
        canvas = self.daliuren_canvas
        
        # 颜色配置
        header_bg = '#FFD700'  # 标题背景（金色）
        chuan_bg = '#98FB98'  # 三传背景（浅绿色）
        text_color = '#2C3E50'  # 文字颜色
        border_color = '#8B4513'  # 边框颜色（棕色）
        
        # 标题
        canvas.create_text(x_start + 150, y_start - 20, 
                         text="三传", 
                         font=('微软雅黑', 16, 'bold'), 
                         fill='#8B0000')
        
        chuan_list = san_chuan['三传']
        chuan_names = ['初传', '中传', '末传']
        
        # 三传竖向排列
        for i, chuan in enumerate(chuan_list):
            if chuan:
                y = y_start + i * cell_size
                x = x_start + 80
                
                # 传名标签（左侧）
                canvas.create_text(x - 40, y + cell_size/2, 
                                 text=chuan_names[i], 
                                 font=('微软雅黑', 10, 'bold'), 
                                 fill='#8B0000')
                
                # 传
                canvas.create_rectangle(x, y, x + cell_size*1.5, y + cell_size, 
                                       fill=chuan_bg, outline=border_color, width=2)
                canvas.create_text(x + cell_size*0.75, y + cell_size/2, text=chuan, 
                                 font=('微软雅黑', 14, 'bold'), fill=text_color)
        
        # 课体和起法
        canvas.create_text(x_start + 280, y_start + cell_size/2, 
                         text=f"课体：{san_chuan['课体']}", 
                         font=('微软雅黑', 10, 'bold'), 
                         fill='#8B0000')
        canvas.create_text(x_start + 280, y_start + cell_size*1.5, 
                         text=f"起法：{san_chuan['起法']}", 
                         font=('微软雅黑', 10, 'bold'), 
                         fill='#8B0000')
    
    def format_daliuren_result(self, result: dict) -> str:
        """格式化大六壬结果"""
        output = []
        output.append("=" * 50)
        output.append("大六壬排盘结果")
        output.append("=" * 50)
        output.append(f"\n月将：{result['月将']}")
        output.append(f"占时：{result['占时']}")
        output.append(f"日柱：{result['日柱']}")
        
        output.append(f"\n【天地盘】")
        output.append("地盘：{}".format(" ".join(result['天地盘']['地盘'])))
        output.append("天盘：{}".format(" ".join(result['天地盘']['天盘'])))
        
        output.append(f"\n【四课】")
        for ke in result['四课']:
            output.append(f"  {ke['name']}: {ke['top']} {ke['bottom']}")
        
        output.append(f"\n【三传】")
        output.append(f"  课体：{result['三传']['课体']}")
        output.append(f"  起法：{result['三传']['起法']}")
        output.append(f"  初传：{result['三传']['三传'][0] if result['三传']['三传'] else ''}")
        output.append(f"  中传：{result['三传']['三传'][1] if len(result['三传']['三传']) > 1 else ''}")
        output.append(f"  末传：{result['三传']['三传'][2] if len(result['三传']['三传']) > 2 else ''}")
        
        output.append(f"\n【禄马贵】")
        output.append(f"  禄：{result['禄马贵']['禄']}")
        output.append(f"  驿马：{result['禄马贵']['驿马']}")
        output.append(f"  贵人：{', '.join(result['禄马贵']['贵人'])}")
        
        output.append("\n" + "=" * 50)
        return "\n".join(output)
    
    def clear_douhou(self):
        """清空斗首输入"""
        self.douhou_mountain.current(0)
        self.start_year.set(2026)
        self.end_year.set(2030)
        self.date_count.set(5)
        self.date_combo['values'] = []
        self.douhou_result.delete(1.0, tk.END)
        self.best_dates = []
        self.selected_date = None
        self.status_var.set("已清空")
    
    def clear_daliuren(self):
        """清空大六壬输入"""
        self.daliuren_month.current(0)
        self.daliuren_shichen.current(0)
        self.daliuren_ri_gan.current(0)
        self.daliuren_ri_zhi.current(0)
        self.daliuren_result.delete(1.0, tk.END)
        self.status_var.set("已清空")
    
    def export_result(self):
        """导出结果"""
        try:
            # 选择导出文件路径
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Word 文档", "*.docx"), ("所有文件", "*.*")],
                initialfile="六壬排盘结果.docx"
            )
            
            if not file_path:
                return
            
            # 导入导出模块
            from export.docx_exporter import LiuRenExporter
            exporter = LiuRenExporter()
            
            # 获取排盘结果
            daliuren_result = None
            
            # 检查综合择日界面
            if hasattr(self, 'comprehensive_dates') and self.comprehensive_dates and self.comp_date_combo.current() >= 0:
                index = self.comp_date_combo.current()
                date_info = self.comprehensive_dates[index]
                daliuren_result = date_info.get('大六壬分析', {}).get('排盘结果', {})
            
            # 检查智能斗首择日界面
            elif hasattr(self, 'best_dates') and self.best_dates and self.date_combo.current() >= 0:
                index = self.date_combo.current()
                date_info = self.best_dates[index]
                daliuren_result = date_info.get('大六壬分析', {}).get('排盘结果', {})
            
            # 检查大六壬排盘界面
            elif hasattr(self, 'daliuren_engine') and hasattr(self, 'daliuren_result'):
                # 从大六壬排盘界面获取数据
                # 注意：这里需要确保 daliuren_engine 已经计算过排盘
                try:
                    lunar_month = int(self.daliuren_month.get().replace('月', ''))
                    shichen = self.daliuren_shichen.get()
                    ri_gan = self.daliuren_ri_gan.get()
                    ri_zhi = self.daliuren_ri_zhi.get()
                    daliuren_result = self.daliuren_engine.full_pai_pan(lunar_month, shichen, ri_gan, ri_zhi)
                except:
                    pass
            
            if not daliuren_result:
                messagebox.showinfo("提示", "暂无排盘数据可导出")
                return
            
            # 导出到 DOCX
            exporter.export_to_docx(daliuren_result, file_path)
            messagebox.showinfo("成功", f"结果已导出到：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
仪度六壬择日软件使用说明（智能版）
================================

【智能斗首择日】
1. 选择山向（二十四山）
2. 选择年份范围（如 2026-2030）
3. 选择需要返回的最优日期个数
4. 点击"开始择日"按钮
5. 从下拉列表中选择一个日期
6. 自动显示详细分析结果，包括：
   - 四柱八字
   - 斗首五星配置
   - 禄马贵到山到向分析
   - 吉凶判断

【大六壬排盘】
1. 选择农历月份
2. 选择占时（时辰）
3. 输入日干支
4. 点击"开始排盘"按钮
5. 查看天地盘、四课、三传、禄马贵

【禄马贵到山到向】
软件会自动分析：
- 山家禄马贵
- 年柱禄马贵
- 月柱禄马贵
- 日柱禄马贵
- 判断是否到山到向
"""
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
仪度六壬择日软件 v2.0
=====================

智能择日版

基于《仪度六壬选日要诀》开发
集成斗首择日和大六壬排盘功能

特色功能：
- 智能自动择日
- 禄马贵到山到向分析
- 年份范围选择
- 吉凶评分系统

开发时间：2026 年
技术支持：真龙风水总馆
"""
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = YiDuLiuRenApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
