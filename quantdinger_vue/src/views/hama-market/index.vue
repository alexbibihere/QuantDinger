<template>
  <div class="hama-market-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>{{ $t('hamaMarket.title') }}</h2>
          <p class="subtitle">{{ $t('hamaMarket.subtitle') }}</p>
        </div>
        <a-space>
          <!-- 连接状态 -->
          <a-tag :color="apiStatusColor">
            <a-icon :type="apiConnected ? 'api' : 'disconnect'" />
            {{ apiStatusText }}
          </a-tag>
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            {{ $t('common.refresh') }}
          </a-button>
          <a-button @click="showSymbolModal">
            <a-icon type="plus" />
            {{ $t('hamaMarket.addSymbol') }}
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card>
          <a-statistic
            :title="$t('hamaMarket.totalSymbols')"
            :value="statistics.total"
            prefix="📊"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            :title="$t('hamaMarket.upTrend')"
            :value="statistics.up"
            suffix="/"
            :value-style="{ color: '#3f8600' }"
            prefix="📈"
          >
            <template #suffix>
              <span style="color: rgba(0,0,0,0.45)">{{ statistics.total }}</span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            :title="$t('hamaMarket.downTrend')"
            :value="statistics.down"
            :value-style="{ color: '#cf1322' }"
            prefix="📉"
          >
            <template #suffix>
              <span style="color: rgba(0,0,0,0.45)">/{{ statistics.total }}</span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            :title="$t('hamaMarket.signals')"
            :value="signals.length"
            prefix="🔔"
            :value-style="{ color: signals.length > 0 ? '#faad14' : '' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 信号面板 -->
    <a-card
      v-if="signals.length > 0"
      :bordered="false"
      :title="$t('hamaMarket.currentSignals')"
      style="margin-bottom: 16px"
    >
      <a-table
        :columns="signalColumns"
        :data-source="signals"
        :pagination="false"
        row-key="symbol"
        size="small"
      >
        <template slot="signal_type" slot-scope="text">
          <a-tag v-if="text === 'UP'" color="green">
            <a-icon type="arrow-up" />
            {{ $t('hamaMarket.upSignal') }}
          </a-tag>
          <a-tag v-else color="red">
            <a-icon type="arrow-down" />
            {{ $t('hamaMarket.downSignal') }}
          </a-tag>
        </template>

        <template slot="price" slot-scope="text">
          {{ formatPrice(text) }}
        </template>

        <template slot="hama_info" slot-scope="text, record">
          <div style="font-size: 12px; color: #666">
            HAMA: {{ record.hama_close ? record.hama_close.toFixed(4) : '-' }} /
            MA: {{ record.ma ? record.ma.toFixed(4) : '-' }}
          </div>
        </template>
      </a-table>
    </a-card>

    <!-- 行情列表 -->
    <a-card :bordered="false" :title="$t('hamaMarket.marketList')">
      <a-table
        :columns="columns"
        :data-source="watchlist"
        :loading="loading"
        :pagination="{ pageSize: 20, showSizeChanger: true, showTotal: total => $t('hamaMarket.total', { total }) }"
        row-key="symbol"
        :scroll="{ x: 1200 }"
        size="middle"
      >
        <!-- 币种 -->
        <template slot="symbol" slot-scope="text">
          <a-tag color="blue">{{ text }}</a-tag>
        </template>

        <!-- 价格 -->
        <template slot="price" slot-scope="text">
          <span class="price-value">{{ formatPrice(text) }}</span>
        </template>

        <!-- HAMA 开盘 -->
        <template slot="hama_open" slot-scope="text">
          <span class="hama-value">{{ formatPrice(text) }}</span>
        </template>

        <!-- HAMA 收盘 -->
        <template slot="hama_close" slot-scope="text">
          <span class="hama-value">{{ formatPrice(text) }}</span>
        </template>

        <!-- HAMA MA -->
        <template slot="hama_ma" slot-scope="text">
          <span class="ma-value">{{ formatPrice(text) }}</span>
        </template>

        <!-- 趋势 -->
        <template slot="trend" slot-scope="text, record">
          <a-tag :color="getTrendColor(record.hama)">
            <a-icon :type="getTrendIcon(record.hama)" />
            {{ getTrendText(record.hama) }}
          </a-tag>
        </template>

        <!-- 交叉信号 -->
        <template slot="cross_signal" slot-scope="text, record">
          <template v-if="record.hama.cross_up">
            <a-tag color="green" style="animation: pulse 2s infinite">
              <a-icon type="arrow-up" />
              {{ $t('hamaMarket.goldenCross') }}
            </a-tag>
          </template>
          <template v-else-if="record.hama.cross_down">
            <a-tag color="red" style="animation: pulse 2s infinite">
              <a-icon type="arrow-down" />
              {{ $t('hamaMarket.deathCross') }}
            </a-tag>
          </template>
          <template v-else>
            <span style="color: #999">-</span>
          </template>
        </template>

        <!-- 布林带状态 -->
        <template slot="bb_status" slot-scope="text, record">
          <div class="bb-status">
            <div style="font-size: 12px; color: #666">
              上: {{ formatPrice(record.bollinger_bands.upper) }}
            </div>
            <div style="font-size: 12px; color: #666">
              下: {{ formatPrice(record.bollinger_bands.lower) }}
            </div>
            <div style="font-size: 12px; color: #666">
              宽: {{ (record.bollinger_bands.width * 100).toFixed(2) }}%
            </div>
          </div>
        </template>

        <!-- 操作 -->
        <template slot="action" slot-scope="text, record">
          <a-button
            type="link"
            size="small"
            :href="getTradingViewUrl(record.symbol)"
            target="_blank"
          >
            <a-icon type="line-chart" />
            TradingView
          </a-button>
        </template>
      </a-table>
    </a-card>

    <!-- 添加币种弹窗 -->
    <a-modal
      v-model="symbolModalVisible"
      :title="$t('hamaMarket.addSymbol')"
      @ok="handleAddSymbol"
      :confirm-loading="addLoading"
    >
      <a-form-model :model="symbolForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('hamaMarket.symbol')">
          <a-input
            v-model="symbolForm.symbol"
            :placeholder="$t('hamaMarket.symbolPlaceholder')"
            @keyup.native="symbolForm.symbol = symbolForm.symbol.toUpperCase()"
          />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import { getHamaWatchlist, getHamaSignals } from '@/api/hamaMarket'
