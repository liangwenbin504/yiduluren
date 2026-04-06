# 比用法专用起课法 SKILL

## 技能描述
比用法专用起课法，用于处理多个克贼且涉害深度相同的情况。通过比较日干阴阳属性，选取与日干阴阳相同的课作为发用。

## 功能隔离
- 独立文件：`.trae/skills/bi-yong-method/SKILL.md`
- 不依赖其他九课专用 SKILL
- 仅接收总起课判断 SKILL 的调用指令
- 输出结果包含自我校验信息

## 核心规则

### 1. 比用法定义
当课式中出现多个克贼（下贼上或上克下），且涉害深度相同时，使用比用法。

### 2. 比用原则
- **阳日**：取阳神（寅申巳亥）发用
- **阴日**：取阴神（子午卯酉）发用
- 如果仍有多者，则取先见者（按四课顺序）

### 3. 日干阴阳
```python
YANG_RI_GAN = ['甲', '丙', '戊', '庚', '壬']  # 阳日干
YIN_RI_GAN = ['乙', '丁', '己', '辛', '癸']  # 阴日干
```

### 4. 地支阴阳
```python
YANG_ZHI = ['子', '寅', '辰', '午', '申', '戌']  # 阳支
YIN_ZHI = ['丑', '卯', '巳', '未', '酉', '亥']  # 阴支
```

注意：比用法中使用的"阴阳神"是指地支的阴阳属性，而非天干的阴阳。

### 5. 中末传起法
- 中传：取初传所乘地盘之神
- 末传：取中传所乘地盘之神

## API 定义

### `is_bi_yong(ke_zai, ri_gan)`
判断是否需要使用比用法。

**参数**：
- `ke_zai`: 克贼列表，每个元素包含 {'shang': 天盘，'xia': 地盘，'type': '贼'/'克'}
- `ri_gan`: 日干

**返回**：
- `bool`: True 表示需要使用比用法，False 表示不需要

**判断条件**：
1. 克贼数量 >= 2
2. 所有克贼的涉害深度相同

### `determine_chu_chuan(ke_zai, ri_gan)`
确定比用法初传。

**参数**：
- `ke_zai`: 克贼列表
- `ri_gan`: 日干

**返回**：
- `str`: 初传（天盘）

**逻辑**：
```python
def determine_chu_chuan(ke_zai, ri_gan):
    # 判断日干阴阳
    is_yang_ri = ri_gan in YANG_RI_GAN
    
    # 筛选与日干阴阳相同的地支
    candidates = []
    for ke in ke_zai:
        shang = ke['shang']  # 天盘
        # 检查天盘的阴阳属性
        if is_yang_ri and shang in YANG_ZHI:
            candidates.append(shang)
        elif not is_yang_ri and shang in YIN_ZHI:
            candidates.append(shang)
    
    # 如果有多个，取先见者（按四课顺序）
    if len(candidates) > 0:
        return candidates[0]
    
    # 如果没有符合条件的，取第一个克贼
    return ke_zai[0]['shang']
```

### `determine_zhong_mo_chuan(chu_chuan, tiandi_pan)`
确定比用法中末传。

**参数**：
- `chu_chuan`: 初传
- `tiandi_pan`: 天地盘映射

**返回**：
- `(zhong_chuan, mo_chuan)`: 中传和末传

**逻辑**：
```python
def determine_zhong_mo_chuan(chu_chuan, tiandi_pan):
    # 找到初传在地盘的位置
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == chu_chuan:
            # 中传：该位置的天盘
            zhong_chuan = tiandi_pan[dizhi]
            # 末传：中传在地盘位置的天盘
            for dizhi2, tianpan2 in tiandi_pan.items():
                if tianpan2 == zhong_chuan:
                    mo_chuan = tiandi_pan[dizhi2]
                    return zhong_chuan, mo_chuan
```

### `validate(sanchuan, ri_gan, ri_zhi)`
验证比用法结果是否正确。

**参数**：
- `sanchuan`: 三传列表 [初传，中传，末传]
- `ri_gan`: 日干
- `ri_zhi`: 日支

**返回**：
- `(is_valid, error_msg)`: 验证结果和错误信息

**验证规则**：
1. 初传必须在克贼列表中
2. 初传的阴阳属性必须与日干匹配
3. 中传必须是初传下神
4. 末传必须是中传下神

### `auto_correct(sanchuan, ke_zai, ri_gan, tiandi_pan)`
自动修正比用法错误。

**参数**：
- `sanchuan`: 当前三传
- `ke_zai`: 克贼列表
- `ri_gan`: 日干
- `tiandi_pan`: 天地盘

**返回**：
- `corrected_sanchuan`: 修正后的三传

**修正逻辑**：
1. 检查初传是否符合比用原则
2. 如不符合，重新选取初传
3. 重新计算中末传

## 自我校验机制

### 校验项目
1. **初传校验**：初传是否在克贼列表中
2. **阴阳匹配**：初传阴阳是否与日干匹配
3. **中传来源**：中传是否为初传下神
4. **末传来源**：末传是否为中传下神

