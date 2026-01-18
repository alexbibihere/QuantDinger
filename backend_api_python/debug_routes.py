#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试路由问题
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app import create_app

app = create_app()

# 打印所有 hama-market 相关的路由
print("\n=== HAMA Market 路由 ===")
for rule in app.url_map.iter_rules():
    if 'hama-market' in rule.rule:
        print(f"{rule.methods} {rule.rule}")

# 测试路由
print("\n=== 测试路由 ===")
with app.app_context():
    with app.test_client() as client:
        # 1. 健康检查
        resp = client.get('/api/hama-market/health')
        print(f"GET /api/hama-market/health: {resp.status_code}")

        # 2. OCR capture
        resp = client.post('/api/hama-market/ocr/capture',
                          json={'symbol': 'BTCUSDT'},
                          content_type='application/json')
        print(f"POST /api/hama-market/ocr/capture: {resp.status_code}")
        print(f"Response: {resp.get_json() if resp.status_code == 200 else resp.data[:200]}")
