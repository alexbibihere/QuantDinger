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
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            {{ $t('common.refresh') }}
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 默认币种 -->
    <a-card
      :bordered="false"
      title="默认币种"
      class="panel-card"
      style="margin-bottom: 16px;"
    >
      <a-table
        :columns="gainerColumns"
        :data-source="defaultCoinsData"
        :loading="loading"
        :pagination="false"
        rowKey="symbol"
        size="small"
        :expandedRowKeys="expandedRowKeys"
        @expand="handleTableExpand"
      >
        <!-- 展开行 - 图表截图 -->
        <template slot="expandedRowRender" slot-scope="record">
          <div class="screenshot-container">
            <div class="screenshot-header">
              <span class="screenshot-title">{{ record.symbol }} - 15分钟图表</span>
              <a-button
                type="link"
                size="small"
                :loading="record.screenshotLoading"
                @click="refreshScreenshot(record)"
              >
                <a-icon type="reload" />
                刷新截图
              </a-button>
            </div>
            <div class="screenshot-wrapper">
              <a-spin :spinning="record.screenshotLoading" tip="正在加载截图...">
                <img
                  v-if="record.screenshotData"
                  :src="'data:image/png;base64,' + record.screenshotData"
                  :alt="record.symbol + ' chart'"
                  class="screenshot-image"
                />
                <a-empty
                  v-else
                  description="点击展开行加载图表截图"
                  :image="Empty.PRESENTED_IMAGE_SIMPLE"
                />
              </a-spin>
            </div>
          </div>
        </template>
        <!-- 排名 -->
        <template slot="rank">
          <div class="rank-badge rank-default">
            ★
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
            {{ formatPrice(text, record.symbol) }}
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

    <!-- 涨幅榜 -->
    <a-card
      :bordered="false"
      :title="`${$t('tradingviewScanner.topGainers')} - 涨幅前10`"
      class="panel-card"
    >
          <a-table
            :columns="gainerColumns"
            :data-source="gainerData"
            :loading="loading"
            :pagination="false"
            :scroll="{ y: 600 }"
            rowKey="symbol"
            size="small"
            :expandedRowKeys="expandedRowKeys"
            @expand="handleTableExpand"
          >
            <!-- 展开行 - 图表截图 -->
            <template slot="expandedRowRender" slot-scope="record">
              <div class="screenshot-container">
                <div class="screenshot-header">
                  <span class="screenshot-title">{{ record.symbol }} - 15分钟图表</span>
                  <a-button
                    type="link"
                    size="small"
                    :loading="record.screenshotLoading"
                    @click="refreshScreenshot(record)"
                  >
                    <a-icon type="reload" />
                    刷新截图
                  </a-button>
                </div>
                <div class="screenshot-wrapper">
                  <a-spin :spinning="record.screenshotLoading" tip="正在加载截图...">
                    <img
                      v-if="record.screenshotData"
                      :src="'data:image/png;base64,' + record.screenshotData"
                      :alt="record.symbol + ' chart'"
                      class="screenshot-image"
                    />
                    <a-empty
                      v-else
                      description="点击展开行加载图表截图"
                      :image="Empty.PRESENTED_IMAGE_SIMPLE"
                    />
                  </a-spin>
                </div>
              </div>
            </template>
            <!-- 排名 -->
            <template slot="rank" slot-scope="text, record, index">
              <div class="rank-badge rank-gainer" :class="getRankClass(index + 1)">
                {{ index + 1 }}
              </div>
            </template>

            <!-- 币种 -->
            <template slot="symbol" slot-scope="text">
              <a-tag color="green">{{ text }}</a-tag>
            </template>

            <!-- 价格 -->
            <template slot="price" slot-scope="text, record">
              <span
                class="price-value"
                :class="{ 'price-flash': isPriceJustUpdated(record.symbol) }"
              >
                {{ formatPrice(text, record.symbol) }}
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
import { getTopGainers, getChartScreenshot } from '@/api/tradingviewScanner'
import realtimePriceMixin from '@/mixins/realtimePrice'
import { Empty } from 'ant-design-vue'

