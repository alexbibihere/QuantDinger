<template>
  <div class="futures-gainers-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>Binance 涨幅榜</h2>
          <p class="subtitle">{{ dataSourceText }} - 币安永续合约涨幅榜</p>
        </div>
        <a-space>
          <a-select
            v-model="dataSource"
            style="width: 140px"
            @change="onDataSourceChange"
          >
            <a-select-option value="cryptobubbles">CryptoBubbles</a-select-option>
            <a-select-option value="aijiaoyi">爱交易</a-select-option>
            <a-select-option value="coingecko">CoinGecko</a-select-option>
          </a-select>
          <a-select
            v-if="dataSource === 'cryptobubbles'"
            v-model="timeframe"
            style="width: 120px"
            @change="fetchData"
          >
            <a-select-option value="1h">1h</a-select-option>
            <a-select-option value="4h">4h</a-select-option>
            <a-select-option value="24h">24h</a-select-option>
            <a-select-option value="7d">7d</a-select-option>
            <a-select-option value="30d">30d</a-select-option>
          </a-select>
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            刷新
          </a-button>
          <a-switch
            v-model="autoRefresh"
            @change="toggleAutoRefresh"
          />
          <span>自动刷新</span>
        </a-space>
      </div>
    </a-card>

    <!-- 统计信息 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="总币种"
            :value="gainersData.length"
            prefix="📊"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="涨幅币种"
            :value="gainersCount"
            prefix="📈"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="HAMA上涨"
            :value="hamaUpCount"
            prefix="🟢"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="更新时间"
            :value="updateTime"
            prefix="🕐"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 涨幅榜 -->
    <a-card
      :bordered="false"
      :title="`涨幅榜 TOP ${dataSource === 'aijiaoyi' ? '20' : dataSource === 'coingecko' ? '30' : '10'} - ${dataSourceText}`"
      class="gainers-card"
    >
      <a-table
        :columns="gainersColumns"
        :data-source="gainersData"
        :loading="loading"
        :pagination="false"
        size="middle"
        :row-key="(record) => record.symbol"
        :scroll="{ x: 1400 }"
      >
        <template #rank="text, record, index">
          <a-tag :color="getRankColor(index)">{{ index + 1 }}</a-tag>
        </template>
        <template #symbol="text, record">
          <div class="symbol-cell">
            <img v-if="record.image" :src="record.image" class="coin-icon" />
            <a :href="getTradingViewUrl(record)" target="_blank" class="symbol-text">{{ text }}</a>
          </div>
        </template>
        <template #price="text">
          <span class="price-text">${{ formatPrice(text) }}</span>
        </template>
        <template #change_pct="text">
          <span v-if="text !== null && text !== undefined" :class="getTextClass(text)">
            <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
            {{ text.toFixed(2) }}%
          </span>
          <span v-else>-</span>
        </template>
        <template #volume="text">
          {{ formatVolume(text) }}
        </template>
        <template #marketcap="text">
          ${{ formatVolume(text) }}
        </template>
        <template #hama_trend="text, record">
          <a-tag v-if="getHamaData(record.binanceSymbol)" :color="getHamaColorTag(getHamaData(record.binanceSymbol).hama_color)" size="small">
            {{ getHamaTrendText(getHamaData(record.binanceSymbol).hama_trend) }}
          </a-tag>
          <a-spin v-else-if="hamaLoading" size="small" />
          <span v-else>-</span>
        </template>
        <template #candle_ma="text, record">
          <span v-if="getHamaData(record.binanceSymbol)" :class="getCandleMAClass(getHamaData(record.binanceSymbol).candle_ma_status)">
            {{ getCandleMAText(getHamaData(record.binanceSymbol).candle_ma_status) }}
          </span>
          <span v-else>-</span>
        </template>
        <template #bb_status="text, record">
          <a-tag v-if="getHamaData(record.binanceSymbol)" :color="getBollingerColor(getHamaData(record.binanceSymbol).bb_status)" size="small">
            {{ getBollingerText(getHamaData(record.binanceSymbol).bb_status) }}
          </a-tag>
          <span v-else>-</span>
        </template>
        <template #last_cross="text, record">
          <span v-if="getHamaData(record.binanceSymbol) && getHamaData(record.binanceSymbol).last_cross_time" class="cross-time">
            {{ formatCrossTime(getHamaData(record.binanceSymbol).last_cross_time) }}
          </span>
          <span v-else>-</span>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
