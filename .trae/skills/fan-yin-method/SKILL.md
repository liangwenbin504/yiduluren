# 反吟法专用起课法 SKILL

## 技能描述
反吟法专用起课法，用于处理天地盘对冲的特殊情况。反吟课指天盘与地盘完全对冲（子午冲、丑未冲等）的特殊课式。

## 功能隔离
- 独立文件：`.trae/skills/fan-yin-method/SKILL.md`
- 不依赖其他九课专用 SKILL
- 仅接收总起课判断 SKILL 的调用指令
- 输出结果包含自我校验信息

## 核心规则

### 1. 反吟课定义
天地盘完全对冲的课式为反吟课。即每个地支位置的天盘都是该地支的对冲地支。

### 2. 反吟课判定
```python
def is_fan_yin(tiandi_pan):
    CHONG_MAP = {
        '子': '午', '午': '子',
        '丑': '未', '未': '丑',
        '寅': '申', '申': '寅',
        '卯': '酉', '酉': '卯',
        '辰': '戌', '戌': '辰',
        '巳': '亥', '亥': '巳'
    }
    
    # 检查每个位置是否都是对冲
    for dizhi, tianpan in tiandi_pan.items():
        if CHONG_MAP[dizhi] != tianpan:
            return False
    return True
```

### 3. 反吟课特点
- 天地盘对冲（天盘 = 地盘所冲）
- 月将与占时对冲（如子将午时、丑将未时等）
- 课体动荡不安，主反复、变化

### 4. 起课原则（标准规则）

反吟课的三传起法遵循以下标准规则：

**规则 1：有贼克按克贼法发用（无依格）**

- 适用条件：四课中有贼克
- 起课方法：
  - 初传：克处（有克贼的上神）
  - 中传：初传之上神（天盘）
  - 末传：中传之上神（天盘）
- 备注：此为无依格，不用遥克法

**规则 2：无贼克用井栏射格（无亲格）**

- 适用条件：四课中无贼克
- 《六壬大全》规定：辛未、辛丑、丁丑、己丑四日反吟课
- 起课方法：
  - 初传：日支驿马（以日支查驿马）
    - 巳酉丑日马在亥，申子辰日马在寅
    - 亥卯未日马在巳，寅午戌日马在申
  - 中传：支上神（**第三课的上神**）
  - 末传：干上神（第一课的上神，即日干寄宫的天盘）
- 格局：井栏格（无亲格）

**重要说明**：
- "驿马"是指**日支的驿马**，不是日干禄位
- **支上神**专指**第三课的上神**（日支的阳神）
- 中传取**第三课的上神**
- 末传取**第一课的上神**（干神的阳神）

**示例**：
- 丁丑日：丑属巳酉丑，驿马在亥，初传=亥
- 辛未日：未属亥卯未，驿马在巳，初传=巳

**特别备注**：
- 丁未、己丑二课列入八专课范畴，不适用反吟法起课规则

### 5. 冲的关系
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

### `is_fan_yin(tiandi_pan)`
判断是否为反吟课。

**参数**：
- `tiandi_pan`: 天地盘映射

**返回**：
- `bool`: True 表示是反吟课，False 表示不是

**判断条件**：
所有地支位置的天盘都是该地支的对冲地支

### `determine_chu_chuan(ri_zhi, tiandi_pan)`
确定反吟法初传。

**参数**：
- `ri_zhi`: 日支
- `tiandi_pan`: 天地盘映射

**返回**：
- `str`: 初传（天盘）

**逻辑**：
```python
def determine_chu_chuan(ri_zhi, tiandi_pan):
    # 取日支上神
    return tiandi_pan[ri_zhi]
```

### `determine_zhong_mo_chuan(chu_chuan)`
确定反吟法中末传。

**参数**：
- `chu_chuan`: 初传

**返回**：
- `(zhong_chuan, mo_chuan)`: 中传和末传

**逻辑**：
```python
def determine_zhong_mo_chuan(chu_chuan):
    CHONG_MAP = {...}
    
    # 中传：初传所冲
    zhong_chuan = CHONG_MAP[chu_chuan]
    
    # 末传：中传所冲（回到初传）
    mo_chuan = CHONG_MAP[zhong_chuan]
    
    return zhong_chuan, mo_chuan
```

注意：由于对冲关系，`CHONG_MAP[CHONG_MAP[chu_chuan]]` = `chu_chuan`，所以末传 = 初传

