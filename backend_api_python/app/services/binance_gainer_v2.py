"""
Binance涨幅榜数据获取服务
支持多个数据源和自动降级
"""
import requests
import ccxt
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class BinanceGainerServiceV2:
    """Binance涨幅榜服务V2 - 支持多数据源"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 配置代理
        import os
        proxy_port = os.getenv('PROXY_PORT')
        proxy_url = os.getenv('PROXY_URL')

        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url,
            }
            logger.info(f"使用代理: {proxy_url}")
        elif proxy_port:
            self.session.proxies = {
                'http': f'http://127.0.0.1:{proxy_port}',
                'https': f'http://127.0.0.1:{proxy_port}',
            }
            logger.info(f"使用代理端口: {proxy_port}")

    def get_top_gainers_futures(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取Binance永续合约涨幅榜TOP币种

        按优先级尝试多个数据源:
        1. Binance期货API (直接)
        2. CCXT库 (封装)
        3. 缓存数据

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        logger.info(f"开始获取Binance永续合约涨幅榜TOP{limit}")

        # 方法1: 直接调用Binance期货API
        gainers = self._get_from_binance_api(limit)
        if gainers:
            return gainers

        # 方法2: 使用CCXT库
        gainers = self._get_from_ccxt(limit)
        if gainers:
            return gainers

        # 方法3: 使用缓存数据(如果存在)
        gainers = self._get_from_cache(limit)
        if gainers:
            logger.warning("使用缓存数据(实时数据不可用)")
            return gainers

        logger.error("所有数据源均失败,返回空列表")
        return []

    def _get_from_binance_api(self, limit: int) -> List[Dict[str, Any]]:
        """从Binance期货API获取数据"""
        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 过滤USDT交易对并排序
            usdt_pairs = [
                d for d in data
                if d['symbol'].endswith('USDT')
            ]

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

            logger.info(f"✅ 成功从Binance期货API获取{len(result)}个币种")
            return result

        except Exception as e:
            logger.warning(f"从Binance期货API获取失败: {e}")
            return []

    def _get_from_ccxt(self, limit: int) -> List[Dict[str, Any]]:
        """从CCXT库获取数据"""
        try:
            import ccxt

            exchange = ccxt.binance({
                'enableRateLimit': True,
                'timeout': 10000,
            })

            # 应用代理
            if self.session.proxies:
                exchange.proxies = self.session.proxies

            # 获取期货市场ticker
            tickers = exchange.fetch_tickers('USDT', params={'type': 'future'})

            # 转换并排序
            pairs = []
            for symbol, ticker in tickers.items():
                if not symbol.endswith('/USDT'):
                    continue

                change_percent = ticker.get('percentage', 0)
                if change_percent is None:
                    continue

                pairs.append({
                    'symbol': symbol.replace('/', ''),
                    'base_asset': symbol.split('/')[0],
                    'price': float(ticker.get('last', 0)),
                    'price_change_percent': float(change_percent),
                    'volume': float(ticker.get('baseVolume', 0)),
                    'quote_volume': float(ticker.get('quoteVolume', 0)),
                    'exchange': 'Binance',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

            # 排序
            sorted_pairs = sorted(
                pairs,
                key=lambda x: x['price_change_percent'],
                reverse=True
            )

            logger.info(f"✅ 成功从CCXT获取{len(sorted_pairs[:limit])}个币种")
            return sorted_pairs[:limit]

        except Exception as e:
            logger.warning(f"从CCXT获取失败: {e}")
            return []

    def _get_from_cache(self, limit: int) -> List[Dict[str, Any]]:
        """从缓存获取数据"""
        try:
            cache_file = '/app/data/gainers_cache.json'

            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # 检查缓存是否过期(5分钟)
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                if datetime.now() - cache_time > timedelta(minutes=5):
                    logger.warning("缓存数据已过期")
                    return []

                gainers = cache_data.get('gainers', [])[:limit]
                logger.info(f"✅ 从缓存获取{len(gainers)}个币种")
                return gainers

            except FileNotFoundError:
                logger.warning("缓存文件不存在")
                return []

        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return []

    def save_to_cache(self, gainers: List[Dict[str, Any]]):
        """保存数据到缓存"""
        try:
            cache_file = '/app/data/gainers_cache.json'

            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'gainers': gainers
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 已保存{len(gainers)}个币种到缓存")

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")


# 便捷函数
def get_top_gainers_futures_v2(limit: int = 20) -> List[Dict[str, Any]]:
    """获取Binance永续合约涨幅榜TOP币种(V2版本)"""
    service = BinanceGainerServiceV2()
    gainers = service.get_top_gainers_futures(limit)

    # 保存到缓存
    if gainers:
        service.save_to_cache(gainers)

    return gainers
