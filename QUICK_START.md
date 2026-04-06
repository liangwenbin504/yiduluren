# 🚀 OpenClaw 快速启动指南

## 已完成 ✅

- ✅ Node.js v25.2.1 已安装
- ✅ OpenClaw 已全局安装
- ✅ 配置文件已创建：`openclaw_config.json`

---

## 第一步：启动 OpenClaw Gateway

在 PowerShell 中依次执行以下命令：

```powershell
# 1. 进入项目目录
cd d:\新建文件夹\仪度六壬择日\yiduluren

# 2. 设置环境变量
$env:OPENCLAW_GATEWAY_PASSWORD = "openclaw-local-token-123456"

# 3. 启动 OpenClaw Gateway
openclaw gateway --config openclaw_config.json --verbose
```

启动成功后，您会看到：
- Gateway 运行在：`http://127.0.0.1:18789`
- OpenAI 兼容 API 已启用

---

## 第二步：在 Trae Solo 中配置

打开 Trae Solo，找到模型选择器，添加自定义 OpenAI 兼容模型：

| 配置项 | 值 |
|--------|-----|
| **API 基础 URL** | `http://127.0.0.1:18789/v1` |
| **API 密钥** | `openclaw-local-token-123456` |
| **模型名称** | `openclaw/default` |

---

## 第三步：测试对话

在 Trae Solo 中选择刚配置的 OpenClaw 模型，发送消息测试！

---

## 📝 重要提示

1. **保持 OpenClaw Gateway 运行** - 不要关闭运行 Gateway 的终端窗口
2. **本地安全** - 所有数据仅在本地处理，不会上传到远程服务器
3. **如需停止** - 在运行 Gateway 的终端按 `Ctrl+C`

---

## 🔧 配置真实模型（可选）

当前使用测试模型。要使用真实 AI：

### 选项 A：Ollama（免费本地模型）
1. 下载安装：https://ollama.com/download
2. 拉取模型：`ollama pull glm-4.7-flash`
3. 修改 `openclaw_config.json` 配置

### 选项 B：免费云模型
OpenClaw 支持 DeepSeek、Groq、Qwen、GLM 等

---

## 📚 更多帮助

详细文档请查看：`TRAE_SOLO_OPENCLAW_INTEGRATION_GUIDE.md`

---

**祝使用愉快！🦞**
