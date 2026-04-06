#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬禄马贵人到山到向完整计算模块
依据传统大六壬理论，实现年月日时四柱禄马贵人到山到向的完整判定逻辑
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core_modules.engine.gui_ren_engine import GuiRenCalculator
from src.utils.dizhi_layout_generator import arrange_tiandi_pan


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
        self.gui_ren_calc = GuiRenCalculator()
    
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
        
        # 评分
        if not ri_result['pillar_qualified']:
            score = 50
            status = '平课（日柱禄马贵人未到山到向）'
        elif qualified_count >= 3:
            score = 100
            status = '上吉课（年月日禄马贵人皆到山到向）'
        elif qualified_count >= 2:
            score = 80
            status = '中吉课（两柱禄马贵人到山到向）'
        else:
            score = 60
            status = '吉课（仅日柱禄马贵人到山到向）'
        
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
        
        if found_count == 0:
            sanchuan_score = 0
            sanchuan_status = '三传无禄马贵人'
        elif found_count == 1:
            sanchuan_score = 30
            sanchuan_status = '三传有一吉（禄或马或贵人）'
        elif found_count == 2:
            sanchuan_score = 60
            sanchuan_status = '三传有二吉'
        else:
            sanchuan_score = 100
            sanchuan_status = '三传禄马贵人俱全'
        
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
