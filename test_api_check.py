import requests

# 测试主界面使用的API检查URL
url = 'http://localhost:5000/api/sizhu?year=2026&month=3&day=29&hour=12'
print(f"测试URL: {url}")

try:
    r = requests.get(url, timeout=5)
    print(f"状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"success: {data.get('success')}")
        sizhu = data.get('sizhu', {})
        print(f"年柱: {sizhu.get('yearPillar')}")
        print(f"月柱: {sizhu.get('monthPillar')}")
        print(f"日柱: {sizhu.get('dayPillar')}")
        print(f"时柱: {sizhu.get('hourPillar')}")
    else:
        print(f"错误响应: {r.text}")
except Exception as e:
    print(f"错误: {e}")
