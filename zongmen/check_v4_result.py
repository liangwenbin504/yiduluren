import json

with open('bifa_matched_results_v4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"课例数：{len(data)}")

# 第一个课例
first_key = list(data.keys())[0]
print(f"\n第一个课例：{first_key}")
print(f"日干支：{data[first_key]['ri_gan_zhi']}")
print(f"匹配规则数：{data[first_key]['bifa_matched_count']}")
print(f"宗门：{data[first_key]['zong_men']}")
print(f"格局：{data[first_key]['ke_ti_ge_ju']}")

# 统计
total_rules = sum(r['bifa_matched_count'] for r in data.values())
print(f"\n总匹配规则数：{total_rules}")
print(f"平均每课匹配规则数：{total_rules / len(data):.2f}")
