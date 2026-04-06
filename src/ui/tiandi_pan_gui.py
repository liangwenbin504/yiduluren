"""
天地盘 GUI 可视化显示
基于 tkinter 实现环形布局显示
"""

import tkinter as tk
from utils.dizhi_layout_generator import arrange_tiandi_pan, DIZHI_POSITIONS


def draw_tiandi_pan_canvas(yuejiang: str = '亥', shichen: str = '午'):
    """
    创建天地盘可视化窗口
    
    :param yuejiang: 月将
    :param shichen: 占时
    """
    # 创建窗口
    root = tk.Tk()
    root.title(f"大六壬天地盘 - {yuejiang}将{shichen}时")
    root.geometry("600x500")
    root.configure(bg='#F5F5DC')
    
    # 创建标题
    title_frame = tk.Frame(root, bg='#8B7355', height=50)
    title_frame.pack(fill=tk.X)
    
    title_label = tk.Label(
        title_frame, 
        text=f"大六壬天地盘（{yuejiang}将加{shichen}时）",
        font=('微软雅黑', 16, 'bold'),
        bg='#8B7355',
        fg='white'
    )
    title_label.pack(pady=10)
    
    # 创建画布
    canvas = tk.Canvas(root, bg='#FFF8DC', width=550, height=400)
    canvas.pack(pady=20)
    
    # 排天地盘
    tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
    
    # 绘制参数
    cell_size = 55
    margin_left = 120
    margin_top = 80
    
    # 绘制每个地支位置
    for dizhi, (col, row) in DIZHI_POSITIONS.items():
        x = margin_left + col * cell_size
        y = margin_top + row * cell_size
        
        # 绘制格子背景
        canvas.create_rectangle(
            x, y, x+cell_size, y+cell_size,
            fill='#E0F0FF', 
            outline='#8B7355',
            width=2
        )
        
        # 显示地盘（蓝色，下方）- 固定不动
        canvas.create_text(
            x+cell_size/2, y+cell_size/2+14,
            text=dizhi, 
            font=('微软雅黑', 14, 'bold'),
            fill='#0066CC'
        )
        
        # 显示天盘（红色，上方）- 根据月将加时转动
        tianzhi = tiandi_pan.get(dizhi, '')
        if tianzhi:
            canvas.create_text(
                x+cell_size/2, y+cell_size/2-10,
                text=tianzhi, 
                font=('微软雅黑', 15, 'bold'),
                fill='#CD5C5C'
            )
    
    # 添加图例
    legend_frame = tk.Frame(root, bg='#F5F5DC')
    legend_frame.pack(pady=10)
    
    # 天盘图例
    tk.Label(
        legend_frame,
        text="■ 天盘（红色）",
        font=('微软雅黑', 10),
        bg='#F5F5DC',
        fg='#CD5C5C'
    ).pack(side=tk.LEFT, padx=20)
    
    # 地盘图例
    tk.Label(
        legend_frame,
        text="■ 地盘（蓝色）",
        font=('微软雅黑', 10),
        bg='#F5F5DC',
        fg='#0066CC'
    ).pack(side=tk.LEFT, padx=20)
    
    # 添加说明
    info_text = f"""
    排盘说明：
    • 地盘永远不动（蓝色）
    • 月将{yuejiang}加在地盘{shichen}位上
    • 天盘按子丑寅卯...顺序顺时针排布（红色）
    """
    
    info_label = tk.Label(
        root,
        text=info_text,
        font=('微软雅黑', 9),
        bg='#F5F5DC',
        justify=tk.LEFT
    )
    info_label.pack(pady=10)
    
    # 添加天地对应列表
    detail_frame = tk.Frame(root, bg='#FFF8DC')
    detail_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    tk.Label(
        detail_frame,
        text="天地对应关系：",
        font=('微软雅黑', 11, 'bold'),
        bg='#FFF8DC'
    ).pack(anchor=tk.W)
    
    # 创建对应关系文本
    detail_text = tk.Text(detail_frame, height=8, font=('微软雅黑', 10), bg='white')
    detail_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # 插入对应关系
    for i, dizhi in enumerate(DIZHI):
        tianzhi = tiandi_pan[dizhi]
        line = f"  {i+1:2d}. 地盘{dizhi:2} → 天盘{tianzhi:2}\n"
        detail_text.insert(tk.END, line)
    
    detail_text.config(state=tk.DISABLED)
    
    # 运行窗口
    root.mainloop()


def test_gui():
    """测试 GUI 显示"""
    # 示例 1：亥将午时
    draw_tiandi_pan_canvas('亥', '午')


if __name__ == '__main__':
    test_gui()
