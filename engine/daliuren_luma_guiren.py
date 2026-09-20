#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬禄马贵人到山到向完整计算模块
依据传统大六壬理论，实现年月日时四柱禄马贵人到山到向的完整判定逻辑
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

# 尝试导入64课经知识库
try:
    from engine.liuren_64ke_v2 import LIU_SHI_KETI, get_keti_info as get_64ke_info
    HAS_64KE_KNOWLEDGE = True
except ImportError:
    try:
        from liuren_64ke_v2 import LIU_SHI_KETI, get_keti_info as get_64ke_info
        HAS_64KE_KNOWLEDGE = True
    except ImportError:
        HAS_64KE_KNOWLEDGE = False
        LIU_SHI_KETI = {}

# 十三吉课名表（加分课体；2026-08-24 课体修正接入）
try:
    from engine.jike_13 import JIKE_13 as _JIKE_13
except ImportError:
    try:
        from jike_13 import JIKE_13 as _JIKE_13
    except ImportError:
        _JIKE_13 = ['龙德', '官爵', '元首', '富贵', '和美', '亨通', '华盖',
                    '斫轮', '德庆', '时泰', '铸印', '荣华', '引从']

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
# 【BUG-FIX 2026-08-24】贵人全失效根因：三个 fallback 均不含实际文件位置 engine/gui_ren_engine.py，
#   GuiRenCalculator 恒为 None → get_guiren_zhi 恒返 None → "贵人到山到向"永不判定。
#   已补 engine.gui_ren_engine（当前生效路径），并最终走上层目录自动发现。
try:
    from engine.gui_ren_engine import GuiRenCalculator as ImportedGuiRenCalculator
    GuiRenCalculator = ImportedGuiRenCalculator
