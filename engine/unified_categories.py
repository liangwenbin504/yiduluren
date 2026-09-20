"""
三大占事分类体系统一交叉映射模块

统一 19 分类方案：
- A. shishi_duanfa_learner (16种)
- B. duanan_knowledge_base (20种)
- C. liuren_training_knowledge (17种)

功能：
1. 任意分类名 → 统一分类
2. 统一分类 → 三系统各自对应名称
3. 查询某系统支持哪些统一分类
"""

UNIFIED_CATEGORIES = {
    "天时": {
        "id": "tianshi",
        "description": "天气气候变化占卜",
        "mapping": {
            "A": ["天时"],
            "B": ["天时"],
            "C": ["天时"],
        },
    },
    "股市投资": {
        "id": "gushi_touzi",
        "description": "股票、基金等金融投资预测",
        "mapping": {
            "A": [],
            "B": [],
            "C": ["求财"],
        },
    },
    "宅墓田宅": {
        "id": "zhaimu_tianzhai",
        "description": "阳宅阴宅、田产家宅",
        "mapping": {
            "A": ["宅墓"],
            "B": ["宅墓"],
            "C": ["田宅"],
        },
    },
    "前程仕进": {
        "id": "qiancheng_shijin",
        "description": "功名仕途、考试晋升",
        "mapping": {
            "A": ["前程"],
            "B": ["前程仕进"],
            "C": ["考试"],
        },
    },
    "终身": {
        "id": "zhongshen",
        "description": "终身命运、一生休咎",
        "mapping": {
            "A": ["终身"],
            "B": ["终身"],
            "C": ["终身"],
        },
    },
    "流年": {
        "id": "liunian",
        "description": "一年运势、年度吉凶",
        "mapping": {
            "A": ["流年"],
            "B": ["流年"],
            "C": ["流年"],
        },
    },
    "婚姻": {
        "id": "hunyin",
        "description": "婚姻感情、配偶缘分",
        "mapping": {
            "A": ["婚姻"],
            "B": ["婚姻"],
            "C": ["婚姻"],
        },
    },
    "胎产子息": {
        "id": "taichan_zixi",
        "description": "怀孕生产、子孙后代",
        "mapping": {
            "A": ["胎产"],
            "B": ["子息胎产"],
            "C": [],
        },
    },
    "求财交易": {
        "id": "qiucai_jiaoyi",
        "description": "求财谋利、买卖交易、经营事业",
        "mapping": {
            "A": ["财产", "交易"],
            "B": ["求财", "谋望买卖", "趋谒干求"],
            "C": ["求财", "交易", "经营"],
        },
    },
    "出行": {
        "id": "chuxing",
        "description": "出行远游、旅途平安",
        "mapping": {
            "A": ["出行"],
            "B": ["出行"],
            "C": ["出行"],
        },
    },
    "行人音信": {
        "id": "xingren_yinxin",
        "description": "行人归来、音信消息",
        "mapping": {
            "A": ["行人音信"],
            "B": ["行人", "觅访"],
            "C": ["行人"],
        },
    },
    "疾病": {
        "id": "jibing",
        "description": "疾病健康、医药治疗",
        "mapping": {
            "A": ["疾病"],
            "B": ["疾病"],
            "C": ["疾病"],
        },
    },
    "六畜": {
        "id": "liuchu",
        "description": "家畜动物、养殖",
        "mapping": {
            "A": ["六畜"],
            "B": ["六畜"],
            "C": [],
        },
    },
    "失物亡盗": {
        "id": "shiwu_wangdao",
        "description": "失物寻找、逃亡缉捕、盗贼偷窃",
        "mapping": {
            "A": ["亡盗"],
            "B": ["逃亡", "盗贼"],
            "C": ["失物"],
        },
    },
    "官讼词讼": {
        "id": "guansong_cisong",
        "description": "官司诉讼、纠纷调解",
        "mapping": {
            "A": ["官讼"],
            "B": ["词讼"],
            "C": ["官讼"],
        },
    },
    "一课二事各断式": {
        "id": "yike_ershi",
        "description": "一课占多事各断",
        "mapping": {
            "A": [],
            "B": ["一课二事各断式"],
            "C": [],
        },
    },
    "开业经营": {
        "id": "kaiye_jingying",
        "description": "开业开市、商业经营",
        "mapping": {
            "A": [],
            "B": [],
            "C": ["开业", "经营"],
        },
    },
    "安葬": {
        "id": "anzang",
        "description": "安葬事宜、阴宅风水",
        "mapping": {
            "A": [],
            "B": [],
            "C": ["安葬"],
        },
    },
    "杂占": {
        "id": "zazhan",
        "description": "杂项杂占",
        "mapping": {
            "A": ["杂占"],
            "B": ["杂占"],
            "C": [],
        },
    },
    "其他": {
        "id": "qita",
        "description": "其他未分类占事",
        "mapping": {
            "A": [],
            "B": [],
            "C": ["其他"],
        },
    },
}

SYSTEM_NAMES = {
    "A": "shishi_duanfa_learner",
    "B": "duanan_knowledge_base",
    "C": "liuren_training_knowledge",
}

SYSTEM_CATEGORY_COUNTS = {"A": 16, "B": 20, "C": 17}


def to_unified(source_system: str, original_name: str) -> str:
    """将某系统的原始分类名映射为统一分类名"""
    for unified_name, info in UNIFIED_CATEGORIES.items():
        if original_name in info["mapping"].get(source_system, []):
            return unified_name
    return "其他"


def from_unified(unified_name: str, target_system: str) -> list:
    """将统一分类名映射到某系统的原始分类名列表"""
    info = UNIFIED_CATEGORIES.get(unified_name)
    if not info:
        return []
    return info["mapping"].get(target_system, [])


def get_supported(target_system: str) -> list:
    """获取某系统支持的所有统一分类名"""
    supported = []
    for unified_name, info in UNIFIED_CATEGORIES.items():
        if info["mapping"].get(target_system, []):
            supported.append(unified_name)
    return supported


def get_all_unified() -> list:
    """获取所有统一分类名"""
    return list(UNIFIED_CATEGORIES.keys())


def get_unified_info(unified_name: str) -> dict:
    """获取统一分类详情"""
    return UNIFIED_CATEGORIES.get(unified_name, {})


def generate_cross_reference_table() -> str:
    """生成交叉引用文本表（供AI提示词/文档使用）"""
    lines = []
    lines.append("=" * 100)
    lines.append("三大占事分类体系统一映射表")
    lines.append("=" * 100)
    lines.append(
        f"{'统一分类':<14} {'A.断法学习器(16)':<28} {'B.断案知识库(20)':<28} {'C.训练知识库(17)':<28}"
    )
    lines.append("-" * 100)
    for unified_name, info in UNIFIED_CATEGORIES.items():
        a_names = ", ".join(info["mapping"]["A"]) or "—"
        b_names = ", ".join(info["mapping"]["B"]) or "—"
        c_names = ", ".join(info["mapping"]["C"]) or "—"
        lines.append(f"{unified_name:<14} {a_names:<28} {b_names:<28} {c_names:<28}")
    lines.append("=" * 100)
    lines.append(f"统一分类数: {len(UNIFIED_CATEGORIES)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_cross_reference_table())

    print("\n\n各系统支持的统一分类:")
    for sys_key, sys_name in SYSTEM_NAMES.items():
        supported = get_supported(sys_key)
        print(f"  {sys_name}: {len(supported)}种 → {supported}")
