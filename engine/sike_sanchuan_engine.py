"""
四课三传计算引擎
实现大六壬四课起法和三传九种法则
"""

from typing import Dict, List, Tuple, Optional


class SiKeSanChuanCalculator:
    """四课三传计算器（V1 · 已废弃）

    ⚠️ 2026-08-17 起废弃：P1 起课统一后，生产链路全部使用
    `SiKeSanChuanCalculator2`（权威 V2，修复别责/遥克/涉害/伏吟 4 个宗门 bug）。
    本类仅保留为 V2 的基类（V2 复用其 _she_hai_fa/_ang_xing_fa/qi_sike 等方法），
    禁止在新代码中直接实例化；其 `fa_sanchuan` 入口会发出 DeprecationWarning。
    """
    
    # 天干寄宫
    TIAN_GAN_JI_GONG = {
        '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未',
        '戊': '巳', '己': '未', '庚': '申', '辛': '戌',
        '壬': '亥', '癸': '丑'
    }
    
    # 地支六冲
    LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    
    # 五行相克
    WU_XING_KE = {
        '金': '木', '木': '土', '土': '水', '水': '火', '火': '金'
    }
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木',
        '辰': '土', '巳': '火', '午': '火', '未': '土',
        '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 天干五行
    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火',
        '戊': '土', '己': '土', '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 地支索引映射
    DIZHI_INDEX = {
        '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
        '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11
    }
    
    # 地支先天数（河图数）
    DIZHI_XIAN_TIAN_NUM = {
        '子': 1, '丑': 2, '寅': 3, '卯': 4,
        '辰': 5, '巳': 6, '午': 7, '未': 8,
        '申': 9, '酉': 10, '戌': 11, '亥': 12
    }
    
    # 地支后天数（洛书数）
    DIZHI_HOU_TIAN_NUM = {
        '子': 1, '丑': 2, '寅': 8, '卯': 3,
        '辰': 4, '巳': 9, '午': 9, '未': 2,
        '申': 7, '酉': 6, '戌': 5, '亥': 1
    }
    
    # 十二天将
    TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                  '天空', '白虎', '太常', '玄武', '太阴', '天后']
    
    # 天干寄宫五行
    GAN_JI_GONG_WUXING_ALL = {
        '寅': ['木'],  # 甲
        '辰': ['木'],  # 乙
        '巳': ['火', '土'],  # 丙、戊
        '未': ['火', '土'],  # 丁、己
        '申': ['金'],  # 庚
        '戌': ['金'],  # 辛
        '亥': ['水'],  # 壬
        '丑': ['水'],  # 癸
    }
    
    # 缓存
    def __init__(self):
        # 天地盘缓存
        self.tiandi_pan_cache = {}
        # 四课缓存
        self.sike_cache = {}
        # 涉害深度缓存
        self.she_hai_depth_cache = {}
        # 三传缓存
        self.sanchuan_cache = {}
    
    def get_tiandi_pan(self, yuejiang: str, shichen: str) -> Dict[str, str]:
        """
        获取天地盘对应关系
        
        月将加时规则：
        - 月将加在时辰位（地盘时辰位置上的天盘是月将）
        - 天盘顺时针排列（子丑寅卯...）
        
        例如：申将子时
        - 地盘子宫上的天盘是申（月将）
        - 地盘丑宫上的天盘是酉
        - ...
        
        返回：{地盘地支: 天盘地支}
        """
        # 【BUG-FIX 2026-08-18】非法月将/时辰兜底（原 KeyError 崩溃）
        if yuejiang not in self.DIZHI_INDEX or shichen not in self.DIZHI_INDEX:
            return {}
        # 检查缓存
        cache_key = f"{yuejiang}:{shichen}"
        if cache_key in self.tiandi_pan_cache:
            return self.tiandi_pan_cache[cache_key]
        
        # 使用预定义的地支顺序和索引映射
        shi_index = self.DIZHI_INDEX[shichen]
        yuejiang_index = self.DIZHI_INDEX[yuejiang]
        
        # 月将加时：地盘时辰位上的天盘是月将
        # 地盘第i位的天盘 = 月将 + (i - 时辰位)
        tiandi_pan = {}
        for i in range(12):
            tian_index = (yuejiang_index + i - shi_index + 12) % 12
            tiandi_pan[self.DIZHI[i]] = self.DIZHI[tian_index]
        
        # 缓存结果
        self.tiandi_pan_cache[cache_key] = tiandi_pan
        return tiandi_pan
    
    def qi_sike(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict[str, str]) -> List[Tuple[str, str, str, str]]:
        """
        起四课
        返回：[(课名，上神，下神，上神天将), ...]
        """
        # 生成缓存键（使用tiandi_pan的字符串表示作为缓存键的一部分）
        tiandi_pan_key = "-".join([f"{k}:{v}" for k, v in sorted(tiandi_pan.items())])
        cache_key = f"{ri_gan}:{ri_zhi}:{tiandi_pan_key}"
        
        # 检查缓存
        if cache_key in self.sike_cache:
            return self.sike_cache[cache_key]
        
        # 【BUG-FIX 2026-08-18】非法干支兜底（原 KeyError 崩溃）
        if ri_gan not in self.TIAN_GAN_JI_GONG or ri_zhi not in self.DIZHI_INDEX:
            return []

        sike = []
        
        # 第一课：日干上神
        # 日干寄宫，看寄宫天盘是什么
        ji_gong = self.TIAN_GAN_JI_GONG[ri_gan]
        gan_shang = tiandi_pan[ji_gong]  # 寄宫的天盘
        sike.append(('第一课', gan_shang, ri_gan, ''))
        
        # 第二课：干上神的上神
        # 看 gan_shang 这个地支的天盘
        gan_shang_shang = tiandi_pan[gan_shang]
        sike.append(('第二课', gan_shang_shang, gan_shang, ''))
        
        # 第三课：日支上神
        zhi_shang = tiandi_pan[ri_zhi]
        sike.append(('第三课', zhi_shang, ri_zhi, ''))
        
        # 第四课：支上神的上神
        zhi_shang_shang = tiandi_pan[zhi_shang]
        sike.append(('第四课', zhi_shang_shang, zhi_shang, ''))
        
        # 缓存结果
        self.sike_cache[cache_key] = sike
        return sike
    
    def is_ke(self, shang: str, xia: str, ri_gan: str = '') -> str:
        """
        判断是否相克
        返回：'克'（上克下），'贼'（下贼上），''（无克）

        参数 ri_gan：日干。传入后启用"寄宫支回退日干本气"（见下）。
        不传则行为与历史一致（向后兼容，供审计/显示类调用使用）。
        
        注意：
        - 上神总是地支，用 DIZHI_WU_XING
        - 第一课下神为天干（日干），其余课下神为地支
        - 【2026-09-09 OX Alpha 复核修复】第一课判克须以日干**寄宫支**五行论
          （"干上神课，下神即日干之寄宫，应以寄宫支五行论生克"——《大六壬大全》通例）。
          原用干五行（如乙=木）致 乙寄辰(土) 克亥(水) 被判成"水生木无克"，漏判下贼上，
          使多贼克课误走"单贼→重审"、发用/课体一并错判（262期乙酉日实证：三贼误判二贼）。
        """
        shang_wuxing = self.DIZHI_WU_XING.get(shang, '')
        
        # 判断下神是天干还是地支
        # 【2026-09-10 正式规则 · 憨爷拍板采纳】第一课下神=日干时，判克用「日干本身五行」
        #   原用「日干寄宫支五行」（2026-09-09 依对 262 期的理论推导所加），
        #   2026-09-10 以《断案疏正》218 古例实证推翻：
        #     寄宫判克 178/207（错 29 案，日干清一色 乙丁戊辛癸）
        #     本气判克 205/207 = 99.0%（错 2 案）
        #   三重验证：三传匹配 86.0%→99.0%、PDF 直提 83.7%→96.7%、古例 M3 88.4%→88.9%，零回归。
        #   262 期两法三传相同（亥/午/丑），仅课体 缀瑕格↔重审课 之差。
        #   详见 _memory/engine_refine_report.md。
        #   一键回退：环境变量 IS_KE_JIGONG=1 → 切回寄宫判克。
        import os as _os
        if xia in self.TIAN_GAN_WU_XING:
            # 下神即日干（第一课）
            if _os.getenv('IS_KE_JIGONG', '0') == '1':
                ji_gong = self.TIAN_GAN_JI_GONG.get(xia, '')
                xia_wuxing = self.DIZHI_WU_XING.get(ji_gong, '')
            else:
                xia_wuxing = self.TIAN_GAN_WU_XING.get(xia, '')
        elif _os.getenv('IS_KE_JIGONG_EXT', '0') == '1' and ri_gan \
                and self.TIAN_GAN_JI_GONG.get(ri_gan, '') == xia:
            # 【2026-09-10 判克扩展 —— ⛔ 实测否决，默认关闭，仅供对照】
            #   设想：下神为「日干寄宫支」时亦回退日干本气。依据是 §宅墓02·007（p.38）
            #     邵公"今第一课卯加辰，卯，木，辰内乙亦木，不克"。
            #   结果（A/B + 原文逐案核实）——**净负，已回退**：
            #     ✅ 修好 §宅墓02·007（四课无克 → 遥克弹射 → 辰/卯/寅）
            #     ❌ 弄坏 §杂占17·216（癸丑日酉将戌时）：原书"兄壬子玄/兄辛亥常/官庚戌虎"
            #        = 子/亥/戌，扩展后变 酉/子/子
            #     ❌ 弄坏 12 案课体：§交易谋为10·148、§亡盗15·188 等原书**明标"课体课格：涉害"**，
            #        扩展后均变"重审课"；且 §亡盗15·188 正是"干来加支"规则的实证案，
            #        扩展后该规则不再生效 → **与"干来加支"修复冲突**
            #   结论：邵公那句是**第一课**判克的解释，不可推广为"任何课的下神为寄宫支即回退本气"。
            #   回退开关：IS_KE_JIGONG_EXT=1 可启用（仅供对照实验）。
            xia_wuxing = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        else:
            xia_wuxing = self.DIZHI_WU_XING.get(xia, '')
        
        if not shang_wuxing or not xia_wuxing:
            return ''
        
        # 上克下：上神五行克下神五行
        if self.WU_XING_KE.get(shang_wuxing) == xia_wuxing:
            return '克'
        
        # 下贼上：下神五行克上神五行
        if self.WU_XING_KE.get(xia_wuxing) == shang_wuxing:
            return '贼'
        
        return ''
    
    def is_yang_ri(self, ri_gan: str) -> bool:
        """判断是否为阳日"""
        return ri_gan in ['甲', '丙', '戊', '庚', '壬']
    
    def is_yang_zhi(self, zhi: str) -> bool:
        """判断是否为阳支"""
        return zhi in ['子', '寅', '辰', '午', '申', '戌']
    
    def compare_zhi_value(self, zhi1: str, zhi2: str, use_xian_tian: bool = True) -> int:
        """
        比较两个地支的数值大小（有比用比原则）
        
        :param zhi1: 地支 1
        :param zhi2: 地支 2
        :param use_xian_tian: True 使用先天数，False 使用后天数
        :return: 1 表示 zhi1 大，-1 表示 zhi2 大，0 表示相等
        """
        if use_xian_tian:
            num1 = self.DIZHI_XIAN_TIAN_NUM.get(zhi1, 0)
            num2 = self.DIZHI_XIAN_TIAN_NUM.get(zhi2, 0)
        else:
            num1 = self.DIZHI_HOU_TIAN_NUM.get(zhi1, 0)
            num2 = self.DIZHI_HOU_TIAN_NUM.get(zhi2, 0)
        
        if num1 > num2:
            return 1
        elif num1 < num2:
            return -1
        else:
            return 0
    
    # 天干长生位（长生十二宫；【BUG-FIX 2026-08-18 案例实证】统一五行长生口径，
    # 原为十干阴阳长生（乙午丁酉己酉辛子癸卯）与案例"辛长生于巳"矛盾，弃用阴阳表）
    TIAN_GAN_CHANG_SHENG = {
        '甲': '亥', '乙': '亥', '丙': '寅', '丁': '寅',
        '戊': '申', '己': '申', '庚': '巳', '辛': '巳',
        '壬': '申', '癸': '申'
    }
    
    # 天干临官位（禄位）
    TIAN_GAN_LU_WEI = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
        '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
        '壬': '亥', '癸': '子'
    }
    
    # 自刑地支
    ZI_XING = ['辰', '午', '酉', '亥']
    
    # 五行相生关系
    WU_XING_SHENG = {
        '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
    }
    
    def _check_wuxing_sheng(self, upper: str, lower: str) -> bool:
        """检查天盘是否生地盘（五行相生）"""
        wu_xing_map = self.DIZHI_WU_XING
        sheng_map = self.WU_XING_SHENG
        upper_wx = wu_xing_map.get(upper, '')
        lower_wx = wu_xing_map.get(lower, '')
        if upper_wx and lower_wx:
            return sheng_map.get(upper_wx) == lower_wx
        return False
    
    def _enrich_ke_ge(self, result: Dict, ri_gan: str, ri_zhi: str,
                      tiandi_pan: Dict, sike: List, shi_chen: str = None) -> Dict:
        """识别附加课体课格（杜传、励德、元胎等）"""
        ke_ge_list = []
        
        # 1. 杜传格 - 伏吟课且初传自刑
        if result.get('课体') == '伏吟课':
            chu = result.get('初传', '')
            if chu in self.ZI_XING:
                ke_ge_list.append('杜传格')
        
        # 2. 励德课 - 天乙贵人立卯酉
        if shi_chen and ri_gan:
            try:
                from engine.gui_ren_engine import GuiRenCalculator
                gr = GuiRenCalculator()
                tian_pan = {'天地对应': tiandi_pan}
                gui_ren_result = gr.arrange_gui_ren_pan(ri_gan, tian_pan, shi_chen)
                gui_ren_pos = gui_ren_result.get('贵人落地盘位置', '')
                if gui_ren_pos in ['卯', '酉']:
                    ke_ge_list.append('励德课')
            except Exception:
                pass
        
        # 3. 元胎课
        # 定义A：四课上下皆相生（标准课经定义）
        is_yuan_tai_a = True
        has_valid_course = False
        for course in sike:
            if len(course) >= 3:
                upper = course[1]
                lower = course[2]
                if upper and lower:
                    has_valid_course = True
                    if not self._check_wuxing_sheng(upper, lower):
                        is_yuan_tai_a = False
                        break
        if has_valid_course and is_yuan_tai_a:
            ke_ge_list.append('元胎课')
        else:
            # 定义B：伏吟课中，初传为日干之临官（禄位）
            if result.get('课体') == '伏吟课':
                chu = result.get('初传', '')
                lu_wei = self.TIAN_GAN_LU_WEI.get(ri_gan, '')
                if chu == lu_wei:
                    ke_ge_list.append('元胎课')
        
        if ke_ge_list:
            result['课体课格'] = ke_ge_list
        return result
    
    def fa_sanchuan(self, sike: List[Tuple], ri_gan: str, ri_zhi: str, 
                    tiandi_pan: Dict[str, str], shi_chen: str = None) -> Dict[str, str]:
        import warnings
        warnings.warn(
            'SiKeSanChuanCalculator(V1) 已废弃：P1 起课统一后请改用 SiKeSanChuanCalculator2'
            '（V1 在反吟/涉害/遥克/伏吟等场景三传有误）', DeprecationWarning, stacklevel=2)
        """
        发三传
        返回：{'初传': str, '中传': str, '末传': str, '课体': str, '起法': str}
        
        九种发用法则顺序：
        1. 贼克法  2. 比用法  3. 涉害法  4. 遥克法  5. 昂星法
        6. 别责法  7. 八专法  8. 伏吟法  9. 反吟法
        """
        # 生成缓存键
        sike_key = "-".join([f"{name}:{shang}:{xia}" for name, shang, xia, _ in sike])
        tiandi_pan_key = "-".join([f"{k}:{v}" for k, v in sorted(tiandi_pan.items())])
        cache_key = f"{ri_gan}:{ri_zhi}:{sike_key}:{tiandi_pan_key}"
        
        # 检查缓存
        if cache_key in self.sanchuan_cache:
            return self.sanchuan_cache[cache_key]
        
        yang_ri = self.is_yang_ri(ri_gan)
        
        # 检查是否为八专日（干支同位）
        is_ba_zhuan = self._is_ba_zhuan(ri_gan, ri_zhi)
        
        # 检查是否为伏吟（天地盘相同）
        is_fu_yin = self._is_fu_yin(tiandi_pan)

        # 检查是否为反吟（天地盘对冲）
        is_fan_yin = self._is_fan_yin(tiandi_pan)

        # 九宗门优先级：伏吟 → 反吟 → 贼克(含比用/涉害) → 遥克 → 昴星 → 别责 → 八专
        # 别责仅在无克贼、无遥克时才判定，不可在贼克之前检查
        if is_fu_yin:
            result = self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)

        # 反吟课（天地盘对冲）
        elif is_fan_yin:
            result = self._fan_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)

        # 1. 贼克法（含比用、涉害）
        else:
            ke_results = []
            for i, (name, shang, xia, _) in enumerate(sike):
                ke_type = self.is_ke(shang, xia, ri_gan)
                if ke_type:
                    ke_results.append((i + 1, ke_type, shang, xia))

            if len(ke_results) == 1:
                # 只有一课克贼
                # 【关键修正】伏吟课优先于八专课
                if is_fu_yin:
                    # 伏吟课有贼克，也要用伏吟法的中末传规则
                    result = self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
                else:
                    # 非伏吟课，用贼克法
                    chu_chuan = ke_results[0][2]
                    zhong_chuan = tiandi_pan[chu_chuan]
                    mo_chuan = tiandi_pan[zhong_chuan]

                    if ke_results[0][1] == '克':
                        ke_ti = '元首课'
                    else:
                        ke_ti = '重审课'

                    result = {
                        '初传': chu_chuan,
                        '中传': zhong_chuan,
                        '末传': mo_chuan,
                        '课体': ke_ti,
                        '起法': '贼克法'
                    }

            elif len(ke_results) > 1:
                # 2. 比用法
                if is_fu_yin:
                    # 伏吟课有多课克贼，也要用伏吟法的中末传规则
                    result = self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
                else:
                    # 多课克贼，先分优先级：下贼上 > 上克下
                    xia_zei_shang = [(k, t, s, x) for k, t, s, x in ke_results if t == '贼']
                    shang_ke_xia = [(k, t, s, x) for k, t, s, x in ke_results if t == '克']

                    # 优先处理下贼上
                    if xia_zei_shang:
                        # 有下贼上，优先处理
                        if len(xia_zei_shang) == 1:
                            # 只有一个下贼上，直接取用
                            chu_chuan = xia_zei_shang[0][2]
                            zhong_chuan = tiandi_pan[chu_chuan]
                            mo_chuan = tiandi_pan[zhong_chuan]

                            result = {
                                '初传': chu_chuan,
                                '中传': zhong_chuan,
                                '末传': mo_chuan,
                                '课体': '重审课',
                                '起法': '贼克法（下贼上）'
                            }
                        else:
                            # 多个下贼上，需要比用
                            bi_yong_results = []
                            for ke_num, ke_type, shang, xia in xia_zei_shang:
                                if yang_ri and self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang, xia))
                                elif not yang_ri and not self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang, xia))

                            if len(bi_yong_results) == 1:
                                chu_chuan = bi_yong_results[0][1]
                                zhong_chuan = tiandi_pan[chu_chuan]
                                mo_chuan = tiandi_pan[zhong_chuan]

                                result = {
                                    '初传': chu_chuan,
                                    '中传': zhong_chuan,
                                    '末传': mo_chuan,
                                    '课体': '重审课',
                                    '起法': '贼克法（下贼上）'
                                }
                            elif len(bi_yong_results) > 1:
                                result = self._she_hai_fa([(k, s, x) for k, s, x in bi_yong_results], tiandi_pan, ri_gan, ri_zhi)
                            else:
                                result = self._she_hai_fa([(k, s, x) for k, _, s, x in xia_zei_shang], tiandi_pan, ri_gan, ri_zhi)
                    else:
                        # 无下贼上，处理上克下
                        if len(shang_ke_xia) == 1:
                            chu_chuan = shang_ke_xia[0][2]
                            zhong_chuan = tiandi_pan[chu_chuan]
                            mo_chuan = tiandi_pan[zhong_chuan]

                            result = {
                                '初传': chu_chuan,
                                '中传': zhong_chuan,
                                '末传': mo_chuan,
                                '课体': '元首课',
                                '起法': '贼克法（上克下）'
                            }
                        else:
                            # 多个上克下，需要比用
                            bi_yong_results = []
                            for ke_num, ke_type, shang, xia in shang_ke_xia:
                                if yang_ri and self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang, xia))
                                elif not yang_ri and not self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang, xia))

                            if len(bi_yong_results) == 1:
                                chu_chuan = bi_yong_results[0][1]
                                zhong_chuan = tiandi_pan[chu_chuan]
                                mo_chuan = tiandi_pan[zhong_chuan]

                                result = {
                                    '初传': chu_chuan,
                                    '中传': zhong_chuan,
                                    '末传': mo_chuan,
                                    '课体': '元首课',
                                    '起法': '贼克法（上克下，比用）'
                                }
                            elif len(bi_yong_results) > 1:
                                result = self._she_hai_fa([(k, s, x) for k, s, x in bi_yong_results], tiandi_pan, ri_gan, ri_zhi)
                            else:
                                result = self._she_hai_fa([(k, s, x) for k, _, s, x in shang_ke_xia], tiandi_pan, ri_gan, ri_zhi)

            else:
                # 无克贼时：遥克 → 别责(四课不全) → 八专(干支同位) → 昴星(四课全无克贼)
                yao_ke_results = []
                for i, (name, shang, xia, _) in enumerate(sike):
                    # 上神克日干
                    shang_wuxing = self.DIZHI_WU_XING.get(shang, '')
                    ri_wuxing = self.TIAN_GAN_WU_XING[ri_gan]

                    if self.WU_XING_KE.get(shang_wuxing) == ri_wuxing:
                        yao_ke_results.append((i + 1, '上克干', shang))
                    elif self.WU_XING_KE.get(ri_wuxing) == shang_wuxing:
                        yao_ke_results.append((i + 1, '干克上', shang))

                if yao_ke_results:
                    # 取上克干为先，无则取干克上
                    shang_ke_gan = [r for r in yao_ke_results if r[1] == '上克干']
                    if shang_ke_gan:
                        # 有多个上克干，需要比用
                        if len(shang_ke_gan) == 1:
                            chu_chuan = shang_ke_gan[0][2]
                        else:
                            # 多个上克干，先比用（阴阳日比较）
                            bi_yong_results = []
                            for ke_num, ke_type, shang in shang_ke_gan:
                                if yang_ri and self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang))
                                elif not yang_ri and not self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang))

                            if len(bi_yong_results) == 1:
                                chu_chuan = bi_yong_results[0][1]
                            elif len(bi_yong_results) > 1:
                                bi_yong_with_xia = []
                                for ke_num, shang in bi_yong_results:
                                    for i, (name, s, x, _) in enumerate(sike):
                                        if i + 1 == ke_num:
                                            bi_yong_with_xia.append((ke_num, shang, x))
                                            break
                                result = self._she_hai_fa(bi_yong_with_xia, tiandi_pan, ri_gan, ri_zhi)
                                self.sanchuan_cache[cache_key] = result
                                return result
                            else:
                                chu_chuan = shang_ke_gan[0][2]
                    else:
                        # 无上克干，取干克上
                        gan_ke_shang = [r for r in yao_ke_results if r[1] == '干克上']
                        if len(gan_ke_shang) == 1:
                            chu_chuan = gan_ke_shang[0][2]
                        else:
                            # 多个干克上，也要比用
                            bi_yong_results = []
                            for ke_num, ke_type, shang in gan_ke_shang:
                                if yang_ri and self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang))
                                elif not yang_ri and not self.is_yang_zhi(shang):
                                    bi_yong_results.append((ke_num, shang))

                            if len(bi_yong_results) == 1:
                                chu_chuan = bi_yong_results[0][1]
                            elif len(bi_yong_results) > 1:
                                bi_yong_with_xia = []
                                for ke_num, shang in bi_yong_results:
                                    for i, (name, s, x, _) in enumerate(sike):
                                        if i + 1 == ke_num:
                                            bi_yong_with_xia.append((ke_num, shang, x))
                                            break
                                result = self._she_hai_fa(bi_yong_with_xia, tiandi_pan, ri_gan, ri_zhi)
                                self.sanchuan_cache[cache_key] = result
                                return result
                            else:
                                chu_chuan = gan_ke_shang[0][2]
                        if not chu_chuan:
                            chu_chuan = yao_ke_results[0][2]

                    zhong_chuan = tiandi_pan[chu_chuan]
                    mo_chuan = tiandi_pan[zhong_chuan]

                    result = {
                        '初传': chu_chuan,
                        '中传': zhong_chuan,
                        '末传': mo_chuan,
                        '课体': '遥克课',
                        '起法': '遥克法'
                    }
                else:
                    # 无遥克：别责(四课不全) → 八专(干支同位) → 昴星(四课全无克贼)
                    if self._is_bie_ze(sike, ri_gan, ri_zhi):
                        result = self._bie_ze_fa(ri_gan, ri_zhi, tiandi_pan, sike)
                    elif is_ba_zhuan:
                        result = self._ba_zhuan_fa(ri_gan, ri_zhi, tiandi_pan, yang_ri)
                    else:
                        # 无克贼、无遥克、四课全 → 昴星法
                        result = self._ang_xing_fa(ri_gan, ri_zhi, tiandi_pan)

        # 识别附加课体课格（杜传、励德、元胎等）
        result = self._enrich_ke_ge(result, ri_gan, ri_zhi, tiandi_pan, sike, shi_chen)
        
        # 缓存结果
        self.sanchuan_cache[cache_key] = result
        return result
    
    def _she_hai_fa(self, bi_yong_results: List, tiandi_pan: Dict, ri_gan: str,
                    ri_zhi: str = '') -> Dict:
        """
        涉害法（完整规则）
        
        使用条件：
        1. 四课中有两课或以上相克（已通过贼克法判断）
        2. 比用后仍有多课（已通过比用法判断，但仍有多个候选）
        
        核心规则：
        - 取涉害深者为用
        - 涉害深度：从本位归原位，数经过的克位数量
        
        特殊格局：
        - 见机格：害深 > 3
        - 涉害课：害深 ≤ 3
        - 缀瑕格：害深相同，取先见者
        
        发用流程：
        1. 计算各候选的涉害深度
        2. 取涉害最深者
        3. 判断格局（见机/涉害/缀瑕）
        4. 确定初传
        5. 中传 = 初传的天盘
        6. 末传 = 中传的天盘
        """
        # 检查无比用的情况
        if len(bi_yong_results) == 0:
            # 无比用，返回空结果
            return {
                '初传': '', '中传': '', '末传': '',
                '课体': '涉害课', '起法': '涉害法',
                '涉害深度': 0, 'error': '无比用候选，无法起课'
            }
        
        # 1.5 【2026-09-10 移植·邵公古法】"干来加支即发用"
        #     涉害候选中，若第 3 课（支上）之上神 = 日干寄宫 且 下神 = 日支，
        #     直接取该课发用，不再计算涉害深度。
        #     原文依据：《断案》§交易谋为10·148 / §亡盗15·188「此课干来加支，即发用」
        #       （癸卯日课3 丑加卯：丑=癸寄、卯=支）；
        #       §六畜走失14·185「未加卯作龙为用」（己卯日课3 未加卯：未=己寄、卯=支）。
        if ri_zhi:
            for _ke_num, _shang, _xia in bi_yong_results:
                if (_ke_num == 3
                        and _shang == self.TIAN_GAN_JI_GONG.get(ri_gan, '')
                        and _xia == ri_zhi):
                    _c = _shang
                    _z = tiandi_pan.get(_c, '')
                    _m = tiandi_pan.get(_z, '')
                    return {
                        '初传': _c, '中传': _z, '末传': _m,
                        '课体': '涉害课', '起法': '涉害法·干来加支',
                        '涉害深度': 0,
                    }

        # 1. 计算每个候选的涉害深度
        hai_depths = []
        for ke_num, shang, xia in bi_yong_results:
            depth = self._calculate_she_hai_depth(shang, xia, tiandi_pan)
            hai_depths.append((ke_num, shang, xia, depth))

        # 1.9 【2026-09-11 立·同日憨爷拍板定口径】涉害取用两说：
        #   · 本门原著《仪度六壬选日要诀》：「涉害深浅相等则取孟」→ 深浅优先（**现默认**）。
        #   · 《注解大六壬指南》：「涉害取法，只以孟仲季为准，不以涉害深浅为义」→ 孟仲季优先。
        #   两说在本项目语料上仅差 1 案（断案 216 vs 217/218）→ 憨爷拍板依本门原著（深浅优先）。
        #   共同点：下神为天干者先转寄宫（Fix B）；孟(寅申巳亥)>仲(子午卯酉)>季(辰戌丑未)仅在深浅相等时裁决。
        #   治好了：《断案》§六畜走失14·186 甲辰（原=戌·午·寅）、赵林声 XJP-13（庚寄申）、新加坡回放 14/14。
        #     回退：环境变量 SHE_HAI_DEPTH_FIRST=1 切回「深浅优先」（仅对照实验用）。
        _meng = ['寅', '申', '巳', '亥']
        _zhong = ['子', '午', '卯', '酉']

        def _xia_pos(x):
            j = self.TIAN_GAN_JI_GONG.get(x, x)
            return 2 if j in _meng else (1 if j in _zhong else 0)

        _depth_first = __import__('os').getenv('SHE_HAI_DEPTH_FIRST', '0') == '1'
        if not _depth_first:
            _best_pos = max(_xia_pos(h[2]) for h in hai_depths)
            hai_depths = [h for h in hai_depths if _xia_pos(h[2]) == _best_pos]
        else:
            _best_pos = None

        # 2. 层内取涉害最深者
        max_depth = max(h[3] for h in hai_depths)
        deepest = [h for h in hai_depths if h[3] == max_depth]

        # 3. 判断格局
        if _best_pos == 0:
            # 俱在季位 → 缀瑕格（刚日干上神／柔日支上神）
            _deepest_all = deepest
            if ri_gan in ['甲', '丙', '戊', '庚', '壬']:
                _c = [c for c in _deepest_all if c[0] in [1, 2]] or _deepest_all
            else:
                _c = [c for c in _deepest_all if c[0] in [3, 4]] or _deepest_all
            chu_chuan = _c[0][1]
            ke_ti = '缀瑕格'
        elif len(deepest) == 1:
            # 层内唯一最深者
            chu_chuan = deepest[0][1]
            if _best_pos == 2:
                ke_ti = '见机格'
            elif _best_pos == 1:
                ke_ti = '察微格'
            else:
                # 未启用孟仲季优先（回退模式）：沿用旧判据
                ke_ti = '见机格' if max_depth > 3 else '涉害课'
        else:
            # 层内涉害深度仍相同，按孟仲季规则取
            # 寅申巳亥为孟，子午卯酉为仲，辰戌丑未为季
            meng = ['寅', '申', '巳', '亥']
            zhong = ['子', '午', '卯', '酉']
            ji = ['辰', '戌', '丑', '未']
            
            # 检查各候选的下神（地盘）是孟仲季
            meng_candidates = []
            zhong_candidates = []
            ji_candidates = []
            
            for ke_num, shang, xia, depth in deepest:
                # Fix B (Task#7)：孟仲季须按上神所加临之地盘判定；
                # 下神为天干(第一课/日干)时须转寄宫再比对（古籍：子加丙→子临巳(孟)）。
                xia_pos_z = self.TIAN_GAN_JI_GONG.get(xia, xia)
                if xia_pos_z in meng:
                    meng_candidates.append((ke_num, shang, xia, depth))
                elif xia_pos_z in zhong:
                    zhong_candidates.append((ke_num, shang, xia, depth))
                else:
                    ji_candidates.append((ke_num, shang, xia, depth))
            
            # 优先取孟上神发用（见机格）
            if meng_candidates:
                chu_chuan = meng_candidates[0][1]  # 取先见者
                ke_ti = '见机格'
            # 无孟，取仲发用（察微格）
            elif zhong_candidates:
                chu_chuan = zhong_candidates[0][1]  # 取先见者
                ke_ti = '察微格'
            # 俱在孟上或在仲季，刚日取日上神（一、二课），阴日取支上神（三、四课）发用（缀瑕格）
            else:
                # 按日干阴阳取
                if ri_gan in ['甲', '丙', '戊', '庚', '壬']:  # 阳日
                    # 取一、二课（日上神）
                    ri_shang_candidates = [c for c in deepest if c[0] in [1, 2]]
                    if ri_shang_candidates:
                        chu_chuan = ri_shang_candidates[0][1]
                    else:
                        chu_chuan = deepest[0][1]
                else:  # 阴日
                    # 取三、四课（支上神）
                    zhi_shang_candidates = [c for c in deepest if c[0] in [3, 4]]
                    if zhi_shang_candidates:
                        chu_chuan = zhi_shang_candidates[0][1]
                    else:
                        chu_chuan = deepest[0][1]
                ke_ti = '缀瑕格'
        
        # 4. 确定三传
        zhong_chuan = tiandi_pan[chu_chuan]  # 中传 = 初传的天盘
        mo_chuan = tiandi_pan[zhong_chuan]  # 末传 = 中传的天盘
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '课体': ke_ti,
            '起法': '涉害法',
            '涉害深度': max_depth
        }
    
    def _calculate_she_hai_depth(self, shang: str, xia: str, tiandi_pan: Dict) -> int:
        """
        计算涉害深度（核心算法）
        
        计算规则：
        1. 从四课下神(xia)出发
        2. 顺时针数到天盘上神本身的位置（不含）
        3. 只统计下贼上（地盘克天盘）
        4. 四季土(辰戌丑未)需计算寄宫天干的下贼上
        
        :param shang: 上神（天盘地支）
        :param xia: 下神（四课下神，起点）
        :param tiandi_pan: 天地盘对应关系
        :return: 涉害深度（经过的克位数）
        """
        # 生成缓存键
        tiandi_pan_key = "-".join([f"{k}:{v}" for k, v in sorted(tiandi_pan.items())])
        cache_key = f"{shang}:{xia}:{tiandi_pan_key}"
        
        # 检查缓存
        if cache_key in self.she_hai_depth_cache:
            return self.she_hai_depth_cache[cache_key]
        
        # 1. 从四课下神出发（如果下神是天干，转换成寄宫地支）
        if xia in self.TIAN_GAN_JI_GONG:
            start_pos = self.TIAN_GAN_JI_GONG[xia]
        else:
            start_pos = xia
        end_pos = shang  # 终点：上神本身的位置（不计）
        start_idx = self.DIZHI_INDEX[start_pos]
        shang_wuxing = self.DIZHI_WU_XING.get(shang, '')
        
        # 2. 顺行计数（只算下贼上）
        depth = 0
        count = 0
        while True:
            current_zhi = self.DIZHI[(start_idx + count) % 12]
            
            # 到达终点（不计）
            if current_zhi == end_pos and count > 0:
                break
            
            current_wuxing = self.DIZHI_WU_XING.get(current_zhi, '')
            
            # 只统计下贼上：地盘五行克上神五行
            if self.WU_XING_KE.get(current_wuxing) == shang_wuxing:
                depth += 1
            
            # 四季土寄宫天干的克（只算下贼上）
            if current_zhi in self.GAN_JI_GONG_WUXING_ALL:
                for ji_gong_wuxing in self.GAN_JI_GONG_WUXING_ALL[current_zhi]:
                    if self.WU_XING_KE.get(ji_gong_wuxing) == shang_wuxing:
                        depth += 1
            
            # 安全保护：最多数一圈
            if count > 12:
                break
            
            count += 1
        
        # 缓存结果
        self.she_hai_depth_cache[cache_key] = depth
        return depth
    
    def _ang_xing_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict) -> Dict:
        """
        昴星法
        规则：四课无克贼、无遥克，普通四课
        阳日取酉上，阴日取酉下
        【关键修正】中末传取法：
        - 阳日：中传取支上神，末传取干上神
        - 阴日：中传取干上神，末传取支上神
        """
        # 1. 确定初传
        if self.is_yang_ri(ri_gan):
            # 阳日：取地盘酉宫的上神
            chu_chuan = tiandi_pan['酉']
        else:
            # 阴日：取天盘酉宫的下神（地盘）
            for dizhi, tianpan in tiandi_pan.items():
                if tianpan == '酉':
                    chu_chuan = dizhi
                    break
        
        # 2. 中传和末传（关键修正：区分阴阳日）
        # 干上神：日干寄宫的天盘
        ri_gan_ji_gong = self.TIAN_GAN_JI_GONG[ri_gan]
        gan_shang = tiandi_pan[ri_gan_ji_gong]
        
        # 支上神：日支的天盘
        zhi_shang = tiandi_pan[ri_zhi]
        
        if self.is_yang_ri(ri_gan):
            # 阳日：中传取支上神，末传取干上神
            zhong_chuan = zhi_shang
            mo_chuan = gan_shang
        else:
            # 阴日：中传取干上神，末传取支上神
            zhong_chuan = gan_shang
            mo_chuan = zhi_shang
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '课体': '昴星课',
            '起法': '昴星法'
        }
    
    def _is_ba_zhuan(self, ri_gan: str, ri_zhi: str) -> bool:
        """
        判断是否为八专日
        八专日：日干寄宫与日支相同
        包括：甲寅、丙巳、戊巳、丁未、己未、庚申、辛戌、壬亥、癸丑
        """
        # 日干寄宫与日支相同即为八专课
        return self.TIAN_GAN_JI_GONG.get(ri_gan) == ri_zhi
    
    def _is_fu_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """
        判断是否为伏吟
        伏吟：天地盘相同，子加子、丑加丑...
        """
        for dizhi in self.DIZHI_WU_XING.keys():
            if tiandi_pan.get(dizhi) != dizhi:
                return False
        return True
    
    def _is_fan_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """
        判断是否为反吟
        反吟：天地盘对冲，子加午、丑加未...
        """
        for dizhi in self.DIZHI_WU_XING.keys():
            expected = self.LIU_CHONG.get(dizhi)
            if tiandi_pan.get(dizhi) != expected:
                return False
        return True
    
    def _is_bie_ze(self, sike: List[Tuple], ri_gan: str, ri_zhi: str = '') -> bool:
        """
        判断是否为别责格
        别责：四课中有两课相同（包括日干寄宫转换后），实际只有三课
        判定规则：日干要转换为寄宫地支后再比较
        Fix A：八专日(干支同位)四课仅两课，会被误判为不备→别责；
               八专为独立宗门，须从别责中互斥排除（据《六壬大全》p130
               "有上下克取克发用，无上下克不取遥克径用八专法"，八专与别责平行）。
        """
        # Fix A：八专为独立宗门，不参与别责判定
        if ri_zhi and self._is_ba_zhuan(ri_gan, ri_zhi):
            return False
        if len(sike) < 4:
            return False  # 四课不全是八专课，不是别责课
        
        # 检查任意两课是否相同（转换日干后）
        for i in range(len(sike)):
            for j in range(i + 1, len(sike)):
                ke1 = sike[i]
                ke2 = sike[j]
                
                # 上神比较
                if ke1[1] != ke2[1]:
                    continue
                
                # 下神比较：日干要转换为寄宫地支
                ke1_xia = ke1[2]
                ke2_xia = ke2[2]
                
                # 转换规则
                if ke1_xia == ri_gan:
                    ke1_xia = self.TIAN_GAN_JI_GONG[ri_gan]
                
                if ke2_xia == ri_gan:
                    ke2_xia = self.TIAN_GAN_JI_GONG[ri_gan]
                
                # 比较转换后的下神
                if ke1_xia == ke2_xia:
                    return True  # 找到两课相同，是别责课
        
        return False
    
    def _bie_ze_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, sike: List[Tuple] = None) -> Dict:
        """
        别责法（不备课规则）—【Task #4 修订 / 2026-09-11 柔日口径修正】据《六壬大全》别责门。

        古籍正例（本地原典 OCR + 赵林声手排 + 《断案》实测 四源印证）：
          - 阳日（刚日）：初传 = 天干五合之神的上神
                （日干合化之干，取该干寄宫地支的天盘上神）
          - 阴日（柔日）：初传 = 日支三合局「顺行下一位」的【地支本身】（不取上神）
                （申→子→辰 / 寅→午→戌 / 巳→酉→丑 / 亥→卯→未，恒 +4 位）
          - 中末传：皆取日干上神（日干寄宫的天盘）

        🔴 2026-09-11 修正：原实现取「四孟长生位的上神」（申子辰→申上神…），
           与古籍不符。铁证：
             ①《图解六壬大全》第1部 p131 别责课例二原文——
               「辛酉日子时亥将占…辛乃柔日，取三合前支为用，支三合乃巳酉丑，
                丑在酉前，即取丑为初传，中末俱用干上酉」（OCR 行 1595-1597）
             ②同书 p130 白话——「丑日越寅卯辰取巳为初传…未日越申酉戌取亥为初传」（行 1474-1476）
             ③《大全》卷一入手法歌诀「柔日支前三合取」（extracted_data/六壬大全_全文.json）
             ④赵林声《新加坡案例》手排：丁酉日→丑、辛未日→亥（与本式全合）
           旧引擎"课位置法"（阳不备取支上/阴不备取干上）亦与古籍不符，早已作废。
        注意：干合partner寄宫须用本项目标准 TIAN_GAN_JI_GONG（己→未，非丑）。
        """
        # 天干五合 → partner 寄宫（甲己化土、乙庚金、丙辛水、丁壬木、戊癸火）
        GAN_HE_JI_GONG = {
            '甲': self.TIAN_GAN_JI_GONG['己'],  # 甲合己 → 未
            '乙': self.TIAN_GAN_JI_GONG['庚'],  # 乙合庚 → 申
            '丙': self.TIAN_GAN_JI_GONG['辛'],  # 丙合辛 → 戌
            '丁': self.TIAN_GAN_JI_GONG['壬'],  # 丁合壬 → 亥
            '戊': self.TIAN_GAN_JI_GONG['癸'],  # 戊合癸 → 丑
            '己': self.TIAN_GAN_JI_GONG['甲'],  # 己合甲 → 寅
            '庚': self.TIAN_GAN_JI_GONG['乙'],  # 庚合乙 → 辰
            '辛': self.TIAN_GAN_JI_GONG['丙'],  # 辛合丙 → 巳
            '壬': self.TIAN_GAN_JI_GONG['丁'],  # 壬合丁 → 未
            '癸': self.TIAN_GAN_JI_GONG['戊'],  # 癸合戊 → 巳
        }
        # 地支三合局「顺行下一位」= 支前三合：生→旺→墓→生，恒 +4 位
        # 《图解六壬大全》第1部 p131「支三合乃巳酉丑，丑在酉前，即取丑为初传」
        SAN_HE_QIAN = {
            '申': '子', '子': '辰', '辰': '申',   # 申子辰 → 申→子→辰
            '寅': '午', '午': '戌', '戌': '寅',   # 寅午戌 → 寅→午→戌
            '巳': '酉', '酉': '丑', '丑': '巳',   # 巳酉丑 → 巳→酉→丑
            '亥': '卯', '卯': '未', '未': '亥',   # 亥卯未 → 亥→卯→未
        }
        gan_ji = self.TIAN_GAN_JI_GONG[ri_gan]
        gan_shang = tiandi_pan[gan_ji]   # 日干上神（中末传）
        yang_ri = self.is_yang_ri(ri_gan)
        if yang_ri:
            chu_chuan = tiandi_pan[GAN_HE_JI_GONG[ri_gan]]
        else:
            # 柔日：取日支三合局顺行下一位的【地支本身】（不取天盘上神）
            chu_chuan = SAN_HE_QIAN[ri_zhi]
        return {
            '初传': chu_chuan,
            '中传': gan_shang,
            '末传': gan_shang,
            '课体': '别责课',
            '起法': '别责法',
            '阴阳日': '阳日（刚日·干合上神）' if yang_ri else '阴日（柔日·支前三合）',
            '起课规则': '干合上神/支前三合'
        }
    
    def _ba_zhuan_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, yang_ri: bool) -> Dict:
        """
        八专法
        规则：干支同位，四课只有两课
        
        起课原则（传统规则 - 永久固定，据《六壬大全》p130"中末总向日上眠"）：
        - 阳日：取日上神（日干寄宫的天盘）顺数第三位为初传
        - 阴日：取第四课上神（支上神的上神）逆数第三位为初传
        - 中传：皆用日干上神（日干寄宫的天盘）
        - 末传：皆用日干上神（日干寄宫的天盘）
        
        顺数/逆数说明：
        - 顺数：从本地支开始，顺时针数到目标位置（包括自己）
        - 逆数：从本地支开始，逆时针数到目标位置（包括自己）
        - 例如：从申顺数第三位 = 申→酉→戌 = 戌
        - 例如：从戌逆数第三位 = 戌→酉→申 = 申
        """
        # 地支顺序
        DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 日干寄宫
        ji_gong = self.TIAN_GAN_JI_GONG[ri_gan]
        
        if yang_ri:
            # 阳日：取日上神顺数第三位
            ri_shang = tiandi_pan[ji_gong]  # 日上神
            ri_shang_index = DIZHI.index(ri_shang)
            chu_chuan_index = (ri_shang_index + 2) % 12  # 顺数第三位（包括自己）
            chu_chuan = DIZHI[chu_chuan_index]
        else:
            # 阴日：取第四课上神逆数第三位
            zhi_shang = tiandi_pan[ri_zhi]  # 支上神
            zhi_shang_shang = tiandi_pan[zhi_shang]  # 第四课上神（支上神的上神）
            zhi_shang_shang_index = DIZHI.index(zhi_shang_shang)
            chu_chuan_index = (zhi_shang_shang_index - 2) % 12  # 逆数第三位
            chu_chuan = DIZHI[chu_chuan_index]
        
        # 中传：日干上神（日干寄宫的天盘）——"中末总向日上眠"
        zhong_chuan = tiandi_pan[ji_gong]
        
        # 末传：日干上神（日干寄宫的天盘）——"中末总向日上眠"
        mo_chuan = tiandi_pan[ji_gong]
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '课体': '八专课',
            '起法': '八专法'
        }
    
    def _fu_yin_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, sike: List) -> Dict:
        """
        伏吟法（完整规则 - 修正版）
        规则：月将与占时相同，天地盘位置重叠（伏吟）
        
        起课顺序：
        1. 若第一课有贼克，仍依贼克法发用
        2. 柔日（阴日）：取支上神为发用
        3. 刚日（阳日）：取日上神为发用
        4. 中传取初传所刑之神
        5. 末传取中传所刑之神
        6. 特殊情况：
           - 初传自刑：以支上神为中传
           - 中传亦自刑：末传取中传所冲之神
        """
        # 1. 检查第一课是否有贼克
        ke_results = []
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.is_ke(shang, xia, ri_gan)
            if ke_type:
                ke_results.append((i + 1, ke_type, shang, xia))
        
        # 2. 有贼克，依贼克法处理
        if len(ke_results) == 1:
            # 只有一课克贼
            chu_chuan = ke_results[0][2]
            
            # 【伏吟课关键修正】中末传不取天盘，而取刑冲
            # 伏吟课天地盘相同，取天盘等于取本身，会导致三传全同
            # 正确：中传取初传所刑，末传取中传所刑
            
            # 计算刑冲（修正：丑未戌三刑的正确顺序）
            xing_map = {
                '子': '卯', '卯': '子',
                '寅': '巳', '巳': '申', '申': '寅',
                '丑': '戌', '戌': '未', '未': '丑',  # 修正：丑→戌→未→丑
                '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'
            }
            
            chong_map = {
                '子': '午', '午': '子',
                '丑': '未', '未': '丑',
                '寅': '申', '申': '寅',
                '卯': '酉', '酉': '卯',
                '辰': '戌', '戌': '辰',
                '巳': '亥', '亥': '巳'
            }
            
            zi_xing = ['辰', '午', '酉', '亥']  # 自刑
            
            # 中传取初传所刑
            zhong_chuan = xing_map.get(chu_chuan, chu_chuan)
            if chu_chuan in zi_xing:
                # 初传自刑，以支上神为中传
                zhi_shang = tiandi_pan[ri_zhi]
                zhong_chuan = zhi_shang
            
            # 末传取中传所刑
            mo_chuan = xing_map.get(zhong_chuan, zhong_chuan)
            if zhong_chuan in zi_xing:
                # 中传自刑，末传取中传所冲
                mo_chuan = chong_map.get(zhong_chuan, zhong_chuan)
            elif mo_chuan == chu_chuan:
                # 【关键修正】末传刑回初传，不能回头刑，改用冲
                mo_chuan = chong_map.get(zhong_chuan, zhong_chuan)
            
            ke_ti = '不虞格'
            
            return {
                '初传': chu_chuan,
                '中传': zhong_chuan,
                '末传': mo_chuan,
                '课体': ke_ti,
                '起法': '伏吟法（有贼克）'
            }
        
        elif len(ke_results) > 1:
            # 多课克贼，用比用法
            yang_ri = self.is_yang_ri(ri_gan)
            bi_yong_results = []
            for ke_num, ke_type, shang, xia in ke_results:
                if yang_ri and self.is_yang_zhi(shang):
                    bi_yong_results.append((ke_num, shang, xia))
                elif not yang_ri and not self.is_yang_zhi(shang):
                    bi_yong_results.append((ke_num, shang, xia))
            
            if len(bi_yong_results) >= 1:
                chu_chuan = bi_yong_results[0][1]
                
                # 【伏吟课关键修正】中末传不取天盘，而取刑冲
                # 计算刑冲（修正：丑未戌三刑的正确顺序）
                xing_map = {
                    '子': '卯', '卯': '子',
                    '寅': '巳', '巳': '申', '申': '寅',
                    '丑': '戌', '戌': '未', '未': '丑',  # 修正：丑→戌→未→丑
                    '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'
                }
                
                chong_map = {
                    '子': '午', '午': '子',
                    '丑': '未', '未': '丑',
                    '寅': '申', '申': '寅',
                    '卯': '酉', '酉': '卯',
                    '辰': '戌', '戌': '辰',
                    '巳': '亥', '亥': '巳'
                }
                
                zi_xing = ['辰', '午', '酉', '亥']  # 自刑
                
                # 中传取初传所刑
                zhong_chuan = xing_map.get(chu_chuan, chu_chuan)
                if chu_chuan in zi_xing:
                    # 初传自刑，以支上神为中传
                    zhi_shang = tiandi_pan[ri_zhi]
                    zhong_chuan = zhi_shang
                
                # 末传取中传所刑
                mo_chuan = xing_map.get(zhong_chuan, zhong_chuan)
                if zhong_chuan in zi_xing:
                    # 中传自刑，末传取中传所冲
                    mo_chuan = chong_map.get(zhong_chuan, zhong_chuan)
                
                return {
                    '初传': chu_chuan,
                    '中传': zhong_chuan,
                    '末传': mo_chuan,
                    '课体': '不虞格',
                    '起法': '伏吟法（有贼克）'
                }
        
        # 3. 无贼克，根据刚柔日起课
        yang_ri = self.is_yang_ri(ri_gan)
        
        if not yang_ri:
            # 柔日（阴日）：取支上神为发用
            zhi_shang = tiandi_pan.get(ri_zhi, ri_zhi)
            chu_chuan = zhi_shang
        else:
            # 刚日（阳日）：取日上神（第一课上神）为发用
            if len(sike) >= 1:
                chu_chuan = sike[0][1]  # 第一课上神（日上神）
            else:
                chu_chuan = ri_zhi  # 备用
        
        # 4. 计算刑冲（修正：丑未戌三刑的正确顺序）
        xing_map = {
            '子': '卯', '卯': '子',
            '寅': '巳', '巳': '申', '申': '寅',
            '丑': '戌', '戌': '未', '未': '丑',  # 修正：丑→戌→未→丑
            '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'
        }
        
        chong_map = {
            '子': '午', '午': '子',
            '丑': '未', '未': '丑',
            '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰',
            '巳': '亥', '亥': '巳'
        }
        
        zi_xing = ['辰', '午', '酉', '亥']  # 自刑
        
        # 5. 中传取法
        # 【2026-09-10 修复】初传自刑时，中传须取「另一课」之上神，分刚柔日：
        #   刚日初传取干上神 → 自刑则改取支上神；
        #   柔日初传取支上神 → 自刑则改取干上神。
        #   原实现「不分阴阳日」一律取支上神 → 柔日时支上神 = 初传本身，
        #   致中传与初传重复、末传退化为取冲。
        #   实证：§官讼16·212（辛酉日 丑将丑时，柔日伏吟无克）
        #     原文三传 酉/戌/未（初传酉=支上神且自刑 → 中传取干上神戌 → 末传戌刑未）；
        #     原实现给 酉/酉/卯。
        if chu_chuan in zi_xing:
            if yang_ri:
                # 刚日：初传=干上神，自刑 → 中传取支上神
                zhong_chuan = tiandi_pan.get(ri_zhi, ri_zhi)
            else:
                # 柔日：初传=支上神，自刑 → 中传取干上神
                zhong_chuan = tiandi_pan.get(
                    self.TIAN_GAN_JI_GONG.get(ri_gan, ri_gan), ri_gan)
        else:
            # 初传不自刑：中传取初传所刑
            zhong_chuan = xing_map.get(chu_chuan, chu_chuan)
        
        # 6. 末传取法（关键修正：按《六壬大全》规则）
        if zhong_chuan in zi_xing:
            # 中传自刑，末传取中传所冲
            mo_chuan = chong_map.get(zhong_chuan, zhong_chuan)
        else:
            # 中传不是自刑，末传取中传所刑
            mo_chuan = xing_map.get(zhong_chuan, zhong_chuan)
            # 防回头刑：末传刑回初传，改用冲
            if mo_chuan == chu_chuan:
                mo_chuan = chong_map.get(zhong_chuan, zhong_chuan)
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '课体': '伏吟课',
            '起法': '伏吟法'
        }
    
    def _fan_yin_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, sike: List) -> Dict:
        """
        反吟法（完整规则 - 按用户提供的标准）
        
        反吟课起课规则：
        1. 有贼克：按贼克法、比用法、涉害法发用（不用遥克）
           - 初传：克处（有克贼的上神）
           - 中传：初传之上神（天盘）
           - 末传：中传之上神（天盘）
           - 此为无依格
        
        2. 无贼克：井栏射格（无亲格）
           - 《六壬大全》规定：辛未、辛丑、丁丑、己丑四日反吟课
           - 初传：驿马（巳酉丑日马在亥，亥卯未日马在巳）
           - 中传：支上神
           - 末传：干上神（日干寄宫的天盘）
        """
        # Fix C：八专+反吟 课按反吟法处理（反吟优先于八专），由下方正常反吟逻辑
        #        计算真实三传；不再返回空三传/错误标签（原退化分支会产出空三传）。
        # 1. 检查贼克
        ke_results = []
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.is_ke(shang, xia, ri_gan)
            if ke_type:
                ke_results.append((i + 1, ke_type, shang, xia))
        
        # 2. 有贼克，按贼克法发用（不用遥克）
        if len(ke_results) > 0:
            # 取第一课有克贼的
            first_ke = ke_results[0]
            chu_chuan = first_ke[2]  # 克处（上神）
            
            # 中传：初传之上神（天盘）
            zhong_chuan = tiandi_pan.get(chu_chuan, chu_chuan)
            
            # 末传：中传之上神（天盘）
            mo_chuan = tiandi_pan.get(zhong_chuan, zhong_chuan)
            
            return {
                '初传': chu_chuan,
                '中传': zhong_chuan,
                '末传': mo_chuan,
                '课体': '反吟课',
                '起法': '反吟法（有贼克）',
                '格局': '无依格'
            }
        
        # 3. 无贼克，井栏射格（无亲格）
        # 《六壬大全》：辛未、辛丑、丁丑、己丑四日反吟课，以驿马为用
        # 驿马规则：以日支查驿马
        # 巳酉丑日马在亥，申子辰日马在寅，亥卯未日马在巳，寅午戌日马在申
        yi_ma = {
            '巳': '亥', '酉': '亥', '丑': '亥',  # 巳酉丑日，驿马在亥
            '申': '寅', '子': '寅', '辰': '寅',  # 申子辰日，驿马在寅
            '亥': '巳', '卯': '巳', '未': '巳',  # 亥卯未日，驿马在巳
            '寅': '申', '午': '申', '戌': '申'   # 寅午戌日，驿马在申
        }
        
        # 初传：日支驿马
        chu_chuan = yi_ma.get(ri_zhi, ri_zhi)
        
        # 中传：支上神（第三课的上神）
        zhong_chuan = sike[2][1]  # 第三课的上神
        
        # 末传：干上神（第一课的上神，即日干寄宫的天盘）
        mo_chuan = sike[0][1]  # 第一课的上神
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '课体': '反吟课',
            '起法': '反吟法',
            '格局': '井栏格（无亲格）'
        }
    
