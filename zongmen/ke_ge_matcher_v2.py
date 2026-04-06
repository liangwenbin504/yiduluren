# -*- coding: utf-8 -*-
"""
大六壬课格匹配系统 v2
将64课经从属课格匹配到8640课例
根据三传等条件判断是否为十三吉课
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 十三吉课定义
SHISAN_JI_KE = {
    "龙德课": {
        "score": 95,
        "level": "上吉",
        "core_condition": "太岁=月将乘贵人发用"
    },
    "斫轮课": {
        "score": 92,
        "level": "上吉",
        "core_condition": "卯临庚辛申酉发用"
    },
    "轩盖课": {
        "score": 90,
        "level": "上吉",
        "core_condition": "正七月午发用，三传午卯子"
    },
    "铸印课": {
        "score": 88,
        "level": "上吉",
        "core_condition": "戌加巳入传，三传巳戌卯"
    },
    "合欢课": {
        "score": 86,
        "level": "上吉",
        "core_condition": "干支合+三传合+年命吉将"
    },
    "合美课": {
        "score": 84,
        "level": "上吉",
        "core_condition": "干支递合或互合"
    },
    "繁昌课": {
        "score": 82,
        "level": "中吉",
        "core_condition": "三传皆旺相有气"
    },
    "富贵课": {
        "score": 80,
        "level": "中吉",
        "core_condition": "贵人乘旺相临日辰发用"
    },
    "时泰课": {
        "score": 78,
        "level": "中吉",
        "core_condition": "太岁月建乘青龙六合发用"
    },
    "亨通课": {
        "score": 76,
        "level": "中吉",
        "core_condition": "三传递生日干"
    },
    "荣华课": {
        "score": 74,
        "level": "中吉",
        "core_condition": "禄马贵人临干支发用"
    },
    "官爵课": {
        "score": 72,
        "level": "中吉",
        "core_condition": "驿马发用+魁常入传"
    },
    "德庆课": {
        "score": 70,
        "level": "中吉",
        "core_condition": "天月日德发用"
    }
}

# 其他课经定义
OTHER_KE_JING = {
    "元首课": {
        "score": 98,
        "level": "上上吉",
        "core_condition": "一上克下为用"
    },
    "重审课": {
        "score": 85,
        "level": "吉",
        "core_condition": "一下克上为用"
    },
    "涉害课": {
        "score": 75,
        "level": "中吉",
        "core_condition": "涉害归家用孟仲季为用"
    },
    "遥克课": {
        "score": 70,
        "level": "中吉",
        "core_condition": "四课上神克日干或日干克上神"
    },
    "昴星课": {
        "score": 65,
        "level": "中",
        "core_condition": "四课无克无遥克"
    },
    "别责课": {
        "score": 60,
        "level": "中",
        "core_condition": "四课不备无克别取一神为用"
    },
    "八专课": {
        "score": 55,
        "level": "中",
        "core_condition": "干支同位无克"
    },
    "伏吟课": {
        "score": 50,
        "level": "中",
        "core_condition": "月将=占时"
    },
    "反吟课": {
        "score": 45,
        "level": "中",
        "core_condition": "月将冲占时"
    },
    "无禄课": {
        "score": 40,
        "level": "凶",
        "core_condition": "四上克下"
    }
}

def match_ke_ge(ke_li: dict) -> dict:
    """匹配课格"""
    result = {
        "is_shisan_ji_ke": False,
        "matched_ke_ge": [],
        "score": 0,
        "level": "",
        "ke_ge_explanation": ""
    }
    
    ke_ti = ke_li.get("sanchuan", {}).get("课体", "")
    sanchuan = ke_li.get("sanchuan", {})
    sanchuan_list = sanchuan.get("三传", [])
    chu_chuan = sanchuan.get("初传", "")
    
    # 检查十三吉课条件
    # 1. 斫轮课：卯临庚辛申酉发用
    if chu_chuan == "卯":
        result["is_shisan_ji_ke"] = True
        result["matched_ke_ge"].append("斫轮课")
        result["score"] = 92
        result["level"] = "上吉"
        result["ke_ge_explanation"] = "【斫轮课】卯临庚辛申酉发用"
        return result
    
    # 2. 轩盖课：正七月午发用，三传午卯子
    yue = ke_li.get("yue", "")
    if yue in ["寅", "申"] and set(sanchuan_list) == {"午", "卯", "子"} and chu_chuan == "午":
        result["is_shisan_ji_ke"] = True
        result["matched_ke_ge"].append("轩盖课")
        result["score"] = 90
        result["level"] = "上吉"
        result["ke_ge_explanation"] = "【轩盖课】正七月午发用，三传午卯子"
        return result
    
    # 3. 铸印课：戌加巳入传，三传巳戌卯
    if set(sanchuan_list) == {"巳", "戌", "卯"}:
        result["is_shisan_ji_ke"] = True
        result["matched_ke_ge"].append("铸印课")
        result["score"] = 88
        result["level"] = "上吉"
        result["ke_ge_explanation"] = "【铸印课】戌加巳入传，三传巳戌卯"
        return result
    
    # 检查其他课经
    if ke_ti in OTHER_KE_JING:
        result["matched_ke_ge"].append(ke_ti)
        result["score"] = OTHER_KE_JING[ke_ti]["score"]
        result["level"] = OTHER_KE_JING[ke_ti]["level"]
        result["ke_ge_explanation"] = f"【{ke_ti}】{OTHER_KE_JING[ke_ti]['core_condition']}"
        return result
    
    # 未知课体
    result["ke_ge_explanation"] = f"课体【{ke_ti}】未在课经定义中找到"
    return result


def process_all_ke_li():
    """处理所有课例"""
    input_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\720_ke_li_jiu_zong_men.json"
    output_file = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\data\8640_ke_ge_matched_v2.json"
    
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
            "shisan_ji_ke_count": 0,
            "other_ke_jing_count": 0,
            "unknown_ke_ti_count": 0,
            "ke_ti_distribution": {},
            "shisan_ji_ke_details": {}
        },
        "ke_li": {}
    }
    
    for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
        if (i + 1) % 1000 == 0:
            print(f"处理进度: {i + 1}/{total}")
        
        ke_ge_result = match_ke_ge(ke_li)
        
        # 统计课体分布
        ke_ti = ke_li.get("sanchuan", {}).get("课体", "")
        if ke_ti:
            results["metadata"]["ke_ti_distribution"][ke_ti] = results["metadata"]["ke_ti_distribution"].get(ke_ti, 0) + 1
        
        # 统计
        if ke_ge_result["is_shisan_ji_ke"]:
            results["metadata"]["shisan_ji_ke_count"] += 1
            for ke_ge in ke_ge_result["matched_ke_ge"]:
                results["metadata"]["shisan_ji_ke_details"][ke_ge] = results["metadata"]["shisan_ji_ke_details"].get(ke_ge, 0) + 1
        elif ke_ge_result["matched_ke_ge"]:
            results["metadata"]["other_ke_jing_count"] += 1
        else:
            results["metadata"]["unknown_ke_ti_count"] += 1
        
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
    
    shisan_details = metadata.get("shisan_ji_ke_details", {})
    if shisan_details:
        for ke_ge, count in sorted(shisan_details.items(), key=lambda x: -x[1]):
            report += f"- {ke_ge}：{count}例\n"
    else:
        report += "- 无匹配\n"
    
    report += "\n## 课体分布统计\n"
    
    ke_ti_dist = metadata.get("ke_ti_distribution", {})
    sorted_dist = sorted(ke_ti_dist.items(), key=lambda x: -x[1])
    for ke_ti, count in sorted_dist:
        score = 0
        level = ""
        if ke_ti in OTHER_KE_JING:
            score = OTHER_KE_JING[ke_ti]["score"]
            level = OTHER_KE_JING[ke_ti]["level"]
        elif ke_ti in SHISAN_JI_KE:
            score = SHISAN_JI_KE[ke_ti]["score"]
            level = SHISAN_JI_KE[ke_ti]["level"]
        report += f"- {ke_ti}（{level}，{score}分）：{count}例\n"
    
    # 添加示例
    report += "\n## 示例课例（十三吉课）\n\n"
    
    count = 0
    for ke_li_key, ke_li in results["ke_li"].items():
        ke_ge = ke_li.get("ke_ge_matched", {})
        if ke_ge.get("is_shisan_ji_ke") and count < 10:
            report += f"""### {ke_li_key}
- 日干支：{ke_li.get('ri_gan_zhi', '')}
- 月：{ke_li.get('yue', '')}
- 三传：{ke_li.get('sanchuan', {}).get('三传', [])}
- 匹配课格：{ke_ge.get('matched_ke_ge', [])}
- 评分：{ke_ge.get('score', 0)}分
- 说明：{ke_ge.get('ke_ge_explanation', '')}

"""
            count += 1
    
    # 保存报告
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"报告已保存: {report_file}")


if __name__ == "__main__":
    process_all_ke_li()
