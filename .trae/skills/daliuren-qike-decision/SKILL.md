---
name: "daliuren-qike-decision"
description: "大六壬总起课判断系统，综合分析九种课式特征，准确判断应起哪一课。Invoke when user needs to determine which of the nine 课式 methods to use for divination."
---

# 大六壬总起课判断系统

## 核心功能

本 SKILL 是大六壬起课的**最终决策系统**，负责：
1. 综合分析四课、天地盘、克贼、遥克等所有因素
2. 调用九课专用起课法 SKILL 进行专业判断
3. 处理冲突和边界情况
4. 做出准确的起课决策

## 调用时机

**当用户需要确定使用哪种起课法则时调用此 SKILL**，包括：
- 用户要求起课但不确定用哪种方法
- 需要验证课式类型
- 多课特征冲突时需要决策
- 复杂课式的综合判断

## 九种起课法则优先级

```
1. 贼克法（有克贼先用）         ← 最高优先级
2. 比用法（多课克贼取比用）
3. 涉害法（比用后仍多课）
4. 遥克法（无克贼有遥克）
5. 昴星法（无克贼无遥克，普通四课）
6. 八专法（日干寄宫=日支，干支同位）  ← 修正：优先于别责
7. 别责法（四课有两课相同）
8. 伏吟法（月将=占时）
9. 反吟法（月将冲占时）         ← 最低优先级
```

**重要修正**：
- **八专课优先于别责课**：八专课是日干支的特殊组合（干支同位），优先级高于四课结构的别责课
- **遥克法比用规则**：遥克法也有比用，比用后仍多课时用涉害法

## 判断流程

### 第一步：基础信息收集

```python
def collect_info(ri_gan, ri_zhi, yue_jiang, shi_chen, tiandi_pan, sike):
    """收集所有判断所需信息"""
    info = {
        'ri_gan': ri_gan,
        'ri_zhi': ri_zhi,
        'yue_jiang': yue_jiang,
        'shi_chen': shi_chen,
        'tiandi_pan': tiandi_pan,
        'sike': sike,
        'ke_zai': [],  # 克贼课
        'yao_ke': [],  # 遥克课
        'is_fu_yin': False,  # 是否伏吟
        'is_fan_yin': False,  # 是否反吟
        'is_bie_ze': False,  # 是否别责
        'is_ba_zhuan': False,  # 是否八专
    }
    
    # 检查克贼
    for ke in sike:
        ke_type = is_ke(ke['shang'], ke['xia'])
        if ke_type:
            info['ke_zai'].append({
                'ke_ci': ke['ci'],
                'type': ke_type,
                'shang': ke['shang'],
                'xia': ke['xia']
            })
    
    # 检查遥克
    info['yao_ke'] = check_yao_ke(ri_gan, sike)
    
    # 检查特殊课体
    info['is_fu_yin'] = (yue_jiang == shi_chen)
    info['is_fan_yin'] = is_chong(yue_jiang, shi_chen)
    info['is_bie_ze'] = check_bie_ze(sike, ri_gan)
    info['is_ba_zhuan'] = (len(sike) < 4)
    
    return info
```

### 第二步：优先级判断

```python
def decide_method(info):
    """根据优先级判断应使用哪种起课法"""
    
    # 1. 检查克贼（最高优先级）
    if len(info['ke_zai']) > 0:
        # 2. 检查是否多课克贼（需要比用）
        if len(info['ke_zai']) > 1:
            # 3. 检查比用后是否仍多课（需要涉害）
            bi_yong_ke = check_bi_yong(info['ke_zai'], info['ri_gan'])
            if len(bi_yong_ke) > 1:
                return '涉害法'
            else:
                return '比用法'
        else:
            return '贼克法'
    
    # 4. 检查遥克
    if len(info['yao_ke']) > 0:
        # 遥克法也有比用
        if len(info['yao_ke']) > 1:
            # 比用后仍多课，用涉害法
            bi_yong_yao_ke = check_bi_yong(info['yao_ke'], info['ri_gan'])
            if len(bi_yong_yao_ke) > 1:
                return '涉害法'
            else:
                return '遥克法（比用）'
        else:
            return '遥克法'
    
    # 5. 检查特殊课体（八专优先于别责）
    if info['is_ba_zhuan']:
        # 八专课：日干寄宫=日支（干支同位）
        return '八专法'
    
    if info['is_bie_ze']:
        # 别责课：四课有两课相同
        return '别责法'
    
    if info['is_fu_yin']:
        return '伏吟法'
    
    if info['is_fan_yin']:
        return '反吟法'
    
    # 6. 普通课式（昴星法）
    return '昴星法'
```

