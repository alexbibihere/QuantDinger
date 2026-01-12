#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试新的优化API"""
import requests
import json
import time

BASE_URL = 'http://localhost:5000/api/gainer-analysis'

def test_batch_analyze():
    """测试批量分析API"""
    print("=" * 80)
    print("测试批量分析API (analyze-batch)")
    print("=" * 80)

    symbols = ['GMTUSDT', 'SOLUSDT', 'BNBUSDT']

    start = time.time()
    response = requests.post(
        f'{BASE_URL}/analyze-batch',
        json={'symbols': symbols, 'force_refresh': True},
        headers={'Content-Type': 'application/json'},
        timeout=120
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            summary = data['summary']

            print(f"\n[OK] 批量分析成功")
            print(f"  总数: {summary['total']}")
            print(f"  成功: {summary['success']}")
            print(f"  失败: {summary['failed']}")
            print(f"  缓存: {summary['cached']}")
            print(f"  总耗时: {elapsed:.2f}秒")
            print(f"  平均: {elapsed/summary['total']:.2f}秒/币种")

            # 显示结果
            for symbol, analysis in data['results'].items():
                if 'error' not in analysis:
                    hama = analysis['hama_analysis']
                    status = hama['technical_indicators'].get('hama_status', 'N/A')
                    rec = hama['recommendation']
                    print(f"  {symbol}: {status} ({rec})")
                else:
                    print(f"  {symbol}: 错误 - {analysis['error']}")
        else:
            print(f"[ERROR] API错误: {result.get('msg')}")
    else:
        print(f"[ERROR] HTTP错误: {response.status_code}")

    print()

def test_cache_stats():
    """测试缓存统计API"""
    print("=" * 80)
    print("测试缓存统计API (cache-stats)")
    print("=" * 80)

    response = requests.get(f'{BASE_URL}/cache-stats', timeout=10)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"\n[OK] 缓存统计成功")
            print(f"  已缓存币种: {data['cached_symbols']}")
            print(f"  缓存有效期: {data['cache_duration_minutes']}分钟")
            print(f"  最早缓存: {data['oldest_cache']}")
            print(f"  最新缓存: {data['newest_cache']}")
            if data['cached_symbols'] > 0:
                print(f"  缓存列表: {', '.join(data['symbols'][:10])}...")
        else:
            print(f"[ERROR] API错误: {result.get('msg')}")
    else:
        print(f"[ERROR] HTTP错误: {response.status_code}")

    print()

def test_preload():
    """测试预加载API(仅测试3个币种)"""
    print("=" * 80)
    print("测试预加载API (preload) - 仅测试3个币种")
    print("=" * 80)

    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

    start = time.time()
    response = requests.post(
        f'{BASE_URL}/preload',
        json={'symbols': symbols},
        headers={'Content-Type': 'application/json'},
        timeout=120
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            print(f"\n[OK] 预加载成功")
            print(f"  总数: {data['total']}")
            print(f"  成功: {data['success']}")
            print(f"  失败: {data['failed']}")
            print(f"  耗时: {data['duration']:.2f}秒")
            if data['failed'] > 0:
                print(f"  失败列表: {data['failed_symbols']}")
        else:
            print(f"[ERROR] API错误: {result.get('msg')}")
    else:
        print(f"[ERROR] HTTP错误: {response.status_code}")

    print()

def test_performance_comparison():
    """性能对比: 单个请求 vs 批量请求"""
    print("=" * 80)
    print("性能对比: 单个请求 vs 批量请求")
    print("=" * 80)

    symbols = ['GMTUSDT', 'SOLUSDT', 'BNBUSDT']

    # 测试1: 单个顺序请求
    print("\n[测试1] 单个顺序请求 (force_refresh=True):")
    start = time.time()
    for symbol in symbols:
        response = requests.post(
            f'{BASE_URL}/analyze-symbol',
            json={'symbol': symbol, 'force_refresh': True},
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 1:
                hama = result['data']['hama_analysis']
                status = hama['technical_indicators'].get('hama_status', 'N/A')
                print(f"  {symbol}: {status}")
    single_time = time.time() - start
    print(f"  总耗时: {single_time:.2f}秒")
    print(f"  平均: {single_time/len(symbols):.2f}秒/币种")

    # 测试2: 批量请求
    print("\n[测试2] 批量请求 (force_refresh=True):")
    start = time.time()
    response = requests.post(
        f'{BASE_URL}/analyze-batch',
        json={'symbols': symbols, 'force_refresh': True},
        headers={'Content-Type': 'application/json'},
        timeout=120
    )
    batch_time = time.time() - start

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 1:
            data = result['data']
            for symbol, analysis in data['results'].items():
                if 'error' not in analysis:
                    hama = analysis['hama_analysis']
                    status = hama['technical_indicators'].get('hama_status', 'N/A')
                    print(f"  {symbol}: {status}")

    print(f"  总耗时: {batch_time:.2f}秒")
    print(f"  平均: {batch_time/len(symbols):.2f}秒/币种")

    # 性能对比
    print(f"\n性能对比:")
    print(f"  批量请求比单个请求快: {single_time/batch_time:.1f}x")
    print(f"  节省时间: {single_time - batch_time:.2f}秒")

    print()

def main():
    print("\n" + "=" * 80)
    print("优化API测试套件")
    print("=" * 80 + "\n")

    # 测试缓存统计
    test_cache_stats()

    # 测试预加载(3个币种)
    test_preload()

    # 测试批量分析
    test_batch_analyze()

    # 性能对比
    test_performance_comparison()

    print("=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
