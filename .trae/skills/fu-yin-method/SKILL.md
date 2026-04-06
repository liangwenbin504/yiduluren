---
name: "fu-yin-method"
description: "伏吟法专用起课技能，用于月将=占时的情况。Invoke when the decision system identifies 伏吟课 (yue_jiang equals shi_chen)."
---

# 伏吟法专用起课技能

## 核心功能

专门处理**月将=占时**（天地盘相同）的情况。

## 调用时机

**当总起课判断 SKILL 检测到月将等于占时时调用此 SKILL**。

## 伏吟法起课规则

### 核心规则

```
刚日（阳日）：初传取干上神，中末取刑冲
柔日（阴日）：初传取支上神，中末取刑冲
自刑日：初传取冲
```

### 《六壬大全》特殊规则：初传自刑的处理

**当出现初传为自刑（辰午酉亥）时**，按以下规则处理：

1. **中传取法**：
   - 阳日（甲丙戊庚壬）：中传取**支上神**（第三课上神）
   - 阴日（乙丁己辛癸）：中传取**干上神**（第一课上神）

2. **末传取法**：
   - 中传不是自刑：末传取**中传所刑**
   - 中传是自刑：末传取**中传所冲**
   - 末传刑回初传（回头刑）：末传取**中传所冲**

### 刑冲关系

```python
# 相刑
XING_MAP = {
    '子': '卯', '卯': '子',  # 子卯相刑
    '寅': '巳', '巳': '申', '申': '寅',  # 寅巳申三刑
    '丑': '戌', '戌': '未', '未': '丑',  # 丑戌未三刑
    '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'  # 自刑
}

# 相冲
CHONG_MAP = {
    '子': '午', '丑': '未', '寅': '申', '卯': '酉',
    '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
    '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
}

# 自刑地支
ZI_XING = ['辰', '午', '酉', '亥']
```

## 处理流程

### 第一步：判断日干阴阳和自刑

```python
def determine_type(ri_gan, ri_zhi):
    """判断伏吟课类型"""
    
    is_yang = is_yang_ri(ri_gan)
    is_zi_xing = ri_zhi in ZI_XING
    
    return {
        'is_yang': is_yang,
        'is_zi_xing': is_zi_xing,
        'type': '刚日' if is_yang else '柔日'
    }
```

### 第二步：确定初传

```python
def determine_chu_chuan(ri_gan, ri_zhi, tiandi_pan, type_info):
    """确定初传"""
    
    # 自刑日：初传取冲
    if type_info['is_zi_xing']:
        return CHONG_MAP[ri_zhi]
    
    # 刚日：初传取干上神
    if type_info['is_yang']:
        ri_gan_ji_gong = TIAN_GAN_JI_GONG[ri_gan]
        return tiandi_pan[ri_gan_ji_gong]
    
    # 柔日：初传取支上神
    else:
        return tiandi_pan[ri_zhi]
```

### 第三步：确定中传

```python
def determine_zhong_chuan(chu_chuan):
    """确定中传（取初传所刑）"""
    
    # 初传自刑，用冲
    if chu_chuan in ZI_XING:
        return CHONG_MAP[chu_chuan]
    
    return XING_MAP.get(chu_chuan, chu_chuan)
```

### 第四步：确定末传

```python
def determine_mo_chuan(chu_chuan, zhong_chuan):
    """确定末传（取中传所刑，防回头刑）"""
    
    # 中传自刑，用冲
    if zhong_chuan in ZI_XING:
        return CHONG_MAP[zhong_chuan]
    
    # 末传刑回初传（回头刑），用冲
    mo_chuan = XING_MAP.get(zhong_chuan, zhong_chuan)
    if mo_chuan == chu_chuan:
        return CHONG_MAP[zhong_chuan]
    
    return mo_chuan
```

## 输出格式

```python
{
    '课体': '伏吟课',
    '起法': '伏吟法',
    '初传': '初传地支',
    '中传': '中传地支',
    '末传': '末传地支',
    '类型': '刚日' or '柔日',
    '是否自刑': True/False,
    '刑冲分析': {
        '初传刑': ...,
        '中传刑': ...,
        '末传冲': ...
    }
}
```

## 自我校验

### 校验规则

```python
def validate(result, info):
    """校验伏吟法结果"""
    
    # 1. 检查课体
    if result['课体'] != '伏吟课':
        return False, '课体错误'
    
    # 2. 检查起法
    if result['起法'] != '伏吟法':
        return False, '起法错误'
    
    # 3. 检查中传是否为初传所刑
    if result['初传'] in ZI_XING:
        expected_zhong = CHONG_MAP[result['初传']]
    else:
        expected_zhong = XING_MAP.get(result['初传'], result['初传'])
    
    if result['中传'] != expected_zhong:
        return False, '中传不是初传所刑'
    
    # 4. 检查末传是否为中传所刑（防回头刑）
    if result['中传'] in ZI_XING:
        expected_mo = CHONG_MAP[result['中传']]
    else:
        expected_mo = XING_MAP.get(result['中传'], result['中传'])
        # 防回头刑
        if expected_mo == result['初传']:
            expected_mo = CHONG_MAP[result['中传']]
    
    if result['末传'] != expected_mo:
        return False, '末传不是中传所刑（或应用冲）'
    
    return True, '校验通过'
```

## 使用示例

### 示例 1：乙丑日丑将丑时（柔日伏吟，非自刑）

```python
info = {
    'ri_gan': '乙',  # 阴日
    'ri_zhi': '丑',  # 非自刑
    'yue_jiang': '丑',
    'shi_chen': '丑',
    'tiandi_pan': {
        '丑': '丑',  # 伏吟，天地盘相同
        '辰': '辰',  # 乙寄辰，辰上见辰
        ...
    }
}

result = execute(info)
# 结果：
# {
#     '课体': '伏吟课',
#     '起法': '伏吟法',
#     '类型': '柔日',
#     '是否自刑': False,
#     '初传': '丑',  # 柔日取支上神
#     '中传': '戌',  # 丑刑戌
#     '末传': '未',  # 戌刑未
# }
```

### 示例 2：丁卯日卯将卯时（柔日伏吟，自刑）

```python
info = {
    'ri_gan': '丁',  # 阴日
    'ri_zhi': '卯',  # 自刑
    'yue_jiang': '卯',
    'shi_chen': '卯',
    'tiandi_pan': {...}
}

result = execute(info)
# 结果：
# {
#     '课体': '伏吟课',
#     '起法': '伏吟法',
#     '类型': '柔日',
#     '是否自刑': True,
#     '初传': '酉',  # 自刑取冲（卯冲酉）
#     '中传': '子',  # 酉刑子
#     '末传': '午',  # 子刑卯（回头刑），改用冲（子冲午）
# }
```

## 版本信息

- **版本**：v2.0（修正三刑关系）
- **更新日期**：2026-03-14
- **依赖**：daliuren-qike-decision
- **修正说明**：
  - v1.0：初始版本，包含回头刑修正
  - **v2.0：修正三刑关系**
    - 丑戌未三刑的正确顺序：**丑→戌→未→丑**
    - 错误顺序：丑→未→戌→丑（已修正）
    - 恃势之刑：丑刑戌，戌刑未，未刑丑
    - **不能反过来**：戌不刑丑，未不刑戌，丑不刑未
