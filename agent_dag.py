#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日 — LangGraph Agent DAG v2.0 (生产级)
=================================================
双模型协作流水线：
  - 简单任务 → 本地 DeepSeek-Coder-v2 独立完成（零网络开销）
  - 复杂任务 → Kimi (Moonshot) 架构分析 + DeepSeek 编码 + Kimi 整合
  - 修复任务 → 自动加载 .agents/skills/ 下技能，走 fix_verify 门控流程

图结构:
  START → classify ─┬─ fix_verify ─┬─ END
                     ├─ simple  → deepseek_solo ──────→ END
                     └─ complex → kimi_analyze → deepseek_code → kimi_merge → END

环境依赖: dag.env (MOONSHOT_API_KEY, OLLAMA_URL)
"""

import os, re, json, logging, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

log = logging.getLogger("agent_dag")
BASE = Path(__file__).parent

# ── 技能加载 ──
def _load_skills():
    """扫描 .agents/skills/ 下所有 SKILL.md"""
    skills_dir = BASE / ".agents" / "skills"
    skills = {}
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skmd = skill_dir / "SKILL.md"
                if skmd.exists():
                    name = skill_dir.name
                    content = skmd.read_text(encoding='utf-8')
                    skills[name] = content
                    log.info("技能加载: %s (%d 字符)", name, len(content))
    return skills

_SKILLS = _load_skills()

def _get_skill_prompt(task: str) -> str:
    """根据任务内容匹配技能，返回注入提示"""
    keywords_fix = ["fix", "修复", "bug", "error", "不工作", "修一下", "修好", "不显示", "错误", "报错"]
    for kw in keywords_fix:
        if kw in task.lower():
            return _SKILLS.get("agent-fix-verify", "")
    return ""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import TypedDict, Optional, Dict, Any, Literal
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# ── 路径 ──
BASE = Path(__file__).parent
ENV_PATH = BASE / "dag.env"
LOG_DIR = BASE / "_memory"


# ══════════════════════════════════════════════════════════
# 日志
# ══════════════════════════════════════════════════════════

def _setup_logger() -> logging.Logger:
    os.makedirs(str(LOG_DIR), exist_ok=True)
    logger = logging.getLogger("agent_dag")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname).1s] %(name)s:%(lineno)d %(message)s",
            "%H:%M:%S",
        )
        # 控制台
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        # 文件
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            str(LOG_DIR / "agent_dag.log"), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


log = _setup_logger()


# ══════════════════════════════════════════════════════════
# 配置 & 环境校验
# ══════════════════════════════════════════════════════════

@dataclass
class AgentConfig:
    """Agent DAG 全局配置"""
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "glm4:9b"
    moonshot_api_key: str = ""
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    moonshot_model: str = "kimi-k3"
    # 超时 & 重试
    llm_timeout_seconds: int = 120
    max_retries: int = 2
    retry_backoff_base: float = 1.5
    # 简单任务走 DeepSeek 的最大 token 估计
    simple_max_chars: int = 3000

    @classmethod
    def from_env(cls) -> "AgentConfig":
        if not ENV_PATH.exists():
            log.warning("dag.env 不存在: %s，使用默认值", ENV_PATH)
            return cls()

        load_dotenv(ENV_PATH, override=True)

        ollama_url = os.getenv("OLLAMA_URL", "").strip()
        if not ollama_url:
            ollama_url = "http://127.0.0.1:11434"

        api_key = os.getenv("MOONSHOT_API_KEY", "").strip()

        return cls(
            ollama_url=ollama_url,
            ollama_model=os.getenv("OLLAMA_MODEL", "glm4:9b").strip(),
            moonshot_api_key=api_key,
            moonshot_base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").strip(),
            moonshot_model=os.getenv("MOONSHOT_MODEL", "kimi-k3").strip(),
            llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT", "120")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        )


# ══════════════════════════════════════════════════════════
# LLM 工厂（带健康检查 & 重试）
# ══════════════════════════════════════════════════════════

def _retry_call(fn, max_retries: int, backoff: float, label: str):
    """带指数退避的重试调用"""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            wait = backoff ** attempt
            log.warning("[%s] 第 %d/%d 次失败，%0.1fs 后重试: %s",
                        label, attempt + 1, max_retries + 1, wait, str(e)[:200])
            if attempt < max_retries:
                time.sleep(wait)
    raise last_err  # type: ignore[misc]


def build_llms(cfg: AgentConfig):
    """构建双模型并执行快速健康检查"""
    log.info("初始化 LLM 客户端…")
    log.info("  DeepSeek (Ollama): %s @ %s", cfg.ollama_model, cfg.ollama_url)
    log.info("  Kimi (Moonshot):   %s @ %s", cfg.moonshot_model, cfg.moonshot_base_url)

    deepseek = ChatOllama(
        model=cfg.ollama_model,
        base_url=cfg.ollama_url,
        temperature=0.1,
        num_ctx=8192,
        timeout=cfg.llm_timeout_seconds,
    )

    kimi: Optional[ChatOpenAI] = None
    if cfg.moonshot_api_key:
        kimi = ChatOpenAI(
            api_key=cfg.moonshot_api_key,
            base_url=cfg.moonshot_base_url,
            model=cfg.moonshot_model,
            temperature=1,  # kimi-k3 只接受 temperature=1
            timeout=cfg.llm_timeout_seconds,
        )
    else:
        log.warning("MOONSHOT_API_KEY 未配置，复杂任务将降级为 DeepSeek 独立处理")

    return deepseek, kimi


def health_check(deepseek: ChatOllama, kimi: Optional[ChatOpenAI]) -> Dict[str, Any]:
    """验证两个 LLM 的连通性，返回诊断结果"""
    results: Dict[str, Any] = {"deepseek": {"ok": False, "latency_ms": 0, "error": ""},
                                "kimi": {"ok": False, "latency_ms": 0, "error": ""}}

    # ── DeepSeek (本地 Ollama) ──
    try:
        t0 = time.time()
        resp = _retry_call(
            lambda: deepseek.invoke("回复 OK"),
            max_retries=1, backoff=2.0, label="health/deepseek",
        )
        elapsed = (time.time() - t0) * 1000
        content = resp.content if hasattr(resp, "content") else str(resp)
        ok = bool(content and len(content) > 0)
        results["deepseek"] = {"ok": ok, "latency_ms": round(elapsed), "error": "" if ok else "空响应"}
        log.info("  DeepSeek 健康检查: %s (%dms, %d chars)", "PASS" if ok else "FAIL", round(elapsed), len(content))
    except Exception as e:
        results["deepseek"]["error"] = str(e)[:200]
        log.error("  DeepSeek 健康检查: FAIL (%s)", str(e)[:200])

    # ── Kimi (Moonshot API) ──
    if kimi is not None:
        try:
            t0 = time.time()
            resp = _retry_call(
                lambda: kimi.invoke("回复 OK"),
                max_retries=1, backoff=2.0, label="health/kimi",
            )
            elapsed = (time.time() - t0) * 1000
            ok = "OK" in (resp.content if hasattr(resp, "content") else str(resp))
            results["kimi"] = {"ok": ok, "latency_ms": round(elapsed), "error": "" if ok else "未返回OK"}
            log.info("  Kimi   健康检查: %s (%dms)", "PASS" if ok else "FAIL", round(elapsed))
        except Exception as e:
            results["kimi"]["error"] = str(e)[:200]
            log.error("  Kimi   健康检查: FAIL (%s)", str(e)[:200])
    else:
        results["kimi"]["error"] = "未配置 API Key"

    return results


# ══════════════════════════════════════════════════════════
# 状态定义
# ══════════════════════════════════════════════════════════

class AgentState(TypedDict, total=False):
    """LangGraph 全局状态，字段随节点执行逐步填充"""
    user_task: str               # 用户原始需求
    task_type: str               # "simple" | "complex" | "fix"
    skill_prompt: str            # 匹配到的技能指令（修复任务时注入）
    # 中间产物
    summary: str                 # Kimi 架构分析（仅 complex）
    code_result: str             # DeepSeek 生成代码
    final_out: str               # 最终输出
    # 元信息
    error: str                   # 捕获的错误
    route_log: str               # 路由决策日志


# ══════════════════════════════════════════════════════════
# 节点实现
# ══════════════════════════════════════════════════════════

# ── 分类器：简单/复杂 ──

# 强制走复杂路径 — 调试/诊断/分析类需求，含这些词直接判定 complex
_RESTART_KEYWORDS = ['重启', 'restart', '重启动', 'restart flask']
_VISION_KEYWORDS = ['截图', '图片', '.png', '.jpg', '.jpeg', 'screen', '看图']

_FORCE_COMPLEX_KEYWORDS = [
    "分析", "诊断", "为什么", "怎么不", "怎么回事", "什么原因",
    "不显示", "不工作", "打不开", "没数据", "找不到", "报错",
    "debug", "排查", "定位", "根因", "修好", "修复这个",
    "不运行", "连不上", "超时", "挂了", "坏了", "没反应",
]

# 复杂任务特征关键词（匹配任一即权重 -2）
_COMPLEX_KEYWORDS = [
    # 架构 / 设计
    "架构", "设计文档", "技术方案", "系统设计", "模块拆分", "重构方案",
    "微服务", "分布式", "高并发", "数据库设计", "API设计", "接口设计",
    # 多文件 / 多模块
    "多模块", "多文件", "项目结构", "工程", "前后端", "全栈",
    "脚手架", "框架搭建", "项目初始化", "目录结构",
    # 复杂分析
    "性能优化", "瓶颈分析", "安全审计", "代码审查", "review",
    "最佳实践", "设计模式", "架构模式",
    # 长文档 / 报告
    "报告", "方案书", "说明书", "文档", "PRD", "技术规范",
    "需求分析", "概要设计", "详细设计",
    # 多步骤
    "完整流程", "端到端", "pipeline", "workflow", "流水线",
]

# 简单任务特征（明确的小粒度需求）
_SIMPLE_KEYWORDS = [
    "函数", "脚本", "片段", "算法", "小工具",
    "单文件", "正则", "转换", "格式化", "排序", "遍历",
    "打印", "读取文件", "写入文件", "命令行", "CLI",
    "单元测试", "一个类", "装饰器", "上下文管理器",
]


def classify_task(state: AgentState) -> dict:
    """智能分类器：综合关键词密度、需求长度、复杂度信号"""
    task = state.get("user_task", "").strip()
    if not task:
        return {"task_type": "simple", "route_log": "空输入 → simple", "skill_prompt": ""}

    task_lower = task.lower()
    char_count = len(task)

    # 0. 重启命令：跳过 LLM 直接走 restart
    for kw in _RESTART_KEYWORDS:
        if kw.lower() in task_lower:
            log.info("分类: 重启命令 → restart")
            return {"task_type": "restart", "route_log": "restart", "skill_prompt": ""}

    # 1. 截图识别
    for kw in _VISION_KEYWORDS:
        if kw.lower() in task_lower:
            log.info('分类: 截图识别 → vision')
            return {'task_type': 'vision', 'route_log': 'vision', 'skill_prompt': ''}

    # 2. 技能匹配：检测修复类任务
    skill_prompt = _get_skill_prompt(task)
    if skill_prompt:
        log.info("分类: 命中修复技能 → fix | %.80s…", task)
        return {"task_type": "fix", "route_log": "skill:fix → fix_verify",
                "skill_prompt": skill_prompt}

    # 1. 强制复杂关键词 — 调试/诊断/分析直接判定 complex
    for kw in _FORCE_COMPLEX_KEYWORDS:
        if kw.lower() in task_lower:
            log.info("分类: 命中强制复杂词 '%s' → complex | %.80s…", kw, task)
            return {"task_type": "complex",
                    "route_log": f"force_complex:{kw} → complex", "skill_prompt": ""}

    # 计分：简单 +1, 复杂 -1
    score = 0

    # 1. 关键词匹配
    for kw in _COMPLEX_KEYWORDS:
        if kw.lower() in task_lower:
            score -= 2
    for kw in _SIMPLE_KEYWORDS:
        if kw.lower() in task_lower:
            score += 2

    # 2. 长度信号：超长需求更可能是复杂任务
    if char_count > 1500:
        score -= 1
    elif char_count < 200:
        score += 1

    # 3. 结构性信号：含代码块/列表/编号 → 可能是复杂需求
    structural_signals = 0
    if "```" in task:
        structural_signals += 1
    if task.count("\n") > 10:
        structural_signals += 1
    if any(marker in task for marker in ["1.", "2.", "3.", "- ", "* ", "# "]):
        structural_signals += 1
    if structural_signals >= 2:
        score -= 1

    task_type = "simple" if score >= 0 else "complex"
    log.info("分类: score=%d, type=%s, chars=%d | %.80s…", score, task_type, char_count, task)

    return {
        "task_type": task_type,
        "route_log": f"score={score} chars={char_count} → {task_type}",
        "skill_prompt": "",
    }


# ── 修复路径：注入技能指令 ──

def fix_verify(state, *, llm_code, cfg):
    task = state["user_task"]
    skill = state.get("skill_prompt", "")
    prompt = f"""你是项目资深开发。按以下铁律修复：

