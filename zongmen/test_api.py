#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 API 是否能正常返回四课三传
"""

import json
import urllib.request
import urllib.parse

# 测试 URL
base_url = "http://localhost:5000/api/qike"
params = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'yue_jiang': '子',
    'shi_chen': '子'
}

url = base_url + '?' + urllib.parse.urlencode(params)

print("=" * 60)
print("测试宗门九课 API")
print("=" * 60)
print(f"\n请求参数：{params}\n")

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        print("✅ 起课成功！\n")
        result = data.get('data', {})
        
        print(f"日干支：{result.get('ri_gan')}{result.get('ri_zhi')}")
        print(f"月将：{result.get('yue_jiang')}")
        print(f"时辰：{result.get('shi_chen')}")
        print()
        
        # 显示四课
        print("【四课】")
        sike = result.get('sike', [])
        for i, ke in enumerate(sike, 1):
            print(f"  第{i}课：上{ke[1]} 下{ke[2]} ({ke[0]})")
        print()
        
        # 显示三传
        print("【三传】")
        sanchuan = result.get('sanchuan', {})
        san_chuan_list = sanchuan.get('三传', [])
        chuan_names = ['初传', '中传', '末传']
        for i, chuan in enumerate(san_chuan_list):
            print(f"  {chuan_names[i]}: {chuan}")
        print()
        
        print(f"起法：{sanchuan.get('起法', '')}")
        print(f"课体：{sanchuan.get('课体', '')}")
        
        print("\n" + "=" * 60)
        print("✅ 测试通过！API 工作正常！")
        print("=" * 60)
    else:
        print("❌ 起课失败！")
        print(f"错误：{data.get('error', '未知错误')}")
        
except urllib.error.URLError as e:
    print("❌ 无法连接到 API 服务器！")
    print(f"错误：{e}")
    print("\n请确保已运行：python http_api_server.py")
except Exception as e:
    print(f"❌ 测试失败：{e}")
    import traceback
    traceback.print_exc()
