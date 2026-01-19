#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用本地 OCR 识别 TradingView 图表中的 HAMA 指标

支持：
1. RapidOCR（推荐）- 速度快，准确率高，兼容性好
2. PaddleOCR - 完全免费，支持中英文
3. Tesseract OCR - 开源 OCR
4. EasyOCR - 易用的 OCR 库

完全免费，无需 API 密钥！
"""
import os
import re
import json
import base64
from typing import Dict, Any, Optional, List
from app.utils.logger import get_logger

# 可选依赖
try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth.stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None
    Stealth = None

logger = get_logger(__name__)


class HAMAOCRExtractor:
    """使用本地 OCR 识别 HAMA 指标"""

    def __init__(self, ocr_engine: str = 'rapidocr'):
        """
        初始化 OCR 提取器

        Args:
            ocr_engine: OCR 引擎类型 ('rapidocr', 'paddleocr', 'tesseract', 'easyocr')
        """
        self.ocr_engine = ocr_engine
        self.ocr = None
        self.cookies = self._load_cookies()

        # 初始化 OCR
        self._init_ocr()

    def _load_cookies(self) -> Optional[list]:
        """加载 TradingView Cookies"""
        cookie_file = os.path.join(
            os.path.dirname(__file__),
            '../../tradingview_cookies.json'
        )

        if not os.path.exists(cookie_file):
            return None

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            cookies_data = config.get('cookies')

            # 如果是字符串格式,转换为 Playwright 需要的数组格式
            if isinstance(cookies_data, str):
                logger.info("检测到字符串格式 cookie,正在转换为 Playwright 格式...")
                cookie_list = []
                for cookie in cookies_data.split(';'):
                    cookie = cookie.strip()
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookie_list.append({
                            'name': key,
                            'value': value,
                            'domain': '.tradingview.com',
                            'path': '/'
                        })
                logger.info(f"✅ 成功转换 {len(cookie_list)} 个 cookies")
                return cookie_list

            # 如果已经是数组格式,直接返回
            elif isinstance(cookies_data, list):
                return cookies_data

            return None

        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return None

    def _load_tradingview_config(self) -> Optional[Dict[str, str]]:
        """加载 TradingView 配置（账号密码）"""
        config_file = os.path.join(
            os.path.dirname(__file__),
            '../../file/tradingview.txt'
        )

        if not os.path.exists(config_file):
            logger.warning(f"TradingView 配置文件不存在: {config_file}")
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            config = {}
            for line in lines:
                line = line.strip()
                # 匹配格式: 账号 ：username 或 密码：password
                if '账号' in line or 'username' in line.lower():
                    # 提取账号
                    if '：' in line:
                        parts = line.split('：')
                        if len(parts) > 1:
                            config['username'] = parts[1].strip()
                    elif ':' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            config['username'] = parts[1].strip()
                elif '密码' in line or 'password' in line.lower():
                    # 提取密码
                    if '：' in line:
                        parts = line.split('：')
                        if len(parts) > 1:
                            config['password'] = parts[1].strip()
                    elif ':' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            config['password'] = parts[1].strip()

            if config.get('username') and config.get('password'):
                logger.info(f"✅ 成功加载 TradingView 配置: {config['username']}")
                return config
            else:
                logger.warning("TradingView 配置文件中缺少账号或密码")
                return None

        except Exception as e:
            logger.error(f"加载 TradingView 配置失败: {e}")
            return None

    def _init_ocr(self):
        """初始化 OCR 引擎"""
        if self.ocr_engine == 'rapidocr':
            try:
                from rapidocr_onnxruntime import RapidOCR
                logger.info("正在初始化 RapidOCR...")

                self.ocr = RapidOCR()
                logger.info("✅ RapidOCR 初始化成功")
            except ImportError:
                logger.warning("RapidOCR 未安装，尝试使用 PaddleOCR")
                self.ocr_engine = 'paddleocr'
                self._init_ocr()
            except Exception as e:
                logger.error(f"RapidOCR 初始化失败: {type(e).__name__}: {e}")
                self.ocr = None

        elif self.ocr_engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                logger.info("正在初始化 PaddleOCR (首次运行会下载模型文件,请耐心等待)...")

                # 使用更兼容的参数
                self.ocr = PaddleOCR(
                    lang='ch'
                )

                logger.info("✅ PaddleOCR 初始化成功")
            except ImportError:
                logger.warning("PaddleOCR 未安装，尝试使用 Tesseract")
                self.ocr_engine = 'tesseract'
                self._init_ocr()
            except Exception as e:
                logger.error(f"PaddleOCR 初始化失败: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")

                # 尝试使用最小参数重新初始化
                try:
                    logger.info("尝试使用最小参数重新初始化 PaddleOCR...")
                    self.ocr = PaddleOCR(lang='ch')
                    logger.info("✅ PaddleOCR 最小参数初始化成功")
                except Exception as e2:
                    logger.error(f"PaddleOCR 最小参数初始化也失败: {e2}")
                    self.ocr = None

        elif self.ocr_engine == 'tesseract':
            try:
                import pytesseract
                from PIL import Image
                self.ocr = pytesseract
                self.pil_image = Image
                logger.info("✅ Tesseract OCR 初始化成功")
            except ImportError:
                logger.warning("Tesseract 未安装，尝试使用 EasyOCR")
                self.ocr_engine = 'easyocr'
                self._init_ocr()
            except Exception as e:
                logger.error(f"Tesseract 初始化失败: {e}")
                self.ocr = None

        elif self.ocr_engine == 'easyocr':
            try:
                import easyocr
                self.ocr = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                logger.info("✅ EasyOCR 初始化成功")
            except ImportError:
                logger.error("EasyOCR 未安装")
                self.ocr = None
            except Exception as e:
                logger.error(f"EasyOCR 初始化失败: {e}")
                self.ocr = None

        if self.ocr is None:
            logger.warning("⚠️ 所有 OCR 引擎都初始化失败")

    def capture_chart(self, chart_url: str, output_path: str = '/tmp/tradingview_chart.png', browser_type: str = 'chromium') -> Optional[str]:
        """截取 TradingView 图表

        Args:
            chart_url: 图表 URL
            output_path: 输出路径
            browser_type: 浏览器类型 (chromium, firefox, webkit, brave)
        """
        proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')
        proxy_config = {'server': proxy_url, 'bypass': 'localhost,127.0.0.1'} if proxy_url else None

        # 调试日志
        logger.info(f"代理配置: proxy_url={repr(proxy_url)}, proxy_config={repr(proxy_config)}")

        try:
            with sync_playwright() as p:
                logger.info(f"启动浏览器 ({browser_type})，访问图表: {chart_url}")

                # 根据浏览器类型选择浏览器
                if browser_type == 'firefox':
                    browser = p.firefox.launch(
                        headless=True,
                        proxy=proxy_config if proxy_url else None
                    )
                    context = browser.new_context()
                    page = context.new_page()

                    # 应用 stealth 模式
                    stealth_config = Stealth()
                    stealth_config.apply_stealth_sync(page)

                    # 添加 cookies
                    if self.cookies:
                        context.add_cookies(self.cookies)

                elif browser_type == 'webkit':
                    browser = p.webkit.launch(
                        headless=True
                    )
                    context = browser.new_context()
                    page = context.new_page()

                    # 应用 stealth 模式
                    stealth_config = Stealth()
                    stealth_config.apply_stealth_sync(page)

                    # 添加 cookies
                    if self.cookies:
                        context.add_cookies(self.cookies)

                elif browser_type == 'brave':
                    # 使用 Brave 浏览器（需要安装 Brave 并配置 Playwright 使用其可执行文件）
                    # 使用独立的用户数据目录，避免与正在运行的 Brave 冲突
                    brave_path = os.path.join(os.path.dirname(__file__), '..', 'brave_profile')
                    os.makedirs(brave_path, exist_ok=True)

                    # Windows 常见 Brave 路径
                    brave_exe_paths = [
                        r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                        r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
                        os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe'),
                    ]
                    brave_exe = None
                    for path in brave_exe_paths:
                        if os.path.exists(path):
                            brave_exe = path
                            break

                    # 检查 Brave 是否安装
                    if not brave_exe:
                        logger.warning(f"未找到 Brave 浏览器，尝试过的路径: {brave_exe_paths}，回退到 Chromium")
                        browser_type = 'chromium'

                        # 构建 args
                        launch_args = ['--no-sandbox', '--disable-setuid-sandbox']
                        if proxy_url:
                            launch_args.append(f'--proxy-server={proxy_url}')

                        browser = p.chromium.launch(
                            headless=True,
                            proxy=proxy_config if proxy_url else None,
                            args=launch_args
                        )
                        context = browser.new_context()
                        page = context.new_page()

                        # 应用 stealth 模式
                        stealth_config = Stealth()
                        stealth_config.apply_stealth_sync(page)

                        # 添加 cookies
                        if self.cookies:
                            context.add_cookies(self.cookies)
                    else:
                        # 使用 Brave 浏览器（不使用持久化上下文，改用普通 launch）
                        logger.info(f"使用 Brave 浏览器: {brave_exe}")

                        # 构建 args
                        launch_args = ['--no-sandbox', '--disable-setuid-sandbox']
                        if proxy_url:
                            launch_args.append(f'--proxy-server={proxy_url}')

                        browser = p.chromium.launch(
                            headless=True,
                            executable_path=brave_exe,
                            proxy=proxy_config if proxy_url else None,
                            args=launch_args
                        )
                        context = browser.new_context()
                        page = context.new_page()

                        # 应用 stealth 模式
                        stealth_config = Stealth()
                        stealth_config.apply_stealth_sync(page)

                        # 添加 cookies
                        if self.cookies:
                            context.add_cookies(self.cookies)
                else:
                    # 默认使用 Chromium
                    # 构建 args
                    launch_args = ['--no-sandbox', '--disable-setuid-sandbox']
                    if proxy_url:
                        launch_args.append(f'--proxy-server={proxy_url}')

                    browser = p.chromium.launch(
                        headless=True,
                        proxy=proxy_config if proxy_url else None,
                        args=launch_args
                    )
                    context = browser.new_context()
                    page = context.new_page()

                    # 应用 stealth 模式
                    stealth_config = Stealth()
                    stealth_config.apply_stealth_sync(page)

                    # 添加 cookies
                    if self.cookies:
                        context.add_cookies(self.cookies)

                # 访问图表
                logger.info("正在加载图表...")
                page.goto(chart_url, timeout=120000, wait_until='load')

                # 检查是否需要登录
                logger.info("检查登录状态...")
                page.wait_for_timeout(3000)  # 等待页面加载

                try:
                    # 检查页面是否有登录按钮
                    login_button = page.query_selector('button[data-name="header-user-auth-start"]')
                    if login_button:
                        logger.info("未登录，开始自动登录...")

                        # 从配置文件读取账号密码
                        config = self._load_tradingview_config()
                        if config and config.get('username') and config.get('password'):
                            username = config['username']
                            password = config['password']

                            # 点击登录按钮
                            login_button.click()
                            page.wait_for_timeout(2000)

                            # 输入用户名
                            username_input = page.query_selector('input[name="username"]')
                            if username_input:
                                username_input.fill(username)
                                logger.info(f"输入用户名: {username}")

                            page.wait_for_timeout(1000)

                            # 输入密码
                            password_input = page.query_selector('input[name="password"]')
                            if password_input:
                                password_input.fill(password)
                                logger.info("输入密码")

                            page.wait_for_timeout(1000)

                            # 点击登录按钮
                            submit_button = page.query_selector('button[type="submit"]')
                            if submit_button:
                                submit_button.click()
                                logger.info("提交登录...")

                            # 等待登录完成
                            page.wait_for_timeout(5000)
                            logger.info("✅ 登录完成")
                        else:
                            logger.warning("未配置 TradingView 账号密码，跳过自动登录")
                    else:
                        logger.info("✅ 已登录")
                except Exception as e:
                    logger.warning(f"自动登录失败: {e}")

                # 等待图表渲染
                logger.info("等待图表渲染...")
                page.wait_for_timeout(50000)

                # 截图 - 截取页面右下角 HAMA 信息面板（精确定位）
                logger.info(f"截取图表右下角 HAMA 面板到: {output_path}")

                # 获取页面尺寸
                viewport_size = page.viewport_size
                page_width = viewport_size['width']
                page_height = viewport_size['height']

                # 计算截图区域: 精确定位到右下角 HAMA 指标面板
                # HAMA 信息面板是表格形式，通常在右下角
                # 只截取从"价格"到"最近交叉"的区域
                clip = {
                    'x': int(page_width * 0.72),   # 从页面 72% 处开始（右侧28%）
                    'y': int(page_height * 0.45),  # 从页面 45% 处开始（往上移动，从55%改为45%）
                    'width': int(page_width * 0.28),   # 截取右侧28%宽度
                    'height': int(page_height * 0.55)  # 截取底部55%高度（增加高度以包含完整区域）
                }

                logger.info(f"页面尺寸: {page_width}x{page_height}, 截图区域: x={clip['x']}, y={clip['y']}, width={clip['width']}, height={clip['height']}")
                page.screenshot(path=output_path, clip=clip)

                # 关闭浏览器
                browser.close()

                logger.info("✅ 图表截图完成")

                return output_path

        except Exception as e:
            logger.error(f"截取图表失败: {e}")
            return None

    def extract_hama_with_ocr(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        使用 OCR 从图片中提取 HAMA 指标

        Args:
            image_path: 图片路径

        Returns:
            HAMA 指标数据
        """
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return None

        if self.ocr is None:
            logger.error("OCR 引擎未初始化")
            return None

        try:
            # 根据不同引擎调用 OCR
            if self.ocr_engine == 'rapidocr':
                text_lines = self._ocr_with_rapidocr(image_path)
            elif self.ocr_engine == 'paddleocr':
                text_lines = self._ocr_with_paddleocr(image_path)
            elif self.ocr_engine == 'tesseract':
                text_lines = self._ocr_with_tesseract(image_path)
            elif self.ocr_engine == 'easyocr':
                text_lines = self._ocr_with_easyocr(image_path)
            else:
                logger.error(f"不支持的 OCR 引擎: {self.ocr_engine}")
                return None

            # 解析 OCR 结果
            hama_data = self._parse_ocr_result(text_lines)

            # 添加原始 OCR 文本到结果中
            hama_data['ocr_text'] = '\n'.join(text_lines)

            logger.info(f"✅ OCR 识别成功: {hama_data}")
            return hama_data

        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return None

    def _ocr_with_rapidocr(self, image_path: str) -> List[str]:
        """使用 RapidOCR 识别图片"""
        result = self.ocr(image_path)

        # RapidOCR 返回格式: (boxes, scores)
        # boxes 格式: [[[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence], ...]
        text_lines = []
        if result and len(result) >= 2 and result[0]:
            for item in result[0]:
                if len(item) >= 3:
                    text = item[1]
                    confidence = item[2]
                    if confidence > 0.5:  # 置信度阈值
                        text_lines.append(text)

        return text_lines

    def _ocr_with_paddleocr(self, image_path: str) -> List[str]:
        """使用 PaddleOCR 识别图片"""
        result = self.ocr.ocr(image_path)

        # 提取所有文字
        text_lines = []
        for line in result:
            if line and len(line) > 0:
                for word_info in line:
                    if word_info and len(word_info) > 1:
                        text = word_info[0]
                        confidence = word_info[1][1]
                        if confidence > 0.5:  # 置信度阈值
                            text_lines.append(text)

        return text_lines

    def _ocr_with_tesseract(self, image_path: str) -> List[str]:
        """使用 Tesseract 识别图片"""
        from PIL import Image

        image = Image.open(image_path)
        text = self.ocr.image_to_string(image)
        text_lines = text.split('\n')

        return [line.strip() for line in text_lines if line.strip()]

    def _ocr_with_easyocr(self, image_path: str) -> List[str]:
        """使用 EasyOCR 识别图片"""
        result = self.ocr.readtext(image_path)

        text_lines = []
        for detection in result:
            text = detection[1]
            confidence = detection[2]
            if confidence > 0.5:
                text_lines.append(text)

        return text_lines

    def _parse_ocr_result(self, text_lines: List[str]) -> Dict[str, Any]:
        """解析 OCR 结果，从右下角 HAMA 面板提取数据"""
        hama_value = None
        hama_color = 'gray'
        trend = 'neutral'
        current_price = None
        bollinger_status = None
        candle_ma_status = None
        last_cross_info = None

        # 合并所有文本，保持行结构
        full_text = ' '.join(text_lines)
        line_text = '\n'.join(text_lines)

        logger.debug(f"OCR 识别文本:\n{line_text}")

        # 1. 查找价格（"价格" 标签后的数值）
        # 新策略：先找到"价格"标签的位置，然后在其后面查找数值
        # 处理两种格式：
        #   格式1: "价格 3210.82" (同行，用空格分隔)
        #   格式2: "价格\n3210.82" (跨行，"价格"单独一行)

        # 方法1: 使用 line_text 查找 "价格" 后面的数值（跨行格式）
        lines = text_lines
        for i, line in enumerate(lines):
            # 检查这一行是否包含"价格"标签（中文或英文）
            line_lower = line.lower().strip()
            if '价格' in line or 'price' in line_lower:
                # 如果这一行只有"价格"标签（中文或英文），检查下一行
                # 使用更宽松的匹配：行内容只包含 "价格" 或 "price"（大小写不敏感）
                if (re.match(r'^\s*价格\s*$', line, re.IGNORECASE) or
                    re.match(r'^\s*price\s*$', line, re.IGNORECASE)):
                    # 检查下一行是否为数值
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        price_match = re.match(r'^([\d,]+\.?\d*)$', next_line)
                        if price_match:
                            try:
                                value = float(price_match.group(1).replace(',', ''))
                                if value >= 0.001:  # 合理价格
                                    current_price = value
                                    logger.info(f"✅ 从价格标签下一行识别到: {current_price}")
                                    break
                            except:
                                pass

                # 如果这一行包含"价格"和数值（格式: "价格 3210.82" 或 "price 3210.82"）
                if not current_price:
                    # 查找"价格"后面的数值（支持中文和英文）
                    price_pattern_cn = r'价格\s+([\d,]+\.?\d*)'
                    price_pattern_en = r'price\s+([\d,]+\.?\d*)'
                    match = re.search(price_pattern_cn, line) or re.search(price_pattern_en, line, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1).replace(',', ''))
                            if value >= 0.001:
                                current_price = value
                                logger.info(f"✅ 从价格标签同行识别到: {current_price}")
                                break
                        except:
                            pass

        # 方法2: 如果上面的方法没找到，使用原来的正则表达式（兼容性）
        if not current_price:
            price_patterns = [
                r'价格\s*[:：]?\s*([\d,]+\.?\d*)',
                r'price\s*[:：]?\s*([\d,]+\.?\d*)',  # 支持小写 price
                r'Price\s*[:：]?\s*([\d,]+\.?\d*)',
                r'\*价格\s*[:：]?\s*([\d,]+\.?\d*)',  # 添加：处理 *价格 格式
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)  # 大小写不敏感
                if matches:
                    for match in matches:
                        try:
                            value = float(match.replace(',', ''))
                            # 验证是否为合理价格（排除时间如 03, 24）
                            # 价格应该 >= 0.001 或者 >= 100
                            if value >= 0.001 and value != int(value):  # 排除整数时间
                                current_price = value
                                logger.info(f"✅ 从正则表达式识别到价格: {current_price}")
                                break
                            elif value >= 100:  # 大数值价格
                                current_price = value
                                logger.info(f"✅ 从正则表达式识别到大数值价格: {current_price}")
                                break
                        except:
                            continue
                if current_price:
                    break

        # 如果没有找到价格标签，尝试在 OCR 文本行中查找
        # 很多时候价格在"价格"标签的前一行或前两行
        if not current_price:
            lines = text_lines
            for i, line in enumerate(lines):
                # 如果这一行包含"价格"或"格"（部分匹配），检查前两行
                if '价格' in line or 'Price' in line.lower() or '格' in line:
                    # 检查前两行
                    for j in range(max(0, i-2), i):
                        check_line = lines[j].strip()
                        price_match = re.search(r'([\d,]+\.?\d*)', check_line)
                        if price_match:
                            try:
                                value = float(price_match.group(1).replace(',', ''))
                                # 合理的价格范围检查
                                if value >= 1000:  # BTC等大数值价格
                                    current_price = value
                                    logger.debug(f"从价格标签前{i-j}行识别到: {current_price}")
                                    break
                                elif value >= 0.001 and value < 1000:  # 小数值价格
                                    current_price = value
                                    logger.debug(f"从价格标签前{i-j}行识别到小数价格: {current_price}")
                                    break
                            except:
                                pass
                    if current_price:
                        break

        # 如果还是没有找到价格标签，尝试查找第一个合理数值
        # 优先匹配带小数点的价格（如 0.3939），然后匹配大数值（如 95000）
        if not current_price:
            # 先查找小数价格（0.001 - 1000，扩大范围）
            for match in re.finditer(r'(0\.\d+|[1-9]\d*\.\d+)', full_text):
                try:
                    value = float(match.group(1).replace(',', ''))
                    # 价格范围（0.001 - 1000），支持更多币种价格
                    if 0.001 <= value <= 1000:
                        current_price = value
                        logger.debug(f"识别小数价格: {current_price}")
                        break
                except:
                    continue

            # 如果没找到小数，再查找大数值（100 - 100000）
            if not current_price:
                for match in re.finditer(r'([1-9][\d,]+\.?\d*)', full_text):
                    try:
                        value = float(match.group(1).replace(',', ''))
                        # 合理的大数值价格范围（100 - 100000）
                        if 100 < value < 100000:
                            current_price = value
                            logger.debug(f"识别大数值价格: {current_price}")
                            break
                    except:
                        continue

        # 2. 查找 HAMA 状态（"HAMA状态" 标签后的文本）
        hama_status_patterns = [
            r'HAMA状态\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
            r'HAMA\s*Status\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
        ]

        for pattern in hama_status_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                status_text = matches[0].strip()
                logger.debug(f"识别 HAMA 状态: {status_text}")

                if '上涨' in status_text or 'bull' in status_text.lower():
                    hama_color = 'green'
                    trend = 'up'
                elif '下跌' in status_text or 'bear' in status_text.lower():
                    hama_color = 'red'
                    trend = 'down'
                elif '盘整' in status_text or 'neutral' in status_text.lower():
                    hama_color = 'gray'
                    trend = 'neutral'
                break

        # 3. 查找布林带状态（"状态" 标签后的文本）
        # 使用 line_text 保留换行，遍历所有匹配找到包含关键词的
        bb_status_patterns = [
            r'状态\s*[:：]?\s*([^\n]+)',
            r'Status\s*[:：]?\s*([^\n]+)',
        ]

        for pattern in bb_status_patterns:
            matches = re.findall(pattern, line_text)
            if matches:
                for status_text in matches:
                    status_text = status_text.strip()
                    # 验证是否包含有效的状态关键词
                    if '收缩' in status_text or 'squeeze' in status_text.lower():
                        bollinger_status = 'squeeze'
                    elif '扩张' in status_text or 'expansion' in status_text.lower():
                        bollinger_status = 'expansion'
                    elif '正常' in status_text or 'normal' in status_text.lower():
                        bollinger_status = 'normal'
                    if bollinger_status:
                        logger.debug(f"识别布林带状态: {bollinger_status}")
                        break
            if bollinger_status:
                break

        # 3.5 查找蜡烛/MA状态（"蜡烛/MA" 标签后的文本）
        candle_ma_patterns = [
            r'蜡烛/MA\s*[:：]?\s*([^\n]+)',
            r'昔烛/MA\s*[:：]?\s*([^\n]+)',  # OCR 可能识别错误
            r'Candle/MA\s*[:：]?\s*([^\n]+)',
        ]

        for pattern in candle_ma_patterns:
            matches = re.findall(pattern, line_text)
            if matches:
                candle_ma_status = matches[0].strip()
                logger.info(f"识别蜡烛/MA状态: {candle_ma_status}")
                break

        # 4. 查找最近交叉信息（"最近交叉" 标签后的文本）
        cross_patterns = [
            r'最近交叉\s*[:：]?\s*([^\n]+)',
            r'Last\s*Cross\s*[:：]?\s*([^\n]+)',
        ]

        for pattern in cross_patterns:
            matches = re.findall(pattern, line_text)  # 使用行文本保留换行
            if matches:
                last_cross_info = matches[0].strip()
                logger.debug(f"识别最近交叉: {last_cross_info}")

                # 从交叉信息中提取信号（涨/跌）
                if '涨' in last_cross_info or 'up' in last_cross_info.lower():
                    if not hama_color or hama_color == 'gray':  # 如果 HAMA 状态未识别，从交叉信息推断
                        hama_color = 'green'
                        trend = 'up'
                elif '跌' in last_cross_info or 'down' in last_cross_info.lower():
                    if not hama_color or hama_color == 'gray':
                        hama_color = 'red'
                        trend = 'down'
                break

        # 5. 如果仍未识别出趋势，尝试从全局文本中查找
        if trend == 'neutral':
            if '上涨趋势' in full_text or 'bullish' in full_text.lower():
                hama_color = 'green'
                trend = 'up'
            elif '下跌趋势' in full_text or 'bearish' in full_text.lower():
                hama_color = 'red'
                trend = 'down'
            elif '绿色' in full_text or 'green' in full_text.lower():
                hama_color = 'green'
                trend = 'up'
            elif '红色' in full_text or 'red' in full_text.lower():
                hama_color = 'red'
                trend = 'down'

        # 构建返回结果
        result = {
            'hama_value': current_price,  # 右下角面板显示价格作为主要值
            'hama_color': hama_color,
            'trend': trend,
            'current_price': current_price,
            'bollinger_status': bollinger_status,
            'candle_ma_status': candle_ma_status,  # 蜡烛/MA 状态
            'last_cross_info': last_cross_info,
            'hama_status': f"{trend}_trend",  # 兼容旧格式
            'ocr_engine': self.ocr_engine,
            'confidence': 'high',  # 右下角面板结构化文本，置信度高
            'source': 'ocr_panel',
            'raw_text': full_text[:500]  # 保存部分原始文本用于调试
        }

        logger.info(f"✅ 解析完成: color={hama_color}, trend={trend}, price={current_price}")
        return result


