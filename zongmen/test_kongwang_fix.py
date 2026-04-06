#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试三传空亡规则修改：
1. 空亡时天干位置保留空字符占位
2. 不显示【空亡】提示信息
"""

import json
import urllib.request
import urllib.parse

base_url = "http://localhost:5000/api/qike"

# 测试：甲子日 戌将子时（涉害课）- 初传空亡
print("测试：甲子日 戌将子时（涉害课）")
print("=" * 60)
print("日干支：甲子（甲子旬，戌亥空）")
print("预期结果：")
print("  - 初传戌土为空亡，但天干位置应有遁干（甲），不显示空亡提示")
print("  - 三传干支应显示为：甲戌、壬申、庚午")
print("  - 三传空亡数组应全为空字符串：['', '', '']")
print()

params = {'ri_gan': '甲', 'ri_zhi': '子', 'yue_jiang': '戌', 'shi_chen': '子'}
url = base_url + '?' + urllib.parse.urlencode(params)

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('success'):
        sanchuan = data.get('data', {}).get('sanchuan', {})
        
        print("实际返回结果:")
        print(f"  三传：{sanchuan.get('三传', [])}")
        print(f"  三传天干：{sanchuan.get('三传天干', [])}")
        print(f"  三传干支：{sanchuan.get('三传干支', [])}")
        print(f"  三传六亲：{sanchuan.get('三传六亲', [])}")
        print(f"  三传天将：{sanchuan.get('三传天将', [])}")
        print(f"  三传空亡：{sanchuan.get('三传空亡', [])}")
        
        print("\n三传显示效果:")
        chuan_names = ['初传', '中传', '末传']
        ganzhi_list = sanchuan.get('三传干支', [])
        liuqin_list = sanchuan.get('三传六亲', [])
        tianjiang_list = sanchuan.get('三传天将', [])
        kongwang_list = sanchuan.get('三传空亡', [])
        
        for i, ganzhi in enumerate(ganzhi_list):
            liuqin = liuqin_list[i] if i < len(liuqin_list) else ''
            tianjiang = tianjiang_list[i] if i < len(tianjiang_list) else ''
            kongwang = kongwang_list[i] if i < len(kongwang_list) else ''
            
            display = f"  {chuan_names[i]}: "
            if liuqin:
                display += f"[{liuqin}]"
            display += ganzhi
            if tianjiang:
                display += f" ({tianjiang})"
            # 不再显示空亡提示
            # if kongwang:
            #     display += f" [{kongwang}]"
            print(display)
        
        print("\n验证结果:")
        # 验证 1：三传天干应该有值（即使空亡也有遁干）
        stem_list = sanchuan.get('三传天干', [])
        if len(stem_list) > 0 and stem_list[0]:  # 初传天干应该有值
            print("  ✓ 空亡的地支也有遁干（天干位置有值）")
        else:
            print("  ✗ 空亡的地支遁干缺失")
        
        # 验证 2：三传空亡数组应该全为空
        if all(k == '' for k in kongwang_list):
            print("  ✓ 三传空亡数组全为空字符串（不显示空亡提示）")
        else:
            print("  ✗ 三传空亡数组包含非空值")
        
        # 验证 3：三传干支应该包含天干
        if len(ganzhi_list) > 0 and len(ganzhi_list[0]) == 2:
            print("  ✓ 三传干支格式正确（天干 + 地支）")
        else:
            print("  ✗ 三传干支格式不正确")
            
    else:
        print("失败:", data.get('error', ''))
except Exception as e:
    print(f"错误：{e}")
    print("请确保 API 服务器已启动（运行 http_api_server.py）")
