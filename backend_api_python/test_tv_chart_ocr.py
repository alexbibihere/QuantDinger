#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import os

print('=' * 70)
print('TradingView 图表 OCR 识别测试')
print('=' * 70)

screenshot_dir = '../screenshot'
images = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]

print(f'\n找到 {len(images)} 张图表\n')

ocr = PaddleOCR(lang='ch')

# 测试每张图片
for i, img_file in enumerate(images[:2], 1):  # 只测试前2张
    img_path = os.path.join(screenshot_dir, img_file)

    print(f'\n[{i}] {img_file}')
    print('-' * 70)

    result = ocr.ocr(img_path)

    if result and len(result) > 0:
        img_result = result[0]
        if isinstance(img_result, list):
            print(f'识别到 {len(img_result)} 个文本块\n')

            all_texts = []
            for line in img_result:
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)):
                        all_texts.append(text_info[0])

            # 显示前20个
            for j, text in enumerate(all_texts[:20], 1):
                print(f'{j:2d}. {text}')

            if len(all_texts) > 20:
                print(f'\n... 还有 {len(all_texts) - 20} 个')

            # 提取价格
            import re
            full_text = ' '.join(all_texts)
            prices = re.findall(r'\d{1,6}[,.]?\d*', full_text)
            if prices:
                print(f'\n价格数据: {prices[:8]}')

print('\n' + '=' * 70)
print('✅ 测试完成')
print('=' * 70)
