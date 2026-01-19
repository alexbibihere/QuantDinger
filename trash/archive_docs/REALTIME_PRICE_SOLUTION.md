# 实时价格更新方案对比

## 方案对比

### 方案 1: WebSocket (推荐) ⭐⭐⭐⭐⭐

**优点**:
- 双向通信,服务器主动推送
- 实时性最好 (< 100ms 延迟)
- 连接复用,开销小
- 支持断线重连

**缺点**:
- 实现相对复杂
- 需要维护连接状态

**适用场景**: 高频交易、实时监控

**技术栈**:
- 后端: Flask-SocketIO / WebSocket
- 前端: Socket.IO / native WebSocket

---

### 方案 2: Server-Sent Events (SSE) ⭐⭐⭐⭐

**优点**:
- 单向推送,服务器主动推送
- 实时性好 (< 500ms 延迟)
- 实现简单,基于 HTTP
- 自动重连

**缺点**:
- 只能服务器推送到客户端
- 不支持二进制数据

**适用场景**: 价格推送、行情更新

**技术栈**:
- 后端: Flask SSE
- 前端: EventSource API

---

### 方案 3: 轮询 (Polling) ⭐⭐⭐

**优点**:
- 实现最简单
- 兼容性好

**缺点**:
- 延迟高 (取决于轮询间隔)
- 服务器压力大
- 浪费资源 (很多无效请求)

**适用场景**: 低频更新

**技术栈**:
- 前端: setInterval + axios
- 后端: 无需特殊处理

---

### 方案 4: 长轮询 (Long Polling) ⭐⭐

**优点**:
- 比普通轮询实时性好
- 减少无效请求

**缺点**:
- 服务器连接占用时间长
- 实现复杂度中等

**适用场景**: 中等实时性要求

---

## 推荐方案

### 🎯 当前项目推荐: SSE (Server-Sent Events)

**理由**:
1. **单向推送**: 价格只需要从服务器推送到前端
2. **实时性好**: 延迟 < 500ms,满足交易需求
3. **实现简单**: 比 WebSocket 简单很多
4. **兼容性好**: 浏览器原生支持
5. **自动重连**: 断线自动重连,无需手动处理

## SSE 实现方案

### 后端实现 (Python Flask)

```python
from flask import Response, stream_with_context
import json
import time
from queue import Queue

# 价格更新队列
price_queues = set()

@app.route('/api/realtime/prices')
def realtime_prices():
    """SSE 实时价格推送"""
    def event_stream():
        q = Queue()
        price_queues.add(q)

        try:
            while True:
                # 从队列获取价格更新
                price_data = q.get(timeout=60)  # 60秒超时

                # 发送SSE事件
                yield f"data: {json.dumps(price_data)}\n\n"

        except GeneratorExit:
            price_queues.remove(q)

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

def broadcast_price(symbol, price):
    """广播价格更新到所有连接的客户端"""
    for q in price_queues:
        q.put({
            'symbol': symbol,
            'price': price,
            'timestamp': time.time()
        })
```

### 前端实现 (Vue.js)

```javascript
// 创建 SSE 连接
const eventSource = new EventSource('http://localhost:5000/api/realtime/prices')

// 监听价格更新
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)

  // 更新页面上的价格
  this.updatePrice(data.symbol, data.price)
}

// 错误处理
eventSource.onerror = (error) => {
  console.error('SSE connection error:', error)
  eventSource.close()

  // 3秒后重连
  setTimeout(() => {
    this.connectSSE()
  }, 3000)
}

// 组件销毁时关闭连接
beforeDestroy() {
  if (this.eventSource) {
    this.eventSource.close()
  }
}
```

## 价格数据来源

### 方案 1: Binance WebSocket API (推荐)

```python
import asyncio
import websockets
import json

async def binance_price_feed():
    """从 Binance WebSocket 获取实时价格"""
    uri = "wss://stream.binance.com:9443/ws/!ticker@arr"

    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            prices = json.loads(data)

            # 广播价格到所有SSE客户端
            for ticker in prices:
                symbol = ticker['s'].replace('USDT', 'USDT')
                price = float(ticker['c'])
                broadcast_price(symbol, price)
```

### 方案 2: Redis Pub/Sub

