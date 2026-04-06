# 遥克法专用起课法 SKILL

## 技能描述
遥克法专用起课法，用于处理四课中无克贼但有遥克的情况。遥克指日干与四课上神之间的相克关系。

## 功能隔离
- 独立文件：`.trae/skills/yao-ke-method/SKILL.md`
- 不依赖其他九课专用 SKILL
- 仅接收总起课判断 SKILL 的调用指令
- 输出结果包含自我校验信息

## 核心规则

### 1. 遥克法定义
四课中无下贼上、无上克下，但日干与四课上神之间存在相克关系时使用遥克法。

### 2. 遥克类型
- **日干克上神**：日干五行克四课上神五行
- **上神克日干**：四课上神五行克日干五行

### 3. 取用原则（重要修正 v2.0）

**多个遥克时的比用规则**：

当有多个遥克（上神克日干或日干克上神）时，**必须遵循"有比用比"原则**：

1. **优先取上神克日干**（他克我为优先）
2. **有多个上神克日干时**：
   - 先比较阴阳（阳日取阳支，阴日取阴支）
   - 阴阳相同：比较先天数，取大者
   - 先天数相同：取先见者
3. **无上神克日干，有多个日干克上神时**：
   - 同样遵循比用规则（阴阳 → 数值 → 先见）

**比用原则详细说明**：
```python
# 多个遥克的比用流程
def determine_chu_chuan_with_bi_yong(yao_ke_list, ri_gan):
    # 1. 分离上神克日干和日干克上神
    shang_ke_gan = [y for y in yao_ke_list if y['type'] == '克干']
    gan_ke_shang = [y for y in yao_ke_list if y['type'] == '干克']
    
    # 2. 优先处理上神克日干
    if shang_ke_gan:
        candidates = shang_ke_gan
    else:
        candidates = gan_ke_shang
    
    # 3. 只有一个候选，直接取
    if len(candidates) == 1:
        return candidates[0]['shang']
    
    # 4. 多个候选，进行比用
    # 4a. 比较阴阳
    yang_ri = is_yang_ri(ri_gan)
    bi_yong_results = []
    for y in candidates:
        shang = y['shang']
        if yang_ri and is_yang_zhi(shang):
            bi_yong_results.append(shang)
        elif not yang_ri and not is_yang_zhi(shang):
            bi_yong_results.append(shang)
    
    # 4b. 比用后只剩一个
    if len(bi_yong_results) == 1:
        return bi_yong_results[0]
    
    # 4c. 比用后仍有多个，比较先天数
    elif len(bi_yong_results) > 1:
        max_shang = None
        max_num = -1
        for shang in bi_yong_results:
            num = get_xian_tian_num(shang)
            if num > max_num:
                max_num = num
                max_shang = shang
        return max_shang
    
    # 4d. 比用后无符合，取先见者
    else:
        return candidates[0]['shang']
```

### 4. 日干五行
```python
RI_GAN_WU_XING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火', '戊': '土',
    '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}
```

### 5. 中末传起法
- 中传：取初传所乘地盘之神
- 末传：取中传所乘地盘之神

## API 定义

### `is_yao_ke(sike, ri_gan)`
判断是否需要使用遥克法。

**参数**：
- `sike`: 四课列表，每个元素包含 {'shang': 天盘，'xia': 地盘}
- `ri_gan`: 日干

**返回**：
- `bool`: True 表示需要使用遥克法，False 表示不需要

**判断条件**：
1. 四课中无下贼上
2. 四课中无上克下
3. 日干与四课上神之间存在相克关系

### `get_yao_ke_list(sike, ri_gan)`
获取所有遥克关系。

**参数**：
- `sike`: 四课列表
- `ri_gan`: 日干

**返回**：
- `yao_ke_list`: 遥克列表，每个元素包含 {'shang': 上神，'type': '克干'/'干克'}

**逻辑**：
```python
def get_yao_ke_list(sike, ri_gan):
    RI_GAN_WU_XING = {...}
    WU_XING_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    WU_XING_KE_BY = {'木': '金', '金': '火', '火': '水', '水': '土', '土': '木'}
    
    ri_gan_wuxing = RI_GAN_WU_XING[ri_gan]
    yao_ke_list = []
    
    for ke in sike:
        shang = ke['shang']
        shang_wuxing = get_dizhi_wuxing(shang)
        
        # 上神克日干
        if WU_XING_KE.get(shang_wuxing) == ri_gan_wuxing:
            yao_ke_list.append({'shang': shang, 'type': '克干'})
        # 日干克上神
        elif WU_XING_KE.get(ri_gan_wuxing) == shang_wuxing:
            yao_ke_list.append({'shang': shang, 'type': '干克'})
    
    return yao_ke_list
```

