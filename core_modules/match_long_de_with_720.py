#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课与 720 课例匹配工具
筛选出符合龙德课条件的课例
"""

import json
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from gui_ren_engine import GuiRenCalculator


def load_720_ke_li():
    """加载 720 课例数据"""
    ke_li_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_jiu_zong_men.json')
    with open(ke_li_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('ke_li', {})


def get_tiandi_pan(yue_jiang, shi_chen):
    """
    计算天地盘
    月将加时顺数
    """
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    yue_index = branches.index(yue_jiang)
    shi_index = branches.index(shi_chen)
    
    # 月将加时顺数
    tiandi_pan = {}
    for i, branch in enumerate(branches):
        # 地盘
        di_pan = branch
        # 天盘：月将加时，顺数
        tian_index = (yue_index + i - shi_index) % 12
        tian_pan = branches[tian_index]
        tiandi_pan[di_pan] = tian_pan
    
    return tiandi_pan


def get_tian_jiang_for_chuan(chuan, ri_gan, tiandi_pan, shi_chen):
    """
    获取三传天将
    使用 GuiRenCalculator 计算
    """
    try:
        calc = GuiRenCalculator()
        # 获取天将盘
        tian_jiang_pan = calc.arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shi_chen)
        # 获取该地支的天将
        tian_jiang_map = tian_jiang_pan.get('天将映射', {})
        return tian_jiang_map.get(chuan, '')
    except Exception as e:
        print(f"计算天将失败：{e}")
        return ''


def check_long_de_ke(ke_example, calculate_tianjiang=False):
    """
    检查是否为龙德课
    龙德课条件：
    1. 初传为太岁（年支）或月将
    2. 初传乘贵人（天将为贵人）
    """
    ri_gan_zhi = ke_example['ri_gan_zhi']
    yue = ke_example['yue']
    shi = ke_example['shi']
    yue_jiang = ke_example['yue_jiang']
    sanchuan = ke_example.get('sanchuan', {})
    
    if not sanchuan or '初传' not in sanchuan:
        return False, "无初传"
    
    chu_chuan = sanchuan['初传']
    
    # 获取年支（太岁）- 简化处理，用月支代替
    tai_sui = yue  # 用月支代替年支
    
    # 检查初传是否为太岁或月将
    is_tai_sui_or_yue_jiang = (chu_chuan == tai_sui or chu_chuan == yue_jiang)
    
    # 检查初传天将是否为贵人
    tian_jiang = sanchuan.get('初传天将', '')
    
    # 如果需要计算天将且当前没有
    if calculate_tianjiang and not tian_jiang:
        # 计算天地盘
        tiandi_pan = get_tiandi_pan(yue_jiang, shi)
        # 计算天将
        ri_gan = ri_gan_zhi[0]  # 取日干
        tian_jiang = get_tian_jiang_for_chuan(chu_chuan, ri_gan, tiandi_pan, shi)
        sanchuan['初传天将'] = tian_jiang
    
    is_gui_ren = tian_jiang == '贵人'
    
    # 龙德课判断
    if is_tai_sui_or_yue_jiang and is_gui_ren:
        if chu_chuan == tai_sui:
            return True, "太岁龙德课"
        else:
            return True, "月将龙德课"
    
    # 如果只有初传条件满足，标记为潜在龙德课
    if is_tai_sui_or_yue_jiang:
        return False, f"初传符合（{chu_chuan}），但天将为{tian_jiang}"
    
    return False, "不符合龙德课条件"


def match_long_de_ke():
    """匹配龙德课与 720 课例"""
    print("=" * 60)
    print("龙德课与 720 课例匹配工具")
    print("=" * 60)
    
    # 加载 720 课例
    print("\n加载 720 课例数据...")
    ke_li = load_720_ke_li()
    print(f"共加载 {len(ke_li)} 个课例")
    
    # 匹配龙德课
    print("\n开始匹配龙德课...")
    print("提示：此过程需要计算天将，可能需要几分钟时间")
    
    long_de_ke_list = []
    fei_long_de_ke_list = []
    processed_count = 0
    
    for ke_id, ke_example in ke_li.items():
        processed_count += 1
        
        # 每处理 1000 个课例显示进度
        if processed_count % 1000 == 0:
            print(f"已处理 {processed_count}/{len(ke_li)} 个课例...")
        
        # 检查是否为龙德课（需要计算天将）
        is_long_de, reason = check_long_de_ke(ke_example, calculate_tianjiang=True)
        
        if is_long_de:
            long_de_ke_list.append({
                'ke_id': ke_id,
                'type': reason,
                'data': ke_example
            })
        else:
            fei_long_de_ke_list.append({
                'ke_id': ke_id,
                'reason': reason,
                'data': ke_example
            })
    
    print(f"\n匹配完成！")
    print(f"龙德课数量：{len(long_de_ke_list)}")
    print(f"非龙德课数量：{len(fei_long_de_ke_list)}")
    
    # 保存结果
    result = {
        'metadata': {
            'total_ke_li': len(ke_li),
            'long_de_count': len(long_de_ke_list),
            'non_long_de_count': len(fei_long_de_ke_list),
            'description': '龙德课与 720 课例匹配结果'
        },
        'long_de_ke': {item['ke_id']: item['data'] for item in long_de_ke_list},
        'long_de_ke_list': long_de_ke_list,
        'non_long_de_ke': {item['ke_id']: item['data'] for item in fei_long_de_ke_list}
    }
    
    # 保存匹配结果
    output_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_long_de_matched.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n匹配结果已保存到：{output_file}")
    
    # 显示前 10 个龙德课示例
    if long_de_ke_list:
        print("\n【前 10 个龙德课示例】")
        print("=" * 60)
        for i, item in enumerate(long_de_ke_list[:10], 1):
            ke = item['data']
            print(f"\n{i}. {item['ke_id']} - {item['type']}")
            print(f"   日干支：{ke['ri_gan_zhi']}")
            print(f"   月将：{ke['yue_jiang']}")
            print(f"   时辰：{ke['shi']}")
            sanchuan = ke.get('sanchuan', {})
            if sanchuan:
                print(f"   三传：{sanchuan.get('初传', '')} {sanchuan.get('中传', '')} {sanchuan.get('末传', '')}")
                print(f"   初传天将：{sanchuan.get('初传天将', '')}")
    
    return result


if __name__ == '__main__':
    match_long_de_ke()
