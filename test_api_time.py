#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试HAMA分析接口的响应时间"""
import requests
import time
import json

def test_api_response_time():
    url = 'http://localhost:5000/api/gainer-analysis/analyze-symbol'
    headers = {'Content-Type': 'application/json'}

    print("=" * 80)
    print("HAMA分析接口响应时间测试")
    print("=" * 80)

    symbols = ['GMTUSDT', 'SOLUSDT', 'BNBUSDT']

    for symbol in symbols:
        print(f"\n测试 {symbol}:")

        # 强制刷新(无缓存)
        print("  [1/2] 强制刷新 (无缓存):")
        data = {'symbol': symbol, 'force_refresh': True}

        start_time = time.time()
        response = requests.post(url, json=data, headers=headers, timeout=60)
        end_time = time.time()
        elapsed_time = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 1:
                hama = result['data']['hama_analysis']
                status = hama['technical_indicators']['hama_status']
                recommendation = hama['recommendation']
                print(f"    状态: {status}, 建议: {recommendation}")
                print(f"    响应时间: {elapsed_time:.2f}秒")
            else:
                print(f"    错误: {result.get('msg')}")
                print(f"    响应时间: {elapsed_time:.2f}秒")
        else:
            print(f"    HTTP错误: {response.status_code}")
            print(f"    响应时间: {elapsed_time:.2f}秒")

        # 使用缓存
        print("  [2/2] 使用缓存:")
        data = {'symbol': symbol, 'force_refresh': False}

        start_time = time.time()
        response = requests.post(url, json=data, headers=headers, timeout=60)
        end_time = time.time()
        cached_time = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 1:
                cached = result['data'].get('cached', False)
                print(f"    缓存: {cached}")
                print(f"    响应时间: {cached_time:.2f}秒")
                if elapsed_time > 0:
                    speedup = elapsed_time / cached_time if cached_time > 0 else 0
                    print(f"    加速比: {speedup:.1f}x")
            else:
                print(f"    错误: {result.get('msg')}")
                print(f"    响应时间: {cached_time:.2f}秒")
        else:
            print(f"    HTTP错误: {response.status_code}")
            print(f"    响应时间: {cached_time:.2f}秒")

    print("\n" + "=" * 80)
    print("性能分析:")
    print("=" * 80)
    print("当前瓶颈:")
    print("  1. 获取K线数据 (200根) - 约2-4秒")
    print("  2. 计算HAMA指标 - <1秒")
    print("  3. 获取实时价格 - 约1-2秒")
    print("  4. 网络延迟 - 取决于代理配置")
    print("\n优化方案:")
    print("  1. 减少K线数据量 (200 -> 100)")
    print("  2. 实时价格单独缓存 (1分钟)")
    print("  3. 使用缓存 (当前5分钟)")

if __name__ == '__main__':
    test_api_response_time()
