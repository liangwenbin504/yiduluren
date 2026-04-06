***

name: "dizhi-layout-generator"
description: "生成传统大六壬地盘布局，地盘永远不动。Invoke when user needs to display 12 地支 in traditional fixed positions with correct coordinates."

--------------------------------------------------------------------------------------------------------------------------------

# 地盘布局生成器（大六壬）

## 功能说明

此 skill 用于生成大六壬传统地盘布局，地盘 12 地支永远固定在以下位置：

```
        巳午未申  ← 上排（4 个，col 0-3）
      辰       酉    ← 左列 (col 0) + 右列 (col 3)
      卯       戌
        寅丑子亥  ← 下排（4 个，col 0-3）
```

## 核心规则

1. **地盘永远不动**：12 地支位置固定不变，显示为蓝色（下方，大字）
2. **月将加时**：月将加在地盘时支位置上
3. **天盘转动**：天盘地支根据月将加时转动，显示为红色（上方，小字）
4. **顺时针排布**：天盘按子丑寅卯...顺序顺时针排布

## 地盘坐标系统（正确版本）

使用网格坐标 (col, row) 定位，5 列 x 4 行：

### 上排（4 个，从左到右，row=0）

- 巳：(0, 0)
- 午：(1, 0)
- 未：(2, 0)
- 申：(3, 0)

### 左列（2 个，从上到下，col=0）

- 辰：(0, 1)
- 卯：(0, 2)

### 右列（2 个，从上到下，col=3）

- 酉：(3, 1)
- 戌：(3, 2)

### 下排（4 个，从右到左，row=3）

- 亥：(3, 3)
- 子：(2, 3)
- 丑：(1, 3)
- 寅：(0, 3)

## 天盘排法

### 月将加时规则

1. 确定月将（根据农历月份或节气）
2. 确定占时（根据地支时辰）
3. 月将加在地盘时支位置上
4. 天盘地支按子丑寅卯...顺序顺时针排布

### 计算公式

```python
# 月将加时计算
shi_index = DIZHI.index(shichen)  # 时支索引
yuejiang_index = DIZHI.index(yuejiang)  # 月将索引

# 计算天盘子位在地盘的哪个位置
zi_position = (shi_index - yuejiang_index) % 12

# 天盘：从地盘子宫开始，每个位置上的天盘地支
tian_pan = []
for i in range(12):
    tian_index = (i - zi_position) % 12
    tian_pan.append(DIZHI[tian_index])

# 天地对应：地盘地支 -> 天盘地支
result = {}
for i in range(12):
    result[DIZHI[i]] = tian_pan[i]
```

### 示例（月将亥，占时午）

1. **月将加时**：亥将加在地盘午位 (1, 0)
2. **天地对应**：
   - 地盘子 (2,3) → 天盘巳
   - 地盘丑 (1,3) → 天盘午
   - 地盘寅 (0,3) → 天盘未
   - 地盘卯 (0,2) → 天盘申
   - 地盘辰 (0,1) → 天盘酉
   - 地盘巳 (0,0) → 天盘戌
   - **地盘午 (1,0) → 天盘亥** ← 月将加时位置
   - 地盘未 (2,0) → 天盘子
   - 地盘申 (3,0) → 天盘丑
   - 地盘酉 (3,1) → 天盘寅
   - 地盘戌 (3,2) → 天盘卯
   - 地盘亥 (3,3) → 天盘辰

## 代码实现

### 数据结构

```python
# 十二地支顺序
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 地盘位置（永远不动）- 正确坐标
DIZHI_POSITIONS = {
    # 上排（4 个，从左到右）
    '巳': (0, 0), '午': (1, 0), '未': (2, 0), '申': (3, 0),
    # 左列（2 个，从上到下）
    '辰': (0, 1), '卯': (0, 2),
    # 右列（2 个，从上到下）
    '酉': (3, 1), '戌': (3, 2),
    # 下排（4 个，从右到左）
    '亥': (3, 3), '子': (2, 3), '丑': (1, 3), '寅': (0, 3),
}
```

### 排盘函数

```python
def arrange_tiandi_pan(yuejiang: str, shichen: str) -> dict:
    """
    排天地盘（月将加时，天盘顺排）
    
    :param yuejiang: 月将（地支）
    :param shichen: 占时（地支）
    :return: 天地盘对应关系 {地盘地支：天盘地支}
    """
    shi_index = DIZHI.index(shichen)
    yuejiang_index = DIZHI.index(yuejiang)
    
    # 计算天盘子位在地盘的哪个位置
    zi_position = (shi_index - yuejiang_index) % 12
    
    # 天盘：从地盘子宫开始，每个位置上的天盘地支
    tian_pan = []
    for i in range(12):
        tian_index = (i - zi_position) % 12
        tian_pan.append(DIZHI[tian_index])
    
    # 天地对应：地盘地支 -> 天盘地支
    result = {}
    for i in range(12):
        result[DIZHI[i]] = tian_pan[i]
    
    return result
```

