#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA指标混合获取服务
结合后端计算和Selenium浏览器的优势
"""
import time
from typing import Dict, Any, Optional, List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HAMAHybridService:
    """HAMA指标混合获取服务"""

    def __init__(self):
        """初始化混合服务"""
        self.backend_enabled = True
        self.selenium_enabled = True

    def get_hama_indicator(
        self,
        symbol: str,
        interval: str = "15",
        use_selenium: bool = False,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取HAMA指标数据(混合模式)

        策略:
        1. 优先使用后端计算(快速、稳定)
        2. 如果后端失败,回退到Selenium
        3. 支持强制使用Selenium(获取页面数据)

        Args:
            symbol: 币种符号
            interval: 时间间隔
            use_selenium: 是否强制使用Selenium
            force_refresh: 是否强制刷新(不使用缓存)

        Returns:
            HAMA指标数据
        """
        start_time = time.time()

        # 方法1: 强制使用Selenium
        if use_selenium:
            logger.info(f"[Selenium模式] 正在获取 {symbol} 的HAMA指标...")
            result = self._get_from_selenium(symbol, interval)
            if result:
                result['source'] = 'selenium'
                result['calculation_time'] = time.time() - start_time
                return result
            else:
                logger.warning(f"Selenium获取失败,尝试后端计算...")
                # Selenium失败,回退到后端计算
                result = self._get_from_backend(symbol, interval, force_refresh)
                if result:
                    result['source'] = 'backend_fallback'
                    result['calculation_time'] = time.time() - start_time
                return result

        # 方法2: 优先使用后端计算(快速)
        if self.backend_enabled:
            logger.info(f"[后端计算模式] 正在获取 {symbol} 的HAMA指标...")
            result = self._get_from_backend(symbol, interval, force_refresh)

            if result:
                result['source'] = 'backend'
                result['calculation_time'] = time.time() - start_time
                logger.info(f"✅ 后端计算成功, 耗时: {result['calculation_time']:.2f}秒")
                return result
            else:
                logger.warning(f"后端计算失败,尝试Selenium...")

        # 方法3: 后端失败,回退到Selenium
        if self.selenium_enabled:
            logger.info(f"[Selenium回退模式] 正在获取 {symbol} 的HAMA指标...")
            result = self._get_from_selenium(symbol, interval)
            if result:
                result['source'] = 'selenium_fallback'
                result['calculation_time'] = time.time() - start_time
                return result

        logger.error(f"❌ 所有方法都失败了")
        return None

    def _get_from_backend(
        self,
        symbol: str,
        interval: str,
        force_refresh: bool
    ) -> Optional[Dict[str, Any]]:
        """从后端计算获取HAMA指标"""
        try:
            from app.services.tradingview_service import TradingViewDataService
            from app.services.hama_cache import HamaCacheManager

            tv_service = TradingViewDataService()
            cache_manager = HamaCacheManager()

            # 检查缓存
            if not force_refresh:
                cached = cache_manager.get(symbol)
                if cached and cached.get('hama_data'):
                    logger.info(f"✅ 从Redis缓存获取 {symbol} 的HAMA数据")
                    return self._format_backend_data(symbol, interval, cached['hama_data'], cached=True)

            # 获取K线数据并计算HAMA (使用私有方法 _fetch_kline_data)
            logger.info(f"正在获取 {symbol} 的K线数据...")
            kline_data = tv_service._fetch_kline_data(symbol, limit=200)

            if not kline_data or len(kline_data) < 100:
                logger.warning(f"K线数据不足: {len(kline_data) if kline_data else 0}")
                return None

            # 计算HAMA指标
            logger.info(f"正在计算HAMA指标...")
            hama_data = self._calculate_hama_indicators(kline_data)

            # 缓存结果
            cache_manager.set(symbol, {
                'symbol': symbol,
                'hama_data': hama_data,
                'timestamp': time.time()
            })

            return self._format_backend_data(symbol, interval, hama_data, cached=False)

        except Exception as e:
            logger.error(f"后端计算失败: {e}", exc_info=True)
            return None

    def _get_from_selenium(
        self,
        symbol: str,
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """从Selenium浏览器获取HAMA指标"""
        try:
            from app.services.hama_indicator_selenium import HAMAIndicatorSelenium

            service = HAMAIndicatorSelenium(headless=True)
            result = service.get_hama_indicator_data(symbol, interval)

            if result:
                # 格式化Selenium数据
                return self._format_selenium_data(symbol, interval, result)

            return None

        except Exception as e:
            logger.error(f"Selenium获取失败: {e}", exc_info=True)
            return None

    def _calculate_hama_indicators(self, kline_data: List[Dict]) -> Dict[str, Any]:
        """
        计算HAMA指标
        使用hamaCandel.txt中的参数

        Args:
            kline_data: K线数据列表

        Returns:
            HAMA指标数据
        """
        import pandas as pd
        import numpy as np

        # 转换为DataFrame
        df = pd.DataFrame(kline_data)
        df = df.sort_values('timestamp')

        # 提取OHLC
        open_price = df['open'].values
        high_price = df['high'].values
        low_price = df['low'].values
        close_price = df['close'].values

        # 计算HAMA蜡烛图 (使用传统Heiken Ashi公式)
        # HA_Close = (O + H + L + C) / 4
        ha_close = (open_price + high_price + low_price + close_price) / 4

        # HA_Open = (previous HA_Open + previous HA_Close) / 2
        ha_open = np.zeros_like(ha_close)
        ha_open[0] = (open_price[0] + close_price[0]) / 2
        for i in range(1, len(ha_close)):
            ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2

        # HA_High = max(H, HA_Open, HA_Close)
        ha_high = np.maximum(high_price, np.maximum(ha_open, ha_close))

        # HA_Low = min(L, HA_Open, HA_Close)
        ha_low = np.minimum(low_price, np.minimum(ha_open, ha_close))

        # 使用EMA平滑HAMA (hamaCandel.txt参数)
        # 开盘价: EMA 45
        # 最高价: EMA 20
        # 最低价: EMA 20
        # 收盘价: WMA 40

        def ema(data, period):
            alpha = 2 / (period + 1)
            result = np.zeros_like(data)
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
            return result

        def wma(data, period):
            result = np.zeros_like(data)
            for i in range(period - 1, len(data)):
                weights = np.arange(1, period + 1)
                result[i] = np.sum(data[i-period+1:i+1] * weights) / weights.sum()
            return result

        # 应用平滑
        candle_open = ema(ha_open, 45)
        candle_high = ema(ha_high, 20)
        candle_low = ema(ha_low, 20)
        candle_close = wma(ha_close, 40)

        # 计算MA100 (WMA)
        ma100 = wma(close_price, 100)

        # 获取最新的值
        latest_idx = -1
        current_candle_open = candle_open[latest_idx]
        current_candle_close = candle_close[latest_idx]
        current_ma100 = ma100[latest_idx]

        # 判断交叉信号
        prev_candle_close = candle_close[latest_idx - 1]
        prev_ma100 = ma100[latest_idx - 1]

        cross_signal = {
            'direction': 0,  # 0=无, 1=涨(金叉), -1=跌(死叉)
            'signal': None
        }

        # 金叉: HAMA收盘价上穿MA100
        if prev_candle_close <= prev_ma100 and current_candle_close > current_ma100:
            cross_signal['direction'] = 1
            cross_signal['signal'] = '涨'

        # 死叉: HAMA收盘价下穿MA100
        elif prev_candle_close >= prev_ma100 and current_candle_close < current_ma100:
            cross_signal['direction'] = -1
            cross_signal['signal'] = '跌'

        # 判断趋势
        if current_candle_close > current_ma100:
            hama_trend = 'bullish'
            status_text = '上涨趋势'
            candle_ma_relation = '蜡烛在MA上'
        elif current_candle_close < current_ma100:
            hama_trend = 'bearish'
            status_text = '下跌趋势'
            candle_ma_relation = '蜡烛在MA下'
        else:
            hama_trend = 'neutral'
            status_text = '盘整'
            candle_ma_relation = '重合'

        # 计算布林带 (周期400, 标准差2倍)
        bb_period = 400
        bb_std = 2.0

        if len(close_price) >= bb_period:
            bb_middle = pd.Series(close_price).rolling(bb_period).mean().values[latest_idx]
            bb_std_val = pd.Series(close_price).rolling(bb_period).std().values[latest_idx]
            bb_upper = bb_middle + bb_std_val * bb_std
            bb_lower = bb_middle - bb_std_val * bb_std

            current_price = close_price[latest_idx]
            bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
            price_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5

            # 判断布林带状态
            if bb_width < 0.1:
                bb_status = 'squeeze'  # 收缩
            elif bb_width > 0.15:
                bb_status = 'expansion'  # 扩张
            else:
                bb_status = 'normal'  # 正常
        else:
            bb_middle = bb_upper = bb_lower = None
            bb_width = price_position = None
            bb_status = None

        return {
            'hama_candles': {
                'open': float(current_candle_open),
                'high': float(candle_high[latest_idx]),
                'low': float(candle_low[latest_idx]),
                'close': float(current_candle_close)
            },
            'ma100': float(current_ma100),
            'ma_type': 'WMA',
            'ma_length': 100,
            'cross_signal': cross_signal,
            'hama_status': {
                'trend': hama_trend,
                'status_text': status_text,
                'candle_ma_relation': candle_ma_relation
            },
            'bollinger_bands': {
                'upper': float(bb_upper) if bb_upper else None,
                'middle': float(bb_middle) if bb_middle else None,
                'lower': float(bb_lower) if bb_lower else None,
                'width': float(bb_width) if bb_width else None,
                'price_position': float(price_position) if price_position is not None else None,
                'status': bb_status
            }
        }

    def _format_backend_data(
        self,
        symbol: str,
        interval: str,
        hama_data: Dict,
        cached: bool
    ) -> Dict[str, Any]:
        """格式化后端数据"""
        return {
            'symbol': symbol,
            'interval': interval,
            'timestamp': hama_data.get('timestamp', time.time()),
            'method': 'backend_calculation',
            'cached': cached,
            **hama_data
        }

    def _format_selenium_data(
        self,
        symbol: str,
        interval: str,
        selenium_data: Dict
    ) -> Dict[str, Any]:
        """格式化Selenium数据"""
        return {
            'symbol': symbol,
            'interval': interval,
            'timestamp': selenium_data.get('timestamp', time.time()),
            'method': 'selenium_browser',
            **selenium_data
        }

    def get_batch_hama_indicators(
        self,
        symbols: List[str],
        interval: str = "15",
        use_selenium: bool = False,
        max_parallel: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量获取HAMA指标数据(并行)

        Args:
            symbols: 币种列表
            interval: 时间间隔
            use_selenium: 是否使用Selenium
            max_parallel: 最大并行数

        Returns:
            HAMA指标数据列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        start_time = time.time()

        logger.info(f"开始批量获取 {len(symbols)} 个币种的HAMA指标 (并行数={max_parallel})...")

        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self.get_hama_indicator, symbol, interval, use_selenium): symbol
                for symbol in symbols
            }

            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.info(f"✅ {symbol} 完成 (来源: {result.get('source', 'unknown')}, 耗时: {result.get('calculation_time', 0):.2f}s)")
                    else:
                        logger.warning(f"❌ {symbol} 失败")
                except Exception as e:
                    logger.error(f"❌ {symbol} 异常: {e}")

        total_time = time.time() - start_time
        logger.info(f"✅ 批量获取完成: {len(results)}/{len(symbols)} 成功, 总耗时: {total_time:.2f}秒")

        return results


