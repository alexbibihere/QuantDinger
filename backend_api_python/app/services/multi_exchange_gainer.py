"""
多交易所涨幅榜对比服务
支持从多个交易所获取涨幅榜数据并对比验证实时性
"""
import requests
import os
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MultiExchangeGainerService:
    """多交易所涨幅榜对比服务"""

    def __init__(self):
        # Binance API
        self.binance_spot_url = "https://api.binance.com/api/v3/ticker/24hr"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1/ticker/24hr"

        # OKX API (公开数据，无需认证)
        self.okx_spot_url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
        self.okx_futures_url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"

        # 配置代理
        self.proxies = self._get_proxies()
        if self.proxies:
            logger.info(f"Using proxy: {self.proxies}")

    def _get_proxies(self):
        """获取代理配置"""
        proxy_url = os.getenv('PROXY_URL')
        if proxy_url:
            return {'http': proxy_url, 'https': proxy_url}

        proxy_port = os.getenv('PROXY_PORT')
        if proxy_port:
            proxy_scheme = os.getenv('PROXY_SCHEME', 'socks5h')
            proxy_host = os.getenv('PROXY_HOST', '127.0.0.1')
            proxy_url = f"{proxy_scheme}://{proxy_host}:{proxy_port}"
            return {'http': proxy_url, 'https': proxy_url}

        for key in ['ALL_PROXY', 'HTTPS_PROXY', 'HTTP_PROXY']:
            proxy_url = os.getenv(key)
            if proxy_url:
                return {'http': proxy_url, 'https': proxy_url}

        return None

    def get_binance_spot_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取Binance现货涨幅榜"""
        try:
            response = requests.get(
                self.binance_spot_url,
                proxies=self.proxies,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x['priceChangePercent']),
                reverse=True
            )

            result = []
            for item in sorted_pairs[:limit]:
                result.append({
                    'symbol': item['symbol'],
                    'base_asset': item['symbol'].replace('USDT', ''),
                    'price': float(item['lastPrice']),
                    'price_change_percent': float(item['priceChangePercent']),
                    'volume': float(item['volume']),
                    'quote_volume': float(item['quoteVolume']),
                    'exchange': 'Binance',
                    'market': 'spot',
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Successfully fetched {len(result)} gainers from Binance Spot")
            return result

        except Exception as e:
            logger.error(f"Error fetching Binance spot gainers: {e}")
            return []

    def get_binance_futures_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取Binance永续合约涨幅榜"""
        try:
            response = requests.get(
                self.binance_futures_url,
                proxies=self.proxies,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x['priceChangePercent']),
                reverse=True
            )

            result = []
            for item in sorted_pairs[:limit]:
                result.append({
                    'symbol': item['symbol'],
                    'base_asset': item['symbol'].replace('USDT', ''),
                    'price': float(item['lastPrice']),
                    'price_change_percent': float(item['priceChangePercent']),
                    'volume': float(item['volume']),
                    'quote_volume': float(item['quoteVolume']),
                    'exchange': 'Binance',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Successfully fetched {len(result)} gainers from Binance Futures")
            return result

        except Exception as e:
            logger.error(f"Error fetching Binance futures gainers: {e}")
            return []

    def get_okx_spot_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取OKX现货涨幅榜"""
        try:
            response = requests.get(
                self.okx_spot_url,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            if data.get('code') != '0':
                logger.error(f"OKX API error: {data.get('msg')}")
                return []

            # 过滤USDT交易对
            usdt_tickers = [
                t for t in data.get('data', [])
                if t['instId'].endswith('-USDT')
            ]

            # 按涨跌幅排序
            sorted_tickers = sorted(
                usdt_tickers,
                key=lambda x: float(x.get('change24h', 0)),
                reverse=True
            )

            result = []
            for ticker in sorted_tickers[:limit]:
                result.append({
                    'symbol': ticker['instId'].replace('-', ''),
                    'base_asset': ticker['instId'].split('-')[0],
                    'price': float(ticker.get('last', 0)),
                    'price_change_percent': float(ticker.get('change24h', 0)),
                    'volume': float(ticker.get('vol24h', 0)),
                    'quote_volume': float(ticker.get('volCcy24h', 0)),
                    'exchange': 'OKX',
                    'market': 'spot',
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Successfully fetched {len(result)} gainers from OKX Spot")
            return result

        except Exception as e:
            logger.error(f"Error fetching OKX spot gainers: {e}")
            return []

    def get_okx_futures_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取OKX永续合约涨幅榜"""
        try:
            response = requests.get(
                self.okx_futures_url,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            if data.get('code') != '0':
                logger.error(f"OKX API error: {data.get('msg')}")
                return []

            # 过滤USDT永续合约
            usdt_swaps = [
                t for t in data.get('data', [])
                if t['instType'] == 'SWAP' and t['instId'].endswith('-USDT-SWAP')
            ]

            # 按涨跌幅排序
            sorted_swaps = sorted(
                usdt_swaps,
                key=lambda x: float(x.get('change24h', 0)),
                reverse=True
            )

            result = []
            for swap in sorted_swaps[:limit]:
                symbol = swap['instId'].replace('-USDT-SWAP', '').replace('-', '')
                result.append({
                    'symbol': symbol + 'USDT',
                    'base_asset': symbol,
                    'price': float(swap.get('last', 0)),
                    'price_change_percent': float(swap.get('change24h', 0)),
                    'volume': float(swap.get('vol24h', 0)),
                    'quote_volume': float(swap.get('volCcy24h', 0)),
                    'exchange': 'OKX',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Successfully fetched {len(result)} gainers from OKX Futures")
            return result

        except Exception as e:
            logger.error(f"Error fetching OKX futures gainers: {e}")
            return []

    def compare_exchanges(
        self,
        market: str = 'futures',
        limit: int = 10,
        with_hama: bool = False  # 默认False，延迟加载
    ) -> Dict[str, Any]:
        """
        对比多个交易所的涨幅榜数据

        Args:
            market: 市场类型 'spot' 或 'futures'
            limit: 返回数量
            with_hama: 是否包含HAMA指标数据（默认False，按需加载）

        Returns:
            包含多个交易所数据和对比分析的字典
        """
        logger.info(f"Comparing exchanges for {market} market, top {limit}, hama={with_hama}")

        # 获取各交易所数据
        binance_data = (
            self.get_binance_futures_gainers(limit)
            if market == 'futures'
            else self.get_binance_spot_gainers(limit)
        )

        okx_data = (
            self.get_okx_futures_gainers(limit)
            if market == 'futures'
            else self.get_okx_spot_gainers(limit)
        )

        # 计算HAMA指标（仅Binance币种）
        hama_data = {}
        if with_hama and binance_data:
            try:
                from app.services.hama_binance_calculator import get_hama_calculator
                symbols = [item['symbol'] for item in binance_data]
                calculator = get_hama_calculator(use_futures=(market == 'futures'))
                hama_data = calculator.calculate_batch(symbols, interval='15m', max_workers=5)
                logger.info(f"计算了 {len(hama_data)} 个币种的HAMA指标")

                # 将HAMA数据合并到binance_data中
                for item in binance_data:
                    symbol = item['symbol']
                    if symbol in hama_data:
                        item['hama'] = {
                            'color': hama_data[symbol].get('hama_color'),
                            'trend': hama_data[symbol].get('hama_trend'),
                            'candle_close': hama_data[symbol].get('candle_close'),
                            'ma': hama_data[symbol].get('ma'),
                            'candle_ma_status': hama_data[symbol].get('candle_ma_status'),
                            'bb_status': hama_data[symbol].get('bb_status'),
                            'bb_upper': hama_data[symbol].get('bb_upper'),
                            'bb_lower': hama_data[symbol].get('bb_lower'),
                            'last_cross_type': hama_data[symbol].get('last_cross_type'),
                            'last_cross_time': hama_data[symbol].get('last_cross_time')
                        }
            except Exception as e:
                logger.error(f"计算HAMA失败: {e}")

        # 分析数据
        comparison = {
            'market': market,
            'limit': limit,
            'timestamp': datetime.now().isoformat(),
            'exchanges': {
                'binance': {
                    'count': len(binance_data),
                    'top_gainers': binance_data
                },
                'okx': {
                    'count': len(okx_data),
                    'top_gainers': okx_data
                }
            },
            'analysis': self._analyze_comparison(binance_data, okx_data)
        }

        return comparison

    def _analyze_comparison(
        self,
        binance_data: List[Dict],
        okx_data: List[Dict]
    ) -> Dict[str, Any]:
        """分析两个交易所的数据差异"""
        # 提取币种列表
        binance_symbols = {item['symbol'] for item in binance_data}
        okx_symbols = {item['symbol'] for item in okx_data}

        # 找出共同币种
        common_symbols = binance_symbols & okx_symbols

        # 对比共同币种的价格差异
        price_diffs = []
        for symbol in common_symbols:
            binance_item = next(
                (i for i in binance_data if i['symbol'] == symbol),
                None
            )
            okx_item = next(
                (i for i in okx_data if i['symbol'] == symbol),
                None
            )

            if binance_item and okx_item:
                price_diff_pct = abs(
                    (binance_item['price_change_percent'] -
                     okx_item['price_change_percent'])
                )
                price_diffs.append({
                    'symbol': symbol,
                    'binance_change': binance_item['price_change_percent'],
                    'okx_change': okx_item['price_change_percent'],
                    'diff': price_diff_pct
                })

        return {
            'total_common_symbols': len(common_symbols),
            'binance_only': list(binance_symbols - okx_symbols)[:5],
            'okx_only': list(okx_symbols - binance_symbols)[:5],
            'price_differences': sorted(
                price_diffs,
                key=lambda x: x['diff'],
                reverse=True
            )[:5]
        }
