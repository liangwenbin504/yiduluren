---
name: "she-hai-method"
description: "涉害法专用起课技能，用于比用后仍有多课的情况，计算涉害深度取最深者。Invoke when the decision system identifies 涉害课 (after 比用 still has multiple courses)."
---

# 涉害法专用起课技能

## 核心功能

专门处理**比用后仍有多课**的情况，通过计算涉害深度（包含天干寄宫）确定初传。

## 调用时机

**当总起课判断 SKILL 检测到比用后仍有多课时调用此 SKILL**。

## 重要前置规则：有比用比原则

**关键区分**：处理优先级

### 优先级顺序

当四课中同时存在上克下和下贼上时：
1. **优先处理下贼上**（重审课优先）
2. 下贼上处理完毕后，再处理上克下

### 有比用比原则（通用规则）

**适用于**：多个下贼上 或 多个上克下 的情况

当存在多个克贼（下贼上或上克下）时，遵循以下统一规则：

#### 1. 优先比较阴阳（传统比用）

- 阳日取阳支，阴日取阴支
- 阴阳不同：取符合者
- 阴阳相同：进入下一步

#### 2. 数值相同进入涉害

阴阳相同时，**直接进入涉害法**：
- 计算各候选课的涉害深度
- 取涉害最深者为初传
- 涉害深度也相同时，按孟仲季规则取用

### 完整处理流程

```
四课多克贼 → 区分下贼上 vs 上克下
              ↓
         【优先处理下贼上】
              ↓
    多个下贼上 → 比较阴阳 → 阴阳不同：取符合者
                            → 阴阳相同：用涉害法
              ↓
         【再处理上克下】（如果下贼上无结果）
              ↓
    多个上克下 → 比较阴阳 → 阴阳不同：取符合者
                            → 阴阳相同：用涉害法
```

### 规则总结

```
【通用规则：有比用比】
多课（下贼上或上克下）→ 比较阴阳 → 阴阳不同：取符合者
                                      → 阴阳相同：用涉害法

【优先级】
1. 下贼上（重审课）优先
2. 上克下（元首课）次之
```

**重要说明**：
- "有比用比"原则**通用**于下贼上和上克下
- 唯一的区别是**处理优先级**：下贼上 > 上克下
- 涉害法在"阴阳相同"的情况下使用

## 涉害深度计算规则

### 路径规则

- **起点**：天盘加临位（天盘落地盘位置）- **计入**
- **终点**：天盘本身位 - **不计**
- **方向**：顺时针
- **统计范围**：只计"我克者"（上神克地盘），"克我者"不计

### 克位统计

**核心规则**：统计上神所克的五行，包含地支本气和天干寄宫

**大六壬天干寄宫规则**：
- 甲寄寅，乙寄辰，丙戊寄巳，丁己寄未，庚寄申，辛寄戌，壬寄亥，癸寄丑
- **注意**：戌中只寄辛金，不寄戊土；丑中只寄癸水，不寄己土

