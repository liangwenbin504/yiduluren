#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毕法赋批量标注脚本 v1.0
========================
对704古案例（sanchuan_kege_annotated_cases.json中的334个完整案例）
运行 bifa_detector 批量检测，统计覆盖率和准确性。
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from engine.bifa_detector import BiFaDetector, get_bifa_summary


def load_cases():
    """加载标注案例"""
    fp = BASE / 'data' / 'sanchuan_kege_annotated_cases.json'
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['cases']


def extract_ri_zhi(ganzhi: str) -> str:
    """从干支中提取日支"""
    if not ganzhi or len(ganzhi) < 2:
        return ''
    # 地支列表
    zhi_list = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    for z in zhi_list:
        if ganzhi.endswith(z):
            return z
    # 如果干支是2字且第二字是地支
    if len(ganzhi) == 2 and ganzhi[1] in zhi_list:
        return ganzhi[1]
    return ganzhi[-1] if len(ganzhi) >= 2 else ''


def annotate_case(case: dict, detector: BiFaDetector) -> dict:
    """对单个案例运行毕法赋检测"""
    ri_gan = case.get('ri_gan', '')
    ganzhi = case.get('ganzhi', '')
    ri_zhi = extract_ri_zhi(ganzhi)
    yuejiang = case.get('yuejiang', '')
    sanchuan_dizhi = case.get('sanchuan_dizhi', [])
    season = case.get('season', '')
    
    result = detector.detect(
        sanchuan_dizhi=sanchuan_dizhi,
        ri_gan=ri_gan,
        ri_zhi=ri_zhi,
        ganzhi=ganzhi,
        yuejiang=yuejiang,
        season=season,
        gan_shang_shen='',  # 案例中无此数据
        zhi_shang_shen='',  # 案例中无此数据
    )
    
    return result


def main():
    print('=' * 70)
    print('  毕法赋检测引擎 — 334古案例批量标注验证')
    print('=' * 70)
    
    cases = load_cases()
    print(f'\n加载案例: {len(cases)} 个')
    
    detector = BiFaDetector()
    
    results = []
    rule_counts = {}  # rule_id -> count
    signal_tally = {'涨': 0, '跌': 0, '震荡': 0, '平': 0}
    total_rules_detected = 0
    cases_with_rules = 0
    
    for i, case in enumerate(cases):
        try:
            result = annotate_case(case, detector)
            detected = result.get('匹配法条', [])
            
            if detected:
                cases_with_rules += 1
                total_rules_detected += len(detected)
                
                # 统计每条规则出现次数
                for rule_name in detected:
                    detail = result['法条详情'].get(rule_name, {})
                    rid = detail.get('id', 0)
                    rule_counts[rid] = rule_counts.get(rid, 0) + 1
            
            # 信号统计
            sig = result['股市信号']['综合倾向']
            signal_tally[sig] = signal_tally.get(sig, 0) + 1
            
            results.append({
                'index': i,
                'ganzhi': case.get('ganzhi', ''),
                'sanchuan': case.get('sanchuan_dizhi', []),
                'kege': case.get('primary_kege', ''),
                'bifa_rules': result['匹配法条'],
                'bifa_count': len(result['匹配法条']),
                'stock_signal': sig,
                'signal_strength': result['股市信号']['信号强度'],
                'advice': result['股市信号']['操作建议'],
            })
            
            if (i + 1) % 50 == 0:
                print(f'  进度: {i+1}/{len(cases)}...')
                
        except Exception as e:
            print(f'  ⚠ 案例 {i} ({case.get("ganzhi","?")}) 检测失败: {e}')
            results.append({
                'index': i,
                'ganzhi': case.get('ganzhi', ''),
                'error': str(e),
            })
    
    # ============ 统计报告 ============
    print(f'\n{"=" * 70}')
    print('  统计报告')
    print(f'{"=" * 70}\n')
    
    print(f'📊 检测概况:')
    print(f'  总案例数:          {len(cases)}')
    print(f'  成功检测:          {len([r for r in results if "error" not in r])}')
    print(f'  命中法条案例数:    {cases_with_rules} ({cases_with_rules/len(cases)*100:.1f}%)')
    print(f'  总命中法条数:      {total_rules_detected}')
    print(f'  平均每案例法条数:  {total_rules_detected/max(cases_with_rules,1):.1f}')
    
    print(f'\n📈 股市信号分布:')
    for sig, count in sorted(signal_tally.items(), key=lambda x: -x[1]):
        pct = count / len(cases) * 100
        bar = '█' * int(pct / 2)
        print(f'  {sig:4s}: {count:4d} ({pct:5.1f}%) {bar}')
    
    print(f'\n📋 法条命中排行 (Top 20):')
    sorted_rules = sorted(rule_counts.items(), key=lambda x: -x[1])
    for rid, count in sorted_rules[:20]:
        # 查找规则名
        rule_name = ''
        for r in results:
            if 'bifa_rules' in r:
                for name in r['bifa_rules']:
                    detail = (r.get('detail_map') or {}).get(name, {})
                    if detail.get('id') == rid:
                        rule_name = name
                        break
            if rule_name:
                break
        pct = count / len(cases) * 100
        bar = '█' * max(1, int(count / max(sorted_rules[0][1], 1) * 20))
        print(f'  #{rid:3d}: {count:4d}次 ({pct:4.1f}%) {bar}')
    
    # 保存结果
    output_fp = BASE / 'data' / 'bifa_annotated_cases.json'
    output = {
        '_meta': {
            'total_cases': len(cases),
            'detection_date': '2026-07-29',
            'engine_version': 'v1.0-batch1+batch2',
            'rules_detectable': len(detector.kb['rules']),
        },
        'stats': {
            'cases_with_rules': cases_with_rules,
            'total_rules_detected': total_rules_detected,
            'coverage_pct': round(cases_with_rules / len(cases) * 100, 1),
            'signal_distribution': signal_tally,
            'rule_frequency': {str(k): v for k, v in sorted_rules},
        },
        'cases': results,
    }
    
    with open(output_fp, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n💾 结果已保存: {output_fp}')
    print(f'{">" * 70}\n')


if __name__ == '__main__':
    main()
