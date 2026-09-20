#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型配置文件 - 从环境变量读取 API Key
DeepSeek V4-Flash 正式版最佳实践（2026-08 优化版）

要点：
  1. 模型名统一 deepseek-v4-flash（正式版 V4-Flash-0731）
  2. 按场景区分 thinking / temperature / max_tokens
  3. base_url 不带 /v1（官方推荐 https://api.deepseek.com）
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ==================== 模型选择 ====================
ACTIVE_MODEL = os.environ.get("ACTIVE_MODEL", "deepseek")

# ==================== 通用默认值 ====================
DEFAULT_DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEFAULT_DEEPSEEK_URL = "https://api.deepseek.com"

# ==================== DeepSeek V4-Flash 配置 ====================
# 定价参考(每1M token)：
#   输入缓存命中 $0.0028 / 缓存未命中 $0.14 / 输出 $0.28
# 缓存策略：固定 system prompt 前缀 → 命中缓存省50倍
DEEPSEEK_CONFIG = {
    "api_key": DEFAULT_DEEPSEEK_KEY,
    "api_url": f"{DEFAULT_DEEPSEEK_URL}/chat/completions",
    "model": "deepseek-v4-flash",          # 正式版 V4-Flash-0731
    "max_tokens": 3000,
    "temperature": 0.3,                    # 占课/预测类任务低温度更稳定
    "thinking": False,                     # 规则类任务默认关闭思考，省钱
    "reasoning_effort": "high",
}

# ==================== 场景化配置（最划算 + 最有效率） ====================
# 规则判断类：无需思考，低温度，快速稳定
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
    "max_tokens": 800,
    "response_format": {"type": "json_object"},
}
# 复杂深度分析：最强推理，thinking=max
SCENE_DEEP = {
    "thinking": True,
    "reasoning_effort": "max",
    "temperature": 0.5,
    "max_tokens": 8000,
}

# ==================== Doubao-Seed-2.0-Code 配置 ====================
DOUBAO_SEED_CONFIG = {
    "api_key": "",  # 请在此输入您的 API Key
    "api_secret": "",  # 请在此输入您的 API Secret（如果需要）
    "api_url": "https://api.doubao.com/v1/chat/completions",  # 假设的 URL
    "model": "Doubao-Seed-2.0-Code",
    "max_tokens": 8192,
    "temperature": 0.7,
}

# ==================== 自定义模型配置 ====================
CUSTOM_CONFIG = {
    "api_key": "",
    "api_secret": "",
    "api_url": "",  # 自定义 API 端点
    "model": "",  # 自定义模型名称
    "max_tokens": 4000,
    "temperature": 0.7,
}

# ==================== 辅助函数 ====================
def get_active_config():
    """获取当前激活的模型配置"""
    configs = {
        "deepseek": DEEPSEEK_CONFIG,
        "doubao_seed": DOUBAO_SEED_CONFIG,
        "custom": CUSTOM_CONFIG,
    }
    return configs.get(ACTIVE_MODEL, DEEPSEEK_CONFIG)

def get_api_key():
    """获取当前模型的 API Key"""
    return get_active_config()["api_key"]

def get_api_url():
    """获取当前模型的 API URL"""
    return get_active_config()["api_url"]

def get_model_name():
    """获取当前模型名称"""
    return get_active_config()["model"]

def get_scene_config(scene: str = "rule"):
    """按场景获取推荐配置（rule/prediction/extract/deep）"""
    return {
        "rule": SCENE_RULE,
        "prediction": SCENE_PREDICTION,
        "extract": SCENE_EXTRACT,
        "deep": SCENE_DEEP,
    }.get(scene, SCENE_RULE)

def build_payload(scene: str = "rule", model: str = None, messages: list = None,
                  stream: bool = False, extra: dict = None) -> dict:
    """按场景构建 DeepSeek 最佳实践 payload"""
    base = get_active_config()
    scene_cfg = get_scene_config(scene)

    payload = {
        "model": model or base["model"],
        "messages": messages or [],
        "stream": stream,
        "max_tokens": scene_cfg.get("max_tokens", base.get("max_tokens", 3000)),
    }

    # thinking 模式：显式控制（默认 V4 开启，规则类任务强制关闭省钱）
    if "thinking" in scene_cfg:
        payload["thinking"] = {"type": "enabled" if scene_cfg["thinking"] else "disabled"}
    if scene_cfg.get("reasoning_effort"):
        payload["reasoning_effort"] = scene_cfg["reasoning_effort"]

    # thinking 模式下 temperature/top_p 无效，仅非思考模式传
    if not scene_cfg.get("thinking", True):
        payload["temperature"] = scene_cfg.get("temperature", base.get("temperature", 0.3))

    # JSON 模式
    if scene_cfg.get("response_format"):
        payload["response_format"] = scene_cfg["response_format"]

    if extra:
        payload.update(extra)

    return payload

# ==================== 初始化检查 ====================
def check_config():
    """检查配置是否有效"""
    config = get_active_config()
    if not config["api_key"]:
        print(f"警告: {ACTIVE_MODEL} 的 API Key 为空，请在 model_config.py 中配置")
        return False
    if not config["api_url"]:
        print(f"警告: {ACTIVE_MODEL} 的 API URL 为空")
        return False
    return True

# 打印当前配置
print(f"[模型配置] 激活模型: {ACTIVE_MODEL}")
print(f"[模型配置] 模型名称: {get_model_name()}")
print(f"[模型配置] API URL: {get_api_url()[:50]}...")
if check_config():
    print("[模型配置] 配置检查通过 ✓")
