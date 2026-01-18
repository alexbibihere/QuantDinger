/**
 * Lightweight Charts 图表组件
 * 基于 TradingView 开源的高性能图表库
 * 支持自定义指标、完全可定制
 */
<template>
  <div class="lightweight-charts-container">
    <div ref="chartContainer" class="chart-container"></div>

    <!-- 图表工具栏 -->
    <div class="chart-toolbar">
      <a-space>
        <a-button-group>
          <a-button
            v-for="tf in timeframes"
            :key="tf.value"
            :type="currentTimeframe === tf.value ? 'primary' : 'default'"
            size="small"
            @click="changeTimeframe(tf.value)"
          >
            {{ tf.label }}
          </a-button>
        </a-button-group>

        <a-divider type="vertical" />

        <a-checkbox v-model="showHAMA" @change="toggleHAMA">
          <span style="color: #666;">HAMA</span>
        </a-checkbox>
        <a-checkbox v-model="showMA" @change="toggleMA">
          <span style="color: #666;">MA(100)</span>
        </a-checkbox>
        <a-checkbox v-model="showBollinger" @change="toggleBollinger">
          <span style="color: #666;">布林带</span>
        </a-checkbox>

        <a-divider type="vertical" />

        <a-button size="small" @click="fitContent">
          <a-icon type="fullscreen" />
          适配
        </a-button>
      </a-space>
    </div>

    <!-- HAMA 指标信息面板 -->
    <div v-if="hamaData" class="hama-info-panel-lightweight">
      <a-card size="small" :bordered="false" style="background: rgba(255,255,255,0.95);">
        <template slot="title">
          <a-icon type="stock" style="margin-right: 8px;" />
          HAMA 指标
        </template>
        <template slot="extra">
          <a-tag :color="hamaData.hama.color === 'green' ? 'green' : 'red'">
            {{ hamaData.hama.color === 'green' ? '上涨' : '下跌' }}
          </a-tag>
        </template>
        <a-row :gutter="[8, 8]">
          <a-col :span="8">
            <div class="info-item">
              <div class="info-label">价格</div>
              <div class="info-value">{{ formatPrice(hamaData.close) }}</div>
            </div>
          </a-col>
          <a-col :span="8">
            <div class="info-item">
              <div class="info-label">HAMA</div>
              <div class="info-value" :style="{color: hamaData.hama.color === 'green' ? '#52c41a' : '#ef5350'}">
                {{ formatPrice(hamaData.hama.close) }}
              </div>
            </div>
          </a-col>
          <a-col :span="8">
            <div class="info-item">
              <div class="info-label">MA</div>
              <div class="info-value">{{ formatPrice(hamaData.hama.ma) }}</div>
            </div>
          </a-col>
        </a-row>
      </a-card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { createChart } from 'lightweight-charts'
import request from '@/utils/request'

