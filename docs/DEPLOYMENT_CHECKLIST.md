# ✅ Docker 部署检查清单 - 涨幅榜分析功能

## 📋 部署前检查

### 环境准备
- [ ] Docker Desktop 已安装并运行
- [ ] Git 已安装 (用于克隆代码)
- [ ] 端口 5000 和 8888 未被占用

### 配置文件
- [ ] `.env` 文件存在于 `backend_api_python/` 目录
- [ ] `CCXT_DEFAULT_EXCHANGE` 已设置 (okx 或 binance)
- [ ] `PROXY_PORT` 已配置 (可选但推荐)
- [ ] `SECRET_KEY` 已设置 (生产环境必需)
- [ ] `ADMIN_USER` 和 `ADMIN_PASSWORD` 已配置

### 依赖检查
- [ ] `requirements.txt` 包含 `numpy>=1.24.0`
- [ ] `requirements.txt` 包含 `ccxt>=4.0.0`
- [ ] `requirements.txt` 包含所有必需依赖

### 文件结构
```
QuantDinger/
├── docker-compose.yml          ✅
├── restart_services.bat        ✅ (Windows)
├── restart_services.sh         ✅ (Linux/Mac)
├── backend_api_python/
│   ├── .env                   ✅
│   ├── Dockerfile             ✅
│   ├── requirements.txt       ✅ (含 numpy)
│   ├── run.py                 ✅
│   ├── app/
│   │   ├── routes/
│   │   │   ├── __init__.py   ✅ (已注册 gainer_analysis_bp)
│   │   │   └── gainer_analysis.py ✅
│   │   └── services/
│   │       ├── binance_gainer.py ✅
│   │       └── tradingview_service.py ✅
│   └── data/                  ✅ (可写)
└── quantdinger_vue/
    ├── src/
    │   ├── views/gainer-analysis/ ✅
    │   ├── api/gainerAnalysis.js ✅
    │   ├── config/router.config.js ✅
    │   └── locales/lang/zh-CN.js ✅
    └── dockerfile              ✅
```

## 🚀 部署步骤

### 方式 1: 使用脚本 (推荐)

**Windows:**
```bash
# 双击运行
restart_services.bat
```

**Linux/Mac:**
```bash
# 命令行运行
./restart_services.sh
```

### 方式 2: 手动命令

```bash
# 1. 停止旧容器
docker-compose down

# 2. 重新构建
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f backend
```

## ✅ 部署验证

### 1. 容器状态检查

```bash
docker-compose ps
```

**预期结果:**
```
NAME                      STATUS
quantdinger-backend       Up (healthy)
quantdinger-frontend      Up (healthy)
```

### 2. 后端健康检查

```bash
curl http://localhost:5000/api/health
```

**预期结果:**
```json
{"status":"healthy","timestamp":"..."}
```

### 3. API 端点检查

```bash
# 测试涨幅榜 API
curl "http://localhost:5000/api/gainer-analysis/top-gainers?limit=3"
```

**预期结果:**
- 返回 JSON 数据
- 包含 `symbols` 数组
- 每个 symbol 包含 `hama_analysis` 和 `conditions`

### 4. 前端访问

**访问地址:** http://localhost:8888

**检查项:**
- [ ] 登录页面正常显示
- [ ] 可以成功登录 (quantdinger/123456)
- [ ] 菜单中显示"涨幅榜分析"
- [ ] 点击后跳转到 `/gainer-analysis`

### 5. 功能测试

**在涨幅榜页面:**
- [ ] 页面正常加载，显示统计卡片
- [ ] 表格显示币种列表
- [ ] 市场类型切换正常 (现货/合约)
- [ ] 刷新按钮功能正常
- [ ] 点击"详情"按钮弹出分析弹窗
- [ ] TradingView 链接可跳转

**数据验证:**
- [ ] 显示 HAMA 趋势 (上升/下降/横盘)
- [ ] 显示交易建议 (BUY/SELL/HOLD)
- [ ] 显示置信度 (30% - 95%)
- [ ] 显示技术指标 (RSI, MACD, EMA 等)

