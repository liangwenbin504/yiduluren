import requests

# 测试API检查
url = 'http://localhost:5000/api/debug/modules'
print(f"测试URL: {url}")

try:
    r = requests.get(url, timeout=5)
    print(f"状态码: {r.status_code}")
    print(f"响应: {r.json()}")
except Exception as e:
    print(f"错误: {e}")
