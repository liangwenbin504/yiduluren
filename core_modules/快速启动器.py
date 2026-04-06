#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - 快速启动器
帮助用户了解如何使用正式程序
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class QuickLauncher:
    """快速启动器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("仪度六壬择日系统 - 启动器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(title_frame, text="仪度六壬综合择日系统", 
                 font=('Microsoft YaHei UI', 18, 'bold')).pack()
        ttk.Label(title_frame, text="增强版 v2.0", 
                 font=('Microsoft YaHei UI', 10)).pack()
        
        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # 说明区域
        info_frame = ttk.LabelFrame(self.root, text="使用说明", padding="15")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 步骤说明
        steps = [
            "1️⃣ 选择山向：点击 24 山按钮（如壬山丙向）",
            "2️⃣ 选择日期：输入开始和结束日期",
            "3️⃣ 选择课格：勾选需要的课格（如龙德课）",
            "4️⃣ 开始择日：点击\"开始择日\"按钮",
            "5️⃣ 查看结果：双击日期查看详细信息"
        ]
        
        for step in steps:
            ttk.Label(info_frame, text=step, 
                     font=('Microsoft YaHei UI', 11),
                     foreground='#333').pack(anchor=tk.W, pady=3)
        
        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # 功能特点
        features_frame = ttk.LabelFrame(self.root, text="功能特点", padding="10")
        features_frame.pack(fill=tk.X, padx=20, pady=10)
        
        features = [
            "✓ 24 山罗盘式选择",
            "✓ 13 种课格多选",
            "✓ 精确节气计算",
            "✓ AI 辅助评价"
        ]
        
        for i, feature in enumerate(features):
            ttk.Label(features_frame, text=feature, 
                     font=('Microsoft YaHei UI', 9),
                     foreground='#0066cc').grid(row=i//2, column=i%2, padx=10, pady=5, sticky=tk.W)
        
        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 启动按钮
        start_btn = ttk.Button(btn_frame, text="启动择日系统", 
                              command=self._start_app,
                              width=20)
        start_btn.pack(side=tk.LEFT, padx=10)
        
        # 测试按钮
        test_btn = ttk.Button(btn_frame, text="测试课格选择", 
                             command=self._start_test,
                             width=15)
        test_btn.pack(side=tk.LEFT, padx=10)
        
        # 帮助按钮
        help_btn = ttk.Button(btn_frame, text="帮助", 
                             command=self._show_help,
                             width=10)
        help_btn.pack(side=tk.LEFT, padx=10)
        
        # 退出按钮
        quit_btn = ttk.Button(btn_frame, text="退出", 
                             command=self.root.quit,
                             width=10)
        quit_btn.pack(side=tk.RIGHT, padx=10)
        
        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪", 
                                     foreground='green',
                                     font=('Microsoft YaHei UI', 9))
        self.status_label.pack(side=tk.LEFT)
        
        # 版权信息
        copyright_label = ttk.Label(self.root, 
                                   text="© 2026 仪度六壬",
                                   font=('Microsoft YaHei UI', 8),
                                   foreground='#999')
        copyright_label.pack(side=tk.RIGHT, padx=10)
    
    def _start_app(self):
        """启动正式程序"""
        self.status_label.config(text="正在启动...", foreground='blue')
        self.root.update()
        
        try:
            # 获取当前目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, 'enhanced_date_selector_gui.py')
            
            # 检查文件是否存在
            if not os.path.exists(script_path):
                messagebox.showerror("错误", f"找不到程序文件：{script_path}")
                self.status_label.config(text="启动失败", foreground='red')
                return
            
            # 启动程序
            subprocess.Popen([sys.executable, script_path], cwd=current_dir)
            
            self.status_label.config(text="程序已启动", foreground='green')
            
            # 提示用户
            messagebox.showinfo("提示", 
                              "择日系统已启动！\n\n"
                              "操作步骤：\n"
                              "1. 选择山向\n"
                              "2. 选择日期范围\n"
                              "3. 勾选课格类型\n"
                              "4. 点击开始择日\n\n"
                              "祝择日顺利！")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{str(e)}")
            self.status_label.config(text="启动失败", foreground='red')
    
    def _start_test(self):
        """启动测试程序"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            test_path = os.path.join(current_dir, 'test_kege_selection.py')
            
            if not os.path.exists(test_path):
                messagebox.showerror("错误", f"找不到测试程序：{test_path}")
                return
            
            subprocess.Popen([sys.executable, test_path], cwd=current_dir)
            self.status_label.config(text="测试程序已启动", foreground='green')
            
        except Exception as e:
            messagebox.showerror("错误", f"启动测试失败：{str(e)}")
            self.status_label.config(text="启动失败", foreground='red')
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
仪度六壬综合择日系统 - 使用帮助

【快速开始】
1. 点击"启动择日系统"按钮
2. 选择山向（24 山网格）
3. 选择日期范围
4. 勾选课格类型（如龙德课）
5. 点击"开始择日"
6. 查看结果

【课格类型】
富贵课、荣华课、龙德课、官爵课、时泰课、
和美课、合欢课、回环课、亨通课、华盖乘轩课、
德庆课、斫轮课、铸印乘轩课

【快捷操作】
- 全选：选择所有课格
- 取消全选：清除选择
- 仅选龙德课：快速选择龙德课
- 传统五课：选择 5 种传统吉课

【评分标准】
9-10 分：上等吉日
7-9 分：中等偏上
5-7 分：普通日课

【技术支持】
详见：快速入门指南.md
        """
        messagebox.showinfo("帮助", help_text)


def main():
    """主程序入口"""
    root = tk.Tk()
    app = QuickLauncher(root)
    root.mainloop()


if __name__ == '__main__':
    main()
