#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬排盘软件 GUI - Skill 与龙德课整合版
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
except ImportError:
    print("错误：需要安装 tkinter 库")
    sys.exit(1)

# 导入整合的排盘软件
from daliuren_paipan_software import DaLiuRenPaipanSoftware


class DaLiuRenPaipanGUI:
    """大六壬排盘软件 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬排盘软件 - Skill 与龙德课整合版")
        self.root.geometry("1400x900")
        
        # 初始化排盘软件
        self.software = DaLiuRenPaipanSoftware()
        
        # 创建界面
        self._create_menu()
        self._create_widgets()
        
        # 存储结果
        self.current_result = None
        self.best_dates = []
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出排盘结果", command=self._export_result)
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
        main_frame.rowconfigure(4, weight=1)
        
        # ===== 标题 =====
        title_label = ttk.Label(main_frame, text="大六壬排盘软件", 
                               font=('微软雅黑', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        subtitle_label = ttk.Label(main_frame, text="Skill 与龙德课整合版", 
                                  font=('微软雅黑', 10))
        subtitle_label.grid(row=1, column=0, columnspan=2)
        
        # ===== 输入区 =====
        input_frame = ttk.LabelFrame(main_frame, text="输入参数", padding="10")
        input_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # 1. 日期时间
        ttk.Label(input_frame, text="1. 日期时间:", font=('微软雅黑', 10, 'bold')).grid(
            row=0, column=0, padx=5, pady=5, sticky='w')
        
        date_frame = ttk.Frame(input_frame)
        date_frame.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # 年
        ttk.Label(date_frame, text="年:").pack(side='left')
        self.year_spin = ttk.Spinbox(date_frame, from_=1900, to=2100, width=8, state='readonly')
        self.year_spin.set(datetime.now().year)
        self.year_spin.pack(side='left', padx=2)
        
        # 月
        ttk.Label(date_frame, text="月:").pack(side='left')
        self.month_spin = ttk.Spinbox(date_frame, from_=1, to=12, width=5, state='readonly')
        self.month_spin.set(datetime.now().month)
        self.month_spin.pack(side='left', padx=2)
        
        # 日
        ttk.Label(date_frame, text="日:").pack(side='left')
        self.day_spin = ttk.Spinbox(date_frame, from_=1, to=31, width=5, state='readonly')
        self.day_spin.set(datetime.now().day)
        self.day_spin.pack(side='left', padx=2)
        
        # 时
        ttk.Label(date_frame, text="时:").pack(side='left')
        self.hour_spin = ttk.Spinbox(date_frame, from_=0, to=23, width=5, state='readonly')
        self.hour_spin.set(10)
        self.hour_spin.pack(side='left', padx=2)
        
        # 城市
        ttk.Label(date_frame, text="城市:").pack(side='left', padx=(10, 0))
        self.city_combo = ttk.Combobox(date_frame, width=10, state='readonly')
        self.city_combo['values'] = ['北京', '上海', '广州', '成都', '西安', '南京', '武汉', '重庆']
        self.city_combo.set('北京')
        self.city_combo.pack(side='left', padx=2)
        
        # 2. 山向选择（可选）
        ttk.Label(input_frame, text="2. 山向选择:", font=('微软雅黑', 10, 'bold')).grid(
            row=1, column=0, padx=5, pady=5, sticky='w')
        
        shan_frame = ttk.Frame(input_frame)
        shan_frame.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(shan_frame, text="坐山:").pack(side='left')
        self.shan_combo = ttk.Combobox(shan_frame, values=self.software.SHAN_24, width=8, state='readonly')
        self.shan_combo.set('壬')
        self.shan_combo.pack(side='left', padx=2)
        
        ttk.Label(shan_frame, text="（用于禄马贵到山到向分析）").pack(side='left', padx=10)
        
        # 操作按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="开始排盘", command=self._paipan, width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear, width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="选择最佳日期", command=self._select_best_dates, width=15).pack(side='left', padx=5)
        
        # ===== 结果显示区（左右分栏）=====
        result_frame = ttk.LabelFrame(main_frame, text="排盘结果", padding="10")
        result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        result_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(1, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 左侧：文字结果
        left_pane = ttk.Frame(result_frame)
        left_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        ttk.Label(left_pane, text="文字排盘", font=('微软雅黑', 10, 'bold')).pack(anchor='w')
        
        self.result_text = scrolledtext.ScrolledText(left_pane, wrap=tk.WORD, width=60, height=35)
        self.result_text.pack(fill='both', expand=True, pady=5)
        
        # 右侧：课体信息
        right_pane = ttk.Frame(result_frame)
        right_pane.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        ttk.Label(right_pane, text="课体与神煞", font=('微软雅黑', 10, 'bold')).pack(anchor='w')
        
        self.info_text = scrolledtext.ScrolledText(right_pane, wrap=tk.WORD, width=40, height=35)
        self.info_text.pack(fill='both', expand=True, pady=5)
        
        # ===== 状态栏 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill='x', expand=True)
    
    def _paipan(self):
        """开始排盘"""
        try:
            # 获取输入
            year = int(self.year_spin.get())
            month = int(self.month_spin.get())
            day = int(self.day_spin.get())
            hour = int(self.hour_spin.get())
            city = self.city_combo.get()
            shan = self.shan_combo.get()
            
            # 更新状态
            self.status_label.config(text=f"正在排盘：{year}年{month}月{day}日 {hour}时 ({city})...")
            self.root.update()
            
            # 排盘 + 禄马贵分析
            self.current_result = self.software.paipan_with_lu_ma_gui(
                year, month, day, hour, shan, city
            )
            
            # 显示结果
            self._display_result()
            
            # 更新状态
            self.status_label.config(text=f"排盘完成 - 综合评分：{self.current_result['综合评分']:.1f}分")
            
        except Exception as e:
            messagebox.showerror("错误", f"排盘失败：{str(e)}")
            self.status_label.config(text="排盘失败")
    
    def _display_result(self):
        """显示排盘结果"""
        if not self.current_result:
            return
        
        result = self.current_result
        paipan = result['排盘结果']
        
        # 左侧：完整排盘
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 70)
        output.append("大六壬完整排盘")
        output.append("=" * 70)
        
        # 基本信息
        output.append("\n【基本信息】")
        output.append(f"公历：{paipan['基本信息']['公历']} ({self.city_combo.get()})")
        output.append(f"四柱：{paipan['基本信息']['四柱']['年柱']}年 "
                     f"{paipan['基本信息']['四柱']['月柱']}月 "
                     f"{paipan['基本信息']['四柱']['日柱']}日 "
                     f"{paipan['基本信息']['四柱']['时柱']}时")
        output.append(f"月将：{paipan['基本信息']['月将']}  占时：{paipan['基本信息']['占时']}  旬空：{paipan['基本信息']['旬空']}")
        
        # 四课
        output.append("\n【四课】")
        for i, ke in enumerate(paipan['四课'], 1):
            gan = ke.get('天干', '')
            zhi = ke.get('地支', '')
            output.append(f"  第{i}课：{gan} {zhi}")
        
        # 三传
        output.append("\n【三传】")
        for chuan_name, chuan_value in paipan['三传'].items():
            if chuan_value:
                output.append(f"  {chuan_name}: {chuan_value}")
        
        # 天地盘
        output.append("\n【天地盘】")
        output.append("  （天盘加临地盘，月将加占时）")
        
        # 天将
        if paipan.get('天将'):
            output.append("\n【天将】")
            for jiang in paipan['天将'][:5]:
                output.append(f"  {jiang}")
        
        # 断语
        output.append("\n【断语】")
        output.append(paipan['断语'])
        
        output.append("\n" + "=" * 70)
        
        self.result_text.insert(tk.END, '\n'.join(output))
        
        # 右侧：课体与神煞信息
        self.info_text.delete(1.0, tk.END)
        
        info_output = []
        info_output.append("=" * 70)
        info_output.append("课体与神煞信息")
        info_output.append("=" * 70)
        
        # 课体判断
        info_output.append("\n【课体判断】")
        ke_ti = paipan.get('课体判断', {})
        info_output.append(f"  课体：{ke_ti.get('课体', '未知')}")
        
        # 龙德课
        info_output.append("\n【龙德课】")
        long_de = paipan.get('龙德课', {})
        if long_de['是龙德课']:
            info_output.append(f"  ✓ {long_de['类型']}")
            info_output.append("  大吉之课，主贵人扶持，百事吉利")
        else:
            info_output.append("  ✗ 非龙德课")
        
        # 禄马贵到山到向
        info_output.append("\n【禄马贵到山到向】")
        lu_ma_gui = result.get('禄马贵分析', {})
        info_output.append(f"  总数：{lu_ma_gui.get('总数', 0)}个")
        for item in lu_ma_gui.get('到山到向详情', []):
            info_output.append(f"  ✓ {item}")
        
        # 神煞
        info_output.append("\n【神煞】")
        shen_sha = paipan.get('神煞', {})
        if '吉神' in shen_sha and shen_sha['吉神']:
            info_output.append(f"  吉神：{', '.join(shen_sha['吉神'][:5])}")
        if '凶煞' in shen_sha and shen_sha['凶煞']:
            info_output.append(f"  凶煞：{', '.join(shen_sha['凶煞'][:5])}")
        
        # 综合评分
        info_output.append("\n【综合评分】")
        info_output.append(f"  评分：{result['综合评分']:.1f}分")
        info_output.append(f"  推荐：{result['推荐指数']}")
        
        info_output.append("\n" + "=" * 70)
        
        self.info_text.insert(tk.END, '\n'.join(info_output))
    
    def _select_best_dates(self):
        """选择最佳日期"""
        try:
            # 获取参数
            shan = self.shan_combo.get()
            city = self.city_combo.get()
            
            # 默认搜索下个月
            today = datetime.now()
            start_date = today
            end_date = today + timedelta(days=30)
            
            # 更新状态
            self.status_label.config(text=f"正在搜索 {shan}山 最佳日期...")
            self.root.update()
            
            # 选择最佳日期
            self.best_dates = self.software.select_best_dates(
                shan=shan,
                start_date=start_date,
                end_date=end_date,
                min_score=6.0,
                only_long_de=True
            )
            
            # 显示结果
            self._display_best_dates()
            
            # 更新状态
            self.status_label.config(text=f"找到 {len(self.best_dates)} 个符合条件的日期")
            
        except Exception as e:
            messagebox.showerror("错误", f"选择失败：{str(e)}")
            self.status_label.config(text="选择失败")
    
    def _display_best_dates(self):
        """显示最佳日期"""
        if not self.best_dates:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "未找到符合条件的日期\n请放宽筛选条件")
            return
        
        self.result_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 70)
        output.append(f"{self.shan_combo.get()}山 最佳日期（龙德课 + 评分≥6.0）")
        output.append("=" * 70)
        output.append(f"\n共找到 {len(self.best_dates)} 个符合条件的日期\n")
        
        for i, item in enumerate(self.best_dates[:10], 1):
            output.append(f"【第{i}名】{item['日期']} {item['时辰']}")
            output.append(f"  四柱：{item['四柱']['年柱']} {item['四柱']['月柱']} "
                         f"{item['四柱']['日柱']} {item['四柱']['时柱']}")
            output.append(f"  课体：{item['课体']}")
            output.append(f"  龙德课：{item['龙德课']}")
            output.append(f"  禄马贵：{item['禄马贵'].get('总数', 0)}个")
            output.append(f"  评分：{item['评分']:.1f}分")
            output.append(f"  推荐：{item['推荐']}")
            output.append("-" * 70)
        
        output.append(f"\n仅显示前 10 个，共 {len(self.best_dates)} 个")
        
        self.result_text.insert(tk.END, '\n'.join(output))
        
        # 清空右侧信息
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "双击日期可查看详细信息\n\n（功能开发中...）")
    
    def _clear(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.info_text.delete(1.0, tk.END)
        self.current_result = None
        self.best_dates = []
        self.status_label.config(text="就绪")
    
    def _export_result(self):
        """导出结果"""
        from tkinter import filedialog
        
        if not self.current_result and not self.best_dates:
            messagebox.showwarning("警告", "没有结果可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("大六壬排盘结果\n")
                    f.write("=" * 80 + "\n\n")
                    
                    if self.current_result:
                        f.write(self.result_text.get(1.0, tk.END))
                        f.write("\n")
                        f.write(self.info_text.get(1.0, tk.END))
                    
                    if self.best_dates:
                        f.write("\n\n最佳日期列表\n")
                        f.write("=" * 80 + "\n")
                        for item in self.best_dates:
                            f.write(f"\n{item['日期']} {item['时辰']}\n")
                            f.write(f"四柱：{item['四柱']}\n")
                            f.write(f"课体：{item['课体']}\n")
                            f.write(f"龙德课：{item['龙德课']}\n")
                            f.write(f"评分：{item['评分']:.1f}分\n")
                            f.write(f"推荐：{item['推荐']}\n")
                
                messagebox.showinfo("成功", f"结果已导出到：{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
【使用说明】

1. 输入日期时间：
   - 选择年、月、日、时
   - 选择城市（用于真太阳时）

2. 选择山向（可选）：
   - 用于禄马贵到山到向分析

3. 开始排盘：
   - 点击"开始排盘"按钮
   - 查看完整排盘结果

4. 选择最佳日期：
   - 点击"选择最佳日期"
   - 自动搜索下个月的最佳日期

5. 导出结果：
   - 文件 → 导出排盘结果
   - 保存为文本文件

【功能特点】

- SKILL 九宗门起课
- 龙德课自动判断
- 禄马贵到山到向
- 综合评分系统
- 真太阳时计算
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _show_about(self):
        """显示关于"""
        about_text = """
大六壬排盘软件
Skill 与龙德课整合版 v1.0

功能：
- 完整大六壬排盘
- SKILL 九宗门起课
- 龙德课判断
- 禄马贵到山到向
- 综合评分
- 最佳日期选择

技术：
- 精确历法计算
- 真太阳时支持
- 64 课经判断

2026 年 3 月
"""
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = DaLiuRenPaipanGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
