#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA蜡烛图信号监控服务
基于TradingView HAMA指标算法实现涨跌信号监控
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import requests
import ccxt

logger = logging.getLogger(__name__)


class HAMASignalMonitor:
    """HAMA信号监控器"""

    def __init__(self, db_path: str = None):
        """
        初始化监控器

        Args:
            db_path: 数据库路径,用于持久化信号
        """
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.signals: List[Dict] = []
        self.callbacks: List[Callable] = []  # 信号回调函数列表
        self.monitored_symbols: Dict[str, Dict] = {}  # 正在监控的币种 {symbol: {last_check, ...}}
        self.check_interval = 60  # 检查间隔(秒)
        self.signal_cooldown = 300  # 信号冷却时间(秒),避免短时间内重复报警

        # 自动获取涨幅榜配置
        self.auto_fetch_gainers = True  # 是否启用自动获取涨幅榜
        self.auto_fetch_interval = 180  # 自动获取间隔(秒),默认3分钟
        self.auto_fetch_limit = 20  # 自动获取数量,默认TOP20
        self.last_auto_fetch_time: Optional[datetime] = None  # 上次自动获取时间

        # API配置
        self.binance_base_url = "https://api.binance.com"

        # HAMA参数(与TradingView指标保持一致)
        self.ma_length = 55
        self.ma_type = "WMA"  # WMA, SMA, EMA
        self.open_length = 25
        self.open_type = "EMA"
        self.high_length = 20
        self.high_type = "EMA"
        self.low_length = 20
        self.low_type = "EMA"
        self.close_length = 20
        self.close_type = "WMA"

        # K线数据缓存
        self.kline_cache: Dict[str, List[Dict]] = {}

    def start(self):
        """启动监控服务"""
        if self.running:
            logger.warning("HAMA监控服务已在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("HAMA信号监控服务已启动")

    def stop(self):
        """停止监控服务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("HAMA信号监控服务已停止")

    def add_symbol(self, symbol: str, market_type: str = "spot"):
        """
        添加监控币种

        Args:
            symbol: 币种符号,如 "BTCUSDT"
            market_type: 市场类型 "spot" 或 "futures"
        """
        self.monitored_symbols[symbol] = {
            "symbol": symbol,
            "market_type": market_type,
            "added_at": datetime.now(),
            "last_check": None,
            "last_signal": None,
            "last_signal_time": None
        }
        logger.info(f"添加监控币种: {symbol} ({market_type})")

    def remove_symbol(self, symbol: str):
        """
        移除监控币种

        Args:
            symbol: 币种符号
        """
        if symbol in self.monitored_symbols:
            del self.monitored_symbols[symbol]
            if symbol in self.kline_cache:
                del self.kline_cache[symbol]
            logger.info(f"移除监控币种: {symbol}")

    def add_signal_callback(self, callback: Callable):
        """
        添加信号回调函数

        Args:
            callback: 回调函数,接收参数 (signal_data)
        """
        self.callbacks.append(callback)

    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """
        获取最近的信号

        Args:
            limit: 返回数量限制

        Returns:
            信号列表
        """
        return sorted(self.signals, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def _monitor_loop(self):
        """监控主循环"""
        logger.info("HAMA监控循环开始")
        while self.running:
            try:
                # 检查所有监控币种的信号
                self._check_all_symbols()

                # 自动获取涨幅榜
                if self.auto_fetch_gainers:
                    self._auto_fetch_top_gainers()

            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}", exc_info=True)

            time.sleep(self.check_interval)

        logger.info("HAMA监控循环结束")

    def _check_all_symbols(self):
        """检查所有监控币种"""
        for symbol, info in self.monitored_symbols.items():
            try:
                self._check_symbol(symbol, info)
            except Exception as e:
                logger.error(f"检查币种 {symbol} 时出错: {str(e)}")

    def _auto_fetch_top_gainers(self):
        """自动获取涨幅榜TOP币种并加入监控"""
        try:
            # 检查是否到达自动获取时间
            now = datetime.now()
            if self.last_auto_fetch_time:
                elapsed = (now - self.last_auto_fetch_time).total_seconds()
                if elapsed < self.auto_fetch_interval:
                    return  # 还未到自动获取时间

            # 获取涨幅榜 (默认使用永续合约)
            from app.services.binance_gainer import BinanceGainerService
            binance = BinanceGainerService()
            gainers = binance.get_top_gainers_futures(self.auto_fetch_limit)

            if not gainers:
                logger.warning("获取涨幅榜失败,跳过自动添加")
                return

            # 添加到监控 (默认使用永续合约)
            added_count = 0
            for gainer in gainers:
                symbol = gainer['symbol']
                if symbol not in self.monitored_symbols:
                    self.add_symbol(symbol, "futures")
                    added_count += 1

            # 更新最后自动获取时间
            self.last_auto_fetch_time = now

            logger.info(f"✅ 自动获取涨幅榜: 添加了 {added_count} 个币种 (总计: {len(gainers)})")

        except Exception as e:
            logger.error(f"自动获取涨幅榜失败: {str(e)}", exc_info=True)

    def _check_symbol(self, symbol: str, info: Dict):
        """
        检查单个币种

        Args:
            symbol: 币种符号
            info: 币种信息
        """
        # 检查冷却时间
        if info.get("last_signal_time"):
            elapsed = (datetime.now() - info["last_signal_time"]).total_seconds()
            if elapsed < self.signal_cooldown:
                logger.debug(f"{symbol} 仍在冷却期内,跳过检查")
                return

        # 获取K线数据
        klines = self._fetch_klines(symbol)
        if not klines or len(klines) < self.ma_length + 10:
            logger.warning(f"{symbol} K线数据不足")
            return

        # 计算HAMA指标
        hama_data = self._calculate_hama(klines)
        if not hama_data:
            return

        # 检测交叉信号
        signal = self._detect_crossover(hama_data, symbol)
        if signal:
            self._handle_signal(signal, info)

        # 更新检查时间
        info["last_check"] = datetime.now()

    def _fetch_klines(self, symbol: str, limit: int = 200) -> Optional[List[Dict]]:
        """
        获取K线数据

        Args:
            symbol: 币种符号
            limit: 获取数量

        Returns:
            K线数据列表
        """
        try:
            # 优先使用Binance期货API(对某些币种限制更少)
            urls = [
                f"{self.binance_base_url}/fapi/v1/klines",  # 期货API
                f"{self.binance_base_url}/api/v3/klines"      # 现货API
            ]

            params = {
                "symbol": symbol,
                "interval": "15m",  # 15分钟K线
                "limit": limit
            }

            # 尝试期货API,失败则尝试现货API
            for url in urls:
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    if data and len(data) > 0:
                        logger.info(f"成功从 {url.split('/')[-2]} 获取 {symbol} K线数据")
                        break
                except Exception as e:
                    logger.warning(f"从 {url} 获取 {symbol} 失败: {e}")
                    continue
            else:
                raise Exception("所有API均失败")

            # 转换为标准格式
            klines = []
            for item in data:
                klines.append({
                    "timestamp": item[0],
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5])
                })

            self.kline_cache[symbol] = klines
            return klines

        except Exception as e:
            logger.error(f"获取 {symbol} K线数据失败: {str(e)}")
            return None

    def _calculate_hama(self, klines: List[Dict]) -> Optional[Dict]:
        """
        计算HAMA指标(基于TradingView算法)

        Args:
            klines: K线数据

        Returns:
            HAMA指标数据
        """
        try:
            import numpy as np

            closes = np.array([k["close"] for k in klines])
            highs = np.array([k["high"] for k in klines])
            lows = np.array([k["low"] for k in klines])
            opens_data = np.array([k["open"] for k in klines])

            # 计算HAMA源数据
            n = len(klines)
            source_open = np.zeros(n)
            source_high = np.zeros(n)
            source_low = np.zeros(n)
            source_close = np.zeros(n)

            for i in range(n):
                if i == 0:
                    source_open[i] = opens_data[i]
                else:
                    source_open[i] = (opens_data[i-1] + closes[i-1]) / 2

                source_high[i] = max(highs[i], closes[i])
                source_low[i] = min(lows[i], closes[i])
                source_close[i] = (opens_data[i] + highs[i] + lows[i] + closes[i]) / 4

            # 计算HAMA蜡烛图
            candle_open = self._calculate_ma(source_open, self.open_length, self.open_type)
            candle_high = self._calculate_ma(source_high, self.high_length, self.high_type)
            candle_low = self._calculate_ma(source_low, self.low_length, self.low_type)
            candle_close = self._calculate_ma(source_close, self.close_length, self.close_type)

            # 计算MA线
            ma = self._calculate_ma(candle_close, self.ma_length, self.ma_type)

            # 返回最近的数据
            return {
                "candle_close": candle_close[-1],
                "candle_close_prev": candle_close[-2] if len(candle_close) > 1 else None,
                "ma": ma[-1],
                "ma_prev": ma[-2] if len(ma) > 1 else None,
                "current_price": closes[-1],
                "timestamp": klines[-1]["timestamp"]
            }

        except Exception as e:
            logger.error(f"计算HAMA指标失败: {str(e)}")
            return None

    def _calculate_ma(self, data: 'numpy.ndarray', length: int, ma_type: str) -> 'numpy.ndarray':
        """
        计算移动平均线

        Args:
            data: 价格数据
            length: 周期
            ma_type: 类型 (SMA, EMA, WMA)

        Returns:
            MA值数组
        """
        import numpy as np

        if ma_type == "SMA":
            # 简单移动平均
            result = np.zeros(len(data))
            for i in range(length - 1, len(data)):
                result[i] = np.mean(data[i - length + 1:i + 1])
            return result

        elif ma_type == "EMA":
            # 指数移动平均
            result = np.zeros(len(data))
            multiplier = 2 / (length + 1)
            result[length - 1] = np.mean(data[:length])
            for i in range(length, len(data)):
                result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
            return result

        elif ma_type == "WMA":
            # 加权移动平均
            result = np.zeros(len(data))
            weights = np.arange(1, length + 1)
            for i in range(length - 1, len(data)):
                result[i] = np.sum(data[i - length + 1:i + 1] * weights) / np.sum(weights)
            return result

        else:
            raise ValueError(f"不支持的MA类型: {ma_type}")

    def _detect_crossover(self, hama_data: Dict, symbol: str) -> Optional[Dict]:
        """
        检测交叉信号

        Args:
            hama_data: HAMA数据
            symbol: 币种符号

        Returns:
            信号数据或None
        """
        candle_close = hama_data["candle_close"]
        candle_close_prev = hama_data["candle_close_prev"]
        ma = hama_data["ma"]
        ma_prev = hama_data["ma_prev"]

        if None in [candle_close_prev, ma_prev]:
            return None

        # 检测上穿(涨信号)
        if candle_close_prev <= ma_prev and candle_close > ma:
            return {
                "symbol": symbol,
                "signal_type": "UP",  # 涨信号
                "price": hama_data["current_price"],
                "candle_close": candle_close,
                "ma": ma,
                "timestamp": datetime.now(),
                "description": f"HAMA蜡烛图上穿MA线"
            }

        # 检测下穿(跌信号)
        if candle_close_prev >= ma_prev and candle_close < ma:
            return {
                "symbol": symbol,
                "signal_type": "DOWN",  # 跌信号
                "price": hama_data["current_price"],
                "candle_close": candle_close,
                "ma": ma,
                "timestamp": datetime.now(),
                "description": f"HAMA蜡烛图下穿MA线"
            }

        return None

    def _handle_signal(self, signal: Dict, info: Dict):
        """
        处理信号

        Args:
            signal: 信号数据
            info: 币种信息
        """
        # 添加到信号列表
        self.signals.append(signal)

        # 限制信号列表大小
        if len(self.signals) > 1000:
            self.signals = self.signals[-500:]

        # 更新币种信息
        info["last_signal"] = signal["signal_type"]
        info["last_signal_time"] = datetime.now()

        # 记录日志
        logger.info(
            f"🔔 HAMA信号: {signal['symbol']} - "
            f"{'📈 涨' if signal['signal_type'] == 'UP' else '📉 跌'} - "
            f"价格: {signal['price']:.4f} - "
            f"{signal['description']}"
        )

        # 调用回调函数
        for callback in self.callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"信号回调函数执行失败: {str(e)}")


# 全局监控器实例
_monitor_instance: Optional[HAMASignalMonitor] = None


def get_monitor() -> HAMASignalMonitor:
    """获取全局监控器实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = HAMASignalMonitor()
    return _monitor_instance
