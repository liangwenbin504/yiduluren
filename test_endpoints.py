import requests

print("测试API端点...")

# 测试sizhu端点
try:
    r = requests.get('http://localhost:5000/api/sizhu?year=2026&month=3&day=29&hour=12', timeout=5)
    print(f"sizhu端点: {r.status_code}")
    if r.status_code == 200:
        print(f"响应: {r.json()}")
except Exception as e:
    print(f"sizhu端点错误: {e}")

# 测试health端点
try:
    r = requests.get('http://localhost:5000/api/health', timeout=5)
    print(f"health端点: {r.status_code}")
except Exception as e:
    print(f"health端点错误: {e}")

# 测试full_range_analyze端点
try:
    payload = {
        "mountain": "壬山",
        "start_date": "2026-04-04",
        "end_date": "2026-04-10",
        "max_results": 5
    }
    r = requests.post('http://localhost:5000/api/doushou/full_range_analyze', json=payload, timeout=30)
    print(f"full_range_analyze端点: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"候选数: {result.get('total_candidates')}")
except Exception as e:
    print(f"full_range_analyze端点错误: {e}")
