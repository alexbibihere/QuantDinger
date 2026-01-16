<template>
  <div class="gainer-history-container">
    <a-card :bordered="false" class="header-card">
      <div class="page-header">
        <div>
          <h2>{{ $t('menu.gainerHistory') || '涨幅榜历史' }}</h2>
          <p class="subtitle">查看每天涨幅榜数据和币种出现统计</p>
        </div>
        <a-space>
          <a-select v-model="days" style="width: 120px" @change="loadData">
            <a-select-option :value="3">最近3天</a-select-option>
            <a-select-option :value="7">最近7天</a-select-option>
            <a-select-option :value="14">最近14天</a-select-option>
            <a-select-option :value="30">最近30天</a-select-option>
          </a-select>
          <a-button type="primary" @click="loadData" :loading="loading">
            <a-icon type="reload" />刷新
          </a-button>
        </a-space>
      </div>
    </a-card>

    <a-row :gutter="16" class="stats-row" v-if="statsOverview">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="记录天数" :value="statsOverview.recordDays" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="涉及币种" :value="statsOverview.totalSymbols" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="最高出现次数" :value="statsOverview.maxCount" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="平均出现次数" :value="statsOverview.avgCount" :precision="1" />
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" title="出现次数排行榜" class="ranking-card">
      <a-list
        :data-source="rankingList"
        :loading="loading"
        item-layout="horizontal"
      >
        <template slot="renderItem" slot-scope="item, index">
          <a-list-item>
            <div class="ranking-item" slot="title">
              <div class="rank-badge" :class="'rank-' + (index + 1)">
                {{ index + 1 }}
              </div>
              <div class="symbol-info">
                <span class="symbol">{{ item.symbol }}</span>
                <a-progress
                  :percent="getPercentage(item.count, rankingList[0].count)"
                  :show-info="false"
                  :stroke-color="getProgressColor(item.count)"
                  size="small"
                />
              </div>
              <div class="count-info">
                <a-tag :color="getCountTagColor(item.count)">
                  出现 {{ item.count }} 次
                </a-tag>
              </div>
            </div>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card :bordered="false" title="每日详情" class="daily-card">
      <a-collapse v-model="activeKeys" :bordered="false">
        <a-collapse-panel
          v-for="day in dailyData"
          :key="day.date"
          :header="getDayHeader(day)"
        >
          <div class="day-stats">
            <a-tag color="blue">共 {{ day.symbols.length }} 个币种</a-tag>
          </div>
          <a-table
            :columns="dayColumns"
            :data-source="day.symbolDetails"
            :pagination="false"
            size="small"
            :row-key="record => record.symbol"
          >
            <template slot="count" slot-scope="text">
              <a-tag :color="getCountTagColor(text)">{{ text }}次</a-tag>
            </template>
            <template slot="changePercentage" slot-scope="text">
              <span v-if="text !== null && text !== undefined" :class="getChangeClass(text)">
                <a-icon :type="text >= 0 ? 'arrow-up' : 'arrow-down'" />
                {{ (text > 0 ? '+' : '') + text.toFixed(2) + '%' }}
              </span>
              <span v-else class="text-muted">-</span>
            </template>
            <template slot="price" slot-scope="text">
              <span v-if="text !== null && text !== undefined" class="price-value">
                {{ formatPrice(text) }}
              </span>
              <span v-else class="text-muted">-</span>
            </template>
          </a-table>
        </a-collapse-panel>
      </a-collapse>
    </a-card>
  </div>
</template>

<script>
import { getGainerHistory } from '@/api/gainerStats'

