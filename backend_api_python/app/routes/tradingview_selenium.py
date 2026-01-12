#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView Selenium API路由
使用Selenium爬取TradingView数据
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Optional

logger = logging.getLogger(__name__)

tradingview_selenium_bp = Blueprint('tradingview_selenium', __name__)


@tradingview_selenium_bp.route('/test', methods=['GET'])
def test_selenium():
    """
    测试Selenium/Chromium是否正常工作

    GET /api/tradingview-selenium/test
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service

        logger.info("正在测试Selenium/Chromium...")

        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(
            options=chrome_options,
            service=Service(executable_path='/usr/bin/chromedriver')
        )

        # 获取浏览器信息
        browser_info = {
            'browser': 'Chromium',
            'version': driver.capabilities.get('browserVersion', 'unknown'),
            'driver_version': driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown'),
            'user_agent': driver.execute_script('return navigator.userAgent;')
        }

        driver.quit()

        logger.info(f"Selenium测试成功: {browser_info['version']}")

        return jsonify({
            'success': True,
            'message': 'Selenium/Chromium 工作正常',
            'data': browser_info
        })

    except Exception as e:
        logger.error(f"Selenium测试失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Selenium测试失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/fetch-page', methods=['POST'])
def fetch_page():
    """
    使用Selenium获取网页内容

    POST /api/tradingview-selenium/fetch-page
    Body:
        {
            "url": "https://www.tradingview.com/chart/...",
            "wait_seconds": 5,
            "selector": ".selector"  # 可选,提取特定元素
        }
    """
    try:
        data = request.get_json()
        url = data.get('url')
        wait_seconds = data.get('wait_seconds', 5)
        selector = data.get('selector')

        if not url:
            return jsonify({
                'success': False,
                'message': '缺少url参数'
            }), 400

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        import time

        logger.info(f"正在使用Selenium获取: {url}")

        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(
            options=chrome_options,
            service=Service(executable_path='/usr/bin/chromedriver')
        )

        try:
            driver.get(url)
            time.sleep(wait_seconds)

            # 如果指定了选择器,提取特定元素
            if selector:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    content = [elem.text for elem in elements if elem.text]
                except Exception as e:
                    logger.warning(f"选择器查找失败: {e}")
                    content = [driver.page_source]
            else:
                content = [driver.page_source]

            result = {
                'url': url,
                'title': driver.title,
                'content': content,
                'content_length': len(str(content))
            }

            logger.info(f"成功获取页面内容: {len(str(content))} 字符")

            return jsonify({
                'success': True,
                'data': result
            })

        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"获取页面失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取页面失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/hama-indicator/<symbol>', methods=['GET'])
def get_hama_indicator(symbol):
    """
    使用Selenium获取单个币种的HAMA指标数据

    GET /api/tradingview-selenium/hama-indicator/BTCUSDT?interval=15

    Args:
        symbol: 币种符号,如 BTCUSDT
        interval: 时间间隔(可选),默认15分钟

    Returns:
        HAMA指标数据,包括:
        - hama_candles: HAMA蜡烛图数据 (open, high, low, close)
        - ma100: MA100均线值
        - cross_signal: 交叉信号 (涨/跌)
        - hama_status: HAMA状态 (上涨趋势/下跌趋势/盘整)
        - bollinger_bands: 布林带数据
    """
    try:
        interval = request.args.get('interval', '15')

        logger.info(f"正在获取 {symbol} 的HAMA指标 (interval={interval})...")

        from app.services.hama_indicator_selenium import get_hama_indicator_selenium

        result = get_hama_indicator_selenium(symbol, interval=interval, headless=True)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '未能获取HAMA指标数据'
            }), 500

    except Exception as e:
        logger.error(f"获取HAMA指标失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取HAMA指标失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/hama-indicator/batch', methods=['POST'])
def get_batch_hama_indicators():
    """
    批量获取多个币种的HAMA指标数据

    POST /api/tradingview-selenium/hama-indicator/batch
    Body:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "interval": "15"
        }

    Returns:
        HAMA指标数据列表
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        interval = data.get('interval', '15')

        if not symbols:
            return jsonify({
                'success': False,
                'message': '缺少symbols参数'
            }), 400

        logger.info(f"正在批量获取 {len(symbols)} 个币种的HAMA指标...")

        from app.services.hama_indicator_selenium import get_multiple_hama_selenium

        results = get_multiple_hama_selenium(symbols, interval=interval, headless=True)

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        logger.error(f"批量获取HAMA指标失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'批量获取失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/hama-cross-signals/<symbol>', methods=['GET'])
def get_hama_cross_signals(symbol):
    """
    从TradingView图表页面解析HAMA交叉信号

    GET /api/tradingview-selenium/hama-cross-signals/BTCUSDT?interval=15

    Args:
        symbol: 币种符号
        interval: 时间间隔

    Returns:
        HAMA交叉信号数据
    """
    try:
        interval = request.args.get('interval', '15')

        logger.info(f"正在解析 {symbol} 的HAMA交叉信号...")

        from app.services.hama_indicator_selenium import HAMAIndicatorSelenium

        service = HAMAIndicatorSelenium(headless=True)
        result = service.get_hama_cross_signals_from_chart(symbol, interval)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '未能解析HAMA交叉信号'
            }), 500

    except Exception as e:
        logger.error(f"解析HAMA交叉信号失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'解析失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/hama-hybrid/<symbol>', methods=['GET'])
def get_hama_hybrid(symbol):
    """
    使用混合模式获取HAMA指标数据
    优先使用后端计算,失败时自动回退到Selenium

    GET /api/tradingview-selenium/hama-hybrid/BTCUSDT?interval=15&use_selenium=false&force_refresh=false

    Args:
        symbol: 币种符号
        interval: 时间间隔(可选),默认15分钟
        use_selenium: 是否强制使用Selenium (默认false)
        force_refresh: 是否强制刷新缓存 (默认false)

    Returns:
        HAMA指标数据
    """
    try:
        interval = request.args.get('interval', '15')
        use_selenium = request.args.get('use_selenium', 'false').lower() == 'true'
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        logger.info(f"[混合模式] 正在获取 {symbol} 的HAMA指标 (use_selenium={use_selenium}, force_refresh={force_refresh})...")

        from app.services.hama_hybrid_service import get_hama_indicator_hybrid

        result = get_hama_indicator_hybrid(symbol, interval, use_selenium, force_refresh)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '未能获取HAMA指标数据'
            }), 500

    except Exception as e:
        logger.error(f"[混合模式] 获取HAMA指标失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取HAMA指标失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/hama-hybrid/batch', methods=['POST'])
def get_batch_hama_hybrid():
    """
    批量获取HAMA指标数据(混合模式+并行)

    POST /api/tradingview-selenium/hama-hybrid/batch
    Body:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "interval": "15",
            "use_selenium": false,
            "max_parallel": 5
        }

    Returns:
        HAMA指标数据列表
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        interval = data.get('interval', '15')
        use_selenium = data.get('use_selenium', False)
        max_parallel = data.get('max_parallel', 5)

        if not symbols:
            return jsonify({
                'success': False,
                'message': '缺少symbols参数'
            }), 400

        logger.info(f"[混合模式批量] 正在获取 {len(symbols)} 个币种的HAMA指标 (并行数={max_parallel})...")

        from app.services.hama_hybrid_service import get_batch_hama_indicators_hybrid

        results = get_batch_hama_indicators_hybrid(symbols, interval, use_selenium, max_parallel)

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results,
            'total': len(symbols),
            'failed': len(symbols) - len(results)
        })

    except Exception as e:
        logger.error(f"[混合模式批量] 获取HAMA指标失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'批量获取失败: {str(e)}'
        }), 500


@tradingview_selenium_bp.route('/tradingview/scanner', methods=['GET'])
def tradingview_scanner():
    """
    使用JavaScript获取TradingView Scanner数据

    GET /api/tradingview-selenium/tradingview/scanner?symbols=BTCUSDT,ETHUSDT
    """
    try:
        symbols = request.args.get('symbols', 'BTCUSDT,ETHUSDT')

        # 构建symbol列表
        symbol_list = [f'BINANCE:{s}' if not s.startswith('BINANCE:') else s
                      for s in symbols.split(',')]

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service

        logger.info(f"正在获取{len(symbol_list)}个币种的Scanner数据...")

        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(
            options=chrome_options,
            service=Service(executable_path='/usr/bin/chromedriver')
        )

        try:
            # 使用TradingView Scanner API
            driver.get('https://scanner.tradingview.com/crypto/scan')

            # 执行JavaScript获取数据
            script = f'''
            return new Promise((resolve) => {{
                fetch('https://scanner.tradingview.com/crypto/scan', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        symbols: {{tickers: {symbol_list}}},
                        columns: ['name', 'description', 'update', 'Recommend.All|15', 'RSI|14|0']
                    }})
                }})
                .then(response => response.json())
                .then(data => resolve(data))
                .catch(err => resolve({{error: err.message}}));
            }});
            '''

            result = driver.execute_script(script)

            driver.quit()

            if result and not result.get('error'):
                # 解析返回数据
                scan_data = result.get('data', [])
                parsed_data = []

                for row in scan_data:
                    if len(row) >= 2:
                        symbol = row[0]
                        values = row[1] if len(row) > 1 else []

                        # 清理symbol
                        clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol

                        if 'USDT' in clean_symbol:
                            parsed_data.append({
                                'symbol': clean_symbol,
                                'description': values[1] if len(values) > 1 else clean_symbol,
                                'recommendation': values[3] if len(values) > 3 else None,
                                'rsi': values[4] if len(values) > 4 else None
                            })

                logger.info(f"成功获取{len(parsed_data)}个币种的数据")

                return jsonify({
                    'success': True,
                    'count': len(parsed_data),
                    'data': parsed_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result.get('error', '获取数据失败')
                }), 500

        except Exception as e:
            driver.quit()
            raise e

    except Exception as e:
        logger.error(f"TradingView Scanner失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Scanner失败: {str(e)}'
        }), 500
