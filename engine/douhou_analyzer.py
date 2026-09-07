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
try:
    from liuxiang_liuti_system import LiuXiangLiuTiCalculator
except ImportError:
    from engine.liuxiang_liuti_system import LiuXiangLiuTiCalculator


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
        # 权威口径（《仪度六壬选日要诀》）：元辰=同我者（化气五行与山家相同），
        # 其余按五行关系推导。例：甲山（水）元辰=丙辛（丙辛化水）；艮山（木）元辰=丁壬（丁壬化木）
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
            # 星曜判定：《仪度六壬选日要诀》同我者为元辰，化气五行与山家比较
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
        
        # 【2026-09-07 前端补齐·斗首扣分原因】六相分析断语（judge_kege_jixiong 内含
        #   "破鬼一位，不宜/武财关鬼格/廉子一位"等加减分明细），原仅取分数、断语被丢弃，
        #   导致前端无法解释"斗首为何只有 74 分"（如破鬼无制反噬 -20）。
        #   现在透传为独立字段 + 合并进吉凶断语，供前端叙事展示。
        _lx_jx, _lx_score, _lx_duanyu = self.liuxiang_calculator.judge_kege_jixiong(liuxiang_analysis)
        kege_result['六相断语'] = _lx_duanyu
        kege_result['扣分原因'] = [d for d in _lx_duanyu if any(
            k in d for k in ('破鬼', '贪官', '不宜', '凶', '需制伏', '重见'))]
        _seen = set(kege_result['吉凶断语'])
        kege_result['吉凶断语'] = kege_result['吉凶断语'] + [d for d in _lx_duanyu if d not in _seen]

        # 【2026-09-07 前端补齐·月柱凶曜制化扣分】_calculate_score 内"月柱贪官/破鬼且
        #   无廉贞制化、武财<2"额外 -10（与六相断语独立），此扣分原无任何断语说明，
        #   现在显式检测并追加（如 2034-06-15 申时：月柱破鬼未制 → -10，与六相破鬼-10合计-20）。
        _mz_info = liuxiang_analysis.get('四柱六相', {}).get('月柱', {})
        _mz_star = _mz_info.get('六相', '') if isinstance(_mz_info, dict) else ''
        if _mz_star in ('贪官', '破鬼'):
            _has_lz = star_counts.get('廉贞', 0) > 0
            _has_wc2 = star_counts.get('武财', 0) >= 2
            if not _has_lz and not _has_wc2:
                _mz_reason = f'月柱带{_mz_star}且无廉贞/双武财制化 → 额外-10'
                if _mz_reason not in kege_result['扣分原因']:
                    kege_result['扣分原因'].append(_mz_reason)
                if _mz_reason not in kege_result['吉凶断语']:
                    kege_result['吉凶断语'].append(_mz_reason)
        
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

        # ── 补充格局（《斗首启用篇》/要诀知识库 ZR_09_01、ZR_10_02）──
        # 全元联曜格：四柱天干全元辰 且 地支全临元辰（山家）五行长生位
        if star_counts.get('元辰', 0) >= 4:
            changsheng = self.WU_XING_WANG_SHUAI.get(shan_wuxing, {}).get('长生', '')
            zhis = [sizhu.get(p, '')[-1:] for p in ['年柱', '月柱', '日柱', '时柱'] if sizhu.get(p)]
            if changsheng and zhis and all(z == changsheng for z in zhis):
                patterns.append({
                    '格局名称': '全元联曜格',
                    '描述': '四元辰得四长生，十年身到凤凰池',
                    '吉凶': '吉',
                    '条件': f'四柱元辰皆临{changsheng}长生'
                })
            else:
                patterns.append({
                    '格局名称': '四元大吉格',
                    '描述': '四柱全元辰，元辰会一家',
                    '吉凶': '吉',
                    '条件': '元辰四现'
                })

        # 三元三武一廉格（第一吉课）
        if (star_counts.get('元辰', 0) == 3 and star_counts.get('廉贞', 0) >= 1) or \
           (star_counts.get('武财', 0) == 3 and star_counts.get('廉贞', 0) >= 1):
            patterns.append({
                '格局名称': '三元三武一廉格',
                '描述': '三元一廉或三武一廉，第一吉课',
                '吉凶': '吉',
                '条件': f"元辰{star_counts.get('元辰',0)}、武财{star_counts.get('武财',0)}、廉贞{star_counts.get('廉贞',0)}"
            })

        # 三元一武格
        if star_counts.get('元辰', 0) == 3 and star_counts.get('武财', 0) == 1:
            patterns.append({
                '格局名称': '三元一武格',
                '描述': '三元配一武，大吉之课',
                '吉凶': '吉',
                '条件': '元辰三现、武财一见'
            })

        # 三重贪官格（文档口径：三柱以上贪官）
        if star_counts.get('贪官', 0) >= 3:
            patterns.append({
                '格局名称': '三重贪官格',
                '描述': '贪官三现以上，克元辰大凶',
                '吉凶': '凶',
                '条件': f"贪官{star_counts['贪官']}次"
            })

        # 廉子重见格（文档口径：两柱以上廉贞，不要求元辰≤1）
        if star_counts.get('廉贞', 0) >= 2 and star_counts.get('元辰', 0) > 1:
            patterns.append({
                '格局名称': '廉子重见格',
                '描述': '廉子重见，伤克子孙损父母',
                '吉凶': '凶',
                '条件': f"廉贞{star_counts['廉贞']}次"
            })

        # ═════════════════════════════════════════
        #  四柱结构格局（斗首择日经典格，与五星课格并列）
        #  来源：多部择日典籍统一口径（zgjm.org/hkfengshui.com/gnkanyu.net/d02.cn）
        #  这些是四柱干支结构本身的格局，不依赖五星（元辰/武财等）计数
        # ═══════════════════════════════════════════
        self._judge_sizhu_structure_patterns(patterns, sizhu)

        return patterns

    def _judge_sizhu_structure_patterns(self, patterns: List[Dict], sizhu: Dict):
        """检测四柱干支结构格局（天地同流/一气/五常/秀气/三合/方局/三奇等）。"""
        # 提取四柱干支
        nz = sizhu.get('年柱', '')
        yz = sizhu.get('月柱', '')
        rz = sizhu.get('日柱', '')
        sz = sizhu.get('时柱', '')

        if not (nz and yz and rz and sz):
            return  # 四柱不全则跳过

        n_gan, n_zhi = nz[0], nz[-1]
        y_gan, y_zhi = yz[0], yz[-1]
        r_gan, r_zhi = rz[0], rz[-1]
        s_gan, s_zhi = sz[0], sz[-1]

        gans = [n_gan, y_gan, r_gan, s_gan]
        zhis = [n_zhi, y_zhi, r_zhi, s_zhi]
        gan_set = set(gans)
        zhi_set = set(zhis)

        # ── Tier 1：天地同流格（最上格，极难得）──
        # 年月日时四柱干支完全相同。仅10格可能：
        # 甲戌、乙酉、丙申、丁未、戊午、己巳、庚辰、辛卯、壬寅、癸亥
        if len(gan_set) == 1 and len(zhi_set) == 1:
            ganzhi = f"{gans[0]}{zhis[0]}"
            patterns.append({
                '格局名称': '天地同流格',
                '描述': '四柱干支完全相同，最为上格，六十年仅4-5次',
                '吉凶': '大吉',
                '条件': f'四柱皆为{ganzhi}',
                '类别': '四柱结构'
            })

        # ── Tier 2：一气格 ──
        # 天元一气格：四柱天干相同，地支不同
        if len(gan_set) == 1 and len(zhi_set) > 1:
            patterns.append({
                '格局名称': '天元一气格',
                '描述': '四柱天干相同而地支不同，气势专一',
                '吉凶': '吉',
                '条件': f"四干皆{gans[0]}",
                '类别': '四柱结构'
            })
        # 地支一气格：四柱地支相同，天干不同
        if len(zhi_set) == 1 and len(gan_set) > 1:
            patterns.append({
                '格局名称': '地支一气格',
                '描述': '四柱地支相同而天干不同，根基稳固',
                '吉凶': '吉',
                '条件': f"四支皆{zhis[0]}",
                '类别': '四柱结构'
            })

        # ── Tier 3：三朋格（次于一气）──
        from collections import Counter
        gan_cnt = Counter(gans)
        zhi_cnt = Counter(zhis)
        for g, c in gan_cnt.items():
            if c >= 3:
                patterns.append({
                    '格局名称': '天干三朋格',
                    '描述': '三柱以上天干相同，朋党合力',
                    '吉凶': '吉',
                    '条件': f'{g}干出现{c}次',
                    '类别': '四柱结构'
                })
        for z, c in zhi_cnt.items():
            if c >= 3:
                patterns.append({
                    '格局名称': '地支三朋格',
                    '描述': '三柱以上地支相同，地气凝聚',
                    '吉凶': '吉',
                    '条件': f'{z}支出现{c}次',
                    '类别': '四柱结构'
                })

        # ── Tier 4：五常格（日干主导的地支三合局全备）──
        wuchang_map = {
            ('甲', '乙'): ('曲直格', ['亥', '卯', '未'], '木'),
            ('丙', '丁'): ('炎上格', ['寅', '午', '戌'], '火'),
            ('庚', '辛'): ('从革格', ['巳', '酉', '丑'], '金'),
            ('壬', '癸'): ('润下格', ['申', '子', '辰'], '水'),
            ('戊', '己'): ('稼穑格', ['辰', '戌', '丑', '未'], '土'),
        }
        for (g1, g2), (name, req_zhis, wx) in wuchang_map.items():
            if r_gan in (g1, g2):
                if all(z in zhis for z in req_zhis):
                    patterns.append({
                        '格局名称': name,
                        '描述': f'五常之{wx}格，{name}成局',
                        '吉凶': '吉',
                        '条件': f'日干{r_gan}属{wx}，地支含{"".join(req_zhis)}',
                        '类别': '四柱结构'
                    })

        # ── Tier 5：四方秀气格（日干+地支连方三支）──
        xiuxiu_map = {
            ('甲', '乙'): ('东方秀气格', ['寅', '卯', '辰']),
            ('丙', '丁'): ('南方秀气格', ['巳', '午', '未']),
            ('庚', '辛'): ('西方秀气格', ['申', '酉', '戌']),
            ('壬', '癸'): ('北方秀气格', ['亥', '子', '丑']),
        }
        for (g1, g2), (name, req_zhis) in xiuxiu_map.items():
            if r_gan in (g1, g2):
                if all(z in zhis for z in req_zhis):
                    patterns.append({
                        '格局名称': name,
                        '描述': f'地支连方成{name}，秀气流行',
                        '吉凶': '吉',
                        '条件': f'日干{r_gan}，地支含{"".join(req_zhis)}',
                        '类别': '四柱结构'
                    })

        # ── Tier 6：三合会局（地支含完整三合）──
        sanhe_map = {
            '申子辰水局': (['申', '子', '辰'], '水'),
            '亥卯未木局': (['亥', '卯', '未'], '木'),
            '寅午戌火局': (['寅', '午', '戌'], '火'),
            '巳酉丑金局': (['巳', '酉', '丑'], '金'),
        }
        for name, (req_zhis_sh, wx) in sanhe_map.items():
            if all(z in zhis for z in req_zhis_sh):
                patterns.append({
                    '格局名称': name,
                    '描述': f'地支三合{wx}局成',
                    '吉凶': '吉',
                    '条件': f'地支含{"".join(req_zhis_sh)}',
                    '类别': '四柱结构'
                })

        # ── Tier 7：会成方局（地支连续三方）──
        fangju_map = {
            '东方方局': ['寅', '卯', '辰'],
            '南方方局': ['巳', '午', '未'],
            '西方方局': ['申', '酉', '戌'],
            '北方方局': ['亥', '子', '丑'],
        }
        for name, req_z in fangju_map.items():
            if all(z in zhis for z in req_z):
                patterns.append({
                    '格局名称': name,
                    '描述': f'地支连会成{name}，一方之气纯厚',
                    '吉凶': '吉',
                    '条件': f'地支含{"".join(req_z)}',
                    '类别': '四柱结构'
                })

        # ── Tier 8：官旺局（地支含临官+帝旺位）──
        guanwang_map = {
            '水官旺': (['亥', '子'], '水'),
            '木官旺': (['寅', '卯'], '木'),
            '火官旺': (['巳', '午'], '火'),
            '金官旺': (['申', '酉'], '金'),
        }
        for name, (req_z, wx) in guanwang_map.items():
            if all(z in zhis for z in req_z):
                patterns.append({
                    '格局名称': name,
                    '描述': f'{wx}临官帝旺并见，官旺得地',
                    '吉凶': '吉',
                    '条件': f'地支含{"".join(req_z)}',
                    '类别': '四柱结构'
                })

        # ── Tier 9：三奇格 ──
        tiandi_sanqi = {'甲', '戊', '庚'}
        renyuan_sanqi = {'乙', '丙', '丁'}
        if tiandi_sanqi.issubset(set(gans)):
            patterns.append({
                '格局名称': '天德三奇格(甲戊庚)',
                '描述': '天德三奇并见，奇数逢吉',
                '吉凶': '吉',
                '条件': '天干含甲戊庚',
                '类别': '四柱结构'
            })
        if renyuan_sanqi.issubset(set(gans)):
            patterns.append({
                '格局名称': '人元三奇格(乙丙丁)',
                '描述': '人元三奇并见，三光普照',
                '吉凶': '吉',
                '条件': '天干含乙丙丁',
                '类别': '四柱结构'
            })
        # _judge_sizhu_structure_patterns 结束

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
            if pattern['吉凶'] in ('吉', '大吉'):
                name = pattern['格局名称']
                # ── 四柱结构格局评分（高优先级）──
                if '天地同流' in name:
                    score += 15
                elif '天元一气' in name or '地支一气' in name:
                    score += 8
                elif '三朋' in name:
                    score += 5
                elif any(x in name for x in ['曲直', '炎上', '从革', '润下', '稼穑']):
                    score += 6
                elif '秀气' in name:
                    score += 5
                elif '三合' in name and '局' in name:
                    score += 4
                elif '方局' in name:
                    score += 4
                elif '官旺' in name:
                    score += 3
                elif '三奇' in name:
                    score += 4
                # ── 五星课格评分（原有）──
                elif '三元辰' in name:
                    score += 5
                elif '三武格' in name:
                    score += 5
                elif '武财生元' in name:
                    score += 5
                elif '全元联曜' in name:
                    score += 10
                elif '三元三武一廉' in name:
                    score += 12
                elif '三元一武' in name:
                    score += 7
                elif '四元大吉' in name:
                    score += 8
            else:
                name = pattern['格局名称']
                if '贪官克元' in name:
                    score -= 5
                elif '破鬼泄气' in name:
                    score -= 5
                elif '廉子伤克' in name:
                    score -= 5
                elif '廉子重见' in name:
                    score -= 5
                elif '三重贪官' in name:
                    score -= 8
        
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
        
        # 2026-08-21 口径修复（消除"大凶并列官禄双全"式矛盾）：
        # ① 六亲凶格命中时，官旺断语改斗首口径（书"贪官墓绝上，庶吉仕凶评"——贪官得地反为忌）；
        # ② 总凶（score<50）时，四柱结构吉格断语降级标注"不抵总凶"。
        _LIUQIN_XIONG = ('贪官克元', '破鬼泄气', '廉子伤克', '廉子重见', '三重贪官')
        _hit_lq_xiong = any(any(k in p.get('格局名称', '') for k in _LIUQIN_XIONG) for p in patterns)
        _zong_xiong = score < 50

        for pattern in patterns:
            name = pattern['格局名称']
            _before = len(duanyu)
            _skip_demote = False
            # ── 四柱结构格局断语 ──
            if '天地同流' in name:
                duanyu.append("天地同流，四柱纯一，最为上格，甚为难得")
            elif '天元一气' in name:
                duanyu.append("天元一气，干神专一，气势贯通")
            elif '地支一气' in name:
                duanyu.append("地支一气，根基稳固，万难不拔")
            elif '天干三朋' in name:
                duanyu.append(f"天干三朋，{pattern.get('条件','')}")
            elif '地支三朋' in name:
                duanyu.append(f"地支三朋，{pattern.get('条件','')}")
            elif '曲直' in name:
                duanyu.append("曲直格成，仁德之风，木气荣发")
            elif '炎上' in name:
                duanyu.append("炎上格成，礼明之象，火势炎炎")
            elif '从革' in name:
                duanyu.append("从革格成，义刚之质，金声铿锵")
            elif '润下' in name:
                duanyu.append("润下格成，智深之德，水润万物")
            elif '稼穑' in name:
                duanyu.append("稼穑格成，信厚之土，载物生生")
            elif '秀气' in name:
                duanyu.append(f"{name}，秀气流行，一方之气纯粹")
            elif '水局' in name or '木局' in name or '火局' in name or '金局' in name:
                duanyu.append(f"{name}成，三合会局，气势团聚")
            elif '方局' in name:
                duanyu.append(f"{name}，连方成局，一方纯厚")
            elif '官旺' in name:
                if _hit_lq_xiong:
                    duanyu.append(f"{name}，临官帝旺得地——斗首以煞星得地为忌（书云\"贪官墓绝上，庶吉仕凶评\"），不抵六亲凶格")
                    _skip_demote = True
                else:
                    duanyu.append(f"{name}，临官帝旺得地，官禄双全")
            elif '天德三奇' in name:
                duanyu.append("天德三奇(甲戊庚)，奇数逢吉，贵人照命")
            elif '人元三奇' in name:
                duanyu.append("人元三奇(乙丙丁)，三光普照，福泽绵长")
            # ── 五星课格断语（原有）──
            elif '三元辰' in name:
                duanyu.append("三元辰格，家业兴隆，子孙昌盛")
            elif '三武格' in name:
                duanyu.append("三武格，财源广进，利市三倍")
            elif '贪官克元' in name:
                duanyu.append("贪官克元，家道中落，人丁不旺")
            elif '破鬼泄气' in name:
                duanyu.append("破鬼泄气，精气耗损，诸事不利")
            elif '廉子伤克' in name:
                duanyu.append("廉子重见，伤克子孙，人丁稀少")
            # 2026-08-21 总凶降级：四柱结构吉格断语标注"不抵总凶"，避免与大凶总评并列误导
            if _zong_xiong and not _skip_demote and len(duanyu) > _before                     and pattern.get('吉凶') == '吉' and pattern.get('类别') == '四柱结构':
                _ln = duanyu.pop()
                duanyu.append('（结构' + name + '，不抵总凶）' + _ln)
        
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
