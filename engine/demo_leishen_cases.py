# -*- coding: utf-8 -*-
"""现代失物课例完整演示：起课(paipan_v2) → 类神定位 → W1-W4 判定 → 方位断语"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leishen_engine import judge_lost_modern, leishen_from_text
from zhanshi_duanyu_patched11 import paipan_v2

print('=' * 72)
print('  现代失物课例完整演示（起课 → 类神 → 判定 → 方位）')
print('=' * 72)

cfg = [
    # (标题, 占辞, 日干, 日支, 月将, 时辰, 初天将, 中天将, 末天将)
    ('课例一 · 占失手机（巳入传乘青龙）', '手机不见了', '辛', '巳', '亥', '申',
     '青龙', '太常', '六合'),
    ('课例二 · 占失钱包（辰受寅木克乘白虎）', '钱包被偷', '甲', '子', '卯', '午',
     '白虎', '天后', '六合'),
    ('课例三 · 占失钥匙（丑加长生）', '钥匙找不到', '丁', '卯', '戌', '巳',
     '六合', '青龙', '天后'),
]

for title, item, rg, rz, yj, sc_zhi, c1, c2, c3 in cfg:
    print()
    print('─' * 72)
    print(f'■ {title}')
    print(f'  占辞：{item}')

    # 1) 真实起课
    pp = paipan_v2(rg, rz, yj, sc_zhi)
    sanchuan = pp.get('sanchuan', [])
    print(f'  起课：{rg}{rz}日 {yj}将 {sc_zhi}时')
    print(f'        三传：{"→".join(sanchuan)} | 课体：{pp.get("keti", "")} | 发用：{pp.get("qifa", "")}')

    # 2) 类神定位
    ls = leishen_from_text(item)
    print(f'  类神：{item} → {ls}（现代分表）')

    # 3) 判定（三传用真实起课输出，天将为课理对应值）
    r = judge_lost_modern(item, sanchuan, rg, rz, [], c1, c2, c3, pp.get('sike', []))
    if r:
        mark = '吉' if r['end'] == '吉' else ('凶' if r['end'] == '凶' else r['end'])
        print(f'  判定：【{mark}】')
        print(f'    断语：{r["narr"]}')
        print(f'    出处：{r["src"]}')
    else:
        print('  判定：无类神，无法判')

print()
print('=' * 72)
print('说明：三传/四课/课体取自 paipan_v2 真实起课；天将为演示按课理标注')
print('  paipan_v2 起课 → leishen_from_text 定位 → judge_lost_modern W1-W4 → 方位断语')
print('=' * 72)