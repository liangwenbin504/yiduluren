"""
智能择日引擎 - 准确版
使用高氏日柱公式和准确的节气计算
"""

from datetime import datetime
from core_modules.data.斗首择日规则 import TIANGAN, DIZHI, LU, YIMA, GUIREN
from engine.douhou_engine import DouShouCalculator
from engine.lunar_converter import solar_to_lunar as convert_to_lunar
import math


class SmartDateSelector:
    """智能择日选择器（准确版）"""
    
    def __init__(self):
        self.calc = DouShouCalculator()
        
        # 天干地支序号
        self.tiangan_num = {tg: i for i, tg in enumerate(TIANGAN)}
        self.dizhi_num = {dz: i for i, dz in enumerate(DIZHI)}
        
        # 60 甲子表
        self.liushijiazi = []
        for i in range(60):
            self.liushijiazi.append((TIANGAN[i % 10], DIZHI[i % 12]))
    
    def get_year_ganzhi(self, year: int) -> tuple:
        """
        获取年干支（以立春为界）
        1984 年为甲子年
        """
        base_year = 1984
        offset = (year - base_year) % 60
        return self.liushijiazi[offset]
    
    def get_month_ganzhi(self, year: int, month: int, day: int) -> tuple:
        """
        获取月干支（以节气为界，准确版）
        使用 sizhu_engine 精确计算
        """
        # 导入 sizhu_engine 的函数
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from sizhu_engine import get_month_ganzhi as sizhu_get_month_ganzhi
        
        return sizhu_get_month_ganzhi(year, month, day)
    
    def _gaoshi_day_ganzhi(self, year: int, month: int, day: int) -> tuple:
        """
        高氏日柱公式（准确版）
        基于公历日期计算日干支
        """
        # 基准日：2000 年 1 月 1 日是戊午日
        base_date = datetime(2000, 1, 1)
        base_ganzhi_index = 54  # 戊午在 60 甲子中的序号
        
        target_date = datetime(year, month, day)
        delta_days = (target_date - base_date).days
        
        # 60 甲子循环
        ganzhi_index = (base_ganzhi_index + delta_days) % 60
        
        return self.liushijiazi[ganzhi_index]
    
    def get_day_ganzhi(self, year: int, month: int, day: int) -> tuple:
        """
        获取日干支
        使用高氏日柱公式
        """
        return self._gaoshi_day_ganzhi(year, month, day)
    
    def get_hour_ganzhi(self, day_tiangan: str, shichen: str) -> tuple:
        """
        获取时干支（五鼠遁）
        """
        if day_tiangan in ['甲', '己']:
            start_tiangan = '甲'
        elif day_tiangan in ['乙', '庚']:
            start_tiangan = '丙'
        elif day_tiangan in ['丙', '辛']:
            start_tiangan = '戊'
        elif day_tiangan in ['丁', '壬']:
            start_tiangan = '庚'
        else:
            start_tiangan = '壬'
        
        shichen_idx = self.dizhi_num[shichen]
        start_idx = self.tiangan_num[start_tiangan]
        hour_tiangan_idx = (start_idx + shichen_idx) % 10
        
        return TIANGAN[hour_tiangan_idx], shichen
    
    def get_shichen_from_hour(self, hour: int) -> str:
        """根据小时数获取时辰地支"""
        if hour >= 23 or hour < 1:
            return '子'
        elif hour < 3:
            return '丑'
        elif hour < 5:
            return '寅'
        elif hour < 7:
            return '卯'
        elif hour < 9:
            return '辰'
        elif hour < 11:
            return '巳'
        elif hour < 13:
            return '午'
        elif hour < 15:
            return '未'
        elif hour < 17:
            return '申'
        elif hour < 19:
            return '酉'
        elif hour < 21:
            return '戌'
        else:
            return '亥'
    
    def solar_to_lunar(self, year: int, month: int, day: int) -> str:
        """
        公历转农历（使用数据表）
        """
        return convert_to_lunar(year, month, day)
    
    def calculate_date_score(self, mountain: str, year: int, month: int, day: int, hour: int = 12) -> dict:
        """
        计算某个日期的分数（使用准确历法）
        """
        # 获取准确的四柱（使用 sizhu_engine）
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from sizhu_engine import get_sizhu
        
        sizhu = get_sizhu(year, month, day, '午')
        year_tiangan, year_dizhi = sizhu['年柱'][0], sizhu['年柱'][1]
        month_tiangan, month_dizhi = sizhu['月柱'][0], sizhu['月柱'][1]
        day_tiangan, day_dizhi = sizhu['日柱'][0], sizhu['日柱'][1]
        shichen = self.get_shichen_from_hour(hour)
        hour_tiangan, hour_dizhi = self.get_hour_ganzhi(day_tiangan, shichen)
        
        # 分析日课
        analysis = self.calc.analyze_douhou_day(
            mountain, year_tiangan, month_tiangan, day_tiangan, hour_tiangan
        )
        
        # 计算禄马贵到山到向
        lu_ma_gui_analysis = self._analyze_lu_ma_gui(
            mountain, year_tiangan, month_tiangan, day_tiangan,
            year_dizhi, month_dizhi, day_dizhi
        )
        
        # 综合评分
        score = self._calculate_score(analysis, lu_ma_gui_analysis)
        
        # 获取农历日期（简化）
        lunar_str = self.solar_to_lunar(year, month, day)
        
        return {
            '公历日期': f"{year}年{month}月{day}日",
            '农历日期': lunar_str,
            '四柱': {
                '年柱': f"{year_tiangan}{year_dizhi}",
                '月柱': f"{month_tiangan}{month_dizhi}",
                '日柱': f"{day_tiangan}{day_dizhi}",
                '时柱': f"{hour_tiangan}{shichen}"
            },
            '斗首分析': analysis,
            '禄马贵分析': lu_ma_gui_analysis,
            '综合评分': score,
            '吉凶等级': self._get_auspicious_level(score)
        }
    
    def _analyze_lu_ma_gui(self, mountain: str, year_tiangan: str, month_tiangan: str, 
                          day_tiangan: str, year_dizhi: str, month_dizhi: str, day_dizhi: str) -> dict:
        """分析禄马贵到山到向"""
        result = {
            '山家禄马贵': {},
            '年柱禄马贵': {},
            '月柱禄马贵': {},
            '日柱禄马贵': {},
            '总结': []
        }
        
        shanjia_wuxing = self.calc.get_shanjia_wuxing(mountain)
        
        result['山家禄马贵'] = {
            '禄': self._get_shanjia_lu(shanjia_wuxing),
            '马': self._get_shanjia_ma(shanjia_wuxing),
            '贵': self._get_shanjia_gui(shanjia_wuxing)
        }
        
        if year_tiangan in LU:
            result['年柱禄马贵']['禄'] = LU[year_tiangan]
        for key, value in YIMA.items():
            if year_dizhi in key:
                result['年柱禄马贵']['马'] = value
                break
        if year_tiangan in GUIREN:
            result['年柱禄马贵']['贵'] = GUIREN[year_tiangan]
        
        if month_tiangan in LU:
            result['月柱禄马贵']['禄'] = LU[month_tiangan]
        
        if day_tiangan in LU:
            result['日柱禄马贵']['禄'] = LU[day_tiangan]
        for key, value in YIMA.items():
            if day_dizhi in key:
                result['日柱禄马贵']['马'] = value
                break
        if day_tiangan in GUIREN:
            result['日柱禄马贵']['贵'] = GUIREN[day_tiangan]
        
        result['总结'] = self._judge_lu_ma_gui_arrival(result, mountain)
        
        return result
    
    def _get_shanjia_lu(self, wuxing: str) -> str:
        lu_map = {'木': '寅', '火': '巳', '土': '巳', '金': '申', '水': '亥'}
        return lu_map.get(wuxing, '')
    
    def _get_shanjia_ma(self, wuxing: str) -> str:
        ma_map = {'木': '巳', '火': '申', '土': '亥', '金': '寅', '水': '巳'}
        return ma_map.get(wuxing, '')
    
    def _get_shanjia_gui(self, wuxing: str) -> str:
        gui_map = {'木': '丑未', '火': '亥酉', '土': '子申', '金': '寅午', '水': '巳卯'}
        return gui_map.get(wuxing, '')
    
    def _judge_lu_ma_gui_arrival(self, lu_ma_gui: dict, mountain: str) -> list:
        judgments = []
        
        if '禄' in lu_ma_gui.get('年柱禄马贵', {}):
            judgments.append(f"年禄在{lu_ma_gui['年柱禄马贵']['禄']}")
        if '马' in lu_ma_gui.get('年柱禄马贵', {}):
            judgments.append(f"年马在{lu_ma_gui['年柱禄马贵']['马']}")
        if '贵' in lu_ma_gui.get('年柱禄马贵', {}):
            judgments.append(f"年贵在{lu_ma_gui['年柱禄马贵']['贵']}")
        
        if '禄' in lu_ma_gui.get('日柱禄马贵', {}):
            judgments.append(f"日禄在{lu_ma_gui['日柱禄马贵']['禄']}")
        if '马' in lu_ma_gui.get('日柱禄马贵', {}):
            judgments.append(f"日马在{lu_ma_gui['日柱禄马贵']['马']}")
        if '贵' in lu_ma_gui.get('日柱禄马贵', {}):
            judgments.append(f"日贵在{lu_ma_gui['日柱禄马贵']['贵']}")
        
        return judgments
    
    def _calculate_score(self, analysis: dict, lu_ma_gui_analysis: dict) -> int:
        score = 50
        
        for name, info in analysis['化气分析'].items():
            if info['与山家关系'] == '比和（吉）':
                score += 20
                break
        
        lu_ma_count = len(lu_ma_gui_analysis.get('总结', []))
        score += min(lu_ma_count * 5, 30)
        
        return max(0, min(100, score))
    
    def _get_auspicious_level(self, score: int) -> str:
        if score >= 90:
            return '上上吉'
        elif score >= 80:
            return '上吉'
        elif score >= 70:
            return '中吉'
        elif score >= 60:
            return '小吉'
        else:
            return '平'
    
    def select_best_dates(self, mountain: str, start_year: int, end_year: int, 
                         date_count: int = 5) -> list:
        all_dates = []
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                for day in range(1, 29):
                    try:
                        result = self.calculate_date_score(mountain, year, month, day)
                        all_dates.append(result)
                    except:
                        continue
        
        all_dates.sort(key=lambda x: x['综合评分'], reverse=True)
        return all_dates[:date_count]


