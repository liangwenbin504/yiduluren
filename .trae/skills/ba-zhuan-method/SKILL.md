# 八专法专用起课法 SKILL

## 技能描述
八专法专用起课法，用于处理日干支同位的特殊情况。八专课指日干和日支在同一位置（伏吟）的特殊课式。

## 功能隔离
- 独立文件：`.trae/skills/ba-zhuan-method/SKILL.md`
- 不依赖其他九课专用 SKILL
- 仅接收总起课判断 SKILL 的调用指令
- 输出结果包含自我校验信息

## 核心规则

### 1. 八专课定义
日干和日支同位（日干寄宫与日支相同）的课式为八专课。

### 2. 八专课判定
```python
def is_ba_zhuan(ri_gan, ri_zhi):
    TIAN_GAN_JI_GONG = {
        '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
        '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'
    }
    
    # 日干寄宫与日支相同
    return TIAN_GAN_JI_GONG[ri_gan] == ri_zhi
```

### 3. 八专课特点
- 四课中只有两课（第一课和第三课相同，第二课和第四课相同）
- 天地盘伏吟（天盘与地盘相同）
- 课体特殊，需专用起课法

### 4. 起课原则（传统规则 - 不可修改）

**八专课起课规则（固定规则，永久不变）**：

- **阳日**：取日上神（日干寄宫的天盘）**顺数第三位**为初传
- **阴日**：取第四课上神（支上神的上神）**逆数第三位**为初传
- **中传**：皆用日支上神
- **末传**：皆用日支上神

**顺数/逆数说明**：
- 顺数：从本地支开始，顺时针数到目标位置（包括自己）
- 逆数：从本地支开始，逆时针数到目标位置（包括自己）
- 例如：从申顺数第三位 = 申→酉→戌 = 戌
- 例如：从戌逆数第三位 = 戌→酉→申 = 申

**注意**：此规则为八专课的传统起课法则，**永久固定，不得修改**。

### 5. 日干上神起法
由于八专课日干寄宫与日支相同，日干上神 = 日支上神

### 6. 冲的关系
```python
CHONG_MAP = {
    '子': '午', '午': '子',
    '丑': '未', '未': '丑',
    '寅': '申', '申': '寅',
    '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰',
    '巳': '亥', '亥': '巳'
}
```

## API 定义

### `is_ba_zhuan(ri_gan, ri_zhi)`
判断是否为八专课。

**参数**：
- `ri_gan`: 日干
- `ri_zhi`: 日支

**返回**：
- `bool`: True 表示是八专课，False 表示不是

**判断条件**：
日干寄宫与日支相同

### `determine_chu_chuan(ri_gan, tiandi_pan, yang_ri)`
确定八专法初传。

**参数**：
- `ri_gan`: 日干
- `tiandi_pan`: 天地盘映射
- `yang_ri`: 是否为阳日

**返回**：
- `str`: 初传（天盘）

**逻辑（传统规则 - 不可修改）**：
```python
def determine_chu_chuan(ri_gan, tiandi_pan, yang_ri):
    TIAN_GAN_JI_GONG = {
        '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
        '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'
    }
    
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    if yang_ri:
        # 阳日：取日上神顺数第三位
        ji_gong = TIAN_GAN_JI_GONG[ri_gan]
        ri_shang = tiandi_pan[ji_gong]  # 日上神
        ri_shang_index = DIZHI.index(ri_shang)
        chu_chuan_index = (ri_shang_index + 2) % 12  # 顺数第三位（包括自己）
        return DIZHI[chu_chuan_index]
    else:
        # 阴日：取第四课上神逆数第三位
        ri_zhi = ...  # 需要从上下文中获取
        zhi_shang = tiandi_pan[ri_zhi]  # 支上神
        zhi_shang_shang = tiandi_pan[zhi_shang]  # 第四课上神
        zhi_shang_shang_index = DIZHI.index(zhi_shang_shang)
        chu_chuan_index = (zhi_shang_shang_index - 2) % 12  # 逆数第三位
        return DIZHI[chu_chuan_index]
```

**注意**：此规则为**永久固定规则，不得修改**。

### `determine_zhong_mo_chuan(ri_zhi, tiandi_pan)`
确定八专法中传和末传。

**参数**：
- `ri_zhi`: 日支
- `tiandi_pan`: 天地盘映射

