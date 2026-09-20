#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票预测专用模板库

包含：
1. 股票专用system prompt
2. 股票专用分析模板
3. 类象映射表（行业五行、代码地支、板块属性）
4. 股票预测专用输出格式

设计原则：
- 与现有模板引擎格式兼容
- 提供17步完整推理链
- 包含股票特有类象映射
"""

from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════
# 1. 行业五行映射表（细分行业版）
# ═══════════════════════════════════════════════════════════

INDUSTRY_WUXING = {
    # ═══════ 金融类 ═══════
    '银行|股份制银行|国有银行|城商行|农商行': '金',
    '证券|券商|投行|经纪业务': '金',
    '保险|人寿险|财产险|再保险': '金',
    '多元金融|信托|期货|租赁|私募': '金',
    '金融科技|金融IT|第三方支付': '金',
    
    # ═══════ 科技类 ═══════
    '芯片|半导体|晶圆|IC设计|封测': '火',
    '人工智能|AI|大模型|机器学习|智能计算': '火',
    '通信|5G|6G|光通信|基站': '火',
    '互联网|电商|云计算|大数据|物联网': '火',
    '软件|操作系统|应用软件|企业服务|SaaS': '火',
    '电子|消费电子|智能手机|笔记本|平板': '火',
    '计算机|服务器|存储|网络设备': '火',
    '信息安全|网络安全|密码学': '火',
    
    # ═══════ 地产类 ═══════
    '地产|房地产|住宅开发|商业地产|产业地产': '土',
    '基建|基础设施|公路|桥梁|隧道': '土',
    '建材|水泥|玻璃|陶瓷|砖瓦': '土',
    '工程|建筑工程|土木工程|装修装饰': '土',
    '物业管理|园区运营': '土',
    
    # ═══════ 消费类 ═══════
    '白酒|白酒酿造|高端白酒|次高端白酒': '木',
    '食品|食品加工|调味品|乳制品|烘焙': '木',
    '饮料|软饮料|果汁|茶饮|咖啡': '木',
    '农业|种植业|养殖业|渔业|林业': '木',
    '医药|生物制药|化学制药|中药|医疗器械': '木',
    '医疗|医院|医疗服务|健康体检': '木',
    '消费零售|商超|百货|购物中心': '木',
    '家电|白色家电|黑色家电|小家电': '木',
    '服饰|服装|鞋帽|箱包|纺织': '木',
    '美妆|化妆品|个人护理|美容': '木',
    
    # ═══════ 能源类 ═══════
    '石油|原油开采|炼油|油气服务': '金',
    '天然气|燃气|LNG|管网': '金',
    '煤炭|动力煤|焦煤|煤化工': '金',
    '有色|有色金属|铜|铝|锌|铅|镍': '金',
    '黄金|金矿|铂金|白银': '金',
    '稀土|稀有金属|战略资源': '金',
    '矿业|采矿|矿山|矿产资源': '金',
    
    # ═══════ 公用事业类 ═══════
    '电力|火电|水电|核电|风电|光伏': '水',
    '水力|水务|自来水|污水处理': '水',
    '环保|固废处理|大气治理|土壤修复': '水',
    '公用事业|城市基础设施': '水',
    '燃气|天然气供应|城市燃气': '水',
    
    # ═══════ 制造类 ═══════
    '汽车|乘用车|商用车|新能源车|电动车': '木',
    '汽车零部件|轮胎|电池|电机|电控': '木',
    '机械|工程机械|农用机械|机床': '木',
    '化工|石油化工|精细化工|日化': '木',
    '制造|装备制造|智能制造|工业自动化': '木',
    '电器|输配电|电机|家电': '木',
    '轻工|造纸|印刷|包装': '木',
    
    # ═══════ 军工类 ═══════
    '军工|国防|航天|航空|导弹|舰艇': '金',
    '航空发动机|直升机|无人机': '金',
    '卫星|火箭|航天测控': '金',
    '雷达|电子对抗|导航': '金',
    
    # ═══════ 传媒类 ═══════
    '传媒|影视|电影|电视剧|综艺': '火',
    '广告|营销|品牌传播': '火',
    '文化|出版|图书|音像': '火',
    '教育|在线教育|职业教育|早教': '火',
    '娱乐|游戏|电竞|直播': '火',
    
    # ═══════ 物流运输类 ═══════
    '物流|快递|仓储|供应链': '水',
    '运输|公路运输|铁路运输': '水',
    '交通|港口|航运|航空运输': '水',
    '机场|航空枢纽': '水',
    
    # ═══════ 周期类 ═══════
    '钢铁|普钢|特钢|不锈钢': '金',
    '化工新材料|高性能纤维|工程塑料': '木',
    '有色加工|铝材|铜材': '金',
    
    # ═══════ 新兴产业类 ═══════
    '光伏|太阳能|硅料|组件': '水',
    '风电|风力发电|风机': '水',
    '储能|电池储能|抽水蓄能': '水',
    '氢能|燃料电池|绿氢': '水',
    '量子计算|量子通信': '火',
    '生物科技|基因工程|生物技术': '木',
    '新材料|碳纤维|复合材料': '金',
}


# ═══════════════════════════════════════════════════════════
# 2. 股票代码→地支映射
# ═══════════════════════════════════════════════════════════

CODE_DIZHI_MAP = {
    '0': '子', '1': '丑', '2': '寅', '3': '卯', '4': '辰',
    '5': '巳', '6': '午', '7': '未', '8': '申', '9': '酉'
}

# 地支→十二神
DIZHI_SHISHEN_MAP = {
    '子': '登明', '丑': '大吉', '寅': '功曹', '卯': '太冲',
    '辰': '天罡', '巳': '太乙', '午': '胜光', '未': '小吉',
    '申': '传送', '酉': '从魁', '戌': '河魁', '亥': '神后'
}

# 地支→天将（固定类象，非排盘天将）
DIZHI_TIANJIANG_MAP = {
    '子': '贵人', '丑': '螣蛇', '寅': '朱雀', '卯': '六合',
    '辰': '勾陈', '巳': '青龙', '午': '天空', '未': '白虎',
    '申': '太常', '酉': '玄武', '戌': '太阴', '亥': '天后'
}


# ═══════════════════════════════════════════════════════════
# 3. 日干五行→股票类象映射
# ═══════════════════════════════════════════════════════════

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
}

# 生我者为父母，我生者为子孙，克我者为官鬼，我克者为妻财，同我者为兄弟
SHENG_WUXING = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
}

KE_WUXING = {
    '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
}

WUXING_LIUQIN_MEANING = {
    '父母': '政策面/基本面',
    '子孙': '市场情绪/散户',
    '官鬼': '主力/庄力',
    '妻财': '资金面/流动性',
    '兄弟': '竞争/阻力',
}


# ═══════════════════════════════════════════════════════════
# 4. 板块五行属性（细分板块版）
# ═══════════════════════════════════════════════════════════

SECTOR_WUXING = {
    # ═══════ 综合指数 ═══════
    '上证指数|上证综指': '金',
    '深证成指|深证综指': '金',
    '沪深300|沪深300指数': '金',
    '上证50|上证50ETF': '金',
    '中证500|中证500指数': '木',
    '中证1000|中证1000指数': '木',
    '创业板指|创业板': '火',
    '科创板50|科创50': '火',
    '恒生指数|恒指': '金',
    '国企指数|H股': '金',
    
    # ═══════ 宽基板块 ═══════
    '金融板块|金融ETF': '金',
    '科技板块|科技ETF': '火',
    '地产板块|房地产ETF': '土',
    '消费板块|消费ETF': '木',
    '能源板块|能源ETF': '金',
    '制造板块|制造ETF': '木',
    '军工板块|军工ETF': '金',
    '传媒板块|传媒ETF': '火',
    '公用事业|公用事业ETF': '水',
    
    # ═══════ 细分行业板块 ═══════
    # 金融细分
    '银行板块|银行ETF|中证银行': '金',
    '券商板块|证券ETF': '金',
    '保险板块|保险ETF': '金',
    '基金板块|基金ETF': '金',
    
    # 科技细分
    '芯片板块|半导体|芯片ETF': '火',
    '人工智能|AI板块|AI ETF': '火',
    '5G板块|通信ETF': '火',
    '云计算|大数据ETF': '火',
    '软件板块|软件ETF': '火',
    '信息安全|网络安全': '火',
    
    # 消费细分
    '白酒板块|白酒ETF|酒ETF': '木',
    '食品饮料|食品饮料ETF': '木',
    '医药板块|医药ETF|医疗ETF': '木',
    '家电板块|家电ETF': '木',
    '服饰板块|纺织服装': '木',
    '美妆板块|化妆品': '木',
    
    # 能源细分
    '石油板块|石油ETF': '金',
    '煤炭板块|煤炭ETF': '金',
    '有色板块|有色金属ETF': '金',
    '黄金板块|黄金ETF': '金',
    '稀土板块|稀土ETF': '金',
    
    # 制造细分
    '汽车板块|汽车ETF|新能源车': '木',
    '锂电池板块|电池ETF|锂电池': '木',
    '光伏板块|光伏ETF|新能源': '水',
    '风电板块|风电ETF': '水',
    '储能板块|储能ETF': '水',
    '机械板块|机械ETF': '木',
    '化工板块|化工ETF': '木',
    
    # 军工细分
    '航天军工|军工ETF|国防军工': '金',
    '航空板块|航空ETF': '金',
    '卫星导航|北斗ETF': '金',
    
    # 其他细分
    '地产细分|建材ETF|基建ETF': '土',
    '环保板块|环保ETF': '水',
    '水务板块|水务ETF': '水',
    '燃气板块|燃气ETF': '水',
    '物流板块|物流ETF': '水',
    '传媒细分|游戏ETF|影视ETF': '火',
    '教育板块|教育ETF': '火',
    '农业板块|农业ETF|种业': '木',
    '养殖板块|畜牧ETF': '木',
    '林业板块|林业ETF': '木',
    
    # ═══════ 概念板块 ═══════
    '新能源|新能源汽车|新能源车ETF': '水',
    '储能|储能概念|储能ETF': '水',
    '光伏|光伏概念|光伏ETF': '水',
    '风电|风电概念|风电ETF': '水',
    '氢能|氢能概念|氢能ETF': '水',
    '人工智能|AI概念|AI ETF': '火',
    '大模型|LLM概念|GPT': '火',
    '机器人|机器人概念|具身智能': '木',
    '自动驾驶|智能驾驶|车联网': '木',
    '数字货币|区块链|币圈': '金',
    '元宇宙|VR|AR': '火',
    '脑科学|脑机接口': '火',
    '生物科技|基因编辑|创新药': '木',
    '医疗器械|医疗设备': '木',
    'CXO|医药外包': '木',
    '消费电子|苹果产业链|华为产业链': '火',
    '华为概念|鸿蒙|华为产业链': '火',
    '苹果概念|苹果产业链': '火',
    '特斯拉概念|特斯拉产业链': '木',
    '比亚迪概念|比亚迪产业链': '木',
    '国产替代|自主可控': '火',
    '信创|信息技术应用创新': '火',
    '特高压|电网改造': '水',
    '碳中和|碳交易|绿色低碳': '水',
    '美丽中国|生态环保': '水',
    '乡村振兴|农业农村': '木',
    '共同富裕|社会保障': '土',
    '一带一路|基建出海': '土',
    '自贸区|自由贸易': '金',
    '大湾区|粤港澳': '金',
    '雄安新区|京津冀': '土',
    '西部大开发|西部基建': '土',
}


# ═══════════════════════════════════════════════════════════
# 5. 股票专用模板（与template_engine格式兼容）
# ═══════════════════════════════════════════════════════════

STOCK_SPECIAL_TEMPLATES = {
    "股票预测": {
        "system_prompt": """你是一个大六壬股票预测推理专家。你的任务是按主干到枝叶的层次客观推理，而非简单分类。

