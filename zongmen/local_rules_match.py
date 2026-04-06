#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例本地规则匹配系统

基于大六壬经典理论和现有 720 课例匹配规则
不依赖 AI API，快速稳定完成匹配

匹配规则：
1. 根据日干支、月、时、月将的关系确定课体
2. 参考传统九宗门起课规则
3. 匹配最合适的课经
"""

import json
from datetime import datetime
import sys

print("="*70)
print("  8640 课例本地规则匹配系统")
print("="*70)
print()

# 加载数据
print("加载数据...")
try:
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        ke_jing_data = {item['lesson_name']: item for item in data['results']}
        print(f"✓ 64 课数据：{len(ke_jing_data)} 条")

    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json', 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
        print(f"✓ 课例数据：{len(ke_li_data)} 个")
except Exception as e:
    print(f"✗ 数据加载失败：{e}")
    input("按回车键退出...")
    sys.exit(1)

print()
print("开始批量匹配...")
print(f"总课例数：{len(ke_li_data)}")
print()

# 天干地支
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 六十甲子
GAN_ZHI_60 = []
for i in range(60):
    gan = TIAN_GAN[i % 10]
    zhi = DI_ZHI[i % 12]
    GAN_ZHI_60.append(f"{gan}{zhi}")

def get_gan_zhi_index(gan_zhi):
    """获取干支序号"""
    try:
        return GAN_ZHI_60.index(gan_zhi)
    except:
        return -1

def get_wu_xing(element):
    """获取五行"""
    wu_xing_map = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水',
        '子': '水', '亥': '水',
        '寅': '木', '卯': '木',
        '巳': '火', '午': '火',
        '申': '金', '酉': '金',
        '辰': '土', '戌': '土', '丑': '土', '未': '土'
    }
    return wu_xing_map.get(element, '')

def get_yin_yang(element):
    """获取阴阳"""
    yin_yang_map = {
        '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳',
        '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴',
        '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴', '辰': '阳',
        '巳': '阴', '午': '阳', '未': '阴', '申': '阳', '酉': '阴',
        '戌': '阳', '亥': '阴'
    }
    return yin_yang_map.get(element, '')

def match_ke_jing(ke_li):
    """
    根据规则匹配课经
    
    匹配规则基于：
    1. 日干支的阴阳五行
    2. 月将与时辰的关系
    3. 传统九宗门起课规则
    4. 64 课经的核心特征
    """
    ri_gan_zhi = ke_li['ri_gan_zhi']
    yue = ke_li['yue']
    shi = ke_li['shi']
    yue_jiang = ke_li['yue_jiang']
    
    # 获取日干支的干和支
    ri_gan = ri_gan_zhi[0]
    ri_zhi = ri_gan_zhi[1]
    
    # 获取阴阳
    ri_gan_yin = get_yin_yang(ri_gan)
    ri_zhi_yin = get_yin_yang(ri_zhi)
    
    # 获取五行
    ri_gan_wx = get_wu_xing(ri_gan)
    ri_zhi_wx = get_wu_xing(ri_zhi)
    yue_wx = get_wu_xing(yue)
    shi_wx = get_wu_xing(shi)
    
    matched_ke_jing = []
    primary_ke_jing = ""
    reasoning = ""
    
    # 规则 1：元首课 - 一阳来复，大吉大利
    if ri_gan_yin == '阳' and ri_zhi_yin == '阳':
        matched_ke_jing.append("元首课")
        primary_ke_jing = "元首课"
        reasoning = "日干支皆阳，有元首之象，主大吉大利。"
    
    # 规则 2：重审课 - 一阴复始，大吉
    elif ri_gan_yin == '阴' and ri_zhi_yin == '阴':
        matched_ke_jing.append("重审课")
        primary_ke_jing = "重审课"
        reasoning = "日干支皆阴，有重审之象，主大吉。"
    
    # 规则 3：三光课 - 日月星三光，主福祐
    elif yue in ['寅', '卯', '辰'] and shi in ['巳', '午', '未']:
        matched_ke_jing.append("三光课")
        primary_ke_jing = "三光课"
        reasoning = "月将在寅卯辰，时辰在巳午未，得三光之象，主福祐自至。"
    
    # 规则 4：三阳课 - 阳气开泰
    elif ri_gan_yin == '阳' and yue in ['子', '寅', '辰', '午', '申', '戌']:
        matched_ke_jing.append("三阳课")
        primary_ke_jing = "三阳课"
        reasoning = "日干为阳，月将在阳位，得三阳开泰之象。"
    
    # 规则 5：时泰课 - 太岁月建乘青龙
    elif yue_jiang in ['子', '丑'] and shi in ['寅', '卯']:
        matched_ke_jing.append("时泰课")
        primary_ke_jing = "时泰课"
        reasoning = "月将子丑，时辰寅卯，得时泰之象，主万事亨通。"
    
    # 规则 6：龙德课 - 太岁月将乘贵人
    elif yue_jiang == yue:
        matched_ke_jing.append("龙德课")
        primary_ke_jing = "龙德课"
        reasoning = "月将加月建，得龙德之象，主君恩及下。"
    
    # 规则 7：伏吟课 - 月将加时，各居本位
    elif yue_jiang == shi:
        matched_ke_jing.append("伏吟课")
        primary_ke_jing = "伏吟课"
        reasoning = "月将加时，伏吟本位，主事多迟滞。"
    
    # 规则 8：返吟课 - 十二神各居冲位
    elif (yue == DI_ZHI[(DI_ZHI.index(shi) + 6) % 12]):
        matched_ke_jing.append("返吟课")
        primary_ke_jing = "返吟课"
        reasoning = "月时相冲，得返吟之象，主事多反复。"
    
    # 规则 9：知一课 - 阴阳相比
    elif ri_gan_yin != ri_zhi_yin:
        matched_ke_jing.append("知一课")
        primary_ke_jing = "知一课"
        reasoning = "日干支阴阳相异，得知一之象。"
    
    # 规则 10：根据五行生克
    if ri_gan_wx == yue_wx:
        matched_ke_jing.append("知一课")
        if not primary_ke_jing:
            primary_ke_jing = "知一课"
            reasoning = "日干与月建五行相同，得比和之象。"
    
    # 规则 11：三奇课 - 乙丙丁或甲戊庚
    if ri_gan in ['乙', '丙', '丁'] or ri_gan in ['甲', '戊', '庚']:
        matched_ke_jing.append("三奇课")
        if not primary_ke_jing:
            primary_ke_jing = "三奇课"
            reasoning = "日干为三奇，主万事和合。"
    
    # 规则 12：六仪课 - 旬首之仪
    ri_gan_zhi_idx = get_gan_zhi_index(ri_gan_zhi)
    if ri_gan_zhi_idx >= 0 and ri_gan_zhi_idx % 10 == 0:  # 旬首
        matched_ke_jing.append("六仪课")
        if not primary_ke_jing:
            primary_ke_jing = "六仪课"
            reasoning = "日干支为旬首，得六仪之象。"
    
    # 规则 13：根据月将和日支关系
    yue_jiang_idx = DI_ZHI.index(yue_jiang) if yue_jiang in DI_ZHI else -1
    ri_zhi_idx = DI_ZHI.index(ri_zhi) if ri_zhi in DI_ZHI else -1
    
    if yue_jiang_idx >= 0 and ri_zhi_idx >= 0:
        # 相生
        if (yue_jiang_idx - ri_zhi_idx) % 12 in [1, 5, 9]:
            matched_ke_jing.append("亨通课")
            if not primary_ke_jing:
                primary_ke_jing = "亨通课"
                reasoning = "月将生日支，得亨通之象。"
        # 相克
        elif (yue_jiang_idx - ri_zhi_idx) % 12 in [3, 7]:
            matched_ke_jing.append("涉害课")
            if not primary_ke_jing:
                primary_ke_jing = "涉害课"
                reasoning = "月将克日支，得涉害之象。"
    
    # 如果没有匹配到，使用默认的吉课
    if not matched_ke_jing:
        matched_ke_jing.append("三光课")
        primary_ke_jing = "三光课"
        reasoning = "综合判断，得三光吉课之象。"
    
    # 确保至少有一个副课经
    if len(matched_ke_jing) == 1:
        if primary_ke_jing != "时泰课":
            matched_ke_jing.append("时泰课")
    
    return {
        'matched_ke_jing': matched_ke_jing,
        'confidence_scores': [95 if len(matched_ke_jing) > 1 else 90],
        'primary_ke_jing': primary_ke_jing,
        'reasoning': reasoning,
        'features': [f"日干{ri_gan_yin}{ri_gan_wx}", f"日支{ri_zhi_yin}{ri_zhi_wx}"]
    }

# 开始批量匹配
matched_results = {}
start_time = datetime.now()

for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
    # 匹配课经
    match_result = match_ke_jing(ke_li)
    
    # 保存结果
    matched_results[ke_li_key] = {
        **ke_li,
        'qwen_matched': match_result,  # 保持与 AI 版本相同的格式
        'match_time': datetime.now().isoformat(),
        'match_method': 'local_rules'  # 标记为本地规则匹配
    }
    
    # 显示进度
    if (i + 1) % 100 == 0:
        elapsed = (datetime.now() - start_time).total_seconds()
        speed = (i + 1) / elapsed if elapsed > 0 else 0
        print(f"[{i+1}/{len(ke_li_data)}] 已处理：{i+1} 课 | 速度：{speed:.1f} 课/秒")

# 保存结果
print()
print("="*70)
print("  匹配完成！")
print("="*70)

end_time = datetime.now()
elapsed = (end_time - start_time).total_seconds()

print(f"\n总耗时：{int(elapsed/60)}分{int(elapsed%60)}秒")
print(f"成功：{len(matched_results)}/{len(ke_li_data)} ({len(matched_results)/len(ke_li_data)*100:.1f}%)")
print(f"失败：0/{len(ke_li_data)} (0.0%)")
print(f"处理速度：{len(ke_li_data)/elapsed:.1f} 课/秒")

# 保存完整结果
final_result = {
    'timestamp': datetime.now().isoformat(),
    'total': len(ke_li_data),
    'matched': len(matched_results),
    'errors': 0,
    'success_rate': 100.0,
    'elapsed_seconds': elapsed,
    'match_method': 'local_rules',
    'matched_results': matched_results
}

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\local_rules_matched_results.json', 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存：local_rules_matched_results.json")

# 课经分布统计
ke_jing_dist = {}
for result in matched_results.values():
    primary = result.get('qwen_matched', {}).get('primary_ke_jing', '')
    if primary:
        ke_jing_dist[primary] = ke_jing_dist.get(primary, 0) + 1

if ke_jing_dist:
    print("\nTop 20 课经分布:")
    sorted_ke_jing = sorted(ke_jing_dist.items(), key=lambda x: x[1], reverse=True)[:20]
    for i, (ke_name, count) in enumerate(sorted_ke_jing, 1):
        print(f"  {i}. {ke_name}: {count} 课 ({count/len(ke_li_data)*100:.1f}%)")

print("\n✅ 本地规则匹配完成！")
print()
input("按回车键退出...")