**返回**：
- `tuple`: (中传，末传)

**逻辑（传统规则 - 不可修改）**：
```python
def determine_zhong_mo_chuan(ri_zhi, tiandi_pan):
    # 中传：日支上神
    zhong_chuan = tiandi_pan[ri_zhi]
    # 末传：日支上神
    mo_chuan = tiandi_pan[ri_zhi]
    return (zhong_chuan, mo_chuan)
```

**注意**：此规则为**永久固定规则，不得修改**。

### `validate(sanchuan, ri_gan, ri_zhi, tiandi_pan)`
验证八专法结果是否正确。

**参数**：
- `sanchuan`: 三传列表 [初传，中传，末传]
- `ri_gan`: 日干
- `ri_zhi`: 日支
- `tiandi_pan`: 天地盘映射

**返回**：
- `(is_valid, error_msg)`: 验证结果和错误信息

**验证规则**：
1. 必须是八专课（日干寄宫 = 日支）
2. 初传必须是日干上神
3. 中传必须是日支上神
4. 末传必须是初传所冲

### `auto_correct(sanchuan, ri_gan, ri_zhi, tiandi_pan)`
自动修正八专法错误。

**参数**：
- `sanchuan`: 当前三传
- `ri_gan`: 日干
- `ri_zhi`: 日支
- `tiandi_pan`: 天地盘

**返回**：
- `corrected_sanchuan`: 修正后的三传

**修正逻辑**：
1. 重新计算初传（日干上神）
2. 重新计算中传（日支上神）
3. 重新计算末传（初传所冲）

## 自我校验机制

### 校验项目
1. **八专课判定**：日干寄宫是否等于日支
2. **伏吟检查**：天地盘是否伏吟（天盘 = 地盘）
3. **初传来源**：初传是否为日干上神
4. **中传来源**：中传是否为日支上神
5. **末传关系**：末传是否为初传所冲

### 校验流程
```python
def validate_ba_zhuan(sanchuan, ri_gan, ri_zhi, tiandi_pan):
    TIAN_GAN_JI_GONG = {...}
    CHONG_MAP = {...}
    
    errors = []
    
    # 1. 检查是否为八专课
    if TIAN_GAN_JI_GONG[ri_gan] != ri_zhi:
        errors.append("不是八专课，日干寄宫与日支不同")
        return False, errors
    
    # 2. 检查伏吟
    for dizhi, tianpan in tiandi_pan.items():
        if dizhi != tianpan:
            errors.append("八专课应伏吟，但天地盘不同")
            break
    
    # 3. 检查初传
    chu_chuan = sanchuan[0]
    ji_gong = TIAN_GAN_JI_GONG[ri_gan]
    expected_chu = tiandi_pan[ji_gong]
    if chu_chuan != expected_chu:
        errors.append(f"初传错误，应为{expected_chu}，实为{chu_chuan}")
    
    # 4. 检查中传
    zhong_chuan = sanchuan[1]
    expected_zhong = tiandi_pan[ri_zhi]
    if zhong_chuan != expected_zhong:
        errors.append(f"中传错误，应为{expected_zhong}，实为{zhong_chuan}")
    
    # 5. 检查末传
    mo_chuan = sanchuan[2]
    expected_mo = CHONG_MAP[chu_chuan]
    if mo_chuan != expected_mo:
        errors.append(f"末传错误，应为{expected_mo}，实为{mo_chuan}")
    
    return len(errors) == 0, errors
```

## 错误修正机制

### 常见错误及修正
1. **初传错误**：重新取日干上神
2. **中传错误**：重新取日支上神
3. **末传错误**：重新取初传所冲

### 修正流程
```python
def auto_correct_ba_zhuan(sanchuan, ri_gan, ri_zhi, tiandi_pan):
    TIAN_GAN_JI_GONG = {...}
    CHONG_MAP = {...}
    
    corrected = sanchuan.copy()
    
    # 修正初传
    ji_gong = TIAN_GAN_JI_GONG[ri_gan]
    corrected[0] = tiandi_pan[ji_gong]
    
    # 修正中传
    corrected[1] = tiandi_pan[ri_zhi]
    
    # 修正末传
    chu_chuan = corrected[0]
    corrected[2] = CHONG_MAP[chu_chuan]
    
    return corrected
```

## 调用示例

