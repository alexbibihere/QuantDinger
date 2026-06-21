<template>
  <div class="hama-market-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div class="header-left">
          <div class="title-row">
            <h2>{{ $t('hamaMarket.title') }}</h2>
            <a-button
              type="primary"
              icon="plus"
              style="margin-left: 24px;"
              @click="showAddModal"
            >
              添加币种
            </a-button>
          </div>
          <p class="subtitle">仅展示你手动添加的币种，点击「添加币种」增加监控品种</p>
        </div>
        <a-space>
          <!-- 数据源选择 -->
          <div style="white-space: nowrap">
            <span style="margin-right: 8px; font-size: 13px; color: #666;">数据源:</span>
            <a-radio-group v-model="dataSource" button-style="solid" size="small" @change="handleDataSourceChange">
              <a-radio-button value="ocr">
                <a-icon type="scan" /> OCR
              </a-radio-button>
              <a-radio-button value="tv">
                <a-icon type="api" /> TV-Bridge
              </a-radio-button>
              <a-radio-button value="auto">
                <a-icon type="check-circle" /> 自动
              </a-radio-button>
            </a-radio-group>
          </div>
          <!-- 时间周期(仅TV模式) -->
          <div v-if="dataSource !== 'ocr'" style="white-space: nowrap">
            <span style="margin-right: 8px; font-size: 13px; color: #666;">周期:</span>
            <a-select v-model="tvTimeframe" style="width: 90px;" size="small" @change="fetchData">
              <a-select-option value="1">1m</a-select-option>
              <a-select-option value="5">5m</a-select-option>
              <a-select-option value="15">15m</a-select-option>
              <a-select-option value="60">1H</a-select-option>
              <a-select-option value="240">4H</a-select-option>
              <a-select-option value="D">日线</a-select-option>
              <a-select-option value="W">周线</a-select-option>
            </a-select>
          </div>
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
            title="监控品种数"
            :value="mySymbols.length"
            prefix="📊"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="上涨趋势"
            :value="watchlist.filter(item => item.hama_tv && item.hama_tv.hama_color === 'green').length"
            :value-style="{ color: '#3f8600' }"
            prefix="📈"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <a-statistic
            title="下跌趋势"
            :value="watchlist.filter(item => item.hama_tv && item.hama_tv.hama_color === 'red').length"
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
        :pagination="{ pageSize: 20, showSizeChanger: true, showTotal: total => `共 ${total} 个品种` }"
        row-key="symbol"
        :scroll="{ x: 2000 }"
        size="middle"
      >
        <!-- 币种 -->
        <template slot="symbol" slot-scope="text">
          <a-tag color="blue">{{ text }}</a-tag>
        </template>

        <!-- 价格 -->
        <template slot="price_value" slot-scope="text, record">
          <span v-if="record.hama_tv" class="price-value">
            {{ formatPrice(record.hama_tv.price) }}
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 涨跌幅 -->
        <template slot="change_pct" slot-scope="text, record">
          <span v-if="record.hama_tv && record.hama_tv.change_pct != null"
            :style="{ color: record.hama_tv.change_pct >= 0 ? '#3f8600' : '#cf1322', fontWeight: 500 }">
            {{ record.hama_tv.change_pct >= 0 ? '+' : '' }}{{ record.hama_tv.change_pct.toFixed(2) }}%
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- HAMA Open -->
        <template slot="hama_open" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number">{{ record.hama_tv.hama_open.toFixed(2) }}</span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- HAMA Close -->
        <template slot="hama_close" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number"
            :style="{ color: record.hama_tv.hama_color === 'green' ? '#3f8600' : '#cf1322' }">
            {{ record.hama_tv.hama_close.toFixed(2) }}
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- HAMA MA -->
        <template slot="hama_ma" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number" style="color: #faad14;">
            {{ record.hama_tv.hama_ma.toFixed(2) }}
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- HAMA 颜色/趋势 -->
        <template slot="hama_status_display" slot-scope="text, record">
          <a-tag
            v-if="record.hama_tv"
            :color="record.hama_tv.hama_color"
          >
            <a-icon :type="record.hama_tv.hama_color === 'green' ? 'arrow-up' : 'arrow-down'" />
            {{ record.hama_tv.hama_color === 'green' ? '多' : record.hama_tv.hama_color === 'red' ? '空' : '盘' }}
          </a-tag>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 金叉 -->
        <template slot="cross_up" slot-scope="text, record">
          <a-icon v-if="record.hama_tv && record.hama_tv.cross_up" type="check-circle" style="color: #52c41a; font-size: 16px;" />
          <span v-else style="color: #eee">－</span>
        </template>

        <!-- 死叉 -->
        <template slot="cross_down" slot-scope="text, record">
          <a-icon v-if="record.hama_tv && record.hama_tv.cross_down" type="close-circle" style="color: #f5222d; font-size: 16px;" />
          <span v-else style="color: #eee">－</span>
        </template>

        <!-- MA 趋势 -->
        <template slot="ma_trend" slot-scope="text, record">
          <span v-if="record.hama_tv">
            <a-tag v-if="record.hama_tv.hama_rising" color="green" style="margin: 0;">↑</a-tag>
            <a-tag v-else-if="record.hama_tv.hama_falling" color="red" style="margin: 0;">↓</a-tag>
            <a-tag v-else style="margin: 0;">→</a-tag>
          </span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 布林上轨 -->
        <template slot="bb_upper" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number" style="color: #52c41a;">{{ record.hama_tv.bb_upper.toFixed(2) }}</span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 布林中轨 -->
        <template slot="bb_basis" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number" style="color: #1890ff;">{{ record.hama_tv.bb_basis.toFixed(2) }}</span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 布林下轨 -->
        <template slot="bb_lower" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number" style="color: #722ed1;">{{ record.hama_tv.bb_lower.toFixed(2) }}</span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 布林带宽 -->
        <template slot="bb_width" slot-scope="text, record">
          <span v-if="record.hama_tv" class="mono-number">{{ (record.hama_tv.bb_width * 100).toFixed(1) }}%</span>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 布林状态 -->
        <template slot="bb_status" slot-scope="text, record">
          <a-tag v-if="record.hama_tv && record.hama_tv.bb_squeeze" color="orange" style="font-size: 11px;">收缩</a-tag>
          <a-tag v-else-if="record.hama_tv && record.hama_tv.bb_expansion" color="blue" style="font-size: 11px;">扩张</a-tag>
          <span v-else style="color: #999">-</span>
        </template>

        <!-- 操作 -->
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a-button
              type="link"
              size="small"
              :href="getTradingViewUrl(record.symbol)"
              target="_blank"
            >
              <a-icon type="line-chart" />
            </a-button>
            <a-button
              type="link"
              size="small"
              @click="showChartSvg(record)"
            >
              <a-icon type="picture" />
            </a-button>
            <a-popconfirm
              title="确定移除此品种？"
              @confirm="removeSymbol(record.symbol)"
            >
              <a-button type="link" size="small" style="color: #ff4d4f;">
                <a-icon type="delete" />
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 添加币种弹窗 -->
    <a-modal
      :visible="addModalVisible"
      title="添加币种"
      @ok="handleAddSymbol"
      @cancel="addModalVisible = false"
      :confirm-loading="addLoading"
      ok-text="添加并查询"
    >
      <a-input-search
        v-model="addSymbolInput"
        placeholder="输入币种名，如 BTCUSDT"
        size="large"
        @search="handleAddSymbol"
        enter-button="添加"
      >
      </a-input-search>
      <div style="margin-top: 12px; font-size: 13px; color: #999;">
        常用币种: 
        <a-tag
          v-for="sym in commonSymbols"
          :key="sym"
          style="cursor: pointer; margin-bottom: 4px;"
          @click="addSymbolInput = sym"
        >{{ sym }}</a-tag>
      </div>
      <p v-if="addError" style="color: #ff4d4f; margin-top: 8px;">{{ addError }}</p>
    </a-modal>

    <!-- SVG 图表弹窗 -->
    <a-modal
      :visible="svgModalVisible"
      :title="svgModalTitle"
      :footer="null"
      @cancel="svgModalVisible = false"
      width="650px"
      centered
    >
      <div style="text-align: center; min-height: 350px; background: #1a1a2e; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <a-spin v-if="svgModalLoading" size="large" />
        <img v-else-if="svgModalImage" :src="svgModalImage" style="width: 100%; border-radius: 6px;" />
        <div v-else style="color: #999;">加载失败</div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { getHamaTv, batchGetHamaTv, getTvBridgeHealth, getHamaChartSvg } from '@/api/hamaTv'
