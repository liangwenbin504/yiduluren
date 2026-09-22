# -*- coding: utf-8 -*-
"""
现代类象链推演器 (engine/leixiang_chain.py)
==========================================
把赵林声（南山道人）《大六壬课例》的断课法工程化为可执行算法：

    课象 → ① 类神锚定 → ② 阴神链展开 → ③ 现代象映射 → ④ 收敛输出

🔴 **边界（铁律）**：纯【叙事层】。只定「是什么事」，**不赋吉凶、不进评分链**
   （M3 89.4% / B1 99.5% / B2 97.8% / 毕法赋 21:0 / 课体 32:0 一律不动）。
🔴 **环境所断**：赵师原话「此是赵师的环境所断，其他环境不能这么断」（课例-28）
   → 输出一律标「参考/待验证」，**跨占类不得泛化**。
🟡 **样本规模**：北大课例 31 题中仅 18 题有正文，不足以支撑任何权重或 valence。

数据源
------
- 现代象映射：内嵌 MODERN_XIANG / JIANG_XIANG / COMBO_XIANG（自北大课例抽取，
  结构化全文见 `_memory/beida_kege_cases.json`）
- 古法类象：`engine/liuren_leixiang_knowledge.SHENJIANG_LEIXIANG`（可选）
- 全宫天将盘：`engine/kege_shensha.tian_jiang_pan`（2026-09-11 真源，8640 对证零差异）
- 遁干：`engine/bifa_detector.get_dun_gan`（甲午旬 午甲/未乙/申丙/酉丁 = 课例-15 实证）

关键定义
--------
- 天地盘 `tiandi_pan` = `{地盘宫位: 天盘支}`
- **阴神(X) = tiandi_pan[X]**（以 X 为地盘宫，取该宫天盘上神；四课第二/四课即此法）
- **坐宫(X)** = 反查 X 所临的地盘宫（X 坐在哪个宫上）
- 伏吟（天盘=地盘）时 阴神(X)==X → 自动断链
"""
from typing import Any, Dict, List, Optional, Tuple

DIZHI = list('子丑寅卯辰巳午未申酉戌亥')
TIANGAN = list('甲乙丙丁戊己庚辛壬癸')

# ═══════════════ 一、现代象表（自北大课例 18 课 + 推演表抽取） ═══════════════
# 标注口径（与 docs/现代事物六壬类象推演表.md 一致）：
#   ✓ = 课例原文直接出现（本题直接引用），△ = 推演待验证

MODERN_XIANG: Dict[str, List[str]] = {
    '戌': ['网络（火库=信息）✓', '狗✓', '财库/银行（乘青龙）✓', '陶瓷/圆物✓',
           '坟墓/墓✓', '块状→胃✓', '数5✓', '库/盒子✓'],
    '卯': ['车✓', '手机✓', '手✓', '门户✓', '药', '佛珠（乘太常遁乙）✓', '树✓', '舟车'],
    '酉': ['玉器/酒具✓', '咽喉✓', '贵重物件✓', '苹果（圆的精致）✓', '桃花✓',
           '碑石', '天医/丧门✓', '刀剑△'],
    '辰': ['水库/墙✓', '大海✓', '网络/信息✓', '证据（乘勾陈）✓', '老家（三课为宅）✓', '田土'],
    '申': ['道路/传送✓', '飞机（乘青龙落空）✓', '警察（乘青龙/太岁）✓', '针灸✓',
           '剑（青龙宝剑）✓', '传递/伸'],
    '午': ['心脏✓', '眼睛（落空）✓', '文书/文明✓', '桃花✓', '马✓', '脸面✓', '光明'],
    '巳': ['热水管道（螣蛇+青龙+癸）✓', '炉灶', '吃喝/胃口（乘太常）✓', '天医/吊客✓',
           '门面店铺✓', '信息/文明✓', '电器/电△', '四（数）✓'],
    '寅': ['肝脏✓', '文书', '道士/文化文艺✓', '猫（乘玄武）✓', '鬼门/木头✓', '官吏', '大树✓'],
    '子': ['取款机（小片）✓', '水', '小孩✓', '妻财✓', '渔屠'],
    '丑': ['金库✓', '腹部✓', '田园', '僧尼'],
    '亥': ['房屋（父母临长生）✓', '酒✓', '天门✓', '大海/水边✓', '幼小/小孩✓'],
    '未': ['财✓', '宴席', '警察（+太岁+勾陈）✓', '羊', '亲族'],
}

JIANG_XIANG: Dict[str, List[str]] = {
    '朱雀': ['银行卡✓', '信息/标签✓', '打电话✓', '吵闹/打架✓', '吹牛说大话（落空）✓', '文书/口舌'],
    '玄武': ['骗子✓', '盗贼✓', '说假话✓', '下贱之神✓', '偷盗/丢失环境✓', '暗昧',
             '诈骗（入墓=水平不高）✓'],
    '勾陈': ['警察（+太岁）✓', '打斗/有心机✓', '带把的东西✓', '迟滞/纠缠', '田土诉讼',
             '勾搭（+空=虚）✓'],
    '白虎': ['病✓', '催官使者（测官）✓', '道路✓', '老虎机（+午）✓', '过硬✓', '刑伤/血光'],
    '青龙': ['财/大财库✓', '纸钱煞✓', '催官/事业大✓', '升天（落空=前景广阔）✓', '喜庆'],
    '太常': ['吃喝/酒✓', '标签/牌子✓', '衣服✓', '宴席✓', '条状长的✓', '印绶/武职'],
    '螣蛇': ['眼睛✓', '神经/睡不着✓', '图腾✓', '弯曲✓', '瘦✓', '惊吓/信息✓'],
    '太阴': ['藏起来✓', '雕刻✓', '神经（乘卯坐申=神经失控）✓', '酒具✓', '女人/阴私'],
    '天后': ['恩泽之神✓', '女人✓', '老婆✓', '公婆', '水神'],
    '六合': ['多✓', '小孩✓', '形状（箱子/盒状）✓', '一整套✓', '婚姻/媒介✓'],
    '天空': ['空/中空✓', '心思不在家✓', '交易空✓', '开口✓', '虚妄'],
    '贵人': ['贵重✓', '名气大✓', '官长/提携', '恩泽'],
}

