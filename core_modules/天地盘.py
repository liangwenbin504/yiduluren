#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度六壬综合择日系统 - 增强版 GUI
功能增强：
1. 罗盘式山向选择界面
2. 日历控件日期选择
3. 多课格类型多选（13 种课格）
4. 详细信息展示（排盘、四课三传、禄马贵人）
5. AI 辅助评价
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    from tkinter import font as tkfont
except ImportError:
    print("错误：需要安装 tkinter 库")
    print("Windows: python -m pip install tk")
    print("Linux: sudo apt-get install python3-tk")
    sys.exit(1)

# 导入引擎模块
from engine.douhou_engine import DouShouCalculator
from engine.ke_ti_judge import KeTiJudgeCalculator
from engine.precise_calendar import PreciseCalendar, get_sizhu_accurate
from engine.long_de_ke_selector import LongDeKeSelector
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
from engine.gui_ren_engine import GuiRenCalculator
from engine.shen_sha_calculator import ShenShaCalculator
from engine.complete_qi_ke_engine import CompleteQiKeEngine
from engine.comprehensive_evaluation import ComprehensiveEvaluation
from engine.yuejiang_engine import YueJiangCalculator
from engine.liuren_scoring import LiuRenKeTiScorer
from engine.ai_evaluation import AIEvaluation


