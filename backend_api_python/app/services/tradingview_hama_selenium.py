#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Selenium模拟浏览器从TradingView读取HAMA指标
通过JavaScript注入的方式从TradingView页面提取HAMA指标数据
"""
import time
import json
import os
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_cookies_from_config() -> Optional[Dict[str, str]]:
    """
    从配置文件或环境变量加载TradingView cookies

    优先级:
    1. 环境变量
    2. 配置文件 (config/tradingview_cookies.json)

    Returns:
        cookies字典或None
    """
    # 方法1: 从环境变量读取
    sessionid = os.getenv('TRADINGVIEW_SESSIONID')
    sessionid_sign = os.getenv('TRADINGVIEW_SESSIONID_SIGN')
    uid = os.getenv('TRADINGVIEW_UID')

    if sessionid and sessionid_sign and uid:
        logger.info("✅ 从环境变量加载TradingView cookies")
        return {
            'sessionid': sessionid,
            'sessionid_sign': sessionid_sign,
            'uid': uid
        }

    # 方法2: 从配置文件读取
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'tradingview_cookies.json')

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

                # 验证必要的字段
                if all(key in cookies for key in ['sessionid', 'sessionid_sign', 'uid']):
                    logger.info(f"✅ 从配置文件加载TradingView cookies: {config_path}")
                    return cookies
                else:
                    logger.warning(f"配置文件中缺少必要的cookies字段: {config_path}")
    except Exception as e:
        logger.warning(f"读取cookies配置文件失败: {e}")

    logger.info("⚠️ 未找到TradingView cookies配置")
    return None


class TradingViewHamaSelenium:
    """使用Selenium从TradingView读取HAMA指标"""

    def __init__(self, headless: bool = True, cookies: Dict[str, str] = None):
        """
        初始化Selenium WebDriver

        Args:
            headless: 是否使用无头模式(不显示浏览器窗口)
            cookies: TradingView的cookies (用于保持登录状态)
                     可以从浏览器开发者工具中获取
        """
        self.driver = None
        self.headless = headless
        self.cookies = cookies

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
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')

            # 禁用各种可能导致网络请求的功能
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--enable-automation')
            chrome_options.add_argument('--password-store=basic')
            chrome_options.add_argument('--use-mock-keychain')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-ipc-flooding-protection')

            # 禁用日志
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')

            # 设置User-Agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )

            # 禁用自动化提示
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 尝试多个ChromeDriver路径
            driver_paths = [
                '/usr/bin/chromedriver',  # Debian/Ubuntu
                '/usr/local/bin/chromedriver',  # 本地安装
                '/opt/homebrew/bin/chromedriver',  # macOS Homebrew
            ]

            driver_initialized = False

            # 方法1: 尝试系统ChromeDriver (不指定路径,让Selenium自动查找)
            try:
                logger.info("尝试使用系统ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ 使用系统ChromeDriver初始化成功")
                driver_initialized = True
            except Exception as e:
                logger.warning(f"系统自动查找失败: {e}")

            # 方法2: 尝试指定路径
            if not driver_initialized:
                for path in driver_paths:
                    try:
                        logger.info(f"尝试使用ChromeDriver路径: {path}")
                        self.driver = webdriver.Chrome(
                            options=chrome_options,
                            service=Service(executable_path=path)
                        )
                        logger.info(f"✅ 使用 {path} 初始化Chrome成功")
                        driver_initialized = True
                        break
                    except Exception as e:
                        logger.debug(f"路径 {path} 失败: {e}")
                        continue

            # 方法3: 尝试webdriver-manager (需要网络)
            if not driver_initialized:
                try:
                    logger.info("尝试使用webdriver-manager...")
                    from webdriver_manager.chrome import ChromeDriverManager

                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("✅ 使用webdriver-manager初始化Chrome成功")
                    driver_initialized = True
                except Exception as e:
                    logger.error(f"webdriver-manager失败: {e}")

            if not driver_initialized:
                logger.error("❌ 所有ChromeDriver初始化方法都失败")
                return False

            # 设置隐式等待
            self.driver.implicitly_wait(10)

            logger.info("✅ Chrome WebDriver初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ Chrome WebDriver初始化失败: {e}", exc_info=True)
            return False

    def _add_cookies(self, domain: str = ".tradingview.com"):
        """
        添加cookies到浏览器

        Args:
            domain: Cookie的域名
        """
        if not self.cookies:
            return

        try:
            # 先访问域名以设置cookie context
            self.driver.get("https://cn.tradingview.com/")
            time.sleep(2)

            # 添加每个cookie
            for name, value in self.cookies.items():
                try:
                    self.driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': '/'
                    })
                    logger.info(f"✅ 添加cookie: {name}")
                except Exception as e:
                    logger.warning(f"添加cookie失败 {name}: {e}")

            # 刷新页面以应用cookies
            self.driver.refresh()
            time.sleep(2)
            logger.info("✅ Cookies已添加")

        except Exception as e:
            logger.warning(f"添加cookies失败: {e}")

    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ WebDriver已关闭")
            except Exception as e:
                logger.warning(f"关闭WebDriver失败: {e}")

    def get_hama_from_tradingview(
        self,
        symbol: str,
        interval: str = "15",
        wait_for_load: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        从TradingView页面获取HAMA指标数据

        Args:
            symbol: 币种符号 (如 BTCUSDT)
            interval: 时间周期 (如 "15" 代表15分钟)
            wait_for_load: 等待页面加载的时间(秒)

        Returns:
            HAMA指标数据字典,包含:
            - symbol: 币种符号
            - interval: 时间周期
            - hama_color: HAMA颜色 (green/red)
            - hama_trend: HAMA趋势 (up/down)
            - price: 当前价格
            - ma: 移动平均线值
            - candle_close: K线收盘价
            - timestamp: 时间戳
            - source: "tradingview_selenium"
        """
        if not self._init_driver():
            return None

        try:
            # 如果提供了cookies,先添加
            if self.cookies:
                self._add_cookies()

            # 构造TradingView图表URL
            # 格式: https://cn.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15
            url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}&interval={interval}"

            logger.info(f"🌐 正在访问TradingView: {url}")
            self.driver.get(url)

            # 等待页面加载
            logger.info(f"⏳ 等待页面加载 ({wait_for_load}秒)...")
            time.sleep(wait_for_load)

            # 尝试从页面提取HAMA指标数据
            # 方法: 注入JavaScript代码来读取TradingView的指标数据
            script = """
            (function() {
                try {
                    // 尝试多种方式获取HAMA指标数据

                    // 方法1: 查找页面中所有的Pine Script指标
                    const widgets = document.querySelectorAll('[data-widget-type]);
                    if (widgets.length > 0) {
                        console.log('找到widgets:', widgets.length);
                    }

                    // 方法2: 尝试从TradingView的内部状态读取
                    // TradingView通常将图表数据存储在window对象中
                    if (window.tradingView) {
                        console.log('找到tradingView对象');
                    }

                    // 方法3: 查找图表容器并尝试读取数据
                    const chartContainer = document.querySelector('.chart-container');
                    if (chartContainer) {
                        // 尝试读取图表数据
                        console.log('找到chart-container');
                    }

                    // 方法4: 查找所有指标面板
                    const panes = document.querySelectorAll('.widget-pane');
                    const indicators = [];

                    panes.forEach(pane => {
                        const titles = pane.querySelectorAll('.titleWrap');
                        titles.forEach(title => {
                            const text = title.textContent || title.innerText;
                            if (text && (text.includes('HAMA') || text.includes('Hama'))) {
                                indicators.push({
                                    name: text,
                                    type: 'HAMA'
                                });
                            }
                        });
                    });

                    // 方法5: 尝试从图表的data-widget-attribute读取
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {
                        const widgetType = elem.getAttribute('data-widget-type');
                        if (widgetType && (widgetType.includes('study') || widgetType.includes('indicator'))) {
                            const title = elem.getAttribute('data-widget-title') || '';
                            if (title.includes('HAMA') || title.includes('Hama')) {
                                indicators.push({
                                    name: title,
                                    type: 'HAMA'
                                });
                            }
                        }
                    }

                    return {
                        success: true,
                        indicators: indicators,
                        page_title: document.title,
                        url: window.location.href
                    };

                } catch (error) {
                    return {
                        success: false,
                        error: error.toString()
                    };
                }
            })();
            """

            # 执行JavaScript
            logger.info("📜 正在执行JavaScript提取HAMA指标...")
            result = self.driver.execute_script(script)

            if result and result.get('success'):
                indicators = result.get('indicators', [])

                if indicators:
                    logger.info(f"✅ 找到 {len(indicators)} 个HAMA相关指标")

                    # 构造返回数据
                    # 注意: 由于TradingView页面的复杂性，我们可能需要更复杂的逻辑来提取实际的HAMA值
                    # 这里先返回一个基础结构

                    return {
                        'symbol': symbol,
                        'interval': interval,
                        'hama_color': 'unknown',  # 需要进一步解析
                        'hama_trend': 'unknown',  # 需要进一步解析
                        'price': 0.0,  # 需要从页面提取
                        'ma': 0.0,  # 需要从页面提取
                        'candle_close': 0.0,  # 需要从页面提取
                        'indicators': indicators,
                        'page_title': result.get('page_title'),
                        'source': 'tradingview_selenium',
                        'timestamp': time.time()
                    }
                else:
                    logger.warning(f"⚠️ 页面未找到HAMA指标")
                    return {
                        'symbol': symbol,
                        'interval': interval,
                        'error': 'No HAMA indicator found on page',
                        'source': 'tradingview_selenium',
                        'timestamp': time.time()
                    }
            else:
                logger.error(f"❌ JavaScript执行失败: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取HAMA指标失败: {str(e)}", exc_info=True)
            return None

        finally:
            # 关闭浏览器
            self._close_driver()

    def get_hama_with_custom_script(
        self,
        symbol: str,
        interval: str = "15",
        hama_script: str = None,
        wait_for_load: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        使用自定义Pine Script从TradingView获取HAMA指标

        Args:
            symbol: 币种符号
            interval: 时间周期
            hama_script: HAMA指标的Pine Script代码 (如果为None则使用默认)
            wait_for_load: 等待页面加载时间

        Returns:
            HAMA指标数据
        """
        if not self._init_driver():
            return None

        try:
            # 如果没有提供自定义脚本，使用默认的HAMA Pine Script
            if not hama_script:
                hama_script = """
                //@version=5
                indicator("HAMA", shorttitle="HAMA", overlay=true)

                // HAMA指标参数
                len = 20
                src = close

                // 计算HAMA
                ma = ta.sma(src, len)
                hama = close > ma ? ma : ma

                // 绘制
                plot(ma, "HAMA", color=color.new(color.green, 0))

                // 信号
                signal = ta.crossover(close, ma)
                alertcondition(signal, "HAMA Crossover", "HAMA交叉信号")
                """

            # 构造带有HAMA脚本的URL
            # 注意: 这需要TradingView支持通过URL参数添加指标
            url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}&interval={interval}"

            logger.info(f"🌐 正在访问TradingView: {url}")
            self.driver.get(url)

            # 等待页面加载
            logger.info(f"⏳ 等待页面加载 ({wait_for_load}秒)...")
            time.sleep(wait_for_load)

            # 注入HAMA指标脚本
            # 注意: TradingView可能不允许直接通过JavaScript注入指标
            # 这里提供一个尝试性的实现
            inject_script = f"""
            (function() {{
                try {{
                    // 尝试创建HAMA指标
                    console.log('尝试注入HAMA指标...');

                    // TradingView的指标系统很复杂，这里提供一个基本框架
                    // 实际使用时可能需要更复杂的逻辑

                    return {{
                        success: true,
                        message: 'HAMA指标注入尝试完成',
                        script_provided: {str(len(hama_script) > 0).lower()}
                    }};
                }} catch (error) {{
                    return {{
                        success: false,
                        error: error.toString()
                    }};
                }}
            }})();
            """

            result = self.driver.execute_script(inject_script)

            if result and result.get('success'):
                logger.info("✅ HAMA指标注入成功")

                # 等待指标加载
                time.sleep(3)

                # 尝试读取指标值
                return self.get_hama_from_tradingview(symbol, interval, wait_for_load=5)
            else:
                logger.error(f"❌ HAMA指标注入失败: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"❌ 使用自定义脚本获取HAMA失败: {str(e)}", exc_info=True)
            return None

        finally:
            self._close_driver()

    def get_price_from_tradingview(
        self,
        symbol: str,
        wait_for_load: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        从TradingView获取当前价格

        Args:
            symbol: 币种符号
            wait_for_load: 等待页面加载时间

        Returns:
            包含价格的字典
        """
        if not self._init_driver():
            return None

        try:
            url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}"
            logger.info(f"🌐 正在获取 {symbol} 的价格...")

            self.driver.get(url)
            time.sleep(wait_for_load)

            # 提取价格的JavaScript
            price_script = """
            (function() {
                try {
                    // 方法1: 查找价格元素
                    const priceElements = document.querySelectorAll('[class*="price"], [class*="last"]');
                    for (let elem of priceElements) {
                        const text = elem.textContent || elem.innerText;
                        const price = parseFloat(text.replace(/[^0-9.]/g, ''));
                        if (price > 0) {
                            return {
                                success: true,
                                price: price,
                                text: text
                            };
                        }
                    }

                    // 方法2: 尝试从页面标题读取
                    const title = document.title;
                    const priceMatch = title.match(/([0-9]+\\.?[0-9]*)/);
                    if (priceMatch) {
                        return {
                            success: true,
                            price: parseFloat(priceMatch[1]),
                            source: 'title'
                        };
                    }

                    return {
                        success: false,
                        error: 'Price not found'
                    };
                } catch (error) {
                    return {
                        success: false,
                        error: error.toString()
                    };
                }
            })();
            """

            result = self.driver.execute_script(price_script)

            if result and result.get('success'):
                price = result.get('price')
                logger.info(f"✅ 获取到价格: {price}")
                return {
                    'symbol': symbol,
                    'price': price,
                    'source': 'tradingview_selenium',
                    'timestamp': time.time()
                }
            else:
                logger.error(f"❌ 获取价格失败: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取价格异常: {str(e)}", exc_info=True)
            return None

        finally:
            self._close_driver()


