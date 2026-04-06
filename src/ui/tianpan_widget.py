"""
天盘图形化排布组件
参照传统样式设计 - 方形 12 宫格布局
"""

import tkinter as tk
from typing import Dict, List


class TianPanWidget(tk.Canvas):
    """天盘排布图形组件（方形 12 宫格）"""
    
    def __init__(self, parent, **kwargs):
        # 默认配置
        default_config = {
            'width': 500,
            'height': 500,
            'bg': '#FAF0E6',  # 米色背景
            'highlightthickness': 0
        }
        default_config.update(kwargs)
        
        super().__init__(parent, **default_config)
        
        # 颜色配置（参照图片）
        self.colors = {
            'bg_outer': '#FFE4C4',    # 外圈背景（天将层）- 浅橙色
            'bg_inner': '#F0F8FF',    # 内圈背景（地支层）- 淡蓝色
            'text_dizhi': '#2C3E50',  # 地支文字 - 深蓝灰
            'text_tian': '#CD5C5C',   # 天盘文字 - 深红色
            'text_tianjiang': '#8B4513',  # 天将文字 - 棕色
            'border': '#8B7355',      # 边框 - 古铜色
            'header': '#8B0000',      # 标题 - 深红色
        }
        
        # 布局参数
        self.cell_size = 55
        self.margin_left = 80
        self.margin_top = 50
        
        # 绑定重绘事件
        self.bind('<Configure>', self.on_resize)
    
    def draw_tiandi_pan(self, tiandi_pan: dict):
        """
        绘制天地盘
        :param tiandi_pan: 天地盘数据
        """
        self.delete("all")
        
        # 地盘位置映射（方形 12 宫格布局）
        # 布局说明：
        # 第 0 行（最下）：巳午未申
        # 第 1 行： 辰    酉
        # 第 2 行： 卯    戌
        # 第 3 行（最上）：寅丑子亥
        positions = {
            '巳': (2, 0), '午': (3, 0), '未': (4, 0), '申': (5, 0),
            '辰': (2, 1), '酉': (5, 1),  # 辰右移一格，酉左移一格
            '卯': (2, 2), '戌': (5, 2),  # 卯右移一格，戌左移一格
            '寅': (1, 3), '丑': (2, 3), '子': (3, 3), '亥': (4, 3),
        }
        
        # 绘制内圈（地盘层）
        for dizhi, (col, row) in positions.items():
            x = self.margin_left + col * self.cell_size
            y = self.margin_top + (3 - row) * self.cell_size  # Y 轴反转
            
            # 绘制背景格
            self.create_rectangle(
                x, y, x + self.cell_size, y + self.cell_size,
                fill=self.colors['bg_inner'],
                outline=self.colors['border'],
                width=1
            )
            
            # 获取天盘地支
            tian_zhi = tiandi_pan['天地对应'].get(dizhi, '')
            
            # 绘制地盘地支（下方，大字）
            self.create_text(
                x + self.cell_size/2, y + self.cell_size/2 + 12,
                text=dizhi,
                font=('微软雅黑', 14, 'bold'),
                fill=self.colors['text_dizhi']
            )
            
            # 绘制天盘地支（上方，小字红色）
            if tian_zhi:
                self.create_text(
                    x + self.cell_size/2, y + self.cell_size/2 - 6,
                    text=tian_zhi,
                    font=('微软雅黑', 11, 'bold'),
                    fill=self.colors['text_tian']
                )
        
        # 绘制标题
        self.create_text(
            self.margin_left + 3.5 * self.cell_size,
            self.margin_top - 25,
            text="天地盘",
            font=('微软雅黑', 18, 'bold'),
            fill=self.colors['header']
        )
        
        # 绘制图例说明
        self.create_text(
            self.margin_left + 3.5 * self.cell_size,
            self.margin_top + 4.5 * self.cell_size + 10,
            text="▲天盘  ▼地盘",
            font=('微软雅黑', 9),
            fill='#666666'
        )
    
    def on_resize(self, event):
        """窗口大小改变时重绘"""
        # 可以在这里添加自适应逻辑
        pass


