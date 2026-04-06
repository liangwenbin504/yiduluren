import json

# 检查 v3 文件
with open('bifa_matched_results_v3.json', 'r', encoding='utf-8') as f:
    v3_data = json.load(f)
    
print(f"v3 课例数：{len(v3_data)}")
keys = list(v3_data.keys())[:3]
print(f"前 3 个键：{keys}")
if keys:
    first_key = keys[0]
    print(f"第一个课例的键：{list(v3_data[first_key].keys())}")