【分析层次 — 由主到次，逐层递进】
┌─────────────────────────────────────────────────────┐
│ 主干: 课体定大局 — 伏吟/反吟/涉害/遥克等课体本身        │
│       就已决定了大势方向，不可被枝叶细节推翻             │
│ 大枝: 三传定时序 — 初传(开盘)/中传(盘中)/末传(尾盘)      │
│       三传走势是操作节奏的核心，制救关系定转折            │
│ 中枝: 六亲+天将 — 财官父子兄各自带将，解读多空力量        │
│ 细枝: 神煞点缀 — 在天喜处添喜，在破碎处加凶，              │
│       不可喧宾夺主推翻主干，但可强化/弱化                 │
│ 末节: 旺衰/旬空/刑冲 — 判断力度与时机的辅助条件           │
└─────────────────────────────────────────────────────┘

【股票类象映射】
- 行业五行决定股票属性：金融=金，科技=火，地产=土，消费=木，能源=金
- 日干与股票五行关系决定六亲：
  · 日干生股票五行 → 子孙（泄气）
  · 股票五行生日干 → 父母（得生）
  · 日干克股票五行 → 妻财（财）
  · 股票五行克日干 → 官鬼（官）
  · 同五行 → 兄弟（竞争）
- 代码尾数映射地支→十二神：0→子(登明)，1→丑(大吉)，...，9→酉(从魁)

