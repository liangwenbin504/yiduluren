"""
deepseek_legacy_compat.py
=========================
旧脚本兼容层：让老代码里的 OpenAI client 用法无缝升级到
DeepSeek V4-Flash 正式版最佳实践。

用法（在旧脚本顶部替换）：
    # 旧代码
    from openai import OpenAI
    api_key = os.environ.get('DEEPSEEK_API_KEY','')
    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com/v1')

    # 新代码（一键替换）
    from deepseek_legacy_compat import LegacyClient
    client = LegacyClient()

这样旧脚本里所有 client.chat.completions.create(model='deepseek-chat', ...)
都会自动升级为 deepseek-v4-flash + thinking控制 + JSON支持 + 指数退避。
"""
import os
import sys
import time
import json

BASE = os.path.dirname(os.path.abspath(__file__))


class _CompatCompletions:
    """模拟 client.chat.completions 接口"""

    def __init__(self, model: str):
        self.model = model

    def create(self, **kwargs):
        """升级版 create：自动切 V4-Flash + 最佳实践"""
        try:
            from deepseek_client import DeepSeekClient
            ds = DeepSeekClient()

            # 兼容参数
            model = kwargs.get("model", self.model)
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 3000)
            temperature = kwargs.get("temperature", 0.3)
            response_format = kwargs.get("response_format")
            stream = kwargs.get("stream", False)

            # 场景判断：默认规则场景（关闭thinking省钱），JSON请求走extract
            if response_format and response_format.get("type") == "json_object":
                from deepseek_client import SCENE_EXTRACT
                scene = dict(SCENE_EXTRACT)
                scene["max_tokens"] = max_tokens
            else:
                from deepseek_client import SCENE_RULE
                scene = dict(SCENE_RULE)
                scene["max_tokens"] = max_tokens

            resp = ds.call(
                messages,
                scene=scene,
                stream=stream,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            if not resp.get("success"):
                raise RuntimeError(resp.get("error", "DeepSeek调用失败"))

            content = resp.get("content", "")
            model = resp.get("model", model)

            # 构造与 OpenAI SDK 返回兼容的对象
            class Msg:
                pass
            msg = Msg()
            msg.content = content
            msg.role = "assistant"
            msg.reasoning_content = resp.get("reasoning_content", "")

            class Choice:
                pass
            choice = Choice()
            choice.message = msg
            choice.index = 0

            class CompletionsResp:
                def __init__(self):
                    self.choices = [choice]
                    self.model = model

            return CompletionsResp()
        except Exception as e:
            # 返回带error的假响应（兼容原脚本 try/except 结构）
            class ErrChoice:
                def __init__(self):
                    class M:
                        def __init__(self):
                            self.content = f"[DeepSeek调用失败] {e}"
                    self.message = M()
            class ErrResp:
                def __init__(self):
                    self.choices = [ErrChoice()]
            return ErrResp()


class LegacyClient:
    """兼容旧代码的客户端"""

    def __init__(self, api_key: str = None, base_url: str = None):
        # 忽略旧参数，统一走 deepseek_client 最佳实践
        self.model = "deepseek-v4-flash"

        # 同时暴露与旧代码一致的属性，防止旧代码引用
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or "https://api.deepseek.com"

    @property
    def chat(self):
        class _Chat:
            def __init__(self, parent):
                self._parent = parent
                self.completions = _CompatCompletions(parent.model)
        return _Chat(self)
