# -*- coding: utf-8 -*-
"""
大六壬课格匹配系统
将64课经从属课格匹配到8640课例中
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 十三吉课定义
SHISAN_JI_KE = {
    "龙德课": {
        "score": 95,
        "level": "上吉",
        "core_condition": "太岁=月将乘贵人发用",
        "sub_ge": {
            "龙德本课": {"ji_xiong": "上吉", "condition": "太岁=月将乘贵人发用"},
            "带煞为日鬼格": {"ji_xiong": "凶", "condition": "龙德课带煞为日鬼，占讼事干朝廷"}
        }
    },
    "斫轮课": {
        "score": 92,
        "level": "上吉",
        "core_condition": "卯临庚辛申酉发用",
        "sub_ge": {
            "斫轮本课": {"ji_xiong": "上吉", "condition": "卯加庚申发用（四绝体盘）"},
            "斫轮次吉": {"ji_xiong": "吉", "condition": "卯加辛酉发用（四墓覆生盘）"},
            "舟楫格": {"ji_xiong": "吉", "condition": "壬癸日见水神，初末有马引从为轩车"},
            "印绶格": {"ji_xiong": "吉", "condition": "传中见太常、河魁作印绶"},
            "旧轮再斫格": {"ji_xiong": "凶", "condition": "传见本日墓神，主退官失职再谋复兴"},
            "朽木难雕格": {"ji_xiong": "凶", "condition": "卯木值空亡，须另改业"},
            "伤斧格": {"ji_xiong": "凶", "condition": "春季甲乙日寅卯时，木太重"},
            "伤轮格": {"ji_xiong": "凶", "condition": "秋季庚辛日申酉时，金太重"},
            "棺椁格": {"ji_xiong": "凶", "condition": "木休囚乘白虎"},
            "财就人格": {"ji_xiong": "吉", "condition": "辛卯日干上卯，宜急取财"}
        }
    },
    "轩盖课": {
        "score": 90,
        "level": "上吉",
        "core_condition": "正七月午发用，三传午卯子",
        "sub_ge": {
            "轩盖本课": {"ji_xiong": "上吉", "condition": "正七月午发用，三传午卯子，天马在午"},
            "华盖轩车格": {"ji_xiong": "上吉", "condition": "卯乘天马或龙常，日用旺相为太岁月将"},
            "三交格": {"ji_xiong": "凶", "condition": "余月轩盖带三交，出军冲野决防战斗"},
            "乘轩落马格": {"ji_xiong": "大凶", "condition": "三传带煞乘蛇虎死气克年命日辰，或空亡，或卯作丧车，身弱人衰"},
            "魂游千里格": {"ji_xiong": "凶", "condition": "占病者魂游千里"},
            "换司易衙格": {"ji_xiong": "凶", "condition": "论讼换司易衙"}
        }
    },
    "铸印课": {
        "score": 88,
        "level": "上吉",
        "core_condition": "戌加巳入传，三传巳戌卯",
        "sub_ge": {
            "铸印本课": {"ji_xiong": "上吉", "condition": "戌加巳入传，乘吉将日用旺相"},
            "铸印乘轩格": {"ji_xiong": "上吉", "condition": "传见太冲为车轮，乘贵人龙常阴合吉将"},
            "印绶双全格": {"ji_xiong": "上吉", "condition": "戊己日为生日之印，遇太常为绶"},
            "破印损模格": {"ji_xiong": "凶", "condition": "春夏巳午日时火旺，戌值空亡月破日辰无气"},
            "铸印不成格": {"ji_xiong": "凶", "condition": "末传得天后玄武临水乡与日相破"},
            "庶人凶格": {"ji_xiong": "凶", "condition": "常人占得反主官灾刑害"}
        }
    },
    "合欢课": {
        "score": 86,
        "level": "上吉",
        "core_condition": "干支合+三传合+年命吉将",
        "sub_ge": {
            "合欢本课": {"ji_xiong": "上吉", "condition": "干支相合+三传六合+年命乘吉将"},
            "三合格": {"ji_xiong": "吉", "condition": "三传三合，事关众，克应过月"},
            "六合格": {"ji_xiong": "吉", "condition": "六合阴阳配，夫妇和顺"},
            "蜜里藏砒格": {"ji_xiong": "凶", "condition": "合带刑冲破害，合而藏祸"},
            "合空格": {"ji_xiong": "凶", "condition": "合逢空亡，事费力难济"},
            "暗鬼克日格": {"ji_xiong": "凶", "condition": "传退连茹合带暗鬼克日乘蛇虎雀"}
        }
    },
    "合美课": {
        "score": 84,
        "level": "上吉",
        "core_condition": "干支递合或互合",
        "sub_ge": {
            "合美本课": {"ji_xiong": "上吉", "condition": "干支递合或互合，三传递相生合"},
            "递生格": {"ji_xiong": "吉", "condition": "三传递生日干"},
            "取还魂债格": {"ji_xiong": "吉", "condition": "传遇三合全脱生干支上财神"},
            "蜜中砒格": {"ji_xiong": "凶", "condition": "三合犯杀（如寅午戌见午自刑丑六害子正冲）"},
            "交合逢空格": {"ji_xiong": "凶", "condition": "交时和美后成画饼"},
            "交合盗气格": {"ji_xiong": "凶", "condition": "彼此怀脱"},
            "交害格": {"ji_xiong": "凶", "condition": "主客各有嫉妒"},
            "交刑格": {"ji_xiong": "凶", "condition": "主合致争竞"},
            "交冲格": {"ji_xiong": "凶", "condition": "主先合后难"},
            "交克格": {"ji_xiong": "凶", "condition": "主合而争讼，笑里藏刀"}
        }
    },
    "繁昌课": {
        "score": 82,
        "level": "中吉",
        "core_condition": "三传皆旺相有气",
        "sub_ge": {
            "繁昌本课": {"ji_xiong": "中吉", "condition": "三传皆旺相有气，生气充盈"},
            "德孕格": {"ji_xiong": "吉", "condition": "夫妻年立德方发用，主怀孕年内必生贵子"},
            "旺孕格": {"ji_xiong": "吉", "condition": "夫妻行年俱随旺相气三合位上"}
        }
    },
    "富贵课": {
        "score": 80,
        "level": "中吉",
        "core_condition": "贵人乘旺相临日辰发用",
        "sub_ge": {
            "富贵本课": {"ji_xiong": "中吉", "condition": "天乙贵人乘旺相气临日辰年命发用"},
            "富贵权印格": {"ji_xiong": "上吉", "condition": "戌加巳，富贵权印之象"},
            "势消课": {"ji_xiong": "凶", "condition": "贵人临辰戌为入狱，告贵不允所占皆凶"}
        }
    },
    "时泰课": {
        "score": 78,
        "level": "中吉",
        "core_condition": "太岁月建乘青龙六合发用",
        "sub_ge": {
            "时泰本课": {"ji_xiong": "中吉", "condition": "太岁月建乘青龙六合带财德神发用"},
            "天恩格": {"ji_xiong": "吉", "condition": "干支属本季旺气得用"},
            "天恩未定格": {"ji_xiong": "凶", "condition": "传见空亡，事多虚喜，上人犹豫不决"}
        }
    },
    "亨通课": {
        "score": 76,
        "level": "中吉",
        "core_condition": "三传递生日干",
        "sub_ge": {
            "亨通本课": {"ji_xiong": "中吉", "condition": "三传递生日干"},
            "递生格": {"ji_xiong": "吉", "condition": "初生中中生末末生干，或末生中中生初初生干"},
            "俱生格": {"ji_xiong": "吉", "condition": "干上生干支上生支"},
            "互生格": {"ji_xiong": "吉", "condition": "干上生支支上生干"},
            "俱旺格": {"ji_xiong": "吉", "condition": "干上乃干旺神支上乃支旺神"},
            "互旺格": {"ji_xiong": "吉", "condition": "干上乃支旺神支上乃干旺神"},
            "自在格": {"ji_xiong": "吉", "condition": "支加干而生日，主有人来资助我"},
            "恩多怨深格": {"ji_xiong": "凶", "condition": "初生中中生末末克日干"},
            "递生值空亡格": {"ji_xiong": "凶", "condition": "递生值空亡破刑克害无甚解救"}
        }
    },
    "荣华课": {
        "score": 74,
        "level": "中吉",
        "core_condition": "禄马贵人临干支发用",
        "sub_ge": {
            "荣华本课": {"ji_xiong": "中吉", "condition": "禄马贵人临干支年命旺相气发用传乘吉将"},
            "两贵周全格": {"ji_xiong": "吉", "condition": "干支见昼夜贵人，主事得两贵周全成合"},
            "贵人蹉跎格": {"ji_xiong": "凶", "condition": "告贵干事多不归一"},
            "遍地贵人格": {"ji_xiong": "凶", "condition": "贵多不贵，告贵无成"},
            "贵人作日鬼格": {"ji_xiong": "凶", "condition": "贵人作日鬼临干，占官利占病神祇为害"},
            "贵人作六害格": {"ji_xiong": "凶", "condition": "占讼理直而作曲断"}
        }
    },
    "官爵课": {
        "score": 72,
        "level": "中吉",
        "core_condition": "驿马发用+魁常入传",
        "sub_ge": {
            "官爵本课": {"ji_xiong": "中吉", "condition": "驿马发用天魁太常入传"},
            "四马带印绶格": {"ji_xiong": "上吉", "condition": "四路驿马带印绶遇德神天马青龙"},
            "官爵淹留格": {"ji_xiong": "凶", "condition": "驿马被冲破"},
            "官爵失印格": {"ji_xiong": "凶", "condition": "天魁太常值空亡或日用休囚"}
        }
    },
    "德庆课": {
        "score": 70,
        "level": "中吉",
        "core_condition": "天月日德发用",
        "sub_ge": {
            "德庆本课": {"ji_xiong": "中吉", "condition": "日德/支德/天德/月德发用年命上神乘吉将"},
            "德神为鬼格": {"ji_xiong": "吉", "condition": "占功名利病无妨乘龙尤吉"},
            "减德格": {"ji_xiong": "凶", "condition": "子日巳德归亥乘元武夹克，事参商"},
            "君子为小人格": {"ji_xiong": "凶", "condition": "乙日申德加酉为用酉来克乙申化鬼四杀不没"},
            "德空格": {"ji_xiong": "凶", "condition": "德神值空亡"},
            "带杀乘虎格": {"ji_xiong": "凶", "condition": "德神带杀乘白虎"}
        }
    }
}

# 其他课经定义
OTHER_KE_JING = {
    "元首课": {
        "score": 98,
        "level": "上上吉",
        "core_condition": "一上克下为用",
        "sub_ge": {
            "元首本课": {"ji_xiong": "上上吉", "condition": "一上克下为用，天地神人万物有序"},
            "上克下有嫌疑格": {"ji_xiong": "凶", "condition": "上克下发用主有嫌疑"}
        }
    },
    "重审课": {
        "score": 85,
        "level": "吉",
        "core_condition": "一下克上为用",
        "sub_ge": {
            "重审本课": {"ji_xiong": "吉", "condition": "一下克上为用，须再审详"},
            "下克上无气格": {"ji_xiong": "凶", "condition": "下克上无气主逆犯"}
        }
    },
    "涉害课": {
        "score": 75,
        "level": "中吉",
        "core_condition": "涉害归家用孟仲季为用",
        "sub_ge": {
            "涉害本课": {"ji_xiong": "中吉", "condition": "涉害归家用孟仲季为用"},
            "见机格": {"ji_xiong": "吉", "condition": "涉害相等取四孟上神发用"},
            "察微格": {"ji_xiong": "凶", "condition": "无孟取仲季为用，主小人谋害"},
            "缀瑕格": {"ji_xiong": "凶", "condition": "涉害相等取四课中先见者用，事艰难"}
        }
    },
    "遥克课": {
        "score": 70,
        "level": "中吉",
        "core_condition": "四课上神克日干或日干克上神",
        "sub_ge": {
            "蒿矢格": {"ji_xiong": "吉", "condition": "四课上神克日干为用，事始惊终安"},
            "弹射格": {"ji_xiong": "凶", "condition": "日干克上神为用，虚名虚得"}
        }
    },
    "昴星课": {
        "score": 65,
        "level": "中",
        "core_condition": "四课无克无遥克",
        "sub_ge": {
            "虎视转蓬格": {"ji_xiong": "吉", "condition": "刚日仰视酉上神为用，主惊恐但可成"},
            "冬蛇掩目格": {"ji_xiong": "凶", "condition": "柔日伏视酉下神为用，事多暗昧"}
        }
    },
    "别责课": {
        "score": 60,
        "level": "中",
        "core_condition": "四课不备无克别取一神为用",
        "sub_ge": {
            "别责本课": {"ji_xiong": "凶", "condition": "四课不备无克别取一神为用"},
            "损而能益格": {"ji_xiong": "吉", "condition": "神将吉日用旺相"}
        }
    },
    "八专课": {
        "score": 55,
        "level": "中",
        "core_condition": "干支同位无克",
        "sub_ge": {
            "八专本课": {"ji_xiong": "凶", "condition": "干支同位无克"},
            "帷簿不修格": {"ji_xiong": "凶", "condition": "遇天后六合玄武入传，主男女淫乱"}
        }
    },
    "伏吟课": {
        "score": 50,
        "level": "中",
        "core_condition": "月将=占时",
        "sub_ge": {
            "伏吟本课": {"ji_xiong": "凶", "condition": "月将=占时"},
            "自任格": {"ji_xiong": "吉", "condition": "刚日伏吟"},
            "自信格": {"ji_xiong": "吉", "condition": "刚日伏吟有克"},
            "杜传格": {"ji_xiong": "凶", "condition": "传行不过"}
        }
    },
    "反吟课": {
        "score": 45,
        "level": "中",
        "core_condition": "月将冲占时",
        "sub_ge": {
            "反吟本课": {"ji_xiong": "凶", "condition": "月将冲占时"},
            "无依格": {"ji_xiong": "凶", "condition": "反吟无克"},
            "无亲格": {"ji_xiong": "凶", "condition": "反吟无克无依"}
        }
    },
    "三光课": {
        "score": 90,
        "level": "上吉",
        "core_condition": "日辰用神旺相吉将",
        "sub_ge": {
            "三光本课": {"ji_xiong": "上吉", "condition": "日辰用神旺相吉将"},
            "日用休囚格": {"ji_xiong": "凶", "condition": "日用休囚神将凶"}
        }
    },
    "三阳课": {
        "score": 88,
        "level": "上吉",
        "core_condition": "阳气开泰用神旺相",
        "sub_ge": {
            "三阳本课": {"ji_xiong": "上吉", "condition": "阳气开泰用神旺相"},
            "三阳开泰格": {"ji_xiong": "上吉", "condition": "加吉将万事吉庆"}
        }
    },
    "引从课": {
        "score": 86,
        "level": "上吉",
        "core_condition": "日辰前后上神为初末传",
        "sub_ge": {
            "引从本课": {"ji_xiong": "上吉", "condition": "日辰前后上神为初末传"},
            "拱干格": {"ji_xiong": "上吉", "condition": "初末传拱天干，主官职升擢"},
            "两贵引从格": {"ji_xiong": "上吉", "condition": "两贵拱干，主上人提携"},
            "拱支格": {"ji_xiong": "吉", "condition": "初末传拱支，主家宅吉庆"},
            "贵临支干拱年命格": {"ji_xiong": "上吉", "condition": "宜告贵用事必得两贵成就"}
        }
    }
}

# 合并所有课经
ALL_KE_JING = {**SHISAN_JI_KE, **OTHER_KE_JING}

# 天干地支
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六阳位、六阴位
LIU_YANG_WEI = ["子", "寅", "辰", "午", "申", "戌"]
LIU_YIN_WEI = ["丑", "卯", "巳", "未", "酉", "亥"]

# 天马查法（正月起午，顺行六阳位）
TIAN_MA_MAP = {
    "子": "辰", "丑": "辰",  # 正月、二月
    "寅": "申", "卯": "申",  # 三月、四月
    "辰": "子", "巳": "子",  # 五月、六月
    "午": "午", "未": "午",  # 七月、八月
    "申": "戌", "酉": "戌",  # 九月、十月
    "戌": "寅", "亥": "寅"   # 十一月、十二月
}

# 驿马查法
YI_MA_MAP = {
    "申子辰": "寅",
    "亥卯未": "巳",
    "寅午戌": "申",
    "巳酉丑": "亥"
}

# 日德查法
RI_DE_MAP = {
    "甲": "寅", "己": "寅",
    "乙": "申", "庚": "申",
    "丙": "巳", "辛": "巳", "戊": "巳", "癸": "巳",
    "丁": "亥", "壬": "亥"
}

# 日禄查法
RI_LU_MAP = {
    "甲": "寅", "乙": "卯",
    "丙": "巳", "丁": "午", "戊": "巳", "己": "午",
    "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子"
}

# 六合
LIU_HE = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]

# 三合
SAN_HE = {
    "申子辰": "水",
    "亥卯未": "木",
    "寅午戌": "火",
    "巳酉丑": "金"
}


def get_ri_gan(ri_gan_zhi: str) -> str:
    """获取日干"""
    return ri_gan_zhi[0] if ri_gan_zhi else ""


def get_ri_zhi(ri_gan_zhi: str) -> str:
    """获取日支"""
    return ri_gan_zhi[1] if ri_gan_zhi else ""


def get_yi_ma(ri_zhi: str) -> str:
    """获取日驿马"""
    for san_he, yi_ma in YI_MA_MAP.items():
        if ri_zhi in san_he:
            return yi_ma
    return ""


def get_ri_de(ri_gan: str) -> str:
    """获取日德"""
    return RI_DE_MAP.get(ri_gan, "")


def get_ri_lu(ri_gan: str) -> str:
    """获取日禄"""
    return RI_LU_MAP.get(ri_gan, "")


def get_tian_ma(yue: str) -> str:
    """获取天马（根据月份）"""
    return TIAN_MA_MAP.get(yue, "")


def check_chu_chuan_is_mao(sanchuan: dict) -> bool:
    """检查初传是否为卯"""
    chu_chuan = sanchuan.get("初传", "")
    return chu_chuan == "卯"


def check_sanchuan_wu_mao_zi(sanchuan: dict) -> bool:
    """检查三传是否为午卯子"""
    sanchuan_list = sanchuan.get("三传", [])
    return set(sanchuan_list) == {"午", "卯", "子"}


def check_sanchuan_si_xu_mao(sanchuan: dict) -> bool:
    """检查三传是否为巳戌卯"""
    sanchuan_list = sanchuan.get("三传", [])
    return set(sanchuan_list) == {"巳", "戌", "卯"}


def check_xu_jia_si(sanchuan: dict) -> bool:
    """检查戌是否加巳（初传为巳，三传含戌）"""
    sanchuan_list = sanchuan.get("三传", [])
    chu_chuan = sanchuan.get("初传", "")
    return chu_chuan == "巳" and "戌" in sanchuan_list


def check_mao_lin_geng_xin(sanchuan: dict, sike: list) -> bool:
    """检查卯是否临庚辛申酉"""
    chu_chuan = sanchuan.get("初传", "")
    if chu_chuan != "卯":
        return False
    
    # 检查四课中卯的位置
    for ke in sike:
        if len(ke) >= 3:
            if ke[1] == "卯":  # 天盘为卯
                di_pan = ke[2] if len(ke) > 2 else ""
                if di_pan in ["庚", "辛", "申", "酉"]:
                    return True
    return False


def is_shisan_ji_ke(ke_ti: str) -> bool:
    """检查是否为十三吉课"""
    return ke_ti in SHISAN_JI_KE


def match_ke_ge(ke_li: dict) -> dict:
    """匹配课格"""
    result = {
        "ke_ti": ke_li.get("sanchuan", {}).get("课体", ""),
        "matched_ke_ge": [],
        "is_shisan_ji_ke": False,
        "score": 0,
        "level": "",
        "sub_ge_matched": [],
        "ke_ge_explanation": ""
    }
    
    ke_ti = result["ke_ti"]
    ri_gan_zhi = ke_li.get("ri_gan_zhi", "")
    ri_gan = get_ri_gan(ri_gan_zhi)
    ri_zhi = get_ri_zhi(ri_gan_zhi)
    yue = ke_li.get("yue", "")
    shi = ke_li.get("shi", "")
    sanchuan = ke_li.get("sanchuan", {})
    sike = ke_li.get("sike", [])
    
    # 检查是否为十三吉课
    if ke_ti in SHISAN_JI_KE:
        result["is_shisan_ji_ke"] = True
        result["score"] = SHISAN_JI_KE[ke_ti]["score"]
        result["level"] = SHISAN_JI_KE[ke_ti]["level"]
        result["matched_ke_ge"].append(ke_ti)
        
        # 匹配从属格
        sub_ge_info = SHISAN_JI_KE[ke_ti]["sub_ge"]
        for sub_ge_name, sub_ge_data in sub_ge_info.items():
            result["sub_ge_matched"].append({
                "name": sub_ge_name,
                "ji_xiong": sub_ge_data["ji_xiong"],
                "condition": sub_ge_data["condition"]
            })
        
        # 生成课格说明
        result["ke_ge_explanation"] = generate_ke_ge_explanation(ke_ti, ke_li)
    
    # 检查其他课经
    elif ke_ti in OTHER_KE_JING:
        result["score"] = OTHER_KE_JING[ke_ti]["score"]
        result["level"] = OTHER_KE_JING[ke_ti]["level"]
        result["matched_ke_ge"].append(ke_ti)
        
        # 匹配从属格
        sub_ge_info = OTHER_KE_JING[ke_ti]["sub_ge"]
        for sub_ge_name, sub_ge_data in sub_ge_info.items():
            result["sub_ge_matched"].append({
                "name": sub_ge_name,
                "ji_xiong": sub_ge_data["ji_xiong"],
                "condition": sub_ge_data["condition"]
            })
        
        result["ke_ge_explanation"] = generate_ke_ge_explanation(ke_ti, ke_li)
    
    else:
        # 未知课体
        result["ke_ge_explanation"] = f"课体【{ke_ti}】未在课经定义中找到"
    
    return result


def generate_ke_ge_explanation(ke_ti: str, ke_li: dict) -> str:
    """生成课格说明"""
    ri_gan_zhi = ke_li.get("ri_gan_zhi", "")
    ri_gan = get_ri_gan(ri_gan_zhi)
    ri_zhi = get_ri_zhi(ri_gan_zhi)
    yue = ke_li.get("yue", "")
    shi = ke_li.get("shi", "")
    sanchuan = ke_li.get("sanchuan", {})
    sike = ke_li.get("sike", [])
    
    explanation_parts = [f"【{ke_ti}】"]
    
    # 添加核心条件
    if ke_ti in ALL_KE_JING:
        core_condition = ALL_KE_JING[ke_ti]["core_condition"]
        explanation_parts.append(f"核心条件：{core_condition}")
    
    # 添加三传信息
    sanchuan_list = sanchuan.get("三传", [])
    chu_chuan = sanchuan.get("初传", "")
    zhong_chuan = sanchuan.get("中传", "")
    mo_chuan = sanchuan.get("末传", "")
    
    explanation_parts.append(f"三传：{chu_chuan}→{zhong_chuan}→{mo_chuan}")
    explanation_parts.append(f"起法：{sanchuan.get('起法', '')}")
    
    # 特殊课格判断
    if ke_ti == "轩盖课":
        tian_ma = get_tian_ma(yue)
        explanation_parts.append(f"天马位置：{tian_ma}")
        if yue in ["子", "午"]:
            explanation_parts.append("【符合】正七月天马在午")
        else:
            explanation_parts.append("【注意】非正七月，需检查是否符合轩盖课条件")
    
    elif ke_ti == "斫轮课":
        if check_mao_lin_geng_xin(sanchuan, sike):
            explanation_parts.append("【符合】卯临庚辛申酉发用")
        else:
            explanation_parts.append("【需核实】检查卯是否临庚辛申酉")
    
    elif ke_ti == "铸印课":
        if check_sanchuan_si_xu_mao(sanchuan):
            explanation_parts.append("【符合】三传巳戌卯")
        else:
            explanation_parts.append("【需核实】检查三传是否为巳戌卯")
    
    return "\n".join(explanation_parts)


def process_all_ke_li():
    """处理所有课例"""
    # 加载课例数据
    input_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\720_ke_li_jiu_zong_men.json"
    output_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\8640_ke_ge_matched.json"
    
    print(f"加载课例数据: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    ke_li_data = data.get("ke_li", {})
    total = len(ke_li_data)
    print(f"共 {total} 个课例")
    
    # 处理每个课例
    results = {
        "metadata": {
            "total": total,
            "processed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "shisan_ji_ke_count": 0,
            "other_ke_jing_count": 0,
            "unknown_ke_ti_count": 0
        },
        "ke_li": {}
    }
    
    for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
        if (i + 1) % 1000 == 0:
            print(f"处理进度: {i + 1}/{total}")
        
        # 匹配课格
        ke_ge_result = match_ke_ge(ke_li)
        
        # 统计
        if ke_ge_result["is_shisan_ji_ke"]:
            results["metadata"]["shisan_ji_ke_count"] += 1
        elif ke_ge_result["matched_ke_ge"]:
            results["metadata"]["other_ke_jing_count"] += 1
        else:
            results["metadata"]["unknown_ke_ti_count"] += 1
        
        # 保存结果
        results["ke_li"][ke_li_key] = {
            **ke_li,
            "ke_ge_matched": ke_ge_result
        }
    
    # 保存结果
    print(f"保存结果: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成报告
    generate_report(results, output_file.replace(".json", "_report.md"))
    
    print("处理完成！")
    return results


def generate_report(results: dict, report_file: str):
    """生成匹配报告"""
    metadata = results["metadata"]
    
    report = f"""# 8640课例课格匹配报告

## 基本信息
- 处理时间：{metadata['processed_time']}
- 总课例数：{metadata['total']}
- 十三吉课数：{metadata['shisan_ji_ke_count']}
- 其他课经数：{metadata['other_ke_jing_count']}
- 未知课体数：{metadata['unknown_ke_ti_count']}

## 十三吉课统计
"""
    
    # 统计各课经数量
    ke_jing_count = {}
    for ke_li_key, ke_li in results["ke_li"].items():
        ke_ge = ke_li.get("ke_ge_matched", {})
        ke_ti = ke_ge.get("ke_ti", "")
        if ke_ti in SHISAN_JI_KE:
            ke_jing_count[ke_ti] = ke_jing_count.get(ke_ti, 0) + 1
    
    for ke_ti, count in sorted(ke_jing_count.items(), key=lambda x: -x[1]):
        score = SHISAN_JI_KE[ke_ti]["score"]
        level = SHISAN_JI_KE[ke_ti]["level"]
        report += f"- {ke_ti}（{level}，{score}分）：{count}例\n"
    
    # 保存报告
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"报告已保存: {report_file}")


if __name__ == "__main__":
    process_all_ke_li()