# 组合象：支+天将 → 更具体的现代象（课例原句）
COMBO_XIANG: Dict[Tuple[str, str], str] = {
    ('戌', '青龙'): '银行 / 大财库（日干财库）✓',
    ('戌', '白虎'): '病（中传官鬼）/ 过硬✓',
    ('戌', '玄武'): '偷盗 / 奴仆✓',
    ('卯', '朱雀'): '手机（发用指向）✓',
    ('卯', '太阴'): '车（藏起来了）✓',
    ('卯', '太常'): '佛珠（卯为手，太常条状长的）✓',
    ('辰', '勾陈'): '交警 / 证据 / 围墙✓',
    ('辰', '螣蛇'): '图腾 / 老家✓',
    ('辰', '天后'): '女人（来冲财库）✓',
    ('酉', '勾陈'): '带把的东西（酒具）✓',
    ('酉', '太常'): '标签 / 牌子（苹果手机的圆）✓',
    ('酉', '螣蛇'): 'S 形（S5）✓',
    ('巳', '太常'): '吃喝 / 胃口✓',
    ('巳', '白虎'): '催官（测官最喜见白虎）✓',
    ('午', '白虎'): '老虎机✓',
    ('午', '六合'): '小孩 / 怀孕（临日干胎地）✓',
    ('申', '青龙'): '飞机 / 交警 / 事业大✓',
    ('子', '太常'): '小孩服装 / 酒水饮食✓',
    ('亥', '玄武'): '中医 / 风水先生（地医）✓',
    ('亥', '天后'): '房屋 / 恩泽✓',
    ('未', '勾陈'): '警察（+太岁）✓',
    ('寅', '玄武'): '猫 / 下贱之神（脱耗贵气）✓',
    ('丑', '贵人'): '金库 / 贵重✓',
    ('巳', '螣蛇'): '热水管（弯曲+热）✓',
    # ── 2026-09-11 课例回放补录（原覆盖率 60.5% → 补齐至 100%）──
    ('酉', '朱雀'): '咽喉 / 口舌（酉为兑，主说与口）✓',
    ('子', '螣蛇'): '瘦 / 精神问题（睡不着）✓',
    ('巳', '朱雀'): '朱雀临门 / 爱吵架（巳为朱雀本家）✓',
    ('酉', '天空'): '败神 / 心思不在家✓',
    ('未', '朱雀'): '吹虚说大话（落空）✓',
    ('午', '螣蛇'): '图腾（巳为螣蛇本家）✓',
    ('申', '六合'): '一整套（申为长生/根=属相）✓',
    ('丑', '螣蛇'): '惊恐 / 无法睡眠✓',
    ('巳', '青龙'): '热水管道（螣蛇青龙皆弯曲 + 巳为热）✓',
    ('巳', '贵人'): '⚠️随日干角色变：为财则财/文明文化/贵重；为官鬼则罚款✓',
    ('戌', '六合'): '箱 / 盒状（六合为形状）✓',
    ('寅', '青龙'): '帅 / 事业（行年看长相）✓',
    ('卯', '勾陈'): '桃花（日干支桃花）✓',
    ('寅', '天空'): '避孕套（中空 + 遁丙为圆）✓',
    # ── 2026-09-11 风水/人事域补录（素材＝赵林声《新加坡案例》14 例）──
    ('辰', '青龙'): '太岁所在 / 喜庆（临辰为岁方）✓',
    ('戌', '朱雀'): '消息 / 刑（戌刑未为日干寄宫→搞鬼之象）✓',
    ('巳', '玄武'): '诈骗（玄武入墓=水平不高）✓',
    ('子', '白虎'): '贼神（子为妻为桃花）✓',
    ('子', '勾陈'): '勾搭 / 虚（勾陈勾搭 + 空=虚）✓',
    ('戌', '天后'): '部队 / 肉 / 聚积（主胖）✓',
    ('寅', '天后'): '东北大树 / 旺财子✓',
    ('酉', '玄武'): '法国红酒 / 常破碎 / 桃花女色✓',
}

DUN_GAN_XIANG: Dict[str, str] = {
    '甲': '根 / 属相 / 一整套✓',
    '乙': '艺术品 / 弯曲✓',
    '丙': '电子产品 / 圆 / 光明✓',
    '丁': '雕刻 / 电子 / 圆✓',
    '戊': '面积 / 宽 / 一大挂✓',
    '己': '开口 / 中央✓',
    '庚': '金属 / 硬',
    '辛': '小金 / 小颗粒 / 精致✓',
    '壬': '水 / 流动',
    '癸': '闭口 / 堵塞✓',
}