【强制流程】
{skill}

【任务】{task}

【要求】列出文件→修改→测试→验证 四步，只报告测试通过的结果。
"""
    try:
        resp = _retry_call(lambda: llm_code.invoke(prompt), max_retries=cfg.max_retries, backoff=cfg.retry_backoff_base, label="fix_verify")
        code = resp.content if hasattr(resp, "content") else str(resp)
        log.info("fix_verify 完成: %d 字符", len(code))
        return {"code_result": code, "final_out": code, "error": ""}
    except Exception as e:
        log.error("fix_verify 失败: %s", str(e)[:300])
        return {"code_result": "", "final_out": f"[错误] {e}", "error": str(e)[:500]}


# ── 测试验证节点 ──

def test_verify(state, *, llm_code, cfg):
    task = state.get("user_task", "")
    skill = state.get("skill_prompt", "")
    prompt = f"""写一段 Python 脚本来验证修复是否生效。脚本必须：
1. 导入 stock_dashboard.app 的 Flask test client
2. 请求相关 API 端点
3. 用 assert 验证关键字段存在
4. 如果 assert 失败，输出 FAIL: [原因]
5. 如果全部通过，输出 ALL TESTS PASSED

任务: {task}
只输出验证脚本，不加解释。
"""
    try:
        resp = _retry_call(lambda: llm_code.invoke(prompt), max_retries=2, backoff=1, label="test_verify")
        test_code = resp.content if hasattr(resp, "content") else str(resp)
        log.info("test_verify 生成测试: %d 字符", len(test_code))
        return {"summary": test_code, "error": ""}
    except Exception as e:
        return {"summary": f"# 测试生成失败: {e}", "error": str(e)[:300]}


def review(state, *, llm_code, cfg):
    code = state.get("code_result", "")
    test = state.get("summary", "")
    prompt = f"""审查以下修复，重点检查：
