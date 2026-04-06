#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬排盘软件 - 简化整合版
整合 SKILL 排盘与龙德课功能
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate
from long_de_ke_selector import LongDeKeSelector
from data.斗首择日规则 import DIZHI


class SimpleDaLiuRenPaipan:
    """简化版大六壬排盘（整合 SKILL 和龙德课）"""
    
    def __init__(self):
        self.calendar = PreciseCalendar()
        self.long_de_selector = LongDeKeSelector()
    
    def get_yue_jiang(self, lunar_month):
        """获取月将（正月亥，二月戌，...）"""
        # 月将 = 12 - 农历月份
        yue_jiang_index = (12 - lunar_month) % 12
        return DIZHI[yue_jiang_index]
    
    def paipan(self, year, month, day, hour, city_name='北京'):
        """
        简化的大六壬排盘
        
        返回：
        - 四柱
        - 月将
        - 占时
        - 课体（简化）
        - 龙德课判断
        """
        # 1. 四柱（真太阳时）- 使用北京经度
        beijing_longitude = 116.4074
        beijing_latitude = 39.9042
        sizhu = get_sizhu_accurate(year, month, day, hour, 0, 
                                   beijing_longitude, beijing_latitude)
        
        # 2. 月将（简化：直接用月份）
        yue_jiang = self.get_yue_jiang(month)
        
        # 3. 占时
        shi_zhi = sizhu['时柱'][1]
        
        # 4. 日干支
        ri_ganzhi = sizhu['日柱']
        
        # 5. 太岁
        tai_sui = self.calendar.get_year_ganzhi(year, month, day)[1]
        
        # 6. 简化的三传（用月将作为初传 - 龙德课判断用）
        sanchuan = {'初传': yue_jiang, '中传': '', '末传': ''}
        
        # 7. 龙德课判断
        is_long_de, long_de_type = self.long_de_selector.is_long_de_ke(
            ri_ganzhi, yue_jiang, tai_sui, sanchuan
        )
        
        # 8. 禄马贵（日干）
        ri_gan = ri_ganzhi[0]
        lu_ma_gui = self.long_de_selector.get_lu_ma_gui_by_gan(ri_gan)
        
        return {
            '四柱': sizhu,
            '月将': yue_jiang,
            '占时': shi_zhi,
            '日干支': ri_ganzhi,
            '太岁': tai_sui,
            '三传': sanchuan,
            '龙德课': {
                '是龙德课': is_long_de,
                '类型': long_de_type if is_long_de else None
            },
            '禄马贵': lu_ma_gui
        }
    
    def display(self, result):
        """显示排盘结果"""
        output = []
        output.append("=" * 70)
        output.append("大六壬排盘（整合 SKILL 与龙德课）")
        output.append("=" * 70)
        
        output.append("\n【四柱】")
        output.append(f"  年：{result['四柱']['年柱']}")
        output.append(f"  月：{result['四柱']['月柱']}")
        output.append(f"  日：{result['四柱']['日柱']}")
        output.append(f"  时：{result['四柱']['时柱']}")
        
        output.append("\n【月将】{result['月将']}  【占时】{result['占时']}")
        output.append(f"【日干支】{result['日干支']}  【太岁】{result['太岁']}")
        
        output.append("\n【三传】")
        output.append(f"  初传：{result['三传']['初传']}")
        output.append(f"  中传：{result['三传']['中传'] or '（空）'}")
        output.append(f"  末传：{result['三传']['末传'] or '（空）'}")
        
        output.append("\n【龙德课】")
        if result['龙德课']['是龙德课']:
            output.append(f"  ✓ {result['龙德课']['类型']}")
            output.append("  大吉之课，主贵人扶持，百事吉利")
        else:
            output.append("  ✗ 非龙德课")
        
        output.append("\n【禄马贵】")
        if '禄' in result['禄马贵']:
            output.append(f"  禄：{result['禄马贵']['禄']}")
        if '贵人' in result['禄马贵']:
            output.append(f"  贵人：{', '.join(result['禄马贵']['贵人'])}")
        
        output.append("\n" + "=" * 70)
        
        return '\n'.join(output)


def main():
    """测试主函数"""
    software = SimpleDaLiuRenPaipan()
    
    print("=" * 70)
    print("大六壬排盘软件 - Skill 与龙德课整合版（简化演示）")
    print("=" * 70)
    
    # 测试排盘
    print("\n【示例排盘】2026 年 9 月 9 日 10 时（北京）")
    result = software.paipan(2026, 9, 9, 10, '北京')
    print(software.display(result))
    
    print("\n按回车键启动 GUI 界面...")
    input()
    
    # 启动 GUI
    print("\n正在启动 GUI 界面...")
    import subprocess
    subprocess.Popen(['python', 'paipan_gui_simple.py'])


if __name__ == '__main__':
    main()
