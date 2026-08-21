#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特殊课格检测引擎 v1.0
检测依赖天将/天地盘/贵人的15种高级课格模式。

盘面课格: 贵登天门、魁度天门、罡塞鬼户、贵塞鬼户、轩盖课
天将课格: 两蛇夹墓、蛇化龙、龙化蛇、虎临干鬼、龙加生气、龙虎交驰、初遭夹克、将逢内战
综合课格: 解离课、游子课

创建: 2026-07-29 | 来源: 毕法赋100法+六壬大全+六壬断案秘诀
"""

from typing import List, Dict, Optional
from .bifa_detector import (
    GAN_WUXING, ZHI_WUXING, MU, GAN_JIGONG,
    _is_gan_ghost, _is_gan_parent,
    DIZHI_ORDER,
)
from .bifa_detector import TIANJIANG_WUXING, GUIREN_MAP  # 复用已有常量


# 五行生克
WX_KE = {'木':'土','火':'金','土':'水','金':'木','水':'火'}

# 六害（彼此猜忌害相随/交车害/墓门开等）
LIU_HAI = {'子':'未','未':'子','丑':'午','午':'丑','寅':'巳','巳':'寅',
           '卯':'辰','辰':'卯','申':'亥','亥':'申','酉':'戌','戌':'酉'}

# 六刑（寅巳申无恩刑、丑戌未恃势刑、子卯无礼刑、辰午酉亥自刑）
XING = {
    '寅': ['巳'], '巳': ['申'], '申': ['寅'],
    '丑': ['戌'], '戌': ['未'], '未': ['丑'],
    '子': ['卯'], '卯': ['子'],
    '辰': ['辰'], '午': ['午'], '酉': ['酉'], '亥': ['亥'],
}

# 吉将（铸印乘轩/舟楫等变格用）
JI_JIANG = {'贵人', '青龙', '太常', '六合', '太阴', '天后'}

# 四季旺相休囚死（乘轩落马·身弱人衰用）
WANG_WX = {'春': '木', '夏': '火', '秋': '金', '冬': '水'}   # 当季旺
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 旺所生=相
SI_WX = {'春': '土', '夏': '金', '秋': '木', '冬': '火'}      # 死气（通解上L5221：春土死夏金死秋木死冬火死）
SANG_CHE = {'春': '酉', '夏': '子', '秋': '卯', '冬': '午'}   # 丧车煞（通解下L13208：春酉夏子秋卯冬午）


def _is_shuai(wx: str, season: str) -> bool:
    """某五行是否「衰」（休囚死：非旺非相）"""
    w = WANG_WX.get(season, '')
    if not w:
        return False
    if wx == w:
        return False
    if wx == WX_SHENG.get(w, ''):
        return False
    return True


def _get_sheng_qi(yuejiang: str) -> str:
    """月将本位即生气"""
    yj = str(yuejiang).replace('将','') if yuejiang else ''
    return yj if yj in DIZHI_ORDER else ''


class SpecialKegeDetector:
    """特殊课格检测器 — 15种高级课格"""

    def __init__(self):
        self.detected_kege: List[Dict] = []

    def detect(self,
               sanchuan_dizhi: List[str],
               ri_gan: str,
               ganzhi: str = '',
               tiandi_pan: Optional[Dict] = None,
               tian_jiang: Optional[Dict] = None,
               gan_shang_shen: str = '',
               zhi_shang_shen: str = '',
               yuejiang: str = '',
               season: str = '',
               kongwang: tuple = ('', ''),
               ben_ming_zhi: str = '',
               xing_nian: str = '') -> Dict:
        """
        主入口。tiandi_pan格式: {地盘支: 天盘支}
        tian_jiang格式: {地支: 天将名} 如 {'子':'贵人','丑':'螣蛇',...}
        """
        self.detected_kege = []
        sc = sanchuan_dizhi if sanchuan_dizhi else []

        # 盘面课格 (需tiandi_pan)
        if tiandi_pan:
            self._guide_tianmen(ri_gan, sc, tiandi_pan)
            self._kuidu_tianmen(sc, tiandi_pan)
            self._gangsai_guihu(tiandi_pan)
            self._gui_sai_guihu(ri_gan, tiandi_pan)
            self._xuangai(sc, tiandi_pan)
            self._chengxuan_luoma(sc, tian_jiang, kongwang, ri_gan, ganzhi, season, ben_ming_zhi, xing_nian)

        # 天将课格 (需tian_jiang)
        if tian_jiang:
            self._ls_jiamu(ri_gan, gan_shang_shen, zhi_shang_shen, tian_jiang)
            self._she_hua_long(sc, tian_jiang)
            self._long_hua_she(sc, tian_jiang)
            self._hu_lin_gangui(ri_gan, sc, gan_shang_shen, zhi_shang_shen, tian_jiang)
            self._long_jia_shengqi(ri_gan, sc, gan_shang_shen, zhi_shang_shen, tian_jiang, yuejiang)
            self._longhu_jiaochi(sc, tian_jiang)
            self._chuzao_jiake(sc, tian_jiang, tiandi_pan)
            self._jiangfeng_neizhan(sc, tian_jiang)

        # 综合课格
        self._jieli(ri_gan, ganzhi, gan_shang_shen, zhi_shang_shen)
        _rz = ganzhi[1] if len(ganzhi) >= 2 else ''
        self._youzi(sc, ri_gan, _rz, ganzhi)

        # 64课/毕法赋变格（从属格，2026-08-16 补）
        self._xiuluan(sc, kongwang)                                       # 朽木难雕/伤轮
        self._poyin(sc, kongwang)                                         # 破印损模
        self._zhuyin_chengxuan(sc, tian_jiang)                            # 铸印乘轩
        self._jiaoche_xing(ri_gan, ganzhi, gan_shang_shen, zhi_shang_shen)   # 交车刑
        self._jiaoche_hai(ri_gan, ganzhi, gan_shang_shen, zhi_shang_shen)    # 交车害
        self._mumen_kai(ri_gan, ganzhi, zhi_shang_shen, tian_jiang)          # 墓门开
        self._biandi_guiren(ri_gan, sc, gan_shang_shen, zhi_shang_shen, tian_jiang)  # 遍地贵人
        self._guiren_rigui(ri_gan, sc, gan_shang_shen, zhi_shang_shen, tian_jiang)   # 贵人作日鬼
        self._zhen_jieli(ri_gan, ganzhi, gan_shang_shen, zhi_shang_shen)     # 真解离

        return self._build_result()

    # ════════════════ 盘面课格 ════════════════

    def _guide_tianmen(self, ri_gan, sc, tp):
        """贵登天门: 贵人加亥(天门)"""
        if not ri_gan: return
        pair = GUIREN_MAP.get(ri_gan)
        if not pair: return
        t = tp.get('亥','')
        if t in pair:
            gtype = '昼贵' if t == pair[0] else '夜贵'
            self._add('贵登天门','大吉',f'{gtype}{t}加天门亥上，无往不利','涨',3)

    def _kuidu_tianmen(self, sc, tp):
        """魁度天门: 戌加亥为初传"""
        if len(sc)<1 or tp.get('亥','')!='戌' or sc[0]!='戌': return
        self._add('魁度天门','凶','天魁戌加天门亥发用，百事阻隔','跌',2)

    def _gangsai_guihu(self, tp):
        """罡塞鬼户: 辰加寅"""
        if tp.get('寅','')=='辰':
            self._add('罡塞鬼户','大吉','天罡辰塞鬼户寅，任谋为必利','涨',2)

    def _gui_sai_guihu(self, ri_gan, tp):
        """贵塞鬼户: 贵人加寅"""
        if not ri_gan: return
        gui = set()
        for p in GUIREN_MAP.values(): gui.update(p)
        t = tp.get('寅','')
        if t in gui:
            self._add('贵塞鬼户','吉',f'贵人{t}塞鬼户寅，宜动宜迁','涨',1)

    def _xuangai(self, sc, tp):
        """轩盖课: 午加卯发用"""
        if len(sc)<1 or tp.get('卯','')!='午' or sc[0]!='午': return
        self._add('轩盖课','吉','午加卯发用，如车轩盖，声名远播','涨',2)

    def _chengxuan_luoma(self, sc, tj, kongwang, ri_gan, ganzhi, season, ben_ming_zhi, xing_nian):
        """乘轩落马（轩盖落马）: 轩盖课（三传午卯子，午加卯发用）而四条任一——
        ①三传乘白虎/螣蛇，克年命日辰；②卯空亡；③卯作丧车煞（秋）；④身弱人衰。
        通解上L7609：「三传带杀，乘蛇虎死气，克年命日辰，或空亡，或卯作丧车…身弱人衰，则为轩盖落马之象」。"""
        if len(sc) < 3:
            return
        if sc[0] != '午' or set(sc) != {'午', '卯', '子'}:
            return
        rz = ganzhi[1] if ganzhi and len(ganzhi) >= 2 else ''
        nian_ming = [z for z in (ben_ming_zhi, xing_nian) if z]
        reasons = []

        # ① 三传乘白虎/螣蛇，克年命日辰（死气作增强描述）
        for z in sc:
            j = (tj or {}).get(z, '')
            if j not in ('白虎', '螣蛇'):
                continue
            zwx = ZHI_WUXING.get(z, '')
            ke_nm = any(nm and WX_KE.get(zwx, '') == ZHI_WUXING.get(nm, '') for nm in nian_ming)
            ke_gan = WX_KE.get(zwx, '') == GAN_WUXING.get(ri_gan, '')
            ke_zhi = bool(rz) and WX_KE.get(zwx, '') == ZHI_WUXING.get(rz, '')
            if ke_nm or ke_gan or ke_zhi:
                siqi = '死气' if (SI_WX.get(season, '') and zwx == SI_WX.get(season, '')) else ''
                reasons.append(f'三传{z}乘{j}{siqi}克年命日辰')
                break

        # ② 卯空亡
        mao_kong = bool(kongwang and kongwang[0] and '卯' in kongwang)
        if mao_kong:
            reasons.append('卯空亡')

        # ③ 卯作丧车煞（丧车=春酉夏子秋卯冬午，秋占卯为丧车）
        if SANG_CHE.get(season, '') == '卯':
            reasons.append('卯作丧车煞')

        # ④ 身弱人衰（日干衰 + 本命/行年衰）
        shen_ruo = _is_shuai(GAN_WUXING.get(ri_gan, ''), season)
        ren_shuai = any(nm and _is_shuai(ZHI_WUXING.get(nm, ''), season) for nm in nian_ming)
        if shen_ruo and ren_shuai:
            reasons.append('身弱人衰')

        if reasons:
            self._add('乘轩落马', '大凶', '轩盖课而马落（' + '、'.join(reasons) + '），乘轩落马', '跌', 3)

    # ════════════════ 天将课格 ════════════════

    def _ls_jiamu(self, ri_gan, gs, zs, tj):
        """两蛇夹墓: 墓神临干支且该位天将=螣蛇"""
        if not ri_gan or not gs or not zs: return
        gm = MU.get(ri_gan,'')
        if not gm: return
        if gs==gm and tj.get(gs,'')=='螣蛇':
            self._add('两蛇夹墓','大凶',f'干上{gs}墓神乘螣蛇，两蛇夹墓','跌',3)
        if zs==gm and tj.get(zs,'')=='螣蛇':
            self._add('两蛇夹墓','大凶',f'支上{zs}墓神乘螣蛇，两蛇夹墓','跌',3)

    def _she_hua_long(self, sc, tj):
        """蛇化龙: 初蛇末龙"""
        if len(sc)<3: return
        if tj.get(sc[0],'')=='螣蛇' and tj.get(sc[2],'')=='青龙':
            self._add('蛇化龙','吉','初蛇末龙，始凶终吉，变泰之象','涨',2)

    def _long_hua_she(self, sc, tj):
        """龙化蛇: 初龙末蛇"""
        if len(sc)<3: return
        if tj.get(sc[0],'')=='青龙' and tj.get(sc[2],'')=='螣蛇':
            self._add('龙化蛇','凶','初龙末蛇，始吉终凶','跌',2)

    def _hu_lin_gangui(self, ri_gan, sc, gs, zs, tj):
        """虎临干鬼: 白虎在日鬼之位（2026-08-21 修复：限课传六处，不再全盘扫天将）"""
        if not ri_gan: return
        for z in list(sc) + [gs, zs]:
            if z and tj.get(z, '')=='白虎' and _is_gan_ghost(ri_gan, z):
                loc = '干上' if z == gs else ('支上' if z == zs else '三传')
                self._add('虎临干鬼','凶',f'白虎临{ri_gan}日鬼{z}上（{loc}），凶速速','跌',3)
                return

    def _long_jia_shengqi(self, ri_gan, sc, gs, zs, tj, yj):
        """龙加生气: 青龙乘生干之神且作月内生气（2026-08-21 修复：限课传六处）"""
        if not ri_gan: return
        sq = _get_sheng_qi(yj)
        for z in list(sc) + [gs, zs]:
            if z and tj.get(z, '')=='青龙' and z==sq and _is_gan_parent(ri_gan, z):
                loc = '干上' if z == gs else ('支上' if z == zs else '三传')
                self._add('龙加生气','大吉',f'青龙临生气{z}生{ri_gan}干（{loc}），吉迟迟','涨',3)
                return

    def _longhu_jiaochi(self, sc, tj):
        """龙虎交驰: 青龙白虎俱入三传"""
        if len(sc)<3: return
        tjs = [tj.get(z,'') for z in sc]
        if '青龙' in tjs and '白虎' in tjs:
            self._add('龙虎交驰','震荡','青龙白虎俱入传，龙争虎斗','震荡',1)

    def _chuzao_jiake(self, sc, tj, tp):
        """初遭夹克: 初传被天将克+被地盘克"""
        if len(sc)<1: return
        c = sc[0]; cw = ZHI_WUXING.get(c,'')
        if not cw: return
        tw = TIANJIANG_WUXING.get(tj.get(c,''),'')
        tj_ke = tw and WX_KE.get(tw,'')==cw
        di_ke = False
        if tp:
            for d,t in tp.items():
                if t==c:
                    dw=ZHI_WUXING.get(d,'')
                    di_ke = dw and WX_KE.get(dw,'')==cw
                    break
        if tj_ke and di_ke:
            self._add('初遭夹克','凶',f'初传{c}天将地盘双克，不由己','跌',3)

    def _jiangfeng_neizhan(self, sc, tj):
        """将逢内战: 天将五行克所乘地支五行(仅三传中)
        只记录第一处发现的内战"""
        found = []
        for z, t in tj.items():
            if z not in sc: continue
            tw = TIANJIANG_WUXING.get(t,'')
            zw = ZHI_WUXING.get(z,'')
            if tw and zw and WX_KE.get(tw,'')==zw:
                found.append(f'{t}({tw})乘{z}({zw})')
        if found:
            self._add('将逢内战','凶',f'天将克地支：{";".join(found)}，内战所谋危','跌',2)

    # ════════════════ 综合课格 ════════════════

    def _jieli(self, ri_gan, ganzhi, gs, zs):
        """解离课: 干上神克支、支上神克干
        【BUG-FIX 2026-08-18】原方向写反（日干克支上神/日支克干上神），
        与通解 p3996/5136「干上神克支、支上神克干」相反；已纠正。"""
        if not ri_gan or not ganzhi or not gs or not zs: return
        if len(ganzhi)<2: return
        rz = ganzhi[1]  # 日支
        gw = GAN_WUXING.get(ri_gan,'')
        zw = ZHI_WUXING.get(rz,'')
        # 干上神五行克日支 + 支上神五行克日干
        gs_wx = ZHI_WUXING.get(gs,'')
        zs_wx = ZHI_WUXING.get(zs,'')
        if gs_wx and zw and WX_KE.get(gs_wx,'')==zw and zs_wx and gw and WX_KE.get(zs_wx,'')==gw:
            self._add('解离课','凶',f'干上{gs}克支{rz}，支上{zs}克干{ri_gan}，解离之象','跌',2)

    def _youzi(self, sc, ri_gan='', ri_zhi='', ganzhi=''):
        """游子课: 三传皆土(辰戌丑未)，遇旬丁/驿马/天马为用
        【BUG-FIX 2026-08-18】原判「三传皆孟(寅申巳亥)」撞玄胎课；改三传皆土后
        仍须逢丁马才算游子（案例："稼穑见旬丁为游子"、"驿马发用游子之象"、
        "天马入传课名游子"）——纯三传皆土是稼穑课，非游子。"""
        if len(sc) < 3:
            return
        if not all(z in {'辰', '戌', '丑', '未'} for z in sc):
            return
        # 旬丁 / 驿马 / 天马 任一在三传
        _has_dingma = False
        try:
            from .bifa_detector import get_ding_shen
            ding = get_ding_shen(ganzhi) if len(ganzhi) >= 2 else ''
            _has_dingma = bool(ding and ding in sc)
        except Exception:
            _has_dingma = False
        if not _has_dingma and ri_zhi:
            _ma = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
                   '亥': '巳', '卯': '巳', '未': '巳', '巳': '亥', '酉': '亥', '丑': '亥'}
            _has_dingma = _ma.get(ri_zhi, '') in sc
        if not _has_dingma:
            return
        self._add('游子课', '震荡', '三传皆土，游子奔波，行情方向不明', '震荡', 1)

    # ════════════════ 64课/毕法赋变格（从属格，2026-08-16 补）════════════════

    def _xiuluan(self, sc, kongwang):
        """朽木难雕/伤轮: 斫轮课（三传含卯）而卯（车轮）空亡"""
        if len(sc)<1 or '卯' not in sc: return
        if kongwang and kongwang[0] and '卯' in kongwang:
            self._add('朽木难雕','凶','斫轮课卯（车轮）空亡，朽木不可雕，宜改图','跌',3)

    def _poyin(self, sc, kongwang):
        """破印损模: 铸印课（三传巳戌卯）而巳（模）或戌（印）空亡"""
        if len(sc)<3 or set(sc) != {'巳','戌','卯'}: return
        if not kongwang or not kongwang[0]: return
        if '巳' in kongwang:
            self._add('破印损模','凶','铸印课巳（铸模）空亡，印破不成','跌',3)
        elif '戌' in kongwang:
            self._add('破印损模','凶','铸印课戌（印）空亡，印破不成','跌',3)

    def _zhuyin_chengxuan(self, sc, tj):
        """铸印乘轩: 铸印课（三传巳戌卯）而卯（车轮）乘吉将"""
        if len(sc)<3 or set(sc) != {'巳','戌','卯'}: return
        if tj and tj.get('卯','') in JI_JIANG:
            self._add('铸印乘轩','上吉','铸印课传见卯为车轮乘吉将，铸印乘轩','涨',3)

    def _jiaoche_xing(self, ri_gan, ganzhi, gs, zs):
        """交车刑: 干上神刑日支、支上神刑日干（寄宫）"""
        if not ri_gan or not gs or not zs or len(ganzhi)<2: return
        rz = ganzhi[1]
        gp = GAN_JIGONG.get(ri_gan,'')
        if rz in XING.get(gs,[]) and gp and gp in XING.get(zs,[]):
            self._add('交车刑','凶',f'干上{gs}刑支{rz}、支上{zs}刑干，和美中必致争竞','跌',2)

    def _jiaoche_hai(self, ri_gan, ganzhi, gs, zs):
        """交车害: 干上神害日支、支上神害日干（寄宫）"""
        if not ri_gan or not gs or not zs or len(ganzhi)<2: return
        rz = ganzhi[1]
        gp = GAN_JIGONG.get(ri_gan,'')
        if LIU_HAI.get(gs,'')==rz and gp and LIU_HAI.get(zs,'')==gp:
            self._add('交车害','凶',f'干上{gs}害支{rz}、支上{zs}害干，彼此相谋害','跌',2)

    def _mumen_kai(self, ri_gan, ganzhi, zs, tj):
        """墓门开: 卯酉日干墓乘蛇/虎加支"""
        if not ri_gan or not zs or len(ganzhi)<2: return
        rz = ganzhi[1]
        if rz not in ('卯','酉'): return
        gm = MU.get(ri_gan,'')
        if not gm or zs != gm: return
        if tj and tj.get(zs,'') in ('螣蛇','白虎'):
            self._add('墓门开','大凶',f'{rz}日干墓{gm}乘蛇虎加支，墓门开主重重有丧','跌',3)

    def _biandi_guiren(self, ri_gan, sc, gs, zs, tj):
        """遍地贵人: 三传+干支上皆乘贵人天将"""
        if not tj or len(sc)<3: return
        zhis = [z for z in list(sc)+[gs,zs] if z]
        if zhis and all(tj.get(z,'')=='贵人' for z in zhis):
            self._add('遍地贵人','凶','四课三传皆贵人，贵多不贵反无依','跌',2)

    def _guiren_rigui(self, ri_gan, sc, gs, zs, tj):
        """贵人作日鬼: 贵人乘日鬼（2026-08-21 修复：限课传六处，不再全盘扫天将）"""
        if not ri_gan or not tj: return
        for z in list(sc) + [gs, zs]:
            if z and tj.get(z, '')=='贵人' and _is_gan_ghost(ri_gan, z):
                loc = '干上' if z == gs else ('支上' if z == zs else '三传')
                self._add('贵人作日鬼','凶',f'贵人乘{z}为日干{ri_gan}之鬼（{loc}），贵人作日鬼','跌',2)
                return

    def _zhen_jieli(self, ri_gan, ganzhi, gs, zs):
        """芜淫卦（彼此全伤）: 干被干上神克、支被支上神克"""
        if not ri_gan or not gs or not zs or len(ganzhi)<2: return
        from .bifa_detector import _zhi_ke_zhi
        rz = ganzhi[1]
        if _is_gan_ghost(ri_gan, gs) and _zhi_ke_zhi(zs, rz):
            self._add('芜淫卦','凶',f'干被干上{gs}克、支被支上{zs}克，彼此全伤','跌',2)

    # ════════════════ 结果构建 ════════════════

    def _add(self, name, level, desc, signal, weight):
        self.detected_kege.append({
            'name':name,'level':level,'desc':desc,
            'signal':signal,'weight':weight
        })

    def _build_result(self) -> Dict:
        if not self.detected_kege:
            return {'匹配课格':[],'课格详情':{},'信号汇总':{'倾向':'平','强度':0,'涨权重':0,'跌权重':0,'震荡权重':0}}

        detail = {}
        scores = {'涨':0,'跌':0,'震荡':0}
        for k in self.detected_kege:
            n = k['name']
            detail[n] = {'等级':k['level'],'描述':k['desc'],'信号':k['signal'],'权重':k['weight']}
            scores[k['signal']] = scores.get(k['signal'],0) + k['weight']

        tw = sum(scores.values()) or 1
        mx = max(scores,key=scores.get)
        mxv = scores[mx]
        # 如果最大票数不超过其他二者之和，则为震荡
        other = tw - mxv
        tendency = mx if mxv > other else '震荡'
        strength = round(mxv/tw, 2)

        return {
            '匹配课格': [k['name'] for k in self.detected_kege],
            '课格详情': detail,
            '信号汇总': {
                '倾向': tendency,
                '强度': strength,
                '涨权重': scores['涨'],
                '跌权重': scores['跌'],
                '震荡权重': scores['震荡'],
            },
        }


def get_kege_summary(result: Dict) -> str:
    """生成课格摘要文本"""
    kege = result.get('匹配课格',[])
    if not kege:
        return '未检测到特殊课格'
    sig = result.get('信号汇总',{})
    t = sig.get('倾向','?')
    s = sig.get('强度',0)
    return f'检测到{len(kege)}个特殊课格(倾向:{t},强度:{s:.1%}): {",".join(kege[:5])}'