export default {
  name: 'TradingViewScanner',
  mixins: [realtimePriceMixin],
  data () {
    return {
      loading: false,
      gainerData: [], // 涨幅榜数据（涨幅前10）
      defaultCoinsData: [ // 默认币种数据
        { symbol: 'BTCUSDT', price: 0, change_percentage: 0, volume: 0 },
        { symbol: 'ETHUSDT', price: 0, change_percentage: 0, volume: 0 }
      ],
      sseConnected: false,
      timer: null,
      expandedRowKeys: [], // 展开的行
      Empty
    }
  },
  computed: {
    sseStatusColor () {
      return this.sseConnected ? 'green' : 'red'
    },
    sseStatusText () {
      return this.sseConnected ? this.$t('tradingviewScanner.connected') : this.$t('tradingviewScanner.disconnected')
    },
    gainerColumns () {
      return [
        {
          title: '排名',
          scopedSlots: { customRender: 'rank' },
          width: 70,
          align: 'center'
        },
        {
          title: '币种',
          dataIndex: 'symbol',
          key: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 120
        },
        {
          title: '价格',
          dataIndex: 'price',
          key: 'price',
          scopedSlots: { customRender: 'price' },
          width: 100,
          align: 'right'
        },
        {
          title: '涨跌幅',
          dataIndex: 'change_percentage',
          key: 'change_percentage',
          scopedSlots: { customRender: 'change_percentage' },
          width: 100,
          align: 'center'
        },
        {
          title: '成交量',
          dataIndex: 'volume',
          key: 'volume',
          scopedSlots: { customRender: 'volume' },
          width: 100,
          align: 'right'
        },
        {
          title: '操作',
          key: 'action',
          scopedSlots: { customRender: 'action' },
          width: 100,
          align: 'center'
        }
      ]
    }
  },
  mounted () {
    this.fetchData()
    // 每5分钟自动刷新
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
    async fetchData () {
      this.loading = true
      try {
        // 获取涨幅榜数据
        const gainerRes = await getTopGainers({ limit: 10 })

        // 处理涨幅榜数据（按涨跌幅排序）
        if (gainerRes.success || gainerRes.data) {
          const gainers = gainerRes.data || []
          console.log('涨幅榜原始数据:', gainers)
          // 按涨跌幅降序排序，取前10
          this.gainerData = gainers
            .sort((a, b) => (b.change_percentage || 0) - (a.change_percentage || 0))
            .slice(0, 10)
          console.log('涨幅榜处理后数据:', this.gainerData)
        } else {
          console.log('涨幅榜响应失败:', gainerRes)
          this.gainerData = []
        }

        // 初始化实时价格订阅
        this.initRealtimePrice()

        this.$message.success('数据刷新成功')
      } catch (error) {
        console.error('获取数据失败:', error)
        this.$message.error('获取数据失败')
      } finally {
        this.loading = false
      }
    },

    initRealtimePrice () {
      // 订阅默认币种和涨幅榜币种的实时价格
      const defaultSymbols = this.defaultCoinsData.map(d => d.symbol)
      const gainerSymbols = this.gainerData.map(d => d.symbol)
      const allSymbols = [...defaultSymbols, ...gainerSymbols]

      // 去重
      const uniqueSymbols = [...new Set(allSymbols)]

      // 调用mixin方法订阅实时价格
      if (this.subscribeRealtimePrices) {
        this.subscribeRealtimePrices(uniqueSymbols)
      }
    },

    formatPrice (price, symbol) {
      if (!price) return '-'
      // 根据币种价格范围调整小数位数
      const numPrice = parseFloat(price)
      if (numPrice < 0.01) return numPrice.toFixed(6)
      if (numPrice < 1) return numPrice.toFixed(4)
      return numPrice.toFixed(2)
    },

    formatVolume (volume) {
      if (!volume) return '-'
      const num = parseFloat(volume)
      if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B'
      if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M'
      if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K'
      return num.toFixed(2)
    },

    getRankClass (rank) {
      if (rank === 1) return 'rank-1'
      if (rank === 2) return 'rank-2'
      if (rank === 3) return 'rank-3'
      return 'rank-normal'
    },

    getTradingViewUrl (symbol) {
      return `https://cn.tradingview.com/chart/?symbol=BINANCE:${symbol}`
    },

    // 处理表格展开/收起
    async handleTableExpand (expanded, record) {
      if (expanded) {
        // 展开行时加载截图
        this.expandedRowKeys = [record.symbol]
        await this.loadScreenshot(record)
      } else {
        // 收起行时清空展开的行
        this.expandedRowKeys = []
      }
    },

    // 加载图表截图
    async loadScreenshot (record) {
      // 如果已经有截图数据,不再重复加载
      if (record.screenshotData) {
        return
      }

      this.$set(record, 'screenshotLoading', true)

      try {
        const res = await getChartScreenshot({
          symbol: record.symbol,
          interval: '15m'
        })

        if (res.success && res.image_base64) {
          this.$set(record, 'screenshotData', res.image_base64)
          this.$message.success(`${record.symbol} 截图加载成功`)
        } else {
          this.$message.error(`${record.symbol} 截图加载失败`)
        }
      } catch (error) {
        console.error('加载截图失败:', error)
        this.$message.error(`${record.symbol} 截图加载失败`)
      } finally {
        this.$set(record, 'screenshotLoading', false)
      }
    },

    // 刷新截图
    async refreshScreenshot (record) {
      // 清空现有截图数据,重新加载
      this.$set(record, 'screenshotData', null)
      await this.loadScreenshot(record)
    },

    // 实时价格相关方法（从mixin继承）
    getRealtimeChangeClass (symbol, change) {
      const rtChange = this.getRealtimeChange(symbol)
      const value = rtChange !== null ? rtChange : change

      if (value > 0) return 'change-up'
      if (value < 0) return 'change-down'
      return 'change-neutral'
    },

    getRealtimeChangeText (symbol, change) {
      const rtChange = this.getRealtimeChange(symbol)
      const value = rtChange !== null ? rtChange : change
      return (value > 0 ? '+' : '') + value.toFixed(2) + '%'
    }
  }
}
</script>

