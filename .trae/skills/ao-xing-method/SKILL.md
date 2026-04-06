---
name: "ao-xing-method"
description: "昴星法专用起课技能，用于四课无克贼无遥克的普通课式。Invoke when the decision system identifies 昴星课 (no 克贼 no 遥克，normal four courses)."
---

# 昴星法专用起课技能

## 核心功能

专门处理**四课无克贼、无遥克、非特殊课体**的普通课式。

## 调用时机

**当总起课判断 SKILL 检测到四课无克贼无遥克且非特殊课体时调用此 SKILL**。

## 昴星法起课规则

### 核心规则

```
阳日取酉上，阴日取酉下
【关键修正】中末传取法：
  阳日：中传取支上神，末传取干上神
  阴日：中传取干上神，末传取支上神
```

### 详细说明

**阳日（甲、丙、戊、庚、壬）**：
- 初传：取地盘酉宫的上神（天盘）
- 中传：取**支上神**（日支的天盘）
- 末传：取**干上神**（日干寄宫的天盘）

**阴日（乙、丁、己、辛、癸）**：
- 初传：取天盘酉宫的下神（地盘）
- 中传：取**干上神**（日干寄宫的天盘）
- 末传：取**支上神**（日支的天盘）

## 处理流程

### 第一步：判断日干阴阳

```python
def is_yang_ri(ri_gan):
    """判断日干是否为阳日"""
    yang_gan = ['甲', '丙', '戊', '庚', '壬']
    return ri_gan in yang_gan
```

### 第二步：确定初传

```python
def determine_chu_chuan(ri_gan, tiandi_pan):
    """确定初传"""
    
    if is_yang_ri(ri_gan):
        # 阳日：取地盘酉宫的上神
        chu_chuan = tiandi_pan['酉']
    else:
        # 阴日：取天盘酉宫的下神（地盘）
        for dizhi, tianpan in tiandi_pan.items():
            if tianpan == '酉':
                chu_chuan = dizhi
                break
    
    return chu_chuan
```

### 第三步：确定中末传

```python
def determine_zhong_mo_chuan(ri_gan, ri_zhi, tiandi_pan):
    """确定中末传（关键修正：区分阴阳日）"""
    
    # 干上神：日干寄宫的天盘
    ri_gan_ji_gong = TIAN_GAN_JI_GONG[ri_gan]
    gan_shang = tiandi_pan[ri_gan_ji_gong]
    
    # 支上神：日支的天盘
    zhi_shang = tiandi_pan[ri_zhi]
    
    if is_yang_ri(ri_gan):
        # 阳日：中传取支上神，末传取干上神
        zhong_chuan = zhi_shang
        mo_chuan = gan_shang
    else:
        # 阴日：中传取干上神，末传取支上神
        zhong_chuan = gan_shang
        mo_chuan = zhi_shang
    
    return zhong_chuan, mo_chuan
```

## 输出格式

```python
{
    '课体': '昴星课',
    '起法': '昴星法',
    '初传': '初传地支',
    '中传': '中传地支',
    '末传': '末传地支',
    '日干阴阳': '阳日' or '阴日',
    '酉的位置': {
        '地盘酉': '天盘 X',
        '天盘酉': '地盘 Y'
    }
}
```

## 自我校验

### 校验规则

```python
def validate(result, info):
    """校验昴星法结果"""
    
    # 1. 检查课体
    if result['课体'] != '昴星课':
        return False, '课体错误'
    
    # 2. 检查起法
    if result['起法'] != '昴星法':
        return False, '起法错误'
    
    # 3. 检查日干阴阳
    is_yang = is_yang_ri(info['ri_gan'])
    if (is_yang and result['日干阴阳'] != '阳日') or \
       (not is_yang and result['日干阴阳'] != '阴日'):
        return False, '日干阴阳判断错误'
    
    # 4. 检查初传
    if is_yang:
        if result['初传'] != info['tiandi_pan']['酉']:
            return False, '阳日初传应该是酉上神'
    else:
        # 阴日检查
        for dizhi, tianpan in info['tiandi_pan'].items():
            if tianpan == '酉':
                if result['初传'] != dizhi:
                    return False, '阴日初传应该是酉下神'
                break
    
    # 5. 检查中传
    ri_gan_shang = info['tiandi_pan'][TIAN_GAN_JI_GONG[info['ri_gan']]]
    if result['中传'] != ri_gan_shang:
        return False, '中传应该是日干上神'
    
    # 6. 检查末传
    ri_zhi_shang = info['tiandi_pan'][info['ri_zhi']]
    if result['末传'] != ri_zhi_shang:
        return False, '末传应该是日支上神'
    
    return True, '校验通过'
```

## 使用示例

### 示例：己巳日午将巳时（阴日昴星课）

```python
info = {
    'ri_gan': '己',
    'ri_zhi': '巳',
    'tiandi_pan': {
        '巳': '酉',  # 天盘酉落地盘巳位
        '未': '申',  # 己寄未，未上见申
        '巳': '午',  # 巳上见午
        ...
    }
}

result = execute(info)
# 结果：
# {
#     '课体': '昴星课',
#     '起法': '昴星法',
#     '初传': '巳',  # 天盘酉落地盘巳位
#     '中传': '申',  # 己寄未，未上见申
#     '末传': '午',  # 巳上见午
#     '日干阴阳': '阴日',
#     '酉的位置': {
#         '地盘酉': '天盘戌',
#         '天盘酉': '地盘巳'
#     }
# }
```

## 版本信息

- **版本**：v2.0（中末传取法修正）
- **更新日期**：2026-03-14
- **依赖**：daliuren-qike-decision
- **修正说明**：
  - v1.0：初始版本
  - **v2.0：修正中末传取法**
    - 阳日：中传取支上神，末传取干上神
    - 阴日：中传取干上神，末传取支上神
