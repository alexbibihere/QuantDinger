<template>
  <div class="guagua-signal-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>🐸 呱呱选币</h2>
          <p class="subtitle">高流动性区信号 · 实时推送高流动性币种涨幅</p>
        </div>
        <a-space>
          <a-select v-model="zoneFilter" style="width: 160px" @change="fetchData">
            <a-select-option value="all">全部区域</a-select-option>
            <a-select-option value="high">🔥 高流动性区</a-select-option>
            <a-select-option value="mid">⚡ 中流动性区</a-select-option>
            <a-select-option value="low">💧 低流动性区</a-select-option>
          </a-select>
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            刷新
          </a-button>
          <a-switch v-model="autoRefresh" @change="toggleAutoRefresh" />
          <span>自动刷新</span>
        </a-space>
      </div>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="12" class="stats-row">
      <a-col :xs="12" :sm="6">
        <a-card :bordered="false">
          <a-statistic title="总信号数" :value="stats.total" :value-style="{ color: '#1890ff' }">
            <a-icon slot="prefix" type="alert" />
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card :bordered="false">
          <a-statistic title="🔥 高流动性区" :value="stats.high_count" :value-style="{ color: '#ff4d4f' }">
            <a-icon slot="prefix" type="fire" />
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card :bordered="false">
          <a-statistic title="⚡ 中流动性区" :value="stats.mid_count" :value-style="{ color: '#faad14' }">
            <a-icon slot="prefix" type="thunderbolt" />
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card :bordered="false">
          <a-statistic title="💧 低流动性区" :value="stats.low_count" :value-style="{ color: '#52c41a' }">
            <a-icon slot="prefix" type="swap" />
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 信号表格 -->
    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="signalData"
        :loading="loading"
        :pagination="{ pageSize: 25, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }"
        :row-class-name="rowClassName"
        size="middle"
        :scroll="{ x: 1100 }"
      >
        <!-- 币种（点击跳转TradingView） -->
        <template slot="symbol" slot-scope="text, record">
          <div class="symbol-cell">
            <a :href="getTradingViewUrl(record)" target="_blank" class="symbol-text">{{ text }}</a>
          </div>
        </template>

        <!-- 价格 -->
        <template slot="price" slot-scope="text">
          <span class="price-text">{{ formatPrice(text) }}</span>
        </template>

        <!-- 首次价格 -->
        <template slot="firstPrice" slot-scope="text, record">
          <span class="first-price">{{ formatPrice(record.first_price) }}</span>
        </template>

        <!-- 涨幅 -->
        <template slot="gain" slot-scope="text">
          <span :class="['gain-text', text >= 0 ? 'gain-up' : 'gain-down']">
            <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
            {{ text >= 0 ? '+' : '' }}{{ text.toFixed(2) }}%
          </span>
        </template>

        <!-- 流动性区 -->
        <template slot="zone" slot-scope="text, record">
          <a-tag :color="getZoneColor(record.liquidity_level)">
            {{ text }}
          </a-tag>
        </template>

        <!-- 预警次数 -->
        <template slot="alertCount" slot-scope="text, record">
          <a-badge :count="record.alert_count" :overflow-count="99" :style="{ backgroundColor: getAlertColor(record.alert_count) }" />
        </template>

        <!-- HAMA趋势（参考涨幅榜逻辑，直接使用后端返回的 hama_status） -->
        <template slot="hama" slot-scope="text, record">
          <a-tag
            v-if="record.hama_status"
            :color="getHamaColorTag(record.hama_status)"
            size="small"
          >
            {{ getHamaTrendText(record.hama_status) }}
          </a-tag>
          <span v-else class="hama-na">-</span>
        </template>

        <!-- 24h成交量 -->
        <template slot="vol24h" slot-scope="text">
          <span>{{ formatVolume(text) }}</span>
        </template>

        <!-- 时间 -->
        <template slot="firstTimestamp" slot-scope="text, record">
          <span class="time-text">{{ record.first_timestamp || '-' }}</span>
        </template>
        <template slot="updatedAt" slot-scope="text, record">
          <span class="time-text">{{ record.updated_at || '-' }}</span>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
import { getGuaguaSignals } from '@/utils/guagua-api'

