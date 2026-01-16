#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 HAMA Market API

使用方法:
python test_hama_market_api.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    response = requests.get(f"{BASE_URL}/api/hama-market/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_watchlist():
    """测试监控列表（默认币种）"""
    print_section("2. 获取监控列表（默认10个币种）")
    response = requests.get(f"{BASE_URL}/api/hama-market/watchlist")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应摘要:")
    if data.get('success'):
        watchlist = data.get('data', {}).get('watchlist', [])
        print(f"  - 监控币种数量: {len(watchlist)}")
        if watchlist:
            print(f"  - 第一个币种: {watchlist[0].get('symbol')}")
            print(f"  - 价格: {watchlist[0].get('price')}")
            print(f"  - HAMA颜色: {watchlist[0].get('hama', {}).get('color')}")
    print(f"\n完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_custom_watchlist():
    """测试自定义监控列表"""
    print_section("3. 获取自定义监控列表（BTCUSDT, ETHUSDT）")
    response = requests.get(
        f"{BASE_URL}/api/hama-market/watchlist",
        params={'symbols': 'BTCUSDT,ETHUSDT'}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应摘要:")
    if data.get('success'):
        watchlist = data.get('data', {}).get('watchlist', [])
        print(f"  - 监控币种数量: {len(watchlist)}")
        for item in watchlist:
            print(f"  - {item.get('symbol')}: 价格={item.get('price')}, "
                  f"趋势={item.get('trend', {}).get('direction')}")
    print(f"\n完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_single_symbol():
    """测试单个币种"""
    print_section("4. 获取单个币种 HAMA 指标（BTCUSDT）")
    response = requests.get(
        f"{BASE_URL}/api/hama-market/symbol",
        params={'symbol': 'BTCUSDT', 'interval': '15m', 'limit': 500}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_signals():
    """测试信号列表"""
    print_section("5. 获取信号列表（默认币种）")
    response = requests.get(f"{BASE_URL}/api/hama-market/signals")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应摘要:")
    if data.get('success'):
        signals = data.get('data', {}).get('signals', [])
        print(f"  - 信号数量: {len(signals)}")
        for signal in signals:
            print(f"  - {signal.get('symbol')}: {signal.get('signal_type')} 信号, "
                  f"价格={signal.get('price')}")
    print(f"\n完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_hot_symbols():
    """测试热门币种列表"""
    print_section("6. 获取热门币种列表")
    response = requests.get(f"{BASE_URL}/api/hama-market/hot-symbols")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应摘要:")
    if data.get('success'):
        symbols = data.get('data', {}).get('symbols', [])
        print(f"  - 热门币种数量: {len(symbols)}")
        print(f"  - 前10个币种: {symbols[:10]}")
    print(f"\n完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("  HAMA Market API 测试")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # 1. 健康检查
        test_health()

        # 2. 监控列表（默认）
        test_watchlist()

        # 3. 自定义监控列表
        test_custom_watchlist()

        # 4. 单个币种
        test_single_symbol()

        # 5. 信号列表
        test_signals()

        # 6. 热门币种
        test_hot_symbols()

        print("\n" + "=" * 80)
        print("  测试完成！")
        print("=" * 80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] 连接失败！")
        print("请确保后端服务正在运行: http://localhost:5000")
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")

if __name__ == '__main__':
    main()
