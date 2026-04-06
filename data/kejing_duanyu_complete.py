#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六壬 64 课经完整断语库
基于《六壬大全》（钦定四库全书本）
"""

KEJING_DUANYU_COMPLETE = {
    # ========== 贼克法 ==========
    '元首课': {
        'score': 85,
        'level': '上吉',
        'duanyu': [
            '元首入课，万事亨通',
            '一上克下，顺其正理',
            '君占则有伊尹之臣',
            '臣占必遇唐虞之君',
            '九宗之元，六十四课之首',
        ],
        'summary': '元首为上吉课，主顺正亨通',
        'special_cases': []
    },
    
    '重审课': {
        'score': 65,
        'level': '小吉',
        'duanyu': [
            '重审入课，先难后易',
            '一下贼上，以下犯上',
            '事起女子，或家祸内生',
            '主在下，宜谨慎',
        ],
        'summary': '重审为小吉课，主先难后易',
        'special_cases': []
    },
    
    '知一课': {
        'score': 70,
        'level': '中吉',
        'duanyu': [
            '知一入课，择善而从',
            '二课相克，取比和者',
            '事贵明确，不致迷惑',
        ],
        'summary': '知一为中吉课，主择善而从',
        'special_cases': []
    },
    
    '比用课': {
        'score': 70,
        'level': '中吉',
        'duanyu': [
            '比用入课，有人相助',
            '阳日用阳，阴日用阴',
            '取比和之神为用',
        ],
        'summary': '比用为中吉课，主和合有助',
        'special_cases': []
    },
    
    '涉害课': {
        'score': 60,
        'level': '吉凶参半',
        'duanyu': [
            '涉害入课，先忧后喜',
            '涉害深浅，经历艰难',
            '路逢多克为用取',
        ],
        'summary': '涉害为吉凶参半课，主经历艰难',
        'special_cases': []
    },
    
    # ========== 涉害法 ==========
    '见机课': {
        'score': 70,
        'level': '中吉',
        'duanyu': [
            '见机入课，当机立断',
            '孟深仲浅季当休',
            '涉害相等取孟上',
            '不宜迟疑',
        ],
        'summary': '见机为中吉课，主见机而作',
        'special_cases': []
    },
    
    '察微课': {
        'score': 65,
        'level': '小吉',
        'duanyu': [
            '察微入课，谨慎行事',
            '无孟取仲',
            '察微知著',
        ],
        'summary': '察微为小吉课，主谨慎',
        'special_cases': []
    },
    
    '缀瑕课': {
        'score': 60,
        'level': '吉凶参半',
        'duanyu': [
            '缀瑕入课，需修补完善',
            '涉害复等，刚日取干上',
            '事有瑕疵',
        ],
        'summary': '缀瑕为吉凶参半课，主有瑕疵',
        'special_cases': []
    },
    
    '复等课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '复等入课，等而后成',
            '涉害俱等，柔日取支上',
            '事有反复',
        ],
        'summary': '复等为吉凶参半课，主反复',
        'special_cases': []
    },
    
    '刑伤课': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '刑伤入课，有损害',
            '涉害逢刑',
            '主刑伤',
        ],
        'summary': '刑伤为小凶课，主损害',
        'special_cases': []
    },
    
    # ========== 遥克法 ==========
    '遥克课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '遥克入课，谋望难成',
            '四课无克号为遥',
            '事主疏远，宜静不宜动',
        ],
        'summary': '遥克为吉凶参半课，主疏远',
        'special_cases': []
    },
    
    '蒿矢课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '蒿矢入课，先凶后吉',
            '神遥克日曰蒿矢',
            '如箭在弦，事有惊扰',
        ],
        'summary': '蒿矢为吉凶参半课，主惊扰',
        'special_cases': []
    },
    
    '弹射课': {
        'score': 60,
        'level': '小吉',
        'duanyu': [
            '弹射入课，主动出击',
            '日遥克神曰弹射',
            '可成，但力量不足',
        ],
        'summary': '弹射为小吉课，主主动',
        'special_cases': []
    },
    
    '矢射课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '矢射入课，事有所中',
            '遥克有克',
            '如矢射物',
        ],
        'summary': '矢射为吉凶参半课，主所中',
        'special_cases': []
    },
    
    '神遥课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '神遥入课，难以成就',
            '神将遥克',
            '事主遥远',
        ],
        'summary': '神遥为吉凶参半课，主遥远',
        'special_cases': []
    },
    
    # ========== 昴星法 ==========
    '昴星课': {
        'score': 45,
        'level': '吉凶参半',
        'duanyu': [
            '昴星入课，宜守不宜进',
            '无遥无克昴星穷',
            '事主困顿',
        ],
        'summary': '昴星为吉凶参半课，主困顿',
        'special_cases': []
    },
    
    '虎视课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '虎视入课，有威严但凶险',
            '刚日先辰而后日',
            '如虎视眈眈',
        ],
        'summary': '虎视为吉凶参半课，主威严',
        'special_cases': []
    },
    
    '冬蛇掩目课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '冬蛇掩目，不宜动作',
            '柔日先日而后辰',
            '如蛇冬眠，事主潜伏',
        ],
        'summary': '冬蛇掩目为吉凶参半课，主潜伏',
        'special_cases': []
    },
    
    '掩目课': {
        'score': 45,
        'level': '吉凶参半',
        'duanyu': [
            '掩目入课，事不明朗',
            '昴星无克',
            '如被掩目',
        ],
        'summary': '掩目为吉凶参半课，主不明',
        'special_cases': []
    },
    
    '伏殃课': {
        'score': 30,
        'level': '中凶',
        'duanyu': [
            '伏殃入课，凶险异常',
            '昴星逢凶',
            '祸殃潜伏',
        ],
        'summary': '伏殃为中凶课，主凶险',
        'special_cases': []
    },
    
    # ========== 别责法 ==========
    '别责课': {
        'score': 60,
        'level': '小吉',
        'duanyu': [
            '别责入课，别求他法',
            '四课不全三课备',
            '另辟蹊径',
        ],
        'summary': '别责为小吉课，主另辟蹊径',
        'special_cases': []
    },
    
    '八专课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '八专入课，专一但力弱',
            '两课无克号八专',
            '事主专一',
        ],
        'summary': '八专为吉凶参半课，主专一',
        'special_cases': []
    },
    
    '帷薄课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '帷薄入课，事不明朗',
            '八专无克',
            '如处帷薄之中',
        ],
        'summary': '帷薄为吉凶参半课，主不明',
        'special_cases': []
    },
    
    '不备课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '不备入课，有缺陷',
            '四课不全',
            '事不周全',
        ],
        'summary': '不备为吉凶参半课，主缺陷',
        'special_cases': []
    },
    
    '淫泆课': {
        'score': 35,
        'level': '小凶',
        'duanyu': [
            '淫泆入课，不正',
            '八专淫泆',
            '事主淫泆',
        ],
        'summary': '淫泆为小凶课，主不正',
        'special_cases': []
    },
    
    # ========== 伏吟法 ==========
    '伏吟课': {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': [
            '伏吟入课，宜静不宜动',
            '月将等于占时',
            '天地盘同，神将伏而不动',
        ],
        'summary': '伏吟为吉凶参半课，主静守',
        'special_cases': []
    },
    
    '自任课': {
        'score': 45,
        'level': '吉凶参半',
        'duanyu': [
            '自任入课，劳心费力',
            '伏吟自刑',
            '事主自任',
        ],
        'summary': '自任为吉凶参半课，主劳心',
        'special_cases': []
    },
    
    '自信课': {
        'score': 55,
        'level': '吉凶参半',
        'duanyu': [
            '自信入课，可成',
            '伏吟有克',
            '事主自信',
        ],
        'summary': '自信为吉凶参半课，主可成',
        'special_cases': []
    },
    
    '杜传课': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '杜传入课，传而不通',
            '伏吟杜塞',
            '事主杜塞',
        ],
        'summary': '杜传为小凶课，主不通',
        'special_cases': []
    },
    
    '孤辰课': {
        'score': 35,
        'level': '小凶',
        'duanyu': [
            '孤辰入课，无助',
            '伏吟逢孤辰',
            '事主孤独',
        ],
        'summary': '孤辰为小凶课，主孤独',
        'special_cases': []
    },
    
    '寡宿课': {
        'score': 35,
        'level': '小凶',
        'duanyu': [
            '寡宿入课，孤单',
            '伏吟逢寡宿',
            '事主寡宿',
        ],
        'summary': '寡宿为小凶课，主孤单',
        'special_cases': []
    },
    
    '绝情课': {
        'score': 30,
        'level': '中凶',
        'duanyu': [
            '绝情入课，无恩义',
            '伏吟绝情',
            '事主绝情',
        ],
        'summary': '绝情为中凶课，主无义',
        'special_cases': []
    },
    
    '无依课': {
        'score': 30,
        'level': '中凶',
        'duanyu': [
            '无依入课，孤立无援',
            '伏吟无依',
            '事主无依',
        ],
        'summary': '无依为中凶课，主孤立',
        'special_cases': []
    },
    
    # ========== 反吟法 ==========
    '反吟课': {
        'score': 45,
        'level': '小凶',
        'duanyu': [
            '反吟入课，反复无常',
            '月将冲占时',
            '天地盘冲，进退两难',
        ],
        'summary': '反吟为小凶课，主反复',
        'special_cases': []
    },
    
    '井栏课': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '井栏入课，视野受限',
            '反吟无克别有井栏名',
            '如处井中',
        ],
        'summary': '井栏为小凶课，主受限',
        'special_cases': []
    },
    
    '井栏射格': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '井栏射格，力不能及',
            '井栏射',
            '如射井中',
        ],
        'summary': '井栏射为小凶课，主不及',
        'special_cases': []
    },
    
    '无亲课': {
        'score': 35,
        'level': '小凶',
        'duanyu': [
            '无亲入课，孤立',
            '反吟无亲',
            '事主无亲',
        ],
        'summary': '无亲为小凶课，主孤立',
        'special_cases': []
    },
    
    '冲克课': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '冲克入课，不和',
            '反吟冲克',
            '事主冲克',
        ],
        'summary': '冲克为小凶课，主不和',
        'special_cases': []
    },
    
    # ========== 吉格 ==========
    '三光课': {
        'score': 92,
        'level': '上吉',
        'duanyu': [
            '三光入课，吉庆有余',
            '三传皆吉神旺相',
            '万事亨通，光明磊落',
            '谋事可成',
            '福禄自来',
        ],
        'summary': '三光为上吉课，主亨通吉庆',
        'special_cases': []
    },
    
    '三阳课': {
        'score': 90,
        'level': '上吉',
        'duanyu': [
            '三阳入课，阳气昌盛',
            '三传皆阳',
            '事主光明',
            '得地得时',
        ],
        'summary': '三阳为上吉课，主昌盛光明',
        'special_cases': []
    },
    
    '三奇课': {
        'score': 88,
        'level': '上吉',
        'duanyu': [
            '三奇入课，转危为安',
            '乙丙丁或甲戊庚',
            '奇事出现',
        ],
        'summary': '三奇为上吉课，主转危为安',
        'special_cases': []
    },
    
    '三合课': {
        'score': 85,
        'level': '上吉',
        'duanyu': [
            '三合入课，众人相助',
            '三传三合局',
            '事主和合',
        ],
        'summary': '三合为上吉课，主和合有助',
        'special_cases': []
    },
    
    '六合课': {
        'score': 85,
        'level': '上吉',
        'duanyu': [
            '六合入课，谋事可成',
            '三传六合',
            '事主和合',
        ],
        'summary': '六合为上吉课，主和合成事',
        'special_cases': []
    },
    
    '龙德课': {
        'score': 95,
        'level': '上上大吉',
        'duanyu': [
            '龙德临身，贵人来助',
            '太岁或月将发用',
            '百事亨通',
            '最宜祭祀祈福',
            '灾消祸散',
        ],
        'summary': '龙德为上上大吉课，主贵人亨通',
        'special_cases': []
    },
    
    '天赦课': {
        'score': 93,
        'level': '上上大吉',
        'duanyu': [
            '天赦入课，百无禁忌',
            '春戊寅夏甲午秋戊申冬甲子',
            '万事大吉',
            '逢凶化吉',
        ],
        'summary': '天赦为上上大吉课，主赦罪化吉',
        'special_cases': []
    },
    
    '天德课': {
        'score': 88,
        'level': '上吉',
        'duanyu': [
            '天德入课，百事皆宜',
            '天德贵人发用',
            '贵人扶持',
        ],
        'summary': '天德为上吉课，主贵人吉利',
        'special_cases': []
    },
    
    '月德课': {
        'score': 88,
        'level': '上吉',
        'duanyu': [
            '月德入课，和顺吉祥',
            '月德贵人发用',
            '贵人相助',
        ],
        'summary': '月德为上吉课，主和顺吉祥',
        'special_cases': []
    },
    
    '生气课': {
        'score': 78,
        'level': '中吉',
        'duanyu': [
            '生气入课，生机勃勃',
            '生气发用',
            '万事可成',
        ],
        'summary': '生气为中吉课，主生机活力',
        'special_cases': []
    },
    
    '青龙课': {
        'score': 78,
        'level': '中吉',
        'duanyu': [
            '青龙入课，喜庆临门',
            '青龙发用',
            '财禄自来',
        ],
        'summary': '青龙为中吉课，主喜庆财禄',
        'special_cases': []
    },
    
    # ========== 凶格 ==========
    '鬼墓课': {
        'score': 25,
        'level': '大凶',
        'duanyu': [
            '鬼墓入课，五行克贼，死墓之乡',
            '鬼主伤残，墓主闭塞不通',
            '凡人占鬼入传，及传墓不吉',
            '人丁多耗，家宅不昌',
            '行人可至，病者如狂',
            '谋为迟滞，捕盗深藏',
            '凡事逢墓则止',
        ],
        'summary': '鬼墓为大凶课，主暗昧闭塞灾凶',
        'special_cases': [
            {'name': '墓神覆日', 'meaning': '主人昏晦'},
            {'name': '干墓临支', 'meaning': '主宅倾颓'},
            {'name': '干支乘墓', 'meaning': '人宅俱不利'},
            {'name': '干支坐墓', 'meaning': '自招其祸'},
            {'name': '干支互换坐墓', 'meaning': '彼此招晦'},
            {'name': '墓门开格', 'meaning': '主丧事'},
            {'name': '传墓入墓', 'meaning': '自明投暗'},
            {'name': '墓加长生', 'meaning': '旧事再发'}
        ]
    },
    
    '天网课': {
        'score': 35,
        'level': '中凶',
        'duanyu': [
            '天网课，如罗网罩身',
            '魁罡加日辰',
            '事主困顿',
            '难以脱身',
        ],
        'summary': '天网为中凶课，主困顿难伸',
        'special_cases': []
    },
    
    '地网课': {
        'score': 30,
        'level': '中凶',
        'duanyu': [
            '地网课，如入地网',
            '岁煞加日辰',
            '难以脱身',
        ],
        'summary': '地网为中凶课，主束缚难脱',
        'special_cases': []
    },
    
    '斩关课': {
        'score': 60,
        'level': '吉凶参半',
        'duanyu': [
            '斩关入课，先难后易',
            '魁罡加日辰发用',
            '突破难关',
        ],
        'summary': '斩关为吉凶参半课，主突破',
        'special_cases': []
    },
    
    '闭口课': {
        'score': 40,
        'level': '小凶',
        'duanyu': [
            '闭口入课，言而有阻',
            '旬尾加旬首',
            '事主闭塞',
        ],
        'summary': '闭口为小凶课，主闭塞',
        'special_cases': []
    },
    
    '冲破课': {
        'score': 30,
        'level': '中凶',
        'duanyu': [
            '冲破入课，谋事难成',
            '岁破月破发用',
            '事主破败',
        ],
        'summary': '冲破为中凶课，主破败',
        'special_cases': []
    },
    
    '空亡课': {
        'score': 25,
        'level': '大凶',
        'duanyu': [
            '空亡入课，谋而无成',
            '旬空发用',
            '事主落空',
        ],
        'summary': '空亡为大凶课，主虚空无成',
        'special_cases': []
    },
    
    '死奇课': {
        'score': 20,
        'level': '上凶',
        'duanyu': [
            '死奇入课，大凶',
            '死气发用',
            '事主死丧',
        ],
        'summary': '死奇为上凶课，主死丧',
        'special_cases': []
    },
}


def get_kejing_info(kejing_name: str) -> dict:
    """获取课经信息"""
    return KEJING_DUANYU_COMPLETE.get(kejing_name, {
        'score': 50,
        'level': '吉凶参半',
        'duanyu': ['课经未找到，按平课论'],
        'summary': '平课，平稳无奇',
        'special_cases': []
    })


def get_all_kejing_names() -> list:
    """获取所有课经名称"""
    return list(KEJING_DUANYU_COMPLETE.keys())


def get_kejing_by_type(ke_type: str) -> list:
    """按类型获取课经"""
    result = []
    for name, info in KEJING_DUANYU_COMPLETE.items():
        # 这里需要根据实际类型筛选
        result.append(name)
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("六壬 64 课经完整断语库")
    print("=" * 80)
    print()
    
    print(f"共收录课经：{len(KEJING_DUANYU_COMPLETE)}个")
    print()
    
    # 按类型统计
    types = {
        '贼克法': 0,
        '涉害法': 0,
        '遥克法': 0,
        '昴星法': 0,
        '别责法': 0,
        '伏吟法': 0,
        '反吟法': 0,
        '吉格': 0,
        '凶格': 0,
        '吉凶参半': 0
    }
    
    for name, info in KEJING_DUANYU_COMPLETE.items():
        level = info.get('level', '')
        if level in types:
            types[level] += 1
    
    print("吉凶等级分布：")
    for level, count in types.items():
        if count > 0:
            print(f"  {level}: {count}个")
    
    print()
    print("=" * 80)
