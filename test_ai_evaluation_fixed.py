#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的 AI 评价功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

print("=" * 80)
print("AI 评价功能测试（修复版）")
print("=" * 80)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API 地址：{BASE_URL}")
print("=" * 80)
print()

# 测试数据
test_payload = {
    '日期': '2026-03-29',
    '四柱': '丙午 辛卯 己亥 甲子',
    '山向': '壬山丙向',
    '斗首课格': '元辰课',
    '斗首评分': 85,
    '六壬评分': 80,
    '综合评分': 82,
    '课格类型': '龙德课，富贵课',
    '课格列表': ['龙德课', '富贵课', '元首课'],
    '吉神': '天德，月德，三合，六合',
    '龙德课': True,
    '龙德类型': '真龙德',
    'daliuren_detail': {
        'shan_jia': '子',
        'xiang_shou': '午',
        'ri_qualified': True,
        'ri_shan_count': 1,
        'ri_xiang_count': 1,
        'yue_qualified': True,
        'yue_shan_count': 1,
        'qualified_count': 2
    }
}

print("【测试】AI 综合评价 API（传统断语模式）")
print("-" * 80)
try:
    start = datetime.now()
    response = requests.post(f"{BASE_URL}/api/ai/evaluate", json=test_payload, timeout=30)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"响应时间：{elapsed:.2f}秒")
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功：{data.get('success', False)}")
        
        if data.get('success'):
            # 显示 AI 服务状态
            ai_available = data.get('ai_service_available', False)
            message = data.get('message', '')
            print(f"AI 服务可用：{'✅ 是' if ai_available else '⚠️  否'}")
            if message:
                print(f"系统消息：{message}")
            
            # 显示 AI 评价
            ai_eval = data.get('ai_evaluation', '无')
            print(f"\n【AI 评价】")
            print("-" * 80)
            if ai_eval and len(ai_eval) > 0:
                print(ai_eval[:500])
                if len(ai_eval) > 500:
                    print("...（内容过长，仅显示前 500 字）")
            else:
                print("无 AI 评价")
            
            # 显示传统断语
            traditional = data.get('traditional_duanyu', '无')
            print(f"\n【传统断语】")
            print("-" * 80)
            if traditional and len(traditional) > 0:
                print(traditional[:800])
                if len(traditional) > 800:
                    print("...（内容过长，仅显示前 800 字）")
            else:
                print("无传统断语")
            
            # 显示结构化评价
            structured = data.get('structured_evaluation', {})
            print(f"\n【结构化评价】")
            print("-" * 80)
            print(json.dumps(structured, ensure_ascii=False, indent=2)[:300])
        else:
            print(f"❌ 错误：{data.get('error', '未知错误')}")
    else:
        print(f"❌ HTTP 错误：{response.text[:500]}")
except Exception as e:
    print(f"❌ 异常：{e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("测试完成！")
print("=" * 80)
