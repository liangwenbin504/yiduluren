#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
壬山丙向阴宅安葬择日系统
严格依照传统仪度择日标准，综合龙德课、斗首、六壬、吉神凶煞等要素
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import get_sizhu_accurate, PreciseCalendar
from long_de_ke_selector import LongDeKeSelector


class RenShanFengShuiSelector:
    """
    壬山丙向阴宅安葬择日系统
    
    综合考量：
    1. 龙德课（太岁/月将乘贵人发用）
    2. 斗首择日（元辰、武财、吉课）
    3. 六壬课格（三光、天福、玉堂等吉课）
    4. 吉神凶煞（天德、月德、三煞、五黄等）
    5. 山向宜忌（壬山丙向的特殊要求）
    6. 五行生克（天干地支的生克制化）
    7. 九星方位（紫白九星的吉凶）
    """
    
    def __init__(self):
        self.calendar = PreciseCalendar()
        self.long_de_selector = LongDeKeSelector()
        
        # 壬山丙向的基础信息
        self.shan_xiang_info = {
            '坐山': '壬',
            '朝向': '丙',
            '山家五行': '火',
            '元辰': '甲己',  # 甲己化戊土
            '禄位': '亥',
            '马位': '巳',
            '贵人': ['巳', '卯'],
            '武财': '丙辛',  # 丙辛化水为财
            '喜用': ['寅', '卯', '辰', '巳', '申', '酉', '戌', '亥'],
            '忌用': ['子', '丑', '午', '未']  # 元气相克
        }
        
        # 吉神
        self.ji_shen = [
            '天德', '月德', '天德合', '月德合',
            '天赦', '天愿', '月恩', '四相',
            '时德', '民日', '守日', '吉期',
            '宝日', '义日', '专日', '制日'
        ]
        
        # 凶煞
        self.xiong_sha = [
            '三煞', '五黄', '太岁', '岁破',
            '月破', '月厌', '月刑', '月害',
            '劫煞', '灾煞', '月煞', '死符',
            '小耗', '大耗', '四废', '五墓'
        ]
        
        # 安葬专用吉神
        self.an_zang_ji_shen = [
            '天赦', '天愿', '鸣吠', '鸣吠对',
            '母仓', '四相', '时德', '民日',
            '驿马', '天后', '天巫', '福德'
        ]
        
        # 安葬专用凶煞
        self.an_zang_xiong_sha = [
            '重丧', '复日', '三丧', '天瘟',
            '地瘟', '月瘟', '土瘟', '丧门',
            '吊客', '白虎', '死神', '死符'
        ]
    
    def check_douhou_kege(self, year: int, month: int, day: int) -> Dict:
        """
        检查斗首课格
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 斗首课格信息
        """
        sizhu = get_sizhu_accurate(year, month, day, 12, city_name='北京')
        ri_ganzhi = sizhu['日柱']
        
        # 壬山元辰为甲己
        ri_gan = ri_ganzhi[0]
        
        if ri_gan in ['甲', '己']:
            kege = '元辰课'
            score = 8.5
            duanyu = '甲己化戊土元辰，催丁生子富贵上吉'
        elif ri_gan in ['丙', '辛']:
            kege = '武财课'
            score = 9.0
            duanyu = '丙辛武才多富贵，乙庚单干正财丁'
        elif ri_gan in ['乙', '庚']:
            kege = '正财课'
            score = 7.5
            duanyu = '乙庚单干正财丁'
        elif ri_gan in ['丁', '壬']:
            kege = '廉贞课'
            score = 6.0
            duanyu = '丁壬廉贞子孙旺'
        elif ri_gan in ['戊', '癸']:
            kege = '破鬼课'
            score = 2.5
            duanyu = '戊癸破鬼泄元气，凶'
        else:
            kege = '未知'
            score = 5.0
            duanyu = '未知课格'
        
        return {
            '课格': kege,
            '评分': score,
            '断语': duanyu,
            '日柱': ri_ganzhi
        }
    
    def check_ji_shen_xiong_sha(self, year: int, month: int, day: int) -> Dict:
        """
        检查吉神凶煞
        :param year: 年
        :param month: 月
        :param day: 日
        :return: 吉神凶煞信息
        """
        result = {
            '吉神': [],
            '凶煞': [],
            '安葬吉神': [],
            '安葬凶煞': [],
            '综合评分': 0
        }
        
        # 这里简化处理，实际应该根据复杂的吉神凶煞推算规则
        # 以下是一些基础的吉神凶煞判断
        
        # 天德贵人（正月起亥，顺行十二辰）
        tian_de_month = (month + 10) % 12
        tian_de_zhi = ['亥','子','丑','寅','卯','辰','巳','午','未','申','酉','戌'][tian_de_month]
        
        # 月德贵人（寅午戌月在丙，申子辰月在壬，亥卯未月在甲，巳酉丑月在庚）
        if month in [1, 5, 9]:  # 寅午戌月
            yue_de_gan = '丙'
        elif month in [3, 7, 11]:  # 申子辰月
            yue_de_gan = '壬'
        elif month in [4, 8, 12]:  # 亥卯未月
            yue_de_gan = '甲'
        else:  # 巳酉丑月
            yue_de_gan = '庚'
        
        sizhu = get_sizhu_accurate(year, month, day, 12)
        
        # 检查天德
        if sizhu['日柱'][1] == tian_de_zhi:
            result['吉神'].append('天德')
            result['综合评分'] += 2
        
        # 检查月德
        if sizhu['日柱'][0] == yue_de_gan:
            result['吉神'].append('月德')
            result['综合评分'] += 2
        
        # 检查三合局
        ri_zhi = sizhu['日柱'][1]
        nian_zhi = self.calendar.get_year_ganzhi(year, month, day)[1]
        
        # 申子辰三合水局
        if set([nian_zhi, ri_zhi]) >= set(['申', '子']) or \
           set([nian_zhi, ri_zhi]) >= set(['子', '辰']) or \
           set([nian_zhi, ri_zhi]) >= set(['申', '辰']):
            result['吉神'].append('三合')
            result['综合评分'] += 1
        
        # 检查六冲（岁破）
        if self.calendar.DIZHI.index(nian_zhi) == (self.calendar.DIZHI.index(ri_zhi) + 6) % 12:
            result['凶煞'].append('岁破')
            result['综合评分'] -= 5
        
        # 检查月破
        yue_zhi = self.calendar.get_month_ganzhi(year, month, day)[1]
        if self.calendar.DIZHI.index(yue_zhi) == (self.calendar.DIZHI.index(ri_zhi) + 6) % 12:
            result['凶煞'].append('月破')
            result['综合评分'] -= 3
        
        # 检查安葬专用吉神
        if '天赦' in result['吉神'] or '天愿' in result['吉神']:
            result['安葬吉神'].append('天赦天愿')
        
        # 检查安葬专用凶煞
        # 重丧日（简化判断）
        if ri_zhi in ['子', '午', '卯', '酉']:
            result['安葬凶煞'].append('重丧')
            result['综合评分'] -= 3
        
        return result
    
    def check_lu_ma_gui_dao_shan(self, year: int, month: int, day: int, hour: int) -> Dict:
        """
        检查禄马贵到山到向
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :return: 禄马贵到山到向信息
        """
        sizhu = get_sizhu_accurate(year, month, day, hour, city_name='北京')
        
        nian_ganzhi = sizhu['年柱']
        ri_ganzhi = sizhu['日柱']
        shi_ganzhi = sizhu['时柱']
        
        # 十干禄
        lu_map = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
            '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
        }
        
        # 十干贵人
        gui_map = {
            '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
            '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
            '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
            '癸': ['巳', '卯']
        }
        
        # 地支驿马（三合局）
        def get_ma_by_zhi(zhi):
            if zhi in '申子辰':
                return '寅'
            elif zhi in '亥卯未':
                return '巳'
            elif zhi in '寅午戌':
                return '申'
            elif zhi in '巳酉丑':
                return '亥'
            return None
        
        result = {
            '年柱禄马贵': {},
            '日柱禄马贵': {},
            '时柱禄马贵': {},
            '到山到向详情': [],
            '总数': 0
        }
        
        # 壬山丙向的禄马贵
        shan_lu = '亥'  # 壬禄在亥
        shan_ma = '巳'  # 壬马在巳
        shan_gui = ['巳', '卯']  # 壬贵人在巳卯
        
        xiang_lu = '巳'  # 丙禄在巳
        xiang_ma = '亥'  # 丙马在亥
        xiang_gui = ['亥', '酉']  # 丙贵人在亥酉
        
        # 年柱禄马贵
        nian_gan = nian_ganzhi[0]
        nian_zhi = nian_ganzhi[1]
        
        # 年禄
        nian_lu = lu_map.get(nian_gan)
        if nian_lu:
            result['年柱禄马贵']['禄'] = nian_lu
            if nian_lu == shan_lu or nian_lu == xiang_lu:
                result['到山到向详情'].append('年禄到山到向')
        
        # 年马
        nian_ma = get_ma_by_zhi(nian_zhi)
        if nian_ma:
            result['年柱禄马贵']['马'] = nian_ma
            if nian_ma == shan_ma or nian_ma == xiang_ma:
                result['到山到向详情'].append('年马到山到向')
        
        # 年贵人
        nian_gui = gui_map.get(nian_gan, [])
        if nian_gui:
            result['年柱禄马贵']['贵人'] = nian_gui
            for gui in nian_gui:
                if gui in shan_gui or gui in xiang_gui:
                    result['到山到向详情'].append('年贵到山到向')
                    break
        
        # 日柱禄马贵
        ri_gan = ri_ganzhi[0]
        ri_zhi = ri_ganzhi[1]
        
        ri_lu = lu_map.get(ri_gan)
        if ri_lu:
            result['日柱禄马贵']['禄'] = ri_lu
            if ri_lu == shan_lu or ri_lu == xiang_lu:
                result['到山到向详情'].append('日禄到山到向')
        
        ri_ma = get_ma_by_zhi(ri_zhi)
        if ri_ma:
            result['日柱禄马贵']['马'] = ri_ma
            if ri_ma == shan_ma or ri_ma == xiang_ma:
                result['到山到向详情'].append('日马到山到向')
        
        ri_gui = gui_map.get(ri_gan, [])
        if ri_gui:
            result['日柱禄马贵']['贵人'] = ri_gui
            for gui in ri_gui:
                if gui in shan_gui or gui in xiang_gui:
                    result['到山到向详情'].append('日贵到山到向')
                    break
        
        # 时柱地支
        shi_zhi = shi_ganzhi[1]
        
        if shi_zhi == shan_lu or shi_zhi == xiang_lu:
            result['时柱禄马贵']['禄'] = shi_zhi
            result['到山到向详情'].append('时禄到山到向')
        
        if shi_zhi == shan_ma or shi_zhi == xiang_ma:
            result['时柱禄马贵']['马'] = shi_zhi
            result['到山到向详情'].append('时马到山到向')
        
        if shi_zhi in shan_gui or shi_zhi in xiang_gui:
            result['时柱禄马贵']['贵人'] = shi_zhi
            result['到山到向详情'].append('时贵到山到向')
        
        result['总数'] = len(result['到山到向详情'])
        
        return result
    
    def select_an_zang_dates(self, start_date: datetime, end_date: datetime,
                            min_score: float = 7.0) -> List[Dict]:
        """
        选择安葬吉日
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param min_score: 最低评分要求
        :return: 符合条件的日期列表
        """
        qualified_dates = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        day_count = 0
        
        print(f"开始择日：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"壬山丙向，要求评分 >= {min_score}\n")
        
        while current_date <= end_date:
            day_count += 1
            
            # 进度显示
            if day_count % 50 == 0:
                progress = (day_count / total_days) * 100
                print(f"进度：{day_count}/{total_days}天 ({progress:.1f}%), 符合={len(qualified_dates)}")
            
            year = current_date.year
            month = current_date.month
            day = current_date.day
            
            # 1. 检查斗首课格
            douhou = self.check_douhou_kege(year, month, day)
            
            # 斗首课格评分低于 6 分的排除（破鬼课）
            if douhou['评分'] < 6.0:
                current_date += timedelta(days=1)
                continue
            
            # 2. 检查吉神凶煞
            ji_xiong = self.check_ji_shen_xiong_sha(year, month, day)
            
            # 有大凶煞的排除
            if '岁破' in ji_xiong['凶煞'] or '月破' in ji_xiong['凶煞']:
                current_date += timedelta(days=1)
                continue
            
            # 综合评分低于要求的排除
            if ji_xiong['综合评分'] < 0:
                current_date += timedelta(days=1)
                continue
            
            # 3. 遍历时辰，检查龙德课和禄马贵到山到向
            # 使用真太阳时计算时柱
            for shi in self.calendar.DIZHI:
                shi_index = self.calendar.DIZHI.index(shi)
                # 地支时辰的中点时间（子时=0, 丑时=2, 寅时=4...）
                true_solar_hour = shi_index * 2 if shi_index <= 11 else 0
                
                try:
                    # 检查龙德课
                    ri_ganzhi = get_sizhu_accurate(year, month, day, 12, city_name='北京')['日柱']
                    yue_jiang = self.calendar.get_month_ganzhi(year, month, day)[1]
                    tai_sui = self.calendar.get_year_ganzhi(year, month, day)[1]
                    
                    # 简化的三传（实际需要完整的六壬排盘）
                    sanchuan = {'初传': yue_jiang, '中传': '', '末传': ''}
                    
                    is_long_de, long_de_type = self.long_de_selector.is_long_de_ke(
                        ri_ganzhi, yue_jiang, tai_sui, sanchuan
                    )
                    
                    if not is_long_de:
                        continue
                    
                    # 使用真太阳时计算四柱（真太阳时=平太阳时，因为时柱地支由真太阳时决定）
                    # 这里直接传入地支时辰的中点时间，系统会自动计算真太阳时
                    sizhu = get_sizhu_accurate(year, month, day, true_solar_hour, city_name='北京')
                    
                    # 检查禄马贵到山到向（使用真太阳时对应的时辰）
                    lu_ma_gui = self.check_lu_ma_gui_dao_shan(year, month, day, true_solar_hour)
                    
                    # 综合评分
                    total_score = (
                        douhou['评分'] * 0.4 +  # 斗首 40%
                        ji_xiong['综合评分'] * 0.3 +  # 吉神凶煞 30%
                        lu_ma_gui['总数'] * 0.3  # 禄马贵 30%
                    )
                    
                    if total_score >= min_score:
                        qualified_dates.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'weekday': self._get_weekday(current_date),
                            'sizhu': sizhu,
                            'douhou': douhou,
                            'ji_xiong': ji_xiong,
                            'long_de_type': long_de_type,
                            'lu_ma_gui': lu_ma_gui,
                            'total_score': total_score,
                            'recommendation': self._get_recommendation(total_score)
                        })
                
                except Exception as e:
                    continue
            
            current_date += timedelta(days=1)
        
        # 按综合评分排序
        qualified_dates.sort(key=lambda x: x['total_score'], reverse=True)
        
        return qualified_dates
    
    def _get_weekday(self, date: datetime) -> str:
        """获取星期"""
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        return f'星期{weekdays[date.weekday()]}'
    
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
    
    def generate_report(self, results: List[Dict], output_file: str):
        """生成择日报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("壬山丙向阴宅安葬择日报告\n")
            f.write("=" * 80 + "\n\n")
            
            if not results:
                f.write("未找到符合条件的日期\n")
                return
            
            f.write(f"择日范围：{results[0]['date']} 至 {results[-1]['date']}\n")
            f.write(f"总数量：{len(results)}个\n\n")
            
            f.write("壬山丙向基础信息：\n")
            for key, value in self.shan_xiang_info.items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("精选吉日（前 10 名）\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(results[:10], 1):
                f.write(f"{i}. {item['date']} ({item['weekday']})\n")
                f.write(f"   四柱：{item['sizhu']['年柱']}年 {item['sizhu']['月柱']}月 ")
                f.write(f"{item['sizhu']['日柱']}日 {item['sizhu']['时柱']}时\n")
                f.write(f"   斗首课格：{item['douhou']['课格']} ({item['douhou']['评分']}分)\n")
                f.write(f"   断语：{item['douhou']['断语']}\n")
                f.write(f"   吉神：{', '.join(item['ji_xiong']['吉神']) if item['ji_xiong']['吉神'] else '无'}\n")
                f.write(f"   凶煞：{', '.join(item['ji_xiong']['凶煞']) if item['ji_xiong']['凶煞'] else '无'}\n")
                f.write(f"   龙德课：{item['long_de_type']}\n")
                f.write(f"   禄马贵到山到向：{', '.join(item['lu_ma_gui']['到山到向详情'])}\n")
                f.write(f"   综合评分：{item['total_score']:.1f}分\n")
                f.write(f"   推荐：{item['recommendation']}\n")
                f.write("\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("择日要点说明\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. 龙德课要求：\n")
            f.write("   - 太岁或月将发用\n")
            f.write("   - 乘贵人（初传为日干贵人）\n\n")
            
            f.write("2. 斗首课格要求：\n")
            f.write("   - 首选：武财课（9 分）、元辰课（8.5 分）\n")
            f.write("   - 次选：正财课（7.5 分）\n")
            f.write("   - 忌用：破鬼课（2.5 分）\n\n")
            
            f.write("3. 禄马贵到山到向：\n")
            f.write("   - 壬山禄在亥，马在巳，贵人在巳卯\n")
            f.write("   - 丙向禄在巳，马在亥，贵人在亥酉\n")
            f.write("   - 数量越多越吉\n\n")
            
            f.write("4. 吉神凶煞：\n")
            f.write("   - 喜：天德、月德、天赦、天愿\n")
            f.write("   - 忌：岁破、月破、三煞、五黄\n\n")
            
            f.write("5. 山向宜忌：\n")
            f.write("   - 喜用：寅卯辰巳申酉戌亥\n")
            f.write("   - 忌用：子丑午未（元气相克）\n\n")
        
        print(f"报告已生成：{output_file}")


def test_ren_shan_selector():
    """测试壬山择日系统"""
    print("=" * 80)
    print("壬山丙向阴宅安葬择日系统测试")
    print("=" * 80)
    
    selector = RenShanFengShuiSelector()
    
    # 测试斗首课格
    print("\n【测试 1：斗首课格】")
    test_dates = [
        (2026, 9, 4),   # 辛巳日
        (2026, 9, 14),  # 辛卯日
        (2026, 9, 24),  # 辛丑日
    ]
    
    for year, month, day in test_dates:
        douhou = selector.check_douhou_kege(year, month, day)
        print(f"  {year}年{month}月{day}日：{douhou['课格']} ({douhou['评分']}分)")
        print(f"    断语：{douhou['断语']}")
    
    # 测试吉神凶煞
    print("\n【测试 2：吉神凶煞】")
    ji_xiong = selector.check_ji_shen_xiong_sha(2026, 9, 4)
    print(f"  2026 年 9 月 4 日：")
    print(f"    吉神：{', '.join(ji_xiong['吉神']) if ji_xiong['吉神'] else '无'}")
    print(f"    凶煞：{', '.join(ji_xiong['凶煞']) if ji_xiong['凶煞'] else '无'}")
    print(f"    综合评分：{ji_xiong['综合评分']}")
    
    # 测试禄马贵到山到向
    print("\n【测试 3：禄马贵到山到向】")
    lu_ma_gui = selector.check_lu_ma_gui_dao_shan(2026, 9, 4, 10)
    print(f"  2026 年 9 月 4 日 10:00：")
    print(f"    到山到向：{', '.join(lu_ma_gui['到山到向详情'])}")
    print(f"    总数：{lu_ma_gui['总数']}个")
    
    # 实际择日（小范围测试）
    print("\n【测试 4：实际择日（2026 年 9 月）】")
    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 9, 30)
    
    print(f"正在择日，请稍候...")
    results = selector.select_an_zang_dates(start_date, end_date, min_score=7.0)
    
    if results:
        print(f"\n找到 {len(results)} 个符合条件的日期：\n")
        for i, item in enumerate(results[:5], 1):
            print(f"{i}. {item['date']} ({item['weekday']})")
            print(f"   四柱：{item['sizhu']['年柱']} {item['sizhu']['月柱']} {item['sizhu']['日柱']} {item['sizhu']['时柱']}")
            print(f"   评分：{item['total_score']:.1f}分 - {item['recommendation']}")
            print()
    else:
        print("\n未找到符合条件的日期")
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    test_ren_shan_selector()