【核心原则】
1. 课体是最重要的判断依据
2. 天将含义取决于所乘何神 + 日干旺衰 + 临何种六亲
3. 身强能担财→涨，身弱不胜财→涨势难继
4. 不可用八字五行直接推导地支间生克""",
        
        "analysis_template": """请按照以下17步完整推理链分析本次股票预测：

【排盘信息】
课体：{keti}
四课加临：{sike}
三传：{sanchuan}
天将：{tianjiang}
五行：{wuxing_analysis}
日干：{day_gan}
身强身弱：{shen_wangshuai}

【股票类象】
股票代码：{stock_code}
股票名称：{stock_name}
行业：{industry}
行业五行：{industry_wuxing}
六亲关系：{liuqin}

【推理步骤 — 17步完整链】
1. 课体定势: 先判断课体在股市中的象意（伏吟=盘整/迟滞，反吟=剧烈反转，涉害=多空博弈激烈，遥克=突发消息驱动，元首=趋势延续等），这是最重要的一步
2. 四课加临: 干上/支上分析益脱制损。⚠️月将临支上=「太阳照宅」→市场向阳大利好! 月将临干上=「太阳照身」→我方得势。配合三传吉更验
3. 用神五气: 发用的旺相休囚死状态决定行情的喜庆程度
4. 三传时序: 初→中→末的节奏变化，制救关系决定转折点。⚠️伏吟课中若带刑冲→「不动变必动」=反转信号！配合螣蛇(主动)、天喜(主涨)更验
5. 六亲力量: 财旺=资金充足但需身强来担，官鬼=主力控盘，父母=政策面
6. 天将动态解读: ⚠️天将不可死板一对一映射！天将的含义取决于【所乘何神 + 日干旺衰 + 临何种六亲】
7. 五行流通: 三传五行生克链条，判断能量的传递方向
8. 旬空+日墓: 空亡则虚，日墓则滞。⚠️月将临墓=「太阳照墓」破暗向明≠利空！
9. 旺衰虚实: 先判身强与否(四大标准)，身强能担财→涨；身弱不胜财→涨势难继
10. 神煞点睛: 在主干判断基础上，追加神煞的强化/弱化效应（绝不能推翻课体判断）
11. 刑冲合害: ⚠️六壬规则: 地支本身不直接作用! 要透过上神!
12. 八杀评分: 德合为吉、鬼墓破害刑冲为凶，综合评分
13. 十二气财星: 三传长生十二宫状态
14. 身强身弱 — 四大标准, 必须逐条查
15. 趋势判断: 综合以上，给出一致性最强的趋势预测
16. 应期: 关键时间节点
17. 风险提示

