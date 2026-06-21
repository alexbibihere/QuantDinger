#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA Brave 浏览器监控服务

⚠️ 已废弃 — 由 tv-bridge (hama_tv_service.py) 替代

原功能: 使用 Playwright + RapidOCR 从 TradingView 图表识别 HAMA 指标
替代方案: hama_tv_service.py 通过 tv-bridge WebSocket 获取数据，更快更准更稳

保留此文件仅为兼容旧代码引用，所有方法均为空实现。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.warning("⚠️ hama_brave_monitor.py 已废弃，正在使用 hama_tv_service.py 替代")


class HamaBraveMonitor:
    """已废弃 — 由 tv-bridge 替代"""

    def __init__(self, *args, **kwargs):
        logger.info("HamaBraveMonitor 已禁用 (tv-bridge 模式)")

    def get_cached_hama(self, symbol: str) -> Optional[Dict[str, Any]]:
        return None

    def set_cached_hama(self, symbol: str, hama_data: Dict[str, Any]) -> bool:
        return False

    def start_monitoring(self, *args, **kwargs):
        logger.info("Brave 监控已禁用 (tv-bridge 模式)")

    def stop_monitoring(self):
        pass

    def start_continuous_monitoring(self, *args, **kwargs):
        logger.info("Brave 持续监控已禁用 (tv-bridge 模式)")

    def get_cache_stats(self):
        return {"status": "disabled", "source": "tv-bridge"}


# 全局单例
_brave_monitor_instance = None


def get_brave_monitor(*args, **kwargs):
    global _brave_monitor_instance
    if _brave_monitor_instance is None:
        _brave_monitor_instance = HamaBraveMonitor()
    return _brave_monitor_instance