export default {
  name: 'GainerHistory',
  data () {
    return {
      days: 7,
      loading: false,
      dailyData: [],
      rankingList: [],
      statsOverview: null,
      activeKeys: [],
      dayColumns: [
        {
          title: '币种',
          dataIndex: 'symbol',
          key: 'symbol',
          width: 120
        },
        {
          title: '出现次数',
          dataIndex: 'count',
          key: 'count',
          width: 100,
          scopedSlots: { customRender: 'count' }
        },
        {
          title: '当天排名',
          dataIndex: 'rank',
          key: 'rank',
          width: 100
        },
        {
          title: '当天涨幅',
          dataIndex: 'changePercentage',
          key: 'changePercentage',
          scopedSlots: { customRender: 'changePercentage' }
        },
        {
          title: '当天价格',
          dataIndex: 'price',
          key: 'price',
          scopedSlots: { customRender: 'price' }
        }
      ]
    }
  },
  mounted () {
    this.loadData()
  },
  methods: {
    async loadData () {
      this.loading = true
      try {
        const response = await getGainerHistory({ days: this.days })
        if (response.code === 1) {
          this.processData(response.data)
        } else {
          this.$message.error('加载失败：' + response.msg)
        }
      } catch (error) {
        console.error('加载涨幅榜历史失败:', error)
        this.$message.error('加载失败')
      } finally {
        this.loading = false
      }
    },
    processData (data) {
      this.dailyData = data.daily || []
      this.rankingList = (data.ranking || []).map(item => ({
        symbol: item.symbol,
        count: item.total_count
      }))
      if (data.ranking && data.ranking.length > 0) {
        const totalCounts = data.ranking.map(r => r.total_count)
        this.statsOverview = {
          recordDays: data.daily ? data.daily.length : 0,
          totalSymbols: data.ranking.length,
          maxCount: Math.max(...totalCounts),
          avgCount: totalCounts.reduce((a, b) => a + b, 0) / totalCounts.length
        }
      }
      if (this.dailyData.length > 0) {
        this.activeKeys = [this.dailyData[0].date]
      }
    },
    getDayHeader (day) {
      return day.date + ' - 共 ' + day.symbols.length + ' 个币种'
    },
    getPercentage (value, max) {
      return max > 0 ? Math.round((value / max) * 100) : 0
    },
    getCountTagColor (count) {
      if (count >= 5) return 'red'
      if (count >= 3) return 'orange'
      if (count >= 2) return 'blue'
      return 'green'
    },
    getProgressColor (count) {
      if (count >= 5) return '#f5222d'
      if (count >= 3) return '#fa8c16'
      if (count >= 2) return '#1890ff'
      return '#52c41a'
    },
    getChangeClass (change) {
      if (change > 0) return 'change-up'
      if (change < 0) return 'change-down'
      return 'change-neutral'
    },
    formatPrice (price) {
      if (!price) return '-'
      const numPrice = parseFloat(price)
      if (numPrice < 0.01) return numPrice.toFixed(6)
      if (numPrice < 1) return numPrice.toFixed(4)
      return numPrice.toFixed(2)
    }
  }
}
</script>

<style lang="less" scoped>
.gainer-history-container {
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

  .stats-row {
    margin-bottom: 16px;
  }

  .ranking-card {
    margin-bottom: 16px;

    .ranking-item {
      display: flex;
      align-items: center;
      width: 100%;
      gap: 12px;

      .rank-badge {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        background: #d9d9d9;

        &.rank-1 {
          background: linear-gradient(135deg, #ffd700, #ffed4e);
          color: #8b5a00;
        }

        &.rank-2 {
          background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
          color: #5a5a5a;
        }

        &.rank-3 {
          background: linear-gradient(135deg, #cd7f32, #e5a158);
          color: #5a3a00;
        }
      }

      .symbol-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;

        .symbol {
          font-weight: 500;
          font-size: 14px;
        }
      }

      .count-info {
        min-width: 100px;
        text-align: right;
      }
    }
  }

  .daily-card {
    margin-bottom: 16px;

    .day-stats {
      margin-bottom: 12px;
    }
  }

  // 涨跌幅样式
  .change-up {
    color: #3f8600;
    font-weight: 500;
  }

  .change-down {
    color: #cf1322;
    font-weight: 500;
  }

  .change-neutral {
    color: #8c8c8c;
  }

  .price-value {
    font-family: 'Roboto Mono', monospace;
    font-weight: 500;
  }

  .text-muted {
    color: #8c8c8c;
  }
}
</style>
