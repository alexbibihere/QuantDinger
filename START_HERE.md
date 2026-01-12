# 🎯 一键部署指南 - 涨幅榜分析功能

## 📍 你现在的位置

你已经在 `d:\github\QuantDinger` 目录下

## 🚀 最简单的部署方法 (3选1)

### ⭐ 方法 1: 双击运行 (最简单!)

1. 在当前文件夹中找到 **`restart_services.bat`** 文件
2. **右键点击** → **"以管理员身份运行"**
3. 在弹出窗口中选择 `N` (不清理旧镜像,更快)
4. 等待 2-3 分钟自动完成
5. 看到"部署完成!"后,访问 http://localhost:8888/gainer-analysis

---

### ⭐ 方法 2: PowerShell 脚本 (推荐)

1. **按 `Win + X` 键**
2. 选择 **"Windows PowerShell (管理员)"**
3. 复制以下命令,粘贴,回车:

```powershell
cd d:\github\QuantDinger; docker-compose down; docker-compose build; docker-compose up -d; Start-Sleep -Seconds 5; docker-compose ps
```

4. 等待完成后访问 http://localhost:8888/gainer-analysis

---

### ⭐ 方法 3: 使用 CMD 命令提示符

1. **按 `Win + R` 键**
2. 输入 `cmd` 并回车
3. 复制以下命令,粘贴,回车:

```cmd
cd /d d:\github\QuantDinger && docker-compose down && docker-compose build && docker-compose up -d
```

4. 等待完成后访问 http://localhost:8888/gainer-analysis

---

## ✅ 验证部署是否成功

### 1. 检查容器状态

在命令行中输入:
```cmd
docker-compose ps
```

**预期结果:** 应该看到两个容器都是 "Up" 状态

### 2. 测试后端健康

浏览器打开:
```
http://localhost:5000/api/health
```

**预期结果:** 看到 `{"status":"healthy","timestamp":"..."}`

### 3. 访问涨幅榜页面

浏览器打开:
```
http://localhost:8888/gainer-analysis
```

**预期结果:** 显示涨幅榜分析页面

---

## 🎉 部署成功后的下一步

### 1. 登录系统

- 用户名: `quantdinger`
- 密码: `123456`

### 2. 使用涨幅榜分析

- 选择市场类型 (现货/合约)
- 点击"刷新"按钮获取数据
- 查看 HAMA 分析结果
- 点击"详情"查看完整分析

### 3. 测试功能

运行测试脚本验证:
```cmd
python test_hama_real_data.py
```

---

## 🐛 如果遇到问题

### 问题 1: 端口被占用

**解决:** 修改端口或结束占用进程
```cmd
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F
```

### 问题 2: Docker 未运行

**解决:**
- 打开 Docker Desktop
- 等待 Docker 完全启动
- 重新运行部署脚本

### 问题 3: 容器启动失败

**解决:** 查看日志
```cmd
docker-compose logs backend
```

---

## 📖 详细文档

如果需要更详细的说明,请查看:
- [DEPLOY_STEP_BY_STEP.md](DEPLOY_STEP_BY_STEP.md) - 详细步骤
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - 完整指南
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 检查清单

---

## 💡 推荐流程

1. **启动 Docker Desktop** (确保正在运行)
2. **双击运行** `restart_services.bat` (选择 N)
3. **等待 2-3 分钟** (自动部署)
4. **浏览器访问** http://localhost:8888/gainer-analysis
5. **开始使用!** 🎉

---

**准备好了吗? 选择一种方法开始部署吧!**

**最推荐: 双击 `restart_services.bat` → 选择 N → 等待完成!**
