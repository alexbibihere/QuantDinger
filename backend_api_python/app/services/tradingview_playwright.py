#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Playwright 从 TradingView 提取图表指标数据
Playwright 是 pyppeteer 的继任者，由 Microsoft 维护
使用同步 API，避免异步上下文问题
"""
import os
import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright 未安装，TradingView 数据提取功能将不可用")
    PLAYWRIGHT_AVAILABLE = False

try:
    from playwright_stealth.stealth import Stealth
    STEALTH_AVAILABLE = True
    logger.info("✅ Playwright Stealth 模式可用 (Stealth 类)")
except ImportError:
    STEALTH_AVAILABLE = False
    logger.warning("Playwright Stealth 未安装，反爬检测能力可能受限")


class TradingViewPlaywrightExtractor:
    """使用 Playwright 从 TradingView 提取数据（同步版本）"""

    def __init__(self, headless: bool = True, cookies: list = None):
        """
        初始化提取器

        Args:
            headless: 是否使用无头模式
            cookies: TradingView cookies 列表（用于访问需要登录的图表）
                     格式: [{'name': 'cookie_name', 'value': 'cookie_value', 'domain': '.tradingview.com'}, ...]
        """
        self.headless = headless
        self.cookies = cookies
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # 获取代理配置
        self.proxy = None
        proxy_server = None  # 用于命令行参数

        proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')
        if proxy_url:
            # Playwright 代理配置格式
            self.proxy = {
                'server': proxy_url,
                'bypass': 'localhost,127.0.0.1'
            }
            proxy_server = proxy_url
            logger.info(f"✅ 使用代理: {proxy_url}")
        else:
            # 尝试从代理端口构建
            proxy_port = os.getenv('PROXY_PORT')
            if proxy_port:
                proxy_host = os.getenv('PROXY_HOST', 'host.docker.internal')
                proxy_url = f"http://{proxy_host}:{proxy_port}"
                self.proxy = {
                    'server': proxy_url,
                    'bypass': 'localhost,127.0.0.1'
                }
                proxy_server = proxy_url
                logger.info(f"✅ 使用代理: {proxy_url}")

        # Playwright 启动参数
        self.launch_args = {
            'headless': self.headless,
            'args': [
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
        }

        # 添加代理配置
        if self.proxy:
            self.launch_args['proxy'] = self.proxy
            # 同时添加命令行参数（双重保险）
            if proxy_server:
                self.launch_args['args'].append(f'--proxy-server={proxy_server}')
                logger.info(f"✅ 代理服务器已添加到启动参数: {proxy_server}")

        # User-Agent
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/120.0.0.0 Safari/537.36'

    def _init_browser(self):
        """初始化浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright 未安装，请运行: pip install playwright")

        if self.browser is None:
            # 使用同步 API
            self.playwright = sync_playwright().start()

            # 启动 Chromium 浏览器
            self.browser = self.playwright.chromium.launch(**self.launch_args)

            # 创建新页面
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            self.page.set_extra_http_headers({
                'User-Agent': self.user_agent,
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            self.page.set_default_timeout(60000)

            # 应用 stealth 模式来绕过反爬检测
            if STEALTH_AVAILABLE:
                try:
                    stealth_config = Stealth()
                    stealth_config.apply_stealth_sync(self.page)
                    logger.info("✅ Stealth 模式已启用 (Stealth.apply_stealth_sync)")
                except Exception as e:
                    logger.warning(f"⚠️ Stealth 模式启用失败: {e}")
            else:
                logger.info("ℹ️ Stealth 模式不可用，使用常规模式")

            # 设置 Cookies（如果提供）
            if self.cookies:
                try:
                    self.page.context.add_cookies(self.cookies)
                    logger.info(f"✅ 已添加 {len(self.cookies)} 个 Cookies")
                except Exception as e:
                    logger.warning(f"⚠️ 添加 Cookies 失败: {e}")

            logger.info("✅ Playwright 浏览器初始化成功")

    def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.close()
                self.browser = None
                self.page = None
                if self.playwright:
                    self.playwright.stop()
                    self.playwright = None
                logger.info("✅ 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器失败: {e}")

    def extract_chart_data(
        self,
        symbol: str = None,
        interval: str = "15",
        exchange: str = "BINANCE",
        chart_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        从 TradingView 提取图表数据

        Args:
            symbol: 币种符号，如 "BTCUSDT"
            interval: 时间间隔，如 "15"（15分钟）
            exchange: 交易所名称，默认 "BINANCE"
            chart_url: 自定义图表 URL（包含特定指标配置的图表链接）

        Returns:
            包含图表数据的字典，或 None
        """
        try:
            self._init_browser()

            # 检查 page 是否初始化成功
            if not self.page:
                raise Exception("浏览器页面初始化失败")

            # 构造 TradingView URL
            if chart_url:
                url = chart_url
                logger.info(f"📊 使用自定义图表 URL: {url}")
            else:
                url = f"https://www.tradingview.com/chart/?symbol={exchange}%3A{symbol}&interval={interval}"
                logger.info(f"📊 正在访问: {url}")

            # 访问页面并等待加载
            # 对于自定义图表 URL，使用 'load' 而不是 'networkidle'，因为页面可能有持续的网络请求
            load_strategy = 'load' if chart_url else 'networkidle'
            self.page.goto(url, wait_until=load_strategy, timeout=90000)
            logger.info("✅ 页面加载完成，等待图表渲染...")

            # 等待图表加载完成（自定义图表需要更长时间）
            wait_time = 60000 if chart_url else 30000
            try:
                # 尝试多个可能的选择器
                self.page.wait_for_selector('[data-role="chart-widget-content"]', timeout=wait_time)
                logger.info("✅ 图表容器加载完成")
            except Exception as e:
                logger.warning(f"⚠️ 等待图表选择器超时: {e}，尝试继续...")

            # 额外等待以确保 JavaScript 执行完成（自定义图表需要更长时间）
            extra_wait = 10000 if chart_url else 5000
            self.page.wait_for_timeout(extra_wait)

            # 截图用于调试（仅在有 chart_url 时）
            if chart_url:
                try:
                    screenshot_path = "/tmp/tradingview_debug.png"
                    self.page.screenshot(path=screenshot_path)
                    logger.info(f"📸 已保存截图: {screenshot_path}")
                except:
                    pass

            # 使用 JavaScript 直接从页面中提取数据
            logger.info("🔍 开始使用 JavaScript 提取图表数据...")
            data = self._extract_data_with_js(symbol)

            if data:
                logger.info(f"✅ JavaScript 提取成功，找到 {len(data.get('indicators_from_legend', []))} 个图例")
                return data

            # 如果 JS 提取失败，尝试使用 HTML 解析
            logger.info("🔄 JS 提取失败，尝试使用 HTML 解析...")
            content = self.page.content()
            logger.info(f"✅ 获取页面内容，长度: {len(content)} 字符")

            # 检查页面是否加载正确
            if len(content) < 200000:
                logger.warning(f"⚠️ 页面内容过少 ({len(content)} 字符)，可能是页面未完全加载或需要登录")

            # 解析数据
            return self._parse_chart_content(content, symbol)

        except Exception as e:
            logger.error(f"❌ 提取图表数据失败: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None
        finally:
            self._close_browser()

    def _extract_data_with_js(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        使用 JavaScript 直接从页面中提取数据

        Args:
            symbol: 币种符号

        Returns:
            提取的数据字典，或 None
        """
        try:
            # JavaScript 代码：尝试从页面中获取图表数据
            js_code = """
            () => {
                try {
                    // 方法 1: 尝试从 window 对象获取 TradingView 实例
                    if (window.ChartWidgetInstance) {
                        const widget = window.ChartWidgetInstance;
                        if (widget._model) {
                            const model = widget._model;
                            const data = {
                                method: 'ChartWidgetInstance',
                                symbol: model._mainSeriesFinancial.symbol(),
                                panes: []
                            };

                            // 获取所有窗格
                            model._panes.forEach(pane => {
                                const paneData = {
                                    sources: []
                                };

                                // 获取每个窗格的数据源
                                pane._sources.forEach(source => {
                                    if (source.name) {
                                        paneData.sources.push({
                                            type: source.constructor.name,
                                            name: source.name(),
                                            title: source.title ? source.title() : null
                                        });
                                    }
                                });

                                data.panes.push(paneData);
                            });

                            return JSON.stringify(data);
                        }
                    }

                    // 方法 2: 尝试查找并解析 script 标签中的数据
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const text = script.textContent;
                        if (text && text.includes('tokenize') && text.includes('symbol')) {
                            // 尝试提取 JSON 数据
                            const matches = text.match(/data-options="([^"]+)"/);
                            if (matches && matches[1]) {
                                return JSON.stringify({
                                    method: 'data-options',
                                    data: matches[1]
                                });
                            }
                        }
                    }

                    // 方法 3: 尝试从图例中提取文本
                    const legends = document.querySelectorAll('.pane-legend-title__container, [class*="legend"]');
                    const legendTexts = [];
                    legends.forEach(legend => {
                        const text = legend.textContent || legend.innerText;
                        if (text && text.trim()) {
                            legendTexts.push(text.trim());
                        }
                    });

                    if (legendTexts.length > 0) {
                        return JSON.stringify({
                            method: 'legend-text',
                            texts: legendTexts
                        });
                    }

                    return null;
                } catch (e) {
                    console.error('JS extraction error:', e);
                    return null;
                }
            }
            """

            # 执行 JavaScript
            result = self.page.evaluate(js_code)

            if result:
                logger.info(f"✅ JavaScript 提取成功: {result[:200]}...")

                # 解析结果
                parsed = json.loads(result)

                if parsed.get('method') == 'legend-text':
                    # 从图例文本中提取 HAMA 信息
                    return self._parse_legend_data(parsed.get('texts', []), symbol)

            return None

        except Exception as e:
            logger.warning(f"JavaScript 提取失败: {e}")
            return None

    def _parse_legend_data(self, texts: list, symbol: str) -> Dict[str, Any]:
        """
        从图例文本中解析数据

        Args:
            texts: 图例文本列表
            symbol: 币种符号

        Returns:
            解析后的数据
        """
        indicators_from_legend = []

        for text in texts:
            if text and text.strip():
                indicators_from_legend.append({
                    'name': text.strip()
                })

        return {
            'symbol': symbol,
            'indicators_from_legend': indicators_from_legend,
            'source': 'tradingview_playwright_js',
            'main_series': None,
            'indicators': []
        }

    def _parse_chart_content(
        self,
        content: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        解析图表页面内容

        Args:
            content: 页面 HTML 内容
            symbol: 币种符号

        Returns:
            解析后的数据字典
        """
        try:
            soup = BeautifulSoup(content, 'lxml')

            # 尝试多种方式查找图表数据
            chart_view = None

            # 方法 1: 查找 js-chart-view 元素
            chart_view = soup.find(attrs={"class": "js-chart-view"})

            # 方法 2: 如果方法1失败，尝试查找 data-options 属性
            if not chart_view:
                chart_view = soup.find(attrs={"data-options": True})

            # 方法 3: 如果还是找不到，尝试查找 script 标签中的数据
            if not chart_view:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'tokenize' in script.string and 'symbol' in script.string:
                        logger.info("✅ 找到包含图表数据的 script 标签")
                        # 这种情况下，我们无法直接解析，返回基本信息
                        return {
                            'symbol': symbol,
                            'source': 'tradingview_playwright',
                            'note': '使用备用数据源',
                            'indicators_from_legend': []
                        }

            if not chart_view or not chart_view.get('data-options'):
                logger.error("❌ 未找到图表数据")
                # 输出页面结构用于调试
                body = soup.find('body')
                if body:
                    classes = [tag.get('class') for tag in body.find_all(class_=True)[:10]]
                    logger.info(f"页面中的类名示例: {classes}")
                return None

            # 解析 JSON 数据
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

            # 从图例中提取指标值
            indicators_from_legend = []
            legend_elements = soup.find_all(attrs={"class": "pane-legend-title__container"})
            for legend in legend_elements:
                try:
                    legend_text = legend.get_text(strip=True)
                    if legend_text:
                        indicators_from_legend.append({
                            'name': legend_text
                        })
                except:
                    pass

            result = {
                'symbol': symbol,
                'main_series': main_series,
                'indicators': indicators,
                'indicators_from_legend': indicators_from_legend,
                'source': 'tradingview_playwright'
            }

            logger.info(f"✅ 成功解析 {symbol} 的图表数据")
            return result

        except Exception as e:
            logger.error(f"❌ 解析图表内容失败: {e}")
            return None


def extract_hama(
    symbol: str = None,
    interval: str = "15",
    headless: bool = True,
    chart_url: str = None,
    cookies: list = None
) -> Optional[Dict[str, Any]]:
    """
    提取 HAMA 指标

    Args:
        symbol: 币种符号（当使用 chart_url 时可以为 None）
        interval: 时间间隔
        headless: 是否使用无头模式
        chart_url: TradingView 图表 URL（需要包含 HAMA 指标的自定义图表）
        cookies: TradingView cookies（用于访问需要登录的私有图表）
                 格式: [{'name': 'cookie_name', 'value': 'cookie_value', 'domain': '.tradingview.com'}, ...]

    Returns:
        HAMA 指标数据

    注意：
    - 如果提供 chart_url，将直接使用该 URL 访问自定义图表
    - 如果不提供 chart_url，将使用默认的 TradingView 图表（可能不包含 HAMA 指标）
    - 如果图表需要登录，需要提供 cookies
    """
    extractor = TradingViewPlaywrightExtractor(headless=headless, cookies=cookies)

    try:
        data = extractor.extract_chart_data(symbol, interval, chart_url=chart_url)

        if not data:
            return None

        # 从图例中查找 HAMA 指标
        hama_value = None
        hama_color = None
        hama_trend = None
        price = None

        # 尝试从图例中提取
        for indicator in data.get('indicators_from_legend', []):
            name = indicator.get('name', '')
            if 'HAMA' in name:
                # 解析 HAMA 值和颜色
                hama_match = re.search(r'HAMA.*?([\d,]+\.?\d*)', name)
                if hama_match:
                    hama_value = float(hama_match.group(1).replace(',', ''))

                # 判断颜色/趋势
                if 'green' in name.lower() or '▲' in name or '↑' in name:
                    hama_color = 'green'
                    hama_trend = 'up'
                elif 'red' in name.lower() or '▼' in name or '↓' in name:
                    hama_color = 'red'
                    hama_trend = 'down'

        # 尝试从主序列获取价格
        if data.get('main_series'):
            states = data['main_series'].get('states', {})
            if states:
                # 获取最新价格
                price = list(states.values())[-1].get('close') if states else None

        # 从图例文本中尝试提取价格
        if not price and data.get('indicators_from_legend'):
            first_legend = data['indicators_from_legend'][0].get('name', '')
            price_match = re.search(r'[\d,]+\.\d{2}', first_legend)
            if price_match:
                price = float(price_match.group().replace(',', ''))

        result = {
            'symbol': symbol or data.get('symbol', 'UNKNOWN'),
            'hama_value': hama_value,
            'hama_color': hama_color,
            'hama_trend': hama_trend,
            'price': price,
            'source': 'tradingview_playwright',
            'note': 'HAMA 指标未在图表中找到' if hama_value is None else None
        }

        if hama_value:
            logger.info(f"✅ 成功提取 {symbol} HAMA 指标: {hama_value} ({hama_color})")
        else:
            logger.warning(f"⚠️ 未找到 HAMA 指标，请确保图表包含 HAMA 指标")

        return result

    except Exception as e:
        logger.error(f"❌ 提取 HAMA 失败: {e}")
        return None
    finally:
        extractor._close_browser()


def get_hama_from_tradingview(
    symbol: str = None,
    interval: str = "15",
    headless: bool = True,
    chart_url: str = None
) -> Optional[Dict[str, Any]]:
    """
    获取 HAMA 指标（同步包装器）

    Args:
        symbol: 币种符号
        interval: 时间间隔
        headless: 是否使用无头模式
        chart_url: 自定义图表 URL（包含 HAMA 指标的图表链接）

    Returns:
        HAMA 指标数据
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright 未安装")
        return None

    return extract_hama(symbol, interval, headless, chart_url)


def get_tradingview_data(
    symbol: str,
    interval: str = "15",
    exchange: str = "BINANCE",
    headless: bool = True
) -> Dict[str, Any]:
    """
    获取 TradingView 图表数据

    Args:
        symbol: 币种符号
        interval: 时间间隔
        exchange: 交易所
        headless: 是否使用无头模式

    Returns:
        图表数据
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright 未安装")
        return {}

    extractor = TradingViewPlaywrightExtractor(headless=headless)
    return extractor.extract_chart_data(symbol, interval, exchange)
