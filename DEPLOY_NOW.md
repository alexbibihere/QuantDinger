# 🚀 立即部署指南 - 手动操作步骤

## 方式 1: 使用 PowerShell 脚本 (最简单) ✨

### Windows 用户:

1. **打开 PowerShell**
   - 在 QuantDinger 根目录
   - 按住 Shift 键
   - 右键点击空白处
   - 选择"在此处打开 PowerShell 窗口"

2. **运行部署脚本**
   ```powershell
   .\deploy.ps1
   ```

3. **等待完成**
   - 脚本会自动执行所有步骤
   - 大约需要 2-3 分钟

4. **访问应用**
   - 前端: http://localhost:8888
   - 涨幅榜: http://localhost:8888/gainer-analysis

---

## 方式 2: 使用批处理脚本

1. **双击运行**
   - 找到 `restart_services.bat`
   - 双击运行

2. **按提示操作**
   - 选择是否清理旧镜像 (建议选 N)
   - 等待部署完成

3. **访问应用**
   - 浏览器打开 http://localhost:8888/gainer-analysis

---

## 方式 3: 手动命令行部署

### Windows PowerShell:

```powershell
# 1. 进入项目目录
cd d:\github\QuantDinger

# 2. 停止旧容器
docker compose down

# 3. 构建镜像
docker compose build

# 4. 启动服务
docker compose up -d

# 5. 查看状态
docker compose ps

# 6. 查看日志
docker compose logs -f backend
```

### Windows CMD:

```cmd
# 1. 进入项目目录
cd /d d:\github\QuantDinger

# 2. 停止旧容器
docker-compose down

# 3. 构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps
```

### Linux/Mac Terminal:

```bash
# 1. 进入项目目录
cd ~/github/QuantDinger

# 2. 停止旧容器
docker-compose down

# 3. 构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps
```

---

## 方式 4: 使用 Docker Desktop (图形界面)

1. **打开 Docker Desktop**
   - 确保 Docker 正在运行

2. **打开终端**
   - 点击 Docker Desktop 右上角的终端图标
   - 或者在项目目录打开终端

3. **执行命令**
   ```bash
   cd d:/github/QuantDinger
   docker compose up -d --build
   ```

4. **查看容器**
   - 在 Docker Desktop 左侧菜单点击"Containers"
   - 查看 quantdinger-backend 和 quantdinger-frontend 状态

---

## ✅ 验证部署

### 1. 检查容器状态

**PowerShell/CMD:**
```powershell
docker compose ps
```

**或使用 Docker Desktop:**
- 打开 Docker Desktop
- 查看 Containers 列表
- 状态应该显示为 "Up (healthy)"

### 2. 测试后端

**浏览器访问:**
```
http://localhost:5000/api/health
```

**应该看到:**
```json
{"status":"healthy","timestamp":"..."}
```

**或使用 PowerShell:**
```powershell
curl http://localhost:5000/api/health
```

### 3. 测试涨幅榜 API

**浏览器访问:**
```
http://localhost:5000/api/gainer-analysis/top-gainers?limit=3
```

**应该看到 JSON 数据**

### 4. 访问前端

**浏览器打开:**
```
http://localhost:8888
```

**然后访问涨幅榜:**
```
http://localhost:8888/gainer-analysis
```

---

## 🐛 常见问题解决

### 问题 1: 端口被占用

**错误信息:**
```
Error: bind: address already in use
```

**解决方法:**

**Windows (PowerShell):**
```powershell
# 查看占用端口的进程
netstat -ano | findstr :5000
netstat -ano | findstr :8888

# 结束进程 (替换 PID)
taskkill /PID <进程ID> /F
```

**或修改端口:**
- 编辑 `docker-compose.yml`
- 将 `5000:5000` 改为 `5001:5000`
- 将 `8888:80` 改为 `8889:80`

### 问题 2: 容器启动失败

**检查日志:**
```powershell
docker compose logs backend
docker compose logs frontend
```

**重建镜像:**
```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 问题 3: 依赖安装失败

**检查 requirements.txt:**
```powershell
cat backend_api_python/requirements.txt
```

**确认包含:**
```
numpy>=1.24.0
ccxt>=4.0.0
```

**手动安装依赖:**
```powershell
docker exec -it quantdinger-backend pip install numpy
```

### 问题 4: 网络连接问题

**检查代理配置:**
```powershell
cat backend_api_python/.env
```

**确认配置:**
```
PROXY_PORT=7890
CCXT_DEFAULT_EXCHANGE=okx
```

### 问题 5: 前端页面空白

**清除浏览器缓存:**
- 按 `Ctrl + Shift + Delete`
- 清除缓存和 Cookie
- 刷新页面

**检查前端日志:**
```powershell
docker compose logs frontend
```

**重启前端:**
```powershell
docker compose restart frontend
```

---

## 📊 部署后测试

### 1. 运行算法测试 (离线)

```powershell
python test_hama_algorithm.py
```

**预期输出:**
- ✅ 5个币种分析
- ✅ 趋势判断正确
- ✅ 技术指标准确

### 2. 运行功能测试 (需要后端)

```powershell
python test_hama_real_data.py
```

**预期输出:**
- ✅ TradingView API 测试
- ✅ 登录成功
- ✅ API 测试通过

### 3. 浏览器测试

1. **访问登录页面**
   - http://localhost:8888
   - 用户名: quantdinger
   - 密码: 123456

2. **访问涨幅榜**
   - 点击菜单"涨幅榜分析"
   - 或直接访问 http://localhost:8888/gainer-analysis

3. **验证功能**
   - ✅ 页面正常显示
   - ✅ 统计卡片显示
   - ✅ 币种列表显示
   - ✅ HAMA 分析结果
   - ✅ 详情弹窗正常
   - ✅ TradingView 链接可跳转

---

## 🎯 快速命令参考

### 查看日志
```powershell
# 实时日志
docker compose logs -f backend

# 最近100行
docker compose logs --tail=100 backend
```

### 重启服务
```powershell
# 重启所有
docker compose restart

# 仅重启后端
docker compose restart backend

# 仅重启前端
docker compose restart frontend
```

### 停止服务
```powershell
docker compose down
```

### 进入容器
```powershell
docker exec -it quantdinger-backend bash
```

### 更新代码
```powershell
# 1. 拉取最新代码
git pull

# 2. 重新部署
docker compose down
docker compose up -d --build
```

---

## 📞 获取帮助

### 查看详细文档

1. [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - 完整部署指南
2. [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 检查清单
3. [DOCKER_README.md](DOCKER_README.md) - 部署包总览

### 检查日志位置

**容器日志:**
```powershell
docker compose logs backend > backend_logs.txt
```

**应用日志:**
```powershell
cat backend_api_python/logs/app.log
```

---

## ✨ 推荐部署方式

**最简单:** 双击 `restart_services.bat`

**最可靠:** 使用 PowerShell 脚本 `deploy.ps1`

**最灵活:** 手动执行 Docker 命令

**最直观:** 使用 Docker Desktop 图形界面

---

## 🎉 完成部署

部署成功后:

1. **访问前端:** http://localhost:8888
2. **登录系统:** quantdinger / 123456
3. **打开涨幅榜:** http://localhost:8888/gainer-analysis
4. **开始使用:** 选择市场,刷新数据,查看分析!

---

**准备好了吗? 选择一种方式开始部署吧! 🚀**
