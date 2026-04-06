# 仪度六壬择日项目结构说明

## 项目概述

本项目是一个综合性的六壬择日系统，集成了大六壬排盘、斗首择日、演禽真法等多种传统择日方法，提供智能化的日课分析和筛选功能。

## 目录结构

```
yiduluren/
├── core_modules/           # 核心 Python 模块
│   ├── engine/            # 分析引擎模块
│   │   ├── daliuren_engine.py        # 大六壬排盘引擎
│   │   ├── daliuren_engine_pro.py    # 大六壬增强引擎
│   │   ├── daliuren_display.py       # 大六壬显示模块
│   │   ├── daliuren_kege_analyzer.py # 大六壬课体分析 (64 课集成版)
│   │   ├── daliuren_64ke_rules.py    # 64 课课经规则库
│   │   ├── sike_sanchuan_engine.py   # 四课三传起课引擎
│   │   ├── douhou_engine.py          # 斗首择日引擎
│   │   ├── douhou_analyzer.py        # 斗首课格分析
│   │   ├── yanqin_analyzer.py        # 演禽真法分析
│   │   ├── comprehensive_scorer.py   # 综合评分模块
│   │   ├── riku_analysis_system.py   # 日课分析系统 (主模块)
│   │   ├── date_range_generator.py   # 日期范围生成
│   │   ├── sizhu_engine.py           # 四柱计算引擎
│   │   ├── gui_ren_engine.py         # 贵人引擎
│   │   ├── lunar_converter.py        # 农历转换
│   │   ├── smart_selector.py         # 智能选择器
│   │   ├── smart_selector_pro.py     # 智能选择器专业版
│   │   └── comprehensive_selector.py # 综合择日选择器
│   ├── data/              # 数据常量模块
│   │   ├── constants.py              # 基础常量 (天干地支五行等)
│   │   └── 斗首择日规则.py            # 斗首择日规则配置
│   └── utils/             # 工具函数模块
│
├── docs/                  # 文档资料
│   ├── guides/           # 使用指南
│   │   ├── 系统使用指南.md
│   │   ├── 快速入门指南.md
│   │   ├── 综合择日系统使用手册.md
│   │   └── ... (其他使用指南)
│   ├── reports/          # 开发报告
│   │   ├── 大六壬 64 课课经集成 - 最终总结.md
│   │   ├── 大六壬 64 课课经集成报告.md
│   │   ├── 大六壬课体分析功能完成报告.md
│   │   ├── 日课分析系统完成报告.md
│   │   ├── 斗首择日功能修复报告.md
│   │   └── ... (其他开发报告)
│   └── references/       # 参考资料
│       ├── README_日课分析系统.md
│       ├── 项目文件清单.md
│       └── ... (其他参考资料)
│
├── data/                  # 数据文件
│   ├── raw/              # 原始数据
│   │   ├── 斗首择日秘本.txt
│   │   ├── 斗首择日第一斗首课格断语.txt
│   │   ├── 斗首择日完整课格断语全集.txt
│   │   ├── 1《仪度六壬选日要诀》注解 1.txt
│   │   ├── 2《仪度六壬选日要诀》注解 2.txt
│   │   └── ... (其他原始数据)
│   ├── processed/        # 处理后的数据
│   └── temp/             # 临时数据
│
├── web/                   # Web 界面文件
│   └── 主界面.html        # 主界面 HTML
│
├── skills/                # SKILL 模块 (.trae/skills/)
│   ├── daliuren-verification/    # 大六壬验证 SKILL
│   ├── daliuren-qike-decision/   # 大六壬起课决策 SKILL
│   ├── jingque-lifa/             # 精确历法 SKILL
│   ├── fu-yin-method/            # 伏吟法 SKILL
│   ├── fan-yin-method/           # 反吟法 SKILL
│   ├── zei-ke-method/            # 贼克法 SKILL
│   ├── bi-yong-method/           # 比用法 SKILL
│   ├── she-hai-method/           # 涉害法 SKILL
│   ├── yao-ke-method/            # 遥克法 SKILL
│   ├── ao-xing-method/           # 昴星法 SKILL
│   ├── bie-ze-method/            # 别责法 SKILL
│   ├── ba-zhuan-method/          # 八专法 SKILL
│   ├── core_rules.md             # 核心规则
│   └── ... (其他 SKILL 模块)
│
├── zongmen/               # 宗门资料
│   ├── pdf_extract/       # PDF 提取资料
│   │   ├── 64_ke_full/   # 64 课完整资料
│   │   ├── sanguang/     # 三光课资料
│   │   └── ... (其他提取资料)
│   ├── bifa_rules_engine.py  # 毕法赋规则引擎
│   └── ... (宗门相关资料)
│
├── .trae/                 # Trae IDE 配置
│   └── skills/           # SKILL 配置
│
├── README.md              # 项目 README
└── 主界面.html            # 主界面 (根目录)
```

