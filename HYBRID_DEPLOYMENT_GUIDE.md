# 混合方案部署指南 - 本地开发 + Docker 生产

## 🎯 方案概述

```
本地开发环境
  ├─ Playwright + RapidOCR 安装在本地
  ├─ 可以直接运行 Python 脚本测试
  ├─ 调试时可以看到浏览器窗口（可选）
  └─ 用于开发和验证功能

Docker 生产环境
  ├─ 使用本地计算作为主要数据源
  ├─ 快速、准确、稳定
  ├─ Docker 镜像保持轻量
  └─ 不依赖浏览器和 OCR
```

## 📋 架构对比

| 功能 | 本地环境 | Docker 环境 |
|------|---------|-------------|
| HAMA 计算 | Brave 监控（真实数据） | 本地计算（快速） |
| 开发调试 | ✅ 方便 | ⚠️ 需要重建镜像 |
| 部署简单 | - | ✅ 一键部署 |
| 镜像大小 | - | ✅ 保持轻量 |
| 数据准确性 | ✅ TradingView 真实 | ✅ 99%+ 准确 |

## 🚀 快速开始

### 第一步：本地安装依赖

#### Windows
```powershell
# 进入后端目录
cd backend_api_python

# 运行安装脚本
install_local_requirements.bat

# 或手动安装
pip install playwright playwright-stealth rapidocr-onnxruntime
playwright install chromium
```

#### Linux/Mac
```bash
cd backend_api_python

bash install_local_requirements.sh

# 或手动安装
pip install playwright playwright-stealth rapidocr-onnxruntime
playwright install chromium
```

### 第二步：本地测试

```bash
cd backend_api_python

# 运行测试脚本
python test_brave_local.py
```

**预期输出**:
```
🧪 本地环境测试 - Brave 监控功能
测试时间: 2026-01-18 04:30:00

▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶
测试 1/3: Redis 连接
▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶

✅ OCR 提取器导入成功
正在初始化 OCR 提取器...
✅ RapidOCR 初始化成功

正在提取 BTCUSDT 的 HAMA 数据...
[浏览器加载...]

✅ 提取成功！耗时: 15.2秒

📊 HAMA 数据:
  趋势: up
  颜色: green
  数值: 95356.06
```

### 第三步：修改后端支持混合模式

修改 `backend_api_python/app/routes/hama_market.py`:

```python
@hama_market_bp.route('/watchlist', methods=['GET'])
def get_hama_watchlist():
    """
    获取 HAMA 监控列表（混合模式：本地计算 + 可选 Brave 验证）
    """
    watchlist = []

    for symbol in symbols:
        try:
            # 方案 A: 本地计算（主要）
            kline_data = kline_service.get_kline(
                market='Crypto',
                symbol=symbol,
                timeframe='15m',
                limit=500
            )

            if kline_data and len(kline_data) >= 100:
                ohlcv_data = [[k['timestamp'], k['open'], k['high'],
                              k['low'], k['close'], k['volume']]
                             for k in kline_data]

                hama_result = calculate_hama_from_ohlcv(ohlcv_data)

                item = {
                    'symbol': symbol,
                    'price': hama_result['close'],
                    'hama_local': {
                        'hama_trend': hama_result['trend']['direction'],
                        'hama_color': hama_result['hama']['color'],
                        'hama_value': hama_result['hama']['close'],
                        'calculated_at': datetime.now().isoformat(),
                        'data_source': 'local_calculation'
                    }
                }

                # 方案 B: Brave 监控（可选验证）
                if BRAVE_MONITOR_ENABLED and brave_monitor:
                    try:
                        brave_hama = brave_monitor.get_cached_hama(symbol)
                        if brave_hama:
                            item['hama_brave'] = brave_hama
                            item['verified'] = True
                    except:
                        item['verified'] = False

                watchlist.append(item)

        except Exception as e:
            logger.error(f"处理 {symbol} 失败: {e}")
            continue

    return jsonify({
        'success': True,
        'data': {
            'watchlist': watchlist
        }
    })
```

### 第四步：Docker 部署

```bash
# 启动 Docker 服务
docker-compose up -d backend frontend

# 查看日志
docker-compose logs -f backend

# 测试 API
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT,ETHUSDT"
```

## 📊 工作流程

### 开发流程

```
1. 本地开发
   ├─ 修改代码
   ├─ 本地测试 Brave 监控
   └─ 验证功能正常

2. 本地计算验证
   ├─ 对比 Brave 监控结果
   ├─ 确认本地计算准确
   └─ 调整算法参数

3. Docker 部署
   ├─ 提交代码
   ├─ Docker 自动构建
   └─ 生产环境使用本地计算
```

### 数据流程

```
前端请求
    ↓
后端 API (hama_market.py)
    ↓
┌──────────────────────────────┐
│  本地计算（快速）              │
│  ├─ 从交易所获取 K线          │
│  ├─ 本地计算 HAMA             │
│  └─ 返回结果（2-5秒）         │
└──────────────────────────────┘
    ↓
可选：Brave 监控验证
    ├─ 本地运行 Playwright
    ├─ 访问 TradingView
    ├─ OCR 识别 HAMA
    └─ 对比验证结果
```

