# -*- coding: utf-8 -*-
"""
大六壬课格匹配系统 v3
支持一课多格的交叉匹配
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 十三吉课定义
SHISAN_JI_KE = {
    "龙德课": {"score": 95, "level": "上吉", "core_condition": "太岁=月将乘贵人发用"},
    "斫轮课": {"score": 92, "level": "上吉", "core_condition": "卯临庚辛申酉发用"},
    "轩盖课": {"score": 90, "level": "上吉", "core_condition": "正七月午发用，三传午卯子"},
    "铸印课": {"score": 88, "level": "上吉", "core_condition": "戌加巳入传，三传巳戌卯"},
    "合欢课": {"score": 86, "level": "上吉", "core_condition": "干支合+三传合+年命吉将"},
    "合美课": {"score": 84, "level": "上吉", "core_condition": "干支递合或互合"},
    "繁昌课": {"score": 82, "level": "中吉", "core_condition": "三传皆旺相有气"},
    "富贵课": {"score": 80, "level": "中吉", "core_condition": "贵人乘旺相临日辰发用"},
    "时泰课": {"score": 78, "level": "中吉", "core_condition": "太岁月建乘青龙六合发用"},
    "亨通课": {"score": 76, "level": "中吉", "core_condition": "三传递生日干"},
    "荣华课": {"score": 74, "level": "中吉", "core_condition": "禄马贵人临干支发用"},
    "官爵课": {"score": 72, "level": "中吉", "core_condition": "驿马发用+魁常入传"},
    "德庆课": {"score": 70, "level": "中吉", "core_condition": "天月日德发用"}
}

# 其他课经定义（含从属格映射）
OTHER_KE_JING = {
    "元首课": {"score": 98, "level": "上上吉", "core_condition": "一上克下为用"},
    "重审课": {"score": 85, "level": "吉", "core_condition": "一下克上为用"},
    "涉害课": {"score": 75, "level": "中吉", "core_condition": "涉害归家用孟仲季为用"},
    "遥克课": {"score": 70, "level": "中吉", "core_condition": "四课上神克日干或日干克上神"},
    "昴星课": {"score": 65, "level": "中", "core_condition": "四课无克无遥克"},
    "别责课": {"score": 60, "level": "中", "core_condition": "四课不备无克别取一神为用"},
    "八专课": {"score": 55, "level": "中", "core_condition": "干支同位无克"},
    "伏吟课": {"score": 50, "level": "中", "core_condition": "月将=占时"},
    "反吟课": {"score": 45, "level": "中", "core_condition": "月将冲占时"},
    "无禄课": {"score": 40, "level": "凶", "core_condition": "四上克下"}
}

# 从属格到主课的映射
SUB_GE_TO_MAIN_KE = {
    "见机格": "涉害课",
    "察微格": "涉害课",
    "缀瑕格": "涉害课",
    "蒿矢格": "遥克课",
    "弹射格": "遥克课",
    "虎视转蓬格": "昴星课",
    "冬蛇掩目格": "昴星课"
}

# 64课经完整定义（用于交叉匹配）
KE_JING_64 = {
    # 宗门九课相关
    "元首课": {"score": 98, "level": "上上吉", "check_func": "check_yuan_shou"},
    "重审课": {"score": 85, "level": "吉", "check_func": "check_zhong_shen"},
    "涉害课": {"score": 75, "level": "中吉", "check_func": "check_she_hai"},
    "遥克课": {"score": 70, "level": "中吉", "check_func": "check_yao_ke"},
    "昴星课": {"score": 65, "level": "中", "check_func": "check_mao_xing"},
    "别责课": {"score": 60, "level": "中", "check_func": "check_bie_ze"},
    "八专课": {"score": 55, "level": "中", "check_func": "check_ba_zhuan"},
    "伏吟课": {"score": 50, "level": "中", "check_func": "check_fu_yin"},
    "反吟课": {"score": 45, "level": "中", "check_func": "check_fan_yin"},
    
    # 伏吟课从属格
    "杜传格": {"score": 50, "level": "凶", "check_func": "check_du_chuan"},
    "自任格": {"score": 55, "level": "吉", "check_func": "check_zi_ren"},
    "自信格": {"score": 55, "level": "吉", "check_func": "check_zi_xin"},
    
    # 其他课体
    "励德课": {"score": 70, "level": "中吉", "check_func": "check_li_de"},
    "元胎课": {"score": 75, "level": "中吉", "check_func": "check_yuan_tai"},
    "连珠课": {"score": 72, "level": "中吉", "check_func": "check_lian_zhu"},
    "间传课": {"score": 68, "level": "中", "check_func": "check_jian_chuan"},
    "盘珠课": {"score": 70, "level": "中吉", "check_func": "check_pan_zhu"},
    "全局课": {"score": 75, "level": "中吉", "check_func": "check_quan_ju"},
    "六阴课": {"score": 40, "level": "凶", "check_func": "check_liu_yin"},
    "龙战课": {"score": 45, "level": "中", "check_func": "check_long_zhan"},
    "死绝课": {"score": 35, "level": "凶", "check_func": "check_si_jue"},
    "解离课": {"score": 40, "level": "凶", "check_func": "check_jie_li"},
    "度厄课": {"score": 45, "level": "中", "check_func": "check_du_e"},
    
    # 十三吉课
    **SHISAN_JI_KE
}


def check_fu_yin(ke_li: dict) -> Tuple[bool, str]:
    """检查伏吟课：月将=占时"""
    yue_jiang = ke_li.get("yue_jiang", "")
    shi = ke_li.get("shi", "")
    if yue_jiang == shi:
        return True, f"月将({yue_jiang})=占时({shi})"
    return False, ""


def check_du_chuan(ke_li: dict) -> Tuple[bool, str]:
    """检查杜传格：伏吟课中传行不过"""
    yue_jiang = ke_li.get("yue_jiang", "")
    shi = ke_li.get("shi", "")
    sanchuan = ke_li.get("sanchuan", {})
    sanchuan_list = sanchuan.get("三传", [])
    
    if yue_jiang == shi:  # 先要是伏吟课
        # 杜传格：三传中有相同或传行受阻
        if len(sanchuan_list) == 3:
            # 检查是否有传行不过的情况
            chu, zhong, mo = sanchuan_list
            if chu == zhong or zhong == mo:  # 传行受阻
                return True, f"三传{sanchuan_list}传行受阻"
    return False, ""


def check_li_de(ke_li: dict) -> Tuple[bool, str]:
    """检查励德课：贵人前干后支"""
    ri_gan_zhi = ke_li.get("ri_gan_zhi", "")
    sike = ke_li.get("sike", [])
    sanchuan = ke_li.get("sanchuan", {})
    
    ri_gan = ri_gan_zhi[0] if ri_gan_zhi else ""
    ri_zhi = ri_gan_zhi[1] if ri_gan_zhi else ""
    
    # 获取贵人位置
    # 简化判断：检查干支上神与贵人的关系
    # 需要贵人信息
    return False, ""


def check_yuan_tai(ke_li: dict) -> Tuple[bool, str]:
    """检查元胎课：三传皆孟"""
    sanchuan = ke_li.get("sanchuan", {})
    sanchuan_list = sanchuan.get("三传", [])
    
    # 四孟：寅申巳亥
    si_meng = ["寅", "申", "巳", "亥"]
    
    if len(sanchuan_list) == 3:
        if all(chuan in si_meng for chuan in sanchuan_list):
            return True, f"三传{sanchuan_list}皆孟（寅申巳亥）"
    return False, ""


def check_lian_zhu(ke_li: dict) -> Tuple[bool, str]:
    """检查连珠课：三传相连"""
    sanchuan = ke_li.get("sanchuan", {})
    sanchuan_list = sanchuan.get("三传", [])
    
    di_zhi_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    if len(sanchuan_list) == 3:
        idx1 = di_zhi_order.index(sanchuan_list[0]) if sanchuan_list[0] in di_zhi_order else -1
        idx2 = di_zhi_order.index(sanchuan_list[1]) if sanchuan_list[1] in di_zhi_order else -1
        idx3 = di_zhi_order.index(sanchuan_list[2]) if sanchuan_list[2] in di_zhi_order else -1
        
        if idx1 != -1 and idx2 != -1 and idx3 != -1:
            if (idx2 - idx1) % 12 == 1 and (idx3 - idx2) % 12 == 1:
                return True, f"三传{sanchuan_list}相连"
    return False, ""


def match_all_ke_ge(ke_li: dict) -> dict:
    """匹配所有可能的课格（支持一课多格）"""
    result = {
        "ri_gan_zhi": ke_li.get("ri_gan_zhi", ""),
        "yue": ke_li.get("yue", ""),
        "shi": ke_li.get("shi", ""),
        "yue_jiang": ke_li.get("yue_jiang", ""),
        "sanchuan": ke_li.get("sanchuan", {}).get("三传", []),
        "matched_ke_ge": [],
        "matched_details": [],
        "total_score": 0,
        "best_level": ""
    }
    
    # 1. 检查宗门九课（起课方法）
    ke_ti = ke_li.get("sanchuan", {}).get("课体", "")
    
    # 映射从属格到主课
    main_ke_ti = SUB_GE_TO_MAIN_KE.get(ke_ti, ke_ti)
    
    if main_ke_ti in OTHER_KE_JING:
        result["matched_ke_ge"].append(main_ke_ti)
        result["matched_details"].append({
            "ke_ge": main_ke_ti,
            "type": "宗门九课",
            "score": OTHER_KE_JING[main_ke_ti]["score"],
            "level": OTHER_KE_JING[main_ke_ti]["level"],
            "reason": OTHER_KE_JING[main_ke_ti]["core_condition"]
        })
    
    # 如果是从属格，也添加从属格信息
    if ke_ti != main_ke_ti:
        result["matched_details"].append({
            "ke_ge": ke_ti,
            "type": "从属格",
            "parent": main_ke_ti,
            "score": OTHER_KE_JING.get(main_ke_ti, {}).get("score", 0),
            "level": OTHER_KE_JING.get(main_ke_ti, {}).get("level", ""),
            "reason": f"{main_ke_ti}的从属格"
        })
    
    # 2. 检查伏吟课及其从属格
    matched, reason = check_fu_yin(ke_li)
    if matched:
        if "伏吟课" not in result["matched_ke_ge"]:
            result["matched_ke_ge"].append("伏吟课")
        result["matched_details"].append({
            "ke_ge": "伏吟课",
            "type": "64课经",
            "score": 50,
            "level": "中",
            "reason": reason
        })
        
        # 检查杜传格
        matched2, reason2 = check_du_chuan(ke_li)
        if matched2:
            result["matched_ke_ge"].append("杜传格")
            result["matched_details"].append({
                "ke_ge": "杜传格",
                "type": "从属格",
                "parent": "伏吟课",
                "score": 50,
                "level": "凶",
                "reason": reason2
            })
    
    # 3. 检查元胎课
    matched, reason = check_yuan_tai(ke_li)
    if matched:
        result["matched_ke_ge"].append("元胎课")
        result["matched_details"].append({
            "ke_ge": "元胎课",
            "type": "64课经",
            "score": 75,
            "level": "中吉",
            "reason": reason
        })
    
    # 4. 检查连珠课
    matched, reason = check_lian_zhu(ke_li)
    if matched:
        result["matched_ke_ge"].append("连珠课")
        result["matched_details"].append({
            "ke_ge": "连珠课",
            "type": "64课经",
            "score": 72,
            "level": "中吉",
            "reason": reason
        })
    
    # 5. 检查十三吉课
    sanchuan = ke_li.get("sanchuan", {})
    sanchuan_list = sanchuan.get("三传", [])
    chu_chuan = sanchuan.get("初传", "")
    yue = ke_li.get("yue", "")
    
    # 斫轮课
    if chu_chuan == "卯":
        result["matched_ke_ge"].append("斫轮课")
        result["matched_details"].append({
            "ke_ge": "斫轮课",
            "type": "十三吉课",
            "score": 92,
            "level": "上吉",
            "reason": "卯临庚辛申酉发用"
        })
    
    # 轩盖课
    if yue in ["寅", "申"] and set(sanchuan_list) == {"午", "卯", "子"} and chu_chuan == "午":
        result["matched_ke_ge"].append("轩盖课")
        result["matched_details"].append({
            "ke_ge": "轩盖课",
            "type": "十三吉课",
            "score": 90,
            "level": "上吉",
            "reason": "正七月午发用，三传午卯子"
        })
    
    # 铸印课
    if set(sanchuan_list) == {"巳", "戌", "卯"}:
        result["matched_ke_ge"].append("铸印课")
        result["matched_details"].append({
            "ke_ge": "铸印课",
            "type": "十三吉课",
            "score": 88,
            "level": "上吉",
            "reason": "戌加巳入传，三传巳戌卯"
        })
    
    # 计算总分和最佳等级
    if result["matched_details"]:
        scores = [d["score"] for d in result["matched_details"]]
        result["total_score"] = max(scores)
        
        best = max(result["matched_details"], key=lambda x: x["score"])
        result["best_level"] = best["level"]
    
    return result


def analyze_specific_case():
    """分析特定课例：己酉年十月壬午日、寅将寅时"""
    print("=" * 60)
    print("课格交叉匹配分析")
    print("=" * 60)
    
    # 构建课例数据
    ke_li = {
        "ri_gan_zhi": "壬午",
        "yue": "亥",  # 十月=亥月
        "shi": "寅",
        "yue_jiang": "寅",  # 寅将
        "sike": [],
        "sanchuan": {
            "三传": ["寅", "巳", "申"],  # 假设三传
            "课体": "伏吟课",
            "起法": "伏吟法",
            "初传": "寅",
            "中传": "巳",
            "末传": "申"
        }
    }
    
    print(f"\n课例信息：")
    print(f"- 日干支：{ke_li['ri_gan_zhi']}")
    print(f"- 月：{ke_li['yue']}（十月）")
    print(f"- 时：{ke_li['shi']}")
    print(f"- 月将：{ke_li['yue_jiang']}")
    print(f"- 三传：{ke_li['sanchuan']['三传']}")
    print(f"- 课体：{ke_li['sanchuan']['课体']}")
    
    # 匹配所有课格
    result = match_all_ke_ge(ke_li)
    
    print(f"\n匹配结果：")
    print(f"- 匹配课格：{result['matched_ke_ge']}")
    print(f"- 总分：{result['total_score']}")
    print(f"- 最佳等级：{result['best_level']}")
    
    print(f"\n详细匹配过程：")
    for i, detail in enumerate(result['matched_details'], 1):
        print(f"\n{i}. {detail['ke_ge']}（{detail['type']}）")
        print(f"   - 评分：{detail['score']}分")
        print(f"   - 等级：{detail['level']}")
        print(f"   - 原因：{detail['reason']}")
        if 'parent' in detail:
            print(f"   - 所属：{detail['parent']}的从属格")
    
    return result


def process_all_ke_li():
    """处理所有课例"""
    input_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\720_ke_li_jiu_zong_men.json"
    output_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\8640_ke_ge_matched_v3.json"
    
    print(f"加载课例数据: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    ke_li_data = data.get("ke_li", {})
    total = len(ke_li_data)
    print(f"共 {total} 个课例")
    
    results = {
        "metadata": {
            "total": total,
            "processed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ke_ge_statistics": {},
            "multi_ke_ge_count": 0
        },
        "ke_li": {}
    }
    
    for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
        if (i + 1) % 1000 == 0:
            print(f"处理进度: {i + 1}/{total}")
        
        ke_ge_result = match_all_ke_ge(ke_li)
        
        # 统计
        for ke_ge in ke_ge_result["matched_ke_ge"]:
            results["metadata"]["ke_ge_statistics"][ke_ge] = results["metadata"]["ke_ge_statistics"].get(ke_ge, 0) + 1
        
        if len(ke_ge_result["matched_ke_ge"]) > 1:
            results["metadata"]["multi_ke_ge_count"] += 1
        
        results["ke_li"][ke_li_key] = ke_ge_result
    
    # 保存结果
    print(f"保存结果: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成报告
    generate_report_v3(results, output_file.replace(".json", "_report.md"))
    
    print("处理完成！")
    return results


def generate_report_v3(results: dict, report_file: str):
    """生成报告"""
    metadata = results["metadata"]
    
    report = f"""# 8640课例课格交叉匹配报告

