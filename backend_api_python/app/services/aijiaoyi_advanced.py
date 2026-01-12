"""
爱交易高级爬虫 - 使用网络监控捕获所有数据
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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AijiaoyiAdvancedScraper:
    """爱交易高级爬虫 - 监控网络请求"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        self.driver = None
        self.is_logged_in = False
        self.network_logs = []

    def _init_driver(self, headless: bool = True) -> bool:
        """初始化Chrome WebDriver并启用性能日志"""
        try:
            chrome_options = ChromeOptions()

            if headless:
                chrome_options.add_argument('--headless')

            # 基本配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # 启用网络日志
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

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

            logger.info("✅ Chrome WebDriver初始化成功(已启用网络监控)")
            return True

        except Exception as e:
            logger.error(f"❌ Chrome WebDriver初始化失败: {e}")
            return False

    def _get_network_logs(self) -> List[Dict]:
        """获取网络请求日志"""
        try:
            logs = self.driver.get_log('performance')
            network_requests = []

            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']

                    if log['method'] == 'Network.responseReceived':
                        response = log['params']['response']
                        if 'json' in response.get('mimeType', '') or 'xhr' in response.get('mimeType', ''):
                            request_id = log['params']['requestId']
                            network_requests.append({
                                'url': response['url'],
                                'status': response['status'],
                                'type': response.get('mimeType', ''),
                                'requestId': request_id
                            })

                    elif log['method'] == 'Network.requestWillBeSent':
                        request = log['params']['request']
                        if 'api' in request['url'].lower() or 'data' in request['url'].lower():
                            network_requests.append({
                                'url': request['url'],
                                'method': request['method'],
                                'type': 'request'
                            })
                except:
                    continue

            return network_requests

        except Exception as e:
            logger.warning(f"获取网络日志失败: {e}")
            return []

    def login(self, username: str = None, password: str = None, headless: bool = True) -> bool:
        """登录爱交易网站"""
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

            # 查找用户名和密码输入框
            try:
                username_input = None
                username_selectors = [
                    "//input[@placeholder='请输入手机号']",
                    "//input[@type='text' and contains(@placeholder, '手机')]",
                ]

                for selector in username_selectors:
                    try:
                        username_input = self.driver.find_element(By.XPATH, selector)
                        if username_input:
                            break
                    except:
                        continue

                if not username_input:
                    logger.error("❌ 未找到用户名输入框")
                    return False

                password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")

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
                    password_input.send_keys(Keys.ENTER)

                # 等待登录完成
                time.sleep(10)

                if self._check_login_status():
                    logger.info("✅ 登录成功!")
                    self.is_logged_in = True
                    return True
                else:
                    logger.error("❌ 登录失败")
                    return False

            except Exception as e:
                logger.error(f"❌ 登录过程出错: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ 访问网站失败: {e}")
            return False

    def _check_login_status(self) -> bool:
        """检查是否已登录"""
        try:
            page_source = self.driver.page_source
            if '登录' in page_source and '注册' in page_source:
                return False
            if '退出' in page_source or '个人中心' in page_source:
                return True
            return True
        except:
            return False

    def get_crypto_list_with_network_monitoring(
        self,
        limit: int = 100,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取加密货币列表 - 使用网络监控

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

            # 点击加密货币按钮
            try:
                self.driver.execute_script('document.getElementById("crypto_currency").click()')
                logger.info("✅ 已点击加密货币按钮")
                time.sleep(5)
            except Exception as e:
                logger.warning(f"点击加密货币按钮失败: {e}")

            # 如果指定了分类,点击分类按钮
            if category:
                try:
                    self.driver.execute_script(f'document.getElementById("{category}").click()')
                    logger.info(f"✅ 已点击分类: {category}")
                    time.sleep(8)
                except:
                    logger.warning(f"点击分类 {category} 失败")

            # 收集初始网络日志
            initial_logs = self._get_network_logs()
            logger.info(f"初始网络请求: {len(initial_logs)} 个")

            # 多次滚动以触发懒加载
            logger.info("开始滚动页面...")
            all_network_logs = []

            for i in range(20):
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)

                # 收集网络日志
                logs = self._get_network_logs()
                if logs:
                    all_network_logs.extend(logs)
                    logger.info(f"滚动第{i+1}次, 新增网络请求: {len(logs)} 个")

            logger.info(f"总共捕获 {len(all_network_logs)} 个网络请求")

            # 滚动回顶部
            self.driver.execute_script('window.scrollTo(0, 0);')
            time.sleep(2)

            # 等待最终数据加载
            time.sleep(5)

            # 保存网络日志
            with open('/tmp/aijiaoyi_network_logs.json', 'w', encoding='utf-8') as f:
                json.dump(all_network_logs, f, ensure_ascii=False, indent=2)
            logger.info("✅ 已保存网络日志到 /tmp/aijiaoyi_network_logs.json")

            # 尝试从DOM获取数据
            crypto_data = []
            try:
                symbol_list = self.driver.find_element(By.ID, 'symbol_list')
                symbols = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
                logger.info(f"从DOM找到 {len(symbols)} 个币种")

                for symbol_elem in symbols[:limit]:
                    try:
                        symbol_id = symbol_elem.get_attribute('id')
                        text = symbol_elem.text

                        parts = text.split('\n')
                        if len(parts) >= 3:
                            name = parts[0] if parts[0] else symbol_id
                            price = parts[1] if len(parts) > 1 else '0'
                            change = parts[2] if len(parts) > 2 else '0%'

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
                logger.warning(f"从DOM获取数据失败: {e}")

            # 分析网络日志,查找API端点
            api_endpoints = set()
            for log in all_network_logs:
                url = log.get('url', '')
                if 'api' in url.lower() or 'symbol' in url.lower() or 'data' in url.lower():
                    api_endpoints.add(url)

            if api_endpoints:
                logger.info(f"发现 {len(api_endpoints)} 个可能的API端点:")
                for endpoint in list(api_endpoints)[:10]:  # 只显示前10个
                    logger.info(f"  - {endpoint}")

                # 保存API端点列表
                with open('/tmp/aijiaoyi_api_endpoints.txt', 'w', encoding='utf-8') as f:
                    for endpoint in api_endpoints:
                        f.write(f"{endpoint}\n")
                logger.info("✅ 已保存API端点到 /tmp/aijiaoyi_api_endpoints.txt")

            logger.info(f"✅ 最终获取到 {len(crypto_data)} 个加密货币数据")

            # 按涨跌幅排序
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
            if not self.is_logged_in:
                self._close_driver()

    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ WebDriver已关闭")
            except Exception as e:
                logger.warning(f"关闭WebDriver失败: {e}")


