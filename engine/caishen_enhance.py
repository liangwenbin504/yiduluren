"""
求财类神专项增强模块
=======================
用户明确指出股票预测的类神优先级：
1. 朱雀+六合同现(四课/三传) → 最高优先级
2. 财爻(妻财) → 次优先级  
3. 青龙 → 辅助确认

原理依据(六壬经典):
- 朱雀主文书消息 → 股市=信息驱动(公告/新闻/政策)
- 六合主交易契约 → 股市=买卖交易/并购合作
- 青龙主财帛吉庆 → 股市=资金流入/主升浪
- 财爻(妻财) → 直接财富指标

本模块作为 D-S 证据融合的新增证据组, 输出信念质量 mass 函数。
"""

from typing import Dict, List, Tuple, Optional

# 日干五行 → 十二长生起始位
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
CHANGSHENG_POS = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}

# ============================================================
# 核心检测函数
# ============================================================

def detect_caishen_patterns(
    tianjiang_list: List[str],
    tianjiang_map: Optional[Dict[str, str]] = None,
    san_chuan: Optional[List[str]] = None,
    si_ke: Optional[List[List[str]]] = None,
    liuqin_list: Optional[List[Dict]] = None,
    ri_gan: str = "",
) -> Dict:
    """
    检测求财类神模式，返回结构化信号。

    参数:
        tianjiang_list: 三传天将列表 ["青龙","朱雀","六合"]
        tianjiang_map: 地盘→天将映射 {地支: 天将名}
        san_chuan: 三传地支 ["巳","寅","亥"]
        si_ke: 四课 [[gan_str, gan_上神, gan_上神地支], ...]
        liuqin_list: 六亲分析列表 [{"六亲":"妻财","地支":"寅",...}, ...]
        ri_gan: 日干

    返回:
        {
            "zhunque_liuhe_together": bool,      # 朱雀+六合同现
            "zhunque_liuhe_positions": [...],    # 同现位置
            "zhunque_liuhe_score": float,        # 同现信号强度
            "caiyao_in_sanchuan": bool,          # 财爻入传
            "caiyao_positions": [...],           # 财爻位置
            "caiyao_with_qinglong": bool,        # 财爻+青龙
            "caiyao_with_zhunque": bool,         # 财爻+朱雀
            "caiyao_with_liuhe": bool,           # 财爻+六合
            "qinglong_in_sanchuan": bool,        # 青龙入传
            "qinglong_position": "",             # 青龙位置
            "overall_bullish": float,            # 综合看涨强度 0-10
            "overall_bearish": float,            # 综合看跌强度 0-10
            "signals": [...],                    # 人类可读信号描述
        }
    """
    result = {
        "zhunque_liuhe_together": False,
        "zhunque_liuhe_positions": [],
        "zhunque_liuhe_score": 0.0,
        "caiyao_in_sanchuan": False,
        "caiyao_positions": [],
        "caiyao_with_qinglong": False,
        "caiyao_with_zhunque": False,
        "caiyao_with_liuhe": False,
        "qinglong_in_sanchuan": False,
        "qinglong_position": "",
        "overall_bullish": 0.0,
        "overall_bearish": 0.0,
        "signals": [],
    }

    if not tianjiang_list or not san_chuan:
        return result

    # ---- 收集所有出现的天将(三传 + 四课) ----
    all_tianjiang = set()
    tj_with_positions = []  # [(位置描述, 天将名, 地支)]
    
    for i, (tj, zhi) in enumerate(zip(tianjiang_list, san_chuan)):
        pos_name = ["初传", "中传", "末传"][i]
        if tj:
            all_tianjiang.add(tj)
            tj_with_positions.append((pos_name, tj, zhi))
    
    # 四课中的天将
    if tianjiang_map and si_ke:
        for i, ke in enumerate(si_ke):
            if len(ke) >= 3:
                shang_shen = ke[2]  # 上神地支
                tj = tianjiang_map.get(shang_shen, "")
                if tj:
                    all_tianjiang.add(tj)
                    ke_name = f"课{i+1}" if i < 4 else f"干上" if i == 0 else "支上"
                    tj_with_positions.append((f"四课-{ke_name}", tj, shang_shen))

    # ============================================================
    # 规则1: 朱雀+六合同现 → 最高优���级
    # ============================================================
    has_zhunque = "朱雀" in all_tianjiang
    has_liuhe = "六合" in all_tianjiang
    
    if has_zhunque and has_liuhe:
        result["zhunque_liuhe_together"] = True
        zq_positions = [(p, t, z) for p, t, z in tj_with_positions if t == "朱雀"]
        lh_positions = [(p, t, z) for p, t, z in tj_with_positions if t == "六合"]
        result["zhunque_liuhe_positions"] = [
            f"{p}({t}临{z})" for p, t, z in zq_positions + lh_positions
        ]

        # 强度计算:
        # 同在三传 → 最强(8分)
        # 一个在三传一个在四课 → 强(6分)
        # 同在四课 → 中强(4分)
        zq_in_sanchuan = any("传" in p for p, _, _ in zq_positions)
        lh_in_sanchuan = any("传" in p for p, _, _ in lh_positions)
        if zq_in_sanchuan and lh_in_sanchuan:
            result["zhunque_liuhe_score"] = 8.0
            result["signals"].append("★★★ 朱雀+六合同入三传：信息驱动+交易活跃，超强看涨")
        elif zq_in_sanchuan or lh_in_sanchuan:
            result["zhunque_liuhe_score"] = 6.0
            result["signals"].append("★★ 朱雀+六合跨三传四课分布：消息面+交易面共振，强看涨")
        else:
            result["zhunque_liuhe_score"] = 4.0
            result["signals"].append("★ 朱雀+六合同现四课：消息面+交易面共振，偏看涨")

        # 【修复】将同现分数累积到 bullish
        result["overall_bullish"] += result["zhunque_liuhe_score"]

    # ============================================================
    # 规则2: 财爻入传
    # ============================================================
    has_caiyao = False
    caiyao_positions_detail = []
    
    if liuqin_list:
        for i, lq in enumerate(liuqin_list):
            if isinstance(lq, dict) and lq.get("六亲") == "妻财":
                has_caiyao = True
                zhi = lq.get("地支", san_chuan[i] if i < len(san_chuan) else "")
                pos_name = ["初传", "中传", "末传"][i] if i < 3 else f"传{i+1}"
                caiyao_positions_detail.append((pos_name, zhi))
                
                # 检查同位置的将
                if i < len(tianjiang_list):
                    tj = tianjiang_list[i]
                    if tj == "青龙":
                        result["caiyao_with_qinglong"] = True
                    elif tj == "朱���":
                        result["caiyao_with_zhunque"] = True
                    elif tj == "六合":
                        result["caiyao_with_liuhe"] = True

    if has_caiyao:
        result["caiyao_in_sanchuan"] = True
        result["caiyao_positions"] = [f"{p}({z})" for p, z in caiyao_positions_detail]
        
        # 位置权重: 初传最重(末传最轻); 财爻入初传=强信号
        caiyao_score = 0.0
        for pos, _ in caiyao_positions_detail:
            if pos == "初传":
                caiyao_score += 5.0
                result["signals"].append(f"财爻入初传({pos})：财运发动，强烈看涨")
            elif pos == "中传":
                caiyao_score += 3.0
                result["signals"].append(f"财爻入中传({pos})：财运行进中，看涨")
            elif pos == "末传":
                caiyao_score += 1.5
                result["signals"].append(f"财爻入末传({pos})：财运收敛，弱看涨")
        
        # 同将加成
        if result["caiyao_with_qinglong"]:
            caiyao_score += 3.0
            result["signals"].append("★★★ 财爻+青龙：资金流入+财星发动，主升浪信号")
        if result["caiyao_with_zhunque"]:
            caiyao_score += 2.0
            result["signals"].append("★★ 财爻+朱雀：消息驱动型上涨，题材炒作信号")
        if result["caiyao_with_liuhe"]:
            caiyao_score += 2.0
            result["signals"].append("★★ 财爻+六合：合作/并购利好，共振上涨信号")
        
        result["overall_bullish"] += caiyao_score

    # ============================================================
    # 规则3: 青龙入传(独立于财爻)
    # ============================================================
    if "青龙" in all_tianjiang:
        result["qinglong_in_sanchuan"] = True
        ql_positions = [(p, z) for p, t, z in tj_with_positions if t == "青龙"]
        if ql_positions:
            result["qinglong_position"] = ql_positions[0][0]
            pos, _ = ql_positions[0]
            if "初传" in pos:
                result["overall_bullish"] += 3.0
                result["signals"].append("青龙入初传：资金面宽松，吉神发动")
            elif "中传" in pos:
                result["overall_bullish"] += 2.0
                result["signals"].append("青龙入中传：资金持续流入")
            elif "末传" in pos:
                result["overall_bullish"] += 1.0
                result["signals"].append("青龙入末传：尾盘资金流入")
            elif "四课" in pos:
                result["overall_bullish"] += 1.5
                result["signals"].append("青龙临四课：背景资金面偏好")
    else:
        # 青龙不在三传/四课中 → 资金面不明确，微偏空
        # 【修复】但如果朱雀+六合同现, 不扣分(共振信号已足够强)
        if not result["zhunque_liuhe_together"]:
            result["overall_bearish"] += 0.5

    # ============================================================
    # 规则4: 朱雀/六合单独出现(不同时)
    # ============================================================
    if has_zhunque and not has_liuhe:
        zq_pos = [(p, z) for p, t, z in tj_with_positions if t == "朱雀"]
        if zq_pos:
            pos, zhi = zq_pos[0]
            if "初传" in pos:
                result["overall_bullish"] += 3.0
                result["signals"].append("朱雀入初传：消息面强驱动，看涨")
            elif "中传" in pos:
                result["overall_bullish"] += 2.0
                result["signals"].append("朱雀入中传：消息驱动中，偏涨")
            else:
                result["overall_bullish"] += 1.0
                result["signals"].append("朱雀在四课：消息面存在")

    if has_liuhe and not has_zhunque:
        lh_pos = [(p, z) for p, t, z in tj_with_positions if t == "六合"]
        if lh_pos:
            pos, zhi = lh_pos[0]
            if "初传" in pos:
                result["overall_bullish"] += 3.5
                result["signals"].append("六合入初传：交易发动，强看涨")
            elif "中传" in pos:
                result["overall_bullish"] += 2.5
                result["signals"].append("六合入中传：交易推进中，偏涨")
            else:
                result["overall_bullish"] += 1.5
                result["signals"].append("六合在四课：市场交投存在")

    # ============================================================
    # 规则5: 朱雀+六合+青龙三神会 → 极大看涨
    # ============================================================
    if has_zhunque and has_liuhe and "青龙" in all_tianjiang:
        result["overall_bullish"] += 2.0
        result["signals"].append("★★★ 朱雀+六合+青龙三神会：信息+交易+资金三共振，极强看涨")

    # ============================================================
    # 规则6: 日干长生入传 + 求财类神在场 → 财源得长生之助 [v6新增]
    # 六壬理论: 日干长生入三传=根基得助/生机发动，若青龙/朱雀/六合在盘则财路通
    # 目标: 救回C-2类边际案例(SZ-092/102/162/222: 巳寅亥+青龙四课+P吉微弱领先)
    # ============================================================
    if ri_gan and san_chuan:
        rw = GAN_WX.get(ri_gan, '')
        cs = CHANGSHENG_POS.get(rw, '')
        if cs and cs in san_chuan:
            # 长生入传成立 → 检查是否有求财类神在场
            wealth_tj = [t for t in all_tianjiang if t in ('青龙', '朱雀', '六合')]
            if wealth_tj:
                bonus = 1.5 + 0.5 * len(wealth_tj)  # 越多越好, 上限2.5
                bonus = min(bonus, 2.5)
                result["overall_bullish"] += bonus
                tj_names = '+'.join(wealth_tj)
                pos = ['初传','中传','末传'][san_chuan.index(cs)] if cs in san_chuan else '三传'
                result["signals"].append(f"★ 日干长生{cs}入{pos}+{tj_names}临盘：财源得长生之助(+{bonus:.1f})")

    # ============================================================
    # 归一化
    # ============================================================
    result["overall_bullish"] = min(10.0, result["overall_bullish"])
    result["overall_bearish"] = min(10.0, result["overall_bearish"])

    return result