```python
import redis
import json

# Redis 发布者
redis_client = redis.Redis(host='localhost', port=6379)

def publish_price(symbol, price):
    """发布价格到Redis"""
    redis_client.publish(
        'price_updates',
        json.dumps({
            'symbol': symbol,
            'price': price,
            'timestamp': time.time()
        })
    )

# Redis 订阅者 (后台线程)
def subscribe_prices():
    """订阅Redis价格更新"""
    pubsub = redis_client.pubsub()
    pubsub.subscribe('price_updates')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            broadcast_price(data['symbol'], data['price'])
```

## 集成到现有系统

### 1. 修改 HAMA 定时任务

```python
def _refresh_hama_data(self):
    """刷新所有币种的HAMA数据"""
    for symbol in self.symbols:
        # 获取HAMA分析
        analysis = self.tv_service.get_hama_cryptocurrency_signals(symbol)

        # 获取实时价格
        realtime_price = self._get_realtime_price(symbol)

        # 广播价格更新
        broadcast_price(symbol, realtime_price)

        # 保存到Redis
        self.cache_manager.set(symbol, result_data)
```

### 2. 前端页面集成

```vue
<template>
  <div>
    <a-table :dataSource="dataSource" :columns="columns">
      <!-- 价格列 -->
      <template slot="price" slot-scope="text, record">
        <span :class="getPriceClass(record)">
          {{ formatPrice(record.price) }}
        </span>
        <a-icon
          v-if="record.priceChanged"
          type="arrow-up"
          :class="record.priceDirection === 'up' ? 'up' : 'down'"
        />
      </template>
    </a-table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      eventSource: null,
      priceHistory: {}
    }
  },

  mounted() {
    this.connectSSE()
  },

  methods: {
    connectSSE() {
      this.eventSource = new EventSource('http://localhost:5000/api/realtime/prices')

      this.eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.updatePrice(data)
      }
    },

    updatePrice(data) {
      const oldPrice = this.priceHistory[data.symbol]
      const priceChanged = oldPrice !== data.price

      // 更新数据源
      const item = this.dataSource.find(i => i.symbol === data.symbol)
      if (item) {
        this.$set(item, 'price', data.price)
        this.$set(item, 'priceChanged', priceChanged)
        this.$set(item, 'priceDirection', data.price > oldPrice ? 'up' : 'down')
      }

      this.priceHistory[data.symbol] = data.price
    }
  },

  beforeDestroy() {
    if (this.eventSource) {
      this.eventSource.close()
    }
  }
}
</script>

<style scoped>
.up { color: #52c41a; }
.down { color: #ff4d4f; }
</style>
```

## 性能优化

### 1. 批量推送
```python
# 不要每个价格都推送,而是批量推送
price_batch = []
for symbol in symbols:
    price_batch.append({'symbol': symbol, 'price': get_price(symbol)})

    if len(price_batch) >= 10:
        broadcast_batch(price_batch)
        price_batch = []
```

### 2. 只推送变化的币种
```python
old_prices = redis_client.hgetall('last_prices')
new_prices = {s: get_price(s) for s in symbols}

# 只推送价格变化的币种
changes = {
    s: new_prices[s]
    for s in symbols
    if old_prices.get(s) != new_prices[s]
}

if changes:
    broadcast_batch(changes)
    redis_client.hset('last_prices', changes)
```

### 3. 客户端节流
```javascript
// 使用 lodash 节流,避免频繁更新UI
import { throttle } from 'lodash'

methods: {
  updatePrice: throttle(function(data) {
    // 更新UI
    this.$set(this.dataSource, data.symbol, data)
  }, 1000) // 1秒内最多更新一次
}
```

## 总结

| 方案 | 实时性 | 复杂度 | 推荐度 |
|------|--------|--------|--------|
| SSE | < 500ms | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| WebSocket | < 100ms | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 轮询 | 取决于间隔 | ⭐ | ⭐⭐ |
| 长轮询 | < 1s | ⭐⭐⭐ | ⭐⭐⭐ |

**推荐**: SSE (Server-Sent Events)
- 实时性足够
- 实现简单
- 维护成本低

如果你需要更高实时性 (< 100ms),可以选择 WebSocket。