## 🔍 问题排查

### 问题 1: 容器无法启动

**检查:**
```bash
# 查看详细日志
docker-compose logs backend

# 检查配置
cat backend_api_python/.env
```

**常见原因:**
- .env 文件缺失或配置错误
- 端口被占用
- Docker 资源不足

**解决:**
```bash
# 重建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 问题 2: API 返回 404

**原因:** blueprint 未注册

**解决:**
```bash
# 完全重启
docker-compose down
docker-compose up -d --build
```

### 问题 3: 数据加载失败

**检查:**
```bash
# 查看日志
docker-compose logs backend | grep -i "error"

# 测试网络连接
docker exec -it quantdinger-backend curl -I https://scanner.tradingview.com
```

**可能原因:**
- 网络限制
- 代理配置问题
- 数据源不可用

**解决:**
- 检查代理配置
- 系统会自动降级到模拟数据
- 等待重试

### 问题 4: 前端页面空白

**检查:**
```bash
# 查看前端日志
docker-compose logs frontend

# 检查前端构建
docker-compose logs frontend | grep -i "error"
```

**解决:**
```bash
# 重启前端
docker-compose restart frontend
```

## 📊 性能检查

### 容器资源使用

```bash
docker stats quantdinger-backend quantdinger-frontend
```

**正常范围:**
- CPU: < 50%
- 内存: < 1GB
- 网络: 根据使用情况

### 响应时间测试

```bash
# 测试后端响应
time curl "http://localhost:5000/api/gainer-analysis/top-gainers?limit=5"
```

**预期:** < 30 秒 (首次加载可能较慢)

## 🎯 功能验证清单

### 基本功能
- [ ] 登录系统
- [ ] 访问涨幅榜页面
- [ ] 查看币种列表
- [ ] 查看统计卡片

### HAMA 分析
- [ ] 趋势显示 (上升/下降/横盘)
- [ ] 蜡烛图形态识别
- [ ] 交易建议 (BUY/SELL/HOLD)
- [ ] 置信度计算
- [ ] 技术指标展示

### 交互功能
- [ ] 市场类型切换
- [ ] 刷新数据
- [ ] 查看详情弹窗
- [ ] TradingView 跳转

### 数据准确性
- [ ] 价格数据正确
- [ ] 涨跌幅计算准确
- [ ] RSI 指标合理 (0-100)
- [ ] EMA 指标合理
- [ ] 支撑/阻力位合理

## 📝 部署记录

### 部署信息

**部署日期:** ___________

**部署人员:** ___________

**环境信息:**
- Docker 版本: ___________
- 操作系统: ___________
- Python 版本: ___________
- Node 版本: ___________

**配置信息:**
- 交易所: ___________
- 代理端口: ___________
- 数据源: ___________

### 部署结果

**容器状态:**
- [ ] 后端: Healthy
- [ ] 前端: Healthy

**功能测试:**
- [ ] 登录: 通过
- [ ] 涨幅榜页面: 通过
- [ ] HAMA 分析: 通过
- [ ] API 测试: 通过

**问题记录:**
1. ___________
2. ___________
3. ___________

**备注:**
___________

## 🎉 部署完成

### 下一步

1. **访问应用:** http://localhost:8888/gainer-analysis

2. **登录系统:** quantdinger / 123456

3. **开始使用:** 查看涨幅榜和 HAMA 分析

4. **监控日志:** `docker-compose logs -f backend`

### 文档参考

- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - 详细部署指南
- [GAINER_ANALYSIS_QUICK_START.md](GAINER_ANALYSIS_QUICK_START.md) - 快速开始
- [GAINER_ANALYSIS_COMPLETE.md](GAINER_ANALYSIS_COMPLETE.md) - 完整功能说明
- [HAMA_IMPLEMENTATION.md](HAMA_IMPLEMENTATION.md) - 技术实现

### 维护命令

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码
git pull
docker-compose down
docker-compose up -d --build
```

---

**部署完成后,访问 http://localhost:8888/gainer-analysis 开始使用! 🚀**
