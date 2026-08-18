# -*- coding: utf-8 -*-
"""
事体走向引擎（六壬断事流程 · 2026-08-18）
=============================================
核心思想（用户方法论）：六壬判断除吉凶外，主要判断**事体的变化过程与走向**——
初始如何 → 中途如何 → 最终如何。吉凶只是走向的终点标签，走向本身才是主体。

本引擎输出三阶段叙事 + 走向类型，规则全部来自古籍断案语料实证：

  语料（壬占汇选543案 + 疏正218案）中提取的走向表述：
    - "初传中传空而末传不空 = 先涉艰难然后得遂"（知识库 L783/L830）
    - "有初传墓库而末传长生 = 自难变易否极泰来"（L1471）
    - "末传生初传生日干 = 暗地有人扶持，所图皆成"（L689/L780）
    - "先兴旺而后衰败也"（§疏正 干支互脱）→ 先吉后凶
    - "先凶后吉，恩旨赦回"（§官讼16·212）→ 先凶后吉
    - "先失后得，先虚后实，耗废尽了却得妻财助起家"（§财产）→ 先败后成
    - "循环格三传不离四课主病多反复"（知识库 L1077）→ 反复
    - "有始无终，乐极生悲"（L1470）→ 先成后败

输入：三传(初/中/末)、日干支、天将、旬空、课体
输出：{'走向': '先难后易'/'先吉后凶'/..., '阶段': {初/中/末 各自态势},
       '叙事': '先...，中...，末...', '终局': '吉'/'凶'/'平'}
"""
import os
import sys
from typing import Dict, List, Any, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 地支五行/天干五行
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
# 日墓（五行三合墓）
GAN_MU = {'甲': '未', '乙': '未', '丙': '戌', '丁': '戌', '戊': '辰',
          '己': '辰', '庚': '丑', '辛': '丑', '壬': '辰', '癸': '辰'}
# 五行长生
WX_CS = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}
# 天将吉凶
_JI_JIANG = {'贵人', '青龙', '六合', '太常', '天后', '太阴'}
_XIONG_JIANG = {'白虎', '玄武', '螣蛇', '朱雀'}


def _duan_shi(zhi: str, ri_gan: str, tj: str, kong: set) -> str:
    """单传态势：吉/凶/平（地支生克 + 天将 + 空亡）。"""
    if not zhi:
        return '平'
    s = 0.0
    gw = GAN_WX.get(ri_gan, '')
    zw = ZHI_WX.get(zhi, '')
    if gw and zw:
        if KE.get(zw) == gw:
            s -= 2  # 克日
        elif SHENG.get(gw) == zw:
            s -= 1  # 泄日
        elif SHENG.get(zw) == gw:
            s += 2  # 生日
    if tj in _JI_JIANG:
        s += 1.5
    elif tj in _XIONG_JIANG:
        s -= 1.5
    if zhi in kong:
        s -= 1.5
    if s >= 1:
        return '吉'
    if s <= -1:
        return '凶'
    return '平'


