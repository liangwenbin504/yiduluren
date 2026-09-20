"""
股票实时预测脚本 — 自动在交易前用大六壬预测当日走势
使用方法: python stock_daily_predict.py

流程:
1. 计算当前日柱(干支)、月将(太阳过宫)、占时(时辰)
2. 运行排盘引擎(四课+三传)
3. 调用DeepSeek API进行股票趋势推理
4. 保存预测结果到_memory/stock_predictions.json

交易结束后，用 stock_result_check.py 对照分析
"""
import json, time, os, sys, re, requests
from datetime import datetime, date, timezone, timedelta
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE, "_memory")
PREDICTIONS_FILE = os.path.join(MEMORY_DIR, "stock_predictions.json")

TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# ── 用户所在地配置（用于真太阳时校正）──
# 修改为你所在的省份和县/市，即可自动计算精确的真太阳时
USER_PROVINCE = "广东省"    # ← 请改为你所在的省份（如"北京市"、"上海市"、"广东省"）
USER_COUNTY = "深圳市"      # ← 请改为你所在的县/区（如"海淀区"、"浦东新区"、"深圳市"）

SHI_CHEN_MAP = {23: '子', 1: '丑', 3: '寅', 5: '卯', 7: '辰', 9: '巳', 11: '午', 13: '未', 15: '申', 17: '酉', 19: '戌', 21: '亥'}

YUE_JIANG_RULES = [
    (1, 20, '子'),   # 大寒(1/20) → 子将
    (2, 19, '亥'),   # 雨水(2/19) → 亥将
    (3, 21, '戌'),   # 春分(3/21) → 戌将
    (4, 20, '酉'),   # 谷雨(4/20) → 酉将
    (5, 21, '申'),   # 小满(5/21) → 申将
    (6, 21, '未'),   # 夏至(6/21) → 未将
    (7, 23, '午'),   # 大暑(7/23) → 午将
    (8, 23, '巳'),   # 处暑(8/23) → 巳将
    (9, 23, '辰'),   # 秋分(9/23) → 辰将
    (10, 23, '卯'),  # 霜降(10/23) → 卯将
    (11, 22, '寅'),  # 小雪(11/22) → 寅将
    (12, 22, '丑'),  # 冬至(12/22) → 丑将
]

TREND_CATEGORIES = ["涨", "跌", "平", "先涨后跌", "先跌后涨", "先涨后平", "先跌后平", "先平后涨", "震荡偏涨", "震荡偏跌"]
TREND_STR = "、".join(TREND_CATEGORIES)


def get_next_trading_day(from_date=None):
    """返回下一个交易日（跳过周末）"""
    if from_date is None:
        d = date.today()
    else:
        d = from_date
    d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d = d + timedelta(days=1)
    return d


def is_post_market(now=None):
    """判断当前是否在收盘后（15:00后 或 周末）"""
    if now is None:
        now = datetime.now()
    if now.weekday() >= 5:
        return True
    return now.hour >= 15


def is_pre_market(now=None):
    """判断当前是否在开盘前（工作日 09:30之前）"""
    if now is None:
        now = datetime.now()
    if now.weekday() >= 5:
        return False
    return now.hour < 9 or (now.hour == 9 and now.minute < 30)


def get_trading_session(now=None):
    """返回当前所处的交易时段标签"""
    if now is None:
        now = datetime.now()
    wd = now.weekday()
    if wd >= 5:
        return "周末休市", ""
    h, m = now.hour, now.minute
    if h < 9 or (h == 9 and m < 30):
        return "盘前", "09:30-11:30 / 13:00-15:00"
    if (h == 11 and m <= 30) or (h == 10) or (h == 9):
        return "上午盘", "09:30-11:30"
    if (h == 13) or (h == 14) or (h == 11) or (h == 12):
        return "下午盘", "13:00-15:00"
    if h >= 15:
        return "盘后", "次日 09:30-15:00"
    return "盘中", "09:30-15:00"

STOCK_RC_FIELDS = ["课体", "四课加临", "用神五气", "三传", "六亲分析", "天将分析", "五行", "旬空", "旺衰", "神煞", "刑冲合害", "八杀", "十二气财星", "身强身弱", "趋势判断", "应期", "风险提示"]

