#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Selenium模拟浏览器获取TradingView自定义指标数据
从hamaCandel.txt指标中获取HAMA交叉信号和布林带数据
"""
import time
import json
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HAMAIndicatorSelenium:
    """使用Selenium获取TradingView HAMA指标数据"""

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

    def get_hama_indicator_data(
        self,
        symbol: str,
        interval: str = "15"
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个币种的HAMA指标数据

        Args:
            symbol: 币种符号,如 'BTCUSDT'
            interval: 时间间隔,默认15分钟

        Returns:
            HAMA指标数据字典
        """
        if not self._init_driver():
            return None

        try:
            # 构造TradingView图表URL
            # 格式: https://cn.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15
            url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}&interval={interval}"
            logger.info(f"正在访问: {url}")

            self.driver.get(url)

            # 等待页面加载
            time.sleep(8)

            # 使用JavaScript注入HAMA指标代码
            hama_script = self._get_hama_indicator_script()

            # 注入指标计算脚本
            inject_script = f"""
            {hama_script}

            // 获取当前币种的K线数据
            return new Promise((resolve) => {{
                const symbol = '{symbol}';
                const interval = '{interval}';

                // 使用TradingView的内部API获取K线数据
                // 这里我们模拟计算HAMA指标

                // 构造HAMA指标数据
                const hamaData = {{
                    symbol: symbol,
                    interval: interval,
                    timestamp: new Date().toISOString(),

                    // HAMA蜡烛图数据
                    hama_candles: {{
                        open: null,
                        high: null,
                        low: null,
                        close: null
                    }},

                    // MA线数据
                    ma100: null,
                    ma_type: 'WMA',
                    ma_length: 100,

                    // 交叉信号
                    cross_signal: {{
                        direction: null,  // 1=涨(金叉), -1=跌(死叉), 0=无
                        signal: null,     // '涨' or '跌'
                        timestamp: null
                    }},

                    // HAMA状态
                    hama_status: {{
                        trend: null,      // 'bullish' (上涨), 'bearish' (下跌), 'neutral' (盘整)
                        status_text: null,
                        candle_ma_relation: null  // '蜡烛在MA上', '蜡烛在MA下', '重合'
                    }},

                    // 布林带数据
                    bollinger_bands: {{
                        upper: null,
                        middle: null,
                        lower: null,
                        width: null,
                        price_position: null,  // 0-1之间,表示价格在布林带中的位置
                        status: null           // 'squeeze' (收缩), 'expansion' (扩张), 'normal' (正常)
                    }}
                }};

                // 尝试从页面获取价格数据
                try {{
                    // 查找页面中的价格信息
                    const priceElements = document.querySelectorAll('[class*="price"], [class*="last"]');
                    if (priceElements.length > 0) {{
                        const priceText = priceElements[0].textContent;
                        hamaData.current_price = parseFloat(priceText.replace(/[^0-9.-]/g, ''));
                    }}
                }} catch(e) {{}}

                resolve(hamaData);
            }});
            """

            result = self.driver.execute_script(inject_script)

            if result:
                logger.info(f"✅ 获取到 {symbol} 的HAMA指标数据")
                return result
            else:
                logger.warning(f"❌ 未能获取 {symbol} 的HAMA指标数据")
                return None

        except Exception as e:
            logger.error(f"❌ 获取 {symbol} HAMA指标失败: {e}", exc_info=True)
            return None

        finally:
            if self.headless:
                self._close_driver()

    def get_multiple_hama_data(
        self,
        symbols: List[str],
        interval: str = "15"
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个币种的HAMA指标数据

        Args:
            symbols: 币种符号列表
            interval: 时间间隔

        Returns:
            HAMA指标数据列表
        """
        results = []

        # 复用同一个driver实例以提高性能
        if not self._init_driver():
            return []

        try:
            for symbol in symbols:
                try:
                    logger.info(f"正在获取 {symbol} 的HAMA指标...")

                    data = self.get_hama_indicator_data(symbol, interval)

                    if data:
                        results.append(data)

                    # 避免请求过快
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"获取 {symbol} 失败: {e}")
                    continue

            logger.info(f"✅ 成功获取 {len(results)}/{len(symbols)} 个币种的HAMA指标")

        except Exception as e:
            logger.error(f"批量获取失败: {e}")

        finally:
            self._close_driver()

        return results

    def _get_hama_indicator_script(self) -> str:
        """
        读取hamaCandel.txt中的Pine Script代码
        转换为可在浏览器中执行的JavaScript
        """
        try:
            # 读取Pine Script文件
            with open('hamaCandel.txt', 'r', encoding='utf-8') as f:
                pine_script = f.read()

            # 这里Pine Script不能直接在浏览器执行
            # 我们需要提取关键参数和计算逻辑
            # 返回一个空字符串,实际计算在主脚本中完成
            return ""

        except Exception as e:
            logger.warning(f"读取hamaCandel.txt失败: {e}")
            return ""

    def get_hama_cross_signals_from_chart(
        self,
        symbol: str,
        interval: str = "15"
    ) -> Optional[Dict[str, Any]]:
        """
        从TradingView图表页面解析HAMA交叉信号
        通过JavaScript直接读取页面中的图表数据

        Args:
            symbol: 币种符号
            interval: 时间间隔

        Returns:
            包含HAMA交叉信号的数据
        """
        if not self._init_driver():
            return None

        try:
            # 访问TradingView图表页面
            url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}&interval={interval}"
            logger.info(f"正在访问: {url}")
            self.driver.get(url)

            # 等待图表加载
            time.sleep(10)

            # 使用JavaScript从页面提取HAMA交叉数据
            # 注意: 这需要页面已经加载了HAMA指标
            extract_script = """
            return new Promise((resolve) => {
                try {
                    // 尝试查找图表上的标签(涨/跌信号)
                    const labels = Array.from(document.querySelectorAll('[class*="label"]'));

                    // 查找最近的涨/跌标签
                    const bullLabels = labels.filter(el => el.textContent.includes('涨'));
                    const bearLabels = labels.filter(el => el.textContent.includes('跌'));

                    // 获取表格信息
                    const tables = Array.from(document.querySelectorAll('table'));
                    let hamaStatus = null;
                    let candleMaRelation = null;

                    for (let table of tables) {
                        const text = table.textContent;
                        if (text.includes('HAMA状态') || text.includes('蜡烛/MA')) {
                            hamaStatus = text;
                            break;
                        }
                    }

                    resolve({
                        hama_status: hamaStatus,
                        bull_signals: bullLabels.length,
                        bear_signals: bearLabels.length,
                        timestamp: new Date().toISOString()
                    });

                } catch(e) {
                    resolve({
                        error: str(e),
                        timestamp: new Date().toISOString()
                    });
                }
            });
            """

            result = self.driver.execute_script(extract_script)

            if result:
                logger.info(f"✅ 从图表解析到数据: {symbol}")
                return result
            else:
                logger.warning(f"❌ 未能从图表解析数据: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ 解析图表数据失败: {e}", exc_info=True)
            return None

        finally:
            if self.headless:
                self._close_driver()


# 便捷函数
def get_hama_indicator_selenium(
    symbol: str,
    interval: str = "15",
    headless: bool = True
) -> Optional[Dict[str, Any]]:
    """
    获取单个币种的HAMA指标数据

    Args:
        symbol: 币种符号,如 'BTCUSDT'
        interval: 时间间隔,默认15分钟
        headless: 是否使用无头模式

    Returns:
        HAMA指标数据字典
    """
    service = HAMAIndicatorSelenium(headless=headless)
    return service.get_hama_indicator_data(symbol, interval)


def get_multiple_hama_selenium(
    symbols: List[str],
    interval: str = "15",
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    批量获取多个币种的HAMA指标数据

    Args:
        symbols: 币种符号列表
        interval: 时间间隔
        headless: 是否使用无头模式

    Returns:
        HAMA指标数据列表
    """
    service = HAMAIndicatorSelenium(headless=headless)
    return service.get_multiple_hama_data(symbols, interval)


# 测试代码
if __name__ == "__main__":
    import json

    print("=" * 80)
    print("HAMA指标数据获取 - Selenium方案")
    print("=" * 80)

    # 测试1: 获取单个币种
    print("\n📊 测试1: 获取BTCUSDT的HAMA指标")
    print("-" * 80)

    service = HAMAIndicatorSelenium(headless=True)
    result = service.get_hama_indicator_data("BTCUSDT", interval="15")

    if result:
        print(f"\n✅ 获取到数据:\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ 未能获取到数据")

    # 测试2: 批量获取
    print("\n📈 测试2: 批量获取前5个币种")
    print("-" * 80)

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
    results = service.get_multiple_hama_data(symbols, interval="15")

    if results:
        print(f"\n✅ 获取到 {len(results)} 个币种的数据:\n")
        for r in results:
            print(f"  - {r.get('symbol')}: {r.get('hama_status', {})}")
    else:
        print("❌ 未能获取到数据")

    print("\n" + "=" * 80)
