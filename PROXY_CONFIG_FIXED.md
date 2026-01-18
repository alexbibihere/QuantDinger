# ✅ 代理配置已修复

## 修改内容

### 1. 修复 `.env` 代理配置 ✅

**修改前 (❌ 有问题)**:
```bash
PROXY_PORT=7890
PROXY_HOST=127.0.0.1
PROXY_SCHEME=socks5h
PROXY_URL=  # 空值导致错误
```

**修改后 (✅ 已修复)**:
```bash
PROXY_PORT=7890
PROXY_HOST=127.0.0.1
PROXY_SCHEME=socks5h
PROXY_URL=socks5h://127.0.0.1:7890  # 使用完整格式
CCXT_PROXY=socks5h://127.0.0.1:7890
```

### 2. 修改 OCR 提取器代理使用 ✅

修改 [`hama_ocr_extractor.py`](backend_api_python/app/services/hama_ycr_extractor.py) 中的 `capture_chart` 方法,支持 SOCKS5 代理:

```python
# 获取代理配置
proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')

# 转换为 Playwright 格式
if 'socks5h://' in proxy_url:
    # socks5h://host:port -> --proxy-server=host:port
    parts = proxy_url.replace('socks5h://', '').split(':')
    host = parts[0]
    port = parts[1] if len(parts) > 1 else '7890'
    proxy_config = f"--proxy-server={host}:{port}"
elif '://' in proxy_url:
    # http://host:port -> --proxy-server=host:port
    parts = proxy_url.split('://')[1].split(':')
    host = parts[0]
    port = parts[1] if len(parts) > 1 else '7890'
    proxy_config = f"--proxy-server={host}:{port}"

# 使用代理配置
args = ['--no-sandbox', '--disable-dev-shm-usage']
if proxy_config:
    args.append(proxy_config)
    browser = p.chromium.launch(
        headless=True,
        args=args
    )
```

## 🚀 重启后端使修复生效

```bash
cd backend_api_python
python run.py
```

## 📊 预期效果

重启后端后:

1. ✅ **代理正常工作**
   - 不再有 `ERR_NO_SUPPORTED_PROXIES` 错误
   - Playwright 能正常访问 TradingView

2. ✅ **Worker 自动监控**
   - Worker 会重新尝试监控
   - 成功截图并保存到数据库

3. ✅ **截图文件生成**
   - 保存到 `backend_api_python/screenshots/` 目录
   - 文件名格式: `hama_brave_{symbol}_{timestamp}.png`

4. ✅ **前端显示截图**
   - API 返回截图 URL
   - 前端展示截图供比对

## 🔄 验证步骤

### 1. 重启后端
```bash
cd backend_api_python
python run.py
```

### 2. 查看日志 (应该不再有代理错误)
```bash
# 日志会显示:
✅ 使用 SOCKS5 代理: 127.0.0.1:7890
正在截图 BTCUSDT...
✅ BTCUSDT HAMA 状态: red (down)
```

### 3. 检查截图文件
```bash
cd backend_api_python/screenshots
ls -lh | grep "hama_brave.*\.png"
```

### 4. 访问前端
http://localhost:8000/#/hama-market

应该能看到:
- ✅ HAMA 数据
- ✅ 截图预览
- ✅ 查看大图按钮

---

**修复状态**: ✅ 代理配置已修复
**等待**: 重启后端服务
**最后更新**: 2026-01-18
