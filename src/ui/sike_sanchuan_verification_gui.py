"""
大六壬四课三传验证 GUI 测试界面
专业美观的验证工具，包含输入区域、结果显示区域、错误标记功能、历史记录功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径 - 最终解决方案
# 使用绝对路径，确保在任何情况下都能找到模块
script_dir = os.path.dirname(os.path.abspath(__file__))  # GUI 脚本所在目录 (src/ui/)
src_dir = os.path.dirname(script_dir)  # src 目录

# 确保工作目录正确
os.chdir(os.path.dirname(src_dir))  # 切换到项目根目录

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 现在可以直接导入
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
from utils.gui_style_config import COLORS, FONTS


class SiKeSanChuanVerificationGUI:
    """四课三传验证 GUI 测试界面"""
    
    # 样式配置
    STYLE = {
        'bg_primary': '#F5F5F5',          # 主背景
        'bg_secondary': '#FFFFFF',        # 次级背景
        'accent_color': '#2196F3',        # 强调色（蓝色）
        'success_color': '#4CAF50',       # 成功色（绿色）
        'error_color': '#F44336',         # 错误色（红色）
        'warning_color': '#FF9800',       # 警告色（橙色）
        'text_primary': '#212121',        # 主文字
        'text_secondary': '#757575',      # 次级文字
        'border_color': '#E0E0E0',        # 边框色
        'header_bg': '#1976D2',           # 标题栏背景
        'header_fg': '#FFFFFF',           # 标题栏文字
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬四课三传验证 2.0 增加版")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.STYLE['bg_primary'])
        
        # 确保路径正确（再次检查）
        self._ensure_path_setup()
        
        # 初始化计算器
        try:
            self.calculator = SiKeSanChuanCalculator()
        except Exception as e:
            messagebox.showerror("致命错误", f"无法初始化计算器：{str(e)}\n\n请确保程序文件完整。")
            raise
        
        # 历史记录
        self.history = []
        self.max_history = 50
        
        # 错误标记
        self.error_marks = []
        
        # 创建界面
        self.create_menu()
        self.create_main_layout()
        self.create_status_bar()
        
        # 加载历史记录
        self.load_history()
    
    def _ensure_path_setup(self):
        """确保项目路径设置正确"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(script_dir)
        
        # 确保工作目录正确
        os.chdir(os.path.dirname(src_dir))
        
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存当前结果", command=self.save_current_result)
        file_menu.add_command(label="导出历史记录", command=self.export_history)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="清空输入", command=self.clear_input)
        edit_menu.add_command(label="清空历史", command=self.clear_history)
        edit_menu.add_command(label="清空错误标记", command=self.clear_error_marks)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_main_layout(self):
        """创建主布局"""
        # 主容器使用 PanedWindow，可调节左右比例
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 左侧面板（输入区 + 历史记录）
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        
        # 右侧面板（结果显示区）
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)
        
        # 创建左侧内容
        self.create_left_panel(left_frame)
        
        # 创建右侧内容
        self.create_right_panel(right_frame)
    
    def create_left_panel(self, parent):
        """创建左侧面板（输入区 + 历史记录）"""
        # 使用 PanedWindow 分隔输入区和历史记录
        left_pane = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        left_pane.pack(fill='both', expand=True)
        
        # 上部：输入区域
        input_frame = ttk.LabelFrame(left_pane, text="输入参数", padding=10)
        left_pane.add(input_frame, weight=2)
        
        self.create_input_section(input_frame)
        
        # 下部：历史记录区域
        history_frame = ttk.LabelFrame(left_pane, text="历史记录", padding=10)
        left_pane.add(history_frame, weight=1)
        
        self.create_history_section(history_frame)
    
    def create_right_panel(self, parent):
        """创建右侧面板（结果显示区）"""
        # 使用 PanedWindow 分隔不同显示区域
        right_pane = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        right_pane.pack(fill='both', expand=True)
        
        # 上部：天地盘显示
        tiandi_frame = ttk.LabelFrame(right_pane, text="天地盘排布", padding=10)
        right_pane.add(tiandi_frame, weight=1)
        
        self.create_tiandi_pan_section(tiandi_frame)
        
        # 中部：四课显示
        sike_frame = ttk.LabelFrame(right_pane, text="四课显示", padding=10)
        right_pane.add(sike_frame, weight=1)
        
        self.create_sike_section(sike_frame)
        
        # 下部：三传显示
        sanchuan_frame = ttk.LabelFrame(right_pane, text="三传显示", padding=10)
        right_pane.add(sanchuan_frame, weight=1)
        
        self.create_sanchuan_section(sanchuan_frame)
    
    def create_input_section(self, parent):
        """创建输入区域"""
        # 标题
        title_label = ttk.Label(
            parent, 
            text="四课三传起课参数",
            font=('微软雅黑', 14, 'bold'),
            foreground=self.STYLE['header_bg']
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15), sticky='w')
        
        # 1. 月将
        ttk.Label(parent, text="月将：", font=('微软雅黑', 10)).grid(
            row=1, column=0, sticky='w', pady=5, padx=5)
        self.yuejiang_var = tk.StringVar()
        self.yuejiang_combo = ttk.Combobox(
            parent, 
            textvariable=self.yuejiang_var,
            width=10, 
            state='readonly',
            font=('微软雅黑', 10)
        )
        self.yuejiang_combo['values'] = [
            '亥 (登明)', '戌 (河魁)', '酉 (从魁)', '申 (传送)', 
            '未 (小吉)', '午 (胜光)', '巳 (太乙)', '辰 (天罡)',
            '卯 (太冲)', '寅 (功曹)', '丑 (大吉)', '子 (神后)'
        ]
        self.yuejiang_combo.current(0)
        self.yuejiang_combo.grid(row=1, column=1, pady=5, padx=5, sticky='w')
        
        # 2. 占时
        ttk.Label(parent, text="占时：", font=('微软雅黑', 10)).grid(
            row=1, column=2, sticky='w', pady=5, padx=5)
        self.shichen_var = tk.StringVar()
        self.shichen_combo = ttk.Combobox(
            parent, 
            textvariable=self.shichen_var,
            width=10, 
            state='readonly',
            font=('微软雅黑', 10)
        )
        self.shichen_combo['values'] = [
            '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'
        ]
        self.shichen_combo.current(2)
        self.shichen_combo.grid(row=1, column=3, pady=5, padx=5, sticky='w')
        
        # 3. 日干
        ttk.Label(parent, text="日干：", font=('微软雅黑', 10)).grid(
            row=2, column=0, sticky='w', pady=5, padx=5)
        self.ri_gan_var = tk.StringVar()
        self.ri_gan_combo = ttk.Combobox(
            parent, 
            textvariable=self.ri_gan_var,
            width=10, 
            state='readonly',
            font=('微软雅黑', 10)
        )
        self.ri_gan_combo['values'] = [
            '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'
        ]
        self.ri_gan_combo.current(0)
        self.ri_gan_combo.grid(row=2, column=1, pady=5, padx=5, sticky='w')
        
        # 4. 日支
        ttk.Label(parent, text="日支：", font=('微软雅黑', 10)).grid(
            row=2, column=2, sticky='w', pady=5, padx=5)
        self.ri_zhi_var = tk.StringVar()
        self.ri_zhi_combo = ttk.Combobox(
            parent, 
            textvariable=self.ri_zhi_var,
            width=10, 
            state='readonly',
            font=('微软雅黑', 10)
        )
        self.ri_zhi_combo['values'] = [
            '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'
        ]
        self.ri_zhi_combo.current(0)
        self.ri_zhi_combo.grid(row=2, column=3, pady=5, padx=5, sticky='w')
        
        # 5. 验证按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=20)
        
        ttk.Button(
            btn_frame, 
            text="开始验证", 
            command=self.calculate_and_verify,
            style='Accent.TButton'
        ).pack(side='left', padx=10)
        
        ttk.Button(
            btn_frame, 
            text="清空输入", 
            command=self.clear_input
        ).pack(side='left', padx=10)
        
        # 6. 错误标记选项
        mark_frame = ttk.LabelFrame(parent, text="错误标记选项", padding=10)
        mark_frame.grid(row=4, column=0, columnspan=4, pady=10, sticky='ew')
        
        self.error_mark_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            mark_frame, 
            text="启用错误标记（自动检测并标记可疑结果）",
            variable=self.error_mark_var
        ).pack(side='left', padx=5)
        
        # 错误标记列表
        self.error_mark_listbox = tk.Listbox(
            mark_frame, 
            height=4, 
            font=('微软雅黑', 9),
            bg=self.STYLE['bg_secondary'],
            selectbackground=self.STYLE['accent_color'],
            selectforeground='white'
        )
        self.error_mark_listbox.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        ttk.Button(
            mark_frame, 
            text="清除标记", 
            command=self.clear_error_marks,
            width=10
        ).pack(side='left', padx=5)
    
    def create_history_section(self, parent):
        """创建历史记录区域"""
        # 历史记录列表
        self.history_listbox = tk.Listbox(
            parent, 
            font=('微软雅黑', 9),
            bg=self.STYLE['bg_secondary'],
            selectbackground=self.STYLE['accent_color'],
            selectforeground='white'
        )
        self.history_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_selected)
        
        # 历史记录操作按钮
        history_btn_frame = ttk.Frame(parent)
        history_btn_frame.pack(side='right', fill='y', padx=5, pady=5)
        
        ttk.Button(
            history_btn_frame, 
            text="加载", 
            command=self.load_selected_history,
            width=8
        ).pack(pady=2)
        
        ttk.Button(
            history_btn_frame, 
            text="删除", 
            command=self.delete_selected_history,
            width=8
        ).pack(pady=2)
        
        ttk.Button(
            history_btn_frame, 
            text="清空", 
            command=self.clear_history,
            width=8
        ).pack(pady=2)
    
    def create_tiandi_pan_section(self, parent):
        """创建天地盘显示区域"""
        # 使用 Text 组件显示天地盘
        self.tiandi_pan_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=60,
            height=8,
            font=('Consolas', 11),
            bg=self.STYLE['bg_secondary'],
            fg=self.STYLE['text_primary'],
            borderwidth=1,
            relief='solid'
        )
        self.tiandi_pan_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_sike_section(self, parent):
        """创建四课显示区域"""
        # 使用 Text 组件显示四课
        self.sike_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=60,
            height=8,
            font=('Consolas', 11),
            bg=self.STYLE['bg_secondary'],
            fg=self.STYLE['text_primary'],
            borderwidth=1,
            relief='solid'
        )
        self.sike_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_sanchuan_section(self, parent):
        """创建三传显示区域"""
        # 使用 Text 组件显示三传
        self.sanchuan_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=60,
            height=10,
            font=('Consolas', 11),
            bg=self.STYLE['bg_secondary'],
            fg=self.STYLE['text_primary'],
            borderwidth=1,
            relief='solid'
        )
        self.sanchuan_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 请输入参数并点击\"开始验证\"")
        
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(10, 5)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def calculate_and_verify(self):
        """计算并验证四课三传"""
        try:
            # 获取输入参数
            yuejiang_full = self.yuejiang_var.get()
            # 提取地支（去掉括号内的内容）
            yuejiang = yuejiang_full.split('(')[0].strip()
            
            shichen = self.shichen_var.get()
            ri_gan = self.ri_gan_var.get()
            ri_zhi = self.ri_zhi_var.get()
            
            # 验证输入
            if not all([yuejiang, shichen, ri_gan, ri_zhi]):
                messagebox.showerror("错误", "请填写所有参数！")
                return
            
            # 1. 获取天地盘
            tiandi_pan = self.calculator.get_tiandi_pan(yuejiang, shichen)
            
            # 2. 起四课
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 3. 发三传
            sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            # 4. 显示结果
            self.display_results(tiandi_pan, sike, sanchuan_result)
            
            # 5. 错误标记检测
            if self.error_mark_var.get():
                self.check_and_mark_errors(sike, sanchuan_result, tiandi_pan, ri_gan, ri_zhi)
            
            # 6. 添加到历史记录
            self.add_to_history(yuejiang, shichen, ri_gan, ri_zhi, sanchuan_result)
            
            # 7. 更新状态
            self.status_var.set(
                f"验证完成 - 课体：{sanchuan_result['课体']} | 起法：{sanchuan_result['起法']}"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"计算失败：{str(e)}")
            self.status_var.set("计算失败")
    
    def display_results(self, tiandi_pan: Dict, sike: List, sanchuan_result: Dict):
        """显示结果"""
        # 1. 显示天地盘
        self.tiandi_pan_text.delete(1.0, tk.END)
        tiandi_output = self.format_tiandi_pan(tiandi_pan)
        self.tiandi_pan_text.insert(tk.END, tiandi_output)
        
        # 2. 显示四课
        self.sike_text.delete(1.0, tk.END)
        sike_output = self.format_sike(sike)
        self.sike_text.insert(tk.END, sike_output)
        
        # 3. 显示三传
        self.sanchuan_text.delete(1.0, tk.END)
        sanchuan_output = self.format_sanchuan(sanchuan_result)
        self.sanchuan_text.insert(tk.END, sanchuan_output)
    
    def format_tiandi_pan(self, tiandi_pan: Dict) -> str:
        """格式化天地盘输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("天地盘排布")
        lines.append("=" * 60)
        lines.append("")
        
        dizhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 分组显示，每行 4 个
        for i in range(0, 12, 4):
            line_parts = []
            for j in range(4):
                if i + j < 12:
                    dizhi = dizhi_list[i + j]
                    tian = tiandi_pan[dizhi]
                    line_parts.append(f"地盘{dizhi:2s} → 天盘{tian:2s}")
            lines.append("    ".join(line_parts))
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_sike(self, sike: List) -> str:
        """格式化四课输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("四课")
        lines.append("=" * 60)
        lines.append("")
        
        for name, shang, xia, _ in sike:
            # 检查是否有克贼
            ke_type = self.calculator.is_ke(shang, xia)
            ke_info = f" [{ke_type}]" if ke_type else ""
            
            line = f"  {name}: 上{shang:2s} 下{xia:2s}{ke_info}"
            lines.append(line)
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_sanchuan(self, sanchuan_result: Dict) -> str:
        """格式化三传输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("三传")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"  初传：{sanchuan_result.get('初传', ''):2s}")
        lines.append(f"  中传：{sanchuan_result.get('中传', ''):2s}")
        lines.append(f"  末传：{sanchuan_result.get('末传', ''):2s}")
        lines.append("")
        lines.append(f"  课体：{sanchuan_result.get('课体', '')}")
        lines.append(f"  起法：{sanchuan_result.get('起法', '')}")
        
        # 显示涉害深度（如果有）
        if '涉害深度' in sanchuan_result:
            lines.append(f"  涉害深度：{sanchuan_result['涉害深度']}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def check_and_mark_errors(self, sike: List, sanchuan_result: Dict, 
                              tiandi_pan: Dict, ri_gan: str, ri_zhi: str):
        """检查并标记错误"""
        self.error_marks = []
        self.error_mark_listbox.delete(0, tk.END)
        
        # 错误检测规则
        errors = []
        
        # 1. 检查四课数量
        if len(sike) != 4:
            errors.append(f"错误：四课数量异常（应为 4 课，实际{len(sike)}课）")
        
        # 2. 检查三传完整性
        if not all([sanchuan_result.get('初传'), 
                   sanchuan_result.get('中传'), 
                   sanchuan_result.get('末传')]):
            errors.append("警告：三传不完整")
        
        # 3. 检查课体是否合理
        valid_ke_ti = [
            '元首课', '重审课', '比用课', '涉害课', '见机格', '缀瑕格',
            '遥克课', '昴星课', '别责课', '八专课', '伏吟课', '反吟课'
        ]
        if sanchuan_result.get('课体') not in valid_ke_ti:
            errors.append(f"警告：可疑课体 '{sanchuan_result.get('课体')}'")
        
        # 4. 检查伏吟课
        is_fu_yin = self.calculator._is_fu_yin(tiandi_pan)
        if is_fu_yin and '伏吟' not in sanchuan_result.get('起法', ''):
            errors.append("警告：天地盘伏吟但未用伏吟法")
        
        # 5. 检查反吟课
        is_fan_yin = self.calculator._is_fan_yin(tiandi_pan)
        if is_fan_yin and '反吟' not in sanchuan_result.get('起法', ''):
            errors.append("警告：天地盘反吟但未用反吟法")
        
        # 6. 检查八专课
        is_ba_zhuan = self.calculator._is_ba_zhuan(ri_gan, ri_zhi)
        if is_ba_zhuan and '八专' not in sanchuan_result.get('起法', ''):
            errors.append("警告：八专日但未用八专法")
        
        # 7. 检查别责课
        is_bie_ze = self.calculator._is_bie_ze(sike, ri_gan)
        if is_bie_ze and '别责' not in sanchuan_result.get('起法', ''):
            errors.append("警告：别责格但未用别责法")
        
        # 添加错误标记
        for error in errors:
            self.error_marks.append(error)
            self.error_mark_listbox.insert(tk.END, error)
        
        if errors:
            # 高亮显示错误
            self.sanchuan_text.tag_configure(
                'error', 
                background='#FFEBEE', 
                foreground='#C62828'
            )
            self.sanchuan_text.tag_add('error', '1.0', tk.END)
        else:
            # 移除高亮
            self.sanchuan_text.tag_delete('error')
            self.status_var.set(
                f"✓ 验证通过 - 课体：{sanchuan_result['课体']} | 起法：{sanchuan_result['起法']}"
            )
    
    def add_to_history(self, yuejiang: str, shichen: str, ri_gan: str, ri_zhi: str, 
                      sanchuan_result: Dict):
        """添加到历史记录"""
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'yuejiang': yuejiang,
            'shichen': shichen,
            'ri_gan': ri_gan,
            'ri_zhi': ri_zhi,
            'result': sanchuan_result
        }
        
        # 添加到历史记录列表
        self.history.insert(0, record)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # 更新历史记录列表框
        self.update_history_listbox()
    
    def update_history_listbox(self):
        """更新历史记录列表框"""
        self.history_listbox.delete(0, tk.END)
        
        for i, record in enumerate(self.history, 1):
            summary = (
                f"{i}. {record['timestamp']} | "
                f"{record['yuejiang']}{record['shichen']} {record['ri_gan']}{record['ri_zhi']} | "
                f"{record['result']['课体']}"
            )
            self.history_listbox.insert(tk.END, summary)
    
    def on_history_selected(self, event):
        """历史记录被选中"""
        pass
    
    def load_selected_history(self):
        """加载选中的历史记录"""
        try:
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一条历史记录")
                return
            
            index = selection[0]
            record = self.history[index]
            
            # 填充输入框
            # 找到对应的月将索引
            yuejiang_values = [v.split('(')[0].strip() for v in self.yuejiang_combo['values']]
            if record['yuejiang'] in yuejiang_values:
                self.yuejiang_combo.current(yuejiang_values.index(record['yuejiang']))
            
            self.shichen_combo.set(record['shichen'])
            self.ri_gan_combo.set(record['ri_gan'])
            self.ri_zhi_combo.set(record['ri_zhi'])
            
            # 重新计算并显示
            self.calculate_and_verify()
            
            self.status_var.set(f"已加载历史记录 #{index + 1}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载历史记录失败：{str(e)}")
    
    def delete_selected_history(self):
        """删除选中的历史记录"""
        try:
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一条历史记录")
                return
            
            index = selection[0]
            del self.history[index]
            self.update_history_listbox()
            
            self.status_var.set("已删除历史记录")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除历史记录失败：{str(e)}")
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.history = []
            self.update_history_listbox()
            self.status_var.set("已清空历史记录")
    
    def clear_input(self):
        """清空输入"""
        self.yuejiang_combo.current(0)
        self.shichen_combo.current(2)
        self.ri_gan_combo.current(0)
        self.ri_zhi_combo.current(0)
        
        self.tiandi_pan_text.delete(1.0, tk.END)
        self.sike_text.delete(1.0, tk.END)
        self.sanchuan_text.delete(1.0, tk.END)
        
        self.clear_error_marks()
        
        self.status_var.set("已清空输入")
    
    def clear_error_marks(self):
        """清空错误标记"""
        self.error_marks = []
        self.error_mark_listbox.delete(0, tk.END)
        self.sanchuan_text.tag_delete('error')
    
    def save_current_result(self):
        """保存当前结果"""
        try:
            # 获取当前参数
            yuejiang_full = self.yuejiang_var.get()
            yuejiang = yuejiang_full.split('(')[0].strip()
            shichen = self.shichen_var.get()
            ri_gan = self.ri_gan_var.get()
            ri_zhi = self.ri_zhi_var.get()
            
            # 获取显示内容
            tiandi_pan_content = self.tiandi_pan_text.get(1.0, tk.END)
            sike_content = self.sike_text.get(1.0, tk.END)
            sanchuan_content = self.sanchuan_text.get(1.0, tk.END)
            
            # 保存为文本文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"verification_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("大六壬四课三传验证结果\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"月将：{yuejiang}\n")
                f.write(f"占时：{shichen}\n")
                f.write(f"日干：{ri_gan}\n")
                f.write(f"日支：{ri_zhi}\n\n")
                f.write(tiandi_pan_content + "\n\n")
                f.write(sike_content + "\n\n")
                f.write(sanchuan_content + "\n\n")
                
                if self.error_marks:
                    f.write("=" * 80 + "\n")
                    f.write("错误标记\n")
                    f.write("=" * 80 + "\n")
                    for error in self.error_marks:
                        f.write(f"  • {error}\n")
            
            messagebox.showinfo("成功", f"结果已保存到：{filename}")
            self.status_var.set(f"结果已保存到：{filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def export_history(self):
        """导出历史记录"""
        try:
            if not self.history:
                messagebox.showinfo("提示", "历史记录为空")
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"history_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"历史记录已导出到：{filename}")
            self.status_var.set(f"历史记录已导出到：{filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出历史记录失败：{str(e)}")
    
    def load_history(self):
        """加载历史记录（从文件）"""
        # 这里可以从文件加载历史记录，暂时留空
        pass
    
    def show_help(self):
        """显示使用说明"""
        help_text = """
