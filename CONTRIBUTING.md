# 贡献指南

感谢您考虑为仪度六壬择日系统做出贡献！

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议：

1. 在 [Issues](https://github.com/your-username/yiduluren/issues) 页面搜索是否已有相关问题
2. 如果没有，创建新的 Issue，详细描述：
   - 问题的详细描述
   - 复现步骤
   - 期望的行为
   - 实际的行为
   - 截图（如有必要）

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/yiduluren.git
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **编写代码**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 编写测试用例

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

5. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 描述您的更改
   - 关联相关的 Issue

## 📝 代码规范

### Python 代码

- 使用 4 空格缩进
- 遵循 PEP 8 规范
- 函数和变量使用 snake_case
- 类使用 PascalCase

### 提交信息格式

```
<type>: <subject>

<body>
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 📚 开发指南

### 环境设置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python api_server.py
```

### 项目结构

```
yiduluren/
├── api_server.py          # API 服务器
├── core_modules/          # 核心计算模块
├── zongmen/               # 课经匹配
├── data/                  # 数据文件
├── docs/                  # 文档
└── tests/                 # 测试文件
```

## 📄 许可证

提交代码即表示您同意您的贡献将根据 MIT 许可证进行许可。

---

再次感谢您的贡献！🙏
