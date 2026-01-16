#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR 识别演示 - 测试 TradingView 图表
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import os

print('=' * 70)
print(' ' * 15 + '🔍 OCR 识别演示 - TradingView 图表')
print('=' * 70)

# 查找测试图片
screenshot_dir = './screenshot'
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)
    print(f'\n⚠️  未找到 {screenshot_dir} 目录,已创建')
    print('💡 请将 TradingView 图表截图放到该目录')
    exit(0)

# 获取所有图片
images = [f for f in os.listdir(screenshot_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

if not images:
    print(f'\n⚠️  {screenshot_dir} 目录中没有图片')
    print('💡 请将 TradingView 图表截图放到该目录')
    exit(0)

print(f'\n📸 找到 {len(images)} 张图片\n')

# 初始化 OCR
print('⚙️  初始化 PaddleOCR...')
ocr = PaddleOCR(lang='ch')
print('✅ OCR 初始化完成\n')

# 处理每张图片
for i, img_file in enumerate(images, 1):
    img_path = os.path.join(screenshot_dir, img_file)

    print(f'[{i}/{len(images)}] 处理: {img_file}')
    print('─' * 70)

    # OCR 识别
    result = ocr.ocr(img_path)

    if result and len(result) > 0:
        img_result = result[0]
        if isinstance(img_result, list) and len(img_result) > 0:
            print(f'✅ 识别到 {len(img_result)} 个文本块\n')

            # 提取所有文本
            all_texts = []
            for line in img_result:
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                        text = text_info[0]
                        all_texts.append(text)

            # 显示前10个文本
            display_count = min(10, len(all_texts))
            print(f'前 {display_count} 个识别结果:')
            print()

            for j in range(display_count):
                print(f'  {j+1}. {all_texts[j]}')

            if len(all_texts) > display_count:
                print(f'\n  ... 还有 {len(all_texts) - display_count} 个文本块')

            # 完整文本
            full_text = ' '.join(all_texts)
            print(f'\n📄 完整文本 (前200字符):')
            print(f'  {full_text[:200]}{"..." if len(full_text) > 200 else ""}')

            # 尝试提取价格信息
            import re
            prices = re.findall(r'[\d,]+\.?\d*[kKmMbB]?', full_text)
            if prices:
                print(f'\n💰 发现的价格数据: {", ".join(prices[:5])}')

        else:
            print('❌ 识别失败')
    else:
        print('❌ 未识别到文本')

    print('\n')

print('=' * 70)
print('✅ 处理完成!')
print('=' * 70)
