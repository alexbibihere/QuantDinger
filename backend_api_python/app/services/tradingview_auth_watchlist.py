"""
TradingView自定义关注列表服务 - 使用完整认证
"""
import requests
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewAuthWatchlist:
    """使用完整cookies认证的TradingView Watchlist服务"""

    # 完整的cookies
    FULL_COOKIES = (
        'cookiePrivacyPreferenceBannerProduction=notApplicable; '
        'cookiesSettings={"analytics":true,"advertising":true}; '
        '_ga=GA1.1.1784921442.1765155922; '
        'g_state={"i_l":0,"i_ll":1765155927489}; '
        'device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; '
        'sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; '
        'sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; '
        'etg=undefined; '
        'cachec=undefined; '
        '_ga_YVVRYGL0E0=GS2.1.s1765155921$o1$g1$t1765156051$j60$l0$h0; '
        '_sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.6.1767983013.1767980054.5b548745-3276-4b37-a1d0-7cd05c81f085.308f7eec-7b41-482c-ad44-e0992e5cdd12.a7fe88e2-fc19-4c6a-90dd-0615d13b67fd.1767983013233.1; '
        '_sp_ses.cf1a=*'
    )

    def __init__(self, cookies: Optional[str] = None):
        """初始化服务"""
        self.base_url = "https://www.tradingview.com"
        self.session = requests.Session()

        # 设置cookies
        cookies_to_use = cookies or self.FULL_COOKIES
        self._parse_cookies(cookies_to_use)

        # 设置headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://www.tradingview.com',
            'Referer': 'https://www.tradingview.com/',
        })

    def _parse_cookies(self, cookies_string: str):
        """解析cookie字符串"""
        for pair in cookies_string.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                self.session.cookies.set(key.strip(), value.strip())
        logger.info(f"✅ 设置了 {len(self.session.cookies)} 个cookies")

    def get_user_watchlists(self) -> List[Dict[str, Any]]:
        """获取用户所有的关注列表"""
        try:
            # 方法1: 尝试获取用户ID相关的watchlist
            url = f"{self.base_url}/api/v1/user_id/watchlists/"

            logger.info(f"正在获取用户关注列表列表: {url}")
            response = self.session.get(url, timeout=15)

            logger.info(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"✅ 成功获取用户关注列表")
                    return data if isinstance(data, list) else []
                except:
                    pass

            # 方法2: 尝试通过sessionid获取用户信息
            logger.info("尝试获取用户信息...")

            # 访问个人主页获取user_id
            profile_url = f"{self.base_url}/u/{self.session.cookies.get('sessionid', '')[:20]}/"
            response = self.session.get(profile_url, timeout=10)

            if response.status_code == 200:
                # 从页面中提取user_id
                import re
                user_ids = re.findall(r'userId["\']?\s*[:=]\s*["\']?(\d+)', response.text)
                if user_ids:
                    user_id = user_ids[0]
                    logger.info(f"找到user_id: {user_id}")

                    # 使用user_id获取watchlists
                    watchlist_url = f"{self.base_url}/api/v1/{user_id}/watchlists/"
                    response = self.session.get(watchlist_url, timeout=15)

                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ 成功获取关注列表")
                        return data if isinstance(data, list) else []

            return []

        except Exception as e:
            logger.error(f"获取用户关注列表失败: {e}", exc_info=True)
            return []

    def get_custom_watchlist(self, list_id: str = "104353945") -> List[Dict[str, Any]]:
        """
        获取指定ID的关注列表

        Args:
            list_id: 关注列表ID
        """
        try:
            url = f"{self.base_url}/api/v1/symbols_list/custom/{list_id}/replace/"

            logger.info(f"正在获取关注列表 {list_id}")

            # POST请求,发送空列表
            response = self.session.post(
                url,
                json=[],  # 空列表表示获取全部
                params={'unsafe': 'true'},
                timeout=15
            )

            logger.info(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, list):
                    logger.info(f"✅ 成功获取 {len(data)} 个币种")

                    if len(data) > 0:
                        logger.info(f"第一个币种: {json.dumps(data[0], ensure_ascii=False)[:200]}")

                    return self._parse_symbols(data)
                else:
                    logger.warning(f"返回数据格式错误: {type(data)}")
                    return []
            else:
                logger.error(f"API请求失败: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return []

        except Exception as e:
            logger.error(f"获取自定义关注列表失败: {e}", exc_info=True)
            return []

    def _parse_symbols(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """解析币种数据"""
        result = []

        for item in data:
            try:
                symbol = item.get('symbol', '')
                name = item.get('name', '')
                exchange = item.get('exchange', '')
                type_val = item.get('type', '')

                # 清理symbol
                clean_symbol = symbol.replace('BINANCE:', '') if 'BINANCE:' in symbol else symbol

                result.append({
                    'symbol': clean_symbol,
                    'full_symbol': symbol,
                    'name': name,
                    'exchange': exchange,
                    'type': type_val,
                    'price': item.get('price', 0),
                    'change': item.get('change', 0),
                    'change_percentage': item.get('change_percentage', 0),
                    'volume': item.get('volume', 0),
                    'market_cap': item.get('market_cap', 0),
                    'description': item.get('description', name),
                    'currency_id': item.get('currency_id', ''),
                    'source': 'TradingView Custom Watchlist'
                })
            except Exception as e:
                logger.debug(f"解析币种失败: {e}")
                continue

        return result

    def get_default_crypto_watchlist(self) -> List[Dict[str, Any]]:
        """获取默认的加密货币列表"""
        try:
            # 使用TradingView Scanner API获取加密货币
            url = "https://scanner.tradingview.com/crypto/scan"

            # 常见的加密货币列表
            symbols = [
                'BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:BNBUSDT',
                'BINANCE:SOLUSDT', 'BINANCE:XRPUSDT', 'BINANCE:ADAUSDT',
                'BINANCE:DOGEUSDT', 'BINANCE:MATICUSDT', 'BINANCE:DOTUSDT',
                'BINANCE:AVAXUSDT', 'BINANCE:LINKUSDT', 'BINANCE:UNIUSDT',
                'BINANCE:LTCUSDT', 'BINANCE:ATOMUSDT', 'BINANCE:NEARUSDT',
                'BINANCE:APTUSDT', 'BINANCE:OPUSDT', 'BINANCE:ARBUSDT',
                'BINANCE:INJUSDT', 'BINANCE:QNTUSDT'
            ]

            payload = {
                'symbols': {'tickers': symbols},
                'columns': [
                    'name', 'description', 'close', 'change',
                    'volume', 'market_cap', 'RSI|14|0'
                ]
            }

            logger.info("正在获取加密货币列表...")
            response = self.session.post(url, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                scan_data = data.get('data', [])

                logger.info(f"✅ 获取到 {len(scan_data)} 个币种")

                return self._parse_scanner_data(scan_data)

            return []

        except Exception as e:
            logger.error(f"获取默认列表失败: {e}")
            return []

    def _parse_scanner_data(self, scan_data: List) -> List[Dict[str, Any]]:
        """解析Scanner数据"""
        result = []

        for row in scan_data:
            try:
                if len(row) >= 2:
                    symbol = row[0]
                    values = row[1] if len(row) > 1 else []

                    clean_symbol = symbol.replace('BINANCE:', '') if ':' in symbol else symbol

                    result.append({
                        'symbol': clean_symbol,
                        'full_symbol': symbol,
                        'name': values[1] if len(values) > 1 else clean_symbol,
                        'exchange': 'Binance',
                        'price': values[2] if len(values) > 2 else 0,
                        'change': values[3] if len(values) > 3 else 0,
                        'volume': values[4] if len(values) > 4 else 0,
                        'market_cap': values[5] if len(values) > 5 else 0,
                        'rsi': values[6] if len(values) > 6 else 0,
                        'source': 'TradingView Scanner'
                    })
            except:
                continue

        return result


# 便捷函数
def get_tradingview_watchlist(list_id: str = None) -> List[Dict[str, Any]]:
    """
    获取TradingView关注列表

    Args:
        list_id: 关注列表ID (可选)

    Returns:
        币种列表
    """
    service = TradingViewAuthWatchlist()

    # 如果指定了list_id,尝试获取自定义列表
    if list_id:
        watchlist = service.get_custom_watchlist(list_id)
        if watchlist:
            return watchlist

    # 否则返回默认列表
    return service.get_default_crypto_watchlist()


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("TradingView关注列表测试")
    print("=" * 80)

    service = TradingViewAuthWatchlist()

    # 测试1: 获取自定义列表
    print("\n测试1: 获取自定义关注列表 (104353945)")
    print("-" * 80)
    watchlist = service.get_custom_watchlist("104353945")

    if watchlist:
        print(f"✅ 获取到 {len(watchlist)} 个币种:\n")
        for i, coin in enumerate(watchlist[:20], 1):
            print(f"{i:2d}. {coin['symbol']:30} {coin['name']:20} "
                  f"价格:{coin.get('price', 0):>12.2f}")
    else:
        print("❌ 列表为空或获取失败")

    # 测试2: 获取默认加密货币列表
    print("\n\n测试2: 获取默认加密货币列表")
    print("-" * 80)
    default_list = service.get_default_crypto_watchlist()

    if default_list:
        print(f"✅ 获取到 {len(default_list)} 个币种:\n")
        for i, coin in enumerate(default_list[:20], 1):
            print(f"{i:2d}. {coin['symbol']:30} {coin['name']:20} "
                  f"价格:{coin.get('price', 0):>12.2f} 涨跌:{coin.get('change', 0):>+8.2f}%")

    print("\n" + "=" * 80)
