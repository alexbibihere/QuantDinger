#!/usr/bin/env pwsh

# 一键重启QuantDinger前后端服务脚本
Write-Host "========================================"
Write-Host "QuantDinger 服务重启脚本"
Write-Host "========================================"
Write-Host ""

# 1. 终止现有进程
Write-Host "1. 终止现有服务进程..."

# 终止后端服务进程
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "✅ 终止后端服务进程 $($_.OwningProcess)"
}

# 终止前端服务进程
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "✅ 终止前端服务进程 $($_.OwningProcess)"
}

Write-Host ""

# 2. 启动后端服务
Write-Host "2. 启动后端服务..."
Start-Process -FilePath "python" -ArgumentList "run.py" -WorkingDirectory "$PSScriptRoot\backend_api_python" -WindowStyle Hidden
Write-Host "✅ 后端服务已启动"

# 等待后端启动（3秒）
Start-Sleep -Seconds 3

# 3. 启动前端服务
Write-Host "3. 启动前端服务..."
Start-Process -FilePath "npm" -ArgumentList "run serve -- --no-lint" -WorkingDirectory "$PSScriptRoot\quantdinger_vue" -WindowStyle Hidden
Write-Host "✅ 前端服务已启动"

# 等待前端启动（3秒）
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================"
Write-Host "服务重启完成！"
Write-Host "========================================"
Write-Host "后端服务地址: http://localhost:5000"
Write-Host "前端服务地址: http://localhost:8000"
Write-Host "默认登录凭证: quantdinger / 123456"
Write-Host ""
Write-Host "========================================"