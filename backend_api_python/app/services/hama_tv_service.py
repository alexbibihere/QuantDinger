#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA TV Service — 通过 TradingView-API WebSocket 桥接层获取 HAMA 指标

替代 OCR 截图方案，直接从 TradingView 获取 OHLCV 数据，本地计算 HAMA 指标。

流程:
  1. Flask 调用 tv-bridge HTTP API (localhost:3456)
  2. tv-bridge 通过 SOCKS5 代理连接 TradingView WebSocket
  3. 获取 OHLCV K 线数据（最多 500 根）
  4. Flask 端 HAMACalculator 计算完整 HAMA 指标
  5. 返回结构化的 HAMA 结果

优点:
  ✅ 比 OCR 快 5-10 倍（1-2s vs 8-15s）
  ✅ 数据精准无 OCR 误差
  ✅ 无浏览器截图的反爬风险
  ✅ 支持多品种多时间框架
  ✅ tv-bridge 不可用时自动降级到 OCR

降级机制:
  当 tv-bridge 连续 3 次请求失败时，自动切换回 OCR 方式。
  每 60 秒尝试恢复 tv-bridge 连接，成功后切回。
"""

import requests
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from app.utils.http import get_retry_session
from app.services.hama_calculator import HAMACalculator

logger = logging.getLogger(__name__)

# tv-bridge 服务地址
TV_BRIDGE_URL = "http://localhost:3456"


class HAMATVService:
    """通过 TV-Bridge 获取 HAMA 指标的服务"""

    def __init__(self):
        self.calculator = HAMACalculator()
        self.http_session = get_retry_session(retries=2, backoff_factor=0.3)
        # 降级状态
        self._degraded = False
        self._consecutive_failures = 0
        self._max_failures = 3
        self._last_attempt_time = 0
        self._recovery_interval = 60  # 60秒尝试恢复

        # 启动后台健康检查线程
        self._start_health_check()

    def get_ohlcv_from_tv_bridge(
        self,
        symbol: str,
        timeframe: str = "D",
        range_count: int = 500,
        timeout: int = 20,
    ) -> Optional[List[Dict]]:
        """
        从 tv-bridge 获取 OHLCV K 线数据

        包含自动降级逻辑：
          - 连续 _max_failures 次失败 → 进入降级模式
          - 降级后每 _recovery_interval 秒尝试恢复
        """
        # 降级检查
        now = time.time()
        if self._degraded:
            if now - self._last_attempt_time < self._recovery_interval:
                logger.warning(f"⚠️ [降级] tv-bridge 不可用，跳过请求 {symbol}")
                return None
            else:
                logger.info(f"🔄 [降级恢复] 尝试恢复 tv-bridge 连接...")
                self._degraded = False
                self._consecutive_failures = 0

        full_symbol = f"BINANCE:{symbol}"
        url = f"{TV_BRIDGE_URL}/chart"

        try:
            logger.info(
                f"从 tv-bridge 获取数据: {full_symbol} ({timeframe}, range={range_count})"
            )
            resp = self.http_session.get(
                url,
                params={
                    "symbol": full_symbol,
                    "timeframe": timeframe,
                    "range": range_count,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            if "periods" not in data or not data["periods"]:
                logger.warning(f"tv-bridge 返回空数据: {full_symbol}")
                return None

            periods = data["periods"]
            logger.info(
                f"✅ 获取到 {len(periods)} 根 K 线: {full_symbol} ({timeframe})"
            )
            return periods

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接 tv-bridge ({TV_BRIDGE_URL})，服务未启动？")
            self._record_failure()
            return None
        except requests.exceptions.Timeout:
            logger.error(f"⏰ tv-bridge 请求超时: {full_symbol}")
            self._record_failure()
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ tv-bridge 请求失败: {e}")
            self._record_failure()
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"❌ tv-bridge 返回数据解析失败: {e}")
            self._record_failure()
            return None

    def _record_failure(self):
        """记录一次失败，达到阈值后进入降级模式"""
        self._consecutive_failures += 1
        self._last_attempt_time = time.time()
        if self._consecutive_failures >= self._max_failures:
            self._degraded = True
            logger.warning(
                f"⚠️ tv-bridge 连续 {self._max_failures} 次失败，"
                f"已切换到降级模式，{self._recovery_interval}s 后尝试恢复"
            )

    def is_degraded(self):
        """是否处于降级模式（tv-bridge 不可用）"""
        return self._degraded

    def reset_status(self):
        """手动重置降级状态"""
        self._degraded = False
        self._consecutive_failures = 0

    def _start_health_check(self):
        """启动后台线程，每30秒检查tv-bridge健康状态"""
        def check_loop():
            while True:
                try:
                    resp = requests.get(f"{TV_BRIDGE_URL}/health", timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        tv_ok = data.get("tvConnected", False)
                        if tv_ok and self._degraded:
                            logger.info("🔄 tv-bridge 已恢复，退出降级模式")
                            self.reset_status()
                        elif not tv_ok and not self._degraded:
                            logger.warning("⚠️ tv-bridge 还在但 TV WebSocket 未连接")
                except requests.exceptions.ConnectionError:
                    if not self._degraded:
                        logger.warning("⚠️ tv-bridge 健康检查失败")
                        self._record_failure()
                except Exception as e:
                    logger.debug(f"tv-bridge 健康检查异常: {e}")
                time.sleep(30)

        thread = threading.Thread(target=check_loop, daemon=True, name="tv-bridge-health")
        thread.start()

    def _periods_to_dataframe(self, periods: List[Dict]) -> pd.DataFrame:
        """
        将 tv-bridge 返回的 periods 转换为 DataFrame

        tv-bridge 返回格式: [{time, open, max, min, close, volume}, ...]
        需要转换成: [{time, open, high, low, close, volume}, ...]
        """
        rows = []
        for p in periods:
            rows.append(
                {
                    "time": p.get("time"),
                    "open": float(p.get("open", 0)),
                    "high": float(p.get("max", p.get("high", 0))),
                    "low": float(p.get("min", p.get("low", 0))),
                    "close": float(p.get("close", 0)),
                    "volume": float(p.get("volume", 0)),
                }
            )

        df = pd.DataFrame(rows)
        # 按时间升序排列（tv-bridge 可能返回降序）
        df = df.sort_values("time").reset_index(drop=True)
        return df

    def get_hama(
        self,
        symbol: str,
        timeframe: str = "D",
        range_count: int = 500,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        """
        获取 HAMA 指标（主要入口）

        Args:
            symbol: 品种符号，如 "BTCUSDT"
            timeframe: 时间周期
            range_count: K 线数量
            timeout: 超时时间

        Returns:
            HAMA 指标数据
        """
        # 1. 获取 OHLCV 数据
        periods = self.get_ohlcv_from_tv_bridge(
            symbol=symbol, timeframe=timeframe, range_count=range_count, timeout=timeout
        )
        if not periods:
            return {
                "success": False,
                "error": "无法从 tv-bridge 获取 OHLCV 数据",
                "symbol": symbol,
                "fallback": True,
            }

        # 2. 转换为 DataFrame
        df = self._periods_to_dataframe(periods)

        # 3. 检查数据量是否足够
        min_required = max(self.calculator.ma_length, self.calculator.close_length)
        if len(df) < min_required:
            return {
                "success": False,
                "error": f"数据不足，需要至少 {min_required} 根，当前 {len(df)} 根",
                "symbol": symbol,
                "data_count": len(df),
                "fallback": True,
            }

        # 4. 用 HAMACalculator 计算完整 HAMA
        try:
            df_result = self.calculator.calculate_hama(df)
        except Exception as e:
            logger.error(f"HAMA 计算失败: {e}")
            return {
                "success": False,
                "error": f"HAMA 计算异常: {str(e)}",
                "symbol": symbol,
            }

        # 5. 提取最新数据
        last = df_result.iloc[-1]

        # 构建返回数据
        result = {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "source": "tradingview-api-websocket",
            # 最新 K 线
            "price": float(last["close"]),
            "open": float(last["open"]),
            "high": float(last["high"]),
            "low": float(last["low"]),
            "volume": float(last["volume"]) if "volume" in last else 0,
            # HAMA 蜡烛
            "hama_open": float(last["hama_open"]),
            "hama_high": float(last["hama_high"]),
            "hama_low": float(last["hama_low"]),
            "hama_close": float(last["hama_close"]),
            "hama_ma": float(last["hama_ma"]),
            "hama_color": last["hama_color"],
            # 交叉信号
            "cross_up": bool(last["hama_cross_up"]),
            "cross_down": bool(last["hama_cross_down"]),
            # MA 趋势
            "hama_rising": bool(last["hama_rising"]),
            "hama_falling": bool(last["hama_falling"]),
            # 布林带
            "bb_upper": float(last["bb_upper"]),
            "bb_basis": float(last["bb_basis"]),
            "bb_lower": float(last["bb_lower"]),
            "bb_width": float(last["bb_width"]),
            "bb_squeeze": bool(last["bb_squeeze"]),
            "bb_expansion": bool(last["bb_expansion"]),
        }

        # 涨跌幅
        if len(df_result) > 1:
            prev = df_result.iloc[-2]
            result["change_pct"] = round(
                (last["close"] - prev["close"]) / prev["close"] * 100, 2
            )
        else:
            result["change_pct"] = 0.0

        logger.info(
            f"✅ HAMA 计算完成: {symbol} ({timeframe}) "
            f"价={last['close']:.2f} 色={last['hama_color']} "
            f"金叉={last['hama_cross_up']} 死叉={last['hama_cross_down']}"
        )

        return result

    def batch_get_hama(
        self,
        symbols: List[str],
        timeframe: str = "D",
        range_count: int = 500,
    ) -> Dict[str, Any]:
        """
        批量获取多个品种的 HAMA 指标

        Args:
            symbols: 品种列表，如 ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            timeframe: 时间周期
            range_count: K 线数量

        Returns:
            批量 HAMA 结果
        """
        results = {}
        errors = {}

        for i, symbol in enumerate(symbols):
            logger.info(f"批量 HAMA [{i+1}/{len(symbols)}]: {symbol}")
            try:
                result = self.get_hama(
                    symbol=symbol,
                    timeframe=timeframe,
                    range_count=range_count,
                )
                if result.get("success"):
                    results[symbol] = result
                else:
                    errors[symbol] = result.get("error", "未知错误")
            except Exception as e:
                errors[symbol] = str(e)
                logger.error(f"批量 HAMA 异常: {symbol} - {e}")

        return {
            "success": len(results) > 0,
            "total": len(symbols),
            "success_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
        }


# 全局单例
hama_tv_service = HAMATVService()
