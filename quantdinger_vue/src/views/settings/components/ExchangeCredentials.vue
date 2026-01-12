<template>
  <div class="exchange-credentials-manager">
    <div class="credentials-header">
      <h3>{{ $t('settings.exchangeCredentials.title') }}</h3>
      <p class="description">{{ $t('settings.exchangeCredentials.description') }}</p>
    </div>

    <!-- 添加凭证按钮 -->
    <div class="actions-bar">
      <a-button type="primary" icon="plus" @click="showAddModal">
        {{ $t('settings.exchangeCredentials.addCredential') }}
      </a-button>
      <a-button icon="reload" @click="loadCredentials" :loading="loading">
        {{ $t('common.refresh') }}
      </a-button>
    </div>

    <!-- 凭证列表 -->
    <a-table
      :columns="columns"
      :data-source="credentials"
      :loading="loading"
      :pagination="pagination"
      rowKey="id"
      class="credentials-table"
    >
      <template slot="exchange_id" slot-scope="text">
        <a-tag :color="getExchangeColor(text)">
          <a-icon :type="getExchangeIcon(text)" style="margin-right: 4px;" />
          {{ getExchangeName(text) }}
        </a-tag>
      </template>

      <template slot="api_key" slot-scope="text">
        <code class="api-key">{{ maskApiKey(text) }}</code>
      </template>

      <template slot="created_at" slot-scope="text">
        {{ formatDate(text) }}
      </template>

      <template slot="action" slot-scope="text, record">
        <a-button type="link" size="small" @click="testConnection(record)" :loading="record.testing">
          <a-icon type="api" />
          {{ $t('settings.exchangeCredentials.testConnection') }}
        </a-button>
        <a-divider type="vertical" />
        <a-popconfirm
          :title="$t('settings.exchangeCredentials.deleteConfirm')"
          :ok-text="$t('common.confirm')"
          :cancel-text="$t('common.cancel')"
          @confirm="deleteCredential(record.id)"
        >
          <a-button type="link" size="small" class="danger-text">
            <a-icon type="delete" />
            {{ $t('common.delete') }}
          </a-button>
        </a-popconfirm>
      </template>
    </a-table>

    <!-- 添加/编辑凭证对话框 -->
    <a-modal
      :visible="modalVisible"
      :title="modalTitle"
      :width="600"
      @ok="handleSubmit"
      @cancel="handleModalCancel"
      :confirmLoading="submitting"
    >
      <a-form-model
        ref="credentialForm"
        :model="form"
        :rules="rules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-model-item :label="$t('settings.exchangeCredentials.exchange')" prop="exchange_id">
          <a-select v-model="form.exchange_id" :placeholder="$t('settings.exchangeCredentials.selectExchange')">
            <a-select-option value="binance">Binance</a-select-option>
            <a-select-option value="okx">OKX</a-select-option>
            <a-select-option value="bybit">Bybit</a-select-option>
            <a-select-option value="bitget">Bitget</a-select-option>
            <a-select-option value="kucoin">KuCoin</a-select-option>
            <a-select-option value="huobi">Huobi</a-select-option>
            <a-select-option value="gate">Gate.io</a-select-option>
            <a-select-option value="coinbase">Coinbase</a-select-option>
            <a-select-option value="kraken">Kraken</a-select-option>
          </a-select>
        </a-form-model-item>

        <a-form-model-item :label="$t('settings.exchangeCredentials.apiKey')" prop="api_key">
          <a-input
            v-model="form.api_key"
            :placeholder="$t('settings.exchangeCredentials.inputApiKey')"
            type="password"
            :visibilityToggle="true"
          />
        </a-form-model-item>

        <a-form-model-item :label="$t('settings.exchangeCredentials.apiSecret')" prop="api_secret">
          <a-input
            v-model="form.api_secret"
            :placeholder="$t('settings.exchangeCredentials.inputApiSecret')"
            type="password"
            :visibilityToggle="true"
          />
        </a-form-model-item>

        <a-form-model-item :label="$t('settings.exchangeCredentials.passphrase')" prop="passphrase">
          <a-input
            v-model="form.passphrase"
            :placeholder="$t('settings.exchangeCredentials.passphraseHint')"
            type="password"
          />
          <div class="form-tip">{{ $t('settings.exchangeCredentials.passphraseHint') }}</div>
        </a-form-model-item>

        <a-alert
          :message="$t('settings.exchangeCredentials.securityTip')"
          type="info"
          show-icon
          class="security-tip"
        >
          <template slot="description">
            <ul>
              <li>{{ $t('settings.exchangeCredentials.tip1') }}</li>
              <li>{{ $t('settings.exchangeCredentials.tip2') }}</li>
              <li>{{ $t('settings.exchangeCredentials.tip3') }}</li>
            </ul>
          </template>
        </a-alert>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  listExchangeCredentials,
  createExchangeCredential,
  deleteExchangeCredential
} from '@/api/credentials'

