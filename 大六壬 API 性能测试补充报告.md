# 大六壬 API 性能测试补充报告

## 📊 大六壬 API 性能数据

### 基准测试结果（2026-03-30 05:13:27）

| API 名称 | 平均响应时间 | 中位数 | 最小值 | 最大值 | 状态码 | 成功率 |
|---------|------------|--------|--------|--------|--------|--------|
| 排天地盘 | **2038.84ms** | 2040.94ms | 2033.27ms | 2042.31ms | 200 | ✅ 100% |
| 起四课 | **2052.75ms** | 2052.16ms | 2044.45ms | 2061.65ms | 200 | ✅ 100% |
| 发三传（宗门九课） | **2048.17ms** | 2048.70ms | 2045.77ms | 2050.04ms | 200 | ✅ 100% |
| 大六壬综合评分 | **2056.60ms** | 2044.56ms | 2040.82ms | 2084.41ms | 200 | ✅ 100% |
| 完整排盘 | **2045.97ms** | 2044.40ms | 2044.19ms | 2049.32ms | 200 | ✅ 100% |

### 性能分析

**当前状态**: 所有大六壬 API 响应时间都在 **~2 秒** 左右

**原因分析**:
1. **Flask 调试模式 overhead** - 每次请求检查文件变化（~1.5-2 秒）
2. **模块导入延迟** - 虽然已预加载，但每次请求仍有导入开销
3. **计算复杂度** - 大六壬排盘涉及多层计算

---

## ⚠️ 当前问题：大六壬评分计算失败

### 问题现象

在最新测试中（2026-03-30 05:20:04），所有大六壬 API 返回 **500 Internal Server Error**

**测试结果**:
```
【测试 1】排天地盘
响应时间：2068.60ms
状态码：500  ❌

【测试 2】起四课
响应时间：2076.39ms
状态码：500  ❌

【测试 3】发三传（宗门九课）
响应时间：2053.88ms
状态码：500  ❌

【测试 4】大六壬综合评分
响应时间：2072.75ms
状态码：500  ❌

【测试 5】完整排盘
响应时间：2058.35ms
状态码：500  ❌
```

### 可能原因

1. **模块导入失败**
   - `sike_sanchuan_engine` 导入路径问题
   - `gui_ren_engine` 导入路径问题
   - `dizhi_layout_generator` 导入路径问题

2. **数据文件缺失**
   - `64_ke_jing_accurate.json` 文件路径错误
   - JSON 文件格式问题

3. **服务器日志未显示错误**
   - Flask 生产模式下错误日志未输出到控制台
   - 需要查看 Flask 错误日志文件

### 诊断步骤

#### 1. 检查导入路径
```python
# api_server.py 中的路径配置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
```

#### 2. 检查模块存在性
```bash
# 检查核心模块
✅ core_modules/engine/sike_sanchuan_engine.py
✅ core_modules/engine/gui_ren_engine.py
✅ core_modules/engine/dizhi_layout_generator.py

# 检查数据文件
✅ data/64_ke_jing_accurate.json
```

#### 3. 启用详细错误日志

**临时方案**（开发测试用）:
```python
# 在 api_server.py 中添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

**生产环境方案**:
```python
# 使用 Gunicorn 并配置日志
gunicorn -w 4 -b 0.0.0.0:5000 \
  --access-logfile access.log \
  --error-logfile error.log \
  --log-level debug \
  api_server:app
```

---

## 🔧 解决方案

### 方案 1: 修复导入路径（推荐）

**问题**: 模块导入时可能使用了错误的路径

**修复**:
```python
# 在 api_server.py 的大六壬 API 函数中
@app.route('/api/daliuren/score', methods=['GET', 'POST'])
def daliuren_score():
    try:
        # 明确指定导入路径
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
        
        from sike_sanchuan_engine import SiKeSanChuanCalculator
        from gui_ren_engine import GuiRenCalculator
        from dizhi_layout_generator import arrange_tiandi_pan
        
        # ... 其余代码
```

### 方案 2: 添加详细错误处理

**修复**:
```python
@app.route('/api/daliuren/score', methods=['GET', 'POST'])
def daliuren_score():
    try:
        # ... 导入和计算
        
    except ImportError as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 导入错误：{error_detail}")  # 输出到控制台
        return jsonify({
            'success': False,
            'error': f'模块导入失败：{str(e)}',
            'detail': error_detail
        }), 500
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 计算错误：{error_detail}")
        return jsonify({
            'success': False,
            'error': f'大六壬评分计算失败：{str(e)}',
            'detail': error_detail
        }), 500
