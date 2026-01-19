@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    从国内镜像源拉取Docker基础镜像
echo ========================================
echo.

setlocal EnableDelayedExpansion

:: 定义镜像列表
set images=python:3.12-slim node:18-alpine nginx:alpine

:: 国内镜像源列表
set mirrors=docker.m.daocloud.io docker.1panel.live docker.anyhub.us.kg dockerhub.icu

set success_count=0
set total_count=3

for %%i in (%images%) do (
    echo ----------------------------------------
    echo 拉取镜像: %%i
    echo ----------------------------------------

    set pulled=0

    for %%m in (%mirrors%) do (
        if !pulled! == 0 (
            echo 尝试镜像源: %%m

            :: 尝试从当前镜像源拉取
            docker pull %%m/%%i >nul 2>&1

            if !errorlevel! == 0 (
                :: 重新标记为原始名称
                docker tag %%m/%%i %%i >nul 2>&1
                echo √ 成功从 %%m 拉取 %%i
                set /a success_count+=1
                set pulled=1
            ) else (
                echo × 从 %%m 拉取失败
            )
        )
    )

    if !pulled! == 0 (
        echo × 无法从任何镜像源拉取 %%i
    )

    echo.
)

echo ========================================
echo 拉取完成!
echo 成功: %success_count% / %total_count%
echo ========================================
echo.

:: 显示本地镜像
echo 本地Docker镜像列表:
docker images | findstr /i "python node nginx"

echo.
echo 镜像拉取完成后,运行部署命令:
echo   cd d:\github\QuantDinger
echo   docker compose up -d --build
echo.

pause