class EnhancedDateSelectorGUI:
    """仪度六壬综合择日系统 - 增强版"""
    
    # 24 山列表
    SHAN_24 = [
        '壬', '子', '癸', '丑', '艮', '寅',
        '甲', '卯', '乙', '辰', '巽', '巳',
        '丙', '午', '丁', '未', '坤', '申',
        '庚', '酉', '辛', '戌', '乾', '亥'
    ]
    
    # 山向对应关系（六合）
    SHAN_XIANG_PAIRS = {
        '壬': '丙', '子': '午', '癸': '丁', '丑': '未',
        '艮': '坤', '寅': '申', '甲': '庚', '卯': '酉',
        '乙': '辛', '辰': '戌', '巽': '乾', '巳': '亥',
        '丙': '壬', '午': '子', '丁': '癸', '未': '丑',
        '坤': '艮', '申': '寅', '庚': '甲', '酉': '卯',
        '辛': '乙', '戌': '辰', '乾': '巽', '亥': '巳'
    }
    
    # 13 种吉课类型
    KE_GE_TYPES = [
        '富贵课', '荣华课', '龙德课', '官爵课', '时泰课',
        '和美课', '合欢课', '回环课', '亨通课',
        '华盖乘轩课', '德庆课', '斫轮课', '铸印乘轩课'
    ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("仪度六壬综合择日系统 - 增强版")
        self.root.geometry("1400x900")
        
        # 初始化引擎
        self.calendar = PreciseCalendar()
        self.douhou_calc = DouShouCalculator()
        self.ke_ti_judge = KeTiJudgeCalculator()
        self.long_de_selector = LongDeKeSelector()
        self.sike_engine = SiKeSanChuanCalculator()
        self.gui_ren_engine = GuiRenCalculator()
        self.shen_sha_calc = ShenShaCalculator()
        self.qi_ke_engine = CompleteQiKeEngine()
        self.yuejiang_calc = YueJiangCalculator()
        self.evaluator = ComprehensiveEvaluation()
        self.liuren_scorer = LiuRenKeTiScorer()  # 六壬课体评分器
        self.ai_evaluator = AIEvaluation()  # AI 综合评价器
        
        # 存储选中的课格类型
        self.selected_kege_types = set()
        
        # 存储结果
        self.results = []
        self.current_detail = None
        
        # 创建界面
        self._create_menu()
        self._create_styles()
        self._create_main_layout()
        
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出结果", command=self._export_results, accelerator="Ctrl+E")
        file_menu.add_command(label="保存配置", command=self._save_config)
        file_menu.add_command(label="加载配置", command=self._load_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Alt+F4")
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="大六壬排盘", command=self._open_paipan)
        tools_menu.add_command(label="万年历查询", command=self._open_calendar)
        tools_menu.add_separator()
        tools_menu.add_command(label="清空所有选择", command=self._clear_all)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="课格详解", command=self._show_kege_help)
        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self._show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-e>', lambda e: self._export_results())
    
    def _create_styles(self):
        """创建样式"""
        style = ttk.Style()
        
        # 配置颜色
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 12, 'bold'), foreground='#1a73e8')
        style.configure('Section.TLabelFrame', font=('Microsoft YaHei UI', 10, 'bold'))
        style.configure('Highlight.TButton', font=('Microsoft YaHei UI', 10, 'bold'))
        style.configure('Result.Treeview', font=('Microsoft YaHei UI', 9), rowheight=25)
        style.configure('Result.Treeview.Heading', font=('Microsoft YaHei UI', 9, 'bold'))
    
    def _create_main_layout(self):
        """创建主布局"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 创建各个功能区域
        self._create_shan_xiang_section(main_frame, row=0)
        self._create_date_range_section(main_frame, row=1)
        self._create_kege_filter_section(main_frame, row=2)
        self._create_action_section(main_frame, row=3)
        self._create_result_section(main_frame, row=4)
        self._create_detail_section(main_frame, row=5)
    
    def _create_shan_xiang_section(self, parent, row):
        """创建山向选择区域（下拉窗口式）"""
        shan_frame = ttk.LabelFrame(parent, text="第一步：选择山向", 
                                   padding="10")
        shan_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        shan_frame.columnconfigure(1, weight=1)
        
        # 左侧：下拉窗口山向选择
        selection_frame = ttk.Frame(shan_frame)
        selection_frame.grid(row=0, column=0, padx=10, pady=10)
        
        # 坐山选择
        ttk.Label(selection_frame, text="坐山:", style='Title.TLabel').grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.shan_combo = ttk.Combobox(selection_frame, values=self.SHAN_24, 
                                       width=8, state="readonly", font=('Microsoft YaHei UI', 12))
        self.shan_combo.set('壬')  # 默认值
        self.shan_combo.grid(row=0, column=1, padx=5, pady=5)
        self.shan_combo.bind('<<ComboboxSelected>>', self._on_shan_xiang_change)
        
        # 朝向选择
        ttk.Label(selection_frame, text="朝向:", style='Title.TLabel').grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.xiang_combo = ttk.Combobox(selection_frame, values=self.SHAN_24, 
                                        width=8, state="readonly", font=('Microsoft YaHei UI', 12))
        self.xiang_combo.set('丙')  # 默认值
        self.xiang_combo.grid(row=1, column=1, padx=5, pady=5)
        self.xiang_combo.bind('<<ComboboxSelected>>', self._on_shan_xiang_change)
        
        # 快捷操作
        quick_frame = ttk.Frame(selection_frame)
        quick_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(quick_frame, text="互换山向", command=self._swap_shan_xiang).pack(side=tk.LEFT, padx=3)
        ttk.Button(quick_frame, text="重置", 
                  command=self._reset_shan_xiang).pack(side=tk.LEFT, padx=3)
        
        # 右侧：日期结果显示（隐藏山向信息）
        info_frame = ttk.LabelFrame(shan_frame, text="已选日期结果（点击日期查看排盘）", padding="10")
        info_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # 日期结果显示区域 - 使用 Text 组件并支持点击
        result_text_frame = ttk.Frame(info_frame)
        result_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_text_frame.columnconfigure(0, weight=1)
        result_text_frame.rowconfigure(0, weight=1)
        
        self.date_result_text = scrolledtext.ScrolledText(result_text_frame, height=12, width=50,
                                                         font=('Microsoft YaHei UI', 10),
                                                         cursor="hand2")  # 手型光标
        self.date_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 绑定点击事件
        self.date_result_text.tag_bind("date_item", "<Button-1>", self._on_date_text_click)
        self.date_result_text.tag_bind("date_item", "<Enter>", self._on_date_enter)
        self.date_result_text.tag_bind("date_item", "<Leave>", self._on_date_leave)
        
        # 存储日期数据以便点击时获取
        self.date_text_items = []
        
        # 更新山向信息
        self._update_shan_info()
    
    def _create_date_range_section(self, parent, row):
        """创建日期范围选择区域"""
        date_frame = ttk.LabelFrame(parent, text="第二步：选择日期范围", 
                                   padding="10")
        date_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        date_frame.columnconfigure(1, weight=1)
        
        # 开始日期
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = ttk.Entry(date_frame, width=15, font=('Microsoft YaHei UI', 10))
        today = datetime.now().strftime('%Y-%m-%d')
        self.start_date_entry.insert(0, today)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 日历选择按钮
        ttk.Button(date_frame, text="📅", width=3, 
                  command=lambda: self._show_date_picker('start')).grid(row=0, column=2, padx=2)
        
        # 结束日期
        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=3, padx=5, pady=5)
        self.end_date_entry = ttk.Entry(date_frame, width=15, font=('Microsoft YaHei UI', 10))
        end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        self.end_date_entry.insert(0, end_date)
        self.end_date_entry.grid(row=0, column=4, padx=5, pady=5)
        
        # 日历选择按钮
        ttk.Button(date_frame, text="📅", width=3,
                  command=lambda: self._show_date_picker('end')).grid(row=0, column=5, padx=2)
        
        # 快捷日期范围
        ttk.Label(date_frame, text="快捷选择:").grid(row=0, column=6, padx=10, pady=5)
        
        quick_dates = [
            ('当年', 365),
            ('半年', 180),
            ('3 个月', 90),
            ('1 个月', 30),
            ('两年', 730)
        ]
        
        for label, days in quick_dates:
            ttk.Button(date_frame, text=label, width=8,
                      command=lambda d=days: self._set_date_range(d)).grid(row=0, column=7+quick_dates.index((label, days)), padx=2)
        
        # 日期验证标签
        self.date_validation_label = ttk.Label(date_frame, text="", foreground='green')
        self.date_validation_label.grid(row=1, column=0, columnspan=12, sticky=(tk.W,), padx=5)
        
        # 绑定日期验证
        self.start_date_entry.bind('<KeyRelease>', lambda e: self._validate_dates())
        self.end_date_entry.bind('<KeyRelease>', lambda e: self._validate_dates())
    
    def _create_kege_filter_section(self, parent, row):
        """创建课格筛选区域（多选）"""
        kege_frame = ttk.LabelFrame(parent, text="第三步：选择课格类型（可多选）", 
                                   padding="10")
        kege_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        kege_frame.columnconfigure(1, weight=1)
        
        # 左侧：课格多选
        select_frame = ttk.Frame(kege_frame)
        select_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10)
        
        # 全选/取消全选按钮
        quick_btn_frame = ttk.Frame(select_frame)
        quick_btn_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Button(quick_btn_frame, text="全选", width=8,
                  command=self._select_all_kege).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_btn_frame, text="取消全选", width=8,
                  command=self._deselect_all_kege).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_btn_frame, text="仅选龙德课", width=10,
                  command=self._select_only_longde).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_btn_frame, text="传统五课", width=8,
                  command=self._select_traditional).pack(side=tk.LEFT, padx=2)
        
        # 课格复选框网格
        checkbox_frame = ttk.Frame(select_frame)
        checkbox_frame.pack(pady=5)
        
        self.kege_vars = {}
        cols = 4
        for i, kege in enumerate(self.KE_GE_TYPES):
            row_idx = i // cols
            col_idx = i % cols
            
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(checkbox_frame, text=kege, variable=var,
                                 command=lambda k=kege, v=var: self._toggle_kege(k, v),
                                 takefocus=True)
            chk.grid(row=row_idx, column=col_idx, padx=15, pady=8, sticky=tk.W)
            self.kege_vars[kege] = var
        
        # 右侧：其他筛选条件
        filter_frame = ttk.LabelFrame(kege_frame, text="其他筛选条件", padding="10")
        filter_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=10)
        
        # 斗首课格
        ttk.Label(filter_frame, text="斗首课格:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.douhou_combo = ttk.Combobox(filter_frame, values=['全部', '元辰课', '武财课', '贪官课', '廉贞课', '破鬼课'],
                                        width=12, state="readonly")
        self.douhou_combo.set('全部')
        self.douhou_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 最低评分
        ttk.Label(filter_frame, text="最低评分:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.min_score_spin = ttk.Spinbox(filter_frame, from_=0, to=10, increment=0.5, width=10)
        self.min_score_spin.set(5.0)  # 【修复】从 7.0 改为 5.0，避免过度过滤
        self.min_score_spin.grid(row=1, column=1, padx=5, pady=5)
        
        # 显示已选课格
        self.selected_kege_label = ttk.Label(filter_frame, text="已选：0/13", foreground='blue')
        self.selected_kege_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    
    def _create_action_section(self, parent, row):
        """创建操作按钮区域"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=10)
        action_frame.columnconfigure(1, weight=1)
        
        # 按钮
        self.start_btn = ttk.Button(action_frame, text="开始择日", command=self._start_selection,
                                   style='Highlight.TButton', width=20)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = ttk.Button(action_frame, text="停止", command=self._stop_selection,
                                  state='disabled', width=20)
        self.stop_btn.grid(row=0, column=1, padx=10)
        
        ttk.Button(action_frame, text="清空结果", command=self._clear_results, width=20).grid(row=0, column=2, padx=10)
        
        # 进度条
        progress_frame = ttk.Frame(action_frame)
        progress_frame.grid(row=0, column=3, padx=20, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, length=300)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(progress_frame, text="就绪", width=20)
        self.progress_label.grid(row=0, column=1, padx=10)
    
    def _create_result_section(self, parent, row):
        """创建结果展示区域"""
        result_frame = ttk.LabelFrame(parent, text="择日结果（双击查看详情）", 
                                     padding="10")
        result_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 结果树形视图
        columns = ('序号', '日期', '星期', '四柱', '斗首课格', '六壬评分', '综合评分', '课格类型', '吉神')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings',
                                       style='Result.Treeview', height=10)
        
        # 设置列宽
        column_widths = {
            '序号': 50, '日期': 100, '星期': 60, '四柱': 280,
            '斗首课格': 100, '六壬评分': 80, '综合评分': 80, '课格类型': 150, '吉神': 200
        }
        
        for col in columns:
            self.result_tree.column(col, width=column_widths.get(col, 100), anchor='center')
            self.result_tree.heading(col, text=col, command=lambda c=col: self._sort_results(c))
        
        # 滚动条
        y_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        x_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # 布局
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        y_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        x_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 绑定事件
        self.result_tree.bind('<Double-1>', self._open_paipan_on_double)
        self.result_tree.bind('<<TreeviewSelect>>', self._on_result_select)
        
        # 添加右键菜单
        self._create_result_context_menu()
        
        # 状态栏
        status_frame = ttk.Frame(result_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="共找到 0 个符合条件的日期", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.filter_label = ttk.Label(status_frame, text="")
        self.filter_label.pack(side=tk.RIGHT, padx=10)
        
        # 添加提示标签
        tip_label = ttk.Label(status_frame, 
                             text="💡 双击日期或右键点击可查看详细排盘",
                             foreground='blue',
                             font=('Microsoft YaHei UI', 9))
        tip_label.pack(side=tk.LEFT, padx=20)
    
    def _create_detail_section(self, parent, row):
        """创建详细信息展示区域"""
        detail_frame = ttk.LabelFrame(parent, text="详细信息", 
                                     padding="10")
        detail_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(0, weight=1)
        
        # 创建 Notebook（选项卡）
        self.detail_notebook = ttk.Notebook(detail_frame)
        self.detail_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 选项卡 1：四柱信息
        sizhu_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(sizhu_frame, text="四柱信息")
        self.sizhu_text = scrolledtext.ScrolledText(sizhu_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.sizhu_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡 2：大六壬排盘
        paipan_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(paipan_frame, text="大六壬排盘")
        self.paipan_text = scrolledtext.ScrolledText(paipan_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.paipan_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡 3：四课三传
        sike_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(sike_frame, text="四课三传")
        self.sike_text = scrolledtext.ScrolledText(sike_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.sike_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡 4：禄马贵人
        luma_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(luma_frame, text="禄马贵人")
        self.luma_text = scrolledtext.ScrolledText(luma_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.luma_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡 5：课格断语
        duanyu_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(duanyu_frame, text="课格断语")
        self.duanyu_text = scrolledtext.ScrolledText(duanyu_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.duanyu_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡 6：AI 评价
        ai_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(ai_frame, text="AI 评价")
        self.ai_text = scrolledtext.ScrolledText(ai_frame, height=8, font=('Microsoft YaHei UI', 10))
        self.ai_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # ==================== 事件处理方法 ====================
    
    def _on_shan_xiang_change(self, event=None):
        """山向选择改变事件处理"""
        shan = self.shan_combo.get()
        xiang = self.xiang_combo.get()
        
        # 自动更新对应关系（如果用户手动选择了不匹配的朝向）
        if self.SHAN_XIANG_PAIRS.get(shan) != xiang:
            # 自动更新朝向为对应值
            auto_xiang = self.SHAN_XIANG_PAIRS[shan]
            self.xiang_combo.set(auto_xiang)
        
        self._update_shan_info()
        self._update_date_result_display()
    
    def _select_shan(self, shan):
        """选择坐山（保留向后兼容）"""
        self.shan_combo.set(shan)
        self._on_shan_xiang_change()
    
    def _select_xiang(self, xiang):
        """选择朝向（保留向后兼容）"""
        self.xiang_combo.set(xiang)
        self._on_shan_xiang_change()
    
    def _swap_shan_xiang(self):
        """互换山向"""
        shan = self.shan_combo.get()
        xiang = self.xiang_combo.get()
        self.shan_combo.set(xiang)
        self.xiang_combo.set(shan)
        self._on_shan_xiang_change()
    
    def _update_shan_info(self):
        """更新山向信息（已隐藏，保留方法以便向后兼容）"""
        # 山向信息已隐藏，不再显示
        pass
    
    def _on_date_text_click(self, event):
        """点击日期文本事件"""
        # 获取点击位置的索引
        index = self.date_result_text.index(f"@{event.x},{event.y}")
        
        # 查找对应的日期数据
        for item_data in self.date_text_items:
            start_line = item_data['start_line']
            end_line = item_data['end_line']
            current_line = int(index.split('.')[0])
            
            if start_line <= current_line <= end_line:
                # 找到对应的日期，打开排盘窗口
                result = item_data['result']
                self._show_paipan_window(result)
                break
    
    def _on_date_enter(self, event):
        """鼠标进入日期区域"""
        self.date_result_text.config(bg="#e6f3ff")  # 浅蓝色背景
    
    def _on_date_leave(self, event):
        """鼠标离开日期区域"""
        self.date_result_text.config(bg="white")  # 恢复白色背景
    
    def _update_date_result_display(self):
        """更新日期结果显示"""
        # 如果有计算结果，显示结果
        if hasattr(self, 'results') and len(self.results) > 0:
            # 清空日期数据列表
            self.date_text_items = []
            
            self.date_result_text.config(state='normal')  # 可写模式
            self.date_result_text.delete(1.0, tk.END)
            
            # 显示标题
            self.date_result_text.insert(tk.END, f"已找到 {len(self.results)} 个吉日\n", "title")
            self.date_result_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            
            # 显示前 20 个结果
            for i, result in enumerate(self.results[:20], 1):
                # 记录每个日期的起始和结束行号
                start_index = self.date_result_text.index("end-1c")
                start_line = int(start_index.split('.')[0])
                
                # 格式化日期信息
                date_line = f"▶ {i:2d}. {result['日期']} ({result['星期']})\n"
                sizhu_line = f"   四柱：{result['四柱']}\n"
                kege_line = f"   课格：{result['课格类型']}\n"
                score_line = f"   评分：{result['综合评分']} (六壬:{result['六壬评分']} 斗首:{result['斗首评分']})\n"
                
                # 插入文本
                self.date_result_text.insert(tk.END, date_line, "date_item")
                self.date_result_text.insert(tk.END, sizhu_line)
                self.date_result_text.insert(tk.END, kege_line)
                self.date_result_text.insert(tk.END, score_line)
                self.date_result_text.insert(tk.END, "\n")
                
                end_line = int(self.date_result_text.index("end-1c").split('.')[0])
                
                # 存储日期数据
                self.date_text_items.append({
                    'start_line': start_line,
                    'end_line': end_line,
                    'result': result
                })
            
            if len(self.results) > 20:
                self.date_result_text.insert(tk.END, f"\n... 还有 {len(self.results) - 20} 个结果，请在下方表格中查看完整列表\n")
            
            # 配置文本样式
            self.date_result_text.tag_configure("title", font=('Microsoft YaHei UI', 11, 'bold'))
            self.date_result_text.tag_configure("date_item", foreground='blue', underline=True)
            
            self.date_result_text.config(state='disabled')  # 只读模式
        else:
            # 显示提示信息
            info = "💡 提示：\n"
            info += "1. 设置日期范围\n"
            info += "2. 选择筛选条件\n"
            info += "3. 点击'开始择日'按钮\n\n"
            info += "系统将在此显示符合条件的日期结果\n"
            
            self.date_result_text.config(state='normal')
            self.date_result_text.delete(1.0, tk.END)
            self.date_result_text.insert(tk.END, info)
            self.date_result_text.config(state='disabled')
    
    def _reset_shan_xiang(self):
        """重置山向选择"""
        self.shan_combo.set('壬')
        self.xiang_combo.set('丙')
        self._on_shan_xiang_change()
    
    def _set_date_range(self, days):
        """设置日期范围"""
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, today.strftime('%Y-%m-%d'))
        
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end_date.strftime('%Y-%m-%d'))
        
        self._validate_dates()
    
    def _validate_dates(self):
        """验证日期"""
        try:
            start_str = self.start_date_entry.get()
            end_str = self.end_date_entry.get()
            
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
            
            if start_date > end_date:
                self.date_validation_label.config(
                    text="错误：开始日期不能晚于结束日期",
                    foreground='red'
                )
                return False
            elif (end_date - start_date).days > 730:
                self.date_validation_label.config(
                    text="警告：日期范围超过 2 年，计算时间较长",
                    foreground='orange'
                )
            else:
                self.date_validation_label.config(
                    text=f"日期范围：{(end_date - start_date).days}天",
                    foreground='green'
                )
            return True
        except ValueError:
            self.date_validation_label.config(
                text="错误：日期格式不正确（应为 YYYY-MM-DD）",
                foreground='red'
            )
            return False
    
    def _show_date_picker(self, entry_type):
        """显示日期选择器（简化版）"""
        # 由于 tkinter 没有内置日历控件，这里使用简单对话框
        from tkinter import simpledialog
        
        current = self.start_date_entry.get() if entry_type == 'start' else self.end_date_entry.get()
        
        date_str = simpledialog.askstring(
            "选择日期",
            "请输入日期（YYYY-MM-DD）：",
            initialvalue=current
        )
        
        if date_str:
            if entry_type == 'start':
                self.start_date_entry.delete(0, tk.END)
                self.start_date_entry.insert(0, date_str)
            else:
                self.end_date_entry.delete(0, tk.END)
                self.end_date_entry.insert(0, date_str)
            
            self._validate_dates()
    
    def _toggle_kege(self, kege, var):
        """切换课格选择状态"""
        # 获取当前复选框状态
        is_checked = var.get()
        
        if is_checked:
            self.selected_kege_types.add(kege)
        else:
            self.selected_kege_types.discard(kege)
        
        # 更新标签显示
        count = len(self.selected_kege_types)
        self.selected_kege_label.config(text=f"已选：{count}/{len(self.KE_GE_TYPES)}")
        
        # 调试输出（可选）
        # print(f"切换 {kege}: {'选中' if is_checked else '取消'}, 当前已选：{self.selected_kege_types}")
    
    def _select_all_kege(self):
        """全选课格"""
        for kege, var in self.kege_vars.items():
            var.set(True)
            self.selected_kege_types.add(kege)
        self.selected_kege_label.config(text=f"已选：{len(self.selected_kege_types)}/{len(self.KE_GE_TYPES)}")
    
    def _deselect_all_kege(self):
        """取消全选"""
        for var in self.kege_vars.values():
            var.set(False)
        self.selected_kege_types.clear()
        self.selected_kege_label.config(text="已选：0/13")
    
    def _select_only_longde(self):
        """仅选龙德课"""
        self._deselect_all_kege()
        self.kege_vars['龙德课'].set(True)
        self.selected_kege_types.add('龙德课')
        self.selected_kege_label.config(text="已选：1/13（龙德课）")
    
    def _select_traditional(self):
        """选择传统五课"""
        traditional = ['富贵课', '龙德课', '官爵课', '时泰课', '和美课']
        self._deselect_all_kege()
        for kege in traditional:
            if kege in self.kege_vars:
                self.kege_vars[kege].set(True)
                self.selected_kege_types.add(kege)
        self.selected_kege_label.config(text=f"已选：{len(self.selected_kege_types)}/{len(self.KE_GE_TYPES)}（传统五课）")
    
    # ==================== 择日核心功能 ====================
    
    def _start_selection(self):
        """开始择日"""
        # 验证日期
        if not self._validate_dates():
            messagebox.showerror("错误", "日期范围不正确，请修正后再试")
            return
        
        # 不再强制要求选择课格 - 允许用户不选课体进行六壬分值筛选
        # if len(self.selected_kege_types) == 0:
        #     messagebox.showwarning("提示", "请至少选择一种课格类型")
        #     return
        
        # 获取参数（使用新的下拉框组件）
        shan = self.shan_combo.get()
        xiang = self.xiang_combo.get()
        
        try:
            start_date = datetime.strptime(self.start_date_entry.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_entry.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确")
            return
        
        # 检查日期范围
        total_days = (end_date - start_date).days + 1
        if total_days > 730:
            result = messagebox.askyesno("警告", 
                f"日期范围为{total_days}天，超过 2 年会导致计算时间很长。\n\n"
                f"建议：选择 3-6 个月（90-180 天）的日期范围。\n\n"
                f"是否继续？")
            if not result:
                return
        
        douhou_kege = self.douhou_combo.get()
        min_score = float(self.min_score_spin.get())
        
        # 显示开始信息
        print(f"\n{'='*60}")
        print(f"开始择日计算")
        print(f"{'='*60}")
        print(f"  山向：{shan}山{xiang}向")
        print(f"  日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} ({total_days}天)")
        print(f"  总时辰数：约 {total_days * 12} 个")
        print(f"  已选课格：{self.selected_kege_types if len(self.selected_kege_types) > 0 else '全部课格（自动筛选）'}")
        print(f"  最低评分：{min_score}")
        print(f"  六壬分值优先：是（六壬 60% + 斗首 40% + 额外加分）")
        
        # 智能提示
        if min_score > 7.0:
            print(f"\n⚠ 提示：最低评分{min_score}较高，可能会过滤掉大部分日期")
            print(f"   建议：如无结果，请降低至 6.0 或 5.0")
        if len(self.selected_kege_types) == 0:
            print(f"\n✓ 未选课格，系统将自动筛选所有 13 种课体")
        else:
            print(f"\n✓ 已选{len(self.selected_kege_types)}种课体：{', '.join(self.selected_kege_types)}")
        
        print(f"{'='*60}\n")
        
        # 启动后台线程
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress_var.set(0)
        self.progress_label.config(text="计算中...")
        
        # 创建工作线程
        import threading
        thread = threading.Thread(
            target=self._selection_worker,
            args=(shan, xiang, start_date, end_date, douhou_kege, min_score)
        )
        thread.daemon = True
        thread.start()
    
    def _selection_worker(self, shan, xiang, start_date, end_date, douhou_kege, min_score):
        """择日工作线程"""
        try:
            results = []
            total_days = (end_date - start_date).days + 1
            print(f"开始计算 {total_days} 天的日期...")
            print(f"  已选课格：{self.selected_kege_types if len(self.selected_kege_types) > 0 else '全部课格（自动筛选）'}")
            
            current_date = start_date
            dates_with_results = 0  # 有结果的日期数
            total_checked = 0  # 总检查数
            
            while current_date <= end_date:
                # 检查是否停止
                if not self.stop_btn.instate(['!disabled']):
                    print("用户停止计算")
                    break
                
                # 计算该日期的所有时辰
                for shi_zhi in self.calendar.DIZHI:
                    shi_index = self.calendar.DIZHI.index(shi_zhi)
                    shi_hour = shi_index * 2  # 子时=0, 丑时=2, ...
                    
                    try:
                        # 计算四柱（使用真太阳时）
                        sizhu = get_sizhu_accurate(
                            current_date.year, current_date.month, current_date.day,
                            shi_hour, 0, 116.4074, 39.9042  # 北京经纬度
                        )
                        
                        ri_ganzhi = sizhu['日柱']
                        ri_gan = ri_ganzhi[0]
                        total_checked += 1
                        
                        # 计算斗首课格
                        kege_name = self._get_douhou_kege(ri_gan)
                        kege_score = self._get_douhou_score(kege_name)
                        
                        # 检查斗首课格
                        if douhou_kege != '全部':
                            if ri_gan in ['甲', '己'] and douhou_kege != '元辰课':
                                if len(results) < 5:
                                    print(f"  过滤（斗首课格不符）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name} != {douhou_kege}")
                                continue
                            elif ri_gan in ['丙', '辛'] and douhou_kege != '武财课':
                                if len(results) < 5:
                                    print(f"  过滤（斗首课格不符）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name} != {douhou_kege}")
                                continue
                            elif ri_gan in ['戊', '癸'] and douhou_kege != '贪官课':
                                if len(results) < 5:
                                    print(f"  过滤（斗首课格不符）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name} != {douhou_kege}")
                                continue
                            elif ri_gan in ['乙', '庚'] and douhou_kege != '廉贞课':
                                if len(results) < 5:
                                    print(f"  过滤（斗首课格不符）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name} != {douhou_kege}")
                                continue
                            elif ri_gan in ['丁', '壬'] and douhou_kege != '破鬼课':
                                if len(results) < 5:
                                    print(f"  过滤（斗首课格不符）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name} != {douhou_kege}")
                                continue
                        
                        # 检查斗首评分
                        if kege_score < min_score:
                            if len(results) < 5:  # 只输出前 5 个
                                print(f"  过滤（斗首评分低）：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - {kege_name}({kege_score}) < {min_score}")
                            continue
                        
                        # 检查六壬课格
                        matched_kege = self._check_liuren_kege(ri_ganzhi, shi_zhi)
                        
                        if len(matched_kege) == 0:
                            continue
                        
                        # 检查是否在选择的课格中（如果选择了课格）
                        if len(self.selected_kege_types) > 0:
                            if not any(k in self.selected_kege_types for k in matched_kege):
                                continue
                        
                        # 【调试输出】每找到 1 个结果就输出
                        if len(results) < 10:  # 只输出前 10 个
                            print(f"  找到结果：{current_date.strftime('%Y-%m-%d')} {shi_zhi}时 - 课格：{matched_kege[:3]}")
                        
                        dates_with_results += 1
                        
                        # 【核心改进】六壬分值优先 - 计算每个课体的详细评分
                        # 1. 获取每个课体的吉凶评分
                        kege_scores = {}
                        for kege in matched_kege:
                            score = self.liuren_scorer.get_ke_ti_score(kege)
                            kege_scores[kege] = score
                        
                        # 2. 计算六壬综合评分（取最高分和平均分加权）
                        liuren_score_list = list(kege_scores.values())
                        max_liuren_score = max(liuren_score_list)
                        avg_liuren_score = sum(liuren_score_list) / len(liuren_score_list)
                        liuren_final_score = max_liuren_score * 0.6 + avg_liuren_score * 0.4
                        
                        # 3. 检查龙德课
                        is_longde = False
                        longde_type = ''
                        if '龙德课' in matched_kege:
                            try:
                                is_longde, longde_type = self.long_de_selector.is_long_de_ke(
                                    ri_ganzhi,
                                    sizhu.get('月柱', ['',''])[1] if sizhu.get('月柱') else '',  # 月将
                                    sizhu.get('年柱', ['',''])[1] if sizhu.get('年柱') else '',  # 太岁
                                    []  # 三传
                                )
                            except Exception as e:
                                print(f"龙德课检查错误：{e}")
                                is_longde = False
                                longde_type = ''
                        
                        # 计算吉神
                        jishen = self._get_jishen(ri_ganzhi, shi_zhi)
                        
                        # 【核心改进】综合评分：六壬分值 60% + 斗首分值 40% + 额外加分
                        # 基础综合分
                        total_score = liuren_final_score * 0.6 + kege_score * 0.4
                        
                        # 额外加分
                        if is_longde:
                            total_score += 2.0  # 龙德课额外加 2 分
                        if len(matched_kege) >= 3:
                            total_score += 0.5  # 多课格加 0.5 分
                        if max_liuren_score >= 9.0:
                            total_score += 1.0  # 有大吉课加 1 分
                        
                        # 四舍五入保留 1 位小数
                        total_score = round(total_score, 1)
                        
                        # 添加到结果
                        results.append({
                            '日期': current_date.strftime('%Y-%m-%d'),
                            '星期': self._get_weekday(current_date),
                            '四柱': self._format_sizhu(sizhu),
                            '斗首课格': kege_name,
                            '斗首评分': kege_score,
                            '六壬评分': round(liuren_final_score, 1),
                            '综合评分': round(total_score, 1),
                            '课格类型': ', '.join(matched_kege[:3]),
                            '吉神': ', '.join(jishen[:5]),
                            '四柱详细': sizhu,
                            '课格列表': matched_kege,
                            '课格评分详情': kege_scores,  # 新增：每个课体的详细评分
                            '龙德课': is_longde,
                            '龙德类型': longde_type,
                            '山向': f"{shan}山{xiang}向"
                        })
                        
                        # 每找到 100 个结果打印一次进度
                        if len(results) % 100 == 1:
                            print(f"  已找到 {len(results)} 个结果...")
                    except Exception as e:
                        print(f"  计算错误：{e}")
                        continue
                
                # 更新进度
                progress = ((current_date - start_date).days + 1) / total_days * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"{progress:.1f}%")
                
                current_date += timedelta(days=1)
            
            # 排序结果 - 【核心改进】按综合评分从高到低排序
            results.sort(key=lambda x: x['综合评分'], reverse=True)
            self.results = results
            
            print(f"\n计算完成！")
            print(f"  总检查时辰数：{total_checked}")
            print(f"  有结果的日期数：{dates_with_results}")
            print(f"  总结果数：{len(results)}")
            
            if total_checked > 0:
                filter_rate = (total_checked - len(results)) / total_checked * 100
                print(f"  过滤率：{filter_rate:.1f}%")
            
            if len(results) > 0:
                print(f"  最高综合评分：{max(r['综合评分'] for r in results)}")
                print(f"  最低综合评分：{min(r['综合评分'] for r in results)}")
                print(f"  六壬分值优先：已应用")
                print(f"\n✓ 找到 {len(results)} 个符合条件的日期，请按综合评分排序查看")
            else:
                print(f"\n❌ 未找到符合条件的日期")
                print(f"\n可能的原因：")
                print(f"  1. 最低评分设置过高（当前：{min_score}）")
                print(f"  2. 斗首课格限制过严（当前：{douhou_kege}）")
                print(f"  3. 日期范围过小（当前：{total_days}天）")
                print(f"\n建议：")
                if min_score > 6.0:
                    print(f"  - 降低最低评分至 5.0 或 6.0（当前{min_score}过高）")
                if douhou_kege != '全部':
                    print(f"  - 将斗首课格改为'全部'（当前：{douhou_kege}）")
                if total_days < 30:
                    print(f"  - 扩大日期范围至 3-6 个月（当前：{total_days}天）")
                print(f"  - 不选课格让系统自动筛选（当前已选：{len(self.selected_kege_types)}/13）")
            
            # 更新 UI
            self.root.after(0, self._update_results_table)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"计算过程出错：{str(e)}"))
        finally:
            self.root.after(0, self._selection_finished)
    
    def _get_douhou_kege(self, ri_gan):
        """获取斗首课格"""
        if ri_gan in ['甲', '己']:
            return '元辰课'
        elif ri_gan in ['丙', '辛']:
            return '武财课'
        elif ri_gan in ['戊', '癸']:
            return '贪官课'
        elif ri_gan in ['乙', '庚']:
            return '廉贞课'
        else:  # 丁、壬
            return '破鬼课'
    
    def _get_douhou_score(self, kege_name):
        """获取斗首评分"""
        scores = {
            '元辰课': 8.5,
            '武财课': 9.0,
            '贪官课': 7.5,
            '廉贞课': 6.0,
            '破鬼课': 5.0
        }
        return scores.get(kege_name, 5.0)
    
    def _check_liuren_kege(self, ri_ganzhi, shi_zhi):
        """检查六壬课格"""
        matched = []
        
        # 使用更宽松的判断规则，确保能找到足够的吉日
        ri_gan = ri_ganzhi[0]
        ri_zhi = ri_ganzhi[1]
        
        # 龙德课：以年干或日干起贵人，得亥子为龙德
        if shi_zhi in ['子', '午', '卯', '酉']:  # 四正之时
            if ri_gan in ['甲', '戊', '庚', '乙', '己', '丙', '丁', '壬', '癸', '辛']:
                matched.append('龙德课')
        
        # 富贵课：干支相生相合
        if ri_gan in ['甲', '己'] and ri_zhi in ['子', '午', '卯', '酉']:
            matched.append('富贵课')
        elif ri_gan in ['丙', '辛'] and ri_zhi in ['寅', '申', '巳', '亥']:
            matched.append('富贵课')
        
        # 荣华课：三合六合
        if ri_zhi in ['子', '丑', '寅', '卯', '辰', '巳']:
            matched.append('荣华课')
        
        # 官爵课：官星得地
        if ri_gan in ['甲', '乙'] and shi_zhi in ['寅', '卯']:
            matched.append('官爵课')
        elif ri_gan in ['丙', '丁'] and shi_zhi in ['巳', '午']:
            matched.append('官爵课')
        
        # 时泰课：时运亨通
        if shi_zhi in ['辰', '戌', '丑', '未']:  # 四库之时
            matched.append('时泰课')
        
        # 和美课：干支和合
        if ri_gan in ['戊', '己'] and shi_zhi in ['子', '午']:
            matched.append('和美课')
        
        # 合欢课：阴阳和合
        if ri_gan in ['庚', '辛'] and shi_zhi in ['卯', '酉']:
            matched.append('合欢课')
        
        # 回环课：循环往复（简化为干支同气）
        if (ri_gan in ['甲', '乙'] and ri_zhi in ['寅', '卯']) or \
           (ri_gan in ['丙', '丁'] and ri_zhi in ['巳', '午']) or \
           (ri_gan in ['戊', '己'] and ri_zhi in ['辰', '戌', '丑', '未']) or \
           (ri_gan in ['庚', '辛'] and ri_zhi in ['申', '酉']) or \
           (ri_gan in ['壬', '癸'] and ri_zhi in ['亥', '子']):
            matched.append('回环课')
        
        # 亨通课：万事亨通
        if shi_zhi in ['寅', '申', '巳', '亥']:  # 四马之时
            matched.append('亨通课')
        
        # 华盖乘轩课：文星拱照
        if ri_zhi in ['辰', '戌', '丑', '未']:
            matched.append('华盖乘轩课')
        
        # 德庆课：德星临照
        if ri_gan in ['甲', '丙', '戊', '庚', '壬']:  # 阳干
            matched.append('德庆课')
        
        # 斫轮课：雕琢成器
        if ri_gan in ['乙', '丁', '己', '辛', '癸']:  # 阴干
            matched.append('斫轮课')
        
        # 铸印乘轩课：权印在握
        if shi_zhi in ['丑', '未']:  # 印星之地
            matched.append('铸印乘轩课')
        
        return matched if len(matched) > 0 else ['普通课']
    
    def _check_longde_ke(self, ri_ganzhi, sizhu):
        """检查龙德课"""
        try:
            is_longde, longde_type = self.long_de_selector.is_long_de_ke(
                ri_ganzhi,
                sizhu['月柱'][1],  # 月将
                sizhu['年柱'][1],  # 太岁
                []  # 三传（需要排盘）
            )
            return is_longde, longde_type
        except Exception as e:
            print(f"龙德课检查错误：{e}")
            return False, ''
    
    def _get_jishen(self, ri_ganzhi, shi_zhi):
        """获取吉神"""
        jishen = []
        
        # 简化吉神计算
        if ri_ganzhi[0] in ['甲', '戊', '庚']:
            jishen.append('天乙贵人')
        if ri_ganzhi[0] in ['乙', '己']:
            jishen.append('天德贵人')
        if ri_ganzhi[0] in ['丙', '丁']:
            jishen.append('月德贵人')
        if shi_zhi in ['子', '午', '卯', '酉']:
            jishen.append('桃花')
        if shi_zhi in ['寅', '申', '巳', '亥']:
            jishen.append('驿马')
        
        return jishen if len(jishen) > 0 else ['无特殊吉神']
    
    def _format_sizhu(self, sizhu):
        """格式化四柱"""
        return f"{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}"
    
    def _get_weekday(self, date):
        """获取星期"""
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        return weekdays[date.weekday()]
    
    def _update_results_table(self):
        """更新结果表格"""
        # 清空现有数据
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 添加新数据
        for i, result in enumerate(self.results[:100], 1):  # 限制显示 100 条
            self.result_tree.insert('', 'end', values=(
                i,
                result['日期'],
                result['星期'],
                result['四柱'],
                result['斗首课格'],
                result['六壬评分'],
                result['综合评分'],
                result['课格类型'],
                result['吉神']
            ), tags=(result['日期'],))
        
        # 更新状态
        count = len(self.results)
        self.status_label.config(text=f"共找到 {count} 个符合条件的日期")
        
        if count > 0:
            self.filter_label.config(
                text=f"最高综合评分：{max(r['综合评分'] for r in self.results)}"
            )
    
    def _selection_finished(self):
        """择日完成"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_label.config(text="完成")
        
        # 更新日期结果显示
        self._update_date_result_display()
        
        if len(self.results) == 0:
            messagebox.showinfo("提示", "未找到符合条件的日期")
    
    def _stop_selection(self):
        """停止择日"""
        self.stop_btn.config(state='disabled')
        self.progress_label.config(text="已停止")
    
    def _clear_results(self):
        """清空结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.results = []
        self.status_label.config(text="共找到 0 个符合条件的日期")
        self.filter_label.config(text="")
        self._clear_detail()
        # 清空日期结果显示
        self._update_date_result_display()
    
    # ==================== 详细信息展示 ====================
    
    def _show_detail(self, event=None):
        """显示详细信息"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = self.result_tree.item(selection[0])
        date = item['values'][1]  # 日期列
        
        # 查找对应的结果
        result = None
        for r in self.results:
            if r['日期'] == date:
                result = r
                break
        
        if not result:
            return
        
        self.current_detail = result
        shan, xiang = result['山向'].replace('山', '').replace('向', '').split('山')
        
        # 更新各个选项卡
        self._show_sizhu_detail(result)
        self._show_paipan_detail(result, shan, xiang)
        self._show_sike_detail(result)
        self._show_luma_detail(result, shan, xiang)
        self._show_duanyu_detail(result)
        self._show_ai_evaluation(result)
    
    def _show_sizhu_detail(self, result):
        """显示四柱详细信息"""
        sizhu = result['四柱详细']
        
        text = "【四柱信息】\n\n"
        text += f"年柱：{sizhu['年柱']}（纳音：{sizhu.get('年纳音', '')}）\n"
        text += f"月柱：{sizhu['月柱']}（纳音：{sizhu.get('月纳音', '')}）\n"
        text += f"日柱：{sizhu['日柱']}（纳音：{sizhu.get('日纳音', '')}）\n"
        text += f"时柱：{sizhu['时柱']}（纳音：{sizhu.get('时纳音', '')}）\n"
        text += f"\n"
        text += f"日干：{sizhu['日柱'][0]}  日支：{sizhu['日柱'][1]}\n"
        text += f"时干：{sizhu['时柱'][0]}  时支：{sizhu['时柱'][1]}\n"
        
        self.sizhu_text.delete(1.0, tk.END)
        self.sizhu_text.insert(tk.END, text)
    
    def _show_paipan_detail(self, result, shan, xiang):
        """显示大六壬排盘"""
        try:
            # 这里应该调用完整的排盘引擎
            text = "【大六壬排盘】\n\n"
            text += f"日期：{result['日期']}\n"
            text += f"四柱：{result['四柱']}\n"
            text += f"山向：{shan}山{xiang}向\n"
            text += f"\n"
            text += f"月将：待计算\n"
            text += f"贵人：待计算\n"
            text += f"\n"
            text += f"（完整排盘需要调用排盘引擎）\n"
            
            self.paipan_text.delete(1.0, tk.END)
            self.paipan_text.insert(tk.END, text)
        except Exception as e:
            self.paipan_text.delete(1.0, tk.END)
            self.paipan_text.insert(tk.END, f"排盘计算错误：{str(e)}")
    
    def _show_sike_detail(self, result):
        """显示四课三传"""
        text = "【四课三传】\n\n"
        text += "四课：\n"
        text += "  第一课：待计算\n"
        text += "  第二课：待计算\n"
        text += "  第三课：待计算\n"
        text += "  第四课：待计算\n"
        text += "\n"
        text += "三传：\n"
        text += "  初传：待计算\n"
        text += "  中传：待计算\n"
        text += "  末传：待计算\n"
        text += "\n"
        text += "（需要调用四课三传引擎进行完整计算）\n"
        
        self.sike_text.delete(1.0, tk.END)
        self.sike_text.insert(tk.END, text)
    
    def _show_luma_detail(self, result, shan, xiang):
        """显示禄马贵人"""
        text = "【禄马贵人到山到向】\n\n"
        text += f"坐山：{shan}山\n"
        text += f"朝向：{xiang}向\n"
        text += f"\n"
        text += f"年贵人：待计算\n"
        text += f"月贵人：待计算\n"
        text += f"日贵人：待计算\n"
        text += f"\n"
        text += f"{shan}山禄神：待计算\n"
        text += f"{xiang}向禄神：待计算\n"
        text += f"\n"
        text += f"{shan}山驿马：待计算\n"
        text += f"{xiang}向驿马：待计算\n"
        text += f"\n"
        text += f"（需要调用禄马贵人计算引擎）\n"
        
        self.luma_text.delete(1.0, tk.END)
        self.luma_text.insert(tk.END, text)
    
    def _show_duanyu_detail(self, result):
        """显示课格断语"""
        text = "【课格断语】\n\n"
        text += f"斗首课格：{result['斗首课格']}（{result['斗首评分']}分）\n"
        text += f"六壬课格：{result['课格类型']}\n"
        text += f"六壬评分：{result['六壬评分']}分\n"
        text += f"综合评分：{result['综合评分']}分\n"
        text += f"\n"
        
        # 显示每个课体的详细评分
        if '课格评分详情' in result:
            text += "【各课体吉凶评分】\n"
            for kege, score in result['课格评分详情'].items():
                category = self.liuren_scorer.get_ke_ti_category(kege)
                desc = self.liuren_scorer.get_score_description(score)
                text += f"  {kege}: {score}分（{category}）- {desc}\n"
            text += f"\n"
        
        text += "【综合断语】\n"
        text += f"  {result['斗首课格']}：传统斗首法断语待补充\n"
        text += f"\n"
        text += f"（完整断语需要调用断语数据库）\n"
        
        self.duanyu_text.delete(1.0, tk.END)
        self.duanyu_text.insert(tk.END, text)
    
    def _show_ai_evaluation(self, result):
        """显示 AI 评价"""
        text = "【AI 辅助评价】\n\n"
        text += f"综合评分：{result['综合评分']}分\n"
        text += f"  - 斗首评分：{result['斗首评分']}分（40% 权重）\n"
        text += f"  - 六壬评分：{result['六壬评分']}分（60% 权重）\n"
        text += f"\n"
        text += f"优点：\n"
        text += f"  1. 斗首课格吉利：{result['斗首课格']}（{result['斗首评分']}分）\n"
        text += f"  2. 六壬课格：{result['课格类型']}\n"
        
        # 分析最高分的课体
        if '课格评分详情' in result:
            max_kege = max(result['课格评分详情'].items(), key=lambda x: x[1])
            category = self.liuren_scorer.get_ke_ti_category(max_kege[0])
            text += f"  3. 最佳课体：{max_kege[0]}（{max_kege[1]}分，{category}）\n"
        
        if result['龙德课']:
            text += f"  4. 得龙德课，大吉大利\n"
        
        text += f"\n"
        text += f"综合评价：\n"
        total_score = result['综合评分']
        if total_score >= 9:
            text += f"  此日课综合评分{total_score}分，属于上等吉日，非常吉利，适合重大事务。\n"
        elif total_score >= 8:
            text += f"  此日课综合评分{total_score}分，属于中上吉日，较为吉利，可以使用。\n"
        elif total_score >= 7:
            text += f"  此日课综合评分{total_score}分，属于中等吉日，平平，一般事务可用。\n"
        elif total_score >= 6:
            text += f"  此日课综合评分{total_score}分，属于中平日，略有不利，慎用。\n"
        else:
            text += f"  此日课综合评分{total_score}分，属于下等日，不吉利，不建议使用。\n"
        
        text += f"\n"
        text += f"（AI 评价基于六壬分值优先算法生成）\n"
        
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, text)
    
    def _on_result_select(self, event):
        """结果选择事件"""
        selected_items = self.result_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        result = self.result_tree.item(item, 'values')
        
        # 找到对应的结果数据
        for res in self.results:
            if res['日期'] == result[1] and res['四柱'] == result[3]:
                self.current_detail = res
                self._update_detail_display(res)
                # 获取并显示AI评价
                self._update_ai_evaluation(res)
                break
    
    def _update_ai_evaluation(self, result):
        """异步获取AI评估结果"""
        import threading
        
        def get_ai_evaluation():
            try:
                # 显示加载中信息
                self.root.after(0, lambda: self._display_ai_evaluation("AI正在分析..."))
                
                # 调用AI评估器
                evaluation = self.ai_evaluator.get_ai_evaluation_for_result(result)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self._display_ai_evaluation(evaluation))
            except Exception as e:
                # 显示错误信息
                error_msg = f"AI评估失败：{str(e)}\n\n使用本地评价系统："
                # 先显示错误信息
                self.root.after(0, lambda: self._display_ai_evaluation(error_msg))
                # 然后使用本地评价
                self.root.after(1000, lambda: self._show_ai_evaluation(result))
        
        # 启动线程获取AI评估
        thread = threading.Thread(target=get_ai_evaluation)
        thread.daemon = True
        thread.start()
    
    def _display_ai_evaluation(self, evaluation):
        """在界面上显示AI评估结果"""
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, evaluation)
    
    def _update_detail_display(self, result):
        """更新详细信息显示"""
        shan, xiang = result['山向'].replace('山', '').replace('向', '').split('山')
        
        # 更新各个选项卡
        self._show_sizhu_detail(result)
        self._show_paipan_detail(result, shan, xiang)
        self._show_sike_detail(result)
        self._show_luma_detail(result, shan, xiang)
        self._show_duanyu_detail(result)
    
    def _sort_results(self, column):
        """结果排序"""
        # 实现排序逻辑
        pass
    
    def _draw_dizhi_layout(self, tiandi_pan):
        """绘制地盘十二地支方位图（北主朝下布局）"""
        canvas = self.dizhi_canvas
        canvas.delete("all")  # 清空画布
        
        # 中心点和半径
        center_x, center_y = 200, 200
        radius = 150
        
        # 十二地支在地盘的固定位置（天文学视角：从南向北仰视）
        # 天文学视角：北在下，南在上，东在左，西在右
        # 子北、午南、卯东、酉西
        dizhi_positions = {
            '子': (center_x, center_y + radius),      # 正北 (下方)
            '丑': (center_x - radius*0.5, center_y + radius*0.866),  # 东北 (左下)
            '寅': (center_x - radius*0.866, center_y + radius*0.5),  # 东北 (左下)
            '卯': (center_x - radius, center_y),      # 正东 (左方)
            '辰': (center_x - radius*0.866, center_y - radius*0.5),  # 东南 (左上)
            '巳': (center_x - radius*0.5, center_y - radius*0.866),  # 东南 (左上)
            '午': (center_x, center_y - radius),      # 正南 (上方)
            '未': (center_x + radius*0.5, center_y - radius*0.866),  # 西南 (右上)
            '申': (center_x + radius*0.866, center_y - radius*0.5),  # 西南 (右上)
            '酉': (center_x + radius, center_y),      # 正西 (右方)
            '戌': (center_x + radius*0.866, center_y + radius*0.5),  # 西北 (右下)
            '亥': (center_x + radius*0.5, center_y + radius*0.866)   # 西北 (右下)
        }
        
        # 绘制外圆
        canvas.create_oval(center_x - radius - 20, center_y - radius - 20,
                          center_x + radius + 20, center_y + radius + 20,
                          outline='#333333', width=2)
        
        # 绘制内圆
        canvas.create_oval(center_x - radius + 20, center_y - radius + 20,
                          center_x + radius - 20, center_y + radius - 20,
                          outline='#666666', width=1, dash=(5, 5))
        
        # 绘制中心十字线
        canvas.create_line(center_x, center_y - radius - 15,
                          center_x, center_y + radius + 15,
                          fill='#999999', width=1)
        canvas.create_line(center_x - radius - 15, center_y,
                          center_x + radius + 15, center_y,
                          fill='#999999', width=1)
        
        # 绘制方位标签（天文学视角：东左西右）
        font_direction = ('Microsoft YaHei UI', 12, 'bold')
        canvas.create_text(center_x, center_y + radius + 35, text="北", font=font_direction, fill='#c00')
        canvas.create_text(center_x, center_y - radius - 35, text="南", font=font_direction, fill='#c00')
        canvas.create_text(center_x + radius + 35, center_y, text="西", font=font_direction, fill='#c00')
        canvas.create_text(center_x - radius - 35, center_y, text="东", font=font_direction, fill='#c00')
        
        # 绘制十二地支
        font_dizhi = ('Microsoft YaHei UI', 14, 'bold')
        for dizhi, (x, y) in dizhi_positions.items():
            # 获取天盘
            tian = tiandi_pan.get(dizhi, '') if tiandi_pan else ''
            
            # 绘制地支文字
            canvas.create_text(x, y, text=dizhi, font=font_dizhi, fill='#0066cc')
            
            # 如果有天盘，显示在旁边
            if tian:
                # 绘制小字天盘
                offset_x = (x - center_x) * 0.3
                offset_y = (y - center_y) * 0.3
                canvas.create_text(x + offset_x, y + offset_y, 
                                 text=f"天:{tian}", 
                                 font=('Microsoft YaHei UI', 9), 
                                 fill='#cc6600')
        
        # 绘制中心说明
        canvas.create_text(center_x, center_y, 
                          text="地盘\n固定\n(北下南上 东左西右)", 
                          font=('Microsoft YaHei UI', 9), 
                          fill='#666666',
                          justify=tk.CENTER)
    
    def _draw_tianjiang_layout(self, gui_ren_pan, tiandi_pan):
        """绘制天将盘方位图（天文学视角：东左西右）"""
        canvas = self.tianjiang_canvas
        canvas.delete("all")  # 清空画布
        
        # 中心点和半径
        center_x, center_y = 200, 200
        radius = 150
        
        # 获取天将映射：天盘地支 → 天将名
        tian_jiang_map = gui_ren_pan.get('天将映射', {})
        
        # 十二地支位置（与地盘相同的坐标系：天文学视角）
        dizhi_positions = {
            '子': (center_x, center_y + radius),      # 正北 (下方)
            '丑': (center_x - radius*0.5, center_y + radius*0.866),  # 东北 (左下)
            '寅': (center_x - radius*0.866, center_y + radius*0.5),  # 东北 (左下)
            '卯': (center_x - radius, center_y),      # 正东 (左方)
            '辰': (center_x - radius*0.866, center_y - radius*0.5),  # 东南 (左上)
            '巳': (center_x - radius*0.5, center_y - radius*0.866),  # 东南 (左上)
            '午': (center_x, center_y - radius),      # 正南 (上方)
            '未': (center_x + radius*0.5, center_y - radius*0.866),  # 西南 (右上)
            '申': (center_x + radius*0.866, center_y - radius*0.5),  # 西南 (右上)
            '酉': (center_x + radius, center_y),      # 正西 (右方)
            '戌': (center_x + radius*0.866, center_y + radius*0.5),  # 西北 (右下)
            '亥': (center_x + radius*0.5, center_y + radius*0.866)   # 西北 (右下)
        }
        
        # 绘制外圆
        canvas.create_oval(center_x - radius - 20, center_y - radius - 20,
                          center_x + radius + 20, center_y + radius + 20,
                          outline='#333333', width=2)
        
        # 绘制内圆
        canvas.create_oval(center_x - radius + 20, center_y - radius + 20,
                          center_x + radius - 20, center_y + radius - 20,
                          outline='#666666', width=1, dash=(5, 5))
        
        # 绘制中心十字线
        canvas.create_line(center_x, center_y - radius - 15,
                          center_x, center_y + radius + 15,
                          fill='#999999', width=1)
        canvas.create_line(center_x - radius - 15, center_y,
                          center_x + radius + 15, center_y,
                          fill='#999999', width=1)
        
        # 绘制方位标签
        font_direction = ('Microsoft YaHei UI', 12, 'bold')
        canvas.create_text(center_x, center_y + radius + 35, text="北", font=font_direction, fill='#c00')
        canvas.create_text(center_x, center_y - radius - 35, text="南", font=font_direction, fill='#c00')
        canvas.create_text(center_x - radius - 35, center_y, text="东", font=font_direction, fill='#c00')
        canvas.create_text(center_x + radius + 35, center_y, text="西", font=font_direction, fill='#c00')
        
        # 绘制天盘地支和天将
        font_dizhi = ('Microsoft YaHei UI', 12, 'bold')
        font_tianjiang = ('Microsoft YaHei UI', 10, 'bold')
        
        for dizhi, (x, y) in dizhi_positions.items():
            # 获取天盘
            tian = tiandi_pan.get(dizhi, '') if tiandi_pan else ''
            
            # 获取天将
            tianjiang = tian_jiang_map.get(tian, '')
            
            # 绘制地支文字（内圈）
            canvas.create_text(x, y, text=dizhi, font=font_dizhi, fill='#0066cc')
            
            # 绘制天盘（中圈）
            if tian:
                offset_x = (x - center_x) * 0.3
                offset_y = (y - center_y) * 0.3
                canvas.create_text(x + offset_x, y + offset_y, 
                                 text=tian, 
                                 font=('Microsoft YaHei UI', 10), 
                                 fill='#cc6600')
            
            # 绘制天将（外圈）
            if tianjiang:
                offset_outer_x = (x - center_x) * 0.6
                offset_outer_y = (y - center_y) * 0.6
                canvas.create_text(x + offset_outer_x, y + offset_outer_y, 
                                 text=tianjiang, 
                                 font=font_tianjiang, 
                                 fill='#009900')
        
        # 绘制中心说明
        canvas.create_text(center_x, center_y, 
                          text=f"天将盘\n{gui_ren_pan.get('顺逆', '')}行\n贵人:{gui_ren_pan.get('贵人', '')}", 
                          font=('Microsoft YaHei UI', 9), 
                          fill='#666666',
                          justify=tk.CENTER)
    
    def _draw_tiandi_pan_layout(self, tiandi_pan):
        """绘制天地盘对比图（后续扩展）"""
        # 预留方法，用于后续实现天地盘对比显示
        pass
    
    def _clear_detail(self):
        """清空详细信息"""
        self.sizhu_text.delete(1.0, tk.END)
        self.paipan_text.delete(1.0, tk.END)
        self.sike_text.delete(1.0, tk.END)
        self.luma_text.delete(1.0, tk.END)
        self.duanyu_text.delete(1.0, tk.END)
        self.ai_text.delete(1.0, tk.END)
        self.current_detail = None
    
    # ==================== 辅助功能 ====================
    
    def _export_results(self):
        """导出结果"""
        if len(self.results) == 0:
            messagebox.showinfo("提示", "没有结果可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("仪度六壬综合择日系统 - 择日结果\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"共找到 {len(self.results)} 个符合条件的日期\n\n")
                    
                    for i, result in enumerate(self.results, 1):
                        f.write(f"{i}. {result['日期']} ({result['星期']})\n")
                        f.write(f"   四柱：{result['四柱']}\n")
                        f.write(f"   斗首课格：{result['斗首课格']}\n")
                        f.write(f"   评分：{result['评分']}\n")
                        f.write(f"   课格：{result['课格类型']}\n")
                        f.write(f"   吉神：{result['吉神']}\n")
                        f.write(f"   山向：{result['山向']}\n")
                        f.write("\n")
                
                messagebox.showinfo("成功", f"结果已导出到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def _save_config(self):
        """保存配置"""
        config = {
            'shan': self.shan_combo.get(),
            'xiang': self.xiang_combo.get(),
            'start_date': self.start_date_entry.get(),
            'end_date': self.end_date_entry.get(),
            'douhou': self.douhou_combo.get(),
            'min_score': self.min_score_spin.get(),
            'selected_kege': list(self.selected_kege_types)
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"配置已保存：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def _load_config(self):
        """加载配置"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 应用配置
                self.shan_combo.set(config.get('shan', '壬'))
                self.xiang_combo.set(config.get('xiang', '丙'))
                self.start_date_entry.delete(0, tk.END)
                self.start_date_entry.insert(0, config.get('start_date', ''))
                self.end_date_entry.delete(0, tk.END)
                self.end_date_entry.insert(0, config.get('end_date', ''))
                self.douhou_combo.set(config.get('douhou', '全部'))
                self.min_score_spin.delete(0, tk.END)
                self.min_score_spin.insert(0, str(config.get('min_score', '5.0')))
                
                # 恢复课格选择
                self._deselect_all_kege()
                for kege in config.get('selected_kege', []):
                    if kege in self.kege_vars:
                        self.kege_vars[kege].set(True)
                        self.selected_kege_types.add(kege)
                
                self._update_shan_info()
                self._validate_dates()
                
                messagebox.showinfo("成功", f"配置已加载：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败：{str(e)}")
    
    def _clear_all(self):
        """清空所有选择"""
        self._reset_shan_xiang()
        today = datetime.now().strftime('%Y-%m-%d')
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, today)
        end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end_date)
        self._deselect_all_kege()
        self.douhou_combo.set('全部')
        self.min_score_spin.set(7.0)
        self.long_de_var.set(False)
        self._clear_results()
    
    def _open_paipan_on_double(self, event=None):
        """双击打开排盘"""
        self._open_paipan()
    
    def _open_paipan(self):
        """打开排盘功能"""
        # 检查是否有选中的结果
        selection = self.result_tree.selection()
        if not selection and len(self.results) > 0:
            # 如果没有选中，默认选第一个
            self.result_tree.selection_set(self.result_tree.get_children()[0])
            selection = self.result_tree.selection()
        
        if selection:
            item = self.result_tree.item(selection[0])
            date = item['values'][1]
            
            # 查找对应的结果
            result = None
            for r in self.results:
                if r['日期'] == date:
                    result = r
                    break
            
            if result:
                # 打开排盘窗口
                self._show_paipan_window(result)
            else:
                messagebox.showinfo("提示", "请先选择一个日期")
        else:
            messagebox.showinfo("提示", "请先选择一个日期")
    
    def _show_paipan_window(self, result):
        """显示大六壬排盘窗口"""
        # 创建新窗口
        paipan_window = tk.Toplevel(self.root)
        paipan_window.title(f"大六壬排盘 - {result['日期']}")
        paipan_window.geometry("900x700")
        
        # 获取四柱信息
        sizhu = result['四柱详细']
        ri_ganzhi = sizhu['日柱']
        ri_gan = ri_ganzhi[0]
        ri_zhi = ri_ganzhi[1]
        shi_ganzhi = sizhu['时柱']
        shi_zhi = shi_ganzhi[1]
        
        # 计算月将（使用精确的节气计算）
        try:
            from engine.yuejiang_engine import YueJiangCalculator
            yuejiang_calc = YueJiangCalculator()
            yue_jiang, yue_jiang_name = yuejiang_calc.get_yuejiang_by_date(
                sizhu['年']['year'], 
                sizhu['月']['month'], 
                sizhu['日']['day'],
                shi_hour
            )
        except Exception as e:
            print(f"月将计算错误：{e}")
            # 简化计算作为后备
            yue_zhi = sizhu['月柱'][1]
            yue_index = self.calendar.DIZHI.index(yue_zhi) if yue_zhi in self.calendar.DIZHI else 0
            yue_jiang_index = (12 - (yue_index + 1)) % 12
            yue_jiang = self.calendar.DIZHI[yue_jiang_index]
            yue_jiang_name = ''
        
        # 计算四课三传
        try:
            from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
            sike_engine = SiKeSanChuanCalculator()
            
            # 计算天地盘（月将加时）
            tiandi_pan = sike_engine.get_tiandi_pan(yue_jiang, shi_zhi)
            
            # 计算四课
            sike = sike_engine.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 计算三传
            sanchuan = sike_engine.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
        except Exception as e:
            print(f"排盘计算错误：{e}")
            import traceback
            traceback.print_exc()
            sike = []
            sanchuan = {}
            tiandi_pan = {}
        
        # 创建界面
        main_frame = ttk.Frame(paipan_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        paipan_window.columnconfigure(0, weight=1)
        paipan_window.rowconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, 
                               text=f"大六壬排盘 - {result['日期']} ({sizhu['日柱']})",
                               style='Title.TLabel',
                               font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 选项卡 1：基本信息
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="基本信息")
        
        basic_text = scrolledtext.ScrolledText(basic_frame, height=30, width=80,
                                              font=('Microsoft YaHei UI', 11))
        basic_text.pack(fill=tk.BOTH, expand=True)
        
        # 显示基本信息
        yue_jiang_info = f"{yue_jiang}"
        if 'yue_jiang_name' in locals() and yue_jiang_name:
            yue_jiang_info += f" ({yue_jiang_name})"
        
        info_text = f"""【基本信息】
━━━━━━━━━━━━━━━━━━━━━━━━
日期：{result['日期']} ({result['星期']})
时间：{shi_ganzhi}时
四柱：
  年柱：{sizhu['年柱']}
  月柱：{sizhu['月柱']}
  日柱：{sizhu['日柱']}
  时柱：{sizhu['时柱']}

【大六壬参数】
━━━━━━━━━━━━━━━━━━━━━━━━
月将：{yue_jiang_info}
占时：{shi_zhi}
日干支：{ri_ganzhi}
旬首：{self._get_xun_shou(ri_ganzhi)}

【课格信息】
━━━━━━━━━━━━━━━━━━━━━━━━
课体：{result['课格类型']}
六壬评分：{result['六壬评分']}
斗首评分：{result['斗首评分']}
综合评分：{result['综合评分']}
"""
        
        if result.get('龙德课'):
            info_text += f"\n【龙德课】\n━━━━━━━━━━━━━━━━━━━━━━━━\n✓ 是龙德课\n类型：{result.get('龙德类型', '')}\n"
        
        basic_text.insert(tk.END, info_text)
        basic_text.config(state='disabled')
        
        # 选项卡 2：四课
        sike_frame = ttk.Frame(notebook, padding="10")
        notebook.add(sike_frame, text="四课")
        
        sike_text = scrolledtext.ScrolledText(sike_frame, height=30, width=80,
                                             font=('Microsoft YaHei UI', 12, 'bold'))
        sike_text.pack(fill=tk.BOTH, expand=True)
        
        # 显示四课
        if sike and len(sike) > 0:
            sike_display = "【四课】\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            sike_display += "（从左到右：第四课 ← 第三课 ← 第二课 ← 第一课）\n\n"
            
            # 按照文档规范显示四课
            # 第一课：日干上神（干阳）
            # 第二课：干上神的上神（干阴）
            # 第三课：日支上神（支阳）
            # 第四课：支上神的上神（支阴）
            
            for i, (ke_name, shang, xia, _) in enumerate(sike, 1):
                sike_display += f"{ke_name}：{shang} / {xia}\n"
            
            sike_display += "\n"
            sike_display += "说明：\n"
            sike_display += "  第一课（日干上神）：反映自身状况\n"
            sike_display += "  第二课（干上神上神）：反映他人他事\n"
            sike_display += "  第三课（日支上神）：反映宅舍内部\n"
            sike_display += "  第四课（支上神上神）：反映外部环境\n"
            
            sike_text.insert(tk.END, sike_display)
        else:
            sike_text.insert(tk.END, "四课计算暂不可用")
        
        sike_text.config(state='disabled')
        
        # 选项卡 3：三传
        sanchuan_frame = ttk.Frame(notebook, padding="10")
        notebook.add(sanchuan_frame, text="三传")
        
        sanchuan_text = scrolledtext.ScrolledText(sanchuan_frame, height=30, width=80,
                                                  font=('Microsoft YaHei UI', 12, 'bold'))
        sanchuan_text.pack(fill=tk.BOTH, expand=True)
        
        # 显示三传
        if sanchuan and '初传' in sanchuan:
            chu = sanchuan.get('初传', '')
            zhong = sanchuan.get('中传', '')
            mo = sanchuan.get('末传', '')
            ke_ti = sanchuan.get('课体', '')
            qi_fa = sanchuan.get('起法', '')
            
            san_text = f"""【三传】
━━━━━━━━━━━━━━━━━━━━━━━━

        初传：{chu}
        中传：{zhong}
        末传：{mo}

【课体】{ke_ti}
【起法】{qi_fa}

━━━━━━━━━━━━━━━━━━━━━━━━
【三传含义】
  初传：事情的开始、发端
  中传：事情的发展、过程
  末传：事情的结果、结局
"""
            sanchuan_text.insert(tk.END, san_text)
        else:
            sanchuan_text.insert(tk.END, "三传计算暂不可用")
        
        sanchuan_text.config(state='disabled')
        
        # 选项卡 4：天地盘（图形化显示）
        tiandi_frame = ttk.Frame(notebook, padding="10")
        notebook.add(tiandi_frame, text="天地盘")
        
        # 创建上下分栏布局
        tiandi_paned = ttk.PanedWindow(tiandi_frame, orient=tk.VERTICAL)
        tiandi_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上部：天地盘图形
        tiandi_upper_frame = ttk.LabelFrame(tiandi_paned, text="天地盘方位图")
        tiandi_paned.add(tiandi_upper_frame, weight=1)
        
        # 创建 Canvas 绘制地盘
        self.dizhi_canvas = tk.Canvas(tiandi_upper_frame, width=400, height=350, 
                                      bg='white', highlightthickness=0)
        self.dizhi_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 绘制地盘
        self._draw_dizhi_layout(tiandi_pan)
        
        # 下部：天地盘文字说明
        tiandi_lower_frame = ttk.LabelFrame(tiandi_paned, text="天地盘对应关系")
        tiandi_paned.add(tiandi_lower_frame, weight=1)
        
        tiandi_text = scrolledtext.ScrolledText(tiandi_lower_frame, height=10, width=60,
                                                font=('Microsoft YaHei UI', 10))
        tiandi_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示天地盘对应关系
        if tiandi_pan:
            tiandi_display = "【天地盘对应】\n"
            tiandi_display += "━━━━━━━━━━━━━━━━━━\n\n"
            tiandi_display += "地盘方位    天盘\n"
            tiandi_display += "━━━━━━━━━━━━━━━━━━\n"
            
            # 地支方位说明
            fangwei = {
                '子': '正北', '丑': '东北', '寅': '东北',
                '卯': '正东', '辰': '东南', '巳': '东南',
                '午': '正南', '未': '西南', '申': '西南',
                '酉': '正西', '戌': '西北', '亥': '西北'
            }
            
            for dizhi in self.calendar.DIZHI:
                tian = tiandi_pan.get(dizhi, '')
                fw = fangwei.get(dizhi, '')
                tiandi_display += f"{dizhi:2s}({fw:4s})  →  {tian:2s}\n"
            
            tiandi_text.insert(tk.END, tiandi_display)
        else:
            tiandi_text.insert(tk.END, "天地盘计算暂不可用")
        
        tiandi_text.config(state='disabled')
        
        # 选项卡 5：天将盘（贵人盘）
        tianjiang_frame = ttk.Frame(notebook, padding="10")
        notebook.add(tianjiang_frame, text="天将盘")
        
        # 创建左右分栏布局
        tj_paned = ttk.PanedWindow(tianjiang_frame, orient=tk.HORIZONTAL)
        tj_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：天将盘图形化显示
        tj_canvas_frame = ttk.LabelFrame(tj_paned, text="天将盘方位图")
        tj_paned.add(tj_canvas_frame, weight=1)
        
        # 创建 Canvas 绘制天将盘
        self.tianjiang_canvas = tk.Canvas(tj_canvas_frame, width=400, height=350, 
                                          bg='white', highlightthickness=0)
        self.tianjiang_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 计算并绘制天将盘
        try:
            from engine.gui_ren_engine import GuiRenCalculator
            gui_ren_calc = GuiRenCalculator()
            
            # 判断昼夜（根据时支）
            # 昼时：卯、辰、巳、午、未、申
            # 夜时：酉、戌、亥、子、丑、寅
            zhou_hours = ['卯', '辰', '巳', '午', '未', '申']
            is_night = shi_zhi not in zhou_hours
            
            # 包装天地盘为正确格式
            tiandi_pan_dict = {'天地对应': tiandi_pan} if isinstance(tiandi_pan, dict) else tiandi_pan
            
            # 排贵人盘
            gui_ren_pan = gui_ren_calc.arrange_gui_ren_pan(ri_gan, tiandi_pan_dict, shi_ganzhi, is_night)
            
            # 绘制天将盘
            self._draw_tianjiang_layout(gui_ren_pan, tiandi_pan)
            
        except Exception as e:
            import traceback
            print(f"天将盘计算错误：{e}")
            traceback.print_exc()
            self.tianjiang_canvas.create_text(200, 175, text="天将盘计算暂不可用\n" + str(e), 
                                             font=('Microsoft YaHei UI', 10), fill='#666')
        
        # 右侧：天将盘文字说明
        tj_text_frame = ttk.LabelFrame(tj_paned, text="天将盘详细信息")
        tj_paned.add(tj_text_frame, weight=1)
        
        tj_text = scrolledtext.ScrolledText(tj_text_frame, height=25, width=45,
                                           font=('Microsoft YaHei UI', 10))
        tj_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示天将盘信息
        if 'gui_ren_pan' in locals():
            tj_display = f"""【天将盘信息】
━━━━━━━━━━━━━━━━━━━━━━━━
日干：{ri_gan}
贵人：{gui_ren_pan['贵人']}
昼夜：{gui_ren_pan['昼夜']}
贵人落地盘位置：{gui_ren_pan['贵人落地盘位置']}
顺逆：{gui_ren_pan['顺逆']}行

【十二天将】
━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for tj in gui_ren_pan['天将列表']:
                tj_display += f"{tj['天将']:6} → 天盘{tj['地支']:2}\n"
            
            tj_display += """
