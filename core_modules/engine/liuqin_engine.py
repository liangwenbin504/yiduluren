"""
六亲计算引擎
六亲关系：父、鬼、子、兄、财
"""

from typing import Dict


class LiuQinCalculator:
    """六亲计算器"""
    
    # 天干五行
    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火',
        '戊': '土', '己': '土', '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木',
        '辰': '土', '巳': '火', '午': '火', '未': '土',
        '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 五行相生
    WU_XING_SHENG = {
        '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
    }
    
    # 五行相克
    WU_XING_KE = {
        '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
    }
    
    def __init__(self):
        pass
    
    def get_liuqin(self, ri_gan: str, dizhi: str) -> str:
        """
        计算六亲关系
        
        规则：
        - 生日干者：父（生我者）
        - 克日干者：鬼（克我者）
        - 泄日干者：子（我生者）
        - 与日干比和者：兄（同我者）
        - 受日干克者：财（我克者）
        
        参数：
        - ri_gan: 日干
        - dizhi: 地支（或天干）
        
        返回：
        - 六亲标注：父、鬼、子、兄、财
        """
        ri_wuxing = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        target_wuxing = self.DIZHI_WU_XING.get(dizhi, '')
        
        if not ri_wuxing or not target_wuxing:
            return ''
        
        # 生日干者：父（生我者）
        # 找哪个五行生日干的五行
        for wuxing, sheng in self.WU_XING_SHENG.items():
            if sheng == ri_wuxing:
                if target_wuxing == wuxing:
                    return '父'
        
        # 克日干者：鬼（克我者）
        for wuxing, ke in self.WU_XING_KE.items():
            if ke == ri_wuxing:
                if target_wuxing == wuxing:
                    return '鬼'
        
        # 泄日干者：子（我生者）
        if self.WU_XING_SHENG.get(ri_wuxing) == target_wuxing:
            return '子'
        
        # 受日干克者：财（我克者）
        if self.WU_XING_KE.get(ri_wuxing) == target_wuxing:
            return '财'
        
        # 与日干比和者：兄（同我者）
        if ri_wuxing == target_wuxing:
            return '兄'
        
        return ''
    
    def get_liuqin_for_tian(self, ri_gan: str, tian_zhi: str) -> str:
        """计算天盘地支的六亲"""
        return self.get_liuqin(ri_gan, tian_zhi)
