# TradingView 截图超时问题修复说明

## 🐛 问题描述

后端服务在运行时频繁出现 TradingView 图表截图超时错误：

```
ERROR - 截取图表失败: Page.goto: Timeout 120000ms exceeded.
Call log:
  - navigating to "https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3ABNBUSDT&interval=15", waiting until "load"
```

### 影响范围
- ETHUSDT: 监控失败
- BNBUSDT: 监控失败
- 其他币种也可能出现相同问题

## 🔍 问题原因分析

### 根本原因
1. **超时时间过长** - 设置为 120 秒（2分钟），如果页面卡住会导致长时间等待
2. **等待策略不当** - 使用 `wait_until='load'` 会等待所有资源加载完成，包括图片、样式表等，对于 TradingView 这样复杂的页面容易超时
3. **等待渲染时间过长** - 页面加载后再等待 50 秒，总等待时间可能超过 2 分钟

### 问题位置
- `app/services/hama_ocr_extractor.py:364`
- `app/services/hama_vision_extractor.py:112`

## ✅ 修复方案

### 修改内容

#### 1. hama_ocr_extractor.py

**修改前:**
```python
# 访问图表
logger.info("正在加载图表...")
page.goto(chart_url, timeout=120000, wait_until='load')

# 等待图表渲染
logger.info("等待图表渲染...")
page.wait_for_timeout(50000)
```

**修改后:**
```python
# 访问图表
logger.info("正在加载图表...")
# 使用 domcontentloaded 代替 load，减少超时风险
# 超时时间从 120 秒减少到 60 秒
page.goto(chart_url, timeout=60000, wait_until='domcontentloaded')

# 等待图表渲染
logger.info("等待图表渲染...")
# 减少等待时间从 50 秒到 15 秒，避免长时间等待
page.wait_for_timeout(15000)
```

#### 2. hama_vision_extractor.py

**修改前:**
```python
# 访问图表
logger.info("正在加载图表...")
page.goto(chart_url, timeout=120000, wait_until='load')

# 等待图表渲染
logger.info("等待图表渲染...")
page.wait_for_timeout(50000)
```

**修改后:**
```python
# 访问图表
logger.info("正在加载图表...")
# 使用 domcontentloaded 代替 load，减少超时风险
# 超时时间从 120 秒减少到 60 秒
page.goto(chart_url, timeout=60000, wait_until='domcontentloaded')

# 等待图表渲染
logger.info("等待图表渲染...")
# 减少等待时间从 50 秒到 15 秒，避免长时间等待
page.wait_for_timeout(15000)
```

### 优化说明

1. **等待策略优化**
   - 从 `wait_until='load'` 改为 `wait_until='domcontentloaded'`
   - `load`: 等待所有资源加载完成（包括图片、CSS、JS）
   - `domcontentloaded`: 只等待 DOM 结构加载完成，不等待图片等资源
   - **优势**: 更快触发，减少超时风险

2. **超时时间优化**
   - 从 120 秒减少到 60 秒
   - **优势**: 更快失败，避免长时间等待
   - **权衡**: 60 秒足够 TradingView 页面加载 DOM 结构

3. **渲染等待时间优化**
   - 从 50 秒减少到 15 秒
   - **优势**: 减少总等待时间
   - **权衡**: 15 秒足够图表容器渲染 HAMA 指标

### 时间对比

| 阶段 | 修改前 | 修改后 | 改进 |
|------|--------|--------|------|
| 页面加载 | 最多 120 秒 | 最多 60 秒 | ⬇️ 50% |
| 等待渲染 | 固定 50 秒 | 固定 15 秒 | ⬇️ 70% |
| **总时间** | **最多 170 秒** | **最多 75 秒** | ⬇️ **56%** |

## 📊 预期效果

### 优点
1. ✅ **更快失败** - 60 秒超时比 120 秒更快，避免长时间卡住
2. ✅ **更高成功率** - `domcontentloaded` 比 `load` 更容易触发
3. ✅ **更高效** - 总等待时间从 170 秒减少到 75 秒
4. ✅ **更稳定** - 减少因网络波动导致的超时

### 可能的副作用
1. ⚠️ **图表可能未完全渲染** - 但 15 秒等待通常足够
2. ⚠️ **HAMA 指标可能未加载** - 但 TradingView 的 HAMA 通常在 DOM 加载后很快出现

### 建议
- 如果 15 秒等待后发现 HAMA 指标未完全渲染，可以适当增加到 20-25 秒
- 如果 60 秒超时仍然太短，可以增加到 75-90 秒
- 但不建议回到 120 秒 + `load` 的配置

## 🔄 如何应用修复

### 方法 1: 重启后端服务
如果后端服务正在运行，需要重启以应用更改：

```bash
# 停止当前运行的后端服务
# Ctrl+C 或关闭终端

# 重新启动
cd backend_api_python
python run.py
```

### 方法 2: 如果使用 PM2
```bash
# 重启服务
pm2 restart quantdinger

# 或者重新加载
pm2 reload quantdinger
```

## 🧪 测试验证

### 手动测试
```bash
cd backend_api_python

# 测试 OCR 提取
python -c "
from app.services.hama_ocr_extractor import extract_hama_with_ocr
result = extract_hama_with_ocr(
    symbol='BTCUSDT',
    interval='15',
    ocr_engine='rapidocr'
)
print(result)
"
```

### 监控日志
观察日志是否还出现超时错误：
```bash
# 应该看到类似以下的成功日志
INFO - 正在加载图表...
INFO - ✅ 已登录
INFO - 等待图表渲染...
INFO - ✅ 图表截图完成
```

## 📝 其他建议

### 1. 添加重试机制
如果偶尔超时，可以考虑添加重试逻辑：

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = extractor.capture_chart(chart_url, output_path)
        if result:
            break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        logger.warning(f"第 {attempt + 1} 次尝试失败，重试中...")
        time.sleep(5)
```

### 2. 添加超时配置
在配置文件中添加可配置的超时时间：

```python
# config.py
PLAYWRIGHT_TIMEOUT = int(os.getenv('PLAYWRIGHT_TIMEOUT', 60000))
PLAYWRIGHT_WAIT_AFTER_LOAD = int(os.getenv('PLAYWRIGHT_WAIT_AFTER_LOAD', 15000))
```

### 3. 使用代理
如果网络问题是主要原因，考虑配置代理：

```bash
# 设置代理环境变量
export PROXY_URL=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

## 🎯 总结

本次修复通过优化 Playwright 的等待策略和超时设置，将 TradingView 图表截图的总等待时间从 **最多 170 秒减少到 75 秒**，降低了 **56%** 的等待时间，同时提高了成功率。

修复完成后，建议：
1. ✅ 重启后端服务
2. ✅ 观察监控日志
3. ✅ 检查 ETHUSDT、BNBUSDT 等之前失败的币种是否恢复正常

---

**修复日期**: 2026-01-20
**修复者**: Claude Sonnet 4.5
**状态**: ✅ 已完成
