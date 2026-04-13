#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 综合评价系统 - 整合版

整合斗首、演禽、六壬三大模块的课格课体断语
重点：贵人禄马与属相、事业的关联评价

基于《仪度六壬选日要诀》完整理论：
- 九宗门：仅作为起课法，不直接判断吉凶
- 64课经：判断吉凶的核心依据
- 毕法赋：100条规则，提供精细断语
- 禄马贵人断语：求官/求财/求富贵/求文昌/求子/求英豪
"""

import json
import requests
from typing import Dict, List, Optional


class AIEvaluation:
    """AI 综合评价类"""

    DIZHI_SHUXIANG = {
        '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
        '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
        '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
    }

    SANHE = {
        '子': ['申', '辰'], '丑': ['巳', '酉'], '寅': ['午', '戌'],
        '卯': ['亥', '未'], '辰': ['子', '申'], '巳': ['丑', '酉'],
        '午': ['寅', '戌'], '未': ['卯', '亥'], '申': ['子', '辰'],
        '酉': ['丑', '巳'], '戌': ['寅', '午'], '亥': ['卯', '未'],
    }

    LIUCHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }

    HANGYE_BEST = {
        '元辰': ['官府', '军警', '管理', '金融投资'],
        '武财': ['金融投资', '房地产', '商业贸易'],
        '廉贞': ['文化教育', '演艺娱乐', '医疗健康'],
        '贪官': ['制造业', '加工业', '技术工程'],
        '破鬼': ['农业', '养殖业', '餐饮服务']
    }

    def __init__(self, enable_ai=False, api_key=""):
        self.enable_ai = enable_ai
        self.api_key = api_key
        self.model = "qwen-turbo"
        self.ai_available = False
        if self.enable_ai and self.api_key:
            self.ai_available = True

        self.kejing_64 = self._load_64ke_rules()
        self.bifa_rules = self._load_bifa_rules()
        self.kekeduanyu = self._load_kekeduanyu()

    def _load_64ke_rules(self) -> Dict:
        """加载64课经规则"""
        try:
            from core_modules.engine.daliuren_64ke_rules import KE_JING_64, get_ke_jing_by_name
            return {
                'data': KE_JING_64,
                'get_by_name': get_ke_jing_by_name
            }
        except ImportError:
            return None

    def _load_bifa_rules(self) -> Dict:
        """加载毕法赋规则"""
        try:
            from zongmen.bifa_rules_engine_v5 import BiFaRulesMatcherV5
            return {'matcher_class': BiFaRulesMatcherV5}
        except ImportError:
            return None

    def _load_kekeduanyu(self) -> Dict:
        """加载日课断语库"""
        try:
            from engine.kekeduanyu import KeKeDuanyu, SizhuAnalyzer
            return {'KeKeDuanyu': KeKeDuanyu, 'SizhuAnalyzer': SizhuAnalyzer}
        except ImportError:
            return None

    def generate_evaluation(self, data: Dict) -> str:
        """生成综合评价"""
        parts = []

        parts.append(self._generate_basic_info(data))
        parts.append(self._generate_doushou_evaluation(data))
        parts.append(self._generate_zongmen_info(data))
        parts.append(self._generate_64kejing_evaluation(data))
        parts.append(self._generate_bifa_evaluation(data))
        parts.append(self._generate_yanqin_evaluation(data))
        parts.append(self._generate_luma_guiren_evaluation(data))
        parts.append(self._generate_kekeduanyu_evaluation(data))
        parts.append(self._generate_lianzi_evaluation(data))
        parts.append(self._generate_wucai_evaluation(data))
        parts.append(self._generate_tangan_evaluation(data))
        parts.append(self._generate_hunyin_evaluation(data))
        parts.append(self._generate_pougui_evaluation(data))
        parts.append(self._generate_kekedi_evaluation(data))
        parts.append(self._generate_xunkong_evaluation(data))
        parts.append(self._generate_wenxue_evaluation(data))
        parts.append(self._generate_yidu_evaluation(data))
        parts.append(self._generate_zhuming_evaluation(data))
        parts.append(self._generate_ziqi_evaluation(data))
        parts.append(self._generate_shuxiang_evaluation(data))
        parts.append(self._generate_hangye_evaluation(data))
        parts.append(self._generate_ai_evaluation(data))

        return '\n'.join([p for p in parts if p])

    def _generate_basic_info(self, data: Dict) -> str:
        """生成基本信息"""
        parts = []
        parts.append("=" * 60)
        parts.append("【课格综合评价】")
        parts.append("=" * 60)

        mountain = data.get('mountain', '') or data.get('坐山', '')
        sizhu = data.get('sizhu', {})
        year_zhu = sizhu.get('年柱', '') or data.get('年柱', '')
        month_zhu = sizhu.get('月柱', '') or data.get('月柱', '')
        day_zhu = sizhu.get('日柱', '') or data.get('日柱', '')
        hour_zhu = sizhu.get('时柱', '') or data.get('时柱', '')

        parts.append(f"\n坐山：{mountain}")
        parts.append(f"四柱：{year_zhu} {month_zhu} {day_zhu} {hour_zhu}")

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')
        if doushou_keti:
            parts.append(f"斗首课格：{doushou_keti}")

        zongmen = data.get('zongmen', '') or data.get('九宗门', '') or data.get('daliuren_keti', '')
        if zongmen:
            parts.append(f"九宗门：{zongmen}（起课法）")

        kejing = data.get('kejing', '') or data.get('课经', '')
        if kejing:
            parts.append(f"64课经：{kejing}")

        patterns = data.get('patterns', []) or data.get('课格列表', [])
        if patterns:
            pattern_names = []
            for p in patterns[:5]:
                if isinstance(p, dict):
                    pattern_names.append(p.get('格局名称', ''))
                elif isinstance(p, str):
                    pattern_names.append(p)
            if pattern_names:
                parts.append(f"格局：{', '.join(pattern_names)}")

        return '\n'.join(parts)

    def _generate_doushou_evaluation(self, data: Dict) -> str:
        """生成斗首课格评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【斗首课格评价】")
        parts.append("=" * 60)

        doushou_score = data.get('doushou_score', 0) or data.get('斗首评分', 0)
        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append(f"\n课格：{doushou_keti if doushou_keti else '未确定'}")
        parts.append(f"评分：{doushou_score}分")

        if doushou_keti:
            jixiong = self._get_doushou_jixiong(doushou_keti)
            parts.append(f"吉凶：{jixiong}")

            duanyu = self._get_doushou_duanyu(doushou_keti)
            if duanyu:
                parts.append(f"\n断语：{duanyu}")

        return '\n'.join(parts)

    def _get_doushou_jixiong(self, kege: str) -> str:
        """获取斗首课格吉凶"""
        jixiong_map = {
            '元辰': '上吉', '武财': '上吉', '廉贞': '中吉',
            '贪官': '凶', '破鬼': '大凶'
        }
        return jixiong_map.get(kege, '平')

    def _get_doushou_duanyu(self, kege: str) -> str:
        """获取斗首课格断语"""
        duanyu_map = {
            '元辰': '元辰课，诸事大吉。主家宅平安，子孙兴旺，功名可就。',
            '武财': '武财课，财源广进。主生意兴隆，财帛丰厚，旺财有方。',
            '廉贞': '廉贞课，文教吉祥。主权柄文书，科甲功名，文化教育有利。',
            '贪官': '贪官课，需谨慎。主人事是非，宜守不宜攻，谨防小人。',
            '破鬼': '破鬼课，大凶之象。主灾祸疾病，阴邪侵扰，诸事不宜。'
        }
        return duanyu_map.get(kege, f'{kege}，需具体分析。')

    def _generate_zongmen_info(self, data: Dict) -> str:
        """生成九宗门信息（仅起课法）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【九宗门起课法】")
        parts.append("=" * 60)

        zongmen = data.get('zongmen', '') or data.get('九宗门', '') or data.get('daliuren_keti', '')

        parts.append(f"\n起课法：{zongmen if zongmen else '未确定'}")
        parts.append("\n说明：九宗门是正课之分章，不是课格，无吉凶。")
        parts.append("起课后须论64课经与毕法赋以定吉凶。")

        return '\n'.join(parts)

    def _generate_64kejing_evaluation(self, data: Dict) -> str:
        """生成64课经评价（核心吉凶判断）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【64课经吉凶判定】")
        parts.append("=" * 60)

        kejing = data.get('kejing', '') or data.get('课经', '') or data.get('daliuren_keti', '')

        if not kejing:
            parts.append("\n64课经：未确定")
            parts.append("\n请根据九宗门起课后，确定属于64课经中的哪一种")
            return '\n'.join(parts)

        parts.append(f"\n课经：{kejing}")

        if self.kejing_64:
            kejing_info = self.kejing_64['get_by_name'](kejing)
            if kejing_info:
                jixiong = kejing_info.get('jixiong', '平')
                base_score = kejing_info.get('base_score', 50)
                duanyu = kejing_info.get('duanyu', '')
                definition = kejing_info.get('definition', '')

                parts.append(f"吉凶：{jixiong}")
                parts.append(f"基础分：{base_score}分")

                if definition:
                    parts.append(f"\n定义：{definition}")
                if duanyu:
                    parts.append(f"\n断语：{duanyu}")
            else:
                parts.append("\n断语：该课经暂无详细资料")
        else:
            parts.append("\n（64课经规则库未加载）")

        return '\n'.join(parts)

    def _generate_bifa_evaluation(self, data: Dict) -> str:
        """生成毕法赋评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【毕法赋精细断语】")
        parts.append("=" * 60)

        bifa_matched = data.get('bifa_matched', []) or data.get('毕法赋', [])

        if not bifa_matched:
            parts.append("\n毕法赋：未匹配到相关规则")
            parts.append("\n说明：毕法赋有100条规则，匹配到越多则分析越精细")
            return '\n'.join(parts)

        parts.append(f"\n匹配到 {len(bifa_matched)} 条毕法赋：")

        for i, rule in enumerate(bifa_matched[:5], 1):
            if isinstance(rule, dict):
                rule_name = rule.get('rule_name', rule.get('名称', ''))
                reasoning = rule.get('reasoning', rule.get('推理', ''))
                parts.append(f"\n{i}. {rule_name}")
                if reasoning:
                    parts.append(f"   {reasoning}")

        if len(bifa_matched) > 5:
            parts.append(f"\n... 还有 {len(bifa_matched) - 5} 条规则")

        return '\n'.join(parts)

    def _generate_yanqin_evaluation(self, data: Dict) -> str:
        """生成演禽评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【演禽真法评价】")
        parts.append("=" * 60)

        yanqin_score = data.get('yanqin_score', 0) or data.get('yanqinScore', 0) or data.get('演禽评分', 0)
        yanqin_info = data.get('yanqin', '') or data.get('yanqinInfo', '')

        parts.append(f"\n信息：{yanqin_info if yanqin_info else '未确定'}")
        parts.append(f"评分：{yanqin_score}分")

        if yanqin_score >= 85:
            parts.append(f"\n吉凶：吉")
            parts.append(f"断语：演禽得位，禽星扶身，主贵人相助，行事顺利。")
        elif yanqin_score >= 70:
            parts.append(f"\n吉凶：平")
            parts.append(f"断语：演禽平稳，禽星无伤，行事中规中矩。")
        else:
            parts.append(f"\n吉凶：凶")
            parts.append(f"断语：演禽失位，禽星受制，行事须防阻碍。")

        return '\n'.join(parts)

    def _generate_luma_guiren_evaluation(self, data: Dict) -> str:
        """生成禄马贵人评价（核心功能）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【禄马贵人评价】")
        parts.append("=" * 60)

        luma_info = data.get('luma_guiren_info', {}) or data.get('luma_info', {})

        if not luma_info:
            parts.append("\n禄马贵人信息未获取")
            return '\n'.join(parts)

        qualified_count = luma_info.get('qualified_count', 0)
        parts.append(f"\n合格柱数：{qualified_count}/4")

        nian_qualified = luma_info.get('nian_qualified', False)
        yue_qualified = luma_info.get('yue_qualified', False)
        ri_qualified = luma_info.get('ri_qualified', False)
        shi_qualified = luma_info.get('shi_qualified', False)

        parts.append(f"\n各柱禄马贵人到山到向：")
        parts.append(f"  年柱：{'✅合格' if nian_qualified else '❌未达标'}")
        parts.append(f"  月柱：{'✅合格' if yue_qualified else '❌未达标'}")
        parts.append(f"  日柱：{'✅合格' if ri_qualified else '❌未达标'}")
        parts.append(f"  时柱：{'✅合格' if shi_qualified else '❌未达标'}")

        ri_luma_in_sanchuan = luma_info.get('ri_luma_guiren_in_sanchuan', False)
        parts.append(f"\n三传禄马贵人：{'✅有' if ri_luma_in_sanchuan else '❌无'}")

        qualification_status = luma_info.get('qualification_status', '')
        if qualification_status:
            parts.append(f"综合评价：{qualification_status}")

        parts.append("\n" + "-" * 40)
        parts.append("【禄马贵人属相应验分析】")
        parts.append("-" * 40)

        day_zhu = self._get_day_zhu(data)
        if day_zhu:
            day_gan = day_zhu[0] if len(day_zhu) > 0 else ''
            day_zhi = day_zhu[1] if len(day_zhu) > 1 else ''

            parts.append(f"\n日柱：{day_zhu}")
            parts.append(f"日干：{day_gan}")
            parts.append(f"日支：{day_zhi}")
            parts.append(f"日支属相：{self.DIZHI_SHUXIANG.get(day_zhi, '')}")

            lu_zhi = self._get_lu_zhi(day_gan)
            ma_zhi = self._get_ma_zhi(day_gan)
            guiren_zhi_list = self._get_guiren_zhi(day_gan)

            parts.append(f"\n禄神：{lu_zhi}（{self.DIZHI_SHUXIANG.get(lu_zhi, '')}）")
            parts.append(f"驿马：{ma_zhi}（{self.DIZHI_SHUXIANG.get(ma_zhi, '')}）")
            guiren_shuxiang = [self.DIZHI_SHUXIANG.get(g, '') for g in guiren_zhi_list if g]
            parts.append(f"贵人：{', '.join(guiren_zhi_list)}（{', '.join(guiren_shuxiang)}）")

            parts.append("\n" + "-" * 40)
            parts.append("【属相应验分析】")
            parts.append("-" * 40)

            self_sanhe = self.SANHE.get(day_zhi, [])
            self_sanhe_shuxiang = [self.DIZHI_SHUXIANG.get(z, '') for z in self_sanhe]
            if self_sanhe_shuxiang:
                parts.append(f"\n◆ 三合属相：{', '.join(self_sanhe_shuxiang)}")
                parts.append(f"  三合属相与日支相生相助，万事顺利")

            lu_shuxiang = self.DIZHI_SHUXIANG.get(lu_zhi, '')
            if lu_shuxiang:
                if lu_zhi == day_zhi:
                    parts.append(f"\n◆ 禄神与本命同宫：{lu_shuxiang}")
                    parts.append(f"  财禄双全，大吉之象，宜求财创业")
                elif lu_zhi in self_sanhe:
                    parts.append(f"\n◆ 禄神与三合：{lu_shuxiang}")
                    parts.append(f"  贵人相助，财运亨通，宜投资理财")

            chong_zhi = self.LIUCHONG.get(day_zhi, '')
            if chong_zhi:
                chong_shuxiang = self.DIZHI_SHUXIANG.get(chong_zhi, '')
                parts.append(f"\n⚠️ 六冲属相：{chong_shuxiang}")
                parts.append(f"  六冲方位不利，宜静不宜动")

        ri_double = luma_info.get('ri_double_qualified', False)
        if ri_double:
            parts.append("\n" + "-" * 40)
            parts.append("【日柱禄马贵人双重达标】")
            parts.append("-" * 40)
            parts.append("\n日柱禄马贵人同时到山到向并发动，")
            parts.append("主财禄、权柄、贵人三重吉运叠加！")

        return '\n'.join(parts)

    def _generate_kekeduanyu_evaluation(self, data: Dict) -> str:
        """生成日课课格断语评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【日课课格断语】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（日课断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']
        SizhuAnalyzer = self.kekeduanyu['SizhuAnalyzer']

        sizhu = data.get('sizhu', {})
        if not sizhu:
            sizhu = {
                '年柱': data.get('年柱', ''),
                '月柱': data.get('月柱', ''),
                '日柱': data.get('日柱', ''),
                '时柱': data.get('时柱', '')
            }

        if not any(sizhu.values()):
            parts.append("\n四柱信息未获取")
            return '\n'.join(parts)

        sizhu_info = SizhuAnalyzer.get_sizhu_info(sizhu)

        parts.append("\n【四柱禄马贵人】")
        for pillar_name, info in sizhu_info.items():
            if info.get('干支'):
                parts.append(f"\n{pillar_name} {info['干支']}:")
                parts.append(f"  天干{info['天干']} | 禄{info['禄']} | 马{info['马']}")
                parts.append(f"  阳贵{info['阳贵']} | 阴贵{info['阴贵']} | 文昌{info['文昌']}")

        parts.append("\n" + "-" * 40)
        parts.append("【六相六替口诀】")
        parts.append("-" * 40)
        parts.append("\n六相：长生、帝旺、冠带、临官、胎、养")
        parts.append("六替：沐浴、衰、病、死、墓、绝")

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')
        if doushou_keti:
            kege_info = KeKeDuanyu.analyze_kege(doushou_keti)
            parts.append("\n" + "-" * 40)
            parts.append("【课格断语】")
            parts.append("-" * 40)
            parts.append(f"\n课格：{kege_info.get('name', '')}")
            parts.append(f"吉凶：{kege_info.get('level', '平')}")
            parts.append(f"断语：{kege_info.get('result', '')}")
            parts.append(f"效应：{kege_info.get('effect', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【应事断语】")
        parts.append("-" * 40)

        luma_info = data.get('luma_guiren_info', {}) or data.get('luma_info', {})
        qualified_count = luma_info.get('qualified_count', 0)
        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        ri_luma_in_sanchuan = luma_info.get('ri_luma_guiren_in_sanchuan', False)
        ri_double_qualified = luma_info.get('ri_double_qualified', False)

        yingshi_types = ['求官', '求财', '求富贵', '求子', '求文昌', '求婚姻']

        for yingshi in yingshi_types:
            if yingshi == '求官':
                if ri_luma_in_sanchuan or qualified_count >= 3:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif qualified_count >= 2:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：中等")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                else:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：较弱")
                    parts.append(f"  {level_info.get('断语', '')}")

            elif yingshi == '求财':
                if '武财' in doushou_keti or ri_double_qualified:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif qualified_count >= 2:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：中等")
                    parts.append(f"  {level_info.get('断语', '')}")
                else:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：较弱")
                    parts.append(f"  {level_info.get('断语', '')}")

            elif yingshi == '求富贵':
                if '全元联曜' in doushou_keti or '禄马齐发' in doushou_keti:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif '三元三武' in doushou_keti:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：次吉")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif qualified_count >= 2:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：一般")
                    parts.append(f"  {level_info.get('断语', '')}")
                else:
                    parts.append(f"\n◆ {yingshi}：较弱")
                    parts.append(f"  宜守成，等待时机")

            elif yingshi == '求子':
                sizhu_info = SizhuAnalyzer.get_sizhu_info(sizhu)
                has_tianxi = any(info.get('天喜') for info in sizhu_info.values() if info.get('干支'))
                has_hongluan = any(info.get('红鸾') for info in sizhu_info.values() if info.get('干支'))

                if (ri_double_qualified or '廉贞' in doushou_keti) and has_tianxi:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif has_tianxi or has_hongluan:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：次吉")
                    parts.append(f"  {level_info.get('断语', '')}")
                else:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：一般")
                    parts.append(f"  {level_info.get('断语', '')}")

            elif yingshi == '求文昌':
                sizhu_info = SizhuAnalyzer.get_sizhu_info(sizhu)
                has_wenchang = any(info.get('文昌') for info in sizhu_info.values() if info.get('干支'))

                if '华盖乘轩' in doushou_keti or '文昌贵人会局' in doushou_keti:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif has_wenchang:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：次吉")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                else:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：一般")
                    parts.append(f"  {level_info.get('断语', '')}")

            elif yingshi == '求婚姻':
                sizhu_info = SizhuAnalyzer.get_sizhu_info(sizhu)
                has_hongluan = any(info.get('红鸾') for info in sizhu_info.values() if info.get('干支'))
                has_tianxi = any(info.get('天喜') for info in sizhu_info.values() if info.get('干支'))

                if ri_double_qualified and has_hongluan and has_tianxi:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, 'best')
                    parts.append(f"\n◆ {yingshi}：大吉！")
                    parts.append(f"  {level_info.get('断语', '')}")
                    if level_info.get('经典'):
                        parts.append(f"  {level_info.get('经典', '')}")
                elif has_hongluan or has_tianxi:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '次吉')
                    parts.append(f"\n◆ {yingshi}：次吉")
                    parts.append(f"  {level_info.get('断语', '')}")
                else:
                    level_info = KeKeDuanyu.get_yingduan(yingshi, '一般')
                    parts.append(f"\n◆ {yingshi}：一般")
                    parts.append(f"  {level_info.get('断语', '')}")

        return '\n'.join(parts)

    def _generate_lianzi_evaluation(self, data: Dict) -> str:
        """生成廉子课评价（第五章：大岁遇廉子配日课）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【廉子课配日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（廉子课断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']
        SizhuAnalyzer = self.kekeduanyu['SizhuAnalyzer']

        sizhu = data.get('sizhu', {})
        if not sizhu:
            sizhu = {
                '年柱': data.get('年柱', ''),
                '月柱': data.get('月柱', ''),
                '日柱': data.get('日柱', ''),
                '时柱': data.get('时柱', '')
            }

        if not any(sizhu.values()):
            parts.append("\n四柱信息未获取")
            return '\n'.join(parts)

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【大岁遇廉子原理】")
        lianzi_base = KeKeDuanyu.get_lianzi_info('大岁遇廉子')
        parts.append(f"\n原理：{lianzi_base.get('原理', '')}")
        parts.append(f"效果：{lianzi_base.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【廉子配课规则】")
        parts.append("-" * 40)

        peike_rules = lianzi_base.get('配课规则', {})
        parts.append(f"\n月建：{peike_rules.get('月建', '宜用元辰生廉以生财')}")
        parts.append(f"日柱：{peike_rules.get('日柱', '宜用武财生扶元辰')}")
        parts.append(f"时柱：{peike_rules.get('时柱', '宜用元辰生入本山')}")
        parts.append(f"忌讳：{peike_rules.get('忌讳', '月建不可用武曲为贪年才坏月印')}")

        parts.append(f"\n相生链：{lianzi_base.get('相生链', '财生杀，杀生印，印生元')}")
        parts.append(f"最佳：{lianzi_base.get('最佳', '从日时生入本山为妙')}")

        if '廉贞' in doushou_keti or '廉子' in doushou_keti:
            parts.append("\n" + "-" * 40)
            parts.append("【廉子吉凶判定】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")

            if '贪官' in doushou_keti:
                parts.append(f"\n吉凶：大凶")
                parts.append(f"断语：{KeKeDuanyu.get_lianzi_duanyu('凶')}")
                parts.append(f"\n说明：{lianzi_base.get('贪官规则', '月建遇贪官则年财助月杀')}")
            else:
                parts.append(f"\n吉凶：大吉")
                parts.append(f"断语：{KeKeDuanyu.get_lianzi_duanyu('大吉')}")

            mountain = data.get('mountain', '') or data.get('坐山', '')
            if mountain:
                mountain_type = self._get_lianzi_mountain_type(mountain)
                if mountain_type and mountain_type in KeKeDuanyu.LIANZI_DUANYU.get('廉子配课法', {}):
                    parts.append("\n" + "-" * 40)
                    parts.append(f"【{mountain_type}廉子配课】")
                    parts.append("-" * 40)
                    lianzhi_info = KeKeDuanyu.get_lianzi_info(mountain_type)
                    parts.append(f"\n元辰：{lianzhi_info.get('元辰', '')}")
                    parts.append(f"廉子：{lianzhi_info.get('廉子', '')}")
                    parts.append(f"吉支：{lianzhi_info.get('吉支', '')}")
                    parts.append(f"凶支：{lianzhi_info.get('凶支', '')}")
                    if lianzhi_info.get('解法'):
                        parts.append(f"解法：{lianzhi_info.get('解法', '')}")

        return '\n'.join(parts)

    def _get_lianzi_mountain_type(self, mountain: str) -> str:
        """根据山家判断廉子山家类型"""
        huoshan = ['丙', '丁', '巳', '午', '庚', '辛']
        jinshan = ['庚', '辛', '申', '酉']
        mushan = ['甲', '乙', '寅', '卯']
        shuishan = ['壬', '癸', '亥', '子']
        tushan = ['戊', '己', '辰', '戌', '丑', '未']

        first_char = mountain[0] if mountain else ''

        if first_char in ['丙', '丁']:
            return '六火山'
        elif first_char in ['庚', '辛']:
            return '六金山'
        elif first_char in ['甲', '乙']:
            return '六木山'
        elif first_char in ['壬', '癸']:
            return '六水山'
        elif first_char in ['戊', '己', '辰', '丑', '未', '戌']:
            return '六土山'
        return ''

    def _generate_wucai_evaluation(self, data: Dict) -> str:
        """生成武财评价（第六章：大岁遇武财配日课）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【武财课配日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（武财断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【大岁遇武财原理】")
        wucai_base = KeKeDuanyu.get_wucai_info('大岁遇武财')
        parts.append(f"\n原理：{wucai_base.get('原理', '')}")
        parts.append(f"效果：{wucai_base.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【武财配课规则】")
        parts.append("-" * 40)

        peike_rules = wucai_base.get('配课规则', {})
        parts.append(f"\n月建：{peike_rules.get('月建', '喜用元辰，或用武财亦可')}")
        parts.append(f"日柱：{peike_rules.get('日柱', '宜武财')}")
        parts.append(f"时柱：{peike_rules.get('时柱', '宜元辰')}")
        parts.append(f"日元：{peike_rules.get('日元', '万不可用元辰与月杀相争斗')}")

        parts.append("\n【日课类型】")
        rike_types = wucai_base.get('日课类型', {})
        for ke_type, effect in rike_types.items():
            parts.append(f"  {ke_type}：{effect}")

        parts.append(f"\n相生链：{wucai_base.get('相生链', '杀生印，印生山')}")
        parts.append(f"忌讳：{wucai_base.get('忌讳', '廉子月建犯贪才坏印，破鬼月建俱不可用')}")

        if '武财' in doushou_keti or '武曲' in doushou_keti:
            parts.append("\n" + "-" * 40)
            parts.append("【本课武财分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")

            mountain = data.get('mountain', '') or data.get('坐山', '')
            if mountain:
                mountain_type = self._get_lianzi_mountain_type(mountain)
                if mountain_type and mountain_type in KeKeDuanyu.WUCAI_DUANYU.get('武财配课法', {}):
                    parts.append(f"\n{mountain_type}武财配课：")
                    wucai_info = KeKeDuanyu.get_wucai_info(mountain_type)
                    parts.append(f"  元辰：{wucai_info.get('元辰', '')}")
                    parts.append(f"  武财：{wucai_info.get('武财', '')}")
                    parts.append(f"  吉支：{wucai_info.get('吉支', '')}")
                    parts.append(f"  凶支：{wucai_info.get('凶支', '')}")
                    if wucai_info.get('解法'):
                        parts.append(f"  解法：{wucai_info.get('解法', '')}")

            if '贪官' in doushou_keti or '破鬼' in doushou_keti:
                parts.append(f"\n吉凶：需谨慎")
                parts.append(f"断语：{KeKeDuanyu.get_wucai_duanyu('凶')}")
            else:
                parts.append(f"\n吉凶：大吉")
                parts.append(f"断语：{KeKeDuanyu.get_wucai_duanyu('大吉')}")

        return '\n'.join(parts)

    def _generate_tangan_evaluation(self, data: Dict) -> str:
        """生成贪官评价（第八章：大岁遇贪官配日课）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【贪官课配日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（贪官断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']
        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【大岁遇贪官原理】")
        tangan_base = KeKeDuanyu.get_tangan_info('大岁遇贪官')
        parts.append(f"\n原理：{tangan_base.get('原理', '')}")
        parts.append(f"效果：{tangan_base.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【贪官配课规则】")
        parts.append("-" * 40)

        peike_rules = tangan_base.get('配课规则', {})
        parts.append(f"\n月建：{peike_rules.get('月建', '急用武财以化其煞')}")
        parts.append(f"月日：{peike_rules.get('月日', '武曲')}")
        parts.append(f"时：{peike_rules.get('时', '时上元辰亦可')}")
        parts.append(f"特殊：{peike_rules.get('月武日元时武', '两印夹一元，亦可')}")

        parts.append("\n【忌讳】")
        jihui = tangan_base.get('忌讳', {})
        parts.append(f"月建：{jihui.get('月建', '万不可用廉子以党其煞')}")
        parts.append(f"忌用：{jihui.get('忌用', '不可用元辰与山煞争斗起祸')}")
        parts.append(f"原则：{jihui.get('原则', '只宜化解，不宜争斗')}")

        parts.append("\n【贪官一位】")
        yiwei = tangan_base.get('贪官一位', {})
        parts.append(f"位置：{yiwei.get('位置', '')}")
        parts.append(f"状态：{yiwei.get('状态', '')}")
        parts.append(f"武财状态：{yiwei.get('武财状态', '')}")
        parts.append(f"效果：{yiwei.get('效果', '')}")

        parts.append("\n【重见贪官】")
        chongjian = tangan_base.get('重见贪官', {})
        parts.append(f"结果：{chongjian.get('结果', '')}")
        parts.append(f"说明：{chongjian.get('说明', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【四贪日课】")
        parts.append("-" * 40)
        siman = tangan_base.get('四贪日课', {})
        parts.append(f"经典：{siman.get('经典', '')}")
        parts.append(f"原理：{siman.get('原理', '')}")
        parts.append(f"效果：{siman.get('效果', '')}")

        sifan_case = tangan_base.get('丙山四贪例', {})
        if sifan_case:
            parts.append(f"\n丙山四贪例：")
            parts.append(f"  山向：{sifan_case.get('山向', '')}")
            parts.append(f"  四柱：{sifan_case.get('四柱', '')}")
            parts.append(f"  三元：{sifan_case.get('三元', '')}")
            parts.append(f"  三传：{sifan_case.get('三传', '')}")
            parts.append(f"  效果：{sifan_case.get('效果', '')}")

        wucai_case = tangan_base.get('武财制贪官例', {})
        if wucai_case:
            parts.append(f"\n武财制贪官例：")
            parts.append(f"  山向：{wucai_case.get('山向', '')}")
            parts.append(f"  主命：{wucai_case.get('主命', '')}")
            parts.append(f"  四柱：{wucai_case.get('四柱', '')}")
            parts.append(f"  三元：{wucai_case.get('三元', '')}")
            parts.append(f"  三传：{wucai_case.get('三传', '')}")
            parts.append(f"  效果：{wucai_case.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【四代单传日课】")
        parts.append("-" * 40)
        sifor_case = tangan_base.get('四代单传日课', {})
        parts.append(f"经典：{sifor_case.get('经典', '')}")
        parts.append(f"原理：{sifor_case.get('原理', '')}")
        parts.append(f"日时忌讳：{sifor_case.get('日时忌讳', '')}")
        parts.append(f"贪官相见：{sifor_case.get('贪官相见', '')}")

        sifor_example = tangan_base.get('四代单传例', {})
        if sifor_example:
            parts.append(f"\n四代单传例：")
            parts.append(f"  山向：{sifor_example.get('山向', '')}")
            parts.append(f"  四柱：{sifor_example.get('四柱', '')}")
            parts.append(f"  三元：{sifor_example.get('三元', '')}")
            parts.append(f"  效果：{sifor_example.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【梁老师失败教训】")
        parts.append("-" * 40)
        fail_case = tangan_base.get('梁老师失败教训', {})
        parts.append(f"  山向：{fail_case.get('山向', '')}")
        parts.append(f"  原日课：{fail_case.get('原日课', '')}")
        parts.append(f"  原理：{fail_case.get('原理', '')}")
        parts.append(f"  问题：{fail_case.get('问题', '')}")
        parts.append(f"  结果：{fail_case.get('结果', '')}")
        parts.append(f"  教训：{fail_case.get('教训', '')}")

        parts.append("\n【偷看时间创新】")
        toupo = tangan_base.get('偷看时间', {})
        parts.append(f"  传统：{toupo.get('传统', '')}")
        parts.append(f"  梁老师实践：{toupo.get('梁老师实践', '')}")
        parts.append(f"  好处：{toupo.get('好处', '')}")
        parts.append(f"  意义：{toupo.get('意义', '')}")

        buji_case = tangan_base.get('成功补救例', {})
        if buji_case:
            parts.append(f"\n成功补救例：")
            parts.append(f"  补救日课：{buji_case.get('补救日课', '')}")
            parts.append(f"  效果：{buji_case.get('效果', '')}")

        if '贪官' in doushou_keti:
            parts.append("\n" + "-" * 40)
            parts.append("【本课贪官分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")
            parts.append(f"\n吉凶：大凶（需化解）")
            parts.append(f"断语：{tangan_base.get('效果', '煞气到山')}")
            parts.append(f"说明：急用武财化解，不宜争斗")

        return '\n'.join(parts)

    def _generate_hunyin_evaluation(self, data: Dict) -> str:
        """生成婚姻评价（求婚姻日课理论）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【婚姻嫁娶日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（婚姻断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']
        SizhuAnalyzer = self.kekeduanyu['SizhuAnalyzer']

        sizhu = data.get('sizhu', {})
        if not sizhu:
            sizhu = {
                '年柱': data.get('年柱', ''),
                '月柱': data.get('月柱', ''),
                '日柱': data.get('日柱', ''),
                '时柱': data.get('时柱', '')
            }

        if not any(sizhu.values()):
            parts.append("\n四柱信息未获取")
            return '\n'.join(parts)

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【欲妻得合旺相】")
        hunyin_base = KeKeDuanyu.get_hunyin_info('欲妻得合旺相')
        parts.append(f"\n经典：{hunyin_base.get('经典', '')}")
        parts.append(f"原理：{hunyin_base.get('原理', '')}")
        parts.append(f"效果：{hunyin_base.get('效果', '')}")

        parts.append("\n【红鸾配婚要诀】")
        peijian = KeKeDuanyu.get_hunyin_info('红鸾配婚要诀')
        parts.append(f"\n关键：{peijian.get('关键', '')}")
        parts.append(f"要求1：{peijian.get('要求1', '')}")
        parts.append(f"要求2：{peijian.get('要求2', '')}")
        parts.append(f"要求3：{peijian.get('要求3', '')}")
        parts.append(f"效果：{peijian.get('效果', '')}")

        parts.append("\n【得力分析】")
        deli = KeKeDuanyu.get_hunyin_info('得力分析')
        parts.append(f"日元：{deli.get('日元', '')}")
        parts.append(f"日禄：{deli.get('日禄', '')}")
        parts.append(f"年马：{deli.get('年马', '')}")
        parts.append(f"效果：{deli.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【婚姻课例】")
        parts.append("-" * 40)

        parts.append("\n课例一：")
        lizi1 = KeKeDuanyu.get_hunyin_info('婚姻课例一')
        parts.append(f"  主命：{lizi1.get('主命', '')}")
        parts.append(f"  山向：{lizi1.get('山向', '')}")
        parts.append(f"  四柱：{lizi1.get('四柱', '')}")
        parts.append(f"  三元：{lizi1.get('三元', '')}")
        parts.append(f"  效果：{lizi1.get('效果', '')}")

        parts.append("\n课例二：")
        lizi2 = KeKeDuanyu.get_hunyin_info('婚姻课例二')
        parts.append(f"  山向：{lizi2.get('山向', '')}")
        parts.append(f"  四柱：{lizi2.get('四柱', '')}")
        parts.append(f"  三元：{lizi2.get('三元', '')}")
        parts.append(f"  效果：{lizi2.get('效果', '')}")

        sizhu_info = SizhuAnalyzer.get_sizhu_info(sizhu)
        has_hongluan = any(info.get('红鸾') for info in sizhu_info.values() if info.get('干支'))
        has_wucai = '武财' in doushou_keti or '武曲' in doushou_keti

        if has_hongluan or has_wucai:
            parts.append("\n" + "-" * 40)
            parts.append("【本课婚姻分析】")
            parts.append("-" * 40)

            if has_hongluan and has_wucai:
                parts.append(f"\n吉凶：大吉！")
                parts.append(f"断语：武财会红鸾，娶得美妻")
                parts.append(f"经典：{hunyin_base.get('经典', '')}")
            elif has_hongluan:
                parts.append(f"\n吉凶：次吉")
                parts.append(f"断语：红鸾到课，姻缘可定")
            elif has_wucai:
                parts.append(f"\n吉凶：次吉")
                parts.append(f"断语：武财到课，财运助力婚姻")

        return '\n'.join(parts)

    def _generate_pougui_evaluation(self, data: Dict) -> str:
        """生成破鬼评价（第七章：大岁遇破鬼配日课）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【破鬼课配日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（破鬼断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【大岁遇破鬼原理】")
        pougui_base = KeKeDuanyu.get_pougui_info('大岁遇破鬼')
        parts.append(f"\n原理：{pougui_base.get('原理', '')}")
        parts.append(f"效果：{pougui_base.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【破鬼配课规则】")
        parts.append("-" * 40)

        peike_rules = pougui_base.get('配课规则', {})
        parts.append(f"\n月建：{peike_rules.get('月建', '万不得已用廉子月建制之')}")
        parts.append(f"月干：{peike_rules.get('月干', '伤官制年上七煞')}")
        parts.append(f"年遁：{peike_rules.get('年遁', '伤官生月遁武才')}")
        parts.append(f"月日：{peike_rules.get('月日', '武财')}")
        parts.append(f"时：{peike_rules.get('时', '元辰旺相')}")
        parts.append(f"年：{peike_rules.get('年', '破军衰败')}")

        parts.append("\n【最佳格局】")
        parts.append(f"格局：{pougui_base.get('最佳格局', '把门破鬼')}")
        parts.append(f"效果：{pougui_base.get('最佳效果', '官盗不侵，先富后贵')}")

        parts.append("\n【破鬼克应】")
        keying = pougui_base.get('破鬼克应', {})
        yike = keying.get('一破鬼两生旺', {})
        parts.append(f"\n一破鬼两生旺：天干{yike.get('天干', '一个破鬼')}，地支{yike.get('地支', '两个生旺')} → {yike.get('结果', '主克妻')}")

        liangke = keying.get('两破鬼一生旺', {})
        parts.append(f"两破鬼一生旺：天干{liangke.get('天干', '两个破鬼')}，地支{liangke.get('地支', '一个生旺')} → {liangke.get('结果', '主克子')}")

        parts.append("\n" + "-" * 40)
        parts.append("【破鬼把门课例】")
        parts.append("-" * 40)

        bamen1 = pougui_base.get('课例一', {})
        if bamen1:
            parts.append(f"\n丁山癸向例：")
            parts.append(f"  山向：{bamen1.get('山向', '')}")
            parts.append(f"  仙命：{bamen1.get('仙命', '')}")
            parts.append(f"  四柱：{bamen1.get('四柱', '')}")
            parts.append(f"  三传：{bamen1.get('三传', '')}")
            parts.append(f"  效果：{bamen1.get('效果', '')}")

        bamen2 = pougui_base.get('课例二', {})
        if bamen2:
            parts.append(f"\n艮山坤向例（李丞相葬母）：")
            parts.append(f"  山向：{bamen2.get('山向', '')}")
            parts.append(f"  四柱：{bamen2.get('四柱', '')}")
            parts.append(f"  效果：{bamen2.get('效果', '')}")

        bamen3 = pougui_base.get('课例三', {})
        if bamen3:
            parts.append(f"\n寅山申向例（最佳破鬼把门）：")
            parts.append(f"  山向：{bamen3.get('山向', '')}")
            parts.append(f"  四柱：{bamen3.get('四柱', '')}")
            parts.append(f"  三传：{bamen3.get('三传', '')}")
            parts.append(f"  效果：{bamen3.get('效果', '')}")

        bamen4 = pougui_base.get('课例四', {})
        if bamen4:
            parts.append(f"\n乙山辛向例（力小的破鬼把门）：")
            parts.append(f"  山向：{bamen4.get('山向', '')}")
            parts.append(f"  四柱：{bamen4.get('四柱', '')}")
            parts.append(f"  三传：{bamen4.get('三传', '')}")
            parts.append(f"  效果：{bamen4.get('效果', '')}")

        bamen5 = pougui_base.get('课例五', {})
        if bamen5:
            parts.append(f"\n辰山戌向例（损人的破鬼）：")
            parts.append(f"  山向：{bamen5.get('山向', '')}")
            parts.append(f"  四柱：{bamen5.get('四柱', '')}")
            parts.append(f"  三传：{bamen5.get('三传', '')}")
            parts.append(f"  效果：{bamen5.get('效果', '')}")

        bamen6 = pougui_base.get('课例六', {})
        if bamen6:
            parts.append(f"\n乾山巽向例（梁老师实践成功）：")
            parts.append(f"  山向：{bamen6.get('山向', '')}")
            parts.append(f"  仙命：{bamen6.get('仙命', '')}")
            parts.append(f"  四柱：{bamen6.get('四柱', '')}")
            parts.append(f"  三传：{bamen6.get('三传', '')}")
            parts.append(f"  效果：{bamen6.get('效果', '')}")

        if '破鬼' in doushou_keti or '破军' in doushou_keti:
            parts.append("\n" + "-" * 40)
            parts.append("【本课破鬼分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")
            parts.append(f"\n吉凶：大凶")
            parts.append(f"断语：{pougui_base.get('效果', '大凶之年')}")
            parts.append(f"\n说明：破鬼为本山煞气，需用把门破鬼格局化解")

        return '\n'.join(parts)

    def _generate_kekedi_evaluation(self, data: Dict) -> str:
        """生成科第评价（求科第日课理论）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【求科第日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（科第断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【求科第禄贵加武财】")
        keke_base = KeKeDuanyu.get_kekedi_info('求科第禄贵加武财')
        parts.append(f"\n经典：{keke_base.get('经典', '')}")
        parts.append(f"原理：{keke_base.get('原理', '')}")
        parts.append(f"效果：{keke_base.get('效果', '')}")

        parts.append("\n【科第配课要诀】")
        peijian = KeKeDuanyu.get_kekedi_info('科第配课要诀')
        parts.append(f"\n关键1：{peijian.get('关键1', '')}")
        parts.append(f"关键2：{peijian.get('关键2', '')}")
        parts.append(f"关键3：{peijian.get('关键3', '')}")
        parts.append(f"要求：{peijian.get('要求', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【科第课例】")
        parts.append("-" * 40)

        parts.append("\n丙山例：")
        lizi1 = KeKeDuanyu.get_kekedi_info('丙山例')
        parts.append(f"  山向：{lizi1.get('山向', '')}")
        parts.append(f"  主命：{lizi1.get('主命', '')}")
        parts.append(f"  四柱：{lizi1.get('四柱', '')}")
        parts.append(f"  三元：{lizi1.get('三元', '')}")
        parts.append(f"  效果：{lizi1.get('效果', '')}")

        parts.append("\n乾山最佳例：")
        lizi2 = KeKeDuanyu.get_kekedi_info('乾山最佳例')
        parts.append(f"  山向：{lizi2.get('山向', '')}")
        parts.append(f"  主命：{lizi2.get('主命', '')}")
        parts.append(f"  四柱：{lizi2.get('四柱', '')}")
        parts.append(f"  三元：{lizi2.get('三元', '')}")
        parts.append(f"  三传：{lizi2.get('三传', '')}")
        parts.append(f"  效果：{lizi2.get('效果', '')}")

        has_wucai = '武财' in doushou_keti or '武曲' in doushou_keti
        has_yuanchen = '元辰' in doushou_keti

        if has_wucai and has_yuanchen:
            parts.append("\n" + "-" * 40)
            parts.append("【本课科第分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")
            parts.append(f"\n吉凶：大吉！")
            parts.append(f"断语：联科及第，一门昌盛")
            parts.append(f"经典：{keke_base.get('经典', '')}")
        elif has_wucai:
            parts.append("\n" + "-" * 40)
            parts.append("【本课科第分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")
            parts.append(f"\n吉凶：次吉")
            parts.append(f"断语：科甲有望，需配合元辰")

        return '\n'.join(parts)

    def _generate_yidu_evaluation(self, data: Dict) -> str:
        """生成仪度六壬要诀评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【仪度六壬选日要诀】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（仪度六壬要诀库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        parts.append("\n【第一要诀】")
        yi = KeKeDuanyu.get_yidu_info('第一要诀')
        parts.append(f"\n内容：{yi.get('内容', '')}")
        parts.append(f"例：{yi.get('例', '')}")
        parts.append(f"要求：{yi.get('要求', '')}")
        parts.append(f"不发传：{yi.get('不发传', '')}")

        parts.append("\n【第二要诀】")
        er = KeKeDuanyu.get_yidu_info('第二要诀')
        parts.append(f"\n内容：{er.get('内容', '')}")
        parts.append(f"例1：{er.get('例1', '')}")
        parts.append(f"例2：{er.get('例2', '')}")

        parts.append("\n【第三要诀】")
        san = KeKeDuanyu.get_yidu_info('第三要诀')
        parts.append(f"\n内容：{san.get('内容', '')}")
        parts.append(f"警示：{san.get('警示', '')}")
        parts.append(f"关键：{san.get('关键', '')}")

        parts.append("\n【机殷】")
        jiyin = KeKeDuanyu.get_yidu_info('机殷')
        parts.append(f"\n解释：{jiyin.get('解释', '')}")
        parts.append(f"例：{jiyin.get('例', '')}")

        parts.append("\n【第四要诀】")
        si = KeKeDuanyu.get_yidu_info('第四要诀')
        parts.append(f"\n内容：{si.get('内容', '')}")
        parts.append(f"说明：{si.get('说明', '')}")

        parts.append("\n【坤山艮向例】")
        kunshan = KeKeDuanyu.get_yidu_info('坤山艮向例')
        parts.append(f"  山向：{kunshan.get('山向', '')}")
        parts.append(f"  四柱：{kunshan.get('四柱', '')}")
        parts.append(f"  三传：{kunshan.get('三传', '')}")
        parts.append(f"  效果：{kunshan.get('效果', '')}")

        parts.append("\n【第五要诀】")
        wu = KeKeDuanyu.get_yidu_info('第五要诀')
        parts.append(f"\n内容：{wu.get('内容', '')}")
        parts.append(f"例：{wu.get('例', '')}")

        parts.append("\n【癸山丁向例】")
        guishan = KeKeDuanyu.get_yidu_info('癸山丁向例')
        parts.append(f"  山向：{guishan.get('山向', '')}")
        parts.append(f"  四柱：{guishan.get('四柱', '')}")
        parts.append(f"  三传：{guishan.get('三传', '')}")
        parts.append(f"  效果：{guishan.get('效果', '')}")

        return '\n'.join(parts)

    def _generate_xunkong_evaluation(self, data: Dict) -> str:
        """生成旬空评价（犯旬空而虚名虚利）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【旬空虚名虚利】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（旬空断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        parts.append("\n【星陷马空虚名虚利】")
        xunkong_base = KeKeDuanyu.get_xunkong_info('星陷马空虚名虚利')
        parts.append(f"\n经典：{xunkong_base.get('经典', '')}")
        parts.append(f"原理：{xunkong_base.get('原理', '')}")
        parts.append(f"效果：{xunkong_base.get('效果', '')}")

        parts.append("\n【甲子命例】")
        jiazi_case = KeKeDuanyu.get_xunkong_info('甲子命例')
        parts.append(f"  主命：{jiazi_case.get('主命', '')}")
        parts.append(f"  四柱：{jiazi_case.get('四柱', '')}")
        parts.append(f"  旬空：{jiazi_case.get('甲辰旬', '')}")
        parts.append(f"  结果：{jiazi_case.get('结果', '')}")

        parts.append("\n【旬空速查】")
        xunkong_lookup = KeKeDuanyu.get_xunkong_info('旬空速查')
        for xun, kong in xunkong_lookup.items():
            parts.append(f"  {xun}：{kong}")

        parts.append("\n【犯旬空忌讳】")
        jihui = KeKeDuanyu.get_xunkong_info('犯旬空忌讳')
        parts.append(f"  禄犯空：{jihui.get('禄犯空', '')}")
        parts.append(f"  马犯空：{jihui.get('马犯空', '')}")
        parts.append(f"  贵犯空：{jihui.get('贵犯空', '')}")
        parts.append(f"  禄马贵皆空：{jihui.get('禄马贵皆空', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【不犯旬空得科甲例】")
        parts.append("-" * 40)
        ke_example = KeKeDuanyu.get_xunkong_info('不犯旬空得科甲例')
        parts.append(f"  主命：{ke_example.get('主命', '')}")
        parts.append(f"  四柱：{ke_example.get('四柱', '')}")
        parts.append(f"  原理：{ke_example.get('原理', '')}")
        parts.append(f"  效果：{ke_example.get('效果', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【梁老师教训例】")
        parts.append("-" * 40)
        liang_example = KeKeDuanyu.get_xunkong_info('梁老师教训例')
        parts.append(f"  山向：{liang_example.get('山向', '')}")
        parts.append(f"  主命：{liang_example.get('主命', '')}")
        parts.append(f"  四柱：{liang_example.get('四柱', '')}")
        parts.append(f"  旬空：{liang_example.get('甲申旬', '')}")
        parts.append(f"  效果：{liang_example.get('效果', '')}")

        return '\n'.join(parts)

    def _generate_wenxue_evaluation(self, data: Dict) -> str:
        """生成求学问评价（禄强马旺饱学高科）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【求学问日课法】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（求学问断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        parts.append("\n【禄强马旺饱学高科】")
        wenxue_base = KeKeDuanyu.get_wenxue_info('禄强马旺饱学高科')
        parts.append(f"\n经典：{wenxue_base.get('经典', '')}")
        parts.append(f"原理：{wenxue_base.get('原理', '')}")
        parts.append(f"效果：{wenxue_base.get('效果', '')}")

        parts.append("\n【求学问配课要诀】")
        peijian = KeKeDuanyu.get_wenxue_info('求学问配课要诀')
        parts.append(f"\n关键1：{peijian.get('关键1', '')}")
        parts.append(f"关键2：{peijian.get('关键2', '')}")
        parts.append(f"关键3：{peijian.get('关键3', '')}")
        parts.append(f"要求：{peijian.get('要求', '')}")

        parts.append("\n【乙卯命例】")
        lizi = KeKeDuanyu.get_wenxue_info('乙卯命例')
        parts.append(f"  山向：{lizi.get('山向', '')}")
        parts.append(f"  主命：{lizi.get('主命', '')}")
        parts.append(f"  四柱：{lizi.get('四柱', '')}")
        parts.append(f"  三元：{lizi.get('三元', '')}")
        parts.append(f"  三传：{lizi.get('三传', '')}")
        parts.append(f"  效果：{lizi.get('效果', '')}")

        return '\n'.join(parts)

    def _generate_zhuming_evaluation(self, data: Dict) -> str:
        """生成主命评价（紧扣主命催发主命）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【紧扣主命催发主命】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（主命断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']

        parts.append("\n【紧扣主命催发主命】")
        zhuming_base = KeKeDuanyu.get_zhuming_info('紧扣主命催发主命')
        parts.append(f"\n经典：{zhuming_base.get('经典', '')}")
        parts.append(f"原理：{zhuming_base.get('原理', '')}")
        parts.append(f"效果：{zhuming_base.get('效果', '')}")

        parts.append("\n【庚子命例】")
        lizi = KeKeDuanyu.get_zhuming_info('庚子命例')
        parts.append(f"  山向：{lizi.get('山向', '')}")
        parts.append(f"  仙命：{lizi.get('仙命', '')}")
        parts.append(f"  四柱：{lizi.get('四柱', '')}")
        parts.append(f"  三传：{lizi.get('三传', '')}")
        parts.append(f"  效果：{lizi.get('效果', '')}")

        parts.append("\n【紧扣要诀】")
        yaojue = KeKeDuanyu.get_zhuming_info('紧扣要诀')
        parts.append(f"  禄到命：{yaojue.get('禄到命', '')}")
        parts.append(f"  贵到命：{yaojue.get('贵到命', '')}")
        parts.append(f"  日与命合：{yaojue.get('日与命合', '')}")
        parts.append(f"  效果：{yaojue.get('效果', '')}")

        return '\n'.join(parts)

    def _generate_ziqi_evaluation(self, data: Dict) -> str:
        """生成子嗣评价（求子嗣理论）"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【子嗣断语分析】")
        parts.append("=" * 60)

        if not self.kekeduanyu:
            parts.append("\n（子嗣断语库未加载）")
            return '\n'.join(parts)

        KeKeDuanyu = self.kekeduanyu['KeKeDuanyu']
        SizhuAnalyzer = self.kekeduanyu['SizhuAnalyzer']

        sizhu = data.get('sizhu', {})
        if not sizhu:
            sizhu = {
                '年柱': data.get('年柱', ''),
                '月柱': data.get('月柱', ''),
                '日柱': data.get('日柱', ''),
                '时柱': data.get('时柱', '')
            }

        if not any(sizhu.values()):
            parts.append("\n四柱信息未获取")
            return '\n'.join(parts)

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')

        parts.append("\n【天元入局弄璋】")
        tianyuan = KeKeDuanyu.get_ziqi_info('天元入局')
        parts.append(f"\n经典：{tianyuan.get('经典', '')}")
        parts.append(f"效果：{tianyuan.get('效果', '')}")
        parts.append(f"原理：{tianyuan.get('原理', '')}")

        parts.append("\n【四柱全廉】")
        silian = KeKeDuanyu.get_ziqi_info('四柱全廉')
        parts.append(f"\n经典：{silian.get('经典', '')}")
        parts.append(f"效果：{silian.get('效果', '')}")
        parts.append(f"忌讳：{silian.get('忌讳', '')}")

        parts.append("\n" + "-" * 40)
        parts.append("【廉子求子宜忌】")
        parts.append("-" * 40)

        ziqi_yiji = KeKeDuanyu.get_ziqi_info('求子宜忌')

        parts.append("\n大吉条件：")
        daji = ziqi_yiji.get('大吉条件', {})
        parts.append(f"  廉子位：{daji.get('廉子位', '')}")
        parts.append(f"  克制：{daji.get('克制', '')}")
        parts.append(f"  效果：{daji.get('效果', '')}")

        parts.append("\n过房条件：")
        guofang = ziqi_yiji.get('过房条件', {})
        parts.append(f"  廉子位：{guofang.get('廉子位', '')}")
        parts.append(f"  日时遇：{guofang.get('日时遇', '')}")
        parts.append(f"  效果：{guofang.get('效果', '')}")

        parts.append("\n凶死条件：")
        xiongsi = ziqi_yiji.get('凶死条件', {})
        parts.append(f"  廉子位：{xiongsi.get('廉子位', '')}")
        parts.append(f"  日时遇：{xiongsi.get('日时遇', '')}")
        parts.append(f"  效果：{xiongsi.get('效果', '')}")

        parts.append("\n绝房条件：")
        juefang = ziqi_yiji.get('绝房条件', {})
        parts.append(f"  双廉坐：{juefang.get('双廉坐', '')}")
        parts.append(f"  元辰：{juefang.get('元辰', '')}")
        parts.append(f"  效果：{juefang.get('效果', '')}")

        parts.append("\n【禄马贵三秀】")
        sanxiu = KeKeDuanyu.get_ziqi_info('禄马贵三秀')
        parts.append(f"\n定义：{sanxiu.get('定义', '')}")
        parts.append(f"效果：{sanxiu.get('效果', '')}")

        parts.append("\n【生双子课例】")
        lizi_example = KeKeDuanyu.get_ziqi_info('生双子课例')
        parts.append(f"\n山向：{lizi_example.get('山向', '')}")
        parts.append(f"四柱：{lizi_example.get('四柱', '')}")
        parts.append(f"三元：{lizi_example.get('三元', '')}")
        parts.append(f"效果：{lizi_example.get('效果', '')}")

        if '廉贞' in doushou_keti or '廉子' in doushou_keti:
            parts.append("\n" + "-" * 40)
            parts.append("【本课廉子分析】")
            parts.append("-" * 40)

            parts.append(f"\n课格：{doushou_keti}")

            if '贪官' in doushou_keti or '破鬼' in doushou_keti:
                parts.append(f"\n吉凶：凶")
                parts.append(f"断语：损少年子女，重即绝也；或主过房、出外死")
                parts.append(f"\n说明：廉子遇贪官枭神，需特别注意")
            else:
                parts.append(f"\n吉凶：吉")
                parts.append(f"断语：定生贵子")
                parts.append(f"\n说明：廉子坐生旺，无贪官枭神，主添丁发贵")

        return '\n'.join(parts)

    def _get_day_zhu(self, data: Dict) -> str:
        """获取日柱"""
        sizhu = data.get('sizhu', {})
        day_zhu = sizhu.get('日柱', '')
        if not day_zhu:
            day_zhu = data.get('日柱', '')
        return day_zhu

    def _get_lu_zhi(self, tiangan: str) -> str:
        """获取禄位地支"""
        lu_map = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
            '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
        }
        return lu_map.get(tiangan, '')

    def _get_ma_zhi(self, tiangan: str) -> str:
        """获取马位地支"""
        ma_map = {
            '甲': '寅', '乙': '亥', '丙': '申', '丁': '巳', '戊': '申',
            '庚': '寅', '辛': '亥', '壬': '申', '癸': '巳'
        }
        return ma_map.get(tiangan, '')

    def _get_guiren_zhi(self, tiangan: str) -> List[str]:
        """获取贵人地支"""
        guiren_map = {
            '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
            '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
            '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
            '癸': ['巳', '卯']
        }
        return guiren_map.get(tiangan, [])

    def _generate_shuxiang_evaluation(self, data: Dict) -> str:
        """生成属相吉凶评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【属相吉凶评价】")
        parts.append("=" * 60)

        sizhu = data.get('sizhu', {})
        year_zhu = sizhu.get('年柱', '') or data.get('年柱', '')

        if year_zhu and len(year_zhu) >= 2:
            year_zhi = year_zhu[1]
            year_shuxiang = self.DIZHI_SHUXIANG.get(year_zhi, '')

            parts.append(f"\n年柱：{year_zhu}")
            parts.append(f"年支属相：{year_shuxiang}")

            luma_info = data.get('luma_guiren_info', {}) or data.get('luma_info', {})
            ri_qualified = luma_info.get('ri_qualified', False)
            nian_qualified = luma_info.get('nian_qualified', False)

            if ri_qualified and nian_qualified:
                parts.append(f"\n◆ {year_shuxiang}属相：诸事大吉")
                parts.append(f"  禄马贵人与年支相合，贵人扶持，运势亨通")
            elif ri_qualified or nian_qualified:
                parts.append(f"\n◆ {year_shuxiang}属相：平顺")
                parts.append(f"  禄马贵人与年支有缘，运势平稳")
            else:
                parts.append(f"\n◆ {year_shuxiang}属相：需谨慎")
                parts.append(f"  禄马贵人未到位，宜守不宜攻")

            sanhe = self.SANHE.get(year_zhi, [])
            sanhe_shuxiang = [self.DIZHI_SHUXIANG.get(z, '') for z in sanhe]
            if sanhe_shuxiang:
                parts.append(f"\n三合属相：{', '.join(sanhe_shuxiang)}")
                parts.append(f"三合属相与年支相生相助，万事顺利")

        return '\n'.join(parts)

    def _generate_hangye_evaluation(self, data: Dict) -> str:
        """生成行业评价"""
        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【事业行业建议】")
        parts.append("=" * 60)

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')
        luma_info = data.get('luma_guiren_info', {}) or data.get('luma_info', {})
        qualified_count = luma_info.get('qualified_count', 0)

        if doushou_keti:
            best_industries = self.HANGYE_BEST.get(doushou_keti, [])
            if best_industries:
                parts.append(f"\n斗首{doushou_keti}最佳行业：")
                for i, ind in enumerate(best_industries[:3], 1):
                    parts.append(f"  {i}. {ind}")

        if qualified_count >= 3:
            parts.append(f"\n禄马贵人合格{qualified_count}柱，贵人运旺盛")
            parts.append(f"宜从事需要贵人相助的行业：")
            parts.append(f"  1. 金融投资（贵人引财）")
            parts.append(f"  2. 房地产（贵人聚财）")
            parts.append(f"  3. 文化产业（贵人扶文）")
        elif qualified_count >= 2:
            parts.append(f"\n禄马贵人合格{qualified_count}柱，中等贵人运")
            parts.append(f"宜从事稳定行业：")
            parts.append(f"  1. 教育培训")
            parts.append(f"  2. 医疗健康")
            parts.append(f"  3. 技术工程")
        else:
            parts.append(f"\n禄马贵人合格{qualified_count}柱，贵人运较弱")
            parts.append(f"宜从事独立作业行业：")
            parts.append(f"  1. 制造业")
            parts.append(f"  2. 餐饮服务")
            parts.append(f"  3. 零售商业")

        return '\n'.join(parts)

    def _generate_ai_evaluation(self, data: Dict) -> str:
        """生成AI综合评价"""
        if not self.ai_available:
            return ""

        parts = []
        parts.append("\n" + "=" * 60)
        parts.append("【AI智能综合分析】")
        parts.append("=" * 60)

        ai_result = self._call_ai_analysis(data)
        if ai_result:
            parts.append(f"\n{ai_result}")

        return '\n'.join(parts)

    def _call_ai_analysis(self, data: Dict) -> str:
        """调用通义千问API"""
        if not self.api_key:
            return ""

        try:
            prompt = self._build_prompt(data)
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

            payload = {
                "model": self.model,
                "input": {"prompt": prompt},
                "parameters": {"temperature": 0.7, "max_tokens": 1500}
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            result = response.json()

            if 'output' in result and 'text' in result['output']:
                return result['output']['text']
            elif 'error' in result:
                return f"【AI评价错误】{result['error'].get('message', '未知错误')}"
            else:
                return f"【AI评价失败】{result}"

        except Exception as e:
            return f"【AI评价异常】{str(e)}"

    def _build_prompt(self, data: Dict) -> str:
        """构建AI分析提示词"""
        mountain = data.get('mountain', '') or data.get('坐山', '')
        sizhu = data.get('sizhu', {})
        year_zhu = sizhu.get('年柱', '') or data.get('年柱', '')
        month_zhu = sizhu.get('月柱', '') or data.get('月柱', '')
        day_zhu = sizhu.get('日柱', '') or data.get('日柱', '')
        hour_zhu = sizhu.get('时柱', '') or data.get('时柱', '')

        doushou_keti = data.get('斗首课格', '') or data.get('doushou_keti', '')
        zongmen = data.get('zongmen', '') or data.get('九宗门', '') or data.get('daliuren_keti', '')
        kejing = data.get('kejing', '') or data.get('课经', '')

        luma_info = data.get('luma_guiren_info', {}) or data.get('luma_info', {})
        qualified_count = luma_info.get('qualified_count', 0)

        doushou_score = data.get('doushou_score', 0) or data.get('斗首评分', 0)
        yanqin_score = data.get('yanqin_score', 0) or data.get('yanqinScore', 0) or data.get('演禽评分', 0)

        prompt = f"""你是大六壬择日专家，请分析以下课象并给出专业评价：

【基本信息】
坐山：{mountain}
四柱：{year_zhu} {month_zhu} {day_zhu} {hour_zhu}
斗首课格：{doushou_keti}
九宗门（起课法）：{zongmen}
64课经（吉凶判定）：{kejing}

【评分】
斗首：{doushou_score}分
演禽：{yanqin_score}分

【禄马贵人】
合格柱数：{qualified_count}/4

请按以下格式输出分析：

一、课体总评（简要概括此课的吉凶，结合64课经判定）

二、禄马贵人分析（重点说明禄马贵人与日柱属相的关系，以及对事业、财运的影响）

三、属相吉凶（根据年支属相，说明哪些属相与此课配合最好，哪些需要谨慎）

四、事业建议（根据课体和禄马贵人情况，推荐最适合的行业）

五、综合结论（总结此课的优劣，给出最终评价）
"""
        return prompt

    def generate_traditional_evaluation(self, data: Dict) -> str:
        """兼容旧接口"""
        return self.generate_evaluation(data)

    def get_ai_evaluation_text(self, data: Dict) -> str:
        """兼容旧接口"""
        return self.generate_evaluation(data)