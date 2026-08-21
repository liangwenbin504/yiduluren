# -*- coding: utf-8 -*-
"""
六壬 64 课经统一知识库（v1+v2 合并层）
============================================================
2026-08-21 憨爷：解决审计 #3 — 64 课体 v1/v2 冗余合并。

设计原则：
  1. 不破坏 v1 (`daliuren_64ke_rules.py` 的 KE_JING_64: base_score/xiang_yue/duanyu)
     与 v2 (`liuren_64ke_v2.py` 的 LIU_SHI_KETI: 宜忌/属相/从属格/判断要点) 现有结构。
  2. 本模块作为**统一入口**：合并两版字段，提供单一查询接口。
  3. 旧接口（v1 的 get_ke_jing_by_name / v2 的 get_keti_info）仍可直接使用，
     新代码应优先使用本模块的 `get_unified_keti` 等函数。

字段合并优先级（同名字段冲突时）：
  - base_score / 统卦 / xiang_yue / duanyu → 取 v1
  - 宜 / 忌 / 有利属相 / 注意属相 / 从属格 / 判断要点 / 卦象 → 取 v2
  - 吉凶 → 两者一致时取任一；冲突时取 v2（更细分等级）
"""
import os, sys, json
from typing import Dict, List, Tuple, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# ── 导入 v1 / v2 数据源 ──
try:
    from daliuren_64ke_rules import KE_JING_64 as _V1_KETI
    from daliuren_64ke_rules import (
        get_ke_jing_by_name as _v1_get,
        get_score_by_name as _v1_score,
        get_jixiong_by_name as _v1_jixiong,
        get_all_ke_names as _v1_names,
    )
    _HAS_V1 = True
except Exception:
    _V1_KETI = {}
    _HAS_V1 = False

try:
    from liuren_64ke_v2 import (
        LIU_SHI_KETI as _V2_KETI,
        SHANGJI_KETI as _V2_SHANGJI,
        ZHONGJI_KETI as _V2_ZHONGJI,
        XIAOJI_KETI as _V2_XIAOJI,
        PING_KETI as _V2_PING,
        XIAOXIONG_KETI as _V2_XIAOXIONG,
        ZHONGXIONG_KETI as _V2_ZHONGXIONG,
        DAXIONG_KETI as _V2_DAXIONG,
        get_keti_info as _v2_get,
        get_keti_level as _v2_level,
        get_all_keti_names as _v2_names,
        get_keti_by_level as _v2_by_level,
    )
    _HAS_V2 = True
except Exception:
    _V2_KETI = {}
    _HAS_V2 = False


# ============================================================================
# 名称归一化：v1 用 "元首课"（带后缀），v2 用 "元首"（不带后缀）
# 统一字典键采用 v1 风格（带"课"后缀），同时支持模糊查询
# ============================================================================

def _stem(name: str) -> str:
    """去掉末尾"课"字，返回词干"""
    return name[:-1] if name.endswith('课') and len(name) > 1 else name


def _with_ke_suffix(name: str) -> str:
    """确保末尾有"课"字"""
    return name if name.endswith('课') else name + '课'


# ============================================================================
# 构建合并字典 UNIFIED_64KE
#   键: v1 风格（带"课"后缀）
#   值: 合并字段（v1 + v2 + 分类等级 level_category）
# ============================================================================

# v2 等级分类映射（用于反查 level_category）
_V2_LEVEL_MAP = {
    'SHANGJI': '上吉',
    'ZHONGJI': '中吉',
    'XIAOJI': '小吉',
    'PING': '平',
    'XIAOXIONG': '小凶',
    'ZHONGXIONG': '中凶',
    'DAXIONG': '大凶',
}

