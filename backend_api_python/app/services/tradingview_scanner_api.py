"""
TradingView Scanner API服务
直接调用TradingView公开的Scanner API,无需Cookie认证
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewScannerAPI:
    """TradingView Scanner API服务"""

    def __init__(self):
        """初始化服务"""
        # TradingView Scanner API端点(公开API,无需认证)
        self.scan_url = "https://scanner.tradingview.com/crypto/scan"

        # 常用加密货币列表
        self.popular_symbols = [
            'BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:BNBUSDT',
            'BINANCE:SOLUSDT', 'BINANCE:XRPUSDT', 'BINANCE:ADAUSDT',
            'BINANCE:DOGEUSDT', 'BINANCE:MATICUSDT', 'BINANCE:DOTUSDT',
            'BINANCE:AVAXUSDT', 'BINANCE:LINKUSDT', 'BINANCE:UNIUSDT',
            'BINANCE:LTCUSDT', 'BINANCE:BCHUSDT', 'BINANCE:ATOMUSDT',
            'BINANCE:XLMUSDT', 'BINANCE:ALGOUSDT', 'BINANCE:VETUSDT',
            'BINANCE:FILUSDT', 'BINANCE:TRXUSDT', 'BINANCE:ETCUSDT'
        ]

        # 配置代理
        import os
        proxy_port = os.getenv('PROXY_PORT')
        proxy_host = os.getenv('PROXY_HOST', '127.0.0.1')

        self.proxies = None
        if proxy_port:
            self.proxies = {
                'http': f'http://{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_host}:{proxy_port}'
            }
            logger.info(f"使用代理: {proxy_host}:{proxy_port}")

    def scan_symbols(
        self,
        symbols: List[str] = None,
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        扫描指定币种列表

        Args:
            symbols: 币种列表,如 ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT']
            columns: 要查询的指标列

        Returns:
            币种数据列表
        """
        if symbols is None:
            symbols = self.popular_symbols

        if columns is None:
            # 默认查询常用指标
            columns = [
                'name',                    # 币种名称
                'description',             # 描述
                'update',                  # 更新时间
                'Recommend.All|15',        # 综合推荐(15分钟)
                'Recommend.All|60',        # 综合推荐(1小时)
                'RSI|14|0',               # RSI(14)
                'RSI|14|15',              # RSI(15分钟)
                'MACD.macd',              # MACD
                'MACD.signal',            # MACD信号线
                'EMA|20|0',               # EMA20
                'EMA|50|0',               # EMA50
                'EMA|200|0',              # EMA200
                'Pivot.Mid.Classic',      # 中枢点
                'Open|0',                 # 开盘价
                'High|0',                 # 最高价
                'Low|0',                  # 最低价
                'Close|0',                # 收盘价
                'Volume|0'                # 成交量
            ]

        try:
            # 构建请求
            payload = {
                "symbols": {"tickers": symbols},
                "columns": columns
            }

            logger.info(f"正在扫描{len(symbols)}个币种...")

            response = requests.post(
                self.scan_url,
                json=payload,
                proxies=self.proxies,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # 解析返回数据
                result = self._parse_scan_data(data, columns)

                logger.info(f"✅ 成功获取{len(result)}个币种数据")
                return result
            else:
                logger.error(f"❌ API请求失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ 扫描币种失败: {e}", exc_info=True)
            return []

    def _parse_scan_data(
        self,
        data: Dict,
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        解析Scanner API返回的数据

        Args:
            data: API返回的原始数据
            columns: 请求的列名列表

        Returns:
            解析后的币种列表
        """
        result = []

        try:
            # Scanner API返回格式: {data: [[symbol, values...], ...]}
            scan_data = data.get('data', [])

            for row in scan_data:
                if len(row) >= 2:
                    symbol = row[0]  # BINANCE:BTCUSDT
                    values = row[1] if len(row) > 1 else []

                    # 提取基础信息
                    clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol

                    # 只处理USDT交易对
                    if 'USDT' not in clean_symbol:
                        continue

                    # 构建币种数据
                    coin_data = {
                        'symbol': clean_symbol,
                        'base_asset': clean_symbol.replace('USDT', ''),
                        'exchange': 'Binance',
                        'market': 'futures',
                        'source': 'TradingView Scanner',
                        'timestamp': datetime.now().isoformat()
                    }

                    # 解析返回的指标值
                    # values是按columns顺序排列的值数组
                    for i, column in enumerate(columns):
                        if i < len(values) and values[i] is not None:
                            # 将列名转换为字段名
                            field_name = self._column_to_field(column)
                            coin_data[field_name] = values[i]

                    result.append(coin_data)

        except Exception as e:
            logger.error(f"解析数据失败: {e}")

        return result

    def _column_to_field(self, column: str) -> str:
        """
        将TradingView列名转换为字段名

        Args:
            column: TradingView列名,如 'RSI|14|0'

        Returns:
            字段名,如 'rsi_14'
        """
        # 移除空格和特殊字符
        parts = column.split('|')

        if len(parts) >= 3:
            # 格式: 指标|参数|周期
            indicator = parts[0].lower()
            period = parts[1] if len(parts) > 1 else ''
            interval = parts[2] if len(parts) > 2 else ''

            # 组合字段名
            if interval == '0':
                # 0表示日线或默认周期
                return f"{indicator}_{period}" if period else indicator
            else:
                return f"{indicator}_{period}_{interval}"
        else:
            # 简单列名
            return column.lower().replace('.', '_')

    def get_top_gainers_by_recommendation(
        self,
        limit: int = 10,
        interval: str = '15'
    ) -> List[Dict[str, Any]]:
        """
        获取推荐度最高的币种(买入信号)

        Args:
            limit: 返回数量
            interval: K线周期(15=15分钟, 60=1小时)

        Returns:
            按推荐度排序的币种列表
        """
        # 扫描所有币种
        all_coins = self.scan_symbols()

        if not all_coins:
            return []

        # 根据推荐度排序
        recommend_field = f'recommend_all_{interval}'

        # 过滤有推荐值的币种并排序
        filtered_coins = []
        for coin in all_coins:
            if recommend_field in coin and coin[recommend_field] is not None:
                filtered_coins.append(coin)

        # 按推荐度排序(值越大越推荐买入)
        sorted_coins = sorted(
            filtered_coins,
            key=lambda x: float(x.get(recommend_field, 0)),
            reverse=True
        )

        return sorted_coins[:limit]

    def get_symbols_with_rsi(
        self,
        min_rsi: float = 30,
        max_rsi: float = 70,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取RSI在指定范围内的币种

        Args:
            min_rsi: 最小RSI值
            max_rsi: 最大RSI值
            limit: 返回数量

        Returns:
            符合条件的币种列表
        """
        all_coins = self.scan_symbols()

        if not all_coins:
            return []

        # 过滤RSI在范围内的币种
        filtered_coins = []
        for coin in all_coins:
            rsi = coin.get('rsi_14_15') or coin.get('rsi_14')

            if rsi is not None and min_rsi <= rsi <= max_rsi:
                coin['rsi_value'] = rsi
                filtered_coins.append(coin)

        # 按RSI排序
        filtered_coins.sort(key=lambda x: x.get('rsi_value', 0), reverse=True)

        return filtered_coins[:limit]


# 便捷函数
def scan_crypto_symbols(
    symbols: List[str] = None,
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    扫描加密货币币种

    Args:
        symbols: 币种列表,如 ['BINANCE:BTCUSDT', ...]
        limit: 限制返回数量

    Returns:
        币种列表
    """
    service = TradingViewScannerAPI()
    result = service.scan_symbols(symbols)

    if limit:
        result = result[:limit]

    return result


def get_buy_signals(limit: int = 10) -> List[Dict[str, Any]]:
    """获取买入信号(推荐度最高的币种)"""
    service = TradingViewScannerAPI()
    return service.get_top_gainers_by_recommendation(limit)


# 测试代码
if __name__ == "__main__":
    import json

    print("=" * 80)
    print("TradingView Scanner API 测试")
    print("=" * 80)

    service = TradingViewScannerAPI()

    # 测试1: 扫描常用币种
    print("\n测试1: 扫描常用币种")
    print("-" * 80)

    symbols = service.scan_symbols()

    print(f"\n获取到 {len(symbols)} 个币种\n")

    if symbols:
        print("TOP10:")
        for i, s in enumerate(symbols[:10], 1):
            name = s.get('description', s['symbol'])
            recommend = s.get('recommend_all_15', 'N/A')
            rsi = s.get('rsi_14_15', 'N/A')
            close_price = s.get('close|0', 'N/A')

            print(f"{i:2d}. {s['symbol']:15} {name:15} "
                  f"推荐:{recommend:5} RSI:{rsi:6} 价格:{close_price}")

    # 测试2: 获取买入信号
    print("\n\n测试2: 获取买入信号(15分钟推荐度最高)")
    print("-" * 80)

    buy_signals = service.get_top_gainers_by_recommendation(limit=10)

    if buy_signals:
        print(f"\n找到 {len(buy_signals)} 个强烈买入信号:\n")

        for i, signal in enumerate(buy_signals, 1):
            symbol = signal['symbol']
            recommend = signal.get('recommend_all_15', 0)
            rsi = signal.get('rsi_14_15', 0)
            print(f"{i}. {symbol:15} 推荐度:{recommend:.1f} RSI:{rsi:.1f}")
    else:
        print("\n暂无买入信号")

    # 测试3: RSI超卖/超买
    print("\n\n测试3: RSI超卖区间(30以下)")
    print("-" * 80)

    oversold = service.get_symbols_with_rsi(min_rsi=0, max_rsi=30, limit=10)

    if oversold:
        print(f"\n找到 {len(oversold)} 个超卖币种:\n")

        for i, coin in enumerate(oversold, 1):
            rsi = coin.get('rsi_value', 0)
            print(f"{i}. {coin['symbol']:15} RSI:{rsi:.1f} (超卖)")
    else:
        print("\n暂无超卖币种")

    print("\n" + "=" * 80)
