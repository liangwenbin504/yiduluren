#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出完整的斗首择日课格断语系统
包含：第一斗首课格 + 二十四山课格
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
from douhou_kege_system import DiYiDouShouKeGe
from douhou_shan_jia_system import DouShouShanJiaKeGe

def export_all_duanyu():
    """导出所有断语"""
    # 第一斗首课格
    kege_analyzer = DiYiDouShouKeGe()
    # 二十四山课格
    shanjia_analyzer = DouShouShanJiaKeGe()
    
    output_path = "斗首择日完整课格断语全集.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("斗首择日 - 完整课格断语全集\n")
        f.write("依据《斗首择日秘本》整理\n")
        f.write("=" * 70 + "\n\n")
        
        # 第一部分：第一斗首课格
        f.write("第一部分：第一斗首课格（五种课格）\n")
        f.write("=" * 70 + "\n\n")
        
        for kege_name in kege_analyzer.get_all_ke_ge_names():
            report = kege_analyzer.analyze_ke_ge(kege_name)
            f.write(report + "\n\n")
        
        # 第二部分：二十四山课格
        f.write("\n第二部分：二十四山课格\n")
        f.write("=" * 70 + "\n\n")
        
        for shanjia_name in shanjia_analyzer.get_all_shan_jia_names():
            report = shanjia_analyzer.analyze_shan_jia(shanjia_name)
            f.write(report + "\n\n")
    
    print(f"✓ 已导出到：{output_path}")
    print(f"✓ 第一斗首课格：{len(kege_analyzer.get_all_ke_ge_names())} 个")
    print(f"✓ 二十四山课格：{len(shanjia_analyzer.get_all_shan_jia_names())} 个")
    print(f"✓ 总断语数：{sum(len(kege_analyzer.get_ke_ge(k)['duanyu']) for k in kege_analyzer.get_all_ke_ge_names()) + sum(len(shanjia_analyzer.get_shan_jia(s)['duanyu']) for s in shanjia_analyzer.get_all_shan_jia_names())} 条")

if __name__ == '__main__':
    export_all_duanyu()
