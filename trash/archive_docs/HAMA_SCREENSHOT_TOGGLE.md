# HAMA 截图折叠展开功能

## 修改时间
2026-01-18

## 功能说明

仿照 TradingView 实时行情页面，使用 `+` / `-` 按钮控制截图的展开和收起，节省页面空间，提升用户体验。

## 核心功能

### 1. 折叠展开按钮

**默认状态（收起）**:
```
┌─────────────┐
│     +       │  展开
└─────────────┘
```

**展开状态**:
```
┌─────────────┐
│     -       │  收起
├─────────────┤
│  [截图]     │
│  时间戳     │
└─────────────┘
```

### 2. 交互逻辑

```javascript
toggleScreenshot(symbol) {
  const index = this.expandedScreenshots.indexOf(symbol)
  if (index > -1) {
    // 已展开，则收起
    this.expandedScreenshots.splice(index, 1)
  } else {
    // 未展开，则展开
    this.expandedScreenshots.push(symbol)
  }
}
```

### 3. 视觉效果

- ✅ **图标切换**: `+` 展开 / `-` 收起
- ✅ **文字提示**: "展开" / "收起"
- ✅ **平滑动画**: 下滑展开效果（0.3s ease）
- ✅ **悬停效果**: 链接悬停变色
- ✅ **点击预览**: 截图仍可点击放大

## 代码实现

### 模板部分

```vue
<template slot="screenshot" slot-scope="text, record">
  <div v-if="record.hama_brave && record.hama_brave.screenshot_url" class="screenshot-cell">
    <!-- 展开/收起按钮 -->
    <a-button
      type="link"
      size="small"
      @click="toggleScreenshot(record.symbol)"
      class="screenshot-toggle"
    >
      <a-icon :type="expandedScreenshots.includes(record.symbol) ? 'minus' : 'plus'" />
      {{ expandedScreenshots.includes(record.symbol) ? '收起' : '展开' }}
    </a-button>

    <!-- 截图内容（使用 v-show 控制显示） -->
    <div v-show="expandedScreenshots.includes(record.symbol)" class="screenshot-content">
      <a-image
        :src="record.hama_brave.screenshot_url"
        :width="280"
        :height="180"
        fit="contain"
        style="border-radius: 4px; border: 1px solid #d9d9d9; background: #f5f5f5;"
      />
      <div class="screenshot-meta">
        <a-tag color="blue" size="small">
          <a-icon type="clock-circle" />
          {{ formatTimestamp(record.hama_brave.cached_at) }}
        </a-tag>
      </div>
    </div>
  </div>
</template>
```

### 数据部分

```javascript
data() {
  return {
    expandedScreenshots: [],  // 展开的截图列表
  }
}
```

### 方法部分

```javascript
methods: {
  toggleScreenshot(symbol) {
    const index = this.expandedScreenshots.indexOf(symbol)
    if (index > -1) {
      this.expandedScreenshots.splice(index, 1)
    } else {
      this.expandedScreenshots.push(symbol)
    }
  }
}
```

### 样式部分

```less
.screenshot-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;

  .screenshot-toggle {
    padding: 0;
    font-size: 12px;
    color: #1890ff;

    &:hover {
      color: #40a9ff;
    }
  }

  .screenshot-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    animation: slideDown 0.3s ease;
  }

  .screenshot-thumbnail {
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      transform: scale(1.02);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## 优化效果

### 修改前
- 截图一直显示，占用大量空间
- 列宽需要 200px
- 不便于快速浏览大量币种

### 修改后
- 默认收起，只显示 `+` 按钮
- 列宽缩小到 120px（节省 40%）
- 需要时点击展开查看
- 平滑的展开/收起动画

## 表格布局

| 列 | 宽度 | 说明 |
|---|------|------|
| 币种 | 120px | 固定左侧 |
| 价格 | 120px | 右对齐 |
| **HAMA截图** ⭐ | **120px** | **折叠展开** |
| HAMA状态 | 150px | 趋势标签 |
| 最近监控 | 150px | 时间戳 |
| 操作 | 120px | 链接按钮 |

**总宽度**: 约 780px（比之前减少 120px）

## 使用场景

### 场景 1: 快速浏览
```
BTCUSDT | 95000 | [+] | 上涨 | 刚刚 | 查看
ETHUSDT | 3425  | [+] | 下跌 | 5分钟| 查看
ADAUSDT | 0.39  | [+] | 盘整 | 1小时| 查看
```

### 场景 2: 查看截图
```
BTCUSDT | 95000 | [-]   | 上涨 | 刚刚 | 查看
                ┌─────────┐
                │ [截图]  │
                │ 刚刚    │
                └─────────┘
```

## 技术优势

✅ **节省空间**: 默认收起，减少 40% 列宽
✅ **按需展开**: 用户主动选择查看截图
✅ **状态独立**: 每个币种独立控制，互不影响
✅ **平滑动画**: 下滑展开效果，体验流畅
✅ **响应式**: 支持同时展开多个截图
✅ **记忆功能**: 刷新页面后状态重置（可根据需求改为 localStorage 持久化）

## 扩展功能建议

### 1. 全部展开/收起
```vue
<a-button @click="toggleAll">全部展开</a-button>
```

```javascript
toggleAll() {
  if (this.expandedScreenshots.length === this.watchlist.length) {
    this.expandedScreenshots = []  // 全部收起
  } else {
    this.expandedScreenshots = this.watchlist.map(w => w.symbol)  // 全部展开
  }
}
```

### 2. 状态持久化
```javascript
// 使用 localStorage 保存展开状态
toggleScreenshot(symbol) {
  // ... 现有逻辑
  localStorage.setItem('expandedScreenshots', JSON.stringify(this.expandedScreenshots))
}

mounted() {
  const saved = localStorage.getItem('expandedScreenshots')
  if (saved) {
    this.expandedScreenshots = JSON.parse(saved)
  }
}
```

### 3. 自动收起其他
```javascript
toggleScreenshot(symbol) {
  // 点击展开某个截图时，自动收起其他截图
  this.expandedScreenshots = [symbol]
}
```

## 相关文件

- 前端页面: `quantdinger_vue/src/views/hama-market/index.vue`
- 截图样式: `.screenshot-cell`, `.screenshot-toggle`, `.screenshot-content`
- 数据管理: `expandedScreenshots` 数组
- 方法: `toggleScreenshot(symbol)`

## 体验对比

| 特性 | 修改前 | 修改后 |
|------|--------|--------|
| 默认状态 | 显示所有截图 | 只显示 `+` 按钮 |
| 占用空间 | 200px 列宽 | 120px 列宽 |
| 浏览速度 | 需要滚动很多 | 快速浏览 |
| 交互性 | 被动查看 | 主动展开 |
| 视觉效果 | 平铺展示 | 折叠展开 |

## 总结

通过参考 TradingView 的设计理念，使用折叠展开的方式展示截图，既节省了页面空间，又提升了用户体验。用户可以根据需要选择性地查看截图，而不会影响整体的浏览速度。这是典型的"渐进式披露"设计模式的应用。
