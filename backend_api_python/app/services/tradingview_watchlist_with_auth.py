"""
TradingView Watchlist API - 使用认证Cookie
支持使用用户提供的cookies访问私有关注列表
"""
import requests
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewWatchlistWithAuth:
    """使用Cookie认证的TradingView Watchlist服务"""

    def __init__(self, cookies: Optional[str] = None):
        """
        初始化服务

        Args:
            cookies: TradingView的cookies字符串
        """
        self.base_url = "https://www.tradingview.com/api/v1"
        self.session = requests.Session()

        # 设置headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.tradingview.com/',
            'Origin': 'https://www.tradingview.com',
        })

        # 如果提供了cookies,解析并设置
        if cookies:
            self._parse_and_set_cookies(cookies)

    def _parse_and_set_cookies(self, cookies_string: str):
        """解析cookie字符串并设置到session"""
        try:
            # cookie格式: key1=value1; key2=value2; ...
            cookie_pairs = cookies_string.split(';')

            for pair in cookie_pairs:
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.session.cookies.set(key.strip(), value.strip())

            logger.info(f"✅ 设置了 {len(self.session.cookies)} 个cookies")

        except Exception as e:
            logger.warning(f"解析cookies失败: {e}")

    def get_custom_watchlist(
        self,
        list_id: str = "104353945",
        unsafe: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取自定义关注列表

        Args:
            list_id: 关注列表ID
            unsafe: 是否使用unsafe参数

        Returns:
            币种列表
        """
        try:
            url = f"{self.base_url}/symbols_list/custom/{list_id}/replace/"
            params = {'unsafe': 'true'} if unsafe else {}

            logger.info(f"正在获取自定义关注列表: {url}")

            response = self.session.get(url, params=params, timeout=15)

            logger.info(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    if isinstance(data, list):
                        logger.info(f"✅ 成功获取 {len(data)} 个币种")
                        return self._parse_watchlist_data(data)
                    else:
                        logger.warning(f"API返回非列表数据: {type(data)}")
                        # 保存响应用于调试
                        with open('/tmp/tradingview_api_response.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        logger.info("已保存API响应到 /tmp/tradingview_api_response.json")
                        return []

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
                    symbol = item.get('symbol', '')
                    name = item.get('name', '')
                    description = item.get('description', '')
                    exchange = item.get('exchange', 'Unknown')
                    type_val = item.get('type', '')
                    currency_id = item.get('currency_id', '')

                    # 提取币种信息
                    clean_symbol = symbol.replace('BINANCE:', '') if 'BINANCE:' in symbol else symbol

                    result.append({
                        'symbol': clean_symbol,
                        'full_symbol': symbol,
                        'name': name,
                        'description': description or name,
                        'exchange': exchange,
                        'type': type_val,
                        'currency_id': currency_id,
                        'price': item.get('price', 0),
                        'change': item.get('change', 0),
                        'change_percentage': item.get('change_percentage', 0),
                        'volume': item.get('volume', 0),
                        'market_cap': item.get('market_cap', 0),
                        'source': 'TradingView Custom Watchlist'
                    })
                except Exception as e:
                    logger.debug(f"解析单个币种失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析关注列表数据失败: {e}")

        return result

    def get_all_watchlists(self) -> List[Dict[str, Any]]:
        """
        获取用户所有的关注列表

        Returns:
            关注列表列表
        """
        try:
            # 这个API可能需要特殊权限
            url = f"{self.base_url}/user_id/watchlists/"

            logger.info(f"正在获取所有关注列表: {url}")

            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 找到 {len(data)} 个关注列表")
                return data
            else:
                logger.warning(f"获取关注列表列表失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"获取所有关注列表失败: {e}")
            return []


# 全局实例(使用用户提供的cookies)
USER_COOKIES = "cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings={\"analytics\":true,\"advertising\":true}; _ga=GA1.1.1784921442.1765155922; g_state={\"i_l\":0,\"i_ll\":1765155927489}; device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; etg=undefined; cachec=undefined; _ga_YVVRYGL0E0=GS2.1.s1765155921$o1$g1$t1765156051$j60$l0$h0; _sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.6.1767983013.1767980054.5b548745-3276-4b37-a1d0-7cd05c81f085.308f7eec-7b41-482c-ad44-e0992e5cdd12.a7fe88e2-fc19-4c6a-90dd-0615d13b67fd.1767983013233.1; _sp_ses.cf1a=*"

# 便捷函数
def get_custom_watchlist(
    list_id: str = "104353945",
    cookies: str = None
) -> List[Dict[str, Any]]:
    """
    获取TradingView自定义关注列表

    Args:
        list_id: 关注列表ID
        cookies: TradingView cookies (可选,默认使用内置cookies)

    Returns:
        币种列表
    """
    cookies_to_use = cookies or USER_COOKIES
    service = TradingViewWatchlistWithAuth(cookies_to_use)
    return service.get_custom_watchlist(list_id)


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("TradingView自定义关注列表测试 (使用Cookie认证)")
    print("=" * 80)

    # 测试: 使用默认cookies获取
    print("\n测试: 获取自定义关注列表")
    print("-" * 80)

    service = TradingViewWatchlistWithAuth(USER_COOKIES)
    watchlist = service.get_custom_watchlist()

    if watchlist:
        print(f"\n✅ 成功获取 {len(watchlist)} 个币种:\n")

        for i, coin in enumerate(watchlist, 1):
            print(f"{i:2d}. {coin['symbol']:30} {coin['name']:30} "
                  f"价格:{coin.get('price', 0):>12.2f} "
                  f"涨跌:{coin.get('change_percentage', 0):>+8.2f}%")
    else:
        print("❌ 未能获取到数据")

    print("\n" + "=" * 80)