1. 是否改了不该改的代码
2. 是否有未使用的 import
3. 是否有潜在的性能问题
4. 测试是否覆盖了边界情况

修复内容: {code[:2000]}
测试脚本: {test[:1000]}

输出格式: PASS | WARN | FAIL + 具体问题列表
"""
    try:
        resp = _retry_call(lambda: llm_code.invoke(prompt), max_retries=2, backoff=1, label="review")
        result = resp.content if hasattr(resp, "content") else str(resp)
        log.info("review 完成: %d 字符", len(result))
        return {"final_out": result, "error": ""}
    except Exception as e:
        return {"final_out": f"审查跳过: {e}", "error": str(e)[:200]}


# ── 自动重启节点 ──

def auto_restart(state, *, llm_code, cfg):
    """检测是否改了 Python 文件，自动重启 Flask"""
    import subprocess
    final = state.get("final_out", "")
    needs_restart = any(ext in final for ext in ['.py', 'Python', '后端', 'Flask', 'stock_dashboard', 'engine'])
    
    if not needs_restart:
        return {"final_out": final + "\n[重启] 跳过 — HTML/前端修改无需重启"}
    
    log.info("检测到 Python 修改，自动重启 Flask...")
    try:
        # 杀旧进程
        result = subprocess.run(
            'for /f "tokens=5" %a in (\'netstat -ano ^| findstr ":5557.*LISTENING"\') do taskkill /F /PID %a 2>nul',
            shell=True, capture_output=True, text=True, timeout=10)
        # 清缓存 + 重启到 5557
        subprocess.run('del /q __pycache__\\*.pyc 2>nul', shell=True, cwd=str(BASE), timeout=5)
        subprocess.Popen(
            f'{BASE/".venv/Scripts/python.exe"} -B stock_dashboard.py',
            shell=True, cwd=str(BASE))
        msg = "\n[重启] ✅ Flask 已自动重启 → http://localhost:5557"
        log.info(msg)
        return {"final_out": final + msg, "error": ""}
    except Exception as e:
        msg = f"\n[重启] ❌ 自动重启失败: {e}\n请手动: .venv\\Scripts\\python -B stock_dashboard.py"
        log.error(msg)
        return {"final_out": final + msg, "error": str(e)[:200]}


# ── 简单路径：DeepSeek 独立完成 ──

def deepseek_solo(state: AgentState, *, llm_code: ChatOllama, cfg: AgentConfig) -> dict:
    """简单任务：本地 DeepSeek 一站式生成（不含 Kimi）"""
    task = state["user_task"]
    prompt = f"""你是资深 Python 工程师。根据需求输出完整可运行代码，只输出代码（含必要注释），不加解释。

