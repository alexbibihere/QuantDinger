"""
TradingView Scanner API - 获取大量加密货币数据
无需登录,可获取数百个币种的实时数据和技术指标
"""
import requests
import json
import os
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewScannerAPI:
    """TradingView Scanner API服务"""

    def __init__(self):
        """初始化服务"""
        self.base_url = "https://scanner.tradingview.com"
        self.session = requests.Session()

        # 获取代理配置
        self.proxy = self._get_proxy()

        # 如果配置了代理,设置到session
        if self.proxy:
            self.session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
            logger.info(f"✅ 使用代理: {self.proxy}")

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    def _get_proxy(self) -> str:
        """获取代理配置"""
        # 1. 检查环境变量
        proxy_url = os.environ.get('PROXY_URL') or os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')

        if proxy_url:
            return proxy_url

        # 2. 检查PROXY_PORT环境变量(简化配置)
        proxy_port = os.environ.get('PROXY_PORT')
        if proxy_port:
            # Docker网络中,宿主机可以通过host.docker.internal访问
            # 或者使用docker-compose中的service名称
            return f'http://host.docker.internal:{proxy_port}'

        # 3. 默认返回None(不使用代理)
        return None

    def get_crypto_data(
        self,
        symbols: List[str],
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取加密货币数据

        Args:
            symbols: 币种列表,如 ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT']
            columns: 要获取的字段列表

        Returns:
            币种数据列表
        """
        if columns is None:
            # 使用最基础的字段,避免API错误
            columns = [
                'name',           # 名称
                'description',    # 描述
                'close',          # 收盘价
                'change',         # 涨跌幅
                'volume',         # 成交量
            ]

        try:
            logger.info(f"正在获取 {len(symbols)} 个币种的数据...")

            response = self.session.post(
                f"{self.base_url}/crypto/scan",
                json={
                    'symbols': {'tickers': symbols},
                    'columns': columns
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                scan_data = data.get('data', [])

                logger.info(f"✅ 成功获取 {len(scan_data)} 个币种的数据")

                return self._parse_scanner_data(scan_data)
            else:
                logger.error(f"API请求失败: {response.status_code}")
                logger.error(f"响应: {response.text[:500]}")
                return []

        except Exception as e:
            logger.error(f"获取数据失败: {e}", exc_info=True)
            return []

    def _parse_scanner_data(self, scan_data: List[Dict]) -> List[Dict[str, Any]]:
        """解析Scanner数据"""
        result = []

        for item in scan_data:
            try:
                symbol = item.get('s', '')  # symbol
                data = item.get('d', [])    # data array

                if not symbol or not data:
                    continue

                # 清理symbol
                clean_symbol = symbol.replace('BINANCE:', '') if 'BINANCE:' in symbol else symbol

                result.append({
                    'symbol': clean_symbol,
                    'full_symbol': symbol,
                    'name': data[0] if len(data) > 0 else clean_symbol,
                    'description': data[1] if len(data) > 1 else clean_symbol,
                    'price': data[2] if len(data) > 2 else 0,
                    'change_percentage': data[3] if len(data) > 3 else 0,
                    'volume': data[4] if len(data) > 4 else 0,
                    'exchange': 'Binance',
                    'source': 'TradingView Scanner'
                })
            except Exception as e:
                logger.debug(f"解析币种失败: {e}")
                continue

        return result

    def get_top_perpetuals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取币安Top永续合约

        Args:
            limit: 数量限制

        Returns:
            币种列表
        """
        try:
            logger.info("正在获取永续合约数据...")

            # 方法1: 尝试使用币安API获取(如果配置了代理)
            if self.proxy:
                try:
                    import ccxt

                    logger.info("尝试使用币安API获取永续合约列表...")

                    exchange_config = {
                        'proxies': {
                            'http': self.proxy,
                            'https': self.proxy
                        },
                        'timeout': 30000
                    }

                    exchange = ccxt.binance(exchange_config)
                    markets = exchange.load_markets()

                    # 筛选USDT永续合约(获取所有,不限制数量)
                    perpetuals = [
                        symbol
                        for symbol, market in markets.items()
                        if symbol.endswith('USDT') and market.get('swap', False)
                    ]

                    logger.info(f"✅ 从币安API获取到 {len(perpetuals)} 个永续合约")

                    # 限制数量并转换为TradingView格式
                    # 注意: 如果传入的limit较大(如500或1000),获取更多币种
                    perpetuals = perpetuals[:limit]
                    tv_symbols = [f"BINANCE:{s}" for s in perpetuals]

                    # 批量获取数据
                    all_data = self._fetch_batch_data(tv_symbols)

                    if all_data:
                        return all_data

                except Exception as e:
                    logger.warning(f"币安API访问失败: {e}, 使用预定义列表")

            # 方法2: 使用预定义的永续合约列表
            logger.info("使用预定义永续合约列表...")

            from app.services.tradingview_perpetuals_list import get_tradingview_symbols

            tv_symbols = get_tradingview_symbols(limit)
            logger.info(f"✅ 使用预定义列表: {len(tv_symbols)} 个永续合约")

            # 批量获取数据
            return self._fetch_batch_data(tv_symbols)

        except Exception as e:
            logger.error(f"获取永续合约失败: {e}", exc_info=True)
            return []

    def _fetch_batch_data(self, tv_symbols: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取TradingView数据(优化版,避免API限制)

        Args:
            tv_symbols: TradingView格式符号列表

        Returns:
            币种数据列表
        """
        # 批量获取数据(每批15个,减少API压力)
        batch_size = 15
        all_data = []
        failed_batches = []

        logger.info(f"开始分批获取 {len(tv_symbols)} 个币种的数据,每批 {batch_size} 个...")

        for i in range(0, len(tv_symbols), batch_size):
            batch = tv_symbols[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(tv_symbols) + batch_size - 1) // batch_size

            logger.info(f"正在处理第 {batch_num}/{total_batches} 批 ({len(batch)} 个币种)...")

            try:
                batch_data = self.get_crypto_data(batch)

                if batch_data:
                    all_data.extend(batch_data)
                    logger.info(f"✅ 第 {batch_num} 批成功获取 {len(batch_data)} 个币种")
                else:
                    logger.warning(f"⚠️ 第 {batch_num} 批未获取到数据")
                    failed_batches.append((batch_num, batch))

                # 避免请求过快 - 每批之间延迟1秒
                import time
                if i + batch_size < len(tv_symbols):  # 不是最后一批
                    time.sleep(1)

            except Exception as e:
                logger.error(f"❌ 第 {batch_num} 批获取失败: {e}")
                failed_batches.append((batch_num, batch))

                # 出错后增加延迟
                import time
                time.sleep(2)

        logger.info(f"✅ 总共获取 {len(all_data)}/{len(tv_symbols)} 个永续合约数据")

        # 如果有失败的批次,尝试重试一次
        if failed_batches and len(all_data) < len(tv_symbols) * 0.5:  # 如果成功率低于50%
            logger.info(f"尝试重试 {len(failed_batches)} 个失败的批次...")
            for batch_num, batch in failed_batches[:3]:  # 最多重试前3个失败批次
                try:
                    logger.info(f"重试第 {batch_num} 批...")
                    batch_data = self.get_crypto_data(batch)
                    if batch_data:
                        all_data.extend(batch_data)
                        logger.info(f"✅ 第 {batch_num} 批重试成功")
                    import time
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ 第 {batch_num} 批重试失败: {e}")

        return all_data

    def get_default_watchlist(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取默认关注列表(Top加密货币)

        Args:
            limit: 数量限制

        Returns:
            币种列表
        """
        # 默认的Top加密货币
        default_symbols = [
            'BINANCE:BTCUSDT',   # Bitcoin
            'BINANCE:ETHUSDT',   # Ethereum
            'BINANCE:BNBUSDT',   # BNB
            'BINANCE:SOLUSDT',   # Solana
            'BINANCE:XRPUSDT',   # XRP
            'BINANCE:ADAUSDT',   # Cardano
            'BINANCE:DOGEUSDT',  # Dogecoin
            'BINANCE:MATICUSDT', # Polygon
            'BINANCE:DOTUSDT',   # Polkadot
            'BINANCE:AVAXUSDT',  # Avalanche
            'BINANCE:LINKUSDT',  # Chainlink
            'BINANCE:UNIUSDT',   # Uniswap
            'BINANCE:LTCUSDT',   # Litecoin
            'BINANCE:ATOMUSDT',  # Cosmos
            'BINANCE:NEARUSDT',  # NEAR
            'BINANCE:APTUSDT',   # Aptos
            'BINANCE:OPUSDT',    # Optimism
            'BINANCE:ARBUSDT',   # Arbitrum
            'BINANCE:INJUSDT',   # Injective
            'BINANCE:QNTUSDT',   # Quant
        ]

        symbols = default_symbols[:limit]

        logger.info(f"获取默认关注列表 ({len(symbols)} 个币种)")

        return self.get_crypto_data(symbols)

    def get_top_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取涨幅榜(按涨跌幅排序)

        Args:
            limit: 返回数量

        Returns:
            按涨幅排序的币种列表
        """
        # 获取所有币安永续合约(增加到600个,以确保包含所有539个USDT永续合约)
        all_coins = self.get_top_perpetuals(limit=600)

        if not all_coins:
            return []

        # 过滤并排序
        gainers = []
        for coin in all_coins:
            try:
                change = coin.get('change_percentage', 0)
                if isinstance(change, (int, float)):
                    coin['change_value'] = change
                    gainers.append(coin)
            except:
                continue

        # 按涨幅降序排序
        gainers.sort(key=lambda x: x.get('change_value', 0), reverse=True)

        result = gainers[:limit]

        # 自动记录到涨幅榜统计
        try:
            from app.services.gainer_tracker import record_gainer_appearance
            symbols = [coin['symbol'] for coin in result]
            record_gainer_appearance(symbols)
        except Exception as e:
            logger.warning(f"记录涨幅榜统计失败: {e}")

        return result


# 便捷函数
def get_tradingview_crypto_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """获取TradingView加密货币数据"""
    api = TradingViewScannerAPI()
    return api.get_crypto_data(symbols)


def get_top_perpetuals(limit: int = 50) -> List[Dict[str, Any]]:
    """获取Top永续合约数据"""
    api = TradingViewScannerAPI()
    return api.get_top_perpetuals(limit)


def get_default_watchlist(limit: int = 20) -> List[Dict[str, Any]]:
    """获取默认关注列表"""
    api = TradingViewScannerAPI()
    return api.get_default_watchlist(limit)


def get_top_gainers(limit: int = 20) -> List[Dict[str, Any]]:
    """获取涨幅榜"""
    api = TradingViewScannerAPI()
    return api.get_top_gainers(limit)


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("TradingView Scanner API测试")
    print("=" * 80)

    api = TradingViewScannerAPI()

    # 测试1: 获取默认列表
    print("\n测试1: 获取默认关注列表")
    print("-" * 80)

    watchlist = api.get_default_watchlist(limit=20)

    if watchlist:
        print(f"\n✅ 获取到 {len(watchlist)} 个币种:\n")
        for i, coin in enumerate(watchlist, 1):
            print(f"{i:2d}. {coin['symbol']:20} {coin['description']:30} "
                  f"价格:{coin['price']:>12.2f} 涨跌:{coin['change_percentage']:>+8.2f}%")
    else:
        print("❌ 未能获取到数据")

    # 测试2: 获取Top永续合约(只取前10个用于测试)
    print("\n\n测试2: 获取Top永续合约(前10个)")
    print("-" * 80)

    perpetuals = api.get_top_perpetuals(limit=10)

    if perpetuals:
        print(f"\n✅ 获取到 {len(perpetuals)} 个永续合约:\n")
        for i, coin in enumerate(perpetuals, 1):
            print(f"{i:2d}. {coin['symbol']:20} 价格:{coin['price']:>12.2f} "
                  f"涨跌:{coin['change_percentage']:>+8.2f}%")

    print("\n" + "=" * 80)
    print("使用示例:")
    print("  from app.services.tradingview_scanner_service import get_top_perpetuals")
    print("  watchlist = get_top_perpetuals(limit=100)  # 获取100个永续合约")
    print("=" * 80)