class TianPanWithTianJiangWidget(tk.Canvas):
    """天盘 + 天将完整排布组件（正方形地支 + 外层天将）"""
    
    def __init__(self, parent, **kwargs):
        default_config = {
            'width': 700,
            'height': 550,
            'bg': '#FAF0E6',
            'highlightthickness': 0
        }
        default_config.update(kwargs)
        
        super().__init__(parent, **default_config)
        
        # 颜色配置（严格参照图片）
        self.colors = {
            'bg_tianjiang': '#FFE4C4',  # 天将背景 - 浅橙色
            'bg_dizhi': '#B0D0F0',      # 地支背景 - 中等蓝色（正方形）- 加深
            'text_dizhi': '#0000FF',    # 地支文字 - 纯蓝色（确保显示为蓝色）
            'text_tian': '#CD5C5C',     # 天盘文字 - 深红色
            'text_tianjiang': '#8B4513', # 天将文字
            'border': '#8B7355',        # 边框
            'header': '#8B0000',        # 标题
        }
        
        # 布局参数 - 闭环正方形结构（顺时针）
        self.cell_size = 55  # 地支格边长（正方形）
        self.margin_left = 100
        self.margin_top = 60
        
        # 地盘位置（方形布局 - 地盘永远固定不动）
        # 布局说明（顺时针）：
        #        巳午未申  ← 上排（4 个）
        #      辰       酉    ← 左列 + 右列
        #      卯       戌
        #        寅丑子亥  ← 下排（4 个）
        self.dizhi_positions = {
            # 上排（4 个，从左到右）
            '巳': (0, 0), '午': (1, 0), '未': (2, 0), '申': (3, 0),
            # 左列（2 个，从上到下）
            '辰': (0, 1), '卯': (0, 2),
            # 右列（2 个，从上到下，左移一格）
            '酉': (3, 1), '戌': (3, 2),
            # 下排（4 个，从右到左）
            '亥': (3, 3), '子': (2, 3), '丑': (1, 3), '寅': (0, 3),
        }
        
        # 天将位置（在地支外围，顺时针排列）
        # 上排天将（在子丑寅上方）
        # 右排天将（在卯辰巳右侧）
        # 下排天将（在午未申下方）
        # 左排天将（在酉戌亥左侧）
        self.tianjiang_positions = {
            # 上排（3 个）
            '后': (0, -1), '龙': (1, -1), '勾': (2, -1),
            # 右排（3 个）
            '合': (4, 0), '雀': (4, 1), '蛇': (4, 2),
            # 下排（3 个）
            '贵': (3, 4), '虎': (2, 4), '空': (1, 4),
            # 左排（3 个）
            '常': (-1, 3), '玄': (-1, 2), '阴': (-1, 1),
        }
    
    def draw(self, tiandi_pan: dict, tianjiang_list: List[dict] = None):
        """
        绘制完整天盘 + 天将
        :param tiandi_pan: 天地盘数据
        :param tianjiang_list: 天将列表（可选）
        """
        self.delete("all")
        
        # 1. 绘制天将（外圈）
        if tianjiang_list:
            self._draw_tianjiang(tianjiang_list, tiandi_pan)
        
        # 2. 绘制天地盘（内圈正方形）
        self._draw_tiandi_pan(tiandi_pan)
        
        # 3. 绘制标题
        self.create_text(
            self.margin_left + 2 * self.cell_size,
            self.margin_top - 40,
            text="天地盘",
            font=('微软雅黑', 20, 'bold'),
            fill=self.colors['header']
        )
        
        # 4. 绘制图例说明
        self.create_text(
            self.margin_left + 2 * self.cell_size,
            self.margin_top - 15,
            text="▲天盘 (红)  ▼地盘 (蓝)",
            font=('微软雅黑', 10),
            fill='#666666'
        )
    
    def _draw_tianjiang(self, tianjiang_list: List[dict], tiandi_pan: dict):
        """
        绘制天将外圈
        
        关键理解：
        - 天将布在天盘地支上
        - 天盘地支落地盘的某个位置
        - 天将应该显示在对应的地盘位置外围
        """
        # 创建天将映射：天盘地支 -> 天将名
        tianjiang_map = {}
        for tj in tianjiang_list:
            tian_zhi = tj['地支']  # 天盘地支
            tianjiang_name = tj['天将']
            short_name = self._get_tianjiang_short(tianjiang_name)
            tianjiang_map[tian_zhi] = short_name
        
        # 创建地盘->天盘的逆映射：天盘地支 -> 地盘地支
        tian_to_di = {}
        for di_zhi, tian_zhi in tiandi_pan['天地对应'].items():
            tian_to_di[tian_zhi] = di_zhi
        
        # 绘制每个天将
        # 天将的位置由它对应的天盘地支落地盘的位置决定
        for tian_zhi, short_name in tianjiang_map.items():
            # 找到这个天盘地支落地盘的哪个位置
            di_zhi = tian_to_di.get(tian_zhi)
            if not di_zhi:
                continue
            
            # 找到地盘位置
            di_pos = self.dizhi_positions.get(di_zhi)
            if not di_pos:
                continue
            
            col, row = di_pos
            
            # 根据地盘位置，确定天将的外围位置
            # 天将在地盘的外围一圈
            tianjiang_pos = self._get_tianjiang_position(di_zhi, col, row)
            if not tianjiang_pos:
                continue
            
            tj_col, tj_row = tianjiang_pos
            x = self.margin_left + tj_col * self.cell_size
            y = self.margin_top + tj_row * self.cell_size
            
            # 绘制背景格（浅橙色正方形）
            self.create_rectangle(
                x, y, x + self.cell_size, y + self.cell_size,
                fill=self.colors['bg_tianjiang'],
                outline=self.colors['border'],
                width=1
            )
            
            # 绘制天将文字
            self.create_text(
                x + self.cell_size/2, y + self.cell_size/2,
                text=short_name,
                font=('微软雅黑', 11, 'bold'),
                fill=self.colors['text_tianjiang']
            )
    
    def _get_tianjiang_position(self, di_zhi: str, col: int, row: int):
        """
        根据地盘位置获取天将的外围位置
        
        天将布在地盘的外围，根据地盘地支的位置确定
        """
        # 根据地盘位置，确定外围天将的位置
        # 上排（子在上方）：后龙勾
        # 右排（卯在右侧）：合雀蛇
        # 下排（午在下方）：贵虎空
        # 左排（酉在左侧）：常玄阴
        
        # 简化处理：直接用地支查找预设位置
        # 但这里的地支是地盘地支，不是天盘地支
        # 需要根据地盘地支找到对应的天将位置
        
        # 实际上，天将位置应该是固定的 12 个位置
        # 每个位置对应一个地盘地支的外围
        
        # 创建地盘地支到外围位置的映射
        outer_positions = {
            # 子上方（天将位）
            '子': (0, -1),  # 后位
            # 丑上方
            '丑': (1, -1),  # 龙位
            # 寅上方
            '寅': (2, -1),  # 勾位
            # 卯右侧
            '卯': (4, 0),   # 合位
            # 辰右侧
            '辰': (4, 1),   # 雀位
            # 巳右侧
            '巳': (4, 2),   # 蛇位
            # 午下方
            '午': (3, 4),   # 贵位
            # 未下方
            '未': (2, 4),   # 虎位
            # 申下方
            '申': (1, 4),   # 空位
            # 酉左侧
            '酉': (-1, 3),  # 常位
            # 戌左侧
            '戌': (-1, 2),  # 玄位
            # 亥左侧
            '亥': (-1, 1),  # 阴位
        }
        
        return outer_positions.get(di_zhi)
    
    def _draw_tiandi_pan(self, tiandi_pan: dict):
        """绘制天地盘内圈（正方形排列）"""
        for dizhi, (col, row) in self.dizhi_positions.items():
            x = self.margin_left + col * self.cell_size
            y = self.margin_top + row * self.cell_size
            
            # 绘制背景格（浅蓝色正方形 - 地盘）
            self.create_rectangle(
                x, y, x + self.cell_size, y + self.cell_size,
                fill=self.colors['bg_dizhi'],
                outline=self.colors['border'],
                width=1
            )
            
            # 获取天盘地支
            tian_zhi = tiandi_pan['天地对应'].get(dizhi, '')
            
            # 先绘制天盘（红色，上方，小字）- 确保在上半部分
            if tian_zhi:
                self.create_text(
                    x + self.cell_size/2, y + self.cell_size/2 - 12,
                    text=tian_zhi,
                    font=('微软雅黑', 11, 'bold'),
                    fill=self.colors['text_tian'],  # 深红色
                    tag='tian'
                )
            
            # 后绘制地盘（蓝色，下方，大字）- 确保在下半部分
            self.create_text(
                x + self.cell_size/2, y + self.cell_size/2 + 12,
                text=dizhi,
                font=('微软雅黑', 12, 'bold'),
                fill=self.colors['text_dizhi'],  # 深蓝色
                tag='di'
            )
    
    def _get_tianjiang_short(self, name: str) -> str:
        """获取天将简称"""
        mapping = {
            '贵人': '贵', '螣蛇': '蛇', '朱雀': '雀', '六合': '合',
            '勾陈': '勾', '青龙': '龙', '天空': '空', '白虎': '虎',
            '太常': '常', '玄武': '玄', '太阴': '阴', '天后': '后'
        }
        return mapping.get(name, name[0])


