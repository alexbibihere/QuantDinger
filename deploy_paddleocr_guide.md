# PaddleOCR 本地部署指南

## 一、安装 PaddleOCR (推荐方案)

### 1. 安装依赖
```bash
# 进入后端目录
cd d:\github\QuantDinger\backend_api_python

# 安装 PaddleOCR 和 PaddlePaddle (CPU版本)
pip install paddleocr paddlepaddle

# 如果有 NVIDIA GPU,安装 GPU版本 (可选)
# pip install paddlepaddle-gpu
```

### 2. 验证安装
```bash
python -c "from paddleocr import PaddleOCR; print('PaddleOCR 安装成功!')"
```

### 3. 测试 OCR 功能
```bash
# 运行测试脚本
python test_hama_market_api.py
```

## 二、使用项目中已有的 OCR API

项目已集成完整的 OCR 提取器,支持:

### 1. 支持的 OCR 引擎
- **PaddleOCR** (推荐) - 完全免费,支持中英文
- **Tesseract OCR** - 开源 OCR
- **EasyOCR** - 易用的 OCR 库

### 2. 已实现的功能
- 自动截图 TradingView 图表
- 本地 OCR 识别 HAMA 指标值
- 解析识别结果,提取结构化数据
- 支持多种图片格式 (PNG, JPG, etc.)

### 3. API 接口

#### 调用示例 (Python)
```python
from app.services.hama_ocr_extractor import extract_hama_with_ocr

# 使用 OCR 提取 HAMA 指标
result = extract_hama_with_ocr(
    chart_url='https://cn.tradingview.com/chart/xxx/',
    symbol='BTCUSDT',
    interval='15',
    ocr_engine='paddleocr'  # 或 'tesseract', 'easyocr'
)

# 返回结果
{
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
    "confidence": "medium"
}
```

## 三、DeepSeek OCR 部署 (可选,需要GPU)

如果您有 NVIDIA GPU (推荐 RTX 4090 24GB),可以部署 DeepSeek OCR:

### 1. 环境要求
- GPU: NVIDIA RTX 4090 (24GB 显存) 或更高
- CUDA: 12.6
- Python: 3.12

### 2. 安装步骤
```bash
# 创建项目目录
mkdir d:\projects\deepseek-ocr
cd d:\projects\deepseek-ocr

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装 vLLM
pip install vllm

# 下载模型 (使用镜像加速)
set HF_ENDPOINT=https://hf-mirror.com
pip install huggingface_hub
huggingface-cli download deepseek-ai/DeepSeek-OCR --local-dir ./DeepSeek-OCR
```

### 3. 启动服务
```bash
vllm serve ./DeepSeek-OCR ^
    --served-model-name deepseek-ocr ^
    --host 0.0.0.0 ^
    --port 8100 ^
    --trust-remote-code ^
    --gpu-memory-utilization 0.35 ^
    --max-model-len 2048 ^
    --api-key your_api_key_here
```

### 4. 调用 API
```python
from openai import OpenAI

client = OpenAI(
    api_key="your_api_key_here",
    base_url="http://localhost:8100/v1"
)

# 读取图片
import base64
with open("chart.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# 调用 OCR
response = client.chat.completions.create(
    model="deepseek-ocr",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}"
                    }
                },
                {
                    "type": "text",
                    "text": "<|grounding|>Convert the document to markdown."
                }
            ]
        }
    ],
    max_tokens=2048
)

print(response.choices[0].message.content)
```

## 四、对比总结

| 特性 | PaddleOCR (推荐) | DeepSeek OCR |
|------|-----------------|--------------|
| **硬件要求** | CPU 即可 | 需要 NVIDIA GPU (24GB+) |
| **安装难度** | 简单 (1条命令) | 复杂 (需要 vLLM) |
| **模型大小** | ~200MB | ~6GB |
| **识别准确率** | 中等 (85-90%) | 高 (95%+) |
| **支持语言** | 中英文混合 | 100+ 语言 |
| **处理速度** | 快 (CPU) | 极快 (GPU) |
| **部署方式** | 完全本地 | 本地 API 服务 |
| **成本** | 免费 | 免费 (开源) |
| **适用场景** | 一般文档识别 | 复杂文档、高精度需求 |

## 五、建议

1. **快速测试**: 使用 PaddleOCR,5分钟内完成部署
2. **生产环境**: 如果有 GPU,使用 DeepSeek OCR 获得更高精度
3. **混合使用**: PaddleOCR 用于实时识别,DeepSeek OCR 用于批量处理

## 六、快速开始

现在立即安装 PaddleOCR:
```bash
cd d:\github\QuantDinger\backend_api_python
pip install paddleocr paddlepaddle
```

然后运行测试:
```bash
python -c "from app.services.hama_ocr_extractor import extract_hama_with_ocr; print('OCR 功能就绪!')"
```
