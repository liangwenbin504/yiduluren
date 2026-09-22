# -*- coding: utf-8 -*-
"""课格「主格裁定」层（2026-09-22 新建；🔴 **零评分影响**，只出裁定不进分）

【为何需要】实证反例：疏正疾病13·169（戊午日亥将戌时占病）
  引擎同时判出「三光失明(凶)」＋「荣华(吉)」＋「三阳(吉)」并列输出，无轻重 ⇒ 断语被稀释。
  传统六壬靠**轻重权衡**定主格，本层把这件事形式化。

【原文依据（逐条）】
  ·《通解》中 L3460 物类课象辞：「六亲俱现，**以用为主**。旺相吉言，休囚凶语。」
  ·《通解》中 L3462：「**凶将乘旺相气不为凶，吉将乘囚休气不为吉**」⇒ 旺囚优先于天将吉凶。
  ·《通解》上 L2568：「生日为吉，**虽凶将亦为吉**；克日为凶，**虽吉将亦为凶**」⇒ 生克日干优先。
  ·《通解》上 L2637：「旺相相生比和则吉；**休囚则转灾**；**空亡减半**；披刑带杀，灾病立至。」
  ·《通解》下 L3544 例：「宅上虽贵人发用，上下夹克为逼迫杀，贵人入庙，**吉不为吉**。」
  ·《通解》上 L6960：三光失明（中末因死乘凶将）⇒ 正格之「变格」优先于正格。

【裁定链（自下而上，后者压前者）】
  R1 变格/缺陷压正格：课体名含「失明／不备／别责／八专」等 ⇒ 降等。
  R2 生克日干优先（上L2568）：用神（初传）克日干 ⇒ 虽吉将亦为凶，吉格「不为吉」。
  R3 旺囚裁定（中L3462）：吉将乘囚休气不为吉；凶将乘旺相不为凶。
  R4 空亡减半（上L2637）：主格所依之支落旬空 ⇒ 减半。
  R5 煞压吉格（下L3544 例）：死气／死神／天鬼／病符 临干支或入传 ⇒ 吉格减等「不为吉」。
  R6 以用为主（中L3460）：多格并列时，取与初传（用神）相关者为主格。
"""
from typing import Any, Dict, List

ZHI = "子丑寅卯辰巳午未申酉戌亥"
# 洛书（太玄）地支本数：子午9／丑未8／寅申7／卯酉6／辰戌5／巳亥4
# 《通解》下 L7772 三限数法实证「申七未八」；评疏「寅数七，其家七口」同此体系。
ZHI_SHU = {'子': 9, '午': 9, '丑': 8, '未': 8, '寅': 7, '申': 7,
           '卯': 6, '酉': 6, '辰': 5, '戌': 5, '巳': 4, '亥': 4}

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火',
          '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土',
          '丑': '土', '未': '土'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

# 阳刃（羊刃）：日干禄之前一辰（阳顺阴逆）。评疏「中、末、日上三个羊刃杀」用此计数。
# 甲卯／乙寅／丙午／丁巳／戊午／己巳／庚酉／辛申／壬子／癸亥
# 实证：本课戊午日 ⇒ 羊刃午，中传午·末传午·干上午 共 3 处（评疏：三个羊刃）。
YANG_REN = {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午',
            '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'}

JI_JIANG = ('贵人', '青龙', '六合', '太常', '天后', '太阴')
XIONG_JIANG = ('螣蛇', '朱雀', '勾陈', '天空', '白虎', '玄武')

# 明确为「凶」的课格关键字（命中即作凶性证据）
XIONG_KEYS = ('失明', '天狱', '天网', '天祸', '天寇', '魄化', '丧魂', '伏殃',
              '灾厄', '死', '绝', '墓门', '六片板', '九丑', '乱首', '赘婿',
              '刑', '害', '鬼', '脱', '空亡', '罗网')
# 明确为「吉」的课格关键字
JI_KEYS = ('三光', '三阳', '三奇', '六仪', '富贵', '龙德', '官爵', '高盖',
           '乘轩', '斫轮', '铸印', '荣华', '合欢', '和美', '时泰', '六合',
           '引从', '升迁', '亨通', '连珠')


def _is_ji(name: str, detail: Dict[str, Any]) -> bool:
    lvl = str((detail or {}).get('等级', ''))
    if '凶' in lvl:
        return False
    if '吉' in lvl:
        return True
    return any(k in name for k in JI_KEYS) and not any(k in name for k in XIONG_KEYS)


def _is_xiong(name: str, detail: Dict[str, Any]) -> bool:
    lvl = str((detail or {}).get('等级', ''))
    if '凶' in lvl:
        return True
    return any(k in name for k in XIONG_KEYS)