## 核心模块说明

### 1. 大六壬模块 (`core_modules/engine/`)

- **daliuren_engine.py**: 基础大六壬排盘引擎
- **daliuren_engine_pro.py**: 增强版大六壬引擎 (支持更多功能)
- **daliuren_kege_analyzer.py**: 大六壬课体分析 (已集成 64 课课经)
- **daliuren_64ke_rules.py**: 64 课课经规则库 (31 课完整定义)
- **sike_sanchuan_engine.py**: 四课三传起课引擎 (支持九宗门)

### 2. 斗首择日模块 (`core_modules/engine/`)

- **douhou_engine.py**: 斗首择日基础引擎
- **douhou_analyzer.py**: 斗首课格分析模块 (支持评分)

### 3. 演禽真法模块 (`core_modules/engine/`)

- **yanqin_analyzer.py**: 演禽真法分析模块

### 4. 综合评分模块 (`core_modules/engine/`)

- **comprehensive_scorer.py**: 综合评分计算器
- **riku_analysis_system.py**: 日课分析系统 (整合所有模块)

### 5. 辅助模块 (`core_modules/engine/`)

- **date_range_generator.py**: 日期范围生成 (支持到 2100 年)
- **sizhu_engine.py**: 四柱计算引擎
- **lunar_converter.py**: 农历转换
- **gui_ren_engine.py**: 贵人计算引擎

## 数据文件说明

### 原始数据 (`data/raw/`)

- **斗首择日秘本.txt**: 斗首择日古籍原文
- **斗首择日课格断语.txt**: 斗首课格断语集合
- **仪度六壬选日要诀注解.txt**: 仪度六壬选日要诀注解

### 处理后的数据 (`data/processed/`)

待处理数据存放处

### 临时数据 (`data/temp/`)

临时数据存放处

## 文档分类

### 使用指南 (`docs/guides/`)

- 系统使用指南
- 快速入门指南
- 各模块使用说明

### 开发报告 (`docs/reports/`)

- 大六壬 64 课课经集成报告
- 日课分析系统完成报告
- 各功能模块开发报告

### 参考资料 (`docs/references/`)

- 项目 README
- 项目文件清单
- 系统架构说明

## SKILL 模块说明

项目使用了多个 SKILL 模块来支持大六壬起课规则:

### 九宗门 SKILL

1. **zei-ke-method**: 贼克法
2. **bi-yong-method**: 比用法
3. **she-hai-method**: 涉害法
4. **yao-ke-method**: 遥克法
5. **ao-xing-method**: 昴星法
6. **bie-ze-method**: 别责法
7. **ba-zhuan-method**: 八专法
8. **fu-yin-method**: 伏吟法
9. **fan-yin-method**: 反吟法

### 辅助 SKILL

- **daliuren-verification**: 大六壬验证工具
- **daliuren-qike-decision**: 大六壬起课决策
- **jingque-lifa**: 精确历法计算

## 快速开始

### 1. 查看使用指南

```bash
# 查看系统使用指南
cat docs/guides/系统使用指南.md
```

### 2. 运行日课分析

```python
# 在 core_modules 目录下
python riku_analysis_system.py
```

### 3. 运行测试

```python
# 运行综合测试
python test_riku_system.py

# 运行大六壬 64 课课经测试
python test_64ke_integration.py
```

## 版本信息

- **当前版本**: v2.0 (64 课课经集成版)
- **最后更新**: 2026-03-24
- **核心功能**: 大六壬排盘、斗首择日、演禽真法、综合评分

## 文件整理说明

本次文件整理工作于 2026-03-24 完成，主要工作包括:

1. **创建核心模块目录** (`core_modules/`)
   - 将所有 Python 源代码文件集中管理
   - 按功能分为 engine、data、utils 三个子目录

2. **创建文档目录** (`docs/`)
   - guides: 使用指南类文档
   - reports: 开发报告类文档
   - references: 参考资料类文档

3. **创建数据目录** (`data/`)
   - raw: 原始数据文件
   - processed: 处理后的数据
   - temp: 临时数据

4. **保持原有结构**
   - `web/`: Web 界面文件
   - `skills/`: SKILL 模块
   - `zongmen/`: 宗门资料

## 注意事项

1. **导入路径**: 由于文件已移动，部分 Python 文件的导入路径可能需要更新
2. **测试验证**: 文件整理后需要进行完整的功能测试
3. **备份**: 建议定期备份项目文件

## 联系方式

如有问题，请查阅:
- `docs/guides/` 下的使用指南
- `docs/reports/` 下的开发报告
- 项目 README.md

---

**整理完成时间**: 2026-03-24  
**整理版本**: v1.0  
**状态**: ✅ 已完成
