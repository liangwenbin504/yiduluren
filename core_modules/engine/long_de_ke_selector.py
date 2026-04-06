#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课到山到向择日引擎
集成龙德课判断、贵人禄马到山到向分析、风水择日功能
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

from complete_qi_ke_engine import CompleteQiKeEngine
from ke_ti_judge_pro import KeTiJudgeProfessional
from data.斗首择日规则 import TIANGAN, DIZHI

# 六十甲子工具类
class LiuShiJiaZi:
    """六十甲子工具类"""
    
    @staticmethod
    def get_all_gan_zhi():
        """获取所有干支组合"""
        gan_zhi_list = []
        for i in range(60):
            gan = TIANGAN[i % 10]
            zhi = DIZHI[i % 12]
            gan_zhi_list.append(f'{gan}{zhi}')
        return gan_zhi_list


class LongDeKeSelector:
    """
    龙德课到山到向择日引擎
    
    功能：
    1. 龙德课判断（太岁或月将发用 + 乘贵人）
    2. 贵人禄马到山到向分析
    3. 二十四山支持
    4. 日期范围筛选
    5. 课格结构生成
    6. 理论依据说明
    """
    
    def __init__(self):
        self.engine = CompleteQiKeEngine()
        self.ke_ti_judge = KeTiJudgeProfessional()
        
        # 二十四山信息
        self._init_shan_jia_info()
        
        # 十干禄马贵
        self._init_lu_ma_gui()
    
    def _init_shan_jia_info(self):
        """初始化二十四山家信息"""
        self.shan_jia_info = {
            # 八干四维
            '甲山': {'五行': '火', '禄': '寅', '马': '申', '贵人': ['丑', '未']},
            '乙山': {'五行': '金', '禄': '卯', '马': '巳', '贵人': ['子', '申']},
            '丙山': {'五行': '火', '禄': '巳', '马': '亥', '贵人': ['亥', '酉']},
            '丁山': {'五行': '火', '禄': '午', '马': '亥', '贵人': ['亥', '酉']},
            '庚山': {'五行': '金', '禄': '申', '马': '寅', '贵人': ['丑', '未']},
            '辛山': {'五行': '金', '禄': '酉', '马': '亥', '贵人': ['午', '寅']},
            '壬山': {'五行': '火', '禄': '亥', '马': '巳', '贵人': ['巳', '卯']},
            '癸山': {'五行': '火', '禄': '子', '马': '巳', '贵人': ['巳', '卯']},
            
            # 十二地支山
            '子山': {'五行': '水', '禄': '亥', '马': '寅', '贵人': ['巳', '卯']},
            '丑山': {'五行': '金', '禄': '申', '马': '亥', '贵人': ['午', '寅']},
            '寅山': {'五行': '水', '禄': '子', '马': '申', '贵人': ['丑', '未']},
            '卯山': {'五行': '木', '禄': '寅', '马': '巳', '贵人': ['子', '申']},
            '辰山': {'五行': '水', '禄': '亥', '马': '寅', '贵人': ['巳', '卯']},
            '巳山': {'五行': '水', '禄': '子', '马': '亥', '贵人': ['亥', '酉']},
            '午山': {'五行': '火', '禄': '巳', '马': '申', '贵人': ['亥', '酉']},
            '未山': {'五行': '金', '禄': '申', '马': '巳', '贵人': ['子', '申']},
            '申山': {'五行': '水', '禄': '亥', '马': '寅', '贵人': ['丑', '未']},
            '酉山': {'五行': '金', '禄': '酉', '马': '亥', '贵人': ['午', '寅']},
            '戌山': {'五行': '火', '禄': '巳', '马': '申', '贵人': ['亥', '酉']},
            '亥山': {'五行': '火', '禄': '午', '马': '巳', '贵人': ['亥', '酉']},
            
            # 四维卦山
            '乾山': {'五行': '金', '禄': '申', '马': '寅', '贵人': ['丑', '未']},
            '坤山': {'五行': '土', '禄': '巳', '马': '亥', '贵人': ['子', '申']},
            '艮山': {'五行': '土', '禄': '巳', '马': '亥', '贵人': ['午', '寅']},
            '巽山': {'五行': '木', '禄': '寅', '马': '巳', '贵人': ['子', '申']},
        }
    
    def _init_lu_ma_gui(self):
        """初始化禄马贵映射"""
        # 十干禄
        self.lu_map = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
            '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
        }
        
        # 十干贵人
        self.gui_map = {
            '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
            '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
            '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
            '癸': ['巳', '卯']
        }
        
        # 地支驿马（三合局）
        self.ma_map = {
            '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥'
        }
    
    def get_date_gan_zhi(self, date: datetime) -> str:
        """获取日干支"""
        base_date = datetime(1984, 1, 1)  # 甲子日
        days_offset = (date - base_date).days
        gan_zhi_index = days_offset % 60
        return LiuShiJiaZi.get_all_gan_zhi()[gan_zhi_index]
    
    def get_year_gan_zhi(self, year: int) -> Tuple[str, str]:
        """获取年干支"""
        base_year = 1984  # 甲子年
        offset = (year - base_year) % 60
        gan_index = offset % 10
        zhi_index = offset % 12
        return TIANGAN[gan_index], DIZHI[zhi_index]
    
    def get_month_jiang(self, lunar_month: int) -> str:
        """获取月将（正月亥，二月戌，...）"""
        yue_jiang_index = (12 - lunar_month) % 12
        return DIZHI[yue_jiang_index]
    
    def get_lu_ma_gui_by_gan(self, gan: str) -> Dict:
        """根据天干获取禄马贵"""
        result = {}
        
        # 禄
        if gan in self.lu_map:
            result['禄'] = self.lu_map[gan]
        
        # 贵人
        if gan in self.gui_map:
            result['贵人'] = self.gui_map[gan]
        
        return result
    
    def get_ma_by_zhi(self, zhi: str) -> Optional[str]:
        """根据地支获取驿马"""
        for san_he, ma in self.ma_map.items():
            if zhi in san_he:
                return ma
        return None
    
    def is_long_de_ke(self, ri_gan_zhi: str, yue_jiang: str, tai_sui: str, 
                      sanchuan: dict) -> Tuple[bool, str]:
        """
        判断龙德课
        
        龙德课条件：
        1. 太岁发用：初传 = 年支（太岁）
        2. 月将发用：初传 = 月将
        3. 乘贵人：初传是日干贵人
        
        满足：(太岁发用 OR 月将发用) AND 乘贵人 = 龙德课
        """
        chu_chuan = sanchuan.get('初传', '') if isinstance(sanchuan, dict) else ''
        
        if not chu_chuan:
            return False, "三传为空"
        
        # 条件 1：太岁或月将发用
        is_tai_sui_yong = (chu_chuan == tai_sui)
        is_yue_jiang_yong = (chu_chuan == yue_jiang)
        
        if not (is_tai_sui_yong or is_yue_jiang_yong):
            return False, "太岁和月将均未发用"
        
        # 条件 2：乘贵人
        ri_gan = ri_gan_zhi[0]
        gui_ren_list = self.gui_map.get(ri_gan, [])
        is_gui_ren_yong = (chu_chuan in gui_ren_list)
        
        if not is_gui_ren_yong:
            return False, f"初传{chu_chuan}不是{ri_gan}日贵人"
        
        # 判断龙德课类型
        if is_tai_sui_yong and is_gui_ren_yong:
            return True, "太岁龙德课（权贵之象）"
        elif is_yue_jiang_yong and is_gui_ren_yong:
            return True, "月将龙德课（光明之象）"
        
        return False, "不符合龙德课条件"
    
    def check_lu_ma_gui_arrival(self, mountain: str, direction: str,
                                 year_gan_zhi: Tuple[str, str],
                                 day_gan_zhi: str,
                                 shi_zhi: str) -> Dict:
        """
        检查禄马贵是否到山到向
        
        :param mountain: 坐山（如'壬'）
        :param direction: 朝向（如'丙'）
        :param year_gan_zhi: 年干支 (天干，地支)
        :param day_gan_zhi: 日干支
        :param shi_zhi: 时支
        :return: 禄马贵到山到向分析结果
        """
        result = {
            '山家信息': {},
            '向方信息': {},
            '年柱禄马贵': {},
            '日柱禄马贵': {},
            '时支分析': {},
            '到山到向详情': [],
            '总结': []
        }
        
        # 获取山家和向方的禄马贵
        shan_key = f'{mountain}山'
        xiang_key = f'{direction}向'
        
        if shan_key in self.shan_jia_info:
            result['山家信息'] = self.shan_jia_info[shan_key]
        else:
            # 尝试不带"山"的键
            if mountain in self.shan_jia_info:
                result['山家信息'] = self.shan_jia_info[mountain]
        
        if xiang_key in self.shan_jia_info:
            result['向方信息'] = self.shan_jia_info[xiang_key]
        else:
            if direction in self.shan_jia_info:
                result['向方信息'] = self.shan_jia_info[direction]
        
        # 年柱禄马贵
        year_gan, year_zhi = year_gan_zhi
        year_lu_ma_gui = self.get_lu_ma_gui_by_gan(year_gan)
        year_ma = self.get_ma_by_zhi(year_zhi)
        if year_ma:
            year_lu_ma_gui['马'] = year_ma
        result['年柱禄马贵'] = year_lu_ma_gui
        
        # 日柱禄马贵
        day_gan = day_gan_zhi[0]
        day_zhi = day_gan_zhi[1]
        day_lu_ma_gui = self.get_lu_ma_gui_by_gan(day_gan)
        day_ma = self.get_ma_by_zhi(day_zhi)
        if day_ma:
            day_lu_ma_gui['马'] = day_ma
        result['日柱禄马贵'] = day_lu_ma_gui
        
        # 时支分析
        result['时支分析'] = {'时支': shi_zhi}
        
        # 判断到山到向
        shan_lu = result['山家信息'].get('禄', '')
        shan_ma = result['山家信息'].get('马', '')
        shan_gui = result['山家信息'].get('贵人', [])
        
        xiang_lu = result['向方信息'].get('禄', '')
        xiang_ma = result['向方信息'].get('马', '')
        xiang_gui = result['向方信息'].get('贵人', [])
        
        # 检查年禄马贵
        if '禄' in year_lu_ma_gui:
            if year_lu_ma_gui['禄'] == shan_lu:
                result['到山到向详情'].append('年禄到山')
            if year_lu_ma_gui['禄'] == xiang_lu:
                result['到山到向详情'].append('年禄到向')
        
        if '马' in year_lu_ma_gui:
            if year_lu_ma_gui['马'] == shan_ma:
                result['到山到向详情'].append('年马到山')
            if year_lu_ma_gui['马'] == xiang_ma:
                result['到山到向详情'].append('年马到向')
        
        if '贵人' in year_lu_ma_gui:
            for gui in year_lu_ma_gui['贵人']:
                if gui in shan_gui:
                    result['到山到向详情'].append('年贵到山')
                if gui in xiang_gui:
                    result['到山到向详情'].append('年贵到向')
        
        # 检查日禄马贵
        if '禄' in day_lu_ma_gui:
            if day_lu_ma_gui['禄'] == shan_lu:
                result['到山到向详情'].append('日禄到山')
            if day_lu_ma_gui['禄'] == xiang_lu:
                result['到山到向详情'].append('日禄到向')
        
        if '马' in day_lu_ma_gui:
            if day_lu_ma_gui['马'] == shan_ma:
                result['到山到向详情'].append('日马到山')
            if day_lu_ma_gui['马'] == xiang_ma:
                result['到山到向详情'].append('日马到向')
        
        if '贵人' in day_lu_ma_gui:
            for gui in day_lu_ma_gui['贵人']:
                if gui in shan_gui:
                    result['到山到向详情'].append('日贵到山')
                if gui in xiang_gui:
                    result['到山到向详情'].append('日贵到向')
        
        # 检查时支
        if shi_zhi == shan_lu:
            result['到山到向详情'].append('时禄到山')
        if shi_zhi == xiang_lu:
            result['到山到向详情'].append('时禄到向')
        
        if shi_zhi == shan_ma:
            result['到山到向详情'].append('时马到山')
        if shi_zhi == xiang_ma:
            result['到山到向详情'].append('时马到向')
        
        if shi_zhi in shan_gui:
            result['到山到向详情'].append('时贵到山')
        if shi_zhi in xiang_gui:
            result['到山到向详情'].append('时贵到向')
        
        # 总结
        if result['到山到向详情']:
            result['总结'] = result['到山到向详情']
        else:
            result['总结'] = ['禄马贵未到山到向']
        
        return result
    
    def select_long_de_dates(self, mountain: str, direction: str,
                             start_date: datetime, end_date: datetime,
                             min_arrival_count: int = 3) -> List[Dict]:
        """
        选择龙德课到山到向的日期
        
        :param mountain: 坐山
        :param direction: 朝向
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param min_arrival_count: 最少到山到向数量要求
        :return: 符合条件的日期列表
        """
        qualified_results = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日干支
            ri_gan_zhi = self.get_date_gan_zhi(current_date)
            ri_gan = ri_gan_zhi[0]
            ri_zhi = ri_gan_zhi[1]
            
            # 获取年干支
            year = current_date.year
            year_gan_zhi = self.get_year_gan_zhi(year)
            _, tai_sui = year_gan_zhi
            
            # 获取月将
            lunar_month = ((current_date.month - 1) % 12) + 1
            yue_jiang = self.get_month_jiang(lunar_month)
            
            # 遍历时辰
            for shi in DIZHI:
                try:
                    result = self.engine.qi_ke(
                        ri_gan_zhi=ri_gan_zhi,
                        yue_jiang=yue_jiang,
                        shi_chen=shi,
                        lunar_month=lunar_month,
                        nian_zhi=tai_sui
                    )
                    
                    sanchuan = result.get('三传', {})
                    
                    # 判断龙德课
                    is_long_de, long_de_type = self.is_long_de_ke(
                        ri_gan_zhi, yue_jiang, tai_sui, sanchuan
                    )
                    
                    if not is_long_de:
                        continue
                    
                    # 检查禄马贵到山到向
                    lu_ma_gui_result = self.check_lu_ma_gui_arrival(
                        mountain, direction, year_gan_zhi, ri_gan_zhi, shi
                    )
                    
                    # 筛选：达到最少到山到向数量
                    arrival_count = len(lu_ma_gui_result['到山到向详情'])
                    if arrival_count >= min_arrival_count:
                        ke_ti_list = result.get('课体', [])
                        
                        qualified_results.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'weekday': self._get_weekday(current_date),
                            'ri_gan_zhi': ri_gan_zhi,
                            'shi': shi,
                            'lunar_month': lunar_month,
                            'yue_jiang': yue_jiang,
                            'tai_sui': tai_sui,
                            'year_gan_zhi': f'{year_gan_zhi[0]}{year_gan_zhi[1]}',
                            'year': year,
                            'sanchuan': sanchuan,
                            'ke_ti': ke_ti_list,
                            'long_de_type': long_de_type,
                            'lu_ma_gui_arrival': lu_ma_gui_result,
                            'arrival_count': arrival_count,
                            'notes': f'{long_de_type}，{" + ".join(lu_ma_gui_result["总结"])}'
                        })
                
                except Exception as e:
                    continue
            
            # 进度显示
            if day_count % 50 == 0:
                progress = (day_count / total_days) * 100
                print(f"进度：{day_count}/{total_days}天 ({progress:.1f}%), 符合={len(qualified_results)}")
            
            current_date += timedelta(days=1)
        
        # 按到山到向数量排序
        qualified_results.sort(key=lambda x: x['arrival_count'], reverse=True)
        
        return qualified_results
    
    def _get_weekday(self, date: datetime) -> str:
        """获取星期"""
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        return f'星期{weekdays[date.weekday()]}'
    
    def generate_kege_structure(self, result: Dict) -> Dict:
        """
        生成完整的课格结构
        
        :param result: 择日结果
        :return: 课格结构
        """
        kege_structure = {
            '基本信息': {
                '日期': result['date'],
                '星期': result['weekday'],
                '四柱': {
                    '年柱': result['year_gan_zhi'],
                    '月柱': self._get_month_gan_zhi(result['year'], result['lunar_month']),
                    '日柱': result['ri_gan_zhi'],
                    '时柱': self._get_hour_gan_zhi(result['ri_gan_zhi'], result['shi'])
                },
                '坐山朝向': f"{result.get('mountain', '壬')}山{result.get('direction', '丙')}向"
            },
            '六壬课式': {
                '月将': result['yue_jiang'],
                '占时': result['shi'],
                '三传': result['sanchuan'],
                '课体': result['ke_ti']
            },
            '龙德课分析': {
                '龙德课类型': result['long_de_type'],
                '判断依据': self._get_long_de_theory(result)
            },
            '到山到向分析': result['lu_ma_gui_arrival'],
            '综合评价': {
                '到山到向数量': result['arrival_count'],
                '课格等级': self._evaluate_kege_level(result),
                '推荐指数': self._get_recommendation_level(result)
            }
        }
        
        return kege_structure
    
    def _get_month_gan_zhi(self, year: int, lunar_month: int) -> str:
        """获取月柱干支"""
        year_gan, _ = self.get_year_gan_zhi(year)
        
        # 五虎遁求月干
        if year_gan in ['甲', '己']:
            start_gan = '丙'
        elif year_gan in ['乙', '庚']:
            start_gan = '戊'
        elif year_gan in ['丙', '辛']:
            start_gan = '庚'
        elif year_gan in ['丁', '壬']:
            start_gan = '壬'
        else:
            start_gan = '甲'
        
        start_idx = TIANGAN.index(start_gan)
        month_gan_idx = (start_idx + lunar_month - 1) % 10
        
        month_dizhi = DIZHI[(lunar_month + 2) % 12]
        
        return f'{TIANGAN[month_gan_idx]}{month_dizhi}'
    
    def _get_hour_gan_zhi(self, ri_gan_zhi: str, shi: str) -> str:
        """获取时柱干支"""
        ri_gan = ri_gan_zhi[0]
        
        # 五鼠遁求时干
        if ri_gan in ['甲', '己']:
            start_gan = '甲'
        elif ri_gan in ['乙', '庚']:
            start_gan = '丙'
        elif ri_gan in ['丙', '辛']:
            start_gan = '戊'
        elif ri_gan in ['丁', '壬']:
            start_gan = '庚'
        else:
            start_gan = '壬'
        
        start_idx = TIANGAN.index(start_gan)
        shi_idx = DIZHI.index(shi)
        hour_gan_idx = (start_idx + shi_idx) % 10
        
        return f'{TIANGAN[hour_gan_idx]}{shi}'
    
    def _get_long_de_theory(self, result: Dict) -> str:
        """获取龙德课理论依据"""
        theory = "龙德课者，太岁或月将乘贵人发用也。\n\n"
        theory += f"【课式条件】\n"
        theory += f"1. 太岁发用：初传 = 年支（{result['tai_sui']}）\n"
        theory += f"2. 月将发用：初传 = 月将（{result['yue_jiang']}）\n"
        theory += f"3. 乘贵人：初传为日干（{result['ri_gan_zhi'][0]}）贵人\n\n"
        
        if '太岁' in result['long_de_type']:
            theory += f"【判断】初传为{result['sanchuan'].get('初传', '')}, 与太岁相同，且为日干贵人，故为太岁龙德课。\n"
            theory += "【断语】太岁龙德，主权贵显达，百事亨通。\n"
        else:
            theory += f"【判断】初传为{result['sanchuan'].get('初传', '')}, 与月将相同，且为日干贵人，故为月将龙德课。\n"
            theory += "【断语】月将龙德，主光明磊落，逢凶化吉。\n"
        
        return theory
    
    def _evaluate_kege_level(self, result: Dict) -> str:
        """评估课格等级"""
        arrival_count = result['arrival_count']
        
        if arrival_count >= 6:
            return '上上大吉 ⭐⭐⭐'
        elif arrival_count >= 5:
            return '上吉 ⭐⭐'
        elif arrival_count >= 4:
            return '中吉 ⭐'
        elif arrival_count >= 3:
            return '小吉'
        else:
            return '平'
    
    def _get_recommendation_level(self, result: Dict) -> str:
        """获取推荐指数"""
        arrival_count = result['arrival_count']
        
        if arrival_count >= 6:
            return '★★★★★ 强烈推荐'
        elif arrival_count >= 5:
            return '★★★★☆ 推荐'
        elif arrival_count >= 4:
            return '★★★☆☆ 可用'
        elif arrival_count >= 3:
            return '★★☆☆☆ 一般'
        else:
            return '★☆☆☆☆ 不建议'
    
    def save_results(self, results: List[Dict], output_file: str):
        """保存结果到 JSON 文件"""
        import json
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到：{output_file}")
    
    def generate_report(self, results: List[Dict], report_file: str,
                       mountain: str = '壬', direction: str = '丙'):
        """生成报告文件"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("龙德课到山到向择日报告\n")
            f.write("=" * 80 + "\n\n")
            
            if not results:
                f.write("未找到符合条件的课例\n")
                return
            
            f.write(f"坐山：{mountain}山\n")
            f.write(f"朝向：{direction}向\n")
            f.write(f"筛选范围：{results[0]['date']} 至 {results[-1]['date']}\n")
            f.write(f"总数量：{len(results)}个\n\n")
            
            # 按年份统计
            year_count = {}
            for item in results:
                year = item['year']
                year_count[year] = year_count.get(year, 0) + 1
            
            f.write("年度分布:\n")
            for year in sorted(year_count.keys()):
                f.write(f"  {year}年：{year_count[year]}个\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("详细列表\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(results, 1):
                f.write(f"{i}. {item['date']} ({item['weekday']}) {item['shi']}时\n")
                f.write(f"   四柱：{item['year_gan_zhi']}年 {self._get_month_gan_zhi(item['year'], item['lunar_month'])}月 {item['ri_gan_zhi']}日 {self._get_hour_gan_zhi(item['ri_gan_zhi'], item['shi'])}时\n")
                f.write(f"   三传：{item['sanchuan'].get('初传', '')} {item['sanchuan'].get('中传', '')} {item['sanchuan'].get('末传', '')}\n")
                f.write(f"   课体：{', '.join(item['ke_ti'][:5])}\n")
                f.write(f"   龙德课：{item['long_de_type']}\n")
                f.write(f"   到山到向：{', '.join(item['lu_ma_gui_arrival']['总结'])}\n")
                f.write(f"   推荐指数：{self._get_recommendation_level(item)}\n")
                f.write("\n")
        
        print(f"报告已生成：{report_file}")


# 测试函数
def test_long_de_selector():
    """测试龙德课选择器"""
    selector = LongDeKeSelector()
    
    print("=" * 80)
    print("龙德课到山到向择日引擎测试")
    print("=" * 80)
    
    # 测试龙德课判断
    print("\n【测试 1：龙德课判断】")
    test_cases = [
        {'ri_gan_zhi': '辛酉', 'yue_jiang': '午', 'tai_sui': '午', 'sanchuan': {'初传': '午', '中传': '卯', '末传': '子'}},
        {'ri_gan_zhi': '丙子', 'yue_jiang': '亥', 'tai_sui': '未', 'sanchuan': {'初传': '亥', '中传': '寅', '末传': '巳'}},
    ]
    
    for case in test_cases:
        is_long_de, long_de_type = selector.is_long_de_ke(
            case['ri_gan_zhi'], case['yue_jiang'], case['tai_sui'], case['sanchuan']
        )
        print(f"  日干支={case['ri_gan_zhi']}, 月将={case['yue_jiang']}, 太岁={case['tai_sui']}")
        print(f"  结果：{is_long_de}, 类型：{long_de_type}\n")
    
    # 测试禄马贵到山到向
    print("\n【测试 2：禄马贵到山到向】")
    mountain = '壬'
    direction = '丙'
    year_gan_zhi = ('丙', '午')
    day_gan_zhi = '辛酉'
    shi_zhi = '子'
    
    result = selector.check_lu_ma_gui_arrival(mountain, direction, year_gan_zhi, day_gan_zhi, shi_zhi)
    print(f"  坐山：{mountain}山，朝向：{direction}向")
    print(f"  年柱：{year_gan_zhi[0]}{year_gan_zhi[1]}")
    print(f"  日柱：{day_gan_zhi}")
    print(f"  时支：{shi_zhi}")
    print(f"  到山到向：{', '.join(result['总结'])}\n")
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    test_long_de_selector()