### `validate(sanchuan, tiandi_pan)`
验证反吟法结果是否正确。

**参数**：
- `sanchuan`: 三传列表 [初传，中传，末传]
- `tiandi_pan`: 天地盘映射

**返回**：
- `(is_valid, error_msg)`: 验证结果和错误信息

**验证规则**：
1. 必须是反吟课（天地盘对冲）
2. 初传必须是某位置的天盘（通常是日支上神）
3. 中传必须是初传所冲
4. 末传必须是中传所冲（应等于初传）

### `auto_correct(sanchuan, ri_zhi, tiandi_pan)`
自动修正反吟法错误。

**参数**：
- `sanchuan`: 当前三传
- `ri_zhi`: 日支
- `tiandi_pan`: 天地盘

**返回**：
- `corrected_sanchuan`: 修正后的三传

**修正逻辑**：
1. 重新计算初传（日支上神）
2. 重新计算中传（初传所冲）
3. 重新计算末传（中传所冲）

## 自我校验机制

### 校验项目
1. **反吟课判定**：天地盘是否完全对冲
2. **初传来源**：初传是否为日支上神
3. **中传关系**：中传是否为初传所冲
4. **末传关系**：末传是否为中传所冲（应等于初传）
5. **回环检查**：末传是否等于初传

### 校验流程
```python
def validate_fan_yin(sanchuan, tiandi_pan):
    CHONG_MAP = {...}
    
    errors = []
    
    # 1. 检查是否为反吟课
    for dizhi, tianpan in tiandi_pan.items():
        if CHONG_MAP[dizhi] != tianpan:
            errors.append("不是反吟课，天地盘不对冲")
            return False, errors
    
    # 2. 检查初传
    chu_chuan = sanchuan[0]
    # 初传应该是某个位置的天盘
    if chu_chuan not in tiandi_pan.values():
        errors.append(f"初传{chu_chuan}不在天盘中")
    
    # 3. 检查中传
    zhong_chuan = sanchuan[1]
    expected_zhong = CHONG_MAP[chu_chuan]
    if zhong_chuan != expected_zhong:
        errors.append(f"中传错误，应为{expected_zhong}，实为{zhong_chuan}")
    
    # 4. 检查末传
    mo_chuan = sanchuan[2]
    expected_mo = CHONG_MAP[zhong_chuan]
    if mo_chuan != expected_mo:
        errors.append(f"末传错误，应为{expected_mo}，实为{mo_chuan}")
    
    # 5. 检查回环
    if mo_chuan != chu_chuan:
        errors.append(f"反吟课末传应等于初传，初传{chu_chuan}，末传{mo_chuan}")
    
    return len(errors) == 0, errors
```

## 错误修正机制

### 常见错误及修正
1. **初传错误**：重新取日支上神
2. **中传错误**：重新取初传所冲
3. **末传错误**：重新取中传所冲

### 修正流程
```python
def auto_correct_fan_yin(sanchuan, ri_zhi, tiandi_pan):
    CHONG_MAP = {...}
    
    corrected = sanchuan.copy()
    
    # 修正初传
    corrected[0] = tiandi_pan[ri_zhi]
    
    # 修正中传
    chu_chuan = corrected[0]
    corrected[1] = CHONG_MAP[chu_chuan]
    
    # 修正末传
    zhong_chuan = corrected[1]
    corrected[2] = CHONG_MAP[zhong_chuan]
    
    return corrected
```

## 调用示例

```python
# 总起课判断 SKILL 调用反吟法专用 SKILL
from .trae.skills.fan_yin_method import is_fan_yin, determine_chu_chuan, determine_zhong_mo_chuan

# 课式信息
info = {
    'ri_zhi': '子',
    'tiandi_pan': {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
}

# 判断是否为反吟课
if is_fan_yin(info['tiandi_pan']):
    # 确定初传
    chu_chuan = determine_chu_chuan(info['ri_zhi'], info['tiandi_pan'])
    
    # 确定中末传
    zhong_chuan, mo_chuan = determine_zhong_mo_chuan(chu_chuan)
    
    # 验证结果
    sanchuan = [chu_chuan, zhong_chuan, mo_chuan]
    is_valid, errors = validate(sanchuan, info['tiandi_pan'])
    
    if not is_valid:
        # 自动修正
        sanchuan = auto_correct(sanchuan, info['ri_zhi'], info['tiandi_pan'])
```

## 优先级说明

