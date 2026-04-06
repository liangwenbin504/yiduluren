# 仪度六壬择日系统 - API接口文档

## 基础信息
- **API基础地址**: http://localhost:5000
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 1. 健康检查

### 接口信息
- **URL**: `/api/health`
- **方法**: GET
- **描述**: 检查API服务器是否正常运行

### 请求参数
无

### 响应示例
```json
{
    "server": "仪度六壬择日 API服务器",
    "status": "ok"
}
```

---

## 2. 四柱计算

### 接口信息
- **URL**: `/api/sizhu`
- **方法**: GET
- **描述**: 根据公历日期计算四柱（年柱、月柱、日柱、时柱）

### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| year | int | 是 | 公历年 | 2026 |
| month | int | 是 | 公历月 | 4 |
| day | int | 是 | 公历日 | 3 |
| hour | int | 是 | 小时（0-23） | 12 |

### 响应示例
```json
{
    "success": true,
    "data": {
        "year_pillar": "丙午",
        "month_pillar": "壬辰",
        "day_pillar": "戊申",
        "hour_pillar": "戊午",
        "year_gan": "丙",
        "year_zhi": "午",
        "month_gan": "壬",
        "month_zhi": "辰",
        "day_gan": "戊",
        "day_zhi": "申",
        "hour_gan": "戊",
        "hour_zhi": "午"
    }
}
```

---

## 3. 斗首完整分析

### 接口信息
- **URL**: `/api/doushou/full_analyze`
- **方法**: POST
- **描述**: 分析斗首课格，计算评分和断语

### 请求参数（JSON Body）
```json
{
    "mountain": "壬",
    "sizhu": {
        "年柱": "戊申",
        "月柱": "丁巳",
        "日柱": "戊午",
        "时柱": "癸亥"
    }
}
```

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| mountain | string | 是 | 坐山（如：壬、子、癸等） |
| sizhu | object | 是 | 四柱信息 |
| sizhu.年柱 | string | 是 | 年柱干支 |
| sizhu.月柱 | string | 是 | 月柱干支 |
| sizhu.日柱 | string | 是 | 日柱干支 |
| sizhu.时柱 | string | 是 | 时柱干支 |

### 响应示例
```json
{
    "success": true,
    "result": {
        "坐山": "壬",
        "山家五行": "土",
        "四柱分析": {
            "年柱": {
                "干支": "戊申",
                "天干": "戊",
                "化气": "火",
                "六亲": "贪官",
                "地支": "申",
                "支藏干": ["庚", "壬", "戊"]
            },
            ...
        },
        "课格格局": ["元辰无气"],
        "吉凶断语": ["四柱当中没有元辰，为元辰无气，不合格之课"],
        "综合评分": 35
    },
    "timestamp": "2026-04-03T12:00:00"
}
```

---

## 4. 演禽四禽分析

### 接口信息
- **URL**: `/api/yanqin/four_qin`
- **方法**: GET
- **描述**: 计算年禽、月禽、日禽、时禽

### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| year_zhi | string | 是 | 年支 | 子 |
| month_zhi | string | 是 | 月支 | 寅 |
| day_zhi | string | 是 | 日支 | 子 |
| hour_zhi | string | 是 | 时支 | 子 |

### 响应示例
```json
{
    "success": true,
    "data": {
        "年禽": {
            "禽名": "虚日鼠",
            "简称": "鼠",
            "吉凶": "凶"
        },
        "月禽": {
            "禽名": "娄金狗",
            "简称": "狗",
            "吉凶": "吉"
        },
        ...
    }
}
```

---

## 5. 导出DOCX文档

### 接口信息
- **URL**: `/api/export/docx`
- **方法**: POST
- **描述**: 导出择日课单为DOCX文档

### 请求参数（JSON Body）
```json
{
    "title_type": "立碑吉课",
    "mountain": "壬",
    "xiangshan": "丙",
    "four_pillars": {
        "year": "丙午",
        "month": "甲午",
        "day": "丙午",
        "hour": "甲午"
    },
    "daliuren_data": {
        "yueJiang": "巳",
        "shiChen": "午"
    },
    "evaluation": "此课大吉...",
    "dates": [
        {
            "date": "2026-04-01",
            "hour": "午时",
            "score": "98"
        }
    ]
}
```

### 响应示例
```json
{
    "success": true,
    "filename": "择日课单_20260403_120000.docx",
    "download_url": "/api/export/download/择日课单_20260403_120000.docx",
    "timestamp": "2026-04-03T12:00:00"
}
```

---

## 6. 下载文档

### 接口信息
- **URL**: `/api/export/download/<filename>`
- **方法**: GET
- **描述**: 下载导出的DOCX文档

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 文件名（从导出接口获取） |

### 响应
文件下载流

---

## 错误处理

所有API在发生错误时，会返回以下格式的响应：

```json
{
    "error": "错误描述信息"
}
```

常见HTTP状态码：
- 200: 成功
- 400: 请求参数错误
- 404: 资源未找到
- 500: 服务器内部错误

---

## 斗首术语标准化

根据最新规范，斗首六亲关系术语如下：

| 术语 | 关系 | 属性 | 说明 |
|------|------|------|------|
| 元辰 | 同我者 | 吉 | 与山家五行相同 |
| 武财 | 我克者 | 吉 | 妻财，主财源 |
| 贪官 | 生我者 | 凶 | 贪化鬼，需制化 |
| 廉贞 | 我生者 | 平 | 子孙，视元辰旺衰定吉凶 |
| 破鬼 | 克我者 | 凶 | 鬼贼，需制伏 |

**注意**：
- 生我者：明确为"贪官"而非"贪狼"
- 克我者：明确为"破鬼"而非"破军"
- 我克者：明确为"武财"而非"武曲"

---

## 前端调用示例

### JavaScript Fetch API

```javascript
// 四柱计算
const sizhuResponse = await fetch(
    `http://localhost:5000/api/sizhu?year=${year}&month=${month}&day=${day}&hour=${hour}`
);
const sizhuData = await sizhuResponse.json();

// 斗首分析
const doushouResponse = await fetch('http://localhost:5000/api/doushou/full_analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        mountain: '壬',
        sizhu: {
            '年柱': '戊申',
            '月柱': '丁巳',
            '日柱': '戊午',
            '时柱': '癸亥'
        }
    })
});
const doushouData = await doushouResponse.json();

// 演禽分析
const yanqinResponse = await fetch(
    `http://localhost:5000/api/yanqin/four_qin?year_zhi=${yearZhi}&month_zhi=${monthZhi}&day_zhi=${dayZhi}&hour_zhi=${hourZhi}`
);
const yanqinData = await yanqinResponse.json();
```

---

## 更新日志

### 2026-04-03
- 修正斗首术语：贪狼→贪官，破军→破鬼，武曲→武财
- 修正 `/api/doushou/full_analyze` 接口调用方式
- 统一API响应格式
- 添加完整的API文档
