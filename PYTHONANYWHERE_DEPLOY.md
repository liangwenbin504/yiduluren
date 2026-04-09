# PythonAnywhere 部署指南

## 概述

本指南将帮助您将仪度六壬择日系统部署到 PythonAnywhere 平台。

## 前置条件

1. 一个 GitHub 账户
2. 项目已推送到 GitHub 仓库（liangwenbin504/yiduluren）
3. 一个 PythonAnywhere 账户（免费版即可）

---

## 第一步：创建 PythonAnywhere 账户

1. 访问 https://www.pythonanywhere.com
2. 点击 "Pricing" → "Create a Beginner account"（免费版）
3. 注册并登录

---

## 第二步：创建 Web 应用

1. 登录后，点击顶部的 "Web" 标签
2. 点击 "Add a new web app"
3. 点击 "Next"
4. 选择 "Flask"
5. 选择 "Python 3.10"（或最新版本）
6. 项目路径输入：`/home/您的用户名/yiduluren`
7. WSGI 文件路径保持默认
8. 点击 "Next"

---

## 第三步：从 GitHub 克隆项目

1. 点击顶部的 "Consoles" 标签
2. 点击 "Bash" 创建一个新的 Bash 控制台
3. 在 Bash 中执行以下命令：

```bash
# 克隆 GitHub 仓库
git clone https://github.com/liangwenbin504/yiduluren.git

# 进入项目目录
cd yiduluren

# 查看文件
ls -la
```

---

## 第四步：安装依赖

在 Bash 控制台中继续执行：

```bash
# 升级 pip
pip3 install --upgrade pip --user

# 安装项目依赖
pip3 install -r requirements.txt --user
```

---

## 第五步：配置 WSGI 文件

1. 点击顶部的 "Web" 标签
2. 在 "Code" 部分，找到 "WSGI configuration file"
3. 点击链接打开 WSGI 配置文件
4. 删除所有现有内容，粘贴以下内容：

```python
import os
import sys

# 添加项目路径
project_home = '/home/您的用户名/yiduluren'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
    sys.path.insert(0, os.path.join(project_home, 'core_modules'))
    sys.path.insert(0, os.path.join(project_home, 'core_modules', 'engine'))

# 设置环境变量
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TZ'] = 'Asia/Shanghai'

# 导入 Flask 应用
from api_server import app as application
```

**重要**：将 `您的用户名` 替换为您的 PythonAnywhere 用户名！

5. 点击 "Save" 保存

---

## 第六步：配置虚拟环境（可选但推荐）

1. 在 "Web" 页面的 "Virtualenv" 部分
2. 点击 "Start a console in this virtualenv"
3. 在控制台中安装依赖：

```bash
cd ~/yiduluren
pip install -r requirements.txt
```

---

## 第七步：配置静态文件

1. 在 "Web" 页面的 "Static files" 部分
2. 添加以下静态文件映射：

| URL | Directory |
|-----|-----------|
| /static/ | /home/您的用户名/yiduluren/static/ |

**注意**：如果项目没有 static 目录，可以跳过此步骤。

---

## 第八步：重新加载 Web 应用

1. 在 "Web" 页面顶部
2. 点击绿色的 "Reload" 按钮
3. 等待几秒钟

---

## 第九步：测试应用

1. 在 "Web" 页面顶部，您会看到您的应用 URL，格式为：
   `https://您的用户名.pythonanywhere.com`
2. 点击该 URL 访问您的应用
3. 测试各项功能是否正常

---

## 常见问题

### 问题 1：导入错误

**错误信息**：`ModuleNotFoundError: No module named 'xxx'`

**解决方案**：
- 确保所有依赖都已安装：`pip3 install -r requirements.txt --user`
- 检查 WSGI 文件中的路径是否正确

### 问题 2：500 内部服务器错误

**解决方案**：
1. 点击 "Web" 页面的 "Log files" 部分
2. 查看 "Error log" 获取详细错误信息
3. 根据错误信息修复问题

### 问题 3：静态文件 404

**解决方案**：
- 检查静态文件路径配置是否正确
- 确保 static 目录存在

---

## 更新应用

当您在 GitHub 上更新代码后：

1. 在 PythonAnywhere 的 Bash 控制台中：

```bash
cd ~/yiduluren
git pull
```

2. 在 "Web" 页面点击 "Reload" 按钮

---

## 免费版限制

- 每天 100 秒 CPU 时间
- 每月 500 MB 带宽
- 每天需要手动续约（点击 "Run until 3 months from today"）

---

## 获得帮助

- PythonAnywhere 官方文档：https://help.pythonanywhere.com/
- Flask 部署指南：https://help.pythonanywhere.com/pages/Flask/

---

祝您部署顺利！
