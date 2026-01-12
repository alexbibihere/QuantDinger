# Docker 镜像加速配置脚本
# 配置国内镜像源以加速Docker镜像下载

Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  Docker 镜像加速配置" -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

# 检查Docker Desktop是否在运行
Write-Host "[1/3] 检查Docker状态..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker正在运行" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker未运行,请先启动Docker Desktop" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 无法连接到Docker" -ForegroundColor Red
    exit 1
}

# 配置镜像加速
Write-Host ""
Write-Host "[2/3] 配置镜像加速..." -ForegroundColor Yellow

# Docker Desktop配置路径
$configPath = "$env:APPDATA\Docker\daemon.json"
$configDir = Split-Path $configPath

# 创建配置目录(如果不存在)
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# 配置内容
$daemonConfig = @{
    "registry-mirrors" = @(
        "https://docker.m.daocloud.io",
        "https://docker.1panel.live",
        "https://docker.anyhub.us.kg",
        "https://dockerhub.icu"
    )
    "insecure-registries" = @()
    "experimental" = $false
    "features" = @{
        "buildkit" = $true
    }
}

# 保存配置
$daemonConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8

Write-Host "✓ 配置已保存到: $configPath" -ForegroundColor Green
Write-Host ""
Write-Host "配置的镜像源:" -ForegroundColor Cyan
foreach ($mirror in $daemonConfig["registry-mirrors"]) {
    Write-Host "  - $mirror" -ForegroundColor White
}

# 重启Docker
Write-Host ""
Write-Host "[3/3] 重启Docker..." -ForegroundColor Yellow
Write-Host ""
Write-Host "需要重启Docker Desktop以应用配置" -ForegroundColor Yellow
Write-Host ""
Write-Host "请按以下步骤操作:" -ForegroundColor Cyan
Write-Host "  1. 右键点击系统托盘的Docker图标" -ForegroundColor White
Write-Host "  2. 选择 'Quit Docker Desktop' (退出Docker)" -ForegroundColor White
Write-Host "  3. 等待Docker完全关闭" -ForegroundColor White
Write-Host "  4. 重新启动 Docker Desktop" -ForegroundColor White
Write-Host "  5. 等待Docker完全启动(约30秒)" -ForegroundColor White
Write-Host ""
Write-Host "然后运行部署命令:" -ForegroundColor Yellow
Write-Host "  cd d:\github\QuantDinger" -ForegroundColor White
Write-Host "  docker compose up -d --build" -ForegroundColor White
Write-Host ""

# 询问是否立即重启
$restart = Read-Host "是否立即重启Docker Desktop? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "正在关闭Docker..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

    Write-Host "等待Docker关闭..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    Write-Host "正在启动Docker..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    Write-Host ""
    Write-Host "========================================"  -ForegroundColor Green
    Write-Host "✓ Docker正在重启" -ForegroundColor Green
    Write-Host "========================================"  -ForegroundColor Green
    Write-Host ""
    Write-Host "请等待约30-60秒让Docker完全启动" -ForegroundColor Yellow
    Write-Host "然后运行部署命令" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "配置已完成,请手动重启Docker Desktop" -ForegroundColor Yellow
}

Write-Host ""