### 第三步：调用专用 SKILL

```python
def execute_method(method_name, info):
    """调用对应的专用起课法 SKILL"""
    
    skill_map = {
        '贼克法': 'zei-ke-method',
        '比用法': 'bi-yong-method',
        '涉害法': 'she-hai-method',
        '遥克法': 'yao-ke-method',
        '昴星法': 'ao-xing-method',
        '别责法': 'bie-ze-method',
        '八专法': 'ba-zhuan-method',
        '伏吟法': 'fu-yin-method',
        '反吟法': 'fan-yin-method'
    }
    
    skill_name = skill_map[method_name]
    
    # 调用专用 SKILL
    result = call_skill(skill_name, info)
    
    # 自我校验
    if not validate_result(result, method_name):
        # 校验失败，尝试修正
        result = auto_correct(result, info, method_name)
    
    return result
```

## 自我校验机制

### 校验规则

```python
def validate_result(result, method_name):
    """校验起课结果是否正确"""
    
    # 1. 检查三传是否存在
    if not result or 'chu_chuan' not in result:
        return False
    
    # 2. 检查课体是否匹配
    if result.get('课体') != method_name.replace('法', '课'):
        return False
    
    # 3. 检查起法是否匹配
    if result.get('起法') != method_name:
        return False
    
    # 4. 特殊校验规则
    if method_name == '贼克法':
        return validate_zai_ke(result)
    elif method_name == '涉害法':
        return validate_she_hai(result)
    elif method_name == '别责法':
        return validate_bie_ze(result)
    # ... 其他校验
    
    return True
```

### 自动修正

```python
def auto_correct(result, info, method_name):
    """自动修正错误的起课结果"""
    
    error_type = identify_error(result, info)
    
    if error_type == 'wrong_method':
        # 用错方法，重新判断
        return decide_and_execute(info)
    elif error_type == 'calculation_error':
        # 计算错误，重新计算
        return recalculate(method_name, info)
    elif error_type == 'missing_data':
        # 数据缺失，补充数据
        return fill_missing_and_execute(result, info, method_name)
    
    # 无法修正，返回原结果并标记警告
    result['warning'] = '校验失败，请人工复核'
    return result
```

## 冲突解决机制

### 优先级冲突

当多个课式特征同时存在时，严格按照优先级顺序：

```
贼克法 > 比用法 > 涉害法 > 遥克法 > 昴星法 > 别责法 > 八专法 > 伏吟法 > 反吟法
```

**示例**：
- 既有克贼又有遥克 → 用贼克法
- 既有伏吟又有别责 → 用别责法（伏吟优先级最低）

### 边界情况处理

```python
def handle_edge_cases(info):
    """处理边界情况"""
    
    # 1. 克贼和遥克同时存在
    if info['ke_zai'] and info['yao_ke']:
        # 优先用克贼
        info['use_yao_ke'] = False
    
    # 2. 伏吟和反吟同时存在（理论上不可能）
    if info['is_fu_yin'] and info['is_fan_yin']:
        # 标记为异常
        raise Exception('伏吟和反吟不能同时存在')
    
    # 3. 八专和别责同时存在（八专优先）
    if info['is_ba_zhuan'] and info['is_bie_ze']:
        # 八专课是日干支的特殊组合，优先级高于别责
        info['use_bie_ze'] = False
        info['use_ba_zhuan'] = True
    
    # 4. 遥克法多课（需要比用）
    if len(info['yao_ke']) > 1:
        # 比用后仍多课，用涉害法
        bi_yong_yao_ke = check_bi_yong(info['yao_ke'], info['ri_gan'])
        if len(bi_yong_yao_ke) > 1:
            info['use_she_hai'] = True
    
    return info
```

## 错误处理

### 错误类型

```python
ERROR_TYPES = {
    'NO_KE_ZAI': '无克贼',
    'NO_YAO_KE': '无遥克',
    'INVALID_SI_KE': '四课无效',
    'INVALID_TIANDI_PAN': '天地盘无效',
    'METHOD_CONFLICT': '方法冲突',
    'CALCULATION_ERROR': '计算错误',
    'UNKNOWN_ERROR': '未知错误'
}
```

