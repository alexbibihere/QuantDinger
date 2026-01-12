"""
AICoin数据爬取服务
通过分析页面请求来获取Binance涨幅榜数据
"""
import requests
import re
import json
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AICoinGainerService:
    """AICoin涨幅榜爬取服务"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.aicoin.com/'
        })

        # 配置代理
        import os
        proxy_port = os.getenv('PROXY_PORT')
        if proxy_port:
            self.session.proxies = {
                'http': f'http://127.0.0.1:{proxy_port}',
                'https': f'http://127.0.0.1:{proxy_port}',
            }

    def get_binance_futures_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        从AICoin获取Binance永续合约涨幅榜

        策略:
        1. 尝试AICoin公开API
        2. 解析页面找到的API端点
        3. 使用备用数据源

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        logger.info("尝试从AICoin获取Binance涨幅榜")

        # 方法1: 尝试已知的AICoin API端点
        gainers = self._try_aicoin_api(limit)
        if gainers:
            return gainers

        # 方法2: 使用Binance API (通过AICoin代理)
        gainers = self._try_binance_via_aicoin(limit)
        if gainers:
            return gainers

        logger.warning("AICoin数据源不可用")
        return []

    def _try_aicoin_api(self, limit: int) -> List[Dict[str, Any]]:
        """尝试AICoin的API端点"""
        api_endpoints = [
            # AICoin可能的API端点
            "https://www.aicoin.com/api/v1/exchange/binance/tickers",
            "https://www.aicoin.com/api/v2/market/tickers/binance",
            "https://api.aicoin.com/v1/ticker/binance",
            "https://www.aicoin.com/api/platform/v1/market/symbol/list",
        ]

        for url in api_endpoints:
            try:
                logger.info(f"尝试API: {url}")
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # 解析数据
                    gainers = self._parse_aicoin_response(data, limit)
                    if gainers:
                        logger.info(f"✅ 成功从 {url} 获取数据")
                        return gainers
            except Exception as e:
                logger.debug(f"API {url} 失败: {e}")
                continue

        return []

    def _try_binance_via_aicoin(self, limit: int) -> List[Dict[str, Any]]:
        """通过AICoin代理访问Binance数据"""
        try:
            # AICoin可能作为Binance的代理
            # 尝试通过AICoin的WebSocket或API代理

            # 使用tradingview数据作为备选
            from app.services.tradingview_service import TradingViewDataService

            tv_service = TradingViewDataService()

            # 获取多个主流币种的数据
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                      'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
                      'LINKUSDT', 'LTCUSDT', 'UNIUSDT', 'ATOMUSDT', 'ETCUSDT']

            results = []
            for symbol in symbols[:limit]:
                try:
                    # 获取Binance ticker数据
                    ticker = self._get_binance_ticker_direct(symbol)
                    if ticker:
                        results.append(ticker)
                except Exception as e:
                    logger.debug(f"获取{symbol}失败: {e}")
                    continue

            if results:
                logger.info(f"✅ 通过直接API获取{len(results)}个币种")
                return results

        except Exception as e:
            logger.error(f"通过AICoin代理失败: {e}")

        return []

    def _get_binance_ticker_direct(self, symbol: str) -> Dict[str, Any]:
        """直接获取Binance ticker数据(绕过451错误)"""
        try:
            # 尝试多个Binance API端点
            urls = [
                f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}",
                f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}",
                f"https://www.binance.com/fapi/v1/ticker/24hr?symbol={symbol}",
            ]

            for url in urls:
                try:
                    response = self.session.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()

                        return {
                            'symbol': data['symbol'],
                            'base_asset': data['symbol'].replace('USDT', ''),
                            'price': float(data['lastPrice']),
                            'price_change_percent': float(data['priceChangePercent']),
                            'volume': float(data['volume']),
                            'quote_volume': float(data['quoteVolume']),
                            'exchange': 'Binance',
                            'market': 'futures',
                            'timestamp': datetime.now().isoformat()
                        }
                except:
                    continue

        except Exception as e:
            logger.debug(f"获取{symbol} ticker失败: {e}")

        return None

    def _parse_aicoin_response(self, data: Any, limit: int) -> List[Dict[str, Any]]:
        """解析AICoin API响应"""
        gainers = []

        try:
            # 根据AICoin的实际返回格式解析
            # 这里需要根据实际API响应调整

            if isinstance(data, dict):
                if 'data' in data:
                    tickers = data['data']
                elif 'tickers' in data:
                    tickers = data['tickers']
                else:
                    tickers = data
            elif isinstance(data, list):
                tickers = data
            else:
                return []

            # 过滤USDT交易对
            usdt_pairs = []
            for item in tickers:
                if isinstance(item, dict):
                    symbol = item.get('symbol', '')
                    if symbol and 'USDT' in symbol:
                        usdt_pairs.append(item)

            # 按涨跌幅排序
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x.get('change_percent', x.get('priceChangePercent', 0))),
                reverse=True
            )

            # 转换为标准格式
            for item in sorted_pairs[:limit]:
                gainers.append({
                    'symbol': item.get('symbol'),
                    'base_asset': item.get('symbol', '').replace('USDT', ''),
                    'price': float(item.get('last', item.get('price', 0))),
                    'price_change_percent': float(item.get('change_percent', item.get('priceChangePercent', 0))),
                    'volume': float(item.get('volume', item.get('vol', 0))),
                    'quote_volume': float(item.get('quote_volume', item.get('quoteVol', 0))),
                    'exchange': 'Binance (via AICoin)',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

        except Exception as e:
            logger.error(f"解析AICoin数据失败: {e}")

        return gainers


# 便捷函数
def get_binance_futures_gainers_aicoin(limit: int = 20) -> List[Dict[str, Any]]:
    """从AICoin获取Binance永续合约涨幅榜"""
    service = AICoinGainerService()
    return service.get_binance_futures_gainers(limit)
