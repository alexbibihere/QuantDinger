#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试Selenium是否可用
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/tradingview-selenium"

print("=" * 80)
print("测试: Selenium/Chromium状态")
print("=" * 80)

url = f"{BASE_URL}/test"
print(f"\n请求: GET {url}")

try:
    response = requests.get(url, timeout=30)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n成功:\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"\n失败:")
        print(response.text)

except Exception as e:
    print(f"\n错误: {e}")

print("\n" + "=" * 80)