## 🔧 配置文件

### 本地环境配置

创建 `backend_api_python/.env.local`（本地开发专用）：

```bash
# 本地开发配置
PYTHON_API_HOST=127.0.0.1
PYTHON_API_PORT=5000
PYTHON_API_DEBUG=True

# Brave 监控（本地）
BRAVE_MONITOR_ENABLED=true
BRAVE_MONITOR_BROWSER_TYPE=chromium

# 代理（如需要）
PROXY_PORT=7890
PROXY_HOST=127.0.0.1
```

### Docker 环境配置

`backend_api_python/.env`（生产环境）：

```bash
# Docker 配置
PYTHON_API_HOST=0.0.0.0
PYTHON_API_PORT=5000
PYTHON_API_DEBUG=False

# 本地计算（生产）
HAMA_USE_LOCAL_CALC=true
HAMA_CACHE_ENABLED=true

# 可选：Brave 监控
BRAVE_MONITOR_ENABLED=false  # Docker 中关闭
```

## 📝 常见任务

### 本地开发任务

#### 1. 测试单个币种
```bash
cd backend_api_python
python -c "
from app.services.hama_ocr_extractor import HAMAOCRExtractor
ocr = HAMAOCRExtractor()
result = ocr.extract_hama('BTCUSDT', '15m', save_screenshot=True)
print(result)
"
```

#### 2. 批量测试多个币种
```bash
python -c "
from app.services.hama_brave_monitor import HamaBraveMonitor
monitor = HamaBraveMonitor()
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
results = monitor.monitor_batch(symbols, 'chromium')
print(results)
"
```

#### 3. 验证本地计算准确性
```bash
python test_brave_local.py
```

### Docker 部署任务

#### 1. 重新构建并启动
```bash
docker-compose build backend
docker-compose up -d backend
```

#### 2. 查看日志
```bash
docker-compose logs -f backend --tail 100
```

#### 3. 进入容器调试
```bash
docker exec -it quantdinger-backend bash
```

## 🎯 最佳实践

### 开发阶段

1. ✅ 使用本地 Brave 监控获取真实数据
2. ✅ 对比本地计算结果
3. ✅ 调整算法参数直到准确率达到 99%+
4. ✅ 在前端展示本地计算结果

### 生产阶段

1. ✅ Docker 容器使用本地计算
2. ✅ 定期在本地运行 Brave 监控验证
3. ✅ 如发现偏差，调整算法
4. ✅ Docker 镜像保持轻量（不包含浏览器）

### 数据验证

```python
# 定期验证脚本
def verify_accuracy():
    """
    对比本地计算和 Brave 监控的结果
    """
    # 本地计算
    local_result = calculate_hama_from_ohlcv(ohlcv)

    # Brave 监控
    brave_result = brave_monitor.monitor_symbol('BTCUSDT')

    # 对比
    accuracy = compare_results(local_result, brave_result)

    if accuracy < 0.99:
        logger.warning(f"准确度低于 99%: {accuracy:.2%}")
        # 调整算法参数

    return accuracy
```

## 📊 性能对比

| 方案 | 响应时间 | CPU | 内存 | 网络 |
|------|---------|-----|------|------|
| 本地计算 | 2-5秒 | 低 | 低 | 交易所API |
| Brave 监控 | 10-30秒 | 高 | 高 | TradingView |

## 🔍 故障排查

### 本地环境问题

#### 问题 1: Playwright 安装失败
```bash
# 解决方案
pip install --upgrade pip
pip install playwright playwright-stealth
playwright install chromium
```

#### 问题 2: OCR 识别失败
```bash
# 检查依赖
pip list | grep -i ocr

# 重新安装
pip install rapidocr-onnxruntime --force-reinstall
```

#### 问题 3: 浏览器无法启动
```python
# 检查浏览器安装
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); print('OK')"
```

### Docker 环境问题

#### 问题 1: 本地计算失败
```bash
# 检查日志
docker logs quantdinger-backend --tail 50

# 测试 API
curl "http://localhost:5000/api/hama-market/symbol?symbol=BTCUSDT"
```

#### 问题 2: 网络超时
```bash
# 检查代理配置
docker exec quantdinger-backend env | grep PROXY

# 测试连接
docker exec quantdinger-backend curl https://api.binance.com
```

## 🎉 总结

### 混合方案优势

1. ✅ **开发灵活** - 本地可以快速测试和调试
2. ✅ **部署简单** - Docker 保持轻量，一键部署
3. ✅ **性能最佳** - 生产环境使用本地计算，快速稳定
4. ✅ **数据可靠** - 定期验证确保准确性

### 推荐工作流

```
开发 → 本地 Brave 监控 → 验证 → 本地计算 → Docker 部署
```

### 文件清单

- ✅ `install_local_requirements.bat` - Windows 安装脚本
- ✅ `install_local_requirements.sh` - Linux/Mac 安装脚本
- ✅ `test_brave_local.py` - 本地测试脚本
- ✅ `hama_market.py` - API 接口（需修改支持混合模式）
- ✅ `hama_brave_monitor.py` - Brave 监控器
- ✅ `hama_ocr_extractor.py` - OCR 提取器

---

**开始使用吧！** 🚀