# v1 的 jixiong 字段（更粗粒度：吉/平/凶/小凶 等）→ level_category 反推映射
# 用于 v1 独有课体（v2 没有对应条目，无法从 v2 取细分等级）
_V1_JIXIONG_TO_LEVEL = {
    '上吉': '上吉',
    '大吉': '上吉',
    '吉': '中吉',      # v1 单"吉"按 base_score 80 对应中吉
    '中吉': '中吉',
    '小吉': '小吉',
    '平': '平',
    '凶': '中凶',      # v1 单"凶"按 base_score 30 对应中凶
    '小凶': '小凶',
    '中凶': '中凶',
    '大凶': '大凶',
}

# ============================================================================
# 缺口补全：v1/v2 都未提供从属格/宜/忌/属相的课体，按 jixiong/统卦 反推
# 设计原则：
#   1. 不编造古籍不存在的细节，仅按 jixiong 等级和统卦五行推断
#   2. 从属格只补"本课"一条（条件=definition，吉凶=jixiong），不臆造变格
#   3. 宜/忌 按 jixiong 等级反推（吉课宜吉事、凶课忌吉事等通用规则）
#   4. 属相按统卦五行推断（卦气→地支属相）
# ============================================================================

# 按 jixiong 反推宜/忌
_JIXIONG_TO_YIJI = {
    '上吉': (['上任', '考试', '婚嫁', '求财', '搬家', '开业', '出行', '诉讼'], []),
    '大吉': (['上任', '考试', '婚嫁', '求财', '搬家', '开业', '出行', '诉讼'], []),
    '中吉': (['上任', '婚嫁', '求财', '搬家', '开业', '出行'], ['征战']),
    '吉':   (['上任', '婚嫁', '求财', '搬家', '开业', '出行'], ['征战']),
    '小吉': (['婚嫁', '求财', '搬家', '出行', '谋望'], ['诉讼', '征战']),
    '平':   (['谋望', '出行', '搬家'], ['大谋', '征战', '上任']),
    '小凶': (['守静', '避祸', '拆分', '谨慎小事'], ['婚嫁', '上任', '求财', '出行', '开业', '征战']),
    '凶':   (['守静', '避祸', '拆分', '决断', '刑狱'], ['婚嫁', '上任', '求财', '出行', '开业', '合作', '谋望']),
    '中凶': (['守静', '避祸', '拆分', '决断', '刑狱'], ['婚嫁', '上任', '求财', '出行', '开业', '合作', '谋望']),
    '大凶': (['守静', '避难', '拆分', '慎独', '丧葬'], ['婚嫁', '上任', '求财', '出行', '开业', '合作', '谋望', '征战', '建宅']),
}

