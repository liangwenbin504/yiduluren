#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
九宗门起课法与 720 课例完整关联系统

功能：
1. 使用九宗门起课法重新计算所有 720 课例
2. 根据实际三传结构匹配 64 课经
3. 实现完整的 64 课经匹配逻辑
4. 保存匹配结果到数据库
"""

import json
import os
import sys
from typing import Dict, List, Tuple

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sike_sanchuan_engine import SiKeSanChuanCalculator


class JiuZongMen720Matcher:
    """九宗门 720 课例匹配器"""
    
    def __init__(self):
        self.calculator = SiKeSanChuanCalculator()
        self.ke_jing_data = self._load_ke_jing_data()
        
        # 60 甲子
        self.liu_shi_jia_zi = [
            '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
            '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
            '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
            '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
            '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
            '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
        ]
        
        # 十二月建
        self.yue_jian = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 十二时辰
        self.shi_chen = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    def _load_ke_jing_data(self) -> Dict:
        """加载 64 课经数据"""
        ke_jing_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', '64_ke_jing_accurate.json')
        if not os.path.exists(ke_jing_file):
            # 尝试另一个文件
            ke_jing_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', '64_ke_jing_full.json')
        
        if os.path.exists(ke_jing_file):
            with open(ke_jing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('课经详情', {})
        return {}
    
    def get_yue_jiang(self, yue_jian: str) -> str:
        """
        根据月建计算月将
        月将 = 太阳过宫，与月建六合
        """
        liu_he = {
            '子': '丑', '丑': '子',
            '寅': '亥', '亥': '寅',
            '卯': '戌', '戌': '卯',
            '辰': '酉', '酉': '辰',
            '巳': '申', '申': '巳',
            '午': '未', '未': '午'
        }
        return liu_he.get(yue_jian, yue_jian)
    
    def calculate_ke_example(self, ri_gan_zhi: str, yue_jian: str, shi_chen: str) -> Dict:
        """
        计算单个课例的九宗门起课结果
        
        :param ri_gan_zhi: 日干支
        :param yue_jian: 月建
        :param shi_chen: 时辰
        :return: 课例信息字典
        """
        # 提取日干、日支
        ri_gan = ri_gan_zhi[0]
        ri_zhi = ri_gan_zhi[1]
        
        # 计算月将
        yue_jiang = self.get_yue_jiang(yue_jian)
        
        # 获取天地盘
        tiandi_pan = self.calculator.get_tiandi_pan(yue_jiang, shi_chen)
        
        # 起四课
        sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
        
        # 发三传（九宗门起法）
        sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
        
        # 提取课体信息
        ke_ti = sanchuan_result.get('课体', '')
        qi_fa = sanchuan_result.get('起法', '')
        
        # 简单的课体列表
        ke_ti_list = []
        if ke_ti:
            ke_ti_list.append(ke_ti)
        if '伏吟' in qi_fa:
            ke_ti_list.append('伏吟课')
        if '反吟' in qi_fa:
            ke_ti_list.append('反吟课')
        
        # 匹配 64 课经
        matched_ke_jing = self._match_64_ke_jing(
            sanchuan_result=sanchuan_result,
            ke_ti_list=ke_ti_list,
            ri_gan=ri_gan,
            ri_zhi=ri_zhi,
            sike=sike
        )
        
        return {
            'ri_gan_zhi': ri_gan_zhi,
            'yue_jian': yue_jian,
            'shi_chen': shi_chen,
            'yue_jiang': yue_jiang,
            'tiandi_pan': tiandi_pan,
            'sike': sike,
            'sanchuan': sanchuan_result,
            'ke_ti_list': ke_ti_list,
            'matched_ke_jing': matched_ke_jing,
            'primary_ke_jing': matched_ke_jing[0] if matched_ke_jing else '',
            'jiu_zong_men_method': sanchuan_result.get('起法', '')
        }
    
    def _match_64_ke_jing(self, sanchuan_result: Dict, ke_ti_list: List[str], 
                          ri_gan: str, ri_zhi: str, sike: List) -> List[str]:
        """
        匹配 64 课经（简化版）
        
        :param sanchuan_result: 三传结果
        :param ke_ti_list: 课体列表
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param sike: 四课
        :return: 匹配的课经列表
        """
        matched = []
        
        # 1. 根据九宗门起法和课体匹配
        qi_fa = sanchuan_result.get('起法', '')
        ke_ti = sanchuan_result.get('课体', '')
        
        # 贼克法
        if '贼克法' in qi_fa:
            if '元首课' in ke_ti:
                matched.append('1_元首课')
            elif '重审课' in ke_ti:
                matched.append('2_重审课')
        
        # 伏吟法
        if '伏吟法' in qi_fa or '伏吟课' in ke_ti_list:
            matched.append('31_伏吟课')
        
        # 反吟法
        if '反吟法' in qi_fa or '反吟课' in ke_ti_list:
            matched.append('39_反吟课')
        
        # 2. 根据三传特征匹配
        san_chuan = sanchuan_result.get('三传', [])
        if len(san_chuan) >= 3:
            # 连珠课：三传相连
            if self._is_lian_zhu(san_chuan):
                matched.append('6_连珠课')
            
            # 全局课：三传合局
            if self._is_quan_ju(san_chuan):
                matched.append('7_全局课')
        
        # 3. 根据四课特征匹配（简化）
        # 无禄课：四课不备
        if self._is_si_ke_bu_bei(sike):
            matched.append('22_无禄课')
        
        return matched
    
    def _is_lian_zhu(self, san_chuan: List[str]) -> bool:
        """判断是否为连珠课（三传相连）"""
        if len(san_chuan) != 3:
            return False
        
        dizhi_order = self.calculator.DIZHI
        try:
            idx1 = dizhi_order.index(san_chuan[0])
            idx2 = dizhi_order.index(san_chuan[1])
            idx3 = dizhi_order.index(san_chuan[2])
            
            # 顺时针相连
            return (idx2 == (idx1 + 1) % 12) and (idx3 == (idx2 + 1) % 12)
        except ValueError:
            return False
    
    def _is_quan_ju(self, san_chuan: List[str]) -> bool:
        """判断是否为全局课（三传合局）"""
        if len(san_chuan) != 3:
            return False
        
        # 三合局
        san_he_ju = [
            {'申', '子', '辰'},  # 水局
            {'亥', '卯', '未'},  # 木局
            {'寅', '午', '戌'},  # 火局
            {'巳', '酉', '丑'}   # 金局
        ]
        
        san_chuan_set = set(san_chuan)
        return any(san_chuan_set == ju for ju in san_he_ju)
    
    def _is_si_ke_bu_bei(self, sike: List) -> bool:
        """判断四课是否不备（无禄课条件）"""
        # 简化判断：如果四课中有上下相同，则为不备
        for _, shang, xia, _ in sike:
            if shang == xia:
                return True
        return False
    
    def batch_process_720_ke_li(self) -> Dict:
        """
        批量处理 720 课例（60 甲子 × 12 月 × 12 时 = 8640 课）
        
        :return: 处理结果统计
        """
        results = {}
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'methods_distribution': {},
            'ke_jing_distribution': {}
        }
        
        print("=" * 80)
        print("开始批量处理 720 课例（实际 8640 课）")
        print("=" * 80)
        
        for ri_gan_zhi in self.liu_shi_jia_zi:
            for yue_jian in self.yue_jian:
                for shi_chen in self.shi_chen:
                    stats['total'] += 1
                    ke_key = f"{ri_gan_zhi}_{yue_jian}_{shi_chen}"
                    
                    try:
                        # 计算课例
                        result = self.calculate_ke_example(ri_gan_zhi, yue_jian, shi_chen)
                        
                        # 保存结果（包含四课三传详细信息）
                        sanchuan_data = result['sanchuan']
                        # 提取三传列表
                        san_chuan_list = [
                            sanchuan_data.get('初传', ''),
                            sanchuan_data.get('中传', ''),
                            sanchuan_data.get('末传', '')
                        ]
                        
                        results[ke_key] = {
                            'ri_gan_zhi': result['ri_gan_zhi'],
                            'yue': result['yue_jian'],
                            'shi': result['shi_chen'],
                            'yue_jiang': result['yue_jiang'],
                            'sike': result['sike'],  # 四课详细信息
                            'sanchuan': {
                                '三传': san_chuan_list,
                                '课体': sanchuan_data.get('课体', ''),
                                '起法': sanchuan_data.get('起法', ''),
                                '初传': sanchuan_data.get('初传', ''),
                                '中传': sanchuan_data.get('中传', ''),
                                '末传': sanchuan_data.get('末传', '')
                            },  # 三传详细信息
                            'matched_ke_jing': [
                                self.ke_jing_data.get(k, {}).get('ke_name', k) 
                                for k in result['matched_ke_jing']
                            ],
                            'primary_ke_jing': self.ke_jing_data.get(
                                result['primary_ke_jing'], {}
                            ).get('ke_name', result['primary_ke_jing']),
                            'jiu_zong_men_method': result['jiu_zong_men_method'],
                            'ke_ti_list': result['ke_ti_list']
                        }
                        
                        stats['success'] += 1
                        
                        # 统计起法分布
                        method = result['jiu_zong_men_method']
                        stats['methods_distribution'][method] = stats['methods_distribution'].get(method, 0) + 1
                        
                        # 统计课经分布
                        for ke_jing in result['matched_ke_jing']:
                            ke_name = self.ke_jing_data.get(ke_jing, {}).get('ke_name', ke_jing)
                            stats['ke_jing_distribution'][ke_name] = stats['ke_jing_distribution'].get(ke_name, 0) + 1
                        
                        # 进度显示
                        if stats['total'] % 100 == 0:
                            print(f"已处理 {stats['total']} 课，成功：{stats['success']}, 失败：{stats['failed']}")
                    
                    except Exception as e:
                        stats['failed'] += 1
                        results[ke_key] = {
                            'error': str(e),
                            'ri_gan_zhi': ri_gan_zhi,
                            'yue': yue_jian,
                            'shi': shi_chen
                        }
                        print(f"处理失败 {ke_key}: {e}")
        
        return results, stats
    
    def save_results(self, results: Dict, stats: Dict, output_file: str = None):
        """保存匹配结果"""
        if output_file is None:
            output_file = os.path.join(
                os.path.dirname(__file__), '..', '..', 'data', '720_ke_li_jiu_zong_men.json'
            )
        
        output_data = {
            'metadata': {
                'total_ke_li': stats['total'],
                'success_count': stats['success'],
                'failed_count': stats['failed'],
                'methods_distribution': stats['methods_distribution'],
                'ke_jing_distribution': stats['ke_jing_distribution'],
                'description': '使用九宗门起课法计算的 720 课例（8640 课）完整匹配结果'
            },
            'ke_li': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到：{output_file}")
        return output_file
    
    def print_statistics(self, stats: Dict):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("统计信息")
        print("=" * 80)
        print(f"总课例数：{stats['total']}")
        print(f"成功：{stats['success']}")
        print(f"失败：{stats['failed']}")
        print(f"成功率：{stats['success']/stats['total']*100:.2f}%")
        
        print("\n九宗门起法分布（前 10）：")
        for method, count in sorted(stats['methods_distribution'].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {method}: {count} 课 ({count/stats['total']*100:.2f}%)")
        
        print("\n课经分布（前 20）：")
        for ke_name, count in sorted(stats['ke_jing_distribution'].items(), 
                                     key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {ke_name}: {count} 课 ({count/stats['total']*100:.2f}%)")


def main():
    """主函数"""
    matcher = JiuZongMen720Matcher()
    
    # 批量处理
    results, stats = matcher.batch_process_720_ke_li()
    
    # 保存结果
    matcher.save_results(results, stats)
    
    # 打印统计
    matcher.print_statistics(stats)
    
    print("\n" + "=" * 80)
    print("九宗门起课法与 720 课例关联完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
