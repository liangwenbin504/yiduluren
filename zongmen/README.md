# 宗门九课起课法模块

大六壬九宗门起课法完整实现，包含 8640 课例（720 课例 × 12 时辰）的完整数据库。

## 📁 目录结构

```
zongmen/
├── src/
│   ├── engine/
│   │   ├── __init__.py              # 模块初始化
│   │   ├── sike_sanchuan_engine.py  # 四课三传计算引擎
│   │   ├── jiu_zong_men_720_matcher.py  # 720 课例匹配器
│   │   └── gui_ren_engine.py        # 贵人排盘引擎（依赖）
│   ├── utils/
│   │   ├── __init__.py              # 工具包初始化
│   │   └── dizhi_layout_generator.py # 天地盘排布（依赖）
│   ├── data/
│   │   ├── __init__.py              # 数据包初始化
│   │   └── 斗首择日规则.py          # 地支天将数据（依赖）
│   └── ui/
│       └── qike_verification_gui.py # GUI 验证界面
├── data/
│   └── 720_ke_li_jiu_zong_men.json  # 720 课例数据库
├── http_api_server.py               # HTTP API 服务器
├── demo.html                        # HTML 演示页面
├── view_jiu_zong_men_720.py         # 课例查看器
├── 快速启动.bat                     # 快速启动菜单
├── README.md                        # 本文档
└── 导入指南.md                      # 集成指南
```

## 🚀 快速开始

### 方式一：Python 直接调用

```python
from src.engine import SiKeSanChuanCalculator

# 创建计算器
calculator = SiKeSanChuanCalculator()

# 计算天地盘
tiandi_pan = calculator.get_tiandi_pan('丑', '子')

# 起四课
sike = calculator.qi_sike('甲', '子', tiandi_pan)

# 发三传（九宗门起法）
sanchuan = calculator.fa_sanchuan(sike, '甲', '子', tiandi_pan)

print(f"三传：{sanchuan['三传']}")
print(f"起法：{sanchuan['起法']}")
print(f"课体：{sanchuan['课体']}")
```

### 方式二：HTTP API 调用

1. **启动 API 服务器**
```bash
python http_api_server.py
```

2. **调用 API**
```bash
# GET 方式
curl "http://localhost:5000/api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=丑&shi_chen=子"

# POST 方式
curl -X POST "http://localhost:5000/api/qike" \
  -H "Content-Type: application/json" \
  -d '{"ri_gan":"甲","ri_zhi":"子","yue_jiang":"丑","shi_chen":"子"}'
```

3. **访问 HTML 演示页面**
```
打开浏览器访问：demo.html
```

## 📊 API 接口文档

### 1. 起课 API

**GET /api/qike**

参数：
- `ri_gan` - 日干（甲、乙、丙、丁...）
- `ri_zhi` - 日支（子、丑、寅、卯...）
- `yue_jiang` - 月将（子、丑、寅、卯...）
- `shi_chen` - 时辰（子、丑、寅、卯...）

示例：
```
GET /api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=丑&shi_chen=子
```

响应：
```json
{
  "success": true,
  "data": {
    "ri_gan": "甲",
    "ri_zhi": "子",
    "yue_jiang": "丑",
    "shi_chen": "子",
    "tiandi_pan": {...},
    "sike": [...],
    "sanchuan": {
      "三传": ["子", "丑", "寅"],
      "课体": "元首课",
      "起法": "贼克法"
    }
  }
}
```

### 2. 课例查询 API

**GET /api/ke_li**

参数：
- `ri_gan_zhi` - 日干支（可选）
- `yue` - 月建（可选）
- `shi` - 时辰（可选）

示例：
```
GET /api/ke_li?ri_gan_zhi=甲子&yue=子&shi=子
```

### 3. 统计信息 API

**GET /api/stats**

获取 720 课例的统计信息。

## 🎯 九宗门起法

本模块完整实现了大六壬九宗门起课法：

1. **贼克法** - 有克贼时使用（元首课、重审课）
2. **比用法** - 多课克贼时用
3. **涉害法** - 比用后仍有多课时用
4. **遥克法** - 无克贼有遥克时用（蒿矢课、弹射课）
5. **昴星法** - 无克贼无遥克时用
6. **别责法** - 四课不完备时用
7. **八专法** - 日干支同位时用
8. **伏吟法** - 月将=占时时用
9. **反吟法** - 月将冲占时时用

## 📖 使用示例

### 示例 1：Python GUI 界面

```bash
# 启动起课验证 GUI
python src/ui/qike_verification_gui.py

# 启动课例查看器
python view_jiu_zong_men_720.py
```

### 示例 2：HTML 集成

在您的 HTML 项目中：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>我的六壬应用</title>
</head>
<body>
    <script>
        async function qike() {
            const response = await fetch('http://localhost:5000/api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=丑&shi_chen=子');
            const data = await response.json();
            
            if (data.success) {
                console.log('三传:', data.data.sanchuan.三传);
                console.log('起法:', data.data.sanchuan.起法);
            }
        }
        
        qike();
    </script>
</body>
</html>
```

## 📊 720 课例数据库

包含 8640 课（60 甲子 × 12 月 × 12 时）的完整数据：

- 每个课例包含：四课、三传、九宗门起法、课体、匹配课经
- 数据文件格式：JSON
- 文件大小：约 10MB

查看数据：
```python
import json

with open('data/720_ke_li_jiu_zong_men.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
# 访问特定课例
ke_li = data['ke_li']['甲子_子_子']
print(ke_li)
```

## 🔧 配置说明

### 依赖

- Python 3.8+
- tkinter（GUI 需要）
- 无其他第三方依赖

### 端口配置

API 服务器默认端口：5000

修改端口：
```bash
python http_api_server.py 8080
```

## 📝 注意事项

1. **API 服务器**：使用 HTTP API 前需先启动 `http_api_server.py`
2. **跨域访问**：API 支持 CORS，可在任意域名的 HTML 页面中调用
3. **数据文件**：确保 `data/720_ke_li_jiu_zong_men.json` 文件存在
4. **编码**：所有文件使用 UTF-8 编码

## 🎓 技术特点

- ✅ 完整的九宗门算法实现（v3.0 修正版）
- ✅ 支持 8640 课例批量处理
- ✅ HTTP API 接口，方便集成
- ✅ HTML 演示页面，开箱即用
- ✅ 详细的课例数据库
- ✅ 100% 成功率，无失败课例

## 📞 技术支持

如有问题，请检查：
1. Python 版本是否 >= 3.8
2. tkinter 模块是否可用
3. API 服务器是否启动
4. 数据文件是否完整

## 📄 版本信息

- 版本：1.0.0
- 更新日期：2026-03-19
- 引擎版本：sike_sanchuan_engine v3.0
