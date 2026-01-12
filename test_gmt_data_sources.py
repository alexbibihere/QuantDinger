#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试不同数据源的GMT HAMA分析"""
import requests
import time

def test_binance_source():
    """测试Binance数据源"""
    print("\n" + "=" * 60)
    print("测试1: Binance数据源 (当前)")
    print("=" * 60)

    start_time = time.time()
    response = requests.post(
        'http://localhost:5000/api/gainer-analysis/analyze-symbol',
        json={'symbol': 'GMTUSDT', 'force_refresh': True},
        headers={'Content-Type': 'application/json'}
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 1:
            hama = data['data']['hama_analysis']
            signals = hama['signals']
            tech = hama['technical_indicators']

            print(f"状态: {tech['hama_status']}")
            print(f"建议: {hama['recommendation']}")
            print(f"置信度: {hama['confidence']:.2%}")
            print(f"HAMA Close: {signals['ha_close']:.6f}")
            print(f"HAMA MA: {signals['hama_ma']:.6f}")
            print(f"偏离度: {signals['deviation_pct']:.2f}%")
            print(f"最后交叉: {signals['last_cross_direction']}")
            print(f"响应时间: {elapsed:.2f}ms")
        else:
            print(f"错误: {data.get('msg')}")
    else:
        print(f"HTTP错误: {response.status_code}")

def test_tradingview_scanner():
    """测试TradingView Scanner数据"""
    print("\n" + "=" * 60)
    print("测试2: TradingView Scanner API")
    print("=" * 60)

    start_time = time.time()
    response = requests.get(
        'https://scanner.tradingview.com/crypto/scan',
        headers={'Content-Type': 'application/json'},
        json={
            "symbols": {"tickers": ["BINANCE:GMTUSDT"], "query": {"types": []}},
            "columns": [
                "name",
                "close",
                "change",
                "volume",
                "Recommend.All|1day"  # 1天综合建议
            ]
        }
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            row = data['data'][0]
            print(f"币种: {row[0]}")
            print(f"价格: {row[1]}")
            print(f"涨跌: {row[2]:.2f}%")
            print(f"成交量: {row[3]}")
            print(f"综合建议(1天): {row[4]}")
            print(f"响应时间: {elapsed:.2f}ms")

            # 综合建议解释
            rec = row[4]
            if rec > 0.5:
                print(f"=> 强烈买入")
            elif rec > 0:
                print(f"=> 买入")
            elif rec < -0.5:
                print(f"=> 强烈卖出")
            elif rec < 0:
                print(f"=>=> 卖出")
            else:
                print(f"=>=> 持有")
        else:
            print(f"无数据")
    else:
        print(f"HTTP错误: {response.status_code}")

    print(f"\n注意: TradingView Scanner提供的是综合技术分析,不是HAMA指标")

def test_binance_api_direct():
    """直接测试Binance API获取最新K线"""
    print("\n" + "=" * 60)
    print("测试3: Binance API直接获取K线")
    print("=" * 60)

    try:
        import ccxt
        import os

        # 配置代理
        proxy_port = os.getenv('PROXY_PORT')
        proxies = None
        if proxy_port:
            proxies = {
                'http': f'http://host.docker.internal:{proxy_port}',
                'https': f'http://host.docker.internal:{proxy_port}'
            }

        exchange = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 10000,
            'proxies': proxies
        })

        start_time = time.time()
        ohlcv = exchange.fetch_ohlcv('GMTUSDT', '15m', limit=5)
        elapsed = (time.time() - start_time) * 1000

        if ohlcv:
            latest = ohlcv[-1]
            print(f"最新15分钟K线:")
            print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest[0]/1000))}")
            print(f"  开盘: {latest[1]:.6f}")
            print(f"  最高: {latest[2]:.6f}")
            print(f"  最低: {latest[3]:.6f}")
            print(f"  收盘: {latest[4]:.6f}")
            print(f"  成交量: {latest[5]:.2f}")

            # 判断涨跌
            change = (latest[4] - latest[1]) / latest[1] * 100
            print(f"  涨跌: {change:.2f}%")
            print(f"  趋势: {'上涨' if change > 0 else '下跌'}")
            print(f"响应时间: {elapsed:.2f}ms")
        else:
            print("无K线数据")
    except Exception as e:
        print(f"错误: {e}")

def main():
    print("=" * 60)
    print("GMT数据源对比测试")
    print("=" * 60)

    # 测试1: Binance (通过我们的HAMA API)
    test_binance_source()

    # 测试2: TradingView Scanner
    # test_tradingview_scanner()  # 可能会被墙,暂时注释

    # 测试3: Binance API直接获取
    test_binance_api_direct()

    print("\n" + "=" * 60)
    print("总结:")
    print("=" * 60)
    print("1. Binance HAMA分析: 基于HAMA蜡烛图和MA交叉逻辑")
    print("2. TradingView Scanner: 综合技术指标(RSI, MACD等)")
    print("3. 两者算法不同,结果可能不一致")
    print("4. 我们使用的是hamaCandle.txt的HAMA逻辑")
    print("=" * 60)

if __name__ == '__main__':
    main()