def arbitrate(env: Dict[str, Any], judged: Dict[str, Any]) -> Dict[str, Any]:
    """主格裁定：输入 judge_all 各层结果，输出主格／降等理由／倾向。"""
    out: Dict[str, Any] = {'主格': '', '主格性质': '平', '吉格': [], '凶格': [],
                           '降等': [], '理由': [], '数目': {}, '倾向': '平'}
    try:
        keti = judged.get('keti_judged') or []
        sp = (judged.get('special_kege') or {})
        bj = (judged.get('bianjie_kege') or {})
        ss = (judged.get('shensha_xiang') or {})
        gan = env.get('ri_gan', '')
        sc = list(env.get('sanchuan') or [])
        chu = sc[0] if sc else ''
        chu_tj = (env.get('sanchuan_tianjiang') or [''])[0] if env.get('sanchuan_tianjiang') else ''
        kong = env.get('kongwang') or ('', '')

        # ── 收集课格 ──
        items: List[Dict[str, Any]] = []
        for h in keti:            # 64 课经层（无等级字段，按名判）
            if isinstance(h, dict) and h.get('课体'):
                items.append({'名': h['课体'], '来源': '课体', '详情': {}})
        for name in (sp.get('匹配课格') or []):
            items.append({'名': name, '来源': '课格', '详情': (sp.get('课格详情') or {}).get(name, {})})
        for name in (bj.get('匹配变格') or [])[:40]:
            items.append({'名': name, '来源': '变格', '详情': (bj.get('变格详情') or {}).get(name, {})})

        ji, xiong = [], []
        for it in items:
            if _is_xiong(it['名'], it['详情']):
                xiong.append(it)
            elif _is_ji(it['名'], it['详情']):
                ji.append(it)
        out['吉格'] = [x['名'] for x in ji][:12]
        out['凶格'] = [x['名'] for x in xiong][:12]

        # ── 降等因子（R1~R5）──
        def down(reason):
            out['降等'].append(reason)

        # R1 变格／缺陷压正格
        for x in items:
            n = x['名']
            if '失明' in n:
                down('R1 变格：%s（正格之变，优先于本格吉论）' % n)
            elif n in ('不备', '别责', '八专') or '不备' in n:
                down('R1 课体缺陷：%s（四课不备，吉课减等）' % n)
        # R2 生克日干优先（上 L2568）
        if chu and gan:
            cwx, gwx = ZHI_WX.get(chu, ''), GAN_WX.get(gan, '')
            if cwx and gwx and WX_KE.get(cwx, '') == gwx:
                down('R2 用神%s克日干%s：虽吉将%s亦为凶（上L2568）' % (chu, gan, chu_tj or '—'))
            elif cwx and gwx and WX_SHENG.get(cwx, '') == gwx:
                out['理由'].append('用神%s生日干%s：虽凶将亦为吉（上L2568）' % (chu, gan))
        # R3 旺囚裁定（中 L3462）
        yue_jian = env.get('yue_zhi', '') or env.get('yue_jian', '')
        if chu_tj and yue_jian:
            ywx = ZHI_WX.get(yue_jian, '')
            cwx = ZHI_WX.get(chu, '')
            wang = bool(cwx and ywx and (cwx == ywx or WX_SHENG.get(ywx, '') == cwx))
            if chu_tj in JI_JIANG and not wang:
                down('R3 吉将%s乘囚休气：不为吉（中L3462）' % chu_tj)
            elif chu_tj in XIONG_JIANG and wang:
                out['理由'].append('凶将%s乘旺相气：不为凶（中L3462）' % chu_tj)
        # R4 空亡减半（上 L2637）
        if chu and chu in kong:
            down('R4 用神%s落旬空：吉减半（上L2637）' % chu)
        # R5 煞压吉格（下 L3544 例）
        for luo in (ss.get('落点') or []):
            if luo.get('煞') in ('死气', '死神', '天鬼', '病符'):
                down('R5 %s%s在%s：吉不为吉（下L3544 例）'
                     % (luo['煞'], luo['支'], '、'.join(luo['位置'])))

        # ── 裁定主格 ──
        if xiong:
            # R6：凶格中优先取与初传相关 / 名含「失明」者
            xiong_sorted = sorted(xiong, key=lambda x: (0 if '失明' in x['名'] else 1,
                                                        len(x['名'])))
            out['主格'] = xiong_sorted[0]['名']
            out['主格性质'] = '凶'
        elif ji:
            out['主格'] = ji[0]['名']
            out['主格性质'] = '吉' if not out['降等'] else '吉而受制'
        else:
            out['主格'] = items[0]['名'] if items else ''
            out['主格性质'] = '平'

        if out['降等'] and out['主格性质'] == '吉而受制':
            out['理由'].append('吉格并列而受降等因子压制 ⇒ 主格「%s」不作纯吉论' % out['主格'])

        # ── 数目（洛书本数；评疏「寅数七」同体系）──
        if chu:
            out['数目'] = {'用神': chu, '本数': ZHI_SHU.get(chu, 0),
                           '参考': '评疏以用神支数论家口／人数（如寅数七＝七口）'}
        # ── 阳刃计数（评疏「中、末、日上三个羊刃杀」）──
        yr = YANG_REN.get(gan, '')
        if yr:
            pos = [('初传', sc[0] if len(sc) > 0 else ''),
                   ('中传', sc[1] if len(sc) > 1 else ''),
                   ('末传', sc[2] if len(sc) > 2 else ''),
                   ('干上', env.get('gan_shang', '')),
                   ('支上', env.get('zhi_shang', ''))]
            hit = [p for p, v in pos if v == yr]
            out['羊刃'] = {'支': yr, '位置': hit, '计数': len(hit),
                           '参考': '评疏以课传阳刃处数论伤亡人数（如三处＝三人）'}
        # ── 倾向 ──
        if out['主格性质'] == '凶':
            out['倾向'] = '凶'
        elif out['主格性质'] == '吉而受制':
            out['倾向'] = '先吉后阻' if len(out['降等']) <= 2 else '凶'
        elif out['主格性质'] == '吉':
            out['倾向'] = '吉'
        else:
            out['倾向'] = '平'
        return out
    except Exception as e:                       # 🔴 裁定层异常绝不外溢
        out['error'] = str(e)
        return out
