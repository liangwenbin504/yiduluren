"""
四课三传计算引擎
实现大六壬四课起法和三传九种法则
"""

from typing import Dict, List, Tuple, Optional


class SiKeSanChuanCalculator:
    """四课三传计算器"""
    
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
    
    def __init__(self):
        pass
    
    def get_tiandi_pan(self, yuejiang: str, shichen: str) -> Dict[str, str]:
        """获取天地盘对应关系"""
        from utils.dizhi_layout_generator import arrange_tiandi_pan
        return arrange_tiandi_pan(yuejiang, shichen)
    
    def get_tian_jiang_pan(self, ri_gan: str, tiandi_pan: Dict[str, str], shi_chen: str = None) -> Dict[str, str]:
        """
        获取天将盘（天盘地支 → 天将名）
        
        :param ri_gan: 日干
        :param tiandi_pan: 天地盘
        :param shi_chen: 占时（可选，用于判断昼夜）
        :return: 天将映射字典 {天盘地支：天将名}
        """
        try:
            from engine.gui_ren_engine import GuiRenCalculator
        except ImportError:
            from gui_ren_engine import GuiRenCalculator
        
        gui_ren_calc = GuiRenCalculator()
        
        # 准备天盘数据（需要包含天地对应关系）
        tian_pan_data = {
            '天地对应': tiandi_pan
        }
        
        # 计算贵人盘（包含天将）
        gui_ren_result = gui_ren_calc.arrange_gui_ren_pan(ri_gan, tian_pan_data, shi_chen)
        
        # 返回天将映射
        return gui_ren_result.get('天将映射', {})
    
    def qi_sike(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict[str, str], *, shi_chen: str = None) -> List[Tuple[str, str, str, str]]:
        """
        起四课
        返回：[(课名，上神，下神，上神天将), ...]
        
        参数说明：
        - ri_gan: 日干
        - ri_zhi: 日支
        - tiandi_pan: 天地盘
        - shi_chen: 占时（可选，用于计算天将，关键字参数）
        """
        # 计算天将盘
        tian_jiang_map = self.get_tian_jiang_pan(ri_gan, tiandi_pan, shi_chen)
        
        sike = []
        
        # 第一课：日干上神
        # 日干寄宫，看寄宫天盘是什么
        ji_gong = self.TIAN_GAN_JI_GONG[ri_gan]
        gan_shang = tiandi_pan[ji_gong]  # 寄宫的天盘
        gan_shang_tian_jiang = tian_jiang_map.get(gan_shang, '')
        sike.append(('第一课', gan_shang, ri_gan, gan_shang_tian_jiang))
        
        # 第二课：干上神的上神
        # 看 gan_shang 这个地支的天盘
        gan_shang_shang = tiandi_pan[gan_shang]
        gan_shang_shang_tian_jiang = tian_jiang_map.get(gan_shang_shang, '')
        sike.append(('第二课', gan_shang_shang, gan_shang, gan_shang_shang_tian_jiang))
        
        # 第三课：日支上神
        zhi_shang = tiandi_pan[ri_zhi]
        zhi_shang_tian_jiang = tian_jiang_map.get(zhi_shang, '')
        sike.append(('第三课', zhi_shang, ri_zhi, zhi_shang_tian_jiang))
        
        # 第四课：支上神的上神
        zhi_shang_shang = tiandi_pan[zhi_shang]
        zhi_shang_shang_tian_jiang = tian_jiang_map.get(zhi_shang_shang, '')
        sike.append(('第四课', zhi_shang_shang, zhi_shang, zhi_shang_shang_tian_jiang))
        
        return sike
    
    def is_ke(self, shang: str, xia: str) -> str:
        """
        判断是否相克
        返回：'克'（上克下），'贼'（下贼上），''（无克）
        
        注意：
        - 上神总是地支，用 DIZHI_WU_XING
        - 下神可能是天干（第一课）或地支（其他课）
        - 天干用 TIAN_GAN_WU_XING，地支用 DIZHI_WU_XING
        """
        shang_wuxing = self.DIZHI_WU_XING.get(shang, '')
        
        # 判断下神是天干还是地支
        if xia in self.TIAN_GAN_WU_XING:
            xia_wuxing = self.TIAN_GAN_WU_XING.get(xia, '')
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
    
    def fa_sanchuan(self, sike: List[Tuple], ri_gan: str, ri_zhi: str, 
                    tiandi_pan: Dict[str, str]) -> Dict[str, str]:
        """
        发三传
        返回：{'初传': str, '中传': str, '末传': str, '课体': str, '起法': str}
        
        九种发用法则顺序：
        1. 贼克法  2. 比用法  3. 涉害法  4. 遥克法  5. 昂星法
        6. 别责法  7. 八专法  8. 伏吟法  9. 反吟法
        """
        yang_ri = self.is_yang_ri(ri_gan)
        
        # 检查是否为八专日（干支同位）
        is_ba_zhuan = self._is_ba_zhuan(ri_gan, ri_zhi)
        
        # 检查是否为伏吟（天地盘相同）
        is_fu_yin = self._is_fu_yin(tiandi_pan)
        
        # 检查是否为反吟（天地盘对冲）
        is_fan_yin = self._is_fan_yin(tiandi_pan)
        
        # 1. 贼克法
        ke_results = []
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.is_ke(shang, xia)
            if ke_type:
                ke_results.append((i + 1, ke_type, shang, xia))
        
        if len(ke_results) == 1:
            # 只有一课克贼
            # 【关键修正】伏吟课优先于八专课
            if is_fu_yin:
                # 伏吟课有贼克，也要用伏吟法的中末传规则
                return self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
            
            # 【关键修正】八专课只有在无贼克时才用，有贼克用贼克法
            # 非伏吟课，用贼克法
            chu_chuan = ke_results[0][2]
            zhong_chuan = tiandi_pan[chu_chuan]
            mo_chuan = tiandi_pan[zhong_chuan]
            
            if ke_results[0][1] == '克':
                ke_ti = '元首课'
            else:
                ke_ti = '重审课'
            
            return {
                '初传': chu_chuan,
                '中传': zhong_chuan,
                '末传': mo_chuan,
                '三传': [chu_chuan, zhong_chuan, mo_chuan],
                '课体': ke_ti,
                '起法': '贼克法'
            }
        
        elif len(ke_results) > 1:
            # 2. 比用法
            # 【关键修正】伏吟课优先于八专课
            if is_fu_yin:
                # 伏吟课有多课克贼，也要用伏吟法的中末传规则
                return self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
            
            # 【关键修正】八专课只有在无贼克时才用，有贼克用贼克法/比用法/涉害法
            # 不再判断八专课，直接用比用法/涉害法
            
            # 【关键修正】多课克贼，先分优先级：下贼上 > 上克下
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
                    
                    return {
                        '初传': chu_chuan,
                        '中传': zhong_chuan,
                        '末传': mo_chuan,
                        '三传': [chu_chuan, zhong_chuan, mo_chuan],
                        '课体': '重审课',
                        '起法': '贼克法（下贼上）'
                    }
                else:
                    # 多个下贼上，需要比用
                    # 【有比用比原则】先比较阴阳，阴阳相同再比较数值大小
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
                        
                        return {
                            '初传': chu_chuan,
                            '中传': zhong_chuan,
                            '末传': mo_chuan,
                            '三传': [chu_chuan, zhong_chuan, mo_chuan],
                            '课体': '重审课',
                            '起法': '贼克法（下贼上）'
                        }
                    elif len(bi_yong_results) > 1:
                        # 【关键修正】比用后仍有多课，用涉害法（不是比较数值）
                        return self._she_hai_fa([(k, s, x) for k, s, x in bi_yong_results], tiandi_pan, ri_gan)
                    else:
                        # 【关键修正】比用后无符合，不是取先见者，而是用涉害法！
                        # 格式：(课次，上神，下神)
                        return self._she_hai_fa([(k, s, x) for k, _, s, x in xia_zei_shang], tiandi_pan, ri_gan)
            else:
                # 无下贼上，处理上克下
                if len(shang_ke_xia) == 1:
                    # 只有一个上克下，直接取用
                    chu_chuan = shang_ke_xia[0][2]
                    zhong_chuan = tiandi_pan[chu_chuan]
                    mo_chuan = tiandi_pan[zhong_chuan]
                    
                    return {
                        '初传': chu_chuan,
                        '中传': zhong_chuan,
                        '末传': mo_chuan,
                        '三传': [chu_chuan, zhong_chuan, mo_chuan],
                        '课体': '元首课',
                        '起法': '贼克法（上克下）'
                    }
                else:
                    # 多个上克下，需要比用
                    # 【有比用比原则】与下贼上同理，先比较阴阳，阴阳相同再比较数值
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
                        
                        return {
                            '初传': chu_chuan,
                            '中传': zhong_chuan,
                            '末传': mo_chuan,
                            '三传': [chu_chuan, zhong_chuan, mo_chuan],
                            '课体': '元首课',
                            '起法': '贼克法（上克下，比用）'
                        }
                    elif len(bi_yong_results) > 1:
                        # 【关键修正】比用后仍有多课，用涉害法（不是比较数值）
                        she_hai_result = self._she_hai_fa([(k, s, x) for k, s, x in bi_yong_results], tiandi_pan, ri_gan)
                        return she_hai_result
                    else:
                        # 【关键修正】比用后无符合，不是取先见者，而是用涉害法！
                        # 格式：(课次，上神，下神)
                        return self._she_hai_fa([(k, s, x) for k, _, s, x in shang_ke_xia], tiandi_pan, ri_gan)
        
        # 4. 遥克法
        # 【关键修正】伏吟课优先于八专课
        if is_fu_yin:
            return self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
        
        if is_ba_zhuan:
            return self._ba_zhuan_fa(ri_gan, ri_zhi, tiandi_pan, yang_ri)
        
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
                        # 比用后仍有多课，用涉害法
                        bi_yong_with_xia = []
                        for ke_num, shang in bi_yong_results:
                            # 找到对应的下神
                            for i, (name, s, x, _) in enumerate(sike):
                                if i + 1 == ke_num:
                                    bi_yong_with_xia.append((ke_num, shang, x))
                                    break
                        # 调用涉害法
                        she_hai_result = self._she_hai_fa(bi_yong_with_xia, tiandi_pan, ri_gan)
                        return she_hai_result
                    else:
                        # 比用后无符合，取先见者
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
                        # 比用后仍有多课，用涉害法
                        bi_yong_with_xia = []
                        for ke_num, shang in bi_yong_results:
                            # 找到对应的下神
                            for i, (name, s, x, _) in enumerate(sike):
                                if i + 1 == ke_num:
                                    bi_yong_with_xia.append((ke_num, shang, x))
                                    break
                        # 调用涉害法
                        she_hai_result = self._she_hai_fa(bi_yong_with_xia, tiandi_pan, ri_gan)
                        return she_hai_result
                    else:
                        # 比用后无符合，取先见者
                        chu_chuan = gan_ke_shang[0][2]
                if not chu_chuan:
                    chu_chuan = yao_ke_results[0][2]
            
            zhong_chuan = tiandi_pan[chu_chuan]
            mo_chuan = tiandi_pan[zhong_chuan]
            
            return {
                '初传': chu_chuan,
                '中传': zhong_chuan,
                '末传': mo_chuan,
                '三传': [chu_chuan, zhong_chuan, mo_chuan],
                '课体': '遥克课',
                '起法': '遥克法'
            }
        
        # 无遥克，检查特殊格局
        # 【关键修正】反吟法优先于别责法
        # 5. 八专课（无贼克、无遥克时）
        if is_ba_zhuan:
            return self._ba_zhuan_fa(ri_gan, ri_zhi, tiandi_pan, yang_ri)
        
        # 6. 伏吟课
        if is_fu_yin:
            return self._fu_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
        
        # 7. 反吟法（天地盘对冲）- 优先于别责
        if is_fan_yin:
            return self._fan_yin_fa(ri_gan, ri_zhi, tiandi_pan, sike)
        
        # 8. 别责法（四课无克贼、无遥克，第一课与第四课相同）
        if self._is_bie_ze(sike, ri_gan):
            return self._bie_ze_fa(ri_gan, ri_zhi, tiandi_pan)
        
        # 9. 默认昂星法
        return self._ang_xing_fa(ri_gan, ri_zhi, tiandi_pan)
    
    def _she_hai_fa(self, bi_yong_results: List, tiandi_pan: Dict, ri_gan: str) -> Dict:
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
            # 无比用，取第一课
            return self._ang_xing_fa(ri_gan, bi_yong_results[0][2] if bi_yong_results else '子', tiandi_pan)
        
        # 1. 计算每个候选的涉害深度
        hai_depths = []
        for ke_num, shang, xia in bi_yong_results:
            # 计算涉害深度：从本位归原位，数克位数量
            depth = self._calculate_she_hai_depth(shang, tiandi_pan)
            hai_depths.append((ke_num, shang, xia, depth))
        
        # 2. 取涉害最深者
        max_depth = max(h[3] for h in hai_depths)
        deepest = [h for h in hai_depths if h[3] == max_depth]
        
        # 3. 判断格局
        if len(deepest) == 1:
            # 只有一个最深者
            chu_chuan = deepest[0][1]
            # 害深 > 3 为见机格，否则为涉害课
            ke_ti = '见机格' if max_depth > 3 else '涉害课'
        else:
            # 涉害深度相同，按孟仲季规则取
            # 寅申巳亥为孟，子午卯酉为仲，辰戌丑未为季
            meng = ['寅', '申', '巳', '亥']
            zhong = ['子', '午', '卯', '酉']
            ji = ['辰', '戌', '丑', '未']
            
            # 检查各候选的下神（地盘）是孟仲季
            meng_candidates = []
            zhong_candidates = []
            ji_candidates = []
            
            for ke_num, shang, xia, depth in deepest:
                if xia in meng:
                    meng_candidates.append((ke_num, shang, xia, depth))
                elif xia in zhong:
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
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
            '课体': ke_ti,
            '起法': '涉害法',
            '涉害深度': max_depth
        }
    
    def _calculate_she_hai_depth(self, shang: str, tiandi_pan: Dict) -> int:
        """
        计算涉害深度（核心算法）- 修正版
        
        计算规则：
        1. 找到天盘上神落地盘的位置（天盘加临位）- 起点
        2. 从该位置顺时针数到天盘上神本身的位置（不含）- 终点不计
        3. 统计经过的位置中，所有相克的五行数量
        
        核心修正：统计所有相克，包含"我克者"（上克下）和"克我者"（下贼上）
        
        例如：天盘酉落地盘巳位
        从巳位顺时针数到酉位（不含）：巳→午→未→申
        统计这段路径上所有与酉（金）相克的五行：
          - 巳：巳火✓ + 丙火✓ = 2（火克金）
          - 午：午火✓ = 1（火克金）
          - 未：未土× + 丁火✓ = 1（丁火克金）
          - 申：申金× = 0（比和）
          - 涉害深度：4
        
        五行生克：
        - 金克木，木克土，土克水，水克火，火克金
        - 统计"我克者"（上神克地盘）和"克我者"（地盘克上神）
        
        注意事项：
        - 起点计入，终点不计
        - 比和者（五行相同）不计为克位
        - 必须顺时针数
        - 地支本气和天干寄宫分别计数
        
        :param shang: 上神（天盘地支）
        :param tiandi_pan: 天地盘对应关系
        :return: 涉害深度（经过的克位数）
        """
        # 1. 找到天盘上神落地盘的位置（起点）
        start_pos = None
        for dizhi, tianpan in tiandi_pan.items():
            if tianpan == shang:
                start_pos = dizhi
                break
        if start_pos is None:
            start_pos = shang  # 默认情况
        
        # 2. 确定终点：天盘上神本身的位置（终点不计）
        end_pos = shang  # 天盘上神本身的地支位置
        
        # 3. 从起始位顺数到终点位，统计克位（包含天干寄宫）
        depth = 0
        dizhi_order = self.DIZHI_WU_XING.keys()
        dizhi_list = list(dizhi_order)
        
        start_idx = dizhi_list.index(start_pos)  # 起始位索引
        shang_wuxing = self.DIZHI_WU_XING.get(shang, '')  # 上神五行
        
        # 天干寄宫的五行（用于计算寄天干的克）
        # 大六壬天干寄宫规则：甲寅、乙辰、丙戊巳、丁己未、庚申、辛戌、壬亥、癸丑
        gan_ji_gong_wuxing_all = {
            '寅': ['木'],  # 甲
            '辰': ['木'],  # 乙
            '巳': ['火', '土'],  # 丙、戊
            '未': ['火', '土'],  # 丁、己
            '申': ['金'],  # 庚
            '戌': ['金'],  # 辛（戌中只寄辛金）
            '亥': ['水'],  # 壬
            '丑': ['水'],  # 癸（丑中只寄癸水）
        }
        
        # 4. 顺行计数
        count = 0
        while True:
            current_zhi = dizhi_list[(start_idx + count) % 12]
            
            # 到达终点（不计）
            if current_zhi == end_pos and count > 0:
                break
            
            current_wuxing = self.DIZHI_WU_XING.get(current_zhi, '')
            
            # 5. 统计所有相克（包含"我克者"和"克我者"）
            ke_count = 0
            
            # a) 地支本气的克
            # 下贼上（克我者）：地支五行克上神五行
            if self.WU_XING_KE.get(current_wuxing) == shang_wuxing:
                ke_count += 1
            # 上克下（我克者）：上神五行克地支五行
            elif self.WU_XING_KE.get(shang_wuxing) == current_wuxing:
                ke_count += 1
            
            # b) 天干寄宫的克
            if current_zhi in gan_ji_gong_wuxing_all:
                for ji_gong_wuxing in gan_ji_gong_wuxing_all[current_zhi]:
                    # 下贼上（克我者）：天干寄宫五行克上神五行
                    if self.WU_XING_KE.get(ji_gong_wuxing) == shang_wuxing:
                        ke_count += 1
                    # 上克下（我克者）：上神五行克天干寄宫五行
                    elif self.WU_XING_KE.get(shang_wuxing) == ji_gong_wuxing:
                        ke_count += 1
            
            # 累加克位数量
            depth += ke_count
            
            # 安全保护：最多数一圈
            if count > 12:
                break
            
            count += 1
        
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
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
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
    
    def _is_bie_ze(self, sike: List[Tuple], ri_gan: str) -> bool:
        """
        判断是否为别责格
        别责：四课中有两课相同（包括日干寄宫转换后），实际只有三课
        判定规则：日干要转换为寄宫地支后再比较
        """
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
    
    def _bie_ze_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict) -> Dict:
        """
        别责法（传统规则 - 永久固定）
        规则：四课中有两课相同（包括日干寄宫转换后），实际只有三课
        
        起课原则：
        - 阳日：取干合上神为初传（日干五合之天干的寄宫位置的天盘）
        - 阴日：取支前三合为初传（三合局的前一位）
        - 中传：皆取日干上神（日干寄宫的天盘）
        - 末传：皆取日干上神（与中传相同）
        """
        # 阴阳日判定
        yang_ri_gan = ['甲', '丙', '戊', '庚', '壬']
        
        if ri_gan in yang_ri_gan:
            # 阳日：取干合上神
            wu_he_map = {
                '甲': '己', '己': '甲',
                '乙': '庚', '庚': '乙',
                '丙': '辛', '辛': '丙',
                '丁': '壬', '壬': '丁',
                '戊': '癸', '癸': '戊'
            }
            he_gan = wu_he_map[ri_gan]
            
            # 五合天干的寄宫
            ji_gong = self.TIAN_GAN_JI_GONG[he_gan]
            
            # 寄宫的天盘为初传
            chu_chuan = tiandi_pan[ji_gong]
            
            rule = '干合上神'
        else:
            # 阴日：取支前三合（《六壬大全》规则）
            # 规则：三合局按顺时针排列（长生→帝旺→墓库），取日支顺时针的下一个
            # 例如：酉的三合局是巳→酉→丑（顺时针），从酉顺时针下一个是丑
            zhi_san_he_qian = {
                # 寅午戌三合：寅→午→戌（顺时针）
                '寅': '午',  # 从寅顺时针下一个是午
                '午': '戌',  # 从午顺时针下一个是戌
                '戌': '寅',  # 从戌顺时针下一个是寅
                # 亥卯未三合：亥→卯→未（顺时针）
                '亥': '卯',  # 从亥顺时针下一个是卯
                '卯': '未',  # 从卯顺时针下一个是未
                '未': '亥',  # 从未顺时针下一个是亥
                # 申子辰三合：申→子→辰（顺时针）
                '申': '子',  # 从申顺时针下一个是子
                '子': '辰',  # 从子顺时针下一个是辰
                '辰': '申',  # 从辰顺时针下一个是申
                # 巳酉丑三合：巳→酉→丑（顺时针）
                '巳': '酉',  # 从巳顺时针下一个是酉
                '酉': '丑',  # 从酉顺时针下一个是丑 ✓
                '丑': '巳'   # 从丑顺时针下一个是巳
            }
            chu_chuan = zhi_san_he_qian[ri_zhi]
            rule = '支前三合'
        
        # 中传、末传皆用日干上神（日干寄宫的天盘）
        ri_gan_shang = tiandi_pan[self.TIAN_GAN_JI_GONG[ri_gan]]
        zhong_chuan = ri_gan_shang
        mo_chuan = ri_gan_shang
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
            '课体': '别责课',
            '起法': '别责法',
            '阴阳日': '阳日' if ri_gan in yang_ri_gan else '阴日',
            '起课规则': rule
        }
    
    def _ba_zhuan_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, yang_ri: bool) -> Dict:
        """
        八专法
        规则：干支同位，四课只有两课
        
        起课原则（传统规则 - 永久固定）：
        - 阳日：取日上神（日干寄宫的天盘）顺数第三位为初传
        - 阴日：取第四课上神（支上神的上神）逆数第三位为初传
        - 中传：皆用日支上神
        - 末传：皆用日支上神
        
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
        
        # 中传：日支上神
        zhong_chuan = tiandi_pan[ri_zhi]
        
        # 末传：日支上神
        mo_chuan = tiandi_pan[ri_zhi]
        
        return {
            '初传': chu_chuan,
            '中传': zhong_chuan,
            '末传': mo_chuan,
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
            '课体': '八专课',
            '起法': '八专法'
        }
    
    def _fu_yin_fa(self, ri_gan: str, ri_zhi: str, tiandi_pan: Dict, sike: List) -> Dict:
        """
        伏吟法（完整规则 - 修正版）
        规则：月将与占时相同，天地盘位置重叠（伏吟）
        
        起课顺序：
        1. 若第一课有贼克，仍依贼克法发用
        2. 柔日（阴日）：取辰上神为发用
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
            ke_type = self.is_ke(shang, xia)
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
            
            if ke_results[0][1] == '克':
                ke_ti = '元首课'
            else:
                ke_ti = '重审课'
            
            return {
                '初传': chu_chuan,
                '中传': zhong_chuan,
                '末传': mo_chuan,
                '三传': [chu_chuan, zhong_chuan, mo_chuan],
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
                    '三传': [chu_chuan, zhong_chuan, mo_chuan],
                    '课体': '比用课',
                    '起法': '伏吟法（有贼克）'
                }
        
        # 3. 无贼克，根据刚柔日起课
        yang_ri = self.is_yang_ri(ri_gan)
        
        if not yang_ri:
            # 柔日（阴日）：取辰上神（第四课上神）为发用
            if len(sike) >= 4:
                chu_chuan = sike[3][1]  # 第四课上神
            else:
                chu_chuan = ri_zhi  # 备用
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
        
        # 5. 中传取法（关键修正：按《六壬大全》规则）
        zhong_chuan = xing_map.get(chu_chuan, chu_chuan)
        if chu_chuan in zi_xing:
            # 【关键修正】初传自刑，按阴阳日取中传
            # 《六壬大全》：阳日取支上神，阴日取干上神
            if yang_ri:
                # 阳日：取支上神（第三课上神）
                zhi_shang = tiandi_pan[ri_zhi]
                zhong_chuan = zhi_shang
            else:
                # 阴日：取干上神（第一课上神，日干寄宫的天盘）
                ri_gan_ji_gong = self.TIAN_GAN_JI_GONG.get(ri_gan, ri_zhi)
                gan_shang = tiandi_pan[ri_gan_ji_gong]
                zhong_chuan = gan_shang
        
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
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
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
        
        3. 特别备注：丁未、己未二课列入八专课，不适用反吟法
        """
        # 特别备注：丁未、己未属于八专课（干支同位）
        if (ri_gan == '丁' and ri_zhi == '未') or (ri_gan == '己' and ri_zhi == '未'):
            # 应该由八专法处理，这里返回错误
            return {
                '初传': '',
                '中传': '',
                '末传': '',
                '课体': '八专课',
                '起法': '反吟法（错误：应为八专课）',
                'error': '丁未、己未日属于八专课，不适用反吟法'
            }
        
        # 1. 检查贼克
        ke_results = []
        for i, (name, shang, xia, _) in enumerate(sike):
            ke_type = self.is_ke(shang, xia)
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
                '三传': [chu_chuan, zhong_chuan, mo_chuan],
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
            '三传': [chu_chuan, zhong_chuan, mo_chuan],
            '课体': '反吟课',
            '起法': '反吟法',
            '格局': '井栏格（无亲格）'
        }
    
    def get_tian_jiang_for_chuan(self, chuan: str, ri_gan: str, tiandi_pan: Dict[str, str], shi_chen: str = None) -> str:
        """获取三传的天将"""
        tian_jiang_map = self.get_tian_jiang_pan(ri_gan, tiandi_pan, shi_chen)
        return tian_jiang_map.get(chuan, '')
