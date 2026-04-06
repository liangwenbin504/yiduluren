import requests

# 测试主界面使用的API检查URL
url = 'http://localhost:5000/api/sizhu?year=2026&month=3&day=29&hour=12'
print(f"测试URL: {url}")

try:
    r = requests.get(url, timeout=5)
    print(f"状态码: {r.status_code}")
    print(f"响应: {r.json()}")
except Exception as e:
    print(f"错误: {e}")