# 统卦（八卦）→ 五行 → 有利属相 / 注意属相
# 原则：卦气五行所生属相为有利，所克属相为注意
_GUA_WX = {
    '乾': '金', '兑': '金',
    '震': '木', '巽': '木',
    '坎': '水',
    '离': '火',
    '坤': '土', '艮': '土',
}
# 64 卦 → 八宫五行映射（按《京房易》八宫归属，宫位五行即卦的五行）
# 用于 v1 统卦非 8 卦时的属相推断；八宫每宫 8 卦
_GUA64_WX = {
    # 乾宫（金）
    '乾': '金', '姤': '金', '遁': '金', '否': '金', '观': '金', '剥': '金', '晋': '金', '大有': '金',
    # 兑宫（金）
    '兑': '金', '困': '金', '萃': '金', '咸': '金', '蹇': '金', '谦': '金', '小过': '金', '归妹': '金',
    # 离宫（火）
    '离': '火', '旅': '火', '鼎': '火', '未济': '火', '蒙': '火', '涣': '火', '讼': '火', '同人': '火',
    # 震宫（木）
    '震': '木', '豫': '木', '解': '木', '恒': '木', '升': '木', '井': '木', '大过': '木', '随': '木',
    # 巽宫（木）
    '巽': '木', '小畜': '木', '家人': '木', '益': '木', '无妄': '木', '噬嗑': '木', '颐': '木', '蛊': '木',
    # 坎宫（水）
    '坎': '水', '节': '水', '屯': '水', '既济': '水', '革': '水', '丰': '水', '明夷': '水', '师': '水',
    # 艮宫（土）
    '艮': '土', '贲': '土', '大畜': '土', '损': '土', '睽': '土', '履': '土', '中孚': '土', '渐': '土',
    # 坤宫（土）
    '坤': '土', '复': '土', '临': '土', '泰': '土', '大壮': '土', '夬': '土', '需': '土', '比': '土',
}
# 五行→属相映射（属相地支五行）
_ZHI_WX = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
    '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
    '戌': '土', '亥': '水',
}
_ZHI_TO_SHENGXIAO = {
    '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔', '辰': '龙', '巳': '蛇',
    '午': '马', '未': '羊', '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪',
}
_WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
_WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def _sx_from_wx(wx: str) -> tuple:
    """按五行推断有利属相（生我/同我）与注意属相（我克/克我）"""
    if not wx:
        return [], []
    youli = []  # 有利：同五行 + 生我之五行
    zhuyi = []  # 注意：我克 + 克我之五行
    sheng_wo = next((w for w, v in _WX_SHENG.items() if v == wx), '')  # 生我者
    for zhi, zhi_wx in _ZHI_WX.items():
        sx = _ZHI_TO_SHENGXIAO[zhi]
        if zhi_wx == wx or zhi_wx == sheng_wo:
            if sx not in youli:
                youli.append(sx)
        elif zhi_wx == _WX_KE[wx] or zhi_wx == _WX_SHENG[wx]:
            # 我克（财）+ 我生（泄气）列为注意
            if sx not in zhuyi:
                zhuyi.append(sx)
    return youli, zhuyi


def _infer_yiji(jixiong: str) -> tuple:
    """按 jixiong 等级推断宜/忌；处理带括号修饰的 jixiong（如"平（守成为宜）"）"""
    if not jixiong:
        return [], []
    # 提取首词（去括号修饰）：如"平（守成为宜）"→"平"，"上吉"→"上吉"
    core = jixiong.split('（')[0].split('(')[0].strip()
    return _JIXIONG_TO_YIJI.get(core) or _JIXIONG_TO_YIJI.get(jixiong, ([], []))


def _infer_sx(tonggua: str) -> tuple:
    """按统卦推断属相；支持 8 卦与 64 卦（按京房八宫五行）"""
    if not tonggua:
        return [], []
    wx = _GUA_WX.get(tonggua) or _GUA64_WX.get(tonggua)
    return _sx_from_wx(wx)


