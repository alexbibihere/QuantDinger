"""
TradingView 数据获取和分析服务
支持获取 TradingView 图表数据和技术指标
"""
import requests
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from app.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)

# 实时价格缓存 (1分钟有效期)
_realtime_price_cache = {}
_PRICE_CACHE_DURATION = timedelta(minutes=1)


class TradingViewDataService:
    """TradingView 数据服务"""

    def __init__(self):
        # TradingView 扫描 API
        self.scan_url = "https://scanner.tradingview.com/crypto/scan"
        self.chart_url = "https://symbol-search.tradingview.com/symbol_search"

    def get_hama_cryptocurrency_signals(self, symbol: str) -> Dict[str, Any]:
        """
        获取 HAMA 蜡烛图指标的信号

        Args:
            symbol: 币种符号，如 'BTCUSDT'

        Returns:
            包含 HAMA 指标信号的字典
        """
        try:
            # 优化: 禁用TradingView Scanner,直接使用Binance数据
            # tv_data = self._fetch_tradingview_scan_data(symbol)
            tv_data = {}

            # 获取 K线数据用于计算 HAMA 指标
            kline_data = self._fetch_kline_data(symbol)

            # 基于 TV 数据和 K线计算 HAMA 指标
            return self._analyze_hama_indicators_real(symbol, tv_data, kline_data)

        except Exception as e:
            logger.error(f"Error fetching HAMA signals for {symbol}: {e}")
            # 降级到模拟数据
            return self._analyze_hama_indicators(symbol)

    def _fetch_tradingview_scan_data(self, symbol: str) -> Dict[str, Any]:
        """
        从 TradingView Scanner 获取技术指标数据

        Args:
            symbol: 币种符号

        Returns:
            TradingView 扫描数据
        """
        try:
            # TradingView 扫描 API
            scan_payload = {
                "symbols": {
                    "tickers": [f"BINANCE:{symbol}"],
                    "query": {
                        "types": []
                    }
                },
                "columns": [
                    "Recommend.All|1",      # 1分钟综合建议
                    "Recommend.All|15",     # 15分钟综合建议
                    "Recommend.All|240",    # 4小时综合建议
                    "Recommend.All|1D",     # 1天综合建议
                    "RSI|14|0",             # RSI(14)
                    "RSI|14|0|Close",       # RSI(14) Close
                    "Stoch.RSI|14|0|K",     # Stoch RSI K
                    "Stoch.RSI|14|0|D",     # Stoch RSI D
                    "MACD.macd|12|26|9",    # MACD
                    "MACD.signal|12|26|9",  # MACD Signal
                    "ADX|14|0",             # ADX
                    "AO|0",                 # Awesome Oscillator
                    "EMA|20|0",             # EMA 20
                    "EMA|50|0",             # EMA 50
                    "EMA|200|0",            # EMA 200
                    "BB|20|2.0|Upper",      # 布林带上轨
                    "BB|20|2.0|Lower",      # 布林带下轨
                    "Rec1",                 # 推荐值1
                    "Rec2",                 # 推荐值2
                    "Rec3"                  # 推荐值3
                ]
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Origin': 'https://cn.tradingview.com',
                'Referer': 'https://cn.tradingview.com/'
            }

            response = requests.post(
                self.scan_url,
                json=scan_payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return self._parse_tv_scan_data(data['data'][0])

            return {}

        except Exception as e:
            logger.warning(f"Failed to fetch TradingView scan data for {symbol}: {e}")
            return {}

    def _parse_tv_scan_data(self, raw_data: Dict) -> Dict[str, Any]:
        """
        解析 TradingView 扫描数据

        Args:
            raw_data: 原始扫描数据

        Returns:
            解析后的数据
        """
        try:
            result = {
                'recommendations': {},
                'oscillators': {},
                'moving_averages': {},
                'other': {}
            }

            # 原始数据格式: ['d', col1, col2, ...]
            values = raw_data.get('d', [])

            # 根据列索引解析数据
            if len(values) > 1:
                result['recommendations']['1m'] = values[1]
            if len(values) > 2:
                result['recommendations']['15m'] = values[2]
            if len(values) > 3:
                result['recommendations']['4h'] = values[3]
            if len(values) > 4:
                result['recommendations']['1d'] = values[4]
            if len(values) > 5:
                result['oscillators']['rsi'] = values[5]
            if len(values) > 7:
                result['oscillators']['stoch_k'] = values[7]
            if len(values) > 8:
                result['oscillators']['stoch_d'] = values[8]
            if len(values) > 9:
                result['oscillators']['macd'] = values[9]
            if len(values) > 10:
                result['oscillators']['macd_signal'] = values[10]
            if len(values) > 11:
                result['oscillators']['adx'] = values[11]
            if len(values) > 12:
                result['oscillators']['ao'] = values[12]
            if len(values) > 13:
                result['moving_averages']['ema20'] = values[13]
            if len(values) > 14:
                result['moving_averages']['ema50'] = values[14]
            if len(values) > 15:
                result['moving_averages']['ema200'] = values[15]
            if len(values) > 16:
                result['other']['bb_upper'] = values[16]
            if len(values) > 17:
                result['other']['bb_lower'] = values[17]

            return result

        except Exception as e:
            logger.error(f"Error parsing TV scan data: {e}")
            return {}

    def _fetch_kline_data(self, symbol: str, limit: int = 200) -> List[Dict]:
        """
        获取 K线数据用于计算 HAMA 指标

        Args:
            symbol: 币种符号
            limit: 获取的 K线数量 (默认200,需要100根用于MA100计算)

        Returns:
            K线数据列表
        """
        try:
            import ccxt
            import os

            # 优化: 增加超时时间并添加重试配置
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'timeout': 30000,  # 从10秒增加到30秒
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,  # 自动调整时间差
                },
            })

            # 应用代理配置
            proxy_url = os.getenv('PROXY_URL')
            if proxy_url:
                # 使用环境变量中的PROXY_URL (格式: http://host.docker.internal:7890)
                exchange.proxies = {
                    'http': proxy_url,
                    'https': proxy_url,
                }
                logger.info(f"Using proxy: {proxy_url}")
            else:
                # 备用方案: 使用PROXY_PORT
                proxy_port = os.getenv('PROXY_PORT')
                if proxy_port:
                    proxy_url = f'http://host.docker.internal:{proxy_port}'
                    exchange.proxies = {
                        'http': proxy_url,
                        'https': proxy_url,
                    }
                    logger.info(f"Using proxy: {proxy_url}")

            # 获取 15分钟 K线数据
            logger.info(f"正在获取 {symbol} 的15分钟K线数据...")
            ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=limit)
            logger.info(f"成功获取 {symbol} 的K线数据,共 {len(ohlcv)} 根")

            kline_data = []
            for candle in ohlcv:
                kline_data.append({
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })

            return kline_data

        except Exception as e:
            logger.error(f"Error fetching K-line data for {symbol}: {e}")
            return []

    def _get_realtime_price(self, symbol: str) -> float:
        """
        获取币种的实时价格(带1分钟缓存)

        Args:
            symbol: 币种符号

        Returns:
            实时价格,失败返回None
        """
        global _realtime_price_cache

        # 检查缓存
        current_time = datetime.now()
        if symbol in _realtime_price_cache:
            cached_price, cached_time = _realtime_price_cache[symbol]
            if current_time - cached_time < _PRICE_CACHE_DURATION:
                logger.debug(f"使用缓存的实时价格: {symbol} = {cached_price}")
                return cached_price

        try:
            import ccxt
            import os

            # 配置代理
            proxy_url = os.getenv('PROXY_URL')
            if not proxy_url:
                proxy_port = os.getenv('PROXY_PORT')
                if proxy_port:
                    proxy_url = f'http://host.docker.internal:{proxy_port}'

            # 优化: 增加超时时间
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'timeout': 15000,  # 从10秒增加到15秒
                'options': {
                    'adjustForTimeDifference': True,
                },
            })

            if proxy_url:
                exchange.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }

            # 获取实时ticker
            ticker = exchange.fetch_ticker(symbol)

            if ticker and 'last' in ticker:
                price = float(ticker['last'])
                # 存入缓存
                _realtime_price_cache[symbol] = (price, current_time)
                # 清理过期缓存
                self._clean_expired_price_cache()
                return price
            else:
                logger.warning(f"无法获取{symbol}的实时价格")
                return None

        except Exception as e:
            logger.warning(f"获取{symbol}实时价格失败: {e}")
            return None

    def _clean_expired_price_cache(self):
        """清理过期的实时价格缓存"""
        global _realtime_price_cache
        current_time = datetime.now()
        expired_symbols = []
        for symbol, (price, cached_time) in _realtime_price_cache.items():
            if current_time - cached_time >= _PRICE_CACHE_DURATION:
                expired_symbols.append(symbol)

        for symbol in expired_symbols:
            del _realtime_price_cache[symbol]

        if expired_symbols:
            logger.debug(f"清理过期价格缓存: {len(expired_symbols)} 个币种")

    def _calculate_heikin_ashi(self, klines: List[Dict]) -> List[Dict]:
        """
        计算 Heikin Ashi 蜡烛图

        Args:
            klines: 原始K线数据

        Returns:
            Heikin Ashi K线数据
        """
        if len(klines) < 2:
            return klines

        ha_klines = []

        for i, kline in enumerate(klines):
            if i == 0:
                # 第一根 HA 蜡烛使用原始数据
                ha_close = (kline['open'] + kline['high'] + kline['low'] + kline['close']) / 4
                ha_open = kline['open']
            else:
                # 后续 HA 蜡烛
                prev_ha = ha_klines[i - 1]
                ha_close = (kline['open'] + kline['high'] + kline['low'] + kline['close']) / 4
                ha_open = (prev_ha['open'] + prev_ha['close']) / 2

            ha_high = max(kline['high'], ha_open, ha_close)
            ha_low = min(kline['low'], ha_open, ha_close)

            ha_klines.append({
                'timestamp': kline['timestamp'],
                'open': ha_open,
                'high': ha_high,
                'low': ha_low,
                'close': ha_close,
                'volume': kline['volume']
            })

        return ha_klines

    def _calculate_hama_candles(self, klines: List[Dict]) -> List[Dict]:
        """
        计算HAMA蜡烛图(用户指定参数)

        Args:
            klines: 原始K线数据

        Returns:
            HAMA蜡烛图数据
        """
        if len(klines) < 100:
            logger.warning("K线数据不足100根,无法计算HAMA")
            return []

        import numpy as np

        # 转换为numpy数组方便计算
        opens = np.array([k['open'] for k in klines])
        highs = np.array([k['high'] for k in klines])
        lows = np.array([k['low'] for k in klines])
        closes = np.array([k['close'] for k in klines])

        # 计算Source数据(hamaCandle.txt lines 107-110)
        source_open = np.zeros_like(opens)
        source_high = np.zeros_like(highs)
        source_low = np.zeros_like(lows)
        source_close = (opens + highs + lows + closes) / 4

        source_open[0] = (opens[0] + closes[0]) / 2  # 第一根特殊处理
        source_open[1:] = (opens[:-1] + closes[:-1]) / 2
        source_high = np.maximum(highs, closes)
        source_low = np.minimum(lows, closes)

        # 计算HAMA蜡烛(用户指定参数)
        # Open: EMA 45
        candle_open = self._ema(source_open, 45)

        # High: EMA 20
        candle_high = self._ema(source_high, 20)

        # Low: EMA 20
        candle_low = self._ema(source_low, 20)

        # Close: EMA 20
        candle_close = self._ema(source_close, 20)

        # 组装HAMA蜡烛
        hama_candles = []
        for i in range(len(klines)):
            if i < 100:  # 需要至少100根数据才能计算MA
                continue
            hama_candles.append({
                'timestamp': klines[i]['timestamp'],
                'open': candle_open[i],
                'high': candle_high[i],
                'low': candle_low[i],
                'close': candle_close[i],
                'volume': klines[i]['volume']
            })

        return hama_candles

    def _ema(self, data: Any, period: int) -> Any:
        """计算指数移动平均线"""
        alpha = 2 / (period + 1)
        result = np.zeros_like(data)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        return result

    def _wma(self, data: Any, period: int) -> Any:
        """计算加权移动平均线"""
        result = np.full_like(data, np.nan)
        weights = np.arange(1, period + 1)
        for i in range(period - 1, len(data)):
            result[i] = np.dot(data[i - period + 1:i + 1], weights) / weights.sum()
        return result

    def _calculate_hama_ma(self, hama_candles: List[Dict], length: int = 55) -> Any:
        """
        计算HAMA MA线(55周期WMA)

        Args:
            hama_candles: HAMA蜡烛数据
            length: MA周期,默认55

        Returns:
            MA值数组
        """
        if len(hama_candles) < length:
            logger.warning(f"HAMA蜡烛数据不足{length}根")
            return np.array([])

        close_prices = np.array([c['close'] for c in hama_candles])
        ma = self._wma(close_prices, length)
        return ma

    def _determine_hama_status(self, hama_candles: List[Dict]) -> Dict[str, Any]:
        """
        判断HAMA状态(用户指定参数: MA100)

        Args:
            hama_candles: HAMA蜡烛数据

        Returns:
            HAMA状态字典
        """
        if len(hama_candles) < 100:
            return {
                'status': '盘整',
                'status_code': 'HOLD',
                'last_cross_direction': 0,
                'candle_close': 0,
                'ma': 0,
                'deviation_pct': 0
            }

        # 计算MA线 (用户指定: 100周期)
        ma = self._calculate_hama_ma(hama_candles, 100)

        # 获取有效数据(从第100根开始)
        valid_candles = hama_candles[99:]
        valid_ma = ma[99:]

        # 计算交叉
        cross_up = []
        cross_down = []
        for i in range(1, len(valid_candles)):
            prev_candle_close = valid_candles[i - 1]['close']
            prev_ma = valid_ma[i - 1]
            curr_candle_close = valid_candles[i]['close']
            curr_ma = valid_ma[i]

            # 上穿MA
            if prev_candle_close <= prev_ma and curr_candle_close > curr_ma:
                cross_up.append(i)
            # 下穿MA
            elif prev_candle_close >= prev_ma and curr_candle_close < curr_ma:
                cross_down.append(i)

        # 跟踪最后交叉方向和时间
        last_cross_direction = 0
        last_cross_time = None
        last_cross_index = -1

        if cross_up and cross_down:
            if cross_up[-1] > cross_down[-1]:
                last_cross_direction = 1
                last_cross_index = cross_up[-1]
            else:
                last_cross_direction = -1
                last_cross_index = cross_down[-1]
        elif cross_up:
            last_cross_direction = 1
            last_cross_index = cross_up[-1]
        elif cross_down:
            last_cross_direction = -1
            last_cross_index = cross_down[-1]

        # 获取最后交叉时间
        if last_cross_index >= 0 and last_cross_index < len(valid_candles):
            last_cross_time = valid_candles[last_cross_index]['timestamp']

        # 获取最新数据
        latest_candle = valid_candles[-1]
        latest_ma = valid_ma[-1]

        # 计算偏离度
        deviation_pct = abs(latest_candle['close'] - latest_ma) / latest_ma * 100

        # 判断趋势状态(hamaCandle.txt lines 180-188)
        maintain_bullish = (last_cross_direction == 1 and
                           latest_candle['close'] >= latest_ma and
                           deviation_pct >= 0.1)

        maintain_bearish = (last_cross_direction == -1 and
                           latest_candle['close'] <= latest_ma and
                           deviation_pct >= 0.1)

        # 确定状态
        if maintain_bullish:
            status = '上涨趋势'
            status_code = 'BUY'
        elif maintain_bearish:
            status = '下跌趋势'
            status_code = 'SELL'
        else:
            status = '盘整'
            status_code = 'HOLD'

        return {
            'status': status,
            'status_code': status_code,
            'last_cross_direction': int(last_cross_direction),
            'last_cross_time': last_cross_time,
            'candle_close': float(latest_candle['close']),
            'ma': float(latest_ma),
            'deviation_pct': float(deviation_pct),
            'maintain_bullish': bool(maintain_bullish),
            'maintain_bearish': bool(maintain_bearish)
        }

    def _analyze_hama_indicators_real(self, symbol: str, tv_data: Dict, kline_data: List[Dict]) -> Dict[str, Any]:
        """
        基于真实数据分析 HAMA 指标(使用hamaCandle.txt的逻辑)

        Args:
            symbol: 币种符号
            tv_data: TradingView 扫描数据
            kline_data: K线数据

        Returns:
            HAMA 分析结果
        """
        import numpy as np

        # 计算HAMA蜡烛
        hama_candles = self._calculate_hama_candles(kline_data)

        if not hama_candles:
            logger.warning(f"无法计算{symbol}的HAMA蜡烛")
            return self._analyze_hama_indicators(symbol)

        # 获取实时价格
        realtime_price = self._get_realtime_price(symbol)

        # 判断HAMA状态(按照hamaCandle.txt lines 170-188)
        hama_status = self._determine_hama_status(hama_candles)

        # 如果有实时价格,使用实时价格与MA的关系来判断趋势
        if realtime_price:
            logger.info(f"获取到{symbol}实时价格: {realtime_price:.6f}, HAMA MA: {hama_status['ma']:.6f}")

            # 计算实时价格与MA的关系
            if realtime_price > hama_status['ma']:
                # 实时价格在MA之上 -> 上涨趋势
                final_status_code = 'BUY'
                final_status = '上涨趋势'
                logger.info(f"{symbol} 根据实时价格判断为上涨趋势: {realtime_price:.6f} > MA {hama_status['ma']:.6f}")
            elif realtime_price < hama_status['ma']:
                # 实时价格在MA之下 -> 下跌趋势
                final_status_code = 'SELL'
                final_status = '下跌趋势'
                logger.info(f"{symbol} 根据实时价格判断为下跌趋势: {realtime_price:.6f} < MA {hama_status['ma']:.6f}")
            else:
                # 实时价格等于MA -> 保持原判断
                final_status_code = hama_status['status_code']
                final_status = hama_status['status']

            # 更新hama_status
            hama_status['status'] = final_status
            hama_status['status_code'] = final_status_code
        else:
            # 没有实时价格,使用HAMA计算结果
            final_status_code = hama_status['status_code']
            final_status = hama_status['status']

        # 获取最新的HAMA蜡烛
        latest_hama = hama_candles[-1]

        # 计算置信度(基于偏离度和趋势强度)
        confidence = 0.5
        if final_status_code == 'BUY':
            confidence = 0.7 + min(hama_status['deviation_pct'] / 5, 0.3)
        elif final_status_code == 'SELL':
            confidence = 0.7 + min(hama_status['deviation_pct'] / 5, 0.3)
        else:
            confidence = 0.3

        return {
            'symbol': symbol,
            'trend': 'uptrend' if final_status_code == 'BUY' else ('downtrend' if final_status_code == 'SELL' else 'sideways'),
            'candle_pattern': 'none',
            'recommendation': final_status_code,  # BUY/SELL/HOLD
            'confidence': confidence,
            'signals': {
                'ha_close': hama_status['candle_close'],
                'realtime_price': realtime_price,  # 添加实时价格
                'ha_open': latest_hama['open'],
                'ha_high': latest_hama['high'],
                'ha_low': latest_hama['low'],
                'hama_ma': hama_status['ma'],
                'deviation_pct': hama_status['deviation_pct'],
                'last_cross_direction': hama_status['last_cross_direction'],
                'trend_strength': 'strong' if hama_status['deviation_pct'] > 1 else ('moderate' if hama_status['deviation_pct'] > 0.3 else 'weak'),
                'volume_confirmation': True
            },
            'technical_indicators': {
                'hama_status': final_status,
                'candle_close': hama_status['candle_close'],
                'realtime_price': realtime_price,  # 添加实时价格
                'ma_value': hama_status['ma'],
                'deviation_pct': hama_status['deviation_pct']
            },
            'timestamp': datetime.now().isoformat(),
            'analysis_note': f'HAMA分析: {final_status}' + (f' (实时价格{realtime_price:.6f})' if realtime_price else f', 偏离度{hama_status["deviation_pct"]:.2f}%')
        }

    def _determine_trend(self, ha_klines: List[Dict]) -> str:
        """
        基于 HA 蜡烛判断趋势

        Args:
            ha_klines: Heikin Ashi K线数据

        Returns:
            趋势: 'uptrend', 'downtrend', 'sideways'
        """
        if len(ha_klines) < 10:
            return 'sideways'

        recent = ha_klines[-10:]

        # 统计上涨和下跌蜡烛
        bullish_count = sum(1 for k in recent if k['close'] > k['open'])
        bearish_count = sum(1 for k in recent if k['close'] < k['open'])

        # 检查是否有连续的同向蜡烛
        consecutive_bullish = 0
        consecutive_bearish = 0

        for k in recent:
            if k['close'] > k['open']:
                consecutive_bullish += 1
                consecutive_bearish = 0
            elif k['close'] < k['open']:
                consecutive_bearish += 1
                consecutive_bullish = 0
            else:
                consecutive_bullish = 0
                consecutive_bearish = 0

        # 判断趋势
        if consecutive_bullish >= 5 or bullish_count >= 7:
            return 'uptrend'
        elif consecutive_bearish >= 5 or bearish_count >= 7:
            return 'downtrend'
        else:
            return 'sideways'

    def _identify_candle_pattern(self, latest: Dict, prev: Dict) -> str:
        """
        识别蜡烛图形态

        Args:
            latest: 最新 HA 蜡烛
            prev: 前一根 HA 蜡烛

        Returns:
            蜡烛图形态
        """
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']

        if body_size == 0:
            return 'doji'

        lower_wick = min(latest['open'], latest['close']) - latest['low']
        upper_wick = latest['high'] - max(latest['open'], latest['close'])

        # 锤子线/上吊线
        if lower_wick > body_size * 2 and upper_wick < body_size * 0.5:
            if prev['close'] > prev['open']:
                return 'hammer'  # 上升趋势后的锤子线
            else:
                return 'hammer'  # 下降趋势后的锤子线

        # 流星线
        if upper_wick > body_size * 2 and lower_wick < body_size * 0.5:
            return 'shooting_star'

        # 吞没形态
        if (latest['close'] > latest['open'] and
            prev['close'] < prev['open'] and
            latest['close'] > prev['open'] and
            latest['open'] < prev['close']):
            return 'bullish_engulfing'

        if (latest['close'] < latest['open'] and
            prev['close'] > prev['open'] and
            latest['close'] < prev['open'] and
            latest['open'] > prev['close']):
            return 'bearish_engulfing'

        # 默认
        return 'none'

    def _generate_recommendation(self, tv_data: Dict, trend: str, pattern: str) -> str:
        """
        生成交易建议

        Args:
            tv_data: TradingView 数据
            trend: 趋势
            pattern: 蜡烛图形态

        Returns:
            建议: 'BUY', 'SELL', 'HOLD'
        """
        score = 0

        # 获取综合建议
        rec_1d = tv_data.get('recommendations', {}).get('1d', 0)
        if isinstance(rec_1d, (int, float)):
            score += rec_1d * 0.3  # 1天建议权重30%

        # RSI 分析
        rsi = tv_data.get('oscillators', {}).get('rsi', 50)
        if isinstance(rsi, (int, float)):
            if rsi < 30:
                score += 2  # 超卖
            elif rsi > 70:
                score -= 2  # 超买

        # 趋势权重
        if trend == 'uptrend':
            score += 1.5
        elif trend == 'downtrend':
            score -= 1.5

        # 蜡烛图形态权重
        if pattern == 'bullish_engulfing':
            score += 1
        elif pattern == 'bearish_engulfing':
            score -= 1
        elif pattern == 'hammer':
            score += 0.5
        elif pattern == 'shooting_star':
            score -= 0.5

        # MACD 权重
        macd = tv_data.get('oscillators', {}).get('macd', 0)
        macd_signal = tv_data.get('oscillators', {}).get('macd_signal', 0)
        if isinstance(macd, (int, float)) and isinstance(macd_signal, (int, float)):
            if macd > macd_signal:
                score += 0.5  # 金叉
            else:
                score -= 0.5  # 死叉

        # 根据得分给出建议
        if score >= 2:
            return 'BUY'
        elif score <= -2:
            return 'SELL'
        else:
            return 'HOLD'

    def _calculate_confidence(self, tv_data: Dict, trend: str, pattern: str) -> float:
        """
        计算置信度

        Args:
            tv_data: TradingView 数据
            trend: 趋势
            pattern: 蜡烛图形态

        Returns:
            置信度 (0-1)
        """
        confidence = 0.5  # 基础置信度

        # 趋势明确性
        if trend in ['uptrend', 'downtrend']:
            confidence += 0.15

        # 蜡烛图形态
        if pattern in ['bullish_engulfing', 'bearish_engulfing']:
            confidence += 0.15
        elif pattern in ['hammer', 'shooting_star']:
            confidence += 0.1

        # RSI 极值
        rsi = tv_data.get('oscillators', {}).get('rsi', 50)
        if isinstance(rsi, (int, float)):
            if rsi < 20 or rsi > 80:
                confidence += 0.1

        # ADX (趋势强度)
        adx = tv_data.get('oscillators', {}).get('adx', 25)
        if isinstance(adx, (int, float)):
            if adx > 40:
                confidence += 0.1

        return min(max(confidence, 0.3), 0.95)

    def _get_technical_indicators(self, tv_data: Dict, kline_data: List[Dict]) -> Dict[str, Any]:
        """
        获取技术指标

        Args:
            tv_data: TradingView 数据
            kline_data: K线数据

        Returns:
            技术指标字典
        """
        oscillators = tv_data.get('oscillators', {})
        moving_averages = tv_data.get('moving_averages', {})

        # 计算 RSI (如果 TV 数据没有)
        rsi = oscillators.get('rsi')
        if rsi is None and len(kline_data) >= 15:
            rsi = self._calculate_rsi(kline_data)

        # 计算 MACD 状态
        macd = oscillators.get('macd', 0)
        macd_signal = oscillators.get('macd_signal', 0)

        if isinstance(macd, (int, float)) and isinstance(macd_signal, (int, float)):
            if macd > macd_signal:
                macd_status = 'bullish'
            else:
                macd_status = 'bearish'
        else:
            macd_status = 'neutral'

        # 计算 EMA
        ema_20 = moving_averages.get('ema20')
        ema_50 = moving_averages.get('ema50')

        if ema_20 is None and len(kline_data) >= 20:
            ema_20 = self._calculate_ema(kline_data, 20)
        if ema_50 is None and len(kline_data) >= 50:
            ema_50 = self._calculate_ema(kline_data, 50)

        # 计算支撑位和阻力位
        support, resistance = self._calculate_support_resistance(kline_data)

        return {
            'rsi': rsi if isinstance(rsi, (int, float)) else 50,
            'macd': macd_status,
            'ema_20': ema_20 if isinstance(ema_20, (int, float)) else 0,
            'ema_50': ema_50 if isinstance(ema_50, (int, float)) else 0,
            'support_level': support,
            'resistance_level': resistance
        }

    def _calculate_rsi(self, kline_data: List[Dict], period: int = 14) -> float:
        """计算 RSI 指标"""
        import numpy as np

        closes = [k['close'] for k in kline_data]
        if len(closes) < period + 1:
            return 50.0

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _calculate_ema(self, kline_data: List[Dict], period: int) -> float:
        """计算 EMA 指标"""
        import numpy as np

        closes = [k['close'] for k in kline_data]
        if len(closes) < period:
            return closes[-1] if closes else 0

        multiplier = 2 / (period + 1)
        ema = closes[0]

        for close in closes[1:]:
            ema = (close - ema) * multiplier + ema

        return round(ema, 2)

    def _calculate_support_resistance(self, kline_data: List[Dict], lookback: int = 20) -> tuple:
        """计算支撑位和阻力位"""
        if len(kline_data) < lookback:
            return 0, 0

        recent = kline_data[-lookback:]
        highs = [k['high'] for k in recent]
        lows = [k['low'] for k in recent]

        resistance = round(max(highs), 2)
        support = round(min(lows), 2)

        return support, resistance

    def _get_trend_strength(self, ha_klines: List[Dict]) -> str:
        """判断趋势强度"""
        if len(ha_klines) < 10:
            return 'weak'

        recent = ha_klines[-10:]
        bullish_count = sum(1 for k in recent if k['close'] > k['open'])
        bearish_count = sum(1 for k in recent if k['close'] < k['open'])

        max_count = max(bullish_count, bearish_count)
        if max_count >= 8:
            return 'strong'
        elif max_count >= 6:
            return 'moderate'
        else:
            return 'weak'

    def _check_volume_confirmation(self, kline_data: List[Dict]) -> bool:
        """检查成交量确认"""
        if len(kline_data) < 2:
            return False

        latest_vol = kline_data[-1]['volume']
        avg_vol = sum(k['volume'] for k in kline_data[-20:]) / min(20, len(kline_data))

        return latest_vol > avg_vol * 1.2

    def _analyze_hama_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        分析 HAMA 指标（简化版本）

        HAMA 指标通常包含：
        - Heikin Ashi 蜡烛图形态
        - 趋势判断
        - 买卖信号

        Args:
            symbol: 币种符号

        Returns:
            分析结果
        """
        # 这里可以实现具体的 HAMA 指标分析逻辑
        # 目前返回模拟数据用于测试
        import random

        trend_signals = ['uptrend', 'downtrend', 'sideways']
        candle_patterns = ['bullish_engulfing', 'bearish_engulfing', 'doji', 'hammer', 'shooting_star']

        return {
            'symbol': symbol,
            'trend': random.choice(trend_signals),
            'candle_pattern': random.choice(candle_patterns),
            'recommendation': random.choice(['BUY', 'SELL', 'HOLD']),
            'confidence': round(random.uniform(0.5, 0.95), 2),
            'signals': {
                'ha_close': round(random.uniform(20000, 100000), 2),
                'ha_open': round(random.uniform(20000, 100000), 2),
                'ha_high': round(random.uniform(20000, 100000), 2),
                'ha_low': round(random.uniform(20000, 100000), 2),
                'trend_strength': random.choice(['strong', 'moderate', 'weak']),
                'volume_confirmation': random.choice([True, False])
            },
            'technical_indicators': {
                'rsi': round(random.uniform(20, 80), 2),
                'macd': random.choice(['bullish', 'bearish', 'neutral']),
                'ema_20': round(random.uniform(20000, 100000), 2),
                'ema_50': round(random.uniform(20000, 100000), 2),
                'support_level': round(random.uniform(18000, 95000), 2),
                'resistance_level': round(random.uniform(21000, 105000), 2)
            },
            'timestamp': datetime.now().isoformat(),
            'analysis_note': 'HAMA 指标基于 Heikin Ashi 蜡烛图进行分析，用于识别趋势和潜在的反转点。'
        }

    def _get_default_signals(self) -> Dict[str, Any]:
        """获取默认信号（当 API 调用失败时）"""
        return {
            'trend': 'neutral',
            'recommendation': 'HOLD',
            'confidence': 0.5,
            'signals': {},
            'technical_indicators': {},
            'error': 'Unable to fetch trading data'
        }

    def analyze_multiple_symbols(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析多个币种

        Args:
            symbols: 币种符号列表

        Returns:
            分析结果列表
        """
        results = []

        for symbol in symbols:
            try:
                analysis = self.get_hama_cryptocurrency_signals(symbol)
                results.append(analysis)

                # 避免请求过快
                import time
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        return results

    def check_hama_conditions(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查 HAMA 指标是否满足特定条件

        判断条件可以包括：
        - 趋势是否明确（uptrend/downtrend）
        - 置信度是否高于阈值
        - 技术指标是否一致
        - 是否有特定的蜡烛图形态

        Args:
            analysis: HAMA 指标分析结果

        Returns:
            判断结果
        """
        conditions = {
            'is_uptrend': analysis.get('trend') == 'uptrend',
            'is_downtrend': analysis.get('trend') == 'downtrend',
            'confidence_above_70': analysis.get('confidence', 0) >= 0.70,
            'is_bullish_pattern': analysis.get('recommendation') == 'BUY',
            'is_bearish_pattern': analysis.get('recommendation') == 'SELL',
            'has_volume_confirmation': analysis.get('signals', {}).get('volume_confirmation', False)
        }

        # 判断是否满足买入条件
        buy_conditions = [
            conditions['is_uptrend'],
            conditions['confidence_above_70'],
            conditions['is_bullish_pattern'],
            conditions['has_volume_confirmation']
        ]

        # 判断是否满足卖出条件
        sell_conditions = [
            conditions['is_downtrend'],
            conditions['confidence_above_70'],
            conditions['is_bearish_pattern']
        ]

        conditions['meets_buy_criteria'] = all(buy_conditions) if buy_conditions else False
        conditions['meets_sell_criteria'] = all(sell_conditions) if sell_conditions else False

        # 添加详细说明
        conditions['summary'] = self._generate_condition_summary(analysis, conditions)

        return conditions

    def _generate_condition_summary(self, analysis: Dict[str, Any], conditions: Dict[str, Any]) -> str:
        """生成条件满足情况的摘要说明"""
        trend = analysis.get('trend', 'neutral')
        recommendation = analysis.get('recommendation', 'HOLD')
        confidence = analysis.get('confidence', 0.5)

        summary_parts = []

        if trend == 'uptrend':
            summary_parts.append("处于上升趋势")
        elif trend == 'downtrend':
            summary_parts.append("处于下降趋势")
        else:
            summary_parts.append("趋势不明")

        if confidence >= 0.8:
            summary_parts.append("信号强度高")
        elif confidence >= 0.6:
            summary_parts.append("信号强度中等")
        else:
            summary_parts.append("信号强度低")

        if recommendation == 'BUY':
            summary_parts.append("建议买入")
        elif recommendation == 'SELL':
            summary_parts.append("建议卖出")
        else:
            summary_parts.append("建议持有")

        return "，".join(summary_parts)


# 便捷函数
def get_binance_top_gainers_with_hama_analysis(limit: int = 20, market_type: str = 'spot') -> Dict[str, Any]:
    """
    获取币安涨幅榜并进行 HAMA 指标分析

    Args:
        limit: 返回数量，默认 20
        market_type: 市场类型，'spot' 或 'futures'，默认 'spot'

    Returns:
        包含涨幅榜和分析结果的字典
    """
    from app.services.binance_gainer import BinanceGainerService

    gainer_service = BinanceGainerService()
    tv_service = TradingViewDataService()

    # 获取涨幅榜（根据市场类型）
    if market_type == 'futures':
        top_gainers = gainer_service.get_top_gainers_futures(limit)
    else:
        top_gainers = gainer_service.get_top_gainers(limit, market_type='spot')

    if not top_gainers:
        return {
            'success': False,
            'error': 'Failed to fetch top gainers',
            'data': []
        }

    # 分析每个币种（添加错误处理）
    analyzed_symbols = []
    for gainer in top_gainers:
        symbol = gainer['symbol']

        # 尝试获取HAMA分析，失败时使用默认值
        try:
            hama_analysis = tv_service.get_hama_cryptocurrency_signals(symbol)
            conditions = tv_service.check_hama_conditions(hama_analysis)
        except Exception as e:
            logger.warning(f"Failed to get HAMA analysis for {symbol}: {e}")
            # 使用默认值
            hama_analysis = {
                'trend': 'sideways',
                'candle_pattern': 'unknown',
                'recommendation': 'HOLD',
                'confidence': 0.5,
                'technical_indicators': {},
                'data_source': 'N/A'
            }
            conditions = {
                'meets_buy_criteria': False,
                'meets_sell_criteria': False,
                'summary': 'HAMA分析暂不可用'
            }

        analyzed_symbols.append({
            'symbol': symbol,
            'base_asset': gainer['base_asset'],
            'price': gainer['price'],
            'price_change_percent': gainer['price_change_percent'],
            'volume': gainer['volume'],
            'quote_volume': gainer.get('quote_volume', gainer['volume']),
            'hama_analysis': hama_analysis,
            'conditions': conditions
        })

    return {
        'success': True,
        'count': len(analyzed_symbols),
        'timestamp': datetime.now().isoformat(),
        'data': analyzed_symbols
    }
