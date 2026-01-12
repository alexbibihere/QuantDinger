#!/usr/bin/env python3
"""
测试BNBUSDT的HAMA状态(按照hamaCandle.txt的逻辑)
"""
import requests
import json

def main():
    # 测试BNB HAMA分析
    print("=" * 60)
    print("BNBUSDT 15分钟 HAMA状态分析")
    print("=" * 60)

    response = requests.post(
        'http://localhost:5000/api/gainer-analysis/analyze-symbol',
        json={'symbol': 'BNBUSDT'},
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 1:
            hama = data['data']['hama_analysis']
            signals = hama['signals']

            print(f"\n📊 HAMA分析结果:")
            print(f"状态: {hama['technical_indicators']['hama_status']}")
            print(f"建议: {hama['recommendation']}")
            print(f"置信度: {hama['confidence']:.2%}")

            print(f"\n📈 关键指标:")
            print(f"HAMA Close: {signals['ha_close']:.2f}")
            print(f"HAMA MA(55): {signals['hama_ma']:.2f}")
            print(f"偏离度: {signals['deviation_pct']:.2f}%")
            print(f"最后交叉方向: {signals['last_cross_direction']} (1=上穿, -1=下穿)")

            print(f"\n🔍 判断逻辑:")
            ha_close = signals['ha_close']
            hama_ma = signals['hama_ma']
            deviation = signals['deviation_pct']
            cross_dir = signals['last_cross_direction']

            # 判断条件
            maintain_bullish = (cross_dir == 1 and ha_close >= hama_ma and deviation >= 0.1)
            maintain_bearish = (cross_dir == -1 and ha_close <= hama_ma and deviation >= 0.1)

            print(f"蜡烛位置: {'MA之上' if ha_close > hama_ma else 'MA之下'} ({ha_close:.2f} vs {hama_ma:.2f})")
            print(f"偏离度达标: {'✅' if deviation >= 0.1 else '❌'} ({deviation:.2f}% >= 0.1%)")
            print(f"上穿后维持: {'✅' if maintain_bullish else '❌'}")
            print(f"下穿后维持: {'✅' if maintain_bearish else '❌'}")

            print(f"\n📝 说明:")
            if maintain_bullish:
                print("✅ 满足上涨趋势条件")
            elif maintain_bearish:
                print("✅ 满足下跌趋势条件")
            else:
                print("⚪ 不满足明确趋势,判定为盘整")

            print(f"\n💡 分析笔记:")
            print(f"{hama['analysis_note']}")
        else:
            print(f"错误: {data.get('msg')}")
    else:
        print(f"请求失败: {response.status_code}")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
