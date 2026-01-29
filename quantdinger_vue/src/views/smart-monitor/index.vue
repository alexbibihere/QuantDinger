<template>
  <div class="smart-monitor-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>
        <a-icon type="thunderbolt" />
        <span>智能监控中心</span>
      </h2>
      <p>实时监控涨幅榜 + 自动检测买卖信号</p>
    </div>

    <!-- 监控状态卡片 -->
    <a-card class="status-card" :bordered="false">
      <template slot="title">
        <span>监控状态</span>
        <a-tag :color="monitorStatus.running ? 'green' : 'red'" style="margin-left: 12px">
          {{ monitorStatus.running ? '运行中' : '已停止' }}
        </a-tag>
      </template>

      <!-- 统计数据 -->
      <a-row :gutter="16">
        <a-col :xs="12" :sm="8" :md="6">
          <a-statistic
            title="监控币种"
            :value="monitorStatus.symbol_count"
            suffix="个"
            prefix="📊"
          />
        </a-col>
        <a-col :xs="12" :sm="8" :md="6">
          <a-statistic
            title="信号数量"
            :value="monitorStatus.total_signals"
            suffix="条"
            prefix="🔔"
          />
        </a-col>
        <a-col :xs="12" :sm="8" :md="6">
          <a-statistic
            title="检查间隔"
            :value="monitorStatus.check_interval"
            suffix="秒"
            prefix="⏱️"
          />
        </a-col>
        <a-col :xs="12" :sm="8" :md="6">
          <a-statistic
            title="冷却时间"
            :value="monitorStatus.signal_cooldown"
            suffix="秒"
            prefix="❄️"
          />
        </a-col>
      </a-row>

      <!-- 控制按钮 -->
      <a-divider />
      <a-space>
        <a-button
          v-if="!monitorStatus.running"
          type="primary"
          icon="play-circle"
          @click="handleStart"
          :loading="loading.start"
        >
          启动监控
        </a-button>
        <a-button
          v-else
          type="danger"
          icon="pause-circle"
          @click="handleStop"
          :loading="loading.stop"
        >
          停止监控
        </a-button>

        <a-button
          icon="plus"
          @click="showAddModal"
        >
          添加币种
        </a-button>

        <a-button
          icon="thunderbolt"
          @click="handleAddTopGainers"
          :loading="loading.addGainers"
        >
          添加涨幅榜TOP20
        </a-button>

        <a-button
          icon="setting"
          @click="showConfigModal"
        >
          配置参数
        </a-button>

        <a-button
          icon="sync"
          @click="refreshData"
          :loading="loading.refresh"
        >
          刷新数据
        </a-button>
      </a-space>
    </a-card>

    <!-- 标签页: 涨幅榜 / 监控币种 / 信号历史 -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-tabs v-model="activeTab">
        <!-- 涨幅榜标签页 -->
        <a-tab-pane key="gainers" tab="📈 涨幅榜TOP20">
          <div class="market-selector" style="margin-bottom: 16px">
            <a-tag color="blue" style="font-size: 14px; padding: 4px 12px">
              永续合约
            </a-tag>
            <a-button
              icon="reload"
              style="margin-left: 12px"
              :loading="loading.gainers"
              @click="fetchGainers"
            >
              刷新涨幅榜
            </a-button>
            <a-button
              type="primary"
              icon="plus"
              style="margin-left: 12px"
              :loading="loading.addAllGainers"
              @click="handleAddAllGainers"
            >
              全部添加到监控
            </a-button>
          </div>

          <a-table
            :columns="gainerColumns"
            :data-source="gainers"
            :loading="loading.gainers"
            :pagination="{ pageSize: 20 }"
            :scroll="{ x: 1200 }"
            rowKey="symbol"
            size="middle"
          >
            <!-- 排名 -->
            <template slot="rank" slot-scope="text, record, index">
              <a-tag :color="getRankColor(index + 1)">{{ index + 1 }}</a-tag>
            </template>

            <!-- 币种 -->
            <template slot="symbol" slot-scope="text">
              <strong>{{ text }}</strong>
            </template>

            <!-- 涨跌幅 -->
            <template slot="priceChangePercent" slot-scope="text">
              <span :style="{ color: text >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }">
                {{ text >= 0 ? '+' : '' }}{{ text?.toFixed(2) }}%
              </span>
            </template>

            <!-- HAMA状态 -->
            <template slot="hamaStatus" slot-scope="text, record">
              <span v-if="monitoredSymbols.includes(record.symbol)" style="color: #999; font-size: 12px">
                <a-tag v-if="record.hama_signal === 'UP'" color="green">涨信号</a-tag>
                <a-tag v-else-if="record.hama_signal === 'DOWN'" color="red">跌信号</a-tag>
                <a-tag v-else color="default">观望</a-tag>
              </span>
              <a-tag v-else color="default">未监控</a-tag>
            </template>

            <!-- 操作 -->
            <template slot="action" slot-scope="text, record">
              <a-button
                size="small"
                type="link"
                icon="plus"
                @click="handleAddSymbol(record.symbol)"
                :disabled="monitoredSymbols.includes(record.symbol)"
              >
                {{ monitoredSymbols.includes(record.symbol) ? '已监控' : '添加' }}
              </a-button>
            </template>
          </a-table>
        </a-tab-pane>

        <!-- 监控币种标签页 -->
        <a-tab-pane key="monitored" tab="📊 监控币种列表">
          <a-table
            :columns="monitoredColumns"
            :data-source="monitoredSymbolsData"
            :loading="loading.monitored"
            :pagination="{ pageSize: 20 }"
            rowKey="symbol"
            size="middle"
          >
            <!-- 币种 -->
            <template slot="symbol" slot-scope="text">
              <strong>{{ text }}</strong>
            </template>

            <!-- 市场类型 -->
            <template slot="market_type" slot-scope="text">
              <a-tag :color="text === 'futures' ? 'blue' : 'green'">
                {{ text === 'futures' ? '永续合约' : '现货' }}
              </a-tag>
            </template>

            <!-- 最后信号 -->
            <template slot="last_signal" slot-scope="text">
              <a-tag v-if="text === 'UP'" color="green">📈 涨</a-tag>
              <a-tag v-else-if="text === 'DOWN'" color="red">📉 跌</a-tag>
              <a-tag v-else color="default">-</a-tag>
            </template>

            <!-- 操作 -->
            <template slot="action" slot-scope="text, record">
              <a-popconfirm
                title="确定移除该币种吗?"
                @confirm="handleRemoveSymbol(record.symbol)"
              >
                <a-button size="small" type="link" icon="delete">移除</a-button>
              </a-popconfirm>
            </template>
          </a-table>
        </a-tab-pane>

        <!-- 信号历史标签页 -->
        <a-tab-pane key="signals" tab="🔔 信号历史">
          <div style="margin-bottom: 16px">
            <a-button
              icon="delete"
              @click="handleClearSignals"
            >
              清空信号历史
            </a-button>
          </div>

          <a-table
            :columns="signalColumns"
            :data-source="signals"
            :loading="loading.signals"
            :pagination="{ pageSize: 50 }"
            rowKey="timestamp"
            size="middle"
          >
            <!-- 信号类型 -->
            <template slot="signal_type" slot-scope="text">
              <a-tag :color="text === 'UP' ? 'green' : 'red'">
                {{ text === 'UP' ? '📈 涨信号' : '📉 跌信号' }}
              </a-tag>
            </template>

            <!-- 时间 -->
            <template slot="timestamp" slot-scope="text">
              {{ formatTime(text) }}
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 添加币种弹窗 -->
    <a-modal
      v-model="addModalVisible"
      title="添加监控币种"
      @ok="handleAddSymbolConfirm"
      @cancel="addModalVisible = false"
    >
      <a-form-model :model="addForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-model-item label="币种符号">
          <a-input
            v-model="addForm.symbol"
            placeholder="例如: BTCUSDT"
            @keyup.enter="handleAddSymbolConfirm"
          />
        </a-form-model-item>
        <a-form-model-item label="市场类型">
          <a-tag color="blue">永续合约</a-tag>
        </a-form-model-item>
      </a-form-model>
    </a-modal>

    <!-- 配置弹窗 -->
    <a-modal
      v-model="configModalVisible"
      title="监控配置"
      @ok="handleSaveConfig"
      @cancel="configModalVisible = false"
    >
      <a-form-model :model="configForm" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item label="检查间隔(秒)">
          <a-input-number
            v-model="configForm.check_interval"
            :min="10"
            :step="10"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            建议值: 60秒 (每分钟检查一次)
          </div>
        </a-form-model-item>
        <a-form-model-item label="信号冷却(秒)">
          <a-input-number
            v-model="configForm.signal_cooldown"
            :min="0"
            :step="60"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            建议值: 300秒 (5分钟内不重复发送同一币种信号)
          </div>
        </a-form-model-item>
        <a-form-model-item label="自动获取涨幅榜">
          <a-switch v-model="configForm.auto_fetch_gainers" />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            启用后每3分钟自动获取涨幅榜TOP20并加入监控
          </div>
        </a-form-model-item>
        <a-form-model-item v-if="configForm.auto_fetch_gainers" label="自动获取间隔(秒)">
          <a-input-number
            v-model="configForm.auto_fetch_interval"
            :min="60"
            :step="60"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            建议值: 180秒 (每3分钟)
          </div>
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getMonitorStatus,
  startMonitor,
  stopMonitor,
  getMonitoredSymbols,
  addSymbol,
  removeSymbol,
  addTopGainers,
  getSignals,
  clearSignals,
  getMonitorConfig,
  updateMonitorConfig
} from '@/api/hamaMonitor'
import { getBinanceGainers } from '@/api/multiExchange'
import { message } from 'ant-design-vue'
import moment from 'moment'
import { mapState } from 'vuex'