SYSTEM_PROMPT = f"""你是一个大六壬股票预测推理专家。你的任务是**按主干到枝叶的层次客观推理**，而非简单分类。

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

【推理步骤 — 17步完整链】
1. 课体定势: 先判断课体在股市中的象意（伏吟=盘整/迟滞，反吟=剧烈反转，涉害=多空博弈激烈，遥克=突发消息驱动，元首=趋势延续等），这是**最重要的一步**
2. 四课加临: 干上/支上分析益脱制损。⚠️月将临支上=「太阳照宅」→市场向阳大利好! 月将临干上=「太阳照身」→我方得势。配合三传吉更验
3. 用神五气: 发用的旺相休囚死状态决定行情的喜庆程度
4. 三传时序: 初→中→末的节奏变化，制救关系决定转折点。⚠️伏吟课中若带刑冲→「不动变必动」=反转信号！配合螣蛇(主动)、天喜(主涨)更验
5. 六亲力量: 财旺=资金充足但需身强来担，官鬼=主力控盘，父母=政策面
6. 天将动态解读: ⚠️天将不可死板一对一映射！天将的含义取决于【所乘何神 + 日干旺衰 + 临何种六亲】:

   【核心原则 — 天将之性随乘神而变】
   - 白虎: 乘财+日干旺相+德禄=「暴发」看涨 | 乘财+日干衰=暴跌 | 乘鬼+日干弱=恐慌
   - 青龙: 乘财+日干旺=主升浪 | 乘鬼+身弱=拉高出货/诱多 | 乘生干=反弹
   - 朱雀: 乘财+旺=利好公告大涨 | 乘鬼=利空恐慌 | 乘生干=政策暖风
   - 腾蛇: 乘财=洗盘后涨(惊中得财) | 乘鬼=假突破陷阱 | 乘空=虚惊一场
   - 腾蛇+天喜+刑冲(伏吟中): 「不动变必动」反转上涨信号!!
   - ⚠️ 月将(太阳之位)自带吉气: 凶将乘月将→凶性被太阳中和; 吉将乘月将→吉力倍增
   - 玄武: 乘财=暗盘资金流入 | 乘鬼=主力出货 | 乘生干=隐形利好
   - 勾陈: 乘财=蓄势待涨 | 乘鬼=盘整阻力 | 乘生干=筑底
   - 贵人: 乘财=主力托市 | 乘鬼=护盘无效 | 乘生干=国家队入场
   - 太阴/天后/太常: 乘财+日干旺=稳步上行 | 乘鬼=缓跌
   - 天空: 无论乘什么，多为虚象、利好落空
   - ⚠️ 关键: 日干12长生状态决定天将之力 = 长生/冠带/临官/帝旺→天将力强 | 死/墓/绝→天将无力

7. 五行流通: 三传五行生克链条，判断能量的传递方向
8. 旬空+日墓: 空亡则虚，日墓则滞。⚠️月将临墓=「太阳照墓」破暗向明≠利空！日鬼临月将=鬼被太阳制化(须使用排盘旬空)
9. 旺衰虚实: 先判身强与否(四大标准)，身强能担财→涨；身弱不胜财→涨势难继
10. 神煞点睛: 在主干判断基础上，追加神煞的强化/弱化效应（绝不能推翻课体判断）
11. 刑冲合害: ⚠️六壬规则: 地支本身不直接作用! 要透过上神!
   支(地盘)靠上神(天盘)行动→上神冲刑才是真冲刑!
   例: 支申上神未→未冲丑=真冲, 支申本身不冲寅!
   上神吉(乘吉将,天喜,德禄)→冲为吉; 上神凶→冲为凶。
   不可用八字五行直接推导地支间生克!
12. 八杀评分: 德合为吉、鬼墓破害刑冲为凶，综合评分
13. 十二气财星: 三传长生十二宫状态
14. 身强身弱 — 四大标准, 必须逐条查:
  ①坐旺: 日干在地盘临官/帝旺/长生位→身强
  ②乘旺: 干上神旺相(临官/帝旺/长生)→身强
  ③干上神不克不脱日干→旺气能存→身强
  ④下临生爻: 干下神(地盘)生日干→有根→身强
  ⚠️满足任一条即为身强! 不可仅凭"财旺"就判"身弱"!
  ⚠️丙坐巳=临官旺地, 巳为禄旺→身强担财! 绝不可误判!
  ⚠️六合环拱: 末传乘六合+生干=市场合力推涨, 大利好
15. 趋势判断: 综合以上，给出一致性最强的趋势预测
16. 应期: 关键时间节点
17. 风险提示】

【神煞速查表 — 按预测周期分层，不可遗漏】

⚠️ 本系统预测明日走势=短线 → 优先级: 日煞 > 月煞 > 季煞 > 年煞

┌─🔥日煞（今日占明日必查！时效最强）─────────────┐
│ 日德  │ 阳干自长生,阴干在合位 — 护盘/政策暖风   │
│       │ 甲寅/乙申/丙巳/丁亥/戊巳/己亥/庚申     │
│       │ 辛巳/壬亥/癸巳                        │
│ 日禄  │ 日干临官位 — 主力支撑/资金底仓          │
│       │ 甲寅/乙卯/丙戊巳/丁己午/庚申/辛酉       │
│       │ 壬亥/癸子    ⚠️禄+财=资金雄厚必涨!     │
│ 日马  │ 寅申巳亥(即驿马,短线时效更强)→快速突破  │
│ 日鬼  │ 克日干之神→主力打压  鬼临青龙+日旺=洗盘  │
│ 日墓  │ 日干墓库→动能衰竭/趋势终结              │
│ 日破  │ 日支相冲→盘中突变/转折                  │
│ 日合  │ 干支相合→趋势延续/资金抱团              │
├─📅月煞（叠加在日煞之上）──────────────────┤
│ 生气  │ 月建后二辰→生机/涨势恢复                │
│ 死气  │ 月建前二辰→衰竭/跌势持续                │
│ 天喜  │ 春戌/夏丑/秋辰/冬未 — 大利好!          │
│ 天德  │ 正月丁...→护盘           月德→多头人气  │
├─📆季煞/年煞（长周期参考）────────────────┤
│ 驿马     │ 寅申巳亥 — 快速变动/突破          │
│ 贵人     │ 主力托市/大盘企稳                  │
│ 羊刃     │ 极端波动/急涨急跌                  │
│ 破碎     │ 回调/崩盘风险                      │
│ 孤辰寡宿 │ 趋势孤单/无人接盘                  │
│ 劫煞     │ 资金劫夺/利空突袭                  │
│ 灾煞     │ 意外暴跌                          │
│ 桃花     │ 虚假繁荣/诱多                      │
│ 华盖     │ 高位筑顶/横盘整理                  │
│ 将星     │ 龙头股/领涨                        │
└────────────────────────────────────────────┘

⚠️ 日墓辩证: 日墓临传 ≠ 必然利空！若月将(太阳)临墓→「太阳照墓」→破暗向明！墓被照亮=向阳积极，反为吉象。同理日鬼临月将→鬼被太阳制化。

【毕法赋100条全本 — 每课自动匹配】

1.前后引从升迁吉  2.首尾相见始终宜  3.帘幕贵人高甲第  4.催官使者赴官期
5.六阳数足须公用  6.六阴相继尽昏迷  7.旺禄临身徒妄作  8.权摄不正禄临支
9.避难逃生须弃旧  10.朽木难雕别作为  11.众鬼虽彰全不畏  12.虽忧狐假虎威仪
13.鬼贼当时无畏忌  14.传财太旺反财亏  15.脱上逢脱防虚诈  16.空上乘空事莫追
17.进茹空亡宜退步  18.踏脚空亡进用宜  19.胎财生气妻怀孕  20.胎财死气损胎推
21.交车相合交关利  22.上下皆合两心齐  23.彼求我事支传干  24.我求彼事干传支
25.金日逢丁凶祸动  26.水日逢丁财动之  27.传财化鬼财休觅  28.传鬼化财钱险危
29.眷属丰盈居狭宅  30.屋宅宽广致人衰  31.三传递生人举荐  32.三传互克众人欺
33.有始无终难变易  34.苦去甘来乐里悲  35.人宅受脱俱招盗  36.干支皆败事倾颓
37.末助初兮三等论  38.闭口卦体两般推  39.太阳照武宜擒贼  40.后合占婚岂用媒
41.富贵干支逢禄马  42.尊崇传内遇三奇  43.害贵讼直作曲断  44.课传俱贵转无依
45.昼夜贵加求两贵  46.贵人差迭事参差  47.贵虽在狱宜临干  48.鬼乘天乙乃神祗
49.两贵受克难干贵  50.二贵皆空虚喜期  51.魁度天门关隔定  52.罡塞鬼户任谋为
53.两蛇夹墓凶难免  54.虎视逢虎力难施  55.所谋多拙逢网罗  56.天网自裹己招非
57.费有余而得不足  58.用破身心无所归  59.华盖覆日人昏晦  60.太阳射宅屋光辉
61.干乘墓虎无占病  62.支乘墓虎有伏尸  63.彼此全伤防两损  64.夫妇芜淫各有私
65.干墓并关人宅废  66.支坟财并旅程稽  67.受虎克神为病症  68.制鬼之位乃良医
69.虎乘遁鬼殃非浅  70.鬼临三四讼灾随  71.病符克宅全家患  72.丧吊全逢挂缟衣
73.前后逼迫难进退  74.空空如也事休追  75.宾主不投刑在上  76.彼此猜忌害相随
77.合中犯煞蜜中砒  78.死奇死绝祸难医  79.罗网遮身难动转  80.墓门开处哭声悲
81.龙战玄黄分胜负  82.三交暗遁谨防危  82b.三六合和喜沂宜(三传合局+通关=鬼被化解)  83.四绝之宫财不聚  84.五福齐聚百祥随
85.反吟冲动事多变  86.伏吟不动且徐徐  87.天乙加临刑害地  88.螣蛇入穴火焚躯
89.朱雀衔符文信至  90.六合私门暗昧居  91.勾陈克日争田土  92.青龙得水跃天衢
93.天空无物是空囊  94.白虎当途路险巇  95.太常宴乐酒食会  96.玄武阴私暗昧虚
97.太阴密谋潜动作  98.天后恩泽福有余  99.德神临日多喜庆  100.刑冲破害总非宜

股市简化映射:
1升迁=涨 14传财太旺=过热回调 19胎财生气=孕育利润看涨 20胎财死气=利润流产看跌
27传财化鬼=获利了结 28传鬼化财=危险利润 31递生=看涨 32递克=看跌
33有始无终=冲高回落 34苦去甘来=探底回升
51魁度天门=遇阻回落 52罡塞鬼户=无阻上涨 53两蛇夹墓=洗盘套牢
54虎视逢虎=暴跌无力 59华盖覆日=方向不明 60太阳射宅=向阳大涨
85反吟=剧烈反转 86伏吟=横盘整理 90六合环拱=市场合力推涨 91勾陈克日=阻力 92青龙得水=主升浪 94白虎当途=暴跌

⚠️ 每课自动扫描100条毕法赋：先看课体(伏吟→86/反吟→85)再看三传(31/32/27/28)再看神将(53/54/60/94)，最后综合。不确定条款注明「可能触发」。

【六亲股市映射】
父母→政策/消息面 | 妻财→资金/利润 | 官鬼→主力/风险
兄弟→板块/竞争 | 子孙→散户/成交量

【天将股市映射】
贵人→护盘 | 青龙→主升浪 | 白虎→暴跌 | 朱雀→消息驱动
玄武→出货陷阱 | 腾蛇→洗盘假突破 | 勾陈→横盘阻力
六合→并购合作 | 太常→业绩兑现 | 天空→利好落空
太阴→主力吸筹 | 天后→宽松流动性

【趋势类型】
涨/跌/平/先涨后跌/先跌后涨/先涨后平/先跌后平/先平后涨/先平后跌/震荡偏涨/震荡偏跌

【课体股市映射】
- 贼克→突发利好/利空，比用→板块轮动
- 涉害→多空博弈震荡，遥克→外围因素影响
- 昴星→庄家运作，别责→概念炒作
- 八专→独立行情，伏吟→横盘整理
- 返吟→剧烈反转

【⚠️ 反偏向指令（必须严格遵守）】
大六壬传统中存在"前程仕进偏向"（即断课时倾向于往吉/有利方向解释），这在股票预测中必须严格禁止：
1. **禁止乐观偏向**：不要因为"传统上喜欢断吉"就倾向于断"涨"。同样，也不要因为要"反传统"就无依据地断"跌"或"先涨后跌"。
2. **必须有据判断**：每一个判断都必须有排盘中的具体依据（哪个地支、哪个天将、哪个六亲），不能凭空说吉凶。
3. **如实输出**：推理支持"涨"就断"涨"，支持"跌"就断"跌"，支持"先跌后涨"就断"先跌后涨"。**不要将有明确依据的简单趋势改为复合趋势**。
4. **禁止默认选项**：没有所谓的"安全选项"。"先跌后涨"和"先涨后跌"不是默认选项。证据指向什么趋势就输出什么趋势。
5. **两条腿走路**：同时列出利多和利空因素，然后如实综合权衡——哪边证据更充分就信哪边。
6. **低振幅日判断（重要！）**：如果课象中旬空多、伏吟格、旺衰平衡无明显偏向时，当日大概率是平盘或窄幅震荡（振幅<0.5%）。此时应优先输出"平"、"震荡偏涨"或"震荡偏跌"，**禁止强行判断"涨"或"跌"等方向性趋势**。历史数据表明低振幅日强行判方向全部失误（0/5）。
7. **三传吉凶需结合大盘背景**：三传天将"凶多吉少"不代表必然下跌，若日干旺相得生、财星有力、课体为元首/铸印等吉课，即使三传初凶亦可上涨。历史数据中三传"凶多吉少"但大盘涨1%+的案例全部误判为"跌"。
8. **神煞不可遗漏**：每周神煞必须逐一查对——天喜（四季节气定位）、天德月德、驿马羊刃破碎等。神煞是枝叶不能推翻课体主干，但**遗漏天喜等强利好神煞是严重错误**。财爻临天喜="喜中得财"应优先考虑上涨方向。
9. **课体为干、三传为枝、神煞为叶**：课体定大势方向，三传定时序节奏，神煞微调信号强度。绝不可用枝叶否定主干，也不可遗漏枝叶信息。
10. **天将不可死板映射**：天将含义取决于【所乘何神 + 日干旺衰】。白虎乘财+日干旺=暴发看涨(非暴跌)；青龙乘鬼+身弱=拉高出货(非主升)；腾蛇乘财=惊中得财(洗盘后涨)。日干12长生: 长生/冠带/临官/帝旺=身强有力 | 死/墓/绝=身弱无力。

【趋势预测范围】
{TREND_STR}

【输出格式】
输出纯JSON，严格按以下模板：
{{"trend_prediction":"","jixiong":"","analysis":"","reasoning_chain":{{"课体":"","四课加临":"","用神五气":"","三传":"","六亲分析":"","天将分析":"","五行":"","旬空":"","旺衰":"","神煞":"","刑冲合害":"","八杀":"","十二气财星":"","身强身弱":"","趋势判断":"","应期":"","风险提示":""}}}}"""

