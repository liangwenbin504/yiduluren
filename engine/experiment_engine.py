"""
十一分类实验引擎

管理多类预测课的日程安排：
  fixed_time         — 固定时辰课（对照组），每日 09:00 起课
  ri_gan_pian_cai    — 日干偏财时课
  ri_zhi_pian_cai    — 日支偏财时课
  ri_gan_shi_shen    — 日干食神时课
  ri_zhi_shi_shen    — 日支食神时课
  ri_gan_zheng_yin   — 日干正印时课
  ri_gan_pian_yin    — 日干偏印时课
  ri_zhi_zheng_yin   — 日支正印时课
  ri_zhi_pian_yin    — 日支偏印时课
  random             — 随机课，每日 13:30~14:00 随机起课
  manual             — 人工指定时

每类课各有一个独立虚拟账户（初始资金 100,000 元），独立交易、独立统计。
"""
from datetime import datetime, timedelta, date

TIAN_GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DI_ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 子→0, 丑→1, ... 亥→11
DI_ZHI_IDX = {z:i for i,z in enumerate(DI_ZHI)}

# 交易时段对应的地支索引：巳(5)=09-11, 午(6)=11-13, 未(7)=13-15
MARKET_SHI_IDX = [5, 6, 7]

CATEGORIES = {
    "fixed_time": "固定时辰课",
    "ri_gan_pian_cai": "日干偏财时",
    "ri_zhi_pian_cai": "日支偏财时",
    "ri_gan_shi_shen": "日干食神时",
    "ri_zhi_shi_shen": "日支食神时",
    "ri_gan_zheng_yin": "日干正印时",
    "ri_gan_pian_yin": "日干偏印时",
    "ri_zhi_zheng_yin": "日支正印时",
    "ri_zhi_pian_yin": "日支偏印时",
    "random": "随机课",
    "manual": "人工指定时",
}

CATEGORY_NAMES = {v:k for k,v in CATEGORIES.items()}

ref = date(1984, 1, 31)

# ======================================================================
#   偏财时表（日干版）—— 以日干为"我"，我克者为财
#   规则：日干庚(金)克木 → 寅卯为偏财时
# ======================================================================
PIAN_CAI_SHI_BY_GAN = {
    '甲': ['辰','戌','丑','未'], '乙': ['辰','戌','丑','未'],
    '丙': ['申','酉'],           '丁': ['申','酉'],
    '戊': ['亥','子'],           '己': ['亥','子'],
    '庚': ['寅','卯'],           '辛': ['寅','卯'],
    '壬': ['巳','午'],           '癸': ['巳','午'],
}

# 日干版食神时（日干所生，阴阳异性）
# 例：庚(阳金)生癸(阴水)→亥
SHI_SHEN_SHI_BY_GAN = {
    '甲': ['巳'],    '乙': ['午'],
    '丙': ['丑','未'], '丁': ['辰','戌'],
    '戊': ['酉'],    '己': ['申'],
    '庚': ['亥'],    '辛': ['子'],
    '壬': ['卯'],    '癸': ['寅'],
}

# 日干版伤官时（日干所生，阴阳同性）—— 仅做参考
SHANG_GUAN_SHI_BY_GAN = {
    '甲': ['午'],    '乙': ['巳'],
    '丙': ['辰','戌'], '丁': ['丑','未'],
    '戊': ['申'],    '己': ['酉'],
    '庚': ['子'],    '辛': ['亥'],
    '壬': ['寅'],    '癸': ['卯'],
}

# ======================================================================
#   偏财时表（日支版）—— 以日支为"我"，我克者为财
#   规则：日支辰(土)克水 → 亥子为偏财时
# ======================================================================
PIAN_CAI_SHI_BY_ZHI = {
    '子': ['巳','午'], '丑': ['亥','子'], '寅': ['辰','戌','丑','未'],
    '卯': ['辰','戌','丑','未'], '辰': ['亥','子'], '巳': ['申','酉'],
    '午': ['申','酉'], '未': ['亥','子'], '申': ['寅','卯'],
    '酉': ['寅','卯'], '戌': ['亥','子'], '亥': ['巳','午'],
}

# 日支版食神时（日支所生，阴阳异性）
SHI_SHEN_SHI_BY_ZHI = {
    '子': ['卯'], '丑': ['申'], '寅': ['巳'], '卯': ['午'],
    '辰': ['酉'], '巳': ['辰','戌'], '午': ['丑','未'],
    '未': ['申'], '申': ['亥'], '酉': ['子'],
    '戌': ['酉'], '亥': ['寅'],
}

