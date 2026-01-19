@echo off
chcp 65001 >nul
title QuantDinger - 停止所有服务

cls
echo.
echo ================================================================================
echo                      停止 QuantDinger 服务
echo ================================================================================
echo.

REM 停止后端服务
echo [停止] 正在停止后端服务...
taskkill /FI "WINDOWTITLE eq QuantDinger-Backend*" /F >nul 2>&1
if %errorlevel%==0 (
    echo [成功] 后端服务已停止
) else (
    echo [跳过] 后端服务未运行
)

REM 停止前端服务
echo [停止] 正在停止前端服务...
taskkill /FI "WINDOWTITLE eq QuantDinger-Frontend*" /F >nul 2>&1
if %errorlevel%==0 (
    echo [成功] 前端服务已停止
) else (
    echo [跳过] 前端服务未运行
)

REM 停止HAMA监控
echo [停止] 正在停止 HAMA 监控...
taskkill /FI "WINDOWTITLE eq HAMA-Monitor*" /F >nul 2>&1
if %errorlevel%==0 (
    echo [成功] HAMA 监控已停止
) else (
    echo [跳过] HAMA 监控未运行
)

echo.
echo ================================================================================
echo                       所有服务已停止
echo ================================================================================
echo.
timeout /t 2 /nobreak >nul