import realtimePriceMixin from '@/mixins/realtimePrice'

const STORAGE_KEY = 'hama_market_symbols'

export default {
  name: 'HamaMarket',
  mixins: [realtimePriceMixin],
  data () {
    return {
      loading: false,
      watchlist: [],
      apiConnected: false,
      timer: null,
      // 数据源设置
      dataSource: 'auto',
      tvTimeframe: 'D',
      tvBridgeConnected: false,
      // 添加币种
      addModalVisible: false,
      addSymbolInput: '',
      addLoading: false,
      addError: '',
      // SVG 截图
      svgModalVisible: false,
      svgModalTitle: '',
      svgModalImage: '',
      svgModalLoading: false,
      // 常用币种快捷选择
      commonSymbols: [
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
        'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT',
        'SUIUSDT', 'OPUSDT', 'ARBUSDT', 'APTUSDT', 'PEPEUSDT'
      ]
    }
  },
  computed: {
    ...mapState({
      navTheme: state => state.app.theme
    }),
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    },
    // 从 localStorage 读取用户自定义的币种列表
    mySymbols: {
      get () {
        try {
          const raw = localStorage.getItem(STORAGE_KEY)
          return raw ? JSON.parse(raw) : []
        } catch {
          return []
        }
      },
      set (list) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
      }
    },
    apiStatusColor () {
      return this.apiConnected ? 'green' : 'red'
    },
    apiStatusText () {
      if (this.dataSource === 'tv' || this.dataSource === 'auto') {
        if (this.tvBridgeConnected) return 'TV桥接 ✓'
        if (this.apiConnected) return '已连接(OCR)'
        return '未连接'
      }
      return this.apiConnected ? this.$t('hamaMarket.connected') : this.$t('hamaMarket.disconnected')
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
          title: '最新价',
          key: 'price_value',
          scopedSlots: { customRender: 'price_value' },
          width: 120,
          align: 'right'
        },
        {
          title: '涨跌幅',
          key: 'change_pct',
          scopedSlots: { customRender: 'change_pct' },
          width: 100,
          align: 'right'
        },
        {
          title: 'HAMA 蜡烛',
          children: [
            { title: 'Open', key: 'hama_open', scopedSlots: { customRender: 'hama_open' }, width: 110, align: 'right' },
            { title: 'Close', key: 'hama_close', scopedSlots: { customRender: 'hama_close' }, width: 110, align: 'right' },
            { title: 'MA', key: 'hama_ma', scopedSlots: { customRender: 'hama_ma' }, width: 110, align: 'right' },
            { title: '颜色', key: 'hama_status_display', scopedSlots: { customRender: 'hama_status_display' }, width: 80, align: 'center' }
          ]
        },
        {
          title: '信号',
          children: [
            { title: '金叉', key: 'cross_up', scopedSlots: { customRender: 'cross_up' }, width: 70, align: 'center' },
            { title: '死叉', key: 'cross_down', scopedSlots: { customRender: 'cross_down' }, width: 70, align: 'center' },
            { title: 'MA趋势', key: 'ma_trend', scopedSlots: { customRender: 'ma_trend' }, width: 80, align: 'center' }
          ]
        },
        {
          title: '布林带',
          children: [
            { title: '上轨', key: 'bb_upper', scopedSlots: { customRender: 'bb_upper' }, width: 110, align: 'right' },
            { title: '中轨', key: 'bb_basis', scopedSlots: { customRender: 'bb_basis' }, width: 110, align: 'right' },
            { title: '下轨', key: 'bb_lower', scopedSlots: { customRender: 'bb_lower' }, width: 110, align: 'right' },
            { title: '带宽', key: 'bb_width', scopedSlots: { customRender: 'bb_width' }, width: 90, align: 'right' },
            { title: '状态', key: 'bb_status', scopedSlots: { customRender: 'bb_status' }, width: 70, align: 'center' }
          ]
        },
        {
          title: this.$t('common.action'),
          key: 'action',
          scopedSlots: { customRender: 'action' },
          width: 140,
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
    // 显示添加币种弹窗
    showAddModal () {
      this.addSymbolInput = ''
      this.addError = ''
      this.addModalVisible = true
    },
    // 添加币种
    async handleAddSymbol () {
      const symbol = (this.addSymbolInput || '').toUpperCase().trim()
      if (!symbol) {
        this.addError = '请输入品种名称'
        return
      }
      this.addError = ''
      this.addLoading = true
      try {
        // 先查询该品种是否可用
        const res = await getHamaTv({ symbol, timeframe: this.tvTimeframe })
        if (!res.success || !res.data) {
          this.addError = `❌ ${symbol} 获取数据失败，请检查品种名是否正确`
          return
        }
        // 获取当前列表
        const current = this.mySymbols
        if (current.includes(symbol)) {
          this.addError = `⚠️ ${symbol} 已在监控列表中`
          return
        }
        // 添加到列表
        current.push(symbol)
        this.mySymbols = current
        this.$message.success(`✅ ${symbol} 已添加`)
        this.addModalVisible = false
        // 重新获取数据
        await this.fetchData()
      } catch (e) {
        this.addError = `❌ 请求失败: ${e.message}`
      } finally {
        this.addLoading = false
      }
    },
    // 移除品种
    removeSymbol (symbol) {
      const current = this.mySymbols.filter(s => s !== symbol)
      this.mySymbols = current
      this.watchlist = this.watchlist.filter(w => w.symbol !== symbol)
      this.$message.success(`已移除 ${symbol}`)
    },
    // 显示 HAMA 图表 SVG
    async showChartSvg (record) {
      const symbol = record.symbol || record
      this.svgModalTitle = `${symbol} HAMA 图表`
      this.svgModalVisible = true
      this.svgModalLoading = true
      this.svgModalImage = ''
      try {
        const res = await getHamaChartSvg({ symbol, timeframe: this.tvTimeframe })
        if (res.success && res.data && res.data.chart_svg_base64) {
          this.svgModalImage = res.data.chart_svg_base64
        } else {
          this.$message.error('生成图表失败')
          this.svgModalVisible = false
        }
      } catch (e) {
        this.$message.error('图表请求异常: ' + e.message)
        this.svgModalVisible = false
      } finally {
        this.svgModalLoading = false
      }
    },
    // 切换数据源
    handleDataSourceChange (val) {
      this.dataSource = val
      this.fetchData()
    },
    // 判断当前应使用 TV 还是 OCR
    shouldUseTv () {
      if (this.dataSource === 'tv') return true
      if (this.dataSource === 'auto') return this.tvBridgeConnected
      return false
    },
    // 主数据获取
    async fetchData () {
      const symbols = this.mySymbols
      if (!symbols || symbols.length === 0) {
        this.watchlist = []
        this.apiConnected = true
        this.loading = false
        return
      }
      this.loading = true
      try {
        // 先检查 TV-Bridge 状态
        try {
          const tvHealth = await getTvBridgeHealth()
          this.tvBridgeConnected = tvHealth.data && tvHealth.data.bridge_connected && tvHealth.data.tv_connected
        } catch (e) {
          this.tvBridgeConnected = false
        }
        if (this.shouldUseTv()) {
          await this.fetchDataFromTv(symbols)
        } else {
          await this.fetchDataFromOcr(symbols)
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        this.$message.error(this.$t('hamaMarket.fetchFailed'))
        this.apiConnected = false
      } finally {
        this.loading = false
      }
    },
    // 从 TV-Bridge 获取数据
    async fetchDataFromTv (symbols) {
      const batchRes = await batchGetHamaTv({
        symbols,
        timeframe: this.tvTimeframe
      })
      this.apiConnected = true
      if (batchRes.success && batchRes.data) {
        const results = batchRes.data.results || {}
        this.watchlist = symbols.map(symbol => {
          const tv = results[symbol]
          if (tv && tv.success) {
            return {
              symbol: tv.symbol,
              price: tv.price,
              hama_tv: tv
            }
          }
          return { symbol, hama_tv: null }
        })
      }
    },
    // 从 OCR 获取数据（原逻辑）
    async fetchDataFromOcr (symbols) {
      // OCR 模式降级：对每个品种单独查询
      const results = []
      for (const symbol of symbols) {
        try {
          const res = await getHamaTv({ symbol, timeframe: this.tvTimeframe })
          if (res.success && res.data) {
            results.push({
              symbol: res.data.symbol || symbol,
              hama_tv: res.data
            })
          } else {
            results.push({ symbol, hama_tv: null })
          }
        } catch {
          results.push({ symbol, hama_tv: null })
        }
      }
      this.watchlist = results
      this.apiConnected = true
    },
    formatPrice (price) {
      if (!price && price !== 0) return '-'
      const numPrice = parseFloat(price)
      if (numPrice < 0.0001) return numPrice.toFixed(8)
      if (numPrice < 0.01) return numPrice.toFixed(6)
      if (numPrice < 1) return numPrice.toFixed(4)
      if (numPrice < 1000) return numPrice.toFixed(2)
      return numPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
    align-items: flex-start;

    .header-left {
      flex: 1;
    }

    .title-row {
      display: flex;
      align-items: center;
    }

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

  .mono-number {
    font-family: 'Roboto Mono', 'Courier New', monospace;
    font-size: 13px;
  }
}
</style>