```python
# 天干寄宫（只计寄宫天干，不计地支本气）
gan_ji_gong_wuxing_all = {
    '寅': ['木'],  # 甲
    '辰': ['木'],  # 乙
    '巳': ['火', '土'],  # 丙、戊
    '未': ['火', '土'],  # 丁、己
    '申': ['金'],  # 庚
    '戌': ['金'],  # 辛（戌中只寄辛金）
    '亥': ['水'],  # 壬
    '丑': ['水'],  # 癸（丑中只寄癸水）
}

def calculate_she_hai_depth(shang, tiandi_pan):
    """
    计算涉害深度（包含天干寄宫，只计"我克者"）
    
    核心规则：
    - 起点计入，终点不计
    - 只计"我克者"（上神克地盘）
    - 地支本气和天干寄宫分别计数
    - 比和者不计
    """
    # 1. 找到天盘加临位（起点）
    start_pos = None
    for dizhi, tianpan in tiandi_pan.items():
        if tianpan == shang:
            start_pos = dizhi
            break
    
    # 2. 确定终点（不计）
    end_pos = shang
    
    # 3. 顺行计数
    depth = 0
    dizhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    start_idx = dizhi_list.index(start_pos)
    shang_wuxing = DIZHI_WU_XING.get(shang, '')
    
    count = 0
    while True:
        current_zhi = dizhi_list[(start_idx + count) % 12]
        
        # 到达终点（不计）
        if current_zhi == end_pos and count > 0:
            break
        
        current_wuxing = DIZHI_WU_XING.get(current_zhi, '')
        
        # 统计该位置所有被上神所克的五行
        ke_count = 0
        
        # a) 地支本气的克（我克者）
        if WU_XING_KE.get(shang_wuxing) == current_wuxing:
            ke_count += 1
        
        # b) 天干寄宫的克（我克者）
        if current_zhi in gan_ji_gong_wuxing_all:
            for ji_gong_wuxing in gan_ji_gong_wuxing_all[current_zhi]:
                if WU_XING_KE.get(shang_wuxing) == ji_gong_wuxing:
                    ke_count += 1
        
        depth += ke_count
        count += 1
        
        if count > 12:
            break
    
    return depth
```

## 处理流程

### 第一步：计算所有候选课的涉害深度

```python
def calculate_all_depths(candidates, tiandi_pan):
    """计算所有候选课的涉害深度"""
    depths = {}
    
    for ke in candidates:
        shang = ke['shang']
        depth = calculate_she_hai_depth(shang, tiandi_pan)
        depths[shang] = {
            'depth': depth,
            'ke_ci': ke['ke_ci'],
            'xia': ke['xia']
        }
    
    return depths
```

### 第二步：比较涉害深度

```python
def compare_depths(depths, candidates):
    """比较涉害深度，取最深者"""
    
    max_depth = max(d['depth'] for d in depths.values())
    deepest = [(shang, depths[shang]['ke_ci'], depths[shang]['xia']) for shang, d in depths.items() if d['depth'] == max_depth]
    
    # 只有一个最深者
    if len(deepest) == 1:
        return deepest[0], 'single', max_depth
    
    # 多个最深者（涉害深度相同）
    else:
        return deepest, 'equal_depth', max_depth
```

### 第三步：处理涉害深度相同（孟仲季规则）

**核心规则**：涉害深浅相等，则取孟上神发用，谓之见机格；如无孟，则取仲发用，谓之察微格；如俱在孟上，或在仲季，则刚日取日上神（一、二课），阴日取支上神（三、四课）发用，谓之缀瑕格。

```python
def handle_equal_depth(deepest, ri_gan):
    """
    处理涉害深度相同的情况（孟仲季规则）
    
    孟仲季分类：
    - 孟：寅申巳亥
    - 仲：子午卯酉
    - 季：辰戌丑未
    
    取用顺序：
    1. 优先取孟上神发用（见机格）
    2. 无孟，取仲发用（察微格）
    3. 俱在孟上或在仲季，刚日取日上神（一、二课），阴日取支上神（三、四课）发用（缀瑕格）
    """
    meng = ['寅', '申', '巳', '亥']
    zhong = ['子', '午', '卯', '酉']
    ji = ['辰', '戌', '丑', '未']
    
    # 检查各候选的下神（地盘）是孟仲季
    meng_candidates = [c for c in deepest if c[2] in meng]  # c[2] 是下神
    zhong_candidates = [c for c in deepest if c[2] in zhong]
    ji_candidates = [c for c in deepest if c[2] in ji]
    
    # 优先取孟上神发用（见机格）
    if meng_candidates:
        chu_chuan = meng_candidates[0][0]  # c[0] 是上神，取先见者
        ke_ti = '见机格'
    # 无孟，取仲发用（察微格）
    elif zhong_candidates:
        chu_chuan = zhong_candidates[0][0]  # 取先见者
        ke_ti = '察微格'
    # 俱在季，或俱在仲季，按日干阴阳取（缀瑕格）
    else:
        # 按日干阴阳取
        if ri_gan in ['甲', '丙', '戊', '庚', '壬']:  # 阳日
            # 取一、二课（日上神）
            ri_shang_candidates = [c for c in deepest if c[1] in [1, 2]]  # c[1] 是课次
            if ri_shang_candidates:
                chu_chuan = ri_shang_candidates[0][0]
            else:
                chu_chuan = deepest[0][0]
        else:  # 阴日
            # 取三、四课（支上神）
            zhi_shang_candidates = [c for c in deepest if c[1] in [3, 4]]
            if zhi_shang_candidates:
                chu_chuan = zhi_shang_candidates[0][0]
            else:
                chu_chuan = deepest[0][0]
        ke_ti = '缀瑕格'
    
    return chu_chuan, ke_ti
```

