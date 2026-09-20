"""
多角度三传分析引擎 — Multi-Angle SanChuan Analyzer

核心理念：三传不能只看一个角度。必须从多个独立角度交叉验证，用角度投票决定最终信号。

五个分析角度：
  1. 课格角度 — 课体本身的吉凶等级
  2. 五行传变角度 — 初→中→末的五行生克＋十神变化
  3. 初传状态角度 — 初传是否受夹克、空亡、旺衰
  4. 末传天将角度 — 末传收官信号（鬼+白虎=暴跌，财+青龙=大涨）
  5. 三传结构角度 — 进连茹/退连茹/三合局/刑冲

融合策略：
  - 角度2(五行传变)和角度3(初传状态)为「否决级」
  - 5个角度多数投票，出现≥3个一致方向时信号增强
  - 分歧大时自动降级为震荡

设计原则（用户要求）：
  "单看三传不看五行生克，登三天课格就是吉课
   但要从几个角度去分析：
   一是从五行生克去，财化鬼→凶
   二看初传辰受夹克，涨不了→凶
   三看末传申鬼乘白虎，下跌厉害→凶
   多角度看三传，不能从单一角度"
"""

from typing import List, Dict, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════
#  基础设施
# ═══════════════════════════════════════════════════════════════

ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}

TIANJIANG_WUXING = {
    '贵人': '土', '螣蛇': '火', '朱雀': '火', '六合': '木',
    '勾陈': '土', '青龙': '木', '天空': '土', '白虎': '金',
    '太常': '土', '玄武': '水', '太阴': '金', '天后': '水',
}

WUXING_SK = {
    '木': {'生': '火', '克': '土'},
    '火': {'生': '土', '克': '金'},
    '土': {'生': '金', '克': '水'},
    '金': {'生': '水', '克': '木'},
    '水': {'生': '木', '克': '火'},
}

# 日干十神判定
def _is_gan_wealth(ri_gan: str, zhi: str) -> bool:
    """判断地支是否为日干的财爻"""
    gan_wx = GAN_WUXING.get(ri_gan, '')
    zhi_wx = ZHI_WUXING.get(zhi, '')
    if not gan_wx or not zhi_wx:
        return False
    return WUXING_SK.get(gan_wx, {}).get('克', '') == zhi_wx

def _is_gan_ghost(ri_gan: str, zhi: str) -> bool:
    """判断地支是否为日干的官鬼"""
    gan_wx = GAN_WUXING.get(ri_gan, '')
    zhi_wx = ZHI_WUXING.get(zhi, '')
    if not gan_wx or not zhi_wx:
        return False
    return WUXING_SK.get(zhi_wx, {}).get('克', '') == gan_wx

def _wuxing_ke(a_wx: str, b_wx: str) -> bool:
    """五行a是否克五行b"""
    return WUXING_SK.get(a_wx, {}).get('克', '') == b_wx

def _wuxing_sheng(a_wx: str, b_wx: str) -> bool:
    """五行a是否生五行b"""
    return WUXING_SK.get(a_wx, {}).get('生', '') == b_wx


# ═══════════════════════════════════════════════════════════════
#  课体吉凶等级映射
# ═══════════════════════════════════════════════════════════════

KETI_LEVEL = {
    # 吉课 → 偏涨（但力度因角度交叉验证会调整）
    '元首': ('涨', 0.5, '元首课，乾纲独断，趋势明确'),
    '铸印': ('涨', 0.7, '铸印课，印绶生身，大利'),
    '轩盖': ('涨', 0.6, '轩盖课，贵人乘车，上行'),
    '从革': ('涨', 0.4, '从革课(涉害)，多空博弈后上涨'),
    '涉害': ('涨', 0.3, '涉害课，多方发力后上行'),
    '登三天': ('涨', 0.3, '登三天课(涉害)，经历博弈后上涨'),
    '重审': ('平', 0.0, '重审课，审慎观望'),
    '知一': ('平', 0.0, '知一课，等待方向'),
    '比用': ('平', 0.0, '比用课，板块轮动'),
    '遥克': ('平', 0.0, '遥克课，外围影响'),
    '昴星': ('跌', 0.3, '昴星课，庄家运作风险'),
    '别责': ('跌', 0.3, '别责课，概念炒作风险'),
    '八专': ('跌', 0.4, '八专课，独立行情易跌'),
    '伏吟': ('跌', 0.5, '伏吟课，横盘滞涨'),
    '反吟': ('跌', 0.6, '反吟课，剧烈反转下行'),
    '察微': ('平', 0.1, '察微课，需细察'),
}

