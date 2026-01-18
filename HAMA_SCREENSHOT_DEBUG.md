# HAMA 截图展开问题调试指南

## 问题描述

点击 `[+]` 展开按钮后，截图区域没有显示图片。

## 已完成的修复

### 1. 后端截图保存 ✅
- 截图保存到: `backend_api_python/app/screenshots/`
- 文件名格式: `hama_brave_{SYMBOL}_{TIMESTAMP}.png`
- 文件大小: ~17-19KB

### 2. 静态文件服务 ✅
- 访问路径: `/screenshot/{filename}`
- HTTP 状态: 200 OK
- Content-Type: image/png

### 3. API 数据返回 ✅
```json
{
  "hama_brave": {
    "screenshot_path": "hama_brave_BTCUSDT_1768728140.png",
    "screenshot_url": "/screenshot/hama_brave_BTCUSDT_1768728140.png"
  }
}
```

### 4. 前端组件优化 ✅
- 从 `a-image` 改为原生 `img` 标签
- 添加图片加载/错误处理
- 添加点击放大预览功能

## 测试步骤

### 1. 测试后端 API
```bash
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT"
```
预期返回包含 `screenshot_url` 字段

### 2. 测试截图 URL
```bash
curl -I "http://localhost:5000/screenshot/hama_brave_BTCUSDT_1768728140.png"
```
预期返回: `HTTP/1.1 200 OK`

### 3. 测试页面
打开 `backend_api_python/test_screenshot_url.html` 查看截图是否能正常显示

### 4. 测试前端
1. 访问 http://localhost:8000/#/hama-market
2. 点击任意币种的 `[+]` 按钮
3. 检查浏览器控制台（F12）

## 可能的问题和解决方案

### 问题1: CORS 错误
**现象**: 控制台显示 CORS policy 错误

**解决**: 后端已配置 CORS，检查 `app/__init__.py`:
```python
CORS(app)  # 已在第 482 行配置
```

### 问题2: 路径错误
**现象**: 404 Not Found

**检查**:
```bash
# 查看后端日志
tail -f backend_api_python/logs/app.log | grep screenshot
```

### 问题3: 图片加载失败
**现象**: 图片显示为破碎图标

**检查**:
1. 浏览器控制台 Network 标签
2. 查找截图 URL 的响应状态
3. 检查图片大小是否正常（应该 ~17-19KB）

### 问题4: v-show 不生效
**现象**: 点击 `[+]` 后区域不显示

**检查**:
1. 使用浏览器开发者工具检查 DOM
2. 查找 `screenshot-content` div 的 `display` 属性
3. 确认 `expandedScreenshots` 数组包含对应币种

### 问题5: 数据未更新
**现象**: 显示旧数据或"暂无截图"

**解决**: 刷新页面或点击"刷新 Brave 监控"按钮

## 代码修改总结

### 前端组件
```vue
<!-- 使用原生 img 标签 -->
<img
  :src="record.hama_brave.screenshot_url"
  @load="handleImageLoad"
  @error="handleImageError"
  @click="previewImage(url)"
/>
```

### 调试方法
```javascript
// 在浏览器控制台执行
console.log(this.watchlist[0].hama_brave)
// 应该看到 screenshot_url 字段

// 手动测试图片加载
const img = new Image()
img.src = 'http://localhost:5000/screenshot/hama_brave_BTCUSDT_1768728140.png'
img.onload = () => console.log('图片加载成功')
img.onerror = (e) => console.error('图片加载失败', e)
```

## 下一步排查

如果问题仍然存在，请：

1. **打开浏览器开发者工具** (F12)
2. **查看 Console 标签**: 看是否有 JavaScript 错误
3. **查看 Network 标签**: 找到截图 URL，查看：
   - Status Code (应该是 200)
   - Response Headers (Content-Type: image/png)
   - Size (应该 ~17000-19000 字节)
4. **截图控制台输出**:
   - "截图加载成功: {url}"
   - "截图加载失败: {url}"
5. **提供完整的错误信息**:
   - 浏览器控制台的错误消息
   - Network 标签中截图请求的详细信息

## 预期效果

点击 `[+]` 展开后应该看到：

```
┌────────────────┐
│  [-] 收起       │
├────────────────┤
│ ┌────────────┐ │
│ │            │ │
│ │  HAMA面板   │ │  280x180px
│ │  截图       │ │
│ │            │ │
│ └────────────┘ │
│ [刚刚]         │
└────────────────┘
```