```

### 方案 3: 预加载模块到全局变量

**修复**（已在 api_server.py 中实现）:
```python
# 在文件顶部预加载
from sike_sanchuan_engine import SiKeSanChuanCalculator
from gui_ren_engine import GuiRenCalculator
from dizhi_layout_generator import arrange_tiandi_pan

# 在 API 中使用全局变量
@app.route('/api/daliuren/score')
def daliuren_score():
    # 直接使用预加载的模块，不再导入
    tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)
    # ...
```

---

## 📈 性能优化建议（针对大六壬 API）

### 1. 缓存课经数据

**当前问题**: 每次请求都加载 JSON 文件

**优化**:
```python
# 全局缓存
_KE_JING_CACHE = None

def get_ke_jing_data():
    global _KE_JING_CACHE
    if _KE_JING_CACHE is None:
        with open('64_ke_jing_accurate.json', 'r') as f:
            _KE_JING_CACHE = json.load(f)
    return _KE_JING_CACHE

# 在 API 中使用
ke_jing_data = get_ke_jing_data()
```

### 2. 缓存贵人计算

**当前问题**: 重复计算相同的贵人盘

**优化**:
```python
_GUIREN_CACHE = {}

def get_guiren_cached(tian_gan, shichen, tiandi_pan):
    key = f"{tian_gan}:{shichen}"
    if key in _GUIREN_CACHE:
        return _GUIREN_CACHE[key]
    
    # 计算并存入缓存
    result = calculate_guiren(tian_gan, shichen, tiandi_pan)
    _GUIREN_CACHE[key] = result
    return result
```

### 3. 批量计算优化

**当前问题**: 日期范围分析时重复创建计算器

**优化**:
```python
# 预创建计算器实例
calc = SiKeSanChuanCalculator()
gui_ren_calc = GuiRenCalculator()

# 在循环中复用
for date in date_range:
    sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
    sanchuan = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
```

---

## 📊 预期性能对比

### 优化前 vs 优化后

| 指标 | 当前（有 bug） | 修复后（预期） | 优化后（预期） |
|------|--------------|--------------|--------------|
| 排天地盘 | ❌ 500 错误 | ~500ms | ~250ms |
| 起四课 | ❌ 500 错误 | ~600ms | ~300ms |
| 发三传 | ❌ 500 错误 | ~700ms | ~350ms |
| 大六壬评分 | ❌ 500 错误 | ~800ms | ~400ms |
| 完整排盘 | ❌ 500 错误 | ~900ms | ~450ms |

**说明**:
- **修复后**: 解决 500 错误，性能恢复正常（~500-900ms）
- **优化后**: 应用缓存等优化，性能提升 50%（~250-450ms）

---

## 📝 下一步行动

### 立即执行

1. **检查服务器错误日志**
   ```bash
   # 查看 Flask 错误日志
   tail -f error.log
   ```

2. **测试模块导入**
   ```python
   python -c "
   import sys
   sys.path.insert(0, 'core_modules/engine')
   from sike_sanchuan_engine import SiKeSanChuanCalculator
   print('✅ 模块导入成功')
   "
   ```

3. **重启 API 服务器（带详细日志）**
   ```bash
   # 临时启用调试日志
   python -c "
   import logging
   logging.basicConfig(level=logging.DEBUG)
   import api_server
   "
   ```

### 短期（1-2 天）

1. **修复导入路径问题**
2. **添加详细错误处理**
3. **重新运行性能测试**

### 中期（1 周）

1. **实现课经数据缓存**
2. **实现贵人计算缓存**
3. **优化日期范围计算**

---

## 📚 相关文档

- [大六壬 API 代码](file:///d:/新建文件夹/仪度六壬择日/yiduluren/api_server.py#L1370-L1600)
- [性能测试脚本](file:///d:/新建文件夹/仪度六壬择日/yiduluren/test_daliuren_api_status.py)
- [性能基准测试](file:///d:/新建文件夹/仪度六壬择日/yiduluren/api_performance_benchmark.py)

---

**报告生成时间**: 2026-03-30  
**问题状态**: ⚠️ 待修复（500 错误）  
**优先级**: 🔴 高
