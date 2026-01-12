#!/usr/bin/env python3
"""测试 SSE 接收的币种数量"""
import requests
import json
import time

def test_sse_symbols():
    url = "http://localhost:8888/api/sse/prices"
    symbols_received = set()

    print(f"Connecting to: {url}")
    print("Listening for 20 seconds...\n")

    try:
        with requests.get(url, stream=True, timeout=None) as response:
            response.raise_for_status()

            start_time = time.time()
            line_count = 0

            for line in response.iter_lines(decode_unicode=True):
                if time.time() - start_time > 20:
                    break

                if line:
                    line_count += 1

                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:].strip())
                            symbol = data.get('symbol', 'N/A')
                            price = data.get('price', 0)
                            change24h = data.get('change24h', 0)

                            if symbol != 'N/A':
                                symbols_received.add(symbol)
                                print(f"[{line_count}] {symbol}: ${price} ({change24h:.2f}%)")
                        except:
                            pass

        print(f"\n=== Summary ===")
        print(f"Total messages: {line_count}")
        print(f"Unique symbols: {len(symbols_received)}")
        print(f"Symbols: {', '.join(sorted(symbols_received))}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_sse_symbols()