### 错误恢复

```python
def handle_error(error_type, info):
    """错误恢复策略"""
    
    if error_type == 'NO_KE_ZAI':
        # 无克贼，降级到遥克法
        return decide_method({**info, 'ke_zai': []})
    elif error_type == 'INVALID_SI_KE':
        # 四课无效，重新起四课
        info['sike'] = qi_si_ke(info['ri_gan'], info['ri_zhi'], info['tiandi_pan'])
        return decide_method(info)
    # ... 其他错误处理
    
    # 无法恢复，返回默认值
    return {'error': error_type, 'default_method': '昴星法'}
```

## 使用示例

### 示例 1：贼克课

```python
info = collect_info(ri_gan='甲', ri_zhi='子', yue_jiang='午', shi_chen='子', ...)
# 检测到克贼：第 2 课（贼）、第 3 课（贼）、第 4 课（克）
method = decide_method(info)
# 结果：'贼克法'
result = execute_method(method, info)
# 结果：{'课体': '贼克课', '起法': '贼克法', '初传': '申', ...}
```

### 示例 2：涉害课

```python
info = collect_info(ri_gan='丁', ri_zhi='卯', yue_jiang='丑', shi_chen='子', ...)
# 检测到多个下贼上，比用后仍多课
method = decide_method(info)
# 结果：'涉害法'
result = execute_method(method, info)
# 结果：{'课体': '涉害课', '起法': '涉害法', '初传': '酉', ...}
```

### 示例 3：别责课

```python
info = collect_info(ri_gan='戊', ri_zhi='辰', yue_jiang='巳', shi_chen='辰', ...)
# 检测到第一课=第四课（转换日干后）
method = decide_method(info)
# 结果：'别责法'
result = execute_method(method, info)
# 结果：{'课体': '别责课', '起法': '别责法', '初传': '寅', '中传': '午', '末传': '午'}
```

## 性能优化

### 缓存机制

```python
# 缓存已计算的课式
cache = {}

def get_cached_result(key):
    """从缓存获取结果"""
    return cache.get(key)

def set_cache(key, result):
    """缓存结果"""
    cache[key] = result
```

### 并行计算

```python
# 并行检查多个条件
def parallel_check(info):
    """并行检查克贼、遥克、特殊课体"""
    with ThreadPoolExecutor() as executor:
        future_ke_zai = executor.submit(check_ke_zai, info['sike'])
        future_yao_ke = executor.submit(check_yao_ke, info['ri_gan'], info['sike'])
        future_special = executor.submit(check_special, info)
        
        info['ke_zai'] = future_ke_zai.result()
        info['yao_ke'] = future_yao_ke.result()
        info.update(future_special.result())
    
    return info
```

## 质量保证

### 测试覆盖率

所有核心函数必须有单元测试：

```python
def test_decide_method():
    """测试判断逻辑"""
    # 测试贼克法
    assert decide_method({'ke_zai': [1]}) == '贼克法'
    # 测试比用法
    assert decide_method({'ke_zai': [1, 2]}) == '比用法'
    # 测试涉害法
    assert decide_method({'ke_zai': [1, 2, 3], 'bi_yong': [1, 2]}) == '涉害法'
    # ... 更多测试
```

### 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('daliuren_decision')

def decide_method(info):
    logger.info(f"开始判断课式：{info['ri_gan']}{info['ri_zhi']}日")
    # ... 判断逻辑
    logger.info(f"判断结果：{method}")
    return method
```

## 版本信息

- **当前版本**：v2.0（修正八专优先、遥克比用）
- **更新日期**：2026-03-14
- **维护者**：大六壬起课系统
- **修正说明**：
  - v1.0：初始版本
  - **v2.0：重要修正**
    - **八专课优先于别责课**：八专课是日干支的特殊组合（干支同位），优先级高于四课结构的别责课
    - **遥克法比用规则**：遥克法也有比用，比用后仍多课时用涉害法（不再比较数值大小）
    - **判断流程修正**：先判断八专，再判断别责

## 相关文件

- **核心引擎**：`src/engine/sike_sanchuan_engine.py`
- **九课专用 SKILL**：`.trae/skills/<课式名>-method/`
- **测试文件**：`test_qike_decision.py`
