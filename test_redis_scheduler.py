#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试Redis缓存和定时任务"""
import requests
import json
import time

BASE_URL = 'http://localhost:5000/api/gainer-analysis'


def test_redis_cache():
    """测试Redis缓存"""
    print("=" * 80)
    print("测试 Redis 缓存")
    print("=" * 80)

    # 1. 查看缓存统计
    print("\n[1] 查看缓存统计:")
    response = requests.get(f'{BASE_URL}/cache-stats', timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"  缓存类型: {data.get('cache_type', 'N/A')}")
            print(f"  已缓存币种: {data['cached_symbols']}")
            print(f"  缓存有效期: {data['cache_duration_minutes']}分钟")
            if data['cached_symbols'] > 0:
                print(f"  缓存列表: {', '.join(data['symbols'][:10])}...")
        else:
            print(f"  错误: {result.get('msg')}")
    else:
        print(f"  HTTP错误: {response.status_code}")

    # 2. 分析一个币种
    print("\n[2] 分析 BTCUSDT:")
    response = requests.post(
        f'{BASE_URL}/analyze-symbol',
        json={'symbol': 'BTCUSDT'},
        headers={'Content-Type': 'application/json'},
        timeout=60
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            cache_source = data.get('cache_source', 'N/A')
            print(f"  成功! 数据来源: {cache_source}")
            hama = data['hama_analysis']
            rec = hama['recommendation']
            print(f"  建议: {rec}")
        else:
            print(f"  错误: {result.get('msg')}")
    else:
        print(f"  HTTP错误: {response.status_code}")

    # 3. 再次查看缓存统计
    print("\n[3] 再次查看缓存统计:")
    response = requests.get(f'{BASE_URL}/cache-stats', timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"  已缓存币种: {data['cached_symbols']}")

    print()


def test_scheduler_status():
    """测试定时任务状态"""
    print("=" * 80)
    print("测试定时任务状态")
    print("=" * 80)

    response = requests.get(f'{BASE_URL}/scheduler/status', timeout=10)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"\n状态:")
            print(f"  运行中: {data['running']}")
            print(f"  币种数: {data['symbols_count']}")
            print(f"  刷新间隔: {data['interval_minutes']}分钟")
            cache_stats = data.get('cache_stats', {})
            print(f"  缓存可用: {cache_stats.get('available', False)}")
            print(f"  已缓存币种: {cache_stats.get('cached_symbols', 0)}")
        else:
            print(f"\n错误: {result.get('msg')}")
    else:
        print(f"\nHTTP错误: {response.status_code}")

    print()


def test_start_scheduler():
    """测试启动定时任务"""
    print("=" * 80)
    print("测试启动定时任务")
    print("=" * 80)

    # 只测试3个币种
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

    print(f"\n启动定时任务 (测试3个币种):")
    response = requests.post(
        f'{BASE_URL}/scheduler/start',
        json={
            'symbols': symbols,
            'interval_minutes': 5
        },
        headers={'Content-Type': 'application/json'},
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"\n成功!")
            print(f"  状态: {data['status']}")
            print(f"  币种数: {data['symbols_count']}")
            print(f"  刷新间隔: {data['interval_minutes']}分钟")
            cache_stats = data.get('cache_stats', {})
            print(f"  已缓存: {cache_stats.get('cached_symbols', 0)}")
        else:
            print(f"\n错误: {result.get('msg')}")
    else:
        print(f"\nHTTP错误: {response.status_code}")

    print()


def test_stop_scheduler():
    """测试停止定时任务"""
    print("=" * 80)
    print("测试停止定时任务")
    print("=" * 80)

    response = requests.post(f'{BASE_URL}/scheduler/stop', timeout=10)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"\n成功!")
            print(f"  状态: {data['status']}")
        else:
            print(f"\n错误: {result.get('msg')}")
    else:
        print(f"\nHTTP错误: {response.status_code}")

    print()


def test_cache_performance():
    """测试缓存性能"""
    print("=" * 80)
    print("测试缓存性能")
    print("=" * 80)

    symbol = 'BTCUSDT'

    # 第一次请求(无缓存)
    print(f"\n[1] 第一次请求 {symbol} (无缓存):")
    start = time.time()
    response = requests.post(
        f'{BASE_URL}/analyze-symbol',
        json={'symbol': symbol, 'force_refresh': True},
        headers={'Content-Type': 'application/json'},
        timeout=60
    )
    first_time = time.time() - start

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"  响应时间: {first_time:.2f}秒")
            print(f"  数据来源: {data.get('cache_source', 'N/A')}")

    # 第二次请求(有缓存)
    print(f"\n[2] 第二次请求 {symbol} (有缓存):")
    start = time.time()
    response = requests.post(
        f'{BASE_URL}/analyze-symbol',
        json={'symbol': symbol},
        headers={'Content-Type': 'application/json'},
        timeout=60
    )
    cached_time = time.time() - start

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            cache_source = data.get('cache_source', 'N/A')
            print(f"  响应时间: {cached_time:.2f}秒")
            print(f"  数据来源: {cache_source}")

            if first_time > 0:
                speedup = first_time / cached_time if cached_time > 0 else 0
                print(f"\n  加速比: {speedup:.1f}x")
                print(f"  节省时间: {first_time - cached_time:.2f}秒")

    print()


def main():
    print("\n" + "=" * 80)
    print("Redis缓存和定时任务测试套件")
    print("=" * 80 + "\n")

    # 1. 测试缓存状态
    test_redis_cache()

    # 2. 测试定时任务状态
    test_scheduler_status()

    # 3. 测试缓存性能
    test_cache_performance()

    # 4. 测试启动定时任务 (可选)
    # test_start_scheduler()

    # 5. 测试停止定时任务 (可选)
    # test_stop_scheduler()

    print("=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
