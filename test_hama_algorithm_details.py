#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析GMT的HAMA计算过程
与TradingView hamaCandle指标对比
"""
import requests
from datetime import datetime

def main():
    print("=" * 70)
    print("GMTUSDT HAMA分析详细报告")
    print("与TradingView hamaCandle.txt指标对比")
    print("=" * 70)

    # 获取HAMA分析
    response = requests.post(
        'http://localhost:5000/api/gainer-analysis/analyze-symbol',
        json={'symbol': 'GMTUSDT', 'force_refresh': True},
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        print(f"API请求失败: {response.status_code}")
        return

    data = response.json()
    if data.get('code') != 1:
        print(f"分析失败: {data.get('msg')}")
        return

    hama = data['data']['hama_analysis']
    signals = hama['signals']
    tech = hama['technical_indicators']

    print(f"\n当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析时间: {data['data']['timestamp']}")

    print(f"\n" + "=" * 70)
    print("HAMA分析结果 (基于hamaCandle.txt算法)")
    print("=" * 70)

    print(f"\n【最终结果】")
    print(f"  状态: {tech['hama_status']}")
    print(f"  建议: {hama['recommendation']}")
    print(f"  置信度: {hama['confidence']:.2%}")
    print(f"  分析笔记: {hama['analysis_note']}")

    print(f"\n【关键指标】")
    print(f"  HAMA Close: {signals['ha_close']:.6f}")
    print(f"  HAMA MA(55 WMA): {signals['hama_ma']:.6f}")

    diff_percent = (signals['ha_close'] / signals['hama_ma'] - 1) * 100
    print(f"  价格差异: {signals['ha_close'] - signals['hama_ma']:.6f} ({diff_percent:.2f}%)")
    print(f"  偏离度: {signals['deviation_pct']:.2f}%")
    print(f"  最后交叉方向: {signals['last_cross_direction']} (1=上穿, -1=下穿, 0=无)")

    print(f"\n【hamaCandle.txt逻辑判断】")
    print(f"  步骤1: 检查HAMA蜡烛与MA的位置")
    if signals['ha_close'] > signals['hama_ma']:
        print(f"    => 蜡烛在MA之上 (高于{diff_percent:.2f}%)")
    else:
        print(f"    => 蜡烛在MA之下 (低于{diff_percent:.2f}%)")

    print(f"  步骤2: 检查偏离度")
    if signals['deviation_pct'] >= 0.1:
        print(f"    => 偏离度{signals['deviation_pct']:.2f}% >= 0.1% (满足条件)")
    else:
        print(f"    => 偏离度{signals['deviation_pct']:.2f}% < 0.1% (不满足)")

    print(f"  步骤3: 判断趋势状态")
    cross_dir = signals['last_cross_direction']
    ha_close = signals['ha_close']
    hama_ma = signals['hama_ma']
    deviation = signals['deviation_pct']

    maintain_bullish = (cross_dir == 1 and ha_close >= hama_ma and deviation >= 0.1)
    maintain_bearish = (cross_dir == -1 and ha_close <= hama_ma and deviation >= 0.1)

    print(f"    上涨趋势条件:")
    print(f"      - 最后交叉方向 == 1 (上穿): {cross_dir == 1}")
    print(f"      - 蜡烛Close >= MA: {ha_close >= hama_ma}")
    print(f"      - 偏离度 >= 0.1%: {deviation >= 0.1}")
    print(f"      => 上涨趋势: {maintain_bullish}")

    print(f"\n    下跌趋势条件:")
    print(f"      - 最后交叉方向 == -1 (下穿): {cross_dir == -1}")
    print(f"      - 蜡烛Close <= MA: {ha_close <= hama_ma}")
    print(f"      - 偏离度 >= 0.1%: {deviation >= 0.1}")
    print(f"      => 下跌趋势: {maintain_bearish}")

    print(f"\n    盘整条件:")
    print(f"      - 不满足上涨 AND 不满足下跌")
    print(f"      => 盘整: {not maintain_bullish and not maintain_bearish}")

    print(f"\n【最终判断】")
    if maintain_bullish:
        print(f"  => 结论: 上涨趋势 (BUY)")
        print(f"  => 理由: 最后上穿MA,蜡烛在MA之上,偏离度足够")
    elif maintain_bearish:
        print(f"  => 结论: 下跌趋势 (SELL) [当前状态]")
        print(f"  => 理由: 最后下穿MA,蜡烛在MA之下,偏离度{deviation:.2f}%")
    else:
        print(f"  => 结论: 盘整 (HOLD)")
        print(f"  => 理由: 不满足明确的上涨或下跌条件")

    print(f"\n" + "=" * 70)
    print("与TradingView对比说明")
    print("=" * 70)
    print(f"\n如果TradingView显示GMT为'上涨趋势',可能原因:")
    print(f"  1. 时间差异:")
    print(f"     - 我们的15分钟K线: 已收盘的完整K线")
    print(f"     - TradingView: 可能显示当前正在形成的K线")
    print(f"     - 几十秒的差异可能导致结果不同")
    print(f"\n  2. 数据源差异:")
    print(f"     - 我们: Binance交易所数据")
    print(f"     - TradingView: 可能聚合多个交易所")
    print(f"\n  3. 计算精度:")
    print(f"     - HAMA蜡烛: EMA/WMA的参数可能有微小差异")
    print(f"     - MA周期: 55 WMA的计算方式")
    print(f"\n建议:")
    print(f"  1. 在TradingView上检查GMT的具体数值:")
    print(f"     - HAMA Close的值")
    print(f"     - HAMA MA(55)的值")
    print(f"     - 最后一次交叉的方向和时间")
    print(f"\n  2. 确认TradingView数据源:")
    print(f"     - 是否使用Binance")
    print(f"     - 是否为15分钟周期")
    print(f"\n  3. 确认K线状态:")
    print(f"     - 当前K线是否已经收盘")
    print(f"     - 检查K线的时间戳")

    print(f"\n我们的算法完全基于hamaCandle.txt逻辑:")
    print(f"  - HAMA蜡烛: Open(EMA25), High(EMA20), Low(EMA20), Close(WMA20)")
    print(f"  - HAMA MA: 55周期WMA")
    print(f"  - 交叉检测: 蜡烛Close与MA的交叉")
    print(f"  - 趋势判断: 基于最后交叉方向和价格位置")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
