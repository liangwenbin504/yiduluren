import json
import os

print(f"当前目录：{os.getcwd()}")
print(f"文件路径：{os.path.exists('data/720_ke_li_jiu_zong_men.json')}")

with open('data/720_ke_li_jiu_zong_men.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)

print(f"总键数：{len(all_data)}")
print(f"metadata: {'metadata' in all_data}")

# 过滤掉 metadata
ke_li_data = {k: v for k, v in all_data.items() if k != 'metadata'}
print(f"课例数：{len(ke_li_data)}")

# 检查第一个课例
if ke_li_data:
    first_key = list(ke_li_data.keys())[0]
    print(f"\n第一个课例：{first_key}")
    print(f"课例类型：{type(ke_li_data[first_key])}")
