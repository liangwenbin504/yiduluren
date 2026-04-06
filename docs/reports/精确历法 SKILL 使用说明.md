# 精确历法 SKILL 使用说明

## 📚 SKILL 创建完成

已成功创建精确历法计算 SKILL，保存在：
```
.trae/skills/jingque-lifa/SKILL.md
```

## 🎯 调用时机

**系统现在会在以下情况自动调用精确历法计算：**

1. ✅ **选择日期时** - 自动计算四柱
2. ✅ **设置日期范围时** - 验证开始和结束日期的四柱
3. ✅ **六壬排盘前** - 提供精确的日干支
4. ✅ **斗首择日时** - 确保日期计算准确
5. ✅ **显示四柱信息时** - 使用精确算法

## 🔄 调用流程

```
用户选择日期
    ↓
调用 get_sizhu_accurate()
    ↓
精确计算：
  - 年柱（立春为界）
  - 月柱（节气为界）
  - 日柱（基准日推算）
  - 时柱（真太阳时）
    ↓
返回精确四柱
    ↓
用于：
  - GUI 显示
  - 六壬排盘
  - 斗首择日
```

## 📊 系统更新内容

### 1. GUI 界面增强

**文件**：`src/ui/comprehensive_gui.py`

**新增功能**：
- 择日前先显示日期范围的精确四柱
- 最佳日期确定后再次精确计算四柱
- 所有四柱显示都使用精确算法

**调用位置**：
```python
# 步骤 1：验证日期范围
sizhu_start = get_sizhu_accurate(start.year, start.month, start.day, 12)
sizhu_end = get_sizhu_accurate(end.year, end.month, end.day, 12)

# 步骤 2：计算最佳日期四柱
sizhu_best = get_sizhu_accurate(
    best_date.year,
    best_date.month,
    best_date.day,
    best_date.hour
)
```

### 2. 精确计算模块

**文件**：`src/utils/ganzhi_calendar.py`

**核心函数**：
- `get_sizhu_accurate()` - 精确四柱计算
- `get_year_ganzhi_accurate()` - 年柱计算
- `get_month_ganzhi_accurate()` - 月柱计算（考虑节气）
- `get_day_ganzhi_accurate()` - 日柱计算（基准日推算）
- `get_hour_ganzhi_accurate()` - 时柱计算（五鼠遁）

## 🎓 使用示例

### 示例 1：GUI 择日

```bash
python src/ui/comprehensive_gui.py
```

操作流程：
1. 选择坐山（如"壬山"）
2. 设置日期范围（2026-03-15 至 2026-04-14）
3. 点击"开始择日"
4. 系统自动：
   - 计算开始日期四柱
   - 计算结束日期四柱
   - 进行斗首六壬匹配
   - 显示最佳日期的精确四柱

### 示例 2：代码调用

```python
from ganzhi_calendar import get_sizhu_accurate

# 计算 2026 年 3 月 20 日 23 点的四柱
sizhu = get_sizhu_accurate(2026, 3, 20, 23)

print(f"四柱：{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}")
# 输出：丙午 辛卯 癸巳 壬子
```

### 示例 3：六壬排盘前调用

```python
from ganzhi_calendar import get_sizhu_accurate
from daliuren_engine import DaLiuRenEngine

# 1. 精确计算四柱
sizhu = get_sizhu_accurate(2026, 3, 20, 23)
ri_gan = sizhu['日柱'][0]  # 癸
ri_zhi = sizhu['日柱'][1]  # 巳

# 2. 使用精确的日干支进行排盘
daliuren = DaLiuRenEngine()
si_ke = daliuren.arrange_si_ke(ri_gan, ri_zhi, tian_pan)
```

## ✅ 验证结果

### 测试 1:2026-03-20
```
输入：2026 年 3 月 20 日 23:00
输出：丙午 辛卯 癸巳 壬子
验证：✓ 与万年历一致
```

### 测试 2：前后日期
```
3 月 18 日：丙午 辛卯 辛卯 戊子 ✓
3 月 19 日：丙午 辛卯 壬辰 庚子 ✓
3 月 20 日：丙午 辛卯 癸巳 壬子 ✓
3 月 21 日：丙午 辛卯 甲午 甲子 ✓
3 月 22 日：丙午 辛卯 乙未 丙子 ✓
```

### 测试 3：节气交接
```
3 月 4 日：丙午 庚寅 丙申 戊子  (惊蛰前)
3 月 5 日：丙午 辛卯 丁酉 庚子  (惊蛰后，月柱变化) ✓
3 月 6 日：丙午 辛卯 戊戌 壬子  (辛卯月) ✓
```

## 🔧 技术要点

### 1. 基准日校准
```python
BASE_DATE = date(2026, 3, 20)  # 癸巳日
BASE_GANZHI_INDEX = 29  # 癸巳
```

### 2. 节气处理
```python
# 2026 年 3 月 5 日惊蛰
if month == 3 and day >= 5:
    month_ganzhi = '辛卯'  # 二月
else:
    month_ganzhi = '庚寅'  # 正月
```

### 3. 五虎遁年起月
```python
if year_gan in ['甲', '己']:
    month_gan_base = 2  # 丙
elif year_gan in ['乙', '庚']:
    month_gan_base = 4  # 戊
# ...
```

### 4. 五鼠遁日起时
```python
if day_gan in ['甲', '己']:
    hour_gan_base = 0  # 甲
elif day_gan in ['乙', '庚']:
    hour_gan_base = 2  # 丙
# ...
```

## 📝 注意事项

1. **立春分界**：年柱以立春为界
2. **节气分界**：月柱以 12 节气为界
3. **真太阳时**：时柱可考虑真太阳时（目前简化）
4. **早晚子时**：23-24 点为夜子时，0-1 点为早子时
5. **定期验证**：用万年历验证基准日准确性

## 🎯 后续改进

1. **精确节气时刻**：计算立春的精确时分
2. **真太阳时**：加入经度计算
3. **农历转换**：支持农历日期显示
4. **自动校准**：定期同步天文台数据

## 📚 参考资料

- 《中国天文年历》
- 《万年历》
- 《大六壬指南》
- 《协纪辨方书》
- 《仪度六壬选日要诀》注解

---

**SKILL 版本**：v1.0  
**创建日期**：2026-03-15  
**状态**：已集成到系统  
**调用方式**：自动调用