import realtimePriceMixin from '@/mixins/realtimePrice'

export default {
  name: 'HamaMarket',
  mixins: [realtimePriceMixin],
  data () {
    return {
      loading: false,
      addLoading: false,
      watchlist: [],
      signals: [],
      apiConnected: false,
      symbolModalVisible: false,
      symbolForm: {
        symbol: ''
      },
      customSymbols: [],
      timer: null
    }
  },
  computed: {
    apiStatusColor () {
      return this.apiConnected ? 'green' : 'red'
    },
    apiStatusText () {
      return this.apiConnected ? this.$t('hamaMarket.connected') : this.$t('hamaMarket.disconnected')
    },
    statistics () {
      const total = this.watchlist.length
      const up = this.watchlist.filter(item => item.trend.direction === 'up').length
      const down = this.watchlist.filter(item => item.trend.direction === 'down').length
      return { total, up, down }
    },
    columns () {
      return [
        {
          title: this.$t('hamaMarket.symbol'),
          dataIndex: 'symbol',
          key: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 120,
          fixed: 'left'
        },
        {
          title: this.$t('hamaMarket.price'),
          dataIndex: 'price',
          key: 'price',
          scopedSlots: { customRender: 'price' },
          width: 120,
          align: 'right'
        },
        {
          title: 'HAMA Open',
          dataIndex: ['hama', 'open'],
          key: 'hama_open',
          scopedSlots: { customRender: 'hama_open' },
          width: 120,
          align: 'right'
        },
        {
          title: 'HAMA Close',
          dataIndex: ['hama', 'close'],
          key: 'hama_close',
          scopedSlots: { customRender: 'hama_close' },
          width: 120,
          align: 'right'
        },
        {
          title: 'HAMA MA',
          dataIndex: ['hama', 'ma'],
          key: 'hama_ma',
          scopedSlots: { customRender: 'hama_ma' },
          width: 120,
          align: 'right'
        },
        {
          title: this.$t('hamaMarket.trend'),
          key: 'trend',
          scopedSlots: { customRender: 'trend' },
          width: 100,
          align: 'center'
        },
        {
          title: this.$t('hamaMarket.crossSignal'),
          key: 'cross_signal',
          scopedSlots: { customRender: 'cross_signal' },
          width: 120,
          align: 'center'
        },
        {
          title: this.$t('hamaMarket.bollingerBands'),
          key: 'bb_status',
          scopedSlots: { customRender: 'bb_status' },
          width: 150
        },
        {
          title: this.$t('common.action'),
          key: 'action',
          scopedSlots: { customRender: 'action' },
          width: 120,
          fixed: 'right',
          align: 'center'
        }
      ]
    },
    signalColumns () {
      return [
        {
          title: this.$t('hamaMarket.symbol'),
          dataIndex: 'symbol',
          key: 'symbol',
          width: 120
        },
        {
          title: this.$t('hamaMarket.signalType'),
          dataIndex: 'signal_type',
          key: 'signal_type',
          scopedSlots: { customRender: 'signal_type' },
          width: 120
        },
        {
          title: this.$t('hamaMarket.price'),
          dataIndex: 'price',
          key: 'price',
          scopedSlots: { customRender: 'price' },
          width: 120,
          align: 'right'
        },
        {
          title: this.$t('hamaMarket.hamaInfo'),
          key: 'hama_info',
          scopedSlots: { customRender: 'hama_info' }
        }
      ]
    }
  },
  mounted () {
    this.fetchData()
    // 每2分钟自动刷新
    this.timer = setInterval(() => {
      this.fetchData()
    }, 120000)
  },
  beforeDestroy () {
    if (this.timer) {
      clearInterval(this.timer)
    }
  },
  methods: {
    async fetchData () {
      this.loading = true
      try {
        // 获取监控列表
        const symbols = this.customSymbols.length > 0 ? this.customSymbols.join(',') : undefined
        const watchlistRes = await getHamaWatchlist({ symbols, market: 'spot' })

        if (watchlistRes.success || watchlistRes.data) {
          this.watchlist = watchlistRes.data.watchlist || []
          this.apiConnected = true
        } else {
          this.watchlist = []
          this.apiConnected = false
        }

        // 获取信号列表
        const signalsRes = await getHamaSignals({ symbols })
        if (signalsRes.success || signalsRes.data) {
          this.signals = signalsRes.data.signals || []
        } else {
          this.signals = []
        }

        // 订阅实时价格
        const allSymbols = this.watchlist.map(item => item.symbol)
        if (this.subscribeRealtimePrices) {
          this.subscribeRealtimePrices(allSymbols)
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        this.$message.error(this.$t('hamaMarket.fetchFailed'))
        this.apiConnected = false
      } finally {
        this.loading = false
      }
    },

    formatPrice (price) {
      if (!price) return '-'
      const numPrice = parseFloat(price)
      if (numPrice < 0.01) return numPrice.toFixed(6)
      if (numPrice < 1) return numPrice.toFixed(4)
      return numPrice.toFixed(2)
    },

    getTrendColor (hama) {
      if (!hama) return 'gray'
      if (hama.color === 'green') return 'green'
      if (hama.color === 'red') return 'red'
      return 'gray'
    },

    getTrendIcon (hama) {
      if (!hama) return 'minus'
      if (hama.color === 'green') return 'arrow-up'
      if (hama.color === 'red') return 'arrow-down'
      return 'minus'
    },

    getTrendText (hama) {
      if (!hama) return '-'
      if (hama.color === 'green') return this.$t('hamaMarket.up')
      if (hama.color === 'red') return this.$t('hamaMarket.down')
      return this.$t('hamaMarket.neutral')
    },

    getTradingViewUrl (symbol) {
      return `https://cn.tradingview.com/chart/?symbol=BINANCE:${symbol}`
    },

    showSymbolModal () {
      this.symbolForm = { symbol: '' }
      this.symbolModalVisible = true
    },

    async handleAddSymbol () {
      if (!this.symbolForm.symbol) {
        this.$message.warning(this.$t('hamaMarket.pleaseEnterSymbol'))
        return
      }

      this.addLoading = true
      try {
        // 添加到自定义列表
        if (!this.customSymbols.includes(this.symbolForm.symbol)) {
          this.customSymbols.push(this.symbolForm.symbol)
          this.$message.success(this.$t('hamaMarket.addSuccess'))
          this.symbolModalVisible = false
          await this.fetchData()
        } else {
          this.$message.warning(this.$t('hamaMarket.symbolExists'))
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMarket.addFailed'))
      } finally {
        this.addLoading = false
      }
    }
  }
}
</script>

<style lang="less" scoped>
.hama-market-container {
  padding: 24px;

  .header-card {
    margin-bottom: 16px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }

    .subtitle {
      margin: 4px 0 0 0;
      color: rgba(0, 0, 0, 0.45);
      font-size: 14px;
    }
  }

  .price-value {
    font-weight: 500;
    font-family: 'Roboto Mono', monospace;
  }

  .hama-value {
    font-family: 'Roboto Mono', monospace;
    color: #1890ff;
  }

  .ma-value {
    font-family: 'Roboto Mono', monospace;
    color: #faad14;
  }

  .bb-status {
    font-family: 'Roboto Mono', monospace;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  }
}
</style>
