# 🆓 免费 OCR 识别方案 - 完整指南

## 🎉 免费方案已实现！

使用 **PaddleOCR** 本地识别，完全免费，无需 API 密钥！

---

## 📋 方案对比

| 方案 | 价格 | 速度 | 准确性 | API密钥 |
|------|------|------|--------|---------|
| **PaddleOCR** | ✅ 完全免费 | ⚡ 秒级 | ⚠️ 中等 | ❌ 不需要 |
| GPT-4o | 💰 $0.0025/次 | 🐌 ~60s | ✅ 高 | ✅ 需要 |
| Groq | 🆓 每天100次免费 | ⚡ 快 | ✅ 高 | ✅ 需要 |
| Gemini | 🆓 每月15次 | ⚡ 快 | ✅ 高 | ✅ 需要 |

---

## 🚀 快速开始

### 1. 安装依赖

PaddleOCR 已添加到 `requirements.txt`，重新构建容器即可：

```bash
cd /d/github/QuantDinger
docker-compose down backend
docker-compose up -d --build backend
```

### 2. 测试健康检查

```bash
curl http://localhost:5000/api/hama-ocr/health
```

预期输出：
```json
{
  "success": true,
  "service": "HAMA OCR API",
  "status": "running",
  "available_engines": ["paddleocr"],
  "default_engine": "paddleocr"
}
```

### 3. 使用 OCR 识别

```bash
curl -X POST http://localhost:5000/api/hama-ocr/extract \
  -H "Content-Type: application/json" \
  -d '{
    "chart_url": "https://cn.tradingview.com/chart/U1FY2qxO/",
    "symbol": "ETHUSD",
    "interval": "15",
    "ocr_engine": "paddleocr"
  }'
```

---

## 📊 支持的 OCR 引擎

### 1. PaddleOCR（推荐）⭐
- ✅ **完全免费**
- ✅ 支持中英文
- ✅ 识别速度快
- ✅ 准确度中等

### 2. Tesseract
- ✅ 开源免费
- ⚠️ 需要额外安装系统依赖
- ✅ 识别速度较快

### 3. EasyOCR
- ✅ 开源免费
- ✅ 易用性好
- ⚠️ 速度较慢

---

## 🔧 Python 使用示例

```python
from app.services.hama_ocr_extractor import extract_hama_with_ocr

# 使用 PaddleOCR 识别
result = extract_hama_with_ocr(
    chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
    symbol='ETHUSD',
    interval='15',
    ocr_engine='paddleocr'
)

if result:
    print(f"HAMA 数值: {result['hama_value']}")
    print(f"颜色: {result['hama_color']}")
    print(f"趋势: {result['trend']}")
```

---

## 📊 预期输出

```json
{
  "success": true,
  "data": {
    "hama_value": 3418.03,
    "hama_color": "green",
    "trend": "up",
    "current_price": 3369.1,
    "bollinger_bands": {
      "upper": 3500.0,
      "middle": 3400.0,
      "lower": 3300.0
    },
    "ocr_engine": "paddleocr",
    "confidence": "medium",
    "source": "ocr",
    "screenshot_path": "/tmp/ETHUSD_15_chart.png",
    "raw_text": "识别的文字内容..."
  }
}
```

---

## ⚖️ OCR vs AI 视觉对比

| 特性 | PaddleOCR | GPT-4o |
|------|-----------|--------|
| **价格** | ✅ 完全免费 | 💰 $0.0025/次 |
| **速度** | ⚡ ~2秒 | 🐌 ~60秒 |
| **准确性** | ⚠️ 中等 | ✅ 高 |
| **隐私** | ✅ 完全本地 | ⚠️ 上传到云端 |
| **依赖** | PaddleOCR | OpenRouter API |
| **推荐场景** | **日常使用** | 特殊情况 |

---

## 💡 使用建议

### 主要方案：PaddleOCR（免费）
- ✅ 日常使用
- ✅ 高频调用
- ✅ 成本敏感

### 备用方案：GPT-4o（付费）
- ✅ 需要高准确度时
- ✅ 偶尔使用
- ✅ OCR 失败时

### 混合策略
```python
def smart_extract(chart_url):
    # 先尝试免费的 OCR
    result = extract_hama_with_ocr(chart_url, ocr_engine='paddleocr')

    # 如果 OCR 识别失败或置信度低，使用 GPT-4o
    if not result or result.get('confidence') == 'low':
        result = extract_hama_with_vision(chart_url)

    return result
```

---

## 🔧 故障排查

### 问题 1：`available_engines: []`

**原因**：PaddleOCR 未安装

**解决**：
```bash
# 手动安装
pip install paddleocr paddlepaddle

# 或重新构建容器
docker-compose down backend
docker-compose up -d --build backend
```

### 问题 2：识别不准确

**原因**：OCR 对复杂图表识别能力有限

**解决**：
1. 调整截图大小和清晰度
2. 使用 GPT-4o 作为备用方案
3. 优化 OCR 解析逻辑

### 问题 3：速度慢

**原因**：OCR 处理大图片较慢

**解决**：
1. 调整截图区域（只截取左上角）
2. 降低图片分辨率
3. 使用更快的 OCR 引擎（如 Tesseract）

---

## 🎉 总结

现在你有**两个免费方案**：

1. ✅ **本地计算**（方案3）- 最快、最准确
2. ✅ **OCR 识别**（方案5）- 完全免费、易于使用

**推荐配置**：
- 生产环境：**方案3（本地计算）**
- 验证/调试：**方案5（OCR）** 或 **方案4（GPT-4o）**

所有方案都已实现，立即可用！🚀