# ═══════════════ 一·B、推演表结构化（P2, 2026-09-11） ═══════════════
# 数据源：docs/现代事物六壬类象推演表.md（人工维护 113 条 / 10 大类）
# 字段：名=事物 级=验证等级 支=地支要素 将=天将要素 合=支×天将组合 干=遁干
#       功=功能/神煞/六亲要素 条=成立条件 备=备注
# 🔴 铁律：级=待验证 的条目**不得单独作断语依据**，输出一律强制标注「△待验证」。
TUIYAN_ITEMS: List[Dict[str, str]] = [
    # ── 一、通信与信息类 ──
    {'名': '手机', '级': '已验证', '支': '卯戌巳', '将': '朱雀白虎贵人', '合': '卯·朱雀', '干': '辛',
     '条': '卯为发用乘朱雀', '备': '苹果S5；卯坐申，卯阴神戌乘白虎，戌阴神巳乘贵遁辛'},
    {'名': '电话', '级': '已验证', '将': '朱雀', '备': '打电话看朱雀'},
    {'名': '信息/消息', '级': '已验证', '将': '朱雀', '支': '辰'},
    {'名': '网络', '级': '已验证', '支': '戌', '功': '火库', '备': '戌=火库（火为信息）'},
    {'名': '电脑', '级': '待验证', '支': '卯戌巳', '条': '坐宫定台式/笔记本'},
    {'名': '电视', '级': '待验证', '支': '午申', '将': '朱雀', '条': '申主信号'},
    {'名': '广播/媒体', '级': '待验证', '支': '午', '将': '朱雀太常', '条': '乘太常=内容/节目'},
    {'名': '书/文件', '级': '传统', '支': '寅', '将': '朱雀青龙'},
    {'名': '邮件/快递', '级': '待验证', '支': '申卯', '将': '玄武青龙', '条': '玄武=丢失，青龙=到达'},
    {'名': '信号/网络信号', '级': '待验证', '支': '巳戌', '条': '空亡=断网'},
    {'名': '数据/信息流', '级': '待验证', '支': '戌巳辰', '条': '辰主数据库'},
    # ── 二、交通出行类 ──
    {'名': '汽车', '级': '已验证', '支': '卯', '将': '太阴', '合': '卯·太阴',
     '条': '乘太阴=藏/偷', '备': '三传空=没被偷；寅=树（停车处）'},
    {'名': '飞机', '级': '已验证', '支': '申', '将': '青龙', '合': '申·青龙', '条': '落空=天空=坐飞机远行'},
    {'名': '火车', '级': '待验证', '支': '申午', '将': '白虎', '条': '乘白虎=高铁快'},
    {'名': '轮船', '级': '待验证', '支': '亥卯', '条': '申(传送)主航线'},
    {'名': '自行车/摩托', '级': '待验证', '支': '卯巳', '条': '小/轻看卯阴神'},
    {'名': '道路', '级': '传统', '支': '申'},
    {'名': '交警', '级': '已验证', '支': '申辰未', '将': '青龙勾陈', '功': '太岁'},
    {'名': '红绿灯', '级': '待验证', '支': '午巳', '将': '朱雀', '条': '巳主通行'},
    {'名': '高速公路', '级': '待验证', '支': '申寅', '将': '青龙', '条': '乘青龙=畅通'},
    {'名': '堵车', '级': '待验证', '支': '申辰', '将': '勾陈', '条': '辰=停滞'},
    # ── 三、金融与商业类 ──
    {'名': '银行卡', '级': '已验证', '将': '朱雀', '备': '朱雀=卡类神'},
    {'名': '取款机', '级': '已验证', '将': '朱雀白虎', '支': '午子', '合': '午·白虎',
     '备': '末传子水=小片'},
    {'名': '银行', '级': '已验证', '支': '戌丑', '将': '青龙', '功': '财库',
     '合': '戌·青龙', '备': '大财库；丑=金库'},
    {'名': '贷款', '级': '已验证', '支': '亥丑', '将': '天后', '功': '马星,天医,金库',
     '条': '本命亥临马星乘天后坐金库丑'},
    {'名': '转账', '级': '待验证', '支': '申', '将': '朱雀', '功': '财', '条': '申(传送) + 财(我克)'},
    {'名': '股票', '级': '待验证', '支': '午巳', '将': '青龙玄武', '条': '巳主K线动'},
    {'名': '纸币', '级': '待验证', '支': '午', '将': '朱雀太常', '条': '乘太常=有面值'},
    {'名': '合同/契约', '级': '传统', '支': '寅', '将': '六合'},
    {'名': '网络支付', '级': '待验证', '支': '戌巳', '将': '朱雀玄武', '条': '玄武=盗刷'},
    {'名': '骗局', '级': '已验证', '将': '玄武', '支': '寅', '条': '玄武乘寅发传化空=跑了'},
    {'名': '欠款', '级': '待验证', '功': '财,兄弟', '条': '传财太旺反财亏'},
    # ── 四、医疗健康类 ──
    {'名': '医院', '级': '待验证', '支': '巳午', '将': '白虎', '功': '天医,吊客'},
    {'名': '医生', '级': '已验证', '支': '巳亥申', '功': '天医,地医', '条': '巳为天医，申指针灸'},
    {'名': '药', '级': '传统', '支': '卯', '备': '用户确认'},
    {'名': '手术', '级': '待验证', '支': '酉', '将': '勾陈白虎', '条': '白虎=主刀'},
    {'名': '检查/化验', '级': '待验证', '支': '巳', '将': '朱雀', '条': '午=血'},
    {'名': '输液/注射', '级': '待验证', '支': '巳子酉'},
    {'名': '心脏', '级': '已验证', '支': '午', '条': '午入墓=心律不齐'},
    {'名': '肝脏', '级': '已验证', '支': '寅', '条': '寅旺=肝火上扬'},
    {'名': '胃/脾胃', '级': '已验证', '支': '戌辰', '备': '戌=块状'},
    {'名': '眼睛', '级': '已验证', '将': '螣蛇', '条': '螣蛇被克=眼病'},
    {'名': '神经/精神', '级': '已验证', '将': '螣蛇太阴', '备': '螣蛇=睡不着；太阴=神经失控'},
    {'名': '腰', '级': '已验证', '将': '白虎', '功': '官鬼', '条': '中传白虎乘官鬼'},
    {'名': '饮食/胃口', '级': '已验证', '支': '巳', '将': '太常', '合': '巳·太常'},
    # ── 五、居住与家居类 ──
    {'名': '房子', '级': '已验证', '支': '亥', '功': '父母,长生'},
    {'名': '门', '级': '传统', '支': '卯'},
    {'名': '窗', '级': '待验证', '支': '卯', '将': '朱雀', '条': '朱雀=光/通气'},
    {'名': '墙', '级': '已验证', '支': '辰', '将': '勾陈', '合': '辰·勾陈', '条': '辰乘勾陈=围墙/官司墙'},
    {'名': '床', '级': '待验证', '支': '酉午', '将': '天后', '条': '乘天后=婚姻床'},
    {'名': '热水管道', '级': '已验证', '支': '巳', '将': '螣蛇青龙', '干': '癸',
     '合': '巳·螣蛇', '备': '吊客/弯曲/热'},
    {'名': '水龙头', '级': '待验证', '支': '子巳', '干': '癸', '条': '癸=闭口=堵塞'},
    {'名': '电器', '级': '待验证', '支': '巳午', '将': '白虎', '条': '乘白虎=漏电/故障'},
    {'名': '空调', '级': '待验证', '支': '巳亥子', '条': '子水=制冷'},
    {'名': '家具', '级': '待验证', '支': '卯丑', '将': '太常', '条': '乘太常=常用'},
    {'名': '灶/厨', '级': '传统', '支': '巳'},
    {'名': '坟/墓', '级': '传统', '支': '辰戌'},
    {'名': '陶器/罐', '级': '已验证', '支': '戌'},
    {'名': '鱼缸', '级': '已验证', '支': '辰', '备': '辰=水库（放鱼缸解辰冲戌墓）'},
    # ── 六、职业与身份类 ──
    {'名': '警察', '级': '已验证', '支': '申未辰', '将': '青龙勾陈', '功': '太岁'},
    {'名': '部队/军人', '级': '已验证', '支': '亥戌', '将': '太常白虎'},
    {'名': '官员', '级': '传统', '将': '贵人'},
    {'名': '教师', '级': '待验证', '支': '寅', '将': '朱雀青龙', '条': '青龙主文教'},
    {'名': '程序员', '级': '待验证', '支': '戌巳卯', '将': '玄武', '条': '玄武=黑客'},
    {'名': '医生(职业)', '级': '已验证', '支': '巳亥', '功': '天医,地医'},
    {'名': '司机', '级': '待验证', '支': '卯申', '将': '白虎', '条': '乘白虎=快/险'},
    {'名': '生意人', '级': '待验证', '将': '青龙六合玄武', '条': '乘玄武=奸商'},
    {'名': '律师/官司', '级': '传统', '将': '勾陈'},
    {'名': '和尚/道士', '级': '已验证', '将': '太阴玄武', '备': '太阴=神佛；玄武=玄学道家'},
    {'名': '骗子', '级': '已验证', '将': '玄武', '条': '玄武=偷盗/虚诈'},
    {'名': '小偷', '级': '传统', '将': '玄武'},
    # ── 七、饮食衣物类 ──
    {'名': '酒', '级': '已验证', '支': '亥酉', '将': '太常', '条': '酉顶亥乘太常=爱喝酒'},
    {'名': '茶/酒具', '级': '已验证', '支': '酉', '将': '太阴'},
    {'名': '衣服', '级': '传统', '将': '太常'},
    {'名': '食物', '级': '传统', '将': '太常'},
    {'名': '鸡类餐饮', '级': '已验证', '支': '酉午', '条': '酉=鸡坐午火'},
    {'名': '肉', '级': '待验证', '支': '午戌', '将': '白虎', '备': '戌=狗肉(忌)'},
    {'名': '药膳/补品', '级': '待验证', '支': '卯', '将': '太常'},
    {'名': '烟', '级': '待验证', '支': '巳午', '将': '白虎', '条': '白虎=伤肺'},
    {'名': '饮料', '级': '待验证', '支': '子亥', '将': '太常玄武', '条': '乘玄武=假货'},
    # ── 八、科技与电子类 ──
    {'名': '电子产品', '级': '已验证', '支': '戌', '干': '丙', '功': '库'},
    {'名': '芯片', '级': '待验证', '支': '戌巳酉', '条': '坐宫定用途'},
    {'名': '电池', '级': '待验证', '支': '巳午丑', '条': '空亡=没电'},
    {'名': '充电', '级': '待验证', '支': '巳', '条': '被克=充不进'},
    {'名': '电线/网线', '级': '待验证', '支': '巳申', '将': '螣蛇', '条': '螣蛇=缠绕/弯曲'},
    {'名': '手机配件', '级': '待验证', '支': '卯', '条': '阴神/坐宫定（壳/膜/充电器）'},
    {'名': '卫星', '级': '待验证', '支': '午申', '将': '青龙', '条': '乘青龙=高空'},
    {'名': '机器人', '级': '待验证', '支': '卯巳戌'},
    {'名': 'AI/程序', '级': '待验证', '支': '戌巳寅', '条': '寅=智能'},
    # ── 九、婚恋家庭类 ──
    {'名': '婚姻', '级': '传统', '将': '六合', '条': '六合临申坐巳=合中有破吵吵不离婚'},
    {'名': '桃花', '级': '已验证', '支': '酉午卯', '备': '申子辰桃花在酉；午=旺月；卯=日桃花'},
    {'名': '情人', '级': '已验证', '支': '午亥', '功': '偏财', '备': '亥=双数多情人'},
    {'名': '怀孕', '级': '已验证', '支': '午', '将': '六合', '功': '胎神',
     '条': '午火临日干胎地乘六合'},
    {'名': '小孩', '级': '已验证', '支': '亥卯子'},
    {'名': '避孕套', '级': '已验证', '支': '寅', '将': '天空', '干': '丙',
     '合': '寅·天空', '条': '寅(淫)+天空(空)+丙(圆)'},
    {'名': '离婚', '级': '已验证', '支': '丑午子酉', '条': '干上丑支上午相害=最坏组合；子酉破=破口骂'},
    {'名': '父母', '级': '已验证', '支': '申', '功': '父母', '条': '父母上三传=好事（非测子孙时）'},
    {'名': '兄弟', '级': '已验证', '支': '子', '功': '兄弟'},
    {'名': '妻/财', '级': '传统', '功': '财'},
    {'名': '夫/官', '级': '传统', '功': '官鬼'},
    {'名': '家宅', '级': '已验证', '支': '辰戌丑未', '条': '支=宅；干=人；干支阴神=父母娘家人'},
    # ── 十、其他通用类象速查 ──
    {'名': '丢失', '级': '传统', '将': '玄武'},
    {'名': '找回', '级': '已验证', '功': '财,行年,日支', '条': '财合行年/日支=找回；冲日冲月=应期'},
    {'名': '官司', '级': '传统', '将': '勾陈', '功': '官符'},
    {'名': '文书/考试', '级': '传统', '将': '朱雀', '支': '寅'},
    {'名': '升官', '级': '已验证', '将': '白虎', '条': '白虎=催官使者；头顶墓=大忌'},
    {'名': '赚钱', '级': '传统', '将': '青龙', '功': '财'},
    {'名': '破财', '级': '已验证', '功': '兄弟', '条': '兄弟=劫财；传财太旺反财亏'},
    {'名': '病', '级': '传统', '将': '白虎'},
    {'名': '死', '级': '已验证', '功': '丧门,吊客,死神,死气', '条': '久病逢冲=死'},
    {'名': '惊扰', '级': '传统', '将': '螣蛇'},
    {'名': '暗昧', '级': '传统', '将': '玄武太阴'},
    {'名': '神佛', '级': '已验证', '将': '太阴'},
]