# 测试
if __name__ == '__main__':
    # 创建测试窗口
    root = tk.Tk()
    root.title("天盘排布测试 - 天将对应天盘")
    
    # 测试数据（月将亥，占时午）
    # 天地盘：月将亥加在地盘午位上
    # 天盘：子 (未)、丑 (申)、寅 (酉)、卯 (戌)、辰 (亥)、巳 (子)、午 (丑)、未 (寅)、申 (卯)、酉 (辰)、戌 (巳)、亥 (午)
    test_tiandi_pan = {
        '天地对应': {
            '子': '巳', '丑': '午', '寅': '未', '卯': '申',
            '辰': '酉', '巳': '戌', '午': '亥', '未': '子',
            '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'
        }
    }
    
    # 天将数据（甲日，占时午，逆行）
    # 甲日贵人丑，占时午（阴位）→ 逆行
    # 贵人丑→螣蛇子→朱雀亥→六合戌→勾陈酉→青龙申→天空未→白虎午→太常巳→玄武辰→太阴卯→天后寅
    test_tianjiang = [
        {'天将': '贵人', '地支': '丑'},  # 贵人丑，落地盘申位
        {'天将': '螣蛇', '地支': '子'},  # 螣蛇子，落地盘未位
        {'天将': '朱雀', '地支': '亥'},  # 朱雀亥，落地盘午位
        {'天将': '六合', '地支': '戌'},  # 六合戌，落地盘巳位
        {'天将': '勾陈', '地支': '酉'},  # 勾陈酉，落地盘辰位
        {'天将': '青龙', '地支': '申'},  # 青龙申，落地盘卯位
        {'天将': '天空', '地支': '未'},  # 天空未，落地盘寅位
        {'天将': '白虎', '地支': '午'},  # 白虎午，落地盘丑位
        {'天将': '太常', '地支': '巳'},  # 太常巳，落地盘子位
        {'天将': '玄武', '地支': '辰'},  # 玄武辰，落地盘亥位
        {'天将': '太阴', '地支': '卯'},  # 太阴卯，落地盘戌位
        {'天将': '天后', '地支': '寅'},  # 天后寅，落地盘酉位
    ]
    
    # 创建组件
    widget = TianPanWithTianJiangWidget(root, width=750, height=520)
    widget.pack(padx=20, pady=20)
    
    # 绘制
    widget.draw(test_tiandi_pan, test_tianjiang)
    
    # 添加说明
    info_label = tk.Label(root, text="天将对应天盘地支，天盘落地盘位置", font=('微软雅黑', 10))
    info_label.pack(pady=5)
    
    root.mainloop()
