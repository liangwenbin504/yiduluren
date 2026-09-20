"""
DeepSeek 统一客户端 (deepseek_client.py)
========================================
封装 DeepSeek V4-Flash 官方最佳实践（2026-08）：
  1. 统一密钥管理（KeyManager 多服务商容错）
  2. 模型统一 deepseek-v4-flash 正式版
  3. 场景化 thinking / temperature / JSON 输出
  4. 指数退避重试（1s→2s→4s→8s）
  5. 缓存友好：system prompt 固定前缀 → 缓存命中省50倍

用法：
    from deepseek_client import DeepSeekClient, SCENE_RULE, SCENE_PREDICTION, SCENE_EXTRACT, SCENE_DEEP

    ds = DeepSeekClient()
    # 简单调用
    text = ds.chat("你好", system="你是六壬专家", scene=SCENE_RULE)
    # 结构化调用（JSON输出）
    data = ds.chat_json("提取案例", system="输出JSON", scene=SCENE_EXTRACT)
    # 完整控制
    resp = ds.call(messages=[...], scene=SCENE_PREDICTION, stream=False, extra={"user_id": "yidu"})
"""
import os
import sys
import time
import json
import random
from typing import Dict, List, Optional, Any

import requests

BASE = os.path.dirname(os.path.abspath(__file__))

# ──────────────── 场景配置（与 model_config.py 保持一致） ────────────────
# 规则判断类：无需思考，低温度，快速稳定（最省钱）
SCENE_RULE = {
    "thinking": False,
    "temperature": 0.1,
    "max_tokens": 1500,
}
# 综合预测类：需推理质量，开 thinking=high
SCENE_PREDICTION = {
    "thinking": True,
    "reasoning_effort": "high",
    "temperature": 0.3,
    "max_tokens": 3000,
}
# 数据抽取/清洗类：机械转换，非思考，JSON输出
SCENE_EXTRACT = {
    "thinking": False,
    "temperature": 0.0,
    "max_tokens": 2000,
    "response_format": {"type": "json_object"},
}
# 复杂深度分析：最强推理，thinking=max
SCENE_DEEP = {
    "thinking": True,
    "reasoning_effort": "max",
    "temperature": 0.5,
    "max_tokens": 8000,
}


