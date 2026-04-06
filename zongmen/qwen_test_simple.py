# -*- coding: utf-8 -*-
"""
使用 Qwen Max API 分析第一课（简化版）
"""

from dashscope import Generation
import json

API_KEY = '***REMOVED***'

# 第一课内容
text = """第一课
元首课：万事顺利，元亨利贞
【原文】
凡一上克下，余课无克，为元首课，象天。如君克臣，必顺其正，无乱动反常之理。为九宗之元，六十四课之首，故名元首。君占则有伊吕之臣，臣占必遇唐虞之君；常人占之，万事顺利。大哉元首，元亨利贞，首出庶物，万国咸宁，统乾之体，乃元吉第一课也。
象曰："天地得位，品物咸新。事用君子，忧喜俱真。君臣和合，父子慈亲。婚谐鸾凤，孕育麒麟。用兵客胜，论讼先陈。市贾出色，各利超群。官职首擢，柱石元勋。门庭喜溢，利见大人。"
【白话提要】
四课中有一课为上克下，其余课中没有克贼，即为元首课。元首课象为天，是九宗门的第一种，也是六十四课中的第一课。元首课中以上克下，这就如同君主克侍臣，是顺理成章的事，不会出现悖礼反常的情况。天地得位，以尊制卑，为诸课之首，故名为元首课。
君王占到此课，会得到像伊尹和吕尚一样的大臣；臣子占到此课，会遇到像唐尧和虞舜一样的君主；常人占到此课，会万事顺利。元首课为大吉大利之课。"""

print("=" * 70)
print("使用 Qwen Max API 分析第一课（元首课）")
print("=" * 70)

task = """请对这段六壬课内容进行分析，提取以下信息并以 JSON 格式返回：

1. 课名和副标题
2. 核心定义（用一句话概括）
3. 占断规则（列出 3-5 个关键点）
4. 吉凶属性
5. 象曰内容
6. 重要术语（3-5 个）

JSON 格式：
{
    "lesson_name": "课名",
    "subtitle": "副标题",
    "core_definition": "核心定义",
    "divination_rules": ["规则 1", "规则 2", "规则 3"],
    "fortune": "吉凶",
    "xiang_yue": "象曰内容",
    "key_terms": {"术语 1": "解释 1", "术语 2": "解释 2"}
}

待分析内容：
""" + text

print("\n正在调用 Qwen Max API...")
print("（这可能需要 10-30 秒）\n")

try:
    response = Generation.call(
        model='qwen-max',
        api_key=API_KEY,
        messages=[
            {'role': 'system', 'content': '你是一位精通大六壬的专家。'},
            {'role': 'user', 'content': task}
        ],
        max_tokens=1500,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.output.choices[0].message.content
        print("✓ API 调用成功！\n")
        print("=" * 70)
        print("分析结果：")
        print("=" * 70)
        print(result)
        
        # 保存结果
        output_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\qwen_analysis\lesson_01_result.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n✓ 结果已保存：{output_path}")
    else:
        print(f"✗ API 调用失败：{response.code} - {response.message}")
        
except Exception as e:
    print(f"✗ 发生错误：{str(e)}")

print("\n" + "=" * 70)