# Phase 2: Stage 1 — 纯推理（不做分类）
STAGE1_SYSTEM_PROMPT = f"""你是一个大六壬股票预测推理专家。你的任务是进行**纯推理分析**，暂不做出最终趋势判断。

【核心要求】
当前是一个实时股票预测任务。请根据提供的排盘信息进行完整的大六壬推理（含《壬归》体系）。
逐项分析以下16个方面：
1. 课体 — 判断课体类型及其在股市中的象意
2. 四课加临 — 分析四课的益气/脱气/损气/制气关系（《壬归》卷之一·一）
3. 用神五气 — 分析发用的旺相休囚死状态（《壬归》卷之一·二）
4. 三传 — 分析初传→中传→末传的走势变化及三传制救（《壬归》卷之一·三）
5. 六亲分析 — 分析妻财（资金）、父母（政策）、官鬼（风险/主力）、兄弟（板块）、子孙（散户/成交量）
6. 天将分析 — 分析各天将的市场信号及贵神吉凶（《壬归》卷之一·四）
7. 五行 — 分析五行生克对趋势的影响
8. 旬空（空亡）——三传是否落空亡，空亡则事虚、趋势不可持续（⚠️ **必须使用排盘信息中给出的旬空，不要自行推算，推算错误会导致严重失准**）
9. 四季旺衰——三传五行的旺相休囚死状态，旺相则力强、休囚死则力弱
10. 神煞——天喜（喜中得财，春戌夏丑秋辰冬未）、天德月德（护盘）、贵人与破碎（涨跌生克）等信号
11. 刑冲克害三合六合——三传之间及与干支的刑冲克害关系，判断多空博弈力度
12. 八杀体系 — 判断德合鬼墓破害刑冲在课传中的表现（《壬归》卷之一·五）
13. 十二气财星 — 分析三传长生十二宫与财星的关系（《壬归》卷之三）
14. 身强身弱 — 判断日干旺衰与财星旺衰的关系（《壬归》卷之三）
15. 趋势判断 — 综合以上分析，列出利多和利空因素
16. 应期 — 分析时间节点（短线交易时段）
17. 风险提示 — 指出潜在风险

【⚠️ 反偏向指令（必须严格遵守）】
1. 禁止"前程仕进偏向"（乐观偏向）：不要因为传统喜欢断吉就倾向断"涨"。
2. 同样禁止悲观偏向：不要因为"反传统"就无依据地倾向断"跌"或复合趋势。
3. **如实分析**：利多因素多于利空就倾向看涨，反之看跌。不偏不倚。
4. **可以在推理末尾给出初步趋势倾向**（如"初步看涨""偏空""先跌后涨可能性大"），但不要输出JSON分类。
5. **低振幅日优先判平**：旬空多、伏吟、旺衰均衡时优先判断平盘/震荡。
6. **三传凶多吉少≠必然下跌**：需结合日干旺衰、课体吉凶、财星力度综判。

【输出要求】
- 输出为**纯文本格式**（不是JSON）
- 逐项分析，每项1-3句
- **可以**在推理末尾给出初步趋势倾向，但不要输出最终JSON分类"""

