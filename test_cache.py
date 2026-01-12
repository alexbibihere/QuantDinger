#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试HAMA分析缓存功能"""
import requests
import time

def test_cache():
    url = 'http://localhost:5000/api/gainer-analysis/analyze-symbol'
    headers = {'Content-Type': 'application/json'}
    symbol = 'BNBUSDT'

    print("=" * 60)
    print("HAMA分析缓存功能测试")
    print("=" * 60)

    # 第1次请求 - 应该从API获取
    print(f"\n[第1次请求] 首次获取 {symbol} 的HAMA分析...")
    start_time = time.time()
    response1 = requests.post(url, json={'symbol': symbol}, headers=headers)
    elapsed1 = (time.time() - start_time) * 1000

    if response1.status_code == 200:
        data1 = response1.json()
        cached1 = data1.get('data', {}).get('cached', False)
        msg1 = data1.get('msg', '')
        print(f"  状态: {msg1}")
        print(f"  是否缓存: {cached1}")
        print(f"  响应时间: {elapsed1:.2f}ms")
    else:
        print(f"  错误: {response1.status_code}")
        return

    # 等待1秒
    time.sleep(1)

    # 第2次请求 - 应该从缓存获取
    print(f"\n[第2次请求] 再次获取 {symbol} 的HAMA分析 (应该从缓存)...")
    start_time = time.time()
    response2 = requests.post(url, json={'symbol': symbol}, headers=headers)
    elapsed2 = (time.time() - start_time) * 1000

    if response2.status_code == 200:
        data2 = response2.json()
        cached2 = data2.get('data', {}).get('cached', False)
        msg2 = data2.get('msg', '')
        print(f"  状态: {msg2}")
        print(f"  是否缓存: {cached2}")
        print(f"  响应时间: {elapsed2:.2f}ms")
    else:
        print(f"  错误: {response2.status_code}")
        return

    # 等待1秒
    time.sleep(1)

    # 第3次请求 - 强制刷新
    print(f"\n[第3次请求] 强制刷新 {symbol} 的HAMA分析...")
    start_time = time.time()
    response3 = requests.post(url, json={'symbol': symbol, 'force_refresh': True}, headers=headers)
    elapsed3 = (time.time() - start_time) * 1000

    if response3.status_code == 200:
        data3 = response3.json()
        cached3 = data3.get('data', {}).get('cached', False)
        msg3 = data3.get('msg', '')
        print(f"  状态: {msg3}")
        print(f"  是否缓存: {cached3}")
        print(f"  响应时间: {elapsed3:.2f}ms")
    else:
        print(f"  错误: {response3.status_code}")
        return

    # 结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    print(f"第1次 (无缓存): {elapsed1:.2f}ms")
    print(f"第2次 (有缓存): {elapsed2:.2f}ms")
    print(f"第3次 (强制刷新): {elapsed3:.2f}ms")

    speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
    print(f"\n加速比: {speedup:.1f}x")

    if cached2 and elapsed2 < 100:
        print("\n[SUCCESS] 缓存功能正常工作!")
    else:
        print("\n[WARNING] 缓存功能可能未生效")

    print("=" * 60)

if __name__ == '__main__':
    test_cache()
