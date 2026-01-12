<template>
  <div class="tradingview-scanner-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>{{ $t('tradingviewScanner.title') }}</h2>
          <p class="subtitle">{{ $t('tradingviewScanner.subtitle') }}</p>
        </div>
        <a-space>
          <!-- SSE 连接状态 -->
          <a-tag :color="sseStatusColor">
            <a-icon :type="sseConnected ? 'sync' : 'disconnect'" :spin="sseConnected" />
            {{ $t('tradingviewScanner.realtimePrice') }}: {{ sseStatusText }}
          </a-tag>
          <a-select
            v-model="dataType"
            style="width: 150px"
            @change="handleDataTypeChange"
          >
            <a-select-option value="perpetuals">
              {{ $t('tradingviewScanner.perpetuals') }}
            </a-select-option>
            <a-select-option value="top-gainers">
              {{ $t('tradingviewScanner.topGainers') }}
            </a-select-option>
            <a-select-option value="watchlist">
              {{ $t('tradingviewScanner.watchlist') }}
            </a-select-option>
          </a-select>
          <a-input-number
            v-model="limit"
            :min="1"
            :max="dataType === 'perpetuals' ? 50 : 50"
            :default-value="10"
            style="width: 100px"
            @change="fetchData"
          />
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            {{ $t('common.refresh') }}
          </a-button>
          <a-button @click="loadAllHAMAIndicators" :loading="loading">
            <a-icon type="thunderbolt" />
            HAMA
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 统计信息 -->
    <a-row :gutter="16" class="stats-row" v-if="statistics">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('tradingviewScanner.stats.total')"
            :value="statistics.total"
            prefix="📊"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('tradingviewScanner.stats.avgChange')"
            :value="statistics.avgChange"
            suffix="%"
            :precision="2"
            :value-style="{ color: statistics.avgChange >= 0 ? '#3f8600' : '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('tradingviewScanner.stats.gainers')"
            :value="statistics.gainers"
            prefix="📈"
            :value-style="{ color: '#3f8600' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('tradingviewScanner.stats.losers')"
            :value="statistics.losers"
            prefix="📉"
            :value-style="{ color: '#cf1322' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 数据表格 -->
    <a-card
      :bordered="false"
      :title="`${$t('tradingviewScanner.tableTitle')} - ${dataSource.length} ${$t('tradingviewScanner.coins')}`"
    >
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200, y: 600 }"
        rowKey="symbol"
        size="middle"
      >
        <!-- 排名 -->
        <template slot="rank" slot-scope="text, record, index">
          <div class="rank-badge" :class="getRankClass(index + 1)">
            {{ index + 1 }}
          </div>
        </template>

        <!-- 币种 -->
        <template slot="symbol" slot-scope="text">
          <a-tag color="blue">{{ text }}</a-tag>
        </template>

        <!-- 价格 -->
        <template slot="price" slot-scope="text, record">
          <span
            class="price-value"
            :class="{ 'price-flash': isPriceJustUpdated(record.symbol) }"
          >
            ${{ formatPrice(text, record.symbol) }}
          </span>
        </template>

        <!-- 涨跌幅 -->
        <template slot="change_percentage" slot-scope="text, record">
          <span
            class="change-badge"
            :class="getRealtimeChangeClass(record.symbol, text)"
          >
            <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
            {{ getRealtimeChangeText(record.symbol, text) }}
          </span>
        </template>

        <!-- 成交量 -->
        <template slot="volume" slot-scope="text">
          {{ formatVolume(text) }}
        </template>
        <!-- HAMA指标 -->
        <template slot="price_ma100" slot-scope="text, record">
          <a-tooltip :title="getHAMATooltip(record)">
            <a-tag :color="getHAMAColor(record)" size="small">
              {{ getHAMAText(record) }}
            </a-tag>
          </a-tooltip>
        </template>

        <!-- 涨幅榜次数 -->
        <template slot="gainer_appearances" slot-scope="text, record">
          <a-tag v-if="record.gainer_count > 0" :color="getGainerCountColor(record.gainer_count)" size="small">
            {{ record.gainer_count }}次
          </a-tag>
          <span v-else style="color: #999;">-</span>
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
import { getWatchlist, getPerpetuals, getTopGainers } from '@/api/tradingviewScanner'
import { getBatchHAMAIndicators } from '@/api/hamaHybrid'
import { getFrequentSymbols } from '@/api/gainerStats'
import request from '@/utils/request'
import realtimePriceMixin from '@/mixins/realtimePrice'

