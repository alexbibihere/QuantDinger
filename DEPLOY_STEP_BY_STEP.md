# 🚀 Docker 部署 - 逐步操作指南

## 准备工作

在开始之前，请确保：
- ✅ Docker Desktop 已安装并正在运行
- ✅ 在 `d:\github\QuantDinger` 目录下
- ✅ `backend_api_python/.env` 文件已配置

---

## 方法 1: 使用 Windows CMD (推荐新手)

### 步骤 1: 打开命令提示符

1. 按 `Win + R` 键
2. 输入 `cmd` 并按回车
3. 在命令提示符中输入:

```cmd
cd /d d:\github\QuantDinger
```

### 步骤 2: 停止旧容器

```cmd
docker-compose down
```

### 步骤 3: 构建镜像

```cmd
docker-compose build
```

等待构建完成（可能需要 2-3 分钟）

### 步骤 4: 启动服务

```cmd
docker-compose up -d
```

### 步骤 5: 验证部署

```cmd
docker-compose ps
```

应该看到两个容器都是 "Up" 状态

---

## 方法 2: 使用 PowerShell (推荐)

### 步骤 1: 打开 PowerShell

1. 在 `d:\github\QuantDinger` 文件夹中
2. 按住 `Shift` 键
3. 右键点击空白处
4. 选择"在此处打开 PowerShell 窗口"

### 步骤 2: 运行部署命令

复制以下所有命令，粘贴到 PowerShell，按回车:

```powershell
# 进入目录
Set-Location d:\github\QuantDinger

# 停止旧容器
docker compose down

# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 等待 5 秒
Start-Sleep -Seconds 5

# 检查状态
docker compose ps
```

---

## 方法 3: 使用脚本文件 (最简单)

### Windows 批处理文件

1. 找到文件: `d:\github\QuantDinger\restart_services.bat`
2. **右键点击** -> **"以管理员身份运行"**
3. 按照提示操作
4. 选择是否清理旧镜像 (建议输入 `N`)

### PowerShell 脚本文件

1. 找到文件: `d:\github\QuantDinger\deploy.ps1`
2. 右键点击 -> "使用 PowerShell 运行"
3. 如果提示权限问题，选择"以管理员身份运行"

---

## 方法 4: 使用 Docker Desktop GUI

### 步骤 1: 启动 Docker Desktop

确保 Docker Desktop 正在运行

### 步骤 2: 打开终端

- 在 Docker Desktop 中，点击右上角的 **终端图标**
- 或者在项目目录按住 Shift 右键，选择"在此处打开命令窗口"

### 步骤 3: 运行命令

```bash
cd d:/github/QuantDinger
docker compose up -d --build
```

### 步骤 4: 查看容器

- 在 Docker Desktop 左侧菜单点击 **"Containers"**
- 应该看到 `quantdinger-backend` 和 `quantdinger-frontend`
- 状态应该显示为 **"Running"** 或 **"Up"**

---

## ✅ 验证部署

### 1. 检查容器状态

**PowerShell/CMD:**
```powershell
docker compose ps
```

**预期输出:**
```
NAME                      STATUS          PORTS
quantdinger-backend       Up (healthy)    0.0.0.0:5000->5000/tcp
quantdinger-frontend      Up (healthy)    0.0.0.0:8888->80/tcp
```

### 2. 测试后端 API

**浏览器访问:**
```
http://localhost:5000/api/health
```

**应该看到:**
```json
{"status":"healthy","timestamp":"2025-01-09T..."}
```

### 3. 访问前端应用

**浏览器打开:**
```
http://localhost:8888
```

**然后访问涨幅榜分析:**
```
http://localhost:8888/gainer-analysis
```

### 4. 运行测试脚本

```powershell
python test_hama_real_data.py
```

---

## 🐛 常见问题解决

### 问题 1: 端口被占用

**错误信息:**
```
Error: bind: address already in use
```

**解决方法:**

查找占用端口的进程:
```cmd
netstat -ano | findstr :5000
netstat -ano | findstr :8888
```

结束进程:
```cmd
taskkill /PID <进程ID> /F
```

或者修改 `docker-compose.yml`:
```yaml
ports:
  - "5001:5000"  # 改成其他端口
  - "8889:80"    # 改成其他端口
```

### 问题 2: 依赖安装失败

**检查 requirements.txt:**
```cmd
type backend_api_python\requirements.txt
```

**确认包含:**
```
numpy>=1.24.0
ccxt>=4.0.0
```

**手动安装:**
```cmd
docker exec -it quantdinger-backend pip install numpy
```

### 问题 3: 容器启动失败

**查看详细日志:**
```powershell
docker compose logs backend
docker compose logs frontend
```

**完全重建:**
```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 问题 4: 权限错误 (PowerShell)

**错误:**
```
无法加载文件，因为在此系统上禁止运行脚本
```

**解决:**

以管理员身份运行 PowerShell:
1. 按 `Win + X`
2. 选择"Windows PowerShell (管理员)"
3. 运行命令:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

然后再次运行 `.\deploy.ps1`

---

## 📊 部署成功后的下一步

### 1. 访问应用

**浏览器打开:**
```
http://localhost:8888/gainer-analysis
```

### 2. 登录系统

- 用户名: `quantdinger`
- 密码: `123456`

### 3. 使用涨幅榜分析

- 选择市场类型 (现货/合约)
- 点击"刷新"按钮
- 查看 HAMA 分析结果
- 点击"详情"查看完整分析

### 4. 查看日志

```powershell
# 实时日志
docker compose logs -f backend

# 后端日志
docker compose logs backend --tail=100
```

---

## 🎯 快速命令备忘

```powershell
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 进入容器
docker exec -it quantdinger-backend bash

# 重建并启动
docker compose down
docker compose build
docker compose up -d
```

---

## 💡 提示

1. **首次部署**需要下载镜像，可能需要 5-10 分钟
2. **数据加载**需要时间，首次访问可能需要 10-30 秒
3. **查看日志**可以帮助诊断问题
4. **代理配置**可以提高数据获取成功率

---

## 📞 需要帮助?

如果遇到问题:
1. 查看 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
2. 查看 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
3. 检查日志: `docker compose logs backend`
4. 运行测试: `python test_hama_real_data.py`

---

**准备好了吗? 选择一种方法开始部署吧! 🚀**
