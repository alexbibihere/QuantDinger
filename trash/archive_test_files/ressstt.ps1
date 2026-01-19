#!/usr/bin/env pwsh

# 一键重启QuantDinger前后端服务脚本
Write-Host "========================================"
Write-Host "QuantDinger 服务重启脚本"
Write-Host "========================================"
Write-Host ""

# 函数：终止占用指定端口的进程
function Stop-ProcessByPort($port) {
    Write-Host "检查端口 $port 是否被占用..."
    $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($process in $processes) {
            $pid = $process.OwningProcess
            Write-Host "终止占用端口 $port 的进程 $pid..."
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "✅ 进程 $pid 已终止"
            } catch {
                Write-Host "❌ 终止进程 $pid 失败: $_"
            }
        }
    } else {
        Write-Host "✅ 端口 $port 未被占用"
    }
}

# 函数：在指定目录启动后台进程
function Start-BackgroundProcess($directory, $command, $name) {
    Write-Host "启动 $name 服务..."
    $scriptBlock = {
        param($dir, $cmd)
        Set-Location $dir
        Invoke-Expression $cmd
    }
    
    # 使用 Start-Job 启动后台进程
    Start-Job -ScriptBlock $scriptBlock -ArgumentList $directory, $command | Out-Null
    Write-Host "✅ $name 服务已在后台启动"
}

# 1. 终止现有进程
Write-Host "1. 终止现有服务进程..."
Stop-ProcessByPort -port 5000  # 后端服务端口
Stop-ProcessByPort -port 8000  # 前端服务端口
Write-Host ""

# 2. 启动后端服务
Write-Host "2. 启动后端服务..."
$backendDir = "$PSScriptRoot\backend_api_python"
$backendCmd = "python run.py"
Start-BackgroundProcess -directory $backendDir -command $backendCmd -name "后端"

# 等待后端启动（3秒）
Start-Sleep -Seconds 3

# 3. 启动前端服务
Write-Host "3. 启动前端服务..."
$frontendDir = "$PSScriptRoot\quantdinger_vue"
$frontendCmd = "npm run serve -- --no-lint"
Start-BackgroundProcess -directory $frontendDir -command $frontendCmd -name "前端"

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
Write-Host "使用以下命令查看服务状态："
Write-Host "  Get-Job  # 查看所有后台作业"
Write-Host "  Receive-Job -Id <JobId>  # 查看指定作业输出"
Write-Host "  Stop-Job -Id <JobId>  # 停止指定作业"
Write-Host ""
Write-Host "========================================"