# Phase 2: Stage 2 — 基于推理做分类
STAGE2_SYSTEM_PROMPT = f"""你是一个大六壬股票预测专家。你的任务是基于已完成的推理分析，做出最终趋势判断。

【核心要求】
下面将提供一个完整的大六壬推理分析过程。请仔细阅读，然后：
1. 确认推理中的利多和利空因素权重
2. 综合权衡后，从以下趋势范围中选择最符合的一个
3. 给出一个明确的判断

【六亲股市映射】
- 父母→政策/消息面，妻财→资金流入/盈利
- 官鬼→风险/庄家，兄弟→板块联动，子孙→散户/成交量

【天将股市映射】
- 青龙→上涨趋势，白虎→暴跌，玄武→庄家陷阱
- 贵人→护盘，朱雀→消息，勾陈→横盘，腾蛇→洗盘

【⚠️ 反偏向指令（必须严格执行）】
1. 禁止"前程仕进偏向"——不要无依据地看涨。
2. 同时禁止悲观看跌偏向——推理说涨就是涨，不要强行转为跌。
3. **如实输出趋势**：如果Stage 1推理得出结论支持"涨"，就输出"涨"。不要画蛇添足改成"先跌后涨"或"先涨后跌"。
4. **禁止默认复合趋势**："先跌后涨"和"先涨后跌"不是安全默认选项。只有推理明确支持时才使用。
5. **你可以参考原始排盘信息验证推理结论**，但不要推翻推理中的核心证据。
6. **低振幅日判断（重要！）**：如果课象中旬空多、伏吟格、旺衰平衡，应优先判断为平盘或震荡，**禁止强行判断涨跌**。
7. **三传凶多吉少≠必然下跌**：若日干旺相、财星有力、吉课加持，即使三传初凶也可上涨。

【趋势预测范围】
{TREND_STR}

【输出格式】
纯JSON，严格按以下模板：
{{"trend_prediction":"","jixiong":"","analysis":"","reasoning_chain":{{"课体":"","四课加临":"","用神五气":"","三传":"","六亲分析":"","天将分析":"","五行":"","旬空":"","旺衰":"","神煞":"","刑冲合害":"","八杀":"","十二气财星":"","身强身弱":"","趋势判断":"","应期":"","风险提示":""}}}}"""  # noqa


def get_beijing_now():
    """获取当前北京时间"""
    utc_now = datetime.now(timezone.utc)
    beijing = utc_now + timedelta(hours=8)
    return beijing


def calc_rizhu(target_date):
    """根据公历日期计算干支日柱（基准: 1984-01-31 = 甲子日，经网上万年历验证）"""
    ref_date = date(1984, 1, 31)
    days = (target_date - ref_date).days
    gan = TIAN_GAN[days % 10]
    zhi = DI_ZHI[days % 12]
    return gan, zhi, f"{gan}{zhi}"


def calc_yuejiang(target_date):
    """根据节气计算月将（2026-08-17 清理：精确中气换将，与原固定日期表对齐口径）

    原固定公历日期表（YUE_JIANG_RULES）在节气时刻浮动年份会错 1 天；
    改为 engine/yuejiang_engine.YueJiangCalculator（sxtwl 精确中气），失败时降级旧表。
    """
    try:
        from engine.yuejiang_engine import YueJiangCalculator
        yj, _name = YueJiangCalculator().get_yuejiang_by_date(
            target_date.year, target_date.month, target_date.day)
        return yj
    except Exception:
        month = target_date.month
        day = target_date.day
        for m, d, jiang in YUE_JIANG_RULES:
            if month == 12 and day >= d:
                return jiang
            if month < m:
                prev_m, prev_d, prev_jiang = YUE_JIANG_RULES[month - 2 if month > 1 else 11]
                return prev_jiang
            if month == m and day >= d:
                return jiang
        idx = month - 2 if month >= 2 else 11
        return YUE_JIANG_RULES[idx][2]


