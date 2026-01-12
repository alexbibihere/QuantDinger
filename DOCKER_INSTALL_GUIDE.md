# 🐳 Docker Desktop 下载和安装完整指南

## 📥 方法1: 自动下载安装 (推荐) ⭐

### 使用自动安装脚本

1. **找到文件**: `d:\github\QuantDinger\install_docker.bat`
2. **右键点击** → **"以管理员身份运行"**
3. **等待自动下载和安装**
4. **按照提示完成后续步骤**

**脚本会自动完成:**
- ✅ 检查是否已安装Docker
- ✅ 下载最新版Docker Desktop
- ✅ 启动安装程序
- ✅ 验证安装是否成功
- ✅ 引导部署QuantDinger

---

## 📥 方法2: 手动下载安装

### 步骤1: 下载Docker Desktop

**选项A: 官网下载**
```
https://www.docker.com/products/docker-desktop/
```
1. 访问上述网址
2. 点击 **"Download for Windows"**
3. 等待下载完成(约500MB)

**选项B: 直接下载链接**
```
https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
```

**选项C: 微软商店**
1. 打开 **Microsoft Store**
2. 搜索 **"Docker Desktop"**
3. 点击 **"获取"** 或 **"安装"**

---

### 步骤2: 安装Docker Desktop

1. **双击运行** 安装程序
   - `Docker Desktop Installer.exe`

2. **安装配置** (推荐)
   - ✅ 勾选 **"Use WSL 2 instead of Hyper-V"**
   - ✅ 勾选 **"Add shortcut to desktop"**
   - 点击 **OK**

3. **等待安装完成**
   - 安装时间: 2-5分钟
   - 可能需要重启电脑

4. **重启电脑** (如果提示)
   - 保存所有工作
   - 点击重启

---

### 步骤3: 启动和初始化

1. **启动Docker Desktop**
   - 双击桌面图标
   - 或在开始菜单搜索"Docker Desktop"

2. **接受服务协议**
   - 阅读协议条款
   - 点击接受

3. **等待启动完成**
   - 查看系统托盘(右下角)
   - 等待鲸鱼图标出现且不再闪烁
   - 通常需要30秒-2分钟

4. **可选配置**
   - 是否发送使用统计(建议选不发送)
   - 是否自动启动(建议选不自动启动)

---

### 步骤4: 验证安装

**打开命令提示符:**
```cmd
docker --version
```

**预期输出:**
```
Docker version 24.x.x
```

**检查Docker状态:**
```cmd
docker info
```

**预期输出:**
```
Client: Docker Engine - Community
 Version:    24.x.x
 ...
```

如果看到版本信息,说明安装成功! ✅

---

## 🚀 安装完成后立即部署 QuantDinger

### 方法A: 一键部署 (最简单)

1. **进入目录**: `d:\github\QuantDinger`
2. **右键点击** `一键部署.bat`
3. **选择** "以管理员身份运行"
4. **等待2-3分钟**自动完成
5. **访问**: http://localhost:8888/hama-monitor

### 方法B: PowerShell部署

1. **按 Win + X**
2. **选择** "Windows PowerShell (管理员)"
3. **运行命令**:
   ```powershell
   cd d:\github\QuantDinger
   docker compose down
   docker compose build
   docker compose up -d
   ```
4. **等待完成后访问**:
   - 前端: http://localhost:8888
   - HAMA监控: http://localhost:8888/hama-monitor

---

## 🔧 常见问题解决

### 问题1: WSL 2 未安装

**错误信息:**
```
WSL 2 is required
```

**解决方法:**

1. **下载WSL 2更新包**:
   ```
   https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
   ```

2. **双击运行**安装程序

3. **重启Docker Desktop**

---

### 问题2: Hyper-V 未启用

**解决方法:**

1. **以管理员身份运行PowerShell**

2. **启用WSL功能**:
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   ```

3. **启用虚拟机平台**:
   ```powershell
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

4. **重启电脑**

---

### 问题3: 虚拟化未启用

**检查方法:**

1. **按 Ctrl + Shift + Esc** 打开任务管理器
2. 点击 **"性能"** 标签
3. 点击 **"CPU"**
4. 查看 **"虚拟化"** 是否显示"已启用"

**如果未启用:**

1. **重启电脑进入BIOS**
   - 不同电脑按键不同(DEL/F2/F10/F12)
   - 开机时连续按对应按键

2. **找到虚拟化设置**
   - Intel: **Intel VT-x** 或 **Intel Virtualization Technology**
   - AMD: **AMD-V** 或 **SVM Mode**