class DeepSeekClient:
    """DeepSeek V4-Flash 统一客户端"""

    MODEL = "deepseek-v4-flash"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None):
        if api_key and base_url:
            self.api_key = api_key
            self.base_url = base_url
            self.model = model or self.MODEL
        else:
            key, url, model = self._load_config()
            self.api_key = key
            self.base_url = url
            self.model = model or self.MODEL

    def _load_config(self) -> tuple:
        """从 KeyManager 读取 DeepSeek 配置（优先）"""
        try:
            sys.path.insert(0, BASE)
            from api_key_manager import KeyManager, Provider
            km = KeyManager()
            cfg = km.get_best_provider(Provider.DEEPSEEK) or km.any_available()
            if cfg:
                m = cfg.chat_model
                if cfg.provider.value == "deepseek":
                    m = self.MODEL
                return cfg.api_key, cfg.base_url, m
        except Exception:
            pass
        # 兜底：环境变量
        key = os.getenv("DEEPSEEK_API_KEY", "")
        return key, "https://api.deepseek.com/chat/completions", self.MODEL

    def call(self, messages: List[Dict], scene: Dict = None,
             stream: bool = False, max_tokens: Optional[int] = None,
             response_format: Optional[Dict] = None,
             extra: Optional[Dict] = None,
             max_retries: int = 4) -> Dict[str, Any]:
        """
        核心调用方法（指数退避重试）

        返回: {"success": bool, "content": str, "model": str, "usage": dict}
        """
        if not self.api_key:
            return {"success": False, "error": "API Key未配置（请运行 python api_key_manager.py --check）"}

        scene = scene or SCENE_RULE

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        # 场景化参数
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        elif "max_tokens" in scene:
            payload["max_tokens"] = scene["max_tokens"]

        # thinking 控制（V4 默认开启，规则类显式关闭省钱）
        if "thinking" in scene:
            payload["thinking"] = {"type": "enabled" if scene["thinking"] else "disabled"}
        if scene.get("reasoning_effort"):
            payload["reasoning_effort"] = scene["reasoning_effort"]
        # thinking 模式下 temperature 无效，仅非思考模式传
        if not scene.get("thinking", True) and "temperature" in scene:
            payload["temperature"] = scene["temperature"]

        # JSON 模式
        fmt = response_format or scene.get("response_format")
        if fmt:
            payload["response_format"] = fmt

        # 额外参数（user_id 等）
        if extra:
            payload.update(extra)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_error = ""
        for attempt in range(max_retries):
            try:
                resp = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    message = data.get("choices", [{}])[0].get("message", {})
                    content = message.get("content", "") or ""
                    usage = data.get("usage", {})
                    return {
                        "success": True,
                        "content": content,
                        "reasoning_content": message.get("reasoning_content", ""),
                        "model": data.get("model", self.model),
                        "usage": usage,
                    }
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if resp.status_code == 401:
                    return {"success": False, "error": f"密钥无效(401): {last_error}"}
                if resp.status_code == 429:
                    backoff = 2 ** attempt + random.uniform(0, 0.5)
                    print(f"  ⏳ [{self.model}] 限流(429)，{backoff:.1f}s后重试 ({attempt+1}/{max_retries})")
                    time.sleep(backoff)
                    continue
            except requests.Timeout:
                last_error = "请求超时(120s)"
            except Exception as e:
                last_error = str(e)

            if attempt < max_retries - 1:
                backoff = 2 ** attempt
                print(f"  ⏳ [{self.model}] {last_error[:80]}，{backoff}s后重试 ({attempt+1}/{max_retries})")
                time.sleep(backoff)

        return {"success": False, "error": last_error}

    def chat(self, prompt: str, system: str = None, scene: Dict = None,
             max_tokens: Optional[int] = None) -> str:
        """简单文本对话"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = self.call(messages, scene=scene or SCENE_RULE, max_tokens=max_tokens)
        return r.get("content", "") if r.get("success") else ""

    def chat_json(self, prompt: str, system: str = None, scene: Dict = None,
                  max_tokens: Optional[int] = None) -> Any:
        """JSON 结构化输出（自动解析）"""
        # DeepSeek 官方要求：response_format=json 时，system 或 user 中必须含"json"字样
        if system and "json" not in system.lower():
            system += "\n\n你必须输出严格合法的JSON，不要输出其他文字。"
        elif not system:
            system = "你是数据抽取助手，必须输出严格合法的JSON，不要输出JSON以外的任何文字。"
        if "json" not in prompt.lower():
            prompt = prompt + "\n\n请以JSON格式输出。"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = self.call(messages, scene=scene or SCENE_EXTRACT,
                      response_format={"type": "json_object"}, max_tokens=max_tokens)
        if not r.get("success"):
            return None
        content = r["content"]
        # 清理可能的 markdown 包裹
        if content.startswith("```"):
            content = content.strip()
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0]
        try:
            return json.loads(content.strip())
        except Exception:
            m = re_search_json(content)
            if m:
                try:
                    return json.loads(m)
                except Exception:
                    pass
            return None


def re_search_json(text: str):
    """从文本中提取第一个JSON对象/数组"""
    import re
    # 找最外层括号
    for i, ch in enumerate(text):
        if ch == '{':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        return text[i:j + 1]
        elif ch == '[':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '[':
                    depth += 1
                elif text[j] == ']':
                    depth -= 1
                    if depth == 0:
                        return text[i:j + 1]
    return None


# 全局单例（保持向后兼容）
deepseek_client = DeepSeekClient()
