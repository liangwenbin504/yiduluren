#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes MCP 服务器 v2.0
======================
将 Hermes Bridge 能力暴露为 MCP 协议供 Deep Code 调用。
直接调用 DeepSeek API，无需 WSL。

工具列表:
  chat          - 智能问答（自动路由到项目各模块）
  analyze       - 分析项目文件/架构
  skills        - 查看可用技能
  predict       - 股票预测流水线
"""

import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from hermes_bridge import ask_hermes, analyze_file, analyze_project, call_deepseek


def handle_request(method: str, params: dict) -> dict:
    """处理 MCP 请求"""

    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "chat",
                    "description": "向项目AI助手提问。可咨询六壬排盘、ML预测、斗首择日、代码分析等。自动路由到最合适的模块。",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "问题"},
                            "model": {"type": "string", "default": "deepseek-chat"}
                        }
                    }
                },
                {
                    "name": "analyze",
                    "description": "分析项目文件或整个项目的代码质量/bug/架构问题",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "文件路径或 'project'（整个项目）"},
                            "focus": {"type": "string", "default": "bug", "description": "关注点: bug/performance/architecture"}
                        }
                    }
                },
                {
                    "name": "skills",
                    "description": "查看项目中可用的 Agent Skills 和模块",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "default": "", "description": "筛选关键词"}
                        }
                    }
                },
                {
                    "name": "predict",
                    "description": "执行股票预测流水线（六壬+ML+行情）",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "目标日期 YYYY-MM-DD，默认今天"}
                        }
                    }
                }
            ]
        }

    elif method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})

        if tool == "chat":
            query = args.get("query", "")
            model = args.get("model", "deepseek-chat")
            result = ask_hermes(query, model)
            return {"content": [{"type": "text", "text": result}]}

        elif tool == "analyze":
            target = args.get("target", "project")
            focus = args.get("focus", "bug")
            if target == "project":
                result = analyze_project(focus)
            else:
                result = analyze_file(target)
            return {"content": [{"type": "text", "text": result}]}

        elif tool == "skills":
            keyword = args.get("keyword", "")
            import os, glob
            skill_dir = os.path.join(os.path.dirname(__file__), '.agents', 'skills')
            skills = []
            if os.path.exists(skill_dir):
                for d in sorted(os.listdir(skill_dir)):
                    skill_md = os.path.join(skill_dir, d, 'SKILL.md')
                    if os.path.exists(skill_md):
                        with open(skill_md, encoding='utf-8') as f:
                            first = f.readline().strip()
                        name = first.replace('---', '').replace('name:', '').strip() if 'name:' in first else d
                        if not keyword or keyword.lower() in d.lower() or keyword.lower() in name.lower():
                            skills.append(f"  - {name} ({d})")
            result = "可用技能:\n" + '\n'.join(skills) if skills else "无匹配技能"
            return {"content": [{"type": "text", "text": result}]}

        elif tool == "predict":
            target = args.get("date", "")
            from langgraph_dag import PredictionPipeline
            pipeline = PredictionPipeline()
            pipeline.build()
            result = pipeline.run(target)
            summary = json.dumps({
                "date": result.get("target_date"),
                "liuren": result.get("liuren_prediction"),
                "ml": result.get("ml_prediction"),
                "consensus": result.get("consensus"),
                "accuracy": result.get("accuracy_trend"),
                "latency_ms": result.get("latency_ms"),
            }, ensure_ascii=False, indent=2)
            return {"content": [{"type": "text", "text": summary}]}

    return {"content": [{"type": "text", "text": f"未知方法: {method}"}]}


def main():
    """MCP stdio 协议主循环"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(
                request.get("method", ""),
                request.get("params", {})
            )
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            err = json.dumps({"error": str(e)}, ensure_ascii=False)
            sys.stdout.write(err + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