# 日支版伤官时（日支所生，阴阳同性）—— 仅做参考
SHANG_GUAN_SHI_BY_ZHI = {
    '子': ['寅'], '丑': ['酉'], '寅': ['午'], '卯': ['巳'],
    '辰': ['申'], '巳': ['丑','未'], '午': ['辰','戌'],
    '未': ['卯'], '申': ['子'], '酉': ['亥'],
    '戌': ['申'], '亥': ['卯'],
}

# ======================================================================
#   正印时（日干版）—— 生日干，阴阳异性
#   规则：以日干的"正印"天干的禄位为时辰
# ======================================================================
ZHENG_YIN_SHI_BY_GAN = {
    '甲': ['子'], '乙': ['亥'], '丙': ['卯'], '丁': ['寅'],
    '戊': ['午'], '己': ['巳'], '庚': ['午'], '辛': ['巳'],
    '壬': ['酉'], '癸': ['申'],
}

# ======================================================================
#   偏印时（日干版）—— 生日干，阴阳同性
# ======================================================================
PIAN_YIN_SHI_BY_GAN = {
    '甲': ['亥'], '乙': ['子'], '丙': ['寅'], '丁': ['卯'],
    '戊': ['巳'], '己': ['午'], '庚': ['巳'], '辛': ['午'],
    '壬': ['申'], '癸': ['酉'],
}

# ======================================================================
#   正印时（日支版）—— 生日支本气，阴阳异性
# ======================================================================
ZHENG_YIN_SHI_BY_ZHI = {
    '子': ['申'], '丑': ['巳'], '寅': ['子'], '卯': ['亥'],
    '辰': ['午'], '巳': ['卯'], '午': ['寅'], '未': ['巳'],
    '申': ['午'], '酉': ['巳'], '戌': ['午'], '亥': ['酉'],
}

# ======================================================================
#   偏印时（日支版）—— 生日支本气，阴阳同性
# ======================================================================
PIAN_YIN_SHI_BY_ZHI = {
    '子': ['酉'], '丑': ['午'], '寅': ['亥'], '卯': ['子'],
    '辰': ['巳'], '巳': ['寅'], '午': ['卯'], '未': ['午'],
    '申': ['巳'], '酉': ['午'], '戌': ['巳'], '亥': ['申'],
}


def calc_rizhu(target_date):
    days = (target_date - ref).days
    return TIAN_GAN[days%10], DI_ZHI[days%12], TIAN_GAN[days%10]+DI_ZHI[days%12]


def get_shichen_from_hour(hour: int) -> str:
    if hour >= 23 or hour < 1:
        return '子'
    result = '子'
    for h, z in [(1,'丑'),(3,'寅'),(5,'卯'),(7,'辰'),(9,'巳'),(11,'午'),
                 (13,'未'),(15,'申'),(17,'酉'),(19,'戌'),(21,'亥')]:
        if hour >= h:
            result = z
    return result


# ── 日干版偏财时查询 ──

def get_pian_cai_shichen_by_gan(ri_gan: str) -> list[str]:
    """按日干查偏财时（日干所克的地支时辰）"""
    return PIAN_CAI_SHI_BY_GAN.get(ri_gan, [])


def get_shi_shen_shichen_by_gan(ri_gan: str) -> list[str]:
    """按日干查食神时（日干所生、阴阳异性的地支时辰）"""
    return SHI_SHEN_SHI_BY_GAN.get(ri_gan, [])


def get_zheng_yin_shichen_by_gan(ri_gan: str) -> list[str]:
    """按日干查正印时（生日干、阴阳异性的地支时辰）"""
    return ZHENG_YIN_SHI_BY_GAN.get(ri_gan, [])


def get_pian_yin_shichen_by_gan(ri_gan: str) -> list[str]:
    """按日干查偏印时（生日干、阴阳同性的地支时辰）"""
    return PIAN_YIN_SHI_BY_GAN.get(ri_gan, [])


def suggest_pian_cai_shichen_by_gan(ri_gan: str) -> dict:
    """
    根据日干，建议今天的财爻时用什么时辰测。

    规则：
    - 偏财时（日干所克）在交易时段(巳午未)内的 → 直接用偏财时
    - 偏财时不在交易时段内 → 改用食神时（日干所生、阴阳异性）
    - 食神时也不在交易时段内 → 无可用时辰
    """
    pcs = PIAN_CAI_SHI_BY_GAN.get(ri_gan, [])
    ss  = SHI_SHEN_SHI_BY_GAN.get(ri_gan, [])

    pc_in_market = [z for z in pcs if DI_ZHI_IDX[z] in MARKET_SHI_IDX]
    ss_in_market = [z for z in ss  if DI_ZHI_IDX[z] in MARKET_SHI_IDX]

    if pc_in_market:
        return {
            "type": "pian_cai",
            "label": "偏财时",
            "shichen_list": pc_in_market,
        }
    elif ss_in_market:
        return {
            "type": "shi_shen",
            "label": "食神时",
            "shichen_list": ss_in_market,
            "fallback_reason": f"偏财时({','.join(pcs)})不在交易时段，改用食神时",
        }
    else:
        return {
            "type": "none",
            "label": "无可用",
            "shichen_list": [],
            "fallback_reason": f"偏财时({','.join(pcs)})与食神时({','.join(ss)})均不在交易时段",
        }