class SiKeSanChuanCalculator2(SiKeSanChuanCalculator):
    """
    四课三传计算器V2 — 三步决策架构

    基于 collect_info() → decide_method() → execute_method() 标准流程
    继承 SiKeSanChuanCalculator，复用所有方法实现，仅重写决策流程

    修复清单:
    ─────────────────────────────────────────────
    Bug 1: 别责在顶层优先于贼克法 → 移至无克贼无遥克分支
    Bug 2: 无克贼分支中遥克法应优先于八专/别责
    Bug 3: _she_hai_fa 空候选崩溃 (line 605 IndexError)
    Bug 4: 遥克法比用后无比用结果时正确处理
    ─────────────────────────────────────────────
    """

    def fa_sanchuan(self, sike: List[Tuple], ri_gan: str, ri_zhi: str,
                    tiandi_pan: Dict[str, str], shi_chen: str = None) -> Dict[str, str]:
        """
        发三传 — 三步决策架构

        流程:
        1. _collect_info()  — 收集四课克贼/遥克/课体信息
        2. _decide_method() — 按宗门九课优先级决策起课法
        3. _execute_method() — 执行对应起课法计算三传
        """
        info = self._collect_info(sike, ri_gan, ri_zhi, tiandi_pan)
        method = self._decide_method(info)
        result = self._execute_method(method, info, tiandi_pan)

        # 附加课体课格识别
        result = self._enrich_ke_ge(result, ri_gan, ri_zhi, tiandi_pan, sike, shi_chen)

        # 反吟课体标记: 反吟有贼克/遥克时，课体应包含"反吟"
        if info['is_fan_yin'] and method != '反吟法':
            current_ke_ti = result.get('课体', '')
            if '反吟' not in current_ke_ti:
                if current_ke_ti:
                    result['课体'] = f'反吟{current_ke_ti}'
                else:
                    result['课体'] = '反吟课'

        return result

    def _collect_info(self, sike: List[Tuple], ri_gan: str, ri_zhi: str,
                      tiandi_pan: Dict[str, str]) -> Dict:
        """收集决策所需的所有信息"""
        yang_ri = self.is_yang_ri(ri_gan)

        # 检查特殊课体
        is_fu_yin = self._is_fu_yin(tiandi_pan)
        is_fan_yin = self._is_fan_yin(tiandi_pan)
        is_ba_zhuan = self._is_ba_zhuan(ri_gan, ri_zhi)

        # 检查四课克贼
        ke_results = []
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.is_ke(shang, xia, ri_gan)
            if ke_type:
                ke_results.append((i + 1, ke_type, shang, xia))

        # 【2026-09-10 修复】《断案》"不可重复取用"：四课中若有两课上下神全同（重复课），
        #   该课不得作为发用（邵先生："干支阴阳已先据其位……不可重复取用"）。
        #   实证 §宅墓02·007（乙巳日 戌将亥时）：第一课 卯/乙(寄辰) 与第四课 卯/辰 全同，
        #   第四课 卯木克辰土 被判"上克下"，原实现直接取其为发用 → 元首课 卯/寅/丑；
        #   原文评："术人多以第四课发用为元首，传用已差……当以日遥克为用，卦名弹射"
        #   → 正解为不备课遥克弹射，三传 辰/卯/寅。
        #   ⚠️ 必须在下方"遥克计算"之前执行 —— 遥克判定带 `if not ke_results` 前置条件，
        #      若放在其后，排除后 ke_results 变空也不会补算遥克，会误入别责法。
        #
        #   ⛔ 2026-09-10 查《大全》后**判定此解法方向错误，默认停用**
        #      （环境变量 DUP_LESSON_FILTER=1 可启用，仅供对照）：
        #
        #      《疏正》§宅墓02·007 原文关键句："今第一课卯加辰，卯，木，**辰内乙亦木，不克**"
        #        —— 原书认为"卯加辰"**根本不构成克**（辰是乙的寄宫，辰内是乙木，与卯木同类）。
        #        故本案四课**本无克贼**，自然走遥克弹射 → 辰/卯/寅，**无需"排除重复课"**。
        #
        #      真正的根因在**判克规则**：当日干寄宫支作为某课下神时（第四课常见，
        #        因"支阴"下神即支上神之天盘位），判克应回退到**日干本气**而非该支五行。
        #        → 待实现：is_ke 需感知"下神 == 日干寄宫支 ⇒ 用日干本气"。
        #      "排除重复课"是错误解法，实测净负：B1 99.5% → 97.6%，
        #        且把 262 期三传由 亥/午/丑（原判）改成 午/丑/申（结构相同即触发，误伤）。
        import os as _os
        dup_nums = set()
        if _os.getenv('DUP_LESSON_FILTER', '0') == '1':
            dup_nums = self._duplicate_lesson_nums(sike, ri_gan, ri_zhi)
            if dup_nums and ke_results:
                ke_results = [k for k in ke_results if k[0] not in dup_nums]

        # 检查别责（四课中有两课相同）；Fix A：八专日已互斥排除
        is_bie_ze = self._is_bie_ze(sike, ri_gan, ri_zhi)

        # 检查遥克（无克贼时上神与日干相克）
        yao_ke_results = []
        if not ke_results:
            for i, (name, shang, xia, _) in enumerate(sike):
                shang_wuxing = self.DIZHI_WU_XING.get(shang, '')
                ri_wuxing = self.TIAN_GAN_WU_XING.get(ri_gan, '')
                if not shang_wuxing or not ri_wuxing:
                    continue
                if self.WU_XING_KE.get(shang_wuxing) == ri_wuxing:
                    yao_ke_results.append((i + 1, '上克干', shang, xia))
                elif self.WU_XING_KE.get(ri_wuxing) == shang_wuxing:
                    yao_ke_results.append((i + 1, '干克上', shang, xia))

        return {
            'sike': sike,
            'ri_gan': ri_gan,
            'ri_zhi': ri_zhi,
            'tiandi_pan': tiandi_pan,
            'yang_ri': yang_ri,
            'is_fu_yin': is_fu_yin,
            'is_fan_yin': is_fan_yin,
            'is_ba_zhuan': is_ba_zhuan,
            'is_bie_ze': is_bie_ze,
            'dup_lesson_nums': dup_nums,
            'ke_results': ke_results,
            'yao_ke_results': yao_ke_results,
        }

    def _duplicate_lesson_nums(self, sike: List[Tuple], ri_gan: str,
                               ri_zhi: str = '') -> set:
        """不备课·「干阳与支阴重复」→ 该两课不可重复取用。

        【判据来源】《大六壬断案疏正》§宅墓02·007 评疏（p.38，刘科乐注）：
          "支阴与干阳相同，干阳为先……**支阴被干阳占据，不能重复取用**，
           因此，应遵循遥克法发用……**这种特殊的取用法则，只发生在少数不备课中**。
           余如辛酉日辛上亥、乙酉日乙上亥、戊寅日干上申亦准此例。
           此占，乙为柔日，先尽支阴，干阳不备。"

        【精确范围】只判 **第一课（干阳）与第四课（支阴）** 上下神是否全同 ——
        不涉及第二课/第三课（那是"支课重复"，不属此例）。

        ⚠️ 2026-09-10 教训：曾错误泛化为"任意两课全同即排除"，
        致 §宅墓02·037（庚戌日，第二课=第三课）被改错（原书三传 子/寅/辰
        被改成 寅/辰/午），B1 从 99.0% 掉到 96.6%。收窄到本判据后恢复正常。
        """
        if not sike or len(sike) < 4:
            return set()
        # 八专日（干支同位）四课本只两课、天然两两重复，属独立宗门，不适用
        if ri_zhi and self._is_ba_zhuan(ri_gan, ri_zhi):
            return set()

        def _norm(xia):
            # 第一课下神为日干，须换算寄宫支（如乙→辰）方能与第四课比对
            return self.TIAN_GAN_JI_GONG.get(xia, xia) if xia in self.TIAN_GAN_WU_XING else xia

        l1 = (sike[0][1], _norm(sike[0][2]))      # 第一课 上神/下神（干阳）
        l4 = (sike[3][1], _norm(sike[3][2]))      # 第四课 上神/下神（支阴）
        return {1, 4} if l1 == l4 else set()

    def _decide_method(self, info: Dict) -> str:
        """
        按宗门九课优先级决策起课法

        完整优先级:
        1. 伏吟法 — 月将=占时（天地盘相同，无克贼可能）
        2. 贼克法 — 四课有克贼（反吟有贼克也用贼克法）
        3. 遥克法 — 无克贼，上神与日干相克（反吟有遥克也用遥克法）
        4. 反吟法 — 反吟且无克贼无遥克
        5. 八专法 — 干支同位（无克贼无遥克）
        6. 别责法 — 四课相同（无克贼无遥克）
        7. 昴星法 — 普通四课，无克贼无遥克

        注意: 反吟是课体特征而非起课法
        反吟有贼克 → 贼克法（课体标反吟）
        反吟无贼克有遥克 → 遥克法（课体标反吟）
        反吟无贼克无遥克 → 反吟法
        """
        # 1. 伏吟法优先（天地盘相同，贼克法无法使用）
        if info['is_fu_yin']:
            return '伏吟法'

        ke_results = info['ke_results']
        yao_ke_results = info['yao_ke_results']

        # 2. 有克贼 → 贼克法（别责课有克贼时仍用贼克法）
        if ke_results:
            return '贼克法'

        # 2.5 【2026-09-10 移植·原文实证】八专日无克 → 径用八专法，不参与遥克
        #     原文依据：《六壬大全》八专门「有上下克取克发用，无上下克不取遥克径用八专法」。
        #     缺陷实证：原判定序把八专放在遥克之后（见下方 is_ba_zhuan 分支），
        #     八专日一旦被判出"遥克"即被遥克法抢先收走 ——
        #     §财产08·133（己未日亥将酉时）四课酉亥酉亥，干克上（蒿矢）被遥克分支误收，
        #     致独足课 酉/酉/酉 被排成遥克 亥/丑/卯（《断案疏正》评疏明列独足课四例之一）。
        #     A/B（218 古例，PY3.12+PYTHONHASHSEED=0）：
        #       JSON 基准 82.6% → 99.0%；PDF 直提基准 80.4% → 96.7%；
        #       且原主引擎算对的 171 案无一回归。
        if info['is_ba_zhuan']:
            return '八专法'

        # 3. 无克贼，有遥克 → 遥克法
        if yao_ke_results:
            return '遥克法'

        # 4. 无克贼无遥克 → 反吟优先于别责
        #    【Task #3 修正】原序为"别责(L1413)→反吟(L1417)"，致反吟+不备课被错归别责。
        #    天地盘相冲(反吟)是比四课不备(别责)更强的结构态，须先于别责判定；
        #    反吟有克/遥克已在上方贼克/遥克分支收走，此处仅承接"反吟且无克无遥"。
        if info['is_fan_yin']:
            return '反吟法'

        # 5. 无克贼无遥克，四课不全 → 别责法（已排除反吟/伏吟/八专）
        if info['is_bie_ze']:
            return '别责法'

        if info['is_ba_zhuan']:
            return '八专法'

        return '昴星法'

    def _execute_method(self, method: str, info: Dict, tiandi_pan: Dict) -> Dict:
        """执行决策出的起课法，计算三传"""
        sike = info['sike']
        ri_gan = info['ri_gan']
        ri_zhi = info['ri_zhi']
        yang_ri = info['yang_ri']
        ke_results = info['ke_results']
        yao_ke_results = info['yao_ke_results']

        if method == '伏吟法':
            return self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)

        if method == '反吟法':
            return self._fan_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)

        if method == '贼克法':
            return self._execute_zei_ke(ke_results, ri_gan, ri_zhi, tiandi_pan, yang_ri)

        if method == '遥克法':
            return self._execute_yao_ke(yao_ke_results, ri_gan, ri_zhi, tiandi_pan, yang_ri, sike)

        if method == '八专法':
            return self._ba_zhuan_fa(ri_gan, ri_zhi, tiandi_pan, yang_ri)

        if method == '别责法':
            return self._bie_ze_fa(ri_gan, ri_zhi, tiandi_pan, sike)

        if method == '昴星法':
            return self._ang_xing_fa(ri_gan, ri_zhi, tiandi_pan)

        return {'初传': '', '中传': '', '末传': '', '课体': '', '起法': method, 'error': f'未知起课法: {method}'}

    def _execute_zei_ke(self, ke_results: List, ri_gan: str, ri_zhi: str,
                        tiandi_pan: Dict, yang_ri: bool) -> Dict:
        """
        贼克法 — 含比用+涉害完整链

        标准流程:
        1. 贼（下贼上）优先于克（上克下）
        2. 多个候选 → 比用（阳日取阳支上神，阴日取阴支上神）
        3. 比用后仍有多候选 → 涉害法
        4. 比用后无候选 → 取原候选中的第一个
        """
        # 分优先级：下贼上 > 上克下
        zei = [(k, s, x) for k, t, s, x in ke_results if t == '贼']
        ke = [(k, s, x) for k, t, s, x in ke_results if t == '克']

        # 【2026-09-10 修复·课体命名】九宗门课体须按「候选数量」定名：
        #   单个下贼上 → 重审课；单个上克下 → 元首课；
        #   **两个及以上**同类克贼 → **知一课（比用课）**（须比用，取与日干阴阳比者）。
        #   原实现只按"贼/克"二分，不论候选数量一律标"重审课/元首课" →
        #   218 古例中主课体与原文一致率仅 17.5%（而三传匹配 99.5%，因取用结果相同）。
        #   实证：§宅墓02·010（庚寅日寅将酉时）两贼（未/寅、子/未）→ 原文标"知一"，
        #   原实现标"重审课"。
        #   ⚠️ 本改动**只改课体名，不参与取用**（取用仍走比用/涉害），故三传不变、零风险。
        #   ⚠️ 若后续比用后仍多候选而走涉害法，课体由涉害法覆盖（见机/察微/缀瑕/涉害课）。
        if zei:
            candidates = zei
            ke_ti = '重审课' if len(zei) == 1 else '知一课'
        else:
            candidates = ke
            ke_ti = '元首课' if len(ke) == 1 else '知一课'

        # 比用
        bi_yong = []
        for ke_num, shang, xia in candidates:
            if yang_ri and self.is_yang_zhi(shang):
                bi_yong.append((ke_num, shang, xia))
            elif not yang_ri and not self.is_yang_zhi(shang):
                bi_yong.append((ke_num, shang, xia))

        use_candidates = bi_yong if bi_yong else candidates

        if len(use_candidates) == 1:
            chu_chuan = use_candidates[0][1]
            zhong_chuan = tiandi_pan[chu_chuan]
            mo_chuan = tiandi_pan[zhong_chuan]
            return {
                '初传': chu_chuan, '中传': zhong_chuan, '末传': mo_chuan,
                '课体': ke_ti, '起法': '贼克法'
            }

        # 多候选 → 涉害法
        return self._she_hai_fa(use_candidates, tiandi_pan, ri_gan, ri_zhi)

    def _execute_yao_ke(self, yao_ke_results: List, ri_gan: str, ri_zhi: str,
                        tiandi_pan: Dict, yang_ri: bool, sike: List) -> Dict:
        """
        遥克法 — 含比用+涉害完整链

        标准流程:
        1. 上克干优先于干克上
        2. 多个候选 → 比用（阳日取阳支上神，阴日取阴支上神）
        3. 比用后仍有多候选 → 涉害法
        4. 比用后无候选 → 取原候选中的第一个
        """
        shang_ke_gan = [(k, t, s, x) for k, t, s, x in yao_ke_results if t == '上克干']
        gan_ke_shang = [(k, t, s, x) for k, t, s, x in yao_ke_results if t == '干克上']

        if shang_ke_gan:
            candidates = shang_ke_gan
        else:
            candidates = gan_ke_shang

        if len(candidates) == 1:
            # Fix A (Task#7)：yao_ke_results 元组=(ke_num,type,shang,xia)，
            # 初传必为上神(shang, 索引2)，原[3]=下神(xia)为 BUG（古籍：遥克初传必为四课上神）。
            chu_chuan = candidates[0][2]
            zhong_chuan = tiandi_pan[chu_chuan]
            mo_chuan = tiandi_pan[zhong_chuan]
            return {
                '初传': chu_chuan, '中传': zhong_chuan, '末传': mo_chuan,
                '课体': '遥克课', '起法': '遥克法'
            }

        # 比用
        bi_yong = []
        for ke_num, ke_type, shang, xia in candidates:
            if yang_ri and self.is_yang_zhi(shang):
                bi_yong.append((ke_num, shang, xia))
            elif not yang_ri and not self.is_yang_zhi(shang):
                bi_yong.append((ke_num, shang, xia))

        use_candidates = bi_yong if bi_yong else [(k, s, x) for k, t, s, x in candidates]

        if len(use_candidates) == 1:
            chu_chuan = use_candidates[0][1]
        else:
            # 多候选 → 涉害法
            result = self._she_hai_fa(use_candidates, tiandi_pan, ri_gan, ri_zhi)
            if result.get('error'):
                chu_chuan = use_candidates[0][1]
                zhong_chuan = tiandi_pan[chu_chuan]
                mo_chuan = tiandi_pan[zhong_chuan]
                return {
                    '初传': chu_chuan, '中传': zhong_chuan, '末传': mo_chuan,
                    '课体': '遥克课', '起法': '遥克法'
                }
            return result

        zhong_chuan = tiandi_pan[chu_chuan]
        mo_chuan = tiandi_pan[zhong_chuan]
        return {
            '初传': chu_chuan, '中传': zhong_chuan, '末传': mo_chuan,
            '课体': '遥克课', '起法': '遥克法'
        }

    def calculate(self, ri_gan: str, ri_zhi: str, yue_jiang: str,
                  shi_chen: str) -> Dict:
        """
        完整排盘接口 — 四课+三传一站式计算

        参数:
            ri_gan: 日干（甲~癸）
            ri_zhi: 日支（子~亥）
            yue_jiang: 月将（子~亥）
            shi_chen: 占时（子~亥）

        返回:
            {
                'tiandi_pan': {地盘: 天盘, ...},
                'sike': [(课名, 上神, 下神, 天将), ...],
                'sanchuan': {'初传': str, '中传': str, '末传': str, ...},
                'ri_gan': str,
                'ri_zhi': str,
                'yue_jiang': str,
                'shi_chen': str
            }
        """
        tiandi_pan = self.get_tiandi_pan(yue_jiang, shi_chen)
        sike = self.qi_sike(ri_gan, ri_zhi, tiandi_pan)
        sanchuan = self.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan, shi_chen)

        return {
            'tiandi_pan': tiandi_pan,
            'sike': sike,
            'sanchuan': sanchuan,
            'ri_gan': ri_gan,
            'ri_zhi': ri_zhi,
            'yue_jiang': yue_jiang,
            'shi_chen': shi_chen,
        }


