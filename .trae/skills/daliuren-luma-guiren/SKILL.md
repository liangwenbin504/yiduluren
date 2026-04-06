---
name: "daliuren-luma-guiren"
description: "大六壬禄马贵人到山到向计算模块，提供完整的年月日时四柱禄马贵人到山到向判定功能。Invoke when user needs to calculate 禄马贵人到山到向、分析择日吉课、或进行山家向首吉课判定。"
---

# 大六壬禄马贵人到山到向 SKILL

## 功能说明

本 SKILL 提供大六壬禄马贵人到山到向的完整计算功能，包括：

1. **禄神计算**：十天干对应禄神位置
2. **驿马计算**：十二地支对应驿马位置
3. **贵人计算**：天乙贵人位置判定
4. **山家向首映射**：二十四山山家、向首斗首体系转换
5. **本山本向判定**：本山禄神、本山贵人特殊规则
6. **完整分析**：年月日时四柱综合分析与评分

## 核心特性

### 1. 二十四山体系

**二十四山山家映射（斗首体系）**：
- 壬子癸丑 → 子山家
- 艮寅甲卯乙辰 → 卯山家
- 巽巳丙午丁未 → 午山家
- 坤申庚酉辛戌 → 酉山家
- 乾亥 → 戌山家

**二十四山向首映射（斗首体系）**：
- 壬子癸丑 → 午向首
- 艮寅甲卯乙辰 → 酉向首
- 巽巳丙午丁未 → 子向首
- 坤申庚酉辛戌 → 卯向首
- 乾亥 → 辰向首

### 2. 禄马贵人规则

**十天干禄神**：
```
甲→寅, 乙→卯, 丙→巳, 丁→午, 戊→巳
己→午, 庚→申, 辛→酉, 壬→亥, 癸→子
```

**十二地支驿马**：
```
申子辰→寅, 亥卯未→巳
寅午戌→申, 巳酉丑→亥
```

**本山禄神**：
每个二十四山都有对应的本山禄神位置

**本山贵人**：
每个二十四山都有对应的本山贵人位置（2个）

### 3. 评分标准

| 条件 | 评分 | 评语 |
|------|------|------|
| 日柱禄马贵人未到山到向 | 50分 | 平课 |
| 仅日柱禄马贵人到山到向 | 60分 | 吉课 |
| 两柱禄马贵人到山到向 | 80分 | 中吉课 |
| 年月日禄马贵人皆到山到向 | 100分 | 上吉课 |
| 本山本向吉课 | +10分（上限100） | 特殊吉课 |

## 使用方法

### 基本调用方式

```python
from core_modules.engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen

# 初始化计算器
calculator = DaLiuRenLuMaGuiRen()

# 完整分析
result = calculator.analyze_full(
    mountain='壬',           # 坐山
    shichen='子',            # 时辰
    nian_gan='甲',           # 年干
    nian_zhi='子',           # 年支
    yue_gan='丙',           # 月干
    yue_zhi='寅',           # 月支
    ri_gan='甲',             # 日干
    ri_zhi='子'              # 日支
)

# 打印分析结果
calculator.print_analysis(result)
```

### 单柱检查

```python
# 检查单柱禄马贵人到山到向
pillar_result = calculator.check_single_pillar(
    tian_gan='甲',
    di_zhi='子',
    tiandi_pan=tiandi_pan,
    shichen='子',
    shan_jia='子',
    xiang_shou='午',
    pillar_name='年'
)
```

### 本山本向检查

```python
# 检查本山本向特殊规则
ben_shan_result = calculator.check_ben_shan_ben_xiang(
    mountain='壬',
    shan_jia='子',
    xiang_shou='午',
    tiandi_pan=tiandi_pan,
    shichen='子',
    nian_gan='甲',
    nian_zhi='子',
    yue_gan='丙',
    yue_zhi='寅',
    ri_gan='甲',
    ri_zhi='子'
)
```

## 返回结果结构

### 完整分析结果

```python
{
    'mountain': '壬',           # 坐山
    'shan_jia': '子',           # 山家
    'xiang_shou': '午',         # 向首
    'shichen': '子',            # 时辰
    'nian_result': {...},       # 年柱结果
    'yue_result': {...},        # 月柱结果
    'ri_result': {...},         # 日柱结果
    'ben_shan_result': {...},   # 本山本向结果
    'qualified_count': 2,       # 合格柱数
    'score': 80,                # 评分
    'status': '中吉课'          # 评语
}
```

### 单柱结果

