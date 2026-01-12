"""
币安涨幅榜数据爬取服务
支持使用TradingView API获取涨幅榜数据
"""
import requests
import os
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BinanceGainerService:
    """币安涨幅榜数据服务"""

    def __init__(self):
        self.base_url = "https://www.binance.com"
        self.futures_url = "https://fapi.binance.com"
        self._spot_url = "https://api.binance.com"
        # TradingView Scanner API
        self.tv_scan_url = "https://scanner.tradingview.com/crypto/scan"
        # TradingView cookie (使用用户提供的cookie)
        self.tv_cookie = "cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings=%7B%22analytics%22%3Atrue%2C%22advertising%22%3Atrue%7D; _ga=GA1.1.1784921442.1765155922; g_state=%7B%22i_l%22%3A0%2C%22i_ll%22%3A1765155927489%7D; device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; etg=undefined; cachec=undefined; _sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.1.1765156051..4c428878-38af-4b44-a437-10934a3be912..fb5f8db0-6053-41b3-af01-7f64f5f2292e.1765155920221.18; _ga_YVVRYGL0E0=GS2.1.s1765155921%24o1%24g1%24t1765156051%24j60%24l0%24h0"

        # 配置代理
        self.proxies = self._get_proxies()
        if self.proxies:
            logger.info(f"Using proxy: {self.proxies}")

    def _get_proxies(self):
        """获取代理配置"""
        # 优先使用PROXY_URL
        proxy_url = os.getenv('PROXY_URL')
        if proxy_url:
            return {
                'http': proxy_url,
                'https': proxy_url
            }

        # 从PROXY_PORT构建
        proxy_port = os.getenv('PROXY_PORT')
        if proxy_port:
            proxy_scheme = os.getenv('PROXY_SCHEME', 'socks5h')
            proxy_host = os.getenv('PROXY_HOST', '127.0.0.1')
            proxy_url = f"{proxy_scheme}://{proxy_host}:{proxy_port}"
            return {
                'http': proxy_url,
                'https': proxy_url
            }

        # 使用标准环境变量
        for key in ['ALL_PROXY', 'HTTPS_PROXY', 'HTTP_PROXY']:
            proxy_url = os.getenv(key)
            if proxy_url:
                return {
                    'http': proxy_url,
                    'https': proxy_url
                }

        return None

    def get_top_gainers(self, limit: int = 20, market_type: str = 'spot') -> List[Dict[str, Any]]:
        """
        获取涨幅榜前 N 的币种
        优先使用TradingView API,失败时回退到Binance API

        Args:
            limit: 返回数量，默认 20
            market_type: 市场类型，'spot' 或 'futures'

        Returns:
            币种列表，每个包含 symbol, name, changePercent, volume 等信息
        """
        # 先尝试使用TradingView API
        result = self._get_top_gainers_from_tradingview(limit)
        if result:
            return result

        # 回退到Binance API
        logger.info("Falling back to Binance API")
        if market_type == 'futures':
            return self.get_top_gainers_futures(limit)
        return self._get_top_gainers_from_binance(limit)

    def _get_top_gainers_from_tradingview(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        使用TradingView Scanner API获取涨幅榜

        Args:
            limit: 返回数量

        Returns:
            币种列表
        """
        try:
            # 准备请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': self.tv_cookie,
                'Content-Type': 'application/json'
            }

            # 构建请求体 - 获取所有加密货币按涨跌幅排序
            payload = {
                "filter": [],
                "options": {
                    "lang": "en",
                    "active_symbols_only": True
                },
                "symbols": {
                    "query": {
                        "types": []
                    },
                    "tickers": []
                },
                "columns": [
                    "name",
                    "close",
                    "change",
                    "change_abs",
                    "high",
                    "low",
                    "volume",
                    "market_cap_calc",
                    "recommendation",
                    "type",
                    "description"
                ],
                "sort": {
                    "sortBy": "change",
                    "sortOrder": "desc"
                },
                "range": [0, limit * 3]
            }

            response = requests.post(
                self.tv_scan_url,
                json=payload,
                headers=headers,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            if not data.get('data'):
                logger.error("No data from TradingView")
                return []

            # 解析数据
            result = []
            for item in data['data']:
                symbol_data = item['d']
                symbol = symbol_data[0]  # name

                # 只保留USDT现货交易对（排除永续合约）
                if ('USDT' in symbol or 'usdt' in symbol):
                    # 检查type字段，排除永续合约
                    is_spot = True
                    if len(symbol_data) > 9:
                        symbol_type = symbol_data[9]
                        if isinstance(symbol_type, str) and 'perpetual' in symbol_type.lower():
                            is_spot = False
                        elif len(symbol_data) > 10:
                            description = symbol_data[10]
                            if isinstance(description, str) and 'perpetual' in description.lower():
                                is_spot = False

                    if is_spot:
                        close_price = symbol_data[1]  # close
                        change_percent = symbol_data[2]  # change
                        change_abs = symbol_data[3]  # change_abs
                        high = symbol_data[4]  # high
                        low = symbol_data[5]  # low
                        volume = symbol_data[6]  # volume

                        result.append({
                            'symbol': symbol.replace('Binance:', ''),
                            'base_asset': symbol.replace('USDT', '').replace('usdt', '').replace('Binance:', ''),
                            'price': close_price,
                            'price_change_percent': change_percent,
                            'price_change_abs': change_abs,
                            'high': high,
                            'low': low,
                            'volume': volume,
                            'quote_volume': volume,
                            'source': 'TradingView'
                        })

                # 达到限制数量后停止
                if len(result) >= limit:
                    break

            logger.info(f"Successfully fetched {len(result)} top gainers from TradingView")
            return result

        except Exception as e:
            logger.error(f"Error fetching from TradingView: {e}")
            return []

    def _get_top_gainers_from_binance(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取涨幅榜前 N 的币种

        Args:
            limit: 返回数量，默认 20

        Returns:
            币种列表，每个包含 symbol, name, changePercent, volume 等信息
        """
        try:
            # 获取 24 小时 ticker 数据
            url = f"{self._spot_url}/api/v3/ticker/24hr"

            response = requests.get(url, proxies=self.proxies, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return []

            # 过滤出 USDT 交易对
            usdt_pairs = [
                item for item in data
                if item.get('symbol', '').endswith('USDT')
            ]

            # 按涨幅排序
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x.get('priceChangePercent', 0)),
                reverse=True
            )

            # 取前 N 个
            top_gainers = sorted_pairs[:limit]

            # 格式化数据
            result = []
            for item in top_gainers:
                result.append({
                    'symbol': item.get('symbol'),
                    'base_asset': item.get('symbol').replace('USDT', ''),
                    'quote_volume': float(item.get('quoteVolume', 0)),
                    'price_change_percent': float(item.get('priceChangePercent', 0)),
                    'price': float(item.get('lastPrice', 0)),
                    'high': float(item.get('highPrice', 0)),
                    'low': float(item.get('lowPrice', 0)),
                    'volume': float(item.get('volume', 0)),
                    'open_time': item.get('openTime'),
                    'close_time': item.get('closeTime')
                })

            logger.info(f"Successfully fetched {len(result)} top gainers from Binance")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching top gainers from Binance: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching top gainers from Binance: {e}", exc_info=True)
            return []

    def get_top_gainers_futures(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取合约市场涨幅榜前 N 的币种
        优先使用TradingView API,失败时回退到Binance API

        Args:
            limit: 返回数量，默认 20

        Returns:
            币种列表
        """
        # 先尝试使用TradingView API获取永续合约数据
        result = self._get_top_gainers_futures_from_tradingview(limit)
        if result:
            return result

        # 回退到Binance API
        logger.info("Falling back to Binance Futures API")
        return self._get_top_gainers_futures_from_binance(limit)

    def _get_top_gainers_futures_from_tradingview(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        使用TradingView Scanner API获取永续合约涨幅榜

        Args:
            limit: 返回数量

        Returns:
            币种列表
        """
        try:
            # 准备请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': self.tv_cookie,
                'Content-Type': 'application/json'
            }

            # 构建请求体 - 获取永续合约按涨跌幅排序
            payload = {
                "filter": [
                    {
                        "left": "type",
                        "operation": "equal",
                        "right": "perpetual"  # 只获取永续合约
                    }
                ],
                "options": {
                    "lang": "en",
                    "active_symbols_only": True
                },
                "symbols": {
                    "query": {
                        "types": []
                    },
                    "tickers": []
                },
                "columns": [
                    "name",
                    "close",
                    "change",
                    "change_abs",
                    "high",
                    "low",
                    "volume",
                    "market_cap_calc",
                    "recommendation",
                    "type",
                    "description"  # 添加描述字段以获取更多信息
                ],
                "sort": {
                    "sortBy": "change",
                    "sortOrder": "desc"
                },
                "range": [0, limit * 3]  # 获取更多数据以便过滤
            }

            response = requests.post(
                self.tv_scan_url,
                json=payload,
                headers=headers,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            if not data.get('data'):
                logger.error("No data from TradingView for futures")
                return []

            # 解析数据
            result = []
            for item in data['data']:
                symbol_data = item['d']
                symbol = symbol_data[0]  # name

                # 改进的永续合约识别逻辑
                is_perpetual = False
                if len(symbol_data) > 9:
                    symbol_type = symbol_data[9]  # type字段
                    if isinstance(symbol_type, str):
                        # 检查type字段包含perpetual
                        if 'perpetual' in symbol_type.lower():
                            is_perpetual = True
                        # 检查描述字段（如果有）
                        elif len(symbol_data) > 10:
                            description = symbol_data[10]
                            if isinstance(description, str) and 'perpetual' in description.lower():
                                is_perpetual = True

                    # 通过symbol名称判断（币安永续合约）
                    if not is_perpetual and 'USDT' in symbol:
                        # 排除交割合约（包含月份缩写）
                        delivery_months = ['MAR', 'JUN', 'SEP', 'DEC', 'H20', 'M20', 'U20', 'Z20',
                                          'H21', 'M21', 'U21', 'Z21', 'H22', 'M22', 'U22', 'Z22',
                                          'H23', 'M23', 'U23', 'Z23', 'H24', 'M24', 'U24', 'Z24',
                                          'H25', 'M25', 'U25', 'Z25']
                        if not any(month in symbol for month in delivery_months):
                            is_perpetual = True

                # 只保留USDT永续合约交易对
                if is_perpetual and ('USDT' in symbol or 'usdt' in symbol):
                    close_price = symbol_data[1]  # close
                    change_percent = symbol_data[2]  # change
                    change_abs = symbol_data[3]  # change_abs
                    high = symbol_data[4]  # high
                    low = symbol_data[5]  # low
                    volume = symbol_data[6]  # volume

                    result.append({
                        'symbol': symbol,
                        'base_asset': symbol.replace('USDT', '').replace('usdt', '').replace('PERP', '').replace('Binance:', ''),
                        'price': close_price,
                        'price_change_percent': change_percent,
                        'price_change_abs': change_abs,
                        'high': high,
                        'low': low,
                        'volume': volume,
                        'quote_volume': volume,
                        'source': 'TradingView Futures',
                        'contract_type': 'perpetual'
                    })

                # 达到限制数量后停止
                if len(result) >= limit:
                    break

            logger.info(f"Successfully fetched {len(result)} top gainers from TradingView Futures")
            return result

        except Exception as e:
            logger.error(f"Error fetching futures from TradingView: {e}")
            return []

    def _get_top_gainers_futures_from_binance(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        使用Binance API获取永续合约涨幅榜

        Args:
            limit: 返回数量，默认 20

        Returns:
            币种列表
        """
        try:
            # 获取合约 24 小时 ticker 数据
            url = f"{self.futures_url}/fapi/v1/ticker/24hr"

            response = requests.get(url, proxies=self.proxies, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return []

            # 过滤出 USDT 交易对
            usdt_pairs = [
                item for item in data
                if item.get('symbol', '').endswith('USDT')
            ]

            # 按涨幅排序
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x.get('priceChangePercent', 0)),
                reverse=True
            )

            # 取前 N 个
            top_gainers = sorted_pairs[:limit]

            # 格式化数据
            result = []
            for item in top_gainers:
                result.append({
                    'symbol': item.get('symbol'),
                    'base_asset': item.get('symbol').replace('USDT', ''),
                    'quote_volume': float(item.get('quoteVolume', 0)),
                    'price_change_percent': float(item.get('priceChangePercent', 0)),
                    'price': float(item.get('lastPrice', 0)),
                    'high': float(item.get('highPrice', 0)),
                    'low': float(item.get('lowPrice', 0)),
                    'volume': float(item.get('volume', 0)),
                    'open_time': item.get('openTime'),
                    'close_time': item.get('closeTime'),
                    'source': 'Binance Futures',
                    'contract_type': 'perpetual'
                })

            logger.info(f"Successfully fetched {len(result)} top gainers from Binance Futures")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching futures top gainers: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching futures top gainers: {e}", exc_info=True)
            return []

    def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取单个币种的 ticker 数据

        Args:
            symbol: 币种符号，如 'BTCUSDT'

        Returns:
            ticker 数据
        """
        try:
            url = f"{self._spot_url}/api/v3/ticker/24hr?symbol={symbol}"

            response = requests.get(url, proxies=self.proxies, timeout=10)
            response.raise_for_status()

            data = response.json()

            return {
                'symbol': data.get('symbol'),
                'price_change_percent': float(data.get('priceChangePercent', 0)),
                'price': float(data.get('lastPrice', 0)),
                'high': float(data.get('highPrice', 0)),
                'low': float(data.get('lowPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'quote_volume': float(data.get('quoteVolume', 0))
            }

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
