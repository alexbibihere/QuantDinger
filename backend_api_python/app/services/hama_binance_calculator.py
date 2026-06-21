#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 指标计算服务（基于 Binance API）
根据 Pine Script 算法本地计算 HAMA 指标，无需截图+OCR
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HAMABinanceCalculator:
    """HAMA 指标计算器"""

    # Binance API 端点（使用 testnet，国内可直接访问）
    BINANCE_FUTURES_API = "https://testnet.binancefuture.com/fapi/v1/klines"
    BINANCE_SPOT_API = "https://testnet.binancefuture.com/fapi/v1/klines"

    def __init__(self, use_futures: bool = True):
        """
        初始化计算器

        Args:
            use_futures: 是否使用合约市场（默认 True），False 则使用现货市场
        """
        self.use_futures = use_futures
        self.base_url = self.BINANCE_FUTURES_API if use_futures else self.BINANCE_SPOT_API

    def get_klines(self, symbol: str, interval: str = '15m', limit: int = 500) -> Optional[pd.DataFrame]:
        """
        获取 K线数据

        Args:
            symbol: 币种符号
            interval: K线周期
            limit: 获取数量

        Returns:
            DataFrame 或 None
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }

            # testnet 可直接访问，但需要禁用环境变量代理避免干扰
            session = requests.Session()
            session.trust_env = False
            resp = session.get(
                self.base_url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'close'}
            )
            resp.raise_for_status()

            data = resp.json()

            # 转为 DataFrame
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # 类型转换
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)

            return df

        except Exception as e:
            logger.error(f"获取 {symbol} K线失败: {e}")
            return None

    def calculate_hama(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        计算 HAMA 指标

        Args:
            df: K线数据 DataFrame

        Returns:
            HAMA 指标数据字典
        """
        if df is None or len(df) < 100:
            return self._empty_result()

        try:
            # ===== 布林带 (bb_length=400, bb_mult=2.0) =====
            bb_length = 400
            df['basis'] = df['close'].rolling(bb_length).mean()
            df['dev'] = df['close'].rolling(bb_length).std()
            df['bb_upper'] = df['basis'] + df['dev'] * 2.0
            df['bb_lower'] = df['basis'] - df['dev'] * 2.0

            # ===== HAMA 蜡烛图 =====
            # Source 数据计算
            df['SourceOpen'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
            df['SourceHigh'] = df[['high', 'close']].max(axis=1)
            df['SourceLow'] = df[['low', 'close']].min(axis=1)
            df['SourceClose'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

            # EMA 计算
            df['CandleOpen'] = df['SourceOpen'].ewm(span=45, adjust=False).mean()
            df['CandleHigh'] = df['SourceHigh'].ewm(span=20, adjust=False).mean()
            df['CandleLow'] = df['SourceLow'].ewm(span=20, adjust=False).mean()
            df['CandleClose'] = df['SourceClose'].ewm(span=40, adjust=False).mean()

            # ===== MA 线 (ma_length=100, 使用 WMA 加权移动平均) =====
            # WMA: 权重从最近到最远递减 (1+2+...+100 = 5050)
            def wma(series, length):
                weights = np.arange(1, length + 1)
                def _wma(arr):
                    if len(arr) < length or np.any(pd.isna(arr)):
                        return np.nan
                    return np.dot(arr[-length:], weights) / weights.sum()
                return series.rolling(length).apply(_wma, raw=True)

            df['ma'] = wma(df['close'], 100)
            df['ma_ema3'] = df['ma'].ewm(span=3, adjust=False).mean()

            # ===== HAMA 颜色判断 =====
            def get_hama_color(row):
                if pd.isna(row['CandleClose']) or pd.isna(row['ma_ema3']):
                    return ('gray', '灰色')
                if row['CandleClose'] > row['ma_ema3']:
                    return ('green', '绿色')
                elif row['CandleClose'] < row['ma_ema3']:
                    return ('red', '红色')
                else:
                    return ('gray', '灰色')

            # 应用颜色判断，分别存储英文和中文
            color_results = df.apply(get_hama_color, axis=1)
            df['hama_color_en'] = [x[0] for x in color_results]
            df['hama_color_cn'] = [x[1] for x in color_results]

            # ===== 蜡烛/MA 关系 =====
            def get_candle_ma_status(row):
                if pd.isna(row['CandleClose']) or pd.isna(row['ma']):
                    return ('unknown', '未知')
                if row['CandleClose'] > row['ma']:
                    return ('candle_above_ma', 'MA上')
                elif row['CandleClose'] < row['ma']:
                    return ('candle_below_ma', 'MA下')
                else:
                    return ('equal', '重合')

            # 应用蜡烛/MA状态，分别存储英文和中文
            status_results = df.apply(get_candle_ma_status, axis=1)
            df['candle_ma_status_en'] = [x[0] for x in status_results]
            df['candle_ma_status_cn'] = [x[1] for x in status_results]

            # ===== 布林带状态 =====
            bb_width = (df['bb_upper'] - df['bb_lower']) / df['basis']

            def get_bb_status(val):
                if pd.isna(val):
                    return ('normal', '正常')
                if val < 0.1:
                    return ('squeeze', '收缩')
                elif val > 0.15:
                    return ('expansion', '扩张')
                else:
                    return ('normal', '正常')

            # 应用布林带状态，分别存储英文和中文
            bb_results = bb_width.apply(get_bb_status)
            df['bb_status_en'] = [x[0] for x in bb_results]
            df['bb_status_cn'] = [x[1] for x in bb_results]

            # ===== 交叉信号 =====
            cross_up = (df['CandleClose'] > df['ma']) & (df['CandleClose'].shift(1) <= df['ma'].shift(1))
            cross_down = (df['CandleClose'] < df['ma']) & (df['CandleClose'].shift(1) >= df['ma'].shift(1))

            # 查找最近一次交叉
            recent_cross_type = None
            recent_cross_type_cn = None
            recent_cross_time = None

            for i in range(len(df) - 1, max(0, len(df) - 100), -1):
                if cross_up.iloc[i]:
                    recent_cross_type = 'up'
                    recent_cross_type_cn = '涨'
                    recent_cross_time = datetime.fromtimestamp(df['open_time'].iloc[i] / 1000)
                    break
                elif cross_down.iloc[i]:
                    recent_cross_type = 'down'
                    recent_cross_type_cn = '跌'
                    recent_cross_time = datetime.fromtimestamp(df['open_time'].iloc[i] / 1000)
                    break

            # 最新数据
            latest = df.iloc[-1]

            # 获取颜色和趋势
            color_en = latest['hama_color_en']
            color_cn = latest['hama_color_cn']
            trend_cn = '上涨' if color_en == 'green' else '下跌' if color_en == 'red' else '盘整'

            # 格式化交叉时间
            cross_time_str = None
            if recent_cross_time:
                cross_time_str = recent_cross_time.strftime('%Y-%m-%d %H:%M')

            return {
                'price': float(latest['close']),
                # 中文显示
                'hama_color': color_cn,           # 绿色/红色/灰色
                'hama_trend': trend_cn,           # 上涨/下跌/盘整
                'candle_ma_status': latest['candle_ma_status_cn'],  # MA上/MA下/重合/未知
                'bb_status': latest['bb_status_cn'],              # 收缩/扩张/正常
                'last_cross_type': recent_cross_type_cn,          # 涨/跌
                # 数值
                'candle_close': float(latest['CandleClose']) if not pd.isna(latest['CandleClose']) else None,
                'ma': float(latest['ma']) if not pd.isna(latest['ma']) else None,
                'ma_ema3': float(latest['ma_ema3']) if not pd.isna(latest['ma_ema3']) else None,
                'bb_upper': float(latest['bb_upper']) if not pd.isna(latest['bb_upper']) else None,
                'bb_basis': float(latest['basis']) if not pd.isna(latest['basis']) else None,
                'bb_lower': float(latest['bb_lower']) if not pd.isna(latest['bb_lower']) else None,
                'bb_width_pct': float(bb_width.iloc[-1] * 100) if not pd.isna(bb_width.iloc[-1]) else None,
                'last_cross_time': cross_time_str,
                'calculation_time': datetime.now().isoformat(),
                'data_source': 'binance_api_local_calc'
            }

        except Exception as e:
            logger.error(f"计算 HAMA 指标失败: {e}")
            return self._empty_result()

    def calculate_for_symbol(self, symbol: str, interval: str = '15m') -> Dict[str, any]:
        """
        为单个币种计算 HAMA 指标

        Args:
            symbol: 币种符号
            interval: K线周期

        Returns:
            HAMA 指标数据字典
        """
        df = self.get_klines(symbol, interval)
        if df is None:
            return self._empty_result()

        result = self.calculate_hama(df)
        result['symbol'] = symbol
        result['interval'] = interval

        return result

    def calculate_batch(self, symbols: List[str], interval: str = '15m', max_workers: int = 5) -> Dict[str, Dict]:
        """
        批量计算多个币种的 HAMA 指标

        Args:
            symbols: 币种列表
            interval: K线周期
            max_workers: 最大并发数

        Returns:
            {symbol: hama_data} 字典
        """
        results = {}

        def calc_one(symbol):
            try:
                return symbol, self.calculate_for_symbol(symbol, interval)
            except Exception as e:
                logger.error(f"计算 {symbol} HAMA 失败: {e}")
                return symbol, self._empty_result()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(calc_one, symbol): symbol for symbol in symbols}

            for future in as_completed(futures):
                symbol, data = future.result()
                results[symbol] = data

        return results

    def _empty_result(self) -> Dict[str, any]:
        """返回空结果（中文）"""
        return {
            'price': None,
            'hama_color': '灰色',
            'hama_trend': '盘整',
            'candle_ma_status': '未知',
            'candle_close': None,
            'ma': None,
            'ma_ema3': None,
            'bb_upper': None,
            'bb_basis': None,
            'bb_lower': None,
            'bb_status': '正常',
            'bb_width_pct': None,
            'last_cross_type': None,
            'last_cross_time': None,
            'calculation_time': datetime.now().isoformat(),
            'data_source': 'binance_api_local_calc',
            'error': 'calculation_failed'
        }


# 全局单例
_calculator_futures = None
_calculator_spot = None


def get_hama_calculator(use_futures: bool = True) -> HAMABinanceCalculator:
    """
    获取 HAMA 计算器单例

    Args:
        use_futures: 是否使用合约市场

    Returns:
        HAMABinanceCalculator 实例
    """
    global _calculator_futures, _calculator_spot

    if use_futures:
        if _calculator_futures is None:
            _calculator_futures = HAMABinanceCalculator(use_futures=True)
        return _calculator_futures
    else:
        if _calculator_spot is None:
            _calculator_spot = HAMABinanceCalculator(use_futures=False)
        return _calculator_spot
