"""
大六壬排盘引擎
实现天地盘、四课、三传等核心功能

⚠️ 2026-08-17 停用警示（股票域清理）：
- 本引擎已被权威 V2 `engine/sike_sanchuan_engine.SiKeSanChuanCalculator2` 取代
  （四课 218/218 一致性已验证；但 fa_san_chuan 在反吟/涉害/遥克等场景与 V2
  有 62/780 组合三传差异，以 V2 为准）。
- `get_yuejiang(农历月)` 为按农历月简化月将，勿用于新代码（精确口径 =
  `engine/yuejiang_engine.YueJiangCalculator.get_yuejiang_by_date` 中气换将）。
- 保留本文件仅因 40+ 历史脚本（_annotate_*.py/build_feature_vectors 等）依赖；
  其中 arrange_tiandi_pan/arrange_si_ke（月将直传）与 V2 一致可继续用。
"""

from data.斗首择日规则 import (
    TIANGAN, DIZHI, JIGONG, YUEJIANG, JIEQI_YUEJIANG,
    DIZHI_CHONG, LU, YIMA, GUIREN, TIANJIANG
)


class DaLiuRenEngine:
    """大六壬排盘引擎（P1 已停用，新代码请用 SiKeSanChuanCalculator2）"""
    
    def __init__(self):
        self.tiangan = TIANGAN
        self.dizhi = DIZHI
    
    def get_yuejiang(self, lunar_month: int) -> str:
        """
        根据农历月份获取月将
        :param lunar_month: 农历月份（1-12）
        :return: 月将地支
        """
        return YUEJIANG.get(lunar_month, '子')
    
    def get_jieqi_yuejiang(self, jieqi: str) -> str:
        """
        根据节气获取月将（中气换将口径）
        :param jieqi: 节气名称
        :return: 月将地支
        【P2 2026-08-17 纠错】原误用数字 key 的 YUEJIANG 表（永远返回'子'），改用 JIEQI_YUEJIANG
        """
        return JIEQI_YUEJIANG.get(jieqi, '子')
    
    def arrange_tiandi_pan(self, yuejiang: str, shichen: str) -> dict:
        """
        排天地盘
        月将加时，顺布天盘
        :param yuejiang: 月将
        :param shichen: 占时（时辰）
        :return: 天地盘字典
        """
        # 地盘固定
        di_pan = DIZHI.copy()
        
        # 天盘：月将加在时支上，顺布
        shi_index = DIZHI.index(shichen)
        yuejiang_index = DIZHI.index(yuejiang)
        
        # 计算偏移量：月将加在占时上
        offset = yuejiang_index - shi_index
        
        # 排天盘
        tian_pan = []
        for i in range(12):
            tian_index = (i + offset) % 12
            tian_pan.append(DIZHI[tian_index])
        
        # 组合天地盘
        result = {
            '地盘': di_pan,
            '天盘': tian_pan,
            '月将': yuejiang,
            '占时': shichen
        }
        
        # 添加对应关系
        result['天地对应'] = {}
        for i in range(12):
            result['天地对应'][di_pan[i]] = tian_pan[i]
        
        return result
    
    def get_jigong(self, tiangan: str) -> str:
        """
        获取十干寄宫
        :param tiangan: 天干
        :return: 寄宫地支
        """
        return JIGONG.get(tiangan, '')
    
    def arrange_si_ke(self, ri_gan: str, ri_zhi: str, tian_pan: dict) -> list:
        """
        起四课
        从日干起二课，从日支起二课
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param tian_pan: 天盘信息（包含天地对应）
        :return: 四课列表
        """
        si_ke = []
        
        # 第一课：日干寄宫的天盘
        ji_gong = self.get_jigong(ri_gan)
        if ji_gong:
            ke1_top = tian_pan['天地对应'].get(ji_gong, '')
            si_ke.append({'top': ke1_top, 'bottom': ri_gan, 'name': '第一课'})
            
            # 第二课：第一课上神的天盘
            if ke1_top in DIZHI:
                ke2_top = tian_pan['天地对应'].get(ke1_top, '')
                si_ke.append({'top': ke2_top, 'bottom': ke1_top, 'name': '第二课'})
        
        # 第三课：日支的天盘
        if ri_zhi in DIZHI:
            ke3_top = tian_pan['天地对应'].get(ri_zhi, '')
            si_ke.append({'top': ke3_top, 'bottom': ri_zhi, 'name': '第三课'})
            
            # 第四课：第三课上神的天盘
            if ke3_top in DIZHI:
                ke4_top = tian_pan['天地对应'].get(ke3_top, '')
                si_ke.append({'top': ke4_top, 'bottom': ke3_top, 'name': '第四课'})
        
        return si_ke
    
    # 五行属性（天干 + 地支）
    WUXING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
        '寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金',
        '酉': '金', '亥': '水', '子': '水', '辰': '土', '戌': '土',
        '丑': '土', '未': '土'
    }
    # 五行相克：木克土，土克水，水克火，火克金，金克木
    KE_REL = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    # 地支三刑（丑戌未、寅巳申、子卯；辰午酉亥自刑）
    XING = {'子': '卯', '卯': '子', '寅': '巳', '巳': '申', '申': '寅',
            '丑': '戌', '戌': '未', '未': '丑'}
    ZI_XING = set('辰午酉亥')

    def _wx(self, x: str) -> str:
        return self.WUXING.get(x, '')

    def _ke(self, a: str, b: str) -> bool:
        """a 是否克 b"""
        return bool(self._wx(a)) and self.KE_REL.get(self._wx(a)) == self._wx(b)

    def check_ke(self, top: str, bottom: str, ri_gan: str = '') -> str:
        """
        检查课体上下克关系（下神论本气五行，不含寄宫）
        :param top: 上神
        :param bottom: 下神
        :return: '克上'(下贼上), '克下'(上克下), '无克'
        """
        top_wx = self._wx(top)
        bottom_wx = self._wx(bottom)
        if not top_wx or not bottom_wx:
            return '无克'
        if self.KE_REL.get(top_wx) == bottom_wx:
            return '克下'  # 上克下
        elif self.KE_REL.get(bottom_wx) == top_wx:
            return '克上'  # 下贼上
        return '无克'
    
    def fa_san_chuan(self, si_ke: list, ri_gan: str, tiandi_pan: dict = None) -> dict:
        """
        发三传（九宗门）
        1. 贼克法 2. 比用法 3. 涉害法 4. 遥克法 5. 昴星法
        6. 别责法 7. 八专法 8. 伏吟法 9. 反吟法
        :param si_ke: 四课
        :param ri_gan: 日干
        :param tiandi_pan: 天地盘（用于连茹三传计算）
        :return: 三传信息
        """
        result = {
            '课体': '',
            '三传': [],
            '起法': ''
        }
        
        if tiandi_pan:
            self._tiandi_pan = tiandi_pan
        
        tp = self._tiandi_pan.get('天地对应', {}) if hasattr(self, '_tiandi_pan') else {}

        # 伏吟 / 反吟检测
        if tp:
            fuyin = all(tp.get(d) == d for d in DIZHI)
            fanyin = all(tp.get(d) == DIZHI_CHONG.get(d, '') for d in DIZHI)
        else:
            fuyin = fanyin = False
        if fuyin:
            return self._fu_yin(si_ke, ri_gan, result)
        if fanyin:
            return self._fan_yin(si_ke, ri_gan, result)

        # 不备检测：第四课下神 = 日干寄宫 → 第四课与第一课重复，作废（不参与克判断）
        jigong = JIGONG.get(ri_gan, '')
        active_ke = [ke for ke in si_ke if not (ke.get('name') == '第四课' and ke['bottom'] == jigong)]

        # 检查四课是否有克
        ke_list = []
        for ke in active_ke:
            ke_type = self.check_ke(ke['top'], ke['bottom'])
            if ke_type != '无克':
                ke_list.append({
                    '课': ke,
                    '类型': ke_type
                })
        
        if not ke_list:
            # 无克：八专（干支同位）→ 遥克 → 昴星
            ri_zhi = si_ke[2]['bottom'] if len(si_ke) > 2 else ''
            if ri_zhi and JIGONG.get(ri_gan) == ri_zhi:
                return self._ba_zhuan(si_ke, ri_gan, result)
            return self._yao_ke_or_ao_xing(si_ke, ri_gan, result)
        
        # 有克，优先用贼克法
        if len(ke_list) == 1:
            # 只有一课有克
            ke_info = ke_list[0]
            result['课体'] = '重审课' if ke_info['类型'] == '克上' else '元首课'
            result['三传'] = self._get_chuan_from_ke(ke_info['课'], si_ke)
            result['起法'] = '贼克法'
        else:
            # 多课有克，先判定: 有下贼上则丢弃所有上克下
            xia_ze = [k for k in ke_list if k['类型'] == '克上']   # 下贼上
            shang_ke = [k for k in ke_list if k['类型'] == '克下']  # 上克下
            
            if xia_ze:
                # 有下贼上: 只取下贼上, 舍上克下
                candidates = xia_ze
                result['起法'] = '贼克法(取下贼上)'
            else:
                candidates = shang_ke
                result['起法'] = '贼克法(取上克下)'
            
            if len(candidates) == 1:
                ke_info = candidates[0]
                result['课体'] = '重审课' if ke_info['类型'] == '克上' else '元首课'
                result['三传'] = self._get_chuan_from_ke(ke_info['课'], si_ke)
                return result
            else:
                # 多个同级克, 用比用法
                return self._bi_yong_or_she_hai(candidates, ri_gan, si_ke, result)
        
        return result
    
    def _step_n(self, zhi: str, n: int) -> str:
        """地支顺移 n 位（n 可为负，表示逆移）"""
        if zhi not in DIZHI:
            return ''
        return DIZHI[(DIZHI.index(zhi) + n) % 12]

    def _chuan_from_chu(self, chu: str) -> list:
        """由初传按地盘递进求三传：中传=初传地盘上神，末传=中传地盘上神"""
        tp = self._tiandi_pan.get('天地对应', {}) if hasattr(self, '_tiandi_pan') else {}
        zhong = tp.get(chu, '') if chu else ''
        mo = tp.get(zhong, '') if zhong else ''
        return [chu, zhong, mo]

    def _bi_yong_pick(self, shangshen: list, ri_gan: str) -> str:
        """多个发用神中取与日干同阴阳者（否则取第一个）"""
        if not shangshen:
            return ''
        is_yang = ri_gan in '甲丙戊庚壬'
        for s in shangshen:
            s_yang = s in '子寅辰午申戌'
            if s_yang == is_yang:
                return s
        return shangshen[0]

    def _ba_zhuan(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """八专法：干支同位两课无克，阳日干上顺三、阴日第四课上神逆三，中末俱干上神"""
        gan_shang = si_ke[0]['top'] if si_ke else ''
        if ri_gan in '甲丙戊庚壬':
            chu = self._step_n(gan_shang, 2)   # 顺数三神（连本位）= 顺移2位
        else:
            zhi_4 = si_ke[3]['top'] if len(si_ke) > 3 else ''
            chu = self._step_n(zhi_4, -2)      # 逆数三神（连本位）= 逆移2位
        result['课体'] = '八专课'
        result['起法'] = '八专法'
        result['三传'] = [chu, gan_shang, gan_shang]
        return result

    def _chuan_xing(self, chu, gan_shang, zhi_shang, ri_gan):
        """伏吟中末传用刑：初刑为中、中刑为末；自刑用杜传"""
        if chu in self.ZI_XING:
            # 杜传：初传自刑，阳日中传取支上神，阴日取干上神
            zhong = zhi_shang if ri_gan in '甲丙戊庚壬' else gan_shang
        else:
            zhong = self.XING.get(chu, '')
        if zhong in self.ZI_XING:
            mo = DIZHI_CHONG.get(zhong, '')  # 中传自刑，末传取中冲
        else:
            mo = self.XING.get(zhong, '')
        return [chu, zhong, mo]

    def _fu_yin(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """伏吟法（月将=占时，天地盘不动）"""
        gan_shang = si_ke[0]['top'] if si_ke else ''
        zhi_shang = si_ke[2]['top'] if len(si_ke) > 2 else ''
        ke_list = []
        for ke in si_ke:
            t = self.check_ke(ke['top'], ke['bottom'])
            if t != '无克':
                ke_list.append({'课': ke, '类型': t})
        if ke_list:
            # 有克（乙癸）：取克为初传，中末用刑
            chu = ke_list[0]['课']['top']
            result['课体'] = '伏吟课(不虞)'
            result['起法'] = '伏吟法(有克)'
        else:
            if ri_gan in '甲丙戊庚壬':
                chu = gan_shang
                result['课体'] = '伏吟课(自任)'
                result['起法'] = '伏吟法(自任)'
            else:
                chu = zhi_shang
                result['课体'] = '伏吟课(自信)'
                result['起法'] = '伏吟法(自信)'
        result['三传'] = self._chuan_xing(chu, gan_shang, zhi_shang, ri_gan)
        return result

    def _fan_yin(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """反吟法（月将与占时对冲）"""
        gan_shang = si_ke[0]['top'] if si_ke else ''
        zhi_shang = si_ke[2]['top'] if len(si_ke) > 2 else ''
        ri_zhi = si_ke[2]['bottom'] if len(si_ke) > 2 else ''
        ke_list = []
        for ke in si_ke:
            t = self.check_ke(ke['top'], ke['bottom'])
            if t != '无克':
                ke_list.append({'课': ke, '类型': t})
        if ke_list:
            # 有克：下贼上优先，再比用；中末用冲（对冲递进）
            xia = [k for k in ke_list if k['类型'] == '克上']
            shang = [k for k in ke_list if k['类型'] == '克下']
            cand = xia if xia else shang
            if len(cand) == 1:
                chu = cand[0]['课']['top']
            else:
                is_yang = ri_gan in '甲丙戊庚壬'
                same = [k for k in cand if (k['课']['top'] in '子寅辰午申戌') == is_yang]
                chu = (same or cand)[0]['课']['top']
            zhong = DIZHI_CHONG.get(chu, '')
            mo = DIZHI_CHONG.get(zhong, '')
            result['课体'] = '反吟课(无依)'
            result['起法'] = '反吟法(有克)'
            result['三传'] = [chu, zhong, mo]
        else:
            # 无克取驿马（井栏格），中支上、末干上
            yima = ''
            for key, value in YIMA.items():
                if ri_zhi in key:
                    yima = value
                    break
            result['课体'] = '反吟课(无亲)'
            result['起法'] = '反吟法(井栏)'
            result['三传'] = [yima, zhi_shang, gan_shang]
        return result

    def _bie_ze(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """别责法（四课不备三课，无克无遥克）：阳日取干合上神，阴日取支三合前一位"""
        gan_shang = si_ke[0]['top'] if si_ke else ''
        zhi_shang = si_ke[2]['top'] if len(si_ke) > 2 else ''
        tp = self._tiandi_pan.get('天地对应', {}) if hasattr(self, '_tiandi_pan') else {}
        if ri_gan in '甲丙戊庚壬':
            # 阳日：初传=干合（五合）之干的上神，中末传皆取干上神
            HE = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛',
                  '辛': '丙', '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}
            he_jigong = JIGONG.get(HE.get(ri_gan, ''), '')
            chu = tp.get(he_jigong, '')
            result['课体'] = '别责课'
            result['起法'] = '别责法(阳日干合)'
            result['三传'] = [chu, gan_shang, gan_shang]
        else:
            # 阴日：初传=支三合前一位，中末传皆取支上神
            SANHE = ['申子辰', '寅午戌', '亥卯未', '巳酉丑']
            ri_zhi = si_ke[2]['bottom'] if len(si_ke) > 2 else ''
            chu = ''
            for ju in SANHE:
                if ri_zhi in ju:
                    idx = ju.index(ri_zhi)
                    chu = ju[(idx + 1) % 3]
                    break
            result['课体'] = '别责课'
            result['起法'] = '别责法(阴日支三合)'
            result['三传'] = [chu, zhi_shang, zhi_shang]
        return result

    def _mao_xing(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """昴星法：阳日虎视、阴日冬蛇掩目"""
        tp = self._tiandi_pan.get('天地对应', {}) if hasattr(self, '_tiandi_pan') else {}
        gan_shang = si_ke[0]['top'] if si_ke else ''
        zhi_shang = si_ke[2]['top'] if len(si_ke) > 2 else ''
        if ri_gan in '甲丙戊庚壬':
            # 阳日虎视：初传=地盘酉上神，中传=支上神，末传=干上神
            chu = tp.get('酉', '')
            result['课体'] = '虎视课'
            result['起法'] = '昴星法(阳日虎视)'
            result['三传'] = [chu, zhi_shang, gan_shang]
        else:
            # 阴日冬蛇掩目：初传=天盘酉所临之地，中传=干上神，末传=支上神
            chu = ''
            for di, tian in tp.items():
                if tian == '酉':
                    chu = di
                    break
            result['课体'] = '冬蛇掩目课'
            result['起法'] = '昴星法(阴日冬蛇掩目)'
            result['三传'] = [chu, gan_shang, zhi_shang]
        return result

    def _yao_ke_or_ao_xing(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """遥克法（蒿矢/弹射）或昴星法"""
        # 课上神（去重保序）
        tops = []
        for ke in si_ke:
            t = ke['top']
            if t in DIZHI and t not in tops:
                tops.append(t)
        # 蒿矢：课上神克日干；弹射：日干克课上神
        haoshi = [t for t in tops if self._ke(t, ri_gan)]
        tanshe = [t for t in tops if self._ke(ri_gan, t)]
        if haoshi:
            chu = self._bi_yong_pick(haoshi, ri_gan)
            result['课体'] = '蒿矢课'
            result['起法'] = '遥克法(蒿矢)'
            result['三传'] = self._chuan_from_chu(chu)
            return result
        if tanshe:
            chu = self._bi_yong_pick(tanshe, ri_gan)
            result['课体'] = '弹射课'
            result['起法'] = '遥克法(弹射)'
            result['三传'] = self._chuan_from_chu(chu)
            return result
        # 无遥克：不备三课 → 别责，否则 → 昴星
        tops = {ke['top'] for ke in si_ke if ke['top'] in DIZHI}
        if len(tops) == 3:
            return self._bie_ze(si_ke, ri_gan, result)
        return self._mao_xing(si_ke, ri_gan, result)
    
    def _bi_yong_or_she_hai(self, ke_list: list, ri_gan: str, si_ke: list, result: dict) -> dict:
        """比用法（知一课）：取与日干同阴阳者发用；若仍多个，转涉害法"""
        is_yang = ri_gan in '甲丙戊庚壬'
        same = []
        other = []
        for k in ke_list:
            top = k['课']['top']
            top_yang = top in '子寅辰午申戌'
            if top_yang == is_yang:
                same.append(k)
            else:
                other.append(k)
        cand = same if same else other
        if len(cand) == 1:
            k = cand[0]
            result['课体'] = '知一课'
            result['起法'] = '比用法'
            result['三传'] = self._get_chuan_from_ke(k['课'], si_ke)
            return result
        return self._she_hai(cand, ri_gan, si_ke, result)

    def _she_hai(self, ke_list: list, ri_gan: str, si_ke: list, result: dict) -> dict:
        """涉害法（邵彦和孟仲季法）：上神加临地盘孟位优先，次仲，次季；同孟仲季则缀瑕"""
        MENG = '寅申巳亥'
        ZHONG = '子午卯酉'

        def di_of(k):
            b = k['课']['bottom']
            return b if b in DIZHI else JIGONG.get(ri_gan, '')

        def cls_of(k):
            d = di_of(k)
            return 0 if d in MENG else (1 if d in ZHONG else 2)

        best_cls = min(cls_of(k) for k in ke_list)
        best = [k for k in ke_list if cls_of(k) == best_cls]
        if len(best) == 1:
            k = best[0]
            result['起法'] = '涉害法(见机)' if best_cls == 0 else '涉害法(察微)'
        else:
            # 缀瑕（复等）：阳日取干上先见，阴日取支上先见
            if ri_gan in '甲丙戊庚壬':
                gan = [x for x in best if x['课'].get('name') in ('第一课', '第二课')]
                k = (gan or best)[0]
            else:
                zhi = [x for x in best if x['课'].get('name') in ('第三课', '第四课')]
                k = (zhi or best)[0]
            result['起法'] = '涉害法(缀瑕)'
        result['课体'] = '涉害课'
        result['三传'] = self._get_chuan_from_ke(k['课'], si_ke)
        return result
    
    def _get_chuan_from_ke(self, ke: dict, si_ke: list) -> list:
        """从课获取三传"""
        chu_chuan = ke['top']
        zhong_chuan = ''
        mo_chuan = ''
        
        # 查找中传：先查四课（bottom匹配），查不到则用天地盘
        zhong_chuan = self._find_next_chuan(chu_chuan, si_ke)
        
        # 查找末传
        if zhong_chuan:
            mo_chuan = self._find_next_chuan(zhong_chuan, si_ke)
        
        return [chu_chuan, zhong_chuan, mo_chuan]

    def _find_next_chuan(self, current: str, si_ke: list) -> str:
        """三传递进：中传=当前地盘上神，末传=中传地盘上神（只用天地盘，不查四课）"""
        if current in DIZHI and hasattr(self, '_tiandi_pan'):
            tp = self._tiandi_pan.get('天地对应', {})
            return tp.get(current, '')
        return ''
    
    def get_lu_ma_gui(self, ri_gan: str, ri_zhi: str) -> dict:
        """
        获取禄马贵
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 禄马贵信息
        """
        lu = LU.get(ri_gan, '')
        
        # 驿马（以日支查）
        yima = ''
        for key, value in YIMA.items():
            if ri_zhi in key:
                yima = value
                break
        
        # 贵人
        guiren_list = GUIREN.get(ri_gan, [])
        
        return {
            '禄': lu,
            '驿马': yima,
            '贵人': guiren_list
        }
    
    def full_pai_pan(self, lunar_month: int, shichen: str, 
                     ri_gan: str, ri_zhi: str) -> dict:
        """
        完整排盘
        :param lunar_month: 农历月份
        :param shichen: 占时
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 完整排盘结果
        """
        # 1. 起月将
        yuejiang = self.get_yuejiang(lunar_month)
        
        # 2. 排天地盘
        tiandi_pan = self.arrange_tiandi_pan(yuejiang, shichen)
        
        # 3. 起四课
        si_ke = self.arrange_si_ke(ri_gan, ri_zhi, tiandi_pan)
        
        # 4. 发三传
        san_chuan = self.fa_san_chuan(si_ke, ri_gan, tiandi_pan)
        
        # 5. 起禄马贵
        lu_ma_gui = self.get_lu_ma_gui(ri_gan, ri_zhi)
        
        return {
            '月将': yuejiang,
            '占时': shichen,
            '日柱': f"{ri_gan}{ri_zhi}",
            '天地盘': tiandi_pan,
            '四课': si_ke,
            '三传': san_chuan,
            '禄马贵': lu_ma_gui
        }


# 测试函数
def test_da_liu_ren():
    """测试大六壬引擎"""
    engine = DaLiuRenEngine()
    
    print("=== 月将测试 ===")
    for month in range(1, 13):
        print(f"农历{month}月：{engine.get_yuejiang(month)}将")
    
    print("\n=== 天地盘测试 ===")
    result = engine.arrange_tiandi_pan('亥', '寅')
    print(f"亥将加寅时：{result}")
    
    print("\n=== 四课测试 ===")
    # 雨水后，甲子日，寅时
    tiandi_pan = engine.arrange_tiandi_pan('亥', '寅')
    si_ke = engine.arrange_si_ke('甲', '子', tiandi_pan)
    for ke in si_ke:
        print(f"{ke['name']}: {ke['top']} {ke['bottom']}")
    
    print("\n=== 完整排盘测试 ===")
    result = engine.full_pai_pan(1, '寅', '甲', '子')
    print(f"排盘结果：{result}")


if __name__ == '__main__':
    test_da_liu_ren()