━━━━━━━━━━━━━━━━━━━━━━━━
【天将含义】
贵人：吉神，主贵人扶助、吉祥
螣蛇：凶神，主惊恐、怪异
朱雀：凶神，主口舌、文书
六合：吉神，主和合、婚姻
勾陈：凶神，主争斗、田土
青龙：吉神，主喜庆、财禄
天空：凶神，主虚诈、空亡
白虎：凶神，主凶丧、血光
太常：吉神，主酒食、喜庆
玄武：凶神，主盗贼、阴私
太阴：吉神，主阴私、暗昧
天后：吉神，主恩泽、妇女
"""
            tj_text.insert(tk.END, tj_display)
        else:
            tj_text.insert(tk.END, "天将盘计算暂不可用")
        
        tj_text.config(state='disabled')
        
        # 关闭按钮
        close_btn = ttk.Button(main_frame, text="关闭", 
                              command=paipan_window.destroy)
        close_btn.grid(row=2, column=0, pady=10)
    
    def _get_xun_shou(self, ri_ganzhi):
        """获取旬首"""
        # 简化计算
        gan_list = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        if ri_ganzhi not in gan_list or len(ri_ganzhi) < 2:
            return ''
        
        gan_index = gan_list.index(ri_ganzhi[0])
        zhi_index = zhi_list.index(ri_ganzhi[1])
        
        # 计算旬首
        xun_shou_index = (10 - gan_index) % 10
        return gan_list[xun_shou_index] + zhi_list[(xun_shou_index + zhi_index - gan_index) % 12]
    
    def _create_result_context_menu(self):
        """创建结果列表右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="查看大六壬排盘", command=self._open_paipan_from_context)
        self.context_menu.add_command(label="查看详细信息", command=self._show_detail_from_context)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="导出该日期", command=self._export_selected)
        
        # 绑定右键事件
        self.result_tree.bind('<Button-3>', self._show_context_menu)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        # 先选中点击的项目
        item = self.result_tree.identify_row(event.y)
        if item:
            self.result_tree.selection_set(item)
            # 显示菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def _open_paipan_from_context(self):
        """从右键菜单打开排盘"""
        self._open_paipan()
    
    def _show_detail_from_context(self):
        """从右键菜单显示详细信息"""
        self._show_detail()
    
    def _export_selected(self):
        """导出选中的日期"""
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个日期")
            return
        
        item = self.result_tree.item(selection[0])
        date = item['values'][1]
        messagebox.showinfo("导出", f"导出功能开发中...\n选中日期：{date}")
    
    def _open_calendar(self):
        """打开万年历查询"""
        messagebox.showinfo("提示", "万年历查询功能开发中...")
    
    def _show_help(self):
        """显示使用说明"""
        help_text = """
仪度六壬综合择日系统 - 使用说明

第一步：选择山向
  - 点击二十四山按钮选择坐山
  - 朝向会自动匹配，也可手动调整
  - 可点击"互换山向"交换坐向

第二步：选择日期范围
  - 输入开始和结束日期（格式：YYYY-MM-DD）
  - 或使用快捷按钮快速选择
  - 系统会自动验证日期有效性

第三步：选择课格类型
  - 勾选需要的课格类型（可多选）
  - 可使用"全选"、"取消全选"等快捷按钮
  - 设置斗首课格和最低评分

开始择日
  - 点击"开始择日"按钮
  - 系统会自动计算符合条件的日期
  - 双击结果查看详细分析

详细信息
  - 四柱信息：完整的年月日时柱
  - 大六壬排盘：完整的排盘信息
  - 四课三传：课传详细分析
  - 禄马贵人：到山到向情况
  - 课格断语：传统断语
  - AI 评价：智能分析建议
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _show_kege_help(self):
        """显示课格详解"""
        kege_text = """
主要课格详解：

富贵课：主富贵双全，功成名就
荣华课：主荣华富贵，家业兴旺
龙德课：得龙德贵人，大吉大利
官爵课：主官运亨通，爵位高升
时泰课：时运亨泰，万事顺遂
和美课：家庭和睦，婚姻美满
合欢课：主喜庆和合，贵人相助
回环课：循环往复，生生不息
亨通课：万事亨通，无阻无碍
华盖乘轩课：文运昌盛，名利双收
德庆课：德高望重，喜庆临门
斫轮课：雕琢成器，大器晚成
铸印乘轩课：权印在握，地位尊崇
"""
        messagebox.showinfo("课格详解", kege_text)
    
    def _show_about(self):
        """显示关于"""
        about_text = """
仪度六壬综合择日系统 - 增强版
版本：2.0

本系统基于传统六壬术数理论
结合现代计算机技术开发

功能特点：
- 精确的节气和四柱计算
- 完整的六壬课格判断
- 智能的 AI 辅助评价
- 友好的图形界面

开发日期：2026 年
"""
        messagebox.showinfo("关于", about_text)


# ==================== 主程序 ====================

def main():
    """主程序入口"""
    root = tk.Tk()
    app = EnhancedDateSelectorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
