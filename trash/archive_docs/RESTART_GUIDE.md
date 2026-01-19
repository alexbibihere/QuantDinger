# QuantDinger 服务重启指南

## 方法一：使用自动重启脚本（推荐）

### Windows 用户

直接双击运行项目根目录下的 **`restart_services.bat`** 文件。

脚本会自动：
1. 停止现有的后端和前端服务
2. 启动后端服务（在新窗口）
3. 等待 5 秒
4. 启动前端服务（在新窗口）

---

## 方法二：手动重启

### 步骤 1: 停止现有服务

**Windows**:
```bash
# 停止后端
taskkill /F /IM python.exe

# 停止前端
taskkill /F /IM node.exe
```

或者在每个服务的窗口中按 `Ctrl+C`

---

### 步骤 2: 启动后端服务

打开**第一个命令行窗口**：

```bash
# 进入后端目录
cd d:\github\QuantDinger\backend_api_python

# 启动后端
python run.py
```

等待看到类似以下输出：
```
QuantDinger Python API v2.0.0
Service starting at: http://0.0.0.0:5000
 * Running on http://0.0.0.0:5000
```

**保持此窗口打开**，不要关闭。

---

### 步骤 3: 启动前端服务

打开**第二个命令行窗口**：

```bash
# 进入前端目录
cd d:\github\QuantDinger\quantdinger_vue

# 启动前端
npm run serve
```

等待看到类似以下输出：
```
  App running at:
  - Local:   http://localhost:8000/
  - Network: http://192.168.x.x:8000/
```

**保持此窗口打开**，不要关闭。

---

## 验证服务是否正常启动

### 测试后端

在浏览器或使用 curl 访问：
```
http://localhost:5000/health
```

应该返回：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-08T..."
}
```

### 测试前端

在浏览器访问：
```
http://localhost:8000
```

应该看到 QuantDinger 的登录页面。

---

## 验证接口修复

服务重启后，运行验证脚本：

```bash
cd d:\github\QuantDinger
python verify_fixes.py
```

应该看到：
```
============================================================
                    验证结果汇总
============================================================

K 线接口              ✓ 通过
回测接口              ✓ 通过
指标接口              ✓ 通过

总计: 3/3 个接口修复成功

🎉 所有接口修复成功！
```

---

## 运行完整测试

```bash
cd d:\github\QuantDinger
python test_apis_fixed.py
```

预期结果：**22/22 接口测试通过 (100%)**

---

## 常见问题

### Q1: 后端启动失败，提示端口被占用

**解决方案**:
```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :5000

# 记下 PID，然后强制结束
taskkill /F /PID <PID号>
```

### Q2: 前端启动失败，提示端口 8000 被占用

**解决方案**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID号>
```

### Q3: npm 命令不存在

**解决方案**:
```bash
# 检查 Node.js 是否安装
node --version
npm --version

# 如果未安装，从 https://nodejs.org/ 下载安装
```

### Q4: Python 命令不存在

**解决方案**:
```bash
# 检查 Python 是否安装
python --version

# 如果未安装，从 https://www.python.org/ 下载安装
```

### Q5: 验证脚本运行失败

**可能原因**:
1. 后端未完全启动 - 等待 5-10 秒后再试
2. 前端未启动 - 不影响后端 API 测试
3. 端口配置不同 - 检查 `BASE_URL` 是否正确

---

## 下一步

服务重启并验证成功后：

1. ✅ 登录系统 (用户名: quantdinger, 密码: 123456)
2. ✅ 测试指标分析页面 (K 线图应该正常显示)
3. ✅ 测试回测功能 (回测历史应该可以查看)
4. ✅ 测试策略管理 (所有接口应该正常工作)

---

## 需要帮助？

如果遇到问题，请检查：
1. 后端日志窗口中的错误信息
2. 前端日志窗口中的错误信息
3. 浏览器控制台 (F12) 中的错误信息

---

**创建时间**: 2026-01-08
**适用版本**: QuantDinger v2.0.0