需求：
{task}
"""
    try:
        resp = _retry_call(
            lambda: llm_code.invoke(prompt),
            max_retries=cfg.max_retries,
            backoff=cfg.retry_backoff_base,
            label="deepseek_solo",
        )
        code = resp.content if hasattr(resp, "content") else str(resp)
        log.info("deepseek_solo 完成，输出 %d 字符", len(code))
        return {"code_result": code, "final_out": code, "error": ""}
    except Exception as e:
        log.error("deepseek_solo 失败: %s", str(e)[:300])
        return {"code_result": "", "final_out": f"[错误] DeepSeek 生成失败: {e}", "error": str(e)[:500]}


# ── 复杂路径 ──

def kimi_analyze(state: AgentState, *, llm_kimi: ChatOpenAI, cfg: AgentConfig) -> dict:
    """复杂任务第一步：Kimi 梳理架构与模块拆分"""
    task = state["user_task"]
    prompt = f"""你是系统架构师。分析以下需求，输出：
1. 整体架构概述（2-3 句）
2. 模块划分（每模块一行，含职责说明）
3. 关键技术选型建议
4. 实现步骤（按顺序列出）

需求：
{task}

用中文输出，结构清晰。"""
    try:
        resp = _retry_call(
            lambda: llm_kimi.invoke(prompt),
            max_retries=cfg.max_retries,
            backoff=cfg.retry_backoff_base,
            label="kimi_analyze",
        )
        summary = resp.content if hasattr(resp, "content") else str(resp)
        log.info("kimi_analyze 完成，输出 %d 字符", len(summary))
        return {"summary": summary, "error": ""}
    except Exception as e:
        log.error("kimi_analyze 失败: %s", str(e)[:300])
        # 降级：无架构分析继续
        return {"summary": f"[降级] Kimi 架构分析失败: {e}\n直接根据需求生成代码。",
                "error": str(e)[:500]}


def deepseek_code(state: AgentState, *, llm_code: ChatOllama, cfg: AgentConfig) -> dict:
    """复杂任务第二步：DeepSeek 根据架构分析生成代码"""
    task = state["user_task"]
    arch = state.get("summary", "")
    prompt = f"""你是资深 Python 工程师。根据需求和架构分析，输出完整可运行代码。

