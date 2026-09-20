# -*- coding: utf-8 -*-
"""古文断语 → 现代白话（今译）映射表（2026-09-12 · 憨爷「不要再说奸淫不足那么难听了」）

🔴 定位＝**纯展示层**，三条铁律：
  ① **古籍原文一律不改**（真源仍是 `liuren_leixiang_knowledge.SHI_ER_SHEN_JIANG`）；
     本模块只提供「原文 → 今译」的**显示用**映射，原文始终保留在出参里（可追溯）。
  ② **绝不用于吉凶判定**！⚠️ `tianjiang_gongwei._XIONG` 把「淫」「羞」当**凶关键词**，
     `side_of_duanyu()` 必须吃**原文**；用今译喂它会**丢凶标**（如 天后·卯「临门，奸淫不足」本为凶）。
     ⇒ 一律：**判定用原文，显示用今译**。
  ③ 出参双轨：`乘神断语`（原文）＋ `乘神断语今`（今译）；`所主`＋`所主今`；`类象`＋`类象今`。

用法：
    from engine.liuren_gloss import gloss
    gloss('临门，奸淫不足')      # → '临门，未婚同居'
"""
from __future__ import annotations

# ── 整句精确映射（「十二将临地」断语，共 12 条含敏感字）──
MODERN_SENTENCE = {
    '临门，奸淫不足': '临门，未婚同居',
    '倚户，奸淫不足': '倚户，未婚同居',
    '裸体，奸淫羞': '失仪，私情外露',
    '遭淫，被乖争勾连争讼': '因私情受牵连，争闹缠讼',
    '裸形，口舌盗贼惊忧': '不加遮掩，招口舌失窃之忧',
    '毁妆，不悲忧则羞辱': '妆容失色，非悲即辱',
    '亡羞，因妄加罪': '失体面，因妄加罪责',
    '巧说，值奸人之谋计': '巧言游说，遭居心不良之人算计',
    '盘龟，祸淫福善': '盘龟，天道赏善罚恶',
    '入私室，不遑宁处': '涉入私密场所，难得安宁',
    '私窜，不明之因': '私下往来，缘由不明',
    '偷窥，因私': '暗中窥探，事出私情',
}

# ── 词级兜底（类象表 / 所主 / 乘神寓意 里的散词）──
# ⚠️ 一律用**多字词**；bare「私」不映射（「私门／私祷／阴私」是六壬正经术语）。
MODERN_WORD = {
    '奸淫不足': '未婚同居',
    '奸淫羞': '私情外露',
    '祸淫福善': '赏善罚恶',
    '奸淫': '私情',
    '淫女': '情感关系复杂之女',
    '娼妇': '风尘女子',
    '娼妓': '风尘女子',
    '乐妓': '歌乐女子',
    '淫泆': '男女关系失当',
    '奸邪': '邪僻',
    '奸人': '居心不良之人',
    '遭淫': '受私情牵连',
    '裸形': '不加遮掩',
    '裸体': '失仪',
    '亡羞': '失体面',
    '奸': '私情',
}

_KEYS = sorted(MODERN_WORD.keys(), key=len, reverse=True)   # 长词优先，防短词截胡


def gloss(text) -> str:
    """原文 → 今译（显示用）。非字符串／空 → 原样返回。"""
    s = str(text or '')
    if not s:
        return s
    if s in MODERN_SENTENCE:
        return MODERN_SENTENCE[s]
    for k in _KEYS:
        if k in s:
            s = s.replace(k, MODERN_WORD[k])
    return s


def gloss_deep(node):
    """对嵌套 dict / list / str 做深拷贝式今译（用于「类象」子表）。"""
    if isinstance(node, dict):
        return {k: gloss_deep(v) for k, v in node.items()}
    if isinstance(node, list):
        return [gloss_deep(v) for v in node]
    if isinstance(node, tuple):
        return tuple(gloss_deep(v) for v in node)
    if isinstance(node, str):
        return gloss(node)
    return node


if __name__ == '__main__':
    for src, want in MODERN_SENTENCE.items():
        got = gloss(src)
        print('%s  %-24s → %s' % ('ok ' if got == want else 'BAD', src, got))
