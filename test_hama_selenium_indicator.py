#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HAMA指标Selenium获取功能
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

# API基础URL
BASE_URL = "http://localhost:5000/api/tradingview-selenium"


def test_single_indicator():
    """测试获取单个币种的HAMA指标"""
    print("=" * 80)
    print("测试1: 获取单个币种的HAMA指标")
    print("=" * 80)

    symbol = "BTCUSDT"
    url = f"{BASE_URL}/hama-indicator/{symbol}?interval=15"

    print(f"\n📊 请求: GET {url}")
    print("-" * 80)

    try:
        response = requests.get(url, timeout=60)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功获取数据:\n")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 请求失败:")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_batch_indicators():
    """测试批量获取多个币种的HAMA指标"""
    print("\n" + "=" * 80)
    print("测试2: 批量获取多个币种的HAMA指标")
    print("=" * 80)

    url = f"{BASE_URL}/hama-indicator/batch"

    payload = {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "15"
    }

    print(f"\n📊 请求: POST {url}")
    print(f"Body: {json.dumps(payload, indent=2)}")
    print("-" * 80)

    try:
        response = requests.post(url, json=payload, timeout=120)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功获取 {data.get('count', 0)} 个币种的数据:\n")
            for item in data.get('data', []):
                print(f"  - {item.get('symbol')}: {item.get('hama_status', {})}")
        else:
            print(f"\n❌ 请求失败:")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_cross_signals():
    """测试从图表页面解析HAMA交叉信号"""
    print("\n" + "=" * 80)
    print("测试3: 从图表页面解析HAMA交叉信号")
    print("=" * 80)

    symbol = "BTCUSDT"
    url = f"{BASE_URL}/hama-cross-signals/{symbol}?interval=15"

    print(f"\n📊 请求: GET {url}")
    print("-" * 80)

    try:
        response = requests.get(url, timeout=60)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功解析数据:\n")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 请求失败:")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_selenium_status():
    """测试Selenium状态"""
    print("\n" + "=" * 80)
    print("测试0: 检查Selenium/Chromium状态")
    print("=" * 80)

    url = f"{BASE_URL}/test"

    print(f"\n📊 请求: GET {url}")
    print("-" * 80)

    try:
        response = requests.get(url, timeout=30)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Selenium状态正常:\n")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ Selenium状态异常:")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HAMA指标Selenium获取功能测试")
    print("=" * 80)

    # 首先检查Selenium状态
    test_selenium_status()

    # 测试单个币种
    test_single_indicator()

    # 测试批量获取 (注释掉,避免耗时过长)
    # test_batch_indicators()

    # 测试交叉信号解析 (注释掉,避免耗时过长)
    # test_cross_signals()

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)
