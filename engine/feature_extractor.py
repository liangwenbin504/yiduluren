# -*- coding: utf-8 -*-
"""长征第1期 · 特征向量提取器
统一打包 10 类引擎输出为「特征向量」，供四元组标注做「引擎依据」。
方案 B：引擎不过滤，输出全部命中 + 标签，标注时人工筛选。
"""
import sys
sys.path.insert(0, '.')


def extract_features(ri_gan, ri_zhi, nian_zhi, yue_zhi, yuejiang, shichen,
                     sanchuan, sike, tian_jiang, tiandi_pan, zhanlei='其他',
                     sec='', y=2026, m=1, d=1, sanchuan_tianjiang=None) -> dict:
    """提取一案的完整特征向量。
    sike: [[课名, 上神, 下神], ...]
    tian_jiang: {天盘支: 天将名}
    tiandi_pan: arrange_tiandi_pan 返回 dict
    """
    feats = {}

    # ── 1~4. 课经(64课) + 毕法赋(100法) + 特殊课格 + 变格（judge_all 编排器）──
    try:
        from engine.judge_orchestrator import build_judge_env, judge_all
        env = build_judge_env(
            ri_gan=ri_gan, ri_zhi=ri_zhi, nian_zhi=nian_zhi, yue_zhi=yue_zhi,
            yuejiang=yuejiang, sike=sike, sanchuan=sanchuan, keti='',
            tian_jiang=tian_jiang, tiandi_pan=tiandi_pan, shichen=shichen,
            zhanlei=zhanlei, y=y, m=m, d=d, sanchuan_tianjiang=sanchuan_tianjiang,
        )
        jr = judge_all(env)
        feats['keti'] = jr.get('keti_judged', [])            # 64课课格 [{课体,条件,依据}]
        feats['bifa'] = jr.get('bifa_judged', {'匹配法句': [], '断法': []})  # 毕法赋（断法含分类）
        feats['special'] = jr.get('special_kege', {'匹配课格': []})
        feats['bianjie'] = jr.get('bianjie_kege', {'匹配变格': []})
    except Exception as e:
        feats['keti'] = []; feats['bifa'] = {'匹配法句': [], '断法': []}
        feats['special'] = {}; feats['bianjie'] = {}
        feats['_err_judge'] = str(e)

    # ── 5. 应期（洛书支数/月建/太岁，叙事层）──
    try:
        from engine.liuren_keti_bifa import get_yingqi_unified
        feats['yingqi'] = get_yingqi_unified(
            ri_gan, ri_zhi, sanchuan, tiandi_pan=tiandi_pan, si_ke=sike,
            shichen=shichen, tai_sui_zhi=nian_zhi, zhanlei=zhanlei)
    except Exception as e:
        feats['yingqi'] = ''

    # ── 6. 类象（神将类象：属相/类象/乘神寓意/乘神断语）──
    try:
        from engine.liuren_leixiang_knowledge import build_leixiang
        gs = sike[0][1] if sike and len(sike) >= 1 else ''
        zs = sike[2][1] if sike and len(sike) >= 3 else ''
        feats['leixiang'] = build_leixiang(tian_jiang, sanchuan, gs, zs)
    except Exception as e:
        feats['leixiang'] = []

    # ── 7. 天将（贵神盘，已传入）──
    feats['tianjiang'] = tian_jiang

    # ── 8. 断案知识（20占类 key_principles + 占类断语）──
    try:
        from engine.zhanlei_duanyu import build_zhanlei_duanyu
        keti_name = feats['keti'][0]['课体'] if feats['keti'] else ''
        bifa_names = feats['bifa'].get('匹配法句', []) or []
        feats['duanan'] = build_zhanlei_duanyu(
            zhanlei=zhanlei, keti=keti_name, bifa_names=bifa_names, sec=sec)
    except Exception as e:
        feats['duanan'] = {}

    return feats