def caishen_to_mass(caishen_result: Dict, base_conf: float = 0.75) -> Dict[str, float]:
    """
    将求财类神检测结果转换为 D-S 信念质量 mass 函数。

    返回: {涨,跌,平,⊤}
    """
    bullish = caishen_result.get("overall_bullish", 0.0)
    bearish = caishen_result.get("overall_bearish", 0.0)
    net = bullish - bearish

    # 没有信号 → 返回纯无知(⊤=1.0)
    if not caishen_result.get("signals") or (bullish < 1.0 and bearish < 1.0):
        return {"涨": 0.0, "跌": 0.0, "平": 0.0, "⊤": 1.0}

    # 信号强度映射到信念质量
    # |net| 0-2 → 弱信号, |net| 3-5 → 中, |net| 6+ → 强
    strength = min(0.95, abs(net) / 10.0)
    
    # 置信度调整：朱雀+六合同现 → 高置信度
    has_dual = caishen_result.get("zhunque_liuhe_together", False)
    conf = min(0.95, base_conf + (0.10 if has_dual else 0.0))
    committed = conf * strength
    mass = {"涨": 0.0, "跌": 0.0, "平": 0.0, "⊤": 1.0 - committed}

    if net > 0:
        mass["涨"] = committed
    elif net < 0:
        mass["跌"] = committed
    else:
        mass["平"] = committed

    return mass


