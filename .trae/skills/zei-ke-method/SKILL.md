---
name: "zei-ke-method"
description: "贼克法专用起课技能，用于四课中有克贼的情况。Invoke when the decision system identifies 贼克课 (has 克贼 in four courses)."
---

# 贼克法专用起课技能

## 核心功能

专门处理**四课中有克贼**的情况，是九种起课法则中**优先级最高**的方法。

## 调用时机

**当总起课判断 SKILL 检测到四课中有克贼时调用此 SKILL**。

## 贼克法定义

### 贼与克

- **贼（下贼上）**：地盘下神克天盘上神（下克上）
  - 例如：地盘午火克天盘申金
  - 性质：为逆，主急，主凶
  - 优先级：高

- **克（上克下）**：天盘上神克地盘下神（上克下）
  - 例如：天盘卯木克地盘丑土
  - 性质：为顺，主缓，主吉
  - 优先级：低

### 起课规则

```
1. 有下贼上，先用下贼上
2. 无上贼下，取上克下
3. 只有一个克贼课，直接取为初传
4. 多个克贼课，进入比用法
```

## 输入参数

```python
{
    'ri_gan': '日干',
    'ri_zhi': '日支',
    'tiandi_pan': 天地盘字典，
    'sike': 四课列表，
    'ke_zai': 克贼课列表
}
```

## 处理流程

### 第一步：分类克贼

```python
def classify_ke_zai(ke_zai):
    """将克贼课分为贼和克"""
    zei_ke = []  # 下贼上
    shang_ke = []  # 上克下
    
    for ke in ke_zai:
        if ke['type'] == '贼':
            zei_ke.append(ke)
        elif ke['type'] == '克':
            shang_ke.append(ke)
    
    return zei_ke, shang_ke
```

### 第二步：判断用贼还是用克

```python
def decide_use_zei_or_ke(zei_ke, shang_ke):
    """决定用贼还是用克"""
    
    # 有下贼上，优先用贼
    if zei_ke:
        return '贼', zei_ke
    
    # 无上贼下，用克
    if shang_ke:
        return '克', shang_ke
    
    # 都没有，返回空
    return None, []
```

### 第三步：确定初传

```python
def determine_chu_chuan(selected_ke, ri_gan):
    """确定初传"""
    
    # 只有一个克贼课，直接取上神
    if len(selected_ke) == 1:
        return selected_ke[0]['shang']
    
    # 多个克贼课，进入比用
    # 1. 比较阴阳（阳日取阳支，阴日取阴支）
    bi_yong_results = []
    for ke in selected_ke:
        shang = ke['shang']
        if is_yang_ri(ri_gan) and is_yang_zhi(shang):
            bi_yong_results.append(ke)
        elif not is_yang_ri(ri_gan) and not is_yang_zhi(shang):
            bi_yong_results.append(ke)
    
    # 2. 比用后判断
    if len(bi_yong_results) == 1:
        # 比用后只剩 1 个，直接取
        return bi_yong_results[0]['shang']
    elif len(bi_yong_results) > 1:
        # 比用后仍有多个，用涉害法
        return use_she_hai_fa(bi_yong_results)
    else:
        # 【关键修正 v6.0】比用后无符合，不是取先见者，而是用涉害法！
        return use_she_hai_fa(selected_ke)
    
    return None
```

### 比用后无符合的处理规则（重要修正 v6.0）

**当多个克贼课比用后无符合时（如都是阳支但日是阴日）**：

- ❌ **错误**：取先见者（第一课）
- ✅ **正确**：用涉害法比较涉害深度

**理由**：
- 比用后无符合，说明阴阳都不匹配
- 此时应该比较各课的涉害深度
- 取涉害最深者为初传
- 涉害深度相同，取先见者（缀瑕格）

**示例**：
```python
# 癸日（阴日），有两个上克下
# 第一课：上戌 下癸 [克]（戌是阳支）✗
# 第三课：上午 下酉 [克]（午是阳支）✗

# 比用：癸日取阴支，戌、午都是阳支，都不符合
# 比用后无符合 → 用涉害法

# 涉害深度：
# 戌：涉害深度 = 5
# 午：涉害深度 = 6

# 结果：取午为初传（涉害更深）
```