def test_smart_selector():
    selector = SmartDateSelector()
    
    print("=== 准确版测试 ===")
    
    print("\n【年柱测试】")
    for year in [2026, 2027, 2028]:
        ganzhi = selector.get_year_ganzhi(year)
        print(f"{year}年：{ganzhi[0]}{ganzhi[1]}年")
    
    print("\n【月柱测试（以节气为界）】")
    # 测试 2026 年不同日期的月柱
    test_month_dates = [
        (2026, 2, 3, "立春前，应为乙巳年己丑月"),
        (2026, 2, 5, "立春后，应为丙午年庚寅月"),
        (2026, 3, 5, "惊蛰前，应为丙午年庚寅月"),
        (2026, 3, 6, "惊蛰后，应为丙午年辛卯月"),
    ]
    for year, month, day, note in test_month_dates:
        ganzhi = selector.get_month_ganzhi(year, month, day)
        print(f"{year}年{month}月{day}日：{ganzhi[0]}{ganzhi[1]}月 ({note})")
    
    print("\n【日柱测试】")
    test_dates = [
        (2026, 1, 1),
        (2026, 1, 15),
        (2026, 2, 1),
        (2026, 6, 15),
        (2026, 12, 31)
    ]
    
    for year, month, day in test_dates:
        ganzhi = selector.get_day_ganzhi(year, month, day)
        print(f"{year}年{month}月{day}日：{ganzhi[0]}{ganzhi[1]}日")
    
    print("\n【择日测试】")
    result = selector.select_best_dates('壬', 2026, 2026, 5)
    
    for i, date in enumerate(result, 1):
        print(f"\n第{i}名：{date['公历日期']}")
        print(f"  农历：{date['农历日期']}")
        print(f"  四柱：{date['四柱']}")
        print(f"  评分：{date['综合评分']}")
        print(f"  吉凶：{date['吉凶等级']}")


if __name__ == '__main__':
    test_smart_selector()