需求：
{task}

架构分析：
{arch}

要求：
- 输出完整可运行的 Python 代码
- 包含必要的 import 和 __main__ 入口
- 关键位置加注释
- 如果架构分析中包含降级提示，优先按需求直接编码
"""
    try:
        resp = _retry_call(
            lambda: llm_code.invoke(prompt),
            max_retries=cfg.max_retries,
            backoff=cfg.retry_backoff_base,
            label="deepseek_code",
        )
        code = resp.content if hasattr(resp, "content") else str(resp)
        log.info("deepseek_code 完成，输出 %d 字符", len(code))
        return {"code_result": code, "error": ""}
    except Exception as e:
        log.error("deepseek_code 失败: %s", str(e)[:300])
        return {"code_result": f"# [错误] DeepSeek 生成失败: {e}",
                "error": str(e)[:500]}


def kimi_merge(state: AgentState, *, llm_kimi: ChatOpenAI, cfg: AgentConfig) -> dict:
    """复杂任务第三步：Kimi 整合架构分析与代码为最终交付物"""
    arch = state.get("summary", "")
    code = state.get("code_result", "")
    prompt = f"""你是技术顾问。整合架构分析和代码，输出一份完整技术方案交付文档，包含：
1. 架构概述
2. 核心模块说明
3. 完整代码（格式化为 markdown 代码块）
4. 使用说明 / 运行方式

架构分析：
{arch}

