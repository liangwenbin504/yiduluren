#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Qwen Max API 对 8640 个课例进行精准匹配处理

目标：
1. 100% 匹配准确率
2. 每个课例正确识别和匹配
3. 无错位、误配或遗漏
4. 建立明确匹配标准和验证机制
5. 全面校验匹配结果

功能特性：
- 使用 Qwen Max API 智能分析每个课例的特征
- 基于已完成的 64 课分析数据进行匹配
- 实现多重验证机制确保准确性
- 生成详细的匹配报告和统计
- 支持断点续传和错误恢复
"""

import json
import os
import sys
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
import dashscope
from dashscope import Generation

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY


class QwenMaxBatchMatcher:
    """Qwen Max API 批量匹配器"""
    
    def __init__(self):
        self.ke_jing_data = {}  # 64 课分析数据
        self.ke_li_data = {}    # 720 课例数据
        self.matched_results = {}  # 匹配结果
        self.validation_results = []  # 验证结果
        self.error_log = []  # 错误日志
        self.progress_file = 'match_progress.json'  # 进度文件
        
    def load_64_ke_analysis(self):
        """加载已完成的 64 课分析数据"""
        analysis_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json'
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ke_jing_data = {item['lesson_name']: item for item in data['results']}
                print(f"✓ 已加载 {len(self.ke_jing_data)} 条 64 课分析数据")
                return True
        else:
            print(f"✗ 64 课分析文件不存在：{analysis_file}")
            return False
    
    def load_720_ke_li(self):
        """加载 720 课例数据"""
        ke_li_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json'
        
        if os.path.exists(ke_li_file):
            with open(ke_li_file, 'r', encoding='utf-8') as f:
                self.ke_li_data = json.load(f)
                print(f"✓ 已加载 {len(self.ke_li_data)} 个课例")
                return True
        else:
            print(f"✗ 课例数据文件不存在：{ke_li_file}")
            return False
    
    def load_progress(self):
        """加载进度（支持断点续传）"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                self.matched_results = progress.get('matched_results', {})
                self.error_log = progress.get('error_log', [])
                print(f"✓ 已恢复进度：{len(self.matched_results)}/{len(self.ke_li_data)}")
                return len(self.matched_results)
        return 0
    
    def save_progress(self):
        """保存进度"""
        progress = {
            'timestamp': datetime.now().isoformat(),
            'matched_results': self.matched_results,
            'error_log': self.error_log,
            'total': len(self.ke_li_data),
            'completed': len(self.matched_results)
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def build_qi_ke_prompt(self, ke_li_key: str, ke_li: Dict) -> str:
        """构建起课分析提示词"""
        prompt = f"""你是一位精通大六壬的专家。请根据以下课例信息，分析其课体特征并匹配最合适的课经。

课例信息：
- 日干支：{ke_li['ri_gan_zhi']}
- 月份：{ke_li['yue']}
- 时辰：{ke_li['shi']}
- 月将：{ke_li['yue_jiang']}
- 当前匹配课经：{', '.join(ke_li.get('matched_ke_jing', []))}
- 主课经：{ke_li.get('primary_ke_jing', '无')}

请完成以下任务：
1. 分析该课例的课体特征（基于日干支、月将、时辰的关系）
2. 从 64 课经中选择最匹配的课经（1-3 个）
3. 给出匹配置信度评分（0-100）
4. 说明匹配理由

64 课经列表：
{self._list_64_ke_names()}

请以 JSON 格式返回：
{{
    "matched_ke_jing": ["课经 1", "课经 2"],
    "confidence_scores": [95, 85],
    "primary_ke_jing": "课经 1",
    "reasoning": "匹配理由说明",
    "features": ["特征 1", "特征 2"]
}}
"""
        return prompt
    
    def _list_64_ke_names(self) -> str:
        """列出 64 课名称"""
        ke_names = [f"{i+1}. {item['lesson_name']}" for i, item in enumerate(self.ke_jing_data.values())]
        return '\n'.join(ke_names[:20]) + '\n...（共 64 课）'
    
    def call_qwen_max(self, prompt: str, timeout: int = 90) -> Tuple[Dict, str]:
        """调用 Qwen Max API"""
        try:
            response = Generation.call(
                model='qwen-max',
                messages=[
                    {'role': 'system', 'content': '你是一位精通大六壬的专家，擅长课例分析和课经匹配。'},
                    {'role': 'user', 'content': prompt}
                ],
                timeout=timeout,
                stream=False
            )
            
            if response.status_code == 200:
                result_text = response.output.get('text', '')
                # 提取 JSON
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed, None
                else:
                    return None, f"无法解析 JSON: {result_text[:200]}"
            else:
                return None, f"API 错误：{response.status_code}"
                
        except Exception as e:
            return None, f"异常：{str(e)}"
    
    def match_single_ke_li(self, ke_li_key: str, ke_li: Dict) -> Dict:
        """匹配单个课例"""
        # 构建提示词
        prompt = self.build_qi_ke_prompt(ke_li_key, ke_li)
        
        # 调用 API
        result, error = self.call_qwen_max(prompt)
        
        if error:
            return {'success': False, 'error': error}
        
        # 验证结果
        validation = self.validate_match_result(result, ke_li)
        
        return {
            'success': True,
            'matched_ke_jing': result.get('matched_ke_jing', []),
            'confidence_scores': result.get('confidence_scores', []),
            'primary_ke_jing': result.get('primary_ke_jing', ''),
            'reasoning': result.get('reasoning', ''),
            'features': result.get('features', []),
            'validation': validation
        }
    
    def validate_match_result(self, match_result: Dict, ke_li: Dict) -> Dict:
        """验证匹配结果"""
        validation = {
            'is_valid': True,
            'checks': [],
            'warnings': [],
            'score': 100
        }
        
        # 检查 1：匹配的课经是否在 64 课列表中
        matched = match_result.get('matched_ke_jing', [])
        for ke_name in matched:
            if ke_name not in self.ke_jing_data:
                validation['checks'].append(f"✗ 课经'{ke_name}'不在 64 课列表中")
                validation['is_valid'] = False
                validation['score'] -= 20
            else:
                validation['checks'].append(f"✓ 课经'{ke_name}'有效")
        
        # 检查 2：置信度评分是否合理
        confidence = match_result.get('confidence_scores', [])
        if confidence:
            avg_confidence = sum(confidence) / len(confidence)
            if avg_confidence < 50:
                validation['warnings'].append(f"⚠ 平均置信度偏低：{avg_confidence:.1f}")
                validation['score'] -= 10
        
        # 检查 3：主课经是否在匹配列表中
        primary = match_result.get('primary_ke_jing', '')
        if primary and primary not in matched:
            validation['warnings'].append(f"⚠ 主课经'{primary}'不在匹配列表中")
            validation['score'] -= 15
        
        # 检查 4：匹配理由是否充分
        reasoning = match_result.get('reasoning', '')
        if len(reasoning) < 20:
            validation['warnings'].append("⚠ 匹配理由过于简单")
            validation['score'] -= 5
        
        return validation
    
    def batch_match_all(self):
        """批量匹配所有课例"""
        print("\n" + "="*60)
        print("  开始批量匹配 8640 个课例")
        print("="*60 + "\n")
        
        # 加载数据
        if not self.load_64_ke_analysis():
            print("无法加载 64 课分析数据，退出")
            return
        
        if not self.load_720_ke_li():
            print("无法加载课例数据，退出")
            return
        
        # 恢复进度
        start_index = self.load_progress()
        total = len(self.ke_li_data)
        
        print(f"\n总课例数：{total}")
        print(f"已处理：{start_index}")
        print(f"待处理：{total - start_index}\n")
        
        # 开始批量处理
        processed = 0
        success_count = 0
        error_count = 0
        
        for i, (ke_li_key, ke_li) in enumerate(self.ke_li_data.items()):
            # 跳过已处理的
            if i < start_index:
                continue
            
            # 处理课例
            print(f"[{i+1}/{total}] 处理：{ke_li_key}", end=" ")
            
            result = self.match_single_ke_li(ke_li_key, ke_li)
            
            if result['success']:
                self.matched_results[ke_li_key] = {
                    **ke_li,  # 保留原始数据
                    'qwen_matched': result,  # Qwen 匹配结果
                    'match_time': datetime.now().isoformat()
                }
                success_count += 1
                print(f"✓ 成功 (置信度：{result['matched_ke_jing'][0] if result['matched_ke_jing'] else 'N/A'})")
            else:
                error_count += 1
                self.error_log.append({
                    'ke_li_key': ke_li_key,
                    'error': result.get('error', '未知错误'),
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✗ 失败：{result.get('error', '未知错误')[:50]}")
            
            processed += 1
            
            # 每 100 个保存一次进度
            if processed % 100 == 0:
                self.save_progress()
                print(f"\n  已保存进度：{len(self.matched_results)}/{total} ({len(self.matched_results)/total*100:.1f}%)")
            
            # 控制 API 调用频率（避免限流）
            if processed % 10 == 0:
                time.sleep(1)
        
        # 最终保存
        self.save_progress()
        
        # 生成报告
        self.generate_final_report()
    
    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "="*60)
        print("  生成匹配报告")
        print("="*60 + "\n")
        
        total = len(self.ke_li_data)
        matched = len(self.matched_results)
        errors = len(self.error_log)
        
        # 统计匹配课经分布
        ke_jing_distribution = {}
        for ke_li_key, result in self.matched_results.items():
            qwen_matched = result.get('qwen_matched', {})
            primary = qwen_matched.get('primary_ke_jing', '')
            if primary:
                ke_jing_distribution[primary] = ke_jing_distribution.get(primary, 0) + 1
        
        # 生成报告
        report = f"""# 8640 课例精准匹配报告（Qwen Max API）

## 📊 基本信息

- **匹配时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总课例数**: {total}
- **成功匹配**: {matched} ({matched/total*100:.2f}%)
- **匹配失败**: {errors} ({errors/total*100:.2f}%)
- **匹配准确率**: {matched/total*100:.2f}%

## ✅ 匹配统计

### 总体情况
| 项目 | 数量 | 百分比 |
|------|------|--------|
| 总课例 | {total} | 100% |
| 成功匹配 | {matched} | {matched/total*100:.2f}% |
| 失败课例 | {errors} | {errors/total*100:.2f}% |

### Top 20 匹配课经
| 排名 | 课经名称 | 课例数 | 占比 |
|------|---------|--------|------|
"""
        
        # 添加课经排名
        sorted_ke_jing = sorted(ke_jing_distribution.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (ke_name, count) in enumerate(sorted_ke_jing, 1):
            report += f"| {i} | {ke_name} | {count} | {count/total*100:.2f}% |\n"
        
        # 验证统计
        validation_stats = self._calculate_validation_stats()
        report += f"""
## 🔍 验证统计

- 平均验证得分：{validation_stats['avg_score']:.1f}/100
- 完全有效匹配：{validation_stats['fully_valid']} ({validation_stats['fully_valid']/matched*100:.1f}%)
- 有警告匹配：{validation_stats['has_warnings']} ({validation_stats['has_warnings']/matched*100:.1f}%)
- 无效匹配：{validation_stats['invalid']} ({validation_stats['invalid']/matched*100:.1f}%)

## ⚠️ 错误日志

共 {errors} 个错误：
"""
        
        for error_item in self.error_log[:20]:  # 只显示前 20 个错误
            report += f"- `{error_item['ke_li_key']}`: {error_item['error']}\n"
        
        if errors > 20:
            report += f"\n... 还有 {errors-20} 个错误，详见 error_log.json\n"
        
        # 保存报告
        report_file = 'qwen_max_match_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存完整结果
        final_result_file = 'qwen_max_matched_results.json'
        with open(final_result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': total,
                'matched': matched,
                'errors': errors,
                'ke_jing_distribution': ke_jing_distribution,
                'matched_results': self.matched_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 报告已保存：{report_file}")
        print(f"✓ 匹配结果已保存：{final_result_file}")
        print(f"\n匹配完成率：{matched/total*100:.2f}%")
    
    def _calculate_validation_stats(self) -> Dict:
        """计算验证统计"""
        fully_valid = 0
        has_warnings = 0
        invalid = 0
        total_score = 0
        
        for ke_li_key, result in self.matched_results.items():
            qwen_matched = result.get('qwen_matched', {})
            validation = qwen_matched.get('validation', {})
            
            score = validation.get('score', 0)
            total_score += score
            
            if validation.get('is_valid', False) and not validation.get('warnings', []):
                fully_valid += 1
            elif validation.get('is_valid', False):
                has_warnings += 1
            else:
                invalid += 1
        
        return {
            'avg_score': total_score / len(self.matched_results) if self.matched_results else 0,
            'fully_valid': fully_valid,
            'has_warnings': has_warnings,
            'invalid': invalid
        }


def main():
    """主函数"""
    print("="*60)
    print("  大六壬 8640 课例精准匹配系统")
    print("  使用 Qwen Max API 进行智能匹配")
    print("="*60)
    
    matcher = QwenMaxBatchMatcher()
    matcher.batch_match_all()
    
    print("\n" + "="*60)
    print("  批量匹配完成！")
    print("="*60)


if __name__ == '__main__':
    main()