export default {
  name: 'TradingViewScanner',
  mixins: [realtimePriceMixin],
  data () {
    return {
      dataType: 'perpetuals',
      loading: false,
      dataSource: [],
      limit: 10,
      statistics: null,
      priceUpdateTimestamps: {}, // 存储价格更新时间戳
      gainerStats: {}, // 存储涨幅榜出现次数统计
      pagination: {
        pageSize: 10,
        current: 1,
        total: 0,
        showSizeChanger: true,
        showTotal: total => `${total} ${this.$t('tradingviewScanner.totalCoins')}`
      },
      columns: [
        {
          title: '#',
          scopedSlots: { customRender: 'rank' },
          width: 60,
          align: 'center',
          fixed: 'left'
        },
        {
          title: this.$t('tradingviewScanner.table.symbol'),
          dataIndex: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 120,
          fixed: 'left'
        },
        {
          title: this.$t('tradingviewScanner.table.price'),
          dataIndex: 'price',
          scopedSlots: { customRender: 'price' },
          width: 120,
          align: 'right'
        },
        {
          title: this.$t('tradingviewScanner.table.change24h'),
          dataIndex: 'change_percentage',
          scopedSlots: { customRender: 'change_percentage' },
          width: 120,
          align: 'center'
        },
        {
          title: this.$t('tradingviewScanner.table.volume'),
          dataIndex: 'volume',
          scopedSlots: { customRender: 'volume' },
          width: 120,
          align: 'right'
        },
        {
          title: 'HAMA指标',
          scopedSlots: { customRender: 'price_ma100' },
          width: 140,
          align: 'center'
        },
        {
          title: '涨幅榜次数',
          dataIndex: 'gainer_appearances',
          scopedSlots: { customRender: 'gainer_appearances' },
          width: 120,
          align: 'center'
        },
        {
          title: this.$t('common.action'),
          scopedSlots: { customRender: 'action' },
          width: 120,
          fixed: 'right'
        }
      ]
    }
  },
  mounted () {
    this.fetchData()
    this.loadGainerStats()
    // 每5分钟自动刷新(与HAMA缓存过期时间匹配)
    this.timer = setInterval(() => {
      this.fetchData()
    }, 300000) // 5分钟 = 300秒
  },
  beforeDestroy () {
    if (this.timer) {
      clearInterval(this.timer)
    }
  },
  methods: {
    // 重写 handlePriceUpdate 方法以处理实时价格更新
    handlePriceUpdate (priceData) {
      // 调用 mixin 的方法
      this.$options.mixins[0].methods.handlePriceUpdate.call(this, priceData)

      const { symbol, price, change24h } = priceData

      // 查找并更新表格中对应的数据行
      const rowIndex = this.dataSource.findIndex(item => item.symbol === symbol)

      if (rowIndex !== -1) {
        // 更新价格和涨跌幅
        this.$set(this.dataSource[rowIndex], 'price', price)
        this.$set(this.dataSource[rowIndex], 'change_percentage', change24h)

        // 记录更新时间戳,用于闪烁效果
        this.$set(this.priceUpdateTimestamps, symbol, Date.now())

        // 500ms后移除闪烁效果
        setTimeout(() => {
          this.$delete(this.priceUpdateTimestamps, symbol)
        }, 500)
      }
    },

    // 检查价格是否刚刚更新
    isPriceJustUpdated (symbol) {
      const timestamp = this.priceUpdateTimestamps[symbol]
      if (!timestamp) return false

      const diff = Date.now() - timestamp
      return diff < 500 // 500ms 内算刚更新
    },

    // 获取实时价格格式化
    formatPrice (price, symbol) {
      // 如果有实时价格,使用实时价格
      const realtimeData = this.realtimePrices[symbol]
      if (realtimeData && realtimeData.price) {
        price = realtimeData.price
      }

      if (!price) return '-'

      if (price >= 1000) {
        return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      } else if (price >= 1) {
        return price.toFixed(4)
      } else {
        return price.toFixed(6)
      }
    },

    // 获取实时涨跌幅样式类名
    getRealtimeChangeClass (symbol, currentChange) {
      const realtimeData = this.realtimePrices[symbol]
      const change = realtimeData && realtimeData.change24h !== undefined ? realtimeData.change24h : currentChange

      return change >= 0 ? 'positive' : 'negative'
    },

    // 获取实时涨跌幅文本
    getRealtimeChangeText (symbol, currentChange) {
      const realtimeData = this.realtimePrices[symbol]
      const change = realtimeData && realtimeData.change24h !== undefined ? realtimeData.change24h : currentChange

      if (change === undefined || change === null) return '-'

      return change.toFixed(2) + '%'
    },

    async fetchData () {
      this.loading = true
      try {
        let response
        const params = { limit: this.limit }

        if (this.dataType === 'perpetuals') {
          response = await getPerpetuals(params)
        } else if (this.dataType === 'top-gainers') {
          response = await getTopGainers(params)
        } else {
          response = await getWatchlist(params)
        }

        if (response.success) {
          this.dataSource = (response.data || []).map(item => ({
            ...item,
            gainer_count: this.getGainerCount(item.symbol)
          }))
          this.pagination.total = this.dataSource.length
          this.calculateStatistics()
          // 自动加载所有币种的HAMA状态(从缓存读取)
          this.autoAnalyzeAllHamaBatch()
          // 不再自动加载HAMA指标,需要用户手动点击HAMA按钮
          // this.loadAllHAMAIndicators()
          this.$message.success(this.$t('tradingviewScanner.messages.fetchSuccess'))
        } else {
          this.$message.error(response.error || this.$t('tradingviewScanner.messages.fetchError'))
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        this.$message.error(this.$t('tradingviewScanner.messages.fetchError'))
      } finally {
        this.loading = false
      }
    },

    // 使用批量分析API自动加载所有币种的HAMA状态(优先使用缓存)
    async autoAnalyzeAllHamaBatch () {
      try {
        // 提取所有币种symbol
        const symbols = this.dataSource.map(item => item.symbol)

        if (symbols.length === 0) {
          return
        }

        console.log(`批量分析 ${symbols.length} 个币种的HAMA状态(优先使用缓存)...`)

        const response = await request({
          url: '/api/gainer-analysis/analyze-batch',
          method: 'post',
          data: {
            symbols: symbols,
            force_refresh: false // 不强制刷新,优先使用缓存
          }
        })

        if (response.code === 1 && response.data) {
          const results = response.data.results
          const summary = response.data.summary

          console.log(`批量分析完成: 总数${summary.total}, 成功${summary.success}, 缓存${summary.cached}`)

          // 将HAMA分析结果合并到dataSource
          this.dataSource.forEach(item => {
            if (results[item.symbol] && !results[item.symbol].error) {
              this.$set(item, 'hama_analysis', results[item.symbol].hama_analysis)
              this.$set(item, 'hama_conditions', results[item.symbol].conditions)
              this.$set(item, 'hama_cached', results[item.symbol].cached)
            }
          })
        } else {
          console.error('批量分析失败:', response.msg)
        }
      } catch (error) {
        console.error('批量分析失败:', error)
      }
    },

    // 批量加载所有币种的 HAMA 指标数据(混合模式)
    async loadAllHAMAIndicators () {
      try {
        let symbols = this.dataSource.map(item => item.symbol)

        if (symbols.length === 0) {
          return
        }

        // 限制每次只加载前10个币种 (现在默认只显示10个币种)
        const MAX_SYMBOLS_PER_REQUEST = 10
        if (symbols.length > MAX_SYMBOLS_PER_REQUEST) {
          symbols = symbols.slice(0, MAX_SYMBOLS_PER_REQUEST)
          this.$message.info(`币种数量较多(${this.dataSource.length}个),本次仅加载前${MAX_SYMBOLS_PER_REQUEST}个币种的HAMA指标`)
        }

        console.log(`[HAMA混合模式] 批量加载 ${symbols.length} 个币种的HAMA指标...`)

        const response = await getBatchHAMAIndicators(symbols, {
          interval: '15',
          use_selenium: false,
          max_parallel: 5
        })

        if (response.success && response.data) {
          const results = response.data
          console.log(`[HAMA混合模式] 加载完成: ${response.count}/${response.total} 成功`)

          // 将HAMA指标数据合并到dataSource
          results.forEach(item => {
            const rowIndex = this.dataSource.findIndex(d => d.symbol === item.symbol)
            if (rowIndex !== -1) {
              this.$set(this.dataSource[rowIndex], 'hama_indicator', item)
            }
          })

          this.$message.success(`HAMA指标加载完成: ${response.count}/${response.total}`)
        } else {
          console.error('[HAMA混合模式] 加载失败:', response.message)
          this.$message.error('HAMA指标加载失败')
        }
      } catch (error) {
        console.error('[HAMA混合模式] 加载失败:', error)
        this.$message.error('HAMA指标加载失败')
      }
    },

    // 获取HAMA状态显示文本
    getHAMAText (record) {
      if (!record.hama_indicator) {
        return '-'
      }

      const hamaStatus = record.hama_indicator.hama_status
      const crossSignal = record.hama_indicator.cross_signal

      if (crossSignal && crossSignal.signal) {
        // 有交叉信号
        return crossSignal.signal
      } else if (hamaStatus) {
        // 显示趋势状态
        return hamaStatus.status_text || '-'
      }

      return '-'
    },

    // 获取HAMA状态颜色
    getHAMAColor (record) {
      if (!record.hama_indicator) {
        return 'default'
      }

      const hamaStatus = record.hama_indicator.hama_status
      const crossSignal = record.hama_indicator.cross_signal

      if (crossSignal && crossSignal.signal === '涨') {
        return 'green'
      } else if (crossSignal && crossSignal.signal === '跌') {
        return 'red'
      } else if (hamaStatus && hamaStatus.trend === 'bullish') {
        return 'cyan'
      } else if (hamaStatus && hamaStatus.trend === 'bearish') {
        return 'orange'
      }

      return 'default'
    },

    // 获取HAMA提示信息
    getHAMATooltip (record) {
      if (!record.hama_indicator) {
        return '点击刷新按钮加载HAMA指标'
      }

      const data = record.hama_indicator
      const hamaStatus = data.hama_status || {}
      const bollinger = data.bollinger_bands || {}

      let tooltip = `来源: ${data.source || 'unknown'}`
      tooltip += `\n耗时: ${data.calculation_time?.toFixed(2) || 0}s`
      tooltip += `\n缓存: ${data.cached ? '是' : '否'}`

      if (hamaStatus.status_text) {
        tooltip += `\n状态: ${hamaStatus.status_text}`
      }

      if (hamaStatus.candle_ma_relation) {
        tooltip += `\n${hamaStatus.candle_ma_relation}`
      }

      if (data.ma100) {
        tooltip += `\nMA100: $${data.ma100.toFixed(2)}`
      }

      if (bollinger.status) {
        const statusMap = { squeeze: '收缩', expansion: '扩张', normal: '正常' }
        tooltip += `\n布林带: ${statusMap[bollinger.status] || bollinger.status}`
      }

      return tooltip
    },

    // 加载涨幅榜统计
    async loadGainerStats () {
      try {
        const response = await getFrequentSymbols({ limit: 50, days: 7 })

        if (response.success && response.data) {
          // 转换为 symbol -> count 映射
          this.gainerStats = {}
          response.data.forEach(item => {
            this.gainerStats[item.symbol] = item.count
          })

          console.log('[涨幅榜统计] 加载完成:', response.data.length, '个币种')
        }
      } catch (error) {
        console.error('加载涨幅榜统计失败:', error)
      }
    },

    // 获取涨幅榜次数
    getGainerCount (symbol) {
      return this.gainerStats[symbol] || 0
    },

    // 获取涨幅榜次数颜色
    getGainerCountColor (count) {
      if (count >= 5) return 'red' // 经常出现
      if (count >= 3) return 'orange' // 有时出现
      return 'green' // 偶尔出现
    },

    // 批量加载所有币种的 MA100 数据
    // async loadAllMA100Data () {
//       try {
//         // 提取所有币种symbol
//         const symbols = this.dataSource.map(item => item.symbol)
//
//         if (symbols.length === 0) {
//           return
//         }
//
//         console.log(`批量加载 ${symbols.length} 个币种的 MA100 数据...`)
//
//         // 批量调用 MA100 API (每批10个币种)
//         const batchSize = 10
//         for (let i = 0; i < symbols.length; i += batchSize) {
//           const batch = symbols.slice(i, i + batchSize)
//           await Promise.all(batch.map(symbol => this.loadMA100ForSymbol(symbol)))
//
//           // 每批次之间稍作延迟,避免过载
//           if (i + batchSize < symbols.length) {
//             await new Promise(resolve => setTimeout(resolve, 100))
//           }
//         }
//
//         console.log('MA100 数据加载完成')
//       } catch (error) {
//         console.error('加载 MA100 数据失败:', error)
//       }
//     },

    // 加载单个币种的 MA100 数据
    async loadMA100ForSymbol (symbol) {
      try {
        const response = await request({
          url: '/api/indicator/ma100',
          method: 'post',
          data: {
            symbol: symbol,
            interval: '15m',
            limit: 1
          }
        })

        if (response.success && response.data && response.data.length > 0) {
          const latestData = response.data[0]
          const currentPrice = latestData.close
          const ma100 = latestData.ma100

          // 查找并更新表格中的数据
          const rowIndex = this.dataSource.findIndex(item => item.symbol === symbol)
          if (rowIndex !== -1) {
            this.$set(this.dataSource[rowIndex], 'ma100', ma100)
            this.$set(this.dataSource[rowIndex], 'price_above_ma100', currentPrice > ma100)
          }
        }
      } catch (error) {
        console.error(`加载 ${symbol} MA100 数据失败:`, error)
      }
    },

    // 自动批量分析所有币种的HAMA状态(备用方法)
    async autoAnalyzeAllHama () {
      // 限制并发数量,避免过载
      const batchSize = 5
      for (let i = 0; i < this.dataSource.length; i += batchSize) {
        const batch = this.dataSource.slice(i, i + batchSize)
        const promises = batch.map(record => this.analyzeHama(record))
        await Promise.all(promises)
        // 每批次之间稍作延迟
        if (i + batchSize < this.dataSource.length) {
          await new Promise(resolve => setTimeout(resolve, 200))
        }
      }
    },

    calculateStatistics () {
      if (this.dataSource.length === 0) {
        this.statistics = null
        return
      }

      const total = this.dataSource.length
      const avgChange = this.dataSource.reduce((sum, item) => sum + (item.change_percentage || 0), 0) / total
      const gainers = this.dataSource.filter(item => item.change_percentage > 0).length
      const losers = this.dataSource.filter(item => item.change_percentage < 0).length

      this.statistics = {
        total,
        avgChange: avgChange.toFixed(2),
        gainers,
        losers
      }
    },

    handleDataTypeChange () {
      // 根据数据类型调整默认limit
      if (this.dataType === 'perpetuals') {
        this.limit = 50
        this.pagination.pageSize = 50
      } else {
        this.limit = 20
        this.pagination.pageSize = 20
      }
      this.fetchData()
    },

    formatVolume (volume) {
      if (!volume) return '0'
      if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(2) + 'B'
      } else if (volume >= 1000000) {
        return (volume / 1000000).toFixed(2) + 'M'
      } else if (volume >= 1000) {
        return (volume / 1000).toFixed(2) + 'K'
      }
      return volume.toFixed(2)
    },

    getRankClass (rank) {
      if (rank === 1) return 'rank-gold'
      if (rank === 2) return 'rank-silver'
      if (rank === 3) return 'rank-bronze'
      return 'rank-normal'
    },

    getTradingViewUrl (symbol) {
      return `https://cn.tradingview.com/chart/?symbol=BINANCE:${symbol}`
    },

    // HAMA分析方法
    async analyzeHama (record, silent = false) {
      // 如果已经有分析结果,跳过
      if (record.hama_analysis) {
        return
      }

      // 设置loading状态
      this.$set(record, 'hama_loading', true)

      try {
        const response = await request({
          url: '/api/gainer-analysis/analyze-symbol',
          method: 'post',
          data: {
            symbol: record.symbol
          }
        })

        if (response.code === 1 && response.data) {
          this.$set(record, 'hama_analysis', response.data.hama_analysis)
          this.$set(record, 'hama_conditions', response.data.conditions)
        } else {
          if (!silent) {
            this.$message.error('HAMA分析失败: ' + (response.msg || '未知错误'))
          }
        }
      } catch (error) {
        console.error('HAMA分析错误:', error)
        if (!silent) {
          this.$message.error('HAMA分析失败')
        }
      } finally {
        this.$set(record, 'hama_loading', false)
      }
    },

    getHamaRecommendationText (recommendation) {
      // 使用hamaCandle.txt中的趋势状态
      const texts = {
        'BUY': '上涨趋势',
        'SELL': '下跌趋势',
        'HOLD': '盘整'
      }
      return texts[recommendation] || recommendation
    },

    getHamaStatusColor (recommendation) {
      // 使用hamaCandle.txt中的颜色方案
      const colors = {
        'BUY': 'green', // 上涨趋势 - 绿色
        'SELL': 'red', // 下跌趋势 - 红色
        'HOLD': '#8c8c8c' // 盘整 - 灰色
      }
      return colors[recommendation] || '#8c8c8c'
    },

    getConfidenceColor (confidence) {
      if (confidence >= 0.8) return '#52c41a'
      if (confidence >= 0.6) return '#1890ff'
      return '#faad14'
    },

    formatCrossTime (timestamp) {
      if (!timestamp) return '-'

      const date = new Date(timestamp)
      const now = new Date()
      const diff = Math.floor((now - date) / 1000) // 秒

      // 1小时内显示"X分钟前"
      if (diff < 60) return '刚刚'
      if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`

      // 24小时内显示"X小时前"
      if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`

      // 7天内显示"X天前"
      if (diff < 604800) return `${Math.floor(diff / 86400)}天前`

      // 超过7天显示具体日期
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.tradingview-scanner-container {
  padding: 20px;

  .header-card {
    margin-bottom: 20px;

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
        margin: 5px 0 0 0;
        color: #8c8c8c;
        font-size: 14px;
      }
    }
  }

  .stats-row {
    margin-bottom: 20px;
  }

  .rank-badge {
    width: 32px;
    height: 32px;
    line-height: 32px;
    text-align: center;
    border-radius: 4px;
    font-weight: bold;
    display: inline-block;

    &.rank-gold {
      background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
      color: #fff;
    }

    &.rank-silver {
      background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%);
      color: #fff;
    }

    &.rank-bronze {
      background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
      color: #fff;
    }

    &.rank-normal {
      background: #f0f0f0;
      color: #666;
    }
  }

  .price-value {
    font-weight: 500;
    font-family: 'Courier New', monospace;

    &.price-flash {
      animation: priceFlash 0.5s ease-in-out;
    }
  }

  @keyframes priceFlash {
    0% {
      background-color: rgba(24, 144, 255, 0.3);
      transform: scale(1.05);
    }
    100% {
      background-color: transparent;
      transform: scale(1);
    }
  }

  .change-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 600;

    &.positive {
      background: #f6ffed;
      color: #52c41a;
    }

    &.negative {
      background: #fff1f0;
      color: #ff4d4f;
    }
  }

  .hama-status {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .hama-status-header {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .hama-tag {
      font-weight: 600;
    }

    .hama-confidence {
      width: 60px;
    }
  }

  .hama-loading {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .hama-pending {
    display: flex;
    justify-content: center;
    align-items: center;
    color: #1890ff;
  }

  .hama-cross-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .cross-time {
      font-size: 12px;
      color: #8c8c8c;
      margin-top: 2px;
    }
  }

  .price-ma100 {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .ma100-info {
      display: flex;
      flex-direction: column;
      align-items: center;

      .ma100-price {
        font-size: 12px;
        color: #8c8c8c;
        margin-top: 2px;
      }
    }
  }
}
</style>