export default {
  name: 'ExchangeCredentials',
  data () {
    return {
      credentials: [],
      loading: false,
      submitting: false,
      modalVisible: false,
      modalTitle: '',
      form: {
        exchange_id: undefined,
        api_key: '',
        api_secret: '',
        passphrase: ''
      },
      rules: {
        exchange_id: [{ required: true, message: this.$t('settings.exchangeCredentials.validation.exchangeRequired'), trigger: 'change' }],
        api_key: [{ required: true, message: this.$t('settings.exchangeCredentials.validation.apiKeyRequired'), trigger: 'blur' }],
        api_secret: [{ required: true, message: this.$t('settings.exchangeCredentials.validation.apiSecretRequired'), trigger: 'blur' }]
      },
      pagination: {
        pageSize: 10,
        current: 1,
        total: 0
      },
      columns: [
        {
          title: this.$t('settings.exchangeCredentials.exchange'),
          dataIndex: 'exchange_id',
          key: 'exchange_id',
          width: 150
        },
        {
          title: this.$t('settings.exchangeCredentials.apiKey'),
          dataIndex: 'api_key',
          key: 'api_key',
          scopedSlots: { customRender: 'api_key' }
        },
        {
          title: this.$t('settings.exchangeCredentials.createdAt'),
          dataIndex: 'created_at',
          key: 'created_at',
          width: 180,
          scopedSlots: { customRender: 'created_at' }
        },
        {
          title: this.$t('common.action'),
          key: 'action',
          width: 200,
          scopedSlots: { customRender: 'action' }
        }
      ]
    }
  },
  mounted () {
    this.loadCredentials()
  },
  methods: {
    async loadCredentials () {
      this.loading = true
      try {
        const res = await listExchangeCredentials()
        if (res.code === 1) {
          this.credentials = res.data.items || []
          this.pagination.total = this.credentials.length
        } else {
          this.$message.error(res.msg || this.$t('settings.exchangeCredentials.messages.loadFailed'))
        }
      } catch (error) {
        console.error('Failed to load credentials:', error)
        this.$message.error(this.$t('settings.exchangeCredentials.messages.loadFailed'))
      } finally {
        this.loading = false
      }
    },

    showAddModal () {
      this.modalTitle = this.$t('settings.exchangeCredentials.addCredential')
      this.form = {
        exchange_id: undefined,
        api_key: '',
        api_secret: '',
        passphrase: ''
      }
      this.modalVisible = true
      this.$nextTick(() => {
        this.$refs.credentialForm.clearValidate()
      })
    },

    handleModalCancel () {
      this.modalVisible = false
    },

    async handleSubmit () {
      this.$refs.credentialForm.validate(async valid => {
        if (valid) {
          this.submitting = true
          try {
            const res = await createExchangeCredential({
              exchange_id: this.form.exchange_id,
              api_key: this.form.api_key,
              api_secret: this.form.api_secret,
              passphrase: this.form.passphrase || null
            })

            if (res.code === 1) {
              this.$message.success(this.$t('settings.exchangeCredentials.messages.addSuccess'))
              this.modalVisible = false
              await this.loadCredentials()
            } else {
              this.$message.error(res.msg || this.$t('settings.exchangeCredentials.messages.addFailed'))
            }
          } catch (error) {
            console.error('Failed to add credential:', error)
            this.$message.error(this.$t('settings.exchangeCredentials.messages.addFailed'))
          } finally {
            this.submitting = false
          }
        }
      })
    },

    async deleteCredential (id) {
      try {
        const res = await deleteExchangeCredential(id)
        if (res.code === 1) {
          this.$message.success(this.$t('settings.exchangeCredentials.messages.deleteSuccess'))
          await this.loadCredentials()
        } else {
          this.$message.error(res.msg || this.$t('settings.exchangeCredentials.messages.deleteFailed'))
        }
      } catch (error) {
        console.error('Failed to delete credential:', error)
        this.$message.error(this.$t('settings.exchangeCredentials.messages.deleteFailed'))
      }
    },

    async testConnection (record) {
      this.$set(record, 'testing', true)
      try {
        // 这里可以添加测试连接的逻辑
        // 目前先显示一个简单的提示
        this.$message.info(this.$t('settings.exchangeCredentials.messages.testNotImplemented'))
      } finally {
        this.$set(record, 'testing', false)
      }
    },

    maskApiKey (key) {
      if (!key) return ''
      if (key.length <= 8) return '*'.repeat(key.length)
      return key.substring(0, 4) + '*'.repeat(8) + key.substring(key.length - 4)
    },

    formatDate (timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp * 1000)
      return date.toLocaleString()
    },

    getExchangeName (exchangeId) {
      const names = {
        binance: 'Binance',
        okx: 'OKX',
        bybit: 'Bybit',
        bitget: 'Bitget',
        kucoin: 'KuCoin',
        huobi: 'Huobi',
        gate: 'Gate.io',
        coinbase: 'Coinbase',
        kraken: 'Kraken'
      }
      return names[exchangeId] || exchangeId
    },

    getExchangeIcon (exchangeId) {
      return 'bank'
    },

    getExchangeColor (exchangeId) {
      const colors = {
        binance: 'gold',
        okx: 'blue',
        bybit: 'cyan',
        bitget: 'green',
        kucoin: 'purple',
        huobi: 'red',
        gate: 'orange',
        coinbase: 'blue',
        kraken: 'purple'
      }
      return colors[exchangeId] || 'default'
    }
  }
}
</script>

<style lang="less" scoped>
.exchange-credentials-manager {
  padding: 16px 0;

  .credentials-header {
    margin-bottom: 24px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
    }

    .description {
      margin: 8px 0 0;
      color: rgba(0, 0, 0, 0.45);
      font-size: 14px;
    }
  }

  .actions-bar {
    margin-bottom: 16px;
    display: flex;
    gap: 8px;
  }

  .credentials-table {
    .api-key {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 3px;
    }

    .danger-text {
      color: #ff4d4f;
    }
  }

  .form-tip {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 4px;
  }

  .security-tip {
    margin-top: 16px;

    ul {
      margin: 8px 0 0;
      padding-left: 20px;

      li {
        margin-bottom: 4px;
        font-size: 12px;
      }
    }
  }
}

.theme-dark {
  .credentials-header {
    .description {
      color: rgba(255, 255, 255, 0.65);
    }
  }

  .api-key {
    background: rgba(255, 255, 255, 0.1);
  }
}
</style>
