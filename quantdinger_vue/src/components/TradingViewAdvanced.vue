/**
 * TradingView 高级图表组件
 * 支持预加载自定义指标和更强大的功能
 */
<template>
  <div class="tradingview-advanced-container">
    <div id="tradingview-widget-container" ref="tvContainer"></div>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'

export default {
  name: 'TradingViewAdvanced',
  props: {
    symbol: {
      type: String,
      default: 'BTCUSDT'
    },
    interval: {
      type: String,
      default: '1D'
    },
    theme: {
      type: String,
      default: 'light'
    },
    height: {
      type: String,
      default: '100%'
    },
    // 自定义 Pine Script 代码
    customPineScript: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const tvContainer = ref(null)
    let widget = null

    // 时间周期映射
    const intervalMap = {
      '1m': '1',
      '5m': '5',
      '15m': '15',
      '30m': '30',
      '1H': '60',
      '4H': '240',
      '1D': 'D',
      '1W': 'W'
    }

    // 币种格式转换
    const formatSymbol = (symbol) => {
      const s = symbol.toUpperCase()
      if (s.includes('/')) {
        return s.replace('/', '')
      }
      return s
    }

    // 创建 TradingView Widget
    const createWidget = () => {
      if (!tvContainer.value) return

      // 清除旧 widget
      if (widget) {
        widget.remove()
        widget = null
      }

      const symbol = formatSymbol(props.symbol)
      const interval = intervalMap[props.interval] || 'D'

      // 使用 TradingView Advanced Real-Time Chart Widget
      // 这个版本支持通过 URL 参数预加载指标
      const config = {
        autosize: true,
        symbol: `BINANCE:${symbol}`,
        interval: interval,
        timezone: 'Etc/UTC',
        theme: props.theme,
        style: '1',
        locale: 'zh_CN',
        toolbar_bg: '#f1f3f6',
        enable_publishing: false,
        allow_symbol_change: true,
        hide_side_toolbar: false,
        details: true,
        calendar: true,
        hotlist: true,
        news: [
          'headlines'
        ],
        // studies - 可以预加载内置指标
        studies: [
          'MASimple@tv-basicstudies',
          'RSI@tv-basicstudies',
          'MACD@tv-basicstudies'
        ],
        // 通过 studies_overrides 可以添加自定义指标
        studies_overrides: {},
        // 通过 overrides 可以自定义指标参数
        overrides: {
          'paneProperties.background': props.theme === 'dark' ? '#131722' : '#ffffff',
          'paneProperties.vertGridProperties.color': props.theme === 'dark' ? '#1f2943' : '#e6e9f0',
          'paneProperties.horzGridProperties.color': props.theme === 'dark' ? '#1f2943' : '#e6e9f0',
          'scalesProperties.textColor': props.theme === 'dark' ? '#d1d4dc' : '#131722'
        },
        container_id: 'tradingview-widget-container',
        load_last_symbol: true,
        // 添加自定义研究
        custom_indicators_getter: (PineJS) => {
          // 返回自定义指标数组
          return Promise.resolve([
            // 如果有自定义 Pine Script，可以在这里添加
            // 这是一个示例，实际使用需要通过 TradingView Widget API
          ])
        }
      }

      // 动态加载 TradingView Widget Library
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/tv.js'
      script.async = true
      script.onload = () => {
        // eslint-disable-next-line no-undef
        widget = new TradingView.widget(config)
        console.log('✅ TradingView Advanced Widget 已创建')
      }
      script.onerror = () => {
        console.error('❌ 加载 TradingView Widget 失败')
      }
      document.head.appendChild(script)
    }

    // 监听 props 变化
    watch(() => props.symbol, () => {
      createWidget()
    })

    watch(() => props.interval, () => {
      createWidget()
    })

    watch(() => props.theme, () => {
      createWidget()
    })

    onMounted(() => {
      createWidget()
    })

    onBeforeUnmount(() => {
      if (widget) {
        widget.remove()
        widget = null
      }
    })

    return {
      tvContainer
    }
  }
}
</script>

<style lang="less" scoped>
.tradingview-advanced-container {
  width: 100%;
  height: 100%;
  min-height: 500px;

  #tradingview-widget-container {
    width: 100%;
    height: 100%;
  }
}
</style>
