#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用大模型视觉能力识别 TradingView 图表中的 HAMA 指标

支持：
1. Playwright 截取图表
2. 使用 OpenRouter GPT-4o 或 Claude 3.5 Sonnet 识别图表
3. 提取 HAMA 指标数值和颜色
"""
import os
import base64
import json
from typing import Dict, Any, Optional
import requests
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


class HAMAVisionExtractor:
    """使用大模型视觉能力提取 HAMA 指标"""

    def __init__(self):
        """初始化提取器"""
        # OpenRouter API 配置
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o')
        self.api_url = 'https://openrouter.ai/api/v1/chat/completions'

        if not self.api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY 未设置，视觉识别功能将不可用")

        # Cookie 配置
        self.cookies = self._load_cookies()

        logger.info(f"HAMA 视觉提取器初始化: model={self.model}")

    def _load_cookies(self) -> Optional[list]:
        """加载 TradingView Cookies"""
        cookie_file = os.path.join(os.path.dirname(__file__), '../../tradingview_cookies.json')

        if not os.path.exists(cookie_file):
            logger.warning(f"Cookie 文件不存在: {cookie_file}")
            return None

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('cookies', [])
        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return None

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def capture_chart(self, chart_url: str, output_path: str = '/tmp/tradingview_chart.png') -> Optional[str]:
        """
        截取 TradingView 图表

        Args:
            chart_url: 图表 URL
            output_path: 输出图片路径

        Returns:
            图片路径（成功）或 None（失败）
        """
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
                    logger.info(f"✅ 已添加 {len(self.cookies)} 个 cookies")

                # 访问图表
                logger.info("正在加载图表...")
                page.goto(chart_url, timeout=120000, wait_until='load')

                # 等待图表渲染
                logger.info("等待图表渲染...")
                page.wait_for_timeout(50000)

                # 截图
                logger.info(f"截取图表到: {output_path}")
                page.screenshot(path=output_path, full_page=False)

                browser.close()
                logger.info("✅ 图表截图完成")

                return output_path

        except Exception as e:
            logger.error(f"截取图表失败: {e}")
            return None

    def extract_hama_from_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        使用大模型从图片中提取 HAMA 指标

        Args:
            image_path: 图片路径

        Returns:
            HAMA 指标数据
        """
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY 未设置，无法使用视觉识别")
            return None

        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return None

        try:
            # 编码图片
            base64_image = self._encode_image(image_path)

            # 构建提示词
            prompt = """请分析这张 TradingView 图表截图，提取 HAMA 指标的数据。

请识别并提取以下信息（以 JSON 格式返回）：
1. HAMA 数值（通常是图表左上角显示的价格，如 "3,418.03"）
2. HAMA 颜色（green/red/gray，对应上涨/下跌/中性）
3. 趋势方向（up/down/neutral）
4. 当前价格（如果可见）
5. 布林带数值（如果可见）

请严格按照以下 JSON 格式返回：
```json
{
  "hama_value": "数值，如 3418.03",
  "hama_color": "green 或 red 或 gray",
  "trend": "up 或 down 或 neutral",
  "current_price": "当前价格",
  "bollinger_bands": {
    "upper": "上轨数值",
    "middle": "中轨数值",
    "lower": "下轨数值"
  },
  "confidence": "high 或 medium 或 low",
  "note": "如果无法识别某些数据，请在此说明"
}
```

注意：
- HAMA 数值通常在图表左上角图例区域
- 绿色表示上涨，红色表示下跌
- 如果某些数据不可见或不清晰，将对应字段设为 null"""

            logger.info(f"调用大模型分析图片: {image_path}")

            # 调用 OpenRouter API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://quantdinger.com',
                'X-Title': 'QuantDinger'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': prompt
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/png;base64,{base64_image}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 1000,
                'temperature': 0.1  # 降低温度以获得更准确的识别
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                # 提取回复内容
                content = result['choices'][0]['message']['content']

                logger.info(f"大模型回复: {content}")

                # 解析 JSON
                # 尝试提取 JSON 代码块
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)

                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 如果没有代码块，尝试直接解析
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        logger.error("无法从回复中提取 JSON")
                        return None

                # 解析 JSON
                hama_data = json.loads(json_str)

                # 清理和转换数据
                cleaned_data = self._clean_hama_data(hama_data)

                logger.info(f"✅ 成功识别 HAMA 数据: {cleaned_data}")

                return cleaned_data

            else:
                logger.error(f"API 调用失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"视觉识别失败: {e}")
            return None

    def _clean_hama_data(self, raw_data: Dict) -> Dict[str, Any]:
        """清理和转换 HAMA 数据"""
        try:
            # 提取数值（去除逗号等格式字符）
            def extract_number(value):
                if value is None or isinstance(value, (int, float)):
                    return value
                if isinstance(value, str):
                    # 移除逗号、空格等
                    cleaned = value.replace(',', '').strip()
                    try:
                        return float(cleaned)
                    except:
                        return None
                return None

            hama_value = extract_number(raw_data.get('hama_value'))
            current_price = extract_number(raw_data.get('current_price'))

            # 布林带
            bb = raw_data.get('bollinger_bands', {})
            bollinger_bands = {
                'upper': extract_number(bb.get('upper')),
                'middle': extract_number(bb.get('middle')),
                'lower': extract_number(bb.get('lower'))
            }

            # 颜色标准化
            color_map = {
                'green': 'green',
                'red': 'red',
                'gray': 'gray',
                'grey': 'gray',
                '上涨': 'green',
                '下跌': 'red',
                '中性': 'gray'
            }
            color = raw_data.get('hama_color', 'gray').lower()
            hama_color = color_map.get(color, 'gray')

            # 趋势标准化
            trend_map = {
                'up': 'up',
                'down': 'down',
                'neutral': 'neutral',
                '上涨': 'up',
                '下跌': 'down',
                '中性': 'neutral'
            }
            trend = raw_data.get('trend', 'neutral').lower()
            hama_trend = trend_map.get(trend, 'neutral')

            return {
                'hama_value': hama_value,
                'hama_color': hama_color,
                'trend': hama_trend,
                'current_price': current_price,
                'bollinger_bands': bollinger_bands,
                'confidence': raw_data.get('confidence', 'unknown'),
                'note': raw_data.get('note', ''),
                'raw_response': raw_data
            }

        except Exception as e:
            logger.error(f"清理数据失败: {e}")
            return {
                'hama_value': None,
                'hama_color': 'gray',
                'trend': 'neutral',
                'error': str(e)
            }


def extract_hama_with_vision(
    chart_url: str = None,
    symbol: str = 'BTCUSDT',
    interval: str = '15'
) -> Optional[Dict[str, Any]]:
    """
    使用视觉识别提取 HAMA 指标（便捷函数）

    Args:
        chart_url: TradingView 图表 URL（如果为 None，使用默认 URL）
        symbol: 币种符号
        interval: 时间周期

    Returns:
        HAMA 指标数据
    """
    extractor = HAMAVisionExtractor()

    # 如果没有提供 URL，使用默认 URL
    if not chart_url:
        chart_url = 'https://cn.tradingview.com/chart/U1FY2qxO/'

    # 1. 截取图表
    screenshot_path = f'/tmp/{symbol}_{interval}_chart.png'

    logger.info(f"开始视觉识别流程: {chart_url}")

    image_path = extractor.capture_chart(chart_url, screenshot_path)

    if not image_path:
        logger.error("图表截图失败")
        return None

    # 2. 使用大模型识别
    hama_data = extractor.extract_hama_from_image(image_path)

    if hama_data:
        # 添加元数据
        hama_data['source'] = 'vision'
        hama_data['chart_url'] = chart_url
        hama_data['symbol'] = symbol
        hama_data['interval'] = interval
        hama_data['screenshot_path'] = screenshot_path

    return hama_data


if __name__ == '__main__':
    # 测试代码
    print("="*60)
    print("HAMA 视觉识别测试")
    print("="*60)

    # 测试视觉识别
    result = extract_hama_with_vision(
        chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
        symbol='ETHUSD',
        interval='15'
    )

    if result:
        print("\n" + "="*60)
        print("识别结果:")
        print("="*60)
        print(f"HAMA 数值: {result.get('hama_value')}")
        print(f"HAMA 颜色: {result.get('hama_color')}")
        print(f"趋势: {result.get('trend')}")
        print(f"当前价格: {result.get('current_price')}")
        print(f"置信度: {result.get('confidence')}")

        bb = result.get('bollinger_bands', {})
        if any(bb.values()):
            print(f"\n布林带:")
            print(f"  上轨: {bb.get('upper')}")
            print(f"  中轨: {bb.get('middle')}")
            print(f"  下轨: {bb.get('lower')}")

        if result.get('note'):
            print(f"\n备注: {result.get('note')}")

        print(f"\n截图路径: {result.get('screenshot_path')}")
        print("="*60)
    else:
        print("❌ 识别失败")
