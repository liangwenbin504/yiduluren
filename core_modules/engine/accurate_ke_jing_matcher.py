#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经与 720 课精准匹配系统

功能：
1. 加载完整的 64 课经数据
2. 根据九宗门起课方法匹配课经
3. 将匹配结果永久关联到 720 课数据库
4. 提供便捷的课经查询功能
"""

import json
import os
import sys

# 路径设置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))


class AccurateKeJingMatcher:
    """精准课经匹配器"""
    
    def __init__(self):
        self.ke_jing_data = {}
        self.ke_li_data = {}
        self.load_ke_jing()
        self.load_ke_li()
    
    def load_ke_jing(self):
        """加载 64 课经数据"""
        ke_jing_file = "data/64_ke_jing_accurate.json"
        if os.path.exists(ke_jing_file):
            with open(ke_jing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ke_jing_data = data.get('courses', {})
                print(f"已加载 {len(self.ke_jing_data)} 条课经数据")
        else:
            print(f"课经数据文件不存在：{ke_jing_file}")
    
    def load_ke_li(self):
        """加载 720 课例数据"""
        ke_li_file = "data/720_ke_li.json"
        if os.path.exists(ke_li_file):
            with open(ke_li_file, 'r', encoding='utf-8') as f:
                self.ke_li_data = json.load(f)
                print(f"已加载 {len(self.ke_li_data)} 个课例")
        else:
            print("课例数据库不存在，需要先创建")
    
    def match_by_complete_qi_ke(self, qi_ke_result: dict):
        """
        根据完整起课结果匹配课经（使用四课三传天将神煞等信息）
        
        :param qi_ke_result: 完整起课结果（来自 CompleteQiKeEngine）
        :return: 匹配的课经列表
        """
        matched_ke_jing = []
        
        # 提取关键信息
        ke_ti_list = qi_ke_result.get('课体', [])
        sanchuan = qi_ke_result.get('三传', {})
        sike = qi_ke_result.get('四课', [])
        
        # 1. 根据课体判断直接匹配
        ke_ti_to_ke_jing = {
            '伏吟课': '14',
            '反吟课': '15',
            '元首课': '1',
            '重审课': '2',
            '比用课': '9',
            '涉害课': '10',
            '遥克课': '11',
            '昴星课': '12',
            '别责课': '13',
            '八专课': '37',
            '无禄课': '16',
            '绝嗣课': '17',
            '度厄课': '18',
            '芜淫课': '19',
            '乱首课': '20',
            '盘珠课': '5',
            '和美课': '21',
            '玄胎课': '46',
            '三奇课': '26',
            '六仪课': '27',
            '时泰课': '28',
            '龙德课': '29',
            '官爵课': '30',
            '富贵课': '31',
            '铸印课': '32',
            '斫轮课': '33',
            '引从课': '34',
            '轩盖课': '35',
            '斗罡课': '36',
            '六冲课': '38',
            '六害课': '39',
            '三合课': '40',
            '三刑课': '41',
            '六破课': '42',
            '天网课': '43',
            '地网课': '44',
            '孤辰课': '45',
            '寡宿课': '47',
            '三光课': '48',
            '三阳课': '49',
            '官厉课': '50',
            '福助课': '51',
            '刑伤课': '52',
            '破败课': '53',
            '惊忧课': '54',
            '疑怪课': '55',
            '灾危课': '56',
            '病符课': '57',
            '死气课': '58',
            '丧吊课': '59',
            '血光课': '60',
            '牢狱课': '61',
            '逃亡课': '62',
            '失脱课': '63',
            '鬼祟课': '64',
        }
        
        # 根据课体匹配课经
        for ke_ti in ke_ti_list:
            if ke_ti in ke_ti_to_ke_jing:
                ke_jing_id = ke_ti_to_ke_jing[ke_ti]
                ke_jing = self.ke_jing_data.get(ke_jing_id, {})
                if ke_jing and ke_jing not in matched_ke_jing:
                    matched_ke_jing.append(ke_jing)
        
        # 2. 根据三传课体补充匹配
        sanchuan_ke_ti = sanchuan.get('课体', '')
        if sanchuan_ke_ti and sanchuan_ke_ti in ke_ti_to_ke_jing:
            ke_jing_id = ke_ti_to_ke_jing[sanchuan_ke_ti]
            ke_jing = self.ke_jing_data.get(ke_jing_id, {})
            if ke_jing and ke_jing not in matched_ke_jing:
                matched_ke_jing.append(ke_jing)
        
        # 3. 如果没有匹配到，使用基本的九宗门方法
        if not matched_ke_jing:
            basic_info = qi_ke_result.get('基本信息', {})
            ri_gan_zhi = basic_info.get('日干支', '')
            yue = basic_info.get('月将', '')
            shi = basic_info.get('占时', '')
            
            basic_matched = self.match_by_jiu_zong_men(
                ri_gan_zhi, yue, shi, yue
            )
            matched_ke_jing.extend(basic_matched)
        
        return matched_ke_jing
    
    def match_by_jiu_zong_men(self, ri_gan_zhi, yue, shi, yue_jiang):
        """
        根据九宗门起课方法匹配课经
        
        :param ri_gan_zhi: 日干支
        :param yue: 月支
        :param shi: 时支
        :param yue_jiang: 月将
        :return: 匹配的课经列表
        """
        matched_ke_jing = []
        
        # 提取日干支的天干地支
        gan = ri_gan_zhi[0]
        zhi = ri_gan_zhi[1]
        
        # 刚日（阳干）：甲丙戊庚壬
        gang_ri = gan in ['甲', '丙', '戊', '庚', '壬']
        
        # 柔日（阴干）：乙丁己辛癸
        rou_ri = gan in ['乙', '丁', '己', '辛', '癸']
        
        # 1. 伏吟课：月将=占时
        if yue_jiang == shi:
            matched_ke_jing.append(self.ke_jing_data.get('14', {}))
        
        # 2. 反吟课：月将冲占时
        elif self._is_chong(yue_jiang, shi):
            matched_ke_jing.append(self.ke_jing_data.get('15', {}))
        
        # 3. 根据日干支阴阳匹配基本课体
        if gang_ri:
            # 刚日多主外事，主动
            matched_ke_jing.append(self.ke_jing_data.get('1', {}))  # 元首课
            matched_ke_jing.append(self.ke_jing_data.get('9', {}))  # 比用课
            matched_ke_jing.append(self.ke_jing_data.get('16', {}))  # 无禄课 (刚日易犯)
        elif rou_ri:
            # 柔日多主内事，主静
            matched_ke_jing.append(self.ke_jing_data.get('2', {}))  # 重审课
            matched_ke_jing.append(self.ke_jing_data.get('13', {}))  # 别责课
            matched_ke_jing.append(self.ke_jing_data.get('17', {}))  # 绝嗣课 (柔日易犯)
        
        # 4. 度厄课：根据月份和时辰关系
        # 度厄三课上下克，正月、七月多犯
        if yue in ['寅', '申'] or shi in ['寅', '申']:
            matched_ke_jing.append(self.ke_jing_data.get('18', {}))  # 度厄课
        
        # 5. 根据月支和时支的关系匹配特殊课体
        if yue == shi:
            matched_ke_jing.append(self.ke_jing_data.get('5', {}))  # 盘珠课
        
        # 6. 根据月将和日支的关系
        if yue_jiang == zhi:
            matched_ke_jing.append(self.ke_jing_data.get('21', {}))  # 和美课
        
        # 7. 乱首课：支克干 (以下犯上)
        if self._is_ke(zhi, gan):
            matched_ke_jing.append(self.ke_jing_data.get('20', {}))  # 乱首课
        
        # 8. 芜淫课：根据日干支相克关系
        if self._is_ke(gan, zhi) or self._is_ke(zhi, gan):
            matched_ke_jing.append(self.ke_jing_data.get('19', {}))  # 芜淫课
        
        # 去除空项
        matched_ke_jing = [k for k in matched_ke_jing if k and k.get('ke_name')]
        
        return matched_ke_jing
    
    def _is_chong(self, zhi1, zhi2):
        """判断是否相冲"""
        chong_pairs = {
            '子': '午', '丑': '未', '寅': '申',
            '卯': '酉', '辰': '戌', '巳': '亥'
        }
        return chong_pairs.get(zhi1) == zhi2
    
    def _is_ke(self, gan_zhi1, gan_zhi2):
        """
        判断五行相克关系
        金克木，木克土，土克水，水克火，火克金
        """
        wu_xing_ke = {
            '甲': '戊己', '乙': '戊己',  # 木克土
            '丙': '庚辛', '丁': '庚辛',  # 火克金
            '戊': '壬癸', '己': '壬癸',  # 土克水
            '庚': '甲乙', '辛': '甲乙',  # 金克木
            '壬': '丙丁', '癸': '丙丁',  # 水克火
            '寅': '辰戌丑未', '卯': '辰戌丑未',  # 木克土
            '巳': '申酉', '午': '申酉',  # 火克金
            '辰': '子亥', '戌': '子亥', '丑': '子亥', '未': '子亥',  # 土克水
            '申': '寅卯', '酉': '寅卯',  # 金克木
            '子': '巳午', '亥': '巳午'   # 水克火
        }
        
        ke_list = wu_xing_ke.get(gan_zhi1, '')
        return gan_zhi2 in ke_list
    
    def match_all_720_ke(self):
        """
        对所有 720 课进行课经匹配
        """
        print("开始匹配 720 课的课经...")
        
        count = 0
        for ke_key, ke_data in self.ke_li_data.items():
            ri_gan_zhi = ke_data['ri_gan_zhi']
            yue = ke_data['yue']
            shi = ke_data['shi']
            yue_jiang = ke_data['yue_jiang']
            
            # 匹配课经
            matched = self.match_by_jiu_zong_men(ri_gan_zhi, yue, shi, yue_jiang)
            
            # 转换为课名列表
            ke_jing_names = [k['ke_name'] for k in matched if k.get('ke_name')]
            
            # 更新课例数据
            ke_data['matched_ke_jing'] = ke_jing_names
            
            # 添加课经断语
            if ke_jing_names:
                ke_data['primary_ke_jing'] = ke_jing_names[0]
                ke_data['duanyu'] = self._get_ke_jing_duanyu(ke_jing_names[0])
            
            count += 1
            
            if count % 100 == 0:
                print(f"已匹配 {count}/{len(self.ke_li_data)} 个课例")
        
        print(f"完成匹配 {count} 个课例")
        
        # 保存结果
        self.save_ke_li()
    
    def _get_ke_jing_duanyu(self, ke_name):
        """获取课经断语"""
        for ke_id, ke_data in self.ke_jing_data.items():
            if ke_data.get('ke_name') == ke_name:
                return {
                    'duanyu': ke_data.get('duanyu', []),
                    'summary': ke_data.get('summary', ''),
                    'score': ke_data.get('score', 0),
                    'level': ke_data.get('level', '')
                }
        return None
    
    def save_ke_li(self):
        """保存课例数据"""
        ke_li_file = "data/720_ke_li.json"
        os.makedirs(os.path.dirname(ke_li_file), exist_ok=True)
        with open(ke_li_file, 'w', encoding='utf-8') as f:
            json.dump(self.ke_li_data, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(self.ke_li_data)} 个课例到 {ke_li_file}")
    
    def query_ke_jing(self, ke_name):
        """
        查询课经信息
        
        :param ke_name: 课名
        :return: 课经详细信息
        """
        for ke_id, ke_data in self.ke_jing_data.items():
            if ke_data.get('ke_name') == ke_name:
                return ke_data
        return None
    
    def query_ke_by_name(self, ke_name):
        """
        根据课名查询所有匹配的课例
        
        :param ke_name: 课名
        :return: 课例列表
        """
        matched_ke_li = []
        for ke_key, ke_data in self.ke_li_data.items():
            if ke_name in ke_data.get('matched_ke_jing', []):
                matched_ke_li.append({
                    'ke_key': ke_key,
                    'ri_gan_zhi': ke_data['ri_gan_zhi'],
                    'yue': ke_data['yue'],
                    'shi': ke_data['shi'],
                    'yue_jiang': ke_data['yue_jiang']
                })
        return matched_ke_li
    
    def get_statistics(self):
        """获取统计信息"""
        stats = {
            'total_ke_jing': len(self.ke_jing_data),
            'total_ke_li': len(self.ke_li_data),
            'matched_ke_li': 0,
            'ke_jing_distribution': {}
        }
        
        # 统计每个课经匹配到的课例数
        for ke_data in self.ke_li_data.values():
            if ke_data.get('matched_ke_jing'):
                stats['matched_ke_li'] += 1
                for ke_name in ke_data['matched_ke_jing']:
                    stats['ke_jing_distribution'][ke_name] = \
                        stats['ke_jing_distribution'].get(ke_name, 0) + 1
        
        return stats


def main():
    """主函数"""
    print("=" * 60)
    print("大六壬 64 课经与 720 课精准匹配系统")
    print("=" * 60)
    
    matcher = AccurateKeJingMatcher()
    
    # 匹配所有课例
    matcher.match_all_720_ke()
    
    # 显示统计信息
    stats = matcher.get_statistics()
    print("\n统计信息:")
    print(f"  课经总数：{stats['total_ke_jing']}")
    print(f"  课例总数：{stats['total_ke_li']}")
    print(f"  已匹配课例：{stats['matched_ke_li']}")
    
    print("\n课经分布 (前 10):")
    sorted_dist = sorted(stats['ke_jing_distribution'].items(), 
                        key=lambda x: x[1], reverse=True)
    for ke_name, count in sorted_dist[:10]:
        print(f"  {ke_name}: {count} 课")
    
    # 测试查询
    print("\n测试查询 - 元首课:")
    ke_data = matcher.query_ke_jing('元首课')
    if ke_data:
        print(f"  课名：{ke_data['ke_name']}")
        print(f"  类型：{ke_data['ke_type']}")
        print(f"  定义：{ke_data['definition']}")
        print(f"  断语：{ke_data['duanyu'][0] if ke_data['duanyu'] else ''}")
        print(f"  评分：{ke_data['score']} ({ke_data['level']})")
    
    # 查询匹配元首课的课例
    print("\n匹配元首课的课例 (前 5):")
    matched = matcher.query_ke_by_name('元首课')
    for item in matched[:5]:
        print(f"  {item['ke_key']} - {item['ri_gan_zhi']}年{item['yue']}月{item['shi']}时")
    
    print("\n匹配完成！")


if __name__ == '__main__':
    main()
