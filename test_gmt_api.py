#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试GMT HAMA分析API"""
import requests
import json

def test_gmt_api():
    print("=" * 70)
    print("测试GMTUSDT HAMA分析API")
    print("=" * 70)

    try:
        response = requests.post(
            'http://localhost:5000/api/gainer-analysis/analyze-symbol',
            json={'symbol': 'GMTUSDT', 'force_refresh': True},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"\nHTTP状态码: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n响应数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"\n解析JSON失败: {e}")
                print(f"原始响应: {response.text[:500]}")
        else:
            print(f"请求失败: {response.text[:500]}")

    except Exception as e:
        print(f"\n错误: {e}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_gmt_api()
