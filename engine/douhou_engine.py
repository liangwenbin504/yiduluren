"""
斗首择日计算引擎
实现山家五行、天干化气、番化五行等核心功能
"""

from data.constants import (
    TIANGAN, DIZHI, TWENTY_FOUR_MOUNTAINS,
    SHANJIA_WUXING, TIANGAN_HUAQI, DOUSHOU_FIVE_STARS,
    WUXING_SHENG, WUXING_KE
)


class DouShouCalculator:
    """斗首择日计算器"""
    
    def __init__(self):
        self.shanjia_wuxing = SHANJIA_WUXING
        self.tiangan_huaqi = TIANGAN_HUAQI
    
    def get_shanjia_wuxing(self, mountain: str) -> str:
        """
        获取山家五行
        :param mountain: 二十四山
        :return: 五行属性
        """
        return self.shanjia_wuxing.get(mountain, '未知')
    
    def get_tiangan_huaqi(self, tiangan: str) -> str:
        """
        获取天干化气五行
        :param tiangan: 天干
        :return: 化气五行
        """
        return self.tiangan_huaqi.get(tiangan, '未知')
    
    def get_wuxing_sheng(self, wuxing: str) -> str:
        """
        获取五行所生
        :param wuxing: 五行
        :return: 所生之五行
        """
        return WUXING_SHENG.get(wuxing, '未知')
    
    def get_wuxing_ke(self, wuxing: str) -> str:
        """
        获取五行所克
        :param wuxing: 五行
        :return: 所克之五行
        """
        return WUXING_KE.get(wuxing, '未知')
    
    def calculate_fanhua_wuxing(self, base_wuxing: str, star: str) -> str:
        """
        计算番化五行（通过元辰、武财、贪官等五星二次转化）
        根据资料：元辰化元辰、武财化贪官等
        :param base_wuxing: 基础五行
        :param star: 星名（元辰、武财、贪官、廉贞、破鬼）
        :return: 番化后的五行
        """
        # 番化规则（根据传统斗首理论）
        fanhua_rules = {
            '元辰': base_wuxing,  # 元辰化元辰（不变）
            '武财': self._get_fanhua_result(base_wuxing, '武财'),
            '贪官': self._get_fanhua_result(base_wuxing, '贪官'),
            '廉贞': self._get_fanhua_result(base_wuxing, '廉贞'),
            '破鬼': self._get_fanhua_result(base_wuxing, '破鬼')
        }
        return fanhua_rules.get(star, base_wuxing)
    
    def _get_fanhua_result(self, wuxing: str, star: str) -> str:
        """
        获取番化结果
        根据斗首理论：武财化贪官、贪官化廉贞等
        """
        # 五行相生顺序：木→火→土→金→水→木
        sheng_order = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        
        if star == '武财':
            # 武财化贪官（我克者为财，财生官）
            return sheng_order.get(self.get_wuxing_ke(wuxing), wuxing)
        elif star == '贪官':
            # 贪官化廉贞
            return sheng_order.get(wuxing, wuxing)
        elif star == '廉贞':
            # 廉贞化破鬼
            return self.get_wuxing_ke(wuxing)
        elif star == '破鬼':
            # 破鬼化元辰
            return wuxing
        return wuxing
    
    def calculate_douhou_stars(self, mountain: str, tiangan: str) -> dict:
        """
        计算斗首五星配置
        根据山家和天干化气确定元辰、武财、贪官等
        :param mountain: 山向（二十四山）
        :param tiangan: 天干
        :return: 五星配置字典
        """
        shanjia_wx = self.get_shanjia_wuxing(mountain)
        huaqi_wx = self.get_tiangan_huaqi(tiangan)
        
        # 元辰：与山家五行相同者
        # 武财：我克者为财
        # 贪官：克我者为官鬼
        # 廉贞：我生者为子孙
        # 破鬼：生我者为父母
        
        stars = {
            '元辰': shanjia_wx,
            '武财': self.get_wuxing_ke(shanjia_wx),
            '贪官': self._get_ke_wo(shanjia_wx),
            '廉贞': self.get_wuxing_sheng(shanjia_wx),
            '破鬼': self._get_sheng_wo(shanjia_wx)
        }
        
        return {
            '山家五行': shanjia_wx,
            '化气五行': huaqi_wx,
            '五星配置': stars,
            '日元天干': tiangan
        }
    
    def _get_ke_wo(self, wuxing: str) -> str:
        """获取克我者"""
        for key, value in WUXING_KE.items():
            if value == wuxing:
                return key
        return '未知'
    
    def _get_sheng_wo(self, wuxing: str) -> str:
        """获取生我者"""
        for key, value in WUXING_SHENG.items():
            if value == wuxing:
                return key
        return '未知'
    
    def analyze_douhou_day(self, mountain: str, year_tiangan: str, month_tiangan: str,
                             day_tiangan: str, hour_tiangan: str) -> dict:
        """
        分析斗首日课吉凶
        :param mountain: 山向
        :param year_tiangan: 年天干
        :param month_tiangan: 月天干
        :param day_tiangan: 日天干
        :param hour_tiangan: 时天干
        :return: 分析结果
        """
        result = {
            '山向': mountain,
            '四柱天干': {
                '年': year_tiangan,
                '月': month_tiangan,
                '日': day_tiangan,
                '时': hour_tiangan
            },
            '山家五行': self.get_shanjia_wuxing(mountain),
            '化气分析': {},
            '五星配置': self.calculate_douhou_stars(mountain, day_tiangan),
            '吉凶判断': []
        }
        
        # 分析各天干化气与山家的关系
        for name, tiangan in result['四柱天干'].items():
            huaqi = self.get_tiangan_huaqi(tiangan)
            shanjia = result['山家五行']
            
            relation = self._analyze_wuxing_relation(huaqi, shanjia)
            result['化气分析'][name] = {
                '天干': tiangan,
                '化气': huaqi,
                '与山家关系': relation
            }
        
        # 吉凶判断
        result['吉凶判断'] = self._judge_auspicious(result)
        
        return result
    
    def _analyze_wuxing_relation(self, wuxing1: str, wuxing2: str) -> str:
        """
        分析五行关系
        :param wuxing1: 五行 1
        :param wuxing2: 五行 2
        :return: 关系描述
        """
        if wuxing1 == wuxing2:
            return '比和（吉）'
        elif WUXING_SHENG.get(wuxing1) == wuxing2:
            return '我生（泄气）'
        elif WUXING_SHENG.get(wuxing2) == wuxing1:
            return '生我（生气）'
        elif WUXING_KE.get(wuxing1) == wuxing2:
            return '我克（财星）'
        elif WUXING_KE.get(wuxing2) == wuxing1:
            return '克我（官鬼）'
        return '未知'
    
    def _judge_auspicious(self, analysis: dict) -> list:
        """
        吉凶判断
        :param analysis: 分析结果
        :return: 吉凶判断列表
        """
        judgments = []
        
        # 元辰到位为吉
        shanjia = analysis['山家五行']
        for name, info in analysis['化气分析'].items():
            if info['化气'] == shanjia:
                judgments.append(f"{name}柱元辰到位，主吉")
        
        # 武财宜有制
        wucai = analysis['五星配置']['五星配置']['武财']
        for name, info in analysis['化气分析'].items():
            if info['化气'] == wucai:
                judgments.append(f"{name}柱见武财，宜有制则吉")
        
        # 官鬼宜制化
        taguan = analysis['五星配置']['五星配置']['贪官']
        for name, info in analysis['化气分析'].items():
            if info['化气'] == taguan:
                judgments.append(f"{name}柱见贪官（官鬼），宜制化")
        
        if not judgments:
            judgments.append("需结合具体格局判断")
        
        return judgments


# 测试函数
def test_douhou():
    """测试斗首计算器"""
    calculator = DouShouCalculator()
    
    # 测试山家五行
    print("=== 山家五行测试 ===")
    for mountain in ['壬', '子', '癸', '丑', '巽', '巳', '丙', '午', '乾', '亥']:
        print(f"{mountain}山：{calculator.get_shanjia_wuxing(mountain)}")
    
    # 测试天干化气
    print("\n=== 天干化气测试 ===")
    for tiangan in TIANGAN:
        print(f"{tiangan}化：{calculator.get_tiangan_huaqi(tiangan)}")
    
    # 测试斗首五星
    print("\n=== 斗首五星配置测试 ===")
    result = calculator.calculate_douhou_stars('壬', '甲')
    print(f"壬山甲日：{result}")
    
    # 测试日课分析
    print("\n=== 斗首日课分析测试 ===")
    result = calculator.analyze_douhou_day('壬', '甲', '丙', '戊', '庚')
    print(f"分析结果：{result}")


if __name__ == '__main__':
    test_douhou()