## 基本信息
- 处理时间：{metadata['processed_time']}
- 总课例数：{metadata['total']}
- 一课多格数：{metadata['multi_ke_ge_count']}

## 课格统计
"""
    
    ke_ge_stats = metadata.get("ke_ge_statistics", {})
    sorted_stats = sorted(ke_ge_stats.items(), key=lambda x: -x[1])
    for ke_ge, count in sorted_stats:
        report += f"- {ke_ge}：{count}例\n"
    
    # 添加多课格示例
    report += "\n## 一课多格示例\n\n"
    
    count = 0
    for ke_li_key, ke_li in results["ke_li"].items():
        if len(ke_li.get("matched_ke_ge", [])) > 1 and count < 10:
            report += f"""### {ke_li_key}
- 日干支：{ke_li.get('ri_gan_zhi', '')}
- 月将：{ke_li.get('yue_jiang', '')}
- 三传：{ke_li.get('sanchuan', [])}
- 匹配课格：{ke_li.get('matched_ke_ge', [])}
- 总分：{ke_li.get('total_score', 0)}分

"""
            count += 1
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"报告已保存: {report_file}")


if __name__ == "__main__":
    # 先分析特定课例
    analyze_specific_case()
    
    print("\n" + "=" * 60)
    print("开始处理所有课例...")
    print("=" * 60 + "\n")
    
    # 处理所有课例
    process_all_ke_li()