def extract_hama_with_ocr(
    chart_url: str = None,
    symbol: str = 'BTCUSDT',
    interval: str = '15',
    ocr_engine: str = 'rapidocr'
) -> Optional[Dict[str, Any]]:
    """
    使用 OCR 提取 HAMA 指标（便捷函数）

    Args:
        chart_url: 图表 URL
        symbol: 币种符号
        interval: 时间周期
        ocr_engine: OCR 引擎 ('rapidocr', 'paddleocr', 'tesseract', 'easyocr')

    Returns:
        HAMA 指标数据
    """
    extractor = HAMAOCRExtractor(ocr_engine=ocr_engine)

    # 如果没有提供 URL，使用默认 URL
    if not chart_url:
        chart_url = 'https://cn.tradingview.com/chart/U1FY2qxO/'

    # 1. 截取图表
    screenshot_path = f'/tmp/{symbol}_{interval}_chart.png'

    logger.info(f"开始 OCR 识别流程: {chart_url}")

    image_path = extractor.capture_chart(chart_url, screenshot_path)

    if not image_path:
        logger.error("图表截图失败")
        return None

    # 2. 使用 OCR 识别
    hama_data = extractor.extract_hama_with_ocr(image_path)

    if hama_data:
        # 添加元数据
        hama_data['chart_url'] = chart_url
        hama_data['symbol'] = symbol
        hama_data['interval'] = interval
        hama_data['screenshot_path'] = screenshot_path

    return hama_data


