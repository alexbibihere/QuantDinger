<template>
  <div class="tv-hama-test-page">
    <a-card :bordered="false" class="chart-card">
      <!-- 页面标题 -->
      <template slot="title">
        <div class="page-title">
          <a-icon type="experiment" style="margin-right: 8px; color: #1890ff;" />
          <span>TradingView HAMA 图表测试</span>
          <a-tag color="blue" style="margin-left: 12px;">Beta</a-tag>
        </div>
      </template>

      <!-- 控制面板 -->
      <div class="control-panel">
        <a-space size="large">
          <!-- 币种选择 -->
          <div class="control-group">
            <label class="control-label">币种:</label>
            <a-select
              v-model="selectedSymbol"
              show-search
              style="width: 200px;"
              @change="handleSymbolChange"
            >
              <a-select-option
                v-for="symbol in popularSymbols"
                :key="symbol.value"
                :value="symbol.value"
              >
                <span style="margin-right: 8px;">{{ symbol.label }}</span>
                <a-tag color="green" size="small">{{ symbol.market }}</a-tag>
              </a-select-option>
            </a-select>
          </div>

          <!-- 市场选择 -->
          <div class="control-group">
            <label class="control-label">市场:</label>
            <a-select v-model="selectedMarket" style="width: 150px;" @change="handleMarketChange">
              <a-select-option value="Crypto">加密货币</a-select-option>
              <a-select-option value="USStock">美股</a-select-option>
              <a-select-option value="Forex">外汇</a-select-option>
            </a-select>
          </div>

          <!-- 主题选择 -->
          <div class="control-group">
            <label class="control-label">主题:</label>
            <a-radio-group v-model="selectedTheme" button-style="solid">
              <a-radio-button value="light">亮色</a-radio-button>
              <a-radio-button value="dark">暗色</a-radio-button>
            </a-radio-group>
          </div>

          <!-- 实时更新开关 -->
          <div class="control-group">
            <label class="control-label">实时更新:</label>
            <a-switch
              v-model="realtimeEnabled"
              checked-children="开"
              un-checked-children="关"
            />
          </div>

          <a-divider type="vertical" />

          <!-- 快捷操作 -->
          <a-button type="primary" icon="reload" @click="handleRefresh">刷新数据</a-button>
          <a-button @click="handleResetSettings">重置设置</a-button>
        </a-space>
      </div>

      <!-- 图表容器 -->
      <div class="chart-wrapper">
        <TradingViewHAMAChart
          ref="hamaChart"
          :symbol="selectedSymbol"
          :market="selectedMarket"
          :timeframe="selectedTimeframe"
          :theme="selectedTheme"
          :show-header="true"
          :realtime-enabled="realtimeEnabled"
          @price-change="handlePriceChange"
          @timeframe-change="handleTimeframeChange"
        />
      </div>
    </a-card>
  </div>
</template>

<script>
/* eslint-disable */
import TradingViewHAMAChart from '@/components/TradingViewHAMAChart.vue'

export default {
  name: 'TvHamaTest',
  components: {
    TradingViewHAMAChart
  },
  data () {
    return {
      // 选中的参数
      selectedSymbol: 'BTCUSDT',
      selectedMarket: 'Crypto',
      selectedTimeframe: '15m',
      selectedTheme: 'light',
      realtimeEnabled: true,

      // 热门币种列表
      popularSymbols: [
        { label: 'BTC/USDT', value: 'BTCUSDT', market: 'Binance' },
        { label: 'ETH/USDT', value: 'ETHUSDT', market: 'Binance' },
        { label: 'BNB/USDT', value: 'BNBUSDT', market: 'Binance' },
        { label: 'SOL/USDT', value: 'SOLUSDT', market: 'Binance' },
        { label: 'XRP/USDT', value: 'XRPUSDT', market: 'Binance' },
        { label: 'ADA/USDT', value: 'ADAUSDT', market: 'Binance' },
        { label: 'DOGE/USDT', value: 'DOGEUSDT', market: 'Binance' },
        { label: 'MATIC/USDT', value: 'MATICUSDT', market: 'Binance' },
        { label: 'DOT/USDT', value: 'DOTUSDT', market: 'Binance' },
        { label: 'AVAX/USDT', value: 'AVAXUSDT', market: 'Binance' }
      ]
    }
  },
  methods: {
    // 币种变化
    handleSymbolChange (symbol) {
      console.log('币种切换:', symbol)
      this.priceInfo = null
      this.hamaStats = null
    },

    // 市场变化
    handleMarketChange (market) {
      console.log('市场切换:', market)
    },

    // 价格变化
    handlePriceChange (data) {
      console.log('价格变化:', data)
    },

    // 周期变化
    handleTimeframeChange (timeframe) {
      this.selectedTimeframe = timeframe
      console.log('周期切换:', timeframe)
    },

    // 刷新数据
    handleRefresh () {
      this.$refs.hamaChart && this.$refs.hamaChart.loadKlineData()
      this.$message.success('数据已刷新')
    },

    // 重置设置
    handleResetSettings () {
      this.selectedSymbol = 'BTCUSDT'
      this.selectedMarket = 'Crypto'
      this.selectedTimeframe = '15m'
      this.selectedTheme = 'light'
      this.realtimeEnabled = true
      this.$message.success('设置已重置')
    }
  }
}
</script>

<style lang="less" scoped>
.tv-hama-test-page {
  padding: 0;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);

  .chart-card {
    margin: 0;
    border-radius: 0;

    .page-title {
      display: flex;
      align-items: center;
      font-size: 18px;
      font-weight: 500;
    }
  }
}

.control-panel {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;

  .control-group {
    display: flex;
    align-items: center;

    .control-label {
      margin-right: 8px;
      font-weight: 500;
      color: #333;
      white-space: nowrap;
    }
  }
}

.chart-wrapper {
  height: 700px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  background: #ffffff;
}

// 暗色主题
@media (prefers-color-scheme: dark) {
  .tv-hama-test-page {
    background: #141414;
  }

  .control-panel {
    background: #1f1f1f;
  }

  .chart-wrapper {
    border-color: #303030;
    background: #1f1f1f;
  }
}
</style>
