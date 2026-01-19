# 截图缓存系统 - 快速使用指南

## 📊 功能概述

将 TradingView 图表截图保存到数据库,避免重复截图,大幅提升响应速度。

## 🎯 核心优势

| 特性 | 说明 |
|------|------|
| **速度提升** | 从 22秒 → 0.2秒 (**100倍**) |
| **持久化** | 数据库存储,重启不丢失 |
| **自动管理** | 双缓存策略,自动迁移 |
| **简单易用** | 一个API调用即可 |

## 🚀 快速开始

### 1. 获取截图 (自动缓存)

```bash
# 基础调用
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&interval=15m"

# 完整参数
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&interval=15m&force_refresh=false"
```

**参数说明**:
- `symbol`: 币种符号 (如 BTCUSDT, ETHUSDT)
- `interval`: 时间周期 (15m, 1h, 4h, 1d)
- `force_refresh`: 是否强制刷新 (true/false, 默认false)

**响应示例**:
```json
{
    "success": true,
    "symbol": "BTCUSDT",
    "interval": "15m",
    "image_base64": "iVBORw0KGgoAAAANS...",
    "content_type": "image/png",
    "cached": true
}
```

### 2. 查看缓存统计

```bash
curl "http://localhost:5000/api/tradingview-scanner/screenshot-cache/stats"
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total_screenshots": 10,
        "total_size_mb": 1.5,
        "top_symbols": [
            ["BTCUSDT", 3],
            ["ETHUSDT", 2]
        ]
    }
}
```

### 3. 清理旧缓存

```bash
# 清理7天前的截图
curl -X POST "http://localhost:5000/api/tradingview-scanner/screenshot-cache/cleanup" \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

## 💻 前端集成

### Vue.js 示例

```vue
<template>
  <div>
    <a-button @click="loadScreenshot">加载图表</a-button>
    <img v-if="imageUrl" :src="imageUrl" alt="TradingView图表" />
    <p v-if="cached">✅ 来自缓存</p>
    <p v-else>⏱️ 首次加载需要20秒...</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      imageUrl: '',
      cached: false
    }
  },
  methods: {
    async loadScreenshot() {
      try {
        const response = await this.$http.get('/api/tradingview-scanner/chart-screenshot', {
          params: {
            symbol: 'BTCUSDT',
            interval: '15m'
          }
        })

        const { image_base64, cached } = response.data
        this.imageUrl = `data:image/png;base64,${image_base64}`
        this.cached = cached

        if (cached) {
          this.$message.success('从缓存加载 (0.2秒)')
        } else {
          this.$message.info('首次加载需要20秒...')
        }
      } catch (error) {
        this.$message.error('加载失败: ' + error.message)
      }
    }
  }
}
</script>
```

### React 示例

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function ChartScreenshot({ symbol, interval }) {
  const [imageUrl, setImageUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [cached, setCached] = useState(false);

  const loadScreenshot = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/tradingview-scanner/chart-screenshot', {
        params: { symbol, interval }
      });

      const { image_base64, cached: isCached } = response.data;
      setImageUrl(`data:image/png;base64,${image_base64}`);
      setCached(isCached);
    } catch (error) {
      console.error('加载失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={loadScreenshot} disabled={loading}>
        {loading ? '加载中...' : '加载图表'}
      </button>
      {imageUrl && <img src={imageUrl} alt="TradingView图表" />}
      {cached && <p>✅ 来自缓存</p>}
    </div>
  );
}

export default ChartScreenshot;
```

## 🐍 Python 示例