def get_caishen_signal_for_fusion(
    tianjiang_list: List[str],
    tianjiang_map: Optional[Dict[str, str]] = None,
    san_chuan: Optional[List[str]] = None,
    si_ke: Optional[List[List[str]]] = None,
    liuqin_list: Optional[List[Dict]] = None,
    ri_gan: str = "",
) -> Tuple[float, bool, float, Dict]:
    """
    生成用于 D-S 融合的求财类神信号。

    返回: (score, up_positive, confidence, detail_dict)
    - score: 正=看涨, 负=看跌
    - up_positive: True
    - confidence: 信号置信度
    - detail_dict: 检测详情
    """
    detail = detect_caishen_patterns(
        tianjiang_list, tianjiang_map, san_chuan, si_ke, liuqin_list, ri_gan
    )

    bullish = detail.get("overall_bullish", 0.0)
    bearish = detail.get("overall_bearish", 0.0)
    net = bullish - bearish

    # 无显著信号
    if abs(net) < 0.5:
        return 0.0, True, 0.0, detail

    # 置信度
    has_dual = detail.get("zhunque_liuhe_together", False)
    conf = 0.75 + (0.10 if has_dual else 0.0)
    if detail.get("caiyao_with_qinglong"):
        conf += 0.10
    
    # 分数缩放
    score = net * 0.8  # 让求财类神信号与现有信号在同一尺度

    return score, True, conf, detail


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    # 测试1: 朱雀+六合同在三传
    print("=== 测试1: 朱雀+六合+青龙三神会 ===")
    r = detect_caishen_patterns(
        tianjiang_list=["朱雀", "六合", "青龙"],
        san_chuan=["巳", "寅", "子"],
        liuqin_list=[{"六亲": "妻财", "地支": "巳"}, {"六亲": "父母", "地支": "寅"}, {"六亲": "官鬼", "地支": "子"}],
    )
    for s in r["signals"]:
        print(f"  {s}")
    print(f"  bullish={r['overall_bullish']}, bearish={r['overall_bearish']}")
    mass = caishen_to_mass(r)
    print(f"  mass: 涨={mass['涨']:.3f} 跌={mass['跌']:.3f} ⊤={mass['⊤']:.3f}")

    # 测试2: 无求财信号
    print("\n=== 测试2: 无求财类神 ===")
    r = detect_caishen_patterns(
        tianjiang_list=["白虎", "玄武", "勾陈"],
        san_chuan=["申", "子", "辰"],
        liuqin_list=[{"六亲": "��鬼", "地支": "申"}, {"六亲": "父母", "地支": "子"}, {"六亲": "兄弟", "地支": "辰"}],
    )
    for s in r["signals"]:
        print(f"  {s}")
    print(f"  bullish={r['overall_bullish']}, bearish={r['overall_bearish']}")

    # 测试3: 财爻+青龙
    print("\n=== 测试3: 财爻+青龙 ===")
    r = detect_caishen_patterns(
        tianjiang_list=["青龙", "朱雀", "太常"],
        san_chuan=["寅", "午", "戌"],
        liuqin_list=[{"六亲": "妻财", "地支": "寅"}, {"六亲": "子孙", "地支": "午"}, {"六亲": "兄弟", "地支": "戌"}],
    )
    for s in r["signals"]:
        print(f"  {s}")
    print(f"  bullish={r['overall_bullish']}, bearish={r['overall_bearish']}")
