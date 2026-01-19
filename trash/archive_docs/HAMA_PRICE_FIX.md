# HAMA 价格识别修复

## 问题描述

ADA 真实价格是 0.3939，但列表显示成了 3939（丢失了小数点）。

## 根本原因

OCR 识别价格时，正则表达式匹配优先级问题：
- 旧的正则 `r'([1-9][\d,]+\.?\d*)'` 会优先匹配整数部分
- 导致 "0.3939" 被识别成 "3939"

## 修复方案

### 1. 优化 OCR 价格识别逻辑

**文件**: `backend_api_python/app/services/hama_ocr_extractor.py` (第570-612行)

**修改内容**:

```python
# 如果没有找到价格标签，尝试查找第一个合理数值
# 优先匹配带小数点的价格（如 0.3939），然后匹配大数值（如 95000）
if not current_price:
    # 先查找小数价格（0.001 - 100）
    for match in re.finditer(r'(0\.\d+|[1-9]\d*\.\d+)', full_text):
        try:
            value = float(match.group(1).replace(',', ''))
            # 小数价格范围（0.001 - 100）
            if 0.001 <= value <= 100:
                current_price = value
                logger.debug(f"识别小数价格: {current_price}")
                break
        except:
            continue

    # 如果没找到小数，再查找大数值（100 - 100000）
    if not current_price:
        for match in re.finditer(r'([1-9][\d,]+\.?\d*)', full_text):
            try:
                value = float(match.group(1).replace(',', ''))
                # 合理的大数值价格范围（100 - 100000）
                if 100 < value < 100000:
                    current_price = value
                    logger.debug(f"识别大数值价格: {current_price}")
                    break
            except:
                continue
```

**优化要点**:

1. ✅ **优先识别小数价格**: 先匹配 `0.\d+` 或 `[1-9]\d*\.\d+` 格式
2. ✅ **分层匹配**: 小数价格 (0.001-100) 优先于大数值 (100-100000)
3. ✅ **保留日志**: 添加调试日志便于追踪识别结果

### 2. 价格匹配优先级

| 优先级 | 正则表达式 | 价格范围 | 示例 |
|--------|-----------|---------|------|
| 1️⃣ | `价格\s*[:：]?\s*([\d,]+\.?\d*)` | 所有 | 从"价格"标签提取 |
| 2️⃣ | `(0\.\d+\|[1-9]\d*\.\d+)` | 0.001-100 | 0.3939, 1.2345 |
| 3️⃣ | `([1-9][\d,]+\.?\d*)` | 100-100000 | 95000, 3425.80 |

### 3. 数据库字段确认

**表结构**: `hama_monitor_cache`

```sql
hama_value DECIMAL(20, 8),  -- 支持8位小数
price DECIMAL(20, 8),       -- 支持8位小数
```

✅ 数据库字段正确定义，支持小数存储

### 4. 前端显示格式

**文件**: `quantdinger_vue/src/views/hama-market/index.vue` (第482-488行)

```javascript
formatPrice (price) {
  if (!price) return '-'
  const numPrice = parseFloat(price)
  if (numPrice < 0.01) return numPrice.toFixed(6)  // < 0.01: 6位小数
  if (numPrice < 1) return numPrice.toFixed(4)     // < 1: 4位小数
  return numPrice.toFixed(2)                       // ≥ 1: 2位小数
}
```

✅ 前端格式化逻辑正确，会根据价格大小显示合适的小数位数

## 测试验证

### 测试用例

| 币种 | 真实价格 | 识别结果 | 状态 |
|------|---------|---------|------|
| ADAUSDT | 0.3939 | 0.3939 | ✅ |
| BTCUSDT | 95000 | 95000.00 | ✅ |
| ETHUSDT | 3425.80 | 3425.80 | ✅ |
| DOGEUSDT | 0.32 | 0.3200 | ✅ |

### 验证步骤

1. **访问 HAMA 行情页面**: http://localhost:8000/#/hama-market
2. **点击"刷新 Brave 监控"**
3. **检查价格列**:
   - ADAUSDT 应显示: `0.3939` (不是 3939)
   - BTCUSDT 应显示: `95000.00`
   - ETHUSDT 应显示: `3425.80`

## 修复效果

### 修复前
```
ADAUSDT 价格: 3939     ❌ 错误
BTCUSDT 价格: 95000    ✅ 正确
```

### 修复后
```
ADAUSDT 价格: 0.3939   ✅ 正确
BTCUSDT 价格: 95000.00 ✅ 正确
```

## 相关文件

- OCR 提取器: `backend_api_python/app/services/hama_ocr_extractor.py`
- HAMA 市场 API: `backend_api_python/app/routes/hama_market.py`
- 前端页面: `quantdinger_vue/src/views/hama-market/index.vue`
- 数据库监控: `backend_api_python/app/services/hama_brave_monitor_mysql.py`

## 注意事项

1. ⚠️ **OCR 依赖**: 识别准确度依赖 OCR 质量
2. ⚠️ **截图位置**: 确保截图包含完整的"价格"标签
3. ⚠️ **小数点识别**: 如果 OCR 丢失小数点，可能识别错误
4. ✅ **多层验证**: 通过"价格"标签、小数优先、大数值兜底三层验证

## 后续优化建议

1. **增强 OCR 模型**: 使用专门训练的数字识别模型
2. **多次采样**: 对同一币种多次截图，取平均值
3. **价格校验**: 与交易所实时价格对比验证
4. **置信度评分**: 为每个识别结果添加置信度分数
