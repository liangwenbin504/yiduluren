#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课体吉凶评分系统
为每个课体提供详细的吉凶评分（0-10 分）
"""

class LiuRenKeTiScorer:
    """六壬课体评分系统"""
    
    # 64 课体吉凶评分表（基于传统六壬理论）
    KE_TI_SCORES = {
        # 大吉课体（9-10 分）
        '龙德课': 10.0,      # 最吉，贵人临身
        '富贵课': 9.5,       # 富贵双全
        '官爵课': 9.5,       # 官运亨通
        '轩盖课': 9.5,       # 文运昌盛
        '铸印课': 9.0,       # 权印在握
        '三奇课': 9.5,       # 天地人三奇
        '六仪课': 9.0,       # 六仪护身
        '时泰课': 9.0,       # 时运亨通
        
        # 上吉课体（8-9 分）
        '荣华课': 8.5,       # 荣华富贵
        '和美课': 8.5,       # 家庭和睦
        '合欢课': 8.5,       # 喜庆和合
        '回环课': 8.0,       # 循环往复
        '亨通课': 8.5,       # 万事亨通
        '华盖乘轩课': 8.5,   # 文星拱照
        '德庆课': 8.0,       # 德星临照
        '斫轮课': 8.0,       # 雕琢成器
        '铸印乘轩课': 8.5,   # 权印文星
        
        # 中吉课体（7-8 分）
        '知一课': 7.5,       # 事有专主
        '比用课': 7.5,       # 比和为用
        '涉害课': 7.0,       # 经历磨难
        '遥克课': 7.0,       # 远方来事
        '昴星课': 7.0,       # 潜藏待发
        '别责课': 7.0,       # 另辟蹊径
        '八专课': 7.0,       # 专注一事
        '伏吟课': 7.0,       # 静守待时
        '反吟课': 7.0,       # 反复无常
        
        # 中平课体（6-7 分）
        '元首课': 6.5,       # 事起男子
        '重审课': 6.5,       # 再三审核
        '始入课': 6.5,       # 初入其境
        '间传课': 6.5,       # 间接传达
        '移易课': 6.5,       # 变动转移
        '移远课': 6.5,       # 远方变动
        '归计课': 6.5,       # 计划回归
        '朝上帝课': 6.5,     # 朝见贵人
        
        # 中小凶课体（5-6 分）
        '无禄课': 5.5,       # 禄位不保
        '绝嗣课': 5.0,       # 后继无人
        '度厄课': 5.5,       # 度过厄运
        '芜淫课': 5.0,       # 淫乱不正
        '乱首课': 5.0,       # 以下犯上
        '冲破课': 5.5,       # 冲击破坏
        '刑伤课': 5.0,       # 刑伤灾祸
        '灾厄课': 5.0,       # 灾难厄运
        
        # 凶课（4-5 分）
        '天网课': 4.5,       # 天罗地网
        '地网课': 4.5,       # 地网束缚
        '死奇课': 4.0,       # 死亡奇祸
        '灾煞课': 4.5,       # 灾祸神煞
        '病符课': 4.0,       # 疾病缠身
        '丧门课': 4.0,       # 丧事临门
        '吊客课': 4.0,       # 吊唁之事
        '白虎课': 4.0,       # 白虎凶神
        
        # 大凶课体（3-4 分）
        '勾陈课': 3.5,       # 勾连陈旧
        '朱雀课': 3.5,       # 口舌是非
        '螣蛇课': 3.5,       # 虚惊怪异
        '玄武课': 3.5,       # 盗贼欺骗
        '天空课': 3.5,       # 空虚不实
        '亡神课': 3.0,       # 亡失心神
        '劫煞课': 3.0,       # 劫难灾煞
        '岁破课': 3.0,       # 岁君冲破
    }
    
    # 课体分类
    KE_TI_CATEGORIES = {
        '大吉': ['龙德课', '富贵课', '官爵课', '轩盖课', '铸印课', '三奇课', '六仪课', '时泰课'],
        '上吉': ['荣华课', '和美课', '合欢课', '回环课', '亨通课', '华盖乘轩课', '德庆课', '斫轮课', '铸印乘轩课'],
        '中吉': ['知一课', '比用课', '涉害课', '遥克课', '昴星课', '别责课', '八专课', '伏吟课', '反吟课'],
        '中平': ['元首课', '重审课', '始入课', '间传课', '移易课', '移远课', '归计课', '朝上帝课'],
        '中小凶': ['无禄课', '绝嗣课', '度厄课', '芜淫课', '乱首课', '冲破课', '刑伤课', '灾厄课'],
        '凶': ['天网课', '地网课', '死奇课', '灾煞课', '病符课', '丧门课', '吊客课', '白虎课'],
        '大凶': ['勾陈课', '朱雀课', '螣蛇课', '玄武课', '天空课', '亡神课', '劫煞课', '岁破课']
    }
    
    def __init__(self):
        pass
    
    def get_ke_ti_score(self, ke_ti_name: str) -> float:
        """获取课体评分"""
        return self.KE_TI_SCORES.get(ke_ti_name, 6.0)  # 默认 6 分（中平）
    
    def get_ke_ti_category(self, ke_ti_name: str) -> str:
        """获取课体分类"""
        score = self.get_ke_ti_score(ke_ti_name)
        
        if score >= 9.0:
            return '大吉'
        elif score >= 8.0:
            return '上吉'
        elif score >= 7.0:
            return '中吉'
        elif score >= 6.0:
            return '中平'
        elif score >= 5.0:
            return '中小凶'
        elif score >= 4.0:
            return '凶'
        else:
            return '大凶'
    
    def get_score_description(self, score: float) -> str:
        """获取评分描述"""
        if score >= 9.0:
            return '最上等吉日，非常吉利'
        elif score >= 8.0:
            return '上等吉日，很吉利'
        elif score >= 7.0:
            return '中等偏上，较为吉利'
        elif score >= 6.0:
            return '中等吉日，平平'
        elif score >= 5.0:
            return '中下等日，略有不利'
        elif score >= 4.0:
            return '下等日，不吉利'
        else:
            return '最下等日，大凶'
    
    def get_all_ke_ti_with_scores(self) -> list:
        """获取所有课体及其评分（按评分排序）"""
        ke_ti_list = [(name, score) for name, score in self.KE_TI_SCORES.items()]
        ke_ti_list.sort(key=lambda x: x[1], reverse=True)
        return ke_ti_list
    
    def get_ke_ti_by_category(self, category: str) -> list:
        """获取某分类下的所有课体"""
        return self.KE_TI_CATEGORIES.get(category, [])
    
    def calculate_comprehensive_score(self, matched_kege: list, douhou_score: float) -> float:
        """
        计算综合评分
        
        :param matched_kege: 匹配的课格列表
        :param douhou_score: 斗首评分
        :return: 综合评分（0-10 分）
        """
        if not matched_kege or len(matched_kege) == 0:
            return douhou_score
        
        # 计算六壬课格的平均分
        liuren_scores = [self.get_ke_ti_score(kege) for kege in matched_kege if kege in self.KE_TI_SCORES]
        
        if not liuren_scores:
            return douhou_score
        
        # 六壬评分（取最高分和平均分的加权）
        max_liuren = max(liuren_scores)
        avg_liuren = sum(liuren_scores) / len(liuren_scores)
        liuren_final = max_liuren * 0.6 + avg_liuren * 0.4
        
        # 综合评分：斗首 40% + 六壬 60%
        comprehensive = douhou_score * 0.4 + liuren_final * 0.6
        
        return round(comprehensive, 1)


# 测试
if __name__ == '__main__':
    scorer = LiuRenKeTiScorer()
    
    print("64 课体吉凶评分表（前 20 个）：")
    print("=" * 50)
    for name, score in scorer.get_all_ke_ti_with_scores()[:20]:
        category = scorer.get_ke_ti_category(name)
        desc = scorer.get_score_description(score)
        print(f"{name:12s} {score:4.1f}分 {category:6s} - {desc}")