## 输出格式

```python
{
    '课体': '贼克课',
    '起法': '贼克法',
    '初传': '初传地支',
    '中传': '中传地支（天盘）',
    '末传': '末传地支（天盘）',
    '克贼类型': '贼' or '克',
    '克贼课次': 第几课
}
```

## 自我校验

### 校验规则

```python
def validate(result, info):
    """校验贼克法结果"""
    
    # 1. 检查课体
    if result['课体'] != '贼克课':
        return False, '课体错误'
    
    # 2. 检查起法
    if result['起法'] != '贼克法':
        return False, '起法错误'
    
    # 3. 检查初传是否来自克贼课
    if result['初传'] not in [ke['shang'] for ke in info['ke_zai']]:
        return False, '初传不是来自克贼课'
    
    # 4. 检查贼克优先级
    if info['ke_zai'] 中有贼 and result['克贼类型'] != '贼':
        return False, '有贼应该优先用贼'
    
    return True, '校验通过'
```

### 错误修正

```python
def auto_correct(result, info):
    """自动修正错误"""
    
    valid, msg = validate(result, info)
    
    if not valid:
        if '课体错误' in msg:
            result['课体'] = '贼克课'
        if '起法错误' in msg:
            result['起法'] = '贼克法'
        if '优先级错误' in msg:
            # 重新执行
            return execute(info)
    
    return result
```

## 中末传起法

### 规则

```python
def get_zhong_mo_chuan(chu_chuan, tiandi_pan):
    """获取中末传"""
    
    # 中传：取初传的上神（天盘）
    zhong_chuan = tiandi_pan[chu_chuan]
    
    # 末传：取中传的上神（天盘）
    mo_chuan = tiandi_pan[zhong_chuan]
    
    return zhong_chuan, mo_chuan
```

## 使用示例

### 示例 1：单课贼克

```python
info = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'ke_zai': [
        {'ke_ci': '第 2 课', 'type': '贼', 'shang': '申', 'xia': '午'}
    ]
}

result = execute(info)
# 结果：
# {
#     '课体': '贼克课',
#     '起法': '贼克法',
#     '初传': '申',
#     '中传': tiandi_pan['申'],
#     '末传': tiandi_pan[tiandi_pan['申']],
#     '克贼类型': '贼',
#     '克贼课次': '第 2 课'
# }
```

### 示例 2：多课贼克（需要比用）

```python
info = {
    'ri_gan': '甲',
    'ri_zhi': '子',
    'ke_zai': [
        {'ke_ci': '第 2 课', 'type': '贼', 'shang': '寅', 'xia': '申'},
        {'ke_ci': '第 3 课', 'type': '贼', 'shang': '午', 'xia': '子'},
        {'ke_ci': '第 4 课', 'type': '克', 'shang': '子', 'xia': '午'}
    ]
}

result = execute(info)
# 结果：返回 None，需要调用比用法
# result['need_bi_yong'] = True
```

## 性能优化

### 快速判断

```python
def quick_check(sike):
    """快速检查是否有克贼"""
    for ke in sike:
        if is_ke(ke['shang'], ke['xia']):
            return True
    return False
```

## 日志记录

```python
logger.info(f"贼克法：检测到{len(ke_zai)}个克贼课")
logger.info(f"贼：{len(zei_ke)}个，克：{len(shang_ke)}个")
logger.info(f"初传：{chu_chuan}")
```

## 版本信息

- **版本**：v6.0（比用后无符合用涉害法）
- **更新日期**：2026-03-14
- **依赖**：daliuren-qike-decision
- **修正说明**：
  - v1.0：初始版本，包含贼克法核心规则、比用法基础
  - **v6.0：比用后无符合用涉害法（重要修正）**
    - 比用后剩 1 个 → 直接取
    - 比用后多课 → 用涉害法
    - 比用后无符合 → 用涉害法 ← 新增
