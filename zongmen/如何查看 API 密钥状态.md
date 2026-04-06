# 如何查看 API 密钥和额度状态

## 📋 检查步骤

### 步骤 1：查看 API 密钥状态

1. **访问 DashScope 控制台**
   - URL: https://dashscope.console.aliyun.com/
   - 或者从阿里云控制台搜索"DashScope"或"模型服务"

2. **查看 API 密钥**
   - 点击左侧菜单的"API-KEY 管理"
   - 找到您的 API 密钥：`***REMOVED***`
   - 检查状态：
     - ✅ **正常** - 显示"已启用"或"Active"
     - ⚠️ **过期** - 显示"已过期"或"Expired"
     - ❌ **禁用** - 显示"已禁用"或"Disabled"

3. **如果密钥过期/禁用**
   - 点击"创建新的 API-KEY"
   - 复制新的密钥
   - 更新到脚本中

---

### 步骤 2：查看剩余额度

1. **在 DashScope 控制台**
   - 点击"用量查询"或"资源包管理"
   - 查看：
     - **剩余 token 数** 或 **剩余调用次数**
     - **本月已用额度**
     - **额度到期时间**

2. **额度类型**
   - **免费额度**: 通常有一定数量的免费 token
   - **付费额度**: 充值后的金额
   - **资源包**: 购买的 token 包

3. **如果额度不足**
   - 点击"充值"或"购买资源包"
   - 选择适合的套餐
   - 完成支付

---

### 步骤 3：查看服务开通状态

1. **检查服务是否开通**
   - 在 DashScope 控制台
   - 查看"服务管理"或"我的服务"
   - 确认"Qwen-Max"服务已开通

2. **如果服务未开通**
   - 点击"开通服务"
   - 同意服务协议
   - 完成开通

---

### 步骤 4：测试 API 密钥

创建测试脚本 `test_api_key.py`:

```python
import dashscope
from dashscope import Generation

# 您的 API 密钥
dashscope.api_key = '***REMOVED***'

print("正在测试 API 连接...")

try:
    # 简单测试
    response = Generation.call(
        model='qwen-max',
        messages=[{'role': 'user', 'content': '你好，请回复"测试成功"'}],
        timeout=30
    )
    
    if response.status_code == 200:
        print("✅ API 测试成功！")
        print(f"返回内容：{response.output.get('text', '')}")
    else:
        print(f"❌ API 错误：{response.status_code}")
        print(f"错误信息：{response.message}")
        
except Exception as e:
    print(f"❌ 异常：{str(e)}")
    print("\n可能的原因：")
    print("1. 网络连接问题")
    print("2. API 密钥无效")
    print("3. 服务未开通")
    print("4. 额度不足")
```

运行测试：
```bash
python test_api_key.py
```

---

## 🔍 常见错误代码

| 错误代码 | 含义 | 解决方法 |
|---------|------|---------|
| 400 | 请求错误 | 检查请求格式 |
| 401 | 认证失败 | API 密钥无效或过期 |
| 402 | 余额不足 | 需要充值 |
| 403 | 权限不足 | 服务未开通或权限受限 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 500 | 服务器错误 | 稍后重试 |

---

## 💡 快速诊断命令

### 1. 检查网络连接
```bash
ping dashscope.aliyuncs.com
```

### 2. 测试 API 连接
```bash
python test_api_key.py
```

### 3. 查看当前 API 密钥
```bash
# 在脚本中查看
echo ***REMOVED***
```

---

## 📞 需要帮助

如果以上步骤都无法解决问题，请提供：

1. **API 密钥状态截图**
   - DashScope 控制台的 API-KEY 管理页面

2. **额度状态截图**
   - 用量查询或资源包管理页面

3. **错误信息**
   - 运行测试脚本的完整输出
   - 包括错误代码和错误信息

这样我可以更准确地帮您诊断问题！

---

**最后更新**: 2026-03-21