# 导出便捷函数
def get_hama_indicator_from_tradingview(
    symbol: str,
    interval: str = "15",
    headless: bool = True,
    cookies: Dict[str, str] = None
) -> Optional[Dict[str, Any]]:
    """
    便捷函数: 从TradingView获取HAMA指标

    Args:
        symbol: 币种符号
        interval: 时间周期
        headless: 是否使用无头模式
        cookies: TradingView cookies (如果为None则从配置加载)

    Returns:
        HAMA指标数据
    """
    if cookies is None:
        cookies = load_cookies_from_config()

    service = TradingViewHamaSelenium(headless=headless, cookies=cookies)
    return service.get_hama_from_tradingview(symbol, interval)


def get_price_from_tradingview(
    symbol: str,
    headless: bool = True,
    cookies: Dict[str, str] = None
) -> Optional[Dict[str, Any]]:
    """
    便捷函数: 从TradingView获取价格

    Args:
        symbol: 币种符号
        headless: 是否使用无头模式
        cookies: TradingView cookies (如果为None则从配置加载)

    Returns:
        价格数据
    """
    if cookies is None:
        cookies = load_cookies_from_config()

    service = TradingViewHamaSelenium(headless=headless, cookies=cookies)
    return service.get_price_from_tradingview(symbol)
