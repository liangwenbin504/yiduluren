#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六相六替完整系统（正确版）
基于《仪度六壬选日要诀》
包含生死辩（季节旺衰）

核心原理：
1. 水土同宫，长生在申
2. 吉星（元辰、武财）要坐六相地支
3. 凶星（贪官、破鬼）要坐六替地支
4. 结合季节旺衰（生死辩）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from typing import Dict, List, Tuple


class LiuXiangLiuTiCorrect:
    """
    正确的六相六替系统
    """
    
    def __init__(self):
        # 十天干化气五行
        self.tiangan_huaqi = {
            '甲': '土', '己': '土',
            '乙': '金', '庚': '金',
            '丙': '水', '辛': '水',
            '丁': '木', '壬': '木',
            '戊': '火', '癸': '火'
        }
        
        # 水土十二长生（水土同宫，长生在申）
        self.shuitou_changsheng = {
            '申': '长生', '酉': '沐浴', '戌': '冠带', '亥': '临官',
            '子': '帝旺', '丑': '衰', '寅': '病', '卯': '死',
            '辰': '墓', '巳': '绝', '午': '胎', '未': '养'
        }
        
        # 木的十二长生（长生在亥）
        self.mu_changsheng = {
            '亥': '长生', '子': '沐浴', '丑': '冠带', '寅': '临官',
            '卯': '帝旺', '辰': '衰', '巳': '病', '午': '死',
            '未': '墓', '申': '绝', '酉': '胎', '戌': '养'
        }
        
        # 金的十二长生（长生在巳）
        self.jin_changsheng = {
            '巳': '长生', '午': '沐浴', '未': '冠带', '申': '临官',
            '酉': '帝旺', '戌': '衰', '亥': '病', '子': '死',
            '丑': '墓', '寅': '绝', '卯': '胎', '辰': '养'
        }
        
        # 火的十二长生（长生在寅，火土同宫论德神禄神）
        self.huo_changsheng = {
            '寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官',
            '午': '帝旺', '未': '衰', '申': '病', '酉': '死',
            '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'
        }
        
        # 六相地支（吉）
        self.liuxiang_zhi = ['长生', '冠带', '临官', '帝旺', '胎', '养']
        
        # 六替地支（凶）
        self.liuti_zhi = ['沐浴', '衰', '病', '死', '墓', '绝']
        
        # 季节旺衰（水土）
        self.season_wangshuai = {
            '春': {'水': '休', '土': '死', '木': '旺', '火': '相', '金': '囚'},
            '夏': {'水': '囚', '土': '旺', '木': '死', '火': '相', '金': '休'},
            '秋': {'水': '相', '土': '休', '木': '囚', '火': '死', '金': '旺'},
            '冬': {'水': '旺', '土': '囚', '木': '相', '火': '休', '金': '死'}
        }
        
        # 月份对应季节
        self.month_season = {
            '寅': '春', '卯': '春', '辰': '春',
            '巳': '夏', '午': '夏', '未': '夏',
            '申': '秋', '酉': '秋', '戌': '秋',
            '亥': '冬', '子': '冬', '丑': '冬'
        }
    
    def get_huaqi(self, tiangan: str) -> str:
        """获取天干化气"""
        return self.tiangan_huaqi.get(tiangan, '土')
    
    def get_changsheng_state(self, wuxing: str, dizhi: str) -> str:
        """获取五行在地支的长生状态"""
        if wuxing in ['水', '土']:
            return self.shuitou_changsheng.get(dizhi, '未知')
        elif wuxing == '木':
            return self.mu_changsheng.get(dizhi, '未知')
        elif wuxing == '金':
            return self.jin_changsheng.get(dizhi, '未知')
        elif wuxing == '火':
            return self.huo_changsheng.get(dizhi, '未知')
        return '未知'
    
    def is_liuxiang(self, state: str) -> bool:
        """判断是否为六相"""
        return state in self.liuxiang_zhi
    
    def is_liuti(self, state: str) -> bool:
        """判断是否为六替"""
        return state in self.liuti_zhi
    
    def get_season(self, month_dizhi: str) -> str:
        """根据地支获取季节"""
        return self.month_season.get(month_dizhi, '未知')
    
    def get_wangshuai(self, wuxing: str, month_dizhi: str) -> str:
        """获取五行在当月的旺衰"""
        season = self.get_season(month_dizhi)
        return self.season_wangshuai.get(season, {}).get(wuxing, '未知')
    
    def analyze_pillar(self, ganzhi: str, shan_wuxing: str = '土') -> Dict:
        """
        分析单柱的六相六替
        
        Args:
            ganzhi: 干支（如'丙午'）
            shan_wuxing: 山家五行（壬山为土）
        
        Returns:
            分析结果字典
        """
        tiangan = ganzhi[0]
        dizhi = ganzhi[1]
        
        # 1. 天干化气
        huaqi = self.get_huaqi(tiangan)
        
        # 2. 确定六亲（以壬山土为例）
        liuqin = self._get_liuqin(huaqi, shan_wuxing)
        
        # 3. 查长生状态
        changsheng_state = self.get_changsheng_state(huaqi, dizhi)
        
        # 4. 判断六相六替
        is_liuxiang = self.is_liuxiang(changsheng_state)
        is_liuti = self.is_liuti(changsheng_state)
        
        # 5. 判断吉凶
        if liuqin in ['元辰', '武财']:
            # 吉星要坐六相
            jixiong = '吉' if is_liuxiang else '凶'
        elif liuqin in ['贪官', '破鬼']:
            # 凶星要坐六替
            jixiong = '吉' if is_liuti else '凶'
        else:  # 廉贞
            jixiong = '平'
        
        return {
            '干支': ganzhi,
            '天干': tiangan,
            '地支': dizhi,
            '化气': huaqi,
            '六亲': liuqin,
            '长生状态': changsheng_state,
            '六相/六替': '六相' if is_liuxiang else '六替',
            '吉凶': jixiong
        }
    
    def _get_liuqin(self, huaqi: str, shan_wuxing: str = '土') -> str:
        """
        根据化气和山家五行确定六亲
        
        壬山（土）：
        - 土：元辰（比旺）
        - 水：武财（我克）
        - 木：贪官（生我）
        - 火：廉贞（我生）
        - 金：破鬼（克我）
        """
        if huaqi == shan_wuxing:
            return '元辰'
        elif shan_wuxing == '土':
            if huaqi == '水':
                return '武财'
            elif huaqi == '木':
                return '贪官'
            elif huaqi == '火':
                return '廉贞'
            elif huaqi == '金':
                return '破鬼'
        return '未知'
    
    def analyze_sizhu(self, sizhu: Dict, shan_wuxing: str = '土') -> Dict:
        """
        分析四柱的六相六替
        
        Args:
            sizhu: 四柱字典
            shan_wuxing: 山家五行
        
        Returns:
            分析结果字典
        """
        result = {
            '四柱分析': {},
            '六相统计': 0,
            '六替统计': 0,
            '吉课数': 0,
            '凶课数': 0,
            '总分': 0,
            '平均分': 0,
            '综合评价': ''
        }
        
        # 评分标准
        score_map = {
            '吉': 90,
            '平': 70,
            '凶': 30
        }
        
        for pillar_name, ganzhi in sizhu.items():
            analysis = self.analyze_pillar(ganzhi, shan_wuxing)
            result['四柱分析'][pillar_name] = analysis
            
            if analysis['六相/六替'] == '六相':
                result['六相统计'] += 1
            else:
                result['六替统计'] += 1
            
            if analysis['吉凶'] == '吉':
                result['吉课数'] += 1
            elif analysis['吉凶'] == '凶':
                result['凶课数'] += 1
            
            # 计分
            pillar_score = score_map.get(analysis['吉凶'], 50)
            result['总分'] += pillar_score
        
        # 平均分
        result['平均分'] = result['总分'] / len(sizhu) if sizhu else 0
        
        # 综合评价
        if result['吉课数'] >= 3:
            result['综合评价'] = '上上大吉'
        elif result['吉课数'] >= 2:
            result['综合评价'] = '吉'
        elif result['吉课数'] >= 1:
            result['综合评价'] = '平'
        else:
            result['综合评价'] = '凶'
        
        return result


