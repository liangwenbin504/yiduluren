#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬综合分析引擎
集成：旬空、四季旺衰、神煞、六亲、刑冲克害、三合六合
依据《大六壬断案疏正》《壬归》判断体系，为股票预测提供全方位分析
"""
from typing import Dict, List, Tuple, Optional
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core_modules.engine.shen_sha_calculator import ShenShaCalculator
except ImportError:
    from engine.shen_sha_calculator import ShenShaCalculator


class LiurenAnalysisEngine:
    """大六壬综合分析引擎"""

    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }

    # 天干寄宫（日干与地支论刑冲合害时须用寄宫地支）
    TIAN_GAN_JI_GONG = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
        '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
        '壬': '亥', '癸': '子'
    }

    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
    }

    # 旬首表（六旬）
    XUN_SHOU = {
        '甲子': 0, '甲戌': 10, '甲申': 20, '甲午': 30, '甲辰': 40, '甲寅': 50
    }

    # 旬空映射（旬首→空亡）
    XUN_KONG_MAP = {
        '甲子': ['戌', '亥'], '甲戌': ['申', '酉'], '甲申': ['午', '未'],
        '甲午': ['辰', '巳'], '甲辰': ['寅', '卯'], '甲寅': ['子', '丑']
    }

    # 地支六合
    LIU_HE = {
        '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
        '辰': '酉', '巳': '申', '午': '未', '未': '午',
        '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
    }

    # 地支六冲
    LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }

    # 地支三合
    SAN_HE_GROUPS = [
        ('申', '子', '辰'), ('亥', '卯', '未'),
        ('寅', '午', '戌'), ('巳', '酉', '丑')
    ]

    # 三合局五行（合成之五行，非局中支各自五行：申子辰合水、亥卯未合木、寅午戌合火、巳酉丑合金）
    SAN_HE_WX = {
        ('申', '子', '辰'): '水', ('亥', '卯', '未'): '木',
        ('寅', '午', '戌'): '火', ('巳', '酉', '丑'): '金'
    }

    # 地支三刑（无恩之刑、无礼之刑、恃势之刑、自刑）
    XING_MAP = {
        '子': '卯', '卯': '子',
        '寅': '巳', '巳': '申', '申': '寅',
        '丑': '戌', '戌': '未', '未': '丑',
        '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'
    }

    # 地支六害（穿心六害）
    LIU_HAI = {
        '子': '未', '未': '子', '丑': '午', '午': '丑',
        '寅': '巳', '巳': '寅', '卯': '辰', '辰': '卯',
        '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'
    }

    # 地支相破
    XIANG_PO = {
        '子': '酉', '酉': '子', '寅': '亥', '亥': '寅',
        '卯': '午', '午': '卯', '辰': '丑', '丑': '辰',
        '巳': '申', '申': '巳', '未': '戌', '戌': '未'
    }

    # 六亲映射（以日干五行为"我"）
    LIU_QIN_MAP = {
        '木': {'生我': '水', '我生': '火', '克我': '金', '我克': '土', '同我': '木'},
        '火': {'生我': '木', '我生': '土', '克我': '水', '我克': '金', '同我': '火'},
        '土': {'生我': '火', '我生': '金', '克我': '木', '我克': '水', '同我': '土'},
        '金': {'生我': '土', '我生': '水', '克我': '火', '我克': '木', '同我': '金'},
        '水': {'生我': '金', '我生': '木', '克我': '土', '我克': '火', '同我': '水'}
    }

    # 六亲名称映射
    LIU_QIN_NAME_MAP = {
        '生我': '父母', '我生': '子孙', '克我': '官鬼', '我克': '妻财', '同我': '兄弟'
    }

    # 四季旺衰（旺相休囚死）
    SEASON_WANG_SHUAI = {
        '春': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
        '夏': {'火': '旺', '土': '相', '木': '休', '水': '囚', '金': '死'},
        '秋': {'金': '旺', '水': '相', '土': '休', '火': '囚', '木': '死'},
        '冬': {'水': '旺', '木': '相', '金': '休', '土': '囚', '火': '死'},
        '四季': {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'}
    }

    # 五行 → 临官（禄位）地支（十二长生·临官）：木寅 火巳 土巳 金申 水亥
    WU_XING_LINGUAN = {'木': '寅', '火': '巳', '土': '巳', '金': '申', '水': '亥'}
    # 天干合德（五合之德）：甲己→寅 乙庚→申 丙辛→巳 丁壬→亥 戊癸→巳（通解 上卷 p138 日干神煞表全十干：甲寅乙申丙巳丁亥戊巳己寅庚申辛巳壬亥癸巳，与 p1194 排法一致）
    # （乙庚合化金，金禄在申，故乙日/庚日德神在申；德只解凶不助吉）
    # 日德（五合日德/合德系统，古例路径实际取用，line 905）
    # 通解 p1194：甲己日寅，乙庚日申，丙辛日巳，戊癸日巳。
    # 2026-08-01 修复（Fix A·Task7审计）：原戊/癸误作'未'，依通解订正为'巳'。
    HE_DE = {'甲': '寅', '己': '寅', '乙': '申', '庚': '申',
             '丙': '巳', '辛': '巳', '丁': '亥', '壬': '亥',
             '戊': '巳', '癸': '巳'}
    # 月建（地支）→ 当令五行（按节气，非公历月份）
    YUEJIAN_TO_YUELING = {'寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火',
                          '未': '土', '申': '金', '酉': '金', '戌': '土',
                          '亥': '水', '子': '水', '丑': '土'}
    # 月令五行 → 旺相休囚死（按节气月建）
    YUEJIAN_WANG_SHUAI = {
        '木': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
        '火': {'火': '旺', '土': '相', '木': '休', '水': '囚', '金': '死'},
        '金': {'金': '旺', '水': '相', '土': '休', '火': '囚', '木': '死'},
        '水': {'水': '旺', '木': '相', '金': '休', '土': '囚', '火': '死'},
        '土': {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'},
    }

    # 月份→季节映射（农历）
    MONTH_TO_SEASON = {
        1: '春', 2: '春', 3: '春',
        4: '夏', 5: '夏', 6: '夏',
        7: '秋', 8: '秋', 9: '秋',
        10: '冬', 11: '冬', 12: '冬'
    }

    # 地支→月份映射（正月寅）
    ZHI_TO_MONTH = {
        '寅': 1, '卯': 2, '辰': 3, '巳': 4, '午': 5, '未': 6,
        '申': 7, '酉': 8, '戌': 9, '亥': 10, '子': 11, '丑': 12
    }

    # ==================== 《壬归》新增常量 ====================

    # 八杀体系（《壬归》卷之一·五）
    BA_SHA_NAME = {
        '德': '德神', '合': '三合六合', '鬼': '日鬼', '墓': '墓库',
        '破': '相破', '害': '六害', '刑': '三刑', '冲': '六冲'
    }

    BA_SHA_MEANING = {
        '德': '合乃完成，德为庆会',
        '合': '合乃完成，德为庆会',
        '鬼': '鬼主伤残，事多凶险',
        '墓': '墓多暧昧，事不明朗',
        '破': '破知损坏，物已损伤',
        '害': '害见侵凌，暗中有害',
        '刑': '刑分强弱，官司刑戮',
        '冲': '冲不安宁，动荡冲散'
    }

    BA_SHA_JIXIONG = {
        '德': 4, '合': 3, '鬼': -4, '墓': -2,
        '破': -2, '害': -1, '刑': -1, '冲': -2
    }

    # 支德
    ZHI_DE = {
        '子': '巳', '丑': '午', '寅': '未', '卯': '申',
        '辰': '酉', '巳': '戌', '午': '亥', '未': '子',
        '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'
    }

    # 日鬼（克日干者，按五行）
    # 实际用五行相克动态判断，此处仅定义规则说明

    # 日墓（三合五行墓：木未/火戌/金丑/水辰/土辰，与 WU_XING_MU 一致）
    RI_MU = {
        '甲': '未', '乙': '未', '丙': '戌', '丁': '戌',
        '戊': '辰', '己': '辰', '庚': '丑', '辛': '丑',
        '壬': '辰', '癸': '辰'
    }

    # 五行之墓（水土同宫，墓在辰——2026-08-15 憨爷指正：土墓非戌乃辰）
    WU_XING_MU = {
        '木': '未', '火': '戌', '土': '辰', '金': '丑', '水': '辰'
    }

    # 十二气（长生十二宫）及其求财含义（《壬归》卷之三·干贵求财）
    SHI_ER_QI_CAI = {
        '长生': '生生不匮，将本求息之财',
        '沐浴': '涣荡消除，无攸利也',
        '冠带': '庄严整饬，冠冕峥嵘之财',
        '临官': '显荣利达，官贵公府之财',
        '帝旺': '当时乘势，财关邦国',
        '衰':   '日消月耗，早图或有成机',
        '病':   '奄奄困顿，弱何如也',
        '死':   '有去无来，望宜止也',
        '墓':   '财神归库，遇刑冲犹可图',
        '绝':   '复生尚需时日，割绝之财可图',
        '胎':   '微而又微，虽有几望',
        '养':   '微而又微，不可过赊'
    }

    # 四吉八凶（《壬归》卷之三）
    CAI_SI_JI = ['长生', '冠带', '临官', '帝旺']
    CAI_BA_XIONG = ['沐浴', '衰', '病', '死', '墓', '绝', '胎', '养']

    # 四吉八凶评分
    CAI_SI_JI_SCORE = 2
    CAI_BA_XIONG_SCORE = -1

    # 天将吉凶（《壬归》卷之一·四）
    TIAN_JIANG_JI_XIONG = {
        '贵人': '吉', '青龙': '吉', '六合': '吉',
        '太常': '吉', '天后': '吉', '太阴': '吉',
        '朱雀': '凶', '勾陈': '凶', '螣蛇': '凶',
        '白虎': '凶', '玄武': '凶', '天空': '凶'
    }

    # 天将主事
    TIAN_JIANG_SHI = {
        '贵人': '贵人之财，权利之财',
        '青龙': '娱乐财，喜庆财，酒色财',
        '六合': '合作财，中介财，和合之财',
        '太常': '日常之财，稳定之财',
        '天后': '女人之财，隐蔽之财',
        '太阴': '阴私之财，蓄积之财',
        '朱雀': '文书口舌之财，信息财',
        '勾陈': '争斗之财，田土之财',
        '螣蛇': '虚惊之财，怪异之财',
        '白虎': '凶险之财，猛烈之财',
        '玄武': '盗失之财，投机之财',
        '天空': '虚诈之财，空中之财'
    }

    # 用神五气吉凶（《壬归》卷之一·二）
    YONG_SHEN_WU_QI = {
        '旺': {'吉凶': '喜庆', '评分': 4},
        '相': {'吉凶': '益财', '评分': 3},
        '休': {'吉凶': '平淡', '评分': 0},
        '囚': {'吉凶': '困顿', '评分': -2},
        '死': {'吉凶': '绝灭', '评分': -4}
    }

    # 初传状态（《壬归》卷之一·二）
    YONG_SHEN_LIN_STATUS = {
        '败': '其事必败',
        '绝': '事结、人信至、病死',
        '墓': '事多暗昧',
        '死': '其事必止',
        '生': '事有生机',
        '旺': '事体壮旺'
    }

    # 四课关系评分（《壬归》卷之一·一）
    SIKE_QI_SCORE = {
        '益气': 3, '脱气': -2, '损气': -3, '制气': 2,
        '人宅相生': 3, '交克': -3, '上脱': -4, '交脱': -2,
        '互合': 2, '交合': 2, '本身逢墓': -3, '家宅逢墓': -2,
        '将身投墓': -4, '交刑': -2, '交害': -1
    }

    def __init__(self):
        self.shen_sha_calc = ShenShaCalculator()
        self._yuejian = None

    # ==================== 旬空计算 ====================

    def get_xun_kong(self, ri_gan_zhi: str) -> List[str]:
        """获取旬空（完整六旬算法）"""
        if len(ri_gan_zhi) != 2:
            return []
        gan = ri_gan_zhi[0]
        zhi = ri_gan_zhi[1]
        if gan not in self.TIANGAN or zhi not in self.DIZHI:
            return []
        gan_idx = self.TIANGAN.index(gan)
        zhi_idx = self.DIZHI.index(zhi)
        gan_offset = gan_idx % 10
        xun_start_zhi = (zhi_idx - gan_offset) % 12
        for xun_name, xun_idx in self.XUN_SHOU.items():
            if xun_idx % 12 == xun_start_zhi:
                return self.XUN_KONG_MAP.get(xun_name, [])
        return []

    def is_kong_wang(self, zhi: str, ri_gan_zhi: str) -> bool:
        """判断某地支是否为空亡"""
        return zhi in self.get_xun_kong(ri_gan_zhi)

    # ==================== 四季旺衰计算 ====================

    def get_season(self, month: int) -> str:
        """获取季节（四季末月辰未戌丑为土旺/四季）"""
        if month in (3, 6, 9, 12):
            return '四季'
        return self.MONTH_TO_SEASON.get(month, '春')

    def get_element_wang_shuai(self, wu_xing: str, month: int) -> str:
        """获取某五行在指定月份的旺衰状态"""
        season = self.get_season(month)
        return self.SEASON_WANG_SHUAI.get(season, {}).get(wu_xing, '平')

    def get_zhi_wang_shuai(self, zhi: str, month: int) -> str:
        """获取某地支在指定月份的旺衰状态"""
        wx = self.DIZHI_WU_XING.get(zhi, '土')
        return self.get_element_wang_shuai(wx, month)

    def get_zhi_wang_shuai_score(self, zhi: str, month: int) -> str:
        """
        获取地支旺衰评分描述
        旺+3 相+2 休0 囚-1 死-2
        """
        status = self.get_zhi_wang_shuai(zhi, month)
        scores = {'旺': '+3(旺)', '相': '+2(相)', '休': '0(休)', '囚': '-1(囚)', '死': '-2(死)'}
        return scores.get(status, '0(平)')

    # ---- 节气月建旺衰 + 临官/禄位升格 ----
    def get_element_wang_shuai_by_yuejian(self, wu_xing: str, yuejian_zhi: str) -> str:
        """按节气月建计算某五行旺衰（如未月→土旺，而非公历7月→秋金旺）"""
        yueling = self.YUEJIAN_TO_YUELING.get(yuejian_zhi, '土')
        return self.YUEJIAN_WANG_SHUAI.get(yueling, {}).get(wu_xing, '平')

    def get_zhi_wang_shuai_by_yuejian(self, zhi: str, yuejian_zhi: str, base_zhi: str = None) -> str:
        """按节气月建算地支旺衰，并应用『坐临官/禄位升格旺相』规则。
        base_zhi: 该地支所坐（地盘）地支；坐在其五行临官位 → 至少升为相，休囚死则升为旺。"""
        wx = self.DIZHI_WU_XING.get(zhi, '土')
        status = self.get_element_wang_shuai_by_yuejian(wx, yuejian_zhi)
        if base_zhi and self.WU_XING_LINGUAN.get(wx) == base_zhi:
            if status in ('休', '囚', '死'):
                status = '旺'
            elif status == '平':
                status = '相'
        return status

    def _ws(self, arg, month, base_zhi=None):
        """统一旺衰解析：若已设节气月建(self._yuejian)则按节气月建+临官升格，否则回退公历月份。"""
        yuejian = getattr(self, '_yuejian', None)
        if yuejian:
            if arg in self.DIZHI_WU_XING:
                return self.get_zhi_wang_shuai_by_yuejian(arg, yuejian, base_zhi)
            return self.get_element_wang_shuai_by_yuejian(arg, yuejian)
        if arg in self.DIZHI_WU_XING:
            return self.get_zhi_wang_shuai(arg, month)
        return self.get_element_wang_shuai(arg, month)

    def get_wang_shuai_value(self, status: str) -> int:
        """旺衰状态转数值"""
        values = {'旺': 3, '相': 2, '休': 0, '囚': -1, '死': -2}
        return values.get(status, 0)

    # ==================== 六亲计算 ====================

    def get_liuqin(self, ri_gan: str, zhi: str) -> str:
        """获取某地支相对于日干的六亲关系"""
        gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        zhi_wx = self.DIZHI_WU_XING.get(zhi, '')
        if not gan_wx or not zhi_wx:
            return ''
        liuqin_base = self.LIU_QIN_MAP.get(gan_wx, {})
        for relation, wx in liuqin_base.items():
            if wx == zhi_wx:
                return self.LIU_QIN_NAME_MAP.get(relation, '')
        return ''

    def get_liuqin_analysis(self, ri_gan: str, zhi_list: List[str]) -> List[Dict]:
        """获取多个地支的六亲分析"""
        result = []
        for zhi in zhi_list:
            result.append({
                '地支': zhi,
                '五行': self.DIZHI_WU_XING.get(zhi, ''),
                '六亲': self.get_liuqin(ri_gan, zhi)
            })
        return result

    # ==================== 刑冲克害三合六合计算 ====================

    def get_liu_he(self, zhi: str) -> Optional[str]:
        """获取地支六合"""
        return self.LIU_HE.get(zhi)

    def get_liu_chong(self, zhi: str) -> Optional[str]:
        """获取地支六冲"""
        return self.LIU_CHONG.get(zhi)

    def get_xing(self, zhi: str) -> Optional[str]:
        """获取地支相刑"""
        return self.XING_MAP.get(zhi)

    def get_liu_hai(self, zhi: str) -> Optional[str]:
        """获取地支六害"""
        return self.LIU_HAI.get(zhi)

    def get_xiang_po(self, zhi: str) -> Optional[str]:
        """获取地支相破"""
        return self.XIANG_PO.get(zhi)

    def get_san_he(self, zhi: str) -> List[str]:
        """获取某地支所在三合局的另两个地支"""
        for group in self.SAN_HE_GROUPS:
            if zhi in group:
                return list(group)
        return []

    def get_relationships(self, zhi: str) -> Dict:
        """获取某地支的所有关系（六合、六冲、三刑、六害、相破、三合）"""
        return {
            '六合': self.get_liu_he(zhi),
            '六冲': self.get_liu_chong(zhi),
            '三刑': self.get_xing(zhi),
            '六害': self.get_liu_hai(zhi),
            '相破': self.get_xiang_po(zhi),
            '三合': self.get_san_he(zhi)
        }

    def analyze_pair_relationship(self, zhi_a: str, zhi_b: str, label_a: str = '', label_b: str = '') -> Dict:
        """分析两个地支之间的关系
        【BUG-FIX 2026-08-18】参数可为天干（如日干），自动转寄宫地支再判刑冲合害，
        原天干直接查 DIZHI 表恒 miss（六合/冲/刑/害/破全部丢失）。"""
        if zhi_a and zhi_a in self.TIAN_GAN_JI_GONG:
            zhi_a = self.TIAN_GAN_JI_GONG[zhi_a]
        if zhi_b and zhi_b in self.TIAN_GAN_JI_GONG:
            zhi_b = self.TIAN_GAN_JI_GONG[zhi_b]
        result = {'甲': zhi_a, '乙': zhi_b, '关系': []}

        if self.LIU_HE.get(zhi_a) == zhi_b:
            result['关系'].append('六合')
        if self.LIU_CHONG.get(zhi_a) == zhi_b:
            result['关系'].append('六冲')
        if self.XING_MAP.get(zhi_a) == zhi_b or self.XING_MAP.get(zhi_b) == zhi_a:
            result['关系'].append('相刑')
        if self.LIU_HAI.get(zhi_a) == zhi_b:
            result['关系'].append('六害')
        if self.XIANG_PO.get(zhi_a) == zhi_b:
            result['关系'].append('相破')

        for group in self.SAN_HE_GROUPS:
            if zhi_a in group and zhi_b in group:
                result['关系'].append('三合')
                break

        wx_a = self.DIZHI_WU_XING.get(zhi_a, '')
        wx_b = self.DIZHI_WU_XING.get(zhi_b, '')
        if wx_a and wx_b:
            if self._is_ke(wx_a, wx_b):
                result['关系'].append(f'{wx_a}克{wx_b}')
            elif self._is_ke(wx_b, wx_a):
                result['关系'].append(f'{wx_b}克{wx_a}')
            if self._is_sheng(wx_a, wx_b):
                result['关系'].append(f'{wx_a}生{wx_b}')
            elif self._is_sheng(wx_b, wx_a):
                result['关系'].append(f'{wx_b}生{wx_a}')

        return result

    @staticmethod
    def _is_ke(wx_a: str, wx_b: str) -> bool:
        """五行相克判断"""
        ke_map = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
        return ke_map.get(wx_a) == wx_b

    @staticmethod
    def _is_sheng(wx_a: str, wx_b: str) -> bool:
        """五行相生判断"""
        sheng_map = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        return sheng_map.get(wx_a) == wx_b

    # ==================== 《壬归》四课加临分析 ====================

    def analyze_sike_qi(self, ri_gan: str, ri_zhi: str, sike: List) -> Dict:
        """
        四课加临之气分析（《壬归》卷之一·一）
        
        分析日上神/辰上神与日/辰之间的益气、脱气、损气、制气关系
        """
        result = {'四课关系': [], '评分': 0, '描述': ''}

        if not sike or len(sike) < 4:
            return result

        gan_shang_shen = ''
        gan = ri_gan
        zhi_shang_shen = ''
        zhi = ri_zhi

        if hasattr(sike[0], '__getitem__') and len(sike[0]) > 1:
            gan_shang_shen = sike[0][1]
        if hasattr(sike[2], '__getitem__') and len(sike[2]) > 1:
            zhi_shang_shen = sike[2][1]  # 第三课为日支课，sike[2]是日支上神

        if not gan_shang_shen or not zhi_shang_shen:
            return result

        gan_wx = self.TIAN_GAN_WU_XING.get(gan, '')
        gan_shang_wx = self.DIZHI_WU_XING.get(gan_shang_shen, '')
        zhi_wx = self.DIZHI_WU_XING.get(zhi, '')
        zhi_shang_wx = self.DIZHI_WU_XING.get(zhi_shang_shen, '')

        # 1. 日上神 vs 日干
        if gan_wx and gan_shang_wx:
            if self._is_sheng(gan_shang_wx, gan_wx):
                result['四课关系'].append({
                    '类型': '益气', '描述': f'日上神{gan_shang_shen}({gan_shang_wx})生日干{gan}({gan_wx})，有益于我，遇灾不凶'
                })
            elif self._is_sheng(gan_wx, gan_shang_wx):
                result['四课关系'].append({
                    '类型': '脱气', '描述': f'日干{gan}({gan_wx})生日上神{gan_shang_shen}({gan_shang_wx})，脱耗于我，事多脱赚'
                })
            if self._is_ke(gan_shang_wx, gan_wx):
                result['四课关系'].append({
                    '类型': '损气', '描述': f'日上神{gan_shang_shen}({gan_shang_wx})克日干{gan}({gan_wx})，有损于我，旺相为官星'
                })
            elif self._is_ke(gan_wx, gan_shang_wx):
                result['四课关系'].append({
                    '类型': '制气', '描述': f'日干{gan}({gan_wx})克日上神{gan_shang_shen}({gan_shang_wx})，受制于我，我克者为财'
                })

        # 2. 辰上神 vs 日支
        if zhi_wx and zhi_shang_wx:
            if self._is_sheng(zhi_shang_wx, zhi_wx):
                result['四课关系'].append({
                    '类型': '支得益气', '描述': f'辰上神{zhi_shang_shen}({zhi_shang_wx})生辰{zhi}({zhi_wx})，宅得益'
                })
            elif self._is_sheng(zhi_wx, zhi_shang_wx):
                result['四课关系'].append({
                    '类型': '支脱气', '描述': f'辰{zhi}({zhi_wx})生辰上神{zhi_shang_shen}({zhi_shang_wx})，宅有脱耗'
                })
            if self._is_ke(zhi_shang_wx, zhi_wx):
                result['四课关系'].append({
                    '类型': '支损气', '描述': f'辰上神{zhi_shang_shen}({zhi_shang_wx})克辰{zhi}({zhi_wx})，宅被克制'
                })

        # 3. 人宅关系（日上神 vs 辰，辰上神 vs 日干）
        if gan_shang_wx and zhi_wx:
            if self._is_sheng(gan_shang_wx, zhi_wx) and self._is_sheng(zhi_shang_wx, gan_wx):
                result['四课关系'].append({
                    '类型': '人宅相生', '描述': f'日上神生辰、辰上神生日，人宅相生彼此受益'
                })
            if self._is_ke(gan_shang_wx, zhi_wx) and self._is_ke(zhi_shang_wx, gan_wx):
                result['四课关系'].append({
                    '类型': '交克', '描述': f'日上神克辰、辰上神克日，人宅相伤宾主不睦'
                })
            if self._is_sheng(gan_wx, gan_shang_wx) and hasattr(sike[0], '__getitem__'):
                gui_ren_on_gan_shang = ''
                result['四课关系'].append({
                    '类型': '上脱', '描述': f'日辰皆生上神，脱上逢脱多虚诈'
                })

        # 4. 互合/交合
        he_pairs = [
            (gan, gan_shang_shen, '日干', '日上神'),
            (zhi, zhi_shang_shen, '日支', '辰上神'),
            (gan_shang_shen, zhi_shang_shen, '日上神', '辰上神')
        ]
        for a, b, la, lb in he_pairs:
            if self.LIU_HE.get(a) == b:
                result['四课关系'].append({
                    '类型': '互合', '描述': f'{la}{a}与{lb}{b}六合，和合圆成'
                })

        # 5. 交互刑害
        for a, b, la, lb in [(gan, gan_shang_shen, '日干', '日上神'), (zhi, zhi_shang_shen, '日支', '辰上神'),
                             (gan_shang_shen, zhi_shang_shen, '日上神', '辰上神')]:
            if self.XING_MAP.get(a) == b or self.XING_MAP.get(b) == a:
                result['四课关系'].append({
                    '类型': '交刑', '描述': f'{la}{a}与{lb}{b}相刑，彼此猜忌'
                })
            if self.LIU_HAI.get(a) == b:
                result['四课关系'].append({
                    '类型': '交害', '描述': f'{la}{a}与{lb}{b}六害，暗中有损'
                })

        # 6. 墓的情况
        ri_mu_zhi = self.RI_MU.get(gan, '')
        if ri_mu_zhi and gan_shang_shen == ri_mu_zhi:
            result['四课关系'].append({
                '类型': '本身逢墓', '描述': f'日上神{gan_shang_shen}为日干{gan}之墓，华盖覆日如雾暗室'
            })
        if ri_mu_zhi and zhi_shang_shen == ri_mu_zhi:
            result['四课关系'].append({
                '类型': '家宅逢墓', '描述': f'辰上神{zhi_shang_shen}为日干{gan}之墓，家宅逢墓'
            })

        # 7. 日上神为日鬼
        if gan_wx and gan_shang_wx and self._is_ke(gan_shang_wx, gan_wx):
            result['四课关系'].append({
                '类型': '日鬼临身', '描述': f'日上神{gan_shang_shen}克日干{gan}，为日鬼临身，最为不吉'
            })

        # 8. 日上辰上特殊神煞
        if gan_shang_shen in ('辰', '戌'):
            result['四课关系'].append({
                '类型': '魁罡临日', '描述': f'日上{gan_shang_shen}为魁罡，事不由己'
            })
        if zhi_shang_shen in ('辰', '戌'):
            result['四课关系'].append({
                '类型': '魁罡临辰', '描述': f'辰上{zhi_shang_shen}为魁罡，家宅不宁'
            })

        # 综合评分
        score = 0
        for item in result['四课关系']:
            score += self.SIKE_QI_SCORE.get(item['类型'], 0)
        result['评分'] = score

        # 综合描述
        qi_types = [item['类型'] for item in result['四课关系']]
        if score >= 5:
            result['描述'] = f'四课关系良好（{score}分），人宅相生、益气扶助，大局有利'
        elif score >= 0:
            result['描述'] = f'四课关系中性（{score}分），有利有弊，需结合其他因素综合判断'
        else:
            result['描述'] = f'四课关系不佳（{score}分），人宅相伤、脱耗克损，需谨慎'

        return result

    # ==================== 《壬归》用神分析 ====================

    def analyze_yong_shen(self, yong_shen_zhi: str, ri_gan: str, month: int,
                          sike: List, gan_shang_shen: str = '', zhi_shang_shen: str = '',
                          tiandi_pan: Dict = None) -> Dict:
        """
        用神（发用）分析（《壬归》卷之一·二）
        
        分析发用的五气状态、所在课位、生克关系
        """
        result = {}
        if not yong_shen_zhi:
            return result

        yong_shen_wx = self.DIZHI_WU_XING.get(yong_shen_zhi, '')

        # 用神五气（坐临官升格：用神天盘地支所坐地盘临官则升格为旺/相）
        _yong_base = None
        if tiandi_pan:
            for _d, _t in tiandi_pan.items():
                if _t == yong_shen_zhi:
                    _yong_base = _d
                    break
        wang_shuai = self._ws(yong_shen_zhi, month, base_zhi=_yong_base)
        wu_qi_info = self.YONG_SHEN_WU_QI.get(wang_shuai, {'吉凶': '平', '评分': 0})
        result['用神地支'] = yong_shen_zhi
        result['五行'] = yong_shen_wx
        result['旺衰'] = wang_shuai
        result['五气吉凶'] = wu_qi_info['吉凶']
        result['五气评分'] = wu_qi_info['评分']

        # 用神所在课位（日上/辰上 → 外事/内事）
        yong_shen_location = ''
        if sike and len(sike) >= 2:
            if hasattr(sike[0], '__getitem__'):
                if sike[0][1] == yong_shen_zhi or (len(sike[0]) > 0 and sike[0][0] == yong_shen_zhi):
                    yong_shen_location = '日上两课'
            if hasattr(sike[2], '__getitem__'):
                if sike[2][1] == yong_shen_zhi or (len(sike[2]) > 0 and sike[2][0] == yong_shen_zhi):
                    yong_shen_location = '辰上两课'
        result['用神所在'] = yong_shen_location

        if yong_shen_location == '日上两课':
            result['事体外内'] = '外事，主远，主去'
        elif yong_shen_location == '辰上两课':
            result['事体外内'] = '内事，主近，主来'
        else:
            result['事体外内'] = ''

        # 用神生克（日干 vs 用神）
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        if ri_gan_wx and yong_shen_wx:
            if self._is_sheng(yong_shen_wx, ri_gan_wx):
                result['日用关系'] = '用神生日干，为益气，吉'
            elif self._is_sheng(ri_gan_wx, yong_shen_wx):
                result['日用关系'] = '日干生用神，为脱气'
            if self._is_ke(yong_shen_wx, ri_gan_wx):
                result['日用关系'] = '用神克日干，为损气，鬼临用'
            elif self._is_ke(ri_gan_wx, yong_shen_wx):
                result['日用关系'] = '日干克用神，为制气，我克者为财'

        # 用神与日上神的关系
        if gan_shang_shen and gan_shang_shen != yong_shen_zhi:
            rel = self.analyze_pair_relationship(yong_shen_zhi, gan_shang_shen, '用神', '日上')
            if rel.get('关系'):
                result['与日上神关系'] = rel['关系']

        return result

    # ==================== 《壬归》三传制救分析 ====================

    def get_yin_shen(self, zhi: str, tiandi_pan: Dict) -> str:
        """
        计算某地支的阴神
        阴神：某地盘上的天盘（即该地支作为地盘，对应的天盘）
        """
        if not tiandi_pan or not zhi:
            return ''
        return tiandi_pan.get(zhi, '')

    def get_yin_shen_chain(self, zhi: str, tiandi_pan: Dict, depth: int = 3) -> List[str]:
        """
        计算阴神链条（阴神的阴神...）
        :param zhi: 起始地支
        :param tiandi_pan: 天地盘
        :param depth: 链条深度（默认3层）
        :return: 阴神列表 [阴神1, 阴神2, 阴神3...]
        """
        chain = []
        current = zhi
        for _ in range(depth):
            yin_shen = self.get_yin_shen(current, tiandi_pan)
            if not yin_shen or yin_shen in chain:
                break
            chain.append(yin_shen)
            current = yin_shen
        return chain

    def analyze_yin_shen(self, sanchuan: Dict, tiandi_pan: Dict, 
                         ri_gan: str = '') -> Dict:
        """
        三传阴神分析（六壬深度推理的核心）
        "传不尽者，以阴神决之"
        """
        result = {
            '初传阴神': '',
            '中传阴神': '',
            '末传阴神': '',
            '三传阴神链': [],
            '阴神六亲': [],
            '阴神旺衰': [],
            '阴神推理提示': []
        }
        
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]
        chuan_names = ['初传', '中传', '末传']
        
        for i, chuan_zhi in enumerate(sanchuan_list):
            if not chuan_zhi:
                continue
            
            yin = self.get_yin_shen(chuan_zhi, tiandi_pan)
            result[f'{chuan_names[i]}阴神'] = yin
            
            if yin:
                yin_chain = self.get_yin_shen_chain(chuan_zhi, tiandi_pan, depth=3)
                result['三传阴神链'].append({
                    '传名': chuan_names[i],
                    '本传': chuan_zhi,
                    '阴神链条': yin_chain
                })
                
                if ri_gan:
                    yin_liuqin = self.get_liuqin(ri_gan, yin)
                    result['阴神六亲'].append(f'{chuan_names[i]}阴神{yin}为{yin_liuqin}')
        
        if result['三传阴神链']:
            result['阴神推理提示'].append('传不尽者，以阴神决之。阴神吉则终吉，阴神凶则终凶。')
        
        return result

    def analyze_sanchuan_zhi_jiu(self, sanchuan: Dict, ri_gan: str, ri_zhi: str,
                                 sike: List, month: int) -> Dict:
        """
        三传制救分析（《壬归》卷之一·三）
        
        分析三传是否有制有救，初传凶是否有救神克制
        """
        result = {}
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]

        # 三传渐见有气/无气
        qi_trend = []
        for chuan_zhi in sanchuan_list:
            if chuan_zhi:
                ws = self._ws(chuan_zhi, month)
                qi_trend.append(ws)

        if all(q in ('旺', '相') for q in qi_trend if q):
            result['气之趋势'] = '三传渐见有气，吉'
        elif all(q in ('休', '囚', '死') for q in qi_trend if q):
            result['气之趋势'] = '三传渐见无气，宜守旧'
        else:
            result['气之趋势'] = '三传之气有起伏'

        # 初传凶末传吉
        if len(sanchuan_list) >= 2:
            chu_ws = self._ws(sanchuan_list[0], month) if sanchuan_list[0] else ''
            mo_ws = self._ws(sanchuan_list[2], month) if sanchuan_list[2] else ''
            if chu_ws in ('囚', '死') and mo_ws in ('旺', '相'):
                result['始终吉凶'] = '初凶末吉，事主先难后易'
            elif chu_ws in ('旺', '相') and mo_ws in ('囚', '死'):
                result['始终吉凶'] = '初吉末凶，事主先易后难'

        # 制救分析（《壬归》：凡日辰之上见凶神恶煞，用能克去之则吉）
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        zhi_wx = self.DIZHI_WU_XING.get(ri_zhi, '')
        zhi_jiu_info = []

        if sike and len(sike) >= 4:
            gan_shang = sike[0][1] if hasattr(sike[0], '__getitem__') and len(sike[0]) > 1 else ''
            zhi_shang = sike[2][1] if hasattr(sike[2], '__getitem__') and len(sike[2]) > 1 else ''
            gan_shang_wx = self.DIZHI_WU_XING.get(gan_shang, '')
            zhi_shang_wx = self.DIZHI_WU_XING.get(zhi_shang, '')

            for chuan_zhi in sanchuan_list:
                if not chuan_zhi:
                    continue
                chuan_wx = self.DIZHI_WU_XING.get(chuan_zhi, '')
                if not chuan_wx or not ri_gan_wx:
                    continue

                if self._is_ke(chuan_wx, ri_gan_wx):
                    # 三传中有鬼，检查是否有救
                    is_saved = False
                    save_source = ''

                    if gan_shang_wx and self._is_ke(gan_shang_wx, chuan_wx):
                        is_saved = True
                        save_source = f'日上神{gan_shang}({gan_shang_wx})克之'
                    if zhi_shang_wx and self._is_ke(zhi_shang_wx, chuan_wx):
                        is_saved = True
                        save_source = f'辰上神{zhi_shang}({zhi_shang_wx})克之'

                    if is_saved:
                        zhi_jiu_info.append(f'{chuan_zhi}为鬼，但有{save_source}，为有救，凶中有吉')
                    else:
                        zhi_jiu_info.append(f'{chuan_zhi}为鬼，无制救，凶')

        if zhi_jiu_info:
            result['制救分析'] = zhi_jiu_info

        return result

    # ==================== 《壬归》贵神吉凶分析 ====================

    def analyze_gui_shen_ji_xiong(self, sanchuan: Dict, shen_sha: Dict) -> Dict:
        """
        贵神吉凶分析（《壬归》卷之一·四）
        
        分析天乙贵人的状态和天将的吉凶
        - 天乙临刑/临害/坐狱/临空/临身
        【BUG-FIX 2026-08-18】原"天乙临刑/临害"用 `gui_ren_zhi in XING_MAP/LIU_HAI`
        判断——两表键覆盖全部12支，恒真 → 天乙状态恒被"临害"覆盖。
        天乙临刑害须两支成对才有意义（如天乙与日辰相刑害），单支不能自判，
        删除无条件临刑/临害；仅保留自刑（辰午酉亥）判定。
        """
        result = {}

        gui_ren = shen_sha.get('天乙贵人', '')
        if gui_ren:
            gui_ren_zhi = gui_ren.replace('/', '').replace('\\', '')[-1] if gui_ren else ''
            if gui_ren_zhi and gui_ren_zhi in self.DIZHI:
                # 天乙坐狱 (履辰戌)
                if gui_ren_zhi in ('辰', '戌'):
                    result['天乙状态'] = '天乙坐狱（履辰戌），干贵必辱'
                # 天乙自刑（午酉亥；辰已含于坐狱，避免覆盖）
                elif gui_ren_zhi in ('午', '酉', '亥'):
                    result['天乙状态'] = f'天乙自刑（{gui_ren_zhi}自刑），为患非轻'

        # 三传天将分析
        sanchuan_tian_jiang = {}
        for chuan_name, tian_jiang_list in sanchuan.items():
            if isinstance(tian_jiang_list, list) and len(tian_jiang_list) > 1:
                sanchuan_tian_jiang[chuan_name] = tian_jiang_list[1]

        if sanchuan_tian_jiang:
            tian_jiang_analysis = []
            for cn, tj in sanchuan_tian_jiang.items():
                jx = self.TIAN_JIANG_JI_XIONG.get(tj, '平')
                shi = self.TIAN_JIANG_SHI.get(tj, '')
                tian_jiang_analysis.append({
                    '三传': cn, '天将': tj, '吉凶': jx, '主事': shi
                })
            result['三传天将'] = tian_jiang_analysis

        return result

    # ==================== 通用理法增强（第三章·判断精髓集要；记录层，不进 valence）====================

    def _dun_gan(self, ri_gan: str, zhi: str) -> str:
        """五子元遁（初建法·日干遁）：以日干五子元遁配地支，取该支遁干。
        起点：甲己→甲子、乙庚→丙子、丙辛→戊子、丁壬→庚子、戊癸→壬子（n0 = gan序×6）。"""
        if not ri_gan or ri_gan not in self.TIANGAN or not zhi or zhi not in self.DIZHI:
            return ''
        gan0_idx = {'甲': 0, '己': 0, '乙': 2, '庚': 2, '丙': 4, '辛': 4,
                    '丁': 6, '壬': 6, '戊': 8, '癸': 8}.get(ri_gan, 0)
        n0 = gan0_idx * 6
        z_idx = self.DIZHI.index(zhi)
        return self.TIANGAN[(n0 + z_idx) % 10]

    def _analyze_jv_san(self, ri_gan: str, sanchuan_list: List[str], sike: List) -> Dict:
        """遁干聚散（第三章 L3308-3344《鬼贼五变中黄经》："干多者为聚，少者为散"）。
        以日干五子元遁（初建法）配课传所有地支，统计遁干五行分布，众数=聚、散者=散。
        记录层（上乘心法，不进 valence）。"""
        result = {'聚散': '', '聚之五行': '', '遁干分布': {}, '说明': ''}
        if not ri_gan or ri_gan not in self.TIANGAN:
            return result
        # 收集课传地支（三传 + 四课上神/下神）
        zhis = [z for z in sanchuan_list if z]
        for ke in (sike or []):
            if isinstance(ke, (list, tuple)):
                for ele in ke:
                    if isinstance(ele, str) and ele in self.DIZHI:
                        zhis.append(ele)
        if not zhis:
            return result
        wx_count = {}
        dun_detail = {}
        for z in zhis:
            dg = self._dun_gan(ri_gan, z)
            if not dg:
                continue
            wx = self.TIAN_GAN_WU_XING.get(dg, '')
            wx_count[wx] = wx_count.get(wx, 0) + 1
            dun_detail.setdefault(f'{dg}{z}', 0)
            dun_detail[f'{dg}{z}'] += 1
        result['遁干分布'] = dun_detail
        if wx_count:
            max_n = max(wx_count.values())
            ju_wx = [k for k, v in wx_count.items() if v == max_n]
            result['聚之五行'] = '/'.join(ju_wx)
            result['聚散'] = '聚' if max_n >= 2 else '散'
            result['说明'] = f'课传遁干五行分布 {wx_count}；以{result["聚之五行"]}为聚，余为散'
        return result

    def _analyze_zheng_shi(self, ri_gan: str, ri_zhi: str, shichen: str) -> Dict:
        """正时八门·先锋门分析（第三章 L3359-3360：正时为先锋门，古法多以之占断来意）。
        判断正时与日干支关系：时乘空亡/时为驿马/时克日鬼/日克时财/时与日辰合冲等。
        记录层（不进 valence）。"""
        result = {'先锋门': shichen, '关系': [], '来意提示': ''}
        if not shichen or shichen not in self.DIZHI:
            return result
        # 时乘空亡
        xun_kong = self.get_xun_kong(ri_gan + ri_zhi)
        if shichen in xun_kong:
            result['关系'].append('时乘空亡，多为虚诈')
        # 时与日干支生克（五行）
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        shi_wx = self.DIZHI_WU_XING.get(shichen, '')
        if ri_gan_wx and shi_wx:
            if self._is_ke(shi_wx, ri_gan_wx):
                result['关系'].append('时克日干，为鬼为贼')
            elif self._is_ke(ri_gan_wx, shi_wx):
                result['关系'].append('日干克时，为财为妻')
            elif self._is_sheng(shi_wx, ri_gan_wx):
                result['关系'].append('时生日干，迭为恩泽')
            elif self._is_sheng(ri_gan_wx, shi_wx):
                result['关系'].append('日干生时，泄气耗神')
        # 时与日支关系
        if shichen == ri_zhi:
            result['关系'].append('时日同辰，多主迟疑偃蹇')
        elif shichen in self.LIU_CHONG:
            if self.LIU_CHONG[shichen] == ri_zhi:
                result['关系'].append('冲辰冲日，颠沛流离')
        # 地支特征（子午卯酉辰戌丑未）
        if shichen in ('子', '午'):
            result['关系'].append('子午之时，往来多变')
        elif shichen in ('卯', '酉'):
            result['关系'].append('卯酉之时，多涉门户')
        elif shichen in ('辰', '戌', '丑', '未'):
            result['关系'].append('辰戌丑未之时，土产墓基')
        result['来意提示'] = '；'.join(result['关系']) if result['关系'] else '正时与日辰无明显冲合'
        return result

    def _analyze_fa_yong_liu_duan(self, ri_gan: str, ri_zhi: str, shichen: str,
                                   sanchuan_list: List[str], yong_shen_zhi: str,
                                   month: int) -> Dict:
        """发用六断（第三章 L3383 发用歌诀）：发用克日/辰/时/末/命/年 + 用临长生败死绝墓。
        记录层（不进 valence）；命/年需年命数据，古例路径无则标注未验。"""
        result = {'六断': [], '用临十二长生': ''}
        # 兼容：yong_shen_zhi 可能为天干（二元课结构下取下神），退回初传
        if not yong_shen_zhi or yong_shen_zhi not in self.DIZHI:
            yong_shen_zhi = sanchuan_list[0] if sanchuan_list else ''
        if not yong_shen_zhi or yong_shen_zhi not in self.DIZHI:
            return result
        yong_wx = self.DIZHI_WU_XING.get(yong_shen_zhi, '')
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        # 克日/克辰
        if yong_wx and ri_gan_wx:
            if self._is_ke(yong_wx, ri_gan_wx):
                result['六断'].append('发用克日干，忧身长上讼')
            elif self._is_ke(ri_gan_wx, yong_wx):
                result['六断'].append('日干克发用，我克为财')
        ri_zhi_wx = self.DIZHI_WU_XING.get(ri_zhi, '')
        if yong_wx and ri_zhi_wx and self._is_ke(yong_wx, ri_zhi_wx):
            result['六断'].append('发用克日支，家宅不安宁')
        # 克时
        if shichen and shichen in self.DIZHI:
            shi_wx = self.DIZHI_WU_XING.get(shichen, '')
            if yong_wx and shi_wx and self._is_ke(yong_wx, shi_wx):
                result['六断'].append('发用克正时，心动惊忧起')
        # 克末
        if len(sanchuan_list) >= 3 and sanchuan_list[2]:
            mo_wx = self.DIZHI_WU_XING.get(sanchuan_list[2], '')
            if yong_wx and mo_wx and self._is_ke(yong_wx, mo_wx):
                result['六断'].append('发用克末传，有始必无终')
        # 克命/克年（需年命，标注未验）
        result['六断'].append('克命上神主得财、克年上神事必乖（需年命数据，此处未验）')
        # 用临十二长生
        stage = self.get_shi_er_chen(ri_gan, yong_shen_zhi)
        if stage:
            result['用临十二长生'] = stage
            stage_hint = {
                '长生': '用起长生，凡谋遂',
                '沐浴': '用败，事坏毁',
                '死': '用死，事坏毁',
                '绝': '用绝，事了人信至',
                '墓': '用墓，事缓病者悲；长生临墓发旧事',
            }
            if stage in stage_hint:
                result['六断'].append(stage_hint[stage])
        return result

    # ==================== 《壬归》八杀体系分析 ====================

    def analyze_ba_sha(self, ri_gan: str, ri_zhi: str, sanchuan: Dict,
                       sike: List, month: int, ri_gan_zhi: str) -> Dict:
        """
        八杀体系分析（《壬归》卷之一·五）
        
        统一分析德、合、鬼、墓、破、害、刑、冲
        看其旺相空亡，定其往来生克
        """
        result = {
            '八杀明细': [],
            '评分': 0,
            '吉凶': '平',
            '描述': ''
        }
        xun_kong = self.get_xun_kong(ri_gan_zhi)
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]
        all_zhi = list(set([z for z in sanchuan_list if z] + [ri_zhi]))
        all_zhi.append(ri_gan)

        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')

        # 1. 德神（合德系统：乙庚合→申；德只解凶不助吉，不增吉分）
        ri_de_zhi = self.HE_DE.get(ri_gan, '')
        zhi_de_zhi = self.ZHI_DE.get(ri_zhi, '')
        de_present = []
        for chuan_zhi in sanchuan_list:
            if chuan_zhi == ri_de_zhi:
                de_present.append(f'三传{chuan_zhi}为日德（合德）')
            if chuan_zhi == zhi_de_zhi:
                de_present.append(f'三传{chuan_zhi}为支德')
        de_present_flag = bool(de_present)
        if de_present:
            is_kong = any(z in xun_kong for z in sanchuan_list if z == ri_de_zhi or z == zhi_de_zhi)
            if is_kong:
                result['八杀明细'].append({
                    '杀': '德', '出现': de_present, '状态': '空亡', '评分': 0,
                    '断语': '德神落空亡，不能为福'
                })
            else:
                result['八杀明细'].append({
                    '杀': '德', '出现': de_present, '状态': '旺相', '评分': 0,
                    '断语': '德神临传（合德），只解凶不助吉，不增吉分'
                })
        else:
            result['八杀明细'].append({
                '杀': '德', '出现': [], '状态': '未现', '评分': 0,
                '断语': '德神未现'
            })

        # 2. 合（三合六合在三传中；日支三合局=通解 p138 日支神煞'三合'行语义：
        #    日支为子，四课三传遇申、辰即三合水局。两支全现=局成计入'合'，
        #    现一支=虚一待用（通解 L1233：缺一神名折腰格，待缺神值日方成，不计'合'评分））
        he_items = []
        # 四课地支（兼容 (课名,上神,下神) 三元 与 (上神,下神) 二元结构：收集课内所有地支元素）
        sike_zhi = []
        for ke in (sike or []):
            if isinstance(ke, (list, tuple)):
                for ele in ke:
                    if isinstance(ele, str) and ele in self.DIZHI:
                        sike_zhi.append(ele)
        for chuan_zhi in sanchuan_list:
            if not chuan_zhi:
                continue
            # 六合
            he_peer = self.LIU_HE.get(chuan_zhi)
            if he_peer and he_peer in sanchuan_list:
                he_items.append(f'{chuan_zhi}与{he_peer}六合')
            # 三合
            for group in self.SAN_HE_GROUPS:
                if chuan_zhi in group:
                    others = [z for z in group if z != chuan_zhi and z in sanchuan_list]
                    if len(others) >= 1:
                        he_items.append(f'{chuan_zhi}在{group}三合局中')
                        break
        # 日支三合局 + 六亲化吉凶（通解 p138「三合」行语义 + 憨爷 2026-08-01 规则）：
        # 日支为子，课传见申、辰=三合水局；局五行相对日干的六亲定吉凶——
        #   官鬼局(局克干)凶、子孙局(干生局/泄身)凶、妻财局(干克局)吉、父母局(局生干)吉、兄弟局(同我)平。
        # 干上神制化：官鬼局+干上子孙(子孙克鬼)→制凶转平；子孙局+干上妻财(子孙生财)→泄气转财源变吉。
        # 2026-08-01 A/B 实证：一律计入'合'评分负回归(M3 87.2→86.6)，故本判定仅作课传分析记录（叙事/显示层），不计 valence。
        for group in self.SAN_HE_GROUPS:
            if ri_zhi in group:
                others = [z for z in group if z != ri_zhi]
                scope = set(sanchuan_list) | set(sike_zhi)
                hit = sorted(z for z in others if z in scope)
                if not hit:
                    break
                # 局五行（三合局合成五行：申子辰水/寅午戌火/巳酉丑金/亥卯未木）
                ju_wx = self.SAN_HE_WX.get(group, '')
                # 局五行相对日干的六亲
                if ju_wx == ri_gan_wx:
                    ju_liuqin = '兄弟'
                elif self._is_sheng(ju_wx, ri_gan_wx):
                    ju_liuqin = '父母'
                elif self._is_sheng(ri_gan_wx, ju_wx):
                    ju_liuqin = '子孙'
                elif self._is_ke(ju_wx, ri_gan_wx):
                    ju_liuqin = '官鬼'
                elif self._is_ke(ri_gan_wx, ju_wx):
                    ju_liuqin = '妻财'
                else:
                    ju_liuqin = ''
                # 干上神（第一课首个地支：三元(课名,上神,下神)取ke[1]、二元(上神,下神)取ke[0]）及其六亲
                gan_shang_zhi = ''
                if sike and isinstance(sike[0], (list, tuple)):
                    for ele in sike[0]:
                        if isinstance(ele, str) and ele in self.DIZHI:
                            gan_shang_zhi = ele
                            break
                gan_shang_wx = self.DIZHI_WU_XING.get(gan_shang_zhi, '')
                if gan_shang_wx and ri_gan_wx:
                    if gan_shang_wx == ri_gan_wx:
                        gan_shang_liuqin = '兄弟'
                    elif self._is_sheng(ri_gan_wx, gan_shang_wx):
                        gan_shang_liuqin = '子孙'
                    elif self._is_ke(ri_gan_wx, gan_shang_wx):
                        gan_shang_liuqin = '妻财'
                    elif self._is_ke(gan_shang_wx, ri_gan_wx):
                        gan_shang_liuqin = '官鬼'
                    elif self._is_sheng(gan_shang_wx, ri_gan_wx):
                        gan_shang_liuqin = '父母'
                    else:
                        gan_shang_liuqin = ''
                else:
                    gan_shang_liuqin = ''
                # 基础吉凶（局六亲定性）
                if ju_liuqin == '官鬼':
                    base = '凶（官鬼局，局克日干）'
                elif ju_liuqin == '子孙':
                    base = '凶（子孙局，泄日干之气）'
                elif ju_liuqin == '妻财':
                    base = '吉（妻财局，日干克局得财）'
                elif ju_liuqin == '父母':
                    base = '吉（父母局，局生日干）'
                else:
                    base = '平（兄弟局，比和）'
                # 干上神制化
                adjust = ''
                if ju_liuqin == '官鬼' and gan_shang_liuqin == '子孙':
                    adjust = '；干上子孙制鬼，凶转平'
                    base = '凶转平（官鬼局，干上子孙制鬼）'
                elif ju_liuqin == '子孙' and gan_shang_liuqin == '妻财':
                    adjust = '；干上妻财，子孙生财，泄气转财源，变吉'
                    base = '吉（子孙局，干上妻财受子孙生，泄气转财源）'
                if len(hit) == 2:
                    result['日支三合局'] = {
                        '局': group, '局五行': ju_wx, '六亲': ju_liuqin, '吉凶': base,
                        '干上神': gan_shang_zhi, '干上六亲': gan_shang_liuqin,
                        '课传见': hit, '说明': f'日支{ri_zhi}成{group}三合局（课传见{hit[0]}、{hit[1]}）{adjust}'
                    }
                else:
                    result['三合虚一待用'] = f'日支{ri_zhi}在{group}局，课传仅见{hit[0]}，待{others[1 - others.index(hit[0])]}值日方成'
                break
        if he_items:
            result['八杀明细'].append({
                '杀': '合', '出现': list(set(he_items)), '状态': '吉', '评分': self.BA_SHA_JIXIONG.get('合', 3),
                '断语': '合乃完成，和合圆成'
            })
        else:
            result['八杀明细'].append({
                '杀': '合', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传中无特殊合局'
            })

        # 3. 鬼（克日干者）
        gui_items = []
        for chuan_zhi in sanchuan_list:
            if not chuan_zhi or not ri_gan_wx:
                continue
            chuan_wx = self.DIZHI_WU_XING.get(chuan_zhi, '')
            if chuan_wx and self._is_ke(chuan_wx, ri_gan_wx):
                gui_items.append(chuan_zhi)
        if gui_items:
            gui_kong = [z for z in gui_items if z in xun_kong]
            if gui_kong:
                result['八杀明细'].append({
                    '杀': '鬼', '出现': gui_items, '状态': '空亡', '评分': -1,
                    '断语': f'鬼主伤残，但落空亡，凶不为凶'
                })
            else:
                gui_score = self.BA_SHA_JIXIONG.get('鬼', -4)
                gui_note = '鬼主伤残，三传见鬼尤凶'
                if de_present_flag:
                    gui_score = int(gui_score / 2)  # 德神解凶，鬼凶减半
                    gui_note = '鬼主伤残，然德神临传解凶，凶性减半'
                result['八杀明细'].append({
                    '杀': '鬼', '出现': gui_items, '状态': '旺相', '评分': gui_score,
                    '断语': gui_note
                })
        else:
            result['八杀明细'].append({
                '杀': '鬼', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传不见日鬼'
            })

        # 4. 墓
        ri_mu_zhi = self.RI_MU.get(ri_gan, '')
        mu_items = []
        for chuan_zhi in sanchuan_list:
            if chuan_zhi == ri_mu_zhi:
                mu_items.append(chuan_zhi)
        if mu_items:
            mu_kong = [z for z in mu_items if z in xun_kong]
            if mu_kong:
                result['八杀明细'].append({
                    '杀': '墓', '出现': mu_items, '状态': '空亡', '评分': 0,
                    '断语': '墓落空亡，不为害'
                })
            else:
                result['八杀明细'].append({
                    '杀': '墓', '出现': mu_items, '状态': '旺相', '评分': self.BA_SHA_JIXIONG.get('墓', -2),
                    '断语': '墓多暧昧，事不明朗'
                })
        else:
            result['八杀明细'].append({
                '杀': '墓', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传不见墓神'
            })

        # 5. 破
        po_items = []
        for i in range(len(sanchuan_list)):
            for j in range(i + 1, len(sanchuan_list)):
                if sanchuan_list[i] and sanchuan_list[j]:
                    if self.XIANG_PO.get(sanchuan_list[i]) == sanchuan_list[j]:
                        po_items.append(f'{sanchuan_list[i]}破{sanchuan_list[j]}')
        if po_items:
            result['八杀明细'].append({
                '杀': '破', '出现': po_items, '状态': '凶', '评分': self.BA_SHA_JIXIONG.get('破', -2),
                '断语': '破知损坏，物已损伤'
            })
        else:
            result['八杀明细'].append({
                '杀': '破', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传中无相破'
            })

        # 6. 害
        hai_items = []
        for i in range(len(sanchuan_list)):
            for j in range(i + 1, len(sanchuan_list)):
                if sanchuan_list[i] and sanchuan_list[j]:
                    if self.LIU_HAI.get(sanchuan_list[i]) == sanchuan_list[j]:
                        hai_items.append(f'{sanchuan_list[i]}害{sanchuan_list[j]}')
        if hai_items:
            result['八杀明细'].append({
                '杀': '害', '出现': hai_items, '状态': '凶', '评分': self.BA_SHA_JIXIONG.get('害', -1),
                '断语': '害见侵凌，暗中有害'
            })
        else:
            result['八杀明细'].append({
                '杀': '害', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传中无六害'
            })

        # 7. 刑
        xing_items = []
        for i in range(len(sanchuan_list)):
            for j in range(i + 1, len(sanchuan_list)):
                if sanchuan_list[i] and sanchuan_list[j]:
                    if self.XING_MAP.get(sanchuan_list[i]) == sanchuan_list[j]:
                        xing_items.append(f'{sanchuan_list[i]}刑{sanchuan_list[j]}')
        for chuan_zhi in sanchuan_list:
            if chuan_zhi and self.XING_MAP.get(chuan_zhi) == chuan_zhi:
                xing_items.append(f'{chuan_zhi}自刑')
        if xing_items:
            result['八杀明细'].append({
                '杀': '刑', '出现': xing_items, '状态': '凶', '评分': self.BA_SHA_JIXIONG.get('刑', -1),
                '断语': '刑分强弱，官司刑戮'
            })
        else:
            result['八杀明细'].append({
                '杀': '刑', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传中无相刑'
            })

        # 8. 冲
        chong_items = []
        for i in range(len(sanchuan_list)):
            for j in range(i + 1, len(sanchuan_list)):
                if sanchuan_list[i] and sanchuan_list[j]:
                    if self.LIU_CHONG.get(sanchuan_list[i]) == sanchuan_list[j]:
                        chong_items.append(f'{sanchuan_list[i]}冲{sanchuan_list[j]}')
        if chong_items:
            result['八杀明细'].append({
                '杀': '冲', '出现': chong_items, '状态': '凶', '评分': self.BA_SHA_JIXIONG.get('冲', -2),
                '断语': '冲不安宁，动荡冲散'
            })
        else:
            result['八杀明细'].append({
                '杀': '冲', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传中无六冲'
            })

        # 8.5 败（八煞之一：败即沐浴；通解 L1009-1011 十干败位：甲乙败子、丙丁败卯、
        #     戊己败酉、庚辛败午、壬癸败酉；败加干支主败坏衰败。评分 0 记录层，不进 valence）
        bai_zhi = {'甲': '子', '乙': '子', '丙': '卯', '丁': '卯',
                   '戊': '酉', '己': '酉', '庚': '午', '辛': '午',
                   '壬': '酉', '癸': '酉'}.get(ri_gan, '')
        bai_items = [z for z in sanchuan_list if z and z == bai_zhi]
        if bai_items:
            result['八杀明细'].append({
                '杀': '败', '出现': bai_items, '状态': '凶', '评分': 0,
                '断语': f'三传见{ri_gan}日败位{bai_zhi}（沐浴），主败坏衰败'
            })
        else:
            result['八杀明细'].append({
                '杀': '败', '出现': [], '状态': '未现', '评分': 0,
                '断语': '三传不见日败位'
            })

        # 综合评分
        total_score = sum(item.get('评分', 0) for item in result['八杀明细'])
        result['评分'] = total_score
        if total_score >= 10:
            result['吉凶'] = '吉'
            result['描述'] = f'八杀综合评分{total_score}分，德合多见、鬼墓破害刑冲少见，大局吉利'
        elif total_score >= 0:
            result['吉凶'] = '平'
            result['描述'] = f'八杀综合评分{total_score}分，吉凶参半'
        else:
            result['吉凶'] = '凶'
            result['描述'] = f'八杀综合评分{total_score}分，鬼墓破害刑冲多见、德合少见，需谨慎'

        return result

    # ==================== 《壬归》十二气财星分析 ====================

    def get_shi_er_chen(self, ri_gan: str, zhi: str) -> str:
        """
        获取地支相对于天干的长生十二宫状态（简版，用于求财分析）
        
        注意：此为简略版本，以五行长生为准
        木长生在亥、火长生在寅、金长生在巳、水土长生在申
        """
        gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        zhi_wx = self.DIZHI_WU_XING.get(zhi, '')

        chang_sheng_zhi = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}
        di_zhi_order = ['亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌']

        cs_zhi = chang_sheng_zhi.get(gan_wx, '')
        if not cs_zhi or cs_zhi not in di_zhi_order:
            return ''

        cs_idx = di_zhi_order.index(cs_zhi)
        zhi_idx = di_zhi_order.index(zhi) if zhi in di_zhi_order else -1
        if zhi_idx < 0:
            return ''

        offset = (zhi_idx - cs_idx) % 12
        stages = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        if 0 <= offset < len(stages):
            return stages[offset]
        return ''

    def analyze_cai_shi_er_qi(self, ri_gan: str, sanchuan: Dict, month: int) -> Dict:
        """
        十二气财星分析（《壬归》卷之三·干贵求财第一）
        
        分析三传在长生十二宫中的状态，判断财星强弱
        """
        result = {'三传十二气': [], '财星评分': 0, '财象': ''}
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]

        for chuan_name, chuan_zhi in zip(['初传', '中传', '末传'], sanchuan_list):
            if not chuan_zhi:
                continue
            stage = self.get_shi_er_chen(ri_gan, chuan_zhi)
            cai_meaning = self.SHI_ER_QI_CAI.get(stage, '')
            is_ji = stage in self.CAI_SI_JI
            is_xiong = stage in self.CAI_BA_XIONG

            entry = {
                '三传': chuan_name,
                '地支': chuan_zhi,
                '十二气': stage or '未知',
                '求财含义': cai_meaning,
                '吉凶': '吉' if is_ji else ('凶' if is_xiong else '平')
            }
            result['三传十二气'].append(entry)

        # 评分
        score = 0
        for item in result['三传十二气']:
            if item['十二气'] in self.CAI_SI_JI:
                score += self.CAI_SI_JI_SCORE
            elif item['十二气'] in self.CAI_BA_XIONG:
                score += self.CAI_BA_XIONG_SCORE
        result['财星评分'] = score

        if score >= 3:
            result['财象'] = '财星强旺，有利可图'
        elif score >= 0:
            result['财象'] = '财星中性，见机而行'
        else:
            result['财象'] = '财星弱势，不宜妄动'

        return result

    # ==================== 《壬归》身强身弱分析 ====================

    def analyze_shen_qiang_cai_ruo(self, ri_gan: str, ri_zhi: str,
                                    sanchuan: Dict, month: int, sike: List) -> Dict:
        """
        身强身弱与财旺财弱分析（《壬归》卷之三·干贵求财）
        
        原则：财旺必须身强，身弱财强无力可取
             财弱身强，我志虽雄财犹恍惚
        """
        result = {'身强评分': 0, '身强身弱': '', '财星评分': 0, '财旺财弱': '', '身财关系': ''}

        # 身强判断：日干在四季的旺衰 + 日上神是否生扶
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        ri_gan_ws = self._ws(ri_gan_wx, month) if ri_gan_wx else '平'
        shen_score = self.get_wang_shuai_value(ri_gan_ws)

        # 日上神生日干则加分
        if sike and len(sike) >= 2 and hasattr(sike[0], '__getitem__') and len(sike[0]) > 1:
            gan_shang_shen = sike[0][1]
            gan_shang_wx = self.DIZHI_WU_XING.get(gan_shang_shen, '')
            if ri_gan_wx and gan_shang_wx and self._is_sheng(gan_shang_wx, ri_gan_wx):
                shen_score += 2
            if ri_gan_wx and gan_shang_wx and self._is_ke(gan_shang_wx, ri_gan_wx):
                shen_score -= 2

        # 三传助身
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]
        for chuan_zhi in sanchuan_list:
            if chuan_zhi and ri_gan_wx:
                chuan_wx = self.DIZHI_WU_XING.get(chuan_zhi, '')
                if chuan_wx and self._is_sheng(chuan_wx, ri_gan_wx):
                    shen_score += 1

        result['身强评分'] = shen_score
        if shen_score >= 4:
            result['身强身弱'] = '身强'
        elif shen_score >= 1:
            result['身强身弱'] = '身偏强'
        elif shen_score >= -1:
            result['身强身弱'] = '身中平'
        elif shen_score >= -3:
            result['身强身弱'] = '身偏弱'
        else:
            result['身强身弱'] = '身弱'

        # 财星评分：三传中妻财 + 日支妻财
        cai_score = 0
        for chuan_zhi in sanchuan_list:
            if chuan_zhi and ri_gan_wx:
                chuan_wx = self.DIZHI_WU_XING.get(chuan_zhi, '')
                if chuan_wx and self._is_ke(ri_gan_wx, chuan_wx):
                    cai_score += 2
        # 日支为妻财则加分
        zhi_wx = self.DIZHI_WU_XING.get(ri_zhi, '')
        if ri_gan_wx and zhi_wx and self._is_ke(ri_gan_wx, zhi_wx):
            cai_score += 1

        result['财星评分'] = cai_score
        if cai_score >= 4:
            result['财旺财弱'] = '财旺'
        elif cai_score >= 1:
            result['财旺财弱'] = '财偏旺'
        elif cai_score >= -1:
            result['财旺财弱'] = '财中平'
        else:
            result['财旺财弱'] = '财弱'

        # 身财关系判断
        shen = result['身强身弱']
        cai = result['财旺财弱']
        if '强' in shen and '旺' in cai:
            result['身财关系'] = '身强财旺，求谋顺利，一往直前'
        elif '强' in shen and ('弱' in cai or '中平' in cai):
            result['身财关系'] = '身强财弱，我志虽雄，财犹恍惚'
        elif ('弱' in shen or '中平' in shen) and '旺' in cai:
            result['身财关系'] = '财旺身弱，无力承担，反致多忧'
        elif '弱' in shen and '弱' in cai:
            result['身财关系'] = '身弱财弱，两相困顿，宜守旧'
        else:
            result['身财关系'] = '身财中平，见机而行'

        return result

    # ==================== 《壬归》综合分析总结 ====================

    def _build_ren_gui_summary(self, all_analysis: Dict) -> str:
        """构建壬归综合总结文本"""
        parts = []

        # 四课加临
        sike_qi = all_analysis.get('四课加临', {})
        if sike_qi:
            parts.append(f"【四课加临】{sike_qi.get('描述', '')}")

        # 用神五气
        yong_shen = all_analysis.get('用神分析', {})
        if yong_shen:
            ys_desc = f"【用神】发用{yong_shen.get('用神地支', '')}"
            ys_desc += f"，旺衰为{yong_shen.get('旺衰', '')}"
            ys_desc += f"，五气{yong_shen.get('五气吉凶', '')}"
            if yong_shen.get('日用关系'):
                ys_desc += f"，{yong_shen['日用关系']}"
            parts.append(ys_desc)

        # 三传制救
        sanchuan_zhi_jiu = all_analysis.get('三传制救', {})
        if sanchuan_zhi_jiu:
            sc_desc = f"【三传制救】{sanchuan_zhi_jiu.get('气之趋势', '')}"
            if sanchuan_zhi_jiu.get('始终吉凶'):
                sc_desc += f"，{sanchuan_zhi_jiu['始终吉凶']}"
            if sanchuan_zhi_jiu.get('制救分析'):
                sc_desc += f"，制救：{'; '.join(sanchuan_zhi_jiu['制救分析'])}"
            parts.append(sc_desc)

        # 贵神吉凶
        gui_shen = all_analysis.get('贵神吉凶', {})
        if gui_shen:
            gs_desc = "【贵神】"
            if gui_shen.get('天乙状态'):
                gs_desc += gui_shen['天乙状态']
            parts.append(gs_desc)

        # 八杀
        ba_sha = all_analysis.get('八杀分析', {})
        if ba_sha:
            parts.append(f"【八杀】{ba_sha.get('描述', '')}")

        # 十二气财星
        shi_er_qi = all_analysis.get('十二气财星', {})
        if shi_er_qi:
            parts.append(f"【十二气财星】{shi_er_qi.get('财象', '')}")

        # 身强身弱
        shen_qiang = all_analysis.get('身强身弱分析', {})
        if shen_qiang:
            sq_desc = f"【身财】{shen_qiang.get('身强身弱', '')}，{shen_qiang.get('财旺财弱', '')}"
            if shen_qiang.get('身财关系'):
                sq_desc += f"，{shen_qiang['身财关系']}"
            parts.append(sq_desc)

        if parts:
            return '\n'.join(parts)
        return ''

    def _build_summary(self, results: Dict) -> str:
        """构建综合描述文本"""
        parts = []

        xk = results.get('旬空分析', results.get('旬空', ''))
        if isinstance(xk, dict):
            xk_zhi = xk.get('空亡地支', xk.get('旬空地支', []))
            if xk_zhi:
                parts.append(f"旬空：{','.join(xk_zhi) if isinstance(xk_zhi, list) else xk_zhi}")
        elif isinstance(xk, list):
            if xk:
                parts.append(f"旬空：{','.join(xk)}")

        wang_shuai = results.get('旺衰分析', {})
        if wang_shuai:
            wang_items = []
            for label, zhi in [('日干', results.get('日干', '')),
                               ('日支', results.get('日支', '')),
                               ('初传', results.get('初传', '')),
                               ('中传', results.get('中传', '')),
                               ('末传', results.get('末传', ''))]:
                if zhi and label in wang_shuai:
                    ws = wang_shuai.get(label, '')
                    if ws:
                        wang_items.append(f"{label}({ws})")
            if wang_items:
                parts.append(f"旺衰：{' '.join(wang_items)}")

        liuqin = results.get('六亲分析', [])
        if liuqin:
            liuqin_strs = []
            for lq in liuqin:
                if isinstance(lq, dict) and lq.get('地支') and lq.get('六亲'):
                    liuqin_strs.append(f"{lq['地支']}({lq['六亲']})")
            if liuqin_strs:
                parts.append(f"六亲：{' '.join(liuqin_strs)}")

        guanxi = results.get('三传与干支关系', results.get('三传关系', []))
        if guanxi:
            if isinstance(guanxi, list):
                guanxi_strs = [r if isinstance(r, str) else str(r) for r in guanxi[:5]]
                if guanxi_strs:
                    parts.append(f"关系：{' '.join(guanxi_strs)}")

        return '；'.join(parts) if parts else ''

    def analyze(self, ri_gan: str, ri_zhi: str, sanchuan: Dict,
                sike: List, tiandi_pan: Dict = None,
                yue_jiang: str = '', shi_chen: str = '',
                lunar_month: int = None, nian_zhi: str = None, yuejian_zhi: str = None,
                ri_gan_zhi: str = None) -> Dict:
        """
        壬归综合分析入口
        
        整合所有分析维度：
        1. 旬空
        2. 四季旺衰
        3. 神煞
        4. 六亲
        5. 刑冲克害三合六合
        6. 四课加临（壬归·卷之一·一）
        7. 用神五气（壬归·卷之一·二）
        8. 三传制救（壬归·卷之一·三）
        9. 贵神吉凶（壬归·卷之一·四）
        10. 八杀体系（壬归·卷之一·五）
        11. 十二气财星（壬归·卷之三）
        12. 身强身弱（壬归·卷之三）
        """
        if not ri_gan_zhi:
            ri_gan_zhi = ri_gan + ri_zhi

        month = lunar_month or 1
        self._yuejian = yuejian_zhi
        result = {
            '日干': ri_gan,
            '日支': ri_zhi,
            '日干支': ri_gan_zhi,
            '月份': month
        }

        # 1. 旬空分析
        xun_kong_zhi = self.get_xun_kong(ri_gan_zhi)
        result['旬空'] = xun_kong_zhi
        result['旬空分析'] = {'空亡地支': xun_kong_zhi}

        # 2. 四季旺衰
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        ri_zhi_wx = self.DIZHI_WU_XING.get(ri_zhi, '')
        gan_ws = self._ws(ri_gan_wx, month) if ri_gan_wx else '平'
        zhi_ws = self._ws(ri_zhi, month)
        _yl = self.YUEJIAN_TO_YUELING.get(yuejian_zhi) if yuejian_zhi else None
        _season_disp = {'木': '春', '火': '夏', '金': '秋', '水': '冬', '土': '四季'}.get(_yl) or self.get_season(month)
        result['旺衰分析'] = {
            '日干': gan_ws,
            '日支': zhi_ws,
            '日干五行': ri_gan_wx,
            '季节': _season_disp
        }

        # 3. 神煞
        shen_sha_result = {}
        try:
            shen_sha_result = self.shen_sha_calc.calculate_all_shen_sha(
                ri_gan=ri_gan,
                ri_zhi=ri_zhi,
                lunar_month=lunar_month or 1,
                nian_zhi=nian_zhi or '子',
                ri_gan_zhi=ri_gan_zhi or (ri_gan + ri_zhi)
            )
        except Exception:
            pass
        result['神煞'] = shen_sha_result

        # 4. 六亲
        sanchuan_list = [sanchuan.get(n, '') for n in ['初传', '中传', '末传']]
        all_zhi_for_liuqin = [z for z in sanchuan_list if z] + [ri_zhi]
        liuqin_result = self.get_liuqin_analysis(ri_gan, all_zhi_for_liuqin)
        result['六亲分析'] = liuqin_result

        # 5. 三传与干支关系（刑冲克害三合六合）
        sanchuan_ganxi = []
        for chuan_zhi in sanchuan_list:
            if chuan_zhi:
                rel_gan = self.analyze_pair_relationship(chuan_zhi, ri_gan, '三传', '日干')
                if rel_gan.get('关系'):
                    for r in rel_gan['关系']:
                        sanchuan_ganxi.append(f'{chuan_zhi}与日干{ri_gan}:{r}')
                rel_zhi = self.analyze_pair_relationship(chuan_zhi, ri_zhi, '三传', '日支')
                if rel_zhi.get('关系'):
                    for r in rel_zhi['关系']:
                        sanchuan_ganxi.append(f'{chuan_zhi}与日支{ri_zhi}:{r}')
        result['三传关系'] = sanchuan_ganxi

        # 6. 四课加临（壬归·卷之一·一）
        result['四课加临'] = self.analyze_sike_qi(ri_gan, ri_zhi, sike)

        # 6.5 正时八门·先锋门（第三章 L3359-3360；记录层）
        try:
            result['正时分析'] = self._analyze_zheng_shi(ri_gan, ri_zhi, shi_chen)
        except Exception:
            result['正时分析'] = {}

        # 6.6 遁干聚散（第三章 L3308-3344；记录层）
        try:
            result['遁干聚散'] = self._analyze_jv_san(ri_gan, sanchuan_list, sike)
        except Exception:
            result['遁干聚散'] = {}

        # 7. 用神五气（壬归·卷之一·二）
        yong_shen_zhi = ''
        if sike and hasattr(sike[0], '__getitem__') and len(sike[0]) > 1:
            yong_shen_zhi = sike[0][1]
        if not yong_shen_zhi and sanchuan_list:
            yong_shen_zhi = sanchuan_list[0]
        gan_shang_shen = sike[0][1] if sike and len(sike) >= 1 and hasattr(sike[0], '__getitem__') and len(sike[0]) > 1 else ''
        zhi_shang_shen = sike[2][1] if sike and len(sike) >= 3 and hasattr(sike[2], '__getitem__') and len(sike[2]) > 1 else ''
        result['用神分析'] = self.analyze_yong_shen(
            yong_shen_zhi, ri_gan, month, sike,
            gan_shang_shen, zhi_shang_shen, tiandi_pan
        )

        # 7.5 发用六断（第三章 L3383 发用歌诀；记录层）
        try:
            result['发用六断'] = self._analyze_fa_yong_liu_duan(
                ri_gan, ri_zhi, shi_chen, sanchuan_list, yong_shen_zhi, month)
        except Exception:
            result['发用六断'] = {}

        # 8. 三传制救（壬归·卷之一·三）
        result['三传制救'] = self.analyze_sanchuan_zhi_jiu(sanchuan, ri_gan, ri_zhi, sike, month)

        # 8.5 三传阴神分析（六壬深度推理核心）
        result['阴神分析'] = self.analyze_yin_shen(sanchuan, tiandi_pan, ri_gan)

        # 9. 贵神吉凶（壬归·卷之一·四）
        result['贵神吉凶'] = self.analyze_gui_shen_ji_xiong(sanchuan, result.get('神煞', {}) or {})

        # 10. 八杀体系（壬归·卷之一·五）
        result['八杀分析'] = self.analyze_ba_sha(ri_gan, ri_zhi, sanchuan, sike, month, ri_gan_zhi)

        # 11. 十二气财星（壬归·卷之三）
        result['十二气财星'] = self.analyze_cai_shi_er_qi(ri_gan, sanchuan, month)

        # 12. 身强身弱（壬归·卷之三）
        result['身强身弱分析'] = self.analyze_shen_qiang_cai_ruo(ri_gan, ri_zhi, sanchuan, month, sike)

        # 综合总结
        result['综合描述'] = self._build_summary(result)
        result['壬归总结'] = self._build_ren_gui_summary(result)

        return result