```python
# 总起课判断 SKILL 调用八专法专用 SKILL
from .trae.skills.ba_zhuan_method import is_ba_zhuan, determine_chu_chuan, determine_zhong_mo_chuan

# 课式信息
info = {
    'ri_gan': '丙',
    'ri_zhi': '巳',  # 丙寄巳，八专课
    'tiandi_pan': {
        '子': '子', '丑': '丑', '寅': '寅', '卯': '卯',
        '辰': '辰', '巳': '巳', '午': '午', '未': '未',
        '申': '申', '酉': '酉', '戌': '戌', '亥': '亥'
    }
}

# 判断是否为八专课
if is_ba_zhuan(info['ri_gan'], info['ri_zhi']):
    # 确定初传
    chu_chuan = determine_chu_chuan(info['ri_gan'], info['tiandi_pan'])
    
    # 确定中末传
    zhong_chuan, mo_chuan = determine_zhong_mo_chuan(chu_chuan, info['ri_zhi'], info['tiandi_pan'])
    
    # 验证结果
    sanchuan = [chu_chuan, zhong_chuan, mo_chuan]
    is_valid, errors = validate(sanchuan, info['ri_gan'], info['ri_zhi'], info['tiandi_pan'])
    
    if not is_valid:
        # 自动修正
        sanchuan = auto_correct(sanchuan, info['ri_gan'], info['ri_zhi'], info['tiandi_pan'])
```

## 优先级说明

八专法在九种起课法则中的优先级：
1. 贼克法
2. 比用法
3. 涉害法
4. 遥克法
5. 昴星法
6. 别责法
7. **八专法（日干支同位）** ← 第 7 优先级
8. 伏吟法
9. 反吟法

## 冲突解决

### 与伏吟法的关系
- 八专课一定是伏吟课（天地盘相同）
- 但伏吟课不一定是八专课（日干支不同位）
- 如果是八专课，优先使用八专法

### 判断流程
```python
def decide_ba_zhuan_or_fu_yin(ri_gan, ri_zhi, tiandi_pan):
    TIAN_GAN_JI_GONG = {...}
    
    # 检查是否伏吟
    is_fu_yin = all(dizhi == tianpan for dizhi, tianpan in tiandi_pan.items())
    
    if not is_fu_yin:
        return None  # 不是伏吟，不用考虑八专
    
    # 检查是否八专
    if TIAN_GAN_JI_GONG[ri_gan] == ri_zhi:
        return '八专法'  # 八专课优先
    
    return '伏吟法'  # 普通伏吟课
```

## 测试用例

### 测试用例 1：丙巳日八专
```python
# 丙巳日 巳将巳时
# 丙寄巳宫，日支巳，八专课
# 天地盘伏吟
# 初传：巳上神 = 巳
# 中传：巳上神 = 巳
# 末传：巳冲 = 亥
expected_sanchuan = ['巳', '巳', '亥']
```

### 测试用例 2：丁未日八专
```python
# 丁未日 未将未时
# 丁寄未宫，日支未，八专课
# 天地盘伏吟
# 初传：未上神 = 未
# 中传：未上神 = 未
# 末传：未冲 = 丑
expected_sanchuan = ['未', '未', '丑']
```

## 八专课例

### 八专课日干支组合
- 甲寅日
- 丙巳日
- 戊巳日
- 丁未日
- 己未日
- 庚申日
- 辛戌日
- 壬亥日
- 癸丑日

注意：乙寄辰，但乙辰日不是八专课（乙木寄辰土，五行不同）

## 文件结构
```
.trae/skills/
├── ba-zhuan-method/
│   └── SKILL.md          # 本文件
├── daliuren-qike-decision/
│   └── SKILL.md          # 总起课判断 SKILL
├── zei-ke-method/
│   └── SKILL.md
├── she-hai-method/
│   └── SKILL.md
├── bi-yong-method/
│   └── SKILL.md
├── yao-ke-method/
│   └── SKILL.md
├── ao-xing-method/
│   └── SKILL.md
├── bie-ze-method/
│   └── SKILL.md
├── fu-yin-method/
│   └── SKILL.md
└── fan-yin-method/
    └── SKILL.md
```

## 版本历史
- v1.0 (2026-03-14): 初始版本，包含八专法核心规则、API 定义、自我校验和错误修正机制
