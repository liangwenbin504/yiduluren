#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 模块 4：大六壬课体分析模块

功能：
1. 为每个时辰的日课独立起大六壬课体
2. 准确生成完整课格要素（四课三传、天将配置、神煞分布、六亲关系）
3. 依据大六壬传统断课规则建立评分模型（0-100 分）
4. 提供课体生成的完整过程记录
5. 支持常见课体类型（伏吟、返吟、元首、重审等）的智能分类
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
from daliuren_64ke_rules import (
    KE_JING_64, get_ke_jing_by_name, get_score_by_name, 
    get_jixiong_by_name, get_all_ke_names
)


class DaLiuRenKegeAnalyzer:
    """大六壬课体分析器"""
    
    # 天干五行
    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火',
        '戊': '土', '己': '土', '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木',
        '辰': '土', '巳': '火', '午': '火', '未': '土',
        '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 天干顺序
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 六亲关系（以日干五行为"我"）
    LIU_QIN_MAP = {
        '木': {'生我': '水', '我生': '火', '克我': '金', '我克': '土', '同我': '木'},
        '火': {'生我': '木', '我生': '土', '克我': '水', '我克': '金', '同我': '火'},
        '土': {'生我': '火', '我生': '金', '克我': '木', '我克': '水', '同我': '土'},
        '金': {'生我': '土', '我生': '水', '克我': '火', '我克': '木', '同我': '金'},
        '水': {'生我': '金', '我生': '木', '克我': '土', '我克': '火', '同我': '水'}
    }
    
    # 十二天将
    TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                  '天空', '白虎', '太常', '玄武', '太阴', '天后']
    
    # 天将吉凶
    TIAN_JIANG_JI_XIONG = {
        '贵人': '吉', '青龙': '吉', '六合': '吉', '太常': '吉',
        '天后': '吉', '太阴': '吉', '朱雀': '凶', '螣蛇': '凶',
        '勾陈': '凶', '白虎': '凶', '天空': '凶', '玄武': '凶'
    }
    
    # 课体吉凶分类（基于 64 课课经）
    KE_TI_JI_XIONG = KE_JING_64
    
    # 神煞配置
    SHEN_SHA = {
        '天德': {'type': '吉', 'score': 10},
        '月德': {'type': '吉', 'score': 10},
        '天赦': {'type': '吉', 'score': 15},
        '驿马': {'type': '平', 'score': 5},
        '桃花': {'type': '平', 'score': 3},
        '劫煞': {'type': '凶', 'score': -10},
        '灾煞': {'type': '凶', 'score': -10},
        '岁破': {'type': '凶', 'score': -15},
        '月破': {'type': '凶', 'score': -10}
    }
    
    def __init__(self):
        self.calculator = SiKeSanChuanCalculator()
        self.logs = []
    
    def log(self, message: str):
        """记录日志"""
        self.logs.append(message)
    
    def get_lunar_month_from_date(self, date: datetime) -> int:
        """
        从公历日期获取农历月份（简化版）
        实际应使用完整的农历转换模块
        """
        # 简化处理：用月份近似
        month = date.month
        # 考虑节气转换（简化）
        if date.day >= 23:
            return month if month <= 12 else 1
        else:
            return month - 1 if month > 1 else 12
    
    def get_yuejiang_from_date(self, date: datetime) -> str:
        """
        根据日期获取月将
        月将规则：雨水亥将，春分戌将，谷雨酉将...
        """
        # 节气与月将对应（简化版）
        yuejiang_by_month = {
            1: '子', 2: '亥', 3: '戌', 4: '酉',
            5: '申', 6: '未', 7: '午', 8: '巳',
            9: '辰', 10: '卯', 11: '寅', 12: '丑'
        }
        return yuejiang_by_month.get(date.month, '子')
    
    def get_shichen_dizhi(self, shichen_index: int) -> str:
        """
        根据时辰序号获取地支
        :param shichen_index: 时辰序号 (1-12)
        :return: 时辰地支
        """
        shichen_map = {
            1: '子', 2: '丑', 3: '寅', 4: '卯',
            5: '辰', 6: '巳', 7: '午', 8: '未',
            9: '申', 10: '酉', 11: '戌', 12: '亥'
        }
        return shichen_map.get(shichen_index, '子')
    
    def analyze_kege(self, date: datetime, shichen_index: int, 
                     ri_gan: str, ri_zhi: str) -> Dict:
        """
        分析大六壬课体
        :param date: 公历日期
        :param shichen_index: 时辰序号 (1-12)
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 课体分析结果
        """
        self.logs = []
        self.log(f"开始大六壬课体分析：{date.strftime('%Y-%m-%d')}")
        
        # 1. 获取月将和占时
        yuejiang = self.get_yuejiang_from_date(date)
        shichen = self.get_shichen_dizhi(shichen_index)
        
        self.log(f"月将：{yuejiang}, 占时：{shichen}")
        
        # 2. 排天地盘
        tiandi_pan = self.calculator.get_tiandi_pan(yuejiang, shichen)
        
        # 3. 起四课
        sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
        
        # 4. 发三传
        sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
        
        # 5. 分析课体结构
        kege_analysis = self._analyze_kege_structure(
            ri_gan, ri_zhi, sike, sanchuan_result, tiandi_pan
        )
        
        # 6. 分析天将配置
        tianjiang_analysis = self._analyze_tianjiang(
            sanchuan_result, ri_gan, shichen
        )
        
        # 7. 分析神煞
        shensha_analysis = self._analyze_shensha(date, ri_gan, ri_zhi)
        
        # 8. 分析六亲关系
        liuqin_analysis = self._analyze_liuqin(ri_gan, sanchuan_result)
        
        # 9. 计算综合评分
        comprehensive_score = self._calculate_score(
            kege_analysis, tianjiang_analysis, shensha_analysis, liuqin_analysis
        )
        
        # 10. 生成吉凶断语
        duanyu = self._generate_duanyu(
            kege_analysis, comprehensive_score
        )
        
        # 构建结果
        result = {
            '基础信息': {
                '日期': date.strftime('%Y-%m-%d'),
                '月将': yuejiang,
                '占时': shichen,
                '日柱': f"{ri_gan}{ri_zhi}"
            },
            '天地盘': tiandi_pan,
            '四课': sike,
            '三传': sanchuan_result,
            '课体结构分析': kege_analysis,
            '天将配置': tianjiang_analysis,
            '神煞分布': shensha_analysis,
            '六亲关系': liuqin_analysis,
            '综合评分': comprehensive_score,
            '吉凶断语': duanyu,
            '日志': []
        }
        
        result['日志'] = self.logs.copy()
        
        return result
    
    def _analyze_kege_structure(self, ri_gan: str, ri_zhi: str,
                                sike: List, sanchuan: Dict,
                                tiandi_pan: Dict) -> Dict:
        """分析课体结构"""
        self.log("分析课体结构...")
        
        analysis = {
            '课体类型': sanchuan.get('课体', ''),
            '起法': sanchuan.get('起法', ''),
            '格局': sanchuan.get('格局', ''),
            '四课结构': [],
            '三传关系': '',
            '特殊格局': []
        }
        
        # 分析四课结构
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.calculator.is_ke(shang, xia)
            analysis['四课结构'].append({
                '课名': name,
                '上神': shang,
                '下神': xia,
                '克应': ke_type if ke_type else '无克'
            })
        
        # 分析三传关系
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        if chu and zhong and mo:
            # 检查三传进退
            chu_idx = self.DIZHI.index(chu) if chu in self.DIZHI else 0
            zhong_idx = self.DIZHI.index(zhong) if zhong in self.DIZHI else 0
            mo_idx = self.DIZHI.index(mo) if mo in self.DIZHI else 0
            
            if chu_idx < zhong_idx < mo_idx:
                analysis['三传关系'] = '进传'
            elif chu_idx > zhong_idx > mo_idx:
                analysis['三传关系'] = '退传'
            else:
                analysis['三传关系'] = '间传'
        
        # 检查特殊格局
        if self.calculator._is_fu_yin(tiandi_pan):
            analysis['特殊格局'].append('伏吟')
        if self.calculator._is_fan_yin(tiandi_pan):
            analysis['特殊格局'].append('反吟')
        
        self.log(f"课体类型：{analysis['课体类型']}")
        
        return analysis
    
    def _analyze_tianjiang(self, sanchuan: Dict, ri_gan: str, shichen: str) -> Dict:
        """分析天将配置（简化版）"""
        self.log("分析天将配置...")
        
        analysis = {
            '初传天将': '',
            '中传天将': '',
            '末传天将': '',
            '天将吉凶': []
        }
        
        # 简化处理：暂不计算具体天将
        # 实际应使用贵人起例法
        
        return analysis
    
    def _analyze_shensha(self, date: datetime, ri_gan: str, ri_zhi: str) -> Dict:
        """分析神煞"""
        self.log("分析神煞分布...")
        
        analysis = {
            '吉神': [],
            '凶神': [],
            '神煞总分': 0
        }
        
        # 简化神煞计算
        # 实际应根据年、月、日、时查神煞
        
        return analysis
    
    def _analyze_liuqin(self, ri_gan: str, sanchuan: Dict) -> Dict:
        """分析六亲关系"""
        self.log("分析六亲关系...")
        
        ri_wuxing = self.TIAN_GAN_WU_XING[ri_gan]
        liuqin_base = self.LIU_QIN_MAP[ri_wuxing]
        
        analysis = {
            '日干五行': ri_wuxing,
            '六亲基准': liuqin_base,
            '三传六亲': []
        }
        
        for chuan_name in ['初传', '中传', '末传']:
            chuan = sanchuan.get(chuan_name, '')
            if chuan:
                chuan_wuxing = self.DIZHI_WU_XING.get(chuan, '')
                
                # 确定六亲
                liuqin = ''
                for qin, wuxing in liuqin_base.items():
                    if wuxing == chuan_wuxing:
                        liuqin = qin
                        break
                
                analysis['三传六亲'].append({
                    '传名': chuan_name,
                    '地支': chuan,
                    '五行': chuan_wuxing,
                    '六亲': liuqin
                })
        
        return analysis
    
    def _calculate_score(self, kege_analysis: Dict, tianjiang_analysis: Dict,
                        shensha_analysis: Dict, liuqin_analysis: Dict) -> int:
        """
        计算综合评分（0-100 分）
        基于 64 课课经规则进行精确评分
        """
        self.log("计算综合评分...")
        
        base_score = 50  # 基础分
        
        # 1. 课体类型分（权重 60%）- 使用 64 课课经的精确分数
        ke_ti = kege_analysis.get('课体类型', '')
        ke_ti_info = self.KE_TI_JI_XIONG.get(ke_ti, {'base_score': 50, 'jixiong': '平'})
        ke_ti_score = ke_ti_info.get('base_score', 50)
        
        # 根据课经分数调整
        if ke_ti_score >= 85:
            base_score += (ke_ti_score - 50) * 0.7
        elif ke_ti_score >= 70:
            base_score += (ke_ti_score - 50) * 0.6
        elif ke_ti_score >= 50:
            base_score += (ke_ti_score - 50) * 0.5
        else:
            base_score += (ke_ti_score - 50) * 0.4
        
        self.log(f"课体类型：{ke_ti} ({ke_ti_score}分)")
        
        # 2. 三传关系分（权重 15%）
        san_chuan_guan_xi = kege_analysis.get('三传关系', '')
        if san_chuan_guan_xi == '进传':
            base_score += 8
        elif san_chuan_guan_xi == '退传':
            base_score -= 8
        
        # 3. 特殊格局分（权重 15%）
        te_shu_ge_ju = kege_analysis.get('特殊格局', [])
        if '伏吟' in te_shu_ge_ju:
            base_score -= 12
        if '反吟' in te_shu_ge_ju:
            base_score -= 12
        
        # 4. 六亲关系分（权重 10%）
        liu_qin = liuqin_analysis.get('三传六亲', [])
        ji_qin_count = 0
        xiong_qin_count = 0
        for qin_info in liu_qin:
            qin = qin_info.get('六亲', '')
            if qin in ['生我', '同我']:
                ji_qin_count += 1
            elif qin in ['克我']:
                xiong_qin_count += 1
        
        base_score += ji_qin_count * 4
        base_score -= xiong_qin_count * 4
        
        # 限制在 0-100
        final_score = max(0, min(100, int(base_score)))
        
        self.log(f"综合评分：{final_score}分")
        
        return final_score
    
    def _generate_duanyu(self, kege_analysis: Dict, score: int) -> List[str]:
        """生成吉凶断语（基于 64 课课经）"""
        duanyu = []
        
        # 根据分数给出总断
        if score >= 90:
            duanyu.append("大六壬上上大吉，百事亨通")
        elif score >= 80:
            duanyu.append("大六壬上吉，诸事顺利")
        elif score >= 70:
            duanyu.append("大六壬中吉，可用")
        elif score >= 60:
            duanyu.append("大六壬小吉，斟酌用之")
        elif score >= 50:
            duanyu.append("大六壬平，吉凶参半")
        elif score >= 40:
            duanyu.append("大六壬小凶，不宜")
        elif score >= 30:
            duanyu.append("大六壬中凶，忌用")
        else:
            duanyu.append("大六壬大凶，不可用")
        
        # 根据课体类型给出具体断语（使用 64 课课经原文）
        ke_ti = kege_analysis.get('课体类型', '')
        ke_ti_info = self.KE_TI_JI_XIONG.get(ke_ti, {})
        
        # 添加课经原文断语
        if ke_ti_info.get('duanyu'):
            duanyu.append(f"【课经】{ke_ti_info['duanyu']}")
        
        # 添加课经象曰
        if ke_ti_info.get('xiang_yue'):
            # 取象曰的前半部分
            xiang_yue = ke_ti_info['xiang_yue'].split('.')[0]
            duanyu.append(f"【象曰】{xiang_yue}")
        
        # 根据课体特征补充断语
        te_zheng = ke_ti_info.get('te_zheng', [])
        if te_zheng:
            duanyu.append(f"【特征】{', '.join(te_zheng)}")
        
        return duanyu
    
    def get_score_description(self, score: int) -> str:
        """根据评分返回吉凶描述"""
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


