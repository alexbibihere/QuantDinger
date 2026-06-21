#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图缓存

⚠️ 已废弃 — OCR/浏览器截图已禁用（由 tv-bridge 替代）
"""

import logging

logger = logging.getLogger(__name__)


class ScreenshotCache:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        return False


def get_screenshot_cache(*args, **kwargs):
    return ScreenshotCache()