# 修复 _she_hai_fa 中的空候选bug（修补父类方法）
def _patched_she_hai_fa(self, bi_yong_results, tiandi_pan, ri_gan, ri_zhi=''):
    """
    涉害法（修复版）- 修复空候选崩溃bug

    Bug: 原版 line 605-607 在 bi_yong_results 为空时
    试图访问 bi_yong_results[0][2]，导致 IndexError
    """
    if len(bi_yong_results) == 0:
        return {
            '初传': '',
            '中传': '',
            '末传': '',
            '课体': '涉害课',
            '起法': '涉害法',
            '涉害深度': 0,
            'error': '无比用候选，无法起课'
        }

    # 1.5 【2026-09-10 移植·邵公古法】"干来加支即发用"（与类内 _she_hai_fa 同规则）
    #     第 3 课（支上）上神 = 日干寄宫 且 下神 = 日支 → 径取该课发用。
    #     原文依据：《断案》§交易谋为10·148 / §亡盗15·188 / §六畜走失14·185。
    if ri_zhi:
        for _ke_num, _shang, _xia in bi_yong_results:
            if (_ke_num == 3
                    and _shang == self.TIAN_GAN_JI_GONG.get(ri_gan, '')
                    and _xia == ri_zhi):
                _c = _shang
                _z = tiandi_pan.get(_c, '')
                _m = tiandi_pan.get(_z, '')
                return {
                    '初传': _c, '中传': _z, '末传': _m,
                    '课体': '涉害课', '起法': '涉害法·干来加支',
                    '涉害深度': 0,
                }

    # 1. 计算每个候选的涉害深度
    hai_depths = []
    for ke_num, shang, xia in bi_yong_results:
        depth = self._calculate_she_hai_depth(shang, xia, tiandi_pan)
        hai_depths.append((ke_num, shang, xia, depth))

    # 1.9 【2026-09-11 立·同日憨爷拍板定口径】同类内 _she_hai_fa：
    #   默认＝深浅优先（本门原著《仪度六壬选日要诀》「深浅相等则取孟」）；
    #   孟仲季(孟>仲>季)仅在深浅相等时裁决，下神天干先转寄宫（Fix B 同步）。
    #   回退：环境变量 SHE_HAI_MENG_ZHONG_JI_FIRST=1 切《指南》孟仲季优先口径（对照实验用）。
    _meng = ['寅', '申', '巳', '亥']
    _zhong = ['子', '午', '卯', '酉']

    def _xia_pos(x):
        j = self.TIAN_GAN_JI_GONG.get(x, x)
        return 2 if j in _meng else (1 if j in _zhong else 0)

    _mzj_first = __import__('os').getenv('SHE_HAI_MENG_ZHONG_JI_FIRST', '0') == '1'
    if _mzj_first:
        _best_pos = max(_xia_pos(h[2]) for h in hai_depths)
        hai_depths = [h for h in hai_depths if _xia_pos(h[2]) == _best_pos]
    else:
        _best_pos = None

    # 2. 层内取涉害最深者
    max_depth = max(h[3] for h in hai_depths)
    deepest = [h for h in hai_depths if h[3] == max_depth]

    # 3. 判断格局
    if _best_pos == 0:
        # 俱在季位 → 缀瑕格（刚日干上神／柔日支上神）
        if ri_gan in ['甲', '丙', '戊', '庚', '壬']:
            _c = [c for c in deepest if c[0] in [1, 2]] or deepest
        else:
            _c = [c for c in deepest if c[0] in [3, 4]] or deepest
        chu_chuan = _c[0][1]
        ke_ti = '缀瑕格'
    elif len(deepest) == 1:
        chu_chuan = deepest[0][1]
        if _best_pos == 2:
            ke_ti = '见机格'
        elif _best_pos == 1:
            ke_ti = '察微格'
        else:
            ke_ti = '见机格' if max_depth > 3 else '涉害课'
    else:
        meng = ['寅', '申', '巳', '亥']
        zhong = ['子', '午', '卯', '酉']
        ji = ['辰', '戌', '丑', '未']

        meng_candidates = []
        zhong_candidates = []
        ji_candidates = []

        for ke_num, shang, xia, depth in deepest:
            # Fix B 同步：下神为天干时先转寄宫（模块级补丁此前漏掉，导致 XJP-13 误判）
            xz = self.TIAN_GAN_JI_GONG.get(xia, xia)
            if xz in meng:
                meng_candidates.append((ke_num, shang, xia, depth))
            elif xz in zhong:
                zhong_candidates.append((ke_num, shang, xia, depth))
            else:
                ji_candidates.append((ke_num, shang, xia, depth))

        if meng_candidates:
            chu_chuan = meng_candidates[0][1]
            ke_ti = '见机格'
        elif zhong_candidates:
            chu_chuan = zhong_candidates[0][1]
            ke_ti = '察微格'
        else:
            if ri_gan in ['甲', '丙', '戊', '庚', '壬']:
                ri_shang_candidates = [c for c in deepest if c[0] in [1, 2]]
                if ri_shang_candidates:
                    chu_chuan = ri_shang_candidates[0][1]
                else:
                    chu_chuan = deepest[0][1]
            else:
                zhi_shang_candidates = [c for c in deepest if c[0] in [3, 4]]
                if zhi_shang_candidates:
                    chu_chuan = zhi_shang_candidates[0][1]
                else:
                    chu_chuan = deepest[0][1]
            ke_ti = '缀瑕格'

    # 4. 确定三传
    zhong_chuan = tiandi_pan[chu_chuan]
    mo_chuan = tiandi_pan[zhong_chuan]

    return {
        '初传': chu_chuan,
        '中传': zhong_chuan,
        '末传': mo_chuan,
        '课体': ke_ti,
        '起法': '涉害法',
        '涉害深度': max_depth
    }


# 注：原始 _she_hai_fa 中的空候选bug已在源头上修复（第605-607行），
# 此补丁保留作为额外的安全防护
SiKeSanChuanCalculator._she_hai_fa = _patched_she_hai_fa