_TY_LEVEL_ORDER = {'已验证': 0, '传统': 1, '待验证': 2}
_TY_JIANG_NAMES = ('贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                   '天空', '白虎', '太常', '玄武', '太阴', '天后')


def _ty_split_zhi(s: str) -> List[str]:
    return [c for c in str(s or '') if c in DIZHI]


def _ty_split_jiang(s: str) -> List[str]:
    s = str(s or '')
    out = []
    for i in range(0, len(s), 2):
        name = s[i:i + 2]
        if name in _TY_JIANG_NAMES:
            out.append(name)
    return out


def _ty_split_func(s: str) -> List[str]:
    return [x for x in str(s or '').replace('，', ',').split(',') if x]


def _ty_build_index():
    """构建推演表索引：地支 / 天将 / 组合 / 功能 / 多要素。"""
    by_zhi: Dict[str, List[Dict[str, Any]]] = {}
    by_jiang: Dict[str, List[Dict[str, Any]]] = {}
    by_combo: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    by_func: Dict[str, List[Dict[str, Any]]] = {}
    for it in TUIYAN_ITEMS:
        for z in _ty_split_zhi(it.get('支', '')):
            by_zhi.setdefault(z, []).append(it)
        for j in _ty_split_jiang(it.get('将', '')):
            by_jiang.setdefault(j, []).append(it)
        for pair in str(it.get('合', '') or '').split('|'):
            pair = pair.strip()
            if '·' in pair:
                a, b = pair.split('·', 1)
                a, b = a.strip(), b.strip()
                if a in DIZHI and b in _TY_JIANG_NAMES:
                    by_combo.setdefault((a, b), []).append(it)
        for f in _ty_split_func(it.get('功', '')):
            by_func.setdefault(f, []).append(it)
    return by_zhi, by_jiang, by_combo, by_func


TUIYAN_BY_ZHI, TUIYAN_BY_JIANG, TUIYAN_COMBO, TUIYAN_BY_FUNC = _ty_build_index()


def _ty_elements(it: Dict[str, str]) -> Tuple[List[str], List[str], List[Tuple[str, str]],
                                              List[str], List[str]]:
    """抽取条目的五类要素（支 / 将 / 支×将 / 功能 / 遁干），用于组合匹配。"""
    return (_ty_split_zhi(it.get('支', '')),
            _ty_split_jiang(it.get('将', '')),
            [tuple(p.strip().split('·', 1)) for p in str(it.get('合', '') or '').split('|')
             if '·' in p],
            _ty_split_func(it.get('功', '')),
            [c for c in str(it.get('干', '') or '') if c in TIANGAN])


def match_tuiyan(nodes: List[Tuple], min_ratio: float = 0.6,
                 top_k: int = 6) -> List[Dict[str, Any]]:
    """多要素组合匹配：给一组 (地支, 天将[, 遁干]) 课象节点，匹配推演表事物。

    仅对**要素数 >= 2** 的条目评分（单要素条目无区分度，走 map_modern_xiang）。
    返回按 命中率 → 等级 排序的候选。
    """
    zi, ji, gi, pairs = set(), set(), set(), set()
    for nd in (nodes or []):
        nd = tuple(nd) if isinstance(nd, (list, tuple)) else (nd,)
        z = str(nd[0]) if len(nd) > 0 and nd[0] else ''
        j = str(nd[1]) if len(nd) > 1 and nd[1] else ''
        g = str(nd[2]) if len(nd) > 2 and nd[2] else ''
        if z:
            zi.add(z)
        if j:
            ji.add(j)
        if g:
            gi.add(g)
        if z and j:
            pairs.add((z, j))
    out = []
    for it in TUIYAN_ITEMS:
        zs, js, cs, fs, gs = _ty_elements(it)
        total = len(zs) + len(js) + len(cs) + len(fs) + len(gs)
        if total < 2:
            continue
        hits: List[str] = []
        for z in zs:
            if z in zi:
                hits.append(z)
        for j in js:
            if j in ji:
                hits.append(j)
        for p in cs:
            if p in pairs:
                hits.append(f'{p[0]}·{p[1]}')
        for f in fs:
            if f in zi or f in ji:      # 功能词暂以 支/将 字面近似（P4 接神煞）
                hits.append(f)
        for g in gs:
            if g in gi:
                hits.append(f'遁{g}')
        if not hits:
            continue
        ratio = len(hits) / total
        lv = it.get('级', '')
        if lv == '待验证':
            # 🔴 铁律：未验证推演须**全要素命中且 >= 3 项**方可入候选，防「△」泛滥
            if ratio < 1.0 or len(hits) < 3:
                continue
        elif ratio < min_ratio:
            continue
        out.append({'事物': it['名'], '等级': it['级'], '命中要素': hits,
                    '命中率': f'{len(hits)}/{total}', '比率': round(ratio, 3),
                    '条件': it.get('条', ''), '备注': it.get('备', '')})
    out.sort(key=lambda d: (-d['比率'], _TY_LEVEL_ORDER.get(d['等级'], 3),
                            -len(d['命中要素'])))
    return out[:top_k]


# ═══════════════ 一·C、行为风水解法（P4, 2026-09-11） ═══════════════
# 数据源：`_memory/beida_kege_cases.json` 的「行为风水」7 条（北大课例原文结构化）
# 🔴 通则（课例-10）：「解的东西一定要在**七处**（行年/本命/行命上神/日上神/支上神/三传/先锋门）」
#    → 只有落在七处的「病位」才给建议，非七处一律不提。
# 🟡 环境所断（赵师原话）：均为参考，**不作定论、不进评分链**；跨占类不可泛化。
XINGWEI_TONGZE = [
    '解的东西一定要落在七处，否则不作数（课例-10）',
    '常用手法：拖、说假话应象、认干亲、调方位（课例-12/29）',
]

XINGWEI_SHOUFA: Dict[str, str] = {
    '空亡': '填实：认该支属相为干亲／放置该支象之物（太岁不可填实）',
    '库': '冲开：以**冲支**之物解（戌库用辰、辰库用戌；置对应方位）',
    '闭口': '打开：疏通堵塞处（癸=闭口）',
    '旺凶': '拖：缓期应事，降低应期压力',
    '刑冲': '应象化解：以象破象（说假话应象／暂避）',
}

# 具体病位模式 → 课例原解法（原文照录，出处可查）
XINGWEI_CASES: List[Dict[str, str]] = [
    {'支': '戌', '状态': '库', '解法': '用辰冲 → 家里北边放鱼缸（辰为水库）', '出处': '课例-10'},
    {'支': '戌', '解法': '把正南窗台陶罐搬开；不能养狗', '出处': '课例-10'},
    {'支': '巳', '遁干': '癸', '解法': '找人把热水管打通（癸闭口就打开）', '出处': '课例-16'},
    {'支': '寅', '状态': '空亡', '解法': '认属虎的做干亲；西北角放木雕老子/鬼谷子像', '出处': '课例-29'},
    {'支': '申', '状态': '空亡', '解法': '调出北京城坐飞机去的地方（申坐卯为东方）', '出处': '课例-27'},
]

# ═══════════════ 一·D、风水占范式（2026-09-11）═══════════════
# 数据源：`_memory/replay_cases_zhaolinsheng_xinjiapo.json` 风水 4 例（赵林声《新加坡案例》原文）。
# 🟡 叙事层参考：不作定论、不进评分链；跨占类不可泛化。
FENGSHUI_FANSHI: List[Dict[str, str]] = [
    {'名': '一宫四位', '则': '一宫 = 天干 + 天将 + 地支 + 坐宫，四位一体即一象'
                          '（风水与事件的对应根本范式）', '源': 'XJP-01'},
    {'名': '祖坟定位', '则': '祖坟看【第四课】与【七杀】；临贵有贵气出官；'
                          '《金口诀》「上克下，宅必矮」', '源': 'XJP-01'},
    {'名': '化解运筹', '则': '过旺取泄：方位 + 物象 + 时辰三要素。如辰过旺取酉泄 → '
                          '祖坟西北埋不封口酒坛（癸=闭口故不封）、亥日巳时取冲', '源': 'XJP-02'},
    {'名': '阴神链揭底', '则': '逐层下探揭底：朱雀（消息）→ 玄武（诈骗）→ 白虎（贼神）；'
                          '单象不足，三象合参', '源': 'XJP-14'},
    {'名': '方位断应', '则': '支定方位（申酉属西、寅属东北、辰巳属东南…），'
                          '宫位四象即现场方位物象', '源': 'XJP-01/03'},
    {'名': '宅象读数', '则': '三传全「兄+父+子」无官鬼 → 宅主经营类象；'
                          '干=人、支=宅，干支阴神=六亲/邻舍', '源': 'XJP-03'},
]

_SI_KU = {'辰': '水库', '戌': '火库', '丑': '金库', '未': '木库'}

_FANGWEI = {'子': '正北', '丑': '东北', '寅': '东北', '卯': '正东', '辰': '东南', '巳': '东南',
            '午': '正南', '未': '西南', '申': '西南', '酉': '正西', '戌': '西北', '亥': '西北'}
_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
          '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}


def _row_state(row: Dict[str, Any], kong: List[str]) -> List[str]:
    """判定课象节点的「可解状态」：空亡 / 库（四库之一）/ 闭口。

    ⚠️ 用「库」而非「墓」：四土支本是**库**，「入墓」指某支五行入其库（如午火入戌库），
    两者不同——统一称「库」以免误导（2026-09-11）。
    """
    z = str(row.get('地支') or '')
    out = []
    if z and z in (kong or []):
        out.append('空亡')
    if z in _SI_KU:
        out.append('库')
    if str(row.get('遁干') or '') == '癸':
        out.append('闭口')
    return out


def recommend_solutions(result: Dict[str, Any], max_items: int = 4) -> Dict[str, Any]:
    """行为风水解法推荐（P4）。

    通则：**只对落在七处的节点给建议**（课例-10「解的东西一定要在七处」）。
    """
    kong = result.get('_kongwang') or []
    rows = []
    for c in (result.get('链') or []):
        for r in (c.get('链') or []):
            if r.get('命中七处'):
                rows.append(r)
    seen, uniq = set(), []
    for r in rows:
        if r['地支'] not in seen:
            seen.add(r['地支'])
            uniq.append(r)
    out = []
    for r in uniq[:max_items]:
        z = r['地支']
        states = _row_state(r, kong)
        hits = '、'.join(r['命中七处'])
        jo = '乘' + r['天将'] if r.get('天将') else ''
        dun = '遁' + r['遁干'] if r.get('遁干') else ''
        item = {'病位': f'{z}{jo}{dun}（{hits}）', '状态': states or ['—'],
                '通用解法': [], '原例参考': '', '出处': '',
                '方位参考': _FANGWEI.get(z, '')}
        for st in states:
            if st == '库':
                # 动态生成：每个支的库名与冲支不同（原硬编码「戌墓用辰冲」会张冠李戴）
                _ch = _CHONG.get(z, '')
                item['通用解法'].append(
                    f'库（{_SI_KU.get(z, "")}）：用{_ch}冲开／置{_FANGWEI.get(_ch, "")}'
                    f'方位之冲支象物（参考）')
            elif st in XINGWEI_SHOUFA:
                item['通用解法'].append(f'{st}: {XINGWEI_SHOUFA[st]}')
        for cse in XINGWEI_CASES:
            if cse.get('支') != z:
                continue
            if cse.get('遁干') and cse['遁干'] != str(r.get('遁干') or ''):
                continue
            if cse.get('状态') and cse['状态'] not in states:
                continue
            item['原例参考'] = cse['解法']
            item['出处'] = cse['出处']
            break
        # 无任何可给的建议 → 不占位（避免噪音）
        if item['通用解法'] or item['原例参考']:
            out.append(item)
    return {'通则': XINGWEI_TONGZE, '建议': out,
            '边界': '行为风水=参考层（环境所断），不作定论、不进评分链'}


# 占类 → 类神兜底（无 leishen_engine 依赖时；有则优先用引擎表）
FALLBACK_CATEGORY: Dict[str, List[str]] = {
    '寻物': ['玄武（盗/丢失环境）', '类神本象（丢什么找什么）'],
    '盗贼': ['玄武'],
    '求财': ['财爻（日干所克）', '青龙（主财）', '六合（和合财）'],
    '官运': ['官鬼（克日干）', '贵人', '青龙', '太常（武职）'],
    '官讼': ['朱雀（词讼）', '勾陈（拘捕）', '白虎（刑伤）'],
    '疾病': ['白虎（病）', '墓神（病地）', '天医/地医'],
    '婚姻': ['六合（媒介）', '天后（女）', '青龙（婿）', '财（男占妻）'],
    '来意': ['发用（矛盾集中点）', '先锋门（正时）'],
    '射覆': ['发用', '太阴/酉（器物）', '勾陈（带把）'],
    '家宅': ['日支（宅）', '父母（房屋）'],
    '谋望': ['六合（和合）', '太常（谋成）', '日德（根基）'],
    '职业': ['正财（第一看）', '偏财（暴财）'],
    # ── 2026-09-11 新增「风水 / 消息 / 饭局测事」域（素材＝赵林声《新加坡案例》14 例）──
    '风水': ['日支（阳宅本体/坟）', '第四课（祖坟）', '七杀（祖坟）', '青龙（来龙生气）',
             '白虎（恶砂煞气）', '勾陈（土石田土）', '玄武（水·暗沟·风水先生）',
             '父母（房屋·碑）', '贵人（神位/官贵之气）', '太常（香火供品）'],
    '消息': ['朱雀（音信/口舌）', '发用（矛盾集中点）', '玄武（诈骗/虚假）'],
    '饭局测事': ['发用（众人共占）', '一课多断（按人分宫）'],
}

# 占类名归一化：赵林声新课例占类多用「主类·子题」复合名
# （如「风水·官运」「风水·祖坟运筹」「饭局测事·婚姻官讼」），整串查表必落空 → 取前缀主类。
_CAT_SEPS = ('·', '·', '／', '/', '|')

# 占类同义词归一（课例/前端口语 → 标准占类）
CATEGORY_ALIAS: Dict[str, str] = {
    '失物': '寻物', '寻找': '寻物', '找东西': '寻物', '找物': '寻物', '丢东西': '寻物',
    '寻人': '行人', '找人': '行人',
    '觅人': '觅访', '访人': '觅访',
    '消息真假': '消息', '信息真假': '消息', '真假': '消息',
    '测人': '来意', '测事': '来意', '来意测事': '来意',
    '选举': '官运', '时局': '官运',
}


def _norm_category(cat: str) -> str:
    """'风水·官运' → '风水'；'消息真假' → '消息'；已是主类则原样返回。"""
    s = str(cat or '').strip()
    for sep in _CAT_SEPS:
        if sep in s:
            h = s.split(sep)[0].strip()
            if h:
                s = h
                break
    return CATEGORY_ALIAS.get(s, s)

# 七处（《北大课例》课例-10 原文：「行、命、行命上神，日上神，支上神，三传、先锋门」）
QI_CHU_NAMES = ['行年', '本命', '行命上神', '日上神', '支上神', '三传', '先锋门']


# ═══════════════ 二、工具函数 ═══════════════

def _as_list(v: Any) -> List[str]:
    """契约：**扁平字符串列表**（三传/空亡等）。⚠️ 不可用于 si_ke！"""
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if x]
    return []


