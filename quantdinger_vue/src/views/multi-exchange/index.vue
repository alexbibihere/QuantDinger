<template>
  <div class="multi-exchange-container">
    <!-- 页面标题 -->
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>{{ $t('multiExchange.title') }}</h2>
          <p class="subtitle">{{ $t('multiExchange.subtitle') }}</p>
        </div>
        <a-space>
          <a-select
            v-model="marketType"
            style="width: 120px"
            @change="handleMarketChange"
          >
            <a-select-option value="futures">{{ $t('multiExchange.futures') }}</a-select-option>
            <a-select-option value="spot">{{ $t('multiExchange.spot') }}</a-select-option>
          </a-select>
          <a-button type="primary" @click="fetchData" :loading="loading">
            <a-icon type="reload" />
            {{ $t('multiExchange.refresh') }}
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 统计信息 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('multiExchange.binanceCount')"
            :value="binanceData.length"
            prefix="📊"
          >
            <template #suffix>
              <span class="exchange-suffix">Binance</span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('multiExchange.okxCount')"
            :value="okxData.length"
            prefix="📈"
          >
            <template #suffix>
              <span class="exchange-suffix">OKX</span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('multiExchange.commonSymbols')"
            :value="analysis.total_common_symbols"
            prefix="🔗"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            :title="$t('multiExchange.updateTime')"
            :value="updateTime"
            prefix="🕒"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 交易所涨幅榜对比 -->
    <a-row :gutter="16" class="tables-row">
      <!-- Binance 涨幅榜 -->
      <a-col :span="12">
        <a-card
          :bordered="false"
          :title="`${$t('multiExchange.binanceTitle')} - ${$t('multiExchange.top10')}`"
          class="exchange-card binance-card"
        >
          <a-table
            :columns="columns"
            :data-source="binanceData"
            :loading="loading"
            :pagination="false"
            size="middle"
            :row-key="(record) => record.symbol"
            :scroll="{ y: 500 }"
          >
            <template #symbol="text">
              <a-tag color="blue">{{ text }}</a-tag>
            </template>
            <template #price_change_percent="text">
              <span :class="text >= 0 ? 'price-up' : 'price-down'">
                <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
                {{ text.toFixed(2) }}%
              </span>
            </template>
            <template #price="text">
              ${{ text.toFixed(4) }}
            </template>
            <template #volume="text">
              {{ formatNumber(text) }}
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- OKX 涨幅榜 -->
      <a-col :span="12">
        <a-card
          :bordered="false"
          :title="`${$t('multiExchange.okxTitle')} - ${$t('multiExchange.top10')}`"
          class="exchange-card okx-card"
        >
          <a-table
            :columns="columns"
            :data-source="okxData"
            :loading="loading"
            :pagination="false"
            size="middle"
            :row-key="(record) => record.symbol"
            :scroll="{ y: 500 }"
          >
            <template #symbol="text">
              <a-tag color="green">{{ text }}</a-tag>
            </template>
            <template #price_change_percent="text">
              <span :class="text >= 0 ? 'price-up' : 'price-down'">
                <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
                {{ text.toFixed(2) }}%
              </span>
            </template>
            <template #price="text">
              ${{ text.toFixed(4) }}
            </template>
            <template #volume="text">
              {{ formatNumber(text) }}
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 对比分析 -->
    <a-card :bordered="false" :title="$t('multiExchange.analysis')" class="analysis-card">
      <a-row :gutter="16">
        <a-col :span="8">
          <div class="analysis-item">
            <h4>{{ $t('multiExchange.binanceOnly') }}</h4>
            <a-tag v-for="symbol in analysis.binance_only" :key="symbol" color="blue">
              {{ symbol }}
            </a-tag>
            <a-empty v-if="analysis.binance_only.length === 0" :description="$t('multiExchange.noData')" />
          </div>
        </a-col>
        <a-col :span="8">
          <div class="analysis-item">
            <h4>{{ $t('multiExchange.okxOnly') }}</h4>
            <a-tag v-for="symbol in analysis.okx_only" :key="symbol" color="green">
              {{ symbol }}
            </a-tag>
            <a-empty v-if="analysis.okx_only.length === 0" :description="$t('multiExchange.noData')" />
          </div>
        </a-col>
        <a-col :span="8">
          <div class="analysis-item">
            <h4>{{ $t('multiExchange.priceDifferences') }}</h4>
            <div v-if="analysis.price_differences.length > 0">
              <div v-for="diff in analysis.price_differences" :key="diff.symbol" class="diff-item">
                <a-tag color="orange">{{ diff.symbol }}</a-tag>
                <span class="diff-value">差: {{ diff.diff.toFixed(2) }}%</span>
              </div>
            </div>
            <a-empty v-else :description="$t('multiExchange.noCommonSymbols')" />
          </div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script>
