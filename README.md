# 仪度六壬择日系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**专业级大六壬择日排盘系统**

基于《仪度六壬选日要诀》的传统择日智慧，结合现代技术实现

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [技术架构](#技术架构)

</div>

---

## 📖 项目简介

仪度六壬择日系统是一款专业的传统择日软件，完整实现了大六壬排盘、斗首择日、演禽择日等传统术数体系。系统遵循《仪度六壬选日要诀》等经典著作，为风水择日提供科学、规范的计算工具。

### 🎯 核心功能

| 功能模块 | 说明 |
|---------|------|
| **大六壬排盘** | 完整实现九宗门起课（贼克、比用、涉害、遥克、昴星、别责、八专、伏吟、返吟） |
| **四课三传** | 自动计算四课、三传，支持64课经匹配 |
| **斗首择日** | 六相六替分析、课格评分、吉凶断语 |
| **演禽择日** | 四禽演禽计算、禽星吉凶分析 |
| **禄马贵人** | 年月日时四柱禄马贵人到山到向计算 |
| **综合评分** | 多维度综合评分，智能推荐吉日 |
| **文档导出** | 支持DOCX格式导出，专业排版 |

---

## ✨ 功能特性

### 🔮 大六壬排盘

```
┌─────────────────────────────────────┐
│           天 地 盘                   │
│   巳    午    未    申               │
│   辰              酉               │
│   卯              戌               │
│   寅    丑    子    亥               │
└─────────────────────────────────────┘
```

- **九宗门起课**：完整实现贼克、比用、涉害、遥克、昴星、别责、八专、伏吟、返吟九种起课方法
- **64课经匹配**：自动匹配课体，提供课经断语
- **天地盘排盘**：精准计算月将加临，生成天地盘
- **四课三传**：自动生成四课，推算三传

### 📊 综合评分系统

| 评分维度 | 权重 | 说明 |
|---------|------|------|
| 斗首评分 | 30% | 六相六替分析、课格评分 |
| 六壬评分 | 40% | 课体吉凶、禄马贵人 |
| 演禽评分 | 30% | 四禽吉凶、禽星分析 |

### 📄 文档导出

- 专业排版格式
- 横向A4页面
- 支持印章图片
- 自动生成择日课单

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Windows / Linux / macOS

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/yiduluren.git
cd yiduluren
```

2. **创建虚拟环境**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动服务**
```bash
python api_server.py
```

5. **访问系统**

打开浏览器访问：`http://localhost:5000`

### Docker 部署

```bash
# 构建镜像
docker build -t yiduluren .

# 运行容器
docker run -d -p 5000:5000 yiduluren
```

---

## 📚 使用指南

### 基本操作流程

1. **选择择日类型**：立碑、安葬、婚嫁等
2. **输入坐山信息**：选择坐山和向首
3. **设置日期范围**：选择筛选的时间范围
4. **执行筛选**：系统自动计算并推荐吉日
5. **查看结果**：查看综合评分和详细分析
6. **导出文档**：生成专业择日课单

### 参数说明

| 参数 | 说明 |
|------|------|
| 坐山 | 坐山方位，如壬山、子山等 |
| 向首 | 向首方位，如丙向、午向等 |
| 日期范围 | 筛选吉日的时间范围 |
| 最低评分 | 设定综合评分的最低阈值 |

---

## 🏗️ 技术架构

```
yiduluren/
├── api_server.py          # Flask API 服务器
├── 主界面.html            # 前端界面
├── export_docx_docx.py    # 文档导出模块
├── core_modules/          # 核心计算模块
│   ├── engine/            # 计算引擎
│   │   ├── sizhu_engine.py        # 四柱计算
│   │   ├── sike_sanchuan_engine.py # 四课三传
│   │   ├── daliuren_engine.py     # 大六壬引擎
│   │   └── kejing_scoring.py      # 课经评分
│   └── data/              # 数据文件
├── zongmen/               # 课经匹配模块
├── data/                  # 数据存储
├── docs/                  # 文档
└── templates/             # 文档模板
```

### 核心模块

- **sizhu_engine** - 四柱干支计算
- **sike_sanchuan_engine** - 四课三传计算
- **daliuren_engine** - 大六壬排盘引擎
- **douhou_analyzer** - 斗首择日分析
- **yanqin_analyzer** - 演禽择日分析
- **daliuren_luma_guiren** - 禄马贵人计算

---

## 📖 参考资料

本项目基于以下传统典籍实现：

- 《仪度六壬选日要诀》
- 《穿山透地真传》
- 《大六壬课经》
- 《斗首择日秘本》

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

## 📞 联系方式

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/your-username/yiduluren/issues)
- 发送邮件至项目维护者

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个 Star ⭐**

Made with ❤️ by 仪度六壬团队

</div>
