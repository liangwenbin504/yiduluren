***

name: "glm-5-turbo"
description: "GLM-5-Turbo 智能体，用于处理自然语言理解和生成任务。Invoke when natural language processing or generation is needed."
---------------------------------------------------------------------------------------------------------------

# GLM-5-Turbo 智能体

## 核心功能

- **自然语言理解**：处理用户的自然语言输入
- **自然语言生成**：生成符合语境的自然语言回复
- **多轮对话**：支持上下文理解的多轮对话
- **知识问答**：基于知识的问答能力
- **代码生成**：生成代码和技术文档

## 调用时机

**当需要处理自然语言任务时调用此 SKILL**，包括：

- 回答用户的问题
- 生成文本内容
- 代码辅助
- 知识查询
- 对话交互

## 实现逻辑

### 核心配置

```python
import requests
import json

class GLM5TurboAgent:
    def __init__(self, api_key):
        self.api_key = ***REMOVED***
        self.base_url = "https://open.bigmodel.cn/api/mllm/v1/chat/completions"
    
    def generate(self, messages, temperature=0.7, max_tokens=2048):
        """调用 GLM-5-Turbo API 生成回复"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "glm-5-turbo",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
```

### 对话处理流程

```python
def process_dialogue(user_input, context=None):
    """处理对话请求"""
    if context is None:
        context = []
    
    # 构建消息列表
    messages = context + [{
        "role": "user",
        "content": user_input
    }]
    
    # 调用 GLM-5-Turbo
    agent = GLM5TurboAgent(api_key="YOUR_API_KEY")
    response = agent.generate(messages)
    
    # 更新上下文
    context.append({"role": "user", "content": user_input})
    context.append({"role": "assistant", "content": response})
    
    return response, context
```

## 输出格式

```python
{
    "response": "生成的回复内容",
    "context": [
        {"role": "user", "content": "用户输入1"},
        {"role": "assistant", "content": "助手回复1"},
        {"role": "user", "content": "用户输入2"},
        {"role": "assistant", "content": "助手回复2"}
    ],
    "model": "glm-5-turbo",
    "timestamp": "2026-03-23T12:00:00Z"
}
```

## 自我校验

### 校验规则

```python
def validate_response(response):
    """校验 GLM-5-Turbo 响应"""
    
    # 1. 检查响应是否为空
    if not response:
        return False, "响应为空"
    
    # 2. 检查响应是否包含错误信息
    if "Error:" in response:
        return False, "API 调用失败"
    
    # 3. 检查响应长度
    if len(response) < 5:
        return False, "响应过短"
    
    return True, "校验通过"
```

## 使用示例

### 示例 1：基本问答

```python
user_input = "什么是大六壬？"
response, context = process_dialogue(user_input)
# 响应：
# "大六壬是中国传统数术之一，属于古代的预测学体系。它以天干地支为基础，通过特定的起课方法..."
```

### 示例 2：代码生成

```python
user_input = "写一个 Python 函数来计算斐波那契数列"
response, context = process_dialogue(user_input)
# 响应：
# "def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    elif n == 2:\n        return [0, 1]\n    else:\n        fib = [0, 1]\n        for i in range(2, n):\n            fib.append(fib[i-1] + fib[i-2])\n        return fib"
```

### 示例 3：多轮对话

```python
# 第一轮
user_input1 = "如何学习大六壬？"
response1, context = process_dialogue(user_input1)

# 第二轮
user_input2 = "有什么推荐的书籍吗？"
response2, context = process_dialogue(user_input2, context)
# 响应会考虑上下文，推荐大六壬相关书籍
```

## 版本信息

- **版本**：v1.0
- **更新日期**：2026-03-23
- **依赖**：requests 库
- **API 参考**：智谱 AI OpenAPI 文档
- **注意事项**：
  - 需要在 `GLM5TurboAgent` 类中设置有效的 API Key
  - 请遵守智谱 AI 的 API 使用规范
  - 建议设置合理的 `max_tokens` 和 `temperature` 参数

## 配置说明

要使用此智能体，需要：

1. **获取 API Key**：访问智谱 AI 官网 (<https://open.bigmodel.cn/>) 注册并获取 API Key
2. **安装依赖**：`pip install requests`
3. **配置 API Key**：在代码中替换 `YOUR_API_KEY` 为实际的 API Key
4. **调整参数**：根据实际需求调整 `temperature` 和 `max_tokens` 参数

## 功能扩展

此智能体可以进一步扩展：

- **领域适配**：针对特定领域（如六壬、风水等）进行微调
- **多模态能力**：支持图像理解和生成
- **工具集成**：与其他工具和服务集成
- **自定义指令**：添加特定的系统指令以优化性能

