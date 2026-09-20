#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Code ↔ Hermes 桥接器 v2.0
==============================
直接调用 DeepSeek API，无需 WSL/Hermes Agent。
用途：
  - 分析项目代码/架构/性能
  - 修复 bug 和诊断问题
  - 解读六壬盘面
  - 智能路由到项目各模块

用法：
  python hermes_bridge.py "分析 auto_scheduler.py 的潜在bug"
  python hermes_bridge.py --analyze-project .
  python hermes_bridge.py --analyze-file engine/yidu_liuren_yaojue.py
"""

import json, os, sys, io, argparse, re
from urllib.request import Request, urlopen
from urllib.error import URLError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── 配置 ──
try:
    from deepseek_client import DeepSeekClient, SCENE_DEEP
    _DS = DeepSeekClient()
    API_KEY = _DS.api_key
except Exception:
    _DS = None
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


# ── API 调用 ──

def call_deepseek(messages: list, model: str = MODEL, timeout: int = 120) -> str:
    """调用 DeepSeek API（V4-Flash 正式版 + 指数退避）"""
    try:
        if _DS:
            resp = _DS.call(messages, scene=SCENE_DEEP, stream=False, max_tokens=4096)
            if resp.get('success'):
                return resp['content']
            return f"[API调用失败] {resp.get('error', '')}"
    except Exception as e:
        pass
    # 兜底：直接调用（保留原逻辑）
    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }).encode('utf-8')

    req = Request(API_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    })

    try:
        resp = urlopen(req, timeout=timeout)
        body = json.loads(resp.read().decode('utf-8'))
        return body['choices'][0]['message']['content']
    except URLError as e:
        return f"[API连接失败] {e}"
    except Exception as e:
        return f"[错误] {e}"


# ── 项目上下文构建 ──

def _list_project_files(max_files: int = 50) -> str:
    """列出项目核心文件结构"""
    lines = []
    count = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '_archive', 'node_modules')]
        for f in files:
            if f.endswith(('.py', '.json', '.md', '.html')):
                rel = os.path.relpath(os.path.join(root, f), PROJECT_ROOT)
                if '/_archive/' in rel or '/__pycache__/' in rel:
                    continue
                lines.append(rel)
                count += 1
                if count >= max_files:
                    return '\n'.join(sorted(lines))
    return '\n'.join(sorted(lines))


def _read_file_safe(path: str, max_lines: int = 100) -> str:
    """安全读取文件内容"""
    full = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(full):
        return f"[文件不存在: {path}]"
    try:
        with open(full, encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            return ''.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} 行省略)"
        return ''.join(lines)
    except Exception as e:
        return f"[读取失败: {e}]"


# ── 智能分析命令 ──

def analyze_project(focus: str = "bug") -> str:
    """分析整个项目的代码质量和潜在问题"""
    file_list = _list_project_files(30)
    prompt = f"""你是大六壬择日股票预测项目（仪度六壬）的代码审查专家。请分析以下项目结构，重点查找{focus}相关问题。

项目文件结构：
{file_list}

请用中文回答：
1. {focus}方面存在哪些问题？
2. 优先级最高的3个修复建议
3. 是否有架构层面的隐患？"""
    return call_deepseek([
        {"role": "system", "content": "你是专业的Python代码审查专家，擅长发现bug和架构问题。回答简洁、具体、可操作。"},
        {"role": "user", "content": prompt},
    ])


def analyze_file(filepath: str) -> str:
    """分析单个文件的bug"""
    code = _read_file_safe(filepath, 200)
    if code.startswith('['):
        return code

    prompt = f"""请分析以下Python文件，找出潜在的bug、性能问题和代码质量问题。

文件: {filepath}
```python
{code}
```

请用中文回答：
1. 存在的bug（如有）
2. 性能瓶颈
3. 代码风格问题
4. 改进建议"""
    return call_deepseek([
        {"role": "system", "content": "你是专业的Python代码审查专家。"},
        {"role": "user", "content": prompt},
    ])


def ask_hermes(query: str, model: str = MODEL, timeout: int = 120) -> str:
    """通用问答——带项目上下文"""
    file_list = _list_project_files(20)
    prompt = f"""你是仪度六壬择日股票预测项目的AI助手。项目基于大六壬进行股票预测和择日分析。

当前项目文件：
{file_list}

用户问题：{query}

请用中文回答，结合项目实际情况给出具体的分析和建议。如果问题涉及代码，请给出具体代码示例。"""
    return call_deepseek([
        {"role": "system", "content": "你是仪度六壬择日系统（Python/LangGraph/Flask）的专家助手。六壬排盘、ML预测、斗首择日、拱贵禄马到山到向等均为项目核心模块。"},
        {"role": "user", "content": prompt},
    ], model, timeout)


# ── 命令行 ──

def main():
    parser = argparse.ArgumentParser(description='仪度六壬 Hermes 桥接器')
    parser.add_argument('query', nargs='?', help='向AI提问')
    parser.add_argument('--analyze-project', action='store_true', help='分析整个项目')
    parser.add_argument('--analyze-file', type=str, help='分析指定文件')
    parser.add_argument('--focus', type=str, default='bug', help='分析重点: bug/performance/architecture')
    parser.add_argument('--model', type=str, default=MODEL)
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args()

    print("=" * 60)
    print("  Hermes Bridge v2.0 — DeepSeek API 直连")
    print("=" * 60)

    if args.analyze_project:
        print("\n🔍 分析项目...\n")
        result = analyze_project(args.focus)
    elif args.analyze_file:
        print(f"\n🔍 分析文件: {args.analyze_file}\n")
        result = analyze_file(args.analyze_file)
    elif args.query:
        print(f"\n💬 提问: {args.query}\n")
        result = ask_hermes(args.query, args.model, args.timeout)
    else:
        result = "用法:\n  python hermes_bridge.py \"你的问题\"\n  python hermes_bridge.py --analyze-project\n  python hermes_bridge.py --analyze-file engine/yidu_liuren_yaojue.py"

    print(result)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
