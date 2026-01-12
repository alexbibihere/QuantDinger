#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用TradingView Scanner API获取GMT数据"""
import requests
import json

def test_tradingview_data():
    print("=" * 70)
    print("TradingView Scanner API - GMTUSDT数据获取")
    print("=" * 70)

    # TradingView Scanner API
    url = "https://scanner.tradingview.com/crypto/scan"

    # 简化请求
    payload = {
        "symbols": {
            "tickers": ["BINANCE:GMTUSDT"]
        },
        "columns": [
            "name",
            "close",
            "change",
            "volume",
            "Recommend.All|1day"
        ]
    }

    print("\n正在从TradingView获取GMTUSDT数据...")

    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            # TradingView返回格式: {"totalCount":1,"data":[{"s":"BINANCE:GMTUSDT","d":[...]}]}
            if 'data' in data and len(data['data']) > 0:
                ticker_data = data['data'][0]
                values = ticker_data.get('d', [])

                print("\n" + "=" * 70)
                print("TradingView数据 (GMTUSDT)")
                print("=" * 70)

                if len(values) >= 4:
                    name = values[0]
                    close = values[1]
                    change = values[2]
                    volume = values[3]
                    recommend = values[4] if len(values) > 4 else None

                    print(f"\n【基本信息】")
                    print(f"  币种: {name}")
                    print(f"  收盘价: ${close:.6f}")
                    print(f"  涨跌幅: {change:.2f}%")
                    print(f"  成交量: {volume:,.0f}")

                    if recommend is not None:
                        print(f"\n【TradingView综合建议(1天)】")
                        print(f"  数值: {recommend:.2f}")

                        if recommend > 0.5:
                            print(f"  建议: 强烈买入")
                        elif recommend > 0:
                            print(f"  建议: 买入")
                        elif recommend < -0.5:
                            print(f"  建议: 强烈卖出")
                        elif recommend < 0:
                            print(f"  建议: 卖出")
                        else:
                            print(f"  建议: 持有")

                    print(f"\n【对比我们的HAMA分析】")
                    print(f"  TradingView: 综合技术指标 (RSI, MACD等)")
                    print(f"  我们的HAMA: 基于MA交叉的hamaCandle.txt逻辑")
                    print(f"  两者的算法和指标完全不同")

                    if recommend is not None:
                        print(f"\n【趋势对比】")
                        if recommend > 0:
                            tv_trend = "看涨"
                        else:
                            tv_trend = "看跌"

                        print(f"  TradingView综合建议: {tv_trend}")
                        print(f"  我们的HAMA分析: 下跌趋势 (SELL)")
                        print(f"  结果: {'一致' if (recommend > 0) == False else '不一致'}")

            else:
                print("\n无数据返回")
        else:
            print(f"\n请求失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"\n错误: {e}")

    print("\n" + "=" * 70)
    print("结论:")
    print("=" * 70)
    print("TradingView Scanner提供的是综合技术分析,不是HAMA指标")
    print("我们的HAMA分析完全基于hamaCandle.txt的MA交叉逻辑")
    print("两者使用不同的算法,所以结果可能不一致")
    print("=" * 70)

if __name__ == '__main__':
    test_tradingview_data()
