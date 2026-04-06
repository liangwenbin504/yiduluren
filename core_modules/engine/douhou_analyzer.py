#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 模块 2：炉传斗首课格分析模块

功能：
1. 基于坐山信息（以炉传斗首理论为依据）生成标准斗首课格
2. 严格参照《斗首择日秘本》中规定的课格标准与方法
3. 根据内置评分规则精确计算吉凶分值（0-100 分）
4. 提供课格生成过程的详细日志记录
"""

from typing import Dict, List
from datetime import datetime
from liuxiang_liuti_system import LiuXiangLiuTiCalculator


class DouhouKegeAnalyzer:
    """炉传斗首课格分析器"""
    
    DOUSHOU_WUXING = {
        '壬': '土', '子': '土', '巽': '土', '巳': '土', '辛': '土', '戌': '土',
        '癸': '火', '丑': '火', '丙': '火', '午': '火', '乾': '火', '亥': '火',
        '艮': '木', '寅': '木', '丁': '木', '未': '木',
        '甲': '水', '卯': '水', '坤': '水', '申': '水',
        '乙': '金', '辰': '金', '庚': '金', '酉': '金'
    }
    
    TIANGAN_HUAQI = {
        '甲': '土', '己': '土',
        '乙': '金', '庚': '金',
        '丙': '水', '辛': '水',
        '丁': '木', '壬': '木',
        '戊': '火', '癸': '火'
    }
    
    LIUQIN_MAP = {
        ('土', '土'): '元辰', ('土', '金'): '廉贞', ('土', '水'): '武财',
        ('土', '木'): '破鬼', ('土', '火'): '贪官',
        
        ('金', '金'): '元辰', ('金', '水'): '廉贞', ('金', '木'): '武财',
        ('金', '火'): '破鬼', ('金', '土'): '贪官',
        
        ('水', '水'): '元辰', ('水', '木'): '廉贞', ('水', '火'): '武财',
        ('水', '土'): '破鬼', ('水', '金'): '贪官',
        
        ('木', '木'): '元辰', ('木', '火'): '廉贞', ('木', '土'): '武财',
        ('木', '金'): '破鬼', ('木', '水'): '贪官',
        
        ('火', '火'): '元辰', ('火', '土'): '廉贞', ('火', '金'): '武财',
        ('火', '水'): '破鬼', ('火', '木'): '贪官'
    }
    
    FANHUA_WUXING = {
        '土山': {'甲己': '土', '乙庚': '水', '丙辛': '火', '丁壬': '金', '戊癸': '木'},
        '火山': {'甲己': '金', '乙庚': '木', '丙辛': '土', '丁壬': '水', '戊癸': '火'},
        '木山': {'甲己': '水', '乙庚': '火', '丙辛': '金', '丁壬': '木', '戊癸': '土'},
        '水山': {'甲己': '木', '乙庚': '土', '丙辛': '水', '丁壬': '火', '戊癸': '金'},
        '金山': {'甲己': '火', '乙庚': '金', '丙辛': '木', '丁壬': '土', '戊癸': '水'}
    }
    
    KEGE_SCORES = {
        '元辰': {
            'base_score': 85,
            'wang_score': 95,
            'shuai_score': 60,
            'ru_mu_score': 30,
        },
        '武财': {
            'base_score': 90,
            'wang_score': 95,
            'shuai_score': 65,
        },
        '贪官': {
            'base_score': 35,
            'with_tongguan': 70,
            'without_tongguan': 20,
        },
        '廉贞': {
            'base_score': 60,
            'with_wang_yuan': 85,
            'with_shuai_yuan': 30,
            'multiple': 40,
        },
        '破鬼': {
            'base_score': 25,
            'with_zhi': 55,
            'without_zhi': 15,
            'yue_zhu': 50,
        }
    }
    
    WU_XING_WANG_SHUAI = {
        '木': {'长生': '亥', '沐浴': '子', '冠带': '丑', '临官': '寅', '帝旺': '卯',
              '衰': '辰', '病': '巳', '死': '午', '墓': '未', '绝': '申', '胎': '酉', '养': '戌'},
        '火': {'长生': '寅', '沐浴': '卯', '冠带': '辰', '临官': '巳', '帝旺': '午',
              '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑'},
        '土': {'长生': '寅', '沐浴': '卯', '冠带': '辰', '临官': '巳', '帝旺': '午',
              '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑'},
        '金': {'长生': '巳', '沐浴': '午', '冠带': '未', '临官': '申', '帝旺': '酉',
              '衰': '戌', '病': '亥', '死': '子', '墓': '丑', '绝': '寅', '胎': '卯', '养': '辰'},
        '水': {'长生': '申', '沐浴': '酉', '冠带': '戌', '临官': '亥', '帝旺': '子',
              '衰': '丑', '病': '寅', '死': '卯', '墓': '辰', '绝': '巳', '胎': '午', '养': '未'}
    }
    
    def __init__(self):
        self.logs = []
        self.liuxiang_calculator = LiuXiangLiuTiCalculator()
    
    def log(self, message: str):
        self.logs.append(message)
    
    def get_shan_jia_wuxing(self, shan: str) -> str:
        return self.DOUSHOU_WUXING.get(shan, '')
    
    def get_tiangan_huaqi(self, tiangan: str) -> str:
        return self.TIANGAN_HUAQI.get(tiangan, '')
    
    def get_liuqin(self, shan_wuxing: str, huaqi_wuxing: str) -> str:
        return self.LIUQIN_MAP.get((shan_wuxing, huaqi_wuxing), '')
    
    def analyze_kege(self, shan: str, sizhu: Dict) -> Dict:
        self.logs = []
        self.log(f"开始分析坐山：{shan}")
        
        shan_wuxing = self.get_shan_jia_wuxing(shan)
        if not shan_wuxing:
            return {'error': f'未知的坐山：{shan}'}
        
        self.log(f"山家五行：{shan_wuxing}")
        
        kege_result = {
            '坐山': shan,
            '山家五行': shan_wuxing,
            '四柱分析': {},
            '六相六替分析': {},
            '课格格局': [],
            '综合评分': 0,
            '吉凶断语': [],
            '日志': []
        }
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        star_counts = {'元辰': 0, '武财': 0, '贪官': 0, '廉贞': 0, '破鬼': 0}
        
        for pillar in pillars:
            ganzhi = sizhu.get(pillar, '')
            if not ganzhi or len(ganzhi) < 2:
                continue
            
            tiangan = ganzhi[0]
            dizhi = ganzhi[1]
            
            huaqi = self.get_tiangan_huaqi(tiangan)
            star = self.get_liuqin(shan_wuxing, huaqi)
            
            kege_result['四柱分析'][pillar] = {
                '干支': ganzhi,
                '天干': tiangan,
                '地支': dizhi,
                '化气五行': huaqi,
                '斗首星曜': star
            }
            
            if star in star_counts:
                star_counts[star] += 1
            
            self.log(f"{pillar}: {ganzhi}, 天干化气={huaqi}, 星曜={star}")
        
        kege_result['六相六替分析'] = self.liuxiang_calculator.analyze_sizhu_liuxiang(shan, sizhu)
        
        liuxiang_analysis = kege_result['六相六替分析']
        star_counts = liuxiang_analysis.get('六相统计', {})
        default_star_counts = {'元辰': 0, '武财': 0, '贪官': 0, '廉贞': 0, '破鬼': 0}
        for key in default_star_counts:
            if key not in star_counts:
                star_counts[key] = default_star_counts[key]
        kege_result['课格格局'] = self._judge_kege_pattern(star_counts, shan_wuxing, sizhu)
        
        kege_result['综合评分'] = self._calculate_score(kege_result['课格格局'], star_counts, sizhu, shan, liuxiang_analysis)
        
        kege_result['吉凶断语'] = self._generate_duanyu(kege_result['课格格局'], kege_result['综合评分'])
        
        kege_result['吉凶等级'] = self.get_score_description(kege_result['综合评分'])
        
        kege_result['日志'] = self.logs.copy()
        
        return kege_result
    
    def _judge_kege_pattern(self, star_counts: Dict, shan_wuxing: str, sizhu: Dict) -> List[Dict]:
        patterns = []
        
        if star_counts['元辰'] >= 3:
            patterns.append({
                '格局名称': '三元辰格',
                '描述': '三柱以上元辰，元辰会一家',
                '吉凶': '吉',
                '条件': f"元辰出现{star_counts['元辰']}次"
            })
        
        if star_counts['武财'] >= 3:
            patterns.append({
                '格局名称': '三武格',
                '描述': '三柱以上武财，武财会一家',
                '吉凶': '吉',
                '条件': f"武财出现{star_counts['武财']}次"
            })
        
        if star_counts['元辰'] >= 2:
            patterns.append({
                '格局名称': '元辰旺相',
                '描述': '元辰得令旺相',
                '吉凶': '吉',
                '条件': '元辰两现以上'
            })
        
        if star_counts['武财'] >= 2 and star_counts['元辰'] >= 1:
            patterns.append({
                '格局名称': '武财生元格',
                '描述': '武财生山家及元辰',
                '吉凶': '吉',
                '条件': '武财两现，元辰一见'
            })
        
        if star_counts['贪官'] >= 2 and star_counts['元辰'] >= 1:
            patterns.append({
                '格局名称': '贪官克元格',
                '描述': '贪官克山头元辰',
                '吉凶': '凶',
                '条件': f"贪官{star_counts['贪官']}次，元辰{star_counts['元辰']}次"
            })
        
        if star_counts['破鬼'] >= 2:
            patterns.append({
                '格局名称': '破鬼泄气格',
                '描述': '破鬼重见泄元气',
                '吉凶': '凶',
                '条件': f"破鬼出现{star_counts['破鬼']}次"
            })
        
        if star_counts['廉贞'] >= 2 and star_counts['元辰'] <= 1:
            patterns.append({
                '格局名称': '廉子伤克格',
                '描述': '廉子重见伤克子孙',
                '吉凶': '凶',
                '条件': f"廉贞{star_counts['廉贞']}次，元辰{star_counts['元辰']}次"
            })
        
        if star_counts['破鬼'] == 1 and star_counts['武财'] >= 2:
            patterns.append({
                '格局名称': '武财关鬼格',
                '描述': '年日为武财夹克鬼破',
                '吉凶': '吉',
                '条件': '破鬼一见，武财两见以上'
            })
        
        return patterns
    
    def _calculate_score(self, patterns: List[Dict], star_counts: Dict, sizhu: Dict, shan: str, liuxiang_analysis: Dict) -> int:
        jixiong, score, duanyu = self.liuxiang_calculator.judge_kege_jixiong(liuxiang_analysis)
        
        sizhu_liuxiang = liuxiang_analysis.get('四柱六相', {})
        yuezhu_info = sizhu_liuxiang.get('月柱', {})
        yuezhu_star = yuezhu_info.get('六相', '')
        
        if yuezhu_star in ['贪官', '破鬼']:
            has_lian_zhen = star_counts.get('廉贞', 0) > 0
            has_wucai = star_counts.get('武财', 0) >= 2
            if not has_lian_zhen and not has_wucai:
                score -= 10
        
        for pattern in patterns:
            if pattern['吉凶'] == '吉':
                if '三元辰' in pattern['格局名称']:
                    score += 5
                elif '三武格' in pattern['格局名称']:
                    score += 5
                elif '武财生元' in pattern['格局名称']:
                    score += 5
            else:
                if '贪官克元' in pattern['格局名称']:
                    score -= 5
                elif '破鬼泄气' in pattern['格局名称']:
                    score -= 5
                elif '廉子伤克' in pattern['格局名称']:
                    score -= 5
        
        final_score = max(0, min(100, score))
        
        return final_score
    
    def _generate_duanyu(self, patterns: List[Dict], score: int) -> List[str]:
        duanyu = []
        
        if score >= 90:
            duanyu.append("上上大吉，百事可为")
        elif score >= 80:
            duanyu.append("上吉之课，大利")
        elif score >= 70:
            duanyu.append("中吉之课，可用")
        elif score >= 60:
            duanyu.append("小吉之课，慎用")
        elif score >= 50:
            duanyu.append("吉凶参半，斟酌用之")
        elif score >= 40:
            duanyu.append("小凶之课，不宜")
        elif score >= 30:
            duanyu.append("中凶之课，忌用")
        elif score >= 20:
            duanyu.append("大凶之课，不可用")
        else:
            duanyu.append("上凶之课，大忌")
        
        for pattern in patterns:
            if '三元辰' in pattern['格局名称']:
                duanyu.append("三元辰格，家业兴隆，子孙昌盛")
            elif '三武格' in pattern['格局名称']:
                duanyu.append("三武格，财源广进，利市三倍")
            elif '贪官克元' in pattern['格局名称']:
                duanyu.append("贪官克元，家道中落，人丁不旺")
            elif '破鬼泄气' in pattern['格局名称']:
                duanyu.append("破鬼泄气，精气耗损，诸事不利")
            elif '廉子伤克' in pattern['格局名称']:
                duanyu.append("廉子重见，伤克子孙，人丁稀少")
        
        return duanyu
    
    def get_score_description(self, score: int) -> str:
        if score >= 90:
            return "上上大吉"
        elif score >= 80:
            return "上吉"
        elif score >= 70:
            return "中吉"
        elif score >= 60:
            return "小吉"
        elif score >= 50:
            return "吉凶参半"
        elif score >= 40:
            return "小凶"
        elif score >= 30:
            return "中凶"
        elif score >= 20:
            return "大凶"
        else:
            return "上凶"


def test_douhou_analyzer():
    print("=" * 70)
    print("炉传斗首课格分析模块测试")
    print("=" * 70)
    
    analyzer = DouhouKegeAnalyzer()
    
    print("\n【测试 1】壬山用事")
    print("四柱：丙午年 辛丑月 壬子日 庚子时")
    sizhu = {
        '年柱': '丙午',
        '月柱': '辛丑',
        '日柱': '壬子',
        '时柱': '庚子'
    }
    result = analyzer.analyze_kege('壬', sizhu)
    
    print(f"\n山家五行：{result['山家五行']}")
    print("\n四柱分析:")
    for pillar, info in result['四柱分析'].items():
        print(f"  {pillar}: {info['干支']}, 化气={info['化气五行']}, 星曜={info['斗首星曜']}")
    
    print("\n课格格局:")
    for pattern in result['课格格局']:
        print(f"  - {pattern['格局名称']} ({pattern['吉凶']}): {pattern['描述']}")
    
    print(f"\n综合评分：{result['综合评分']}分 ({analyzer.get_score_description(result['综合评分'])})")
    
    print("\n吉凶断语:")
    for duanyu in result['吉凶断语']:
        print(f"  - {duanyu}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_douhou_analyzer()