### `determine_chu_chuan(yao_ke_list)`
确定遥克法初传。

**参数**：
- `yao_ke_list`: 遥克列表

**返回**：
- `str`: 初传（天盘）

**逻辑**：
```python
def determine_chu_chuan(yao_ke_list):
    # 优先取上神克日干
    for yao_ke in yao_ke_list:
        if yao_ke['type'] == '克干':
            return yao_ke['shang']
    
    # 无上神克日干，取日干克上神
    for yao_ke in yao_ke_list:
        if yao_ke['type'] == '干克':
            return yao_ke['shang']
    
    return None
```

### `determine_zhong_mo_chuan(chu_chuan, tiandi_pan)`
确定遥克法中末传。

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

### `validate(sanchuan, sike, ri_gan)`
验证遥克法结果是否正确。

**参数**：
- `sanchuan`: 三传列表 [初传，中传，末传]
- `sike`: 四课列表
- `ri_gan`: 日干

**返回**：
- `(is_valid, error_msg)`: 验证结果和错误信息

**验证规则**：
1. 初传必须在四课上神中
2. 初传必须与日干存在遥克关系
3. 中传必须是初传下神
4. 末传必须是中传下神

### `auto_correct(sanchuan, sike, ri_gan, tiandi_pan)`
自动修正遥克法错误。

**参数**：
- `sanchuan`: 当前三传
- `sike`: 四课列表
- `ri_gan`: 日干
- `tiandi_pan`: 天地盘

**返回**：
- `corrected_sanchuan`: 修正后的三传

**修正逻辑**：
1. 检查初传是否与日干存在遥克关系
2. 如不符合，重新选取初传
3. 重新计算中末传

## 自我校验机制

### 校验项目
1. **无克贼校验**：四课中确实无下贼上、无上克下
2. **遥克存在**：日干与四课上神存在相克关系
3. **初传来源**：初传是否来自四课上神
4. **遥克关系**：初传是否与日干存在遥克关系
5. **中传来源**：中传是否为初传下神
6. **末传来源**：末传是否为中传下神

### 校验流程
```python
def validate_yao_ke(sanchuan, sike, ri_gan, tiandi_pan):
    errors = []
    
    # 1. 检查四课无克贼
    for ke in sike:
        shang = ke['shang']
        xia = ke['xia']
        if is_xia zei_shang(shang, xia) or is_shang_ke_xia(shang, xia):
            errors.append("四课中存在克贼，不应使用遥克法")
            return False, errors
    
    # 2. 检查初传在四课上神中
    chu_chuan = sanchuan[0]
    if not any(ke['shang'] == chu_chuan for ke in sike):
        errors.append("初传不在四课上神中")
    
    # 3. 检查初传与日干的遥克关系
    ri_gan_wuxing = RI_GAN_WU_XING[ri_gan]
    chu_chuan_wuxing = get_dizhi_wuxing(chu_chuan)
    
    has_yao_ke = (
        WU_XING_KE.get(chu_chuan_wuxing) == ri_gan_wuxing or  # 上神克日干
        WU_XING_KE.get(ri_gan_wuxing) == chu_chuan_wuxing     # 日干克上神
    )
    
    if not has_yao_ke:
        errors.append("初传与日干无遥克关系")
    
    # 4. 检查中传
    zhong_chuan = sanchuan[1]
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == chu_chuan:
            expected_zhong = tiandi_pan[dizhi]
            if zhong_chuan != expected_zhong:
                errors.append(f"中传错误，应为{expected_zhong}，实为{zhong_chuan}")
            break
    
    # 5. 检查末传
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
1. **初传无遥克关系**：重新选取与日干有遥克关系的上神
2. **优先级错误**：应先取上神克日干，再取日干克上神
3. **中末传错误**：重新按"初传下神为中传，中传下神为末传"计算

### 修正流程
```python
def auto_correct_yao_ke(sanchuan, sike, ri_gan, tiandi_pan):
    corrected = sanchuan.copy()
    
    # 修正初传
    ri_gan_wuxing = RI_GAN_WU_XING[ri_gan]
    
    # 优先找上神克日干
    for ke in sike:
        shang = ke['shang']
        shang_wuxing = get_dizhi_wuxing(shang)
        if WU_XING_KE.get(shang_wuxing) == ri_gan_wuxing:
            corrected[0] = shang
            break
    else:
        # 再找日干克上神
        for ke in sike:
            shang = ke['shang']
            shang_wuxing = get_dizhi_wuxing(shang)
            if WU_XING_KE.get(ri_gan_wuxing) == shang_wuxing:
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
# 总起课判断 SKILL 调用遥克法专用 SKILL
from .trae.skills.yao_ke_method import is_yao_ke, get_yao_ke_list, determine_chu_chuan, determine_zhong_mo_chuan

