#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当代六壬案例爬虫
================
自动抓取：知乎/东方术士(39long)/股吧 的六壬案例，
用 DeepSeek 解析 HTML → 结构化 JSON → 入库。

用法:
  python crawl_modern_cases.py          # 全量爬取
  python crawl_modern_cases.py --quick  # 快速模式(只爬10页)
"""

import json, os, sys, io, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
from pathlib import Path

BASE = Path(__file__).parent
KB_FILE = BASE / "extracted_data" / "壬占汇选_训练数据_v2.json"
# 统一密钥管理（DeepSeek V4-Flash 正式版）
try:
    from deepseek_client import DeepSeekClient, SCENE_EXTRACT
    DS_CLIENT = DeepSeekClient()
    API_KEY = DS_CLIENT.api_key
except Exception:
    DS_CLIENT = None
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ── 目标URL ──
TARGETS = [
    # 东方术士 - 六壬案例列表页
    {
        "name": "东方术士-大六壬案例",
        "url": "https://39long.com/daliuren",
        "pages": 5,  # 爬5页
    },
    {
        "name": "东方术士-灵觉经案例",
        "url": "https://39long.com/node/1167",
        "pages": 1,
    },
    # 知乎专栏文章(可通过API获取)
    {
        "name": "知乎-六壬案例",
        "url": "https://zhuanlan.zhihu.com/p/600732234",  # 壬海拾贝
        "pages": 1,
    },
    {
        "name": "知乎-股市预测2024",
        "url": "https://zhuanlan.zhihu.com/p/678206020",
        "pages": 1,
    },
    # 股吧
    {
        "name": "股吧-六壬测股票",
        "url": "http://liaoba.yjcf360.com/liaoba/301025/4137738.htm",
        "pages": 1,
    },
]

# ── HTML抓取 ──
def fetch_url(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(f"    ⚠️ 抓取失败 {url[:50]}: {e}")
        return None


def fetch_paginated(base_url, max_pages=5):
    """东方术士分页抓取"""
    all_text = []
    for page in range(max_pages):
        url = f"{base_url}?page={page}" if page > 0 else base_url
        html = fetch_url(url)
        if html:
            # 提取正文(去除导航)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            text = text[:8000]  # 限制长度
            all_text.append(text)
            print(f"    页{page+1}: {len(text)}字符")
        time.sleep(1)
    return '\n--- 分页 ---\n'.join(all_text)


# ── DeepSeek 解析 ──
def llm_extract_cases(page_text, source_name):
    """用DeepSeek从页面文本中提取六壬案例"""
    prompt = f"""你是六壬专家。从以下网页文本中提取所有大六壬占卜案例，返回JSON数组。

每个案例字段(有则提取,无则null)：
- ganzhi: 日干支(如"乙酉")
- yuejiang: 月将(如"午将")
- shichen: 时辰(如"未时")
- question: 占问何事
- sanchuan: 三传数组(3个天干地支)
- keti: 课体名称
- prediction: 占断预测内容
- outcome: 实际验证结果
- source: 来源名称

只输出JSON数组，不要其他文字。文本：
{page_text[:6000]}
"""
    try:
        if DS_CLIENT:
            # 统一客户端：JSON输出 + 指数退避重试
            cases = DS_CLIENT.chat_json(prompt, scene=SCENE_EXTRACT, max_tokens=4000)
            return cases if isinstance(cases, list) else []
        # 兜底：直接调用
        r = requests.post('https://api.deepseek.com/chat/completions',
            headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek-v4-flash', 'messages': [{'role': 'user', 'content': prompt}],
                  'max_tokens': 4000, 'temperature': 0.1,
                  'thinking': {'type': 'disabled'},
                  'response_format': {'type': 'json_object'}},
            timeout=120)
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content'].strip()
            try:
                cases = json.loads(content)
                return cases if isinstance(cases, list) else []
            except:
                print(f"    JSON解析失败, 原始: {content[:200]}")
                return []
        else:
            print(f"    API错误: {r.status_code}")
            return []
    except Exception as e:
        print(f"    LLM异常: {e}")
        return []


# ── 主流程 ──
def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--quick', action='store_true')
    args = p.parse_args()

    print("=" * 55)
    print("  当代六壬案例爬虫 (DeepSeek解析)")
    print("=" * 55)

    # 加载现有案例
    with open(KB_FILE, 'r', encoding='utf-8') as f:
        all_cases = json.load(f)
    print(f"  现有案例: {len(all_cases)}")

    max_pages = 1 if args.quick else None
    total_new = 0

    for target in TARGETS:
        name = target['name']
        url = target['url']
        pages = target.get('pages', 1) if max_pages is None else min(1, target.get('pages', 1))

        print(f"\n  🌐 爬取: {name}")
        print(f"     URL: {url}")

        # 抓取
        if pages > 1:
            text = fetch_paginated(url, pages)
        else:
            text = fetch_url(url)
            if text:
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text)[:8000]

        if not text:
            print(f"    ⚠️ 无内容")
            continue

        # LLM解析
        print(f"    🤖 DeepSeek解析中...")
        cases = llm_extract_cases(text, name)
        if cases:
            valid = [c for c in cases if c.get('ganzhi') and c.get('sanchuan')]
            print(f"    ✅ 提取 {len(cases)} 个案例 (有效: {len(valid)})")
            for c in valid[:3]:
                print(f"       {c.get('ganzhi','?')}日 {c.get('yuejiang','?')} {c.get('question','?')[:30]}")
            all_cases.extend(valid)
            total_new += len(valid)
        else:
            print(f"    ⚠️ 未提取到案例,可能是反爬或页面复杂")

        time.sleep(2)  # API限速

    # 保存
    with open(KB_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_cases, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"  ✅ 完成! 新增 {total_new} 个案例")
    print(f"  总案例: {len(all_cases)}")
    print(f"  文件: {KB_FILE}")


if __name__ == '__main__':
    main()
