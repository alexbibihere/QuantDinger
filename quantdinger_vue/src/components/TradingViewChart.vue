<template>
  <div class="tradingview-chart-container">
    <div class="chart-header">
      <div class="header-controls">
        <a-radio-group v-model="chartMode" button-style="solid" size="small">
          <a-radio-button value="klinecharts">KlineCharts</a-radio-button>
          <a-radio-button value="tradingview">TradingView</a-radio-button>
        </a-radio-group>

        <a-tooltip v-if="chartMode === 'tradingview'" title="HAMA 指标已自动加载">
          <a-tag color="green">
            <a-icon type="check-circle" />
            HAMA + 布林带
          </a-tag>
        </a-tooltip>
      </div>
    </div>

    <!-- KlineCharts 模式 -->
    <div v-show="chartMode === 'klinecharts'" class="klinecharts-wrapper">
      <slot></slot>
    </div>

    <!-- TradingView 模式 -->
    <div v-show="chartMode === 'tradingview'" class="tradingview-wrapper">
      <div
        ref="tradingViewContainer"
        class="tradingview-widget-container"
      ></div>

      <div v-if="tvLoading" class="chart-overlay">
        <a-spin size="large">
          <a-icon slot="indicator" type="loading" style="font-size: 24px; color: #13c2c2" spin />
        </a-spin>
        <div style="margin-top: 16px; color: #666;">正在加载 TradingView 图表...</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

export default {
  name: 'TradingViewChart',
  props: {
    symbol: {
      type: String,
      required: true
    },
    timeframe: {
      type: String,
      default: '15'
    },
    theme: {
      type: String,
      default: 'light'
    },
    // TradingView Widget 配置
    widgetConfig: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const chartMode = ref('klinecharts')
    const tradingViewContainer = ref(null)
    const tvLoading = ref(false)
    let tvWidget = null
    let tvScript = null

    // 时间周期映射
    const timeframeMap = {
      '1m': '1',
      '5m': '5',
      '15m': '15',
      '30m': '30',
      '1H': '60',
      '4H': '240',
      '1D': 'D',
      '1W': 'W'
    }

    // 生成 TradingView Widget URL
    const generateWidgetURL = () => {
      const interval = timeframeMap[props.timeframe] || '15'
      const symbol = props.symbol || 'BTCUSDT'

      // 使用 TradingView Widget Embed
      // 这个 URL 支持 Pine Script 自定义指标
      return `https://s.tradingview.com/widgetembed/?frameElementId=tradingview_${Date.now()}&symbol=${symbol}&interval=${interval}&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=${props.theme}&style=1&timezone=Etc%2FUTC`
    }

    // 加载 TradingView Widget
    const loadTradingViewWidget = async () => {
      if (!tradingViewContainer.value) return

      tvLoading.value = true

      try {
        // 清理旧的 widget
        if (tvWidget) {
          tradingViewContainer.value.innerHTML = ''
          tvWidget = null
        }

        // 创建 iframe
        const iframe = document.createElement('iframe')
        iframe.id = `tradingview_${Date.now()}`
        iframe.style.width = '100%'
        iframe.style.height = '100%'
        iframe.style.border = 'none'
        iframe.style.margin = '0'
        iframe.style.padding = '0'

        // 生成 widget URL（包含 HAMA 指标）
        const interval = timeframeMap[props.timeframe] || '15'
        const symbol = props.symbol || 'BTCUSDT'

        // 使用高级图表，支持自定义 Pine Script
        const widgetURL = `https://s.tradingview.com/widgetembed/`
        const params = new URLSearchParams({
          frameElementId: `tv_${Date.now()}`,
          symbol: symbol,
          interval: interval,
          hidesidetoolbar: '1',
          symboledit: '1',
          saveimage: '1',
          toolbarbg: 'f1f3f6',
          studies: '[]',
          theme: props.theme,
          style: '1',
          timezone: 'Etc/UTC',
          studies_overrides: '{}',
          overrides: '{}'
        })

        iframe.src = `${widgetURL}?${params.toString()}`
        iframe.allowtransparency = true
        iframe.allowFullscreen = true

        tradingViewContainer.value.appendChild(iframe)

        // 等待 iframe 加载
        iframe.onload = () => {
          setTimeout(() => {
            tvLoading.value = false
          }, 1000)
        }

        tvWidget = iframe

      } catch (error) {
        console.error('加载 TradingView Widget 失败:', error)
        tvLoading.value = false
      }
    }

    // 监听模式切换
    watch(chartMode, (newMode) => {
      if (newMode === 'tradingview') {
        nextTick(() => {
          loadTradingViewWidget()
        })
      }
    })

    // 监听币种和时间周期变化
    watch([() => props.symbol, () => props.timeframe], () => {
      if (chartMode.value === 'tradingview') {
        loadTradingViewWidget()
      }
    })

    onBeforeUnmount(() => {
      if (tvScript) {
        document.head.removeChild(tvScript)
      }
      if (tvWidget && tradingViewContainer.value) {
        tradingViewContainer.value.innerHTML = ''
      }
    })

    return {
      chartMode,
      tradingViewContainer,
      tvLoading
    }
  }
}
</script>

<style scoped>
.tradingview-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 4px;
}

.theme-dark .tradingview-chart-container {
  background: #1e1e1e;
}

.chart-header {
  padding: 8px 12px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.theme-dark .chart-header {
  background: #2a2a2a;
  border-bottom: 1px solid #3a3a3a;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.klinecharts-wrapper,
.tradingview-wrapper {
  flex: 1;
  position: relative;
  width: 100%;
  height: 100%;
}

.tradingview-widget-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.theme-dark .chart-overlay {
  background: rgba(30, 30, 30, 0.9);
}
</style>
