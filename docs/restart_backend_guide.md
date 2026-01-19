# 重启后端服务以加载 HAMA 分析功能

## 问题说明

新增的 `gainer_analysis_bp` blueprint 需要重启后端服务才能生效。

## 重启步骤

### 方法 1: Docker 部署 (推荐)

```bash
cd d:\github\QuantDinger

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
```

### 方法 2: 本地开发

```bash
cd d:\github\QuantDinger\backend_api_python

# 停止当前运行的后端 (Ctrl+C)

# 重新启动
python run.py
```

## 验证服务

### 1. 检查健康状态

```bash
curl http://localhost:5000/api/health
```

应该返回:
```json
{"status":"healthy","timestamp":"..."}
```

### 2. 测试涨幅榜 API

```bash
curl "http://localhost:5000/api/gainer-analysis/top-gainers?limit=3"
```

### 3. 运行完整测试

```bash
python test_hama_real_data.py
```

## 常见问题

### 1. ImportError: No module named 'numpy'

**解决方案**:
```bash
cd backend_api_python
pip install numpy
```

### 2. CCXT 配置错误

**解决方案**:
检查 `.env` 文件中的交易所配置:
```
CCXT_DEFAULT_EXCHANGE=okx
```

### 3. 代理配置问题

**解决方案**:
确保 `.env` 中配置了代理:
```
PROXY_PORT=7890
```

或使用完整代理 URL:
```
PROXY_URL=socks5h://127.0.0.1:7890
```

### 4. TradingView API 连接失败

**原因**:
- TradingView 可能需要代理才能访问
- 网络限制或防火墙阻止

**解决方案**:
系统会自动降级到模拟数据,确保服务可用性。

## 日志检查

### Docker 日志
```bash
docker-compose logs -f backend
```

### 本地日志
```bash
tail -f backend_api_python/logs/app.log
```

## 功能说明

重启后,以下 API 将可用:

1. **GET /api/gainer-analysis/top-gainers**
   - 获取币安涨幅榜前N名
   - 自动进行 HAMA 指标分析
   - 参数: limit (1-100), market (spot/futures)

2. **POST /api/gainer-analysis/analyze-symbol**
   - 分析单个币种
   - 请求体: {"symbol": "BTCUSDT"}

3. **POST /api/gainer-analysis/refresh**
   - 刷新涨幅榜数据
   - 请求体: {"limit": 20, "market": "spot"}

## 性能优化建议

1. **缓存**: 可以添加 Redis 缓存 TradingView 数据
2. **异步**: 使用异步请求提高批量分析速度
3. **限流**: 避免过于频繁的 API 调用

## 监控

重启后,可以访问前端页面:
- 路径: `/gainer-analysis`
- 功能: 查看涨幅榜和 HAMA 分析

或使用测试脚本验证功能:
```bash
python test_hama_real_data.py
```
