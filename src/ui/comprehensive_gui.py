#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度六壬综合择日 GUI 系统

功能：
1. 六壬课格评分查看（下拉选择、搜索、分类浏览）
2. 斗首法与六壬法综合择日
3. 权衡算法可视化
4. 决策依据展示
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_modules.engine.kejing_scoring import KeJingScoring
from core_modules.engine.comprehensive_selector import ComprehensiveSelector
from src.utils.yiduluren_paipan import YiDuLiuRenPaiPan
from core_modules.engine.daliuren_engine import DaLiuRenEngine
from src.utils.ganzhi_calendar import get_sizhu_accurate
from core_modules.engine.comprehensive_evaluation import ComprehensiveEvaluation


class KeJingScoreViewer(ttk.Frame):
    """六壬课格评分查看器"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.scoring = KeJingScoring()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(title_frame, text="六壬课格评分查询系统", 
                 font=('微软雅黑', 16, 'bold')).pack()
        
        # 搜索框
        search_frame = ttk.LabelFrame(self, text="搜索课格", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="搜索", command=self.search_kejing).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="清除", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        # 分类选择
        category_frame = ttk.LabelFrame(self, text="分类浏览", padding=10)
        category_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(category_frame, text="吉凶等级:").pack(side=tk.LEFT, padx=5)
        
        self.category_var = tk.StringVar(value="全部")
        categories = ["全部", "上上大吉", "上吉", "中吉", "小吉", "吉凶参半", "小凶", "中凶", "大凶", "上凶"]
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                     values=categories, width=15, state='readonly')
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.filter_by_category)
        
        ttk.Button(category_frame, text="显示全部", command=self.show_all_kejing).pack(side=tk.LEFT, padx=5)
        
        # 课格列表
        list_frame = ttk.LabelFrame(self, text="课格列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建 Treeview
        columns = ('课格', '基础分', '吉凶等级', '是否可用')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # 详细信息
        detail_frame = ttk.LabelFrame(self, text="详细信息", padding=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap=tk.WORD, font=('微软雅黑', 10))
        self.detail_text.pack(fill=tk.X)
        
        # 初始化显示
        self.show_all_kejing()
    
    def show_all_kejing(self):
        """显示所有课格"""
        self.clear_tree()
        
        all_scores = self.scoring.get_all_kejing_scores()
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        
        for kejing, score in sorted_scores:
            level = self.scoring.get_score_level(score)
            usable = self.scoring.is_usable(score)
            usable_text = "✓ 可用" if usable else "✗ 不建议"
            
            self.tree.insert('', tk.END, values=(kejing, f"{score:.1f}分", level, usable_text))
    
    def search_kejing(self):
        """搜索课格"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return
        
        self.clear_tree()
        
        all_scores = self.scoring.get_all_kejing_scores()
        found = False
        
        for kejing, score in all_scores.items():
            if keyword in kejing:
                level = self.scoring.get_score_level(score)
                usable = self.scoring.is_usable(score)
                usable_text = "✓ 可用" if usable else "✗ 不建议"
                self.tree.insert('', tk.END, values=(kejing, f"{score:.1f}分", level, usable_text))
                found = True
        
        if not found:
            messagebox.showinfo("搜索结果", f"未找到包含'{keyword}'的课格")
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.show_all_kejing()
    
    def filter_by_category(self, event=None):
        """按分类筛选"""
        category = self.category_var.get()
        if category == "全部":
            self.show_all_kejing()
            return
        
        self.clear_tree()
        
        all_scores = self.scoring.get_all_kejing_scores()
        
        for kejing, score in all_scores.items():
            level = self.scoring.get_score_level(score)
            if level == category:
                usable = self.scoring.is_usable(score)
                usable_text = "✓ 可用" if usable else "✗ 不建议"
                self.tree.insert('', tk.END, values=(kejing, f"{score:.1f}分", level, usable_text))
    
    def clear_tree(self):
        """清空列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def on_select(self, event):
        """选择课格时显示详细信息"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        kejing = item['values'][0]
        score = float(item['values'][1].replace('分', ''))
        
        # 获取详细信息
        all_scores = self.scoring.get_all_kejing_scores()
        base_score = all_scores.get(kejing, 5.0)
        
        # 计算综合分（假设有贵人、禄神）
        test_score = self.scoring.calculate_score(kejing, ['贵人'], ['天德'], [])
        
        detail = f"""课格名称：{kejing}

基础评分：{base_score:.1f}分
吉凶等级：{self.scoring.get_score_level(base_score)}
是否可用：{'✓ 推荐使用' if self.scoring.is_usable(base_score) else '✗ 不建议使用'}

综合评分示例：
  - 无神煞：{base_score:.1f}分
  - 有贵人：{self.scoring.calculate_score(kejing, ['贵人'], [], []):.1f}分
  - 有贵人 + 天德：{test_score:.1f}分

评分标准：
  - 9.0-10.0: 上上大吉
  - 8.0-8.9: 上吉
  - 7.0-7.9: 中吉
  - 6.0-6.9: 小吉
  - 5.0-5.9: 吉凶参半
  - 4.0-4.9: 小凶
  - 3.0-3.9: 中凶
  - 2.0-2.9: 大凶
  - 0.0-1.9: 上凶

使用建议：
  5 分以上可用，7 分以上为吉，9 分以上为上吉
  5 分以下不建议使用"""
        
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, detail)


