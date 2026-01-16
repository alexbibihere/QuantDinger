#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图助手 - 简洁的 API 封装
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class ScreenshotHelper:
    """截图助手 - 使用 Selenium"""

    def __init__(self, proxy_port: Optional[int] = None, headless: bool = True):
        """
        初始化截图助手

        Args:
            proxy_port: 代理端口
            headless: 是否无头模式
        """
        self.proxy_port = proxy_port or os.environ.get('PROXY_PORT')
        self.headless = headless
        self.driver = None

    def _get_options(self) -> Options:
        """获取 Chrome 选项"""
        options = Options()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # 代理配置
        if self.proxy_port:
            options.add_argument(f'--proxy-server=http://127.0.0.1:{self.proxy_port}')
            logger.info(f'使用代理: 127.0.0.1:{self.proxy_port}')

        return options

    def capture(
        self,
        url: str,
        output_path: str,
        wait_time: int = 10,
        width: int = 1920,
        height: int = 1080
    ) -> Dict[str, Any]:
        """
        截取网页

        Args:
            url: 目标 URL
            output_path: 输出路径
            wait_time: 等待时间(秒)
            width: 窗口宽度
            height: 窗口高度

        Returns:
            结果字典
        """
        start_time = time.time()

        try:
            # 配置浏览器
            options = self._get_options()
            options.add_argument(f'--window-size={width},{height}')

            self.driver = webdriver.Chrome(options=options)

            # 访问页面
            logger.info(f'访问: {url}')
            self.driver.get(url)

            # 等待加载
            if wait_time > 0:
                logger.info(f'等待 {wait_time} 秒...')
                time.sleep(wait_time)

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # 截图
            self.driver.save_screenshot(output_path)
            file_size = os.path.getsize(output_path)
            elapsed = time.time() - start_time

            logger.info(f'✅ 截图成功: {output_path} ({file_size / 1024:.1f} KB, {elapsed:.1f}s)')

            return {
                'success': True,
                'output_path': output_path,
                'file_size': file_size,
                'elapsed': elapsed
            }

        except Exception as e:
            logger.error(f'❌ 截图失败: {e}')
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            if self.driver:
                self.driver.quit()

    def capture_with_cookie(
        self,
        url: str,
        output_path: str,
        cookie_string: str,
        wait_time: int = 10
    ) -> Dict[str, Any]:
        """
        使用 Cookie 截图

        Args:
            url: 目标 URL
            output_path: 输出路径
            cookie_string: Cookie 字符串
            wait_time: 等待时间

        Returns:
            结果字典
        """
        start_time = time.time()

        try:
            # 配置浏览器
            options = self._get_options()
            options.add_argument('--window-size=2560,1440')

            self.driver = webdriver.Chrome(options=options)

            # 先访问主页
            logger.info('访问主页以设置域...')
            self.driver.get('https://cn.tradingview.com/')
            time.sleep(2)

            # 添加 Cookie
            logger.info('添加 Cookie...')
            for item in cookie_string.split('; '):
                if '=' in item:
                    name, value = item.split('=', 1)
                    try:
                        self.driver.add_cookie({
                            'name': name,
                            'value': value,
                            'domain': '.tradingview.com',
                            'path': '/'
                        })
                    except:
                        pass

            # 访问目标页面
            logger.info(f'访问: {url}')
            self.driver.get(url)

            # 等待加载
            if wait_time > 0:
                logger.info(f'等待 {wait_time} 秒...')
                time.sleep(wait_time)

            # 截图
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            self.driver.save_screenshot(output_path)
            file_size = os.path.getsize(output_path)
            elapsed = time.time() - start_time

            logger.info(f'✅ 截图成功: {output_path} ({file_size / 1024:.1f} KB, {elapsed:.1f}s)')

            return {
                'success': True,
                'output_path': output_path,
                'file_size': file_size,
                'elapsed': elapsed
            }

        except Exception as e:
            logger.error(f'❌ 截图失败: {e}')
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            if self.driver:
                self.driver.quit()


# 便捷函数
def capture_screenshot(
    url: str,
    output_path: str,
    wait_time: int = 10,
    proxy_port: Optional[int] = None
) -> Dict[str, Any]:
    """
    快速截图

    Args:
        url: 目标 URL
        output_path: 输出路径
        wait_time: 等待时间
        proxy_port: 代理端口

    Returns:
        结果字典
    """
    helper = ScreenshotHelper(proxy_port=proxy_port)
    return helper.capture(url, output_path, wait_time)


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)

    # 测试 1: 基本截图
    print('测试 1: TradingView Widget')
    result = capture_screenshot(
        url='https://s.tradingview.com/widgetembed/?symbol=BINANCE%3ABTCUSDT&interval=15',
        output_path='../screenshot/test_quick.png',
        wait_time=10
    )
    print(f'结果: {result}\n')

    # 测试 2: 使用 Cookie
    if os.path.exists('./tradingview_cookies.json'):
        import json
        with open('./tradingview_cookies.json', 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)

        print('测试 2: 使用 Cookie')
        helper = ScreenshotHelper()
        result = helper.capture_with_cookie(
            url='https://cn.tradingview.com/chart/U1FY2qxO/',
            output_path='../screenshot/test_with_cookie.png',
            cookie_string=cookie_data['cookies'],
            wait_time=15
        )
        print(f'结果: {result}')
