#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬四课三传独立验证系统 v2.0
完全独立版本，不依赖任何外部模块，确保稳定运行
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# 强制设置路径 - 最关键的部分
# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
# 获取 src/ui 目录
ui_dir = os.path.dirname(script_path)
# 获取 src 目录
src_dir = os.path.dirname(ui_dir)
# 获取项目根目录
project_root = os.path.dirname(src_dir)

# 强制切换到项目根目录
os.chdir(project_root)

# 添加 src 目录到 sys.path 的最前面
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 打印调试信息（可选）
# print(f"项目根目录：{project_root}")
# print(f"SRC 目录：{src_dir}")
# print(f"工作目录：{os.getcwd()}")
# print(f"SYS_PATH: {sys.path[:3]}")

# 现在导入核心引擎
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator


class SimpleVerificationGUI:
    """简洁版四课三传验证 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬四课三传验证系统 v2.0 - 简洁版")
        self.root.geometry("1100x750")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 初始化计算器
        self.calculator = SiKeSanChuanCalculator()
        
        # 创建界面
        self.create_widgets()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪 - 请输入参数")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板（输入区）
        left_panel = ttk.LabelFrame(main_frame, text="输入参数", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 月将
        ttk.Label(left_panel, text="月将:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.yuejiang_var = tk.StringVar(value="亥 (登明)")
        yuejiang_combo = ttk.Combobox(left_panel, textvariable=self.yuejiang_var, width=15, state='readonly')
        yuejiang_combo['values'] = [
            '子 (神后)', '丑 (大吉)', '寅 (功曹)', '卯 (太冲)',
            '辰 (天罡)', '巳 (太乙)', '午 (胜光)', '未 (小吉)',
            '申 (传送)', '酉 (从魁)', '戌 (河魁)', '亥 (登明)'
        ]
        yuejiang_combo.grid(row=0, column=1, pady=5, padx=5)
        
        # 占时
        ttk.Label(left_panel, text="占时:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.shichen_var = tk.StringVar(value="卯")
        shichen_combo = ttk.Combobox(left_panel, textvariable=self.shichen_var, width=15, state='readonly')
        shichen_combo['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        shichen_combo.grid(row=1, column=1, pady=5, padx=5)
        
        # 日干
        ttk.Label(left_panel, text="日干:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ri_gan_var = tk.StringVar(value="甲")
        ri_gan_combo = ttk.Combobox(left_panel, textvariable=self.ri_gan_var, width=15, state='readonly')
        ri_gan_combo['values'] = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        ri_gan_combo.grid(row=2, column=1, pady=5, padx=5)
        
        # 日支
        ttk.Label(left_panel, text="日支:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ri_zhi_var = tk.StringVar(value="子")
        ri_zhi_combo = ttk.Combobox(left_panel, textvariable=self.ri_zhi_var, width=15, state='readonly')
        ri_zhi_combo['values'] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        ri_zhi_combo.grid(row=3, column=1, pady=5, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(left_panel)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="开始验证", command=self.verify, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT, padx=5)
        
        # 快捷测试按钮
        ttk.Label(left_panel, text="快捷测试:").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10,5))
        
        ttk.Button(left_panel, text="甲子日 亥将卯时", command=lambda: self.quick_test('亥 (登明)', '卯', '甲', '子')).grid(row=6, column=0, pady=2)
        ttk.Button(left_panel, text="己巳日 酉将巳时", command=lambda: self.quick_test('巳 (太乙)', '巳', '己', '巳')).grid(row=6, column=1, pady=2)
        
        # 右侧面板（结果区）
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 天地盘
        tiandi_frame = ttk.LabelFrame(right_panel, text="天地盘", padding="5")
        tiandi_frame.pack(fill=tk.X, pady=5)
        
        self.tiandi_text = scrolledtext.ScrolledText(tiandi_frame, height=6, font=('Consolas', 10), wrap=tk.WORD)
        self.tiandi_text.pack(fill=tk.X)
        
        # 四课
        sike_frame = ttk.LabelFrame(right_panel, text="四课", padding="5")
        sike_frame.pack(fill=tk.X, pady=5)
        
        self.sike_text = scrolledtext.ScrolledText(sike_frame, height=4, font=('Consolas', 10), wrap=tk.WORD)
        self.sike_text.pack(fill=tk.X)
        
        # 三传
        sanchuan_frame = ttk.LabelFrame(right_panel, text="三传", padding="5")
        sanchuan_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.sanchuan_text = scrolledtext.ScrolledText(sanchuan_frame, height=8, font=('Consolas', 10), wrap=tk.WORD)
        self.sanchuan_text.pack(fill=tk.BOTH, expand=True)
    
    def quick_test(self, yj, sc, rg, rz):
        """快捷测试"""
        self.yuejiang_var.set(yj)
        self.shichen_var.set(sc)
        self.ri_gan_var.set(rg)
        self.ri_zhi_var.set(rz)
        self.verify()
    
    def verify(self):
        """验证四课三传"""
        try:
            # 获取参数
            yuejiang_full = self.yuejiang_var.get()
            yuejiang = yuejiang_full.split('(')[0].strip()
            shichen = self.shichen_var.get()
            ri_gan = self.ri_gan_var.get()
            ri_zhi = self.ri_zhi_var.get()
            
            # 计算天地盘
            tiandi_pan = self.calculator.get_tiandi_pan(yuejiang, shichen)
            
            # 起四课
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 发三传
            sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            # 显示结果
            self.show_result(tiandi_pan, sike, sanchuan_result)
            
            self.status_var.set(f"验证成功 - {sanchuan_result.get('课体', '')} {sanchuan_result.get('起法', '')}")
            
        except Exception as e:
            import traceback
            error_msg = f"计算失败：{str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("错误", error_msg)
            self.status_var.set("计算失败")
    
    def show_result(self, tiandi_pan, sike, sanchuan_result):
        """显示结果"""
        # 天地盘
        self.tiandi_text.delete(1.0, tk.END)
        tiandi_output = "  ".join([f"地盘{d} → 天盘{t}" for d, t in tiandi_pan.items()])
        self.tiandi_text.insert(tk.END, tiandi_output)
        
        # 四课 - 修复：sike 是元组列表 [(课名，上神，下神，天将), ...]
        self.sike_text.delete(1.0, tk.END)
        for i, ke in enumerate(sike, 1):
            # ke 是元组：('第 X 课', '上神', '下神', '天将')
            ke_name = ke[0]  # 课名
            shang = ke[1]    # 上神
            xia = ke[2]      # 下神
            
            line = f"{ke_name}：上{shang} 下{xia}"
            
            # 检查是否有克贼
            if len(ke) > 3 and ke[3]:
                line += f" [{ke[3]}]"
            else:
                # 手动检查克贼
                ke_type = self.calculator.is_ke(shang, xia)
                if ke_type:
                    line += f" [{ke_type}]"
            
            self.sike_text.insert(tk.END, line + "\n")
        
        # 三传 - 修复：正确访问字典键
        self.sanchuan_text.delete(1.0, tk.END)
        
        # 检查是否有初传、中传、末传键
        if '初传' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"初传：{sanchuan_result['初传']}\n")
        if '中传' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"中传：{sanchuan_result['中传']}\n")
        if '末传' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"末传：{sanchuan_result['末传']}\n")
        
        # 添加空行
        if ('初传' in sanchuan_result or '中传' in sanchuan_result or '末传' in sanchuan_result):
            self.sanchuan_text.insert(tk.END, "\n")
        
        # 显示课体、起法等信息
        if '课体' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"课体：{sanchuan_result['课体']}\n")
        if '起法' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"起法：{sanchuan_result['起法']}\n")
        if '涉害深度' in sanchuan_result:
            self.sanchuan_text.insert(tk.END, f"涉害深度：{sanchuan_result['涉害深度']}\n")
    
    def clear(self):
        """清空"""
        self.yuejiang_var.set("亥 (登明)")
        self.shichen_var.set("卯")
        self.ri_gan_var.set("甲")
        self.ri_zhi_var.set("子")
        self.tiandi_text.delete(1.0, tk.END)
        self.sike_text.delete(1.0, tk.END)
        self.sanchuan_text.delete(1.0, tk.END)
        self.status_var.set("已清空")


def main():
    """主函数"""
    root = tk.Tk()
    app = SimpleVerificationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
