#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试多个币种的实时价格HAMA分析"""
import requests
import json

def test_symbol(symbol):
    """测试单个币种"""
    try:
        response = requests.post(
            'http://localhost:5000/api/gainer-analysis/analyze-symbol',
            json={'symbol': symbol, 'force_refresh': True},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                hama = data['data']['hama_analysis']
                signals = hama['signals']
                tech = hama['technical_indicators']

                realtime = signals.get('realtime_price')
                ma = signals.get('hama_ma')

                return {
                    'symbol': symbol,
                    'status': tech.get('hama_status', 'N/A'),
                    'recommendation': hama['recommendation'],
                    'realtime_price': realtime,
                    'hama_ma': ma,
                    'trend': '上涨' if realtime and ma and realtime > ma else ('下跌' if realtime and ma and realtime < ma else '持平'),
                    'confidence': f"{hama['confidence']:.2%}"
                }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}

    return {'symbol': symbol, 'error': 'API请求失败'}

def main():
    print("=" * 80)
    print("多币种实时价格HAMA分析测试")
    print("=" * 80)

    symbols = ['GMTUSDT', 'SOLUSDT', 'BNBUSDT', 'BTCUSDT', 'ETHUSDT']

    results = []
    for symbol in symbols:
        print(f"\n正在测试 {symbol}...")
        result = test_symbol(symbol)
        results.append(result)

    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"{'币种':<12} {'状态':<12} {'建议':<8} {'实时价格':<12} {'HAMA MA':<12} {'趋势':<8} {'置信度':<10}")
    print("-" * 80)

    for r in results:
        if 'error' in r:
            print(f"{r['symbol']:<12} 错误: {r['error']}")
        else:
            rp = r['realtime_price']
            ma = r['hama_ma']
            rp_str = f"{rp:.6f}" if rp else 'N/A'
            ma_str = f"{ma:.6f}" if ma else 'N/A'
            print(f"{r['symbol']:<12} {r['status']:<12} {r['recommendation']:<8} {rp_str:<12} {ma_str:<12} {r['trend']:<8} {r['confidence']:<10}")

    print("=" * 80)

if __name__ == '__main__':
    main()
