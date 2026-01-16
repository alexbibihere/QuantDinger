#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 OCR 识别图片
"""
import sys
import io

# 设置 stdout 编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import requests

print('=' * 60)
print('OCR 图片识别测试')
print('=' * 60)

# 图片 URL
img_url = 'https://maas-log-prod.cn-wlcb.ufileos.com/anthropic/82535413-f275-40d3-951a-d545bf6862f5/39df8f3fbfc8361bee144e62b9ba0865.png?UCloudPublicKey=TOKEN_e15ba47a-d098-4fbd-9afc-a0dcf0e4e621&Expires=1768555843&Signature=h9GsX43Bi63IPGEH+XI+v8Nbj3M='

# 下载图片
print('\n📥 下载图片...')
response = requests.get(img_url)
img_path = './test_ocr_image.png'
with open(img_path, 'wb') as f:
    f.write(response.content)
print(f'✅ 图片已保存: {img_path}')
print(f'   图片大小: {len(response.content)} bytes\n')

# 初始化 OCR
print('🔍 初始化 PaddleOCR...')
ocr = PaddleOCR(lang='ch')
print('✅ OCR 初始化完成!\n')

# 识别图片
print('🔎 开始识别图片...\n')
result = ocr.ocr(img_path)

if result and result[0]:
    print('=' * 60)
    print('识别结果:')
    print('=' * 60)
    print()

    # 整理所有文本
    all_texts = []
    for i, line in enumerate(result[0], 1):
        text_info = line[1]

        # 处理不同的返回格式
        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
            text = text_info[0]
            confidence = text_info[1]
        else:
            # 如果只是字符串
            text = str(text_info)
            confidence = 0.0

        all_texts.append((text, confidence))

    # 输出所有识别的文本
    for i, (text, confidence) in enumerate(all_texts, 1):
        print(f'[{i}] {text}')
        print(f'    置信度: {confidence:.2%}\n')

    print('=' * 60)
    print(f'🎉 识别完成! 共识别 {len(all_texts)} 个文本块')
    print('=' * 60)

    # 尝试提取 HAMA 相关信息
    print('\n' + '=' * 60)
    print('HAMA 指标信息提取:')
    print('=' * 60)

    full_text = ' '.join([t[0] for t in all_texts])
    print(f'\n完整文本:\n{full_text}\n')

    # 查找数字和价格
    import re
    prices = re.findall(r'[\d,]+\.?\d*', full_text)
    if prices:
        print(f'找到的价格数据: {prices[:5]}')

else:
    print('❌ 未识别到文本')
