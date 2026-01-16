# 🤖 HAMA 视觉识别 - 快速开始指南

## 📋 前置要求

### 1. 获取 OpenRouter API 密钥

**步骤**：

1. **访问 OpenRouter**：https://openrouter.ai/

2. **注册账号**
   - 点击 "Sign in"
   - 使用 GitHub 或 Google 账号登录
   - 或使用邮箱注册

3. **获取 API 密钥**
   - 登录后访问：https://openrouter.ai/keys
   - 点击 "Create Key"
   - 输入密钥名称（如：QuantDinger-HAMA）
   - 点击 "Create" 生成密钥
   - 复制密钥（格式：`sk-or-v1-xxxxx`）

4. **充值（可选）**
   - OpenRouter 按使用量计费
   - 建议先充值 $5-10 测试
   - GPT-4o 价格：约 $0.0025/张图片

### 2. 配置 API 密钥

**方法 1：修改 .env 文件（推荐）**

编辑 `backend_api_python/.env` 文件，添加：

```bash
# OpenRouter API 配置
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=openai/gpt-4o
```

**方法 2：通过环境变量**

```bash
# Linux/Mac
export OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# Windows (PowerShell)
$env:OPENROUTER_API_KEY="sk-or-v1-your-actual-key-here"

# Windows (CMD)
set OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

**方法 3：通过 docker-compose.yml**

编辑 `docker-compose.yml`：

```yaml
services:
  backend:
    environment:
      - OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
      - OPENROUTER_MODEL=openai/gpt-4o
```

### 3. 重启服务

```bash
# 重新构建并启动
docker-compose down backend
docker-compose up -d --build backend

# 或者只重启
docker-compose restart backend
```

## 🚀 测试功能

### 1. 验证配置

```bash
curl http://localhost:5000/api/hama-vision/health
```

预期输出：
```json
{
  "success": true,
  "service": "HAMA Vision API",
  "status": "running",
  "api_key_configured": true,  // ← 应该是 true
  "model": "openai/gpt-4o"
}
```

### 2. 运行测试脚本

```bash
# 进入容器
docker exec -it quantdinger-backend bash

# 运行测试
cd /app
python test_hama_vision.py
```

### 3. 调用 API

```bash
curl -X POST http://localhost:5000/api/hama-vision/extract \
  -H "Content-Type: application/json" \
  -d '{
    "chart_url": "https://cn.tradingview.com/chart/U1FY2qxO/",
    "symbol": "ETHUSD",
    "interval": "15"
  }'
```

## 📊 预期输出

成功时返回：
```json
{
  "success": true,
  "data": {
    "hama_value": 3418.03,
    "hama_color": "green",
    "trend": "up",
    "current_price": 3369.1,
    "bollinger_bands": {
      "upper": 3500.0,
      "middle": 3400.0,
      "lower": 3300.0
    },
    "confidence": "high",
    "source": "vision",
    "symbol": "ETHUSD",
    "interval": "15",
    "screenshot_path": "/tmp/ETHUSD_15_chart.png"
  }
}
```

## 🔧 故障排查

### 问题 1：`api_key_configured: false`

**原因**：API 密钥未配置

**解决**：
1. 检查 `.env` 文件中是否有 `OPENROUTER_API_KEY`
2. 确保密钥格式正确（以 `sk-or-v1-` 开头）
3. 重启容器

### 问题 2：`error: API 调用失败: 401`

**原因**：API 密钥无效

**解决**：
1. 访问 https://openrouter.ai/keys 检查密钥
2. 确保密钥没有过期
3. 尝试重新生成密钥

### 问题 3：`error: API 调用失败: 429`

**原因**：速率限制或配额用尽

**解决**：
1. 检查账户余额：https://openrouter.ai/settings/credit
2. 充值后重试
3. 降低调用频率

### 问题 4：图表加载失败

**原因**：网络问题或 Cookie 失效

**解决**：
1. 检查代理配置
2. 更新 TradingView Cookies
3. 使用其他图表 URL

## 💰 成本估算

### OpenRouter 定价（2026年1月）

| 模型 | 价格/张图片 | 每天成本* | 每月成本* |
|------|-----------|----------|----------|
| GPT-4o | $0.0025 | $0.24 | $7.20 |
| Claude 3.5 Sonnet | $0.0015 | $0.14 | $4.32 |

*假设每 15 分钟调用一次（每天 96 次）

### 节省成本建议

1. **缓存结果**：识别结果缓存 15 分钟
2. **按需调用**：只在需要时使用视觉识别
3. **优先使用本地计算**：日常使用方案 3（本地计算）
4. **批量处理**：一次调用识别多个币种

## 🎯 使用场景建议

### ✅ 适合使用视觉识别

- 需要验证本地计算的准确性
- 图表布局特殊，无法用常规方法提取
- 偶尔使用，不需要高频调用
- 开发调试阶段

### ❌ 不适合使用视觉识别

- 高频交易（每秒/每分钟调用）
- 成本敏感的应用
- 需要实时响应的场景

### 💡 推荐做法

```python
def smart_hama_extraction(ohlcv_data, chart_url=None):
    """智能 HAMA 提取：优先本地，必要时视觉识别"""

    # 1. 优先使用本地计算（快速、免费）
    result = calculate_hama_from_ohlcv(ohlcv_data)

    if result:
        return result

    # 2. 本地计算失败，使用视觉识别（备用）
    if chart_url:
        result = extract_hama_with_vision(chart_url)

    return result
```

## 📞 技术支持

如有问题，请：
1. 查看日志：`docker logs quantdinger-backend --tail 100`
2. 检查配置：`docker exec quantdinger-backend env | grep OPENROUTER`
3. 测试 API：https://openrouter.ai/playground

## 📚 相关链接

- OpenRouter 官网：https://openrouter.ai/
- API 文档：https://openrouter.ai/docs/quick-start
- 定价：https://openrouter.ai/docs#models
- 密钥管理：https://openrouter.ai/keys
