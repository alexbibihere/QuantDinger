#!/usr/bin/env python
import sys
sys.path.insert(0, '/app')

from app.services.tradingview_watchlist_with_auth import TradingViewWatchlistWithAuth

print('='*80)
print('测试TradingView自定义关注列表')
print('='*80)

service = TradingViewWatchlistWithAuth()
watchlist = service.get_custom_watchlist()

if watchlist:
    print(f'\n✅ 成功获取 {len(watchlist)} 个币种:\n')
    for i, coin in enumerate(watchlist[:50], 1):
        symbol = coin.get('symbol', 'N/A')
        name = coin.get('name', 'N/A')
        price = coin.get('price', 0)
        print(f'{i:2d}. {symbol:30} {name:20} 价格:{price:>12.2f}')
else:
    print('❌ 未能获取到数据')
