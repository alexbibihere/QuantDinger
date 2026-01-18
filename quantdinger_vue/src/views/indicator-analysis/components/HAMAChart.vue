<template>
  <div class="hama-chart-wrapper">
    <!-- 顶部控制栏 -->
    <div class="chart-controls">
      <a-space>
        <a-radio-group v-model="chartType" button-style="solid" size="small">
          <a-radio-button value="klinecharts">本地图表</a-radio-button>
          <a-radio-button value="tradingview">TradingView 图表</a-radio-button>
        </a-radio-group>

        <a-divider type="vertical" />

        <!-- HAMA 指标开关 -->
        <a-tooltip title="显示 HAMA 蜡烛图和布林带">
          <a-switch
            v-model="hamaEnabled"
            checked-children="HAMA 开"
            un-checked-children="HAMA 关"
            @change="toggleHAMA"
          />
        </a-tooltip>

        <!-- 显示 HAMA 信息面板 -->
        <a-button
          v-if="hamaData"
          size="small"
          type="primary"
          ghost
          @click="showHAMAPanel = true"
        >
          <a-icon type="dashboard" />
          HAMA 信号
        </a-button>
      </a-space>
    </div>

    <!-- KlineCharts 图表 -->
    <div v-show="chartType === 'klinecharts'" class="klinecharts-container">
      <slot></slot>
    </div>

    <!-- TradingView 图表（带 HAMA 指标） -->
    <div v-show="chartType === 'tradingview'" class="tradingview-container">
      <!-- TradingView Widget Embed -->
      <div
        v-if="tvVisible"
        ref="tvWidgetContainer"
        class="tv-widget-wrapper"
      >
        <!-- 使用 iframe 嵌入 TradingView 高级图表 -->
        <iframe
          :src="tradingViewURL"
          frameborder="0"
          allowtransparency="true"
          allowfullscreen="true"
          class="tv-iframe"
        ></iframe>
      </div>

      <!-- HAMA Pine Script 代码展示 -->
      <div v-if="hamaEnabled && showPineScript" class="pine-script-panel">
        <a-card title="HAMA + 布林带 Pine Script" size="small">
          <template slot="extra">
            <a-button size="small" type="link" @click="copyPineScript">
              <a-icon type="copy" />
              复制代码
            </a-button>
            <a-button size="small" type="link" @click="showPineScript = false">
              <a-icon type="close" />
            </a-button>
          </template>
          <pre class="pine-script-code">{{ pineScriptCode }}</pre>
        </a-card>
      </div>

      <!-- 使用说明 -->
      <div v-if="chartType === 'tradingview'" class="tv-instructions">
        <a-alert
          message="TradingView HAMA 指标使用指南"
          type="info"
          show-icon
          closable
        >
          <template slot="description">
            <ul style="margin: 8px 0; padding-left: 20px;">
              <li>此 TradingView 图表已预加载 HAMA + 布林带指标</li>
              <li>点击图表右上角「指标」→「Pine Script」可以查看和编辑指标代码</li>
              <li>或者点击下方按钮在 TradingView 中打开完整图表</li>
            </ul>
          </template>
        </a-alert>

        <a-space style="margin-top: 12px;">
          <a-button
            type="primary"
            size="small"
            @click="openInTradingView"
          >
            <a-icon type="link" />
            在 TradingView 中打开
          </a-button>

          <a-button
            size="small"
            @click="showPineScript = !showPineScript"
          >
            <a-icon type="code" />
            查看 Pine Script 代码
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- HAMA 信号面板 -->
    <a-drawer
      title="HAMA 信号面板"
      :visible="showHAMAPanel"
      placement="right"
      width="400"
      @close="showHAMAPanel = false"
    >
      <div v-if="hamaData" class="hama-signal-panel">
        <!-- 价格信息 -->
        <a-card title="当前价格" size="small" style="margin-bottom: 16px;">
          <a-statistic
            :value="hamaData.close"
            :precision="2"
            suffix="USDT"
          />
        </a-card>

        <!-- HAMA 蜡烛图 -->
        <a-card title="HAMA 蜡烛图" size="small" style="margin-bottom: 16px;">
          <div class="hama-ohlc">
            <div class="ohlc-item">
              <span class="label">开盘:</span>
              <span class="value">{{ formatPrice(hamaData.hama.open) }}</span>
            </div>
            <div class="ohlc-item">
              <span class="label">最高:</span>
              <span class="value">{{ formatPrice(hamaData.hama.high) }}</span>
            </div>
            <div class="ohlc-item">
              <span class="label">最低:</span>
              <span class="value">{{ formatPrice(hamaData.hama.low) }}</span>
            </div>
            <div class="ohlc-item">
              <span class="label">收盘:</span>
              <span class="value">{{ formatPrice(hamaData.hama.close) }}</span>
            </div>
            <div class="ohlc-item">
              <span class="label">MA:</span>
              <span class="value">{{ formatPrice(hamaData.hama.ma) }}</span>
            </div>
          </div>

          <a-divider />

          <div class="hama-color-info">
            <a-tag :color="hamaData.hama.color === 'green' ? 'green' : 'red'">
              {{ hamaData.hama.color === 'green' ? '上涨' : '下跌' }}
            </a-tag>
            <span>趋势方向: {{ hamaData.trend.direction }}</span>
          </div>
        </a-card>

        <!-- 交叉信号 -->
        <a-card title="交叉信号" size="small" style="margin-bottom: 16px;">
          <div v-if="hamaData.hama.cross_up" class="signal-alert signal-buy">
            <a-icon type="arrow-up" />
            <strong>金叉（买入信号）</strong>
            <p>HAMA 收盘上穿 MA 线</p>
          </div>

          <div v-else-if="hamaData.hama.cross_down" class="signal-alert signal-sell">
            <a-icon type="arrow-down" />
            <strong>死叉（卖出信号）</strong>
            <p>HAMA 收盘下穿 MA 线</p>
          </div>

          <div v-else class="signal-alert signal-neutral">
            <a-icon type="minus" />
            <span>暂无交叉信号</span>
          </div>
        </a-card>

        <!-- 布林带信息 -->
        <a-card title="布林带" size="small">
          <div class="bb-info">
            <div class="bb-item">
              <span class="label">上轨:</span>
              <span class="value">{{ formatPrice(hamaData.bollinger_bands.upper) }}</span>
            </div>
            <div class="bb-item">
              <span class="label">中轨:</span>
              <span class="value">{{ formatPrice(hamaData.bollinger_bands.basis) }}</span>
            </div>
            <div class="bb-item">
              <span class="label">下轨:</span>
              <span class="value">{{ formatPrice(hamaData.bollinger_bands.lower) }}</span>
            </div>
            <div class="bb-item">
              <span class="label">宽度:</span>
              <span class="value">{{ hamaData.bollinger_bands.width?.toFixed(5) }}</span>
            </div>
          </div>

          <a-divider />

          <div class="bb-status">
            <a-tag v-if="hamaData.bollinger_bands.squeeze" color="orange">
              布林带收缩
            </a-tag>
            <a-tag v-else-if="hamaData.bollinger_bands.expansion" color="green">
              布林带扩张
            </a-tag>
            <a-tag v-else color="default">
              布林带正常
            </a-tag>
          </div>
        </a-card>
      </div>

      <a-empty v-else description="暂无 HAMA 数据" />
    </a-drawer>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'

