#!/bin/bash

# QuantDinger 一键启动脚本 (Linux/Mac)

echo ""
echo "================================================================================"
echo "                        QuantDinger 一键启动"
echo "================================================================================"
echo ""

# 检查当前目录
if [ ! -d "backend_api_python" ]; then
    echo "[错误] 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] Python3 未安装"
    exit 1
fi

echo "[信息] 正在启动后端服务..."
echo ""

# 启动后端
cd backend_api_python
python3 run.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "[等待] 等待后端服务启动..."
sleep 5

echo ""
echo "[信息] 正在启动前端服务..."
echo ""

# 检查前端目录
if [ ! -d "quantdinger_vue" ]; then
    echo "[警告] 前端目录不存在，跳过前端启动"
    echo "[提示] 请先安装前端依赖：cd quantdinger_vue && npm install"
else
    # 检查npm是否安装
    if ! command -v npm &> /dev/null; then
        echo "[警告] npm 未安装，跳过前端启动"
    else
        # 启动前端
        cd quantdinger_vue
        npm run serve &
        FRONTEND_PID=$!
        cd ..
    fi
fi

echo ""
echo "================================================================================"
echo "                           启动完成！"
echo "================================================================================"
echo ""
echo "后端地址: http://localhost:5000"
echo "前端地址: http://localhost:8000"
echo ""
echo "API文档: http://localhost:5000/api/health"
echo ""
echo "后端进程 PID: $BACKEND_PID"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "前端进程 PID: $FRONTEND_PID"
fi
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
trap "echo ''; echo '[信息] 正在停止服务...'; kill $BACKEND_PID 2>/dev/null; [ ! -z \"$FRONTEND_PID\" ] && kill $FRONTEND_PID 2>/dev/null; echo '[完成] 所有服务已停止'; exit 0" INT

# 保持脚本运行
wait
