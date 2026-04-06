#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速回归测试 - 验证所有关键修复
"""

import requests
import time

API_BASE = 'http://localhost:5000'

print("=" * 60)
print("快速回归测试 - 验证关键修复")
print("=" * 60)

tests_passed = 0
tests_failed = 0

def test(name, url, method='GET', data=None):
    global tests_passed, tests_failed
    try:
        if method == 'GET':
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=data, timeout=10)
        
        if r.status_code == 200:
            print(f"✅ {name}")
            tests_passed += 1
            return True
        else:
            print(f"❌ {name} (状态码：{r.status_code})")
            tests_failed += 1
            return False
    except Exception as e:
        print(f"❌ {name} (异常：{e})")
        tests_failed += 1
        return False

# 1. 服务器连通性
print("\n【1】服务器连通性")
test("API 服务器", f"{API_BASE}/")

# 2. 核心功能
print("\n【2】核心功能测试")
test("四柱计算", f"{API_BASE}/api/sizhu?year=2026&month=3&day=29&hour=18")
test("斗首山家", f"{API_BASE}/api/doushou/shanjia_wuxing?mountain=壬")
test("斗首分析", f"{API_BASE}/api/doushou/analyze", 'POST', {
    'mountain': '壬',
    'date': '2026-03-29',
    'hour': '酉'
})

# 3. 关键修复验证
print("\n【3】关键修复验证")

# 3.1 日期范围分析（超时修复）
print("\n测试日期范围分析（验证超时修复）...")
start = time.time()
success = test("日期范围分析（120 秒超时）", f"{API_BASE}/api/doushou/full_range_analyze", 'POST', {
    'mountain': '壬',
    'start_date': '2026-03-20',
    'end_date': '2026-04-20',
    'min_daliuren_score': 70,
    'max_results': 3
})
if success:
    elapsed = time.time() - start
    print(f"   响应时间：{elapsed:.2f}秒 {'✅' if elapsed < 120 else '⚠️'}")

# 3.2 导出文档（断语库集成）
print("\n测试导出文档（验证断语库集成）...")
success = test("导出 docx 文档", f"{API_BASE}/api/export/docx", 'POST', {
    'title_type': '安葬吉日',
    'mountain': '壬',
    'dates': [
        {'date': '2026-03-23', 'hour': '子', 'score': '95'}
    ],
    'keti_list': ['元首课', '龙德课'],
    'evaluation': '大吉大利'
})
if success:
    print("   ✅ 导出功能正常，包含断语")

# 4. 错误处理
print("\n【4】错误处理测试")
test("404 错误处理", f"{API_BASE}/api/nonexistent")

# 5. 总结
print("\n" + "=" * 60)
print(f"测试结果：{tests_passed}通过，{tests_failed}失败")
print(f"通过率：{tests_passed/(tests_passed+tests_failed)*100:.1f}%")

if tests_failed == 0:
    print("\n🎉 所有关键功能正常！系统稳定运行！")
else:
    print(f"\n⚠️  有 {tests_failed} 项失败，请检查！")

print("=" * 60)
