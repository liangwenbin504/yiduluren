#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例精准匹配系统 - 稳定版

特性：
1. 更保守的超时设置（60 秒）
2. 详细的错误处理
3. 每 10 个课例保存一次进度
4. 更长的等待时间确保稳定
"""

import json
import os
import re
import time
from datetime import datetime
import dashscope
from dashscope import Generation

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

# 文件路径
ANALYSIS_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json'
KE_LI_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json'
PROGRESS_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\match_progress_stable.json'
RESULT_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_max_matched_results_stable.json'

# 64 课名称（简化）
KE_JING_LIST = "元首课、重审课、知一课、涉害课、遥克课、昴星课、别责课、八专课、伏吟课、返吟课、三光课、三阳课、三奇课、六仪课、时泰课、龙德课、官爵课、富贵课、轩盖课、铸印课、斫轮课、引从课、亨通课、繁昌课、荣华课、德庆课、合欢课、和美课、斩关课、闭口课、游子课、三交课、赘婿课、冲破课、淫泆课、芜淫课、解离课、度厄课、无禄课、绝嗣课、迍福课、侵害课、刑伤课、二烦课、天祸课、天狱课、天寇课、天网课、魄化课、三阴课、龙战课、死奇课、灾厄课、殃咎课、九丑课、鬼墓课、励德课、盘珠课、全局课、元胎课、连珠课、间传课、六纯课、杂状课、物类课"


def load_data():
    """加载数据"""
    print("加载数据...")
    with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        ke_jing_data = {item['lesson_name']: item for item in data['results']}
        print(f"✓ 已加载 {len(ke_jing_data)} 条 64 课数据")
    
    with open(KE_LI_FILE, 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
        print(f"✓ 已加载 {len(ke_li_data)} 个课例")
    
    return ke_jing_data, ke_li_data


def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            print(f"✓ 已恢复进度：{progress.get('completed', 0)}")
            return progress.get('matched_results', {}), progress.get('error_log', []), progress.get('completed', 0)
    return {}, [], 0


def save_progress(matched_results, error_log, completed, total):
    """保存进度"""
    progress = {
        'timestamp': datetime.now().isoformat(),
        'completed': completed,
        'total': total,
        'matched_results': matched_results,
        'error_log': error_log
    }
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def match_single(ke_li, ke_jing_data):
    """匹配单个课例"""
    prompt = f"""大六壬课例分析：
日干支：{ke_li['ri_gan_zhi']}
月：{ke_li['yue']}
时：{ke_li['shi']}
月将：{ke_li['yue_jiang']}

请从 64 课经中选择最匹配的 1 个课经。
64 课经：{KE_JING_LIST}

返回 JSON 格式：
{{"matched_ke_jing":["课经名"],"confidence_scores":[90],"primary_ke_jing":"课经名","reasoning":"简要理由"}}
"""
    
    try:
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '你是一位大六壬专家。'},
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
                
                # 验证课经是否在列表中
                matched = result.get('matched_ke_jing', [])
                if matched and matched[0] in ke_jing_data:
                    return result, None
                else:
                    return None, f"课经不在 64 课列表中：{matched[0] if matched else '空'}"
            else:
                return None, "无法解析 JSON"
        else:
            return None, f"API 错误：{response.status_code}"
            
    except Exception as e:
        return None, f"异常：{str(e)[:50]}"


def batch_match():
    """批量匹配"""
    print("\n" + "="*70)
    print("  8640 课例精准匹配系统 - 稳定版")
    print("  预计时间：30-40 分钟")
    print("="*70 + "\n")
    
    # 加载数据
    ke_jing_data, ke_li_data = load_data()
    
    # 加载进度
    matched_results, error_log, start_index = load_progress()
    
    total = len(ke_li_data)
    print(f"\n总课例数：{total}")
    print(f"待处理：{total - start_index}\n")
    
    # 开始匹配
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # 测试模式：设置为 False 关闭，True 开启（只处理前 100 个）
    test_mode = False  # 改为 True 只测试前 100 个
    max_test_count = 100
    
    for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
        # 跳过已处理的
        if i < start_index:
            continue
        
        # 测试模式：只处理前 100 个
        if test_mode and i >= max_test_count:
            print(f"\n[测试模式] 已处理 {max_test_count} 个课例，停止")
            break
        
        # 显示进度
        elapsed = time.time() - start_time
        processed = i - start_index + 1
        avg_time = elapsed / processed if processed > 0 else 0
        remaining = (total - i) * avg_time
        
        print(f"[{i+1}/{total}] {ke_li_key}", end=" ")
        
        # 匹配课例
        result, error = match_single(ke_li, ke_jing_data)
        
        if result and not error:
            matched_results[ke_li_key] = {
                **ke_li,
                'qwen_matched': result,
                'match_time': datetime.now().isoformat()
            }
            success_count += 1
            print(f"✓ {result.get('primary_ke_jing', 'N/A')}")
        else:
            error_count += 1
            error_log.append({
                'ke_li_key': ke_li_key,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
            print(f"✗ {error}")
        
        # 每 10 个保存一次进度
        if (i + 1) % 10 == 0:
            save_progress(matched_results, error_log, i + 1, total)
            print(f"  [进度已保存]")
        
        # 等待 2 秒，确保 API 稳定
        time.sleep(2)
    
    # 最终保存
    save_progress(matched_results, error_log, total if not test_mode else i+1, total)
    
    # 保存结果
    final_result = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'processed': len(matched_results),
        'errors': len(error_log),
        'success_rate': len(matched_results) / len(ke_li_data) * 100,
        'matched_results': matched_results
    }
    
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    # 显示总结
    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print("  匹配完成！")
    print("="*70)
    print(f"\n总耗时：{int(elapsed/60)}分{int(elapsed%60)}秒")
    print(f"成功：{len(matched_results)}")
    print(f"失败：{len(error_log)}")
    print(f"\n结果文件：{RESULT_FILE}")
    
    # 课经分布
    ke_jing_dist = {}
    for result in matched_results.values():
        primary = result.get('qwen_matched', {}).get('primary_ke_jing', '')
        if primary:
            ke_jing_dist[primary] = ke_jing_dist.get(primary, 0) + 1
    
    if ke_jing_dist:
        print("\nTop 课经分布:")
        sorted_ke_jing = sorted(ke_jing_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (ke_name, count) in enumerate(sorted_ke_jing, 1):
            print(f"  {i}. {ke_name}: {count} 课")


if __name__ == '__main__':
    try:
        batch_match()
        print("\n✅ 批量匹配完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，进度已保存")
    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
        import traceback
        traceback.print_exc()
