#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首择日 - 六相六替之法模块

依据《仪度六壬选日要诀》古籍整理
六相：指斗首五行与四柱化气的六种相生相克关系
六替：指番化五行的六种转化规律

核心理论：
1. 三元理论：天元（天干）、地元（地支）、人元（遁到山）
2. 番化诀：元元武化贪，官鬼子孙财
3. 六相：元辰、武财、贪官、廉贞、破鬼、鬼破
4. 六替：番化五行的循环转化
"""

from typing import Dict, List, Tuple


class LiuXiangLiuTiCalculator:
    """六相六替计算类"""
    
    def __init__(self):
        # 二十四山斗首五行
        self.DOUSHOU_WUXING = {
            '壬': '土', '子': '土', '巽': '土', '巳': '土', '辛': '土', '戌': '土',
            '癸': '火', '丑': '火', '丙': '火', '午': '火', '乾': '火', '亥': '火',
            '艮': '木', '寅': '木', '丁': '木', '未': '木',
            '坤': '水', '申': '水', '甲': '水', '卯': '水',
            '乙': '金', '辰': '金', '庚': '金', '酉': '金'
        }
        
        # 十天干化气五行
        self.TIANGAN_HUAQI = {
            '甲': '土', '己': '土',
            '乙': '金', '庚': '金',
            '丙': '水', '辛': '水',
            '丁': '木', '壬': '木',
            '戊': '火', '癸': '火'
        }
        
        # 六相（五星）定义
        self.LIUXIANG_NAMES = {
            '元辰': '同我者（比和）',
            '武财': '我克者（克出）',
            '贪官': '生我者（生入）',
            '廉贞': '我生者（生出）',
            '破鬼': '克我者（克入）'
        }
        
        # 六替番化规则（核心秘诀）
        # 元元武化贪，官鬼子孙财
        # 元辰化元辰，武财化贪官，贪官化破鬼，破鬼化廉子，廉子化武财
        self.LIUTI_FANHUA = {
            '元辰': '元辰',  # 元辰番化是元辰
            '武财': '贪官',  # 武财化贪官
            '贪官': '破鬼',  # 贪官化破鬼
            '破鬼': '廉贞',  # 破鬼化廉子
            '廉贞': '武财'   # 廉子化武财
        }
        
        # 五行生克关系
        self.WUXING_SHENG = {
            '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
        }
        self.WUXING_KE = {
            '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
        }
    
    def get_douhou_wuxing(self, shan: str) -> str:
        """获取坐山斗首五行"""
        return self.DOUSHOU_WUXING.get(shan, '土')
    
    def get_tiangan_huaqi(self, tiangan: str) -> str:
        """获取天干化气五行"""
        return self.TIANGAN_HUAQI.get(tiangan, '土')
    
    def determine_liuxiang(self, shan_wuxing: str, huagi_wuxing: str) -> str:
        """
        确定六相（五星）
        :param shan_wuxing: 山家斗首五行
        :param huagi_wuxing: 化气五行
        :return: 六相名称
        """
        if shan_wuxing == huagi_wuxing:
            return '元辰'  # 同我者
        elif self.WUXING_KE.get(shan_wuxing) == huagi_wuxing:
            return '武财'  # 我克者
        elif self.WUXING_SHENG.get(huagi_wuxing) == shan_wuxing:
            return '贪官'  # 生我者
        elif self.WUXING_SHENG.get(shan_wuxing) == huagi_wuxing:
            return '廉贞'  # 我生者
        else:  # 克我者
            return '破鬼'
    
    def calculate_fanhua_wuxing(self, star: str, base_wuxing: str) -> str:
        """
        计算番化五行（六替之法）
        :param star: 星名（元辰、武财等）
        :param base_wuxing: 基础五行
        :return: 番化后的五行
        """
        # 番化诀：元元武化贪，官鬼子孙财
        fanhua_map = {
            ('元辰', '土'): '土',  # 元辰化元辰（土）
            ('元辰', '火'): '火',  # 元辰化元辰（火）
            ('元辰', '木'): '木',  # 元辰化元辰（木）
            ('元辰', '水'): '水',  # 元辰化元辰（水）
            ('元辰', '金'): '金',  # 元辰化元辰（金）
            
            ('武财', '土'): '木',  # 武财化贪官（木克土）
            ('武财', '火'): '金',  # 武财化贪官（金被火克）
            ('武财', '木'): '土',  # 武财化贪官（土被木克）
            ('武财', '水'): '火',  # 武财化贪官（火被水克）
            ('武财', '金'): '水',  # 武财化贪官（水被金生）
            
            ('贪官', '土'): '金',  # 贪官化破鬼（金）
            ('贪官', '火'): '水',  # 贪官化破鬼（水）
            ('贪官', '木'): '火',  # 贪官化破鬼（火）
            ('贪官', '水'): '木',  # 贪官化破鬼（木）
            ('贪官', '金'): '土',  # 贪官化破鬼（土）
            
            ('破鬼', '土'): '水',  # 破鬼化廉贞（水）
            ('破鬼', '火'): '金',  # 破鬼化廉贞（金）
            ('破鬼', '木'): '火',  # 破鬼化廉贞（火）
            ('破鬼', '水'): '土',  # 破鬼化廉贞（土）
            ('破鬼', '金'): '木',  # 破鬼化廉贞（木）
            
            ('廉贞', '土'): '木',  # 廉贞化武财（木克土）
            ('廉贞', '火'): '金',  # 廉贞化武财（金）
            ('廉贞', '木'): '土',  # 廉贞化武财（土）
            ('廉贞', '水'): '火',  # 廉贞化武财（火）
            ('廉贞', '金'): '水',  # 廉贞化武财（水）
        }
        
        return fanhua_map.get((star, base_wuxing), base_wuxing)
    
    def analyze_sizhu_liuxiang(self, shan: str, sizhu: Dict) -> Dict:
        """
        分析四柱六相配置
        :param shan: 坐山
        :param sizhu: 四柱信息（包含年柱、月柱、日柱、时柱）
        :return: 六相分析结果
        """
        shan_wuxing = self.get_douhou_wuxing(shan)
        
        result = {
            '山家五行': shan_wuxing,
            '四柱六相': {},
            '四柱番化': {},
            '六相统计': {},
            '三元分析': {}
        }
        
        # 分析每一柱
        for zhuname, ganzhi in sizhu.items():
            if len(ganzhi) >= 2:
                tiangan = ganzhi[0]
                dizhi = ganzhi[1]
                
                # 获取天干化气
                huagi = self.get_tiangan_huaqi(tiangan)
                
                # 确定六相
                liuxiang = self.determine_liuxiang(shan_wuxing, huagi)
                
                # 计算番化五行
                fanhua = self.calculate_fanhua_wuxing(liuxiang, shan_wuxing)
                
                result['四柱六相'][zhuname] = {
                    '干支': ganzhi,
                    '天干': tiangan,
                    '化气': huagi,
                    '六相': liuxiang,
                    '番化': fanhua
                }
                
                result['四柱番化'][zhuname] = fanhua
                
                # 统计六相出现次数
                result['六相统计'][liuxiang] = result['六相统计'].get(liuxiang, 0) + 1
        
        # 三元分析
        result['三元分析'] = self._analyze_sanyuan(shan, sizhu, result['四柱六相'])
        
        return result
    
    def _analyze_sanyuan(self, shan: str, sizhu: Dict, liuxiang_result: Dict) -> Dict:
        """
        分析三元（天元、地元、人元）
        """
        shan_wuxing = self.get_douhou_wuxing(shan)
        
        # 天元：四柱天干化气
        tianyuan = []
        for zhuname, ganzhi in sizhu.items():
            if len(ganzhi) >= 1:
                tiangan = ganzhi[0]
                huagi = self.get_tiangan_huaqi(tiangan)
                tianyuan.append(f"{tiangan}化{huagi}")
        
        # 地元：四柱地支
        diyuan = []
        for zhuname, ganzhi in sizhu.items():
            if len(ganzhi) >= 2:
                dizhi = ganzhi[1]
                diyuan.append(dizhi)
        
        # 人元：遁到山（以山家五行为准）
        renyuan = shan_wuxing
        
        return {
            '天元': tianyuan,
            '地元': diyuan,
            '人元': renyuan,
            '说明': '天元为明用，地元为暗用，人元为山家根本'
        }
    
    def judge_kege_jixiong(self, liuxiang_result: Dict) -> Tuple[str, int, List[str]]:
        """
        判断课格吉凶
        :param liuxiang_result: 六相分析结果
        :return: (吉凶等级，评分，断语列表)
        """
        liuxiang_tongji = liuxiang_result['六相统计']
        duanyu = []
        score = 50  # 基础分
        jixiong = '平'
        
        # 元辰分析
        yuanchen_count = liuxiang_tongji.get('元辰', 0)
        if yuanchen_count >= 3:
            duanyu.append('三元辰格，元辰会一家，上吉')
            score += 30
        elif yuanchen_count >= 2:
            duanyu.append('二元辰，元辰旺相，吉')
            score += 20
        elif yuanchen_count == 1:
            duanyu.append('一元辰，平稳')
            score += 10
        
        # 武财分析
        wucai_count = liuxiang_tongji.get('武财', 0)
        if wucai_count >= 3:
            duanyu.append('三武格，武财会一家，财源广进，上吉')
            score += 35
        elif wucai_count >= 2:
            duanyu.append('双武生元，吉')
            score += 25
        elif wucai_count == 1:
            duanyu.append('武财一位，小吉')
            score += 15
        
        # 贪官分析
        tanlang_count = liuxiang_tongji.get('贪官', 0)
        if tanlang_count >= 3:
            duanyu.append('三重贪官克元辰，大凶')
            score -= 40
        elif tanlang_count >= 2:
            duanyu.append('贪官重见，凶')
            score -= 20
        elif tanlang_count == 1:
            duanyu.append('贪官一位，需制伏')
            score -= 5
        
        # 廉贞分析
        lianzhen_count = liuxiang_tongji.get('廉贞', 0)
        if lianzhen_count >= 3:
            duanyu.append('廉子重见，伤克子孙，大凶')
            score -= 35
        elif lianzhen_count == 2:
            duanyu.append('廉子两位，人丁稀矣')
            score -= 15
        elif lianzhen_count == 1:
            # 元辰旺时见廉贞为吉
            if yuanchen_count >= 2:
                duanyu.append('元辰旺见一位廉子，大旺人丁，吉')
                score += 20
            else:
                duanyu.append('廉子一位，平')
                score += 5
        
        # 破鬼分析
        pojun_count = liuxiang_tongji.get('破鬼', 0)
        if pojun_count >= 3:
            duanyu.append('破鬼重见，大凶')
            score -= 40
        elif pojun_count >= 2:
            duanyu.append('破鬼重见，凶')
            score -= 25
        elif pojun_count == 1:
            # 武财夹克破鬼为吉（武财关鬼格）
            if wucai_count >= 2:
                duanyu.append('武财关鬼格，可用')
                score += 15
            else:
                duanyu.append('破鬼一位，不宜')
                score -= 10
        
        # 确定吉凶等级
        if score >= 90:
            jixiong = '上上大吉'
        elif score >= 80:
            jixiong = '上吉'
        elif score >= 70:
            jixiong = '中吉'
        elif score >= 60:
            jixiong = '小吉'
        elif score >= 50:
            jixiong = '平'
        elif score >= 40:
            jixiong = '小凶'
        elif score >= 30:
            jixiong = '中凶'
        elif score >= 20:
            jixiong = '大凶'
        else:
            jixiong = '上凶'
        
        return jixiong, min(100, max(0, score)), duanyu


def test_liuxiang_liuti():
    """测试六相六替功能"""
    calculator = LiuXiangLiuTiCalculator()
    
    print('=' * 80)
    print('斗首择日 - 六相六替之法测试')
    print('=' * 80)
    
    # 测试案例：2026 年 3 月 31 日未时 壬山
    shan = '壬'
    sizhu = {
        '年柱': '丙午',
        '月柱': '辛卯',
        '日柱': '甲辰',
        '时柱': '辛未'
    }
    
    print(f'\n坐山：{shan}山')
    print(f'四柱：{sizhu["年柱"]} {sizhu["月柱"]} {sizhu["日柱"]} {sizhu["时柱"]}')
    
    # 分析六相
    result = calculator.analyze_sizhu_liuxiang(shan, sizhu)
    
    print(f'\n【山家五行】{result["山家五行"]}')
    
    print(f'\n【四柱六相分析】')
    for zhuname, data in result['四柱六相'].items():
        print(f'  {zhuname}: {data["干支"]} - 天干{data["天干"]}化{data["化气"]} - {data["六相"]} - 番化{data["番化"]}')
    
    print(f'\n【六相统计】')
    for liuxiang, count in result['六相统计'].items():
        print(f'  {liuxiang}: {count}重')
    
    print(f'\n【三元分析】')
    sanyuan = result['三元分析']
    print(f'  天元：{", ".join(sanyuan["天元"])}')
    print(f'  地元：{", ".join(sanyuan["地元"])}')
    print(f'  人元：{sanyuan["人元"]}')
    print(f'  说明：{sanyuan["说明"]}')
    
    # 判断吉凶
    jixiong, score, duanyu = calculator.judge_kege_jixiong(result)
    
    print(f'\n【课格吉凶】{jixiong} ({score}分)')
    print(f'【断语】')
    for d in duanyu:
        print(f'  - {d}')
    
    print('\n' + '=' * 80)


if __name__ == '__main__':
    test_liuxiang_liuti()