class LiuChenEngine:
    """事体走向引擎：三阶段（初=始/中=过程/末=结局）走向判定"""

    def _mk(self, walk, end, chu_shi, zhong_shi, mo_shi, chu, zhong, mo, narr):
        return {
            '走向': walk,
            '终局': end,
            '阶段': {'初传': chu_shi, '中传': zhong_shi, '末传': mo_shi},
            '叙事': narr,
            '三传': f'{chu}·{zhong}·{mo}',
        }

    def analyze(self, ri_gan: str, ri_zhi: str,
                sanchuan: List[str], tianjiang_list: List[str] = None,
                kongwang=('', ''), keti: str = '', sike: List = None) -> Dict[str, Any]:
        """
        主入口。返回事体走向分析。
        sanchuan: [初传, 中传, 末传]
        tianjiang_list: [初传天将, 中传天将, 末传天将]
        sike: 四课（用于循环格"三传不离四课"判定，L1077）
        """
        if not sanchuan or len(sanchuan) < 3:
            return {'走向': '未定', '阶段': {}, '叙事': '三传不全，无法判断事体走向', '终局': '平'}
        tj = list(tianjiang_list or [])
        kong = set(kongwang or [])
        chu, zhong, mo = sanchuan[0], sanchuan[1], sanchuan[2]
        chu_tj = tj[0] if len(tj) > 0 else ''
        zhong_tj = tj[1] if len(tj) > 1 else ''
        mo_tj = tj[2] if len(tj) > 2 else ''

        # ── 阶段态势 ──
        chu_shi = _duan_shi(chu, ri_gan, chu_tj, kong)
        zhong_shi = _duan_shi(zhong, ri_gan, zhong_tj, kong)
        mo_shi = _duan_shi(mo, ri_gan, mo_tj, kong)
        mu_zhi = GAN_MU.get(ri_gan, '')
        cs_zhi = WX_CS.get(GAN_WX.get(ri_gan, ''), '')
        gw = GAN_WX.get(ri_gan, '')
        chu_wx, zhong_wx, mo_wx = ZHI_WX.get(chu, ''), ZHI_WX.get(zhong, ''), ZHI_WX.get(mo, '')

        # ── 知识库增强规则（duanan_knowledge_base 实证）──
        # ① 三传递生：初生中、中生末、末生日干 → 得人引荐扶持事成（L777/L722）
        if (gw and chu_wx and zhong_wx and mo_wx and
                SHENG.get(chu_wx) == zhong_wx and SHENG.get(zhong_wx) == mo_wx and
                SHENG.get(mo_wx) == gw):
            return self._mk('三传递生', '吉', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            '三传{0}递生（{1}生{2}、{2}生{3}、{3}生日干），得人引荐扶持，事成所谋遂意'.format(
                                f'{chu}·{zhong}·{mo}', chu_wx, zhong_wx, mo_wx))
        # ② 三传递克：初克中、中克末、末克日干 → 交易损伤事败（L723）
        if (gw and chu_wx and zhong_wx and mo_wx and
                KE.get(chu_wx) == zhong_wx and KE.get(zhong_wx) == mo_wx and
                KE.get(mo_wx) == gw):
            return self._mk('三传递克', '凶', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                            '三传{0}递克（{1}克{2}、{2}克{3}、{3}克日干），层层伤害，事有损伤终归败'.format(
                                f'{chu}·{zhong}·{mo}', chu_wx, zhong_wx, mo_wx))
        # ③ 干支交互相克 → 官非口舌（§0047 实证"干支交互相克，家庭必主官非口舌"）
        #    简化判据：初传克日干 且 中传生初传（干支互克之象）——由 _duan_shi 已覆盖部分，
        #    此处用"初传克日+末传克日"双鬼作加强走向判定
        # ④ 循环格：三传不离四课 → 反复（L1077"循环格主病多反复"）——需四课，见下方

        # ── 基础走向判定（语料实证规则）──
        # ⓪ 循环格：三传不离四课 → 反复（L1077"循环格主病多反复"，L1374"主贼人复来"）
        if sike and len(sike) >= 4:
            sike_zhi = set()
            for k in sike:
                if isinstance(k, (list, tuple)) and len(k) >= 2:
                    sike_zhi.add(str(k[1]))
                    if len(k) >= 3:
                        sike_zhi.add(str(k[2]))
                elif isinstance(k, dict):
                    sike_zhi.add(str(k.get('上神', '')))
                    sike_zhi.add(str(k.get('下神', '')))
            if {chu, zhong, mo} <= sike_zhi:
                return self._mk('反复', '平', chu_shi, zhong_shi, mo_shi, chu, zhong, mo,
                                f'三传{chu}·{zhong}·{mo}不离四课，循环格，事有反复，一波三折')
        # ① 末传生日干 → 暗地有人扶持，事终成（知识库 L689/L780）
        if ZHI_WX.get(mo) and SHENG.get(ZHI_WX.get(mo, '')) == GAN_WX.get(ri_gan, ''):
            walk = '先难后易' if chu_shi == '凶' else '渐入佳境'
            narr = f'初传{chu}{chu_shi}，中传{zhong}{zhong_shi}，末传{mo}生日干，暗地有人扶持，事终有济'
            end = '吉'
        # ② 末传=长生 → 结局转生（自墓传生/否极泰来）
        elif mo == cs_zhi:
            walk = '先凶后吉' if (chu_shi == '凶' or zhong_shi == '凶') else '终得生助'
            narr = f'初{chu_shi}中{zhong_shi}，末传{mo}为日干长生，先难后易，否极泰来'
            end = '吉'
        # ③ 末传=日墓 → 有始无终/乐极生悲（L1470）
        elif mo == mu_zhi:
            walk = '先成后败' if (chu_shi == '吉' or zhong_shi == '吉') else '终归于晦'
            narr = f'初{chu_shi}中{zhong_shi}，末传{mo}为日墓，有始无终，乐极生悲之象'
            end = '凶'
        # ④ 初传中传空亡而末传不空 → 先涉艰难然后得遂（L783/L830）
        elif (chu in kong and zhong in kong) and mo not in kong:
            walk = '先难后易'
            narr = f'初传{chu}中传{zhong}空亡，末传{mo}不空，先涉艰难费尽心力然后得遂'
            end = '吉'
        # ⑤ 初凶末吉 → 先凶后吉
        elif chu_shi == '凶' and mo_shi == '吉':
            walk = '先凶后吉'
            narr = f'初传{chu}凶，末传{mo}吉，先凶后吉，终得吉'
            end = '吉'
        # ⑥ 初吉末凶 → 先吉后凶
        elif chu_shi == '吉' and mo_shi == '凶':
            walk = '先吉后凶'
            narr = f'初传{chu}吉，末传{mo}凶，先吉后凶，终归于凶'
            end = '凶'
        # ⑦ 三传皆吉 → 事必成
        elif chu_shi == '吉' and zhong_shi == '吉' and mo_shi == '吉':
            walk = '顺遂有成'
            narr = f'三传{chu}·{zhong}·{mo}皆吉，事必成，一帆风顺'
            end = '吉'
        # ⑧ 三传皆凶 → 事必败
        elif chu_shi == '凶' and zhong_shi == '凶' and mo_shi == '凶':
            walk = '艰阻终败'
            narr = f'三传{chu}·{zhong}·{mo}皆凶，事多艰阻，终归于败'
            end = '凶'
        # ⑨ 中末空亡 → 反复难定
        elif mo in kong and zhong in kong:
            walk = '反复难定'
            narr = f'中末传空亡，事有反复，一波三折，须耐心等待'
            end = '平'
        # ⑩ 默认：按末传态势定终局
        else:
            if mo_shi == '吉':
                walk = '终得吉' if chu_shi != '吉' else '始终向吉'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，末传{mo}吉，事终有济'
                end = '吉'
            elif mo_shi == '凶':
                walk = '终归于凶' if chu_shi != '凶' else '始终向凶'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，末传{mo}凶，事终不利'
                end = '凶'
            else:
                walk = '吉凶参半'
                narr = f'初{chu_shi}中{zhong_shi}末{mo_shi}，吉凶参半，看类神走向'
                end = '平'

        return self._mk(walk, end, chu_shi, zhong_shi, mo_shi, chu, zhong, mo, narr)


def analyze_liuchen(ri_gan: str, ri_zhi: str, sanchuan: List[str],
                    tianjiang_list: List[str] = None, kongwang=('', ''), keti: str = '',
                    sike: List = None) -> Dict[str, Any]:
    """便捷入口"""
    return LiuChenEngine().analyze(ri_gan, ri_zhi, sanchuan, tianjiang_list, kongwang, keti, sike)


if __name__ == '__main__':
    # 自测
    for sc, tj, rg in [(['亥', '酉', '卯'], ['六合', '太阴', '青龙'], '甲'),
                       (['戌', '午', '丑'], ['玄武', '朱雀', '白虎'], '甲'),
                       (['申', '亥', '寅'], ['白虎', '六合', '青龙'], '甲')]:
        r = analyze_liuchen(rg, '子', sc, tj)
        print(f'{sc} {tj} → {r["走向"]} / {r["终局"]} / {r["叙事"]}')
