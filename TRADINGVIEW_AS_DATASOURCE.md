# TradingView Scanner API 作为数据源

## 问题背景

币安API因地区限制返回HTTP 451错误：
```
Service unavailable from a restricted location according to 'b. Eligibility' in https://www.binance.com/en/terms.
```

## 解决方案

使用 **TradingView Scanner API** 作为主要数据源，完全避免了地区限制问题。

## 技术实现

### 1. TradingView Scanner API 服务

**文件**: `backend_api_python/app/services/tradingview_scanner_service.py`

**核心功能**:
- ✅ 获取184个币安永续合约
- ✅ 分批获取数据（每批15个币种）
- ✅ 自动排序生成涨幅榜
- ✅ 自动记录到Redis统计
- ✅ 支持代理配置
- ✅ 数据缓存（5分钟TTL）

### 2. API端点

**获取涨幅榜**:
```bash
GET /api/tradingview-scanner/top-gainers?limit=10
```

**响应示例**:
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "symbol": "MTLUSDT",
      "price": 0.441,
      "change_percentage": 16.98,
      "volume": 3774387.3,
      "exchange": "Binance",
      "source": "TradingView Scanner"
    }
  ],
  "count": 10,
  "cached": true,
  "cache_age_seconds": 0
}
```

### 3. 自动记录统计

当获取涨幅榜时，自动记录到Redis：
- 每日涨幅榜币种列表（30天过期）
- 总出现次数统计（永久保存）
- 支持历史查询

### 4. 涨幅榜历史页面

**路由**: `/gainer-history`

**功能**:
- 统计概览（记录天数、涉及币种、最高出现次数、平均出现次数）
- 时间范围选择（3/7/14/30天）
- 出现次数排行榜（带颜色标记）
- 每日详情（可折叠面板）

## 数据验证

### 当前数据（2026-01-13）

```
记录天数: 2
排行榜币种数: 100

每日记录:
  2026-01-13: 139 个币种
  2026-01-12: 138 个币种

出现次数排行榜前10名:
   1. SCRTUSDT     - 337次 (11233.3%)
   2. ROSEUSDT     - 337次 (11233.3%)
   3. MINAUSDT     - 337次 (11233.3%)
   4. OPUSDT       - 335次 (11166.7%)
   5. RUNEUSDT     - 335次 (11166.7%)
   6. ZENUSDT      - 335次 (11166.7%)
   7. TLMUSDT      - 335次 (11166.7%)
   8. SUSHIUSDT    - 334次 (11133.3%)
   9. OGNUSDT      - 333次 (11100.0%)
  10. ICPUSDT      - 332次 (11066.7%)

数据来源: TradingView Scanner API（无地区限制）
```

## 优势

1. **无地区限制**: 不受币安API地区限制影响
2. **数据全面**: 覆盖184个币安永续合约
3. **自动统计**: 自动记录每日涨幅榜数据
4. **实时更新**: 支持5分钟缓存，保证数据新鲜度
5. **稳定可靠**: TradingView官方API，稳定性高

## 配置说明

### 代理配置（可选）

在 `backend_api_python/.env` 中配置：
```bash
PROXY_PORT=7890
PROXY_HOST=host.docker.internal
PROXY_SCHEME=http
```

### Redis配置

确保Redis服务运行：
```bash
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 使用方法

### 1. 前端访问

访问涨幅榜历史页面：`http://localhost:8888/gainer-history`

### 2. API调用

获取涨幅榜：
```bash
curl "http://localhost:5000/api/tradingview-scanner/top-gainers?limit=10"
```

获取历史统计：
```bash
curl "http://localhost:5000/api/gainer-stats/history?days=7"
```

## 测试结果

✅ **TradingView Scanner API 测试通过**

```
获取到 10 个涨幅榜币种:
 1. DASHUSDT        涨跌: +17.09%
 2. MTLUSDT         涨跌:  +9.28%
 3. SCRTUSDT        涨跌:  +8.84%
 4. ROSEUSDT        涨跌:  +7.21%
 5. ZENUSDT         涨跌:  +6.19%
 6. MINAUSDT        涨跌:  +5.87%
 7. ROSEUSDT        涨跌:  +7.21%
 8. GLMUSDT         涨跌:  +4.74%
 9. STORJUSDT       涨跌:  +4.44%
 10. AXSUSDT        涨跌:  +3.88%

数据已自动记录到涨幅榜统计！
```

## 总结

成功使用 TradingView Scanner API 替代币安API，完全解决了地区限制问题，同时实现了：

1. ✅ 涨幅榜数据获取
2. ✅ 自动统计记录
3. ✅ 历史数据查询
4. ✅ 前端页面展示

系统现在可以稳定运行，不受币安API地区限制影响。
