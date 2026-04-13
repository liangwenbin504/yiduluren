#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六相六替完整系统（正确版）
基于《仪度六壬选日要诀》
包含真假生死辨

核心原理：
1. 水土同宫，长生在申
2. 吉星（元辰、武财）要坐六相地支
3. 凶星（贪官、破鬼）要坐六替地支
4. 真假生死辨：月令气势决定化气五行的真假
   - 月令生助化气 → 真生（即使六替也有气可用）
   - 月令克泄化气 → 真死（即使六相也无气不可用）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from typing import Dict, List, Tuple


class LiuXiangLiuTiCorrect:
    """
    正确的六相六替系统（包含真假生死辨）
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

        # 月令地支的五行属性
        self.month_zhi_wuxing = {
            '寅': '木', '卯': '木',
            '巳': '火', '午': '火',
            '申': '金', '酉': '金',
            '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土'
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

        # 火的十二长生（长生在寅）
        self.huo_changsheng = {
            '寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官',
            '午': '帝旺', '未': '衰', '申': '病', '酉': '死',
            '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'
        }

        # 六相地支（吉位）
        self.liuxiang_zhi = ['长生', '冠带', '临官', '帝旺', '胎', '养']

        # 六替地支（凶位）
        self.liuti_zhi = ['沐浴', '衰', '病', '死', '墓', '绝']

        # 月份对应季节
        self.month_season = {
            '寅': '春', '卯': '春', '辰': '春',
            '巳': '夏', '午': '夏', '未': '夏',
            '申': '秋', '酉': '秋', '戌': '秋',
            '亥': '冬', '子': '冬', '丑': '冬'
        }

        # 五行生克
        self.wuxing_sheng = {
            '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
        }
        self.wuxing_ke = {
            '木': '土', '火': '金', '土': '水', '金': '木', '水': '火'
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

    def get_month_zhi_wuxing(self, month_dizhi: str) -> str:
        """获取月令地支的五行属性"""
        return self.month_zhi_wuxing.get(month_dizhi, '土')

    def judge_zhenjia(self, huaqi: str, month_dizhi: str) -> Dict:
        """
        判断真假生死（月柱专用）

        核心：月令气势决定化气五行的真假
        - 月令生助化气 → 真生（化气有气）
        - 月令克泄化气 → 真死（化气无气）

        Returns:
            {
                '真假': '真生'/'真死'/'假生'/'假死',
                '有无气': '有气'/'无气',
                '可用性': '可用'/'不可用'/'平日',
                '原因': str
            }
        """
        month_wuxing = self.get_month_zhi_wuxing(month_dizhi)
        season = self.month_season.get(month_dizhi, '')

        result = {
            '真假': '',
            '有无气': '',
            '可用性': '',
            '原因': '',
            '月令五行': month_wuxing,
            '季节': season
        }

        # 判断月令与化气的生克关系
        # 1. 月令生化气：月令的五行生助化气 → 有气（真生）
        # 2. 月令克化气：月令的五行克化气 → 无气（真死）
        # 3. 化气生月令：化气生月令 → 泄气 → 无气（真死）
        # 4. 化气克月令：化气克月令 → 有气（假生）
        # 5. 月令化气同气：都旺 → 有气（真生）

        if self.wuxing_sheng.get(month_wuxing) == huaqi:
            # 月令生助化气
            result['真假'] = '真生'
            result['有无气'] = '有气'
            result['可用性'] = '可用'
            result['原因'] = f'{month_wuxing}生{huaqi}，化气得令'
        elif self.wuxing_ke.get(month_wuxing) == huaqi:
            # 月令克化气
            result['真假'] = '真死'
            result['有无气'] = '无气'
            result['可用性'] = '不可用'
            result['原因'] = f'{month_wuxing}克{huaqi}，化气受克'
        elif huaqi == month_wuxing:
            # 化气与月令相同（当令）
            result['真假'] = '真生'
            result['有无气'] = '有气'
            result['可用性'] = '可用'
            result['原因'] = f'{huaqi}与月令同旺'
        elif self.wuxing_sheng.get(huaqi) == month_wuxing:
            # 化气生月令（泄气）
            result['真假'] = '真死'
            result['有无气'] = '无气'
            result['可用性'] = '不可用'
            result['原因'] = f'{huaqi}生月令{month_wuxing}，化气泄气'
        elif self.wuxing_ke.get(huaqi) == month_wuxing:
            # 化气克月令
            result['真假'] = '假生'
            result['有无气'] = '有气'
            result['可用性'] = '平日'
            result['原因'] = f'{huaqi}克月令{month_wuxing}'
        else:
            # 其他情况
            result['真假'] = '假生'
            result['有无气'] = '有气'
            result['可用性'] = '平日'
            result['原因'] = f'{huaqi}与月令{month_wuxing}相帮'

        return result

    def analyze_pillar(self, ganzhi: str, shan_wuxing: str = '土', is_month_pillar: bool = False, month_dizhi: str = None) -> Dict:
        """
        分析单柱的六相六替（包含真假生死辨）

        Args:
            ganzhi: 干支（如'丙午'）
            shan_wuxing: 山家五行（壬山为土）
            is_month_pillar: 是否为月柱（只有月柱才论真假生死辨）
            month_dizhi: 月柱地支（仅月柱时需要）

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
        liuxiang_type = '六相' if is_liuxiang else '六替'

        # 5. 真假生死辨（仅月柱）
        if is_month_pillar and month_dizhi:
            zhenjia = self.judge_zhenjia(huaqi, month_dizhi)
        else:
            zhenjia = None

        # 6. 判断吉凶（考虑真假）
        jixiong, jixiong_reason = self._judge_jixiong(
            liuqin, huaqi, is_liuxiang, is_liuti, zhenjia, changsheng_state
        )

        result = {
            '干支': ganzhi,
            '天干': tiangan,
            '地支': dizhi,
            '化气': huaqi,
            '六亲': liuqin,
            '长生状态': changsheng_state,
            '六相/六替': liuxiang_type,
            '吉凶': jixiong,
            '吉凶原因': jixiong_reason
        }

        if zhenjia:
            result['真假生死辨'] = zhenjia
            result['季节'] = zhenjia.get('季节', '')

        return result

    def _judge_jixiong(self, liuqin: str, huaqi: str, is_liuxiang: bool, is_liuti: bool, zhenjia: Dict = None, changsheng_state: str = None) -> Tuple[str, str]:
        """
        判断吉凶

        规则：
        - 吉星（元辰、武财）+ 六相 = 大吉
        - 吉星（元辰、武财）+ 六替 = 凶（除非真假生死辨证明有气）
        - 凶星（贪官、破鬼）+ 六替 = 大吉
        - 凶星（贪官、破鬼）+ 六相 = 凶（除非真假生死辨证明无气）
        """
        # 无真假辨时，使用传统判断
        if not zhenjia:
            state = changsheng_state if changsheng_state else ('六相' if is_liuxiang else '六替')
            if liuqin in ['元辰', '武财']:
                if is_liuxiang:
                    return '吉', f'{liuqin}坐{state}位，六相吉'
                else:
                    return '凶', f'{liuqin}坐{state}位，六替凶'
            elif liuqin in ['贪官', '破鬼']:
                if is_liuti:
                    return '吉', f'{liuqin}坐{state}位，六替反吉'
                else:
                    return '凶', f'{liuqin}坐{state}位，六相凶'
            else:
                return '平', f'{liuqin}为中神'

        # 有真假辨时，按新规则判断
        youqi = zhenjia.get('有无气', '')
        zhenjia_reason = zhenjia.get('原因', '')

        if liuqin in ['元辰', '武财']:
            # 吉星需要化气有气
            if youqi == '有气':
                return '吉', f'{liuqin}化气{huaqi}有气，{zhenjia_reason}'
            else:
                return '凶', f'{liuqin}化气{huaqi}无气，{zhenjia_reason}'

        elif liuqin in ['贪官', '破鬼']:
            # 凶星需要化气无气
            if youqi == '无气':
                return '吉', f'{liuqin}化气{huaqi}无气，{zhenjia_reason}'
            else:
                return '凶', f'{liuqin}化气{huaqi}有气，{zhenjia_reason}'

        else:
            return '平', f'{liuqin}为中神'

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
        分析四柱的六相六替（包含真假生死辨）

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
            '平课数': 0,
            '总分': 0,
            '平均分': 0,
            '综合评价': '',
            '真假辨说明': ''
        }

        # 获取月柱地支用于真假辨
        month_zhi = sizhu.get('月柱', '')[1] if len(sizhu.get('月柱', '')) > 1 else None

        # 评分标准
        score_map = {
            '吉': 90,
            '平': 70,
            '凶': 30
        }

        # 特别加分：帝旺、临官
        bonus_map = {
            '帝旺': 10,
            '临官': 5,
            '长生': 5,
            '冠带': 3,
            '胎': 2,
            '养': 1
        }

        # 特别减分：死、墓、绝
        penalty_map = {
            '死': -10,
            '墓': -5,
            '绝': -5,
            '病': -3,
            '衰': -2,
            '沐浴': -2
        }

        for pillar_name, ganzhi in sizhu.items():
            is_month = (pillar_name == '月柱')
            analysis = self.analyze_pillar(ganzhi, shan_wuxing, is_month, month_zhi)
            result['四柱分析'][pillar_name] = analysis

            if analysis['六相/六替'] == '六相':
                result['六相统计'] += 1
            else:
                result['六替统计'] += 1

            if analysis['吉凶'] == '吉':
                result['吉课数'] += 1
            elif analysis['吉凶'] == '凶':
                result['凶课数'] += 1
            else:
                result['平课数'] += 1

            # 计分
            pillar_score = score_map.get(analysis['吉凶'], 50)

            # 附加分（基于长生状态）
            changsheng = analysis['长生状态']
            if changsheng in bonus_map:
                pillar_score += bonus_map[changsheng]
            elif changsheng in penalty_map:
                pillar_score += penalty_map[changsheng]

            analysis['分数'] = max(0, min(100, pillar_score))
            result['总分'] += analysis['分数']

        # 平均分
        result['平均分'] = result['总分'] / len(sizhu) if sizhu else 0

        # 真假辨说明
        month_analysis = result['四柱分析'].get('月柱', {})
        if '真假生死辨' in month_analysis:
            zj = month_analysis['真假生死辨']
            result['真假辨说明'] = f"月柱{zj['真假']}，{zj['原因']}"

        # 综合评价
        if result['吉课数'] >= 3 and result['凶课数'] == 0:
            result['综合评价'] = '上上大吉'
        elif result['吉课数'] >= 2:
            result['综合评价'] = '吉'
        elif result['吉课数'] >= 1:
            result['综合评价'] = '平'
        else:
            result['综合评价'] = '凶'

        return result


