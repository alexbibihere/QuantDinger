<template>
  <a-card :bordered="false" class="hama-monitor-card">
    <!-- 页面标题和操作栏 -->
    <template slot="title">
      <span>{{ $t('hamaMonitor.title') }}</span>
      <a-tag :color="monitorStatus.running ? 'green' : 'red'" style="margin-left: 12px">
        {{ monitorStatus.running ? $t('hamaMonitor.running') : $t('hamaMonitor.stopped') }}
      </a-tag>
    </template>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="6">
        <a-statistic
          :title="$t('hamaMonitor.monitoredSymbols')"
          :value="monitorStatus.symbol_count"
          prefix="📊"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="$t('hamaMonitor.totalSignals')"
          :value="monitorStatus.total_signals"
          prefix="🔔"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="$t('hamaMonitor.checkInterval')"
          :value="monitorStatus.check_interval"
          suffix="s"
          prefix="⏱️"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="$t('hamaMonitor.signalCooldown')"
          :value="monitorStatus.signal_cooldown"
          suffix="s"
          prefix="❄️"
        />
      </a-col>
    </a-row>

    <!-- 控制按钮 -->
    <div style="margin-bottom: 24px">
      <a-space>
        <a-button
          v-if="!monitorStatus.running"
          type="primary"
          icon="play-circle"
          @click="handleStart"
          :loading="loading.start"
        >
          {{ $t('hamaMonitor.startMonitor') }}
        </a-button>
        <a-button
          v-else
          type="danger"
          icon="pause-circle"
          @click="handleStop"
          :loading="loading.stop"
        >
          {{ $t('hamaMonitor.stopMonitor') }}
        </a-button>

        <a-button
          icon="plus"
          @click="showAddModal"
          :disabled="!monitorStatus.running"
        >
          {{ $t('hamaMonitor.addSymbol') }}
        </a-button>

        <a-button
          icon="thunderbolt"
          @click="handleAddTopGainers"
          :loading="loading.addGainers"
          :disabled="!monitorStatus.running"
        >
          {{ $t('hamaMonitor.addTopGainers') }}
        </a-button>

        <a-button
          icon="setting"
          @click="showConfigModal"
        >
          {{ $t('hamaMonitor.config') }}
        </a-button>

        <a-button
          icon="sync"
          @click="refreshData"
          :loading="loading.refresh"
        >
          {{ $t('common.refresh') }}
        </a-button>
      </a-space>
    </div>

    <!-- 监控币种列表 -->
    <a-card :title="$t('hamaMonitor.monitoredSymbols')" style="margin-bottom: 24px">
      <a-table
        :columns="symbolColumns"
        :data-source="symbols"
        :loading="loading.symbols"
        :pagination="{ pageSize: 10 }"
        row-key="symbol"
        size="middle"
      >
        <template slot="market_type" slot-scope="text">
          <a-tag :color="text === 'spot' ? 'blue' : 'purple'">
            {{ text === 'spot' ? $t('hamaMonitor.spot') : $t('hamaMonitor.futures') }}
          </a-tag>
        </template>

        <template slot="last_signal" slot-scope="text">
          <a-tag v-if="text === 'UP'" color="green">📈 {{ $t('hamaMonitor.upSignal') }}</a-tag>
          <a-tag v-else-if="text === 'DOWN'" color="red">📉 {{ $t('hamaMonitor.downSignal') }}</a-tag>
          <a-tag v-else color="gray">-</a-tag>
        </template>

        <template slot="action" slot-scope="text, record">
          <a-button
            type="link"
            size="small"
            icon="delete"
            @click="handleRemoveSymbol(record)"
          >
            {{ $t('common.remove') }}
          </a-button>
        </template>
      </a-table>
    </a-card>

    <!-- 信号历史 -->
    <a-card :title="$t('hamaMonitor.signalHistory')">
      <template slot="extra">
        <a-button
          type="link"
          icon="delete"
          @click="handleClearSignals"
          :disabled="signals.length === 0"
        >
          {{ $t('hamaMonitor.clearHistory') }}
        </a-button>
      </template>

      <a-table
        :columns="signalColumns"
        :data-source="signals"
        :loading="loading.signals"
        :pagination="{ pageSize: 20 }"
        row-key="timestamp"
        size="middle"
        :scroll="{ x: 800 }"
      >
        <template slot="signal_type" slot-scope="text">
          <a-tag v-if="text === 'UP'" color="green">📈 {{ $t('hamaMonitor.upSignal') }}</a-tag>
          <a-tag v-else-if="text === 'DOWN'" color="red">📉 {{ $t('hamaMonitor.downSignal') }}</a-tag>
        </template>

        <template slot="price" slot-scope="text, record">
          <div>
            <div>{{ $t('hamaMonitor.price') }}: {{ text ? text.toFixed(4) : '-' }}</div>
            <div style="font-size: 12px; color: #999">
              HAMA: {{ record.candle_close ? record.candle_close.toFixed(4) : '-' }} /
              MA: {{ record.ma ? record.ma.toFixed(4) : '-' }}
            </div>
          </div>
        </template>

        <template slot="timestamp" slot-scope="text">
          {{ formatTime(text) }}
        </template>

        <template slot="description" slot-scope="text">
          <a-tooltip :title="text">
            <span>{{ text }}</span>
          </a-tooltip>
        </template>
      </a-table>
    </a-card>

    <!-- 添加币种弹窗 -->
    <a-modal
      v-model="addModalVisible"
      :title="$t('hamaMonitor.addSymbol')"
      @ok="handleAddSymbol"
      :confirm-loading="loading.add"
    >
      <a-form-model :model="addForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('hamaMonitor.symbol')">
          <a-input
            v-model="addForm.symbol"
            :placeholder="$t('hamaMonitor.symbolPlaceholder')"
            @keyup.native="addForm.symbol = addForm.symbol.toUpperCase()"
          />
        </a-form-model-item>

        <a-form-model-item :label="$t('hamaMonitor.marketType')">
          <a-select v-model="addForm.market_type">
            <a-select-option value="spot">{{ $t('hamaMonitor.spot') }}</a-select-option>
            <a-select-option value="futures">{{ $t('hamaMonitor.futures') }}</a-select-option>
          </a-select>
        </a-form-model-item>
      </a-form-model>
    </a-modal>

    <!-- 添加涨幅榜弹窗 -->
    <a-modal
      v-model="addGainersModalVisible"
      :title="$t('hamaMonitor.addTopGainers')"
      @ok="handleConfirmAddGainers"
      :confirm-loading="loading.addGainers"
    >
      <a-form-model :model="addGainersForm" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
        <a-form-model-item :label="$t('hamaMonitor.marketType')">
          <a-select v-model="addGainersForm.market">
            <a-select-option value="spot">{{ $t('hamaMonitor.spot') }}</a-select-option>
            <a-select-option value="futures">{{ $t('hamaMonitor.futures') }}</a-select-option>
          </a-select>
        </a-form-model-item>

        <a-form-model-item :label="$t('hamaMonitor.limit')">
          <a-input-number
            v-model="addGainersForm.limit"
            :min="1"
            :max="50"
            style="width: 100%"
          />
        </a-form-model-item>
      </a-form-model>
    </a-modal>

    <!-- 配置弹窗 -->
    <a-modal
      v-model="configModalVisible"
      :title="$t('hamaMonitor.config')"
      @ok="handleSaveConfig"
      :confirm-loading="loading.config"
    >
      <a-form-model :model="configForm" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
        <a-form-model-item :label="$t('hamaMonitor.checkInterval')">
          <a-input-number
            v-model="configForm.check_interval"
            :min="10"
            :max="3600"
            style="width: 100%"
          />
          <span style="margin-left: 8px">秒</span>
        </a-form-model-item>

        <a-form-model-item :label="$t('hamaMonitor.signalCooldown')">
          <a-input-number
            v-model="configForm.signal_cooldown"
            :min="0"
            :max="3600"
            style="width: 100%"
          />
          <span style="margin-left: 8px">秒</span>
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </a-card>
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
import moment from 'moment'

