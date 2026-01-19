# Selenium 截图快速开始

## 📦 已安装工具

✅ **Selenium** - 已安装并测试通过

## 🚀 快速开始

### 方法 1: 使用便捷函数 (推荐)

```python
from app.services.screenshot_helper import capture_screenshot

# 快速截图
result = capture_screenshot(
    url='https://example.com',
    output_path='../screenshot/example.png',
    wait_time=10
)

if result['success']:
    print(f'成功! 保存到: {result["output_path"]}')
else:
    print(f'失败: {result["error"]}')
```

### 方法 2: 使用截图助手

```python
from app.services.screenshot_helper import ScreenshotHelper

# 创建助手
helper = ScreenshotHelper(
    proxy_port=7890,  # 可选: 代理端口
    headless=True     # 可选: 无头模式
)

# 截图
result = helper.capture(
    url='https://example.com',
    output_path='../screenshot/example.png',
    wait_time=10,
    width=1920,
    height=1080
)
```

### 方法 3: 使用 Cookie 访问私有页面

```python
from app.services.screenshot_helper import ScreenshotHelper

helper = ScreenshotHelper(proxy_port=7890)

result = helper.capture_with_cookie(
    url='https://cn.tradingview.com/chart/U1FY2qxO/',
    output_path='../screenshot/private_chart.png',
    cookie_string='your_cookie_string_here',
    wait_time=15
)
```

## 📝 常用场景

### 场景 1: 截图 TradingView Widget

```python
from app.services.screenshot_helper import capture_screenshot

widget_url = 'https://s.tradingview.com/widgetembed/'
params = '?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1'

result = capture_screenshot(
    url=widget_url + params,
    output_path='../screenshot/btcusdt_15m.png',
    wait_time=10
)
```

### 场景 2: 批量截图多个币种

```python
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

for symbol in symbols:
    params = f'?symbol=BINANCE%3A{symbol}&interval=15'
    result = capture_screenshot(
        url='https://s.tradingview.com/widgetembed/' + params,
        output_path=f'../screenshot/{symbol.lower()}_15m.png',
        wait_time=10
    )
    print(f'{symbol}: {"成功" if result["success"] else "失败"}')
```

### 场景 3: 使用代理访问

```python
# 方法 1: 环境变量
import os
os.environ['PROXY_PORT'] = '7890'

result = capture_screenshot(
    url='https://example.com',
    output_path='../screenshot/example.png'
)

# 方法 2: 直接指定
result = capture_screenshot(
    url='https://example.com',
    output_path='../screenshot/example.png',
    proxy_port=7890
)
```

### 场景 4: 截图 + OCR 识别

```python
from app.services.screenshot_helper import capture_screenshot
from paddleocr import PaddleOCR
import os

# 1. 截图
result = capture_screenshot(
    url='https://s.tradingview.com/widgetembed/?symbol=BINANCE%3ABTCUSDT&interval=15',
    output_path='../screenshot/btcusdt.png',
    wait_time=10
)

if result['success']:
    # 2. OCR 识别
    ocr = PaddleOCR(lang='en')
    ocr_result = ocr.ocr(result['output_path'])

    if ocr_result and len(ocr_result) > 0:
        texts = ocr_result[0].rec_texts
        for text in texts:
            print(text)
```

## 🛠️ 配置选项

### 截图参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | str | 必填 | 目标 URL |
| `output_path` | str | 必填 | 输出文件路径 |
| `wait_time` | int | 10 | 等待时间(秒) |
| `width` | int | 1920 | 窗口宽度 |
| `height` | int | 1080 | 窗口高度 |
| `proxy_port` | int | None | 代理端口 |
| `headless` | bool | True | 是否无头模式 |

### 返回值

```python
{
    'success': True/False,        # 是否成功
    'output_path': 'path/to/png', # 文件路径
    'file_size': 12345,           # 文件大小(字节)
    'elapsed': 10.5,              # 耗时(秒)
    'error': 'error message'      # 错误信息(如果失败)
}
```

## 📁 相关文件

- [screenshot_helper.py](backend_api_python/app/services/screenshot_helper.py) - 截图助手
- [screenshot_service.py](backend_api_python/app/services/screenshot_service.py) - 统一截图服务
- [quick_screenshot.py](backend_api_python/quick_screenshot.py) - 快速截图工具
- [examples/screenshot_usage.py](backend_api_python/examples/screenshot_usage.py) - 使用示例

## 🎯 运行示例

```bash
# 基本示例
python quick_screenshot.py

# 使用示例
python examples/screenshot_usage.py

# 性能对比
python test_screenshot_comparison.py
```

## 💡 提示

1. **等待时间**: 动态页面建议设置 10-15 秒
2. **代理配置**: 如果网络受限,设置 `proxy_port=7890`
3. **分辨率**: 需要 2K 截图时设置 `width=2560, height=1440`
4. **错误处理**: 始终检查 `result['success']`

## 🔧 故障排除

### 问题 1: 连接超时
**解决**: 配置代理
```python
result = capture_screenshot(url, path, proxy_port=7890)
```

### 问题 2: 截图空白
**解决**: 增加等待时间
```python
result = capture_screenshot(url, path, wait_time=15)
```

### 问题 3: Cookie 无效
**解决**: 更新 Cookie 文件
```bash
# 从浏览器复制最新的 Cookie
# 保存到 tradingview_cookies.json
```

---

**更新时间**: 2026-01-16
**状态**: ✅ 可用
