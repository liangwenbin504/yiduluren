#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬排盘软件 - 整合 Skill 与龙德课功能

功能整合：
1. 大六壬排盘引用 SKILL 功能
2. 集成龙德课功能
3. 数据交互与逻辑衔接
4. 完整的排盘 + 择日体系
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

# 导入排盘引擎
try:
    from complete_qi_ke_engine import CompleteQiKeEngine
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    from ke_ti_judge import KeTiJudgeCalculator
    from gui_ren_engine import GuiRenEngine
    from shen_sha_calculator import ShenShaCalculator
    from precise_calendar import PreciseCalendar, get_sizhu_accurate
except ImportError:
    # 如果在 src 目录下找不到，尝试直接导入
    from src.engine.complete_qi_ke_engine import CompleteQiKeEngine
    from src.engine.sike_sanchuan_engine import SiKeSanChuanCalculator
    from src.engine.ke_ti_judge import KeTiJudgeCalculator
    from src.engine.gui_ren_engine import GuiRenEngine
    from src.engine.shen_sha_calculator import ShenShaCalculator
    from src.engine.precise_calendar import PreciseCalendar, get_sizhu_accurate

# 导入龙德课引擎
try:
    from long_de_ke_selector import LongDeKeSelector
except ImportError:
    from src.engine.long_de_ke_selector import LongDeKeSelector


