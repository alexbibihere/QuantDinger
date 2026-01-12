"""
TradingView自定义关注列表API
直接使用TradingView API获取用户自定义的watchlist
"""
import requests
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewCustomWatchlist:
    """TradingView自定义关注列表API"""

    def __init__(self):
        self.base_url = "https://www.tradingview.com/api/v1"
        self.session = requests.Session()

        # 设置headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.tradingview.com/',
        })

    def get_custom_watchlist(self, list_id: str = "104353945", unsafe: bool = True) -> List[Dict[str, Any]]:
        """
        获取自定义关注列表

        Args:
            list_id: 关注列表ID (默认从您提供的URL获取)
            unsafe: 是否使用unsafe参数

        Returns:
            币种列表
        """
        try:
            url = f"{self.base_url}/symbols_list/custom/{list_id}/replace/"
            params = {'unsafe': 'true'} if unsafe else {}

            logger.info(f"正在获取自定义关注列表: {url}")

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()

                    if not data:
                        logger.warning("API返回空数据")
                        return []

                    logger.info(f"✅ 成功获取 {len(data)} 个币种")

                    return self._parse_watchlist_data(data)

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")
                    logger.error(f"响应内容: {response.text[:500]}")
                    return []
            else:
                logger.error(f"API请求失败: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return []

        except Exception as e:
            logger.error(f"获取自定义关注列表失败: {e}", exc_info=True)
            return []

    def _parse_watchlist_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """解析关注列表数据"""
        result = []

        try:
            for item in data:
                try:
                    # TradingView API返回的数据格式
                    # 可能包含: symbol, name, description, exchange, etc.
                    symbol = item.get('symbol', '')
                    name = item.get('name', '')
                    description = item.get('description', '')
                    exchange = item.get('exchange', 'Unknown')
                    type_val = item.get('type', '')

                    # 过滤只保留加密货币
                    if 'crypto' in type_val.lower() or 'usdt' in symbol.lower():
                        result.append({
                            'symbol': symbol,
                            'name': name,
                            'description': description or name,
                            'exchange': exchange,
                            'type': type_val,
                            'price': item.get('price', 0),
                            'change': item.get('change', 0),
                            'volume': item.get('volume', 0),
                            'source': 'TradingView Custom Watchlist'
                        })
                except Exception as e:
                    logger.debug(f"解析单个币种失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析关注列表数据失败: {e}")

        return result

    def get_watchlist_with_details(
        self,
        list_id: str = "104353945",
        include_hama: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取关注列表并包含详细信息

        Args:
            list_id: 关注列表ID
            include_hama: 是否包含HAMA指标

        Returns:
            包含详细信息的币种列表
        """
        # 获取基础列表
        watchlist = self.get_custom_watchlist(list_id)

        if not watchlist:
            return []

        # 如果需要HAMA指标
        if include_hama:
            try:
                from app.services.tradingview_service import TradingViewDataService
                tv_service = TradingViewDataService()

                for coin in watchlist:
                    try:
                        symbol = coin['symbol']
                        hama_data = tv_service.get_hama_cryptocurrency_signals(symbol)

                        # 合并HAMA数据
                        coin.update({
                            'hama_trend': hama_data.get('trend'),
                            'hama_pattern': hama_data.get('candle_pattern'),
                            'hama_recommendation': hama_data.get('recommendation'),
                            'hama_confidence': hama_data.get('confidence'),
                        })

                        # 避免请求过快
                        import time
                        time.sleep(0.5)

                    except Exception as e:
                        logger.debug(f"获取{symbol}的HAMA指标失败: {e}")
                        continue

            except Exception as e:
                logger.error(f"导入TradingView服务失败: {e}")

        return watchlist


# 便捷函数
def get_tradingview_custom_watchlist(
    list_id: str = "104353945",
    include_hama: bool = False
) -> List[Dict[str, Any]]:
    """
    获取TradingView自定义关注列表

    Args:
        list_id: 关注列表ID (默认从您提供的URL)
        include_hama: 是否包含HAMA指标

    Returns:
        币种列表
    """
    service = TradingViewCustomWatchlist()
    return service.get_watchlist_with_details(list_id, include_hama)


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("TradingView自定义关注列表测试")
    print("=" * 80)

    # 测试: 获取自定义关注列表
    print("\n测试: 获取自定义关注列表")
    print("-" * 80)

    service = TradingViewCustomWatchlist()
    watchlist = service.get_custom_watchlist()

    if watchlist:
        print(f"\n✅ 成功获取 {len(watchlist)} 个币种:\n")

        for i, coin in enumerate(watchlist, 1):
            print(f"{i:2d}. {coin['symbol']:30} {coin['name']:30} "
                  f"{coin.get('exchange', 'N/A'):15} 价格:{coin.get('price', 0):>10.2f}")
    else:
        print("❌ 未能获取到数据")

    print("\n" + "=" * 80)