代码：
{code}
"""
    try:
        resp = _retry_call(
            lambda: llm_kimi.invoke(prompt),
            max_retries=cfg.max_retries,
            backoff=cfg.retry_backoff_base,
            label="kimi_merge",
        )
        merged = resp.content if hasattr(resp, "content") else str(resp)
        log.info("kimi_merge 完成，输出 %d 字符", len(merged))
        return {"final_out": merged, "error": ""}
    except Exception as e:
        log.error("kimi_merge 失败，降级输出纯代码: %s", str(e)[:200])
        # 降级：直接输出代码
        return {"final_out": code, "error": str(e)[:500]}


def handle_error(state: AgentState) -> dict:
    """全局错误处理节点"""
    err = state.get("error", "未知错误")
    log.error("进入错误处理节点: %s", err)
    return {
        "final_out": f"[系统错误] 任务执行失败: {err}\n请检查日志 _memory/agent_dag.log 获取详情。",
    }


# ══════════════════════════════════════════════════════════
# 路由
# ══════════════════════════════════════════════════════════

def route_by_type(state: AgentState) -> Literal["restart", "fix_verify", "deepseek_solo", "kimi_analyze"]:
    task_type = state.get("task_type", "")
    if task_type == "restart":
        return "restart"
    if task_type == "fix":
        return "fix_verify"
    return "kimi_analyze" if task_type == "complex" else "deepseek_solo"

def _old_route_helper(state: AgentState) -> Literal["deepseek_solo", "kimi_analyze"]:
    task_type = state.get("task_type", "simple")
    if task_type == "complex":
        log.info("路由 → complex 分支 (Kimi + DeepSeek)")
        return "kimi_analyze"
    log.info("路由 → simple 分支 (DeepSeek 独立)")
    return "deepseek_solo"


def route_after_analyze(state: AgentState) -> Literal["deepseek_code", "handle_error"]:
    if state.get("error"):
        log.warning("kimi_analyze 有错误，但仍进入 deepseek_code")
    return "deepseek_code"


def route_after_code(state: AgentState) -> Literal["kimi_merge", "handle_error"]:
    # 即使 code 出错也尝试 merge（会输出错误信息）
    return "kimi_merge"


# ══════════════════════════════════════════════════════════
# 图构建
# ══════════════════════════════════════════════════════════

def build_dag(cfg: AgentConfig, deepseek: ChatOllama, kimi: Optional[ChatOpenAI]):
    """构建并编译 LangGraph DAG"""

    builder = StateGraph(AgentState)

    # ── 添加节点 ──
    builder.add_node("classify_task", classify_task)
    builder.add_node("auto_restart_node", lambda s: auto_restart(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("fix_verify", lambda s: fix_verify(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("test_verify", lambda s: test_verify(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("review", lambda s: review(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("auto_restart", lambda s: auto_restart(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("deepseek_solo", lambda s: deepseek_solo(s, llm_code=deepseek, cfg=cfg))
    builder.add_node("handle_error", handle_error)

    if kimi is not None:
        builder.add_node("kimi_analyze", lambda s: kimi_analyze(s, llm_kimi=kimi, cfg=cfg))
        builder.add_node("deepseek_code", lambda s: deepseek_code(s, llm_code=deepseek, cfg=cfg))
        builder.add_node("kimi_merge", lambda s: kimi_merge(s, llm_kimi=kimi, cfg=cfg))

        # ── 路由：fix → fix_verify, complex → kimi, simple → deepseek ──
        builder.add_edge(START, "classify_task")
        builder.add_conditional_edges("classify_task", route_by_type, {
            "restart": "auto_restart_node",
            "fix_verify": "fix_verify",
            "deepseek_solo": "deepseek_solo",
            "kimi_analyze": "kimi_analyze",
        })
        builder.add_edge("auto_restart_node", END)  # 重启直达
        builder.add_edge("fix_verify", "test_verify")
        builder.add_edge("test_verify", "review")
        builder.add_edge("review", "auto_restart")
        builder.add_edge("auto_restart", END)  # 修复→审查→重启
        builder.add_edge("kimi_analyze", "deepseek_code")
        builder.add_edge("deepseek_code", "kimi_merge")
        builder.add_edge("kimi_merge", END)

        # 简单路径
        builder.add_edge("deepseek_solo", END)
    else:
        # ── 降级模式：无 Kimi ──
        log.warning("Kimi 不可用，DAG 降级为纯 DeepSeek 模式")
        builder.add_edge(START, "classify_task")
        builder.add_conditional_edges("classify_task", route_by_type, {
            "restart": "auto_restart_node",
            "fix_verify": "fix_verify",
            "deepseek_solo": "deepseek_solo",
            "kimi_analyze": "deepseek_solo",
        })
        builder.add_edge("auto_restart_node", END)  # 重启直达
        builder.add_edge("fix_verify", "test_verify")
        builder.add_edge("test_verify", "review")
        builder.add_edge("review", "auto_restart")
        builder.add_edge("auto_restart", END)
        builder.add_edge("deepseek_solo", END)

    dag = builder.compile(checkpointer=MemorySaver())
    log.info("DAG 编译完成")
    return dag


# ══════════════════════════════════════════════════════════
# ════════════════  测试 & 入口  ══════════════════════════
# ══════════════════════════════════════════════════════════

def run_health_suite(cfg: AgentConfig, deepseek: ChatOllama, kimi: Optional[ChatOpenAI]) -> bool:
    """完整健康检查套件，返回是否全部通过"""
    print("\n" + "=" * 60)
    print("  Agent DAG 健康检查")
    print("=" * 60)

    # 1. 环境检查
    print(f"\n[1/3] 环境配置")
    print(f"  dag.env 存在:   {'[OK]' if ENV_PATH.exists() else '[MISSING]'}")
    print(f"  OLLAMA_URL:      {cfg.ollama_url}")
    print(f"  MOONSHOT_KEY:    {'[OK] 已配置' if cfg.moonshot_api_key else '[MISSING] 未配置 (Kimi不可用)'}")
    print(f"  DeepSeek Model:  {cfg.ollama_model}")
    print(f"  Kimi Model:      {cfg.moonshot_model}")

    # 2. LLM 连通性
    print(f"\n[2/3] LLM 连通性")
    hc = health_check(deepseek, kimi)

    # 3. DAG 编译
    print(f"\n[3/3] DAG 编译")
    try:
        dag = build_dag(cfg, deepseek, kimi)
        print("  DAG 编译:         [OK] 成功")
        dag_ok = True
    except Exception as e:
        print(f"  DAG 编译:         [FAIL] 失败 ({e})")
        dag_ok = False

    # 汇总
    ds_ok = hc["deepseek"]["ok"]
    km_ok = hc["kimi"]["ok"] or kimi is None
    all_ok = ds_ok and km_ok and dag_ok

    print(f"\n{'─' * 60}")
    print(f"  综合判定: {'[PASS] 全部通过' if all_ok else '[FAIL] 存在失败'}")
    print(f"  DeepSeek: {'[OK]' if ds_ok else '[FAIL]'} | Kimi: {'[OK]' if km_ok else '[FAIL]' if kimi else '[N/A] 未配置'} | DAG: {'[OK]' if dag_ok else '[FAIL]'}")
    print(f"{'=' * 60}\n")

    return all_ok


def run_test_tasks(dag, cfg: AgentConfig):
    """执行一组测试任务，覆盖简单/复杂两条路径"""
    test_cases = [
        # (标签, 任务文本, 期望分类, 预期成功)
        ("简单-函数", "写一个递归遍历目录、跳过 .venv 和 __pycache__ 的 Python 函数", "simple", True),
        ("简单-脚本", "写一个 Python 脚本读取 CSV 文件并计算每列的平均值", "simple", True),
        ("复杂-架构", "设计一个微服务架构的电商订单系统，包含用户服务、订单服务、库存服务三个模块，"
                     "要求设计数据库表结构和 RESTful API 接口，请给出完整技术方案和代码框架", "complex", True),
    ]

    print("=" * 60)
    print("  测试任务执行")
    print("=" * 60)

    for idx, (label, task, expect_type, _) in enumerate(test_cases, 1):
        print(f"\n── [{idx}/{len(test_cases)}] {label} ──")
        print(f"  需求: {task[:100]}…")
        print(f"  预期分类: {expect_type}")

        state: AgentState = {"user_task": task}
        try:
            result = dag.invoke(state)
            actual_type = result.get("task_type", "?")
            final = result.get("final_out", "")
            error = result.get("error", "")
            route_log = result.get("route_log", "")

            match = "[MATCH]" if actual_type == expect_type else "[MISMATCH]"
            print(f"  分类结果: {match} {actual_type} ({route_log})")
            save_run_memory(state.get("user_task",""), final[:300])
            print(f"  最终输出: {len(final)} 字符")
            if error:
                print(f"  [WARN] 错误: {error[:200]}")

            # 打印输出预览
            preview = final[:300].replace("\n", "\\n")
            print(f"  输出预览: {preview}…" if len(final) > 300 else f"  输出: {final}")

        except Exception as e:
            print(f"  [FAIL] 执行异常: {e}")

    print(f"\n{'─' * 60}")
    print("  测试任务完成")




# ===== Memory (MemorySaver at graph level) =====
# 跨会话的持久记忆通过 _memory/agent_memory.json 实现
AGENT_MEMORY = BASE / "_memory" / "agent_memory.json"

def save_run_memory(task, result_summary):
    from datetime import datetime
    mem = {}
    if AGENT_MEMORY.exists():
        try: mem = json.load(open(AGENT_MEMORY, encoding="utf-8"))
        except: pass
    mem.setdefault("runs", []).append({
        "time": datetime.now().isoformat(),
        "task": task[:200],
        "result": result_summary[:300]
    })
    mem["runs"] = mem["runs"][-50:]  # keep last 50
    mem["total"] = len(mem["runs"])
    json.dump(mem, open(AGENT_MEMORY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def load_run_memory():
    if AGENT_MEMORY.exists():
        try: return json.load(open(AGENT_MEMORY, encoding="utf-8"))
        except: pass
    return {"runs": [], "total": 0}


def main():
    """CLI 入口：支持 --task / --check / --simple"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent DAG — 本地 DeepSeek + Kimi 双模型协作",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 简单任务（仅本地 DeepSeek，0 费用）
  .venv\\Scripts\\python agent_dag.py --task "写一个 CSV 转 JSON 函数"

  # 带文件上下文（把代码喂给 agent 分析）
  .venv\\Scripts\\python agent_dag.py --task "分析为什么预测总数不显示" --file stock_dashboard.py

  # 多文件上下文
  .venv\\Scripts\\python agent_dag.py --task "对比两个模块" -f stock_dashboard.py -f api_server.py

  # 复杂任务（Kimi 分析 + DeepSeek 编码 + Kimi 整合）
  .venv\\Scripts\\python agent_dag.py --task "设计一个用户认证系统"

  # 强制只用本地模型（不调 Kimi，0 网络请求）
  .venv\\Scripts\\python agent_dag.py --task "xxx" --simple

  # 健康检查
  .venv\\Scripts\\python agent_dag.py --check
        """,
    )
    parser.add_argument("--task", "-t", type=str, default=None,
                        help="任务描述，不传则运行默认测试套件")
    parser.add_argument("--file", "-f", type=str, action="append", default=None,
                        help="注入文件内容作为上下文（可多次指定），超出 6000 字符自动截断")
    parser.add_argument("--simple", "-s", action="store_true",
                        help="强制走简单路径（仅本地 DeepSeek，零费用）")
    parser.add_argument("--check", "-c", action="store_true",
                        help="仅运行健康检查，不执行任务")
    args = parser.parse_args()

    cfg = AgentConfig.from_env()
    deepseek, kimi = build_llms(cfg)

    # ── 纯健康检查 ──
    if args.check:
        run_health_suite(cfg, deepseek, kimi)
        return

    # ── 跑任务 ──
    if args.task:
        task_text = args.task

        # 注入文件上下文
        if args.file:
            context_parts = []
            for fpath in args.file:
                fp = Path(fpath)
                if not fp.exists():
                    print(f"[WARN] 文件不存在，跳过: {fpath}")
                    continue
                try:
                    content = fp.read_text(encoding="utf-8", errors="replace")
                    # 超长截断，保留头尾
                    max_len = 6000
                    if len(content) > max_len:
                        half = max_len // 2
                        content = content[:half] + f"\n\n… ({len(content) - max_len} 字符省略) …\n\n" + content[-half:]
                    context_parts.append(f"=== {fp.name} ({len(content)} 字符) ===\n{content}")
                    print(f"[OK] 加载上下文: {fpath} ({len(content)} 字符)")
                except Exception as e:
                    print(f"[WARN] 读取失败 {fpath}: {e}")

            if context_parts:
                task_text = "\n\n".join(context_parts) + "\n\n--- 以上为项目文件，请基于此分析以下问题 ---\n\n" + args.task

        dag = build_dag(cfg, deepseek, kimi)
        state: dict = {"user_task": task_text}

        if args.simple:
            # 强制 simple，绕过分类器
            print(f"\n[强制 Simple 模式] 仅用本地 DeepSeek，不调 Kimi\n")
            print(f"任务: {args.task[:200]}…\n")
            print(f"{'─' * 50}")
            result = dag.invoke({**state, "task_type": "simple"}, config={"configurable": {"thread_id": "main"}})
            output = result.get("final_out", "")
            print(output)
            print(f"\n{'─' * 50}")
            save_run_memory(state.get("user_task",""), output[:300])
            print(f"输出 {len(output)} 字符 | DeepSeek 独立完成 (0 费用)")
        else:
            # 自动分类
            print(f"\n任务: {args.task[:200]}…\n")
            print(f"{'─' * 50}")
            result = dag.invoke(state, config={"configurable": {"thread_id": "main"}})
            output = result.get("final_out", "")
            actual_type = result.get("task_type", "?")
            route_log = result.get("route_log", "")
            error = result.get("error", "")
            print(output)
            print(f"\n{'─' * 50}")
            save_run_memory(state.get("user_task",""), output[:300])
            print(f"分类: {actual_type} ({route_log}) | 输出 {len(output)} 字符")
            if error:
                print(f"警告: {error[:200]}")
        return

    # ── 无参数：默认测试套件 ──
    all_ok = run_health_suite(cfg, deepseek, kimi)
    if not all_ok:
        print("[WARN] 健康检查未全部通过，继续执行测试任务（部分可能失败）…")
    dag = build_dag(cfg, deepseek, kimi)
    run_test_tasks(dag, cfg)
    print("\n日志文件: _memory/agent_dag.log")


if __name__ == "__main__":
    main()