# 全局实例
_hama_hybrid_service = None


def get_hama_hybrid_service() -> HAMAHybridService:
    """获取HAMA混合服务实例"""
    global _hama_hybrid_service
    if _hama_hybrid_service is None:
        _hama_hybrid_service = HAMAHybridService()
    return _hama_hybrid_service


# 便捷函数
def get_hama_indicator_hybrid(
    symbol: str,
    interval: str = "15",
    use_selenium: bool = False,
    force_refresh: bool = False
) -> Optional[Dict[str, Any]]:
    """
    获取HAMA指标(混合模式)

    Args:
        symbol: 币种符号
        interval: 时间间隔
        use_selenium: 是否强制使用Selenium
        force_refresh: 是否强制刷新

    Returns:
        HAMA指标数据
    """
    service = get_hama_hybrid_service()
    return service.get_hama_indicator(symbol, interval, use_selenium, force_refresh)


def get_batch_hama_indicators_hybrid(
    symbols: List[str],
    interval: str = "15",
    use_selenium: bool = False,
    max_parallel: int = 5
) -> List[Dict[str, Any]]:
    """
    批量获取HAMA指标(混合模式)

    Args:
        symbols: 币种列表
        interval: 时间间隔
        use_selenium: 是否使用Selenium
        max_parallel: 最大并行数

    Returns:
        HAMA指标数据列表
    """
    service = get_hama_hybrid_service()
    return service.get_batch_hama_indicators(symbols, interval, use_selenium, max_parallel)
