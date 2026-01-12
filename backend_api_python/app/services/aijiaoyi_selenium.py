"""
爱交易(aijiaoyi.xyz) Selenium爬虫服务
支持登录后获取更多加密货币数据
"""
import time
import json
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AijiaoyiSeleniumService:
    """爱交易网站爬虫服务"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化服务

        Args:
            username: 爱交易账号(可选)
            password: 爱交易密码(可选)
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
            self.driver = webdriver.Chrome(
                options=chrome_options,
                service=Service(executable_path='/usr/bin/chromedriver')
            )

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

    def login(self, username: str = None, password: str = None, headless: bool = True) -> bool:
        """
        登录爱交易网站

        Args:
            username: 用户名(如果为None则使用初始化时的用户名)
            password: 密码(如果为None则使用初始化时的密码)
            headless: 是否使用无头模式(默认True,Docker环境需要)

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
            logger.info(f"正在访问爱交易网站...")
            self.driver.get("https://aijiaoyi.xyz/chart")

            # 等待页面加载
            time.sleep(5)

            # 查找用户名和密码输入框(登录框已经显示)
            try:
                # 查找手机号输入框
                username_input = None
                username_selectors = [
                    "//input[@placeholder='请输入手机号']",
                    "//input[@type='text' and contains(@placeholder, '手机')]",
                    "//input[@name='username' or @id='username' or @name='phone' or @id='phone']",
                ]

                for selector in username_selectors:
                    try:
                        username_input = self.driver.find_element(By.XPATH, selector)
                        if username_input:
                            logger.info(f"✅ 找到用户名输入框")
                            break
                    except:
                        continue

                if not username_input:
                    logger.error("❌ 未找到用户名输入框")
                    return False

                # 查找密码输入框
                password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
                logger.info(f"✅ 找到密码输入框")

                # 输入用户名和密码
                username_input.clear()
                username_input.send_keys(username)
                logger.info(f"✅ 已输入用户名")

                password_input.clear()
                password_input.send_keys(password)
                logger.info(f"✅ 已输入密码")

                time.sleep(1)

                # 查找并点击登录按钮
                submit_selectors = [
                    "//button[contains(text(), '登录')]",
                    "//div[@type='button' and contains(text(), '登录')]",
                    "//*[@type='submit']",
                ]

                submit_btn = None
                for selector in submit_selectors:
                    try:
                        submit_btn = self.driver.find_element(By.XPATH, selector)
                        if submit_btn and submit_btn.is_displayed():
                            break
                    except:
                        continue

                if submit_btn:
                    submit_btn.click()
                    logger.info("✅ 已点击登录按钮")
                else:
                    logger.warning("⚠️ 未找到登录按钮,尝试按Enter键")
                    password_input.send_keys(Keys.ENTER)

                # 等待登录完成
                time.sleep(10)

                # 检查是否登录成功
                if self._check_login_status():
                    logger.info("✅ 登录成功!")
                    self.is_logged_in = True
                    return True
                else:
                    logger.error("❌ 登录失败,请检查用户名和密码")
                    return False

            except Exception as e:
                logger.error(f"❌ 登录过程出错: {e}")
                import traceback
                traceback.print_exc()
                return False

        except Exception as e:
            logger.error(f"❌ 访问网站失败: {e}")
            return False

    def _check_login_status(self) -> bool:
        """检查是否已登录"""
        try:
            # 检查页面是否包含用户信息或登录后的元素
            page_source = self.driver.page_source

            # 如果还包含登录按钮,可能登录失败
            if '登录' in page_source and '注册' in page_source:
                return False

            # 如果包含用户相关元素,说明登录成功
            if '退出' in page_source or '个人中心' in page_source or 'user' in page_source.lower():
                return True

            return True  # 默认认为成功

        except:
            return False

    def get_crypto_list(self, limit: int = 50, category: str = None) -> List[Dict[str, Any]]:
        """
        获取加密货币列表

        Args:
            limit: 限制返回数量
            category: 分类 (如 'binance_perpetual', 'binance_spot' 等)

        Returns:
            加密货币列表
        """
        if not self._init_driver(headless=True):
            return []

        try:
            logger.info("正在访问爱交易网站...")
            self.driver.get("https://aijiaoyi.xyz/chart")

            # 等待页面加载
            time.sleep(5)

            # 如果已登录,等待用户信息加载
            if self.is_logged_in:
                time.sleep(3)

            # 点击加密货币按钮
            try:
                # 使用JavaScript点击,避免被遮挡
                self.driver.execute_script('document.getElementById("crypto_currency").click()')
                logger.info("✅ 已点击加密货币按钮")
                time.sleep(5)  # 等待数据加载
            except Exception as e:
                logger.warning(f"点击加密货币按钮失败: {e}")

            # 如果指定了分类,点击分类按钮
            if category:
                try:
                    category_btn = self.driver.find_element(By.ID, category)
                    self.driver.execute_script(f'document.getElementById("{category}").click()')
                    logger.info(f"✅ 已点击分类: {category}")
                    time.sleep(8)  # 等待更长时间让数据加载
                except:
                    logger.warning(f"点击分类 {category} 失败")

            # 多次滚动以触发懒加载
            try:
                for i in range(15):  # 增加到15次滚动
                    self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    time.sleep(0.8)
                logger.info("✅ 已完成页面滚动")
                # 滚动回顶部
                self.driver.execute_script('window.scrollTo(0, 0);')
                time.sleep(2)
            except Exception as e:
                logger.warning(f"页面滚动失败: {e}")

            # 等待异步数据加载
            logger.info("等待异步数据加载...")
            time.sleep(10)

            # 查找币种列表 - 尝试多种方法
            crypto_data = []

            # 方法1: 使用原来的选择器
            try:
                symbol_list = self.driver.find_element(By.ID, 'symbol_list')
                symbols = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
                logger.info(f"方法1找到 {len(symbols)} 个币种")

                for symbol_elem in symbols[:limit]:
                    try:
                        symbol_id = symbol_elem.get_attribute('id')
                        text = symbol_elem.text

                        # 提取数据
                        parts = text.split('\n')
                        if len(parts) >= 3:
                            name = parts[0] if parts[0] else symbol_id
                            price = parts[1] if len(parts) > 1 else '0'
                            change = parts[2] if len(parts) > 2 else '0%'

                            # 清理symbol
                            clean_symbol = symbol_id.replace('BINANCE:', '') if 'BINANCE:' in symbol_id else symbol_id

                            crypto_data.append({
                                'symbol': clean_symbol,
                                'full_symbol': symbol_id,
                                'name': name,
                                'price': float(price.replace(',', '')) if price != 'N/A' else 0,
                                'change_percent': change,
                                'source': 'aijiaoyi'
                            })
                    except:
                        continue

            except Exception as e:
                logger.warning(f"方法1失败: {e}")

            # 方法2: 查找所有li元素
            if len(crypto_data) < 10:
                try:
                    symbol_list = self.driver.find_element(By.ID, 'symbol_list')
                    all_items = symbol_list.find_elements(By.TAG_NAME, 'li')
                    logger.info(f"方法2找到 {len(all_items)} 个li元素")

                    for item in all_items[:limit]:
                        try:
                            text = item.text
                            if text and '\n' in text:
                                parts = text.split('\n')
                                if len(parts) >= 3:
                                    crypto_data.append({
                                        'symbol': parts[0],
                                        'name': parts[0],
                                        'price': float(parts[1].replace(',', '')) if parts[1] != 'N/A' else 0,
                                        'change_percent': parts[2],
                                        'source': 'aijiaoyi'
                                    })
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"方法2失败: {e}")

            # 方法3: 尝试从JavaScript变量获取数据
            if len(crypto_data) < 10:
                try:
                    # 尝试获取页面中的数据
                    js_data = self.driver.execute_script("""
                        // 查找可能包含币种数据的变量
                        if (typeof window.symbolData !== 'undefined') {
                            return window.symbolData;
                        }
                        if (typeof window.symbols !== 'undefined') {
                            return window.symbols;
                        }
                        if (typeof window.cryptoList !== 'undefined') {
                            return window.cryptoList;
                        }
                        // 尝试从React/Vue实例获取
                        if (typeof window.__INITIAL_STATE__ !== 'undefined') {
                            return window.__INITIAL_STATE__;
                        }
                        return null;
                    """)
                    if js_data:
                        logger.info(f"方法3从JavaScript获取到数据: {type(js_data)}")
                except Exception as e:
                    logger.warning(f"方法3失败: {e}")

            # 方法4: 获取页面HTML并解析
            if len(crypto_data) < 10:
                try:
                    page_source = self.driver.page_source
                    # 保存完整HTML用于调试
                    with open('/tmp/aijiaoyi_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    logger.info("✅ 已保存页面源码到 /tmp/aijiaoyi_page_source.html")

                    # 统计币种数量
                    import re
                    # 查找所有可能的币种符号格式
                    patterns = [
                        r'BINANCE:[A-Z]+USDT',
                        r'[A-Z]+USDT',
                        r'BINANCE:[A-Z]+USDTPERP',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, page_source)
                        if matches:
                            logger.info(f"模式 {pattern} 匹配到 {len(set(matches))} 个唯一币种")
                except Exception as e:
                    logger.warning(f"方法4失败: {e}")

            logger.info(f"✅ 最终获取到 {len(crypto_data)} 个加密货币数据")

            # 按涨跌幅排序(如果有涨跌幅数据)
            if crypto_data:
                crypto_data.sort(
                    key=lambda x: float(x['change_percent'].replace('%', '')) if isinstance(x['change_percent'], str) and x['change_percent'] != 'N/A' else 0,
                    reverse=True
                )

            return crypto_data[:limit]

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []

        finally:
            if not self.is_logged_in:  # 如果不是登录状态,关闭driver
                self._close_driver()

    def get_top_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取涨幅榜

        Args:
            limit: 返回数量

        Returns:
            按涨幅排序的币种列表
        """
        all_coins = self.get_crypto_list(limit=100)  # 获取更多币种

        if not all_coins:
            return []

        # 过滤并排序
        gainers = []
        for coin in all_coins:
            try:
                change_str = coin.get('change_percent', '0%')
                if isinstance(change_str, str):
                    change = float(change_str.replace('%', ''))
                    coin['change_value'] = change

                    # 只保留涨幅为正的币种
                    if change > 0:
                        gainers.append(coin)
            except:
                continue

        # 按涨幅降序排序
        gainers.sort(key=lambda x: x.get('change_value', 0), reverse=True)

        return gainers[:limit]


# 便捷函数
def get_aijiaoyi_crypto_list(
    username: Optional[str] = None,
    password: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    获取爱交易加密货币列表

    Args:
        username: 爱交易账号(可选,不登录可能获取的数据有限)
        password: 爱交易密码(可选)
        limit: 限制返回数量

    Returns:
        加密货币列表
    """
    service = AijiaoyiSeleniumService(username, password)

    # 如果提供了账号密码,先登录
    if username and password:
        if not service.login(username, password):
            logger.warning("⚠️ 登录失败,将尝试获取公开数据")

    return service.get_crypto_list(limit)


def get_aijiaoyi_top_gainers(
    username: Optional[str] = None,
    password: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    获取爱交易涨幅榜

    Args:
        username: 爱交易账号(可选)
        password: 爱交易密码(可选)
        limit: 返回数量

    Returns:
        涨幅榜列表
    """
    service = AijiaoyiSeleniumService(username, password)

    # 如果提供了账号密码,先登录
    if username and password:
        if not service.login(username, password):
            logger.warning("⚠️ 登录失败,将尝试获取公开数据")

    return service.get_top_gainers(limit)


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("爱交易爬虫测试")
    print("=" * 80)

    # 测试1: 不登录获取数据
    print("\n测试1: 不登录获取加密货币列表")
    print("-" * 80)

    service = AijiaoyiSeleniumService()
    coins = service.get_crypto_list(limit=20)

    if coins:
        print(f"\n获取到 {len(coins)} 个币种:\n")
        for i, coin in enumerate(coins[:10], 1):
            print(f"{i:2d}. {coin['symbol']:15} {coin['name']:15} "
                  f"价格:{coin['price']:12.2f} 涨跌:{coin['change_percent']}")

    # 测试2: 登录后获取数据
    print("\n\n测试2: 登录后获取数据")
    print("-" * 80)
    print("如需测试登录功能,请提供用户名和密码:")
    print("  service = AijiaoyiSeleniumService()")
    print("  service.login('your_username', 'your_password')")
    print("  coins = service.get_crypto_list()")

    print("\n" + "=" * 80)