/* eslint-disable */
import request from '@/utils/request'

export default {
  name: 'FuturesGainers',
  data() {
    return {
      dataSource: 'cryptobubbles',
      gainersData: [],
      allData: [],
      hamaData: {},
      loading: false,
      hamaLoading: false,
      autoRefresh: false,
      refreshInterval: null,
      updateTime: '-',
      timeframe: '24h'
    }
  },
  computed: {
    dataSourceText() {
      const map = {
        'cryptobubbles': 'Crypto Bubbles 数据源',
        'aijiaoyi': '爱交易数据源',
        'coingecko': 'CoinGecko 数据源'
      }
      return map[this.dataSource] || 'Crypto Bubbles 数据源'
    },
    gainersCount() {
      return this.gainersData.filter(item => {
        const val = item.change_pct
        return val !== null && val !== undefined && val > 0
      }).length
    },
    hamaUpCount() {
      return Object.values(this.hamaData).filter(h => h.hama_color === '绿色').length
    },
    gainersColumns() {
      return [
        {
          title: '排名',
          scopedSlots: { customRender: 'rank' },
          width: 60,
          align: 'center',
          fixed: 'left'
        },
        {
          title: '币种',
          dataIndex: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 140,
          fixed: 'left'
        },
        {
          title: '价格',
          dataIndex: 'price',
          scopedSlots: { customRender: 'price' },
          align: 'right',
          width: 120,
          sorter: (a, b) => (parseFloat(a.price) || 0) - (parseFloat(b.price) || 0)
        },
        {
          title: `${this.timeframe.toUpperCase()}涨跌`,
          dataIndex: 'change_pct',
          scopedSlots: { customRender: 'change_pct' },
          align: 'right',
          width: 110,
          sorter: (a, b) => (a.change_pct || -9999) - (b.change_pct || -9999),
          defaultSortOrder: 'descend'
        },
        {
          title: '24h成交额',
          dataIndex: 'volume',
          scopedSlots: { customRender: 'volume' },
          align: 'right',
          width: 120,
          sorter: (a, b) => (parseFloat(a.volume) || 0) - (parseFloat(b.volume) || 0)
        },
        {
          title: '市值',
          dataIndex: 'marketcap',
          scopedSlots: { customRender: 'marketcap' },
          align: 'right',
          width: 120,
          sorter: (a, b) => (parseFloat(a.marketcap) || 0) - (parseFloat(b.marketcap) || 0)
        },
        {
          title: '7天出现',
          dataIndex: 'appearCount',
          align: 'center',
          width: 80,
          sorter: (a, b) => (a.appearCount || 0) - (b.appearCount || 0)
        },
        {
          title: 'HAMA趋势',
          scopedSlots: { customRender: 'hama_trend' },
          align: 'center',
          width: 90
        },
        {
          title: '蜡烛/MA',
          scopedSlots: { customRender: 'candle_ma' },
          align: 'center',
          width: 90
        },
        {
          title: '布林带',
          scopedSlots: { customRender: 'bb_status' },
          align: 'center',
          width: 90
        },
        {
          title: '最近交叉',
          scopedSlots: { customRender: 'last_cross' },
          align: 'center',
          width: 110
        }
      ]
    }
  },
  mounted() {
    this.fetchData()
  },
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  methods: {
    onDataSourceChange() {
      this.gainersData = []
      this.hamaData = {}
      this.fetchData()
    },

    async fetchData() {
      this.loading = true

      try {
        if (this.dataSource === 'aijiaoyi') {
          await this.fetchAijiaoyiData()
        } else if (this.dataSource === 'coingecko') {
          await this.fetchCoinGeckoData()
        } else {
          await this.fetchCryptoBubblesData()
        }

        // 更新时间
        const now = new Date()
        this.updateTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`

        // 并行获取 HAMA 指标和出现次数统计
        await Promise.all([
          this.fetchHamaData(),
          this.fetchAppearCounts()
        ])

      } catch (error) {
        console.error('Fetch error:', error)
        this.$message.error('获取数据失败')
      } finally {
        this.loading = false
      }
    },

    async fetchAijiaoyiData() {
      try {
        const res = await request.get('/api/aijiaoyi/gainers?limit=20')

        if (res && res.success && res.data) {
          this.gainersData = res.data.map(item => ({
            symbol: item.symbol_short || item.symbol.replace('USDT', ''),
            binanceSymbol: item.symbol,
            price: item.price,
            change_pct: item.change_pct,
            volume: null,
            marketcap: null,
            source: 'aijiaoyi'
          }))
        } else {
          this.gainersData = []
        }
      } catch (error) {
        console.error('Fetch Aijiaoyi error:', error)
        this.$message.error('获取爱交易数据失败')
      }
    },

    async fetchCoinGeckoData() {
      try {
        const res = await request.get('/api/coingecko/top?limit=30')

        if (res && res.success && res.data) {
          this.gainersData = res.data.map(item => ({
            symbol: item.symbol_short,
            binanceSymbol: (item.symbol_short || '') + 'USDT',
            price: item.price,
            change_pct: item.change_pct,
            volume: item.volume_24h,
            marketcap: item.market_cap,
            appearCount: 0,
            source: 'coingecko',
            image: item.image || null,
          }))
          // 重新映射 binanceSymbol（部分币种名可能不直接加USDT）
          this.gainersData.forEach(item => {
            if (item.binanceSymbol === 'USDTUSDT') item.binanceSymbol = 'USDT'
            if (item.binanceSymbol === 'USDUSDT') item.binanceSymbol = 'USDCUSDT'
          })
        } else {
          this.gainersData = []
        }
      } catch (error) {
        console.error('Fetch CoinGecko error:', error)
        this.$message.error('获取 CoinGecko 数据失败')
      }
    },

    async fetchCryptoBubblesData() {
      try {
        const res = await request.get('/api/futures/futures-gainers/cryptobubbles?limit=1000')

        if (res && res.data && Array.isArray(res.data)) {
          this.allData = res.data
          // 筛选有 Binance 价格的币种并排序
          this.filterAndSort()
        } else {
          this.gainersData = []
        }
      } catch (error) {
        console.error('Fetch Crypto Bubbles error:', error)
        throw error
      }
    },

    filterAndSort() {
      // 筛选有 Binance 价格的币种
      const binanceCoins = this.allData.filter(item => {
        return item.exchangePrices && item.exchangePrices.binance !== undefined
      })

      console.log('筛选出有 Binance 价格的币种:', binanceCoins.length)

      // 添加涨跌幅字段（使用后端返回的字段名）
      const timeframeField = this.getTimeframeField()
      binanceCoins.forEach(item => {
        item.change_pct = item.performance ? item.performance[timeframeField] : null
        // 获取 Binance symbol
        item.binanceSymbol = this.getBinanceSymbol(item.symbol)
      })

      console.log('币种映射示例:', binanceCoins.slice(0, 3).map(i => ({ symbol: i.symbol, binanceSymbol: i.binanceSymbol, change_pct: i.change_pct })))

      // 按涨跌幅排序，取前10
      this.gainersData = binanceCoins
        .sort((a, b) => (b.change_pct || -9999) - (a.change_pct || -9999))
        .slice(0, 10)

      console.log('最终涨幅榜数据:', this.gainersData.map(i => ({ symbol: i.symbol, binanceSymbol: i.binanceSymbol, change_pct: i.change_pct })))
    },

    getTimeframeField() {
      const map = {
        '1h': 'hour',
        '4h': 'hour4',
        '24h': 'day',
        '7d': 'week',
        '30d': 'month'
      }
      return map[this.timeframe] || 'day'
    },

    getBinanceSymbol(symbol) {
      const symbolMapping = {
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'BNB': 'BNBUSDT',
        'SOL': 'SOLUSDT',
        'XRP': 'XRPUSDT',
        'ADA': 'ADAUSDT',
        'DOGE': 'DOGEUSDT',
        'AVAX': 'AVAXUSDT',
        'DOT': 'DOTUSDT',
        'MATIC': 'MATICUSDT',
        'LINK': 'LINKUSDT',
        'ATOM': 'ATOMUSDT',
        'UNI': 'UNIUSDT',
        'LTC': 'LTCUSDT',
        'BCH': 'BCHUSDT',
        'FIL': 'FILUSDT',
        'TRX': 'TRXUSDT',
        'ETC': 'ETCUSDT',
        'XLM': 'XLMUSDT',
        'VET': 'VETUSDT',
        'SHIB': 'SHIBUSDT',
        'APE': 'APEUSDT',
        'SAND': 'SANDUSDT',
        'MANA': 'MANAUSDT',
        'AXS': 'AXSUSDT',
        'NEAR': 'NEARUSDT',
        'FLOW': 'FLOWUSDT',
        'GMT': 'GMTUSDT',
        'ID': 'IDUSDT',
        'XTZ': 'XTZUSDT',
        '1INCH': '1INCHUSDT'
      }
      return symbolMapping[symbol] || symbol + 'USDT'
    },

    async fetchHamaData() {
      const binanceSymbols = this.gainersData.map(item => item.binanceSymbol).filter(s => s)

      if (binanceSymbols.length === 0) {
        console.log('没有可获取 HAMA 数据的币种')
        return
      }

      console.log('准备获取 HAMA 数据的币种:', binanceSymbols)
      this.hamaLoading = true
      try {
        const res = await request.get(`/api/futures/futures-gainers/hama/${binanceSymbols.join(',')}`)

        console.log('HAMA API 响应:', res)

        if (res.success && res.data) {
          this.hamaData = res.data
          console.log('HAMA 数据已加载:', Object.keys(this.hamaData).length, '个币种')
        } else {
          console.log('HAMA API 返回失败:', res)
        }
      } catch (error) {
        console.error('Fetch HAMA data error:', error)
      } finally {
        this.hamaLoading = false
      }
    },

    async fetchAppearCounts() {
      try {
        const res = await request({
          method: 'get',
          url: '/api/gainer-stats/frequent-symbols',
          params: { days: 7, limit: 1000 }
        })
        if (res && res.success && res.data) {
          const countMap = {}
          res.data.forEach(item => {
            // 后端可能返回 symbol 带 USDT 或不带，两种都匹配
            const sym = item.symbol
            countMap[sym] = item.count
            // 如果后端返回的是 BTCUSDT 格式，也存 BTC 格式
            if (sym.endsWith('USDT')) {
              countMap[sym.replace('USDT', '')] = item.count
            }
          })
          // 给 gainersData 每个币种加上 appearCount
          this.gainersData.forEach(item => {
            item.appearCount = countMap[item.binanceSymbol] || 0
          })
          console.log('出现次数已更新:', this.gainersData.map(i => ({ s: i.symbol, c: i.appearCount })))
        }
      } catch (error) {
        console.error('获取出现次数失败:', error)
      }
    },

    getHamaData(symbol) {
      return this.hamaData[symbol]
    },

    getHamaColorTag(color) {
      const map = {
        '绿色': 'green',
        '红色': 'red',
        '灰色': 'default'
      }
      return map[color] || 'default'
    },

    getHamaTrendText(trend) {
      const map = {
        '上涨': '上涨',
        '下跌': '下跌',
        '盘整': '盘整'
      }
      return map[trend] || '-'
    },

    getCandleMAClass(status) {
      if (status === 'MA上') return 'candle-above'
      if (status === 'MA下') return 'candle-below'
      return ''
    },

    getCandleMAText(status) {
      const map = {
        'MA上': 'MA上',
        'MA下': 'MA下',
        '重合': '重合'
      }
      return map[status] || '-'
    },

    getBollingerColor(status) {
      const map = {
        '收缩': 'orange',
        '扩张': 'blue',
        '正常': 'default'
      }
      return map[status] || 'default'
    },

    getBollingerText(status) {
      const map = {
        '收缩': '收缩',
        '扩张': '扩张',
        '正常': '正常'
      }
      return map[status] || '-'
    },

    formatCrossTime(timeStr) {
      if (!timeStr) return '-'
      const parts = timeStr.split(' ')
      if (parts.length >= 2) {
        const datePart = parts[0].split('-')
        const timePart = parts[1].split(':')
        if (datePart.length >= 3 && timePart.length >= 2) {
          return `${datePart[1]}-${datePart[2]} ${timePart[0]}:${timePart[1]}`
        }
      }
      return timeStr
    },

    getTextClass(value) {
      if (value === null || value === undefined) return ''
      return value >= 0 ? 'price-up' : 'price-down'
    },

    formatPrice(price) {
      if (!price) return '-'
      const num = parseFloat(price)
      if (num >= 1000) return num.toFixed(2)
      if (num >= 1) return num.toFixed(4)
      return num.toFixed(6)
    },

    formatVolume(volume) {
      if (!volume) return '-'
      const num = parseFloat(volume)
      if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T'
      if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B'
      if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M'
      if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K'
      return num.toFixed(2)
    },

    getRankColor(index) {
      if (index === 0) return 'red'
      if (index === 1) return 'orange'
      if (index === 2) return 'gold'
      return 'default'
    },

    getTradingViewUrl(record) {
      const symbol = record.binanceSymbol || record.symbol + 'USDT'
      return `https://cn.tradingview.com/chart/?symbol=BINANCE:${symbol}`
    },

    toggleAutoRefresh(checked) {
      if (checked) {
        this.refreshInterval = setInterval(() => {
          this.fetchData()
        }, 60000)
        this.$message.info('自动刷新已开启')
      } else {
        if (this.refreshInterval) {
          clearInterval(this.refreshInterval)
          this.refreshInterval = null
        }
        this.$message.info('自动刷新已关闭')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.futures-gainers-container {
  padding: 16px;

  .header-card {
    margin-bottom: 16px;

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
  }

  .stats-row {
    margin-bottom: 16px;
  }

  .gainers-card {
    border-top: 3px solid #F0B90B; // Binance 黄色

    ::v-deep .ant-card-head-title {
      font-size: 16px;
      font-weight: 600;
    }

    .symbol-cell {
      display: flex;
      align-items: center;
      gap: 8px;

      .coin-icon {
        width: 20px;
        height: 20px;
        border-radius: 50%;
      }
    }

    .symbol-text {
      font-weight: 600;
      font-family: 'Courier New', monospace;
      color: var(--primary-color, #1890ff);
      text-decoration: none;
      &:hover {
        text-decoration: underline;
        opacity: 0.85;
      }
    }

    .price-text {
      font-family: 'Courier New', monospace;
    }

    .price-up {
      color: #52c41a;
    }

    .price-down {
      color: #f5222d;
    }

    .candle-above {
      color: #52c41a;
      font-weight: 500;
    }

    .candle-below {
      color: #f5222d;
      font-weight: 500;
    }

    .cross-time {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
    }
  }
}
</style>
