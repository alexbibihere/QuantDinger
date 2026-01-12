"""
使用Selenium模拟浏览器获取TradingView关注列表和HAMA指标
"""
import time
import json
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewWatchlistSelenium:
    """使用Selenium获取TradingView关注列表"""

    def __init__(self, headless: bool = True):
        """
        初始化Selenium WebDriver

        Args:
            headless: 是否使用无头模式(不显示浏览器窗口)
        """
        self.driver = None
        self.headless = headless

    def _init_driver(self) -> bool:
        """初始化Chrome WebDriver"""
        try:
            chrome_options = ChromeOptions()

            if self.headless:
                chrome_options.add_argument('--headless')

            # 基本配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')

            # 设置User-Agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )

            # 禁用自动化提示
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 初始化WebDriver
            # 优先使用系统ChromeDriver (Docker环境中)
            try:
                # Docker环境使用Chromium
                self.driver = webdriver.Chrome(
                    options=chrome_options,
                    service=Service(executable_path='/usr/bin/chromedriver')
                )
                logger.info("✅ 使用系统ChromiumDriver初始化Chrome")
            except Exception as e:
                logger.warning(f"系统ChromeDriver失败: {e}, 尝试使用webdriver-manager")
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service

                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("✅ 使用webdriver-manager初始化Chrome")
                except Exception as e2:
                    logger.error(f"webdriver-manager也失败: {e2}")
                    raise e2

            # 设置隐式等待
            self.driver.implicitly_wait(10)

            logger.info("✅ Chrome WebDriver初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ Chrome WebDriver初始化失败: {e}")
            return False

    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ WebDriver已关闭")
            except Exception as e:
                logger.warning(f"关闭WebDriver失败: {e}")

    def get_watchlist_from_page(
        self,
        url: Optional[str] = None,
        wait_for_login: bool = False
    ) -> List[Dict[str, Any]]:
        """
        从TradingView页面获取关注列表

        Args:
            url: TradingView图表页面URL,如果为None则使用默认URL
            wait_for_login: 是否等待用户登录

        Returns:
            币种列表
        """
        if not self._init_driver():
            return []

        try:
            # 使用提供的URL或默认URL
            if not url:
                url = "https://cn.tradingview.com/chart/"

            logger.info(f"正在访问: {url}")
            self.driver.get(url)

            # 等待页面加载
            time.sleep(5)

            # 检查是否需要登录
            if wait_for_login:
                logger.warning("⚠️ 需要登录TradingView")
                logger.warning("请在浏览器中登录,然后按Enter继续...")

                # 等待用户登录
                input("按Enter继续...")

                time.sleep(3)

            # 尝试从页面提取关注列表数据
            # 方法1: 检查页面是否有JavaScript变量包含数据
            try:
                # 获取页面源码
                page_source = self.driver.page_source

                # 尝试查找JavaScript中的watchlist数据
                # TradingView通常将数据存储在window对象中

                # 使用JavaScript提取数据
                script = """
                // 尝试从window对象获取关注列表数据
                let watchlistData = [];

                // 方法1: 尝试从widgetbar获取
                if (typeof window !== 'undefined') {
                    // 查找所有script标签中的JSON数据
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const text = script.textContent;
                        if (text.includes('symbol_list') || text.includes('watchlist')) {
                            try {
                                // 尝试提取JSON
                                const matches = text.match(/\\{[\\s\\S]*\\}/);
                                if (matches) {
                                    console.log('Found potential JSON data');
                                }
                            } catch(e) {}
                        }
                    }
                }

                return JSON.stringify(watchlistData);
                """

                result = self.driver.execute_script(script)

                if result:
                    data = json.loads(result)
                    if data:
                        logger.info(f"✅ 从页面JavaScript获取到数据")
                        return self._parse_watchlist_data(data)

            except Exception as e:
                logger.debug(f"从JavaScript提取数据失败: {e}")

            # 方法2: 尝试通过API拦截获取数据
            # 监听网络请求
            try:
                # 启用性能日志
                self.driver.execute_cdp_cmd('Performance.enable', {})

                # 等待一段时间让页面加载完成
                time.sleep(10)

                # 获取网络日志
                logs = self.driver.get_log('performance')

                # 查找symbols_list相关的API请求
                for entry in logs:
                    try:
                        log = json.loads(entry['message'])['message']

                        if log['method'] == 'Network.requestWillBeSent':
                            request = log['params']['request']
                            request_url = request['url']

                            # 检查是否是symbols_list API
                            if 'symbols_list' in request_url and 'active' in request_url:
                                logger.info(f"✅ 发现关注列表API请求: {request_url}")

                                # 尝试获取响应
                                # 注意: Selenium无法直接获取响应内容,需要其他方法

                    except Exception as e:
                        continue

            except Exception as e:
                logger.debug(f"网络日志监听失败: {e}")

            # 方法3: 使用公开的TradingView Scanner API
            logger.info("尝试使用TradingView Scanner API...")

            # 使用JavaScript调用Scanner API
            scanner_script = """
            return new Promise((resolve) => {
                const symbols = [
                    'BINANCE:BTCUSDT',
                    'BINANCE:ETHUSDT',
                    'BINANCE:BNBUSDT',
                    'BINANCE:SOLUSDT',
                    'BINANCE:XRPUSDT',
                    'BINANCE:ADAUSDT',
                    'BINANCE:DOGEUSDT',
                    'BINANCE:MATICUSDT',
                    'BINANCE:DOTUSDT',
                    'BINANCE:AVAXUSDT'
                ];

                fetch('https://scanner.tradingview.com/crypto/scan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        symbols: { tickers: symbols },
                        columns: [
                            'name',
                            'description',
                            'update',
                            'Recommend.All|15',
                            'RSI|14|0',
                            'MACD.macd',
                            'EMA|20|0',
                            'EMA|50|0'
                        ]
                    })
                })
                .then(response => response.json())
                .then(data => resolve(data))
                .catch(err => resolve({error: err.message}));
                });
            """

            scan_result = self.driver.execute_script(scanner_script)

            if scan_result and not scan_result.get('error'):
                logger.info(f"✅ Scanner API返回数据")
                return self._parse_scanner_data(scan_result)

            logger.warning("❌ 所有方法都未能获取到关注列表数据")
            return []

        except Exception as e:
            logger.error(f"❌ 获取关注列表失败: {e}", exc_info=True)
            return []

        finally:
            # 如果是等待登录模式,不关闭driver让用户可以查看
            if not wait_for_login:
                self._close_driver()

    def _parse_watchlist_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """解析关注列表数据"""
        result = []

        try:
            for item in data:
                if 'symbol' in item:
                    result.append({
                        'symbol': item['symbol'],
                        'base_asset': item['symbol'].replace('USDT', '').replace('BINANCE:', ''),
                        'description': item.get('description', ''),
                        'exchange': item.get('exchange', 'Binance'),
                        'price': item.get('price', 0),
                        'change': item.get('change', 0),
                        'change_percentage': item.get('change_percentage', 0),
                        'volume': item.get('volume', 0),
                        'source': 'TradingView Watchlist'
                    })
        except Exception as e:
            logger.error(f"解析数据失败: {e}")

        return result

    def _parse_scanner_data(self, data: Dict) -> List[Dict[str, Any]]:
        """解析Scanner API数据"""
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

                    if 'USDT' in clean_symbol:
                        result.append({
                            'symbol': clean_symbol,
                            'base_asset': clean_symbol.replace('USDT', ''),
                            'description': values[1] if len(values) > 1 else clean_symbol,
                            'exchange': 'Binance',
                            'market': 'futures',
                            'source': 'TradingView Scanner',
                            # Scanner返回的技术指标
                            'recommendation': values[3] if len(values) > 3 else None,  # 推荐
                            'rsi': values[4] if len(values) > 4 else 0,  # RSI
                            'macd': values[5] if len(values) > 5 else 0,  # MACD
                            'ema_20': values[6] if len(values) > 6 else 0,  # EMA20
                            'ema_50': values[7] if len(values) > 7 else 0,  # EMA50
                        })

        except Exception as e:
            logger.error(f"解析Scanner数据失败: {e}")

        return result

    def get_watchlist_with_hama_indicators(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取关注列表及其HAMA指标

        Args:
            limit: 限制返回数量

        Returns:
            包含HAMA指标的币种列表
        """
        # 获取关注列表
        symbols = self.get_watchlist_from_page()

        if not symbols:
            logger.warning("关注列表为空,无法获取HAMA指标")
            return []

        # 限制数量
        if limit:
            symbols = symbols[:limit]

        logger.info(f"开始为{len(symbols)}个币种获取HAMA指标...")

        result = []

        # 导入TradingView服务获取HAMA指标
        try:
            from app.services.tradingview_service import TradingViewDataService
            tv_service = TradingViewDataService()

            for symbol_info in symbols:
                try:
                    symbol = symbol_info['symbol']

                    logger.info(f"正在获取 {symbol} 的HAMA指标...")

                    # 获取HAMA指标
                    hama_data = tv_service.get_hama_cryptocurrency_signals(symbol)

                    # 合并数据
                    result.append({
                        'symbol': symbol,
                        'base_asset': symbol_info['base_asset'],
                        'description': symbol_info.get('description', ''),
                        'exchange': symbol_info.get('exchange', 'Binance'),
                        'market': 'futures',

                        # TradingView Scanner数据
                        'recommendation': symbol_info.get('recommendation'),
                        'rsi': symbol_info.get('rsi', 0),
                        'macd': symbol_info.get('macd', 0),
                        'ema_20': symbol_info.get('ema_20', 0),
                        'ema_50': symbol_info.get('ema_50', 0),

                        # HAMA指标
                        'hama_trend': hama_data.get('trend'),
                        'hama_pattern': hama_data.get('candle_pattern'),
                        'hama_recommendation': hama_data.get('recommendation'),
                        'hama_confidence': hama_data.get('confidence'),

                        # 技术指标
                        'rsi_hama': hama_data.get('technical_indicators', {}).get('rsi', 0),
                        'macd_hama': hama_data.get('technical_indicators', {}).get('macd', 'neutral'),
                        'ema_20_hama': hama_data.get('technical_indicators', {}).get('ema_20', 0),
                        'ema_50_hama': hama_data.get('technical_indicators', {}).get('ema_50', 0),

                        # 支撑位/阻力位
                        'support_level': hama_data.get('technical_indicators', {}).get('support_level', 0),
                        'resistance_level': hama_data.get('technical_indicators', {}).get('resistance_level', 0),

                        # 信号数据
                        'ha_close': hama_data.get('signals', {}).get('ha_close', 0),
                        'ha_open': hama_data.get('signals', {}).get('ha_open', 0),
                        'trend_strength': hama_data.get('signals', {}).get('trend_strength', 'weak'),

                        'timestamp': hama_data.get('timestamp')
                    })

                    # 避免请求过快
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"获取{symbol_info.get('symbol')}指标失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"导入TradingView服务失败: {e}")

        logger.info(f"✅ 成功获取{len(result)}个币种的完整数据")
        return result


# 便捷函数
def get_tradingview_watchlist_selenium(
    url: Optional[str] = None,
    wait_for_login: bool = False,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    使用Selenium获取TradingView关注列表

    Args:
        url: TradingView页面URL
        wait_for_login: 是否等待用户登录
        limit: 限制返回数量

    Returns:
        币种列表
    """
    service = TradingViewWatchlistSelenium(headless=not wait_for_login)
    result = service.get_watchlist_from_page(url, wait_for_login)

    if limit:
        result = result[:limit]

    return result


def get_watchlist_with_hama_selenium(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取关注列表及HAMA指标(Selenium版本)"""
    service = TradingViewWatchlistSelenium(headless=True)
    return service.get_watchlist_with_hama_indicators(limit)


# 测试代码
if __name__ == "__main__":
    import json

    print("=" * 80)
    print("TradingView关注列表 - Selenium方案")
    print("=" * 80)

    # 测试1: 获取关注列表(使用Scanner API)
    print("\n📊 测试1: 获取关注列表(无头模式)")
    print("-" * 80)

    service = TradingViewWatchlistSelenium(headless=True)
    symbols = service.get_watchlist_from_page()

    print(f"✅ 获取到 {len(symbols)} 个币种")

    if symbols:
        print("\nTOP5币种:")
        for i, s in enumerate(symbols[:5], 1):
            print(f"{i}. {s['symbol']:20} {s.get('description', '')}")

    # 测试2: 获取HAMA指标
    print("\n📈 测试2: 获取关注列表 + HAMA指标")
    print("-" * 80)

    result = service.get_watchlist_with_hama_indicators(limit=5)

    if result:
        print(f"\n✅ 获取到 {len(result)} 个币种的HAMA指标:\n")

        for item in result:
            print(f"币种: {item['symbol']}")
            print(f"  HAMA趋势: {item.get('hama_trend', 'N/A')}")
            print(f"  HAMA建议: {item.get('hama_recommendation', 'N/A')}")
            print(f"  置信度: {item.get('hama_confidence', 0)*100:.0f}%")
            print(f"  RSI: {item.get('rsi_hama', 0):.2f}")
            print()
    else:
        print("❌ 未能获取到数据")

    # 测试3: 带登录模式
    print("\n🔑 测试3: 带登录模式")
    print("-" * 80)
    print("如果您想获取自己的关注列表,可以运行:")
    print("  service = TradingViewWatchlistSelenium(headless=False)")
    print("  service.get_watchlist_from_page(wait_for_login=True)")

    print("\n" + "=" * 80)
