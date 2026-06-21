# BrowserAct 快速使用指南

## 🚀 5分钟快速上手

### 步骤1：安装 BrowserAct CLI

**Windows 用户：**
```bash
install_browseract.bat
```

**手动安装：**
```bash
# 1. 安装 uv 包管理器
pip install uv

# 2. 安装 BrowserAct CLI
uv tool install browser-act-cli --python 3.12

# 3. 验证安装
browser-act --version
```

### 步骤2：配置环境变量

编辑 `backend_api_python/.env` 文件：

```env
# 启用 BrowserAct 监控
BROWSERACT_MONITOR_ENABLED=true
BROWSERACT_MONITOR_METHOD=hybrid

# 性能配置
BROWSERACT_INTERVAL=300
BROWSERACT_MAX_WORKERS=5
```

### 步骤3：启动系统

```bash
start_browseract_hama.bat
```

### 步骤4：验证功能

打开浏览器访问：`http://localhost:5000/api/browseract/status`

应该看到类似的响应：
```json
{
  "success": true,
  "browseract": {
    "available": true,
    "status": {
      "type": "browseract",
      "extraction_method": "browseract_direct"
    }
  }
}
```

## 📊 核心功能使用

### 1. 监控单个交易对

```bash
# API 调用
GET http://localhost:5000/api/browseract/symbol/BTCUSDT?timeframe=15m

# Python 代码
import requests
response = requests.get('http://localhost:5000/api/browseract/symbol/BTCUSDT')
data = response.json()
print(data['data'])
```

### 2. 批量监控

```bash
# API 调用
POST http://localhost:5000/api/browseract/monitor
Content-Type: application/json

{
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "timeframe": "15m"
}
```

### 3. 性能对比

```bash
# 对比 BrowserAct 和传统方案
GET http://localhost:5000/api/browseract/compare
```

### 4. 功能测试

```bash
# 测试指定交易对
POST http://localhost:5000/api/browseract/test
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "method": "auto"
}
```

## 🎯 配置优化建议

### 高性能配置（适合活跃交易）
```env
BROWSERACT_MONITOR_METHOD=browseract
BROWSERACT_INTERVAL=180          # 3分钟
BROWSERACT_MAX_WORKERS=8         # 高并发
```

### 均衡配置（推荐）
```env
BROWSERACT_MONITOR_METHOD=hybrid
BROWSERACT_INTERVAL=300          # 5分钟
BROWSERACT_MAX_WORKERS=5
```

### 稳定性配置（适合长时间运行）
```env
BROWSERACT_MONITOR_METHOD=hybrid
BROWSERACT_INTERVAL=600          # 10分钟
BROWSERACT_MAX_WORKERS=3
```

## 🔧 常见问题解决

### Q1: BrowserAct CLI 未找到
**A:** 运行 `install_browseract.bat` 或手动安装：
```bash
uv tool install browser-act-cli --python 3.12
```

### Q2: Python 版本不兼容
**A:** BrowserAct 需要 Python 3.12+，可以：
1. 安装 Python 3.12
2. 或使用混合模式自动降级：`BROWSERACT_MONITOR_METHOD=hybrid`

### Q3: 监控数据不准确
**A:** 检查数据源配置：
```bash
# 对比两种方案
GET http://localhost:5000/api/browseract/compare

# 查看详细日志
backend_api_python/logs/app.log
```

### Q4: 速度慢或超时
**A:** 优化配置：
```env
# 减少监控数量
BROWSERACT_MONITOR_SYMBOLS=BTCUSDT,ETHUSDT

# 增加超时时间
BROWSERACT_TIMEOUT=60

# 降低并发数
BROWSERACT_MAX_WORKERS=2
```

## 📈 性能监控

### 查看监控状态
```bash
# 获取实时状态
GET http://localhost:5000/api/browseract/status

# 响应示例
{
  "browseract": {
    "available": true,
    "status": {
      "is_monitoring": true,
      "symbols_count": 10,
      "interval": 300,
      "last_monitor_time": "2026-05-21T10:30:00"
    }
  }
}
```

### 性能指标
- **响应时间**: < 5秒（BrowserAct）vs < 20秒（传统）
- **成功率**: > 95%（BrowserAct）vs > 85%（传统）
- **并发能力**: 5-8个交易对（BrowserAct）vs 2-3个（传统）

## 🎓 进阶使用

### 自定义监控策略
```python
# app/services/custom_strategy.py
from app import get_current_hama_monitor

def custom_monitoring_strategy():
    monitor = get_current_hama_monitor()

    # 高频监控核心币种
    core_symbols = ['BTCUSDT', 'ETHUSDT']
    monitor.monitor_batch_parallel(core_symbols, timeframe='5m')

    # 低频监控其他币种
    other_symbols = ['BNBUSDT', 'SOLUSDT', 'ADAUSDT']
    monitor.monitor_batch_parallel(other_symbols, timeframe='15m')
```

### 多时间周期分析
```bash
# 同时监控多个时间周期
POST http://localhost:5000/api/browseract/monitor
{
  "symbols": ["BTCUSDT"],
  "timeframes": ["5m", "15m", "1h"]
}
```

### 自动化交易信号
```python
# 根据监控结果自动交易
def on_hama_signal(data):
    if data['hama_trend'] == '金叉':
        # 执行买入策略
        execute_buy_order(data['symbol'])
    elif data['hama_trend'] == '死叉':
        # 执行卖出策略
        execute_sell_order(data['symbol'])
```

## 📞 获取帮助

- **文档**: [BrowserAct 集成说明](BROWSERACT_INTEGRATION.md)
- **API 文档**: http://localhost:5000/api/docs
- **日志文件**: `backend_api_python/logs/app.log`
- **GitHub Issues**: https://github.com/browser-act/skills/issues

## 💡 最佳实践

1. **定期检查状态**: 每天检查一次 `/api/browseract/status`
2. **监控日志**: 关注 `app.log` 中的错误和警告
3. **性能测试**: 定期运行 `/api/browseract/test` 对比性能
4. **配置优化**: 根据实际使用情况调整监控间隔和并发数
5. **数据验证**: 重要决策前验证多个数据源

---

**提示**: 首次使用建议先运行 `test_browseract.bat` 测试所有功能！