export default {
  name: 'SmartMonitor',
  data () {
    return {
      activeTab: 'gainers',
      marketType: 'futures', // 默认使用永续合约

      // 监控状态
      monitorStatus: {
        running: false,
        symbol_count: 0,
        total_signals: 0,
        check_interval: 60,
        signal_cooldown: 300
      },

      // 涨幅榜数据
      gainers: [],
      monitoredSymbols: [],
      monitoredSymbolsData: [],
      signals: [],

      // 弹窗状态
      addModalVisible: false,
      configModalVisible: false,

      // 表单数据
      addForm: {
        symbol: '',
        market_type: 'futures' // 默认使用永续合约
      },
      configForm: {
        check_interval: 60,
        signal_cooldown: 300,
        auto_fetch_gainers: false,
        auto_fetch_interval: 180
      },

      // 加载状态
      loading: {
        start: false,
        stop: false,
        addGainers: false,
        refresh: false,
        gainers: false,
        monitored: false,
        signals: false,
        addAllGainers: false
      },

      // 表格列配置
      gainerColumns: [
        { title: '排名', dataIndex: 'rank', width: 80, align: 'center', scopedSlots: { customRender: 'rank' } },
        { title: '币种', dataIndex: 'symbol', width: 150 },
        { title: '最新价', dataIndex: 'price', width: 120, align: 'right', customRender: (text) => text ? text.toFixed(2) : '-' },
        { title: '涨跌幅', dataIndex: 'price_change_percent', width: 120, align: 'right', scopedSlots: { customRender: 'priceChangePercent' } },
        { title: '成交量(USDT)', dataIndex: 'quote_volume', width: 150, align: 'right', customRender: (text) => text ? (text / 1000000).toFixed(2) + 'M' : '-' },
        { title: 'HAMA状态', dataIndex: 'hama_signal', width: 120, align: 'center', scopedSlots: { customRender: 'hamaStatus' } },
        { title: '操作', dataIndex: 'action', width: 100, align: 'center', scopedSlots: { customRender: 'action' } }
      ],

      monitoredColumns: [
        { title: '币种', dataIndex: 'symbol', width: 150 },
        { title: '市场类型', dataIndex: 'market_type', width: 120, align: 'center', scopedSlots: { customRender: 'market_type' } },
        { title: '添加时间', dataIndex: 'added_at', width: 180 },
        { title: '最后检查', dataIndex: 'last_check', width: 180 },
        { title: '最后信号', dataIndex: 'last_signal', width: 120, align: 'center', scopedSlots: { customRender: 'last_signal' } },
        { title: '操作', dataIndex: 'action', width: 100, align: 'center', scopedSlots: { customRender: 'action' } }
      ],

      signalColumns: [
        { title: '币种', dataIndex: 'symbol', width: 150 },
        { title: '信号类型', dataIndex: 'signal_type', width: 120, align: 'center', scopedSlots: { customRender: 'signal_type' } },
        { title: '价格', dataIndex: 'price', width: 120, align: 'right' },
        { title: 'HAMA收盘价', dataIndex: 'candle_close', width: 120, align: 'right' },
        { title: 'MA均线', dataIndex: 'ma', width: 120, align: 'right' },
        { title: '描述', dataIndex: 'description' },
        { title: '时间', dataIndex: 'timestamp', width: 180, scopedSlots: { customRender: 'timestamp' } }
      ]
    }
  },
  computed: {
    ...mapState({
      navTheme: state => state.app.theme
    }),
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    }
  },
  mounted () {
    // 先获取监控列表,再获取涨幅榜(以便合并HAMA信号状态)
    this.refreshData().then(() => {
      this.fetchGainers()
    })
    this.fetchConfig()
  },
  methods: {
    // 刷新所有数据
    async refreshData () {
      try {
        this.loading.refresh = true
        await Promise.all([
          this.fetchMonitorStatus(),
          this.fetchMonitoredSymbols(),
          this.fetchSignals()
        ])
      } finally {
        this.loading.refresh = false
      }
    },

    // 获取监控状态
    async fetchMonitorStatus () {
      try {
        const res = await getMonitorStatus()
        if (res.success) {
          this.monitorStatus = res.data
        }
      } catch (error) {
        console.error('获取监控状态失败:', error)
      }
    },

    // 获取涨幅榜
    async fetchGainers () {
      try {
        this.loading.gainers = true
        const res = await getBinanceGainers({
          market: 'futures', // 固定使用永续合约
          limit: 20
        })
        // multiExchange API返回格式: { code: 1, msg: "success", data: { gainers: [] } }
        if (res.code === 1 && res.data) {
          this.gainers = res.data.gainers || []

          // 合并HAMA信号状态:从监控列表中查找并添加hama_signal字段
          this.gainers.forEach(gainer => {
            const monitored = this.monitoredSymbolsData.find(m => m.symbol === gainer.symbol)
            if (monitored && monitored.last_signal) {
              gainer.hama_signal = monitored.last_signal
            } else {
              gainer.hama_signal = null
            }
          })
        }
      } catch (error) {
        message.error('获取涨幅榜失败')
      } finally {
        this.loading.gainers = false
      }
    },

    // 获取监控币种
    async fetchMonitoredSymbols () {
      try {
        this.loading.monitored = true
        const res = await getMonitoredSymbols()
        if (res.success) {
          this.monitoredSymbolsData = res.data.symbols || []
          this.monitoredSymbols = this.monitoredSymbolsData.map(s => s.symbol)
        }
      } catch (error) {
        console.error('获取监控币种失败:', error)
      } finally {
        this.loading.monitored = false
      }
    },

    // 获取信号历史
    async fetchSignals () {
      try {
        this.loading.signals = true
        const res = await getSignals({ limit: 100 })
        if (res.success) {
          this.signals = res.data.signals || []
        }
      } catch (error) {
        console.error('获取信号历史失败:', error)
      } finally {
        this.loading.signals = false
      }
    },

    // 获取配置
    async fetchConfig () {
      try {
        const res = await getMonitorConfig()
        if (res.success) {
          this.configForm = {
            check_interval: res.data.check_interval,
            signal_cooldown: res.data.signal_cooldown,
            auto_fetch_gainers: false,
            auto_fetch_interval: 180
          }
        }
      } catch (error) {
        console.error('获取配置失败:', error)
      }
    },

    // 启动监控
    async handleStart () {
      try {
        this.loading.start = true
        const res = await startMonitor()
        if (res.success) {
          message.success('监控服务已启动')
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('启动监控失败')
      } finally {
        this.loading.start = false
      }
    },

    // 停止监控
    async handleStop () {
      try {
        this.loading.stop = true
        const res = await stopMonitor()
        if (res.success) {
          message.success('监控服务已停止')
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('停止监控失败')
      } finally {
        this.loading.stop = false
      }
    },

    // 显示添加弹窗
    showAddModal () {
      this.addForm = { symbol: '', market_type: 'futures' }
      this.addModalVisible = true
    },

    // 添加单个币种
    async handleAddSymbol (symbol) {
      try {
        const res = await addSymbol({
          symbol,
          market_type: 'futures' // 固定使用永续合约
        })
        if (res.success) {
          message.success(`已添加 ${symbol}`)
          this.addModalVisible = false
          await this.fetchMonitoredSymbols()
          await this.fetchMonitorStatus()
          // 刷新涨幅榜以更新HAMA状态
          await this.fetchGainers()
        }
      } catch (error) {
        message.error('添加币种失败')
      }
    },

    // 添加币种确认
    async handleAddSymbolConfirm () {
      if (!this.addForm.symbol) {
        message.warning('请输入币种符号')
        return
      }
      await this.handleAddSymbol(this.addForm.symbol.toUpperCase())
    },

    // 移除币种
    async handleRemoveSymbol (symbol) {
      try {
        const res = await removeSymbol({ symbol })
        if (res.success) {
          message.success(`已移除 ${symbol}`)
          await this.fetchMonitoredSymbols()
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('移除币种失败')
      }
    },

    // 添加涨幅榜TOP20
    async handleAddTopGainers () {
      try {
        this.loading.addGainers = true
        const res = await addTopGainers({
          limit: 20,
          market: 'futures' // 固定使用永续合约
        })
        if (res.success) {
          message.success(`已添加 ${res.data.added} 个涨幅榜币种`)
          await this.fetchMonitoredSymbols()
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('添加涨幅榜失败')
      } finally {
        this.loading.addGainers = false
      }
    },

    // 添加当前涨幅榜所有币种
    async handleAddAllGainers () {
      try {
        this.loading.addAllGainers = true
        let addedCount = 0
        for (const gainer of this.gainers) {
          if (!this.monitoredSymbols.includes(gainer.symbol)) {
            await addSymbol({
              symbol: gainer.symbol,
              market_type: 'futures' // 固定使用永续合约
            })
            addedCount++
          }
        }
        message.success(`已添加 ${addedCount} 个币种`)
        await this.fetchMonitoredSymbols()
        await this.fetchMonitorStatus()
      } catch (error) {
        message.error('批量添加失败')
      } finally {
        this.loading.addAllGainers = false
      }
    },

    // 清空信号历史
    async handleClearSignals () {
      try {
        const res = await clearSignals()
        if (res.success) {
          message.success('已清空信号历史')
          await this.fetchSignals()
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('清空失败')
      }
    },

    // 显示配置弹窗
    showConfigModal () {
      this.configModalVisible = true
    },

    // 保存配置
    async handleSaveConfig () {
      try {
        const res = await updateMonitorConfig({
          check_interval: this.configForm.check_interval,
          signal_cooldown: this.configForm.signal_cooldown
        })
        if (res.success) {
          message.success('配置已保存')
          this.configModalVisible = false
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        message.error('保存配置失败')
      }
    },

    // 市场类型切换
    async handleMarketChange () {
      await this.fetchGainers()
    },

    // 获取排名颜色
    getRankColor (rank) {
      if (rank === 1) return 'gold'
      if (rank === 2) return 'silver'
      if (rank === 3) return '#cd7f32'
      return 'default'
    },

    // 格式化时间
    formatTime (timestamp) {
      return moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    }
  }
}
</script>

<style lang="less" scoped>
.smart-monitor-page {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);

  .page-header {
    margin-bottom: 24px;
    background: #fff;
    padding: 24px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;

      .anticon {
        margin-right: 12px;
        color: #1890ff;
      }
    }

    p {
      margin: 0;
      color: #666;
      font-size: 14px;
    }
  }

  .status-card {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .market-selector {
    display: flex;
    align-items: center;
  }
}
</style>