## 输出格式

```python
{
    '课体': '涉害课' or '见机格' or '察微格' or '缀瑕格',
    '起法': '涉害法',
    '初传': '初传地支',
    '中传': '中传地支',
    '末传': '末传地支',
    '涉害深度': depth,
    '候选课涉害深度': {
        '申': {'depth': 2, 'ke_ci': '第 1 课', 'xia': '申'},
        '酉': {'depth': 3, 'ke_ci': '第 3 课', 'xia': '酉'}
    }
}
```

## 自我校验

### 校验规则

```python
def validate(result, info):
    """校验涉害法结果"""
    
    # 1. 检查课体
    if result['课体'] not in ['涉害课', '见机格', '察微格', '缀瑕格']:
        return False, '课体错误'
    
    # 2. 检查起法
    if result['起法'] != '涉害法':
        return False, '起法错误'
    
    # 3. 检查初传是否来自候选课
    if result['初传'] not in [ke['shang'] for ke in info['candidates']]:
        return False, '初传不是来自候选课'
    
    # 4. 检查涉害深度计算
    depths = calculate_all_depths(info['candidates'], info['tiandi_pan'])
    max_depth = max(d['depth'] for d in depths.values())
    
    # 如果只有一个最深者，检查是否取最深者
    deepest_count = sum(1 for d in depths.values() if d['depth'] == max_depth)
    if deepest_count == 1:
        if depths[result['初传']]['depth'] != max_depth:
            return False, '初传不是涉害最深者'
    else:
        # 涉害深度相同，检查是否按孟仲季规则取
        # 这里需要实现孟仲季规则的校验逻辑
        pass
    
    return True, '校验通过'
```

## 中末传起法

```python
def get_zhong_mo_chuan(chu_chuan, tiandi_pan):
    """获取中末传"""
    
    # 中传：取初传的上神
    zhong_chuan = tiandi_pan[chu_chuan]
    
    # 末传：取中传的上神
    mo_chuan = tiandi_pan[zhong_chuan]
    
    return zhong_chuan, mo_chuan
```

## 使用示例

### 示例 1：己巳日酉将巳时（上克下案例）

```python
info = {
    'ri_gan': '己',
    'ri_zhi': '巳',
    'candidates': [
        {'ke_ci': '第 1 课', 'shang': '亥', 'xia': '己'},
        {'ke_ci': '第 3 课', 'shang': '酉', 'xia': '巳'}
    ],
    'tiandi_pan': {...}
}

depths = calculate_all_depths(info['candidates'], info['tiandi_pan'])
# 亥涉害深度：2
# 酉涉害深度：3

result = execute(info)
# 结果：
# {
#     '课体': '涉害课',
#     '起法': '涉害法',
#     '初传': '酉',  # 涉害更深
#     '中传': '丑',
#     '末传': '巳',
#     '涉害深度': 3
# }
```

**说明**：此案例为上克下，阴阳比用后仍有 2 课，直接使用涉害法。

### 示例 2：辛未日巳将戌时（用户验证案例，上克下）

