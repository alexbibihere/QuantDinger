# QuantDinger Docker 部署脚本 (PowerShell)
# 使用方法：右键 -> 使用 PowerShell 运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuantDinger Docker 部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[错误] 请将此脚本放在 QuantDinger 根目录下运行" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查 Docker 是否运行
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
} catch {
    Write-Host "[错误] Docker 未找到，请确保已安装 Docker Desktop" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "[1/5] 停止现有容器..." -ForegroundColor Yellow
docker compose down
Write-Host ""

Write-Host "[2/5] 重新构建镜像..." -ForegroundColor Yellow
$clean = Read-Host "是否清理旧镜像? (y/N)"
if ($clean -eq "y" -or $clean -eq "Y") {
    docker compose build --no-cache
} else {
    docker compose build
}
Write-Host ""

Write-Host "[3/5] 启动容器..." -ForegroundColor Yellow
docker compose up -d
Write-Host ""

Write-Host "[4/5] 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

Write-Host "[5/5] 检查服务状态..." -ForegroundColor Yellow
Write-Host ""
docker compose ps
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试后端健康..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[成功] 后端健康检查通过!" -ForegroundColor Green
    }
} catch {
    Write-Host "[警告] 后端可能还在启动中，请稍等片刻" -ForegroundColor Yellow
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
Write-Host "常用命令:" -ForegroundColor White
Write-Host "  查看日志: docker compose logs -f backend" -ForegroundColor Gray
Write-Host "  停止服务: docker compose down" -ForegroundColor Gray
Write-Host "  重启后端: docker compose restart backend" -ForegroundColor Gray
Write-Host "  进入容器: docker exec -it quantdinger-backend bash" -ForegroundColor Gray
Write-Host ""
Write-Host "按回车键退出..."
$null = Read-Host