# 部分匹配（含后缀的课体）
def _get_keti_level(name: str):
    """从课体名获取吉凶等级（支持前缀匹配）"""
    name_clean = str(name).replace('课', '').replace('格', '').strip()
    for key, val in KETI_LEVEL.items():
        if key in name_clean:
            return val
    return ('平', 0.0, '未知课体')


# ═══════════════════════════════════════════════════════════════
#  角度1: 课格角度
# ═══════════════════════════════════════════════════════════════

class KetiAngle:
    """课体本身的吉凶判断"""
    
    @staticmethod
    def analyze(keti: str) -> Dict:
        direction, strength, reason = _get_keti_level(keti)
        return {
            'angle': '课格角度',
            'direction': direction,  # '涨'/'跌'/'平'
            'strength': strength,   # 0.0-1.0
            'reason': reason,
            'weight': 1.0,  # 权重（课格角度为基础，不否决）
        }


# ═══════════════════════════════════════════════════════════════
#  角度2: 五行传变角度
# ═══════════════════════════════════════════════════════════════

class WuxingChainAngle:
    """初→中→末的五行生克+十神传变"""
    
    @staticmethod
    def analyze(sanchuan: List[str], ri_gan: str) -> Dict:
        if len(sanchuan) != 3 or not ri_gan:
            return {'angle': '五行传变', 'direction': '平', 'strength': 0, 'reason': '数据不足', 'weight': 1.5}
        
        chu, zhong, mo = sanchuan
        chu_wx = ZHI_WUXING.get(chu, '')
        zhong_wx = ZHI_WUXING.get(zhong, '')
        mo_wx = ZHI_WUXING.get(mo, '')
        
        signals = []
        
        # ── 规则1: 传财化鬼 → 凶（否决级）──
        if _is_gan_wealth(ri_gan, chu) and _is_gan_ghost(ri_gan, mo):
            signals.append(('跌', 0.9, f'传财化鬼：初传{chu}(财)→末传{mo}(鬼)，取财致祸，大跌信号'))
        
        # ── 规则2: 传鬼化财 → 险中求财 ──
        if _is_gan_ghost(ri_gan, chu) and _is_gan_wealth(ri_gan, mo):
            signals.append(('涨', 0.6, f'传鬼化财：初传{chu}(鬼)→末传{mo}(财)，险中获利'))
        
        # ── 规则3: 三传递生 → 涨 ──
        if _wuxing_sheng(chu_wx, zhong_wx) and _wuxing_sheng(zhong_wx, mo_wx):
            signals.append(('涨', 0.5, f'三传递生：{chu}({chu_wx})生{zhong}({zhong_wx})生{mo}({mo_wx})'))
        
        # ── 规则4: 三传互克 → 跌 ──
        if _wuxing_ke(chu_wx, zhong_wx) and _wuxing_ke(zhong_wx, mo_wx):
            signals.append(('跌', 0.5, f'三传互克：{chu}({chu_wx})克{zhong}({zhong_wx})克{mo}({mo_wx})'))
        
        # ── 规则5: 初生中，中生末 → 递生吉 ──
        if _wuxing_sheng(chu_wx, zhong_wx) and _wuxing_sheng(zhong_wx, mo_wx):
            if not any(s[0] == '涨' and s[1] >= 0.5 for s in signals):
                signals.append(('涨', 0.4, f'递生：{chu}生{zhong}生{mo}'))
        
        # ── 规则6: 初克中，中克末 → 递克凶 ──
        if _wuxing_ke(chu_wx, zhong_wx) and _wuxing_ke(zhong_wx, mo_wx):
            if not any(s[0] == '跌' and s[1] >= 0.5 for s in signals):
                signals.append(('跌', 0.4, f'递克：{chu}克{zhong}克{mo}'))
        
        if not signals:
            return {'angle': '五行传变', 'direction': '平', 'strength': 0, 'reason': '无显著传变', 'weight': 1.5}
        
        # 取最强的信号
        signals.sort(key=lambda x: x[1], reverse=True)
        best = signals[0]
        return {
            'angle': '五行传变',
            'direction': best[0],
            'strength': best[1],
            'reason': best[2],
            'weight': 1.5,  # 否决级权重
        }


