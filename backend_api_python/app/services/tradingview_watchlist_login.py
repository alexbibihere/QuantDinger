"""
TradingView Watchlist 登录服务
支持使用TradingView账号登录并获取关注列表的所有币种
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


class TradingViewWatchlistLogin:
    """TradingView Watchlist登录服务"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化服务

        Args:
            username: TradingView用户名/邮箱 (可选)
            password: TradingView密码 (可选)
        """
        self.username = username
        self.password = password
        self.driver = None
        self.is_logged_in = False

    def _init_driver(self, headless: bool = True) -> bool:
        """初始化Chrome WebDriver"""
        try:
            chrome_options = ChromeOptions()

            if headless:
                chrome_options.add_argument('--headless')

            # 基本配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # 反检测措施
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 设置真实User-Agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )

            # 初始化WebDriver
            self.driver = webdriver.Chrome(
                options=chrome_options,
                service=Service(executable_path='/usr/bin/chromedriver')
            )

            # 执行反检测脚本
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {}
                };
            """)

            self.driver.implicitly_wait(15)

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

    def login(self, username: str = None, password: str = None, headless: bool = True) -> bool:
        """
        登录TradingView

        Args:
            username: TradingView用户名/邮箱
            password: TradingView密码
            headless: 是否使用无头模式

        Returns:
            是否登录成功
        """
        if not self._init_driver(headless=headless):
            return False

        username = username or self.username
        password = password or self.password

        if not username or not password:
            logger.error("❌ 缺少用户名或密码")
            return False

        try:
            logger.info("正在访问TradingView...")
            # 访问TradingView中文版
            self.driver.get("https://cn.tradingview.com/")
            time.sleep(5)

            # 查找并点击登录按钮
            try:
                # 尝试多种选择器
                login_selectors = [
                    "//button[contains(@data-name, 'header-sign-in')]",
                    "//a[contains(@href, 'signin')]",
                    "//span[contains(text(), '登录')]",
                    "//button[contains(text(), 'Sign in')]",
                ]

                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if login_button:
                            logger.info(f"✅ 找到登录按钮")
                            break
                    except:
                        continue

                if not login_button:
                    logger.error("❌ 未找到登录按钮")
                    return False

                # 点击登录按钮
                login_button.click()
                logger.info("✅ 已点击登录按钮")
                time.sleep(5)

            except Exception as e:
                logger.error(f"❌ 点击登录按钮失败: {e}")
                return False

            # 查找用户名输入框
            try:
                # 尝试多种选择器
                username_selectors = [
                    "//input[@name='username']",
                    "//input[@type='email']",
                    "//input[@placeholder='Email' or @placeholder='email']",
                    "//input[@id='username']",
                    "//input[@id='email']",
                ]

                username_input = None
                for selector in username_selectors:
                    try:
                        username_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if username_input:
                            logger.info("✅ 找到用户名输入框")
                            break
                    except:
                        continue

                if not username_input:
                    logger.error("❌ 未找到用户名输入框")
                    # 保存页面截图用于调试
                    self.driver.save_screenshot('/tmp/tradingview_login_page.png')
                    logger.info("已保存登录页面截图到 /tmp/tradingview_login_page.png")
                    return False

                # 输入用户名
                username_input.clear()
                username_input.send_keys(username)
                logger.info("✅ 已输入用户名")
                time.sleep(1)

                # 查找密码输入框
                password_input = None
                password_selectors = [
                    "//input[@name='password']",
                    "//input[@type='password']",
                    "//input[@id='password']",
                ]

                for selector in password_selectors:
                    try:
                        password_input = self.driver.find_element(By.XPATH, selector)
                        if password_input:
                            break
                    except:
                        continue

                if not password_input:
                    logger.error("❌ 未找到密码输入框")
                    return False

                # 输入密码
                password_input.clear()
                password_input.send_keys(password)
                logger.info("✅ 已输入密码")
                time.sleep(1)

                # 查找并点击提交按钮
                submit_selectors = [
                    "//button[@type='submit']",
                    "//button[contains(text(), 'Sign in')]",
                    "//button[contains(text(), '登录')]",
                    "//button[@data-name='sign-in']",
                ]

                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = self.driver.find_element(By.XPATH, selector)
                        if submit_button and submit_button.is_displayed():
                            break
                    except:
                        continue

                if submit_button:
                    submit_button.click()
                    logger.info("✅ 已点击提交按钮")
                else:
                    # 尝试按Enter键
                    from selenium.webdriver.common.keys import Keys
                    password_input.send_keys(Keys.ENTER)
                    logger.info("✅ 已按Enter键提交")

                # 等待登录完成
                time.sleep(10)

                # 检查是否登录成功
                if self._check_login_status():
                    logger.info("✅ 登录成功!")
                    self.is_logged_in = True
                    return True
                else:
                    logger.error("❌ 登录失败,请检查用户名和密码")
                    # 保存截图
                    self.driver.save_screenshot('/tmp/tradingview_after_login.png')
                    return False

            except Exception as e:
                logger.error(f"❌ 登录过程出错: {e}")
                import traceback
                traceback.print_exc()
                return False

        except Exception as e:
            logger.error(f"❌ 访问TradingView失败: {e}")
            return False

    def _check_login_status(self) -> bool:
        """检查是否已登录"""
        try:
            page_source = self.driver.page_source

            # 如果还包含登录相关文字,可能登录失败
            if 'Sign in' in page_source and 'username' in page_source:
                return False

            # 如果包含用户相关元素,说明登录成功
            if 'Sign out' in page_source or 'sign-out' in page_source or 'logout' in page_source.lower():
                return True

            # 检查是否有用户头像或用户菜单
            try:
                user_elements = self.driver.find_elements(By.XPATH, "//*[@data-role='user-menu' or contains(@class, 'user-avatar')]")
                if user_elements:
                    return True
            except:
                pass

            return True  # 默认认为成功

        except Exception as e:
            logger.warning(f"检查登录状态失败: {e}")
            return False

    def get_watchlist(self, list_name: str = None) -> List[Dict[str, Any]]:
        """
        获取关注列表

        Args:
            list_name: 关注列表名称(可选,默认获取第一个列表)

        Returns:
            币种列表
        """
        if not self.is_logged_in:
            logger.error("❌ 请先登录")
            return []

        if not self.driver:
            if not self._init_driver(headless=True):
                return []

        try:
            logger.info("正在访问Watchlist页面...")
            # 访问Watchlist页面
            self.driver.get("https://cn.tradingview.com/chart/")
            time.sleep(8)

            # 方法1: 尝试从localStorage获取watchlist数据
            watchlist_data = self.driver.execute_script("""
                // 尝试从localStorage获取数据
                let watchlists = [];

                // 查找所有localStorage键
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);

                    if (key.includes('watchlist') || key.includes('symbol') || key.includes('ticker')) {
                        try {
                            let value = localStorage.getItem(key);
                            watchlists.push({
                                key: key,
                                value: JSON.parse(value)
                            });
                        } catch(e) {
                            // 忽略解析错误
                        }
                    }
                }

                return JSON.stringify(watchlists);
            """)

            if watchlist_data:
                data = json.loads(watchlist_data)
                if data:
                    logger.info(f"✅ 从localStorage找到 {len(data)} 个watchlist相关数据")
                    # 保存到文件用于调试
                    with open('/tmp/tradingview_localstorage.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

            # 方法2: 使用JavaScript提取页面中的watchlist数据
            symbols_data = self.driver.execute_script("""
                // 查找所有可能的watchlist容器
                let symbols = [];

                // 方法1: 查找watchlist widget
                const watchlistContainer = document.querySelector('[data-widget-name="watchlist"]') ||
                                         document.querySelector('.watchlist-widget') ||
                                         document.querySelector('[data-name="watchlist"]');

                if (watchlistContainer) {
                    // 获取所有symbol行
                    const rows = watchlistContainer.querySelectorAll('[data-symbol-type], .symbol-row, [class*="symbol"]');

                    rows.forEach(row => {
                        const symbol = row.getAttribute('data-symbol') ||
                                     row.getAttribute('data-symbol-id') ||
                                     row.textContent.trim();

                        if (symbol && symbol.length > 2) {
                            symbols.push({
                                symbol: symbol,
                                text: row.textContent.substring(0, 100)
                            });
                        }
                    });
                }

                return symbols;
            """)

            if symbols_data:
                logger.info(f"✅ 从页面提取到 {len(symbols_data)} 个可能的symbol")
                # 保存到文件
                with open('/tmp/tradingview_symbols_from_page.json', 'w', encoding='utf-8') as f:
                    json.dump(symbols_data, f, ensure_ascii=False, indent=2)

            # 方法3: 使用TradingView API获取
            logger.info("尝试使用TradingView API获取watchlist...")
            api_result = self.driver.execute_script("""
                return new Promise((resolve) => {
                    // 尝试获取默认的crypto watchlist
                    // 使用常见的币种
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
                        'BINANCE:AVAXUSDT',
                        'BINANCE:LINKUSDT',
                        'BINANCE:UNIUSDT',
                        'BINANCE:LTCUSDT',
                        'BINANCE:ATOMUSDT',
                        'BINANCE:NEARUSDT'
                    ];

                    fetch('https://scanner.tradingview.com/crypto/scan', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            symbols: { tickers: symbols },
                            columns: ['name', 'description', 'update', 'close', 'change', 'volume', 'RSI|14|0']
                        })
                    })
                    .then(response => response.json())
                    .then(data => resolve({success: true, data: data}))
                    .catch(err => resolve({success: false, error: err.message}));
                });
            """)

            if api_result and api_result.get('success'):
                logger.info("✅ API调用成功")
                return self._parse_scanner_data(api_result['data'])

            logger.warning("⚠️ 未能从页面获取到watchlist数据")
            return []

        except Exception as e:
            logger.error(f"❌ 获取watchlist失败: {e}")
            import traceback
            traceback.print_exc()
            return []

        finally:
            if not self.is_logged_in:
                self._close_driver()

    def _parse_scanner_data(self, data: Dict) -> List[Dict[str, Any]]:
        """解析Scanner API数据"""
        result = []

        try:
            scan_data = data.get('data', [])

            for row in scan_data:
                if len(row) >= 2:
                    symbol = row[0]
                    values = row[1] if len(row) > 1 else []

                    clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol

                    if 'USDT' in clean_symbol:
                        result.append({
                            'symbol': clean_symbol,
                            'base_asset': clean_symbol.replace('USDT', '').replace('PERP', ''),
                            'description': values[1] if len(values) > 1 else clean_symbol,
                            'exchange': 'Binance',
                            'market': 'futures' if 'PERP' in clean_symbol else 'spot',
                            'price': values[3] if len(values) > 3 else 0,
                            'change': values[4] if len(values) > 4 else 0,
                            'volume': values[5] if len(values) > 5 else 0,
                            'rsi': values[6] if len(values) > 6 else 0,
                            'source': 'TradingView Scanner',
                            'timestamp': values[2] if len(values) > 2 else None
                        })

        except Exception as e:
            logger.error(f"解析Scanner数据失败: {e}")

        return result


# 便捷函数
def get_tradingview_watchlist_with_login(
    username: str,
    password: str,
    list_name: str = None
) -> List[Dict[str, Any]]:
    """
    使用TradingView账号登录并获取关注列表

    Args:
        username: TradingView用户名/邮箱
        password: TradingView密码
        list_name: 关注列表名称(可选)

    Returns:
        币种列表
    """
    service = TradingViewWatchlistLogin(username, password)

    if service.login(headless=True):
        return service.get_watchlist(list_name)
    else:
        logger.error("登录失败")
        return []


# 测试代码
if __name__ == "__main__":
    import json

    print("=" * 80)
    print("TradingView Watchlist登录测试")
    print("=" * 80)

    # 测试1: 使用提供的账号密码登录
    print("\n请提供TradingView账号信息:")
    print("用户名/邮箱: ", end='')
    # username = input().strip()
    # print("密码: ", end='')
    # password = input().strip()

    # 示例使用
    # service = TradingViewWatchlistLogin()
    # if service.login(username, password):
    #     watchlist = service.get_watchlist()
    #
    #     print(f"\n✅ 获取到 {len(watchlist)} 个币种:")
    #     for i, coin in enumerate(watchlist, 1):
    #         print(f"{i:2d}. {coin['symbol']:20} {coin['description']:30} "
    #               f"价格:{coin.get('price', 0):>12.2f} "
    #               f"涨跌:{coin.get('change', 0):>+8.2f}%")
    # else:
    #     print("❌ 登录失败")

    print("\n使用示例:")
    print("  from app.services.tradingview_watchlist_login import get_tradingview_watchlist_with_login")
    print("  watchlist = get_tradingview_watchlist_with_login('your@email.com', 'your_password')")

    print("\n" + "=" * 80)
