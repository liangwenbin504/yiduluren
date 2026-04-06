"""
大六壬 GUI 统一样式配置
确保所有图形界面输出格式一致
"""

# 颜色配置
COLORS = {
    'background': '#FAF0E6',      # 主背景色（淡米色）
    'title': '#8B0000',           # 标题颜色（深红色）
    'subtitle': '#555555',        # 副标题颜色（深灰色）
    'text': '#000000',            # 主要文字颜色（黑色）
    'highlight': '#FF4500',       # 高亮颜色（橙红色）
    'success': '#228B22',         # 成功标记颜色（绿色）
    'error': '#DC143C',           # 错误标记颜色（红色）
    'border': '#D2B48C',          # 边框颜色（棕褐色）
}

# 字体配置
FONTS = {
    'title': ('微软雅黑', 20, 'bold'),      # 主标题字体
    'subtitle': ('微软雅黑', 14, 'bold'),   # 副标题字体
    'normal': ('微软雅黑', 10, 'normal'),   # 正常文本字体
    'content': ('Consolas', 11, 'normal'),  # 代码/内容显示字体
    'small': ('微软雅黑', 8, 'normal'),     # 小提示字体
}

# 分隔线配置
SEPARATORS = {
    'major': '=' * 70,    # 主要分隔线（大标题）
    'minor': '-' * 70,    # 次要分隔线（小标题）
    'section': '=' * 80,  # 章节分隔线
}

# 窗口尺寸配置
WINDOW_SIZES = {
    'full_chart': (1300, 800),      # 完整排盘窗口
    'verification': (900, 700),     # 验证工具窗口
    'she_hai_test': (1000, 800),    # 涉害法测试窗口
    'demo': (900, 700),             # 演示窗口
}

# 边距配置
PADDING = {
    'main': 10,         # 主框架边距
    'control': 10,      # 控制区边距
    'content': 5,       # 内容区边距
}

# 文本对齐配置
ALIGNMENT = {
    'dizhi_width': 2,   # 地支字段宽度
    'wuxing_width': 2,  # 五行字段宽度
    'number_align': 'right',  # 数字对齐方式
}

# 涉害法显示配置
SHE_HAI_DISPLAY = {
    'show_path': True,          # 显示路径
    'show_ke_wei': True,        # 显示克位
    'mark_ke_wei': '↑',        # 克位标记符号
    'show_depth': True,         # 显示深度
    'highlight_max': True,      # 高亮最大深度
}

# 天地盘显示格式
TIANDI_PAN_FORMAT = {
    'format_string': '地盘{dizhi:2s} → 天盘{tian:2s}',
    'per_line': 4,              # 每行显示 4 个
    'spacing': '    ',          # 间隔空格
}

# 四课显示格式
SIKE_FORMAT = {
    'format_string': '  {name}: 上{shang:2s} 下{xia:2s}{ke_info}',
    'show_ke_type': True,       # 显示克贼类型
}

# 三传显示格式
SANCHUAN_FORMAT = {
    'show_ke_ti': True,         # 显示课体
    'show_qi_fa': True,         # 显示起法
    'show_depth': True,         # 显示涉害深度
    'liuqin_format': '{name}: {tian_gan}{zhi} ({liuqin_full})',
}

# 贵人盘显示格式
GUI_REN_FORMAT = {
    'show_zhou_ye': True,       # 显示昼夜
    'format_string': '  {dizhi}: {tianjiang}',
}

# 输出模板
OUTPUT_TEMPLATES = {
    'header': """
{separator_major}
{title}
{separator_major}
""",
    
    'section': """
{separator_minor}
{section_title}
{separator_minor}
""",
    
    'footer': """
{separator_major}
{footer_text}
{separator_major}
""",
}


def get_style_config():
    """获取完整的样式配置"""
    return {
        'colors': COLORS,
        'fonts': FONTS,
        'separators': SEPARATORS,
        'window_sizes': WINDOW_SIZES,
        'padding': PADDING,
        'alignment': ALIGNMENT,
        'display': SHE_HAI_DISPLAY,
        'formats': {
            'tiandi_pan': TIANDI_PAN_FORMAT,
            'sike': SIKE_FORMAT,
            'sanchuan': SANCHUAN_FORMAT,
            'gui_ren': GUI_REN_FORMAT,
        },
        'templates': OUTPUT_TEMPLATES,
    }


def apply_style(widget, style_type='normal'):
    """
    应用样式到 widget
    
    :param widget: tkinter widget
    :param style_type: 样式类型 ('title', 'subtitle', 'normal', 'content')
    """
    if style_type in FONTS:
        widget.config(font=FONTS[style_type])
    
    if style_type == 'title':
        widget.config(background=COLORS['background'], foreground=COLORS['title'])
    elif style_type == 'subtitle':
        widget.config(foreground=COLORS['subtitle'])
    elif style_type == 'content':
        widget.config(bg='white', fg=COLORS['text'])


def format_tiandi_pan(tiandi_pan):
    """格式化天地盘输出"""
    lines = []
    dizhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    for i, dizhi in enumerate(dizhi_list):
        tian = tiandi_pan[dizhi]
        line = TIANDI_PAN_FORMAT['format_string'].format(dizhi=dizhi, tian=tian)
        
        if (i + 1) % TIANDI_PAN_FORMAT['per_line'] == 0:
            lines.append(line)
        else:
            if lines:
                lines[-1] += TIANDI_PAN_FORMAT['spacing'] + line
            else:
                lines.append(line)
    
    return '\n'.join(lines)


def format_sike(sike):
    """格式化四课输出"""
    lines = []
    for name, shang, xia, _ in sike:
        ke_type = ''
        if name in ['第一课', '第二课', '第三课', '第四课']:
            # 这里需要根据实际克贼类型填充
            ke_info = ''
        else:
            ke_info = ''
        
        line = SIKE_FORMAT['format_string'].format(
            name=name, 
            shang=shang, 
            xia=xia, 
            ke_info=ke_info
        )
        lines.append(line)
    
    return '\n'.join(lines)


# 导出所有配置
__all__ = [
    'COLORS',
    'FONTS',
    'SEPARATORS',
    'WINDOW_SIZES',
    'PADDING',
    'ALIGNMENT',
    'SHE_HAI_DISPLAY',
    'TIANDI_PAN_FORMAT',
    'SIKE_FORMAT',
    'SANCHUAN_FORMAT',
    'GUI_REN_FORMAT',
    'OUTPUT_TEMPLATES',
    'get_style_config',
    'apply_style',
    'format_tiandi_pan',
    'format_sike',
]
