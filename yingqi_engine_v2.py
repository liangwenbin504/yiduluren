# -*- coding: utf-8 -*-
"""应期增强引擎 v2（2026-08-20）——疏正43案回测归纳：古籍应期主流是"干支年/干支日"，
非仅"到月"。四法补强（全部标出处，叙事层不参与评分）：
  ① 旬空填实日（精确到日）——知识库 YQ_05"空亡填实/冲合"
  ② 三传合冲日（精确到日）——知识库 YQ_03"三传合住冲日方动；三传相冲合日方住"
  ③ 太岁冲合年（精确到年）——疏正25案干支年实例（"至辛亥年十月方得身动"）
  ④ 类神速迟定性——知识库 YQ_04"类神旺相应期月内/休囚月后/死绝年外"、YQ_05"临初传速/中传中/末传迟"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_ZHI = '子丑寅卯辰巳午未申酉戌亥'
_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
          '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
_LIUHE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
          '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
_SANHE = ({'申', '子', '辰'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'亥', '卯', '未'})
WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
      '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}


def _xunkong(rg, rz):
    """日干支 → 旬空两支。"""
    g = '甲乙丙丁戊己庚辛壬癸'.index(rg)
    z = _ZHI.index(rz)
    shou = (z - g) % 12
    return {_ZHI[(shou + 10) % 12], _ZHI[(shou + 11) % 12]}


def fa_xunkong_tianshi(rg, rz, sanchuan):
    """① 旬空填实日：旬空两支，填实（值日）或冲空（冲动）之日应。"""
    if rg not in '甲乙丙丁戊己庚辛壬癸' or rz not in _ZHI:
        return ''
    kw = _xunkong(rg, rz)
    sc = set(z for z in sanchuan if z)
    lines = []
    for k in sorted(kw):
        if k in sc:
            lines.append(f'旬空{k}入传：填实值{k}之日、冲空值{_CHONG[k]}之日为应')
        else:
            lines.append(f'旬空{k}未现：填实值{k}之日应，冲动值{_CHONG[k]}之日应')
    if not lines:
        return ''
    return '旬空填实法：' + '；'.join(lines) + '（《壬归》"空亡填实/冲合"；疏正例"果于乙卯日"即填实之应）'


def fa_sanchuan_hechong(rg, rz, sanchuan):
    """② 三传合冲日：三传成三合局→冲日支之日方动；三传含冲日支→合日支之日方住。"""
    if rz not in _ZHI or len(sanchuan) < 3:
        return ''
    sc = [z for z in sanchuan if z]
    if len(sc) < 3:
        return ''
    sc_set = set(sc)
    chong_rz = _CHONG.get(rz, '')
    if any(sc_set == s for s in _SANHE):
        return f'三传合住（{"".join(sorted(sc_set))}局）：冲{rz}（值{chong_rz}）之日方动（《壬归》"三传合住，冲日方动"）'
    if chong_rz and chong_rz in sc_set:
        return f'三传见冲{rz}（{chong_rz}）：合{rz}（值{_LIUHE.get(rz, "")}）之日方住（《壬归》"三传相冲，合日方住"）'
    return ''


def infer_sex(text: str) -> str:
    """性别从求测人身份推断（古籍惯例：看求测何事即知男女）。
    占妻/妾/妇/室→男（为己测妻）；占夫/婿→女；功名仕宦科举→男（古代皆男子为之）。
    文本不明 → ''（行年不启用，不臆造）。"""
    t = str(text or '')
    if any(k in t for k in ('妻', '妾', '妇', '婢', '室')):
        return '男'
    if any(k in t for k in ('夫', '婿', '郎君')):
        return '女'
    if any(k in t for k in ('官', '仕', '任', '赴任', '差委', '科', '试', '举')):
        return '男'
    return ''


def xing_nian_zhen(ben_ming_zhi: str, age: int, sex: str) -> str:
    """真行年：男命一岁起丙寅顺数（寅顺推 age-1）；女命一岁起壬申逆行（申逆推 age-1）。
    《六壬大全》行年例："男一岁起丙寅，女一岁起壬申"。"""
    if ben_ming_zhi not in _ZHI or not age or age < 1 or sex not in ('男', '女'):
        return ''
    if sex == '男':
        return _ZHI[(_ZHI.index('寅') + (age - 1)) % 12]
    return _ZHI[(_ZHI.index('申') - (age - 1)) % 12]


def fa_taisui_chonghe(tai_sui_zhi, ben_ming_zhi='', ben_ming_age=0, sex='', text=''):
    """③ 太岁/行年冲合年：当年（太岁）应；冲太岁之年应动；真行年（男女分起）冲合之年应。"""
    if tai_sui_zhi not in _ZHI:
        return ''
    lines = [f'太岁{tai_sui_zhi}：当年应']
    ct = _CHONG.get(tai_sui_zhi)
    if ct:
        lines.append(f'冲太岁（值{ct}）之年应动')
    if ben_ming_zhi in _ZHI:
        try:
            _age = int(ben_ming_age)
        except Exception:
            _age = 0
        _sex = sex if sex in ('男', '女') else infer_sex(text)
        if _age and _age >= 1 and _sex:
            xn = xing_nian_zhen(ben_ming_zhi, _age, _sex)
            if xn:
                lines.append(f'行年{xn}（{_sex}命{_age}岁起{("丙寅顺数" if _sex == "男" else "壬申逆行")}）：值{xn}年应，冲{_CHONG.get(xn, "")}之年应动')
    return '太岁行年法：' + '；'.join(lines) + '（疏正例"至辛亥年十月方得身动"——冲合填实之年）'


def fa_leishen_suchi(sanchuan, wangshuai_fn=None, yuejiang=''):
    """④ 类神速迟定性：初传旺相→速（月内）；休囚→中（月后）；死绝→迟（年外）。
    初传为事发端，其旺衰定迟速（《壬归》"类神旺相则速，休囚则迟"）。"""
    if not sanchuan or not sanchuan[0]:
        return ''
    chu = sanchuan[0]
    ws = ''
    if wangshuai_fn and WX.get(chu):
        try:
            ws = wangshuai_fn(WX[chu], yuejiang) if wangshuai_fn.__code__.co_argcount >= 2 else wangshuai_fn(WX[chu])
        except Exception:
            try:
                ws = wangshuai_fn(chu)
            except Exception:
                ws = ''
    if ws in ('旺', '相'):
        speed = '初传' + chu + '旺相：事应速，月内或近期'
    elif ws in ('死',):
        speed = '初传' + chu + '死绝：事应迟，年外或无期'
    elif ws in ('休', '囚'):
        speed = '初传' + chu + '休囚：事应中，月后'
    else:
        return ''
    return speed + '（《六壬大全·旺相休囚死》"类神旺相应期在月内；休囚月后；死绝年外"）'


def fa_wangdao_shichen(zhanlei, sanchuan, leishen='', sike=None, tdp=None):
    """⑤ 亡盗/失物时辰+方位级应期：类神临四孟→当日速获；临四仲→数日中获；临四季→旬月迟获。
    出处：疏正亡盗案"申牌后于厕坑左右寻得"（庚辰日，类神申为孟支，当日申时寻得）、
    "炉下寻见"（己丑）、"东方园内羊群中寻见"（己卯）——失物以类神临孟仲季断速迟。"""
    if str(zhanlei or '') not in ('亡盗', '六畜走失', '走失', '失物', '贼盗'):
        return ''
    ys = str(leishen or '')
    if ys not in _ZHI and sanchuan:
        ys = str(sanchuan[0] or '')
    if ys not in _ZHI:
        return ''
    if ys in ('寅', '申', '巳', '亥'):
        spd = f'失物应期：类神{ys}临四孟，主当日速获（疏正亡盗例庚辰日类神申"申牌后于厕坑左右寻得"——孟支当日应）'
    elif ys in ('子', '午', '卯', '酉'):
        spd = f'失物应期：类神{ys}临四仲，主数日方获'
    else:
        spd = f'失物应期：类神{ys}临四季，主旬月迟获'
    # 方位联动（fangwei 引擎：类神加临方位）
    try:
        from fangwei_engine_v7 import leishen_jia_fang
        r = leishen_jia_fang(ys, sike, tdp, sanchuan)
        fw = (r or {}).get('叙事') or (r or {}).get('方位') or ''
        if fw:
            spd += '；寻方：' + str(fw)[:60]
    except Exception:
        pass
    return spd


def _xun_shouwei(rg, rz):
    """日干支所在旬：返回（旬首支, 旬尾支）。甲子旬→(子,亥)；甲戌旬→(戌,酉)…"""
    if rg not in '甲乙丙丁戊己庚辛壬癸' or rz not in _ZHI:
        return '', ''
    shou_i = (_ZHI.index(rz) - '甲乙丙丁戊己庚辛壬癸'.index(rg)) % 12
    return _ZHI[shou_i], _ZHI[(shou_i + 9) % 12]


def _gan_zhi_shang(sike):
    """四课 → (干上神, 支上神)。兼容 tuple/dict 两种四课格式。"""
    gan = zhi = ''
    for i, k in enumerate(sike or []):
        us = ''
        if isinstance(k, (list, tuple)) and len(k) >= 2:
            us = str(k[1])
        elif isinstance(k, dict):
            us = str(k.get('上神', ''))
        if i == 0:
            gan = us
        if i == 2:
            zhi = us
    return gan, zhi


def fa_xun_ji(rg, rz, sanchuan, sike=None):
    """⑥ 旬级应期（疏正18案旬语境归纳）：
    ① 旬空出旬：旬内空亡不应，出旬填实/冲动方应；
    ② 干上旬尾+支上旬首 = 一旬周遍格（周而复始，首起尾止）；
    ③ 旬尾加旬首 = 闭口（旬内难言难成，出旬方动）。
    出处：疏正例"甲子旬亥戌空亡…虚名文学""甲申旬未乃空亡，渐次脱去"
    "旬首加旬尾，乃周而复始格""干上旬尾支上旬首，为一旬周遍格，来了又去"
    "甲申旬末，故闭口不能言也""旬末加旬首，名闭口，仕途不通"。"""
    if rg not in '甲乙丙丁戊己庚辛壬癸' or rz not in _ZHI:
        return ''
    shou, wei = _xun_shouwei(rg, rz)
    if not shou:
        return ''
    lines = []
    # ① 旬空出旬
    kw = sorted(_xunkong(rg, rz))
    if kw:
        lines.append('旬空出旬：旬空%s本旬不应；出旬后值%s之日填实而应，冲动值%s之日亦应（疏正例"甲申旬未乃空亡，渐次脱去"）'
                     % ('、'.join(kw), '、'.join(kw), '、'.join(_CHONG.get(x, '') for x in kw)))
    # ②③ 干上旬尾/支上旬首
    gan_s, zhi_s = _gan_zhi_shang(sike)
    if gan_s == wei and zhi_s == shou:
        lines.append(f'干上旬尾{wei}加支上旬首{shou}：一旬周遍格，周而复始——应于值{shou}（旬首）之期起、值{wei}（旬尾）之期止；'
                     f'兼旬尾加旬首闭口之象，旬内难言难成，出旬方动（疏正例"干上旬尾支上旬首，一旬周遍格，来了又去"、"旬末加旬首，名闭口"）')
    elif gan_s == wei:
        lines.append(f'干上旬尾{wei}：事近旬终，值{wei}之日应止，出旬方启新事')
    elif zhi_s == shou:
        lines.append(f'支上旬首{shou}：事起旬首，值{shou}之日应起')
    return '旬级应期法：' + '；'.join(lines)


def yingqi_v2(ri_gan, ri_zhi, sanchuan, tiandi_pan=None, si_ke=None, shichen='',
              tai_sui_zhi='', zhanlei='其他', zishu='', ben_ming_zhi='', ben_ming_age=0,
              sex='', text='', leishen='', wangshuai_fn=None, yuejiang='') -> str:
    """应期增强总输出：原三法（支数/月建/太岁临身）由调用方 get_yingqi_unified 提供；
    本函数追加四法块（填实日/合冲日/太岁冲合年/类神速迟）。返回追加文本。"""
    blocks = []
    t1 = fa_xunkong_tianshi(ri_gan, ri_zhi, sanchuan)
    if t1:
        blocks.append(t1)
    t2 = fa_sanchuan_hechong(ri_gan, ri_zhi, sanchuan)
    if t2:
        blocks.append(t2)
    t3 = fa_taisui_chonghe(tai_sui_zhi, ben_ming_zhi, ben_ming_age, sex=sex, text=text)
    if t3:
        blocks.append(t3)
    t4 = fa_leishen_suchi(sanchuan, wangshuai_fn, yuejiang)
    if t4:
        blocks.append(t4)
    t5 = fa_wangdao_shichen(zhanlei, sanchuan, leishen=leishen, sike=si_ke, tdp=tiandi_pan)
    if t5:
        blocks.append(t5)
    t6 = fa_xun_ji(ri_gan, ri_zhi, sanchuan, sike=si_ke)
    if t6:
        blocks.append(t6)
    return '\n'.join(blocks)


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # 自检：丙寅日午将午时（FB-002 提车课，伏吟）
    sc = ['巳', '申', '寅']
    print('① 旬空填实:', fa_xunkong_tianshi('丙', '寅', sc))
    print('② 合冲日:', fa_sanchuan_hechong('丙', '寅', sc))
    print('③ 太岁行年:', fa_taisui_chonghe('午', '甲子', 42))
    from engine.liuchen_shensha import wang_shuai
    print('④ 类神速迟:', fa_leishen_suchi(sc, wang_shuai, '午'))
