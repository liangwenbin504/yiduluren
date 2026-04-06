#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出斗首择日第一斗首课格断语
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
from douhou_kege_system import DiYiDouShouKeGe

def export_duanyu():
    """导出所有课格断语"""
    analyzer = DiYiDouShouKeGe()
    
    output_path = "斗首择日第一斗首课格断语.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("斗首择日 - 第一斗首课格断语全集\n")
        f.write("依据《斗首择日秘本》整理\n")
        f.write("=" * 70 + "\n\n")
        
        for kege_name in analyzer.get_all_ke_ge_names():
            report = analyzer.analyze_ke_ge(kege_name)
            f.write(report + "\n\n")
    
    print(f"✓ 已导出到：{output_path}")
    print(f"✓ 共导出 {len(analyzer.get_all_ke_ge_names())} 个课格")
    
    # 显示预览
    print("\n" + "=" * 70)
    print("预览：元辰课断语")
    print("=" * 70)
    print(analyzer.analyze_ke_ge('元辰课'))

if __name__ == '__main__':
    export_duanyu()
