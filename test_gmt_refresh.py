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

        print("=" * 70)
        print("GMTUSDT 最新HAMA分析 (force_refresh)")
        print("=" * 70)
        print(f"HAMA Close: {signals['ha_close']:.6f}")
        print(f"HAMA MA: {signals['hama_ma']:.6f}")
        print(f"状态: {hama['technical_indicators']['hama_status']}")
        print(f"建议: {hama['recommendation']}")
        print(f"置信度: {hama['confidence']:.2%}")
        print(f"偏离度: {signals['deviation_pct']:.2f}%")
        print(f"最后交叉: {signals['last_cross_direction']}")

        print(f"\n对比TradingView:")
        print(f"TradingView价格: $0.019420 (+19.80%)")
        print(f"我们的HAMA Close: {signals['ha_close']:.6f}")
        print(f"差异: {(0.019420 - signals['ha_close']):.6f}")
        print("=" * 70)
