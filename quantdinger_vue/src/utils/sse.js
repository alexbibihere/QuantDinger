/**
 * SSE (Server-Sent Events) 实时价格推送服务
 */
import { Message } from 'ant-design-vue'

class SSEPriceService {
  constructor () {
    this.eventSource = null
    this.listeners = new Map() // 存储价格更新监听器
    this.isConnected = false
    this.retryCount = 0
    this.maxRetries = 5
    this.retryDelay = 3000 // 3秒
    this.reconnectTimer = null
  }

  /**
   * 连接到 SSE 价格推送服务
   * @param {Function} onPriceUpdate - 价格更新回调函数
   * @param {Function} onConnected - 连接成功回调
   * @param {Function} onError - 错误回调
   */
  connect (onPriceUpdate, onConnected, onError) {
    if (this.eventSource) {
      console.warn('[SSE] 已存在连接,先关闭旧连接')
      this.disconnect()
    }

    try {
      const apiBase = process.env.VUE_APP_API_BASE_URL || '/api'
      const sseUrl = `${apiBase}/sse/prices`

      console.log('[SSE] 正在连接到:', sseUrl)

      this.eventSource = new EventSource(sseUrl)

      // 连接成功事件
      this.eventSource.addEventListener('connected', (event) => {
        console.log('[SSE] ✅ 已连接到价格推送服务')
        this.isConnected = true
        this.retryCount = 0

        if (onConnected) {
          const data = JSON.parse(event.data)
          onConnected(data)
        }
      })

      // 价格更新事件
      this.eventSource.addEventListener('price', (event) => {
        try {
          const priceData = JSON.parse(event.data)
          console.log('[SSE] 📡 收到价格更新:', priceData)

          // 通知所有监听器
          this.notifyListeners(priceData)

          // 调用用户自定义回调
          if (onPriceUpdate) {
            onPriceUpdate(priceData)
          }
        } catch (error) {
          console.error('[SSE] 解析价格数据失败:', error)
        }
      })

      // 心跳事件 (保持连接)
      this.eventSource.addEventListener('heartbeat', (event) => {
        // 心跳事件,用于保持连接活跃
        // console.log('[SSE] 💓 心跳')
      })

      // 错误处理
      this.eventSource.onerror = (error) => {
        console.error('[SSE] ❌ 连接错误:', error)

        this.isConnected = false

        // EventSource 会自动重连,但我们添加额外的重试逻辑
        if (this.eventSource.readyState === EventSource.CLOSED) {
          console.log('[SSE] 连接已关闭')

          if (this.retryCount < this.maxRetries) {
            this.retryCount++
            console.log(`[SSE] ${this.retryDelay / 1000}秒后重连 (${this.retryCount}/${this.maxRetries})...`)

            this.reconnectTimer = setTimeout(() => {
              console.log('[SSE] 正在重连...')
              this.connect(onPriceUpdate, onConnected, onError)
            }, this.retryDelay)
          } else {
            console.error('[SSE] 已达到最大重试次数,停止重连')
            Message.error('实时价格服务连接失败')

            if (onError) {
              onError(error)
            }
          }
        }
      }

      // 打开事件
      this.eventSource.onopen = () => {
        console.log('[SSE] 连接已打开')
      }
    } catch (error) {
      console.error('[SSE] 创建 SSE 连接失败:', error)
      Message.error('无法连接到实时价格服务')

      if (onError) {
        onError(error)
      }
    }
  }

  /**
   * 添加价格更新监听器
   * @param {String} symbol - 币种符号 (如 'BTCUSDT')
   * @param {Function} callback - 回调函数
   */
  addListener (symbol, callback) {
    if (!this.listeners.has(symbol)) {
      this.listeners.set(symbol, [])
    }
    this.listeners.get(symbol).push(callback)
    console.log(`[SSE] 添加监听器: ${symbol}`)
  }

  /**
   * 移除价格更新监听器
   * @param {String} symbol - 币种符号
   * @param {Function} callback - 回调函数
   */
  removeListener (symbol, callback) {
    if (this.listeners.has(symbol)) {
      const callbacks = this.listeners.get(symbol).filter(cb => cb !== callback)
      if (callbacks.length > 0) {
        this.listeners.set(symbol, callbacks)
      } else {
        this.listeners.delete(symbol)
      }
    }
  }

  /**
   * 通知所有监听器
   * @param {Object} priceData - 价格数据 { symbol, price, change_24h, timestamp }
   */
  notifyListeners (priceData) {
    const { symbol } = priceData

    // 通知特定币种的监听器
    if (this.listeners.has(symbol)) {
      this.listeners.get(symbol).forEach(callback => {
        try {
          callback(priceData)
        } catch (error) {
          console.error(`[SSE] 监听器回调错误 (${symbol}):`, error)
        }
      })
    }

    // 通知 'all' 监听器 (监听所有币种)
    if (this.listeners.has('all')) {
      this.listeners.get('all').forEach(callback => {
        try {
          callback(priceData)
        } catch (error) {
          console.error('[SSE] 监听器回调错误 (all):', error)
        }
      })
    }
  }

  /**
   * 断开 SSE 连接
   */
  disconnect () {
    console.log('[SSE] 正在断开连接...')

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }

    this.isConnected = false
    this.listeners.clear()
    console.log('[SSE] 已断开连接')
  }

  /**
   * 获取连接状态
   * @returns {Boolean}
   */
  getConnectionStatus () {
    return this.isConnected
  }
}

// 导出单例
export default new SSEPriceService()