except ImportError:
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
    
    # 十二地支顺序（用于间神计算）
    DIZHI_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
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
    
    # 二十四山山家映射（斗首体系；八宫归法 2026-08-14 修正四库错位：丑→丑、辰→辰、未→未、戌→戌）
    SHAN_JIA_MAP = {
        '壬': '子', '子': '子', '癸': '子', '丑': '丑',
        '艮': '丑', '寅': '丑', '甲': '卯', '卯': '卯',
        '乙': '卯', '辰': '辰', '巽': '辰', '巳': '辰',
        '丙': '午', '午': '午', '丁': '午', '未': '未',
        '坤': '未', '申': '未', '庚': '酉', '酉': '酉',
        '辛': '酉', '戌': '戌', '乾': '戌', '亥': '戌'
    }
    
    # 三合局
    SAN_HE = {
        '申子辰': ['申','子','辰'], '亥卯未': ['亥','卯','未'],
        '寅午戌': ['寅','午','戌'], '巳酉丑': ['巳','酉','丑'],
    }
    # 单个地支的三合伙伴
    SAN_HE_PARTNERS = {
        '申': {'子','辰'}, '子': {'申','辰'}, '辰': {'申','子'},
        '亥': {'卯','未'}, '卯': {'亥','未'}, '未': {'亥','卯'},
        '寅': {'午','戌'}, '午': {'寅','戌'}, '戌': {'寅','午'},
        '巳': {'酉','丑'}, '酉': {'巳','丑'}, '丑': {'巳','酉'},
    }

    YUEJIANG_MAP = {
        '寅': '亥', '卯': '戌', '辰': '酉', '巳': '申',
        '午': '未', '未': '午', '申': '巳', '酉': '辰',
        '戌': '卯', '亥': '寅', '子': '丑', '丑': '子'
    }

    # 向首映射（二十四山对宫，2026-08-14 憨爷拍板：寅→申、丑→未、辰→戌、巳→亥、未→丑、申→寅、戌→辰、亥→巳）
    XIANG_SHOU_MAP = {
        '壬': '午', '子': '午', '癸': '午', '丑': '未',
        '艮': '未', '寅': '申', '甲': '酉', '卯': '酉',
        '乙': '酉', '辰': '戌', '巽': '戌', '巳': '亥',
        '丙': '子', '午': '子', '丁': '子', '未': '丑',
        '坤': '丑', '申': '寅', '庚': '卯', '酉': '卯',
        '辛': '卯', '戌': '辰', '乾': '辰', '亥': '巳'
    }

    # 本山贵人（二十四山本山对应贵人）
    #   现按斗首"十二双山"取贵干法则统一为地支贵人格：
    #   壬子→壬、癸丑→癸、艮寅→艮纳丙、甲卯→甲、乙辰→乙、巽巳→巽纳辛、
    #   丙午→丙、丁未→丁、坤申→坤纳乙、庚酉→庚、辛戌→辛、乾亥→乾纳甲；
    #   卦无贵人者以纳甲取干（艮纳丙、巽纳辛、坤纳乙、乾纳甲、兑纳丁）。
    # 【四正位双组贵人】子午卯酉为本地支又居坎离震兑后天卦宫，故并取双山干贵 + 所在卦纳甲贵：
    #   子（坎纳戊丑未）、卯（震纳庚丑未）、午（离纳己子申）、酉（兑纳丁亥酉），
    #   与双山干贵取并集（卯两源皆丑未，合一）。
    #   依原著核对：酉山取庚丑未、又"酉作丙丁岁贵/酉作丁贵"取亥酉(L5483、L5387-5388)；
    #   甲山丑未、乙向申、丁山亥、癸山卯、辛山寅 均吻合。
    BEN_SHAN_GUIREN = {
        '壬': ['卯', '巳'], '癸': ['卯', '巳'], '丑': ['卯', '巳'],
        '子': ['卯', '巳', '丑', '未'],        # 壬子双山壬卯巳 + 坎纳戊丑未
        '艮': ['亥', '酉'], '寅': ['亥', '酉'], '甲': ['丑', '未'],
        '卯': ['丑', '未'],                    # 甲卯双山甲丑未 + 震纳庚丑未(同源合一)
        '乙': ['子', '申'], '辰': ['子', '申'], '巽': ['寅', '午'], '巳': ['寅', '午'],
        '丙': ['亥', '酉'],
        '午': ['亥', '酉', '子', '申'],        # 丙午双山丙亥酉 + 离纳己子申
        '丁': ['亥', '酉'], '未': ['亥', '酉'],
        '坤': ['子', '申'], '申': ['子', '申'], '庚': ['丑', '未'],
        '酉': ['丑', '未', '亥', '酉'],        # 庚酉双山庚丑未 + 兑纳丁亥酉
        '辛': ['寅', '午'], '戌': ['寅', '午'], '乾': ['丑', '未'], '亥': ['丑', '未']
    }

    # ── 太阳躔度·二十八宿配宫（《仪度六壬择日要诀》"先查之法/合方之法"）──
    # 十二地支宫位 → 二十八宿（十二星次躔舍，每宫含宿）。原著核对：
    #   甲禄在寅 → 天体尾箕躔合（寅→尾箕）｜甲贵在未 → 天体井鬼躔合（未→井鬼）
    #   寅马在申 → 天体觜参躔合（申→觜参）｜壬禄在亥 → 天体室壁躔合（亥→室壁）。
    # 标准十二星次：娵訾亥(室壁)/降娄戌(奎娄)/大梁酉(昴毕胃)/实沈申(觜参)/鹑首未(井鬼)/
    #   鹑火午(柳星张)/鹑尾巳(翼轸)/寿星辰(角亢)/大火卯(氐房心)/析木寅(尾箕)/星纪丑(斗牛)/玄枵子(女虚危)。
    DIZHI_XIU_MAP = {
        '子': '女虚危', '丑': '斗牛', '寅': '尾箕', '卯': '氐房心',
        '辰': '角亢', '巳': '翼轸', '午': '柳星张', '未': '井鬼',
        '申': '觜参', '酉': '毕昴胃', '戌': '奎娄', '亥': '室壁'
    }

    # 十天干所带天乙贵人地支集合（静态贵人口诀，供"本命贵人"判定与回测核对）
    # 甲戊庚→丑未｜乙己→子申｜丙丁→亥酉｜壬癸→**巳卯**｜辛→**午寅**
    # 【2026-09-11 顺序订正】本表仅按"集合"语义使用（本命贵人命中判定），顺序无功能影响；
    #   但原列序 壬癸(卯巳)、辛(寅午) 与权威"昼贵在前"次序相反，易被下游复制误用，故正序。
    #   权威：《图解六壬大全》第1部 p.364「壬癸日昼贵巳，夜贵卯 / 辛日昼贵午，夜贵寅」。
    # 【本命贵人】命主本命支若落在某柱天干之贵人集合内，则该柱为"本命贵人"到位。
    #   如子命者，柱干乙/己之贵人支含"子"=本命 → 乙己年月日时即子命的贵人（乙己鼠猴乡）。
    GAN_GUIREN_ZHIS = {
        '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
        '乙': ['子', '申'], '己': ['子', '申'],
        '丙': ['亥', '酉'], '丁': ['亥', '酉'],
        '壬': ['巳', '卯'], '癸': ['巳', '卯'],
        '辛': ['午', '寅']
    }

    # 生肖映射（地支 → 属相）
    SHENGXIAO = {
        '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔', '辰': '龙',
        '巳': '蛇', '午': '马', '未': '羊', '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
    }

    # 本山禄神·双山纳甲取法（与贵人取干同理，取该干之禄神）
    # 双山分组：壬子/癸丑/艮寅/甲卯/乙辰/巽巳/丙午/丁未/坤申/庚酉/辛戌/乾亥；
    #   卦无禄干者纳甲取干（艮纳丙、巽纳辛、坤纳乙、乾纳甲）；
    #   四正位子午卯酉再并取所在后天卦宫纳甲干之禄（坎纳戊、震纳庚、离纳己、兑纳丁）。
    # 干禄：甲寅乙卯丙巳丁午戊巳己午庚申辛酉壬亥癸子。
    #   子→壬禄亥+坎纳戊禄巳｜卯→甲禄寅+震纳庚禄申｜午→丙禄巳+离纳己禄午｜酉→庚禄申+兑纳丁禄午。
    BEN_SHAN_LU_DSM = {
        '壬': ['亥'], '癸': ['子'], '丑': ['子'],
        '子': ['亥', '巳'],                                # 壬子双山壬禄亥 + 坎纳戊禄巳
        '艮': ['巳'], '寅': ['巳'],                        # 艮寅→艮纳丙→丙禄巳
        '甲': ['寅'],
        '卯': ['寅', '申'],                                # 甲卯双山甲禄寅 + 震纳庚禄申
        '乙': ['卯'], '辰': ['卯'],
        '巽': ['酉'], '巳': ['酉'],                        # 巽巳→巽纳辛→辛禄酉
        '丙': ['巳'],
        '午': ['巳', '午'],                                # 丙午双山丙禄巳 + 离纳己禄午
        '丁': ['午'], '未': ['午'],
        '坤': ['卯'], '申': ['卯'],                        # 坤申→坤纳乙→乙禄卯
        '庚': ['申'],
        '酉': ['申', '午'],                                # 庚酉双山庚禄申 + 兑纳丁禄午
        '辛': ['酉'], '戌': ['酉'],
        '乾': ['寅'], '亥': ['寅'],                        # 乾亥→乾纳甲→甲禄寅
    }

    def check_hulu_hugui(self, nian_gan: str, yue_gan: str, ri_gan: str, 
                          bm_gan: str, mountain: str, yue_zhi: str = '') -> Dict:
        """
        检查互禄互贵格（2026-08-26 修正）
        
        【互禄】禄神跨柱交叉对应：
          1. 年干禄是月干/日干/本命/坐山的贵人地支
             - LU[nian_gan] ∈ GAN_GUIREN_ZHIS[yue_gan/ri_gan/bm_gan]
             - LU[nian_gan] ∈ BEN_SHAN_GUIREN[mountain]
          2. 本命禄是坐山的贵人地支
             - LU[bm_gan] ∈ BEN_SHAN_GUIREN[mountain]
          3. 月禄（月干的禄）是年干/月干/日干/坐山的贵人地支
             - LU[yue_gan] ∈ GAN_GUIREN_ZHIS[nian_gan/yue_gan/ri_gan]
             - LU[yue_gan] ∈ BEN_SHAN_GUIREN[mountain]
        
        【互贵】贵人跨柱交叉对应（反向）：
          1. 年干贵人包含月干/日干/本命/坐山的禄地支
             - GAN_GUIREN_ZHIS[nian_gan] ∋ LU[yue_gan/ri_gan/bm_gan]
             - GAN_GUIREN_ZHIS[nian_gan] ∋ LU of 坐山
          2. 本命贵人包含坐山的禄地支
             - GAN_GUIREN_ZHIS[bm_gan] ∋ LU of 坐山
          3. 月贵人包含年干/月干/日干/坐山的禄地支
             - GAN_GUIREN_ZHIS[yue_gan] ∋ LU[nian_gan/yue_gan/ri_gan]
             - GAN_GUIREN_ZHIS[yue_gan] ∋ LU of 坐山
        
        互禄互贵是大六壬择日中非常重要的吉格，属于上上吉课的必要条件之一。
        """
        details = {
            'nian_gan': nian_gan, 'yue_gan': yue_gan, 'ri_gan': ri_gan,
            'bm_gan': bm_gan, 'mountain': mountain, 'yue_zhi': yue_zhi,
        }
        
        # --- 互禄检查 ---
        hulu_checks = []
        hulu_count = 0
        
        nian_lu_zhi = self.LU.get(nian_gan, '')    # 年干禄所在地支
        yue_lu_zhi = self.LU.get(yue_gan, '')       # 月干禄所在地支
        bm_lu_zhi = self.LU.get(bm_gan, '')         # 本命禄所在地支
        
        yue_gui_zhis = self.GAN_GUIREN_ZHIS.get(yue_gan, [])
        ri_gui_zhis = self.GAN_GUIREN_ZHIS.get(ri_gan, [])
        bm_gui_zhis = self.GAN_GUIREN_ZHIS.get(bm_gan, []) if bm_gan else []
        nian_gui_zhis = self.GAN_GUIREN_ZHIS.get(nian_gan, [])
        mtn_gui_zhis = self.BEN_SHAN_GUIREN.get(mountain, [])
        
        # 1. 年干禄是月干/日干/本命/坐山的贵人
        if nian_lu_zhi:
            targets = []
            if nian_lu_zhi in yue_gui_zhis:
                targets.append(f'月干贵人({yue_gan})')
            if nian_lu_zhi in ri_gui_zhis:
                targets.append(f'日干贵人({ri_gan})')
            if bm_gan and nian_lu_zhi in bm_gui_zhis:
                targets.append(f'本命贵人({bm_gan})')
            if nian_lu_zhi in mtn_gui_zhis:
                targets.append(f'坐山贵人({mountain})')
            if targets:
                hulu_count += len(targets)
                hulu_checks.append(f'年干{nian_gan}禄{nian_lu_zhi}为{", ".join(targets)}')
        
        # 2. 本命禄是坐山的贵人
        if bm_gan and bm_lu_zhi and mtn_gui_zhis:
            if bm_lu_zhi in mtn_gui_zhis:
                hulu_count += 1
                hulu_checks.append(f'本命{bm_gan}禄{bm_lu_zhi}为坐山{mountain}贵人')
        
        # 3. 月禄（月干的禄）是年干/月干/日干/坐山的贵人
        if yue_lu_zhi:
            targets = []
            if yue_lu_zhi in nian_gui_zhis:
                targets.append(f'年干贵人({nian_gan})')
            if yue_lu_zhi in yue_gui_zhis:
                targets.append(f'月干贵人({yue_gan})')
            if yue_lu_zhi in ri_gui_zhis:
                targets.append(f'日干贵人({ri_gan})')
            if yue_lu_zhi in mtn_gui_zhis:
                targets.append(f'坐山贵人({mountain})')
            if targets:
                hulu_count += len(targets)
                hulu_checks.append(f'月干{yue_gan}禄{yue_lu_zhi}为{", ".join(targets)}')
        
        # --- 互贵检查 ---
        hugui_checks = []
        hugui_count = 0
        
        # 坐山禄地支集合（BEN_SHAN_LU_DSM 存储的是禄神所在地支）
        mtn_lu_zhis = set(self.BEN_SHAN_LU_DSM.get(mountain, []))
        
        # 天干禄地支字典（用于反向查询）
        gan_lu_zhi_map = {g: self.LU.get(g, '') for g in [nian_gan, yue_gan, ri_gan, bm_gan] if g}
        
        # 1. 年干贵人包含月干/日干/本命/坐山的禄
        if nian_gui_zhis:
            lu_targets = []
            for gan, lu_zhi in [('月干', yue_gan), ('日干', ri_gan), ('本命', bm_gan)]:
                if lu_zhi and gan_lu_zhi_map.get(lu_zhi, '') in nian_gui_zhis:
                    lu_targets.append(f'{gan}禄({gan_lu_zhi_map[lu_zhi]})')
            for lu_zhi in mtn_lu_zhis:
                if lu_zhi in nian_gui_zhis:
                    lu_targets.append(f'坐山禄({lu_zhi})')
            if lu_targets:
                hugui_count += len(lu_targets)
                hugui_checks.append(f'年干{nian_gan}贵人含{", ".join(lu_targets)}')
        
        # 2. 本命贵人包含坐山的禄
        if bm_gan and bm_gui_zhis and mtn_lu_zhis:
            matched = [lu for lu in mtn_lu_zhis if lu in bm_gui_zhis]
            if matched:
                hugui_count += len(matched)
                hugui_checks.append(f'本命{bm_gan}贵人含坐山禄({", ".join(matched)})')
        
        # 3. 月贵人包含年干/月干/日干/坐山的禄
        if yue_gui_zhis:
            lu_targets = []
            for gan_name, gan in [('年干', nian_gan), ('月干', yue_gan), ('日干', ri_gan)]:
                lu = gan_lu_zhi_map.get(gan, '')
                if lu and lu in yue_gui_zhis:
                    lu_targets.append(f'{gan_name}禄({lu})')
            for lu_zhi in mtn_lu_zhis:
                if lu_zhi in yue_gui_zhis:
                    lu_targets.append(f'坐山禄({lu_zhi})')
            if lu_targets:
                hugui_count += len(lu_targets)
                hugui_checks.append(f'月干{yue_gan}贵人含{", ".join(lu_targets)}')
        
        is_hulu = hulu_count > 0
        is_hugui = hugui_count > 0
        
        return {
            'is_hulu': is_hulu,
            'is_hugui': is_hugui,
            'is_mutual_lu_gui': is_hulu or is_hugui,
            'is_full_mutual': is_hulu and is_hugui,
            'hulu_count': hulu_count,
            'hugui_count': hugui_count,
            'details': {
                **details,
                'nian_lu_zhi': nian_lu_zhi,
                'yue_lu_zhi': yue_lu_zhi,
                'bm_lu_zhi': bm_lu_zhi,
                'mtn_lu_zhis': list(mtn_lu_zhis),
                'hulu_checks': hulu_checks,
                'hugui_checks': hugui_checks,
                'hulu_summary': f'互禄命中{hulu_count}项：{"；".join(hulu_checks) if hulu_checks else "无"}',
                'hugui_summary': f'互贵命中{hugui_count}项：{"；".join(hugui_checks) if hugui_checks else "无"}',
            }
        }

    def get_ben_shan_lu_dsm(self, mountain: str) -> List:
        """获取本山双山纳甲禄神列表（原旧表 BEN_SHAN_LU 已删除，仅用双山纳甲口径）"""
        return self.BEN_SHAN_LU_DSM.get(mountain, [])

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
        """精确计算月将(2024-2027中气precomputed，跨年自动处理)"""
        from datetime import date
        zq = {
            2024:{1:20,2:19,3:20,4:19,5:20,6:21,7:22,8:22,9:22,10:23,11:22,12:21},
            2025:{1:20,2:18,3:20,4:20,5:21,6:21,7:22,8:23,9:23,10:23,11:22,12:21},
            2026:{1:20,2:18,3:20,4:20,5:21,6:21,7:23,8:23,9:23,10:23,11:22,12:22},
            2027:{1:20,2:19,3:21,4:20,5:21,6:21,7:23,8:23,9:23,10:24,11:22,12:22},
            2028:{1:20,2:19,3:20,4:19,5:20,6:21,7:22,8:23,9:22,10:23,11:22,12:21},
            2029:{1:20,2:18,3:20,4:20,5:21,6:21,7:23,8:23,9:23,10:23,11:22,12:22},
            2030:{1:20,2:19,3:20,4:20,5:21,6:21,7:23,8:23,9:23,10:23,11:22,12:22},
            2031:{1:20,2:19,3:21,4:20,5:21,6:21,7:23,8:23,9:23,10:24,11:22,12:22},
            2032:{1:20,2:19,3:20,4:19,5:20,6:21,7:22,8:22,9:22,10:23,11:22,12:21},
            2033:{1:20,2:18,3:20,4:20,5:21,6:21,7:22,8:23,9:23,10:23,11:22,12:21},
            2034:{1:20,2:18,3:20,4:20,5:21,6:21,7:23,8:23,9:23,10:23,11:22,12:22},
            2035:{1:20,2:19,3:21,4:20,5:21,6:21,7:23,8:23,9:23,10:24,11:22,12:22},
        }
        today = date(year, month, day)

        # 确定包含today的节气周期: 从上一个冬至开始，到下一个小雪结束
        # 如果today >= 当年冬至(12月) → 使用当年的冬至作为起点
        # 否则 → 使用上一年的冬至作为起点
        this_dz = date(year, 12, zq.get(year, {12:22}).get(12, 22))
        if today >= this_dz:
            base_year = year  # 当年冬至已过
        else:
            base_year = year - 1  # 还在上一年冬至周期中

        d = zq.get(base_year, {m:20 for m in range(1,13)})
        next_d = zq.get(base_year+1, {m:20 for m in range(1,13)})

        # 12个中气边界，从当年冬至到下一年小雪
        # 月将映射: 子月=丑将, 丑月=子将, 寅月=亥将, 卯月=戌将, 辰月=酉将, 巳月=申将, 午月=未将, 未月=午将, 申月=巳将, 酉月=辰将, 戌月=卯将, 亥月=寅将
        YJ_LIST = ['丑','子','亥','戌','酉','申','未','午','巳','辰','卯','寅']
        boundaries = [
            date(base_year,12,d[12]),  # 冬至
            date(base_year+1,1,next_d[1]),   # 大寒
            date(base_year+1,2,next_d[2]),   # 雨水
            date(base_year+1,3,next_d[3]),   # 春分
            date(base_year+1,4,next_d[4]),   # 谷雨
            date(base_year+1,5,next_d[5]),   # 小满
            date(base_year+1,6,next_d[6]),   # 夏至
            date(base_year+1,7,next_d[7]),   # 大暑
            date(base_year+1,8,next_d[8]),   # 处暑
            date(base_year+1,9,next_d[9]),   # 秋分
            date(base_year+1,10,next_d[10]), # 霜降
            date(base_year+1,11,next_d[11]), # 小雪
        ]
        result = '寅'  # fallback
        for i in range(len(boundaries)):
            if today >= boundaries[i]:
                result = YJ_LIST[i]
        return result

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
        """获取贵人位置（返回**地盘支**）
        【BUG-FIX 2026-08-18】arrange_gui_ren_pan 的'天将映射'键为**天盘支**，
        原直接返回 → 与禄马（已转地盘支）口径不一致，三传匹配/到山到向全错位。
        现经 _get_tiandi_position 转为地盘支，与 check_pillar_all_qualified 的禄马口径统一。"""
        if not self.gui_ren_calc:
            return None
        try:
            guiren_info = self.gui_ren_calc.arrange_gui_ren_pan(
                tian_gan, {'天地对应': tiandi_pan}, shichen
            )
            tianjiang_map = guiren_info.get('天将映射', {})
            for zhi, tj in tianjiang_map.items():
                if tj == '贵人':
                    return self._get_tiandi_position(zhi, tiandi_pan)
        except Exception:
            pass
        return None
    
    def check_pillar_all_qualified(self, tian_gan: str, di_zhi: str,
                                    tiandi_pan: Dict, shichen: str,
                                    shan_jia: str, xiang_shou: str) -> bool:
        """
        检查某柱的禄、马、贵人是否至少有一个到山或到向

        重要：禄马贵人指的是天盘的地支，不是地盘的地支！
        癸禄在天盘子 → 天盘子转动后对应地盘申 → 检查申是否到山或向

        参数:
            tian_gan: 天干
            di_zhi: 地支
            tiandi_pan: 天地盘（格式：{地盘地支: 天盘地支}）
            shichen: 时辰
            shan_jia: 山家
            xiang_shou: 向首

        返回:
            True 如果禄、马、贵人至少有一个到山或到向
        """
        lu_zhi = self.get_lu_zhi(tian_gan)
        ma_zhi = self.get_ma_zhi(di_zhi)
        guiren_zhi = self.get_guiren_zhi(tian_gan, tiandi_pan, shichen)

        # 禄马贵人需要从天盘查找，不是直接用地盘的禄位
        # 癸禄在地盘子，天盘子转动后对应地盘申
        tianpan_lu_zhi = self._get_tiandi_position(lu_zhi, tiandi_pan)
        tianpan_ma_zhi = self._get_tiandi_position(ma_zhi, tiandi_pan)

        # 贵人在天盘已经是查找到的天盘位置，直接用
        tianpan_guiren_zhi = guiren_zhi

        # 检查是否到山或到向（主吉应）
        lu_qualified = (tianpan_lu_zhi == shan_jia or tianpan_lu_zhi == xiang_shou) if tianpan_lu_zhi else False
        ma_qualified = (tianpan_ma_zhi == shan_jia or tianpan_ma_zhi == xiang_shou) if tianpan_ma_zhi else False
        guiren_qualified = (tianpan_guiren_zhi == shan_jia or tianpan_guiren_zhi == xiang_shou) if tianpan_guiren_zhi else False

        # 三合次吉应：禄/马/贵人的三合伙伴临山或向
        # 【2026-08-24 修复】原 lu_sanhe/ma_sanhe 计算后未被 return 使用（死代码），且贵人缺三合；现一并启用
        lu_sanhe = (tianpan_lu_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                    tianpan_lu_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if tianpan_lu_zhi else False
        ma_sanhe = (tianpan_ma_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                    tianpan_ma_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if tianpan_ma_zhi else False
        guiren_sanhe = (tianpan_guiren_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                        tianpan_guiren_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if tianpan_guiren_zhi else False

        return (lu_qualified or ma_qualified or guiren_qualified) or (lu_sanhe or ma_sanhe or guiren_sanhe)

    def check_pillar_direct_qualified(self, tian_gan: str, di_zhi: str,
                                      tiandi_pan: Dict, shichen: str,
                                      shan_jia: str, xiang_shou: str) -> bool:
        """【严格直达口径】禄/马/贵人**加临后正好落山家或向首** —— 不含三合次吉。

        【为何单列】2026-09-07 憨爷拍板：「到山到向 = 禄马贵加临后正好落山家/向首
        （**不含三合次吉**）」，已应用于 calculate_new_score 四柱合格 / analyze_yidu_full
        daoshan_daoxiang / 顶格择日三处。但 `check_pillar_all_qualified`（含三合次吉的**宽口径**）
        仍被 stock_dashboard 本命评分(⑦)调用，导致：
          ① 宽口径枚举 207360 组样本通过率 **89.6%**（直临仅 41.6%，三合单独贡献 48.0pp）
             → 本命「禄马贵到山向」加分 +8 近乎**恒得**，失去区分度；
          ② 同一响应体内 `luma_qualified`(宽) 与 `lu/ma/guiren.to_shan/to_xiang`(严) 自相矛盾
             —— 与 2026-09-07 修掉的 `analyze_yidu_full` 同款问题。
        故抽出本函数作为**唯一的严格口径入口**，供评分/展示/本命路径统一调用。
        判定等价于 check_single_pillar 的 (shan_count>=1 or xiang_count>=1)。
        """
        r = self.check_single_pillar(tian_gan, di_zhi, tiandi_pan, shichen,
                                     shan_jia, xiang_shou)
        return bool((r.get('shan_count') or 0) >= 1 or (r.get('xiang_count') or 0) >= 1)

    def _get_tiandi_position(self, dizhi: str, tiandi_pan: Dict) -> Optional[str]:
        """
        获取地支在天盘转动后对应的实际地盘位置

        例如：癸禄在地盘子，天盘子转动后对应地盘申
        tiandi_pan = {子: 申, 丑: 酉, ...}
        要找：天盘=子 对应的地盘 = 申

        参数:
            dizhi: 地支
            tiandi_pan: 天地盘（格式：{地盘地支: 天盘地支}）

        返回:
            转换后的地盘地支
        """
        if not dizhi or not tiandi_pan:
            return dizhi

        for di, tian in tiandi_pan.items():
            if tian == dizhi:
                return di

        return dizhi
    
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
        # 【2026-09-06 BUG-FIX 坐标系混用】贵人"发三传"必须看传支（天盘支）所乘天将是否为贵人，
        #   不能再用 get_guiren_zhi（贵人加临的**地盘宫位**）与传支做字面匹配——
        #   例：初玄武·中朱雀·末白虎 的课，夜贵申加临**地盘卯宫**，而"卯"是**天盘传支**（在戌宫
        #   乘白虎），旧代码把二字面"卯"判成贵人命中 → 假阳性，禄马贵计数虚高。
        #   修正后按天将口径：三传乘将无贵人 → 贵人不计数，与用户核对结论一致。
        _guiren_hit = self._sanchuan_guiren_hit(sanchuan, ri_gan, tiandi_pan, shichen)

        count = 0
        if ri_lu and ri_lu in chuan_list:
            count += 1
        if ri_ma and ri_ma in chuan_list:
            count += 1
        if _guiren_hit:
            count += 1

        return count

    def check_ymr_sanchuan_luma_guiren_count(self, sanchuan: Dict,
                                             nian_gan: str, nian_zhi: str,
                                             yue_gan: str, yue_zhi: str,
                                             ri_gan: str, ri_zhi: str,
                                             tiandi_pan: Dict = None,
                                             shichen: str = None) -> int:
        """
        【2026-09-06 用户口径】年月日禄马贵人发三传计数（0-3）：
          禄 = 年/月/日三干之禄任一支入传；
          马 = 年/月/日三支之驿马任一支入传；
          贵 = 日干贵人乘传（天将口径，与 _sanchuan_guiren_hit 一致）。
        每类命中计 1，∞3。 时柱禄马贵人仅作优先项，不计入发传硬闸。
        """
        chuan_set = set(c for c in self._chuan_list(sanchuan) if c)
        lu_set = {self.LU.get(nian_gan), self.LU.get(yue_gan), self.LU.get(ri_gan)}
        ma_set = {self.YIMA.get(nian_zhi), self.YIMA.get(yue_zhi), self.YIMA.get(ri_zhi)}
        count = 0
        if lu_set & chuan_set:
            count += 1
        if ma_set & chuan_set:
            count += 1
        if self._sanchuan_guiren_hit(sanchuan, ri_gan, tiandi_pan, shichen):
            count += 1
        return count

    @staticmethod
    def _chuan_list(sanchuan: Dict) -> list:
        """兼容两种三传结构：{'三传': [...]} 或 {'初传','中传','末传'}"""
        if not sanchuan:
            return []
        if '三传' in sanchuan and isinstance(sanchuan.get('三传'), list):
            return sanchuan['三传']
        return [sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]

    def _sanchuan_guiren_hit(self, sanchuan: Dict, ri_gan: str,
                              tiandi_pan: Dict = None, shichen: str = None) -> bool:
        """是否命中贵人发传（bool 版，供 count 使用）"""
        return bool(self._sanchuan_guiren_chuan(sanchuan, ri_gan, tiandi_pan, shichen))

    def _sanchuan_guiren_chuan(self, sanchuan: Dict, ri_gan: str,
                               tiandi_pan: Dict = None, shichen: str = None) -> set:
        """
        【2026-09-06】贵人发传判定（天将口径）：
        返回三传传支（天盘支）中乘天将==贵人的传支集合。
        仅当有天地盘+时辰时按乘将判定；无盘时退化：贵人本支（静态表）命中传支。
        （旧 get_guiren_zhi 返回"贵人加临的地盘宫位"，与传支字面匹配 → 坐标系混用假阳性）
        """
        chuan_list = self._chuan_list(sanchuan)
        chuan_set = set(c for c in chuan_list if c)
        if tiandi_pan and shichen and self.gui_ren_calc:
            try:
                guiren_info = self.gui_ren_calc.arrange_gui_ren_pan(
                    ri_gan, {'天地对应': tiandi_pan}, shichen)
                tianjiang_map = guiren_info.get('天将映射', {})
                return {c for c in chuan_list if c and tianjiang_map.get(c) == '贵人'}
            except Exception:
                pass
        # 无天地盘退化：日贵本支（静态表）命中传支
        return chuan_set & set(self.GAN_GUIREN_ZHIS.get(ri_gan, []))

    def get_taiyang_position(self, gregorian_month: int, day: int, year: int = None) -> str:
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
            year: 公历年份；缺省取当前年（【2026-08-24 修复】原硬编码 2026，
                  跨年/超出节气表会算错或回退"寅"，现改为可传 year 动态获取）

        返回:
            太阳/月将所在宫位
        """
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        return self.get_yuejiang_by_date(year, gregorian_month, day)

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
                                   gregorian_month: int = None, year: int = None) -> Dict:
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
            year: 公历年份（缺省取当前年），用于太阳走宫精确计算
        """
        if not gregorian_month:
            gregorian_month = 6
        taiyang = self.get_taiyang_position(gregorian_month, 15, year)

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

    def get_dizhi_xiu(self, dizhi: str) -> str:
        """地支宫位 → 二十八宿（躔合宿名）。如 申→觜参、亥→室壁、寅→尾箕、未→井鬼。"""
        return self.DIZHI_XIU_MAP.get(dizhi, '')

    def check_sun_chanhe_daoshan(self, mountain: str, shichen: str,
                                  tian_gan: str, di_zhi: str,
                                  shan_jia: str = None, xiang_shou: str = None,
                                  year: int = None, month: int = None, day: int = None,
                                  yuejiang: str = None) -> Dict:
        """
        太阳躔度·合方之法（《仪度六壬择日要诀》"先查之法/合方之法"）

        原著：
          "先查之法，如申上天体觜参，查系寅方马位；亥上天体室壁，查系壬方禄位。
           合方之法，如乙向贵人在申，则求天体在申之觜参轮加辰上；
           丁山贵人在亥，则求天体在亥之室壁轮加未上是也。"
          "以甲寅日论：酉神加巳则立夏前后太阳在酉，以酉之躔合加巳支上轮之，
           而酉后一位申马之躔合在辰……"（申马真到辰＝天罡位）
          "以壬午日论：申神加辰则芒种前后太阳在申，以申之躔合加辰支上轮之，
           而申前四位亥禄之躔合在未……"（亥禄真到未＝小吉位）

        机制（六壬天地盘＝太阳加时）：
          太阳（月将）加占时 → 排天地盘 → 该柱禄/马/贵在天盘之支加临到地盘之支
          ＝天体（二十八宿）躔合加临后的"真到"方位 → 若==坐山/向首 则"临山/照向"。

        参数:
            mountain: 坐山
            shichen: 占时
            tian_gan: 柱天干（取禄/贵）
            di_zhi: 柱地支（取马）
            shan_jia / xiang_shou: 山家/向首（缺省自动取）
            year/month/day: 公历日期（太阳过宫精确计算，可选）
            yuejiang: 月将（可选，缺省用日期或默认）

        返回:
            { taiyang(月将), taiyang_xiu, tiandi_pan, items: [{type, zhi, xiu, daoshan_zhi, to_shan, to_xiang}],
              hit_count, qualified, description }
        """
        if shan_jia is None:
            shan_jia = self.get_shan_jia(mountain)
        if xiang_shou is None:
            xiang_shou = self.get_xiang_shou(mountain)

        # 太阳（月将）定位：日期→精确月将；否则用传入或月支推算
        if not yuejiang:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = '亥'  # 默认
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)

        # 该柱的禄 / 马 / 贵（天盘支）
        lu_zhi = self.get_lu_zhi(tian_gan)
        ma_zhi = self.get_ma_zhi(di_zhi)
        guiren_zhi = self.get_guiren_zhi(tian_gan, tiandi_pan, shichen)  # 已转地盘支

        items = []
        for typ, zhi in [('禄', lu_zhi), ('马', ma_zhi)]:
            if not zhi:
                continue
            daoshan = self._get_tiandi_position(zhi, tiandi_pan)  # 天盘zhi加临地盘位
            items.append({
                'type': typ, 'zhi': zhi,
                'xiu': self.get_dizhi_xiu(zhi),
                'daoshan_zhi': daoshan,
                'to_shan': daoshan == shan_jia,
                'to_xiang': daoshan == xiang_shou,
            })
        # 贵人（get_guiren_zhi 已按天盘加临转地盘）
        if guiren_zhi:
            items.append({
                'type': '贵', 'zhi': guiren_zhi,
                'xiu': self.get_dizhi_xiu(guiren_zhi),
                'daoshan_zhi': guiren_zhi,
                'to_shan': guiren_zhi == shan_jia,
                'to_xiang': guiren_zhi == xiang_shou,
            })

        hit = [it for it in items if it['to_shan'] or it['to_xiang']]
        desc = f'太阳躔度（月将{yuejiang}）：'
        desc += '；'.join(
            f'{it["type"]}{it["zhi"]}（{it["xiu"]}）加临{it["daoshan_zhi"]}{"到山" if it["to_shan"] else ""}{"照向" if it["to_xiang"] else ""}'
            for it in items
        ) if items else '本柱无禄马贵'

        return {
            'taiyang': yuejiang,
            'taiyang_xiu': self.get_dizhi_xiu(yuejiang),
            'tian_gan': tian_gan, 'di_zhi': di_zhi,
            'items': items,
            'hit_count': len(hit),
            'qualified': len(hit) >= 1,
            'description': desc,
        }

    def calc_sun_chanhe_bonus(self, mountain: str, shichen: str,
                              shan_jia: str = None, xiang_shou: str = None,
                              nian_gan: str = '', nian_zhi: str = '',
                              yue_gan: str = '', yue_zhi: str = '',
                              ri_gan: str = '', ri_zhi: str = '',
                              shi_gan: str = '', shi_zhi: str = '',
                              yuejiang: str = None) -> Dict:
        """
        太阳躔度·合方法 加分（切实到山向，接入评分）

        《要诀》"山向实得禄马贵人则不是虚空之活已"——合方法以太阳躔合加临定禄马贵
        "真到"方位，较"太阳宫==山"（check_taiyang_luma_guiren）更切实，作加分项。

        分值：
          日柱禄/马/贵真到山或向 → +10（日柱为课之主，最贵）
          年月时柱真到山或向     → 每柱 +3
        返回 { bonus, details(逐柱), hit_pillars, ri_qualified }
        """
        if shan_jia is None:
            shan_jia = self.get_shan_jia(mountain)
        if xiang_shou is None:
            xiang_shou = self.get_xiang_shou(mountain)

        details = {}
        bonus = 0
        hit = []
        for pname, pg, pz in [('年', nian_gan, nian_zhi), ('月', yue_gan, yue_zhi),
                              ('日', ri_gan, ri_zhi), ('时', shi_gan, shi_zhi)]:
            if not pg or not pz:
                continue
            r = self.check_sun_chanhe_daoshan(
                mountain, shichen, pg, pz, shan_jia, xiang_shou, yuejiang=yuejiang)
            details[pname] = r
            if r['qualified']:
                hit.append(pname)
                bonus += 10 if pname == '日' else 3

        return {
            'bonus': bonus,
            'details': details,
            'hit_pillars': hit,
            'ri_qualified': bool(details.get('日', {}).get('qualified', False)),
        }

    def check_riyue_hesu_daoshan(self, mountain: str, shichen: str,
                                 shan_jia: str = None, xiang_shou: str = None,
                                 year: int = None, month: int = None, day: int = None,
                                 yuejiang: str = None) -> Dict:
        """
        日月合塑 / 日月对望 判定（《仪度六壬择日要诀》吊天星第二课）

        原著（"吊天星"节）：
          "日月合塑即太阳和月亮重叠到山或到向；
           日月对望即太阳到山同时月亮到向，或月亮到山同时太阳到向。
           造葬能同时得到太阳和月亮的吉气纳入，自然福力巨大。"
          "唯每年太阳太阴在上合朔十二次，因分天体有十二躔舍。"

        机制（与太阳躔度合方之法同排盘）：
          太阳（月将）加占时 → 天地盘；太阳宫位与月亮宿宫位（XIU_ZHI 地支宫）
          各自经天盘加临后的"真到"地盘支：
            - 日月同宫（太阳宫==月亮宫），真到==坐山/向首  → 日月合塑
            - 日真到==坐山 且 月真到==向首（或反之）      → 日月对望

        参数:
            mountain: 坐山
            shichen: 占时
            shan_jia / xiang_shou: 山家/向首（缺省自动取）
            year/month/day: 公历日期（太阳精确过宫 + 月亮精确躔度，可选）
            yuejiang: 月将（可选，缺省用日期或默认）

        返回:
            { type: '合塑'|'对望'|'无', sun_zhi, moon_zhi, moon_xiu,
              sun_dao, moon_dao, hits: [..], qualified, description }
        """
        try:
            from engine.moon_liangdu import moon_liangdu
        except Exception:
            moon_liangdu = None
        if shan_jia is None:
            shan_jia = self.get_shan_jia(mountain)
        if xiang_shou is None:
            xiang_shou = self.get_xiang_shou(mountain)

        # 太阳（月将）定位：日期→精确月将；否则用传入或默认
        if not yuejiang:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = '亥'
        # 【2026-09-07 真实天文修复】古法月宿（moon_liangdu：《通解》初一固定宿逐日推）与真实太阳宫
        #   相位永远错位 → 30年0合朔（"更详七政历细度为准"）。改用 sxtwl 真实农历日判朔/望：
        #   朔日（月龄≈1：日月同黄经）→ 日月重叠=合塑前提；望日（月龄≈15）→ 日月对宫。
        moon_zhi = ''
        moon_xiu = ''
        is_shuo = is_wang = False
        try:
            import sxtwl as _sx
            if year and month and day:
                _lun = _sx.fromSolar(year, month, day)
                _ld = int(_lun.getLunarDay())
                is_shuo = _ld <= 2 or _ld >= 28   # 朔前后
                is_wang = 14 <= _ld <= 16         # 望前后
        except Exception:
            pass
        # 月亮宫：朔=与日同宫（重叠）；望=日对宫（地支+6）
        if is_shuo or is_wang:
            _szi = self.DIZHI_ORDER.index(yuejiang) if yuejiang in self.DIZHI_ORDER else 0
            moon_zhi = yuejiang if is_shuo else self.DIZHI_ORDER[(_szi + 6) % 12]

        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
        sun_dao = self._get_tiandi_position(yuejiang, tiandi_pan)   # 太阳真到
        moon_dao = self._get_tiandi_position(moon_zhi, tiandi_pan) if moon_zhi else ''

        hits = []
        hes = '无'
        if is_shuo and sun_dao in (shan_jia, xiang_shou):
            hes = '合塑'
            hits.append(f'朔日日月重叠，太阳真到{"山" if sun_dao == shan_jia else "向"}({sun_dao})')
        elif is_wang and moon_zhi:
            if sun_dao == shan_jia and moon_dao == xiang_shou:
                hes = '对望'
                hits.append(f'望日日到山({sun_dao})月到向({moon_dao})')
            elif moon_dao == shan_jia and sun_dao == xiang_shou:
                hes = '对望'
                hits.append(f'望日月到山({moon_dao})日到向({sun_dao})')

        desc = f'日月{"合塑" if hes == "合塑" else ("对望" if hes == "对望" else "")}：' \
               f'太阳{yuejiang}真到{sun_dao}；月亮{"同宫" if is_shuo else ("对宫" if is_wang else "")}{moon_zhi or "—"}真到{moon_dao or "—"}' \
               + (f'（农历日={"朔" if is_shuo else ("望" if is_wang else "—")}）' if (is_shuo or is_wang) else '')
        if hits:
            desc += '；' + '；'.join(hits)

        return {
            'type': hes,
            'sun_zhi': yuejiang,
            'moon_zhi': moon_zhi,
            'moon_xiu': moon_xiu,
            'sun_dao': sun_dao,
            'moon_dao': moon_dao,
            'hits': hits,
            'qualified': hes in ('合塑', '对望'),
            'description': desc,
        }

    def calc_riyue_hesu_bonus(self, mountain: str, shichen: str,
                              shan_jia: str = None, xiang_shou: str = None,
                              year: int = None, month: int = None, day: int = None,
                              yuejiang: str = None) -> Dict:
        """
        日月合塑/日月对望 加分（《要诀》"福力最巨大"，附加于合方之法）

        分值（设计上限，与 sun_chanhe 加分同层级、可叠加）：
          日月合塑到山/向   → +10（日月重叠，福力最巨大）
          日月对望         → +8
        返回 { bonus, type, details }
        """
        r = self.check_riyue_hesu_daoshan(
            mountain, shichen, shan_jia, xiang_shou,
            year, month, day, yuejiang)
        bonus = 10 if r['type'] == '合塑' else (8 if r['type'] == '对望' else 0)
        return {
            'bonus': bonus,
            'type': r['type'],
            'details': r,
        }

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
                            ke_ti_list: List = None,
                            yuejiang: str = None,
                            ben_ming: str = None, ben_ming_gan: str = None,
                            year: int = None, month: int = None, day: int = None) -> Dict:
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
        # 【2026-09-05 统一】太阳（月将）定位优先级与 analyze_full 一致：
        #   显式 yuejiang > 日期节气过宫 get_yuejiang_by_date > 月支映射 get_yuejiang。
        #   三传禄马贵（check_sanchuan_luma_guiren(_count)）共用本 tiandi_pan，口径随之统一。
        if yuejiang is None:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = self.get_yuejiang(yue_zhi) if yue_zhi else '亥'
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
        
        # 1. 检查四柱禄马贵人是否都到山到向
        # 【2026-09-07 用户拍板：严格直达】"到山到向"= 禄马贵加临后正好落山家/向首（不含三合次吉）。
        #    check_pillar_all_qualified 含三合次吉（宽松），评分/展示/顶格三处口径须统一 → 改严格直达。
        def _pillar_qualified_strict(g, z):
            try:
                _sp = self.check_single_pillar(g, z, tiandi_pan, shichen, shan_jia, xiang_shou, '')
                return bool((_sp.get('lu_to_shan') or _sp.get('lu_to_xiang') or
                             _sp.get('ma_to_shan') or _sp.get('ma_to_xiang') or
                             _sp.get('guiren_to_shan') or _sp.get('guiren_to_xiang')))
            except Exception:
                return False
        nian_qualified = _pillar_qualified_strict(nian_gan, nian_zhi)
        yue_qualified = _pillar_qualified_strict(yue_gan, yue_zhi)
        ri_qualified = _pillar_qualified_strict(ri_gan, ri_zhi)
        shi_qualified = (_pillar_qualified_strict(shi_gan, shi_zhi)
                         if shi_gan and shi_zhi else False)
        
        pillar_qualified_count = sum([nian_qualified, yue_qualified, ri_qualified, shi_qualified])
        
        # 2. 检查三传禄马贵人数量
        # 【2026-09-07 用户拍板统一】发传计数用"年月日禄马贵"口径（check_ymr_...，与顶格判定/前端
        #   同口径）。旧用日柱口径（check_sanchuan_luma_guiren_count）→ 同课"年月日2个达标 vs 日柱1个
        #   不达标被压档"分裂（2027-02-17 寅时实测）。
        sanchuan_luma_count = 0
        sanchuan_qualified = False
        jianshen_guiren_info = {'count': 0, 'items': []}
        if sanchuan:
            sanchuan_luma_count = self.check_ymr_sanchuan_luma_guiren_count(
                sanchuan, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi,
                tiandi_pan, shichen
            )
            # 三传中至少2个禄马贵人
            sanchuan_qualified = sanchuan_luma_count >= 2
            
            # 检查三传间神贵人（传间见贵）
            _sanchuan_detail = self.check_sanchuan_luma_guiren(
                sanchuan, ri_gan, ri_zhi,
                nian_gan=nian_gan, nian_zhi=nian_zhi,
                yue_gan=yue_gan, yue_zhi=yue_zhi,
                tiandi_pan=tiandi_pan, shichen=shichen
            )
            jianshen_guiren_info = {
                'count': _sanchuan_detail.get('jianshen_guiren_count', 0),
                'items': _sanchuan_detail.get('jianshen_guiren', [])
            }
        
        # 3. 计算基础评分
        # 满分条件：4柱合格 + 三传至少2个禄马贵人
        # 平课条件：0柱合格 + 三传0个禄马贵人

        # 4. 课体课格修正（【2026-09-05 统一拍板口径】改用 apply_keti_adjustment：
        #    十三吉课 1-2 个 +10 / ≥3 个 +20；非十三吉课凶课扣分封顶 -20；吉课非十三/平/小吉 0 不加不减。
        #    替代旧 get_keti_deduction（凶课可扣至 -40、平课 -10、无十三吉课加分），
        #    使 luma_base(final_score) 与 analyze_full/批量同口径，且与 1b 展示 keti_adjust 一致。
        #    【2026-09-05 提前计算】课体判定需在 base 分档前完成，供"荣华课三传合格档让位"去重）
        ke_ti_deduction = 0
        ke_ti_level = '未知'
        is_daxiong = False
        _keti_adj = {'jike_hits': 0, 'keti_level': '平课', 'add': 0, 'deduct': 0, 'ke_score': 0,
                     'note': '无课体信息，课体不加不减'}
        if ke_ti_list:
            ke_ti_name = ke_ti_list[0] if isinstance(ke_ti_list, list) else str(ke_ti_list)
            # 【2026-09-05 十三吉课精细判据】构造 jike_ctx（sike/三传/天将/禄马/龙德），
            #   使 apply_keti_adjustment 以 jike_13.check_jike_13 逐课按64课经落码判定
            _jike_ctx = self._build_jike_ctx(
                ri_gan, ri_zhi, nian_zhi, yue_zhi, sanchuan, tiandi_pan, shichen, ben_ming or '',
                shan_jia, xiang_shou, mountain,
                nian_gan=nian_gan or '', yue_gan=yue_gan or '', yuejiang=yuejiang or '')
            _keti_adj = self.apply_keti_adjustment(ke_ti_name, jike_ctx=_jike_ctx)
            ke_ti_deduction = _keti_adj['ke_score']      # 带符号净额（+加分 / -扣分）
            ke_ti_level = _keti_adj['keti_level']
            is_daxiong = _keti_adj.get('deduct', 0) >= 20

        # 【2026-09-05 三传禄马贵充分类吉课·合格档让位】荣华课（禄马贵三传全备）与富贵课（天干二贵
        #   皆在三传）⇒ 三传禄马贵≥2 100% 蕴含；luma_base 内"三传合格档(+3/满档)"与"课体修正
        #   (+10~20)"为同一"三传禄马贵充分"双计。修复：命中时三传合格档让位（不计入满足项），
        #   由课体修正独享（用户拍板 2026-09-05）。
        _lmg_full_hit = any(k in str(_keti_adj.get('jike_details') or [])
                            for k in ('三传全备', '天干二贵'))

        # 满足的项数：四柱合格数 + (三传合格 ? 1 : 0)（荣华/富贵命中时三传项让位）
        satisfied_items = pillar_qualified_count
        if sanchuan_qualified and not _lmg_full_hit:
            satisfied_items += 1

        # 每项扣分：3分（用户要求）
        item_deduction = 3

        # 基础得分 = 100 - (5 - 满足项数) * 3
        base_score = 100 - (5 - satisfied_items) * item_deduction
        base_score = max(60, min(100, base_score))  # 限制在60-100之间

        # 5. 最终得分（ke_score 已带符号：凶课负、十三吉课正）
        final_score = base_score + ke_ti_deduction
        final_score = max(30, min(100, final_score))  # 最低30分
        # 【2026-09-06 铁律硬闸·禄马贵人发三传】古法"禄马贵人发出三传方为吉课之用"：
        #   四柱到山到向再齐，三传禄马贵 <2（未发全）亦非大用 → 六壬分降档封顶 89（掉出上上吉）。
        #   防"base97灌满+bonus顶100"式的虚满（用户核对 2027-05-15 甲午日课发现：三传仅发禄1个却得100）。
        if not sanchuan_qualified and final_score > 89:
            final_score = 89

        # 6. 生成状态描述
        if pillar_qualified_count == 4 and sanchuan_qualified:
            status = '满分：年月日时禄马贵人皆到山到向，三传禄马贵人俱全'
        elif pillar_qualified_count == 0 and sanchuan_luma_count == 0:
            status = '平课：禄马贵人不到山不到向，三传无禄马贵人'
        else:
            status = f'{pillar_qualified_count}柱合格，三传禄马贵人{sanchuan_luma_count}个'

        result = {
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
            'taisui_bonus': 0,
            'mijue_score_adj': 0,
            'mijue_details': {},
            # 三传间神贵人（传间见贵）
            'jianshen_guiren_count': jianshen_guiren_info.get('count', 0),
            'jianshen_guiren': jianshen_guiren_info.get('items', []),
        }

        # 7. 六壬断案秘诀规则调整
        # 【BUG-FIX 2026-08-18】原此段位于 `return {...}` 之后为死代码，永不执行；
        # 已移至 return 之前，使秘诀扣分/加分真正生效。
        try:
            from engine.mijue_engine import analyze_with_mijue, check_shas
            mijue = analyze_with_mijue(
                ri_gan=ri_gan, ri_zhi=ri_zhi, yue_zhi=yue_zhi,
                sanchuan=list(sanchuan.values()) if isinstance(sanchuan, dict) else (sanchuan if isinstance(sanchuan, list) else []),
                sike=[], tiandi_pan=tiandi_pan, tianjiang_map={},
                sanchuan_tj=None, gan_shang_shen=None
            )
            result['mijue_details'] = mijue
            result['mijue_score_adj'] = mijue.get('score_adjustment', 0)
            result['final_score'] = round(result['final_score'] + result['mijue_score_adj'], 1)
            result['final_score'] = max(20, min(100, result['final_score']))
        except ImportError:
            pass

        # 8. 太阳到山 / 太岁月建禄马贵人 吉格加分
        # 【2026-08-24 接入】原 check_taiyang_luma_guiren / check_taisui_luma_guiren 从未被调用，
        #    taiyang_bonus / taisui_bonus 恒为 0，太阳/太岁这两大顶级择日吉格形同虚设。现正式接入评分。
        taiyang_bonus = 0
        taisui_bonus = 0
        try:
            _yuelist = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
            if yue_zhi in _yuelist:
                _gm = (_yuelist.index(yue_zhi) + 2)  # 节气月 → 公历月近似（寅=2月...丑=1月）
                _gm = _gm if _gm <= 12 else _gm - 12
                _taiyang = self.check_taiyang_luma_guiren(
                    mountain, shan_jia, xiang_shou,
                    nian_zhi, yue_zhi, ri_zhi, shi_zhi, _gm
                )
                taiyang_bonus = _taiyang.get('bonus_score', 0)
                result['taiyang_label'] = _taiyang.get('descriptions', [])
            _taisui = self.check_taisui_luma_guiren(
                mountain, shan_jia, xiang_shou, nian_zhi, yue_zhi, ri_zhi
            )
            taisui_bonus = _taisui.get('bonus_score', 0)
            result['taisui_label'] = _taisui.get('descriptions', [])
        except Exception:
            taiyang_bonus, taisui_bonus = 0, 0

        result['taiyang_bonus'] = taiyang_bonus
        result['taisui_bonus'] = taisui_bonus
        # 【2026-09-05 太阳同源去重】旧口径"太阳到山"(check_taiyang_luma_guiren) 与新口径
        #   "太阳躔度·合方"(calc_sun_chanhe_bonus，更精确的天体躔合到山向) 同为"太阳到山/照向"加分，
        #   两者同时命中造成同一事实双计（实测 38% 课程重叠）。修复：合方法命中则合方法计分、
        #   旧口径仅作降级（无日期等合方法拿不到时兜底），不再叠加。
        result['final_score'] = round(result['final_score'] + taisui_bonus, 1)
        result['final_score'] = max(20, min(100, result['final_score']))

        # 太阳躔度·合方法 加分（切实到山向，比"太阳宫==山"更精确；日柱+10/他柱+3）
        # 【2026-09-05 接入】B 点：check_sun_chanhe_daoshan 已实现并集成 analyze_full；
        #   此处使单课评分链路（/api/zeri/analyze 等）同样纳入合方法加分。
        try:
            _sun_chanhe = self.calc_sun_chanhe_bonus(
                mountain, shichen, shan_jia, xiang_shou,
                nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi,
                shi_gan or '', shi_zhi or '', yuejiang=yuejiang)
            sun_chanhe_bonus = _sun_chanhe['bonus']
            result['sun_chanhe_bonus'] = sun_chanhe_bonus
            result['sun_chanhe_details'] = _sun_chanhe['details']
            result['sun_chanhe_hit_pillars'] = _sun_chanhe['hit_pillars']
            result['sun_chanhe_ri_qualified'] = _sun_chanhe['ri_qualified']
        except Exception:
            sun_chanhe_bonus = 0
        taiyang_effective = taiyang_bonus if sun_chanhe_bonus == 0 else 0
        result['taiyang_applied'] = taiyang_effective   # 实际计入额（合方法命中时旧口径让位）
        result['final_score'] = round(result['final_score'] + taiyang_effective + sun_chanhe_bonus, 1)
        result['final_score'] = max(20, min(100, result['final_score']))

        # 日月合塑/日月对望 加分（《要诀》吊天星第二课，"福力最巨大"；2026-09-05 步骤2）
        try:
            _riyue = self.calc_riyue_hesu_bonus(
                mountain, shichen, shan_jia, xiang_shou,
                year, month, day, yuejiang)
            riyue_bonus = _riyue['bonus']
            result['riyue_hesu_bonus'] = riyue_bonus
            result['riyue_hesu_type'] = _riyue['type']
            result['riyue_hesu_details'] = _riyue['details']
        except Exception:
            riyue_bonus = 0
        result['final_score'] = round(result['final_score'] + riyue_bonus, 1)
        result['final_score'] = max(20, min(100, result['final_score']))
        # 【2026-09-06 铁律硬闸·禄马贵人发三传（终闸）】所有秘诀/太阳/太岁/躔度/合塑加分
        #   结算完后仍守"未发三传不得上上吉"：六壬分封顶 89（防加分项顶回 100 虚满）
        if not sanchuan_qualified and result['final_score'] > 89:
            result['final_score'] = 89

        # 精细禄马贵人评分 + 课体修正（2026-08-25：与 analyze_full_with_sanchuan 同源，
        #   使生产批量接口 /api/zeri/batch 的 _ns.get('precision') 能取到 position_detail）
        _sc_res = {}
        try:
            if sanchuan:
                _sc_res = self.check_sanchuan_luma_guiren(
                    sanchuan, ri_gan, ri_zhi, nian_gan, nian_zhi,
                    yue_gan, yue_zhi, tiandi_pan, shichen
                )
        except Exception:
            _sc_res = {}
        result['precision'] = self.score_precision_luma_guiren(
            mountain, shichen,
            nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi,
            shi_gan, shi_zhi, ben_ming, ben_ming_gan,
            sanchuan, _sc_res
        )
        result['keti_adjust'] = _keti_adj   # 复用课体段计算结果（十三吉课±20 拍板口径，已计入 final_score）
        _kadj = result['keti_adjust']
        _prec = result['precision']
        _prec['keti'] = _kadj
        _prec['base_score'] = _prec.get('precision_score', 0)
        _prec['precision_score'] = round(max(0, min(100, _prec.get('precision_score', 0) + _kadj['ke_score'])), 2)
        _prec['keti_score'] = _kadj['ke_score']
        _prec['keti_note'] = _kadj['note']
        _prec['qualified'] = _prec['base_score'] >= 60

        return result
    
    def get_keti_deduction(self, ke_ti_name: str) -> Tuple[int, str, bool]:
        """
        根据课体名称获取扣分（基于64课经知识库）

        重要：九宗门（贼克、比用、涉害、遥克、昴星、别责、八专、伏吟、反吟）是起课方法，不是吉凶依据！
        吉凶应根据实际的课体课格名称（如龙德、富贵、官爵等）来判断

        返回: (扣分, 课体等级, 是否大凶课)
        """
        if not ke_ti_name or ke_ti_name == '待定':
            return 10, '平课', False

        # 如果有64课经知识库，优先使用
        if HAS_64KE_KNOWLEDGE and get_64ke_info:
            info = get_64ke_info(ke_ti_name)
            if info:
                level = info.get('吉凶', '平')
                # 【BUG-FIX 2026-08-18】补齐 64 课通解知识库实际值域：
                # 上吉/吉/凶（原缺这三键，命中'吉'/'凶'课会漏走 level_map）
                level_map = {
                    '上吉': (0, False),
                    '大吉': (0, False),
                    '吉': (0, False),
                    '中吉': (0, False),
                    '小吉': (5, False),
                    '平': (10, False),
                    '小凶': (20, False),
                    '凶': (25, False),
                    '中凶': (30, False),
                    '大凶': (40, True),
                }
                if level in level_map:
                    deduction, is_daxiong = level_map[level]
                    return deduction, info.get('名称', level), is_daxiong

        # 备用判断逻辑（基于关键字匹配）
        ke_ti_lower = ke_ti_name.lower()

        # 上上吉课（扣0分）
        # 上上吉课（扣0分）——【2026-08-18 清理】天福/天恩/天赦为吉神名非课体，删除
        shangshangji = ['三光', '三阳']
        for name in shangshangji:
            if name in ke_ti_name or name in ke_ti_lower:
                return 0, '上上吉课', False

        # 上吉课（扣0分）
        shangji = ['龙德', '官爵', '富贵', '喜庆', '玉堂', '金堂', '圣心', '益后', '续世', '三奇', '六仪', '时泰', '元首', '重审']
        for name in shangji:
            if name in ke_ti_name or name in ke_ti_lower:
                return 0, '上吉课', False

        # 中吉课（扣0分）
        # 【2026-08-18 清理】生气/解神/天医/福德/天喜/六合/太阴/青龙/明堂/金匮 为吉神/天将名非课体，删除
        zhongji = ['斫轮', '铸印', '轩盖', '登三天', '龙战', '引从', '亨通', '繁昌', '荣华', '德庆', '合欢']
        for name in zhongji:
            if name in ke_ti_name or name in ke_ti_lower:
                return 0, '中吉课', False

        # 小吉课（扣5分）
        # 【2026-08-18 清理】移除 6 个无效课体名（刑德/始破/平吉/小成/守成/安定）：
        #   引擎(64ke/sanchuan_kege)从不产出这些课体名，匹配永不命中；且 64 课经权威源未收录
        #   （平吉/小成/守成/安定为评级词、刑德为神煞概念、始破无考），保留会造成误导。
        xiaoji = ['进连茹', '退连茹', '间传课', '交车课']
        for name in xiaoji:
            if name in ke_ti_name or name in ke_ti_lower:
                return 5, '小吉课', False

        # 平课（扣10分）- 已知一、昴星等起课法为主的课
        pingke = ['知一', '昴星', '返吟', '伏吟', '普通', '无特殊课体', '连珠']
        for name in pingke:
            if name in ke_ti_name or name in ke_ti_lower:
                return 10, '平课', False

        # 小凶课（扣20分）- 基于课格名
        # 【2026-08-18 清理】小耗/败亡/破败/失脱为凶煞名非课体；比用为V1课体(V2已并入涉害流程)，均删除
        xiaoxiong = ['涉害', '遥克', '别责', '八专', '芜淫', '解离', '度厄', '无禄', '绝嗣']
        for name in xiaoxiong:
            if name in ke_ti_name or name in ke_ti_lower:
                return 20, '小凶课', False

        # 中凶课（扣30分）
        # 【2026-08-18 清理】孤辰/寡宿/天寇/死气/病符/官符为神煞名或引擎不产，删除
        zhongxiong = ['刑伤', '二烦', '三烦', '九丑', '天祸', '丧吊']
        for name in zhongxiong:
            if name in ke_ti_name or name in ke_ti_lower:
                return 30, '中凶课', False

        # 大凶课（扣40分）
        # 【2026-08-18 清理】丧门/白虎/岁破/大耗/绝灭为神煞/天将名非课体，删除
        daxiong = ['天罗地网', '死奇', '魄化', '飞魂', '灭门']
        for name in daxiong:
            if name in ke_ti_name or name in ke_ti_lower:
                return 40, '大凶课', True

        # 未匹配的课体默认为平课
        return 10, '普通课', False

    def apply_keti_adjustment(self, ke_ti_name: str, jike_ctx: Dict = None) -> Dict:
        """
        课体修正（2026-08-24 接入，用户口径拍板）
        【规则】
          以禄马贵人到山到向分（precision_score）为唯一合格依据。
          课体只作 ± 修正，不改变合格判定：
            · 十三吉课加分 → 按命中个数分档：1-2 个 +10，≥3 个 +20（封顶+20）
            · 非十三吉课命中凶格 → 复用 get_keti_deduction，扣分封顶 -20
              （上限只扣 20 分——世上没有全吉之事，不搞一票否决）
            · 其余（吉课非十三 / 平 / 小吉）→ 0，不加不减
          加分与减分互斥：命中十三吉课则只加分，不再判凶减分。
        【2026-09-05 精细判据】十三吉课优先用 jike_13.check_jike_13 逐课按 64 课经 definition 落码
          （sike 干上/支上 + 三传 + 天将 + 禄马贵 + 旬德等），jike_ctx 提供这些上下文；
          精细参数缺失或未命中时退回课体名子串匹配兜底（防漏判）。
        返回 {jike_hits, keti_level, add, deduct, ke_score, note, jike_details}。
        注：ke_score 为 ± 修正净额，需加到 base 分上，最终 clamp 到 [0,100]。
        """
        ke_ti_name = (ke_ti_name or '').strip()
        if not ke_ti_name or ke_ti_name == '待定':
            return {'jike_hits': 0, 'keti_level': '平课', 'add': 0,
                    'deduct': 0, 'ke_score': 0, 'note': '无课体信息，课体不加不减',
                    'jike_details': []}

        # 十三吉课加分（精细判据优先，逐课按64课经落码）
        jike_hits = 0
        jike_details = []
        jike_src = '课体名'
        if isinstance(jike_ctx, dict) and jike_ctx.get('sanchuan_dizhi'):
            try:
                from engine.jike_13 import check_jike_13 as _cj13
                _jc = _cj13(
                    keti=ke_ti_name,
                    sike=jike_ctx.get('sike'),
                    sanchuan_dizhi=jike_ctx.get('sanchuan_dizhi'),
                    tianjiang_list=jike_ctx.get('tianjiang_list'),
                    ri_gan=jike_ctx.get('ri_gan', '') or '',
                    ri_zhi=jike_ctx.get('ri_zhi', '') or '',
                    nian_zhi=jike_ctx.get('nian_zhi', '') or '',
                    yue_zhi=jike_ctx.get('yue_zhi', '') or '',
                    lu_zhi=jike_ctx.get('lu_zhi', '') or '',
                    ma_zhi=jike_ctx.get('ma_zhi', '') or '',
                    longde_matched=bool(jike_ctx.get('longde_matched')),
                    ben_ming_zhi=jike_ctx.get('ben_ming_zhi', '') or '',
                    lmg_dsdx=jike_ctx.get('lmg_dsdx'),
                    shan_lmg=jike_ctx.get('shan_lmg'),
                )
                if _jc.get('hits'):
                    jike_hits = len(_jc['hits'])
                    jike_details = _jc.get('details', [])
                    jike_src = '精细判据'
            except Exception:
                jike_hits = 0
        if not jike_hits:
            jike_hits = sum(1 for n in _JIKE_13 if n in ke_ti_name)
            if jike_hits:
                jike_src = '课体名'
        if jike_hits:
            add = 10 if jike_hits <= 2 else 20
            return {'jike_hits': jike_hits, 'keti_level': '十三吉课',
                    'add': add, 'deduct': 0, 'ke_score': add,
                    'note': f'命中十三吉课 {jike_hits} 个({jike_src}解析)，加分 +{add}',
                    'jike_details': jike_details}

        # 非十三吉课：凶课减分（复用 get_keti_deduction，封顶 -20）
        ded, level, is_daxiong = self.get_keti_deduction(ke_ti_name)
        if ded >= 20:            # 小凶20/中凶30/大凶40 → 一律封顶扣 20
            deduct = min(ded, 20)
            return {'jike_hits': 0, 'keti_level': level, 'add': 0,
                    'deduct': deduct, 'ke_score': -deduct,
                    'note': f'{level}：课体凶，扣分 -{deduct}',
                    'jike_details': []}

        # 其余（吉课非十三 / 平 / 小吉）不加不减
        return {'jike_hits': 0, 'keti_level': level, 'add': 0,
                'deduct': 0, 'ke_score': 0, 'note': f'{level}：课体不加不减',
                'jike_details': []}

    def _build_jike_ctx(self, ri_gan: str, ri_zhi: str, nian_zhi: str, yue_zhi: str,
                        sanchuan: Dict, tiandi_pan: Dict, shichen: str,
                        ben_ming: str = '', shan_jia: str = '', xiang_shou: str = '',
                        mountain: str = '', nian_gan: str = '', yue_gan: str = '',
                        yuejiang: str = '') -> Dict:
        """构造十三吉课精细判据上下文（jike_13.check_jike_13 需要）。
        - sike：四课 [(课名,上神,下神,天将)] 内部重排（与生产起课同源 SiKeSanChuanCalculator2）
        - sanchuan_dizhi / tianjiang_list：三传地支与天将
        - lmg_dsdx：禄马贵人到山到向的支集合（《要诀》亨通/和美课"禄马贵人到山到向"；
          check_single_pillar 日柱天盘加临到山/向判定——防与拱格"三传在传"同源重复计分）
        - shan_lmg：山向禄马贵人支集合（《要诀》时太课"山向禄马贵人"；山禄+山贵人）
        - lu_zhi / ma_zhi / longde_matched / ben_ming_zhi 等判据要素
        """
        ctx = {
            'sike': None, 'sanchuan_dizhi': [], 'tianjiang_list': [], 'lmg_dsdx': None,
            'shan_lmg': None,
            'ri_gan': ri_gan or '', 'ri_zhi': ri_zhi or '',
            'nian_zhi': nian_zhi or '', 'yue_zhi': yue_zhi or '',
            'lu_zhi': self.get_lu_zhi(ri_gan) if ri_gan else '',
            'ma_zhi': self.get_ma_zhi(ri_zhi) if ri_zhi else '',
            'longde_matched': False, 'ben_ming_zhi': '',
        }
        if ben_ming:
            ctx['ben_ming_zhi'] = ben_ming[-1] if len(ben_ming) >= 2 else ben_ming
        if isinstance(sanchuan, dict):
            ctx['sanchuan_dizhi'] = [sanchuan.get('初传', '') or '', sanchuan.get('中传', '') or '',
                                     sanchuan.get('末传', '') or '']
        elif sanchuan:
            ctx['sanchuan_dizhi'] = [str(x) for x in sanchuan][:3]
        # 【2026-09-06 龙德课真判定】月将推导：显式 yuejiang > 天地盘反推（天盘子位加临=月将）> 月支映射；
        #   龙德判定本身在天将列表就绪后执行（见下方）。
        if not yuejiang and (isinstance(tiandi_pan, dict) and (tiandi_pan.get('子') or '')):
            yuejiang = str(tiandi_pan.get('子'))
        if not yuejiang and yue_zhi:
            try:
                yuejiang = self.get_yuejiang(yue_zhi) or ''
            except Exception:
                yuejiang = ''
        if ri_gan and ri_zhi:
            try:
                from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2 as _S2
                _tdp = tiandi_pan or arrange_tiandi_pan('亥', '子')
                ctx['sike'] = _S2().qi_sike(ri_gan, ri_zhi, _tdp) or None
            except Exception:
                ctx['sike'] = None
        if ri_gan and shichen and ctx['sanchuan_dizhi']:
            try:
                from engine.gui_ren_engine import GuiRenCalculator
                _tjm = GuiRenCalculator().arrange_gui_ren_pan(
                    ri_gan, {'天地对应': tiandi_pan or {}}, shichen).get('天将映射', {})
                ctx['tianjiang_list'] = [_tjm.get(z, '') for z in ctx['sanchuan_dizhi']]
            except Exception:
                pass
        # 【2026-09-06 龙德课真判定】判据：《要诀》= 太岁（年支）与月将相符，且贵人乘发用（初传天将=贵人）。
        #   旧逻辑 `'龙德' in 课体名` 恒 False（正常课体名如"重审课"不含"龙德"）。
        _chu_tj = ctx['tianjiang_list'][0] if ctx.get('tianjiang_list') else ''
        ctx['longde_matched'] = bool(nian_zhi and yuejiang and nian_zhi == yuejiang and _chu_tj == '贵人')
        # 禄马贵人到山到向支集合（【2026-09-06 用户口径修复】年月日三柱合集，原仅日柱——
        #   富贵/和美/亨通课"禄马贵人到山到向"判据被单柱口径系统性压低，30年0顶格主因之一）
        #   能算（有 shan_jia/xiang_shou）则给严格集合（可为空=未到山向→不命中）；
        #   无能力则保持 None（调用方退回"在传"近似）
        if ri_gan and ri_zhi and shan_jia and xiang_shou:
            try:
                _dsdx = []
                for _g, _z in ((nian_gan or ri_gan, nian_zhi or ri_zhi),
                               (yue_gan or ri_gan, yue_zhi or ri_zhi),
                               (ri_gan, ri_zhi)):
                    _sp = self.check_single_pillar(_g, _z,
                                                   tiandi_pan or arrange_tiandi_pan('亥', '子'),
                                                   shichen or '子', shan_jia, xiang_shou, '')
                    for _zv, _ts, _tx in ((_sp.get('lu_zhi'), _sp.get('lu_to_shan'), _sp.get('lu_to_xiang')),
                                          (_sp.get('ma_zhi'), _sp.get('ma_to_shan'), _sp.get('ma_to_xiang')),
                                          (_sp.get('guiren_zhi'), _sp.get('guiren_to_shan'), _sp.get('guiren_to_xiang'))):
                        if _zv and (_ts or _tx):
                            _dsdx.append(_zv)
                ctx['lmg_dsdx'] = list(dict.fromkeys(_dsdx))  # 去重保序
            except Exception:
                ctx['lmg_dsdx'] = None
        # 山向禄马贵人集合（《要诀》时太课"取年支月支发传即为山向禄马贵人"：山禄+山贵人；
        #   2026-09-05 原文核对改判据新增）
        if mountain:
            try:
                _sl = set()
                _mlu = self.LU.get(mountain, '')
                if _mlu:
                    _sl.add(_mlu)
                for _g in (self.BEN_SHAN_GUIREN.get(mountain) or []):
                    if _g:
                        _sl.add(_g)
                ctx['shan_lmg'] = sorted(_sl)
            except Exception:
                ctx['shan_lmg'] = None
        return ctx

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
        guiren_zhi = self.get_guiren_zhi(tian_gan, tiandi_pan, shichen)  # 贵人为天盘加临后地盘位

        # 【A·口径统一 2026-09-05】禄/马亦须"天盘加临到地盘"再对山/向（原静态比对与
        #   check_pillar_all_qualified 不一致，导致批量(analyze_full)与单课(calculate_new_score)
        #   评分口径分叉）。原文"禄马贵人指的是天盘的地支，不是地盘的地支"（癸禄在天盘子→
        #   天盘子转动后对应地盘申）。lu_zhi/ma_zhi 保留静态位（展示用），判定改用 tianpan_*。
        tianpan_lu_zhi = self._get_tiandi_position(lu_zhi, tiandi_pan) if lu_zhi else None
        tianpan_ma_zhi = self._get_tiandi_position(ma_zhi, tiandi_pan) if ma_zhi else None

        lu_to_shan = (tianpan_lu_zhi == shan_jia)
        lu_to_xiang = (tianpan_lu_zhi == xiang_shou)
        ma_to_shan = (tianpan_ma_zhi == shan_jia)
        ma_to_xiang = (tianpan_ma_zhi == xiang_shou)
        guiren_to_shan = (guiren_zhi == shan_jia)
        guiren_to_xiang = (guiren_zhi == xiang_shou)

        # 三合次吉（与 check_pillar_all_qualified 对齐）：禄/马/贵加临位的三合伙伴临山或向
        lu_sanhe = (tianpan_lu_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                    tianpan_lu_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if tianpan_lu_zhi else False
        ma_sanhe = (tianpan_ma_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                    tianpan_ma_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if tianpan_ma_zhi else False
        guiren_sanhe = (guiren_zhi in self.SAN_HE_PARTNERS.get(shan_jia, set()) or
                        guiren_zhi in self.SAN_HE_PARTNERS.get(xiang_shou, set())) if guiren_zhi else False

        shan_count = sum([lu_to_shan, ma_to_shan, guiren_to_shan])
        xiang_count = sum([lu_to_xiang, ma_to_xiang, guiren_to_xiang])
        sanhe_count = sum([lu_sanhe, ma_sanhe, guiren_sanhe])

        pillar_qualified = (shan_count >= 1 or xiang_count >= 1 or sanhe_count >= 1)

        result = {
            'pillar': pillar_name,
            'tian_gan': tian_gan,
            'di_zhi': di_zhi,
            'lu_zhi': lu_zhi,
            'ma_zhi': ma_zhi,
            'guiren_zhi': guiren_zhi or '无',
            'tianpan_lu_zhi': tianpan_lu_zhi or '',
            'tianpan_ma_zhi': tianpan_ma_zhi or '',
            'lu_to_shan': lu_to_shan,
            'lu_to_xiang': lu_to_xiang,
            'ma_to_shan': ma_to_shan,
            'ma_to_xiang': ma_to_xiang,
            'guiren_to_shan': guiren_to_shan,
            'guiren_to_xiang': guiren_to_xiang,
            'lu_sanhe': lu_sanhe,
            'ma_sanhe': ma_sanhe,
            'guiren_sanhe': guiren_sanhe,
            'shan_count': shan_count,
            'xiang_count': xiang_count,
            'sanhe_count': sanhe_count,
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
        
        # 检查本山禄神（双山纳甲取法；支持四正位双组多支）
        # 【2026-08-24 接入】原用单一旧表 BEN_SHAN_LU(双山一级地支配对)，现切换为
        #   BEN_SHAN_LU_DSM(双山纳甲：十二双山取干+卦纳甲+四正位双组禄)，循环逐支判定到山到向。
        for ben_shan_lu in self.BEN_SHAN_LU_DSM.get(mountain, []):
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
    
    def check_ben_ming_guiren(self, ben_ming: str,
                              nian_gan: str, yue_gan: str,
                              ri_gan: str, shi_gan: str) -> Dict:
        """
        本命贵人判定（2026-08-24 新增，口径按憨爷确认）
        【规则】命主本命支若落在某柱天干之天乙贵人地支集合(GAN_GUIREN_ZHIS)内，
        则该柱即为该命主之"本命贵人"到位（发贵应于此命主）。
        例：子命者，柱干乙/己之贵人支含"子"=本命 → 乙己年月日时即子命之贵人。

        参数: ben_ming: 命主本命地支(如'子')
              nian_gan/yue_gan/ri_gan/shi_gan: 年/月/日/时四柱天干
        返回: 各柱本命贵人命中情况
        """
        pillars = [
            ('年', nian_gan), ('月', yue_gan),
            ('日', ri_gan), ('时', shi_gan)
        ]
        hits = []
        for name, gan in pillars:
            if gan and ben_ming in self.GAN_GUIREN_ZHIS.get(gan, []):
                hits.append({'pillar': name, 'gan': gan})
        return {
            'ben_ming': ben_ming,
            'hits': hits,
            'count': len(hits),
            'has_ben_ming_guiren': len(hits) > 0
        }
    
    def check_ben_ming_ma_lu(self, ben_ming: str,
                             ben_ming_gan: str = None,
                             nian_zhi: str = None, yue_zhi: str = None,
                             ri_zhi: str = None, shi_zhi: str = None) -> Dict:
        """
        本命作马、作禄判定（2026-08-24 新增，原著口径 L1455-1467）
        【规则·原著】由本命干支推导命主之禄支/马支，再看四柱地支是否"坐"于此支，
        即该柱即为本命作禄/作马到位（发财物应于此命主）。
          · 命马支 = 本命地支之三合驿马 YIMA[命支]（如 丑命→亥，子命→寅）
          · 命禄支 = 本命天干之干禄 LU[命干]（如 癸命→子，壬命→亥）
        例(原著宗癸丑命)：子为癸命禄、亥为丑命马 —— 若某柱支为子即命禄到位，为亥即命马到位。

        参数: ben_ming: 命主本命地支(如'丑')
              ben_ming_gan: 命主本命天干(如'癸')；缺省则不做本命作禄判定
              年/月/日/时四柱地支
        返回: 各柱本命作禄/作马命中情况
        """
        ma_zhi = self.YIMA.get(ben_ming, '')
        lu_zhi = self.LU.get(ben_ming_gan, '') if ben_ming_gan else ''
        pillars = [
            ('年', nian_zhi), ('月', yue_zhi),
            ('日', ri_zhi), ('时', shi_zhi)
        ]
        lu_hits, ma_hits = [], []
        for name, zhi in pillars:
            if not zhi:
                continue
            if lu_zhi and zhi == lu_zhi:
                lu_hits.append({'pillar': name, 'zhi': zhi, 'lu': lu_zhi})
            if ma_zhi and zhi == ma_zhi:
                ma_hits.append({'pillar': name, 'zhi': zhi, 'ma': ma_zhi})
        return {
            'ben_ming': ben_ming,
            'lu_gan': ben_ming_gan or '',
            'lu_zhi': lu_zhi,
            'ma_zhi': ma_zhi,
            'lu_hits': lu_hits,
            'ma_hits': ma_hits,
            'lu_count': len(lu_hits),
            'ma_count': len(ma_hits),
            'has_ben_ming_lu': len(lu_hits) > 0,
            'has_ben_ming_ma': len(ma_hits) > 0
        }

    def check_gong_pillars(self, nian_gan: str, nian_zhi: str,
                           yue_gan: str, yue_zhi: str,
                           ri_gan: str, ri_zhi: str,
                           shi_gan: str = None, shi_zhi: str = None,
                           ben_ming: str = None, mountain: str = None) -> Dict:
        """
        四柱夹拱判定：拱贵 / 拱禄 / 拱马（2026-08-24 新增）
        【原理·原著】经云"拱贵建贵出英豪"。
          建贵 = 贵人支直接当值出现在日课四柱；
          拱贵 = 贵人支本身不出现，但其三合局两翼(如卯贵三合亥卯未，只见亥、未)
                  把中间的贵人支夹拱出来 → "拱卯贵"(癸未癸亥拱卯贵, L1963)。
          拱禄/拱马同理(禄神/驿马作为被拱中神)。
          例：甲日禄在寅，甲午月甲午日甲戌时 → 午戌拱寅禄(L735)。
        【口径】四柱地支集中出现某目标的两个三合伙伴(缺中神)，即该目标被"拱"出。
          目标来源：拱贵=各柱干之天乙贵人(GAN_GUIREN_ZHIS)；拱禄=各柱干之禄(LU)；
                    拱马=日支与本命支之驿马(YIMA)。
        【收紧口径·2026-08-24】
          ① L3141 干一致：被拱之贵/禄对应的干须在四柱出现≥2次(两干同，如两癸/两乙)；
          ② 到山到向：被拱出的贵/禄/马支须等于山家或向首才计分(拱须拱到本山/本向，
             合原著"双贵三合拱子山向""夹寅贵于巽山")。
        """
        pillars = [('年', nian_gan, nian_zhi), ('月', yue_gan, yue_zhi), ('日', ri_gan, ri_zhi)]
        if shi_gan and shi_zhi:
            pillars.append(('时', shi_gan, shi_zhi))
        zhi_set = {p[2] for p in pillars if p[2]}
        # 收紧①：干一致(L3141)——被拱贵/禄对应的干须出现≥2次
        gan_counter = {}
        for _, gan, _ in pillars:
            if gan:
                gan_counter[gan] = gan_counter.get(gan, 0) + 1
        # 收紧②：到山到向——被拱支须等于山家或向首
        shan_jia = self.get_shan_jia(mountain) if mountain else None
        xiang_shou = self.get_xiang_shou(mountain) if mountain else None

        def _daoshan(target_zhi: str) -> bool:
            return shan_jia is not None and target_zhi in (shan_jia, xiang_shou)

        def _is_gong(target_zhi: str) -> bool:
            """目标支未现，但其两个三合伙伴都在四柱 → 被拱出"""
            if target_zhi in zhi_set:
                return False  # 已建当值，不算拱
            part = self.SAN_HE_PARTNERS.get(target_zhi, set())
            return len(part) == 2 and part <= zhi_set

        results = []
        hit_types = set()  # ('贵'|'禄'|'马', 地支) 去重，同类同支只记一次

        # 拱贵（贵=各柱干之天乙贵人）
        for name, gan, _ in pillars:
            if not gan:
                continue
            for g in self.GAN_GUIREN_ZHIS.get(gan, []):
                key = ('拱贵', g)
                if key in hit_types:
                    continue
                if gan_counter.get(gan, 0) < 2 or not _daoshan(g):
                    continue
                if _is_gong(g):
                    hit_types.add(key)
                    results.append({
                        'type': '拱贵', 'zhi': g, 'gan': gan, 'pillar': name,
                        'desc': f'{name}干{gan}之贵人{g}未现，三合两翼拱至%s'
                                % ('山' if g == shan_jia else '向')
                    })

        # 拱禄（禄=各柱干之禄，甲寅乙卯丙巳丁午…）
        for name, gan, _ in pillars:
            if not gan:
                continue
            lu = self.LU.get(gan)
            key = ('拱禄', lu)
            if not lu or key in hit_types:
                continue
            if gan_counter.get(gan, 0) < 2 or not _daoshan(lu):
                continue
            if _is_gong(lu):
                hit_types.add(key)
                results.append({
                    'type': '拱禄', 'zhi': lu, 'gan': gan, 'pillar': name,
                    'desc': f'{name}干{gan}之禄神{lu}未现，三合两翼拱至%s'
                            % ('山' if lu == shan_jia else '向')
                })

        # 拱马（马=日支之驿马 + 本命支之驿马；无干故不做干一致，仍须到山到向）
        ma_targets = []
        if ri_zhi:
            ma_targets.append(('日支', ri_zhi, self.YIMA.get(ri_zhi)))
        if ben_ming:
            ma_targets.append(('本命', ben_ming, self.YIMA.get(ben_ming)))
        for src, src_zhi, maz in ma_targets:
            key = ('拱马', maz)
            if not maz or key in hit_types:
                continue
            if not _daoshan(maz):
                continue
            if _is_gong(maz):
                hit_types.add(key)
                results.append({
                    'type': '拱马', 'zhi': maz, 'src': src, 'src_zhi': src_zhi,
                    'pillar': src, 'desc': f'{src}支{src_zhi}之驿马{maz}未现，三合两翼拱至%s'
                            % ('山' if maz == shan_jia else '向')
                })

        gong_bonus = min(30, 10 * len(hit_types))  # 每类拱格 +10，最多 +30
        return {
            'results': results,
            'count': len(hit_types),
            'has_gong': len(results) > 0,
            'gong_bonus': gong_bonus,
            'zhi_set': sorted(zhi_set),
        }

    def score_precision_luma_guiren(self, mountain: str, shichen: str,
                                    nian_gan: str, nian_zhi: str,
                                    yue_gan: str, yue_zhi: str,
                                    ri_gan: str, ri_zhi: str,
                                    shi_gan: str = None, shi_zhi: str = None,
                                    ben_ming: str = None, ben_ming_gan: str = None,
                                    sanchuan: Dict = None, sanchuan_result: Dict = None) -> Dict:
        """
        精细禄马贵人评分（2026-08-24 新增）
        【口径·用户确认】
          六位置权值（缺扣=分值，求和100）：时8 日13 月15 年17 坐山23 本命24。
          类别权重（缺马最小→缺贵人最大）：禄35% 马25% 贵人40%。
          到山到向三级：双到×1.0 > 仅到向×0.7 > 仅到山×0.5。
          发传系数（该禄/马/贵支在三传则发传）：
            · 到位+发传 ×1.3 > 到位未发传 ×1.0 > 发传未到位 ×0.15 > 未到位未发传 ×0。
          及格线：总分≥60 为合格，<60 为平课。
        每类得分 = 位置权值 × 类别占比 × 到山到向系数 × 发传系数，累加即总分。
        六位置各自的目标支：
          年末/月/日/时 = 该柱干之禄、支之马、干之贵人；
          坐山 = 本山禄(BEN_SHAN_LU_DSM)、本山马(YIMA[山家])、本山贵人(BEN_SHAN_GUIREN)；
          本命 = 命禄(LU[命干])、命马(YIMA[命支])、本命贵人=命支。
        """
        # ── 权值表（用户拍板）──
        POS_W = {'时': 8, '日': 13, '月': 15, '年': 17, '坐山': 23, '本命': 24}
        CAT_W = {'贵': 0.40, '禄': 0.35, '马': 0.25}   # 贵人最贵，马最可舍
        SHAN_JIA = self.get_shan_jia(mountain)
        XIANG = self.get_xiang_shou(mountain)
        yuejiang = self.get_yuejiang(yue_zhi) if yue_zhi else '亥'
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)

        # 三传中出现的目标支集合（发传判定）
        all_lu = (sanchuan_result or {}).get('all_lu', [])
        all_ma = (sanchuan_result or {}).get('all_ma', [])
        all_guiren = (sanchuan_result or {}).get('all_guiren', [])

        def _dmult(zhi: str):
            """到山到向三级系数"""
            to_shan = (zhi == SHAN_JIA)
            to_xiang = (zhi == XIANG)
            if to_shan and to_xiang:
                return 1.0, '双到'
            if to_xiang:
                return 0.7, '到向'
            if to_shan:
                return 0.5, '到山'
            return 0.0, '未到'

        def _fmult(dmult: float, in_chuan: bool) -> float:
            """发传组合系数（到位+发传×1.3 > 到位×1.0 > 发传未到位×0.15）"""
            if dmult > 0 and in_chuan:
                return dmult * 1.3
            if dmult > 0:
                return dmult
            if in_chuan:
                return 0.15
            return 0.0

        # 构造 六位置 × {类: [候选支]}
        pillars = [('年', nian_gan, nian_zhi), ('月', yue_gan, yue_zhi),
                   ('日', ri_gan, ri_zhi), ('时', shi_gan, shi_zhi)]
        pos_targets = {}
        for name, gan, zhi in pillars:
            p = self.check_single_pillar(gan, zhi, tiandi_pan, shichen, SHAN_JIA, XIANG, name) if zhi else {}
            pos_targets[name] = {
                '贵': [p.get('guiren_zhi')] if p.get('guiren_zhi') and p.get('guiren_zhi') != '无' else [],
                '禄': [p.get('lu_zhi')] if p.get('lu_zhi') else [],
                '马': [p.get('ma_zhi')] if p.get('ma_zhi') else [],
            }
        # 坐山：本山禄/本山贵人(多支取最佳)、本山马=山家之驿马
        pos_targets['坐山'] = {
            '禄': list(self.BEN_SHAN_LU_DSM.get(mountain, [])),
            '马': [self.YIMA.get(SHAN_JIA, '')] if SHAN_JIA else [],
            '贵': list(self.BEN_SHAN_GUIREN.get(mountain, [])),
        }
        # 本命：命禄、命马、命贵(命支)
        pos_targets['本命'] = {
            '禄': [self.LU.get(ben_ming_gan, '')] if ben_ming_gan else [],
            '马': [self.YIMA.get(ben_ming, '')] if ben_ming else [],
            '贵': [ben_ming] if ben_ming else [],
        }

        # 评分
        pos_scores, pos_complete = {}, 0
        pos_detail = []
        for name, w in POS_W.items():
            cls_total, cls_detail = 0.0, []
            complete = True
            for cat, pct in CAT_W.items():
                cands = pos_targets[name].get(cat, [])
                best = 0.0
                best_state = '未到'
                used_zhi = ''
                for zhi in cands:
                    dmult, state = _dmult(zhi)
                    if dmult > best:
                        best, best_state, used_zhi = dmult, state, zhi
                # 发传判定（坐山/本命支若恰在三传亦计；否则不发）
                in_chuan = False
                if used_zhi and used_zhi != '':
                    if cat == '禄':
                        in_chuan = used_zhi in all_lu
                    elif cat == '马':
                        in_chuan = used_zhi in all_ma
                    else:
                        in_chuan = used_zhi in all_guiren
                mult = _fmult(best, in_chuan)
                s = w * pct * mult
                cls_total += s
                if best <= 0:
                    complete = False
                cls_detail.append({
                    'type': cat, 'zhi': used_zhi or '无', 'daoshan': best_state,
                    'mult': round(mult, 3), 'score': round(s, 2), 'in_chuan': in_chuan,
                })
            pos_scores[name] = round(cls_total, 2)
            if complete:
                pos_complete += 1
            pos_detail.append({
                'position': name,
                'weight': w, 'score': pos_scores[name],
                'classes': cls_detail,
            })

        total = round(sum(pos_scores.values()), 2)
        qualified = total >= 60
        grade = '合格' if qualified else '平课'
        # 档位：6位置禄马贵人齐备数为n → 第(7-n)档（6全齐一档，5二档…0七档）
        level = f'第{7 - pos_complete}档'
        return {
            'precision_score': total,
            'qualified': qualified,
            'grade': grade,
            'complete_positions': pos_complete,
            'level': level,
            'position_detail': pos_detail,
            'params': {'pos_weights': POS_W, 'cat_weights': CAT_W,
                       'pass_line': 60, 'shan_jia': SHAN_JIA, 'xiang_shou': XIANG},
        }

    def analyze_full(self, mountain: str, shichen: str,
                    nian_gan: str, nian_zhi: str,
                    yue_gan: str, yue_zhi: str,
                    ri_gan: str, ri_zhi: str,
                    shi_gan: str = None, shi_zhi: str = None,
                    ben_ming: str = None, ben_ming_gan: str = None,
                    year: int = None, month: int = None, day: int = None,
                    yuejiang: str = None) -> Dict:
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
            year/month/day: 公历日期（可选）——有则太阳（月将）按节气精确过宫
                            get_yuejiang_by_date；否则退回月支映射 get_yuejiang。
            yuejiang: 月将（可选，显式传入优先，覆盖日期/月支推算）

        返回:
            完整分析结果
        """
        shan_jia = self.get_shan_jia(mountain)
        xiang_shou = self.get_xiang_shou(mountain)
        # 【2026-09-05 修复】太阳（月将）定位优先级：显式 yuejiang > 日期节气过宫 > 月支映射。
        #   原仅 get_yuejiang(yue_zhi)（月支映射），与节气精确过宫可能不一致（如午月→未将，
        #   而立夏前后太阳实际在酉），导致太阳躔度合方法（依赖太阳位置）定位偏差。
        if yuejiang is None:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = self.get_yuejiang(yue_zhi) if yue_zhi else '亥'
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
        
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
        # 时柱（可选）：时贵计分——时贵也是禄马贵之一，有其他柱没有则仍算合格
        shi_result = None
        if shi_gan and shi_zhi:
            shi_result = self.check_single_pillar(
                shi_gan, shi_zhi, tiandi_pan, shichen,
                shan_jia, xiang_shou, '时'
            )
        
        # 太阳躔度·合方之法（B：以太阳加时排天地盘，定禄马贵天体加临到山/向）
        sun_chanhe = {}
        for pname, pg, pz in [('年', nian_gan, nian_zhi), ('月', yue_gan, yue_zhi),
                              ('日', ri_gan, ri_zhi), ('时', shi_gan or '', shi_zhi or '')]:
            if pg and pz:
                sun_chanhe[pname] = self.check_sun_chanhe_daoshan(
                    mountain, shichen, pg, pz, shan_jia, xiang_shou, yuejiang=yuejiang)
        sun_hit_pillars = [p for p, r in sun_chanhe.items() if r['qualified']]
        # 加分：日柱真到 +10，年月时柱各 +3（切实到山向，接入评分）
        sun_bonus = sum((10 if p == '日' else 3) for p in sun_hit_pillars)

        # 日月合塑/日月对望（吊天星第二课；《要诀》"福力最巨大"，2026-09-05 步骤2）
        #   需公历日期（月亮躔度由 sxtwl 反解农历）；无日期则安全跳过（加分0）
        riyue_hesu = {'type': '无', 'bonus': 0}
        if year and month and day:
            try:
                _rh = self.calc_riyue_hesu_bonus(
                    mountain, shichen, shan_jia, xiang_shou,
                    year, month, day, yuejiang)
                riyue_hesu = {'type': _rh['type'], 'bonus': _rh['bonus'], 'details': _rh['details']}
            except Exception:
                riyue_hesu = {'type': '无', 'bonus': 0}
        
        # 检查本山本向
        ben_shan_result = self.check_ben_shan_ben_xiang(
            mountain, shan_jia, xiang_shou, tiandi_pan, shichen,
            nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi
        )
        
        # 本命贵人（可选）：命主本命支命中各柱干之天乙贵人
        ben_ming_result = None
        if ben_ming:
            ben_ming_result = self.check_ben_ming_guiren(
                ben_ming, nian_gan, yue_gan, ri_gan, shi_gan or ''
            )
            # 本命作禄/作马（可选，2026-08-24 新增，原著口径：命干→命禄支、命支→命马支）
            ben_ming_result['ma_lu'] = self.check_ben_ming_ma_lu(
                ben_ming, ben_ming_gan,
                nian_zhi, yue_zhi, ri_zhi, shi_zhi
            )
        
        # 统计
        qualified_count = sum([
            nian_result['pillar_qualified'],
            yue_result['pillar_qualified'],
            ri_result['pillar_qualified'],
            shi_result['pillar_qualified'] if shi_result else False
        ])
        
        # 评分（口径统一 2026-08-24：与SKILL文档一致 50/60/80/100）
        if not ri_result['pillar_qualified']:
            base_score = 50
            status = '平课（日柱禄马贵人未到山到向）'
        elif qualified_count == 1:
            base_score = 60
            status = '吉课（仅日柱禄马贵人到山到向）'
        elif qualified_count == 2:
            base_score = 80
            status = '中吉课（两柱禄马贵人到山到向）'
        else:
            base_score = 100
            status = '上吉课（年月日禄马贵人皆到山到向）'
        
        # 本山本向吉课加分
        if ben_shan_result['has_ben_shan_ji']:
            base_score = min(100, base_score + 10)
        
        # 拱格加分（拱贵/拱禄/拱马，2026-08-24 新增；旧口径 = base_score，新口径 = score）
        gong_result = self.check_gong_pillars(
            nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi,
            shi_gan, shi_zhi, ben_ming, mountain
        )
        gong_bonus = gong_result['gong_bonus']
        score = min(100, base_score + gong_bonus + sun_bonus + riyue_hesu['bonus'])
        if gong_bonus > 0:
            status += f'；拱{gong_result["count"]}格(+{gong_bonus})'
        if sun_bonus > 0:
            status += f'；太阳躔度合方({"、".join(sun_hit_pillars)}柱)(+{sun_bonus})'
        if riyue_hesu['bonus'] > 0:
            status += f'；日月{riyue_hesu["type"]}(+{riyue_hesu["bonus"]})'

        return {
            'mountain': mountain,
            'shan_jia': shan_jia,
            'xiang_shou': xiang_shou,
            'shichen': shichen,
            'nian_result': nian_result,
            'yue_result': yue_result,
            'ri_result': ri_result,
            'shi_result': shi_result,
            'ben_ming_result': ben_ming_result,
            'ben_shan_result': ben_shan_result,
            'gong_result': gong_result,
            'sun_chanhe': sun_chanhe,          # 太阳躔度·合方之法（逐柱详情）
            'sun_chanhe_hit_pillars': sun_hit_pillars,  # 合方法达标的柱
            'sun_chanhe_bonus': sun_bonus,     # 合方法加分（日+10/他柱+3）
            'riyue_hesu': riyue_hesu,          # 日月合塑/对望（吊天星第二课）
            'qualified_count': qualified_count,
            'base_score': base_score,   # 旧口径(不含拱格/合方法加分)
            'score': score,             # 新口径(含拱格+合方法加分)
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
            # 展示：静态禄马位 + 天盘加临后的到山到向（口径统一：天盘加临）
            lu_show = pillar['lu_zhi'] or '无'
            lu_pos = pillar.get('tianpan_lu_zhi', '')
            lu_disp = f"{lu_show}→{lu_pos}" if lu_pos and lu_pos != lu_show else lu_show
            ma_show = pillar['ma_zhi'] or '无'
            ma_pos = pillar.get('tianpan_ma_zhi', '')
            ma_disp = f"{ma_show}→{ma_pos}" if ma_pos and ma_pos != ma_show else ma_show
            print(f"  禄神: {lu_disp} {'到山' if pillar['lu_to_shan'] else ''} {'到向' if pillar['lu_to_xiang'] else ''} {'三合' if pillar.get('lu_sanhe') else ''}")
            print(f"  驿马: {ma_disp} {'到山' if pillar['ma_to_shan'] else ''} {'到向' if pillar['ma_to_xiang'] else ''} {'三合' if pillar.get('ma_sanhe') else ''}")
            print(f"  贵人: {pillar['guiren_zhi']} {'到山' if pillar['guiren_to_shan'] else ''} {'到向' if pillar['guiren_to_xiang'] else ''} {'三合' if pillar.get('guiren_sanhe') else ''}")
            print(f"  到山数: {pillar['shan_count']} 到向数: {pillar['xiang_count']} 三合数: {pillar.get('sanhe_count', 0)}")
            print(f"  合格: {'✅' if pillar['pillar_qualified'] else '❌'}")
        
        if result['ben_shan_result']['has_ben_shan_ji']:
            print(f"\n⭐ 本山本向吉课:")
            for bs_result in result['ben_shan_result']['results']:
                print(f"   - {bs_result['desc']}")
        
        # 本命贵人 / 作禄 / 作马展示
        if result.get('ben_ming_result') and result['ben_ming_result'].get('hits'):
            bm = result['ben_ming_result']
            print(f"\n👤 本命贵人（本命{bm['ben_ming']}）:")
            for hit in bm['hits']:
                print(f"   - {hit['pillar']}柱天干{hit['gan']}之贵人")
        if result.get('ben_ming_result') and result['ben_ming_result'].get('ma_lu'):
            ml = result['ben_ming_result']['ma_lu']
            if ml['has_ben_ming_lu']:
                lu_desc = '；'.join(
                    '{}柱坐命禄{}'.format(h['pillar'], h['lu']) for h in ml['lu_hits'])
                print('   · 本命作禄（命干{}，禄在{}）：'.format(ml['lu_gan'], ml['lu_zhi']) + lu_desc)
            if ml['has_ben_ming_ma']:
                ma_desc = '；'.join(
                    '{}柱坐命马{}'.format(h['pillar'], h['ma']) for h in ml['ma_hits'])
                print('   · 本命作马（{}命，马在{}）：'.format(ml['ben_ming'], ml['ma_zhi']) + ma_desc)
        
        print(f"\n📊 合格数: {result['qualified_count']}/3")
        print(f"🎯 评分: {result['score']}分")
        print(f"📋 评语: {result['status']}")
        
        # 太阳躔度·合方之法展示（附加，不参与既有评分）
        if result.get('sun_chanhe'):
            print("\n☀️ 太阳躔度·合方之法（天体加临到山/向）:")
            for pname, r in result['sun_chanhe'].items():
                mark = '✅' if r['qualified'] else '  '
                print(f"  {mark} {pname}柱: {r['description']}")
        
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
        # 保存静态映射表中的贵人天盘支（用于夹贵检查）——贵人本支（天盘贵支），与"发传"判定同源
        ri_guiren_tian_zhi_set = set(self.GAN_GUIREN_ZHIS.get(ri_gan, []))
        # 【2026-09-06 坐标系混用修复】"贵人发三传"改为天将口径（传支所乘天将==贵人）。
        #   ri_guiren 保留 get_guiren_zhi（贵人加临的**地盘宫位**）仅供展示"贵人临何宫"，
        #   不再参与入传匹配（旧代码拿"加临宫位卯"与"天盘传支卯"字面匹配 → 假阳性）。
        ri_guiren = self.get_guiren_zhi(ri_gan, tiandi_pan, shichen) if (tiandi_pan and shichen) else self.GAN_GUIREN_ZHIS.get(ri_gan, [])

        nian_lu = self.get_lu_zhi(nian_gan) if nian_gan else None
        nian_ma = self.get_ma_zhi(nian_zhi) if nian_zhi else None
        # 年/月贵人：天将盘由**日干**唯一决定，年干/月干没有自己的乘将位；
        #   原 get_guiren_zhi(年干/月干) 返回的仍是"日贵加临位"，正确性错误。
        #   统一用静态本支（GAN_GUIREN_ZHIS）匹配传支。
        nian_guiren = list(self.GAN_GUIREN_ZHIS.get(nian_gan, [])) if nian_gan else None
        yue_lu = self.get_lu_zhi(yue_gan) if yue_gan else None
        yue_ma = self.get_ma_zhi(yue_zhi) if yue_zhi else None
        yue_guiren = list(self.GAN_GUIREN_ZHIS.get(yue_gan, [])) if yue_gan else None
        
        all_lu = set(filter(None, [ri_lu, nian_lu, yue_lu]))
        all_ma = set(filter(None, [ri_ma, nian_ma, yue_ma]))
        
        # 展开贵人列表（支持单值或列表）
        def _flatten_guiren(guiren_val):
            if guiren_val is None:
                return set()
            if isinstance(guiren_val, list):
                return set(guiren_val)
            return {guiren_val}
        
        all_guiren = set()
        all_guiren.update(_flatten_guiren(ri_guiren))
        all_guiren.update(_flatten_guiren(nian_guiren))
        all_guiren.update(_flatten_guiren(yue_guiren))
        
        lu_in_sanchuan = []
        ma_in_sanchuan = []
        guiren_in_sanchuan = []

        # 【2026-09-06 坐标系混用修复】日贵人入传 = 传支乘贵人之将（天将口径），
        #   guiren_chuan_hit 为乘贵人的传支集合（供下方收集 + 前端展示）。
        guiren_chuan_hit = self._sanchuan_guiren_chuan(sanchuan, ri_gan, tiandi_pan, shichen)

        for i, chuan in enumerate(chuan_list):
            chuan_name = ['初传', '中传', '末传'][i]
            if chuan in all_lu:
                lu_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '禄神'})
            if chuan in all_ma:
                ma_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '驿马'})
            # 【2026-09-06 坐标系混用修复】贵人入传改为天将口径：传支所乘天将==贵人。
            #   all_guiren 含"加临宫位(展示用)"，不能再用字面匹配（例：卯宫乘贵 ↔ 传支卯乘白虎）。
            if chuan in guiren_chuan_hit:
                guiren_in_sanchuan.append({'传': chuan_name, '地支': chuan, '类型': '贵人'})

        # 检查日柱禄马贵人是否在三传中（支持列表形式的贵人）
        ri_lu_in_sanchuan = ri_lu in chuan_list if ri_lu else False
        ri_ma_in_sanchuan = ri_ma in chuan_list if ri_ma else False
        ri_guiren_in_sanchuan = bool(guiren_chuan_hit)
        
        ri_luma_guiren_in_sanchuan = ri_lu_in_sanchuan or ri_ma_in_sanchuan or ri_guiren_in_sanchuan
        
        nian_lu_in_sanchuan = nian_lu in chuan_list if nian_lu else False
        nian_ma_in_sanchuan = nian_ma in chuan_list if nian_ma else False
        nian_guiren_set = _flatten_guiren(nian_guiren)
        nian_guiren_in_sanchuan = any(g in chuan_list for g in nian_guiren_set) if nian_guiren_set else False
        
        yue_lu_in_sanchuan = yue_lu in chuan_list if yue_lu else False
        yue_ma_in_sanchuan = yue_ma in chuan_list if yue_ma else False
        yue_guiren_set = _flatten_guiren(yue_guiren)
        yue_guiren_in_sanchuan = any(g in chuan_list for g in yue_guiren_set) if yue_guiren_set else False
        
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
        
        # ===== 三传间神贵禄检查（传间见贵/夹贵/夹禄）=====
        # 检查三传两两之间的间神是否为日干贵人或日干禄
        # 规则：两传之间的中间地支（间神）若为日干贵人，则为吉格"夹贵"
        #       若为日干禄，则为吉格"夹禄"
        jianshen_guiren = []
        ri_lu_zhi = self.LU.get(ri_gan, '')  # 日干的禄支
        
        for i in range(len(chuan_list) - 1):
            chuan_a = chuan_list[i]
            chuan_b = chuan_list[i + 1]
            a_idx = self.DIZHI_ORDER.index(chuan_a) if chuan_a in self.DIZHI_ORDER else -1
            b_idx = self.DIZHI_ORDER.index(chuan_b) if chuan_b in self.DIZHI_ORDER else -1
            
            if a_idx < 0 or b_idx < 0:
                continue
            
            # 计算间神：取较短路径上的中间地支
            diff_clockwise = (b_idx - a_idx) % 12
            diff_counterclockwise = (a_idx - b_idx) % 12
            
            if diff_clockwise <= diff_counterclockwise:
                # 顺时针方向
                if diff_clockwise > 1:
                    jianshen_idx = (a_idx + diff_clockwise // 2) % 12
                    jianshen_zhi = self.DIZHI_ORDER[jianshen_idx]
                else:
                    jianshen_zhi = None
            else:
                # 逆时针方向
                if diff_counterclockwise > 1:
                    jianshen_idx = (b_idx + diff_counterclockwise // 2) % 12
                    jianshen_zhi = self.DIZHI_ORDER[jianshen_idx]
                else:
                    jianshen_zhi = None
            
            if jianshen_zhi:
                # 检查是否为日干贵人（夹贵）或日干禄（夹禄）
                # 使用贵人的天盘支（ri_guiren_tian_zhi_set）检查夹贵
                if jianshen_zhi in ri_guiren_tian_zhi_set:
                    chuan_names = ['初传', '中传', '末传']
                    jianshen_guiren.append({
                        'between': f"{chuan_names[i]}({chuan_a})与{chuan_names[i+1]}({chuan_b})",
                        'jianshen': jianshen_zhi,
                        'type': '日干贵人',
                        'pattern': '夹贵'
                    })
                elif jianshen_zhi == ri_lu_zhi:
                    chuan_names = ['初传', '中传', '末传']
                    jianshen_guiren.append({
                        'between': f"{chuan_names[i]}({chuan_a})与{chuan_names[i+1]}({chuan_b})",
                        'jianshen': jianshen_zhi,
                        'type': '日干禄',
                        'pattern': '夹禄'
                    })
        
        # 初末传之间的间神（首尾相连）
        if len(chuan_list) == 3:
            chuan_first = chuan_list[0]
            chuan_last = chuan_list[-1]
            f_idx = self.DIZHI_ORDER.index(chuan_first) if chuan_first in self.DIZHI_ORDER else -1
            l_idx = self.DIZHI_ORDER.index(chuan_last) if chuan_last in self.DIZHI_ORDER else -1
            
            if f_idx >= 0 and l_idx >= 0:
                diff_cw = (f_idx - l_idx) % 12
                diff_ccw = (l_idx - f_idx) % 12
                
                if diff_cw <= diff_ccw:
                    if diff_cw > 1:
                        jianshen_idx = (l_idx + diff_cw // 2) % 12
                        jianshen_zhi = self.DIZHI_ORDER[jianshen_idx]
                    else:
                        jianshen_zhi = None
                else:
                    if diff_ccw > 1:
                        jianshen_idx = (f_idx + diff_ccw // 2) % 12
                        jianshen_zhi = self.DIZHI_ORDER[jianshen_idx]
                    else:
                        jianshen_zhi = None
                
                if jianshen_zhi:
                    # 检查是否为日干贵人（夹贵）或日干禄（夹禄）
                    # 使用贵人的天盘支（ri_guiren_tian_zhi_set）检查夹贵
                    if jianshen_zhi in ri_guiren_tian_zhi_set:
                        jianshen_guiren.append({
                            'between': f"末传({chuan_last})与初传({chuan_first})",
                            'jianshen': jianshen_zhi,
                            'type': '日干贵人',
                            'pattern': '夹贵'
                        })
                    elif jianshen_zhi == ri_lu_zhi:
                        jianshen_guiren.append({
                            'between': f"末传({chuan_last})与初传({chuan_first})",
                            'jianshen': jianshen_zhi,
                            'type': '日干禄',
                            'pattern': '夹禄'
                        })
        
        has_jianshen_guiren = len(jianshen_guiren) > 0
        jianshen_guiren_score = len(jianshen_guiren) * 8  # 每个间神贵人+8分
        
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
            'sanchuan_status': sanchuan_status,
            # 三传间神贵人（传间见贵）
            'jianshen_guiren': jianshen_guiren,
            'has_jianshen_guiren': has_jianshen_guiren,
            'jianshen_guiren_count': len(jianshen_guiren),
            'jianshen_guiren_score': jianshen_guiren_score
        }

    def get_benefited_zodiacs(self, ri_gan: str, yuejiang: str, shichen: str,
                               sanchuan: list = None,
                               nian_gan: str = None, yue_gan: str = None) -> Dict:
        """
        计算得利属相（贵人禄乘临属相）
        
        核心逻辑：
        1. 发传的贵人禄上 → 贵人禄所在地支对应的属相得利
        2. 贵人禄下临的地支 → 贵人禄乘临地支对应的属相得利
        
        示例：
        - 三传申子辰水局
        - 乙巳年月日，贵人在申、子
        - 申下为辰，子下为申
        - 所以申子辰属相的人得利
        
        参数：
            ri_gan: 日干
            yuejiang: 月将
            shichen: 时辰
            sanchuan: 三传列表
            nian_gan: 年干（可选）
            yue_gan: 月干（可选）
        
        返回：
            包含得利属相信息的字典
        """
        if sanchuan is None:
            sanchuan = []
        
        # 计算天地盘
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
        
        # 创建天盘→地盘的反向映射
        tian_to_di = {}
        for di_zhi, tian_zhi in tiandi_pan.items():
            if tian_zhi not in tian_to_di:
                tian_to_di[tian_zhi] = di_zhi
        
        # 收集所有贵人禄
        all_guiren_zhis = set()
        all_lu_zhis = set()
        
        # 日干贵人禄
        ri_guiren_zhis = self.GAN_GUIREN_ZHIS.get(ri_gan, [])
        ri_lu_zhi = self.LU.get(ri_gan, '')
        
        # 从三传中提取贵人禄
        for chuan_zhi in sanchuan:
            if chuan_zhi in ri_guiren_zhis:
                all_guiren_zhis.add(chuan_zhi)
            if chuan_zhi == ri_lu_zhi:
                all_lu_zhis.add(chuan_zhi)
            
            # 年干贵人禄
            if nian_gan:
                nian_guiren_zhis = self.GAN_GUIREN_ZHIS.get(nian_gan, [])
                nian_lu_zhi = self.LU.get(nian_gan, '')
                if chuan_zhi in nian_guiren_zhis:
                    all_guiren_zhis.add(chuan_zhi)
                if chuan_zhi == nian_lu_zhi:
                    all_lu_zhis.add(chuan_zhi)
            
            # 月干贵人禄
            if yue_gan:
                yue_guiren_zhis = self.GAN_GUIREN_ZHIS.get(yue_gan, [])
                yue_lu_zhi = self.LU.get(yue_gan, '')
                if chuan_zhi in yue_guiren_zhis:
                    all_guiren_zhis.add(chuan_zhi)
                if chuan_zhi == yue_lu_zhi:
                    all_lu_zhis.add(chuan_zhi)
        
        # 计算得利地支
        benefited_zhis = set()
        jianshen_details = []
        
        # 贵人所在地支本身的属相得利
        for zhi in all_guiren_zhis:
            benefited_zhis.add(zhi)
            jianshen_details.append({
                'zhi': zhi,
                'zodiac': self.SHENGXIAO.get(zhi, '未知'),
                'reason': '贵人所在',
                'type': '贵人'
            })
        
        # 禄所在地支本身的属相得利
        for zhi in all_lu_zhis:
            benefited_zhis.add(zhi)
            jianshen_details.append({
                'zhi': zhi,
                'zodiac': self.SHENGXIAO.get(zhi, '未知'),
                'reason': '禄所在',
                'type': '禄'
            })
        
        # 贵人乘临地支的属相得利
        for guiren_zhi in all_guiren_zhis:
            lin_zhi = tian_to_di.get(guiren_zhi, '')
            if lin_zhi:
                benefited_zhis.add(lin_zhi)
                jianshen_details.append({
                    'zhi': lin_zhi,
                    'zodiac': self.SHENGXIAO.get(lin_zhi, '未知'),
                    'reason': f'贵人{guiren_zhi}乘临',
                    'type': '贵人乘临'
                })
        
        # 禄乘临地支的属相得利
        for lu_zhi in all_lu_zhis:
            lin_zhi = tian_to_di.get(lu_zhi, '')
            if lin_zhi:
                benefited_zhis.add(lin_zhi)
                jianshen_details.append({
                    'zhi': lin_zhi,
                    'zodiac': self.SHENGXIAO.get(lin_zhi, '未知'),
                    'reason': f'禄{lu_zhi}乘临',
                    'type': '禄乘临'
                })
        
        # 排序得利地支（按地支顺序）
        sorted_zhis = sorted(benefited_zhis, 
                             key=lambda x: self.DIZHI_ORDER.index(x) if x in self.DIZHI_ORDER else 99)
        
        # 生成得利属相列表
        benefited_zodiacs = []
        for zhi in sorted_zhis:
            zodiac = self.SHENGXIAO.get(zhi, '未知')
            benefited_zodiacs.append(f"{zhi}({zodiac})")
        
        return {
            'benefited_zhis': sorted_zhis,
            'benefited_zodiacs': benefited_zodiacs,
            'all_guiren_zhis': list(all_guiren_zhis),
            'all_lu_zhis': list(all_lu_zhis),
            'jianshen_details': jianshen_details,
            'tiandi_pan': tiandi_pan
        }

    def analyze_full_with_sanchuan(self, mountain: str, shichen: str,
                                    nian_gan: str, nian_zhi: str,
                                    yue_gan: str, yue_zhi: str,
                                    ri_gan: str, ri_zhi: str,
                                    shi_gan: str = None, shi_zhi: str = None,
                                    sanchuan: Dict = None,
                                    year: int = None, month: int = None, day: int = None,
                                    ben_ming: str = None, ben_ming_gan: str = None) -> Dict:
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
            ri_gan, ri_zhi,
            shi_gan, shi_zhi,
            ben_ming, ben_ming_gan,
            year=year, month=month, day=day
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

        # 【2026-09-06 修复】tiandi_pan/yuejiang 仅在 `if sanchuan:` 分支定义；
        #   sanchuan 为空时下方 jike_ctx 构造会 UnboundLocalError → 此处兜底补算（保持同口径）。
        if not sanchuan:
            if year and month and day:
                yuejiang = self.get_yuejiang_by_date(year, month, day)
            else:
                yuejiang = self.get_yuejiang(yue_zhi) if yue_zhi else '亥'
            tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)

        # 精细禄马贵人评分（2026-08-24：六位置×三类带权，到山到向三级+发传，≥60合格）
        base_result['precision'] = self.score_precision_luma_guiren(
            mountain, shichen,
            nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi,
            shi_gan, shi_zhi, ben_ming, ben_ming_gan,
            sanchuan, base_result.get('sanchuan_result')
        )

        # 课体修正（2026-08-24：禄马贵人到山到向为基础分，十三吉课加分、凶课减分封顶20）
        ke_ti_name = (sanchuan or {}).get('课体') or (sanchuan or {}).get('keti') or ''
        # 【2026-09-05 十三吉课精细判据】构造 jike_ctx（sike/三传/天将/禄马/龙德），jike_13.check_jike_13 落码
        _jike_ctx = self._build_jike_ctx(
            ri_gan, ri_zhi, nian_zhi, yue_zhi, sanchuan, tiandi_pan, shichen, ben_ming or '',
            shan_jia, xiang_shou, mountain or '',
            nian_gan=nian_gan or '', yue_gan=yue_gan or '', yuejiang=yuejiang or '')
        base_result['keti_adjust'] = self.apply_keti_adjustment(ke_ti_name, jike_ctx=_jike_ctx)
        _kadj = base_result['keti_adjust']
        _prec = base_result['precision']
        # 最终分 = 禄马贵人到山到向(基础) + 课体±修正；合格仍以基础分≥60为准（加分不抬合格）
        _prec['keti'] = _kadj
        _prec['base_score'] = _prec.get('precision_score', 0)
        _prec['precision_score'] = round(max(0, min(100, _prec.get('precision_score', 0) + _kadj['ke_score'])), 2)
        _prec['keti_score'] = _kadj['ke_score']
        _prec['keti_note'] = _kadj['note']
        # qualified 保持为基础分判定，仅提排序
        _prec['qualified'] = _prec['base_score'] >= 60

        # 三传间神贵人（传间见贵）字段提取到顶层
        _sr = base_result.get('sanchuan_result') or {}
        base_result['jianshen_guiren_count'] = _sr.get('jianshen_guiren_count', 0)
        base_result['jianshen_guiren'] = _sr.get('jianshen_guiren', [])
        base_result['has_jianshen_guiren'] = _sr.get('has_jianshen_guiren', False)

        return base_result
