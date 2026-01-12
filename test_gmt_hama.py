#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GMT HAMA分析详细报告"""
import requests
import json

def main():
    print("=" * 60)
    print("GMTUSDT 15分钟 HAMA分析详细报告")
    print("=" * 60)

    # 强制刷新获取最新数据
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

            print(f"\nHAMA分析结果:")
            print(f"  状态: {tech['hama_status']}")
            print(f"  建议: {hama['recommendation']}")
            print(f"  置信度: {hama['confidence']:.2%}")
            print(f"  偏离度: {signals['deviation_pct']:.2f}%")

            print(f"\n关键数据:")
            print(f"  HAMA Close: {signals['ha_close']:.6f}")
            print(f"  HAMA MA(55): {signals['hama_ma']:.6f}")
            print(f"  价格差异: {signals['ha_close'] - signals['hama_ma']:.6f}")
            print(f"  最后交叉方向: {signals['last_cross_direction']} (1=上穿, -1=下穿)")

            print(f"\n判断逻辑:")
            ha_close = signals['ha_close']
            hama_ma = signals['hama_ma']
            deviation = signals['deviation_pct']
            cross_dir = signals['last_cross_direction']

            # 判断条件
            maintain_bullish = (cross_dir == 1 and ha_close >= hama_ma and deviation >= 0.1)
            maintain_bearish = (cross_dir == -1 and ha_close <= hama_ma and deviation >= 0.1)

            print(f"  蜡烛位置: {'MA之上' if ha_close > hama_ma else 'MA之下'}")
            print(f"  价格对比: {ha_close:.6f} vs {hama_ma:.6f}")
            print(f"  偏离度: {deviation:.2f}% {'>= 0.1% OK' if deviation >= 0.1 else '< 0.1%'}")
            print(f"  上涨趋势条件: {maintain_bullish}")
            print(f"  下跌趋势条件: {maintain_bearish}")

            print(f"\n结论:")
            if maintain_bullish:
                print(f"  => 满足上涨趋势条件")
            elif maintain_bearish:
                print(f"  => 满足下跌趋势条件 (当前状态)")
            else:
                print(f"  => 不满足明确趋势,判定为盘整")

            print(f"\n注意:")
            print(f"  - 基于最新200根15分钟K线数据")
            print(f"  - HAMA算法与hamaCandle.txt一致")
            print(f"  - 如果与TradingView不一致,可能是时间点或数据源差异")
        else:
            print(f"错误: {data.get('msg')}")
    else:
        print(f"请求失败: {response.status_code}")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
