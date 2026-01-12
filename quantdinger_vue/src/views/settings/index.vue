<template>
  <div class="settings-page" :class="{ 'theme-dark': isDarkTheme }">
    <!-- 重启提示 -->
    <a-alert
      v-if="showRestartTip"
      class="restart-alert"
      type="warning"
      showIcon
      closable
      @close="showRestartTip = false"
    >
      <template slot="message">
        <span>{{ $t('settings.restartRequired') }}</span>
        <a-button size="small" type="link" @click="copyRestartCommand">
          {{ $t('settings.copyRestartCmd') }}
        </a-button>
      </template>
    </a-alert>

    <div class="settings-header">
      <h2 class="page-title">
        <a-icon type="setting" />
        <span>{{ $t('settings.title') }}</span>
      </h2>
      <p class="page-desc">{{ $t('settings.description') }}</p>
    </div>

    <a-spin :spinning="loading">
      <div class="settings-content">
        <a-collapse v-model="activeKeys" :bordered="false" class="settings-collapse">
          <a-collapse-panel v-for="(group, groupKey) in schema" :key="groupKey">
            <template slot="header">
              <span class="panel-header">
                <span class="panel-title">{{ getGroupTitle(groupKey, group.title) }}</span>
              </span>
            </template>
            <template slot="extra">
              <a-icon :type="getGroupIcon(groupKey)" class="panel-icon" />
            </template>

            <a-form :form="form" layout="vertical" class="settings-form">
              <a-row :gutter="24">
                <a-col
                  :xs="24"
                  :sm="24"
                  :md="12"
                  :lg="12"
                  v-for="item in group.items"
                  :key="item.key">
                  <a-form-item>
                    <template slot="label">
                      <span class="form-label-with-link">
                        <span>{{ getItemLabel(groupKey, item) }}</span>
                        <a
                          v-if="item.link"
                          :href="item.link"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="api-link"
                          @click.stop
                        >
                          <a-icon type="link" />
                          {{ getLinkText(item.link_text) }}
                        </a>
                      </span>
                    </template>
                    <!-- 文本输入 -->
                    <template v-if="item.type === 'text'">
                      <a-input
                        v-decorator="[item.key, { initialValue: getFieldValue(groupKey, item.key) }]"
                        :placeholder="item.default ? `${$t('settings.default')}: ${item.default}` : ''"
                        allowClear
                      />
                    </template>

                    <!-- 密码输入 -->
                    <template v-else-if="item.type === 'password'">
                      <div class="password-field">
                        <a-input
                          v-decorator="[item.key, { initialValue: getFieldValue(groupKey, item.key) }]"
                          :type="passwordVisible[item.key] ? 'text' : 'password'"
                          :placeholder="$t('settings.inputApiKey')"
                          allowClear
                        >
                          <a-icon
                            slot="suffix"
                            :type="passwordVisible[item.key] ? 'eye' : 'eye-invisible'"
                            @click="togglePasswordVisible(item.key)"
                            style="cursor: pointer"
                          />
                        </a-input>
                      </div>
                    </template>

                    <!-- 数字输入 -->
                    <template v-else-if="item.type === 'number'">
                      <a-input-number
                        v-decorator="[item.key, { initialValue: getNumberValue(groupKey, item.key, item.default) }]"
                        :placeholder="item.default ? `${$t('settings.default')}: ${item.default}` : ''"
                        style="width: 100%"
                      />
                    </template>

                    <!-- 布尔开关 -->
                    <template v-else-if="item.type === 'boolean'">
                      <a-switch
                        v-decorator="[item.key, { valuePropName: 'checked', initialValue: getBoolValue(groupKey, item.key, item.default) }]"
                      />
                    </template>

                    <!-- 下拉选择 -->
                    <template v-else-if="item.type === 'select'">
                      <a-select
                        v-decorator="[item.key, { initialValue: getFieldValue(groupKey, item.key) || item.default }]"
                        :placeholder="item.default ? `${$t('settings.default')}: ${item.default}` : $t('settings.pleaseSelect')"
                      >
                        <a-select-option v-for="opt in item.options" :key="opt" :value="opt">
                          {{ opt }}
                        </a-select-option>
                      </a-select>
                    </template>

                    <div class="field-default" v-if="item.default && item.type !== 'boolean' && item.type !== 'password'">
                      {{ $t('settings.default') }}: {{ item.default }}
                    </div>
                  </a-form-item>
                </a-col>
              </a-row>
            </a-form>
          </a-collapse-panel>

          <!-- 交易所凭证管理 -->
          <a-collapse-panel key="exchange_credentials">
            <template slot="header">
              <span class="panel-header">
                <span class="panel-title">{{ $t('settings.exchangeCredentials.title') }}</span>
              </span>
            </template>
            <template slot="extra">
              <a-icon type="bank" class="panel-icon" />
            </template>
            <exchange-credentials />
          </a-collapse-panel>
        </a-collapse>
      </div>
    </a-spin>

    <div class="settings-footer">
      <a-button @click="handleReset" :disabled="saving">
        <a-icon type="undo" />
        {{ $t('settings.reset') }}
      </a-button>
      <a-button type="primary" @click="handleSave" :loading="saving">
        <a-icon type="save" />
        {{ $t('settings.save') }}
      </a-button>
    </div>
  </div>
