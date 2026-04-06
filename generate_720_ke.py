#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成720课例 - 基于宗门九课规则

功能：
1. 月将加时生成天地盘
2. 起四课
3. 按宗门九课规则发三传
4. 生成720课例
"""

from core_modules.engine.sike_sanchuan_engine import SiKeSanChuanCalculator
import json
from datetime import datetime

class SeventyTwoKeGenerator:
    """720课例生成器"""
    
    # 天干
    TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支
    DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 月建与月将对应关系
    YUE_JIAN_TO_YUE_JIANG = {
        '寅': '亥', '卯': '戌', '辰': '酉', '巳': '申',
        '午': '未', '未': '午', '申': '巳', '酉': '辰',
        '戌': '卯', '亥': '寅', '子': '丑', '丑': '子'
    }
    
    def __init__(self):
        self.calculator = SiKeSanChuanCalculator()
        self.ke_li = []
    
    def generate_ke_li(self):
        """生成720课例"""
        print("开始生成720课例...")
        print("=" * 60)
        
        count = 0
        
        # 遍历所有日干
        for ri_gan in self.TIAN_GAN:
            # 遍历所有日支
            for ri_zhi in self.DI_ZHI:
                # 遍历所有月建（12个）
                for yue_jian in self.DI_ZHI:
                    yue_jiang = self.YUE_JIAN_TO_YUE_JIANG[yue_jian]
                    # 遍历所有时辰（12个）
                    for shi_chen in self.DI_ZHI:
                        try:
                            # 1. 计算天地盘
                            tiandi_pan = self.calculator.get_tiandi_pan(yue_jiang, shi_chen)
                            
                            # 2. 起四课
                            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
                            
                            # 3. 发三传（按宗门九课规则）
                            sanchuan = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
                            
                            # 4. 构建课例
                            ke = {
                                'id': count + 1,
                                'ri_gan': ri_gan,
                                'ri_zhi': ri_zhi,
                                'yue_jian': yue_jian,
                                'yue_jiang': yue_jiang,
                                'shi_chen': shi_chen,
                                'tiandi_pan': tiandi_pan,
                                'si_ke': sike,
                                'san_chuan': sanchuan,
                                'ke_ti': sanchuan.get('课体', '未知'),
                                'qi_fa': sanchuan.get('起法', '未知'),
                                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            self.ke_li.append(ke)
                            count += 1
                            
                            # 每100个课例输出一次进度
                            if count % 100 == 0:
                                print(f"已生成 {count} 个课例...")
                                
                        except Exception as e:
                            print(f"生成课例失败: {ri_gan}{ri_zhi}, 月建{yue_jian}, 时辰{shi_chen}, 错误: {e}")
                            continue
        
        print("=" * 60)
        print(f"生成完成！共生成 {len(self.ke_li)} 个课例")
        
    def save_ke_li(self, filename='720_ke_li.json'):
        """保存课例到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.ke_li, f, ensure_ascii=False, indent=2)
        print(f"课例已保存到 {filename}")
    
    def analyze_ke_li(self):
        """分析课例统计信息"""
        print("\n课例分析：")
        print("=" * 60)
        
        # 统计课体分布
        ke_ti_count = {}
        for ke in self.ke_li:
            ke_ti = ke.get('ke_ti', '未知')
            ke_ti_count[ke_ti] = ke_ti_count.get(ke_ti, 0) + 1
        
        print("课体分布：")
        for ke_ti, count in ke_ti_count.items():
            print(f"  {ke_ti}: {count} 个")
        
        # 统计起法分布
        qi_fa_count = {}
        for ke in self.ke_li:
            qi_fa = ke.get('qi_fa', '未知')
            qi_fa_count[qi_fa] = qi_fa_count.get(qi_fa, 0) + 1
        
        print("\n起法分布：")
        for qi_fa, count in qi_fa_count.items():
            print(f"  {qi_fa}: {count} 个")
        
        print("=" * 60)

if __name__ == '__main__':
    generator = SeventyTwoKeGenerator()
    generator.generate_ke_li()
    generator.save_ke_li()
    generator.analyze_ke_li()