def calc_shichen(hour):
    """根据当前小时计算时辰"""
    for start_hour, dz in SHI_CHEN_MAP.items():
        if hour >= start_hour:
            result = dz
    if hour < 1:
        return '子'
    return result


def format_paipan_text(engine_result, tianjiang_map, analysis_engine=None, ri_gan_zhi='', lunar_month=1):
    """格式化排盘文本用于prompt注入（含综合分析）"""
    sanchuan = engine_result['sanchuan']
    sike = engine_result['sike']
    tiandi_pan = engine_result['tiandi_pan']
    ri_gan = engine_result.get('ri_gan', '')
    ri_zhi = engine_result.get('ri_zhi', '')

    sike_strs = []
    for i, ke in enumerate(sike, 1):
        if isinstance(ke, dict):
            top = ke.get('top', ke.get('shang', ''))
            bottom = ke.get('bottom', ke.get('xia', ''))
        elif isinstance(ke, (list, tuple)):
            top = ke[1] if len(ke) > 1 else ke[0]
            bottom = ke[-1]
        else:
            top, bottom = str(ke), ''
        sike_strs.append(f"第{i}课: {top}→{bottom}")

    chuan_list = [sanchuan.get(k, '') for k in ['初传', '中传', '末传']]
    chuan_with_tj = []
    for chuan in chuan_list:
        tj = tianjiang_map.get(chuan, '')
        chuan_with_tj.append(f"{chuan}({tj})" if tj else chuan)

    xun_kong_str = ''
    if analysis_engine and ri_gan_zhi:
        xk = analysis_engine.get_xun_kong(ri_gan_zhi)
        if xk:
            xun_kong_str = f"  旬空（空亡）：{'、'.join(xk)}"

    lines = [
        "【排盘信息】（由计算引擎提供，保证正确）",
        f"  日柱：{ri_gan}{ri_zhi}",
        f"  月将：{engine_result.get('yue_jiang', '')}  占时：{engine_result.get('shi_chen', '')}",
        f"  课体：{sanchuan.get('课体', '')}",
        f"  四课：{' | '.join(sike_strs)}",
        f"  三传：{' → '.join(chuan_with_tj)}",
        f"  发用：{sanchuan.get('起法', '')}",
    ]
    if xun_kong_str:
        lines.insert(3, xun_kong_str)

    if analysis_engine and ri_gan_zhi:
        analysis = analysis_engine.analyze(
            ri_gan=ri_gan, ri_zhi=ri_zhi,
            sanchuan=sanchuan, sike=sike,
            tiandi_pan=tiandi_pan,
            yue_jiang=engine_result.get('yue_jiang', ''),
            shi_chen=engine_result.get('shi_chen', ''),
            lunar_month=lunar_month,
            ri_gan_zhi=ri_gan_zhi
        )
        lines.append("")
        lines.append("【综合排盘分析】")
        lines.append(analysis['综合描述'])
        lines.append("")
        lines.append("【《壬归》深入分析】")
        lines.append(analysis.get('壬归总结', ''))

    return "\n".join(lines)


def get_stock_prediction_prompt(paipan_text, rizhu="", shi_chen="", session_label="上午盘", session_desc="09:30-11:30", target_date_str=""):
    """构建股票预测的完整prompt（动态注入日柱、时辰、时段、目标日期）"""
    date_hint = f"\n目标日期：{target_date_str}" if target_date_str else ""
    user_content = f"""请对以下大六壬排盘进行股票走势预测。

预测对象：上证指数（000001）
预测时段：{session_label}（{session_desc}）
预测日期：{rizhu}日 {shi_chen}时{date_hint}

{paipan_text}

请按以下推理链进行完整推理（含《壬归》深入分析）：
1. 课体：判断课体类型及其在股市中的象意
2. 四课加临：分析四课的益气/脱气/损气/制气关系（《壬归》卷之一·一）
3. 用神五气：分析发用的旺相休囚死状态（《壬归》卷之一·二）
4. 三传：分析初传→中传→末传的走势变化及三传制救（《壬归》卷之一·三）
5. 六亲分析：分析妻财（资金）、父母（政策）、官鬼（风险/主力）、兄弟（板块）、子孙（散户/成交量）
6. 天将分析：分析各天将的市场信号及贵神吉凶（《壬归》卷之一·四）
7. 五行：分析五行生克对趋势的影响
8. 八杀体系：判断德合鬼墓破害刑冲在课传中的表现（《壬归》卷之一·五）
9. 十二气财星：分析三传长生十二宫与财星的关系（《壬归》卷之三）
10. 身强身弱：判断日干旺衰与财星旺衰的关系（《壬归》卷之三）
11. 趋势判断：综合以上分析给出趋势结论
12. 应期：分析时间节点（短线交易时段）
13. 风险提示：指出潜在风险

输出纯JSON格式。"""
    return user_content


