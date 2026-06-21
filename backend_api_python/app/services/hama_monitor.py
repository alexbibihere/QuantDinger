#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 监控服务

⚠️ 已废弃 — 由 tv-bridge (hama_tv_service.py) 替代
"""

import logging

logger = logging.getLogger(__name__)
logger.warning("⚠️ hama_monitor.py 已废弃，使用 hama_tv_service.py 替代")


class HAMAMonitor:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        logger.info("HAMA Monitor 已禁用 (tv-bridge 模式)")

    def stop(self):
        pass

    def is_running(self):
        return False


def get_monitor(*args, **kwargs):
    return HAMAMonitor()
