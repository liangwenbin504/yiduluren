#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试 API
"""

import requests

try:
    print("Testing API...")
    response = requests.get('http://localhost:5000/api/doushou/shanjia_wuxing?mountain=壬', timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
