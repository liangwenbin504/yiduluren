"""
DeepSeek API 本地代理 — 过滤 image_url 等多模态内容

========================================
  解决问题：
  Trae IDE 会自动注入工作区截图/文件预览等 image_url 内容，
  但 deepseek-v4-flash 是纯文本模型，收到 image_url 会报 400：
  "unknown variant `image_url`, expected `text`"

  解决方案：
  在 Trae IDE 和 DeepSeek 之间架设本地代理，自动剥离 image_url，
  将图片内容替换为文字占位符，再转发给 DeepSeek。

  Trae IDE 配置：
    Base URL → http://localhost:8765
    API Key  → 你的 DeepSeek Key
    模型名   → deepseek-v4-flash
========================================

用法:
  python deepseek_proxy.py                # 默认端口 8765
  python deepseek_proxy.py --port 9000    # 自定义端口
  python deepseek_proxy.py --debug       # 开启调试日志
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, Response, stream_with_context
import requests as http_requests

# ──────────────── 配置 ────────────────
DEEPSEEK_BASE = "https://api.deepseek.com"
PORT = 8765
DEBUG = "--debug" in sys.argv
if "--port" in sys.argv:
    idx = sys.argv.index("--port")
    if idx + 1 < len(sys.argv):
        PORT = int(sys.argv[idx + 1])

# ──────────────── 日志 ────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ds_proxy")

app = Flask(__name__)


# ──────────────── 核心：清洗 messages ────────────────
def clean_messages(messages):
    """
    清洗消息列表，剥离所有 image_url 类型的内容。

    OpenAI 消息格式:
      messages[i].content 可以是:
        - string (纯文本，无需处理)
        - list of content blocks, 例如:
          [
            {"type": "text", "text": "..."},
            {"type": "image_url", "image_url": {"url": "..."}},  ← 要去掉
          ]

    处理策略:
      1. content 是 list → 过滤掉 image_url 块，只保留 text 块
      2. 如果过滤后 list 只剩1个 text 块 → 简化为 string
      3. 如果过滤后 list 为空 → 替换为占位符
      4. content 是 string → 不处理
    """
    cleaned = 0

    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue

        new_blocks = []
        for block in content:
            btype = block.get("type", "")
            if btype == "image_url":
                cleaned += 1
                # 替换为文字占位符
                new_blocks.append({
                    "type": "text",
                    "text": "[图片已过滤：纯文本模型不支持图片输入]"
                })
            elif btype == "text":
                new_blocks.append(block)
            else:
                # 其他类型（如 audio）也过滤
                cleaned += 1
                new_blocks.append({
                    "type": "text",
                    "text": f"[{btype}内容已过滤]"
                })

        # 简化：如果只剩1个 text 块，转为 string
        if len(new_blocks) == 1 and new_blocks[0]["type"] == "text":
            msg["content"] = new_blocks[0]["text"]
        elif len(new_blocks) == 0:
            msg["content"] = "[内容已过滤]"
        else:
            msg["content"] = new_blocks

    return cleaned


def clean_tools(tools):
    """
    清洗 tools 定义，确保 schema 兼容纯文本模型。
    某些工具定义中可能含有不兼容的 schema 字段。
    """
    if not tools:
        return tools

    cleaned_tools = []
    for tool in tools:
        # 确保有 type 字段
        if "type" not in tool:
            tool["type"] = "function"
        # 确保 function 字段存在
        if "function" not in tool and "function" == tool.get("type"):
            continue
        cleaned_tools.append(tool)

    return cleaned_tools


# ──────────────── 代理路由 ────────────────
@app.route("/chat/completions", methods=["POST"])
@app.route("/v1/chat/completions", methods=["POST"])
def proxy_chat_completions():
    """代理 /chat/completions 端点"""

    body = request.get_json(silent=True)
    if not body:
        return {"error": {"message": "Invalid JSON body", "code": "invalid_request_error"}}, 400

    # ── 1. 清洗 messages ──
    messages = body.get("messages", [])
    removed = clean_messages(messages)
    if removed > 0:
        log.info(f"🧹 已过滤 {removed} 个 image_url 内容块 (共 {len(messages)} 条消息)")

    # ── 2. 清洗 tools ──
    if "tools" in body:
        body["tools"] = clean_tools(body.get("tools"))

    # ── 3. 确保模型名正确 ──
    model = body.get("model", "deepseek-v4-flash")
    log.info(f"📤 转发请求 → DeepSeek (model={model}, messages={len(messages)}, stream={body.get('stream', False)})")

    # ── 4. 提取 API Key ──
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return {"error": {"message": "Missing API key in Authorization header", "code": "invalid_request_error"}}, 401

    api_key = auth[7:]  # 去掉 "Bearer "

    # ── 5. 转发到 DeepSeek ──
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    target_url = f"{DEEPSEEK_BASE}/chat/completions"
    is_stream = body.get("stream", False)

    try:
        if is_stream:
            # 流式响应
            resp = http_requests.post(
                target_url, headers=headers, json=body,
                stream=True, timeout=300,
            )

            if resp.status_code != 200:
                log.error(f"❌ DeepSeek 返回 {resp.status_code}: {resp.text[:300]}")
                return {"error": {"message": resp.text[:500], "code": "upstream_error"}}, resp.status_code

            def generate():
                for chunk in resp.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk

            return Response(
                stream_with_context(generate()),
                content_type=resp.headers.get("Content-Type", "text/event-stream"),
            )
        else:
            # 非流式响应
            resp = http_requests.post(
                target_url, headers=headers, json=body,
                timeout=120,
            )

            if resp.status_code != 200:
                log.error(f"❌ DeepSeek 返回 {resp.status_code}: {resp.text[:300]}")
                return {"error": {"message": resp.text[:500], "code": "upstream_error"}}, resp.status_code

            log.info(f"✅ DeepSeek 响应成功 ({len(resp.content)} bytes)")
            return Response(resp.content, status=200, content_type="application/json")

    except http_requests.Timeout:
        log.error("❌ 请求超时")
        return {"error": {"message": "Request timeout", "code": "timeout"}}, 504
    except Exception as e:
        log.error(f"❌ 代理异常: {e}")
        return {"error": {"message": str(e), "code": "proxy_error"}}, 502


# ──────────────── 其他端点透传 ────────────────
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_passthrough(path):
    """其他端点直接透传"""
    target_url = f"{DEEPSEEK_BASE}/{path}"
    auth = request.headers.get("Authorization", "")
    headers = {"Content-Type": request.content_type or "application/json"}
    if auth:
        headers["Authorization"] = auth

    try:
        resp = http_requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            timeout=120,
        )
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type", "application/json"))
    except Exception as e:
        return {"error": {"message": str(e), "code": "proxy_error"}}, 502


@app.route("/", methods=["GET"])
def index():
    return {
        "service": "DeepSeek API Proxy",
        "status": "running",
        "target": DEEPSEEK_BASE,
        "features": ["image_url过滤", "多模态内容剥离", "纯文本模型适配"],
        "port": PORT,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "port": PORT}


# ──────────────── 启动 ────────────────
if __name__ == "__main__":
    print()
    print("=" * 55)
    print("  🔧 DeepSeek API 本地代理 (image_url 过滤)")
    print("=" * 55)
    print(f"  监听端口: {PORT}")
    print(f"  目标地址: {DEEPSEEK_BASE}")
    print(f"  调试模式: {'开启' if DEBUG else '关闭'}")
    print()
    print("  Trae IDE 配置:")
    print(f"    Base URL → http://localhost:{PORT}")
    print(f"    API Key  → 你的 DeepSeek Key")
    print(f"    模型名   → deepseek-v4-flash")
    print("=" * 55)
    print()

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG, threaded=True)