# ═══════════════════════════════════════════════════════════════
#  角度3: 初传状态角度
# ═══════════════════════════════════════════════════════════════

class ChuChuanAngle:
    """初传是否受夹克、空亡、旺衰"""
    
    @staticmethod
    def analyze(sanchuan: List[str], tian_jiang: Dict, tiandi_pan: Dict) -> Dict:
        if len(sanchuan) < 1:
            return {'angle': '初传状态', 'direction': '平', 'strength': 0, 'reason': '无初传', 'weight': 1.5}
        
        chu = sanchuan[0]
        chu_wx = ZHI_WUXING.get(chu, '')
        signals = []
        
        # ── 规则1: 初遭夹克（天将克+地盘克）→ 暴跌 ──
        jiang = tian_jiang.get('初传', '') if tian_jiang else ''
        tianjiang_ke = False
        dipan_ke = False
        dipan_zhi = ''
        
        if jiang:
            jiang_wx = TIANJIANG_WUXING.get(jiang, '')
            if jiang_wx and chu_wx and _wuxing_ke(jiang_wx, chu_wx):
                tianjiang_ke = True
        
        if tiandi_pan:
            for di, tian in tiandi_pan.items():
                if tian == chu:
                    dipan_zhi = di
                    di_wx = ZHI_WUXING.get(di, '')
                    if di_wx and chu_wx and _wuxing_ke(di_wx, chu_wx):
                        dipan_ke = True
                    break
        
        if tianjiang_ke and dipan_ke:
            signals.append(('跌', 0.95, f'初遭夹克：初传{chu}({chu_wx})被天将{jiang}+地盘{dipan_zhi}双重夹克，身不由己暴跌信号'))
        elif tianjiang_ke:
            signals.append(('跌', 0.4, f'初传{chu}被天将{jiang}克，受压'))
        
        # ── 规则2: 初传旺相+吉将 → 偏涨 ──
        if jiang in ('青龙', '六合', '贵人', '太常'):
            if not tianjiang_ke:
                signals.append(('涨', 0.3, f'初传{chu}乘{jiang}，吉将发用'))
        
        # ── 规则3: 初传坐墓库 → 受阻 ──
        if dipan_zhi:
            mu_map = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
                      '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}
            # 简化：初传坐自已的墓库位
            ri_gan_based = False  # 需要日干，从外部传入
            if dipan_zhi == chu:  # 自坐本气，不算墓
                pass
        
        if not signals:
            return {'angle': '初传状态', 'direction': '平', 'strength': 0, 'reason': '初传正常', 'weight': 1.5}
        
        signals.sort(key=lambda x: x[1], reverse=True)
        best = signals[0]
        return {
            'angle': '初传状态',
            'direction': best[0],
            'strength': best[1],
            'reason': best[2],
            'weight': 1.5,  # 否决级权重
        }


# ═══════════════════════════════════════════════════════════════
#  角度4: 末传天将角度
# ═══════════════════════════════════════════════════════════════

class MoChuanAngle:
    """末传收官信号——最关键的收盘方向"""
    
    @staticmethod
    def analyze(sanchuan: List[str], tian_jiang: Dict, ri_gan: str) -> Dict:
        if len(sanchuan) < 3:
            return {'angle': '末传天将', 'direction': '平', 'strength': 0, 'reason': '无末传', 'weight': 1.2}
        
        mo = sanchuan[2]
        jiang = tian_jiang.get('末传', '') if tian_jiang else ''
        signals = []
        
        # ── 规则1: 末传鬼+白虎 → 暴跌（最强利空）──
        if ri_gan and _is_gan_ghost(ri_gan, mo) and jiang == '白虎':
            signals.append(('跌', 0.95, f'末传{mo}(鬼)乘白虎，虎临干鬼凶速速，暴跌信号'))
        
        # ── 规则2: 末传鬼 → 利空 ──
        elif ri_gan and _is_gan_ghost(ri_gan, mo):
            severity = 0.6 if jiang in ('螣蛇', '玄武', '勾陈') else 0.4
            signals.append(('跌', severity, f'末传{mo}(鬼)乘{jiang}，尾盘压力'))
        
        # ── 规则3: 末传财+青龙 → 大涨 ──
        if ri_gan and _is_gan_wealth(ri_gan, mo) and jiang == '青龙':
            signals.append(('涨', 0.8, f'末传{mo}(财)乘青龙，龙财收尾，大涨信号'))
        
        # ── 规则4: 末传财+吉将 → 偏涨 ──
        elif ri_gan and _is_gan_wealth(ri_gan, mo):
            if jiang in ('六合', '贵人', '太常'):
                signals.append(('涨', 0.5, f'末传{mo}(财)乘{jiang}，尾盘收涨'))
        
        # ── 规则5: 末传白虎(非鬼) → 偏跌 ──
        if jiang == '白虎' and not (ri_gan and _is_gan_ghost(ri_gan, mo)):
            signals.append(('跌', 0.4, f'末传{mo}乘白虎，尾盘承压'))
        
        if not signals:
            return {'angle': '末传天将', 'direction': '平', 'strength': 0, 'reason': f'末传{mo}乘{jiang}，中性', 'weight': 1.2}
        
        signals.sort(key=lambda x: x[1], reverse=True)
        best = signals[0]
        return {
            'angle': '末传天将',
            'direction': best[0],
            'strength': best[1],
            'reason': best[2],
            'weight': 1.2,
        }