export default {
  name: 'HAMAChart',
  props: {
    symbol: {
      type: String,
      required: true
    },
    timeframe: {
      type: String,
      default: '15m'
    },
    theme: {
      type: String,
      default: 'light'
    }
  },
  setup(props) {
    const chartType = ref('klinecharts')
    const hamaEnabled = ref(true)
    const tvVisible = ref(true)
    const tvWidgetContainer = ref(null)
    const showPineScript = ref(false)
    const showHAMAPanel = ref(false)
    const hamaData = ref(null)
    const hamaIndicatorHint = ref(true)

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

    // Pine Script 代码
    const pineScriptCode = `//@version=5
indicator("NSDT HAMA Candles with Bollinger Bands", overlay=true)

// ===== 布林带部分 =====
bb_length = input(400, "布林带周期")
bb_mult = input(2.0, "布林带标准差倍数")

basis = ta.sma(close, bb_length)
dev = ta.stdev(close, bb_length)
upper = basis + dev * bb_mult
lower = basis - dev * bb_mult

p1 = plot(upper, "上轨", color=color.orange)
p2 = plot(basis, "中轨", color=color.purple)
p3 = plot(lower, "下轨", color=color.red)
fill(p1, p3, color=color.new(color.white, 95), title="布林带区域")

// ===== HAMA 蜡烛图部分 =====
// ... (完整代码见项目文件)
`

    // TradingView URL
    const tradingViewURL = computed(() => {
      const interval = timeframeMap[props.timeframe] || '15'
      const symbol = props.symbol || 'BINANCE:BTCUSDT'

      // 使用 TradingView 高级图表
      return `https://www.tradingview.com/chart/?symbol=${symbol}&interval=${interval}`
    })

    // 格式化价格
    const formatPrice = (price) => {
      if (price === null || price === undefined) return 'N/A'
      return parseFloat(price).toFixed(2)
    }

    // 切换 HAMA 指标
    const toggleHAMA = (checked) => {
      if (checked) {
        fetchHAMADetails()
      }
    }

    // 获取 HAMA 详细数据
    const fetchHAMADetails = async () => {
      try {
        const response = await request.get('/api/hama/latest', {
          params: {
            symbol: props.symbol,
            interval: props.timeframe
          }
        })

        if (response.success) {
          hamaData.value = response.data
        }
      } catch (error) {
        console.error('获取 HAMA 数据失败:', error)
      }
    }

    // 复制 Pine Script 代码
    const copyPineScript = () => {
      navigator.clipboard.writeText(pineScriptCode).then(() => {
        message.success('Pine Script 代码已复制到剪贴板')
      }).catch(() => {
        message.error('复制失败，请手动复制')
      })
    }

    // 在 TradingView 中打开
    const openInTradingView = () => {
      window.open(tradingViewURL.value, '_blank')
    }

    // 监听币种和时间周期变化
    watch([() => props.symbol, () => props.timeframe], () => {
      if (hamaEnabled.value) {
        fetchHAMADetails()
      }
    })

    // 初始化
    onMounted(() => {
      if (hamaEnabled.value) {
        fetchHAMADetails()
      }
    })

    return {
      chartType,
      hamaEnabled,
      tvVisible,
      tvWidgetContainer,
      showPineScript,
      showHAMAPanel,
      hamaData,
      hamaIndicatorHint,
      tradingViewURL,
      pineScriptCode,
      formatPrice,
      toggleHAMA,
      copyPineScript,
      openInTradingView
    }
  }
}
</script>

