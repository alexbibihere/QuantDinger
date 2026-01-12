"""
使用Selenium从AICoin爬取Binance涨幅榜数据
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AICoinSeleniumService:
    """使用Selenium爬取AICoin数据"""

    def __init__(self):
        self.driver = None
        self.headless = True  # 无头模式

    def _init_driver(self):
        """初始化Chrome浏览器"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')

            # 设置User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 禁用图片加载以加快速度
            prefs = {
                'profile.managed_default_content_settings.images': 2
            }
            chrome_options.add_experimental_option('prefs', prefs)

            # 配置代理
            import os
            proxy_port = os.getenv('PROXY_PORT')
            if proxy_port:
                chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{proxy_port}')
                logger.info(f"使用代理: 127.0.0.1:{proxy_port}")

            # 初始化驱动
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)

            logger.info("Selenium Chrome驱动初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化Selenium驱动失败: {e}")
            return False

    def get_binance_futures_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        从AICoin获取Binance永续合约涨幅榜

        Args:
            limit: 返回数量

        Returns:
            涨幅榜数据列表
        """
        if not self._init_driver():
            return []

        try:
            logger.info("开始从AICoin爬取Binance涨幅榜")

            # 访问AICoin Binance涨幅榜页面
            url = "https://www.aicoin.com/rank/binance/futures"
            self.driver.get(url)

            # 等待页面加载
            time.sleep(5)

            # 查找数据表格或列表
            gainers = self._parse_page_data(limit)

            logger.info(f"✅ 成功从AICoin爬取{len(gainers)}个币种")
            return gainers

        except Exception as e:
            logger.error(f"从AICoin爬取数据失败: {e}")
            return []

        finally:
            self._close_driver()

    def _parse_page_data(self, limit: int) -> List[Dict[str, Any]]:
        """解析页面数据"""
        gainers = []

        try:
            # 方法1: 查找表格元素
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"找到{len(tables)}个表格")

            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                logger.info(f"表格有{len(rows)}行")

                for row in rows[1:limit+1]:  # 跳过表头
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 4:
                            # 提取数据 (需要根据实际页面结构调整)
                            symbol = cells[0].text.strip()
                            price = self._extract_number(cells[1].text)
                            change_percent = self._extract_number(cells[2].text)

                            if symbol and price:
                                gainers.append({
                                    'symbol': symbol,
                                    'base_asset': symbol.replace('USDT', ''),
                                    'price': price,
                                    'price_change_percent': change_percent,
                                    'volume': 0,  # 页面可能不显示
                                    'quote_volume': 0,
                                    'exchange': 'Binance (via AICoin)',
                                    'market': 'futures',
                                    'timestamp': datetime.now().isoformat()
                                })

                        if len(gainers) >= limit:
                            break

                    except Exception as e:
                        logger.debug(f"解析行失败: {e}")
                        continue

                if gainers:
                    break

            # 方法2: 如果表格方法失败,尝试查找JSON数据
            if not gainers:
                gainers = self._extract_json_data(limit)

        except Exception as e:
            logger.error(f"解析页面数据失败: {e}")

        return gainers

    def _extract_json_data(self, limit: int) -> List[Dict[str, Any]]:
        """从页面中提取JSON数据"""
        try:
            # 获取页面源码
            page_source = self.driver.page_source

            # 查找JSON数据
            # 常见的JSON数据位置
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'__NEXT_DATA__\s*=\s*({.+?})\s*</script>',
                r'data-tickers="([^"]+)"',
            ]

            import re
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    try:
                        # 尝试解析JSON
                        data = json.loads(matches[0])

                        # 根据数据结构解析
                        gainers = self._parse_json_data(data, limit)
                        if gainers:
                            return gainers
                    except:
                        continue

        except Exception as e:
            logger.debug(f"提取JSON数据失败: {e}")

        return []

    def _parse_json_data(self, data: Any, limit: int) -> List[Dict[str, Any]]:
        """解析JSON数据"""
        gainers = []

        try:
            # 这里需要根据AICoin实际返回的JSON结构来解析
            # 示例代码,需要根据实际情况调整

            if isinstance(data, dict):
                # 查找可能的ticker数据字段
                for key in ['tickers', 'data', 'symbols', 'list']:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            for item in items[:limit]:
                                if isinstance(item, dict):
                                    symbol = item.get('symbol') or item.get('code')
                                    if symbol and 'USDT' in str(symbol):
                                        gainers.append({
                                            'symbol': symbol,
                                            'base_asset': str(symbol).replace('USDT', ''),
                                            'price': float(item.get('price', item.get('last', 0))),
                                            'price_change_percent': float(item.get('change', item.get('change_percent', 0))),
                                            'volume': float(item.get('volume', 0)),
                                            'quote_volume': float(item.get('quote_volume', 0)),
                                            'exchange': 'Binance (via AICoin)',
                                            'market': 'futures',
                                            'timestamp': datetime.now().isoformat()
                                        })
                                    if len(gainers) >= limit:
                                        break

        except Exception as e:
            logger.error(f"解析JSON数据失败: {e}")

        return gainers

    def _extract_number(self, text: str) -> float:
        """从文本中提取数字"""
        try:
            # 移除所有非数字字符(保留小数点和负号)
            import re
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0

    def _close_driver(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium浏览器已关闭")
            except:
                pass


# 便捷函数
def get_binance_futures_gainers_selenium(limit: int = 20) -> List[Dict[str, Any]]:
    """使用Selenium从AICoin获取Binance永续合约涨幅榜"""
    service = AICoinSeleniumService()
    return service.get_binance_futures_gainers(limit)
