# OpenClaw 与 Trae Solo 集成指南

## 🎯 目标

将 OpenClaw 集成到 Trae Solo 的自定义模型选择器中，实现本地安全对话。

---

## 📋 前置条件

- ✅ Node.js 22.16+ 或 24+ (已安装 v25.2.1)
- ✅ OpenClaw (已全局安装)
- ✅ Trae Solo IDE

---

## 🚀 快速开始

### 步骤 1: 启动 OpenClaw Gateway

双击运行 `start_openclaw.bat`，或在命令行中执行：

```bash
cd d:\新建文件夹\仪度六壬择日\yiduluren
start_openclaw.bat
```

### 步骤 2: 在 Trae Solo 中配置 OpenClaw

1. 打开 Trae Solo
2. 点击模型选择器（通常在右上角或设置中）
3. 选择 "添加自定义模型" 或 "OpenAI 兼容 API"
4. 填写以下配置：

| 配置项 | 值 |
|--------|-----|
| **API 基础 URL** | `http://127.0.0.1:18789/v1` |
| **API 密钥** | `openclaw-local-token-123456` |
| **模型名称** | `openclaw/default` |

### 步骤 3: 测试连接

在 Trae Solo 中选择新配置的 OpenClaw 模型，发送测试消息：
`你好，请介绍一下自己`

---

## 🔧 配置详解

### OpenClaw 配置文件

位置：`openclaw_config.json`

```json5
{
  gateway: {
    bind: "loopback",           // 仅本地访问
    port: 18789,                // 端口号
    auth: {
      mode: "password",         // 认证模式
      password: "openclaw-local-token-123456"
    },
    http: {
      endpoints: {
        chatCompletions: { enabled: true }  // 启用 OpenAI 兼容 API
      }
    }
  },
  // ... 更多配置
}
```

### 可用的 API 端点

OpenClaw 提供以下 OpenAI 兼容端点：

- `POST /v1/chat/completions` - 聊天完成
- `GET /v1/models` - 模型列表
- `GET /v1/models/{id}` - 模型详情
- `POST /v1/embeddings` - 嵌入生成
- `POST /v1/responses` - 响应生成

### 模型 ID 格式

在 Trae Solo 中可以使用以下模型 ID：

- `openclaw` - 默认代理
- `openclaw/default` - 默认代理（推荐）
- `openclaw/<agentId>` - 特定代理

---

## 🛠️ 高级配置

### 配置真实的 LLM 提供商

当前配置使用 `synthetic/test` 测试模型。要使用真实模型，请选择以下方式之一：

#### 选项 A: 使用 Ollama（本地模型）

1. 安装 Ollama: https://ollama.com/download
2. 拉取模型：
   ```bash
   ollama pull glm-4.7-flash
   ```
3. 修改 `openclaw_config.json`：
   ```json5
   {
     agents: {
       defaults: {
         model: { primary: "ollama/glm-4.7-flash" }
       }
     },
     models: {
       mode: "merge",
       providers: {
         ollama: {
           baseUrl: "http://127.0.0.1:11434",
           apiKey: "ollama-local",
           api: "ollama"
         }
       }
     }
   }
   ```

#### 选项 B: 使用免费云模型

OpenClaw 支持众多免费/付费模型提供商：
- DeepSeek
- Groq
- Qwen
- GLM
- 等等...

修改配置文件添加相应的 API 密钥即可。

---

## 🔍 验证和调试

### 测试 API 是否工作

使用 curl 测试：

```bash
curl -sS http://127.0.0.1:18789/v1/models ^
  -H "Authorization: Bearer openclaw-local-token-123456"
```

测试聊天：

```bash
curl -sS http://127.0.0.1:18789/v1/chat/completions ^
  -H "Authorization: Bearer openclaw-local-token-123456" ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"openclaw/default\", \"messages\": [{\"role\":\"user\",\"content\":\"hi\"}]}"
```

### 检查 OpenClaw 状态

```bash
openclaw status
openclaw doctor
```

---

## 📝 故障排除

### 问题 1: 无法连接到 OpenClaw

**解决方案：**
- 确认 `start_openclaw.bat` 正在运行
- 检查防火墙是否阻止 18789 端口
- 访问 http://127.0.0.1:18789 查看是否有响应

### 问题 2: 认证失败

**解决方案：**
- 确认 API 密钥正确：`openclaw-local-token-123456`
- 检查配置文件中的 `gateway.auth.password`

### 问题 3: 模型没有响应

**解决方案：**
- 检查是否配置了真实的 LLM 提供商
- 查看 OpenClaw 控制台的日志输出
- 运行 `openclaw doctor` 诊断问题

---

## 🔐 安全说明

1. **本地访问：** OpenClaw 默认仅绑定到 `loopback` (127.0.0.1)，外部无法访问
2. **密码保护：** API 需要密码认证
3. **数据安全：** 所有对话在本地处理（取决于配置的模型）

---

## 📚 更多资源

- OpenClaw 官方文档: https://docs.openclaw.ai
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- Ollama: https://ollama.com

---

## ✅ 完成检查清单

- [ ] OpenClaw Gateway 已启动并运行在 http://127.0.0.1:18789
- [ ] Trae Solo 中已配置自定义 OpenAI 兼容 API
- [ ] 测试消息发送成功
- [ ] （可选）配置了真实的 LLM 提供商

---

**祝使用愉快！🦞**
