#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例匹配 - 详细调试版
"""

import json
import re
import time
import sys
from datetime import datetime
import dashscope
from dashscope import Generation

print("="*70)
print("  8640 课例匹配 - 详细调试版")
print("="*70)
print()

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

try:
    # 加载数据
    print("步骤 1: 加载数据...")
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        ke_jing_data = {item['lesson_name']: item for item in data['results']}
        print(f"   ✓ 64 课数据：{len(ke_jing_data)} 条")

    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json', 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
        print(f"   ✓ 课例数据：{len(ke_li_data)} 个")
    print()

    # 测试第一个课例
    print("步骤 2: 测试第一个课例...")
    first_key = list(ke_li_data.keys())[0]
    first_ke_li = ke_li_data[first_key]
    print(f"   课例：{first_key}")
    print(f"   日干支：{first_ke_li['ri_gan_zhi']}")
    print(f"   月：{first_ke_li['yue']}")
    print(f"   时：{first_ke_li['shi']}")
    print(f"   月将：{first_ke_li['yue_jiang']}")
    print()

    prompt = f"{first_ke_li['ri_gan_zhi']}{first_ke_li['yue']}{first_ke_li['shi']}{first_ke_li['yue_jiang']} 匹配 JSON:{{\"matched_ke_jing\":[\"课经\"],\"primary_ke_jing\":\"课经\"}}"
    print(f"   提示词：{prompt}")
    print(f"   长度：{len(prompt)}")
    print()

    print("   正在调用 API...")
    response = Generation.call(
        model='qwen-max',
        messages=[
            {'role': 'system', 'content': '大六壬专家。'},
            {'role': 'user', 'content': prompt}
        ],
        timeout=60,
        stream=False
    )

    print(f"   状态码：{response.status_code}")

    if response.status_code == 200:
        result_text = response.output.get('text', '')
        print(f"   返回长度：{len(result_text)}")
        print(f"   返回内容：{result_text[:200]}")

        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            print(f"   ✓ 解析成功！")
            print(f"   主课经：{result.get('primary_ke_jing', '')}")
        else:
            print(f"   ✗ 无法解析 JSON")
    else:
        print(f"   ✗ API 错误：{response.status_code}")
        if hasattr(response, 'message'):
            print(f"   错误信息：{response.message}")

    print()
    print("步骤 3: 准备开始批量匹配...")
    print(f"   总课例数：{len(ke_li_data)}")
    print()

    response = input("是否继续执行批量匹配？(输入 y 继续，其他键取消): ")
    if response.lower() != 'y':
        print("已取消")
        sys.exit(0)

    # 开始批量匹配
    print()
    print("="*70)
    print("  开始批量匹配")
    print("="*70)
    print()

    matched_results = {}
    error_log = []
    start_time = time.time()

    for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
        elapsed = time.time() - start_time
        avg_time = elapsed / (i + 1)
        remaining = (len(ke_li_data) - i) * avg_time

        print(f"[{i+1}/{len(ke_li_data)}] {ke_li_key} | 预计:{int(remaining/60)}分", end=" ")
        sys.stdout.flush()

        prompt = f"{ke_li['ri_gan_zhi']}{ke_li['yue']}{ke_li['shi']}{ke_li['yue_jiang']} 匹配 JSON:{{\"matched_ke_jing\":[\"课经\"],\"primary_ke_jing\":\"课经\"}}"

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
                        print(f"✗ 课经无效：{primary}")
                        error_log.append({'ke_li_key': ke_li_key, 'error': f'课经无效:{primary}'})
                else:
                    print(f"✗ 解析失败")
                    error_log.append({'ke_li_key': ke_li_key, 'error': '无法解析 JSON'})
            else:
                print(f"✗ API:{response.status_code}")
                error_log.append({'ke_li_key': ke_li_key, 'error': f'API 错误:{response.status_code}'})

        except Exception as e:
            print(f"✗ 异常:{str(e)[:30]}")
            error_log.append({'ke_li_key': ke_li_key, 'error': str(e)})

        # 每 5 个保存一次进度
        if (i + 1) % 5 == 0:
            progress = {
                'timestamp': datetime.now().isoformat(),
                'completed': i + 1,
                'total': len(ke_li_data),
                'matched_results': matched_results,
                'error_log': error_log
            }
            with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\match_progress_debug.json', 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
            print(f"  [已保存进度：{i+1}/{len(ke_li_data)}]")

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

    final_result = {
        'timestamp': datetime.now().isoformat(),
        'total': len(ke_li_data),
        'matched': len(matched_results),
        'errors': len(error_log),
        'success_rate': len(matched_results) / len(ke_li_data) * 100,
        'matched_results': matched_results
    }

    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_max_debug_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存")
    print()
    input("按回车键退出...")

except Exception as e:
    print(f"\n❌ 严重错误：{str(e)}")
    import traceback
    traceback.print_exc()
    print()
    input("按回车键退出...")
    sys.exit(1)
