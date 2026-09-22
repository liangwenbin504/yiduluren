# -*- coding: utf-8 -*-
"""禳解／趋避提示层（2026-09-22 新建；🔴 **零评分影响**，只出提示不进分）

【原文依据】
  《通解》中 L1841（三阴课）：「或丧魂游魄、五鬼伏殃，诸煞并临，其祸尤甚……
    占病必死……百事凶殃，**宜禳之**。……**六处有救解神，未传旺相**，
    则应九二『鸣鹤在阴，其子和之』之象也。」⇒ 既给"宜禳"，也给"有救"判据。
  《通解》中 L2201（伏殃）：「天鬼者，正酉二午三卯四子……占主伏兵杀伤或**全家病**，
    **惟宜禳祷以除之**。」
  《通解》中 L2305（墓门开）：「出外宜**迁葬以禳之**」「人内宜**合寿木以禳之**」。
  《通解》中 L2450（励德）：「庶人身宅忧移动，魂梦不安**谢土神**」。
  《通解》中 L9371（刘日新验例）：「去此桃树、移厕远井，后果安静」⇒ 移改形煞之禳。

【数据】data/rangjie_map.json（规则表：触发／占类／提示／禳法／原文／验例）
【产出】{宜禳, 提示[], 禳法[], 有救, 有救理由[], 依据[]}
⛔ 只提示不判分；禳解属方术实践层，输出须带原文出处，不得凭空编法。
"""
import json
import os
from typing import Any, Dict, List

ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火',
          '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土',
          '丑': '土', '未': '土'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

_MAP_CACHE = None


def _load_map() -> Dict[str, Any]:
    global _MAP_CACHE
    if _MAP_CACHE is not None:
        return _MAP_CACHE
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'data', 'rangjie_map.json')
    try:
        with open(p, encoding='utf-8') as f:
            _MAP_CACHE = json.load(f)
    except Exception:
        _MAP_CACHE = {'规则': []}
    return _MAP_CACHE


def _is_wang(zhi: str, yue_jian: str) -> bool:
    """旺相：同气，或月建生之。"""
    zw, yw = ZHI_WX.get(zhi, ''), ZHI_WX.get(yue_jian, '')
    if not zw or not yw:
        return False
    return zw == yw or WX_SHENG.get(yw, '') == zw


def suggest(env: Dict[str, Any], judged: Dict[str, Any]) -> Dict[str, Any]:
    """产出禳解／趋避提示（🔴 不进评分链）。"""
    out: Dict[str, Any] = {'宜禳': False, '提示': [], '禳法': [],
                           '有救': False, '有救理由': [], '依据': [],
                           '占类': env.get('zhanlei', '') or ''}
    try:
        mp = _load_map()
        rules = mp.get('规则') or []
        ss = (judged.get('shensha_xiang') or {})
        ss_luo = ss.get('落点') or []
        ss_names = {x.get('煞') for x in ss_luo}
        keti = [h.get('课体') for h in (judged.get('keti_judged') or [])
                if isinstance(h, dict) and h.get('课体')]
        # 课格名来源：特殊课格 + 变格（变格名常带后缀，如「墓门开格重丧」，用子串匹配）
        kege = list(((judged.get('special_kege') or {}).get('匹配课格') or []))
        kege += list(((judged.get('bianjie_kege') or {}).get('匹配变格') or []))
        kege += [env.get('keti', '')] if env.get('keti') else []
        zhanlei = env.get('zhanlei', '') or '其他'

        for r in rules:
            # ── 主触发（OR）：必须是**特异煞/特异格** ──
            trig = r.get('触发') or []
            hit = False
            for t in trig:
                if t.startswith('shensha:') and t.split(':', 1)[1] in ss_names:
                    hit = True
                elif t.startswith('keti:') and any(t.split(':', 1)[1] in k for k in keti):
                    hit = True
                elif t.startswith('kege:') and any(t.split(':', 1)[1] in k for k in kege):
                    hit = True
            if not hit:
                continue
            # ── 佐证（「诸煞并临」「怪异骈集」：需 ≥N 个高频煞同时在课传六处）──
            need = int(r.get('佐证至少') or 0)
            if need > 0:
                ev = [t.split(':', 1)[1] for t in (r.get('佐证') or [])
                      if t.startswith('shensha:') and t.split(':', 1)[1] in ss_names]
                if len(set(ev)) < need:
                    continue
            cats = r.get('占类') or []
            if cats and zhanlei not in cats:
                continue
            out['提示'].append(r.get('提示', ''))
            if r.get('禳法'):
                out['禳法'].append(r.get('禳法'))
            if r.get('原文'):
                out['依据'].append('%s：%s' % (r.get('名', ''), r.get('原文')))
            if r.get('验例'):
                out['依据'].append('验例：%s' % r.get('验例'))
            out['宜禳'] = True

        # ── 有救判据（中 L1841：六处有救解神，未传旺相）──
        sc = list(env.get('sanchuan') or [])
        mo = sc[2] if len(sc) > 2 else ''
        yue_jian = env.get('yue_zhi', '') or env.get('yue_jian', '')
        if mo and _is_wang(mo, yue_jian):
            out['有救'] = True
            out['有救理由'].append('末传%s旺相（中L1841「未传旺相」⇒ 有救）' % mo)
        tj = env.get('tian_jiang') or {}
        gan = env.get('ri_gan', '')
        gwx = GAN_WX.get(gan, '')
        for z, j in tj.items():
            if j in ('贵人', '太常', '天后') and ZHI_WX.get(z, '') and gwx:
                if WX_SHENG.get(ZHI_WX.get(z, ''), '') == gwx:
                    out['有救'] = True
                    out['有救理由'].append('%s乘%s生干（六处有救解神）' % (j, z))
                    break
        if out['宜禳'] and out['有救']:
            out['提示'].append('宜禳而**有救**：禳之可解（中L1841「六处有救解神，未传旺相」）。')
        elif out['宜禳'] and not out['有救']:
            out['提示'].append('宜禳**而无救**：凶势难挽，禳仅可减（中L1841）。')
        return out
    except Exception as e:                      # 🔴 异常绝不外溢
        out['error'] = str(e)
        return out
