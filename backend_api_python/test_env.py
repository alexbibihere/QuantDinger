#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试环境变量读取
"""
import os

print("="*60)
print("环境变量测试")
print("="*60)

env_vars = [
    'PROXY_PORT',
    'PROXY_HOST',
    'PROXY_URL',
    'ALL_PROXY',
    'HTTP_PROXY',
    'HTTPS_PROXY'
]

for var in env_vars:
    value = os.getenv(var)
    print(f"{var} = {value}")

print("="*60)