# 便捷函数
def get_aijiaoyi_with_monitoring(
    username: Optional[str] = None,
    password: Optional[str] = None,
    limit: int = 100,
    category: str = None
) -> List[Dict[str, Any]]:
    """
    使用网络监控获取爱交易数据

    Args:
        username: 爱交易账号(可选)
        password: 爱交易密码(可选)
        limit: 限制返回数量
        category: 分类

    Returns:
        加密货币列表
    """
    scraper = AijiaoyiAdvancedScraper(username, password)

    # 如果提供了账号密码,先登录
    if username and password:
        if not scraper.login(username, password):
            logger.warning("⚠️ 登录失败,将尝试获取公开数据")

    return scraper.get_crypto_list_with_network_monitoring(limit=limit, category=category)


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("爱交易高级爬虫测试 - 网络监控模式")
    print("=" * 80)

    # 测试: 使用网络监控获取数据
    print("\n测试: 使用网络监控获取币安永续数据")
    print("-" * 80)

    scraper = AijiaoyiAdvancedScraper()
    coins = scraper.get_crypto_list_with_network_monitoring(
        limit=100,
        category='binance_perpetual'
    )

    if coins:
        print(f"\n获取到 {len(coins)} 个币种:\n")
        for i, coin in enumerate(coins[:20], 1):  # 只显示前20个
            print(f"{i:2d}. {coin['symbol']:20} {coin['name']:20} "
                  f"价格:{coin['price']:12.2f} 涨跌:{coin['change_percent']}")

    print("\n" + "=" * 80)
    print("检查以下文件获取更多信息:")
    print("  - /tmp/aijiaoyi_network_logs.json (网络请求日志)")
    print("  - /tmp/aijiaoyi_api_endpoints.txt (发现的API端点)")
    print("=" * 80)
