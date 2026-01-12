"""
AICoin/非小号涨幅榜数据获取服务
当Binance API不可用时,使用AICoin等第三方数据源
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AICoinGainerService:
    """AICoin涨幅榜服务"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 配置代理
        import os
        proxy_port = os.getenv('PROXY_PORT')
        if proxy_port:
            self.session.proxies = {
                'http': f'http://127.0.0.1:{proxy_port}',
                'https': f'http://127.0.0.1:{proxy_port}',
            }

    def get_binance_futures_gainers_aicoin(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        从AICoin获取Binance永续合约涨幅榜

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        try:
            # AICoin API端点 (可能需要根据实际情况调整)
            url = "https://www.aicoin.com/api/v1/exchange/binance/tickers"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()

            # 解析数据 (需要根据实际API响应格式调整)
            gainers = self._parse_aicoin_data(data, limit)

            logger.info(f"成功从AICoin获取{len(gainers)}个Binance涨幅币种")
            return gainers

        except Exception as e:
            logger.error(f"从AICoin获取数据失败: {e}")
            return []

    def get_binance_futures_gainers_feixiaohao(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        从非小号(Feixiaohao)获取Binance永续合约涨幅榜

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        try:
            # 非小号API
            url = "https://api.feixiaohao.com/v6/ticker/binance-usdt"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()

            # 解析非小号数据
            gainers = self._parse_feixiaohao_data(data, limit)

            logger.info(f"成功从非小号获取{len(gainers)}个Binance涨幅币种")
            return gainers

        except Exception as e:
            logger.error(f"从非小号获取数据失败: {e}")
            return []

    def _parse_aicoin_data(self, data: Dict, limit: int) -> List[Dict[str, Any]]:
        """解析AICoin数据"""
        # 这里需要根据AICoin实际返回的JSON格式来解析
        # 以下是示例代码,需要根据实际API调整
        gainers = []

        # 假设AICoin返回格式类似Binance API
        if isinstance(data, list):
            # 过滤USDT交易对
            usdt_pairs = [d for d in data if d.get('symbol', '').endswith('USDT')]

            # 按涨跌幅排序
            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x.get('change_percent', 0)),
                reverse=True
            )

            for item in sorted_pairs[:limit]:
                gainers.append({
                    'symbol': item.get('symbol'),
                    'base_asset': item.get('symbol', '').replace('USDT', ''),
                    'price': float(item.get('last', 0)),
                    'price_change_percent': float(item.get('change_percent', 0)),
                    'volume': float(item.get('volume', 0)),
                    'quote_volume': float(item.get('quote_volume', 0)),
                    'exchange': 'Binance',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

        return gainers

    def _parse_feixiaohao_data(self, data: Dict, limit: int) -> List[Dict[str, Any]]:
        """解析非小号数据"""
        gainers = []

        # 非小号API返回格式示例
        # 需要根据实际API调整
        if isinstance(data, dict) and 'data' in data:
            tickers = data['data']

            # 按涨跌幅排序
            sorted_tickers = sorted(
                tickers.items(),
                key=lambda x: float(x[1].get('change_percent', 0)),
                reverse=True
            )

            for symbol, ticker_data in sorted_tickers[:limit]:
                gainers.append({
                    'symbol': symbol,
                    'base_asset': symbol.replace('USDT', ''),
                    'price': float(ticker_data.get('last', 0)),
                    'price_change_percent': float(ticker_data.get('change_percent', 0)),
                    'volume': float(ticker_data.get('volume', 0)),
                    'quote_volume': float(ticker_data.get('quote_volume', 0)),
                    'exchange': 'Binance',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

        return gainers

    def get_binance_futures_gainers_fallback(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        使用备用数据源获取Binance永续合约涨幅榜

        按优先级尝试多个数据源:
        1. AICoin
        2. 非小号
        3. CoinGecko

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        logger.info("尝试从备用数据源获取Binance涨幅榜")

        # 优先尝试AICoin
        gainers = self.get_binance_futures_gainers_aicoin(limit)
        if gainers:
            return gainers

        # 尝试非小号
        gainers = self.get_binance_futures_gainers_feixiaohao(limit)
        if gainers:
            return gainers

        logger.warning("所有备用数据源均失败")
        return []


# 便捷函数
def get_binance_futures_gainers_fallback(limit: int = 20) -> List[Dict[str, Any]]:
    """
    获取Binance永续合约涨幅榜(使用备用数据源)

    Args:
        limit: 返回数量

    Returns:
        涨幅榜数据列表
    """
    service = AICoinGainerService()
    return service.get_binance_futures_gainers_fallback(limit)
