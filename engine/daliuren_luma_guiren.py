#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬禄马贵人到山到向完整计算模块
依据传统大六壬理论，实现年月日时四柱禄马贵人到山到向的完整判定逻辑
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

# 先定义默认值
GuiRenCalculator = None

# 完整的天地盘函数
def arrange_tiandi_pan(yuejiang, shichen):
    DIZHI_LOCAL = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    shi_index = DIZHI_LOCAL.index(shichen)
    yuejiang_index = DIZHI_LOCAL.index(yuejiang)
    zi_position = (shi_index - yuejiang_index) % 12
    tian_pan = []
    for i in range(12):
        tian_index = (i - zi_position) % 12
        tian_pan.append(DIZHI_LOCAL[tian_index])
    result = {}
    for i in range(12):
        result[DIZHI_LOCAL[i]] = tian_pan[i]
    return result

# 动态导入：尝试多种路径
try:
    from gui_ren_engine import GuiRenCalculator as ImportedGuiRenCalculator
    GuiRenCalculator = ImportedGuiRenCalculator
except ImportError:
    try:
        from core_modules.engine.gui_ren_engine import GuiRenCalculator as ImportedGuiRenCalculator
        GuiRenCalculator = ImportedGuiRenCalculator
    except ImportError:
        pass


class DaLiuRenLuMaGuiRen:
    """大六壬禄马贵人到山到向计算器"""
    
    # 十天干禄神
    LU = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
        '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    # 十二地支驿马
    YIMA = {
        '申': '寅', '子': '寅', '辰': '寅',
        '亥': '巳', '卯': '巳', '未': '巳',
        '寅': '申', '午': '申', '戌': '申',
        '巳': '亥', '酉': '亥', '丑': '亥'
    }
    
    # 二十四山山家映射（斗首体系）
    SHAN_JIA_MAP = {
        '壬': '子', '子': '子', '癸': '子', '丑': '子',
        '艮': '丑', '寅': '丑', '甲': '卯', '卯': '卯',
        '乙': '卯', '辰': '卯', '巽': '辰', '巳': '辰',
        '丙': '午', '午': '午', '丁': '午', '未': '午',
        '坤': '未', '申': '未', '庚': '酉', '酉': '酉',
        '辛': '酉', '戌': '酉', '乾': '戌', '亥': '戌'
    }
    
    YUEJIANG_MAP = {
        '寅': '亥', '卯': '戌', '辰': '酉', '巳': '申',
        '午': '未', '未': '午', '申': '巳', '酉': '辰',
        '戌': '卯', '亥': '寅', '子': '丑', '丑': '子'
    }
    
    def get_yuejiang(self, yue_zhi: str) -> str:
        """
        根据月支获取月将
        
        月将（太阳过宫）对应关系：
        正月（寅）：亥（登明）
        二月（卯）：戌（河魁）
        三月（辰）：酉（从魁）
        四月（巳）：申（传送）
        五月（午）：未（小吉）
        六月（未）：午（胜光）
        七月（申）：巳（太乙）
        八月（酉）：辰（天罡）
        九月（戌）：卯（太冲）
        十月（亥）：寅（功曹）
        十一月（子）：丑（大吉）
        十二月（丑）：子（神后）
        """
        return self.YUEJIANG_MAP.get(yue_zhi, '亥')
    
    def get_yuejiang_by_date(self, year: int, month: int, day: int) -> str:
        """
        根据日期计算月将（考虑中气）
        
        月将（太阳过宫）是根据太阳在黄道上的位置确定的：
        每个月的中气日期大约在：
        - 1月20日左右：大寒 → 子（神后）
        - 2月19日左右：雨水 → 亥（登明）
        - 3月21日左右：春分 → 戌（河魁）
        - 4月20日左右：谷雨 → 酉（从魁）
        - 5月21日左右：小满 → 申（传送）
        - 6月21日左右：夏至 → 未（小吉）
        - 7月23日左右：大暑 → 午（胜光）
        - 8月23日左右：处暑 → 巳（太乙）
        - 9月23日左右：秋分 → 辰（天罡）
        - 10月24日左右：霜降 → 卯（太冲）
        - 11月22日左右：小雪 → 寅（功曹）
        - 12月22日左右：冬至 → 丑（大吉）
        
        注意：中气日期每年略有不同，这里使用近似值
        """
        ZHONGQI_DATES = [
            (1, 20, '子'),
            (2, 19, '亥'),
            (3, 21, '戌'),
            (4, 20, '酉'),
            (5, 21, '申'),
            (6, 21, '未'),
            (7, 23, '午'),
            (8, 23, '巳'),
            (9, 23, '辰'),
            (10, 24, '卯'),
            (11, 22, '寅'),
            (12, 22, '丑'),
        ]
        
        yuejiang = '子'
        for m, d, yj in ZHONGQI_DATES:
            if (month > m) or (month == m and day >= d):
                yuejiang = yj
        
        return yuejiang
    
    # 二十四山向首映射（斗首体系）
    XIANG_SHOU_MAP = {
        '壬': '午', '子': '午', '癸': '午', '丑': '午',
        '艮': '未', '寅': '未', '甲': '酉', '卯': '酉',
        '乙': '酉', '辰': '酉', '巽': '戌', '巳': '戌',
        '丙': '子', '午': '子', '丁': '子', '未': '子',
        '坤': '丑', '申': '丑', '庚': '卯', '酉': '卯',
        '辛': '卯', '戌': '卯', '乾': '辰', '亥': '辰'
    }
    
    # 本山禄神（二十四山本山对应禄神）
    BEN_SHAN_LU = {
        '壬': '亥', '子': '子', '癸': '子', '丑': '丑',
        '艮': '寅', '寅': '寅', '甲': '卯', '卯': '卯',
        '乙': '辰', '辰': '辰', '巽': '巳', '巳': '巳',
        '丙': '午', '午': '午', '丁': '未', '未': '未',
        '坤': '申', '申': '申', '庚': '酉', '酉': '酉',
        '辛': '戌', '戌': '戌', '乾': '亥', '亥': '亥'
    }
    
    # 本山贵人（二十四山本山对应贵人）
    BEN_SHAN_GUIREN = {
        '壬': ['卯', '巳'], '子': ['坤', '巽'], '癸': ['卯', '巳'], '丑': ['艮', '兑'],
        '艮': ['丑', '未'], '寅': ['艮', '坤'], '甲': ['丑', '未'], '卯': ['震', '兑'],
        '乙': ['子', '申'], '辰': ['巽', '乾'], '巽': ['辰', '戌'], '巳': ['巽', '乾'],
        '丙': ['亥', '酉'], '午': ['离', '坎'], '丁': ['亥', '酉'], '未': ['坤', '艮'],
        '坤': ['未', '丑'], '申': ['坤', '巽'], '庚': ['寅', '午'], '酉': ['兑', '震'],
        '辛': ['寅', '午'], '戌': ['乾', '巽'], '乾': ['戌', '辰'], '亥': ['乾', '巽']
    }
    
    def __init__(self):
        self.gui_ren_calc = GuiRenCalculator() if GuiRenCalculator else None
    
    def get_shan_jia(self, mountain: str) -> str:
        """获取山家（斗首体系）"""
        return self.SHAN_JIA_MAP.get(mountain, '子')
    
    def get_xiang_shou(self, mountain: str) -> str:
        """获取向首（斗首体系）"""
        return self.XIANG_SHOU_MAP.get(mountain, '午')
    
    def get_lu_zhi(self, tian_gan: str) -> str:
        """获取日干禄神位置"""
        return self.LU.get(tian_gan, '')
    
    def get_ma_zhi(self, di_zhi: str) -> str:
        """获取日支驿马位置"""
        return self.YIMA.get(di_zhi, '')
    
    def get_guiren_zhi(self, tian_gan: str, tiandi_pan: Dict, shichen: str) -> Optional[str]:
        """获取贵人位置"""
        if not self.gui_ren_calc:
            return None
        try:
            guiren_info = self.gui_ren_calc.arrange_gui_ren_pan(
                tian_gan, {'天地对应': tiandi_pan}, shichen
            )
            tianjiang_map = guiren_info.get('天将映射', {})
            for zhi, tj in tianjiang_map.items():
                if tj == '贵人':
                    return zhi
        except Exception:
            pass
        return None
    
    def check_pillar_all_qualified(self, tian_gan: str, di_zhi: str,
                                    tiandi_pan: Dict, shichen: str,
                                    shan_jia: str, xiang_shou: str) -> bool:
        """
        检查某柱的禄、马、贵人是否至少有一个到山或到向
        
        调整：每柱只要禄、马、贵人中有一个到山或到向，该柱就算合格
        （原要求三个都到太严格，导致几乎没有合格课）
        
        参数:
            tian_gan: 天干
            di_zhi: 地支
            tiandi_pan: 天地盘
            shichen: 时辰
            shan_jia: 山家
            xiang_shou: 向首
        
        返回:
            True 如果禄、马、贵人至少有一个到山或到向
        """
        lu_zhi = self.get_lu_zhi(tian_gan)
        ma_zhi = self.get_ma_zhi(di_zhi)
        guiren_zhi = self.get_guiren_zhi(tian_gan, tiandi_pan, shichen)
        
        # 禄到山或到向
        lu_qualified = (lu_zhi == shan_jia or lu_zhi == xiang_shou) if lu_zhi else False
        
        # 马到山或到向
        ma_qualified = (ma_zhi == shan_jia or ma_zhi == xiang_shou) if ma_zhi else False
        
        # 贵人到山或到向
        guiren_qualified = (guiren_zhi == shan_jia or guiren_zhi == xiang_shou) if guiren_zhi else False
        
        # 只要有一个到山或到向就算合格
        return lu_qualified or ma_qualified or guiren_qualified
    
    def check_sanchuan_luma_guiren_count(self, sanchuan: Dict,
                                          ri_gan: str, ri_zhi: str,
                                          tiandi_pan: Dict = None, shichen: str = None) -> int:
        """
        检查三传中禄马贵人的数量
        
        用户要求：三传中至少要有禄、马、贵人中的两个
        
        参数:
            sanchuan: 三传信息
            ri_gan: 日干
            ri_zhi: 日支
            tiandi_pan: 天地盘
            shichen: 时辰
        
        返回:
            三传中禄马贵人的数量（0-3）
        """
        chuan_list = [
            sanchuan.get('初传', ''),
            sanchuan.get('中传', ''),
            sanchuan.get('末传', '')
        ]
        
        ri_lu = self.get_lu_zhi(ri_gan)
        ri_ma = self.get_ma_zhi(ri_zhi)
        ri_guiren = self.get_guiren_zhi(ri_gan, tiandi_pan, shichen) if tiandi_pan and shichen else None
        
        count = 0
        if ri_lu and ri_lu in chuan_list:
            count += 1
        if ri_ma and ri_ma in chuan_list:
            count += 1
        if ri_guiren and ri_guiren in chuan_list:
            count += 1

        return count

    def get_taiyang_position(self, gregorian_month: int, day: int) -> str:
        """
        根据日期获取太阳/月将所在宫位

        太阳即月将，按二十四节气中气过宫来论：
        - 小寒（1月5日）后：子（神后）
        - 大寒（1月20日）后：丑（大吉）
        - 立春（2月4日）后：寅月开始，但雨水前仍是子将
        - 雨水（2月19日）后：亥（登明）
        - 春分（3月21日）后：戌（河魁）
        - 谷雨（4月20日）后：酉（从魁）
        - 小满（5月21日）后：申（传送）
        - 夏至（6月21日）后：未（小吉）
        - 大暑（7月23日）后：午（胜光）
        - 处暑（8月23日）后：巳（太乙）
        - 秋分（9月23日）后：辰（天罡）
        - 霜降（10月24日）后：卯（太冲）
        - 小雪（11月22日）后：寅（功曹）
        - 冬至（12月22日）后：子（神后）

        参数:
            gregorian_month: 公历月份（1-12）
            day: 日期

        返回:
            太阳/月将所在宫位
        """
        return self.get_yuejiang_by_date(2026, gregorian_month, day)

    def gregorian_month_to_yueling(self, gregorian_month: int) -> str:
        """
        将公历月份转换为节气月地支

        十二节气月与公历月份的对应关系：
        - 公历1月（小寒后）-> 丑月
        - 公历2月（立春后）-> 寅月
        - 公历3月（惊蛰后）-> 卯月
        - 公历4月（清明后）-> 辰月
        - 公历5月（立夏后）-> 巳月
        - 公历6月（芒种后）-> 午月
        - 公历7月（小暑后）-> 未月
        - 公历8月（立秋后）-> 申月
        - 公历9月（白露后）-> 酉月
        - 公历10月（寒露后）-> 戌月
        - 公历11月（立冬后）-> 亥月
        - 公历12月（大雪后）-> 子月

        参数:
            gregorian_month: 公历月份（1-12）

        返回:
            节气月地支
        """
        YUELING_LIST = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
        return YUELING_LIST[(gregorian_month - 2 + 12) % 12]

    def check_taiyang_luma_guiren(self, mountain: str, shan_jia: str, xiang_shou: str,
                                   nian_zhi: str, yue_zhi: str, ri_zhi: str, shi_zhi: str,
                                   gregorian_month: int = None) -> Dict:
        """
        检查太阳带禄马贵人到山到向

        梁老师注解：
        1. 太阳带贵人：如甲山以未为贵人，每年午月，太阳在未宫
        2. 太阳带禄神：如甲山以寅为禄，每年亥月，太阳在寅宫
        3. 太阳带太岁：太阳在某宫，该宫地支年即为太岁年

        参数:
            mountain: 坐山
            shan_jia: 山家
            xiang_shou: 向首
            nian_zhi, yue_zhi, ri_zhi, shi_zhi: 年月日时地支
            gregorian_month: 公历月份（1-12），用于计算月将/太阳
        """
        if not gregorian_month:
            gregorian_month = 6
        taiyang = self.get_taiyang_position(gregorian_month, 15)

        mountain_lu = self.LU.get(mountain, '')
        mountain_guiren_list = self.BEN_SHAN_GUIREN.get(mountain, [])

        results = {
            'taiyang': taiyang,
            'taiyang_to_shan': taiyang == shan_jia,
            'taiyang_to_xiang': taiyang == xiang_shou,
            'taiyang_lu': taiyang == mountain_lu,
            'taiyang_guiren': taiyang in mountain_guiren_list,
            'taiyang_ma': False,
            'taiyang_is_taisui': False,
            'taisui_zhi': '',
            'bonus_score': 0,
            'descriptions': []
        }

        if results['taiyang_to_shan']:
            results['descriptions'].append(f'太阳带{taiyang}到山')
        if results['taiyang_to_xiang']:
            results['descriptions'].append(f'太阳带{taiyang}到向')
        if results['taiyang_lu']:
            results['descriptions'].append(f'太阳带{taiyang}禄神到山/向（{mountain}山禄在{taiyang}）')
        if results['taiyang_guiren']:
            guiren_name = mountain_guiren_list[0] if mountain_guiren_list else taiyang
            results['descriptions'].append(f'太阳带{taiyang}贵人到山/向（{mountain}山贵人在{taiyang}）')

        for dz in [nian_zhi, yue_zhi, ri_zhi, shi_zhi]:
            if dz == taiyang:
                results['taiyang_is_taisui'] = True
                results['taisui_zhi'] = taiyang
                results['descriptions'].append(f'太阳在{taiyang}宫，{taiyang}年即为太岁年（太阳带太岁）')
                break

        if results['taiyang_lu'] or results['taiyang_guiren']:
            results['bonus_score'] += 10
        if results['taiyang_is_taisui']:
            results['bonus_score'] += 15

        return results

    def check_taisui_luma_guiren(self, mountain: str, shan_jia: str, xiang_shou: str,
                                  nian_zhi: str, yue_zhi: str, ri_zhi: str) -> Dict:
        """
        检查太岁月建禄马贵人到山到向（以地支论）

        梁老师注解：
        本日、本山向的禄马贵即是大岁和月建，专以地支来论
        如甲山以寅为禄，那么大岁和月建的地支就用寅
        如甲山以丑未为贵人，大岁和月建的地支就用丑未

        参数:
            mountain: 坐山
            shan_jia: 山家
            xiang_shou: 向首
            nian_zhi, yue_zhi, ri_zhi: 年月日地支

        返回:
            太岁月建禄马贵人判定结果
        """
        mountain_lu = self.LU.get(mountain, '')
        mountain_guiren_list = self.BEN_SHAN_GUIREN.get(mountain, [])

        results = {
            'taisui_zhi': nian_zhi,
            'yuejian_zhi': yue_zhi,
            'taisui_lu_to_shan': nian_zhi == mountain_lu and mountain_lu == shan_jia,
            'taisui_lu_to_xiang': nian_zhi == mountain_lu and mountain_lu == xiang_shou,
            'taisui_guiren_to_shan': nian_zhi in mountain_guiren_list and nian_zhi == shan_jia,
            'taisui_guiren_to_xiang': nian_zhi in mountain_guiren_list and nian_zhi == xiang_shou,
            'yuejian_lu_to_shan': yue_zhi == mountain_lu and mountain_lu == shan_jia,
            'yuejian_lu_to_xiang': yue_zhi == mountain_lu and mountain_lu == xiang_shou,
            'yuejian_guiren_to_shan': yue_zhi in mountain_guiren_list and yue_zhi == shan_jia,
            'yuejian_guiren_to_xiang': yue_zhi in mountain_guiren_list and yue_zhi == xiang_shou,
            'bonus_score': 0,
            'descriptions': []
        }

        if results['taisui_lu_to_shan']:
            results['descriptions'].append(f'太岁{nian_zhi}带{mountain}山禄到山')
            results['bonus_score'] += 10
        if results['taisui_lu_to_xiang']:
            results['descriptions'].append(f'太岁{nian_zhi}带{mountain}山禄到向')
            results['bonus_score'] += 10
        if results['taisui_guiren_to_shan']:
            results['descriptions'].append(f'太岁{nian_zhi}带{mountain}山贵人到山')
            results['bonus_score'] += 10
        if results['taisui_guiren_to_xiang']:
            results['descriptions'].append(f'太岁{nian_zhi}带{mountain}山贵人到向')
            results['bonus_score'] += 10
        if results['yuejian_lu_to_shan']:
            results['descriptions'].append(f'月建{yue_zhi}带{mountain}山禄到山')
            results['bonus_score'] += 5
        if results['yuejian_lu_to_xiang']:
            results['descriptions'].append(f'月建{yue_zhi}带{mountain}山禄到向')
            results['bonus_score'] += 5
        if results['yuejian_guiren_to_shan']:
            results['descriptions'].append(f'月建{yue_zhi}带{mountain}山贵人到山')
            results['bonus_score'] += 5
        if results['yuejian_guiren_to_xiang']:
            results['descriptions'].append(f'月建{yue_zhi}带{mountain}山贵人到向')
            results['bonus_score'] += 5

        return results

    def calculate_new_score(self, mountain: str, shichen: str,
                            nian_gan: str, nian_zhi: str,
                            yue_gan: str, yue_zhi: str,
                            ri_gan: str, ri_zhi: str,
                            shi_gan: str, shi_zhi: str,
                            sanchuan: Dict = None,
                            ke_ti_list: List = None) -> Dict:
        """
        按新规则计算评分
        
        评分规则：
        1. 年月日时禄马贵人全到山或全到向且发出三传（禄马贵人之二必占）为100分
        2. 少一项扣分，依次相减
        3. 虽是吉课但禄马贵人不到山也不到向，又不发出三传为平课60分
        4. 之后根据大六壬课体课格的吉凶又依次减分
        
        参数:
            mountain: 坐山
            shichen: 时辰
            nian_gan, nian_zhi: 年柱
            yue_gan, yue_zhi: 月柱
            ri_gan, ri_zhi: 日柱
            shi_gan, shi_zhi: 时柱
            sanchuan: 三传信息
            ke_ti_list: 课体列表
        
        返回:
            评分结果
        """
        shan_jia = self.get_shan_jia(mountain)
        xiang_shou = self.get_xiang_shou(mountain)
        tiandi_pan = arrange_tiandi_pan('亥', shichen)
        
        # 1. 检查四柱禄马贵人是否都到山到向
        nian_qualified = self.check_pillar_all_qualified(
            nian_gan, nian_zhi, tiandi_pan, shichen, shan_jia, xiang_shou
        )
        yue_qualified = self.check_pillar_all_qualified(
            yue_gan, yue_zhi, tiandi_pan, shichen, shan_jia, xiang_shou
        )
        ri_qualified = self.check_pillar_all_qualified(
            ri_gan, ri_zhi, tiandi_pan, shichen, shan_jia, xiang_shou
        )
        shi_qualified = self.check_pillar_all_qualified(
            shi_gan, shi_zhi, tiandi_pan, shichen, shan_jia, xiang_shou
        ) if shi_gan and shi_zhi else False
        
        pillar_qualified_count = sum([nian_qualified, yue_qualified, ri_qualified, shi_qualified])
        
        # 2. 检查三传禄马贵人数量
        sanchuan_luma_count = 0
        sanchuan_qualified = False
        if sanchuan:
            sanchuan_luma_count = self.check_sanchuan_luma_guiren_count(
                sanchuan, ri_gan, ri_zhi, tiandi_pan, shichen
            )
            # 三传中至少2个禄马贵人
            sanchuan_qualified = sanchuan_luma_count >= 2
        
        # 3. 计算基础评分
        # 满分条件：4柱合格 + 三传至少2个禄马贵人
        # 平课条件：0柱合格 + 三传0个禄马贵人
        
        # 满足的项数：四柱合格数 + (三传合格 ? 1 : 0)
        satisfied_items = pillar_qualified_count + (1 if sanchuan_qualified else 0)
        
        # 每项扣分：3分（用户要求）
        item_deduction = 3
        
        # 基础得分 = 100 - (5 - 满足项数) * 3
        base_score = 100 - (5 - satisfied_items) * item_deduction
        base_score = max(60, min(100, base_score))  # 限制在60-100之间
        
        # 4. 课体课格扣分
        ke_ti_deduction = 0
        ke_ti_level = '未知'
        is_daxiong = False
        
        if ke_ti_list:
            ke_ti_name = ke_ti_list[0] if isinstance(ke_ti_list, list) else str(ke_ti_list)
            ke_ti_deduction, ke_ti_level, is_daxiong = self.get_keti_deduction(ke_ti_name)
        
        # 5. 最终得分
        final_score = base_score - ke_ti_deduction
        final_score = max(30, min(100, final_score))  # 最低30分

        # 6. 生成状态描述
        if pillar_qualified_count == 4 and sanchuan_qualified:
            status = '满分：年月日时禄马贵人皆到山到向，三传禄马贵人俱全'
        elif pillar_qualified_count == 0 and sanchuan_luma_count == 0:
            status = '平课：禄马贵人不到山不到向，三传无禄马贵人'
        else:
            status = f'{pillar_qualified_count}柱合格，三传禄马贵人{sanchuan_luma_count}个'

        return {
            'base_score': round(base_score, 1),
            'ke_ti_deduction': ke_ti_deduction,
            'ke_ti_level': ke_ti_level,
            'final_score': round(final_score, 1),
            'status': status,
            'is_daxiong': is_daxiong,
            'pillar_qualified_count': pillar_qualified_count,
            'sanchuan_luma_count': sanchuan_luma_count,
            'sanchuan_qualified': sanchuan_qualified,
            'satisfied_items': satisfied_items,
            'nian_qualified': nian_qualified,
            'yue_qualified': yue_qualified,
            'ri_qualified': ri_qualified,
            'shi_qualified': shi_qualified,
            'taiyang_bonus': 0,
            'taisui_bonus': 0
        }
    
    def get_keti_deduction(self, ke_ti_name: str) -> Tuple[int, str, bool]:
        """
        根据课体名称获取扣分
        
        返回: (扣分, 课体等级, 是否大凶课)
        """
        # 上上吉课
        shangshangji = ['三光课', '富贵课', '龙德课', '三奇课', '六仪课', '时泰课']
        # 上吉课
        shangji = ['元首课', '连珠课', '重审课', '比用课', '涉害课', '遥克课', '昴星课', '别责课', '八专课']
        # 中吉课
        zhongji = ['和美课', '斩关课', '游子课', '长庚课', '玄胎课', '回环课']
        # 小吉课
        xiaoji = ['进连珠', '退连珠', '间传课', '交车课', '交车合', '交车害']
        # 平课
        pingke = ['普通课', '无特殊课体', '伏吟课', '反吟课']
        # 小凶课
        xiaoxiong = ['芜淫课', '解离课', '度厄课', '无禄课', '绝嗣课']
        # 中凶课
        zhongxiong = '孤辰课', '寡宿课', '刑伤课', '二烦课', '三烦课'
        # 大凶课
        daxiong = ['九丑课', '天祸课', '天寇课', '天罗地网', '死奇课', '魄化课', '飞魂课', '丧吊课']
        
        ke_ti_lower = ke_ti_name.lower()
        
        for name in shangshangji:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 0, '上上吉课', False
        
        for name in shangji:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 0, '上吉课', False
        
        for name in zhongji:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 0, '中吉课', False
        
        for name in xiaoji:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 5, '小吉课', False
        
        for name in pingke:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 10, '平课', False
        
        for name in xiaoxiong:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 35, '小凶课', False
        
        for name in zhongxiong:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 40, '中凶课', False
        
        for name in daxiong:
            if name in ke_ti_name or ke_ti_lower in name.lower():
                return 30, '大凶课', True
        
        return 0, '未知', False

    def check_single_pillar(self, tian_gan: str, di_zhi: str, 
                           tiandi_pan: Dict, shichen: str,
                           shan_jia: str, xiang_shou: str,
                           pillar_name: str = '') -> Dict:
        """
        检查单柱禄马贵人到山到向
        
        参数:
            tian_gan: 天干
            di_zhi: 地支
            tiandi_pan: 天地盘
            shichen: 时辰
            shan_jia: 山家
            xiang_shou: 向首
            pillar_name: 柱名（年/月/日/时）
        
        返回:
            禄马贵人到山到向详细信息
        """
        lu_zhi = self.get_lu_zhi(tian_gan)
        ma_zhi = self.get_ma_zhi(di_zhi)
        guiren_zhi = self.get_guiren_zhi(tian_gan, tiandi_pan, shichen)
        
        lu_to_shan = (lu_zhi == shan_jia)
        lu_to_xiang = (lu_zhi == xiang_shou)
        ma_to_shan = (ma_zhi == shan_jia)
        ma_to_xiang = (ma_zhi == xiang_shou)
        guiren_to_shan = (guiren_zhi == shan_jia)
        guiren_to_xiang = (guiren_zhi == xiang_shou)
        
        shan_count = sum([lu_to_shan, ma_to_shan, guiren_to_shan])
        xiang_count = sum([lu_to_xiang, ma_to_xiang, guiren_to_xiang])
        
        pillar_qualified = (shan_count >= 1 or xiang_count >= 1)
        
        result = {
            'pillar': pillar_name,
            'tian_gan': tian_gan,
            'di_zhi': di_zhi,
            'lu_zhi': lu_zhi,
            'ma_zhi': ma_zhi,
            'guiren_zhi': guiren_zhi or '无',
            'lu_to_shan': lu_to_shan,
            'lu_to_xiang': lu_to_xiang,
            'ma_to_shan': ma_to_shan,
            'ma_to_xiang': ma_to_xiang,
            'guiren_to_shan': guiren_to_shan,
            'guiren_to_xiang': guiren_to_xiang,
            'shan_count': shan_count,
            'xiang_count': xiang_count,
            'pillar_qualified': pillar_qualified
        }
        
        return result
    
    def check_ben_shan_ben_xiang(self, mountain: str, 
                                  shan_jia: str, xiang_shou: str,
                                  tiandi_pan: Dict, shichen: str,
                                  nian_gan: str, nian_zhi: str,
                                  yue_gan: str, yue_zhi: str,
                                  ri_gan: str, ri_zhi: str) -> Dict:
        """
        检查本山本向禄马贵人特殊判定规则
        
        规则：
        1. 壬山的禄马贵人到子山
        2. 丙向的禄马贵人到午向
        3. 本山禄神到山/向首
        4. 本山贵人到山/向首
        
        参数:
            mountain: 坐山
            shan_jia: 山家
            xiang_shou: 向首
            tiandi_pan: 天地盘
            shichen: 时辰
            nian_gan: 年干
            nian_zhi: 年支
            yue_gan: 月干
            yue_zhi: 月支
            ri_gan: 日干
            ri_zhi: 日支
        
        返回:
            本山本向判定结果
        """
        ben_shan_results = []
        
        # 检查本山禄神
        ben_shan_lu = self.BEN_SHAN_LU.get(mountain, '')
        if ben_shan_lu:
            lu_to_ben_shan = (ben_shan_lu == shan_jia)
            lu_to_ben_xiang = (ben_shan_lu == xiang_shou)
            if lu_to_ben_shan or lu_to_ben_xiang:
                ben_shan_results.append({
                    'type': '本山禄神',
                    'zhi': ben_shan_lu,
                    'to_shan': lu_to_ben_shan,
                    'to_xiang': lu_to_ben_xiang,
                    'desc': f'本山{mountain}禄神{ben_shan_lu}到{"山" if lu_to_ben_shan else ""}{"向" if lu_to_ben_xiang else ""}'
                })
        
        # 检查本山贵人
        ben_shan_guiren_list = self.BEN_SHAN_GUIREN.get(mountain, [])
        for guiren_zhi in ben_shan_guiren_list:
            guiren_to_ben_shan = (guiren_zhi == shan_jia)
            guiren_to_ben_xiang = (guiren_zhi == xiang_shou)
            if guiren_to_ben_shan or guiren_to_ben_xiang:
                ben_shan_results.append({
                    'type': '本山贵人',
                    'zhi': guiren_zhi,
                    'to_shan': guiren_to_ben_shan,
                    'to_xiang': guiren_to_ben_xiang,
                    'desc': f'本山{mountain}贵人{guiren_zhi}到{"山" if guiren_to_ben_shan else ""}{"向" if guiren_to_ben_xiang else ""}'
                })
        
        # 壬山丙向特殊判定
        if mountain == '壬' or mountain == '丙':
            # 壬山检查子山
            if mountain == '壬':
                # 检查各柱禄马贵人到子山
                for pillar_name, (gan, zhi) in [
                    ('年', (nian_gan, nian_zhi)),
                    ('月', (yue_gan, yue_zhi)),
                    ('日', (ri_gan, ri_zhi))
                ]:
                    pillar_result = self.check_single_pillar(
                        gan, zhi, tiandi_pan, shichen, '子', '午', pillar_name
                    )
                    if pillar_result['pillar_qualified']:
                        ben_shan_results.append({
                            'type': '壬山特殊',
                            'pillar': pillar_name,
                            'desc': f'壬山{pillar_name}柱禄马贵人到子山'
                        })
            
            # 丙向检查午向
            if mountain == '丙':
                for pillar_name, (gan, zhi) in [
                    ('年', (nian_gan, nian_zhi)),
                    ('月', (yue_gan, yue_zhi)),
                    ('日', (ri_gan, ri_zhi))
                ]:
                    pillar_result = self.check_single_pillar(
                        gan, zhi, tiandi_pan, shichen, '子', '午', pillar_name
                    )
                    if pillar_result['pillar_qualified']:
                        ben_shan_results.append({
                            'type': '丙向特殊',
                            'pillar': pillar_name,
                            'desc': f'丙向{pillar_name}柱禄马贵人到午向'
                        })
        
        return {
            'has_ben_shan_ji': len(ben_shan_results) > 0,
            'results': ben_shan_results
        }
    
    def analyze_full(self, mountain: str, shichen: str,
                    nian_gan: str, nian_zhi: str,
                    yue_gan: str, yue_zhi: str,
                    ri_gan: str, ri_zhi: str) -> Dict:
        """
        完整分析年月日时四柱禄马贵人到山到向
        
        参数:
            mountain: 坐山
            shichen: 时辰
            nian_gan: 年干
            nian_zhi: 年支
            yue_gan: 月干
            yue_zhi: 月支
            ri_gan: 日干
            ri_zhi: 日支
        
        返回:
            完整分析结果
        """
        shan_jia = self.get_shan_jia(mountain)
        xiang_shou = self.get_xiang_shou(mountain)
        tiandi_pan = arrange_tiandi_pan('亥', shichen)
        
        # 分析各柱
        nian_result = self.check_single_pillar(
            nian_gan, nian_zhi, tiandi_pan, shichen, 
            shan_jia, xiang_shou, '年'
        )
        yue_result = self.check_single_pillar(
            yue_gan, yue_zhi, tiandi_pan, shichen, 
            shan_jia, xiang_shou, '月'
        )
        ri_result = self.check_single_pillar(
            ri_gan, ri_zhi, tiandi_pan, shichen, 
            shan_jia, xiang_shou, '日'
        )
        
        # 检查本山本向
        ben_shan_result = self.check_ben_shan_ben_xiang(
            mountain, shan_jia, xiang_shou, tiandi_pan, shichen,
            nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi
        )
        
        # 统计
        qualified_count = sum([
            nian_result['pillar_qualified'],
            yue_result['pillar_qualified'],
            ri_result['pillar_qualified']
        ])
        
        # 评分（按用户要求：禄马贵人到山或到向=70分）
        if not ri_result['pillar_qualified']:
            score = 50
            status = '平课（日柱禄马贵人未到山到向）'
        else:
            # 日柱禄马贵人到山到向 = 70分（基础分）
            score = 70
            status = '吉课（日柱禄马贵人到山到向）'
            
            # 年柱禄马贵人到山到向加分
            if nian_result['pillar_qualified']:
                score += 10
            
            # 月柱禄马贵人到山到向加分
            if yue_result['pillar_qualified']:
                score += 10
            
            if qualified_count >= 3:
                status = '上吉课（年月日禄马贵人皆到山到向）'
            elif qualified_count >= 2:
                status = '中吉课（两柱禄马贵人到山到向）'
        
        # 本山本向吉课加分
        if ben_shan_result['has_ben_shan_ji']:
            score = min(100, score + 10)
        
        return {
            'mountain': mountain,
            'shan_jia': shan_jia,
            'xiang_shou': xiang_shou,
            'shichen': shichen,
            'nian_result': nian_result,
            'yue_result': yue_result,
            'ri_result': ri_result,
            'ben_shan_result': ben_shan_result,
            'qualified_count': qualified_count,
            'score': score,
            'status': status
        }
    
    def print_analysis(self, result: Dict):
        """打印分析结果"""
        print("=" * 100)
        print("大六壬禄马贵人到山到向完整分析")
        print("=" * 100)
        print(f"\n坐山: {result['mountain']}")
        print(f"山家: {result['shan_jia']}")
        print(f"向首: {result['xiang_shou']}")
        print(f"时辰: {result['shichen']}")
        
        pillars = ['nian_result', 'yue_result', 'ri_result']
        pillar_names = ['年柱', '月柱', '日柱']
        
        for pillar_key, pillar_name in zip(pillars, pillar_names):
            pillar = result[pillar_key]
            print(f"\n{pillar_name}: {pillar['tian_gan']}{pillar['di_zhi']}")
            print(f"  禄神: {pillar['lu_zhi']} {'到山' if pillar['lu_to_shan'] else ''} {'到向' if pillar['lu_to_xiang'] else ''}")
            print(f"  驿马: {pillar['ma_zhi']} {'到山' if pillar['ma_to_shan'] else ''} {'到向' if pillar['ma_to_xiang'] else ''}")
            print(f"  贵人: {pillar['guiren_zhi']} {'到山' if pillar['guiren_to_shan'] else ''} {'到向' if pillar['guiren_to_xiang'] else ''}")
            print(f"  到山数: {pillar['shan_count']}")
            print(f"  到向数: {pillar['xiang_count']}")
            print(f"  合格: {'✅' if pillar['pillar_qualified'] else '❌'}")
        
        if result['ben_shan_result']['has_ben_shan_ji']:
            print(f"\n⭐ 本山本向吉课:")
            for bs_result in result['ben_shan_result']['results']:
                print(f"   - {bs_result['desc']}")
        
        print(f"\n📊 合格数: {result['qualified_count']}/3")
        print(f"🎯 评分: {result['score']}分")
        print(f"📋 评语: {result['status']}")
        print("\n" + "=" * 100)

    def check_sanchuan_luma_guiren(self, sanchuan: Dict, 
                                    ri_gan: str, ri_zhi: str,
                                    nian_gan: str = None, nian_zhi: str = None,
                                    yue_gan: str = None, yue_zhi: str = None,
                                    tiandi_pan: Dict = None, shichen: str = None) -> Dict:
        """
        检查三传中是否包含禄马贵人
        
        规则：三传组合中必须包含禄、马、贵人这三个关键神煞中的一个、两个或全部
        
        核心标准：
        1. 日柱禄马贵人必须发出三传（在三传中出现）
        2. 年月时柱禄马贵人发出三传为加分项
        
        参数:
            sanchuan: 三传信息 {'初传': str, '中传': str, '末传': str, '课体': str}
            ri_gan: 日干
            ri_zhi: 日支
            nian_gan: 年干（可选，用于年禄）
            nian_zhi: 年支（可选，用于年马）
            yue_gan: 月干（可选，用于月禄）
            yue_zhi: 月支（可选，用于月马）
            tiandi_pan: 天地盘（可选，用于贵人计算）
            shichen: 时辰（可选，用于贵人计算）
        
        返回:
            三传禄马贵人检查结果
        """
        chuan_list = [
            sanchuan.get('初传', ''),
            sanchuan.get('中传', ''),
            sanchuan.get('末传', '')
        ]
        
        ri_lu = self.get_lu_zhi(ri_gan)
        ri_ma = self.get_ma_zhi(ri_zhi)
        ri_guiren = self.get_guiren_zhi(ri_gan, tiandi_pan, shichen) if tiandi_pan and shichen else None
        
        nian_lu = self.get_lu_zhi(nian_gan) if nian_gan else None
        nian_ma = self.get_ma_zhi(nian_zhi) if nian_zhi else None
        nian_guiren = self.get_guiren_zhi(nian_gan, tiandi_pan, shichen) if nian_gan and tiandi_pan and shichen else None
        
        yue_lu = self.get_lu_zhi(yue_gan) if yue_gan else None
        yue_ma = self.get_ma_zhi(yue_zhi) if yue_zhi else None
        yue_guiren = self.get_guiren_zhi(yue_gan, tiandi_pan, shichen) if yue_gan and tiandi_pan and shichen else None
        
        all_lu = set(filter(None, [ri_lu, nian_lu, yue_lu]))
        all_ma = set(filter(None, [ri_ma, nian_ma, yue_ma]))
        all_guiren = set(filter(None, [ri_guiren, nian_guiren, yue_guiren]))
        
        lu_in_sanchuan = []
        ma_in_sanchuan = []
        guiren_in_sanchuan = []
        
        for i, chuan in enumerate(chuan_list):
            chuan_name = ['初传', '中传', '末传'][i]
            if chuan in all_lu:
                lu_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '禄神'})
            if chuan in all_ma:
                ma_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '驿马'})
            if chuan in all_guiren:
                guiren_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '贵人'})
        
        ri_lu_in_sanchuan = ri_lu in chuan_list if ri_lu else False
        ri_ma_in_sanchuan = ri_ma in chuan_list if ri_ma else False
        ri_guiren_in_sanchuan = ri_guiren in chuan_list if ri_guiren else False
        
        ri_luma_guiren_in_sanchuan = ri_lu_in_sanchuan or ri_ma_in_sanchuan or ri_guiren_in_sanchuan
        
        nian_lu_in_sanchuan = nian_lu in chuan_list if nian_lu else False
        nian_ma_in_sanchuan = nian_ma in chuan_list if nian_ma else False
        nian_guiren_in_sanchuan = nian_guiren in chuan_list if nian_guiren else False
        
        yue_lu_in_sanchuan = yue_lu in chuan_list if yue_lu else False
        yue_ma_in_sanchuan = yue_ma in chuan_list if yue_ma else False
        yue_guiren_in_sanchuan = yue_guiren in chuan_list if yue_guiren else False
        
        found_items = []
        found_count = 0
        
        if lu_in_sanchuan:
            found_count += 1
            found_items.extend(lu_in_sanchuan)
        if ma_in_sanchuan:
            found_count += 1
            found_items.extend(ma_in_sanchuan)
        if guiren_in_sanchuan:
            found_count += 1
            found_items.extend(guiren_in_sanchuan)
        
        has_luma_guiren = found_count >= 1
        
        # 三传评分（按用户要求：发出三传额外加分）
        sanchuan_score = 0
        
        # 日柱禄马贵人发出三传：每项+10分
        if ri_lu_in_sanchuan:
            sanchuan_score += 10
        if ri_ma_in_sanchuan:
            sanchuan_score += 10
        if ri_guiren_in_sanchuan:
            sanchuan_score += 10
        
        # 年柱禄马贵人发出三传：每项+5分
        if nian_lu_in_sanchuan:
            sanchuan_score += 5
        if nian_ma_in_sanchuan:
            sanchuan_score += 5
        if nian_guiren_in_sanchuan:
            sanchuan_score += 5
        
        # 月柱禄马贵人发出三传：每项+5分
        if yue_lu_in_sanchuan:
            sanchuan_score += 5
        if yue_ma_in_sanchuan:
            sanchuan_score += 5
        if yue_guiren_in_sanchuan:
            sanchuan_score += 5
        
        # 最高100分
        sanchuan_score = min(100, sanchuan_score)
        
        if sanchuan_score == 0:
            sanchuan_status = '三传无禄马贵人'
        elif sanchuan_score >= 30:
            sanchuan_status = '三传禄马贵人俱全'
        elif sanchuan_score >= 20:
            sanchuan_status = '三传有二吉'
        else:
            sanchuan_status = '三传有一吉'
        
        return {
            'sanchuan': sanchuan,
            'chuan_list': chuan_list,
            'ri_lu': ri_lu,
            'ri_ma': ri_ma,
            'ri_guiren': ri_guiren,
            'all_lu': list(all_lu),
            'all_ma': list(all_ma),
            'all_guiren': list(all_guiren),
            'lu_in_sanchuan': lu_in_sanchuan,
            'ma_in_sanchuan': ma_in_sanchuan,
            'guiren_in_sanchuan': guiren_in_sanchuan,
            'ri_lu_in_sanchuan': ri_lu_in_sanchuan,
            'ri_ma_in_sanchuan': ri_ma_in_sanchuan,
            'ri_guiren_in_sanchuan': ri_guiren_in_sanchuan,
            'ri_luma_guiren_in_sanchuan': ri_luma_guiren_in_sanchuan,
            'nian_lu_in_sanchuan': nian_lu_in_sanchuan,
            'nian_ma_in_sanchuan': nian_ma_in_sanchuan,
            'nian_guiren_in_sanchuan': nian_guiren_in_sanchuan,
            'yue_lu_in_sanchuan': yue_lu_in_sanchuan,
            'yue_ma_in_sanchuan': yue_ma_in_sanchuan,
            'yue_guiren_in_sanchuan': yue_guiren_in_sanchuan,
            'found_items': found_items,
            'found_count': found_count,
            'has_luma_guiren': has_luma_guiren,
            'sanchuan_score': sanchuan_score,
            'sanchuan_status': sanchuan_status
        }

    def analyze_full_with_sanchuan(self, mountain: str, shichen: str,
                                    nian_gan: str, nian_zhi: str,
                                    yue_gan: str, yue_zhi: str,
                                    ri_gan: str, ri_zhi: str,
                                    sanchuan: Dict = None,
                                    year: int = None, month: int = None, day: int = None) -> Dict:
        """
        完整分析（包含三传禄马贵人检查）
        
        核心标准 - 双重达标原则：
        日柱禄马贵人必须同时满足：
        1. 到山到向（禄/马/贵人临山或向）
        2. 发出三传（禄/马/贵人出现在三传中）
        
        判定规则：
        - 禄、马、贵人三者中，至少有一个同时满足两个条件（双重达标）
        - 年月柱禄马贵人发出三传为加分项
        
        参数:
            mountain: 坐山
            shichen: 时辰
            nian_gan: 年干
            nian_zhi: 年支
            yue_gan: 月干
            yue_zhi: 月支
            ri_gan: 日干
            ri_zhi: 日支
            sanchuan: 三传信息（可选）
            year: 年份（用于计算月将）
            month: 月份（用于计算月将）
            day: 日期（用于计算月将）
        
        返回:
            完整分析结果（包含三传检查和合格判定）
        """
        base_result = self.analyze_full(
            mountain, shichen,
            nian_gan, nian_zhi,
            yue_gan, yue_zhi,
            ri_gan, ri_zhi
        )
        
        ri_result = base_result.get('ri_result', {})
        shan_jia = base_result.get('shan_jia', '')
        xiang_shou = base_result.get('xiang_shou', '')
        
        ri_lu_zhi = ri_result.get('lu_zhi', '')
        ri_ma_zhi = ri_result.get('ma_zhi', '')
        ri_guiren_zhi = ri_result.get('guiren_zhi', '')
        
        ri_lu_to_shan = ri_result.get('lu_to_shan', False)
        ri_lu_to_xiang = ri_result.get('lu_to_xiang', False)
        ri_ma_to_shan = ri_result.get('ma_to_shan', False)
        ri_ma_to_xiang = ri_result.get('ma_to_xiang', False)
        ri_guiren_to_shan = ri_result.get('guiren_to_shan', False)
        ri_guiren_to_xiang = ri_result.get('guiren_to_xiang', False)
        
        if sanchuan:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = self.get_yuejiang(yue_zhi)
            tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
            sanchuan_result = self.check_sanchuan_luma_guiren(
                sanchuan, ri_gan, ri_zhi,
                nian_gan, nian_zhi,
                yue_gan, yue_zhi,
                tiandi_pan, shichen
            )
            base_result['sanchuan_result'] = sanchuan_result
            
            ri_lu_in_sanchuan = sanchuan_result.get('ri_lu_in_sanchuan', False)
            ri_ma_in_sanchuan = sanchuan_result.get('ri_ma_in_sanchuan', False)
            ri_guiren_in_sanchuan = sanchuan_result.get('ri_guiren_in_sanchuan', False)
            
            nian_lu_in_sanchuan = sanchuan_result.get('nian_lu_in_sanchuan', False)
            nian_ma_in_sanchuan = sanchuan_result.get('nian_ma_in_sanchuan', False)
            nian_guiren_in_sanchuan = sanchuan_result.get('nian_guiren_in_sanchuan', False)
            
            yue_lu_in_sanchuan = sanchuan_result.get('yue_lu_in_sanchuan', False)
            yue_ma_in_sanchuan = sanchuan_result.get('yue_ma_in_sanchuan', False)
            yue_guiren_in_sanchuan = sanchuan_result.get('yue_guiren_in_sanchuan', False)
            
            ri_lu_double_qualified = (ri_lu_to_shan or ri_lu_to_xiang) and ri_lu_in_sanchuan
            ri_ma_double_qualified = (ri_ma_to_shan or ri_ma_to_xiang) and ri_ma_in_sanchuan
            ri_guiren_double_qualified = (ri_guiren_to_shan or ri_guiren_to_xiang) and ri_guiren_in_sanchuan
            
            double_qualified_count = sum([ri_lu_double_qualified, ri_ma_double_qualified, ri_guiren_double_qualified])
            
            is_qualified = double_qualified_count >= 1
            
            nian_yue_bonus = sum([
                nian_lu_in_sanchuan, nian_ma_in_sanchuan, nian_guiren_in_sanchuan,
                yue_lu_in_sanchuan, yue_ma_in_sanchuan, yue_guiren_in_sanchuan
            ])
            
            double_qualified_items = []
            if ri_lu_double_qualified:
                double_qualified_items.append(f'禄神{ri_lu_zhi}')
            if ri_ma_double_qualified:
                double_qualified_items.append(f'驿马{ri_ma_zhi}')
            if ri_guiren_double_qualified:
                double_qualified_items.append(f'贵人{ri_guiren_zhi}')
            
            single_qualified_items = []
            if (ri_lu_to_shan or ri_lu_to_xiang) and not ri_lu_in_sanchuan:
                single_qualified_items.append(f'禄神{ri_lu_zhi}(到山到向但未发传)')
            if ri_lu_in_sanchuan and not (ri_lu_to_shan or ri_lu_to_xiang):
                single_qualified_items.append(f'禄神{ri_lu_zhi}(发传但未到山到向)')
            if (ri_ma_to_shan or ri_ma_to_xiang) and not ri_ma_in_sanchuan:
                single_qualified_items.append(f'驿马{ri_ma_zhi}(到山到向但未发传)')
            if ri_ma_in_sanchuan and not (ri_ma_to_shan or ri_ma_to_xiang):
                single_qualified_items.append(f'驿马{ri_ma_zhi}(发传但未到山到向)')
            if (ri_guiren_to_shan or ri_guiren_to_xiang) and not ri_guiren_in_sanchuan:
                single_qualified_items.append(f'贵人{ri_guiren_zhi}(到山到向但未发传)')
            if ri_guiren_in_sanchuan and not (ri_guiren_to_shan or ri_guiren_to_xiang):
                single_qualified_items.append(f'贵人{ri_guiren_zhi}(发传但未到山到向)')
            
            if double_qualified_count == 0:
                if single_qualified_items:
                    qualification_status = f'不合格：日柱禄马贵人均未双重达标（{"; ".join(single_qualified_items[:2])}）'
                else:
                    qualification_status = '不合格：日柱禄马贵人未到山到向且未发出三传'
                qualification_score = 0
            elif double_qualified_count == 3:
                qualification_status = f'上上吉：日柱禄马贵人三者皆双重达标（{", ".join(double_qualified_items)}）'
                qualification_score = 100
            elif double_qualified_count == 2:
                if nian_yue_bonus >= 2:
                    qualification_status = f'上吉：日柱两吉双重达标，年月柱亦发传'
                    qualification_score = 95
                else:
                    qualification_status = f'上吉：日柱两吉双重达标（{", ".join(double_qualified_items)}）'
                    qualification_score = 90
            else:
                if nian_yue_bonus >= 3:
                    qualification_status = f'中吉：日柱一吉双重达标（{double_qualified_items[0]}），年月柱多发传'
                    qualification_score = 85
                elif nian_yue_bonus >= 1:
                    qualification_status = f'中吉：日柱一吉双重达标（{double_qualified_items[0]}），年月柱部分发传'
                    qualification_score = 80
                else:
                    qualification_status = f'合格：日柱一吉双重达标（{double_qualified_items[0]}）'
                    qualification_score = 60
            
            daoshan_score = base_result['score']
            sanchuan_score = sanchuan_result['sanchuan_score']
            
            combined_score = int(daoshan_score * 0.3 + sanchuan_score * 0.3 + qualification_score * 0.4)
            base_result['combined_score'] = combined_score
            base_result['combined_status'] = qualification_status
            base_result['is_qualified'] = is_qualified
            base_result['qualification_status'] = qualification_status
            base_result['qualification_score'] = qualification_score
            base_result['ri_luma_guiren_in_sanchuan'] = ri_lu_in_sanchuan or ri_ma_in_sanchuan or ri_guiren_in_sanchuan
            base_result['double_qualified_count'] = double_qualified_count
            base_result['double_qualified_items'] = double_qualified_items
            base_result['single_qualified_items'] = single_qualified_items
            base_result['ri_double_qualified_detail'] = {
                'ri_lu_double_qualified': ri_lu_double_qualified,
                'ri_ma_double_qualified': ri_ma_double_qualified,
                'ri_guiren_double_qualified': ri_guiren_double_qualified,
                'ri_lu_to_shan_xiang': ri_lu_to_shan or ri_lu_to_xiang,
                'ri_lu_in_sanchuan': ri_lu_in_sanchuan,
                'ri_ma_to_shan_xiang': ri_ma_to_shan or ri_ma_to_xiang,
                'ri_ma_in_sanchuan': ri_ma_in_sanchuan,
                'ri_guiren_to_shan_xiang': ri_guiren_to_shan or ri_guiren_to_xiang,
                'ri_guiren_in_sanchuan': ri_guiren_in_sanchuan
            }
            base_result['ri_sanchuan_detail'] = {
                'ri_lu_in_sanchuan': ri_lu_in_sanchuan,
                'ri_ma_in_sanchuan': ri_ma_in_sanchuan,
                'ri_guiren_in_sanchuan': ri_guiren_in_sanchuan
            }
            base_result['nian_yue_sanchuan_detail'] = {
                'nian_lu_in_sanchuan': nian_lu_in_sanchuan,
                'nian_ma_in_sanchuan': nian_ma_in_sanchuan,
                'nian_guiren_in_sanchuan': nian_guiren_in_sanchuan,
                'yue_lu_in_sanchuan': yue_lu_in_sanchuan,
                'yue_ma_in_sanchuan': yue_ma_in_sanchuan,
                'yue_guiren_in_sanchuan': yue_guiren_in_sanchuan,
                'bonus_count': nian_yue_bonus
            }
        else:
            base_result['sanchuan_result'] = None
            base_result['combined_score'] = base_result['score']
            base_result['combined_status'] = base_result['status']
            base_result['is_qualified'] = False
            base_result['qualification_status'] = '无三传数据'
            base_result['qualification_score'] = 0
            base_result['double_qualified_count'] = 0
            base_result['double_qualified_items'] = []
        
        return base_result