# 课式信息
info = {
    'sike': [
        {'shang': '寅', 'xia': '子'},
        {'shang': '戌', 'xia': '寅'},
        {'shang': '午', 'xia': '戌'},
        {'shang': '申', 'xia': '午'}
    ],
    'ri_gan': '甲',
    'tiandi_pan': {...}
}

# 判断是否需要遥克法
if is_yao_ke(info['sike'], info['ri_gan']):
    # 获取遥克列表
    yao_ke_list = get_yao_ke_list(info['sike'], info['ri_gan'])
    
    # 确定初传
    chu_chuan = determine_chu_chuan(yao_ke_list)
    
    # 确定中末传
    zhong_chuan, mo_chuan = determine_zhong_mo_chuan(chu_chuan, info['tiandi_pan'])
    
    # 验证结果
    sanchuan = [chu_chuan, zhong_chuan, mo_chuan]
    is_valid, errors = validate(sanchuan, info['sike'], info['ri_gan'])
    
    if not is_valid:
        # 自动修正
        sanchuan = auto_correct(sanchuan, info['sike'], info['ri_gan'], info['tiandi_pan'])
```

## 优先级说明

遥克法在九种起课法则中的优先级：
1. 贼克法（有克贼）
2. 比用法（多克贼涉害相同）
3. 涉害法（多克贼涉害不同）
4. **遥克法（无克贼，有遥克）** ← 第 4 优先级
5. 昴星法（无克贼无遥克）
6. 别责法
7. 八专法
8. 伏吟法
9. 反吟法

## 冲突解决

### 与贼克法的冲突
- 有四课克贼 → 使用贼克法（或比用、涉害）
- 无四课克贼，有遥克 → 使用遥克法

### 与昴星法的冲突
- 有遥克 → 使用遥克法
- 无遥克 → 使用昴星法

### 判断流程
```python
def decide_yao_ke_or_other(sike, ri_gan):
    # 1. 检查克贼
    ke_zai = []
    for ke in sike:
        if is_xia_zei_shang(ke['shang'], ke['xia']):
            ke_zai.append(ke)
        elif is_shang_ke_xia(ke['shang'], ke['xia']):
            ke_zai.append(ke)
    
    if len(ke_zai) > 0:
        return '贼克法/比用法/涉害法'  # 有克贼，不用遥克
    
    # 2. 检查遥克
    yao_ke_list = get_yao_ke_list(sike, ri_gan)
    
    if len(yao_ke_list) > 0:
        return '遥克法'  # 有遥克，用遥克
    
    return '昴星法'  # 无克贼无遥克，用昴星
```

## 测试用例

### 测试用例 1：上神克日干
```python
# 甲子日 戌将卯时
# 四课：寅子、戌寅、午戌、申午
# 甲木，申金克甲木
# 取申发用
expected_chu_chuan = '申'
```

### 测试用例 2：日干克上神
```python
# 甲子日 亥将辰时
# 四课：巳子、戌巳、卯戌、申卯
# 甲木，戌土被甲木克
# 取戌发用
expected_chu_chuan = '戌'
```

### 测试用例 3：优先上神克日干
```python
# 甲子日 酉将寅时
# 四课：酉子、未酉、巳未、卯巳
# 甲木，酉金克甲木（优先）
# 甲木克未土（次选）
# 取酉发用
expected_chu_chuan = '酉'
```

## 文件结构
```
.trae/skills/
├── yao-ke-method/
│   └── SKILL.md          # 本文件
├── daliuren-qike-decision/
│   └── SKILL.md          # 总起课判断 SKILL
├── zei-ke-method/
│   └── SKILL.md
├── she-hai-method/
│   └── SKILL.md
├── bi-yong-method/
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
- v1.0 (2026-03-14): 初始版本，包含遥克法核心规则、API 定义、自我校验和错误修正机制
- v2.0 (2026-03-14): 添加多个遥克时的比用规则（有比用比原则）
  - 多个上神克日干时，先比较阴阳，再比较先天数
  - 与涉害法、贼克法的比用规则保持一致
