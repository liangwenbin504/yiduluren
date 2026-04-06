#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
课格选择功能测试脚本
用于验证复选框选择功能是否正常
"""

import tkinter as tk
from tkinter import ttk, messagebox

# 13 种课格
KE_GE_TYPES = [
    '富贵课', '荣华课', '龙德课', '官爵课', '时泰课',
    '和美课', '合欢课', '回环课', '亨通课',
    '华盖乘轩课', '德庆课', '斫轮课', '铸印乘轩课'
]

class TestKegeSelection:
    """测试课格选择功能"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("课格选择功能测试")
        self.root.geometry("600x400")
        
        # 存储选中的课格
        self.selected_kege_types = set()
        self.kege_vars = {}
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建测试界面"""
        # 标题
        ttk.Label(self.root, text="课格选择功能测试", 
                 font=('Microsoft YaHei UI', 14, 'bold')).pack(pady=10)
        
        # 说明
        ttk.Label(self.root, text="请勾选下方的课格，观察右下角计数是否正确更新",
                 font=('Microsoft YaHei UI', 10)).pack(pady=5)
        
        # 课格复选框区域
        frame = ttk.Frame(self.root)
        frame.pack(pady=20)
        
        cols = 4
        for i, kege in enumerate(KE_GE_TYPES):
            row_idx = i // cols
            col_idx = i % cols
            
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(frame, text=kege, variable=var,
                                 command=lambda k=kege, v=var: self._toggle_kege(k, v))
            chk.grid(row=row_idx, column=col_idx, padx=15, pady=8, sticky=tk.W)
            self.kege_vars[kege] = var
        
        # 快捷按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="全选", command=self._select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消全选", command=self._deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="仅选龙德课", command=self._select_only_longde).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试开始择日", command=self._test_start).pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(self.root, text="已选：0/13", 
                                     font=('Microsoft YaHei UI', 12, 'bold'),
                                     foreground='blue')
        self.status_label.pack(pady=10)
        
        # 日志区域
        ttk.Label(self.root, text="操作日志:").pack(anchor=tk.W, padx=20)
        self.log_text = tk.Text(self.root, height=8, width=70, font=('Consolas', 9))
        self.log_text.pack(pady=5, padx=20)
    
    def _toggle_kege(self, kege, var):
        """切换课格选择状态"""
        is_checked = var.get()
        
        if is_checked:
            self.selected_kege_types.add(kege)
            action = f"✓ 勾选：{kege}"
        else:
            self.selected_kege_types.discard(kege)
            action = f"✗ 取消：{kege}"
        
        count = len(self.selected_kege_types)
        self.status_label.config(text=f"已选：{count}/13")
        self._log(action)
    
    def _select_all(self):
        """全选"""
        self._deselect_all()  # 先取消全选
        for kege, var in self.kege_vars.items():
            var.set(True)
            self.selected_kege_types.add(kege)
        self.status_label.config(text="已选：13/13")
        self._log("✓ 全选所有课格")
    
    def _deselect_all(self):
        """取消全选"""
        for var in self.kege_vars.values():
            var.set(False)
        self.selected_kege_types.clear()
        self.status_label.config(text="已选：0/13")
        self._log("✗ 取消所有选择")
    
    def _select_only_longde(self):
        """仅选龙德课"""
        self._deselect_all()
        self.kege_vars['龙德课'].set(True)
        self.selected_kege_types.add('龙德课')
        self.status_label.config(text="已选：1/13（龙德课）")
        self._log("✓ 仅选择龙德课")
    
    def _test_start(self):
        """测试开始择日"""
        if len(self.selected_kege_types) == 0:
            messagebox.showwarning("提示", "请至少选择一种课格类型")
            self._log("⚠ 验证失败：未选择任何课格")
        else:
            count = len(self.selected_kege_types)
            selected = ', '.join(self.selected_kege_types)
            messagebox.showinfo("成功", f"验证通过！\n已选择 {count} 种课格：\n{selected}")
            self._log(f"✓ 验证成功：已选择{count}种课格")
    
    def _log(self, message):
        """记录日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)


def main():
    root = tk.Tk()
    app = TestKegeSelection(root)
    root.mainloop()


if __name__ == '__main__':
    main()