3. **启用虚拟化**
   - 设置为 **Enabled**
   - 保存并退出(通常按F10)

4. **重启电脑**

---

### 问题4: 下载失败

**可能原因:**
- 网络连接问题
- 防火墙阻止下载
- 下载服务器暂时不可用

**解决方法:**

**方法1: 使用浏览器下载**
```
https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
```
保存到: `C:\Users\你的用户名\Downloads\`

**方法2: 使用镜像下载**
- 阿里云镜像: https://mirrors.aliyun.com/docker-toolbox/windows/
- 清华镜像: https://mirrors.tuna.tsinghua.edu.cn/docker-toolbox/windows/

**方法3: 使用微软商店**
- 打开Microsoft Store
- 搜索"Docker Desktop"
- 点击安装

---

### 问题5: 安装后Docker无法启动

**解决方法:**

1. **检查WSL 2是否正确安装**
   ```powershell
   wsl --list --verbose
   ```

2. **手动安装WSL 2更新**
   ```
   https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
   ```

3. **重启Docker Desktop**

4. **检查Windows版本**
   - Windows 10 版本 1903 或更高
   - Windows 11 任意版本

5. **更新Windows**
   - 设置 → 更新和安全 → 检查更新

---

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10 64位 (专业版、企业版、教育版)
- **版本**: 版本 1903 或更高
- **内存**: 至少 4GB RAM
- **硬盘**: 至少 4GB 可用空间

### 推荐配置
- **操作系统**: Windows 11 任意版本
- **内存**: 8GB+ RAM
- **硬盘**: SSD, 20GB+ 可用空间
- **CPU**: 支持虚拟化的双核处理器

### 不支持的版本
- Windows 10 家庭版 (需要升级到专业版)
- Windows 7/8/8.1
- Windows 10 32位系统

---

## 📊 快速参考

### 下载链接
- **官网**: https://www.docker.com/products/docker-desktop/
- **直接下载**: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
- **WSL 2更新**: https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

### 验证命令
```cmd
docker --version
docker info
docker compose version
```

### 部署QuantDinger
```cmd
cd d:\github\QuantDinger
docker compose down
docker compose build
docker compose up -d
```

### 访问地址
- **前端**: http://localhost:8888
- **HAMA监控**: http://localhost:8888/hama-monitor
- **涨幅榜分析**: http://localhost:8888/gainer-analysis

---

## ✅ 安装检查清单

安装完成后,请确认以下项目:

- [ ] Docker Desktop 已安装
- [ ] Docker Desktop 正在运行 (系统托盘有鲸鱼图标)
- [ ] `docker --version` 可以正常执行
- [ ] `docker info` 可以正常执行
- [ ] `docker compose version` 可以正常执行
- [ ] 在 `d:\github\QuantDinger` 目录下
- [ ] 准备运行 `一键部署.bat`

---

## 🎯 下一步操作

1. **验证Docker安装**
   ```cmd
   docker --version
   docker info
   ```

2. **运行QuantDinger部署**
   ```bash
   # 方法1: 双击运行
   一键部署.bat

   # 方法2: PowerShell
   cd d:\github\QuantDinger
   docker compose down && docker compose build && docker compose up -d
   ```

3. **访问应用**
   - 前端: http://localhost:8888
   - HAMA监控: http://localhost:8888/hama-monitor
   - 登录: quantdinger / 123456

4. **启动HAMA监控**
   - 点击"启动监控"
   - 点击"添加涨幅榜"
   - 等待信号产生

---

## 📞 获取帮助

### Docker官方文档
- [Docker Desktop 文档](https://docs.docker.com/desktop/windows/)
- [Docker 安装指南](https://docs.docker.com/engine/install/)
- [WSL 2 文档](https://docs.microsoft.com/en-us/windows/wsl/)

### 如果遇到问题

1. **查看Docker日志**
   - Docker Desktop → 菜单 → Troubleshoot → Logs

2. **运行诊断**
   - Docker Desktop → 菜单 → Troubleshoot → Diagnose

3. **重置Docker**
   - Docker Desktop → 菜单 → Troubleshoot → Clean/Purge data

4. **查看QuantDinger文档**
   - [快速开始.md](快速开始.md)
   - [HAMA_MONITOR_QUICKSTART.md](HAMA_MONITOR_QUICKSTART.md)

---

**祝您安装顺利!** 🐳

安装完成后,立即开始使用HAMA信号监控系统! 🚀