### 校验流程
```python
def validate_bi_yong(sanchuan, ke_zai, ri_gan, tiandi_pan):
    errors = []
    
    # 1. 检查初传是否在克贼中
    chu_chuan = sanchuan[0]
    if not any(ke['shang'] == chu_chuan for ke in ke_zai):
        errors.append("初传不在克贼列表中")
    
    # 2. 检查阴阳匹配
    is_yang_ri = ri_gan in YANG_RI_GAN
    is_yang_zhi = chu_chuan in YANG_ZHI
    if is_yang_ri != is_yang_zhi:
        errors.append(f"初传{chu_chuan}阴阳与日干{ri_gan}不匹配")
    
    # 3. 检查中传
    zhong_chuan = sanchuan[1]
    # 找到初传在地盘的位置
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == chu_chuan:
            expected_zhong = tiandi_pan[dizhi]
            if zhong_chuan != expected_zhong:
                errors.append(f"中传错误，应为{expected_zhong}，实为{zhong_chuan}")
            break
    
    # 4. 检查末传
    mo_chuan = sanchuan[2]
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == zhong_chuan:
            expected_mo = tiandi_pan[dizhi]
            if mo_chuan != expected_mo:
                errors.append(f"末传错误，应为{expected_mo}，实为{mo_chuan}")
            break
    
    return len(errors) == 0, errors
```

## 错误修正机制

### 常见错误及修正
1. **初传阴阳错误**：重新选取与日干阴阳相同的克贼
2. **中末传错误**：重新按"初传下神为中传，中传下神为末传"计算

### 修正流程
```python
def auto_correct_bi_yong(sanchuan, ke_zai, ri_gan, tiandi_pan):
    corrected = sanchuan.copy()
    
    # 修正初传
    is_yang_ri = ri_gan in YANG_RI_GAN
    for ke in ke_zai:
        shang = ke['shang']
        is_yang_zhi = shang in YANG_ZHI
        if is_yang_ri == is_yang_zhi:
            corrected[0] = shang
            break
    
    # 修正中传
    chu_chuan = corrected[0]
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == chu_chuan:
            corrected[1] = tiandi_pan[dizhi]
            # 修正末传
            zhong_chuan = corrected[1]
            for dizhi2, tianpan2 in tiandi_pan.items():
                if tianpan2 == zhong_chuan:
                    corrected[2] = tiandi_pan[dizhi2]
                    break
            break
    
    return corrected
```

## 调用示例

```python
# 总起课判断 SKILL 调用比用法专用 SKILL
from .trae.skills.bi_yong_method import is_bi_yong, determine_chu_chuan, determine_zhong_mo_chuan

# 课式信息
info = {
    'ke_zai': [
        {'shang': '寅', 'xia': '申', 'type': '贼'},
        {'shang': '午', 'xia': '子', 'type': '贼'}
    ],
    'ri_gan': '甲',
    'tiandi_pan': {...}
}

# 判断是否需要比用法
if is_bi_yong(info['ke_zai'], info['ri_gan']):
    # 确定初传
    chu_chuan = determine_chu_chuan(info['ke_zai'], info['ri_gan'])
    
    # 确定中末传
    zhong_chuan, mo_chuan = determine_zhong_mo_chuan(chu_chuan, info['tiandi_pan'])
    
    # 验证结果
    sanchuan = [chu_chuan, zhong_chuan, mo_chuan]
    is_valid, errors = validate(sanchuan, info['ri_gan'], info['ri_zhi'])
    
    if not is_valid:
        # 自动修正
        sanchuan = auto_correct(sanchuan, info['ke_zai'], info['ri_gan'], info['tiandi_pan'])
```

## 优先级说明

比用法在九种起课法则中的优先级：
1. 贼克法（单克贼）
2. **比用法（多克贼涉害相同）** ← 第 2 优先级
3. 涉害法（多克贼涉害不同）
4. 遥克法
5. 昴星法
6. 别责法
7. 八专法
8. 伏吟法
9. 反吟法

## 冲突解决

### 与涉害法的冲突
- 如果多克贼涉害深度**相同** → 使用比用法
- 如果多克贼涉害深度**不同** → 使用涉害法（取最深者）

### 判断流程
```python
def decide_between_bi_yong_and_she_hai(ke_zai, tiandi_pan):
    if len(ke_zai) < 2:
        return None  # 不需要比用或涉害
    
    # 计算所有克贼的涉害深度
    depths = []
    for ke in ke_zai:
        depth = calculate_she_hai_depth(ke['shang'], tiandi_pan)
        depths.append(depth)
    
    # 检查涉害深度是否相同
    if len(set(depths)) == 1:
        return '比用法'  # 深度相同，用比用
    else:
        return '涉害法'  # 深度不同，取最深者
```

## 测试用例

### 测试用例 1：阳日比用
```python
# 甲子日 午将子时
# 克贼：寅申（贼）、午子（贼）
# 甲为阳日，寅为阳支，午为阳支
# 取先见者寅发用
expected_chu_chuan = '寅'
```

### 测试用例 2：阴日比用
```python
# 乙丑日 卯将丑时
# 克贼：申卯（贼）、酉午（贼）
# 乙为阴日，申为阳支，酉为阴支
# 取酉发用
expected_chu_chuan = '酉'
```

## 文件结构
```
.trae/skills/
├── bi-yong-method/
│   └── SKILL.md          # 本文件
├── daliuren-qike-decision/
│   └── SKILL.md          # 总起课判断 SKILL
├── zei-ke-method/
│   └── SKILL.md
├── she-hai-method/
│   └── SKILL.md
├── yao-ke-method/
│   └── SKILL.md
├── ao-xing-method/
│   └── SKILL.md
├── bie-ze-method/
│   └── SKILL.md
├── ba-zhuan-method/
│   └── SKILL.md
├── fu-yin-method/
│   └── SKILL.md
└── fan-yin-method/
    └── SKILL.md
```

## 版本历史
- v1.0 (2026-03-14): 初始版本，包含比用法核心规则、API 定义、自我校验和错误修正机制
