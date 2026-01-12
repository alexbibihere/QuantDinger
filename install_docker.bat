@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    Docker Desktop 自动下载安装
echo ========================================
echo.
echo 此脚本将:
echo 1. 下载 Docker Desktop 安装程序
echo 2. 自动运行安装
echo 3. 提供安装指引
echo.
pause

REM 设置下载URL
set DOCKER_URL=https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
set INSTALLER_FILE="%USERPROFILE%\Downloads\DockerDesktopInstaller.exe"

REM 检查是否已安装
echo.
echo [1/4] 检查是否已安装 Docker Desktop...
where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 检测到 Docker 已安装
    docker --version
    echo.
    choice /C YN /M "是否跳过安装直接部署 QuantDinger"
    if errorlevel 2 goto :run_deploy
    if errorlevel 1 goto :download_installer
) else (
    echo   未检测到 Docker,开始下载...
)

:download_installer
echo.
echo [2/4] 下载 Docker Desktop 安装程序...
echo   下载地址: %DOCKER_URL%
echo   保存位置: %INSTALLER_FILE%
echo.

REM 检查是否已有安装文件
if exist %INSTALLER_FILE% (
    echo   发现已有安装文件
    choice /C YN /M "是否重新下载"
    if errorlevel 2 goto :install
    del %INSTALLER_FILE%
)

REM 创建下载目录
if not exist "%USERPROFILE%\Downloads" mkdir "%USERPROFILE%\Downloads"

echo   正在下载,请稍候...
echo   文件大小约 500MB,可能需要几分钟...
echo.

REM 使用 PowerShell 下载
powershell -Command "& {Invoke-WebRequest -Uri '%DOCKER_URL%' -OutFile %INSTALLER_FILE% -UseBasicParsing}"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 下载失败
    echo.
    echo 可能的原因:
    echo 1. 网络连接问题
    echo 2. 防火墙阻止下载
    echo 3. 下载地址无法访问
    echo.
    echo 建议:
    echo 1. 检查网络连接
    echo 2. 手动下载: %DOCKER_URL%
    echo 3. 保存到: %INSTALLER_FILE%
    echo.
    pause
    exit /b 1
)

echo   ✅ 下载完成
echo.

:install
echo [3/4] 安装 Docker Desktop...
echo   安装程序: %INSTALLER_FILE%
echo.
echo 即将启动安装程序,请按照提示操作:
echo.
echo 推荐配置:
echo   ✓ 勾选 "Use WSL 2 instead of Hyper-V"
echo   ✓ 勾选 "Add shortcut to desktop"
echo.
echo 安装过程可能需要:
echo   - 2-5 分钟
echo   - 可能需要重启电脑
echo.
pause

start /wait %INSTALLER_FILE%

echo.
echo [4/4] 验证安装...
timeout /t 5 /nobreak >nul

where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Docker Desktop 安装成功!
    echo ========================================
    echo.
    docker --version
    echo.
    echo 下一步:
    echo 1. 启动 Docker Desktop (桌面图标或开始菜单)
    echo 2. 等待 Docker 完全启动 (系统托盘鲸鱼图标不再闪烁)
    echo 3. 运行 QuantDinger 部署脚本
    echo.
    echo 按任意键启动 Docker Desktop...
    pause >nul

    REM 尝试启动 Docker Desktop
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    echo.
    echo Docker Desktop 正在启动...
    echo 请等待约30秒-2分钟
    echo.
    echo 启动完成后,请运行以下命令验证:
    echo   docker info
    echo.

    goto :run_deploy
) else (
    echo.
    echo ========================================
    echo ⚠️ Docker 可能未正确安装
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. 安装未完成
    echo 2. 需要重启电脑
    echo 3. Docker Desktop 未启动
    echo.
    echo 建议操作:
    echo 1. 重启电脑
    echo 2. 手动启动 Docker Desktop
    echo 3. 验证安装: docker --version
    echo.
    goto :manual_guide
)

:run_deploy
echo.
echo ========================================
echo 准备部署 QuantDinger
echo ========================================
echo.
echo Docker 安装完成! 现在可以部署 QuantDinger 了
echo.
echo 选择部署方式:
echo   1. 运行一键部署脚本 (推荐)
echo   2. 查看手动部署说明
echo   3. 退出
echo.
choice /C 123 /M "请选择"
if errorlevel 3 goto :end
if errorlevel 2 goto :manual_deploy
if errorlevel 1 goto :auto_deploy

:auto_deploy
echo.
echo 启动一键部署...
echo.
if exist "一键部署.bat" (
    start "" cmd /k "一键部署.bat"
) else (
    echo.
    echo ❌ 未找到 一键部署.bat
    echo.
    echo 请手动运行:
    echo   docker compose down
    echo   docker compose build
    echo   docker compose up -d
    echo.
)
goto :end

:manual_deploy
echo.
echo ========================================
echo 手动部署步骤
echo ========================================
echo.
echo 1. 确认 Docker Desktop 正在运行
echo    - 查看系统托盘是否有鲸鱼图标
echo    - 运行命令: docker info
echo.
echo 2. 打开 PowerShell (管理员)
echo    - 按 Win + X
echo    - 选择 "Windows PowerShell (管理员)"
echo.
echo 3. 进入项目目录
echo    cd d:\github\QuantDinger
echo.
echo 4. 运行部署命令
echo    docker compose down
echo    docker compose build
echo    docker compose up -d
echo.
echo 5. 访问应用
echo    前端: http://localhost:8888
echo    HAMA监控: http://localhost:8888/hama-monitor
echo.
pause
goto :end

:manual_guide
echo.
echo ========================================
echo 手动下载和安装指南
echo ========================================
echo.
echo 方法1: 官网下载
echo   访问: https://www.docker.com/products/docker-desktop/
echo   点击 "Download for Windows"
echo.
echo 方法2: 直接下载链接
echo   %DOCKER_URL%
echo.
echo 方法3: 微软商店
echo   打开 Microsoft Store
echo   搜索 "Docker Desktop"
echo   点击安装
echo.
echo 安装步骤:
echo   1. 双击运行下载的安装程序
echo   2. 勾选 "Use WSL 2 instead of Hyper-V"
echo   3. 点击 OK 等待安装完成
echo   4. 重启电脑 (如果提示)
echo   5. 启动 Docker Desktop
echo   6. 等待初始化完成 (约1-2分钟)
echo.
echo 验证安装:
echo   打开命令提示符,运行:
echo   docker --version
echo   docker info
echo.
echo 安装成功后,运行: 一键部署.bat
echo.
pause

:end
echo.
echo 感谢使用!
echo.
