import requests

r = requests.get('http://localhost:5000/api/health')
print(r.status_code)
import json
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