### 可视化绘制函数（Tkinter）

```python
def draw_dizhi_layout(canvas, tiandi_pan: dict):
    """
    绘制地盘布局（GUI 显示）
    
    :param canvas: Tkinter 画布
    :param tiandi_pan: 天地盘对应关系
    """
    cell_width = 80
    cell_height = 60
    margin_x = 100
    margin_y = 50
    gap_x = 20
    
    for dizhi, (col, row) in DIZHI_POSITIONS.items():
        x = margin_x + col * (cell_width + gap_x)
        y = margin_y + row * (cell_height + 10)
        
        tian_zhi = tiandi_pan.get(dizhi, '')
        
        # 绘制背景（浅蓝色）
        canvas.create_rectangle(
            x, y, x + cell_width, y + cell_height,
            fill='#B0D0F0',
            outline='#8B7355',
            width=2
        )
        
        # 绘制天盘（红色，上方，小字）
        if tian_zhi:
            canvas.create_text(
                x + cell_width/2,
                y + cell_height/2 - 12,
                text=tian_zhi,
                font=('微软雅黑', 14, 'bold'),
                fill='#CD5C5C'  # 红色
            )
        
        # 绘制地盘（蓝色，下方，大字）
        canvas.create_text(
            x + cell_width/2,
            y + cell_height/2 + 12,
            text=dizhi,
            font=('微软雅黑', 16, 'bold'),
            fill='#0000FF'  # 蓝色
        )
```

## 使用方法

### Python 调用

```python
from src.utils.dizhi_layout_generator import arrange_tiandi_pan, DIZHI_POSITIONS

# 排天地盘
yuejiang = '亥'  # 月将
shichen = '午'   # 占时

result = arrange_tiandi_pan(yuejiang, shichen)

# 获取天地盘对应关系
for dizhi, (col, row) in DIZHI_POSITIONS.items():
    tianzhi = result[dizhi]
    print(f"地盘{dizhi} → 天盘{tianzhi} (坐标：{col},{row})")
```

### 文本可视化

```python
from src.utils.dizhi_layout_generator import print_tiandi_pan

# 打印环形布局
print_tiandi_pan('亥', '午')
```

输出：
```
月将：亥，占时：午
========================================
        戌巳  亥午  子未  丑申
        辰      酉
        卯      戌
        未寅  午丑  巳子  辰亥
========================================
```

### GUI 可视化

```python
from src.utils.gui_visual_test import DIZHILayoutViewer
import tkinter as tk

root = tk.Tk()
app = DIZHILayoutViewer(root)
root.mainloop()
```

## 关键验证点

### ✅ 辰卯酉戌位置

- **辰**：坐标 (0, 1) - 左列，col=0
- **卯**：坐标 (0, 2) - 左列，col=0
- **酉**：坐标 (3, 1) - 右列，col=3（左移一格）
- **戌**：坐标 (3, 2) - 右列，col=3（左移一格）

### ✅ 颜色配置

- **地盘文字**：蓝色 `#0000FF`（下方，大字）
- **天盘文字**：红色 `#CD5C5C`（上方，小字）
- **格子背景**：浅蓝色 `#B0D0F0`
- **月将加时**：红色边框标记

### ✅ 月将加时验证

以亥将午时为例：
- 地盘午位 (1, 0) → 天盘亥
- 天盘从午位开始顺时针：亥→子→丑→寅→卯→辰→巳→午→未→申→酉→戌

## 注意事项

1. **地盘固定**：地盘 12 地支位置永远不变
2. **天盘转动**：天盘根据月将加时转动
3. **顺时针排布**：天盘子丑寅卯...按顺时针方向排布
4. **坐标正确**：辰卯在 col 0（最左），酉戌在 col 3（左移一格）
5. **颜色区分**：地盘蓝色在下，天盘红色在上

## 相关文件

- `src/utils/dizhi_layout_generator.py` - 核心排盘模块
- `src/utils/gui_visual_test.py` - GUI 可视化测试
- `src/utils/visual_test.py` - 文本可视化测试
- `src/ui/tianpan_widget.py` - UI 组件（已使用正确坐标）

## 测试命令

```bash
# 文本可视化测试
python -m src.utils.visual_test

# GUI 可视化测试
python -m src.utils.gui_visual_test

# 基础排盘测试
python -m src.utils.dizhi_layout_generator
```

## 参考经典

- 《仪度六壬选日要诀》
- 《大六壬指南》
- 《六壬大全》

## 更新日志

- ✅ 修正辰卯坐标：(0, 1) 和 (0, 2)（左列，col=0）
- ✅ 修正酉戌坐标：(3, 1) 和 (3, 2)（右列，col=3）
- ✅ 修正颜色配置：地盘蓝色 `#0000FF`，天盘红色 `#CD5C5C`
- ✅ 添加 GUI 可视化测试
- ✅ 添加详细文本可视化测试
