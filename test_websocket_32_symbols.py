#!/usr/bin/env python3
"""测试 Binance WebSocket 同时监控 32 个币种"""
import asyncio
import websockets
import json

async def test_binance_ws_32_symbols():
    # 监控 32 个币种
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
        'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'ATOMUSDT',
        'UNIUSDT', 'LTCUSDT', 'BCHUSDT', 'FILUSDT',
        'GMTUSDT', 'EGLDUSDT', 'IDUSDT', 'XTZUSDT',
        'FLOWUSDT', '1INCHUSDT', 'NEARUSDT', 'APEUSDT',
        'SANDUSDT', 'MANAUSDT', 'AXSUSDT', 'SHIBUSDT',
        'TRXUSDT', 'ETCUSDT', 'XLMUSDT', 'VETUSDT'
    ]

    # 转换为小写
    streams = [s.lower() for s in symbols]
    url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}@ticker"

    print(f"Connecting to: {url}")
    print(f"Monitoring {len(symbols)} symbols...\n")

    try:
        async with websockets.connect(url, ping_interval=20) as ws:
            print("WebSocket connected successfully!")

            # 统计接收到的币种
            received_symbols = set()

            # 接收 30 条消息
            for i in range(30):
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(message)

                    event_type = data.get('e', 'unknown')
                    symbol = data.get('s', 'N/A')

                    if symbol != 'N/A':
                        received_symbols.add(symbol)

                    print(f"[{i+1}] {symbol}")

                except asyncio.TimeoutError:
                    print("Timeout, waiting for more data...")
                    # 继续等待,不退出
                    continue

            print(f"\n=== Summary ===")
            print(f"Total messages received: {len(received_symbols)}")
            print(f"Unique symbols: {len(received_symbols)}")
            print(f"Symbols: {', '.join(sorted(received_symbols))}")

            if len(received_symbols) == len(symbols):
                print(f"\n✅ SUCCESS! All {len(symbols)} symbols are streaming!")
            else:
                print(f"\n⚠️  Only {len(received_symbols)}/{len(symbols)} symbols received")
                print(f"Missing: {set(symbols) - received_symbols}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_binance_ws_32_symbols())
