/**
 * 实时价格 Mixin
 * 在组件中混入此 mixin 可以轻松实现实时价格更新
 */
import sseService from '@/utils/sse'

export default {
  data () {
    return {
      sseConnected: false,
      realtimePrices: {} // 存储实时价格数据 { symbol: { price, change_24h, timestamp } }
    }
  },

  mounted () {
    // 组件挂载时自动连接 SSE
    this.connectSSE()
  },

  beforeDestroy () {
    // 组件销毁时断开 SSE
    this.disconnectSSE()
  },

  methods: {
    /**
     * 连接到 SSE 服务
     */
    connectSSE () {
      sseService.connect(
        // onPriceUpdate
        this.handlePriceUpdate,
        // onConnected
        () => {
          this.sseConnected = true
          this.$message.success('已连接到实时价格服务')
        },
        // onError
        (error) => {
          this.sseConnected = false
          console.error('SSE 连接错误:', error)
        }
      )
    },

    /**
     * 断开 SSE 连接
     */
    disconnectSSE () {
      sseService.disconnect()
      this.sseConnected = false
    },

    /**
     * 处理价格更新
     * 可以在组件中覆盖此方法以自定义处理逻辑
     */
    handlePriceUpdate (priceData) {
      const { symbol, price, change24h } = priceData

      // 存储价格数据
      this.$set(this.realtimePrices, symbol, {
        price,
        change24h,
        timestamp: priceData.timestamp
      })

      // 触发自定义事件,方便父组件监听
      this.$emit('price-update', priceData)
    },

    /**
     * 获取币种的实时价格
     * @param {String} symbol - 币种符号
     * @returns {Object|null} 价格数据
     */
    getRealtimePrice (symbol) {
      return this.realtimePrices[symbol] || null
    },

    /**
     * 格式化价格显示
     * @param {String} symbol - 币种符号
     * @param {Number} fallbackPrice - 如果没有实时价格,使用此价格
     * @returns {String} 格式化后的价格
     */
    formatPrice (symbol, fallbackPrice = null) {
      const realtimeData = this.realtimePrices[symbol]
      const price = realtimeData ? realtimeData.price : fallbackPrice

      if (!price) return '-'

      // 根据价格大小决定小数位数
      if (price >= 1000) {
        return price.toFixed(2)
      } else if (price >= 1) {
        return price.toFixed(4)
      } else {
        return price.toFixed(6)
      }
    },

    /**
     * 获取涨跌幅样式
     * @param {Number} change - 涨跌幅百分比
     * @returns {Object} 样式对象
     */
    getChangeStyle (change) {
      if (!change) return {}

      return {
        color: change > 0 ? '#52c41a' : change < 0 ? '#f5222d' : ''
      }
    },

    /**
     * 获取涨跌箭头
     * @param {Number} change - 涨跌幅百分比
     * @returns {String} 箭头符号
     */
    getChangeArrow (change) {
      if (!change) return ''

      return change > 0 ? '▲' : change < 0 ? '▼' : '─'
    },

    /**
     * 格式化涨跌幅
     * @param {Number} change - 涨跌幅百分比
     * @returns {String} 格式化后的涨跌幅
     */
    formatChange (change) {
      if (!change) return '-'

      const arrow = this.getChangeArrow(change)
      const sign = change > 0 ? '+' : ''

      return `${arrow} ${sign}${change.toFixed(2)}%`
    },

    /**
     * 检查价格是否刚更新
     * 用于显示闪烁效果
     * @param {String} symbol - 币种符号
     * @param {Number} milliseconds - 毫秒数 (默认 500ms)
     * @returns {Boolean}
     */
    isPriceJustUpdated (symbol, milliseconds = 500) {
      const data = this.realtimePrices[symbol]
      if (!data || !data.timestamp) return false

      const now = new Date().getTime()
      const timestamp = new Date(data.timestamp).getTime()

      return (now - timestamp) < milliseconds
    }
  },

  computed: {
    /**
     * SSE 连接状态文本
     */
    sseStatusText () {
      return this.sseConnected ? '已连接' : '未连接'
    },

    /**
     * SSE 连接状态颜色
     */
    sseStatusColor () {
      return this.sseConnected ? 'success' : 'default'
    }
  }
}