# ── 日支版偏财时查询 ──

def get_pian_cai_shichen_by_zhi(ri_zhi: str) -> list[str]:
    """按日支查偏财时（日支所克的地支时辰）"""
    return PIAN_CAI_SHI_BY_ZHI.get(ri_zhi, [])


def get_shi_shen_shichen_by_zhi(ri_zhi: str) -> list[str]:
    """按日支查食神时"""
    return SHI_SHEN_SHI_BY_ZHI.get(ri_zhi, [])


def get_zheng_yin_shichen_by_zhi(ri_zhi: str) -> list[str]:
    """按日支查正印时"""
    return ZHENG_YIN_SHI_BY_ZHI.get(ri_zhi, [])


def get_pian_yin_shichen_by_zhi(ri_zhi: str) -> list[str]:
    """按日支查偏印时"""
    return PIAN_YIN_SHI_BY_ZHI.get(ri_zhi, [])


def suggest_pian_cai_shichen_by_zhi(ri_zhi: str) -> dict:
    """
    根据日支，建议今天的财爻时用什么时辰测。

    规则同 suggest_pian_cai_shichen_by_gan，但基于日支查表。
    """
    pcs = PIAN_CAI_SHI_BY_ZHI.get(ri_zhi, [])
    ss  = SHI_SHEN_SHI_BY_ZHI.get(ri_zhi, [])

    pc_in_market = [z for z in pcs if DI_ZHI_IDX[z] in MARKET_SHI_IDX]
    ss_in_market = [z for z in ss  if DI_ZHI_IDX[z] in MARKET_SHI_IDX]

    if pc_in_market:
        return {
            "type": "pian_cai",
            "label": "日支偏财时",
            "shichen_list": pc_in_market,
        }
    elif ss_in_market:
        return {
            "type": "shi_shen",
            "label": "日支食神时",
            "shichen_list": ss_in_market,
            "fallback_reason": f"偏财时({','.join(pcs)})不在交易时段，改用食神时",
        }
    else:
        return {
            "type": "none",
            "label": "无可用",
            "shichen_list": [],
            "fallback_reason": f"偏财时({','.join(pcs)})与食神时({','.join(ss)})均不在交易时段",
        }