# ═══════════════════════════════════════════════════════════════
#  角度5: 三传结构角度
# ═══════════════════════════════════════════════════════════════

class StructureAngle:
    """进连茹/退连茹/三合局/刑冲"""
    
    @staticmethod
    def analyze(sanchuan: List[str]) -> Dict:
        if len(sanchuan) != 3:
            return {'angle': '三传结构', 'direction': '平', 'strength': 0, 'reason': '非标准三传', 'weight': 0.8}
        
        all_zhi = '子丑寅卯辰巳午未申酉戌亥'
        idx = [all_zhi.find(z) for z in sanchuan]
        
        if -1 in idx:
            return {'angle': '三传结构', 'direction': '平', 'strength': 0, 'reason': '无效地支', 'weight': 0.8}
        
        # ── 进连茹（三传连续递增）→ 涨 ──
        if idx[2] == (idx[1] + 1) % 12 and idx[1] == (idx[0] + 1) % 12:
            return {'angle': '三传结构', 'direction': '涨', 'strength': 0.5, 'reason': '进连茹，趋势向上', 'weight': 0.8}
        
        # ── 退连茹（三传连续递减）→ 跌 ──
        if idx[2] == (idx[1] - 1) % 12 and idx[1] == (idx[0] - 1) % 12:
            return {'angle': '三传结构', 'direction': '跌', 'strength': 0.5, 'reason': '退连茹，趋势下行', 'weight': 0.8}
        
        # ── 三合局检测 ──
        sanhe = {
            ('寅', '午', '戌'): '火局', ('申', '子', '辰'): '水局',
            ('巳', '酉', '丑'): '金局', ('亥', '卯', '未'): '木局',
        }
        for (a, b, c), name in sanhe.items():
            if {a, b, c} == set(sanchuan):
                if '火' in name or '木' in name:
                    return {'angle': '三传结构', 'direction': '涨', 'strength': 0.7, 'reason': f'三合{name}，合力向上', 'weight': 0.8}
                else:
                    return {'angle': '三传结构', 'direction': '跌', 'strength': 0.5, 'reason': f'三合{name}，合力偏空', 'weight': 0.8}
        
        # ── 三刑检测 ──
        xing_map = {'寅': '巳', '巳': '申', '申': '寅', '丑': '戌', '戌': '未', '未': '丑',
                     '子': '卯', '卯': '子', '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'}
        xing_count = sum(1 for z in sanchuan if xing_map.get(z, z) in sanchuan)
        if xing_count >= 2:
            return {'angle': '三传结构', 'direction': '跌', 'strength': 0.4, 'reason': f'三传带刑({xing_count}个)，动荡偏空', 'weight': 0.8}
        
        return {'angle': '三传结构', 'direction': '平', 'strength': 0, 'reason': '无特殊结构', 'weight': 0.8}


# ═══════════════════════════════════════════════════════════════
#  多角度融合引擎
# ═══════════════════════════════════════════════════════════════

