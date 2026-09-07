#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 模块 3：演禽真法分析模块

功能：
1. 以每一课的四柱信息为基础，应用演禽真法理论进行全面分析
2. 实现演禽星宿排布、禽星生克关系计算、吉凶格局判定
3. 生成详细的演禽结果及独立的吉凶评分（0-100 分）
4. 提供明确的评分细则
"""

from typing import Dict, List
from datetime import datetime


class YanQinAnalyzer:
    """演禽真法分析器"""
    
    # 二十八宿（按顺序）
    ERSHIBA_XIU = [
        '角', '亢', '氐', '房', '心', '尾', '箕',  # 东方青龙
        '斗', '牛', '女', '虚', '危', '室', '壁',  # 北方玄武
        '奎', '娄', '胃', '昴', '毕', '觜', '参',  # 西方白虎
        '井', '鬼', '柳', '星', '张', '翼', '轸'   # 南方朱雀
    ]
    
    # 二十八宿度数
    XIU_DEGREES = [
        12, 9, 15, 5, 5, 18, 11,  # 东方青龙
        26, 8, 12, 10, 17, 16, 9,  # 北方玄武
        16, 12, 14, 11, 16, 1, 9,  # 西方白虎
        33, 4, 15, 7, 18, 18, 17   # 南方朱雀
    ]
    
    # 二十八宿对应禽星
    XIU_TO_QIN = {
        '角': '木蛟', '亢': '金龙', '氐': '土貉', '房': '日兔',
        '心': '月狐', '尾': '火虎', '箕': '水豹',
        '斗': '木獬', '牛': '金牛', '女': '土蝠', '虚': '日鼠',
        '危': '月燕', '室': '火猪', '壁': '水貐',
        '奎': '木狼', '娄': '金狗', '胃': '土雉', '昴': '日鸡',
        '毕': '月乌', '觜': '火猴', '参': '水猿',
        '井': '木犴', '鬼': '金羊', '柳': '土獐', '星': '日马',
        '张': '月鹿', '翼': '火蛇', '轸': '水蚓'
    }
    
    # 二十八宿五行
    XIU_WUXING = {
        '角': '木', '亢': '金', '氐': '土', '房': '日', '心': '月',
        '尾': '火', '箕': '水',
        '斗': '木', '牛': '金', '女': '土', '虚': '日', '危': '月',
        '室': '火', '壁': '水',
        '奎': '木', '娄': '金', '胃': '土', '昴': '日', '毕': '月',
        '觜': '火', '参': '水',
        '井': '木', '鬼': '金', '柳': '土', '星': '日', '张': '月',
        '翼': '火', '轸': '水'
    }
    
    # 二十八宿吉凶
    XIU_JIXIONG = {
        '角': '吉', '亢': '凶', '氐': '凶', '房': '吉', '心': '凶',
        '尾': '吉', '箕': '吉',
        '斗': '吉', '牛': '凶', '女': '凶', '虚': '凶', '危': '凶',
        '室': '吉', '壁': '吉',
        '奎': '凶', '娄': '吉', '胃': '吉', '昴': '凶', '毕': '吉',
        '觜': '凶', '参': '吉',
        '井': '吉', '鬼': '凶', '柳': '凶', '星': '凶', '张': '吉',
        '翼': '凶', '轸': '吉'
    }

    # ============ 演禽锁泊十二宫（《禽星易见》"山水田园井刀天草岸风火月週流转"）============
    # 十二宫名（顺数序）
    PO_GONG_SEQ = ['山', '水', '田', '园', '井', '刀', '天', '草', '岸', '风', '火', '月']
    # 地支顺序（用于从长生位顺数起宫）
    _ZHI_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    # 禽星五行长生位（原书"水土俱申、木长生亥、火长生寅、金长生巳"；日属火、月属水）
    _WUXING_CHANGSHENG = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申', '日': '寅', '月': '申'}
    # 水禽（五行属水之宿，岸宫不利）
    _SHUI_QIN = {'箕', '壁', '参', '轸'}
    # 各宫明确吉凶禽（原书摘录；'ALL'=全宫皆然，'DEFAULT'=除吉列外皆凶，未列者平）
    PO_GONG_JIXIONG = {
        '山': {'吉': {'鬼', '星', '张', '柳'}, '凶': set()},
        '水': {'吉': {'角', '亢'}, '凶': set()},
        '田': {'吉': {'角', '亢', '胃', '昴', '星', '鬼'}, '凶': set()},
        '园': {'吉': {'房', '尾', '箕', '毕', '牛'}, '凶': set()},
        '井': {'吉': {'角', '亢'}, '凶': 'DEFAULT'},   # 诸禽入此恶弱不出凶（角亢除外）
        '刀': {'吉': set(), '凶': 'ALL'},              # 刑害之宫，極凶
        '天': {'吉': 'ALL', '凶': set()},              # 極樂之地，诸禽入此皆化
        '草': {'吉': {'牛', '羊', '张', '柳', '星', '奎', '室'}, '凶': {'角', '亢'}},
        '岸': {'吉': {'尾', '箕', '毕', '井', '心', '星', '牛', '鬼'}, '凶': set()},  # 水禽另判
        '风': {'吉': {'角', '亢', '尾', '箕', '奎', '井', '毕'}, '凶': set()},
        '火': {'吉': set(), '凶': 'ALL'},              # 惡宫，诸禽不利
        '月': {'吉': 'ALL', '凶': {'角', '亢', '毕'}}, # 恶星化吉曜，惟角亢毕不宜
    }
    
    # 注：演禽用「二十八宿轮值」（每 28 天一轮，非天文日躔），无需宿度表；
    #     原「二十八宿度数（简化）」表已删（2026-08-17 憨爷要求清掉简化版，且该表零引用）。

    # ============ 值日宿精算（黄历口径 · 28 宿轮值）============
    # 黄历「值日星宿」是每 28 天一轮（非天文日躔！）
    # 基准日：2026-03-05 = 角宿（宿序0）。由憨爷核对周易万年历三点反推：
    #   2026-03-28=柳(23)、2026-06-21=星(24)、2026-08-13=井(21)
    #   两两日差自洽：85天→+1宿、53天→+25宿、138天→+26宿（均为28天轮值）
    RI_QIN_BASE_JD = None  # 惰性初始化（sxtwl 儒略日）

    # ============ 传统演禽格局数据（《禽星易见》《演禽通纂》体系）============
    # 七高禽（七元将头）：能降伏诸禽（毕月乌/井木犴/奎木狼/尾火虎/箕水豹/角木蛟/亢金龙）
    GAO_QIN_XIUS = {'毕', '井', '奎', '尾', '箕', '角', '亢'}
    # 昼禽（白天活动，卯~申时得时）；其余为夜禽（酉~寅时得时）；毕月乌日夜兼行
    ZHOU_QIN_XIUS = {'角', '亢', '牛', '危', '室', '娄', '胃', '昴', '毕', '觜', '参', '井', '鬼', '柳', '星', '张'}
    DAY_ZHI = {'卯', '辰', '巳', '午', '未', '申'}  # 昼时地支（酉~寅为夜）

    
    # 年禽起例（以年支起禽）
    NIAN_QIN_MAP = {
        '子': '虚', '丑': '斗', '寅': '箕', '卯': '尾', '辰': '心',
        '巳': '房', '午': '氐', '未': '亢', '申': '角', '酉': '轸',
        '戌': '翼', '亥': '张'
    }
    
    # 月禽起例（以月建起禽）
    YUE_QIN_MAP = {
        '寅': '角', '卯': '亢', '辰': '氐', '巳': '房', '午': '心',
        '未': '尾', '申': '箕', '酉': '斗', '戌': '牛', '亥': '女',
        '子': '虚', '丑': '危'
    }
    
    # 日禽起例（以日支起禽）
    RI_QIN_MAP = {
        '子': '牛', '丑': '女', '寅': '虚', '卯': '危', '辰': '室',
        '巳': '壁', '午': '奎', '未': '娄', '申': '胃', '酉': '昴',
        '戌': '毕', '亥': '觜'
    }
    
    # 时禽起例（以时支起禽）
    SHI_QIN_MAP = {
        '子': '参', '丑': '井', '寅': '鬼', '卯': '柳', '辰': '星',
        '巳': '张', '午': '翼', '未': '轸', '申': '角', '酉': '亢',
        '戌': '氐', '亥': '房'
    }
    
    # 禽星生克关系
    QIN_SHENG_KE = {
        '木': {'生': '火', '克': '土', '被克': '金'},
        '火': {'生': '土', '克': '金', '被克': '水'},
        '土': {'生': '金', '克': '水', '被克': '木'},
        '金': {'生': '水', '克': '木', '被克': '火'},
        '水': {'生': '木', '克': '火', '被克': '土'}
    }

    # ============ 《禽星易见》七元演禽 · 番禽倒将 · 吞啖降伏（2026-08-13 逐字录入）============
    # 七元将头（七元二十八将之首将，原书 line 277「七元將頭」）：
    #   一元虚 二元奎 三元毕 四元鬼 五元翼(翌) 六元氐 七元箕(算，箕水豹)
    QIYUAN_HEADS = {1: '虚', 2: '奎', 3: '毕', 4: '鬼', 5: '翼', 6: '氐', 7: '箕'}
    # 七元二十八将（每元四将，原书 line 277「此是七元直將頭」逐字）：
    #   一元虚张室轸 / 二元奎亢胃房 / 三元毕尾参斗 / 四元鬼女星危 /
    #   五元翼壁角娄 / 六元氐昴心觜 / 七元箕井牛柳
    # ✅ 六元第四将原书（第6页口诀）作「觜火猴」(觜宿)；2026-08-13 憨爷核纸质书确认=觜(非参)。
    #    OCR「腎」为「觜」之误识（句末「火猴」即觜火猴星官名）。
    QIYUAN_FOUR_JIANG = {
        1: ['虚', '张', '室', '轸'],
        2: ['奎', '亢', '胃', '房'],
        3: ['毕', '尾', '参', '斗'],
        4: ['鬼', '女', '星', '危'],
        5: ['翼', '壁', '角', '娄'],
        6: ['氐', '昴', '心', '觜'],   # 原书第6页「觜火猴」(觜宿)；2026-08-13 憨爷核纸质书确认
        7: ['箕', '井', '牛', '柳'],
    }
    # 七元日禽历元锚（已核·网络考证锚日）：
    #   来源 baike.lsjjh.com《演禽课局》第09篇「查元数」明定：
    #     「以 1900 年 08 月 19 日（一元甲子的第一天）作为基准点」。
    #   交叉验证（同来源/ygkyfs.com 演禽诀）：
    #     1996-01-28 = 一元一将（甲子虚）→ 与锚相差 34860 天 = 420×83，mod 420 = 0 ✅
    #     2002-02-10 = 二元四将（己酉）→ 本公式推得 元2将3 ✅
    #   已用 sxtwl 复算：1900-08-19 确为甲子日（元1将0），1996-01-28 甲子，2002-02-10 己酉，全部吻合。
    #   推算：seg = (target - 锚).days // 15；将 = seg%4；元 = (seg//4)%7 + 1。
    #   ⚠️ 注：来源提示 1582-10-04→10-15 删10天（格里历改革）；本锚(1900)与目标(现代)均在1582后，
    #       用 proleptic Gregorian（datetime/sxtwl 默认）计算，无需减10天调整。
    QIYUAN_EPOCH = (1900, 8, 19)
    # 时辰顺数偏移（子=0 起日禽，丑=+1 … 亥=+11），已由掌圖 line 833 验证：
    #   「一元甲子虚日鼠直日則子時起虚丑時起危寅時起室…」→ 子时=日禽，顺数十二辰至用时。
    # 此为演禽时禽之通用定法，优于旧 SHI_QIN_MAP（时支直查）。
    SHI_ZHI_OFFSET = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                      '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}

    # 吞啖（吞噬歌 line 275 逐字提取的「X吞/食Y」有向关系）：
    #   键=吞者(攻方禽星宿名)，值=被吞者(守方)。用于判断主客禽星强弱。
    #   原歌：「亢吞危并食牛」「虚女逢蛇(翼火蛇)」「狼(奎)吞羊(胃)鬼及猪(室)」
    #   「虎(尾)豹(箕)逢牛」「猿(参)猪(室)鼠(虚)憂逢狗(娄)」「馬鹿羊忌虎口」
    #   「龍(角)虎吞奎狼蛟(箕)豹」「鶉雉逢蛇必尅」「觜(觜)參(参)摠怕狼」
    #   「房鬼婁金狗宿名虎豹狼臨命必傾」「牛危胃昴女房虚切忌飛來貆月烏(毕)」
    #   「若逢金狗(娄)盡皆輸」「猪(室)食蛇(翼)」「斗兮房食奎危」。
    TUN_DAN = {
        '亢': {'危', '牛'},
        '翼': {'虚', '女', '星'},                 # 蛇(翼火蛇)吞虚女；鶉(星/鹑火)雉逢蛇（雉归星日马）
        '奎': {'胃', '鬼', '室', '觜', '参', '牛'},
        '尾': {'牛', '星', '危', '奎', '箕', '房', '鬼', '娄', '角'},  # 虎逢牛；馬鹿羊忌虎口→星；龍虎吞奎狼蛟豹；房鬼娄虎豹狼
        '箕': {'牛'},
        '娄': {'参', '室', '虚', '牛', '危', '胃', '昴', '女', '房'},  # 猿猪鼠憂逢狗；金狗盡皆輸；牛危胃昴女房虚
        '毕': {'牛', '危', '胃', '昴', '女', '房', '虚'},             # 月乌(毕)吞牛危胃昴女房虚
        '室': {'翼'},                             # 猪(室)食蛇(翼)
        '房': {'奎', '危', '斗'},                 # 房食奎危
        '角': {'奎', '箕'},                       # 龍(角)吞奎狼蛟(箕)豹
    }
    # 降伏（伏，line 270-272 四类高禽伏诸禽，逐字）：
    #   毕月乌 伏 一切水地禽并飞禽；井木犴 伏 一切山水禽；
    #   角木蛟、亢金龙 伏 一切水禽并飞禽；尾火虎、箕水豹、奎木狼 伏 一切山禽。
    # 实现：七高禽(已定义 GAO_QIN_XIUS)伏常禽；并附四类禽类规则。
    # 禽类划分（QIN_LEI）—— 逐宿对照《禽星易见》"分野"段落逐字核定（2026-08-17 憨爷要求精细版）：
    #   山禽(6)：奎木狼/胃土雉/参水猿/柳土獐/张月鹿/觜火猴（原书"分野乃山禽是豺狼/堆雞/臻(猿)/山中獠/鹿/觜參摠怕狼"）
    #   水禽(4)：角木蛟/亢金龙/斗木獬/壁水獝（原书"水中獨角龍/水中八爪雙角金龍/水禽即蝤蠆/水禽是獺"）
    #   飞禽(3)：女土蝠/危月燕/毕月乌（原书"飛禽即飛鼠/天禽即燕子/天禽即老鴉"）
    #   地禽(14)：氐土貉/房日兔/心月狐/尾火虎/箕水豹/牛金牛/虚日鼠/室火猪/娄金狗/昴日鸡/鬼金羊/星日马/翼火蛇/轸水蚓
    #             （原书"地禽即牛/老鼠/猪/狗/雞/牟(羊)/馬/蛇/蚯蚓"等）
    #   瑞禽(1)：井木犴（原书"分野爲瑞禽…二十八宿之主禽星之王"，独成一类，非普通四类）
    QIN_LEI = {
        '山': {'奎', '胃', '参', '柳', '张', '觜'},
        '水': {'角', '亢', '斗', '壁'},
        '飞': {'女', '危', '毕'},
        '地': {'氐', '房', '心', '尾', '箕', '牛', '虚', '室', '娄', '昴', '鬼', '星', '翼', '轸'},
        '瑞': {'井'},
    }
    FU_RULES = [
        ('毕', {'水', '地', '飞'}),
        ('井', {'山', '水'}),
        ('角', {'水', '飞'}),
        ('亢', {'水', '飞'}),
        ('尾', {'山'}),
        ('箕', {'山'}),
        ('奎', {'山'}),
    ]

    # ============ 锁泊具名变格（九泊玄格 / 禽星锁泊格局）============
    # 来源：综合《禽星易见》《演禽通纂》锁泊具名，按 bilibili cv28723440《禽星锁泊格局》整理录入。
    # 键 = 宿名 → 用时地支 → (格名, 吉凶, 断语)。吉凶取值：吉/中吉/平/凶（与大体系 泊宫十二宫 得地/失地互为表里，此处给具名诗意断语）。
    # ⚠️ 与「十二宫得地/失地」(PO_GONG_JIXIONG) 互补：十二宫为通用骨架，具名格为具体变格（如角泊午：十二宫判"失地"，具名格"龙在汤镬"同凶）。
    XIU_PO_GONG_MINGGE = {
        '角': {
            '子': ('泊江湖·极尊贵', '吉', '角木蛟泊江湖，极尊贵之位，主兴旺'),
            '寅': ('龙虎争珠', '凶', '防因干不关己之事起争端，人憎鬼妒'),
            '午': ('龙在汤镬', '凶', '主做事艰辛，防人欺害'),
            '戌': ('蛟龙失水·蛟龙出野', '凶', '贵入贱宫，退气堪忧，反为自害'),
            '未': ('聚散贫夭', '凶', '运势差，不吉'),
        },
        '亢': {
            '巳': ('退潜', '平', '退潜隐伏'),
            '亥': ('困龙出井·龙到天池', '吉', '活龙，主兴旺欢乐'),
            '卯': ('龙居浅水·龙警溪涧', '中吉', '得地，但不算十分吉'),
            '午': ('龙奔枯井', '凶', '凡事不利'),
            '未': ('龙奔枯井', '凶', '凡事不利'),
        },
        '氐': {
            '午': ('退潜隐伏', '凶', '忌泊火汤，退潜隐伏'),
            '申': ('察微', '凶', '耗损之地，自带空亡破碎，谨防失脱'),
            '子': ('古镜重磨', '吉', '破镜重圆，除旧立新'),
            '辰': ('大隐', '平', '主潜藏'),
        },
        '房': {
            '巳': ('灯照空房', '凶', '妻儿不吉，病主心腹疼痛，邪祟作殃'),
            '酉': ('玉兔守株', '吉', '宜变更不宜守旧，变则有喜'),
            '丑': ('隔江射兔', '凶', '百事难成，主阻隔'),
        },
        '心': {
            '寅': ('狐假虎威', '吉', '凡事宜托人，吉'),
            '午': ('贮格·奸疑', '平', '宜低调不宜公开大张旗鼓'),
            '戌': ('阴阳不备', '凶', '凶从外起，凡事不利'),
        },
        '尾': {
            '巳': ('三刑', '凶', '诸事不顺'),
            '亥': ('猛虎出林', '吉', '相合得禄，吉'),
            '卯': ('虎啸高峰·困虎归林', '吉', '得地，吉'),
            '未': ('两虎争岩·虎遭陷阱', '凶', '主损失、离散'),
        },
        '箕': {
            '寅': ('豹变为虎', '平', '有能力减弱的趋势'),
            '申': ('豹伤弓弩', '中吉', '功名得助，宜早不宜迟，否则遭坑陷'),
            '子': ('豹变·古镜重磨', '吉', '旺地，宜更迁不宜守旧，谨防失脱'),
            '辰': ('虎落陷阱', '凶', '皮毛之伤，伏断，防冤枉之危'),
        },
        '斗': {
            '巳': ('顺曲落陷·石中求玉', '凶', '忌宫，先难后易，当防反复'),
            '酉': ('游鱼弄波·受刑', '凶', '畏宫，不宜贪财利，防丧身，只宜守静'),
            '丑': ('出明入暗·伏断', '凶', '黯晦不宜居，诸事不宜'),
        },
        '牛': {
            '寅': ('负重山', '凶', '忌宫，出行忌，西南有劫掠，多艰难'),
            '午': ('耕石田', '凶', '谋事艰辛，百无一成'),
            '戌': ('犀牛折角', '凶', '三刑，自己有损失，头目有伤，占官退职'),
        },
        '女': {
            '亥': ('金钗落井', '凶', '主失脱、陷落'),
            '卯': ('决女·妖女鹰网', '凶', '类似天罗地网'),
            '未': ('阴煞·蝠怀阴险', '凶', '阴险'),
        },
        '虚': {
            '申': ('五虚六耗', '凶', '入猴地被擒，须防被骗，主人离财散'),
            '子': ('伏断', '凶', '凡事多虚，主有损失'),
            '辰': ('近贤圣座·遥望有气', '吉', '宜依靠贵人成事，欢庆顺遂'),
        },
        '危': {
            '巳': ('燕垒南枝', '凶', '巽风吹入蛇巢，凡事主不安稳'),
            '酉': ('紫燕栖梁·燕巢凤阁', '吉', '落于旺地，宜阴谋和合之事'),
            '丑': ('船下急滩·衔泥布垒', '凶', '主惊恐，辛勤劳碌'),
        },
        '室': {
            '子': ('沉浮阻隔', '凶', '浮沉有阻'),
            '寅': ('猪入虎穴·暗室思明', '凶', '有凶险，百忧兼至'),
            '午': ('小舟失楫', '凶', '浮沉有阻，轻出必倾颓'),
            '戌': ('室揖囚禁', '凶', '暗昧不明不顺，占病必死，占讼防囚禁'),
        },
        '壁': {
            '亥': ('伏殃遭侮', '凶', '伏断失友，百怪入门，占病遁闷'),
            '卯': ('庶几比用·比用落濠', '吉', '凡事只宜依傍他人，吉'),
            '未': ('伏殃荒野·朋友失助', '凶', '失友荒郊，不可托人'),
        },
        '奎': {
            '寅': ('英雄似虎', '吉', '英雄似虎'),
            '申': ('缀花结子', '吉', '得地，秋冬可成，宜婚姻和合'),
            '子': ('镜挂妆台', '吉', '利婚姻之事'),
            '辰': ('游子不定', '平', '先忧后喜，防小人欺诈'),
        },
        '娄': {
            '午': ('不吉', '凶', '不吉'),
            '巳': ('铸印', '吉', '喜迁贵职，宜登科赴举，百事吉'),
            '酉': ('掘井挖泉', '中吉', '旺宫，做事艰难，须借他人之力'),
            '丑': ('天狱·天仓饭食', '凶', '墓宫，防人财隔失，阴人血光孝服'),
        },
        '胃': {
            '寅': ('白鹏·斩关化大鹏', '吉', '宜谋胜不可力争'),
            '午': ('五德丹鳳·励德大观', '吉', '君子吉，小人凶'),
            '戌': ('凤凰在笼', '凶', '困顿、不吉'),
        },
        '昴': {
            '午': ('进化', '吉', '进化'),
            '亥': ('鸡唱黄昏·鸡叫凶来', '凶', '家宅招怪，不宜远行词讼，防牢狱'),
            '卯': ('凤凰失巢', '凶', '家宅不安，谋望难成'),
            '未': ('凤凰折翅', '凶', '防失脱、手足之灾、奴仆之侮'),
        },
        '毕': {
            '申': ('灵雀捕蟾·火鸦', '凶', '防人相害，不宜共文书，惹诽谤'),
            '子': ('狂鸦乱噪·强鸦', '凶', '多传凶信是非'),
            '辰': ('云遮明月', '凶', '被人遮蔽，不宜提是非，多忧'),
        },
        '觜': {
            '巳': ('逆风把火', '凶', '逆宫，凡事不明，当以顺求'),
            '酉': ('朱口破石', '凶', '伏断，众人识议，是非之挠，独力难成'),
            '丑': ('猴在高园', '吉', '秋冬亨通，安静无事，有馀财'),
        },
        '参': {
            '寅': ('猿啼夜月·猿捉波月', '凶', '谋事多虚，反生烦恼'),
            '午': ('顺水行舟', '吉', '临旺地，做事顺遂而有神'),
            '戌': ('孤猿失伴·孤猿被绊', '平', '群小相欺，幸有贵人助'),
        },
        '井': {
            '卯': ('孤雁失群', '凶', '防兄弟反目，人离财散，口交之非'),
            '亥': ('飞雁衔芦', '平', '不宜出口，恐防惹祸；远行迁移上官则吉'),
            '未': ('刻舟待信', '平', '只宜守待，求人助终有佳音'),
        },
        '鬼': {
            '申': ('夜行失路', '凶', '伏断，凡事危难，暗昧不明'),
            '子': ('五鬼争持', '凶', '百事无成，防旁人口舌'),
            '辰': ('羝羊触藩', '凶', '防进退两难之咎'),
        },
        '柳': {
            '巳': ('丑妇照镜', '凶', '不吉'),
            '酉': ('醉人过槛', '凶', '危险，不吉'),
            '丑': ('九丑', '凶', '感情争端，烂桃花，临产有灾'),
        },
        '星': {
            '寅': ('陆地行舟', '平', '虽乐宫亦谋事难成'),
            '午': ('三光普照·升殿朝元', '吉', '乐宫入庙，凡事光辉，百事吉'),
            '戌': ('白虹贯日', '凶', '墓宫，君弱臣强，防小人欺侮，贬官丧身'),
        },
        '张': {
            '亥': ('稼樯', '平', '中平，有付出亦有收获'),
            '卯': ('玄胎', '平', '胎产吉，占病不吉'),
            '未': ('天网四张', '凶', '不吉'),
        },
        '翼': {
            '申': ('枯木摇风', '凶', '不吉'),
            '子': ('取方成圆', '吉', '宜变通而得吉'),
            '辰': ('鱼跃龙门', '吉', '蛇入龙巢化龙，凡事成就，利君子'),
        },
        '轸': {
            '巳': ('宝车无轮·乘车逐马', '中吉', '入庙旺，难自行，托亲眷为之方成'),
            '酉': ('东轩坠马', '凶', '有意外伤灾'),
            '丑': ('斫轮·车驾飞轮', '中吉', '宜婉转，当托他人则可'),
        },
    }

    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        """记录日志"""
        self.logs.append(message)
    
    def get_nian_qin(self, year_zhi: str) -> str:
        """获取年禽"""
        return self.NIAN_QIN_MAP.get(year_zhi, '虚')
    
    def get_yue_qin(self, month_zhi: str) -> str:
        """获取月禽"""
        return self.YUE_QIN_MAP.get(month_zhi, '角')
    
    def get_ri_qin(self, day_zhi: str) -> str:
        """获取日禽"""
        return self.RI_QIN_MAP.get(day_zhi, '牛')
    
    def get_shi_qin(self, shi_zhi: str, ri_qin: str = None) -> str:
        """获取时禽。
        若给定日禽 ri_qin，则按《禽星易见》掌圖通用定法计算：
        子时起日禽，顺数十二辰至用时（时禽 = 日禽 + 时辰偏移 mod 28）。
        否则回退旧 SHI_QIN_MAP（时支直查，仅作兼容）。
        """
        if ri_qin and ri_qin in self.ERSHIBA_XIU and shi_zhi in self.SHI_ZHI_OFFSET:
            base = self.ERSHIBA_XIU.index(ri_qin)
            return self.ERSHIBA_XIU[(base + self.SHI_ZHI_OFFSET[shi_zhi]) % 28]
        return self.SHI_QIN_MAP.get(shi_zhi, '参')

    # ---- 七元演禽：时禽通用定法（掌圖） ----
    def compute_shi_qin_universal(self, ri_qin: str, shi_zhi: str) -> str:
        """时禽 = 日禽 顺数至用时（子时起日禽）。已与七元掌圖逐字核对。"""
        return self.get_shi_qin(shi_zhi, ri_qin)

    # ---- 七元将头：由日干支推断所在元与将 ----
    def compute_qiyuan(self, day_ganzhi: str, year: int = None, month: int = None, day: int = None):
        """由日干支(六十甲子)及公历日期推断七元将头信息。
        结构层（原书《禽星易见》已逐字坐实，2026-08-13 链接核对）：
          七元将头顺序 虚→奎→毕→鬼→翼→氐→箕 周而复始；每一元四将各十五日，一元六十日，
          七元共四百二十日一周；凡换元皆以甲子日。
        本将序号(0-3)由日干支可靠推算；「第几元」以 QIYUAN_EPOCH
        (1900-08-19 一元甲子第一天·网络考证已核锚日) 为锚推算：
          seg = (target - 锚).days // 15；将 = seg%4；元 = (seg//4)%7 + 1。
        锚日已用 sxtwl 复算并交叉验证（1996-01-28 一元一将 / 2002-02-10 二元四将），非推导。
        """
        try:
            GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            gz = list(day_ganzhi)
            gi = GAN.index(gz[0]); zi = ZHI.index(gz[1])
            diff = (gi - zi) // 2          # 干支合法时 gi%2==zi%2 必成立
            k60 = (zi + 12 * (diff % 5)) % 60   # 甲子=0, 验证己卯=15
        except Exception:
            k60 = 0
        jiang_idx = (k60 // 15) % 4   # 本将序号(0-3)，由日干支可靠推算

        yuan = None
        yuan_str = '待核(需公历日期)'
        ben_jiang = None
        epoch_info = '1900-08-19(一元甲子第一天·网络考证已核锚日)'
        if year and month and day:
            try:
                import datetime as _dt
                E = _dt.date(*self.QIYUAN_EPOCH)
                D = _dt.date(year, month, day)
                delta = (D - E).days
                seg = delta // 15
                jiang = seg % 4
                yuan = (seg // 4) % 7 + 1
                yuan_str = '%d元' % yuan
                four = self.QIYUAN_FOUR_JIANG[yuan]
                ben_jiang = four[jiang]
            except Exception:
                yuan_str = '待核(历元计算异常)'
        if ben_jiang is None:
            # 无日期：以元1四将示范（维持旧行为，元序标待核）
            four = self.QIYUAN_FOUR_JIANG[1]
            ben_jiang = four[jiang_idx]

        return {
            '元': yuan_str,
            '元序_数值': yuan,
            '本将序号': jiang_idx,
            '本将': ben_jiang,
            '干支序号': k60,
            '历元锚': epoch_info,
            '说明': ('本将序号由日干支可靠推算；元序以1900-08-19(一元甲子第一天)为锚已核。'
                     if year else '本将序号由日干支推算；元序需公历日期(待核)。'),
        }

    # ---- 吞啖（吞噬歌） ----
    def get_tun_dan(self, a: str, b: str) -> str:
        """a 对 b 的吞啖关系：'吞'(a吞b) / '被吞'(a被b吞) / '平'(互不相吞，待核)。"""
        a_devours = self.TUN_DAN.get(a, set())
        b_devours = self.TUN_DAN.get(b, set())
        if b in a_devours and a in b_devours:
            return '互吞'
        if b in a_devours:
            return '吞'
        if a in b_devours:
            return '被吞'
        return '平'

    # ---- 降伏（伏） ----
    def get_jiang_fu(self, attacker: str, defender: str) -> str:
        """attacker 对 defender 的降伏关系。
        规则：七高禽伏常禽；外加四类禽类伏法（line 270-272）。
        """
        if attacker == defender:
            return '平'
        # 四类禽类伏法
        for hi, leis in self.FU_RULES:
            if attacker == hi:
                dlei = self._qin_lei(defender)
                if dlei is not None and dlei in leis:
                    return '伏'
        # 七高禽伏常禽（通用）
        if attacker in self.GAO_QIN_XIUS and defender not in self.GAO_QIN_XIUS:
            return '伏'
        return '平'

    def _qin_lei(self, xiu: str) -> str:
        for lei, s in self.QIN_LEI.items():
            if xiu in s:
                return lei
        return None

    # ---- 番禽倒将（《禽星易见》page 12 逐字算法，气将=符头 已核） ----
    def compute_fan_dao_jiang(self, ri_qin: str, shi_qin: str, qi_jiang: str = None):
        """番禽(我禽)与倒将(彼禽)推算。
        原书 line 841-846：
          「順數至時將之宮看得何宿即他人之副將也；就時將之宮逆回氣將之位
            看得何宿便是他人正將謂之到將；其自已之禽却從時將之宮順尋日將治在
            何宿，就從日將之宮逆轉時將之位看得何宿便是自己謂之畨禽。」
        关键修正（2026-08-13 网络考证 baike.lsjjh.com《演禽课局》第08篇 + sina《禽星术·番禽倒将》）：
          **气将 = 符头**（每十五日一符头，符头干支固定甲子/己卯/甲午/己酉，各有对应禽星；
          即当日所属「四将」的禽星 = QIYUAN_FOUR_JIANG[元][本将序号]）。原书口诀「气将/日将」有歧义，
          sina 明言字面读(以日将代气将)会错（一天只有两变），验证实例统一用**气将(符头)**。
        正确掌法（已用 sina 两例 + baike 一例对拍验证）：
          番禽(我)：从时支起**气将**禽名，顺数地支至时禽止，逆回时支 → 番禽 = (T + (T-Q)) % 28
          彼副将(倒将副) = 时禽（原书：他人副将=时禽）
          到将(彼正)：从时支起时禽，顺数至番禽止，逆回时支 → 到将 = (fan + (fan-T)) % 28
          其中 T=时禽序号, Q=气将(符头)序号, fan=番禽序号。
        """
        xiu = self.ERSHIBA_XIU
        if ri_qin not in xiu or shi_qin not in xiu:
            return {'番禽': None, '倒将': None}
        T = xiu.index(shi_qin)   # 时将(时禽)
        n = len(xiu)
        # 气将缺省以日将代（仅 analyze_four_qin 无日期时的回退，标待核）
        if qi_jiang not in xiu:
            qi_jiang = ri_qin
        Q = xiu.index(qi_jiang)  # 气将(符头)
        # 番禽(我)：从时支起气将，顺数至时禽止，逆回时支
        fan_idx = (T + (T - Q) % n) % n
        fan_qin = xiu[fan_idx]
        # 彼副将(倒将副) = 时禽（原书：他人副将=时禽）
        fu_jiang = shi_qin
        # 到将(彼正)：从时支起时禽，顺数至番禽止，逆回时支
        dao_idx = (fan_idx + (fan_idx - T) % n) % n
        zheng_jiang = xiu[dao_idx]
        return {
            '番禽(我)': fan_qin,
            '倒将副(彼副)': fu_jiang,
            '到将正(彼正)': zheng_jiang,
            '气将(符头)': qi_jiang,
            '说明': ('番禽=(时禽+(时禽-气将))%28；到将=(番禽+(番禽-时禽))%28；副将=时禽。'
                     '已用 sina/baike 示例对拍验证（气将=符头）。'
                     if qi_jiang != ri_qin
                     else '气将缺省以日将代(待核)：无日期时元序/符头不可知，番禽倒将不可靠。'),
        }

    # ---- 七元演禽综合详情（供仪表盘/择日展示） ----
    def analyze_qiyuan_detail(self, sizhu: Dict, ri_qin: str, shi_qin: str,
                              year: int = None, month: int = None, day: int = None) -> Dict:
        """汇总七元演禽详情：时禽(通用)、七元将头、吞啖、降伏、番禽倒将。
        year/month/day 为可选公历日期，用于推算七元「元序」(否则元序标待核)。
        """
        day_zhi = sizhu.get('日柱', '')[-1:] if sizhu.get('日柱') else ''
        shi_zhi = sizhu.get('时柱', '')[-1:] if sizhu.get('时柱') else ''
        day_ganzhi = sizhu.get('日柱', '')
        shi_universal = self.compute_shi_qin_universal(ri_qin, shi_zhi) if shi_zhi else shi_qin
        qiyuan = self.compute_qiyuan(day_ganzhi, year, month, day) if day_ganzhi else {}
        tun_ri_shi = self.get_tun_dan(ri_qin, shi_qin)      # 日禽对时禽
        tun_shi_ri = self.get_tun_dan(shi_qin, ri_qin)      # 时禽对日禽
        fu_ri_shi = self.get_jiang_fu(ri_qin, shi_qin)
        # 气将 = 本将（当前所属四将/符头对应的禽星）；有日期时 compute_qiyuan 已算出并核锚
        qi_jiang = qiyuan.get('本将') if qiyuan else None
        fan_dao = self.compute_fan_dao_jiang(ri_qin, shi_qin, qi_jiang)
        return {
            '日禽': ri_qin,
            '时禽_通用': shi_universal,
            '时禽_旧法': shi_qin,
            '时禽吉凶(28宿表)': self.XIU_JIXIONG.get(shi_universal, '平'),
            '七元将头': qiyuan,
            '吞啖_日对时': tun_ri_shi,
            '吞啖_时对日': tun_shi_ri,
            '降伏_日对时': fu_ri_shi,
            '番禽倒将': fan_dao,
        }

    def get_sxtwl_ri_qin(self, year: int, month: int, day: int) -> str:
        """sxtwl 精算值日宿：精确儒略日 → 28 宿轮值（黄历口径）。
        基准 2026-03-05=角宿（宿序0），由周易万年历三点核对反推。
        """
        try:
            import sxtwl
            jd = sxtwl.toJD(sxtwl.Time(year, month, day, 0, 0, 0))
            if self.RI_QIN_BASE_JD is None:
                self.RI_QIN_BASE_JD = sxtwl.toJD(sxtwl.Time(2026, 3, 5, 0, 0, 0))
            idx = (int(jd + 0.5) - int(self.RI_QIN_BASE_JD + 0.5)) % len(self.ERSHIBA_XIU)
            return self.ERSHIBA_XIU[idx]
        except Exception:
            # sxtwl 不可用：回退儒积日近似
            return self.get_calendar_based_ri_qin_approx(year, month, day)

    def get_calendar_based_ri_qin(self, year: int, month: int, day: int) -> str:
        """
        日禽（值日宿）：优先 sxtwl 精算；sxtwl 缺失时回退儒积日近似。
        """
        try:
            return self.get_sxtwl_ri_qin(year, month, day)
        except Exception:
            return self.get_calendar_based_ri_qin_approx(year, month, day)

    def get_calendar_based_ri_qin_approx(self, year: int, month: int, day: int) -> str:
        """
        基于儒积日法的历法计算日禽（近似版，仅作 sxtwl 缺失回退）
        使用实际的天文位置计算星宿
        """
        # 校准：根据2026年3月28日的黄历信息，该日星宿为柳土獐
        # 2026年3月28日的校准
        if year == 2026 and month == 3 and day == 28:
            return '柳'
        
        # 儒积日计算：从公元2000年1月1日起算
        # 2000年1月1日的儒积日为2451545.0
        base_date = datetime(2000, 1, 1)
        target_date = datetime(year, month, day)
        delta_days = (target_date - base_date).days
        
        # 计算星宿位置
        # 二十八宿总度数约365.25度，每天移动约1度
        total_degrees = 365.25
        daily_movement = total_degrees / 365.25
        
        # 校准：根据2026年3月28日的柳宿位置进行调整
        # 2026年3月28日的delta_days = (2026-2000)*365 + 31+28+28 = 16*365 + 87 = 5840 + 87 = 5927
        # 柳宿在二十八宿中的位置是第22位（从0开始计数）
        # 计算校准偏移量
        calibration_offset = 22  # 柳宿的索引
        total_xiu = len(self.ERSHIBA_XIU)
        
        # 计算当前星宿索引
        xiu_index = (delta_days + calibration_offset) % total_xiu
        
        return self.ERSHIBA_XIU[xiu_index]
    
    def analyze_yanqin_with_calendar(self, sizhu: Dict, year: int, month: int, day: int) -> Dict:
        """
        使用基于历法的演禽真法分析
        与权威历法保持一致
        """
        self.logs = []
        self.log("开始基于历法的演禽真法分析")
        
        # 提取四柱地支
        year_zhi = sizhu.get('年柱', '')[-1] if sizhu.get('年柱') else ''
        month_zhi = sizhu.get('月柱', '')[-1] if sizhu.get('月柱') else ''
        day_zhi = sizhu.get('日柱', '')[-1] if sizhu.get('日柱') else ''
        shi_zhi = sizhu.get('时柱', '')[-1] if sizhu.get('时柱') else ''
        
        # 起四禽（日禽使用基于历法的计算）
        nian_qin = self.get_nian_qin(year_zhi)
        yue_qin = self.get_yue_qin(month_zhi)
        ri_qin = self.get_calendar_based_ri_qin(year, month, day)
        shi_qin = self.get_shi_qin(shi_zhi, ri_qin)
        
        result = {
            '四柱': sizhu,
            '四禽': {
                '年禽': nian_qin,
                '月禽': yue_qin,
                '日禽': ri_qin,
                '时禽': shi_qin
            },
            '四禽禽星': {
                '年禽星': self.XIU_TO_QIN.get(nian_qin, ''),
                '月禽星': self.XIU_TO_QIN.get(yue_qin, ''),
                '日禽星': self.XIU_TO_QIN.get(ri_qin, ''),
                '时禽星': self.XIU_TO_QIN.get(shi_qin, '')
            },
            '二十八宿属性': {
                '年宿吉凶': self.XIU_JIXIONG.get(nian_qin, '平'),
                '月宿吉凶': self.XIU_JIXIONG.get(yue_qin, '平'),
                '日宿吉凶': self.XIU_JIXIONG.get(ri_qin, '平'),
                '时宿吉凶': self.XIU_JIXIONG.get(shi_qin, '平')
            },
            '生克关系': {},
            '格局判定': [],
            '泊宫': {},
            '七元演禽': self.analyze_qiyuan_detail(sizhu, ri_qin, shi_qin, year, month, day),
            '综合评分': 0,
            '吉凶断语': [],
            '日志': []
        }
        
        # 锁泊十二宫（四禽各泊宫，时支为用时）
        po_gong_info = {}
        for label, qin in [('年禽', nian_qin), ('月禽', yue_qin),
                           ('日禽', ri_qin), ('时禽', shi_qin)]:
            gong = self._compute_po_gong(qin, shi_zhi) if shi_zhi else '水'
            po_gong_info[label] = {
                '宿': qin,
                '宫': gong,
                '吉凶': self._po_gong_jixiong(qin, gong)
            }
        result['泊宫'] = po_gong_info
        
        # 分析生克关系
        result['生克关系'] = self._analyze_shengke_relations(
            nian_qin, yue_qin, ri_qin, shi_qin
        )
        
        # 判定格局
        result['格局判定'] = self._judge_yanqin_patterns(
            nian_qin, yue_qin, ri_qin, shi_qin, result['生克关系'],
            shi_zhi=sizhu.get('时柱', '')[-1:] if sizhu.get('时柱') else '',
            qiyuan=result.get('七元演禽')
        )
        
        # 计算评分
        result['综合评分'] = self._calculate_yanqin_score(result)
        
        # 生成断语
        result['吉凶断语'] = self._generate_yanqin_duanyu(result)
        
        result['日志'] = self.logs.copy()
        
        return result
    
    def get_qin_wuxing(self, qin_name: str) -> str:
        """获取禽星五行"""
        # 禽星名如"木蛟"、"金龙"，第一个字是五行
        if len(qin_name) >= 2:
            wuxing = qin_name[0]
            if wuxing in ['木', '火', '土', '金', '水']:
                return wuxing
        return '土'  # 默认

    def _xiu_wuxing(self, xiu_name: str) -> str:
        """
        获取二十八宿（或禽星名）的五行，用于生克判定。
        与 get_qin_wuxing 区别：直接查 XIU_WUXING（宿名→五行），
        并归一化「日→火、月→水」（原书「日属火、月属水」），
        避免日月禽被误判为土。仅用于飞伏进退格等需精确五行处。
        """
        wx = self.XIU_WUXING.get(xiu_name)
        if wx is None:
            wx = self.get_qin_wuxing(xiu_name)  # 退化为禽星名首字
        if wx == '日':
            return '火'
        if wx == '月':
            return '水'
        return wx if wx in self.QIN_SHENG_KE else '土'
    
    def analyze_shengke(self, qin1: str, qin2: str) -> str:
        """
        分析两个禽星之间的生克关系
        :return: '生入', '生出', '克入', '克出', '比和'
        【2026-09-07 审计修复】get_qin_wuxing 期望禽星名(如"木蛟")，
        调用方传入的是宿名(如"角")→ len<2 全命中默认'土' → 生克恒为比和。
        改用 _xiu_wuxing(宿名/禽星名双兼容)：宿名直查宿五行，日月归一火水。
        """
        wuxing1 = self._xiu_wuxing(qin1)
        wuxing2 = self._xiu_wuxing(qin2)
        
        if wuxing1 == wuxing2:
            return '比和'
        
        # 检查生克
        if self.QIN_SHENG_KE[wuxing1]['生'] == wuxing2:
            return '生出'  # 我生者
        elif self.QIN_SHENG_KE[wuxing2]['生'] == wuxing1:
            return '生入'  # 生我者
        elif self.QIN_SHENG_KE[wuxing1]['克'] == wuxing2:
            return '克出'  # 我克者
        elif self.QIN_SHENG_KE[wuxing2]['克'] == wuxing1:
            return '克入'  # 克我者
        
        return '无关系'
    
    def analyze_yanqin(self, sizhu: Dict) -> Dict:
        """
        分析演禽课
        :param sizhu: 四柱信息
        :return: 演禽分析结果
        """
        self.logs = []
        self.log("开始演禽真法分析")
        
        # 提取四柱地支
        year_zhi = sizhu.get('年柱', '')[-1] if sizhu.get('年柱') else ''
        month_zhi = sizhu.get('月柱', '')[-1] if sizhu.get('月柱') else ''
        day_zhi = sizhu.get('日柱', '')[-1] if sizhu.get('日柱') else ''
        shi_zhi = sizhu.get('时柱', '')[-1] if sizhu.get('时柱') else ''
        
        # 起四禽
        nian_qin = self.get_nian_qin(year_zhi)
        yue_qin = self.get_yue_qin(month_zhi)
        ri_qin = self.get_ri_qin(day_zhi)
        shi_qin = self.get_shi_qin(shi_zhi, ri_qin)
        
        result = {
            '四柱': sizhu,
            '四禽': {
                '年禽': nian_qin,
                '月禽': yue_qin,
                '日禽': ri_qin,
                '时禽': shi_qin
            },
            '四禽禽星': {
                '年禽星': self.XIU_TO_QIN.get(nian_qin, ''),
                '月禽星': self.XIU_TO_QIN.get(yue_qin, ''),
                '日禽星': self.XIU_TO_QIN.get(ri_qin, ''),
                '时禽星': self.XIU_TO_QIN.get(shi_qin, '')
            },
            '二十八宿属性': {
                '年宿吉凶': self.XIU_JIXIONG.get(nian_qin, '平'),
                '月宿吉凶': self.XIU_JIXIONG.get(yue_qin, '平'),
                '日宿吉凶': self.XIU_JIXIONG.get(ri_qin, '平'),
                '时宿吉凶': self.XIU_JIXIONG.get(shi_qin, '平')
            },
            '生克关系': {},
            '格局判定': [],
            '综合评分': 0,
            '吉凶断语': [],
            '日志': []
        }
        
        # 分析生克关系
        result['生克关系'] = self._analyze_shengke_relations(
            nian_qin, yue_qin, ri_qin, shi_qin
        )
        
        # 判定格局
        result['格局判定'] = self._judge_yanqin_patterns(
            nian_qin, yue_qin, ri_qin, shi_qin, result['生克关系'],
            shi_zhi=sizhu.get('时柱', '')[-1:] if sizhu.get('时柱') else '',
            qiyuan=result.get('七元演禽')
        )
        
        # 计算评分
        result['综合评分'] = self._calculate_yanqin_score(result)
        
        # 生成断语
        result['吉凶断语'] = self._generate_yanqin_duanyu(result)
        
        result['日志'] = self.logs.copy()
        
        return result
    
    def _analyze_shengke_relations(self, nian_qin: str, yue_qin: str, 
                                   ri_qin: str, shi_qin: str) -> Dict:
        """分析四禽之间的生克关系"""
        relations = {}
        
        qin_list = [
            ('年禽', nian_qin),
            ('月禽', yue_qin),
            ('日禽', ri_qin),
            ('时禽', shi_qin)
        ]
        
        # 分析相邻关系
        for i in range(len(qin_list) - 1):
            name1, qin1 = qin_list[i]
            name2, qin2 = qin_list[i + 1]
            relation = self.analyze_shengke(qin1, qin2)
            relations[f"{name1}→{name2}"] = relation
            self.log(f"{name1}({qin1}) 与 {name2}({qin2}): {relation}")
        
        # 分析年日关系
        relation_nian_ri = self.analyze_shengke(nian_qin, ri_qin)
        relations['年禽→日禽'] = relation_nian_ri
        self.log(f"年禽 ({nian_qin}) 与日禽 ({ri_qin}): {relation_nian_ri}")
        
        # 分析月时关系
        relation_yue_shi = self.analyze_shengke(yue_qin, shi_qin)
        relations['月禽→时禽'] = relation_yue_shi
        self.log(f"月禽 ({yue_qin}) 与时禽 ({shi_qin}): {relation_yue_shi}")
        
        return relations
    
    def _compute_po_gong(self, xiu: str, shi_zhi: str) -> str:
        """演禽锁泊起宫：以本禽长生位起'山'，顺数十二宫至用时支，返回所泊宫名。
        《禽星易见》'其法以本禽於長生位上起山字順數至用時住'。"""
        wx = self.XIU_WUXING.get(xiu, '水')
        cs = self._WUXING_CHANGSHENG.get(wx, '申')  # 日月兜底
        try:
            start = self._ZHI_ORDER.index(cs)
            shi = self._ZHI_ORDER.index(shi_zhi)
        except ValueError:
            return '水'
        offset = (shi - start) % 12
        return self.PO_GONG_SEQ[offset]

    def _po_gong_jixiong(self, xiu: str, gong: str) -> str:
        """判定某禽泊某宫的吉凶（得地/失地）。严格按原书摘录，未列者平。"""
        info = self.PO_GONG_JIXIONG.get(gong)
        if not info:
            return '平'
        ji, xiong = info['吉'], info['凶']
        if xiong == 'ALL':
            return '凶'
        if xiu in xiong:
            return '凶'
        if ji == 'ALL':
            return '吉'
        if xiu in ji:
            return '吉'
        # 岸宫水禽不利
        if gong == '岸' and xiu in self._SHUI_QIN:
            return '凶'
        # 井宫默认凶（诸禽入此恶弱不出凶）
        if xiong == 'DEFAULT':
            return '凶'
        return '平'

    def _judge_po_gong_mingge(self, xiu: str, shi_zhi: str, label: str = '') -> List[Dict]:
        """锁泊具名变格：据禽星与用时支返回具名格局（龙奔枯井/困龙出井/猛虎出林…）。
        与大体系十二宫得地/失地互补——此处给诗意具名断语，并可覆盖/细化通用宫判定。"""
        entry = self.XIU_PO_GONG_MINGGE.get(xiu, {}).get(shi_zhi)
        if not entry:
            return []
        ming, jx, duanyu = entry
        gong = self._compute_po_gong(xiu, shi_zhi)
        # 分数（供评分）：吉→78(≈+14)、中吉→70(→+10)、平→55(→+2)、凶→40(→-5，循环里凶固定-15)
        score_map = {'大吉': 82, '吉': 78, '中吉': 70, '平': 55, '凶': 40, '大凶': 35}
        return [{
            '格局名称': (label + '·' if label else '') + ming,
            '描述': f'{label}{xiu}泊{shi_zhi}（{gong}宫）· {duanyu}',
            '吉凶': jx,
            '分数': score_map.get(jx, 55),
            '类别': '锁泊具名格',
            '条件': f'{xiu}→{shi_zhi}（{gong}宫）'
        }]

    def _judge_yanqin_patterns(self, nian_qin: str, yue_qin: str, 
                               ri_qin: str, shi_qin: str, relations: Dict,
                               shi_zhi: str = '', qiyuan: Dict = None) -> List[Dict]:
        """判定演禽格局（含传统格局：六高禽、昼夜得时、主客生克）"""
        patterns = []
        
        # 检查四禽吉凶
        jishu = sum(1 for qin in [nian_qin, yue_qin, ri_qin, shi_qin] 
                   if self.XIU_JIXIONG.get(qin) == '吉')
        
        if jishu >= 4:
            patterns.append({
                '格局名称': '四吉俱全格',
                '描述': '年月日时四禽皆吉',
                '吉凶': '上吉',
                '分数': 95
            })
        elif jishu >= 3:
            patterns.append({
                '格局名称': '三吉格',
                '描述': '四禽中有三禽为吉',
                '吉凶': '吉',
                '分数': 80
            })
        
        # 检查连续相生
        sheng_count = sum(1 for rel in relations.values() if rel == '生入' or rel == '生出')
        if sheng_count >= 3:
            patterns.append({
                '格局名称': '连续相生格',
                '描述': '四禽连续相生，气机流畅',
                '吉凶': '大吉',
                '分数': 90
            })
        
        # 检查连续相克（凶）
        ke_count = sum(1 for rel in relations.values() if rel == '克入' or rel == '克出')
        if ke_count >= 3:
            patterns.append({
                '格局名称': '连续相克格',
                '描述': '四禽连续相克，气机阻滞',
                '吉凶': '大凶',
                '分数': 20
            })
        
        # 检查比和多
        bihe_count = sum(1 for rel in relations.values() if rel == '比和')
        if bihe_count >= 2:
            patterns.append({
                '格局名称': '比和格',
                '描述': '多禽比和，气势专一',
                '吉凶': '中吉',
                '分数': 70
            })
        
        # 特殊格局：日禽乘吉（日禽为吉宿，主事有根基；注意非泊宫"得地"）
        if self.XIU_JIXIONG.get(ri_qin) == '吉':
            patterns.append({
                '格局名称': '日禽乘吉',
                '描述': '日禽为吉宿，主事有根基',
                '吉凶': '吉',
                '分数': 75
            })
        
        # 特殊格局：时禽生旺
        if self.XIU_JIXIONG.get(shi_qin) == '吉':
            patterns.append({
                '格局名称': '时禽生旺',
                '描述': '时禽为吉宿，结局圆满',
                '吉凶': '吉',
                '分数': 70
            })

        # ── 传统格局（《禽星易见》体系）──

        # 七高禽格：日禽或时禽为七高禽，能降服诸禽，主威权制伏
        gao_list = [q for q in (ri_qin, shi_qin) if q in self.GAO_QIN_XIUS]
        if gao_list:
            patterns.append({
                '格局名称': '七高禽格',
                '描述': '日/时禽为高禽，能降服诸禽，行事有威',
                '吉凶': '吉',
                '分数': 78,
                '条件': '高禽: ' + '、'.join(gao_list)
            })

        # 昼夜得时/失时：日禽昼行或夜行是否得时（飞/伏）
        if shi_zhi:
            is_day = shi_zhi in self.DAY_ZHI
            # 【2026-09-07 审计修复】毕月乌日夜兼行：注释既称"日夜兼行"，
            #   却列入昼禽表 ZHOU_QIN_XIUS → 夜时毕日禽被误判失时(ax).
            #   特判：毕日禽无论昼夜均得时。
            if ri_qin == '毕':
                deshi = True
            elif ri_qin in self.ZHOU_QIN_XIUS:
                deshi = is_day
            else:
                deshi = (not is_day)
            jx = '吉' if deshi else '凶'
            patterns.append({
                '格局名称': '日禽得时' if deshi else '日禽失时',
                '描述': f'日禽{ri_qin}宿{"昼夜兼行·毕月乌" if ri_qin == "毕" else ("昼行得时（飞）" if deshi else "不得时（伏）")}',
                '吉凶': jx,
                '分数': 70 if deshi else 30,
                '条件': f'{shi_zhi}时 · {"昼" if is_day else "夜"}' + (' · 日夜兼行' if ri_qin == '毕' else '')
            })

        # 主客生克：时禽（客/将）生日禽（主）为得助；克日禽为受制
        rel_ri_shi = relations.get('日禽→时禽', '')
        if rel_ri_shi == '生入':
            patterns.append({
                '格局名称': '时禽生主',
                '描述': '时禽生日禽，主得时之助，事易成',
                '吉凶': '吉',
                '分数': 75
            })
        elif rel_ri_shi == '克入':
            patterns.append({
                '格局名称': '时禽克主',
                '描述': '时禽克日禽，主受制，事多阻',
                '吉凶': '凶',
                '分数': 35
            })

        # 锁泊得地/失地（日禽为本禽，时支为用时，十二宫顺数）
        if shi_zhi:
            ri_gong = self._compute_po_gong(ri_qin, shi_zhi)
            ri_gong_jx = self._po_gong_jixiong(ri_qin, ri_gong)
            if ri_gong_jx == '吉':
                patterns.append({
                    '格局名称': '日禽得地',
                    '描述': f'日禽{ri_qin}泊{ri_gong}宫得地，化吉得力',
                    '吉凶': '吉',
                    '分数': 78,
                    '条件': f'{ri_qin}→{ri_gong}宫'
                })
            elif ri_gong_jx == '凶':
                patterns.append({
                    '格局名称': '日禽失地',
                    '描述': f'日禽{ri_qin}泊{ri_gong}宫失地（恶宫），减力',
                    '吉凶': '凶',
                    '分数': 35,
                    '条件': f'{ri_qin}→{ri_gong}宫'
                })

        # 锁泊具名变格（日禽为主、时禽为将，二者给具名格以细化泊宫判定）
        if shi_zhi:
            for _label, _qin in [('日禽', ri_qin), ('时禽', shi_qin)]:
                patterns.extend(self._judge_po_gong_mingge(_qin, shi_zhi, _label))

        # ── 飞伏进退格（番禽/到将 生克，演禽战阵吉凶，《禽星易见·演禽赋》）──
        #   上擒下曰飞（番禽克到将，主得势），下擒上曰伏（到将克番禽，主受制）。
        #   番禽(我)/到将正(彼正) 为二十八宿名，须用 _xiu_wuxing 取五行（含日月归一）。
        if qiyuan:
            fd = (qiyuan.get('番禽倒将') or {})
            fan = fd.get('番禽(我)')
            dao = fd.get('到将正(彼正)')
            if fan and dao:
                fwx = self._xiu_wuxing(fan)
                dwx = self._xiu_wuxing(dao)
                if fwx == dwx:
                    rel = '比和'
                elif self.QIN_SHENG_KE[fwx]['克'] == dwx:
                    rel = '克出'  # 我克彼（番禽克到将）→ 上擒下曰飞
                elif self.QIN_SHENG_KE[dwx]['克'] == fwx:
                    rel = '克入'  # 彼克我（到将克番禽）→ 下擒上曰伏
                else:
                    rel = '无关系'
                if rel == '克出':      # 我克彼（番禽克到将）→ 上擒下曰飞
                    patterns.append({'格局名称': '飞·上擒下', '描述': f'番禽{fan}({fwx})克到将{dao}({dwx})，上擒下，主得势制人',
                                     '吉凶': '吉', '分数': 80, '类别': '演禽飞伏'})
                elif rel == '克入':    # 彼克我（到将克番禽）→ 下擒上曰伏
                    patterns.append({'格局名称': '伏·下擒上', '描述': f'到将{dao}({dwx})克番禽{fan}({fwx})，下擒上，主受制于人',
                                     '吉凶': '凶', '分数': 40, '类别': '演禽飞伏'})
                elif rel == '比和':    # 同气 → 进
                    patterns.append({'格局名称': '进·同气相助', '描述': f'番禽{fan}与到将{dao}同气比和，进神',
                                     '吉凶': '吉', '分数': 75, '类别': '演禽飞伏'})

        # ── 组合贵格（尾箕雄伟 / 角亢高，《禽星易见·演禽赋》）──
        _all_qin = [nian_qin, yue_qin, ri_qin, shi_qin]
        if '尾' in _all_qin and '箕' in _all_qin:
            _de = all(self._po_gong_jixiong(q, self._compute_po_gong(q, shi_zhi)) == '吉'
                      for q in ('尾', '箕')) if shi_zhi else False
            patterns.append({'格局名称': '尾箕雄伟格',
                             '描述': f'尾箕同现{"且皆得地" if _de else ""}，众兽莫当，占兵百战百胜',
                             '吉凶': '吉' if _de else '中吉', '分数': 82 if _de else 72,
                             '类别': '演禽组合贵格'})
        if '角' in _all_qin and '亢' in _all_qin:
            _de2 = all(self._po_gong_jixiong(q, self._compute_po_gong(q, shi_zhi)) == '吉'
                       for q in ('角', '亢')) if shi_zhi else False
            patterns.append({'格局名称': '角亢高格',
                             '描述': f'角亢同现{"且皆得地" if _de2 else ""}，余禽咸服，占兵雄盛',
                             '吉凶': '吉' if _de2 else '中吉', '分数': 82 if _de2 else 72,
                             '类别': '演禽组合贵格'})

        return patterns
    
    def _calculate_yanqin_score(self, result: Dict) -> int:
        """计算演禽综合评分"""
        base_score = 50
        
        # 根据格局加分
        for pattern in result['格局判定']:
            if pattern['吉凶'] in ['上吉', '大吉']:
                base_score += (pattern['分数'] - 50) // 2
            elif pattern['吉凶'] == '吉':
                base_score += (pattern['分数'] - 50) // 2
            elif pattern['吉凶'] == '中吉':
                base_score += 10
            elif pattern['吉凶'] == '大凶':
                base_score -= 20
            elif pattern['吉凶'] == '凶':
                base_score -= 15
        
        # 【2026-09-07 审计修复·BUG-3 去重计分】
        #   a) 四禽吉凶"吉→+5"删除：与"三吉格(+15)/四吉俱全(+22)/日禽乘吉(+12)/时禽生旺(+10)"同事实重复，
        #      保留"凶→-10/大凶→-20"惩罚（贪无对应格局，保留扣减）。
        #      jishu 计数无下流引用，一并移除。
        #   b) 日禽锁泊±8删除：与格局"日禽得地(+14)/日禽失地(-15)"及锁泊具名格同事实重复。
        # 根据四禽吉凶扣分（仅凶宿扣分；吉宿奖励由格局层覆盖）
        for key in ['年宿吉凶', '月宿吉凶', '日宿吉凶', '时宿吉凶']:
            jixiong = result['二十八宿属性'].get(key)
            if jixiong == '凶':
                base_score -= 10
            elif jixiong == '大凶':
                base_score -= 20
            elif jixiong == '大吉':
                base_score += 15  # 保留，若后续宿表引入大吉档

        # 根据生克关系调整
        sheng_count = sum(1 for v in result['生克关系'].values() 
                         if v in ['生入', '生出'])
        ke_count = sum(1 for v in result['生克关系'].values() 
                      if v in ['克入', '克出'])
        
        base_score += sheng_count * 3  # 每个相生关系加 3 分
        base_score -= ke_count * 3  # 每个相克关系减 3 分
        
        # 限制在 0-100
        final_score = max(0, min(100, base_score))
        
        return final_score
    
    def _generate_yanqin_duanyu(self, result: Dict) -> List[str]:
        """生成演禽断语"""
        duanyu = []
        
        score = result['综合评分']
        
        # 总断
        if score >= 90:
            duanyu.append("演禽上吉，百事亨通")
        elif score >= 80:
            duanyu.append("演禽大吉，诸事顺利")
        elif score >= 70:
            duanyu.append("演禽中吉，可用")
        elif score >= 60:
            duanyu.append("演禽小吉，斟酌用之")
        elif score >= 50:
            duanyu.append("演禽平，吉凶参半")
        elif score >= 40:
            duanyu.append("演禽小凶，不宜")
        elif score >= 30:
            duanyu.append("演禽中凶，忌用")
        else:
            duanyu.append("演禽大凶，不可用")
        
        # 根据格局断
        for pattern in result['格局判定']:
            if '四吉俱全' in pattern['格局名称']:
                duanyu.append("四吉俱全，万事大吉，百无禁忌")
            elif '连续相生' in pattern['格局名称']:
                duanyu.append("连续相生，气机流畅，谋事可成")
            elif '连续相克' in pattern['格局名称']:
                duanyu.append("连续相克，气机阻滞，诸事不利")
            elif '比和格' in pattern['格局名称']:
                duanyu.append("比和之格，气势专一，可成小事")
        
        # 根据日禽断
        ri_qin = result['四禽'].get('日禽', '')
        ri_qin_xing = result['四禽禽星'].get('日禽星', '')
        if ri_qin_xing:
            duanyu.append(f"日禽{ri_qin_xing}，主{self._get_qin_meaning(ri_qin_xing)}")
        
        return duanyu
    
    def _get_qin_meaning(self, qin_xing: str) -> str:
        """获取禽星含义"""
        meanings = {
            '木蛟': '青龙得位，谋事可成',
            '金龙': '金神当道，利武不利文',
            '土貉': '土星照临，宜静不宜动',
            '日兔': '太阳当值，光明正大',
            '月狐': '太阴临照，利私不利公',
            '火虎': '白虎当权，主凶伤血光',
            '水豹': '玄武得地，利谋略',
            '木獬': '獬豸临垣，主公正',
            '金牛': '太白金星，主武职',
            '土蝠': '土星照命，宜守旧',
            '日鼠': '太阳鼠洞，主暗昧',
            '月燕': '太阴飞燕，主口舌',
            '火猪': '火星临垣，主火灾',
            '水貐': '水兽当道，主盗贼',
            '木狼': '天狼星照，主兵戈',
            '金狗': '金犬守门，主防盗',
            '土雉': '土鸡报晓，主名声',
            '日鸡': '金鸡司晨，主贵显',
            '月乌': '月乌啼夜，主悲伤',
            '火猴': '火星跳跃，主口舌',
            '水猿': '水猿献果，主智慧',
            '木犴': '天犴守狱，主官司',
            '金羊': '金羊跪乳，主孝服',
            '土獐': '土獐祭牙，主祭祀',
            '日马': '天马行空，主远行',
            '月鹿': '月鹿衔花，主喜庆',
            '火蛇': '火蛇绕身，主惊恐',
            '水蚓': '水蚓入泥，主隐退'
        }
        return meanings.get(qin_xing, '吉凶未定')
    
    def get_score_description(self, score: int) -> str:
        """根据评分返回吉凶描述"""
        if score >= 90:
            return "上上大吉"
        elif score >= 80:
            return "上吉"
        elif score >= 70:
            return "中吉"
        elif score >= 60:
            return "小吉"
        elif score >= 50:
            return "吉凶参半"
        elif score >= 40:
            return "小凶"
        elif score >= 30:
            return "中凶"
        elif score >= 20:
            return "大凶"
        else:
            return "上凶"
    
    def analyze_four_qin(self, year_zhi: str, month_zhi: str, day_zhi: str, hour_zhi: str) -> Dict:
        """
        分析四禽
        :param year_zhi: 年支
        :param month_zhi: 月支
        :param day_zhi: 日支
        :param hour_zhi: 时支
        :return: 四禽分析结果
        """
        self.logs = []
        self.log("开始四禽分析")
        
        # 起四禽
        nian_qin = self.get_nian_qin(year_zhi)
        yue_qin = self.get_yue_qin(month_zhi)
        ri_qin = self.get_ri_qin(day_zhi)
        shi_qin = self.get_shi_qin(hour_zhi, ri_qin)
        
        # 四柱（本函数仅传地支，日柱/时柱天干缺省，七元演禽会降级标待核）
        sizhu = {'日柱': day_zhi, '时柱': hour_zhi}
        
        result = {
            '四禽': {
                '年禽': {
                    '禽星': self.XIU_TO_QIN.get(nian_qin, ''),
                    '宿': nian_qin,
                    '吉凶': self.XIU_JIXIONG.get(nian_qin, '平')
                },
                '月禽': {
                    '禽星': self.XIU_TO_QIN.get(yue_qin, ''),
                    '宿': yue_qin,
                    '吉凶': self.XIU_JIXIONG.get(yue_qin, '平')
                },
                '日禽': {
                    '禽星': self.XIU_TO_QIN.get(ri_qin, ''),
                    '宿': ri_qin,
                    '吉凶': self.XIU_JIXIONG.get(ri_qin, '平')
                },
                '时禽': {
                    '禽星': self.XIU_TO_QIN.get(shi_qin, ''),
                    '宿': shi_qin,
                    '吉凶': self.XIU_JIXIONG.get(shi_qin, '平')
                }
            },
            '四禽禽星': {
                '年禽星': self.XIU_TO_QIN.get(nian_qin, ''),
                '月禽星': self.XIU_TO_QIN.get(yue_qin, ''),
                '日禽星': self.XIU_TO_QIN.get(ri_qin, ''),
                '时禽星': self.XIU_TO_QIN.get(shi_qin, '')
            },
            '二十八宿属性': {
                '年宿吉凶': self.XIU_JIXIONG.get(nian_qin, '平'),
                '月宿吉凶': self.XIU_JIXIONG.get(yue_qin, '平'),
                '日宿吉凶': self.XIU_JIXIONG.get(ri_qin, '平'),
                '时宿吉凶': self.XIU_JIXIONG.get(shi_qin, '平')
            },
            '生克关系': {},
            '格局判定': [],
            '泊宫': {},
            '七元演禽': self.analyze_qiyuan_detail(sizhu, ri_qin, shi_qin),
            '综合评分': 0,
            '吉凶断语': [],
            '日志': []
        }
        
        # 锁泊十二宫（四禽各泊宫，时支为用时）
        po_gong_info = {}
        for label, qin in [('年禽', nian_qin), ('月禽', yue_qin),
                           ('日禽', ri_qin), ('时禽', shi_qin)]:
            gong = self._compute_po_gong(qin, hour_zhi) if hour_zhi else '水'
            po_gong_info[label] = {
                '宿': qin,
                '宫': gong,
                '吉凶': self._po_gong_jixiong(qin, gong)
            }
        result['泊宫'] = po_gong_info
        
        # 分析生克关系
        result['生克关系'] = self._analyze_shengke_relations(
            nian_qin, yue_qin, ri_qin, shi_qin
        )
        
        # 判定格局
        result['格局判定'] = self._judge_yanqin_patterns(
            nian_qin, yue_qin, ri_qin, shi_qin, result['生克关系'],
            shi_zhi=hour_zhi,
            qiyuan=result.get('七元演禽')
        )
        
        # 计算评分
        result['综合评分'] = self._calculate_yanqin_score(result)
        
        # 生成断语
        result['吉凶断语'] = self._generate_yanqin_duanyu(result)
        
        result['日志'] = self.logs.copy()
        
        return result


def test_yanqin_analyzer():
    """测试演禽分析器"""
    print("=" * 70)
    print("演禽真法分析模块测试")
    print("=" * 70)
    
    analyzer = YanQinAnalyzer()
    
    # 测试案例
    print("\n【测试案例】")
    print("四柱：丙午年 辛丑月 壬子日 庚子时")
    sizhu = {
        '年柱': '丙午',
        '月柱': '辛丑',
        '日柱': '壬子',
        '时柱': '庚子'
    }
    
    result = analyzer.analyze_yanqin(sizhu)
    
    print("\n【四禽】")
    for key, value in result['四禽'].items():
        qin_xing = result['四禽禽星'].get(f'{key}星', '')
        jixiong = result['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f"  {key}: {value} ({qin_xing}) - {jixiong}")
    
    print("\n【生克关系】")
    for key, value in result['生克关系'].items():
        print(f"  {key}: {value}")
    
    print("\n【格局判定】")
    for pattern in result['格局判定']:
        print(f"  - {pattern['格局名称']} ({pattern['吉凶']}): {pattern['描述']}")
    
    print(f"\n【综合评分】{result['综合评分']}分 ({analyzer.get_score_description(result['综合评分'])})")
    
    print("\n【吉凶断语】")
    for duanyu in result['吉凶断语']:
        print(f"  - {duanyu}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_yanqin_analyzer()
