#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA BrowserAct 监控服务
使用 BrowserAct 框架实现智能化的 TradingView 监控
支持直接数据提取、自动登录、Cloudflare绕过

主要优势:
- 直接提取结构化数据，无需OCR
- 自动处理登录和验证
- 多账号并行监控
- 智能反检测
"""

import time
import json
import subprocess
import threading
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 全局单例
_browseract_monitor_instance = None


def get_browseract_monitor(redis_client=None, cache_ttl: int = 900, use_sqlite: bool = True):
    """
    获取 BrowserAct 监控器单例

    Args:
        redis_client: Redis 客户端
        cache_ttl: 缓存过期时间（秒）
        use_sqlite: 是否使用 SQLite (默认 True)

    Returns:
        HamaBrowserActMonitor 实例
    """
    global _browseract_monitor_instance

    if _browseract_monitor_instance is None:
        _browseract_monitor_instance = HamaBrowserActMonitor(redis_client, cache_ttl, use_sqlite)

    return _browseract_monitor_instance


class HamaBrowserActMonitor:
    """HAMA BrowserAct 智能监控器"""

    def __init__(self, redis_client=None, cache_ttl: int = 900, use_sqlite: bool = True, enable_email: bool = True):
        """
        初始化 BrowserAct 监控器

        Args:
            redis_client: Redis 客户端
            cache_ttl: 缓存过期时间（秒）
            use_sqlite: 是否使用 SQLite (默认 True)
            enable_email: 是否启用邮件通知 (默认 True)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.prefix = "hama:browseract:"
        self.is_monitoring = False
        self.monitor_thread = None
        self.symbols = []  # 监控币种列表
        self.interval = 300  # BrowserAct模式使用更短的间隔（5分钟）
        self.last_monitor_time = None
        self.enable_email = enable_email

        # BrowserAct 配置
        self.browseract_available = self._check_browseract()
        self.browseract_cmd = self._get_browseract_cmd()
        self.browser_profiles = {}  # 多浏览器配置

        # 并发配置
        self.max_workers = 5  # BrowserAct支持更高并发

        # SQLite 支持
        self.use_sqlite = use_sqlite
        self.sqlite_conn = None
        if use_sqlite:
            self._init_sqlite()

        # 初始化邮件通知器
        if self.enable_email:
            try:
                from app.services.hama_email_notifier import get_hama_email_notifier
                self.email_notifier = get_hama_email_notifier()
                logger.info("邮件通知器初始化成功")
            except Exception as e:
                logger.warning(f"邮件通知器初始化失败: {e}")
                self.email_notifier = None
        else:
            self.email_notifier = None

        # 记录上次状态
        self.last_states = self._load_last_states_from_db()

        if self.browseract_available:
            logger.info("✅ BrowserAct监控器初始化成功")
        else:
            logger.warning("⚠️  BrowserAct未安装，将使用降级方案")

    def _check_browseract(self) -> bool:
        """检查 BrowserAct CLI 是否可用"""
        try:
            result = subprocess.run(
                ['browser-act', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"BrowserAct版本: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("BrowserAct CLI未找到，将使用降级方案")
        except Exception as e:
            logger.warning(f"BrowserAct检查失败: {e}")
        return False

    def _get_browseract_cmd(self) -> str:
        """获取 BrowserAct 命令路径"""
        if self.browseract_available:
            return 'browser-act'
        return None

    def _init_sqlite(self):
        """初始化 SQLite 数据库"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            self.sqlite_conn = sqlite3.connect(db_path)
            self.sqlite_conn.row_factory = sqlite3.Row

            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hama_browseract_cache (
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    hama_trend VARCHAR(10),
                    hama_color VARCHAR(10),
                    hama_value DECIMAL(20, 8),
                    price DECIMAL(20, 8),
                    data_source VARCHAR(50),
                    raw_data TEXT,
                    extraction_method VARCHAR(20),
                    email_sent INTEGER DEFAULT 0,
                    email_sent_at TIMESTAMP NULL,
                    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, timeframe)
                )
            ''')

            # 创建邮件发送记录表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_send_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    email_type VARCHAR(50) NOT NULL,
                    hama_color VARCHAR(10),
                    hama_trend VARCHAR(10),
                    hama_value DECIMAL(20, 8),
                    price DECIMAL(20, 8),
                    cross_type VARCHAR(20),
                    recipients TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    screenshot_path VARCHAR(255),
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_log_symbol
                ON email_send_log(symbol)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_log_sent_at
                ON email_send_log(sent_at)
            ''')

            self.sqlite_conn.commit()
            logger.info("BrowserAct SQLite表初始化完成（包含邮件日志表）")
        except Exception as e:
            logger.error(f"SQLite初始化失败: {e}")

    def _load_last_states_from_db(self) -> Dict[str, Any]:
        """从数据库加载上次状态"""
        states = {}
        if not self.sqlite_conn:
            return states

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                SELECT symbol, hama_trend, hama_color, hama_value
                FROM hama_browseract_cache
            ''')
            for row in cursor.fetchall():
                states[row['symbol']] = {
                    'trend': row['hama_trend'],
                    'color': row['hama_color'],
                    'value': float(row['hama_value']) if row['hama_value'] else 0
                }
            logger.info(f"从数据库加载了 {len(states)} 个币种的历史状态")
        except Exception as e:
            logger.warning(f"加载历史状态失败: {e}")

        return states

    def extract_hama_data_direct(self, symbol: str, timeframe: str = '15m') -> Optional[Dict[str, Any]]:
        """
        使用 BrowserAct 直接提取 HAMA 数据

        Args:
            symbol: 交易对符号 (如 BTCUSDT)
            timeframe: 时间周期

        Returns:
            提取的数据字典，失败返回 None
        """
        if not self.browseract_available:
            logger.warning(f"BrowserAct不可用，无法提取 {symbol} 数据")
            return None

        try:
            # TradingView URL 构造
            tradingview_url = f"https://cn.tradingview.com/chart/?symbol=BINANCE%3A{symbol}"

            logger.info(f"🚀 使用 BrowserAct 提取 {symbol} HAMA 数据...")

            # 方法1: 尝试使用 stealth-extract
            cmd = [
                self.browseract_cmd,
                'stealth-extract',
                tradingview_url,
                '--content-type', 'markdown'
            ]

            logger.info(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'HTTP_PROXY': 'http://127.0.0.1:7890', 'HTTPS_PROXY': 'http://127.0.0.1:7890'}
            )

            if result.returncode == 0:
                logger.info(f"✅ BrowserAct 提取 {symbol} 成功")
                try:
                    if result.stdout.strip():
                        # 解析 markdown 内容
                        content = result.stdout
                        return self._parse_browseract_response(content, symbol)
                    else:
                        logger.warning(f"BrowserAct 返回空响应")
                        return None
                except Exception as e:
                    logger.error(f"解析 {symbol} BrowserAct响应失败: {e}")
                    return None
            else:
                # 方法2: 尝试使用浏览器会话方式
                logger.info(f"stealth-extract 失败，尝试浏览器会话方式...")
                return self._extract_via_browser_session(symbol, timeframe)

        except subprocess.TimeoutExpired:
            logger.error(f"BrowserAct提取 {symbol} 超时")
            return self._extract_via_browser_session(symbol, timeframe)
        except Exception as e:
            logger.error(f"BrowserAct提取 {symbol} 异常: {e}")
            return self._extract_via_browser_session(symbol, timeframe)

    def _extract_via_browser_session(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        使用浏览器会话方式提取数据

        Args:
            symbol: 交易对符号
            timeframe: 时间周期

        Returns:
            提取的数据字典
        """
        session_name = None
        try:
            import uuid
            from app.config.browseract_config import BrowserActConfig

            # 获取配置的浏览器
            browser_config = BrowserActConfig.get_browser_config()
            browser_id = browser_config['id']
            browser_type = browser_config.get('type', 'chrome')
            is_headless = browser_config.get('headless', True)

            session_name = f"hama_{symbol}_{uuid.uuid4().hex[:8]}"
            tradingview_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}"

            logger.info(f"🔄 使用浏览器会话方式提取 {symbol} 数据...")
            logger.info(f"📱 浏览器: {browser_config['name']} ({'无头模式' if is_headless else '有窗口'})")

            # 清理旧会话
            self._cleanup_old_sessions(browser_id)

            # Chrome浏览器不使用代理
            if browser_type == 'chrome':
                env_vars = {k: v for k, v in os.environ.items() if k not in ['HTTP_PROXY', 'HTTPS_PROXY']}
            else:
                env_vars = os.environ.copy()

            # 打开浏览器会话
            cmd_open = [
                self.browseract_cmd,
                '--session', session_name,
                'browser', 'open', browser_id,
                tradingview_url
            ]

            result = subprocess.run(
                cmd_open,
                capture_output=True,
                text=False,  # 使用bytes避免编码问题
                timeout=60,
                env=env_vars
            )

            if result.returncode != 0:
                stderr_output = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
                logger.error(f"浏览器会话打开失败: {stderr_output}")
                return None

            logger.info(f"浏览器会话已打开，等待页面加载...")

            # 等待页面加载
            import time
            time.sleep(12)  # 等待页面完全加载

            # 获取页面markdown内容
            cmd_extract = [
                self.browseract_cmd,
                '--session', session_name,
                'get', 'markdown'
            ]

            result = subprocess.run(
                cmd_extract,
                capture_output=True,
                text=False,  # 使用bytes
                timeout=30,
                env=env_vars
            )

            # 关闭会话
            try:
                subprocess.run(
                    [self.browseract_cmd, '--session', session_name, 'session', 'close'],
                    capture_output=True,
                    timeout=10,
                    env=env_vars
                )
            except:
                pass  # 忽略关闭失败

            if result.returncode == 0 and result.stdout:
                content = result.stdout.decode('utf-8', errors='replace')
                if content.strip():
                    logger.info(f"✅ 浏览器会话提取成功，内容长度: {len(content)}")
                    return self._parse_browseract_response(content, symbol)
                else:
                    logger.warning(f"浏览器会话提取内容为空")
                    return None
            else:
                stderr_output = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
                logger.warning(f"浏览器会话提取失败: {stderr_output}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"浏览器会话提取 {symbol} 超时")
            if session_name:
                self._close_session_safe(session_name)
            return None
        except Exception as e:
            logger.error(f"浏览器会话提取异常: {e}")
            if session_name:
                self._close_session_safe(session_name)
            return None

    def _cleanup_old_sessions(self, browser_id: str):
        """清理指定浏览器的旧会话"""
        try:
            result = subprocess.run(
                [self.browseract_cmd, 'session', 'list'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f'browser_id={browser_id}' in line:
                        # 提取会话名称
                        parts = line.split()
                        if parts and '=' in parts[0]:
                            session_name = parts[0].split('=')[1]
                            self._close_session_safe(session_name)
        except:
            pass  # 忽略清理失败

    def _close_session_safe(self, session_name: str):
        """安全关闭会话"""
        try:
            subprocess.run(
                [self.browseract_cmd, 'session', 'close', session_name],
                capture_output=True,
                timeout=10
            )
        except:
            pass

    def _parse_browseract_response(self, content: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        解析 BrowserAct 响应内容

        Args:
            content: BrowserAct 返回的内容
            symbol: 交易对符号

        Returns:
            解析后的HAMA数据
        """
        try:
            logger.info(f"🔍 解析 {symbol} 的 BrowserAct 响应...")

            hama_data = {
                'symbol': symbol,
                'timeframe': '15m',
                'hama_trend': None,
                'hama_color': None,
                'hama_value': None,
                'price': None,
                'trend': None,
                'color': None,
                'current_price': None,
                'bollinger_status': None,
                'candle_ma_status': None,
                'last_cross_info': None,
                'last_cross_time': None,
                'data_source': 'browseract_direct',
                'extraction_method': 'browser_session',
                'raw_data': content[:1000] if content else ''  # 保存前1000字符
            }

            # 分析内容查找 HAMA 相关信息
            content_upper = content.upper()

            # 检测趋势关键词
            if any(keyword in content_upper for keyword in ['GOLDEN CROSS', '金叉', 'BULLISH', '买入信号', 'UP TREND']):
                hama_data['hama_trend'] = '金叉'
                hama_data['trend'] = 'up'
                hama_data['hama_color'] = 'green'
                hama_data['color'] = 'green'
            elif any(keyword in content_upper for keyword in ['DEATH CROSS', '死叉', 'BEARISH', '卖出信号', 'DOWN TREND']):
                hama_data['hama_trend'] = '死叉'
                hama_data['trend'] = 'down'
                hama_data['hama_color'] = 'red'
                hama_data['color'] = 'red'
            else:
                hama_data['hama_trend'] = '中性'
                hama_data['trend'] = 'neutral'
                hama_data['hama_color'] = 'gray'
                hama_data['color'] = 'gray'

            # 尝试提取价格信息
            import re
            price_patterns = [
                r'(\d+\.?\d*)\s*USDT',
                r'[\"\']price[\"\']:\s*[\"\']?(\d+\.?\d*)',
                r'[\"\']last[\"\']:\s*[\"\']?(\d+\.?\d*)',
                r'BINANCE.*?(\d+\.?\d*)'
            ]

            for pattern in price_patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        price = float(match.group(1))
                        # 合理价格范围检查 (加密货币通常 > 0.01)
                        if 0.01 < price < 1000000:
                            hama_data['price'] = price
                            hama_data['current_price'] = price
                            logger.info(f"✅ 提取到价格: {price}")
                            break
                    except (ValueError, IndexError):
                        continue

            logger.info(f"✅ {symbol} BrowserAct 数据解析完成")
            logger.info(f"   趋势: {hama_data['hama_trend']}")
            logger.info(f"   颜色: {hama_data['hama_color']}")
            logger.info(f"   价格: {hama_data['price']}")

            return hama_data

        except Exception as e:
            logger.error(f"解析BrowserAct响应失败: {e}")
            import traceback
            logger.debug(f"详细错误: {traceback.format_exc()}")
            return None

    def _parse_tradingview_data(self, raw_data: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """
        解析 TradingView 提取的数据

        Args:
            raw_data: BrowserAct提取的原始数据
            symbol: 交易对符号

        Returns:
            解析后的HAMA数据
        """
        try:
            logger.info(f"🔍 开始解析 {symbol} 的 BrowserAct 数据...")

            hama_data = {
                'symbol': symbol,
                'timeframe': '15m',
                'hama_trend': None,
                'hama_color': None,
                'hama_value': None,
                'price': None,
                'trend': None,
                'color': None,
                'current_price': None,
                'bollinger_status': None,
                'candle_ma_status': None,
                'last_cross_info': None,
                'last_cross_time': None,
                'data_source': 'browseract_direct',
                'extraction_method': 'dom_extraction',
                'raw_data': json.dumps(raw_data, ensure_ascii=False)
            }

            # 尝试多种方式提取HAMA数据
            # 方法1: 检查是否包含页面文本内容
            if isinstance(raw_data, dict):
                # 检查页面内容
                page_content = raw_data.get('content', '') or raw_data.get('text', '') or str(raw_data)

                # 尝试从页面文本中提取HAMA相关信息
                if 'HAMA' in page_content or 'Hull' in page_content:
                    logger.info(f"✅ 在页面中找到HAMA相关内容")

                    # 简单的关键词匹配来检测趋势
                    if any(keyword in page_content for keyword in ['金叉', '向上', '买入', 'bullish']):
                        hama_data['hama_trend'] = '金叉'
                        hama_data['trend'] = 'up'
                        hama_data['hama_color'] = 'green'
                        hama_data['color'] = 'green'
                    elif any(keyword in page_content for keyword in ['死叉', '向下', '卖出', 'bearish']):
                        hama_data['hama_trend'] = '死叉'
                        hama_data['trend'] = 'down'
                        hama_data['hama_color'] = 'red'
                        hama_data['color'] = 'red'
                    else:
                        hama_data['hama_trend'] = '中性'
                        hama_data['trend'] = 'neutral'
                        hama_data['hama_color'] = 'gray'
                        hama_data['color'] = 'gray'

                # 方法2: 尝试提取价格信息
                import re
                price_patterns = [
                    r'(\d+\.?\d*)\s*USDT',
                    r'price[\"\']:\s*[\"\']?(\d+\.?\d*)',
                    r'[\"\']last[\"\']:\s*[\"\']?(\d+\.?\d*)'
                ]

                for pattern in price_patterns:
                    match = re.search(pattern, page_content)
                    if match:
                        try:
                            price = float(match.group(1))
                            hama_data['price'] = price
                            hama_data['current_price'] = price
                            logger.info(f"✅ 提取到价格: {price}")
                            break
                        except (ValueError, IndexError):
                            continue

            logger.info(f"✅ {symbol} 数据解析完成")
            logger.info(f"   趋势: {hama_data['hama_trend']}")
            logger.info(f"   颜色: {hama_data['hama_color']}")
            logger.info(f"   价格: {hama_data['price']}")

            return hama_data

        except Exception as e:
            logger.error(f"解析TradingView数据失败: {e}")
            import traceback
            logger.debug(f"详细错误: {traceback.format_exc()}")
            return None

    def extract_hama_data_screenshot_ocr(self, symbol: str, timeframe: str = '15m') -> Optional[Dict[str, Any]]:
        """
        使用 BrowserAct 截图 + OCR 提取数据（混合方案）

        Args:
            symbol: 交易对符号
            timeframe: 时间周期

        Returns:
            提取的数据字典
        """
        try:
            from app.services.hama_ocr_extractor import HAMAOCRExtractor
            from app.config.browseract_config import BrowserActConfig
            import uuid

            logger.info(f"🔄 使用 BrowserAct 截图 + OCR 方式提取 {symbol} 数据...")

            # 获取配置的浏览器
            browser_config = BrowserActConfig.get_browser_config()
            browser_id = browser_config['id']

            # 生成会话名称
            session_name = f"hama_ocr_{symbol}_{uuid.uuid4().hex[:8]}"

            # 构建 TradingView URL
            tradingview_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}"

            # 打开浏览器会话
            cmd_open = [
                self.browseract_cmd,
                '--session', session_name,
                'browser', 'open', browser_id,
                tradingview_url
            ]

            result = subprocess.run(
                cmd_open,
                capture_output=True,
                text=False,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"浏览器会话打开失败")
                return None

            logger.info(f"浏览器会话已打开，等待页面加载...")

            # 等待页面加载
            import time
            time.sleep(15)

            # 截图保存路径
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = int(time.time())
            screenshot_path = os.path.join(screenshot_dir, f"hama_browseract_{symbol}_{timeframe}_{timestamp}.png")

            # 截图
            cmd_screenshot = [
                self.browseract_cmd,
                '--session', session_name,
                'screenshot', screenshot_path
            ]

            result = subprocess.run(
                cmd_screenshot,
                capture_output=True,
                text=False,
                timeout=30
            )

            # 关闭会话
            try:
                subprocess.run(
                    [self.browseract_cmd, '--session', session_name, 'session', 'close'],
                    capture_output=True,
                    timeout=10
                )
            except:
                pass

            if not os.path.exists(screenshot_path):
                logger.error(f"截图文件未生成: {screenshot_path}")
                return None

            logger.info(f"✅ 截图已保存: {screenshot_path}")

            # 使用 OCR 识别
            ocr_extractor = HAMAOCRExtractor(ocr_engine='rapidocr')

            # 读取截图并识别
            hama_data = ocr_extractor.extract_hama_with_ocr(screenshot_path)

            if hama_data:
                hama_data['symbol'] = symbol
                hama_data['timeframe'] = timeframe
                hama_data['screenshot_path'] = os.path.basename(screenshot_path)
                hama_data['data_source'] = 'browseract_screenshot_ocr'
                hama_data['extraction_method'] = 'screenshot_ocr'

                logger.info(f"✅ {symbol} OCR 识别成功: {hama_data.get('color')} ({hama_data.get('trend')})")
                return hama_data
            else:
                logger.warning(f"OCR 识别失败: {symbol}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"BrowserAct 截图超时: {symbol}")
            return None
        except Exception as e:
            logger.error(f"BrowserAct 截图+OCR 提取失败: {e}")
            import traceback
            logger.debug(f"详细错误: {traceback.format_exc()}")
            return None

    def monitor_single_symbol(self, symbol: str, timeframe: str = '15m', check_email: bool = True) -> Optional[Dict[str, Any]]:
        """
        监控单个交易对（使用 BrowserAct 截图 + OCR）

        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            check_email: 是否检查并发送邮件通知

        Returns:
            监控结果
        """
        # 使用 BrowserAct 截图 + OCR 方式
        result = self.extract_hama_data_screenshot_ocr(symbol, timeframe)

        # 保存到数据库
        if result:
            self._save_to_db(result)

            # 检查并发送邮件通知（仅对 BTC 和 ETH）
            if check_email and self.enable_email and self.email_notifier:
                try:
                    self._check_and_notify_trend(symbol, result)
                except Exception as e:
                    logger.warning(f"发送邮件通知失败: {e}")

        return result

    def monitor_batch_parallel(self, symbols: List[str], timeframe: str = '15m') -> Dict[str, Any]:
        """
        并发监控多个交易对

        Args:
            symbols: 交易对列表
            timeframe: 时间周期

        Returns:
            监控结果汇总
        """
        results = {}
        success_count = 0
        failed_symbols = []

        logger.info(f"🚀 BrowserAct并发监控 {len(symbols)} 个交易对...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.monitor_single_symbol, symbol, timeframe): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=60)
                    if result:
                        results[symbol] = result
                        success_count += 1
                        logger.info(f"✅ {symbol} 监控成功")
                    else:
                        failed_symbols.append(symbol)
                        logger.warning(f"⚠️  {symbol} 监控失败")
                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.error(f"❌ {symbol} 监控异常: {e}")

        logger.info(f"📊 监控完成: {success_count}/{len(symbols)} 成功")

        if failed_symbols:
            logger.warning(f"失败的交易对: {', '.join(failed_symbols)}")

        return {
            'total': len(symbols),
            'success': success_count,
            'failed': len(failed_symbols),
            'results': results,
            'failed_symbols': failed_symbols
        }

    def _save_to_db(self, data: Dict[str, Any]):
        """保存监控数据到数据库"""
        if not self.sqlite_conn:
            return

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO hama_browseract_cache
                (symbol, timeframe, hama_trend, hama_color, hama_value, price,
                 data_source, raw_data, extraction_method, monitored_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'],
                data['timeframe'],
                data.get('hama_trend'),
                data.get('hama_color'),
                data.get('hama_value'),
                data.get('price'),
                data.get('data_source'),
                data.get('raw_data'),
                data.get('extraction_method'),
                datetime.now(),
                datetime.now()
            ))
            self.sqlite_conn.commit()
        except Exception as e:
            logger.error(f"保存数据库失败: {e}")

    def _get_last_sent_email_state(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从邮件发送日志查询最后一次发送邮件时的状态

        Args:
            symbol: 币种符号

        Returns:
            {'color': ..., 'trend': ..., 'value': ..., 'sent_at': ...} 或 None
        """
        if not self.sqlite_conn:
            return None

        try:
            cursor = self.sqlite_conn.cursor()

            # 查询最后一次成功发送邮件的记录
            cursor.execute('''
                SELECT hama_color, hama_trend, hama_value, sent_at
                FROM email_send_log
                WHERE symbol = ? AND status = 'success'
                ORDER BY sent_at DESC
                LIMIT 1
            ''', (symbol,))

            email_row = cursor.fetchone()

            if email_row:
                return {
                    'color': email_row[0] or '',
                    'trend': email_row[1] or '',
                    'value': float(email_row[2]) if email_row[2] else 0,
                    'sent_at': email_row[3]
                }

            return None

        except Exception as e:
            logger.warning(f"从邮件发送日志查询最后状态失败 {symbol}: {e}")
            return None

    def _log_email_send(
        self,
        symbol: str,
        email_type: str,
        hama_color: str,
        hama_trend: str,
        hama_value: Any,
        price: Any,
        cross_type: Optional[str],
        screenshot_path: str,
        success: bool,
        recipients: str,
        error_message: Optional[str] = None
    ):
        """
        记录邮件发送日志到数据库

        Args:
            symbol: 币种符号
            email_type: 邮件类型 (trend_notification)
            hama_color: HAMA 颜色
            hama_trend: HAMA 趋势
            hama_value: HAMA 值
            price: 当前价格
            cross_type: 交叉类型
            screenshot_path: 截图路径
            success: 是否发送成功
            recipients: 收件人
            error_message: 错误信息（如果失败）
        """
        if not self.sqlite_conn:
            return

        try:
            cursor = self.sqlite_conn.cursor()

            # 插入邮件发送记录
            cursor.execute("""
                INSERT INTO email_send_log (
                    symbol, email_type, hama_color, hama_trend, hama_value, price,
                    cross_type, recipients, status, error_message, screenshot_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                email_type,
                hama_color,
                hama_trend,
                float(hama_value) if hama_value else 0,
                float(price) if price else 0,
                cross_type or '',
                recipients,
                'success' if success else 'failed',
                error_message,
                screenshot_path or ''
            ))

            self.sqlite_conn.commit()
            logger.info(f"✅ 邮件发送记录已保存: {symbol} - {email_type} - {'成功' if success else '失败'}")

        except Exception as e:
            logger.error(f"记录邮件发送日志失败: {e}")

    def _check_and_notify_trend(self, symbol: str, hama_data: Dict[str, Any]) -> bool:
        """
        检查趋势并发送邮件通知

        Args:
            symbol: 币种符号
            hama_data: HAMA 数据

        Returns:
            是否发送了邮件
        """
        try:
            # 提取当前状态
            current_color = hama_data.get('hama_color', '')
            current_trend = hama_data.get('hama_trend', '')
            current_value = hama_data.get('hama_value', 0)
            price = hama_data.get('price', 0)

            # 从邮件发送日志查询最后一次发送邮件时的状态
            last_email_state = self._get_last_sent_email_state(symbol)

            # 检查是否需要发送通知（趋势变化）
            should_notify = False
            cross_type = None

            if last_email_state:
                # 有邮件发送历史，比较当前状态与最后一次发送邮件时的状态
                last_email_color = last_email_state.get('color', '')

                logger.info(f"{symbol} 状态对比(上次邮件状态): 上次邮件={last_email_color}, 当前={current_color}")

                # 只要颜色发生变化就触发邮件
                if last_email_color != current_color:
                    # 颜色变化，检测金叉/死叉
                    if current_color == 'green':
                        should_notify = True
                        cross_type = 'cross_up'
                        logger.info(f"✅ 检测到金叉信号: {symbol} (上次邮件颜色: {last_email_color} → 当前: {current_color})")
                    elif current_color == 'red':
                        should_notify = True
                        cross_type = 'cross_down'
                        logger.info(f"✅ 检测到死叉信号: {symbol} (上次邮件颜色: {last_email_color} → 当前: {current_color})")
                    else:
                        logger.info(f"ℹ️ {symbol} 颜色变化: {last_email_color} → {current_color}，非绿/红趋势，不发送邮件")
                else:
                    logger.info(f"❌ {symbol} 颜色与上次邮件相同: {last_email_color} → {current_color}，不发送邮件")
            else:
                # 从未发送过邮件（首次邮件通知）
                logger.info(f"🆕 首次邮件通知 {symbol}（无邮件发送历史），当前状态: {current_color}")
                # 只要是 green 或 red 状态就发送首次通知
                if current_color == 'green':
                    should_notify = True
                    cross_type = 'cross_up'
                    logger.info(f"✅ 首次邮件通知 - 检测到上涨趋势: {symbol} ({current_color})")
                elif current_color == 'red':
                    should_notify = True
                    cross_type = 'cross_down'
                    logger.info(f"✅ 首次邮件通知 - 检测到下跌趋势: {symbol} ({current_color})")
                else:
                    logger.info(f"ℹ️ 首次监控 {symbol} 当前状态为 {current_color}，非绿/红趋势，不发送邮件")

            if not should_notify:
                return False

            # 检查是否在邮件监控白名单中（只有 BTC 和 ETH 才发送邮件）
            email_whitelist = ['BTCUSDT', 'ETHUSDT']
            if symbol not in email_whitelist:
                logger.info(f"{symbol} 不在邮件监控白名单中，跳过发送（仅 BTC/ETH 发送邮件）")
                return False

            # 发送邮件通知
            logger.info(f"准备发送邮件通知: {symbol} ({current_color}, {current_trend})")

            extra_data = {
                'data_source': hama_data.get('data_source', 'browseract'),
                'extraction_method': hama_data.get('extraction_method', 'unknown')
            }

            success = self.email_notifier.notify_trend_formed(
                symbol=symbol,
                trend=current_trend,
                hama_color=current_color,
                hama_value=float(current_value) if current_value else 0,
                price=float(price) if price else 0,
                cross_type=cross_type,
                screenshot_url=None,
                screenshot_path=None,
                full_chart_path=None,
                extra_data=extra_data
            )

            # 记录邮件发送日志到数据库
            self._log_email_send(
                symbol=symbol,
                email_type='trend_notification',
                hama_color=current_color,
                hama_trend=current_trend,
                hama_value=current_value,
                price=price,
                cross_type=cross_type,
                screenshot_path='',
                success=success,
                recipients=self.email_notifier.default_recipients if self.email_notifier else ''
            )

            if success:
                logger.info(f"✅ {symbol} 邮件通知发送成功")
                return True
            else:
                logger.warning(f"❌ {symbol} 邮件通知发送失败")
                return False

        except Exception as e:
            logger.error(f"检查趋势并发送邮件失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def start_monitoring(self, symbols: List[str], interval: int = 300):
        """
        启动监控循环

        Args:
            symbols: 交易对列表
            interval: 监控间隔（秒）
        """
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return

        self.symbols = symbols
        self.interval = interval
        self.is_monitoring = True

        def monitor_loop():
            while self.is_monitoring:
                try:
                    logger.info(f"🔄 开始新一轮监控 ({len(self.symbols)} 个交易对)")
                    self.monitor_batch_parallel(self.symbols)
                    self.last_monitor_time = datetime.now()

                    # 等待下一轮
                    logger.info(f"⏳ 等待 {self.interval} 秒后开始下一轮...")
                    time.sleep(self.interval)

                except Exception as e:
                    logger.error(f"监控循环异常: {e}")
                    time.sleep(60)  # 出错后等待1分钟

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"✅ BrowserAct监控已启动，间隔: {interval}秒")

    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 BrowserAct监控已停止")

    def get_status(self) -> Dict[str, Any]:
        """获取监控器状态"""
        return {
            'type': 'browseract',
            'available': self.browseract_available,
            'is_monitoring': self.is_monitoring,
            'symbols_count': len(self.symbols),
            'interval': self.interval,
            'last_monitor_time': self.last_monitor_time.isoformat() if self.last_monitor_time else None,
            'extraction_method': 'browseract_direct' if self.browseract_available else 'fallback_ocr'
        }

    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        if self.sqlite_conn:
            self.sqlite_conn.close()
        logger.info("BrowserAct监控器资源已清理")

    def test_browseract_integration(self) -> Dict[str, Any]:
        """
        测试 BrowserAct 集成功能

        Returns:
            测试结果字典
        """
        logger.info("🧪 开始测试 BrowserAct 集成...")

        test_results = {
            'cli_available': self.browseract_available,
            'cli_version': None,
            'test_extraction': False,
            'test_symbol': 'BTCUSDT',
            'extraction_result': None,
            'extraction_time': None,
            'errors': []
        }

        try:
            # 测试1: 检查CLI版本
            if self.browseract_available:
                result = subprocess.run(
                    [self.browseract_cmd, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    test_results['cli_version'] = result.stdout.strip()
                    logger.info(f"✅ BrowserAct 版本: {test_results['cli_version']}")

            # 测试2: 测试数据提取
            import time
            start_time = time.time()

            test_symbol = test_results['test_symbol']
            logger.info(f"🔍 测试提取 {test_symbol} 数据...")

            extraction_result = self.extract_hama_data_direct(test_symbol, '15m')
            extraction_time = time.time() - start_time

            test_results['extraction_time'] = round(extraction_time, 2)
            test_results['extraction_result'] = extraction_result is not None

            if extraction_result:
                test_results['test_extraction'] = True
                logger.info(f"✅ 数据提取测试成功 (耗时: {extraction_time:.2f}秒)")
                logger.info(f"   结果: {extraction_result}")
            else:
                test_results['errors'].append("数据提取返回None")
                logger.warning("⚠️  数据提取测试失败")

        except Exception as e:
            error_msg = f"测试异常: {str(e)}"
            test_results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")

        logger.info("🧪 BrowserAct 集成测试完成")
        return test_results