def get_today_schedule(today_date: date = None) -> list[dict]:
    """
    返回今天的各类别排程。

    返回格式：
    [
      {"category": "fixed_time",     "label": "固定时辰课",    "shi_chen": "巳", "time": "09:00", "minute": 540},
      {"category": "ri_gan_pian_cai", "label": "日干偏财时课", "shi_chen": "...", ...},
      ...
    ]
    """
    if today_date is None:
        today_date = date.today()

    if today_date.weekday() >= 5:
        return []

    gan, zhi, rizhu = calc_rizhu(today_date)
    schedule = []

    # ① 固定时辰课 — 09:00（巳时）
    schedule.append({
        "category": "fixed_time",
        "label": "固定时辰课",
        "shi_chen": "巳",
        "time": "09:00",
        "minute": 540,
        "ri_gan": gan,
        "ri_zhi": zhi,
        "rizhu": rizhu,
    })

    # ② 日干偏财时课
    cai_yao_gan = suggest_pian_cai_shichen_by_gan(gan)
    if cai_yao_gan["shichen_list"]:
        shi = cai_yao_gan["shichen_list"][0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_gan_pian_cai",
            "label": "日干偏财时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "subtype": cai_yao_gan["type"],
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ③ 日干食神时
    if shi_shen_shichen_by_gan := SHI_SHEN_SHI_BY_GAN.get(gan):
        shi = shi_shen_shichen_by_gan[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_gan_shi_shen",
            "label": "日干食神时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ④ 日干正印时
    if zheng_yin_by_gan := ZHENG_YIN_SHI_BY_GAN.get(gan):
        shi = zheng_yin_by_gan[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_gan_zheng_yin",
            "label": "日干正印时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑤ 日干偏印时
    if pian_yin_by_gan := PIAN_YIN_SHI_BY_GAN.get(gan):
        shi = pian_yin_by_gan[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_gan_pian_yin",
            "label": "日干偏印时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑥ 日支偏财时课（日支版）
    cai_yao_zhi = suggest_pian_cai_shichen_by_zhi(zhi)
    if cai_yao_zhi["shichen_list"]:
        shi = cai_yao_zhi["shichen_list"][0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_zhi_pian_cai",
            "label": "日支偏财时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "subtype": cai_yao_zhi["type"],
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑦ 日支食神时
    if shi_shen_by_zhi := SHI_SHEN_SHI_BY_ZHI.get(zhi):
        shi = shi_shen_by_zhi[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_zhi_shi_shen",
            "label": "日支食神时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑧ 日支正印时
    if zheng_yin_by_zhi := ZHENG_YIN_SHI_BY_ZHI.get(zhi):
        shi = zheng_yin_by_zhi[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_zhi_zheng_yin",
            "label": "日支正印时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑨ 日支偏印时
    if pian_yin_by_zhi := PIAN_YIN_SHI_BY_ZHI.get(zhi):
        shi = pian_yin_by_zhi[0]
        idx = DI_ZHI_IDX[shi]
        hour = idx * 2
        minute = hour * 60
        schedule.append({
            "category": "ri_zhi_pian_yin",
            "label": "日支偏印时",
            "shi_chen": shi,
            "time": f"{hour:02d}:{0:02d}",
            "minute": minute,
            "ri_gan": gan,
            "ri_zhi": zhi,
            "rizhu": rizhu,
        })

    # ⑩ 随机课 — 13:30~14:00 之间（未时）
    schedule.append({
        "category": "random",
        "label": "随机课",
        "shi_chen": "未",
        "time": "13:45",
        "minute": 825,
        "ri_gan": gan,
        "ri_zhi": zhi,
        "rizhu": rizhu,
    })

    return schedule


def get_category_for_minute(minute: int, today_date: date = None) -> str | None:
    """
    当前分钟数属于哪一类课（用于调度器判断时间窗口）
    """
    if today_date is None:
        today_date = date.today()
    schedule = get_today_schedule(today_date)
    for entry in schedule:
        cat_minute = entry["minute"]
        cat = entry["category"]
        if cat in ("fixed_time", "ri_gan_pian_cai", "ri_zhi_pian_cai", "ri_gan_shi_shen", "ri_zhi_shi_shen",
                    "ri_gan_zheng_yin", "ri_gan_pian_yin", "ri_zhi_zheng_yin", "ri_zhi_pian_yin", "random"):
            if cat_minute <= minute < cat_minute + 30:
                return cat
    return None


def is_weekday(dt: datetime) -> bool:
    return dt.weekday() < 5


def format_schedule(schedule: list[dict]) -> str:
    """格式化输出今天的排程"""
    lines = []
    lines.append("=" * 55)
    lines.append("  今日十一分类实验排程")
    lines.append("=" * 55)
    for entry in schedule:
        lines.append(f"  {entry['label']:<10}  {entry['shi_chen']}时  {entry['time']}")
    lines.append("=" * 55)
    return "\n".join(lines)


if __name__ == "__main__":
    from datetime import date
    today = date.today()
    gan, zhi, rizhu = calc_rizhu(today)

    print(f"今日日柱: {rizhu}  ({gan}干{zhi}支)")
    print()
    print("── 日干偏财时 ──")
    print(f"  偏财时(日干{gan}所克): {get_pian_cai_shichen_by_gan(gan)}")
    print(f"  食神时(日干{gan}所生异性): {get_shi_shen_shichen_by_gan(gan)}")
    cai_gan = suggest_pian_cai_shichen_by_gan(gan)
    print(f"  建议用: {cai_gan['label']} → {cai_gan['shichen_list']}")
    if cai_gan.get('fallback_reason'):
        print(f"  原因: {cai_gan['fallback_reason']}")

    print()
    print("── 日支偏财时 ──")
    print(f"  偏财时(日支{zhi}所克): {get_pian_cai_shichen_by_zhi(zhi)}")
    print(f"  食神时(日支{zhi}所生异性): {get_shi_shen_shichen_by_zhi(zhi)}")
    cai_zhi = suggest_pian_cai_shichen_by_zhi(zhi)
    print(f"  建议用: {cai_zhi['label']} → {cai_zhi['shichen_list']}")
    if cai_zhi.get('fallback_reason'):
        print(f"  原因: {cai_zhi['fallback_reason']}")

    print()
    print("── 日干正印时/偏印时 ──")
    print(f"  正印时(日干{gan}): {get_zheng_yin_shichen_by_gan(gan)}")
    print(f"  偏印时(日干{gan}): {get_pian_yin_shichen_by_gan(gan)}")
    print()
    print("── 日支正印时/偏印时 ──")
    print(f"  正印时(日支{zhi}): {get_zheng_yin_shichen_by_zhi(zhi)}")
    print(f"  偏印时(日支{zhi}): {get_pian_yin_shichen_by_zhi(zhi)}")

    print()
    schedule = get_today_schedule(today)
    print(format_schedule(schedule))
