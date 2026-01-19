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
        </a-space>
      </div>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="币种总数"
            :value="watchlist.length"
            prefix="📊"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="上涨趋势"
            :value="watchlist.filter(item => item.hama_brave && item.hama_brave.hama_trend === 'up').length"
            :value-style="{ color: '#3f8600' }"
            prefix="📈"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="下跌趋势"
            :value="watchlist.filter(item => item.hama_brave && item.hama_brave.hama_trend === 'down').length"
            :value-style="{ color: '#cf1322' }"
            prefix="📉"
          />
        </a-card>
      </a-col>
    </a-row>

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
        <template slot="price_value" slot-scope="text, record">
          <span v-if="record.hama_brave && record.hama_brave.hama_value" class="price-value">
            {{ formatPrice(record.hama_brave.hama_value) }}
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- HAMA 状态 -->
        <template slot="hama_status_display" slot-scope="text, record">
          <a-tag
            v-if="record.hama_brave && record.hama_brave.hama_trend"
            :color="record.hama_brave.hama_trend === 'up' ? 'green' : record.hama_brave.hama_trend === 'down' ? 'red' : 'black'"
          >
            <a-icon :type="record.hama_brave.hama_trend === 'up' ? 'arrow-up' : record.hama_brave.hama_trend === 'down' ? 'arrow-down' : 'minus'" />
            {{ record.hama_brave.hama_trend === 'up' ? '上涨' : record.hama_brave.hama_trend === 'down' ? '下跌' : '盘整' }}
          </a-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>

        <!-- 蜡烛/MA -->
        <template slot="candle_ma" slot-scope="text, record">
          <span
            v-if="record.hama_brave && record.hama_brave.candle_ma_status"
            style="font-size: 12px"
          >
            {{ record.hama_brave.candle_ma_status }}
          </span>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>

        <!-- 布林带状态 -->
        <template slot="bollinger_status" slot-scope="text, record">
          <a-tag
            v-if="record.hama_brave && record.hama_brave.bollinger_status"
            :color="record.hama_brave.bollinger_status === 'squeeze' ? 'orange' : 'blue'"
            style="font-size: 11px"
          >
            {{ record.hama_brave.bollinger_status === 'squeeze' ? '收缩' : record.hama_brave.bollinger_status === 'expansion' ? '扩张' : '正常' }}
          </a-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>

        <!-- 最近交叉 -->
        <template slot="last_cross" slot-scope="text, record">
          <div v-if="record.hama_brave && record.hama_brave.last_cross_info" style="font-size: 12px">
            {{ record.hama_brave.last_cross_info }}
          </div>
          <span v-else style="color: #999; font-size: 12px">-</span>
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
  </div>
</template>

<script>
import { getHamaWatchlist } from '@/api/hamaMarket'
import realtimePriceMixin from '@/mixins/realtimePrice'

export default {
  name: 'HamaMarket',
  mixins: [realtimePriceMixin],
  data () {
    return {
      loading: false,
      watchlist: [],
      apiConnected: false,
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
      // 使用 hama_brave.hama_color 判断趋势
      const up = this.watchlist.filter(item => item.hama_brave && item.hama_brave.hama_color === 'green').length
      const down = this.watchlist.filter(item => item.hama_brave && item.hama_brave.hama_color === 'red').length
      return { total, up, down }
    },
    columns () {
      return [
        {
          title: this.$t('hamaMarket.symbol'),
          dataIndex: 'symbol',
          key: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 100,
          fixed: 'left'
        },
        {
          title: '价格',
          key: 'price_value',
          scopedSlots: { customRender: 'price_value' },
          width: 120,
          align: 'right'
        },
        {
          title: 'HAMA状态',
          key: 'hama_status_display',
          scopedSlots: { customRender: 'hama_status_display' },
          width: 120,
          align: 'center'
        },
        {
          title: '蜡烛/MA',
          key: 'candle_ma',
          scopedSlots: { customRender: 'candle_ma' },
          width: 150,
          align: 'center'
        },
        {
          title: '布林带状态',
          key: 'bollinger_status',
          scopedSlots: { customRender: 'bollinger_status' },
          width: 120,
          align: 'center'
        },
        {
          title: '最近交叉',
          key: 'last_cross',
          scopedSlots: { customRender: 'last_cross' },
          width: 180,
          align: 'center'
        },
        {
          title: this.$t('common.action'),
          key: 'action',
          scopedSlots: { customRender: 'action' },
          width: 100,
          fixed: 'right',
          align: 'center'
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
        const watchlistRes = await getHamaWatchlist({ market: 'spot' })

        if (watchlistRes.success || watchlistRes.data) {
          this.watchlist = watchlistRes.data.watchlist || []
          this.apiConnected = true
        } else {
          this.watchlist = []
          this.apiConnected = false
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
