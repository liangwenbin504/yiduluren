"""
大六壬完整排盘 GUI（统一样式版本）
包含：天地盘、贵人盘、四柱、四课、三传
使用统一样式配置，确保视觉呈现一致性
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.dizhi_layout_generator import arrange_tiandi_pan, DIZHI_POSITIONS
from engine.gui_ren_engine import GuiRenCalculator
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
from engine.liuqin_engine import LiuQinCalculator
from utils.gui_style_config import COLORS, FONTS, SEPARATORS, WINDOW_SIZES, PADDING


def get_xun_shou(ri_gan: str, ri_zhi: str) -> tuple:
    """
    计算日干支的旬首和空亡（旬遁法）
    
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: (旬首天干，旬首地支，空亡地支列表)
    """
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    gan_index = stems.index(ri_gan)
    zhi_index = branches.index(ri_zhi)
    
    # 60 甲子序号计算
    ganzhi_index = (gan_index * 6 - zhi_index * 5) % 60
    if ganzhi_index < 0:
        ganzhi_index += 60
    
    # 旬首序号 = 60 甲子序号 // 10 × 10
    xun_shou_index = (ganzhi_index // 10) * 10
    
    # 旬首天干总是甲
    xun_shou_gan = '甲'
    
    # 旬首地支 = 旬首序号 % 12
    xun_shou_zhi = branches[xun_shou_index % 12]
    
    # 计算空亡
    kong_wang_index1 = (xun_shou_index % 12 + 10) % 12
    kong_wang_index2 = (xun_shou_index % 12 + 11) % 12
    kong_wang = [branches[kong_wang_index1], branches[kong_wang_index2]]
    
    return xun_shou_gan, xun_shou_zhi, kong_wang


def get_stem_for_branch(branch: str, ri_gan: str, ri_zhi: str) -> str:
    """
    根据日干支计算地支的遁干（旬遁法）
    
    :param branch: 地支
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: 遁干
    """
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 获取旬首
    xun_shou_gan, xun_shou_zhi, _ = get_xun_shou(ri_gan, ri_zhi)
    
    # 旬首地支的索引
    xun_index = branches.index(xun_shou_zhi)
    
    # 目标地支的索引
    branch_index = branches.index(branch)
    
    # 计算从旬首到目标地支的距离
    distance = (branch_index - xun_index) % 12
    
    # 遁干按天干顺序循环
    stem_index = distance % 10
    
    return stems[stem_index]


class DaliurenFullChartViewer:
    """大六壬完整排盘查看器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("大六壬完整排盘（验证模式）")
        self.root.geometry(f"{WINDOW_SIZES['full_chart'][0]}x{WINDOW_SIZES['full_chart'][1]}")
        self.root.configure(bg=COLORS['background'])
        
        # 贵人计算器
        self.gui_ren_calc = GuiRenCalculator()
        
        # 四课三传计算器
        self.sike_sanchuan_calc = SiKeSanChuanCalculator()
        
        # 六亲计算器
        self.liuqin_calc = LiuQinCalculator()
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding=str(PADDING['main']))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题（使用统一样式）
        title_label = ttk.Label(
            main_frame,
            text="大六壬完整排盘（验证模式）",
            font=FONTS['title'],
            background=COLORS['background'],
            foreground=COLORS['title']
        )
        title_label.pack(pady=10)
        
        # 月将信息提示
        hint_label = ttk.Label(
            main_frame,
            text='提示：可通过"月将"下拉框选择不同的月将值，结合日辰占时验证起课规则 | 月将参考：雨水→亥将 (登明) | 春分→戌将 (河魁) | 谷雨→酉将 (从魁) | 小满→申将 (传送)',
            font=('微软雅黑', 8),
            background='#FAF0E6',
            foreground='#555555',
            wraplength=1200
        )
        hint_label.pack(pady=5)
        
        # 创建控制框架
        control_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        control_frame.pack(fill=tk.X, pady=10)
        
        # 年柱
        ttk.Label(control_frame, text="年柱:").grid(row=0, column=0, padx=5, pady=5)
        self.nian_gan_var = tk.StringVar(value='甲')
        nian_gan_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.nian_gan_var,
            values=['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
            width=3,
            state='readonly'
        )
        nian_gan_combo.grid(row=0, column=1, padx=2, pady=5)
        
        self.nian_zhi_var = tk.StringVar(value='子')
        nian_zhi_combo = ttk.Combobox(
            control_frame,
            textvariable=self.nian_zhi_var,
            values=['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
            width=3,
            state='readonly'
        )
        nian_zhi_combo.grid(row=0, column=2, padx=2, pady=5)
        
        # 月柱
        ttk.Label(control_frame, text="月柱:").grid(row=0, column=3, padx=5, pady=5)
        self.yue_gan_var = tk.StringVar(value='丙')
        yue_gan_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.yue_gan_var,
            values=['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
            width=3,
            state='readonly'
        )
        yue_gan_combo.grid(row=0, column=4, padx=2, pady=5)
        
        self.yue_zhi_var = tk.StringVar(value='寅')
        yue_zhi_combo = ttk.Combobox(
            control_frame,
            textvariable=self.yue_zhi_var,
            values=['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
            width=3,
            state='readonly'
        )
        yue_zhi_combo.grid(row=0, column=5, padx=2, pady=5)
        
        # 日柱
        ttk.Label(control_frame, text="日柱:").grid(row=0, column=6, padx=5, pady=5)
        self.ri_gan_var = tk.StringVar(value='甲')
        ri_gan_combo = ttk.Combobox(
            control_frame,
            textvariable=self.ri_gan_var,
            values=['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
            width=3,
            state='readonly'
        )
        ri_gan_combo.grid(row=0, column=7, padx=2, pady=5)
        
        self.ri_zhi_var = tk.StringVar(value='子')
        ri_zhi_combo = ttk.Combobox(
            control_frame,
            textvariable=self.ri_zhi_var,
            values=['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
            width=3,
            state='readonly'
        )
        ri_zhi_combo.grid(row=0, column=8, padx=2, pady=5)
        
        # 时柱
        ttk.Label(control_frame, text="时柱:").grid(row=0, column=9, padx=5, pady=5)
        self.shi_gan_var = tk.StringVar(value='甲')
        shi_gan_combo = ttk.Combobox(
            control_frame,
            textvariable=self.shi_gan_var,
            values=['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
            width=3,
            state='readonly'
        )
        shi_gan_combo.grid(row=0, column=10, padx=2, pady=5)
        
        self.shi_zhi_var = tk.StringVar(value='子')
        shi_zhi_combo = ttk.Combobox(
            control_frame,
            textvariable=self.shi_zhi_var,
            values=['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
            width=3,
            state='readonly'
        )
        shi_zhi_combo.grid(row=0, column=11, padx=2, pady=5)
        
        # 月将选择栏（用于验证起课规则）
        ttk.Label(control_frame, text="月将:").grid(row=0, column=12, padx=5, pady=5)
        self.yuejiang_var = tk.StringVar(value='亥')
        yuejiang_combo = ttk.Combobox(
            control_frame,
            textvariable=self.yuejiang_var,
            values=['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
            width=3,
            state='readonly'
        )
        yuejiang_combo.grid(row=0, column=13, padx=2, pady=5)
        
        # 更新按钮
        update_btn = ttk.Button(
            control_frame,
            text="起课",
            command=self.update_display
        )
        update_btn.grid(row=0, column=14, padx=20, pady=5)
        
        # 创建画布和详细信息框架（使用 PanedWindow 确保右侧占 1/3）
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 使用 PanedWindow 控制左右比例
        paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图形画布（占 2/3）
        canvas_frame = ttk.Frame(paned)
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            width=700,
            height=650,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：详细验证信息（占 1/3）
        info_frame = ttk.LabelFrame(paned, text="起课验证详情", padding="10")
        self.info_text = tk.Text(
            info_frame,
            font=('Consolas', 9),
            bg='white',
            wrap=tk.WORD,
            padx=5,
            pady=5,
            width=55,  # 进一步增加宽度
            height=30
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.info_text, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        
        # 将两个框架添加到 PanedWindow，设置比例
        paned.add(canvas_frame, weight=2)  # 左侧占 2 份
        paned.add(info_frame, weight=1)    # 右侧占 1 份
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.info_text, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        
        # 初始显示
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        self.canvas.delete("all")
        
        # 获取参数
        nian_gan = self.nian_gan_var.get()
        nian_zhi = self.nian_zhi_var.get()
        yue_gan = self.yue_gan_var.get()
        yue_zhi = self.yue_zhi_var.get()
        ri_gan = self.ri_gan_var.get()
        ri_zhi = self.ri_zhi_var.get()
        shi_gan = self.shi_gan_var.get()
        shi_zhi = self.shi_zhi_var.get()
        
        # 月将（使用手动选择的值，用于验证起课规则）
        yuejiang = self.yuejiang_var.get()
        
        # 绘制四柱（上方）
        self.draw_sizhu(nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi, shi_gan, shi_zhi)
        
        # 计算并绘制四课（右侧）
        tiandi_pan = arrange_tiandi_pan(yuejiang, shi_zhi)
        tiandi_pan_dict = {'天地对应': tiandi_pan}
        sike = self.sike_sanchuan_calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
        # 排贵人盘获取天将
        gui_ren_result = self.gui_ren_calc.arrange_gui_ren_pan(ri_gan, tiandi_pan_dict, shi_zhi)
        self.draw_sike(sike, tiandi_pan, ri_gan, gui_ren_result)
        
        # 计算并绘制三传（天神右侧）
        sanchuan = self.sike_sanchuan_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
        self.draw_sanchuan(sanchuan, tiandi_pan, ri_gan, ri_zhi, shi_zhi)
        
        # 绘制天地盘 + 贵人盘
        self.draw_tiandi_and_guiren(yuejiang, shi_zhi, ri_gan)
        
        # 更新右侧详细验证信息
        self.update_verification_info(yuejiang, shi_zhi, ri_gan, ri_zhi, tiandi_pan, sike, sanchuan)
    
    def update_verification_info(self, yuejiang, shi_zhi, ri_gan, ri_zhi, tiandi_pan, sike, sanchuan):
        """更新右侧详细验证信息"""
        # 清空旧信息
        self.info_text.delete(1.0, tk.END)
        
        # 1. 基本信息
        self.info_text.insert(tk.END, "=" * 38 + "\n")
        self.info_text.insert(tk.END, "起课信息\n")
        self.info_text.insert(tk.END, "=" * 38 + "\n\n")
        
        self.info_text.insert(tk.END, f"日柱：{ri_gan}{ri_zhi}\n")
        self.info_text.insert(tk.END, f"占时：{shi_zhi}\n")
        self.info_text.insert(tk.END, f"月将：{yuejiang}\n\n")
        
        # 2. 天地盘
        self.info_text.insert(tk.END, "-" * 38 + "\n")
        self.info_text.insert(tk.END, "天地盘（月将加时）\n")
        self.info_text.insert(tk.END, "-" * 38 + "\n\n")
        
        self.info_text.insert(tk.END, f"月将{yuejiang}加在占时{shi_zhi}上\n\n")
        
        # 格式化显示天地盘
        for i, dizhi in enumerate(['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']):
            tian = tiandi_pan[dizhi]
            self.info_text.insert(tk.END, f"地{dizhi:2s}→天{tian:2s}  ")
            if (i + 1) % 4 == 0:
                self.info_text.insert(tk.END, "\n")
        
        self.info_text.insert(tk.END, "\n\n")
        
        # 3. 四课
        self.info_text.insert(tk.END, "-" * 38 + "\n")
        self.info_text.insert(tk.END, "四课（天干寄宫）\n")
        self.info_text.insert(tk.END, "-" * 38 + "\n\n")
        
        # 显示天干寄宫
        ji_gong = self.sike_sanchuan_calc.TIAN_GAN_JI_GONG[ri_gan]
        self.info_text.insert(tk.END, f"日干{ri_gan}寄宫在{ji_gong}\n\n")
        
        for i, (name, shang, xia, _) in enumerate(sike):
            self.info_text.insert(tk.END, f"{name}: {shang}上{xia}下\n")
        
        self.info_text.insert(tk.END, "\n")
        
        # 4. 三传
        self.info_text.insert(tk.END, "-" * 38 + "\n")
        self.info_text.insert(tk.END, "三传（九种法则）\n")
        self.info_text.insert(tk.END, "-" * 38 + "\n\n")
        
        self.info_text.insert(tk.END, f"课体：{sanchuan['课体']}\n")
        self.info_text.insert(tk.END, f"起法：{sanchuan['起法']}\n\n")
        
        self.info_text.insert(tk.END, "三传：\n")
        self.info_text.insert(tk.END, f"  初传：{sanchuan['初传']}\n")
        self.info_text.insert(tk.END, f"  中传：{sanchuan['中传']}\n")
        self.info_text.insert(tk.END, f"  末传：{sanchuan['末传']}\n\n")
        
        # 涉害深度（如果有）
        if '涉害深度' in sanchuan:
            self.info_text.insert(tk.END, f"涉害深度：{sanchuan['涉害深度']}\n\n")
        
        # 5. 规则说明
        self.info_text.insert(tk.END, "-" * 38 + "\n")
        self.info_text.insert(tk.END, "规则验证说明\n")
        self.info_text.insert(tk.END, "-" * 38 + "\n\n")
        
        qi_fa = sanchuan['起法']
        self.info_text.insert(tk.END, f"【{qi_fa}】\n\n")
        
        # 根据起法显示规则说明
        rule_explanation = self._get_rule_explanation(qi_fa, sanchuan, ri_gan, tiandi_pan)
        self.info_text.insert(tk.END, rule_explanation)
        
        self.info_text.insert(tk.END, "\n" + "=" * 38 + "\n")
    
    def _get_rule_explanation(self, qi_fa: str, sanchuan: dict, ri_gan: str, tiandi_pan: dict) -> str:
        """获取规则说明"""
        explanations = {
            '贼克法': self._explain_zai_ke(sanchuan),
            '比用法': self._explain_bi_yong(sanchuan, ri_gan),
            '涉害法': self._explain_she_hai(sanchuan),
            '遥克法': self._explain_yao_ke(),
            '昂星法': self._explain_ang_xing(ri_gan),
            '别责法': self._explain_bie_ze(),
            '八专法': self._explain_ba_zhuan(ri_gan),
            '伏吟法': self._explain_fu_yin(),
            '反吟法': self._explain_fan_yin(),
        }
        return explanations.get(qi_fa, '')
    
    def _explain_zai_ke(self, sanchuan: dict) -> str:
        """贼克法说明"""
        ke_ti = sanchuan['课体']
        if ke_ti == '元首课':
            return "四课中只有一课相克。\n上克下，尊制卑，事顺。\n取克贼之神为初传。"
        else:
            return "四课中只有一课相克。\n下贼上，卑犯尊，事逆。\n取克贼之神为初传。"
    
    def _explain_bi_yong(self, sanchuan: dict, ri_gan: str) -> str:
        """比用法说明"""
        yang_ri = ri_gan in ['甲', '丙', '戊', '庚', '壬']
        return (f"四课中有两课或以上相克。\n"
                f"取与日干阴阳相同者为用。\n"
                f"日干{ri_gan}为{'阳' if yang_ri else '阴'}，取{'阳支' if yang_ri else '阴支'}为用。")
    
    def _explain_she_hai(self, sanchuan: dict) -> str:
        """涉害法说明"""
        ke_ti = sanchuan['课体']
        depth = sanchuan.get('涉害深度', '?')
        text = ("比用后仍有多课，取涉害深者为用。\n"
                "从本位归原位，数经过的克位数量。\n"
                f"涉害深度：{depth}\n")
        if ke_ti == '见机格':
            text += "害深明显，当机立断。"
        elif ke_ti == '缀瑕格':
            text += "害深相同，取先见者。"
        else:
            text += "取涉害最深者为初传。"
        return text
    
    def _explain_yao_ke(self) -> str:
        """遥克法说明"""
        return ("四课无克贼，取遥克。\n"
                "1. 取上神克日干者（上克干）\n"
                "2. 无上克干，取日干克上神者（干克上）\n"
                "取先见者为初传。")
    
    def _explain_ang_xing(self, ri_gan: str) -> str:
        """昂星法说明"""
        yang_ri = ri_gan in ['甲', '丙', '戊', '庚', '壬']
        return (f"四课无克，非特殊格局。\n"
                f"{'阳日' if yang_ri else '阴日'}，取{'酉上神' if yang_ri else '酉下神（酉本身）'}为初传。")
    
    def _explain_bie_ze(self) -> str:
        """别责法说明"""
        return ("四课不全，只有三课。\n"
                "取干上神之合神为初传。\n"
                "中传、末传皆用日支上神。")
    
    def _explain_ba_zhuan(self, ri_gan: str) -> str:
        """八专法说明"""
        yang_ri = ri_gan in ['甲', '丙', '戊', '庚', '壬']
        return (f"干支同位（八专日），四课只有两课。\n"
                f"{'阳日' if yang_ri else '阴日'}，从干上神{'顺' if yang_ri else '逆'}数第{'三' if yang_ri else '四'}位为初传。\n"
                "中末传皆用日支上神。")
    
    def _explain_fu_yin(self) -> str:
        """伏吟法说明"""
        return ("天地盘相同（子加子、丑加丑...）。\n"
                "有克取克贼，无克用自刑。\n"
                "取日支为初传，中末传取刑位。")
    
    def _explain_fan_yin(self) -> str:
        """反吟法说明"""
        return ("天地盘对冲（子加午、丑加未...）。\n"
                "有克取克贼，无克取冲神。\n"
                "中末传取冲神，末传复归本位。")
    
    def _calculate_kong_wang(self, ri_gan: str, ri_zhi: str) -> list:
        """
        计算空亡地支
        空亡规则：甲子旬戌亥空，甲戌旬申酉空，甲申旬午未空，
                甲午旬辰巳空，甲辰旬寅卯空，甲寅旬子丑空
        
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 空亡地支列表
        """
        # 六十甲子顺序
        liujia = ['甲子', '甲戌', '甲申', '甲午', '甲辰', '甲寅']
        kong_wang_map = {
            '甲子': ['戌', '亥'],
            '甲戌': ['申', '酉'],
            '甲申': ['午', '未'],
            '甲午': ['辰', '巳'],
            '甲辰': ['寅', '卯'],
            '甲寅': ['子', '丑']
        }
        
        # 计算日柱在六十甲子中的序号
        tian_gan_list = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        di_zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 找到日柱属于哪一旬
        gan_index = tian_gan_list.index(ri_gan)
        zhi_index = di_zhi_list.index(ri_zhi)
        
        # 计算旬首（甲子、甲戌等）
        # 天干地支差值决定旬首
        diff = (zhi_index - gan_index) % 12
        diff = diff // 2  # 每两个为一旬
        
        # 确定旬首
        xun_shou = liujia[diff]
        
        # 返回空亡地支
        return kong_wang_map.get(xun_shou, [])
    
    def draw_sizhu(self, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi, shi_gan, shi_zhi):
        """绘制四柱（年柱、月柱、日柱、时柱）"""
        margin_x = 100
        margin_y = 40
        pillar_width = 60
        pillar_height = 70
        gap = 30
        
        # 标题
        self.canvas.create_text(
            margin_x + 1.5 * (pillar_width + gap),
            margin_y - 20,
            text="四柱",
            font=('微软雅黑', 12, 'bold'),
            fill='#8B0000'
        )
        
        pillars = [
            ('年柱', nian_gan, nian_zhi),
            ('月柱', yue_gan, yue_zhi),
            ('日柱', ri_gan, ri_zhi),
            ('时柱', shi_gan, shi_zhi)
        ]
        
        for i, (label, gan, zhi) in enumerate(pillars):
            x = margin_x + i * (pillar_width + gap)
            y = margin_y
            
            # 绘制框
            self.canvas.create_rectangle(
                x, y, x + pillar_width, y + pillar_height,
                fill='#FFF8DC',
                outline='#8B4513',
                width=2
            )
            
            # 标签
            self.canvas.create_text(
                x + pillar_width/2, y + 12,
                text=label,
                font=('微软雅黑', 8, 'bold'),
                fill='#8B4513'
            )
            
            # 天干（红色）
            self.canvas.create_text(
                x + pillar_width/2, y + 35,
                text=gan,
                font=('微软雅黑', 14, 'bold'),
                fill='#CD5C5C'
            )
            
            # 地支（蓝色）
            self.canvas.create_text(
                x + pillar_width/2, y + 58,
                text=zhi,
                font=('微软雅黑', 14, 'bold'),
                fill='#0066CC'
            )
    
    def draw_sike(self, sike, tiandi_pan, ri_gan, gui_ren_result):
        """绘制四课（从右往左竖排，上方显示天将）"""
        # 四课位置（右侧，远离天地盘）
        base_x = 410  # 向右移动一个图标位置（原 350 + 60 = 410）
        margin_y = 200  # 向下移动 50px，为天将预留空间（原 150）
        cell_width = 50
        cell_height = 40
        row_gap = 8
        col_gap = 55  # 调整列间距，避免与三传重叠
        
        # 天将区域参数
        tianjiang_height = 30  # 天将格子高度
        tianjiang_gap = 5  # 天将与四课的间距
        
        # 标题
        self.canvas.create_text(
            base_x + 1.5 * col_gap - 10,
            margin_y - tianjiang_height - tianjiang_gap - 10,
            text="四课",
            font=('微软雅黑', 12, 'bold'),
            fill='#8B0000'
        )
        
        # 获取天将映射
        tianjiang_mapping = gui_ren_result.get('天将映射', {})
        
        # 四课数据：[(课名，上神，下神，_), ...]
        # 从右往左：第一课（右）→ 第四课（左）
        for i, (label, shang_shen, xia_shen, _) in enumerate(sike):
            # 从右往左排列：第一课在最右（i=0, 3-i=3），第四课在最左（i=3, 3-i=0）
            x = base_x + (3 - i) * col_gap
            y = margin_y
            
            # 获取上神对应的天将
            tianjiang = tianjiang_mapping.get(shang_shen, '')
            
            # 绘制天将（浅橙色背景，位于四课上方）
            tianjiang_y = y - tianjiang_height - tianjiang_gap
            self.canvas.create_rectangle(
                x, tianjiang_y, x + cell_width, tianjiang_y + tianjiang_height,
                fill='#FFE4C4',  # 浅橙色
                outline='#8B4513',
                width=1
            )
            self.canvas.create_text(
                x + cell_width/2, tianjiang_y + tianjiang_height/2,
                text=tianjiang,
                font=('微软雅黑', 11, 'bold'),  # 加大字体（原 8 号）
                fill='#8B4513'
            )
            
            # 移除课名标签，用户已知四课排列顺序
            
            # 上神（红色）
            self.canvas.create_rectangle(
                x, y, x + cell_width, y + cell_height,
                fill='#FFF8DC',
                outline='#8B4513',
                width=1
            )
            self.canvas.create_text(
                x + cell_width/2, y + cell_height/2,
                text=shang_shen,
                font=('微软雅黑', 11, 'bold'),
                fill='#CD5C5C'
            )
            
            # 下神（蓝色）
            self.canvas.create_rectangle(
                x, y + cell_height + row_gap, 
                x + cell_width, y + cell_height * 2 + row_gap,
                fill='#B0D0F0',
                outline='#8B7355',
                width=1
            )
            self.canvas.create_text(
                x + cell_width/2, y + cell_height + row_gap + cell_height/2,
                text=xia_shen,
                font=('微软雅黑', 11, 'bold'),
                fill='#0066CC'
            )
    
    def draw_sanchuan(self, sanchuan, tiandi_pan, ri_gan, ri_zhi, shichen):
        """绘制三传（竖排，左侧六亲，右侧天将，显示完整干支，处理空亡）"""
        # 三传位置（天神右侧，靠近盘式）
        base_x = 740  # 向右移动（原 680 + 60 = 740，跟随四课移动）
        margin_y = 150
        cell_width = 50
        cell_height = 40
        gap = 10
        
        # 六亲区域参数
        liuqin_width = 40  # 六亲标注宽度（双字需要更宽）
        
        # 六亲映射（单字→双字）
        liuqin_mapping = {
            '父': '父母',
            '鬼': '官鬼',
            '子': '子孙',
            '兄': '兄弟',
            '财': '妻财'
        }
        
        # 天干推算（旬遁法）- ✅ 正确！
        # 根据日干支所属的旬，从旬首开始顺排天干
        
        # 地支序号
        dizhi_order = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5, 
                       '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
        
        # 计算空亡（根据日柱）
        kong_wang = self._calculate_kong_wang(ri_gan, ri_zhi)
        
        # 标题
        self.canvas.create_text(
            base_x + cell_width/2,
            margin_y - 30,
            text="三传",
            font=('微软雅黑', 12, 'bold'),
            fill='#8B0000'
        )
        
        # 课体信息
        ke_ti = sanchuan.get('课体', '')
        qi_fa = sanchuan.get('起法', '')
        
        self.canvas.create_text(
            base_x + cell_width/2,
            margin_y - 10,
            text=f"{ke_ti}（{qi_fa}）",
            font=('微软雅黑', 8, 'bold'),
            fill='#8B4513'
        )
        
        # 获取天将映射
        tiandi_pan_dict = {'天地对应': tiandi_pan}
        gui_ren_result = self.gui_ren_calc.arrange_gui_ren_pan(ri_gan, tiandi_pan_dict, shichen)
        tianjiang_mapping = gui_ren_result.get('天将映射', {})
        
        # 三传数据（移除标签）
        sanchuan_data = [
            sanchuan.get('初传', ''),
            sanchuan.get('中传', ''),
            sanchuan.get('末传', '')
        ]
        
        for i, zhi in enumerate(sanchuan_data):
            y = margin_y + i * (cell_height + gap + 5)
            x = base_x
            
            # 检查是否为空亡
            is_kong_wang = zhi in kong_wang
            
            if not zhi:
                continue
            
            # 计算天干（使用旬遁法）- ✅ 正确！
            tian_gan = get_stem_for_branch(zhi, ri_gan, ri_zhi)
            
            # 计算六亲
            liuqin_single = self.liuqin_calc.get_liuqin(ri_gan, zhi)
            liuqin = liuqin_mapping.get(liuqin_single, liuqin_single)  # 转换为双字
            
            # 获取天将
            tianjiang = tianjiang_mapping.get(zhi, '')
            
            # 绘制六亲标注（三传地支左侧）
            if liuqin:
                self.canvas.create_text(
                    x - liuqin_width,  # 地支左侧
                    y + cell_height/2,
                    text=liuqin,
                    font=('微软雅黑', 10, 'bold'),  # 与地支字体大小一致
                    fill='#8B4513',
                    anchor=tk.E
                )
            
            # 绘制干支（处理空亡：空亡地支不配天干，只显示地支本身）
            if is_kong_wang:
                # 空亡：只显示地支，不添加标记，颜色保持不变
                ganzhi = zhi
            else:
                # 正常：显示天干 + 地支
                ganzhi = f"{tian_gan}{zhi}"
            
            # 统一使用正常颜色，不因空亡而改变
            fill_color = '#B0D0F0'  # 正常蓝色背景
            
            self.canvas.create_rectangle(
                x, y, x + cell_width, y + cell_height,
                fill=fill_color,
                outline='#8B7355',
                width=1
            )
            self.canvas.create_text(
                x + cell_width/2, y + cell_height/2,
                text=ganzhi,
                font=('微软雅黑', 10, 'bold'),  # 缩小字体以适应干支
                fill='#0066CC'  # 统一使用蓝色，不因空亡改变
            )
            
            # 天将（地支右侧）
            if tianjiang:
                tianjiang_x = x + cell_width + 5  # 地支右侧
                self.canvas.create_rectangle(
                    tianjiang_x, y,
                    tianjiang_x + cell_width, y + cell_height,
                    fill='#FFE4C4',
                    outline='#8B4513',
                    width=1
                )
                self.canvas.create_text(
                    tianjiang_x + cell_width/2,
                    y + cell_height/2,
                    text=tianjiang,
                    font=('微软雅黑', 9, 'bold'),
                    fill='#8B4513'
                )
    
    def draw_tiandi_and_guiren(self, yuejiang, shichen, ri_gan):
        """绘制天地盘和贵人盘（移除六亲，放大 20%）"""
        # 绘制参数（放大 20%）
        cell_width = 54   # 原 45 * 1.2 = 54
        cell_height = 42  # 原 35 * 1.2 = 42
        margin_x = 50     # 向左移动（原 200）
        margin_y = 180    # 向下移动
        gap_x = 7         # 原 6 * 1.2 ≈ 7
        gap_y = 6         # 原 5 * 1.2 = 6
        
        # 贵人盘间距
        guiren_spacing = 4  # 原 3 * 1.2 ≈ 4
        
        # 排天盘
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
        tiandi_pan_dict = {'天地对应': tiandi_pan}
        
        # 排贵人盘
        gui_ren_result = self.gui_ren_calc.arrange_gui_ren_pan(ri_gan, tiandi_pan_dict, shichen)
        
        # 绘制天地盘和贵人盘
        for dizhi, (col, row) in DIZHI_POSITIONS.items():
            x = margin_x + col * (cell_width + gap_x)
            y = margin_y + row * (cell_height + gap_y)
            
            tian_zhi = tiandi_pan.get(dizhi, '')
            gui_ren = gui_ren_result['天将映射'].get(tian_zhi, '')
            
            # 移除六亲计算和显示
            
            # 绘制天地盘格子（内侧）
            fill_color = '#B0D0F0'
            self.canvas.create_rectangle(
                x, y, x + cell_width, y + cell_height,
                fill=fill_color,
                outline='#8B7355',
                width=1
            )
            
            # 绘制天盘（红色，上方，小字）
            if tian_zhi:
                self.canvas.create_text(
                    x + cell_width/2,
                    y + cell_height/2 - 6,
                    text=tian_zhi,
                    font=('微软雅黑', 11, 'bold'),  # 放大 20%：原 9 * 1.2 ≈ 11
                    fill='#CD5C5C'
                )
            
            # 绘制地盘（白色，下方）
            self.canvas.create_text(
                x + cell_width/2,
                y + cell_height/2 + 10,  # 调整位置适应放大
                text=dizhi,
                font=('微软雅黑', 6, 'bold'),  # 放大 20%：原 5 * 1.2 = 6
                fill='#FFFFFF'  # 白色
            )
            
            # 绘制贵人盘（外侧格子）
            if row == 0:  # 上排：贵人盘在上方
                guiren_x = x
                guiren_y = y - cell_height - guiren_spacing
            elif row == 3:  # 下排：贵人盘在下方
                guiren_x = x
                guiren_y = y + cell_height + guiren_spacing
            elif col == 0:  # 左列：贵人盘在左方
                guiren_x = x - cell_width - guiren_spacing
                guiren_y = y
            elif col == 3:  # 右列：贵人盘在右方
                guiren_x = x + cell_width + guiren_spacing
                guiren_y = y
            else:
                guiren_x = x
                guiren_y = y
            
            # 贵人盘背景（浅橙色）
            self.canvas.create_rectangle(
                guiren_x, guiren_y,
                guiren_x + cell_width, guiren_y + cell_height,
                fill='#FFE4C4',
                outline='#8B4513',
                width=1
            )
            
            # 绘制贵人（天将）文字
            if gui_ren:
                self.canvas.create_text(
                    guiren_x + cell_width/2,
                    guiren_y + cell_height/2,
                    text=gui_ren,
                    font=('微软雅黑', 8, 'bold'),
                    fill='#8B4513'
                )
            
            # 贵人位置红色方框标记（标记贵人）
            if gui_ren == '贵人':
                self.canvas.create_rectangle(
                    guiren_x-2, guiren_y-2, 
                    guiren_x + cell_width+2, guiren_y + cell_height+2,
                    outline='#FF0000',
                    width=2
                )


def main():
    """主函数"""
    root = tk.Tk()
    app = DaliurenFullChartViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
