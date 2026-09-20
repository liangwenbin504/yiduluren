#!/usr/bin/env python3
"""
昼夜贵人计算模块 — 基于真太阳时 + 节气 + 经纬度

六壬贵神规则:
  甲戊庚牛羊, 乙己鼠猴乡, 丙丁猪鸡位, 壬癸兔蛇藏, 六辛逢马虎
  昼贵顺行(巳→午→未→...), 夜贵逆行(巳→辰→卯→...)
  
  昼夜分界: 日落时刻(非固定时辰!)
            夏季酉时可能为昼, 冬季酉时可能为夜
            以真太阳时+地理经纬度计算

关系图:
  gui_ren_daynight.py ← 本模块(核心)
    ├──→ gui_ren_engine.py (GuiRenCalculator — 调用本模块获取昼夜判断)
    ├──→ stock_daily_predict.py (SYSTEM_PROMPT — 引用贵神规则知识)
    ├──→ stock_dashboard.py (API — 返回天将数据给前端)
    └──→ stock_dashboard.html (前端JS — 用本模块逻辑显示天将)
"""

import math
from datetime import date, datetime, timedelta

# === 基础常量 ===

# 贵人歌诀: 日干→(昼贵, 夜贵)

# === 安龙县全年日落表(25.1N,105.5E) ===
#  1月:18:06  2月:18:18  3月:18:43  4月:19:15
#  5月:19:38  6月:19:44  7月:19:34  8月:19:20
#  9月:19:07 10月:18:54 11月:18:35 12月:18:15
#  4-9月酉时全昼 | 10-3月酉时跨昼夜

GUI_REN = {
    '甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
    '乙': ('子', '申'), '己': ('子', '申'),
    '丙': ('亥', '酉'), '丁': ('亥', '酉'),
    '壬': ('巳', '卯'), '癸': ('巳', '卯'),
    '辛': ('午', '寅'),
}

# 12天将顺序
TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
              '天空', '白虎', '太常', '玄武', '太阴', '天后']

# 地支
ZHI = '子丑寅卯辰巳午未申酉戌亥'

# 时辰→小时映射(北京时间)
SHI_CHEN_HOUR = {
    '子': 23, '丑': 1, '寅': 3, '卯': 5, '辰': 7,
    '巳': 9, '午': 11, '未': 13, '申': 15, '酉': 17, '戌': 19, '亥': 21
}


# === 真太阳时日落计算 ===

def calc_sunset_hour(lat=25.1, lon=105.5, d=None):
    """
    计算日落时刻(北京时间小数)
    lat: 纬度(度), 默认安龙县25.1
    lon: 经度(度), 默认安龙县105.5
    d: 日期, 默认今天
    """
    if d is None:
        d = date.today()
    
    doy = d.timetuple().tm_yday
    
    # 太阳赤纬(度)
    decl_deg = 23.45 * math.sin(math.radians(360.0 / 365 * (284 + doy)))
    decl = math.radians(decl_deg)
    
    # 半天弧长(小时) — 从正午到日落
    lat_rad = math.radians(lat)
    cosH = -math.tan(lat_rad) * math.tan(decl)
    cosH = max(-1.0, min(1.0, cosH))
    halfday = math.degrees(math.acos(cosH)) / 15.0
    
    # 均时差(分钟) — Equation of Time
    B = math.radians(360.0 / 365 * (doy - 81))
    eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    
    # 真太阳时正午(分钟,北京时间)
    # 标准子午线120°E, 每1°经度差=4分钟时差
    noon_local = 12 * 60 + 4 * (120 - lon) + eot
    
    # 日落 = 正午 + 半天弧长
    sunset_min = noon_local + halfday * 60
    return sunset_min / 60.0


def calc_sunrise_hour(lat=25.1, lon=105.5, d=None):
    """
    计算日出时刻(北京时间小数)
    lat/lon/d 同 calc_sunset_hour
    """
    if d is None:
        d = date.today()
    doy = d.timetuple().tm_yday
    decl_deg = 23.45 * math.sin(math.radians(360.0 / 365 * (284 + doy)))
    decl = math.radians(decl_deg)
    lat_rad = math.radians(lat)
    cosH = -math.tan(lat_rad) * math.tan(decl)
    cosH = max(-1.0, min(1.0, cosH))
    halfday = math.degrees(math.acos(cosH)) / 15.0
    B = math.radians(360.0 / 365 * (doy - 81))
    eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    noon_local = 12 * 60 + 4 * (120 - lon) + eot
    sunrise_min = noon_local - halfday * 60
    return sunrise_min / 60.0


def is_daytime(shi_chen_or_hour, minute=0, lat=25.1, lon=105.5, d=None):
    """
    判断当前时刻是否为昼(精确到分钟)
    
    用法:
      is_daytime('酉') → 以酉时起始17:00判断
      is_daytime('酉', 5) → 17:05判断
      is_daytime(17, 5) → 17:05判断
      is_daytime(19, 33) → 19:33判断
    
    返回: True=昼(日未落), False=夜(日已落)
    """
    if d is None:
        d = date.today()
    
    sunrise_h = calc_sunrise_hour(lat, lon, d)
    sunset_h = calc_sunset_hour(lat, lon, d)
    
    # 解析输入时间
    if isinstance(shi_chen_or_hour, str):
        sc_h = SHI_CHEN_HOUR.get(shi_chen_or_hour, 12)
    else:
        sc_h = shi_chen_or_hour
    
    now = sc_h + minute / 60.0  # 当前时刻(小时小数)
    if now < 0:
        now += 24
    
    return sunrise_h <= now < sunset_h  # 日出后、日落前 = 昼


