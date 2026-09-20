"""
大六壬股票预测规则引擎
基于六亲体系 + 十二天将 + 三传的股票市场映射规则

数据来源：
- 大六壬投资心法系列（1~10篇）
- 六壬应用研究与股市实战解秘（张海斌）
- 实战案例总结
"""

STOCK_LIUQIN_MAP = {
    "父母": {
        "stock_meaning": "政策/消息面/大盘环境",
        "detail": {
            "旺相": "政策利好、国家支持、行业扶持",
            "休囚": "政策中性、利好出尽",
            "临青龙": "重大利好、资金面宽松",
            "临白虎": "政策打压、利空消息",
            "临朱雀": "新闻传闻、消息面驱动",
            "临太常": "常规政策、业绩兑现",
            "临天空": "利好落空、政策突变",
            "临玄武": "政策不明、暗箱操作"
        },
        "judge_rules": [
            "父母旺相生合日干 → 政策利好，可做多",
            "父母休囚克日干 → 政策利空，需回避",
            "父母临白虎 + 官鬼 → 重大监管风险",
            "父母空亡 → 利好/利空落空，走势平"
        ]
    },
    "妻财": {
        "stock_meaning": "利润/资金流入/盈利",
        "detail": {
            "旺相": "盈利丰厚、资金充裕、利润增长",
            "休囚": "利润微薄、资金紧张",
            "临青龙": "资金大幅流入、主升浪",
            "临白虎": "资金出逃、利润回吐",
            "临朱雀": "题材炒作、游资推动",
            "临玄武": "暗箱资金、庄家操盘",
            "临勾陈": "资金被套、横盘整理",
            "临腾蛇": "资金进出反复、波动大"
        },
        "judge_rules": [
            "妻财旺相临青龙 → 强势上涨，可重仓",
            "妻财临白虎/玄武 → 主力出货，需警惕",
            "妻财空亡 → 业绩不及预期、虚涨",
            "妻财生日干 → 得财，盈利可期",
            "妻财被日干克 → 求财辛苦，利润被压缩"
        ]
    },
    "官鬼": {
        "stock_meaning": "主力/庄家/风险/监管",
        "detail": {
            "旺相": "主力控盘强、市场风险大",
            "休囚": "主力弱势、风险释放",
            "临白虎": "暴跌风险、主力砸盘",
            "临青龙": "主力拉升、机构主导",
            "临朱雀": "监管问询、政策干预",
            "临玄武": "庄家出货、暗藏风险",
            "临勾陈": "主力被套、横盘",
            "临腾蛇": "洗盘、震荡、技术回调"
        },
        "judge_rules": [
            "官鬼临白虎克日干 → 暴跌预警，清仓",
            "官鬼生日干 → 主力拉升，跟随",
            "官鬼临玄武 → 庄股陷阱，回避",
            "官鬼空亡 → 风险解除、利空出尽",
            "官鬼旺相伤妻财 → 主力打压股价"
        ]
    },
    "兄弟": {
        "stock_meaning": "同行/板块联动/竞争",
        "detail": {
            "旺相": "板块效应强、联动明显",
            "休囚": "板块分化、个股独立行情",
            "临青龙": "板块龙头领涨",
            "临白虎": "板块普跌、踩踏",
            "临朱雀": "板块消息刺激",
            "临勾陈": "板块轮动慢、滞涨"
        },
        "judge_rules": [
            "兄弟旺相 → 板块联动，注意跟风效应",
            "兄弟劫财 → 板块内资金分流",
            "兄弟化官鬼 → 板块利空",
            "兄弟临白虎 → 板块性暴跌"
        ]
    },
    "子孙": {
        "stock_meaning": "散户/跟风盘/成交量/技术指标",
        "detail": {
            "旺相": "跟风积极、成交量放大",
            "休囚": "跟风不足、成交量萎缩",
            "临青龙": "量价齐升、散户跟风",
            "临白虎": "放量下跌、散户踩踏",
            "临朱雀": "消息驱动型交易",
            "临腾蛇": "技术性波动、指标背离"
        },
        "judge_rules": [
            "子孙旺相生妻财 → 跟风盘推高股价",
            "子孙化官鬼 → 散户被套、接盘",
            "子孙空亡 → 成交量萎缩、无人关注",
            "子孙临白虎 → 恐慌抛售、放量下跌"
        ]
    }
}