def call_api_stage1(user_content):
    """Stage 1: 纯推理分析（深度思考模式，可给出初步趋势倾向）"""
    messages = [
        {"role": "system", "content": STAGE1_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    payload = {"model": MODEL, "messages": messages, "temperature": 0.2, "max_tokens": 2000,
               "thinking": {"type": "enabled"}, "reasoning_effort": "high"}
    return _api_call(payload)


def call_api_stage2(stage1_reasoning, temperature=0.4, raw_text=""):
    """Stage 2: 基于推理+原始排盘做分类（非思考模式，省钱且快）"""
    extra_context = ""
    if raw_text:
        extra_context = "\n\n【原始排盘信息】\n" + raw_text[:300]
    user_content = f"""【第一阶段推理结果】\n{stage1_reasoning}\n\n{extra_context}\n\n【任务】基于上述推理（可参考原始排盘验证），请做出最终趋势判断。输出纯JSON格式。"""
    messages = [
        {"role": "system", "content": STAGE2_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    payload = {"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": 1500,
               "thinking": {"type": "disabled"}, "response_format": {"type": "json_object"}}
    return _api_call(payload)


def _api_call(payload, max_retries=3):
    """底层API调用（带自动重试，指数退避）"""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    retryable_http = {429, 500, 502, 503, 504}
    last_err = ""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message'].get('content', '').strip()
                return True, content
            if resp.status_code in retryable_http:
                last_err = f"http_{resp.status_code}"
                if attempt < max_retries:
                    wait = 2 ** attempt
                    print(f"  [重试] {last_err}，{wait}s后第{attempt+1}次重试...", flush=True)
                    time.sleep(wait)
                    continue
                return False, last_err
            return False, f"http_{resp.status_code}"
        except requests.exceptions.Timeout:
            last_err = "timeout"
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  [重试] 请求超时，{wait}s后第{attempt+1}次重试...", flush=True)
                time.sleep(wait)
                continue
            return False, f"err:timeout"
        except requests.exceptions.ConnectionError:
            last_err = "connection_error"
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  [重试] 连接失败，{wait}s后第{attempt+1}次重试...", flush=True)
                time.sleep(wait)
                continue
            return False, f"err:connection_error"
        except Exception as e:
            return False, f"err:{e}"
    return False, f"err:{last_err}"


def call_api_single(user_content):
    """备选方案：单阶段调用（降级）"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    payload = {"model": MODEL, "messages": messages, "temperature": 0.3, "max_tokens": 2000}
    return _api_call(payload)


def parse_json(text):
    if not text or not text.strip():
        return None
    try:
        d = json.loads(text)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    t = text.strip()
    m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', t)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    for m in re.finditer(r'```(?:json)?\s*\n?(\{.*?\})\n?```', text, re.DOTALL):
        try:
            d = json.loads(m.group(1))
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    i, j = t.find('{'), t.rfind('}')
    if i != -1 and j != -1 and j > i:
        candidate = t[i:j + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
        try:
            return json.loads(candidate.replace("'", '"'))
        except Exception:
            pass
    return None


def validate_prediction(data):
    trend = (data.get("trend_prediction") or "").strip()
    jx = (data.get("jixiong") or "").strip()
    rc = data.get("reasoning_chain") or {}
    rc_filled = 0
    rc_out = {}
    if isinstance(rc, dict):
        for f in STOCK_RC_FIELDS:
            v = rc.get(f, "")
            rc_out[f] = (v if isinstance(v, str) else "").strip()
            if rc_out[f]:
                rc_filled += 1
    ok = bool(trend and trend in TREND_CATEGORIES and (
        jx in ("吉", "凶", "中平", "大吉", "大凶", "小吉", "小凶", "平") or
        "藏" in jx or
        "后" in jx or
        "转" in jx
    ))
    return {"valid": ok, "trend_prediction": trend, "jixiong": jx,
            "analysis": data.get("analysis", ""), "rc": rc_out, "rc_filled": rc_filled}


def save_prediction(prediction_entry):
    """保存预测结果到记忆文件"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    predictions = []
    if os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                predictions = json.load(f)
                if not isinstance(predictions, list):
                    predictions = []
        except Exception:
            predictions = []
    # upsert：同 id 视为同一次运行（同分钟重复触发/调度重复），保留第一条、跳过后续，
    # 杜绝 REALTIME_YYYYMMDD_HHMM 同一分钟内被写出两条重复记录。
    eid = prediction_entry.get("id")
    if eid is not None and any((p or {}).get("id") == eid for p in predictions):
        print(f"  [去重] id={eid} 已存在，跳过重复写入（保留首次）", flush=True)
    else:
        predictions.append(prediction_entry)
    tmp_file = PREDICTIONS_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, PREDICTIONS_FILE)
    except Exception as e:
        print(f"  [ERROR] save failed: {e}", flush=True)


def _prediction_exists(category: str, target_date: str) -> bool:
    """检查给定类别是否已有同一目标日期的预测"""
    if os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for p in data:
                    if p.get("category") == category and p.get("target_date") == target_date:
                        return True
        except Exception:
            pass
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="大六壬股票预测 — 十一分类实验")
    parser.add_argument("--category", choices=["fixed_time", "ri_gan_pian_cai", "ri_zhi_pian_cai", "ri_gan_shi_shen", "ri_zhi_shi_shen", "ri_gan_zheng_yin", "ri_gan_pian_yin", "ri_zhi_zheng_yin", "ri_zhi_pian_yin", "random", "manual"],
                        default="fixed_time", help="预测类别")
    parser.add_argument("--shi-chen", default="", help="手动指定时辰（仅 manual 模式有效，如 子丑寅卯辰巳午未申酉戌亥）")
    args = parser.parse_args()
    category = args.category

    label_map = {
        "fixed_time": "固定时辰课", "ri_gan_pian_cai": "日干偏财时", "ri_zhi_pian_cai": "日支偏财时",
        "ri_gan_shi_shen": "日干食神时", "ri_zhi_shi_shen": "日支食神时",
        "ri_gan_zheng_yin": "日干正印时", "ri_gan_pian_yin": "日干偏印时",
        "ri_zhi_zheng_yin": "日支正印时", "ri_zhi_pian_yin": "日支偏印时",
        "random": "随机课", "manual": "人工指定时",
    }
    print("=" * 60, flush=True)
    print(f"大六壬股票实时预测系统 — {label_map[category]}", flush=True)
    print("=" * 60, flush=True)

    now = get_beijing_now()
    target_date_str = now.strftime('%Y-%m-%d')
    target_date_str_target = get_next_trading_day(now.date()).strftime('%Y-%m-%d')

    # ── 一天一课防重复 ──
    if _prediction_exists(category, target_date_str_target):
        label = label_map[category]
        print(f"\n  ⚠️  「{label}」已有 {target_date_str_target} 的预测，一天仅限一占！", flush=True)
        print(f"  💡 如需重新预测请等待次日", flush=True)
        return
    print(f"\n当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})", flush=True)

    # ── 真太阳时校正 ──
    from engine.solar_time import get_true_solar_time, format_solar_report
    solar = get_true_solar_time(USER_PROVINCE, USER_COUNTY, now)
    print(f"\n{format_solar_report(solar)}", flush=True)

    today = now.date()
    ri_gan, ri_zhi, rizhu = calc_rizhu(today)
    
    # ── 十神时辰映射：根据日干/日支+类别确定正确的时辰地支 ──
    from engine.ganzhi_shishen import get_shichen_for_category, print_shichen_table
    
    # 默认时辰：真太阳时校正后的当前时辰（固定时辰/随机课使用）
    default_shi_chen = solar["shi_chen"]
    if args.shi_chen and args.shi_chen in DI_ZHI:
        default_shi_chen = args.shi_chen
    
    # 根据预测类别确定实际起课时辰
    if category == 'random':
        import random as _random
        shi_chen = _random.choice(DI_ZHI)
    else:
        shi_chen = get_shichen_for_category(category, ri_gan, ri_zhi, default_shi_chen)
    yue_jiang = calc_yuejiang(today)

    print(f"\n【排盘参数】", flush=True)
    print(f"  日柱: {rizhu}（{ri_gan}干{ri_zhi}支）", flush=True)
    print(f"  月将: {yue_jiang}将", flush=True)
    if category in ('fixed_time', 'random', 'manual'):
        if args.shi_chen and args.shi_chen in DI_ZHI:
            print(f"  占时: {shi_chen}时（手动指定）", flush=True)
        else:
            print(f"  占时: {shi_chen}时（真太阳时）", flush=True)
    else:
        print(f"  占时: {shi_chen}时（{label_map[category]}专属时辰）", flush=True)

    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    from engine.liuren_analysis_engine import LiurenAnalysisEngine

    print(f"\n【引擎排盘】", flush=True)
    engine = SiKeSanChuanCalculator2()
    result = engine.calculate(ri_gan, ri_zhi, yue_jiang, shi_chen)

    sanchuan = result['sanchuan']
    sike = result['sike']
    tiandi_pan = result['tiandi_pan']

    print(f"  天地盘: {tiandi_pan}", flush=True)
    print(f"  课体: {sanchuan.get('课体', '')}", flush=True)
    print(f"  发用: {sanchuan.get('起法', '')}", flush=True)

    sike_display = []
    for ke in sike:
        if isinstance(ke, dict):
            sike_display.append(f"{ke.get('top','?')}→{ke.get('bottom','?')}")
        else:
            sike_display.append(str(ke))
    print(f"  四课: {' | '.join(sike_display)}", flush=True)

    chuan_list = [sanchuan.get(k, '') for k in ['初传', '中传', '末传']]
    print(f"  三传: {' → '.join(chuan_list)}", flush=True)

    gui_calc = GuiRenCalculator()
    gui_ren_result = gui_calc.arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shi_chen)
    tianjiang_map = gui_ren_result['天将映射']
    chuan_with_tj = []
    for chuan in chuan_list:
        tj = tianjiang_map.get(chuan, "")
        chuan_with_tj.append(f"{chuan}({tj})" if tj else chuan)
    print(f"  三传天将: {' → '.join(chuan_with_tj)}", flush=True)

    lunar_month = today.month
    analysis_engine = LiurenAnalysisEngine()
    paipan_text = format_paipan_text(result, tianjiang_map, analysis_engine, rizhu, lunar_month)

    session_label, session_desc = get_trading_session(now)
    user_content = get_stock_prediction_prompt(paipan_text, rizhu, shi_chen, session_label, session_desc, target_date_str_target)

    print(f"\n【调用DeepSeek API进行预测 — 两阶段推理+自洽性投票】", flush=True)
    print(f"  模型: {MODEL}", flush=True)

    # Stage 1: 纯推理
    print(f"  Stage 1: 推理分析...", flush=True)
    ok1, stage1_reasoning = call_api_stage1(user_content)
    if not ok1:
        print(f"  [WARN] Stage 1失败: {stage1_reasoning}，降级到单阶段", flush=True)
        ok, response = call_api_single(user_content)
        if not ok:
            print(f"  [ERROR] API调用失败: {response}", flush=True)
            print(f"\n❌ 预测失败，请稍后重试", flush=True)
            return
        single_stage_mode = True
    else:
        print(f"  Stage 1完成: {len(stage1_reasoning)}字符", flush=True)
        single_stage_mode = False

    # Stage 2: 自洽性投票
    if not single_stage_mode:
        vote_temps = [0.05, 0.1, 0.2]
        stage2_results = []
        for temp in vote_temps:
            ok2, resp2 = call_api_stage2(stage1_reasoning, temperature=temp, raw_text=user_content)
            if ok2:
                data = parse_json(resp2)
                if data:
                    trend = data.get("trend_prediction", "").strip()
                    if trend in TREND_CATEGORIES:
                        stage2_results.append((temp, data, trend))
                        print(f"  Stage 2 T={temp}: trend={trend}", flush=True)
                    else:
                        print(f"  Stage 2 T={temp}: invalid trend='{trend}'", flush=True)
                else:
                    print(f"  Stage 2 T={temp}: parse failed", flush=True)
            else:
                print(f"  Stage 2 T={temp}: {resp2}", flush=True)

        if stage2_results:
            from engine.online_learner import get_weighted_winner
            raw_trends = [r[2] for r in stage2_results]
            from collections import Counter
            raw_counter = Counter(raw_trends)
            winner, weighted_votes, is_unanimous = get_weighted_winner(
                [(r[0], r[2]) for r in stage2_results]
            )
            # 构建逐温度详情
            vote_detail = {}
            for temp, _, trend in stage2_results:
                vote_detail[f"t{temp}"] = trend
            # 选择winner中rc_filled最高的
            best_data = None
            best_rc = -1
            for _, data, trend in stage2_results:
                if trend == winner:
                    v = validate_prediction(data)
                    if v["rc_filled"] > best_rc:
                        best_rc = v["rc_filled"]
                        best_data = data
            data = best_data
            print(f"  原始投票: {dict(raw_counter)}", flush=True)
            print(f"  加权投票: {weighted_votes} → winner={winner} (unanimous={is_unanimous})", flush=True)
        else:
            # 投票失败，尝试单阶段
            ok, response = call_api_single(user_content)
            if not ok:
                print(f"  [ERROR] API调用失败: {response}", flush=True)
                print(f"\n❌ 预测失败，请稍后重试", flush=True)
                return
            data = parse_json(response)
            single_stage_mode = True
    else:
        data = parse_json(response)

    if not data:
        print(f"  [ERROR] JSON解析失败", flush=True)
        print(f"  原始响应: {response[:500] if 'response' in dir() else stage1_reasoning[:500]}", flush=True)
        return

    v = validate_prediction(data)
    if not v["valid"]:
        print(f"  [WARN] 格式验证未完全通过: trend={v['trend_prediction']}, jx={v['jixiong']}", flush=True)

    print(f"\n{'=' * 60}", flush=True)
    print(f"【预测结果】", flush=True)
    print(f"  趋势预测: {v['trend_prediction']}", flush=True)
    print(f"  吉凶判断: {v['jixiong']}", flush=True)

    # ── 统一训练库自进化修正 ──
    evo_data = {'evo_boost': 0, 'corrections': []}
    try:
        from unified_trainer import get_trainer
        trainer = get_trainer()
        # 提取纯天将名列表（去掉括号中的地支）
        tianjiang_list = []
        for ctj in chuan_with_tj:
            import re as _re
            m = _re.search(r'\((.+)\)', ctj)
            tianjiang_list.append(m.group(1) if m else ctj)
        keti = sanchuan.get('课体', '')
        # 计算修正分
        fs, fr = trainer.get_factor_impacts(chuan_list, tianjiang_list, v['jixiong'], v['trend_prediction'])
        cs, cr = trainer.apply_corrections(keti, chuan_list, tianjiang_list, ri_gan + ri_zhi)
        evo_boost = fs + cs
        evo_data = {
            'evo_boost': evo_boost,
            'factor_impacts': fr,
            'corrections_applied': cr,
            'trainer_summary': trainer.get_summary(),
        }
        # 强修正信号：自进化规则强烈翻转判断
        if evo_boost >= 5:
            is_bullish = '涨' in v['trend_prediction'] or v['jixiong'] == '吉'
            if is_bullish:
                v['confidence_adj'] = f'+{evo_boost}(自进化强化看涨)'
            else:
                v['confidence_adj'] = f'+{evo_boost}(自进化修正偏空→偏多)'
            if v['jixiong'] == '凶' and evo_boost >= 5:
                v['jixiong'] = '中平'
                v['trend_prediction'] = '震荡偏涨' if v['trend_prediction'] in ('跌', '凶') else v['trend_prediction']
                print(f"  🔄 [自进化修正] 评分+{evo_boost}→吉凶:凶→{v['jixiong']} 趋势→{v['trend_prediction']}", flush=True)
        elif evo_boost >= 3:
            v['confidence_adj'] = f'+{evo_boost}(自进化偏多修正)'
            print(f"  📝 [自进化参考] 评分+{evo_boost}, 建议关注{fr if fr else cr}", flush=True)
        elif evo_boost <= -3:
            v['confidence_adj'] = f'{evo_boost}(自进化偏空提示)'
            print(f"  ⚠️ [自进化风险] 评分{evo_boost}, 建议谨慎", flush=True)
    except Exception as e:
        try: print(f"  [自进化修正跳过] {e}", flush=True)
        except: pass
        evo_data = {'evo_boost': 0, 'error': str(e)}

    print(f"  综合分析: {v['analysis'][:200] if v['analysis'] else '无'}", flush=True)

    print(f"\n【推理链】({v['rc_filled']}/{len(STOCK_RC_FIELDS)})", flush=True)
    for field in STOCK_RC_FIELDS:
        content = v['rc'].get(field, "")
        if content:
            print(f"  [{field}] {content[:150]}", flush=True)

    prediction_entry = {
        "id": f"REALTIME_{now.strftime('%Y%m%d_%H%M')}",
        "category": category,
        "predict_time": now.strftime('%Y-%m-%d %H:%M:%S'),
        "predict_session": session_label,
        "target": "上证指数(000001)",
        "date": now.strftime('%Y-%m-%d'),
        "target_date": target_date_str_target,
        "rizhu": rizhu,
        "yue_jiang": yue_jiang,
        "shi_chen": shi_chen,
        "keti": sanchuan.get('课体', ''),
        "fayong": sanchuan.get('起法', ''),
        "sike": sike_display,
        "sanchuan": chuan_list,
        "sanchuan_tianjiang": chuan_with_tj,
        "trend_prediction": v['trend_prediction'],
        "jixiong": v['jixiong'],
        "analysis": v['analysis'],
        "reasoning_chain": v['rc'],
        "rc_filled": v['rc_filled'],
        "stage1_reasoning": stage1_reasoning if not single_stage_mode else "",
        "vote_result": weighted_votes if not single_stage_mode and stage2_results else {},
        "vote_detail": vote_detail if not single_stage_mode and stage2_results else {},
        "method": "two_stage_voting" if not single_stage_mode else "single_stage",
        "raw_response": response if single_stage_mode else str(stage2_results),
        "actual_result": None,
        "status": "pending",
        "evo_correction": evo_data  # 自进化修正记录
    }

    save_prediction(prediction_entry)
    print(f"\n✅ 预测已保存到: {PREDICTIONS_FILE}", flush=True)

    # ── 虚拟自动交易 ──
    try:
        from engine.virtual_trader import VirtualTrader
        trader = VirtualTrader(category)

        ref_price = 4100.0
        if v.get("actual_details") and v["actual_details"].get("prev_close"):
            ref_price = v["actual_details"]["prev_close"]
        elif v.get("details") and v["details"].get("prev_close"):
            ref_price = v["details"]["prev_close"]
        else:
            import akshare as ak
            try:
                df = ak.stock_zh_index_daily(symbol="sh000001")
                ref_price = float(df.iloc[-1]["close"])
                print(f"  从akshare获取上证收盘价: {ref_price}", flush=True)
            except Exception:
                try:
                    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                        exists = json.load(f)
                    last_details = None
                    for p in reversed(exists):
                        if p.get("actual_details") and p["actual_details"].get("price"):
                            last_details = p["actual_details"]
                            break
                    if last_details:
                        ref_price = last_details["price"]
                        print(f"  从历史预测取最近收盘价: {ref_price}", flush=True)
                    else:
                        print(f"  使用默认参考价: {ref_price}", flush=True)
                except Exception:
                    print(f"  使用默认参考价: {ref_price}", flush=True)

        trader.after_predict(prediction_entry, ref_price)

        # 将交易状态写回预测文件
        try:
            PREDICTIONS_PATH = os.path.join(MEMORY_DIR, "stock_predictions.json")
            with open(PREDICTIONS_PATH, "r", encoding="utf-8") as f:
                all_preds = json.load(f)
            pred_id = prediction_entry.get("id", "")
            for p in all_preds:
                if p.get("id") == pred_id:
                    p["trade_executed"] = True
                    p["trade_detail"] = {
                        "ref_price": ref_price,
                        "trade_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    break
            tmp = PREDICTIONS_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(all_preds, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, PREDICTIONS_PATH)
        except Exception:
            pass
    except Exception as e:
        print(f"  [WARN] 虚拟交易引擎异常: {e}", flush=True)

    print(f"\n{'=' * 60}", flush=True)
    print(f"等待交易结果...", flush=True)
    print(f"  交易结束后运行: python stock_result_check.py {today}", flush=True)
    print(f"{'=' * 60}", flush=True)


if __name__ == "__main__":
    main()