export default {
  name: 'GuaguaSignal',
  data () {
    return {
      loading: false,
      autoRefresh: false,
      autoTimer: null,
      zoneFilter: 'high',
      signalData: [],
      stats: { total: 0, high_count: 0, mid_count: 0, low_count: 0 },
      columns: [
        {
          title: '币种',
          dataIndex: 'symbol',
          key: 'symbol',
          width: 100,
          fixed: 'left',
          scopedSlots: { customRender: 'symbol' }
        },
        {
          title: '当前价格',
          dataIndex: 'price',
          key: 'price',
          width: 120,
          scopedSlots: { customRender: 'price' }
        },
        {
          title: '首次价格',
          dataIndex: 'first_price',
          key: 'firstPrice',
          width: 120,
          scopedSlots: { customRender: 'firstPrice' }
        },
        {
          title: '涨幅',
          dataIndex: 'gain',
          key: 'gain',
          width: 110,
          sorter: (a, b) => a.gain - b.gain,
          defaultSortOrder: 'descend',
          scopedSlots: { customRender: 'gain' }
        },
        {
          title: '流动性区',
          dataIndex: 'zone',
          key: 'zone',
          width: 110,
          scopedSlots: { customRender: 'zone' }
        },
        {
          title: '预警次数',
          dataIndex: 'alert_count',
          key: 'alertCount',
          width: 100,
          scopedSlots: { customRender: 'alertCount' }
        },
        {
          title: 'HAMA趋势',
          key: 'hama',
          width: 100,
          align: 'center',
          scopedSlots: { customRender: 'hama' }
        },
        {
          title: '24h成交量',
          dataIndex: 'vol_24h',
          key: 'vol24h',
          width: 130,
          scopedSlots: { customRender: 'vol24h' }
        },
        {
          title: '首次推送',
          dataIndex: 'first_timestamp',
          key: 'firstTimestamp',
          width: 160,
          scopedSlots: { customRender: 'firstTimestamp' }
        },
        {
          title: '最新时间',
          dataIndex: 'updated_at',
          key: 'updatedAt',
          width: 160,
          scopedSlots: { customRender: 'updatedAt' }
        }
      ]
    }
  },
  mounted () {
    this.fetchData()
  },
  beforeDestroy () {
    this.stopAutoRefresh()
  },
  methods: {
    async fetchData () {
      this.loading = true
      try {
        const res = await getGuaguaSignals({ zone: this.zoneFilter })
        if (res && res.success && res.data) {
          this.signalData = res.data
          this.stats = res.stats || { total: 0, high_count: 0, mid_count: 0, low_count: 0 }
        } else {
          console.warn('呱呱选币数据异常:', res)
        }
      } catch (err) {
        console.error('获取呱呱选币数据失败:', err)
        this.$message.error('获取呱呱选币数据失败: ' + (err.message || ''))
      } finally {
        this.loading = false
      }
    },
    toggleAutoRefresh (val) {
      if (val) {
        this.autoTimer = setInterval(() => this.fetchData(), 60000)
      } else {
        this.stopAutoRefresh()
      }
    },
    stopAutoRefresh () {
      if (this.autoTimer) {
        clearInterval(this.autoTimer)
        this.autoTimer = null
      }
    },
    formatPrice (price) {
      if (price === null || price === undefined) return '-'
      const num = parseFloat(price)
      if (num < 0.0001) return num.toFixed(8)
      if (num < 0.01) return num.toFixed(6)
      if (num < 1) return num.toFixed(4)
      if (num < 100) return num.toFixed(2)
      return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    formatVolume (vol) {
      if (!vol) return '-'
      const num = parseFloat(vol)
      if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B'
      if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M'
      if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K'
      return num.toFixed(2)
    },
    getZoneColor (level) {
      const map = { 3: 'red', 2: 'orange', 1: 'green', 0: 'default' }
      return map[level] || 'default'
    },
    getTradingViewUrl (record) {
      const symbol = (record.binanceSymbol || record.symbol).toUpperCase()
      const fullSymbol = symbol.endsWith('USDT') ? symbol : symbol + 'USDT'
      return `https://cn.tradingview.com/chart/?symbol=BINANCE:${fullSymbol}.P`
    },
    getAlertColor (count) {
      if (count >= 10) return '#ff4d4f'
      if (count >= 5) return '#faad14'
      return '#52c41a'
    },
    // HAMA 相关方法（参考涨幅榜逻辑，直接使用后端 hama_status）
    getHamaColorTag (hamaStatus) {
      if (!hamaStatus) return 'default'
      const map = {
        'green': 'green',
        'red': 'red',
        'gray': 'default'
      }
      return map[hamaStatus.color] || 'default'
    },
    getHamaTrendText (hamaStatus) {
      if (!hamaStatus) return '-'
      const map = {
        'up': '上涨',
        'down': '下跌',
        'neutral': '盘整'
      }
      return map[hamaStatus.trend] || '-'
    },
    rowClassName (record) {
      if (record.liquidity_level === 3) return 'row-high-liquidity'
      if (record.liquidity_level === 2) return 'row-mid-liquidity'
      return ''
    }
  }
}
</script>

<style scoped>
.guagua-signal-container {
  padding: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
}
.subtitle {
  margin: 4px 0 0;
  color: #888;
  font-size: 13px;
}
.stats-row {
  margin-top: 16px;
}
.stats-row .ant-card {
  border-radius: 8px;
}
.table-card {
  margin-top: 16px;
  border-radius: 8px;
}
.symbol-tag {
  font-weight: 600;
  font-size: 13px;
}
.price-text {
  font-family: 'Courier New', monospace;
  font-weight: 500;
}
.first-price {
  font-family: 'Courier New', monospace;
  color: #888;
}
.gain-text {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}
.gain-up {
  color: #52c41a;
}
.gain-down {
  color: #ff4d4f;
}
.time-text {
  font-size: 12px;
  color: #999;
}
.symbol-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.symbol-text {
  font-weight: 600;
  color: #1890ff;
  text-decoration: none;
}
.symbol-text:hover {
  color: #40a9ff;
  text-decoration: underline;
}
.hama-na {
  color: #999;
}
</style>

<style>
/* 全局样式 - 高亮行 */
.row-high-liquidity td {
  background-color: rgba(255, 77, 79, 0.04) !important;
}
.row-mid-liquidity td {
  background-color: rgba(250, 173, 20, 0.03) !important;
}

/* 涨幅列排序高亮 */
.ant-table-column-sorter {
  color: #1890ff;
}
</style>
