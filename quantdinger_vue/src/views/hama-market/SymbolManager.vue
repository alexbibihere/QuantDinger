<template>
  <div class="symbol-manager">
    <!-- 币种管理按钮 -->
    <a-button @click="openManager" type="default">
      <a-icon type="setting" />
      币种管理
    </a-button>

    <!-- 币种管理弹窗 -->
    <a-modal
      v-model="visible"
      title="HAMA 币种管理"
      width="900px"
      :footer="null"
      @cancel="closeManager"
    >
      <div class="manager-content">
        <!-- 操作栏 -->
        <div class="toolbar">
          <a-space>
            <a-button type="primary" size="small" @click="showAddModal">
              <a-icon type="plus" />
              添加币种
            </a-button>
            <a-button size="small" @click="loadSymbols" :loading="loading">
              <a-icon type="reload" />
              刷新
            </a-button>
            <a-button size="small" @click="batchEnable(true)">
              <a-icon type="check-square" />
              批量启用
            </a-button>
            <a-button size="small" @click="batchEnable(false)">
              <a-icon type="stop" />
              批量禁用
            </a-button>
          </a-space>

          <a-input-search
            v-model="searchText"
            placeholder="搜索币种..."
            style="width: 200px"
            size="small"
            @search="onSearch"
          />
        </div>

        <!-- 币种列表 -->
        <a-table
          :columns="columns"
          :data-source="filteredSymbols"
          :loading="loading"
          :pagination="{ pageSize: 10, size: 'small' }"
          :row-selection="{
            selectedRowKeys: selectedKeys,
            onChange: onSelectChange
          }"
          row-key="id"
          size="small"
          style="margin-top: 16px"
        >
          <!-- 币种 -->
          <template slot="symbol" slot-scope="text, record">
            <a-tag color="blue">{{ text }}</a-tag>
          </template>

          <!-- 名称 -->
          <template slot="symbol_name" slot-scope="text">
            <span>{{ text || '-' }}</span>
          </template>

          <!-- 启用状态 -->
          <template slot="enabled" slot-scope="text">
            <a-switch
              :checked="text"
              size="small"
              @change="checked => toggleEnable(record.symbol, checked)"
            />
          </template>

          <!-- 优先级 -->
          <template slot="priority" slot-scope="text">
            <a-tag color="orange">{{ text }}</a-tag>
          </template>

          <!-- 通知设置 -->
          <template slot="notify_enabled" slot-scope="text">
            <a-tag v-if="text" color="green">已启用</a-tag>
            <a-tag v-else color="default">未启用</a-tag>
          </template>

          <!-- 操作 -->
          <template slot="action" slot-scope="text, record">
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="editSymbol(record)"
              >
                <a-icon type="edit" />
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个币种吗?"
                @confirm="removeSymbol(record.symbol)"
                ok-text="确定"
                cancel-text="取消"
              >
                <a-button type="link" size="small" danger>
                  <a-icon type="delete" />
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </a-table>
      </div>
    </a-modal>

    <!-- 添加/编辑币种弹窗 -->
    <a-modal
      v-model="formModalVisible"
      :title="isEditMode ? '编辑币种' : '添加币种'"
      @ok="handleFormSubmit"
      :confirm-loading="formLoading"
      @cancel="resetForm"
    >
      <a-form-model
        ref="symbolForm"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-model-item label="币种符号" prop="symbol">
          <a-input
            v-model="formData.symbol"
            placeholder="例如: BTCUSDT"
            :disabled="isEditMode"
            @keyup.native="formData.symbol = formData.symbol.toUpperCase()"
          />
        </a-form-model-item>

        <a-form-model-item label="币种名称" prop="symbol_name">
          <a-input
            v-model="formData.symbol_name"
            placeholder="例如: Bitcoin"
          />
        </a-form-model-item>

        <a-form-model-item label="市场" prop="market">
          <a-select v-model="formData.market">
            <a-select-option value="spot">现货</a-select-option>
            <a-select-option value="futures">合约</a-select-option>
          </a-select>
        </a-form-model-item>

        <a-form-model-item label="优先级" prop="priority">
          <a-input-number
            v-model="formData.priority"
            :min="0"
            :max="1000"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            数值越大优先级越高，默认 0
          </div>
        </a-form-model-item>

        <a-form-model-item label="启用监控" prop="enabled">
          <a-switch v-model="formData.enabled" />
        </a-form-model-item>

        <a-form-model-item label="启用通知" prop="notify_enabled">
          <a-switch v-model="formData.notify_enabled" />
        </a-form-model-item>

        <a-form-model-item
          v-if="formData.notify_enabled"
          label="通知阈值"
          prop="notify_threshold"
        >
          <a-input-number
            v-model="formData.notify_threshold"
            :min="0.1"
            :max="100"
            :step="0.1"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            涨跌幅达到该百分比时发送通知，默认 2.0%
          </div>
        </a-form-model-item>

        <a-form-model-item label="备注" prop="notes">
          <a-textarea
            v-model="formData.notes"
            :rows="3"
            placeholder="添加备注信息..."
          />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getSymbolsList,
  addSymbol,
  updateSymbol,
  deleteSymbol,
  toggleSymbol as toggleSymbolApi,
  batchEnableSymbols
} from '@/api/hamaMarket'