class DaLiuRenPaipanSoftware:
    """
    大六壬排盘软件
    
    整合功能：
    1. SKILL 排盘功能（九宗门起课）
    2. 龙德课判断功能
    3. 禄马贵到山到向分析
    4. 综合评分系统
    """
    
    def __init__(self):
        # 排盘引擎
        self.qi_ke_engine = CompleteQiKeEngine()
        self.sike_engine = SiKeSanChuanCalculator()
        self.ke_ti_judge = KeTiJudgeCalculator()
        self.gui_ren_engine = GuiRenEngine()
        self.shen_sha_calc = ShenShaCalculator()
        self.calendar = PreciseCalendar()
        
        # 龙德课引擎
        self.long_de_selector = LongDeKeSelector()
        
        # 二十四山
        self.SHAN_24 = [
            '壬', '子', '癸', '丑', '艮', '寅',
            '甲', '卯', '乙', '辰', '巽', '巳',
            '丙', '午', '丁', '未', '坤', '申',
            '庚', '酉', '辛', '戌', '乾', '亥'
        ]
    
    def full_paipan(self, year: int, month: int, day: int, hour: int, 
                     city_name: str = '北京') -> Dict:
        """
        完整大六壬排盘
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :param city_name: 城市名称（用于真太阳时）
        :return: 完整排盘结果
        """
        # 1. 计算四柱（使用真太阳时）
        sizhu = get_sizhu_accurate(year, month, day, hour, city_name=city_name)
        
        # 2. 起四课三传（使用 SKILL 九宗门法则）
        ri_ganzhi = sizhu['日柱']
        ri_gan = ri_ganzhi[0]
        ri_zhi = ri_ganzhi[1]
        
        # 获取月将
        yue_jiang = self.calendar.get_month_jiang(year, month, day)
        
        # 获取占时
        shi_zhi = sizhu['时柱'][1]
        
        # 起四课
        si_ke = self.sike_engine.get_si_ke(ri_ganzhi, yue_jiang)
        
        # 发三传（九宗门法则）
        san_chuan = self.sike_engine.fa_chuan(si_ke, ri_gan, yue_jiang, shi_zhi)
        
        # 3. 排天地盘
        tiandi_pan = self.qi_ke_engine.arrange_tiandi_pan(yue_jiang, shi_zhi)
        
        # 4. 排天将
        tian_jiang = self.gui_ren_engine.calculate_tian_jiang(
            ri_gan, ri_zhi, shi_zhi, yue_jiang
        )
        
        # 5. 神煞计算
        shen_sha = self.shen_sha_calc.calculate_all_shen_sha(
            ri_ganzhi, year, month, day, hour
        )
        
        # 6. 课体判断
        ke_ti = self.ke_ti_judge.judge_all_ke_ti(
            si_ke, san_chuan, tiandi_pan, ri_gan, ri_zhi,
            yue_jiang, shi_zhi
        )
        
        # 7. 龙德课判断
        tai_sui = self.calendar.get_year_ganzhi(year, month, day)[1]
        is_long_de, long_de_type = self.long_de_selector.is_long_de_ke(
            ri_ganzhi, yue_jiang, tai_sui, san_chuan
        )
        
        # 8. 综合结果
        result = {
            '基本信息': {
                '公历': f'{year}年{month}月{day}日 {hour}时',
                '四柱': sizhu,
                '月将': yue_jiang,
                '占时': shi_zhi,
                '旬空': self._get_xun_kong(ri_ganzhi)
            },
            '四课': si_ke,
            '三传': san_chuan,
            '天地盘': tiandi_pan,
            '天将': tian_jiang,
            '神煞': shen_sha,
            '课体判断': ke_ti,
            '龙德课': {
                '是龙德课': is_long_de,
                '类型': long_de_type if is_long_de else None
            },
            '断语': self._generate_duanyu(
                ke_ti, is_long_de, long_de_type, shen_sha
            )
        }
        
        return result
    
    def paipan_with_lu_ma_gui(self, year: int, month: int, day: int, hour: int,
                               shan: str, city_name: str = '北京') -> Dict:
        """
        排盘 + 禄马贵到山到向分析
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :param shan: 山向
        :param city_name: 城市名称
        :return: 排盘 + 禄马贵分析结果
        """
        # 1. 完整排盘
        paipan_result = self.full_paipan(year, month, day, hour, city_name)
        
        # 2. 禄马贵到山到向分析
        ri_ganzhi = paipan_result['基本信息']['四柱']['日柱']
        shi_ganzhi = paipan_result['基本信息']['四柱']['时柱']
        
        lu_ma_gui_result = self.long_de_selector.check_lu_ma_gui_dao_shan_xiang(
            ri_ganzhi, shi_ganzhi, shan
        )
        
        # 3. 综合评分
        total_score = self._calculate_total_score(
            paipan_result, lu_ma_gui_result
        )
        
        # 4. 合并结果
        result = {
            '排盘结果': paipan_result,
            '禄马贵分析': lu_ma_gui_result,
            '综合评分': total_score,
            '推荐指数': self._get_recommendation(total_score)
        }
        
        return result
    
    def select_best_dates(self, shan: str, start_date: datetime, 
                          end_date: datetime, min_score: float = 7.0,
                          only_long_de: bool = True) -> List[Dict]:
        """
        选择最佳日期（整合排盘和龙德课）
        
        :param shan: 山向
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param min_score: 最低评分
        :param only_long_de: 是否仅龙德课
        :return: 最佳日期列表
        """
        best_dates = []
        current_date = start_date
        day_count = 0
        total_days = (end_date - start_date).days + 1
        
        while current_date <= end_date:
            day_count += 1
            print(f"进度：{day_count}/{total_days} ({day_count/total_days*100:.1f}%), 符合={len(best_dates)}", end='\r')
            
            year = current_date.year
            month = current_date.month
            day = current_date.day
            
            # 遍历 12 个时辰
            for shi_hour in range(0, 24, 2):
                try:
                    # 排盘 + 禄马贵分析
                    result = self.paipan_with_lu_ma_gui(
                        year, month, day, shi_hour, shan
                    )
                    
                    # 检查是否龙德课
                    is_long_de = result['排盘结果']['龙德课']['是龙德课']
                    if only_long_de and not is_long_de:
                        continue
                    
                    # 检查评分
                    score = result['综合评分']
                    if score < min_score:
                        continue
                    
                    # 添加到结果
                    best_dates.append({
                        '日期': current_date.strftime('%Y-%m-%d'),
                        '时辰': f'{shi_hour:02d}:00',
                        '四柱': result['排盘结果']['基本信息']['四柱'],
                        '课体': result['排盘结果']['课体判断'].get('课体', '未知'),
                        '龙德课': result['排盘结果']['龙德课']['类型'],
                        '禄马贵': result['禄马贵分析'],
                        '评分': score,
                        '推荐': result['推荐指数']
                    })
                    
                except Exception as e:
                    continue
            
            current_date = current_date + timedelta(days=1)
        
        # 按评分排序
        best_dates.sort(key=lambda x: x['评分'], reverse=True)
        
        return best_dates
    
    def _get_xun_kong(self, ri_ganzhi: str) -> str:
        """获取旬空"""
        from data.斗首择日规则 import TIANGAN, DIZHI
        
        # 计算旬首
        gan_index = TIANGAN.index(ri_ganzhi[0])
        zhi_index = DIZHI.index(ri_ganzhi[1])
        offset = (zhi_index - gan_index) % 12
        
        # 旬空
        xun_kong_zhi = DIZHI[(zhi_index + 6) % 12]
        return xun_kong_zhi
    
    def _generate_duanyu(self, ke_ti: Dict, is_long_de: bool, 
                         long_de_type: Optional[str], shen_sha: Dict) -> str:
        """生成断语"""
        duanyu_list = []
        
        # 课体断语
        if ke_ti and '课体' in ke_ti:
            ke_ti_name = ke_ti['课体']
            duanyu_list.append(f"【课体】{ke_ti_name}")
        
        # 龙德课断语
        if is_long_de:
            duanyu_list.append(f"【龙德课】{long_de_type} - 大吉之课，主贵人扶持，百事吉利")
        
        # 吉神断语
        if '吉神' in shen_sha and shen_sha['吉神']:
            ji_shen = ', '.join(shen_sha['吉神'][:3])
            duanyu_list.append(f"【吉神】{ji_shen}")
        
        # 凶煞断语
        if '凶煞' in shen_sha and shen_sha['凶煞']:
            xiong_sha = ', '.join(shen_sha['凶煞'][:3])
            duanyu_list.append(f"【凶煞】{xiong_sha} - 宜化解")
        
        return '\n'.join(duanyu_list) if duanyu_list else "平课"
    
    def _calculate_total_score(self, paipan_result: Dict, 
                                lu_ma_gui_result: Dict) -> float:
        """计算综合评分"""
        score = 0.0
        
        # 1. 课体评分（40%）
        ke_ti = paipan_result.get('课体判断', {})
        ke_ti_name = ke_ti.get('课体', '')
        
        if '龙德' in ke_ti_name or '三光' in ke_ti_name or '富贵' in ke_ti_name:
            score += 9.0 * 0.4
        elif '天福' in ke_ti_name or '玉堂' in ke_ti_name:
            score += 8.0 * 0.4
        elif '官爵' in ke_ti_name or '时泰' in ke_ti_name:
            score += 7.0 * 0.4
        else:
            score += 5.0 * 0.4
        
        # 2. 龙德课评分（30%）
        if paipan_result['龙德课']['是龙德课']:
            score += 9.0 * 0.3
        else:
            score += 5.0 * 0.3
        
        # 3. 禄马贵评分（30%）
        lu_ma_gui_count = lu_ma_gui_result.get('总数', 0)
        score += min(lu_ma_gui_count, 10) * 0.3
        
        return score
    
    def _get_recommendation(self, score: float) -> str:
        """获取推荐指数"""
        if score >= 9.0:
            return '★★★★★ 上上大吉'
        elif score >= 8.0:
            return '★★★★☆ 上吉'
        elif score >= 7.0:
            return '★★★☆☆ 中吉'
        elif score >= 6.0:
            return '★★☆☆☆ 小吉'
        else:
            return '★☆☆☆☆ 平'
    
    def display_paipan(self, result: Dict) -> str:
        """格式化显示排盘结果"""
        output = []
        output.append("=" * 80)
        output.append("大六壬完整排盘")
        output.append("=" * 80)
        
        # 基本信息
        output.append("\n【基本信息】")
        for key, value in result['基本信息'].items():
            if isinstance(value, dict):
                output.append(f"  {key}:")
                for k, v in value.items():
                    output.append(f"    {k}: {v}")
            else:
                output.append(f"  {key}: {value}")
        
        # 四课
        output.append("\n【四课】")
        for i, ke in enumerate(result['四课'], 1):
            output.append(f"  第{i}课：{ke.get('天干', '')} {ke.get('地支', '')}")
        
        # 三传
        output.append("\n【三传】")
        for chuan_name, chuan_value in result['三传'].items():
            if chuan_value:
                output.append(f"  {chuan_name}: {chuan_value}")
        
        # 课体判断
        output.append("\n【课体判断】")
        output.append(f"  课体：{result['课体判断'].get('课体', '未知')}")
        
        # 龙德课
        output.append("\n【龙德课】")
        if result['龙德课']['是龙德课']:
            output.append(f"  ✓ {result['龙德课']['类型']}")
        else:
            output.append("  ✗ 非龙德课")
        
        # 禄马贵
        if '禄马贵分析' in result:
            output.append("\n【禄马贵到山到向】")
            output.append(f"  总数：{result['禄马贵分析'].get('总数', 0)}个")
            for item in result['禄马贵分析'].get('到山到向详情', []):
                output.append(f"  ✓ {item}")
        
        # 综合评分
        if '综合评分' in result:
            output.append("\n【综合评分】")
            output.append(f"  评分：{result['综合评分']:.1f}分")
            output.append(f"  推荐：{result['推荐指数']}")
        
        # 断语
        output.append("\n【断语】")
        output.append(result['断语'])
        
        output.append("\n" + "=" * 80)
        
        return '\n'.join(output)


