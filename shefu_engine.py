# -*- coding: utf-8 -*-
"""六壬射覆引擎（2026-08-18）

射覆（覆物猜物）判法，全部出自《大六壬通解·下卷》射覆专章
（袁天罡《射覆无移口鉴》三十四诀，data/_tongjie_ocr/通解_下.txt L9372-9739）
与《大六壬苗公射覆鬼撮脚》（engine/ancient_truth_labels.json source 字段）。

输出链：有无 → 物类 → 形质 → 颜色 → 死活 → 新旧 → 虚实 → 数目 → 左右/覆仰 → 五味。
"""

# ══════════════════════════════════════════════════════════════
# 一、用神取法（口诀一："刚日柔辰射覆基"——阳干看日上神、阴干看辰上神，兼初传）
# ══════════════════════════════════════════════════════════════
GAN_RUO = {'甲': '刚', '丙': '刚', '戊': '刚', '庚': '刚', '壬': '刚',
           '乙': '柔', '丁': '柔', '己': '柔', '辛': '柔', '癸': '柔'}


def shefu_yongshen(ri_gan: str, sike, sanchuan) -> dict:
    """射覆用神：刚日=干上神(第一课上神)，柔日=支上神(第三课上神)，兼初传发用。"""
    gan_shang = ''
    zhi_shang = ''
    for k in (sike or []):
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            if str(k[0]) in ('第一课', '一'):
                gan_shang = str(k[1])
            if str(k[0]) in ('第三课', '三'):
                zhi_shang = str(k[2 - 2] if False else k[1])
    for i, k in enumerate(sike or []):
        us = str(k[1]) if isinstance(k, (list, tuple)) and len(k) >= 2 else str(k.get('上神', '')) if isinstance(k, dict) else ''
        if i == 0:
            gan_shang = us
        if i == 2:
            zhi_shang = us
    sc = list(sanchuan or [])
    chu = sc[0] if sc else ''
    ys = gan_shang if GAN_RUO.get(ri_gan) == '刚' else zhi_shang
    return {'用神': ys, '初传': chu, '日上神': gan_shang, '辰上神': zhi_shang,
            'mode': f'刚日看日上神' if GAN_RUO.get(ri_gan) == '刚' else '柔日看辰上神',
            'src': '《射覆无移口鉴》"刚日柔辰射覆基…阳干看日上神，阴干看辰上神；次兼初传发用之神，合而决之"'}
