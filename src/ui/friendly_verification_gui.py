#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬四课三传友好验证系统 - 专业版
用户友好的图形界面，支持完整的起课验证功能
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

from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2


class FriendlyVerificationGUI:
    """友好版四课三传验证 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬四课三传验证 2.0 增加版 - 专业版")
        self.root.geometry("1300x850")
        
        # 设置窗口图标（可选）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 初始化计算器
        self.calculator = SiKeSanChuanCalculator2()
        
        # 创建界面
        self.create_main_layout()
        self.create_menu()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 请输入月将和占时")
        self.status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            height=1,
            bg='#f0f0f0'
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="清空", command=self.clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_main_layout(self):
        """创建主布局"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="大六壬四课三传验证 2.0 增加版",
            font=('微软雅黑', 18, 'bold'),
            bg='white',
            fg='#1976D2'
        )
        title_label.pack(pady=(0, 20))
        
        # 输入区域
        input_frame = tk.LabelFrame(
            main_frame, 
            text="起课参数输入", 
            font=('微软雅黑', 12, 'bold'),
            bg='white',
            fg='#333',
            padx=20,
            pady=20
        )
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 第一行：日干、日支
        row1 = tk.Frame(input_frame, bg='white')
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="日干:", font=('微软雅黑', 11), bg='white', width=8, anchor='e').pack(side=tk.LEFT, padx=5)
        self.ri_gan_var = tk.StringVar()
        ri_gan_combo = ttk.Combobox(row1, textvariable=self.ri_gan_var, width=10, font=('微软雅黑', 11))
        ri_gan_combo['values'] = ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸')
        ri_gan_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="日支:", font=('微软雅黑', 11), bg='white', width=8, anchor='e').pack(side=tk.LEFT, padx=(20, 5))
        self.ri_zhi_var = tk.StringVar()
        ri_zhi_combo = ttk.Combobox(row1, textvariable=self.ri_zhi_var, width=10, font=('微软雅黑', 11))
        ri_zhi_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        ri_zhi_combo.pack(side=tk.LEFT, padx=5)
        
        # 第二行：月将、占时
        row2 = tk.Frame(input_frame, bg='white')
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="月将:", font=('微软雅黑', 11), bg='white', width=8, anchor='e').pack(side=tk.LEFT, padx=5)
        self.yuejiang_var = tk.StringVar()
        yuejiang_combo = ttk.Combobox(row2, textvariable=self.yuejiang_var, width=10, font=('微软雅黑', 11))
        yuejiang_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        yuejiang_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="占时:", font=('微软雅黑', 11), bg='white', width=8, anchor='e').pack(side=tk.LEFT, padx=(20, 5))
        self.shichen_var = tk.StringVar()
        shichen_combo = ttk.Combobox(row2, textvariable=self.shichen_var, width=10, font=('微软雅黑', 11))
        shichen_combo['values'] = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
        shichen_combo.pack(side=tk.LEFT, padx=5)
        
        # 验证按钮
        btn_frame = tk.Frame(input_frame, bg='white')
        btn_frame.pack(pady=15)
        
        verify_btn = tk.Button(
            btn_frame,
            text="验证三传",
            command=self.verify_sanchuan,
            font=('微软雅黑', 12, 'bold'),
            bg='#1976D2',
            fg='white',
            width=15,
            height=2,
            relief=tk.RAISED,
            cursor='hand2'
        )
        verify_btn.pack(side=tk.LEFT, padx=10)
        
        clear_btn = tk.Button(
            btn_frame,
            text="清空",
            command=self.clear_all,
            font=('微软雅黑', 11),
            bg='#f5f5f5',
            fg='#333',
            width=10,
            height=2,
            relief=tk.RAISED,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(
            main_frame, 
            text="验证结果", 
            font=('微软雅黑', 12, 'bold'),
            bg='white',
            fg='#333',
            padx=15,
            pady=15
        )
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 使用 ScrolledText 显示结果
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            font=('Consolas', 11),
            bg='#ffffff',
            fg='#212121',
            wrap=tk.WORD,
            relief=tk.SUNKEN,
            bd=2
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def verify_sanchuan(self):
        """验证三传"""
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
        self.result_text.insert(tk.END, "=" * 70 + "\n")
        self.result_text.insert(tk.END, f"  大六壬四课三传验证结果\n")
        self.result_text.insert(tk.END, "=" * 70 + "\n\n")
        
        # 基本信息
        self.result_text.insert(tk.END, f"【起课参数】\n")
        self.result_text.insert(tk.END, f"  日干：{ri_gan}  日支：{ri_zhi}\n")
        self.result_text.insert(tk.END, f"  月将：{yuejiang}  占时：{shichen}\n\n")
        
        # 天地盘
        self.result_text.insert(tk.END, f"【天地盘】\n")
        for i, dizhi in enumerate(self.calculator.DIZHI):
            tianpan = tiandi_pan[dizhi]
            self.result_text.insert(tk.END, f"  {dizhi}:{tianpan}  ")
            if (i + 1) % 6 == 0:
                self.result_text.insert(tk.END, "\n")
        self.result_text.insert(tk.END, "\n\n")
        
        # 四课
        self.result_text.insert(tk.END, f"【四课】\n")
        for name, shang, xia, _ in sike:
            ke_type = self.calculator.is_ke(shang, xia)
            ke_str = f" [{ke_type}]" if ke_type else ""
            self.result_text.insert(tk.END, f"  {name}：上{shang} 下{xia}{ke_str}\n")
        self.result_text.insert(tk.END, "\n")
        
        # 三传
        self.result_text.insert(tk.END, f"【三传】\n")
        self.result_text.insert(tk.END, f"  初传：{result.get('初传', '')}\n")
        self.result_text.insert(tk.END, f"  中传：{result.get('中传', '')}\n")
        self.result_text.insert(tk.END, f"  末传：{result.get('末传', '')}\n\n")
        
        # 课体信息
        self.result_text.insert(tk.END, f"【课体信息】\n")
        self.result_text.insert(tk.END, f"  课体：{result.get('课体', '')}\n")
        self.result_text.insert(tk.END, f"  起法：{result.get('起法', '')}\n")
        if '涉害深度' in result:
            self.result_text.insert(tk.END, f"  涉害深度：{result.get('涉害深度', '')}\n")
        if '阴阳日' in result:
            self.result_text.insert(tk.END, f"  阴阳日：{result.get('阴阳日', '')}\n")
        if '起课规则' in result:
            self.result_text.insert(tk.END, f"  起课规则：{result.get('起课规则', '')}\n")
        
        self.result_text.insert(tk.END, "\n" + "=" * 70 + "\n")
    
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
大六壬四课三传验证系统 - 使用说明
====================================

1. 输入起课参数：
   - 日干：选择当日的天干（甲、乙、丙、丁...）
   - 日支：选择当日的地支（子、丑、寅、卯...）
   - 月将：选择月将（太阳过宫）
   - 占时：选择占测的时辰

2. 点击"验证三传"按钮：
   - 系统会自动计算天地盘
   - 起四课并判断克贼
   - 根据九种法则发三传
   - 显示完整的验证结果

3. 查看结果：
   - 天地盘对应关系
   - 四课及克贼情况
   - 三传（初传、中传、末传）
   - 课体名称和起法

4. 支持的起课法则：
   - 贼克法、比用法、涉害法
   - 遥克法、昴星法、别责法
   - 八专法、伏吟法、反吟法

5. 涉害法完整规则（v3.2）：
   - 统计"我克者"（上神克地盘）
   - 包含天干寄宫
   - 终点位置计入
   - 有比用比原则支持

提示：确保输入的日干支、月将、占时正确！
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
大六壬四课三传验证 2.0 增加版 - 专业版
====================================

版本：v3.2
开发日期：2026 年 3 月

功能特性：
- 完整的四课三传计算
- 九种起课法则支持
- 涉害法完整规则
- 有比用比原则
- 友好的图形界面
- 实时验证反馈

基于《仪度六壬选日要诀》开发

祝您使用愉快！
        """
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = FriendlyVerificationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
