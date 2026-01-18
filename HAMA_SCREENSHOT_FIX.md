# HAMA 截图访问问题修复总结

## 问题原因

从 Redis 缓存切换到 SQLite 存储后，截图无法访问的原因：

1. **截图被删除**: 在 `hama_brave_monitor_mysql.py` 第224行，截图在OCR识别后被删除
2. **保存路径错误**: 截图保存到当前工作目录，而不是 `app/screenshots/` 目录
3. **路径不匹配**: 静态文件服务查找的路径与实际保存路径不一致

## 修复方案

### 1. 修改截图保存逻辑

**文件**: `backend_api_python/app/services/hama_brave_monitor_mysql.py` (第207-231行)

**修改前**:
```python
screenshot_path = f"hama_brave_{symbol}_{int(time.time())}.png"
result_path = self.ocr_extractor.capture_chart(chart_url, screenshot_path)

# OCR 识别后删除截图
os.remove(result_path)
```

**修改后**:
```python
# 构建截图保存路径（保存到 app/screenshots/ 目录）
import os
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
screenshot_dir = os.path.join(app_dir, 'screenshots')
os.makedirs(screenshot_dir, exist_ok=True)

screenshot_filename = f"hama_brave_{symbol}_{int(time.time())}.png"
screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

logger.info(f"截图保存路径: {screenshot_path}")

# 截图后不删除，保留用于前端展示
result_path = self.ocr_extractor.capture_chart(chart_url, screenshot_path)
logger.debug(f"截图已保留: {result_path}")
```

### 2. 添加截图路径字段

**文件**: `backend_api_python/app/services/hama_brave_monitor_mysql.py` (第239-241行)

```python
# 添加截图路径（相对路径用于前端访问）
hama_data['screenshot_path'] = screenshot_filename  # 只保存文件名
hama_data['screenshot_absolute_path'] = result_path  # 保存完整路径用于调试
```

### 3. 修复静态文件服务路径

**文件**: `backend_api_python/app/routes/static_files.py` (第16-25行)

**修改前**:
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))
screenshot_dir = os.path.join(app_dir, 'screenshots')
```

**修改后**:
```python
routes_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(routes_dir)
screenshot_dir = os.path.join(app_dir, 'screenshots')
logger.info(f"截图目录: {screenshot_dir}")
```

### 4. 添加调试日志

**文件**: `backend_api_python/app/routes/static_files.py` (第37-42行)

```python
logger.info(f"访问截图: {filename}, 截图目录: {screenshot_dir}")
logger.info(f"完整文件路径: {file_path}, 存在: {os.path.exists(file_path)}")
```

## 修复效果

### 修复前
```
HTTP/1.1 404 NOT FOUND
Content-Length: 49
```

### 修复后
```
HTTP/1.1 200 OK
Content-Length: 19148
```

## 截图生命周期

```
1. 触发监控
   ↓
2. 访问 TradingView 图表
   ↓
3. 截取右下角 HAMA 面板
   ↓
4. 保存到 app/screenshots/ 目录 ✅
   ↓
5. OCR 识别数据
   ↓
6. 保存到 SQLite 数据库（包含截图路径）
   ↓
7. 前端请求 /screenshot/filename.png
   ↓
8. 静态文件服务返回截图 ✅
   ↓
9. 前端展示截图（支持折叠展开）
```

## 相关文件

- 监控服务: `backend_api_python/app/services/hama_brave_monitor_mysql.py`
- 静态文件: `backend_api_python/app/routes/static_files.py`
- 前端页面: `quantdinger_vue/src/views/hama-market/index.vue`
- 截图目录: `backend_api_python/app/screenshots/`

## 测试验证

### 1. 测试监控功能
```bash
cd backend_api_python
python -c "
from app.services.hama_brave_monitor_mysql import get_brave_monitor
monitor = get_brave_monitor()
result = monitor.monitor_symbol('BTCUSDT')
print(result['screenshot_path'])
print(result['screenshot_absolute_path'])
"
```

### 2. 测试截图访问
```bash
curl -I "http://localhost:5000/screenshot/hama_brave_BTCUSDT_1768727957.png"
```

预期输出:
```
HTTP/1.1 200 OK
Content-Type: image/png
Content-Length: 19148
```

### 3. 测试前端显示
1. 访问 http://localhost:8000/#/hama-market
2. 查看 "HAMA截图" 列
3. 点击 `[+]` 展开截图
4. 确认截图正常显示

## 总结

问题的根源是从 Redis 切换到 SQLite 后，截图管理逻辑发生了变化：
- **Redis 版本**: 截图以 base64 或二进制形式存储在 Redis 中
- **SQLite 版本**: 只存储路径，需要保留文件在文件系统中

修复的关键点：
1. ✅ 截图保存到正确目录 `app/screenshots/`
2. ✅ 不删除截图文件
3. ✅ 静态文件服务路径正确
4. ✅ 数据库保存相对路径供前端访问

现在截图功能已完全恢复正常！🎉