STOCK_TIANJIANG_MAP = {
    "贵人": {
        "stock_meaning": "国家队/权重股/政策底",
        "speed": "慢、稳",
        "judge": "贵人临传 → 有机构护盘，下跌空间有限"
    },
    "腾蛇": {
        "stock_meaning": "洗盘/技术回调/假突破",
        "speed": "快、反复",
        "judge": "腾蛇临财 → 冲高回落，适合高抛低吸"
    },
    "朱雀": {
        "stock_meaning": "消息面/新闻/传闻/游资",
        "speed": "快、消息驱动",
        "judge": "朱雀临父 → 利好公告；朱雀临鬼 → 利空传闻"
    },
    "六合": {
        "stock_meaning": "并购/合作/板块共振",
        "speed": "中等、谈判周期",
        "judge": "六合临财 → 并购利好；六合临兄 → 板块联动"
    },
    "勾陈": {
        "stock_meaning": "横盘/阻力位/拖延",
        "speed": "慢、拖延",
        "judge": "勾陈临财 → 横盘整理，需耐心等待"
    },
    "青龙": {
        "stock_meaning": "资金流入/上涨趋势/主力",
        "speed": "可快可慢",
        "judge": "青龙临财 → 主升浪，重仓持有"
    },
    "天空": {
        "stock_meaning": "利好落空/高开低走",
        "speed": "快、落空",
        "judge": "天空临父 → 利好落空，高开低走"
    },
    "白虎": {
        "stock_meaning": "暴跌/恐慌/放量下跌",
        "speed": "快、猛",
        "judge": "白虎临官 → 暴跌预警，清仓回避"
    },
    "太常": {
        "stock_meaning": "业绩兑现/常规走势",
        "speed": "常规",
        "judge": "太常临财 → 业绩驱动，慢牛走势"
    },
    "玄武": {
        "stock_meaning": "庄家出货/陷阱/假象",
        "speed": "隐秘、慢",
        "judge": "玄武临财 → 诱多陷阱；玄武临鬼 → 阴跌"
    },
    "太阴": {
        "stock_meaning": "主力吸筹/低调建仓",
        "speed": "隐秘、慢",
        "judge": "太阴临财 → 主力暗中吸筹，后市看涨"
    },
    "天后": {
        "stock_meaning": "流动性宽松/资金面",
        "speed": "滋润、慢",
        "judge": "天后临父 → 流动性宽松，利好股市"
    }
}

SANCHUAN_STOCK_MAP = {
    "贼克": {
        "name": "突然袭击",
        "stock_meaning": "突发利好/利空",
        "feature": "来得快，去得也快，适合短线应对"
    },
    "比用": {
        "name": "同类相争",
        "stock_meaning": "板块轮动/分化",
        "feature": "分化行情，需精选个股，不能闭眼买板块"
    },
    "涉害": {
        "name": "多重矛盾",
        "stock_meaning": "多空博弈激烈",
        "feature": "震荡行情，适合高抛低吸"
    },
    "遥克": {
        "name": "远因触发",
        "stock_meaning": "外部因素/外围市场",
        "feature": "受外盘/宏观因素影响大"
    },
    "昴星": {
        "name": "暗中行事",
        "stock_meaning": "庄家运作/内幕交易",
        "feature": "庄股行情，信息不对称，回避"
    },
    "别责": {
        "name": "借力行事",
        "stock_meaning": "借壳/重组/概念炒作",
        "feature": "借题材炒作，注意风险"
    },
    "八专": {
        "name": "我行我素",
        "stock_meaning": "独立行情/主力自嗨",
        "feature": "独立走势，不跟大盘"
    },
    "伏吟": {
        "name": "原地踏步",
        "stock_meaning": "横盘/缩量整理",
        "feature": "整理行情，等待方向"
    },
    "返吟": {
        "name": "反复无常",
        "stock_meaning": "剧烈震荡/反转",
        "feature": "方向不明，多看少动"
    }
}

