#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬完整起课引擎系统
集成：四课、三传、天将、神煞、课体判断
实现 64 课经完整匹配
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sike_sanchuan_engine import SiKeSanChuanCalculator
from gui_ren_engine import GuiRenCalculator
from daliuren_engine_pro import DaLiuRenEnginePro
from shen_sha_calculator import ShenShaCalculator
from ke_ti_judge import KeTiJudgeCalculator


class CompleteQiKeEngine:
    """完整起课引擎"""
    
    def __init__(self):
        self.sike_calculator = SiKeSanChuanCalculator()
        self.gui_ren_calculator = GuiRenCalculator()
        self.daliuren_engine = DaLiuRenEnginePro()
        self.shen_sha_calculator = ShenShaCalculator()
        self.ke_ti_judge = KeTiJudgeCalculator()
    
    def qi_ke(self, ri_gan_zhi: str, yue_jiang: str, shi_chen: str,
              lunar_month: int = 1, nian_zhi: str = '子') -> Dict:
        """
        完整起课
        
        :param ri_gan_zhi: 日干支 (如'甲子')
        :param yue_jiang: 月将
        :param shi_chen: 时辰
        :param lunar_month: 农历月份 (用于神煞)
        :param nian_zhi: 年支 (用于神煞)
        :return: 完整课式信息
        """
        ri_gan = ri_gan_zhi[0]
        ri_zhi = ri_gan_zhi[1]
        
        # 1. 排天地盘
        tiandi_pan = self.daliuren_engine.arrange_tiandi_pan(yue_jiang, shi_chen)
        
        # 2. 起四课
        sike_dict = self.daliuren_engine.arrange_si_ke(ri_gan, ri_zhi, tiandi_pan)
        
        # 格式转换：dict -> tuple (兼容 sike_sanchuan_engine)
        # sike_sanchuan_engine 期望格式：[(name, shang, xia, _), ...]
        sike_tuple = []
        for ke in sike_dict:
            sike_tuple.append((ke['name'], ke['top'], ke['bottom'], ''))
        
        # 3. 发三传
        sanchuan_result = self.sike_calculator.fa_sanchuan(
            sike_tuple, ri_gan, ri_zhi, tiandi_pan['天地对应']
        )
        
        # 4. 排天将
        is_night = self.gui_ren_calculator.is_night_time(shi_chen)
        gui_ren_pan = self.gui_ren_calculator.arrange_gui_ren_pan(
            ri_gan, tiandi_pan, shi_chen, is_night
        )
        
        # 5. 计算神煞
        shen_sha = self.shen_sha_calculator.calculate_all_shen_sha(
            ri_gan, ri_zhi, lunar_month, nian_zhi
        )
        
        # 6. 判断课体（使用 dict 格式，方便课体判断模块处理）
        ke_ti_list = self.ke_ti_judge.judge_all_ke_ti(
            sike_dict, sanchuan_result, tiandi_pan['天地对应'], ri_gan, ri_zhi
        )
        
        # 组装结果
        result = {
            '基本信息': {
                '日干支': ri_gan_zhi,
                '月将': yue_jiang,
                '占时': shi_chen,
                '农历月': lunar_month,
                '年支': nian_zhi
            },
            '天地盘': tiandi_pan,
            '四课': sike_dict,
            '三传': sanchuan_result,
            '天将': gui_ren_pan,
            '神煞': shen_sha,
            '课体': ke_ti_list,
            '课体数量': len(ke_ti_list)
        }
        
        return result
    
    def print_result(self, result: Dict):
        """打印结果"""
        print("=" * 70)
        print("大六壬完整课式")
        print("=" * 70)
        
        # 基本信息
        basic = result['基本信息']
        print(f"\n【基本信息】")
        print(f"  日干支：{basic['日干支']}")
        print(f"  月将：{basic['月将']}")
        print(f"  占时：{basic['占时']}")
        
        # 天地盘
        print(f"\n【天地盘】")
        print(f"  天盘：{result['天地盘']['天盘']}")
        print(f"  地盘：{result['天地盘']['地盘']}")
        
        # 四课
        print(f"\n【四课】")
        for i, ke in enumerate(result['四课'], 1):
            print(f"  第{i}课：{ke['top']} (上) / {ke['bottom']} (下)")
        
        # 三传
        print(f"\n【三传】")
        sanchuan = result['三传']
        print(f"  初传：{sanchuan.get('初传', '')}")
        print(f"  中传：{sanchuan.get('中传', '')}")
        print(f"  末传：{sanchuan.get('末传', '')}")
        print(f"  课体：{sanchuan.get('课体', '')}")
        print(f"  起法：{sanchuan.get('起法', '')}")
        
        # 天将
        print(f"\n【天将】")
        print(f"  贵人：{result['天将']['贵人']}")
        print(f"  顺逆：{result['天将']['顺逆']}")
        print(f"  昼夜：{result['天将']['昼夜']}")
        
        # 神煞
        print(f"\n【神煞】")
        shen_sha = result['神煞']
        for name, value in shen_sha.items():
            if value:
                print(f"  {name:8s}: {value}")
        
        # 课体
        print(f"\n【课体判断】")
        ke_ti = result['课体']
        if ke_ti:
            for kt in ke_ti:
                print(f"  ✓ {kt}")
        else:
            print(f"  (无特殊课体)")
        
        print("=" * 70)


def test_complete_engine():
    """测试完整引擎"""
    engine = CompleteQiKeEngine()
    
    # 测试案例 1：甲子日亥将午时
    print("\n测试案例 1: 甲子日亥将午时")
    result = engine.qi_ke('甲子', '亥', '午', lunar_month=1)
    engine.print_result(result)
    
    # 测试案例 2: 伏吟课
    print("\n\n测试案例 2: 戊辰日子将子时 (伏吟)")
    result = engine.qi_ke('戊辰', '子', '子', lunar_month=12)
    engine.print_result(result)
    
    # 测试案例 3: 反吟课
    print("\n\n测试案例 3: 丙寅日戌将辰时 (反吟)")
    result = engine.qi_ke('丙寅', '戌', '辰', lunar_month=9)
    engine.print_result(result)


if __name__ == '__main__':
    test_complete_engine()
