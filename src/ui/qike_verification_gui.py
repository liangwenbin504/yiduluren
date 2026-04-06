#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬起课方法验证测试系统 - 专业版
专门用于验证各种起课方法的正确性
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# 路径设置
script_path = os.path.abspath(__file__)
ui_dir = os.path.dirname(script_path)
src_dir = os.path.dirname(ui_dir)
project_root = os.path.dirname(src_dir)
os.chdir(project_root)

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from engine.sike_sanchuan_engine import SiKeSanChuanCalculator


class QikeVerificationGUI:
    """起课方法验证 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬起课方法验证系统 - 专业测试版")
        self.root.geometry("1400x900")
        
        # 设置背景色
        self.root.configure(bg='#f5f5f5')
        
        # 初始化计算器
        self.calculator = SiKeSanChuanCalculator()
        
        # 创建界面
        self.create_main_layout()
        self.create_menu()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 请输入起课参数进行验证")
        self.status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            height=1,
            bg='#1976D2',
            fg='white',
            font=('微软雅黑', 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="清空", command=self.clear_all, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Alt+F4")
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-n>', lambda e: self.clear_all())
    
    def create_main_layout(self):
        """创建主布局"""
        # 标题
        title_frame = tk.Frame(self.root, bg='white')
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="大六壬起课方法验证系统",
            font=('微软雅黑', 20, 'bold'),
            bg='white',
            fg='#1976D2'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="专业测试版 - 支持九种起课法则完整验证",
            font=('微软雅黑', 11),
            bg='white',
            fg='#666'
        )
        subtitle_label.pack(pady=5)
        
        # 主内容区
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 左侧：输入区
        left_frame = tk.LabelFrame(
            main_frame,
            text="起课参数输入",
            font=('微软雅黑', 12, 'bold'),
            bg='white',
            fg='#333',
            padx=15,
            pady=15,
            width=400
        )
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 日干支
        row1 = tk.Frame(left_frame, bg='white')
        row1.pack(fill=tk.X, pady=8)
        
        tk.Label(row1, text="日干:", font=('微软雅黑', 11), bg='white', width=6, anchor='e').pack(side=tk.LEFT)
        self.ri_gan_var = tk.StringVar()
        ri_gan_combo = ttk.Combobox(row1, textvariable=self.ri_gan_var, width=8, font=('微软雅黑', 11))
        ri_gan_combo['values'] = ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸')
        ri_gan_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="日支:", font=('微软雅黑', 11), bg='white', width=6, anchor='e').pack(side=tk.LEFT, padx=(10, 0))
        self.ri_zhi_var = tk.StringVar()
        ri_zhi_combo = ttk.Combobox(row1, textvariable=self.ri_zhi_var, width=8, font=('微软雅黑', 11))
        ri_zhi_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        ri_zhi_combo.pack(side=tk.LEFT, padx=5)
        
        # 月将占时
        row2 = tk.Frame(left_frame, bg='white')
        row2.pack(fill=tk.X, pady=8)
        
        tk.Label(row2, text="月将:", font=('微软雅黑', 11), bg='white', width=6, anchor='e').pack(side=tk.LEFT)
        self.yuejiang_var = tk.StringVar()
        yuejiang_combo = ttk.Combobox(row2, textvariable=self.yuejiang_var, width=8, font=('微软雅黑', 11))
        yuejiang_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        yuejiang_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="占时:", font=('微软雅黑', 11), bg='white', width=6, anchor='e').pack(side=tk.LEFT, padx=(10, 0))
        self.shichen_var = tk.StringVar()
        shichen_combo = ttk.Combobox(row2, textvariable=self.shichen_var, width=8, font=('微软雅黑', 11))
        shichen_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        shichen_combo.pack(side=tk.LEFT, padx=5)
        
        # 验证按钮
        btn_frame = tk.Frame(left_frame, bg='white')
        btn_frame.pack(pady=20)
        
        verify_btn = tk.Button(
            btn_frame,
            text="验证起课",
            command=self.verify_qike,
            font=('微软雅黑', 12, 'bold'),
            bg='#1976D2',
            fg='white',
            width=12,
            height=2,
            relief=tk.RAISED,
            cursor='hand2'
        )
        verify_btn.pack(pady=5)
        
        clear_btn = tk.Button(
            btn_frame,
            text="清空重置",
            command=self.clear_all,
            font=('微软雅黑', 11),
            bg='#f5f5f5',
            fg='#333',
            width=12,
            height=2,
            relief=tk.RAISED,
            cursor='hand2'
        )
        clear_btn.pack(pady=5)
        
        # 常用案例快捷按钮
        case_frame = tk.LabelFrame(
            left_frame,
            text="快速测试案例",
            font=('微软雅黑', 10, 'bold'),
            bg='white',
            fg='#333',
            padx=10,
            pady=10
        )
        case_frame.pack(fill=tk.X, pady=15)
        
        # 案例 1：遥克法
        case1_btn = tk.Button(
            case_frame,
            text="遥克法案例",
            command=lambda: self.load_case('yao_ke'),
            font=('微软雅黑', 9),
            bg='#4CAF50',
            fg='white',
            width=15,
            cursor='hand2'
        )
        case1_btn.pack(pady=3)
        
        # 案例 2：涉害法
        case2_btn = tk.Button(
            case_frame,
            text="涉害法案例",
            command=lambda: self.load_case('she_hai'),
            font=('微软雅黑', 9),
            bg='#FF9800',
            fg='white',
            width=15,
            cursor='hand2'
        )
        case2_btn.pack(pady=3)
        
        # 案例 3：贼克法（刚修正的案例）
        case3_btn = tk.Button(
            case_frame,
            text="贼克法案例",
            command=lambda: self.load_case('zei_ke'),
            font=('微软雅黑', 9),
            bg='#2196F3',
            fg='white',
            width=15,
            cursor='hand2'
        )
        case3_btn.pack(pady=3)
        
        # 右侧：结果显示区
        right_frame = tk.LabelFrame(
            main_frame,
            text="验证结果详情",
            font=('微软雅黑', 12, 'bold'),
            bg='white',
            fg='#333',
            padx=15,
            pady=15
        )
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 使用 ScrolledText 显示结果
        self.result_text = scrolledtext.ScrolledText(
            right_frame,
            font=('Consolas', 10),
            bg='#ffffff',
            fg='#212121',
            wrap=tk.WORD,
            relief=tk.SUNKEN,
            bd=2,
            spacing1=5,
            spacing3=5
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def load_case(self, case_type):
        """加载测试案例"""
        cases = {
            'yao_ke': {
                'ri_gan': '辛', 'ri_zhi': '未',
                'yuejiang': '巳', 'shichen': '午'
            },
            'she_hai': {
                'ri_gan': '辛', 'ri_zhi': '未',
                'yuejiang': '巳', 'shichen': '戌'
            },
            'zei_ke': {
                'ri_gan': '壬', 'ri_zhi': '申',
                'yuejiang': '午', 'shichen': '亥'
            }
        }
        
        if case_type in cases:
            case = cases[case_type]
            self.ri_gan_var.set(case['ri_gan'])
            self.ri_zhi_var.set(case['ri_zhi'])
            self.yuejiang_var.set(case['yuejiang'])
            self.shichen_var.set(case['shichen'])
            self.status_var.set(f"已加载{case_type}案例 - 点击'验证起课'进行测试")
    
    def verify_qike(self):
        """验证起课"""
        try:
            # 获取输入
            ri_gan = self.ri_gan_var.get()
            ri_zhi = self.ri_zhi_var.get()
            yuejiang = self.yuejiang_var.get()
            shichen = self.shichen_var.get()
            
            # 验证输入
            if not all([ri_gan, ri_zhi, yuejiang, shichen]):
                messagebox.showwarning("警告", "请填写所有起课参数！")
                return
            
            # 获取天地盘
            tiandi_pan = self.calculator.get_tiandi_pan(yuejiang, shichen)
            
            # 起四课
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 发三传
            result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            # 显示结果
            self.display_result(ri_gan, ri_zhi, yuejiang, shichen, sike, result, tiandi_pan)
            
            self.status_var.set(f"验证完成 - {result.get('课体', '')} - {result.get('起法', '')}")
            
        except Exception as e:
            import traceback
            error_msg = f"验证失败：{str(e)}\n\n{traceback.format_exc()}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, error_msg)
            self.status_var.set("验证失败 - 请检查输入")
            messagebox.showerror("错误", f"验证过程中发生错误：{str(e)}")
    
    def display_result(self, ri_gan, ri_zhi, yuejiang, shichen, sike, result, tiandi_pan):
        """显示结果"""
        self.result_text.delete(1.0, tk.END)
        
        # 标题
        self.result_text.insert(tk.END, "═" * 80 + "\n")
        self.result_text.insert(tk.END, "                    大六壬起课验证结果\n")
        self.result_text.insert(tk.END, "═" * 80 + "\n\n")
        
        # 基本信息
        self.result_text.insert(tk.END, "【基本信息】\n")
        self.result_text.insert(tk.END, f"  日柱：{ri_gan}{ri_zhi}\n")
        self.result_text.insert(tk.END, f"  月将：{yuejiang}  占时：{shichen}\n")
        self.result_text.insert(tk.END, f"  阴阳：{ri_gan}日（{'阳' if self.calculator.is_yang_ri(ri_gan) else '阴'}）\n\n")
        
        # 天地盘
        self.result_text.insert(tk.END, "【天地盘】\n")
        for i, dizhi in enumerate(self.calculator.DIZHI):
            tianpan = tiandi_pan[dizhi]
            self.result_text.insert(tk.END, f"  {dizhi}:{tianpan}")
            if (i + 1) % 6 == 0:
                self.result_text.insert(tk.END, "\n")
        self.result_text.insert(tk.END, "\n\n")
        
        # 四课
        self.result_text.insert(tk.END, "【四课】\n")
        for name, shang, xia, _ in sike:
            ke_type = self.calculator.is_ke(shang, xia)
            ke_str = f" [{ke_type}]" if ke_type else ""
            self.result_text.insert(tk.END, f"  {name}：上{shang} 下{xia}{ke_str}\n")
        self.result_text.insert(tk.END, "\n")
        
        # 三传
        self.result_text.insert(tk.END, "【三传】\n")
        self.result_text.insert(tk.END, f"  初传：{result.get('初传', '')}\n")
        self.result_text.insert(tk.END, f"  中传：{result.get('中传', '')}\n")
        self.result_text.insert(tk.END, f"  末传：{result.get('末传', '')}\n\n")
        
        # 课体信息
        self.result_text.insert(tk.END, "【课体信息】\n")
        self.result_text.insert(tk.END, f"  课体：{result.get('课体', '')}\n")
        self.result_text.insert(tk.END, f"  起法：{result.get('起法', '')}\n")
        if '涉害深度' in result:
            self.result_text.insert(tk.END, f"  涉害深度：{result.get('涉害深度', '')}\n")
        if '阴阳日' in result:
            self.result_text.insert(tk.END, f"  阴阳日：{result.get('阴阳日', '')}\n")
        if '起课规则' in result:
            self.result_text.insert(tk.END, f"  起课规则：{result.get('起课规则', '')}\n")
        
        # 分析说明
        self.result_text.insert(tk.END, "\n【分析说明】\n")
        self.result_text.insert(tk.END, self.get_analysis(sike, result, ri_gan))
        
        self.result_text.insert(tk.END, "\n" + "═" * 80 + "\n")
    
    def get_analysis(self, sike, result, ri_gan):
        """获取分析说明"""
        analysis = ""
        
        # 统计克贼
        ke_count = sum(1 for _, _, _, _ in sike if self.calculator.is_ke(_, _))
        
        if '遥克' in result.get('课体', ''):
            analysis = "  此课为遥克课，四课无克贼，但日干与上神有遥克关系。\n"
            analysis += "  按照'有比用比'原则，多个遥克时应先比较阴阳，再比较数值。\n"
        elif '涉害' in result.get('课体', ''):
            analysis = "  此课为涉害课，比用后仍有多课，故用涉害法。\n"
            analysis += f"  涉害深度：{result.get('涉害深度', 'N/A')}，取涉害最深者为初传。\n"
        elif '元首' in result.get('课体', ''):
            analysis = "  此课为元首课，只有一个上克下，直接取为初传。\n"
        elif '重审' in result.get('课体', ''):
            analysis = "  此课为重审课，只有一个下贼上，直接取为初传。\n"
        
        return analysis
    
    def clear_all(self):
        """清空所有输入和结果"""
        self.ri_gan_var.set('')
        self.ri_zhi_var.set('')
        self.yuejiang_var.set('')
        self.shichen_var.set('')
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("已清空 - 请输入新的参数")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
大六壬起课方法验证系统 - 使用说明
====================================

1. 输入起课参数：
   - 日干：选择当日的天干
   - 日支：选择当日的地支
   - 月将：选择月将（太阳过宫）
   - 占时：选择占测的时辰

2. 点击"验证起课"：
   - 系统自动计算天地盘
   - 起四课并判断克贼
   - 根据九种法则发三传
   - 显示完整的验证结果

3. 快速测试案例：
   - 遥克法案例：辛未日巳将午时
   - 涉害法案例：辛未日巳将戌时
   - 贼克法案例：壬申日午将亥时（刚修正）

4. 支持的起课法则：
   - 贼克法、比用法、涉害法
   - 遥克法（v2.0 已修正比用规则）
   - 昴星法、别责法、八专法
   - 伏吟法、反吟法

5. 验证重点：
   - 遥克法：多个遥克时用涉害法（v2.0）
   - 涉害法：涉害深度计算（含终点）
   - 贼克法：比用后多课用涉害法（v3.3 修正）

提示：确保输入的日干支、月将、占时正确！
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
大六壬起课方法验证系统 - 专业测试版
====================================

版本：v2.0
开发日期：2026 年 3 月

功能特性：
- 完整的九种起课法则
- 遥克法比用规则 v2.0
- 涉害法完整规则 v3.2
- 贼克法修正 v3.3（比用后多课用涉害法）
- 专业的图形化界面
- 快速测试案例

基于《仪度六壬选日要诀》开发

祝您验证顺利！
        """
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = QikeVerificationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
