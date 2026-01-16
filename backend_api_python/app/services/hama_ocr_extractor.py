#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用本地 OCR 识别 TradingView 图表中的 HAMA 指标

支持：
1. PaddleOCR（推荐）- 完全免费，支持中英文
2. Tesseract OCR - 开源 OCR
3. EasyOCR - 易用的 OCR 库

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

    def __init__(self, ocr_engine: str = 'paddleocr'):
        """
        初始化 OCR 提取器

        Args:
            ocr_engine: OCR 引擎类型 ('paddleocr', 'tesseract', 'easyocr')
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
            return config.get('cookies', [])
        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return None

    def _init_ocr(self):
        """初始化 OCR 引擎"""
        if self.ocr_engine == 'paddleocr':
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

    def capture_chart(self, chart_url: str, output_path: str = '/tmp/tradingview_chart.png') -> Optional[str]:
        """截取 TradingView 图表"""
        proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')
        proxy_config = {'server': proxy_url, 'bypass': 'localhost,127.0.0.1'} if proxy_url else None

        try:
            with sync_playwright() as p:
                logger.info(f"启动浏览器，访问图表: {chart_url}")

                browser = p.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        f'--proxy-server={proxy_url}' if proxy_url else ''
                    ]
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

                # 等待图表渲染
                logger.info("等待图表渲染...")
                page.wait_for_timeout(50000)

                # 截图 - 截取页面右侧居中区域
                logger.info(f"截取图表右侧区域到: {output_path}")

                # 获取页面尺寸
                viewport_size = page.viewport_size
                page_width = viewport_size['width']
                page_height = viewport_size['height']

                # 计算截图区域: 右侧 60% 的宽度,垂直居中
                # TradingView 右侧面板通常显示详细的指标数据
                clip = {
                    'x': int(page_width * 0.4),  # 从页面 40% 处开始(右侧60%)
                    'y': 0,                     # 从顶部开始
                    'width': int(page_width * 0.6),  # 截取右侧60%宽度
                    'height': page_height       # 全屏高度
                }

                logger.info(f"页面尺寸: {page_width}x{page_height}, 截图区域: x={clip['x']}, y={clip['y']}, width={clip['width']}, height={clip['height']}")
                page.screenshot(path=output_path, clip=clip)

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
            if self.ocr_engine == 'paddleocr':
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

            logger.info(f"✅ OCR 识别成功: {hama_data}")
            return hama_data

        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return None

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
        """解析 OCR 结果，提取 HAMA 数据"""
        hama_value = None
        hama_color = 'gray'
        trend = 'neutral'
        current_price = None
        bollinger_bands = {'upper': None, 'middle': None, 'lower': None}

        # 合并所有文本
        full_text = ' '.join(text_lines)

        # 1. 查找 HAMA 数值（格式：3,418.03 或 3418.03）
        hama_patterns = [
            r'HAMA.*?([\d,]+\.?\d*)',
            r'([1-9][\d,]+\.?\d*)',  # 大数值
        ]

        for pattern in hama_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # 转换为浮点数
                for match in matches:
                    try:
                        value = float(match.replace(',', ''))
                        # 合理的价格范围（100 - 100000）
                        if 100 < value < 100000:
                            hama_value = value
                            break
                    except:
                        continue
                if hama_value:
                    break

        # 2. 查找颜色信息
        if 'green' in full_text.lower() or '上涨' in full_text or '▲' in full_text or 'up' in full_text.lower():
            hama_color = 'green'
            trend = 'up'
        elif 'red' in full_text.lower() or '下跌' in full_text or '▼' in full_text or 'down' in full_text.lower():
            hama_color = 'red'
            trend = 'down'

        # 3. 查找当前价格（通常在图表顶部）
        price_patterns = [
            r'(\d+[,.]\d+)\s*▲',
            r'(\d+[,.]\d+)\s*▼',
            r'(?:ETH|BTC|USDT).*?(\d+[,.]\d+)',
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                try:
                    current_price = float(matches[0].replace(',', ''))
                    break
                except:
                    continue

        # 4. 查找布林带数值
        bb_patterns = [
            r'上轨[：:]\s*([\d,]+\.?\d*)',
            r'Upper[：:]\s*([\d,]+\.?\d*)',
            r'下轨[：:]\s*([\d,]+\.?\d*)',
            r'Lower[：:]\s*([\d,]+\.?\d*)',
            r'中轨[：:]\s*([\d,]+\.?\d*)',
            r'Basis[：:]\s*([\d,]+\.?\d*)',
        ]

        for pattern in bb_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    if '上轨' in pattern or 'Upper' in pattern:
                        bollinger_bands['upper'] = value
                    elif '下轨' in pattern or 'Lower' in pattern:
                        bollinger_bands['lower'] = value
                    elif '中轨' in pattern or 'Basis' in pattern:
                        bollinger_bands['middle'] = value
                except:
                    continue

        return {
            'hama_value': hama_value,
            'hama_color': hama_color,
            'trend': trend,
            'current_price': current_price,
            'bollinger_bands': bollinger_bands,
            'ocr_engine': self.ocr_engine,
            'confidence': 'medium',  # OCR 的置信度通常中等
            'source': 'ocr',
            'raw_text': full_text[:500]  # 保存部分原始文本用于调试
        }


def extract_hama_with_ocr(
    chart_url: str = None,
    symbol: str = 'BTCUSDT',
    interval: str = '15',
    ocr_engine: str = 'paddleocr'
) -> Optional[Dict[str, Any]]:
    """
    使用 OCR 提取 HAMA 指标（便捷函数）

    Args:
        chart_url: 图表 URL
        symbol: 币种符号
        interval: 时间周期
        ocr_engine: OCR 引擎 ('paddleocr', 'tesseract', 'easyocr')

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
    print("HAMA OCR 识别测试")
    print("="*60)

    # 测试 OCR 识别
    result = extract_hama_with_ocr(
        chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
        symbol='ETHUSD',
        interval='15',
        ocr_engine='paddleocr'
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
        print("\n请确保已安装 PaddleOCR:")
        print("pip install paddleocr paddlepaddle")