【关键规则速查】
- 白虎乘财+日干旺相+德禄=「暴发」看涨
- 青龙乘财+日干旺=主升浪
- 腾蛇+天喜+刑冲(伏吟中): 「不动变必动」反转上涨信号
- 月将(太阳之位)自带吉气: 凶将乘月将→凶性被太阳中和; 吉将乘月将→吉力倍增
- 日干12长生状态决定天将之力""",
        
        "output_format": """请输出JSON格式：
{
    "keti_judgment": "课体判断（10字以内，如'吉课看涨'）",
    "trend_prediction": "趋势预测（大涨/上涨/震荡偏涨/震荡/震荡偏跌/下跌/大跌）",
    "key_factors": {
        "keti_score": 0-100,
        "sanchuan_score": 0-100,
        "tianjiang_score": 0-100,
        "liuqin_score": 0-100,
        "shen_status": "身强/身弱"
    },
    "analysis_summary": "分析摘要（50字以内）",
    "risk_warning": "风险提示（如有则写，无则写'无明显风险'）",
    "operation_advice": "操作建议（买入/卖出/观望/减仓）",
    "confidence_score": 0-100
}"""
    },
    
    "大盘预测": {
        "system_prompt": """你是一个大六壬大盘走势预测专家。请根据排盘信息判断大盘整体走势。

【大盘预测核心】
1. 课体决定大盘整体方向
2. 三传决定日内走势节奏
3. 天将反映市场情绪
4. 六亲体现资金面状况""",
        
        "analysis_template": """请分析大盘走势：

【排盘信息】
课体：{keti}
三传：{sanchuan}
天将：{tianjiang}
五行：{wuxing_analysis}

【大盘关键指标】
- 课体吉凶
- 三传连续性（是否成局）
- 天将吉凶分布
- 六亲旺衰

【推理重点】
1. 大盘整体方向（涨/跌/震荡）
2. 日内节奏（早盘/午盘/尾盘）
3. 板块轮动信号
4. 成交量预判""",
        
        "output_format": """{
    "market_trend": "大涨/上涨/震荡偏涨/震荡/震荡偏跌/下跌/大跌",
    "intraday_pattern": "早盘强/午盘强/尾盘强/全天弱",
    "sector_rotation": "有/无",
    "volume_prediction": "放量/缩量/正常",
    "key_signals": ["信号1", "信号2"],
    "confidence_score": 0-100
}"""
    },
    
    "个股预测": {
        "system_prompt": """你是一个大六壬个股预测专家。请根据排盘信息和股票类象进行个股走势预测。

