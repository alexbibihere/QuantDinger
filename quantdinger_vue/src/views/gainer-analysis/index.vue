<template>
  <div class="gainer-analysis-page" :class="{ 'theme-dark': isDarkTheme }">
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">
          <a-icon type="rise" />
          <span>{{ $t('gainerAnalysis.title') }}</span>
        </h2>
        <p class="page-desc">{{ $t('gainerAnalysis.description') }}</p>
      </div>

      <div class="header-actions">
        <a-select
          v-model="marketType"
          style="width: 120px; margin-right: 12px;"
          @change="handleMarketChange"
        >
          <a-select-option value="spot">{{ $t('gainerAnalysis.market.spot') }}</a-select-option>
          <a-select-option value="futures">{{ $t('gainerAnalysis.market.futures') }}</a-select-option>
        </a-select>

        <a-button
          type="primary"
          icon="reload"
          :loading="loading"
          @click="handleRefresh"
        >
          {{ $t('common.refresh') }}
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            :title="$t('gainerAnalysis.stats.totalSymbols')"
            :value="statistics.total"
            suffix=""
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            :title="$t('gainerAnalysis.stats.avgChange')"
            :value="statistics.avgChange"
            suffix="%"
            :precision="2"
            :value-style="{ color: statistics.avgChange >= 0 ? '#3f8600' : '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            :title="$t('gainerAnalysis.stats.metCriteria')"
            :value="statistics.metCriteria"
            suffix=""
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            :title="$t('gainerAnalysis.stats.strongSignals')"
            :value="statistics.strongSignals"
            suffix=""
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 币种列表 -->
    <a-card
      class="table-card"
      :bordered="false"
      :title="$t('gainerAnalysis.tableTitle')"
    >
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200 }"
        rowKey="symbol"
        class="gainer-table"
      >
        <!-- 排名 -->
        <template slot="rank" slot-scope="text, record, index">
          <div class="rank-badge" :class="getRankClass(index + 1)">
            {{ index + 1 }}
          </div>
        </template>

        <!-- 币种 -->
        <template slot="symbol" slot-scope="text, record">
          <div class="symbol-cell">
            <div class="symbol-name">{{ record.base_asset }}</div>
            <div class="symbol-pair">{{ text }}</div>
          </div>
        </template>

        <!-- 价格 -->
        <template slot="price" slot-scope="text">
          <span class="price-value">${{ formatPrice(text) }}</span>
        </template>

        <!-- 涨跌幅 -->
        <template slot="changePercent" slot-scope="text">
          <span
            class="change-badge"
            :class="text >= 0 ? 'positive' : 'negative'"
          >
            <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
            {{ text.toFixed(2) }}%
          </span>
        </template>

        <!-- HAMA 分析结果 -->
        <template slot="hamaAnalysis" slot-scope="text, record">
          <div class="hama-analysis">
            <!-- 趋势 -->
            <div class="trend-badge" :class="record.hama_analysis.trend">
              <a-icon :type="getTrendIcon(record.hama_analysis.trend)" />
              {{ getTrendText(record.hama_analysis.trend) }}
            </div>

            <!-- 信号 -->
            <div class="recommendation-badge" :class="record.hama_analysis.recommendation.toLowerCase()">
              {{ getRecommendationText(record.hama_analysis.recommendation) }}
            </div>

            <!-- 置信度 -->
            <div class="confidence-bar">
              <a-progress
                :percent="record.hama_analysis.confidence * 100"
                :show-info="false"
                :stroke-color="getConfidenceColor(record.hama_analysis.confidence)"
                size="small"
              />
            </div>
          </div>
        </template>

        <!-- 条件判断 -->
        <template slot="conditions" slot-scope="text, record">
          <div class="conditions-tags">
            <a-tag
              v-if="record.conditions.meets_buy_criteria"
              color="green"
              class="condition-tag"
            >
              <a-icon type="check-circle" />
              {{ $t('gainerAnalysis.conditions.meetsBuy') }}
            </a-tag>
            <a-tag
              v-if="record.conditions.meets_sell_criteria"
              color="red"
              class="condition-tag"
            >
              <a-icon type="close-circle" />
              {{ $t('gainerAnalysis.conditions.meetsSell') }}
            </a-tag>
            <a-tag
              v-if="!record.conditions.meets_buy_criteria && !record.conditions.meets_sell_criteria"
              color="default"
              class="condition-tag"
            >
              <a-icon type="minus-circle" />
              {{ $t('gainerAnalysis.conditions.neutral') }}
            </a-tag>
          </div>
        </template>

        <!-- 操作 -->
        <template slot="action" slot-scope="text, record">
          <a-button
            type="link"
            size="small"
            @click="showDetail(record)"
          >
            <a-icon type="eye" />
            {{ $t('common.detail') }}
          </a-button>
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

    <!-- 详情对话框 -->
    <a-modal
      :visible="detailModalVisible"
      :title="detailModalTitle"
      :width="800"
      @ok="handleModalOk"
      @cancel="detailModalVisible = false"
      :footer="null"
    >
      <div v-if="selectedRecord" class="detail-content">
        <!-- 基本信息 -->
        <a-descriptions title="" :column="2" bordered size="small">
          <a-descriptions-item :label="$t('gainerAnalysis.detail.symbol')">
            {{ selectedRecord.symbol }}
          </a-descriptions-item>
          <a-descriptions-item :label="$t('gainerAnalysis.detail.price')">
            <span class="price-large">${{ formatPrice(selectedRecord.price) }}</span>
          </a-descriptions-item>
          <a-descriptions-item :label="$t('gainerAnalysis.detail.changePercent')">
            <span :class="selectedRecord.price_change_percent >= 0 ? 'positive' : 'negative'">
              {{ selectedRecord.price_change_percent.toFixed(2) }}%
            </span>
          </a-descriptions-item>
          <a-descriptions-item :label="$t('gainerAnalysis.detail.volume')">
            {{ formatVolume(selectedRecord.volume) }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- HAMA 分析 -->
        <a-divider>{{ $t('gainerAnalysis.detail.hamaAnalysis') }}</a-divider>

        <div class="analysis-section">
          <div class="analysis-item">
            <span class="label">{{ $t('gainerAnalysis.detail.trend') }}:</span>
            <a-tag :color="getTrendColor(selectedRecord.hama_analysis.trend)">
              <a-icon :type="getTrendIcon(selectedRecord.hama_analysis.trend)" />
              {{ getTrendText(selectedRecord.hama_analysis.trend) }}
            </a-tag>
          </div>

          <div class="analysis-item">
            <span class="label">{{ $t('gainerAnalysis.detail.recommendation') }}:</span>
            <a-tag :color="getRecommendationColor(selectedRecord.hama_analysis.recommendation)">
              {{ getRecommendationText(selectedRecord.hama_analysis.recommendation) }}
            </a-tag>
          </div>

          <div class="analysis-item">
            <span class="label">{{ $t('gainerAnalysis.detail.confidence') }}:</span>
            <a-progress
              :percent="selectedRecord.hama_analysis.confidence * 100"
              :stroke-color="getConfidenceColor(selectedRecord.hama_analysis.confidence)"
            />
          </div>

          <div class="analysis-item">
            <span class="label">{{ $t('gainerAnalysis.detail.summary') }}:</span>
            <p class="summary-text">{{ selectedRecord.conditions.summary }}</p>
          </div>
        </div>

        <!-- 技术指标 -->
        <a-divider>{{ $t('gainerAnalysis.detail.technicalIndicators') }}</a-divider>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-statistic
              :title="$t('gainerAnalysis.detail.rsi')"
              :value="selectedRecord.hama_analysis.technical_indicators.rsi"
              suffix=""
              :precision="2"
            />
          </a-col>
          <a-col :span="12">
            <a-statistic
              :title="$t('gainerAnalysis.detail.macd')"
              :value="getMacdText(selectedRecord.hama_analysis.technical_indicators.macd)"
            />
          </a-col>
        </a-row>

        <a-row :gutter="16" style="margin-top: 16px;">
          <a-col :span="8">
            <a-statistic
              title="EMA 20"
              :value="selectedRecord.hama_analysis.technical_indicators.ema_20"
              :precision="2"
              suffix="$"
            />
          </a-col>
          <a-col :span="8">
            <a-statistic
              title="EMA 50"
              :value="selectedRecord.hama_analysis.technical_indicators.ema_50"
              :precision="2"
              suffix="$"
            />
          </a-col>
          <a-col :span="8">
            <a-statistic
              :title="$t('gainerAnalysis.detail.supportLevel')"
              :value="selectedRecord.hama_analysis.technical_indicators.support_level"
              :precision="2"
              suffix="$"
              :value-style="{ color: '#52c41a' }"
            />
          </a-col>
        </a-row>

        <!-- 操作按钮 -->
        <div class="detail-actions">
          <a-button
            type="primary"
            :href="getTradingViewUrl(selectedRecord.symbol)"
            target="_blank"
            icon="line-chart"
          >
            {{ $t('gainerAnalysis.detail.viewOnTradingView') }}
          </a-button>
          <a-button
            @click="detailModalVisible = false"
          >
            {{ $t('common.close') }}
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { getTopGainers } from '@/api/gainerAnalysis'
import { baseMixin } from '@/store/app-mixin'

export default {
  name: 'GainerAnalysis',
  mixins: [baseMixin],
  data () {
    return {
      loading: false,
      marketType: 'spot',
      dataSource: [],
      selectedRecord: null,
      detailModalVisible: false,
      detailModalTitle: '',
      statistics: {
        total: 0,
        avgChange: 0,
        metCriteria: 0,
        strongSignals: 0
      },
      pagination: {
        pageSize: 20,
        current: 1,
        total: 0,
        showSizeChanger: false
      },
      columns: [
        {
          title: '#',
          scopedSlots: { customRender: 'rank' },
          width: 60,
          align: 'center'
        },
        {
          title: this.$t('gainerAnalysis.table.symbol'),
          dataIndex: 'symbol',
          scopedSlots: { customRender: 'symbol' },
          width: 150
        },
        {
          title: this.$t('gainerAnalysis.table.price'),
          dataIndex: 'price',
          scopedSlots: { customRender: 'price' },
          width: 120,
          align: 'right'
        },
        {
          title: this.$t('gainerAnalysis.table.changePercent'),
          dataIndex: 'price_change_percent',
          scopedSlots: { customRender: 'changePercent' },
          width: 120,
          align: 'center'
        },
        {
          title: this.$t('gainerAnalysis.table.hamaAnalysis'),
          scopedSlots: { customRender: 'hamaAnalysis' },
          width: 200
        },
        {
          title: this.$t('gainerAnalysis.table.conditions'),
          scopedSlots: { customRender: 'conditions' },
          width: 150
        },
        {
          title: this.$t('common.action'),
          scopedSlots: { customRender: 'action' },
          width: 150,
          fixed: 'right'
        }
      ]
    }
  },
  computed: {
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    }
  },
  mounted () {
    this.loadData()
  },
  methods: {
    async loadData () {
      this.loading = true
      try {
        const res = await getTopGainers({
          limit: 20,
          market: this.marketType
        })

        if (res.code === 1) {
          this.dataSource = res.data.symbols || []
          this.updateStatistics()
          this.pagination.total = this.dataSource.length
        } else {
          this.$message.error(res.msg || this.$t('gainerAnalysis.messages.loadFailed'))
        }
      } catch (error) {
        console.error('Failed to load data:', error)
        this.$message.error(this.$t('gainerAnalysis.messages.loadFailed'))
      } finally {
        this.loading = false
      }
    },

    updateStatistics () {
      const total = this.dataSource.length
      if (total === 0) return

      // 计算平均涨幅
      const avgChange = this.dataSource.reduce((sum, item) => sum + item.price_change_percent, 0) / total

      // 计算满足条件的币种数量
      const metCriteria = this.dataSource.filter(item => item.conditions.meets_buy_criteria || item.conditions.meets_sell_criteria).length

      // 计算强信号数量
      const strongSignals = this.dataSource.filter(item => item.hama_analysis.confidence >= 0.7).length

      this.statistics = {
        total,
        avgChange: avgChange.toFixed(2),
        metCriteria,
        strongSignals
      }
    },

    async handleRefresh () {
      await this.loadData()
      this.$message.success(this.$t('gainerAnalysis.messages.refreshSuccess'))
    },

    handleMarketChange () {
      this.loadData()
    },

    showDetail (record) {
      this.selectedRecord = record
      this.detailModalTitle = `${record.symbol} - ${this.$t('gainerAnalysis.detail.title')}`
      this.detailModalVisible = true
    },

    handleModalOk () {
      this.detailModalVisible = false
    },

    formatPrice (price) {
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(price)
    },

    formatVolume (volume) {
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

    getTrendIcon (trend) {
      const icons = {
        uptrend: 'arrow-up',
        downtrend: 'arrow-down',
        sideways: 'minus'
      }
      return icons[trend] || 'minus'
    },

    getTrendText (trend) {
      const texts = {
        uptrend: '上升趋势',
        downtrend: '下降趋势',
        sideways: '横盘整理'
      }
      return texts[trend] || trend
    },

    getTrendColor (trend) {
      const colors = {
        uptrend: 'green',
        downtrend: 'red',
        sideways: 'default'
      }
      return colors[trend] || 'default'
    },

    getRecommendationText (recommendation) {
      const texts = {
        BUY: '买入',
        SELL: '卖出',
        HOLD: '持有'
      }
      return texts[recommendation] || recommendation
    },

    getRecommendationColor (recommendation) {
      const colors = {
        BUY: 'green',
        SELL: 'red',
        HOLD: 'default'
      }
      return colors[recommendation] || 'default'
    },

    getConfidenceColor (confidence) {
      if (confidence >= 0.8) return '#52c41a'
      if (confidence >= 0.6) return '#1890ff'
      return '#faad14'
    },

    getMacdText (macd) {
      const texts = {
        bullish: '看涨',
        bearish: '看跌',
        neutral: '中性'
      }
      return texts[macd] || macd
    },

    getTradingViewUrl (symbol) {
      // 使用用户提供的 TradingView 链接格式
      return `https://cn.tradingview.com/chart/jvR08dsB/?symbol=BINANCE:${symbol}`
    }
  }
}
</script>

<style lang="less" scoped>
.gainer-analysis-page {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;

    .header-content {
      flex: 1;
      min-width: 300px;

      .page-title {
        margin: 0;
        font-size: 24px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .page-desc {
        margin: 8px 0 0;
        color: rgba(0, 0, 0, 0.45);
        font-size: 14px;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .stats-row {
    margin-bottom: 24px;

    .stat-card {
      .ant-statistic-title {
        font-size: 14px;
      }

      .ant-statistic-content {
        font-size: 20px;
        font-weight: 500;
      }
    }
  }

  .table-card {
    .gainer-table {
      .rank-badge {
        width: 32px;
        height: 32px;
        line-height: 32px;
        text-align: center;
        border-radius: 4px;
        font-weight: bold;

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

      .symbol-cell {
        .symbol-name {
          font-weight: 500;
          font-size: 14px;
        }

        .symbol-pair {
          font-size: 12px;
          color: rgba(0, 0, 0, 0.45);
        }
      }

      .price-value {
        font-weight: 500;
      }

      .change-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 500;

        &.positive {
          background: #f6ffed;
          color: #52c41a;
        }

        &.negative {
          background: #fff1f0;
          color: #ff4d4f;
        }
      }

      .hama-analysis {
        display: flex;
        flex-direction: column;
        gap: 6px;

        .trend-badge {
          display: inline-flex;
          align-items: center;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;

          &.uptrend {
            background: #f6ffed;
            color: #52c41a;
          }

          &.downtrend {
            background: #fff1f0;
            color: #ff4d4f;
          }

          &.sideways {
            background: #f0f0f0;
            color: #666;
          }
        }

        .recommendation-badge {
          display: inline-flex;
          align-items: center;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;

          &.buy {
            background: #f6ffed;
            color: #52c41a;
          }

          &.sell {
            background: #fff1f0;
            color: #ff4d4f;
          }

          &.hold {
            background: #f0f0f0;
            color: #666;
          }
        }

        .confidence-bar {
          max-width: 100px;
        }
      }

      .conditions-tags {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;

        .condition-tag {
          font-size: 12px;
        }
      }
    }
  }

  .detail-content {
    .price-large {
      font-size: 24px;
      font-weight: 500;
    }

    .positive {
      color: #52c41a;
    }

    .negative {
      color: #ff4d4f;
    }

    .analysis-section {
      margin: 16px 0;

      .analysis-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;

        .label {
          font-weight: 500;
          margin-right: 12px;
          min-width: 100px;
        }

        .summary-text {
          margin: 0;
          color: rgba(0, 0, 0, 0.65);
          line-height: 1.5;
        }
      }
    }

    .detail-actions {
      margin-top: 24px;
      text-align: right;
    }
  }
}

.theme-dark {
  .page-desc {
    color: rgba(255, 255, 255, 0.65);
  }

  .symbol-pair {
    color: rgba(255, 255, 255, 0.45) !important;
  }

  .rank-normal {
    background: #2c2c2c !important;
    color: #999 !important;
  }

  .change-badge {
    &.positive {
      background: rgba(82, 196, 26, 0.2) !important;
    }

    &.negative {
      background: rgba(255, 77, 79, 0.2) !important;
    }
  }
}
</style>
