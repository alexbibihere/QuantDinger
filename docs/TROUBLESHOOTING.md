# 🔧 Docker 部署问题排查和解决

## 问题: restart_services.bat 无法启动

### 可能的原因和解决方案

---

## 原因 1: choice 命令兼容性问题

**解决方案:** 使用简化版脚本

我刚创建了一个简化版脚本: **`DEPLOY_SIMPLE.bat`**

**使用方法:**
1. 在文件管理器中找到 `d:\github\QuantDinger\DEPLOY_SIMPLE.bat`
2. 右键点击 → **"以管理员身份运行"**
3. 等待自动完成

---

## 原因 2: Docker 未正确安装或未运行

**检查方法:**

打开命令提示符(CMD)或PowerShell,输入:
```cmd
docker --version
docker info
```

**解决方案:**

1. **启动 Docker Desktop**
   - 在开始菜单找到 "Docker Desktop"
   - 点击启动
   - 等待鲸鱼图标出现在系统托盘
   - 等待 Docker 完全启动(约30秒)

2. **验证 Docker 运行**
   ```cmd
   docker info
   ```
   如果看到 Docker 信息输出,说明已成功启动

3. **重新运行部署脚本**

---

## 原因 3: 权限不足

**解决方案:**

1. **右键点击** `DEPLOY_SIMPLE.bat`
2. 选择 **"以管理员身份运行"**
3. 如果提示 UAC,点击"是"

---

## 原因 4: 路径问题

**检查方法:**

确认你在正确的目录:
- `d:\github\QuantDinger`
- 应该能看到 `docker-compose.yml` 文件

**解决方案:**

打开命令提示符,手动执行:
```cmd
cd /d d:\github\QuantDinger
dir docker-compose.yml
```

如果看到文件,继续执行:
```cmd
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 原因 5: docker-compose 命令不存在

**检查方法:**

```cmd
docker-compose --version
```

**解决方案:**

新版本 Docker 使用 `docker compose` (没有连字符)

创建新文件 `DEPLOY_NEW.bat`:
```batch
@echo off
echo 正在部署 QuantDinger...
docker compose down
docker compose build
docker compose up -d
echo.
echo 部署完成!
echo 前端: http://localhost:8888
pause
```

然后运行:
```cmd
DEPLOY_NEW.bat
```

---

## 🎯 最简单的手动部署步骤

如果脚本都无法运行,请手动执行以下步骤:

### 步骤 1: 打开 PowerShell (管理员)

1. 按 `Win + X` 键
2. 选择 "Windows PowerShell (管理员)"

### 步骤 2: 进入项目目录

```powershell
cd d:\github\QuantDinger
```

### 步骤 3: 停止旧容器

```powershell
docker-compose down
```

或者:
```powershell
docker compose down
```

### 步骤 4: 构建镜像

```powershell
docker-compose build
```

或者:
```powershell
docker compose build
```

### 步骤 5: 启动服务

```powershell
docker-compose up -d
```

或者:
```powershell
docker compose up -d
```

### 步骤 6: 验证部署

```powershell
docker-compose ps
```

或访问:
```
http://localhost:5000/api/health
```

---

## 🐛 常见错误和解决

### 错误 1: "docker-compose" 不是内部或外部命令

**原因:** 使用的是新版 Docker (需要 `docker compose`)

**解决:** 创建 `DEPLOY_NEW.bat` 使用 `docker compose` 命令

### 错误 2: "Cannot connect to the Docker daemon"

**原因:** Docker Desktop 未运行

**解决:**
1. 启动 Docker Desktop
2. 等待完全启动
3. 重新运行命令

### 错误 3: "port is already allocated"

**原因:** 端口 5000 或 8888 被占用

**解决:**

查找并结束占用进程:
```cmd
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F
```

或修改 `docker-compose.yml` 中的端口映射

### 错误 4: 构建失败 - 依赖安装错误

**原因:** requirements.txt 或网络问题

**解决:**
1. 检查 `requirements.txt` 是否包含 `numpy>=1.24.0`
2. 检查网络连接
3. 清理缓存重新构建:
```cmd
docker-compose build --no-cache
```

---

## 📝 完整的手动部署命令

复制以下所有命令到 PowerShell (管理员):

```powershell
# 设置错误动作
$ErrorActionPreference = "Stop"

# 进入目录
Set-Location d:\github\QuantDinger

# 停止容器
Write-Host "停止容器..." -ForegroundColor Yellow
docker compose down

# 构建镜像
Write-Host "构建镜像..." -ForegroundColor Yellow
docker compose build

# 启动服务
Write-Host "启动服务..." -ForegroundColor Yellow
docker compose up -d

# 等待启动
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查状态
Write-Host "检查状态..." -ForegroundColor Yellow
docker compose ps

# 测试健康
Write-Host "测试后端健康..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[成功] 后端健康检查通过!" -ForegroundColor Green
    }
} catch {
    Write-Host "[警告] 后端可能还在启动中" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "部署完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "前端地址: http://localhost:8888" -ForegroundColor White
Write-Host "后端地址: http://localhost:5000" -ForegroundColor White
Write-Host "涨幅榜分析: http://localhost:8888/gainer-analysis" -ForegroundColor Cyan
Write-Host ""
Write-Host "按回车键退出..."
$null = Read-Host
```

---

## ✅ 部署成功验证

### 1. 检查容器

```cmd
docker-compose ps
```

应该看到:
```
NAME                      STATUS
quantdinger-backend       Up (healthy)
quantdinger-frontend      Up (healthy)
```

### 2. 浏览器访问

```
http://localhost:8888/gainer-analysis
```

### 3. 运行测试

```cmd
python test_hama_real_data.py
```

---

## 💡 推荐操作流程

1. **启动 Docker Desktop** (确保运行)

2. **打开 PowerShell (管理员)**
   - 按 `Win + X`
   - 选择 "Windows PowerShell (管理员)"

3. **进入项目目录**
   ```powershell
   cd d:\github\QuantDinger
   ```

4. **运行部署命令**
   ```powershell
   docker compose down
   docker compose build
   docker compose up -d
   ```

5. **等待完成**
   - 构建需要 2-3 分钟
   - 首次可能需要 5-10 分钟

6. **访问应用**
   ```
   http://localhost:8888/gainer-analysis
   ```

---

## 📞 还是有问题?

### 检查清单

- [ ] Docker Desktop 已安装
- [ ] Docker Desktop 正在运行
- [ ] 在 `d:\github\QuantDinger` 目录下
- [ ] `requirements.txt` 包含 `numpy>=1.24.0`
- [ ] 以管理员身份运行脚本
- [ ] 端口 5000 和 8888 未被占用

### 获取帮助

查看详细日志:
```cmd
docker-compose logs backend
```

查看完整文档:
- [START_HERE.md](START_HERE.md)
- [DEPLOY_STEP_BY_STEP.md](DEPLOY_STEP_BY_STEP.md)
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

**现在可以试试:**
1. 使用 `DEPLOY_SIMPLE.bat` (简化版)
2. 或手动执行 PowerShell 命令 (最可靠)