```python
{
    'pillar': '年',
    'tian_gan': '甲',
    'di_zhi': '子',
    'lu_zhi': '寅',
    'ma_zhi': '寅',
    'guiren_zhi': '未',
    'lu_to_shan': False,
    'lu_to_xiang': False,
    'ma_to_shan': False,
    'ma_to_xiang': False,
    'guiren_to_shan': False,
    'guiren_to_xiang': False,
    'shan_count': 0,
    'xiang_count': 0,
    'pillar_qualified': False
}
```

## 依赖模块

本 SKILL 依赖以下模块：

1. `gui_ren_engine` - 贵人计算引擎
2. `dizhi_layout_generator` - 天地盘布局生成器

## 跨项目通用性

为确保跨项目通用性，本 SKILL 遵循以下设计原则：

1. **独立接口**：所有功能通过 `DaLiuRenLuMaGuiRen` 类统一暴露
2. **标准数据结构**：使用 Python 标准数据类型（dict、list、str）
3. **最小依赖**：仅依赖核心计算模块，无外部库依赖
4. **清晰文档**：提供完整的 API 文档和使用示例

## 集成到其他项目

### 步骤 1：复制核心文件

将以下文件复制到目标项目：
- `core_modules/engine/daliuren_luma_guiren.py`
- `core_modules/engine/gui_ren_engine.py`
- `core_modules/engine/dizhi_layout_generator.py`

### 步骤 2：调整导入路径

根据目标项目的目录结构，调整 `daliuren_luma_guiren.py` 中的导入语句：

```python
# 原导入
from gui_ren_engine import GuiRenCalculator
from dizhi_layout_generator import arrange_tiandi_pan

# 调整为目标项目路径
from .gui_ren_engine import GuiRenCalculator
from .dizhi_layout_generator import arrange_tiandi_pan
# 或
from your_package.gui_ren_engine import GuiRenCalculator
from your_package.dizhi_layout_generator import arrange_tiandi_pan
```

### 步骤 3：初始化并使用

```python
# 导入模块
from your_package.daliuren_luma_guiren import DaLiuRenLuMaGuiRen

# 使用
calculator = DaLiuRenLuMaGuiRen()
result = calculator.analyze_full(...)
```

## 输出格式规范

### 控制台输出格式

```
====================================================================================================
大六壬禄马贵人到山到向完整分析
====================================================================================================

坐山: 壬
山家: 子
向首: 午
时辰: 子

年柱: 甲子
  禄神: 寅 
  驿马: 寅 
  贵人: 未 
  到山数: 0
  到向数: 0
  合格: ❌

月柱: 丙寅
  禄神: 巳 
  驿马: 申 
  贵人: 亥 
  到山数: 0
  到向数: 0
  合格: ❌

日柱: 甲子
  禄神: 寅 
  驿马: 寅 
  贵人: 未 
  到山数: 0
  到向数: 0
  合格: ❌

⭐ 本山本向吉课:
   - 本山壬禄神亥到山
   - 本山壬贵人卯到山
   - 本山壬贵人巳到山

📊 合格数: 0/3
🎯 评分: 60分
📋 评语: 吉课（仅日柱禄马贵人到山到向）

====================================================================================================
```

## 测试验证

### 测试案例

**案例 1：壬山甲子年丙寅月甲子日子时**
- 坐山：壬
- 年柱：甲子
- 月柱：丙寅
- 日柱：甲子
- 时辰：子

**案例 2：丙山丙午年甲午月丙午日午时**
- 坐山：丙
- 年柱：丙午
- 月柱：甲午
- 日柱：丙午
- 时辰：午

## 版本信息

- **当前版本**：v1.0
- **创建日期**：2026-03-27
- **核心功能**：禄马贵人到山到向计算、本山本向判定、综合评分
- **状态**：✅ 已完成，可跨项目集成

## 注意事项

1. **依赖模块**：确保 `gui_ren_engine` 和 `dizhi_layout_generator` 模块可用
2. **天地盘**：默认月将为亥，可根据需要修改
3. **评分规则**：评分标准可根据实际需求调整
4. **本山本向**：壬山丙向有特殊判定规则

## 维护指南

### 添加新的判定规则

在 `check_ben_shan_ben_xiang` 方法中添加新的规则分支。

### 修改评分标准

在 `analyze_full` 方法中修改评分逻辑。

### 扩展二十四山

在 `SHAN_JIA_MAP` 和 `XIANG_SHOU_MAP` 中添加新的映射关系。