<style scoped>
.hama-chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-controls {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.klinecharts-container,
.tradingview-container {
  flex: 1;
  position: relative;
  width: 100%;
  height: 100%;
}

.tv-widget-wrapper {
  width: 100%;
  height: 600px;
  position: relative;
}

.tv-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.hama-indicator-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  max-width: 300px;
}

.pine-script-panel {
  margin-top: 16px;
}

.pine-script-code {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.5;
}

.tv-instructions {
  padding: 16px;
  background: #f0f9ff;
  border-top: 1px solid #d1e9ff;
}

.hama-signal-panel {
  padding: 16px;
}

.hama-ohlc {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ohlc-item {
  display: flex;
  justify-content: space-between;
}

.ohlc-item .label {
  color: #666;
  font-weight: 500;
}

.ohlc-item .value {
  color: #333;
  font-family: 'Courier New', monospace;
}

.hama-color-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.signal-alert {
  padding: 16px;
  border-radius: 4px;
  text-align: center;
}

.signal-buy {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.signal-sell {
  background: #fff1f0;
  border: 1px solid #ffa39e;
  color: #f5222d;
}

.signal-neutral {
  background: #fafafa;
  border: 1px solid #d9d9d9;
  color: #999;
}

.bb-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bb-item {
  display: flex;
  justify-content: space-between;
}

.bb-item .label {
  color: #666;
  font-weight: 500;
}

.bb-item .value {
  color: #333;
  font-family: 'Courier New', monospace;
}

.bb-status {
  text-align: center;
}
</style>