def _build_unified() -> Dict[str, Dict]:
    """构建合并后的统一字典"""
    unified: Dict[str, Dict] = {}

    # 第一遍：灌入 v1 全部课体（基础字段）
    if _HAS_V1:
        for name, info in _V1_KETI.items():
            key = name  # v1 已带"课"后缀
            unified[key] = {
                '名称': key,
                'base_score': info.get('base_score', 50),
                '吉凶': info.get('jixiong', '平'),
                '统卦': info.get('统卦', ''),
                'definition': info.get('definition', ''),
                'xiang_yue': info.get('xiang_yue', ''),
                'duanyu': info.get('duanyu', ''),
                'level_category': '',  # 待第二遍填入
                '来源': ['v1'],
            }

    # 第二遍：合并 v2 字段（按词干匹配）
    if _HAS_V2:
        # 先构建 v2 词干索引
        v2_by_stem: Dict[str, Tuple[str, Dict, str]] = {}
        for cat_name, cat_dict in [
            ('SHANGJI', _V2_SHANGJI), ('ZHONGJI', _V2_ZHONGJI),
            ('XIAOJI', _V2_XIAOJI), ('PING', _V2_PING),
            ('XIAOXIONG', _V2_XIAOXIONG), ('ZHONGXIONG', _V2_ZHONGXIONG),
            ('DAXIONG', _V2_DAXIONG),
        ]:
            for k, v in cat_dict.items():
                v2_by_stem[_stem(k)] = (k, v, cat_name)

        # 合并到已有 v1 条目
        for key, entry in unified.items():
            stem = _stem(key)
            if stem in v2_by_stem:
                v2_key, v2_info, cat_name = v2_by_stem[stem]
                # v2 独有字段
                for f in ['卦象', '主象', '判断要点', '宜', '忌',
                          '有利属相', '注意属相', '从属格']:
                    if f in v2_info:
                        entry[f] = v2_info[f]
                # 同名字段冲突：取 v2 的吉凶（更细分）
                if '吉凶' in v2_info:
                    entry['吉凶'] = v2_info['吉凶']
                # 统卦：v1 优先，v1 空则取 v2
                if not entry.get('统卦') and v2_info.get('统卦'):
                    entry['统卦'] = v2_info['统卦']
                # 象曰：v1 xiang_yue 优先，v1 空则取 v2 象曰
                if not entry.get('xiang_yue') and v2_info.get('象曰'):
                    entry['xiang_yue'] = v2_info['象曰']
                # definition：v1 优先，v1 空则取 v2 定义
                if not entry.get('definition') and v2_info.get('定义'):
                    entry['definition'] = v2_info['定义']
                entry['level_category'] = _V2_LEVEL_MAP.get(cat_name, '')
                entry['来源'].append('v2')
                # 标记已合并
                v2_by_stem[stem] = None  # type: ignore

        # 第二遍半：对仍缺 level_category 的 v1 独有课体，按 v1 jixiong 反推
        # （v2 没有对应条目，无法从 v2 取细分等级，只能按 v1 的 jixiong 推断）
        for key, entry in unified.items():
            if not entry.get('level_category'):
                v1_jixiong = entry.get('吉凶', '平')
                entry['level_category'] = _V1_JIXIONG_TO_LEVEL.get(v1_jixiong, '平')

        # 第三遍：补入 v2 独有（v1 没有的）课体
        # v2 独有课体的 base_score 按等级推断
        _LEVEL_BASE_SCORE = {
            '上吉': 95, '中吉': 80, '小吉': 70, '吉': 80,
            '平': 50, '小凶': 30, '中凶': 20, '大凶': 10,
        }
        for stem, item in v2_by_stem.items():
            if item is None:
                continue  # 已合并
            v2_key, v2_info, cat_name = item
            key = _with_ke_suffix(v2_key) if not v2_key.endswith('课') else v2_key
            jixiong = v2_info.get('吉凶', _V2_LEVEL_MAP.get(cat_name, '平'))
            entry = {
                '名称': key,
                'base_score': _LEVEL_BASE_SCORE.get(jixiong, 50),
                '吉凶': jixiong,
                '统卦': v2_info.get('统卦', ''),
                'definition': v2_info.get('定义', ''),
                'xiang_yue': v2_info.get('象曰', ''),
                'duanyu': '',
                'level_category': _V2_LEVEL_MAP.get(cat_name, ''),
                '来源': ['v2'],
            }
            for f in ['卦象', '主象', '判断要点', '宜', '忌',
                      '有利属相', '注意属相', '从属格']:
                if f in v2_info:
                    entry[f] = v2_info[f]
            unified[key] = entry

    # 第四遍：缺口补全 — 对仍缺从属格/宜/忌/属相 的课体，按 jixiong/统卦 反推
    # 设计原则：不编造古籍细节，仅按等级与卦气推断；标注来源为 "推断"
    for key, entry in unified.items():
        jixiong = entry.get('吉凶', '平')
        tonggua = entry.get('统卦', '')
        # 从属格：仅补"本课"一条（条件=definition，吉凶=jixiong）
        if not entry.get('从属格'):
            stem_name = _stem(key)  # "元首课" → "元首"
            entry['从属格'] = {
                f'{stem_name}本课': {
                    '吉凶': jixiong,
                    '条件': entry.get('definition', ''),
                }
            }
            entry.setdefault('来源', []).append('推断·从属格')
        # 宜/忌：按 jixiong 等级反推；上吉/大吉课忌确实为空（吉课无禁忌），接受空
        yi, ji = _infer_yiji(jixiong)
        if not entry.get('宜') and yi:
            entry['宜'] = yi
            if '推断·宜' not in entry.get('来源', []):
                entry['来源'].append('推断·宜')
        # 忌：仅在 jixiong 不属于"上吉/大吉"且 ji 非空时补全
        if not entry.get('忌') and ji:
            entry['忌'] = ji
            if '推断·忌' not in entry.get('来源', []):
                entry['来源'].append('推断·忌')
        # 有利属相/注意属相：按统卦五行推断（统卦为空则不补，避免无依据）
        youli, zhuyi = _infer_sx(tonggua)
        if not entry.get('有利属相') and youli:
            entry['有利属相'] = youli
            if '推断·属相' not in entry.get('来源', []):
                entry['来源'].append('推断·属相')
        if not entry.get('注意属相') and zhuyi:
            entry['注意属相'] = zhuyi
            if '推断·属相' not in entry.get('来源', []):
                entry['来源'].append('推断·属相')

    return unified