if __name__ == '__main__':
    # 测试代码
    print("="*60)
    print("HAMA OCR 识别测试 (RapidOCR)")
    print("="*60)

    # 测试 OCR 识别
    result = extract_hama_with_ocr(
        chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
        symbol='ETHUSD',
        interval='15',
        ocr_engine='rapidocr'
    )

    if result:
        print("\n" + "="*60)
        print("识别结果:")
        print("="*60)
        print(f"HAMA 数值: {result.get('hama_value')}")
        print(f"HAMA 颜色: {result.get('hama_color')}")
        print(f"趋势: {result.get('trend')}")
        print(f"当前价格: {result.get('current_price')}")
        print(f"OCR 引擎: {result.get('ocr_engine')}")
        print(f"置信度: {result.get('confidence')}")

        bb = result.get('bollinger_bands', {})
        if any(bb.values()):
            print(f"\n布林带:")
            print(f"  上轨: {bb.get('upper')}")
            print(f"  中轨: {bb.get('middle')}")
            print(f"  下轨: {bb.get('lower')}")

        print(f"\n原始文本（前500字符）:")
        print(result.get('raw_text', ''))
        print(f"\n截图路径: {result.get('screenshot_path')}")
        print("="*60)
    else:
        print("❌ 识别失败")
        print("\n请确保已安装 RapidOCR:")
        print("pip install rapidocr_onnxruntime")
        print("\n或使用其他 OCR 引擎:")
        print("pip install paddleocr paddlepaddle  # PaddleOCR")
        print("pip install easyocr  # EasyOCR")
