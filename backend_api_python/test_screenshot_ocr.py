#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import os
import re

print('=' * 70)
print('TradingView 图表 OCR 识别测试')
print('=' * 70)

screenshot_dir = '../screenshot'
images = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]

if not images:
    print('❌ 没有找到截图')
    exit(0)

# 选择最新的截图
images_with_time = [(f, os.path.getmtime(os.path.join(screenshot_dir, f))) for f in images]
images_with_time.sort(key=lambda x: x[1], reverse=True)
latest_image = images_with_time[0][0]
img_path = os.path.join(screenshot_dir, latest_image)

print(f'\n测试图片: {latest_image}')
print(f'文件大小: {os.path.getsize(img_path) / 1024:.1f} KB')
print('-' * 70)

# 使用英文模型
print('\n初始化 PaddleOCR (英文模型)...')
ocr = PaddleOCR(lang='en')
print('✅ 就绪\n')

print('开始识别...\n')
result = ocr.ocr(img_path)

if result and len(result) > 0:
    ocr_result = result[0]

    # 获取文本
    texts = []

    if hasattr(ocr_result, 'rec_texts'):
        texts = ocr_result.rec_texts
    elif isinstance(ocr_result, dict):
        for key, value in ocr_result.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
                texts = value
                break

    if texts:
        print(f'✅ 识别到 {len(texts)} 个文本块\n')
        print('=' * 70)
        print('识别结果:')
        print('=' * 70 + '\n')

        for i, text in enumerate(texts[:50], 1):
            print(f'{i:2d}. {text}')

        # 完整文本
        full_text = ' '.join(texts)
        print(f'\n完整文本 (前500字符):')
        print('-' * 70)
        print(full_text[:500])

        # 价格数据
        prices = re.findall(r'\d{1,6}[,.]?\d{0,2}', full_text)
        print(f'\n发现的价格数据: {prices[:20]}')

        # HAMA 相关
        keywords = ['HAMA', 'hama', 'Heiken', 'Ashi', 'MA', 'EMA', 'BB']
        found = [text for text in texts if any(k in text for k in keywords)]
        if found:
            print(f'\n指标相关信息:')
            for item in found:
                print(f'  - {item}')

    else:
        print('❌ 无法提取文本')
        if isinstance(ocr_result, dict):
            print('所有键:', list(ocr_result.keys())[:20])

else:
    print('❌ OCR 识别失败')

print('\n' + '=' * 70)