def test_correct_system():
    """测试正确的六相六替系统"""
    print('=' * 100)
    print('六相六替完整系统（正确版）')
    print('包含生死辩（季节旺衰）')
    print('=' * 100)
    
    system = LiuXiangLiuTiCorrect()
    
    # 测试 5 个日课
    test_cases = [
        {
            '排名': 1,
            '公历': '2026 年 4 月 22 日 申时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '壬辰',
                '日柱': '丙寅',
                '时柱': '丙申'
            }
        },
        {
            '排名': 2,
            '公历': '2026 年 3 月 31 日 未时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '辛卯',
                '日柱': '甲辰',
                '时柱': '辛未'
            }
        }
    ]
    
    for case in test_cases:
        print(f'\n{"="*100}')
        print(f'第{case["排名"]}名：{case["公历"]}')
        print(f'四柱：{case["sizhu"]["年柱"]} {case["sizhu"]["月柱"]} {case["sizhu"]["日柱"]} {case["sizhu"]["时柱"]}')
        print('='*100)
        
        result = system.analyze_sizhu(case['sizhu'], '土')
        
        print(f'\n【逐柱分析】')
        for pillar_name, analysis in result['四柱分析'].items():
            print(f'\n{pillar_name}: {analysis["干支"]}')
            print(f'  化气：{analysis["化气"]} → {analysis["六亲"]}')
            print(f'  长生状态：{analysis["长生状态"]} ({analysis["六相/六替"]})')
            print(f'  吉凶：{analysis["吉凶"]}')
        
        print(f'\n【综合统计】')
        print(f'  六相：{result["六相统计"]}个')
        print(f'  六替：{result["六替统计"]}个')
        print(f'  吉课：{result["吉课数"]}个')
        print(f'  凶课：{result["凶课数"]}个')
        print(f'  综合评价：{result["综合评价"]}')
    
    print('\n' + '='*100)
    print('测试完成')
    print('='*100)


if __name__ == '__main__':
    test_correct_system()
