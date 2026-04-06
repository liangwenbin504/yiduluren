#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例快速匹配 - 简化提示词版
特性：超短提示词，快速响应
"""

import json
import re
import time
from datetime import datetime
import dashscope
from dashscope import Generation

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

print("="*70)
print("  8640 课例快速匹配 - 简化版")
print("="*70)
print()

# 加载数据
print("加载数据...")
with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    ke_jing_data = {item['lesson_name']: item for item in data['results']}
    print(f"✓ 64 课数据：{len(ke_jing_data)} 条")

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json', 'r', encoding='utf-8') as f:
    ke_li_data = json.load(f)
    print(f"✓ 课例数据：{len(ke_li_data)} 个")
print()

# 开始匹配
print("开始批量匹配...")
print(f"总课例数：{len(ke_li_data)}")
print()

matched_results = {}
error_log = []
start_time = time.time()

for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
    # 显示进度
    elapsed = time.time() - start_time
    avg_time = elapsed / (i + 1)
    remaining = (len(ke_li_data) - i) * avg_time
    
    print(f"[{i+1}/{len(ke_li_data)}] {ke_li_key} | 预计:{int(remaining/60)}分", end=" ")
    
    # 超短提示词
    prompt = f"{ke_li['ri_gan_zhi']}{ke_li['yue']}{ke_li['shi']}{ke_li['yue_jiang']} 匹配课经 JSON:{{\"matched_ke_jing\":[\"课经\"],\"primary_ke_jing\":\"课经\",\"reasoning\":\"理由\"}}"
    
    try:
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '大六壬专家。'},
                {'role': 'user', 'content': prompt}
            ],
            timeout=60,
            stream=False
        )
        
        if response.status_code == 200:
            result_text = response.output.get('text', '')
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                primary = result.get('primary_ke_jing', '')
                
                if primary and primary in ke_jing_data:
                    matched_results[ke_li_key] = {
                        **ke_li,
                        'qwen_matched': result,
                        'match_time': datetime.now().isoformat()
                    }
                    print(f"✓ {primary}")
                else:
                    print(f"✗ 课经无效")
                    error_log.append({'ke_li_key': ke_li_key, 'error': '课经无效'})
            else:
                print(f"✗ 解析失败")
                error_log.append({'ke_li_key': ke_li_key, 'error': '无法解析 JSON'})
        else:
            print(f"✗ API:{response.status_code}")
            error_log.append({'ke_li_key': ke_li_key, 'error': f'API 错误:{response.status_code}'})
    
    except Exception as e:
        print(f"✗ 异常:{str(e)[:30]}")
        error_log.append({'ke_li_key': ke_li_key, 'error': str(e)})
    
    # 每 10 个保存一次进度
    if (i + 1) % 10 == 0:
        progress = {
            'timestamp': datetime.now().isoformat(),
            'completed': i + 1,
            'total': len(ke_li_data),
            'matched_results': matched_results,
            'error_log': error_log
        }
        with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\match_progress_quick.json', 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        print(f"  [进度已保存]")
    
    # 短暂等待
    time.sleep(0.5)

# 最终保存
print()
print("="*70)
print("  匹配完成！")
print("="*70)

elapsed = time.time() - start_time
print(f"\n总耗时：{int(elapsed/60)}分{int(elapsed%60)}秒")
print(f"成功：{len(matched_results)}/{len(ke_li_data)} ({len(matched_results)/len(ke_li_data)*100:.1f}%)")
print(f"失败：{len(error_log)}/{len(ke_li_data)} ({len(error_log)/len(ke_li_data)*100:.1f}%)")

# 保存结果
final_result = {
    'timestamp': datetime.now().isoformat(),
    'total': len(ke_li_data),
    'matched': len(matched_results),
    'errors': len(error_log),
    'success_rate': len(matched_results) / len(ke_li_data) * 100,
    'matched_results': matched_results
}

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_max_quick_results.json', 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存：qwen_max_quick_results.json")

# 课经分布统计
ke_jing_dist = {}
for result in matched_results.values():
    primary = result.get('qwen_matched', {}).get('primary_ke_jing', '')
    if primary:
        ke_jing_dist[primary] = ke_jing_dist.get(primary, 0) + 1

if ke_jing_dist:
    print("\nTop 10 课经分布:")
    sorted_ke_jing = sorted(ke_jing_dist.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (ke_name, count) in enumerate(sorted_ke_jing, 1):
        print(f"  {i}. {ke_name}: {count} 课 ({count/len(ke_li_data)*100:.1f}%)")

print("\n✅ 批量匹配完成！")
