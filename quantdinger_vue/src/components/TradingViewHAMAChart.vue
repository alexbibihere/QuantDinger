<template>
  <div class="tv-hama-chart-container" :class="{ 'theme-dark': isDark }">
    <!-- 图表头部工具栏 -->
    <div class="chart-header" v-if="showHeader">
      <div class="header-left">
        <div class="symbol-info">
          <span class="symbol-title">{{ currentSymbol }}</span>
          <span class="symbol-price" :style="{ color: priceColor }">
            {{ currentPrice }}
          </span>
          <span class="symbol-change" :class="priceChangeClass">
            {{ priceChange }}
          </span>
        </div>
      </div>

      <div class="header-right">
        <!-- HAMA 开关 -->
        <a-tooltip title="显示/隐藏 HAMA 指标">
          <a-switch
            v-model="hamaEnabled"
            size="small"
            checked-children="HAMA"
            un-checked-children="HAMA"
            @change="toggleHAMA"
          />
        </a-tooltip>

        <!-- 布林带开关 -->
        <a-tooltip title="显示/隐藏 布林带">
          <a-switch
            v-model="bbEnabled"
            size="small"
            checked-children="BB"
            un-checked-children="BB"
            @change="toggleBollingerBands"
          />
        </a-tooltip>

        <!-- MA 线开关 -->
        <a-tooltip title="显示/隐藏 MA 线">
          <a-switch
            v-model="maEnabled"
            size="small"
            checked-children="MA"
            un-checked-children="MA"
            @change="toggleMA"
          />
        </a-tooltip>

        <a-divider type="vertical" />

        <!-- 周期选择 -->
        <a-radio-group v-model="selectedTimeframe" size="small" button-style="solid">
          <a-radio-button value="1m">1m</a-radio-button>
          <a-radio-button value="5m">5m</a-radio-button>
          <a-radio-button value="15m">15m</a-radio-button>
          <a-radio-button value="1H">1H</a-radio-button>
          <a-radio-button value="4H">4H</a-radio-button>
          <a-radio-button value="1D">1D</a-radio-button>
        </a-radio-group>

        <a-divider type="vertical" />

        <!-- 全屏按钮 -->
        <a-tooltip title="全屏">
          <a-button size="small" icon="fullscreen" @click="toggleFullscreen" />
        </a-tooltip>
      </div>
    </div>

    <!-- HAMA 信息面板 -->
    <div class="hama-info-panel" v-if="hamaEnabled && hamaData">
      <div class="info-item">
        <span class="info-label">HAMA</span>
        <span class="info-value" :style="{ color: getHAMATrendColor() }">
          {{ getHAMALatestValue() }}
        </span>
      </div>
      <div class="info-item" v-if="maEnabled">
        <span class="info-label">MA({{ hamaParams.maLength }})</span>
        <span class="info-value">{{ getMALatestValue() }}</span>
      </div>
      <div class="info-item" v-if="bbEnabled">
        <span class="info-label">BB 上轨</span>
        <span class="info-value">{{ getBBUpperValue() }}</span>
      </div>
      <div class="info-item" v-if="bbEnabled">
        <span class="info-label">BB 下轨</span>
        <span class="info-value">{{ getBBLowerValue() }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">信号</span>
        <span class="info-value signal" :class="getSignalClass()">
          {{ getSignalText() }}
        </span>
      </div>
    </div>

    <!-- 图表容器 -->
    <div
      ref="chartContainer"
      class="tv-chart-wrapper"
      :class="{ 'with-header': showHeader }"
    >
      <!-- HAMA 指标详情浮层 (叠加在图表上) -->
      <div
        class="hama-overlay-info"
        v-if="hamaEnabled && hamaData && !loading"
        style="position: absolute !important; bottom: 16px !important; right: 16px !important; top: auto !important; left: auto !important;"
      >
        <div class="overlay-section">
          <div class="overlay-title">HAMA 指标</div>
          <div class="overlay-content">
            <div class="overlay-row">
              <span class="overlay-label">HAMA:</span>
              <span class="overlay-value" :style="{ color: getHAMATrendColor() }">
                {{ getHAMALatestValue() }}
              </span>
            </div>
            <div class="overlay-row" v-if="maEnabled">
              <span class="overlay-label">MA({{ hamaParams.maLength }}):</span>
              <span class="overlay-value">{{ getMALatestValue() }}</span>
            </div>
            <div class="overlay-row">
              <span class="overlay-label">信号:</span>
              <span class="overlay-value signal-badge" :class="getSignalClass()">
                {{ getSignalText() }}
              </span>
            </div>
          </div>
        </div>

        <div class="overlay-section" v-if="bbEnabled">
          <div class="overlay-title">布林带</div>
          <div class="overlay-content">
            <div class="overlay-row">
              <span class="overlay-label">上轨:</span>
              <span class="overlay-value bb-upper">{{ getBBUpperValue() }}</span>
            </div>
            <div class="overlay-row">
              <span class="overlay-label">下轨:</span>
              <span class="overlay-value bb-lower">{{ getBBLowerValue() }}</span>
            </div>
            <div class="overlay-row" v-if="getBBWidth()">
              <span class="overlay-label">带宽:</span>
              <span class="overlay-value">{{ getBBWidth() }}</span>
            </div>
          </div>
        </div>

        <div class="overlay-section" v-if="getPricePosition()">
          <div class="overlay-title">价格位置</div>
          <div class="overlay-content">
            <div class="overlay-row">
              <span class="overlay-label">位置:</span>
              <span class="overlay-value">{{ getPricePosition() }}</span>
            </div>
            <div class="overlay-progress">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: getPricePositionPercent(), backgroundColor: getPositionColor() }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div class="overlay-section" v-if="getLastCrossSignal()">
          <div class="overlay-title">最近信号</div>
          <div class="overlay-content">
            <div class="overlay-row">
              <span class="overlay-value signal-badge" :class="getLastCrossClass()">
                {{ getLastCrossSignal().signal }}
              </span>
              <span class="overlay-time">{{ formatCrossTime(getLastCrossSignal().timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="chart-loading">
      <a-spin size="large">
        <a-icon slot="indicator" type="loading" style="font-size: 24px; color: #13c2c2" spin />
      </a-spin>
      <div class="loading-text">加载中...</div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="chart-error">
      <a-icon type="warning" style="font-size: 32px; color: #ef5350" />
      <div class="error-text">{{ error }}</div>
      <a-button type="primary" size="small" @click="handleRetry" style="margin-top: 12px">
        重试
      </a-button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { init, dispose } from 'klinecharts'
import { HAMAIndicator, registerHAMAIndicator, updateHAMAIndicator } from '@/utils/indicators/klinechartsHAMA'
import { calculateHAMAEnhanced } from '@/utils/indicators/hamaIndicatorEnhanced'
import request from '@/utils/request'

export default {
  name: 'TradingViewHAMAChart',
  props: {
    symbol: {
      type: String,
      required: true
    },
    market: {
      type: String,
      default: 'Crypto'
    },
    timeframe: {
      type: String,
      default: '15m'
    },
    theme: {
      type: String,
      default: 'light'
    },
    showHeader: {
      type: Boolean,
      default: true
    },
    realtimeEnabled: {
      type: Boolean,
      default: true
    }
  },
  emits: ['price-change', 'symbol-change', 'timeframe-change'],
  setup (props, { emit }) {
    const chartContainer = ref(null)
    const chart = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // 指标状态
    const hamaEnabled = ref(true)
    const bbEnabled = ref(true)
    const maEnabled = ref(true)

    // 数据状态
    const klineData = ref([])
    const hamaData = ref(null)
    const currentPrice = ref('-')
    const priceChange = ref('-')

    // UI 状态
    const selectedTimeframe = ref(props.timeframe)
    const isDark = computed(() => props.theme === 'dark')

    // HAMA 参数
    const hamaParams = ref({
      openLength: 45,
      openType: 'EMA',
      highLength: 20,
      highType: 'EMA',
      lowLength: 20,
      lowType: 'EMA',
      closeLength: 40,
      closeType: 'WMA',
      maLength: 100,
      maType: 'WMA',
      bbLength: 400,
      bbMult: 2.0
    })

    const currentSymbol = computed(() => {
      return props.symbol || 'BTCUSDT'
    })

    const priceColor = computed(() => {
      if (priceChange.value === '-') return '#999'
      return priceChange.value.startsWith('+') ? '#26a69a' : '#ef5350'
    })

    const priceChangeClass = computed(() => {
      if (priceChange.value === '-') return ''
      return priceChange.value.startsWith('+') ? 'up' : 'down'
    })

    // 初始化图表
    const initChart = () => {
      if (!chartContainer.value) return

      try {
        // 销毁旧图表
        if (chart.value) {
          dispose(chartContainer.value)
        }

        // 创建新图表
        chart.value = init(chartContainer.value, {
          grid: {
            visible: true,
            show: true
          },
          candle: {
            type: 'candle',
            bar: {
              upColor: '#26a69a',
              downColor: '#ef5350',
              noChangeColor: '#888888'
            },
            tooltip: {
              showRule: 'always',
              showType: 'standard',
              labels: ['时间: ', '开: ', '高: ', '低: ', '收: ', '成交量: '],
              text: {
                size: 12,
                color: '#D9D9D9'
              }
            }
          },
          indicator: {
            tooltips: []
          }
        })

        // 设置主题
        chart.value.setStyles({
          grid: {
            show: true
          },
          crosshair: {
            show: true,
            mode: 1,
            horizontal: {
              show: true,
              line: {
                show: true,
                style: 'dashed'
              }
            },
            vertical: {
              show: true,
              line: {
                show: true,
                style: 'dashed'
              }
            }
          }
        })

        // 注册 HAMA 指标
        if (hamaEnabled.value) {
          registerHAMAIndicator(chart.value)
        }

        // 加载初始数据
        loadKlineData()

        // 开始实时更新
        if (props.realtimeEnabled) {
          startRealtimeUpdate()
        }
      } catch (err) {
        console.error('初始化图表失败:', err)
        error.value = '初始化图表失败: ' + err.message
      }
    }

    // 加载 K线数据
    const loadKlineData = async () => {
      if (!props.symbol) return

      loading.value = true
      error.value = null

      try {
        const response = await request({
          url: '/api/indicator/kline',
          method: 'post',
          data: {
            market: props.market,
            symbol: props.symbol,
            timeframe: selectedTimeframe.value,
            limit: 500
          }
        })

        if (response.code === 1 && response.data && Array.isArray(response.data)) {
          // 转换数据格式
          klineData.value = response.data.map(item => ({
            timestamp: item.time * 1000,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
            volume: item.volume
          }))

          // 更新图表
          chart.value.applyNewData(klineData.value)

          // 计算并更新 HAMA 指标
          if (hamaEnabled.value) {
            updateHAMAIndicator(chart.value, klineData.value, hamaParams.value)

            // 使用增强版计算,包含完整的统计信息
            const enhancedResult = calculateHAMAEnhanced(response.data, hamaParams.value)

            // 转换数据格式用于图表显示
            hamaData.value = HAMAIndicator.calc(klineData.value, hamaParams.value)

            // 合并增强版分析数据
            if (enhancedResult && enhancedResult.hamaAnalysis) {
              hamaData.value = {
                ...hamaData.value,
                bbWidth: enhancedResult.bbAnalysis?.width || [],
                pricePosition: enhancedResult.bbAnalysis?.pricePosition || [],
                crossSignals: enhancedResult.hamaAnalysis?.crossSignals || [],
                hamaStatus: enhancedResult.hamaAnalysis?.status || [],
                candleMARelation: enhancedResult.hamaAnalysis?.candleMARelation || []
              }
            }
          }

          // 更新价格信息
          updatePriceInfo(response.data)
        } else {
          throw new Error(response.msg || '获取数据失败')
        }
      } catch (err) {
        console.error('加载K线数据失败:', err)
        error.value = err.message || '加载失败'
      } finally {
        loading.value = false
      }
    }

    // 更新价格信息
    const updatePriceInfo = (data) => {
      if (!data || data.length === 0) return

      const last = data[data.length - 1]
      const prev = data[data.length - 2]

      currentPrice.value = last.close.toFixed(2)

      if (prev) {
        const change = ((last.close - prev.close) / prev.close) * 100
        priceChange.value = (change >= 0 ? '+' : '') + change.toFixed(2) + '%'

        // 计算增强版 HAMA 统计信息
        const hamaEnhanced = calculateHAMAEnhanced(data, hamaParams.value)

        emit('price-change', {
          price: last.close,
          change: change,
          symbol: props.symbol,
          stats: hamaEnhanced.stats || null
        })
      }
    }

    // 实时更新
    let realtimeTimer = null
    const startRealtimeUpdate = () => {
      stopRealtimeUpdate()

      const intervalMap = {
        '1m': 10000,
        '5m': 30000,
        '15m': 60000,
        '1H': 300000,
        '4H': 600000,
        '1D': 900000
      }

      const interval = intervalMap[selectedTimeframe.value] || 60000

      realtimeTimer = setInterval(() => {
        loadKlineData()
      }, interval)
    }

    const stopRealtimeUpdate = () => {
      if (realtimeTimer) {
        clearInterval(realtimeTimer)
        realtimeTimer = null
      }
    }

    // 切换 HAMA 指标
    const toggleHAMA = (enabled) => {
      if (enabled) {
        registerHAMAIndicator(chart.value)
        if (klineData.value.length > 0) {
          updateHAMAIndicator(chart.value, klineData.value, hamaParams.value)

          // 使用增强版计算
          const enhancedResult = calculateHAMAEnhanced(
            klineData.value.map(k => ({
              time: k.timestamp / 1000,
              open: k.open,
              high: k.high,
              low: k.low,
              close: k.close,
              volume: k.volume
            })),
            hamaParams.value
          )

          hamaData.value = HAMAIndicator.calc(klineData.value, hamaParams.value)

          // 合并增强版数据
          if (enhancedResult && enhancedResult.hamaAnalysis) {
            hamaData.value = {
              ...hamaData.value,
              bbWidth: enhancedResult.bbAnalysis?.width || [],
              pricePosition: enhancedResult.bbAnalysis?.pricePosition || [],
              crossSignals: enhancedResult.hamaAnalysis?.crossSignals || [],
              hamaStatus: enhancedResult.hamaAnalysis?.status || [],
              candleMARelation: enhancedResult.hamaAnalysis?.candleMARelation || []
            }
          }
        }
      } else {
        chart.value.removeIndicator('HAMA')
        hamaData.value = null
      }
    }

    // 切换布林带
    const toggleBollingerBands = (enabled) => {
      // klinecharts 会自动处理
    }

    // 切换 MA 线
    const toggleMA = (enabled) => {
      // klinecharts 会自动处理
    }

    // 获取 HAMA 最新值
    const getHAMALatestValue = () => {
      if (!hamaData.value || !hamaData.value.candle || hamaData.value.candle.length === 0) return '-'
      const last = hamaData.value.candle[hamaData.value.candle.length - 1]
      return last.close ? last.close.toFixed(2) : '-'
    }

    // 获取 MA 最新值
    const getMALatestValue = () => {
      if (!hamaData.value || !hamaData.value.ma || hamaData.value.ma.length === 0) return '-'
      const last = hamaData.value.ma[hamaData.value.ma.length - 1]
      return last.value ? last.value.toFixed(2) : '-'
    }

    // 获取布林带上轨
    const getBBUpperValue = () => {
      if (!hamaData.value || !hamaData.value.bbUpper || hamaData.value.bbUpper.length === 0) return '-'
      const last = hamaData.value.bbUpper[hamaData.value.bbUpper.length - 1]
      return last.value ? last.value.toFixed(2) : '-'
    }

    // 获取布林带下轨
    const getBBLowerValue = () => {
      if (!hamaData.value || !hamaData.value.bbLower || hamaData.value.bbLower.length === 0) return '-'
      const last = hamaData.value.bbLower[hamaData.value.bbLower.length - 1]
      return last.value ? last.value.toFixed(2) : '-'
    }

    // 获取布林带宽度
    const getBBWidth = () => {
      if (!hamaData.value || !hamaData.value.bbWidth || hamaData.value.bbWidth.length === 0) return null
      const last = hamaData.value.bbWidth[hamaData.value.bbWidth.length - 1]
      return last !== null ? (last * 100).toFixed(3) + '%' : null
    }

    // 获取价格位置
    const getPricePosition = () => {
      if (!hamaData.value || !hamaData.value.pricePosition || hamaData.value.pricePosition.length === 0) return null
      const last = hamaData.value.pricePosition[hamaData.value.pricePosition.length - 1]
      return last !== null ? (last * 100).toFixed(1) + '%' : null
    }

    // 获取价格位置百分比 (用于进度条)
    const getPricePositionPercent = () => {
      if (!hamaData.value || !hamaData.value.pricePosition || hamaData.value.pricePosition.length === 0) return '0%'
      const last = hamaData.value.pricePosition[hamaData.value.pricePosition.length - 1]
      return last !== null ? (last * 100).toFixed(1) + '%' : '0%'
    }

    // 获取位置颜色
    const getPositionColor = () => {
      if (!hamaData.value || !hamaData.value.pricePosition || hamaData.value.pricePosition.length === 0) return '#999'
      const last = hamaData.value.pricePosition[hamaData.value.pricePosition.length - 1]
      if (last === null) return '#999'
      if (last > 0.8) return '#ef5350' // 接近上轨 - 超买
      if (last < 0.2) return '#26a69a' // 接近下轨 - 超卖
      return '#ffd700' // 中性
    }

    // 获取最近交叉信号
    const getLastCrossSignal = () => {
      if (!hamaData.value || !hamaData.value.crossSignals || hamaData.value.crossSignals.length === 0) return null
      return hamaData.value.crossSignals[hamaData.value.crossSignals.length - 1]
    }

    // 获取交叉信号样式
    const getLastCrossClass = () => {
      const signal = getLastCrossSignal()
      if (!signal) return ''
      return signal.type === 'up' ? 'signal-buy' : 'signal-sell'
    }

    // 格式化交叉时间
    const formatCrossTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${hours}:${minutes}`
    }

    // 获取 HAMA 趋势颜色
    const getHAMATrendColor = () => {
      if (!hamaData.value || !hamaData.value.candle || hamaData.value.candle.length === 0) return '#999'
      const last = hamaData.value.candle[hamaData.value.candle.length - 1]
      return last.color || '#999'
    }

    // 获取信号
    const getSignalText = () => {
      if (!hamaData.value) return '无数据'

      const hamaClose = getHAMALatestValue()
      const maValue = getMALatestValue()

      if (hamaClose === '-' || maValue === '-') return '等待数据'

      const hc = parseFloat(hamaClose)
      const mv = parseFloat(maValue)

      if (hc > mv) return '买入'
      if (hc < mv) return '卖出'
      return '观望'
    }

    const getSignalClass = () => {
      const signal = getSignalText()
      if (signal === '买入') return 'signal-buy'
      if (signal === '卖出') return 'signal-sell'
      return 'signal-neutral'
    }

    // 重试
    const handleRetry = () => {
      loadKlineData()
    }

    // 全屏切换
    const toggleFullscreen = () => {
      const elem = chartContainer.value
      if (!document.fullscreenElement) {
        elem.requestFullscreen().catch(err => {
          console.error('全屏失败:', err)
        })
      } else {
        document.exitFullscreen()
      }
    }

    // 监听属性变化
    watch(() => props.symbol, () => {
      loadKlineData()
    })

    watch(selectedTimeframe, () => {
      emit('timeframe-change', selectedTimeframe.value)
      loadKlineData()
      startRealtimeUpdate()
    })

    watch(() => props.theme, () => {
      if (chart.value) {
        chart.value.setStyles({
          layout: {
            background: {
              type: 'solid',
              color: isDark.value ? '#131722' : '#ffffff'
            },
            textColor: isDark.value ? '#d1d4dc' : '#333333'
          }
        })
      }
    })

    // 生命周期
    onMounted(() => {
      nextTick(() => {
        initChart()
      })
    })

    onBeforeUnmount(() => {
      stopRealtimeUpdate()
      if (chart.value && chartContainer.value) {
        dispose(chartContainer.value)
      }
    })

    return {
      chartContainer,
      loading,
      error,
      hamaEnabled,
      bbEnabled,
      maEnabled,
      hamaData,
      hamaParams,
      currentSymbol,
      currentPrice,
      priceChange,
      priceColor,
      priceChangeClass,
      selectedTimeframe,
      isDark,
      toggleHAMA,
      toggleBollingerBands,
      toggleMA,
      getHAMALatestValue,
      getMALatestValue,
      getBBUpperValue,
      getBBLowerValue,
      getBBWidth,
      getPricePosition,
      getPricePositionPercent,
      getPositionColor,
      getLastCrossSignal,
      getLastCrossClass,
      formatCrossTime,
      getHAMATrendColor,
      getSignalText,
      getSignalClass,
      handleRetry,
      toggleFullscreen
    }
  }
}
</script>

<style lang="less">
.tv-hama-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  position: relative;

  &.theme-dark {
    background: #131722;
  }
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;

  .theme-dark & {
    background: #1e222d;
    border-bottom-color: #2a2e39;
  }

  .header-left {
    display: flex;
    align-items: center;
  }

  .symbol-info {
    display: flex;
    align-items: center;
    gap: 12px;

    .symbol-title {
      font-size: 16px;
      font-weight: bold;
      color: #333;

      .theme-dark & {
        color: #d1d4dc;
      }
    }

    .symbol-price {
      font-size: 18px;
      font-weight: bold;
      font-family: 'Courier New', monospace;
    }

    .symbol-change {
      font-size: 14px;
      font-weight: 500;
      padding: 2px 8px;
      border-radius: 3px;

      &.up {
        color: #26a69a;
        background: rgba(38, 166, 154, 0.1);
      }

      &.down {
        color: #ef5350;
        background: rgba(239, 83, 80, 0.1);
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.hama-info-panel {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e8e8e8;
  flex-wrap: wrap;

  .theme-dark & {
    background: rgba(19, 23, 34, 0.95);
    border-bottom-color: #2a2e39;
  }

  .info-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;

    .info-label {
      color: #999;
      font-weight: 500;
    }

    .info-value {
      color: #333;
      font-family: 'Courier New', monospace;
      font-weight: bold;

      .theme-dark & {
        color: #d1d4dc;
      }

      &.signal {
        padding: 2px 8px;
        border-radius: 3px;

        &.signal-buy {
          color: #26a69a;
          background: rgba(38, 166, 154, 0.1);
        }

        &.signal-sell {
          color: #ef5350;
          background: rgba(239, 83, 80, 0.1);
        }

        &.signal-neutral {
          color: #999;
          background: rgba(153, 153, 153, 0.1);
        }
      }
    }
  }
}

.tv-chart-wrapper {
  flex: 1;
  width: 100%;
  min-height: 500px;
  position: relative;

  &.with-header {
    min-height: 400px;
  }
}

// HAMA 指标浮层样式
.hama-overlay-info {
  position: absolute !important;
  bottom: 16px !important;
  right: 16px !important;
  top: auto !important;
  left: auto !important;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
  max-width: 280px;
  pointer-events: none; // 让鼠标事件穿透到图表

  .overlay-section {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    pointer-events: auto;

    .theme-dark & {
      background: rgba(19, 23, 34, 0.92);
      border-color: rgba(255, 255, 255, 0.1);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    .overlay-title {
      font-size: 12px;
      font-weight: 600;
      color: #666;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
      padding-bottom: 4px;

      .theme-dark & {
        color: #999;
        border-bottom-color: rgba(255, 255, 255, 0.1);
      }
    }

    .overlay-content {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .overlay-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;

      .overlay-label {
        color: #999;
        font-weight: 500;
      }

      .overlay-value {
        color: #333;
        font-family: 'Courier New', monospace;
        font-weight: bold;

        .theme-dark & {
          color: #d1d4dc;
        }

        &.bb-upper {
          color: #ffa500;
        }

        &.bb-lower {
          color: #ef5350;
        }

        &.signal-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;

          &.signal-buy {
            color: #26a69a;
            background: rgba(38, 166, 154, 0.15);
          }

          &.signal-sell {
            color: #ef5350;
            background: rgba(239, 83, 80, 0.15);
          }

          &.signal-neutral {
            color: #999;
            background: rgba(153, 153, 153, 0.15);
          }
        }
      }

      .overlay-time {
        font-size: 11px;
        color: #999;
        margin-left: 8px;
      }
    }

    .overlay-progress {
      margin-top: 4px;

      .progress-bar {
        width: 100%;
        height: 6px;
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
        overflow: hidden;

        .theme-dark & {
          background: rgba(255, 255, 255, 0.1);
        }

        .progress-fill {
          height: 100%;
          transition: width 0.3s ease, background-color 0.3s ease;
          border-radius: 3px;
        }
      }
    }
  }
}

.chart-loading,
.chart-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  z-index: 100;

  .theme-dark & {
    background: rgba(19, 23, 34, 0.95);
  }

  .loading-text,
  .error-text {
    margin-top: 16px;
    color: #666;

    .theme-dark & {
      color: #9c27b0;
    }
  }
}
</style>