<style lang="less" scoped>
.tradingview-scanner-container {
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

  .panel-card {
    margin-bottom: 16px;

    ::v-deep .ant-card-head {
      background: #fafafa;
    }
  }

  // 排名徽章
  .rank-badge {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 14px;
    background: #d9d9d9;
    color: #5a5a5a;

    &.rank-1 {
      background: linear-gradient(135deg, #ffd700, #ffed4e);
      color: #8b5a00;
      box-shadow: 0 2px 4px rgba(255, 215, 0, 0.3);
    }

    &.rank-2 {
      background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
      color: #5a5a5a;
      box-shadow: 0 2px 4px rgba(192, 192, 192, 0.3);
    }

    &.rank-3 {
      background: linear-gradient(135deg, #cd7f32, #e5a158);
      color: #5a3a00;
      box-shadow: 0 2px 4px rgba(205, 127, 50, 0.3);
    }

    &.rank-gainer {
      &.rank-1 {
        background: linear-gradient(135deg, #ff4d4f, #ff7875);
        color: white;
      }
    }
  }

  // 价格样式
  .price-value {
    font-weight: 500;
    font-family: 'Roboto Mono', monospace;

    &.price-flash {
      animation: priceFlash 0.5s ease-in-out;
    }
  }

  @keyframes priceFlash {
    0% { background-color: transparent; }
    50% { background-color: rgba(24, 144, 255, 0.2); }
    100% { background-color: transparent; }
  }

  // 涨跌幅样式
  .change-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
    font-family: 'Roboto Mono', monospace;

    &.change-up {
      color: #3f8600;
      background: rgba(63, 134, 0, 0.1);
    }

    &.change-down {
      color: #cf1322;
      background: rgba(207, 19, 34, 0.1);
    }

    &.change-neutral {
      color: #8c8c8c;
      background: rgba(140, 140, 140, 0.1);
    }
  }

  // 截图容器
  .screenshot-container {
    padding: 16px;
    background: #fafafa;
    border-radius: 4px;

    .screenshot-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #e8e8e8;

      .screenshot-title {
        font-size: 14px;
        font-weight: 500;
        color: rgba(0, 0, 0, 0.85);
      }
    }

    .screenshot-wrapper {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;

      .screenshot-image {
        max-width: 100%;
        height: auto;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      }
    }
  }
}
</style>