大六壬四课三传验证系统使用说明
================================

【功能简介】
本系统用于验证大六壬四课三传的起课规则，支持九种起课法则：
1. 贼克法  2. 比用法  3. 涉害法  4. 遥克法  5. 昴星法
6. 别责法  7. 八专法  8. 伏吟法  9. 反吟法

【使用方法】
1. 输入参数：
   - 月将：选择月将（十二神将）
   - 占时：选择占时（十二地支）
   - 日干：选择日干（十天干）
   - 日支：选择日支（十二地支）

2. 点击"开始验证"按钮
   - 系统自动计算天地盘、四课、三传
   - 显示详细的起课过程和结果
   - 自动检测并标记可疑错误

3. 查看结果：
   - 天地盘排布：显示地盘与天盘的对应关系
   - 四课显示：显示四课的上神下神及克贼情况
   - 三传显示：显示初传、中传、末传及课体起法

4. 错误标记功能：
   - 自动检测四课数量异常
   - 检测三传完整性
   - 检测课体合理性
   - 检测特殊课式（伏吟、反吟、八专、别责）是否正确应用

5. 历史记录功能：
   - 自动保存每次验证记录
   - 可点击历史记录重新加载参数
   - 可删除单条或清空所有历史记录
   - 支持导出历史记录为 JSON 文件