def _sike_rows(v: Any) -> List[Any]:
    """契约：si_ke 元素 = (课名, 上神, 下神, 天将) 的**元组列表**，必须保持结构。

    【2026-09-11 踩坑】误用 _as_list 处理 si_ke 会把元组展平成字符串，
    导致 sk[j][1] 取到 '(' → 日上神/支上神恒为空 → **四课链全部不生成**（静默）。
    与 MEMORY「类型契约混用」A 类同型。
    """
    if isinstance(v, (list, tuple)):
        return [x for x in v]
    return []


def zuo_gong(zhi: str, tiandi_pan: Any) -> str:
    """反查天盘支 zhi 所临的地盘宫（它坐在哪个宫上）。"""
    if not zhi or not isinstance(tiandi_pan, dict):
        return ''
    for d, t in tiandi_pan.items():
        if t == zhi and d in DIZHI:
            return d
    return ''


def yin_shen(zhi: str, tiandi_pan: Any) -> str:
    """阴神(X) = tiandi_pan[X]（以 X 为地盘宫，取该宫天盘上神）。"""
    if not zhi or not isinstance(tiandi_pan, dict):
        return ''
    return str(tiandi_pan.get(zhi, '') or '')


def expand_chain(start: str, tiandi_pan: Any, jiang_pan: Any = None,
                 ri_ganzhi: str = '', max_depth: int = 3) -> List[Dict[str, Any]]:
    """从起始地支逐层展开阴神链。

    返回 [{'层':0,'地支':..,'天将':..,'遁干':..,'坐宫':..}, ...]
    收敛：遇到伏吟自环（next==cur）或链中出现过的支 → 停止。
    """
    if not start or not isinstance(tiandi_pan, dict):
        return []
    dun = _dun_gan_fn(ri_ganzhi)
    out: List[Dict[str, Any]] = []
    seen = set()
    cur = start
    for depth in range(max(1, int(max_depth))):
        if not cur or cur in seen:
            break
        seen.add(cur)
        row = {
            '层': depth,
            '地支': cur,
            '天将': (jiang_pan or {}).get(cur, ''),
            '遁干': dun(cur) if dun else '',
            '坐宫': zuo_gong(cur, tiandi_pan),
        }
        out.append(row)
        nxt = yin_shen(cur, tiandi_pan)
        if not nxt or nxt == cur:      # 伏吟自环 / 数据不足
            break
        cur = nxt
    return out


