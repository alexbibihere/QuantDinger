# OCR 功能使用指南

## ✅ 部署状态

**PaddleOCR 已成功部署并测试通过!**

- ✅ PaddleOCR 已安装 (v3.3.2)
- ✅ PaddlePaddle 已安装 (v3.2.2)
- ✅ 模型文件已下载 (PP-OCRv5)
- ✅ OCR 模块已集成到项目
- ✅ 支持中英文混合识别

## 🚀 快速开始

### 1. Python 代码调用

```python
from app.services.hama_ocr_extractor import extract_hama_with_ocr

# 使用 OCR 提取 HAMA 指标
result = extract_hama_with_ocr(
    chart_url='https://cn.tradingview.com/chart/xxx/',
    symbol='BTCUSDT',
    interval='15',
    ocr_engine='paddleocr'  # 或 'tesseract', 'easyocr'
)

# 返回结果示例
print(f"HAMA 数值: {result['hama_value']}")
print(f"HAMA 颜色: {result['hama_color']}")
print(f"趋势: {result['trend']}")
print(f"当前价格: {result['current_price']}")
print(f"布林带上轨: {result['bollinger_bands']['upper']}")
```

### 2. API 接口调用

项目已集成 `/api/hama-ocr/extract` 接口 (如果已注册路由):

```bash
curl -X GET "http://localhost:5000/api/hama-ocr/extract?symbol=BTCUSDT&interval=15"
```

**返回数据格式:**
```json
{
  "success": true,
  "data": {
    "hama_value": 95000.0,
    "hama_color": "green",
    "trend": "up",
    "current_price": 95234.5,
    "bollinger_bands": {
      "upper": 96500.0,
      "middle": 95000.0,
      "lower": 93500.0
    },
    "ocr_engine": "paddleocr",
    "confidence": "medium",
    "source": "ocr",
    "raw_text": "识别的原始文本...",
    "chart_url": "https://cn.tradingview.com/chart/xxx/",
    "symbol": "BTCUSDT",
    "interval": "15"
  }
}
```

## 📊 支持的 OCR 引擎

### 1. PaddleOCR (推荐) ✅
- **状态**: 已安装
- **优点**: 完全免费、支持中英文、识别准确率高
- **缺点**: 首次运行需要下载模型文件 (~200MB)
- **适用场景**: 一般文档、图表识别

### 2. Tesseract OCR
- **安装**:
  ```bash
  pip install pytesseract pillow
  # Windows 还需要下载安装 Tesseract-OCR
  ```
- **优点**: 开源、支持多语言
- **缺点**: 识别准确率较低、需要额外安装语言包

### 3. EasyOCR
- **安装**:
  ```bash
  pip install easyocr
  ```
- **优点**: 易用、支持 80+ 语言
- **缺点**: 模型较大、速度较慢

## 🎯 应用场景

### 1. 识别 TradingView 图表

```python
from app.services.hama_ocr_extractor import HAMAOCRExtractor

# 创建提取器实例
extractor = HAMAOCRExtractor(ocr_engine='paddleocr')

# 截取图表
screenshot_path = extractor.capture_chart(
    chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
    output_path='./screenshot.png'
)

# OCR 识别
hama_data = extractor.extract_hama_with_ocr('./screenshot.png')
```

### 2. 批量处理图片

```python
import os
from app.services.hama_ocr_extractor import HAMAOCRExtractor

extractor = HAMAOCRExtractor(ocr_engine='paddleocr')

# 遍历图片目录
for img_file in os.listdir('./images'):
    if img_file.endswith(('.png', '.jpg', '.jpeg')):
        result = extractor.extract_hama_with_ocr(f'./images/{img_file}')
        print(f"{img_file}: {result['hama_value']}")
```

### 3. 实时监控

结合定时任务,定期截图并识别:

```python
import schedule
import time

def monitor_hama():
    result = extract_hama_with_ocr(
        chart_url='https://cn.tradingview.com/chart/xxx/',
        symbol='BTCUSDT'
    )
    # 处理识别结果...
    print(f"当前 HAMA: {result['hama_value']}, 趋势: {result['trend']}")

# 每 5 分钟执行一次
schedule.every(5).minutes.do(monitor_hama)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## 🔧 高级配置

### 调整 OCR 参数

如果需要调整 PaddleOCR 的参数,可以修改 `hama_ocr_extractor.py`:

```python
self.ocr = PaddleOCR(
    lang='ch',  # 语言: 'ch'中文, 'en'英文, 'japan'日语等
    # 更多参数请参考 PaddleOCR 文档
)
```

### 网络代理配置

如果需要访问 TradingView,确保代理配置正确:

```bash
# 在 .env 文件中设置
PROXY_PORT=7890
# 或
PROXY_URL=socks5h://127.0.0.1:7890
```

### 禁用模型源检查 (加速启动)

```bash
# Windows PowerShell
$env:DISABLE_MODEL_SOURCE_CHECK="True"

# Linux/Mac
export DISABLE_MODEL_SOURCE_CHECK=True
```

## 📝 测试脚本

项目已包含测试脚本:

### 1. 快速测试
```bash
python test_ocr_quick.py
```

### 2. PaddleOCR 初始化测试
```bash
python test_paddleocr.py
```

### 3. 完整 OCR 流程测试
```bash
python -c "from app.services.hama_ocr_extractor import extract_hama_with_ocr; print('OCR OK')"
```

## 🐛 常见问题

### Q1: 首次运行很慢?
**A**: 首次运行需要下载模型文件 (~200MB),之后会缓存到 `C:\Users\{用户名}\.paddlex\` 目录

### Q2: 识别准确率不高?
**A**: 可以尝试:
- 使用更高分辨率的图片
- 调整图片对比度和亮度
- 尝试其他 OCR 引擎 (tesseract, easyocr)

### Q3: 中文显示乱码?
**A**: 确保使用 UTF-8 编码:
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### Q4: 能否识别其他语言?
**A**: 可以! PaddleOCR 支持 80+ 语言,修改 `lang` 参数:
```python
ocr = PaddleOCR(lang='en')  # 英文
ocr = PaddleOCR(lang='japan')  # 日语
ocr = PaddleOCR(lang='korean')  # 韩语
```

## 📚 参考资料

- [PaddleOCR 官方文档](https://github.com/PaddlePaddle/PaddleOCR)
- [项目 HAMA OCR 提取器代码](backend_api_python/app/services/hama_ocr_extractor.py)
- [部署完整指南](deploy_paddleocr_guide.md)

## 🎉 总结

您现在拥有一个**完全本地、免费、功能强大**的 OCR 系统!

**下一步建议:**
1. ✅ 测试识别 TradingView 图表
2. ✅ 集成到 HAMA Market 页面
3. ✅ (可选) 如果有 GPU,部署 DeepSeek OCR 获得更高精度

---

**生成时间**: 2026-01-16
**项目**: QuantDinger
**OCR 引擎**: PaddleOCR v3.3.2
