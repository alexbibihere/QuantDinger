#!/usr/bin/env python3
"""测试 Binance WebSocket Ticker 数据"""
import asyncio
import websockets
import json

async def test_binance_ws():
    # 监控 4 个币种
    symbols = ['btcusdt', 'ethusdt', 'bnbusdt', 'solusdt']
    streams = '/'.join(symbols)
    url = f"wss://stream.binance.com:9443/ws/{streams}@ticker"

    print(f"Connecting to: {url}")

    try:
        async with websockets.connect(url, ping_interval=20) as ws:
            print("WebSocket connected")

            # Receive 10 messages
            for i in range(10):
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(message)

                    event_type = data.get('e', 'unknown')
                    symbol = data.get('s', 'N/A')

                    print(f"[{i+1}] Event: {event_type}, Symbol: {symbol}")
                except asyncio.TimeoutError:
                    print("Timeout, no data received")
                    break

            print("Test complete")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_binance_ws())