YINGQI_STOCK_MAP = {
    "地支应期": {
        "子": "11天左右/11月/23-1点",
        "丑": "8天左右/12月/1-3点",
        "寅": "6天左右/1月/3-5点",
        "卯": "4天左右/2月/5-7点",
        "辰": "2天左右/3月/7-9点",
        "巳": "1天左右/4月/9-11点",
        "午": "半天左右/5月/11-13点",
        "未": "2天左右/6月/13-15点",
        "申": "4天左右/7月/15-17点",
        "酉": "6天左右/8月/17-19点",
        "戌": "8天左右/9月/19-21点",
        "亥": "11天左右/10月/21-23点"
    },
    "三传应期": {
        "初传": "1天~2周（催化剂出现）",
        "中传": "1周~2月（主升/主跌浪）",
        "末传": "1月~数月（最终结局）"
    },
    "天将应期": {
        "快（青龙/白虎/朱雀/腾蛇）": "几天内完成",
        "中（贵人/六合）": "几周至月",
        "慢（勾陈/太常/玄武/太阴/天后）": "月至季"
    }
}


class StockLiuRenRules:
    """股票六壬规则引擎"""

    @staticmethod
    def get_liuqin_analysis(liuqin: str, tianjiang: str = "", qiangruo: str = "旺相") -> dict:
        """分析六亲在股票中的含义"""
        if liuqin not in STOCK_LIUQIN_MAP:
            return {"meaning": "未知", "judge": ""}

        info = STOCK_LIUQIN_MAP[liuqin]
        result = {
            "stock_meaning": info["stock_meaning"],
            "detail": info["detail"].get(qiangruo, info["detail"].get("旺相", "")),
            "rules": []
        }

        if tianjiang:
            key = f"临{tianjiang}"
            if key in info["detail"]:
                result["detail"] = info["detail"][key]

        result["rules"] = info["judge_rules"]
        return result

    @staticmethod
    def get_tianjiang_analysis(tianjiang: str) -> dict:
        """分析天将在股票中的含义"""
        if tianjiang not in STOCK_TIANJIANG_MAP:
            return {"meaning": "未知", "judge": ""}
        return STOCK_TIANJIANG_MAP[tianjiang]

    @staticmethod
    def get_sanchuan_analysis(fayong: str) -> dict:
        """分析发用模式在股票中的含义"""
        if fayong not in SANCHUAN_STOCK_MAP:
            return {"meaning": "未知", "feature": ""}
        return SANCHUAN_STOCK_MAP[fayong]

    @staticmethod
    def judge_trend(sike: list, sanchuan: list, tianjiang_list: list) -> dict:
        """综合判断股票走势趋势"""
        score = 0
        reasons = []

        for chuan, tj in zip(sanchuan, tianjiang_list):
            chuan_analysis = StockLiuRenRules.get_liuqin_analysis(chuan, tj)
            if "妻财" in chuan and tj in ("青龙", "六合"):
                score += 2
                reasons.append(f"妻财临{tj}，上涨信号强")
            elif "妻财" in chuan and tj in ("白虎", "玄武", "腾蛇"):
                score -= 1
                reasons.append(f"妻财临{tj}，涨势不稳")
            elif "官鬼" in chuan and tj == "白虎":
                score -= 2
                reasons.append(f"官鬼临白虎，暴跌风险")
            elif "父母" in chuan and tj == "青龙":
                score += 1
                reasons.append(f"父母临青龙，政策利好")
            elif "兄弟" in chuan and tj == "白虎":
                score -= 1
                reasons.append(f"兄弟临白虎，板块利空")

        if score >= 3:
            trend = "涨"
            confidence = min(80 + score * 5, 95)
        elif score >= 1:
            trend = "涨"
            confidence = 60 + score * 5
        elif score >= -1:
            trend = "平"
            confidence = 50
        elif score >= -3:
            trend = "跌"
            confidence = 60 + abs(score) * 5
        else:
            trend = "跌"
            confidence = min(80 + abs(score) * 5, 95)

        return {
            "trend": trend,
            "confidence": confidence,
            "score": score,
            "reasons": reasons
        }
