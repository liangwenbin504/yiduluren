#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
课格课体吉凶评价优化方案

优化原则：
1. 内容筛选：只保留核心吉凶判断
2. 层级划分：核心判断 → 禄马贵人 → 宜忌速查
3. 语言精简：合并重复内容，删除冗余断语
4. 重点突出：禄马贵人精准到各属相
"""

class OptimizedEvaluation:
    """精简版课格评价类"""
    
    # 地支与属相对应
    DIZHI_SHUXIANG = {
        '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
        '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
        '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
    }
    
    # 三合属相
    SANHE = {
        '子': ['申', '辰'],  # 鼠-猴-龙
        '丑': ['巳', '酉'],  # 牛-蛇-鸡
        '寅': ['午', '戌'],  # 虎-马-狗
        '卯': ['亥', '未'],  # 兔-猪-羊
        '辰': ['子', '申'],  # 龙-鼠-猴
        '巳': ['丑', '酉'],  # 蛇-牛-鸡
        '午': ['寅', '戌'],  # 马-虎-狗
        '未': ['卯', '亥'],  # 羊-兔-猪
        '申': ['子', '辰'],  # 猴-鼠-龙
        '酉': ['丑', '巳'],  # 鸡-牛-蛇
        '戌': ['寅', '午'],  # 狗-虎-马
        '亥': ['卯', '未'],  # 猪-兔-羊
    }
    
    # 六冲属相
    LIUCHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    
    def generate_optimized_evaluation(self, data: dict, liuren_duanyu) -> str:
        """
        生成精简版课格评价
        
        :param data: 课格数据
        :param liuren_duanyu: 六壬断语库
        :return: 精简版评价内容
        """
        parts = []
        
        # 一、核心判断
        parts.append(self._generate_core_judgment(data, liuren_duanyu))
        
        # 二、禄马贵人双重达标（精准到属相）
        parts.append(self._generate_luma_guiren_analysis(data))
        
        # 三、属相吉凶速查
        parts.append(self._generate_shuxiang_summary(data, liuren_duanyu))
        
        # 四、宜忌速查
        parts.append(self._generate_yiji_summary(data, liuren_duanyu))
        
        return ''.join([p for p in parts if p])
    
    def _generate_core_judgment(self, data: dict, liuren_duanyu) -> str:
        """生成核心判断"""
        parts = []
        parts.append("【核心判断】\n")
        
        # 课体等级汇总
        keti_list = self._get_keti_list(data)
        if keti_list:
            # 取最高等级
            best_keti = None
            best_level = 0
            level_map = {'上吉': 4, '中吉': 3, '平': 2, '下凶': 1}
            
            for keti in keti_list[:3]:
                keti_info = liuren_duanyu.get_keti_duanyu(keti)
                level = level_map.get(keti_info['等级'], 2)
                if level > best_level:
                    best_level = level
                    best_keti = keti_info
            
            if best_keti:
                level_name = best_keti['等级']
                parts.append(f"◆ 课体等级：{level_name}\n")
                parts.append(f"◆ 综合断语：{best_keti['断语'][:50]}\n")
        
        return ''.join(parts)
    
    def _generate_luma_guiren_analysis(self, data: dict) -> str:
        """生成禄马贵人分析（精准到属相）"""
        luma_info = data.get('luma_guiren_info', {})
        if not luma_info:
            return ""
        
        parts = []
        parts.append("\n【禄马贵人双重达标】\n")
        
        double_qualified_items = luma_info.get('double_qualified_items', [])
        dq_detail = luma_info.get('ri_double_qualified_detail', {})
        
        if double_qualified_items:
            parts.append(f"◆ 双重达标：{', '.join(double_qualified_items)}\n")
            
            # 禄神分析
            if dq_detail.get('ri_lu_double_qualified'):
                lu_zhi = self._get_lu_zhi(data)
                parts.append(f"\n◆ 禄神{lu_zhi}：到向+发传，主财禄双全\n")
                
                # 精准到属相
                lu_shuxiang = self.DIZHI_SHUXIANG.get(lu_zhi, '')
                sanhe = self.SANHE.get(lu_zhi, [])
                sanhe_shuxiang = [self.DIZHI_SHUXIANG.get(z, '') for z in sanhe]
                
                parts.append(f"  应验属相：{lu_shuxiang}（本命）")
                if sanhe_shuxiang:
                    parts.append(f"、{', '.join(sanhe_shuxiang)}（三合）大吉\n")
                
                # 六冲属相需谨慎
                chong_zhi = self.LIUCHONG.get(lu_zhi, '')
                if chong_zhi:
                    chong_shuxiang = self.DIZHI_SHUXIANG.get(chong_zhi, '')
                    parts.append(f"  需谨慎：{chong_shuxiang}（六冲）\n")
            
            # 驿马分析
            if dq_detail.get('ri_ma_double_qualified'):
                ma_zhi = self._get_ma_zhi(data)
                parts.append(f"\n◆ 驿马{ma_zhi}：到山到向+发传，主出行顺利\n")
                
                ma_shuxiang = self.DIZHI_SHUXIANG.get(ma_zhi, '')
                parts.append(f"  应验属相：{ma_shuxiang}（本命）出行大吉\n")
            
            # 贵人分析
            if dq_detail.get('ri_guiren_double_qualified'):
                guiren_zhi = self._get_guiren_zhi(data)
                parts.append(f"\n◆ 贵人{guiren_zhi}：到山到向+发传，主贵人扶持\n")
                
                guiren_shuxiang = self.DIZHI_SHUXIANG.get(guiren_zhi, '')
                parts.append(f"  应验属相：{guiren_shuxiang}（本命）贵人运旺\n")
        else:
            # 无双重达标
            single_items = luma_info.get('single_qualified_items', [])
            if single_items:
                parts.append(f"◆ 单一达标：{'; '.join(single_items[:2])}\n")
                parts.append(f"  提示：未达双重标准，吉力减半\n")
            else:
                parts.append(f"◆ 无双重达标项\n")
                parts.append(f"  提示：此课禄马贵人未双重达标，需谨慎\n")
        
        return ''.join(parts)
    
    def _generate_shuxiang_summary(self, data: dict, liuren_duanyu) -> str:
        """生成属相吉凶速查"""
        keti_list = self._get_keti_list(data)
        if not keti_list:
            return ""
        
        parts = []
        parts.append("\n【属相吉凶速查】\n")
        
        all_ji = set()
        all_xiong = set()
        
        for keti in keti_list:
            keti_info = liuren_duanyu.get_keti_duanyu(keti)
            if keti_info.get('属相吉'):
                all_ji.update(keti_info['属相吉'])
            if keti_info.get('属相凶'):
                all_xiong.update(keti_info['属相凶'])
        
        if all_ji:
            parts.append(f"◆ 大吉属相：{', '.join(sorted(list(all_ji)))}\n")
        if all_xiong:
            parts.append(f"◆ 需谨慎属相：{', '.join(sorted(list(all_xiong)))}\n")
        
        return ''.join(parts)
    
    def _generate_yiji_summary(self, data: dict, liuren_duanyu) -> str:
        """生成宜忌速查"""
        keti_list = self._get_keti_list(data)
        if not keti_list:
            return ""
        
        parts = []
        parts.append("\n【宜忌速查】\n")
        
        all_yi = set()
        all_ji = set()
        all_hangye = set()
        
        for keti in keti_list:
            keti_info = liuren_duanyu.get_keti_duanyu(keti)
            if keti_info.get('宜事'):
                all_yi.update(keti_info['宜事'])
            if keti_info.get('忌事'):
                all_ji.update(keti_info['忌事'])
            if keti_info.get('行业'):
                all_hangye.update(keti_info['行业'])
        
        if all_yi:
            parts.append(f"◆ 宜：{', '.join(sorted(list(all_yi))[:6])}\n")
        if all_ji:
            parts.append(f"◆ 忌：{', '.join(sorted(list(all_ji))[:4])}\n")
        if all_hangye:
            parts.append(f"◆ 适宜行业：{', '.join(sorted(list(all_hangye))[:5])}\n")
        
        return ''.join(parts)
    
    def _get_keti_list(self, data: dict) -> list:
        """获取课体列表"""
        keti_list = data.get('课格列表', [])
        if not keti_list and '课格类型' in data:
            keti_list = [k.strip() for k in data['课格类型'].split(',')]
        if not keti_list and 'patterns' in data:
            patterns = data.get('patterns', [])
            keti_list = []
            for p in patterns:
                if isinstance(p, str):
                    keti_list.append(p)
                elif isinstance(p, dict) and p.get('格局名称'):
                    keti_list.append(p['格局名称'])
        return keti_list
    
    def _get_lu_zhi(self, data: dict) -> str:
        """获取禄神地支"""
        sizhu = data.get('sizhu', {})
        ri_zhu = sizhu.get('日柱', '')
        if ri_zhu:
            ri_gan = ri_zhu[0]
            LU_MAP = {
                '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
                '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
            }
            return LU_MAP.get(ri_gan, '')
        return ''
    
    def _get_ma_zhi(self, data: dict) -> str:
        """获取驿马地支"""
        sizhu = data.get('sizhu', {})
        ri_zhu = sizhu.get('日柱', '')
        if ri_zhu and len(ri_zhu) >= 2:
            ri_zhi = ri_zhu[1]
            MA_MAP = {
                '申': '寅', '子': '寅', '辰': '寅',
                '寅': '申', '午': '申', '戌': '申',
                '亥': '巳', '卯': '巳', '未': '巳',
                '巳': '亥', '酉': '亥', '丑': '亥'
            }
            return MA_MAP.get(ri_zhi, '')
        return ''
    
    def _get_guiren_zhi(self, data: dict) -> str:
        """获取贵人地支"""
        luma_info = data.get('luma_guiren_info', {})
        dq_detail = luma_info.get('ri_double_qualified_detail', {})
        # 从双重达标信息中提取
        # 这里简化处理，实际需要根据天干计算
        return ''


# 优化后的输出格式示例
EXAMPLE_OUTPUT = """
【核心判断】
◆ 课体等级：中吉
◆ 综合断语：遥克课，遥相克制，事有阻隔，远方可成。

【禄马贵人双重达标】
◆ 双重达标：禄神午
◆ 禄神午：到向+发传，主财禄双全
  应验属相：马（本命）、虎、狗（三合）大吉
  需谨慎：鼠（六冲）

【属相吉凶速查】
◆ 大吉属相：虎, 马, 狗
◆ 需谨慎属相：猴, 鼠, 龙

【宜忌速查】
◆ 宜：安葬, 立碑, 出行, 外贸
◆ 忌：婚嫁, 开业
◆ 适宜行业：外贸, 旅游, 外交
"""
