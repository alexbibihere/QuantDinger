"""
从TradingView关注列表获取数据
"""
import requests
import json
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewWatchlistService:
    """TradingView关注列表服务"""

    def __init__(self):
        # 您的TradingView关注列表API
        self.watchlist_url = "https://www.tradingview.com/api/v1/symbols_list/custom/104353945"
        # 使用您提供的cookie
        self.tv_cookie = "cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings=%7B%22analytics%22%3Atrue%2C%22advertising%22%3Atrue%7D; _ga=GA1.1.1784921442.1765155922; g_state=%7B%22i_l%22%3A0%2C%22i_ll%22%3A1765155927489%7D; device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; etg=undefined; cachec=undefined; _sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.1.1765156051..4c428878-38af-4b44-a437-10934a3be912..fb5f8db0-6053-41b3-af01-7f64f5f2292e.1765155920221.18; _ga_YVVRYGL0E0=GS2.1.s1765155921%24o1%24g1%24t1765156051%24j60%24l0%24h0"

    def get_watchlist_symbols(self) -> List[Dict[str, Any]]:
        """
        从关注列表获取币种数据

        Returns:
            币种列表
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': self.tv_cookie,
                'Accept': 'application/json'
            }

            logger.info(f"Fetching watchlist from: {self.watchlist_url}")
            response = requests.get(self.watchlist_url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched watchlist data")

            # 解析关注列表数据
            result = []
            for item in data:
                # 只保留加密货币/USDT交易对
                symbol = item.get('symbol', '')
                if 'USDT' in symbol and item.get('type') in ['crypto', 'bitcoin']:
                    try:
                        # 提取价格数据
                        price_data = {
                            'symbol': symbol,
                            'base_asset': symbol.replace('USDT', '').replace('BINANCE:', '').replace('OKX:', ''),
                            'description': item.get('description', ''),
                            'exchange': item.get('exchange', ''),
                            'type': item.get('type', ''),
                            'price': item.get('price', 0),
                            'change': item.get('change', 0),
                            'change_percentage': item.get('change_percentage', 0),
                            'volume': item.get('volume', 0),
                            'market_cap': item.get('market_cap', 0),
                            'source': 'TradingView Watchlist'
                        }
                        result.append(price_data)
                    except Exception as e:
                        logger.warning(f"Error processing symbol {symbol}: {e}")
                        continue

            logger.info(f"Successfully parsed {len(result)} symbols from watchlist")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching watchlist: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}", exc_info=True)
            return []

    def get_top_gainers_from_watchlist(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从关注列表获取涨幅榜前N

        Args:
            limit: 返回数量

        Returns:
            按涨幅排序的币种列表
        """
        symbols = self.get_watchlist_symbols()

        # 按涨幅排序
        sorted_symbols = sorted(
            symbols,
            key=lambda x: float(x.get('change_percentage', 0)),
            reverse=True
        )

        return sorted_symbols[:limit]


if __name__ == "__main__":
    # 测试代码
    service = TradingViewWatchlistService()

    print("=" * 70)
    print("测试TradingView关注列表API")
    print("=" * 70)

    symbols = service.get_watchlist_symbols()

    print(f"\n✅ 共获取 {len(symbols)} 个币种:")

    # 显示TOP10
    print("\n📊 TOP10涨幅榜:")
    for i, symbol in enumerate(symbols[:10], 1):
        change_pct = symbol.get('change_percentage', 0)
        price = symbol.get('price', 0)
        print(f"{i:2d}. {symbol['symbol']:15} 价格: ${price:10.4f}  涨跌: {change_pct:+6.2f}%")

    print("\n" + "=" * 70)