class MultiAngleAnalyzer:
    """多角度三传分析器 — 主入口"""
    
    def __init__(self):
        self.angles = [
            KetiAngle(),
            WuxingChainAngle(),
            ChuChuanAngle(),
            MoChuanAngle(),
            StructureAngle(),
        ]
    
    def analyze(self,
                sanchuan: List[str],
                ri_gan: str = '',
                keti: str = '',
                tian_jiang: Optional[Dict] = None,
                tiandi_pan: Optional[Dict] = None,
                ) -> Dict:
        """
        多角度分析三传，返回融合信号。
        
        参数:
            sanchuan: 三传地支列表 ['辰','午','申']
            ri_gan: 日干
            keti: 课体名
            tian_jiang: 天将映射 {'初传':'六合','中传':'青龙','末传':'白虎'}
            tiandi_pan: 天地盘 {'寅':'辰',...}
        
        返回:
            {
                'angles': [各角度分析结果],
                'final': {'direction': '涨'/'跌'/'震荡', 'strength': 0-10, 'confidence': 0-100},
                'reasoning': '综合理由',
                'bull_votes': N, 'bear_votes': N, 'neutral_votes': N,
                'veto_triggered': bool
            }
        """
        if tian_jiang is None:
            tian_jiang = {}
        if tiandi_pan is None:
            tiandi_pan = {}
        
        # ── 逐角度分析 ──
        results = []
        
        # 角度1: 课格
        results.append(KetiAngle.analyze(keti))
        
        # 角度2: 五行传变
        results.append(WuxingChainAngle.analyze(sanchuan, ri_gan))
        
        # 角度3: 初传状态
        results.append(ChuChuanAngle.analyze(sanchuan, tian_jiang, tiandi_pan))
        
        # 角度4: 末传天将
        results.append(MoChuanAngle.analyze(sanchuan, tian_jiang, ri_gan))
        
        # 角度5: 三传结构
        results.append(StructureAngle.analyze(sanchuan))
        
        # ── 投票统计 ──
        bull_votes = 0.0   # 加权涨票数
        bear_votes = 0.0   # 加权跌票数
        neutral_votes = 0.0
        bull_count = 0
        bear_count = 0
        neutral_count = 0
        
        for r in results:
            w = r.get('weight', 1.0)
            d = r.get('direction', '平')
            if d == '涨':
                bull_votes += w
                bull_count += 1
            elif d == '跌':
                bear_votes += w
                bear_count += 1
            else:
                neutral_votes += w
                neutral_count += 1
        
        # ── 否决级检查 ──
        # 角度2(五行传变)和角度3(初传状态)如果同时指向跌 → 否决课格涨信号
        angle2 = results[1]  # 五行传变
        angle3 = results[2]  # 初传状态
        veto_triggered = False
        veto_reason = ''
        
        if angle2['direction'] == '跌' and angle2['strength'] >= 0.6 and \
           angle3['direction'] == '跌' and angle3['strength'] >= 0.4:
            veto_triggered = True
            veto_reason = f'五行传变({angle2["reason"][:30]}) + 初传状态({angle3["reason"][:30]}) → 双否决级看跌，覆盖课格偏涨信号'
        
        # ── 最终决策 ──
        total_weighted = bull_votes + bear_votes + neutral_votes
        if total_weighted == 0:
            return self._build_result(results, '震荡', 0, 50, bull_count, bear_count, neutral_count, veto_triggered)
        
        bull_pct = bull_votes / total_weighted
        bear_pct = bear_votes / total_weighted
        
        # 如果双否决触发，强制判跌
        if veto_triggered:
            direction = '跌'
            # 强度由熊方投票比例决定
            strength = round(bear_pct * 10, 1)
            confidence = min(95, round(bear_pct * 100) + 10)
            return self._build_result(results, direction, strength, confidence,
                                      bull_count, bear_count, neutral_count, veto_triggered, veto_reason)
        
        # 多数投票
        if bear_pct >= 0.60:
            direction = '跌'
        elif bull_pct >= 0.55:
            direction = '涨'
        elif bear_pct >= 0.45:
            direction = '跌'
        elif bull_pct >= 0.40:
            direction = '涨'
        else:
            direction = '震荡'
        
        strength = round(max(bull_pct, bear_pct) * 10, 1)
        confidence = round(max(bull_pct, bear_pct) * 100)
        
        return self._build_result(results, direction, strength, confidence,
                                  bull_count, bear_count, neutral_count, veto_triggered)
    
    def _build_result(self, angles, direction, strength, confidence,
                      bull, bear, neutral, veto, veto_reason=''):
        reasons = []
        for a in angles:
            icons = {'涨': '📈', '跌': '📉', '平': '➖'}
            icon = icons.get(a['direction'], '❓')
            reasons.append(f"  [{a['angle']}] {icon} {a['reason']}")
        
        if veto:
            reasons.insert(0, f'  ⚠️ 否决触发: {veto_reason}')
        
        return {
            'angles': angles,
            'final': {
                'direction': direction,
                'strength': strength,
                'confidence': confidence,
            },
            'votes': {
                'bull_weighted': round(sum(a.get('weight',1) for a in angles if a['direction']=='涨'), 1),
                'bear_weighted': round(sum(a.get('weight',1) for a in angles if a['direction']=='跌'), 1),
                'neutral_weighted': round(sum(a.get('weight',1) for a in angles if a['direction']=='平'), 1),
                'bull_count': bull,
                'bear_count': bear,
                'neutral_count': neutral,
            },
            'veto_triggered': veto,
            'reasoning': '\n'.join(reasons),
        }


