#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量为二十四山课格数据添加评分字段
"""

# 二十四山评分数据
scores_data = {
    '壬山': (8.0, True), '子山': (8.5, True), '癸山': (8.0, True), '丑山': (7.5, True),
    '艮山': (7.5, True), '寅山': (7.5, True), '甲山': (7.0, True), '卯山': (7.5, True),
    '乙山': (7.0, True), '辰山': (7.0, True), '巽山': (7.0, True), '巳山': (8.0, True),
    '丙山': (7.5, True), '午山': (8.0, True), '丁山': (8.5, True), '未山': (8.0, True),
    '坤山': (7.5, True), '申山': (7.0, True), '庚山': (8.0, True), '酉山': (7.0, True),
    '辛山': (7.5, True), '戌山': (7.5, True), '乾山': (8.0, True), '亥山': (8.0, True),
}

# 读取文件
with open('src/engine/douhou_shan_jia_system.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 添加评分字段
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # 在每个山的 jinji 字段后添加评分
    if "'jinji':" in line:
        # 查找当前山名
        for j in range(i-1, max(0, i-15), -1):
            if "'name':" in lines[j]:
                shan_name = lines[j].split("'")[1]
                if shan_name in scores_data:
                    score, usable = scores_data[shan_name]
                    indent = " " * 16
                    new_lines.append(f"{indent}'score': {score},  # 吉凶评分\n")
                    new_lines.append(f"{indent}'usable': {usable}\n")
                break

# 写入文件
with open('src/engine/douhou_shan_jia_system.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ 已完成二十四山课格评分添加！")
print("\n评分列表：")
for shan, (score, usable) in sorted(scores_data.items()):
    status = "✓ 可用" if usable else "✗ 不可用"
    print(f"  {shan}: {score}分 - {status}")
