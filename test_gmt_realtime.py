#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试GMT HAMA分析最新数据"""
import requests
import json

# 强制刷新
response = requests.post(
    'http://localhost:5000/api/gainer-analysis/analyze-symbol',
    json={'symbol': 'GMTUSDT', 'force_refresh': True},
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    data = response.json()
    if data.get('code') == 1:
        hama = data['data']['hama_analysis']
        signals = hama['signals']
        tech = hama['technical_indicators']

        print("=" * 70)
        print("GMTUSDT 最新HAMA分析 (使用实时价格)")
        print("=" * 70)
        print(f"HAMA Close: {signals['ha_close']:.6f}")
        print(f"实时价格: {signals.get('realtime_price', 'N/A')}")
        print(f"HAMA MA: {tech['ma_value']:.6f}")
        print(f"状态: {tech['hama_status']}")
        print(f"建议: {hama['recommendation']}")
        print(f"置信度: {hama['confidence']:.2%}")
        print(f"分析笔记: {hama['analysis_note']}")

        if signals.get('realtime_price'):
            print(f"\n实时价格对比:")
            print(f"  实时价格: {signals['realtime_price']:.6f}")
            print(f"  HAMA MA: {tech['ma_value']:.6f}")
            if signals['realtime_price'] > tech['ma_value']:
                print(f"  => 实时价格 > MA: 上涨趋势")
            else:
                print(f"  => 实时价格 < MA: 下跌趋势")

        print("=" * 70)
