#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA OCR 识别服务

使用 Playwright + RapidOCR 从 TradingView 识别 HAMA 指标面板
支持无头模式，速度快，准确率高
"""
import asyncio
import os
import sys
import re
import json
from datetime import datetime
from typing import Optional, Dict, Tuple, List

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False
# 导入 OCR 缓存服务
try:
    from app.services.hama_ocr_cache import ORCCache, create_ocr_cache_table
    OCR_CACHE_AVAILABLE = True
except ImportError:
    OCR_CACHE_AVAILABLE = False
    ORCCache = None


from app.utils.logger import get_logger

logger = get_logger(__name__)


# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class HAMAOCRService:
    """HAMA OCR 识别服务"""

    def __init__(self):
        self.ocr = None
        self.cookies = None
        self.tv_url = None
        self.screenshot_dir = "screenshot"

        # 创建截图目录
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # 初始化 OCR
        if RAPIDOCR_AVAILABLE:
            self.ocr = RapidOCR()
            logger.info("RapidOCR 初始化成功")
        else:
            logger.warning("RapidOCR 未安装，OCR 功能不可用")

    def load_config(self):
        """从 tradingview.txt 加载配置"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), '../../file/tradingview.txt')

            if not os.path.exists(config_file):
                logger.error(f"配置文件不存在: {config_file}")
                return False

            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取 URL
            url_match = re.search(r'(https://[^\s]+)', content)
            self.tv_url = url_match.group(1) if url_match else "https://cn.tradingview.com/chart/U1FY2qxO/"

            # 提取 Cookie
            cookie_match = re.search(r'cookie:(.+)', content)
            cookie_str = cookie_match.group(1).strip() if cookie_match else ""

            # 解析 Cookie
            self.cookies = []
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    self.cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.tradingview.com',
                        'path': '/'
                    })

            logger.info(f"配置加载成功: {len(self.cookies)} cookies, URL: {self.tv_url}")
            return True

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return False

    def parse_cookie_string(self, cookie_str):
        """解析 Cookie 字符串为字典列表"""
        cookies = []
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.tradingview.com',
                    'path': '/'
                })
        return cookies

    def parse_hama_ocr_text(self, ocr_results):
        """解析 OCR 识别结果，提取 HAMA 指标数据"""
        hama_data = {
            'symbol': None,
            'trend': None,
            'hama_value': None,
            'hama_color': None,
            'status': None,
            'candle_ma': None,
            'contraction': None,
            'last_cross': None,
            'price': None,
            'raw_text': []
        }

        if not ocr_results:
            return hama_data

        # RapidOCR 返回格式: (results, elapse)
        # results 是列表，每个元素格式: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence]
        if isinstance(ocr_results, tuple):
            ocr_list = ocr_results[0]
        else:
            ocr_list = ocr_results

        all_texts = []
        hama_data['raw_text'] = []

        for item in ocr_list:
            if isinstance(item, list) and len(item) >= 3:
                if isinstance(item[1], str):
                    text = item[1].strip()
                    confidence = item[2] if isinstance(item[2], (int, float)) else 0.0

                    if text:
                        all_texts.append(text)
                        hama_data['raw_text'].append((text, confidence))

                        # 提取特定字段
                        if 'HAMA状态' in text or text == 'HAMA状态':
                            continue
                        elif '上涨趋势' in text or 'UP' in text.upper():
                            hama_data['trend'] = 'UP'
                            hama_data['hama_color'] = 'green'
                        elif '下跌趋势' in text or 'DOWN' in text.upper():
                            hama_data['trend'] = 'DOWN'
                            hama_data['hama_color'] = 'red'
                        elif '蜡烛在MA上' in text:
                            hama_data['candle_ma'] = 'above'
                        elif '蜡烛在MA下' in text:
                            hama_data['candle_ma'] = 'below'
                        elif '收缩' in text:
                            hama_data['contraction'] = 'yes'
                        elif '扩张' in text:
                            hama_data['contraction'] = 'no'
                        elif '涨' in text or '跌' in text:
                            if '交叉' in all_texts[-2:] if all_texts else False:
                                hama_data['last_cross'] = text

        all_text = ' '.join(all_texts)

        # 提取价格（识别数字格式：3311.73 或 3,311.73）
        price_matches = re.findall(r'(\d{1,5}[,.]?\d{0,2}[,.]?\d{0,2})', all_text)
        if price_matches:
            # 取最后一个价格（通常是当前价格）
            for price_str in reversed(price_matches[-5:]):
                try:
                    # 清理价格字符串
                    price_clean = price_str.replace(',', '').strip()
                    price = float(price_clean)
                    # 合理的价格范围（100 - 200000）
                    if 100 < price < 200000:
                        hama_data['price'] = price
                        break
                except:
                    continue

        return hama_data

    async def capture_hama_panel(self, symbol: Optional[str] = None, tv_url: Optional[str] = None) -> Dict:
        """
        截取并识别 HAMA 面板

        参数:
            symbol: 币种符号（可选，用于构建 URL）
            tv_url: TradingView 图表 URL（可选，覆盖 symbol）

        返回:
            {
                'success': True/False,
                'data': {
                    'symbol': 'BTCUSDT',
                    'trend': 'UP',
                    'hama_color': 'green',
                    'candle_ma': 'above',
                    'contraction': 'yes',
                    'last_cross': None,
                    'price': 3311.73,
                    'screenshot': 'path/to/screenshot.png',
                    'timestamp': '20260118_081620'
                },
                'error': None
            }
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {
                'success': False,
                'error': 'Playwright 未安装'
            }

        if not RAPIDOCR_AVAILABLE:
            return {
                'success': False,
                'error': 'RapidOCR 未安装'
            }

        try:
            # 加载配置
            if not self.cookies or not self.tv_url:
                if not self.load_config():
                    return {
                        'success': False,
                        'error': '配置加载失败'
                    }

            # 确定 URL
            url = tv_url or self.tv_url
            if symbol and not tv_url:
                # 如果提供了 symbol，构建 URL
                url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol={symbol}"

            # 从 URL 提取币种
            symbol_match = re.search(r'/s([A-Z]+)', url) or re.search(r'symbol=([A-Z]+)', url)
            display_symbol = (symbol_match.group(1) + 'USDT') if symbol_match else (symbol or 'UNKNOWN')

            logger.info(f"开始截取 HAMA 面板: {display_symbol}")

            async with async_playwright() as p:
                # Brave 浏览器路径（Windows）
                brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                user_data_dir = "./brave_profile"

                # 启动浏览器（无头模式）
                try:
                    # 检查是否配置了代理
                    proxy_config = {}
                    proxy_port = os.getenv('PROXY_PORT')
                    proxy_host = os.getenv('PROXY_HOST')

                    if proxy_port and proxy_host:
                        proxy_url = f"{os.getenv('PROXY_SCHEME', 'socks5h')}://{proxy_host}:{proxy_port}"
                        proxy_config = {
                            'server': {
                                'host': proxy_host,
                                'port': int(proxy_port)
                            }
                        }
                        logger.info(f"使用代理: {proxy_url}")

                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=False,  # 有头模式，显示浏览器窗口
                        executable_path=brave_path if os.path.exists(brave_path) else None,
                        viewport={'width': 1920, 'height': 1080},
                        args=['--disable-blink-features=AutomationControlled'],
                        proxy=proxy_config if proxy_config else None
                    )
                except Exception as e:
                    logger.warning(f"Brave 启动失败: {e}，使用 Chromium")
                    # 检查是否配置了代理
                    proxy_config = {}
                    proxy_port = os.getenv('PROXY_PORT')
                    proxy_host = os.getenv('PROXY_HOST')

                    if proxy_port and proxy_host:
                        proxy_url = f"{os.getenv('PROXY_SCHEME', 'socks5h')}://{proxy_host}:{proxy_port}"
                        proxy_config = {
                            'server': {
                                'host': proxy_host,
                                'port': int(proxy_port)
                            }
                        }
                        logger.info(f"使用代理: {proxy_url}")

                    browser = await p.chromium.launch(
                        headless=False,  # 有头模式，显示浏览器窗口
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--disable-setuid-sandbox'
                        ],
                        proxy=proxy_config if proxy_config else None
                    )

                context = browser
                if len(context.pages) > 0:
                    page = context.pages[0]
                else:
                    page = await context.new_page()

                try:
                    # 访问 TradingView
                    await page.goto(url, wait_until='domcontentloaded', timeout=90000)

                    # 等待图表加载
                    await page.wait_for_timeout(8000)

                    # 截取右侧 HAMA 面板
                    viewport_size = page.viewport_size
                    page_width = viewport_size['width']
                    page_height = viewport_size['height']

                    # 右侧居中区域 - 根据实际截图调整
                    # HAMA 面板大约在右侧 72%-95% 宽度，高度 15%-70% 位置
                    hama_clip = {
                        'x': int(page_width * 0.72),   # 稍微向左调整
                        'y': int(page_height * 0.18),  # 稍微向上调整
                        'width': int(page_width * 0.23),  # 稍微减小宽度
                        'height': int(page_height * 0.50)  # 稍微减小高度
                    }

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(self.screenshot_dir, f"hama_panel_{timestamp}.png")

                    await page.screenshot(path=screenshot_path, clip=hama_clip)
                    logger.info(f"截图保存: {screenshot_path}")

                    # OCR 识别
                    result = self.ocr(screenshot_path)

                    # 解析结果
                    hama_data = self.parse_hama_ocr_text(result) if result else {}

                    # 添加额外信息
                    hama_data['symbol'] = display_symbol
                    hama_data['screenshot'] = screenshot_path
                    hama_data['timestamp'] = timestamp

                    logger.info(f"HAMA 识别成功: {display_symbol}, 趋势: {hama_data.get('trend')}")

                    return {
                        'success': True,
                        'data': hama_data
                    }

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"截取 HAMA 面板失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def capture_hama_panel_sync(self, symbol: Optional[str] = None, tv_url: Optional[str] = None) -> Dict:
        """
        同步版本的截取方法（用于从同步代码调用）

        参数:
            symbol: 币种符号（可选）
            tv_url: TradingView 图表 URL（可选）

        返回:
            同上
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.capture_hama_panel(symbol, tv_url))


# 全局单例
_ocr_service = None


def get_ocr_service() -> HAMAOCRService:
    """获取 OCR 服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = HAMAOCRService()
    return _ocr_service