def _dun_gan_fn(ri_ganzhi: str):
    """惰性取遁干函数（避免顶层 import 副作用）。"""
    if not ri_ganzhi or len(ri_ganzhi) < 2:
        return None
    try:
        from engine.bifa_detector import get_dun_gan
    except Exception:
        return None
    return lambda z: get_dun_gan(ri_ganzhi, z)


def qi_chu_map(env: Dict[str, Any]) -> Dict[str, Any]:
    """七处锚点 → 地支（命中判定用）。"""
    tdp = env.get('tiandi_pan') or {}
    sk = _sike_rows(env.get('si_ke'))
    xing = str(env.get('xing_nian') or '')
    ming = str(env.get('ben_ming') or '')

    def _up(z):
        return yin_shen(z, tdp) if z else ''

    def _sk_up(j):
        # si_ke 元素 = (课名, 上神, 下神, 天将)
        return str(sk[j][1]) if len(sk) > j and isinstance(sk[j], (list, tuple)) and len(sk[j]) > 1 else ''

    return {
        '行年': xing,
        '本命': ming,
        # 【P4 2026-09-11】原文「行、命、行命上神」→ 行命上神兼指**行年上神／本命上神**
        # 两解，改列表覆盖（原 `or` 只取先出现的那个，丢一处）。
        '行命上神': [x for x in dict.fromkeys([_up(xing), _up(ming)]) if x],
        '日上神': str(env.get('gan_shang') or '') or _sk_up(0),
        '支上神': str(env.get('zhi_shang') or '') or _sk_up(2),
        '三传': _as_list(env.get('sanchuan')) or _as_list(
            [env.get('chu'), env.get('zhong'), env.get('mo')]),
        '先锋门': str(env.get('shichen') or ''),
    }


def _hit_qi_chu(zhi: str, qc: Dict[str, Any]) -> List[str]:
    if not zhi:
        return []
    hits = []
    for name in QI_CHU_NAMES:
        v = qc.get(name)
        if isinstance(v, (list, tuple)):
            if zhi in v:
                hits.append(name)
        elif v and v == zhi:
            hits.append(name)
    return hits


# ═══════════════ 三、① 类神锚定 ═══════════════

def anchor_leishen(category: str, ri_gan: str = '', ri_zhi: str = '',
                   tai_sui: str = '', season: str = '') -> Dict[str, Any]:
    """① 类神锚定：按占类定位类神（优先引擎表，降级兜底表）。

    返回 {'占类':.., '类神':[..], '类神地支':[..], '来源':..}
    """
    cat = str(category or '').strip()
    out: Dict[str, Any] = {'占类': cat, '类神': [], '类神地支': [], '来源': ''}
    if not cat:
        return out
    # 【2026-09-11】占类名归一化：'风水·官运' → '风水'（整串查表必落空）
    norm = _norm_category(cat)
    out['归一化占类'] = norm
    cands = [cat] if norm == cat else [cat, norm]
    # 优先用引擎的类神表
    try:
        from engine.leishen_engine import get_category_leishen
        for c in cands:
            r = get_category_leishen(c, ri_gan=ri_gan, tai_sui=tai_sui,
                                     season=season, ri_zhi=ri_zhi) or {}
            tj = r.get('tianjiang_table') or {}
            if tj:
                out['类神'] = [f'{k}（{v[0]}）' if isinstance(v, (list, tuple)) and v else k
                               for k, v in tj.items()]
            # 【2026-09-11 修复断链】引擎实际返回字段为 zhi_list，
            # 原读 leishen_zhi/zhi → 恒空（MEMORY「B 类·字段缺失」同型）。
            zhi = r.get('zhi_list') or r.get('leishen_zhi') or r.get('zhi') or []
            if isinstance(zhi, (list, tuple)):
                out['类神地支'] = [str(z) for z in zhi if z]
            if out['类神'] or out['类神地支']:
                out['来源'] = 'leishen_engine'
                return out
    except Exception:
        pass
    out['类神'] = list(FALLBACK_CATEGORY.get(cat) or FALLBACK_CATEGORY.get(norm) or [])
    out['来源'] = 'fallback'
    return out


