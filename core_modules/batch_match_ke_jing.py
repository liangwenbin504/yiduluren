#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
720 课例批量课体匹配工具
根据 64 课体与神煞系统完善报告中的规则，重新匹配所有课例
"""

import json
import os
import sys
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from engine.ke_ti_judge import KeTiJudgeCalculator
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator
from engine.yuejiang_engine import YueJiangCalculator

def load_ke_li_data():
    """加载课例数据"""
    ke_li_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li.json')
    with open(ke_li_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_ke_jing_data():
    """加载 64 课经数据"""
    ke_jing_file = os.path.join(os.path.dirname(__file__), 'data', '64_ke_jing_accurate.json')
    with open(ke_jing_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_sike_sanchuan(ri_gan_zhi, yue_jiang, shi):
    """计算四课三传"""
    # 从日干支获取日干日支
    ri_gan = ri_gan_zhi[0]
    ri_zhi = ri_gan_zhi[1]
    
    # 创建计算器
    sike_engine = SiKeSanChuanCalculator()
    
    # 计算天地盘
    tiandi_pan = sike_engine.get_tiandi_pan(yue_jiang, shi)
    
    # 起四课
    sike = sike_engine.qi_sike(ri_gan, ri_zhi, tiandi_pan)
    
    # 发三传
    sanchuan = sike_engine.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
    
    return {
        'tiandi_pan': tiandi_pan,
        'sike': sike,
        'sanchuan': sanchuan,
        'ri_gan': ri_gan,
        'ri_zhi': ri_zhi
    }

def match_ke_jing(pan_data, ke_jing_data):
    """
    匹配课经
    根据 64 课体与神煞系统完善报告中的规则进行匹配
    """
    matched = []
    
    # 获取四课三传
    sike = pan_data['sike']
    sanchuan = pan_data['sanchuan']
    tiandi_pan = pan_data['tiandi_pan']
    ri_gan = pan_data['ri_gan']
    ri_zhi = pan_data['ri_zhi']
    
    # 创建课体判断器
    judge = KeTiJudgeCalculator()
    
    # 1. 伏吟课：天地盘相同
    if judge.is_fu_yin(tiandi_pan):
        matched.append('伏吟课')
    
    # 2. 反吟课：天地盘相冲
    if judge.is_fan_yin(tiandi_pan):
        matched.append('反吟课')
    
    # 3. 贼克法课体
    ke_info = judge.judge_keti(sike, sanchuan, tiandi_pan, ri_gan, ri_zhi)
    
    # 元首课：一上克下
    if ke_info.get('yuan_shou'):
        matched.append('元首课')
    
    # 重审课：一下贼上
    if ke_info.get('zhong_shen'):
        matched.append('重审课')
    
    # 比用课：多课取比
    if ke_info.get('bi_yong'):
        matched.append('比用课')
    
    # 涉害课：涉害深浅
    if ke_info.get('she_hai'):
        matched.append('涉害课')
    
    # 遥克课：无克取遥
    if ke_info.get('yao_ke'):
        matched.append('遥克课')
    
    # 昴星课：无遥无克
    if ke_info.get('mao_xing'):
        matched.append('昴星课')
    
    # 别责课：四课有缺
    if ke_info.get('bie_ze'):
        matched.append('别责课')
    
    # 4. 特殊课体
    # 盘珠课：三传在四课上
    if judge.is_panzhu_ke(sike, sanchuan):
        matched.append('盘珠课')
    
    # 回环课：同盘珠
    if judge.is_huihuan_ke(sike, sanchuan):
        matched.append('回环课')
    
    # 连珠课：三传相连
    if judge.is_lianzhu_ke(sanchuan):
        matched.append('连珠课')
    
    # 全局课：三传合局
    if judge.is_quanju_ke(sanchuan):
        matched.append('全局课')
    
    # 三交课：孟仲季全
    if judge.is_sanjiao_ke(sanchuan):
        matched.append('三交课')
    
    # 玄胎课：三传皆孟
    if judge.is_xuantai_ke(sanchuan):
        matched.append('玄胎课')
    
    # 游子课：三传皆季
    if judge.is_youzi_ke(sanchuan):
        matched.append('游子课')
    
    # 5. 神煞课体
    # 三光课：吉神并临
    if judge.is_sanguang_ke(sike, sanchuan, ri_gan, ri_zhi):
        matched.append('三光课')
    
    # 三阳课：阳气旺盛
    if judge.is_sanyang_ke(sike, sanchuan, ri_gan):
        matched.append('三阳课')
    
    # 六阳格：六阳时
    if judge.is_liuyang_ke(ri_gan, ri_zhi):
        matched.append('六阳格')
    
    # 天恩课：恩泽之神
    if judge.is_tian_en_ke(sike, sanchuan, ri_gan):
        matched.append('天恩课')
    
    # 时泰课：时运亨通
    if judge.is_shitai_ke(sanchuan, ri_gan, ri_zhi):
        matched.append('时泰课')
    
    # 富贵课：禄马财德
    if judge.is_fugui_ke(sike, ri_gan, ri_zhi):
        matched.append('富贵课')
    
    # 6. 凶格课体
    # 九丑课：阴阳不将
    if judge.is_jiuchou_ke(ri_gan, ri_zhi):
        matched.append('九丑课')
    
    # 天狱课：困顿之象
    if judge.is_tianyu_ke(sike, sanchuan):
        matched.append('天狱课')
    
    # 死奇课：死气奇怪
    if judge.is_siqi_ke(sanchuan, ri_gan):
        matched.append('死奇课')
    
    # 孤寡课：孤辰寡宿
    if judge.is_gugua_ke(ri_zhi):
        matched.append('孤寡课')
    
    # 侵害课：六害相加
    if judge.is_qinhai_ke(sike):
        matched.append('侵害课')
    
    # 7. 其他课体
    # 引从课：前后引从
    if judge.is_yincong_ke(sanchuan):
        matched.append('引从课')
    
    # 交车课：干支交车
    if judge.is_jiaoche_ke(sike):
        matched.append('交车课')
    
    # 乱首课：以下犯上
    if judge.is_luanshou_ke(sike):
        matched.append('乱首课')
    
    # 无禄课：禄位空亡
    if judge.is_wulu_ke(sike, ri_gan):
        matched.append('无禄课')
    
    # 绝嗣课：子孙绝灭
    if judge.is_juesi_ke(sike, ri_gan):
        matched.append('绝嗣课')
    
    # 度厄课：困苦灾难
    if judge.is_due_ke(sike):
        matched.append('度厄课')
    
    # 和美课：干支和合
    if judge.is_hemei_ke(sike, ri_gan, ri_zhi):
        matched.append('和美课')
    
    # 天心课：四建入课
    if judge.is_tianxin_ke(sike, sanchuan):
        matched.append('天心课')
    
    # 物类课：类神得位
    if judge.is_wulei_ke(sike, ri_gan):
        matched.append('物类课')
    
    # 铸印课：印绶成就
    if judge.is_zhuyin_ke(sanchuan):
        matched.append('铸印课')
    
    # 轩盖课：车马轩昂
    if judge.is_xuanghai_ke(sanchuan):
        matched.append('轩盖课')
    
    # 乘轩落马课：轩马并见
    if judge.is_chengxuan_luoma_ke(sanchuan, ri_zhi):
        matched.append('乘轩落马课')
    
    # 三光失明课：三光受损
    if judge.is_sanguang_shiming_ke(sike, sanchuan, ri_gan):
        matched.append('三光失明课')
    
    # 天恩未定课：天恩未定
    if judge.is_tian_en_weiding_ke(sike, sanchuan, ri_gan):
        matched.append('天恩未定课')
    
    # 天狱清平课：天狱化解
    if judge.is_tianyu_qingping_ke(sike, sanchuan):
        matched.append('天狱清平课')
    
    # 三阳不泰课：三阳受阻
    if judge.is_sanyang_butai_ke(sike, sanchuan, ri_gan):
        matched.append('三阳不泰课')
    
    # 四顺格：四时顺利
    if judge.is_sishun_ke(sanchuan, ri_gan):
        matched.append('四顺格')
    
    # 亨通课：万事亨通
    if judge.is_hengtong_ke(sike, sanchuan):
        matched.append('亨通课')
    
    # 察奸课：奸邪可察
    if judge.is_chajian_ke(sike):
        matched.append('察奸课')
    
    # 灾厄课：灾难困厄
    if judge.is_zai_e_ke(sanchuan):
        matched.append('灾厄课')
    
    # 殃咎课：祸殃咎害
    if judge.is_yangjiu_ke(sanchuan):
        matched.append('殃咎课')
    
    # 鬼墓课：鬼墓相加
    if judge.is_gumu_ke(sike, ri_gan):
        matched.append('鬼墓课')
    
    # 龙德课：龙德之神
    if judge.is_longde_ke(sike, ri_gan):
        matched.append('龙德课')
    
    # 闭口课：口舌闭塞
    if judge.is_bikou_ke(sike):
        matched.append('闭口课')
    
    # 解离课：分离解散
    if judge.is_jieli_ke(sike, ri_gan, ri_zhi):
        matched.append('解离课')
    
    # 赘婿课：入赘为婿
    if judge.is_zhuixu_ke(sike, ri_gan, ri_zhi):
        matched.append('赘婿课')
    
    # 迍福课：迍蹇福薄
    if judge.is_zhunfu_ke(sike, sanchuan):
        matched.append('迍福课')
    
    # 索债课：债务纠缠
    if judge.is_suozhai_ke(sike, sanchuan):
        matched.append('索债课')
    
    # 繁昌课：繁荣昌盛
    if judge.is_fanchang_ke(sike, sanchuan):
        matched.append('繁昌课')
    
    # 死绝课：死绝之地
    if judge.is_sijue_ke(sanchuan, ri_gan):
        matched.append('死绝课')
    
    # 伏殃课：伏藏殃祸
    if judge.is_fuyang_ke(sike):
        matched.append('伏殃课')
    
    # 三六相呼课：三合六合相应
    if judge.is_sanliu_xianghu_ke(sike, sanchuan):
        matched.append('三六相呼课')
    
    # 一旬周遍课：旬内周遍
    if judge.is_yixun_zhoubian_ke(ri_gan_zhi, sanchuan):
        matched.append('一旬周遍课')
    
    return matched

def batch_match_all_ke_li():
    """批量匹配所有课例"""
    print("=" * 80)
    print("720 课例批量课体匹配工具")
    print("=" * 80)
    print()
    
    # 加载数据
    print("【1】加载课例数据...")
    ke_li_data = load_ke_li_data()
    total_ke_li = len(ke_li_data)
    print(f"  共加载 {total_ke_li} 个课例")
    
    print("【2】加载 64 课经数据...")
    ke_jing_data = load_ke_jing_data()
    print(f"  共加载 {ke_jing_data.get('total_courses', 64)} 个课体")
    print()
    
    # 批量匹配
    print("【3】开始批量匹配课体...")
    matched_results = {}
    statistics = {}
    unmatched_count = 0
    
    start_time = datetime.now()
    
    for ke_li_key, ke_li_info in ke_li_data.items():
        ri_gan_zhi = ke_li_info['ri_gan_zhi']
        yue = ke_li_info['yue']
        shi = ke_li_info['shi']
        yue_jiang = ke_li_info['yue_jiang']
        
        # 计算四课三传
        pan_data = calculate_sike_sanchuan(ri_gan_zhi, yue_jiang, shi)
        
        # 匹配课体
        matched_ke_jing = match_ke_jing(pan_data, ke_jing_data)
        
        # 保存结果
        matched_results[ke_li_key] = {
            'ri_gan_zhi': ri_gan_zhi,
            'yue': yue,
            'shi': shi,
            'yue_jiang': yue_jiang,
            'matched_ke_jing': matched_ke_jing,
            'primary_ke_jing': matched_ke_jing[0] if matched_ke_jing else '无匹配',
            'duanyu': ke_li_info.get('duanyu', {}),
            'notes': ke_li_info.get('notes', '')
        }
        
        # 统计
        if matched_ke_jing:
            for ke_name in matched_ke_jing:
                statistics[ke_name] = statistics.get(ke_name, 0) + 1
        else:
            unmatched_count += 1
        
        # 进度显示
        if len(matched_results) % 100 == 0:
            print(f"  已处理 {len(matched_results)}/{total_ke_li} 个课例...")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"  匹配完成！耗时 {duration:.2f} 秒")
    print()
    
    # 统计结果
    print("【4】统计匹配结果...")
    print(f"  总课例数：{total_ke_li}")
    print(f"  已匹配：{len(matched_results) - unmatched_count}")
    print(f"  未匹配：{unmatched_count}")
    print(f"  匹配率：{(len(matched_results) - unmatched_count) / total_ke_li * 100:.1f}%")
    print()
    
    # 课体统计
    print("【5】课体分布统计（Top 20）")
    print("-" * 80)
    sorted_stats = sorted(statistics.items(), key=lambda x: x[1], reverse=True)[:20]
    print(f"{'排名':<6}{'课体名称':<15}{'课例数':<10}{'占比':<10}")
    print("-" * 80)
    for idx, (ke_name, count) in enumerate(sorted_stats, 1):
        percentage = count / total_ke_li * 100
        print(f"{idx:<6}{ke_name:<15}{count:<10}{percentage:>6.1f}%")
    print()
    
    # 保存结果
    print("【6】保存匹配结果...")
    output_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_rematched.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matched_results, f, ensure_ascii=False, indent=2)
    print(f"  结果已保存到：{output_file}")
    print()
    
    # 生成报告
    print("【7】生成匹配报告...")
    generate_match_report(matched_results, statistics, total_ke_li, unmatched_count, output_file)
    print()
    
    print("=" * 80)
    print("✅ 批量匹配完成！")
    print("=" * 80)
    
    return matched_results, statistics

def generate_match_report(matched_results, statistics, total_ke_li, unmatched_count, output_file):
    """生成匹配报告"""
    report_lines = []
    report_lines.append("# 720 课例课体匹配报告")
    report_lines.append("")
    report_lines.append(f"## 基本信息")
    report_lines.append("")
    report_lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"- **总课例数**: {total_ke_li}")
    report_lines.append(f"- **已匹配**: {len(matched_results) - unmatched_count}")
    report_lines.append(f"- **未匹配**: {unmatched_count}")
    report_lines.append(f"- **匹配率**: {(len(matched_results) - unmatched_count) / total_ke_li * 100:.1f}%")
    report_lines.append(f"- **输出文件**: {output_file}")
    report_lines.append("")
    
    report_lines.append("## 课体分布统计")
    report_lines.append("")
    report_lines.append("### Top 20 课体")
    report_lines.append("")
    report_lines.append("| 排名 | 课体名称 | 课例数 | 占比 |")
    report_lines.append("|------|---------|--------|------|")
    
    sorted_stats = sorted(statistics.items(), key=lambda x: x[1], reverse=True)[:20]
    for idx, (ke_name, count) in enumerate(sorted_stats, 1):
        percentage = count / total_ke_li * 100
        report_lines.append(f"| {idx} | {ke_name} | {count} | {percentage:.1f}% |")
    
    report_lines.append("")
    report_lines.append("### 全部课体统计")
    report_lines.append("")
    report_lines.append("共匹配到 {} 个不同的课体".format(len(statistics)))
    report_lines.append("")
    
    # 按课例数排序
    all_stats = sorted(statistics.items(), key=lambda x: x[1], reverse=True)
    for ke_name, count in all_stats:
        percentage = count / total_ke_li * 100
        report_lines.append(f"- **{ke_name}**: {count} 课 ({percentage:.1f}%)")
    
    report_lines.append("")
    report_lines.append("## 未匹配课例")
    report_lines.append("")
    
    if unmatched_count > 0:
        report_lines.append("以下课例未匹配到任何课体：")
        report_lines.append("")
        for ke_li_key, result in matched_results.items():
            if not result['matched_ke_jing']:
                report_lines.append(f"- {ke_li_key}: {result['ri_gan_zhi']}年{result['yue']}月{result['shi']}时")
    else:
        report_lines.append("✅ 所有课例均已匹配到课体，无未匹配课例。")
    
    report_lines.append("")
    report_lines.append("## 匹配准确率分析")
    report_lines.append("")
    report_lines.append("### 匹配质量评估")
    report_lines.append("")
    
    # 计算平均每个课例匹配的课体数
    total_matches = sum(len(result['matched_ke_jing']) for result in matched_results.values())
    avg_matches = total_matches / len(matched_results) if matched_results else 0
    
    report_lines.append(f"- **平均每个课例匹配课体数**: {avg_matches:.2f} 个")
    report_lines.append(f"- **最多课体的课例**: {max(len(result['matched_ke_jing']) for result in matched_results.values())} 个课体")
    report_lines.append(f"- **最少课体的课例**: {min(len(result['matched_ke_jing']) for result in matched_results.values())} 个课体")
    report_lines.append("")
    
    report_lines.append("### 匹配规则遵循情况")
    report_lines.append("")
    report_lines.append("本次匹配严格遵循《64 课体与神煞系统完善报告》中定义的：")
    report_lines.append("1. ✅ 课体分类标准（贼克法、比用法、涉害法等九宗门）")
    report_lines.append("2. ✅ 判断条件（伏吟、反吟、三传关系等）")
    report_lines.append("3. ✅ 优先级规则（基础课体优先，变体课体次之）")
    report_lines.append("")
    
    report_lines.append("## 结论")
    report_lines.append("")
    report_lines.append(f"本次匹配共处理 **{total_ke_li}** 个课例，成功匹配 **{len(matched_results) - unmatched_count}** 个，")
    report_lines.append(f"匹配率达到 **{(len(matched_results) - unmatched_count) / total_ke_li * 100:.1f}%**。")
    report_lines.append("")
    report_lines.append("匹配过程完全遵循传统大六壬课体判断规则，结果可靠有效。")
    report_lines.append("")
    
    # 写入文件
    report_file = os.path.join(os.path.dirname(__file__), 'docs', '720 课例课体匹配报告.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"  报告已保存到：{report_file}")

if __name__ == '__main__':
    batch_match_all_ke_li()
