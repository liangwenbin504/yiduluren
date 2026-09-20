#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
三传课格批量标注管线
====================

用 sanchuan_kege v2.0 引擎批量标注704个古案例，
生成三传课格→吉凶→涨跌的训练数据集。

输入: extracted_data/壬占汇选_训练数据_v2.json
输出: data/sanchuan_kege_annotated_cases.json

创建日期: 2026-07-29
"""

import json
import sys
import os
from collections import Counter, defaultdict

# 确保能导入 engine 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.sanchuan_kege import SanChuanKegeDetector, detect_sanchuan_kege


def extract_dizhi(ganzhi_str: str) -> str:
    """从干支字符串提取地支，如 '壬申' → '申'"""
    if not ganzhi_str or len(ganzhi_str) < 2:
        return ganzhi_str
    return ganzhi_str[-1]  # 最后一个字符是地支


def extract_rigan(ganzhi_str: str) -> str:
    """从干支字符串提取天干（日干），如 '甲子' → '甲'"""
    if not ganzhi_str or len(ganzhi_str) < 1:
        return ''
    return ganzhi_str[0]  # 第一个字符是天干


def get_season_from_yuejiang(yuejiang: str) -> str:
    """从月将推断季节
    月将: 亥将(冬), 子将(冬), 丑将(冬), 寅将(春), 卯将(春), 辰将(春),
          巳将(夏), 午将(夏), 未将(夏), 申将(秋), 酉将(秋), 戌将(秋)
    """
    season_map = {
        '寅': '春', '卯': '春', '辰': '春',
        '巳': '夏', '午': '夏', '未': '夏',
        '申': '秋', '酉': '秋', '戌': '秋',
        '亥': '冬', '子': '冬', '丑': '冬',
    }
    # 月将字符串如 '午将' → '午'
    yj = yuejiang.replace('将', '').strip() if yuejiang else ''
    return season_map.get(yj, '')


def annotate_cases(input_path: str, output_path: str) -> dict:
    """批量标注古案例"""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    detector = SanChuanKegeDetector()
    
    annotated = []
    stats = {
        'total': len(cases),
        'with_sanchuan': 0,
        'annotated': 0,
        'skipped': 0,
        'kege_counter': Counter(),
        'signal_counter': Counter(),
        'jixiong_counter': Counter(),
    }
    
    for i, case in enumerate(cases):
        sanchuan_raw = case.get('sanchuan', [])
        
        # 检查三传是否完整（需要3个位置）
        if not sanchuan_raw or len(sanchuan_raw) < 3:
            stats['skipped'] += 1
            continue
        
        stats['with_sanchuan'] += 1
        
        # 提取纯地支三传
        sanchuan_dizhi = [extract_dizhi(s) for s in sanchuan_raw[:3]]
        
        # 验证地支有效性
        valid_dizhi = {'子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'}
        if not all(z in valid_dizhi for z in sanchuan_dizhi):
            stats['skipped'] += 1
            continue
        
        # 提取日干
        ganzhi = case.get('ganzhi', '')
        ri_gan = extract_rigan(ganzhi)
        
        # 推断季节
        yuejiang = case.get('yuejiang', '')
        season = get_season_from_yuejiang(yuejiang)
        
        # 运行课格检测
        result = detector.detect(
            sanchuan_dizhi,
            ri_gan=ri_gan,
            season=season
        )
        
        # 统计课格
        for kege in result['课格列表']:
            stats['kege_counter'][kege] += 1
        
        signal = result['股市信号'].get('综合倾向', '平')
        stats['signal_counter'][signal] += 1
        
        # 统计吉凶
        for kege_name, detail in result['课格详情'].items():
            jx = detail.get('吉凶', '')
            if jx:
                stats['jixiong_counter'][jx] += 1
        
        # 构建标注记录
        record = {
            'index': i,
            'ganzhi': ganzhi,
            'yuejiang': yuejiang,
            'shichen': case.get('shichen', ''),
            'season': season,
            'sanchuan_ganzhi': sanchuan_raw[:3],
            'sanchuan_dizhi': sanchuan_dizhi,
            'ri_gan': ri_gan,
            'kege_list': result['课格列表'],
            'kege_count': len(result['课格列表']),
            'primary_kege': result['课格列表'][0] if result['课格列表'] else '',
            'stock_signal': result['股市信号'].get('综合倾向', '平'),
            'signal_strength': result['股市信号'].get('信号强度', 0),
            'stock_advice': result['股市信号'].get('操作建议', ''),
            'sanchuan_trend': result['三传分类'].get('三传走势', ''),
            'question': case.get('question', ''),
            'source': case.get('source', ''),
            # 详细课格信息（用于训练）
            'kege_details_summary': {
                name: {
                    'type': detail.get('类型', ''),
                    'jixiong': detail.get('吉凶', ''),
                    'duanyu': detail.get('断语', ''),
                }
                for name, detail in result['课格详情'].items()
                if detail.get('类型') not in ('三传属性', '三传属性（参考）')
            },
        }
        
        annotated.append(record)
        stats['annotated'] += 1
    
    # 写入标注结果
    output = {
        '_meta': {
            'name': '三传课格标注数据集',
            'version': '2.0.0',
            'created': '2026-07-29',
            'source': input_path,
            'engine': 'sanchuan_kege v2.0',
            'total_cases': stats['total'],
            'with_sanchuan': stats['with_sanchuan'],
            'annotated': stats['annotated'],
            'skipped': stats['skipped'],
        },
        'stats': {
            'kege_distribution': dict(stats['kege_counter'].most_common(50)),
            'signal_distribution': dict(stats['signal_counter']),
            'jixiong_distribution': dict(stats['jixiong_counter']),
        },
        'cases': annotated,
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return stats


def print_report(stats: dict):
    """打印标注统计报告"""
    print("=" * 70)
    print("三传课格批量标注报告")
    print("=" * 70)
    print(f"\n总案例数: {stats['total']}")
    print(f"有完整三传: {stats['with_sanchuan']}")
    print(f"成功标注: {stats['annotated']}")
    print(f"跳过: {stats['skipped']}")
    
    print(f"\n--- 课格分布 Top 30 ---")
    for kege, count in stats['kege_counter'].most_common(30):
        print(f"  {kege:20s}: {count:4d}")
    
    print(f"\n--- 股市信号分布 ---")
    for signal, count in stats['signal_counter'].most_common():
        pct = count / max(stats['annotated'], 1) * 100
        print(f"  {signal:12s}: {count:4d} ({pct:.1f}%)")
    
    print(f"\n--- 吉凶分布 ---")
    for jx, count in stats['jixiong_counter'].most_common():
        print(f"  {jx:12s}: {count:4d}")
    
    # 覆盖率
    no_kege = stats['annotated'] - sum(1 for k, c in stats['kege_counter'].items() if c > 0)
    kege_coverage = sum(1 for k, c in stats['kege_counter'].items() if c > 0)
    print(f"\n--- 覆盖率 ---")
    print(f"  识别到课格的案例: {kege_coverage}")
    print(f"  课格类型总数: {len(stats['kege_counter'])}")
    print(f"  平均每案例课格数: {sum(stats['kege_counter'].values()) / max(stats['annotated'], 1):.1f}")


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(__file__), 'extracted_data', '壬占汇选_训练数据_v2.json')
    output_path = os.path.join(os.path.dirname(__file__), 'data', 'sanchuan_kege_annotated_cases.json')
    
    stats = annotate_cases(input_path, output_path)
    print_report(stats)
    print(f"\n标注结果已保存: {output_path}")
