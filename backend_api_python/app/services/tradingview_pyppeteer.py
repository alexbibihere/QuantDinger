#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 pyppeteer 从 TradingView 提取图表指标数据
参考: https://github.com/jchao01/TradingView-data-scraper
"""
import asyncio
import json
import re
import nest_asyncio
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from app.utils.logger import get_logger

# 应用 nest_asyncio 以在同步环境中运行异步代码
nest_asyncio.apply()

logger = get_logger(__name__)

try:
    import pyppeteer
    pyppeteer.DEBUG = False
    PYPPETEER_AVAILABLE = True
except ImportError:
    logger.warning("pyppeteer 未安装，TradingView 数据提取功能将不可用")
    PYPPETEER_AVAILABLE = False


class TradingViewPyppeteerExtractor:
    """使用 pyppeteer 从 TradingView 提取数据"""

    def __init__(self, headless: bool = True):
        """
        初始化提取器

        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        self.browser = None
        self.page = None

        # Pyppeteer 启动参数
        self.args = [
            '--window-size=1920,1080',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-certificate-errors',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--disable-gpu',
            '--disable-infobars',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]

        # User-Agent
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        }

    async def _init_browser(self):
        """初始化浏览器"""
        if not PYPPETEER_AVAILABLE:
            raise ImportError("pyppeteer 未安装，请运行: pip install pyppeteer")

        if self.browser is None:
            # 使用系统安装的 Chromium
            import os
            chromium_path = '/usr/bin/chromium'

            if not os.path.exists(chromium_path):
                logger.warning(f"系统 Chromium 不存在于 {chromium_path}，尝试使用 pyppeteer 下载的版本")
            else:
                # 添加可执行路径参数
                self.args.append(f'--executable-path={chromium_path}')
                logger.info(f"📦 使用系统 Chromium: {chromium_path}")

            self.browser = await pyppeteer.launch(
                headless=self.headless,
                ignoreHTTPSErrors=True,
                args=self.args,
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False
            )

            self.page = await self.browser.newPage()
            await self.page.setViewport(dict(width=1920, height=1080))
            await self.page.setUserAgent(self.headers['user-agent'])
            await self.page.setDefaultNavigationTimeout(60000)

            logger.info("✅ Pyppeteer 浏览器初始化成功")

    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
                self.page = None
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器失败: {e}")

    async def extract_chart_data(
        self,
        symbol: str,
        interval: str = "15",
        exchange: str = "BINANCE"
    ) -> Optional[Dict[str, Any]]:
        """
        从 TradingView 提取图表数据

        Args:
            symbol: 币种符号 (如 BTCUSDT)
            interval: 时间间隔 (15, 60, D等)
            exchange: 交易所名称

        Returns:
            包含价格和指标数据的字典
        """
        try:
            await self._init_browser()

            # 构造 TradingView 图表 URL
            url = f"https://www.tradingview.com/chart/?symbol={exchange}%3A{symbol}&interval={interval}"

            logger.info(f"🌐 正在访问 TradingView: {url}")

            # 访问页面
            await self.page.goto(url, {'waitUntil': 'networkidle2'})

            # 等待图表加载
            try:
                await self.page.waitForSelector('.pane-legend-title__container', {'timeout': 15000})
            except:
                logger.warning("未找到 .pane-legend-title__container，尝试其他选择器")
                # 尝试其他可能的选择器
                await asyncio.sleep(5)

            # 获取页面内容
            content = await self.page.content()

            # 解析数据
            data = await self._parse_chart_content(content, symbol)

            return data

        except Exception as e:
            logger.error(f"提取图表数据失败: {e}", exc_info=True)
            return None

        finally:
            await self._close_browser()

    async def _parse_chart_content(
        self,
        content: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        解析图表内容

        Args:
            content: HTML 内容
            symbol: 币种符号

        Returns:
            解析后的数据
        """
        try:
            soup = BeautifulSoup(content, 'lxml')

            # 提取指标名称和值
            ind_titles = soup.findAll(attrs={"class": "pane-legend-line"})
            indicators_info = []

            for ind in ind_titles:
                try:
                    name_elem = ind.find(attrs={"class": "pane-legend-title__description"})
                    values = ind.findAll(attrs={"class": "pane-legend-item-value-wrap"})

                    if name_elem:
                        name = name_elem.get_text().strip()
                        value_str = ' '.join([v.get_text().strip() for v in values])
                        indicators_info.append({
                            'name': name,
                            'value': value_str
                        })
                except Exception as e:
                    logger.debug(f"解析指标行失败: {e}")
                    continue

            # 提取主要的图表数据
            chart_data = None
            chart_view = soup.find(attrs={"class": "js-chart-view"})

            if chart_view and chart_view.get('data-options'):
                try:
                    json_string = chart_view['data-options']
                    parsed_string = json.loads(json_string)
                    panes = json.loads(parsed_string['content'])['panes']

                    # 提取主序列和指标
                    main_series = None
                    indicators = []

                    for pane in panes:
                        for source in pane.get('sources', []):
                            if source.get('type') == 'MainSeries':
                                main_series = source
                            elif source.get('type') == 'Study':
                                indicators.append(source)

                    if main_series:
                        # 提取 OHLCV 数据
                        bars_data = main_series.get('bars', {}).get('data', [])

                        if bars_data:
                            # 获取最新的K线数据
                            latest_bar = bars_data[-1]
                            values = latest_bar.get('value', [])

                            if len(values) >= 5:
                                chart_data = {
                                    'time': values[0],
                                    'open': values[1],
                                    'high': values[2],
                                    'low': values[3],
                                    'close': values[4],
                                    'volume': values[5] if len(values) > 5 else 0
                                }

                                # 提取指标数据
                                indicator_values = {}
                                for indicator in indicators:
                                    meta_info = indicator.get('metaInfo', {})
                                    short_name = meta_info.get('shortDescription', 'Unknown')

                                    # 查找对应的指标数据
                                    ind_data = indicator.get('data', {}).get('data', [])
                                    for ind_bar in ind_data:
                                        if ind_bar['value'][0] == chart_data['time']:
                                            # 匹配时间戳
                                            ind_values = ind_bar['value'][1:]  # 去掉时间戳
                                            indicator_values[short_name] = ind_values
                                            break

                                chart_data['indicators'] = indicator_values

                except Exception as e:
                    logger.error(f"解析图表 JSON 数据失败: {e}")

            # 构造返回结果
            result = {
                'symbol': symbol,
                'indicators_from_legend': indicators_info,
                'chart_data': chart_data,
                'source': 'tradingview_pyppeteer',
                'raw_html_available': True
            }

            logger.info(f"✅ 成功提取 {symbol} 的数据")
            return result

        except Exception as e:
            logger.error(f"解析图表内容失败: {e}", exc_info=True)
            return None


# 导出便捷函数
async def get_tradingview_data_async(
    symbol: str,
    interval: str = "15",
    exchange: str = "BINANCE",
    headless: bool = True
) -> Optional[Dict[str, Any]]:
    """
    异步获取 TradingView 数据

    Args:
        symbol: 币种符号
        interval: 时间间隔
        exchange: 交易所
        headless: 是否无头模式

    Returns:
        图表数据
    """
    if not PYPPETEER_AVAILABLE:
        logger.error("pyppeteer 未安装")
        return None

    extractor = TradingViewPyppeteerExtractor(headless=headless)
    return await extractor.extract_chart_data(symbol, interval, exchange)


def get_tradingview_data(
    symbol: str,
    interval: str = "15",
    exchange: str = "BINANCE",
    headless: bool = True
) -> Optional[Dict[str, Any]]:
    """
    同步包装函数 - 获取 TradingView 数据

    Args:
        symbol: 币种符号
        interval: 时间间隔
        exchange: 交易所
        headless: 是否无头模式

    Returns:
        图表数据
    """
    if not PYPPETEER_AVAILABLE:
        logger.error("pyppeteer 未安装")
        return None

    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        get_tradingview_data_async(symbol, interval, exchange, headless)
    )


def get_hama_from_tradingview(
    symbol: str,
    interval: str = "15",
    headless: bool = True
) -> Optional[Dict[str, Any]]:
    """
    从 TradingView 获取 HAMA 指标数据

    Args:
        symbol: 币种符号
        interval: 时间间隔
        headless: 是否无头模式

    Returns:
        HAMA 指标数据
    """
    data = get_tradingview_data(symbol, interval, "BINANCE", headless)

    if not data:
        return None

    # 尝试从图例中提取 HAMA 指标
    hama_value = None
    hama_color = None
    hama_trend = None

    for indicator in data.get('indicators_from_legend', []):
        name = indicator.get('name', '').upper()
        value = indicator.get('value', '')

        # 查找 HAMA 相关指标
        if 'HAMA' in name or 'Hama' in name:
            hama_value = value

            # 尝试从值中提取颜色/趋势信息
            # TradingView 通常会在值前加颜色标记
            if '↑' in value or '▼' in value or '+' in value.split()[0]:
                hama_color = 'green'
                hama_trend = 'up'
            elif '↓' in value or '▲' in value or '-' in value.split()[0]:
                hama_color = 'red'
                hama_trend = 'down'

            break

    # 从图表数据中获取价格信息
    chart_data = data.get('chart_data', {})
    price = chart_data.get('close', 0) if chart_data else 0

    result = {
        'symbol': symbol,
        'interval': interval,
        'hama_value': hama_value,
        'hama_color': hama_color,
        'hama_trend': hama_trend,
        'price': price,
        'source': 'tradingview_pyppeteer',
        'raw_data': data
    }

    return result
