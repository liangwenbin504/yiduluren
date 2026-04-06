import json

with open('data/720_ke_li_jiu_zong_men.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"键：{list(data.keys())[:5]}")
print(f"总课例数：{len(data)}")

# 查找第一个非 metadata 的键
for key in data.keys():
    if key != 'metadata':
        print(f"\n第一个课例键：{key}")
        print(f"课例数据：{data[key]}")
        break
