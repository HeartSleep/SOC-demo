#!/bin/bash
# SOC Platform Local Development Stop Script

echo "🛑 停止 SOC 安全平台..."

# 创建日志目录
mkdir -p logs

# 停止后端服务
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm -f logs/backend.pid
fi

# 停止前端服务
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm -f logs/frontend.pid
fi

# 停止所有相关进程
pkill -f "uvicorn app.main:app"
pkill -f "vite"

echo "✅ 所有服务已停止"