export default {
  name: 'HamaMonitor',
  data () {
    return {
      monitorStatus: {
        running: false,
        symbol_count: 0,
        total_signals: 0,
        check_interval: 60,
        signal_cooldown: 300
      },
      symbols: [],
      signals: [],
      loading: {
        start: false,
        stop: false,
        symbols: false,
        signals: false,
        add: false,
        addGainers: false,
        config: false,
        refresh: false
      },
      addModalVisible: false,
      addForm: {
        symbol: '',
        market_type: 'spot'
      },
      addGainersModalVisible: false,
      addGainersForm: {
        market: 'spot',
        limit: 20
      },
      configModalVisible: false,
      configForm: {
        check_interval: 60,
        signal_cooldown: 300
      },
      symbolColumns: [
        {
          title: this.$t('hamaMonitor.symbol'),
          dataIndex: 'symbol',
          key: 'symbol'
        },
        {
          title: this.$t('hamaMonitor.marketType'),
          dataIndex: 'market_type',
          scopedSlots: { customRender: 'market_type' },
          width: 120
        },
        {
          title: this.$t('hamaMonitor.lastSignal'),
          dataIndex: 'last_signal',
          scopedSlots: { customRender: 'last_signal' },
          width: 150
        },
        {
          title: this.$t('hamaMonitor.lastCheckTime'),
          dataIndex: 'last_check',
          customRender: (text) => text ? this.formatTime(text) : '-',
          width: 180
        },
        {
          title: this.$t('common.action'),
          key: 'action',
          scopedSlots: { customRender: 'action' },
          width: 100
        }
      ],
      signalColumns: [
        {
          title: this.$t('hamaMonitor.symbol'),
          dataIndex: 'symbol',
          key: 'symbol',
          width: 120
        },
        {
          title: this.$t('hamaMonitor.signalType'),
          dataIndex: 'signal_type',
          scopedSlots: { customRender: 'signal_type' },
          width: 120
        },
        {
          title: this.$t('hamaMonitor.priceInfo'),
          dataIndex: 'price',
          scopedSlots: { customRender: 'price' },
          width: 180
        },
        {
          title: this.$t('hamaMonitor.timestamp'),
          dataIndex: 'timestamp',
          scopedSlots: { customRender: 'timestamp' },
          width: 180
        },
        {
          title: this.$t('hamaMonitor.description'),
          dataIndex: 'description',
          scopedSlots: { customRender: 'description' }
        }
      ],
      refreshTimer: null
    }
  },
  mounted () {
    this.refreshData()
    this.startAutoRefresh()
  },
  beforeDestroy () {
    this.stopAutoRefresh()
  },
  methods: {
    async refreshData () {
      this.loading.refresh = true
      try {
        await Promise.all([
          this.fetchMonitorStatus(),
          this.fetchSymbols(),
          this.fetchSignals()
        ])
      } finally {
        this.loading.refresh = false
      }
    },

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

    async fetchSymbols () {
      this.loading.symbols = true
      try {
        const res = await getMonitoredSymbols()
        if (res.success) {
          this.symbols = res.data.symbols || []
        }
      } catch (error) {
        console.error('获取监控币种失败:', error)
      } finally {
        this.loading.symbols = false
      }
    },

    async fetchSignals () {
      this.loading.signals = true
      try {
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

    async handleStart () {
      this.loading.start = true
      try {
        const res = await startMonitor()
        if (res.success) {
          this.$message.success(res.message)
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.startFailed'))
      } finally {
        this.loading.start = false
      }
    },

    async handleStop () {
      this.loading.stop = true
      try {
        const res = await stopMonitor()
        if (res.success) {
          this.$message.success(res.message)
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.stopFailed'))
      } finally {
        this.loading.stop = false
      }
    },

    showAddModal () {
      this.addForm = { symbol: '', market_type: 'spot' }
      this.addModalVisible = true
    },

    async handleAddSymbol () {
      if (!this.addForm.symbol) {
        this.$message.warning(this.$t('hamaMonitor.pleaseEnterSymbol'))
        return
      }

      this.loading.add = true
      try {
        const res = await addSymbol(this.addForm)
        if (res.success) {
          this.$message.success(res.message)
          this.addModalVisible = false
          await Promise.all([this.fetchMonitorStatus(), this.fetchSymbols()])
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.addFailed'))
      } finally {
        this.loading.add = false
      }
    },

    async handleRemoveSymbol (record) {
      this.$confirm({
        title: this.$t('hamaMonitor.confirmRemove'),
        content: this.$t('hamaMonitor.confirmRemoveContent', { symbol: record.symbol }),
        onOk: async () => {
          try {
            const res = await removeSymbol({ symbol: record.symbol })
            if (res.success) {
              this.$message.success(res.message)
              await Promise.all([this.fetchMonitorStatus(), this.fetchSymbols()])
            }
          } catch (error) {
            this.$message.error(this.$t('hamaMonitor.removeFailed'))
          }
        }
      })
    },

    handleAddTopGainers () {
      this.addGainersForm = { market: 'spot', limit: 20 }
      this.addGainersModalVisible = true
    },

    async handleConfirmAddGainers () {
      this.loading.addGainers = true
      try {
        const res = await addTopGainers(this.addGainersForm)
        if (res.success) {
          this.$message.success(
            this.$t('hamaMonitor.addedGainers', {
              total: res.data.total,
              added: res.data.added
            })
          )
          this.addGainersModalVisible = false
          await Promise.all([this.fetchMonitorStatus(), this.fetchSymbols()])
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.addGainersFailed'))
      } finally {
        this.loading.addGainers = false
      }
    },

    async handleClearSignals () {
      this.$confirm({
        title: this.$t('hamaMonitor.confirmClear'),
        content: this.$t('hamaMonitor.confirmClearContent'),
        onOk: async () => {
          try {
            const res = await clearSignals()
            if (res.success) {
              this.$message.success(res.message)
              await this.fetchSignals()
            }
          } catch (error) {
            this.$message.error(this.$t('hamaMonitor.clearFailed'))
          }
        }
      })
    },

    async showConfigModal () {
      try {
        const res = await getMonitorConfig()
        if (res.success) {
          this.configForm = res.data
          this.configModalVisible = true
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.getConfigFailed'))
      }
    },

    async handleSaveConfig () {
      this.loading.config = true
      try {
        const res = await updateMonitorConfig(this.configForm)
        if (res.success) {
          this.$message.success(res.message)
          this.configModalVisible = false
          await this.fetchMonitorStatus()
        }
      } catch (error) {
        this.$message.error(this.$t('hamaMonitor.saveConfigFailed'))
      } finally {
        this.loading.config = false
      }
    },

    formatTime (timestamp) {
      return moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },

    startAutoRefresh () {
      // 每10秒自动刷新
      this.refreshTimer = setInterval(() => {
        if (this.monitorStatus.running) {
          this.fetchMonitorStatus()
          this.fetchSignals()
        }
      }, 10000)
    },

    stopAutoRefresh () {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    }
  }
}
</script>

<style scoped>
.hama-monitor-card {
  min-height: calc(100vh - 120px);
}
</style>