# ═══════════════════════════════════════════════════════════════
#  便捷接口
# ═══════════════════════════════════════════════════════════════

def multi_angle_score(result: Dict) -> Tuple[str, int, str]:
    """
    从多角度分析结果中提取20d评分系统所需的增量分数和信号。
    
    返回: (direction, score_delta, reason)
      - score_delta: 建议在 trend_score 上加减的分数
      - direction: 用于覆盖趋势判断
    """
    final = result.get('final', {})
    direction = final.get('direction', '平')
    strength = final.get('strength', 0)
    veto = result.get('veto_triggered', False)
    
    if veto:
        # 否决级 → 强制跌，大幅扣分
        return ('跌', -int(strength * 1.5), f'多角度否决: {result.get("reasoning","")[:100]}')
    
    if direction == '跌' and strength >= 4:
        return ('跌', -int(strength), f'多角度偏跌 (强度{strength})')
    elif direction == '涨' and strength >= 4:
        return ('涨', +int(strength * 0.8), f'多角度偏涨 (强度{strength})')
    elif direction == '跌':
        return ('跌', -2, f'多角度略偏跌')
    elif direction == '涨':
        return ('涨', +2, f'多角度略偏涨')
    else:
        return ('平', 0, '多角度分歧，中性')


# ═══════════════════════════════════════════════════════════════
#  自测
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 测试：甲辰日辰时 三传辰→午→申（用户指出的问题案例）
    analyzer = MultiAngleAnalyzer()
    
    sanchuan = ['辰', '午', '申']
    tian_jiang = {'初传': '六合', '中传': '青龙', '末传': '白虎'}
    tiandi_pan = {'寅': '辰', '卯': '巳', '辰': '午', '巳': '未', '午': '申',
                  '未': '酉', '申': '戌', '酉': '亥', '戌': '子', '亥': '丑',
                  '子': '寅', '丑': '卯'}
    
    result = analyzer.analyze(
        sanchuan=sanchuan,
        ri_gan='甲',
        keti='涉害课(登三天)',
        tian_jiang=tian_jiang,
        tiandi_pan=tiandi_pan,
    )
    
    print("=" * 60)
    print("  多角度三传分析 — 甲辰日辰时 辰→午→申(登三天)")
    print("=" * 60)
    print()
    print("【各角度分析】")
    for a in result['angles']:
        icons = {'涨': '📈', '跌': '📉', '平': '➖'}
        print(f"  [{a['angle']}] {icons.get(a['direction'],'?')} {a['direction']} "
              f"(强度:{a['strength']:.1f} 权重:{a['weight']:.1f}) — {a['reason']}")
    
    print()
    print("【投票统计】")
    v = result['votes']
    print(f"  看涨: {v['bull_count']}角度 (加权{v['bull_weighted']})")
    print(f"  看跌: {v['bear_count']}角度 (加权{v['bear_weighted']})")
    print(f"  中性: {v['neutral_count']}角度 (加权{v['neutral_weighted']})")
    print(f"  否决触发: {result['veto_triggered']}")
    
    f = result['final']
    print()
    print(f"【最终信号】{f['direction']} (强度:{f['strength']} 置信:{f['confidence']}%)")
    
    if result['veto_triggered']:
        print(f"  ⚠️ {[a['reason'] for a in result['angles'] if a.get('angle')=='五行传变'][0]}")
        print(f"  ⚠️ {[a['reason'] for a in result['angles'] if a.get('angle')=='初传状态'][0]}")
