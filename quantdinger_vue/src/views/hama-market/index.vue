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
        :scroll="{ x: 1500 }"
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

        <!-- 15分钟周期 -->
        <template slot="timeframe_15m" slot-scope="text, record">
          <a-tag
            v-if="record.hama_brave && record.hama_brave.timeframe_15m"
            :color="getTimeframeColor(record.hama_brave.timeframe_15m.hama_color)"
            style="font-size: 11px"
          >
            <a-icon :type="getTimeframeIcon(record.hama_brave.timeframe_15m.hama_trend)" />
            {{ getTimeframeText(record.hama_brave.timeframe_15m.hama_trend) }}
          </a-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>

        <!-- 1小时周期 -->
        <template slot="timeframe_1h" slot-scope="text, record">
          <a-tag
            v-if="record.hama_brave && record.hama_brave.timeframe_1h"
            :color="getTimeframeColor(record.hama_brave.timeframe_1h.hama_color)"
            style="font-size: 11px"
          >
            <a-icon :type="getTimeframeIcon(record.hama_brave.timeframe_1h.hama_trend)" />
            {{ getTimeframeText(record.hama_brave.timeframe_1h.hama_trend) }}
          </a-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>

        <!-- 4小时周期 -->
        <template slot="timeframe_4h" slot-scope="text, record">
          <a-tag
            v-if="record.hama_brave && record.hama_brave.timeframe_4h"
            :color="getTimeframeColor(record.hama_brave.timeframe_4h.hama_color)"
            style="font-size: 11px"
          >
            <a-icon :type="getTimeframeIcon(record.hama_brave.timeframe_4h.hama_trend)" />
            {{ getTimeframeText(record.hama_brave.timeframe_4h.hama_trend) }}
          </a-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
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

        <!-- HAMA截图 -->
        <template slot="screenshot" slot-scope="text, record">
          <div v-if="record.hama_brave && record.hama_brave.screenshot_base64" class="screenshot-container">
            <img
              :src="`data:image/png;base64,${record.hama_brave.screenshot_base64}`"
              :alt="`${record.symbol} HAMA截图`"
              class="screenshot-thumbnail"
              @click="previewScreenshot(record)"
            />
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

    <!-- 图片预览 -->
    <a-modal
      :visible="previewVisible"
      :title="previewTitle"
      :footer="null"
      @cancel="handlePreviewCancel"
      width="800px"
      centered
    >
      <img :src="previewImage" style="width: 100%" />
    </a-modal>
  </div>
</template>

<script>
import { mapState } from 'vuex'
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
      timer: null,
      previewVisible: false,
      previewImage: '',
      previewTitle: ''
    }
  },
  computed: {
    ...mapState({
      navTheme: state => state.app.theme
    }),
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    },
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
          title: '15分钟',
          key: 'timeframe_15m',
          scopedSlots: { customRender: 'timeframe_15m' },
          width: 120,
          align: 'center'
        },
        {
          title: '1小时',
          key: 'timeframe_1h',
          scopedSlots: { customRender: 'timeframe_1h' },
          width: 120,
          align: 'center'
        },
        {
          title: '4小时',
          key: 'timeframe_4h',
          scopedSlots: { customRender: 'timeframe_4h' },
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
          title: 'HAMA截图',
          key: 'screenshot',
          scopedSlots: { customRender: 'screenshot' },
          width: 120,
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
    },

    previewScreenshot (record) {
      if (record.hama_brave && record.hama_brave.screenshot_base64) {
        this.previewImage = `data:image/png;base64,${record.hama_brave.screenshot_base64}`
        this.previewTitle = `${record.symbol} HAMA截图`
        this.previewVisible = true
      }
    },

    handlePreviewCancel () {
      this.previewVisible = false
    },

    // 多周期数据辅助方法
    getTimeframeColor (hamaColor) {
      if (!hamaColor) return 'default'
      const color = hamaColor.toLowerCase()
      if (color === 'green') return 'green'
      if (color === 'red') return 'red'
      return 'default'
    },

    getTimeframeIcon (hamaTrend) {
      if (!hamaTrend) return 'minus'
      const trend = hamaTrend.toLowerCase()
      if (trend === 'up') return 'arrow-up'
      if (trend === 'down') return 'arrow-down'
      return 'minus'
    },

    getTimeframeText (hamaTrend) {
      if (!hamaTrend) return '-'
      const trend = hamaTrend.toLowerCase()
      if (trend === 'up') return '上涨'
      if (trend === 'down') return '下跌'
      if (trend === 'neutral') return '盘整'
      return '-'
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

  .screenshot-container {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .screenshot-thumbnail {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid #d9d9d9;
    transition: all 0.3s;

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      border-color: #1890ff;
    }
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
