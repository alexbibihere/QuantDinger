#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 指标本地计算服务

基于 TradingView 的 Pine Script 代码实现：
"NDT HAMA Candles with Bollinger Bands"

参考文件: backend_api_python/file/hamaAicoin.txt
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HAMACalculator:
    """HAMA 指标计算器"""

    def __init__(self):
        """初始化 HAMA 计算器"""
        # HAMA 参数（与 Pine Script 完全一致）
        self.open_length = 45  # 开盘价 EMA 周期
        self.high_length = 20  # 最高价 EMA 周期
        self.low_length = 20   # 最低价 EMA 周期
        self.close_length = 40  # 收盘价 WMA 周期（注意：WMA）
        self.ma_length = 100    # MA WMA 长度（注意：WMA）

        # 布林带参数
        self.bb_length = 400   # 布林带 SMA 周期（注意：SMA）
        self.bb_mult = 2.0     # 标准差倍数

        logger.info(f"HAMA 计算器初始化: Open=EMA({self.open_length}), High=EMA({self.high_length}), "
                   f"Low=EMA({self.low_length}), Close=WMA({self.close_length}), MA=WMA({self.ma_length}), BB=SMA({self.bb_length})")

    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线 (EMA)

        Args:
            data: 价格序列
            period: EMA 周期

        Returns:
            EMA 序列
        """
        return data.ewm(span=period, adjust=False).mean()

    def calculate_wma(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算加权移动平均线 (WMA)

        Args:
            data: 价格序列
            period: WMA 周期

        Returns:
            WMA 序列
        """
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum() if len(x) == period else np.nan,
            raw=True
        )

    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算简单移动平均线 (SMA)

        Args:
            data: 价格序列
            period: SMA 周期

        Returns:
            SMA 序列
        """
        return data.rolling(window=period).mean()

    def calculate_hama(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 HAMA 指标

        Args:
            df: K线数据，包含 open, high, low, close 列

        Returns:
            添加了 HAMA 指标的 DataFrame
        """
        if df.empty or len(df) < max(self.ma_length, self.close_length):
            logger.warning(f"数据不足，至少需要 {max(self.ma_length, self.close_length)} 条 K线数据")
            return df

        logger.info(f"开始计算 HAMA 指标，数据量: {len(df)} 条")

        # 1. 计算 HAMA 源数据
        # SourceOpen = (前一根K线的开盘价 + 前一根K线的收盘价) / 2
        df['source_open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2

        # SourceHigh = max(当前最高价, 当前收盘价)
        df['source_high'] = df[['high', 'close']].max(axis=1)

        # SourceLow = min(当前最低价, 当前收盘价)
        df['source_low'] = df[['low', 'close']].min(axis=1)

        # SourceClose = (开盘价 + 最高价 + 最低价 + 收盘价) / 4
        df['source_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

        # 2. 计算 HAMA 蜡烛图
        df['hama_open'] = self.calculate_ema(df['source_open'], self.open_length)
        df['hama_high'] = self.calculate_ema(df['source_high'], self.high_length)
        df['hama_low'] = self.calculate_ema(df['source_low'], self.low_length)
        df['hama_close'] = self.calculate_wma(df['source_close'], self.close_length)  # 使用 WMA

        # 3. 计算 HAMA MA 线（使用 WMA，与 Pine Script 一致）
        df['hama_ma'] = self.calculate_wma(df['close'], self.ma_length)

        # 4. 判断颜色/趋势
        # 如果 HAMA Open > 前一根 HAMA Open，则为绿色（上涨），否则为红色（下跌）
        df['hama_color'] = df.apply(
            lambda row: 'green' if row['hama_open'] > row.get('hama_open_prev', row['hama_open']) else 'red',
            axis=1
        )

        # 保存前一根 HAMA Open 用于下次比较
        df['hama_open_prev'] = df['hama_open'].shift(1)

        # 5. 判断交叉信号
        # 金叉：HAMA Close 上穿 HAMA MA
        df['hama_cross_up'] = (
            (df['hama_close'] > df['hama_ma']) &
            (df['hama_close'].shift(1) <= df['hama_ma'].shift(1))
        )

        # 死叉：HAMA Close 下穿 HAMA MA
        df['hama_cross_down'] = (
            (df['hama_close'] < df['hama_ma']) &
            (df['hama_close'].shift(1) >= df['hama_ma'].shift(1))
        )

        # 6. 计算布林带（使用 SMA，与 Pine Script 一致）
        df['bb_basis'] = self.calculate_sma(df['close'], self.bb_length)
        df['bb_dev'] = df['close'].rolling(window=self.bb_length).std()
        df['bb_upper'] = df['bb_basis'] + df['bb_dev'] * self.bb_mult
        df['bb_lower'] = df['bb_basis'] - df['bb_dev'] * self.bb_mult

        # 7. 布林带状态
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_basis']
        df['bb_squeeze'] = df['bb_width'] < 0.1  # 布林带收缩
        df['bb_expansion'] = df['bb_width'] > 0.15  # 布林带扩张

        # 8. MA 趋势
        df['hama_rising'] = df['hama_ma'] > df['hama_ma'].shift(1)
        df['hama_falling'] = df['hama_ma'] < df['hama_ma'].shift(1)

        logger.info("HAMA 指标计算完成")

        return df

    def get_latest_hama(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        获取最新的 HAMA 指标值

        Args:
            df: K线数据

        Returns:
            最新的 HAMA 指标数据
        """
        if df.empty:
            return None

        # 计算 HAMA 指标
        df_with_hama = self.calculate_hama(df)

        if df_with_hama.empty:
            return None

        # 获取最后一行数据
        latest = df_with_hama.iloc[-1]

        result = {
            'timestamp': latest.name if hasattr(latest.name, 'timestamp') else None,
            'open': float(latest['open']) if pd.notna(latest['open']) else None,
            'high': float(latest['high']) if pd.notna(latest['high']) else None,
            'low': float(latest['low']) if pd.notna(latest['low']) else None,
            'close': float(latest['close']) if pd.notna(latest['close']) else None,
            'hama': {
                'open': float(latest['hama_open']) if pd.notna(latest['hama_open']) else None,
                'high': float(latest['hama_high']) if pd.notna(latest['hama_high']) else None,
                'low': float(latest['hama_low']) if pd.notna(latest['hama_low']) else None,
                'close': float(latest['hama_close']) if pd.notna(latest['hama_close']) else None,
                'ma': float(latest['hama_ma']) if pd.notna(latest['hama_ma']) else None,
                'color': latest['hama_color'] if pd.notna(latest['hama_color']) else 'gray',
                'cross_up': bool(latest['hama_cross_up']) if pd.notna(latest['hama_cross_up']) else False,
                'cross_down': bool(latest['hama_cross_down']) if pd.notna(latest['hama_cross_down']) else False,
            },
            'bollinger_bands': {
                'upper': float(latest['bb_upper']) if pd.notna(latest['bb_upper']) else None,
                'basis': float(latest['bb_basis']) if pd.notna(latest['bb_basis']) else None,
                'lower': float(latest['bb_lower']) if pd.notna(latest['bb_lower']) else None,
                'width': float(latest['bb_width']) if pd.notna(latest['bb_width']) else None,
                'squeeze': bool(latest['bb_squeeze']) if pd.notna(latest['bb_squeeze']) else False,
                'expansion': bool(latest['bb_expansion']) if pd.notna(latest['bb_expansion']) else False,
            },
            'trend': {
                'rising': bool(latest['hama_rising']) if pd.notna(latest['hama_rising']) else False,
                'falling': bool(latest['hama_falling']) if pd.notna(latest['hama_falling']) else False,
            }
        }

        # 趋势判断
        if result['hama']['color'] == 'green':
            result['trend']['direction'] = 'up'
        elif result['hama']['color'] == 'red':
            result['trend']['direction'] = 'down'
        else:
            result['trend']['direction'] = 'neutral'

        return result


# 全局实例
hama_calculator = HAMACalculator()


def calculate_hama_from_ohlcv(ohlcv_data: list) -> Optional[Dict[str, Any]]:
    """
    从 OHLCV 数据计算 HAMA 指标

    Args:
        ohlcv_data: OHLCV 数据列表，格式: [[timestamp, open, high, low, close, volume], ...]

    Returns:
        最新的 HAMA 指标数据
    """
    if not ohlcv_data or len(ohlcv_data) < 100:
        logger.warning(f"数据不足，至少需要 100 条 OHLCV 数据，当前: {len(ohlcv_data) if ohlcv_data else 0}")
        return None

    try:
        # 转换为 DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # 计算指标
        result = hama_calculator.get_latest_hama(df)

        return result

    except Exception as e:
        logger.error(f"计算 HAMA 指标失败: {e}")
        return None


if __name__ == '__main__':
    # 测试代码
    print("HAMA 计算器测试")

    # 生成模拟数据
    import random
    from datetime import datetime, timedelta

    # 生成 500 根 K线数据
    base_price = 3000
    ohlcv_data = []

    for i in range(500):
        timestamp = int((datetime.now() - timedelta(minutes=500-i)).timestamp() * 1000)

        # 随机生成 OHLC
        open_price = base_price + random.uniform(-50, 50)
        close_price = base_price + random.uniform(-50, 50)
        high_price = max(open_price, close_price) + random.uniform(0, 20)
        low_price = min(open_price, close_price) - random.uniform(0, 20)
        volume = random.uniform(100, 1000)

        ohlcv_data.append([timestamp, open_price, high_price, low_price, close_price, volume])

        # 更新基准价格
        base_price = close_price

    # 计算 HAMA
    result = calculate_hama_from_ohlcv(ohlcv_data)

    if result:
        print("\\n" + "="*60)
        print("HAMA 指标计算结果:")
        print("="*60)
        print(f"价格: {result['close']:.2f}")
        print(f"\\nHAMA 蜡烛图:")
        print(f"  开盘: {result['hama']['open']:.2f}")
        print(f"  最高: {result['hama']['high']:.2f}")
        print(f"  最低: {result['hama']['low']:.2f}")
        print(f"  收盘: {result['hama']['close']:.2f}")
        print(f"  MA:   {result['hama']['ma']:.2f}")
        print(f"  颜色: {result['hama']['color']}")
        print(f"\\n趋势: {result['trend']['direction']}")
        if result['hama']['cross_up']:
            print("  信号: 🟢 金叉（买入信号）")
        elif result['hama']['cross_down']:
            print("  信号: 🔴 死叉（卖出信号）")
        print("="*60)