# ═══════════════ 四、③ 现代象映射 ═══════════════

def map_modern_xiang(zhi: str, jiang: str = '', dun_gan: str = '',
                     zuo: str = '') -> Dict[str, Any]:
    """③ 现代象映射：支 × 天将 × 遁干 × 坐宫 → 候选现代象（带证据强度）。"""
    xiang: List[str] = []
    evidence = '△推演'
    combo = COMBO_XIANG.get((zhi, jiang), '')
    if combo:
        xiang.append(combo)
        evidence = '✓课例'
    if zhi in MODERN_XIANG:
        xiang.extend(MODERN_XIANG[zhi])
        if evidence != '✓课例' and jiang:
            evidence = '传统'
    if jiang in JIANG_XIANG:
        xiang.extend(f'{jiang}：{s}' for s in JIANG_XIANG[jiang])
    if dun_gan and dun_gan in DUN_GAN_XIANG:
        xiang.append(f'遁{dun_gan}：{DUN_GAN_XIANG[dun_gan]}')
    if zuo:
        base = MODERN_XIANG.get(zuo)
        if base:
            xiang.append(f'坐{zuo}：{base[0]}')
    # 去重保序
    seen, uniq = set(), []
    for x in xiang:
        if x and x not in seen:
            seen.add(x)
            uniq.append(x)
    # P2（2026-09-11）：推演表命中（按 地支 / 天将 / 支×天将），等级优先排序
    ty: List[Dict[str, Any]] = []
    seen_ty = set()

    def _add_ty(items):
        for it in items or []:
            if it['名'] not in seen_ty:
                seen_ty.add(it['名'])
                ty.append(it)

    if zhi:
        _add_ty(TUIYAN_BY_ZHI.get(zhi))
    if jiang:
        _add_ty(TUIYAN_BY_JIANG.get(jiang))
    if zhi and jiang:
        _add_ty(TUIYAN_COMBO.get((zhi, jiang)))
    ty.sort(key=lambda it: _TY_LEVEL_ORDER.get(it.get('级', ''), 3))
    # 输出策略：已验证/传统 优先保 9 条，待验证 限 3 条（防 △ 淹没 ✓）
    conf = [it for it in ty if it.get('级') != '待验证']
    pend = [it for it in ty if it.get('级') == '待验证']
    sel = conf[:9] + pend[:3]
    ty_out = [{'名': it['名'], '等级': it['级'], '条件': it.get('条', '')} for it in sel]
    return {'象': uniq, '证据': evidence, '组合': combo, '推演表': ty_out}


# ═══════════════ 五、②+④ 主入口：推演 + 收敛 ═══════════════

def pursue_chain(env: Dict[str, Any], category: str = '',
                 start: str = '', max_depth: int = 3,
                 top_k: int = 6) -> Dict[str, Any]:
    """完整推演：① 类神锚定 → ② 阴神链 → ③ 现代象映射 → ④ 收敛输出。

    env 与 `kege_shensha.judge_all` 同构：
      ri_gan / ri_zhi / ri_ganzhi(可选) / si_ke / sanchuan(or chu/zhong/mo)
      tian_jiang / tiandi_pan / shichen / xing_nian / ben_ming / kongwang

    start: 链条起点（不给则按 三传初传 → 类神地支 → 日上神 的顺序自动选）
    """
    env = env or {}
    ri_gan = str(env.get('ri_gan') or '')
    ri_zhi = str(env.get('ri_zhi') or '')
    tdp = env.get('tiandi_pan') or {}
    shichen = str(env.get('shichen') or '')
    ri_ganzhi = str(env.get('ri_ganzhi') or (ri_gan + ri_zhi))

    # 天将盘：优先 env 自带，其次用全宫真源补算
    jiang_pan = env.get('tian_jiang_pan')
    if not isinstance(jiang_pan, dict) or not jiang_pan:
        tian_jiang = env.get('tian_jiang')
        if isinstance(tian_jiang, dict):
            jiang_pan = tian_jiang
        else:
            jp = {}
            try:
                from engine.kege_shensha import tian_jiang_pan
                jp = tian_jiang_pan(ri_gan, shichen, tdp) or {}
            except Exception:
                jp = {}
            jiang_pan = jp

    qc = qi_chu_map(env)
    anchor = anchor_leishen(category, ri_gan=ri_gan, ri_zhi=ri_zhi,
                            tai_sui=str(env.get('nian_zhi') or ''))

    # 起点选择
    picks: List[Tuple[str, str]] = []
    if start:
        picks.append(('指定', start))
    else:
        # P3：外应锚定 —— 用户填「看到了什么」（如课例-11「见狗取戌」），程序无法自得
        _hint = str(env.get('hint_zhi') or '').strip()
        if _hint in DIZHI:
            picks.append(('外应', _hint))
        chu = str(env.get('chu') or '')
        if not chu:
            sc = _as_list(env.get('sanchuan'))
            chu = sc[0] if sc else ''
        if chu:
            picks.append(('初传', chu))
        for z in anchor.get('类神地支', [])[:2]:
            picks.append(('类神', str(z)))
        gs = qc.get('日上神')
        if gs:
            picks.append(('日上神', str(gs)))

    chains: List[Dict[str, Any]] = []
    seen_rows = set()
    for src, st in picks:
        if not st:
            continue
        rows = expand_chain(st, tdp, jiang_pan, ri_ganzhi, max_depth=max_depth)
        if not rows:
            continue
        key = tuple(r['地支'] for r in rows)
        if key in seen_rows:
            continue
        seen_rows.add(key)
        for r in rows:
            r['现代象'] = map_modern_xiang(r['地支'], r.get('天将', ''),
                                           r.get('遁干', ''), r.get('坐宫', ''))
            r['命中七处'] = _hit_qi_chu(r['地支'], qc)
        chains.append({'起点来源': src, '链': rows})

    # ④ 收敛：按 七处命中 + 证据强度 排序
    ev_rank = {'✓课例': 2, '传统': 1, '△推演': 0}

    def _score(row):
        return (len(row.get('命中七处') or []),
                ev_rank.get(row.get('现代象', {}).get('证据', '△推演'), 0))

    flat = [r for c in chains for r in c['链']]
    flat.sort(key=_score, reverse=True)
    # 节点级去重（2026-09-11）：同一课象会出现在多条链中（如 初传链 与 日上神链 同含午），
    # 「收敛候选」语义为**候选集合**须唯一 —— 只对整条链去重不够，节点也要去重。
    _seen_node, _uniq = set(), []
    for _r in flat:
        _k = (_r.get('地支'), _r.get('天将', ''), _r.get('遁干', ''))
        if _k in _seen_node:
            continue
        _seen_node.add(_k)
        _uniq.append(_r)
    flat = _uniq

    kong = _as_list(env.get('kongwang'))
    out = {
        '占类': anchor.get('占类', ''),
        '类神锚定': anchor,
        '七处': {k: v for k, v in qc.items()},
        '链': chains,
        '收敛候选': [
            {'地支': r['地支'], '天将': r.get('天将', ''), '遁干': r.get('遁干', ''),
             '坐宫': r.get('坐宫', ''), '现代象': r.get('现代象', {}).get('象', [])[:top_k],
             '推演表': r.get('现代象', {}).get('推演表', [])[:top_k],
             '证据': r.get('现代象', {}).get('证据', ''), '命中七处': r.get('命中七处', []),
             '空亡': r['地支'] in kong}
            for r in flat[:top_k]
        ],
        # P2：多要素组合匹配（要素数 >= 2 的推演条目）
        '推演匹配': match_tuiyan(
            [(r['地支'], r.get('天将', ''), r.get('遁干', '')) for r in flat], top_k=top_k),
        '边界': '纯叙事层参考；环境所断，跨占类不可泛化；不赋吉凶、不进评分链',
    }
    # P4：行为风水解法（通则「解的东西一定要在七处」→ 仅对命中七处的节点给建议）
    out['行为风水'] = recommend_solutions({**out, '_kongwang': kong})
    # P4.2（2026-09-11）：风水占 → 附风水范式（叙事层，来源＝赵林声《新加坡案例》）
    if '风水' in str(anchor.get('归一化占类') or anchor.get('占类') or ''):
        out['风水范式'] = FENGSHUI_FANSHI
    out['叙事'] = to_narrative(out)
    return out


