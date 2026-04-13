#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合择日 GUI 界面
功能：
1. 选择山向（24 山）
2. 选择日期范围
3. 根据条件筛选（斗首课格、六壬课体）
4. 显示最佳日期
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
except ImportError:
    print("错误：需要安装 tkinter 库")
    print("Windows: python -m pip install tk")
    print("Linux: sudo apt-get install python3-tk")
    sys.exit(1)

from engine.douhou_engine import DouShouCalculator
from engine.ke_ti_judge import KeTiJudgeCalculator
from engine.precise_calendar import PreciseCalendar, get_sizhu_accurate
from engine.long_de_ke_selector import LongDeKeSelector
from engine.complete_qi_ke_engine import CompleteQiKeEngine
from core_modules.data.斗首择日规则 import DIZHI


class ComprehensiveDateSelectorGUI:
    """综合择日 GUI 界面"""
    
    # 24 山列表
    SHAN_24 = [
        '壬', '子', '癸', '丑', '艮', '寅',
        '甲', '卯', '乙', '辰', '巽', '巳',
        '丙', '午', '丁', '未', '坤', '申',
        '庚', '酉', '辛', '戌', '乾', '亥'
    ]
    
    # 斗首课格类型
    DOUHOU_KEGE = ['全部', '元辰课', '武财课', '贪官课', '廉贞课', '破鬼课']
    
    # 六壬吉课列表
    LIUREN_JI_KE = [
        '全部', '龙德课', '富贵课', '三光课', '天福课', '玉堂课',
        '官爵课', '斩关课', '游子课', '三奇课', '六仪课',
        '时泰课', '龙德课', '天赦课', '天愿课'
    ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("仪度六壬综合择日系统")
        self.root.geometry("1200x800")
        
        # 初始化引擎
        self.calendar = PreciseCalendar()
        self.douhou_calc = DouShouCalculator()
        self.ke_ti_judge = KeTiJudgeCalculator()
        self.long_de_selector = LongDeKeSelector()
        self.qi_ke_engine = CompleteQiKeEngine()
        
        # 创建界面
        self._create_menu()
        self._create_widgets()
        
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出结果", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # ===== 第一步：选择山向 =====
        step1_frame = ttk.LabelFrame(main_frame, text="第一步：选择山向", padding="10")
        step1_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(step1_frame, text="坐山:").grid(row=0, column=0, padx=5)
        self.shan_combo = ttk.Combobox(step1_frame, values=self.SHAN_24, width=10, state="readonly")
        self.shan_combo.set('壬')
        self.shan_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(step1_frame, text="朝向:").grid(row=0, column=2, padx=5)
        self.xiang_combo = ttk.Combobox(step1_frame, values=self.SHAN_24, width=10, state="readonly")
        self.xiang_combo.set('丙')
        self.xiang_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(step1_frame, text="互换山向", command=self._swap_shan_xiang).grid(row=0, column=4, padx=10)
        
        # 显示山向信息
        self.shan_info_text = scrolledtext.ScrolledText(step1_frame, height=4, width=80)
        self.shan_info_text.grid(row=1, column=0, columnspan=5, pady=10, sticky=(tk.W, tk.E))
        
        # ===== 第二步：选择日期范围 =====
        step2_frame = ttk.LabelFrame(main_frame, text="第二步：选择日期范围", padding="10")
        step2_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(step2_frame, text="开始日期:").grid(row=0, column=0, padx=5)
        self.start_date_entry = ttk.Entry(step2_frame, width=15)
        self.start_date_entry.insert(0, "2026-03-15")
        self.start_date_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(step2_frame, text="结束日期:").grid(row=0, column=2, padx=5)
        self.end_date_entry = ttk.Entry(step2_frame, width=15)
        self.end_date_entry.insert(0, "2027-12-31")
        self.end_date_entry.grid(row=0, column=3, padx=5)
        
        # 快捷日期范围
        ttk.Label(step2_frame, text="快捷:").grid(row=0, column=4, padx=5)
        date_range_btn = ttk.Menubutton(step2_frame, text="选择范围", direction='below')
        date_range_btn.menu = tk.Menu(date_range_btn, tearoff=0)
        date_range_btn["menu"] = date_range_btn.menu
        date_range_btn.menu.add_command(label="当年", command=lambda: self._set_date_range(0))
        date_range_btn.menu.add_command(label="半年", command=lambda: self._set_date_range(0.5))
        date_range_btn.menu.add_command(label="两年", command=lambda: self._set_date_range(2))
        date_range_btn.grid(row=0, column=5, padx=5)
        
        # ===== 第三步：筛选条件 =====
        step3_frame = ttk.LabelFrame(main_frame, text="第三步：设置筛选条件", padding="10")
        step3_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 斗首课格筛选
        ttk.Label(step3_frame, text="斗首课格:").grid(row=0, column=0, padx=5)
        self.douhou_combo = ttk.Combobox(step3_frame, values=self.DOUHOU_KEGE, width=12, state="readonly")
        self.douhou_combo.set('全部')
        self.douhou_combo.grid(row=0, column=1, padx=5)
        
        # 最低评分
        ttk.Label(step3_frame, text="最低评分:").grid(row=0, column=2, padx=5)
        self.min_score_spin = ttk.Spinbox(step3_frame, from_=0, to=10, increment=0.5, width=8)
        self.min_score_spin.set(6.0)
        self.min_score_spin.grid(row=0, column=3, padx=5)
        
        # 六壬吉课筛选
        ttk.Label(step3_frame, text="六壬吉课:").grid(row=0, column=4, padx=5)
        self.liuren_combo = ttk.Combobox(step3_frame, values=self.LIUREN_JI_KE, width=12, state="readonly")
        self.liuren_combo.set('全部')
        self.liuren_combo.grid(row=0, column=5, padx=5)
        
        # 其他选项
        self.long_de_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(step3_frame, text="仅龙德课", variable=self.long_de_var).grid(row=0, column=6, padx=10)
        
        # ===== 执行按钮 =====
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(action_frame, text="开始择日", command=self._start_selection, width=20)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = ttk.Button(action_frame, text="停止", command=self._stop_selection, state='disabled', width=20)
        self.stop_btn.grid(row=0, column=1, padx=10)
        
        ttk.Button(action_frame, text="清空结果", command=self._clear_results, width=20).grid(row=0, column=2, padx=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=0, column=3, padx=20)
        
        self.progress_label = ttk.Label(action_frame, text="就绪")
        self.progress_label.grid(row=0, column=4, padx=10)
        
        # ===== 结果展示 =====
        result_frame = ttk.LabelFrame(main_frame, text="择日结果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 结果树形视图
        columns = ('序号', '日期', '星期', '四柱', '斗首课格', '评分', '六壬课体', '吉神', '推荐')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=20)
        
        # 设置列宽
        self.result_tree.column('序号', width=50, anchor='center')
        self.result_tree.column('日期', width=100, anchor='center')
        self.result_tree.column('星期', width=60, anchor='center')
        self.result_tree.column('四柱', width=280, anchor='center')
        self.result_tree.column('斗首课格', width=100, anchor='center')
        self.result_tree.column('评分', width=60, anchor='center')
        self.result_tree.column('六壬课体', width=120, anchor='center')
        self.result_tree.column('吉神', width=150, anchor='center')
        self.result_tree.column('推荐', width=120, anchor='center')
        
        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
        
        # 滚动条
        y_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        x_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # 布局
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        y_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        x_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 双击查看详情
        self.result_tree.bind('<Double-1>', self._show_detail)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="共找到 0 个符合条件的日期", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 存储结果
        self.results = []
        
    def _swap_shan_xiang(self):
        """互换山向"""
        shan = self.shan_combo.get()
        xiang = self.xiang_combo.get()
        self.shan_combo.set(xiang)
        self.xiang_combo.set(shan)
        self._update_shan_info()
    
    def _set_date_range(self, years):
        """设置日期范围"""
        today = datetime.now()
        start_date = today
        
        if years == 0:  # 当年
            start_date = datetime(today.year, 1, 1)
            end_date = datetime(today.year, 12, 31)
        elif years == 0.5:  # 半年
            end_date = today + timedelta(days=180)
        elif years == 2:  # 两年
            end_date = today + timedelta(days=730)
        else:
            end_date = today + timedelta(days=365)
        
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, start_date.strftime('%Y-%m-%d'))
        
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end_date.strftime('%Y-%m-%d'))
    
    def _update_shan_info(self):
        """更新山向信息"""
        shan = self.shan_combo.get()
        xiang = self.xiang_combo.get()
        
        # 这里可以添加山向详细信息
        info = f"坐{shan}山朝{xiang}向 - 详细信息待补充\n"
        info += "禄马贵：待计算\n"
        
        self.shan_info_text.delete(1.0, tk.END)
        self.shan_info_text.insert(tk.END, info)
    
    def _start_selection(self):
        """开始择日"""
        try:
            # 获取参数
            shan = self.shan_combo.get()
            xiang = self.xiang_combo.get()
            
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            if start_date > end_date:
                messagebox.showerror("错误", "开始日期不能晚于结束日期")
                return
            
            # 获取筛选条件
            douhou_kege = self.douhou_combo.get()
            min_score = float(self.min_score_spin.get())
            liuren_ke = self.liuren_combo.get()
            only_long_de = self.long_de_var.get()
            
            # 清空结果
            self._clear_results()
            
            # 更新按钮状态
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
            # 开始择日（在后台线程中执行）
            import threading
            thread = threading.Thread(
                target=self._selection_worker,
                args=(shan, xiang, start_date, end_date, douhou_kege, min_score, liuren_ke, only_long_de)
            )
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"发生错误：{str(e)}")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def _selection_worker(self, shan, xiang, start_date, end_date, douhou_kege, min_score, liuren_ke, only_long_de):
        """择日工作线程"""
        try:
            total_days = (end_date - start_date).days + 1
            qualified_count = 0
            total_ke_count = 0
            
            current_date = start_date
            day_count = 0
            
            while current_date <= end_date:
                day_count += 1
                
                # 更新进度
                progress = (day_count / total_days) * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"{day_count}/{total_days}")
                
                # 处理日期
                year, month, day = current_date.year, current_date.month, current_date.day
                
                # 1. 检查斗首课格
                # 获取四柱天干
                sizhu_temp = get_sizhu_accurate(year, month, day, 12, city_name='北京')
                year_gan = sizhu_temp['年柱'][0]
                month_gan = sizhu_temp['月柱'][0]
                day_gan = sizhu_temp['日柱'][0]
                hour_gan = sizhu_temp['时柱'][0]
                
                # 分析斗首课格
                douhou_result = self.douhou_calc.analyze_douhou_day(shan, year_gan, month_gan, day_gan, hour_gan)
                
                # 根据日干确定课格
                ri_gan = day_gan
                if ri_gan in ['甲', '己']:
                    kege_name = '元辰课'
                    kege_score = 8.5
                elif ri_gan in ['丙', '辛']:
                    kege_name = '武财课'
                    kege_score = 9.0
                elif ri_gan in ['乙', '庚']:
                    kege_name = '贪官课'
                    kege_score = 7.0
                elif ri_gan in ['丁', '壬']:
                    kege_name = '廉贞课'
                    kege_score = 6.0
                else:  # 戊、癸
                    kege_name = '破鬼课'
                    kege_score = 2.5
                
                # 筛选斗首课格
                if douhou_kege != '全部' and kege_name != douhou_kege:
                    current_date += timedelta(days=1)
                    continue
                
                # 筛选评分
                if kege_score < min_score:
                    current_date += timedelta(days=1)
                    continue
                
                # 2. 获取四柱
                sizhu = get_sizhu_accurate(year, month, day, 12, city_name='北京')
                
                # 3. 获取日干支、月将、太岁
                ri_ganzhi = sizhu['日柱']
                ri_gan = ri_ganzhi[0]
                ri_zhi = ri_ganzhi[1]
                
                # 获取年支（太岁）
                year_ganzhi = sizhu['年柱']
                tai_sui = year_ganzhi[1]
                
                # 获取月将（根据节气）
                try:
                    yue_jiang = self.calendar.get_month_ganzhi(year, month, day)[1]
                except:
                    # 简化：根据月份估算月将
                    lunar_month = month
                    yue_jiang_index = (12 - lunar_month) % 12
                    yue_jiang = DIZHI[yue_jiang_index]
                
                # 4. 遍历12个时辰，使用完整起课引擎
                for shi_chen in DIZHI:
                    total_ke_count += 1
                    
                    try:
                        # 使用完整起课引擎计算三传
                        qi_ke_result = self.qi_ke_engine.qi_ke(
                            ri_gan_zhi=ri_ganzhi,
                            yue_jiang=yue_jiang,
                            shi_chen=shi_chen,
                            lunar_month=month,
                            nian_zhi=tai_sui
                        )
                        
                        sanchuan = qi_ke_result.get('三传', {})
                        ke_ti_list = qi_ke_result.get('课体', [])
                        
                    except Exception as e:
                        # 如果起课失败，跳过此时辰
                        continue
                    
                    # 检查龙德课
                    is_long_de, long_de_type = self.long_de_selector.is_long_de_ke(
                        ri_ganzhi, yue_jiang, tai_sui, sanchuan
                    )
                    
                    # 筛选龙德课
                    if only_long_de and not is_long_de:
                        continue
                    
                    # 确定课体名称
                    if is_long_de:
                        ke_ti_name = long_de_type
                    elif ke_ti_list:
                        ke_ti_name = ke_ti_list[0] if isinstance(ke_ti_list, list) else str(ke_ti_list)
                    else:
                        ke_ti_name = '普通课'
                    
                    # 筛选六壬吉课
                    if liuren_ke != '全部' and liuren_ke not in ke_ti_name:
                        continue
                    
                    # 5. 综合评分
                    total_score = kege_score
                    if is_long_de:
                        total_score += 1.0  # 龙德课加分
                    
                    # 6. 获取吉神
                    ji_shen = self._get_ji_shen(year, month, day)
                    
                    # 7. 添加到结果
                    weekday = self._get_weekday(current_date)
                    sizhu_str = f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}"
                    
                    recommendation = self._get_recommendation(total_score)
                    
                    result = {
                        '序号': qualified_count + 1,
                        'date': current_date,
                        '日期': current_date.strftime('%Y-%m-%d'),
                        '星期': weekday,
                        '四柱': sizhu_str,
                        '斗首课格': kege_name,
                        '评分': total_score,
                        '六壬课体': ke_ti_name,
                        '吉神': ji_shen,
                        '推荐': recommendation,
                        '时辰': shi_chen,
                        '三传': sanchuan,
                        'detail': {
                            'sizhu': sizhu,
                            'douhou': douhou_result,
                            'liuren': ke_ti_list,
                            'long_de': long_de_type if is_long_de else None
                        }
                    }
                    
                    self.results.append(result)
                    qualified_count += 1
                    
                    # 更新 UI（使用 after 方法）
                    self.root.after(0, self._add_result_to_tree, result)
                
                current_date += timedelta(days=1)
            
            # 完成
            self.root.after(0, self._selection_complete, qualified_count, total_ke_count)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, self._selection_error, str(e))
    
    def _add_result_to_tree(self, result):
        """添加结果到树形视图"""
        values = (
            result['序号'],
            result['日期'],
            result['星期'],
            result['四柱'],
            result['斗首课格'],
            f"{result['评分']:.1f}",
            result['六壬课体'],
            result['吉神'],
            result['推荐']
        )
        self.result_tree.insert('', tk.END, values=values)
    
    def _selection_complete(self, count, total_ke_count=0):
        """择日完成"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_var.set(100)
        self.progress_label.config(text="完成")
        self.status_label.config(text=f"共遍历{total_ke_count}课，筛选出{count}个吉课")
        
        if count > 0:
            messagebox.showinfo("完成", f"择日完成！\n共遍历{total_ke_count}课，筛选出{count}个吉课")
        else:
            messagebox.showwarning("完成", f"未找到符合条件的日期\n共遍历{total_ke_count}课\n请放宽筛选条件")
    
    def _selection_error(self, error_msg):
        """择日错误"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_label.config(text="错误")
        messagebox.showerror("错误", f"择日过程中发生错误：{error_msg}")
    
    def _stop_selection(self):
        """停止择日"""
        # 这里需要添加停止标志
        self.stop_btn.config(state='disabled')
        self.progress_label.config(text="已停止")
    
    def _clear_results(self):
        """清空结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.results = []
        self.status_label.config(text="共找到 0 个符合条件的日期")
        self.progress_var.set(0)
        self.progress_label.config(text="就绪")
    
    def _show_detail(self, event):
        """显示详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = self.result_tree.item(selection[0])
        values = item['values']
        index = int(values[0]) - 1
        
        if index < 0 or index >= len(self.results):
            return
        
        result = self.results[index]
        detail = result['detail']
        
        # 创建详情窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"详细信息 - {result['日期']}")
        detail_window.geometry("600x500")
        
        # 四柱信息
        info_text = scrolledtext.ScrolledText(detail_window, height=30, width=70)
        info_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        info = f"【{result['日期']} {result['星期']}】\n\n"
        info += f"四柱：{result['四柱']}\n\n"
        info += f"斗首课格：{result['斗首课格']} ({result['评分']:.1f}分)\n"
        info += f"六壬课体：{result['六壬课体']}\n"
        info += f"吉神：{result['吉神']}\n"
        info += f"推荐：{result['推荐']}\n\n"
        
        if detail.get('long_de'):
            info += f"龙德课：{detail['long_de']}\n\n"
        
        if 'duanyu' in detail['douhou']:
            info += f"斗首断语：{detail['douhou']['duanyu']}\n"
        
        info_text.insert(tk.END, info)
        info_text.config(state='disabled')
    
    def _get_weekday(self, date):
        """获取星期"""
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        return f'星期{weekdays[date.weekday()]}'
    
    def _get_recommendation(self, score):
        """获取推荐指数"""
        if score >= 9.0:
            return '★★★★★ 上上大吉'
        elif score >= 8.0:
            return '★★★★☆ 上吉'
        elif score >= 7.0:
            return '★★★☆☆ 中吉'
        elif score >= 6.0:
            return '★★☆☆☆ 小吉'
        else:
            return '★☆☆☆☆ 平'
    
    def _get_ji_shen(self, year, month, day):
        """获取吉神（简化版）"""
        # 这里可以添加完整的吉神计算
        sizhu = get_sizhu_accurate(year, month, day, 12)
        ri_gan = sizhu['日柱'][0]
        ri_zhi = sizhu['日柱'][1]
        
        ji_shen_list = []
        
        # 天德贵人（简化）
        if month in [1, 5, 9] and ri_gan == '丙':
            ji_shen_list.append('月德')
        elif month in [3, 7, 11] and ri_gan == '壬':
            ji_shen_list.append('月德')
        elif month in [4, 8, 12] and ri_gan == '甲':
            ji_shen_list.append('月德')
        elif month in [2, 6, 10] and ri_gan == '庚':
            ji_shen_list.append('月德')
        
        return '、'.join(ji_shen_list) if ji_shen_list else '无'
    
    def _export_results(self):
        """导出结果"""
        if not self.results:
            messagebox.showwarning("警告", "没有结果可导出")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("仪度六壬综合择日结果\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for result in self.results:
                        f.write(f"{result['序号']}. {result['日期']} ({result['星期']})\n")
                        f.write(f"   四柱：{result['四柱']}\n")
                        f.write(f"   斗首课格：{result['斗首课格']} ({result['评分']:.1f}分)\n")
                        f.write(f"   六壬课体：{result['六壬课体']}\n")
                        f.write(f"   吉神：{result['吉神']}\n")
                        f.write(f"   推荐：{result['推荐']}\n\n")
                
                messagebox.showinfo("成功", f"结果已导出到：{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
【使用说明】

1. 选择山向：
   - 从下拉列表中选择坐山和朝向
   - 点击"互换山向"可快速交换

2. 选择日期范围：
   - 输入开始和结束日期（格式：YYYY-MM-DD）
   - 或使用快捷按钮快速设置范围

3. 设置筛选条件：
   - 选择斗首课格类型（元辰、武财等）
   - 设置最低评分（0-10 分）
   - 选择六壬吉课类型（龙德课等）
   - 勾选"仅龙德课"只筛选龙德课

4. 开始择日：
   - 点击"开始择日"按钮
   - 等待计算完成
   - 结果会显示在下方列表中

5. 查看结果：
   - 双击列表项查看详细分析
   - 使用"导出结果"保存为文本文件
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _show_about(self):
        """显示关于"""
        about_text = """
仪度六壬综合择日系统 v1.0

功能特点：
- 支持 24 山向选择
- 斗首择日法（5 种课格）
- 大六壬课体判断（64 课经）
- 龙德课筛选
- 综合评分系统

技术支持：
仪度六壬择日系统开发团队

2026 年 3 月
"""
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = ComprehensiveDateSelectorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
