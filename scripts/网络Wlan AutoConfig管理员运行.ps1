# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# 检测网络连接状态
function Test-NetworkConnection {
    # 方法1: 检测是否有活动的网络适配器
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }

    # 方法2: 尝试ping DNS服务器
    $pingTest = Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet -TimeoutSeconds 2

    # 方法3: 检测默认网关
    $gateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue

    # 综合判断：有活动适配器 且 能ping通 或 有默认网关
    if ($adapters -and ($pingTest -or $gateway)) {
        return $true
    }

    return $false
}

# 检测网络状态
$hasNetwork = Test-NetworkConnection

if ($hasNetwork) {
    Write-Host "✓ 检测到网络连接正常，无需重启WLAN服务。" -ForegroundColor Green
    Write-Host ""
    Write-Host "当前活动网络适配器:"
    Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Format-Table Name, InterfaceDescription, Status -AutoSize
} else {
    Write-Host "✗ 未检测到网络连接，正在重启WLAN AutoConfig服务..." -ForegroundColor Red
    Write-Host ""

    try {
        Restart-Service -Name WlanSvc -Force -ErrorAction Stop
        Write-Host "✓ WLAN AutoConfig服务已重启成功。" -ForegroundColor Green

        # 等待服务完全启动
        Start-Sleep -Seconds 2

        # 再次检测网络
        Write-Host "正在重新检测网络连接..."
        Start-Sleep -Seconds 3

        $hasNetworkAfter = Test-NetworkConnection
        if ($hasNetworkAfter) {
            Write-Host "✓ 网络连接已恢复！" -ForegroundColor Green
        } else {
            Write-Host "⚠ 网络仍未连接，请检查网络设置。" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "✗ 重启服务失败: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "按任意键退出..."
[Console]::ReadKey($true) | Out-Null