import { compareExchanges } from '@/api/multiExchange'
import moment from 'moment'

export default {
  name: 'MultiExchange',
  data () {
    return {
      marketType: 'futures',
      loading: false,
      binanceData: [],
      okxData: [],
      analysis: {
        total_common_symbols: 0,
        binance_only: [],
        okx_only: [],
        price_differences: []
      },
      updateTime: '',
      columns: [
        {
          title: this.$t('multiExchange.rank'),
          width: 60,
          align: 'center',
          customRender: (text, record, index) => index + 1
        },
        {
          title: this.$t('multiExchange.symbol'),
          dataIndex: 'symbol',
          width: 120,
          slots: { customRender: 'symbol' }
        },
        {
          title: this.$t('multiExchange.price'),
          dataIndex: 'price',
          width: 100,
          slots: { customRender: 'price' }
        },
        {
          title: this.$t('multiExchange.change24h'),
          dataIndex: 'price_change_percent',
          width: 100,
          slots: { customRender: 'price_change_percent' }
        },
        {
          title: this.$t('multiExchange.volume24h'),
          dataIndex: 'volume',
          slots: { customRender: 'volume' }
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
        const response = await compareExchanges({
          market: this.marketType,
          limit: 10
        })

        if (response.code === 1) {
          const data = response.data
          this.binanceData = data.exchanges.binance.top_gainers || []
          this.okxData = data.exchanges.okx.top_gainers || []
          this.analysis = data.analysis || {}
          this.updateTime = moment().format('HH:mm:ss')

          this.$message.success(this.$t('multiExchange.fetchSuccess'))
        } else {
          this.$message.error(response.msg || this.$t('multiExchange.fetchError'))
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        this.$message.error(this.$t('multiExchange.fetchError'))
      } finally {
        this.loading = false
      }
    },
    handleMarketChange (value) {
      this.marketType = value
      this.fetchData()
    },
    formatNumber (num) {
      if (num >= 1000000000) {
        return (num / 1000000000).toFixed(2) + 'B'
      } else if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K'
      }
      return num.toFixed(2)
    }
  }
}
</script>

<style lang="scss" scoped>
.multi-exchange-container {
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

    .exchange-suffix {
      font-size: 14px;
      color: #8c8c8c;
      margin-left: 8px;
    }
  }

  .tables-row {
    margin-bottom: 20px;

    .exchange-card {
      ::v-deep .ant-card-head {
        background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
        font-weight: 600;
        font-size: 16px;
      }

      &.binance-card ::v-deep .ant-card-head {
        background: linear-gradient(90deg, #fff7ed 0%, #ffedd5 100%);
      }

      &.okx-card ::v-deep .ant-card-head {
        background: linear-gradient(90deg, #f0fdf4 0%, #dcfce7 100%);
      }
    }

    .price-up {
      color: #f5222d;
      font-weight: 600;
    }

    .price-down {
      color: #52c41a;
      font-weight: 600;
    }
  }

  .analysis-card {
    .analysis-item {
      h4 {
        margin-bottom: 12px;
        color: #262626;
        font-weight: 600;
      }

      .ant-tag {
        margin: 4px;
      }

      .diff-item {
        margin-bottom: 8px;

        .diff-value {
          margin-left: 8px;
          color: #fa8c16;
          font-weight: 500;
        }
      }
    }
  }
}
</style>