# ============================================================================
# 统一字典与查询函数
# ============================================================================

_JSON_PATH = os.path.join(BASE, '..', 'data', 'unified_64ke.json')

def _load_from_json() -> Optional[Dict[str, Dict]]:
    """从 data/unified_64ke.json 加载合并后的课体数据（单一数据源）。
    JSON 为 v1+v2 合并后的冻结快照，避免运行时依赖 v1/v2 源文件。
    """
    if not os.path.exists(_JSON_PATH):
        return None
    try:
        with open(_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ketis = data.get('ketis', {})
        return ketis if ketis else None
    except Exception:
        return None

# 优先从 JSON（单一数据源）加载；JSON 不存在或加载失败时回退到 v1/v2 构建
_json_data = _load_from_json()
if _json_data:
    UNIFIED_64KE: Dict[str, Dict] = _json_data
    _DATA_SOURCE = 'json'
else:
    UNIFIED_64KE: Dict[str, Dict] = _build_unified()
    _DATA_SOURCE = 'v1+v2_fallback'


def get_unified_keti(name: str) -> Dict:
    """
    通用查询：按课体名称获取合并后的全部字段。
    支持模糊匹配：先精确 → 去后缀 → 子串包含。
    """
    if not name:
        return {}
    # 1. 精确匹配
    if name in UNIFIED_64KE:
        return UNIFIED_64KE[name]
    # 2. 去后缀匹配
    stem = _stem(name)
    key_with_suffix = _with_ke_suffix(name)
    if key_with_suffix in UNIFIED_64KE:
        return UNIFIED_64KE[key_with_suffix]
    if stem in UNIFIED_64KE:
        return UNIFIED_64KE[stem]
    # 3. 子串包含
    for k, v in UNIFIED_64KE.items():
        k_stem = _stem(k)
        if k_stem == stem or stem in k_stem or k_stem in stem:
            return v
    return {}


def get_score(name: str) -> int:
    """获取课体的 base_score（0-100）"""
    info = get_unified_keti(name)
    if not info:
        # 回退到 v1 原始函数
        if _HAS_V1:
            return _v1_score(name)
        return 50
    return info.get('base_score', 50)


def get_jixiong(name: str) -> str:
    """获取课体的吉凶等级（上吉/中吉/小吉/吉/平/小凶/中凶/大凶）"""
    info = get_unified_keti(name)
    if not info:
        if _HAS_V1:
            return _v1_jixiong(name)
        return '平'
    return info.get('吉凶', '平')


def get_level(name: str) -> Tuple[str, int, bool]:
    """
    获取等级与扣分（兼容 v2 接口）
    返回: (等级名, 扣分数, 是否大凶课)
    """
    info = get_unified_keti(name)
    level = info.get('吉凶', '平') if info else '平'
    level_map = {
        '上吉': (0, False), '大吉': (0, False),
        '中吉': (0, False), '小吉': (5, False),
        '吉': (5, False), '平': (10, False),
        '凶': (15, False), '小凶': (20, False),
        '中凶': (30, False), '大凶': (40, True),
    }
    if level in level_map:
        deduction, is_daxiong = level_map[level]
        return level, deduction, is_daxiong
    return '普通课', 10, False


def get_all_keti_names() -> List[str]:
    """获取全部课体名称（统一后）"""
    return list(UNIFIED_64KE.keys())


def get_keti_count() -> int:
    """获取课体总数"""
    return len(UNIFIED_64KE)


def get_by_level(level: str) -> Dict[str, Dict]:
    """按吉凶等级筛选课体"""
    return {k: v for k, v in UNIFIED_64KE.items() if v.get('吉凶') == level}


def get_by_category(category: str) -> Dict[str, Dict]:
    """按 v2 分类等级筛选（上吉/中吉/小吉/平/小凶/中凶/大凶）"""
    return {k: v for k, v in UNIFIED_64KE.items()
            if v.get('level_category') == category}


def get_subordinate_patterns(name: str) -> Dict:
    """获取课体的从属格（变格）"""
    info = get_unified_keti(name)
    return info.get('从属格', {}) if info else {}


def get_yi(name: str) -> List[str]:
    """获取课体的'宜'列表"""
    info = get_unified_keti(name)
    return info.get('宜', []) if info else []


def get_ji(name: str) -> List[str]:
    """获取课体的'忌'列表"""
    info = get_unified_keti(name)
    return info.get('忌', []) if info else []


# ============================================================================
# 来源统计（供审计用）
# ============================================================================

def get_source_stats() -> Dict:
    """统计 v1/v2/合并 覆盖情况"""
    only_v1 = [k for k, v in UNIFIED_64KE.items() if v['来源'] == ['v1']]
    only_v2 = [k for k, v in UNIFIED_64KE.items() if v['来源'] == ['v2']]
    both = [k for k, v in UNIFIED_64KE.items() if len(v['来源']) >= 2]
    return {
        '总课体数': len(UNIFIED_64KE),
        '数据源': _DATA_SOURCE,
        'v1_only': len(only_v1),
        'v2_only': len(only_v2),
        '合并(v1+v2)': len(both),
        'v1_only_list': only_v1,
        'v2_only_list': only_v2,
    }


# ============================================================================
# 自检（直接运行时打印统计）
# ============================================================================

if __name__ == '__main__':
    stats = get_source_stats()
    print(f"== 64 课经统一库自检 ==")
    print(f"数据源: {stats['数据源']}")
    print(f"总课体数: {stats['总课体数']}")
    print(f"v1 独有: {stats['v1_only']} 条 → {stats['v1_only_list']}")
    print(f"v2 独有: {stats['v2_only']} 条 → {stats['v2_only_list']}")
    print(f"v1+v2 合并: {stats['合并(v1+v2)']} 条")
    # 抽样检查
    for sample in ['元首课', '重审课', '三光课', '进连茹课', '天罗地网课']:
        info = get_unified_keti(sample)
        if info:
            fields = list(info.keys())
            print(f"\n[{sample}] 字段: {fields}")
            print(f"  base_score={info.get('base_score')}, 吉凶={info.get('吉凶')}, "
                  f"level_category={info.get('level_category')}, 来源={info.get('来源')}")
            if '从属格' in info:
                print(f"  从属格数: {len(info['从属格'])}")
            if '宜' in info:
                print(f"  宜: {info['宜']}")
