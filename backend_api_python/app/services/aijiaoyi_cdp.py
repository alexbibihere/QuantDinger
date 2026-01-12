"""
爱交易高级爬虫 - 使用CDP捕获网络请求
"""
import time
import json
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AijiaoyiCDPScraper:
    """使用CDP监控网络请求"""

    def __init__(self):
        self.driver = None
        self.network_data = []

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

    def _extract_symbols_from_page(self) -> List[Dict[str, Any]]:
        """从页面提取币种数据"""
        symbols = []

        try:
            # 方法1: 从 symbol_list 提取
            symbol_list = self.driver.find_element(By.ID, 'symbol_list')
            elements = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')

            for elem in elements:
                try:
                    symbol_id = elem.get_attribute('id')
                    text = elem.text

                    if not text or '\n' not in text:
                        continue

                    parts = text.split('\n')
                    if len(parts) >= 3:
                        name = parts[0] if parts[0] else symbol_id
                        price_str = parts[1].replace(',', '').replace('N/A', '0')
                        change = parts[2]

                        try:
                            price = float(price_str)
                        except:
                            price = 0

                        clean_symbol = symbol_id.replace('BINANCE:', '') if 'BINANCE:' in symbol_id else symbol_id

                        symbols.append({
                            'symbol': clean_symbol,
                            'full_symbol': symbol_id,
                            'name': name,
                            'price': price,
                            'change_percent': change,
                            'source': 'aijiaoyi'
                        })
                except:
                    continue

        except Exception as e:
            logger.warning(f"从页面提取币种失败: {e}")

        return symbols

    def _check_all_containers(self) -> List[Dict[str, Any]]:
        """检查页面所有可能的容器"""
        all_symbols = []

        try:
            # 获取页面HTML
            page_source = self.driver.page_source

            # 保存到文件
            with open('/tmp/aijiaoyi_cdp_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)

            # 查找所有div元素
            from selenium.webdriver.common.by import By
            divs = self.driver.find_elements(By.TAG_NAME, 'div')

            logger.info(f"页面共有 {len(divs)} 个div元素")

            # 查找可能包含币种数据的div
            for div in divs:
                try:
                    div_id = div.get_attribute('id')
                    if div_id and ('symbol' in div_id.lower() or 'list' in div_id.lower() or 'coin' in div_id.lower()):
                        text = div.text
                        if text and '\n' in text:
                            lines = text.split('\n')
                            # 检查是否像币种数据
                            for i in range(len(lines) - 2):
                                if 'USDT' in lines[i] or 'PERP' in lines[i]:
                                    logger.info(f"在容器 {div_id} 中发现可能的数据: {lines[i]}")
                except:
                    continue

        except Exception as e:
            logger.warning(f"检查容器失败: {e}")

        return all_symbols

    def get_crypto_list(
        self,
        limit: int = 100,
        category: str = None,
        scroll_times: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取加密货币列表

        Args:
            limit: 限制返回数量
            category: 分类
            scroll_times: 滚动次数

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

            # 如果指定了分类
            if category:
                try:
                    self.driver.execute_script(f'document.getElementById("{category}").click()')
                    logger.info(f"✅ 已点击分类: {category}")
                    time.sleep(8)
                except:
                    logger.warning(f"点击分类 {category} 失败")

            # 记录初始数量
            initial_symbols = self._extract_symbols_from_page()
            logger.info(f"初始币种数量: {len(initial_symbols)}")

            # 滚动并监控变化
            logger.info(f"开始滚动页面 (共{scroll_times}次)...")
            max_symbols = 0
            best_symbols = []

            for i in range(scroll_times):
                # 滚动到底部
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(0.5)

                # 每5次滚动检查一次数量
                if i % 5 == 0:
                    current_symbols = self._extract_symbols_from_page()
                    current_count = len(current_symbols)

                    if current_count > max_symbols:
                        max_symbols = current_count
                        best_symbols = current_symbols
                        logger.info(f"滚动第{i}次: 发现 {current_count} 个币种 ⬆️")
                    elif current_count < max_symbols:
                        logger.info(f"滚动第{i}次: 当前 {current_count} 个币种 (最高{max_symbols})")
                    else:
                        logger.info(f"滚动第{i}次: {current_count} 个币种")

            # 滚动回顶部
            self.driver.execute_script('window.scrollTo(0, 0);')
            time.sleep(2)

            # 最后检查一次
            final_symbols = self._extract_symbols_from_page()
            if len(final_symbols) > len(best_symbols):
                best_symbols = final_symbols
                logger.info(f"✅ 最终获取: {len(best_symbols)} 个币种")
            else:
                logger.info(f"✅ 最佳结果: {len(best_symbols)} 个币种")

            # 检查其他容器
            self._check_all_containers()

            # 排序
            if best_symbols:
                best_symbols.sort(
                    key=lambda x: float(x['change_percent'].replace('%', '')) if isinstance(x['change_percent'], str) and x['change_percent'] != 'N/A' else 0,
                    reverse=True
                )

            return best_symbols[:limit]

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []

        finally:
            self._close_driver()

    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ WebDriver已关闭")
            except Exception as e:
                logger.warning(f"关闭WebDriver失败: {e}")


# 测试函数
def test_cdp_scraper():
    """测试CDP爬虫"""
    print("=" * 80)
    print("爱交易CDP爬虫测试")
    print("=" * 80)

    scraper = AijiaoyiCDPScraper()

    print("\n测试1: 获取默认分类数据")
    print("-" * 80)
    coins = scraper.get_crypto_list(limit=100, scroll_times=30)

    if coins:
        print(f"\n✅ 获取到 {len(coins)} 个币种:\n")
        for i, coin in enumerate(coins[:30], 1):
            print(f"{i:2d}. {coin['symbol']:20} {coin['name']:20} "
                  f"价格:{coin['price']:12.2f} 涨跌:{coin['change_percent']}")

    print("\n测试2: 获取币安永续数据")
    print("-" * 80)
    coins = scraper.get_crypto_list(limit=100, category='binance_perpetual', scroll_times=30)

    if coins:
        print(f"\n✅ 获取到 {len(coins)} 个币种:\n")
        for i, coin in enumerate(coins[:30], 1):
            print(f"{i:2d}. {coin['symbol']:20} {coin['name']:20} "
                  f"价格:{coin['price']:12.2f} 涨跌:{coin['change_percent']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_cdp_scraper()
