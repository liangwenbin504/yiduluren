"""GLM评分服务 - 统一密钥管理 + 多服务商容错版本

支持的模型/服务商：
  1. Ox Alpha / GLM-5.3-Flash (智谱 BigModel，100万上下文，低价高性能，默认首选)
  2. DeepSeek V4-Flash (次级降级，快速低成本)
  3. 其他 OpenAI 兼容端点

用法：
    from glm_service import GLMService

    # 默认（GLM-5.3-Flash，KeyManager优先GLM）
    svc = GLMService()

    # 使用 Ox Alpha (GLM-5.3-Flash)
    svc = GLMService.ox_alpha()

    # 自定义
    svc = GLMService(api_key="sk-xxx", base_url="https://...", model="glm-5.3-flash")
"""
import requests
import json
import os
import re
import sys
import time
from typing import Optional, Dict, Any


BIGMODEL_BASE = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
OX_ALPHA_MODEL = "glm-5.3-flash"
FREE_MODEL = "glm-4-flash"


def _init_cfg():
    """读取统一 KeyManager；按优先级选择；失败则走环境变量兜底"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from api_key_manager import KeyManager, Provider
        km = KeyManager()
        cfg = km.get_best_provider(Provider.GLM) or km.get_best_provider(Provider.DEEPSEEK) or km.any_available()
        if cfg:
            model = cfg.chat_model
            if cfg.provider.value == "deepseek":
                model = "deepseek-v4-flash"
            elif cfg.provider.value == "glm":
                model = OX_ALPHA_MODEL
            return cfg.api_key, cfg.base_url, model, km
    except Exception:
        pass
    # 环境变量兜底优先级：BigModel > GLM > ZAI > DeepSeek
    key = (os.getenv('BIGMODEL_API_KEY') or
           os.getenv('GLM_API_KEY') or
           os.getenv('ZAI_API_KEY') or
           os.getenv('DEEPSEEK_API_KEY') or '')
    if key and key != 'your-bigmodel-api-key-here':
        return key, BIGMODEL_BASE, OX_ALPHA_MODEL, None
    return key, "https://api.deepseek.com/chat/completions", "deepseek-v4-flash", None


class GLMService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None):
        if api_key and base_url:
            self.api_key = api_key
            self.base_url = base_url.rstrip('/')
            self.model = model or "deepseek-v4-flash"
            self._km = None
        else:
            key, url, mdl, km = _init_cfg()
            self.api_key = key
            self.base_url = url.rstrip('/') if url else ""
            self.model = mdl
            self._km = km

    @classmethod
    def ox_alpha(cls, api_key: Optional[str] = None):
        """创建 Ox Alpha (GLM-5.3-Flash) 服务实例"""
        key = api_key or os.getenv('BIGMODEL_API_KEY', '') or os.getenv('GLM_API_KEY', '')
        if key == 'your-bigmodel-api-key-here':
            key = ''
        return cls(api_key=key, base_url=BIGMODEL_BASE, model=OX_ALPHA_MODEL)

    @classmethod
    def deepseek(cls, api_key: Optional[str] = None):
        """创建 DeepSeek V4-Flash 服务实例"""
        key = api_key or os.getenv('DEEPSEEK_API_KEY', '')
        return cls(api_key=key, base_url="https://api.deepseek.com/chat/completions", model="deepseek-v4-flash")

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_model(self, model: str):
        self.model = model

    def set_provider(self, provider: str = "deepseek", api_key: Optional[str] = None):
        """切换服务商: 'deepseek' | 'ox_alpha' | 'bigmodel'"""
        p = provider.lower()
        if p in ("deepseek", "ds"):
            self.base_url = "https://api.deepseek.com/chat/completions"
            self.model = "deepseek-v4-flash"
            if api_key:
                self.api_key = api_key
        elif p in ("ox_alpha", "bigmodel", "glm"):
            self.base_url = BIGMODEL_BASE
            self.model = OX_ALPHA_MODEL
            if api_key:
                self.api_key = api_key
            elif not self.api_key or self.api_key == 'your-bigmodel-api-key-here':
                # 【2026-09-05 修复】独立脚本/引擎直跑时未加载 .env → key 为空致 401；
                #   幂等加载 .env 使 key 始终可读（Flask 场景 load_dotenv 已加载则跳过）
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                except Exception:
                    pass
                self.api_key = os.getenv('BIGMODEL_API_KEY', '') or os.getenv('GLM_API_KEY', '')

    def generate(self, messages: list, temperature: float = 0.7, max_tokens: int = 2048,
                 thinking: bool = None, response_format: dict = None,
                 extra: dict = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        生成响应（支持多模型自适应）

        参数:
          messages: OpenAI格式消息列表
          temperature: 温度（部分模型无效）
          max_tokens: 最大输出token
          thinking: True=开启思考 / False=关闭思考 / None=跟随模型默认
          response_format: {'type': 'json_object'} 开启JSON输出
          extra: 额外参数（如 reasoning_effort, user_id 等）
          max_retries: 指数退避重试次数

        模型自适应：
          - glm-5.3-flash: 强制思考模式，用 reasoning_effort 控制强度 (low/high/max)
          - deepseek-v4-flash: 支持 thinking on/off
        """
        if not self.api_key:
            return {"error": "API Key未设置"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        is_glm_flash = "glm-5.3-flash" in self.model.lower()

        if is_glm_flash:
            # GLM-5.3-Flash 始终思考，用 reasoning_effort 控制强度
            effort = (extra or {}).pop("reasoning_effort", "low")
            if thinking is False:
                effort = "low"
            elif thinking is True:
                effort = effort or "high"
            payload["thinking"] = {"type": "enabled", "reasoning_effort": effort}
        else:
            # 其他模型：标准 thinking 控制
            if thinking is not None:
                payload["thinking"] = {"type": "enabled" if thinking else "disabled"}
                if thinking:
                    payload["reasoning_effort"] = (extra or {}).pop("reasoning_effort", "high")
            else:
                payload["temperature"] = temperature

        if response_format:
            payload["response_format"] = response_format

        if extra:
            payload.update(extra)

        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    message = result.get('choices', [{}])[0].get('message', {})
                    content = message.get('content', '')
                    reasoning_content = message.get('reasoning_content', '')
                    if not content:
                        content = reasoning_content
                    if content:
                        resp = {"success": True, "content": content}
                        if reasoning_content:
                            resp["reasoning_content"] = reasoning_content
                        return resp
                    return {"success": False, "error": "API返回空内容"}
                try:
                    error_json = response.json()
                except:
                    error_json = response.text
                # 429限流 → 指数退避重试
                if response.status_code == 429 and attempt < max_retries - 1:
                    backoff = 2 ** attempt
                    print(f"  ⏳ [{self.model}] 限流(429)，{backoff}s后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(backoff)
                    continue
                return {"success": False, "error": f"HTTP {response.status_code}: {error_json}"}
            except Exception as e:
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt
                    print(f"  ⏳ [{self.model}] 网络异常: {e}，{backoff}s后重试")
                    time.sleep(backoff)
                    continue
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "重试次数耗尽"}

    def _parse_json(self, content: str) -> dict:
        """从AI响应中提取JSON"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            m = re.search(r'\{[\s\S]*\}', content)
            if m:
                try:
                    return json.loads(m.group())
                except:
                    pass
            return {}

    def _with_model(self, model: str):
        """创建一个临时切换模型的副本（不影响原实例）"""
        import copy
        obj = copy.copy(self)
        obj.model = model
        return obj

    def grade_kanhua(self, title: str, student_text: str, image_desc: str = "") -> Dict[str, Any]:
        """看图写话评分 — 自动使用免费 glm-4-flash 节省费用"""
        if not self.api_key:
            return self._mock_kanhua(title, student_text)

        desc = f"\n图片描述：{image_desc}" if image_desc else ""

        messages = [
            {
                "role": "system",
                "content": "你是一位有20年经验的小学语文老师，正在教二升三年级（7-8岁）的孩子。请以鼓励为主，评价孩子的看图写话。"
            },
            {
                "role": "user",
                "content": f"""请评价这位二年级小朋友的看图写话：

作文题目：{title}{desc}

学生写话：
{student_text}

请从以下维度评分（每项满分100，总分为加权平均）：
1. 内容完整（30分）：是否描述了图上的主要内容
2. 语句通顺（25分）：句子是否通顺，有没有明显语病
3. 观察仔细（20分）：有没有注意到图中的细节
4. 词汇运用（15分）：是否用了好词好句
5. 标点正确（10分）：标点符号使用是否正确

请用JSON格式回复，注意用鼓励的语气：
{{
    "total_score": 总分,
    "comment": "总评（用温暖鼓励的语气，100字以内，用⭐💡等emoji）",
    "strengths": "亮点（30字以内）",
    "suggestion": "小建议（30字以内）"
}}
"""
            }
        ]

        # 评分任务走免费模型（规则明确，不需要深度推理）
        r = self._with_model(FREE_MODEL).generate(
            messages, temperature=0.7, thinking=False,
            response_format={"type": "json_object"}, max_tokens=1024
        )
        if r.get("success"):
            parsed = self._parse_json(r["content"])
            if parsed:
                return parsed
        # 免费模型失败时回退到默认模型
        result = self.generate(messages, temperature=0.7, thinking=False,
                               response_format={"type": "json_object"}, max_tokens=1024)
        if result.get("success"):
            parsed = self._parse_json(result["content"])
            if parsed:
                return parsed
        return self._mock_kanhua(title, student_text)

    def grade_yuedu(self, question: str, student_answer: str, standard_answer: str) -> Dict[str, Any]:
        """阅读理解评分 — 自动使用免费 glm-4-flash 节省费用"""
        if not self.api_key:
            return self._mock_yuedu(question, student_answer, standard_answer)

        messages = [
            {
                "role": "system",
                "content": "你是一位资深小学语文教师，擅长阅读理解教学。请分析学生的阅读理解答案，给出评分和改进建议。"
            },
            {
                "role": "user",
                "content": f"""请分析以下阅读理解题目和学生的答案：

题目：{question}

标准答案：{standard_answer}

学生答案：{student_answer}

请从以下维度分析：
1. 是否抓住了关键点
2. 理解和表达的准确性
3. 给出一个0-100的分数
4. 给出简短的改进建议

请用JSON格式回复：{{"score": 分数, "comment": "分析内容（用鼓励语气，100字以内）", "suggestion": "改进建议（30字以内）"}}
"""
            }
        ]

        # 免费模型优先
        r = self._with_model(FREE_MODEL).generate(
            messages, temperature=0.7, thinking=False,
            response_format={"type": "json_object"}, max_tokens=1024
        )
        if r.get("success"):
            parsed = self._parse_json(r["content"])
            if parsed:
                return parsed
        # 回退
        result = self.generate(messages, temperature=0.7, thinking=False,
                               response_format={"type": "json_object"}, max_tokens=1024)
        if result.get("success"):
            parsed = self._parse_json(result["content"])
            if parsed:
                return parsed
        return self._mock_yuedu(question, student_answer, standard_answer)

    def grade_sentence(self, question_content: str, student_answer: str, standard_answer: str) -> Dict[str, Any]:
        """句子练习评分 — 自动使用免费 glm-4-flash 节省费用"""
        if not self.api_key:
            return self._mock_sentence(student_answer, standard_answer)

        messages = [
            {
                "role": "system",
                "content": "你是一位资深小学语文教师，擅长句子练习批改。请直接输出JSON结果。"
            },
            {
                "role": "user",
                "content": f"""请根据题目原文中的具体要求，对学生答案进行评分。

题目原文（含具体写作要求）：{question_content}

学生答案：{student_answer}

标准答案参考：{standard_answer}

评分规则：
- 学生答案不必逐字与标准答案相同，意思对即可
- 如果学生答案存在错别字或语序不当但意思正确，适当扣分（扣10-20%）
- 空白答案给0分

请用JSON格式回复：{{"score": 0-100的分数, "comment": "分析内容（用鼓励语气，60字以内）", "suggestion": "改进建议（30字以内）"}}
"""
            }
        ]

        # 免费模型优先
        r = self._with_model(FREE_MODEL).generate(
            messages, temperature=0.5, thinking=False,
            response_format={"type": "json_object"}, max_tokens=1024
        )
        if r.get("success"):
            parsed = self._parse_json(r["content"])
            if parsed:
                return parsed
        # 回退
        result = self.generate(messages, temperature=0.5, thinking=False,
                               response_format={"type": "json_object"}, max_tokens=1024)
        if result.get("success"):
            parsed = self._parse_json(result["content"])
            if parsed:
                return parsed
        return self._mock_sentence(student_answer, standard_answer)

    @staticmethod
    def _lcs(s1: str, s2: str) -> str:
        n, m = len(s1), len(s2)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        i, j = n, m
        chars = []
        while i > 0 and j > 0:
            if s1[i - 1] == s2[j - 1]:
                chars.append(s1[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        return ''.join(reversed(chars))

    @staticmethod
    def _mock_kanhua(title: str, student_text: str) -> Dict[str, Any]:
        score = min(95, 50 + max(0, len(student_text) // 5))
        return {
            "total_score": score,
            "comment": f"⭐ 写得真不错！你写了{len(student_text)}个字，内容很丰富。继续加油！",
            "strengths": "能完整表达自己的想法",
            "suggestion": "💡 可以多用一些好词好句，让文章更生动"
        }

    @staticmethod
    def _mock_yuedu(question: str, student_answer: str, standard_answer: str) -> Dict[str, Any]:
        if not student_answer:
            return {"score": 0, "comment": "没有作答，请再想想哦", "suggestion": ""}
        similarity = len(set(student_answer) & set(standard_answer)) / max(len(set(standard_answer)), 1)
        score = int(60 + similarity * 40)
        return {
            "score": score,
            "comment": f"⭐ 答得不错，抓住了{int(similarity * 100)}%的关键点",
            "suggestion": "💡 可以再仔细读读原文，说不定有更多发现"
        }

    @staticmethod
    def _mock_sentence(student_answer: str, standard_answer: str) -> Dict[str, Any]:
        if not student_answer:
            return {"score": 0, "comment": "没有写答案哦", "suggestion": ""}
        lcs_str = GLMService._lcs(student_answer, standard_answer)
        coverage = len(lcs_str) / max(len(standard_answer), 1)
        score = int(coverage * 100)
        return {
            "score": score,
            "comment": f"⭐ 与标准答案相似度{score}%",
            "suggestion": ""
        }


glm_service = GLMService()