反吟法在九种起课法则中的优先级：
1. 贼克法
2. 比用法
3. 涉害法
4. 遥克法
5. 昴星法
6. 别责法
7. 八专法
8. 伏吟法
9. **反吟法（天地盘对冲）** ← 第 9 优先级

注意：反吟法优先级最低，因为反吟课是特殊课体，通常在其他法则都不适用时才使用

## 冲突解决

### 与伏吟法的关系
- 伏吟课：天地盘相同（子位子、丑位丑...）
- 反吟课：天地盘对冲（子位午、丑位未...）
- 两者互斥，不可能同时发生

### 与其他课式的关系
- 反吟课可能同时是贼克课、遥克课等
- 如果反吟课有其他克贼关系，优先使用其他法则
- 只有在无克无遥的情况下，才使用反吟法

### 判断流程
```python
def decide_fan_yin_or_other(sike, tiandi_pan):
    # 1. 检查是否反吟
    if not is_fan_yin(tiandi_pan):
        return None  # 不是反吟
    
    # 2. 检查克贼
    ke_zai = []
    for ke in sike:
        if is_xia_zei_shang(ke['shang'], ke['xia']):
            ke_zai.append(ke)
        elif is_shang_ke_xia(ke['shang'], ke['xia']):
            ke_zai.append(ke)
    
    if len(ke_zai) > 0:
        return '贼克法/比用法/涉害法'  # 有克贼，优先用克贼法
    
    # 3. 检查遥克
    yao_ke_list = get_yao_ke_list(sike, ri_gan)
    
    if len(yao_ke_list) > 0:
        return '遥克法'  # 有遥克，用遥克
    
    return '反吟法'  # 无克无遥，用反吟
```

## 测试用例

### 测试用例 1：子午反吟
```python
# 甲子日 午将子时
# 天地盘：子位午、丑位未、寅位申...
# 日支子，子上神午
# 初传：午
# 中传：午冲 = 子
# 末传：子冲 = 午
expected_sanchuan = ['午', '子', '午']
```

### 测试用例 2：丑未反吟
```python
# 乙丑日 未将丑时
# 天地盘：子位午、丑位未、寅位申...
# 日支丑，丑上神未
# 初传：未
# 中传：未冲 = 丑
# 末传：丑冲 = 未
expected_sanchuan = ['未', '丑', '未']
```

## 反吟课例

### 反吟课月将时冲组合
- 子将午时
- 丑将未时
- 寅将申时
- 卯将酉时
- 辰将戌时
- 巳将亥时
- 午将子时
- 未将丑时
- 申将寅时
- 酉将卯时
- 戌将辰时
- 亥将巳时

## 反吟课特点

### 课体特征
- 天地盘对冲，主动荡不安
- 事多反复，难以安定
- 来去匆匆，不久长
- 旧事重提，故人重逢

### 三传特点
- 初传与末传相同（回环）
- 中传为初传所冲
- 传变快速，变化多端

## 文件结构
```
.trae/skills/
├── fan-yin-method/
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
├── ba-zhuan-method/
│   └── SKILL.md
└── fu-yin-method/
    └── SKILL.md
```

## 版本历史
- v1.0 (2026-03-14): 初始版本，包含反吟法核心规则、API 定义、自我校验和错误修正机制
- v2.0 (2026-03-14): 修正井栏格规则，按《六壬大全》规定：
  - 辛未、辛丑、丁丑、己丑四日反吟课，以驿马为用
  - 驿马规则：巳酉丑日马在亥，亥卯未日马在巳
  - 初传取驿马，中传取支上神，末传取干上神
  - 格局：井栏格（无亲格）
- v3.0 (2026-03-14): 再次修正井栏格规则
  - 井栏格的"驿马"实际是指**日干禄位**，不是三合局驿马
  - 丁禄在巳，己禄在午，辛禄在酉
  - 中传取**第四课的上神**（支神的阴神），不是第三课
  - 末传取**第一课的上神**（干神的阳神）
- v4.0 (2026-03-14): 最终修正驿马规则
  - "驿马"是指**日支的驿马**，不是日干禄位
  - 驿马规则：巳酉丑日马在亥，申子辰日马在寅，亥卯未日马在巳，寅午戌日马在申
  - 示例：丁丑日，丑属巳酉丑，驿马在亥
- v5.0 (2026-03-14): 修正支上神定义
  - **支上神**专指**第三课的上神**（日支的阳神）
  - 中传取**第三课的上神**
