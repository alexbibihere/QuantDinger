# HAMA 右下角面板 OCR 识别完成

## 修改时间
2026-01-18

## 修改内容

### 1. 截图区域调整
**文件**: `backend_api_python/app/services/hama_ocr_extractor.py`

**修改前**: 截取右侧 60% 宽度，全屏高度
**修改后**: 截取右下角信息面板（右侧 40% 宽度，下半部分 50% 高度）

```python
clip = {
    'x': int(page_width * 0.6),   # 从页面 60% 处开始（右侧40%）
    'y': int(page_height * 0.5),  # 从页面 50% 处开始（下半部分）
    'width': int(page_width * 0.4),  # 截取右侧40%宽度
    'height': int(page_height * 0.5)  # 截取下半部分50%高度
}
```

### 2. OCR 解析逻辑优化

针对 TradingView 右下角 HAMA 信息面板的结构化文本识别，新增以下字段：

- **价格**: 从"价格"标签提取数值
- **HAMA 状态**: 识别"上涨趋势/下跌趋势/盘整"
- **布林带状态**: 识别"收缩/扩张/正常"
- **最近交叉**: 提取交叉信号和时间（如"涨(2026-01-18 16:30)"）

### 3. 识别结果示例

```json
{
  "current_price": 3425.80,
  "hama_color": "green",
  "trend": "up",
  "bollinger_status": "expansion",
  "last_cross_info": "涨(2026-01-18 16:30)",
  "ocr_engine": "rapidocr",
  "confidence": "high",
  "source": "ocr_panel"
}
```

### 4. 关键优势

✅ **更精准** - 只截取信息面板，避免图表噪音
✅ **更快速** - 截图区域更小，处理更快
✅ **更准确** - 结构化文本识别，置信度从 medium → high
✅ **更丰富** - 新增布林带状态、最近交叉时间等字段

## 测试方法

### 方式1: 通过 API 测试
```bash
curl -X POST http://localhost:5000/api/hama-ocr/extract \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "interval": "15"}'
```

### 方式2: 通过 Python 脚本测试
```bash
cd backend_api_python
python -c "
import sys
sys.path.insert(0, '.')
from app.services.hama_ocr_extractor import extract_hama_with_ocr
result = extract_hama_with_ocr(
    chart_url='https://cn.tradingview.com/chart/U1FY2qxO/',
    symbol='BTCUSDT',
    interval='15',
    ocr_engine='rapidocr'
)
print(result)
"
```

### 方式3: 通过 Brave 监控测试
```bash
cd backend_api_python
python auto_hama_monitor_mysql.py
```

## 后端状态

✅ 后端已重启并运行在 http://localhost:5000
✅ OCR 引擎（RapidOCR）已初始化成功
✅ 健康检查通过: `{"status":"healthy"}`

## 注意事项

1. **OCR 引擎**: 当前使用 RapidOCR，完全免费，速度快
2. **等待时间**: 图表渲染需要等待 50 秒，确保数据加载完成
3. **截图保留**: 测试时会自动清理截图，如需调试可修改代码保留
4. **代理设置**: 如需使用代理，请在 `.env` 文件中配置 `PROXY_URL`

## 相关文件

- OCR 提取器: `backend_api_python/app/services/hama_ocr_extractor.py`
- Brave 监控: `backend_api_python/app/services/hama_brave_monitor_mysql.py`
- 自动监控脚本: `backend_api_python/auto_hama_monitor_mysql.py`
- HAMA 指标代码: `backend_api_python/file/hamaCandle.txt`
