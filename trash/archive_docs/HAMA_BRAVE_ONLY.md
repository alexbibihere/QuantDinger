# HAMA 行情页面 - 仅展示 Brave 监控数据

## 修改说明

已修改 [`hama_market.py`](backend_api_python/app/routes/hama_market.py) 使其**只展示通过 Brave 监控 OCR 识别的数据**。

## 修改内容

### 之前 (显示本地计算备用数据)
```python
if brave_hama:
    # 显示 Brave 监控数据
else:
    # 显示本地计算数据作为备用 ❌
```

### 现在 (仅显示 Brave 监控数据)
```python
if brave_hama:
    # 显示 Brave 监控数据 ✅
else:
    # 不显示任何数据 ✅
    item = {
        'symbol': symbol,
        'price': 0,
        'hama_brave': None
    }
```

## 数据展示规则

- ✅ **显示**: 有 Brave 监控 OCR 识别数据
- ❌ **不显示**: 没有 Brave 监控数据 (hama_brave = null)

## 如何获取 Brave 监控数据

### 方法 1: 运行自动监控脚本
```bash
cd backend_api_python
python auto_hama_monitor_mysql.py
```

### 方法 2: 前端手动触发
1. 访问 http://localhost:8000/#/hama-market
2. 点击 "刷新 Brave 监控" 按钮
3. 等待监控完成 (每个币种约20-30秒)

### 方法 3: API 手动触发
```bash
curl -X POST "http://localhost:5000/api/hama-monitor/monitor" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]}'
```

## 前端显示效果

### 有 Brave 监控数据
```
币种       价格        HAMA颜色    HAMA数值    趋势
BTCUSDT    95159.0     🟢绿色      95117.59    上涨
```

### 无 Brave 监控数据
```
币种       价格        HAMA颜色    HAMA数值    趋势
ETHUSDT    0          -           -           暂未监控
```

## 下一步操作

**请重启后端服务:**
```bash
# 停止当前服务 (Ctrl+C)
# 然后重新启动
cd backend_api_python
python run.py
```

**然后启动 Brave 监控:**
```bash
# 新开一个终端窗口
cd backend_api_python
python auto_hama_monitor_mysql.py
```

## 验证步骤

1. **重启后端** (使代码修改生效)
2. **启动监控** (运行自动监控脚本)
3. **等待监控完成** (首次监控需要几分钟)
4. **刷新前端页面** (查看数据)

---

**修改状态**: ✅ 已完成
**等待**: 重启后端服务
**最后更新**: 2026-01-18