【错误标记说明】
系统会自动检测以下错误：
- 四课数量异常（应为 4 课）
- 三传不完整（初、中、末传缺失）
- 可疑课体（不在标准课体列表中）
- 伏吟课未用伏吟法
- 反吟课未用反吟法
- 八专日未用八专法
- 别责格未用别责法

【快捷键】
- Ctrl+N: 清空输入
- Ctrl+S: 保存当前结果
- Ctrl+H: 清空历史记录
- Ctrl+E: 导出历史记录

【注意事项】
- 所有参数必须填写完整
- 月将和占时决定天地盘
- 日干支决定四课和三传
- 系统会自动保存验证历史
"""
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
大六壬四课三传验证 2.0 增加版
============================

专业的大六壬起课验证工具

功能特性：
- 完整的四课三传计算
- 九种起课法则支持
- 智能错误检测标记
- 历史记录管理
- 结果导出保存
- 涉害法完整规则（v3.2）
- 有比用比原则支持

基于《仪度六壬选日要诀》开发
集成大六壬引擎核心算法

开发时间：2026 年
技术支持：真龙风水总馆
"""
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')  # 使用现代主题
    
    # 配置 Accent 按钮样式
    style.configure(
        'Accent.TButton',
        background='#2196F3',
        foreground='white',
        font=('微软雅黑', 10, 'bold')
    )
    style.map('Accent.TButton',
        background=[('active', '#1976D2'), ('pressed', '#0D47A1')]
    )
    
    app = SiKeSanChuanVerificationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