```python
import requests
import base64

def get_chart_screenshot(symbol='BTCUSDT', interval='15m'):
    """获取图表截图"""
    url = 'http://localhost:5000/api/tradingview-scanner/chart-screenshot'

    response = requests.get(url, params={
        'symbol': symbol,
        'interval': interval
    })

    data = response.json()

    if data['success']:
        # 解码base64图片
        image_data = base64.b64decode(data['image_base64'])

        # 保存到文件
        filename = f'{symbol}_{interval}.png'
        with open(filename, 'wb') as f:
            f.write(image_data)

        print(f"✅ 截图已保存: {filename}")
        print(f"   是否缓存: {data['cached']}")
        print(f"   文件大小: {len(image_data)} bytes")

        return filename
    else:
        print(f"❌ 获取失败: {data['error']}")
        return None

# 使用示例
get_chart_screenshot('BTCUSDT', '15m')
```

## 📈 性能对比

### 首次访问
```
用户请求 → 访问TradingView → 等待加载 → 截图 → 保存到数据库
耗时: ~22秒
```

### 缓存命中
```
用户请求 → 从数据库读取 → 返回图片
耗时: ~0.2秒

速度提升: 100倍! 🚀
```

## 🔧 定时任务 (可选)

### 自动预缓存热门币种

```python
import time
import requests

def cache_popular_symbols():
    """自动缓存热门币种"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

    for symbol in symbols:
        print(f"正在缓存 {symbol}...")
        response = requests.get(
            'http://localhost:5000/api/tradingview-scanner/chart-screenshot',
            params={'symbol': symbol, 'interval': '15m'}
        )

        if response.json().get('success'):
            print(f"✅ {symbol} 缓存成功")

        time.sleep(1)  # 避免请求过快

if __name__ == '__main__':
    cache_popular_symbols()
```

### 定时清理旧缓存

```python
import schedule
import time
import requests

def cleanup_old_screenshots():
    """清理超过7天的截图"""
    response = requests.post(
        'http://localhost:5000/api/tradingview-scanner/screenshot-cache/cleanup',
        json={'days': 7}
    )

    data = response.json()
    print(f"✅ 已清理 {data['deleted_count']} 条旧截图")

# 每周日凌晨2点清理
schedule.every().sunday.at("02:00").do(cleanup_old_screenshots)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 🛠️ 故障排查

### 问题1: 缓存未命中

**原因**: 首次访问或缓存被清理

**解决**:
```bash
# 检查缓存统计
curl "http://localhost:5000/api/tradingview-scanner/screenshot-cache/stats"

# 强制刷新
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&force_refresh=true"
```

### 问题2: 数据库过大

**原因**: 缓存过多截图

**解决**:
```bash
# 清理旧截图
curl -X POST "http://localhost:5000/api/tradingview-scanner/screenshot-cache/cleanup" \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

### 问题3: 截图失败

**原因**: 网络问题或 TradingView 访问受限

**解决**:
1. 检查代理配置
2. 查看 Redis 是否可用
3. 查看后端日志

## 📊 监控指标

建议监控以下指标:

```python
import requests

def get_cache_stats():
    """获取缓存统计"""
    response = requests.get(
        'http://localhost:5000/api/tradingview-scanner/screenshot-cache/stats'
    )
    data = response.json()['data']

    print(f"总截图数: {data['total_screenshots']}")
    print(f"总大小: {data['total_size_mb']} MB")
    print(f"热门币种:")

    for symbol, count in data['top_symbols'][:5]:
        print(f"  - {symbol}: {count} 张")

get_cache_stats()
```

## 🎓 最佳实践

1. **预缓存热门币种**
   - 在低峰期预先缓存
   - 减少用户等待时间

2. **定期清理旧缓存**
   - 每周清理一次
   - 避免数据库过大

3. **监控缓存命中率**
   - 目标: > 90%
   - 低于目标增加预缓存

4. **合理设置刷新频率**
   - 热门币种: 每小时
   - 普通币种: 每天
   - 冷门币种: 按需

## 📚 相关文档

- [优化总结](SCREENSHOT_CACHE_OPTIMIZATION.md)
- [验证报告](SCREENSHOT_CACHE_VERIFICATION.md)

---

**最后更新**: 2026-01-18
**版本**: 1.0.0
**状态**: ✅ 生产就绪