export default {
  name: 'SymbolManager',
  data () {
    return {
      visible: false,
      loading: false,
      formLoading: false,
      formModalVisible: false,
      isEditMode: false,
      symbols: [],
      selectedKeys: [],
      searchText: '',
      formData: {
        symbol: '',
        symbol_name: '',
        market: 'spot',
        enabled: true,
        priority: 0,
        notify_enabled: false,
        notify_threshold: 2.0,
        notes: ''
      },
      formRules: {
        symbol: [
          { required: true, message: '请输入币种符号', trigger: 'blur' },
          { pattern: /^[A-Z]+USDT$/, message: '币种符号格式错误（例如: BTCUSDT）', trigger: 'blur' }
        ]
      },
      columns: [
        {
          title: '币种',
          dataIndex: 'symbol',
          key: 'symbol',
          width: 120,
          scopedSlots: { customRender: 'symbol' }
        },
        {
          title: '名称',
          dataIndex: 'symbol_name',
          key: 'symbol_name',
          scopedSlots: { customRender: 'symbol_name' }
        },
        {
          title: '市场',
          dataIndex: 'market',
          key: 'market',
          width: 80
        },
        {
          title: '启用',
          dataIndex: 'enabled',
          key: 'enabled',
          width: 80,
          align: 'center',
          scopedSlots: { customRender: 'enabled' }
        },
        {
          title: '优先级',
          dataIndex: 'priority',
          key: 'priority',
          width: 80,
          align: 'center',
          scopedSlots: { customRender: 'priority' }
        },
        {
          title: '通知',
          dataIndex: 'notify_enabled',
          key: 'notify_enabled',
          width: 80,
          align: 'center',
          scopedSlots: { customRender: 'notify_enabled' }
        },
        {
          title: '操作',
          key: 'action',
          width: 150,
          scopedSlots: { customRender: 'action' }
        }
      ]
    }
  },
  computed: {
    filteredSymbols () {
      if (!this.searchText) {
        return this.symbols
      }
      const lowerSearch = this.searchText.toLowerCase()
      return this.symbols.filter(s =>
        s.symbol.toLowerCase().includes(lowerSearch) ||
        (s.symbol_name && s.symbol_name.toLowerCase().includes(lowerSearch))
      )
    }
  },
  methods: {
    openManager () {
      this.visible = true
      this.loadSymbols()
    },

    closeManager () {
      this.visible = false
    },

    async loadSymbols () {
      this.loading = true
      try {
        const res = await getSymbolsList({ enabled: false })
        if (res.success && res.data) {
          this.symbols = res.data.symbols || []
        }
      } catch (error) {
        console.error('加载币种列表失败:', error)
        this.$message.error('加载币种列表失败')
      } finally {
        this.loading = false
      }
    },

    showAddModal () {
      this.isEditMode = false
      this.formModalVisible = true
      this.resetForm()
    },

    editSymbol (record) {
      this.isEditMode = true
      this.formModalVisible = true
      this.formData = {
        symbol: record.symbol,
        symbol_name: record.symbol_name || '',
        market: record.market || 'spot',
        enabled: record.enabled,
        priority: record.priority || 0,
        notify_enabled: record.notify_enabled || false,
        notify_threshold: record.notify_threshold || 2.0,
        notes: record.notes || ''
      }
    },

    resetForm () {
      this.formData = {
        symbol: '',
        symbol_name: '',
        market: 'spot',
        enabled: true,
        priority: 0,
        notify_enabled: false,
        notify_threshold: 2.0,
        notes: ''
      }
      this.formModalVisible = false
    },

    async handleFormSubmit () {
      this.$refs.symbolForm.validate(async valid => {
        if (!valid) return

        this.formLoading = true
        try {
          if (this.isEditMode) {
            await updateSymbol(this.formData)
            this.$message.success('更新成功')
          } else {
            await addSymbol(this.formData)
            this.$message.success('添加成功')
          }
          this.formModalVisible = false
          this.resetForm()
          await this.loadSymbols()
          // 通知父组件刷新
          this.$emit('symbols-changed')
        } catch (error) {
          console.error('操作失败:', error)
          this.$message.error(error.response?.data?.error || '操作失败')
        } finally {
          this.formLoading = false
        }
      })
    },

    async toggleEnable (symbol, enabled) {
      try {
        await toggleSymbolApi({ symbol, enabled })
        this.$message.success(`${enabled ? '启用' : '禁用'}成功`)
        await this.loadSymbols()
        this.$emit('symbols-changed')
      } catch (error) {
        console.error('切换状态失败:', error)
        this.$message.error('操作失败')
        // 恢复开关状态
        await this.loadSymbols()
      }
    },

    async removeSymbol (symbol) {
      try {
        await deleteSymbol({ symbol })
        this.$message.success('删除成功')
        await this.loadSymbols()
        this.$emit('symbols-changed')
      } catch (error) {
        console.error('删除失败:', error)
        this.$message.error('删除失败')
      }
    },

    onSelectChange (selectedKeys) {
      this.selectedKeys = selectedKeys
    },

    async batchEnable (enabled) {
      if (this.selectedKeys.length === 0) {
        this.$message.warning('请先选择币种')
        return
      }

      const selectedSymbols = this.symbols
        .filter(s => this.selectedKeys.includes(s.id))
        .map(s => s.symbol)

      try {
        await batchEnableSymbols({
          symbols: selectedSymbols,
          enabled
        })
        this.$message.success(`批量${enabled ? '启用' : '禁用'}成功`)
        this.selectedKeys = []
        await this.loadSymbols()
        this.$emit('symbols-changed')
      } catch (error) {
        console.error('批量操作失败:', error)
        this.$message.error('批量操作失败')
      }
    },

    onSearch () {
      // 搜索由 computed 自动处理
    }
  }
}
</script>

<style lang="less" scoped>
.symbol-manager {
  display: inline-block;

  .manager-content {
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
  }
}
</style>