# === 贵神盘计算 ===

def get_gui_ren_pan(ri_gan, shi_chen, minute=0, lat=25.1, lon=105.5, d=None):
    """
    计算贵神天将盘
    ri_gan: 日干 '甲'~'癸'
    shi_chen: 时辰地支
    lat/lon: 经纬度
    返回: {地支: 天将, ...}
    """
    if d is None:
        d = date.today()
    
    gui = GUI_REN.get(ri_gan, ('丑', '未'))
    yang_gui = gui[0]; yin_gui = gui[1]  # 阳贵/阴贵本始
    
    day_time = is_daytime(shi_chen, minute, lat, lon, d)
    
    # 昼夜翻转阴阳: 昼→阳贵=歌诀前者, 夜→阳贵=歌诀后者
    start_zhi = yang_gui if day_time else yin_gui
    gi = ZHI.index(start_zhi)
    
    # 顺逆看阳贵人落宫: 巳午未申酉戌→逆排, 亥子丑寅卯辰→顺排
    ni_pai = start_zhi in '巳午未申酉戌'
    
    pan = {}
    for i in range(12):
        if ni_pai:
            di = ZHI[(gi + 12 - i) % 12]   # 逆排
        else:
            di = ZHI[(gi + i) % 12]        # 顺排
        pan[di] = TIAN_JIANG[i]
    
    return pan


def get_tianjiang_for_dizhi(ri_gan, shi_chen, target_zhi, lat=25.1, lon=105.5, d=None):
    """查询特定地支的天将"""
    pan = get_gui_ren_pan(ri_gan, shi_chen, minute, lat, lon, d)
    return pan.get(target_zhi, '')


def get_tianjiang_for_sanchuan(ri_gan, shi_chen, sanchuan, minute=0, lat=25.1, lon=105.5, d=None):
    """查询三传各支的天将"""
    pan = get_gui_ren_pan(ri_gan, shi_chen, minute, lat, lon, d)
    return {dz: pan.get(dz, '') for dz in sanchuan}


def get_tianjiang_for_sike(ri_gan, shi_chen, sike, minute=0, lat=25.1, lon=105.5, d=None):
    """查询四课上神的天将"""
    pan = get_gui_ren_pan(ri_gan, shi_chen, minute, lat, lon, d)
    result = {}
    for sk in sike:
        # sike格式: [课名, 上神, 下神] or dict with 'top' key
        if isinstance(sk, dict):
            up = sk.get('top', sk.get('shangshen', ''))
        elif isinstance(sk, (list, tuple)):
            up = sk[1] if len(sk) > 1 else ''
        else:
            up = ''
        result[up] = pan.get(up, '')
    return result


# === 日落调试信息 ===

def get_sunset_info(lat=25.1, lon=105.5, d=None):
    """返回日落详细信息的字典"""
    if d is None:
        d = date.today()
    
    doy = d.timetuple().tm_yday
    sunset_h = calc_sunset_hour(lat, lon, d)
    h = int(sunset_h)
    m = int((sunset_h - h) * 60)
    
    offset_min = int(4 * (120 - lon))  # 真太阳时偏移
    
    day_sc = []
    night_sc = []
    for sc in ZHI:
        if is_daytime(sc, lat, lon, d):
            day_sc.append(sc)
        else:
            night_sc.append(sc)
    
    return {
        'date': d.isoformat(),
        'doy': doy,
        'lat': lat,
        'lon': lon,
        'sunset': f'{h:02d}:{m:02d}',
        'sunset_hour': round(sunset_h, 2),
        'solar_offset_min': offset_min,
        'day_shichen': ''.join(day_sc),
        'night_shichen': ''.join(night_sc),
    }


# === 测试 ===

if __name__ == '__main__':
    # 基本信息
    info = get_sunset_info(25.1, 105.5)
    print(f"安龙县日落信息:")
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    print()
    print("=== 时辰昼夜 ===")
    for sc in '卯辰巳午未申酉戌亥子丑寅':
        day = is_daytime(sc, 25.1, 105.5)
        sc_h = SHI_CHEN_HOUR[sc]
        print(f"  {sc}时({sc_h:02d}-{(sc_h+2)%24:02d}) {'☀昼' if day else '🌙夜'}")
    
    print()
    print("=== 贵神盘示例(乙日酉时) ===")
    pan = get_gui_ren_pan('乙', '酉', 25.1, 105.5)
    for di in '子丑寅卯辰巳午未申酉戌亥':
        print(f"  {di}→{pan.get(di,'')}")
    
    print()
    print("=== 三传天将(乙日酉时, 巳丑酉) ===")
    tj = get_tianjiang_for_sanchuan('乙', '酉', ['巳', '丑', '酉'], 25.1, 105.5)
    print(f"  {tj}")
