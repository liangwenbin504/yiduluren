#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十二建星模块 (engine/jianxing.py)
=================================
【用户拍板 2026-08-25】十二建星（建除满平定执破危成收开闭）进批语叙事，不参与评分。

固定口诀（网上通例、《协纪辨方书》口径）：
  顺序：建 除 满 平 定 执 破 危 成 收 开 闭
  黄黑道：建满平收黑，除危定执黄，成开皆可用，闭破不相当
  算法：按月建起建——月建地支起"建"，逐日顺推一位。

用途（用户确认）：只进批语叙事，不加减分。
  四态叙事：课吉+黄道=吉上加吉 / 课凶+黑道=凶上加凶 /
            课吉+黑道=吉上减吉 / 课凶+黄道=凶上减凶

用法：
    from engine.jianxing import get_jianxing
    jx = get_jianxing(month_zhi='寅', day_zhi='午')   # 寅月午日
    # jx = {'name': '定', 'huang_dao': True, 'level': '吉', 'desc': '定日宜冠带、安床、定盟', 'idx': 4}
"""

# 十二建星固定顺序
JIANXING = ['建', '除', '满', '平', '定', '执', '破', '危', '成', '收', '开', '闭']

# 黄道/黑道（口诀：建满平收黑，除危定执黄，成开皆可用，闭破不相当）
HUANG_DAO = {'除', '危', '定', '执', '成', '开'}     # 黄道吉
HEI_DAO = {'建', '满', '平', '收', '闭', '破'}       # 黑道凶

# 吉凶倾向 + 宜忌歌（网上通例）
JX_INFO = {
    '建': {'level': '凶', 'desc': '建日诸事不宜，动土出行均忌（建之始）'},
    '除': {'level': '吉', 'desc': '除旧迎新，宜扫舍、沐浴、去灾'},
    '满': {'level': '凶', 'desc': '满日祭祀尚可，嫁娶开仓多忌'},
    '平': {'level': '平', 'desc': '平日凡事平平，宜平涂泥、修饰垣墙'},
    '定': {'level': '吉', 'desc': '定日宜冠带、安床、定盟、纳采'},
    '执': {'level': '吉', 'desc': '执日宜捕捉、断狱，忌嫁娶出行'},
    '破': {'level': '大凶', 'desc': '破日诸事不宜，宜破屋坏垣'},
    '危': {'level': '吉', 'desc': '危日宜安床、祈福、祭祀，忌登高'},
    '成': {'level': '吉', 'desc': '成日宜开市、嫁娶、入学、交易（成就）'},
    '收': {'level': '吉', 'desc': '收日宜纳财、收账，忌安葬、开市'},
    '开': {'level': '吉', 'desc': '开日宜开业、开市、出行（开张）'},
    '闭': {'level': '凶', 'desc': '闭日宜筑堤、塞穴、断狱，诸事不宜'},
}

_ZHI = '子丑寅卯辰巳午未申酉戌亥'


def get_jianxing(month_zhi='', day_zhi=''):
    """
    计算某日的十二建星（月建起建）。

    参数：
        month_zhi: 月建地支（如 '寅'=正月；也可传月柱如 '戊寅' 取支）
        day_zhi:   日支（如 '午'；也可传日柱如 '甲午' 取支）

    返回：
        {'name': 建星名, 'idx': 0-11, 'huang_dao': bool, 'level': 吉凶,
         'desc': 宜忌歌, 'pos_from_month': 距月建位数}
    """
    if len(month_zhi) >= 2 and month_zhi[0] in '甲乙丙丁戊己庚辛壬癸':
        month_zhi = month_zhi[1]
    if len(day_zhi) >= 2 and day_zhi[0] in '甲乙丙丁戊己庚辛壬癸':
        day_zhi = day_zhi[1]
    if month_zhi not in _ZHI or day_zhi not in _ZHI:
        return {'name': '', 'idx': -1, 'huang_dao': False, 'level': '', 'desc': '', 'pos_from_month': -1}
    m_i = _ZHI.index(month_zhi)
    d_i = _ZHI.index(day_zhi)
    # 月建起"建"：月建支 idx=0，日支相对位移 = (d_i - m_i) % 12
    pos = (d_i - m_i) % 12
    name = JIANXING[pos]
    return {
        'name': name,
        'idx': pos,
        'huang_dao': name in HUANG_DAO,
        'level': JX_INFO[name]['level'],
        'desc': JX_INFO[name]['desc'],
        'pos_from_month': pos,
    }


# ── 地支类象（传统定式 + 赵林声《北大课例》现代实战类象，2026-08-25）──
# 完整版见 docs/大六壬类象总表.md；此处为叙事用精炼版。现代延伸留待探索，不编造。
ZHI_LEIXIANG = {
    '子': '水、妇女、暗昧、井、小孩、取款机小片',
    '丑': '田园、坟墓、牛、迟滞、腹、金库、部队',
    '寅': '山林、公门、虎、文书、文化文艺、儿子、树木、猫、鬼门、飞机',
    '卯': '舟车、门户、药、小孩、手、艺术品、车、手机、桃花',
    '辰': '水库、龙、争斗、网罗、墙、网络、警察、块状',
    '巳': '炉灶、蛇、惊扰、驿马、门面店铺、热水管、吊客、天医针灸',
    '午': '文书、马、光明、酒食、心脏、眼睛、文明、脸面、情人、桃花',
    '未': '田园、羊、酒食、眷属、鬼、财、土特产、名贵',
    '申': '道路、神佛、传送、行人、飞机、警察、针灸、剑、父母职业',
    '酉': '刀剑、门户、鸡、金银、咽喉、贵重物件、玉器酒具、兑口破骂',
    '戌': '坟墓、犬、刑狱、牢狱、网络、陶瓷、部队、财库银行',
    '亥': '小孩、水、江海、沐浴、酒、天门、房屋、神佛用水',
}
# 天将类象（传统定式 + 邵老实战）
TJ_LEIXIANG = {
    '贵人': '尊长、官贵、提携、贵重、国家企业',
    '螣蛇': '惊扰、怪异、纠缠、弯曲、图腾、眼睛、神经',
    '朱雀': '文书、口舌、信息、电话、银行卡、标签',
    '六合': '和合、交易、婚姻、多、一整套、小孩',
    '勾陈': '田土、争斗、迟滞、警察交警、打斗、带把',
    '青龙': '财帛、喜庆、文书、纸钱煞、飞机、文化文艺',
    '天空': '虚诈、空亡、奴婢、中间空',
    '白虎': '道路、血光、凶丧、病、催官使者、老虎机',
    '太常': '酒食、宴席、衣物、标签、经常条状长物',
    '玄武': '盗贼、暗昧、失脱、鬼神、下贱、玄学',
    '太阴': '神佛、阴私、妇女、神经、玉器、藏匿',
    '天后': '恩泽、婚姻、妇女、国家机关',
}


def _yingshi_small(level, name):
    """黑道日+吉课的琐碎应事提示（邵老断法：凶应小事不伤大局）。"""
    if name == '破':
        return '主琐碎破耗之失——如汤水洒溅、器物损毁、小儿玩水湿衣之属，不伤大局'
    if name == '闭':
        return '主闭藏阻滞之微——如门户偶闭、道路暂阻、往来小滞，不碍大事'
    if name == '建':
        return '主创建初起之扰——如事之始有小挫、布置暂未妥帖，无碍成就'
    if name == '满':
        return '主盈满小溢之失——如饮食丰盛而有小损、器物满溢而微失，无伤大体'
    if name == '平':
        return '主平常无奇之应——事体平平，吉凶皆小，无大波澜'
    if name == '收':
        return '主收敛小取之应——如收付稍滞、财物小有出入，不损大局'
    return '主琐碎小事之应，不伤大局'


def jianxing_narrative(jx, course_jixiong='吉', sanchuan=None, tianjiang=None):
    """
    生成批语叙事（四态 + 黑道吉课的琐碎应事提示，邵老断法）。

    参数：
        jx: get_jianxing() 返回值
        course_jixiong: 课体吉凶倾向（'吉'/'凶'/'平'）
        sanchuan: 三传地支列表（可选，用于类象提示）
        tianjiang: 三传天将列表（可选，用于类象提示）

    返回叙事句。
    """
    if not jx or not jx.get('name'):
        return ''
    name = jx['name']
    parts = []
    if jx['huang_dao']:
        dao = '黄道吉日'
        if course_jixiong == '吉':
            tail = '吉上加吉'
        elif course_jixiong == '凶':
            tail = '凶上减凶'
        else:
            tail = '黄道增吉'
        parts.append(f'本日为建星·{name}日（{dao}），{tail}')
    else:
        dao = '黑道凶日'
        if course_jixiong == '吉':
            tail = '吉上减吉'
            # 邵老断法：黑道+吉课 → 凶应小事不伤大局
            parts.append(f'本日为建星·{name}日（{dao}），{tail}')
            small = _yingshi_small(jx.get('level', ''), name)
            parts.append(f'然课体清明不损大事，{small}')
        elif course_jixiong == '凶':
            tail = '凶上加凶'
            parts.append(f'本日为建星·{name}日（{dao}），{tail}')
        else:
            tail = '黑道减吉'
            parts.append(f'本日为建星·{name}日（{dao}），{tail}')
    # 类象提示（可选，不编造现代延伸；仅列传统类象）
    if sanchuan and tianjiang and len(sanchuan) == len(tianjiang):
        imgs = []
        for z, tj in zip(sanchuan, tianjiang):
            zx = ZHI_LEIXIANG.get(z, '')
            tx = TJ_LEIXIANG.get(tj, '')
            if zx and tx:
                imgs.append(f'{z}{tj}（{zx}·{tx}）')
            elif zx:
                imgs.append(f'{z}（{zx}）')
        if imgs and len(imgs) <= 3:
            parts.append('三传类象：' + '、'.join(imgs))
    return '；'.join(parts)


if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("== jianxing 自测 ==")
    # 寅月各日
    for dz in '子丑寅卯辰巳午未申酉戌亥':
        jx = get_jianxing('寅', dz)
        print(f"寅月{dz}日 → {jx['name']}日({jx['level']}) {'黄' if jx['huang_dao'] else '黑'}")
    print()
    # 叙事测试（含三传类象）
    cases = [
        (get_jianxing('寅', '寅'), '吉', ['巳', '申', '亥'], ['贵人', '太阴', '六合']),  # 建日+吉课
        (get_jianxing('寅', '申'), '吉', ['巳', '申', '亥'], ['贵人', '太阴', '六合']),  # 破日+吉课（邵老案例）
        (get_jianxing('寅', '申'), '凶', ['巳', '申', '亥'], ['白虎', '玄武', '螣蛇']),  # 破日+凶课
    ]
    for jx, gx, sc, tj in cases:
        print(jianxing_narrative(jx, gx, sc, tj))
        print()