def test_daliuren_analyzer():
    """测试大六壬分析器"""
    print("=" * 70)
    print("大六壬课体分析模块测试")
    print("=" * 70)
    
    analyzer = DaLiuRenKegeAnalyzer()
    
    # 测试案例
    print("\n【测试案例】")
    print("日期：2026 年 3 月 24 日 午时 (第 7 个时辰)")
    print("四柱：丙午年 辛卯月 丁酉日 丙午时")
    
    from datetime import datetime
    test_date = datetime(2026, 3, 24)
    
    result = analyzer.analyze_kege(
        date=test_date,
        shichen_index=7,
        ri_gan='丁',
        ri_zhi='酉'
    )
    
    print("\n【基础信息】")
    for key, value in result['基础信息'].items():
        print(f"  {key}: {value}")
    
    print("\n【课体结构分析】")
    kege = result['课体结构分析']
    print(f"  课体类型：{kege.get('课体类型', '')}")
    print(f"  起法：{kege.get('起法', '')}")
    print(f"  三传关系：{kege.get('三传关系', '')}")
    
    print("\n【四课】")
    for ke in result['四课']:
        print(f"  {ke[0]}: {ke[1]} {ke[2]}")
    
    print("\n【三传】")
    sanchuan = result['三传']
    print(f"  初传：{sanchuan.get('初传', '')}")
    print(f"  中传：{sanchuan.get('中传', '')}")
    print(f"  末传：{sanchuan.get('末传', '')}")
    
    print(f"\n【综合评分】{result['综合评分']}分 ({analyzer.get_score_description(result['综合评分'])})")
    
    print("\n【吉凶断语】")
    for duanyu in result['吉凶断语']:
        print(f"  - {duanyu}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_daliuren_analyzer()