def test_correct_system():
    """测试正确的六相六替系统（包含真假生死辨）"""
    print('=' * 80)
    print('六相六替与真假生死辨分析系统')
    print('=' * 80)

    system = LiuXiangLiuTiCorrect()

    # 测试案例
    test_cases = [
        {
            'name': '庚子日（金真死）',
            'shan': '壬',
            'shan_wuxing': '土',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '壬子',  # 庚子日，月令=子月水旺
                '日柱': '庚子',
                '时柱': '丙申'
            }
        },
        {
            'name': '壬子日（木不败）',
            'shan': '壬',
            'shan_wuxing': '土',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '壬子',  # 壬子日，木在子沐浴，但水生木
                '日柱': '壬子',
                '时柱': '丙申'
            }
        },
        {
            'name': '辛卯日（水真死）',
            'shan': '壬',
            'shan_wuxing': '土',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '辛卯',  # 辛化水，水的死地在卯
                '日柱': '辛卯',
                '时柱': '丙申'
            }
        }
    ]

    for case in test_cases:
        print(f'\n{"="*80}')
        print(f'【{case["name"]}】坐山：{case["shan"]}山（五行：{case["shan_wuxing"]}）')
        print(f'四柱：{case["sizhu"]["年柱"]} {case["sizhu"]["月柱"]} {case["sizhu"]["日柱"]} {case["sizhu"]["时柱"]}')
        print('='*80)

        result = system.analyze_sizhu(case['sizhu'], case['shan_wuxing'])

        print(f'\n【逐柱分析】（包含真假生死辨）')
        for pillar_name, analysis in result['四柱分析'].items():
            print(f'\n  {pillar_name}: {analysis["干支"]}')
            print(f'    天干化气：{analysis["天干"]} → {analysis["化气"]}')
            print(f'    六亲：{analysis["六亲"]}')
            print(f'    长生状态：{analysis["长生状态"]} ({analysis["六相/六替"]})')
            if '真假生死辨' in analysis:
                zj = analysis['真假生死辨']
                print(f'    真假生死辨：{zj["真假"]} - {zj["原因"]}')
                print(f'    可用性：{zj["可用性"]}')
            print(f'    吉凶：{analysis["吉凶"]} ({analysis["吉凶原因"]})')
            print(f'    评分：{analysis["分数"]}分')

        print(f'\n【统计】')
        print(f'  六相数：{result["六相统计"]}')
        print(f'  六替数：{result["六替统计"]}')
        print(f'  吉课数：{result["吉课数"]}')
        print(f'  平课数：{result["平课数"]}')
        print(f'  凶课数：{result["凶课数"]}')
        print(f'  总分：{result["总分"]}')
        print(f'  平均分：{result["平均分"]:.1f}')
        print(f'  综合评价：{result["综合评价"]}')
        if result['真假辨说明']:
            print(f'  真假辨：{result["真假辨说明"]}')


if __name__ == '__main__':
    test_correct_system()