def main():
    """测试主函数"""
    from datetime import datetime
    
    software = DaLiuRenPaipanSoftware()
    
    print("=" * 80)
    print("大六壬排盘软件 - Skill 与龙德课整合版")
    print("=" * 80)
    
    # 测试 1：完整排盘
    print("\n【测试 1】完整排盘（2026 年 9 月 9 日 10 时）")
    result = software.full_paipan(2026, 9, 9, 10, city_name='北京')
    print(software.display_paipan(result))
    
    # 测试 2：排盘 + 禄马贵分析
    print("\n【测试 2】排盘 + 禄马贵到山到向（壬山）")
    result2 = software.paipan_with_lu_ma_gui(2026, 9, 9, 10, '壬', '北京')
    print(software.display_paipan(result2))
    
    # 测试 3：选择最佳日期
    print("\n【测试 3】选择壬山最佳日期（2026 年 9 月）")
    start = datetime(2026, 9, 1)
    end = datetime(2026, 9, 30)
    best_dates = software.select_best_dates('壬', start, end, min_score=6.0)
    
    print(f"\n找到 {len(best_dates)} 个符合条件的日期：\n")
    for i, item in enumerate(best_dates[:5], 1):
        print(f"{i}. {item['日期']} {item['时辰']}")
        print(f"   四柱：{item['四柱']['年柱']} {item['四柱']['月柱']} {item['四柱']['日柱']} {item['四柱']['时柱']}")
        print(f"   课体：{item['课体']}, 龙德课：{item['龙德课']}")
        print(f"   评分：{item['评分']:.1f}分，推荐：{item['推荐']}")
        print()


if __name__ == '__main__':
    main()
