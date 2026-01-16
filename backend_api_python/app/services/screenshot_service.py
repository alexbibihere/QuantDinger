#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图服务 - 支持多种截图方案
"""
import os
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ScreenshotService:
    """截图服务 - 支持多种截图引擎"""

    def __init__(self, engine: str = 'playwright'):
        """
        初始化截图服务

        Args:
            engine: 截图引擎 ('playwright', 'selenium', 'pyppeteer')
        """
        self.engine = engine
        self._init_engine()

    def _init_engine(self):
        """初始化截图引擎"""
        if self.engine == 'playwright':
            self._init_playwright()
        elif self.engine == 'selenium':
            self._init_selenium()
        elif self.engine == 'pyppeteer':
            self._init_pyppeteer()
        else:
            raise ValueError(f'不支持的截图引擎: {self.engine}')

    def _init_playwright(self):
        """初始化 Playwright"""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright
            self.browser = None
            logger.info('✅ Playwright 初始化成功')
        except ImportError:
            logger.error('❌ Playwright 未安装')
            logger.info('安装: pip install playwright && playwright install chromium')
            raise

    def _init_selenium(self):
        """初始化 Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            self.webdriver = webdriver
            self.chrome_options = Options()
            self.chrome_options.add_argument('--headless')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--window-size=1920,1080')
            logger.info('✅ Selenium 初始化成功')
        except ImportError:
            logger.error('❌ Selenium 未安装')
            logger.info('安装: pip install selenium')
            raise

    def _init_pyppeteer(self):
        """初始化 Pyppeteer"""
        try:
            import pyppeteer
            self.pyppeteer = pyppeteer
            logger.info('✅ Pyppeteer 初始化成功')
        except ImportError:
            logger.error('❌ Pyppeteer 未安装')
            logger.info('安装: pip install pyppeteer')
            raise

    def capture(
        self,
        url: str,
        output_path: str,
        wait_time: int = 5,
        width: int = 1920,
        height: int = 1080,
        full_page: bool = False,
        selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        截取网页截图

        Args:
            url: 目标 URL
            output_path: 输出文件路径
            wait_time: 等待时间(秒)
            width: 窗口宽度
            height: 窗口高度
            full_page: 是否截取整个页面
            selector: CSS 选择器(只截取特定元素)

        Returns:
            包含截图信息的字典
        """
        if self.engine == 'playwright':
            return self._capture_playwright(
                url, output_path, wait_time, width, height, full_page, selector
            )
        elif self.engine == 'selenium':
            return self._capture_selenium(
                url, output_path, wait_time, width, height, full_page, selector
            )
        elif self.engine == 'pyppeteer':
            return self._capture_pyppeteer(
                url, output_path, wait_time, width, height, full_page, selector
            )

    def _capture_playwright(
        self,
        url: str,
        output_path: str,
        wait_time: int,
        width: int,
        height: int,
        full_page: bool,
        selector: Optional[str]
    ) -> Dict[str, Any]:
        """使用 Playwright 截图"""
        start_time = time.time()

        with self.playwright() as p:
            self.browser = p.chromium.launch(headless=True)
            page = self.browser.new_page(viewport={'width': width, 'height': height})

            # 访问页面
            logger.info(f'访问: {url}')
            page.goto(url, wait_until='networkidle', timeout=60000)

            # 等待加载
            if wait_time > 0:
                logger.info(f'等待 {wait_time} 秒...')
                time.sleep(wait_time)

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # 截图
            if selector:
                # 只截取特定元素
                logger.info(f'截取元素: {selector}')
                element = page.query_selector(selector)
                if element:
                    element.screenshot(path=output_path)
                else:
                    logger.warning(f'未找到元素: {selector}, 截取整个页面')
                    page.screenshot(path=output_path, full_page=full_page)
            else:
                # 截取整个页面或视口
                page.screenshot(path=output_path, full_page=full_page)

            self.browser.close()

        file_size = os.path.getsize(output_path)
        elapsed = time.time() - start_time

        logger.info(f'✅ 截图成功: {output_path} ({file_size / 1024:.1f} KB, 耗时 {elapsed:.1f}s)')

        return {
            'success': True,
            'output_path': output_path,
            'file_size': file_size,
            'elapsed': elapsed,
            'engine': 'playwright'
        }

    def _capture_selenium(
        self,
        url: str,
        output_path: str,
        wait_time: int,
        width: int,
        height: int,
        full_page: bool,
        selector: Optional[str]
    ) -> Dict[str, Any]:
        """使用 Selenium 截图"""
        start_time = time.time()

        # 设置窗口大小
        self.chrome_options.add_argument(f'--window-size={width},{height}')

        driver = self.webdriver.Chrome(options=self.chrome_options)

        try:
            # 访问页面
            logger.info(f'访问: {url}')
            driver.get(url)

            # 等待加载
            if wait_time > 0:
                logger.info(f'等待 {wait_time} 秒...')
                time.sleep(wait_time)

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # 截图
            if selector:
                # 只截取特定元素
                logger.info(f'截取元素: {selector}')
                try:
                    from selenium.webdriver.common.by import By
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    element.screenshot(output_path)
                except:
                    logger.warning(f'未找到元素: {selector}, 截取整个页面')
                    driver.save_screenshot(output_path)
            else:
                driver.save_screenshot(output_path)

            file_size = os.path.getsize(output_path)
            elapsed = time.time() - start_time

            logger.info(f'✅ 截图成功: {output_path} ({file_size / 1024:.1f} KB, 耗时 {elapsed:.1f}s)')

            return {
                'success': True,
                'output_path': output_path,
                'file_size': file_size,
                'elapsed': elapsed,
                'engine': 'selenium'
            }

        finally:
            driver.quit()

    def _capture_pyppeteer(
        self,
        url: str,
        output_path: str,
        wait_time: int,
        width: int,
        height: int,
        full_page: bool,
        selector: Optional[str]
    ) -> Dict[str, Any]:
        """使用 Pyppeteer 截图"""
        import asyncio

        async def _screenshot():
            browser = await self.pyppeteer.launch(headless=True)
            page = await browser.newPage()
            await page.setViewport({'width': width, 'height': height})

            # 访问页面
            logger.info(f'访问: {url}')
            await page.goto(url, wait_until='networkidle0')

            # 等待加载
            if wait_time > 0:
                logger.info(f'等待 {wait_time} 秒...')
                await asyncio.sleep(wait_time)

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # 截图
            if selector:
                logger.info(f'截取元素: {selector}')
                await page.querySelectorEval(selector, 'e => e.screenshot()')
            else:
                await page.screenshot({'path': output_path, 'fullPage': full_page})

            await browser.close()

        start_time = time.time()
        asyncio.get_event_loop().run_until_complete(_screenshot())

        file_size = os.path.getsize(output_path)
        elapsed = time.time() - start_time

        logger.info(f'✅ 截图成功: {output_path} ({file_size / 1024:.1f} KB, 耗时 {elapsed:.1f}s)')

        return {
            'success': True,
            'output_path': output_path,
            'file_size': file_size,
            'elapsed': elapsed,
            'engine': 'pyppeteer'
        }


# 便捷函数
def capture_screenshot(
    url: str,
    output_path: str,
    engine: str = 'playwright',
    **kwargs
) -> Dict[str, Any]:
    """
    截图便捷函数

    Args:
        url: 目标 URL
        output_path: 输出路径
        engine: 截图引擎 ('playwright', 'selenium', 'pyppeteer')
        **kwargs: 其他参数

    Returns:
        截图结果字典
    """
    service = ScreenshotService(engine=engine)
    return service.capture(url, output_path, **kwargs)


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)

    # 测试 TradingView Widget
    widget_url = 'https://s.tradingview.com/widgetembed/'
    params = '?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1'

    result = capture_screenshot(
        url=widget_url + params,
        output_path='../screenshot/test_screenshot.png',
        engine='selenium',  # 使用 selenium,因为已安装
        wait_time=10,
        width=1920,
        height=1080
    )

    print(f'\n结果: {result}')
