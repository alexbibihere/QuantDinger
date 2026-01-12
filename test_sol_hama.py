#!/usr/bin/env python3
"""
测试SOLUSDT的HAMA状态(按照hamaCandle.txt的逻辑)
"""
import ccxt
import os
import pandas as pd
import numpy as np

def calculate_hama_candles(df):
    """计算HAMA蜡烛图(与hamaCandle.txt一致)"""
    # Source数据
    df['SourceOpen'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
    df['SourceHigh'] = df[['high', 'close']].max(axis=1)
    df['SourceLow'] = df[['low', 'close']].min(axis=1)
    df['SourceClose'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    # 计算移动平均
    # Open: EMA 25
    df['CandleOpen'] = df['SourceOpen'].ewm(span=25, adjust=False).mean()

    # High: EMA 20
    df['CandleHigh'] = df['SourceHigh'].ewm(span=20, adjust=False).mean()

    # Low: EMA 20
    df['CandleLow'] = df['SourceLow'].ewm(span=20, adjust=False).mean()

    # Close: WMA 20
    def weighted_ma(series, span=20):
        weights = np.arange(1, span + 1)
        return series.rolling(span).apply(
            lambda x: np.dot(x, weights) / weights.sum(),
            raw=True
        )

    df['CandleClose'] = weighted_ma(df['SourceClose'], 20)

    return df

def calculate_hama_ma(df, length=55, ma_type='WMA'):
    """计算HAMA MA线"""
    if ma_type == 'WMA':
        def weighted_ma(series, span=length):
            weights = np.arange(1, span + 1)
            return series.rolling(span).apply(
                lambda x: np.dot(x, weights) / weights.sum(),
                raw=True
            )
        df['ma'] = weighted_ma(df['CandleClose'], length)
    elif ma_type == 'SMA':
        df['ma'] = df['CandleClose'].rolling(window=length).mean()
    elif ma_type == 'EMA':
        df['ma'] = df['CandleClose'].ewm(span=length, adjust=False).mean()

    return df

def determine_hama_status(df):
    """判断HAMA状态(按照hamaCandle.txt的逻辑)"""
    # 计算交叉
    df['cross_up'] = (df['CandleClose'] > df['ma']) & (df['CandleClose'].shift(1) <= df['ma'].shift(1))
    df['cross_down'] = (df['CandleClose'] < df['ma']) & (df['CandleClose'].shift(1) >= df['ma'].shift(1))

    # 跟踪交叉方向
    df['last_cross_direction'] = 0
    last_direction = 0

    for i in range(1, len(df)):
        if df['cross_up'].iloc[i]:
            last_direction = 1
        elif df['cross_down'].iloc[i]:
            last_direction = -1
        df['last_cross_direction'].iloc[i] = last_direction

    # 计算偏离度
    df['deviation_pct'] = np.abs(df['CandleClose'] - df['ma']) / df['ma'] * 100

    # 判断趋势状态
    df['maintain_bullish'] = (df['last_cross_direction'] == 1) & (df['CandleClose'] >= df['ma']) & (df['deviation_pct'] >= 0.1)
    df['maintain_bearish'] = (df['last_cross_direction'] == -1) & (df['CandleClose'] <= df['ma']) & (df['deviation_pct'] >= 0.1)

    # HAMA状态
    df['hama_status'] = '盘整'
    df.loc[df['maintain_bullish'], 'hama_status'] = '上涨趋势'
    df.loc[df['maintain_bearish'], 'hama_status'] = '下跌趋势'

    return df

def main():
    symbol = 'SOLUSDT'

    # 初始化交易所
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'timeout': 10000,
    })

    # 应用代理
    proxy_port = os.getenv('PROXY_PORT')
    if proxy_port:
        exchange.proxies = {
            'http': f'http://127.0.0.1:{proxy_port}',
            'https': f'http://127.0.0.1:{proxy_port}',
        }

    # 获取15分钟K线数据
    print(f"获取 {symbol} 15分钟K线数据...")
    ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=200)

    # 转换为DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    print(f"\n数据范围: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
    print(f"最新价格: {df['close'].iloc[-1]:.2f}")

    # 计算HAMA蜡烛
    print("\n计算HAMA蜡烛图...")
    df = calculate_hama_candles(df)

    # 计算HAMA MA线
    print("计算HAMA MA(55 WMA)线...")
    df = calculate_hama_ma(df, length=55, ma_type='WMA')

    # 判断HAMA状态
    print("判断HAMA状态...")
    df = determine_hama_status(df)

    # 获取最新数据
    latest = df.iloc[-1]

    print("\n" + "="*60)
    print(f"SOLUSDT 15分钟 HAMA状态分析")
    print("="*60)
    print(f"HAMA Close: {latest['CandleClose']:.2f}")
    print(f"HAMA MA(55): {latest['ma']:.2f}")
    print(f"价格偏离: {latest['deviation_pct']:.2f}%")
    print(f"最后交叉方向: {latest['last_cross_direction']} (1=上穿, -1=下穿, 0=无)")
    print(f"\nHAMA状态: {latest['hama_status']}")

    # 颜色
    if latest['hama_status'] == '上涨趋势':
        status_color = "🟢 绿色"
    elif latest['hama_status'] == '下跌趋势':
        status_color = "🔴 红色"
    else:
        status_color = "⚪ 灰色"

    print(f"显示颜色: {status_color}")

    # 最近10根K线的状态
    print("\n最近10根15分钟K线的HAMA状态:")
    print("-" * 60)
    recent = df.tail(10)
    for idx, row in recent.iterrows():
        status_icon = "📈" if row['hama_status'] == '上涨趋势' else ("📉" if row['hama_status'] == '下跌趋势' else "➡️")
        print(f"{row['timestamp'].strftime('%H:%M')} | {row['CandleClose']:>8.2f} | MA:{row['ma']:>8.2f} | {status_icon} {row['hama_status']}")

if __name__ == '__main__':
    main()