export default {
  name: 'LightweightCharts',
  props: {
    symbol: {
      type: String,
      required: true
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
      type: Number,
      default: 500
    }
  },
  setup (props) {
    const chartContainer = ref(null)
    let chart = null
    let candlestickSeries = null
    let volumeSeries = null

    const showHAMA = ref(true)
    const showMA = ref(true)
    const showBollinger = ref(true)
    const currentTimeframe = ref(props.interval)
    const hamaData = ref(null)

    const timeframes = [
      { label: '1分', value: '1m' },
      { label: '5分', value: '5m' },
      { label: '15分', value: '15m' },
      { label: '30分', value: '30m' },
      { label: '1小时', value: '1H' },
      { label: '4小时', value: '4H' },
      { label: '1天', value: '1D' }
    ]

    // 格式化价格
    const formatPrice = (price) => {
      if (price === null || price === undefined) return '-'
      return parseFloat(price).toFixed(2)
    }

    // 获取图表颜色配置
    const getChartColors = () => {
      const isDark = props.theme === 'dark'
      return {
        background: isDark ? '#131722' : '#ffffff',
        grid: isDark ? '#1f2943' : '#e6e9f0',
        text: isDark ? '#d1d4dc' : '#131722',
        candleUp: '#26a69a',
        candleDown: '#ef5350',
        hamaClose: '#2196F3',
        hamaMA: '#9C27B0',
        bbUpper: '#FF9800',
        bbLower: '#F44336'
      }
    }

    // 初始化图表
    const initChart = () => {
      if (!chartContainer.value) return

      const colors = getChartColors()

      chart = createChart(chartContainer.value, {
        width: chartContainer.value.clientWidth,
        height: props.height,
        layout: {
          background: { color: colors.background },
          textColor: colors.text
        },
        grid: {
          vertLines: { color: colors.grid },
          horzLines: { color: colors.grid }
        },
        timeScale: {
          borderColor: colors.grid,
          timeVisible: true,
          secondsVisible: false
        },
        rightPriceScale: {
          borderColor: colors.grid
        },
        crosshair: {
          mode: 1
        }
      })

      // 添加 K线系列
      candlestickSeries = chart.addCandlestickSeries({
        upColor: colors.candleUp,
        downColor: colors.candleDown,
        borderUpColor: colors.candleUp,
        borderDownColor: colors.candleDown,
        wickUpColor: colors.candleUp,
        wickDownColor: colors.candleDown
      })

      // 添加成交量系列
      volumeSeries = chart.addHistogramSeries({
        priceFormat: {
          type: 'volume'
        },
        priceScaleId: '',
        scaleMargins: {
          top: 0.8,
          bottom: 0
        }
      })

      console.log('✅ Lightweight Charts 已初始化')
    }

    // 加载 K线数据
    const loadData = async () => {
      try {
        const response = await request.get('/api/kline', {
          params: {
            symbol: props.symbol,
            interval: currentTimeframe.value,
            limit: 1000
          }
        })

        if (response && response.data) {
          const klines = response.data

          // 转换为 Lightweight Charts 格式
          const candlestickData = klines.map(k => ({
            time: k.time / 1000,
            open: parseFloat(k.open),
            high: parseFloat(k.high),
            low: parseFloat(k.low),
            close: parseFloat(k.close)
          }))

          const volumeData = klines.map(k => ({
            time: k.time / 1000,
            value: parseFloat(k.volume),
            color: parseFloat(k.close) >= parseFloat(k.open) ? '#26a69a80' : '#ef535080'
          }))

          candlestickSeries.setData(candlestickData)
          volumeSeries.setData(volumeData)

          // 加载 HAMA 指标
          await loadHAMAIndicator(klines)

          console.log(`✅ 已加载 ${candlestickData.length} 条 K线数据`)
        }
      } catch (error) {
        console.error('❌ 加载 K线数据失败:', error)
      }
    }

    // 加载 HAMA 指标
    const loadHAMAIndicator = async (klines) => {
      try {
        const response = await request.get('/api/hama/latest', {
          params: {
            symbol: props.symbol,
            interval: currentTimeframe.value,
            limit: 1000
          }
        })

        if (response.success && response.data) {
          hamaData.value = response.data

          // 这里需要调用后端获取完整的 HAMA 数据序列，而不仅仅是最新值
          // 暂时只显示最新值在面板上
          console.log('✅ HAMA 指标已加载')
        }
      } catch (error) {
        console.error('❌ 加载 HAMA 指标失败:', error)
      }
    }

    // 切换时间周期
    const changeTimeframe = (tf) => {
      currentTimeframe.value = tf
      loadData()
    }

    // 切换 HAMA 显示
    const toggleHAMA = () => {
      // TODO: 实现 HAMA 线的显示/隐藏
      console.log('Toggle HAMA:', showHAMA.value)
    }

    // 切换 MA 显示
    const toggleMA = () => {
      // TODO: 实现 MA 线的显示/隐藏
      console.log('Toggle MA:', showMA.value)
    }

    // 切换布林带显示
    const toggleBollinger = () => {
      // TODO: 实现布林带的显示/隐藏
      console.log('Toggle Bollinger:', showBollinger.value)
    }

    // 适配图表
    const fitContent = () => {
      if (chart) {
        chart.timeScale().fitContent()
      }
    }

    // 响应窗口大小变化
    const handleResize = () => {
      if (chart && chartContainer.value) {
        chart.applyOptions({
          width: chartContainer.value.clientWidth
        })
      }
    }

    // 监听属性变化
    watch(() => props.symbol, () => {
      loadData()
    })

    watch(() => props.interval, () => {
      currentTimeframe.value = props.interval
      loadData()
    })

    watch(() => props.theme, () => {
      if (chart) {
        const colors = getChartColors()
        chart.applyOptions({
          layout: {
            background: { color: colors.background },
            textColor: colors.text
          },
          grid: {
            vertLines: { color: colors.grid },
            horzLines: { color: colors.grid }
          }
        })
      }
    })

    onMounted(() => {
      initChart()
      loadData()
      window.addEventListener('resize', handleResize)
    })

    onBeforeUnmount(() => {
      if (chart) {
        chart.remove()
        chart = null
      }
      window.removeEventListener('resize', handleResize)
    })

    return {
      chartContainer,
      timeframes,
      currentTimeframe,
      showHAMA,
      showMA,
      showBollinger,
      hamaData,
      formatPrice,
      changeTimeframe,
      toggleHAMA,
      toggleMA,
      toggleBollinger,
      fitContent
    }
  }
}
</script>

<style lang="less" scoped>
.lightweight-charts-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;

  .chart-container {
    width: 100%;
    height: 100%;
  }

  .chart-toolbar {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 100;
    background: rgba(255, 255, 255, 0.95);
    padding: 8px 12px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .hama-info-panel-lightweight {
    position: absolute;
    top: 60px;
    left: 10px;
    z-index: 100;
    width: 320px;

    .info-item {
      text-align: center;

      .info-label {
        font-size: 12px;
        color: #999;
        margin-bottom: 4px;
      }

      .info-value {
        font-size: 16px;
        font-weight: 600;
        color: #333;
      }
    }
  }
}

.theme-dark {
  .chart-toolbar {
    background: rgba(19, 23, 34, 0.95);
  }
}
</style>