class ComprehensiveDateSelector(ttk.Frame):
    """综合择日系统"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.selector = ComprehensiveSelector()
        # 导入斗首二十四山系统
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
        from douhou_shan_jia_system import DouShouShanJiaKeGe
        self.shanjia = DouShouShanJiaKeGe()
        # 初始化综合评价系统
        self.evaluator = ComprehensiveEvaluation()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(title_frame, text="仪度六壬综合择日系统", 
                 font=('微软雅黑', 16, 'bold')).pack()
        
        # 参数设置
        param_frame = ttk.LabelFrame(self, text="择日参数", padding=10)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 坐山选择（第一步）
        shan_frame = ttk.Frame(param_frame)
        shan_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(shan_frame, text="【第一步】选择坐山:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, padx=5, sticky='w')
        
        # 二十四山列表
        shan_names = ['壬山', '子山', '癸山', '丑山', '艮山', '寅山', 
                      '甲山', '卯山', '乙山', '辰山', '巽山', '巳山',
                      '丙山', '午山', '丁山', '未山', '坤山', '申山',
                      '庚山', '酉山', '辛山', '戌山', '乾山', '亥山']
        
        self.shan_var = tk.StringVar()
        self.shan_combo = ttk.Combobox(shan_frame, textvariable=self.shan_var, 
                                       values=shan_names, width=15, state='readonly')
        self.shan_combo.grid(row=0, column=1, padx=5)
        self.shan_combo.current(0)
        self.shan_combo.bind('<<ComboboxSelected>>', self.on_shan_selected)
        
        # 显示元辰信息
        self.yuanchen_label = ttk.Label(shan_frame, text="元辰：--", foreground='blue')
        self.yuanchen_label.grid(row=0, column=2, padx=20)
        
        # 显示山家五行
        self.wuxing_label = ttk.Label(shan_frame, text="五行：--", foreground='green')
        self.wuxing_label.grid(row=0, column=3, padx=5)
        
        # 日期范围
        date_frame = ttk.Frame(param_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="【第二步】日期范围:").grid(row=0, column=0, padx=5, sticky='w')
        
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=1, padx=5)
        self.start_date = ttk.Entry(date_frame, width=15)
        self.start_date.grid(row=0, column=1, padx=5)
        
        # 【功能 1】自动设置开始日期为系统当前日期
        today = datetime.now()
        self.start_date.insert(0, today.strftime('%Y-%m-%d'))
        
        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=2, padx=5)
        self.end_date = ttk.Entry(date_frame, width=15)
        self.end_date.grid(row=0, column=3, padx=5)
        # 默认 30 天范围
        self.end_date.insert(0, (today + timedelta(days=30)).strftime('%Y-%m-%d'))
        
        # 评分要求
        score_frame = ttk.Frame(param_frame)
        score_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(score_frame, text="【第三步】评分要求:").grid(row=0, column=0, padx=5, sticky='w')
        
        ttk.Label(score_frame, text="斗首最低:").grid(row=0, column=1, padx=5)
        self.min_doushou = ttk.Combobox(score_frame, values=[9.0, 8.0, 7.0, 6.0, 5.0], width=8, state='readonly')
        self.min_doushou.grid(row=0, column=2, padx=5)
        self.min_doushou.current(2)  # 默认 7.0
        
        ttk.Label(score_frame, text="六壬最低:").grid(row=0, column=3, padx=5)
        self.min_kejing = ttk.Combobox(score_frame, values=[9.0, 8.0, 7.0, 6.0, 5.0], width=8, state='readonly')
        self.min_kejing.grid(row=0, column=4, padx=5)
        self.min_kejing.current(2)  # 默认 7.0
        
        # 执行按钮
        btn_frame = ttk.Frame(param_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="【第四步】开始择日", command=self.run_selection).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="清空结果", command=self.clear_result).pack(side=tk.LEFT, padx=10)
        
        # 提示标签
        tip_label = ttk.Label(param_frame, text="择日流程：选择坐山 → 设置日期 → 设置评分 → 开始择日", 
                             foreground='gray', font=('微软雅黑', 9))
        tip_label.pack(fill=tk.X, pady=5)
        
        # 四柱显示
        sizhu_frame = ttk.LabelFrame(self, text="四柱信息（年月日时）", padding=10)
        sizhu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 四柱标签
        columns = ('年柱', '月柱', '日柱', '时柱')
        self.sizhu_labels = {}
        for i, col in enumerate(columns):
            frame = ttk.Frame(sizhu_frame)
            frame.grid(row=0, column=i, padx=10, pady=5)
            
            ttk.Label(frame, text=col, font=('微软雅黑', 10, 'bold')).pack()
            label = ttk.Label(frame, text="--", font=('微软雅黑', 14), foreground='red')
            label.pack()
            self.sizhu_labels[col] = label
        
        # 六壬排盘显示
        daliuren_frame = ttk.LabelFrame(self, text="六壬排盘", padding=10)
        daliuren_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建排盘文本区域
        self.daliuren_text = scrolledtext.ScrolledText(daliuren_frame, wrap=tk.WORD, 
                                                       font=('Consolas', 10), height=15)
        self.daliuren_text.pack(fill=tk.BOTH, expand=True)
        
        # 三传显示
        san_chuan_frame = ttk.LabelFrame(self, text="三传信息（初传、中传、末传）", padding=10)
        san_chuan_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 三传标签
        self.san_chuan_labels = {}
        for i, chuan_name in enumerate(['初传', '中传', '末传']):
            frame = ttk.Frame(san_chuan_frame)
            frame.grid(row=0, column=i, padx=20, pady=5)
            
            ttk.Label(frame, text=chuan_name, font=('微软雅黑', 11, 'bold')).pack()
            label = ttk.Label(frame, text="--", font=('微软雅黑', 16, 'bold'), foreground='darkblue')
            label.pack()
            self.san_chuan_labels[chuan_name] = label
        
        # 课体显示
        self.ke_ti_label = ttk.Label(san_chuan_frame, text="课体：--", font=('微软雅黑', 11))
        self.ke_ti_label.grid(row=0, column=3, padx=20)
        
        # 起法显示
        self.qi_fa_label = ttk.Label(san_chuan_frame, text="起法：--", font=('微软雅黑', 11))
        self.qi_fa_label.grid(row=0, column=4, padx=20)
        
        # 综合吉凶评价
        pingjia_frame = ttk.LabelFrame(self, text="综合吉凶评价（0-100 分制）", padding=10)
        pingjia_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 综合评分显示
        score_display = ttk.Frame(pingjia_frame)
        score_display.pack(fill=tk.X)
        
        # 综合评分（大字体）
        self.zonghe_score_label = ttk.Label(score_display, text="综合评分：--", 
                                           font=('微软雅黑', 24, 'bold'), foreground='darkred')
        self.zonghe_score_label.pack(side=tk.LEFT, padx=20)
        
        # 吉凶等级
        self.jixiong_level_label = ttk.Label(score_display, text="吉凶等级：--", 
                                            font=('微软雅黑', 16), foreground='blue')
        self.jixiong_level_label.pack(side=tk.LEFT, padx=20)
        
        # 综合评语
        self.zonghe_pingyu_text = scrolledtext.ScrolledText(pingjia_frame, wrap=tk.WORD, 
                                                           font=('微软雅黑', 10), height=6)
        self.zonghe_pingyu_text.pack(fill=tk.X, pady=5)
        
        # 宜忌显示
        yiji_frame = ttk.Frame(pingjia_frame)
        yiji_frame.pack(fill=tk.X)
        
        self.yi_label = ttk.Label(yiji_frame, text="宜：--", font=('微软雅黑', 10, 'bold'), 
                                 foreground='green', wraplength=400, justify=tk.LEFT)
        self.yi_label.pack(side=tk.LEFT, padx=20, pady=2)
        
        self.ji_label = ttk.Label(yiji_frame, text="忌：--", font=('微软雅黑', 10, 'bold'), 
                                 foreground='red', wraplength=400, justify=tk.LEFT)
        self.ji_label.pack(side=tk.LEFT, padx=20, pady=2)
        
        # 结果展示
        result_frame = ttk.LabelFrame(self, text="择日结果", padding=10)
        result_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=('微软雅黑', 10), height=15)
        self.result_text.pack(fill=tk.X)
        
        # 初始化排盘引擎
        self.paipan = YiDuLiuRenPaiPan()
        self.daliuren = DaLiuRenEngine()
        
        # 初始化显示第一个山的元辰
        self.on_shan_selected(None)
    
    def calculate_sizhu(self, dt: datetime) -> dict:
        """
        精确计算四柱（年月日时）
        使用 get_sizhu_accurate 函数
        """
        return get_sizhu_accurate(dt.year, dt.month, dt.day, dt.hour)
    
    def display_sizhu(self, dt: datetime):
        """显示四柱"""
        sizhu = self.calculate_sizhu(dt)
        for col, ganzhi in sizhu.items():
            # 将文字改为竖排显示
            vertical_text = '\n'.join(ganzhi)
            self.sizhu_labels[col].config(text=vertical_text)
    
    def display_daliuren_paipan(self, dt: datetime, shan_name: str = None):
        """显示六壬排盘（含三传）"""
        try:
            # 获取四柱
            sizhu = self.calculate_sizhu(dt)
            ri_gan = sizhu['日柱'][0]  # 日干
            ri_zhi = sizhu['日柱'][1]  # 日支
            shi_zhi = sizhu['时柱'][1]  # 时支
            
            # 简化：假设农历月份
            lunar_month = (dt.month % 12) + 1
            yuejiang = self.paipan.get_yuejiang_by_month(lunar_month)
            
            # 排天盘
            tian_pan = self.paipan.arrange_tian_pan(yuejiang, shi_zhi)
            
            # 排四课
            try:
                si_ke = self.daliuren.arrange_si_ke(ri_gan, ri_zhi, tian_pan)
            except:
                si_ke = []
            
            # 发三传
            san_chuan_result = {}
            if si_ke:
                try:
                    san_chuan_result = self.daliuren.fa_san_chuan(si_ke, ri_gan)
                except Exception as e:
                    print(f"三传计算错误：{e}")
            
            # 构建排盘显示
            paipan_text = []
            paipan_text.append("=" * 60)
            paipan_text.append(f"日期：{dt.strftime('%Y-%m-%d %H:%M')}")
            paipan_text.append(f"四柱：{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}")
            paipan_text.append("=" * 60)
            paipan_text.append("")
            paipan_text.append("【天盘】")
            paipan_text.append(f"月将：{yuejiang}  占时：{shi_zhi}")
            paipan_text.append("")
            
            # 天盘示意图
            paipan_text.append("      巳    午    未    申")
            paipan_text.append(f"      {tian_pan.get('巳', '-'):>3}    {tian_pan.get('午', '-'):>3}    {tian_pan.get('未', '-'):>3}    {tian_pan.get('申', '-'):>3}")
            paipan_text.append(f"辰 {tian_pan.get('辰', '-'):>3}                  酉 {tian_pan.get('酉', '-'):>3}")
            paipan_text.append(f"卯 {tian_pan.get('卯', '-'):>3}                  戌 {tian_pan.get('戌', '-'):>3}")
            paipan_text.append(f"寅 {tian_pan.get('寅', '-'):>3}    丑    子    亥    酉 {tian_pan.get('亥', '-'):>3}")
            paipan_text.append(f"      {tian_pan.get('丑', '-'):>3}    {tian_pan.get('子', '-'):>3}    {tian_pan.get('亥', '-'):>3}")
            paipan_text.append("")
            
            # 四课
            paipan_text.append("【四课】")
            if si_ke:
                for i, ke in enumerate(si_ke, 1):
                    paipan_text.append(f"  第{i}课：{ke.get('top', '-')}（上） / {ke.get('bottom', '-')}（下）")
            else:
                paipan_text.append("  四课暂未计算")
            
            paipan_text.append("")
            
            # 三传
            paipan_text.append("【三传】")
            if san_chuan_result and san_chuan_result.get('三传'):
                san_chuan = san_chuan_result['三传']
                paipan_text.append(f"  初传：{san_chuan[0] if len(san_chuan) > 0 else '--'}")
                paipan_text.append(f"  中传：{san_chuan[1] if len(san_chuan) > 1 else '--'}")
                paipan_text.append(f"  末传：{san_chuan[2] if len(san_chuan) > 2 else '--'}")
                paipan_text.append(f"  课体：{san_chuan_result.get('课体', '--')}")
                paipan_text.append(f"  起法：{san_chuan_result.get('起法', '--')}")
            else:
                paipan_text.append("  三传暂未计算")
            
            paipan_text.append("")
            paipan_text.append("=" * 60)
            
            # 显示
            self.daliuren_text.delete(1.0, tk.END)
            self.daliuren_text.insert(tk.END, "\n".join(paipan_text))
            
            # 更新三传显示区域
            self.display_san_chuan(san_chuan_result)
            
        except Exception as e:
            self.daliuren_text.delete(1.0, tk.END)
            self.daliuren_text.insert(tk.END, f"排盘失败：{str(e)}\n\n请使用专业排盘软件进行验证")
    
    def display_san_chuan(self, san_chuan_result: dict):
        """显示三传信息"""
        # 重置所有标签
        for label in self.san_chuan_labels.values():
            label.config(text="--")
        self.ke_ti_label.config(text="课体：--")
        self.qi_fa_label.config(text="起法：--")
        
        if not san_chuan_result:
            return
        
        # 显示三传
        san_chuan = san_chuan_result.get('三传', [])
        if len(san_chuan) > 0 and san_chuan[0]:
            self.san_chuan_labels['初传'].config(text=san_chuan[0])
        if len(san_chuan) > 1 and san_chuan[1]:
            self.san_chuan_labels['中传'].config(text=san_chuan[1])
        if len(san_chuan) > 2 and san_chuan[2]:
            self.san_chuan_labels['末传'].config(text=san_chuan[2])
        
        # 显示课体和起法
        ke_ti = san_chuan_result.get('课体', '')
        qi_fa = san_chuan_result.get('起法', '')
        if ke_ti:
            self.ke_ti_label.config(text=f"课体：{ke_ti}")
        if qi_fa:
            self.qi_fa_label.config(text=f"起法：{qi_fa}")
    
    def on_shan_selected(self, event):
        """坐山选择事件"""
        shan_name = self.shan_var.get()
        shan_info = self.shanjia.get_shan_jia(shan_name)
        
        if shan_info:
            yuanchen = shan_info.get('yuan_chen', '--')
            wuxing = shan_info.get('wuxing', '--')
            score = shan_info.get('score', 5.0)
            
            self.yuanchen_label.config(text=f"元辰：{yuanchen}")
            self.wuxing_label.config(text=f"五行：{wuxing}")
            
            # 根据评分显示颜色
            if score >= 8.0:
                self.yuanchen_label.config(foreground='red')  # 上吉
            elif score >= 7.0:
                self.yuanchen_label.config(foreground='blue')  # 中吉
            else:
                self.yuanchen_label.config(foreground='gray')  # 一般
    
    def run_selection(self):
        """执行择日"""
        try:
            # 获取坐山信息
            shan_name = self.shan_var.get()
            shan_info = self.shanjia.get_shan_jia(shan_name)
            
            if not shan_info:
                messagebox.showwarning("警告", "请先选择坐山！")
                return
            
            yuanchen = shan_info.get('yuan_chen', '')
            wuxing = shan_info.get('wuxing', '')
            
            start = datetime.strptime(self.start_date.get(), '%Y-%m-%d')
            end = datetime.strptime(self.end_date.get(), '%Y-%m-%d')
            min_ds = float(self.min_doushou.get())
            min_kj = float(self.min_kejing.get())
            
            # 【重要】先调用精确历法计算，验证日期范围
            print("=" * 60)
            print("【精确历法计算】")
            print("=" * 60)
            
            # 计算开始日期和结束日期的四柱
            sizhu_start = get_sizhu_accurate(start.year, start.month, start.day, 12)
            sizhu_end = get_sizhu_accurate(end.year, end.month, end.day, 12)
            
            print(f"开始日期：{start.strftime('%Y-%m-%d')}")
            print(f"四柱：{sizhu_start['年柱']} {sizhu_start['月柱']} {sizhu_start['日柱']} {sizhu_start['时柱']}")
            print(f"结束日期：{end.strftime('%Y-%m-%d')}")
            print(f"四柱：{sizhu_end['年柱']} {sizhu_end['月柱']} {sizhu_end['日柱']} {sizhu_end['时柱']}")
            print()
            
            # 重定向输出
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                best_match, history = self.selector.select_auspicious_date_with_shan(
                    shan_name, yuanchen, start, end, min_ds, min_kj
                )
            
            result = f.getvalue()
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            
            # 显示最佳日期的四柱和排盘
            if best_match:
                best_date = best_match['date']
                # 默认显示子时（23-1 点）
                best_date_with_hour = best_date.replace(hour=23, minute=0)
                
                # 【精确计算】四柱
                print("\n【最佳日期精确四柱】")
                sizhu_best = get_sizhu_accurate(
                    best_date_with_hour.year,
                    best_date_with_hour.month,
                    best_date_with_hour.day,
                    best_date_with_hour.hour
                )
                
                # 显示四柱
                self.display_sizhu(best_date_with_hour)
                
                # 显示六壬排盘（含三传）
                self.display_daliuren_paipan(best_date_with_hour, shan_name)
                
                # 显示综合吉凶评价
                kejing_name = best_match.get('kejing', '')
                self.display_comprehensive_evaluation(best_date_with_hour, shan_name, kejing_name)
                
                messagebox.showinfo("择日成功", 
                                   f"坐山：{shan_name} ({wuxing}，元辰{yuanchen})\n"
                                   f"最佳日期：{best_match['date'].strftime('%Y-%m-%d')}\n"
                                   f"斗首：{best_match['doushou_kege']} ({best_match['doushou_score']:.1f}分)\n"
                                   f"六壬：{best_match['kejing']} ({best_match['kejing_score']:.1f}分)\n"
                                   f"综合评分：{best_date_with_hour.hour}时评价已生成")
            else:
                messagebox.showwarning("未找到", "未找到合适的日期组合，建议扩大范围或降低要求")
        
        except Exception as e:
            messagebox.showerror("错误", f"择日失败：{str(e)}")
    
    def clear_result(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        # 清空综合评价显示
        self.zonghe_score_label.config(text="综合评分：--")
        self.jixiong_level_label.config(text="吉凶等级：--")
        self.zonghe_pingyu_text.delete(1.0, tk.END)
        self.yi_label.config(text="宜：--")
        self.ji_label.config(text="忌：--")
        # 清空三传显示
        for label in self.san_chuan_labels.values():
            label.config(text="--")
        self.ke_ti_label.config(text="课体：--")
        self.qi_fa_label.config(text="起法：--")
    
    def display_comprehensive_evaluation(self, dt: datetime, shan_name: str, kejing_name: str):
        """显示综合吉凶评价"""
        try:
            # 调用综合评价系统
            eval_result = self.evaluator.evaluate_date(
                dt.year, dt.month, dt.day, dt.hour, 
                shan_name, kejing_name
            )
            
            # 显示综合评分
            score = eval_result.get('综合评分', 0)
            self.zonghe_score_label.config(text=f"综合评分：{score}分")
            
            # 根据分数设置颜色
            if score >= 80:
                self.zonghe_score_label.config(foreground='darkred')  # 大吉
            elif score >= 60:
                self.zonghe_score_label.config(foreground='blue')  # 吉
            elif score >= 40:
                self.zonghe_score_label.config(foreground='black')  # 平
            else:
                self.zonghe_score_label.config(foreground='gray')  # 凶
            
            # 显示吉凶等级
            level = eval_result.get('吉凶等级', '--')
            self.jixiong_level_label.config(text=f"吉凶等级：{level}")
            
            # 显示综合评语
            pingyu = eval_result.get('综合评语', '')
            self.zonghe_pingyu_text.delete(1.0, tk.END)
            self.zonghe_pingyu_text.insert(tk.END, pingyu)
            
            # 显示宜忌
            yiji = eval_result.get('宜忌', {})
            yi = yiji.get('宜', [])
            ji = yiji.get('忌', [])
            
            if yi:
                self.yi_label.config(text=f"宜：{','.join(yi)}")
            else:
                self.yi_label.config(text="宜：--")
            
            if ji:
                self.ji_label.config(text=f"忌：{','.join(ji)}")
            else:
                self.ji_label.config(text="忌：--")
            
        except Exception as e:
            print(f"综合评价失败：{e}")
            self.zonghe_pingyu_text.delete(1.0, tk.END)
            self.zonghe_pingyu_text.insert(tk.END, f"综合评价计算失败：{str(e)}")


class MainApplication(ttk.Frame):
    """主应用程序"""
    
    def __init__(self, parent):
        super().__init__(parent)
        parent.title("仪度六壬综合系统 - 课格评分与择日")
        parent.geometry("1000x700")
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 课格评分查看器
        self.score_viewer = KeJingScoreViewer(self.notebook)
        self.notebook.add(self.score_viewer, text="六壬课格评分")
        
        # 综合择日系统
        self.date_selector = ComprehensiveDateSelector(self.notebook)
        self.notebook.add(self.date_selector, text="综合择日")
        
        self.pack(fill=tk.BOTH, expand=True)


def main():
    """主函数"""
    root = tk.Tk()
    app = MainApplication(root)
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('vista')  # Windows 样式
    
    root.mainloop()


if __name__ == '__main__':
    main()