```python
# 四课：
# 第一课：上巳 下辛 [克]
# 第二课：上子 下巳 [克]
# 第三课：上寅 下未 [克]
# 第四课：上酉 下寅 [克]

# 涉害深度计算（包含终点位置）：
# 巳（火）从戌位到巳位：戌→亥→子→丑→寅→卯→辰→巳
#   - 戌（辛金寄宫）：火克金 ✓ (1 个)
#   - 其他位置无金
#   - 终点巳位：巳火（比和，不计），丙火戊土寄宫（比和/相生，不计）
#   - 涉害深度：1

# 酉（金）从寅位到酉位：寅→卯→辰→巳→午→未→申→酉
#   - 寅（甲木寄宫 + 寅木）：金克木 ✓ (2 个)
#   - 卯（卯木）：金克木 ✓ (1 个)
#   - 辰（乙木寄宫）：金克木 ✓ (1 个)
#   - 其他位置无木
#   - 终点酉位：酉金（比和，不计），庚金寄宫（比和，不计）
#   - 涉害深度：4

# 结果：取酉为初传（涉害深度 4 > 1）
result = {
    '课体': '见机格',
    '起法': '涉害法',
    '初传': '酉',
    '中传': '辰',
    '末传': '亥',
    '涉害深度': 4
}
```

**说明**：此案例为上克下，辛日（阴日）取阴支（巳、酉），阴阳比用后仍有 2 课，直接使用涉害法。

### 示例 3：假想案例（下贼上，有比用比）

```python
# 假设案例：甲日，四课中有两个下贼上
# 第一课：上寅 下甲 [贼]
# 第三课：上申 下某 [贼]
# 甲日（阳日），寅（阳支）、申（阳支）都符合

# 比较先天数：
# 寅先天数 = 3
# 申先天数 = 9
# 申 > 寅

# 结果：直接取申为初传（数值大者），不使用涉害法
result = {
    '课体': '重审课',
    '起法': '贼克法（下贼上，比用数值）',
    '初传': '申',
    '中传': '...',
    '末传': '...'
}
```

**说明**：此案例为下贼上，阴阳比用后仍有 2 课（都是阳支），比较先天数后，申（9）> 寅（3），直接取申，不使用涉害法。这体现了"有比用比"原则。

## 版本信息

- **版本**：v8.0（修正涉害法流程）
- **更新日期**：2026-03-14
- **依赖**：daliuren-qike-decision
- **修正说明**：
  - v2.0：涉害深度统计"我克者"（上神克地盘）← 错误
  - v3.0：添加"有比用比"前置规则说明
  - v3.1：明确区分上克下和下贼上的不同处理规则
  - v3.2：统一上克下与下贼上规则（仅优先级不同）
  - v4.0：修正为统计"克我者"（地盘克上神）← 仍不完整
  - v5.0：统一统计"上克下"和"下贼上" ← 不正确
  - v6.0：添加孟仲季规则 ← 正确
  - v7.0：修正涉害深度计算规则 ← 最新
    - **起点计入，终点不计**
    - **只计"我克者"（上神克地盘），"克我者"不计**
    - **大六壬天干寄宫规则**：
      - 甲寄寅，乙寄辰，丙戊寄巳，丁己寄未，庚寄申，辛寄戌，壬寄亥，癸寄丑
      - **戌中只寄辛金，不寄戊土**
      - **丑中只寄癸水，不寄己土**
    - **涉害深度计算示例**：
      - 卯（木）从未位到卯位（不含）：未（2）+ 戌（1）+ 丑（1）= 4
        - 未：未土✓ + 己土✓ = 2
        - 戌：戌土✓ = 1
        - 丑：丑土✓ = 1
      - 未（土）从亥位到未位（不含）：亥（2）+ 子（2）= 4
        - 亥：亥水✓ + 壬水✓ = 2
        - 子：子水✓ + 癸水✓ = 2
  - **v8.0：修正涉害法流程** ← 最新
    - **涉害法在"阴阳相同"时使用，不再比较数值大小**
    - **比用后，阴阳不同取符合者，阴阳相同直接用涉害法**
