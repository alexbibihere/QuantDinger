#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR 识别测试报告
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import requests
import os

print('=' * 70)
print(' ' * 20 + 'OCR 识别测试报告')
print('=' * 70)

# 测试图片 URL
img_url = 'https://maas-log-prod.cn-wlcb.ufileos.com/anthropic/82535413-f275-40d3-951a-d545bf6862f5/39df8f3fbfc8361bee144e62b9ba0865.png?UCloudPublicKey=TOKEN_e15ba47a-d098-4fbd-9afc-a0dcf0e4e621&Expires=1768555843&Signature=h9GsX43Bi63IPGEH+XI+v8Nbj3M='

print('\n【步骤 1】下载图片')
print('-' * 70)
response = requests.get(img_url)
img_path = './test_ocr_temp.png'
with open(img_path, 'wb') as f:
    f.write(response.content)
print(f'✅ 图片已保存: {img_path}')
print(f'   文件大小: {len(response.content):,} bytes ({len(response.content)/1024:.1f} KB)')

print('\n【步骤 2】初始化 PaddleOCR')
print('-' * 70)
ocr = PaddleOCR(lang='ch')
print('✅ PaddleOCR 初始化完成')

print('\n【步骤 3】执行 OCR 识别')
print('-' * 70)
result = ocr.ocr(img_path)

if result and result[0]:
    print(f'✅ 成功识别到 {len(result[0])} 个文本块\n')

    print('识别详情:')
    print('┌' + '─' * 66 + '┐')

    for i, line in enumerate(result[0], 1):
        box = line[0]
        text_info = line[1]

        # 处理不同的返回格式
        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
            text = text_info[0]
            confidence = text_info[1] if isinstance(text_info[1], (int, float)) else 0.0
        else:
            text = str(text_info)
            confidence = 0.0

        # 显示文本(截断过长的文本)
        display_text = text if len(text) <= 50 else text[:47] + '...'
        print(f'│ [{i:2d}] {display_text:<50} │')
        if confidence > 0:
            print(f'│      置信度: {confidence*100:6.2f}%                              │')

    print('└' + '─' * 66 + '┘')

    # 汇总信息
    print('\n汇总信息:')
    print('─' * 70)
    all_text = ' '.join([
        line[1][0] if isinstance(line[1], (list, tuple)) and len(line[1]) >= 1 else str(line[1])
        for line in result[0]
    ])
    print(f'完整文本: {all_text}')
    print(f'文本块数: {len(result[0])}')

    # 字符统计
    chinese_chars = sum(1 for c in all_text if '\u4e00' <= c <= '\u9fff')
    english_chars = sum(1 for c in all_text if c.isalpha() and ord(c) < 128)
    numbers = sum(1 for c in all_text if c.isdigit())
    other_chars = len(all_text) - chinese_chars - english_chars - numbers

    print(f'\n字符统计:')
    print(f'  中文字符: {chinese_chars}')
    print(f'  英文字符: {english_chars}')
    print(f'  数字字符: {numbers}')
    print(f'  其他字符: {other_chars}')
    print(f'  总计: {len(all_text)}')

else:
    print('❌ 未识别到任何文本')

print('\n' + '=' * 70)
print('测试完成!')
print('=' * 70)

# 清理临时文件
if os.path.exists(img_path):
    os.remove(img_path)
    print(f'\n🧹 已清理临时文件: {img_path}')
