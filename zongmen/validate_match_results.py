#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例匹配验证系统

功能：
1. 验证所有课例是否都已匹配
2. 检查匹配质量
3. 识别并标记异常匹配
4. 生成验证报告
5. 确保 100% 准确率
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple


class MatchValidator:
    """匹配验证器"""
    
    def __init__(self):
        self.ke_jing_data = {}
        self.matched_results = {}
        self.validation_report = {}
        
    def load_data(self) -> bool:
        """加载数据"""
        # 加载 64 课数据
        ke_jing_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json'
        if os.path.exists(ke_jing_file):
            with open(ke_jing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ke_jing_data = {item['lesson_name']: item for item in data['results']}
                print(f"✓ 已加载 {len(self.ke_jing_data)} 条 64 课数据")
        else:
            print(f"✗ 64 课数据文件不存在")
            return False
        
        # 加载匹配结果
        matched_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_max_matched_results.json'
        if os.path.exists(matched_file):
            with open(matched_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.matched_results = data.get('matched_results', {})
                print(f"✓ 已加载 {len(self.matched_results)} 个匹配结果")
        else:
            print(f"✗ 匹配结果文件不存在")
            return False
        
        return True
    
    def validate_all(self) -> Dict:
        """执行全面验证"""
        print("\n" + "="*60)
        print("  开始全面验证匹配结果")
        print("="*60 + "\n")
        
        total = 8640  # 720 × 12
        matched = len(self.matched_results)
        
        validation = {
            'timestamp': datetime.now().isoformat(),
            'total_expected': total,
            'total_matched': matched,
            'match_rate': matched / total * 100 if total > 0 else 0,
            'completeness_check': self._check_completeness(),
            'accuracy_check': self._check_accuracy(),
            'consistency_check': self._check_consistency(),
            'quality_check': self._check_quality(),
            'anomalies': [],
            'overall_passed': False
        }
        
        # 检查是否达到 100% 匹配
        validation['overall_passed'] = (
            validation['match_rate'] >= 100 and
            validation['completeness_check']['passed'] and
            validation['accuracy_check']['passed']
        )
        
        return validation
    
    def _check_completeness(self) -> Dict:
        """检查完整性"""
        print("1. 检查匹配完整性...")
        
        # 检查 720 课例是否都有匹配
        expected_keys = set()
        gan_zhi_list = self._generate_gan_zhi_list()
        months = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        hours = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        for ri_gan_zhi in gan_zhi_list:
            for yue in months:
                for shi in hours:
                    expected_keys.add(f"{ri_gan_zhi}_{yue}_{shi}")
        
        matched_keys = set(self.matched_results.keys())
        missing_keys = expected_keys - matched_keys
        extra_keys = matched_keys - expected_keys
        
        check = {
            'passed': len(missing_keys) == 0 and len(extra_keys) == 0,
            'expected_count': len(expected_keys),
            'matched_count': len(matched_keys),
            'missing_keys': list(missing_keys)[:20],  # 只显示前 20 个
            'missing_count': len(missing_keys),
            'extra_keys': list(extra_keys)[:20],
            'extra_count': len(extra_keys),
            'completeness_rate': len(matched_keys & expected_keys) / len(expected_keys) * 100 if expected_keys else 0
        }
        
        print(f"   预期课例数：{check['expected_count']}")
        print(f"   匹配课例数：{check['matched_count']}")
        print(f"   缺失课例数：{check['missing_count']}")
        print(f"   多余课例数：{check['extra_count']}")
        print(f"   完整率：{check['completeness_rate']:.2f}%")
        print(f"   检查结果：{'✓ 通过' if check['passed'] else '✗ 未通过'}\n")
        
        return check
    
    def _check_accuracy(self) -> Dict:
        """检查准确性"""
        print("2. 检查匹配准确性...")
        
        invalid_ke_jing = []
        missing_primary = []
        low_confidence = []
        
        for ke_li_key, result in self.matched_results.items():
            qwen_matched = result.get('qwen_matched', {})
            
            # 检查课经是否在 64 课列表中
            matched_ke_jing = qwen_matched.get('matched_ke_jing', [])
            for ke_name in matched_ke_jing:
                if ke_name not in self.ke_jing_data:
                    invalid_ke_jing.append({
                        'ke_li_key': ke_li_key,
                        'invalid_ke_jing': ke_name
                    })
            
            # 检查是否有主课经
            primary = qwen_matched.get('primary_ke_jing', '')
            if not primary:
                missing_primary.append(ke_li_key)
            
            # 检查置信度
            confidence_scores = qwen_matched.get('confidence_scores', [])
            if confidence_scores and min(confidence_scores) < 50:
                low_confidence.append({
                    'ke_li_key': ke_li_key,
                    'min_confidence': min(confidence_scores)
                })
        
        check = {
            'passed': len(invalid_ke_jing) == 0 and len(missing_primary) == 0,
            'invalid_ke_jing_count': len(invalid_ke_jing),
            'invalid_ke_jing_samples': invalid_ke_jing[:10],
            'missing_primary_count': len(missing_primary),
            'missing_primary_samples': missing_primary[:10],
            'low_confidence_count': len(low_confidence),
            'low_confidence_samples': low_confidence[:10],
            'accuracy_rate': (len(self.matched_results) - len(invalid_ke_jing)) / len(self.matched_results) * 100 if self.matched_results else 0
        }
        
        print(f"   无效课经数：{check['invalid_ke_jing_count']}")
        print(f"   缺失主课经数：{check['missing_primary_count']}")
        print(f"   低置信度数：{check['low_confidence_count']}")
        print(f"   准确率：{check['accuracy_rate']:.2f}%")
        print(f"   检查结果：{'✓ 通过' if check['passed'] else '✗ 未通过'}\n")
        
        return check
    
    def _check_consistency(self) -> Dict:
        """检查一致性"""
        print("3. 检查匹配一致性...")
        
        # 检查相同日干支的课例是否有一致性
        consistency_issues = []
        
        ri_gan_zhi_groups = {}
        for ke_li_key, result in self.matched_results.items():
            ri_gan_zhi = result.get('ri_gan_zhi', '')
            if ri_gan_zhi not in ri_gan_zhi_groups:
                ri_gan_zhi_groups[ri_gan_zhi] = []
            ri_gan_zhi_groups[ri_gan_zhi].append(result)
        
        # 检查每个日干支组内的一致性
        for ri_gan_zhi, results in ri_gan_zhi_groups.items():
            primary_ke_jing_list = [r.get('qwen_matched', {}).get('primary_ke_jing', '') for r in results]
            unique_primary = set(primary_ke_jing_list)
            
            # 如果同一个日干支有太多不同的主课经，可能有问题
            if len(unique_primary) > 8:  # 阈值设为 8
                consistency_issues.append({
                    'ri_gan_zhi': ri_gan_zhi,
                    'unique_primary_count': len(unique_primary),
                    'primary_ke_jing_list': list(unique_primary)[:10]
                })
        
        check = {
            'passed': len(consistency_issues) == 0,
            'consistency_issues_count': len(consistency_issues),
            'consistency_issues_samples': consistency_issues[:10],
            'consistency_rate': (len(ri_gan_zhi_groups) - len(consistency_issues)) / len(ri_gan_zhi_groups) * 100 if ri_gan_zhi_groups else 0
        }
        
        print(f"   一致性问题数：{check['consistency_issues_count']}")
        print(f"   一致性率：{check['consistency_rate']:.2f}%")
        print(f"   检查结果：{'✓ 通过' if check['passed'] else '✗ 未通过'}\n")
        
        return check
    
    def _check_quality(self) -> Dict:
        """检查质量"""
        print("4. 检查匹配质量...")
        
        total_score = 0
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        
        for ke_li_key, result in self.matched_results.items():
            qwen_matched = result.get('qwen_matched', {})
            validation = qwen_matched.get('validation', {})
            score = validation.get('score', 0)
            
            total_score += score
            
            if score >= 90:
                high_quality += 1
            elif score >= 70:
                medium_quality += 1
            else:
                low_quality += 1
        
        avg_score = total_score / len(self.matched_results) if self.matched_results else 0
        
        check = {
            'passed': avg_score >= 80,
            'average_score': avg_score,
            'high_quality_count': high_quality,
            'high_quality_rate': high_quality / len(self.matched_results) * 100 if self.matched_results else 0,
            'medium_quality_count': medium_quality,
            'medium_quality_rate': medium_quality / len(self.matched_results) * 100 if self.matched_results else 0,
            'low_quality_count': low_quality,
            'low_quality_rate': low_quality / len(self.matched_results) * 100 if self.matched_results else 0,
            'quality_distribution': {
                'high': high_quality,
                'medium': medium_quality,
                'low': low_quality
            }
        }
        
        print(f"   平均得分：{check['average_score']:.1f}/100")
        print(f"   高质量数：{check['high_quality_count']} ({check['high_quality_rate']:.1f}%)")
        print(f"   中质量数：{check['medium_quality_count']} ({check['medium_quality_rate']:.1f}%)")
        print(f"   低质量数：{check['low_quality_count']} ({check['low_quality_rate']:.1f}%)")
        print(f"   检查结果：{'✓ 通过' if check['passed'] else '✗ 未通过'}\n")
        
        return check
    
    def _generate_gan_zhi_list(self) -> List[str]:
        """生成六十甲子列表"""
        tian_gan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        di_zhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        gan_zhi_list = []
        for i in range(60):
            gan = tian_gan[i % 10]
            zhi = di_zhi[i % 12]
            gan_zhi_list.append(f"{gan}{zhi}")
        
        return gan_zhi_list
    
    def generate_report(self, validation: Dict):
        """生成验证报告"""
        print("\n" + "="*60)
        print("  生成验证报告")
        print("="*60 + "\n")
        
        report = f"""# 8640 课例匹配验证报告

## 📊 基本信息

- **验证时间**: {validation['timestamp']}
- **总课例数**: {validation['total_expected']}
- **已匹配**: {validation['total_matched']}
- **匹配率**: {validation['match_rate']:.2f}%
- **总体通过**: {'✓ 是' if validation['overall_passed'] else '✗ 否'}

---

## ✅ 验证结果

### 1. 完整性检查 {'✓ 通过' if validation['completeness_check']['passed'] else '✗ 未通过'}

- 预期课例数：{validation['completeness_check']['expected_count']}
- 匹配课例数：{validation['completeness_check']['matched_count']}
- 缺失课例数：{validation['completeness_check']['missing_count']}
- 多余课例数：{validation['completeness_check']['extra_count']}
- 完整率：{validation['completeness_check']['completeness_rate']:.2f}%

{'**缺失课例示例**:' if validation['completeness_check']['missing_count'] > 0 else ''}
{chr(10).join(['- ' + key for key in validation['completeness_check']['missing_keys'][:10]]) if validation['completeness_check']['missing_count'] > 0 else '无缺失'}

### 2. 准确性检查 {'✓ 通过' if validation['accuracy_check']['passed'] else '✗ 未通过'}

- 无效课经数：{validation['accuracy_check']['invalid_ke_jing_count']}
- 缺失主课经数：{validation['accuracy_check']['missing_primary_count']}
- 低置信度数：{validation['accuracy_check']['low_confidence_count']}
- 准确率：{validation['accuracy_check']['accuracy_rate']:.2f}%

{'**无效课经示例**:' if validation['accuracy_check']['invalid_ke_jing_count'] > 0 else ''}
{chr(10).join(['- ' + item['ke_li_key'] + ': ' + item['invalid_ke_jing'] for item in validation['accuracy_check']['invalid_ke_jing_samples']]) if validation['accuracy_check']['invalid_ke_jing_count'] > 0 else '无无效课经'}

### 3. 一致性检查 {'✓ 通过' if validation['consistency_check']['passed'] else '✗ 未通过'}

- 一致性问题数：{validation['consistency_check']['consistency_issues_count']}
- 一致性率：{validation['consistency_check']['consistency_rate']:.2f}%

{'**一致性问题示例**:' if validation['consistency_check']['consistency_issues_count'] > 0 else ''}
{chr(10).join(['- ' + item['ri_gan_zhi'] + ': ' + str(item['unique_primary_count']) + ' 种主课经' for item in validation['consistency_check']['consistency_issues_samples']]) if validation['consistency_check']['consistency_issues_count'] > 0 else '无一致性问题'}

### 4. 质量检查 {'✓ 通过' if validation['quality_check']['passed'] else '✗ 未通过'}

- 平均得分：{validation['quality_check']['average_score']:.1f}/100
- 高质量数：{validation['quality_check']['high_quality_count']} ({validation['quality_check']['high_quality_rate']:.1f}%)
- 中质量数：{validation['quality_check']['medium_quality_count']} ({validation['quality_check']['medium_quality_rate']:.1f}%)
- 低质量数：{validation['quality_check']['low_quality_count']} ({validation['quality_check']['low_quality_rate']:.1f}%)

---

## 📈 总体评估

### 匹配完成率
- **目标**: 100%
- **实际**: {validation['match_rate']:.2f}%
- **状态**: {'✓ 达成' if validation['match_rate'] >= 100 else '⚠ 未达成'}

### 匹配准确率
- **目标**: 100%
- **实际**: {validation['accuracy_check']['accuracy_rate']:.2f}%
- **状态**: {'✓ 达成' if validation['accuracy_check']['accuracy_rate'] >= 100 else '⚠ 未达成'}

### 匹配质量
- **目标**: 平均分 ≥ 80
- **实际**: {validation['quality_check']['average_score']:.1f}
- **状态**: {'✓ 达成' if validation['quality_check']['average_score'] >= 80 else '⚠ 未达成'}

---

## 🎯 最终结论

{'**✅ 匹配验证通过！所有课例都已准确匹配，质量符合要求。**' if validation['overall_passed'] else '**⚠ 匹配验证未通过，需要进一步处理。**'}

### 需要改进的方面：
{'' if validation['completeness_check']['passed'] else f"- 完整性：需要补充 {validation['completeness_check']['missing_count']} 个缺失课例\n"}{'' if validation['accuracy_check']['passed'] else f"- 准确性：需要修正 {validation['accuracy_check']['invalid_ke_jing_count']} 个无效匹配\n"}{'' if validation['consistency_check']['passed'] else f"- 一致性：需要检查 {validation['consistency_check']['consistency_issues_count']} 个一致性问题\n"}{'' if validation['quality_check']['passed'] else f"- 质量：需要提升 {validation['quality_check']['low_quality_count']} 个低质量匹配的质量\n"}

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        report_file = 'validation_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存验证数据
        validation_data_file = 'validation_data.json'
        with open(validation_data_file, 'w', encoding='utf-8') as f:
            json.dump(validation, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 验证报告已保存：{report_file}")
        print(f"✓ 验证数据已保存：{validation_data_file}")
        
        # 打印总结
        print("\n" + "="*60)
        print("  验证总结")
        print("="*60)
        print(f"\n匹配率：{validation['match_rate']:.2f}%")
        print(f"准确率：{validation['accuracy_check']['accuracy_rate']:.2f}%")
        print(f"平均质量分：{validation['quality_check']['average_score']:.1f}/100")
        print(f"总体状态：{'✓ 通过' if validation['overall_passed'] else '✗ 未通过'}")
        
        return report


def main():
    """主函数"""
    print("="*60)
    print("  大六壬 8640 课例匹配验证系统")
    print("="*60)
    
    validator = MatchValidator()
    
    if not validator.load_data():
        print("\n数据加载失败，退出")
        return
    
    validation = validator.validate_all()
    validator.generate_report(validation)
    
    print("\n" + "="*60)
    print("  验证完成！")
    print("="*60)


if __name__ == '__main__':
    main()
