"""
TradingView关注列表API服务
从用户的TradingView关注列表获取币种和HAMA指标数据
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewWatchlistAPI:
    """TradingView关注列表API服务"""

    def __init__(self):
        # TradingView关注列表API端点
        self.api_url = "https://www.tradingview.com/api/v1/symbols_list/active/104353945/"

        # TradingView Cookie (用于认证)
        self.tv_cookie = (
            "cookiePrivacyPreferenceBannerProduction=notApplicable; "
            "cookiesSettings={\"analytics\":true,\"advertising\":true}; "
            "_ga=GA1.1.1784921442.1765155922; "
            "g_state={\"i_l\":0,\"i_ll\":1765155927489}; "
            "device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; "
            "sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; "
            "sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; "
            "etg=undefined; cachec=undefined; "
            "_ga_YVVRYGL0E0=GS2.1.s1765155921$o1$g1$t1765156051$j60$l0$h0; "
            "_sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.4.1767972515.1767938774.c0a7c7c9-7259-4e0f-9f32-d4899aa408a0.c63288ff-0cbd-4c88-900a-30bf1c67d3f1.e00e97b8-52a1-4c79-8d30-cd85c37b8970.1767972514706.1; "
            "_sp_ses.cf1a=*"
        )

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.tradingview.com/',
            'Origin': 'https://www.tradingview.com',
            'Cookie': self.tv_cookie
        }

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

    def get_watchlist_symbols(self) -> List[Dict[str, Any]]:
        """
        获取TradingView关注列表中的币种

        Returns:
            币种列表
        """
        try:
            logger.info(f"正在获取TradingView关注列表: {self.api_url}")

            response = requests.get(
                self.api_url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功获取关注列表数据")

                # 解析数据
                result = []
                for item in data:
                    try:
                        symbol = item.get('symbol', '')
                        if not symbol:
                            continue

                        # 过滤加密货币USDT交易对
                        if 'USDT' in symbol and item.get('type') in ['crypto', 'bitcoin']:
                            result.append({
                                'symbol': symbol,
                                'base_asset': symbol.replace('USDT', '').replace('BINANCE:', '').replace('OKX:', ''),
                                'description': item.get('description', ''),
                                'exchange': item.get('exchange', ''),
                                'type': item.get('type', ''),
                                'price': float(item.get('price', 0)) if item.get('price') else 0,
                                'change': float(item.get('change', 0)) if item.get('change') else 0,
                                'change_percentage': float(item.get('change_percentage', 0)) if item.get('change_percentage') else 0,
                                'volume': float(item.get('volume', 0)) if item.get('volume') else 0,
                                'market_cap': float(item.get('market_cap', 0)) if item.get('market_cap') else 0,
                                'source': 'TradingView Watchlist'
                            })
                    except Exception as e:
                        logger.debug(f"处理币种数据失败: {e}")
                        continue

                logger.info(f"✅ 成功解析{len(result)}个币种")
                return result

            else:
                logger.error(f"❌ API请求失败: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络错误: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 获取关注列表失败: {e}")
            return []

    def get_watchlist_with_hama_indicators(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取关注列表币种及其HAMA指标

        Args:
            limit: 限制返回数量

        Returns:
            包含HAMA指标的币种列表
        """
        # 获取关注列表
        symbols = self.get_watchlist_symbols()

        if not symbols:
            logger.warning("关注列表为空,无法获取HAMA指标")
            return []

        # 限制数量
        if limit:
            symbols = symbols[:limit]

        logger.info(f"开始为{len(symbols)}个币种获取HAMA指标...")

        result = []
        from app.services.tradingview_service import TradingViewDataService

        tv_service = TradingViewDataService()

        for symbol_info in symbols:
            try:
                symbol = symbol_info['symbol']

                # 转换symbol格式 (BINANCE:BTCUSDT -> BTCUSDT)
                clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol

                logger.info(f"正在获取 {clean_symbol} 的HAMA指标...")

                # 获取HAMA指标
                hama_data = tv_service.get_hama_cryptocurrency_signals(clean_symbol)

                # 合并数据
                result.append({
                    'symbol': clean_symbol,
                    'base_asset': symbol_info['base_asset'],
                    'description': symbol_info['description'],
                    'exchange': symbol_info.get('exchange', 'Binance'),
                    'market': 'futures',

                    # TradingView价格数据
                    'price': symbol_info.get('price', 0),
                    'change': symbol_info.get('change', 0),
                    'change_percentage': symbol_info.get('change_percentage', 0),
                    'volume': symbol_info.get('volume', 0),

                    # HAMA指标
                    'hama_trend': hama_data.get('trend'),
                    'hama_pattern': hama_data.get('candle_pattern'),
                    'hama_recommendation': hama_data.get('recommendation'),
                    'hama_confidence': hama_data.get('confidence'),

                    # 技术指标
                    'rsi': hama_data.get('technical_indicators', {}).get('rsi', 0),
                    'macd': hama_data.get('technical_indicators', {}).get('macd', 'neutral'),
                    'ema_20': hama_data.get('technical_indicators', {}).get('ema_20', 0),
                    'ema_50': hama_data.get('technical_indicators', {}).get('ema_50', 0),

                    # 支撑位/阻力位
                    'support_level': hama_data.get('technical_indicators', {}).get('support_level', 0),
                    'resistance_level': hama_data.get('technical_indicators', {}).get('resistance_level', 0),

                    # 信号数据
                    'ha_close': hama_data.get('signals', {}).get('ha_close', 0),
                    'ha_open': hama_data.get('signals', {}).get('ha_open', 0),
                    'trend_strength': hama_data.get('signals', {}).get('trend_strength', 'weak'),

                    'timestamp': datetime.now().isoformat()
                })

                # 避免请求过快
                import time
                time.sleep(1)

            except Exception as e:
                logger.error(f"获取{symbol_info.get('symbol')}指标失败: {e}")
                continue

        logger.info(f"✅ 成功获取{len(result)}个币种的完整数据")
        return result

    def get_top_gainers_from_watchlist(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从关注列表获取涨幅榜TOP币种

        Args:
            limit: 返回数量

        Returns:
            按涨幅排序的币种列表
        """
        symbols_with_indicators = self.get_watchlist_with_hama_indicators()

        if not symbols_with_indicators:
            return []

        # 按涨跌幅排序
        sorted_symbols = sorted(
            symbols_with_indicators,
            key=lambda x: float(x.get('change_percentage', 0)),
            reverse=True
        )

        return sorted_symbols[:limit]

    def get_buy_signals_from_watchlist(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        从关注列表获取HAMA买入信号币种

        Args:
            limit: 返回数量

        Returns:
            HAMA建议为BUY的币种列表
        """
        symbols_with_indicators = self.get_watchlist_with_hama_indicators(limit)

        if not symbols_with_indicators:
            return []

        # 过滤买入信号
        buy_signals = [
            s for s in symbols_with_indicators
            if s.get('hama_recommendation') == 'BUY'
        ]

        # 按置信度排序
        buy_signals.sort(key=lambda x: x.get('hama_confidence', 0), reverse=True)

        return buy_signals


# 便捷函数
def get_tradingview_watchlist(limit: int = None) -> List[Dict[str, Any]]:
    """获取TradingView关注列表"""
    service = TradingViewWatchlistAPI()
    return service.get_watchlist_symbols()[:limit] if limit else service.get_watchlist_symbols()


def get_watchlist_with_hama(limit: int = None) -> List[Dict[str, Any]]:
    """获取关注列表及HAMA指标"""
    service = TradingViewWatchlistAPI()
    return service.get_watchlist_with_hama_indicators(limit)


def get_watchlist_buy_signals(limit: int = None) -> List[Dict[str, Any]]:
    """获取关注列表中的买入信号"""
    service = TradingViewWatchlistAPI()
    return service.get_buy_signals_from_watchlist(limit)


# 测试代码
if __name__ == "__main__":
    import json

    service = TradingViewWatchlistAPI()

    print("=" * 80)
    print("TradingView关注列表 + HAMA指标")
    print("=" * 80)

    # 测试获取关注列表
    print("\n📊 测试1: 获取关注列表")
    print("-" * 80)
    symbols = service.get_watchlist_symbols()
    print(f"✅ 获取到 {len(symbols)} 个币种")

    if symbols:
        print("\nTOP5币种:")
        for i, s in enumerate(symbols[:5], 1):
            print(f"{i}. {s['symbol']:20} 价格: ${s['price']:10.2f}  涨跌: {s['change_percentage']:+6.2f}%")

    # 测试获取HAMA指标
    print("\n📈 测试2: 获取关注列表 + HAMA指标")
    print("-" * 80)
    result = service.get_watchlist_with_hama_indicators(limit=5)

    print(f"\n✅ 获取到 {len(result)} 个币种的HAMA指标:\n")

    for item in result:
        print(f"币种: {item['symbol']}")
        print(f"  价格: ${item['price']:,.2f}")
        print(f"  涨跌幅: {item['change_percentage']:+.2f}%")
        print(f"  HAMA趋势: {item['hama_trend']}")
        print(f"  HAMA建议: {item['hama_recommendation']}")
        print(f"  置信度: {item['hama_confidence']*100:.0f}%")
        print(f"  RSI: {item['rsi']:.2f}")
        print(f"  MACD: {item['macd']}")
        print()

    # 测试买入信号
    print("🟢 测试3: 获取买入信号")
    print("-" * 80)
    buy_signals = service.get_buy_signals_from_watchlist()

    if buy_signals:
        print(f"\n✅ 找到 {len(buy_signals)} 个买入信号:\n")
        for i, signal in enumerate(buy_signals, 1):
            print(f"{i}. {signal['symbol']:15} {signal['hama_trend']:12} 置信度: {signal['hama_confidence']*100:.0f}%")
    else:
        print("\n❌ 当前没有买入信号")

    print("\n" + "=" * 80)
