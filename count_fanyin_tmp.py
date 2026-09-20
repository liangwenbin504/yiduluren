# -*- coding: utf-8 -*-
"""临时统计：返吟判定改经典后，219 真实案中多少例改变 返吟/伏吟 状态。"""
import sys, json
sys.path.insert(0, r'E:\仪度六壬择日\yiduluren')
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
from engine.liuren_keti_bifa import _is_tiandi_fan_yin, _is_tiandi_fu_yin

REAL = json.load(open(r'E:\仪度六壬择日\yiduluren\engine\shuzheng_real_cases.json', encoding='utf-8'))
VALID = set("子丑寅卯辰巳午未申酉戌亥")
CHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}

calc = SiKeSanChuanCalculator2()
lose_fanyin, gain_fanyin, gain_fuyin = [], [], []
n_valid = 0
for c in REAL:
    sc = c.get("sanchuan") or []
    if not isinstance(sc, list):
        sc = list(sc)
    rizhu = c.get("day_ganzhi", "")
    if len(sc) < 3 or not rizhu or len(rizhu) < 2:
        continue
    truth = c.get("label", "")
    if truth not in ("吉","凶","平"):
        continue
    n_valid += 1
    rg, rz = rizhu[0], rizhu[1]
    yj = c["yue_jiang"] if c.get("yue_jiang") in VALID else ""
    scn = c["shichen"] if c.get("shichen") in VALID else ""
    try:
        res = calc.calculate(rg, rz, yj, scn)
        tdp = res.get("tiandi_pan", {})
    except Exception:
        tdp = {}
    # 旧代理：初末传冲
    a, c2 = sc[0], sc[2]
    old_fy = CHONG.get(a) == c2
    # 新经典：天地盘全冲 / 全同
    new_fy = _is_tiandi_fan_yin(tdp) if tdp else False
    new_fu = _is_tiandi_fu_yin(tdp) if tdp else False
    tag = f"{c.get('case_id')} rizhu={rizhu} cat={c.get('zhanlei')} label={truth}"
    if old_fy and not new_fy:
        lose_fanyin.append(tag)
    if (not old_fy) and new_fy:
        gain_fanyin.append(tag)
    if new_fu:
        gain_fuyin.append(tag)

print(f"有效案例总数: {n_valid}")
print(f"\n【失去返吟】(旧代理标返吟 → 新经典不标): {len(lose_fanyin)} 例")
for t in lose_fanyin:
    print("   ", t)
print(f"\n【获得返吟】(旧未标 → 新经典标返吟): {len(gain_fanyin)} 例")
for t in gain_fanyin:
    print("   ", t)
print(f"\n【获得伏吟】(新经典新增，旧无确定性伏吟): {len(gain_fuyin)} 例")
for t in gain_fuyin:
    print("   ", t)
print(f"\n净变化: 返吟 -{len(lose_fanyin)} +{len(gain_fanyin)}; 伏吟 +{len(gain_fuyin)}")