【个股预测核心】
1. 股票类象映射（行业五行、代码地支）
2. 课体与股票类象的匹配度
3. 天将在该股票类象下的含义
4. 六亲关系与股票属性的关联""",
        
        "analysis_template": """请分析个股走势：

【股票信息】
代码：{stock_code}
名称：{stock_name}
行业：{industry}
行业五行：{industry_wuxing}
代码地支：{code_dizhi}
类象十二神：{code_shishen}

【排盘信息】
课体：{keti}
三传：{sanchuan}
天将：{tianjiang}
日干：{day_gan}
六亲：{liuqin}

【推理重点】
1. 行业五行与课体/三传的生克关系
2. 代码地支对应的十二神在课传中的状态
3. 六亲关系（妻财/官鬼/父母等）对该股的影响
4. 该股的特有类象（如白酒→太常/未，银行→太阴/酉）""",
        
        "output_format": """{
    "stock_trend": "大涨/上涨/震荡偏涨/震荡/震荡偏跌/下跌/大跌",
    "stock_specific_factors": {
        "industry_match": "行业与课体匹配度",
        "code_dizhi_status": "代码地支在课传中的状态",
        "liuqin_signal": "六亲信号"
    },
    "entry_point": "建议买入点位（如有）",
    "exit_point": "建议卖出点位（如有）",
    "stop_loss": "止损位（如有）",
    "confidence_score": 0-100
}"""
    },
}


# ═══════════════════════════════════════════════════════════
# 5.5 个股级类象数据库（热门个股映射）
# ═══════════════════════════════════════════════════════════

# 热门个股类象映射表
# 每个条目包含：代码、名称、行业五行、特有类象、关键关联
STOCK_LEIXIANG_DATABASE = {
    # ═══════ 白酒龙头 ═══════
    '600519': {
        'name': '贵州茅台', 'wuxing': '木', 'industry': '白酒',
        'unique_leixiang': '茅台=酒祖，对应太常/未（酒水类象）',
        'key_association': '白酒龙头，行业标杆',
        'code_dizhi': '酉', 'code_shishen': '从魁',
    },
    '000858': {
        'name': '五粮液', 'wuxing': '木', 'industry': '白酒',
        'unique_leixiang': '五粮液=酒王，对应太常/丑',
        'key_association': '浓香型白酒龙头',
        'code_dizhi': '酉', 'code_shishen': '从魁',
    },
    '600809': {
        'name': '山西汾酒', 'wuxing': '木', 'industry': '白酒',
        'unique_leixiang': '汾酒=清香型代表，对应太常/未',
        'key_association': '清香型白酒龙头',
        'code_dizhi': '酉', 'code_shishen': '从魁',
    },
    '000568': {
        'name': '泸州老窖', 'wuxing': '木', 'industry': '白酒',
        'unique_leixiang': '老窖=浓香型，对应太常/丑',
        'key_association': '浓香型白酒鼻祖',
        'code_dizhi': '酉', 'code_shishen': '从魁',
    },
    
    # ═══════ 银行龙头 ═══════
    '601398': {
        'name': '工商银行', 'wuxing': '金', 'industry': '银行',
        'unique_leixiang': '工行=宇宙第一行，对应太阴/酉',
        'key_association': '国有大行龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '601288': {
        'name': '农业银行', 'wuxing': '金', 'industry': '银行',
        'unique_leixiang': '农行=县域金融，对应太阴/酉',
        'key_association': '国有大行',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '600036': {
        'name': '招商银行', 'wuxing': '金', 'industry': '银行',
        'unique_leixiang': '招行=零售之王，对应太阴/酉',
        'key_association': '股份制银行龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '601318': {
        'name': '中国平安', 'wuxing': '金', 'industry': '保险',
        'unique_leixiang': '平安=综合金融，对应太阴/酉',
        'key_association': '保险龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    
    # ═══════ 科技龙头 ═══════
    '002594': {
        'name': '比亚迪', 'wuxing': '木', 'industry': '新能源车',
        'unique_leixiang': '比亚迪=新能源汽车龙头，对应木/寅卯',
        'key_association': '新能源车全球龙头',
        'code_dizhi': '巳', 'code_shishen': '太乙',
    },
    '300750': {
        'name': '宁德时代', 'wuxing': '木', 'industry': '锂电池',
        'unique_leixiang': '宁德时代=电池之王，对应木/寅',
        'key_association': '动力电池全球龙头',
        'code_dizhi': '巳', 'code_shishen': '太乙',
    },
    '688981': {
        'name': '中芯国际', 'wuxing': '火', 'industry': '芯片',
        'unique_leixiang': '中芯=晶圆代工，对应火/巳午',
        'key_association': '国产芯片代工龙头',
        'code_dizhi': '丑', 'code_shishen': '大吉',
    },
    '688012': {
        'name': '中微公司', 'wuxing': '火', 'industry': '芯片',
        'unique_leixiang': '中微=刻蚀设备，对应火/午',
        'key_association': '半导体设备龙头',
        'code_dizhi': '丑', 'code_shishen': '大吉',
    },
    
    # ═══════ 光伏新能源 ═══════
    '601012': {
        'name': '隆基绿能', 'wuxing': '水', 'industry': '光伏',
        'unique_leixiang': '隆基=光伏龙头，对应水/亥子',
        'key_association': '光伏组件全球龙头',
        'code_dizhi': '亥', 'code_shishen': '神后',
    },
    '002459': {
        'name': 'TCL中环', 'wuxing': '水', 'industry': '光伏',
        'unique_leixiang': 'TCL中环=硅片龙头，对应水/子',
        'key_association': '光伏硅片龙头',
        'code_dizhi': '卯', 'code_shishen': '太冲',
    },
    
    # ═══════ 医药龙头 ═══════
    '600276': {
        'name': '恒瑞医药', 'wuxing': '木', 'industry': '医药',
        'unique_leixiang': '恒瑞=创新药龙头，对应木/寅卯',
        'key_association': '创新药龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '300760': {
        'name': '迈瑞医疗', 'wuxing': '木', 'industry': '医疗器械',
        'unique_leixiang': '迈瑞=医疗器械龙头，对应木/卯',
        'key_association': '医疗器械全球龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    
    # ═══════ 消费龙头 ═══════
    '603288': {
        'name': '海天味业', 'wuxing': '木', 'industry': '食品',
        'unique_leixiang': '海天=酱油龙头，对应木/未',
        'key_association': '调味品龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '600887': {
        'name': '伊利股份', 'wuxing': '木', 'industry': '乳业',
        'unique_leixiang': '伊利=乳业龙头，对应木/丑',
        'key_association': '乳制品龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    
    # ═══════ 地产基建 ═══════
    '600048': {
        'name': '保利发展', 'wuxing': '土', 'industry': '地产',
        'unique_leixiang': '保利=地产龙头，对应土/辰戌',
        'key_association': '地产龙头',
        'code_dizhi': '辰', 'code_shishen': '天罡',
    },
    '601668': {
        'name': '中国建筑', 'wuxing': '土', 'industry': '基建',
        'unique_leixiang': '中建=基建龙头，对应土/辰',
        'key_association': '建筑工程龙头',
        'code_dizhi': '酉', 'code_shishen': '从魁',
    },
    
    # ═══════ 能源龙头 ═══════
    '601857': {
        'name': '中国石油', 'wuxing': '金', 'industry': '石油',
        'unique_leixiang': '中石油=油老大，对应金/酉',
        'key_association': '石油龙头',
        'code_dizhi': '午', 'code_shishen': '胜光',
    },
    '601088': {
        'name': '中国神华', 'wuxing': '金', 'industry': '煤炭',
        'unique_leixiang': '神华=煤龙头，对应金/申酉',
        'key_association': '煤炭龙头',
        'code_dizhi': '辰', 'code_shishen': '天罡',
    },
    
    # ═══════ 军工龙头 ═══════
    '600760': {
        'name': '中航沈飞', 'wuxing': '金', 'industry': '航空',
        'unique_leixiang': '沈飞=歼击机摇篮，对应金/申',
        'key_association': '航空制造龙头',
        'code_dizhi': '子', 'code_shishen': '登明',
    },
    '000768': {
        'name': '中航西飞', 'wuxing': '金', 'industry': '航空',
        'unique_leixiang': '西飞=运输机基地，对应金/酉',
        'key_association': '航空制造',
        'code_dizhi': '申', 'code_shishen': '传送',
    },
    
    # ═══════ 传媒互联网 ═══════
    '300059': {
        'name': '东方财富', 'wuxing': '火', 'industry': '金融科技',
        'unique_leixiang': '东财=互联网券商，对应火/巳午',
        'key_association': '互联网金融龙头',
        'code_dizhi': '申', 'code_shishen': '传送',
    },
    '300750_media': {
        'name': '东方财富', 'wuxing': '火', 'industry': '金融科技',
        'unique_leixiang': '东财=互联网券商，对应火/巳午',
        'key_association': '互联网金融龙头',
        'code_dizhi': '申', 'code_shishen': '传送',
        'note': '注意：300750实际是宁德时代，东方财富是300059'
    },
    
    # ═══════ 公用事业 ═══════
    '600900': {
        'name': '长江电力', 'wuxing': '水', 'industry': '电力',
        'unique_leixiang': '长电=水电龙头，对应水/亥子',
        'key_association': '水电龙头',
        'code_dizhi': '子', 'code_shishen': '登明',
    },
    '601985': {
        'name': '中国核电', 'wuxing': '水', 'industry': '电力',
        'unique_leixiang': '中核=核电龙头，对应水/子',
        'key_association': '核电龙头',
        'code_dizhi': '申', 'code_shishen': '传送',
    },
}


# ═══════════════════════════════════════════════════════════
# 6. 辅助函数
# ═══════════════════════════════════════════════════════════

def infer_industry_wuxing(name: str, industry: str = "") -> str:
    """从股票名称/行业推断五行（多级匹配：个股→板块→行业）"""
    import re
    
    # 第一级：精确匹配个股数据库
    # 通过代码或名称查找
    for code, info in STOCK_LEIXIANG_DATABASE.items():
        if info['name'] in name or code in name:
            return info['wuxing']
    
    # 第二级：从行业映射表匹配（精确优先）
    text = f"{name} {industry}"
    
    # 精确匹配优先（无正则符号的条目）
    exact_matches = []
    regex_matches = []
    
    for pattern, wx in INDUSTRY_WUXING.items():
        # 检查是否包含正则符号
        if '|' in pattern or '?' in pattern:
            regex_matches.append((pattern, wx))
        else:
            exact_matches.append((pattern, wx))
    
    # 先尝试精确匹配
    for pattern, wx in exact_matches:
        if pattern in text:
            return wx
    
    # 再尝试正则匹配（更长的模式优先）
    regex_matches.sort(key=lambda x: len(x[0]), reverse=True)
    for pattern, wx in regex_matches:
        if re.search(pattern, text):
            return wx
    
    return "土"  # 默认土


def get_sector_wuxing(sector_name: str) -> str:
    """获取板块五行属性"""
    import re
    
    # 精确匹配
    if sector_name in SECTOR_WUXING:
        return SECTOR_WUXING[sector_name]
    
    # 正则匹配
    for pattern, wx in SECTOR_WUXING.items():
        if re.search(pattern, sector_name):
            return wx
    
    return "土"


def get_stock_leixiang(stock_code: str) -> Optional[Dict]:
    """获取个股类象信息"""
    return STOCK_LEIXIANG_DATABASE.get(str(stock_code), None)


def search_stock_by_name(name: str) -> List[Dict]:
    """按名称搜索股票"""
    results = []
    for code, info in STOCK_LEIXIANG_DATABASE.items():
        if name in info['name'] or info['name'] in name:
            result = info.copy()
            result['code'] = code
            results.append(result)
    return results


def get_code_dizhi(code: str) -> Dict:
    """获取股票代码对应的地支和十二神"""
    code_str = str(code).strip()
    last_digit = code_str[-1] if code_str else '0'
    
    dizhi = CODE_DIZHI_MAP.get(last_digit, '子')
    shishen = DIZHI_SHISHEN_MAP.get(dizhi, '未知')
    tianjiang = DIZHI_TIANJIANG_MAP.get(dizhi, '未知')
    
    return {
        'code': code,
        'last_digit': last_digit,
        'dizhi': dizhi,
        'shishen': shishen,
        'tianjiang': tianjiang,
    }


def calculate_liuqin(day_gan: str, stock_wuxing: str) -> str:
    """计算六亲关系"""
    gan_wx = GAN_WUXING.get(day_gan, '土')
    
    # 日干生股票五行 → 子孙
    if SHENG_WUXING.get(gan_wx) == stock_wuxing:
        return '子孙(泄气)'
    # 股票五行生日干 → 父母
    elif SHENG_WUXING.get(stock_wuxing) == gan_wx:
        return '父母(得生)'
    # 日干克股票五行 → 妻财
    elif KE_WUXING.get(gan_wx) == stock_wuxing:
        return '妻财(财)'
    # 股票五行克日干 → 官鬼
    elif KE_WUXING.get(stock_wuxing) == gan_wx:
        return '官鬼(官)'
    # 同五行 → 兄弟
    else:
        return '兄弟(竞争)'


def get_stock_template(zhanshi_type: str) -> Optional[Dict]:
    """获取股票专用模板
    
    Args:
        zhanshi_type: 占事类型 ('股票预测', '大盘预测', '个股预测')
    
    Returns:
        模板字典或None
    """
    return STOCK_SPECIAL_TEMPLATES.get(zhanshi_type, None)


def get_all_stock_template_names() -> List[str]:
    """获取所有股票专用模板名称"""
    return list(STOCK_SPECIAL_TEMPLATES.keys())


def create_stock_template_context(stock_code: str, stock_name: str, 
                                   industry: str, day_gan: str) -> Dict:
    """创建股票模板上下文（支持个股数据库增强）
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        industry: 行业
        day_gan: 日干
    
    Returns:
        上下文字典
    """
    # 获取类象映射
    code_info = get_code_dizhi(stock_code)
    
    # 第一级：检查个股数据库
    stock_leixiang = get_stock_leixiang(stock_code)
    
    # 如果有个股数据库记录，使用其五行
    if stock_leixiang:
        industry_wuxing = stock_leixiang['wuxing']
        # 使用个股数据库中的地支信息（如果有）
        if stock_leixiang.get('code_dizhi'):
            code_info['dizhi'] = stock_leixiang['code_dizhi']
        if stock_leixiang.get('code_shishen'):
            code_info['shishen'] = stock_leixiang['code_shishen']
    else:
        # 第二级：推断行业五行
        industry_wuxing = infer_industry_wuxing(stock_name, industry)
    
    # 计算六亲
    liuqin = calculate_liuqin(day_gan, industry_wuxing)
    
    # 构建上下文
    context = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'industry': industry,
        'industry_wuxing': industry_wuxing,
        'code_dizhi': code_info['dizhi'],
        'code_shishen': code_info['shishen'],
        'code_tianjiang': code_info['tianjiang'],
        'liuqin': liuqin,
        'liuqin_meaning': WUXING_LIUQIN_MEANING.get(liuqin.split('(')[0], '未知'),
    }
    
    # 添加个股特有类象信息（如果有）
    if stock_leixiang:
        context['has_special_leixiang'] = True
        context['unique_leixiang'] = stock_leixiang.get('unique_leixiang', '')
        context['key_association'] = stock_leixiang.get('key_association', '')
    else:
        context['has_special_leixiang'] = False
        context['unique_leixiang'] = ''
        context['key_association'] = ''
    
    return context


def get_enhanced_industry_info(stock_code: str, stock_name: str, 
                                industry: str = "") -> Dict:
    """获取增强版行业信息（多级匹配）
    
    匹配顺序：个股数据库 → 行业映射 → 板块映射 → 默认
    
    Returns:
        包含匹配来源的详细信息
    """
    result = {
        'wuxing': '土',
        'source': 'default',
        'details': {}
    }
    
    # 1. 尝试个股数据库
    stock_info = get_stock_leixiang(stock_code)
    if stock_info:
        result['wuxing'] = stock_info['wuxing']
        result['source'] = 'stock_database'
        result['details'] = {
            'stock_name': stock_info['name'],
            'industry': stock_info['industry'],
            'unique_leixiang': stock_info.get('unique_leixiang', ''),
            'key_association': stock_info.get('key_association', ''),
        }
        return result
    
    # 2. 尝试行业映射
    wx = infer_industry_wuxing(stock_name, industry)
    if wx != '土':  # 非默认值
        result['wuxing'] = wx
        result['source'] = 'industry_mapping'
        return result
    
    # 3. 尝试板块映射
    if industry:
        sector_wx = get_sector_wuxing(industry)
        if sector_wx != '土':
            result['wuxing'] = sector_wx
            result['source'] = 'sector_mapping'
            return result
    
    # 4. 默认
    result['source'] = 'default'
    return result


def get_industry_wuxing_stats() -> Dict:
    """获取行业五行映射统计"""
    return {
        'industry_mappings': len(INDUSTRY_WUXING),
        'sector_mappings': len(SECTOR_WUXING),
        'stock_database': len(STOCK_LEIXIANG_DATABASE),
        'wuxing_distribution': {
            '金': sum(1 for v in INDUSTRY_WUXING.values() if v == '金'),
            '木': sum(1 for v in INDUSTRY_WUXING.values() if v == '木'),
            '水': sum(1 for v in INDUSTRY_WUXING.values() if v == '水'),
            '火': sum(1 for v in INDUSTRY_WUXING.values() if v == '火'),
            '土': sum(1 for v in INDUSTRY_WUXING.values() if v == '土'),
        }
    }
