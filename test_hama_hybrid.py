#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HAMA指标混合获取模式
"""
import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

# API基础URL
BASE_URL = "http://localhost:5000/api/tradingview-selenium"


def test_hybrid_single():
    """测试混合模式单个币种"""
    print("=" * 80)
    print("测试1: 混合模式获取单个币种")
    print("=" * 80)

    symbol = "BTCUSDT"
    url = f"{BASE_URL}/hama-hybrid/{symbol}?interval=15&use_selenium=false&force_refresh=false"

    print(f"\n请求: GET {url}")
    print("-" * 80)

    start = time.time()
    try:
        response = requests.get(url, timeout=60)
        elapsed = time.time() - start

        print(f"状态码: {response.status_code}")
        print(f"耗时: {elapsed:.2f}秒")

        if response.status_code == 200:
            data = response.json()
            print(f"\n成功:\n")

            result = data.get('data', {})
            print(f"币种: {result.get('symbol')}")
            print(f"来源: {result.get('source', 'unknown')}")
            print(f"缓存: {result.get('cached', False)}")
            print(f"计算耗时: {result.get('calculation_time', 0):.2f}秒")
            print(f"\nHAMA状态:")
            hama_status = result.get('hama_status', {})
            print(f"  趋势: {hama_status.get('trend')}")
            print(f"  状态: {hama_status.get('status_text')}")
            print(f"  关系: {hama_status.get('candle_ma_relation')}")
            print(f"\nMA100: {result.get('ma100')}")
            print(f"HAMA收盘: {result.get('hama_candles', {}).get('close')}")
            print(f"\n交叉信号:")
            cross = result.get('cross_signal', {})
            print(f"  信号: {cross.get('signal')}")
            print(f"  方向: {cross.get('direction')}")
        else:
            print(f"\n失败:")
            print(response.text)

    except Exception as e:
        print(f"\n错误: {e}")


def test_hybrid_batch():
    """测试混合模式批量获取"""
    print("\n" + "=" * 80)
    print("测试2: 混合模式批量获取(并行)")
    print("=" * 80)

    url = f"{BASE_URL}/hama-hybrid/batch"

    payload = {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
        "interval": "15",
        "use_selenium": False,
        "max_parallel": 3
    }

    print(f"\n请求: POST {url}")
    print(f"Body: {json.dumps(payload, indent=2)}")
    print("-" * 80)

    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=120)
        elapsed = time.time() - start

        print(f"状态码: {response.status_code}")
        print(f"总耗时: {elapsed:.2f}秒")

        if response.status_code == 200:
            data = response.json()
            print(f"\n成功:")
            print(f"  总数: {data.get('total', 0)}")
            print(f"  成功: {data.get('count', 0)}")
            print(f"  失败: {data.get('failed', 0)}")
            print(f"\n币种列表:")

            for item in data.get('data', []):
                print(f"  - {item.get('symbol')}: {item.get('hama_status', {}).get('status_text')} "
                      f"(来源: {item.get('source', 'unknown')}, "
                      f"耗时: {item.get('calculation_time', 0):.2f}s)")
        else:
            print(f"\n失败:")
            print(response.text)

    except Exception as e:
        print(f"\n错误: {e}")


def test_backend_vs_selenium():
    """对比后端计算和Selenium的速度"""
    print("\n" + "=" * 80)
    print("测试3: 对比后端计算 vs Selenium")
    print("=" * 80)

    symbol = "BTCUSDT"

    # 测试1: 后端计算
    print(f"\n[后端计算] {symbol}")
    print("-" * 80)

    url_backend = f"{BASE_URL}/hama-hybrid/{symbol}?interval=15&use_selenium=false&force_refresh=true"

    start = time.time()
    try:
        response = requests.get(url_backend, timeout=60)
        elapsed_backend = time.time() - start

        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {})
            print(f"✅ 成功")
            print(f"   来源: {result.get('source')}")
            print(f"   耗时: {elapsed_backend:.2f}秒")
        else:
            print(f"❌ 失败")
            elapsed_backend = None
    except Exception as e:
        print(f"❌ 错误: {e}")
        elapsed_backend = None

    # 测试2: Selenium (如果可用)
    print(f"\n[Selenium] {symbol}")
    print("-" * 80)

    url_selenium = f"{BASE_URL}/hama-hybrid/{symbol}?interval=15&use_selenium=true"

    start = time.time()
    try:
        response = requests.get(url_selenium, timeout=120)
        elapsed_selenium = time.time() - start

        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {})
            print(f"✅ 成功")
            print(f"   来源: {result.get('source')}")
            print(f"   耗时: {elapsed_selenium:.2f}秒")
        else:
            print(f"❌ 失败: {response.text}")
            elapsed_selenium = None
    except Exception as e:
        print(f"❌ 错误: {e}")
        elapsed_selenium = None

    # 对比结果
    print(f"\n[速度对比]")
    print("-" * 80)
    if elapsed_backend and elapsed_selenium:
        ratio = elapsed_selenium / elapsed_backend
        print(f"后端计算: {elapsed_backend:.2f}秒")
        print(f"Selenium:  {elapsed_selenium:.2f}秒")
        print(f"后端快了 {ratio:.1f} 倍")
    elif elapsed_backend:
        print(f"后端计算: {elapsed_backend:.2f}秒")
        print(f"Selenium:  不可用")
    else:
        print("两种方法都失败了")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HAMA指标混合获取模式测试")
    print("=" * 80)

    # 测试1: 单个币种
    test_hybrid_single()

    # 测试2: 批量获取
    # test_hybrid_batch()

    # 测试3: 速度对比
    # test_backend_vs_selenium()

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)