</template>

<script>
import { getSettingsSchema, getSettingsValues, saveSettings } from '@/api/settings'
import { baseMixin } from '@/store/app-mixin'
import ExchangeCredentials from './components/ExchangeCredentials.vue'

export default {
  name: 'Settings',
  components: {
    ExchangeCredentials
  },
  mixins: [baseMixin],
  data () {
    return {
      loading: false,
      saving: false,
      schema: {},
      values: {},
      activeKeys: ['ai', 'data_source', 'app', 'auth', 'exchange_credentials'],
      passwordVisible: {},
      showRestartTip: false
    }
  },
  computed: {
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    }
  },
  beforeCreate () {
    this.form = this.$form.createForm(this)
  },
  mounted () {
    this.loadSettings()
  },
  methods: {
    async loadSettings () {
      this.loading = true
      try {
        const [schemaRes, valuesRes] = await Promise.all([
          getSettingsSchema(),
          getSettingsValues()
        ])

        if (schemaRes.code === 1) {
          this.schema = schemaRes.data
        }

        if (valuesRes.code === 1) {
          this.values = valuesRes.data
        }
      } catch (error) {
        this.$message.error(this.$t('settings.loadFailed'))
      } finally {
        this.loading = false
      }
    },

    getGroupIcon (groupKey) {
      const icons = {
        auth: 'lock',
        server: 'cloud-server',
        worker: 'schedule',
        notification: 'notification',
        smtp: 'mail',
        twilio: 'phone',
        strategy: 'fund',
        proxy: 'global',
        app: 'appstore',
        ai: 'robot',
        market: 'stock',
        data_source: 'database',
        search: 'search'
      }
      return icons[groupKey] || 'setting'
    },

    getGroupTitle (groupKey, defaultTitle) {
      const key = `settings.group.${groupKey}`
      const translated = this.$t(key)
      return translated !== key ? translated : defaultTitle
    },

    getItemLabel (groupKey, item) {
      const key = `settings.field.${item.key}`
      const translated = this.$t(key)
      return translated !== key ? translated : item.label
    },

    getLinkText (linkText) {
      if (!linkText) return this.$t('settings.getApi')
      // 如果是翻译键（以 settings.link. 开头），则翻译
      if (linkText.startsWith('settings.link.')) {
        const translated = this.$t(linkText)
        return translated !== linkText ? translated : linkText
      }
      return linkText
    },

    getFieldValue (groupKey, key) {
      const groupValues = this.values[groupKey] || {}
      return groupValues[key] || ''
    },

    togglePasswordVisible (key) {
      this.$set(this.passwordVisible, key, !this.passwordVisible[key])
    },

    getNumberValue (groupKey, key, defaultVal) {
      const val = this.getFieldValue(groupKey, key)
      if (val === '' || val === null || val === undefined) {
        return defaultVal ? parseFloat(defaultVal) : null
      }
      return parseFloat(val)
    },

    getBoolValue (groupKey, key, defaultVal) {
      const val = this.getFieldValue(groupKey, key)
      if (val === '' || val === null || val === undefined) {
        return defaultVal === 'True' || defaultVal === 'true' || defaultVal === true
      }
      return val === 'True' || val === 'true' || val === true
    },

    handleReset () {
      this.form.resetFields()
      this.loadSettings()
    },

    copyRestartCommand () {
      const cmd = 'cd backend_api_python && py run.py'
      navigator.clipboard.writeText(cmd).then(() => {
        this.$message.success(this.$t('settings.copySuccess'))
      }).catch(() => {
        this.$message.error(this.$t('settings.copyFailed'))
      })
    },

    async handleSave () {
      this.form.validateFields(async (err, formValues) => {
        if (err) {
          return
        }

        this.saving = true
        try {
          // 按组整理数据
          const data = {}
          for (const groupKey of Object.keys(this.schema)) {
            data[groupKey] = {}
            const group = this.schema[groupKey]
            for (const item of group.items) {
              if (item.key in formValues) {
                let value = formValues[item.key]
                // 布尔值转字符串
                if (item.type === 'boolean') {
                  value = value ? 'True' : 'False'
                }
                data[groupKey][item.key] = value
              }
            }
          }

          const res = await saveSettings(data)
          if (res.code === 1) {
            this.$message.success(res.msg || this.$t('settings.saveSuccess'))
            // 显示重启提示
            if (res.data && res.data.requires_restart) {
              this.showRestartTip = true
            }
            // 重新加载配置
            this.loadSettings()
          } else {
            this.$message.error(res.msg || this.$t('settings.saveFailed'))
          }
        } catch (error) {
          this.$message.error(this.$t('settings.saveFailed') + ': ' + error.message)
        } finally {
          this.saving = false
        }
      })
    }
  }
}
</script>