def merge_guishen_into_chain(result: Dict[str, Any],
                            judged: Dict[str, Any] = None,
                            top_k: int = 6) -> Dict[str, Any]:
    """把「寺观·僧道·鬼祟」取象并入 `pursue_chain` 的输出（🔴 **零评分影响**）。

    【单一真源】象域判定与候选排序 **只在** `engine.guishen_xiang_engine` 里做一次，
    由 `judge_orchestrator.judge_all` 产出 `judged['guishen_xiang']`。
    本函数 ⛔ 不重算、⛔ 不另立判据，只做两件事：
      ① 把候选支对应的「僧道寺观／神祠／鬼祟」象注入链上节点的 `现代象`
         （**置顶**，避免被 `top_k` 截断后看不见）；
      ② 在链输出内挂 `寺观鬼祟` 段（类象语 / 候选 / 依据 / 边界）。

    【为何不在 pursue_chain 内自算】
      生产调用点（stock_dashboard 排盘段）里，类象链**早于** `judge_all` 执行，
      此时还没有 `shensha_xiang`（幽冥煞）与 `rangjie`（宜禳）。若在链内自算，
      就会与 `judge_all` 的 `guishen_xiang` 形成**双真源漂移**（同课两处口径不同）。
      ⇒ 故改为「后合并」：链算完 → judge 算完 → 用 judge 的结果回注链。

    【原文依据】(见 guishen_xiang_engine 文件头)
      寅申＝寺观 下L4556｜辰＝寺观 下L10788｜申＝僧（谐音）下L10788
      未＝神鬼·祭祀 下L9631、下L1182｜子＝祷祝鬼神 下L9598｜戌＝塑画（神像）下L9643
    """
    if not isinstance(result, dict):
        return result
    gs = (judged or {}).get('guishen_xiang') or {}
    if not (isinstance(gs, dict) and gs.get('象域')):
        result['寺观鬼祟'] = {'象域': False}
        return result

    result['寺观鬼祟'] = {
        '象域': True,
        '强度': gs.get('强度', 0),
        '候选': gs.get('候选') or [],
        '类象语': gs.get('类象语', ''),
        '祷所': gs.get('祷所', ''),
        '依据': gs.get('依据') or [],
        '边界': ('寺观/僧道/神祠之象；东岳庙、城隍庙抑或土地庙由当地实况定，'
                 '引擎不落专名（三段式第③段交人）；纯叙事层，不进评分链'),
    }

    zhi2cls: Dict[str, str] = {}
    for c in gs.get('候选') or []:
        if isinstance(c, dict) and c.get('支'):
            zhi2cls[str(c['支'])] = str(c.get('建筑类') or '')
    if not zhi2cls:
        return result
    keep = max(int(top_k or 6), 8)

    def _put(row: Dict[str, Any]) -> None:
        z = str(row.get('地支') or '')
        if z not in zhi2cls:
            return
        # 🔴 去重键＝**完整 tag**（不是 建筑类 短名），否则重复调用会叠加
        tag = '僧道寺观：%s' % zhi2cls[z]
        row['寺观象'] = zhi2cls[z]
        xi = row.get('现代象')
        if isinstance(xi, dict):
            arr = [x for x in (xi.get('象') or []) if x and x != tag]
            arr.insert(0, tag)
            xi['象'] = arr[:keep]
        else:
            arr = [x for x in (xi or []) if x and x != tag]
            arr.insert(0, tag)
            row['现代象'] = arr[:keep]

    for ch in (result.get('链') or []):
        for r in ((ch or {}).get('链') or []):
            if isinstance(r, dict):
                _put(r)
    for c in (result.get('收敛候选') or []):
        if isinstance(c, dict):
            _put(c)
    return result


def to_narrative(result: Dict[str, Any], max_len: int = 240) -> str:
    """把推演结果压成一句可用批语的叙事串（不含吉凶）。"""
    if not result:
        return ''
    parts: List[str] = []
    ls = result.get('类神锚定') or {}
    if ls.get('类神'):
        parts.append(f"类神看{'、'.join(ls['类神'][:3])}")
    for c in (result.get('链') or [])[:2]:
        rows = c.get('链') or []
        seg = []
        for r in rows:
            s = r['地支']
            if r.get('天将'):
                s += f"乘{r['天将']}"
            if r.get('遁干'):
                s += f"遁{r['遁干']}"
            if r.get('命中七处'):
                s += f"（{'/'.join(r['命中七处'])}）"
            seg.append(s)
        if seg:
            zs = (rows[0].get('现代象') or {}).get('组合') or ''
            parts.append('→'.join(seg) + (f" ⇒ {zs}" if zs else ''))
    cands = result.get('收敛候选') or []
    xiang = []
    for r in cands[:3]:
        for x in (r.get('现代象') or [])[:2]:
            if x not in xiang:
                xiang.append(x)
    if xiang:
        parts.append('候选象：' + '、'.join(xiang[:6]))
    # P2：推演匹配（多要素组合；待验证强制标注 △）
    tms = result.get('推演匹配') or []
    if tms:
        seg = []
        for t in tms[:3]:
            mark = '△' if t.get('等级') == '待验证' else '✓'
            seg.append(f"{t['事物']}{mark}({t['命中率']})")
        parts.append('推演：' + '、'.join(seg))
    txt = '；'.join(p for p in parts if p)
    return txt[:max_len] + ('…' if len(txt) > max_len else '')


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # 自测：构造课例-19 的简化课象（卯乘朱雀 → 戌 → 巳）
    demo_pan = {d: d for d in DIZHI}
    demo_pan.update({'卯': '戌', '戌': '巳', '巳': '午', '午': '未',
                     '未': '申', '申': '酉'})
    env = {
        'ri_gan': '辛', 'ri_zhi': '酉', 'shichen': '申',
        'san_chuan': ['卯', '戌', '巳'], 'sanchuan': ['卯', '戌', '巳'],
        'chu': '卯', 'zhong': '戌', 'mo': '巳',
        'tian_jiang': {'卯': '朱雀', '戌': '白虎', '巳': '贵人'},
        'tiandi_pan': demo_pan,
        'si_ke': [('第一课', '卯', '酉', '朱雀')],
    }
    r = pursue_chain(env, category='寻物', max_depth=3)
    print('类神锚定:', r['类神锚定']['类神'][:3], '| 来源:', r['类神锚定']['来源'])
    print('链数:', len(r['链']))
    for c in r['链']:
        print(' 起点', c['起点来源'], '→',
              ' → '.join(f"{x['地支']}{('乘' + x['天将']) if x['天将'] else ''}" for x in c['链']))
    print('收敛候选:')
    for x in r['收敛候选']:
        print(f"  {x['地支']}{x['天将']} 证据={x['证据']} 七处={x['命中七处']} 象={x['现代象'][:2]}")
    print('叙事:', r['叙事'])