<style lang="less" scoped>
@primary-color: #1890ff;
@success-color: #52c41a;
@border-radius: 12px;
@card-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

.settings-page {
  padding: 24px;
  min-height: calc(100vh - 120px);
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);

  .restart-alert {
    margin-bottom: 16px;
    border-radius: 8px;
  }

  .settings-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 700;
      margin: 0 0 8px 0;
      color: #1e3a5f;
      display: flex;
      align-items: center;
      gap: 12px;

      .anticon {
        font-size: 28px;
        color: @primary-color;
      }
    }

    .page-desc {
      color: #64748b;
      font-size: 14px;
      margin: 0;
    }
  }

  .settings-content {
    margin-bottom: 80px;
  }

  .settings-collapse {
    background: transparent;

    /deep/ .ant-collapse-item {
      margin-bottom: 16px;
      border: none;
      border-radius: @border-radius;
      overflow: hidden;
      background: #fff;
      box-shadow: @card-shadow;

      .ant-collapse-header {
        font-size: 16px;
        font-weight: 600;
        color: #1e3a5f;
        padding: 16px 24px;
        padding-left: 48px;
        background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        align-items: center;

        .ant-collapse-arrow {
          color: @primary-color;
          left: 20px;
        }

        .panel-header {
          display: inline-flex;
          align-items: center;
          flex: 1;

          .panel-title {
            font-size: 16px;
          }
        }

        .panel-icon {
          font-size: 18px;
          color: @primary-color;
        }
      }

      .ant-collapse-content {
        border-top: none;

        .ant-collapse-content-box {
          padding: 24px;
        }
      }
    }
  }

  .settings-form {
    /deep/ .ant-form-item-label {
      padding-bottom: 4px;

      label {
        color: #475569;
        font-weight: 500;
      }

      .form-label-with-link {
        display: flex;
        align-items: center;
        gap: 8px;

        .api-link {
          font-size: 12px;
          font-weight: 400;
          color: @primary-color;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          background: rgba(24, 144, 255, 0.08);
          border-radius: 4px;
          transition: all 0.2s;

          &:hover {
            background: rgba(24, 144, 255, 0.15);
            color: darken(@primary-color, 10%);
          }

          .anticon {
            font-size: 11px;
          }
        }
      }
    }

    /deep/ .ant-input,
    /deep/ .ant-input-number,
    /deep/ .ant-select-selection {
      border-radius: 8px;
    }

    /deep/ .ant-input-number {
      width: 100%;
    }

    .password-field {
      .field-hint {
        margin-top: 4px;
        font-size: 12px;
        color: @success-color;
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }

    .field-default {
      margin-top: 4px;
      font-size: 12px;
      color: #94a3b8;
    }
  }

  .settings-footer {
    position: fixed;
    bottom: 0;
    left: 208px;
    right: 0;
    padding: 16px 24px;
    background: #fff;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    z-index: 100;

    .ant-btn {
      min-width: 100px;
      height: 40px;
      border-radius: 8px;
      font-weight: 500;
    }
  }

  // 暗黑主题
  &.theme-dark {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);

    .restart-alert {
      background: #2d333b;
      border-color: #b08800;
    }

    .settings-header {
      .page-title {
        color: #e0e6ed;
      }

      .page-desc {
        color: #8b949e;
      }
    }

    .settings-collapse {
      /deep/ .ant-collapse-item {
        background: #1e222d;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);

        .ant-collapse-header {
          background: linear-gradient(135deg, #252a36 0%, #1e222d 100%);
          color: #e0e6ed;
          border-bottom-color: rgba(255, 255, 255, 0.06);

          .panel-header .panel-title {
            color: #e0e6ed;
          }
        }

        .ant-collapse-content {
          background: #1e222d;

          .ant-collapse-content-box {
            background: #1e222d;
          }
        }
      }
    }

    .settings-form {
      /deep/ .ant-form-item-label {
        label {
          color: #c9d1d9;
        }

        .form-label-with-link .api-link {
          background: rgba(24, 144, 255, 0.15);
          color: #58a6ff;

          &:hover {
            background: rgba(24, 144, 255, 0.25);
          }
        }
      }

      /deep/ .ant-input,
      /deep/ .ant-input-password,
      /deep/ .ant-input-number,
      /deep/ .ant-select-selection {
        background: #0d1117;
        border-color: #30363d;
        color: #c9d1d9;

        &:hover,
        &:focus {
          border-color: @primary-color;
        }
      }

      /deep/ .ant-input-number-input {
        background: transparent;
        color: #c9d1d9;
      }

      /deep/ .ant-select-arrow {
        color: #8b949e;
      }

      .field-default {
        color: #6e7681;
      }
    }

    .settings-footer {
      background: #1e222d;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.25);
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .settings-page {
    padding: 16px;

    .settings-footer {
      left: 0;
      padding: 12px 16px;
    }
  }
}
</style>
